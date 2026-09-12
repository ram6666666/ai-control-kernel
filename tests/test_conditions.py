import pytest

from ai_control_kernel.conditions import AMBER_CODES, RED_CODES, SEMANTIC_CODES, ConditionDetector


@pytest.mark.parametrize("code", sorted(AMBER_CODES))
def test_amber_detectors(code: str) -> None:
    facts = {
        "authoritative_source_revisions": {"x": "2"},
        "derived_view_source_revisions": {"x": "1"},
        "active_authority_value": "2",
        "copied_metadata_value": "1",
        "declared_precedence_rule": "canonical",
        "telemetry_requirement_spec": {"optional_fields": ["latency"]},
        "runtime_observations": {},
        "scheduler_attempt_observed": True,
        "start_receipts": [],
        "claims": [],
        "task_events": [],
        "checkpoints": [],
        "artifacts": [],
        "active_rule_uniquely_resolved": True,
        "superseded_text_present": True,
        "reference_required_for_operation": False,
        "reference_unavailable": True,
    }
    assert ConditionDetector().detect(code, facts)["condition_class"] == "AMBER"


@pytest.mark.parametrize("code", sorted(RED_CODES))
def test_red_detectors(code: str) -> None:
    facts = {
        "top_rank_authorities_conflict": True,
        "declared_reconciliation_rule_absent": True,
        "compatibility_verdict": "INCOMPATIBLE",
        "any_required_revision_mismatch": True,
        "identity_comparison": "MISMATCH",
        "exact_artifact_required": True,
        "independent_retrieval_verified": False,
        "incompatible_active_claim_exists": True,
        "requested_expected_revision": "1",
        "observed_current_revision": "2",
        "declared_edge_exists": False,
        "required_flag_missing_or_false": True,
        "owner_or_delegation_match": False,
        "any_required_gate_unsatisfied": True,
    }
    assert ConditionDetector().detect(code, facts)["condition_class"] == "RED"


@pytest.mark.parametrize("code", sorted(SEMANTIC_CODES))
def test_semantic_detectors(code: str) -> None:
    facts = {
        "ranking_requires_interpretation_of_intended_meaning": True,
        "material_rescope_cannot_be_determined_from_machine_fields": True,
        "apparent_conflict_requires_semantic_interpretation": True,
        "adequacy_correctness_or_value_judgment_is_intentionally_nonmechanical": True,
    }
    result = ConditionDetector().detect(code, facts)
    assert result["semantic_review_required"] is True
