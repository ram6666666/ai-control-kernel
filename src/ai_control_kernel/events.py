"""Immutable event validation and bounded local materialization."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping, Protocol, Sequence

from .canonical import canonical_json_bytes, sha256_bytes


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def validate_event(event: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("event_id", "event_type", "payload", "source_ref", "predecessor_ref"):
        if key not in event:
            errors.append(f"missing {key}")
    if not isinstance(event.get("event_id"), str) or not event.get("event_id"):
        errors.append("event_id must be a non-empty string")
    if not isinstance(event.get("payload"), Mapping):
        errors.append("payload must be an object")
    return errors


def materialize_events(events: Iterable[Mapping[str, Any]], initial_state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Replay immutable events in supplied order and return a derived snapshot."""

    state = dict(initial_state or {})
    seen: set[str] = set()
    last_id: str | None = None
    evidence: list[Mapping[str, Any]] = []
    for event in events:
        errors = validate_event(event)
        if errors:
            raise ValueError("invalid immutable event: " + ", ".join(errors))
        event_id = str(event["event_id"])
        if event_id in seen:
            raise ValueError(f"duplicate immutable event: {event_id}")
        predecessor = event.get("predecessor_ref")
        if predecessor not in (None, last_id):
            raise ValueError("event predecessor does not match prior event")
        payload = dict(_map(event.get("payload")))
        patch = _map(payload.get("state")) if isinstance(payload.get("state"), Mapping) else payload
        state.update(patch)
        seen.add(event_id)
        last_id = event_id
        source = event.get("source_ref")
        if isinstance(source, Mapping):
            evidence.append(source)
    canonical = canonical_json_bytes(state)
    return {"state": state, "last_event_id": last_id, "event_count": len(seen), "revision": sha256_bytes(canonical), "evidence": evidence}


class EventSource(Protocol):
    def list_events(self, event_root: str, after_revision: str | None = None) -> list[Mapping[str, Any]]: ...


@dataclass
class ImmutableEventReader:
    """In-memory event port used by fixtures and adapter contract tests."""

    events: tuple[Mapping[str, Any], ...]

    def __init__(self, events: Sequence[Mapping[str, Any]]) -> None:
        self.events = tuple(dict(event) for event in events)

    def list_events(self, event_root: str = "", after_revision: str | None = None) -> list[Mapping[str, Any]]:
        del event_root
        if after_revision is None:
            return [dict(event) for event in self.events]
        result: list[Mapping[str, Any]] = []
        found = False
        for event in self.events:
            if found:
                result.append(dict(event))
            if event.get("event_id") == after_revision:
                found = True
        return result

