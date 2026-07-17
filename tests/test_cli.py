from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_reliability_lab.cli import main
from tests.helpers import write_scenario


def test_direct_cli_covers_full_artifact_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenarios = tmp_path / "scenarios"
    scenario = write_scenario(scenarios)
    output = tmp_path / "benchmark"

    assert main(["validate", str(scenario)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "valid"

    assert main(["run", str(scenario), "--strategy", "resilient", "--output", str(tmp_path / "single")]) == 0
    single = json.loads(capsys.readouterr().out)
    assert single["passed"] is True

    assert main(["suite", str(scenarios), "--output", str(output)]) == 0
    suite = json.loads(capsys.readouterr().out)
    assert suite["runs"] == 2

    assert main(["compare", str(output / "runs"), "--output", str(tmp_path / "comparison.html")]) == 0
    assert json.loads(capsys.readouterr().out)["runs"] == 2

    trace = next((output / "runs").glob("*/trace.jsonl"))
    assert main(["replay", str(trace)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


@pytest.mark.parametrize(
    "arguments",
    [
        ["suite", "empty"],
        ["compare", "empty"],
    ],
)
def test_direct_cli_reports_empty_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(arguments) == 2
    assert "error:" in capsys.readouterr().err


def test_direct_cli_reports_invalid_strategy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = write_scenario(tmp_path)

    assert main(["run", str(scenario), "--strategy", "magic"]) == 2
    assert "unknown strategy" in capsys.readouterr().err


def test_direct_cli_rejects_tampered_trace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trace = tmp_path / "trace.jsonl"
    trace.write_text('{"event_hash":"wrong","previous_hash":"wrong"}\n', encoding="utf-8")

    assert main(["replay", str(trace)]) == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False

