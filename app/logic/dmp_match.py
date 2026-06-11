from typing import Any

from app.schemas import BriefTarget


def match_dmp_segments(target: BriefTarget, segments: list[dict[str, Any]]) -> dict[str, Any]:
    requested = [*target.interests, *target.behaviors]
    matched = []
    gaps = []
    seen_segment_keys = set()

    for item in requested:
        segment = _find_segment(item, segments)
        if segment:
            key = segment["key"]
            if key not in seen_segment_keys:
                matched.append(segment)
                seen_segment_keys.add(key)
        else:
            gaps.append(
                {
                    "term": item,
                    "severity": "high" if _is_high_intent_gap(item) else "medium",
                    "suggested_proxy": _suggest_proxy(item),
                }
            )

    estimated_size = estimate_size(matched)
    return {
        "matched": matched,
        "gaps": gaps,
        "size_est": estimated_size,
        "explanation": _explain(matched, gaps, estimated_size),
    }


def estimate_size(matched: list[dict[str, Any]]) -> int:
    if not matched:
        return 0
    base = min(int(segment["size"]) for segment in matched)
    overlap_discount = 0.82 ** max(len(matched) - 1, 0)
    return int(base * overlap_discount)


def _find_segment(term: str, segments: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized = _normalize(term)
    for segment in segments:
        aliases = [_normalize(segment["name"]), *[_normalize(alias) for alias in segment.get("aliases", [])]]
        if normalized in aliases:
            return segment
    return None


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _is_high_intent_gap(term: str) -> bool:
    normalized = _normalize(term)
    return any(token in normalized for token in ["insurance", "bao hiem", "du hoc", "study abroad"])


def _suggest_proxy(term: str) -> str:
    normalized = _normalize(term)
    if "insurance" in normalized or "bao hiem" in normalized:
        return "Use Health interest + Finance interest until Insurance segment is available."
    if "study abroad" in normalized or "du hoc" in normalized:
        return "Use Education interest + High income household as proxy."
    if "sea" in normalized:
        return "Use Travel intent + Air travel + Hotel booker as proxy."
    return "Create a new DMP segment or use closest interest proxy."


def _explain(matched: list[dict[str, Any]], gaps: list[dict[str, Any]], size_est: int) -> str:
    if not matched:
        return "No DMP segment matched; campaign should not launch without a proxy or new segment."
    if gaps:
        return f"Matched {len(matched)} DMP segments with estimated size {size_est:,}; {len(gaps)} requested terms need proxy."
    return f"Matched {len(matched)} DMP segments with estimated size {size_est:,}; no major DMP gap."
