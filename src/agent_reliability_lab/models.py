from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]

FAULT_KINDS = frozenset(
    {
        "timeout",
        "provider_failure",
        "malformed_output",
        "partial_stream",
        "stale_memory",
        "repeated_call",
    }
)


@dataclass(frozen=True, slots=True)
class Step:
    tool: str
    arguments: dict[str, JSONValue]
    result: dict[str, JSONValue]

    def to_dict(self) -> dict[str, JSONValue]:
        return {"tool": self.tool, "arguments": self.arguments, "result": self.result}


@dataclass(frozen=True, slots=True)
class FaultSpec:
    kind: str
    step: int
    occurrence: int = 1
    repeat: int = 1

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "kind": self.kind,
            "step": self.step,
            "occurrence": self.occurrence,
            "repeat": self.repeat,
        }


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    description: str
    seed: int
    steps: tuple[Step, ...]
    faults: tuple[FaultSpec, ...]

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "description": self.description,
            "seed": self.seed,
            "steps": [step.to_dict() for step in self.steps],
            "faults": [fault.to_dict() for fault in self.faults],
        }


@dataclass(frozen=True, slots=True)
class TraceEvent:
    index: int
    kind: str
    step: int
    tool: str
    attempt: int
    detail: str
    virtual_time_ms: int

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "index": self.index,
            "kind": self.kind,
            "step": self.step,
            "tool": self.tool,
            "attempt": self.attempt,
            "detail": self.detail,
            "virtual_time_ms": self.virtual_time_ms,
        }


MetricValue: TypeAlias = int | float


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    scenario: str
    strategy: str
    passed: bool
    failure_reason: str | None
    metrics: dict[str, MetricValue]
    trace: tuple[TraceEvent, ...]

    def manifest(self) -> dict[str, JSONValue]:
        metrics: dict[str, JSONValue] = {
            name: value for name, value in self.metrics.items()
        }
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "scenario": self.scenario,
            "strategy": self.strategy,
            "passed": self.passed,
            "failure_reason": self.failure_reason,
            "metrics": metrics,
        }
