"""Publish verified PF-b survivors into their family as ordinary items (Slice 2 §5.3).

Publication is a content change, like writing a card (Slice A §0.3): the item
is written through the ordinary vault writer, gets its own practice card
(``resolve_legacy_item``; shared memory is Phase 3b's decision), joins its
family through an append-only membership event, and enters the queue. It is
gated by ``pf.generation_enabled`` and capped at ``pf.max_published_per_day``
per UTC day. A candidate whose reference is unverified is never published
(P9): this module refuses it, and SQL refuses a published row without a
verified reference.

Mechanics follow the probe re-mint path (an existing deterministic mint): the
published item copies the parent's measurement contract — LO, mode, facets and
weights, the rubric verbatim (the 078 surface-variant rule; the structure check
confirmed it applies), the trace contract for isomorphs — and stamps the
parent's surface group as ``evidence_fingerprint.source_family`` so kinship
discounting treats sibling evidence as correlated, as rung variants do.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.families import append_membership
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.pf import candidate as load_candidate
from learnloop.db.stores.pf import published_count_between, update_candidate
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.substrate.item_fingerprints import render_expected_answer
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.writer import upsert_practice_item

_LOGGER = logging.getLogger(__name__)

PUBLISH_POLICY_VERSION = "pf-publish-v1"
PF_TAG = "pf_generated"


class PublishRefused(ValueError):
    """The candidate may not be published (unverified, disabled, wrong state)."""


def utc_day_bounds(clock: Clock | None = None) -> tuple[str, str]:
    now = datetime.fromisoformat(utc_now_iso(clock).replace("Z", "+00:00")).astimezone(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Same "...Z" format as utc_now_iso, so string bounds compare correctly.
    return (start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))


def remaining_publish_slots(vault: LoadedVault, repository: Repository,
                            clock: Clock | None = None) -> int:
    start, end = utc_day_bounds(clock)
    with repository.connection() as connection:
        used = published_count_between(connection, start, end)
    return max(0, vault.config.pf.max_published_per_day - used)


def published_item_id(candidate_id: str) -> str:
    return "pi_pf_" + content_key(["pf_publish", candidate_id])[:24]


def build_item_payload(vault: LoadedVault, parent: PracticeItem, row: dict[str, Any],
                       *, item_id: str, now_iso: str) -> dict[str, Any]:
    payload = json.loads(row["payload_json"])
    relation = row["final_relation"] or row["declared_relation"]

    def dump(model: Any) -> Any:
        return None if model is None else model.model_dump(mode="json", exclude_none=False)

    fingerprint: dict[str, Any] = {"source_family": surface_group_id(parent)}
    if parent.evidence_fingerprint.solution_recipe_family and relation in {"same_target", "isomorph"}:
        fingerprint["solution_recipe_family"] = parent.evidence_fingerprint.solution_recipe_family
    keep_trace = relation in {"same_target", "isomorph"}
    return {
        "schema_version": parent.schema_version,
        "id": item_id,
        "learning_object_id": parent.learning_object_id,
        "subjects": list(parent.subjects) if parent.subjects is not None else None,
        "practice_mode": parent.practice_mode,
        "attempt_types_allowed": list(parent.attempt_types_allowed),
        "evidence_facets": list(parent.evidence_facets),
        "evidence_weights": dict(parent.evidence_weights),
        "criterion_facet_weights": {key: dict(value) for key, value in parent.criterion_facet_weights.items()},
        "trace_contract": dump(parent.trace_contract) if keep_trace else None,
        "prompt": payload["stem"],
        "expected_answer": render_expected_answer(payload["final_answer"], payload["solution"]),
        "difficulty": row["difficulty"],
        "difficulty_source": "solver_panel" if row["difficulty"] is not None else None,
        "tags": sorted({PF_TAG, f"pf_path_{row['generation_path']}"}),
        "retrieval_demand": parent.retrieval_demand,
        "scaffold_level": parent.scaffold_level,
        "capability": parent.capability,
        "task_features": dict(parent.task_features) if parent.task_features else None,
        "task_feature_schema": parent.task_feature_schema,
        "evidence_fingerprint": fingerprint,
        "grading_rubric": dump(parent.grading_rubric),
        "status": "active",
        "provenance": {
            "origin": "codex_proposal",
            "source_refs": [{
                "ref_type": "existing_entity", "ref_id": parent.id,
                "locator": f"pf_candidate:{row['id']}",
            }],
        },
        "family_id": row["family_id"],
        "variant_relation": relation,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def publish_candidate(vault: LoadedVault, repository: Repository, candidate_id: str, *,
                      clock: Clock | None = None) -> tuple[LoadedVault, str]:
    """Publish one selected, verified candidate; idempotent after a crash.

    Returns the refreshed vault and the published item id. The caller checks
    the daily cap and holds the PF run lock.
    """
    if not vault.config.pf.generation_enabled:
        raise PublishRefused("pf.generation_enabled is off")
    with repository.connection() as connection:
        row = load_candidate(connection, candidate_id)
    if row is None:
        raise PublishRefused(f"Unknown candidate {candidate_id}")
    if row["status"] == "published":
        return vault, row["published_item_id"]
    if row["verification"] != "verified":
        raise PublishRefused("An unverified reference is never published")
    if row["generation_path"] == "single_shot" or row["status"] != "selected":
        raise PublishRefused(f"Candidate is {row['status']} on the {row['generation_path']} path")
    parent = vault.practice_items.get(row["parent_item_id"])
    family = vault.activity_families.get(row["family_id"])
    if parent is None or family is None:
        raise PublishRefused("The parent item or family no longer exists")
    item_id = published_item_id(candidate_id)
    now_iso = utc_now_iso(clock)
    payload = build_item_payload(vault, parent, row, item_id=item_id, now_iso=now_iso)
    PracticeItem.model_validate(payload)
    decision_id = "pfpub_" + content_key([candidate_id, row["content_hash"], PUBLISH_POLICY_VERSION])
    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (decision_id,)).fetchone() is None:
            append_judgment(
                connection, id=decision_id, task="pf_publish", left_kind="pf_candidate",
                left_id=candidate_id, right_kind="practice_item", right_id=item_id,
                judge="verifier", prompt_version=PUBLISH_POLICY_VERSION,
                input_hash=row["content_hash"], verdict="publish",
                rationale=json.dumps({
                    "verification": row["verification"],
                    "verification_check": row["verification_check"],
                    "filters": json.loads(row["filters_json"] or "{}"),
                    "family_id": row["family_id"],
                    "variant_relation": payload["variant_relation"],
                }, sort_keys=True),
                created_at=now_iso,
            )
    if item_id not in vault.practice_items:
        upsert_practice_item(vault.root, payload, clock=clock, loaded_vault=vault)
    vault = load_vault(vault.root)
    item = vault.practice_items[item_id]
    resolved = resolve_legacy_item(vault, repository, item, purpose="practice", clock=clock)
    with repository.connection() as connection:
        append_membership(
            connection, family_id=row["family_id"],
            member={"card_id": resolved.card_id, "item_id": item_id,
                    "variant_relation": payload["variant_relation"]},
            action="add", proposal_id="pfpub_" + candidate_id, judgment_id=decision_id,
            created_at=now_iso,
        )
        update_candidate(connection, candidate_id, status="published", published_item_id=item_id,
                         published_at=now_iso, updated_at=now_iso)
    # Fresh scheduling state, as the next state sync would derive it.
    repository.upsert_practice_item_state(item_id, active=True,
                                          content_hash=practice_item_hash(item), clock=clock)
    try:
        repository.bump_queue_revision(clock=clock)
    except Exception:  # noqa: BLE001 - queue nudging never blocks publication
        _LOGGER.warning("failed to bump queue revision after PF publication", exc_info=True)
    return vault, item_id


def publish_selected(vault: LoadedVault, repository: Repository, candidate_ids: list[str], *,
                     clock: Clock | None = None) -> tuple[LoadedVault, dict[str, Any]]:
    """Publish in order while today's cap allows; the rest stay ``selected``."""
    published: list[str] = []
    capped: list[str] = []
    for candidate_id in candidate_ids:
        with repository.connection() as connection:
            row = load_candidate(connection, candidate_id)
        if row is None or row["status"] != "selected":
            continue
        if remaining_publish_slots(vault, repository, clock) <= 0:
            capped.append(candidate_id)
            continue
        vault, item_id = publish_candidate(vault, repository, candidate_id, clock=clock)
        published.append(item_id)
    return vault, {"published_item_ids": published, "capped_candidates": len(capped),
                   "cap": vault.config.pf.max_published_per_day}


__all__ = [
    "PF_TAG", "PUBLISH_POLICY_VERSION", "PublishRefused", "build_item_payload",
    "publish_candidate", "publish_selected", "published_item_id", "remaining_publish_slots",
    "utc_day_bounds",
]
