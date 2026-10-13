"""Which source text a search covers: current extractions, scopes and exclusions.

A *scope* names the extractions a search reads and the spans it must never
return. The library scope is today's (every reader-enabled source, nothing
excluded). The teaching scope, used for the tutor's grounding, is the subject's
sources minus everything without teaching authority: source-set material whose
role lacks ``semantic_contract`` authority (exam, problem set, notes, unknown;
whole members or unit overrides, in every extraction of the source) and spans
linked by ``exercise`` or ``assessment_alignment`` provenance. Assessment lanes
never enter a teaching context (ING M8 §9.1). A source with no role (in no
source set, cited by no teaching link) fails closed like an unknown role. In an
item-bound context (practice, feedback) the item's own linked passages, and
exercise and solution blocks, are dropped as well.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import json
from typing import Any

from learnloop.content.sources.role_authority import role_authority
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    REGION_BODY_HINTS,
    AssessmentLink,
    HintRow,
    UnitRow,
    assessment_link_locators,
    block_content_hashes,
    entity_link_locators,
    extraction_hint_rows,
    extraction_source_ids,
    extraction_units,
    hinted_extraction_ids,
    lead_regions,
    revision_source_ids,
    section_header_titles,
    source_extraction_ids,
    spans_with_content_hashes,
    teaching_link_locators,
)
from learnloop.ingest.block_roles import lead_role, unit_heading_role
from learnloop.ingest.locators import parse_block_span
from learnloop.vault.models import LoadedVault, PracticeItem, learning_object_facet_union


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
#: the body that follows it), may be the item's own worked answer. Worked
#: examples are not dropped wholesale: the one the item was made from is
#: linked to it (dropped below, with its body), and any other is the tutor's
#: best scaffold; the answer-overlap filter and the verifier still apply.
ITEM_BOUND_EXCLUDED_ROLE_HINTS = ("exercise", "solution")
_REGION_ROLE_HINTS = ("solution",)
#: An item-linked block that leads one of these takes the body after it.
_ITEM_LEAD_REGION_HINTS = ("worked_example", "exercise", "solution")
#: Hints a heading cue can assign to every block under a heading. Trusted only
#: from the block's own lead text or a heading that names the whole unit.
_CUED_ROLES = frozenset({"exercise", "solution", "worked_example"})


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


def _heading(row: HintRow, titles: Mapping[str, str]) -> str:
    """The block's nearest heading, a Marker header ref resolved to its text."""

    try:
        path = json.loads(row.section_path_json or "[]")
    except (TypeError, ValueError):
        return ""
    for element in reversed(path if isinstance(path, list) else []):
        value = str(element or "").strip()
        if value and value.lower() != "root":
            return titles.get(value, value)
    return ""


def effective_hint(row: HintRow, titles: Mapping[str, str]) -> str | None:
    """The block's role hint, unless only a heading substring gave it.

    Heading cues tag every block under a heading such as "Solutions of linear
    systems" or "The eigenvalue problem"; such a hint is not the block's own
    role, so it counts as ordinary prose. A hint from the block's lead text
    ("Solution:", "Problem 4.") or from a heading naming the whole unit
    ("Exercises", "Solutions to Selected Problems") is kept.
    """

    hint = row.role_hint
    if hint in _CUED_ROLES and lead_role(row.text) != hint \
            and unit_heading_role(_heading(row, titles)) != hint:
        return "ordinary_prose"
    return hint


#: Kept for callers written before the hint was public (canonical sources S1).
_effective_hint = effective_hint


def role_keys(connection, extraction_ids: Iterable[str], roles: Iterable[str]) -> set[tuple[str, str]]:
    """Blocks whose EFFECTIVE role hint is one of ``roles`` (a positive filter).

    The effective hint discounts heading-only cues (:func:`effective_hint`), so
    a block under "Solutions of linear systems" is not a solution.
    """

    wanted = {str(role) for role in roles if role}
    found: set[tuple[str, str]] = set()
    if not wanted:
        return found
    cued = wanted & _CUED_ROLES
    for extraction_id in sorted({str(value) for value in extraction_ids if value}):
        titles = section_header_titles(connection, extraction_id) if cued else {}
        for row in extraction_hint_rows(connection, extraction_id):
            if row.role_hint not in wanted:
                continue
            if effective_hint(row, titles) in wanted:
                found.add(row.key)
    return found


def _role_hint_exclusions(connection, extraction_ids: Iterable[str]) -> set[tuple[str, str]]:
    """Exercise and solution blocks (a solution with the body after its lead)."""

    found: set[tuple[str, str]] = set()
    for extraction_id in hinted_extraction_ids(connection, extraction_ids, ITEM_BOUND_EXCLUDED_ROLE_HINTS):
        titles = section_header_titles(connection, extraction_id)

        def mark(row: HintRow, titles: Mapping[str, str] = titles) -> str:
            hint = effective_hint(row, titles)
            if hint in ITEM_BOUND_EXCLUDED_ROLE_HINTS:
                return "region" if hint in _REGION_ROLE_HINTS else "block"
            return "body" if hint in REGION_BODY_HINTS else "stop"

        found |= lead_regions(extraction_hint_rows(connection, extraction_id), mark)
    return found


def _ref_spans(extraction_id: str | None, span_ids: Sequence[str]) -> set[tuple[str, str]]:
    """A YAML source ref's ``span_ids``: plain (``s4``) or namespaced (``ext/s4``, ``ext:s4``)."""

    found: set[tuple[str, str]] = set()
    for value in span_ids:
        span = str(value or "").strip()
        if not span:
            continue
        if extraction_id and span.startswith((f"{extraction_id}/", f"{extraction_id}:")):
            found.add((extraction_id, span[len(extraction_id) + 1:]))
        elif "/" in span:
            head, _, tail = span.partition("/")
            found.add((head, tail))
        elif extraction_id:
            found.add((extraction_id, span))
    return found


def _same_text_elsewhere(connection, linked: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """The linked blocks' text in every other extraction of the same source.

    A re-extraction renumbers span ids, and the tutor reads the source's
    latest run, so a link into an older run is matched there by block text.
    """

    by_extraction: dict[str, set[str]] = {}
    for extraction_id, span_id in linked:
        by_extraction.setdefault(extraction_id, set()).add(span_id)
    sources = extraction_source_ids(connection, by_extraction)
    found: set[tuple[str, str]] = set()
    for extraction_id, span_ids in sorted(by_extraction.items()):
        source_id = sources.get(extraction_id)
        hashes = block_content_hashes(connection, extraction_id, span_ids)
        if not source_id or not hashes:
            continue
        for other in source_extraction_ids(connection, source_id=source_id):
            if other != extraction_id:
                found.update((other, span_id) for span_id in spans_with_content_hashes(connection, other, hashes))
    return found


def item_exclusions(repository: Repository, item: PracticeItem) -> Exclusions:
    """Every passage the practice item is linked to, whatever the relation.

    An item made from a worked example (or an exercise, or a solution) may link
    it as ``primary``, ``support`` or ``alternate`` as well as ``exercise``: in
    an item-bound context that passage is the item's own worked answer. Both
    the item's ``entity_source_links`` (every relation and status) and its YAML
    ``provenance.source_refs`` count. A block locator names one block (and the
    same text in the source's other extractions), and a linked block that
    leads a worked example, exercise or solution takes the body after it too;
    a link or source ref that names no block excludes its whole extraction (or
    its revision's or source's extractions). A ref to another entity or a note
    names no source and excludes nothing.
    """

    whole: set[str] = set()
    spans: set[tuple[str, str]] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        links = list(entity_link_locators(connection, "practice_item", item.id))
        for ref in item.provenance.source_refs:
            source_id = ref.source_id or (ref.ref_id if ref.ref_type == "canonical_source" else None)
            if not (ref.extraction_id or ref.revision_id or source_id):
                continue
            named = _ref_spans(ref.extraction_id, ref.span_ids)
            spans |= named
            if ref.locator or not named:
                links.append(AssessmentLink(ref.extraction_id, ref.locator or "", source_id, ref.revision_id))
        for link in links:
            _link_exclusions(connection, link, whole, spans)
        linked = {key for key in spans if key[0] not in whole}
        linked |= {key for key in _same_text_elsewhere(connection, linked) if key[0] not in whole}
        spans |= linked
        for extraction_id in sorted({key[0] for key in linked}):
            titles = section_header_titles(connection, extraction_id)

            def mark(row: HintRow, titles: Mapping[str, str] = titles) -> str:
                hint = effective_hint(row, titles)
                if row.key in linked:
                    return "region" if hint in _ITEM_LEAD_REGION_HINTS else "block"
                return "body" if hint in REGION_BODY_HINTS else "stop"

            spans |= lead_regions(extraction_hint_rows(connection, extraction_id), mark)
    return Exclusions(frozenset(whole), frozenset(spans))


def _teaching_standing(vault: LoadedVault, repository: Repository) -> tuple[set[str], set[str]]:
    """Sources (and extractions) with a role: a source-set member, or cited by
    a learning object's, facet's or concept's teaching-relation link."""

    sources = {str(member.source_id) for source_set in vault.source_sets for member in source_set.members}
    extractions: set[str] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        links = teaching_link_locators(connection)
        revisions = revision_source_ids(connection, [link.revision_id for link in links
                                                     if link.revision_id and not link.source_id])
    for link in links:
        if link.extraction_id:
            extractions.add(link.extraction_id)
        if link.source_id:
            sources.add(link.source_id)
        elif link.revision_id in revisions:
            sources.add(revisions[link.revision_id])
    return sources, extractions


def teaching_scope(vault: LoadedVault, repository: Repository,
                   learning_object_ids: Iterable[str], *, item_bound: bool = False,
                   item: PracticeItem | None = None) -> Scope:
    """The tutor's grounding scope: the LOs' subjects' teaching sources.

    Sources come from the subjects' source sets plus any source the LOs'
    teaching provenance cites. With no LO, or no source found for them, every
    current source with a role is searched: a source in no source set that no
    learning object, facet or concept cites as teaching material has no role,
    and fails closed like an unknown one. Either way
    :func:`teaching_exclusions` applies (whole extractions leave the scope),
    and an ``item_bound`` context (practice, feedback) also drops exercise and
    solution blocks and, given the ``item``, every passage linked to it
    (:func:`item_exclusions`), since one of them may be its own worked answer.
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
        standing_sources, standing_extractions = _teaching_standing(vault, repository)
        extractions = {key: value for key, value in every.items()
                       if value.source_id in standing_sources or key in standing_extractions}
        notes.append("no source is linked to these learning objects; every source with a role is searched")
        unplaced = len({value.source_id for value in every.values()}) - len(
            {value.source_id for value in extractions.values()})
        if unplaced:
            notes.append(f"{unplaced} source(s) in no source set and cited by no teaching link excluded")
    exclusions = teaching_exclusions(vault, repository)
    dropped = sorted(set(extractions) & exclusions.extractions)
    for extraction_id in dropped:
        del extractions[extraction_id]
    if dropped:
        notes.append(f"{len(dropped)} source extraction(s) without teaching authority excluded")
    excluded = set(exclusions.spans)
    if item_bound and item is not None:
        own = item_exclusions(repository, item)
        own_whole = sorted(set(extractions) & own.extractions)
        for extraction_id in own_whole:
            del extractions[extraction_id]
        own_spans = {key for key in own.spans if key[0] in extractions}
        excluded |= own_spans
        if own_whole or own_spans:
            notes.append(f"{len(own_spans)} block(s) and {len(own_whole)} whole source extraction(s) "
                         "linked to the practice item excluded")
    if item_bound and extractions:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            hinted = _role_hint_exclusions(connection, extractions)
        if hinted:
            notes.append(f"{len(hinted)} exercise or solution block(s) excluded")
        excluded |= hinted
    return Scope("teaching", extractions, frozenset(excluded), tuple(notes))


__all__ = [
    "Exclusions",
    "ITEM_BOUND_EXCLUDED_ROLE_HINTS",
    "Scope",
    "SourceExtraction",
    "assessment_spans",
    "current_extractions",
    "effective_hint",
    "extraction_scope",
    "item_exclusions",
    "library_scope",
    "role_keys",
    "teaching_exclusions",
    "teaching_scope",
]
