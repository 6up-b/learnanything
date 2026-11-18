"""Stable content identities shared by diagnosis writers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def content_id(prefix: str, value: Any) -> str:
    """Identify content so new rows deduplicate against stored rows.

    The serialized bytes are pinned by tests/test_identity_pins.py because stored
    ids and newly computed ids must compare equal for the same content.
    """

    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"

