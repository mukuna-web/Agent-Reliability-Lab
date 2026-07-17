from __future__ import annotations

from dataclasses import dataclass

from agent_reliability_lab.models import JSONValue


@dataclass(frozen=True, slots=True)
class Strategy:
    name: str
    max_retries: int
    deduplicate_repeated_calls: bool
    reset_stale_memory: bool

    @classmethod
    def baseline(cls) -> Strategy:
        return cls("baseline", 0, False, False)

    @classmethod
    def resilient(cls) -> Strategy:
        return cls("resilient", 2, True, True)

    @classmethod
    def named(cls, name: str) -> Strategy:
        normalized = name.strip().lower()
        if normalized == "baseline":
            return cls.baseline()
        if normalized == "resilient":
            return cls.resilient()
        raise ValueError(f"unknown strategy: {name}")

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "max_retries": self.max_retries,
            "deduplicate_repeated_calls": self.deduplicate_repeated_calls,
            "reset_stale_memory": self.reset_stale_memory,
        }

