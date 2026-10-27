"""
simulation/engine.py
Core simulation engine: tick loop, A* pathfinding, movement, safety checks.
"""
from __future__ import annotations
import asyncio
import heapq
import math
import time
import uuid
from typing import Dict, List, Optional, Tuple

from simulation.environment import Environment, CellType
from simulation.robot import RobotState, RobotStatus, compute_orientation


# ──────────────────────────────────────────────
# A* Pathfinding
# ──────────────────────────────────────────────
def astar(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    width: int,
    height: int,
) -> Optional[List[Tuple[int, int]]]:
    """
    A* on a 2-D occupancy grid.
    Returns list of (col, row) tuples from start to goal (inclusive),
    or None if no path exists.
    Walls / obstacles are impassable.
    """
    PASSABLE = {
        int(CellType.FLOOR),
        int(CellType.RECEPTION),
        int(CellType.STORAGE),
        int(CellType.LABORATORY),
        int(CellType.CORRIDOR),
        int(CellType.CHARGING_STATION),
    }

    def h(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])   # Manhattan

    def neighbors(node: Tuple[int, int]):
        c, r = node
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc, nr = c + dc, r + dr
            if 0 <= nr < height and 0 <= nc < width:
                if grid[nr][nc] in PASSABLE:
                    yield (nc, nr)

    if grid[start[1]][start[0]] not in PASSABLE:
        return None
    if grid[goal[1]][goal[0]] not in PASSABLE:
        return None

    open_set: list = []
    heapq.heappush(open_set, (0.0, start))
    came_from: Dict[Tuple, Optional[Tuple]] = {start: None}
    g_score: Dict[Tuple, float] = {start: 0.0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            return list(reversed(path))

        for nb in neighbors(current):
            tentative = g_score[current] + 1.0
            if nb not in g_score or tentative < g_score[nb]:
                g_score[nb] = tentative
                f = tentative + h(nb, goal)
                heapq.heappush(open_set, (f, nb))
                came_from[nb] = current

    return None   # no path


# ──────────────────────────────────────────────
# Simulation Engine
# ──────────────────────────────────────────────
class SimulationEngine:
    TICK_INTERVAL = 0.15       # seconds between ticks (≈6–7 ticks/s)
    BATTERY_DRAIN = 0.05       # percent per step

    def __init__(self):
        self.env = Environment()
        self.robot = RobotState()
        self.running = False       # mission active
        self.paused = False
        self.events: List[dict] = []
        self._lock = asyncio.Lock()
        self._initialized = False

    # ── Lifecycle ─────────────────────────────
    def initialize(self):
        self.env.reset()
        self.robot.reset()
        self.running = False
        self.paused = False
        self.events = []
        self._initialized = True
        self._log_event("SYSTEM", "Simulation initialized.")

    def reset(self):
        self.initialize()

    # ── Event log ────────────────────────────
    def _log_event(self, category: str, message: str, data: Optional[dict] = None):
        self.events.append({
            "id": str(uuid.uuid4())[:8],
            "timestamp": time.time(),
            "category": category,
            "message": message,
            "data": data or {},
        })

    # ── Path planning ─────────────────────────
    def plan_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> Optional[List[List[int]]]:
        path = astar(self.env.grid, start, goal, self.env.width, self.env.height)
        if path:
            return [[c, r] for c, r in path]
        return None

    # ── Mission control ───────────────────────
    def start_mission(self, waypoints: List[List[int]], mission_id: Optional[str] = None):
        """
        Set a path for the robot to follow.
        waypoints: list of [col, row] grid cells.
        """
        if not waypoints:
            return False

        start = self.robot.grid_position()
        goal = (waypoints[-1][0], waypoints[-1][1])

        path = self.plan_path(start, goal)
        if path is None:
            self._log_event("NAVIGATION", f"No path found from {start} to {goal}.")
            return False

        self.robot.mission_id = mission_id or str(uuid.uuid4())[:8]
        self.robot.path = path
        self.robot.path_index = 0
        self.robot.destination = waypoints[-1]
        self.robot.travelled_path = [list(start)]
        self.robot.status = RobotStatus.MOVING
        self.robot.current_task = f"Navigating to {goal}"
        self.running = True
        self.paused = False
        self._log_event("MISSION", f"Mission {self.robot.mission_id} started. Path length: {len(path)}.")
        return True

    def pause_mission(self):
        if self.running and not self.paused:
            self.paused = True
            self.robot.status = RobotStatus.PAUSED
            self._log_event("MISSION", "Mission paused.")

    def resume_mission(self):
        if self.running and self.paused:
            self.paused = False
            self.robot.status = RobotStatus.MOVING
            self._log_event("MISSION", "Mission resumed.")

    def stop_mission(self):
        if self.running:
            self.running = False
            self.paused = False
            self.robot.status = RobotStatus.STOPPED
            self.robot.path = []
            self.robot.path_index = 0
            self._log_event("MISSION", "Mission stopped by user.")

    # ── Tick (movement step) ──────────────────
    def _tick(self):
        """Advance robot one step along its path."""
        robot = self.robot

        if not self.running or self.paused:
            return

        if robot.status == RobotStatus.STOPPED:
            return

        if robot.path_index >= len(robot.path):
            # Reached destination
            robot.status = RobotStatus.IDLE
            self.running = False
            robot.current_task = "Mission complete"
            self._log_event("MISSION", "Robot reached destination.")
            return

        next_wp = robot.path[robot.path_index]
        nc, nr = next_wp[0], next_wp[1]

        # Safety check: is next cell still walkable?
        if not self.env.is_walkable(nc, nr):
            robot.status = RobotStatus.REPLANNING
            self._log_event("SAFETY", f"Next cell ({nc},{nr}) is blocked. Replanning...")

            current_col, current_row = robot.grid_position()
            goal = robot.path[-1]
            new_path = self.plan_path(
                (current_col, current_row),
                (goal[0], goal[1]),
            )
            if new_path is None:
                robot.status = RobotStatus.BLOCKED
                self.running = False
                self._log_event("SAFETY", "No alternative path found. Robot blocked.")
                return
            else:
                robot.path = new_path
                robot.path_index = 0
                robot.replanning_count += 1
                robot.status = RobotStatus.MOVING
                self._log_event("NAVIGATION", f"Replanned path. Length: {len(new_path)}. Replans: {robot.replanning_count}.")
                return

        # Update orientation
        robot.orientation = compute_orientation(robot.col, robot.row, nc, nr)

        # Move
        robot.col = float(nc)
        robot.row = float(nr)
        robot.path_index += 1
        robot.steps_taken += 1
        robot.battery = max(0.0, robot.battery - self.BATTERY_DRAIN)

        # Record travelled path
        tp = [round(robot.col), round(robot.row)]
        if not robot.travelled_path or robot.travelled_path[-1] != tp:
            robot.travelled_path.append(tp)

    # ── Async loop ────────────────────────────
    async def run_loop(self):
        """Background asyncio task: tick at TICK_INTERVAL."""
        while True:
            async with self._lock:
                if self._initialized:
                    effective_interval = self.TICK_INTERVAL / max(self.robot.speed, 0.1)
                    self._tick()
            await asyncio.sleep(self.TICK_INTERVAL / max(self.robot.speed, 0.1))

    # ── Serialisation ─────────────────────────
    def get_state(self) -> dict:
        return {
            "robot": self.robot.to_dict(),
            "environment": self.env.to_dict(),
            "running": self.running,
            "paused": self.paused,
            "events": self.events[-50:],   # last 50 events
        }
