"""Adaptive hints H0: authored-hint reveals as ``help_assists`` rows.

The practice screen reveals an item's authored hints itself and sends the
count at submit (``hints_used``); before H0 nothing recorded when each hint
was shown, or on what work (spec_adaptive_hints_v1 §3.2). H0 records each
reveal (``practice.record_hint_reveal``) under the client's stable submission
key and attaches the rows to that submission's attempt at submit (repaired by
a retried submit or a recovery, never swept into another submission), so the
report can say how today's hints are used and what
follows (§6, §10 H0): the baseline the adaptive kinds are compared with.

Telemetry only (§9, H0's authored-reveal rows): nothing here changes
``hints_used``, ``primed``, reveal events, evidence, FSRS, certification,
scheduling or grading, and nothing that computes them reads these rows.
``hints.telemetry_enabled = false`` writes nothing at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
from typing import Any

from learnloop.clock import SystemClock, parse_utc
from learnloop.db.stores import help_assists as store
from learnloop.ids import new_ulid
from learnloop.vault.hashes import practice_item_hash

#: The level an authored hint is recorded at: §4.2's table puts the kind
#: ``authored`` at level 3 (the ladder's "a hint": help that is not worked).
AUTHORED_LEVEL = 3
#: How far ahead of the sidecar's clock a client's reveal time may be before
#: it is not believed (a clock-skew allowance for display timing, not a rule).
_CLIENT_CLOCK_AHEAD = timedelta(seconds=60)


@dataclass(frozen=True)
class RevealRecord:
    recorded: bool
    reason: str | None = None
    assist_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"recorded": self.recorded, "reason": self.reason, "assist_id": self.assist_id}


def telemetry_enabled(config: Any) -> bool:
    return bool(config.hints.telemetry_enabled)


def work_digest(work_md: str) -> tuple[str, int]:
    """The draft's sha256 and length: the row keeps these, never the text."""

    return hashlib.sha256(work_md.encode("utf-8")).hexdigest(), len(work_md)


def _iso_ms(instant: datetime) -> str:
    return instant.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def reveal_instant(client_value: str | None, *, now: datetime) -> str:
    """When the hint was shown: the client's press time (the sidecar answers
    one request at a time, so a reveal sent while another call runs would be
    stamped late), unless it is missing, malformed or ahead of the sidecar's
    clock; then the sidecar's own time."""

    if client_value:
        try:
            parsed = parse_utc(client_value)
        except ValueError:
            parsed = None
        if parsed is not None and parsed <= now + _CLIENT_CLOCK_AHEAD:
            return _iso_ms(parsed)
    return _iso_ms(now)


def record_authored_reveal(
    repository: Any,
    *,
    item: Any,
    session_id: str,
    submission_id: str,
    authored_index: int,
    work_md: str,
    revealed_at: str | None = None,
    now: datetime | None = None,
) -> RevealRecord:
    """One ``help_assists`` row for an authored hint the practice screen showed."""

    current = now or SystemClock().now()
    shown_at = reveal_instant(revealed_at, now=current)
    work_hash, work_chars = work_digest(work_md)
    assist_id = "ha_" + new_ulid()
    row = {
        "id": assist_id,
        "surface": "practice",
        "assist_kind": "hint",
        "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item),
        "practice_session_id": session_id,
        "submission_id": submission_id,
        "hint_kind": "authored",
        "level": AUTHORED_LEVEL,
        "authored_index": int(authored_index),
        "work_hash": work_hash,
        "work_chars": work_chars,
        "chooser": "none",
        "shown": 1,
        "counted_by": "client",
        "requested_at": shown_at,
        "shown_at": shown_at,
    }
    with repository.connection() as connection:
        store.insert_assist(connection, row)
    return RevealRecord(recorded=True, assist_id=assist_id)


def stamp_submission(
    repository: Any,
    *,
    submission_id: str,
    practice_item_id: str,
    latency_seconds: float | None = None,
    now: datetime | None = None,
) -> str:
    """When the submission reached the sidecar, before any grading (the end of
    "hint shown -> submit"; ``practice_attempts.created_at`` is stamped after
    the grader), with the open-to-submit latency the same submission sent.
    Written together on the submission's unattached rows at once, so a grading
    fallback answered later keeps both (its retry sends a later latency);
    returned for the attach."""

    submitted_at = _iso_ms((now or SystemClock().now()))
    with repository.connection() as connection:
        store.stamp_submitted(
            connection, submission_id=submission_id, practice_item_id=practice_item_id, submitted_at=submitted_at,
            latency_seconds=latency_seconds,
        )
    return submitted_at


def attach_reveals_to_attempt(
    repository: Any,
    *,
    submission_id: str,
    practice_item_id: str,
    attempt_id: str,
    submitted_at: str | None = None,
    latency_seconds: float | None = None,
) -> int:
    """Fill ``attempt_id`` on the rows recorded under the submission key (and
    the submit time with its latency where the stamp was not made)."""

    with repository.connection() as connection:
        return store.attach_submission(
            connection,
            submission_id=submission_id,
            practice_item_id=practice_item_id,
            attempt_id=attempt_id,
            submitted_at=submitted_at,
            latency_seconds=latency_seconds,
        )


__all__ = [
    "AUTHORED_LEVEL",
    "RevealRecord",
    "attach_reveals_to_attempt",
    "record_authored_reveal",
    "reveal_instant",
    "stamp_submission",
    "telemetry_enabled",
    "work_digest",
]
