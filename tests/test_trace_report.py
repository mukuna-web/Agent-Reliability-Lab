from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from agent_reliability_lab.engine import run_scenario
from agent_reliability_lab.report import write_report
from agent_reliability_lab.scenario import load_scenario
from agent_reliability_lab.storage import load_runs, write_run
from agent_reliability_lab.strategy import Strategy
from agent_reliability_lab.trace import load_trace, verify_trace
from tests.helpers import write_scenario


def test_run_artifact_contains_manifest_and_hash_chained_trace(tmp_path: Path) -> None:
    result = run_scenario(load_scenario(write_scenario(tmp_path)), Strategy.resilient())

    run_dir = write_run(result, tmp_path / "runs")
    events = load_trace(run_dir / "trace.jsonl")
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    assert manifest["run_id"] == result.run_id
    assert manifest["passed"] is True
    assert verify_trace(events) is True
    assert events[-1]["event_hash"]


def test_trace_verification_detects_tampering(tmp_path: Path) -> None:
    result = run_scenario(load_scenario(write_scenario(tmp_path)), Strategy.resilient())
    run_dir = write_run(result, tmp_path / "runs")
    events = load_trace(run_dir / "trace.jsonl")
    events[0]["detail"] = "tampered"

    assert verify_trace(events) is False


def test_write_run_is_idempotent(tmp_path: Path) -> None:
    result = run_scenario(load_scenario(write_scenario(tmp_path)), Strategy.resilient())
    first = write_run(result, tmp_path / "runs")
    second = write_run(result, tmp_path / "runs")

    assert first == second
    assert len(load_runs(tmp_path / "runs")) == 1


def test_report_summarizes_pass_rates(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path))
    results = [
        run_scenario(scenario, Strategy.baseline()),
        run_scenario(scenario, Strategy.resilient()),
    ]

    json_path = write_report(results, tmp_path / "report.html")
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "Agent Reliability Lab" in html
    assert "baseline" in html and "resilient" in html
    assert payload["summary"]["baseline"]["pass_rate"] == 0.0
    assert payload["summary"]["resilient"]["pass_rate"] == 1.0
    csv_text = (tmp_path / "report.csv").read_text(encoding="utf-8")
    assert csv_text.splitlines()[0] == (
        "scenario,strategy,passed,faults_injected,faults_recovered,tool_calls,virtual_latency_ms"
    )
    assert "baseline" in csv_text and "resilient" in csv_text


def _report_manifest(
    *,
    scenario: str = "safe-scenario",
    strategy: str = "safe-strategy",
    metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "safe-run",
        "scenario": scenario,
        "strategy": strategy,
        "passed": True,
        "failure_reason": None,
        "metrics": metrics
        or {
            "faults_injected": 1,
            "faults_recovered": 1,
            "tool_calls": 2,
            "virtual_latency_ms": 40,
        },
    }


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_report_csv_neutralizes_formula_leading_text(tmp_path: Path, prefix: str) -> None:
    write_report(
        [
            _report_manifest(
                scenario=f"{prefix}scenario",
                strategy=f"{prefix}strategy",
            )
        ],
        tmp_path / "report.html",
    )

    with (tmp_path / "report.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["scenario"] == f"'{prefix}scenario"
    assert row["strategy"] == f"'{prefix}strategy"


def test_report_escapes_stored_labels_and_coerces_numeric_metrics(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs" / "tampered"
    runs_dir.mkdir(parents=True)
    manifest = _report_manifest(
        scenario='<img src=x onerror="alert(1)">',
        metrics={
            "faults_injected": "1",
            "faults_recovered": "1.0",
            "tool_calls": "2",
            "virtual_latency_ms": "40",
        },
    )
    (runs_dir / "run.json").write_text(json.dumps(manifest), encoding="utf-8")

    write_report(load_runs(tmp_path / "runs"), tmp_path / "report.html")

    report_html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert '<img src=x onerror="alert(1)">' not in report_html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in report_html
    with (tmp_path / "report.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["faults_injected"] == "1"
    assert row["virtual_latency_ms"] == "40"


def test_report_rejects_tampered_non_numeric_metrics(tmp_path: Path) -> None:
    manifest = _report_manifest()
    manifest["metrics"] = {
        "faults_injected": '<img src=x onerror="alert(1)">',
        "faults_recovered": 1,
        "tool_calls": 2,
        "virtual_latency_ms": 40,
    }

    with pytest.raises(ValueError, match="metrics.faults_injected"):
        write_report([manifest], tmp_path / "report.html")
