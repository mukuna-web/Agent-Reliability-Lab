# Deployment runbook

Run `uv run --extra dev make verify`, `uv run --extra dev pip-audit`, and `uv run --extra dev make demo`. Verify deterministic reruns, hash-chain checks, JSON/CSV/HTML outputs, dashboard expansion, and Print/PDF. Keep production traces out of a public deployment; use a controlled artifact store and least-privilege adapter credentials.

Roll back a strategy/report version on metric drift, trace failure, or missing evidence. For accidental data ingestion, stop the adapter, preserve minimal evidence, delete unintended artifacts where authorized, rotate exposed secrets, and document scope.
