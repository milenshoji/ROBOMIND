"""
api/models.py
Pydantic request and response models.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class MoveRequest(BaseModel):
    col: int = Field(..., description="Target column")
    row: int = Field(..., description="Target row")


class MissionRequest(BaseModel):
    command: Optional[str] = Field(None, description="Natural language command (Phase 3+)")
    waypoints: Optional[List[List[int]]] = Field(
        None, description="Explicit waypoints [[col,row], ...] for Phase 1"
    )


class ObstacleRequest(BaseModel):
    col: int
    row: int
    is_dynamic: bool = True
    label: str = "Dynamic Obstacle"


class SpeedRequest(BaseModel):
    speed: float = Field(..., ge=0.1, le=10.0, description="Simulation speed multiplier")


class RobotResponse(BaseModel):
    position: List[float]
    col: float
    row: float
    orientation: float
    status: str
    battery: float
    carried_object_id: Optional[str]
    path: List[List[int]]
    path_index: int
    destination: Optional[List[int]]
    travelled_path: List[List[int]]
    mission_id: Optional[str]
    current_task: str
    steps_taken: int
    replanning_count: int
    speed: float


class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
