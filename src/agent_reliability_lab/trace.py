from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from agent_reliability_lab.models import TraceEvent

GENESIS_HASH = "0" * 64


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def chained_events(events: Sequence[TraceEvent]) -> list[dict[str, Any]]:
    previous = GENESIS_HASH
    output: list[dict[str, Any]] = []
    for event in events:
        payload: dict[str, Any] = event.to_dict()
        payload["previous_hash"] = previous
        payload["event_hash"] = _digest(payload)
        previous = payload["event_hash"]
        output.append(payload)
    return output


def write_trace(events: Sequence[TraceEvent], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(event, sort_keys=True) for event in chained_events(events)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_trace(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_trace(events: Sequence[dict[str, Any]]) -> bool:
    previous = GENESIS_HASH
    for event in events:
        payload = dict(event)
        claimed = payload.pop("event_hash", None)
        if payload.get("previous_hash") != previous or claimed != _digest(payload):
            return False
        if not isinstance(claimed, str):
            return False
        previous = claimed
    return True

