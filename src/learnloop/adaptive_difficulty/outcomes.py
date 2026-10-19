"""§5.3's outcome categories: help-adjusted, ordinal, with an explicit censored class.

One definition of success is shared with the certification cold probe
(correctness >= 0.8) and the partial threshold with the ledger (0.40). The
forecast event everywhere (band, receipts, scoring, the update) is ``Y = 2``
on a first presentation that ends in a submitted, graded attempt.

**Help timing** ``h_t`` is a per-attempt label with an explicit ``unknown``:
ordinary hints keep only their total before AD1, so a hint with no
``first_hint_progress`` marker is ``unknown``, never "after work began". A
help-equivalent question is a practice-context tutor question bound to the
attempt that field reads as help (``hint_equivalent``, or a help type), timed
by its ``attempt_progress`` (or ``seconds_into_attempt = 0``).

**Primed attempts.** A presentation whose answer was exposed before it was
served (``pre_exposed``) is not a fresh presentation: excluded from the update
and from scoring. A primed attempt revealed during its bound presentation is
the censored factor ``{0, 1}`` (its correctness is never used). A primed
attempt with no bound presentation is excluded (its reveal's timing is unknown).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty.model import CENSORED

HELP_TYPES = frozenset({"prerequisite", "mechanism", "clarification", "strategy"})
NO_DRAFT = "no_draft"
DRAFT_STARTED = "draft_started"

NONE = "none"
BEFORE_WORK = "before_work"
AFTER_WORK = "after_work"
UNKNOWN = "unknown"

#: §5.6 step 1 (with deviation D1: hinted and "I don't know" answers are presentations too).
ELIGIBLE_TYPES = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt", "hinted_attempt",
                            "dont_know"})


@dataclass(frozen=True)
class HelpQuestion:
    """A help-equivalent practice question bound to the attempt: its logged progress marker."""

    attempt_progress: str | None = None
    seconds_into_attempt: float | None = None

    @property
    def before_work(self) -> bool:
        return self.attempt_progress == NO_DRAFT or self.seconds_into_attempt == 0

    @property
    def after_work(self) -> bool:
        return self.attempt_progress == DRAFT_STARTED


@dataclass(frozen=True)
class AttemptFacts:
    correctness: float | None
    hints_used: int = 0
    first_hint_progress: str | None = None
    help_questions: tuple[HelpQuestion, ...] = field(default_factory=tuple)
    primed: bool = False
    pre_exposed: bool = False
    bound_presentation: bool = False
    #: An empty "I'm stuck" submission or an "I don't know" answer (a fail whatever its grade);
    #: a stuck learner who wrote an answer is not this (replay.forced_failure).
    stuck: bool = False


def help_timing(facts: AttemptFacts) -> str:
    hints = int(facts.hints_used or 0) > 0
    questions = tuple(facts.help_questions)
    if not hints and not questions:
        return NONE
    if (hints and facts.first_hint_progress == NO_DRAFT) or any(q.before_work for q in questions):
        return BEFORE_WORK
    hint_after = (not hints) or facts.first_hint_progress == DRAFT_STARTED
    if hint_after and all(q.after_work for q in questions):
        return AFTER_WORK
    return UNKNOWN


def category(facts: AttemptFacts) -> int | None:
    """``2``, ``1``, ``0``, :data:`CENSORED`, or None when the attempt is excluded (§5.3)."""

    if facts.pre_exposed:
        return None
    if facts.primed:
        return CENSORED if facts.bound_presentation else None
    if facts.stuck:
        return 0
    if facts.correctness is None:
        return None
    y = float(facts.correctness)
    timing = help_timing(facts)
    if timing == BEFORE_WORK:
        return 0
    if y >= P.SUCCESS:
        return {NONE: 2, AFTER_WORK: 1, UNKNOWN: CENSORED}[timing]
    if y >= P.PARTIAL and timing == NONE:
        return 1
    return 0


def unassisted_success(category_value: int | None) -> float | None:
    """The binary event: 1 for ``Y = 2``, 0 otherwise; None when excluded. Any help, or a
    reveal during the presentation, makes it 0 (§8.3)."""

    if category_value is None:
        return None
    return 1.0 if category_value == 2 else 0.0


def help_questions_from_rows(rows: Iterable[dict]) -> tuple[HelpQuestion, ...]:
    questions = []
    for row in rows:
        if row.get("context") != "practice":
            continue
        if not (bool(row.get("hint_equivalent")) or row.get("question_type") in HELP_TYPES):
            continue
        seconds = row.get("seconds_into_attempt")
        questions.append(HelpQuestion(row.get("attempt_progress"), float(seconds) if seconds is not None else None))
    return tuple(questions)


__all__ = [
    "AFTER_WORK",
    "AttemptFacts",
    "BEFORE_WORK",
    "DRAFT_STARTED",
    "ELIGIBLE_TYPES",
    "HELP_TYPES",
    "HelpQuestion",
    "NONE",
    "NO_DRAFT",
    "UNKNOWN",
    "category",
    "help_questions_from_rows",
    "help_timing",
    "unassisted_success",
]
