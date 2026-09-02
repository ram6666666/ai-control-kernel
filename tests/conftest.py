from pathlib import Path

import pytest

from ai_control_kernel.predicates import PredicateRegistry
from ai_control_kernel.schema import SchemaRegistry, load_yaml


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def registry(repo_root: Path) -> SchemaRegistry:
    return SchemaRegistry(repo_root)


@pytest.fixture
def predicate_registry(registry: SchemaRegistry) -> PredicateRegistry:
    return PredicateRegistry(registry.spec("predicate_registry.yaml"))


@pytest.fixture
def policy(registry: SchemaRegistry):
    return registry.spec("permission_policy.yaml")


@pytest.fixture
def state_machine(registry: SchemaRegistry):
    return registry.spec("state_machine.yaml")


@pytest.fixture
def status_registry(registry: SchemaRegistry):
    return registry.spec("status_normalization.yaml")

