from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Callable

import httpx


DEFAULT_BRIEF = "Brand: ShieldCare. Setup lead bao hiem suc khoe, budget 150 trieu, KPI CPL ROAS."


@dataclass
class Check:
    name: str
    run: Callable[[httpx.Client], None]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the Campaign Ads Agent HTTP runtime.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Running app base URL.")
    args = parser.parse_args()

    checks = [
        Check("GET /health", check_health),
        Check("GET /", check_ui_root),
        Check("POST /invocations setup", check_invocation_setup),
        Check("POST /invocations report", check_invocation_report),
        Check("POST /invocations alert", check_invocation_alert),
        Check("POST /invocations empty", check_invocation_empty),
        Check("POST /api/creative/inspect", check_creative_upload),
        Check("POST /api/setup/plan", check_setup_plan),
    ]

    failures: list[str] = []
    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        for check in checks:
            try:
                check.run(client)
                print(f"[PASS] {check.name}")
            except Exception as exc:  # noqa: BLE001 - CLI smoke should report all failures cleanly.
                failures.append(f"{check.name}: {exc}")
                print(f"[FAIL] {check.name}: {exc}")

    if failures:
        print("\nSmoke failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nSmoke passed: local runtime is ready for demo and Docker validation.")
    return 0


def check_health(client: httpx.Client) -> None:
    data = _json(client.get("/health"))
    _assert(data == {"status": "healthy"}, f"unexpected health payload: {data}")


def check_ui_root(client: httpx.Client) -> None:
    response = client.get("/")
    _assert(response.status_code == 200, f"status {response.status_code}")
    html = response.text
    for text in [
        "Campaign Ads Agent",
        "CHAT",
        "WORKSPACE",
        "Parse brief",
        'type="file"',
        "Recommend zones",
        "Map DMP segment",
        "Run setup",
        "Build alert",
    ]:
        _assert(text in html, f"missing UI text: {text}")


def check_invocation_setup(client: httpx.Client) -> None:
    data = _api_data(client.post("/invocations", json={"message": DEFAULT_BRIEF, "top_n": 5}))
    _assert(data["action"] == "setup_plan", f"action {data['action']}")
    result = data["result"]
    _assert(result["brief"]["brand"] == "ShieldCare", f"brand {result['brief']['brand']}")
    _assert(result["brief"]["budget_vnd"] == 150_000_000, f"budget {result['brief']['budget_vnd']}")
    _assert(len(result["zones"]) == 5, f"zones {len(result['zones'])}")
    _assert(sum(row["budget_vnd"] for row in result["budget_split"]) == 150_000_000, "budget split mismatch")


def check_invocation_report(client: httpx.Client) -> None:
    data = _api_data(client.post("/invocations", json={"message": "Analyze campaign reports"}))
    _assert(data["action"] == "report_analysis", f"action {data['action']}")
    _assert(data["result"]["total_records"] == 480, f"records {data['result']['total_records']}")
    _assert(data["result"]["reports"] == 15, f"reports {data['result']['reports']}")
    _assert(data["result"]["verdict"] == {"good": 99, "watch": 238, "bad": 143}, "verdict mismatch")


def check_invocation_alert(client: httpx.Client) -> None:
    data = _api_data(client.post("/invocations", json={"message": "Create AO alert"}))
    _assert(data["action"] == "ao_alert", f"action {data['action']}")
    _assert("143 bad records" in data["reply"], f"reply {data['reply']}")


def check_invocation_empty(client: httpx.Client) -> None:
    data = _api_data(client.post("/invocations", json={}))
    _assert(data["action"] == "guidance", f"action {data['action']}")


def check_creative_upload(client: httpx.Client) -> None:
    files = {"file": ("creative.txt", b"mock creative bytes", "text/plain")}
    data = _api_data(client.post("/api/creative/inspect", files=files))
    _assert(data["status"] == "accepted", f"status {data['status']}")
    _assert(data["size_bytes"] == len(b"mock creative bytes"), f"size {data['size_bytes']}")


def check_setup_plan(client: httpx.Client) -> None:
    payload = {
        "brief_text": DEFAULT_BRIEF,
        "creative": {"filename": "shieldcare-banner.png", "content_type": "image/png", "size_bytes": 2048},
        "top_n": 5,
    }
    data = _api_data(client.post("/api/setup/plan", json=payload))
    _assert(data["creative"]["filename"] == "shieldcare-banner.png", f"creative {data['creative']}")
    _assert(data["campaigns"][0]["creative"] == "shieldcare-banner.png", "creative not applied to campaign draft")


def _json(response: httpx.Response) -> Any:
    _assert(response.status_code == 200, f"status {response.status_code}: {response.text[:300]}")
    return response.json()


def _api_data(response: httpx.Response) -> Any:
    payload = _json(response)
    _assert(payload.get("status") == "ok", f"api status {payload.get('status')}")
    return payload["data"]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    sys.exit(main())
