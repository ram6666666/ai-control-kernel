"""Deterministic condition detectors owned by the kernel core."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence


AMBER_CODES = {
    "A_STALE_DERIVED_VIEW", "A_STALE_COPIED_METADATA", "A_OPTIONAL_TELEMETRY_MISSING",
    "A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT", "A_HISTORICAL_POLICY_TEXT_PRESENT", "A_NONCRITICAL_REFERENCE_UNAVAILABLE",
}
RED_CODES = {
    "R_AUTHORITY_CONFLICT", "R_POLICY_INCOMPATIBLE", "R_POLICY_FINGERPRINT_MISMATCH", "R_ARTIFACT_IDENTITY_MISMATCH",
    "R_REQUIRED_ARTIFACT_UNAVAILABLE", "R_CLAIM_CONFLICT", "R_STALE_EXPECTED_REVISION", "R_ILLEGAL_TRANSITION",
    "R_MISSING_AUTHORIZATION", "R_ROLE_WRITE_VIOLATION", "R_REQUIRED_GATE_MISSING",
}
SEMANTIC_CODES = {"S_AUTHORITY_MEANING_AMBIGUOUS", "S_SCOPE_CHANGE_AMBIGUOUS", "S_REQUIREMENT_CONFLICT", "S_ACCEPTANCE_JUDGMENT_REQUIRED"}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _refs(observations: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates = observations.get("evidence", observations.get("source_refs", []))
    if isinstance(candidates, Mapping):
        candidates = [candidates]
    return [item for item in _list(candidates) if isinstance(item, Mapping)]


def _result(code: str, observed: bool, observations: Mapping[str, Any], explanation: str, predicates: Mapping[str, bool] | None = None) -> dict[str, Any]:
    cls = "AMBER" if code in AMBER_CODES else "RED" if code in RED_CODES else "SEMANTIC"
    return {
        "condition_code": code,
        "condition_class": cls,
        "detector_id": f"detect_{code.lower()}",
        "observed": observed,
        "evidence": _refs(observations),
        "predicate_results": dict(predicates or {}),
        "explanation": explanation,
        "semantic_review_required": cls == "SEMANTIC" and observed,
    }


class ConditionDetector:
    _detectors: dict[str, Callable[[Mapping[str, Any]], tuple[bool, str, Mapping[str, bool]]]]

    def __init__(self, registry: Mapping[str, Any] | None = None) -> None:
        self.registry = registry or {}
        self._detectors = {
            "A_STALE_DERIVED_VIEW": self._stale_derived,
            "A_STALE_COPIED_METADATA": self._stale_copied,
            "A_OPTIONAL_TELEMETRY_MISSING": self._optional_telemetry,
            "A_SCHEDULER_DEGRADED_NO_SIDE_EFFECT": self._scheduler_degraded,
            "A_HISTORICAL_POLICY_TEXT_PRESENT": self._historical_policy,
            "A_NONCRITICAL_REFERENCE_UNAVAILABLE": self._noncritical_reference,
            "R_AUTHORITY_CONFLICT": self._authority_conflict,
            "R_POLICY_INCOMPATIBLE": self._policy_incompatible,
            "R_POLICY_FINGERPRINT_MISMATCH": self._fingerprint_mismatch,
            "R_ARTIFACT_IDENTITY_MISMATCH": self._artifact_mismatch,
            "R_REQUIRED_ARTIFACT_UNAVAILABLE": self._required_artifact_unavailable,
            "R_CLAIM_CONFLICT": self._claim_conflict,
            "R_STALE_EXPECTED_REVISION": self._stale_revision,
            "R_ILLEGAL_TRANSITION": self._illegal_transition,
            "R_MISSING_AUTHORIZATION": self._missing_authorization,
            "R_ROLE_WRITE_VIOLATION": self._role_violation,
            "R_REQUIRED_GATE_MISSING": self._required_gate_missing,
            "S_AUTHORITY_MEANING_AMBIGUOUS": self._semantic_authority,
            "S_SCOPE_CHANGE_AMBIGUOUS": self._semantic_scope,
            "S_REQUIREMENT_CONFLICT": self._semantic_requirement,
            "S_ACCEPTANCE_JUDGMENT_REQUIRED": self._semantic_acceptance,
        }

    def detect(self, condition_code: str, observations: Mapping[str, Any] | None = None) -> dict[str, Any]:
        facts = observations or {}
        detector = self._detectors.get(condition_code)
        if detector is None:
            raise ValueError(f"unknown condition code: {condition_code}")
        observed, explanation, predicates = detector(facts)
        return _result(condition_code, observed, facts, explanation, predicates)

    def detect_many(self, observations: Mapping[str, Any], condition_codes: Sequence[str] | None = None) -> list[dict[str, Any]]:
        codes = list(condition_codes or self._detectors)
        return [self.detect(code, observations) for code in codes]

    @staticmethod
    def _stale_derived(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        auth, derived = _map(o.get("authoritative_source_revisions")), _map(o.get("derived_view_source_revisions"))
        return bool(auth and derived and auth != derived), "derived view revision differs from authoritative source", {"revisions_differ": auth != derived}

    @staticmethod
    def _stale_copied(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        active, copied = o.get("active_authority_value"), o.get("copied_metadata_value")
        return active != copied and "declared_precedence_rule" in o, "copied metadata differs from stronger active authority", {"values_differ": active != copied}

    @staticmethod
    def _optional_telemetry(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        spec, observations = _map(o.get("telemetry_requirement_spec")), _map(o.get("runtime_observations"))
        required = _list(spec.get("optional_fields"))
        missing = [field for field in required if field not in observations]
        return bool(missing), "optional telemetry fields are absent", {"missing": bool(missing)}

    @staticmethod
    def _scheduler_degraded(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        checks = {"scheduler_attempt_observed": bool(o.get("scheduler_attempt_observed", o.get("scheduler_observation"))), "start_receipt_absent": not bool(_list(o.get("start_receipts"))), "claim_absent": not bool(_list(o.get("claims"))), "content_event_absent": not bool(_list(o.get("task_events"))), "checkpoint_absent": not bool(_list(o.get("checkpoints"))), "artifact_absent": not bool(_list(o.get("artifacts")))}
        return all(checks.values()), "scheduler attempt has no durable side effect", checks

    @staticmethod
    def _historical_policy(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("active_rule_uniquely_resolved")) and bool(o.get("superseded_text_present")), "superseded policy text remains present", {"active_rule_uniquely_resolved": bool(o.get("active_rule_uniquely_resolved")), "superseded_text_present": bool(o.get("superseded_text_present"))}

    @staticmethod
    def _noncritical_reference(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("reference_required_for_operation") is False and bool(o.get("reference_unavailable")), "optional evidence reference is unavailable", {"reference_not_required": o.get("reference_required_for_operation") is False}

    @staticmethod
    def _authority_conflict(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("top_rank_authorities_conflict")) and bool(o.get("declared_reconciliation_rule_absent", True)), "same-rank authorities conflict without reconciliation", {}

    @staticmethod
    def _policy_incompatible(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("compatibility_verdict") == "INCOMPATIBLE", "project binding is incompatible with active policy", {}

    @staticmethod
    def _fingerprint_mismatch(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("any_required_revision_mismatch")) or _map(o.get("expected_monitored_revisions")) != _map(o.get("observed_monitored_revisions")), "monitored policy fingerprint differs", {}

    @staticmethod
    def _artifact_mismatch(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        expected, observed = _map(o.get("expected_artifact_identity")), _map(o.get("observed_artifact_identity"))
        return o.get("identity_comparison") == "MISMATCH" or (bool(expected) and bool(observed) and expected != observed), "artifact byte identity differs", {}

    @staticmethod
    def _required_artifact_unavailable(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("exact_artifact_required")) and o.get("independent_retrieval_verified") is not True, "required artifact cannot be independently retrieved", {}

    @staticmethod
    def _claim_conflict(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("incompatible_active_claim_exists")), "an incompatible active claim exists", {}

    @staticmethod
    def _stale_revision(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("requested_expected_revision") != o.get("observed_current_revision"), "expected source revision is stale", {}

    @staticmethod
    def _illegal_transition(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("declared_edge_exists") is False, "requested edge is not declared", {}

    @staticmethod
    def _missing_authorization(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("required_flag_missing_or_false") is True, "required authorization flag is absent", {}

    @staticmethod
    def _role_violation(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("owner_or_delegation_match") is False, "actor is not the declared writer owner", {}

    @staticmethod
    def _required_gate_missing(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return o.get("any_required_gate_unsatisfied") is True, "one or more required gates are unsatisfied", {}

    @staticmethod
    def _semantic_authority(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("ranking_requires_interpretation_of_intended_meaning")), "authority meaning requires semantic review", {}

    @staticmethod
    def _semantic_scope(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("material_rescope_cannot_be_determined_from_machine_fields")), "scope change is semantically ambiguous", {}

    @staticmethod
    def _semantic_requirement(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("apparent_conflict_requires_semantic_interpretation")), "requirements conflict beyond machine precedence", {}

    @staticmethod
    def _semantic_acceptance(o: Mapping[str, Any]) -> tuple[bool, str, Mapping[str, bool]]:
        return bool(o.get("adequacy_correctness_or_value_judgment_is_intentionally_nonmechanical")), "acceptance requires a non-mechanical judgment", {}


def detect_condition(condition_code: str, observations: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return ConditionDetector().detect(condition_code, observations)

