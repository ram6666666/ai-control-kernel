from pathlib import Path

import pytest

from ai_control_kernel.adapters import FilesystemArtifactReader, FilesystemControlSourceReader, FilesystemShadowOutputSink
from ai_control_kernel.events import ImmutableEventReader, materialize_events, validate_event


def _event(event_id: str, predecessor: str | None, value: str) -> dict:
    return {"event_id": event_id, "event_type": "STATE", "payload": {"state": {"status": value}}, "source_ref": {"source_type": "IMMUTABLE_EVENT", "locator": event_id, "authority_class": "EVIDENCE"}, "predecessor_ref": predecessor}


def test_event_replay_and_conflict() -> None:
    events = [_event("e1", None, "READY"), _event("e2", "e1", "RUNNING")]
    assert materialize_events(events)["state"]["status"] == "RUNNING"
    assert ImmutableEventReader(events).list_events(after_revision="e1")[0]["event_id"] == "e2"
    with pytest.raises(ValueError):
        materialize_events([_event("e1", None, "READY"), _event("e1", "e1", "RUNNING")])
    assert validate_event({"event_id": "x"})


def test_filesystem_adapters_are_root_bounded(tmp_path: Path) -> None:
    (tmp_path / "input.json").write_text('{"value": 1}', encoding="utf-8")
    (tmp_path / "typed.yaml").write_text("when: 2026-01-01\n", encoding="utf-8")
    reader = FilesystemControlSourceReader(tmp_path)
    assert reader.read_source("input.json")["content"]["value"] == 1
    assert reader.read_source("typed.yaml")["content"]["when"] == "2026-01-01"
    artifact = FilesystemArtifactReader(tmp_path)
    assert artifact.read_identity("input.json")["byte_size"] > 0
    with pytest.raises(ValueError):
        artifact.read_identity("../outside")
    sink = FilesystemShadowOutputSink(tmp_path / "shadow")
    receipt = sink.write_result("state", {"ok": True}, [])
    assert Path(receipt["result_locator"]).exists()
