from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path

import pytest
from jsonschema.exceptions import UnknownType

from ai_control_kernel.adapters import FixtureExecutorCapabilitySource, FixtureRuntimeObservationSource, FilesystemArtifactReader, FilesystemControlSourceReader
from ai_control_kernel.canonical import canonical_json, normalize_timestamp, sha256_file, sha256_stream, stable_unique
from ai_control_kernel.capsules import CandidateCapsuleCompiler, ExecutionCapsuleCompiler, is_capsule_invalidated
from ai_control_kernel.conditions import ConditionDetector, _result
from ai_control_kernel.effective_state import EffectiveStateResolver
from ai_control_kernel.events import ImmutableEventReader, materialize_events, validate_event
from ai_control_kernel.policy import PermissionEvaluator, evaluate_operation
from ai_control_kernel.predicates import PredicateRegistry
from ai_control_kernel.schema import SchemaValidationError, _json_compatible, load_json, load_yaml, require_valid, validate_document
from ai_control_kernel.state_machine import TransitionValidation, TransitionValidator
from ai_control_kernel.status import StatusNormalizer, normalize_status


def test_adapter_and_hash_edges(tmp_path: Path) -> None:
    (tmp_path / "data.yaml").write_text("value: 2\n", encoding="utf-8")
    (tmp_path / "data.txt").write_text("plain", encoding="utf-8")
    reader = FilesystemControlSourceReader(tmp_path)
    assert reader.read_source("data.yaml")["content"]["value"] == 2
    assert reader.read_source("data.txt")["content"] == "plain"
    artifact = FilesystemArtifactReader(tmp_path)
    with artifact.open_bytes("data.txt") as handle:
        assert handle.read() == b"plain"
    digest, size = sha256_stream(BytesIO(b"abc"), chunk_size=1)
    assert size == 3
    assert digest != sha256_file(tmp_path / "data.txt")[0]
    assert sha256_file(tmp_path / "data.txt", root=tmp_path)[1] == 5
    with pytest.raises(ValueError):
        sha256_file(tmp_path / "data.txt", root=tmp_path / "other")
    assert FixtureRuntimeObservationSource({}).observe_runtime("missing")["observation_type"] == "UNAVAILABLE"
    assert FixtureExecutorCapabilitySource({}).get_capabilities("missing")["executor_id"] == "missing"


def test_schema_and_status_edges(tmp_path: Path, status_registry) -> None:
    (tmp_path / "list.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_json(tmp_path / "list.json")
    with pytest.raises(ValueError):
        load_yaml(tmp_path / "list.json")
    with pytest.raises(SchemaValidationError):
        require_valid({}, {"type": "object", "required": ["x"]})
    normalizer = StatusNormalizer(status_registry)
    assert normalizer.normalize(None) == "UNKNOWN"
    assert normalizer.normalize(1) == "UNKNOWN"
    assert normalizer.normalize("") == "UNKNOWN"
    assert normalizer.normalize_with_source(None)["raw_status"] == ""


def test_condition_negative_and_unknown_edges() -> None:
    detector = ConditionDetector()
    for code in ("A_STALE_DERIVED_VIEW", "A_STALE_COPIED_METADATA", "A_OPTIONAL_TELEMETRY_MISSING", "A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT", "A_HISTORICAL_POLICY_TEXT_PRESENT", "A_NONCRITICAL_REFERENCE_UNAVAILABLE"):
        assert detector.detect(code, {})["observed"] is False
    for code in ("R_AUTHORITY_CONFLICT", "R_POLICY_INCOMPATIBLE", "R_POLICY_FINGERPRINT_MISMATCH", "R_ARTIFACT_IDENTITY_MISMATCH", "R_REQUIRED_ARTIFACT_UNAVAILABLE", "R_CLAIM_CONFLICT", "R_STALE_EXPECTED_REVISION", "R_ILLEGAL_TRANSITION", "R_MISSING_AUTHORIZATION", "R_ROLE_WRITE_VIOLATION", "R_REQUIRED_GATE_MISSING"):
        assert detector.detect(code, {})["observed"] is False
    for code in ("S_AUTHORITY_MEANING_AMBIGUOUS", "S_SCOPE_CHANGE_AMBIGUOUS", "S_REQUIREMENT_CONFLICT", "S_ACCEPTANCE_JUDGMENT_REQUIRED"):
        assert detector.detect(code, {})["observed"] is False
    with pytest.raises(ValueError):
        detector.detect("P_UNKNOWN", {})


def test_event_validation_edges() -> None:
    with pytest.raises(ValueError):
        materialize_events([{"event_id": "e", "event_type": "x", "payload": {}, "source_ref": {}, "predecessor_ref": "wrong"}])
    with pytest.raises(ValueError):
        materialize_events([{"event_id": "e", "event_type": "x", "payload": {}, "source_ref": {}, "predecessor_ref": None}, {"event_id": "e2", "event_type": "x", "payload": {}, "source_ref": {}, "predecessor_ref": "other"}])


def test_capsule_validation_edges() -> None:
    compiler = CandidateCapsuleCompiler()
    with pytest.raises(ValueError):
        compiler.compile({}, {"operation_class": "READ_DIAGNOSE", "result": "ALLOW"})
    assert compiler.validate({"schema_version": "bad", "capsule_type": "BAD", "concurrency": {"claim_id": "x", "lease_or_expected_revision": "x"}, "integrity": {"compiler_result": "RED"}})
    execution = ExecutionCapsuleCompiler()
    with pytest.raises(ValueError):
        execution.compile({}, {}, {})
    assert execution.validate({"schema_version": "bad", "capsule_type": "BAD", "concurrency": {}})
    assert is_capsule_invalidated({"capsule_type": "CANDIDATE", "source_revisions": {}}, {}) is False


def test_predicate_false_branches(predicate_registry: PredicateRegistry) -> None:
    base = {"actor_role": "x", "target_state_class": "y", "single_writer_map": {}, "delegations": [{"actor_role": "x", "owner_class": "y", "valid": False}], "parent_permissions": [], "proposed_permissions": ["x"], "local_restrictions": {"forbidden_actions": []}, "operation_gate_spec": {"required": ["g"]}, "available_evidence": ["z"], "proposed_claim": {"execution_unit_id": "u", "claim_id": "c", "claimant": "a", "lease_revision": "1"}, "active_claims": [{"execution_unit_id": "u", "claim_id": "d"}], "requested_mutations": {"status": "RUNNING"}, "shadow_inputs": [{"authority_class": "EVIDENCE", "treated_as_authoritative": True}], "audit_gate": {"exact_artifact_required": False}, "observed_amber_conditions": ["A"], "promotion_gate_relevance_map": {"A": ["facet"]}, "required_promotion_facets": ["facet"], "semantic_change_flags": [True], "requested_policy_repair": {"mechanically_decidable": False}}
    for predicate_id in predicate_registry.registry:
        predicate_registry.evaluate(predicate_id, base)
    assert predicate_registry.evaluate("P_REQUIRED_GATES_PRESENT", {"operation_gate_spec": "bad", "available_evidence": {}}).passed is False


def test_policy_function_and_naive_time(policy, predicate_registry) -> None:
    result = evaluate_operation(policy, "DISCUSS_PLAN", context={}, predicates=predicate_registry)
    assert result["result"] == "ALLOW"
    assert datetime.now().tzinfo is None


def test_canonical_and_schema_alternatives(tmp_path: Path) -> None:
    assert normalize_timestamp("2026-01-01T00:00:00") == "2026-01-01T00:00:00.000000Z"
    with pytest.raises(TypeError):
        sha256_stream(StringIO("not-bytes"))  # type: ignore[arg-type]
    assert stable_unique(["a", "a", "b"]) == ["a", "b"]
    assert canonical_json({"x": 1}) == '{"x":1}'
    assert _json_compatible(datetime(2026, 1, 1)).startswith("2026-01-01")
    assert _json_compatible(date(2026, 1, 1)) == "2026-01-01"
    assert _json_compatible({1: ("x", True)}) == {"1": ["x", True]}
    with pytest.raises(TypeError):
        _json_compatible(object())
    require_valid({"x": 1}, {"type": "object", "required": ["x"]})
    with pytest.raises(UnknownType):
        validate_document({}, {"type": "not-a-real-type"})
    assert normalize_status("READY", {"mappings": {"global": {"READY": "READY"}}}) == "READY"


def test_capsule_and_effective_state_alternatives() -> None:
    state = {
        "identity": {"project_id": {"value": "p"}, "task_id": {"value": "t"}},
        "execution": {"phase": {"value": "RUN"}, "role": {"value": "worker"}, "objective": {"value": "do"}},
        "constraints": {"allowed_actions": [{"action": "READ_DIAGNOSE"}], "forbidden_actions": [{"id": "MUTATE_CONTROL_STATE"}]},
        "storage": {"authoritative_inputs": [{"locator": "input", "identity": {"status": "VERIFIED"}, "purpose": "source"}], "write_targets": []},
        "provenance_trace": {},
    }
    decision = {"operation_class": "EXECUTE_AND_CHECKPOINT", "result": "ALLOW", "risk_mode": "GREEN"}
    candidate = CandidateCapsuleCompiler().compile(state, decision, context={})
    claim = {"claim_id": "c", "claimant": "a", "lease_revision": "1"}
    with pytest.raises(ValueError):
        ExecutionCapsuleCompiler().compile(candidate, claim, {})
    execution = ExecutionCapsuleCompiler().compile(candidate, claim, {"operation_class": "CLAIM_EXECUTION_UNIT", "result": "ALLOW"})
    assert is_capsule_invalidated(execution, candidate["source_revisions"], {"claim_id": "different", "claimant": "a", "lease_or_expected_revision": "1"})
    resolver = EffectiveStateResolver()
    assert resolver._actions({"x": 1, "allowed_actions": [{"action": "A"}, {"id": "B"}, 1, "A"]}, key="allowed_actions") == ["A", "B"]
    resolved = resolver.resolve({"global_policy": {}, "package_authority": {"normalized_status": "READY"}, "authority_resolution": "INVALID"}, resolved_at="2026-01-01T00:00:00Z")
    assert resolved["health"]["authority_resolution"] == "UNIQUE"


def test_condition_event_policy_and_state_alternatives(policy, predicate_registry, state_machine) -> None:
    assert _result("A_STALE_DERIVED_VIEW", False, {}, "x", {"seen": True})["predicate_results"] == {"seen": True}
    assert ConditionDetector().detect("A_STALE_COPIED_METADATA", {"active_authority_value": "a", "copied_metadata_value": "b"})["observed"] is False
    assert ConditionDetector().detect("S_ACCEPTANCE_JUDGMENT_REQUIRED", {})["semantic_review_required"] is False
    assert validate_event({"event_id": 1, "event_type": "x", "payload": {}, "source_ref": {}, "predecessor_ref": None})
    event = {"event_id": "e", "event_type": "x", "payload": {"state": {"x": 1}}, "source_ref": None, "predecessor_ref": None}
    assert materialize_events([event])["evidence"] == []
    assert ImmutableEventReader([event]).list_events() == [event]
    assert PermissionEvaluator(policy, predicate_registry).evaluate("READ_DIAGNOSE", ["S_AUTHORITY_MEANING_AMBIGUOUS"], context={})["result"] == "ALLOW"
    validator = TransitionValidation(True, "r", "OP", "OWNER", (), (), (), "ok")
    assert validator.as_dict()["allowed"] is True
    machine = TransitionValidator(state_machine, predicate_registry)
    assert not machine.validate("NOT_A_STATE", "READY").allowed
    assert not machine.validate("PLANNING", "READY", operation_class="READ_DIAGNOSE", context={}).allowed
    assert not machine.validate("AUDIT_PENDING", "VERIFIED", operation_class="MUTATE_CONTROL_STATE", context={"available_evidence": ["independent_audit_pass_when_required"]}).allowed


def test_predicate_dispatch_and_alternate_inputs(predicate_registry: PredicateRegistry) -> None:
    assert predicate_registry.evaluate("P_UNKNOWN", {"evidence": {"locator": "one"}}).evidence
    assert not predicate_registry.evaluate("P_UNKNOWN", {"evidence": "not-a-sequence"}).evidence
    custom = PredicateRegistry({"predicates": {"P_CUSTOM": {"evaluator": "missing"}, "P_RAISE": {"evaluator": "raise_type"}}})
    custom._EVALUATORS["raise_type"] = lambda _context: (_ for _ in ()).throw(TypeError("bad input"))
    assert custom.evaluate("P_CUSTOM").reason == "unimplemented predicate evaluator"
    assert custom.evaluate("P_RAISE").passed is False
    assert predicate_registry._writer_owner({"actor_role": "A", "target_state_class": "T", "single_writer_map": {"T": "O"}, "delegations": [{"actor_role": "A", "owner_class": "O", "valid": True}]})
    assert predicate_registry._required_integrity({"operation_required_integrity_verdicts": []})
    assert not predicate_registry._source_current({"expected_revisions": {}, "observed_current_revisions": {"x": "1"}})
    assert predicate_registry._required_gates({"operation_gate_spec": {"gates": ["g"]}, "available_evidence": ["g"]})
    assert not predicate_registry._required_gates({"operation_gate_spec": "bad", "available_evidence": {}})
    proposed = {"execution_unit_id": "u", "claim_id": "c", "claimant": "a", "lease_revision": "1", "idempotency_key": "k", "payload_hash": "h"}
    assert predicate_registry._claim_conflict_absent({"proposed_claim": proposed, "idempotency_record": {"idempotency_key": "k", "claim_id": "c", "payload_hash": "h"}})
    assert not predicate_registry._claim_conflict_absent({"proposed_claim": proposed, "idempotency_record": {"idempotency_key": "k", "claim_id": "other", "payload_hash": "h"}})
    assert predicate_registry._claim_conflict_absent({"proposed_claim": proposed, "active_claims": [{"execution_unit_id": "other"}]})
    assert predicate_registry._claim_conflict_absent({"proposed_claim": proposed, "active_claims": [{"execution_unit_id": "u", "claim_id": "c", "claimant": "a", "lease_revision": "1"}]})
    assert not predicate_registry._claim_conflict_absent({"proposed_claim": proposed, "active_claims": [{"execution_unit_id": "u", "claim_id": "other"}]})
    assert predicate_registry._recovery_no_content_advance({"requested_mutations": {"worker_enabled": True}})
    assert not predicate_registry._recovery_no_content_advance({"requested_mutations": {"status": "RUNNING"}})
    assert predicate_registry._recovery_target_observed({"requested_repair_condition_code": "A", "observed_condition_codes": ["A"]})
    assert not predicate_registry._recovery_target_observed({"requested_repair_condition_code": 1, "observed_condition_codes": [1]})
    assert not predicate_registry._shadow_input_trust({"shadow_inputs": [{"treated_as_authoritative": True, "authority_class": "EVIDENCE"}]})
    assert predicate_registry._shadow_input_trust({"shadow_inputs": [{"treated_as_authoritative": False, "authority_class": "EVIDENCE"}]})
    assert predicate_registry._noncanonical_explicit({"requested_output_authority_class": "NONCANONICAL"})
    assert predicate_registry._audit_input_exact({"audit_gate": {"exact_artifact_required": False}})
    assert predicate_registry._audit_input_exact({"audit_gate": {"exact_artifact_required": True}, "audit_input_identity": {"status": "VERIFIED"}, "retrieval_observation": {"independent_retrieval_verified": True}})
    assert not predicate_registry._audit_input_exact({"audit_gate": {"exact_artifact_required": True}})
    assert predicate_registry._promotion_amber_irrelevant({"observed_amber_conditions": ["A"], "promotion_gate_relevance_map": {"A": ["other"]}, "required_promotion_facets": ["facet"]})
    assert not predicate_registry._promotion_amber_irrelevant({"observed_amber_conditions": ["A"], "promotion_gate_relevance_map": {"A": ["facet"]}, "required_promotion_facets": ["facet"]})
    assert predicate_registry._recovery_role({"actor_role": "A", "recovery_owner_class": "A"})
    assert predicate_registry._recovery_role({"actor_role": "A", "recovery_owner_class": "O", "delegations": [{"actor_role": "A", "owner_class": "O", "valid": True}]})
    assert predicate_registry._policy_reconciliation_scope({"semantic_change_flags": [], "requested_policy_repair": {}})
    assert not predicate_registry._policy_reconciliation_scope({"semantic_change_flags": [True], "requested_policy_repair": {}})


def test_each_frozen_operation_and_state_edge_is_exercised(policy, predicate_registry, state_machine) -> None:
    evaluator = PermissionEvaluator(policy, predicate_registry)
    context = {
        "authority_resolution": "UNIQUE",
        "expected_revisions": {"task": "1"},
        "observed_current_revisions": {"task": "1"},
        "operation_required_integrity_verdicts": [{"status": "VERIFIED"}],
        "required_gates": [],
        "available_evidence": {},
        "active_claims": [],
        "proposed_claim": {},
        "requested_mutations": {},
        "parent_permissions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE"],
        "proposed_permissions": [],
        "local_restrictions": [],
        "requested_output_authority_class": "NONCANONICAL",
        "shadow_inputs": [],
        "audit_gate": {"exact_artifact_required": False},
        "observed_amber_conditions": [],
        "required_promotion_facets": [],
        "semantic_change_flags": [],
        "requested_policy_repair": {},
        "requested_repair_condition_code": "A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT",
        "observed_condition_codes": ["A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT"],
        "recovery_owner_class": "PACKAGE_CONTROLLER",
    }
    for operation in policy["base_by_operation"]:
        decision = evaluator.evaluate(operation, context=context)
        assert decision["operation_class"] == operation
    validator = TransitionValidator(state_machine, predicate_registry)
    for rule in state_machine["rules"]:
        current = str(rule.get("from", rule.get("from_set", [""])[0]))
        target = str(rule["to"])
        edge_context = dict(context)
        edge_context.update({"actor_role": str(rule["writer_owner"]), "target_state_class": str(rule["writer_owner"])})
        if rule.get("evidence_requirements"):
            edge_context["evidence_requirements"] = {str(item): True for item in rule["evidence_requirements"]}
        result = validator.validate(current, target, operation_class=str(rule["operation_class"]), context=edge_context)
        assert result.rule_id == str(rule["id"])

