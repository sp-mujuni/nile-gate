from fastapi.testclient import TestClient

from nile_gate.api import app, service
from nile_gate.service import MissionService
from nile_gate.store import Store


def test_api_mission_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "store", Store(tmp_path / "api.db"))
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["mode"] == "planning-only"

    created = client.post("/missions", json={
        "name": "Telemetry Replay",
        "objective": "Review a simulated telemetry replay and summarize anomalies.",
        "environment": "simulation",
        "waypoints": ["load", "review", "report"],
    })
    assert created.status_code == 201
    mission_id = created.json()["id"]

    planned = client.post(f"/missions/{mission_id}/plan")
    assert planned.status_code == 200
    assert planned.json()["status"] == "planned"
    assert planned.json()["plan"]["execution_enabled"] is False

    assert client.get(f"/missions/{mission_id}").status_code == 200
    assert client.get("/events").json()["events"]


def test_api_unknown_mission_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "store", Store(tmp_path / "api-missing.db"))
    client = TestClient(app)
    assert client.get("/missions/not-a-real-id").status_code == 404
