"""Which source text a search covers: current extractions, scopes and exclusions.

A *scope* names the extractions a search reads and the spans it must never
return. The library scope is today's (every reader-enabled source, nothing
excluded). The teaching scope, used for the tutor's grounding, is the subject's
sources minus everything without teaching authority: source-set material whose
role lacks ``semantic_contract`` authority (exam, problem set, notes, unknown;
whole members or unit overrides, in every extraction of the source) and spans
linked by ``exercise`` or ``assessment_alignment`` provenance. Assessment lanes
never enter a teaching context (ING M8 §9.1). In an item-bound context
(practice, feedback) exercise and solution blocks are dropped as well.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.sources.role_authority import role_authority
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    AssessmentLink,
    UnitRow,
    assessment_link_locators,
    extraction_units,
    role_hint_spans,
    source_extraction_ids,
)
from learnloop.ingest.locators import parse_block_span
from learnloop.vault.models import LoadedVault, learning_object_facet_union


@dataclass(frozen=True)
class SourceExtraction:
    source_id: str
    extraction_id: str
    title: str
    reader_enabled: bool


@dataclass(frozen=True)
class Scope:
    name: str
    extractions: Mapping[str, SourceExtraction]
    excluded: frozenset[tuple[str, str]] = frozenset()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def allows(self, extraction_id: str, span_id: str) -> bool:
        return extraction_id in self.extractions and (extraction_id, span_id) not in self.excluded

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "sources": len(self.extractions),
                "excluded_spans": len(self.excluded), "notes": list(self.notes)}


def _title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str:
    """The library's display title (the same order the reader search uses)."""

    return str(
        artifact.get("display_title")
        or (revision or {}).get("original_uri")
        or artifact.get("canonical_uri")
        or artifact.get("id")
    )


def current_extractions(repository: Repository) -> dict[str, SourceExtraction]:
    """Every source artifact's current extraction, keyed by extraction id."""

    found: dict[str, SourceExtraction] = {}
    for artifact in repository.all_source_artifacts():
        source_id = str(artifact["id"])
        extraction_id = resolve_extraction_id(repository, source_id)
        if extraction_id is None:
            continue
        run = repository.get_extraction_run(extraction_id) or {}
        revision = repository.get_source_revision(str(run.get("revision_id") or ""))
        found[extraction_id] = SourceExtraction(
            source_id=source_id, extraction_id=extraction_id,
            title=_title(artifact, revision),
            reader_enabled=bool(artifact.get("reader_enabled", 1)),
        )
    return found


def library_scope(repository: Repository) -> Scope:
    """Today's library search scope: every reader-enabled source, nothing excluded."""

    extractions = {key: value for key, value in current_extractions(repository).items()
                   if value.reader_enabled}
    return Scope("library", extractions)


def extraction_scope(repository: Repository, extraction_id: str) -> Scope:
    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    source_id = str(revision.get("source_id") or "")
    artifact = repository.get_source_artifact(source_id) or {"id": source_id}
    return Scope("extraction", {extraction_id: SourceExtraction(
        source_id=source_id, extraction_id=extraction_id, title=_title(artifact, revision),
        reader_enabled=bool(artifact.get("reader_enabled", 1)))})


def _subjects(vault: LoadedVault, learning_object_ids: Iterable[str]) -> set[str]:
    subjects: set[str] = set()
    for lo_id in learning_object_ids:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is not None:
            subjects.update(learning_object.subjects)
    return subjects


def _linked_extractions(vault: LoadedVault, repository: Repository,
                        learning_object_ids: Iterable[str]) -> set[str]:
    """Extractions the LOs' (and their facets') teaching provenance cites."""

    found: set[str] = set()
    for lo_id in learning_object_ids:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is None:
            continue
        entities = [("learning_object", lo_id)] + [
            ("facet", vault.canonical_facet_id(str(facet_id)))
            for facet_id in learning_object_facet_union(learning_object)
        ]
        for entity_type, entity_id in entities:
            for link in repository.entity_source_links(entity_type, entity_id):
                if link.get("relation") in ("primary", "support", "alternate") and link.get("extraction_id") \
                        and link.get("status") in (None, "current"):
                    found.add(str(link["extraction_id"]))
    return found


#: In an item-bound tutor context (practice, feedback) these block roles are
#: never grounding: an exercise statement, or a solution (its lead block and
#: the body that follows it), may be the item's own worked answer.
ITEM_BOUND_EXCLUDED_ROLE_HINTS = ("exercise", "solution")
_REGION_ROLE_HINTS = ("solution",)


@dataclass(frozen=True)
class Exclusions:
    """What a teaching context never reads: whole extractions and single spans."""

    extractions: frozenset[str] = frozenset()
    spans: frozenset[tuple[str, str]] = frozenset()


def _teaches(role: str | None) -> bool:
    """A role whose sources may ground teaching: ``semantic_contract`` authority.

    ``exam``, ``problem_set``, ``notes`` and every unknown role fail closed
    (spec_source_ingestion_v2 §4.2), so the tutor reads only what the old
    semantic-authority links could cite.
    """

    return role_authority(role).semantic_contract


def _descendants(units: Sequence[UnitRow], roots: set[str]) -> set[str]:
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


def _member_exclusions(connection, repository: Repository, member: Any,
                       whole: set[str], spans: set[tuple[str, str]]) -> None:
    """A source-set member's non-teaching material, in EVERY extraction of its source.

    Resolved by ``source_id`` (all revisions, all runs), so a re-import whose
    set still pins the old revision is excluded too. A member whose default role
    does not teach is excluded whole. A unit override that does not teach is
    resolved per extraction: by unit id in the pinned extraction, by the pinned
    unit's label elsewhere (unit ids are positional); an override that cannot be
    resolved in some extraction excludes that whole extraction (fail closed).
    """

    narrowing = {scope.unit_id for scope in member.scope
                 if scope.role_override and not _teaches(scope.role_override)}
    default_teaches = _teaches(member.default_role)
    if default_teaches and not narrowing:
        return
    extraction_ids = list(dict.fromkeys(
        source_extraction_ids(connection, source_id=member.source_id)
        + source_extraction_ids(connection, revision_id=member.revision_id)))
    if not default_teaches:
        whole.update(extraction_ids)
        return
    pinned = resolve_extraction_id(repository, member.revision_id)
    pinned_units = {unit.unit_id: unit for unit in extraction_units(connection, pinned)} if pinned else {}
    labels = {pinned_units[unit_id].label for unit_id in narrowing if unit_id in pinned_units}
    for extraction_id in extraction_ids:
        units = extraction_units(connection, extraction_id)
        if extraction_id == pinned:
            roots = {unit.unit_id for unit in units if unit.unit_id in narrowing}
            resolved = roots == narrowing
        else:
            roots = {unit.unit_id for unit in units if unit.label in labels}
            resolved = len(labels) == len(narrowing) and {unit.label for unit in units if unit.unit_id in roots} == labels
        if not resolved:
            whole.add(extraction_id)
            continue
        chosen = _descendants(units, roots)
        spans.update((extraction_id, span_id) for unit in units if unit.unit_id in chosen
                     for span_id in unit.span_ids)


def _link_exclusions(connection, link: AssessmentLink,
                     whole: set[str], spans: set[tuple[str, str]]) -> None:
    """An ``exercise`` / ``assessment_alignment`` link's span, else its whole extraction.

    A ``block_span_v1`` locator names one block, and so does the malformed
    early-v2 ``span:<span>`` form with the link's extraction. A heading path,
    time range, arXiv label or unknown locator is not resolved to blocks here,
    so the extraction it points into is excluded whole (fail closed); a link
    without an extraction falls back to its revision's or source's extractions.
    """

    locator = link.locator.strip()
    parsed = parse_block_span(locator)
    if parsed is not None:
        spans.add((parsed[0], parsed[1]))
        return
    if link.extraction_id and locator.startswith("span:") and "/" not in locator and len(locator) > 5:
        spans.add((link.extraction_id, locator[len("span:"):]))
        return
    if link.extraction_id:
        whole.add(link.extraction_id)
    elif link.revision_id:
        whole.update(source_extraction_ids(connection, revision_id=link.revision_id))
    elif link.source_id:
        whole.update(source_extraction_ids(connection, source_id=link.source_id))


def teaching_exclusions(vault: LoadedVault, repository: Repository) -> Exclusions:
    """Everything a teaching context never reads, vault-wide.

    Source-set material without teaching authority (exam, problem_set, notes and
    unknown roles, whole members or unit overrides, which covers held-out exam
    questions and whole ``held_out_evaluation`` units), in every extraction of
    its source, plus every span an ``exercise`` or ``assessment_alignment`` link
    cites (or, for a locator that does not name a block, its whole extraction).
    """

    whole: set[str] = set()
    spans: set[tuple[str, str]] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for source_set in vault.source_sets:
            for member in source_set.members:
                _member_exclusions(connection, repository, member, whole, spans)
        for link in assessment_link_locators(connection):
            _link_exclusions(connection, link, whole, spans)
    return Exclusions(frozenset(whole), frozenset(spans))


def assessment_spans(vault: LoadedVault, repository: Repository) -> frozenset[tuple[str, str]]:
    """The span-level part of :func:`teaching_exclusions` (whole extractions aside)."""

    return teaching_exclusions(vault, repository).spans


def teaching_scope(vault: LoadedVault, repository: Repository,
                   learning_object_ids: Iterable[str], *, item_bound: bool = False) -> Scope:
    """The tutor's grounding scope: the LOs' subjects' teaching sources.

    Sources come from the subjects' source sets plus any source the LOs'
    teaching provenance cites. With no LO, or no source found for them, every
    current source is searched. Either way :func:`teaching_exclusions` applies
    (whole extractions leave the scope), and an ``item_bound`` context
    (practice, feedback) also drops exercise and solution blocks, since one of
    them may be the item's own worked answer.
    """

    lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
    every = current_extractions(repository)
    subjects = _subjects(vault, lo_ids)
    chosen: set[str] = set()
    for source_set in vault.source_sets:
        if source_set.subject_id not in subjects:
            continue
        for member in source_set.members:
            extraction_id = resolve_extraction_id(repository, member.revision_id)
            if extraction_id is not None:
                chosen.add(extraction_id)
    chosen |= _linked_extractions(vault, repository, lo_ids)
    notes: list[str] = []
    extractions = {key: value for key, value in every.items() if key in chosen}
    for extraction_id in sorted(chosen - set(extractions)):
        # A source-set member or link may name a revision that is not the
        # source's current one; its own extraction is still searchable.
        extractions[extraction_id] = extraction_scope(repository, extraction_id).extractions[extraction_id]
    if not extractions:
        extractions = dict(every)
        notes.append("no source is linked to these learning objects; every source is searched")
    exclusions = teaching_exclusions(vault, repository)
    dropped = sorted(set(extractions) & exclusions.extractions)
    for extraction_id in dropped:
        del extractions[extraction_id]
    if dropped:
        notes.append(f"{len(dropped)} source extraction(s) without teaching authority excluded")
    excluded = set(exclusions.spans)
    if item_bound and extractions:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            excluded |= role_hint_spans(connection, extractions, ITEM_BOUND_EXCLUDED_ROLE_HINTS,
                                        region_hints=_REGION_ROLE_HINTS)
    return Scope("teaching", extractions, frozenset(excluded), tuple(notes))


__all__ = [
    "Exclusions",
    "ITEM_BOUND_EXCLUDED_ROLE_HINTS",
    "Scope",
    "SourceExtraction",
    "assessment_spans",
    "current_extractions",
    "extraction_scope",
    "library_scope",
    "teaching_exclusions",
    "teaching_scope",
]
