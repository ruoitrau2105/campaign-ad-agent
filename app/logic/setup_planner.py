from typing import Any

from app.logic.dmp_match import match_dmp_segments
from app.logic.zone_scoring import recommend_zones
from app.schemas import CampaignBrief


def build_setup_plan(
    brief: CampaignBrief,
    zones: list[dict[str, Any]],
    dmp_segments: list[dict[str, Any]],
    creative: dict[str, Any] | None,
    top_n: int = 5,
) -> dict[str, Any]:
    zone_recommendations = recommend_zones(zones, brief.funnel_stage, top_n)
    dmp = match_dmp_segments(brief.target, dmp_segments)
    budget_split = _split_budget(brief.budget_vnd, zone_recommendations)
    campaigns = _draft_campaigns(brief, zone_recommendations, budget_split, creative)

    return {
        "brief": brief.model_dump(),
        "creative": creative or {"status": "missing", "message": "Creative can be uploaded later."},
        "dmp": dmp,
        "zones": zone_recommendations,
        "budget_split": budget_split,
        "campaigns": campaigns,
        "schedule": brief.flight or "Run full flight from brief; default pacing is even daily delivery.",
        "bid_strategy": _bid_strategy(brief.funnel_stage),
        "readout": _readout(brief, dmp, zone_recommendations),
    }


def _split_budget(budget_vnd: int | None, zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not zones:
        return []
    total_score = sum(float(zone["score"]) for zone in zones) or len(zones)
    budget = budget_vnd or 100_000_000
    rows = []
    allocated = 0
    for index, zone in enumerate(zones):
        if index == len(zones) - 1:
            amount = budget - allocated
        else:
            amount = int(budget * (float(zone["score"]) / total_score))
            allocated += amount
        rows.append(
            {
                "zone_id": zone["zone_id"],
                "share_pct": round(amount / budget * 100, 1),
                "budget_vnd": amount,
                "expected_cpm_vnd": zone["cpm_vnd"],
            }
        )
    return rows


def _draft_campaigns(
    brief: CampaignBrief,
    zones: list[dict[str, Any]],
    budget_split: list[dict[str, Any]],
    creative: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    creative_name = (creative or {}).get("filename", "creative-pending")
    return [
        {
            "campaign_id": f"DRAFT-{idx:03d}",
            "name": f"{brief.brand} · {brief.funnel_stage} · {zone['zone_id']}",
            "zone_id": zone["zone_id"],
            "format": zone["format"],
            "creative": creative_name,
            "budget_vnd": budget_split[idx - 1]["budget_vnd"],
            "status": "draft",
        }
        for idx, zone in enumerate(zones[:3], start=1)
    ]


def _bid_strategy(objective: str) -> str:
    if objective == "awareness":
        return "CPM bidding, prioritize high VI and large-format placements."
    if objective == "consideration":
        return "CPC/optimized CPM blend, prioritize CTR and landing visit quality."
    if objective == "retention":
        return "CPA/ROAS guardrail, prioritize CRM and loyalty audiences."
    return "CPA/CPL guardrail, prioritize high CTR and efficient CPM placements."


def _readout(brief: CampaignBrief, dmp: dict[str, Any], zones: list[dict[str, Any]]) -> str:
    top_zone = zones[0]["zone_id"] if zones else "no zone"
    gap_text = f"{len(dmp['gaps'])} DMP gaps" if dmp["gaps"] else "no DMP gap"
    return f"{brief.brand}: setup uses {top_zone} as leading zone, estimated audience {dmp['size_est']:,}, {gap_text}."
