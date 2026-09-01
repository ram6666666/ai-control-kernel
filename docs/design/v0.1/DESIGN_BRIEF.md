# AI Control Kernel v0.1 — Minimal Design Brief

status: WORKING_DESIGN
implementation_authorized: false
production_cutover_authorized: false

## 1. Purpose

AI Control Kernel is a small deterministic control layer for long-running work across replaceable AI models, tools and workflow runtimes.

It exists to remove mechanically decidable control work from LLM reasoning while preserving user-owned authority, provenance, project semantics, independent audit and model/runtime portability.

It is **not** another autonomous-agent framework and is **not** a replacement for mature workflow, scheduling, storage or model infrastructure.

Core principle:

**Deterministic software handles mechanics; AI handles semantic reasoning; humans retain goals, material scope and high-impact judgment. Mature infrastructure is integrated behind adapters rather than rebuilt.**

## 2. v0.1 deterministic modules

### K1 — Schema Validator

Validates versioned serialized control contracts using JSON Schema Draft 2020-12.

### K2 — Effective-State Resolver

Computes one explicit effective control view from declared authority sources and domain-specific precedence rules, retaining field-level provenance.

It may resolve stale copied global metadata through stronger current authority, but cannot silently change project/task semantics or widen permissions.

### K3 — Condition and Transition Evaluator

Detects mechanical condition codes, identifies semantic-review boundaries, validates explicit state-machine edges and evaluates operation-specific permission from table-driven policy.

It returns `ALLOW`, `DENY`, `SEMANTIC_REVIEW_REQUIRED`, or `NOOP_IDEMPOTENT`; it never invents intent.

### K4 — Event Materializer

Validates immutable lifecycle events and derives bounded shadow read models such as latest lifecycle state, claims, artifact-verification status and completion evidence.

Derived views are caches/read models, not peer authority.

### K5 — Artifact Identity

Computes/verifies artifact identity only from actual byte streams or explicitly supported immutable provider-revision identity.

LLM text/base64 transcription is never a binary transport mechanism.

### K6 — Capsule Compiler

Compilation has two stages:

1. **CandidateCapsule** — pre-claim, non-executable, revision-bound candidate view;
2. **ExecutionCapsule** — created only after an external claim/lease is acquired and independently verified against current revisions.

The v0.1 kernel does not acquire production claims or dispatch work.

## 3. Normative machine artifacts

Core I/O schema:
- `schemas/v0.1/core-contracts.schema.json`

Executable control specifications:
- `spec/v0.1/permission_policy.yaml`
- `spec/v0.1/predicate_registry.yaml`
- `spec/v0.1/condition_detectors.yaml`
- `spec/v0.1/state_machine.yaml`
- `spec/v0.1/status_normalization.yaml`
- `spec/v0.1/ports.yaml`
- `spec/v0.1/capsule_lifecycle.yaml`

Registry schemas currently required by the freeze gate:
- `schemas/v0.1/permission-policy.schema.json`
- `schemas/v0.1/state-machine.schema.json`

`MACHINE_CONTRACTS.md` explains these artifacts but does not override them.

## 4. Authority and semantic boundary

The kernel may decide mechanically:
- schema validity;
- exact revision/hash mismatch;
- explicit authority precedence;
- dependency/gate presence;
- claim/idempotency conflict;
- declared state-machine legality;
- operation permission from closed policy tables;
- byte hash/size when bytes are supplied;
- deterministic materialization of accepted events.

The kernel must defer:
- scientific correctness;
- writing quality;
- material project rescope;
- ambiguous requirement meaning;
- adequacy/value judgment;
- interpretation of unresolved legacy textual authority.

Semantic boundaries are emitted as `S_*` conditions plus explicit questions.

## 5. Risk model

A/R/S conditions are distinct:
- `A_*`: mechanical degradation that may be nonblocking for some operations;
- `R_*`: mechanical blocker for ordinary authority effects;
- `S_*`: semantic-review boundary.

Permission is computed for the requested operation. A stale derived snapshot may be AMBER for execution while an artifact identity mismatch is RED for audit/publication.

The normative evaluator is `spec/v0.1/permission_policy.yaml`; no provider adapter may decide risk.

## 6. State and lifecycle model

Raw statuses are normalized only by exact registered mappings. Unknown status -> `UNKNOWN`; fuzzy linguistic inference is forbidden.

Legal transitions are explicit registry edges with writer owner, predicates and evidence requirements.

Task/package-specific extensions require namespace/version/owner metadata and may narrow core behavior without silently broadening prohibitions.

## 7. Integration boundary

Core code depends only on provider-neutral ports. GitHub, Drive/filesystem, workflow engines, model providers and future schedulers belong behind adapters.

Equivalent normalized observations from two adapters must produce the same core decision.

Initial implementation should use only local/filesystem fixture adapters. GitHub/Drive/workflow-runtime adapters come after pure core regression tests.

## 8. Dependency posture

External contracts: JSON Schema Draft 2020-12.

Python v0.1 runtime:
- standard library;
- `jsonschema`;
- PyYAML using safe loading/dumping only.

Testing:
- `pytest`;
- property testing only if it materially improves state-machine coverage.

No Pydantic, agent framework, workflow engine, model SDK, ORM or database is required in the v0.1 core.

## 9. Shadow-mode migration

v0.1 begins read-only/shadow:
1. read existing real control objects through adapters;
2. validate/resolve/detect/materialize/compile isolated results;
3. compare against current controller/reconciler interpretation;
4. adjudicate every discrepancy;
5. convert useful incidents into sanitized public regression fixtures;
6. propose only a narrow reversible mechanical cutover after sustained agreement.

The first cutover should be schema validation, effective-state resolution or deterministic artifact hashing—not scheduler ownership or scientific acceptance.

## 10. Regression basis

The fixture plan covers real observed failure shapes including:
- stale copied policy metadata;
- dirty policy fingerprint;
- duplicate/idempotent claim cases;
- scheduler wake without first durable receipt;
- unexpected worker disable;
- independent audit input unavailable;
- lossy artifact transport/hash mismatch;
- noncanonical shadow artifact mistaken for baseline;
- event/snapshot divergence;
- stricter local restrictions surviving global overlays;
- cross-runtime and cross-model adapter neutrality.

Public fixtures are sanitized structural reproductions; real private operational locators stay in the parent control plane.

## 11. Explicit non-responsibilities

v0.1 does not:
- choose scientific truth;
- rewrite project goals;
- issue autonomous scientific acceptance;
- acquire production claims;
- launch Work/Codex/model sessions;
- replace the production scheduler;
- implement a new workflow engine;
- create a second global task truth;
- perform arbitrary binary transport;
- auto-repair semantic conflicts;
- migrate every legacy project into a database.

## 12. Design-freeze gate

`DESIGN_V0_1_FREEZE_READY` requires:
- exact module boundary;
- normative core schemas;
- executable permission policy and predicates;
- explicit condition-detector ownership;
- explicit state-machine and normalization registries;
- provider-neutral ports;
- CandidateCapsule/ExecutionCapsule claim lifecycle;
- deterministic/semantic boundary;
- golden/negative fixture plan;
- minimal dependency decision;
- integration-first boundary;
- shadow-first reversible migration;
- current production control plane remaining authoritative;
- a second design audit finding no unresolved policy/contract blocker.

Implementation and production cutover are separately authorized transitions.

## 13. Work / Codex boundary

Work is not needed for architecture closure.

Codex becomes useful only after design freeze, when it can receive bounded implementation packages for schemas/models/evaluator/compiler/tests without being asked to invent policy.
