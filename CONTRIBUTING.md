# Contributing

1. Create an isolated Python 3.11+ environment.
2. Install `pip install -e ".[dev]"`.
3. Add or update a failing test before changing behavior.
4. Run `make verify` and `make build`.
5. Keep scenarios synthetic, deterministic, and free of credentials.

New fault types should document their trigger, recovery contract, trace events, and expected
baseline/resilient behavior.

