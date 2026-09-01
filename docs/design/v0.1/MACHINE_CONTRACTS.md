# AI Control Kernel v0.1 — Machine Contracts

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED

This document defines the semantic machine contracts that must be frozen before code is written. The eventual implementation may use JSON Schema, Pydantic, dataclasses, or another small typed layer, but it must preserve these semantics.

## A. Common primitives

### SourceRef
Every resolved field that can affect authorization must be traceable to a concrete source.

```yaml
source_type: POLICY | REGISTRY | PROJECT_STATE | TASK_AUTHORITY | PACKAGE_AUTHORITY | IMMUTABLE_EVENT | ARTIFACT_RECORD | RUNTIME_OBSERVATION | DERIVED_VIEW
locator: string
revision: string | null
content_hash: string | null
observed_at: timestamp | null
authority_class: CANONICAL | AUTHORITATIVE_CURRENT | NARROWING_AUTHORITY | EVIDENCE | DERIVED
```

### ProvenancedValue
```yaml
value: any
source: SourceRef
resolution_rule: string
warnings: []
```

### IntegrityVerdict
```yaml
status: VERIFIED | UNVERIFIED | MISMATCH | NOT_APPLICABLE
algorithm: SHA256 | GIT_BLOB_SHA | PROVIDER_REVISION | OTHER | null
expected: string | null
observed: string | null
source: SourceRef | null
```

## B. EffectiveState

`EffectiveState` is a deterministic read model. It is never an independent source of truth.

```yaml
schema_version: ack.effective_state.v0.1
resolved_at: timestamp
resolution_id: string

sources:
  global_policy_fingerprint: SourceRef
  project_registry_entry: SourceRef | null
  project_state: SourceRef | null
  task_authority: SourceRef | null
  package_authority: SourceRef | null
  immutable_events: [SourceRef]
  runtime_observations: [SourceRef]

policy:
  epoch: ProvenancedValue
  fingerprint_status: ProvenancedValue
  handshake_status: ProvenancedValue | null
  project_compatibility: ProvenancedValue | null

identity:
  project_id: ProvenancedValue
  task_id: ProvenancedValue | null
  package_id: ProvenancedValue | null

execution:
  phase: ProvenancedValue | null
  role: ProvenancedValue | null
  objective: ProvenancedValue | null
  raw_status: ProvenancedValue | null
  normalized_status: ProvenancedValue | null
  implementation_authorized: ProvenancedValue | null
  production_authorized: ProvenancedValue | null

constraints:
  allowed_actions: [ProvenancedValue]
  forbidden_actions: [ProvenancedValue]
  stricter_local_restrictions: [ProvenancedValue]
  dependencies: [ProvenancedValue]
  acceptance_gates: [ProvenancedValue]

storage:
  write_targets: [ProvenancedValue]
  authoritative_inputs: [ProvenancedValue]
  checkpoint_targets: [ProvenancedValue]

claim:
  active_claim_id: ProvenancedValue | null
  claimant: ProvenancedValue | null
  lease_state: ProvenancedValue | null

health:
  mechanical_summary: GREEN | AMBER | RED
  authority_resolution: UNIQUE | AMBIGUOUS | CONFLICT
  semantic_review_required: bool
  observed_condition_codes: []
  warnings: []
  blockers: []

provenance_trace:
  <field_path>: SourceRef
```

`health.mechanical_summary` is a conservative state summary. It is **not** the final permission for every possible operation. Operation permission is computed separately by `TransitionDecision` using the requested operation and relevant conditions.

### EffectiveState resolution invariants

1. **A derived view never outranks its source.** `PROGRESS_SNAPSHOT`, `CURRENT_HANDOFF`, generated indexes and future capsules may be read as hints/evidence but cannot override current authoritative task/project state.
2. **An immutable command record proves intent/provenance, not successful state mutation.** A command becomes current execution authority only through the corresponding authoritative task/project/package state transition.
3. **Global overlay may repair stale copied global metadata only.** It cannot widen project-local permissions, production authorization, scientific scope or acceptance gates.
4. **Narrowing is monotonic.** A package may narrow a task; a task may narrow a project. A lower-level authority cannot silently broaden a higher-level prohibition.
5. **Stricter local restrictions survive.** If current project/task/package state imposes a stricter restriction than the global default, the stricter restriction is retained unless an explicit authorized state transition removes it.
6. **Conflicting same-rank authorities do not resolve by timestamp or filename.** Result is `authority_resolution: CONFLICT` and mechanical RED unless a declared reconciliation rule exists.
7. **Historical text is not active authority merely because it is present in the same file.** Version/supersession metadata must identify the active rule; otherwise return semantic review rather than infer from prose order.
8. **Semantic uncertainty is represented explicitly.** It must not be hidden inside an AMBER permission or repaired by linguistic guesswork.

## C. OperationClass

Operation risk is evaluated for one declared class:

```text
READ_DIAGNOSE
DISCUSS_PLAN
SHADOW_VALIDATE
WRITE_DIAGNOSTIC_EVIDENCE
PRODUCE_NONCANONICAL_WORKING_ARTIFACT
CLAIM_EXECUTION_UNIT
EXECUTE_AND_CHECKPOINT
PUBLISH_AUTHORITATIVE_ARTIFACT
ISSUE_INDEPENDENT_AUDIT_VERDICT
MUTATE_CONTROL_STATE
PROMOTE_OR_ACCEPT_CANONICAL
LIVENESS_REPAIR
POLICY_RECONCILIATION
```

The operation taxonomy is versioned. Unknown operations are never mapped linguistically to the "closest" known operation; they require explicit mapping or semantic review.

## D. ProposedTransition

The kernel validates a transition request; it does not generate project intent.

```yaml
schema_version: ack.transition_request.v0.1
request_id: string
requested_at: timestamp
operation_class: OperationClass
actor:
  role: string
  actor_id: string | null
source_authorization: [SourceRef]
project_id: string
task_id: string | null
package_id: string | null
expected_current_state:
  raw_status: string | null
  state_revision: string | null
transition:
  type: string
  target_status: string | null
  requested_mutations: object
idempotency_key: string
required_evidence: [SourceRef]
```

## E. TransitionDecision

```yaml
schema_version: ack.transition_decision.v0.1
decision_id: string
request_id: string
decided_at: timestamp
operation_class: OperationClass
result: ALLOW | DENY | SEMANTIC_REVIEW_REQUIRED | NOOP_IDEMPOTENT
risk_mode: GREEN | AMBER | RED
observed_condition_codes: []
blocking_condition_codes: []
nonblocking_warning_codes: []
checks:
  - check_id: string
    result: PASS | FAIL | WARN | NOT_APPLICABLE
    evidence: [SourceRef]
    reason: string
conflicts: []
missing_requirements: []
semantic_questions: []
write_plan:
  allowed: bool
  required_event_type: string | null
  target_writer_role: string | null
  expected_current_revision: string | null
```

`risk_mode` is operation-scoped. A stale derived snapshot can be AMBER for `READ_DIAGNOSE`, while an exact artifact mismatch is RED for `ISSUE_INDEPENDENT_AUDIT_VERDICT`.

A semantic ambiguity may produce `result: SEMANTIC_REVIEW_REQUIRED`; `risk_mode` then reflects whether ordinary execution of that requested operation must remain blocked until review.

### Mandatory deterministic transition checks

- operation class is explicitly known;
- expected revision/status still current;
- dependencies satisfied;
- actor role allowed for the requested state surface;
- no active conflicting claim/lease;
- all required integrity evidence present;
- no higher-level prohibition is widened;
- required audit/acceptance gate cannot be bypassed;
- duplicate `idempotency_key` is either an exact replay (`NOOP_IDEMPOTENT`) or conflict (`DENY`);
- transition edge exists in the declared state machine;
- operation-specific GREEN/AMBER/RED permission rule passes;
- transition does not require semantic interpretation that the kernel cannot perform.

## F. ExecutionCapsule

The capsule is a short-lived compiled view for exactly one bounded execution unit. It must be reproducible from source revisions and must never become a second task database.

```yaml
schema_version: ack.execution_capsule.v0.1
capsule_id: string
compiled_at: timestamp
expires_or_invalidates_on:
  - source_revision_change
  - policy_epoch_change
  - task_or_package_authority_change
  - claim_change

source_revisions:
  policy_fingerprint: SourceRef
  project_registry: SourceRef | null
  project_state: SourceRef | null
  task_authority: SourceRef
  package_authority: SourceRef | null
  latest_checkpoint: SourceRef | null

identity:
  project_id: string
  task_id: string
  package_id: string | null
  execution_unit_id: string

execution:
  phase: string
  role: string
  objective: string
  allowed_actions: []
  forbidden_actions: []

inputs:
  authoritative_inputs:
    - locator: string
      identity: IntegrityVerdict
      purpose: string
  reference_packet: SourceRef | null

outputs:
  write_targets: []
  checkpoint_target: string | null
  event_root: string

concurrency:
  claim_id: string | null
  lease_or_expected_revision: string | null
  idempotency_key: string

acceptance:
  local_gate: object | null
  audit_required: bool
  acceptance_gate: object
  next_legal_transition: string | null

capabilities:
  required: []
  forbidden_or_unavailable: []

integrity:
  compiler_result: GREEN | AMBER | RED
  observed_condition_codes: []
  blockers: []
  warnings: []

provenance_trace:
  <field_path>: SourceRef
```

### Capsule invariants

- capsule generation requires `EffectiveState.health.authority_resolution == UNIQUE`;
- RED operation decision cannot produce an executable capsule;
- AMBER may produce an executable capsule only when the operation-specific permission matrix explicitly allows the observed conditions; otherwise a diagnostic/noncanonical capsule only;
- an executor must reject a capsule whose bound source revisions changed before claim/execution;
- capsule permissions are the intersection of all effective allowed scopes after prohibitions and stricter local restrictions, never their union;
- capsule does not contain active tokens/codes as conversational proof when existing policy requires independent external retrieval; it may contain the authoritative locator and verification requirement;
- capsule compilation never performs the target scientific/content work.

## G. Normalized lifecycle categories

Legacy raw statuses remain preserved. The kernel may additionally map them to a small normalized class for cross-project materialization:

```text
PLANNING
READY
CLAIMED
RUNNING
BLOCKED
WAITING_EXTERNAL
WAITING_USER
ARTIFACT_READY
AUDIT_PENDING
REVISION_REQUIRED
VERIFIED
ACCEPTED
COMPLETE
SUPERSEDED
REJECTED
QUARANTINED
CANCELLED
UNKNOWN
```

Mapping must be explicit and versioned. Unknown raw states map to `UNKNOWN`; the kernel must not infer the nearest state linguistically.

## H. Risk-mode rule

`GREEN`, `AMBER`, `RED` is an operational classification, not a replacement for detailed condition/blocker codes.

- `RED`: the requested operation is mechanically blocked by integrity/authority/concurrency/legal-transition conditions, or must remain blocked pending semantic review.
- `AMBER`: current authority remains uniquely resolvable and required integrity is not false, but a noncritical or operation-irrelevant degradation exists. Allowed actions are determined by the explicit operation permission matrix.
- `GREEN`: all required mechanical checks for the requested operation pass.

The same observed state can yield different operation risk decisions. The kernel must emit both condition codes and the operation class.

## I. Compiler explainability

Every kernel CLI/API decision must be able to emit a machine-readable explanation containing:
- source files/revisions read;
- authority precedence rules applied;
- field-level provenance;
- requested operation class;
- observed/blocking/nonblocking condition codes;
- every PASS/WARN/FAIL check;
- whether any semantic decision was intentionally deferred.

A bare boolean or bare color is not an acceptable control decision.
