"""Learner questions, reveals, promotions and claims.

Owns question events and promotion requests, reveal events and learner claims."""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop import hint_window
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import _UNSET
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


def _decode_question_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["facets"] = _loads(payload.pop("facets_json"), [])
    payload["source_context"] = _loads(payload.pop("source_context_json", None), {})
    payload["hint_equivalent"] = bool(payload["hint_equivalent"])
    payload["leak_suspected"] = bool(payload["leak_suspected"])
    # saved_note_id (migration 027) is a plain column and rides along in
    # dict(row); older DBs predating the transcript join surface it as None.
    payload.setdefault("saved_note_id", None)
    # §13.4 context columns (migration 030) ride along in dict(row); default
    # them for rows read before the migration applied.
    payload.setdefault("signal_channel", None)
    # Reveal quantification (migration 154); absent on rows read from a DB that
    # predates the ledger.
    payload.setdefault("leak_overlap", None)
    payload.setdefault("remediation_episode_id", None)
    if payload.get("direct_explanation_request") is not None:
        payload["direct_explanation_request"] = bool(payload["direct_explanation_request"])
    return payload


def _decode_question_promotion(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["attributed_facets"] = _loads(payload.pop("attributed_facets_json"), [])
    attempted = payload.get("attempted_in_thread")
    payload["attempted_in_thread"] = None if attempted is None else bool(attempted)
    return payload


def _decode_question_promotion_request(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["retryable"] = bool(payload.get("retryable"))
    return payload


class QuestionStoreMixin:

    # ── Tutor Q&A question events ─────────────────────────────────────────

    def insert_question_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        """Append a learner question. Q10 (diagnosis input provenance): it
        records the item contract (revision) it was asked about: the one the
        caller names (the item as presented), else, for a question asked
        about a graded attempt, the attempt's pinned contract; None on no
        item.

        RO0's fields (rows 1 to 3: ``reveal_state_json`` and the generating
        process it fills) are never in the row's insert (landing ruling R1):
        they follow in their own savepoint, so a refused receipt leaves the
        question, and the answer it waits for, standing."""

        from learnloop.db.stores import router_objective as receipts

        event, receipt = receipts.split_receipt("question_events", event)
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            contract = event.get("assessment_contract_version_id")
            if contract is None and event.get("attempt_id") and event.get("practice_item_id"):
                from learnloop.db.stores.write_provenance import pinned_contract_ids

                contract = pinned_contract_ids(
                    connection, {str(event["attempt_id"]): str(event["practice_item_id"])}
                ).get(str(event["attempt_id"]))
            if not event.get("practice_item_id"):
                contract = None
            connection.execute(
                """
                INSERT INTO question_events(
                  id, context, note_id, practice_item_id, attempt_id, session_id,
                  question_md, answer_md, question_type, facets_json,
                  hint_equivalent, leak_suspected, rating, seconds_into_attempt,
                  provider, answer_status,
                  preceding_tutor_move, scaffold_level, warning_state, learner_mode,
                  question_opportunity, hints_used_before, direct_explanation_request,
                  attempt_progress, signal_channel, source_context_json, created_at,
                  assessment_contract_version_id, answer_mode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event["context"],
                    event.get("note_id"),
                    event.get("practice_item_id"),
                    event.get("attempt_id"),
                    event.get("session_id"),
                    event["question_md"],
                    event.get("answer_md"),
                    event.get("question_type"),
                    _json(sorted({str(facet) for facet in event.get("facets", [])})),
                    1 if event.get("hint_equivalent") else 0,
                    1 if event.get("leak_suspected") else 0,
                    event.get("rating"),
                    event.get("seconds_into_attempt"),
                    event.get("provider"),
                    event.get("answer_status") or "answered",
                    event.get("preceding_tutor_move"),
                    event.get("scaffold_level"),
                    event.get("warning_state"),
                    event.get("learner_mode"),
                    event.get("question_opportunity"),
                    event.get("hints_used_before"),
                    1 if event.get("direct_explanation_request") else 0,
                    event.get("attempt_progress"),
                    event.get("signal_channel"),
                    (
                        _json(dict(event["source_context"]))
                        if isinstance(event.get("source_context"), Mapping)
                        else None
                    ),
                    now,
                    None if contract is None else str(contract),
                    # Adaptive difficulty AD1 (§5.11, fix round 4, V5): the
                    # reader tutor's answer mode, set once at the ask.
                    event.get("answer_mode"),
                ),
            )
            # RO0 rows 1 to 3, after the row: only a question RO0 read has them. Refused, the question stands without them.
            receipts.fill_receipt(connection, "question_events", event_id, receipt)
            connection.commit()
        return event_id

    def update_question_event_answer(
        self,
        event_id: str,
        *,
        answer_md: str | None,
        question_type: str | None,
        facets: list[str] | None,
        hint_equivalent: bool,
        leak_suspected: bool,
        answer_status: str,
        signal_channel: str | None = None,
        source_context: Mapping[str, Any] | None = None,
        leak_overlap: float | None = None,
        remediation_episode_id: str | None = None,
        answered_at: str | None = None,
    ) -> bool:
        """Complete (or fail) a pending question event after the provider call.

        Second half of the two-phase write: the question row already exists
        with answer_status='pending'; this fills in the answer and the tutor's
        classification (including the §13.4 epistemic vs interaction-preference
        channel), or marks the turn 'failed' while keeping the question text as
        evidence. An answer stamps ``answered_at`` (default: now) once: the
        first completion's time is kept (adaptive difficulty AD1, migration
        213; Codex review F4)."""

        completed = answered_at or utc_now_iso()
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE question_events
                SET answer_md = ?, question_type = ?, facets_json = ?,
                    hint_equivalent = ?, leak_suspected = ?, answer_status = ?,
                    signal_channel = COALESCE(?, signal_channel),
                    source_context_json = COALESCE(?, source_context_json),
                    leak_overlap = COALESCE(?, leak_overlap),
                    remediation_episode_id = COALESCE(?, remediation_episode_id),
                    answered_at = CASE WHEN ? = 'answered' THEN COALESCE(answered_at, ?) ELSE answered_at END
                WHERE id = ?
                """,
                (
                    answer_md,
                    question_type,
                    _json(sorted({str(facet) for facet in facets})) if facets is not None else _json([]),
                    1 if hint_equivalent else 0,
                    1 if leak_suspected else 0,
                    answer_status,
                    signal_channel,
                    _json(dict(source_context)) if source_context is not None else None,
                    leak_overlap,
                    remediation_episode_id,
                    answer_status,
                    completed,
                    event_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        answer_status: str | None = None,
        resolution: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM question_events"
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("context", context),
            ("note_id", note_id),
            ("practice_item_id", practice_item_id),
            ("attempt_id", attempt_id),
            ("session_id", session_id),
            ("answer_status", answer_status),
            ("resolution", resolution),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        if since is not None:
            clauses.append("created_at >= ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at < ?")
            parameters.append(until)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_decode_question_event(row) for row in rows]

    def count_question_events(
        self,
        *,
        context: str | None = None,
        note_id: str | None = None,
        practice_item_id: str | None = None,
        attempt_id: str | None = None,
        session_id: str | None = None,
        since: str | None = None,
        answer_status: str | None = None,
        resolution: str | None = None,
    ) -> int:
        return len(
            self.question_events(
                context=context,
                note_id=note_id,
                practice_item_id=practice_item_id,
                attempt_id=attempt_id,
                session_id=session_id,
                since=since,
                answer_status=answer_status,
                resolution=resolution,
            )
        )

    def question_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_events WHERE id = ?", (event_id,)
            ).fetchone()
        return _decode_question_event(row) if row is not None else None

    def set_question_event_rating(self, event_id: str, *, useful: bool) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET rating = ? WHERE id = ?",
                (1 if useful else 0, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def set_question_event_resolution(self, event_id: str, *, resolution: str) -> bool:
        """Learner-facing queue state (migration 102): open | resolved | dismissed."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET resolution = ? WHERE id = ?",
                (resolution, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def count_hint_equivalent_question_events(
        self,
        practice_item_id: str,
        session_id: str | None,
        *,
        since: str | None = None,
        until: str | None = None,
        item_window_only: bool = False,
    ) -> int:
        """Substantive questions on this item in the hint-equivalence window.

        Questions on this (item, session) newer than ``since`` (typically the
        previous attempt on the item) and, when ``until`` is given, at or before
        it (for reconstructing the count post hoc).

        A Reader question bound to the item by a workbench session
        (``context = 'reader'`` with an item: only RW1c's server-derived
        binding writes one, ``ITEM_WINDOW_QUESTION_CONTEXTS``) counts in the
        ITEM window whatever its practice session, or none: the learner can
        ask before any practice session is open, or in one that ends before
        they submit in the next, and the help is still on the item (RW1c fix
        round 4, F1, the rule RW2b's held help already follows). The window
        start is the item's last attempt, so whichever attempt of the item
        commits next counts it once and the window then moves past it.
        ``item_window_only`` counts only those (a submit that will open its
        own practice session sees no other session's practice rows).

        Deliberately NOT filtered by context. A mechanism question asked from
        the *feedback* screen — where the graded solution is already on screen —
        helps the next attempt on the same item at least as much as the same
        question asked mid-attempt; gating on ``context = 'practice'`` let that
        help land as clean unassisted evidence. ``hint_equivalent`` is set by
        ``tutor_qa.ask_question`` for every context where a practice item is
        bound, so the flag alone carries the policy now."""

        query = (
            "SELECT COUNT(*) AS n FROM question_events "
            "WHERE hint_equivalent = 1 AND practice_item_id = ?"
        )
        parameters: list[Any] = [practice_item_id]
        # The window's session rule, shared with the learner field's link
        # from a question to the attempt it preceded (fix round 5, R3).
        clause, clause_parameters = hint_window.session_clause(session_id, item_window_only=item_window_only)
        query += clause
        parameters.extend(clause_parameters)
        if since is not None:
            query += " AND created_at > ?"
            parameters.append(since)
        if until is not None:
            query += " AND created_at <= ?"
            parameters.append(until)
        with self.connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return int(row["n"]) if row is not None else 0

    # ── Reveal ledger (migration 154) ─────────────────────────────────────

    def insert_reveal_event(
        self, event: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str:
        """Append one answer-exposure entry to the cross-channel reveal ledger.

        Every surface that can hand a learner part of a graded solution writes
        here — tutor answers, repair-suggestion displays, guided redos, source
        review — so the submit path can ask one question ("how much of this
        item's answer has been exposed since the last attempt?") instead of
        re-deriving it per channel."""

        event_id = str(event.get("id") or new_ulid())
        amount = max(0.0, min(1.0, float(event.get("amount") or 0.0)))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO reveal_events(
                  id, practice_item_id, learning_object_id, remediation_episode_id,
                  source_kind, amount, basis, question_event_id, attempt_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    str(event["practice_item_id"]),
                    event.get("learning_object_id"),
                    event.get("remediation_episode_id"),
                    str(event["source_kind"]),
                    amount,
                    event.get("basis"),
                    event.get("question_event_id"),
                    event.get("attempt_id"),
                    event.get("created_at") or utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def reveal_events(
        self,
        *,
        practice_item_id: str | None = None,
        remediation_episode_id: str | None = None,
        source_kind: str | None = None,
        attempt_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("practice_item_id", practice_item_id),
            ("remediation_episode_id", remediation_episode_id),
            ("source_kind", source_kind),
            ("attempt_id", attempt_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        if since is not None:
            clauses.append("created_at > ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at <= ?")
            parameters.append(until)
        query = "SELECT * FROM reveal_events"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def reveal_events_for_target(
        self,
        *,
        practice_item_id: str | None = None,
        learning_object_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reveals on this item OR anywhere in this learning object (OR, not AND).

        The cold lane's question is wider than one item: a reveal on the cold
        item is an answer leak, and a reveal elsewhere in the same learning
        object is material exposure the receipt has to see before it can claim
        isolation. Both arrive in one time-bounded, index-backed read so a
        caller cannot accidentally scan only half of it. Window convention
        matches ``total_reveal_amount``: ``since`` exclusive, ``until``
        inclusive. Ordered oldest first."""

        clauses: list[str] = []
        parameters: list[Any] = []
        targets: list[str] = []
        if practice_item_id is not None:
            targets.append("practice_item_id = ?")
            parameters.append(practice_item_id)
        if learning_object_id is not None:
            targets.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        if not targets:
            return []
        clauses.append("(" + " OR ".join(targets) + ")")
        if since is not None:
            clauses.append("created_at > ?")
            parameters.append(since)
        if until is not None:
            clauses.append("created_at <= ?")
            parameters.append(until)
        query = (
            "SELECT * FROM reveal_events WHERE "
            + " AND ".join(clauses)
            + " ORDER BY created_at, id"
        )
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def total_reveal_amount(
        self,
        practice_item_id: str,
        *,
        since: str | None = None,
        until: str | None = None,
        linked_attempt_id: str | None = None,
        linked_kinds: Sequence[str] = (),
        routine_basis_prefixes: Sequence[str] = (),
        routine_covered_from: str | None = None,
    ) -> float:
        """Summed reveal amount for one item in a window.

        Same window convention as
        ``count_hint_equivalent_question_events``: ``since`` is exclusive (the
        previous attempt's timestamp, whose evidence already absorbed anything
        before it) and ``until`` is inclusive.

        ``linked_attempt_id``/``linked_kinds``: rows of those kinds linked to
        that attempt (the one at ``since``) were written after it by
        construction, so they count even when stamped in its own second.

        ``routine_basis_prefixes``/``routine_covered_from`` (UX Phase 4): an
        ``answer_display`` row whose basis starts with one of the prefixes (the
        plain surface's routine displays) counts by its coverage instead of the
        window: when stamped at or after ``routine_covered_from``, whatever
        attempts came between (a full answer still on screen after the last
        attempt is an exposure for the next). Every other row keeps the window.
        A submission's own disclosure is subtracted by the caller, which parses
        each row's identity (``reveal_ledger.is_own_disclosure``)."""

        def prefix_match(prefixes: Sequence[str]) -> tuple[str, list[Any]]:
            # A prefix match without LIKE (its "_" is a wildcard).
            clause = " OR ".join("substr(COALESCE(basis, ''), 1, ?) = ?" for _ in prefixes)
            values: list[Any] = []
            for prefix in prefixes:
                values.extend([len(prefix), prefix])
            return clause, values

        window = ""
        window_parameters: list[Any] = []
        if since is not None and linked_attempt_id is not None and linked_kinds:
            marks = ", ".join("?" for _ in linked_kinds)
            window = "(created_at > ? OR (attempt_id = ? AND source_kind IN (" + marks + ") AND created_at >= ?))"
            window_parameters = [since, linked_attempt_id, *linked_kinds, since]
        elif since is not None:
            window = "created_at > ?"
            window_parameters = [since]

        query = "SELECT COALESCE(SUM(amount), 0.0) AS total FROM reveal_events WHERE practice_item_id = ?"
        parameters: list[Any] = [practice_item_id]
        if until is not None:
            query += " AND created_at <= ?"
            parameters.append(until)
        if routine_basis_prefixes and routine_covered_from is not None:
            routine_clause, routine_values = prefix_match(routine_basis_prefixes)
            routine = f"(source_kind = 'answer_display' AND ({routine_clause}))"
            query += (
                f" AND (({routine} AND created_at >= ?)"
                f" OR (NOT {routine}" + (f" AND {window}" if window else "") + "))"
            )
            parameters.extend([*routine_values, routine_covered_from, *routine_values, *window_parameters])
        elif window:
            query += f" AND {window}"
            parameters.extend(window_parameters)
        with self.connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return float(row["total"]) if row is not None else 0.0

    def question_counts_by_facet(self) -> dict[str, int]:
        """Total question_events touching each classified facet."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT facets_json FROM question_events WHERE facets_json IS NOT NULL"
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for facet in _loads(row["facets_json"], []):
                counts[str(facet)] = counts.get(str(facet), 0) + 1
        return counts

    def set_question_event_saved_note(self, event_id: str, note_id: str | None) -> bool:
        """Persist the tutor-turn -> saved-note link (migration 027, spec §5).

        Written by ``save_tutor_answer_note`` so the "saved" UI state survives a
        remount and ``get_tutor_transcript`` can surface it."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE question_events SET saved_note_id = ? WHERE id = ?",
                (note_id, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    # --- question_promotions (spec_tutor_promotion.md §5) ----------------------

    def insert_question_promotion(
        self,
        *,
        question_event_id: str,
        intent: str,
        route: str,
        attributed_facets: list[str] | None = None,
        question_nature: str | None = None,
        attempted_in_thread: bool | None = None,
        learner_claim_id: str | None = None,
        intervention_need_id: str | None = None,
        proposed_patch_id: str | None = None,
        saved_note_id: str | None = None,
        existing_practice_item_id: str | None = None,
        created_practice_item_id: str | None = None,
        created_learning_object_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert the promotion ledger row for a tutor turn (§4 step 4).

        Idempotency is the caller's contract: the PK is ``question_event_id``,
        so re-promoting an already-promoted turn raises IntegrityError — the
        promotion service checks ``question_promotion(event_id)`` first."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_promotions(
                  question_event_id, intent, attributed_facets_json, question_nature,
                  attempted_in_thread, learner_claim_id, intervention_need_id,
                  proposed_patch_id, saved_note_id, existing_practice_item_id,
                  created_practice_item_id, created_learning_object_id, route,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    question_event_id,
                    intent,
                    _json(list(attributed_facets)) if attributed_facets is not None else None,
                    question_nature,
                    None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
                    learner_claim_id,
                    intervention_need_id,
                    proposed_patch_id,
                    saved_note_id,
                    existing_practice_item_id,
                    created_practice_item_id,
                    created_learning_object_id,
                    route,
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_event_id

    def update_question_promotion(
        self,
        question_event_id: str,
        *,
        route: Any = _UNSET,
        attributed_facets: Any = _UNSET,
        question_nature: Any = _UNSET,
        attempted_in_thread: Any = _UNSET,
        learner_claim_id: Any = _UNSET,
        intervention_need_id: Any = _UNSET,
        proposed_patch_id: Any = _UNSET,
        saved_note_id: Any = _UNSET,
        existing_practice_item_id: Any = _UNSET,
        created_practice_item_id: Any = _UNSET,
        created_learning_object_id: Any = _UNSET,
        clock: Clock | None = None,
    ) -> bool:
        """Fill created ids / transition the route on an existing promotion row.

        Only the supplied fields are written (``_UNSET`` sentinel distinguishes
        "leave unchanged" from an explicit ``None``); ``updated_at`` always
        advances."""

        assignments: list[str] = []
        parameters: list[Any] = []

        def _set(column: str, value: Any) -> None:
            assignments.append(f"{column} = ?")
            parameters.append(value)

        if route is not _UNSET:
            _set("route", route)
        if attributed_facets is not _UNSET:
            _set(
                "attributed_facets_json",
                _json(list(attributed_facets)) if attributed_facets is not None else None,
            )
        if question_nature is not _UNSET:
            _set("question_nature", question_nature)
        if attempted_in_thread is not _UNSET:
            _set(
                "attempted_in_thread",
                None if attempted_in_thread is None else (1 if attempted_in_thread else 0),
            )
        if learner_claim_id is not _UNSET:
            _set("learner_claim_id", learner_claim_id)
        if intervention_need_id is not _UNSET:
            _set("intervention_need_id", intervention_need_id)
        if proposed_patch_id is not _UNSET:
            _set("proposed_patch_id", proposed_patch_id)
        if saved_note_id is not _UNSET:
            _set("saved_note_id", saved_note_id)
        if existing_practice_item_id is not _UNSET:
            _set("existing_practice_item_id", existing_practice_item_id)
        if created_practice_item_id is not _UNSET:
            _set("created_practice_item_id", created_practice_item_id)
        if created_learning_object_id is not _UNSET:
            _set("created_learning_object_id", created_learning_object_id)

        _set("updated_at", utc_now_iso(clock))
        parameters.append(question_event_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE question_promotions SET {', '.join(assignments)} WHERE question_event_id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def question_promotion(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM question_promotions WHERE question_event_id = ?",
                (event_id,),
            ).fetchone()
        return _decode_question_promotion(row) if row is not None else None

    def question_promotions(self) -> list[dict[str, Any]]:
        """All promotion rows, oldest first (requested-floor + signal joins)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM question_promotions ORDER BY created_at, question_event_id"
            ).fetchall()
        return [_decode_question_promotion(row) for row in rows]

    def question_promotions_for_events(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Promotion rows keyed by question_event_id, for the tutor transcript.

        Returns a dict so the transcript can attach promotion state per turn in
        one query (empty when no ids are given)."""

        ids = [str(event_id) for event_id in event_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM question_promotions WHERE question_event_id IN ({placeholders})",
                ids,
            ).fetchall()
        return {row["question_event_id"]: _decode_question_promotion(row) for row in rows}

    def question_promotions_for_patch(self, patch_id: str) -> list[dict[str, Any]]:
        """Promotion rows awaiting or completed through one proposal patch."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM question_promotions
                WHERE proposed_patch_id = ?
                ORDER BY created_at, question_event_id
                """,
                (patch_id,),
            ).fetchall()
        return [_decode_question_promotion(row) for row in rows]

    # --- durable question-promotion requests (migration 117) ------------------

    def insert_question_promotion_request(
        self,
        *,
        question_event_id: str,
        intent: str,
        subject_id: str | None = None,
        learning_object_id: str | None = None,
        status: str = "queued",
        stage: str = "queued",
        batch_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO question_promotion_requests(
                  question_event_id, intent, subject_id, learning_object_id,
                  status, stage, batch_id, promotion_route, error_code,
                  error_message, retryable, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 0, ?, ?)
                """,
                (
                    question_event_id,
                    intent,
                    subject_id,
                    learning_object_id,
                    status,
                    stage,
                    batch_id,
                    now,
                    now,
                ),
            )
            connection.commit()
        return question_event_id

    def update_question_promotion_request(
        self,
        question_event_id: str,
        *,
        status: Any = _UNSET,
        stage: Any = _UNSET,
        batch_id: Any = _UNSET,
        promotion_route: Any = _UNSET,
        error_code: Any = _UNSET,
        error_message: Any = _UNSET,
        retryable: Any = _UNSET,
        subject_id: Any = _UNSET,
        learning_object_id: Any = _UNSET,
        clock: Clock | None = None,
    ) -> bool:
        assignments: list[str] = []
        parameters: list[Any] = []

        def _set(column: str, value: Any) -> None:
            assignments.append(f"{column} = ?")
            parameters.append(value)

        for column, value in (
            ("status", status),
            ("stage", stage),
            ("batch_id", batch_id),
            ("promotion_route", promotion_route),
            ("error_code", error_code),
            ("error_message", error_message),
            ("subject_id", subject_id),
            ("learning_object_id", learning_object_id),
        ):
            if value is not _UNSET:
                _set(column, value)
        if retryable is not _UNSET:
            _set("retryable", 1 if retryable else 0)
        _set("updated_at", utc_now_iso(clock))
        parameters.append(question_event_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE question_promotion_requests
                SET {', '.join(assignments)}
                WHERE question_event_id = ?
                """,
                parameters,
            )
            connection.commit()
        return cursor.rowcount > 0

    def question_promotion_request(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM question_promotion_requests
                WHERE question_event_id = ?
                """,
                (event_id,),
            ).fetchone()
        return _decode_question_promotion_request(row) if row is not None else None

    def question_promotion_requests_for_events(
        self, event_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        ids = [str(event_id) for event_id in event_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM question_promotion_requests
                WHERE question_event_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
        return {
            row["question_event_id"]: _decode_question_promotion_request(row)
            for row in rows
        }

    def retry_question_promotion_request(
        self, event_id: str, *, clock: Clock | None = None
    ) -> bool:
        """Re-open a failed durable request without losing its selected target."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE question_promotion_requests
                SET status = 'queued',
                    stage = 'queued',
                    promotion_route = NULL,
                    error_code = NULL,
                    error_message = NULL,
                    retryable = 0,
                    updated_at = ?
                WHERE question_event_id = ? AND status = 'failed'
                """,
                (utc_now_iso(clock), event_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def insert_learner_claim(self, claim: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        claim_id = str(claim.get("id") or new_ulid())
        created_at = str(claim.get("created_at") or utc_now_iso(clock))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learner_claims(
                  id, claim_type, scope_type, scope_id, evidence_family,
                  claimed_level, prior_pseudo_count, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    claim["claim_type"],
                    claim["scope_type"],
                    claim.get("scope_id"),
                    claim.get("evidence_family"),
                    claim["claimed_level"],
                    claim["prior_pseudo_count"],
                    claim["source"],
                    created_at,
                ),
            )
            connection.commit()
        return claim_id

    def learner_claims(self, *, include_superseded: bool = False) -> list[dict[str, Any]]:
        """The claims in force (newest first); ``include_superseded`` adds the replaced ones.

        A claim another claim replaced (``superseded_by``, successor mvp-0.36,
        migration 225) is kept for replay only: every live reader reads the
        claims in force, which are exactly the rows the predecessor's replace
        seam left (it deleted the replaced ones). Replay passes
        ``include_superseded`` and applies each claim at its own point."""

        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM learner_claims ORDER BY created_at DESC, id").fetchall()
        claims = [dict(row) for row in rows]
        if include_superseded:
            return claims
        # Filtered here, not in SQL: a database attached below migration 225 has no such column.
        return [claim for claim in claims if claim.get("superseded_by") is None]

    def replace_learner_claim(
        self,
        claim: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str:
        """The replace seam: ``claim`` replaces the in-force claims of its source on its scope; its id.

        One source keeps one claim in force per scope (init-wizard global
        claims, rung-variant requests and too-easy/too-hard reports per LO).
        The replaced rows stay (the successor mvp-0.36), marked
        ``superseded_by`` the new claim's id in the transaction that inserts
        it, so replay can apply each at its own time."""

        with self.atomic():
            claim_id = self.insert_learner_claim(claim, clock=clock)
            query = (
                "UPDATE learner_claims SET superseded_by = ? WHERE source = ? AND scope_type = ? "
                "AND superseded_by IS NULL AND id <> ?"
            )
            params: list[Any] = [claim_id, claim["source"], claim["scope_type"], claim_id]
            if claim.get("scope_id") is not None:
                query += " AND scope_id = ?"
                params.append(claim["scope_id"])
            with self.connection() as connection:
                connection.execute(query, params)
                connection.commit()
        return claim_id

    def delete_learner_claims(
        self, *, source: str, scope_type: str, scope_id: str | None = None
    ) -> int:
        """Delete claims by (source, scope_type[, scope_id]) — the replace seam
        for init-wizard (global) and rung-variant (per-LO) re-claims.

        Below the claim-fixes successor ``covering_learner_claim`` breaks
        specificity ties by pseudo-count, then highest claimed_level, so
        re-seeding a LOWER level must remove the old row rather than append
        beside it. (From the successor on the newest claim wins the tie; the
        replace seam stays, so one source keeps one row per scope.)
        """

        query = "DELETE FROM learner_claims WHERE source = ? AND scope_type = ?"
        params: list[Any] = [source, scope_type]
        if scope_id is not None:
            query += " AND scope_id = ?"
            params.append(scope_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
        return cursor.rowcount
