# AI Control Kernel v0.1 — Operation-Specific Risk and Permission Matrix

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED
normative_policy: `spec/v0.1/permission_policy.yaml`
condition_registry: `spec/v0.1/condition_detectors.yaml`
predicate_registry: `spec/v0.1/predicate_registry.yaml`

## 1. Rule

Risk is evaluated for one requested operation, not assigned as a single global permission color.

The kernel separates:
1. observed facts/conditions;
2. conservative mechanical state summary;
3. operation-scoped permission decision.

`TransitionDecision.risk_mode` is operation-scoped.

## 2. Condition classes

AMBER codes:
- `A_STALE_DERIVED_VIEW`;
- `A_STALE_COPIED_METADATA`;
- `A_OPTIONAL_TELEMETRY_MISSING`;
- `A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT`;
- `A_HISTORICAL_POLICY_TEXT_PRESENT`;
- `A_NONCRITICAL_REFERENCE_UNAVAILABLE`.

RED mechanical codes:
- `R_AUTHORITY_CONFLICT`;
- `R_POLICY_INCOMPATIBLE`;
- `R_POLICY_FINGERPRINT_MISMATCH`;
- `R_ARTIFACT_IDENTITY_MISMATCH`;
- `R_REQUIRED_ARTIFACT_UNAVAILABLE`;
- `R_CLAIM_CONFLICT`;
- `R_STALE_EXPECTED_REVISION`;
- `R_ILLEGAL_TRANSITION`;
- `R_MISSING_AUTHORIZATION`;
- `R_ROLE_WRITE_VIOLATION`;
- `R_REQUIRED_GATE_MISSING`.

Semantic-review codes:
- `S_AUTHORITY_MEANING_AMBIGUOUS`;
- `S_SCOPE_CHANGE_AMBIGUOUS`;
- `S_REQUIREMENT_CONFLICT`;
- `S_ACCEPTANCE_JUDGMENT_REQUIRED`.

Semantic codes return `SEMANTIC_REVIEW_REQUIRED` when the requested authority effect depends on the unresolved question. They are not “mechanical failures” and are not repaired automatically.

All A/R/S codes are emitted in `observed_condition_codes`; detailed unresolved semantic questions are emitted in `semantic_questions`.

## 3. Operation classes

The v0.1 operation registry is closed:
- `READ_DIAGNOSE`;
- `DISCUSS_PLAN`;
- `SHADOW_VALIDATE`;
- `WRITE_DIAGNOSTIC_EVIDENCE`;
- `PRODUCE_NONCANONICAL_WORKING_ARTIFACT`;
- `CLAIM_EXECUTION_UNIT`;
- `EXECUTE_AND_CHECKPOINT`;
- `PUBLISH_AUTHORITATIVE_ARTIFACT`;
- `ISSUE_INDEPENDENT_AUDIT_VERDICT`;
- `MUTATE_CONTROL_STATE`;
- `PROMOTE_OR_ACCEPT_CANONICAL`;
- `LIVENESS_REPAIR`;
- `POLICY_RECONCILIATION`.

Unknown operations require an explicit new mapping/spec revision; fuzzy mapping is forbidden.

## 4. Normative executable policy

The exact condition × operation behavior is defined in `spec/v0.1/permission_policy.yaml`.

The policy contains only:
- closed outcome tokens;
- closed `P_*` predicate IDs;
- condition-specific allow/recovery/conditional operation sets;
- fixed evaluation order.

`spec/v0.1/predicate_registry.yaml` maps each predicate ID to one deterministic evaluator contract. Arbitrary expression evaluation is forbidden.

`schemas/v0.1/permission-policy.schema.json` validates the policy shape.

Natural-language words such as “conditional”, “strict”, “relevant”, or “mechanically decidable” are explanatory only and cannot be implementation inputs unless reduced to a declared outcome token or `P_*` check.

## 5. Examples

### Stale copied policy metadata

If stronger current authority resolves uniquely, the stale copy is AMBER. Read/shadow work can continue. Execution or promotion proceeds only when the machine policy's declared predicates pass.

### Scheduler launch without first durable receipt

Launch metadata alone cannot advance lifecycle state. Diagnosis is allowed. Liveness repair requires its writer owner and cannot advance content. Execution on another healthy substrate still requires fresh task/package authority, claim and integrity checks.

### Exact audit artifact unavailable

`ISSUE_INDEPENDENT_AUDIT_VERDICT` is denied with `R_REQUIRED_ARTIFACT_UNAVAILABLE`. A reconstructed substitute does not become authoritative by semantic similarity.

### Lossy text/base64 transport

Byte identity/publication/audit/promotion are blocked on mismatch. Remediation requires a byte-preserving file/stream interface; an LLM is never a binary reconstruction transport.

## 6. Decision output

Every operation decision emits at minimum:

```yaml
operation_class:
result: ALLOW | DENY | SEMANTIC_REVIEW_REQUIRED | NOOP_IDEMPOTENT
risk_mode: GREEN | AMBER | RED
observed_condition_codes: []
blocking_condition_codes: []
nonblocking_warning_codes: []
checks: []
conflicts: []
missing_requirements: []
semantic_questions: []
write_plan: {}
```

A bare color is invalid.

## 7. Shadow-mode boundary

During v0.1 shadow validation the policy is evaluated without mutating production control state. Disagreements with the existing controller become adjudicated regression fixtures.
