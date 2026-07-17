from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence

from agent_reliability_lab.models import FaultSpec, RunResult, Scenario, TraceEvent
from agent_reliability_lab.strategy import Strategy

FAULT_LATENCY_MS = {
    "timeout": 500,
    "provider_failure": 120,
    "malformed_output": 40,
    "partial_stream": 70,
    "stale_memory": 35,
    "repeated_call": 10,
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "scenario"


def _run_id(scenario: Scenario, strategy: Strategy) -> str:
    payload = {"scenario": scenario.to_dict(), "strategy": strategy.to_dict()}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:12]
    return f"{_slug(scenario.name)}-{strategy.name}-{digest}"


def _active_fault(faults: tuple[FaultSpec, ...], step: int, attempt: int) -> str | None:
    for fault in faults:
        if fault.step != step:
            continue
        if fault.occurrence <= attempt < fault.occurrence + fault.repeat:
            return fault.kind
    return None


def run_scenario(scenario: Scenario, strategy: Strategy) -> RunResult:
    events: list[TraceEvent] = []
    virtual_time = 0
    tool_calls = 0
    injected = 0
    recovered = 0

    def record(kind: str, step: int, tool: str, attempt: int, detail: str) -> None:
        events.append(
            TraceEvent(len(events), kind, step, tool, attempt, detail, virtual_time)
        )

    for step_index, step in enumerate(scenario.steps):
        attempt = 1
        pending_faults = 0
        while True:
            tool_calls += 1
            virtual_time += 25 + ((scenario.seed + step_index + attempt) % 11)
            record("call", step_index, step.tool, attempt, "tool invoked")
            fault_kind = _active_fault(scenario.faults, step_index, attempt)
            if fault_kind is None:
                recovered += pending_faults
                record("success", step_index, step.tool, attempt, "expected result returned")
                break

            injected += 1
            pending_faults += 1
            virtual_time += FAULT_LATENCY_MS[fault_kind]
            record("fault", step_index, step.tool, attempt, fault_kind)

            if fault_kind == "repeated_call" and strategy.deduplicate_repeated_calls:
                recovered += pending_faults
                record("deduplicated", step_index, step.tool, attempt, "duplicate suppressed")
                record("success", step_index, step.tool, attempt, "cached result returned")
                break

            if fault_kind == "stale_memory" and strategy.reset_stale_memory:
                record("memory_reset", step_index, step.tool, attempt, "stale state cleared")

            if attempt <= strategy.max_retries:
                record("retry", step_index, step.tool, attempt, "retry budget available")
                attempt += 1
                continue

            record("failure", step_index, step.tool, attempt, fault_kind)
            metrics: dict[str, int | float] = {
                "steps_completed": step_index,
                "tool_calls": tool_calls,
                "faults_injected": injected,
                "faults_recovered": recovered,
                "virtual_latency_ms": virtual_time,
                "cost_units": float(tool_calls),
            }
            return RunResult(
                _run_id(scenario, strategy),
                scenario.name,
                strategy.name,
                False,
                fault_kind,
                metrics,
                tuple(events),
            )

    metrics = {
        "steps_completed": len(scenario.steps),
        "tool_calls": tool_calls,
        "faults_injected": injected,
        "faults_recovered": recovered,
        "virtual_latency_ms": virtual_time,
        "cost_units": float(tool_calls),
    }
    return RunResult(
        _run_id(scenario, strategy),
        scenario.name,
        strategy.name,
        True,
        None,
        metrics,
        tuple(events),
    )


def run_suite(scenarios: Sequence[Scenario], strategies: Sequence[Strategy]) -> list[RunResult]:
    return [
        run_scenario(scenario, strategy)
        for scenario in scenarios
        for strategy in strategies
    ]

