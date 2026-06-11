from collections import Counter
from typing import Any


def summarize_reports(records: list[dict[str, Any]]) -> dict[str, Any]:
    verdicts = Counter(str(row.get("Verdict", "")).lower() for row in records)
    spend = sum(float(row.get("Spend VND") or 0) for row in records)
    revenue = sum(float(row.get("Revenue VND") or row.get("Revenue from Signup") or 0) for row in records)
    sheets = sorted({row.get("Sheet") for row in records if row.get("Sheet")})

    return {
        "total_records": len(records),
        "reports": len(sheets),
        "sheets": sheets,
        "verdict": {
            "good": verdicts.get("good", 0),
            "watch": verdicts.get("watch", 0),
            "bad": verdicts.get("bad", 0),
        },
        "total_spend_vnd": int(spend),
        "total_revenue_vnd": int(revenue),
        "total_roas": round(revenue / spend, 2) if spend else 0,
        "top_bad": _top_records(records, "bad", 10),
        "top_good": _top_records(records, "good", 10),
    }


def _top_records(records: list[dict[str, Any]], verdict: str, limit: int) -> list[dict[str, Any]]:
    filtered = [r for r in records if str(r.get("Verdict", "")).lower() == verdict]
    filtered.sort(key=lambda r: float(r.get("Spend VND") or 0), reverse=True)
    return [
        {
            "campaign_id": row.get("Campaign ID"),
            "brand": row.get("Brand"),
            "sheet": row.get("Sheet"),
            "zone": row.get("Zone"),
            "spend_vnd": row.get("Spend VND"),
            "roas": row.get("ROAS") or row.get("Signup ROAS") or row.get("Reactivation ROAS"),
            "hint": row.get("Agent Analysis Hint") or row.get("Agent Hint"),
        }
        for row in filtered[:limit]
    ]
