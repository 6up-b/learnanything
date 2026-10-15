"""Exam and held-out material: THE predicate (exam-protection stage, 2026-10-13).

Owner rule (2026-10-13): exams and problem sets are assessment material. They
may seed question kinds and rigor, but held-out exam material is never taught,
never shown to a model as teaching or explanation, never leaked into practice,
and never reused as an independent check once the learner has seen it.

Every reader and writer that must tell exam material apart asks this module
one question: *is this span, unit, extraction or item exam or held-out
material, and as of which revision?* (the callers are listed in
``docs/reviews/exam-protection.md``). It is a leaf: the standard library, the
role-authority matrix, the database connection and the stdlib-only block store
at import time; the repository is duck-typed, and the two heavier helpers it
may need (a member's pinned extraction, a split unit's own blocks) are
imported where they are used.

**What is exam material**, read from the vault's source sets and the
database's unit selections when it is built:

1. *An exam member, whole, in every revision.* Every extraction of a source
   (all its revisions and runs) that a source-set member gives the default
   role ``exam``, or that a unit selection's outline role pick names ``exam``
   (the import-batch path's role, before the source joins a set): a
   re-import, or an extraction of a revision the set does not pin, is exam
   material too.
2. *An exam unit.* A member's scope entry with ``role_override: exam`` (a
   textbook chapter overridden to exam), on the reading the scope names
   (``SourceSetMember.scope_extraction_id``, exam protection by extraction
   identity, 2026-10-15) and nowhere else, by unit id with every nested unit
   (a merged unit is its members; a split child is the blocks under its own
   heading where that reading's boundary overrides define it, else its whole
   raw parent); a unit id that does not resolve there holds that reading out
   whole (fail closed). Rule 4 decides the book's other readings.
3. *A held-out unit, whatever its role.* Every unit marked
   ``held_out_evaluation`` in a unit selection (in a source set or not,
   whatever role its member has; owner, 2026-10-13), on the extraction whose
   selection marks it and whose :data:`MARKS_MADE_ON_KEY` names it, by unit
   id. A split child withholds its whole raw parent and a merged unit its
   members; a mark that does not resolve there withholds that whole
   extraction (fail closed). Nowhere else: rule 4.
4. *A reading held back until it is marked exactly* (protection redesign,
   2026-10-15; extraction identity, the same day's fourth round). Every
   protection mark names the reading it was made on and is resolved there
   only; nothing is rebound or inferred from positional unit ids, creation
   order or content matching. A book is *protected* when any extraction of
   any revision carries any mark or signal: an exam scope (rule 2), a
   held-out mark or the owner's "Mark exam material on this reading"
   (:data:`PROTECTION_MARK_KEY`) (rule 3), or a held-out assessment signal
   (the ``source_held_out_signal_marks`` ledger: the spans a model run
   marked held out on the reading it read, made under an exam role or on a
   book that is exam material; a cached inventory reused for another
   reading writes none, so it never marks that reading and never erases the
   origin's). Marks and signals are found across every revision and
   extraction, whatever the source sets pin now. Every extraction of a
   protected book with no exact owner's mark on it is withheld whole, as
   held-out material: no Reader Ask, no teaching or tutor context, no
   generation or retrieval, no leakage-gate pass, no search hit, no margin
   cue, whatever the settings. A held-out signal marks the reading it was
   made on only when the book carries no owner's mark at all. A legacy mark
   that names no reading it can be on (a scope without
   ``scope_extraction_id``, a selection without :data:`MARKS_MADE_ON_KEY`
   or naming another reading) is *ambiguous*: it is an owner's mark that
   places nothing, so every reading not marked exactly is withheld whole
   (:data:`AMBIGUOUS_MARK`) until the owner marks it. A marked reading is
   protected exactly as marked, by its own marks only.

The **held-out partition** (§8.5: what the leakage gate fingerprints and an
import or a generated item must never reproduce) is rule 3, rule 4 and the
held-out assessment signals (on the marked reading their model run read, and
nowhere else): :func:`held_out_partition`. It is the one held-out predicate
(Codex review F3): :attr:`ExamMaterial.held_out`, the Reader's refusals
(:func:`held_out_material`, read with the vault's source sets) and the gate
all read it.

**Revisions.** A verdict names the revision of the extraction the span lies in
and the pinned revisions of the members that made it exam material
(:class:`ExamVerdict`); every revision of an exam source counts, not only the
pinned one.

**Items** (:func:`item_exam_status`): an item reserved for a goal's held-out
exam is exam material, and so is an item whose own source (its canonical
exercise region, its block-level source refs) is. Serving reads two item
rules, behind one kill switch (``goals.held_out_selection``,
:func:`held_out_selection_active`; Codex review F6): an item made from
held-out material (:func:`held_out_items`) stays out of routine practice and
is never a cold probe or retry (F1), and an item whose own material the
learner has been shown (:func:`exposed_items`) is never an exam item, a cold
probe or a cold retry, and leaves a reserved exam before it starts (F5).

What a caller does with the answer is its own: teaching contexts and model
readers withhold exam material under every policy, the leakage gate
fingerprints the held-out partition, an import refuses exam material, the
Reader's model contexts (Ask and its dialogue, preset synthesis, quick and
passage checks) refuse held-out material (:func:`held_out_material`), and the
facet-meaning chokepoint resolves a citation of exam material to the role
``exam`` (assessment alignment only) while an explanatory citation beside it
may still support a facet's meaning (support, not leakage:
``role_authority.support_verdict``).
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.sources.role_authority import ASSESSMENT_ONLY_ROLES
from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import UnitRow, extraction_units, source_extraction_ids
from learnloop.db.stores.source_service import shown_items

#: The exam use mode of a protected, held-out evaluation unit (spec_source_ingestion_v2 §4.2).
HELD_OUT_EVALUATION = "held_out_evaluation"
#: The role whose material is assessment-only (``role_authority``).
EXAM_ROLE = "exam"

#: Why a span or extraction is exam material (:attr:`ExamVerdict.reasons`).
EXAM_MEMBER = "exam_member"
EXAM_UNIT = "exam_unit"
HELD_OUT_UNIT = "held_out_unit"
HELD_OUT_SIGNAL = "held_out_signal"
UNRESOLVED_UNIT = "unresolved_unit"
#: A whole reading of a protected source with no protection marked on it (rule 4).
UNMARKED_READING = "unmarked_reading"
#: A whole reading of a book whose legacy mark names no reading it can be on (rule 4).
AMBIGUOUS_MARK = "ambiguous_mark"
EXAM_RESERVED = "exam_reserved"
EXAM_SOURCE = "exam_source"

#: The key of a unit selection's ``exam_paper_metadata`` under which the
#: owner's "Mark exam material on this reading" records that it was marked
#: (``{"at": time, "from": [the readings its suggestion came from]}``): the
#: reading is marked even when nothing on it is held out (rule 4).
PROTECTION_MARK_KEY = "protection_marked"
#: The key of a unit selection's ``exam_paper_metadata`` naming the reading its
#: marks (held-out units, :data:`PROTECTION_MARK_KEY`) were made on:
#: ``{"extraction_id", "revision_id"}`` (exam protection by extraction
#: identity). Written by every writer of marks (:func:`marks_made_on`);
#: marks without it, or naming another reading, are ambiguous.
MARKS_MADE_ON_KEY = "marks_made_on"

SpanKey = tuple[str, str]


def is_exam_role(role: str | None) -> bool:
    """Whether a role's material is exam material (assessment-only)."""

    return str(role or "").strip() in ASSESSMENT_ONLY_ROLES


@dataclass(frozen=True)
class ExamVerdict:
    """Whether one span (or a whole extraction) is exam material, and why."""

    extraction_id: str
    span_id: str | None
    exam: bool
    held_out: bool
    reasons: tuple[str, ...] = ()
    #: The revision of the extraction the span lies in (None when unknown).
    revision_id: str | None = None
    source_id: str | None = None
    #: The pinned revisions of the members that made it exam material. Any
    #: revision of an exam source counts: ``revision_id`` need not be one of them.
    pinned_revision_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"extraction_id": self.extraction_id, "span_id": self.span_id, "exam": self.exam,
                "held_out": self.held_out, "reasons": list(self.reasons), "revision_id": self.revision_id,
                "source_id": self.source_id, "pinned_revision_ids": list(self.pinned_revision_ids)}


@dataclass
class _Acc:
    """What a build has found so far, with its reasons and the pinned revisions behind it."""

    whole: dict[str, set[str]] = field(default_factory=dict)
    spans: dict[SpanKey, set[str]] = field(default_factory=dict)
    pinned: dict[str, set[str]] = field(default_factory=dict)

    def add_whole(self, extraction_id: str, reason: str, pinned_revision: str | None) -> None:
        self.whole.setdefault(extraction_id, set()).add(reason)
        if pinned_revision:
            self.pinned.setdefault(extraction_id, set()).add(pinned_revision)

    def add_spans(self, extraction_id: str, span_ids: Iterable[str], reason: str,
                  pinned_revision: str | None) -> None:
        for span_id in span_ids:
            self.spans.setdefault((extraction_id, str(span_id)), set()).add(reason)
        if pinned_revision:
            self.pinned.setdefault(extraction_id, set()).add(pinned_revision)


@dataclass(frozen=True)
class Material:
    """Withheld material: whole extractions and single spans (with their reasons)."""

    extractions: frozenset[str] = frozenset()
    spans: frozenset[SpanKey] = frozenset()
    reasons: Mapping[Any, frozenset[str]] = field(default_factory=dict)
    pinned_revisions: Mapping[str, frozenset[str]] = field(default_factory=dict)

    def covers(self, extraction_id: str, span_id: str | None = None) -> bool:
        """Whether the span (or, with no span, the whole extraction) is in this material."""

        if extraction_id in self.extractions:
            return True
        return span_id is not None and (extraction_id, span_id) in self.spans

    def covered(self, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]:
        """The keys among ``keys`` this material covers."""

        wanted = {(str(key[0]), str(key[1])) for key in keys}
        return frozenset(key for key in wanted if self.covers(*key))

    @property
    def touched(self) -> frozenset[str]:
        """Every extraction this material covers wholly or in part."""

        return self.extractions | frozenset(key[0] for key in self.spans)

    @property
    def empty(self) -> bool:
        return not self.extractions and not self.spans

    @classmethod
    def from_acc(cls, acc: _Acc) -> Material:
        reasons: dict[Any, frozenset[str]] = {key: frozenset(value) for key, value in acc.spans.items()}
        reasons.update({key: frozenset(value) for key, value in acc.whole.items()})
        return cls(frozenset(acc.whole), frozenset(acc.spans), reasons,
                   {key: frozenset(value) for key, value in acc.pinned.items()})

    def union(self, other: Material) -> Material:
        reasons: dict[Any, frozenset[str]] = dict(self.reasons)
        for key, value in other.reasons.items():
            reasons[key] = reasons.get(key, frozenset()) | value
        pinned = dict(self.pinned_revisions)
        for key, value in other.pinned_revisions.items():
            pinned[key] = pinned.get(key, frozenset()) | value
        return Material(self.extractions | other.extractions, self.spans | other.spans, reasons, pinned)


@dataclass(frozen=True)
class ExamMaterial:
    """Exam material vault-wide (rules 1-3), with the held-out part (rule 3) apart."""

    material: Material
    held_out: Material
    #: ``{extraction id: (revision id, source id)}`` for every extraction read.
    runs: Mapping[str, tuple[str | None, str | None]] = field(default_factory=dict)

    @property
    def extractions(self) -> frozenset[str]:
        return self.material.extractions

    @property
    def spans(self) -> frozenset[SpanKey]:
        return self.material.spans

    def covers(self, extraction_id: str, span_id: str | None = None) -> bool:
        """Whether the span is exam material (held-out included)."""

        return self.material.covers(str(extraction_id), None if span_id is None else str(span_id))

    def is_held_out(self, extraction_id: str, span_id: str | None = None) -> bool:
        return self.held_out.covers(str(extraction_id), None if span_id is None else str(span_id))

    def withheld(self, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]:
        """The keys among ``keys`` that are exam material."""

        return self.material.covered(keys)

    def verdict(self, extraction_id: str, span_id: str | None = None) -> ExamVerdict:
        """The span's verdict, with its revision and the pinned revisions behind it."""

        extraction_id = str(extraction_id)
        span = None if span_id is None else str(span_id)
        reasons: set[str] = set(self.material.reasons.get(extraction_id, frozenset()))
        if span is not None:
            reasons |= set(self.material.reasons.get((extraction_id, span), frozenset()))
        revision_id, source_id = self.runs.get(extraction_id, (None, None))
        return ExamVerdict(
            extraction_id=extraction_id, span_id=span, exam=self.covers(extraction_id, span),
            held_out=self.is_held_out(extraction_id, span), reasons=tuple(sorted(reasons)),
            revision_id=revision_id, source_id=source_id,
            pinned_revision_ids=tuple(sorted(self.material.pinned_revisions.get(extraction_id, frozenset()))),
        )


# --- unit resolution ---------------------------------------------------------------------


def descendants(units: Sequence[UnitRow], roots: set[str]) -> set[str]:
    """``roots`` and every unit nested below them (a chapter's sections)."""

    chosen = set(roots)
    changed = True
    while changed:
        changed = False
        for unit in units:
            if unit.unit_id not in chosen and unit.parent_unit_id in chosen:
                chosen.add(unit.unit_id)
                changed = True
    return chosen


def raw_roots(unit_id: str, units: Mapping[str, UnitRow]) -> set[str] | None:
    """The raw units an effective unit id covers, or None when one is unknown.

    A raw id is itself; a merged unit (``a+b``) is its members; a split child
    (``a#slug``) is its whole raw parent (fail closed: its siblings too).
    """

    roots: set[str] = set()
    for part in str(unit_id).split("+"):
        raw = part.split("#", 1)[0]
        if raw not in units:
            return None
        roots.add(raw)
    return roots


class _Reader:
    """One build's database reads, each made once."""

    def __init__(self, connection: Any, repository: Any) -> None:
        self.connection = connection
        self.repository = repository
        self._units: dict[str, list[UnitRow]] = {}
        self._extractions: dict[tuple[str, str], list[str]] = {}
        self._readings: dict[str, list[str]] = {}
        self._selections: dict[str, Mapping[str, Any]] = {}
        self._effective: dict[str, Mapping[str, tuple[str, ...]] | None] = {}
        self._runs: dict[str, tuple[str | None, str | None] | None] = {}

    def units(self, extraction_id: str) -> list[UnitRow]:
        if extraction_id not in self._units:
            self._units[extraction_id] = extraction_units(self.connection, extraction_id)
        return self._units[extraction_id]

    def run(self, extraction_id: str | None) -> tuple[str | None, str | None] | None:
        """``(revision id, source id)`` of an extraction run, None when there is none."""

        if not extraction_id:
            return None
        key = str(extraction_id)
        if key not in self._runs:
            row = self.connection.execute(
                "SELECT run.revision_id, revision.source_id FROM source_extraction_runs AS run "
                "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id WHERE run.id = ?",
                (key,)).fetchone()
            self._runs[key] = None if row is None else (
                None if row[0] is None else str(row[0]), None if row[1] is None else str(row[1]))
        return self._runs[key]

    def source_extractions(self, source_id: str | None, revision_id: str | None) -> list[str]:
        key = (str(source_id or ""), str(revision_id or ""))
        if key not in self._extractions:
            found = (source_extraction_ids(self.connection, source_id=source_id) if source_id else []) + (
                source_extraction_ids(self.connection, revision_id=revision_id) if revision_id else [])
            self._extractions[key] = list(dict.fromkeys(found))
        return self._extractions[key]

    def readings(self, revision_id: str | None) -> list[str]:
        """The revision's completed top-level readings, oldest first."""

        if not revision_id:
            return []
        if revision_id not in self._readings:
            self._readings[revision_id] = [str(row[0]) for row in self.connection.execute(
                "SELECT id FROM source_extraction_runs WHERE revision_id = ? AND status = 'completed' "
                "AND parent_extraction_id IS NULL ORDER BY created_at, id", (str(revision_id),))]
        return self._readings[revision_id]

    def selection(self, extraction_id: str) -> Mapping[str, Any]:
        if extraction_id not in self._selections:
            self._selections[extraction_id] = self.repository.get_unit_selection(extraction_id) or {}
        return self._selections[extraction_id]

    def effective_spans(self, extraction_id: str) -> Mapping[str, tuple[str, ...]] | None:
        """``{effective unit id: its spans}`` under the extraction's own boundary overrides."""

        if extraction_id not in self._effective:
            overrides = list(self.selection(extraction_id).get("boundary_overrides") or [])
            ir = self.repository.load_document_ir(extraction_id) if overrides else None
            if ir is None:
                self._effective[extraction_id] = None
            else:
                from learnloop.content.synthesis.source_unit_selection import effective_unit_spans

                self._effective[extraction_id] = effective_unit_spans(ir, overrides)
        return self._effective[extraction_id]


def _origin_units(reader: _Reader, origin: str, narrowing: set[str]) -> tuple[set[str], set[str]] | None:
    """The scope resolved by unit id on the reading it names: ``(its spans
    there, the labels of its raw units)``, or None when a unit id does not
    resolve there."""

    units = reader.units(origin)
    by_id = {unit.unit_id: unit for unit in units}
    roots_of = {unit_id: raw_roots(unit_id, by_id) for unit_id in narrowing}
    if any(roots is None for roots in roots_of.values()):
        return None
    effective = reader.effective_spans(origin) if any("#" in unit_id for unit_id in narrowing) else None
    spans: set[str] = set()
    for unit_id, roots in roots_of.items():
        own = effective.get(unit_id) if effective is not None and "#" in unit_id else None
        if own is not None:
            spans.update(own)  # a split child: the blocks under its own heading
            continue
        chosen = descendants(units, set(roots or ()))
        spans.update(span for unit in units if unit.unit_id in chosen for span in unit.span_ids)
    labels = {by_id[root].label for roots in roots_of.values() for root in roots or ()}
    return spans, labels


def scope_reading_of(member: Any, run: tuple[str | None, str | None] | None) -> bool:
    """Whether a member's ``scope_extraction_id`` names a reading its scope can
    be on: an extraction of the member's own book, of the revision the
    member records for it (``scope_revision_id``, when recorded)."""

    if not getattr(member, "scope_extraction_id", None) or run is None:
        return False
    revision_id, source_id = run
    recorded_revision = getattr(member, "scope_revision_id", None)
    return source_id == str(member.source_id) and (not recorded_revision or recorded_revision == revision_id)


def _exact_scope_reading(reader: _Reader, member: Any) -> str | None:
    """The reading a member's scope names, when it names one it can be on (else None)."""

    extraction_id = getattr(member, "scope_extraction_id", None)
    return str(extraction_id) if scope_reading_of(member, reader.run(extraction_id)) else None


#: How a role's scope reaches the book's readings beyond the one it names.
#: An exam role read without the marks (``role_material``): every other extraction whole.
_ELSEWHERE_WHOLE = "whole"
#: A role that carries no exam protection (problem sets, notes): by label.
_ELSEWHERE_LABEL = "label"


def _member_units(reader: _Reader, member: Any, narrowing: set[str], acc: _Acc, reason: str, *,
                  elsewhere: str) -> None:
    """Resolve a member's narrowing units on the reading its scope names
    (``scope_extraction_id``), by unit id; a unit id that does not resolve
    there withholds every extraction of the book (fail closed). Every other
    extraction: ``elsewhere``.

    A scope that names no reading it can be on: an exam role withholds every
    extraction of the book whole; any other role is read, as before the
    field existed, on the first completed top-level reading of its pinned
    revision (those roles carry no exam protection)."""

    extraction_ids = reader.source_extractions(member.source_id, member.revision_id)
    pinned_revision = str(member.revision_id or "") or None
    origin = _exact_scope_reading(reader, member)
    if origin is None and elsewhere == _ELSEWHERE_WHOLE:
        for extraction_id in extraction_ids:
            acc.add_whole(extraction_id, AMBIGUOUS_MARK, pinned_revision)
        return
    if origin is None:
        found = reader.readings(member.revision_id)
        origin = found[0] if found else None
    resolved = _origin_units(reader, origin, narrowing) if origin else None
    if resolved is None:
        for extraction_id in dict.fromkeys([*extraction_ids, *([origin] if origin else [])]):
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
        return
    spans, labels = resolved
    acc.add_spans(origin, spans, reason, pinned_revision)
    for extraction_id in extraction_ids:
        if extraction_id == origin:
            continue
        if elsewhere == _ELSEWHERE_WHOLE:
            acc.add_whole(extraction_id, reason, pinned_revision)
            continue
        units = reader.units(extraction_id)
        roots = {unit.unit_id for unit in units if unit.label in labels}
        if {unit.label for unit in units if unit.unit_id in roots} != labels:
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
            continue
        chosen = descendants(units, roots)
        acc.add_spans(extraction_id, (span for unit in units if unit.unit_id in chosen for span in unit.span_ids),
                      reason, pinned_revision)


def _exam_narrowing(member: Any) -> set[str]:
    """The member's scope units overridden to an exam role (rule 2)."""

    return {str(entry.unit_id) for entry in member.scope if entry.role_override and is_exam_role(entry.role_override)}


def _role_material(reader: _Reader, member: Any, withheld_role: Callable[[str | None], bool], acc: _Acc, *,
                   member_reason: str, unit_reason: str) -> None:
    """A member's material whose role ``withheld_role`` names: the whole
    source when its default role does (rule 1), else its scope's units on the
    reading the scope names: exam units with every other extraction whole,
    the other roles by label."""

    if withheld_role(member.default_role):
        for extraction_id in reader.source_extractions(member.source_id, member.revision_id):
            acc.add_whole(extraction_id, member_reason, str(member.revision_id or "") or None)
        return
    narrowing = {str(entry.unit_id) for entry in member.scope
                 if entry.role_override and withheld_role(entry.role_override)}
    exam_units = narrowing & _exam_narrowing(member)
    if exam_units:
        _member_units(reader, member, exam_units, acc, unit_reason, elsewhere=_ELSEWHERE_WHOLE)
    if narrowing - exam_units:
        _member_units(reader, member, narrowing - exam_units, acc, unit_reason, elsewhere=_ELSEWHERE_LABEL)


def _outline_exam_sources(connection: Any) -> list[tuple[str | None, str | None, str]]:
    """``(source id, revision id, extraction id)`` of every unit selection whose
    outline role pick names ``exam`` (the import-batch path, before any source set)."""

    rows = connection.execute(
        "SELECT s.extraction_id, COALESCE(s.source_id, revision.source_id), run.revision_id "
        "FROM source_unit_selections AS s "
        "LEFT JOIN source_extraction_runs AS run ON run.id = s.extraction_id "
        "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id "
        "WHERE s.role_override = ? ORDER BY s.extraction_id", (EXAM_ROLE,)).fetchall()
    return [(None if row[1] is None else str(row[1]), None if row[2] is None else str(row[2]), str(row[0]))
            for row in rows]


# --- rules 2-4: protection marks, each bound to the reading it was made on ---------------


def _json_value(text: Any, default: Any) -> Any:
    try:
        value = json.loads(text) if text else default
    except (TypeError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def marks_made_on(extraction_id: str, revision_id: str | None) -> dict[str, Any]:
    """The value of :data:`MARKS_MADE_ON_KEY` a writer records with the marks it
    makes on ``extraction_id`` (``revision_id``: that extraction's revision)."""

    return {"extraction_id": str(extraction_id), "revision_id": None if revision_id is None else str(revision_id)}


def selection_marks_exact(extraction_id: str, metadata: Mapping[str, Any] | None,
                          run: tuple[str | None, str | None] | None) -> bool:
    """Whether a selection's marks name the reading they sit on: its
    :data:`MARKS_MADE_ON_KEY` names this extraction and its run's revision.
    Marks without it (written before it existed) or naming another reading
    (copied from one) are ambiguous."""

    made_on = (metadata or {}).get(MARKS_MADE_ON_KEY)
    if not isinstance(made_on, Mapping) or str(made_on.get("extraction_id") or "") != str(extraction_id):
        return False
    if run is None:
        return False
    recorded = made_on.get("revision_id")
    return not recorded or str(recorded) == str(run[0] or "")


def _marked_selections(connection: Any) -> list[tuple[str, str | None, str | None, list[str], bool,
                                                    Mapping[str, Any]]]:
    """``(extraction id, source id, revision id, held-out unit ids, marked by
    the owner's action, paper metadata)`` of every unit selection that marks
    protection: a held-out mark (rule 3) or the owner's "Mark exam material
    on this reading" (:data:`PROTECTION_MARK_KEY`)."""

    rows = connection.execute(
        "SELECT s.extraction_id, COALESCE(s.source_id, revision.source_id), run.revision_id, "
        "s.exam_use_modes_json, s.exam_paper_metadata_json FROM source_unit_selections AS s "
        "LEFT JOIN source_extraction_runs AS run ON run.id = s.extraction_id "
        "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id "
        "WHERE s.exam_use_modes_json LIKE ? OR s.exam_paper_metadata_json LIKE ? ORDER BY s.extraction_id",
        (f"%{HELD_OUT_EVALUATION}%", f"%{PROTECTION_MARK_KEY}%")).fetchall()
    found: list[tuple[str, str | None, str | None, list[str], bool, Mapping[str, Any]]] = []
    for extraction_id, source_id, revision_id, modes_json, metadata_json in rows:
        modes = _json_value(modes_json, {})
        held = sorted(str(unit) for unit, mode in modes.items() if mode == HELD_OUT_EVALUATION)
        metadata = _json_value(metadata_json, {})
        flagged = PROTECTION_MARK_KEY in metadata
        if held or flagged:
            found.append((str(extraction_id), None if source_id is None else str(source_id),
                          None if revision_id is None else str(revision_id), held, flagged, metadata))
    return found


def _signal_ledger(connection: Any) -> list[dict[str, Any]]:
    """Every row of the held-out signal ledger with its book (migration 225)."""

    rows = connection.execute(
        "SELECT m.revision_id, m.extraction_id, m.unit_id, m.made_as_role, m.span_ids_json, r.source_id "
        "FROM source_held_out_signal_marks AS m LEFT JOIN source_revisions AS r ON r.id = m.revision_id "
        "ORDER BY m.created_at, m.id").fetchall()
    return [{"revision_id": None if row[0] is None else str(row[0]),
             "extraction_id": None if row[1] is None else str(row[1]), "unit_id": str(row[2]),
             "made_as_role": None if row[3] is None else str(row[3]),
             "span_ids": frozenset(str(span) for span in _json_value(row[4], []) if span),
             "source_id": None if row[5] is None else str(row[5])} for row in rows]


#: What kind of legacy mark makes a book's protection ambiguous (:attr:`SourceMarks.ambiguous`).
AMBIGUOUS_SCOPE = "scope"
AMBIGUOUS_SELECTION = "selection"


@dataclass
class _Marks:
    """One book's protection marks, each on the reading it names (rules 2-4)."""

    source_id: str | None
    revision_id: str | None
    #: Every extraction of the book (all revisions and runs), the marking ones included.
    extractions: list[str] = field(default_factory=list)
    #: The readings an exact owner's mark is on: an exam scope naming it, a
    #: held-out mark of its own selection, the owner's marking action.
    owner: set[str] = field(default_factory=set)
    #: The readings the owner's "Mark exam material on this reading" marked
    #: exactly: the owner reviewed every mark of the book for them, legacy
    #: ones included, so no ambiguity reaches them.
    confirmed: set[str] = field(default_factory=set)
    #: ``{reading: its exact exam scope's unit ids}`` (rule 2).
    scope_units: dict[str, set[str]] = field(default_factory=dict)
    #: ``{reading: the pinned revisions of the members whose scope names it}``.
    scope_pins: dict[str, set[str]] = field(default_factory=dict)
    #: ``{reading: its own held-out unit ids}`` (rule 3).
    held_units: dict[str, list[str]] = field(default_factory=dict)
    #: ``{reading: [(held-out signal spans, revision)]}``: signals a model run made on it.
    signals: dict[str, list[tuple[frozenset[str], str | None]]] = field(default_factory=dict)
    #: Legacy marks that name no reading they can be on (:data:`AMBIGUOUS_SCOPE`, ...).
    ambiguous: set[str] = field(default_factory=set)
    #: An exam scope names no reading it can be on: it may be about any reading.
    ambiguous_everywhere: bool = False
    #: Readings whose own selection carries marks that name no reading (or another one).
    ambiguous_on: set[str] = field(default_factory=set)
    #: Held-out signals whose reading is not known (a cache row rebound before the ledger).
    unbound: bool = False
    #: ``{reading: legacy held-out unit ids}``: placed nowhere, kept for the marking's suggestion.
    legacy_units: dict[str, list[str]] = field(default_factory=dict)
    #: The unit ids of the exam scopes that name no reading (the suggestion reads them).
    legacy_scope_units: set[str] = field(default_factory=set)

    @property
    def protected(self) -> bool:
        """Any mark or signal on any reading of the book (exact, ambiguous or unbound)."""

        return bool(self.owner or self.scope_units or self.held_units or self.signals or self.ambiguous
                    or self.unbound)

    @property
    def marked(self) -> set[str]:
        """The readings protection is marked on exactly: an owner's mark that
        no ambiguous mark may also be about (a legacy exam scope may be about
        any reading, a legacy selection mark about its own), unless the
        owner's marking action marked it; or, where the book carries no
        owner's mark at all (exact or ambiguous), the readings with held-out
        signals of their own."""

        if not (self.owner or self.ambiguous):
            return set(self.signals)
        return {reading for reading in self.owner if reading in self.confirmed or (
            not self.ambiguous_everywhere and reading not in self.ambiguous_on)}

    @property
    def unmarked(self) -> list[str]:
        """The extractions withheld whole until protection is marked on them exactly."""

        if not self.protected:
            return []
        marked = self.marked
        return [extraction_id for extraction_id in self.extractions if extraction_id not in marked]


def _signal_counts(row: Mapping[str, Any], *, exam_sources: set[str], scoped: set[str],
                   scope_spans: Mapping[str, set[str]]) -> bool:
    """Whether a ledger row's held-out signals are protection: made under an
    exam role, or on a book that is exam material now (rule 1: an exam member
    of any set, or an outline exam pick), or on spans an exact exam scope
    names on the same reading, or (a row whose role was not recorded) on a
    book with an exam scope that names no reading (fail closed)."""

    if is_exam_role(row["made_as_role"]):
        return True
    source_id = row["source_id"]
    if source_id in exam_sources:
        return True
    extraction_id = row["extraction_id"]
    if extraction_id and row["span_ids"] & scope_spans.get(extraction_id, set()):
        return True
    return row["made_as_role"] is None and source_id in scoped


def _protection_marks(reader: _Reader, vault_or_sets: Any) -> dict[tuple[str, str], _Marks]:
    """Every book's protection marks, each on the reading it names (rules 2-4),
    read from the vault's source sets and the database, across every revision
    and extraction of the book whatever its membership: exam scopes (rule 2),
    held-out marks and the owner's marking action (rule 3, the unit
    selections) and the held-out signal ledger. Grouped by book (a mark
    whose run names no book by its revision, else its own extraction)."""

    found: dict[tuple[str, str], _Marks] = {}

    def group(source_id: str | None, revision_id: str | None, extraction_id: str | None) -> _Marks:
        key = (("source", source_id) if source_id else ("revision", revision_id) if revision_id
               else ("extraction", str(extraction_id or "")))
        if key not in found:
            found[key] = _Marks(source_id, None if source_id else revision_id)
        return found[key]

    sets = _source_sets(vault_or_sets)
    exam_sources: set[str] = set()
    scoped: set[str] = set()
    for source_set in sets:
        for member in source_set.members:
            if is_exam_role(member.default_role):
                exam_sources.add(str(member.source_id))
                continue
            units = _exam_narrowing(member)
            if not units:
                continue
            scoped.add(str(member.source_id))
            marks = group(str(member.source_id), str(member.revision_id or "") or None, None)
            reading = _exact_scope_reading(reader, member)
            if reading is None:
                marks.ambiguous.add(AMBIGUOUS_SCOPE)
                marks.ambiguous_everywhere = True
                marks.legacy_scope_units |= units
                continue
            marks.owner.add(reading)
            marks.extractions.append(reading)
            marks.scope_units.setdefault(reading, set()).update(units)
            if member.revision_id:
                marks.scope_pins.setdefault(reading, set()).add(str(member.revision_id))
    exam_sources |= {str(source_id) for source_id, _revision, _picked in _outline_exam_sources(reader.connection)
                     if source_id}
    for extraction_id, source_id, revision_id, held, flagged, metadata in _marked_selections(reader.connection):
        marks = group(source_id, revision_id, extraction_id)
        marks.extractions.append(extraction_id)
        if not selection_marks_exact(extraction_id, metadata, reader.run(extraction_id)):
            marks.ambiguous.add(AMBIGUOUS_SELECTION)
            marks.ambiguous_on.add(extraction_id)
            if held:
                marks.legacy_units[extraction_id] = held
            continue
        marks.owner.add(extraction_id)
        if flagged:
            marks.confirmed.add(extraction_id)
        if held:
            marks.held_units[extraction_id] = held
    scope_spans: dict[str, set[str]] = {}
    for marks in found.values():
        for reading, units in marks.scope_units.items():
            resolved = _origin_units(reader, reading, units)
            scope_spans[reading] = resolved[0] if resolved is not None else {
                span for unit in reader.units(reading) for span in unit.span_ids}
    for row in _signal_ledger(reader.connection):
        if not row["span_ids"] or not _signal_counts(row, exam_sources=exam_sources, scoped=scoped,
                                                     scope_spans=scope_spans):
            continue
        marks = group(row["source_id"], row["revision_id"], row["extraction_id"])
        extraction_id = row["extraction_id"]
        run = reader.run(extraction_id)
        if extraction_id and run is not None and run[0] == row["revision_id"]:
            marks.signals.setdefault(extraction_id, []).append((row["span_ids"], row["revision_id"]))
            marks.extractions.append(extraction_id)
        else:
            marks.unbound = True
    for marks in found.values():
        everything = reader.source_extractions(marks.source_id, marks.revision_id) if (
            marks.source_id or marks.revision_id) else []
        marks.extractions = list(dict.fromkeys([*everything, *marks.extractions]))
    return {key: marks for key, marks in found.items() if marks.protected}


def _held_units(reader: _Reader, extraction_id: str, unit_ids: Iterable[str], held: _Acc) -> None:
    """An extraction's own held-out marks (rule 3), by unit id: a split child
    withholds its whole raw parent, a merged unit its members; a mark that
    does not resolve withholds the whole extraction (fail closed)."""

    units = reader.units(extraction_id)
    by_id = {unit.unit_id: unit for unit in units}
    roots: set[str] = set()
    for unit_id in unit_ids:
        resolved = raw_roots(unit_id, by_id)
        if resolved is None:
            held.add_whole(extraction_id, UNRESOLVED_UNIT, None)
            return
        roots |= resolved
    chosen = descendants(units, roots)
    held.add_spans(extraction_id, (span for unit in units if unit.unit_id in chosen for span in unit.span_ids),
                   HELD_OUT_UNIT, None)


def _add_protection(reader: _Reader, vault_or_sets: Any, held: _Acc, exam: _Acc | None = None) -> None:
    """Rules 2-4 into ``held`` (and the exam scopes' units into ``exam``): on
    each reading marked exactly, its own exam scope units, held-out marks and
    signals; every other extraction of a protected book, whole. An exact
    scope unit that does not resolve on the reading it names holds that
    reading out whole (fail closed)."""

    for marks in _protection_marks(reader, vault_or_sets).values():
        marked = marks.marked
        whole_reasons = (UNMARKED_READING, AMBIGUOUS_MARK) if marks.ambiguous else (UNMARKED_READING,)
        for extraction_id in marks.unmarked:
            for reason in whole_reasons:
                held.add_whole(extraction_id, reason, None)
        for reading, units in sorted(marks.scope_units.items()):
            if reading not in marked:
                continue
            pins = sorted(marks.scope_pins.get(reading, ())) or [None]
            resolved = _origin_units(reader, reading, units)
            if resolved is None:
                for pin in pins:
                    held.add_whole(reading, UNRESOLVED_UNIT, pin)
            elif exam is not None:
                for pin in pins:
                    exam.add_spans(reading, resolved[0], EXAM_UNIT, pin)
        for extraction_id, unit_ids in sorted(marks.held_units.items()):
            if extraction_id in marked:
                _held_units(reader, extraction_id, unit_ids, held)
        for reading, entries in sorted(marks.signals.items()):
            if reading not in marked:
                continue
            for spans, revision_id in entries:
                held.add_spans(reading, spans, HELD_OUT_SIGNAL, revision_id)


def _runs(connection: Any, extraction_ids: Iterable[str]) -> dict[str, tuple[str | None, str | None]]:
    ids = sorted({str(value) for value in extraction_ids if value})
    found: dict[str, tuple[str | None, str | None]] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for extraction_id, revision_id, source_id in connection.execute(
            "SELECT run.id, run.revision_id, revision.source_id FROM source_extraction_runs AS run "
            "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id "
            f"WHERE run.id IN ({', '.join('?' for _ in chunk)})", chunk,
        ):
            found[str(extraction_id)] = (None if revision_id is None else str(revision_id),
                                         None if source_id is None else str(source_id))
    return found


def _source_sets(vault_or_sets: Any) -> list[Any]:
    sets = getattr(vault_or_sets, "source_sets", vault_or_sets)
    return list(sets or ())


def exam_material(vault_or_sets: Any, repository: Any) -> ExamMaterial:
    """Exam material vault-wide (rules 1-4): ``vault`` or its ``source_sets``."""

    acc = _Acc()
    held = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        for source_set in _source_sets(vault_or_sets):
            for member in source_set.members:
                if is_exam_role(member.default_role):
                    for extraction_id in reader.source_extractions(member.source_id, member.revision_id):
                        acc.add_whole(extraction_id, EXAM_MEMBER, str(member.revision_id or "") or None)
        for source_id, revision_id, picked in _outline_exam_sources(connection):
            for extraction_id in dict.fromkeys([*reader.source_extractions(source_id, revision_id), picked]):
                acc.add_whole(extraction_id, EXAM_SOURCE, None)
        _add_protection(reader, vault_or_sets, held, acc)
        held_material = Material.from_acc(held)
        material = Material.from_acc(acc).union(held_material)
        runs = _runs(connection, set(material.extractions) | {key[0] for key in material.spans})
    return ExamMaterial(material=material, held_out=held_material, runs=runs)


def role_material(vault_or_sets: Any, repository: Any, withheld_role: Callable[[str | None], bool], *,
                  member_reason: str = "role_member", unit_reason: str = "role_unit") -> Material:
    """Members' material whose role ``withheld_role`` names (rules 1 and 2),
    for callers that withhold more than exams (``corpus.teaching_exclusions``:
    problem sets, notes and unknown roles). A scope's units are resolved on
    the reading it names; beyond it a role that carries no exam protection is
    followed by label, and an exam unit withholds every other extraction
    whole (and a scope that names no reading, every extraction)."""

    acc = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        for source_set in _source_sets(vault_or_sets):
            for member in source_set.members:
                _role_material(reader, member, withheld_role, acc, member_reason=member_reason,
                               unit_reason=unit_reason)
    return Material.from_acc(acc)


def exam_withheld(vault_or_sets: Any, repository: Any, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]:
    """The keys among ``keys`` that are exam material."""

    wanted = [(str(key[0]), str(key[1])) for key in keys]
    if not wanted:
        return frozenset()
    return exam_material(vault_or_sets, repository).withheld(wanted)


# --- rule 4 for the book's card, doctor and the owner's marking ---------------------------


@dataclass(frozen=True)
class SourceMarks:
    """One protected book's readings: where protection is marked exactly, the
    extractions held back until it is marked on them (rule 4), and the
    legacy marks that name no reading (``ambiguous``: :data:`AMBIGUOUS_SCOPE`,
    :data:`AMBIGUOUS_SELECTION`)."""

    source_id: str
    marked: tuple[str, ...]
    unmarked: tuple[str, ...]
    ambiguous: tuple[str, ...] = ()


def source_marks(vault_or_sets: Any, repository: Any) -> dict[str, SourceMarks]:
    """``{source id: its marks}`` for every protected book (rule 4): what the
    book's card ("Mark exam material on this reading"), doctor and the marking
    action read."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        found = _protection_marks(reader, vault_or_sets)
    return {str(marks.source_id): SourceMarks(
        str(marks.source_id), tuple(sorted(marks.marked & set(marks.extractions))), tuple(marks.unmarked),
        tuple(sorted(marks.ambiguous)))
        for marks in found.values() if marks.source_id}


def reading_held_back(vault_or_sets: Any, repository: Any, extraction_id: str | None) -> bool:
    """Whether a reading is withheld whole until protection is marked on it (rule 4)."""

    if not extraction_id:
        return False
    return any(str(extraction_id) in marks.unmarked for marks in source_marks(vault_or_sets, repository).values())


def protected_spans_by_reading(vault_or_sets: Any, repository: Any, source_id: str) -> dict[str, set[str]]:
    """``{reading: spans}`` every mark of a book would protect if it were read
    on that reading by its own unit ids, exact or not: the owner's marking
    suggestion's sources (never an authority). Exact marks and signals on the
    reading they name; a legacy held-out mark on the reading its selection
    sits on; a legacy exam scope (it names no reading) on every reading by
    unit id. A unit id that does not resolve suggests nothing."""

    found: dict[str, set[str]] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        marks = next((value for value in _protection_marks(reader, vault_or_sets).values()
                      if value.source_id == str(source_id)), None)
        if marks is None:
            return {}

        def place(reading: str, unit_ids: Iterable[str]) -> None:
            units = reader.units(reading)
            by_id = {unit.unit_id: unit for unit in units}
            for unit_id in unit_ids:
                roots = raw_roots(unit_id, by_id)
                if roots is None:
                    continue
                chosen = descendants(units, roots)
                found.setdefault(reading, set()).update(
                    span for unit in units if unit.unit_id in chosen for span in unit.span_ids)

        for reading, units in marks.scope_units.items():
            place(reading, units)
        for reading, unit_ids in [*marks.held_units.items(), *marks.legacy_units.items()]:
            place(reading, unit_ids)
        for reading, entries in marks.signals.items():
            for spans, _revision in entries:
                found.setdefault(reading, set()).update(spans)
        if marks.legacy_scope_units:
            for reading in marks.extractions:
                place(reading, marks.legacy_scope_units)
    return found


# --- the Reader's model contexts ---------------------------------------------------------

#: What a learner is told when a Reader request would show held-out material to a model.
HELD_OUT_REFUSAL = ("This passage is held out for evaluation (an exam you'll sit later), so LearnLoop won't "
                    "explain it or make questions from it: that keeps the exam a fair test.")
#: What a learner is told when the passage is on a reading held back until its
#: exam material is marked (rule 4): not an exam question, a reading not yet checked.
HELD_BACK_REFUSAL = ("This reading of the book is held back until you mark its exam material (on the book's card "
                     "in the Library), so LearnLoop won't explain it or make questions from it yet.")


def held_out_refusal(material: Material, extraction_id: str | None) -> str:
    """The plain refusal for a Reader request over ``material``: a reading held
    back until it is marked says so (rule 4); anything else is held out."""

    reasons = material.reasons.get(str(extraction_id or ""), frozenset())
    return HELD_BACK_REFUSAL if UNMARKED_READING in reasons else HELD_OUT_REFUSAL


def held_out_material(vault_or_sets: Any, repository: Any) -> Material:
    """The held-out partition (:func:`held_out_partition`, every subject): what
    the Reader's model contexts refuse and a Reader import never turns into
    practice. The same material as :attr:`ExamMaterial.held_out` and as the
    leakage gate's fingerprint, so a caller that holds only a repository loads
    the vault's source sets rather than reading a narrower partition (Codex
    review F3: the exam units' held-out assessment signals need them)."""

    return held_out_partition(vault_or_sets, repository)


def held_out_among(material: Material, extraction_id: str | None, span_ids: Iterable[str | None]) -> list[str]:
    """The span ids among ``span_ids`` (in order, each once) that ``material`` covers."""

    extraction = str(extraction_id or "")
    if not extraction:
        return []
    wanted = dict.fromkeys(str(span) for span in span_ids if span)
    return [span for span in wanted if material.covers(extraction, span)]


# --- the held-out partition --------------------------------------------------------------


@dataclass(frozen=True)
class HeldOutSpan:
    """One held-out span: its identity and block text."""

    extraction_id: str
    span_id: str
    text: str

    @property
    def key(self) -> str:
        return f"{self.extraction_id}/{self.span_id}"


def held_out_partition(vault_or_sets: Any, repository: Any, *,
                       subject_ids: Iterable[str] | None = None) -> Material:
    """The held-out partition: every held-out unit (rule 3, any role, on the
    extraction that marks it), every reading held back until protection is
    marked on it exactly (rule 4, whole), plus the held-out assessment
    signals on the marked reading their model run read. The one held-out
    predicate: the leakage gate fingerprints it, the Reader refuses it
    (:func:`held_out_material`) and :attr:`ExamMaterial.held_out` is it.

    ``subject_ids`` no longer narrows anything (exam protection by extraction
    identity): a signal is its book's protection whatever source sets it is
    in now, so every subject's gate counts it (fail closed)."""

    del subject_ids  # protection marks are their book's, wherever it sits (see the docstring)
    held = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        _add_protection(_Reader(connection, repository), vault_or_sets, held)
    return Material.from_acc(held)


def held_out_spans(vault_or_sets: Any, repository: Any, *,
                   subject_ids: Iterable[str] | None = None) -> list[HeldOutSpan]:
    """Every held-out span with its text, in a deterministic order (a span listed once).

    A whole held-out extraction (a held-out unit that does not resolve there)
    contributes every block it has (fail closed)."""

    partition = held_out_partition(vault_or_sets, repository, subject_ids=subject_ids)
    found: list[HeldOutSpan] = []
    seen: set[SpanKey] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for extraction_id in sorted(partition.extractions):
            for span_id, text in connection.execute(
                    "SELECT span_id, text FROM source_document_blocks WHERE extraction_id=? ORDER BY ordinal, span_id",
                    (extraction_id,)):
                key = (extraction_id, str(span_id))
                if text and key not in seen:
                    seen.add(key)
                    found.append(HeldOutSpan(extraction_id, str(span_id), str(text)))
        wanted = sorted(key for key in partition.spans if key not in seen and key[0] not in partition.extractions)
        for start in range(0, len(wanted), 400):
            chunk = wanted[start:start + 400]
            marks = ",".join("(?, ?)" for _ in chunk)
            texts = {(str(row[0]), str(row[1])): row[2] for row in connection.execute(
                f"SELECT extraction_id, span_id, text FROM source_document_blocks WHERE (extraction_id, span_id) IN "
                f"(VALUES {marks})", [value for key in chunk for value in key])}
            for key in chunk:
                text = texts.get(key)
                if text and key not in seen:
                    seen.add(key)
                    found.append(HeldOutSpan(key[0], key[1], str(text)))
    return found


# --- items ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class ItemExamStatus:
    """Why an item is exam material: reserved for a held-out exam, or made from exam material."""

    practice_item_id: str
    reasons: tuple[str, ...]
    held_out: bool
    spans: tuple[SpanKey, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"practice_item_id": self.practice_item_id, "reasons": list(self.reasons),
                "held_out": self.held_out, "spans": [list(key) for key in self.spans]}


def _parse_block_span(locator: str) -> SpanKey | None:
    from learnloop.ingest.locators import parse_block_span

    parsed = parse_block_span(str(locator or ""))
    return None if parsed is None else (str(parsed[0]), str(parsed[1]))


def source_ref_keys(ref: Any) -> tuple[set[SpanKey], set[str]]:
    """One source ref's location, normalized: ``(block keys, extractions it
    names without a block)``. The shared parser for provenance refs: a
    ``block_span_v1`` locator, and span ids plain (under the ref's
    extraction) or namespaced (``ext/span``, ``ext:span``)."""

    keys: set[SpanKey] = set()
    whole: set[str] = set()
    extraction_id = getattr(ref, "extraction_id", None)
    spans = [str(span) for span in getattr(ref, "span_ids", None) or () if span]
    parsed = _parse_block_span(getattr(ref, "locator", None) or "")
    if parsed is not None:
        keys.add(parsed)
    for span in spans:
        if extraction_id and span.startswith((f"{extraction_id}/", f"{extraction_id}:")):
            keys.add((str(extraction_id), span[len(extraction_id) + 1:]))
        elif "/" in span or ":" in span:
            # Block span ids never carry a separator (``s12``): this is ``ext/span`` or ``ext:span``.
            cut = min(index for index in (span.find("/"), span.find(":")) if index >= 0)
            head, tail = span[:cut], span[cut + 1:]
            keys.add((head or str(extraction_id or ""), tail))
        elif extraction_id:
            keys.add((str(extraction_id), span))
    if extraction_id and not spans and parsed is None:
        whole.add(str(extraction_id))
    return keys, whole


def item_source_keys(item: Any) -> tuple[set[SpanKey], set[str]]:
    """The item's own source: ``(block keys, whole extractions)`` its canonical
    exercise and its provenance source refs name (:func:`source_ref_keys`)."""

    keys: set[SpanKey] = set()
    whole: set[str] = set()
    exercise = getattr(item, "canonical_exercise", None)
    if exercise is not None and getattr(exercise, "extraction_id", None):
        keys |= {(str(exercise.extraction_id), str(span)) for span in exercise.span_ids or ()}
    provenance = getattr(item, "provenance", None)
    for ref in getattr(provenance, "source_refs", None) or ():
        ref_keys, ref_whole = source_ref_keys(ref)
        keys |= ref_keys
        whole |= ref_whole
    return keys, whole


def source_ref_protected(material: ExamMaterial, ref: Any, repository: Any) -> bool:
    """Whether a source ref's text (its quote) may be exam or held-out material,
    so a model context must not carry it (PF's parent quotes; Codex review F4).

    Located through :func:`source_ref_keys`; conservative where it cannot place
    the text: a block of the material, an extraction the ref names without a
    block where any of it is material, a block id that is not a block of a
    partly protected extraction, or a ref with no location whose source or
    revision has material in it."""

    keys, whole = source_ref_keys(ref)
    touched = material.material.touched
    if any(material.covers(*key) for key in keys) or whole & touched:
        return True
    partial = {extraction for extraction, _span in keys if extraction in touched}
    if partial:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            for extraction in partial:
                blocks = {str(row[0]) for row in connection.execute(
                    "SELECT span_id FROM source_document_blocks WHERE extraction_id=?", (extraction,))}
                if any(span not in blocks for key_extraction, span in keys if key_extraction == extraction):
                    return True
    if keys or whole:
        return False
    revision_id = getattr(ref, "revision_id", None)
    source_id = getattr(ref, "source_id", None)
    if not revision_id and not source_id:
        return False
    runs = [material.runs.get(extraction, (None, None)) for extraction in touched]
    return any((revision_id and run[0] == str(revision_id)) or (source_id and run[1] == str(source_id))
               for run in runs)


def held_out_item_ids(items: Iterable[Any], held_out: Material) -> frozenset[str]:
    """The items whose own source (:func:`item_source_keys`: the canonical
    exercise, block-level provenance refs, an extraction named whole) lies in
    ``held_out`` material (Codex review F1: an item imported before its unit
    was marked held out). An extraction a ref names without a block counts
    only when it is held out whole."""

    if held_out.empty:
        return frozenset()
    found: set[str] = set()
    for item in items:
        keys, whole = item_source_keys(item)
        if any(held_out.covers(*key) for key in keys) or any(held_out.covers(extraction) for extraction in whole):
            found.add(str(item.id))
    return frozenset(found)


def held_out_items(vault: Any, repository: Any) -> frozenset[str]:
    """The vault's practice items made from held-out material (:func:`held_out_material`)."""

    items = list(getattr(vault, "practice_items", {}).values())
    if not items:
        return frozenset()
    return held_out_item_ids(items, held_out_material(vault, repository))


def held_out_selection_active(vault: Any) -> bool:
    """``goals.held_out_selection``: the kill switch of the serving rules (Codex
    review F6). On (the default): material the learner has been shown never
    becomes an exam item, a certification cold probe or a cold retry; an exam
    item shown after its reservation is withdrawn before the exam starts; an
    item made from held-out material stays out of routine practice. Off, each
    selection is the predecessor's. Live at every version: replay never reads
    it. The model-context protections are not switched."""

    goals = getattr(getattr(vault, "config", None), "goals", None)
    return bool(getattr(goals, "held_out_selection", True))


#: Why an item is made from held-out material (:func:`exposed_items`).
HELD_OUT_MATERIAL = "held_out_material"


def exposed_items(vault: Any, repository: Any, items: Iterable[Any], *,
                  with_held_out: bool = False) -> dict[str, list[str]]:
    """``{item id: reasons}`` for the items among ``items`` that are no longer
    an independent check: the learner has been shown their own material
    (``db.stores.source_service.shown_items``: ``revealed``,
    ``source_exposed``, ``seen_in_proposal``) and, with ``with_held_out``,
    items made from held-out material (``held_out_material``: a cold probe or
    a cold retry would put an exam question in front of the learner).

    The serving rules' one reader of shown material: the exam pool, the exam's
    start, the certification cold probe and the cold retry. Empty with
    ``goals.held_out_selection`` off (each selection is then the
    predecessor's)."""

    items = list(items)
    if not items or not held_out_selection_active(vault):
        return {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = {item_id: list(reasons) for item_id, reasons in shown_items(connection, items).items()}
    if with_held_out:
        for item_id in held_out_item_ids(items, held_out_material(vault, repository)):
            found.setdefault(item_id, []).append(HELD_OUT_MATERIAL)
    return {item_id: sorted(reasons) for item_id, reasons in sorted(found.items())}


#: What a learner is told when a pick or a serve reaches an item made from held-out material.
HELD_OUT_ITEM_REFUSAL = ("that item was made from material held out for evaluation (an exam you'll sit later), so "
                         "it isn't practised: that keeps the exam a fair test")


def item_exam_status(item: Any, *, material: ExamMaterial | None = None,
                     reserved: Iterable[str] = ()) -> ItemExamStatus | None:
    """Whether a practice item is exam material, or None.

    ``reserved`` is the set of items reserved for a goal's held-out exam
    (``repository.reserved_exam_pool_item_ids()``); ``material`` the vault's
    exam material (:func:`exam_material`), when the item's own source should
    be judged too."""

    reasons: list[str] = []
    if item.id in set(reserved):
        reasons.append(EXAM_RESERVED)
    held_out = False
    found: list[SpanKey] = []
    if material is not None:
        keys, whole = item_source_keys(item)
        found = sorted(key for key in keys if material.covers(*key))
        found += [(extraction_id, "") for extraction_id in sorted(whole) if material.covers(extraction_id)]
        if found:
            reasons.append("exam_material")
            held_out = any(material.is_held_out(key[0], key[1] or None) for key in found)
    if not reasons:
        return None
    return ItemExamStatus(practice_item_id=str(item.id), reasons=tuple(reasons), held_out=held_out,
                          spans=tuple(found))


def exam_reserved(repository: Any, item_id: str | None) -> bool:
    """Whether the item is reserved for a goal's held-out exam (an unreleased exam-pool row)."""

    if not item_id:
        return False
    return str(item_id) in set(repository.reserved_exam_pool_item_ids())


__all__ = [
    "AMBIGUOUS_MARK",
    "AMBIGUOUS_SCOPE",
    "AMBIGUOUS_SELECTION",
    "EXAM_MEMBER",
    "EXAM_RESERVED",
    "EXAM_ROLE",
    "EXAM_SOURCE",
    "EXAM_UNIT",
    "ExamMaterial",
    "ExamVerdict",
    "HELD_OUT_EVALUATION",
    "HELD_BACK_REFUSAL",
    "HELD_OUT_ITEM_REFUSAL",
    "HELD_OUT_MATERIAL",
    "HELD_OUT_REFUSAL",
    "HELD_OUT_SIGNAL",
    "HELD_OUT_UNIT",
    "HeldOutSpan",
    "ItemExamStatus",
    "MARKS_MADE_ON_KEY",
    "Material",
    "PROTECTION_MARK_KEY",
    "SourceMarks",
    "UNMARKED_READING",
    "UNRESOLVED_UNIT",
    "descendants",
    "exam_material",
    "exam_reserved",
    "exam_withheld",
    "exposed_items",
    "held_out_among",
    "held_out_item_ids",
    "held_out_items",
    "held_out_material",
    "held_out_partition",
    "held_out_refusal",
    "held_out_selection_active",
    "held_out_spans",
    "is_exam_role",
    "item_exam_status",
    "item_source_keys",
    "marks_made_on",
    "protected_spans_by_reading",
    "raw_roots",
    "reading_held_back",
    "role_material",
    "scope_reading_of",
    "selection_marks_exact",
    "source_marks",
    "source_ref_keys",
    "source_ref_protected",
]
