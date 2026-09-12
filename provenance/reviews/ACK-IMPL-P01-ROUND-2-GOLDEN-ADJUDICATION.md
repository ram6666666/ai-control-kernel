# ACK-IMPL-P01 Round-2 golden adjudication

Status: EXPLICIT_IMPLEMENTATION_FIXTURE_ADJUDICATION

Scope: F01, F09, and F10 subsystem outputs required by PR #5 Round-2 review. This record does not change frozen design, spec, schema, or package semantics and does not accept or merge the implementation.

Method: candidate outputs were printed for inspection, checked against `docs/design/v0.1/GOLDEN_FIXTURE_PLAN.md`, and then the expected JSON files were written explicitly. No implementation or CI command generated, refreshed, or committed golden files.

- F01 `effective_state.json`: adjudicated because canonical `policy-v0.1` wins over copied `policy-v0.0`, `A_STALE_COPIED_METADATA` remains AMBER, and the project-local `MUTATE_CONTROL_STATE` prohibition survives in effective permissions.
- F09 `materialized_view.json`: adjudicated because ordered immutable events `event-1 -> event-2` deterministically materialize state `S2`; the starting `S1` snapshot remains derived evidence and does not override the event stream.
- F10 `effective_state.json`: adjudicated because global permission includes `MUTATE_CONTROL_STATE`, project authority forbids it, and the effective allowed set removes it while retaining the local prohibition.
- F10 `transition_decision.json`: adjudicated as `DENY` with `R_MISSING_AUTHORIZATION`, derived from the effective local prohibition rather than an unrelated writer-role mismatch.
- F10 `candidate_capsule.json`: adjudicated because a separately allowed execution candidate carries `MUTATE_CONTROL_STATE` only in `forbidden_actions`; the denied mutation decision cannot compile an execution-authorizing capsule.

Adjudicated canonical JSON SHA-256 values:

- F01 effective state: `41dca1eb10cbdb83b92534b6e27a84088e8d1299df95c9cd3b9783a46ff2b634`
- F09 materialized view: `51444afdf9de1e64fdf2a34c442ccb536e28f4f84dc845b58e30e77de75b244d`
- F10 candidate capsule: `4a6d30a8fc9d259322936d1afcd539577212f609451702e5a1a3cf3d852e913c`
- F10 effective state: `612613ec22578d01f3c3d8ca647a38a70d0f5e4b9a588e5421ff6495617a4846`
- F10 transition decision: `f340428e566d7276df1c1322823c4b2af25e4985aa788c200682b8e65c655110`

CI contract: compare these checked-in canonical JSON values byte-semantically; never create or refresh them.
