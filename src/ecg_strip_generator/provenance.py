"""Canonical JSON and checksums, without timestamps or local paths."""

import hashlib
import json
from typing import Any

from ecg_strip_generator.models import Signal


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def signal_digest(signal: Signal) -> str:
    return sha256(canonical_json(signal.model_dump(mode="json")))
