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
   textbook chapter overridden to exam). In the member's pinned extraction it
   is resolved by unit id with every nested unit (a merged unit is its
   members; a split child is the blocks under its own heading where that
   extraction's boundary overrides define it, else its whole raw parent); in
   every other extraction of the source by the pinned unit's label (unit ids
   are positional; a split child by its raw parent's label). A unit that does
   not resolve in an extraction makes that whole extraction exam material
   (fail closed).
3. *A held-out unit, whatever its role.* Every unit marked
   ``held_out_evaluation`` in any unit selection of the source (in a source
   set or not, whatever role its member has; owner, 2026-10-13): by id in the
   extraction whose selection marks it, by label in every other extraction of
   the source. A split child withholds its whole raw parent and a merged unit
   its members; an id or label that does not resolve withholds the whole
   extraction (fail closed).

The **held-out partition** (§8.5: what the leakage gate fingerprints and an
import or a generated item must never reproduce) is rule 3 plus the held-out
assessment signals of exam units (an exam unit's inventory signals marked
``held_out``, resolved in the member's pinned extraction):
:func:`held_out_partition`.

**Revisions.** A verdict names the revision of the extraction the span lies in
and the pinned revisions of the members that made it exam material
(:class:`ExamVerdict`); every revision of an exam source counts, not only the
pinned one.

**Items** (:func:`item_exam_status`): an item reserved for a goal's held-out
exam is exam material, and so is an item whose own source (its canonical
exercise region, its block-level source refs) is.

What a caller does with the answer is its own: teaching contexts and model
readers withhold exam material under every policy, the leakage gate
fingerprints the held-out partition, an import refuses exam material, and the
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
        self._selections: dict[str, Mapping[str, Any]] = {}
        self._effective: dict[str, Mapping[str, tuple[str, ...]] | None] = {}

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


def _member_units(reader: _Reader, member: Any, narrowing: set[str], acc: _Acc, reason: str) -> None:
    """Resolve a member's narrowing units (by id in its pinned extraction, by
    label in every other extraction of its source); fail closed per extraction."""

    extraction_ids = reader.source_extractions(member.source_id, member.revision_id)
    pinned = reader.pinned(member.revision_id)
    pinned_revision = str(member.revision_id or "") or None
    pinned_units = {unit.unit_id: unit for unit in reader.units(pinned)} if pinned else {}
    roots_of = {unit_id: raw_roots(unit_id, pinned_units) for unit_id in narrowing}
    resolved_in_pinned = all(roots is not None for roots in roots_of.values())
    labels = {pinned_units[root].label for roots in roots_of.values() if roots for root in roots}
    for extraction_id in extraction_ids:
        units = reader.units(extraction_id)
        if extraction_id == pinned:
            if not resolved_in_pinned:
                acc.add_whole(extraction_id, UNRESOLVED_UNIT, pinned_revision)
                continue
            effective = reader.effective_spans(extraction_id) if any("#" in unit_id for unit_id in narrowing) \
                else None
            spans: set[str] = set()
            for unit_id, roots in roots_of.items():
                own = effective.get(unit_id) if effective is not None and "#" in unit_id else None
                if own is not None:
                    spans.update(own)  # a split child: the blocks under its own heading
                    continue
                chosen = descendants(units, set(roots or ()))
                spans.update(span for unit in units if unit.unit_id in chosen for span in unit.span_ids)
            acc.add_spans(extraction_id, spans, reason, pinned_revision)
            continue
        roots = {unit.unit_id for unit in units if unit.label in labels}
        if not resolved_in_pinned or {unit.label for unit in units if unit.unit_id in roots} != labels:
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


def _held_out_units(reader: _Reader, source_id: str | None, revision_id: str | None, marking: Iterable[str],
                    acc: _Acc) -> None:
    """Units marked ``held_out_evaluation`` in a unit selection of a source (any role).

    By id in the extraction whose selection marks it, by its label elsewhere
    (unit ids are positional); a split child withholds its raw parent; an id or
    label that does not resolve withholds the whole extraction (fail closed).
    """

    extraction_ids = list(dict.fromkeys([*reader.source_extractions(source_id, revision_id), *sorted(marking)]))
    marked: dict[str, set[str]] = {}
    unresolved: set[str] = set()
    labels: set[str] = set()
    for extraction_id in extraction_ids:
        held = _held_out_ids(reader.selection(extraction_id))
        if not held:
            continue
        units = reader.units(extraction_id)
        by_id = {unit.unit_id: unit for unit in units}
        roots: set[str] = set()
        for unit_id in held:
            resolved = raw_roots(unit_id, by_id)
            if resolved is None:
                unresolved.add(extraction_id)
                break
            roots |= resolved
        else:
            marked[extraction_id] = roots
            labels |= {by_id[unit_id].label for unit_id in roots}
    for extraction_id in sorted(unresolved):
        acc.add_whole(extraction_id, UNRESOLVED_UNIT, None)
    if not marked:
        return
    for extraction_id in extraction_ids:
        if extraction_id in unresolved:
            continue
        units = reader.units(extraction_id)
        if extraction_id in marked:
            roots = set(marked[extraction_id])
        else:
            roots = {unit.unit_id for unit in units if unit.label in labels}
            if {unit.label for unit in units if unit.unit_id in roots} != labels:
                acc.add_whole(extraction_id, UNRESOLVED_UNIT, None)
                continue
        chosen = descendants(units, roots)
        acc.add_spans(extraction_id, (span for unit in units if unit.unit_id in chosen for span in unit.span_ids),
                      HELD_OUT_UNIT, None)


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
        for source_id, revision_id, marking in _held_out_sources(connection).values():
            _held_out_units(reader, source_id, revision_id, marking, held)
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


def held_out_partition(vault_or_sets: Any, repository: Any, *,
                       subject_ids: Iterable[str] | None = None) -> Material:
    """The held-out partition: every held-out unit (rule 3, any role, every
    extraction, fail closed) plus the held-out assessment signals of exam units
    (resolved in the member's pinned extraction).

    ``subject_ids`` narrows the exam units' signals to those subjects' source
    sets; held-out units count wherever they sit."""

    subjects = None if subject_ids is None else {str(value) for value in subject_ids}
    held = _Acc()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        reader = _Reader(connection, repository)
        for source_id, revision_id, marking in _held_out_sources(connection).values():
            _held_out_units(reader, source_id, revision_id, marking, held)
        for source_set in _source_sets(vault_or_sets):
            if subjects is not None and source_set.subject_id not in subjects:
                continue
            for member in source_set.members:
                overrides = {str(entry.unit_id): entry.role_override for entry in member.scope if entry.role_override}
                if not is_exam_role(member.default_role) and not any(is_exam_role(role) for role in overrides.values()):
                    continue
                pinned = reader.pinned(member.revision_id)
                if pinned is None:
                    continue
                scope_units = [str(entry.unit_id) for entry in member.scope] or [
                    unit.unit_id for unit in reader.units(pinned)]
                inventories = {str(row["unit_id"]): row["inventory"]
                               for row in repository.unit_inventories_for_revision(member.revision_id)
                               if row.get("inventory")}
                modes = reader.selection(pinned).get("exam_use_modes") or {}
                for unit_id in scope_units:
                    if not is_exam_role(overrides.get(unit_id, member.default_role)):
                        continue
                    inventory = inventories.get(unit_id)
                    if inventory:
                        held.add_spans(pinned, _signal_spans(inventory, held_out_only=modes.get(unit_id)
                                                             != HELD_OUT_EVALUATION),
                                       HELD_OUT_SIGNAL, str(member.revision_id or "") or None)
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


def item_source_keys(item: Any) -> tuple[set[SpanKey], set[str]]:
    """The item's own source: ``(block keys, whole extractions)`` its canonical
    exercise and its provenance source refs name."""

    keys: set[SpanKey] = set()
    whole: set[str] = set()
    exercise = getattr(item, "canonical_exercise", None)
    if exercise is not None and getattr(exercise, "extraction_id", None):
        keys |= {(str(exercise.extraction_id), str(span)) for span in exercise.span_ids or ()}
    provenance = getattr(item, "provenance", None)
    for ref in getattr(provenance, "source_refs", None) or ():
        extraction_id = getattr(ref, "extraction_id", None)
        spans = [str(span) for span in getattr(ref, "span_ids", None) or () if span]
        parsed = _parse_block_span(getattr(ref, "locator", None) or "")
        if parsed is not None:
            keys.add(parsed)
        for span in spans:
            if extraction_id and span.startswith((f"{extraction_id}/", f"{extraction_id}:")):
                keys.add((str(extraction_id), span[len(extraction_id) + 1:]))
            elif "/" in span:
                head, _, tail = span.partition("/")
                keys.add((head, tail))
            elif extraction_id:
                keys.add((str(extraction_id), span))
        if extraction_id and not spans and parsed is None:
            whole.add(str(extraction_id))
    return keys, whole


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
    "held_out_partition",
    "held_out_spans",
    "is_exam_role",
    "item_exam_status",
    "item_source_keys",
    "raw_roots",
    "role_material",
]
