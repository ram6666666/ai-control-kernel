from ai_control_kernel.effective_state import EffectiveStateResolver
from ai_control_kernel.schema import validate_document


def test_effective_state_precedence_and_schema(registry, status_registry) -> None:
    global_policy = {"epoch": "N", "fingerprint_status": "VERIFIED", "allowed_actions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE"], "source_ref": {"source_type": "POLICY", "locator": "global", "authority_class": "CANONICAL"}}
    project = {"project_id": "project-alpha", "raw_status": "READY", "forbidden_actions": ["MUTATE_CONTROL_STATE"], "source_ref": {"source_type": "PROJECT_STATE", "locator": "project", "authority_class": "NARROWING_AUTHORITY"}}
    task = {"task_id": "task-001", "raw_status": "READY", "source_ref": {"source_type": "TASK_AUTHORITY", "locator": "task", "authority_class": "AUTHORITATIVE_CURRENT"}}
    state = EffectiveStateResolver(status_registry=status_registry).resolve({"global_policy": global_policy, "project_state": project, "task_authority": task}, resolved_at="2026-01-01T00:00:00Z", resolution_id="r1")
    assert state["identity"]["project_id"]["value"] == "project-alpha"
    assert state["execution"]["normalized_status"]["value"] == "READY"
    assert not validate_document(state, registry.schema("core-contracts.schema.json"))


def test_permission_layers_intersect_and_retain_item_provenance() -> None:
    resolver = EffectiveStateResolver()
    sources = {
        "global_policy": {"allowed_actions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE"], "source_ref": {"source_type": "POLICY", "locator": "global", "authority_class": "CANONICAL"}},
        "project_state": {"allowed_actions": ["READ_DIAGNOSE", "MUTATE_CONTROL_STATE", "PUBLISH_AUTHORITATIVE_ARTIFACT"], "source_ref": {"source_type": "PROJECT_STATE", "locator": "project", "authority_class": "NARROWING_AUTHORITY"}},
        "task_authority": {"allowed_actions": ["READ_DIAGNOSE"], "source_ref": {"source_type": "TASK_AUTHORITY", "locator": "task", "authority_class": "AUTHORITATIVE_CURRENT"}},
    }
    state = resolver.resolve(sources, resolved_at="2026-01-01T00:00:00Z")
    allowed = state["constraints"]["allowed_actions"]
    assert [item["value"] for item in allowed] == ["READ_DIAGNOSE"]
    assert allowed[0]["source"]["locator"] == "task"


def test_invalid_authority_resolution_is_ambiguous() -> None:
    state = EffectiveStateResolver().resolve({"global_policy": {}, "authority_resolution": "NOT_A_STATE"}, resolved_at="2026-01-01T00:00:00Z")
    assert state["health"]["authority_resolution"] == "AMBIGUOUS"
    assert state["health"]["semantic_review_required"] is True
