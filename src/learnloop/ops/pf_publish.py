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

from collections.abc import Mapping
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
from learnloop.db.stores.pf import (
    candidate_verdicts, published_count_between, update_candidate, verdict_survived, verdict_verified,
)
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.substrate.item_fingerprints import render_expected_answer
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.required_method import VARIANT_CONTRADICTS_METHOD, inherit_required_method
from learnloop.vault.models import ActivityFamily, LoadedVault, PracticeItem
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault_lock import vault_mutation_lock

_LOGGER = logging.getLogger(__name__)

PUBLISH_POLICY_VERSION = "pf-publish-v2"
JUDGED_INPUTS_VERSION = "pf-judged-inputs-v1"
# The parent fields a published item copies or the judges compared against.
_CONTRACT_FIELDS = (
    "schema_version", "learning_object_id", "subjects", "practice_mode", "attempt_types_allowed",
    "evidence_facets", "evidence_weights", "criterion_facet_weights", "trace_contract", "prompt",
    "expected_answer", "grading_rubric", "retrieval_demand", "scaffold_level", "capability",
    "task_features", "task_feature_schema", "evidence_fingerprint", "status",
)
PF_TAG = "pf_generated"
# Relations that keep the parent's trace contract: each needs a passing
# checkpoint-preservation (structure) check.
TRACE_RELATIONS = frozenset({"same_target", "isomorph"})
#: Canonical sources (Codex review F11): PF's own verification of a published
#: variant, as the reference-key status the C3 gate reads. The same reading as
#: the import ladder: a passing symbolic check is ``checked``, panel agreement
#: on a non-symbolic answer ``panel_agrees``, a quote-verified supported span
#: ``book_solution``. Anything else records no check (the honest default).
PF_KEY_STATUS = {
    "execution_cas": "checked",
    "panel_agreement+sympy": "checked",
    "panel_agreement": "panel_agrees",
    "quote_verified_span+support": "book_solution",
}


class PublishRefused(ValueError):
    """The candidate may not be published (unverified, disabled, wrong state)."""


class VariantContradictsRequiredMethod(PublishRefused):
    """The variant's stem negates the parent's required method or leaves it
    optional, while the parent's rubric (copied verbatim) grades use of it
    (re-review F10): rejected, so a later run regenerates the variant."""


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
    item = {
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
        # Canonical sources S1 (§7.4): a variant of a textbook exercise points at it.
        **({"canonical_exercise": {**parent.canonical_exercise.model_dump(mode="json"), "relation": "variant_of"}}
           if getattr(parent, "canonical_exercise", None) is not None else {}),
    }
    # Method-explicit items (owner rule 2026-10-13): the variant keeps the
    # parent's rubric verbatim, so it keeps its required method too, and its
    # stem states it ("Use {method} in your answer." when the stem does not).
    # A stem that contradicts the method is never given the instruction nor
    # published (re-review F10).
    if VARIANT_CONTRADICTS_METHOD in inherit_required_method(item, parent):
        raise VariantContradictsRequiredMethod(
            f"The variant's stem contradicts the parent's required method "
            f"{parent.required_method.name!r} (it negates it or leaves it optional)"
        )
    return item


def _contract_view(vault: LoadedVault, parent: PracticeItem) -> dict[str, Any]:
    """What the judges compared against and what publication copies from the parent."""
    dumped = parent.model_dump(mode="json")
    rubric = vault.rubric_for_item(parent)
    return {
        **{field: dumped.get(field) for field in _CONTRACT_FIELDS},
        "effective_rubric": rubric.model_dump(mode="json") if rubric is not None else None,
        "source_family": surface_group_id(parent),
        # Only when set, so every other parent's contract view is unchanged.
        **({"required_method": dumped["required_method"]} if dumped.get("required_method") else {}),
    }


def judged_inputs(vault: LoadedVault, parent: PracticeItem, family: ActivityFamily) -> dict[str, Any]:
    """The parent/family revisions and effective rubric a family run is judged against.

    Persisted on every candidate (``pf_candidates.judged_inputs_json``) when the
    run starts; publication recomputes it under the vault mutation lock and
    refuses a selection whose inputs changed (an edited rubric, facets or
    family contract, or a family undo that removed the parent).
    """
    rubric = vault.rubric_for_item(parent)
    return {
        "version": JUDGED_INPUTS_VERSION,
        "parent_item_id": parent.id,
        "parent_input_hash": content_key(_contract_view(vault, parent)),
        "effective_rubric_hash": content_key(rubric.model_dump(mode="json") if rubric is not None else None),
        "parent_membership": {"family_id": parent.family_id, "variant_relation": parent.variant_relation},
        "family_id": family.id,
        "family_revision": content_key({"purpose": family.purpose, "learning_object_id": family.learning_object_id,
                                        "idea_statement": family.idea_statement,
                                        "retrieval_target": family.retrieval_target}),
    }


def stale_inputs(vault: LoadedVault, row: Mapping[str, Any]) -> list[str]:
    """The judged inputs that no longer hold (empty when the selection is current)."""
    try:
        stored = json.loads(row.get("judged_inputs_json") or "{}")
    except ValueError:
        stored = {}
    if stored.get("version") != JUDGED_INPUTS_VERSION:
        return ["judged_inputs_missing"]
    parent = vault.practice_items.get(row["parent_item_id"])
    family = vault.activity_families.get(row["family_id"])
    if parent is None or family is None:
        return ["parent_or_family_missing"]
    current = judged_inputs(vault, parent, family)
    return sorted(key for key, value in current.items() if stored.get(key) != value)


class StaleSelection(PublishRefused):
    """The selection was judged against a parent or family that has since changed."""


def publish_candidate(vault: LoadedVault, repository: Repository, candidate_id: str, *,
                      clock: Clock | None = None) -> tuple[LoadedVault, str]:
    """Publish one selected, verified candidate; idempotent after a crash.

    Runs under the shared vault mutation lock and reloads the vault inside it,
    so the parent contract and family it copies are the ones the judges saw
    (else :class:`StaleSelection`). Returns the refreshed vault and the
    published item id. The caller checks the daily cap and holds the PF run
    lock.
    """
    if not vault.config.pf.generation_enabled:
        raise PublishRefused("pf.generation_enabled is off")
    with vault_mutation_lock(vault.root, purpose="pf_publish"):
        return _publish_locked(load_vault(vault.root), repository, candidate_id, clock=clock)


def _publish_locked(vault: LoadedVault, repository: Repository, candidate_id: str, *,
                    clock: Clock | None) -> tuple[LoadedVault, str]:
    with repository.connection() as connection:
        row = load_candidate(connection, candidate_id)
    if row is None:
        raise PublishRefused(f"Unknown candidate {candidate_id}")
    if row["status"] == "published":
        # Recovery after a crash between the published mark and scheduling
        # initialization: initialize only when absent, never overwrite.
        item = vault.practice_items.get(row["published_item_id"])
        if item is not None:
            with repository.connection() as connection:
                _record_variant_key_check(connection, item, row, now_iso=utc_now_iso(clock))
                connection.commit()
            _initialize_scheduling(repository, item, clock)
        return vault, row["published_item_id"]
    if row["verification"] != "verified":
        raise PublishRefused("An unverified reference is never published")
    if row["generation_path"] == "single_shot" or row["status"] != "selected":
        raise PublishRefused(f"Candidate is {row['status']} on the {row['generation_path']} path")
    with repository.connection() as connection:
        verdicts = candidate_verdicts(connection, [candidate_id])[candidate_id]
    _check_ledger(row, verdicts)
    item_id = published_item_id(candidate_id)
    now_iso = utc_now_iso(clock)
    decision_id = "pfpub_" + content_key([candidate_id, row["content_hash"], PUBLISH_POLICY_VERSION])
    with repository.connection() as connection:
        decided = connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (decision_id,)).fetchone()
    if decided is None or item_id not in vault.practice_items:
        # Only a publication whose item file is already written (a crash after
        # the decision) resumes as is; anything else copies the parent's
        # contract now, so the judged inputs must still hold.
        changed = stale_inputs(vault, row)
        if changed:
            _refuse_stale(repository, row, changed, now_iso)
            raise StaleSelection(f"The parent or family changed since judging: {', '.join(changed)}")
    parent = vault.practice_items.get(row["parent_item_id"])
    family = vault.activity_families.get(row["family_id"])
    if parent is None or family is None:
        raise PublishRefused("The parent item or family no longer exists")
    try:
        payload = build_item_payload(vault, parent, row, item_id=item_id, now_iso=now_iso)
    except VariantContradictsRequiredMethod as exc:
        _refuse_contradiction(repository, row, str(exc), now_iso)
        raise
    PracticeItem.model_validate(payload)
    with repository.connection() as connection:
        if decided is None:
            append_judgment(
                connection, id=decision_id, task="pf_publish", left_kind="pf_candidate",
                left_id=candidate_id, right_kind="practice_item", right_id=item_id,
                judge="verifier", prompt_version=PUBLISH_POLICY_VERSION,
                input_hash=row["content_hash"], verdict="publish",
                rationale=json.dumps({
                    "verification": row["verification"],
                    "verification_check": row["verification_check"],
                    "filters": dict(sorted(verdicts["filters"].items())),
                    "verdict_source": "judgment_ledger",
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
        # The variant's own verification, bound to the content it was
        # published with, commits with the published mark (F11).
        _record_variant_key_check(connection, item, row, now_iso=now_iso, decision_id=decision_id)
        update_candidate(connection, candidate_id, status="published", published_item_id=item_id,
                         published_at=now_iso, updated_at=now_iso)
    _initialize_scheduling(repository, item, clock)
    try:
        repository.bump_queue_revision(clock=clock)
    except Exception:  # noqa: BLE001 - queue nudging never blocks publication
        _LOGGER.warning("failed to bump queue revision after PF publication", exc_info=True)
    return vault, item_id


def _record_variant_key_check(connection: Any, item: PracticeItem, row: Mapping[str, Any], *, now_iso: str,
                              decision_id: str | None = None) -> str | None:
    """A published variant of a textbook exercise records PF's verification of
    it as a reference-key check bound to its own content (idempotent).

    The variant carries ``canonical_exercise`` (``variant_of``), so the C3
    gate reads it as an exercise import; without this row its key would read
    ``model_answer``. The parent's checks are never inherited: what is bound
    is this candidate's verification and this item's content hash."""

    from learnloop.db.stores.source_service import insert_key_check, reference_content_hash

    if getattr(item, "canonical_exercise", None) is None or row.get("verification") != "verified":
        return None
    check = str(row.get("verification_check") or "")
    status = PF_KEY_STATUS.get(check)
    if status is None or connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='reference_key_checks'").fetchone() is None:
        return None
    content_hash = reference_content_hash(item)
    check_id = "rkc_pf_" + content_key([row["id"], content_hash])[:32]
    if connection.execute("SELECT 1 FROM reference_key_checks WHERE id=?", (check_id,)).fetchone() is not None:
        return check_id
    insert_key_check(
        connection, id=check_id, practice_item_id=item.id, content_hash=content_hash, key_status=status,
        rung=f"pf:{check}", trigger="verify", started_at=now_iso, created_at=now_iso,
        verification={"source": "pf_publish", "candidate_id": row["id"], "verification_check": check,
                      "candidate_content_hash": row.get("content_hash"), "publish_decision_id": decision_id},
        ledger_ids=[decision_id] if decision_id else [],
    )
    return check_id


def _refuse_stale(repository: Repository, row: Mapping[str, Any], changed: list[str], now_iso: str) -> None:
    """Ledger the refusal and retire the selection from the backlog (regenerate to retry)."""
    with repository.connection() as connection:
        refusal_id = "pfstale_" + content_key([row["id"], row["judged_inputs_json"], changed, PUBLISH_POLICY_VERSION])
        if connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (refusal_id,)).fetchone() is None:
            append_judgment(
                connection, id=refusal_id, task="pf_publish", left_kind="pf_candidate", left_id=row["id"],
                judge="verifier", prompt_version=PUBLISH_POLICY_VERSION,
                input_hash=content_key([row["content_hash"], row["judged_inputs_json"]]), verdict="refuse_stale",
                rationale=json.dumps({"changed": changed, "family_id": row["family_id"],
                                      "parent_item_id": row["parent_item_id"]}, sort_keys=True),
                created_at=now_iso,
            )
        update_candidate(connection, row["id"], status="rejected", rejection_filter="stale_judged_inputs",
                         updated_at=now_iso)


def _refuse_contradiction(repository: Repository, row: Mapping[str, Any], reason: str, now_iso: str) -> None:
    """Ledger the refusal and reject the candidate (re-review F10; regenerate to retry)."""
    with repository.connection() as connection:
        refusal_id = "pfmethod_" + content_key([row["id"], row["content_hash"], PUBLISH_POLICY_VERSION])
        if connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (refusal_id,)).fetchone() is None:
            append_judgment(
                connection, id=refusal_id, task="pf_publish", left_kind="pf_candidate", left_id=row["id"],
                judge="verifier", prompt_version=PUBLISH_POLICY_VERSION, input_hash=row["content_hash"],
                verdict="refuse_contradicts_required_method",
                rationale=json.dumps({"reason": reason, "family_id": row["family_id"],
                                      "parent_item_id": row["parent_item_id"]}, sort_keys=True),
                created_at=now_iso,
            )
        update_candidate(connection, row["id"], status="rejected", rejection_filter="required_method_contradicted",
                         updated_at=now_iso)


def _check_ledger(row: dict[str, Any], verdicts: dict[str, Any]) -> None:
    """Publication reads the authoritative verdicts (§5.8), never workflow JSON.

    The ledger must show a verified reference, no failing filter, a passing
    freshness gate and structure check, and, for a relation that keeps the
    parent's trace contract, a structure check that confirmed the checkpoint
    sequence.
    """
    if not verdict_verified(verdicts, row["generation_path"]):
        raise PublishRefused("The ledger holds no verified reference for this candidate")
    if not verdict_survived(verdicts) or verdicts["filters"].get("structure_check") != "pass":
        raise PublishRefused("The ledger does not show every filter passed")
    relation = row["final_relation"] or row["declared_relation"]
    if relation in TRACE_RELATIONS:
        detail = verdicts["filter_details"].get("structure_check") or {}
        if detail.get("checkpoint_sequence_preserved") is not True or detail.get("judged_relation") not in TRACE_RELATIONS:
            raise PublishRefused(f"A final {relation} needs a passing checkpoint-preservation check")


def _initialize_scheduling(repository: Repository, item: PracticeItem, clock: Clock | None) -> None:
    """Fresh scheduling state, as the next state sync would derive it, only when absent.

    A retried publication may find practice the sidecar already recorded for
    the item (it discovered the file before the crash); that row is kept.
    """
    repository.initialize_practice_item_state(item.id, content_hash=practice_item_hash(item), clock=clock)


def publish_selected(vault: LoadedVault, repository: Repository, candidate_ids: list[str], *,
                     clock: Clock | None = None) -> tuple[LoadedVault, dict[str, Any]]:
    """Publish in order while today's cap allows; the rest stay ``selected``."""
    published: list[str] = []
    capped: list[str] = []
    stale: list[str] = []
    refused: list[str] = []
    for candidate_id in candidate_ids:
        with repository.connection() as connection:
            row = load_candidate(connection, candidate_id)
        if row is None or row["status"] != "selected":
            continue
        if remaining_publish_slots(vault, repository, clock) <= 0:
            capped.append(candidate_id)
            continue
        try:
            vault, item_id = publish_candidate(vault, repository, candidate_id, clock=clock)
        except StaleSelection:
            stale.append(candidate_id)
            continue
        except VariantContradictsRequiredMethod:
            refused.append(candidate_id)
            continue
        published.append(item_id)
    return vault, {"published_item_ids": published, "capped_candidates": len(capped),
                   "stale_candidates": len(stale), "refused_candidates": len(refused),
                   "cap": vault.config.pf.max_published_per_day}


__all__ = [
    "JUDGED_INPUTS_VERSION", "PF_TAG", "PUBLISH_POLICY_VERSION", "TRACE_RELATIONS", "PublishRefused",
    "StaleSelection", "VariantContradictsRequiredMethod", "build_item_payload", "judged_inputs", "publish_candidate",
    "publish_selected", "published_item_id", "remaining_publish_slots", "stale_inputs", "utc_day_bounds",
]
