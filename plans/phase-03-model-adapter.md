# Phase 03 - Model Adapter and Agent Logic

## Problem

The local agent has strong deterministic mock logic, but it needs a clean model boundary before moving toward GreenNode MaaS and AgentBase. Without this boundary, model choices would be scattered through business logic and hard to swap during the contest.

## Target Architecture

- Keep deterministic Python logic as the source of truth for scoring, DMP matching, budget split, report verdicts, and campaign setup.
- Add one OpenAI-compatible adapter in `app/llm.py`.
- Keep model routing in `config/models.json`.
- Allow task-specific model path overrides through environment variables.
- Default to mock fallback so local demo and tests do not require cloud credentials.
- Only use live model calls when `CAMP_ADS_LLM_MODE=live` or equivalent and an API key is configured.

## Model Routing

| Task | Model | Why |
| --- | --- | --- |
| `chat_orchestration` | Qwen 3.5 27B | Fast chat routing, Vietnamese/English operator guidance |
| `brief_parse` | Qwen 3.5 27B | Natural brief to structured JSON |
| `segment_explain` | Gemma 4 31B-IT | DMP segment reasoning, gaps, proxy explanation |
| `setup_explain` | Gemma 4 31B-IT | Structured campaign setup explanation |
| `report_explain` | Gemma 4 31B-IT | Report interpretation over deterministic verdicts |
| `ao_alert` | Qwen 3.5 27B | Concise AO/account alert drafting |
| `developer_support` | MiniMax M2.5 | Build-time code generation/support only, not runtime demo path |

## Environment Contract

Provider defaults to GreenNode AI Platform:

```text
https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
```

Supported environment variables:

```text
CAMP_ADS_LLM_MODE=mock|live
MAAS_BASE_URL or LLM_BASE_URL
MAAS_API_KEY or LLM_API_KEY
LLM_MODEL_CHAT_ORCHESTRATION
LLM_MODEL_BRIEF_PARSE
LLM_MODEL_SEGMENT_EXPLAIN
LLM_MODEL_SETUP_EXPLAIN
LLM_MODEL_REPORT_EXPLAIN
LLM_MODEL_AO_ALERT
LLM_MODEL_DEVELOPER_SUPPORT
```

The `LLM_MODEL_*` values should use the GreenNode model `path` once confirmed in the model catalog. The committed config keeps human-readable model names as safe defaults.

## Delivered

- `config/models.json` defines provider settings, task routes, model strengths, temperature, runtime flag, and output type.
- `app/llm.py` provides:
  - `get_model_route`
  - `routing_snapshot`
  - `call_llm`
  - `call_llm_json`
  - safe mock fallback
- `/api/context` exposes the current LLM routing snapshot.
- Setup, DMP, report, AO alert, and invocation responses include route/readout metadata without replacing deterministic output.
- Tests cover model routing, env override, mock fallback, safe context snapshot, and invocation route metadata.

## Acceptance Criteria

- `pytest -q` passes.
- `scripts/smoke_local.py` passes against the running local server.
- App runs without LLM credentials.
- No secret values are committed or printed by context responses.
- Model route selection matches the task strengths table.
- Existing API contracts remain backwards-compatible; new LLM fields are additive.

## Out Of Scope

- Creating or storing GreenNode API keys.
- Listing or enabling live GreenNode models.
- Running eval parity gates.
- Deploying to AgentBase cloud.
- Replacing deterministic business decisions with LLM output.
