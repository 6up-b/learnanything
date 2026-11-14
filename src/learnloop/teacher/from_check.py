"""What a diagnostic check found, for a lesson the learner opened from it (``brief["from_check"]``).

Two controls hand a check to a lesson: "Teach me this" when a check ends with a gap to teach, and "Stop diagnosing and
teach me" during one. Both persist the check's typed transition decision on its episode before the lesson opens
(``diagnosis.probe_episodes.stop_diagnosing_and_teach``, ``diagnosis.probe_blocks.end_diagnostic_block``), and the
lesson's opening names the episode. Without this entry the lesson would know the check's answers only as cold results
("result only") and would find the gap again itself.

**Topic-level words only.** A check's questions re-serve, so nothing here quotes or paraphrases one, its answer or the
grader's notes on it (``learner_protection.WITHHELD_PROBE`` still withholds those and everything written about them).
The entry is the decision's diagnosed gap named as the topic's own words (a registered mix-up's statement, a confused
concept's title, or a fixed phrase for a template hypothesis), its confidence rounded to tens, and whether the next step
repairs a belief or teaches from the start. The first error step (an id inside a protected answer's trace), the
posterior, the tutor's move and its scaffold and reveal numbers never leave the decision.

**An episode that doesn't fit is ignored, never refused.** One on another topic, still measuring, abandoned, or with no
typed decision (an opening stamp has a ``kind``) gives no entry; the lesson opens as "Teach me this" on the topic does,
and the open turn's record says why. Read-only: nothing is written and no model is called.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.diagnosis.probe_hypotheses import (
    CONFUSES_PREFIX,
    H_OTHER,
    H_PROCEDURE_WITHOUT_SELECTION,
    H_RECALL_WITHOUT_MECHANISM,
    H_ROBUST,
    H_SCHEMA_WITHOUT_TRANSFER,
    H_SURFACE_ONLY,
    H_UNFAMILIAR,
    MISCONCEPTION_PREFIX,
)

_LOG = logging.getLogger(__name__)

VERSION = "lesson_from_check_v1"

#: What the teacher reads the entry as (the doctrine names no such key, so the entry says what it is).
ABOUT = ("What the short check on this topic found just before this lesson opened. Topic-level only: the check's "
         "questions and the learner's answers to them are not given and must not be asked about.")

#: The template hypotheses' gaps in plain words (``diagnosis.probe_hypotheses``, §6.1).
_TEMPLATE_WORDS = {
    H_UNFAMILIAR: ("not_learned_yet", "has not learned this topic yet"),
    H_SURFACE_ONLY: ("surface_only", "knows the surface of this topic but not why it works"),
    H_RECALL_WITHOUT_MECHANISM: ("recall_without_mechanism", "recalls the statement without the mechanism behind it"),
    H_PROCEDURE_WITHOUT_SELECTION: ("procedure_without_selection",
                                    "can run the procedure but not choose when to use it"),
    H_SCHEMA_WITHOUT_TRANSFER: ("schema_without_transfer", "has the idea but does not carry it to new situations"),
    H_OTHER: ("unnamed", "a cause the check could not name"),
    H_ROBUST: ("no_gap", "no gap: the check leaned towards a sound grasp"),
}

#: Why an episode gave no entry (the open turn's record).
NOT_FOUND = "the check is not on record"
OTHER_TOPIC = "the check was on another topic"
STILL_OPEN = "the check has not ended"
NO_DECISION = "the check recorded no finding"
UNREADABLE = "the check's finding could not be read"

_ENDED = {"complete": "the check finished", "converted_to_tutoring": "the learner stopped the check and asked to be taught"}


def _misconception_statement(repository: Any, misconception_id: str) -> str | None:
    with repository.connection() as connection:
        row = connection.execute("SELECT statement FROM misconceptions WHERE id = ?", (misconception_id,)).fetchone()
    return None if row is None or not str(row[0] or "").strip() else " ".join(str(row[0]).split())


def _gap(vault: Any, repository: Any, label: str) -> dict[str, str]:
    if label.startswith(MISCONCEPTION_PREFIX):
        key = label[len(MISCONCEPTION_PREFIX):]
        statement = _misconception_statement(repository, key)
        # A legacy hypothesis keys on an error type, not a registered mix-up: its name is the words there are.
        return {"kind": "mix_up", "words": statement or key.replace("_", " ")}
    if label.startswith(CONFUSES_PREFIX):
        key = label[len(CONFUSES_PREFIX):]
        other = vault.concepts.get(key) or vault.learning_objects.get(key)
        return {"kind": "confused_with", "words": f"mixes this topic up with {other.title if other else 'a neighbouring topic'}"}
    kind, words = _TEMPLATE_WORDS.get(label, _TEMPLATE_WORDS[H_OTHER])
    return {"kind": kind, "words": words}


def _confidence(value: Any) -> str | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not 0.0 <= number <= 1.0:
        return None
    return f"about {round(number * 10) * 10}%"


def from_check(vault: Any, repository: Any, *, probe_episode_id: str,
               learning_object_ids: Sequence[str]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """``(the brief's entry or None, the open turn's record)`` for a lesson opened from this check."""

    record: dict[str, Any] = {"version": VERSION, "probe_episode_id": probe_episode_id}

    def ignored(why: str) -> tuple[None, dict[str, Any]]:
        _LOG.warning("lesson from a check: episode %s ignored (%s)", probe_episode_id, why)
        record.update({"status": "ignored", "why": why})
        return None, record

    try:
        episode = repository.probe_episode(probe_episode_id)
    except Exception:  # noqa: BLE001 - a lesson opens without the finding rather than not at all
        _LOG.warning("lesson from a check: episode %s could not be read", probe_episode_id, exc_info=True)
        return ignored(UNREADABLE)
    if episode is None:
        return ignored(NOT_FOUND)
    if episode.learning_object_id not in set(learning_object_ids):
        return ignored(OTHER_TOPIC)
    if episode.status not in _ENDED:
        return ignored(STILL_OPEN)
    decision = episode.target_decision
    # Only a typed transition is a finding: an opening or relock stamp carries a ``kind`` (tutor_qa's rule).
    if not isinstance(decision, Mapping) or not decision or "kind" in decision:
        return ignored(NO_DECISION)
    lo = vault.learning_objects.get(episode.learning_object_id)
    entry: dict[str, Any] = {
        "about": ABOUT,
        "topic": lo.title if lo is not None else episode.learning_object_id,
        "learning_object_id": episode.learning_object_id,
        "ended": _ENDED[episode.status],
        "gap": _gap(vault, repository, str(decision.get("diagnosed_gap") or H_OTHER)),
        "next_step": "repair the belief" if decision.get("instructional_intent") == "repair" else "teach it",
    }
    confidence = _confidence(decision.get("diagnostic_confidence"))
    if confidence is not None:
        entry["confidence"] = confidence
    record.update({"status": "used", "why": ""})
    return entry, record


__all__ = ["ABOUT", "VERSION", "from_check"]
