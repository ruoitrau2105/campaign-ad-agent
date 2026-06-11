import re
import unicodedata
from typing import Any

from app.llm import get_model_route
from app.logic.alert_builder import build_ao_alert
from app.logic.brief_parser import parse_brief_mock
from app.logic.llm_readouts import draft_ao_alert, explain_report, explain_setup
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
            "model_route": get_model_route("chat_orchestration").public_dict(),
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
        alert["llm_readout"] = draft_ao_alert(alert)
        return {
            "action": "ao_alert",
            "reply": alert["subject"],
            "model_route": get_model_route("ao_alert").public_dict(),
            "result": alert,
        }

    if _has_any(normalized, ["report", "analyze", "analysis", "phan tich"]):
        summary = summarize_reports(reports)
        summary["llm_readout"] = explain_report(summary)
        return {
            "action": "report_analysis",
            "reply": (
                f"Analyzed {summary['total_records']} records across {summary['reports']} reports. "
                f"ROAS is {summary['total_roas']:.2f}x."
            ),
            "model_route": get_model_route("report_explain").public_dict(),
            "result": summary,
        }

    brief = parse_brief_mock(clean_message)
    setup = build_setup_plan(brief, zones, dmp_segments, creative, top_n)
    setup["llm_readout"] = explain_setup(setup)
    return {
        "action": "setup_plan",
        "reply": setup["readout"],
        "model_routes": {
            "chat_orchestration": get_model_route("chat_orchestration").public_dict(),
            "brief_parse": get_model_route("brief_parse").public_dict(),
            "segment_explain": get_model_route("segment_explain").public_dict(),
            "setup_explain": get_model_route("setup_explain").public_dict(),
        },
        "result": setup,
    }


def _has_any(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"(^|\W){re.escape(term)}($|\W)", text) for term in terms)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
