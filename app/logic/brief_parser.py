import re
import unicodedata

from app.schemas import BriefTarget, CampaignBrief


def parse_brief_mock(text: str) -> CampaignBrief:
    normalized = _normalize(text)

    if any(token in normalized for token in ["conversion", "lead", "cpl", "roas", "don hang", "form"]):
        funnel = "conversion"
        kpi = ["CR", "CPL", "ROAS"]
    elif any(token in normalized for token in ["consideration", "traffic", "engagement", "landing"]):
        funnel = "consideration"
        kpi = ["CTR", "CPC", "Landing Visit Rate"]
    elif any(token in normalized for token in ["retention", "loyalty", "reactivation", "tai kich hoat"]):
        funnel = "retention"
        kpi = ["Repeat Rate", "CPA", "ROAS"]
    else:
        funnel = "awareness"
        kpi = ["Reach", "CPM", "VTR"]

    brand = "Demo Brand"
    for marker in ["brand:", "brand ", "nhan hang:"]:
        if marker in normalized:
            start = normalized.index(marker) + len(marker)
            candidate = re.split(r"[\n.,;|]", text[start:], maxsplit=1)[0].strip(" -:")
            if candidate:
                brand = candidate[:80]
            break

    interests = []
    interest_map = {
        "travel": ["Travel", "Air travel", "Hotels"],
        "du lich": ["Travel", "Air travel", "Hotels"],
        "insurance": ["Insurance", "Finance", "Health"],
        "bao hiem": ["Insurance", "Finance", "Health"],
        "finance": ["Finance"],
        "tai chinh": ["Finance"],
        "health": ["Health"],
        "suc khoe": ["Health"],
        "beauty": ["Beauty"],
        "retail": ["Retail shoppers"],
    }
    for key, values in interest_map.items():
        if key in normalized:
            interests.extend(values)

    return CampaignBrief(
        brand=brand,
        objective=text.strip()[:180] or "Mock campaign objective",
        funnel_stage=funnel,  # type: ignore[arg-type]
        target=BriefTarget(interests=sorted(set(interests))),
        budget_vnd=_extract_budget_vnd(normalized),
        kpi=kpi,
        formats=["banner", "native", "video"],
    )


def _extract_budget_vnd(text: str) -> int | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(m|mn|million|trieu|ti|ty|billion)", text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit in {"ti", "ty", "billion"}:
        return int(value * 1_000_000_000)
    return int(value * 1_000_000)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
