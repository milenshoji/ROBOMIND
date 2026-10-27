"""
tests/test_phase1.py
Phase 1 automated tests.
Run with:  cd backend && pytest tests/ -v
"""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport

# Bootstrap the app without a running event loop
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from simulation.engine import SimulationEngine, astar
from simulation.environment import Environment, CellType


# ──────────────────────────────────────────────
# Fixture: inject engine into app.state so
# API routes can access it without running the
# full lifespan (which starts a background task).
# ──────────────────────────────────────────────
@pytest.fixture(autouse=True)
def inject_engine():
    """Attach a fresh SimulationEngine to app.state before each test."""
    engine = SimulationEngine()
    engine.initialize()
    app.state.engine = engine
    yield engine
    # Cleanup: remove reference
    try:
        del app.state.engine
    except Exception:
        pass


# ──────────────────────────────────────────────
# Unit tests: A* pathfinder
# ──────────────────────────────────────────────
class TestAstar:
    def _make_simple_grid(self):
        """5×5 open grid (all FLOOR)."""
        return [[int(CellType.FLOOR)] * 5 for _ in range(5)]

    def test_straight_path(self):
        grid = self._make_simple_grid()
        path = astar(grid, (0, 0), (4, 0), 5, 5)
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (4, 0)
        assert len(path) == 5

    def test_path_around_wall(self):
        grid = self._make_simple_grid()
        # Vertical wall at col=2, rows 0-3
        for r in range(4):
            grid[r][2] = int(CellType.WALL)
        path = astar(grid, (0, 0), (4, 0), 5, 5)
        assert path is not None
        # Path must go around — no cell should have col==2 (except row==4)
        for c, r in path:
            if r < 4:
                assert c != 2, f"Path passed through wall at ({c},{r})"

    def test_blocked_start(self):
        grid = self._make_simple_grid()
        grid[0][0] = int(CellType.WALL)
        path = astar(grid, (0, 0), (4, 4), 5, 5)
        assert path is None

    def test_blocked_goal(self):
        grid = self._make_simple_grid()
        grid[4][4] = int(CellType.WALL)
        path = astar(grid, (0, 0), (4, 4), 5, 5)
        assert path is None

    def test_unreachable_destination(self):
        grid = self._make_simple_grid()
        # Surround goal with walls
        for r in range(3, 5):
            for c in range(3, 5):
                grid[r][c] = int(CellType.WALL)
        path = astar(grid, (0, 0), (4, 4), 5, 5)
        assert path is None

    def test_same_start_and_goal(self):
        grid = self._make_simple_grid()
        path = astar(grid, (2, 2), (2, 2), 5, 5)
        assert path is not None
        assert len(path) == 1


# ──────────────────────────────────────────────
# Unit tests: Environment
# ──────────────────────────────────────────────
class TestEnvironment:
    def test_walls_not_walkable(self):
        env = Environment()
        # Corner (0,0) should be a wall
        assert not env.is_walkable(0, 0)

    def test_reception_walkable(self):
        env = Environment()
        # Reception centre should be walkable
        centre = env.get_room_centre("reception")
        assert centre is not None
        c, r = centre
        assert env.is_walkable(c, r)

    def test_add_remove_obstacle(self):
        env = Environment()
        # Find a walkable cell
        c, r = env.get_room_centre("laboratory")
        obs = env.add_obstacle(c, r, is_dynamic=True)
        assert obs is not None
        assert not env.is_walkable(c, r)
        env.remove_obstacle(obs.id)
        assert env.is_walkable(c, r)

    def test_reset_restores_state(self):
        env = Environment()
        c, r = env.get_room_centre("laboratory")
        env.add_obstacle(c, r)
        env.reset()
        assert env.is_walkable(c, r)

    def test_location_aliases(self):
        env = Environment()
        assert env.get_room_centre("storage") is not None
        assert env.get_room_centre("lab") is not None
        assert env.get_room_centre("lobby") is not None

    def test_unknown_location(self):
        env = Environment()
        assert env.get_room_centre("moon_base") is None


# ──────────────────────────────────────────────
# Integration tests: API via httpx ASGI transport
# ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_environment_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/environment")
    assert resp.status_code == 200
    data = resp.json()
    assert "grid" in data
    assert "width" in data
    assert "rooms" in data


@pytest.mark.asyncio
async def test_robot_initial_state():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/robot")
    assert resp.status_code == 200
    robot = resp.json()
    assert robot["status"] == "IDLE"
    assert robot["battery"] == 100.0


@pytest.mark.asyncio
async def test_reset_simulation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/simulation/reset")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_add_and_remove_obstacle_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        add_resp = await client.post("/api/obstacles", json={"col": 26, "row": 7, "is_dynamic": True})
        assert add_resp.status_code == 200
        obs_id = add_resp.json()["data"]["obstacle_id"]

        del_resp = await client.delete(f"/api/obstacles/{obs_id}")
        assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_wall_blocks_navigation():
    """A mission targeting a wall cell must fail at path planning."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Reset first
        await client.post("/api/simulation/reset")
        # (0,0) is a wall — should be unreachable
        resp = await client.post(
            "/api/missions",
            json={"waypoints": [[0, 0]]},
        )
    # Expect 422 (unreachable) or success=False
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        assert resp.json()["success"] is False
