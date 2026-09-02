def test_predicates_pass_and_fail(predicate_registry) -> None:
    context = {
        "authority_resolution": "UNIQUE", "operation_required_integrity_verdicts": [{"status": "VERIFIED"}],
        "actor_role": "OWNER", "target_state_class": "TASK", "single_writer_map": {"TASK": "OWNER"},
        "expected_revisions": {"task": "1"}, "observed_current_revisions": {"task": "1"},
        "parent_permissions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE"], "local_restrictions": ["MUTATE_CONTROL_STATE"], "proposed_permissions": ["READ_DIAGNOSE"],
        "operation_gate_spec": ["gate"], "available_evidence": {"gate": True},
        "active_claims": [], "proposed_claim": {"execution_unit_id": "u", "claim_id": "c", "claimant": "x", "lease_revision": "1", "idempotency_key": "k"},
        "requested_mutations": {"worker_enabled": True}, "requested_repair_condition_code": "A", "observed_condition_codes": ["A"],
        "shadow_inputs": [{"authority_class": "CANONICAL", "treated_as_authoritative": True}], "requested_output_authority_class": "NONCANONICAL",
        "audit_gate": {"exact_artifact_required": True}, "audit_input_identity": {"status": "VERIFIED"}, "retrieval_observation": {"independent_retrieval_verified": True},
        "observed_amber_conditions": [], "promotion_gate_relevance_map": {}, "required_promotion_facets": [],
        "recovery_owner_class": "OWNER", "requested_policy_repair": {"mechanically_decidable": True}, "semantic_change_flags": [],
    }
    for predicate_id in predicate_registry.registry:
        result = predicate_registry.evaluate(predicate_id, context)
        assert result.predicate_id == predicate_id
        assert isinstance(result.passed, bool)
    assert predicate_registry.evaluate("P_SOURCE_REVISION_CURRENT", {**context, "observed_current_revisions": {"task": "2"}}).passed is False
    assert predicate_registry.evaluate("P_UNKNOWN", context).passed is False

