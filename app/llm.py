from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

import httpx
from dotenv import load_dotenv


TaskName = Literal[
    "chat_orchestration",
    "brief_parse",
    "segment_explain",
    "setup_explain",
    "report_explain",
    "ao_alert",
    "developer_support",
]

Message = dict[str, str]

CONFIG_PATH = Path("config/models.json")
LIVE_MODES = {"1", "true", "live", "maas", "cloud"}


@dataclass(frozen=True)
class ModelRoute:
    task: str
    model: str
    configured_model: str
    provider: str
    base_url: str
    model_env: str
    runtime: bool
    temperature: float
    output: str
    strength: str

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["base_url"] = _redact_url(data["base_url"])
        return data


def routing_snapshot() -> dict[str, Any]:
    config = _load_config()
    routes = {task: get_model_route(task) for task in config["tasks"]}
    return {
        "provider": config["provider"]["name"],
        "mode": llm_mode(),
        "live_enabled": is_live_enabled(),
        "api_key_configured": _api_key(config) is not None,
        "base_url": _redact_url(_base_url(config)),
        "routes": {task: route.public_dict() for task, route in routes.items()},
    }


def llm_mode() -> str:
    load_dotenv()
    return os.getenv("CAMP_ADS_LLM_MODE", os.getenv("LLM_MODE", "mock")).strip().lower() or "mock"


def is_live_enabled() -> bool:
    config = _load_config()
    return llm_mode() in LIVE_MODES and _api_key(config) is not None


def get_model_route(task: str) -> ModelRoute:
    load_dotenv()
    config = _load_config()
    tasks = config["tasks"]
    if task not in tasks:
        known = ", ".join(sorted(tasks))
        raise ValueError(f"Unknown LLM task '{task}'. Known tasks: {known}")

    task_config = tasks[task]
    provider = config["provider"]
    configured_model = str(task_config["model"])
    model_env = str(task_config["model_env"])
    model = os.getenv(model_env, configured_model).strip() or configured_model
    return ModelRoute(
        task=task,
        model=model,
        configured_model=configured_model,
        provider=str(provider["name"]),
        base_url=_base_url(config),
        model_env=model_env,
        runtime=bool(task_config.get("runtime", True)),
        temperature=float(task_config.get("temperature", 0.2)),
        output=str(task_config.get("output", "text")),
        strength=str(task_config.get("strength", "")),
    )


def call_llm(
    task: TaskName,
    messages: Sequence[Message],
    *,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    route = get_model_route(task)
    if not route.runtime:
        return _mock_response(route, "route is marked build-time only")
    if not is_live_enabled():
        return _mock_response(route, "LLM live mode is disabled or API key is not configured")

    payload: dict[str, Any] = {
        "model": route.model,
        "messages": list(messages),
        "temperature": route.temperature,
    }
    if route.output == "json":
        payload["response_format"] = {"type": "json_object"}

    try:
        response = httpx.post(
            f"{route.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {_api_key()}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return {
            "mode": "live",
            "task": task,
            "route": route.public_dict(),
            "content": content,
            "raw_usage": body.get("usage"),
        }
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        fallback = _mock_response(route, f"live call failed: {exc.__class__.__name__}")
        fallback["error"] = str(exc)
        return fallback


def call_llm_json(
    task: TaskName,
    messages: Sequence[Message],
    *,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    result = call_llm(task, messages, timeout_seconds=timeout_seconds)
    content = result.get("content")
    if result["mode"] != "live" or not isinstance(content, str):
        result["json"] = None
        return result

    try:
        result["json"] = json.loads(content)
        return result
    except json.JSONDecodeError as exc:
        result["mode"] = "mock"
        result["json"] = None
        result["error"] = f"JSON parse failed: {exc.msg}"
        result["fallback_reason"] = "live JSON response was invalid"
        return result


def _mock_response(route: ModelRoute, reason: str) -> dict[str, Any]:
    return {
        "mode": "mock",
        "task": route.task,
        "route": route.public_dict(),
        "content": None,
        "fallback_reason": reason,
    }


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Model config not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _base_url(config: dict[str, Any]) -> str:
    load_dotenv()
    provider = config["provider"]
    for env_name in provider.get("base_url_env", []):
        value = os.getenv(str(env_name))
        if value:
            return value.strip().rstrip("/")
    return str(provider["base_url"]).rstrip("/")


def _api_key(config: dict[str, Any] | None = None) -> str | None:
    load_dotenv()
    provider = (config or _load_config())["provider"]
    for env_name in provider.get("api_key_env", ["MAAS_API_KEY", "LLM_API_KEY"]):
        value = os.getenv(env_name)
        if value:
            return value.strip()
    return None


def _redact_url(value: str) -> str:
    return value.rstrip("/")
