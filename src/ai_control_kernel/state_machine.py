"""Explicit normalized lifecycle transition validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .predicates import PredicateRegistry


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


@dataclass(frozen=True)
class TransitionValidation:
    allowed: bool
    rule_id: str | None
    operation_class: str | None
    writer_owner: str | None
    required_predicates: tuple[str, ...]
    checks: tuple[dict[str, Any], ...]
    evidence_requirements: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "rule_id": self.rule_id,
            "operation_class": self.operation_class,
            "writer_owner": self.writer_owner,
            "required_predicates": list(self.required_predicates),
            "checks": [dict(check) for check in self.checks],
            "evidence_requirements": list(self.evidence_requirements),
            "reason": self.reason,
        }


class TransitionValidator:
    def __init__(self, state_machine: Mapping[str, Any], predicates: PredicateRegistry | None = None) -> None:
        self.spec = state_machine
        self.predicates = predicates or PredicateRegistry({})
        self.states = set(str(item) for item in _items(state_machine.get("normalized_states")))
        self.rules = [item for item in _items(state_machine.get("rules")) if isinstance(item, Mapping)]

    def find_rule(self, current_state: str, target_state: str) -> Mapping[str, Any] | None:
        for rule in self.rules:
            from_states = {str(rule["from"])} if "from" in rule else {str(item) for item in _items(rule.get("from_set"))}
            if current_state in from_states and str(rule.get("to")) == target_state:
                return rule
        return None

    def validate(
        self,
        current_state: str,
        target_state: str,
        *,
        operation_class: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> TransitionValidation:
        facts = dict(context or {})
        if current_state == "UNKNOWN":
            allowed_operations = set(_items(_mapping(self.spec.get("unknown_state_policy")).get("allowed_operations")))
            allowed = operation_class in allowed_operations and target_state in {"UNKNOWN", ""}
            return TransitionValidation(allowed, None, operation_class, None, (), (), (), "unknown state permits diagnosis only")
        if current_state not in self.states or target_state not in self.states:
            return TransitionValidation(False, None, operation_class, None, (), (), (), "state is not in normalized registry")
        rule = self.find_rule(current_state, target_state)
        if rule is None:
            return TransitionValidation(False, None, operation_class, None, (), (), (), "transition edge is not declared")
        declared_operation = str(rule.get("operation_class"))
        if operation_class is not None and operation_class != declared_operation:
            return TransitionValidation(False, str(rule.get("id")), declared_operation, str(rule.get("writer_owner")), (), (), (), "operation class does not match declared edge")
        predicate_ids = tuple(str(item) for item in _items(rule.get("require_predicates")))
        checks = tuple(result.as_dict() | {"check_id": result.predicate_id} for result in self.predicates.evaluate_many(predicate_ids, facts))
        predicates_pass = all(check.get("result") == "PASS" for check in checks)
        evidence_requirements = tuple(str(item) for item in _items(rule.get("evidence_requirements")))
        evidence = facts.get("evidence_requirements", facts.get("available_evidence", {}))
        evidence_pass = all(bool(_mapping(evidence).get(item, False)) for item in evidence_requirements) if isinstance(evidence, Mapping) else all(item in _items(evidence) for item in evidence_requirements)
        return TransitionValidation(predicates_pass and evidence_pass, str(rule.get("id")), declared_operation, str(rule.get("writer_owner")), predicate_ids, checks, evidence_requirements, "transition is declared and predicates/evidence pass" if predicates_pass and evidence_pass else "transition predicate or evidence requirement failed")

    def validate_transition(self, current_state: str, target_state: str, **kwargs: Any) -> dict[str, Any]:
        return self.validate(current_state, target_state, **kwargs).as_dict()
