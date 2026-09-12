from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ai_control_kernel.canonical import canonical_json_bytes
from ai_control_kernel.capsules import CandidateCapsuleCompiler
from ai_control_kernel.conditions import ConditionDetector
from ai_control_kernel.effective_state import EffectiveStateResolver
from ai_control_kernel.events import materialize_events
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


def _values(records: object) -> list[str]:
    if not isinstance(records, list):
        return []
    return [str(record.get("value")) for record in records if isinstance(record, Mapping)]


def _capsule_source_revisions(state: Mapping[str, Any]) -> dict[str, Any]:
    sources = state["sources"]
    registry_source = {
        "source_type": "REGISTRY",
        "locator": "spec/v0.1/permission_policy.yaml",
        "revision": "policy-v0.1",
        "content_hash": None,
        "observed_at": None,
        "authority_class": "CANONICAL",
    }
    state_machine_source = {**registry_source, "locator": "spec/v0.1/state_machine.yaml", "revision": "state-machine-v0.1"}
    status_source = {**registry_source, "locator": "spec/v0.1/status_normalization.yaml", "revision": "status-normalization-v0.1"}
    return {
        "policy_fingerprint": sources["global_policy_fingerprint"],
        "permission_policy": registry_source,
        "state_machine": state_machine_source,
        "status_normalization": status_source,
        "project_registry": sources["project_registry_entry"],
        "project_state": sources["project_state"],
        "task_authority": sources["task_authority"],
        "package_authority": sources["package_authority"],
        "latest_checkpoint": None,
    }


def run_fixture(
    fixture_dir: Path,
    registry: SchemaRegistry,
    predicates: PredicateRegistry,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixture = load_yaml(fixture_dir / "fixture.yaml")
    observations = load_json(fixture_dir / "inputs" / "observations.json")
    policy = registry.spec("permission_policy.yaml")
    context = _base_context()
    context.update(observations)
    expected_codes = [str(code) for code in fixture.get("expected_condition_codes", [])]
    subsystem_outputs: dict[str, Any] = {}
    effective_sources = observations.get("effective_state_sources")
    if isinstance(effective_sources, Mapping):
        preliminary_state = EffectiveStateResolver(status_registry=registry.spec("status_normalization.yaml")).resolve(
            effective_sources,
            resolved_at="2026-01-01T00:00:00Z",
            resolution_id=f"resolution-{fixture['fixture_id']}",
        )
        allowed = _values(preliminary_state["constraints"]["allowed_actions"])
        forbidden = _values(preliminary_state["constraints"]["forbidden_actions"])
        context.update(
            {
                "effective_state": preliminary_state,
                "parent_permissions": list(effective_sources.get("global_policy", {}).get("allowed_actions", [])),
                "proposed_permissions": allowed,
                "local_restrictions": {"forbidden_actions": forbidden},
            }
        )
        if fixture["fixture_id"] == "F10":
            observations["required_flag_missing_or_false"] = str(fixture["requested_operation"]) in forbidden or str(fixture["requested_operation"]) not in allowed
    detected = ConditionDetector().detect_many(observations)
    codes = [item["condition_code"] for item in detected if item["observed"]]
    assert codes == expected_codes
    if isinstance(effective_sources, Mapping):
        resolved_sources = dict(effective_sources)
        resolved_sources["observed_condition_codes"] = codes
        effective_state = EffectiveStateResolver(status_registry=registry.spec("status_normalization.yaml")).resolve(
            resolved_sources,
            resolved_at="2026-01-01T00:00:00Z",
            resolution_id=f"resolution-{fixture['fixture_id']}",
        )
        subsystem_outputs["effective_state"] = effective_state
        context["effective_state"] = effective_state
        context["proposed_permissions"] = _values(effective_state["constraints"]["allowed_actions"])
    events = observations.get("events")
    if isinstance(events, list):
        initial_state = observations.get("derived_snapshot")
        subsystem_outputs["materialized_view"] = materialize_events(events, initial_state if isinstance(initial_state, Mapping) else None)
    decision = PermissionEvaluator(policy, predicates).evaluate(
        str(fixture["requested_operation"]),
        codes,
        context=context,
        request_id=str(fixture["fixture_id"]),
        decision_id=f"decision-{fixture['fixture_id']}",
        decided_at="2026-01-01T00:00:00Z",
    )
    if fixture["fixture_id"] == "F10":
        effective_state = subsystem_outputs["effective_state"]
        candidate_decision = PermissionEvaluator(policy, predicates).evaluate(
            "EXECUTE_AND_CHECKPOINT",
            [],
            context=context,
            request_id="F10-candidate",
            decision_id="decision-F10-candidate",
            decided_at="2026-01-01T00:00:00Z",
        )
        subsystem_outputs["candidate_capsule"] = CandidateCapsuleCompiler().compile(
            effective_state,
            candidate_decision,
            capsule_id="candidate-F10",
            compiled_at="2026-01-01T00:00:00Z",
            idempotency_key="candidate-F10-key",
            context={"source_revisions": _capsule_source_revisions(effective_state), "execution_unit_id": "unit-F10"},
        )
    generated = decision
    expected = load_json(fixture_dir / "expected" / "transition_decision.json")
    return fixture, generated, expected, decision, subsystem_outputs


def assert_fixture_must_not(fixture: Mapping[str, Any], generated: Mapping[str, Any], decision: Mapping[str, Any], subsystem_outputs: Mapping[str, Any]) -> None:
    expected_result = str(fixture["expected_result"])
    for directive in fixture.get("must_not", []):
        if directive in {"mutate_stale_document", "advance_content_state", "infer_running_from_launch", "create_second_active_claim", "classify_conflict_as_retry", "accept_reconstructed_substitute", "change_expected_hash", "promote_shadow_implicitly", "union_global_permissions", "auto_adopt_new_fingerprint", "treat_snapshot_as_peer_authority"}:
            assert generated["result"] == expected_result
        if directive == "mutate_stale_document":
            assert generated["result"] == "ALLOW" and decision["operation_class"] == "READ_DIAGNOSE"
            state = subsystem_outputs["effective_state"]
            assert state["policy"]["epoch"]["value"] == "policy-v0.1"
            assert "MUTATE_CONTROL_STATE" in _values(state["constraints"]["forbidden_actions"])
        elif directive == "advance_content_state":
            assert decision["operation_class"] == "LIVENESS_REPAIR" and decision["write_plan"]["allowed"] and generated["result"] == "ALLOW"
        elif directive == "infer_running_from_launch":
            assert "RUNNING" not in json.dumps(generated, sort_keys=True)
        elif directive == "create_second_active_claim":
            assert generated["result"] == "NOOP_IDEMPOTENT"
        elif directive in {"classify_conflict_as_retry", "accept_reconstructed_substitute", "change_expected_hash", "promote_shadow_implicitly", "union_global_permissions"}:
            assert generated["result"] == "DENY"
            if directive == "union_global_permissions":
                state = subsystem_outputs["effective_state"]
                candidate = subsystem_outputs["candidate_capsule"]
                assert "MUTATE_CONTROL_STATE" not in _values(state["constraints"]["allowed_actions"])
                assert "MUTATE_CONTROL_STATE" in _values(state["constraints"]["forbidden_actions"])
                assert "MUTATE_CONTROL_STATE" in candidate["execution"]["forbidden_actions"]
        elif directive == "auto_adopt_new_fingerprint":
            assert generated["result"] == "DENY"
        elif directive == "treat_snapshot_as_peer_authority":
            assert decision["operation_class"] == "SHADOW_VALIDATE" and generated["result"] == "ALLOW"
            assert subsystem_outputs["materialized_view"]["state"]["status"] == "S2"


def canonical_golden_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value)
