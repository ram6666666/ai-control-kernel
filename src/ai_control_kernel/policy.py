"""Operation-scoped permission evaluation for the frozen policy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .canonical import normalize_timestamp
from .predicates import PredicateRegistry


_RISK_ORDER = {"GREEN": 0, "AMBER": 1, "RED": 2}
_RESULT_ORDER = {"NOOP_IDEMPOTENT": 0, "ALLOW": 1, "SEMANTIC_REVIEW_REQUIRED": 2, "DENY": 3}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


class PermissionEvaluator:
    def __init__(self, policy: Mapping[str, Any], predicates: PredicateRegistry | None = None) -> None:
        self.policy = policy
        self.predicates = predicates or PredicateRegistry({})

    def evaluate(
        self,
        operation_class: str,
        condition_codes: Sequence[str] | None = None,
        *,
        context: Mapping[str, Any] | None = None,
        request_id: str = "request",
        decision_id: str = "decision",
        decided_at: str | datetime | None = None,
    ) -> dict[str, Any]:
        facts = dict(context or {})
        codes = list(dict.fromkeys(condition_codes or []))
        base_rules = _mapping(_mapping(self.policy.get("base_by_operation")).get(operation_class))
        known_operations = set(_mapping(self.policy.get("base_by_operation")))
        if operation_class not in known_operations:
            return self._decision(operation_class, "SEMANTIC_REVIEW_REQUIRED", "RED", codes, [], request_id, decision_id, decided_at, facts, semantic_questions=["operation class is not in the closed registry"])

        overrides = _mapping(self.policy.get("condition_overrides"))
        unknown = [code for code in codes if code not in overrides and code not in {"S_AUTHORITY_MEANING_AMBIGUOUS", "S_SCOPE_CHANGE_AMBIGUOUS", "S_REQUIREMENT_CONFLICT", "S_ACCEPTANCE_JUDGMENT_REQUIRED"}]
        if unknown:
            checks = [self._check("unknown_condition", False, facts, f"unknown condition code: {code}") for code in unknown]
            return self._decision(operation_class, "DENY", "RED", codes, checks, request_id, decision_id, decided_at, facts, blockers=unknown)

        semantic_codes = [code for code in codes if code.startswith("S_")]
        if semantic_codes and operation_class not in {"READ_DIAGNOSE", "DISCUSS_PLAN"}:
            questions = [f"semantic condition {code} requires authoritative review" for code in semantic_codes]
            return self._decision(operation_class, "SEMANTIC_REVIEW_REQUIRED", "RED", codes, [], request_id, decision_id, decided_at, facts, semantic_questions=questions)

        if operation_class == "CLAIM_EXECUTION_UNIT" and self._is_idempotent_replay(facts):
            return self._decision(operation_class, "NOOP_IDEMPOTENT", "GREEN", codes, [], request_id, decision_id, decided_at, facts)

        risks = ["GREEN"]
        rules: list[Mapping[str, Any]] = []
        for code in codes:
            override = _mapping(overrides.get(code))
            declared_risk = override.get("risk")
            risk = declared_risk if isinstance(declared_risk, str) and declared_risk in _RISK_ORDER else "GREEN"
            risks.append(risk)
            operation_overrides = _mapping(override.get("operation_overrides"))
            rules.append(_mapping(operation_overrides.get(operation_class)) or _mapping(base_rules.get(risk, base_rules.get("GREEN", {}))))
        risk_mode = max(risks, key=lambda item: _RISK_ORDER.get(item, 2))
        if not rules:
            rules = [_mapping(base_rules.get("GREEN", {}))]
        # A condition-specific rule is authoritative over the base rule. Multiple
        # rules are merged conservatively: one failed gate denies the operation.
        all_checks: list[dict[str, Any]] = []
        outcomes: list[str] = []
        effect_scopes: list[str] = []
        for rule in rules:
            outcome, checks = self._apply_rule(rule, facts)
            outcomes.append(outcome)
            all_checks.extend(checks)
            effect = rule.get("effect_scope")
            if isinstance(effect, str):
                effect_scopes.append(effect)
        result = max(outcomes, key=lambda item: _RESULT_ORDER.get(item, 3))
        if result == "NOOP_IDEMPOTENT" and any(item == "DENY" for item in outcomes):
            result = "DENY"
        blockers = [item.get("check_id", "predicate") for item in all_checks if item.get("result") == "FAIL"]
        warnings = [code for code in codes if code.startswith("A_")]
        if result == "DENY" and not blockers and codes:
            blockers = [code for code in codes if code.startswith("R_")]
        return self._decision(operation_class, result, risk_mode, codes, all_checks, request_id, decision_id, decided_at, facts, blockers=blockers, warnings=warnings, effect_scope=effect_scopes[0] if effect_scopes else None)

    @staticmethod
    def _is_idempotent_replay(context: Mapping[str, Any]) -> bool:
        proposed = _mapping(context.get("proposed_claim"))
        record = _mapping(context.get("idempotency_record"))
        if not proposed or not record:
            return False
        key = proposed.get("idempotency_key", context.get("idempotency_key"))
        proposed_lease = proposed.get("lease_revision", proposed.get("lease_or_expected_revision"))
        record_lease = record.get("lease_revision", record.get("lease_or_expected_revision"))
        if not all((key, proposed.get("claim_id"), proposed.get("claimant"), proposed_lease, proposed.get("payload_hash"), record.get("claim_id"), record.get("claimant"), record_lease, record.get("payload_hash"))):
            return False
        return (
            record.get("idempotency_key") == key
            and record.get("claim_id") == proposed.get("claim_id")
            and record.get("claimant") == proposed.get("claimant")
            and record_lease == proposed_lease
            and record.get("payload_hash") == proposed.get("payload_hash")
        )

    def _apply_rule(self, rule: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        if rule.get("mode") == "DIRECT":
            return str(rule.get("result", "DENY")), []
        checks: list[dict[str, Any]] = []
        passed = True
        for predicate_id in _items(rule.get("predicates")):
            result = self.predicates.evaluate(str(predicate_id), context)
            checks.append(result.as_dict() | {"check_id": result.predicate_id})
            passed = passed and result.passed
        return (str(rule.get("on_pass", "ALLOW")) if passed else "DENY"), checks

    @staticmethod
    def _check(check_id: str, passed: bool, context: Mapping[str, Any], reason: str) -> dict[str, Any]:
        evidence = context.get("predicate_evidence", context.get("evidence", []))
        refs = list(evidence) if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes)) else []
        return {"check_id": check_id, "result": "PASS" if passed else "FAIL", "evidence": refs, "reason": reason}

    def _decision(
        self,
        operation_class: str,
        result: str,
        risk_mode: str,
        observed: list[str],
        checks: list[dict[str, Any]],
        request_id: str,
        decision_id: str,
        decided_at: str | datetime | None,
        context: Mapping[str, Any],
        *,
        blockers: list[str] | None = None,
        warnings: list[str] | None = None,
        semantic_questions: list[str] | None = None,
        effect_scope: str | None = None,
    ) -> dict[str, Any]:
        at = normalize_timestamp(decided_at or datetime.now(timezone.utc))
        allowed = result in {"ALLOW", "NOOP_IDEMPOTENT"}
        target = context.get("target_writer_role", context.get("writer_owner"))
        expected = context.get("expected_current_revision")
        return {
            "schema_version": "ack.transition_decision.v0.1",
            "decision_id": decision_id,
            "request_id": request_id,
            "decided_at": at,
            "operation_class": operation_class,
            "result": result,
            "risk_mode": risk_mode,
            "observed_condition_codes": list(dict.fromkeys(observed)),
            "blocking_condition_codes": list(dict.fromkeys(blockers or [])),
            "nonblocking_warning_codes": list(dict.fromkeys(warnings or [])),
            "checks": checks,
            "conflicts": context.get("conflicts", []),
            "missing_requirements": context.get("missing_requirements", []),
            "semantic_questions": semantic_questions or [],
            "write_plan": {"allowed": allowed, "required_event_type": context.get("required_event_type") if allowed else None, "target_writer_role": target if allowed else None, "expected_current_revision": expected if allowed else None},
        }


def evaluate_operation(
    policy: Mapping[str, Any],
    operation_class: str,
    condition_codes: Sequence[str] | None = None,
    *,
    context: Mapping[str, Any] | None = None,
    predicates: PredicateRegistry | None = None,
) -> dict[str, Any]:
    return PermissionEvaluator(policy, predicates).evaluate(operation_class, condition_codes, context=context)

