# Phase 02 - Prototype Alignment

## Problem

The current local UI is a test workspace, not the provided `Camp_Ads_Agent_Prototype_v2.html` direction. It exposes too many controls at once and does not clearly separate chat from the operational workspace.

## Target UX

- Match the prototype structure: left pane is Chat UI, right pane is Workspace.
- Use progressive disclosure: show one active step at a time, with locked future steps.
- Each step has one primary action and a clear approval/continue path.
- Workspace state and chat state stay in sync.
- Creative flow is upload/check material, not creative suggestion.
- Setup is split into zone recommendation, DMP mapping, and final campaign setup.

## Step Flow

1. Brief: paste or edit client brief, parse to structured fields.
2. Creative: upload creative and inspect metadata.
3. Zones: recommend ad zones by objective, price, and performance.
4. DMP: map target to DMP segments and show gaps/proxies.
5. Setup: create campaign draft plan from brief, creative, zones, and DMP.
6. Report: analyze 15 mock reports / 480 campaign records.
7. Alert: build AO/account alert from bad-performing records.

## Acceptance Criteria

- `GET /` renders split layout with `CHAT` and `WORKSPACE` panes.
- User can complete the flow one step at a time without filling every input upfront.
- Future steps are visually locked until prior steps complete.
- Buttons call real local APIs, not hardcoded-only mock outputs.
- Existing API contracts remain stable.
- `pytest -q` passes.
- `scripts/smoke_local.py` passes against the running local server.

## Out Of Scope

- AgentBase cloud deployment.
- Real GreenNode MaaS calls.
- Production AdServer/DMP integration.
- Full visual parity with Figma; this phase targets functional parity with the HTML prototype direction.
