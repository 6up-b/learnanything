"""The doctrine: the teacher's policy, a versioned prompt set (spec_teacher_v1 §10).

Written from scratch in our own words (LearnHarness's ideas, never its text: it is
AGPL-3.0 and this repository is Apache-2.0). Behaviour changes by editing the
doctrine, not by adding code. The version and the text's hash are recorded on
every lesson and receipt.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

#: The doctrine in force (a new directory is a new version: a different forecaster for §12.2's pool).
DOCTRINE_VERSION = "teacher_doctrine_v1"
_DIRECTORY = Path(__file__).resolve().parent / "doctrine" / "v1"


@lru_cache(maxsize=1)
def doctrine_text() -> str:
    """The doctrine's files in order, joined."""

    parts = [path.read_text(encoding="utf-8").strip() for path in sorted(_DIRECTORY.glob("*.md"))]
    if not parts:  # pragma: no cover - a packaging error
        raise RuntimeError(f"the teacher doctrine is missing: {_DIRECTORY}")
    return "\n\n".join(parts) + "\n"


def doctrine_hash() -> str:
    return hashlib.sha256(doctrine_text().encode("utf-8")).hexdigest()


def doctrine_identity() -> dict[str, str]:
    return {"version": DOCTRINE_VERSION, "sha256": doctrine_hash()}


__all__ = ["DOCTRINE_VERSION", "doctrine_hash", "doctrine_identity", "doctrine_text"]
