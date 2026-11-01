"""What the figure author is told about the learner (learner data-relax 2).

Owner principle (2026-11-01): the learner's questions, answers and history
are not private; include them wherever they help. A figure helps more when
its author knows where this learner stands on what the passage teaches, so
with ``figures.author_learner_state`` on (:func:`enabled`) the author's
context gains ``learner_state`` for the passage's topics
(:func:`anchored_learning_objects`):

* each topic's **status in words** (``reading_paths.lo_statuses``: shown on
  their own, assumed known, learning, new);
* the **open misconception and gap statements** on those topics: active
  misconceptions (LearnLoop's diagnosis wrote them) and learner-text gaps
  not undone (LearnLoop's reading of the learner's words, or the words
  themselves when nothing was named), each labelled with who wrote it;
* at most :data:`RECENT_ANSWERS` **recent answers** of the learner's own on
  those topics, with the question as it was graded (the attempt's pinned
  contract, never today's prompt) and the result.

**Exam material never shows.** Every answer is read through
``learner_protection`` (the one authority the router card and the chat
frontend share): an attempt on exam or held-out material, exam work, an
item reserved for an assessment, an item a cold check or a repair's cold
retry holds (cold-in-flight), a diagnostic probe or an item the vault cannot
read shows nothing, and is skipped (the next unprotected answer takes its
place). A statement written from any such answer is left out
(``PastWork.evidence_reason``), and so is one whose answers cannot be
established (fail closed). When the protection cannot be read at all, no
answer and no statement is sent. Only an item's graded question is read,
never a reference answer, an answer key or a rubric.

**Empty means the predecessor.** :func:`learner_state` returns None when there
is nothing to say (no statement, no answer, every topic new): the author's
payload, prompt version and reuse key are then exactly the predecessor's, so
a learner with no state keeps today's keys and reuse. With state, the reuse
key names :func:`state_hash` (``figures.service.request_hash``).

Read-only: nothing is written and no model is called. Figures stay help,
never evidence: nothing here is read by scoring, scheduling, projection or
serving (``evidence-never-reads-figures``).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.db.connection import connect
from learnloop.figure_admission import author_learner_state_enabled

_LOG = logging.getLogger(__name__)

#: keep: prompt size. The passage's topics described (an anchor names one or
#: two; a grounded request at most a few passages' worth).
MAX_TOPICS = 4
#: keep: prompt size. Open statements sent across those topics (newest first).
MAX_STATEMENTS = 6
#: keep: prompt size. One statement's characters.
STATEMENT_CHARS = 300
#: keep: the owner's bound for this stage ("at most two recent answer
#: excerpts on those LOs").
RECENT_ANSWERS = 2
#: keep: prompt size. One answer excerpt's characters.
ANSWER_CHARS = 600
#: keep: prompt size. One graded question's characters.
QUESTION_CHARS = 300
#: keep: read size. The newest attempts scanned for two unprotected answers.
ATTEMPTS_SCANNED = 30

#: A topic's status (``reading_paths.STATUSES``) in the words the author reads.
STATUS_WORDS = {
    "demonstrated": "shown on their own",
    "assumed": "assumed known (not yet shown on their own)",
    "learning": "learning (has answered on it, not yet shown on their own)",
    "new": "new (no answers on it yet)",
}

WRITTEN_BY_DIAGNOSIS = "LearnLoop's diagnosis of their answers"
WRITTEN_BY_GAP_READING = "LearnLoop's reading of their own words"
WRITTEN_BY_LEARNER = "the learner"


def enabled(vault: Any) -> bool:
    """``figures.author_learner_state`` under ``figures.enabled``."""

    return author_learner_state_enabled(vault)


def excerpt(text: Any, limit: int) -> str:
    flat = " ".join(str(text or "").split())
    return flat if len(flat) <= limit else flat[: max(limit - 1, 0)].rstrip() + "…"


def anchored_learning_objects(vault: Any, repository: Any, *, extraction_id: str | None,
                              span_ids: Sequence[str], keys: Sequence[tuple[str, str]] = ()) -> list[str]:
    """The passage's learning objects (``reader_tutor.passage_learning_objects``):
    the anchor's spans on ``extraction_id``, then each grounding key's (a
    request with no passage: its kept passages, else where the learner was
    reading). At most :data:`MAX_TOPICS`; unreadable: none (the author is
    then sent nothing about the learner)."""

    from learnloop.source_retrieval.reader_tutor import passage_learning_objects

    groups: list[tuple[str, list[str]]] = []
    if extraction_id and span_ids:
        groups.append((str(extraction_id), [str(span) for span in span_ids if span]))
    by_extraction: dict[str, list[str]] = {}
    for key_extraction, key_span in keys:
        if key_extraction and key_span:
            by_extraction.setdefault(str(key_extraction), []).append(str(key_span))
    groups.extend(by_extraction.items())
    found: list[str] = []
    for group_extraction, spans in groups:
        try:
            found.extend(passage_learning_objects(vault, repository, extraction_id=group_extraction,
                                                  span_ids=spans))
        except Exception:  # noqa: BLE001 - the author is then told nothing about the learner
            _LOG.warning("figure learner state: the passage's topics could not be read", exc_info=True)
    return [lo for lo in dict.fromkeys(found) if lo in vault.learning_objects][:MAX_TOPICS]


class _AnswerText:
    """The text rule (``learner_protection.TextRule``) once the shared
    protection has passed: the question as graded (the pinned contract's)
    and the learner's own answer, both shortened."""

    def __init__(self, past: Any) -> None:
        self.past = past

    def question(self, attempt_id: str, lo_id: Any) -> tuple[str | None, str | None]:
        pin = self.past.pinned(attempt_id)
        question = pin.question(QUESTION_CHARS, excerpt) if pin is not None else None
        return (excerpt(question, QUESTION_CHARS), None) if question else (None, None)

    def answer(self, attempt_id: str, text: Any, limit: int) -> tuple[str | None, str | None]:
        shown = excerpt(text, limit)
        return (shown or None), None

    def statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Any = (), items: Any = (),
                  los: Any = ()) -> tuple[str | None, str | None]:
        return (excerpt(text, limit) or None), None


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def _named(row: Mapping[str, Any]) -> str:
    named = row.get("named") or row.get("named_json") or {}
    if isinstance(named, str):
        try:
            named = json.loads(named)
        except ValueError:
            named = {}
    if not isinstance(named, Mapping):
        return ""
    return str(named.get("belief_statement") or named.get("prerequisite_line")
               or named.get("prerequisite_name") or "").strip()


def _misconception_statements(connection: Any, repository: Any, past: Any, rule: _AnswerText,
                              los: Sequence[str], titles: Mapping[str, str]) -> list[dict[str, Any]]:
    from learnloop.learner_protection import statement_text

    found: list[dict[str, Any]] = []
    for lo in los:
        for record in repository.misconceptions_for_learning_object(lo, statuses=("active",)):
            statement = str(getattr(record, "statement", "") or "").strip()
            events = [str(event) for event in (getattr(record, "source_error_event_ids", None) or ()) if event]
            if not statement or not events:
                continue  # no recorded answers behind it: it cannot be checked, so it is left out
            answers = [str(row[0]) for row in connection.execute(
                f"SELECT DISTINCT attempt_id FROM error_events WHERE id IN ({_marks(events)}) "
                "AND attempt_id IS NOT NULL", events)]
            if not answers:
                continue
            shown, _note, withheld = statement_text(past, rule, "misconception", record.id, statement,
                                                    STATEMENT_CHARS, answers=answers, los=(lo,))
            if withheld or not shown:
                continue
            found.append({"topic": titles.get(lo, lo), "kind": "misconception", "statement": shown,
                          "written_by": WRITTEN_BY_DIAGNOSIS,
                          "_at": str(getattr(record, "updated_at", None) or getattr(record, "created_at", "") or "")})
    return found


def _gap_statements(connection: Any, past: Any, rule: _AnswerText, los: Sequence[str],
                    titles: Mapping[str, str]) -> list[dict[str, Any]]:
    from learnloop.db.stores import learner_gaps as gap_store
    from learnloop.learner_protection import statement_text

    rows = gap_store.gaps(connection, learning_object_ids=list(los))
    undone = {row["gap_id"] for row in gap_store.reversals(connection, [row["id"] for row in rows])}
    found: list[dict[str, Any]] = []
    for row in rows:
        if row["id"] in undone or row.get("kind") not in ("prerequisite", "misconception"):
            continue
        named = _named(row)
        text, written_by = (named, WRITTEN_BY_GAP_READING) if named else (
            str(row.get("learner_text") or "").strip(), WRITTEN_BY_LEARNER)
        if not text:
            continue
        target = row.get("target_id") if row.get("target_id") in los else row.get("anchor_learning_object_id")
        shown, _note, withheld = statement_text(
            past, rule, "learner_text_gap", row["id"], text, STATEMENT_CHARS,
            answers=[row["attempt_id"]] if row.get("attempt_id") else [],
            items=[row["practice_item_id"]] if row.get("practice_item_id") else [],
            los=(row.get("anchor_learning_object_id"),))
        if withheld or not shown:
            continue
        found.append({"topic": titles.get(str(target), str(target)), "kind": f"named {row['kind']}",
                      "statement": shown, "written_by": written_by, "_at": str(row.get("created_at") or "")})
    return found


def _recent_answers(connection: Any, past: Any, rule: _AnswerText, los: Sequence[str],
                    titles: Mapping[str, str]) -> list[dict[str, Any]]:
    from learnloop.learner_protection import attempt_result, past_work_text

    rows = [dict(row) for row in connection.execute(
        f"SELECT id, learning_object_id, correctness, learner_answer_md, created_at FROM practice_attempts "
        f"WHERE learning_object_id IN ({_marks(los)}) AND learner_answer_md IS NOT NULL "
        f"AND TRIM(learner_answer_md) != '' ORDER BY created_at DESC, id DESC LIMIT ?",
        (*los, ATTEMPTS_SCANNED))]
    held = past.held([row["id"] for row in rows])
    shown: list[dict[str, Any]] = []
    for row in rows:
        text = past_work_text(past, rule, row["id"], row["learning_object_id"], row["learner_answer_md"],
                              ANSWER_CHARS)
        if text.withheld or not text.answer:
            continue  # protected work shows nothing; the next unprotected answer takes its place
        entry: dict[str, Any] = {"topic": titles.get(row["learning_object_id"], row["learning_object_id"]),
                                 "answered_at": row["created_at"],
                                 "result": attempt_result(row["correctness"], row["id"] in held).replace("_", " "),
                                 "answer": text.answer}
        if text.stem:
            entry["question"] = text.stem
        shown.append(entry)
        if len(shown) >= RECENT_ANSWERS:
            break
    return shown


def learner_state(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> dict[str, Any] | None:
    """The author's ``learner_state`` for these topics (module docstring), or
    None when there is nothing to say (no statement, no answer, every topic
    new) or it cannot be read (the author is then sent the predecessor's
    payload)."""

    from learnloop.learner_protection import PastWork
    from learnloop.source_retrieval.reading_paths import lo_statuses

    los = [lo for lo in dict.fromkeys(str(lo) for lo in learning_object_ids) if lo in vault.learning_objects]
    los = los[:MAX_TOPICS]
    if not los:
        return None
    titles = {lo: str(getattr(vault.learning_objects[lo], "title", "") or lo) for lo in los}
    try:
        statuses = lo_statuses(vault, repository, los)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            past = PastWork(connection, vault, repository)
            rule = _AnswerText(past)
            statements = [*_misconception_statements(connection, repository, past, rule, los, titles),
                          *(_gap_statements(connection, past, rule, los, titles)
                            if _table(connection, "learner_text_gaps") else [])]
            answers = _recent_answers(connection, past, rule, los, titles)
    except Exception:  # noqa: BLE001 - the author is then told nothing about the learner
        _LOG.warning("figure learner state could not be read; the figure is built without it", exc_info=True)
        return None
    statements.sort(key=lambda entry: entry["_at"], reverse=True)
    statements = [{key: value for key, value in entry.items() if key != "_at"} for entry in statements]
    statements = statements[:MAX_STATEMENTS]
    topics = [{"topic": titles[lo], "status": STATUS_WORDS.get(statuses[lo].status, statuses[lo].status)}
              for lo in los if lo in statuses]
    if not statements and not answers and all(statuses[lo].status == "new" for lo in los if lo in statuses):
        return None
    state: dict[str, Any] = {"topics": topics}
    if statements:
        state["open_questions"] = statements
    if answers:
        state["recent_answers"] = answers
    return state


def state_hash(state: Mapping[str, Any] | None) -> str | None:
    """The reuse key's name for a non-empty state (None for none)."""

    return content_key({"learner_state": dict(state)}) if state else None


__all__ = [
    "ANSWER_CHARS",
    "ATTEMPTS_SCANNED",
    "MAX_STATEMENTS",
    "MAX_TOPICS",
    "QUESTION_CHARS",
    "RECENT_ANSWERS",
    "STATEMENT_CHARS",
    "STATUS_WORDS",
    "anchored_learning_objects",
    "enabled",
    "excerpt",
    "learner_state",
    "state_hash",
]
