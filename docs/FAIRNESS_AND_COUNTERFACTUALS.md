# Counterfactual and fairness checks

Scenario display labels must not alter recovery behavior. Tests run otherwise identical scenarios with different names and require identical pass status and metrics. Determinism tests require identical run IDs, metrics, and traces for identical complete inputs.

Expand tests by varying labels, description text, ordering where semantics are unchanged, and adapter-only identity metadata. These are engineering invariance checks; the lab has no demographic model and cannot establish fairness of a deployed agent or scenario portfolio.
