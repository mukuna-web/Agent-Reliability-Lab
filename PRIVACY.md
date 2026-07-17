# Privacy and local analysis

The bundled lab uses synthetic TOML scenarios and a deterministic local simulator. It makes no model or provider call. Reports contain declared scenario labels, strategies, aggregate metrics, and synthetic traces; CSV excludes trace detail.

Real-agent adapters may ingest prompts, outputs, provider metadata, or identifiers. Before enabling one, minimize fields, redact secrets, isolate outputs, define retention/deletion, and update this boundary. Use synthetic data for public demos and delete run directories plus exported JSON/CSV/HTML/PDF together.
