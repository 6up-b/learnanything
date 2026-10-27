"""Mobile PR-4: atomic session operations and ownership (migration 225).

``spec_mobile_tailnet_v1`` §6.5. One session is open at a time, because the
session-scoped caps are counted per session id. Two processes (the desktop
sidecar and the phone host, or the host's two workers) start, adopt, write to
and end that session, so every operation here is one ``BEGIN IMMEDIATE``
transaction (``Repository.atomic()``) that reads the session row and decides
from it under the write lock:

* :meth:`start_session_exclusive` creates a session and ends the others in one
  transaction, so interleaved starts leave exactly one open session. A session
  another device owns is never ended silently: the caller gets
  ``session_open_elsewhere`` with its snapshot, and replaces it only by naming
  it (compare-and-swap on its id), which keeps its checkpoint in
  ``session_handoffs`` first.
* :meth:`adopt_session` moves a session to another device, a compare-and-swap
  on ``owner_generation``. The session id, so the caps, the stable submission
  id and the scheduler-offer binding, carry over; the checkpoint is untouched.
* :meth:`require_session_owner` is the check every session-scoped write makes
  inside its own transaction: a write from a device that does not own the
  session fails with ``session_moved``. Reads are unrestricted.

``owner_device_id`` NULL is the desktop. The device a request comes from is
the request origin's (§6.8, PR-5), never a parameter.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid

#: The owner label of a session no device owns.
DESKTOP_LABEL = "desktop"
#: How much of a draft's first line a snapshot carries.
DRAFT_PREVIEW_CHARS = 120


class SessionOwnershipError(Exception):
    """A session operation refused by its owner or its state.

    ``code`` is the stable error code the sidecar and the host return
    (``not_found``, ``session_ended``, ``session_moved``,
    ``session_open_elsewhere``, ``current_item_desktop_only``); ``details``
    is the snapshot the client shows. None of them is retryable as is: the
    client re-reads and asks the learner.
    """

    def __init__(self, code: str, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


def _same_owner(left: str | None, right: str | None) -> bool:
    return (left or None) == (right or None)


def _draft_text(checkpoint: Mapping[str, Any] | None) -> str:
    if not checkpoint:
        return ""
    answer = checkpoint.get("current_answer")
    return answer if isinstance(answer, str) else ""


class SessionOwnershipStoreMixin:
    """Repository methods for session ownership; every write is one transaction."""

    # -- reads -----------------------------------------------------------

    def device_label(self, device_id: str | None) -> str:
        """The label the learner gave a device; ``desktop`` for NULL."""

        if not device_id:
            return DESKTOP_LABEL
        with self.connection() as connection:
            row = connection.execute("SELECT label FROM mobile_devices WHERE id = ?", (device_id,)).fetchone()
        return str(row["label"]) if row is not None and row["label"] else device_id

    def session_owner_snapshot(self, session: Mapping[str, Any]) -> dict[str, Any]:
        """What a client shows about a session another device holds (§6.5):
        its owner, its current item, and whether a draft exists, with the
        draft's first line."""

        checkpoint = self.fetch_session_checkpoint(str(session["id"]))
        draft = _draft_text(checkpoint)
        first_line = next((line.strip() for line in draft.splitlines() if line.strip()), "")
        owner = session.get("owner_device_id")
        return {
            "session_id": str(session["id"]),
            "started_at": session.get("started_at"),
            "owner_device_id": owner,
            "owner_label": self.device_label(owner),
            "owner_generation": int(session.get("owner_generation") or 0),
            "current_practice_item_id": (checkpoint or {}).get("current_practice_item_id"),
            "has_draft": bool(draft.strip()),
            "draft_first_line": first_line[:DRAFT_PREVIEW_CHARS] if first_line else None,
        }

    def session_handoffs(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM session_handoffs WHERE session_id = ? ORDER BY at, id", (session_id,)
            ).fetchall()
        handoffs = []
        for row in rows:
            payload = dict(row)
            raw = payload.pop("checkpoint_json")
            payload["checkpoint"] = json.loads(raw) if raw else None
            handoffs.append(payload)
        return handoffs

    # -- the ownership check ----------------------------------------------

    def require_session_owner(
        self,
        session_id: str,
        device_id: str | None,
        *,
        require_open: bool = True,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        """The session row, if ``device_id`` owns it; ``session_moved`` otherwise.

        Called by every session-scoped write, inside the write's own
        transaction when it has one, so no adopt commits between the check
        and the write. ``require_open`` (the default) also refuses an ended
        session, as the writes did before ownership existed.

        ``expected_generation`` is for a write that checked ownership before
        slow work outside its transaction (a skip builds the queue first) and
        checks again inside it: a session that moved in between, even one
        adopted back by the same device, is ``session_moved``, because its
        checkpoint may now be another device's draft (Codex review F1).
        """

        session = self.fetch_session(session_id)
        if session is None:
            raise SessionOwnershipError("not_found", f"Session {session_id} was not found.")
        moved = expected_generation is not None and int(session.get("owner_generation") or 0) != int(
            expected_generation
        )
        if moved or not _same_owner(session.get("owner_device_id"), device_id):
            snapshot = self.session_owner_snapshot(session)
            raise SessionOwnershipError(
                "session_moved",
                f"This session continued on {snapshot['owner_label']}.",
                {key: snapshot[key] for key in ("session_id", "owner_device_id", "owner_label", "owner_generation")},
            )
        if require_open and session["ended_at"] is not None:
            raise SessionOwnershipError("session_ended", f"Session {session_id} has ended.")
        return session

    # -- operations --------------------------------------------------------

    def start_session_exclusive(
        self,
        fields: Mapping[str, Any],
        owner_device_id: str | None,
        replace: str | None = None,
        *,
        settle_checkpoint: Callable[[dict[str, Any]], None] | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Start the one open session for ``owner_device_id`` (§6.5, PR-4).

        In one ``BEGIN IMMEDIATE`` transaction it reads the open sessions:

        * none, or only the caller's own: create the new session and end the
          others at their last activity, as starting did before (the caller's
          own session is replaced silently);
        * one another device owns and ``replace`` is None, or names any other
          session: raise ``session_open_elsewhere`` with its snapshot;
        * ``replace`` names no open session (a stale replacement, such as a
          retry of one that already committed) while a session is open, the
          caller's own included: raise ``session_open_elsewhere`` with the
          open session's snapshot, ending nothing (a compare-and-swap on the
          id, checked before the same-owner rule);
        * ``replace`` names that session (the learner chose "start fresh"):
          keep its checkpoint in ``session_handoffs``, end it, and create the
          new one.

        ``fields`` are ``create_session``'s (energy, sleep quality, available
        minutes, notes path). ``settle_checkpoint`` runs, inside the
        transaction, on the checkpoint of every session about to end (the
        sidecar settles a pending self-grade disclosure there). Returns the
        new session's id.
        """

        with self.atomic():
            with self.connection() as connection:
                open_rows = [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC, id DESC"
                    ).fetchall()
                ]
            foreign = [row for row in open_rows if not _same_owner(row.get("owner_device_id"), owner_device_id)]
            if replace is not None and open_rows and all(row["id"] != replace for row in open_rows):
                # A stale ``replace`` (Codex review F2): the session it names
                # is no longer open, so the learner's "start fresh" was decided
                # on a session that has since ended (typically by this very
                # replacement, whose response was lost). The open session,
                # even the caller's own, is not ended on that stale decision:
                # the caller re-reads it and asks again.
                held = (foreign or open_rows)[0]
                raise SessionOwnershipError(
                    "session_open_elsewhere",
                    f"A session is open on {self.device_label(held.get('owner_device_id'))}.",
                    self.session_owner_snapshot(held),
                )
            if foreign:
                held = foreign[0]
                if replace is None or replace != held["id"]:
                    raise SessionOwnershipError(
                        "session_open_elsewhere",
                        f"A session is open on {self.device_label(held.get('owner_device_id'))}.",
                        self.session_owner_snapshot(held),
                    )
            now = utc_now_iso(clock)
            for row in foreign:
                self._record_handoff(
                    session_id=str(row["id"]), kind="replace",
                    from_device_id=row.get("owner_device_id"), to_device_id=owner_device_id,
                    generation=int(row.get("owner_generation") or 0),
                    checkpoint=self.fetch_session_checkpoint(str(row["id"])), at=now,
                )
            session_id = self.create_session(**dict(fields), clock=clock)
            if owner_device_id is not None:
                with self.connection() as connection:
                    connection.execute(
                        "UPDATE sessions SET owner_device_id = ? WHERE id = ?", (owner_device_id, session_id)
                    )
                    connection.commit()
            if settle_checkpoint is not None:
                for checkpoint in self.open_session_checkpoints_except(session_id):
                    settle_checkpoint(checkpoint)
            self.end_open_sessions_except(session_id, clock=clock)
        return session_id

    def adopt_session(
        self,
        session_id: str,
        owner_device_id: str | None,
        expected_generation: int,
        *,
        current_item_ineligible: Callable[[str], bool] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Move an open session to ``owner_device_id`` (§6.5, PR-4).

        A compare-and-swap on ``owner_generation``: it sets the owner,
        increments the generation and records the handoff, in one
        transaction; the checkpoint is untouched. A stale
        ``expected_generation`` (another device adopted it in between) raises
        ``session_moved`` with the current owner and generation. Adopting a
        session the caller already owns changes nothing (a retried adopt).

        ``current_item_ineligible`` (PR-6's device eligibility, for the
        adopting device): when the checkpoint's current item is ineligible
        and carries a non-empty draft, the adopt is refused with
        ``current_item_desktop_only``, so adopting never loses a draft.
        Returns the session's ownership snapshot.
        """

        with self.atomic():
            session = self.fetch_session(session_id)
            if session is None:
                raise SessionOwnershipError("not_found", f"Session {session_id} was not found.")
            if session["ended_at"] is not None:
                raise SessionOwnershipError("session_ended", f"Session {session_id} has ended.")
            if _same_owner(session.get("owner_device_id"), owner_device_id):
                return self.session_owner_snapshot(session)
            generation = int(session.get("owner_generation") or 0)
            if generation != int(expected_generation):
                snapshot = self.session_owner_snapshot(session)
                raise SessionOwnershipError(
                    "session_moved",
                    f"This session moved to {snapshot['owner_label']} first.",
                    {key: snapshot[key] for key in ("session_id", "owner_device_id", "owner_label",
                                                    "owner_generation")},
                )
            checkpoint = self.fetch_session_checkpoint(session_id)
            item_id = (checkpoint or {}).get("current_practice_item_id")
            if (
                current_item_ineligible is not None
                and item_id
                and _draft_text(checkpoint).strip()
                and current_item_ineligible(str(item_id))
            ):
                raise SessionOwnershipError(
                    "current_item_desktop_only",
                    "The current question has a draft and can only be answered on the desktop.",
                    self.session_owner_snapshot(session),
                )
            now = utc_now_iso(clock)
            with self.connection() as connection:
                cursor = connection.execute(
                    "UPDATE sessions SET owner_device_id = ?, owner_generation = owner_generation + 1, "
                    "updated_at = ? WHERE id = ? AND owner_generation = ? AND ended_at IS NULL",
                    (owner_device_id, now, session_id, generation),
                )
                connection.commit()
            if cursor.rowcount != 1:  # unreachable under the write lock; kept as the swap's own guard
                raise SessionOwnershipError("session_moved", "This session moved first.", {"session_id": session_id})
            self._record_handoff(
                session_id=session_id, kind="adopt",
                from_device_id=session.get("owner_device_id"), to_device_id=owner_device_id,
                generation=generation + 1, checkpoint=checkpoint, at=now,
            )
            return self.session_owner_snapshot(self.fetch_session(session_id) or session)

    def end_session_owned(
        self,
        session_id: str,
        device_id: str | None,
        *,
        clear: Callable[[str], Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """End a session its owner ends, in one transaction (§6.5, PR-4).

        Ending an already-ended session returns it unchanged, as before.
        ``clear`` (the sidecar's checkpoint clear, which settles a pending
        disclosure first) runs inside the same transaction.
        """

        with self.atomic():
            self.require_session_owner(session_id, device_id, require_open=False)
            row = self.end_session(session_id, clock=clock)
            if row is None:  # unreachable: the row was read under the write lock
                raise SessionOwnershipError("not_found", f"Session {session_id} was not found.")
            if clear is not None:
                clear(session_id)
        return row

    def _record_handoff(
        self,
        *,
        session_id: str,
        kind: str,
        from_device_id: str | None,
        to_device_id: str | None,
        generation: int,
        checkpoint: Mapping[str, Any] | None,
        at: str,
    ) -> str:
        handoff_id = f"sho_{new_ulid()}"
        with self.connection() as owned:
            owned.execute(
                "INSERT INTO session_handoffs (id, session_id, kind, from_device_id, to_device_id, generation, "
                "checkpoint_json, at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    handoff_id, session_id, kind, from_device_id, to_device_id, generation,
                    json.dumps(dict(checkpoint), sort_keys=True) if checkpoint is not None else None, at,
                ),
            )
            owned.commit()
        return handoff_id
