from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from agent_reliability_lab.models import FAULT_KINDS, FaultSpec, JSONValue, Scenario, Step


class ScenarioError(ValueError):
    """Raised when a scenario file cannot be validated."""


def _table(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScenarioError(f"{label} must be a table")
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{label} must be a non-empty string")
    return value.strip()


def _json_object(value: Any, label: str) -> dict[str, JSONValue]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ScenarioError(f"{label} must be a table")
    return value


def load_scenario(path: Path) -> Scenario:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ScenarioError(f"invalid TOML in {path}: {exc}") from exc

    header = _table(payload.get("scenario"), "scenario")
    name = _nonempty_string(header.get("name"), "scenario.name")
    description_value = header.get("description", "")
    if not isinstance(description_value, str):
        raise ScenarioError("scenario.description must be a string")
    seed = header.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ScenarioError("scenario.seed must be an integer")

    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ScenarioError("scenario requires at least one step")
    steps: list[Step] = []
    for index, raw_step in enumerate(raw_steps):
        step = _table(raw_step, f"steps[{index}]")
        steps.append(
            Step(
                tool=_nonempty_string(step.get("tool"), f"steps[{index}].tool"),
                arguments=_json_object(step.get("arguments", {}), f"steps[{index}].arguments"),
                result=_json_object(step.get("result", {}), f"steps[{index}].result"),
            )
        )

    raw_faults = payload.get("faults", [])
    if not isinstance(raw_faults, list):
        raise ScenarioError("faults must be an array of tables")
    faults: list[FaultSpec] = []
    for index, raw_fault in enumerate(raw_faults):
        fault = _table(raw_fault, f"faults[{index}]")
        kind = _nonempty_string(fault.get("kind"), f"faults[{index}].kind")
        if kind not in FAULT_KINDS:
            raise ScenarioError(f"unsupported fault kind: {kind}")
        step_index = fault.get("step")
        if not isinstance(step_index, int) or isinstance(step_index, bool):
            raise ScenarioError(f"faults[{index}].step must be an integer")
        if step_index < 0 or step_index >= len(steps):
            raise ScenarioError(f"fault {index} references missing step {step_index}")
        occurrence = fault.get("occurrence", 1)
        repeat = fault.get("repeat", 1)
        if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 1:
            raise ScenarioError("fault occurrence must be positive")
        if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 1:
            raise ScenarioError("fault repeat must be positive")
        faults.append(FaultSpec(kind, step_index, occurrence, repeat))

    return Scenario(name, description_value.strip(), seed, tuple(steps), tuple(faults))

