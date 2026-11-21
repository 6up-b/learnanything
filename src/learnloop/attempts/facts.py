"""Attempt facts: what happened around one answer, each fact with where it came from and how well it was captured.

Readers of an attempt have each worked out for themselves what help preceded it (hints, reveals, tutor questions),
when it was served and answered, and what the learner declared, and then applied their own yes-or-no ("assisted",
"cold", "primed", "eligible"). :class:`AttemptFacts` holds those facts once, as stored, and
:mod:`learnloop.attempts.fact_predicates` holds the yes-or-no questions the readers ask of them, each under its
owner's name.

Two ways in:

- :func:`collect_facts` reads stored attempts through a :class:`FactReader`, the reader carrying the caller's
  visibility (a plain connection, or a filter such as adaptive difficulty's material view, so material withheld from
  that caller stays invisible here as it is there), and an evidence :class:`~learnloop.db.evidence_cutoff.Cutoff`
  saying which attempts it admits and, under historical corrections, which help it may show as known.
- :func:`facts_from_draft` and :func:`submitted_facts` build the submitted part alone, with no database: the
  submission path before an attempt id exists, and the compatibility adapters of readers that hold only an attempt
  row.

**Nothing is inferred backwards.** The submitted count and flags (``hints_used``, ``primed``,
``first_hint_progress``) are kept verbatim, beside the help rows they summarize, never recomputed from them; where the
two disagree both stay and the coverage says so. A source that does not exist in the vault, or a row an older
attempt never wrote, is ``absent`` (or ``count_only``), never "no help". Each fact's coverage names its source column
and the ids of the rows it came from (:class:`FieldCoverage`).

The value is an input to named predicates and to later renderings; it is never dumped whole into a cache key, seed,
hash, manifest or prompt, and no grading context imports it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from learnloop.clock import parse_utc
from learnloop.db.evidence_cutoff import CORRECTIONS_THEN, Cutoff

# -- coverage --------------------------------------------------------------------------------------------------

#: Captured, with its source row ids where it has rows.
PRESENT = "present"
#: Only the submitted count or flag exists: no detail rows (an attempt before the help ledger, help telemetry off,
#: or no help taken; the rows cannot tell these apart).
COUNT_ONLY = "count_only"
#: Detail rows exist but do not account for the submitted count, or a historical read cannot reconstruct part of
#: them (a help row's attachment has no time of its own).
PARTIAL = "partial"
#: The source does not exist for this attempt (a table older than the vault's schema, a column the row never wrote).
ABSENT = "absent"
#: The source was not read: a draft, or a compatibility adapter that holds the attempt row alone.
NOT_READ = "not_read"
COVERAGES = (PRESENT, COUNT_ONLY, PARTIAL, ABSENT, NOT_READ)

#: ``detail``: the help detail rows were read and found (``full``), or only the submitted count stands.
DETAIL_FULL = "full"
DETAIL_COUNTS_ONLY = "counts_only"

#: Where a reveal sits relative to the attempt's serve: before the presentation was served, between serve and
#: answer, or unknown (no served time was read).
BEFORE_SERVE = "before_serve"
DURING = "during"
POSITION_UNKNOWN = "unknown"

#: The help kinds the submit's fold counts into ``hints_used`` (``db.stores.help_assists.HINT_EQUIVALENT_KINDS_SQL``):
#: used here only to say whether the rows account for the submitted count, never to recompute it.
_COUNTED_KINDS = ("hint", "figure")


@dataclass(frozen=True)
class FieldCoverage:
    """How one fact was captured: its coverage, the stored source it was read from, the source rows, and why."""

    field: str
    coverage: str
    source: str
    source_ids: tuple[str, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        if self.coverage not in COVERAGES:
            raise ValueError(f"unknown coverage {self.coverage!r}")


@dataclass(frozen=True)
class HelpFact:
    """One ``help_assists`` row: an assist requested on the attempt's item under its submission, shown or not,
    attached to the attempt or not."""

    assist_id: str
    surface: str | None
    assist_kind: str | None
    hint_kind: str | None
    level: int | None
    counted_by: str | None
    requested_at: str | None
    shown: bool
    shown_at: str | None
    #: The row's ``attempt_id`` names this attempt (the attach at submit, or a later repair attach).
    attached: bool
    submitted_at: str | None
    #: The draft's length when the help was asked for (the text itself is not read).
    work_chars: int | None


@dataclass(frozen=True)
class QuestionFact:
    """One ``question_events`` row bound to the attempt: a question to the tutor during it."""

    question_id: str
    context: str | None
    question_type: str | None
    hint_equivalent: bool
    attempt_progress: str | None
    seconds_into_attempt: float | None
    created_at: str | None


@dataclass(frozen=True)
class RevealFact:
    """One ``reveal_events`` row on the attempt's item between the item's previous attempt and this one: how much
    of the answer a surface displayed, and when. A display row records coverage (the answer was on screen), not
    that the learner read it."""

    reveal_id: str
    source_kind: str | None
    amount: float
    basis: str | None
    created_at: str | None
    linked_attempt_id: str | None
    remediation_episode_id: str | None
    position: str


@dataclass(frozen=True)
class AttemptFacts:
    """What happened around one attempt, as stored (module docstring). Submitted values are verbatim."""

    attempt_id: str | None
    practice_item_id: str | None
    learning_object_id: str | None
    #: The stored attempt type.
    produced_as: Any
    correctness: Any = None
    hints_used: Any = 0
    primed: Any = False
    first_hint_progress: str | None = None
    declared_dont_know: Any = False
    declared_stuck: Any = False
    #: Whether the submitted answer was blank (None where the answer was not read).
    answer_empty: bool | None = None
    submission_id: str | None = None
    #: Where the answer was given (desktop, phone, TUI, MCP...): provenance only. One answer is one attempt and one
    #: set of facts whatever surface carried it.
    entry_surface: str | None = None
    hints: tuple[HelpFact, ...] = ()
    questions: tuple[QuestionFact, ...] = ()
    reveals: tuple[RevealFact, ...] = ()
    created_at: str | None = None
    received_at: str | None = None
    presented_at: str | None = None
    latency_seconds: Any = None
    active_seconds: Any = None
    plan_presentation_id: str | None = None
    probe_presentation_id: str | None = None
    #: Adaptive difficulty's ``pre_exposed`` comes from its own frozen serve inputs, read only by its replay through
    #: its material view: None here (coverage ``absent``).
    pre_exposed: bool | None = None
    detail: str = DETAIL_COUNTS_ONLY
    coverage: tuple[FieldCoverage, ...] = ()

    @property
    def bound_presentation(self) -> bool:
        """The attempt answers a recorded plan presentation (adaptive difficulty's ``bound_presentation``)."""

        return bool(self.plan_presentation_id)

    def coverage_of(self, field_name: str) -> FieldCoverage | None:
        for entry in self.coverage:
            if entry.field == field_name:
                return entry
        return None

    def assists(self, kind: str, *, shown: bool | None = None) -> tuple[HelpFact, ...]:
        """The help rows of one ``assist_kind`` (``check``, ``figure``, ``hint``...), optionally only the shown ones."""

        return tuple(row for row in self.hints if row.assist_kind == kind and (shown is None or row.shown == shown))

    def shown_before(self) -> tuple[RevealFact, ...]:
        return tuple(row for row in self.reveals if row.position == BEFORE_SERVE)

    def shown_during(self) -> tuple[RevealFact, ...]:
        return tuple(row for row in self.reveals if row.position == DURING)


# -- the submitted part alone ----------------------------------------------------------------------------------

_SUBMITTED_SOURCES = (
    ("produced_as", "practice_attempts.attempt_type"),
    ("hints_used", "practice_attempts.hints_used"),
    ("primed", "practice_attempts.primed"),
)
_DETAIL_SOURCES = (
    ("hints", "help_assists"),
    ("questions", "question_events"),
    ("reveals", "reveal_events"),
    ("presented_at", "plan_presentations.served_at"),
)
#: Built once: an adapter builds a facts value per row on hot paths (the router card's per-LO counts).
_SUBMITTED_COVERAGE = tuple(FieldCoverage(name, PRESENT, source) for name, source in _SUBMITTED_SOURCES) + tuple(
    FieldCoverage(name, NOT_READ, source) for name, source in _DETAIL_SOURCES)


def submitted_facts(
    *,
    attempt_type: Any,
    hints_used: Any = 0,
    primed: Any = False,
    correctness: Any = None,
    first_hint_progress: str | None = None,
    declared_dont_know: Any = False,
    declared_stuck: Any = False,
    attempt_id: str | None = None,
    practice_item_id: str | None = None,
    learning_object_id: str | None = None,
) -> AttemptFacts:
    """The submitted values alone, verbatim, with every detail source ``not_read``: what a reader holding an
    attempt row (or a draft) knows. No database."""

    return AttemptFacts(
        attempt_id=attempt_id, practice_item_id=practice_item_id, learning_object_id=learning_object_id,
        produced_as=attempt_type, correctness=correctness, hints_used=hints_used, primed=primed,
        first_hint_progress=first_hint_progress, declared_dont_know=declared_dont_know,
        declared_stuck=declared_stuck, coverage=_SUBMITTED_COVERAGE)


def facts_from_draft(draft: Any) -> AttemptFacts:
    """The facts of a submission before it has an attempt id: the draft's own fields (an
    ``attempts.attempts.AttemptDraft`` or anything with its field names), no database read, every stored detail
    ``not_read``."""

    facts = submitted_facts(
        attempt_type=getattr(draft, "attempt_type", None),
        hints_used=getattr(draft, "hints_used", 0),
        primed=getattr(draft, "primed", False),
        first_hint_progress=getattr(draft, "first_hint_progress", None),
        declared_dont_know=getattr(draft, "declared_dont_know", False),
        declared_stuck=getattr(draft, "declared_stuck", False),
        practice_item_id=getattr(draft, "practice_item_id", None),
    )
    answer = getattr(draft, "learner_answer_md", None)
    return _replace(
        facts,
        answer_empty=None if answer is None else not str(answer).strip(),
        submission_id=getattr(draft, "submission_id", None),
        latency_seconds=getattr(draft, "latency_seconds", None),
        active_seconds=getattr(draft, "active_seconds", None),
        plan_presentation_id=getattr(draft, "plan_presentation_id", None),
        probe_presentation_id=getattr(draft, "probe_presentation_id", None),
    )


def _replace(facts: AttemptFacts, **changes: Any) -> AttemptFacts:
    values = {name: getattr(facts, name) for name in AttemptFacts.__dataclass_fields__}
    values.update(changes)
    return AttemptFacts(**values)


# -- reading stored attempts -----------------------------------------------------------------------------------


class FactReader(Protocol):
    """Where :func:`collect_facts` reads: a connection, and the caller's visibility over the rows it reads."""

    @property
    def connection(self) -> Any: ...

    def visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class ConnectionReader:
    """Every row is visible: the caller's own connection, as the readers outside adaptive difficulty read."""

    connection: Any

    def visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return rows


@dataclass(frozen=True)
class FilteredReader:
    """Rows filtered by a view with adaptive difficulty's material view's shape (``filter(connection, table,
    rows)``): what it withholds (an item held out for an exam, a revision cut from held-out material, and every
    attempt, help row, question and reveal that names one) is never read here either."""

    connection: Any
    view: Any

    def visible(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self.view.filter(self.connection, table, rows)


_CHUNK = 500


def _tables(connection: Any) -> frozenset[str]:
    return frozenset(str(row[0]) for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"))


def _select(reader: FactReader, table: str, where: str, values: Sequence[Any], order: str) -> list[dict[str, Any]]:
    """``SELECT *`` (every column, so the reader's visibility rule sees every reference) in chunks of ids."""

    out: list[dict[str, Any]] = []
    for start in range(0, len(values), _CHUNK) if values else ():
        chunk = list(values[start:start + _CHUNK])
        marks = ",".join("?" for _ in chunk)
        cursor = reader.connection.execute(
            f"SELECT * FROM {table} WHERE {where.format(marks=marks)} ORDER BY {order}", chunk)
        names = [description[0] for description in cursor.description]
        out.extend(dict(zip(names, row, strict=True)) for row in cursor.fetchall())
    return reader.visible(table, out)


def _instant(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_utc(str(value))
    except (TypeError, ValueError):
        return None


def _known_by(value: Any, known_at: datetime | None) -> bool:
    """Under historical corrections, a time at or before the cutoff's known time; an unreadable one is not
    (fails closed, as the cutoff's own ``as_known_at`` rule)."""

    moment = _instant(value)
    return moment is not None and known_at is not None and moment <= known_at


def collect_facts(reader: FactReader, attempt_ids: Iterable[str], cutoff: Cutoff) -> dict[str, AttemptFacts]:
    """The facts of each stored attempt the reader shows and the cutoff admits, by attempt id, in the order asked.

    An attempt the reader withholds, or the cutoff does not admit (``Cutoff.admits`` over its ``created_at``,
    ``received_at`` and id), is left out. Under ``corrections = "then"`` (``Cutoff.as_known_at``) help is shown as
    known by the cutoff's ``known_at``: a row requested later is left out, a row shown later reads not shown, and its
    attachment (which writes no time of its own) is ``partial``. Every other preset reads the rows as they stand.

    The reads are a fixed handful per call whatever the number of attempts (attempts, the item's earlier attempts,
    help rows, questions, reveals, presentations, and the schema), each through the reader's visibility."""

    wanted = list(dict.fromkeys(str(value) for value in attempt_ids))
    if not wanted:
        return {}
    connection = reader.connection
    tables = _tables(connection)
    attempts = {str(row["id"]): row for row in _select(
        reader, "practice_attempts", "id IN ({marks})", wanted, "created_at, id")}
    admitted = {attempt_id: row for attempt_id, row in attempts.items()
                if cutoff.admits(row.get("created_at"), row.get("received_at") or None, attempt_id=attempt_id)}
    if not admitted:
        return {}
    then = cutoff.corrections == CORRECTIONS_THEN
    known_at = _instant(cutoff.time("known_at")) if then else None

    items = sorted({str(row["practice_item_id"]) for row in admitted.values() if row.get("practice_item_id")})
    earlier = _select(reader, "practice_attempts", "practice_item_id IN ({marks})", items, "created_at, id")
    previous: dict[str, str | None] = {}
    by_item: dict[str, list[dict[str, Any]]] = {}
    for row in earlier:
        by_item.setdefault(str(row["practice_item_id"]), []).append(row)
    for attempt_id, row in admitted.items():
        key = (str(row.get("created_at")), attempt_id)
        prior = [str(other["created_at"]) for other in by_item.get(str(row.get("practice_item_id")), ())
                 if (str(other.get("created_at")), str(other["id"])) < key]
        previous[attempt_id] = prior[-1] if prior else None

    help_by_attempt: dict[str, list[dict[str, Any]]] = {attempt_id: [] for attempt_id in admitted}
    if "help_assists" in tables:
        keys = {(str(row["submission_id"]), str(row["practice_item_id"])): attempt_id
                for attempt_id, row in admitted.items() if row.get("submission_id")}
        rows = _select(reader, "help_assists", "attempt_id IN ({marks})", list(admitted), "requested_at, rowid")
        if keys:
            rows += _select(reader, "help_assists", "attempt_id IS NULL AND submission_id IN ({marks})",
                            sorted({key[0] for key in keys}), "requested_at, rowid")
        for row in rows:
            owner = str(row["attempt_id"]) if row.get("attempt_id") else keys.get(
                (str(row.get("submission_id")), str(row.get("practice_item_id"))))
            if owner in help_by_attempt:
                help_by_attempt[owner].append(row)

    questions_by_attempt: dict[str, list[dict[str, Any]]] = {attempt_id: [] for attempt_id in admitted}
    if "question_events" in tables:
        for row in _select(reader, "question_events", "attempt_id IN ({marks})", list(admitted), "created_at, id"):
            questions_by_attempt[str(row["attempt_id"])].append(row)

    reveals_by_item: dict[str, list[dict[str, Any]]] = {}
    if "reveal_events" in tables:
        for row in _select(reader, "reveal_events", "practice_item_id IN ({marks})", items, "created_at, id"):
            reveals_by_item.setdefault(str(row["practice_item_id"]), []).append(row)

    served: dict[str, Any] = {}
    plan_ids = sorted({str(row["plan_presentation_id"]) for row in admitted.values()
                       if row.get("plan_presentation_id")})
    if "plan_presentations" in tables:
        served = {str(row["id"]): row.get("served_at") for row in _select(
            reader, "plan_presentations", "id IN ({marks})", plan_ids, "id")}

    out: dict[str, AttemptFacts] = {}
    for attempt_id in wanted:
        row = admitted.get(attempt_id)
        if row is None:
            continue
        out[attempt_id] = _facts(
            row, tables=tables, help_rows=help_by_attempt[attempt_id],
            question_rows=questions_by_attempt[attempt_id],
            reveal_rows=reveals_by_item.get(str(row.get("practice_item_id")), []),
            previous_at=previous.get(attempt_id), served=served, then=then, known_at=known_at)
    return out


def _facts(row: Mapping[str, Any], *, tables: frozenset[str], help_rows: list[dict[str, Any]],
           question_rows: list[dict[str, Any]], reveal_rows: list[dict[str, Any]], previous_at: str | None,
           served: Mapping[str, Any], then: bool, known_at: datetime | None) -> AttemptFacts:
    attempt_id = str(row["id"])
    coverage: list[FieldCoverage] = [FieldCoverage(name, PRESENT, source, (attempt_id,))
                                     for name, source in _SUBMITTED_SOURCES]

    def column(name: str, source: str) -> None:
        coverage.append(FieldCoverage(name, PRESENT if row.get(name) is not None else ABSENT, source, (attempt_id,)))

    column("first_hint_progress", "practice_attempts.first_hint_progress")
    column("correctness", "practice_attempts.correctness")
    column("received_at", "practice_attempts.received_at")
    column("latency_seconds", "practice_attempts.latency_seconds")
    column("active_seconds", "practice_attempts.active_seconds")
    coverage.append(FieldCoverage(
        "declared", PRESENT, "practice_attempts.declared_dont_know, practice_attempts.declared_stuck", (attempt_id,),
        "a row written before its column existed reads the column's default (0)"))

    if then:
        help_rows = [help_row for help_row in help_rows if _known_by(help_row.get("requested_at"), known_at)]
    hints = tuple(_help_fact(help_row, attempt_id, then=then, known_at=known_at) for help_row in help_rows)
    coverage.append(_help_coverage(row, hints, tables, then=then))

    if "question_events" not in tables:
        coverage.append(FieldCoverage("questions", ABSENT, "question_events", note="no such table"))
        questions: tuple[QuestionFact, ...] = ()
    else:
        if then:
            question_rows = [q for q in question_rows if _known_by(q.get("created_at"), known_at)]
        questions = tuple(_question_fact(q) for q in question_rows)
        coverage.append(FieldCoverage("questions", PRESENT, "question_events",
                                      tuple(q.question_id for q in questions)))

    presentation_id = row.get("plan_presentation_id")
    presented_at = served.get(str(presentation_id)) if presentation_id else None
    if presented_at is not None:
        coverage.append(FieldCoverage("presented_at", PRESENT, "plan_presentations.served_at",
                                      (str(presentation_id),)))
    else:
        coverage.append(FieldCoverage(
            "presented_at", ABSENT, "plan_presentations.served_at",
            note="no plan presentation bound or read" + ("; a probe presentation's serve time is not read here"
                                                         if row.get("probe_presentation_id") else "")))

    if "reveal_events" not in tables:
        coverage.append(FieldCoverage("reveals", ABSENT, "reveal_events", note="no such table"))
        reveals: tuple[RevealFact, ...] = ()
    else:
        reveals = _reveal_facts(row, reveal_rows, previous_at, presented_at, then=then, known_at=known_at)
        coverage.append(FieldCoverage(
            "reveals", PRESENT, "reveal_events", tuple(r.reveal_id for r in reveals),
            "rows on the item after its previous attempt, at or before this one: the ledger's rows, without the "
            "submit path's routine-display horizon or own-disclosure exemption"))
    coverage.append(FieldCoverage("pre_exposed", ABSENT, "item_serve_inputs.pre_exposed",
                                  note="adaptive difficulty's frozen serve inputs, read only by its replay"))

    hint_coverage = next(entry for entry in coverage if entry.field == "hints")
    answer = row.get("learner_answer_md")
    return AttemptFacts(
        attempt_id=attempt_id, practice_item_id=row.get("practice_item_id"),
        learning_object_id=row.get("learning_object_id"), produced_as=row.get("attempt_type"),
        correctness=row.get("correctness"), hints_used=row.get("hints_used"), primed=row.get("primed"),
        first_hint_progress=row.get("first_hint_progress"), declared_dont_know=row.get("declared_dont_know"),
        declared_stuck=row.get("declared_stuck"),
        answer_empty=None if "learner_answer_md" not in row else not str(answer or "").strip(),
        submission_id=row.get("submission_id"), entry_surface=row.get("entry_surface"), hints=hints,
        questions=questions, reveals=reveals,
        created_at=row.get("created_at"), received_at=row.get("received_at"), presented_at=presented_at,
        latency_seconds=row.get("latency_seconds"), active_seconds=row.get("active_seconds"),
        plan_presentation_id=presentation_id, probe_presentation_id=row.get("probe_presentation_id"),
        detail=DETAIL_FULL if hint_coverage.coverage in (PRESENT, PARTIAL) else DETAIL_COUNTS_ONLY,
        coverage=tuple(coverage))


def _help_fact(row: Mapping[str, Any], attempt_id: str, *, then: bool, known_at: datetime | None) -> HelpFact:
    shown = bool(row.get("shown"))
    shown_at = row.get("shown_at")
    if then and shown and not _known_by(shown_at, known_at):
        # Shown after the cutoff: as known then it had not been shown.
        shown, shown_at = False, None
    level = row.get("level")
    work_chars = row.get("work_chars")
    return HelpFact(
        assist_id=str(row["id"]), surface=row.get("surface"), assist_kind=row.get("assist_kind"),
        hint_kind=row.get("hint_kind"), level=None if level is None else int(level),
        counted_by=row.get("counted_by"), requested_at=row.get("requested_at"), shown=shown, shown_at=shown_at,
        attached=str(row.get("attempt_id") or "") == attempt_id, submitted_at=row.get("submitted_at"),
        work_chars=None if work_chars is None else int(work_chars))


def _help_coverage(row: Mapping[str, Any], hints: tuple[HelpFact, ...], tables: frozenset[str], *,
                   then: bool) -> FieldCoverage:
    source = "help_assists"
    if "help_assists" not in tables:
        return FieldCoverage("hints", ABSENT, source, note="no help_assists table: the submitted count alone")
    ids = tuple(hint.assist_id for hint in hints)
    if not hints:
        return FieldCoverage("hints", COUNT_ONLY, source,
                             note="no help row under the attempt or its submission key: no help, or none captured; "
                                  "the submitted count stands")
    counted = sum(1 for hint in hints if hint.attached and hint.shown and hint.assist_kind in _COUNTED_KINDS
                  and (hint.level is None or 1 <= hint.level <= 3))
    notes = []
    if counted != int(row.get("hints_used") or 0):
        notes.append(f"the rows account for {counted} of the submitted {int(row.get('hints_used') or 0)}: "
                     "both are kept")
    if any(not hint.attached for hint in hints):
        notes.append("some rows are under the submission key but not attached to the attempt")
    if then:
        notes.append("as known then: attachment and submit times have no time of their own")
    return FieldCoverage("hints", PARTIAL if notes else PRESENT, source, ids, "; ".join(notes) or None)


def _question_fact(row: Mapping[str, Any]) -> QuestionFact:
    seconds = row.get("seconds_into_attempt")
    return QuestionFact(
        question_id=str(row["id"]), context=row.get("context"), question_type=row.get("question_type"),
        hint_equivalent=bool(row.get("hint_equivalent")), attempt_progress=row.get("attempt_progress"),
        seconds_into_attempt=None if seconds is None else float(seconds), created_at=row.get("created_at"))


def _reveal_facts(row: Mapping[str, Any], reveal_rows: list[dict[str, Any]], previous_at: str | None,
                  presented_at: Any, *, then: bool, known_at: datetime | None) -> tuple[RevealFact, ...]:
    at = _instant(row.get("created_at"))
    start = _instant(previous_at)
    served = _instant(presented_at)
    out = []
    for reveal in reveal_rows:
        moment = _instant(reveal.get("created_at"))
        if moment is None or at is None or moment > at or (start is not None and moment <= start):
            continue
        if then and not _known_by(reveal.get("created_at"), known_at):
            continue
        position = POSITION_UNKNOWN if served is None else (BEFORE_SERVE if moment < served else DURING)
        out.append(RevealFact(
            reveal_id=str(reveal["id"]), source_kind=reveal.get("source_kind"), amount=float(reveal.get("amount") or 0.0),
            basis=reveal.get("basis"), created_at=reveal.get("created_at"),
            linked_attempt_id=reveal.get("attempt_id"), remediation_episode_id=reveal.get("remediation_episode_id"),
            position=position))
    return tuple(out)


__all__ = [
    "ABSENT", "AttemptFacts", "BEFORE_SERVE", "COUNT_ONLY", "COVERAGES", "ConnectionReader", "DETAIL_COUNTS_ONLY",
    "DETAIL_FULL", "DURING", "FactReader", "FieldCoverage", "FilteredReader", "HelpFact", "NOT_READ", "PARTIAL",
    "POSITION_UNKNOWN", "PRESENT", "QuestionFact", "RevealFact", "collect_facts", "facts_from_draft",
    "submitted_facts",
]
