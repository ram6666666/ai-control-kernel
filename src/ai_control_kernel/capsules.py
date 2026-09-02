"""Candidate/Execution capsule compilation and invalidation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .canonical import canonical_json_bytes, normalize_timestamp, sha256_bytes


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _source(value: object, fallback: str) -> dict[str, Any]:
    source = _map(value)
    return {
        "source_type": str(source.get("source_type", "DERIVED_VIEW")),
        "locator": str(source.get("locator", fallback)),
        "revision": source.get("revision"),
        "content_hash": source.get("content_hash"),
        "observed_at": source.get("observed_at"),
        "authority_class": str(source.get("authority_class", "DERIVED")),
    }


def _source_revisions(state: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    current = _map(context.get("source_revisions", _map(state.get("sources"))))
    keys = ("policy_fingerprint", "permission_policy", "state_machine", "status_normalization", "project_registry", "project_state", "task_authority", "package_authority", "latest_checkpoint")
    result: dict[str, Any] = {}
    for key in keys:
        result[key] = current.get(key) if key in current else None
    return result


class CandidateCapsuleCompiler:
    def compile(
        self,
        effective_state: Mapping[str, Any],
        transition_decision: Mapping[str, Any],
        *,
        capsule_id: str = "candidate-1",
        compiled_at: str | datetime | None = None,
        idempotency_key: str = "candidate-key",
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if transition_decision.get("operation_class") != "EXECUTE_AND_CHECKPOINT" or transition_decision.get("result") != "ALLOW":
            raise ValueError("CandidateCapsule requires an ALLOW EXECUTE_AND_CHECKPOINT decision")
        ctx = context or {}
        identity = _map(effective_state.get("identity"))
        execution = _map(effective_state.get("execution"))
        constraints = _map(effective_state.get("constraints"))
        storage = _map(effective_state.get("storage"))
        source = _source(_map(effective_state.get("provenance_trace")).get("execution.normalized_status"), "effective-state")
        inputs = []
        for item in _items(ctx.get("authoritative_inputs", storage.get("authoritative_inputs"))):
            record = _map(item)
            identity_value = _map(record.get("identity"))
            inputs.append({"locator": str(record.get("locator", identity_value.get("locator", "input"))), "identity": identity_value or {"status": "NOT_APPLICABLE", "algorithm": None, "expected": None, "observed": None, "source": None}, "purpose": str(record.get("purpose", "authoritative input"))})
        if not inputs:
            inputs = [{"locator": "none", "identity": {"status": "NOT_APPLICABLE", "algorithm": None, "expected": None, "observed": None, "source": None}, "purpose": "no declared input"}]
        allowed = [str(item.get("value", item)) if isinstance(item, Mapping) else str(item) for item in _items(constraints.get("allowed_actions"))]
        forbidden = [str(item.get("value", item)) if isinstance(item, Mapping) else str(item) for item in _items(constraints.get("forbidden_actions"))]
        package_id = _map(identity.get("package_id")).get("value")
        task_id = _map(identity.get("task_id")).get("value")
        project_id = _map(identity.get("project_id")).get("value", "unknown-project")
        capsule = {
            "schema_version": "ack.candidate_capsule.v0.1",
            "capsule_type": "CANDIDATE",
            "capsule_id": capsule_id,
            "compiled_at": normalize_timestamp(compiled_at or datetime.now(timezone.utc)),
            "source_revisions": _source_revisions(effective_state, ctx),
            "identity": {"project_id": str(project_id), "task_id": str(task_id or "unknown-task"), "package_id": str(package_id) if package_id is not None else None, "execution_unit_id": str(ctx.get("execution_unit_id", package_id or task_id or "execution-unit"))},
            "execution": {"phase": str(_map(execution.get("phase")).get("value", "UNKNOWN")), "role": str(_map(execution.get("role")).get("value", "UNKNOWN")), "objective": str(_map(execution.get("objective")).get("value", "")), "allowed_actions": list(dict.fromkeys(allowed)), "forbidden_actions": list(dict.fromkeys(forbidden))},
            "inputs": {"authoritative_inputs": inputs, "reference_packet": ctx.get("reference_packet")},
            "outputs": {"write_targets": [str(item.get("value", item)) if isinstance(item, Mapping) else str(item) for item in _items(storage.get("write_targets"))], "checkpoint_target": ctx.get("checkpoint_target"), "event_root": str(ctx.get("event_root", "events"))},
            "concurrency": {"claim_id": None, "lease_or_expected_revision": None, "idempotency_key": idempotency_key},
            "acceptance": {"local_gate": ctx.get("local_gate"), "audit_required": bool(ctx.get("audit_required", False)), "acceptance_gate": ctx.get("acceptance_gate", {}), "next_legal_transition": ctx.get("next_legal_transition")},
            "capabilities": {"required": [str(item) for item in _items(ctx.get("required_capabilities"))], "forbidden_or_unavailable": [str(item) for item in _items(ctx.get("forbidden_capabilities"))]},
            "integrity": {"compiler_result": str(transition_decision.get("risk_mode", "GREEN")), "observed_condition_codes": list(transition_decision.get("observed_condition_codes", [])), "blockers": list(transition_decision.get("blocking_condition_codes", [])), "warnings": list(transition_decision.get("nonblocking_warning_codes", []))},
            "provenance_trace": {"effective_state": source, "decision": _source(ctx.get("decision_source"), "transition-decision")},
        }
        return capsule

    def validate(self, capsule: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        if capsule.get("schema_version") != "ack.candidate_capsule.v0.1":
            errors.append("invalid candidate schema_version")
        if capsule.get("capsule_type") != "CANDIDATE":
            errors.append("candidate capsule_type must be CANDIDATE")
        concurrency = _map(capsule.get("concurrency"))
        if concurrency.get("claim_id") is not None or concurrency.get("lease_or_expected_revision") is not None:
            errors.append("candidate capsule cannot carry claim/lease identity")
        integrity = _map(capsule.get("integrity"))
        if integrity.get("compiler_result") == "RED":
            errors.append("candidate capsule cannot be executable under RED integrity")
        return errors


class ExecutionCapsuleCompiler:
    def compile(
        self,
        candidate: Mapping[str, Any],
        claim: Mapping[str, Any],
        claim_decision: Mapping[str, Any],
        *,
        capsule_id: str = "execution-1",
        compiled_at: str | datetime | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        errors = CandidateCapsuleCompiler().validate(candidate)
        if errors:
            raise ValueError("invalid candidate capsule: " + "; ".join(errors))
        if claim_decision.get("operation_class") != "CLAIM_EXECUTION_UNIT" or claim_decision.get("result") != "ALLOW":
            raise ValueError("ExecutionCapsule requires an ALLOW CLAIM_EXECUTION_UNIT decision")
        claim_source = _source(claim.get("source_ref"), "claim")
        result = dict(candidate)
        result.update({"schema_version": "ack.execution_capsule.v0.1", "capsule_type": "EXECUTION", "capsule_id": capsule_id, "candidate_capsule_id": str(candidate.get("capsule_id")), "candidate_payload_hash": sha256_bytes(canonical_json_bytes(candidate)), "compiled_at": normalize_timestamp(compiled_at or datetime.now(timezone.utc)), "concurrency": {"claim_id": str(claim.get("claim_id")), "claimant": str(claim.get("claimant")), "lease_or_expected_revision": str(claim.get("lease_revision")), "idempotency_key": str(idempotency_key or claim.get("idempotency_key", "execution-key")), "claim_source": claim_source}})
        result["provenance_trace"] = dict(_map(candidate.get("provenance_trace"))) | {"claim": claim_source, "claim_verification_decision": _source(claim_decision.get("decision_source"), "claim-decision")}
        return result

    def validate(self, capsule: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        if capsule.get("schema_version") != "ack.execution_capsule.v0.1":
            errors.append("invalid execution schema_version")
        if capsule.get("capsule_type") != "EXECUTION":
            errors.append("execution capsule_type must be EXECUTION")
        concurrency = _map(capsule.get("concurrency"))
        for field in ("claim_id", "claimant", "lease_or_expected_revision", "idempotency_key", "claim_source"):
            if not concurrency.get(field):
                errors.append(f"missing execution claim field: {field}")
        return errors


def is_capsule_invalidated(capsule: Mapping[str, Any], current_source_revisions: Mapping[str, Any], current_claim: Mapping[str, Any] | None = None) -> bool:
    bound = _map(capsule.get("source_revisions"))
    if dict(bound) != dict(current_source_revisions):
        return True
    if capsule.get("capsule_type") == "CANDIDATE":
        return False
    concurrency = _map(capsule.get("concurrency"))
    claim = current_claim or {}
    if claim.get("status") in {"RELEASED", "EXPIRED", "REASSIGNED", "CONFLICT"}:
        return True
    return any(concurrency.get(field) != claim.get(field) for field in ("claim_id", "claimant", "lease_or_expected_revision") if field in claim)

