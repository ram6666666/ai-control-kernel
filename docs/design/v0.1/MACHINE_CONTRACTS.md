# AI Control Kernel v0.1 — Machine Contracts

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED

This document explains the v0.1 contracts. Normative machine semantics live in `schemas/v0.1/` and `spec/v0.1/`; examples in this document do not override those artifacts.

## 1. Normative contract set

Core serialized I/O:
- `schemas/v0.1/core-contracts.schema.json`

Executable policy and registries:
- `spec/v0.1/permission_policy.yaml`
- `spec/v0.1/condition_detectors.yaml`
- `spec/v0.1/state_machine.yaml`
- `spec/v0.1/status_normalization.yaml`
- `spec/v0.1/ports.yaml`
- `spec/v0.1/capsule_lifecycle.yaml`

Schemas for policy registries:
- `schemas/v0.1/permission-policy.schema.json`
- `schemas/v0.1/state-machine.schema.json`

A contradiction between prose and a normative schema/spec is a design defect. Code must not choose whichever interpretation is convenient.

## 2. SourceRef and provenance

Every field capable of affecting authorization must retain source identity: locator, revision/hash where available, authority class and observation time where relevant.

Authority classes remain:
- `CANONICAL`;
- `AUTHORITATIVE_CURRENT`;
- `NARROWING_AUTHORITY`;
- `EVIDENCE`;
- `DERIVED`.

A derived object never outranks its source.

## 3. EffectiveState

`EffectiveState` is a deterministic read model, never a task database.

It resolves:
- active policy/fingerprint/binding;
- project/task/package identity and current authority;
- execution phase/role/status;
- allowed/forbidden actions and stricter local restrictions;
- dependencies and acceptance gates;
- authoritative inputs/write/checkpoint targets;
- claim observations;
- field-level provenance;
- mechanical condition codes.

Key invariants:
1. command records prove intent/provenance, not successful mutation;
2. a global overlay may repair stale copied global metadata but cannot broaden project semantics or permissions;
3. task/package authority may narrow parent scope but not silently broaden it;
4. conflicting same-rank authorities are not resolved by timestamp or filename;
5. semantic uncertainty is explicit and never converted into an AMBER guess;
6. `health.mechanical_summary` is a state summary only; operation permission is evaluated separately.

## 4. Operation-scoped decisions

Every requested control action declares one `OperationClass` from the closed registry in the core schema.

`TransitionDecision` emits:
- `ALLOW`, `DENY`, `SEMANTIC_REVIEW_REQUIRED`, or `NOOP_IDEMPOTENT`;
- operation-scoped `GREEN`, `AMBER`, or `RED`;
- observed/blocking/nonblocking condition codes;
- PASS/WARN/FAIL checks with evidence;
- missing requirements/conflicts/semantic questions;
- a write plan identifying allowed writer and expected revision.

The evaluator follows `spec/v0.1/permission_policy.yaml`; adapters do not classify risk.

## 5. Condition detection

`spec/v0.1/condition_detectors.yaml` owns mapping from normalized observations to condition codes.

Adapters supply facts such as revisions, receipts, claims, bytes and runtime observations. Core detector logic classifies those facts.

Semantic ambiguity uses `S_SEMANTIC_AMBIGUITY` and returns `SEMANTIC_REVIEW_REQUIRED`; it is not a mechanical RED detector pretending to know meaning.

## 6. State machine and normalization

`spec/v0.1/status_normalization.yaml` maps exact raw statuses into a small normalized lifecycle vocabulary. Unknown states map to `UNKNOWN`; fuzzy linguistic mapping is forbidden.

`spec/v0.1/state_machine.yaml` defines legal normalized edges, required owner classes, predicates and evidence. Project/task extensions require explicit namespace/version/owner metadata and may narrow core behavior, not broaden a prohibition silently.

Transition legality must never be inferred from a plausible-looking status name.

## 7. CandidateCapsule and ExecutionCapsule

The earlier single-capsule concept is split deliberately.

### CandidateCapsule

A pre-claim compiled view used to determine whether an execution unit can be claimed by a compatible executor.

Properties:
- `capsule_type: CANDIDATE`;
- no claim or lease identity;
- `executable: false` by lifecycle rule;
- bound to policy/task/package/input revisions and required capabilities;
- invalidated by relevant source changes.

A CandidateCapsule can never be treated as active execution authority.

### ExecutionCapsule

Created only after an external `DISPATCHER_CLAIM_MANAGER` acquires a claim/lease and the kernel independently verifies that claim against current source revisions.

It additionally binds:
- candidate capsule identity/payload hash;
- claim ID and claimant;
- lease/claim revision;
- claim source provenance;
- execution idempotency key.

Before execution, the executor/launch adapter must revalidate that all bound revisions and the claim are still current. Any relevant change invalidates the capsule and requires recompilation from authority.

The kernel v0.1 does not acquire claims itself.

## 8. Artifact identity

Artifact identity is deterministic only when the adapter supplies actual bytes or an explicitly supported immutable provider revision identity.

Rules:
- SHA-256 is computed from actual byte streams only;
- LLM text/base64 transcription is never a byte transport mechanism;
- semantic similarity never substitutes for byte identity;
- provider revision identity and byte hash remain distinct integrity modes;
- exact-input gates fail if the required artifact cannot be independently retrieved.

## 9. Port boundary

The provider-neutral ports are normative in `spec/v0.1/ports.yaml`.

Core logic may not import provider SDK object models. GitHub, Drive/filesystem, workflow runtimes and model providers belong behind adapters. Equivalent normalized observations from different adapters must yield the same core decision.

## 10. Serialized contract posture

JSON Schema Draft 2020-12 is the external schema boundary. YAML is allowed as a JSON-compatible authoring representation, loaded safely at the edge. Golden byte comparison uses canonical JSON serialization rather than YAML emitter formatting.

Dependency rationale is frozen in `ADAPTER_PORTS_AND_DEPENDENCY_DECISION.md`.

## 11. Explainability requirement

Every kernel decision must be able to emit:
- source revisions read;
- rules/registries applied;
- field-level provenance;
- operation class;
- detected conditions;
- every PASS/WARN/FAIL check;
- semantic questions intentionally deferred.

A bare boolean, bare color, or untraceable model judgment is not an acceptable control decision.

## 12. v0.1 write boundary

In shadow mode the kernel validates, resolves, detects, materializes and compiles isolated outputs. It does not mutate production task/project/global state, acquire production claims, launch production executors, issue scientific audit judgments or promote canonical artifacts.
