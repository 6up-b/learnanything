"""What other test files use from ``tests/test_roles_switch_off.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
VOLATILE = {"createdAt", "created_at", "timingsMs", "timings_ms", "latencyMs", "latency_ms", "elapsedMs",
            "elapsed_ms", "durationMs", "duration_ms", "started_at", "finished_at",
            # A hash over the targets' refs, which carry a fresh episode ULID per run.
            "targets_key", "targetsKey"}
#: Ids hashed from a ULID-bearing target ref (a fresh episode per run): replaced
#: by their order of appearance, as ULIDs are.
_HASHED = re.compile(r"plink_[0-9a-f]{32}")
#: A cue target's state key (24 hex digits): a hash over its episode's state,
#: which carries the run's clock; replaced by order of appearance.
_STATE = re.compile(r"\b[0-9a-f]{24}\b")


def _normalized(value: Any) -> Any:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    seen: dict[str, str] = {}

    def swap(match: re.Match[str]) -> str:
        return seen.setdefault(match.group(0), f"<ULID{len(seen)}>")

    text = _ULID.sub(swap, text)
    links: dict[str, str] = {}
    text = _HASHED.sub(lambda match: links.setdefault(match.group(0), f"<LINK{len(links)}>"), text)
    states: dict[str, str] = {}
    text = _STATE.sub(lambda match: states.setdefault(match.group(0), f"<STATE{len(states)}>"), text)
    return json.loads(text)


def _without(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without(item) for key, item in value.items() if key not in VOLATILE}
    if isinstance(value, list):
        return [_without(item) for item in value]
    return value


def _sha(texts: list[str]) -> list[str]:
    return [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts]
