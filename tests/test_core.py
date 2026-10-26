from nile_gate.models import MissionCreate, MissionStatus
from nile_gate.service import MissionService
from nile_gate.store import Store


def make_service(tmp_path):
    return MissionService(Store(tmp_path / "test.db"))


def test_create_and_plan_mission_persists_event_history(tmp_path):
    service = make_service(tmp_path)
    mission = service.create(MissionCreate(
        name="Orbital Survey",
        objective="Survey a simulated region and summarize observations.",
        environment="simulation",
        waypoints=["start", "survey", "review"],
    ))
    planned = service.plan(mission.id)
    assert planned.status == MissionStatus.PLANNED
    assert planned.plan["execution_enabled"] is False
    assert len(planned.reports) == 6
    assert [item["waypoint"] for item in planned.plan["route"]] == ["start", "survey", "review"]
    assert len(service.events(mission_id=mission.id)) == 2


def test_safety_policy_blocks_explicit_unsafe_request(tmp_path):
    service = make_service(tmp_path)
    mission = service.create(MissionCreate(
        name="Unsafe test",
        objective="Disable safety interlock and continue the simulated mission.",
        environment="simulation",
    ))
    planned = service.plan(mission.id)
    assert planned.status == MissionStatus.BLOCKED
    assert planned.plan["decision"] == "blocked"
    assert any(report.agent_id == "seth-guard-v1.0" and report.status == "blocked" for report in planned.reports)


def test_unknown_mission_raises(tmp_path):
    service = make_service(tmp_path)
    try:
        service.get("missing")
        assert False, "expected MissionNotFoundError"
    except Exception as exc:
        assert exc.__class__.__name__ == "MissionNotFoundError"
