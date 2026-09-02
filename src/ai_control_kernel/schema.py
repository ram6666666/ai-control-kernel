"""Safe registry loading and Draft 2020-12 validation."""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


class SchemaValidationError(ValueError):
    """Raised when a contract fails its registered JSON Schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _json_compatible(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"YAML value is not JSON-compatible: {type(value).__name__}")


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load YAML with ``safe_load`` and reject non-object documents."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    compatible = _json_compatible(loaded)
    if not isinstance(compatible, dict):
        raise ValueError(f"expected object document in {path}")
    return compatible


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"expected object document in {path}")
    return loaded


def validate_document(document: Any, schema: Mapping[str, Any]) -> list[str]:
    """Return deterministic path-qualified validation errors."""

    try:
        validator = Draft202012Validator(schema)
    except SchemaError:
        raise
    errors = sorted(validator.iter_errors(document), key=lambda error: (list(error.path), error.message))
    return [f"{'/'.join(str(part) for part in error.path) or '$'}: {error.message}" for error in errors]


def require_valid(document: Any, schema: Mapping[str, Any]) -> None:
    errors = validate_document(document, schema)
    if errors:
        raise SchemaValidationError(errors)


class SchemaRegistry:
    """Resolver for the frozen v0.1 schemas and registries."""

    def __init__(self, repository_root: str | Path) -> None:
        self.root = Path(repository_root).resolve()
        self.schema_root = self.root / "schemas" / "v0.1"
        self.spec_root = self.root / "spec" / "v0.1"

    def schema(self, name: str) -> dict[str, Any]:
        return load_json(self.schema_root / name)

    def spec(self, name: str) -> dict[str, Any]:
        return load_yaml(self.spec_root / name)

    def validate_spec(self, spec_name: str, schema_name: str) -> list[str]:
        return validate_document(self.spec(spec_name), self.schema(schema_name))

    def validate_all(self) -> dict[str, list[str]]:
        pairs = {
            "permission_policy.yaml": "permission-policy.schema.json",
            "predicate_registry.yaml": "predicate-registry.schema.json",
            "state_machine.yaml": "state-machine.schema.json",
            "status_normalization.yaml": "status-normalization.schema.json",
        }
        return {spec_name: self.validate_spec(spec_name, schema_name) for spec_name, schema_name in pairs.items()}

