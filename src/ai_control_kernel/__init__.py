"""AI Control Kernel v0.1 deterministic core.

The public API intentionally consists of pure functions and small adapters.  No
provider, workflow, model, database, or web framework is imported here.
"""

from .canonical import canonical_json, canonical_json_bytes, sha256_bytes, sha256_file, sha256_stream
from .capsules import CandidateCapsuleCompiler, ExecutionCapsuleCompiler, is_capsule_invalidated
from .conditions import ConditionDetector, detect_condition
from .effective_state import EffectiveStateResolver
from .events import ImmutableEventReader, materialize_events, validate_event
from .policy import PermissionEvaluator, evaluate_operation
from .predicates import PredicateRegistry, PredicateResult
from .schema import SchemaRegistry, load_yaml, validate_document
from .state_machine import TransitionValidator
from .status import StatusNormalizer, normalize_status

__all__ = [
    "CandidateCapsuleCompiler",
    "ConditionDetector",
    "EffectiveStateResolver",
    "ExecutionCapsuleCompiler",
    "ImmutableEventReader",
    "PermissionEvaluator",
    "PredicateRegistry",
    "PredicateResult",
    "SchemaRegistry",
    "StatusNormalizer",
    "TransitionValidator",
    "canonical_json",
    "canonical_json_bytes",
    "detect_condition",
    "evaluate_operation",
    "is_capsule_invalidated",
    "load_yaml",
    "materialize_events",
    "normalize_status",
    "sha256_bytes",
    "sha256_file",
    "sha256_stream",
    "validate_document",
    "validate_event",
]

__version__ = "0.1.0"

