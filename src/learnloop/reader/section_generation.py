"""Section practice candidates, separate from reader grounding.

This keeps practice_generation out of reader_progression.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.reader.reader_progression import learning_objects_for_section
from learnloop.vault.models import LoadedVault


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
