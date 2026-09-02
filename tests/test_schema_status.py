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
    project = {"exact_mappings": {"READY": "BLOCKED"}}
    task = {"exact_mappings": {"READY": "RUNNING"}}
    assert normalizer.normalize("READY", project_extension=project, project_task_extension=task) == "RUNNING"


def test_validation_reports_paths() -> None:
    errors = validate_document({}, {"type": "object", "required": ["x"]})
    assert errors and errors[0].startswith("$")

