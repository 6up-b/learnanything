"""Remediation episodes and follow-up work.

Owns remediation episodes, follow-up tasks, ratings and readiness records."""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import _decode_followup_task
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


def _queued_followup_action(action: Any) -> tuple[str, str] | None:
    if not isinstance(action, str):
        return None
    if action.startswith("negative_surprise_followup:"):
        return ("negative_surprise_followup", action.split(":", 1)[1])
    if action.startswith("intervention_followup:queued:"):
        return ("intervention_followup", action.split(":", 2)[2])
    return None


def _decode_remediation_episode(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["passages_shown"] = _loads(payload.pop("passages_shown_json"), [])
    return payload


class RemediationStoreMixin:

    def pending_followup_practice_item_ids(self, *, clock: Clock | None = None) -> list[str]:
        """Return queued follow-up item ids that have not yet been attempted."""

        return [
            item["practice_item_id"]
            for item in self.pending_followup_practice_items(clock=clock)
        ]

    def pending_followup_practice_items(
        self, *, clock: Clock | None = None
    ) -> list[dict[str, str]]:
        """Return queued follow-ups that have not yet been attempted.

        Follow-up insertion is represented in MVP as an action recorded on
        ``attempt_surprise``. The scheduler consumes those actions until a later
        attempt exists for the chosen Practice Item.
        """

        task_rows = self.due_followup_tasks(clock=clock)
        # ``action_type`` follows the task's own ``kind`` (migration 139): the
        # table now carries two delayed lanes and hardcoding ``cold_retry`` here
        # would label a §5.7 certification probe as a repair retry all the way
        # into the scheduler's plain-English reason.
        pending: list[dict[str, str]] = [
            {
                "practice_item_id": str(task["selected_item_id"]),
                "action_type": str(task["kind"]),
                "followup_task_id": str(task["id"]),
            }
            for task in task_rows
            if task.get("selected_item_id")
        ]
        seen: set[str] = {item["practice_item_id"] for item in pending}
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT attempt_id, triggered_actions_json, created_at
                FROM attempt_surprise
                WHERE triggered_actions_json IS NOT NULL
                ORDER BY created_at DESC, attempt_id DESC
                """
            ).fetchall()
            for row in rows:
                for action in _loads(row["triggered_actions_json"], []):
                    parsed = _queued_followup_action(action)
                    if parsed is None:
                        continue
                    action_type, practice_item_id = parsed
                    if not practice_item_id or practice_item_id in seen:
                        continue
                    later_attempt = connection.execute(
                        """
                        SELECT 1 FROM practice_attempts
                        WHERE practice_item_id = ? AND created_at > ?
                        LIMIT 1
                        """,
                        (practice_item_id, row["created_at"]),
                    ).fetchone()
                    if later_attempt is not None:
                        continue
                    seen.add(practice_item_id)
                    pending.append({"practice_item_id": practice_item_id, "action_type": action_type})
        return pending

    # -- Structured remediation episodes and delayed follow-ups -----------

    def create_remediation_episode(
        self,
        *,
        case_kind: str,
        case_ref: str,
        passages_shown: Sequence[Mapping[str, Any]] = (),
        state: str = "diagnosis",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        episode_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO remediation_episodes(
                  id, case_kind, case_ref, state, passages_shown_json,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (episode_id, case_kind, case_ref, state, _json(list(passages_shown)), now, now),
            )
            connection.commit()
        episode = self.remediation_episode(episode_id)
        assert episode is not None
        return episode

    def remediation_episode(self, episode_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM remediation_episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return _decode_remediation_episode(row) if row is not None else None

    def get_or_create_open_remediation_episode(
        self,
        *,
        case_kind: str,
        case_ref: str,
        states: Sequence[str],
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The newest episode for the case in one of ``states``, else a new one.

        Idempotent create, atomically: the SELECT and the INSERT run inside one
        write transaction, so two near-simultaneous "start this repair" calls
        (React StrictMode double-mounts the repair overlay) resolve to ONE
        episode instead of minting a duplicate pair. A plain SELECT-then-INSERT
        across two repository calls was exactly the race that left orphaned
        `diagnosis`-state twins beside every committed episode."""

        episode_id = new_ulid()
        now = utc_now_iso(clock)
        placeholders = ",".join("?" for _ in states)
        with self.connection() as connection:
            if not connection.in_transaction:
                # Take the write lock BEFORE reading so the check-and-insert is
                # one atomic step even across connections.
                connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                f"""
                SELECT id FROM remediation_episodes
                 WHERE case_kind = ? AND case_ref = ?
                   AND state IN ({placeholders})
                 ORDER BY created_at DESC, id DESC
                 LIMIT 1
                """,
                (case_kind, case_ref, *states),
            ).fetchone()
            if row is not None:
                episode_id = str(row["id"])
            else:
                connection.execute(
                    """
                    INSERT INTO remediation_episodes(
                      id, case_kind, case_ref, state, passages_shown_json,
                      created_at, updated_at
                    ) VALUES (?, ?, ?, 'diagnosis', '[]', ?, ?)
                    """,
                    (episode_id, case_kind, case_ref, now, now),
                )
            connection.commit()
        episode = self.remediation_episode(episode_id)
        assert episode is not None
        return episode

    def update_remediation_episode(
        self, episode_id: str, *, clock: Clock | None = None, **changes: Any
    ) -> dict[str, Any] | None:
        allowed = {
            "state", "passages_shown", "primed_item_id", "cold_item_id",
            "primed_attempt_id", "cold_attempt_id", "completed_at",
            "cold_measurement_opportunity_id",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return self.remediation_episode(episode_id)
        assignments: list[str] = []
        params: list[Any] = []
        for key, value in values.items():
            column = "passages_shown_json" if key == "passages_shown" else key
            assignments.append(f"{column} = ?")
            params.append(_json(value) if key == "passages_shown" else value)
        assignments.append("updated_at = ?")
        params.extend([utc_now_iso(clock), episode_id])
        with self.connection() as connection:
            connection.execute(
                f"UPDATE remediation_episodes SET {', '.join(assignments)} WHERE id = ?",
                params,
            )
            connection.commit()
        return self.remediation_episode(episode_id)

    def open_remediation_episode_for_case(
        self, *, case_kind: str, case_ref: str
    ) -> dict[str, Any] | None:
        """The newest episode for the case that has not yet recorded a primed attempt.

        Guided-redo binding (Fix 3): a redo on the ORIGINAL item may serve as
        the episode's primed attempt when the episode is still open —
        `diagnosis`/`prescribed` (uncommitted) or `treatment` with no primed
        attempt recorded yet."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM remediation_episodes
                WHERE case_kind = ? AND case_ref = ?
                  AND primed_attempt_id IS NULL
                  AND state IN ('diagnosis', 'prescribed', 'treatment')
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (case_kind, case_ref),
            ).fetchone()
        return _decode_remediation_episode(row) if row is not None else None

    def open_remediation_episode_for_primed_item(self, practice_item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM remediation_episodes
                WHERE primed_item_id = ? AND primed_attempt_id IS NULL
                  AND state = 'treatment'
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        return _decode_remediation_episode(row) if row is not None else None

    def open_remediation_episodes_for_item(
        self, practice_item_id: str
    ) -> list[dict[str, Any]]:
        """Live episodes that bound this item as their primed or cold surface.

        Reveal attribution (migration 154) needs the reverse of
        ``open_remediation_episode_for_primed_item``: given an item the learner
        was just shown something about, which repair — if any — does that
        exposure belong to? The cold surface is included because a reveal on a
        *scheduled but not yet due* cold item is precisely the contamination the
        ledger exists to catch. Newest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM remediation_episodes
                WHERE (primed_item_id = ? OR cold_item_id = ?)
                  AND state NOT IN ('completed', 'abandoned')
                ORDER BY created_at DESC, id DESC
                """,
                (practice_item_id, practice_item_id),
            ).fetchall()
        return [_decode_remediation_episode(row) for row in rows]

    def create_followup_task(
        self,
        *,
        kind: str,
        case_kind: str,
        case_ref: str,
        not_before: str,
        selected_item_id: str | None,
        source_attempt_id: str | None = None,
        remediation_episode_id: str | None = None,
        expires_at: str | None = None,
        context: Mapping[str, Any] | None = None,
        learning_object_id: str | None = None,
        measurement_opportunity_id: str | None = None,
        measurement_decision_reason: str | None = None,
        measurement_candidate_summary: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Schedule one delayed follow-up.

        ``context`` (migration 124, spec §6.2) travels WITH the task: the cold
        retry that consumes it needs the source attempt, causal factor,
        hypothesis set, repair class, and avoided affordances, and reconstructing
        them days later from a bare item id is exactly the "future caller"
        assumption the causal spec forbids. The §5.7 certification cold probe
        (migration 139) carries its certificate receipt through the same channel.

        ``learning_object_id`` (migration 139) is the indexed scope a
        certification probe needs so "is there a live probe for an LO whose
        certificate has since been withdrawn?" is a query rather than a JSON scan.
        """

        task_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO followup_tasks(
                  id, kind, case_kind, case_ref, source_attempt_id,
                  remediation_episode_id, not_before, expires_at, status,
                  selected_item_id, context_json, learning_object_id,
                  measurement_opportunity_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id, kind, case_kind, case_ref, source_attempt_id,
                    remediation_episode_id, not_before, expires_at,
                    selected_item_id,
                    _json(dict(context)) if context is not None else None,
                    learning_object_id,
                    measurement_opportunity_id,
                    now, now,
                ),
            )
            if (
                measurement_opportunity_id is not None
                and measurement_decision_reason is not None
            ):
                # The queue row and the opportunity's scheduled decision are
                # one transaction. A crash cannot leave a schedulable task
                # whose denominator row still says "undecided".
                connection.execute(
                    """
                    INSERT OR IGNORE INTO cold_measurement_opportunity_decisions(
                      id, measurement_opportunity_id, decision, reason,
                      followup_task_id, selected_item_id,
                      candidate_summary_json, scheduled_not_before,
                      scheduled_expires_at, created_at
                    ) VALUES (?, ?, 'scheduled', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        measurement_opportunity_id,
                        measurement_decision_reason,
                        task_id,
                        selected_item_id,
                        _json(dict(measurement_candidate_summary or {})),
                        not_before,
                        expires_at,
                        now,
                    ),
                )
            connection.commit()
        task = self.followup_task(task_id)
        assert task is not None
        return task

    # -- Cold-measurement opportunities (migration 151) -------------------

    def get_or_create_cold_measurement_opportunity(
        self,
        *,
        lane: str,
        trigger_kind: str,
        trigger_ref: str,
        policy_version: str,
        learning_object_id: str | None = None,
        case_kind: str | None = None,
        case_ref: str | None = None,
        remediation_episode_id: str | None = None,
        source_attempt_id: str | None = None,
        certificate_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Create the denominator row before candidate selection.

        The unique ``(lane, trigger_kind, trigger_ref)`` key makes scheduler
        replay idempotent.  The row is append-only: a later scheduling decision
        is a child record rather than a mutation of the opportunity.
        """

        opportunity_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT OR IGNORE INTO cold_measurement_opportunities(
                  id, lane, trigger_kind, trigger_ref, learning_object_id,
                  case_kind, case_ref, remediation_episode_id,
                  source_attempt_id, certificate_id, policy_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opportunity_id,
                    lane,
                    trigger_kind,
                    trigger_ref,
                    learning_object_id,
                    case_kind,
                    case_ref,
                    remediation_episode_id,
                    source_attempt_id,
                    certificate_id,
                    policy_version,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM cold_measurement_opportunities
                 WHERE lane = ? AND trigger_kind = ? AND trigger_ref = ?
                """,
                (lane, trigger_kind, trigger_ref),
            ).fetchone()
            connection.commit()
        assert row is not None
        return dict(row)

    def cold_measurement_opportunity(
        self, opportunity_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM cold_measurement_opportunities WHERE id = ?",
                (opportunity_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def record_cold_measurement_opportunity_decision(
        self,
        *,
        measurement_opportunity_id: str,
        decision: str,
        reason: str,
        followup_task_id: str | None = None,
        selected_item_id: str | None = None,
        candidate_summary: Mapping[str, Any] | None = None,
        scheduled_not_before: str | None = None,
        scheduled_expires_at: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Settle an opportunity once, preserving the first terminal decision."""

        decision_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO cold_measurement_opportunity_decisions(
                  id, measurement_opportunity_id, decision, reason,
                  followup_task_id, selected_item_id, candidate_summary_json,
                  scheduled_not_before, scheduled_expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    measurement_opportunity_id,
                    decision,
                    reason,
                    followup_task_id,
                    selected_item_id,
                    _json(dict(candidate_summary or {})),
                    scheduled_not_before,
                    scheduled_expires_at,
                    utc_now_iso(clock),
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM cold_measurement_opportunity_decisions
                 WHERE measurement_opportunity_id = ?
                """,
                (measurement_opportunity_id,),
            ).fetchone()
            connection.commit()
        assert row is not None
        return self._decode_cold_measurement_opportunity_decision(row)

    @staticmethod
    def _decode_cold_measurement_opportunity_decision(
        row: Any,
    ) -> dict[str, Any]:
        payload = dict(row)
        payload["candidate_summary"] = _loads(
            payload.pop("candidate_summary_json"), {}
        )
        return payload

    def cold_measurement_opportunity_decision(
        self, measurement_opportunity_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM cold_measurement_opportunity_decisions
                 WHERE measurement_opportunity_id = ?
                """,
                (measurement_opportunity_id,),
            ).fetchone()
        return (
            self._decode_cold_measurement_opportunity_decision(row)
            if row is not None
            else None
        )

    def followup_task(self, task_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM followup_tasks WHERE id = ?", (task_id,)).fetchone()
        return _decode_followup_task(row) if row is not None else None

    def attach_followup_task_measurement_opportunity(
        self, task_id: str, measurement_opportunity_id: str, *, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        """Prospectively attach lineage to a pre-151 task, without replacing it."""

        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks
                   SET measurement_opportunity_id = ?, updated_at = ?
                 WHERE id = ? AND measurement_opportunity_id IS NULL
                """,
                (measurement_opportunity_id, utc_now_iso(clock), task_id),
            )
            connection.commit()
        return self.followup_task(task_id)

    def due_followup_tasks(self, *, clock: Clock | None = None) -> list[dict[str, Any]]:
        """The due tasks, each marked served, and the expired ones marked so. Those two marks are lazy and change
        nothing this returns, so a read-only attach (the plan's prefetch) reads the same rows and leaves them."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            if not self._read_only:
                lapsed_episodes = {
                    str(row[0]) for row in connection.execute(
                        """
                        SELECT remediation_episode_id FROM followup_tasks
                        WHERE kind = 'cold_retry' AND remediation_episode_id IS NOT NULL
                          AND status IN ('pending', 'served') AND expires_at IS NOT NULL AND expires_at < ?
                        """,
                        (now,),
                    )
                }
                connection.execute(
                    """
                    UPDATE followup_tasks SET status = 'expired', updated_at = ?
                    WHERE status IN ('pending', 'served') AND expires_at IS NOT NULL
                      AND expires_at < ?
                    """,
                    (now, now),
                )
                # The retry the episode reserved its cold item for has ended unanswered.
                for episode_id in sorted(lapsed_episodes):
                    self._release_cold_reservation(connection, episode_id, now)
            rows = connection.execute(
                """
                SELECT * FROM followup_tasks
                WHERE status IN ('pending', 'served') AND not_before <= ?
                  AND (expires_at IS NULL OR expires_at >= ?)
                ORDER BY not_before, created_at, id
                """,
                (now, now),
            ).fetchall()
            if not self._read_only:
                ids = [row["id"] for row in rows if row["status"] == "pending"]
                if ids:
                    placeholders = ",".join("?" for _ in ids)
                    connection.execute(
                        f"UPDATE followup_tasks SET status = 'served', updated_at = ? WHERE id IN ({placeholders})",
                        (now, *ids),
                    )
                connection.commit()
        return [_decode_followup_task(row) | {"status": "served"} for row in rows]

    def active_followup_task_for_item(
        self, practice_item_id: str, *, kind: str | None = None, at: str | None = None
    ) -> dict[str, Any] | None:
        """The due, unconsumed follow-up task selecting ``practice_item_id``.

        ``kind`` (migration 139) narrows to one lane. Since 139 there are two
        lanes queued on the same table, and a caller that means "the cold retry"
        must say so rather than take whichever row sorted first — an unfiltered
        read would let a certification probe answer a remediation question.
        """

        now = at or utc_now_iso()
        clause = "" if kind is None else " AND kind = ?"
        params: tuple[Any, ...] = (
            (practice_item_id, now, now)
            if kind is None
            else (practice_item_id, now, now, kind)
        )
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM followup_tasks
                WHERE selected_item_id = ? AND status IN ('pending', 'served')
                  AND not_before <= ? AND (expires_at IS NULL OR expires_at >= ?)
                  {clause}
                ORDER BY not_before, created_at, id LIMIT 1
                """,
                params,
            ).fetchone()
        return _decode_followup_task(row) if row is not None else None

    def followup_task_for_case(self, *, kind: str, case_ref: str) -> dict[str, Any] | None:
        """Any task of ``kind`` for ``case_ref``, whatever its status.

        The idempotency read behind "one delayed cold probe per certificate, ever"
        (§5.7): a consumed or expired probe must still suppress a second one, so
        this deliberately does NOT filter on status the way
        ``active_followup_task_for_item`` does.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM followup_tasks
                WHERE kind = ? AND case_ref = ?
                ORDER BY created_at, id LIMIT 1
                """,
                (kind, case_ref),
            ).fetchone()
        return _decode_followup_task(row) if row is not None else None

    @staticmethod
    def _release_cold_reservation(connection: Any, episode_id: str, now: str) -> bool:
        """End a ``cold_scheduled`` episode whose cold retry has no open task left, so its cold item
        stops being reserved. An episode with a live retry (a replacement was scheduled) is untouched."""

        cursor = connection.execute(
            """
            UPDATE remediation_episodes SET state = 'abandoned', updated_at = ?
            WHERE id = ? AND state = 'cold_scheduled'
              AND NOT EXISTS (
                SELECT 1 FROM followup_tasks
                WHERE remediation_episode_id = remediation_episodes.id AND kind = 'cold_retry'
                  AND status IN ('pending', 'served'))
            """,
            (now, episode_id),
        )
        return cursor.rowcount > 0

    def release_cold_reservation(self, episode_id: str, *, clock: Clock | None = None) -> bool:
        """:meth:`_release_cold_reservation` for the caller that ended the retry (a withdrawal)."""

        with self.connection() as connection:
            released = self._release_cold_reservation(connection, episode_id, utc_now_iso(clock))
            connection.commit()
        return released

    def _remediation_cold_item_ids(self, *, awaiting_primed: bool) -> set[str]:
        """Cold items of live remediation episodes: those with a cold retry open, and (``awaiting_primed``)
        those still waiting for the primed attempt, before any task exists. An episode that took its primed
        attempt and has no open retry reserves nothing: a retry that was never scheduled has nothing left to
        protect."""

        waiting = "primed_attempt_id IS NULL OR " if awaiting_primed else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT cold_item_id FROM remediation_episodes AS episode
                WHERE cold_item_id IS NOT NULL AND state NOT IN ('completed', 'abandoned')
                  AND ({waiting}EXISTS (
                    SELECT 1 FROM followup_tasks AS task
                    WHERE task.remediation_episode_id = episode.id AND task.kind = 'cold_retry'
                      AND task.status IN ('pending', 'served')))
                """
            ).fetchall()
        return {str(row[0]) for row in rows}

    def open_remediation_cold_item_ids(self) -> set[str]:
        """The wider reservation, for the learner-initiated selectors and the tutor (``find_practice``, the
        quick check, practice admission, AD's slot check, ``cold_administration_open``, protection): the cold
        item is held from the moment the episode chooses it, while its primed attempt is still to be taken."""

        return self._remediation_cold_item_ids(awaiting_primed=True)

    def pending_remediation_cold_item_ids(self) -> set[str]:
        """The narrower reservation Today's routine queue honours: only an open cold retry. An episode whose
        primed attempt is never taken has no lifetime (nothing ends it), and withholding the item from the
        queue without one would take it out of practice indefinitely, so the queue waits for a real check."""

        return self._remediation_cold_item_ids(awaiting_primed=False)

    def open_followup_tasks_of_kind(
        self, kind: str, *, learning_object_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Tasks of ``kind`` still awaiting an attempt (``pending`` or ``served``)."""

        clause = "" if learning_object_id is None else " AND learning_object_id = ?"
        params: tuple[Any, ...] = (
            (kind,) if learning_object_id is None else (kind, learning_object_id)
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM followup_tasks
                WHERE kind = ? AND status IN ('pending', 'served'){clause}
                ORDER BY not_before, created_at, id
                """,
                params,
            ).fetchall()
        return [_decode_followup_task(row) for row in rows]

    def open_followup_tasks_for_item(self, practice_item_id: str) -> list[dict[str, Any]]:
        """Every task of any kind still awaiting an attempt on this item, in
        ``active_followup_task_for_item``'s order (``serve_eligibility`` judges
        them all: the first due one is the task submit answers)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM followup_tasks
                WHERE selected_item_id = ? AND status IN ('pending', 'served')
                ORDER BY not_before, created_at, id
                """,
                (practice_item_id,),
            ).fetchall()
        return [_decode_followup_task(row) for row in rows]

    def followup_tasks_of_kind(self, kind: str) -> list[dict[str, Any]]:
        """Every task of ``kind``, any status — the metric's denominator read."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM followup_tasks WHERE kind = ?
                ORDER BY created_at, id
                """,
                (kind,),
            ).fetchall()
        return [_decode_followup_task(row) for row in rows]

    def expire_followup_task(
        self, task_id: str, *, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        """Retire an un-taken task. Never touches a consumed one.

        Used when the claim a task was scheduled to test no longer stands — a
        withdrawn certificate must not go on to schedule or serve its §5.7 probe.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks SET status = 'expired', updated_at = ?
                WHERE id = ? AND status IN ('pending', 'served')
                """,
                (now, task_id),
            )
            connection.commit()
        return self.followup_task(task_id)

    def defer_followup_task(
        self, task_id: str, *, not_before: str, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        """Push an un-taken task's ``not_before`` later. Never touches expiry.

        The single-use cold measurement is worth more than its promptness: when
        the answer has been shown since the task was created, serving it now
        would burn the one measurement on contaminated evidence. Deferral is a
        push of the earliest serve time only — ``expires_at`` is deliberately
        untouched, so an episode that keeps being revealed runs out its original
        window and censors as ``right_censored_expired`` through the existing
        sweep, which is the honest ending. Monotone (never pulls a task
        earlier) and inert on a consumed or expired row.
        """

        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks SET not_before = ?, updated_at = ?
                WHERE id = ? AND status IN ('pending', 'served')
                  AND not_before < ?
                """,
                (not_before, utc_now_iso(clock), task_id, not_before),
            )
            connection.commit()
        return self.followup_task(task_id)

    def consume_followup_task(
        self, task_id: str, attempt_id: str, *, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE followup_tasks
                SET status = 'consumed', consumed_attempt_id = ?, updated_at = ?
                WHERE id = ? AND status IN ('pending', 'served')
                """,
                (attempt_id, now, task_id),
            )
            connection.commit()
        return self.followup_task(task_id)

    def followup_source_attempt(self, attempt_id: str) -> str | None:
        """Gate-decision attempt whose queued follow-up this attempt answered.

        Mirrors ``pending_followup_practice_items``: the newest earlier
        ``attempt_surprise`` row carrying a queued action for this attempt's
        practice item, with no intervening attempt on that item between the
        gate row and this attempt. None when this attempt is not a follow-up.
        """

        with self.connection() as connection:
            attempt = connection.execute(
                "SELECT practice_item_id, created_at FROM practice_attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
            if attempt is None:
                return None
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.triggered_actions_json, s.created_at
                FROM attempt_surprise s
                WHERE s.triggered_actions_json IS NOT NULL
                  AND s.created_at <= ?
                  AND s.attempt_id != ?
                ORDER BY s.created_at DESC, s.attempt_id DESC
                """,
                (attempt["created_at"], attempt_id),
            ).fetchall()
            for row in rows:
                for action in _loads(row["triggered_actions_json"], []):
                    parsed = _queued_followup_action(action)
                    if parsed is None or parsed[1] != attempt["practice_item_id"]:
                        continue
                    intervening = connection.execute(
                        """
                        SELECT 1 FROM practice_attempts
                        WHERE practice_item_id = ? AND created_at > ? AND created_at < ? AND id != ?
                        LIMIT 1
                        """,
                        (
                            attempt["practice_item_id"],
                            row["created_at"],
                            attempt["created_at"],
                            attempt_id,
                        ),
                    ).fetchone()
                    if intervening is None:
                        return row["attempt_id"]
        return None

    def upsert_followup_rating(
        self,
        *,
        attempt_id: str,
        gate_attempt_id: str | None,
        useful: bool,
        source: str = "user",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO followup_ratings(attempt_id, gate_attempt_id, useful, source, rated_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET
                  gate_attempt_id = excluded.gate_attempt_id,
                  useful = excluded.useful,
                  source = excluded.source,
                  updated_at = excluded.updated_at
                """,
                (attempt_id, gate_attempt_id, 1 if useful else 0, source, now, now),
            )
            connection.commit()

    def followup_rating(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM followup_ratings WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["useful"] = bool(payload["useful"])
        return payload

    def remediation_episodes_created_between(
        self, *, after: str, before: str
    ) -> list[dict[str, Any]]:
        """Episodes CREATED inside the interval, for the prepared-passages scan.

        Creation time is the only trustworthy boundary: `updated_at` is
        overwritten by every later state transition (including the very cold
        completion the scan runs for), and there is no per-passage prescription
        timestamp — which is exactly why passages prepared in-interval land as
        `indeterminate`, never as a silent pass.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM remediation_episodes
                 WHERE created_at > ? AND created_at < ?
                 ORDER BY created_at, id
                """,
                (after, before),
            ).fetchall()
        return [_decode_remediation_episode(row) for row in rows]

    def remediation_episodes_for_case_refs(
        self, case_refs: Sequence[str]
    ) -> list[dict[str, Any]]:
        """Remediation episodes (any state) whose case_ref is in ``case_refs``.

        Engagement probe for the bounded-deferral sweep: an episode existing at
        all — whatever its state — proves the learner (or the TEACH_ME_NOW /
        common-repair path acting for them) engaged the case's repair lane.
        """

        refs = [str(value) for value in case_refs if str(value)]
        if not refs:
            return []
        placeholders = ",".join("?" for _ in refs)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM remediation_episodes
                 WHERE case_ref IN ({placeholders})
                 ORDER BY created_at, id
                """,
                refs,
            ).fetchall()
        return [_decode_remediation_episode(row) for row in rows]

    def consumed_followup_task_for_attempt(
        self, attempt_id: str, *, kind: str | None = None
    ) -> dict[str, Any] | None:
        """The delayed task this attempt discharged, with its carried context.

        Used by the cold-verification wiring (§6.2): the attempt that consumes a
        ``cold_retry`` task is the cold observation, and the task carries the
        source attempt, factor, hypothesis set, repair class and avoided
        affordances resolved when the retry was scheduled.

        ``kind`` (migration 139) pins the lane. One attempt can discharge a task
        in each lane — the same item may be both a remediation cold item and a
        §5.7 certification probe — and an unfiltered read would then return the
        other lane's row, silently skipping the verification this exists for.
        """

        clause = "" if kind is None else " AND kind = ?"
        params: tuple[Any, ...] = (attempt_id,) if kind is None else (attempt_id, kind)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM followup_tasks
                WHERE consumed_attempt_id = ?{clause}
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return _decode_followup_task(row) if row is not None else None
