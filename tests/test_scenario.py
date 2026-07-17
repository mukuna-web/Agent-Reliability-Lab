from __future__ import annotations

from pathlib import Path

import pytest

from agent_reliability_lab.scenario import ScenarioError, load_scenario
from tests.helpers import write_scenario


def test_loads_typed_scenario(tmp_path: Path) -> None:
    scenario = load_scenario(write_scenario(tmp_path))

    assert scenario.name == "timeout-case"
    assert scenario.seed == 17
    assert scenario.steps[0].tool == "fetch_logs"
    assert scenario.steps[0].result == {"status": "healthy", "incidents": 0}
    assert scenario.faults[0].kind == "timeout"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("kind", "telepathy", "unsupported fault kind"),
        ("step", 9, "references missing step"),
        ("occurrence", 0, "occurrence must be positive"),
        ("repeat", 0, "repeat must be positive"),
    ],
)
def test_rejects_invalid_faults(
    tmp_path: Path, field: str, value: str | int, message: str
) -> None:
    values: dict[str, str | int] = {
        "fault": "timeout",
        "step": 0,
        "occurrence": 1,
        "repeat": 1,
    }
    values["fault" if field == "kind" else field] = value
    path = write_scenario(
        tmp_path,
        fault=str(values["fault"]),
        step=int(values["step"]),
        occurrence=int(values["occurrence"]),
        repeat=int(values["repeat"]),
    )

    with pytest.raises(ScenarioError, match=message):
        load_scenario(path)


def test_rejects_missing_steps(tmp_path: Path) -> None:
    path = tmp_path / "empty.toml"
    path.write_text('[scenario]\nname = "empty"\n', encoding="utf-8")

    with pytest.raises(ScenarioError, match="at least one step"):
        load_scenario(path)


def test_rejects_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "broken.toml"
    path.write_text("[scenario\n", encoding="utf-8")

    with pytest.raises(ScenarioError, match="invalid TOML"):
        load_scenario(path)

