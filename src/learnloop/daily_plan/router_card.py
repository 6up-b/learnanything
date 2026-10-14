"""Router R2a: gathering ``LearnerStateCardV1``'s inputs at a plan boundary.

The pure builder is :mod:`learnloop.router.card`; this module reads the
ledger for one decision, strictly before the decision time, and applies the
card's leakage rules (plan §3.6, gate G5) before anything is rendered. Its
reads scale with the card's topics (at most ``LEARNING_OBJECT_LIMIT``), never
with the candidate items: the attempt history of those topics is read in full
(for the evidence counts), the held-grade predicate reads it in 500-attempt
chunks, and the headline classification reads each topic's certification.

* it never reads a reference solution, an answer key, a rubric or source text;
* a candidate item contributes its topic, minutes and kind only (no stem of
  an item the learner has not attempted);
* past work on exam material (an ``exam_attempt``, or an item whose
  provenance cites what ``source_retrieval.corpus.exam_exclusions`` names:
  exam-role members and every ``held_out_evaluation`` unit) and on a surface
  holding a live assessment reservation keeps its result but shows no
  question and no answer; when the exam predicate cannot be read, no past
  work shows a question or an answer (fail closed);
* a grade held for review (THE predicate, ``held_grades``) is "held for
  review", never a score;
* an answer on an unverified key says so (``reference_status``);
* past work shows the question the learner answered: the prompt of the
  attempt's pinned assessment contract (the revision it was graded against),
  never today's edited prompt; an attempt whose revision cannot be
  established shows no question (review F6).

A topic is ``demonstrated`` or ``assumed`` only by the Today headline's
classification (capability-matched, unassisted certification credit; open
placement assumptions); other attempted topics are ``attempted_not_demonstrated``
or ``assisted_only`` (review F7). Open problems use the daily plan's own
resolution predicate (review F8).

A section that cannot be read is named in ``unknowns`` rather than guessed.
Read-only; nothing is written and no model is called.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import timedelta
from math import exp, log, sqrt
from typing import Any

from learnloop.clock import parse_utc
from learnloop.daily_plan.types import BlockCandidate, PlanState
from learnloop.router.card import CardInputs, LearnerStateCard, build_card

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


def _result(correctness: Any, held: bool) -> str:
    if held:
        return "held_for_review"
    if correctness is None:
        return "not_graded"
    value = float(correctness)
    if value >= 0.999:
        return "correct"
    if value <= 0.001:
        return "incorrect"
    return "partial"


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
        with self.repository.connection() as connection:
            as_of = connection.execute(
                "SELECT id FROM practice_attempts WHERE created_at < ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (now_iso,),
            ).fetchone()
            attempts = self._attempts(connection, los, now_iso)
            held = self._held(connection, [row["id"] for row in attempts])
            pinned = self._pinned_stems(connection, attempts[:RECENT_WORK_LIMIT], unknowns)
            learning_objects = self._learning_objects(los, candidate_los, attempts, held, feasible, titles, now_iso,
                                                      unknowns)
            interaction = self._interaction(connection, now_iso, unknowns)
            hypotheses = self._open_problems(connection, set(los), titles, unknowns)
            reports = self._self_reports(connection, set(los), titles, now_iso, unknowns)
        recent = self._recent_work(attempts, held, pinned, titles, unknowns)
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
        )

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
        rows = connection.execute(
            f"SELECT id, practice_item_id, learning_object_id, practice_mode, attempt_type, correctness, hints_used, "
            f"primed, learner_answer_md, created_at, {status} FROM practice_attempts "
            f"WHERE learning_object_id IN ({_marks(los)}) AND created_at < ? ORDER BY created_at DESC, id DESC",
            (*los, now_iso),
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _held(connection: Any, attempt_ids: Sequence[str]) -> frozenset[str]:
        from learnloop.held_grades import held_for_review_attempts

        return held_for_review_attempts(connection, attempt_ids) if attempt_ids else frozenset()

    @staticmethod
    def _pinned_stems(connection: Any, attempts: Sequence[Mapping[str, Any]], unknowns: list[str]) -> dict[str, str]:
        """The question each attempt answered (review F6): the prompt of its
        pinned assessment contract, the one contract its current grading
        evidence names, belonging to the attempt's item. Only the prompt is
        read (``json_extract``), never the contract's answer key or rubric. An
        attempt with no contract, or several, gets no stem: today's prompt is
        never substituted for the revision the learner saw."""

        items = {str(row["id"]): row.get("practice_item_id") for row in attempts}
        if not items:
            return {}
        try:
            if not _table(connection, "assessment_contract_versions"):
                return {}
            contracts: dict[str, set[Any]] = {}
            for attempt_id, contract_id in connection.execute(
                f"SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
                f"WHERE superseded_at IS NULL AND attempt_id IN ({_marks(list(items))})",
                list(items),
            ):
                contracts.setdefault(str(attempt_id), set()).add(contract_id)
            single = {attempt: next(iter(ids)) for attempt, ids in contracts.items() if len(ids) == 1 and None not in ids}
            if not single:
                return {}
            versions = sorted({str(value) for value in single.values()})
            prompts = {
                str(row[0]): (row[1], row[2])
                for row in connection.execute(
                    f"SELECT id, practice_item_id, json_extract(contract_json, '$.prompt') "
                    f"FROM assessment_contract_versions WHERE id IN ({_marks(versions)})",
                    versions,
                )
            }
        except Exception:  # noqa: BLE001 - named as unknown; no question shows
            _LOG.warning("router R2a card: pinned questions not read", exc_info=True)
            unknowns.append("the questions past work answered could not be read: none is shown")
            return {}
        stems: dict[str, str] = {}
        for attempt_id, version_id in single.items():
            item_id, prompt = prompts.get(str(version_id), (None, None))
            if item_id is not None and item_id == items.get(attempt_id) and isinstance(prompt, str) and prompt.strip():
                stems[attempt_id] = prompt
        return stems

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
            result = _result(row["correctness"], row["id"] in held)
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
            out[lo] = row
            if status == "untested" and lo in candidate_los:
                unknowns.append(f"never tested: {titles.get(lo, lo)}")
            elif status == "assumed":
                unknowns.append(f"assumed known (not demonstrated): {titles.get(lo, lo)}")
        return out

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
        self, connection: Any, los: set[str], titles: Mapping[str, str], unknowns: list[str]
    ) -> list[dict[str, Any]]:
        from learnloop.router.card import STATEMENT_LIMIT, excerpt

        entries: list[dict[str, Any]] = []
        if not los:
            return entries
        try:
            if _table(connection, "causal_hypotheses"):
                from learnloop.db.stores.daily_plans import open_learner_state_hypotheses

                # The daily plan's own resolution predicate (review F8): a
                # validated cause whose promoted misconception is resolved is
                # closed. Each entry names the evidence it rests on.
                for row in open_learner_state_hypotheses(connection, los):
                    entries.append({
                        "kind": "diagnosed_cause", "learning_object_id": row["learning_object_id"],
                        "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                        "status": row["status"], "since": row["created_at"],
                        "statement": excerpt(row["statement"], STATEMENT_LIMIT),
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
                    f"""SELECT id, anchor_learning_object_id, target_id, kind, learner_text, created_at
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
                    entries.append({
                        "kind": f"learner_named_{row['kind']}", "learning_object_id": lo,
                        "topic": titles.get(lo, lo), "status": "open", "since": row["created_at"],
                        "statement": excerpt(row["learner_text"], STATEMENT_LIMIT),
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

    def _withheld_items(self, unknowns: list[str]) -> frozenset[str] | None:
        """Practice items whose question and answers the card never shows:
        exam material (the exam predicate) and reserved assessment surfaces.
        None when the exam predicate cannot be read (then none show)."""

        vault = self.vault
        withheld: set[str] = set()
        try:
            for row in self.repository.reserved_assessment_surfaces():
                if row.get("legacy_practice_item_id"):
                    withheld.add(str(row["legacy_practice_item_id"]))
        except Exception:  # noqa: BLE001 - fail closed
            unknowns.append("assessment reservations could not be read: past questions and answers are withheld")
            return None
        try:
            from learnloop.source_retrieval.corpus import exam_exclusions

            exam = exam_exclusions(vault, self.repository)
        except Exception:  # noqa: BLE001 - fail closed
            unknowns.append("exam material could not be read: past questions and answers are withheld")
            return None
        for item in vault.practice_items.values():
            for ref in getattr(getattr(item, "provenance", None), "source_refs", None) or ():
                extraction = getattr(ref, "extraction_id", None)
                if not extraction:
                    continue
                if extraction in exam.extractions or any(
                    (extraction, span) in exam.spans for span in getattr(ref, "span_ids", None) or ()
                ):
                    withheld.add(item.id)
                    break
        return frozenset(withheld)

    def _recent_work(
        self, attempts: Sequence[Mapping[str, Any]], held: frozenset[str], pinned: Mapping[str, str],
        titles: Mapping[str, str], unknowns: list[str],
    ) -> list[dict[str, Any]]:
        withheld = self._withheld_items(unknowns)
        work: list[dict[str, Any]] = []
        for row in attempts[:RECENT_WORK_LIMIT]:
            exam_work = row.get("attempt_type") == "exam_attempt"
            hidden = withheld is None or exam_work or row["practice_item_id"] in withheld
            status = row.get("reference_status")
            work.append({
                "attempt_id": row["id"],
                "at": row["created_at"],
                "learning_object_id": row["learning_object_id"],
                "topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                "kind": row.get("practice_mode"),
                "result": _result(row["correctness"], row["id"] in held),
                "hints_used": int(row.get("hints_used") or 0),
                "assisted": bool(row.get("primed")),
                "key_status": status if status in ("verified", "unverified") else None,
                "withheld": "exam or reserved material" if hidden and withheld is not None else (
                    "exam predicate unavailable" if hidden else None
                ),
                # The pinned revision's question, never today's (review F6).
                "stem": None if hidden else pinned.get(str(row["id"])),
                "stem_note": None if hidden or str(row["id"]) in pinned else "question revision not recorded",
                "answer": None if hidden else (row.get("learner_answer_md") or None),
            })
        return work


__all__ = ["CardGatherer", "RECENT_WORK_LIMIT"]
