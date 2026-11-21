"""Shared builders for the attempt-facts tests: stored attempts, help rows, questions, reveals and presentations
written straight into a basic vault's database, and the mapping from attempt facts onto adaptive difficulty's own
facts (which adaptive difficulty cannot import, so it lives with the tests)."""

from __future__ import annotations

from contextlib import closing
import sqlite3
from typing import Any

from learnloop.adaptive_difficulty import outcomes as O
from learnloop.attempts.facts import AttemptFacts

ITEM = "pi_svd_define_001"
LO = "lo_svd_definition"


def raw(path: Any) -> sqlite3.Connection:
    """A plain connection on the vault's database (foreign keys off: a presentation's block is not built)."""

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def insert(path: Any, table: str, **values: Any) -> None:
    with closing(raw(path)) as connection:
        names = list(values)
        connection.execute(f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
                           [values[name] for name in names])
        connection.commit()


def attempt(path: Any, attempt_id: str, created_at: str, *, item: str = ITEM, lo: str = LO,
            attempt_type: str = "independent_attempt", **values: Any) -> None:
    insert(path, "practice_attempts", id=attempt_id, practice_item_id=item, learning_object_id=lo,
           practice_mode="constructed_response", attempt_type=attempt_type, created_at=created_at,
           learner_answer_md=values.pop("learner_answer_md", "an answer"), **values)


def assist(path: Any, assist_id: str, requested_at: str, *, item: str = ITEM, shown: int = 1, **values: Any) -> None:
    insert(path, "help_assists", id=assist_id, surface=values.pop("surface", "practice"),
           assist_kind=values.pop("assist_kind", "hint"), practice_item_id=item,
           chooser=values.pop("chooser", "none"), shown=shown, requested_at=requested_at, **values)


def reveal(path: Any, reveal_id: str, created_at: str, *, item: str = ITEM, amount: float = 0.2,
           source_kind: str = "tutor_answer", **values: Any) -> None:
    insert(path, "reveal_events", id=reveal_id, practice_item_id=item, learning_object_id=LO,
           source_kind=source_kind, amount=amount, created_at=created_at, **values)


def question(path: Any, question_id: str, created_at: str, attempt_id: str, **values: Any) -> None:
    insert(path, "question_events", id=question_id, context=values.pop("context", "practice"),
           question_md="why?", created_at=created_at, attempt_id=attempt_id,
           practice_item_id=values.pop("practice_item_id", ITEM), **values)


def presentation(path: Any, presentation_id: str, served_at: str, *, item: str = ITEM) -> None:
    insert(path, "plan_presentations", id=presentation_id, block_id=f"blk_{presentation_id}", practice_item_id=item,
           origin="plan", served_at=served_at)


def ad_facts(facts: AttemptFacts, *, stuck: bool = False, pre_exposed: bool = False) -> O.AttemptFacts:
    """Adaptive difficulty's facts built from attempt facts the way its replay builds them from the same stored
    values (``adaptive_difficulty.replay.load_events``): the submitted count and flags, the help-equivalent
    practice questions' progress markers, and a bound plan presentation."""

    return O.AttemptFacts(
        correctness=None if facts.correctness is None else float(facts.correctness),
        hints_used=int(facts.hints_used or 0),
        first_hint_progress=facts.first_hint_progress,
        help_questions=O.help_questions_from_rows(
            {"context": question.context, "hint_equivalent": question.hint_equivalent,
             "question_type": question.question_type, "attempt_progress": question.attempt_progress,
             "seconds_into_attempt": question.seconds_into_attempt} for question in facts.questions),
        primed=bool(facts.primed),
        pre_exposed=pre_exposed,
        bound_presentation=facts.bound_presentation,
        stuck=stuck,
    )
