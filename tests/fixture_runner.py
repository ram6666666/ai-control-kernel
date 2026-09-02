from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ai_control_kernel.canonical import canonical_json_bytes
from ai_control_kernel.conditions import ConditionDetector
from ai_control_kernel.policy import PermissionEvaluator
from ai_control_kernel.predicates import PredicateRegistry
from ai_control_kernel.schema import SchemaRegistry, load_json, load_yaml


def _base_context() -> dict[str, Any]:
    return {
        "authority_resolution": "UNIQUE",
        "expected_revisions": {"task": "task-rev-1"},
        "observed_current_revisions": {"task": "task-rev-1"},
        "operation_required_integrity_verdicts": [{"status": "VERIFIED"}],
        "required_gates": [],
        "available_evidence": {},
        "active_claims": [],
        "proposed_claim": {},
        "actor_role": "PACKAGE_CONTROLLER",
        "target_state_class": "PACKAGE_CONTROLLER",
        "single_writer_map": {"PACKAGE_CONTROLLER": "PACKAGE_CONTROLLER"},
        "parent_permissions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE"],
        "proposed_permissions": [],
        "local_restrictions": [],
        "requested_mutations": {},
        "requested_output_authority_class": "NONCANONICAL",
        "shadow_inputs": [],
        "audit_gate": {"exact_artifact_required": False},
        "audit_input_identity": {"status": "VERIFIED"},
        "retrieval_observation": {"independent_retrieval_verified": True},
        "observed_amber_conditions": [],
        "promotion_gate_relevance_map": {},
        "required_promotion_facets": [],
        "semantic_change_flags": [],
        "requested_policy_repair": {"mechanically_decidable": True},
    }


def run_fixture(fixture_dir: Path, registry: SchemaRegistry, predicates: PredicateRegistry) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixture = load_yaml(fixture_dir / "fixture.yaml")
    observations = load_json(fixture_dir / "inputs" / "observations.json")
    policy = registry.spec("permission_policy.yaml")
    context = _base_context()
    context.update(observations)
    expected_codes = [str(code) for code in fixture.get("expected_condition_codes", [])]
    detected = ConditionDetector().detect_many(observations)
    codes = [item["condition_code"] for item in detected if item["observed"]]
    assert codes == expected_codes
    decision = PermissionEvaluator(policy, predicates).evaluate(
        str(fixture["requested_operation"]),
        codes,
        context=context,
        request_id=str(fixture["fixture_id"]),
        decision_id=f"decision-{fixture['fixture_id']}",
        decided_at="2026-01-01T00:00:00Z",
    )
    generated = decision
    expected = load_json(fixture_dir / "expected" / "transition_decision.json")
    return fixture, generated, expected, decision


def assert_fixture_must_not(fixture: Mapping[str, Any], generated: Mapping[str, Any], decision: Mapping[str, Any]) -> None:
    expected_result = str(fixture["expected_result"])
    for directive in fixture.get("must_not", []):
        if directive in {"mutate_stale_document", "advance_content_state", "infer_running_from_launch", "create_second_active_claim", "classify_conflict_as_retry", "accept_reconstructed_substitute", "change_expected_hash", "promote_shadow_implicitly", "union_global_permissions", "auto_adopt_new_fingerprint", "treat_snapshot_as_peer_authority"}:
            assert generated["result"] == expected_result
        if directive == "mutate_stale_document":
            assert generated["result"] == "ALLOW" and decision["operation_class"] == "READ_DIAGNOSE"
        elif directive == "advance_content_state":
            assert decision["operation_class"] == "LIVENESS_REPAIR" and decision["write_plan"]["allowed"] and generated["result"] == "ALLOW"
        elif directive == "infer_running_from_launch":
            assert "RUNNING" not in json.dumps(generated, sort_keys=True)
        elif directive == "create_second_active_claim":
            assert generated["result"] == "NOOP_IDEMPOTENT"
        elif directive in {"classify_conflict_as_retry", "accept_reconstructed_substitute", "change_expected_hash", "promote_shadow_implicitly", "union_global_permissions"}:
            assert generated["result"] == "DENY"
        elif directive == "auto_adopt_new_fingerprint":
            assert generated["result"] == "DENY"
        elif directive == "treat_snapshot_as_peer_authority":
            assert decision["operation_class"] == "SHADOW_VALIDATE" and generated["result"] == "ALLOW"


def canonical_golden_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value)
