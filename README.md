# Camp Ads Agent

Camp Ads Agent is a mock-first advertising operations agent for GreenNode Claw-a-thon 2026.

The agent helps an ad operations team move from campaign brief to campaign setup, report analysis, and action alerts using synthetic data only.

## Core Flow

1. Parse campaign brief.
2. Upload and preview creative assets.
3. Recommend ad zones by objective, price, reach, and historical performance.
4. Map target audience to DMP segments and detect missing segment gaps.
5. Simulate campaign setup with budget split, bid, schedule, and zone plan.
6. Analyze mock campaign reports and classify records as good, watch, or bad.
7. Generate action alerts for AO/account teams.

## Architecture

The project follows a deterministic-first custom agent approach:

- FastAPI runtime with `GET /health` on port `8080`.
- Agent-style `POST /invocations` endpoint for local and container contract tests.
- Local mock data before any cloud deployment.
- Python business logic for scoring, DMP matching, budget split, and report thresholds.
- OpenAI-compatible MaaS/LLM adapter planned after the deterministic mock workflow is validated.
- AgentBase deployment only after local and Docker validation pass.

## Phase 1 Local Setup

Current implementation plan:

```text
plans/phase-02-prototype-alignment.md
```

Create a virtual environment and install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Generate sanitized mock data from local contest material:

```powershell
python scripts\extract_mock_data.py
```

Run the app:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080` for the mock UI.

Run tests:

```powershell
pytest -q
```

Run local HTTP smoke checks against a running server:

```powershell
python scripts\smoke_local.py --base-url http://127.0.0.1:8080
```

Run Docker build and container smoke checks after Docker Desktop is running:

```powershell
.\scripts\smoke_docker.ps1
```

## API Surface

- `GET /health` - runtime health check.
- `POST /invocations` - agent-style message endpoint for brief setup, report analysis, or AO alert routing.
- `POST /api/chat` - workspace chat alias for `POST /invocations`.
- `GET /api/context` - project, model, and baseline context.
- `GET /api/zones` - ad zone catalog.
- `POST /api/zones/recommend` - deterministic zone recommendations by objective.
- `GET /api/dmp/segments` - mock DMP segment catalog.
- `POST /api/dmp/match` - target-to-DMP segment matching and gap detection.
- `POST /api/creative/inspect` - upload and inspect creative metadata for the prototype.
- `POST /api/setup/plan` - full mock campaign setup plan from brief, creative, zones, and DMP.
- `GET /api/reports/summary` - 15-report baseline summary.
- `GET /api/reports/analyze` - good/watch/bad analysis and top records.
- `POST /api/alerts/ao` - AO/account action alert from bad-performing records.
- `POST /api/brief/parse` - mock brief parser for local development.

## Current Baseline

- 15 synthetic campaign reports.
- 480 campaign records.
- 99 good, 238 watch, 143 bad records.
- Total mock ROAS: 2.60x.

## Deployment Strategy

The project is developed and tested locally first. Deployment to GreenNode AgentBase is the final step after:

- Unit tests pass.
- API contract tests pass.
- UI flow works end to end.
- Docker build and health check pass.
