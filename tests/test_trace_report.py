from __future__ import annotations

import json
from pathlib import Path

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

