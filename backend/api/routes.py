"""
api/routes.py
All FastAPI route handlers. Engine accessed via request.app.state.engine.
"""
from __future__ import annotations
import time
import uuid
from typing import List

from fastapi import APIRouter, Request, HTTPException

from api.models import (
    MissionRequest,
    ObstacleRequest,
    SpeedRequest,
    SuccessResponse,
)
from db.database import save_mission_event, get_mission_history

router = APIRouter()


def get_engine(request: Request):
    return request.app.state.engine


# ─────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────
@router.get("/api/environment")
async def get_environment(request: Request):
    engine = get_engine(request)
    return engine.env.to_dict()


# ─────────────────────────────────────────────
# Robot
# ─────────────────────────────────────────────
@router.get("/api/robot")
async def get_robot(request: Request):
    engine = get_engine(request)
    return engine.robot.to_dict()


# ─────────────────────────────────────────────
# Full simulation state (single poll endpoint)
# ─────────────────────────────────────────────
@router.get("/api/state")
async def get_state(request: Request):
    engine = get_engine(request)
    return engine.get_state()


# ─────────────────────────────────────────────
# Missions
# ─────────────────────────────────────────────
@router.post("/api/missions", response_model=SuccessResponse)
async def create_mission(body: MissionRequest, request: Request):
    engine = get_engine(request)
    async with engine._lock:
        mission_id = str(uuid.uuid4())[:8]

        if body.waypoints:
            waypoints = body.waypoints
        else:
            # Default demo: navigate to storage room then reception
            storage = list(engine.env.get_room_centre("storage_room"))
            reception = list(engine.env.get_room_centre("reception"))
            waypoints = [storage, reception]

        ok = engine.start_mission(waypoints, mission_id=mission_id)
        if not ok:
            raise HTTPException(status_code=422, detail="Cannot plan path — destination unreachable.")

        await save_mission_event(mission_id, "STARTED", {"waypoints": waypoints})

    return SuccessResponse(
        success=True,
        message=f"Mission {mission_id} started.",
        data={"mission_id": mission_id, "path_length": len(engine.robot.path)},
    )


@router.post("/api/missions/navigate", response_model=SuccessResponse)
async def navigate_to(body: dict, request: Request):
    """Navigate to a named location."""
    engine = get_engine(request)
    location = body.get("location", "")
    async with engine._lock:
        centre = engine.env.get_room_centre(location)
        if centre is None:
            raise HTTPException(status_code=404, detail=f"Unknown location: {location}")

        mission_id = str(uuid.uuid4())[:8]
        ok = engine.start_mission([list(centre)], mission_id=mission_id)
        if not ok:
            raise HTTPException(status_code=422, detail="No path to destination.")

    return SuccessResponse(
        success=True,
        message=f"Navigating to {location}.",
        data={"mission_id": mission_id},
    )


@router.post("/api/missions/pause", response_model=SuccessResponse)
async def pause_mission(request: Request):
    engine = get_engine(request)
    async with engine._lock:
        engine.pause_mission()
    return SuccessResponse(success=True, message="Mission paused.")


@router.post("/api/missions/resume", response_model=SuccessResponse)
async def resume_mission(request: Request):
    engine = get_engine(request)
    async with engine._lock:
        engine.resume_mission()
    return SuccessResponse(success=True, message="Mission resumed.")


@router.post("/api/missions/stop", response_model=SuccessResponse)
async def stop_mission(request: Request):
    engine = get_engine(request)
    async with engine._lock:
        engine.stop_mission()
    return SuccessResponse(success=True, message="Mission stopped.")


# ─────────────────────────────────────────────
# Simulation control
# ─────────────────────────────────────────────
@router.post("/api/simulation/reset", response_model=SuccessResponse)
async def reset_simulation(request: Request):
    engine = get_engine(request)
    async with engine._lock:
        engine.reset()
    return SuccessResponse(success=True, message="Simulation reset.")


@router.post("/api/simulation/speed", response_model=SuccessResponse)
async def set_speed(body: SpeedRequest, request: Request):
    engine = get_engine(request)
    engine.robot.speed = body.speed
    return SuccessResponse(success=True, message=f"Speed set to {body.speed}x.")


# ─────────────────────────────────────────────
# Obstacles
# ─────────────────────────────────────────────
@router.post("/api/obstacles", response_model=SuccessResponse)
async def add_obstacle(body: ObstacleRequest, request: Request):
    engine = get_engine(request)
    async with engine._lock:
        obs = engine.env.add_obstacle(body.col, body.row, body.is_dynamic)
        if obs is None:
            raise HTTPException(status_code=422, detail="Invalid obstacle position.")
        engine._log_event("OBSTACLE", f"Obstacle added at ({body.col},{body.row}).")
    return SuccessResponse(
        success=True,
        message=f"Obstacle {obs.id} added.",
        data={"obstacle_id": obs.id},
    )


@router.delete("/api/obstacles/{obstacle_id}", response_model=SuccessResponse)
async def remove_obstacle(obstacle_id: str, request: Request):
    engine = get_engine(request)
    async with engine._lock:
        removed = engine.env.remove_obstacle(obstacle_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Obstacle not found.")
        engine._log_event("OBSTACLE", f"Obstacle {obstacle_id} removed.")
    return SuccessResponse(success=True, message=f"Obstacle {obstacle_id} removed.")


# ─────────────────────────────────────────────
# Events & statistics
# ─────────────────────────────────────────────
@router.get("/api/events")
async def get_events(request: Request):
    engine = get_engine(request)
    return {"events": engine.events[-100:]}


@router.get("/api/statistics")
async def get_statistics(request: Request):
    engine = get_engine(request)
    robot = engine.robot
    return {
        "steps_taken": robot.steps_taken,
        "replanning_count": robot.replanning_count,
        "battery": robot.battery,
        "path_length": len(robot.path),
        "travelled_path_length": len(robot.travelled_path),
        "status": robot.status.value,
        "event_count": len(engine.events),
    }


@router.get("/api/missions/history")
async def mission_history():
    history = await get_mission_history()
    return {"missions": history}
