from app.schemas import BriefTarget, CampaignBrief


def parse_brief_mock(text: str) -> CampaignBrief:
    lowered = text.lower()

    if any(token in lowered for token in ["conversion", "lead", "cpl", "roas", "đơn hàng", "form"]):
        funnel = "conversion"
        kpi = ["CR", "CPL", "ROAS"]
    elif any(token in lowered for token in ["consideration", "traffic", "engagement", "landing"]):
        funnel = "consideration"
        kpi = ["CTR", "CPC", "Landing Visit Rate"]
    elif any(token in lowered for token in ["retention", "loyalty", "reactivation", "tái kích hoạt"]):
        funnel = "retention"
        kpi = ["Repeat Rate", "CPA", "ROAS"]
    else:
        funnel = "awareness"
        kpi = ["Reach", "CPM", "VTR"]

    brand = "Demo Brand"
    for marker in ["brand:", "brand ", "nhãn hàng:"]:
        if marker in lowered:
            start = lowered.index(marker) + len(marker)
            candidate = text[start:].splitlines()[0].strip(" -:|")
            if candidate:
                brand = candidate[:80]
            break

    interests = []
    interest_map = {
        "travel": ["Travel", "Air travel", "Hotels"],
        "du lịch": ["Travel", "Air travel", "Hotels"],
        "insurance": ["Insurance", "Finance", "Health"],
        "bảo hiểm": ["Insurance", "Finance", "Health"],
        "finance": ["Finance"],
        "tài chính": ["Finance"],
        "beauty": ["Beauty"],
        "retail": ["Retail shoppers"],
    }
    for key, values in interest_map.items():
        if key in lowered:
            interests.extend(values)

    return CampaignBrief(
        brand=brand,
        objective=text.strip()[:180] or "Mock campaign objective",
        funnel_stage=funnel,  # type: ignore[arg-type]
        target=BriefTarget(interests=sorted(set(interests))),
        budget_vnd=_extract_budget_vnd(lowered),
        kpi=kpi,
        formats=["banner", "native", "video"],
    )


def _extract_budget_vnd(text: str) -> int | None:
    import re

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(m|mn|million|triệu|ty|tỷ|billion)", text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit in {"ty", "tỷ", "billion"}:
        return int(value * 1_000_000_000)
    return int(value * 1_000_000)
