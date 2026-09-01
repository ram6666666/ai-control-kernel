# AI Control Kernel v0.1 — Control Surface Authority Map

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED

This map prevents the kernel from becoming another peer source of truth. Each existing surface is classified by what the v0.1 kernel may do with it.

## Treatment vocabulary

- `READ_AUTHORITY`: authoritative/current input for specified fields.
- `READ_EVIDENCE`: evidence only; cannot override authority.
- `VALIDATE`: mechanically validate structure/integrity/consistency.
- `DERIVE`: generate a read model from stronger sources.
- `COMPARE_SHADOW`: compare kernel output with current controller interpretation.
- `NEVER_MUTATE_V0_1`: kernel v0.1 cannot write this surface.
- `FUTURE_CUTOVER_CANDIDATE`: a later reviewed version may own this mechanical function.

## Global policy/control surfaces

| Surface | Current role | v0.1 treatment | Logical writer today | Kernel writer in v0.1 |
|---|---|---|---|---|
| `global/AI_GLOBAL_CONTEXT.md` and monitored global policy files | canonical durable global rules | READ_AUTHORITY, VALIDATE hash only | explicit policy-authoring/reconciliation process | NEVER_MUTATE_V0_1 |
| Drive `AI_GLOBAL_MEMORY_HANDSHAKE` | runtime liveness/global-memory token | READ_AUTHORITY through a supplied runtime observation adapter; validate agreement | authorized global migration/reconciliation | NEVER_MUTATE_V0_1 |
| Drive runtime global-memory mirror | runtime reinforcement and discoverability | READ_EVIDENCE + consistency validation; active metadata may support runtime agreement | authorized global migration/reconciliation | NEVER_MUTATE_V0_1 |
| `ai-control/GLOBAL_POLICY_VERSION.yaml` | current policy fingerprint/watchdog state | READ_AUTHORITY for fingerprint status and monitored SHAs; VALIDATE | policy reconciler/W5 | NEVER_MUTATE_V0_1 initially; FUTURE_CUTOVER_CANDIDATE for validator output only |
| `ai-control/POLICY_BINDINGS/<epoch>.yaml` | current global compatibility overlay | READ_AUTHORITY for global-control compatibility only | global policy reconciliation | NEVER_MUTATE_V0_1 |
| `ai-control/POLICIES/GLOBAL_POLICY_ENFORCEMENT.md` | runtime enforcement description | READ_EVIDENCE/VALIDATE consistency; not higher than canonical policy/fingerprint/registry | control maintenance/policy process | NEVER_MUTATE_V0_1 |

## Project/task authority surfaces

| Surface | Current role | v0.1 treatment | Writer | Kernel writer in v0.1 |
|---|---|---|---|---|
| `ai-control/ACTIVE_PROJECTS.yaml` | active/resumable project registry, pointers and effective global binding | READ_AUTHORITY for registration/pointers/global binding; VALIDATE | Global Control Center / reconciler according to policy | NEVER_MUTATE_V0_1 |
| project `PROJECT_STATE.*` | project-local current semantic/phase state | READ_AUTHORITY | PROJECT_HOME/TASK_CONTROL or authorized project transition role | NEVER_MUTATE_V0_1 |
| project `CURRENT_TASK.*` / task authority | current task semantics, scope, deliverables and gates | READ_AUTHORITY | TASK_CONTROL / authorized task controller | NEVER_MUTATE_V0_1 |
| project package queue / package authority | bounded package scope, dependencies, role and gates | READ_AUTHORITY; package may narrow but never broaden parent | task/package controller | NEVER_MUTATE_V0_1 |
| `ai-control/CONTROL_TASKS/*.yaml` | durable control-engineering task state | READ_AUTHORITY for that control task | control task controller | NEVER_MUTATE_V0_1 |
| immutable command records | user intent/provenance and requested operational change | READ_EVIDENCE for historical intent; current only after corresponding authority mutation | command intake surface | NEVER_MUTATE_V0_1 |

## Lifecycle/concurrency surfaces

| Surface | Current role | v0.1 treatment | Writer | Kernel writer in v0.1 |
|---|---|---|---|---|
| `ai-control/TASK_EVENTS/<task>/...` | immutable lifecycle evidence | READ_AUTHORITY for event history after schema/integrity validation; DERIVE read models | authorized actor per event type | v0.1 may create events only in isolated test/shadow namespace, never production lifecycle |
| claims/leases/slot session records | concurrency/executor ownership | READ_AUTHORITY for current claim/lease when current and verified | dispatcher / authorized slot controller | NEVER_MUTATE_V0_1 |
| START/terminal receipts | worker invocation evidence | READ_EVIDENCE / VALIDATE chronology and pairing | worker/watchdog runtime | NEVER_MUTATE_V0_1 |
| `WORKER_HEALTH.yaml` | current materialized worker-health snapshot | READ_EVIDENCE and COMPARE_SHADOW; health observations beneath it may be stronger | liveness reconciler/watchdog | DERIVE shadow only; FUTURE_CUTOVER_CANDIDATE for materialization |

## Artifact/audit surfaces

| Surface | Current role | v0.1 treatment | Writer | Kernel writer in v0.1 |
|---|---|---|---|---|
| Drive/GitHub artifact locator | actual artifact location | READ_AUTHORITY only when task/storage authority identifies it | producing executor / storage process | NEVER_MUTATE_V0_1 |
| artifact identity/manifest record | stable identity/integrity metadata | READ_AUTHORITY after validation | producer/publication process | kernel may generate isolated identity records when supplied actual bytes; no canonical promotion |
| audit input manifest | exact frozen reviewer input and integrity contract | READ_AUTHORITY for audit mechanics | producer publication/control intake, not auditor scientific verdict | VALIDATE only |
| independent audit verdict | review findings/acceptance evidence | READ_AUTHORITY for stated verdict after provenance validation | independent auditor | NEVER_MUTATE_V0_1 |

## Derived/global user-facing views

| Surface | Current role | v0.1 treatment | Writer | Kernel writer in v0.1 |
|---|---|---|---|---|
| `PROGRESS_SNAPSHOT.yaml` | current user-facing derived global rollup | READ_EVIDENCE, COMPARE_SHADOW; never override project/task/event authority | W5/GCC reconciler | DERIVE shadow; prime future materializer cutover candidate |
| `CONTROL_CENTER/CURRENT_HANDOFF.yaml` | mutable convenience pointer for fresh controller recovery | READ_EVIDENCE/pointers, not peer task truth | GCC/W5 | NEVER_MUTATE_V0_1 |
| `TASK_QUEUE.yaml` | current central dispatch/read model plus task registrations | READ_AUTHORITY for currently declared dispatch state, but reconcile against project/package authority/events | GCC/task controller/W5 per policy | NEVER_MUTATE_V0_1; future dispatcher cutover only after separate design |
| shared task/completion/transition Markdown logs | compatibility/index surfaces | READ_EVIDENCE only | W5/reconciler | DERIVE only if needed; never authority |

## Authority precedence by domain

The kernel must not use one universal scalar rank for all fields. Precedence is domain-specific.

### Global policy compatibility
1. canonical monitored policy content + current fingerprint state;
2. active project registry current binding pointer/overlay;
3. project-embedded copied global metadata;
4. runtime/derived snapshots.

A current global overlay can supersede stale copied global metadata but not project semantics.

### Project/task semantics
1. explicit current project-local task/package authority appropriate to the field;
2. current project state/bootstrap defaults;
3. active-project registry metadata/pointers;
4. command/event historical evidence;
5. derived snapshots/handoffs.

A package can narrow task scope; it cannot broaden parent prohibitions.

### Current lifecycle fact
1. validated immutable lifecycle events + current conflict-safe authoritative snapshot/claim where policy defines both;
2. artifact/checkpoint readback evidence;
3. worker receipts/runtime observations;
4. derived logs/progress snapshots;
5. conversation/self-report: never accepted as machine authority.

If event history and current snapshot disagree in a way not resolved by an explicit transition/materialization rule, result is conflict, not timestamp guessing.

### Artifact identity
1. actual bytes + deterministic hash/size when byte handle is available and matches the authoritative storage locator;
2. verified provider/Git revision identity where byte hash is unavailable by design;
3. manifest/sidecar evidence;
4. filenames, chat claims and reconstructed content: non-authoritative.

## v0.1 single-writer validation matrix

The kernel will validate that proposed writes target the correct logical owner class:

| State class | Logical owner class |
|---|---|
| user command provenance | COMMAND_INTAKE |
| project scientific/task semantics | PROJECT_TASK_CONTROL |
| package release/dependency authority | PACKAGE_CONTROLLER |
| claim/lease | DISPATCHER_CLAIM_MANAGER |
| artifact bytes | PRODUCER_EXECUTOR |
| audit verdict | INDEPENDENT_AUDITOR |
| policy fingerprint | POLICY_RECONCILER |
| worker enable/liveness state | LIVENESS_CONTROLLER |
| derived progress/materialized views | MATERIALIZER_RECONCILER |

A role mismatch yields `DENY` unless the current authoritative policy explicitly delegates that exact write.

## Initial shadow comparisons

The first kernel prototype should compare, without writing production state:
1. resolved active policy epoch/binding against current W5/GCC view;
2. normalized lifecycle state derived from immutable events against `TASK_QUEUE`/project package snapshots;
3. generated progress subset against `PROGRESS_SNAPSHOT`;
4. artifact identity calculation against existing sidecars/manifests where exact bytes are available;
5. generated `ExecutionCapsule` against the authority a real executor currently reconstructs manually.

Every discrepancy becomes a fixture and adjudication item. The kernel output is not presumed correct merely because it is deterministic.
