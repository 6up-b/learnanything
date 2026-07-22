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

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.reader_guidance import _span_for_ref, extraction_sections
from learnloop.vault.models import LoadedVault, learning_object_facet_union


def learning_objects_for_section(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
) -> list[str]:
    """Active Learning Objects whose provenance cites spans inside the section.

    Reuses the guide plan's span resolution (`_span_for_ref`) so item passages,
    quick-checks, and progression triggers agree on what belongs to a section.
    Returns a sorted, de-duplicated id list; empty when the section has no
    provenance-linked LOs (thin citation — see the source-finished sweep).
    """

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return []
    revision = repository.get_source_revision(run["revision_id"])
    source_id = str((revision or {}).get("source_id") or "")
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return []
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)
    section = next((row for row in section_rows if row["id"] == section_id), None)
    if section is None:
        return []
    section_spans = set(section["span_ids"])
    blocks = [block_by_span[span_id] for span_id in section["span_ids"] if span_id in block_by_span]

    from learnloop.services.reader_guidance import _canonical_note_ids

    artifact = repository.get_source_artifact(source_id) or {}
    note_ids = _canonical_note_ids(vault, artifact)

    matched: set[str] = set()
    for learning_object in vault.learning_objects.values():
        if learning_object.status != "active":
            continue
        refs = list(learning_object.provenance.source_refs)
        for facet_id in learning_object_facet_union(learning_object):
            facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
            if facet is not None:
                refs.extend(facet.provenance.source_refs)
        for ref in refs:
            span_id = _span_for_ref(
                ref,
                source_id=source_id,
                extraction_id=extraction_id,
                note_ids=note_ids,
                blocks=blocks,
            )
            if span_id is not None and span_id in section_spans:
                matched.add(learning_object.id)
                break
    return sorted(matched)


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

    from learnloop.services.practice_generation import (
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
