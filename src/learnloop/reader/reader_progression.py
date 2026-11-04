"""Reader-driven progressive practice seeding (reader-first bootstrap).

Under an items-off ("as_you_read") bootstrap the study map ships with zero
practice items. This module closes the loop: when the learner completes a guide
section, the section's spans are mapped back to the Learning Objects whose
provenance (their own or their facets') cites those spans, and a per-LO
practice-expansion job is enqueued for exactly those LOs — probe gate waived,
rung + difficulty calibrated from the learner claim / mastery by the standard
generation path.

Idempotence lives on ``reader_section_progress.generation_batch_id``: a section
triggers at most one generation, stamped atomically before the job runs.
"""

from __future__ import annotations

import hashlib
from typing import Any

from learnloop.content.sources.span_aliases import SpanTranslator
from learnloop.db.repositories import Repository
from learnloop.reader.reader_guidance import _span_for_ref, extraction_sections
from learnloop.section_map import (  # moved below every package that reads them; this name stays the Reader's
    learning_objects_by_section,
    learning_objects_for_section,
    learning_objects_for_span,
    section_id_for_span,
)
from learnloop.vault.models import LoadedVault, learning_object_facet_union
from learnloop.vault.paths import VaultPaths


_SOURCE_BUNDLE_RADIUS = 5
_MAX_SOURCE_BUNDLES_PER_LO = 4


def source_refs_for_span(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
    learning_object_ids: list[str],
) -> list[dict[str, Any]]:
    """Canonical, path-backed grounding bundles for a selected reader target."""

    section_id = section_id_for_span(
        repository, extraction_id=extraction_id, span_id=span_id
    )
    if section_id is None:
        return []
    return source_refs_for_section(
        vault,
        repository,
        extraction_id=extraction_id,
        section_id=section_id,
        learning_object_ids=learning_object_ids,
    )


def section_generation_candidates(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    target_items_per_lo: int = 3,
    max_new_per_lo: int = 3,
) -> list[str]:
    """LOs in the section that actually need items (dry-run of the expansion
    plan with the probe gate waived). Empty = nothing to generate."""

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_practice_expansion_plan,
    )

    lo_ids = learning_objects_for_section(
        vault, repository, extraction_id=extraction_id, section_id=section_id
    )
    if not lo_ids:
        return []
    try:
        plan = build_practice_expansion_plan(
            vault,
            repository,
            learning_object_ids=lo_ids,
            require_completed_probe=False,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
        )
    except PracticeExpansionError:
        return []
    # Only LOs with a real deficit: named LOs past their target still get a
    # courtesy item from the planner, which is wrong for an automatic trigger.
    return sorted(
        target.learning_object_id
        for target in plan.targets
        if target.existing_practice_items < target_items_per_lo
    )


def source_refs_for_section(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
    learning_object_ids: list[str],
) -> list[dict[str, Any]]:
    """Build bounded, proposal-local citation bundles for reader seeding.

    Section completion previously used LO/facet provenance only for routing and
    then discarded it before authoring.  These refs preserve the immutable
    source/revision/extraction identity plus enough neighboring blocks to avoid
    handing the model a sentence fragment (common for captions and PDF blocks).

    ``ref_id`` identifies the citation bundle, not merely the source artifact,
    so several distinct spans from one source remain independently selectable by
    ``AuthoringProposalItem.source_ref_ids``.
    """

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return []
    revision = repository.get_source_revision(str(run.get("revision_id") or ""))
    if revision is None:
        return []
    source_id = str(revision.get("source_id") or "")
    ir = repository.load_document_ir(extraction_id)
    if not source_id or ir is None:
        return []
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)
    section = next((row for row in section_rows if row["id"] == section_id), None)
    if section is None:
        return []
    ordered_spans = [span_id for span_id in section["span_ids"] if span_id in block_by_span]
    if not ordered_spans:
        return []
    blocks = [block_by_span[span_id] for span_id in ordered_spans]
    index_by_span = {span_id: index for index, span_id in enumerate(ordered_spans)}

    from learnloop.reader.reader_guidance import _canonical_note_ids

    artifact = repository.get_source_artifact(source_id) or {}
    note_ids = _canonical_note_ids(vault, artifact)
    # Grounding cites the same text only: a ref on an earlier reading counts
    # here when its alias is exact (re-read safety).
    translator = SpanTranslator(repository, extraction_id)
    raw_path = VaultPaths(vault.root, vault.config).canonical_source_raw_path(
        str(revision.get("asset_hash") or "")
    )
    relative_raw_path = (
        raw_path.relative_to(vault.root).as_posix() if raw_path.is_file() else None
    )

    source_refs: list[dict[str, Any]] = []
    for learning_object_id in learning_object_ids:
        learning_object = vault.learning_objects.get(learning_object_id)
        if learning_object is None:
            continue
        prioritized_refs: list[tuple[int, Any]] = [
            (0, ref) for ref in learning_object.provenance.source_refs
        ]
        for facet_id in learning_object_facet_union(learning_object):
            facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
            if facet is not None:
                prioritized_refs.extend((1, ref) for ref in facet.provenance.source_refs)

        anchors_by_span: dict[str, tuple[int, Any]] = {}
        for priority, ref in prioritized_refs:
            span_id = _span_for_ref(
                ref,
                source_id=source_id,
                extraction_id=extraction_id,
                note_ids=note_ids,
                blocks=blocks,
                translator=translator,
            )
            if span_id is None or span_id not in index_by_span:
                continue
            prior = anchors_by_span.get(span_id)
            if prior is None or priority < prior[0]:
                anchors_by_span[span_id] = (priority, ref)
        selected_anchors = sorted(
            anchors_by_span,
            key=lambda span_id: (anchors_by_span[span_id][0], index_by_span[span_id]),
        )[:_MAX_SOURCE_BUNDLES_PER_LO]
        intervals = _merged_context_intervals(
            [index_by_span[span_id] for span_id in selected_anchors], len(ordered_spans)
        )
        for start, end in intervals:
            bundle_blocks = blocks[start : end + 1]
            bundle_span_ids = [block.span_id for block in bundle_blocks]
            quote = "\n".join(block.text for block in bundle_blocks)
            quote_hash = "sha256:" + hashlib.sha256(quote.encode("utf-8")).hexdigest()
            span_hash_material = "\n".join(block.content_hash for block in bundle_blocks)
            span_hash = "sha256:" + hashlib.sha256(
                span_hash_material.encode("utf-8")
            ).hexdigest()
            first_span, last_span = bundle_span_ids[0], bundle_span_ids[-1]
            source_refs.append(
                {
                    "ref_type": "canonical_source",
                    "ref_id": (
                        f"reader_citation:{extraction_id}:{learning_object_id}:"
                        f"{first_span}-{last_span}"
                    ),
                    "path": relative_raw_path,
                    "locator": f"span:{extraction_id}/{first_span}",
                    "quote": quote,
                    "quote_hash": quote_hash,
                    "source_id": source_id,
                    "revision_id": str(revision["id"]),
                    "extraction_id": extraction_id,
                    "span_ids": bundle_span_ids,
                    "span_hash": span_hash,
                    "section_id": section_id,
                    "learning_object_ids": [learning_object_id],
                }
            )
    return source_refs


def _merged_context_intervals(anchor_indices: list[int], span_count: int) -> list[tuple[int, int]]:
    intervals = sorted(
        (
            max(0, index - _SOURCE_BUNDLE_RADIUS),
            min(span_count - 1, index + _SOURCE_BUNDLE_RADIUS),
        )
        for index in set(anchor_indices)
    )
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
