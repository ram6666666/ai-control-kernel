from ai_control_kernel.capsules import CandidateCapsuleCompiler, ExecutionCapsuleCompiler, is_capsule_invalidated


def _state() -> dict:
    source = {"source_type": "PROJECT_STATE", "locator": "state", "revision": "1", "content_hash": None, "observed_at": None, "authority_class": "AUTHORITATIVE_CURRENT"}
    pv = lambda value: {"value": value, "source": source, "resolution_rule": "test", "warnings": []}
    return {"identity": {"project_id": pv("p"), "task_id": pv("t"), "package_id": pv("pkg")}, "execution": {"phase": pv("RUN"), "role": pv("producer"), "objective": pv("objective")}, "constraints": {"allowed_actions": [pv("EXECUTE_AND_CHECKPOINT")], "forbidden_actions": [], "acceptance_gates": []}, "storage": {"authoritative_inputs": [], "write_targets": [], "checkpoint_targets": []}, "sources": {"policy_fingerprint": source, "permission_policy": source, "state_machine": source, "status_normalization": source, "project_registry": None, "project_state": source, "task_authority": source, "package_authority": source, "latest_checkpoint": None}, "provenance_trace": {"execution.normalized_status": source}}


def test_candidate_execution_binding_and_invalidation() -> None:
    state = _state()
    decision = {"operation_class": "EXECUTE_AND_CHECKPOINT", "result": "ALLOW", "risk_mode": "GREEN", "observed_condition_codes": [], "blocking_condition_codes": [], "nonblocking_warning_codes": []}
    candidate = CandidateCapsuleCompiler().compile(state, decision, capsule_id="c", compiled_at="2026-01-01T00:00:00Z", context={"source_revisions": state["sources"]})
    assert not CandidateCapsuleCompiler().validate(candidate)
    claim = {"claim_id": "claim", "claimant": "worker", "lease_revision": "1", "source_ref": {"source_type": "CLAIM", "locator": "claim", "authority_class": "AUTHORITATIVE_CURRENT"}}
    claim_decision = {"operation_class": "CLAIM_EXECUTION_UNIT", "result": "ALLOW"}
    execution = ExecutionCapsuleCompiler().compile(candidate, claim, claim_decision, capsule_id="e", compiled_at="2026-01-01T00:00:00Z")
    assert not ExecutionCapsuleCompiler().validate(execution)
    assert is_capsule_invalidated(execution, {**state["sources"], "task_authority": {"revision": "2"}})
    assert is_capsule_invalidated(execution, state["sources"], {"claim_id": "claim", "claimant": "worker", "lease_revision": "1", "status": "EXPIRED"})
    assert not is_capsule_invalidated(execution, state["sources"], {"claim_id": "claim", "claimant": "worker", "lease_revision": "1", "status": "ACTIVE"})
    assert is_capsule_invalidated(execution, state["sources"], {"claim_id": "claim", "claimant": "worker", "lease_revision": "2", "status": "ACTIVE"})
    assert is_capsule_invalidated(execution, state["sources"], None)

