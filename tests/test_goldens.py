from pathlib import Path

import yaml

from ai_control_kernel.conditions import ConditionDetector
from ai_control_kernel.policy import PermissionEvaluator
from ai_control_kernel.schema import load_yaml


def test_all_public_fixtures_exist_and_expected_are_stable() -> None:
    root = Path(__file__).parent / "fixtures"
    expected_ids = {"F01", "F02", "F03A", "F03B", "F04", "F05", "F06", "F07", "F08", "F09", "F10"}
    assert {path.name for path in root.iterdir() if path.is_dir()} == expected_ids
    for fixture in sorted(expected_ids):
        data = load_yaml(root / fixture / "fixture.yaml")
        expected = (root / fixture / "expected" / "transition_decision.json").read_text(encoding="utf-8")
        assert data["fixture_id"] == fixture and fixture in expected


def test_f01_f10_condition_and_policy_shapes(policy, predicate_registry) -> None:
    evaluator = PermissionEvaluator(policy, predicate_registry)
    amber = evaluator.evaluate("READ_DIAGNOSE", ["A_STALE_COPIED_METADATA"], context={"predicate_evidence": []})
    red = evaluator.evaluate("EXECUTE_AND_CHECKPOINT", ["R_POLICY_FINGERPRINT_MISMATCH"], context={"predicate_evidence": []})
    assert amber["result"] == "ALLOW" and amber["risk_mode"] == "AMBER"
    assert red["result"] == "DENY" and red["risk_mode"] == "RED"
    assert ConditionDetector().detect("A_STALE_DERIVED_VIEW", {"authoritative_source_revisions": {"x": "2"}, "derived_view_source_revisions": {"x": "1"}})["observed"]

