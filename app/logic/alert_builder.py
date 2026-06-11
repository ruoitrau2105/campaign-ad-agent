from typing import Any

from app.logic.report_analyzer import summarize_reports


def build_ao_alert(records: list[dict[str, Any]], max_items: int = 8) -> dict[str, Any]:
    summary = summarize_reports(records)
    bad = summary["top_bad"][:max_items]
    watch_count = summary["verdict"]["watch"]
    bad_count = summary["verdict"]["bad"]
    good_count = summary["verdict"]["good"]

    subject = f"[Camp Ads Agent] {bad_count} bad records need AO action"
    body_lines = [
        "Hi AO team,",
        "",
        f"Agent analyzed {summary['total_records']} records across {summary['reports']} reports.",
        f"Verdict split: {good_count} good / {watch_count} watch / {bad_count} bad.",
        f"Total ROAS: {summary['total_roas']:.2f}x.",
        "",
        "Priority actions:",
    ]
    for row in bad:
        body_lines.append(
            f"- Pause or review {row['campaign_id']} ({row['brand']}, {row['zone']}): {row.get('hint') or 'Bad performance signal.'}"
        )
    body_lines.extend(
        [
            "",
            "Recommended next step: pause high-spend bad records, move budget to good records, and A/B test watch group creatives.",
            "",
            "Camp Ads Agent",
        ]
    )
    return {
        "subject": subject,
        "body": "\n".join(body_lines),
        "priority_records": bad,
        "summary": {
            "records": summary["total_records"],
            "reports": summary["reports"],
            "verdict": summary["verdict"],
            "total_roas": summary["total_roas"],
        },
    }
