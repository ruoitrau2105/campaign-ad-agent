---
title: "Camp Ads Agent Roadmap"
status: active
updated: 2026-06-11
owner: "Pawgrammers"
scope: "Mock-first local agent, then GreenNode AgentBase cloud"
---

# Camp Ads Agent Roadmap

## Purpose

This roadmap is the persistent source of truth for the Camp Ads Agent build. It keeps the project recoverable across Codex sessions and separates local mock validation from GreenNode AgentBase deployment.

Camp Ads Agent automates the campaign ads lifecycle on synthetic data:

1. Receive and parse campaign brief.
2. Upload and inspect creative material.
3. Recommend ad zones by objective, price, reach, and performance.
4. Map target audience to DMP segments and identify gaps or proxy segments.
5. Draft campaign setup with budget, bid, schedule, zone plan, and DMP mapping.
6. Analyze mock campaign reports.
7. Generate AO/account alerts for weak-performing campaigns.

## Current State

| Area | State |
| --- | --- |
| Repo | `https://github.com/ruoitrau2105/campaign-ad-agent` |
| Runtime | FastAPI custom agent on port `8080` |
| UI | Split `CHAT` + `WORKSPACE` prototype flow |
| Data baseline | 15 reports, 480 campaign records |
| Report baseline | 99 good, 238 watch, 143 bad, total ROAS 2.60x |
| Test baseline | `pytest -q` and `scripts/smoke_local.py` pass |
| Docker baseline | Docker smoke has passed locally |
| Model adapter | OpenAI-compatible adapter with mock fallback is implemented |
| Cloud deploy | Not started; intentionally after local/eval gates |

## Phase Overview

| Phase | Name | Status | Priority | Gate |
| --- | --- | --- | --- | --- |
| 0 | Context and Repo Setup | Completed | P1 | Repo, skills, material context ready |
| 1 | Local Mock Agent Base | Completed | P1 | FastAPI, mock APIs, tests, Docker smoke ready |
| 2 | Prototype Alignment | In progress | P1 | Split chat/workspace progressive flow matches prototype direction |
| 3 | Model Adapter and Agent Logic | Completed | P1 | OpenAI-compatible model adapter with task-to-model routing |
| 4 | Eval and Quality Gate | Pending | P1 | Golden cases pass parity and stability thresholds |
| 5 | AgentBase Cloud Deploy | Pending | P1 | Runtime deployed and health verified on GreenNode AgentBase |
| 6 | Demo and Submission Polish | Pending | P2 | Demo script, video, README/runbook, final freeze |

## Phase 0: Context and Repo Setup

Status: Completed

### Delivered

- Read project material from `clawathon_material`.
- Installed GreenNode AgentBase skills from the official skill pack.
- Created GitHub repository.
- Confirmed project direction: mock-first local build, AgentBase deployment later.
- Confirmed core product adjustment: automate campaign lifecycle, not just suggest actions.

### Acceptance

- Project context is available in repo.
- Team can continue from GitHub without relying on chat memory.
- AgentBase skill pack is installed locally.

## Phase 1: Local Mock Agent Base

Status: Completed

### Delivered

- FastAPI app with `GET /health`.
- Agent-style `POST /invocations` endpoint.
- Local API surface:
  - `POST /api/brief/parse`
  - `POST /api/creative/inspect`
  - `GET /api/zones`
  - `POST /api/zones/recommend`
  - `GET /api/dmp/segments`
  - `POST /api/dmp/match`
  - `POST /api/setup/plan`
  - `GET /api/reports/summary`
  - `GET /api/reports/analyze`
  - `POST /api/alerts/ao`
- Deterministic business logic for zone scoring, DMP matching, setup planning, report verdicts, and alerts.
- Local smoke script and Docker smoke script.
- Unit tests for API and core contracts.

### Acceptance

- `pytest -q` passes.
- `python scripts/smoke_local.py --base-url http://127.0.0.1:8080` passes against a running server.
- `scripts/smoke_docker.ps1` passes when Docker Desktop is available.
- No production API dependency exists.

## Phase 2: Prototype Alignment

Status: In progress

Detailed plan: `plans/phase-02-prototype-alignment.md`

### Goal

Make the local UI follow `Camp_Ads_Agent_Prototype_v2.html`: left side is `CHAT`, right side is `WORKSPACE`, and the user moves through one step at a time.

### Delivered So Far

- Replaced earlier all-in-one test workspace with split `CHAT` + `WORKSPACE`.
- Flow now advances step by step:
  - `Brief`
  - `Creative`
  - `Zones`
  - `DMP`
  - `Setup`
  - `Report`
  - `Alert`
- Creative step supports upload/check material instead of creative suggestion.
- Setup flow is decomposed into zone recommendation, DMP mapping, and final setup plan.
- UI copy is mostly Vietnamese while preserving required English terms:
  - `Campaign Ads Agent`
  - `CHAT`
  - `WORKSPACE`
  - process names such as `Brief`, `Creative`, `Zones`, `DMP`, `Setup`, `Report`, `Alert`
- Removed unwanted labels:
  - `Split Chat + Workspace`
  - `progressive disclosure`
  - old Vietnamese topbar tagline about step-by-step mock data flow
  - duplicate green `Chat` text beside the `CHAT` badge

### Remaining Work

- Check the UI against `Camp_Ads_Agent_Prototype_v2.html` one more time for layout and flow gaps.
- Add small UX polish only where it improves clarity or demo flow.
- Keep the page lightweight and demo-safe.

### Acceptance

- User can complete the full flow without entering every input upfront.
- Future steps remain visually locked until prior steps complete.
- Workspace state and chat state stay in sync.
- Existing local API contracts remain stable.
- `pytest -q` passes.
- `scripts/smoke_local.py` passes.

## Phase 3: Model Adapter and Agent Logic

Status: Completed

Detailed plan: `plans/phase-03-model-adapter.md`

### Goal

Add a single OpenAI-compatible model adapter while preserving deterministic-first behavior. Business decisions stay in Python; LLMs handle natural-language parsing, explanation, and alert writing.

### Model Direction

Use the current contest model names from the user:

| Task | Preferred Model |
| --- | --- |
| Chat orchestration | Qwen 3.5 27B |
| Brief parsing | Qwen 3.5 27B |
| Segment explanation | Gemma 4 31B-IT |
| Setup explanation | Gemma 4 31B-IT |
| Report explanation | Gemma 4 31B-IT |
| AO/account alert drafting | Qwen 3.5 27B |
| Heavy dev/code generation support | MiniMax M2.5 |

### Implementation Targets

- Create a single model boundary: `app/llm.py`.
- Add task-to-model config: `config/models.json`.
- Support env-based config:
  - `MAAS_BASE_URL` or `LLM_BASE_URL`
  - `MAAS_API_KEY` or `LLM_API_KEY`
  - task-specific model names
- Add JSON contract helpers:
  - low temperature
  - schema-guided prompts
  - parse failure handling
  - repair retry if needed
- Keep mock/deterministic fallback available so demos do not fail when model credentials are absent.

### Delivered

- `config/models.json` maps each task to the model that fits its role.
- `app/llm.py` provides OpenAI-compatible `call_llm` and `call_llm_json`.
- Live mode is opt-in through env; mock fallback is the default.
- `/api/context` exposes current model routing without secrets.
- Setup, DMP, report, AO alert, and invocation responses include additive LLM route/readout metadata.
- Tests cover routing, env override, mock fallback, context safety, and invocation route metadata.

### Acceptance

- [x] App still runs without cloud keys in mock mode.
- [x] Model adapter can be enabled by env/config only.
- [x] No API keys are committed.
- [x] Tests cover adapter fallback and task routing.
- [x] Core deterministic results do not regress.

## Phase 4: Eval and Quality Gate

Status: Pending

### Goal

Create an eval gate before any AgentBase cloud deployment. This prevents deploying a visually polished app that fails model reliability.

### Eval Targets

- Golden set for:
  - brief parsing
  - zone recommendation explanation
  - DMP segment mapping
  - setup plan explanation
  - report analysis
  - AO/account alert drafting
- Suggested thresholds:
  - JSON valid rate: at least 90%
  - deterministic field accuracy: at least 99%
  - LLM field match: at least 85%
  - no fatal runtime errors across repeated demo runs

### Implementation Targets

- Add `evals/cases.jsonl`.
- Add `evals/run.py`.
- Add report output under `evals/results/` or `plans/reports/`.
- Add Make/PowerShell command or README command for running eval.

### Acceptance

- Eval command runs locally.
- Results are reproducible enough for demo confidence.
- Any failing cases are documented with mitigation:
  - adjust prompt
  - add few-shot
  - move logic to Python
  - change task model

## Phase 5: AgentBase Cloud Deploy

Status: Pending

### Goal

Deploy only after local, Docker, and eval gates pass.

### AgentBase Path

Use the Custom Agent path:

- Container listens on `0.0.0.0:8080`.
- `GET /health` returns `200`.
- Secrets are provided through environment or AgentBase identity/key management.
- No production AdServer/DMP API is called.

### Implementation Targets

- Verify Dockerfile for linux/amd64.
- Build final image.
- Push to the required registry if AgentBase flow requires it.
- Deploy with GreenNode AgentBase deploy skill.
- Monitor runtime logs and health.
- Record runtime ID, endpoint, image tag, and deploy notes in a deploy log.

### Acceptance

- AgentBase runtime is `ACTIVE`.
- Cloud endpoint `/health` passes.
- Invocation endpoint works with a smoke request.
- Logs show no startup crash or missing env.
- README has the final cloud run instructions.

## Phase 6: Demo and Submission Polish

Status: Pending

### Goal

Prepare a voting-friendly demo package. The demo should make the value obvious within 15-30 seconds and show measurable impact.

### Demo Story

Recommended demo sequence:

1. Paste or use a campaign brief.
2. Upload/check creative.
3. Show objective-based zone recommendation with price and performance.
4. Show DMP match and gap/proxy handling.
5. Generate setup plan.
6. Analyze 15 reports / 480 rows.
7. Generate AO/account alert from bad-performing campaigns.

### Implementation Targets

- Freeze demo data.
- Add a short demo script.
- Add screenshots or video notes.
- Polish README and runbook.
- Confirm submission assets:
  - repo URL
  - local/cloud URL if required
  - video
  - brief description
  - limitation note: synthetic data only

### Acceptance

- A teammate can run the demo from README without asking the builder.
- Demo path is stable across repeated runs.
- Final submission tells the story in simple business terms.

## Global Definition of Done

Before considering the project ready for submission:

- `pytest -q` passes.
- Local smoke passes.
- Docker smoke passes.
- Eval gate passes or known limitations are documented.
- AgentBase cloud health check passes if cloud deploy is in scope for the submitted version.
- No secrets are committed.
- README and this roadmap reflect the latest state.
- Demo script matches the actual UI and API behavior.

## Session Continuity Checklist

At the start of a new session:

1. Read this file: `plans/roadmap.md`.
2. Check the current phase and next pending acceptance criteria.
3. Run `git status --short --untracked-files=all`.
4. Read the relevant phase file if one exists.
5. Run the smallest relevant verification command before editing.

Useful commands:

```powershell
git status --short --untracked-files=all
pytest -q
python scripts\smoke_local.py --base-url http://127.0.0.1:8080
.\scripts\smoke_docker.ps1
```

## Known Untracked Local Files

- `image_feedback/camp_ads.png` is a local feedback image and should not be committed unless explicitly requested.
