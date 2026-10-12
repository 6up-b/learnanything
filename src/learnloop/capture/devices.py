"""Hashed credentials and durable, serialized pairing admission.

Revision 2 pairing is intentional: the owner's implementation request retains
scopes and exchange even though the later on-disk spec removes them.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid

from .errors import CaptureError

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone aware")
    return value.astimezone(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _label(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise CaptureError("validation_error", 422, "A device label of 1–200 characters is required")
    return value.strip()


def create_pairing(
    repo: Repository, *, label: str = "Phone", scope: str = "capture",
    now: datetime | None = None,
) -> dict:
    label = _label(label)
    if scope not in ("capture", "app"):
        raise CaptureError("validation_error", 422, "Unknown token scope")
    at = _now(now)
    secret = secrets.token_urlsafe(32)
    code = "".join(secrets.choice(_ALPHABET) for _ in range(10))
    pairing_id = new_ulid()
    expires = (at + timedelta(minutes=5)).isoformat()
    with repo.atomic(), repo.connection() as conn:
        _expire_unclaimed(conn, at)
        conn.execute("DELETE FROM mobile_pairings WHERE expires_at<=?", (at.isoformat(),))
        # Only an explicit local pair command clears a durable lock.
        conn.execute("UPDATE mobile_pairing_guard SET locked=0 WHERE id=1")
        conn.execute("DELETE FROM mobile_pairing_attempts")
        conn.execute(
            """INSERT INTO mobile_pairings
               (id,label,scope,secret_hash,code_hash,created_at,expires_at)
               VALUES (?,?,?,?,?,?,?)""",
            (pairing_id, label, scope, _hash(secret), _hash(code), at.isoformat(), expires),
        )
    return dict(pairing_id=pairing_id, secret=secret, code=code, expires_at=expires)


def exchange_pairing(
    repo: Repository, *, secret: str | None = None, code: str | None = None,
    device_label: str | None = None, tailscale_login: str | None = None,
    now: datetime | None = None,
) -> dict:
    at = _now(now)
    stamp = at.isoformat()
    error = None
    result = None
    valid = (isinstance(secret, str) and code is None) or (
        isinstance(code, str) and secret is None
    )
    credential = secret if secret is not None else (code.upper() if isinstance(code, str) else "")
    column = "secret_hash" if secret is not None else "code_hash"
    label = _label(device_label) if device_label is not None else None
    # Locked exchanges must not contend for the vault's writer reservation.
    with repo.connection() as conn:
        if conn.execute("SELECT locked FROM mobile_pairing_guard WHERE id=1").fetchone()[0]:
            raise CaptureError("pairing_locked", 429, "Run pair on the desktop to unlock pairing")
    with repo.atomic(), repo.connection() as conn:
        locked = conn.execute("SELECT locked FROM mobile_pairing_guard WHERE id=1").fetchone()[0]
        row = conn.execute(
            f"SELECT * FROM mobile_pairings WHERE {column}=?",
            (_hash(credential) if valid else "",),
        ).fetchone()
        if locked:
            error = CaptureError("pairing_locked", 429, "Run pair on the desktop to unlock pairing")
        elif (not row or row["consumed_at"] or row["expires_at"] <= stamp
              or row["failed_attempts"] >= 5):
            # An opaque wrong code cannot identify its intended record. Charge
            # every live record, rather than allowing guesses to evade its cap.
            conn.execute(
                """UPDATE mobile_pairings SET failed_attempts=failed_attempts+1
                   WHERE consumed_at IS NULL AND expires_at>? AND failed_attempts<5""",
                (stamp,),
            )
            conn.execute("DELETE FROM mobile_pairing_attempts WHERE at<?",
                         ((at - timedelta(minutes=10)).isoformat(),))
            conn.execute("INSERT INTO mobile_pairing_attempts(at) VALUES (?)", (stamp,))
            count = conn.execute("SELECT count(*) FROM mobile_pairing_attempts").fetchone()[0]
            if count >= 20:
                conn.execute("UPDATE mobile_pairing_guard SET locked=1 WHERE id=1")
                error = CaptureError("pairing_locked", 429, "Run pair on the desktop to unlock pairing")
            else:
                error = CaptureError("invalid_pairing", 401, "Pairing is invalid, expired or already used")
        else:
            token, device_id = secrets.token_urlsafe(32), new_ulid()
            conn.execute("UPDATE mobile_pairings SET consumed_at=? WHERE id=?", (stamp, row["id"]))
            conn.execute(
                """INSERT INTO mobile_devices(id,label,scope,token_hash,tailscale_login,created_at)
                   VALUES (?,?,?,?,?,?)""",
                (device_id, label or row["label"], row["scope"], _hash(token), tailscale_login, stamp),
            )
            result = dict(device_id=device_id, scope=row["scope"], token=token)
    # Raise only AFTER committing the failed-attempt accounting.
    if error:
        raise error
    return result


def _expire_unclaimed(conn, at: datetime) -> None:
    conn.execute(
        """UPDATE mobile_devices SET revoked_at=?
           WHERE revoked_at IS NULL AND last_seen_at IS NULL AND created_at<=?""",
        (at.isoformat(), (at - timedelta(hours=24)).isoformat()),
    )


def authenticate_device(
    repo: Repository, token: str, *, scope: str = "capture", now: datetime | None = None,
) -> dict:
    if scope not in ("capture", "app"):
        raise CaptureError("validation_error", 422, "Unknown required scope")
    at = _now(now)
    with repo.connection() as conn:
        row = conn.execute("SELECT * FROM mobile_devices WHERE token_hash=?",
                           (_hash(token),)).fetchone()
    if row is None or row["revoked_at"] or (
        row["last_seen_at"] is None
        and row["created_at"] <= (at - timedelta(hours=24)).isoformat()
    ):
        raise CaptureError("unauthorized", 401, "A valid device token is required")
    if scope == "app" and row["scope"] != "app":
        raise CaptureError("insufficient_scope", 403, "This endpoint requires an app token")
    return dict(device_id=row["id"], label=row["label"], scope=row["scope"])


def touch_device(repo: Repository, device_id: str, *, now: datetime | None = None) -> None:
    """Persist admitted use at most once per minute, never during credential checks."""
    at = _now(now)
    cutoff = (at - timedelta(minutes=1)).isoformat()
    with repo.connection() as conn:
        row = conn.execute("SELECT last_seen_at FROM mobile_devices WHERE id=?", (device_id,)).fetchone()
    if row is not None and (row["last_seen_at"] is None or row["last_seen_at"] < cutoff):
        with repo.atomic(), repo.connection() as conn:
            conn.execute(
                """UPDATE mobile_devices SET last_seen_at=?,claimed_at=COALESCE(claimed_at,?)
                   WHERE id=? AND revoked_at IS NULL AND (last_seen_at IS NULL OR last_seen_at<?)""",
                (at.isoformat(), at.isoformat(), device_id, cutoff),
            )


def list_devices(repo: Repository, *, now: datetime | None = None) -> list[dict]:
    at = _now(now)
    with repo.connection() as conn:
        rows = [dict(row) for row in conn.execute(
            "SELECT id,label,scope,created_at,last_seen_at,revoked_at FROM mobile_devices ORDER BY created_at,id"
        )]
    for row in rows:
        if not row["revoked_at"] and row["last_seen_at"] is None:
            expiry = datetime.fromisoformat(row["created_at"]) + timedelta(hours=24)
            if expiry <= at:
                row["revoked_at"] = expiry.isoformat()
    return rows


def revoke_device(repo: Repository, device_id: str, *, now: datetime | None = None) -> dict:
    with repo.atomic(), repo.connection() as conn:
        if not conn.execute("SELECT 1 FROM mobile_devices WHERE id=?", (device_id,)).fetchone():
            raise CaptureError("not_found", 404, "Device not found")
        conn.execute("UPDATE mobile_devices SET revoked_at=COALESCE(revoked_at,?) WHERE id=?",
                     (_now(now).isoformat(), device_id))
    return dict(device_id=device_id, revoked=True)
