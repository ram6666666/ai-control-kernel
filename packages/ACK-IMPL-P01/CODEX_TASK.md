# ACK-IMPL-P01 — Codex Execution Contract

status: FROZEN_PACKAGE_INSTRUCTIONS
execution: NOT_AUTHORIZED_UNTIL_PACKAGE.yaml IS EXPLICITLY ENABLED

## Objective

Implement the pure deterministic AI Control Kernel v0.1 core against the frozen design baseline. The job is implementation and testing, not architecture redesign.

## Startup

Before changing code:

1. Read `packages/ACK-IMPL-P01/PACKAGE.yaml` completely.
2. Read `releases/design-v0.1/FREEZE_MANIFEST.yaml`.
3. Verify the repository base contains design-freeze merge commit `4eafb779256325471ae0461c17fec9a779eb188a` or a descendant with identical frozen normative blob SHAs.
4. Read the normative machine artifacts under `spec/v0.1/` and `schemas/v0.1/`.
5. Read `docs/design/v0.1/DESIGN_AUDIT_002.md` and `docs/architecture/INTEGRATION_FIRST.md`.
6. Confirm `PACKAGE.yaml: implementation_authorized == true` before making implementation changes. If false, stop without code changes.

## Non-negotiable boundaries

- Do not edit frozen control semantics to make implementation easier.
- Do not invent behavior for an underspecified case. Record it in `DEVIATION_REPORT.yaml` and block that unit.
- Do not implement GitHub/Drive/workflow/model production integrations.
- Do not acquire production claims or mutate production state.
- Do not add an agent framework to core.
- Do not build a scheduler, database or UI.
- Do not use fuzzy matching for states/statuses.
- Do not evaluate arbitrary policy expression strings.
- Do not compute artifact identity from reconstructed LLM text.

## Implementation order

Recommended dependency order:

1. project skeleton / dependency metadata;
2. canonical serialization and schema loading;
3. normalized contract types and ports;
4. status normalization;
5. predicate registry and evaluator dispatch;
6. condition detectors;
7. permission evaluator;
8. state-machine transition validator;
9. EffectiveState resolver primitives required by fixtures;
10. artifact byte identity;
11. CandidateCapsule compilation;
12. fixture claim verification and ExecutionCapsule compilation;
13. F01-F10 fixtures/goldens;
14. invariants and negative tests;
15. CI and documentation.

Implementation may reorganize modules if tests and boundaries remain clearer, but may not change frozen semantics without a deviation.

## Test requirements

At minimum test:

- all normative JSON schemas self-validate under Draft 2020-12;
- each registry validates against its schema where a schema is supplied;
- all P_* references resolve;
- all normalized state references are valid;
- unknown raw status -> UNKNOWN;
- F01-F10 expected decisions;
- restrictive permission intersection;
- idempotency replay/conflict;
- capsule invalidation on bound revision/claim changes;
- exact artifact SHA-256 from actual bytes;
- semantic conditions never produce an authority-effect ALLOW;
- equivalent normalized adapter evidence produces the same core decision.

## Completion

Do not call the work production-ready.

If all P01 gates pass, report only:

`IMPLEMENTED_P01_AWAITING_INDEPENDENT_REVIEW_AND_PRIVATE_SHADOW_E2E`

Commit `IMPLEMENTATION_REPORT.md` and `DEVIATION_REPORT.yaml` with the implementation.

A nonempty deviation report blocks package acceptance until the control/design authority adjudicates it.
