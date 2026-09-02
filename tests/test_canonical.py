from io import BytesIO

import pytest

from ai_control_kernel.canonical import canonical_json, canonical_json_bytes, normalize_timestamp, sha256_bytes, sha256_stream


def test_canonical_is_sorted_and_repeatable() -> None:
    value = {"z": 1, "a": [True, "é"]}
    assert canonical_json(value) == '{"a":[true,"é"],"z":1}'
    assert canonical_json_bytes(value) == canonical_json_bytes(value)


def test_canonical_rejects_nan() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes(float("nan"))


def test_timestamp_and_binary_hash() -> None:
    assert normalize_timestamp("2026-01-01T01:00:00+01:00") == "2026-01-01T00:00:00.000000Z"
    digest, size = sha256_stream(BytesIO(b"abc"))
    assert digest == sha256_bytes(b"abc")
    assert size == 3

