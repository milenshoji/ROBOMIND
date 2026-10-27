"""
simulation/environment.py
Grid-based occupancy map for the virtual office environment.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple
import copy

# ──────────────────────────────────────────────
# Cell types
# ──────────────────────────────────────────────
class CellType(IntEnum):
    FLOOR = 0
    WALL = 1
    OBSTACLE_STATIC = 2
    OBSTACLE_DYNAMIC = 3
    CHARGING_STATION = 4
    RECEPTION = 5
    STORAGE = 6
    LABORATORY = 7
    CORRIDOR = 8


# ──────────────────────────────────────────────
# Map dimensions
# ──────────────────────────────────────────────
MAP_WIDTH = 32
MAP_HEIGHT = 22


# ──────────────────────────────────────────────
# Named rooms / locations (centre cells)
# ──────────────────────────────────────────────
ROOMS: Dict[str, dict] = {
    "reception": {
        "label": "Reception",
        "rect": (1, 1, 9, 6),        # (col_start, row_start, col_end, row_end)
        "centre": (5, 3),
        "cell_type": CellType.RECEPTION,
    },
    "storage_room": {
        "label": "Storage Room",
        "rect": (1, 8, 9, 14),
        "centre": (5, 11),
        "cell_type": CellType.STORAGE,
    },
    "laboratory": {
        "label": "Laboratory",
        "rect": (22, 1, 30, 14),
        "centre": (26, 7),
        "cell_type": CellType.LABORATORY,
    },
    "corridor_h": {
        "label": "Corridor",
        "rect": (10, 3, 21, 5),
        "centre": (15, 4),
        "cell_type": CellType.CORRIDOR,
    },
    "corridor_v": {
        "label": "Corridor",
        "rect": (10, 5, 12, 20),
        "centre": (11, 13),
        "cell_type": CellType.CORRIDOR,
    },
    "charging_station": {
        "label": "Charging Station",
        "rect": (1, 16, 5, 20),
        "centre": (3, 18),
        "cell_type": CellType.CHARGING_STATION,
    },
}

# Aliases for navigation
LOCATION_ALIASES: Dict[str, str] = {
    "reception": "reception",
    "front desk": "reception",
    "lobby": "reception",
    "storage": "storage_room",
    "storage room": "storage_room",
    "store room": "storage_room",
    "lab": "laboratory",
    "laboratory": "laboratory",
    "charger": "charging_station",
    "charging station": "charging_station",
    "charging": "charging_station",
}


# ──────────────────────────────────────────────
# Object definitions
# ──────────────────────────────────────────────
@dataclass
class SimObject:
    id: str
    label: str
    position: List[int]          # [col, row]
    color: str                   # hex string for renderer
    pickable: bool = True
    picked_up: bool = False
    delivered: bool = False


# ──────────────────────────────────────────────
# Obstacle
# ──────────────────────────────────────────────
@dataclass
class Obstacle:
    id: str
    position: List[int]          # [col, row]
    is_dynamic: bool = False
    label: str = "Obstacle"


# ──────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────
class Environment:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self._base_grid: List[List[int]] = []
        self.grid: List[List[int]] = []
        self.objects: Dict[str, SimObject] = {}
        self.obstacles: Dict[str, Obstacle] = {}
        self._next_obstacle_id = 1
        self._build_base_grid()
        self._place_default_objects()
        self._place_default_obstacles()
        self._sync_grid()

    # ── Grid construction ──────────────────────
    def _build_base_grid(self):
        g = [[CellType.WALL] * self.width for _ in range(self.height)]

        def fill(r0, c0, r1, c1, ct):
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    g[r][c] = ct

        # Rooms
        fill(1, 1, 6, 9, CellType.RECEPTION)
        fill(8, 1, 14, 9, CellType.STORAGE)
        fill(1, 22, 14, 30, CellType.LABORATORY)
        fill(3, 10, 5, 21, CellType.CORRIDOR)      # horizontal corridor
        fill(5, 10, 20, 12, CellType.CORRIDOR)      # vertical corridor
        fill(16, 1, 20, 5, CellType.CHARGING_STATION)

        self._base_grid = g

    def _build_base_grid(self):
        """Build a clean base grid from room definitions."""
        g = [[int(CellType.WALL)] * self.width for _ in range(self.height)]

        for room_key, room in ROOMS.items():
            c0, r0, c1, r1 = room["rect"]
            ct = int(room["cell_type"])
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if 0 <= r < self.height and 0 <= c < self.width:
                        g[r][c] = ct

        self._base_grid = g

    def _sync_grid(self):
        """Copy base grid then stamp obstacles onto it."""
        self.grid = [row[:] for row in self._base_grid]
        for obs in self.obstacles.values():
            c, r = obs.position
            if 0 <= r < self.height and 0 <= c < self.width:
                self.grid[r][c] = int(
                    CellType.OBSTACLE_DYNAMIC if obs.is_dynamic
                    else CellType.OBSTACLE_STATIC
                )

    # ── Objects ───────────────────────────────
    def _place_default_objects(self):
        self.objects = {
            "red_box": SimObject(
                id="red_box",
                label="Red Box",
                position=[5, 11],   # inside storage room
                color="#FF3B30",
                pickable=True,
            ),
            "blue_crate": SimObject(
                id="blue_crate",
                label="Blue Crate",
                position=[7, 12],
                color="#007AFF",
                pickable=True,
            ),
            "green_package": SimObject(
                id="green_package",
                label="Green Package",
                position=[6, 10],
                color="#34C759",
                pickable=True,
            ),
        }

    def _place_default_obstacles(self):
        self.obstacles = {
            "obs_1": Obstacle(
                id="obs_1",
                position=[15, 4],
                is_dynamic=False,
                label="Shelf Unit",
            ),
        }

    # ── Public API ────────────────────────────
    def is_walkable(self, col: int, row: int) -> bool:
        if not (0 <= row < self.height and 0 <= col < self.width):
            return False
        return self.grid[row][col] not in (
            int(CellType.WALL),
            int(CellType.OBSTACLE_STATIC),
            int(CellType.OBSTACLE_DYNAMIC),
        )

    def add_obstacle(self, col: int, row: int, is_dynamic: bool = True) -> Optional[Obstacle]:
        if not (0 <= row < self.height and 0 <= col < self.width):
            return None
        obs_id = f"obs_{self._next_obstacle_id}"
        self._next_obstacle_id += 1
        obs = Obstacle(id=obs_id, position=[col, row], is_dynamic=is_dynamic)
        self.obstacles[obs_id] = obs
        self._sync_grid()
        return obs

    def remove_obstacle(self, obs_id: str) -> bool:
        if obs_id in self.obstacles:
            del self.obstacles[obs_id]
            self._sync_grid()
            return True
        return False

    def get_room_centre(self, location_key: str) -> Optional[Tuple[int, int]]:
        key = LOCATION_ALIASES.get(location_key.lower(), location_key.lower())
        room = ROOMS.get(key)
        if room:
            return tuple(room["centre"])
        return None

    def reset(self):
        self._place_default_objects()
        self._place_default_obstacles()
        self._sync_grid()

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "grid": self.grid,
            "rooms": {
                k: {
                    "label": v["label"],
                    "rect": list(v["rect"]),
                    "centre": list(v["centre"]),
                }
                for k, v in ROOMS.items()
            },
            "objects": {
                k: {
                    "id": o.id,
                    "label": o.label,
                    "position": o.position,
                    "color": o.color,
                    "pickable": o.pickable,
                    "picked_up": o.picked_up,
                    "delivered": o.delivered,
                }
                for k, o in self.objects.items()
            },
            "obstacles": {
                k: {
                    "id": obs.id,
                    "position": obs.position,
                    "is_dynamic": obs.is_dynamic,
                    "label": obs.label,
                }
                for k, obs in self.obstacles.items()
            },
        }
