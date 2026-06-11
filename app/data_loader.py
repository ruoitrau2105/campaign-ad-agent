import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _read_json(name: str) -> Any:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_zones() -> list[dict[str, Any]]:
    return _read_json("ad_zones.json")


@lru_cache(maxsize=1)
def load_campaign_reports() -> list[dict[str, Any]]:
    return _read_json("campaign_reports.json")


@lru_cache(maxsize=1)
def load_report_summary() -> dict[str, Any]:
    return _read_json("report_summary.json")


@lru_cache(maxsize=1)
def load_dmp_segments() -> list[dict[str, Any]]:
    return _read_json("dmp_segments.json")
