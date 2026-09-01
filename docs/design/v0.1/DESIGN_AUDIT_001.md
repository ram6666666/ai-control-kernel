# AI Control Kernel v0.1 — Design Audit 001

status: INTERNAL_DESIGN_AUDIT
verdict: REVISION_REQUIRED_BEFORE_DESIGN_FREEZE
implementation_authorized: false
production_cutover_authorized: false

## 1. Audit scope

Reviewed together:
- `DESIGN_BRIEF.md`;
- `MACHINE_CONTRACTS.md` as revised on this branch;
- `CONTROL_SURFACE_MAP.md`;
- `OPERATION_PERMISSION_MATRIX.md`;
- `GOLDEN_FIXTURE_PLAN.md`;
- `docs/architecture/INTEGRATION_FIRST.md`;
- repository migration/authority split.

This is an internal architecture audit, not an independent external acceptance review.

## 2. What is already strong enough

### A. Kernel boundary — PASS

v0.1 is bounded to deterministic mechanics and does not attempt to become a general autonomous agent, scheduler, scientific judge, or storage engine.

### B. Authority model — PASS WITH IMPLEMENTATION DETAIL PENDING

The design correctly distinguishes authoritative sources, evidence, derived views and narrowing authority. It rejects timestamp/filename guessing and preserves stricter local restrictions.

### C. Execution capsule concept — PASS

The capsule is explicitly derived, revision-bound, short-lived and non-authoritative. It has sufficient provenance intent to reduce executor startup interpretation burden.

### D. Semantic boundary — PASS

`SEMANTIC_REVIEW_REQUIRED` is first-class and semantic uncertainty is no longer conflated with ordinary AMBER degradation.

### E. Risk model — PASS AT CONCEPT LEVEL

Operation-scoped decisions solve the major flaw in a single global fail-closed flag. Read/diagnostic/recovery operations can continue under defects that must still block execution or canonical promotion.

### F. Regression strategy — PASS AT PLAN LEVEL

The fixture plan captures real failure shapes, includes negative assertions, property/invariant testing and cross-adapter neutrality tests. Public/private fixture separation is appropriate for a public repository.

### G. Integration-first architecture — PASS

The kernel owns the missing control semantics and treats workflow engines, schedulers, SDKs, storage and observability as replaceable infrastructure behind adapters.

### H. Repository migration — PASS

Exact source blob identities were preserved, global control authority remains in the parent control repository, and no second global policy truth was created.

## 3. Freeze blockers

The design is **not yet `DESIGN_V0_1_FREEZE_READY`**. The remaining blockers are concrete and mechanical enough to finish without Work.

### B1 — Permission matrix is still prose, not an executable contract

The current matrix contains values such as `CONDITIONAL`, `CONDITIONAL_STRICT`, and long natural-language exceptions. A deterministic kernel cannot implement these without reinterpreting prose.

Required revision:
- define a machine-readable permission-policy schema;
- enumerate condition code × operation class outcomes;
- represent required predicates explicitly;
- eliminate implementation-time interpretation of words like "relevant", "strict", or "if mechanically decidable" unless those terms map to declared predicates.

Acceptance evidence:
- one YAML/JSON policy object can produce expected decisions for F01–F10 without LLM reasoning.

### B2 — Transition state machine/edge registry is not defined

`TransitionValidator` requires that an edge "exists in the declared state machine", but no machine contract currently defines the transition registry.

Required revision:
- define `StateMachineSpec` / `TransitionRule` schema;
- distinguish normalized lifecycle categories from domain-specific raw states;
- support task/package-specific extensions without linguistic inference;
- bind every rule to version/revision and owner class.

Acceptance evidence:
- F03/F09 and at least one audit/remediation chain can be evaluated from explicit transition rules.

### B3 — Raw-status normalization registry is unspecified

The design says raw statuses map explicitly to normalized lifecycle categories but does not define where mappings live, their precedence, or behavior when project-specific statuses overlap.

Required revision:
- define normalization registry schema;
- unknown raw status -> `UNKNOWN`;
- project/task-specific mapping may narrow/extend only under declared namespace/version;
- no fuzzy/language-based mapping.

### B4 — Adapter port contracts are not concrete

Integration-first is a design principle, but Codex still lacks exact ports/interfaces.

Required revision:
Define provider-neutral interfaces for at least:
- control-source/revision reader;
- immutable-event reader;
- artifact byte/identity reader;
- runtime observation source;
- executor capability source;
- optional workflow-runtime dispatch adapter boundary;
- serialization/output sink for shadow results.

Core modules must depend on these ports, not on GitHub/Drive/Temporal/LangGraph/provider SDK object models.

### B5 — Dependency choice is unresolved

The design intentionally postponed JSON Schema/Pydantic/dataclass selection. Before implementation freeze, choose a minimal dependency posture and state why.

Decision criteria:
- schema versioning;
- deterministic serialization;
- validation error explainability;
- easy JSON/YAML interchange;
- low dependency weight;
- no runtime-framework lock-in.

This does not require choosing a workflow engine.

### B6 — Capsule compilation versus claim acquisition boundary needs one sharper rule

The capsule includes claim/lease metadata but the kernel is not the dispatcher in v0.1. The exact ordering must be explicit.

Required revision:
- decide whether a capsule is compiled pre-claim, post-claim, or in two forms;
- define invalidation on claim/revision change;
- prevent a reusable pre-claim capsule from being mistaken for active execution authority.

Preferred direction for review: `CandidateCapsule` before claim, `ExecutionCapsule` only after externally verified claim/lease binding.

### B7 — Condition detection contracts need ownership

Condition codes are defined, but the design has not yet said which deterministic detector/source is responsible for asserting each code.

Required revision:
- map every A/R condition code to required inputs and detector function;
- condition detectors return evidence/provenance;
- adapters supply observations; core detector logic classifies them.

Without this, adapters could smuggle policy decisions into provider-specific code.

## 4. Non-blocking future items

These should not delay v0.1 design freeze:

- choosing Temporal, LangGraph, Restate, Dapr or another durable runtime for a future production adapter;
- capability-based scheduler implementation;
- full event-sourced migration of existing projects;
- database backend;
- UI/control dashboard;
- broad multi-user permissions system;
- automatic cross-provider cost optimization.

They belong after the deterministic core proves itself in shadow mode.

## 5. Dependency recommendation direction

Preliminary recommendation for the next decision unit:

- use **JSON Schema as the serialized contract boundary** because contracts must remain language/runtime neutral and inspectable;
- use a small Python typed-model layer internally, potentially Pydantic, if it materially reduces validation/serialization boilerplate;
- do not make Pydantic objects the canonical external format;
- use standard `hashlib` for SHA-256;
- keep provider/workflow integrations behind explicit Python protocols/adapters;
- avoid adopting an agent framework inside the core.

This remains a recommendation until the dependency/adapter decision is written and audited.

## 6. Recommended next design units

Proceed in this order:

1. `EXECUTABLE_PERMISSION_POLICY_SPEC` — remove prose ambiguity from GREEN/AMBER/RED decisions.
2. `STATE_MACHINE_AND_NORMALIZATION_SPEC` — define transition edges and raw-status mapping.
3. `ADAPTER_PORTS_AND_DEPENDENCY_DECISION` — freeze replaceable integration boundaries and minimal Python dependency strategy.
4. `CAPSULE_CLAIM_LIFECYCLE_SPEC` — separate candidate capsule from claim-bound execution capsule.
5. Re-run design audit against the freeze gate.

## 7. Work / Codex assessment

### Work
Not needed for the remaining design blockers. They are tightly coupled architecture decisions best resolved in the current design thread and repository branch.

### Codex
Do not invoke yet. Codex becomes useful after the blockers above are closed and the design can be converted into bounded implementation tasks without asking the coding model to invent policy.

## 8. Audit verdict

`REVISION_REQUIRED_BEFORE_DESIGN_FREEZE`

This is a productive failure: the architecture direction is coherent, but several places still contain human-readable words where the eventual kernel requires executable policy objects. The next revision should specifically compile those remaining prose rules into machine contracts rather than add more conceptual layers.
