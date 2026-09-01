# AI Control Kernel v0.1 — Golden Fixture and Regression Plan

status: WORKING_DESIGN
implementation: NOT_AUTHORIZED

## 1. Test philosophy

The kernel must be validated against failure shapes observed in real control-plane operation, not only synthetic happy paths.

However, this repository is public. Real incidents are converted into **sanitized structural fixtures**. Fixtures preserve the authority graph, state transitions, revisions, hashes, event order and failure mechanism needed for deterministic testing, while removing private project content, personal information, secrets, provider tokens, private file identifiers, scientific manuscript text and unrelated operational metadata.

The test corpus therefore has two layers:

- **public golden fixtures** in this repository: sanitized, deterministic, safe to distribute;
- **private integration fixtures** in the user's operational control plane: real locators/revisions/artifacts used only for shadow E2E validation and never required for the public unit-test suite.

## 2. Golden-fixture contract

Each public fixture directory should eventually contain:

```text
tests/fixtures/<fixture_id>/
  README.md
  inputs/
    ... sanitized control objects ...
  expected/
    effective_state.yaml
    transition_decision.yaml
    execution_capsule.yaml       # only when compilation should succeed
    materialized_view.yaml       # when relevant
  fixture.yaml
```

`fixture.yaml` minimum fields:

```yaml
fixture_id:
incident_class:
sanitization: PUBLIC_SAFE_STRUCTURAL_REPRODUCTION
input_revisions: {}
requested_operation:
expected_result:
expected_risk_mode:
expected_condition_codes: []
expected_semantic_review: false
must_not: []
```

Fixtures must use fixed timestamps, stable IDs and deterministic serialization so outputs can be compared byte-for-byte where appropriate.

## 3. Initial fixture set

### F01 — Stale copied policy metadata, current overlay unambiguous

**Failure shape:** a secondary/runtime document still says policy epoch N-1 while current canonical fingerprint, registry and compatibility overlay establish epoch N.

Expected behavior:
- `EffectiveState` resolves current policy epoch uniquely from stronger authority;
- stale copied field produces `A_STALE_COPIED_METADATA`;
- read/shadow operations remain allowed;
- lower-level stale copy cannot overwrite active policy;
- stricter project-local non-global restrictions remain intact.

Must not:
- globally mark every operation RED merely because copied metadata is stale;
- mutate the stale document in shadow mode;
- treat newest timestamp as the authority rule.

### F02 — Canonical fingerprint mismatch

**Failure shape:** monitored canonical file revision differs from the expected fingerprint.

Expected behavior:
- condition `R_POLICY_FINGERPRINT_MISMATCH`;
- ordinary claim/execution/promotion denied;
- diagnosis and explicit policy reconciliation remain available to authorized roles;
- no capsule executable for ordinary production.

Must not:
- auto-adopt the unexpected canonical change solely because it is newer;
- silently rewrite the expected fingerprint.

### F03 — Duplicate claim: idempotent replay vs true conflict

Two variants:

**F03A exact replay**
- same package, same actor, same claim ID/idempotency key, same source revision;
- expected `NOOP_IDEMPOTENT`.

**F03B conflicting duplicate**
- same package, different active claimant or incompatible mutation under same key;
- expected `R_CLAIM_CONFLICT` and DENY.

Must not:
- create two active claims;
- classify all duplicates as harmless retries.

### F04 — Scheduler wake with no first durable receipt

**Failure shape:** scheduler metadata indicates a launch attempt, but no START receipt, claim, event, checkpoint or artifact exists.

Expected behavior:
- scheduler substrate condition `A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT`;
- task lifecycle must not advance to RUNNING/COMPLETE;
- liveness controller may retry/recover if role and idempotency checks pass;
- execution on a different healthy substrate is not globally forbidden if task authority and inputs are otherwise valid.

Must not:
- infer execution from scheduler launch metadata alone;
- duplicate a package if later evidence proves an earlier run did execute.

### F05 — Worker unexpectedly disabled, mechanically recoverable

**Failure shape:** desired worker state says enabled; runtime observation says disabled; no content-side effects or active claim exist.

Expected behavior:
- liveness-repair operation can be mechanically allowed to the liveness owner;
- content state remains unchanged;
- recovery event records before/after observation.

Must not:
- rerun scientific/content work as part of merely re-enabling a worker;
- let a generic executor mutate liveness state.

### F06 — Independent audit input unavailable

**Failure shape:** producer references an artifact, but reviewer cannot independently retrieve the exact frozen input.

Expected behavior:
- `R_REQUIRED_ARTIFACT_UNAVAILABLE` for `ISSUE_INDEPENDENT_AUDIT_VERDICT`;
- audit remains blocked;
- discussion/relay repair remains possible;
- no reconstructed substitute is promoted as exact input.

Must not:
- accept producer-local state as independent reviewer retrieval;
- downgrade exact-byte requirement because semantic content appears similar.

### F07 — Artifact identity mismatch / lossy text transport

**Failure shape:** expected size/hash describes artifact A; reconstructed bytes from a text/base64 transcription differ.

Expected behavior:
- `R_ARTIFACT_IDENTITY_MISMATCH`;
- publication/audit/promotion denied;
- artifact metadata records both expected and observed identity;
- remediation requests a byte-preserving file/stream transport.

Must not:
- ask an LLM to reproduce missing binary/base64 bytes;
- change expected hash to match reconstructed content.

### F08 — Noncanonical shadow artifact mistaken for authoritative baseline

**Failure shape:** a shadow/test artifact exists and may be useful for evaluation, but explicit authority states that it is not the exact baseline.

Expected behavior:
- artifact can be used only where noncanonical inputs are permitted;
- canonical edit/audit/promotion requiring the exact baseline is denied;
- provenance trace clearly labels shadow status.

Must not:
- use filename freshness, quality, or model judgment to promote it implicitly.

### F09 — Event replay and materialized snapshot divergence

**Failure shape:** immutable event stream proves state S2 while a derived snapshot remains at S1.

Expected behavior when event/snapshot relation is explicitly defined:
- `A_STALE_DERIVED_VIEW`;
- materializer derives S2;
- snapshot is evidence/cache, not peer authority.

Conflict variant:
- event stream and an independently authoritative current snapshot disagree with no declared reconciliation rule;
- expected `R_AUTHORITY_CONFLICT` or semantic review, not timestamp guessing.

### F10 — Stricter local restriction survives global overlay

**Failure shape:** global policy permits an operation generally, but current project/task/package authority explicitly forbids it.

Expected behavior:
- effective permissions use intersection/narrowing semantics;
- local prohibition survives;
- capsule lists the operation under `forbidden_actions`;
- attempted transition denied.

Must not:
- treat global overlay as a permission union;
- use global compatibility to rewrite local scientific/task semantics.

## 4. Additional architecture fixtures

After F01–F10, add integration-focused fixtures that prove replaceable adapters:

### F11 — Two workflow-runtime adapters, same core decision

Feed equivalent runtime observations through two adapter shapes. Core `EffectiveState` and `TransitionDecision` must be identical after normalization.

Purpose: prove the kernel is runtime-neutral rather than secretly coupled to one scheduler/workflow engine.

### F12 — Two model/provider executor capability records

Equivalent capability sets from different model/provider adapters must yield the same eligibility result for the same execution capsule.

Purpose: prove model-neutral routing contracts.

### F13 — Provider revision vs byte hash identity

One artifact source supplies actual bytes/SHA-256; another supplies a trusted immutable provider revision but no byte stream. The kernel must preserve different integrity semantics rather than pretending they are equivalent.

Purpose: keep storage adapters explicit and auditable.

## 5. Test layers

### Layer A — Pure unit tests

No network, no LLM, no GitHub/Drive/API calls.

Test:
- schema parsing;
- authority precedence;
- narrowing/intersection rules;
- status normalization;
- condition classification;
- transition legality;
- idempotency;
- capsule compilation;
- deterministic serialization;
- SHA-256 on local fixture bytes.

### Layer B — Golden regression tests

Run complete fixture directories and compare generated outputs with expected outputs.

Any changed golden output requires explicit review explaining whether:
- the kernel fixed a bug;
- the contract changed intentionally;
- the fixture expectation was wrong.

Never auto-refresh goldens in CI.

### Layer C — Adapter contract tests

Test Git/GitHub, filesystem/artifact and future workflow/model adapters against mocked or disposable environments. Core domain logic must not import provider SDKs directly.

### Layer D — Private shadow E2E

Run the public kernel against real operational control objects in read-only/shadow mode. Compare outputs with the existing controller/reconciler.

Every disagreement becomes:
1. an adjudicated discrepancy;
2. a sanitized public regression fixture when safe and structurally useful;
3. a contract/design change only if justified.

## 6. Property and invariant tests

In addition to golden examples, v0.1 should test invariants:

- adding a stricter prohibition cannot increase allowed actions;
- replacing a derived snapshot with a staler one cannot override stronger authority;
- conflicting same-rank authorities never resolve merely by timestamp;
- a changed bound source revision invalidates an execution capsule;
- identical idempotency replay cannot produce a second state advancement;
- a different request under the same idempotency key is rejected;
- RED required-input integrity cannot yield executable production capsule;
- semantic ambiguity cannot be converted into `ALLOW` without a new authoritative decision;
- provider adapter substitution with equivalent normalized evidence does not change core decisions;
- artifact hash is computed only from bytes actually supplied to the artifact interface.

Property-based testing may be added later if it materially improves state-machine/conflict coverage; v0.1 does not require a heavyweight framework merely for novelty.

## 7. Privacy and public-repository gate

Before committing a fixture to this public repository, verify it contains none of:

- personal names/contact information;
- private scientific manuscript content;
- private Drive/file IDs or signed URLs;
- secrets, auth tokens, execution codes or credentials;
- unpublished private project data;
- provider account identifiers;
- conversation transcripts beyond minimal syntheticized control statements.

Use generated identifiers such as `project-alpha`, `task-001`, `artifact-A` and fake deterministic hashes where real identities are unnecessary.

Real operational evidence remains referenced only from the private/global control plane and is not copied here.

## 8. Fixture acceptance gate

The fixture design is freeze-ready when:

- F01–F10 each have a precise expected kernel result;
- AMBER vs RED distinctions map to the operation permission matrix;
- public/private evidence boundary is explicit;
- at least one cross-runtime and one cross-model adapter-neutrality fixture is specified;
- negative assertions (`must_not`) exist for each safety-critical incident;
- fixture outputs can be produced without an LLM;
- future Codex implementation can turn the specification into tests without reinterpreting system policy.
