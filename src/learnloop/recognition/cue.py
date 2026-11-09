"""RE0 §4.2: the cue label, ``attempt_cue_v1(attempt, ledger)``.

Which cues were present when an attempt was made, so a result on "which idea does this problem need?" can be told
apart from one where the block, the stem, a reading or a lesson gave the idea away. A pure function of the attempt and
a :class:`CueLedger` (plain records, read once by :mod:`learnloop.recognition.ledger`): the same ledger gives the same
label, and no table or migration backs it, so it works on every old attempt.

The seven fields (the spec's table):

* ``same_lo_before`` / ``same_concept_before``: the previous practice attempt in the session was on the same learning
  object / concept. The previous attempt is the latest earlier one with the same ``session_id``; an attempt with no
  session reads the router objective's own session rule (less than ``session_gap_minutes`` since the previous attempt,
  itself with no session).
* ``after_reading`` / ``after_lesson``: a Reader exposure or a reveal on the attempt's learning object / a lesson on it
  ended within ``window_hours`` before the attempt began. The attempt began at its time less its latency when it has
  one, so help given during the attempt (a reveal, a tutor answer) is help, not a cue, and a reveal tied to this attempt
  is never counted. The window is the caller's (the report passes the outcome contract's retention minimum, 24 hours, the delay under which
  a read is not a delayed one).
* ``method_stated``: the item's frozen required method (its assessment contract's), so the stem names the method.
* ``followup_of_miss``: the attempt answered a follow-up bound to an earlier miss.
* ``randomized_check``: the attempt answered one of RO5's randomized daily checks, the closest thing to an uncued
  observation, which is why it is listed rather than excluded.

**Uncued** is every field false. A field the records cannot speak to (an old attempt with no pinned contract, an
imported exam answer with no session) is listed in ``unreadable`` and never read as false silently; an imported answer
has no ledger at all, so its label is ``unlabelled``, not ``uncued``.

A leaf: the standard library only. Observational: nothing here estimates an effect, and nothing serving, scoring,
scheduling, replay or adaptive difficulty reads it (spec §4.1; ``tests/test_re0_capture.py``).
"""

from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

CUE_VERSION = "attempt_cue_v1"
FIELDS: tuple[str, ...] = (
    "same_lo_before", "same_concept_before", "after_reading", "after_lesson", "method_stated", "followup_of_miss",
    "randomized_check",
)
UNCUED, CUED, UNLABELLED = "uncued", "cued", "unlabelled"
#: Attempts that are not practice in a session: a self-report, a skip, and imported exam answers (which carry no session
#: and sit on the exam's date, so they are neither a cue nor labelled).
NOT_PRACTICE = frozenset({"self_report", "skip", "exam_evidence"})
IMPORTED = frozenset({"exam_evidence"})
#: ``Exposure.kind``: what the warmth source was.
READING, LESSON = "reading", "lesson"


def parse(stamp: str) -> datetime:
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


@dataclass(frozen=True)
class Exposure:
    """One exposure to a learning object: a Reader exposure or a reveal (``reading``), or a lesson's end (``lesson``).
    ``attempt_id`` names the attempt a reveal was tied to, which it never cues."""

    learning_object_id: str
    at: str
    kind: str = READING
    attempt_id: str | None = None


@dataclass(frozen=True)
class CueLedger:
    """What the label reads, as plain records. ``attempts`` are ``practice_attempts`` rows (id, session_id,
    learning_object_id, concept, created_at, latency_seconds, attempt_type); ``method_stated`` maps an attempt to
    whether its pinned contract froze a required method (None: no pinned contract, so unreadable); ``followups`` and
    ``checks`` are the attempt ids bound to a follow-up and to a randomized check."""

    attempts: Sequence[Mapping[str, object]]
    exposures: Sequence[Exposure] = ()
    method_stated: Mapping[str, bool | None] = field(default_factory=dict)
    followups: frozenset[str] = frozenset()
    checks: frozenset[str] = frozenset()
    window_hours: float = 0.0
    session_gap_minutes: float = 0.0
    _by_session: Mapping[str, tuple[tuple[tuple[datetime, str], Mapping[str, object]], ...]] = field(
        init=False, repr=False, compare=False, default_factory=dict)
    _unsessioned: tuple[tuple[tuple[datetime, str], Mapping[str, object]], ...] = field(
        init=False, repr=False, compare=False, default=())
    _exposed: Mapping[str, tuple[Exposure, ...]] = field(init=False, repr=False, compare=False, default_factory=dict)

    def __post_init__(self) -> None:
        by_session: dict[str, list[tuple[tuple[datetime, str], Mapping[str, object]]]] = defaultdict(list)
        loose: list[tuple[tuple[datetime, str], Mapping[str, object]]] = []
        for row in self.attempts:
            if str(row.get("attempt_type") or "") in NOT_PRACTICE or not row.get("created_at"):
                continue
            keyed = ((parse(str(row["created_at"])), str(row["id"])), row)
            if row.get("session_id"):
                by_session[str(row["session_id"])].append(keyed)
            else:
                loose.append(keyed)
        object.__setattr__(self, "_by_session", {key: tuple(sorted(rows, key=lambda r: r[0]))
                                                 for key, rows in by_session.items()})
        object.__setattr__(self, "_unsessioned", tuple(sorted(loose, key=lambda r: r[0])))
        exposed: dict[str, list[Exposure]] = defaultdict(list)
        for exposure in self.exposures:
            exposed[str(exposure.learning_object_id)].append(exposure)
        object.__setattr__(self, "_exposed", {key: tuple(rows) for key, rows in exposed.items()})

    def previous(self, attempt: Mapping[str, object]) -> Mapping[str, object] | None:
        """The previous practice attempt in the attempt's session, or None."""

        if not attempt.get("created_at"):
            return None
        key = (parse(str(attempt["created_at"])), str(attempt["id"]))
        session = attempt.get("session_id")
        rows = self._by_session.get(str(session), ()) if session else self._unsessioned
        index = bisect_left(rows, key, key=lambda row: row[0])
        if index == 0:
            return None
        (before, _id), found = rows[index - 1]
        if not session and key[0] - before >= timedelta(minutes=float(self.session_gap_minutes)):
            return None
        return found

    def exposures_of(self, learning_object_id: str) -> tuple[Exposure, ...]:
        return self._exposed.get(str(learning_object_id), ())


@dataclass(frozen=True)
class AttemptCue:
    """The label: the seven fields, the fields the records could not speak to, and the cue version."""

    attempt_id: str
    same_lo_before: bool = False
    same_concept_before: bool = False
    after_reading: bool = False
    after_lesson: bool = False
    method_stated: bool = False
    followup_of_miss: bool = False
    randomized_check: bool = False
    unreadable: tuple[str, ...] = ()
    imported: bool = False
    version: str = CUE_VERSION

    @property
    def present(self) -> tuple[str, ...]:
        return tuple(name for name in FIELDS if getattr(self, name))

    @property
    def label(self) -> str:
        if self.imported:
            return UNLABELLED
        return CUED if self.present else UNCUED


def _began(attempt: Mapping[str, object]) -> datetime:
    began = parse(str(attempt["created_at"]))
    latency = attempt.get("latency_seconds")
    return began - timedelta(seconds=float(latency)) if isinstance(latency, (int, float)) and latency > 0 else began


def attempt_cue_v1(attempt: Mapping[str, object], ledger: CueLedger) -> AttemptCue:
    """The cues present on ``attempt`` (module docstring). Pure: the ledger is read, never written."""

    attempt_id = str(attempt["id"])
    if str(attempt.get("attempt_type") or "") in IMPORTED or not attempt.get("created_at"):
        return AttemptCue(attempt_id=attempt_id, imported=True, unreadable=FIELDS)
    unreadable: list[str] = []
    previous = ledger.previous(attempt)
    lo, concept = attempt.get("learning_object_id"), attempt.get("concept")
    same_lo = previous is not None and lo is not None and previous.get("learning_object_id") == lo
    same_concept = previous is not None and concept is not None and previous.get("concept") == concept
    after_reading = after_lesson = False
    if lo is not None:
        began = _began(attempt)
        horizon = began - timedelta(hours=float(ledger.window_hours))
        for exposure in ledger.exposures_of(str(lo)):
            if exposure.attempt_id == attempt_id:
                continue
            try:
                at = parse(exposure.at)
            except (TypeError, ValueError):
                continue
            if horizon <= at <= began:
                after_lesson = after_lesson or exposure.kind == LESSON
                after_reading = after_reading or exposure.kind != LESSON
    method = ledger.method_stated.get(attempt_id)
    if method is None:
        unreadable.append("method_stated")
    return AttemptCue(
        attempt_id=attempt_id, same_lo_before=bool(same_lo), same_concept_before=bool(same_concept),
        after_reading=after_reading, after_lesson=after_lesson, method_stated=bool(method),
        followup_of_miss=attempt_id in ledger.followups, randomized_check=attempt_id in ledger.checks,
        unreadable=tuple(unreadable))


def cues(attempts: Iterable[Mapping[str, object]], ledger: CueLedger) -> dict[str, AttemptCue]:
    """The label of each attempt, by id."""

    return {str(row["id"]): attempt_cue_v1(row, ledger) for row in attempts}
