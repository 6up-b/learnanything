"""Work claims of the shared "same or different?" judge (Slice 2 T1, migration 176).

One row per question a producer is asked: (task, producer, prompt version,
input). The judge claims the row in a short write transaction BEFORE it calls
the model, calls outside any transaction, and appends its verdict only while
its lease epoch still holds (completion fencing). A live lease held by another
worker means "someone is already paying for this": the pair is skipped. An
expired lease (a crashed worker) is re-claimed with a new epoch, so the late
worker's verdict is fenced out instead of landing as a second, conflicting one.

Every function runs inside the caller's transaction; none commits.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from typing import Any

from learnloop.clock import parse_utc

CLAIMED, HELD, DONE = "claimed", "held", "done"


def _row(connection: sqlite3.Connection, claim_key: str) -> dict[str, Any] | None:
    cursor = connection.execute(
        "SELECT state, lease_owner, lease_expires_at, lease_epoch, judgment_id FROM judgment_work_claims "
        "WHERE claim_key = ?",
        (claim_key,),
    )
    raw = cursor.fetchone()
    if raw is None:
        return None
    return dict(zip([column[0] for column in cursor.description], raw))


def claim_work(
    connection: sqlite3.Connection,
    *,
    claim_key: str,
    task: str,
    producer: str,
    prompt_version: str | None,
    input_hash: str,
    owner: str,
    now: str,
    lease_seconds: int,
    rerun: bool = False,
) -> tuple[str, int | None]:
    """Claim one question; returns (``claimed``, epoch), (``held``, None) or (``done``, None).

    ``done`` means a verdict was already completed under this claim (only a
    ``rerun`` re-claims it); ``held`` means another worker's lease is live.
    """

    expires = (parse_utc(now) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
    row = _row(connection, claim_key)
    if row is None:
        connection.execute(
            "INSERT INTO judgment_work_claims(claim_key, task, producer, prompt_version, input_hash, state, "
            "lease_owner, lease_expires_at, lease_epoch, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'leased', ?, ?, 1, ?, ?)",
            (claim_key, task, producer, prompt_version, input_hash, owner, expires, now, now),
        )
        return CLAIMED, 1
    if row["state"] == "done" and not rerun:
        return DONE, None
    if (
        row["state"] == "leased"
        and row["lease_owner"] not in (None, owner)
        and row["lease_expires_at"]
        and parse_utc(str(row["lease_expires_at"])) > parse_utc(now)
    ):
        return HELD, None
    epoch = int(row["lease_epoch"] or 0) + 1
    connection.execute(
        "UPDATE judgment_work_claims SET state = 'leased', lease_owner = ?, lease_expires_at = ?, "
        "lease_epoch = ?, updated_at = ? WHERE claim_key = ?",
        (owner, expires, epoch, now, claim_key),
    )
    return CLAIMED, epoch


def holds_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int) -> bool:
    """True while this worker's lease (owner and epoch) is the claim's current one."""

    row = _row(connection, claim_key)
    return (
        row is not None
        and row["state"] == "leased"
        and row["lease_owner"] == owner
        and int(row["lease_epoch"] or 0) == int(epoch)
    )


def complete_claim(
    connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, judgment_id: str, now: str
) -> bool:
    """Mark the question answered; False (and no change) when fenced out."""

    cursor = connection.execute(
        "UPDATE judgment_work_claims SET state = 'done', lease_owner = NULL, lease_expires_at = NULL, "
        "judgment_id = ?, updated_at = ? WHERE claim_key = ? AND state = 'leased' AND lease_owner = ? "
        "AND lease_epoch = ?",
        (judgment_id, now, claim_key, owner, int(epoch)),
    )
    return cursor.rowcount == 1


def lease_holder(connection: sqlite3.Connection, *, claim_key: str) -> str | None:
    """The owner of the claim's live or lapsed lease (None unless it is leased)."""

    row = _row(connection, claim_key)
    if row is None or row["state"] != "leased":
        return None
    return str(row["lease_owner"]) if row["lease_owner"] is not None else None


def take_over_claim(
    connection: sqlite3.Connection,
    *,
    claim_key: str,
    from_owner: str,
    owner: str,
    now: str,
    lease_seconds: int,
) -> int | None:
    """Take a lease from ``from_owner`` before it expires, when the caller
    knows that owner has ended (its job finished without completing or
    releasing the claim). Returns the new epoch, which fences the old owner
    out, or None when the lease is no longer ``from_owner``'s."""

    expires = (parse_utc(now) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
    row = _row(connection, claim_key)
    if row is None or row["state"] != "leased" or row["lease_owner"] != from_owner:
        return None
    epoch = int(row["lease_epoch"] or 0) + 1
    cursor = connection.execute(
        "UPDATE judgment_work_claims SET lease_owner = ?, lease_expires_at = ?, lease_epoch = ?, updated_at = ? "
        "WHERE claim_key = ? AND state = 'leased' AND lease_owner = ? AND lease_epoch = ?",
        (owner, expires, epoch, now, claim_key, from_owner, int(row["lease_epoch"] or 0)),
    )
    return epoch if cursor.rowcount == 1 else None


def renew_claim(
    connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, now: str, lease_seconds: int
) -> bool:
    """Extend a live lease (a heartbeat); False (and no change) when it is no longer this worker's."""

    expires = (parse_utc(now) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
    cursor = connection.execute(
        "UPDATE judgment_work_claims SET lease_expires_at = ?, updated_at = ? WHERE claim_key = ? "
        "AND state = 'leased' AND lease_owner = ? AND lease_epoch = ?",
        (expires, now, claim_key, owner, int(epoch)),
    )
    return cursor.rowcount == 1


def live_lease(connection: sqlite3.Connection, *, claim_key: str, now: str) -> bool:
    """True when someone holds an unexpired lease on the claim (read-only)."""

    row = _row(connection, claim_key)
    return bool(
        row is not None
        and row["state"] == "leased"
        and row["lease_expires_at"]
        and parse_utc(str(row["lease_expires_at"])) > parse_utc(now)
    )


def release_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, now: str) -> bool:
    """Give an unanswered claim back (a failed or refused call) so another run may take it."""

    cursor = connection.execute(
        "UPDATE judgment_work_claims SET state = 'released', lease_owner = NULL, lease_expires_at = NULL, "
        "updated_at = ? WHERE claim_key = ? AND state = 'leased' AND lease_owner = ? AND lease_epoch = ?",
        (now, claim_key, owner, int(epoch)),
    )
    return cursor.rowcount == 1


__all__ = [
    "CLAIMED", "DONE", "HELD", "claim_work", "complete_claim", "holds_claim", "lease_holder", "live_lease",
    "release_claim", "renew_claim", "take_over_claim",
]
