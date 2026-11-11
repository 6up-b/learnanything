"""What other test files use from ``tests/test_data_capture_successor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import re

from tests.router_mixture_helpers import rows


#: What differs by construction between two runs: fresh ids, and the version label and its hashes.
_VOLATILE = {"id", "snapshot_hash", "algorithm_version", "seed", "card_hash", "created_at"}


def _canonical_rows(env):
    def scrub(value):
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items() if key not in _VOLATILE and "hash" not in key}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, str):
            return re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", value)
        return value

    return [scrub({key: value for key, value in row.items()}) for row in rows(env)]


def _blocks(record):
    return [(block.lane, block.action, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]
