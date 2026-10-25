"""Router R2a: gathering ``LearnerStateCardV1``'s inputs at a plan boundary.

The pure builder is :mod:`learnloop.router.card`; this module reads the
ledger for one decision, strictly before the decision time, and applies the
card's leakage rules (plan §3.6, gate G5) before anything is rendered. Its
reads scale with the card's topics (at most ``LEARNING_OBJECT_LIMIT``), never
with the candidate items: the attempt history of those topics is read in full
(for the evidence counts), the held-grade predicate reads it in 500-attempt
chunks, and the headline classification reads each topic's certification.

**The protection is shared** with the chat frontend's read model
(``learnloop.learner_protection``, one authority; converged at the chat
frontend's landing, Q16 of docs/reviews/mcp-c1a-narrow.md). Only the card's
text rule is its own (:class:`CardText`, G5): its reader is the router model,
which reads the learner's own answers and the statements LearnLoop's
diagnosers wrote; the chat's rule (``learner_context.TextGuard``) shows far
less.

* it never reads a reference solution, an answer key, a rubric or source text;
* a candidate item contributes its topic, minutes and kind only (no stem of
  an item the learner has not attempted);
* past work on protected material keeps its result but shows no question and
  no answer, naming why (``learner_protection.withheld_items`` and
  ``attempt_protection``): exam material by the one exam predicate
  (``content.sources.exam_material.item_exam_status``: an item reserved for a
  goal's held-out exam, or one whose own source is exam material, every
  ``held_out_evaluation`` unit included) and exam work, a surface holding a
  live assessment reservation, an item an open cold check or a repair's cold
  retry holds, a diagnostic probe, and an item the vault cannot read, whatever
  ``goals.held_out_selection`` says (a model-context protection, never
  switched); when the predicates cannot be read, no past work shows a
  question or an answer (fail closed);
* a statement written from protected work (a cause whose episode rests on an
  exam answer, a learner's words about a probe) keeps its entry and never its
  words (``learner_protection.statement_text``);
* a grade held for review (THE predicate, ``held_grades``) is "held for
  review", never a score;
* an answer on an unverified key says so (``reference_status``);
* past work shows the question the learner answered: the prompt of the
  attempt's pinned assessment contract (the revision it was graded against),
  never today's edited prompt; an attempt whose revision cannot be
  established shows no question (review F6). A contract that froze a
  required method shows its instruction ("Use {method} in your answer."),
  rendered from the frozen field after the statement and kept whole when the
  question is shortened (``learner_protection.PinnedContract.question``).

A topic is ``demonstrated`` or ``assumed`` only by the Today headline's
classification (capability-matched, unassisted certification credit; open
placement assumptions); other attempted topics are ``attempted_not_demonstrated``
or ``assisted_only`` (review F7). Open problems use the daily plan's own
resolution predicate (review F8).

Confidence (teacher TE0, spec_teacher_v1 §15.2): each shown attempt carries
its confidence event (its tap and the grader's hedge read with its result,
rendered by ``learnloop.confidence_events``), the candidate topics' events in
the 7-day window are listed, and the limit is stated when the taps so far do
not span the scale. A protected attempt keeps its result here, so its event
(which names no question and no answer) stays with it. Each topic lists at
most ``confidence_events.CONTEXT_EVENT_LIMIT`` events (newest first; the rest
are counted in ``confidence_omitted``), and every read is in one snapshot, so
an attempt's result and its hedge read are one revision's (review F2, F3).
With the kill switch ``teacher.confidence_events_enabled`` off nothing is
read and the card is the predecessor's (review F5).

A section that cannot be read is named in ``unknowns`` rather than guessed.
Read-only; nothing is written and no model is called.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import timedelta
from math import exp, log, sqrt
from typing import Any

from learnloop import confidence_events
from learnloop import learner_protection as protection
from learnloop.clock import parse_utc
from learnloop.daily_plan.types import BlockCandidate, PlanState
from learnloop.db.stores.write_provenance import read_snapshot
from learnloop.learner_protection import PastWork, Withheld, attempt_result, past_work_text, statement_text
from learnloop.router.card import (
    EXCERPT_LIMIT,
    STATEMENT_LIMIT,
    STEM_LIMIT,
    CardInputs,
    LearnerStateCard,
    build_card,
    excerpt,
)

_LOG = logging.getLogger(__name__)

#: Past graded attempts considered before the budget (newest first).
RECENT_WORK_LIMIT = 30
#: Learning objects described (the candidates' first, then their prerequisites).
LEARNING_OBJECT_LIMIT = 40
OPEN_PROBLEM_LIMIT = 20
SELF_REPORT_LIMIT = 10
NOT_RECORDED = "the timing of ordinary hints (each attempt keeps only its total)"


def _sigmoid(value: float) -> float:
    value = max(-700.0, min(700.0, value))
    return 1.0 / (1.0 + exp(-value))


def _logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return log(p / (1 - p))


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def _status(klass: str | None, counts: Mapping[str, int] | None) -> str:
    """A topic's status on the card (review F7).

    ``demonstrated`` and ``assumed`` come only from the Today headline's
    classification (``klass``; None when it could not be read). Otherwise a
    topic with past attempts is ``assisted_only`` when every one was assisted
    (hints or a primed redo) and ``attempted_not_demonstrated`` when not: a
    graded attempt is never a demonstration. With no attempts here, the
    headline's ``learning`` (direct evidence recorded elsewhere) stands, and
    anything else is ``untested``."""

    if klass in ("demonstrated", "assumed"):
        return klass
    if counts and counts.get("attempts"):
        return "assisted_only" if counts.get("assisted", 0) >= counts["attempts"] else "attempted_not_demonstrated"
    return "learning" if klass == "learning" else "untested"


class CardText:
    """The card's text rule (plan §3.6, gate G5), a parameter of the shared
    protection (``learner_protection.TextRule``). It is asked only once the
    shared protection has passed: the router model reads the question as
    graded (:meth:`question`), the learner's own answer whole (the builder
    shortens it) and a statement as LearnLoop wrote it."""

    def __init__(self, past: PastWork) -> None:
        self.past = past

    def question(self, attempt_id: str, lo_id: Any) -> tuple[str | None, str | None]:
        pin = self.past.pinned(attempt_id)
        question = pin.question(STEM_LIMIT, excerpt) if pin is not None else None
        return (question, None) if question else (None, protection.STEM_UNRECORDED)

    def answer(self, attempt_id: str, text: Any, limit: int) -> tuple[str | None, str | None]:
        # Whole: the builder shortens it to ``limit`` (and drops older ones first).
        return (text or None), None

    def statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Any = (), items: Any = (),
                  los: Any = ()) -> tuple[str | None, str | None]:
        return excerpt(text, limit), None


class CardGatherer:
    """Builds the card for one plan decision (``StagedChooser.card_builder``)."""

    def __init__(self, vault: Any, repository: Any, *, clock: Any = None, session_id: str | None = None) -> None:
        self.vault = vault
        self.repository = repository
        self.clock = clock
        self.session_id = session_id

    def __call__(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> LearnerStateCard:
        from learnloop.clock import utc_now_iso

        inputs = self.inputs(state, feasible, now_iso=utc_now_iso(self.clock))
        budget = int(getattr(self.vault.config.router, "card_token_budget", 16_000))
        return build_card(inputs, token_budget=budget)

    # -- the inputs -------------------------------------------------------------

    def inputs(self, state: PlanState, feasible: Sequence[BlockCandidate], *, now_iso: str) -> CardInputs:
        vault = self.vault
        titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
        candidate_los = list(dict.fromkeys(lo for candidate in feasible for lo in candidate.learning_object_ids))
        neighbours: list[str] = []
        for lo_id in candidate_los:
            learning_object = vault.learning_objects.get(lo_id)
            for prerequisite in getattr(learning_object, "prerequisites", None) or ():
                if prerequisite in vault.learning_objects and prerequisite not in candidate_los:
                    neighbours.append(prerequisite)
        los = list(dict.fromkeys(candidate_los + neighbours))[:LEARNING_OBJECT_LIMIT]
        unknowns: list[str] = [f"not recorded: {NOT_RECORDED}"]
        # The shared protection (learner_protection): the withheld items, by the
        # one exam predicate and the rest (unavailable: nothing shows).
        withheld = self._withheld_items(unknowns)
        confidence_on = confidence_events.enabled(vault)
        # One read snapshot (TE0 review F2): an attempt's result, its held
        # status and its hedge read are one committed revision's.
        with self.repository.connection() as connection, read_snapshot(connection):
            past = PastWork(connection, vault, self.repository, withheld=withheld, unknowns=unknowns)
            rule = CardText(past)
            as_of = connection.execute(
                "SELECT id FROM practice_attempts WHERE created_at < ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (now_iso,),
            ).fetchone()
            attempts = self._attempts(connection, los, now_iso)
            held = past.held([row["id"] for row in attempts])
            learning_objects = self._learning_objects(los, candidate_los, attempts, held, feasible, titles, now_iso,
                                                      unknowns)
            interaction = self._interaction(connection, now_iso, unknowns)
            hypotheses = self._open_problems(connection, set(los), titles, unknowns, past, rule)
            reports = self._self_reports(connection, set(los), titles, now_iso, unknowns)
            evidence_sections = self._evidence_sections(connection, los, titles, now_iso, withheld, unknowns)
            recent = self._recent_work(attempts, held, past, rule, titles)
            confidence_7d, confidence_limit, confidence_omitted = (
                self._confidence(connection, attempts, candidate_los, recent, held, now_iso, unknowns)
                if confidence_on else ({}, None, 0))
        candidates = [self._candidate(candidate, titles) for candidate in feasible]
        session = {
            "plan_id": state.plan_id,
            "plan_kind": state.kind,
            "minutes_budget": round(float(state.minutes_budget), 2),
            "minutes_left": round(float(state.minutes_left), 2),
            "lane_minutes_left": {lane: round(float(value), 2) for lane, value in sorted(state.lane_minutes_left.items())},
            "items_left": state.items_left,
            "days_since_last_activity": state.days_since_last_activity,
            "streak_days": state.streak_days,
            "reentry": state.kind == "reentry",
            "in_session": self.session_id is not None,
        }
        intent = {
            lo: {"choice": view.choice, "disposition": view.disposition, "recall_target": view.recall_target,
                 "deadline": view.deadline}
            for lo, view in sorted((state.intents or {}).items()) if lo in candidate_los
        }
        decision = {
            "surface": "daily_plan",
            "decided_at": now_iso,
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "as_of_attempt_id": as_of["id"] if as_of is not None else None,
        }
        return CardInputs(
            decision=decision,
            session=session,
            intent=intent,
            candidates=candidates,
            learning_objects=learning_objects,
            interaction_7d=interaction,
            open_hypotheses=hypotheses,
            unknowns=unknowns,
            self_reports=reports,
            recent_work=recent,
            evidence_sections=evidence_sections,
            confidence_7d=confidence_7d,
            confidence_limit=confidence_limit,
            confidence_omitted=confidence_omitted,
            confidence_enabled=confidence_on,
        )

    @staticmethod
    def _confidence(
        connection: Any, attempts: Sequence[Mapping[str, Any]], candidate_los: Sequence[str],
        recent: list[dict[str, Any]], held: frozenset[str], now_iso: str, unknowns: list[str],
    ) -> tuple[dict[str, list[dict[str, Any]]], str | None, int]:
        """TE0 (spec_teacher_v1 §15.2): the confidence events. Each shown
        attempt gains its event (``recent``, in place), the candidate topics'
        events in the 7-day window are returned by topic, and the stated limit.
        An attempt with neither a tap nor a hedge read has no event; nothing
        here is a count or a threshold. Each topic keeps its newest
        ``CONTEXT_EVENT_LIMIT`` events (a prompt-size bound, ``keep``); the
        number left out is returned with them."""

        now = parse_utc(now_iso)
        since = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ") if now is not None else None
        candidates = set(candidate_los)
        window = [row for row in attempts if since is not None and str(row["created_at"]) >= since
                  and str(row["learning_object_id"]) in candidates]
        shown = {entry["attempt_id"] for entry in recent}
        wanted = [row for row in attempts if row["id"] in shown] + window
        try:
            found = confidence_events.readings(connection, wanted)
            taps = confidence_events.taps_before(connection, now_iso)
        except Exception:  # noqa: BLE001 - named as unknown, never guessed
            _LOG.warning("router card: confidence not read", exc_info=True)
            unknowns.append("confidence taps and the grader's hedge reads could not be read")
            return {}, None, 0
        for entry in recent:
            event = confidence_events.event_text(found.get(str(entry["attempt_id"])), str(entry["result"]))
            if event:
                entry["confidence"] = event
        by_lo: dict[str, list[dict[str, Any]]] = {}
        omitted = 0
        for row in window:  # newest first
            result = attempt_result(row["correctness"], row["id"] in held)
            event = confidence_events.event_text(found.get(str(row["id"])), result)
            if not event:
                continue
            bucket = by_lo.setdefault(str(row["learning_object_id"]), [])
            if len(bucket) >= confidence_events.CONTEXT_EVENT_LIMIT:
                omitted += 1
                continue
            bucket.append({"attempt_id": row["id"], "at": row["created_at"], "event": event})
        return by_lo, confidence_events.taps_limit(taps), omitted

    @staticmethod
    def _evidence_sections(connection: Any, los: Sequence[str], titles: Mapping[str, str], now_iso: str,
                           withheld: Withheld, unknowns: list[str]) -> dict[str, Any]:
        """The typed evidence registry (R2a's hook). Router R2c: teach-back summaries."""

        sections: dict[str, Any] = {}
        try:
            from learnloop.daily_plan import router_teach_back

            summaries = router_teach_back.summaries_for(connection, los, before=now_iso, withheld=withheld,
                                                         titles=titles)
        except Exception:  # noqa: BLE001 - a section that cannot be read is named, never guessed
            unknowns.append("teach-back summaries could not be read")
            summaries = []
        if summaries:
            sections[router_teach_back.SECTION] = summaries
        return sections

    # -- sections -----------------------------------------------------------------

    @staticmethod
    def _candidate(candidate: BlockCandidate, titles: Mapping[str, str]) -> dict[str, Any]:
        notes = dict(candidate.annotations or {})
        return {
            "ref": candidate.candidate_id,
            "lane": candidate.lane,
            "kind": candidate.action + (f"/{candidate.subtype}" if candidate.subtype else ""),
            "est_minutes": round(float(candidate.est_minutes), 2),
            "item_count": len(candidate.item_ids),
            "topics": [titles.get(lo, lo) for lo in candidate.learning_object_ids],
            "learning_object_ids": list(candidate.learning_object_ids),
            "section": candidate.reading.section_title if candidate.reading is not None else None,
            "reversible": bool(notes.get("reversible", True)),
            "reason_code": notes.get("reason_code"),
            "ladder": notes.get("ladder"),
        }

    def _attempts(self, connection: Any, los: Sequence[str], now_iso: str) -> list[dict[str, Any]]:
        if not los:
            return []
        columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")}
        status = "reference_status" if "reference_status" in columns else "NULL AS reference_status"
        tap = "answer_confidence" if "answer_confidence" in columns else "NULL AS answer_confidence"
        rows = connection.execute(
            f"SELECT id, practice_item_id, learning_object_id, practice_mode, attempt_type, correctness, hints_used, "
            f"primed, learner_answer_md, created_at, {status}, {tap} FROM practice_attempts "
            f"WHERE learning_object_id IN ({_marks(los)}) AND created_at < ? ORDER BY created_at DESC, id DESC",
            (*los, now_iso),
        ).fetchall()
        return [dict(row) for row in rows]

    def _classes(self, los: Sequence[str], now_iso: str, unknowns: list[str]) -> dict[str, str] | None:
        """The Today headline's class of each LO (review F7), or None when it
        cannot be read (then no topic is demonstrated or assumed)."""

        from learnloop.daily_plan import headline

        try:
            return headline.classify_learning_objects(
                self.vault, self.repository, now=parse_utc(now_iso), learning_object_ids=los,
            )
        except Exception:  # noqa: BLE001 - named as unknown; fail closed
            _LOG.warning("router R2a card: topic classes not read", exc_info=True)
            unknowns.append("which topics are demonstrated could not be read: none is shown as demonstrated")
            return None

    def _learning_objects(
        self, los: Sequence[str], candidate_los: Sequence[str], attempts: Sequence[Mapping[str, Any]],
        held: frozenset[str], feasible: Sequence[BlockCandidate], titles: Mapping[str, str], now_iso: str,
        unknowns: list[str],
    ) -> dict[str, dict[str, Any]]:
        vault = self.vault
        evidence: dict[str, dict[str, int]] = {}
        last: dict[str, str] = {}
        for row in attempts:
            lo = str(row["learning_object_id"])
            counts = evidence.setdefault(lo, {"attempts": 0, "graded": 0, "correct": 0, "partial": 0, "incorrect": 0,
                                              "held": 0, "assisted": 0})
            counts["attempts"] += 1
            result = attempt_result(row["correctness"], row["id"] in held)
            if result == "held_for_review":
                counts["held"] += 1
            elif result != "not_graded":
                counts["graded"] += 1
                counts[result] += 1
            if int(row.get("hints_used") or 0) > 0 or bool(row.get("primed")):
                counts["assisted"] += 1
            last.setdefault(lo, str(row["created_at"]))
        classes = self._classes(los, now_iso, unknowns)
        # The candidate items each LO is offered through, for the predictor and FSRS.
        items_by_lo: dict[str, list[str]] = {}
        for candidate in feasible:
            for item_id in candidate.item_ids:
                item = vault.practice_items.get(item_id)
                if item is not None:
                    items_by_lo.setdefault(item.learning_object_id, []).append(item_id)
        predictor = None
        try:
            from learnloop.placement.predictor import active_predictor

            predictor = active_predictor(vault, self.repository, now_iso=now_iso)
        except Exception:  # noqa: BLE001 - named as unknown
            unknowns.append("the learner predictor is unavailable: no predicted success is shown")
        states = self.repository.practice_item_states()
        now = parse_utc(now_iso)
        out: dict[str, dict[str, Any]] = {}
        for lo in los:
            counts = evidence.get(lo)
            status = _status((classes or {}).get(lo), counts)
            row: dict[str, Any] = {
                "title": titles.get(lo, lo),
                "role": "candidate" if lo in candidate_los else "prerequisite",
                "status": status,
                "evidence": counts or {},
                "last_attempt_at": last.get(lo),
            }
            probe_item = (items_by_lo.get(lo) or [None])[0]
            if predictor is not None and probe_item is not None:
                try:
                    prediction = predictor.predict_item(probe_item)
                    spread = 1.96 * sqrt(max(float(prediction.logit_variance), 0.0))
                    centre = _logit(float(prediction.p_success))
                    row["predictor"] = {
                        "p_success": round(float(prediction.p_success), 4),
                        "low": round(_sigmoid(centre - spread), 4),
                        "high": round(_sigmoid(centre + spread), 4),
                        "item": probe_item,
                    }
                except Exception:  # noqa: BLE001 - this LO only
                    row["predictor"] = None
            recalls = []
            for item_id in items_by_lo.get(lo) or ():
                state = states.get(item_id)
                stability = getattr(state, "stability", None)
                last_at = parse_utc(getattr(state, "last_attempt_at", None)) if state is not None else None
                if stability and last_at is not None and now is not None:
                    from learnloop.scheduling.fsrs import forgetting_curve

                    elapsed = max((now - last_at).total_seconds() / 86400.0, 0.0)
                    recalls.append(forgetting_curve(float(stability), elapsed))
            if recalls:
                row["recall_now"] = round(sum(recalls) / len(recalls), 4)
            ad_fields = self._adaptive_difficulty(lo, unknowns)
            if ad_fields is not None:
                # Adaptive difficulty AD2+AD3 (spec §10.1): the subject view's
                # readiness numbers, labelled as predictions, with
                # promoted_predictor on; absent otherwise (the card unchanged).
                row["adaptive_difficulty"] = ad_fields
            out[lo] = row
            if status == "untested" and lo in candidate_los:
                unknowns.append(f"never tested: {titles.get(lo, lo)}")
            elif status == "assumed":
                unknowns.append(f"assumed known (not demonstrated): {titles.get(lo, lo)}")
        return out

    def _adaptive_difficulty(self, lo: str, unknowns: list[str]) -> dict[str, Any] | None:
        from learnloop.adaptive_difficulty.successor import subject_view_live

        if not subject_view_live(self.vault.config):
            return None
        try:
            from learnloop.adaptive_difficulty.readiness import card_fields

            return card_fields(self.vault, self.repository, lo)
        except Exception:  # noqa: BLE001 - named as unknown
            if "adaptive difficulty's predictions are unavailable" not in unknowns:
                unknowns.append("adaptive difficulty's predictions are unavailable")
            return None

    def _interaction(self, connection: Any, now_iso: str, unknowns: list[str]) -> dict[str, Any]:
        now = parse_utc(now_iso)
        if now is None:
            return {}
        since = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        row = connection.execute(
            "SELECT COUNT(*) AS attempts, COUNT(DISTINCT session_id) AS sessions, "
            "COUNT(DISTINCT substr(created_at, 1, 10)) AS active_days, COALESCE(SUM(hints_used), 0) AS hints, "
            "COALESCE(SUM(CASE WHEN primed THEN 1 ELSE 0 END), 0) AS assisted_redos "
            "FROM practice_attempts WHERE created_at >= ? AND created_at < ?",
            (since, now_iso),
        ).fetchone()
        signals = {
            "attempts": int(row["attempts"]), "sessions": int(row["sessions"]), "active_days": int(row["active_days"]),
            "hints_used": int(row["hints"]), "assisted_redos": int(row["assisted_redos"]),
        }
        for table, key in (("question_events", "tutor_questions"), ("reveal_events", "answers_revealed")):
            if _table(connection, table):
                signals[key] = int(connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE created_at >= ? AND created_at < ?", (since, now_iso)
                ).fetchone()[0])
            else:
                unknowns.append(f"not recorded in this database: {key.replace('_', ' ')}")
        return signals

    def _open_problems(
        self, connection: Any, los: set[str], titles: Mapping[str, str], unknowns: list[str], past: PastWork,
        rule: CardText,
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if not los:
            return entries
        try:
            if _table(connection, "causal_hypotheses"):
                from learnloop.db.stores.daily_plans import open_learner_state_hypotheses

                # The daily plan's own resolution predicate (review F8): a
                # validated cause whose promoted misconception is resolved is
                # closed. Each entry names the evidence it rests on.
                rows = open_learner_state_hypotheses(connection, los)
                behind = protection.hypothesis_answers(connection, [row["id"] for row in rows])
                for row in rows:
                    # A cause diagnosed from protected work (any answer of its
                    # episode: exam or reserved material, a check waiting, a
                    # probe) keeps its topic and status, never its statement:
                    # the shared leakage rule. Fail closed as past work does.
                    statement, _note, reason = statement_text(
                        past, rule, "hypothesis", row["id"], row["statement"], STATEMENT_LIMIT,
                        answers=sorted(behind.get(str(row["id"]), frozenset()) | {str(row["attempt_id"] or "")}),
                        los=(row["learning_object_id"],))
                    entries.append({
                        "kind": "diagnosed_cause", "learning_object_id": row["learning_object_id"],
                        "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                        "status": row["status"], "since": row["created_at"],
                        "statement": statement,
                        "withheld": reason,
                        "hypothesis_id": row["id"], "attempt_id": row["attempt_id"],
                        "error_event_id": row["error_event_id"],
                        "promoted_misconception_id": row["promoted_misconception_id"],
                    })
            if _table(connection, "unresolved_cause_factors"):
                for row in connection.execute(
                    f"""SELECT a.learning_object_id, COUNT(*) AS n, MIN(f.created_at) AS since
                          FROM unresolved_cause_factors f JOIN practice_attempts a ON a.id = f.attempt_id
                         WHERE f.status = 'open' AND a.learning_object_id IN ({_marks(sorted(los))})
                         GROUP BY a.learning_object_id ORDER BY a.learning_object_id""",
                    sorted(los),
                ):
                    entries.append({
                        "kind": "unresolved_cause", "learning_object_id": row["learning_object_id"],
                        "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                        "status": "open", "since": row["since"],
                        "statement": f"{row['n']} answer(s) whose cause is not settled",
                    })
            if _table(connection, "learner_text_gaps"):
                reversed_ids = set()
                if _table(connection, "learner_text_gap_reversals"):
                    reversed_ids = {row[0] for row in connection.execute("SELECT gap_id FROM learner_text_gap_reversals")}
                for row in connection.execute(
                    f"""SELECT id, anchor_learning_object_id, target_id, kind, learner_text, created_at,
                               attempt_id, practice_item_id
                          FROM learner_text_gaps
                         WHERE kind IN ('prerequisite', 'misconception')
                           AND (anchor_learning_object_id IN ({_marks(sorted(los))})
                                OR (target_kind = 'learning_object' AND target_id IN ({_marks(sorted(los))})))
                         ORDER BY created_at DESC, id DESC""",
                    (*sorted(los), *sorted(los)),
                ):
                    if row["id"] in reversed_ids:
                        continue
                    lo = row["target_id"] if row["target_id"] in los else row["anchor_learning_object_id"]
                    # The learner's own words (G5 shows them), unless they were
                    # written about protected work (the shared leakage rule).
                    statement, _note, reason = statement_text(
                        past, rule, "learner_text_gap", row["id"], row["learner_text"], STATEMENT_LIMIT,
                        answers=[row["attempt_id"]] if row["attempt_id"] else [],
                        items=[row["practice_item_id"]] if row["practice_item_id"] else [],
                        los=(row["anchor_learning_object_id"],))
                    entries.append({
                        "kind": f"learner_named_{row['kind']}", "learning_object_id": lo,
                        "topic": titles.get(lo, lo), "status": "open", "since": row["created_at"],
                        "statement": statement, "withheld": reason,
                    })
        except Exception:  # noqa: BLE001 - named as unknown
            _LOG.warning("router R2a card: open problems not read", exc_info=True)
            unknowns.append("open problems could not be read")
        return entries[:OPEN_PROBLEM_LIMIT]

    def _self_reports(
        self, connection: Any, los: set[str], titles: Mapping[str, str], now_iso: str, unknowns: list[str]
    ) -> list[dict[str, Any]]:
        reports: list[dict[str, Any]] = []
        if not los:
            return reports
        try:
            if _table(connection, "assumption_returns"):
                for row in connection.execute(
                    f"SELECT learning_object_id, reason, created_at FROM assumption_returns "
                    f"WHERE learning_object_id IN ({_marks(sorted(los))}) AND created_at < ? "
                    "ORDER BY created_at DESC, id DESC",
                    (*sorted(los), now_iso),
                ):
                    reports.append({"at": row["created_at"], "topic": titles.get(row["learning_object_id"]),
                                    "report": str(row["reason"] or "returned").replace("_", " ")})
            if _table(connection, "learner_claims"):
                for row in connection.execute(
                    f"SELECT scope_id, claim_type, claimed_level, created_at FROM learner_claims "
                    f"WHERE scope_type = 'learning_object' AND scope_id IN ({_marks(sorted(los))}) AND created_at < ? "
                    "ORDER BY created_at DESC, id DESC",
                    (*sorted(los), now_iso),
                ):
                    reports.append({"at": row["created_at"], "topic": titles.get(row["scope_id"]),
                                    "report": f"{str(row['claim_type']).replace('_', ' ')} ({row['claimed_level']})"})
        except Exception:  # noqa: BLE001 - named as unknown
            unknowns.append("self-reports could not be read")
        reports.sort(key=lambda entry: str(entry.get("at") or ""), reverse=True)
        return reports[:SELF_REPORT_LIMIT]

    def _withheld_items(self, unknowns: list[str]) -> Withheld:
        """The items whose question and answers the card never shows: the
        shared predicate (``learner_protection.withheld_items``, the chat
        frontend's too): exam material by the one exam predicate, live
        assessment reservations, items a cold check or a repair's cold retry
        holds, diagnostic probes, and items the vault cannot read. Unavailable
        when any of it cannot be read (then none show, and ``unknowns`` says so).

        Not behind ``goals.held_out_selection``: that switch restores the
        predecessor's *serving* selection, and the card is a model context
        (R2b sends it), whose protections are never switched."""

        withheld = protection.withheld_items(self.vault, self.repository)
        for unknown in withheld.unknowns:
            if unknown not in unknowns:
                unknowns.append(unknown)
        return withheld

    def _recent_work(
        self, attempts: Sequence[Mapping[str, Any]], held: frozenset[str], past: PastWork, rule: CardText,
        titles: Mapping[str, str],
    ) -> list[dict[str, Any]]:
        work: list[dict[str, Any]] = []
        for row in attempts[:RECENT_WORK_LIMIT]:
            # The shared protection, then the card's text rule: the pinned
            # revision's question (never today's, review F6) and the answer.
            shown = past_work_text(past, rule, row["id"], row["learning_object_id"], row.get("learner_answer_md"),
                                   EXCERPT_LIMIT)
            status = row.get("reference_status")
            work.append({
                "attempt_id": row["id"],
                "at": row["created_at"],
                "learning_object_id": row["learning_object_id"],
                "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                "kind": row.get("practice_mode"),
                "result": attempt_result(row["correctness"], row["id"] in held),
                "hints_used": int(row.get("hints_used") or 0),
                "assisted": bool(row.get("primed")),
                "key_status": status if status in ("verified", "unverified") else None,
                "withheld": shown.withheld,
                "stem": shown.stem,
                "stem_note": shown.stem_note,
                "answer": shown.answer,
            })
        return work


__all__ = ["CardGatherer", "CardText", "RECENT_WORK_LIMIT"]
