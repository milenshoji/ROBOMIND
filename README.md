# RoboMind 🤖

**AI-Powered Robotic Digital Twin and Autonomous Decision-Making Platform**

A software-only interactive 2D robot simulation featuring A\* pathfinding, dynamic obstacle avoidance, autonomous replanning, and a professional real-time dashboard.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Terminal 1 — Backend

```bash
cd robomind/backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

### Terminal 2 — Frontend

```bash
cd robomind/frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Project Structure

```
robomind/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt
│   ├── simulation/
│   │   ├── environment.py       # Grid map, rooms, obstacles
│   │   ├── robot.py             # Robot state & orientation
│   │   └── engine.py            # A* pathfinding, tick loop
│   ├── api/
│   │   ├── routes.py            # All API endpoints
│   │   └── models.py            # Pydantic models
│   ├── db/
│   │   └── database.py          # SQLite mission history
│   └── tests/
│       └── test_phase1.py       # pytest suite
└── frontend/
    └── src/
        ├── App.tsx              # Root component
        ├── components/          # Header, Canvas, Controls, Status
        ├── hooks/               # useSimulation polling hook
        └── types/               # TypeScript type definitions
```

---

## Running Tests

```bash
cd robomind/backend
pytest tests/ -v
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/state | Full simulation state (robot + env + events) |
| GET | /api/environment | Map grid, rooms, objects |
| GET | /api/robot | Robot state |
| POST | /api/missions | Start mission (waypoints or default) |
| POST | /api/missions/navigate | Navigate to named location |
| POST | /api/missions/pause | Pause |
| POST | /api/missions/resume | Resume |
| POST | /api/missions/stop | Stop |
| POST | /api/simulation/reset | Full reset |
| POST | /api/simulation/speed | Set speed multiplier |
| POST | /api/obstacles | Add obstacle |
| DELETE | /api/obstacles/{id} | Remove obstacle |
| GET | /api/events | Event log |
| GET | /api/statistics | Mission statistics |

Interactive docs: http://localhost:8000/docs

---

## Phase 1 — What's Implemented

- ✅ FastAPI backend with async tick loop
- ✅ 32×22 grid virtual office (Reception, Storage, Laboratory, Corridors, Charging)
- ✅ A\* pathfinding with collision checking
- ✅ Dynamic obstacle insertion + automatic replanning
- ✅ Robot state: position, orientation, battery, status
- ✅ React/TypeScript/Vite frontend
- ✅ HTML5 Canvas renderer (60fps, smooth robot animation)
- ✅ Mission controls: Start, Pause, Resume, Stop, Reset
- ✅ Speed control slider (0.5×–5×)
- ✅ Click-to-place obstacles on the map
- ✅ Real-time event log
- ✅ SQLite mission history database
- ✅ pytest test suite (12 tests)

## What Remains (Phases 2–6)

- Phase 2: Advanced A\* visualisation, multi-waypoint missions
- Phase 3: Natural language command parser
- Phase 4: Object pickup/delivery simulation
- Phase 5: Full safety monitoring dashboard
- Phase 6: Faculty demonstration workflow, mission history UI

---

## Troubleshooting

**Backend won't start:** Check Python 3.10+. Run `pip install -r requirements.txt` again.

**Frontend shows "Backend offline":** Make sure `uvicorn` is running on port 8000. Check CORS settings.

**No path found:** Target cell may be a wall. Use the Quick Navigate buttons to go to named rooms.

**Canvas not rendering:** Hard-reload the browser (Ctrl+Shift+R).
