from datetime import datetime, timezone


def _ctx() -> dict:
    return {
        "authority_resolution": "UNIQUE", "expected_revisions": {"task": "1"}, "observed_current_revisions": {"task": "1"},
        "operation_required_integrity_verdicts": [{"status": "VERIFIED"}], "required_gates": [], "available_evidence": {},
        "active_claims": [], "proposed_claim": {}, "actor_role": "PACKAGE_CONTROLLER", "target_state_class": "PACKAGE_CONTROLLER",
        "single_writer_map": {"PACKAGE_CONTROLLER": "PACKAGE_CONTROLLER"}, "proposed_permissions": [], "parent_permissions": [], "local_restrictions": [],
        "requested_mutations": {}, "requested_output_authority_class": "NONCANONICAL", "shadow_inputs": [], "predicate_evidence": [],
    }


def test_direct_and_predicate_policy(policy, predicate_registry) -> None:
    from ai_control_kernel.policy import PermissionEvaluator

    evaluator = PermissionEvaluator(policy, predicate_registry)
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert evaluator.evaluate("READ_DIAGNOSE", [], context=_ctx(), decided_at=at)["result"] == "ALLOW"
    assert evaluator.evaluate("EXECUTE_AND_CHECKPOINT", ["R_POLICY_FINGERPRINT_MISMATCH"], context=_ctx(), decided_at=at)["result"] == "DENY"
    assert evaluator.evaluate("EXECUTE_AND_CHECKPOINT", ["S_ACCEPTANCE_JUDGMENT_REQUIRED"], context=_ctx(), decided_at=at)["result"] == "SEMANTIC_REVIEW_REQUIRED"
    assert evaluator.evaluate("NO_SUCH_OPERATION", [], context=_ctx(), decided_at=at)["result"] == "SEMANTIC_REVIEW_REQUIRED"
    assert evaluator.evaluate("READ_DIAGNOSE", ["R_NOT_A_CODE"], context=_ctx(), decided_at=at)["result"] == "DENY"


def test_idempotent_policy_and_recovery(policy, predicate_registry) -> None:
    from ai_control_kernel.policy import PermissionEvaluator

    ctx = _ctx()
    ctx.update({"actor_role": "LIVENESS_OWNER", "recovery_owner_class": "LIVENESS_OWNER", "requested_repair_condition_code": "A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT", "observed_condition_codes": ["A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT"]})
    evaluator = PermissionEvaluator(policy, predicate_registry)
    assert evaluator.evaluate("LIVENESS_REPAIR", ["A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT"], context=ctx)["result"] == "ALLOW"

