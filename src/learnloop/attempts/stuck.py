""""Write what you can" replaces "I don't know" (``mvp-0.13``).

The learner's "I'm stuck" control opens the answer box with one prompt. What
they send is an ORDINARY attempt at the standard attempt mass:

* with text, it is graded by the grader (the blind grader in split vaults,
  the joint grader when the split is switched off) and diagnosed like any
  other answer. The grader also returns a :class:`StuckReading`: whether the
  text attempts the answer, whether it says what is confusing, and the
  learner's own words for it. A reading that describes confusion becomes a
  ``stuck_confusion`` interaction signal on the item's LO
  (``learnloop.field.signals``). Text on a choice item never takes the
  option-letter shortcut: the grader reads it;
* empty, it is scored 0 by a deterministic grade, with no model call (there
  is nothing to grade) and, by owner decision 2026-10-12, no error tag: no
  attribution and no error event.

Nothing here is ``dont_know``: there is no separate weight. The algorithm
version gates the control and ``stuck_prompt.enabled`` is its kill switch;
replay never reads either (the persisted ``practice_attempts.declared_stuck``
column and the reading's ``judgment_ledger`` verdict are what an attempt was).

This module is a leaf: wire model, prompt text, the activity gate, the
reading's ``judgment_ledger`` verdict (task ``stuck_reading``, written in the
grading transaction) and a read-only view of stuck answers for the later
learner-text-gaps stage (every stuck answer, :func:`stuck_answers`, or one
by its id, :func:`stuck_answer`).
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.algorithm_versions import STUCK_PROMPT_VERSIONS
from learnloop.attempt_types import default_attempt_type

#: The control's label and the one prompt it opens the answer box with.
STUCK_CONTROL_LABEL = "I'm stuck"
STUCK_PROMPT_TEXT = "Write what you can, or what's confusing you"
#: ``BlindGradingContext.answer_prompt["kind"]`` for a stuck answer.
STUCK_ANSWER_PROMPT_KIND = "stuck"
#: Appended to the blind prompt version when the stuck rules are in the task.
STUCK_PROMPT_VERSION_SUFFIX = "+stuck-v1"
#: The blind record key holding the validated reading (the diagnoser's
#: context shows it with the attempt's blind grade).
STUCK_READING_KEY = "stuck_reading"
STUCK_READING_VERSION = "stuck-reading-v1"
#: ``judgment_ledger.task`` of the grader's classification of a stuck answer
#: (review F6): one single-record verdict per grading, ``left`` = the
#: attempt, the verdict the verified reading as JSON. A regrade appends a
#: superseding one. :func:`stuck_answers` reads the current one back.
STUCK_READING_JUDGMENT_TASK = "stuck_reading"
#: The deterministic grade of an empty stuck answer: ``grading_evidence`` tier
#: 2 ("heuristic auto-grade"), so the deferred self-grade regrade (tier 1)
#: never sends it to a model, and this local grader id names it.
EMPTY_STUCK_LOCAL_GRADER_ID = "empty_stuck_answer"
EMPTY_STUCK_GRADER_TIER = 2
EMPTY_STUCK_EVIDENCE = "Empty answer sent with \"I'm stuck\": nothing to grade, scored 0."
EMPTY_STUCK_FEEDBACK = (
    "You were stuck and sent nothing, so this counts as an ordinary answer "
    "scored 0. The worked answer is shown below."
)


def stuck_prompt_active(vault: Any) -> bool:
    """Does this vault offer "I'm stuck" for NEW answers?

    The algorithm version gates it; ``stuck_prompt.enabled`` is its kill
    switch. Read only when an answer is recorded or a surface is drawn.
    """

    config = vault.config
    if config.algorithms.algorithm_version not in STUCK_PROMPT_VERSIONS:
        return False
    section = getattr(config, "stuck_prompt", None)
    return bool(getattr(section, "enabled", True))


def stuck_answer_prompt() -> dict[str, str]:
    """What the blind grader is told about how the answer was asked for."""

    return {
        "kind": STUCK_ANSWER_PROMPT_KIND,
        "control": STUCK_CONTROL_LABEL,
        "prompt": STUCK_PROMPT_TEXT,
    }


def stuck_attempt_type(
    allowed: list[str] | tuple[str, ...] | None,
    *,
    hints_used: int = 0,
    probe: bool = False,
) -> str:
    """The ordinary attempt type a stuck answer records on this item.

    The same choice the answer box makes for a submitted answer: a committed
    diagnostic presentation forces ``diagnostic_probe``; hints prefer
    ``hinted_attempt`` where the item allows it; otherwise the item's default
    recording type. Never ``dont_know``.
    """

    if probe:
        return "diagnostic_probe"
    if hints_used > 0 and (not allowed or "hinted_attempt" in allowed):
        return "hinted_attempt"
    return default_attempt_type(allowed)


def is_empty_stuck(draft: Any) -> bool:
    """A declared-stuck draft with nothing written (the deterministic zero)."""

    return bool(getattr(draft, "declared_stuck", False)) and not str(
        getattr(draft, "learner_answer_md", "") or ""
    ).strip()


class StuckReading(WireModel):
    """How the grader read an answer written under the stuck prompt.

    Generated after the grade, so it never moves a criterion. The marker the
    confusion signal and the learner-text-gaps stage read.
    """

    attempts_answer: bool = Field(
        description=(
            "True when the text makes ANY attempt at the answer itself "
            "(a step, a claim, a partial result)."
        )
    )
    describes_confusion: bool = Field(
        description=(
            "True when the text says what the learner is confused or unsure "
            "about: a question, or a named concept, step, term or condition "
            "they cannot do. 'No idea' alone names nothing and is false."
        )
    )
    confusion_quote: str = Field(
        default="",
        description=(
            "When describes_confusion is true: the learner's words that state "
            "the confusion, copied VERBATIM from the answer. Empty otherwise."
        ),
    )


STUCK_PROMPT_RULES = (
    "STUCK PROMPT (`context.answer_prompt`). The learner pressed \"I'm stuck\" "
    "and was asked: \"Write what you can, or what's confusing you\". Grade the "
    "text as an answer exactly as you would any other, against the same "
    "rubric: award points only for correct work actually shown. Text that only "
    "describes confusion earns no criterion points; admitting confusion is "
    "never itself an error. Do not use the retrieval-failure error type merely "
    "because the learner says they are stuck. LAST, fill `stuck_reading`: "
    "`attempts_answer`, `describes_confusion`, and `confusion_quote` copied "
    "verbatim from the learner's answer when it describes confusion."
)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def verified_stuck_reading(reading: StuckReading, learner_answer_md: str) -> dict[str, Any]:
    """The persisted marker: the reading plus whether its quote is verbatim.

    A quote not found in the answer (whitespace and case aside) is dropped,
    never kept as the learner's words; the confusion flag stands, and the
    full answer text remains the confusion text.
    """

    quote = (reading.confusion_quote or "").strip()
    verified = bool(quote) and reading.describes_confusion and _squash(quote) in _squash(
        learner_answer_md
    )
    return {
        "version": STUCK_READING_VERSION,
        "attempts_answer": bool(reading.attempts_answer),
        "describes_confusion": bool(reading.describes_confusion),
        "confusion_quote": quote if verified else "",
        "quote_verified": verified,
    }


def _current_stuck_judgment(connection: Any, attempt_id: str) -> Any:
    """The attempt's current stuck-reading judgment row (None when there is none).

    Current = not superseded by another; ties (none are written) fall back to
    the latest.
    """

    return connection.execute(
        """
        SELECT j.id, j.created_at, j.verdict FROM judgment_ledger j
        WHERE j.task = ? AND j.left_kind = 'attempt' AND j.left_id = ?
          AND j.right_kind IS NULL
          AND NOT EXISTS (SELECT 1 FROM judgment_ledger s WHERE s.supersedes_id = j.id)
        ORDER BY j.created_at DESC, j.id DESC LIMIT 1
        """,
        (STUCK_READING_JUDGMENT_TASK, attempt_id),
    ).fetchone()


def record_stuck_reading_judgment(
    connection: Any,
    *,
    attempt_id: str,
    marker: Mapping[str, Any],
    judge_model: str | None,
    prompt_version: str,
    input_hash: str,
    created_at: str,
) -> str:
    """Append the grader's reading of a stuck answer to ``judgment_ledger``.

    Called inside the transaction that records the grade (and, blind, its
    blind record), so the verdict and the measurement commit together. A
    reading of an attempt that already has one (a regrade) supersedes it.
    ``input_hash`` is the grading context hash; ``prompt_version`` the
    grader's (with the ``+stuck-v1`` suffix).
    """

    from learnloop.db.stores.judgments import append_judgment

    current = _current_stuck_judgment(connection, attempt_id)
    confused = bool(marker.get("describes_confusion"))
    quote = str(marker.get("confusion_quote") or "")
    rationale = (
        f"stuck answer describes confusion: {quote!r}" if confused and quote
        else "stuck answer describes confusion" if confused
        else "stuck answer describes no confusion"
    )
    return append_judgment(
        connection,
        task=STUCK_READING_JUDGMENT_TASK,
        left_kind="attempt",
        left_id=attempt_id,
        judge="llm",
        judge_model=str(judge_model or "unknown"),
        prompt_version=prompt_version,
        input_hash=input_hash,
        verdict=json.dumps(dict(marker), sort_keys=True),
        rationale=rationale,
        supersedes_id=str(current[0]) if current is not None else None,
        created_at=created_at,
    )


def _has_table(connection: Any, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        is not None
    )


def _has_stuck_column(connection: Any) -> bool:
    if not _has_table(connection, "practice_attempts"):
        return False
    return any(
        row[1] == "declared_stuck"
        for row in connection.execute("PRAGMA table_info(practice_attempts)")
    )


#: The attempt columns a stuck-answer row is built from (in this order).
_STUCK_ATTEMPT_COLUMNS = (
    "id, practice_item_id, learning_object_id, subject, session_id, "
    "attempt_type, learner_answer_md, rubric_score, created_at"
)

_Reading = tuple[str, str, "Mapping[str, Any] | None"]


def _judged_reading(row: Any) -> _Reading:
    """(judgment id, graded at, reading) from a current stuck-reading judgment."""

    try:
        verdict = json.loads(row[2] or "{}")
    except ValueError:
        verdict = None
    return str(row[0]), str(row[1]), verdict if isinstance(verdict, Mapping) else None


def _blind_reading(record_id: Any, created_at: Any, record_json: Any) -> _Reading:
    """(blind record id, graded at, reading) from a blind grade record."""

    try:
        record = json.loads(record_json or "{}")
    except ValueError:
        record = {}
    reading = record.get(STUCK_READING_KEY) if isinstance(record, dict) else None
    return str(record_id), str(created_at), reading if isinstance(reading, Mapping) else None


def _stuck_row(attempt: Any, blind: _Reading | None, judged: _Reading | None) -> dict[str, Any]:
    (
        attempt_id,
        practice_item_id,
        learning_object_id,
        subject,
        session_id,
        attempt_type,
        learner_answer_md,
        rubric_score,
        created_at,
    ) = attempt
    record_id, graded_at, reading = blind if blind is not None else (None, None, None)
    judgment_id = None
    if judged is not None:
        judgment_id, graded_at, reading = judged
    text = str(learner_answer_md or "")
    return {
        "attempt_id": str(attempt_id),
        "practice_item_id": str(practice_item_id),
        "learning_object_id": str(learning_object_id),
        "subject_id": str(subject or "default"),
        "session_id": session_id,
        "attempt_type": str(attempt_type),
        "created_at": str(created_at),
        "has_text": bool(text.strip()),
        "learner_answer_md": text,
        "rubric_score": rubric_score,
        "blind_grade_record_id": record_id,
        "judgment_id": judgment_id,
        "graded_at": graded_at,
        "reading": dict(reading) if reading is not None else None,
        "describes_confusion": bool(reading and reading.get("describes_confusion")),
    }


def stuck_answers(connection: Any) -> list[dict[str, Any]]:
    """Every stuck answer, its text and its CURRENT grader reading (read-only).

    One row per ``declared_stuck`` attempt in completion order. ``reading`` is
    the verdict of the attempt's current ``stuck_reading`` judgment (blind or
    joint grading; a regrade supersedes), or, for a blind grade recorded
    before the judgment existed, its latest blind record's reading; None for
    an empty answer (deterministic), a self-graded fallback, or a grade from
    before the reading existed. ``judgment_id`` names the verdict read. A
    vault without the column (before migration 178) has none. Never migrates.
    One attempt's row, without reading the others: :func:`stuck_answer`.
    """

    if not _has_stuck_column(connection):
        return []
    readings: dict[str, _Reading] = {}
    judgments: dict[str, _Reading] = {}
    if _has_table(connection, "judgment_ledger"):
        for (attempt_id,) in connection.execute(
            "SELECT id FROM practice_attempts WHERE declared_stuck = 1"
        ).fetchall():
            row = _current_stuck_judgment(connection, str(attempt_id))
            if row is None:
                continue
            judgments[str(attempt_id)] = _judged_reading(row)
    if _has_table(connection, "blind_grade_records"):
        for attempt_id, record_id, created_at, record_json in connection.execute(
            """
            SELECT b.attempt_id, b.id, b.created_at, b.record_json
            FROM blind_grade_records b
            JOIN practice_attempts a ON a.id = b.attempt_id
            WHERE a.declared_stuck = 1
            ORDER BY b.attempt_id, b.created_at, b.id
            """
        ):
            readings[str(attempt_id)] = _blind_reading(record_id, created_at, record_json)
    return [
        _stuck_row(attempt, readings.get(str(attempt[0])), judgments.get(str(attempt[0])))
        for attempt in connection.execute(
            f"SELECT {_STUCK_ATTEMPT_COLUMNS} FROM practice_attempts "
            "WHERE declared_stuck = 1 ORDER BY created_at, id"
        )
    ]


def stuck_answer(connection: Any, attempt_id: str) -> dict[str, Any] | None:
    """One stuck answer by its id: the row :func:`stuck_answers` gives it.

    Reads that one attempt, its current ``stuck_reading`` judgment and its
    latest blind record (the same choice of reading), never every stuck
    answer, so a caller that asks about each answer as it is recorded (the
    learner-text gaps queue) stays O(1) per answer. None when the attempt is
    not a stuck answer, does not exist, or the vault predates migration 178.
    An empty stuck answer is returned with ``has_text`` false: it carries no
    learner text. Never migrates.
    """

    if not _has_stuck_column(connection):
        return None
    attempt = connection.execute(
        f"SELECT {_STUCK_ATTEMPT_COLUMNS} FROM practice_attempts WHERE id = ? AND declared_stuck = 1",
        (attempt_id,),
    ).fetchone()
    if attempt is None:
        return None
    judged = None
    if _has_table(connection, "judgment_ledger"):
        row = _current_stuck_judgment(connection, str(attempt_id))
        if row is not None:
            judged = _judged_reading(row)
    blind = None
    if _has_table(connection, "blind_grade_records"):
        record = connection.execute(
            "SELECT id, created_at, record_json FROM blind_grade_records WHERE attempt_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (attempt_id,),
        ).fetchone()
        if record is not None:
            blind = _blind_reading(*record)
    return _stuck_row(tuple(attempt), blind, judged)


def _seconds_between(start: str | None, end: str | None) -> float | None:
    from datetime import datetime

    if not start or not end:
        return None
    try:
        begin = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        finish = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (finish - begin).total_seconds())


def stuck_answer_summary(connection: Any) -> dict[str, Any]:
    """Aggregate-only owner view: what to watch after mvp-0.13 goes live.

    * the share of stuck answers that contain text (versus empty "I'm stuck");
    * how many the grader read as describing confusion;
    * the grading wait on a stuck answer with text: the wall time of its
      blind grading run (the learner waits for it, P7). An empty one makes no
      call and is recorded at once.

    No learner text and no model output leaves this function.
    """

    rows = stuck_answers(connection)
    with_text = [row for row in rows if row["has_text"]]
    waits: list[float] = []
    if _has_table(connection, "agent_runs"):
        for started_at, completed_at in connection.execute(
            """
            SELECT started_at, completed_at FROM agent_runs
            WHERE purpose = 'grading' AND status = 'completed'
              AND prompt_version LIKE ?
            """,
            (f"%{STUCK_PROMPT_VERSION_SUFFIX}",),
        ):
            seconds = _seconds_between(started_at, completed_at)
            if seconds is not None:
                waits.append(seconds)
    waits.sort()

    def quantile(fraction: float) -> float | None:
        if not waits:
            return None
        return round(waits[min(len(waits) - 1, int(fraction * (len(waits) - 1) + 0.5))], 1)

    return {
        "total": len(rows),
        "with_text": len(with_text),
        "empty": len(rows) - len(with_text),
        "share_with_text": round(len(with_text) / len(rows), 3) if rows else None,
        "graded_with_reading": sum(row["reading"] is not None for row in with_text),
        "describes_confusion": sum(row["describes_confusion"] for row in rows),
        "grading_wait_seconds": {
            "runs": len(waits),
            "median": quantile(0.5),
            "p90": quantile(0.9),
            "max": round(waits[-1], 1) if waits else None,
        },
    }


__all__ = [
    "EMPTY_STUCK_EVIDENCE",
    "EMPTY_STUCK_FEEDBACK",
    "EMPTY_STUCK_GRADER_TIER",
    "EMPTY_STUCK_LOCAL_GRADER_ID",
    "STUCK_ANSWER_PROMPT_KIND",
    "STUCK_CONTROL_LABEL",
    "STUCK_PROMPT_RULES",
    "STUCK_PROMPT_TEXT",
    "STUCK_PROMPT_VERSION_SUFFIX",
    "STUCK_READING_JUDGMENT_TASK",
    "STUCK_READING_KEY",
    "STUCK_READING_VERSION",
    "StuckReading",
    "is_empty_stuck",
    "record_stuck_reading_judgment",
    "stuck_answer",
    "stuck_answer_prompt",
    "stuck_answer_summary",
    "stuck_answers",
    "stuck_attempt_type",
    "stuck_prompt_active",
    "verified_stuck_reading",
]
