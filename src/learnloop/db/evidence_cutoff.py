"""Evidence cutoffs: which evidence a read admits, as of when, and which corrections it applies.

A fact has two times, when it happened and when LearnLoop knew it (an imported exam, a late grade), and a
correction axis apart from both: what LearnLoop now says the fact was. Every reader of learner evidence already
picks a rule for the three, each its own way (inclusive or exclusive boundaries, a stored string or a parsed
instant, ties ordered by id or not, corrections as they stand now or as they stood). :class:`Cutoff` names that
rule as a value: its preset, its admission and correction policies, its anchor and the times it was built from,
every boundary with its comparison and what a missing or unreadable time does, and the fields a read could not
reconstruct historically. It serializes to canonical JSON and back, so a prediction snapshot can store the rule
it was made under.

The presets reproduce the readers that exist; none chooses a new rule:

- :meth:`Cutoff.current`: everything, corrections now.
- :meth:`Cutoff.corrected_before`: events before an attempt in ``(created_at, id)`` text order, corrections now
  (the planted-history store's rule).
- :meth:`Cutoff.as_known_at`: events known by an anchor, corrections as they stood then; a field the inventory
  (:data:`MUTABLE_FIELDS`) cannot reconstruct is listed in ``approximate``, never shown as current. No reader
  applies historical corrections yet: the value exists so a read that cannot honour it can say so.
- :meth:`Cutoff.closure_through` and :meth:`Cutoff.closure_at`: the router objective's closure, exclusive at the
  next local midnight or inclusive at a stamp, both times of an answer tested, grades and holds now.
- :meth:`Cutoff.history_v1`: the diagnoser's history, a hybrid of an attempt order, a known-time gate and a
  written-before rule for records, corrections now except a causal hypothesis's version.
- :meth:`Cutoff.ad_replay`: adaptive difficulty's replay, inclusive on occurrence time in days.
- :meth:`Cutoff.completed_by`: the learner field's attempt rows, inclusive on the stored completion text.

The comparison kernels below are the readers' own expressions, moved here so the reader and its preset share
one copy. A kernel that looks simplifiable (a text comparison that could parse, a strict test that could be
inclusive) is kept as it is: each reproduces a stored result, and changing one is a change of persisted meaning
under ``docs/algorithm-change-playbook.md``.

A cutoff never goes into an existing cache key, seed, hash or prompt: :meth:`Cutoff.identity_scalar` gives the
scalar each reader keyed by before this type existed.

Dependency-light by design: the standard library and :mod:`learnloop.clock` only, so attempts, diagnosis, the
router, adaptive difficulty and the field can all import it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import json
import math
from typing import Any, Mapping

from learnloop.clock import parse_utc

SCHEMA = "evidence_cutoff/1"

# -- presets -------------------------------------------------------------------------------------------------

CURRENT = "current"
CORRECTED_BEFORE = "corrected_before"
AS_KNOWN_AT = "as_known_at"
CLOSURE = "closure"
HISTORY_V1 = "history_v1"
AD_REPLAY = "ad_replay"
COMPLETED_BY = "completed_by"
PRESETS = (CURRENT, CORRECTED_BEFORE, AS_KNOWN_AT, CLOSURE, HISTORY_V1, AD_REPLAY, COMPLETED_BY)

# -- admission and correction policies -------------------------------------------------------------------------

ADMIT_ALL = "all"
ADMIT_OCCURRED_BEFORE = "occurred_before"
ADMIT_KNOWN_BY = "known_by"
#: Closure: an event's occurrence time and, for an answer, its received time are both by the limit.
ADMIT_OCCURRED_AND_RECEIVED_BY = "occurred_and_received_by"
#: The diagnoser's history: attempts by order and known time, records by when they were written.
ADMIT_HISTORY_V1 = "history_v1"
ADMIT_OCCURRED_BY = "occurred_by"
ADMISSIONS = (ADMIT_ALL, ADMIT_OCCURRED_BEFORE, ADMIT_KNOWN_BY, ADMIT_OCCURRED_AND_RECEIVED_BY, ADMIT_HISTORY_V1,
              ADMIT_OCCURRED_BY)

CORRECTIONS_NOW = "now"
CORRECTIONS_THEN = "then"
CORRECTIONS = (CORRECTIONS_NOW, CORRECTIONS_THEN)

ANCHOR_NONE = "none"
ANCHOR_ATTEMPT = "attempt"
ANCHOR_MOMENT = "moment"
ANCHOR_LOCAL_DATE = "local_date"
ANCHORS = (ANCHOR_NONE, ANCHOR_ATTEMPT, ANCHOR_MOMENT, ANCHOR_LOCAL_DATE)

# -- boundaries ----------------------------------------------------------------------------------------------

#: Parsed to an aware UTC instant (``clock.parse_utc``).
COMPARE_INSTANT = "instant"
#: The stored text compared as text (lexicographic; equal to instant order only for one canonical format).
COMPARE_TEXT = "text"
#: The ``(time text, id)`` pair compared as text: ties within one time break by id.
COMPARE_TEXT_KEY = "text_key"
#: A parsed instant as float days since the epoch (adaptive difficulty's ``replay.days``).
COMPARE_DAYS = "days"
COMPARISONS = (COMPARE_INSTANT, COMPARE_TEXT, COMPARE_TEXT_KEY, COMPARE_DAYS)

#: What a missing or unreadable time does at a boundary.
TIME_EXCLUDED = "excluded"
TIME_ADMITTED = "admitted"
TIME_RAISES = "raises"
TIME_IGNORED = "ignored"
TIME_RULES = (TIME_EXCLUDED, TIME_ADMITTED, TIME_RAISES, TIME_IGNORED)

#: The availability time a known-time boundary reads (``db.attempt_availability``).
AVAILABILITY_CREATED = "created_at"
#: ``received_at`` when set and non-empty, else ``created_at`` (the loaded-row form, ``known_at``).
AVAILABILITY_RECEIVED_OR_CREATED = "received_or_created"
#: Both times tested separately (closure).
AVAILABILITY_BOTH = "occurred_and_received"
AVAILABILITY_NONE = "none"
AVAILABILITIES = (AVAILABILITY_CREATED, AVAILABILITY_RECEIVED_OR_CREATED, AVAILABILITY_BOTH, AVAILABILITY_NONE)


@dataclass(frozen=True)
class Boundary:
    """One test a read applies: ``<subject>.<time> <op> <anchor time>`` under ``comparison``.

    ``subject`` names the rows it applies to (``attempts``, ``records``, ``events``...), ``op`` is ``<`` or
    ``<=``, ``missing`` and ``malformed`` say what a row without a time, or with one that does not parse, does.
    """

    subject: str
    time: str
    op: str
    anchor: str
    comparison: str
    missing: str
    malformed: str

    def to_dict(self) -> dict[str, str]:
        return {"subject": self.subject, "time": self.time, "op": self.op, "anchor": self.anchor,
                "comparison": self.comparison, "missing": self.missing, "malformed": self.malformed}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Boundary":
        value = cls(**{name: str(raw[name]) for name in ("subject", "time", "op", "anchor", "comparison", "missing",
                                                          "malformed")})
        if value.op not in ("<", "<=") or value.comparison not in COMPARISONS:
            raise ValueError(f"not a boundary: {dict(raw)!r}")
        if value.missing not in TIME_RULES or value.malformed not in TIME_RULES:
            raise ValueError(f"not a boundary: {dict(raw)!r}")
        return value

    @property
    def inclusive(self) -> bool:
        return self.op == "<="


@dataclass(frozen=True)
class FieldApproximation:
    """A field a read showed although it could not reconstruct its value at the cutoff."""

    field: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "status": self.status, "reason": self.reason}


# -- the mutable-field inventory ---------------------------------------------------------------------------------

#: Historical reconstruction of a field: exact from its own rows, by a timestamp on the row, from another table's
#: rows where they exist (``partial``), or not at all.
RECOVERABLE_EXACT = "exact"
RECOVERABLE_BY_TIMESTAMP = "by_timestamp"
RECOVERABLE_PARTIAL = "partial"
RECOVERABLE_NONE = "none"
RECOVERABILITY = (RECOVERABLE_EXACT, RECOVERABLE_BY_TIMESTAMP, RECOVERABLE_PARTIAL, RECOVERABLE_NONE)


@dataclass(frozen=True)
class MutableField:
    """One column (or derived value) the evidence reads change in place, and whether its past is recoverable."""

    table: str
    column: str
    recoverable: str
    how: str
    writer: str

    @property
    def name(self) -> str:
        return f"{self.table}.{self.column}"


def _fields(table: str, columns: str, recoverable: str, how: str, writer: str) -> tuple[MutableField, ...]:
    return tuple(MutableField(table, column, recoverable, how, writer) for column in columns.split())


#: What the evidence reads overwrite, and whether its past can be read back (EP spec §7.1's inventory, re-located
#: at this tip and extended with the help ledger's set-once updates). A table named in parentheses is derived or
#: applied at read time, not a stored row. ``as_known_at`` lists every field below ``exact``/``by_timestamp`` that a
#: read asks for as approximate.
MUTABLE_FIELDS: tuple[MutableField, ...] = (
    *_fields("grading_evidence", "superseded_at superseded_by_evidence_id", RECOVERABLE_BY_TIMESTAMP,
             "a superseded row keeps its superseded_at: the epoch in force at a time is the rows not yet superseded",
             "db/stores/attempts.py::supersede_grading_evidence; db/repositories.py"),
    *_fields("practice_attempts", "rubric_score correctness confidence", RECOVERABLE_PARTIAL,
             "rewritten at a regrade; recoverable from grading_evidence where criterion rows exist, otherwise not",
             "db/stores/attempts.py (regrade); db/repositories.py"),
    *_fields("(held_for_review)", "held", RECOVERABLE_PARTIAL,
             "derived from blind records and current evidence (held_grades.held_for_review_attempts): by their "
             "timestamps, except the review reason replay writes",
             "held_grades.py::held_for_review_attempts"),
    *_fields("misconceptions", "status", RECOVERABLE_EXACT,
             "misconception_transition_events holds the creation and every transition (since migration 056)",
             "db/stores/learner_model.py"),
    *_fields("misconceptions", "statement facet_ids_json severity source_error_event_ids_json", RECOVERABLE_NONE,
             "overwritten in place; no version kept", "db/stores/learner_model.py"),
    *_fields("misconception_candidates",
             "status occurrence_count source_error_event_ids_json statement statement_normalized", RECOVERABLE_NONE,
             "overwritten in place; no history", "db/repositories.py; db/stores/learner_model.py"),
    *_fields("unresolved_cause_factors", "status", RECOVERABLE_PARTIAL,
             "no history; a resolution's observation ids date it, otherwise not", "db/stores/causal.py"),
    *_fields("unresolved_cause_factors", "candidate_causes_json", RECOVERABLE_NONE,
             "overwritten in place; no history", "db/stores/causal.py"),
    *_fields("probe_presentations", "status submitted_at ended_at", RECOVERABLE_BY_TIMESTAMP,
             "each status change stamps served_at, submitted_at or ended_at", "db/stores/probes.py"),
    *_fields("probe_episodes", "status completed_at", RECOVERABLE_BY_TIMESTAMP,
             "completion is dated by completed_at", "db/stores/probes.py"),
    *_fields("probe_episodes", "completion_posterior_json completion_detail_json", RECOVERABLE_NONE,
             "written once at completion, the posterior before it not kept", "db/stores/probes.py"),
    *_fields("remediation_episodes", "state primed_attempt_id cold_attempt_id", RECOVERABLE_NONE,
             "overwritten in place", "db/stores/remediation.py"),
    *_fields("error_events", "status misconception_id", RECOVERABLE_NONE,
             "overwritten in place", "db/stores/learner_model.py"),
    *_fields("learner_claims", "superseded_by", RECOVERABLE_BY_TIMESTAMP,
             "dated by the superseding claim's created_at", "db/repositories.py; db/stores/questions.py"),
    *_fields("learner_claims", "applied_after_attempts", RECOVERABLE_NONE,
             "a running count", "db/repositories.py; db/stores/questions.py"),
    *_fields("followup_tasks", "consumed_attempt_id", RECOVERABLE_PARTIAL,
             "dated by the consuming attempt's created_at", "db/repositories.py; db/stores/remediation.py"),
    *_fields("followup_tasks", "status not_before", RECOVERABLE_NONE,
             "overwritten in place", "db/repositories.py; db/stores/remediation.py"),
    *_fields("fitted_parameters", "active deactivated_at", RECOVERABLE_BY_TIMESTAMP,
             "each fit inserts a row; history rows are kept with deactivated_at", "db/stores/practice_state.py"),
    *_fields("help_assists", "shown shown_at", RECOVERABLE_BY_TIMESTAMP,
             "set once, with shown_at (mark_shown)", "db/stores/help_assists.py::mark_shown"),
    *_fields("help_assists", "attempt_id", RECOVERABLE_PARTIAL,
             "the attachment writes no time of its own: the attached attempt's created_at bounds it, a later "
             "repair attach does not", "db/stores/help_assists.py::attach_submission"),
    *_fields("help_assists", "submitted_at submit_latency_seconds", RECOVERABLE_PARTIAL,
             "set once; an attach may fill a submit time it did not observe", "db/stores/help_assists.py"),
    *_fields("help_assists", "practice_session_id", RECOVERABLE_NONE,
             "a workbench row's session is filled later without a time", "db/stores/help_assists.py"),
    *_fields("(protection)", "material_view", RECOVERABLE_NONE,
             "exam reservations and held-out spans are applied as of now by the material view",
             "adaptive_difficulty/material_view.py"),
)

_INVENTORY = {entry.name: entry for entry in MUTABLE_FIELDS}


def recoverability(field_name: str) -> MutableField | None:
    """The inventory's entry for ``table.column``, or None for a field the evidence reads never overwrite."""

    return _INVENTORY.get(field_name)


def approximate_fields(field_names: tuple[str, ...] | list[str]) -> tuple[FieldApproximation, ...]:
    """The fields of ``field_names`` a read as of then cannot reconstruct exactly, sorted by name. A field
    missing from the inventory is not overwritten in place, so it is exact."""

    out = []
    for name in sorted(set(field_names)):
        entry = _INVENTORY.get(name)
        if entry is not None and entry.recoverable not in (RECOVERABLE_EXACT, RECOVERABLE_BY_TIMESTAMP):
            out.append(FieldApproximation(name, entry.recoverable, entry.how))
    return tuple(out)


# -- the comparison kernels (each reader's own expression) -------------------------------------------------------


def closure_through_limit(local_date: str) -> tuple[datetime, bool]:
    """``(limit, inclusive)`` for the end of ``local_date`` in the machine's local time: the next local midnight,
    exclusive; a date with no next day (``9999-12-31``) admits every event, inclusive at the largest instant."""

    try:
        following = date.fromisoformat(local_date) + timedelta(days=1)
        return datetime(following.year, following.month, following.day).astimezone().astimezone(UTC), False
    except (OverflowError, ValueError):  # the far future (``9999-12-31``): every event
        return datetime.max.replace(tzinfo=UTC), True


def closure_at_limit(stamp: str) -> datetime:
    """The instant ``stamp`` names (a window's ``window_closes_at``): events at or before it."""

    moment = parse_utc(str(stamp))
    assert moment is not None
    return moment


def closure_admits(limit: datetime, inclusive: bool, occurred: Any, received: Any = None) -> bool:
    """Whether an event that happened at ``occurred`` (and, for an answer, became known at ``received``, None
    where the two are one) is in the read: both at or before the closure. An event with no time is not; an
    unreadable time raises."""

    if not occurred:
        return False
    for stamp in (occurred, received):
        if not stamp:
            continue
        moment = parse_utc(str(stamp))
        if moment is None or moment > limit or (moment == limit and not inclusive):
            return False
    return True


def history_v1_written_before(written: datetime | None, cutoff: datetime | None) -> bool:
    """A record written strictly before the cutoff instant. An unknown or unparseable time is never "before":
    the history fails closed rather than leak a record that may postdate the cutoff."""

    return written is not None and cutoff is not None and written < cutoff


def history_v1_known_by(known: datetime | None, cutoff: datetime | None) -> bool:
    """True unless the attempt became known after the cutoff (always True where no known time was read)."""

    return known is None or cutoff is None or known <= cutoff


def ad_replay_excludes(at: float, limit: float) -> bool:
    """An event at ``at`` days is after the replay's ``limit`` days (``math.inf`` with no ``as_of``)."""

    return at > limit


def completed_by_excludes(created_at: Any, as_of: Any) -> bool:
    """An attempt whose stored ``created_at`` text sorts after ``as_of``: the field's completion cutoff, a text
    comparison (a ``None`` time raises, an empty one is admitted)."""

    return created_at > as_of


def _instant_or_none(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_utc(str(value))
    except (TypeError, ValueError):
        return None


def _days(value: Any) -> float:
    parsed = parse_utc(str(value)) if value else None
    if parsed is None:
        raise ValueError(f"unreadable time {value!r}")
    return parsed.timestamp() / 86400.0


# -- the value ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Cutoff:
    """Which evidence a read admits, as of when, and which corrections it applies (module docstring)."""

    preset: str
    admission: str
    corrections: str
    anchor_kind: str = ANCHOR_NONE
    anchor_id: str | None = None
    #: The instants the cutoff was built from, by name, as text (``limit``, ``completed_at``, ``known_at``...).
    times: tuple[tuple[str, str], ...] = ()
    boundaries: tuple[Boundary, ...] = ()
    #: The order rows are read in when two share a time (``(created_at, id)``), or None where the read keeps none.
    tie_order: str | None = None
    availability: str = AVAILABILITY_NONE
    #: Fields a ``now`` policy still reads as of then (the diagnoser's causal hypothesis versions).
    corrections_then: tuple[str, ...] = ()
    approximate: tuple[FieldApproximation, ...] = ()
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        if self.preset not in PRESETS:
            raise ValueError(f"unknown cutoff preset {self.preset!r}")
        if self.admission not in ADMISSIONS or self.corrections not in CORRECTIONS:
            raise ValueError(f"unknown policy {self.admission!r}/{self.corrections!r}")
        if self.anchor_kind not in ANCHORS or self.availability not in AVAILABILITIES:
            raise ValueError(f"unknown anchor or availability {self.anchor_kind!r}/{self.availability!r}")
        if self.schema != SCHEMA:
            raise ValueError(f"unsupported cutoff schema {self.schema!r}")
        # Times are a mapping: held sorted so a cutoff read back from canonical JSON equals the one written.
        object.__setattr__(self, "times", tuple(sorted((str(name), str(value)) for name, value in self.times)))

    # -- presets ---------------------------------------------------------------------------------------------

    @classmethod
    def current(cls) -> "Cutoff":
        """Everything LearnLoop holds, every correction as it stands now."""

        return cls(CURRENT, ADMIT_ALL, CORRECTIONS_NOW)

    @classmethod
    def corrected_before(cls, attempt_id: str, occurred_at: str) -> "Cutoff":
        """Events before an attempt in ``(created_at, id)`` text order (two in one second order by id), every
        correction as it stands now: a regrade reaches the read. The planted-history store's rule."""

        return cls(
            CORRECTED_BEFORE, ADMIT_OCCURRED_BEFORE, CORRECTIONS_NOW, ANCHOR_ATTEMPT, str(attempt_id),
            (("occurred_at", str(occurred_at)),),
            (Boundary("attempts", "(created_at, id)", "<", "(occurred_at, anchor_id)", COMPARE_TEXT_KEY,
                      TIME_ADMITTED, TIME_ADMITTED),
             Boundary("records", "source attempt (created_at, id)", "<", "(occurred_at, anchor_id)",
                      COMPARE_TEXT_KEY, TIME_EXCLUDED, TIME_EXCLUDED)),
            "(created_at, id)", AVAILABILITY_CREATED)

    @classmethod
    def as_known_at(cls, known_at: str, *, attempt_id: str | None = None,
                    fields: tuple[str, ...] | list[str] = ()) -> "Cutoff":
        """Events known by ``known_at`` (an attempt's known time, or a moment), corrections as they stood then.
        Each of ``fields`` the inventory cannot reconstruct is listed in ``approximate``."""

        return cls(
            AS_KNOWN_AT, ADMIT_KNOWN_BY, CORRECTIONS_THEN,
            ANCHOR_ATTEMPT if attempt_id is not None else ANCHOR_MOMENT,
            str(attempt_id) if attempt_id is not None else str(known_at),
            (("known_at", str(known_at)),),
            (Boundary("events", "received_or_created", "<=", "known_at", COMPARE_INSTANT, TIME_EXCLUDED,
                      TIME_EXCLUDED),),
            "(created_at, id)", AVAILABILITY_RECEIVED_OR_CREATED,
            approximate=approximate_fields(tuple(fields)))

    @classmethod
    def closure_through(cls, local_date: str) -> "Cutoff":
        """The end of a local date: events before the next local midnight (the instant is computed in the
        machine's local time when the cutoff is made and stored, so it does not move with a later time zone)."""

        limit, inclusive = closure_through_limit(local_date)
        return cls._closure(ANCHOR_LOCAL_DATE, str(local_date), limit, inclusive)

    @classmethod
    def closure_at(cls, stamp: str) -> "Cutoff":
        """A stamp itself (a window's closing moment): events at or before it."""

        return cls._closure(ANCHOR_MOMENT, str(stamp), closure_at_limit(stamp), True)

    @classmethod
    def _closure(cls, anchor_kind: str, anchor_id: str, limit: datetime, inclusive: bool) -> "Cutoff":
        op = "<=" if inclusive else "<"
        return cls(
            CLOSURE, ADMIT_OCCURRED_AND_RECEIVED_BY, CORRECTIONS_NOW, anchor_kind, anchor_id,
            (("limit", limit.isoformat()),),
            (Boundary("events", "occurred_at", op, "limit", COMPARE_INSTANT, TIME_EXCLUDED, TIME_RAISES),
             Boundary("answers", "received_at", op, "limit", COMPARE_INSTANT, TIME_IGNORED, TIME_RAISES)),
            None, AVAILABILITY_BOTH)

    @classmethod
    def history_v1(cls, attempt_id: str, completed_at: str, *, known_at: str | None = None,
                   available_at_reads: bool = False) -> "Cutoff":
        """The diagnoser's history as it is read today (``diagnosis.split.history.VaultHistoryStore``).

        Attempts: ``(created_at, id)`` text order strictly before the target's, and, with ``[router_objective]
        available_at_reads`` on, known (a non-empty ``received_at``) by the target's known time, inclusive
        (``known_at``, else its ``completed_at``). Records (hypotheses, registry rows, cold verifications): written
        strictly before the target's ``completed_at`` instant. Learner marks: ``created_at`` text strictly before
        the target's ``completed_at`` text. Corrections now, except a causal hypothesis's version: its latest
        written before the cutoff."""

        times = [("completed_at", str(completed_at))]
        if known_at:
            times.append(("known_at", str(known_at)))
        known = (Boundary("attempts", "received_at", "<=", "known_at or completed_at", COMPARE_INSTANT,
                          TIME_ADMITTED, TIME_ADMITTED),) if available_at_reads else ()
        return cls(
            HISTORY_V1, ADMIT_HISTORY_V1, CORRECTIONS_NOW, ANCHOR_ATTEMPT, str(attempt_id), tuple(sorted(times)),
            (Boundary("attempts", "(created_at, id)", "<", "(completed_at, anchor_id)", COMPARE_TEXT_KEY,
                      TIME_ADMITTED, TIME_ADMITTED),
             *known,
             Boundary("records", "written_at", "<", "completed_at", COMPARE_INSTANT, TIME_EXCLUDED, TIME_EXCLUDED),
             Boundary("learner_marks", "created_at", "<", "completed_at", COMPARE_TEXT, TIME_ADMITTED,
                      TIME_ADMITTED)),
            "(created_at, id)",
            AVAILABILITY_RECEIVED_OR_CREATED if available_at_reads else AVAILABILITY_CREATED,
            corrections_then=("causal_hypotheses.version",))

    @classmethod
    def ad_replay(cls, as_of: str | None) -> "Cutoff":
        """Adaptive difficulty's replay (``replay.load_events``): attempts, reading opportunities and claims at or
        before ``as_of`` in float days of their parsed time (an unreadable time is skipped; no ``as_of`` admits
        every readable one); grades, holds, claims' supersession and protection as they stand now."""

        times = (("as_of", str(as_of)),) if as_of else ()
        boundaries = tuple(
            Boundary(subject, time, "<=", "as_of", COMPARE_DAYS, TIME_EXCLUDED, TIME_EXCLUDED)
            for subject, time in (("attempts", "created_at"), ("reading_opportunities", "source_written_at"),
                                  ("claims", "created_at")))
        return cls(AD_REPLAY, ADMIT_OCCURRED_BY, CORRECTIONS_NOW, ANCHOR_MOMENT if as_of else ANCHOR_NONE,
                   str(as_of) if as_of else None, times, boundaries, "(created_at, id)", AVAILABILITY_CREATED)

    @classmethod
    def completed_by(cls, as_of: str | None) -> "Cutoff":
        """The learner field's attempt rows (``field.outcomes.load_attempt_rows``): ``created_at`` text at or
        before ``as_of`` text (a ``None`` time raises, an empty one is admitted; no ``as_of`` admits all); the
        latest surviving grading epoch and the field's revision policy now, not a point-in-time reconstruction."""

        times = (("as_of", str(as_of)),) if as_of is not None else ()
        return cls(COMPLETED_BY, ADMIT_OCCURRED_BY, CORRECTIONS_NOW,
                   ANCHOR_MOMENT if as_of is not None else ANCHOR_NONE, str(as_of) if as_of is not None else None,
                   times,
                   (Boundary("attempts", "created_at", "<=", "as_of", COMPARE_TEXT, TIME_RAISES, TIME_ADMITTED),),
                   "(created_at, id)", AVAILABILITY_CREATED)

    # -- reading it ------------------------------------------------------------------------------------------

    def time(self, name: str) -> str | None:
        return dict(self.times).get(name)

    @property
    def is_approximate(self) -> bool:
        return bool(self.approximate)

    def identity_scalar(self) -> str | None:
        """The scalar each reader keyed its caches and identities by before this type existed (an ``as_of``,
        a closure's date or stamp, an attempt id; None for the current read). A cutoff never enters an existing
        key itself: its serialization is new bytes."""

        if self.preset in (AD_REPLAY, COMPLETED_BY):
            return self.time("as_of") if self.anchor_kind != ANCHOR_NONE else None
        return self.anchor_id

    def admits(self, occurred: Any, received: Any = None, *, attempt_id: str | None = None) -> bool:
        """Whether an attempt (or event) that happened at ``occurred``, known at ``received`` (None where the two
        are one), with id ``attempt_id`` (for a tie), is admitted, by exactly the rule of the preset's reader."""

        if self.preset == CURRENT:
            return True
        if self.preset == CORRECTED_BEFORE:
            return (str(occurred), str(attempt_id or "")) < (str(self.time("occurred_at")), str(self.anchor_id))
        if self.preset == AS_KNOWN_AT:
            # The loaded-row availability time (``attempt_availability.available_at``); unreadable fails closed.
            known = _instant_or_none(received if received else occurred)
            anchor = _instant_or_none(self.time("known_at"))
            return known is not None and anchor is not None and known <= anchor
        if self.preset == CLOSURE:
            limit = parse_utc(str(self.time("limit")))
            assert limit is not None
            return closure_admits(limit, self.boundaries[0].inclusive, occurred, received)
        if self.preset == HISTORY_V1:
            key = (str(occurred), str(attempt_id or ""))
            target = (str(self.time("completed_at")), str(self.anchor_id))
            if not key < target:
                return False
            if self.availability != AVAILABILITY_RECEIVED_OR_CREATED or not received:
                return True
            return history_v1_known_by(_instant_or_none(received), self.history_known_cutoff())
        if self.preset == AD_REPLAY:
            try:
                at = _days(occurred)
            except ValueError:
                return False
            limit = _days(self.time("as_of")) if self.time("as_of") else math.inf
            return not ad_replay_excludes(at, limit)
        if self.preset == COMPLETED_BY:
            as_of = self.time("as_of")
            return as_of is None or not completed_by_excludes(occurred, as_of)
        raise AssertionError(self.preset)

    def history_known_cutoff(self) -> datetime | None:
        """``history_v1``: when the decision at the target was made, its known time, else its completion."""

        self._require(HISTORY_V1)
        return _instant_or_none(self.time("known_at")) or _instant_or_none(self.time("completed_at"))

    def written_before(self, written: Any) -> bool:
        """``history_v1``: a record written strictly before the target's completion instant."""

        self._require(HISTORY_V1)
        moment = written if isinstance(written, datetime) else _instant_or_none(written)
        return history_v1_written_before(moment, _instant_or_none(self.time("completed_at")))

    def mark_before(self, created_at: Any) -> bool:
        """``history_v1``: a learner mark whose ``created_at`` text sorts strictly before the target's."""

        self._require(HISTORY_V1)
        return str(created_at or "") < str(self.time("completed_at"))

    def _require(self, preset: str) -> None:
        if self.preset != preset:
            raise ValueError(f"a {self.preset} cutoff has no {preset} rule")

    # -- serialization ---------------------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "preset": self.preset,
            "admission": self.admission,
            "corrections": self.corrections,
            "corrections_then": list(self.corrections_then),
            "anchor": {"kind": self.anchor_kind, "id": self.anchor_id},
            "times": {name: value for name, value in self.times},
            "boundaries": [boundary.to_dict() for boundary in self.boundaries],
            "tie_order": self.tie_order,
            "availability": self.availability,
            "approximate": [entry.to_dict() for entry in self.approximate],
        }

    def to_json(self) -> str:
        """Canonical JSON: sorted keys, compact separators, UTF-8 text kept as is."""

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Cutoff":
        if raw.get("schema") != SCHEMA:
            raise ValueError(f"unsupported cutoff schema {raw.get('schema')!r}")
        anchor = raw.get("anchor") or {}
        return cls(
            preset=str(raw["preset"]),
            admission=str(raw["admission"]),
            corrections=str(raw["corrections"]),
            anchor_kind=str(anchor.get("kind", ANCHOR_NONE)),
            anchor_id=None if anchor.get("id") is None else str(anchor["id"]),
            times=tuple((str(name), str(value)) for name, value in (raw.get("times") or {}).items()),
            boundaries=tuple(Boundary.from_dict(entry) for entry in raw.get("boundaries") or ()),
            tie_order=None if raw.get("tie_order") is None else str(raw["tie_order"]),
            availability=str(raw.get("availability", AVAILABILITY_NONE)),
            corrections_then=tuple(str(value) for value in raw.get("corrections_then") or ()),
            approximate=tuple(FieldApproximation(str(entry["field"]), str(entry["status"]), str(entry["reason"]))
                              for entry in raw.get("approximate") or ()),
            schema=str(raw["schema"]),
        )

    @classmethod
    def from_json(cls, text: str) -> "Cutoff":
        return cls.from_dict(json.loads(text))


__all__ = [
    "AD_REPLAY", "AS_KNOWN_AT", "Boundary", "CLOSURE", "COMPLETED_BY", "CORRECTED_BEFORE", "CURRENT", "Cutoff",
    "FieldApproximation", "HISTORY_V1", "MUTABLE_FIELDS", "MutableField", "PRESETS", "SCHEMA", "ad_replay_excludes",
    "approximate_fields", "closure_admits", "closure_at_limit", "closure_through_limit", "completed_by_excludes",
    "history_v1_known_by", "history_v1_written_before", "recoverability",
]
