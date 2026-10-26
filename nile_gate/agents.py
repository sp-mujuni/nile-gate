"""Deterministic, inspectable agents for the first Nile Gate MVP.

These agents produce planning recommendations only. They do not command hardware,
execute vehicle control, or claim flight certification.
"""
from __future__ import annotations

import re
from typing import Any

from nile_gate.models import AgentReport, MissionRecord

AGENT_CATALOG = [
    {"id": "anubis-guide-v1.0", "name": "Anubis Guide", "role": "mission intake, scope and completeness"},
    {"id": "horus-vision-v1.0", "name": "Horus Vision", "role": "coordination and final synthesis"},
    {"id": "sobek-archive-v1.0", "name": "Sobek Archive", "role": "mission knowledge and event history"},
    {"id": "seth-guard-v1.0", "name": "Seth Guard", "role": "policy checks and safety boundaries"},
    {"id": "ra-pathfinder-v1.0", "name": "Ra Pathfinder", "role": "route and sequence planning"},
    {"id": "thoth-strategy-v1.0", "name": "Thoth Strategy", "role": "objective decomposition and priorities"},
]

# Conservative keyword checks are guardrails for this sandbox, not a complete safety system.
BLOCKED_TERMS = (
    "disable safety", "bypass interlock", "weapon release", "target civilians",
    "override all safeguards", "disable telemetry", "ignore collision warning",
)


def _report(agent_id: str, name: str, status: str, summary: str, findings: list[str] | None = None, data: dict[str, Any] | None = None) -> AgentReport:
    return AgentReport(agent_id=agent_id, agent_name=name, status=status, summary=summary, findings=findings or [], data=data or {})


def anubis_guide(mission: MissionRecord) -> AgentReport:
    findings = []
    if len(mission.objective.split()) < 3:
        findings.append("Objective is short; clarify measurable success criteria.")
    if mission.environment.lower() in {"simulation", "simulator", "test"}:
        findings.append("Environment is explicitly identified as a test/simulation context.")
    else:
        findings.append("Non-simulation environment declared; this MVP still operates in planning-only mode.")
    if not mission.waypoints:
        findings.append("No waypoints supplied; route planning will return a sequence of mission stages instead.")
    return _report("anubis-guide-v1.0", "Anubis Guide", "ok", "Mission intake checked.", findings,
                   {"name_length": len(mission.name), "waypoint_count": len(mission.waypoints), "constraint_count": len(mission.constraints)})


def seth_guard(mission: MissionRecord) -> AgentReport:
    text = " ".join([mission.name, mission.objective, mission.environment, *mission.constraints]).lower()
    hits = [term for term in BLOCKED_TERMS if term in text]
    if hits:
        return _report("seth-guard-v1.0", "Seth Guard", "blocked",
                       "Mission request contains language that conflicts with the sandbox safety policy.",
                       ["The plan is blocked pending human review.", "This keyword screen is intentionally conservative."],
                       {"matched_terms": hits, "policy_version": "sandbox-policy-1"})
    return _report("seth-guard-v1.0", "Seth Guard", "ok",
                   "No blocked phrase was detected by the basic policy screen.",
                   ["This is not a complete hazard analysis or flight-safety certification."],
                   {"policy_version": "sandbox-policy-1", "human_review_required_for_real_operations": True})


def thoth_strategy(mission: MissionRecord) -> AgentReport:
    objective = mission.objective.strip().rstrip(".")
    steps = [
        {"step": 1, "priority": "high", "action": "Confirm mission objective and measurable success criteria"},
        {"step": 2, "priority": "high", "action": "Validate constraints, assumptions, and operating boundaries"},
        {"step": 3, "priority": "medium", "action": f"Plan and evaluate: {objective}"},
        {"step": 4, "priority": "high", "action": "Review proposed plan against safety and mission constraints"},
        {"step": 5, "priority": "medium", "action": "Record outcomes and update the mission knowledge base"},
    ]
    return _report("thoth-strategy-v1.0", "Thoth Strategy", "ok", "Objective decomposed into reviewable planning stages.",
                   [item["action"] for item in steps], {"steps": steps})


def ra_pathfinder(mission: MissionRecord) -> AgentReport:
    # This is a sequence planner, not a physical trajectory solver.
    if mission.waypoints:
        route = [{"order": i + 1, "waypoint": point} for i, point in enumerate(mission.waypoints)]
        method = "user_supplied_sequence"
    else:
        route = [
            {"order": 1, "waypoint": "mission_start"},
            {"order": 2, "waypoint": "objective_assessment"},
            {"order": 3, "waypoint": "verification_checkpoint"},
            {"order": 4, "waypoint": "mission_review"},
        ]
        method = "default_stage_sequence"
    return _report("ra-pathfinder-v1.0", "Ra Pathfinder", "ok",
                   "A reviewable sequence has been prepared; no physical trajectory or propulsion calculation was performed.",
                   [f"{len(route)} ordered stages prepared.", "Confirm all waypoints and transitions with a qualified mission engineer."],
                   {"method": method, "route": route, "physical_navigation": False})


def sobek_archive(mission: MissionRecord, recent_event_count: int = 0) -> AgentReport:
    return _report("sobek-archive-v1.0", "Sobek Archive", "ok", "Mission context prepared for archival.",
                   ["The canonical mission snapshot and event history are stored locally in SQLite."],
                   {"mission_id": mission.id, "prior_event_count": recent_event_count, "retention": "local SQLite event ledger"})


def horus_vision(reports: list[AgentReport]) -> AgentReport:
    blocked = [r.agent_name for r in reports if r.status == "blocked"]
    failed = [r.agent_name for r in reports if r.status == "error"]
    status = "blocked" if blocked else ("warning" if failed else "ok")
    findings = []
    if blocked:
        findings.append("Coordination halted because a safety-policy agent blocked the request.")
    if failed:
        findings.append("One or more agents failed and require operator review.")
    if not blocked and not failed:
        findings.append("All required agents returned a report.")
    return _report("horus-vision-v1.0", "Horus Vision", status,
                   "Agent outputs consolidated into one mission assessment.", findings,
                   {"agents_considered": [r.agent_id for r in reports], "blocked_agents": blocked, "failed_agents": failed})


def run_agents(mission: MissionRecord, recent_event_count: int = 0) -> tuple[list[AgentReport], dict[str, Any]]:
    guide = anubis_guide(mission)
    guard = seth_guard(mission)
    reports = [guide, guard]
    if guard.status == "blocked":
        reports.append(horus_vision(reports))
        return reports, {"decision": "blocked", "reason": "Safety policy requires human review."}

    strategy = thoth_strategy(mission)
    pathfinder = ra_pathfinder(mission)
    archive = sobek_archive(mission, recent_event_count)
    reports.extend([strategy, pathfinder, archive])
    reports.append(horus_vision(reports))
    return reports, {
        "decision": "planning_only",
        "route": pathfinder.data.get("route", []),
        "strategy_steps": strategy.data.get("steps", []),
        "required_human_review": True,
        "execution_enabled": False,
        "notes": [
            "This plan is a software prototype output, not a flight-ready command sequence.",
            "No external model or physical hardware is contacted."
        ],
    }
