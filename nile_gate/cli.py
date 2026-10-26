"""Small CLI for local health checks and mission planning."""
from __future__ import annotations

import argparse
import json

from nile_gate.models import MissionCreate
from nile_gate.service import MissionService


def main() -> None:
    parser = argparse.ArgumentParser(prog="nile-gate", description="Nile Gate planning-only multi-agent sandbox")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("agents", help="List the registered agents")
    create = sub.add_parser("demo", help="Create and plan a demonstration mission")
    create.add_argument("--name", default="Orbital Survey Demo")
    create.add_argument("--objective", default="Survey a simulated orbital region and return a verified observation summary.")
    args = parser.parse_args()
    service = MissionService()
    if args.command == "agents":
        print(json.dumps(service.agents(), indent=2))
        return
    mission = service.create(MissionCreate(name=args.name, objective=args.objective, environment="simulation",
                                           waypoints=["simulation_start", "survey_region", "verification_checkpoint", "review"]))
    planned = service.plan(mission.id)
    print(planned.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
