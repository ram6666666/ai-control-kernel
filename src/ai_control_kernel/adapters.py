"""Provider-neutral local adapters for the P01 fixture boundary."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, BinaryIO, Mapping, Sequence

import yaml  # type: ignore[import-untyped]

from .canonical import canonical_json_bytes, sha256_stream


def _safe_path(root: Path, locator: str) -> Path:
    candidate = (root / locator).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path escapes configured root") from exc
    return candidate


@dataclass
class FilesystemControlSourceReader:
    root: Path

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def read_source(self, locator: str) -> dict[str, Any]:
        path = _safe_path(self.root, locator)
        raw = path.read_bytes()
        source_type = "OTHER"
        if path.suffix.lower() in {".yaml", ".yml"}:
            content = yaml.safe_load(raw.decode("utf-8"))
        elif path.suffix.lower() == ".json":
            content = json.loads(raw.decode("utf-8"))
        else:
            content = raw.decode("utf-8")
        source_ref = {"source_type": source_type, "locator": locator, "revision": None, "content_hash": None, "observed_at": None, "authority_class": "EVIDENCE"}
        with path.open("rb") as handle:
            observed, _ = sha256_stream(handle)
        return {"content": content, "source_ref": source_ref, "integrity": {"status": "VERIFIED", "algorithm": "SHA256", "expected": None, "observed": observed, "source": source_ref}}


@dataclass
class FilesystemArtifactReader:
    root: Path

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def open_bytes(self, locator: str) -> BinaryIO:
        path = _safe_path(self.root, locator)
        return path.open("rb")

    def read_identity(self, locator: str) -> dict[str, Any]:
        path = _safe_path(self.root, locator)
        with path.open("rb") as handle:
            digest, size = sha256_stream(handle)
        source_ref = {"source_type": "ARTIFACT_RECORD", "locator": locator, "revision": None, "content_hash": digest, "observed_at": None, "authority_class": "EVIDENCE"}
        return {"locator": locator, "byte_size": size, "sha256": digest, "provider_revision": None, "source_ref": source_ref, "availability": "AVAILABLE"}


@dataclass(frozen=True)
class FixtureRuntimeObservationSource:
    observations: Mapping[str, Mapping[str, Any]]

    def observe_runtime(self, target_id: str) -> Mapping[str, Any]:
        return dict(self.observations.get(target_id, {"target_id": target_id, "observation_type": "UNAVAILABLE", "values": {}}))


@dataclass(frozen=True)
class FixtureExecutorCapabilitySource:
    records: Mapping[str, Mapping[str, Any]]

    def get_capabilities(self, executor_id: str) -> Mapping[str, Any]:
        return dict(self.records.get(executor_id, {"executor_id": executor_id, "capabilities": [], "constraints": {}, "provider_metadata_evidence": []}))


@dataclass
class FilesystemShadowOutputSink:
    root: Path

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write_result(self, result_type: str, payload: Mapping[str, Any], source_revisions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        locator = f"{result_type}.json"
        path = _safe_path(self.root, locator)
        path.write_bytes(canonical_json_bytes(payload))
        source_ref = {"source_type": "DERIVED_VIEW", "locator": str(path), "revision": None, "content_hash": None, "observed_at": None, "authority_class": "DERIVED"}
        return {"result_locator": str(path), "revision": None, "source_ref": source_ref, "source_revisions": list(source_revisions)}

