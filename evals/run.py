from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("CAMP_ADS_LLM_MODE", "mock")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data_loader import load_campaign_reports, load_dmp_segments, load_zones
from app.llm import routing_snapshot
from app.logic.alert_builder import build_ao_alert
from app.logic.brief_parser import parse_brief_mock
from app.logic.dmp_match import match_dmp_segments
from app.logic.invocation import run_invocation
from app.logic.llm_readouts import draft_ao_alert, explain_dmp_match, explain_report, explain_setup
from app.logic.report_analyzer import summarize_reports
from app.logic.setup_planner import build_setup_plan
from app.logic.zone_scoring import recommend_zones
from app.schemas import BriefTarget


DEFAULT_CASES = Path("evals/cases.jsonl")
DEFAULT_OUTPUT_DIR = Path("evals/results")
DEFAULT_THRESHOLDS = {
    "json_valid_rate": 0.90,
    "deterministic_field_accuracy": 0.99,
    "model_route_match": 0.85,
    "fatal_errors": 0,
}


@dataclass
class CheckResult:
    path: str
    op: str
    expected: Any = None
    actual: Any = None
    passed: bool = False
    message: str = ""


def run_eval(cases_path: Path = DEFAULT_CASES, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    cases = _load_cases(cases_path)
    results = [_run_case(case) for case in cases]
    summary = _summarize(results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cases_path": str(cases_path),
        "thresholds": DEFAULT_THRESHOLDS,
        "quality_gate": summary["quality_gate"],
        "metrics": summary["metrics"],
        "llm": routing_snapshot(),
        "results": results,
    }
    _write_reports(report, output_dir)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Camp Ads Agent golden evals.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = run_eval(args.cases, args.output_dir)
    metrics = report["metrics"]
    print(
        "Eval {status}: {passed}/{total} cases, field accuracy {field:.2%}, JSON valid {json_rate:.2%}, route match {route:.2%}".format(
            status=report["quality_gate"]["status"],
            passed=metrics["cases_passed"],
            total=metrics["cases_total"],
            field=metrics["deterministic_field_accuracy"],
            json_rate=metrics["json_valid_rate"],
            route=metrics["model_route_match"],
        )
    )
    return 0 if report["quality_gate"]["passed"] else 1


def _load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        output = _execute_case(case)
        json_valid = _is_json_valid(output)
        checks = [_evaluate_check(output, check) for check in case.get("expect", [])]
        passed = json_valid and all(check.passed for check in checks)
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": passed,
            "json_valid": json_valid,
            "fatal_error": None,
            "checks": [check.__dict__ for check in checks],
        }
    except Exception as exc:
        return {
            "id": case.get("id", "unknown"),
            "type": case.get("type", "unknown"),
            "passed": False,
            "json_valid": False,
            "fatal_error": f"{exc.__class__.__name__}: {exc}",
            "checks": [],
        }


def _execute_case(case: dict[str, Any]) -> dict[str, Any]:
    case_type = case["type"]
    payload = case.get("input", {})

    if case_type == "brief_parse":
        data = parse_brief_mock(payload["text"]).model_dump()
        data["model_route"] = routing_snapshot()["routes"]["brief_parse"]
        return data

    if case_type == "zone_recommend":
        return {
            "objective": payload["objective"],
            "model_route": routing_snapshot()["routes"]["setup_explain"],
            "zones": recommend_zones(load_zones(), payload["objective"], payload.get("top_n", 5)),
        }

    if case_type == "dmp_match":
        target = BriefTarget(**payload["target"])
        data = match_dmp_segments(target, load_dmp_segments())
        data["model_route"] = routing_snapshot()["routes"]["segment_explain"]
        data["llm_readout"] = explain_dmp_match(data)
        return data

    if case_type == "setup_plan":
        brief = parse_brief_mock(payload["brief_text"])
        data = build_setup_plan(
            brief=brief,
            zones=load_zones(),
            dmp_segments=load_dmp_segments(),
            creative=payload.get("creative"),
            top_n=payload.get("top_n", 5),
        )
        routes = routing_snapshot()["routes"]
        data["model_routes"] = {
            "brief_parse": routes["brief_parse"],
            "segment_explain": routes["segment_explain"],
            "setup_explain": routes["setup_explain"],
        }
        data["llm_readout"] = explain_setup(data)
        return data

    if case_type == "report_analyze":
        data = summarize_reports(load_campaign_reports())
        data["model_route"] = routing_snapshot()["routes"]["report_explain"]
        data["llm_readout"] = explain_report(data)
        return data

    if case_type == "ao_alert":
        data = build_ao_alert(load_campaign_reports(), payload.get("max_items", 8))
        data["model_route"] = routing_snapshot()["routes"]["ao_alert"]
        data["llm_readout"] = draft_ao_alert(data)
        return data

    if case_type == "invocation":
        return run_invocation(
            message=payload.get("message", ""),
            zones=load_zones(),
            dmp_segments=load_dmp_segments(),
            reports=load_campaign_reports(),
            creative=payload.get("creative"),
            top_n=payload.get("top_n", 5),
        )

    raise ValueError(f"Unknown eval case type: {case_type}")


def _evaluate_check(output: dict[str, Any], check: dict[str, Any]) -> CheckResult:
    path = check["path"]
    op = check["op"]
    expected = check.get("value")
    values = _values_at_path(output, path)
    actual: Any = values if "*" in path else (values[0] if values else None)

    if op == "exists":
        passed = bool(values)
    elif op == "equals":
        passed = actual == expected
    elif op == "approx_equals":
        tolerance = float(check.get("tolerance", 0.001))
        passed = actual is not None and abs(float(actual) - float(expected)) <= tolerance
    elif op == "contains":
        passed = expected in values if "*" in path else _contains(actual, expected)
    elif op == "contains_text":
        passed = any(str(expected) in str(value) for value in values)
    elif op == "len_equals":
        passed = hasattr(actual, "__len__") and len(actual) == int(expected)
    elif op == "gte":
        passed = actual is not None and float(actual) >= float(expected)
    elif op == "lte":
        passed = actual is not None and float(actual) <= float(expected)
    elif op == "sum_equals":
        passed = sum(float(value) for value in values) == float(expected)
    else:
        raise ValueError(f"Unknown check op: {op}")

    return CheckResult(
        path=path,
        op=op,
        expected=expected,
        actual=actual,
        passed=passed,
        message="ok" if passed else f"expected {op} {expected}, got {actual}",
    )


def _values_at_path(data: Any, path: str) -> list[Any]:
    values = [data]
    for part in path.split("."):
        next_values: list[Any] = []
        for value in values:
            if part == "*":
                if isinstance(value, list):
                    next_values.extend(value)
                continue
            if isinstance(value, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(value):
                    next_values.append(value[index])
                continue
            if isinstance(value, dict) and part in value:
                next_values.append(value[part])
        values = next_values
    return values


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(actual, list):
        return expected in actual
    return str(expected) in str(actual)


def _is_json_valid(output: Any) -> bool:
    try:
        json.dumps(output, ensure_ascii=False, default=str)
        return True
    except (TypeError, ValueError):
        return False


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    case_total = len(results)
    case_passed = sum(1 for result in results if result["passed"])
    fatal_errors = sum(1 for result in results if result["fatal_error"])
    json_valid = sum(1 for result in results if result["json_valid"])
    checks = [check for result in results for check in result["checks"]]
    checks_passed = sum(1 for check in checks if check["passed"])
    route_checks = [
        check
        for check in checks
        if check["path"].endswith("configured_model") or ".configured_model" in check["path"]
    ]
    route_passed = sum(1 for check in route_checks if check["passed"])

    metrics = {
        "cases_total": case_total,
        "cases_passed": case_passed,
        "case_pass_rate": case_passed / case_total if case_total else 0,
        "fatal_errors": fatal_errors,
        "json_valid_rate": json_valid / case_total if case_total else 0,
        "field_checks_total": len(checks),
        "field_checks_passed": checks_passed,
        "deterministic_field_accuracy": checks_passed / len(checks) if checks else 0,
        "model_route_checks_total": len(route_checks),
        "model_route_checks_passed": route_passed,
        "model_route_match": route_passed / len(route_checks) if route_checks else 1,
    }
    passed = (
        metrics["json_valid_rate"] >= DEFAULT_THRESHOLDS["json_valid_rate"]
        and metrics["deterministic_field_accuracy"] >= DEFAULT_THRESHOLDS["deterministic_field_accuracy"]
        and metrics["model_route_match"] >= DEFAULT_THRESHOLDS["model_route_match"]
        and metrics["fatal_errors"] <= DEFAULT_THRESHOLDS["fatal_errors"]
    )
    return {
        "metrics": metrics,
        "quality_gate": {
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
        },
    }


def _write_reports(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "latest.md").write_text(_markdown_report(report), encoding="utf-8")


def _markdown_report(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    failed = [result for result in report["results"] if not result["passed"]]
    lines = [
        "# Camp Ads Agent Eval Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Quality gate: **{report['quality_gate']['status']}**",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Cases | {metrics['cases_passed']} / {metrics['cases_total']} |",
        f"| JSON valid rate | {metrics['json_valid_rate']:.2%} |",
        f"| Deterministic field accuracy | {metrics['deterministic_field_accuracy']:.2%} |",
        f"| Model route match | {metrics['model_route_match']:.2%} |",
        f"| Fatal errors | {metrics['fatal_errors']} |",
        "",
    ]
    if failed:
        lines.append("## Failed Cases")
        lines.append("")
        for result in failed:
            lines.append(f"- `{result['id']}`: {result['fatal_error'] or 'check failure'}")
    else:
        lines.append("All golden cases passed.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
