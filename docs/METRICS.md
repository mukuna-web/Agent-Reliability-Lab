# Outcome metrics

Track pass rate, faults recovered/injected, tool-call overhead, virtual-latency overhead, trace verification rate, scenario coverage, reviewer acceptance of findings, correction rate, and analysis time saved versus manual trace inspection. Always report scenario count, strategy version, seed set, and confidence/variation when introducing nondeterministic adapters.

Do not optimize pass rate alone; a strategy can retry excessively or avoid meaningful work. Suggested synthetic gates: 100% trace verification, deterministic repeatability, zero unexplained label-counterfactual differences, and human review of every production-promotion recommendation.
