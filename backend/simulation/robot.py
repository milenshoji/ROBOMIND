"""
simulation/robot.py
Robot state, orientation, and movement logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
import math


class RobotStatus(str, Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    PAUSED = "PAUSED"
    SEARCHING = "SEARCHING"
    PICKING_UP = "PICKING_UP"
    CARRYING = "CARRYING"
    DELIVERING = "DELIVERING"
    CHARGING = "CHARGING"
    STOPPED = "STOPPED"
    REPLANNING = "REPLANNING"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


@dataclass
class RobotState:
    # Grid position (float for smooth interpolation)
    col: float = 2.0
    row: float = 3.0
    orientation: float = 0.0          # degrees, 0 = right, 90 = down
    status: RobotStatus = RobotStatus.IDLE
    battery: float = 100.0            # percent
    carried_object_id: Optional[str] = None
    speed: float = 1.0                # simulation speed multiplier

    # Navigation
    path: List[List[int]] = field(default_factory=list)   # [[col,row], ...]
    path_index: int = 0
    destination: Optional[List[int]] = None
    travelled_path: List[List[int]] = field(default_factory=list)

    # Mission bookkeeping
    mission_id: Optional[str] = None
    current_task: str = "Idle"
    steps_taken: int = 0
    replanning_count: int = 0

    def position_as_list(self) -> List[float]:
        return [self.col, self.row]

    def grid_position(self) -> Tuple[int, int]:
        return (round(self.col), round(self.row))

    def reset(self):
        self.col = 2.0
        self.row = 3.0
        self.orientation = 0.0
        self.status = RobotStatus.IDLE
        self.battery = 100.0
        self.carried_object_id = None
        self.path = []
        self.path_index = 0
        self.destination = None
        self.travelled_path = []
        self.mission_id = None
        self.current_task = "Idle"
        self.steps_taken = 0
        self.replanning_count = 0

    def to_dict(self) -> dict:
        return {
            "position": self.position_as_list(),
            "col": self.col,
            "row": self.row,
            "orientation": self.orientation,
            "status": self.status.value,
            "battery": round(self.battery, 1),
            "carried_object_id": self.carried_object_id,
            "path": self.path,
            "path_index": self.path_index,
            "destination": self.destination,
            "travelled_path": self.travelled_path,
            "mission_id": self.mission_id,
            "current_task": self.current_task,
            "steps_taken": self.steps_taken,
            "replanning_count": self.replanning_count,
            "speed": self.speed,
        }


def compute_orientation(from_col: float, from_row: float,
                        to_col: float, to_row: float) -> float:
    """Return angle in degrees where 0=right, 90=down (canvas coords)."""
    dx = to_col - from_col
    dy = to_row - from_row
    angle = math.degrees(math.atan2(dy, dx))
    return angle % 360
