"""Deterministic EffectiveState resolution and narrowing semantics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .canonical import normalize_timestamp
from .status import StatusNormalizer


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _source(source: Mapping[str, Any] | None, source_type: str, locator: str) -> dict[str, Any]:
    candidate = _map(source.get("source_ref")) if source else {}
    return {
        "source_type": str(candidate.get("source_type", source_type)),
        "locator": str(candidate.get("locator", locator)),
        "revision": candidate.get("revision"),
        "content_hash": candidate.get("content_hash"),
        "observed_at": candidate.get("observed_at"),
        "authority_class": str(candidate.get("authority_class", "EVIDENCE")),
    }


def _pv(value: Any, source: Mapping[str, Any], rule: str, warnings: Sequence[str] = ()) -> dict[str, Any]:
    return {"value": value, "source": dict(source), "resolution_rule": rule, "warnings": list(warnings)}


def _value(source: object, key: str, default: Any = None) -> Any:
    return _map(source).get(key, default)


class EffectiveStateResolver:
    """Resolve parent/project/task/package observations into a schema-shaped view."""

    def __init__(self, *, status_normalizer: StatusNormalizer | None = None, status_registry: Mapping[str, Any] | None = None) -> None:
        self.status_normalizer = status_normalizer or (StatusNormalizer(status_registry) if status_registry else None)

    def resolve(
        self,
        sources: Mapping[str, Any],
        *,
        resolved_at: str | datetime | None = None,
        resolution_id: str = "resolution-1",
    ) -> dict[str, Any]:
        global_policy = _map(sources.get("global_policy"))
        project = _map(sources.get("project_state", sources.get("project")))
        task = _map(sources.get("task_authority", sources.get("task")))
        package = _map(sources.get("package_authority", sources.get("package")))
        global_ref = _source(global_policy, "POLICY", "global-policy")
        project_ref = _source(project, "PROJECT_STATE", "project-state") if project else None
        task_ref = _source(task, "TASK_AUTHORITY", "task-authority") if task else None
        package_ref = _source(package, "PACKAGE_AUTHORITY", "package-authority") if package else None
        events = [_source(_map(item), "IMMUTABLE_EVENT", f"event-{index}") for index, item in enumerate(_list(sources.get("immutable_events")))]
        runtime_refs = [_source(_map(item), "RUNTIME_OBSERVATION", f"runtime-{index}") for index, item in enumerate(_list(sources.get("runtime_observations")))]

        policy_epoch = _value(global_policy, "epoch", _value(project, "policy_epoch", "UNKNOWN"))
        fingerprint_status = _value(global_policy, "fingerprint_status", "UNVERIFIED")
        handshake_status = _value(project, "handshake_status") or _value(global_policy, "handshake_status")
        compatibility = _value(project, "project_compatibility", _value(global_policy, "project_compatibility"))
        project_id = _value(project, "project_id", _value(task, "project_id", "unknown-project"))
        task_id = _value(task, "task_id")
        package_id = _value(package, "package_id", _value(task, "package_id"))

        raw_status = _value(package, "raw_status", _value(task, "raw_status", _value(project, "raw_status")))
        normalized = _value(package, "normalized_status", _value(task, "normalized_status"))
        if normalized is None and self.status_normalizer is not None:
            normalized = self.status_normalizer.normalize(raw_status, project_task_extension=_map(task.get("status_extension")), project_extension=_map(project.get("status_extension")))
        normalized = normalized or "UNKNOWN"

        allowed = self._actions(global_policy, project, task, package, key="allowed_actions")
        forbidden = self._actions(global_policy, project, task, package, key="forbidden_actions")
        local_restrictions = self._actions(project, task, package, {}, key="stricter_local_restrictions")
        dependencies = self._actions(project, task, package, {}, key="dependencies")
        gates = self._actions(project, task, package, {}, key="acceptance_gates")

        conditions = [str(item) for item in _list(sources.get("observed_condition_codes", _map(sources.get("health")).get("observed_condition_codes")))]
        conflicts = bool(sources.get("authority_conflict", False)) or _value(project, "authority_resolution") == "CONFLICT"
        authority_resolution = str(sources.get("authority_resolution", "CONFLICT" if conflicts else "UNIQUE"))
        if authority_resolution not in {"UNIQUE", "AMBIGUOUS", "CONFLICT"}:
            authority_resolution = "UNIQUE"
        semantic = any(code.startswith("S_") for code in conditions) or bool(sources.get("semantic_review_required", False))
        amber = any(code.startswith("A_") for code in conditions)
        red = any(code.startswith("R_") for code in conditions)
        mechanical = "RED" if red else "AMBER" if amber else "GREEN"
        warnings = [code for code in conditions if code.startswith("A_")]
        blockers = [code for code in conditions if code.startswith("R_")]
        now = normalize_timestamp(resolved_at or datetime.now(timezone.utc))

        sources_obj = {
            "global_policy_fingerprint": global_ref,
            "project_registry_entry": _source(_map(sources.get("project_registry_entry")), "OTHER", "project-registry") if sources.get("project_registry_entry") else None,
            "project_state": project_ref,
            "task_authority": task_ref,
            "package_authority": package_ref,
            "immutable_events": events,
            "runtime_observations": runtime_refs,
        }
        provenance = {"policy.epoch": global_ref, "identity.project_id": project_ref or global_ref, "execution.normalized_status": package_ref or task_ref or project_ref or global_ref}
        return {
            "schema_version": "ack.effective_state.v0.1",
            "resolved_at": now,
            "resolution_id": resolution_id,
            "sources": sources_obj,
            "policy": {
                "epoch": _pv(policy_epoch, global_ref, "global_policy_precedes_copied_metadata"),
                "fingerprint_status": _pv(fingerprint_status, global_ref, "global_policy_fingerprint"),
                "handshake_status": _pv(handshake_status, project_ref or global_ref, "current_project_handshake") if handshake_status is not None else None,
                "project_compatibility": _pv(compatibility, project_ref or global_ref, "project_binding_compatibility") if compatibility is not None else None,
            },
            "identity": {
                "project_id": _pv(project_id, project_ref or global_ref, "project_identity_precedence"),
                "task_id": _pv(task_id, task_ref or project_ref or global_ref, "task_authority") if task_id is not None else None,
                "package_id": _pv(package_id, package_ref or task_ref or project_ref or global_ref, "package_authority") if package_id is not None else None,
            },
            "execution": {
                "phase": _pv(_value(package, "phase", _value(task, "phase", "UNKNOWN")), package_ref or task_ref or global_ref, "package_then_task_phase"),
                "role": _pv(_value(package, "role", _value(task, "role", "UNKNOWN")), package_ref or task_ref or global_ref, "package_then_task_role"),
                "objective": _pv(_value(package, "objective", _value(task, "objective", "")), package_ref or task_ref or global_ref, "package_then_task_objective"),
                "raw_status": _pv(raw_status, package_ref or task_ref or project_ref or global_ref, "raw_status_preserved") if raw_status is not None else None,
                "normalized_status": _pv(normalized, package_ref or task_ref or project_ref or global_ref, "exact_status_registry_mapping"),
                "implementation_authorized": _pv(bool(_value(package, "implementation_authorized", _value(task, "implementation_authorized", False))), package_ref or task_ref or global_ref, "explicit_authorization_only"),
                "production_authorized": _pv(bool(_value(package, "production_authorized", _value(task, "production_authorized", False))), package_ref or task_ref or global_ref, "explicit_authorization_only"),
            },
            "constraints": {
                "allowed_actions": [_pv(item, package_ref or task_ref or project_ref or global_ref, "narrowing_intersection") for item in allowed],
                "forbidden_actions": [_pv(item, package_ref or task_ref or project_ref or global_ref, "narrowing_union") for item in forbidden],
                "stricter_local_restrictions": [_pv(item, project_ref or task_ref or package_ref or global_ref, "local_restriction_survives_overlay") for item in local_restrictions],
                "dependencies": [_pv(item, task_ref or project_ref or package_ref or global_ref, "declared_dependencies") for item in dependencies],
                "acceptance_gates": [_pv(item, task_ref or project_ref or package_ref or global_ref, "declared_acceptance_gates") for item in gates],
            },
            "storage": {
                "write_targets": [_pv(item, package_ref or task_ref or project_ref or global_ref, "declared_write_targets") for item in self._actions(project, task, package, {}, key="write_targets")],
                "authoritative_inputs": [_pv(item, package_ref or task_ref or project_ref or global_ref, "declared_authoritative_inputs") for item in self._actions(project, task, package, {}, key="authoritative_inputs")],
                "checkpoint_targets": [_pv(item, package_ref or task_ref or project_ref or global_ref, "declared_checkpoint_targets") for item in self._actions(project, task, package, {}, key="checkpoint_targets")],
            },
            "claim": {
                "active_claim_id": _pv(_value(sources.get("claim"), "claim_id"), _source(_map(sources.get("claim")), "CLAIM", "claim"), "current_claim") if _value(sources.get("claim"), "claim_id") is not None else None,
                "claimant": _pv(_value(sources.get("claim"), "claimant"), _source(_map(sources.get("claim")), "CLAIM", "claim"), "current_claim") if _value(sources.get("claim"), "claimant") is not None else None,
                "lease_state": _pv(_value(sources.get("claim"), "status"), _source(_map(sources.get("claim")), "CLAIM", "claim"), "current_claim") if _value(sources.get("claim"), "status") is not None else None,
            },
            "health": {"mechanical_summary": mechanical, "authority_resolution": authority_resolution, "semantic_review_required": semantic, "observed_condition_codes": list(dict.fromkeys(conditions)), "warnings": warnings, "blockers": blockers},
            "provenance_trace": provenance,
        }

    @staticmethod
    def _actions(*layers: Mapping[str, Any], key: str) -> list[str]:
        values: list[str] = []
        for layer in layers:
            for item in _list(layer.get(key)):
                if isinstance(item, Mapping):
                    value = item.get("value", item.get("action", item.get("id")))
                else:
                    value = item
                if isinstance(value, str) and value not in values:
                    values.append(value)
        return values

