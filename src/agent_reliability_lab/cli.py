from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_reliability_lab.engine import run_scenario, run_suite
from agent_reliability_lab.report import write_report
from agent_reliability_lab.scenario import ScenarioError, load_scenario
from agent_reliability_lab.storage import load_runs, write_run
from agent_reliability_lab.strategy import Strategy
from agent_reliability_lab.trace import load_trace, verify_trace


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-reliability-lab")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a scenario")
    validate.add_argument("scenario", type=Path)

    run = commands.add_parser("run", help="run one scenario")
    run.add_argument("scenario", type=Path)
    run.add_argument("--strategy", default="resilient")
    run.add_argument("--output", type=Path, default=Path("runs"))

    suite = commands.add_parser("suite", help="benchmark every TOML scenario in a directory")
    suite.add_argument("scenarios", type=Path)
    suite.add_argument("--strategies", default="baseline,resilient")
    suite.add_argument("--output", type=Path, default=Path("benchmark"))

    compare = commands.add_parser("compare", help="rebuild a report from stored runs")
    compare.add_argument("runs", type=Path)
    compare.add_argument("--output", type=Path, default=Path("reliability-report.html"))

    replay = commands.add_parser("replay", help="verify a stored trace hash chain")
    replay.add_argument("trace", type=Path)
    return parser


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            scenario = load_scenario(args.scenario)
            _print(
                {
                    "status": "valid",
                    "name": scenario.name,
                    "steps": len(scenario.steps),
                    "faults": len(scenario.faults),
                }
            )
            return 0
        if args.command == "run":
            scenario = load_scenario(args.scenario)
            result = run_scenario(scenario, Strategy.named(args.strategy))
            run_dir = write_run(result, args.output)
            _print({"run_id": result.run_id, "run_dir": str(run_dir.resolve()), "passed": result.passed})
            return 0
        if args.command == "suite":
            paths = sorted(args.scenarios.glob("*.toml"))
            if not paths:
                raise ValueError(f"no TOML scenarios found in {args.scenarios}")
            scenarios = [load_scenario(path) for path in paths]
            strategies = [Strategy.named(name) for name in args.strategies.split(",") if name.strip()]
            if not strategies:
                raise ValueError("at least one strategy is required")
            results = run_suite(scenarios, strategies)
            runs_dir = args.output / "runs"
            for result in results:
                write_run(result, runs_dir)
            report = args.output / "reliability-report.html"
            write_report(results, report)
            _print({"runs": len(results), "report": str(report.resolve())})
            return 0
        if args.command == "compare":
            manifests = load_runs(args.runs)
            if not manifests:
                raise ValueError(f"no run manifests found in {args.runs}")
            write_report(manifests, args.output)
            _print({"runs": len(manifests), "report": str(args.output.resolve())})
            return 0
        if args.command == "replay":
            valid = verify_trace(load_trace(args.trace))
            _print({"trace": str(args.trace), "valid": valid})
            return 0 if valid else 1
    except (OSError, ScenarioError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2

