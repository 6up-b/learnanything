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
   textbook chapter overridden to exam). A scope names unit ids of the
   reading it was made on, and unit ids are positional: a re-read of the
   pinned revision may reuse ``u1`` for another unit (re-read safety, Codex
   review F1). A scope does not record its reading, so every completed
   top-level reading of the pinned revision is a possible origin, and each
   interpretation is withheld (over-protective, never released): in each
   origin the scope is resolved by unit id with every nested unit (a merged
   unit is its members; a split child is the blocks under its own heading
   where that extraction's boundary overrides define it, else its whole raw
   parent), and every other origin's interpretation is carried onto it
   through the alias authority's verified carry (the same words wherever the
   re-read put them, never a matching label: Codex re-review F1; one that
   can't be verified withholds the whole reading); in every other extraction
   of the source (another revision, a page repair) by the labels the
   interpretations resolve to (a split child by its raw parent's label). A
   unit that does not resolve in an extraction makes that whole extraction
   exam material (fail closed).
3. *A held-out unit, whatever its role.* Every unit marked
   ``held_out_evaluation`` in any unit selection of the source (in a source
   set or not, whatever role its member has; owner, 2026-10-13). A mark is a
   restriction on the source, so every extraction carries every mark (Codex
   review F2): its own by unit id, another reading of its revision's through
   the verified carry (Codex re-review F1), any other extraction's by label.
   A split child withholds its whole raw parent and a merged unit its
   members; a carry that can't be verified or a label that does not resolve
   withholds the whole extraction, and a mark that resolves nowhere
   withholds every extraction of its source (fail closed).

The **held-out partition** (§8.5: what the leakage gate fingerprints and an
import or a generated item must never reproduce) is rule 3 plus the held-out
assessment signals of exam units (an exam unit's inventory signals marked
``held_out``, on the reading the inventory was made on, and carried to every
other reading of its revision through the one alias authority's verified
carry, every block that may hold the signal's words; a signal whose words
can't be followed there withholds that whole reading: Codex review F2,
re-review F2):
:func:`held_out_partition`. It is the one held-out predicate (Codex review
F3): :attr:`ExamMaterial.held_out`, the Reader's refusals
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
#: A held-out signal span with no alias on another reading of its revision.
UNRESOLVED_SIGNAL = "unresolved_signal"
EXAM_RESERVED = "exam_reserved"
EXAM_SOURCE = "exam_source"

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
        self._pinned: dict[str, str | None] = {}
        self._readings: dict[str, list[str]] = {}
        self._selections: dict[str, Mapping[str, Any]] = {}
        self._effective: dict[str, Mapping[str, tuple[str, ...]] | None] = {}
        self._reading_revision: dict[str, str | None] = {}
        self._carrier: Any = None

    def reading_revision(self, extraction_id: str) -> str | None:
        """The revision of a completed top-level reading (None for anything else:
        a page repair, a run not completed)."""

        if extraction_id not in self._reading_revision:
            row = self.connection.execute(
                "SELECT revision_id FROM source_extraction_runs WHERE id = ? AND status = 'completed' "
                "AND parent_extraction_id IS NULL", (str(extraction_id),)).fetchone()
            self._reading_revision[extraction_id] = None if row is None or row[0] is None else str(row[0])
        return self._reading_revision[extraction_id]

    def carry_into(self, protected: Mapping[str, Iterable[str]], to_extraction_id: str) -> set[str] | None:
        """``protected`` (``{reading: its spans}``, other readings of the
        revision) onto ``to_extraction_id`` through the alias authority's
        verified carry (``span_aliases.SpanCarrier``: every block that may hold
        the same words, never a matching label; Codex re-review F1, F2).
        ``None`` when one of them can't be verified there."""

        if self._carrier is None:
            from learnloop.content.sources.span_aliases import SpanCarrier

            self._carrier = SpanCarrier(self.repository)
        landed: set[str] = set()
        for origin, spans in protected.items():
            if origin == to_extraction_id:
                landed.update(spans)
                continue
            carried = self._carrier.carry(origin, spans, to_extraction_id)
            if carried is None:
                return None
            landed |= carried
        return landed

    def units(self, extraction_id: str) -> list[UnitRow]:
        if extraction_id not in self._units:
            self._units[extraction_id] = extraction_units(self.connection, extraction_id)
        return self._units[extraction_id]

    def source_extractions(self, source_id: str | None, revision_id: str | None) -> list[str]:
        key = (str(source_id or ""), str(revision_id or ""))
        if key not in self._extractions:
            found = (source_extraction_ids(self.connection, source_id=source_id) if source_id else []) + (
                source_extraction_ids(self.connection, revision_id=revision_id) if revision_id else [])
            self._extractions[key] = list(dict.fromkeys(found))
        return self._extractions[key]

    def readings(self, revision_id: str | None) -> list[str]:
        """The revision's completed top-level readings, oldest first: what a
        scope's unit ids may name (re-read safety, Codex review F1)."""

        if not revision_id:
            return []
        if revision_id not in self._readings:
            self._readings[revision_id] = [str(row[0]) for row in self.connection.execute(
                "SELECT id FROM source_extraction_runs WHERE revision_id = ? AND status = 'completed' "
                "AND parent_extraction_id IS NULL ORDER BY created_at, id", (str(revision_id),))]
        return self._readings[revision_id]

    def origins(self, revision_id: str | None) -> list[str]:
        """Every reading a member's scope may have been made on: each completed
        top-level reading of its pinned revision, else the pinned extraction."""

        found = self.readings(revision_id)
        if found:
            return found
        pinned = self.pinned(revision_id)
        return [pinned] if pinned else []

    def pinned(self, revision_id: str | None) -> str | None:
        """The member revision's extraction (its latest completed top-level run)."""

        if not revision_id:
            return None
        if revision_id not in self._pinned:
            from learnloop.content.sources.source_outline import resolve_extraction_id

            self._pinned[revision_id] = resolve_extraction_id(self.repository, str(revision_id))
        return self._pinned[revision_id]

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
    """The scope resolved by unit id in one reading it may have been made on:
    ``(its spans there, the labels of its raw units)``, or None when a unit
    id does not resolve there."""

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


def _member_units(reader: _Reader, member: Any, narrowing: set[str], acc: _Acc, reason: str) -> None:
    """Resolve a member's narrowing units; fail closed per extraction.

    The scope's unit ids name units of the reading it was made on, which the
    scope does not record: every completed top-level reading of the pinned
    revision is a possible origin (a re-read may reuse ``u1`` for another
    unit; Codex review F1). Each interpretation is withheld. In each origin:
    its own by unit id, and every other origin's carried onto it through the
    alias authority's verified carry (the same words, wherever the re-read put
    them; a matching label is not the same material: Codex re-review F1), the
    whole reading when one can't be verified there. In every other extraction
    of the source (another revision, a page repair) by the labels the
    interpretations resolve to."""

    extraction_ids = reader.source_extractions(member.source_id, member.revision_id)
    pinned_revision = str(member.revision_id or "") or None
    origins = reader.origins(member.revision_id)
    resolved = {origin: _origin_units(reader, origin, narrowing) for origin in origins}
    found = {origin: hit for origin, hit in resolved.items() if hit is not None}
    all_labels = set().union(*(hit[1] for hit in found.values())) if found else set()
    interpretations = {origin: hit[0] for origin, hit in found.items()}
    for extraction_id in dict.fromkeys([*extraction_ids, *origins]):
        # No origin resolves every unit id (nothing names the scope's units
        # at all), or this origin doesn't: fail closed.
        if not found or (extraction_id in resolved and resolved[extraction_id] is None):
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
            continue
        if extraction_id in resolved:
            spans = reader.carry_into(interpretations, extraction_id)
            if spans is None:
                acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
            else:
                acc.add_spans(extraction_id, spans, reason, pinned_revision)
            continue
        units = reader.units(extraction_id)
        roots = {unit.unit_id for unit in units if unit.label in all_labels}
        if {unit.label for unit in units if unit.unit_id in roots} != all_labels:
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
            continue
        chosen = descendants(units, roots)
        acc.add_spans(extraction_id, (span for unit in units if unit.unit_id in chosen for span in unit.span_ids),
                      reason, pinned_revision)


def _role_material(reader: _Reader, member: Any, withheld_role: Callable[[str | None], bool], acc: _Acc, *,
                   member_reason: str, unit_reason: str) -> None:
    """A member's material whose role ``withheld_role`` names, in EVERY extraction of its source."""

    narrowing = {str(entry.unit_id) for entry in member.scope
                 if entry.role_override and withheld_role(entry.role_override)}
    if withheld_role(member.default_role):
        for extraction_id in reader.source_extractions(member.source_id, member.revision_id):
            acc.add_whole(extraction_id, member_reason, str(member.revision_id or "") or None)
        return
    if narrowing:
        _member_units(reader, member, narrowing, acc, unit_reason)


def _held_out_ids(selection: Mapping[str, Any]) -> list[str]:
    modes = selection.get("exam_use_modes") or {}
    return sorted(str(unit) for unit, mode in modes.items() if mode == HELD_OUT_EVALUATION)


def _held_out_sources(connection: Any) -> dict[tuple[str, str], tuple[str | None, str | None, set[str]]]:
    """Every source with a unit selection that marks a unit held out:
    ``{key: (source id, revision id, the marking extractions)}``. A selection
    whose run names no source is its own group (its extraction still counts)."""

    rows = connection.execute(
        "SELECT s.extraction_id, COALESCE(s.source_id, revision.source_id), run.revision_id "
        "FROM source_unit_selections AS s "
        "LEFT JOIN source_extraction_runs AS run ON run.id = s.extraction_id "
        "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id "
        "WHERE s.exam_use_modes_json LIKE ? ORDER BY s.extraction_id", (f"%{HELD_OUT_EVALUATION}%",)).fetchall()
    found: dict[tuple[str, str], tuple[str | None, str | None, set[str]]] = {}
    for extraction_id, source_id, revision_id in rows:
        source = None if source_id is None else str(source_id)
        revision = None if revision_id is None else str(revision_id)
        key = ("source", source) if source else ("revision", revision) if revision else ("extraction", str(extraction_id))
        found.setdefault(key, (source, revision if not source else None, set()))[2].add(str(extraction_id))
    return found


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


def _label_occurrences(units: Sequence[UnitRow]) -> dict[str, tuple[str, int, str]]:
    """``{unit id: (label, n, content hash)}``: the unit is the n-th (from 0, in
    outline order) of its extraction's units with that label."""

    seen: dict[str, int] = {}
    found: dict[str, tuple[str, int, str]] = {}
    for unit in units:
        index = seen.get(unit.label, 0)
        seen[unit.label] = index + 1
        found[unit.unit_id] = (unit.label, index, unit.semantic_hash)
    return found


def _held_out_units(reader: _Reader, source_id: str | None, revision_id: str | None, marking: Iterable[str],
                    acc: _Acc) -> None:
    """Units marked ``held_out_evaluation`` in a unit selection of a source (any role).

    A mark is a restriction on the SOURCE (Codex review F2 of the stage), so
    every extraction of the source carries every mark, its own and the
    others':

    * its own marks by unit id (a split child withholds its raw parent, a
      merged unit its members);
    * another reading of the same revision's marks (a book read again)
      through the alias authority's verified carry: the marked unit's words,
      wherever the re-read put them (a re-read can keep a unit's heading and
      move its question into another unit: a matching label is not the same
      material, Codex re-review F1); a mark that can't be verified there
      withholds the whole reading;
    * any other extraction's marks (another revision, a page repair) by label
      (unit ids are positional), every unit with that label (labels can
      repeat: "Exercises" under each chapter). The one exception: a mark is
      already carried by an extraction that itself marks the same unit, the
      n-th with that label and the same content hash (the unit marked again
      after a re-extraction);
    * a label that does not resolve withholds the whole extraction; a mark
      that does not resolve at all (its unit, so its label, is unknown)
      withholds EVERY extraction of the source (fail closed).
    """

    extraction_ids = list(dict.fromkeys([*reader.source_extractions(source_id, revision_id), *sorted(marking)]))
    marked: dict[str, set[str]] = {}
    marked_keys: dict[str, set[tuple[str, int, str]]] = {}
    marked_spans: dict[str, set[str]] = {}
    unresolved = False
    for extraction_id in extraction_ids:
        held = _held_out_ids(reader.selection(extraction_id))
        if not held:
            continue
        units = reader.units(extraction_id)
        by_id = {unit.unit_id: unit for unit in units}
        occurrence = _label_occurrences(units)
        roots: set[str] = set()
        for unit_id in held:
            resolved = raw_roots(unit_id, by_id)
            if resolved is None:
                unresolved = True
                continue
            roots |= resolved
        marked[extraction_id] = roots
        marked_keys[extraction_id] = {occurrence[unit_id] for unit_id in roots}
        chosen = descendants(units, roots)
        marked_spans[extraction_id] = {span for unit in units if unit.unit_id in chosen for span in unit.span_ids}
    if unresolved:
        for extraction_id in extraction_ids:
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, None)
        return
    if not marked:
        return
    for extraction_id in extraction_ids:
        units = reader.units(extraction_id)
        revision = reader.reading_revision(extraction_id)
        siblings = {other for other in marked
                    if other != extraction_id and revision is not None and reader.reading_revision(other) == revision}
        carried = reader.carry_into({other: marked_spans[other] for other in sorted(siblings)}, extraction_id)
        if carried is None:
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, None)
            continue
        own_keys = marked_keys.get(extraction_id, set())
        labels = {key[0] for other, keys in marked_keys.items() if other != extraction_id and other not in siblings
                  for key in keys if key not in own_keys}
        by_label = {unit.unit_id for unit in units if unit.label in labels}
        if {unit.label for unit in units if unit.unit_id in by_label} != labels:
            acc.add_whole(extraction_id, UNRESOLVED_UNIT, None)
            continue
        chosen = descendants(units, marked.get(extraction_id, set()) | by_label)
        carried.update(span for unit in units if unit.unit_id in chosen for span in unit.span_ids)
        acc.add_spans(extraction_id, carried, HELD_OUT_UNIT, None)


def _add_held_out(connection: Any, reader: _Reader, held: _Acc) -> None:
    """Rule 3 into ``held``: every held-out unit of every source, from the database alone."""

    for source_id, revision_id, marking in _held_out_sources(connection).values():
        _held_out_units(reader, source_id, revision_id, marking, held)


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
    """Exam material vault-wide (rules 1-3): ``vault`` or its ``source_sets``."""

    acc = _Acc()
    held = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        for source_set in _source_sets(vault_or_sets):
            for member in source_set.members:
                _role_material(reader, member, is_exam_role, acc, member_reason=EXAM_MEMBER, unit_reason=EXAM_UNIT)
        for source_id, revision_id, picked in _outline_exam_sources(connection):
            for extraction_id in dict.fromkeys([*reader.source_extractions(source_id, revision_id), picked]):
                acc.add_whole(extraction_id, EXAM_SOURCE, None)
        _add_held_out(connection, reader, held)
        _add_signals(reader, vault_or_sets, held)
        held_material = Material.from_acc(held)
        material = Material.from_acc(acc).union(held_material)
        runs = _runs(connection, set(material.extractions) | {key[0] for key in material.spans})
    return ExamMaterial(material=material, held_out=held_material, runs=runs)


def role_material(vault_or_sets: Any, repository: Any, withheld_role: Callable[[str | None], bool], *,
                  member_reason: str = "role_member", unit_reason: str = "role_unit") -> Material:
    """Members' material whose role ``withheld_role`` names, by the same
    resolution as exam material (rules 1 and 2), for callers that withhold
    more than exams (``corpus.teaching_exclusions``: problem sets, notes and
    unknown roles)."""

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


# --- the Reader's model contexts ---------------------------------------------------------

#: What a learner is told when a Reader request would show held-out material to a model.
HELD_OUT_REFUSAL = ("This passage is held out for evaluation (an exam you'll sit later), so LearnLoop won't "
                    "explain it or make questions from it: that keeps the exam a fair test.")


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


def _signal_spans(inventory: Mapping[str, Any], *, held_out_only: bool) -> set[str]:
    spans: set[str] = set()
    for signal in inventory.get("assessment_signals", []) or []:
        if held_out_only and not signal.get("held_out"):
            continue
        spans |= {str(span) for span in signal.get("span_ids", []) or [] if span}
    return spans


def _add_signals(reader: _Reader, vault_or_sets: Any, held: _Acc, *,
                 subjects: set[str] | None = None) -> None:
    """The held-out assessment signals of exam units into ``held``: an exam
    unit's inventory signals marked ``held_out`` (every signal of an exam unit
    itself marked held out). ``subjects`` narrows them to those subjects'
    source sets.

    Each inventory names spans of the reading it was made on (its own
    ``extraction_id``), never "the latest reading" (Codex review F2): its
    signals hold there, and on every other completed reading of the revision
    through the one alias authority's verified carry (every block that may
    hold the signal's words: both halves of a split, never only the one an
    approximate alias names; Codex re-review F2). A signal whose words can't
    be followed onto a reading withholds that whole reading (fail closed).
    An inventory's unit is an exam unit when its own
    reading's units say so: the member's exam material (rules 1 and 2, every
    interpretation of its scope) covers it there."""

    repository = reader.repository
    for source_set in _source_sets(vault_or_sets):
        if subjects is not None and source_set.subject_id not in subjects:
            continue
        for member in source_set.members:
            overrides = {str(entry.unit_id): entry.role_override for entry in member.scope if entry.role_override}
            if not is_exam_role(member.default_role) and not any(is_exam_role(role) for role in overrides.values()):
                continue
            pinned_revision = str(member.revision_id or "") or None
            rows = [row for row in repository.unit_inventories_for_revision(member.revision_id)
                    if row.get("inventory") and row.get("extraction_id")]
            if not rows:
                continue
            exam = _Acc()
            _role_material(reader, member, is_exam_role, exam, member_reason=EXAM_MEMBER, unit_reason=EXAM_UNIT)
            readings = reader.origins(member.revision_id)
            for row in rows:
                origin, unit_id = str(row["extraction_id"]), str(row["unit_id"])
                units = reader.units(origin)
                roots = raw_roots(unit_id, {unit.unit_id: unit for unit in units})
                chosen = descendants(units, roots or set())
                unit_spans = {span for unit in units if unit.unit_id in chosen for span in unit.span_ids}
                # An exam unit on its own reading (a unit no longer found there
                # counts: fail closed).
                if roots is not None and origin not in exam.whole and not any(
                        (origin, span) in exam.spans for span in unit_spans):
                    continue
                modes = reader.selection(origin).get("exam_use_modes") or {}
                spans = _signal_spans(row["inventory"], held_out_only=modes.get(unit_id) != HELD_OUT_EVALUATION)
                if not spans:
                    continue
                held.add_spans(origin, spans, HELD_OUT_SIGNAL, pinned_revision)
                for reading in readings:
                    if reading == origin:
                        continue
                    landed = reader.carry_into({origin: spans}, reading)
                    if landed is None:
                        held.add_whole(reading, UNRESOLVED_SIGNAL, pinned_revision)
                        continue
                    held.add_spans(reading, landed, HELD_OUT_SIGNAL, pinned_revision)


def held_out_partition(vault_or_sets: Any, repository: Any, *,
                       subject_ids: Iterable[str] | None = None) -> Material:
    """The held-out partition: every held-out unit (rule 3, any role, every
    extraction, fail closed) plus the held-out assessment signals of exam units
    (resolved in the member's pinned extraction). The one held-out predicate:
    the leakage gate fingerprints it, the Reader refuses it
    (:func:`held_out_material`) and :attr:`ExamMaterial.held_out` is it.

    ``subject_ids`` narrows the exam units' signals to those subjects' source
    sets; held-out units count wherever they sit."""

    subjects = None if subject_ids is None else {str(value) for value in subject_ids}
    held = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        _add_held_out(connection, reader, held)
        _add_signals(reader, vault_or_sets, held, subjects=subjects)
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
    "EXAM_MEMBER",
    "EXAM_RESERVED",
    "EXAM_ROLE",
    "EXAM_SOURCE",
    "EXAM_UNIT",
    "ExamMaterial",
    "ExamVerdict",
    "HELD_OUT_EVALUATION",
    "HELD_OUT_ITEM_REFUSAL",
    "HELD_OUT_MATERIAL",
    "HELD_OUT_REFUSAL",
    "HELD_OUT_SIGNAL",
    "HELD_OUT_UNIT",
    "HeldOutSpan",
    "ItemExamStatus",
    "Material",
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
    "held_out_selection_active",
    "held_out_spans",
    "is_exam_role",
    "item_exam_status",
    "item_source_keys",
    "raw_roots",
    "role_material",
    "source_ref_keys",
    "source_ref_protected",
]
