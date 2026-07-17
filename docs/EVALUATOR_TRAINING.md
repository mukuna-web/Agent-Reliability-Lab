# Evaluator training guide

1. Confirm scenario, seed, steps, fault placement, repeat count, and strategy.
2. Verify the trace hash chain before trusting metrics.
3. Read pass/fail and failure reason before aggregate rates.
4. Compare faults injected/recovered, calls, and virtual latency; do not equate simulator latency with a production SLA.
5. Record a named human decision to accept, reject, or request a scenario change outside the generated artifact before promoting a strategy.

Calibrate two reviewers on the same synthetic suite. Stop evaluation when runs are missing, traces fail verification, scenario coverage is insufficient, or adapter provenance is unclear.
