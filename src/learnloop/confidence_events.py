"""Teacher TE0: the learner's confidence, rendered as events (spec_teacher_v1 §15.2).

Two readings of how sure the learner was exist, and no model role read
either before TE0:

* **the tap**: ``practice_attempts.answer_confidence`` (1-5, migration 031),
  the learner's own mark before the answer was graded;
* **the hedge read**: ``grading_evidence.learner_confidence`` on the attempt's
  current (unsuperseded) criterion rows, the grader's reading of the answer's
  tone (``hedged`` or ``confident``; ``absent`` and ``unknown`` say nothing).
  Rows written from a stated number rather than read from an answer (a
  self-grade, an imported exam outcome, a simulated grade:
  :data:`NOT_GRADER_READS`) are not hedge reads.

Both are rendered as **events in words with the attempt's outcome**, for
example "marked 5/5 sure; wrong" or "no tap; the grader read the answer as
hedged; right", never as raw scalars or threshold counts: the reading models
decide what counts as confident (§15.2). One stated limit goes with them
(:func:`taps_limit`): when the taps so far do not span the tap's scale, the
context says so ("your taps so far are all 4-5"), since a reader cannot
calibrate a confidence that never varies.

Readers: the router card (``daily_plan.router_card``), the history-aware
diagnoser (``diagnosis.split``), the hint writer and the tutor. **Never the
blind grader** (blind-split S1): nothing in ``attempts.blind_grading`` or
``attempts.grading`` imports this module, and a test pins it.

Protection (:func:`learner_events`, the hint writer's and the tutor's
block): an attempt whose question and answer a model context withholds
(``learner_protection.attempt_protection``: exam or held-out material, a
reserved surface, a check waiting, a diagnostic probe) contributes no event,
and when the protection cannot be read no event shows at all (fail closed).
A held grade is "held for review", never a score (THE predicate). The card
keeps its own rule (protected past work keeps its result there, so its
confidence event stays with it).

Consistency (review F2): an attempt's outcome, its hedge read, whether its
grade is held and the taps so far are read in ONE read snapshot
(:func:`learner_events`, ``diagnosis.split.live.current_confidence``, the
router card's gatherer), so a regrade committed between two reads never
yields an event that neither revision recorded.

Kill switch (review F5): ``teacher.confidence_events_enabled`` (default on;
:func:`enabled`), read by every reader. Off, no reader carries an event or
the limit, and each context is its predecessor's (the card is a
``learner_state_card_v1`` card).

TE0 changes model contexts and the card only: no persisted meaning, no
learned weight (the tap/hedge recalibration is LP-min, later). Read-only;
nothing is written and no model is called.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_LOG = logging.getLogger(__name__)

#: The block's identity inside a model context (receipts read it there).
VERSION = "confidence-events-v1"
#: What a reading model is told about the block (no rule: the model decides).
NOTE = (
    "How sure the learner said they were before the answer was graded (their tap, 1 to 5) and how the "
    "grader read the tone of the answer (hedged or confident), each with how the answer was graded. These "
    "are events, not a score: decide from them, with the rest of the evidence, what they say about this "
    "learner. Never quote them back as a judgement of the learner."
)
#: The tap's own scale (structural: migration 031's CHECK).
TAP_MIN = 1
TAP_MAX = 5
HEDGE_VALUES = ("hedged", "confident")
#: ``grading_evidence.local_grader_id`` values whose ``learner_confidence`` was
#: derived from a stated number, not read from the answer.
NOT_GRADER_READS = frozenset({"self", "exam_import", "sim"})
#: Prompt-size bound on the events one hint-writer or tutor context carries
#: per topic (the newest first; ``keep``: a size bound, never a judgement).
CONTEXT_EVENT_LIMIT = 12
_CHUNK = 500

_RESULT_WORDS = {
    "correct": "right",
    "incorrect": "wrong",
    "partial": "partly right",
    "held_for_review": "held for review (no score yet)",
    "not_graded": "not graded",
}
_HEDGE_WORDS = {
    "hedged": "the grader read the answer as hedged",
    "confident": "the grader read the answer as confident",
    "mixed": "the grader read parts of the answer as hedged",
}


def enabled(vault: Any) -> bool:
    """TE0's kill switch, ``teacher.confidence_events_enabled`` (default on)."""

    teacher = getattr(getattr(vault, "config", None), "teacher", None)
    return bool(getattr(teacher, "confidence_events_enabled", True))


@dataclass(frozen=True)
class Reading:
    """One attempt's tap and hedge read (either may be missing)."""

    tap: int | None = None
    #: ``hedged`` | ``confident`` | ``mixed`` (criteria read both ways) | None.
    hedge: str | None = None

    @property
    def present(self) -> bool:
        return self.tap is not None or self.hedge is not None


def valid_tap(value: Any) -> int | None:
    try:
        tap = int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    return tap if tap is not None and TAP_MIN <= tap <= TAP_MAX else None


def combine_hedges(values: Iterable[Any]) -> str | None:
    """An attempt's hedge read from its criterion reads: all hedged, all
    confident, or ``mixed``; None when no criterion was read either way."""

    seen = {str(value) for value in values if str(value or "") in HEDGE_VALUES}
    if not seen:
        return None
    return seen.pop() if len(seen) == 1 else "mixed"


def hedge_from_record(record: Mapping[str, Any] | None) -> str | None:
    """The hedge read of a blind-grade record (its criteria's ``learner_confidence``)."""

    rows = (record or {}).get("criteria") or ()
    return combine_hedges(row.get("learner_confidence") for row in rows if isinstance(row, Mapping))


def result_class(score: Any, max_points: Any, *, held: bool = False) -> str:
    """The outcome class of a score out of ``max_points`` (``attempt_result``'s classes)."""

    from learnloop.learner_protection import attempt_result

    if held:
        return "held_for_review"
    try:
        correctness = float(score) / float(max_points) if score is not None and max_points else None
    except (TypeError, ValueError, ZeroDivisionError):
        correctness = None
    return attempt_result(correctness, False)


def event_text(reading: Reading | None, result: str) -> str | None:
    """The event in words ("marked 5/5 sure; wrong"), or None with no reading."""

    if reading is None or not reading.present:
        return None
    parts = [f"marked {reading.tap}/{TAP_MAX} sure" if reading.tap is not None else "no tap"]
    if reading.hedge is not None:
        parts.append(_HEDGE_WORDS.get(reading.hedge, f"the grader read the answer as {reading.hedge}"))
    parts.append(_RESULT_WORDS.get(result, str(result).replace("_", " ")))
    return "; ".join(parts)


def current_block(reading: Reading | None, result: str, taps: Sequence[Any] = ()) -> dict[str, Any] | None:
    """The diagnosed attempt's block (version, note, event and the stated
    limit over ``taps``, which include its own); None with no reading. Live
    and offline diagnosis both build it here (review F4)."""

    event = event_text(reading, result)
    if event is None:
        return None
    block: dict[str, Any] = {"version": VERSION, "note": NOTE, "event": event}
    limit = taps_limit(taps)
    if limit:
        block["taps_so_far"] = limit
    return block


def taps_limit(taps: Sequence[Any]) -> str | None:
    """The stated limit when the taps so far do not span the tap's scale, or None.

    "Your taps so far are all 4-5 (29 taps)": the range is a fact, the scale
    bounds are structural, and nothing here judges what spread is enough."""

    values = [tap for tap in (valid_tap(value) for value in taps) if tap is not None]
    if not values:
        return None
    low, high = min(values), max(values)
    if low == TAP_MIN and high == TAP_MAX:
        return None
    span = f"{low}" if low == high else f"{low}–{high}"
    count = len(values)
    return f"your taps so far are all {span} ({count} tap{'s' if count != 1 else ''})"


# -- reads ----------------------------------------------------------------------------


def _columns(connection: Any, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _chunks(values: Sequence[str]) -> Iterable[Sequence[str]]:
    for start in range(0, len(values), _CHUNK):
        yield values[start:start + _CHUNK]


def read_hedges(connection: Any, attempt_ids: Iterable[Any] | None = None) -> dict[str, str]:
    """Each attempt's hedge read from its current grading evidence (all
    attempts when ``attempt_ids`` is None); attempts with none are absent."""

    columns = _columns(connection, "grading_evidence")
    if not {"learner_confidence", "superseded_at"} <= columns:
        return {}
    grader = "local_grader_id" if "local_grader_id" in columns else "NULL"
    query = (f"SELECT attempt_id, learner_confidence, {grader} FROM grading_evidence "
             "WHERE superseded_at IS NULL AND learner_confidence IN ('hedged', 'confident')")
    reads: dict[str, list[str]] = {}

    def take(rows: Iterable[Any]) -> None:
        for attempt_id, value, local_grader in rows:
            if local_grader is not None and str(local_grader) in NOT_GRADER_READS:
                continue
            reads.setdefault(str(attempt_id), []).append(str(value))

    if attempt_ids is None:
        take(connection.execute(query + " ORDER BY attempt_id, id"))
    else:
        ids = sorted({str(value) for value in attempt_ids if value})
        for chunk in _chunks(ids):
            marks = ",".join("?" for _ in chunk)
            take(connection.execute(query + f" AND attempt_id IN ({marks}) ORDER BY attempt_id, id", tuple(chunk)))
    return {attempt_id: hedge for attempt_id, values in reads.items() if (hedge := combine_hedges(values))}


def taps_before(connection: Any, before_iso: str) -> list[int]:
    """Every tap on an attempt created strictly before ``before_iso`` (for :func:`taps_limit`)."""

    if "answer_confidence" not in _columns(connection, "practice_attempts"):
        return []
    rows = connection.execute(
        "SELECT answer_confidence FROM practice_attempts WHERE answer_confidence IS NOT NULL AND created_at < ?",
        (before_iso,),
    )
    return [tap for (value,) in rows if (tap := valid_tap(value)) is not None]


def readings(connection: Any, attempts: Sequence[Mapping[str, Any]]) -> dict[str, Reading]:
    """The readings of ``attempts`` (rows carrying ``id`` and, when read,
    ``answer_confidence``); attempts with neither reading are absent."""

    hedges = read_hedges(connection, [row["id"] for row in attempts])
    out: dict[str, Reading] = {}
    for row in attempts:
        reading = Reading(tap=valid_tap(row.get("answer_confidence")), hedge=hedges.get(str(row["id"])))
        if reading.present:
            out[str(row["id"])] = reading
    return out


def learner_events(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], before_iso: str,
                   titles: Mapping[str, str] | None = None, limit: int = CONTEXT_EVENT_LIMIT) -> dict[str, Any] | None:
    """The block a hint-writer or tutor context carries: per topic in
    ``learning_object_ids``, the learner's confidence events before
    ``before_iso``, newest first, each "YYYY-MM-DD: <event>", with the stated
    limit. An attempt the shared protection withholds contributes nothing.
    None when there is no event (the context then renders exactly as before
    TE0), when the protection cannot be read (fail closed), and with the
    kill switch off. The outcomes, hedge reads, held grades and taps are
    read in one snapshot (review F2)."""

    from learnloop import learner_protection as protection
    from learnloop.db.stores.write_provenance import read_snapshot

    if not enabled(vault):
        return None
    los = [str(lo) for lo in dict.fromkeys(learning_object_ids) if lo]
    if not los:
        return None
    marks = ",".join("?" for _ in los)
    with repository.connection() as connection, read_snapshot(connection):
        columns = _columns(connection, "practice_attempts")
        if "answer_confidence" not in columns:
            return None
        probe = "probe_presentation_id" if "probe_presentation_id" in columns else "NULL AS probe_presentation_id"
        rows = [dict(row) for row in connection.execute(
            "SELECT id, learning_object_id, practice_item_id, attempt_type, correctness, answer_confidence, "
            f"created_at, {probe} FROM practice_attempts WHERE learning_object_id IN ({marks}) AND created_at < ? "
            "ORDER BY created_at DESC, id DESC",
            (*los, before_iso),
        )]
        found = readings(connection, rows)
        held = protection.held_attempts(connection, list(found)) if found else frozenset()
        taps = taps_before(connection, before_iso) if found else []
    if not found:
        return None
    # The shared protection, read only when there is something to show.
    withheld = protection.withheld_items(vault, repository)
    if not withheld.available:
        return None
    kept: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if str(row["id"]) not in found or protection.attempt_protection(
                withheld, {"item": row["practice_item_id"], "type": row["attempt_type"],
                           "probe": row["probe_presentation_id"]}) is not None:
            continue
        bucket = kept.setdefault(str(row["learning_object_id"]), [])
        if len(bucket) < limit:
            bucket.append(row)
    if not kept:
        return None
    topics = []
    for lo in los:
        events = []
        for row in kept.get(lo, ()):
            result = protection.attempt_result(row["correctness"], str(row["id"]) in held)
            events.append(f"{str(row['created_at'])[:10]}: {event_text(found[str(row['id'])], result)}")
        if events:
            topics.append({"topic": (titles or {}).get(lo, lo), "events": events})
    block: dict[str, Any] = {"version": VERSION, "note": NOTE, "topics": topics}
    limit_text = taps_limit(taps)
    if limit_text:
        block["taps_so_far"] = limit_text
    return block


def safe_learner_events(vault: Any, repository: Any, **kwargs: Any) -> dict[str, Any] | None:
    """:func:`learner_events`, or None when it cannot be read (never fails a hint or an answer)."""

    try:
        return learner_events(vault, repository, **kwargs)
    except Exception:  # noqa: BLE001 - a context without the block, never a failed request
        _LOG.warning("confidence events not read", exc_info=True)
        return None


__all__ = [
    "CONTEXT_EVENT_LIMIT",
    "NOTE",
    "NOT_GRADER_READS",
    "Reading",
    "VERSION",
    "combine_hedges",
    "current_block",
    "enabled",
    "event_text",
    "hedge_from_record",
    "learner_events",
    "read_hedges",
    "readings",
    "result_class",
    "safe_learner_events",
    "taps_before",
    "taps_limit",
    "valid_tap",
]
