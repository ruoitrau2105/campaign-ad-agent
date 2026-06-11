import re
import unicodedata
from typing import Any

from app.logic.alert_builder import build_ao_alert
from app.logic.brief_parser import parse_brief_mock
from app.logic.report_analyzer import summarize_reports
from app.logic.setup_planner import build_setup_plan


def run_invocation(
    message: str,
    zones: list[dict[str, Any]],
    dmp_segments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    creative: dict[str, Any] | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    clean_message = message.strip()
    if not clean_message:
        return {
            "action": "guidance",
            "reply": "Send a campaign brief, ask to analyze reports, or ask for an AO alert.",
            "result": {
                "examples": [
                    "Setup ShieldCare lead campaign, budget 150 trieu, target bao hiem suc khoe",
                    "Analyze campaign reports",
                    "Create AO alert",
                ]
            },
        }

    normalized = _normalize(clean_message)
    if _has_any(normalized, ["alert", "ao", "warning", "canh bao"]):
        alert = build_ao_alert(reports)
        return {
            "action": "ao_alert",
            "reply": alert["subject"],
            "result": alert,
        }

    if _has_any(normalized, ["report", "analyze", "analysis", "phan tich"]):
        summary = summarize_reports(reports)
        return {
            "action": "report_analysis",
            "reply": (
                f"Analyzed {summary['total_records']} records across {summary['reports']} reports. "
                f"ROAS is {summary['total_roas']:.2f}x."
            ),
            "result": summary,
        }

    brief = parse_brief_mock(clean_message)
    setup = build_setup_plan(brief, zones, dmp_segments, creative, top_n)
    return {
        "action": "setup_plan",
        "reply": setup["readout"],
        "result": setup,
    }


def _has_any(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"(^|\W){re.escape(term)}($|\W)", text) for term in terms)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
