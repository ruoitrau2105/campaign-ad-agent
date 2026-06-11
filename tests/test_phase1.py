from fastapi.testclient import TestClient

from app.data_loader import load_campaign_reports, load_report_summary, load_zones
from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_mock_data_baseline() -> None:
    summary = load_report_summary()["total"]
    assert len(load_zones()) == 26
    assert len(load_campaign_reports()) == 480
    assert summary["total_records"] == 480
    assert summary["reports"] == 15
    assert summary["verdict"] == {"good": 99, "watch": 238, "bad": 143}
    assert round(summary["total_roas"], 2) == 2.60


def test_brief_parse_and_zone_recommendation() -> None:
    brief = client.post(
        "/api/brief/parse",
        json={"text": "Brand: ShieldCare. Thu lead bảo hiểm sức khỏe, budget 150 triệu, KPI CPL ROAS."},
    )
    assert brief.status_code == 200
    data = brief.json()["data"]
    assert data["funnel_stage"] == "conversion"
    assert data["budget_vnd"] == 150_000_000

    rec = client.post("/api/zones/recommend", json={"objective": "conversion", "top_n": 3})
    assert rec.status_code == 200
    zones = rec.json()["data"]["zones"]
    assert len(zones) == 3
    assert zones[0]["score"] >= zones[-1]["score"]
