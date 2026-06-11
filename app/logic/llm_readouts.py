from __future__ import annotations

import json
from typing import Any

from app.llm import call_llm


def explain_setup(setup: dict[str, Any]) -> dict[str, Any]:
    return call_llm(
        "setup_explain",
        [
            {
                "role": "system",
                "content": "Explain a campaign setup plan in concise operator language. Do not recalculate numbers.",
            },
            {"role": "user", "content": _compact_json(setup, keep_keys=["brief", "dmp", "zones", "budget_split"])},
        ],
    )


def explain_dmp_match(dmp: dict[str, Any]) -> dict[str, Any]:
    return call_llm(
        "segment_explain",
        [
            {
                "role": "system",
                "content": "Explain DMP segment matches, gaps, and proxy choices. Keep the result concise.",
            },
            {"role": "user", "content": _compact_json(dmp, keep_keys=["matched", "gaps", "size_est", "explanation"])},
        ],
    )


def explain_report(summary: dict[str, Any]) -> dict[str, Any]:
    return call_llm(
        "report_explain",
        [
            {
                "role": "system",
                "content": "Explain campaign report performance from the provided deterministic verdicts. Do not change counts.",
            },
            {"role": "user", "content": _compact_json(summary, keep_keys=["total_records", "reports", "verdict", "total_roas", "top_bad", "top_good"])},
        ],
    )


def draft_ao_alert(alert: dict[str, Any]) -> dict[str, Any]:
    return call_llm(
        "ao_alert",
        [
            {
                "role": "system",
                "content": "Draft a concise AO/account alert from the provided deterministic priority records.",
            },
            {"role": "user", "content": _compact_json(alert, keep_keys=["subject", "priority_records", "summary"])},
        ],
    )


def _compact_json(data: dict[str, Any], *, keep_keys: list[str]) -> str:
    compact = {key: data.get(key) for key in keep_keys if key in data}
    return json.dumps(compact, ensure_ascii=False, default=str)
