# AI Control Kernel v0.1 — P01 implementation

This branch implements `ACK-IMPL-P01`: a pure deterministic core, Draft
2020-12 validation, exact status normalization, closed predicate and policy
dispatch, explicit lifecycle validation, revision-bound capsules, immutable
event materialization, SHA-256 byte identity, and local fixture adapters.

The core imports only the Python standard library, `jsonschema`, and PyYAML.
Provider SDKs, workflow runtimes, model providers, schedulers, databases, and
production state writers are intentionally outside this package.

## Commands

```text
python -m pip install -c constraints.txt -e .[dev]
ruff check src tests
ruff format --check src tests
mypy --strict src
pytest --cov=ai_control_kernel --cov-branch --cov-fail-under=95
python -m build --sdist --wheel
```

Tests read frozen registries from `spec/v0.1/` and schemas from
`schemas/v0.1/`. Golden output is canonical UTF-8 JSON and is never refreshed
automatically.

