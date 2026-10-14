"""Which source text a search covers: current extractions, scopes and exclusions.

A *scope* names the extractions a search reads and the spans it must never
return. The library scope is today's (every reader-enabled source, nothing
excluded). The teaching scope, used for the tutor's grounding, is the subject's
sources minus everything without teaching authority: exam and held-out
material by the one predicate (``content.sources.exam_material``), source-set
material whose role lacks ``semantic_contract`` authority (problem set, notes,
unknown; whole members or unit overrides, in every extraction of the source)
and spans linked by ``exercise`` or ``assessment_alignment`` provenance. Assessment lanes
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

from learnloop.content.sources import exam_material as EM
from learnloop.content.sources.exam_material import is_exam_role
from learnloop.content.sources.role_authority import role_authority
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.sources.span_aliases import CitationResolver
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    REGION_BODY_HINTS,
    AssessmentLink,
    HintRow,
    assessment_link_locators,
    block_content_hashes,
    entity_link_locators,
    extraction_hint_rows,
    extraction_source_ids,
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


def _withheld_besides_exams(role: str | None) -> bool:
    """A role without teaching authority that is not ``exam``: problem sets,
    notes and unknown roles (exams are the shared predicate's)."""

    return not _teaches(role) and not is_exam_role(role)


#: The exam use mode of a protected, held-out evaluation unit (spec_source_ingestion_v2 §4.2).
HELD_OUT_EVALUATION = EM.HELD_OUT_EVALUATION


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

    Exam and held-out material, by the one predicate
    (``content.sources.exam_material``: exam members and exam units in every
    revision of their source, every ``held_out_evaluation`` unit whatever its
    role, unresolvable units failing closed); source-set material of the
    other roles without teaching authority (problem_set, notes and unknown
    roles, whole members or unit overrides, resolved the same way); and every
    span an ``exercise`` or ``assessment_alignment`` link cites (or, for a
    locator that does not name a block, its whole extraction).
    """

    exam = EM.exam_material(vault, repository).material
    others = EM.role_material(vault, repository, _withheld_besides_exams)
    whole: set[str] = set(exam.extractions | others.extractions)
    spans: set[tuple[str, str]] = set(exam.spans | others.spans)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for link in assessment_link_locators(connection):
            _link_exclusions(connection, link, whole, spans)
    return Exclusions(frozenset(whole), frozenset(spans))


def exam_exclusions(vault: LoadedVault, repository: Repository) -> Exclusions:
    """Exam material only, by the one predicate (``content.sources.exam_material``):
    the narrow part of :func:`teaching_exclusions` the canonical-sources paths
    that read the whole library withhold (tutor pins, ``find_sources`` pools,
    comparisons); notes, problem sets and solutions keep those paths' own rules."""

    exam = EM.exam_material(vault, repository).material
    return Exclusions(exam.extractions, exam.spans)


def source_exam_exclusions(vault: LoadedVault, repository: Repository, *, source_id: str,
                           revision_id: str | None) -> Exclusions:
    """The exam material a book's automatic build must leave out (UX Phase 1:
    a book's scope is planned before its first study map exists), by the one
    predicate (``content.sources.exam_material``), so there is exactly one
    exam and held-out test.

    The predicate's rule 3 reads every unit selection's ``held_out_evaluation``
    marks whether or not the source is in a source set, and its rule 1 every
    outline role pick ``exam``, so the book's own marks before its first study
    map are already in :func:`exam_exclusions`; nothing is added here.
    ``source_id`` and ``revision_id`` name the book the caller plans (the
    material is vault-wide: a caller reads its own extraction's entries)."""

    del source_id, revision_id  # the predicate is vault-wide; see the docstring
    return exam_exclusions(vault, repository)


def exam_withheld(vault: LoadedVault, repository: Repository,
                  keys: Iterable[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """The keys among ``keys`` that are exam material (the one predicate)."""

    return EM.exam_withheld(vault, repository, keys)


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


def role_proposal_keys(connection, repository: Repository, extraction_ids: Iterable[str],
                       roles: Iterable[str]) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Spans a Reader RW4e role proposal gives one of ``roles``: ``(confident, low)``.

    RW4e writes its proposals as ``source_object_versions.authorial_role``
    (proposed or reviewed) with the spans they cite; a ``low``-confidence
    proposal counts only when nothing better exists (the caller decides).
    A proposal only ever widens the positive filter: the scope, ingest's
    exclusions and item links still apply (the Reader's G44). Feature-detected:
    no table, or no proposal, gives nothing."""

    wanted = {str(role) for role in roles if role}
    extractions = {str(value) for value in extraction_ids if value}
    strong: set[tuple[str, str]] = set()
    weak: set[tuple[str, str]] = set()
    if not wanted or not extractions or connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_object_versions'").fetchone() is None:
        return strong, weak
    marks = ",".join("?" for _ in wanted)
    rows = connection.execute(
        "SELECT v.content_json, c.revision_id, c.span_id, c.block_content_hash, c.created_at "
        "FROM source_object_versions v "
        "JOIN source_object_citations c ON c.source_object_version_id = v.id "
        f"WHERE v.status IN ('proposed', 'reviewed') AND v.authorial_role IN ({marks})",
        tuple(sorted(wanted))).fetchall()
    # Each citation on the reading it was made on, moved to its book's
    # current reading only through an exact alias (re-read safety): never
    # "the latest reading + the old span id".
    citations = CitationResolver(repository)
    for content_json, revision_id, span_id, block_content_hash, created_at in rows:
        key = citations.current_key({"revision_id": revision_id, "span_id": span_id,
                                     "block_content_hash": block_content_hash, "created_at": created_at})
        if key is None or key[0] not in extractions:
            continue
        try:
            confidence = (json.loads(content_json or "{}") or {}).get("confidence")
        except (TypeError, ValueError):
            confidence = None
        (weak if confidence == "low" else strong).add(key)
    return strong, weak - strong


def block_roles(connection, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str | None]:
    """Each block's EFFECTIVE role (:func:`effective_hint`), a solution region's
    body included: the unhinted text after a "Solution:" lead is ``solution``.

    The Marker ``block_type`` (``Text``, ``ListGroup``) is not a role; readers
    that must withhold solutions read this instead (spec §5.3, SC3).
    """

    wanted = {(str(key[0]), str(key[1])) for key in keys}
    roles: dict[tuple[str, str], str | None] = {}
    for extraction_id in sorted({key[0] for key in wanted}):
        titles = section_header_titles(connection, extraction_id)
        rows = extraction_hint_rows(connection, extraction_id)
        hints = {row.key: effective_hint(row, titles) for row in rows}

        def mark(row: HintRow, hints: Mapping[tuple[str, str], str | None] = hints) -> str:
            hint = hints[row.key]
            if hint in _REGION_ROLE_HINTS:
                return "region"
            return "body" if hint in REGION_BODY_HINTS else "stop"

        solution_region = lead_regions(rows, mark)
        for key in wanted:
            if key[0] != extraction_id or key not in hints:
                continue
            roles[key] = "solution" if key in solution_region else (hints[key] or None)
    return roles


#: Effective roles a model reader never receives (spec §5.3, SC3).
MODEL_WITHHELD_ROLES = frozenset({"solution"})


def model_reader_withheld(vault: LoadedVault, repository: Repository,
                          keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str]:
    """The spans a result returned to a MODEL must drop, each with its reason.

    Whatever the policy (``reading`` included, and whether or not an item is
    bound): ``solution`` for a solution block or the body after its lead, by
    effective role; ``assessment_lane`` for material without teaching
    authority (exam, problem-set and unknown-role members, held-out units) and
    every span an ``exercise`` or ``assessment_alignment`` link cites
    (:func:`teaching_exclusions`). A learner still reads all of it in the
    Reader; only what a model receives is narrowed.
    """

    wanted = {(str(key[0]), str(key[1])) for key in keys}
    if not wanted:
        return {}
    exclusions = teaching_exclusions(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        roles = block_roles(connection, wanted)
    withheld: dict[tuple[str, str], str] = {}
    for key in wanted:
        if roles.get(key) in MODEL_WITHHELD_ROLES:
            withheld[key] = "solution"
        elif key in exclusions.spans or key[0] in exclusions.extractions:
            withheld[key] = "assessment_lane"
    return withheld


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
    "MODEL_WITHHELD_ROLES",
    "assessment_spans",
    "block_roles",
    "current_extractions",
    "effective_hint",
    "extraction_scope",
    "item_exclusions",
    "library_scope",
    "exam_exclusions",
    "exam_withheld",
    "model_reader_withheld",
    "role_keys",
    "role_proposal_keys",
    "source_exam_exclusions",
    "teaching_exclusions",
    "teaching_scope",
]
