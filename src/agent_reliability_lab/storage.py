from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_reliability_lab.models import RunResult
from agent_reliability_lab.trace import write_trace


def write_run(result: RunResult, runs_dir: Path) -> Path:
    run_dir = runs_dir / result.run_id
    manifest_path = run_dir / "run.json"
    if manifest_path.is_file():
        return run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(result.manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_trace(result.trace, run_dir / "trace.jsonl")
    return run_dir


def load_runs(runs_dir: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    if not runs_dir.exists():
        return manifests
    for path in sorted(runs_dir.glob("*/run.json")):
        manifests.append(json.loads(path.read_text(encoding="utf-8")))
    return manifests

