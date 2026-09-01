# AI Control Kernel v0.1 — Design Audit 002

status: INTERNAL_DESIGN_AUDIT
verdict: DESIGN_V0_1_FREEZE_READY
implementation_authorized: false
production_cutover_authorized: false

## 1. Scope

This audit re-evaluates the freeze blockers from `DESIGN_AUDIT_001.md` and the complete v0.1 design-freeze gate.

Reviewed:
- `DESIGN_BRIEF.md`;
- `MACHINE_CONTRACTS.md`;
- `CONTROL_SURFACE_MAP.md`;
- `OPERATION_PERMISSION_MATRIX.md`;
- `GOLDEN_FIXTURE_PLAN.md`;
- `ADAPTER_PORTS_AND_DEPENDENCY_DECISION.md`;
- `docs/architecture/INTEGRATION_FIRST.md`;
- `schemas/v0.1/*`;
- `spec/v0.1/*`;
- repository authority split with `ram6666666/ai-`.

This is an internal design audit. It is not an independent external scientific/security review and it does not authorize production cutover.

## 2. Audit-001 blocker closure

### B1 — Executable permission policy: CLOSED / PASS

Closure evidence:
- `spec/v0.1/permission_policy.yaml` is table-driven;
- decision rules are only `DIRECT` or `PREDICATE_GATE`;
- pass/fail results and effect scope are explicit;
- multi-condition merge and unknown-condition behavior are explicit;
- arbitrary expression parsing is absent;
- predicates reference closed `P_*` identifiers from `predicate_registry.yaml`;
- `permission-policy.schema.json` validates the policy shape.

A local static validation using Python 3.13.5, `jsonschema 4.26.0` and PyYAML 6.0.3 produced zero schema-validation errors for the current table-driven permission-policy object/schema pair.

### B2 — Transition state-machine registry: CLOSED / PASS

Closure evidence:
- `spec/v0.1/state_machine.yaml` declares normalized states and explicit edges;
- every edge declares operation class, writer owner and `P_*` predicates;
- terminal/unknown behavior is explicit;
- extension rules require namespace/version/owner and forbid silent broadening;
- `state-machine.schema.json` constrains registry shape and predicate IDs.

Local Draft 2020-12 validation produced zero errors for the current state-machine object/schema pair.

### B3 — Raw-status normalization registry: CLOSED / PASS

Closure evidence:
- exact mapping registry in `status_normalization.yaml`;
- explicit precedence order;
- unknown -> `UNKNOWN`;
- no fuzzy/case/filename/timestamp inference;
- project extensions must be explicit and cannot silently broaden permissions;
- `status-normalization.schema.json` constrains the registry.

### B4 — Adapter ports: CLOSED / PASS

Closure evidence:
- `ports.yaml` defines provider-neutral ports for control sources, immutable events, artifact bytes/identity, runtime observations, executor capabilities, claim observations, optional dispatch and shadow output;
- provider SDK objects do not cross the core boundary;
- adapters provide observations, not control-policy decisions;
- equivalent normalized adapter evidence must preserve core decisions.

### B5 — Dependency posture: CLOSED / PASS

Frozen decision:
- JSON Schema Draft 2020-12 is the serialized contract boundary;
- Python core uses standard library + `jsonschema` + PyYAML safe loading/dumping;
- `pytest` for tests;
- Pydantic is not required in v0.1;
- no agent framework/workflow engine/model SDK/database framework is part of core.

The dependency choice preserves runtime/language neutrality and keeps the first implementation inspectable.

### B6 — Capsule/claim lifecycle: CLOSED / PASS

Closure evidence:
- pre-claim `CandidateCapsule` is non-executable;
- claim acquisition remains external to v0.1 core;
- post-claim `ExecutionCapsule` requires independently verified claim binding;
- claim/source revision changes invalidate the capsule;
- pre-start revalidation is mandatory;
- no undefined `AMBER_ALLOWED` or equivalent token remains.

### B7 — Condition-detector ownership: CLOSED / PASS

Closure evidence:
- `condition_detectors.yaml` maps every v0.1 A/R/S condition to a core detector contract and required observations;
- `predicate_registry.yaml` owns closed `P_*` checks;
- provider adapters cannot classify policy state;
- semantic conditions are separated from mechanical RED conditions.

## 3. Full design-freeze gate

| Gate | Verdict |
|---|---|
| exact module boundary | PASS |
| canonical core input/output schemas | PASS |
| authority precedence and narrowing invariants | PASS |
| single-writer ownership direction | PASS |
| operation-scoped GREEN/AMBER/RED model | PASS |
| executable permission policy | PASS |
| deterministic condition/predicate ownership | PASS |
| explicit state machine | PASS |
| explicit status normalization | PASS |
| CandidateCapsule / ExecutionCapsule contracts | PASS |
| artifact byte-identity boundary | PASS |
| deterministic vs semantic boundary | PASS |
| provider/model/runtime-neutral ports | PASS |
| integration-first architecture | PASS |
| real-incident golden fixture plan | PASS |
| public/private fixture privacy boundary | PASS |
| dependency choice | PASS |
| shadow-mode first / reversible migration | PASS |
| parent control plane remains authoritative | PASS |
| Work/Codex implementation boundary identified | PASS |

## 4. Important non-blocking implementation work

These are required for implementation quality but do not require additional architecture policy invention before coding begins:

1. implement JSON Schema files for remaining auxiliary registries if useful during coding (`ports`, condition detectors, capsule lifecycle);
2. create actual sanitized F01–F10 fixture directories and golden outputs from the frozen specs;
3. implement deterministic canonical JSON serializer;
4. implement filesystem/fixture adapters only for the first package;
5. implement tests proving predicate references resolve and state-machine statuses exist in normalization vocabulary;
6. add CI after the first testable implementation package;
7. add GitHub/Drive/workflow-runtime adapters only after pure core tests pass;
8. perform private shadow E2E before any production cutover;
9. consider independent external architecture/security review before the first production-write cutover.

None of these authorizes the coding model to alter the frozen control semantics silently.

## 5. Remaining design cautions

### C1 — Normalized lifecycle is intentionally lossy

Normalized states exist for common control semantics and materialized views. Project-specific raw state remains authoritative where additional distinctions matter. Implementers must not replace raw project state with the normalized category.

### C2 — Permission policy is restrictive by construction

Unknown operation/condition/predicate cases fail closed or return semantic review. Do not add convenience fallbacks during implementation merely to make fixtures pass.

### C3 — Core schemas are control contracts, not a database schema

Do not turn v0.1 into a persistence/database migration project. Persistence remains adapter/runtime infrastructure.

### C4 — Integration-first still applies

The first implementation must not import Temporal/LangGraph/agent SDKs into core merely because those integrations are expected later.

## 6. Implementation transition

The design is now suitable to freeze and convert into bounded implementation packages.

Recommended first implementation package:

**ACK-IMPL-P01 — Pure deterministic core + schemas + local fixtures**

Scope:
- package/project skeleton;
- schema loading/validation;
- typed/immutable core records where useful;
- canonical JSON serialization;
- exact status normalization;
- predicate registry dispatch;
- condition detection;
- permission evaluator;
- state-machine transition validator;
- CandidateCapsule/ExecutionCapsule compiler/validator;
- local artifact SHA-256;
- F01–F10 sanitized fixtures and unit/golden tests;
- filesystem/fixture adapters only.

Explicitly excluded:
- GitHub/Drive production adapters;
- workflow-runtime dispatch;
- production claims;
- production state writes;
- model-provider invocation;
- scheduler replacement;
- production cutover.

This package is a good Codex task because its policy semantics are now externally frozen.

## 7. Work / Codex verdict

### Work

Still not required for P01. It becomes useful later for multi-package migration or broad private shadow E2E across many operational objects.

### Codex

**NOW RECOMMENDED for ACK-IMPL-P01**, after the design branch is merged and an immutable implementation package is published.

Codex should implement the package; it must not redesign policy or expand scope.

## 8. Audit verdict

`DESIGN_V0_1_FREEZE_READY`

Meaning:
- the remaining work can be expressed as bounded implementation/testing tasks without requiring a coding model to invent core control semantics;
- design may be merged as the v0.1 implementation baseline;
- implementation remains separately gated;
- production cutover remains explicitly unauthorized.
