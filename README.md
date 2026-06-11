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
- Local mock data before any cloud deployment.
- Python business logic for scoring, DMP matching, budget split, and report thresholds.
- A single OpenAI-compatible LLM adapter for brief parsing, explanations, and alert drafting.
- AgentBase deployment only after local and Docker validation pass.

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

