# Nile Gate

**A multi-agent mission-planning and coordination sandbox for Nile Galactic.**

Nile Gate is the orchestration layer for a family of mission-support agents. This first implementation turns the six documented agent roles into a working, inspectable Python service with a REST API, a persistent SQLite event ledger, mission planning, safety-policy screening, and tests.

> **Important scope boundary:** This is an early software prototype for planning and simulation. It does not connect to spacecraft, control hardware, calculate flight-certified trajectories, or issue commands to real missions. Outputs require qualified human review before any real-world use.

## Agent roster

| Agent | Responsibility in this MVP |
|---|---|
| **Anubis Guide v1.0** | Checks mission intake, scope, and completeness |
| **Horus Vision v1.0** | Coordinates agent outputs and produces the overall assessment |
| **Sobek Archive v1.0** | Records mission context and links work to event history |
| **Seth Guard v1.0** | Applies conservative safety-policy checks and can block a plan |
| **Ra Pathfinder v1.0** | Creates a reviewable sequence of mission stages; not a physics-based trajectory solver |
| **Thoth Strategy v1.0** | Breaks objectives into ordered, reviewable planning steps |

The first version deliberately uses deterministic agents rather than requiring external AI keys. This makes the execution path reproducible, inspectable, and testable. Model-backed reasoning can be added behind agent interfaces later, while policy checks and mission-state transitions remain explicit.

## Architecture

- **FastAPI** exposes the REST API and interactive OpenAPI documentation.
- **Mission service** owns lifecycle operations and orchestrates agents.
- **Agent layer** returns typed reports with summaries, findings, and structured data.
- **SQLite** stores mission snapshots and an append-only event history. The snapshot is a convenience; the event ledger records what happened.
- **Human review** remains required. A plan is a proposal, never an execution authorization.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
uvicorn nile_gate.api:app --reload
```

Then open:

- API health: http://127.0.0.1:8000/health
- Agent roster: http://127.0.0.1:8000/agents
- Interactive API docs: http://127.0.0.1:8000/docs

The SQLite database defaults to `data/nile_gate.db`. Override its location with `NILE_GATE_DB_PATH`.

## Try a mission

Create a mission:

```bash
curl -X POST http://127.0.0.1:8000/missions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Orbital Survey Demo",
    "objective": "Survey a simulated orbital region and summarize observations.",
    "environment": "simulation",
    "waypoints": ["simulation_start", "survey_region", "verification_checkpoint", "review"],
    "constraints": ["simulation only", "human review required"]
  }'
```

Copy the returned mission `id`, then plan it:

```bash
curl -X POST http://127.0.0.1:8000/missions/YOUR_MISSION_ID/plan
```

Useful endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health and operating mode |
| GET | `/agents` | Agent roster |
| POST | `/missions` | Create a mission draft |
| GET | `/missions` | List recent missions |
| GET | `/missions/{id}` | Inspect a mission |
| POST | `/missions/{id}/plan` | Run the agent workflow |
| GET | `/events` | Inspect the event ledger; optional `mission_id` filter |

## CLI demo

```bash
nile-gate agents
nile-gate demo
```

## Run tests

```bash
pytest
```

## Current limitations and next milestones

This is a functional MVP, not yet a full autonomous mission system.

1. **Mission contracts:** formal schemas for mission types, capabilities, resources, and success criteria.
2. **Stronger policy engine:** versioned policies, structured hazard analysis, approval gates, and adversarial tests. The current keyword screen is only a starter guardrail.
3. **Agent communication protocol:** typed task messages, timeouts, retries, and explicit conflict resolution.
4. **Archive evolution:** event replay, schema migrations, provenance, and controlled export/import.
5. **Simulation adapter:** a mock environment with measurable outcomes and repeatable test scenarios.
6. **Observability:** structured logs, metrics, trace IDs, and per-agent latency.
7. **Model adapters:** optional LLM-backed agents behind strict input/output contracts, without letting model output bypass Seth Guard or human approval.
8. **Deployment hardening:** authentication, authorization, secrets management, backups, rate limits, and operational security review.

## Repository structure

```text
nile-gate/
├── nile_gate/
│   ├── agents.py       # Six deterministic agents
│   ├── api.py          # FastAPI endpoints
│   ├── cli.py          # Local CLI
│   ├── models.py       # Typed mission and report schemas
│   ├── service.py      # Mission lifecycle and orchestration
│   └── store.py        # SQLite snapshots and event ledger
├── tests/
│   └── test_core.py
├── pyproject.toml
└── README.md
```

## Project principle

Nile Gate should make agent behavior **coordinated, traceable, constrained, and reviewable** before it becomes more autonomous. Each agent has a defined role; Horus Vision synthesizes the result; Seth Guard can block a plan; Sobek Archive preserves the event trail; and no agent can directly execute a real-world action in this MVP.
