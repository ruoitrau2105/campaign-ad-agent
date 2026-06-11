from typing import Any


def recommend_zones(zones: list[dict[str, Any]], objective: str, top_n: int = 5) -> list[dict[str, Any]]:
    scored = []
    reach_values = [float(z.get("reach", 0) or 0) for z in zones]
    cpm_values = [float(z.get("cpm_vnd", 0) or 0) for z in zones]
    area_values = [_size_area(str(z.get("size", ""))) for z in zones]

    for zone in zones:
        reach_norm = _norm(float(zone.get("reach", 0) or 0), reach_values)
        cpm_norm = _norm(float(zone.get("cpm_vnd", 0) or 0), cpm_values)
        area_norm = _norm(_size_area(str(zone.get("size", ""))), area_values)
        vi = float(zone.get("vi_pct", 0) or 0) / 100
        ctr = float(zone.get("ctr_pct", 0) or 0) / 100

        if objective == "awareness":
            score = 0.5 * vi + 0.3 * reach_norm + 0.2 * area_norm
        elif objective == "consideration":
            score = 0.4 * ctr + 0.3 * vi + 0.3 * (1 - cpm_norm)
        else:
            score = 0.6 * ctr + 0.4 * (1 - cpm_norm)

        scored.append(
            {
                **zone,
                "score": round(score, 4),
                "fit_reason": _reason(objective, zone),
            }
        )

    return sorted(scored, key=lambda z: z["score"], reverse=True)[:top_n]


def _norm(value: float, values: list[float]) -> float:
    if not values:
        return 0
    low = min(values)
    high = max(values)
    if high == low:
        return 1
    return (value - low) / (high - low)


def _size_area(size: str) -> float:
    try:
        width, height = size.lower().split("x", 1)
        return float(width) * float(height)
    except Exception:
        return 0


def _reason(objective: str, zone: dict[str, Any]) -> str:
    if objective == "awareness":
        return f"VI {zone.get('vi_pct')}%, reach {zone.get('reach')}, large-format fit."
    if objective == "consideration":
        return f"Balanced CTR {zone.get('ctr_pct')}%, VI {zone.get('vi_pct')}%, CPM {zone.get('cpm_vnd')}."
    return f"Conversion fit from CTR {zone.get('ctr_pct')}% and CPM {zone.get('cpm_vnd')}."
