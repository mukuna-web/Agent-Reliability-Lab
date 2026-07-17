from __future__ import annotations

from pathlib import Path


def write_scenario(
    directory: Path,
    *,
    name: str = "timeout-case",
    fault: str = "timeout",
    step: int = 0,
    occurrence: int = 1,
    repeat: int = 1,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.toml"
    path.write_text(
        f'''[scenario]
name = "{name}"
description = "Synthetic reliability scenario"
seed = 17

[[steps]]
tool = "fetch_logs"
arguments = {{ service = "api" }}
result = {{ status = "healthy", incidents = 0 }}

[[steps]]
tool = "check_metrics"
arguments = {{ service = "api" }}
result = {{ error_rate = 0.01 }}

[[faults]]
kind = "{fault}"
step = {step}
occurrence = {occurrence}
repeat = {repeat}
''',
        encoding="utf-8",
    )
    return path

