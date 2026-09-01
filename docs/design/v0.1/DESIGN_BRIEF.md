# AI Control Kernel v0.1 — Minimal Design Brief

status: WORKING_DESIGN
project: progress-scheduling
task: AI-CONTROL-KERNEL-V0-1
policy_epoch_at_design_start: GP-20260901-06
working_branch: ai-control-kernel-v0.1-design
production_authorized: false

## 1. Purpose

The current AI work system has already validated several important control ideas: durable external state, discussion/execution separation, immutable lifecycle evidence, bounded execution packages, external checkpoints, artifact readback, independent audit, policy compatibility checks, and centralized progress reconciliation.

The next problem is not lack of control rules. It is that too much mechanically decidable control logic is still interpreted and executed by LLMs reading many Markdown/YAML surfaces. AI Control Kernel v0.1 moves a deliberately small subset of those mechanics into deterministic, testable software while leaving semantic/scientific judgment with humans and AI roles.

The kernel is not a new autonomous agent and is not a replacement for the existing control plane. v0.1 is initially a shadow validator/compiler beside the current system.

## 2. Core design rule

**Software decides what can be decided mechanically. AI decides what requires meaning. Humans retain authority over goals, material scope, irreversible/high-impact acceptance and ambiguous semantic conflict.**

The kernel must never infer new project intent from convenience, chat momentum, filenames, timestamps or model memory.

## 3. v0.1 module boundary

The first implementation contains six deterministic modules only.

### K1 — Schema Validator
Validates machine-readable control objects against versioned schemas.

Initial object classes:
- global policy fingerprint metadata;
- project registry entry;
- task state;
- package state;
- immutable task event;
- artifact identity record;
- execution capsule.

It reports structural errors but does not repair semantic content.

### K2 — Effective-State Resolver
Computes one explicit effective control view from declared authority sources and precedence rules.

Initial resolution targets:
- active policy epoch/fingerprint state;
- project compatibility binding;
- current task/package authority;
- stricter project-local restrictions;
- current role/scope/write-target/acceptance boundary.

Resolution must preserve the existing principle that a global overlay may supersede stale copied global metadata but may not silently change project scientific/task semantics.

Output is an `EffectiveState` object plus a provenance trace showing exactly which source supplied each resolved field.

### K3 — Transition Validator
Given `EffectiveState + proposed transition`, determines whether the transition is mechanically legal.

Examples of deterministic checks:
- dependency satisfied or not;
- required predecessor status present;
- claim already active;
- exact expected status matches;
- implementation/promotion authorization flag present;
- audit-required gate not bypassed;
- forbidden transition from blocked/quarantined state;
- idempotent replay vs conflicting second transition.

It must return `ALLOW`, `DENY`, or `SEMANTIC_REVIEW_REQUIRED`; it must not invent a transition.

### K4 — Event Materializer
Validates immutable lifecycle events and derives machine-generated views from them.

v0.1 targets only bounded derived views used for shadow comparison, not wholesale replacement of all current YAML state.

Candidate derived outputs:
- latest task lifecycle state;
- latest package lifecycle state;
- claim ownership summary;
- artifact-verification summary;
- completion-evidence summary.

Historical events remain immutable.

### K5 — Artifact Identity
Creates/verifies metadata for artifacts when the kernel has actual byte access.

Fields:
- artifact_id;
- source locator;
- storage class;
- MIME/type when known;
- byte size;
- SHA-256;
- producer/run identity;
- publication/readback evidence;
- authoritative/noncanonical classification.

Hard rule: the kernel may hash bytes it actually receives through a file/path/stream interface; it must never ask an LLM to transcribe base64 or binary content in order to recreate bytes.

Actual cross-system byte transport is not implemented in v0.1; only the transport interface and identity contract are defined.

### K6 — Execution Capsule Compiler
Compiles the resolved authority required by one bounded executor unit into one machine-readable `ExecutionCapsule`.

The capsule is a derived authorization view, not a new source of project truth.

Minimum fields:
```yaml
schema_version:
capsule_id:
compiled_at:
source_revisions:
  policy_fingerprint_sha:
  project_state_sha:
  task_state_sha:
  package_state_sha:
project_id:
task_id:
package_id:
phase:
role:
objective:
authoritative_inputs:
allowed_actions:
forbidden_actions:
write_targets:
reference_packet:
required_capabilities:
claim_or_lease:
idempotency_key:
acceptance_gate:
next_legal_transition:
integrity_requirements:
```

Every important field must retain provenance back to the authority from which it was compiled.

## 4. Explicit non-responsibilities

v0.1 does **not**:
- decide scientific correctness;
- decide writing quality;
- rewrite project goals or reader models;
- choose a materially new research direction;
- promote canonical scientific artifacts;
- replace independent audit;
- replace the current scheduler;
- autonomously launch Work/Claude/Codex/ChatGPT;
- migrate every legacy project into a new database;
- become a second parallel task truth;
- treat a newer filename or `FINAL` label as authority;
- repair ambiguous semantic conflicts.

## 5. Deterministic vs semantic boundary

Examples that the kernel SHOULD decide:
- YAML/schema validity;
- SHA mismatch;
- missing required pointer;
- dependency status;
- duplicate claim;
- stale expected blob SHA;
- illegal state-machine edge;
- artifact byte size/hash when bytes are available;
- whether all explicitly enumerated mechanical prerequisites of a gate are present;
- generation of a derived progress/state view from accepted immutable events.

Examples that MUST remain AI/human review:
- whether a writing requirement is scientifically sufficient;
- whether two project requirements conflict semantically;
- whether an audit criticism warrants changing scientific scope;
- whether an approximation is acceptable for a given pedagogical goal;
- whether a user instruction materially rescopes a project;
- whether an ambiguous legacy record should be interpreted as authoritative.

Unclear cases return `SEMANTIC_REVIEW_REQUIRED`, never an invented deterministic answer.

## 6. Failure classes

v0.1 must distinguish at least:

### RED / hard block
- authoritative SHA/integrity mismatch;
- conflicting task authority;
- illegal transition;
- incompatible policy binding;
- unresolved concurrent claim/write conflict;
- missing required artifact when exact identity is a gate;
- invalid authorization/provenance chain.

Only diagnosis/recovery/migration actions are allowed where current policy requires fail-closed behavior.

### AMBER / degraded
- stale non-authoritative copied metadata when effective authority is unambiguous;
- stale derived snapshot;
- missing optional telemetry;
- known scheduler liveness degradation with no evidence of unauthorized side effects;
- historical superseded policy text that does not alter resolved active authority.

AMBER must never silently permit canonical promotion or irreversible/high-impact transitions if the missing data is relevant to that action.

### GREEN
- schemas valid;
- effective authority resolves uniquely;
- required integrity checks pass;
- proposed mechanical transition is legal.

The exact degraded-mode permission matrix is a design-review item before implementation.

## 7. Single-writer direction

The kernel should make ownership explicit rather than allowing multiple controllers to mutate the same state opportunistically.

Target logical ownership:
- user/command provenance -> command intake surface;
- desired task state -> task controller;
- package claim/lease -> dispatcher/claim manager;
- artifact bytes -> producing executor;
- audit verdict -> independent auditor;
- policy fingerprint -> policy reconciler;
- worker enable/liveness control -> liveness controller;
- derived progress/materialized views -> deterministic materializer.

In v0.1 this is first represented as a validation/ownership map. Enforcement cutover is later.

## 8. Shadow-mode migration

No active system component is replaced initially.

Sequence:
1. read existing real control objects;
2. kernel validates/resolves/compiles in read-only or isolated output mode;
3. compare kernel result with current W5/GCC interpretation;
4. investigate every discrepancy;
5. build golden fixtures from resolved incidents;
6. only after sustained agreement propose one narrowly scoped mechanical cutover;
7. preserve rollback to the existing external-state workflow.

The first production cutover should be a low-semantic-risk function such as schema validation, effective-policy resolution, or deterministic artifact hashing—not scheduler ownership or scientific acceptance.

## 9. Initial real-world regression fixtures

The test corpus should reuse actual control failures rather than synthetic happy paths only.

Minimum fixtures:
1. active GP06 authority with stale GP05 metadata embedded in a secondary runtime/control document;
2. canonical fingerprint mismatch / `POLICY_DIRTY` case;
3. duplicate or stale package claim;
4. worker scheduler launch with no first durable receipt and no observed side effect;
5. unexpected worker disable mechanically recoverable without content rerun;
6. external audit input inaccessible to reviewer;
7. artifact identity mismatch or lossy base64-transcription path;
8. shadow/noncanonical artifact explicitly forbidden from being treated as exact authoritative baseline;
9. immutable event replay showing idempotent duplicate vs true conflict;
10. project-local stricter restriction that must survive a global overlay.

## 10. Proposed repository layout

Working proposal only:
```text
ai-control/kernel/
  README.md
  schemas/
  src/
    resolver.py
    transitions.py
    events.py
    artifacts.py
    capsule.py
    models.py
    cli.py
  tests/
    fixtures/
    golden/
```

Do not create implementation files until the design gate is accepted.

## 11. Dependency posture

Prefer a small, inspectable dependency surface. The implementation gate will choose between:
- standard-library dataclasses + a schema library;
- Pydantic-based typed models;
- JSON Schema validation with explicit Python domain objects.

The choice should be driven by deterministic validation, stable serialization, migration/versioning and testability—not framework fashion.

No agent framework is required for the kernel itself.

## 12. Work / Codex boundary

### Work
Not needed for design. It may become useful later for a large migration/deployment validation that spans many control objects or for orchestrating multiple bounded implementation/test packages after the package graph is frozen.

### Codex
Likely useful after `DESIGN_V0_1_FREEZE_READY` for the first implementation package: repository-aware Python scaffolding, schemas, CLI and a comprehensive test suite. Codex should receive a frozen implementation package rather than being asked to redesign the control plane while coding.

No Work or Codex handoff is currently authorized or necessary.

## 13. Design-freeze acceptance questions

Before implementation, we must be able to answer yes to all of the following:
1. Can every v0.1 module be tested without an LLM?
2. Is there exactly one declared authority-precedence algorithm?
3. Can the kernel explain where every compiled capsule field came from?
4. Can a semantic ambiguity be represented without the kernel guessing?
5. Can the kernel run in shadow mode without changing current project/task state?
6. Are state transitions idempotent/conflict-safe by construction?
7. Does artifact hashing operate only on real byte handles/streams?
8. Can current control operation continue unchanged if the kernel fails?
9. Is the first cutover reversible and mechanically verifiable?
10. Is the kernel materially reducing LLM control burden rather than adding another protocol layer?

## 14. Next design step

Define three machine contracts before any implementation:
1. `EffectiveState` schema;
2. `ProposedTransition / TransitionDecision` schema;
3. `ExecutionCapsule` schema.

Then build a decision table mapping existing control surfaces to authoritative inputs, derived views, single-writer owner, and kernel treatment (`READ`, `VALIDATE`, `DERIVE`, `NEVER_MUTATE_IN_V0_1`).
