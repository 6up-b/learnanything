"""Sole owner of the shadow family FSRS projection. Never a scheduling reader."""
from __future__ import annotations

from collections import Counter

from learnloop.db.scopes import atomic_repository_call
from learnloop.offline_outcomes import digest
from learnloop.scheduling.family_memory_model import FamilyMemory
from learnloop.substrate.family_memory_rows import load_rows
from learnloop.substrate.activities import canonical_json
from learnloop.params.fitted_params import resolve_fsrs_weights

PROJECTION_VERSION = "family-memory-cold-v2"


@atomic_repository_call
def rebuild_family_memory(vault, repository) -> dict:
    if not any(getattr(item, "family_id", None) for item in vault.practice_items.values()):
        with repository.connection() as connection:
            connection.execute("DELETE FROM family_memory_state")
        return {"reviews": 0, "families": 0, "skipped": {},
                "projection_version": PROJECTION_VERSION}
    weights = resolve_fsrs_weights(repository)
    arm = FamilyMemory("family", weights)
    rows, source = load_rows(vault, repository, legacy_fallback="current_content",
                             for_projection=True)
    skipped: Counter = Counter()
    count = 0
    for row in sorted(rows, key=lambda r: (r.features.observed_at, r.features.attempt_id)):
        if not row.features.family_id:
            skipped["no_family"] += 1
        elif not row.memory_eligible:
            skipped[row.exclusion or ("not_cold" if not row.cold else "transfer")] += 1
        else:
            arm.observe(row)
            count += 1
    with repository.connection() as connection:
        connection.execute("DELETE FROM family_memory_state")
        for key, history in sorted(arm.history.items()):
            from learnloop.db.stores.families import record_revision

            family = vault.activity_families[key.removeprefix("family:")]
            # Authored family content is sufficient; no separate paid workflow
            # or sync command is a prerequisite for a deterministic rebuild.
            record_revision(connection, family_id=family.id,
                            spec_json=canonical_json(family.model_dump(mode="json")),
                            title=family.idea_statement, created_at=family.updated_at)
            connection.execute(
                """INSERT INTO family_memory_state
                   (family_id, difficulty, stability, retrievability, last_review_at,
                    review_count, weights_hash, projection_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (key.removeprefix("family:"), history.state.difficulty,
                 history.state.stability, history.state.retrievability,
                 history.last_review_at.isoformat(), history.review_count,
                 digest(weights), PROJECTION_VERSION))
    return {"reviews": count, "families": len(arm.history), "skipped": dict(skipped),
            "source": source, "projection_version": PROJECTION_VERSION}
