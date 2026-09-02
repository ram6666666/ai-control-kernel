"""Exact raw-status normalization with explicit extension precedence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class StatusNormalizer:
    def __init__(self, registry: Mapping[str, Any]) -> None:
        self.registry = registry
        mappings = registry.get("mappings", {})
        self.global_mapping: Mapping[str, str] = mappings.get("global", {})

    @staticmethod
    def _extension_mapping(extension: Mapping[str, Any] | None) -> Mapping[str, str]:
        if extension is None:
            return {}
        required_text = ("namespace", "version", "owner_class", "rationale_pointer")
        if any(not isinstance(extension.get(field), str) or not extension[field].strip() for field in required_text):
            return {}
        if extension.get("may_override_global_mapping") is not True:
            return {}
        if extension.get("override_requires_explicit_raw_status_key") is not True:
            return {}
        if extension.get("may_change_semantic_meaning_without_authority") is not False:
            return {}
        exact = extension.get("exact_mappings", {})
        return exact if isinstance(exact, Mapping) else {}

    def normalize(
        self,
        raw_status: object,
        *,
        project_task_extension: Mapping[str, Any] | None = None,
        project_extension: Mapping[str, Any] | None = None,
    ) -> str:
        if not isinstance(raw_status, str):
            return "UNKNOWN"
        value = raw_status.strip()
        if not value:
            return "UNKNOWN"
        for mapping in (
            self._extension_mapping(project_task_extension),
            self._extension_mapping(project_extension),
            self.global_mapping,
        ):
            result = mapping.get(value)
            if isinstance(result, str):
                return result
        return "UNKNOWN"

    def normalize_with_source(self, raw_status: object, **kwargs: Any) -> dict[str, str]:
        normalized = self.normalize(raw_status, **kwargs)
        return {"raw_status": raw_status if isinstance(raw_status, str) else "", "normalized_status": normalized}


def normalize_status(
    raw_status: object,
    registry: Mapping[str, Any],
    *,
    project_task_extension: Mapping[str, Any] | None = None,
    project_extension: Mapping[str, Any] | None = None,
) -> str:
    return StatusNormalizer(registry).normalize(
        raw_status,
        project_task_extension=project_task_extension,
        project_extension=project_extension,
    )
