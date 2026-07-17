from __future__ import annotations

from pathlib import Path

import pytest

from agent_reliability_lab.engine import run_scenario, run_suite
from agent_reliability_lab.scenario import load_scenario
from agent_reliability_lab.strategy import Strategy
from tests.helpers import write_scenario


def test_baseline_fails_on_first_timeout(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path))

    result = run_scenario(scenario, Strategy.baseline())

    assert result.passed is False
    assert result.failure_reason == "timeout"
    assert result.metrics["faults_injected"] == 1
    assert result.metrics["faults_recovered"] == 0


@pytest.mark.parametrize(
    "fault",
    ["timeout", "provider_failure", "malformed_output", "partial_stream", "stale_memory"],
)
def test_resilient_strategy_recovers_retryable_faults(tmp_path: Path, fault: str) -> None:
    scenario = load_scenario(write_scenario(tmp_path, fault=fault))

    result = run_scenario(scenario, Strategy.resilient())

    assert result.passed is True
    assert result.metrics["faults_injected"] == 1
    assert result.metrics["faults_recovered"] == 1
    assert result.metrics["tool_calls"] == 3
    assert any(event.kind == "retry" for event in result.trace)


def test_resilient_strategy_deduplicates_repeated_call(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path, fault="repeated_call"))

    result = run_scenario(scenario, Strategy.resilient())

    assert result.passed is True
    assert result.metrics["tool_calls"] == 2
    assert result.metrics["faults_recovered"] == 1
    assert any(event.kind == "deduplicated" for event in result.trace)


def test_fault_repeat_can_exhaust_retry_budget(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path, repeat=3))

    result = run_scenario(scenario, Strategy.resilient())

    assert result.passed is False
    assert result.failure_reason == "timeout"
    assert result.metrics["tool_calls"] == 3


def test_runs_are_deterministic_and_content_addressed(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path))
    first = run_scenario(scenario, Strategy.resilient())
    second = run_scenario(scenario, Strategy.resilient())

    assert first.run_id == second.run_id
    assert first.metrics == second.metrics
    assert [event.to_dict() for event in first.trace] == [
        event.to_dict() for event in second.trace
    ]


def test_suite_compares_strategies(tmp_path: Path) -> None:
    scenarios = [
        load_scenario(write_scenario(tmp_path, name="timeout", fault="timeout")),
        load_scenario(write_scenario(tmp_path, name="malformed", fault="malformed_output")),
    ]

    results = run_suite(scenarios, [Strategy.baseline(), Strategy.resilient()])

    assert len(results) == 4
    assert sum(result.passed for result in results if result.strategy == "baseline") == 0
    assert sum(result.passed for result in results if result.strategy == "resilient") == 2


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown strategy"):
        Strategy.named("magic")


def test_scenario_display_name_does_not_change_reliability_metrics(tmp_path: Path) -> None:
    first = load_scenario(write_scenario(tmp_path / "one", name="team-alpha"))
    second = load_scenario(write_scenario(tmp_path / "two", name="team-beta"))

    first_result = run_scenario(first, Strategy.resilient())
    second_result = run_scenario(second, Strategy.resilient())

    assert first_result.metrics == second_result.metrics
    assert first_result.passed == second_result.passed
