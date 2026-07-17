# Agent Reliability Lab MVP — TDD Evidence

## Source and journeys

There was no source plan file; journeys were derived during this TDD run.

1. A reliability engineer can declare deterministic tool workflows and injected faults in TOML.
2. A developer can compare baseline and resilient strategies under the same failures.
3. A reviewer can inspect and verify content-addressed, hash-chained run traces.
4. A portfolio visitor can run the complete benchmark without an API key, model, or network.

## RED evidence

Tests were created before production modules and executed with:

```text
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m pytest -q
```

Result: collection failed with three `ModuleNotFoundError` errors for the missing
`agent_reliability_lab` package. The test files compiled; the missing implementation was the
intended compile-time RED signal.

## GREEN and final evidence

The first minimal implementation produced:

```text
25 passed in 0.23s
```

Direct CLI coverage and release verification then produced:

```text
30 passed in 0.33s
Total branch coverage: 95.65%
Ruff: All checks passed
Ruff security rules: All checks passed
mypy --strict: Success; 10 source files checked
Secret-pattern scan: PASS
pip-audit: No known vulnerabilities found
Build: wheel and source distribution created successfully
Clean-wheel smoke test: 12 benchmark runs and an HTML report generated successfully
```

## Guarantee index

| Guarantee | Evidence | Type | Result |
|---|---|---|---|
| Invalid scenarios and fault definitions are rejected | `tests/test_scenario.py` | unit | PASS |
| Baseline fails and resilient strategy recovers as specified | `tests/test_engine.py` | integration | PASS |
| Timeout, provider, malformed, partial, stale, and repeated-call faults are deterministic | `tests/test_engine.py` | unit/integration | PASS |
| Run IDs and stored artifacts are idempotent | `tests/test_trace_report.py` | integration | PASS |
| Trace mutation is detected by the SHA-256 chain | `tests/test_trace_report.py` | security | PASS |
| Installed CLI validates, runs, compares, and reports | `tests/test_cli.py`, `tests/test_cli_e2e.py` | E2E | PASS |

## Known boundary

The built-in executor is a deterministic simulator. It verifies recovery mechanics and evidence
generation, but it does not claim that a real model will select the correct tools or recover under
provider-specific behavior. Real-agent adapters remain an explicit integration layer.

