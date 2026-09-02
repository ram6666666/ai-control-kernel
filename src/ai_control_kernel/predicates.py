"""Closed, deterministic predicate registry dispatch.

Predicate names are loaded from the frozen registry, but evaluator dispatch is
an explicit table.  No expression, Python code, or provider callback is ever
evaluated from a policy document.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True)
class PredicateResult:
    predicate_id: str
    passed: bool
    evidence: tuple[Mapping[str, Any], ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "predicate_id": self.predicate_id,
            "result": "PASS" if self.passed else "FAIL",
            "evidence": [dict(item) for item in self.evidence],
            "reason": self.reason,
        }


def _evidence(context: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    supplied = context.get("predicate_evidence", context.get("evidence", []))
    if isinstance(supplied, Mapping):
        supplied = [supplied]
    if isinstance(supplied, Sequence) and not isinstance(supplied, (str, bytes)):
        return tuple(item for item in supplied if isinstance(item, Mapping))
    return ()


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: object) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _equal_maps(left: object, right: object) -> bool:
    return isinstance(left, Mapping) and isinstance(right, Mapping) and dict(left) == dict(right)


class PredicateRegistry:
    """Evaluate only the 15 P01 predicate IDs from the frozen registry."""

    _EVALUATORS: dict[str, Callable[[Mapping[str, Any]], bool]] = {}

    def __init__(self, registry: Mapping[str, Any]) -> None:
        predicates = registry.get("predicates", {})
        self.registry = predicates if isinstance(predicates, Mapping) else {}
        self._EVALUATORS = {
            "check_authority_unique": self._authority_unique,
            "check_required_integrity": self._required_integrity,
            "check_writer_owner": self._writer_owner,
            "check_source_revision_current": self._source_current,
            "check_permission_intersection": self._permission_intersection,
            "check_required_gates": self._required_gates,
            "check_claim_conflict_absent": self._claim_conflict_absent,
            "check_recovery_no_content_advance": self._recovery_no_content_advance,
            "check_recovery_targets_observed_defect": self._recovery_target_observed,
            "check_shadow_input_trust": self._shadow_input_trust,
            "check_noncanonical_output_explicit": self._noncanonical_explicit,
            "check_audit_input_integrity": self._audit_input_exact,
            "check_promotion_amber_relevance": self._promotion_amber_irrelevant,
            "check_recovery_role": self._recovery_role,
            "check_policy_reconciliation_scope": self._policy_reconciliation_scope,
        }

    def evaluate(self, predicate_id: str, context: Mapping[str, Any] | None = None) -> PredicateResult:
        ctx = context or {}
        definition = self.registry.get(predicate_id)
        if not isinstance(definition, Mapping):
            return PredicateResult(predicate_id, False, _evidence(ctx), "unknown predicate ID")
        evaluator_name = definition.get("evaluator")
        evaluator = self._EVALUATORS.get(str(evaluator_name))
        if evaluator is None:
            return PredicateResult(predicate_id, False, _evidence(ctx), "unimplemented predicate evaluator")
        try:
            passed = bool(evaluator(ctx))
        except (KeyError, TypeError, ValueError):
            passed = False
        return PredicateResult(predicate_id, passed, _evidence(ctx), "predicate passed" if passed else "predicate failed")

    def evaluate_many(self, predicate_ids: Sequence[str], context: Mapping[str, Any] | None = None) -> list[PredicateResult]:
        return [self.evaluate(predicate_id, context) for predicate_id in predicate_ids]

    @staticmethod
    def _authority_unique(context: Mapping[str, Any]) -> bool:
        state = _as_mapping(context.get("effective_state"))
        health = _as_mapping(state.get("health"))
        value = context.get("authority_resolution", health.get("authority_resolution"))
        return bool(value == "UNIQUE")

    @staticmethod
    def _required_integrity(context: Mapping[str, Any]) -> bool:
        verdicts = _as_list(context.get("operation_required_integrity_verdicts", context.get("integrity_verdicts", [])))
        return all(_as_mapping(verdict).get("status") in {"VERIFIED", "NOT_APPLICABLE"} for verdict in verdicts)

    @staticmethod
    def _writer_owner(context: Mapping[str, Any]) -> bool:
        actor = context.get("actor_role")
        target = context.get("target_state_class")
        owners = _as_mapping(context.get("single_writer_map"))
        if owners.get(str(target)) == actor:
            return True
        for delegation in _as_list(context.get("delegations")):
            item = _as_mapping(delegation)
            if item.get("actor_role") == actor and item.get("owner_class") == owners.get(str(target)) and item.get("valid", True):
                return True
        return False

    @staticmethod
    def _source_current(context: Mapping[str, Any]) -> bool:
        return _equal_maps(context.get("expected_revisions"), context.get("observed_current_revisions"))

    @staticmethod
    def _permission_intersection(context: Mapping[str, Any]) -> bool:
        parent = set(str(x) for x in _as_list(context.get("parent_permissions")))
        proposed = set(str(x) for x in _as_list(context.get("proposed_permissions")))
        restrictions = context.get("local_restrictions")
        if isinstance(restrictions, Mapping):
            forbidden = set(str(x) for x in _as_list(restrictions.get("forbidden_actions")))
        else:
            forbidden = set(str(x) for x in _as_list(restrictions))
        return proposed <= (parent - forbidden)

    @staticmethod
    def _required_gates(context: Mapping[str, Any]) -> bool:
        spec = context.get("operation_gate_spec", context.get("required_gates", []))
        evidence = context.get("available_evidence", {})
        if isinstance(spec, Mapping):
            required = spec.get("required", spec.get("gates", []))
        else:
            required = spec
        if not isinstance(required, Sequence) or isinstance(required, (str, bytes)):
            return bool(required) is False
        if isinstance(evidence, Mapping):
            return all(bool(evidence.get(str(gate), False)) for gate in required)
        available = {str(item) for item in _as_list(evidence)}
        return all(str(gate) in available for gate in required)

    @staticmethod
    def _claim_conflict_absent(context: Mapping[str, Any]) -> bool:
        proposed = _as_mapping(context.get("proposed_claim"))
        key = proposed.get("idempotency_key", context.get("idempotency_key"))
        claim_id = proposed.get("claim_id")
        record = _as_mapping(context.get("idempotency_record"))
        if record and record.get("idempotency_key") == key:
            return record.get("claim_id") == claim_id and record.get("payload_hash") == proposed.get("payload_hash", record.get("payload_hash"))
        for claim in _as_list(context.get("active_claims")):
            item = _as_mapping(claim)
            if item.get("execution_unit_id") != proposed.get("execution_unit_id"):
                continue
            same = item.get("claim_id") == claim_id and item.get("claimant") == proposed.get("claimant") and item.get("lease_revision") == proposed.get("lease_revision")
            if not same:
                return False
        return True

    @staticmethod
    def _recovery_no_content_advance(context: Mapping[str, Any]) -> bool:
        mutations = _as_mapping(context.get("requested_mutations"))
        forbidden = {"status", "target_status", "artifact", "artifact_id", "content", "checkpoint", "result", "objective"}
        return not any(key in forbidden for key in mutations)

    @staticmethod
    def _recovery_target_observed(context: Mapping[str, Any]) -> bool:
        requested = context.get("requested_repair_condition_code")
        observed = {str(item) for item in _as_list(context.get("observed_condition_codes"))}
        return isinstance(requested, str) and requested in observed

    @staticmethod
    def _shadow_input_trust(context: Mapping[str, Any]) -> bool:
        for item in _as_list(context.get("shadow_inputs")):
            record = _as_mapping(item)
            if record.get("treated_as_authoritative") and record.get("authority_class") in {"EVIDENCE", "DERIVED", "UNTRUSTED"}:
                return False
        return True

    @staticmethod
    def _noncanonical_explicit(context: Mapping[str, Any]) -> bool:
        return context.get("requested_output_authority_class") == "NONCANONICAL"

    @staticmethod
    def _audit_input_exact(context: Mapping[str, Any]) -> bool:
        gate = _as_mapping(context.get("audit_gate"))
        if gate.get("exact_artifact_required") is False:
            return True
        identity = _as_mapping(context.get("audit_input_identity"))
        retrieval = _as_mapping(context.get("retrieval_observation"))
        return identity.get("status") == "VERIFIED" and retrieval.get("independent_retrieval_verified") is True

    @staticmethod
    def _promotion_amber_irrelevant(context: Mapping[str, Any]) -> bool:
        observed = {str(item) for item in _as_list(context.get("observed_amber_conditions"))}
        mapping = _as_mapping(context.get("promotion_gate_relevance_map"))
        required = {str(item) for item in _as_list(context.get("required_promotion_facets"))}
        return not any(required.intersection({str(x) for x in _as_list(mapping.get(code))}) for code in observed)

    @staticmethod
    def _recovery_role(context: Mapping[str, Any]) -> bool:
        actor = context.get("actor_role")
        owner = context.get("recovery_owner_class")
        return actor == owner or any(_as_mapping(item).get("actor_role") == actor and _as_mapping(item).get("owner_class") == owner and _as_mapping(item).get("valid", True) for item in _as_list(context.get("delegations")))

    @staticmethod
    def _policy_reconciliation_scope(context: Mapping[str, Any]) -> bool:
        flags = context.get("semantic_change_flags", [])
        repair = _as_mapping(context.get("requested_policy_repair"))
        return not any(bool(flag) for flag in _as_list(flags)) and repair.get("mechanically_decidable", True) is True

