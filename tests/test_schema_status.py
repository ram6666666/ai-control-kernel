from ai_control_kernel.schema import validate_document
from ai_control_kernel.status import StatusNormalizer


def test_frozen_registry_schema_cross_references(registry) -> None:
    results = registry.validate_all()
    assert all(not errors for errors in results.values())


def test_yaml_is_safe_and_unknown_status_is_exact(status_registry) -> None:
    normalizer = StatusNormalizer(status_registry)
    assert normalizer.normalize("  RUNNING  ") == "RUNNING"
    assert normalizer.normalize("running") == "UNKNOWN"
    assert normalizer.normalize("not-a-status") == "UNKNOWN"


def test_extension_precedence(status_registry) -> None:
    normalizer = StatusNormalizer(status_registry)
    project = {"namespace": "project", "version": "1", "owner_class": "PROJECT_TASK_CONTROL", "exact_mappings": {"READY": "BLOCKED"}, "rationale_pointer": "fixture/project", "may_override_global_mapping": True, "override_requires_explicit_raw_status_key": True, "may_change_semantic_meaning_without_authority": False}
    task = {"namespace": "task", "version": "1", "owner_class": "PROJECT_TASK_CONTROL", "exact_mappings": {"READY": "RUNNING"}, "rationale_pointer": "fixture/task", "may_override_global_mapping": True, "override_requires_explicit_raw_status_key": True, "may_change_semantic_meaning_without_authority": False}
    assert normalizer.normalize("READY", project_extension=project, project_task_extension=task) == "RUNNING"


def test_invalid_extension_metadata_cannot_override_global(status_registry) -> None:
    normalizer = StatusNormalizer(status_registry)
    invalid = {"exact_mappings": {"READY": "BLOCKED"}}
    assert normalizer.normalize("READY", project_extension=invalid) == "READY"


def test_validation_reports_paths() -> None:
    errors = validate_document({}, {"type": "object", "required": ["x"]})
    assert errors and errors[0].startswith("$")

