import re
from pathlib import Path

from ai_control_kernel.adapters import FixtureExecutorCapabilitySource, FixtureRuntimeObservationSource


def test_core_source_has_no_provider_or_dynamic_execution_imports() -> None:
    root = Path(__file__).parents[1]
    source = "\n".join(path.read_text(encoding="utf-8") for path in (root / "src").rglob("*.py"))
    forbidden = ("import boto3", "import requests", "import httpx", "import temporalio", "import langgraph", "import openai", "import sqlalchemy", "eval(", "exec(")
    assert not any(token in source for token in forbidden)
    assert "yaml.safe_load" in source
    assert "yaml.load(" not in source


def test_public_fixtures_are_sanitized_and_adapters_emit_observations_only() -> None:
    root = Path(__file__).parents[1]
    fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in (root / "tests" / "fixtures").rglob("*") if path.is_file())
    secret_patterns = (r"ghp_[A-Za-z0-9_]+", r"github_pat_[A-Za-z0-9_]+", r"-----BEGIN .*PRIVATE KEY-----", r"bearer\s+[A-Za-z0-9._-]+", r"signed[_ -]?url")
    assert not any(re.search(pattern, fixture_text, re.IGNORECASE) for pattern in secret_patterns)
    observation = FixtureRuntimeObservationSource({}).observe_runtime("target")
    capability = FixtureExecutorCapabilitySource({}).get_capabilities("executor")
    assert observation["observation_type"] == "UNAVAILABLE"
    assert capability["executor_id"] == "executor"
    assert "result" not in observation and "decision" not in capability
