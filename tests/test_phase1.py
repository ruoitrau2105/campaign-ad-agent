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


def test_dmp_match_detects_gap() -> None:
    response = client.post(
        "/api/dmp/match",
        json={
            "target": {
                "interests": ["Health", "Insurance", "Finance", "Du hoc"],
                "behaviors": [],
                "location": [],
            }
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["size_est"] > 0
    gap_terms = {gap["term"] for gap in data["gaps"]}
    assert "Insurance" in gap_terms
    assert "Du hoc" in gap_terms


def test_setup_plan_end_to_end_contract() -> None:
    response = client.post(
        "/api/setup/plan",
        json={
            "brief_text": "Brand: ShieldCare. Thu lead bao hiem suc khoe, budget 150 trieu, KPI CPL ROAS. Target Health, Insurance, Finance, Du hoc.",
            "creative": {"filename": "shieldcare-banner.png", "content_type": "image/png", "size_bytes": 2048},
            "top_n": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["brief"]["funnel_stage"] == "conversion"
    assert len(data["zones"]) == 5
    assert len(data["budget_split"]) == 5
    assert sum(row["budget_vnd"] for row in data["budget_split"]) == 150_000_000
    assert len(data["campaigns"]) == 3
    assert data["creative"]["filename"] == "shieldcare-banner.png"


def test_creative_inspect_and_ao_alert() -> None:
    upload = client.post(
        "/api/creative/inspect",
        files={"file": ("creative.txt", b"mock creative bytes", "text/plain")},
    )
    assert upload.status_code == 200
    assert upload.json()["data"]["status"] == "accepted"
    assert upload.json()["data"]["size_bytes"] == len(b"mock creative bytes")

    alert = client.post("/api/alerts/ao", json={"max_items": 4})
    assert alert.status_code == 200
    data = alert.json()["data"]
    assert "143 bad records" in data["subject"]
    assert len(data["priority_records"]) == 4
    assert data["summary"]["total_roas"] == 2.6


def test_invocations_agent_chat_contract() -> None:
    response = client.post(
        "/invocations",
        json={
            "message": "Brand: ShieldCare. Setup lead bao hiem suc khoe, budget 150 trieu, KPI CPL ROAS.",
            "creative": {"filename": "shieldcare-banner.png", "content_type": "image/png", "size_bytes": 2048},
            "top_n": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "setup_plan"
    assert data["result"]["brief"]["brand"] == "ShieldCare"
    assert data["result"]["brief"]["funnel_stage"] == "conversion"
    assert sum(row["budget_vnd"] for row in data["result"]["budget_split"]) == 150_000_000


def test_invocations_empty_message_is_graceful() -> None:
    response = client.post("/invocations", json={})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "guidance"


def test_invocations_alert_contract() -> None:
    response = client.post("/invocations", json={"message": "Create AO alert"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "ao_alert"
    assert "143 bad records" in data["reply"]
