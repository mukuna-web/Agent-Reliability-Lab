from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tests.helpers import write_scenario

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "agent_reliability_lab", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_validate_and_run_commands(tmp_path: Path) -> None:
    scenario = write_scenario(tmp_path / "scenarios")

    validated = run_cli("validate", str(scenario))
    executed = run_cli(
        "run", str(scenario), "--strategy", "resilient", "--output", str(tmp_path / "runs")
    )

    assert validated.returncode == 0
    assert json.loads(validated.stdout)["status"] == "valid"
    assert executed.returncode == 0
    run_dir = Path(json.loads(executed.stdout)["run_dir"])
    assert (run_dir / "run.json").is_file()


def test_suite_generates_portable_report(tmp_path: Path) -> None:
    scenarios = tmp_path / "scenarios"
    write_scenario(scenarios, name="timeout", fault="timeout")
    write_scenario(scenarios, name="partial", fault="partial_stream")

    completed = run_cli(
        "suite",
        str(scenarios),
        "--strategies",
        "baseline,resilient",
        "--output",
        str(tmp_path / "benchmark"),
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["runs"] == 4
    assert Path(payload["report"]).is_file()


def test_invalid_scenario_returns_actionable_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text('[scenario]\nname = "bad"\n', encoding="utf-8")

    completed = run_cli("validate", str(bad))

    assert completed.returncode == 2
    assert "at least one step" in completed.stderr

