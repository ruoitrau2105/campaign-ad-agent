from fastapi.testclient import TestClient

from app.llm import call_llm, get_model_route, routing_snapshot
from app.main import app


client = TestClient(app)


def test_model_routes_match_task_strengths() -> None:
    assert get_model_route("chat_orchestration").configured_model == "Qwen 3.5 27B"
    assert get_model_route("brief_parse").configured_model == "Qwen 3.5 27B"
    assert get_model_route("segment_explain").configured_model == "Gemma 4 31B-IT"
    assert get_model_route("setup_explain").configured_model == "Gemma 4 31B-IT"
    assert get_model_route("report_explain").configured_model == "Gemma 4 31B-IT"
    assert get_model_route("ao_alert").configured_model == "Qwen 3.5 27B"
    assert get_model_route("developer_support").configured_model == "MiniMax M2.5"
    assert get_model_route("developer_support").runtime is False


def test_model_route_can_be_overridden_by_env(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL_BRIEF_PARSE", "provider/path/qwen-3-5-27b")
    route = get_model_route("brief_parse")
    assert route.model == "provider/path/qwen-3-5-27b"
    assert route.configured_model == "Qwen 3.5 27B"
    assert route.model_env == "LLM_MODEL_BRIEF_PARSE"


def test_llm_call_uses_mock_fallback_by_default(monkeypatch) -> None:
    monkeypatch.setenv("CAMP_ADS_LLM_MODE", "mock")
    result = call_llm("ao_alert", [{"role": "user", "content": "Draft AO alert"}])
    assert result["mode"] == "mock"
    assert result["task"] == "ao_alert"
    assert result["content"] is None
    assert result["route"]["configured_model"] == "Qwen 3.5 27B"


def test_routing_snapshot_is_safe_for_context() -> None:
    snapshot = routing_snapshot()
    assert snapshot["provider"] == "GreenNode AI Platform"
    assert "api_key_configured" in snapshot
    assert "routes" in snapshot
    assert snapshot["routes"]["report_explain"]["configured_model"] == "Gemma 4 31B-IT"
    assert "bearer " not in str(snapshot).lower()
    assert "authorization" not in str(snapshot).lower()


def test_context_endpoint_exposes_llm_routing() -> None:
    response = client.get("/api/context")
    assert response.status_code == 200
    llm = response.json()["data"]["llm"]
    assert llm["routes"]["brief_parse"]["configured_model"] == "Qwen 3.5 27B"
    assert llm["routes"]["developer_support"]["runtime"] is False


def test_invocation_response_includes_model_routing() -> None:
    response = client.post(
        "/invocations",
        json={"message": "Brand: ShieldCare. Setup lead bao hiem suc khoe, budget 150 trieu."},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "setup_plan"
    assert data["model_routes"]["brief_parse"]["configured_model"] == "Qwen 3.5 27B"
    assert data["model_routes"]["setup_explain"]["configured_model"] == "Gemma 4 31B-IT"
    assert data["result"]["llm_readout"]["mode"] == "mock"
    assert data["result"]["llm_readout"]["route"]["configured_model"] == "Gemma 4 31B-IT"
