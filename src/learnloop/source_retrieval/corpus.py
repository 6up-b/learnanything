"""Which source text a search covers: current extractions, scopes and exclusions.

A *scope* names the extractions a search reads and the spans it must never
return. The library scope is today's (every reader-enabled source, nothing
excluded). The teaching scope, used for the tutor's grounding, is the subject's
sources minus every assessment span: whole exam-role units (held-out exam
questions included) and spans linked by ``exercise`` or
``assessment_alignment`` provenance. Assessment lanes never enter a teaching
context (ING M8 §9.1).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import assessment_link_locators
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


def assessment_spans(vault: LoadedVault, repository: Repository) -> frozenset[tuple[str, str]]:
    """Every span that belongs to an assessment lane, vault-wide.

    Whole exam-role units (a member's default role or a unit override), which
    covers held-out exam questions and whole ``held_out_evaluation`` units, plus
    every span cited by an ``exercise`` or ``assessment_alignment`` link.
    """

    spans: set[tuple[str, str]] = set()
    for source_set in vault.source_sets:
        for member in source_set.members:
            overrides = {s.unit_id: s.role_override for s in member.scope if s.role_override}
            if member.default_role != "exam" and "exam" not in overrides.values():
                continue
            extraction_id = resolve_extraction_id(repository, member.revision_id)
            if extraction_id is None:
                continue
            ir = repository.load_document_ir(extraction_id)
            if ir is None:
                continue
            for unit in ir.units:
                if overrides.get(unit.unit_id, member.default_role) == "exam":
                    spans.update((str(extraction_id), str(span_id)) for span_id in unit.span_ids)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        links = assessment_link_locators(connection)
    for extraction_id, locator in links:
        parsed = parse_block_span(locator or "")
        if parsed is not None:
            spans.add((parsed[0], parsed[1]))
        elif extraction_id:
            # The malformed early-v2 ``span:<span>`` form names only the span.
            span_id = locator[len("span:"):] if locator.startswith("span:") else locator
            if span_id:
                spans.add((extraction_id, span_id))
    return frozenset(spans)


def teaching_scope(vault: LoadedVault, repository: Repository,
                   learning_object_ids: Iterable[str]) -> Scope:
    """The tutor's grounding scope: the LOs' subjects' sources, assessment excluded.

    Sources come from the subjects' source sets plus any source the LOs'
    teaching provenance cites. With no LO, or no source found for them, every
    current source is searched (still without assessment spans).
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
    return Scope("teaching", extractions, assessment_spans(vault, repository), tuple(notes))


__all__ = [
    "Scope",
    "SourceExtraction",
    "assessment_spans",
    "current_extractions",
    "extraction_scope",
    "library_scope",
    "teaching_scope",
]
