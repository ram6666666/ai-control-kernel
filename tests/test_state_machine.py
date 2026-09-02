import pytest

from ai_control_kernel.state_machine import TransitionValidator


def _pass_context() -> dict:
    return {
        "authority_resolution": "UNIQUE", "expected_revisions": {"task": "1"}, "observed_current_revisions": {"task": "1"},
        "operation_required_integrity_verdicts": [{"status": "VERIFIED"}], "active_claims": [], "proposed_claim": {},
        "actor_role": "PACKAGE_CONTROLLER", "target_state_class": "PACKAGE_CONTROLLER", "single_writer_map": {"PACKAGE_CONTROLLER": "PACKAGE_CONTROLLER"},
        "operation_gate_spec": [], "available_evidence": {}, "predicate_evidence": [],
    }


def test_declared_edge_and_negative_cases(state_machine, predicate_registry) -> None:
    validator = TransitionValidator(state_machine, predicate_registry)
    assert validator.validate("PLANNING", "READY", operation_class="MUTATE_CONTROL_STATE", context=_pass_context()).allowed
    assert not validator.validate("PLANNING", "COMPLETE", operation_class="MUTATE_CONTROL_STATE", context=_pass_context()).allowed
    assert not validator.validate("UNKNOWN", "READY", operation_class="MUTATE_CONTROL_STATE", context=_pass_context()).allowed
    assert validator.validate("UNKNOWN", "UNKNOWN", operation_class="READ_DIAGNOSE", context=_pass_context()).allowed


@pytest.mark.parametrize("edge", [("READY", "CLAIMED", "CLAIM_EXECUTION_UNIT"), ("CLAIMED", "RUNNING", "MUTATE_CONTROL_STATE"), ("RUNNING", "ARTIFACT_READY", "MUTATE_CONTROL_STATE"), ("ARTIFACT_READY", "AUDIT_PENDING", "MUTATE_CONTROL_STATE"), ("AUDIT_PENDING", "VERIFIED", "MUTATE_CONTROL_STATE"), ("VERIFIED", "ACCEPTED", "PROMOTE_OR_ACCEPT_CANONICAL"), ("ACCEPTED", "COMPLETE", "MUTATE_CONTROL_STATE")])
def test_representative_edges(edge, state_machine, predicate_registry) -> None:
    validator = TransitionValidator(state_machine, predicate_registry)
    result = validator.validate(*edge[:2], operation_class=edge[2], context=_pass_context())
    assert result.rule_id is not None

