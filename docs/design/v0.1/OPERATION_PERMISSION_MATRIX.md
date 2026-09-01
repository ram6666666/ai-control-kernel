# AI Control Kernel v0.1 — Operation-Specific Risk and Permission Matrix

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED

## 1. Why risk must be operation-specific

A single global `GREEN / AMBER / RED` flag is too coarse for a real control plane.

The same observed defect can be harmless for one operation and blocking for another. A stale derived progress snapshot should not prevent read-only diagnosis. A missing exact artifact hash may not prevent discussion, but it must block an audit or canonical promotion whose gate requires byte identity.

Therefore v0.1 separates:

1. **observed conditions** — facts such as stale metadata, authority conflict, missing telemetry, or hash mismatch;
2. **state summary** — a conservative summary of known mechanical health;
3. **operation decision** — the risk classification and permission for one requested operation.

`TransitionDecision.risk_mode` is operation-scoped. It is not merely copied from a global health flag.

## 2. Condition classes

### GREEN conditions

All mechanical prerequisites relevant to the requested operation are satisfied:
- authority resolves uniquely;
- required policy compatibility passes;
- required source revisions are current;
- required artifact identity/integrity passes;
- required dependencies/gates are present;
- no conflicting claim/write exists;
- requested actor owns or is delegated the target write surface.

### AMBER conditions

AMBER means authority remains uniquely resolvable and no required integrity fact is known false, but a noncritical or operation-irrelevant degradation exists.

Initial AMBER condition codes:

| Code | Condition |
|---|---|
| `A_STALE_DERIVED_VIEW` | progress/handoff/materialized snapshot stale while stronger sources remain current |
| `A_STALE_COPIED_METADATA` | copied global metadata stale but current authoritative overlay resolves unambiguously |
| `A_OPTIONAL_TELEMETRY_MISSING` | optional worker/runtime telemetry missing |
| `A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT` | scheduler launch/receipt reliability degraded with no evidence of unauthorized execution |
| `A_HISTORICAL_POLICY_TEXT_PRESENT` | superseded historical policy text remains visible but active rule is explicitly resolvable |
| `A_NONCRITICAL_REFERENCE_UNAVAILABLE` | optional/non-authoritative reference unavailable, not required by the requested gate |

AMBER must carry the exact condition codes. It is never a generic "probably fine" state.

### RED conditions

RED is a hard mechanical blocker for ordinary execution/promotion when relevant to the requested operation.

Initial RED condition codes:

| Code | Condition |
|---|---|
| `R_AUTHORITY_CONFLICT` | same-domain authority cannot be uniquely resolved |
| `R_POLICY_INCOMPATIBLE` | required active policy binding incompatible |
| `R_POLICY_FINGERPRINT_MISMATCH` | required canonical fingerprint/integrity is dirty |
| `R_ARTIFACT_IDENTITY_MISMATCH` | required authoritative artifact bytes/hash/size do not match |
| `R_REQUIRED_ARTIFACT_UNAVAILABLE` | operation requires an exact artifact that cannot be retrieved independently |
| `R_CLAIM_CONFLICT` | concurrent claim/write ownership conflict unresolved |
| `R_STALE_EXPECTED_REVISION` | requested mutation was built against a state revision that is no longer current |
| `R_ILLEGAL_TRANSITION` | requested state-machine edge is not legal |
| `R_MISSING_AUTHORIZATION` | required production/implementation/promotion authorization absent |
| `R_ROLE_WRITE_VIOLATION` | actor does not own/delegated-write the target surface |
| `R_REQUIRED_GATE_MISSING` | required audit, dependency, acceptance, or publication gate missing |
| `R_SEMANTIC_AMBIGUITY` | a decision would require semantic interpretation outside deterministic authority |

`R_SEMANTIC_AMBIGUITY` normally yields `SEMANTIC_REVIEW_REQUIRED` rather than an automated repair.

## 3. Operation classes

The kernel v0.1 recognizes these coarse operation classes for permission decisions:

| Operation | Meaning |
|---|---|
| `READ_DIAGNOSE` | read authority/evidence, inspect inconsistency, compute explanations |
| `DISCUSS_PLAN` | human/AI semantic discussion or planning with no authoritative state mutation |
| `SHADOW_VALIDATE` | schema/resolver/materializer/capsule computation in isolated read-only/shadow mode |
| `WRITE_DIAGNOSTIC_EVIDENCE` | append isolated diagnostic/reconciliation evidence without advancing work state |
| `PRODUCE_NONCANONICAL_WORKING_ARTIFACT` | produce explicitly noncanonical draft/intermediate output |
| `CLAIM_EXECUTION_UNIT` | acquire task/package claim or lease |
| `EXECUTE_AND_CHECKPOINT` | perform authorized package work and write bounded checkpoint/output |
| `PUBLISH_AUTHORITATIVE_ARTIFACT` | publish artifact intended to become authoritative input/output |
| `ISSUE_INDEPENDENT_AUDIT_VERDICT` | auditor issues verdict on frozen authoritative inputs |
| `MUTATE_CONTROL_STATE` | mutate task/package/queue/current state under declared writer ownership |
| `PROMOTE_OR_ACCEPT_CANONICAL` | canonical promotion/final acceptance/high-impact irreversible state transition |
| `LIVENESS_REPAIR` | mechanically recover worker enable/receipt/stale-claim state |
| `POLICY_RECONCILIATION` | reconcile policy fingerprint/binding/runtime metadata under explicit authority |

## 4. Base permission matrix

`CONDITIONAL` means the kernel must evaluate the condition's relevance to the exact operation and required gate. It does not mean automatic allow.

| Operation | GREEN | AMBER | RED |
|---|---|---|---|
| `READ_DIAGNOSE` | ALLOW | ALLOW | ALLOW_RECOVERY_SCOPE_ONLY |
| `DISCUSS_PLAN` | ALLOW | ALLOW | ALLOW_NO_AUTHORITY_EFFECT |
| `SHADOW_VALIDATE` | ALLOW | ALLOW_WITH_WARNINGS | ALLOW_DIAGNOSTIC_ONLY_IF_NO_UNTRUSTED_INPUT_IS_TREATED_AS_VALID |
| `WRITE_DIAGNOSTIC_EVIDENCE` | ALLOW | ALLOW | CONDITIONAL_RECOVERY_ROLE_ONLY |
| `PRODUCE_NONCANONICAL_WORKING_ARTIFACT` | ALLOW | CONDITIONAL | DENY_BY_DEFAULT |
| `CLAIM_EXECUTION_UNIT` | ALLOW | CONDITIONAL | DENY |
| `EXECUTE_AND_CHECKPOINT` | ALLOW | CONDITIONAL | DENY |
| `PUBLISH_AUTHORITATIVE_ARTIFACT` | ALLOW | CONDITIONAL_STRICT | DENY |
| `ISSUE_INDEPENDENT_AUDIT_VERDICT` | ALLOW | CONDITIONAL_STRICT | DENY |
| `MUTATE_CONTROL_STATE` | ALLOW | CONDITIONAL_STRICT | DENY_EXCEPT_AUTHORIZED_RECOVERY_TRANSITION |
| `PROMOTE_OR_ACCEPT_CANONICAL` | ALLOW | DENY_UNLESS_AMBER_CONDITION_EXPLICITLY_DECLARED_IRRELEVANT_BY_MACHINE_RULE | DENY |
| `LIVENESS_REPAIR` | ALLOW_IF_ROLE_AUTHORIZED | ALLOW_IF_MECHANICALLY_DECIDABLE | ALLOW_ONLY_WHEN_RED_CONDITION_IS_THE_LIVENESS_DEFECT_BEING_REPAIRED_AND_REPAIR_CANNOT_ADVANCE_CONTENT |
| `POLICY_RECONCILIATION` | NOOP_OR_VALIDATE | ALLOW_IF_MECHANICALLY_DECIDABLE | ALLOW_ONLY_FOR_EXPLICIT_RECONCILIATION_ROLE; SEMANTIC_POLICY_CHANGE_ESCALATES |

## 5. AMBER relevance rules

An AMBER operation may proceed only if all of the following are true:

1. authority for the requested operation is still `UNIQUE`;
2. no required integrity fact is false or missing;
3. the AMBER condition is explicitly classified as nonblocking for that operation;
4. proceeding cannot silently widen permissions or skip a gate;
5. the decision records the warning code and evidence;
6. canonical promotion uses stricter rules than draft/diagnostic operations.

If relevance cannot be determined mechanically, return `SEMANTIC_REVIEW_REQUIRED` rather than treating AMBER as permission.

## 6. Examples from current incidents

### Stale GP05 metadata while GP06 authority is uniquely resolved

- `READ_DIAGNOSE`: ALLOW / AMBER.
- `SHADOW_VALIDATE`: ALLOW_WITH_WARNINGS.
- `EXECUTE_AND_CHECKPOINT`: may be ALLOW if active GP06 fingerprint/binding and task/package authority are independently verified and the stale field is copied metadata only.
- `PROMOTE_OR_ACCEPT_CANONICAL`: only if the operation-specific gate explicitly does not rely on the stale field; otherwise DENY/REVIEW.

### Scheduler launch with no first durable receipt and no side effects

- discussion and diagnosis: ALLOW;
- direct execution in another independently healthy executor substrate: may be allowed if all package/state gates are green;
- treating the failed scheduler launch as RUNNING or COMPLETE: DENY;
- re-enabling/retrying the scheduler: allowed only through liveness/recovery ownership and idempotency checks.

### Exact audit artifact inaccessible to reviewer

- planning and relay diagnosis: ALLOW;
- independent audit verdict: DENY with `R_REQUIRED_ARTIFACT_UNAVAILABLE`;
- reconstructed substitute cannot be promoted to authoritative input merely because it is semantically similar.

### Lossy base64 transcription path

- discussion of artifact contents: may proceed only as non-authoritative analysis if provenance makes the limitation explicit;
- byte identity verification: DENY;
- canonical publication/audit: DENY until a byte-preserving transport path supplies the actual artifact.

## 7. Semantic-review rule

`SEMANTIC_REVIEW_REQUIRED` is a first-class successful outcome of deterministic control evaluation. It means the kernel correctly found the boundary of what software can decide.

Examples:
- whether an apparently stale requirement is actually superseded;
- whether an audit criticism materially changes scientific scope;
- whether two textual requirements conflict in meaning;
- whether a noncanonical working artifact is adequate for a human decision.

The kernel must output the exact unresolved question and relevant sources. It must not convert semantic uncertainty into AMBER permission.

## 8. Decision output requirements

For every operation decision, emit:

```yaml
operation:
result: ALLOW | DENY | SEMANTIC_REVIEW_REQUIRED | NOOP_IDEMPOTENT
risk_mode: GREEN | AMBER | RED
observed_conditions: []
blocking_conditions: []
nonblocking_warnings: []
required_sources: []
checks: []
writer_owner_check:
source_revision_check:
reason:
```

A decision is invalid if it only emits a color without the condition codes and operation.

## 9. v0.1 enforcement boundary

During shadow mode, this matrix is evaluated but does not itself mutate production state. The kernel compares its decision against the current control-plane decision and records discrepancies as test fixtures.

The first cutover must not begin with canonical promotion or scheduler ownership. Prefer read-only validation, effective-state resolution, or artifact hashing first.
