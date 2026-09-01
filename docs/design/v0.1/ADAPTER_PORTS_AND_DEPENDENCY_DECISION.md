# AI Control Kernel v0.1 — Adapter Ports and Dependency Decision

status: DESIGN_DECISION
implementation_authorized: false

## Decision

v0.1 uses a deliberately small Python core with language-neutral serialized contracts.

### External contract boundary

- **JSON Schema Draft 2020-12** is the normative schema format for machine contracts.
- YAML may be used as a human-editable representation of JSON-compatible data, but YAML syntax is not itself the canonical semantic contract.
- Schema identifiers and contract versions are explicit and immutable once released.

### Python validation layer

Use the Python `jsonschema` package with an explicit Draft 2020-12 validator.

Rationale:
- current `jsonschema` documentation states full Draft 2020-12 support;
- validation errors expose paths/schema paths and can therefore feed explainable control decisions;
- schemas remain usable outside Python;
- this avoids making a Python object-model framework the portable control contract.

### YAML loading

Use PyYAML only at the serialization/adapter boundary and only through `safe_load` / `safe_dump` equivalents.

Rules:
- unsafe object construction is forbidden;
- parsed YAML must become JSON-compatible primitive structures before entering the core;
- deterministic comparison/golden output uses canonical JSON serialization, not PyYAML emitter formatting.

### Internal Python models

v0.1 does **not require Pydantic**.

Use:
- standard-library `dataclasses` where immutable typed records materially help implementation;
- standard-library `typing.Protocol` for ports;
- standard dictionaries/lists for validated schema payloads where additional class layers add no value;
- `enum` for closed operation/result/state identifiers where useful;
- `hashlib.sha256` for actual byte hashing.

Pydantic may be reconsidered later if implementation evidence shows substantial validation/serialization boilerplate that JSON Schema + small domain records do not handle well. It is not part of the v0.1 freeze dependency set.

## Required dependency set

Runtime:
- Python standard library;
- `jsonschema`;
- `PyYAML` for YAML interoperability.

Development/test:
- `pytest`;
- optional property-testing library only if state-machine testing demonstrates a real coverage benefit.

No agent framework, workflow engine, model SDK, database ORM, web framework or provider SDK belongs in `core/`.

## Deterministic serialization

Canonical machine output for golden comparison is UTF-8 JSON with:
- sorted object keys;
- explicit separators;
- no NaN/Infinity extensions;
- normalized UTC timestamp strings defined by schema;
- stable enum strings;
- no implicit YAML typing in the canonical byte representation.

Human-facing YAML may be generated from the canonical object but is not used for byte-for-byte golden truth.

## Port boundary

The normative port list is `spec/v0.1/ports.yaml`.

The core may depend only on normalized port return types. Provider-specific adapters may depend on GitHub, Drive/filesystem, Temporal, LangGraph, Restate, Dapr, OpenAI, Anthropic or other SDKs in the future, but those objects do not cross the core boundary.

This preserves the Integration-First rule: mature infrastructure is integrated behind adapters; the kernel owns only missing authority/provenance/control semantics.

## Initial adapter implementation scope

The first implementation package should include only adapters needed for local/public fixtures:
- filesystem control-source reader;
- filesystem immutable-event reader;
- filesystem artifact byte reader;
- fixture runtime-observation source;
- fixture executor-capability source;
- filesystem shadow-output sink.

GitHub/Drive/workflow-runtime adapters are later bounded packages after pure core tests pass. This prevents network/provider concerns from obscuring core correctness.

## Version posture

Do not hard-code a library's latest minor version into design semantics. Implementation may pin a tested compatible range in project metadata and CI. The control contract depends on JSON Schema Draft 2020-12 semantics, not on a particular `jsonschema` internal API beyond the supported public validator interface.

## Security posture

- YAML parsing uses safe loaders only.
- byte identity is computed from actual byte streams only.
- no adapter may execute content merely by deserializing it.
- provider credentials remain outside normalized core objects.
- signed/ephemeral provider URLs must not be persisted in public fixtures.

## Decision status

B4 (adapter port contracts): CLOSED AT DESIGN LEVEL.

B5 (dependency choice): CLOSED AT DESIGN LEVEL.

Implementation remains blocked until the remaining freeze items and second design audit pass.
