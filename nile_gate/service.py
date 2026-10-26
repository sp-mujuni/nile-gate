"""Application service layer for Nile Gate."""
from __future__ import annotations

from datetime import datetime, timezone

from nile_gate.agents import AGENT_CATALOG, run_agents
from nile_gate.models import MissionCreate, MissionRecord, MissionStatus
from nile_gate.store import Store


class MissionNotFoundError(LookupError):
    pass


class MissionService:
    def __init__(self, store: Store | None = None):
        self.store = store or Store()

    def agents(self) -> list[dict]:
        return AGENT_CATALOG

    def create(self, request: MissionCreate) -> MissionRecord:
        mission = MissionRecord(**request.model_dump())
        self.store.save_mission(mission, event_type="mission.created", actor="operator",
                                payload={"name": mission.name, "environment": mission.environment})
        return mission

    def get(self, mission_id: str) -> MissionRecord:
        mission = self.store.get_mission(mission_id)
        if mission is None:
            raise MissionNotFoundError(mission_id)
        return mission

    def list(self, limit: int = 50) -> list[MissionRecord]:
        return self.store.list_missions(limit)

    def plan(self, mission_id: str) -> MissionRecord:
        mission = self.get(mission_id)
        recent_count = len(self.store.list_events(mission_id=mission_id, limit=1000))
        reports, plan = run_agents(mission, recent_event_count=recent_count)
        mission.reports = reports
        mission.plan = plan
        mission.status = MissionStatus.BLOCKED if plan["decision"] == "blocked" else MissionStatus.PLANNED
        mission.updated_at = datetime.now(timezone.utc)
        self.store.save_mission(mission, event_type="mission.planned" if mission.status != MissionStatus.BLOCKED else "mission.blocked",
                                actor="horus-vision-v1.0", payload={"status": mission.status.value, "agent_count": len(reports)})
        return mission

    def events(self, mission_id: str | None = None, limit: int = 100):
        if mission_id and self.store.get_mission(mission_id) is None:
            raise MissionNotFoundError(mission_id)
        return self.store.list_events(mission_id=mission_id, limit=limit)
