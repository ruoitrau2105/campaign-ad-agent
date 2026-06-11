# Phase 04 - Eval and Quality Gate

## Problem

Before deploying to AgentBase, the project needs a repeatable gate that proves the mock-first workflow still behaves correctly. Unit tests cover code contracts, but the demo also needs golden business cases that validate the campaign lifecycle from brief to AO alert.

## Target

- Add a golden eval set with enough coverage for the current demo flow.
- Run evals locally without MaaS credentials.
- Measure quality using explicit thresholds.
- Generate machine-readable and human-readable reports.
- Fail the command when the quality gate does not pass.

## Eval Coverage

The golden set has 18 cases in `evals/cases.jsonl`:

- Brief parsing: awareness, conversion, consideration, retention.
- Zone recommendation: awareness, consideration, conversion.
- DMP matching: gap case, no-gap travel case, empty target.
- Setup plan: conversion and awareness budget flows.
- Report analysis: baseline counts and top-bad shape.
- AO alert: default and limited-item alert.
- Invocation routing: setup and AO alert.

## Metrics

The runner in `evals/run.py` reports:

| Metric | Threshold |
| --- | --- |
| JSON valid rate | >= 90% |
| Deterministic field accuracy | >= 99% |
| Model route match | >= 85% |
| Fatal errors | 0 |

Current mock-first result:

```text
Eval PASS: 18/18 cases, field accuracy 100.00%, JSON valid 100.00%, route match 100.00%
```

## Commands

Run the eval gate:

```powershell
python evals\run.py
```

Generated reports are written to `evals/results/latest.json` and `evals/results/latest.md`. The results directory is ignored by git.

## Acceptance Criteria

- `python evals\run.py` passes.
- `pytest -q` includes the eval gate test and passes.
- Generated eval result files are not committed.
- Eval cases cover every demo-critical workflow.
- Failures explain which case/check failed.

## Out Of Scope

- Live MaaS parity scoring.
- Human review of generated LLM prose quality.
- AgentBase cloud deployment.
- Production API validation.
