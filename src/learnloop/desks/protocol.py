"""The workbench's write protocol (spec §3.4, review F3), shared by ``desk.apply`` and ``pad.apply``.

Every write call carries ``{client_id, seq, ops}``. ``seq`` numbers a client's batches, desk and pad
batches alike, from 1 with no gap. The server

* applies a batch in one SQLite transaction together with its stored reply (its receipt);
* refuses a batch whose ``seq`` is not the client's next number (``seq_gap``), so batches land in order;
* answers a batch whose ``seq`` was already applied with the stored reply, unchanged, and applies
  nothing; the same number with different ops is refused (``seq_reused``), since replying with another
  batch's receipt would hide a client bug;
* lets each op name the head it expects: a stale head is not applied and its result is
  ``conflict`` with the current head; an op that cannot apply at all is ``refused`` with a code. Either
  way the batch is applied (its other ops land) and its number is used, so one bad op never blocks the
  client's outbox.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.stores import workspace_batches as batches

OK = "ok"
CONFLICT = "conflict"
REFUSED = "refused"


class ProtocolError(Exception):
    """A batch the server will not take (nothing applied, nothing stored)."""

    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


class OpRefused(Exception):
    """One op that cannot apply; the batch goes on (its result is ``refused``)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class OpConflict(Exception):
    """One op whose expected head is stale; the batch goes on (its result is ``conflict``)."""

    def __init__(self, current: Mapping[str, Any]) -> None:
        super().__init__("stale head")
        self.current = dict(current)


def ok(**extra: Any) -> dict[str, Any]:
    return {"status": OK, **extra}


def run_op(connection: Any, apply: Callable[[], Mapping[str, Any] | None]) -> dict[str, Any]:
    """One op's result. Each op runs in a savepoint of the batch's transaction (the repository's
    atomic connection gives one per ``with``), so an op refused halfway leaves none of its writes."""

    try:
        with connection:
            extra = apply() or {}
    except OpConflict as conflict:
        return {"status": CONFLICT, "current": conflict.current}
    except OpRefused as refused:
        return {"status": REFUSED, "code": refused.code, "message": str(refused)}
    return ok(**extra)


def request_hash(channel: str, request: Mapping[str, Any]) -> str:
    body = json.dumps({"channel": channel, "request": request}, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def apply_batch(
    repository: Any,
    *,
    channel: str,
    client_id: str,
    seq: int,
    request: Mapping[str, Any],
    apply_ops: Callable[[Any, str], dict[str, Any]],
    pad_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Apply one batch exactly once, in order, with its receipt; return its reply.

    ``request`` is the batch's canonical form (what a retry must repeat to be the same batch);
    ``apply_ops(connection, now)`` applies its ops inside the transaction and returns the reply."""

    if not client_id:
        raise ProtocolError("validation_error", "A write batch names its client.")
    if seq < 1:
        raise ProtocolError("validation_error", "A batch's number starts at 1.")
    digest = request_hash(channel, request)
    with repository.atomic():
        connection = repository.connection()
        stored = batches.find_receipt(connection, client_id, seq)
        if stored is not None:
            if stored.channel != channel or stored.request_hash != digest:
                raise ProtocolError(
                    "seq_reused",
                    f"Batch {seq} of this client was already applied with other ops.",
                    {"seq": seq},
                )
            return stored.result
        expected = batches.last_seq(connection, client_id) + 1
        if seq != expected:
            raise ProtocolError(
                "seq_gap",
                f"Batch {seq} arrived before batch {expected}; send the batches in order.",
                {"seq": seq, "expected_seq": expected},
            )
        now = utc_now_iso(clock)
        reply = {"applied_seq": seq, **apply_ops(connection, now)}
        batches.insert_receipt(connection, channel=channel, client_id=client_id, seq=seq, request_hash=digest,
                               result=reply, applied_at=now, pad_id=pad_id)
    return reply


def client_seq_heads(repository: Any) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [{"client_id": client, "seq": seq} for client, seq in batches.client_heads(connection)]


__all__ = [
    "CONFLICT", "OK", "REFUSED", "OpConflict", "OpRefused", "ProtocolError", "apply_batch", "client_seq_heads", "ok",
    "request_hash", "run_op",
]
