"""The Reader tutor's learner state (learner-blindness relax; owner direction 2026-11-01).

The owner's direction: blindness only where it matters, the grader. The Reader
tutor (Ask) was blind to the learner by design (design A.2: "the manifest
carries no learner ability reading"); with ``reader_tutor.learner_state_enabled``
on, its context also carries, for the passage's learning objects:

* **readiness in words**: the Today headline's class of each topic
  (``daily_plan.headline.classify_learning_objects``: demonstrated, assumed,
  learning, untested), rendered as a phrase, never a number or a posterior;
* **the learner's confidence events** (TE0's block,
  ``confidence_events.safe_learner_events``: the tap and the grader's hedge
  read with the outcome), which TE0's ruling had kept out of the Reader;
* **recent attempt outcomes** on each topic (date, result class, how much help),
  a held grade "held for review" and never a score;
* **recent practice and feedback exchanges** on each topic: the learner's own
  question, and the answer they were shown only once that item can no longer
  be answered cold (``PastWork.solution_reason``: a feedback answer was
  written with the rubric); inside a workbench session bound to an item no
  earlier tutor answer is carried at all (the binding's guard plans every
  model-written text of the call, ``reader_modes.plan_bound_delivery``).

Everything is read through the one protection (``learner_protection``): an
attempt or exchange on exam or held-out material, a reserved surface, an item
an open cold check holds or a diagnostic probe contributes nothing, and when the
protection cannot be read nothing shows (fail closed). A question asked during
a cold administration carries no learner state at all (its in-flight response
is never read here, and the manifest keeps ``cold_in_flight_response``
excluded); nothing here reads an answer key, a rubric or a reference solution.

Context only: nothing is written and no model is called; the tutor still
writes no attempt, claim or mastery from a Reader question (P0 invariant 10).
Only the sidecar composes this module (it reads the daily plan's headline,
which the Reader and the tutor packages may not import), so the tutor
receives it by injection.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field, replace
from typing import Any

from learnloop import confidence_events
from learnloop import learner_protection as protection
from learnloop.clock import parse_utc
from learnloop.db.connection import connect

_LOG = logging.getLogger(__name__)

#: The block's identity inside a model context (receipts read it there).
VERSION = "reader-learner-state-v1"
NOTE = (
    "LearnLoop's reading of where the learner stands on this passage's topics: readiness in words (from "
    "unassisted, capability-matched credit, never a score), their recent attempts' outcomes and their recent "
    "questions to the tutor. Context for pitching the explanation, not a grade."
)
#: Prompt-size bounds (``keep``: structural size bounds, never judgements):
#: topics described, attempts and exchanges per topic, characters per text.
TOPIC_LIMIT = 8
ATTEMPT_LIMIT = 5
EXCHANGE_LIMIT = 3
TEXT_LIMIT = 400

READINESS_WORDS = {
    "demonstrated": "demonstrated: the whole topic has unassisted, capability-matched credit",
    "assumed": "assumed from placement, not yet checked",
    "learning": "learning: some direct evidence, not yet demonstrated",
    "untested": "untested: no direct evidence yet",
}
READINESS_UNREAD = "not read (the readiness classes could not be read)"
READINESS_INACTIVE = "not tracked (an inactive topic)"

#: Why a question carries no learner state (the manifest records it).
OMITTED_COLD = "cold_administration"
OMITTED_NO_TOPICS = "no_learning_objects"
OMITTED_UNREADABLE = "protection_unreadable"

_RESULT_WORDS = {
    "correct": "right",
    "incorrect": "wrong",
    "partial": "partly right",
    "held_for_review": "held for review (no score yet)",
    "not_graded": "not graded",
}
_EXCHANGE_CONTEXTS = ("practice", "feedback")


def enabled(vault: Any) -> bool:
    """The kill switch, ``reader_tutor.learner_state_enabled`` (default on)."""

    section = getattr(getattr(vault, "config", None), "reader_tutor", None)
    return bool(getattr(section, "learner_state_enabled", True))


def _excerpt(text: Any, limit: int = TEXT_LIMIT) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


@dataclass(frozen=True)
class ReaderLearnerState:
    """What one Reader question's tutor context gains (or why it gains nothing).

    ``state`` is the ``learner_state`` block (None: nothing to say),
    ``confidence`` TE0's ``learner_confidence`` block (None: none), and
    ``omitted`` why the question carries none (a cold administration, a
    passage with no learning object, protection that could not be read)."""

    state: dict[str, Any] | None = None
    confidence: dict[str, Any] | None = None
    omitted: str | None = None
    learning_object_ids: tuple[str, ...] = ()
    counts: Mapping[str, int] = field(default_factory=dict)

    def apply(self, context: Any) -> Any:
        """The tutor context with the state (unchanged when there is none)."""

        if self.state is None and self.confidence is None:
            return context
        return replace(context, learner_state=self.state, learner_confidence=self.confidence)

    def receipt(self) -> dict[str, Any]:
        """What the question's ``source_context`` records (no text)."""

        out: dict[str, Any] = {"version": VERSION, "learning_object_ids": list(self.learning_object_ids),
                               "given": self.state is not None or self.confidence is not None}
        if self.omitted:
            out["omitted"] = self.omitted
        if self.counts:
            out["counts"] = dict(self.counts)
        if self.confidence is not None:
            out["confidence_events"] = True
        return out

    def manifest(self) -> dict[str, Any]:
        """The manifest's record: the receipt and exactly what the tutor was given."""

        return {**self.receipt(), "state": self.state, "learner_confidence": self.confidence}


def omitted(reason: str, learning_object_ids: Sequence[str] = ()) -> ReaderLearnerState:
    return ReaderLearnerState(omitted=reason, learning_object_ids=tuple(learning_object_ids))


def _readiness(vault: Any, repository: Any, los: Sequence[str], now_iso: str) -> dict[str, str]:
    from learnloop.daily_plan import headline

    try:
        classes = headline.classify_learning_objects(vault, repository, now=parse_utc(now_iso),
                                                     learning_object_ids=los)
    except Exception:  # noqa: BLE001 - named, never guessed
        _LOG.warning("reader learner state: readiness classes not read", exc_info=True)
        return {lo: READINESS_UNREAD for lo in los}
    return {lo: READINESS_WORDS.get(str(classes[lo]), str(classes[lo])) if lo in classes else READINESS_INACTIVE
            for lo in los}


def _attempt_text(row: Mapping[str, Any], held: frozenset[str]) -> str:
    result = protection.attempt_result(row.get("correctness"), str(row["id"]) in held)
    help_parts: list[str] = []
    hints = int(row.get("hints_used") or 0)
    if hints:
        help_parts.append(f"with {hints} hint{'s' if hints != 1 else ''}")
    if row.get("primed"):
        help_parts.append("after the answer was shown")
    helped = ", ".join(help_parts) if help_parts else "unassisted"
    return f"{str(row.get('created_at') or '')[:10]}: {_RESULT_WORDS.get(result, result)}, {helped}"


def build(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], now_iso: str,
          bound_item_id: str | None = None) -> ReaderLearnerState:
    """The learner state on these learning objects strictly before ``now_iso``.

    ``bound_item_id`` (a workbench session's item): no earlier tutor answer
    is carried. Never raises: a read that fails yields no state."""

    los = [str(lo) for lo in dict.fromkeys(learning_object_ids) if lo and str(lo) in vault.learning_objects]
    los = los[:TOPIC_LIMIT]
    if not los:
        return omitted(OMITTED_NO_TOPICS)
    try:
        return _build(vault, repository, los, now_iso, bound_item_id)
    except Exception:  # noqa: BLE001 - a context without the state, never a failed answer
        _LOG.warning("reader learner state not read", exc_info=True)
        return omitted(OMITTED_UNREADABLE, los)


def _build(vault: Any, repository: Any, los: list[str], now_iso: str,
           bound_item_id: str | None) -> ReaderLearnerState:
    from learnloop.tutor.tutor_qa import delivered_answer_md

    titles = {lo.id: lo.title for lo in vault.learning_objects.values()}
    withheld = protection.withheld_items(vault, repository)
    if not withheld.available:
        return omitted(OMITTED_UNREADABLE, los)
    marks = ",".join("?" for _ in los)
    item_lo = {item_id: str(item.learning_object_id) for item_id, item in vault.practice_items.items()}
    item_ids = [item_id for item_id, lo in item_lo.items() if lo in los]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        past = protection.PastWork(connection, vault, repository, withheld=withheld)
        attempts = [dict(row) for row in connection.execute(
            "SELECT id, practice_item_id, learning_object_id, attempt_type, correctness, hints_used, primed, "
            f"created_at FROM practice_attempts WHERE learning_object_id IN ({marks}) AND created_at < ? "
            "AND attempt_type != 'self_report' ORDER BY created_at DESC, id DESC",
            (*los, now_iso),
        )]
        kept_attempts: dict[str, list[dict[str, Any]]] = {}
        for row in attempts:
            bucket = kept_attempts.setdefault(str(row["learning_object_id"]), [])
            if len(bucket) >= ATTEMPT_LIMIT or past.attempt_reason(row["id"]) is not None:
                continue
            bucket.append(row)
        shown_attempts = [row["id"] for rows in kept_attempts.values() for row in rows]
        held = past.held(shown_attempts) if shown_attempts else frozenset()
        exchanges: dict[str, list[dict[str, Any]]] = {}
        withheld_answers = 0
        if item_ids:
            item_marks = ",".join("?" for _ in item_ids)
            rows = [dict(row) for row in connection.execute(
                "SELECT * FROM question_events WHERE context IN ('practice', 'feedback') "
                f"AND answer_status = 'answered' AND practice_item_id IN ({item_marks}) AND created_at < ? "
                "ORDER BY created_at DESC, id DESC",
                (*item_ids, now_iso),
            )]
            for row in rows:
                lo = item_lo.get(str(row.get("practice_item_id")))
                if lo is None:
                    continue
                bucket = exchanges.setdefault(lo, [])
                if len(bucket) >= EXCHANGE_LIMIT:
                    continue
                item_id = str(row["practice_item_id"])
                answers = [row["attempt_id"]] if row.get("attempt_id") else []
                if past.evidence_reason(answers=answers, items=[item_id]) is not None:
                    continue
                entry: dict[str, Any] = {
                    "date": str(row.get("created_at") or "")[:10],
                    "when": "during an attempt" if row.get("context") == "practice" else "after a graded attempt",
                    "learner_question": _excerpt(row.get("question_md")),
                }
                answer_reason = ("asked inside a bound workbench session" if bound_item_id is not None
                                 else past.solution_reason([item_id]))
                answer = delivered_answer_md(_decoded(row))
                if answer_reason is None and answer:
                    entry["answer_shown"] = _excerpt(answer)
                elif answer:
                    entry["answer_left_out"] = answer_reason
                    withheld_answers += 1
                bucket.append(entry)
    topics: list[dict[str, Any]] = []
    readiness = _readiness(vault, repository, los, now_iso)
    for lo in los:
        topic: dict[str, Any] = {"topic": titles.get(lo, lo), "readiness": readiness[lo]}
        attempts_text = [_attempt_text(row, held) for row in kept_attempts.get(lo, [])]
        if attempts_text:
            topic["recent_attempts"] = attempts_text
        if exchanges.get(lo):
            topic["recent_tutor_questions"] = list(reversed(exchanges[lo]))
        topics.append(topic)
    confidence = confidence_events.safe_learner_events(
        vault, repository, learning_object_ids=los, before_iso=now_iso, titles=titles)
    state = {"version": VERSION, "note": NOTE, "topics": topics}
    counts = {"topics": len(topics), "attempts": len(shown_attempts),
              "exchanges": sum(len(v) for v in exchanges.values()), "answers_left_out": withheld_answers}
    return ReaderLearnerState(state=state, confidence=confidence, learning_object_ids=tuple(los), counts=counts)


def _decoded(row: Mapping[str, Any]) -> dict[str, Any]:
    """A raw ``question_events`` row as ``delivered_answer_md`` reads it (its source context decoded)."""

    import json

    out = dict(row)
    raw = out.pop("source_context_json", None)
    try:
        out["source_context"] = json.loads(raw) if raw else None
    except (TypeError, ValueError):
        out["source_context"] = None
    return out


__all__ = [
    "ATTEMPT_LIMIT",
    "EXCHANGE_LIMIT",
    "NOTE",
    "OMITTED_COLD",
    "OMITTED_NO_TOPICS",
    "OMITTED_UNREADABLE",
    "READINESS_WORDS",
    "ReaderLearnerState",
    "TEXT_LIMIT",
    "TOPIC_LIMIT",
    "VERSION",
    "build",
    "enabled",
    "omitted",
]
