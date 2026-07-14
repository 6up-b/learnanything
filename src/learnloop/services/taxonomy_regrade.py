"""Non-destructive taxonomy regrade-check (knowledge-model §16 Taxonomy row).

The mechanism taxonomy (§10.1) is a grader contract: bumping ``GRADING_PROMPT_VERSION``
changes the vocabulary the grader emits under mvp-0.7. This check mirrors
``services/probe_audit.run_probe_regrade_checks`` — it re-grades a sample of
already-graded practice attempts under the current prompt version and compares
the *mechanism* each attribution resolves to (through ``map_legacy_error_type``),
so a version bump that renames labels while preserving the mechanism shows **no
attribution regression**. It NEVER writes belief state, supersedes evidence, or
replays: it only reads the stored response, re-runs the grader, and reports.

A "regression" is a mechanism the original grading attributed that the regrade
fails to reproduce (dropped or changed). Comparing in the canonical mechanism
space means legacy (mvp-0.6) and mvp-0.7 attributions are directly comparable.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.error_taxonomy_map import map_legacy_error_type
from learnloop.vault.models import LoadedVault


def _mechanisms(error_types: list[str | None]) -> set[str]:
    return {
        mechanism
        for mechanism in (map_legacy_error_type(et) for et in error_types if et)
        if mechanism
    }


def run_taxonomy_regrade_checks(
    vault: LoadedVault,
    repository: Repository,
    client: Any,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    """Re-grade a sample of graded attempts and report attribution regressions.

    Returns a report with ``attempted`` / ``checked`` counts, a per-attempt
    ``regressions`` list (dropped mechanisms), and a top-level ``no_regressions``
    flag. Deterministic given a deterministic ``client`` — no LLM required for
    tests (pass a canned grader).
    """

    from learnloop.services.grading import (
        build_grading_context,
        validate_codex_grading_proposal,
    )

    attempted = 0
    checked = 0
    failed = 0
    regressions: list[dict[str, Any]] = []
    for learning_object_id in sorted(repository.learning_object_ids_with_attempts()):
        if attempted >= limit:
            break
        for attempt in repository.list_attempts_by_learning_object(learning_object_id):
            if attempted >= limit:
                break
            attempt_id = str(attempt["id"])
            events = repository.error_events_for_attempt(attempt_id)
            original = _mechanisms([event.get("error_type") for event in events])
            if not original:
                continue  # nothing attributed to compare against
            item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
            if item is None:
                continue
            attempted += 1
            try:
                context = build_grading_context(
                    vault,
                    item,
                    attempt_id=attempt_id,
                    learner_answer_md=attempt.get("learner_answer_md") or "",
                )
                proposal = client.run_grading_proposal(context)
                validated = validate_codex_grading_proposal(
                    proposal, attempt_id=attempt_id, item=item, vault=vault
                )
            except Exception:
                failed += 1
                continue
            checked += 1
            regrade = _mechanisms(
                [attribution.error_type for attribution in validated.error_attributions]
            )
            dropped = sorted(original - regrade)
            if dropped:
                regressions.append(
                    {
                        "attempt_id": attempt_id,
                        "practice_item_id": item.id,
                        "learning_object_id": learning_object_id,
                        "original_mechanisms": sorted(original),
                        "regrade_mechanisms": sorted(regrade),
                        "dropped_mechanisms": dropped,
                    }
                )
    return {
        "prompt_version": _grading_prompt_version(),
        "attempted": attempted,
        "checked": checked,
        "failed": failed,
        "regressions": regressions,
        "regression_count": len(regressions),
        "no_regressions": not regressions,
    }


def _grading_prompt_version() -> str:
    from learnloop.codex.prompts import GRADING_PROMPT_VERSION

    return GRADING_PROMPT_VERSION
