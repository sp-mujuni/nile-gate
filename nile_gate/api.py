"""FastAPI entry point and dashboard delivery."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from nile_gate import __version__
from nile_gate.models import MissionCreate, MissionRecord
from nile_gate.service import MissionNotFoundError, MissionService

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

app = FastAPI(
    title="Nile Gate API",
    version=__version__,
    description="A safety-oriented multi-agent mission planning sandbox for Nile Galactic. Planning only; no hardware control.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

service = MissionService()


@app.get("/", include_in_schema=False)
def dashboard():
    if not (STATIC_DIR / "index.html").is_file():
        raise HTTPException(status_code=404, detail="Dashboard assets are not installed.")
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "nile-gate", "version": __version__, "mode": "planning-only"}


@app.get("/agents")
def list_agents():
    return {"agents": service.agents()}


@app.post("/missions", response_model=MissionRecord, status_code=201)
def create_mission(request: MissionCreate):
    return service.create(request)


@app.get("/missions", response_model=list[MissionRecord])
def list_missions(limit: int = Query(default=50, ge=1, le=200)):
    return service.list(limit)


@app.get("/missions/{mission_id}", response_model=MissionRecord)
def get_mission(mission_id: str):
    try:
        return service.get(mission_id)
    except MissionNotFoundError:
        raise HTTPException(status_code=404, detail="Mission not found.") from None


@app.post("/missions/{mission_id}/plan", response_model=MissionRecord)
def plan_mission(mission_id: str):
    try:
        return service.plan(mission_id)
    except MissionNotFoundError:
        raise HTTPException(status_code=404, detail="Mission not found.") from None


@app.get("/events")
def list_events(mission_id: str | None = None, limit: int = Query(default=100, ge=1, le=1000)):
    try:
        events = service.events(mission_id=mission_id, limit=limit)
        return {"events": [event.model_dump(mode="json") for event in events]}
    except MissionNotFoundError:
        raise HTTPException(status_code=404, detail="Mission not found.") from None
