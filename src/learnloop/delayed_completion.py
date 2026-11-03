"""One versioned delayed-completion definition (data capture A4).

Router outcomes and adaptive difficulty's dose outcomes both ask one question of
a presentation: was this a genuine delayed attempt at the objective, and did the
learner complete it on their own? This module is that one answer, so warm
performance can never carry a cold label on either side:

* **The delay runs since the last exposure or practice**, never since an offer: an
  attempt, a reveal, a tutor question or a reading on the objective before the
  presentation (a caller may also name ``not_before``, the decision the outcome
  follows, as the intention-to-treat rule does). The threshold is the outcome
  contract's own :data:`~learnloop.outcome_contract.RETENTION_MIN_DELAY_SECONDS`;
  no number is added here. An unobserved delay never qualifies.
* **Requested help on a genuinely delayed, unexposed presentation is a failure of
  unassisted completion**, as adaptive difficulty already defines it (§8.3: "any
  help, or a reveal during the presentation, makes it 0"). Its value is 0: the
  learner could not finish on their own, whatever the assisted answer scored.
* **A pre-exposed presentation stays separate** (the answer was seen before the
  item was served): it measures nothing, neither success nor failure.
* **Abandonment stays separate** (presented, never answered): unobserved, never a
  failure.

Only the outcome readers read this: no certification, mastery, grading, FSRS or
projection change. A changed rule is a new :data:`DELAYED_COMPLETION_VERSION`.

A leaf: the outcome contract and the standard library only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import parse_utc
from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS, retention_exclusions

DELAYED_COMPLETION_VERSION = "delayed_completion_v1"
#: The one threshold: the outcome contract's, reused, never a second number.
MIN_DELAY_SECONDS = RETENTION_MIN_DELAY_SECONDS

COMPLETED = "completed"
FAILED_WITH_HELP = "failed_with_help"
PRE_EXPOSED = "pre_exposed"
ABANDONED = "abandoned"
NOT_DELAYED = "not_delayed"
EXCLUDED = "excluded"
#: The two statuses that are an outcome of delayed completion.
OUTCOME_STATUSES: frozenset[str] = frozenset({COMPLETED, FAILED_WITH_HELP})

#: A tutor question that reads as help during an attempt (adaptive difficulty's rule, §5.3).
HELP_TYPES: frozenset[str] = frozenset({"prerequisite", "mechanism", "clarification", "strategy"})
#: What the outcome contract calls requested help or exposure, decided here rather than excluded.
_HELP_REASONS = frozenset({"hinted", "primed"})
#: The contract's own delay reasons, decided here from the presentation's own times.
_DELAY_REASONS = frozenset({"insufficient_delay", "intervening_practice"})
#: The attempt type of an answer given with hints: a presentation like any other.
HINTED_ATTEMPT_TYPE = "hinted_attempt"


@dataclass(frozen=True)
class Presentation:
    """What one presentation was, from frozen facts only.

    ``presented_at``: when it was served. ``last_exposure_at``: the newest exposure
    or practice on the objective strictly before that (a reveal during the
    presentation is help, not a prior exposure). ``not_before``: the decision an
    intention-to-treat outcome follows. ``help_requested``: a hint, a help-equivalent
    question or a reveal during this presentation. ``pre_exposed``: the answer was
    exposed before it was served. ``answered``: False for an abandoned presentation.
    ``exclusions``: the contract's other reasons (held, unresolved, unscorable, ...).
    """

    presented_at: str
    last_exposure_at: str | None
    correctness: float | None = None
    answered: bool = True
    help_requested: bool = False
    pre_exposed: bool = False
    not_before: str | None = None
    exclusions: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Completion:
    status: str
    value: float | None
    delay_seconds: int | None
    reasons: tuple[str, ...] = ()
    version: str = DELAYED_COMPLETION_VERSION

    @property
    def is_outcome(self) -> bool:
        return self.status in OUTCOME_STATUSES


def _seconds(later: str, earlier: str) -> int | None:
    late, early = parse_utc(later), parse_utc(earlier)
    if late is None or early is None:
        return None
    return int((late - early).total_seconds())


def delay_seconds(presentation: Presentation) -> int | None:
    """Seconds since the last exposure or practice (and since ``not_before`` when named), or None."""

    references = [value for value in (presentation.last_exposure_at, presentation.not_before) if value]
    if not references:
        return None
    gaps = [gap for gap in (_seconds(presentation.presented_at, value) for value in references) if gap is not None]
    return min(gaps) if len(gaps) == len(references) else None


def classify(presentation: Presentation) -> Completion:
    """THE definition (module docstring)."""

    delay = delay_seconds(presentation)
    if not presentation.answered:
        return Completion(ABANDONED, None, delay)
    if presentation.pre_exposed:
        return Completion(PRE_EXPOSED, None, delay)
    if delay is None or delay < MIN_DELAY_SECONDS:
        return Completion(NOT_DELAYED, None, delay, ("insufficient_delay",))
    if presentation.exclusions:
        return Completion(EXCLUDED, None, delay, tuple(presentation.exclusions))
    if presentation.help_requested:
        return Completion(FAILED_WITH_HELP, 0.0, delay)
    if presentation.correctness is None:
        return Completion(EXCLUDED, None, delay, ("outcome_unscorable",))
    return Completion(COMPLETED, float(presentation.correctness), delay)


def other_exclusions(row: Mapping[str, Any]) -> tuple[str, ...]:
    """The outcome contract's reasons for ``row`` (its ``retention_exclusions`` keys) other than
    help and delay, which :func:`classify` decides itself. An unscorable answer given with help is
    still help: its score is not read, so the label's absence excludes nothing there."""

    reasons = [reason for reason in retention_exclusions(row) if reason not in _HELP_REASONS | _DELAY_REASONS]
    if reasons == ["outcome_unscorable"] and row.get("outcome_hints_used"):
        return ()
    return tuple(reasons)


def help_question(row: Mapping[str, Any]) -> bool:
    """Whether a question event reads as requested help during its attempt (AD's §5.3 rule)."""

    if row.get("context") != "practice":
        return False
    return bool(row.get("hint_equivalent")) or row.get("question_type") in HELP_TYPES


def last_before(times: Iterable[str], moment: str) -> str | None:
    """The newest of ``times`` strictly before ``moment``."""

    return max((value for value in times if value < moment), default=None)


__all__ = [
    "ABANDONED",
    "COMPLETED",
    "Completion",
    "DELAYED_COMPLETION_VERSION",
    "EXCLUDED",
    "FAILED_WITH_HELP",
    "HELP_TYPES",
    "HINTED_ATTEMPT_TYPE",
    "MIN_DELAY_SECONDS",
    "NOT_DELAYED",
    "OUTCOME_STATUSES",
    "PRE_EXPOSED",
    "Presentation",
    "classify",
    "delay_seconds",
    "help_question",
    "last_before",
    "other_exclusions",
]
