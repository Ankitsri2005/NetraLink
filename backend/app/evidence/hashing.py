from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_digest(data: str | bytes) -> str:
    """Compute SHA-256 hex digest for given data."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_evidence_payload(
    source_type: str,
    record_id: str,
    payload: dict[str, Any] | str,
    previous_hash: str | None = None,
) -> str:
    """
    Generate an immutable evidence block hash.
    Chains with previous_hash for verifiable audit integrity.
    """
    serialized_payload = (
        json.dumps(payload, sort_keys=True)
        if isinstance(payload, dict)
        else str(payload)
    )
    block_data = f"{source_type}:{record_id}:{serialized_payload}:{previous_hash or 'GENESIS'}"
    return sha256_digest(block_data)


def verify_evidence_chain(
    current_hash: str,
    source_type: str,
    record_id: str,
    payload: dict[str, Any] | str,
    previous_hash: str | None = None,
) -> bool:
    """Verify evidence integrity against expected SHA-256 hash."""
    expected = hash_evidence_payload(source_type, record_id, payload, previous_hash)
    return current_hash.lower() == expected.lower()
