"""
RoboMind Backend — Main FastAPI Application Entry Point
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from db.database import init_db
from simulation.engine import SimulationEngine

# Global simulation engine instance
engine = SimulationEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_db()
    engine.initialize()
    # Start background tick loop
    task = asyncio.create_task(engine.run_loop())
    app.state.engine = engine
    app.state.tick_task = task
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="RoboMind API",
    description="AI-Powered Robotic Digital Twin and Autonomous Decision-Making Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject engine into routes via app.state
app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "RoboMind Backend",
        "version": "1.0.0",
        "phase": 1,
    }
