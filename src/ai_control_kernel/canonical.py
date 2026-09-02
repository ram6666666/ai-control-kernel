"""Canonical JSON and byte-identity helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, BinaryIO, Iterable


def canonical_json_bytes(value: Any) -> bytes:
    """Return UTF-8 RFC-style canonical JSON bytes.

    ``allow_nan=False`` is deliberate: non-JSON numeric values cannot be part
    of a deterministic machine contract.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def normalize_timestamp(value: str | datetime) -> str:
    """Normalize an ISO timestamp to an explicit UTC ``Z`` form."""

    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    rendered = parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return rendered


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_stream(stream: BinaryIO, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    """Hash bytes read from a binary stream and return ``(digest, size)``."""

    digest = sha256()
    size = 0
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise TypeError("artifact streams must yield bytes")
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def sha256_file(path: str | Path, *, root: str | Path | None = None) -> tuple[str, int]:
    """Hash a file through a binary handle, optionally enforcing a root."""

    candidate = Path(path).resolve()
    if root is not None:
        root_path = Path(root).resolve()
        try:
            candidate.relative_to(root_path)
        except ValueError as exc:
            raise ValueError("path escapes configured root") from exc
    with candidate.open("rb") as handle:
        return sha256_stream(handle)


def stable_unique(values: Iterable[str]) -> list[str]:
    """Preserve first occurrence order while removing duplicate strings."""

    return list(dict.fromkeys(values))
