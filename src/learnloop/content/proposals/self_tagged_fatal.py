"""Queue reviewed rubric fatal-error proposals from repeated learner self-tags.

The attempt completion path calls this promotion after recording a self-tag.
"""

from __future__ import annotations

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault, PracticeItem


def maybe_promote_self_tagged_fatal_error(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    error_type: str | None,
    clock: Clock | None = None,
) -> str | None:
    """Queue a reviewed proposal to add a repeatedly self-tagged misconception ``E`` to
    an item's rubric ``fatal_errors`` (spec §12.4 — durable-probe promotion).

    Promotion is **independent of the per-attempt trust weight ``w``**: cross-attempt
    repetition is the only N=1-safe signal that the item *reliably* reveals ``E`` (same
    philosophy as §3 / §7.4). It fires exactly once, when the per-``(item, E)`` self-tag
    count reaches ``probe.self_tag.promotion_threshold``; the proposal is always
    ``review_required`` (never auto-applied) — the review gate guards against a learner
    talking themselves into a misconception. Returns the patch id when queued, else None.
    """

    if not error_type:
        return None
    error = vault.error_types.get(error_type)
    if error is None or not error.is_misconception:
        return None
    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return None
    if any(fatal_error.id == error_type for fatal_error in rubric.fatal_errors):
        return None  # already a rubric-asserted probe of E

    threshold = vault.config.probe.self_tag.promotion_threshold
    if repository.count_attempts_with_error_type(item.id, error_type) < threshold:
        return None

    client_item_id = f"self_tag_promotion:{item.id}:{error_type}"
    if repository.proposal_items_by_client_id(client_item_id):
        return None  # already proposed (pending/accepted/rejected) — fire once

    now = utc_now_iso(clock)
    fatal_errors = [fatal_error.model_dump(mode="json", exclude_none=True) for fatal_error in rubric.fatal_errors]
    fatal_errors.append(
        {
            "id": error_type,
            "description": f"Learner repeatedly self-attributed {error.title} on this item.",
            "max_grade": 1,
        }
    )
    rubric_payload = {
        "target_practice_item_id": item.id,
        "max_points": rubric.max_points,
        "criteria": [criterion.model_dump(mode="json", exclude_none=True) for criterion in rubric.criteria],
        "fatal_errors": fatal_errors,
    }
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "self_tag_promotion",
            "provider": "self",
            "prompt_template": "self_tag_promotion",
            "started_at": now,
            "completed_at": now,
            "status": "completed",
        }
    )
    return repository.persist_proposal_batch(
        {
            "id": new_ulid(),
            "agent_run_id": agent_run_id,
            "purpose": "self_tag_promotion",
            "source_refs": [],
            "summary": f"Promote self-attributed {error_type} to a fatal error on {item.id}.",
            "created_at": now,
            "updated_at": now,
        },
        [
            {
                "id": new_ulid(),
                "client_item_id": client_item_id,
                "item_type": "rubric",
                "operation": "update",
                "target_entity_type": "rubric",
                "target_entity_id": item.id,
                "payload": rubric_payload,
                "decision": "pending",
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
