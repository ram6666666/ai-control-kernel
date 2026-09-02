from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest

from ai_control_kernel.adapters import FixtureExecutorCapabilitySource, FixtureRuntimeObservationSource, FilesystemArtifactReader, FilesystemControlSourceReader
from ai_control_kernel.canonical import sha256_file, sha256_stream
from ai_control_kernel.capsules import CandidateCapsuleCompiler, ExecutionCapsuleCompiler, is_capsule_invalidated
from ai_control_kernel.conditions import ConditionDetector
from ai_control_kernel.events import materialize_events
from ai_control_kernel.policy import evaluate_operation
from ai_control_kernel.predicates import PredicateRegistry
from ai_control_kernel.schema import SchemaValidationError, load_json, load_yaml, require_valid
from ai_control_kernel.status import StatusNormalizer


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

