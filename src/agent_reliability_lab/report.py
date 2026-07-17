from __future__ import annotations

import csv
import html
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from agent_reliability_lab.models import RunResult

_REPORT_COUNT_METRICS = (
    "faults_injected",
    "faults_recovered",
    "tool_calls",
    "virtual_latency_ms",
)
_SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def _csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(_SPREADSHEET_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _required_bool(payload: Mapping[str, Any], field: str) -> bool:
    value = payload.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _nonnegative_integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a non-negative integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative integer") from exc
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError(f"{field} must be a non-negative integer")
    return int(number)


def _manifest(item: RunResult | Mapping[str, Any]) -> dict[str, Any]:
    raw = item.manifest() if isinstance(item, RunResult) else dict(item)
    metrics = raw.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError("metrics must be an object")

    normalized = dict(raw)
    normalized["scenario"] = _required_text(raw, "scenario")
    normalized["strategy"] = _required_text(raw, "strategy")
    normalized["passed"] = _required_bool(raw, "passed")
    normalized_metrics = dict(metrics)
    for name in _REPORT_COUNT_METRICS:
        normalized_metrics[name] = _nonnegative_integer(
            metrics.get(name), f"metrics.{name}"
        )
    normalized["metrics"] = normalized_metrics
    return normalized


def _summary(manifests: Sequence[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in manifests:
        grouped[str(item["strategy"])].append(item)
    output: dict[str, dict[str, float | int]] = {}
    for strategy, rows in sorted(grouped.items()):
        count = len(rows)
        passed = sum(bool(row["passed"]) for row in rows)
        calls = sum(float(row["metrics"]["tool_calls"]) for row in rows)
        output[strategy] = {
            "runs": count,
            "passed": passed,
            "pass_rate": passed / count if count else 0.0,
            "average_tool_calls": calls / count if count else 0.0,
        }
    return output


def write_report(
    results: Sequence[RunResult | Mapping[str, Any]], output: Path
) -> Path:
    manifests = [_manifest(item) for item in results]
    summary = _summary(manifests)
    payload = {"schema_version": 1, "summary": summary, "runs": manifests}
    json_path = output.with_suffix(".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path = output.with_suffix(".csv")
    ordered = sorted(
        manifests,
        key=lambda value: (str(value["scenario"]), str(value["strategy"])),
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "scenario",
                "strategy",
                "passed",
                "faults_injected",
                "faults_recovered",
                "tool_calls",
                "virtual_latency_ms",
            )
        )
        writer.writerows(
            tuple(
                _csv_cell(value)
                for value in (
                    row["scenario"],
                    row["strategy"],
                    row["passed"],
                    row["metrics"]["faults_injected"],
                    row["metrics"]["faults_recovered"],
                    row["metrics"]["tool_calls"],
                    row["metrics"]["virtual_latency_ms"],
                )
            )
            for row in ordered
        )

    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['scenario']))}</td>"
        f"<td>{html.escape(str(row['strategy']))}</td>"
        f"<td><span class=\"pill {'pass' if row['passed'] else 'fail'}\">"
        f"{'PASS' if row['passed'] else 'FAIL'}</span></td>"
        f"<td>{row['metrics']['faults_injected']}</td>"
        f"<td>{row['metrics']['faults_recovered']}</td>"
        f"<td>{row['metrics']['tool_calls']}</td>"
        f"<td>{row['metrics']['virtual_latency_ms']}</td>"
        "</tr>"
        for row in sorted(manifests, key=lambda value: (str(value["scenario"]), str(value["strategy"])))
    )
    cards = "".join(
        f"<article><h2>{html.escape(strategy)}</h2>"
        f"<strong>{values['pass_rate']:.0%}</strong><span> pass rate</span>"
        f"<p>{values['passed']} of {values['runs']} scenarios passed</p></article>"
        for strategy, values in summary.items()
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Agent Reliability Lab</title><style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; background:#0b1020; color:#e8eefc }}
body {{ max-width:1100px; margin:auto; padding:48px 24px }} h1 {{ font-size:clamp(2rem,6vw,4rem); margin:.2em 0 }}
.eyebrow {{ color:#8ab4ff; text-transform:uppercase; letter-spacing:.15em }} .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin:32px 0 }}
article {{ background:#151d33; border:1px solid #263452; border-radius:16px; padding:22px }} article strong {{ font-size:2.5rem }}
table {{ width:100%; border-collapse:collapse; background:#11182b }} th,td {{ padding:12px; border-bottom:1px solid #263452; text-align:left }}
.pill {{ padding:4px 9px; border-radius:999px; font-weight:700 }} .pass {{ background:#123d31; color:#7de2b8 }} .fail {{ background:#4b2028; color:#ff9ca8 }}
.scroll {{ overflow:auto; border-radius:14px; border:1px solid #263452 }} footer {{ color:#96a3bd; margin-top:28px }}
summary {{ cursor:pointer; color:#8ab4ff; margin:12px 0 }} @media print {{ :root {{ color-scheme:light }} body {{ padding:0 }} }}
</style></head><body><p class="eyebrow">Fault injection benchmark</p><h1>Agent Reliability Lab</h1>
<p>Deterministic comparison of recovery strategies under tool and provider failures.</p>
<section class="cards">{cards}</section><details open><summary>Per-scenario evidence</summary><div class="scroll"><table><thead><tr><th>Scenario</th><th>Strategy</th><th>Result</th><th>Faults</th><th>Recovered</th><th>Calls</th><th>Virtual ms</th></tr></thead><tbody>{rows}</tbody></table></div></details>
<footer>Metrics are generated by the deterministic simulator and are not production SLA claims.</footer></body></html>"""
    output.write_text(document, encoding="utf-8")
    return json_path
