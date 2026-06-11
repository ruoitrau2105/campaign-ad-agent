from pathlib import Path

from evals.run import run_eval


def test_phase4_eval_gate_passes(tmp_path: Path) -> None:
    report = run_eval(output_dir=tmp_path)

    assert report["quality_gate"]["passed"] is True
    assert report["metrics"]["cases_total"] == 18
    assert report["metrics"]["cases_passed"] == 18
    assert report["metrics"]["json_valid_rate"] == 1
    assert report["metrics"]["deterministic_field_accuracy"] == 1
    assert report["metrics"]["model_route_match"] == 1
    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "latest.md").exists()
