"""What a named gap does, each behind its own switch, each undoable by one tap.

* **A matched prerequisite that is not declared:** after a "needed for this
  item?" yes from the authoritative judge, a ``prerequisite`` edge from its
  concept to the item LO's concept, refused when it would close a cycle,
  labelled as added from the learner's text (``learner_text_gap_v1``).
* **A missing prerequisite:** one concept, one LO and the edge, written live
  in the asking item's subject with ``learner_text_gap_v1`` provenance, seeded
  with one practice item through the question-promotion path, with a light
  commitment (one delayed check) placement reads.
* **A stated belief:** a sighting on the registry entry it matched, or a new
  holding-pen candidate. Promotion stays with T1's rule.
* **A sooner check (``mvp-0.13``):** a matched prerequisite on an LO assumed
  known or in maintenance brings its next check forward.

Undo: an edge is deleted; a created LO goes dormant (its items stop being
served) and its edge is deleted; "not what I meant" on a belief is a
``learner_card`` ``different`` verdict and withdraws a candidate this gap
created. Nothing here writes evidence, mastery or certification (G13).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
import re
from typing import Any

from learnloop.algorithm_versions import LEARNER_TEXT_GAP_VERSIONS
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.text_gaps.contract import PROVENANCE_MECHANISM, SAME_BELIEF_TASK, LearnerText
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault_lock import vault_mutation_lock

_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass
class ActionOutcome:
    action: str
    target_kind: str | None = None
    target_id: str | None = None
    target_subject_id: str | None = None
    match_basis: str | None = None
    edge_id: str | None = None
    created_concept_id: str | None = None
    created_learning_object_id: str | None = None
    seed_practice_item_id: str | None = None
    seed_status: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def day_start(now_iso: str) -> str:
    return parse_utc(now_iso).strftime("%Y-%m-%dT00:00:00Z")


# -- the prerequisite graph ----------------------------------------------------------------


def prerequisite_graph(vault: LoadedVault) -> dict[str, set[str]]:
    """Concept -> concepts that build on it (``prerequisite`` edges and LO declarations)."""

    graph: dict[str, set[str]] = defaultdict(set)
    for edge in vault.edges:
        if edge.relation_type == "prerequisite":
            graph[edge.source].add(edge.target)
    for learning_object in vault.learning_objects.values():
        for prerequisite in learning_object.prerequisites:
            graph[prerequisite].add(learning_object.concept)
    return graph


def would_cycle(vault: LoadedVault, prerequisite_concept: str, dependent_concept: str) -> bool:
    """Would ``prerequisite -> dependent`` close a cycle (or point a concept at itself)?"""

    if prerequisite_concept == dependent_concept:
        return True
    graph = prerequisite_graph(vault)
    seen, stack = set(), [dependent_concept]
    while stack:
        concept = stack.pop()
        if concept == prerequisite_concept:
            return True
        if concept in seen:
            continue
        seen.add(concept)
        stack.extend(graph.get(concept, ()))
    return False


def declared_prerequisite(vault: LoadedVault, prerequisite_lo: str, dependent_lo: str) -> bool:
    from learnloop.placement.state import prerequisite_learning_objects

    return prerequisite_lo in prerequisite_learning_objects(vault, dependent_lo)


def add_prerequisite_edge(
    root: Path, vault: LoadedVault, *, prerequisite_lo: str, dependent_lo: str, text: LearnerText,
    rationale: str, clock: Clock | None = None,
) -> tuple[str | None, str]:
    """Write the edge; returns (edge id, status) with status ``added`` or why not."""

    from learnloop.vault.writer import upsert_concept_edge

    prerequisite = vault.learning_objects.get(prerequisite_lo)
    dependent = vault.learning_objects.get(dependent_lo)
    if prerequisite is None or dependent is None:
        return None, "missing_learning_object"
    if would_cycle(vault, prerequisite.concept, dependent.concept):
        return None, "refused_cycle"
    now = utc_now_iso(clock)
    edge_id = f"edge_ltg_{new_ulid().lower()}"
    with vault_mutation_lock(vault.root, purpose="learner_text_gap_edge"):
        upsert_concept_edge(
            root,
            {
                "id": edge_id,
                "relation_type": "prerequisite",
                "source": prerequisite.concept,
                "target": dependent.concept,
                "strength": 1.0,
                "rationale": f"Added from your question ({PROVENANCE_MECHANISM}): {rationale}"[:500],
                "provenance": {"mechanism": PROVENANCE_MECHANISM, "learner_text": text.subject_key},
                "created_at": now,
                "updated_at": now,
            },
            clock=clock,
        )
    return edge_id, "added"


def delete_edge(root: Path, edge_id: str) -> bool:
    from learnloop.vault.writer import delete_concept_edge

    with vault_mutation_lock(root, purpose="learner_text_gap_undo"):
        return delete_concept_edge(root, edge_id) is not None


# -- a missing prerequisite ------------------------------------------------------------------


def slug(text: str, *, limit: int = 40) -> str:
    return (_SLUG.sub("_", text.lower()).strip("_") or "prerequisite")[:limit].strip("_")


def creations_today(repository: Repository, *, now_iso: str) -> int:
    """Kept creations since today's UTC midnight (the daily cap counts these)."""

    from learnloop.diagnosis.text_gaps.candidates import created_today

    return len(created_today(repository, day_start=day_start(now_iso)))


def subject_for_creation(vault: LoadedVault, text: LearnerText, shortlist_subjects: list[Any]) -> str | None:
    """The asking item's subject, else the subject the shortlist points to. Never new."""

    if text.subject_id and text.subject_id in vault.subjects:
        return text.subject_id
    for subject in shortlist_subjects:
        for candidate in subject.scope.get("subjects") or ():
            if candidate in vault.subjects:
                return str(candidate)
    return None


def write_created_prerequisite(
    root: Path, vault: LoadedVault, repository: Repository, *, draft: Any, subject_id: str,
    dependent_lo: str | None, text: LearnerText, clock: Clock | None = None,
    progress: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the concept, the LO and (when there is an asking LO) the edge.

    ``progress`` is what an earlier attempt of the same job already wrote
    (job payload): those are reused, never written twice.
    """

    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.writer import upsert_concept, upsert_learning_object

    done = dict(progress or {})
    now = utc_now_iso(clock)
    suffix = new_ulid().lower()[-8:]
    concept_id = done.get("concept_id") or f"{slug(draft.concept_title)}_{suffix}"
    learning_object_id = done.get("learning_object_id") or f"lo_ltg_{slug(draft.learning_object_title)}_{suffix}"
    provenance = {"origin": "codex_proposal", "source_refs": [], "mechanism": PROVENANCE_MECHANISM,
                  "learner_text": text.subject_key}
    with vault_mutation_lock(vault.root, purpose="learner_text_gap_create"):
        if concept_id not in vault.concepts:
            upsert_concept(
                root, concept_id,
                {
                    "title": draft.concept_title.strip()[:200],
                    "type": draft.concept_type,
                    "aliases": [],
                    "description": draft.concept_description.strip()[:2000],
                    "tags": [PROVENANCE_MECHANISM],
                    "created_at": now,
                    "updated_at": now,
                },
                clock=clock,
            )
        if learning_object_id not in vault.learning_objects:
            upsert_learning_object(
                root,
                {
                    "id": learning_object_id,
                    "title": draft.learning_object_title.strip()[:200],
                    "subjects": [subject_id],
                    "concept": concept_id,
                    "knowledge_type": draft.knowledge_type,
                    "status": "active",
                    "summary": draft.learning_object_statement.strip()[:2000],
                    "prerequisites": [],
                    "confusables": [],
                    "tags": [PROVENANCE_MECHANISM],
                    "provenance": provenance,
                    "created_at": now,
                    "updated_at": now,
                },
                clock=clock,
            )
    done.update(concept_id=concept_id, learning_object_id=learning_object_id)
    vault = load_vault(root)
    if dependent_lo is not None and not done.get("edge_status"):
        edge_id, status = add_prerequisite_edge(
            root, vault, prerequisite_lo=learning_object_id, dependent_lo=dependent_lo, text=text,
            rationale=draft.edge_rationale, clock=clock,
        )
        done.update(edge_id=edge_id, edge_status=status)
        vault = load_vault(root)
    sync_vault_state(vault, repository, clock=clock)
    return done


def grounding_learning_object_ids(text: LearnerText) -> list[str]:
    return list(text.anchor_learning_object_ids)


def seed_from_question(
    root: Path, *, question_event_id: str, learning_object_id: str, tutor_client: Any, authoring_client: Any,
    grounding: list[str], clock: Clock | None = None,
) -> tuple[str | None, str]:
    """One practice item made from the question and the tutor's answer.

    Through the existing question-promotion path (``tutor/promotions.py``),
    targeted at the created LO and grounded in the asking LO's source notes.
    Returns (practice item id, ``auto_apply`` | ``review_required`` |
    ``already_promoted`` | ``no_item``).
    """

    from learnloop.tutor.promotions import PromotionNoItemError, promote_tutor_question

    try:
        row = promote_tutor_question(
            root, tutor_client, event_id=question_event_id, intent="practice",
            learning_object_id=learning_object_id, authoring_client=authoring_client,
            grounding_learning_object_ids=grounding, clock=clock,
        )
    except PromotionNoItemError:
        return None, "no_item"
    created_item = row.get("created_practice_item_id")
    if row.get("created_learning_object_id") not in (None, learning_object_id) or (
        row.get("existing_practice_item_id") and not created_item
    ):
        return None, "already_promoted"
    vault = load_vault(root)
    item = vault.practice_items.get(str(created_item)) if created_item else None
    if created_item and item is not None and item.learning_object_id != learning_object_id:
        return None, "already_promoted"
    return (str(created_item) if created_item else None), str(row.get("route") or "review_required")


def undo_creation(root: Path, repository: Repository, gap: Mapping[str, Any], *, clock: Clock | None = None) -> dict[str, Any]:
    """The created LO goes dormant (its items are no longer served); its edge goes."""

    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.writer import upsert_learning_object

    vault = load_vault(root)
    detail: dict[str, Any] = {}
    learning_object_id = gap.get("created_learning_object_id")
    if learning_object_id and learning_object_id in vault.learning_objects:
        with vault_mutation_lock(vault.root, purpose="learner_text_gap_undo"):
            upsert_learning_object(root, {"id": learning_object_id, "status": "dormant",
                                          "subjects": vault.learning_objects[learning_object_id].subjects},
                                   clock=clock)
        detail["learning_object"] = "dormant"
    if gap.get("edge_id"):
        detail["edge_deleted"] = delete_edge(root, str(gap["edge_id"]))
    sync_vault_state(load_vault(root), repository, clock=clock)
    return detail


# -- beliefs -----------------------------------------------------------------------------------


def record_belief(
    vault: LoadedVault, repository: Repository, *, text: LearnerText, statement: str,
    matched: Mapping[str, Any] | None, clock: Clock | None = None,
) -> ActionOutcome:
    """A sighting on the matched entry, or a new holding-pen candidate."""

    from learnloop.diagnosis.misconceptions import normalize_text

    anchor = text.anchor
    if anchor is None or anchor not in vault.learning_objects:
        return ActionOutcome("unplaced", detail={"reason": "no single learning object to hold the belief"})
    subject = vault.learning_objects[anchor].subjects[0] if vault.learning_objects[anchor].subjects else None
    if matched is not None:
        registry_kind = str(matched["registry_kind"])
        registry_id = str(matched["registry_id"])
        detail: dict[str, Any] = {"sighting_of": f"{registry_kind}:{registry_id}"}
        if registry_kind == "candidate" and repository.causal_hypothesis(registry_id) is None:
            row = repository.misconception_candidate_by_id(registry_id)
            if row is not None and str(row.get("status") or "candidate") == "candidate":
                repository.update_misconception_candidate(
                    registry_id, occurrence_count=int(row.get("occurrence_count") or 0) + 1, clock=clock,
                )
                detail["occurrence_count"] = int(row.get("occurrence_count") or 0) + 1
        return ActionOutcome(
            "belief_sighting", target_kind=registry_kind, target_id=registry_id, target_subject_id=subject,
            match_basis="judge", detail=detail,
        )
    learning_object = vault.learning_objects[anchor]
    candidate_id = repository.insert_misconception_candidate(
        learning_object_id=anchor,
        statement=statement,
        statement_normalized=normalize_text(statement),
        concept_id=learning_object.concept,
        occurrence_count=1,
        severity=0.0,
        mechanism=None,
        clock=clock,
    )
    return ActionOutcome(
        "belief_candidate", target_kind="candidate", target_id=candidate_id, target_subject_id=subject,
        match_basis="new", detail={"holding_pen": "new_candidate", "created_by_gap": True},
    )


def not_this_belief(repository: Repository, gap: Mapping[str, Any], *, clock: Clock | None = None) -> dict[str, Any]:
    """The learner's "not what I meant": a ``learner_card`` ``different`` verdict."""

    from learnloop.ai.execution import content_key

    target_kind, target_id = gap.get("target_kind"), gap.get("target_id")
    detail: dict[str, Any] = {}
    if target_kind in ("durable", "candidate") and target_id:
        with repository.atomic():
            detail["judgment_id"] = append_judgment(
                repository.connection(), task=SAME_BELIEF_TASK, left_kind="learner_gap",
                left_id=f"{gap['source_kind']}:{gap['source_id']}", right_kind="misconception",
                right_id=f"{target_kind}:{target_id}", judge="learner_card",
                input_hash=content_key({"gap": gap["id"], "target": [target_kind, target_id]}),
                verdict="different", rationale="The learner tapped \"not what I meant\".",
                created_at=utc_now_iso(clock),
            )
        if target_kind == "candidate" and (gap.get("detail") or {}).get("created_by_gap"):
            row = repository.misconception_candidate_by_id(str(target_id))
            if row is not None and str(row.get("status") or "") == "candidate" and repository.causal_hypothesis(str(target_id)) is None:
                repository.update_misconception_candidate(str(target_id), status="withdrawn", clock=clock)
                detail["candidate"] = "withdrawn"
    return detail


# -- the sooner check (mvp-0.13) ---------------------------------------------------------


def sooner_check_active(vault: LoadedVault) -> bool:
    config = vault.config.learner_text_gaps
    return (
        vault.config.algorithms.algorithm_version in LEARNER_TEXT_GAP_VERSIONS
        and bool(config.enabled)
        and bool(config.sooner_check_enabled)
    )


def advance_check(
    vault: LoadedVault, repository: Repository, *, learning_object_id: str, now_iso: str,
) -> dict[str, Any] | None:
    """The advance row to write for a matched prerequisite, or None.

    Only for an LO assumed known (an open assumption) or in maintenance, only
    when the advanced due date (``sooner_check_delay_hours`` after the gap) is
    earlier than the check it replaces, and never past an earlier advance
    still waiting.
    """

    from learnloop.placement.state import load_placement_state, placement_active

    if not sooner_check_active(vault) or not placement_active(vault):
        return None
    state = load_placement_state(vault, repository, now_iso=now_iso)
    delay = timedelta(hours=int(vault.config.learner_text_gaps.sooner_check_delay_hours))
    advanced_due = _iso((parse_utc(now_iso) + delay).replace(microsecond=0))
    assumption = state.open_by_lo.get(learning_object_id)
    intent = state.intent_by_lo.get(learning_object_id)
    if assumption is not None:
        original = assumption.first_review_due
        row = {"intent": "assumed", "assumption_id": assumption.id, "original_due": original}
    elif intent is not None and intent.intent == "maintenance":
        dues = [
            state_row.due_at for item_id, state_row in repository.practice_item_states().items()
            if state_row.due_at and (item := vault.practice_items.get(item_id)) is not None
            and item.learning_object_id == learning_object_id
        ]
        pending = state.gap_check_due_by_lo.get(learning_object_id)
        if pending is not None:
            return None
        original = min(dues) if dues else None
        row = {"intent": "maintenance", "assumption_id": intent.assumption_id, "original_due": original}
    else:
        return None
    if original is not None and advanced_due >= str(original):
        return None
    return {**row, "learning_object_id": learning_object_id, "advanced_due": advanced_due,
            "algorithm_version": vault.config.algorithms.algorithm_version}


def persist_check_advance(connection: Any, advance: Mapping[str, Any], *, gap_id: str, now_iso: str) -> str:
    return store.insert_check_advance(connection, {**advance, "gap_id": gap_id, "created_at": now_iso})


def commitment_row(vault: LoadedVault, *, learning_object_id: str, practice_item_id: str | None, now_iso: str) -> dict[str, Any]:
    days = int(vault.config.learner_text_gaps.seed_check_delay_days)
    due = _iso((parse_utc(now_iso) + timedelta(days=days)).replace(microsecond=0))
    return {"learning_object_id": learning_object_id, "practice_item_id": practice_item_id,
            "first_review_due": due, "algorithm_version": vault.config.algorithms.algorithm_version}


# -- undo -----------------------------------------------------------------------------------


REVERSALS = {
    "undo_edge": ("matched_prerequisite",),
    "undo_creation": ("created_prerequisite",),
    "not_this_belief": ("belief_sighting", "belief_candidate"),
}


class UndoError(ValueError):
    pass


def reverse_gap(
    root: Path, repository: Repository, gap_id: str, reversal: str, *, actor: str = "learner",
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Apply one reversal (idempotent: a repeated tap changes nothing)."""

    if reversal not in REVERSALS:
        raise UndoError(f"unknown reversal {reversal!r}")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        gap = store.gap(connection, gap_id)
        existing = [row for row in store.reversals(connection, [gap_id]) if row["reversal"] == reversal]
    if gap is None:
        raise UndoError(f"learner-text gap {gap_id} was not found")
    if gap["action"] not in REVERSALS[reversal]:
        raise UndoError(f"a {gap['action']} gap cannot take {reversal}")
    if reversal == "undo_edge" and not gap.get("edge_id"):
        raise UndoError("this gap added no edge")
    if existing:
        return {"gap_id": gap_id, "reversal": reversal, "status": "already_reversed"}
    if reversal == "undo_edge":
        detail = {"edge_deleted": delete_edge(root, str(gap["edge_id"]))}
        from learnloop.substrate.state_sync import sync_vault_state

        sync_vault_state(load_vault(root), repository, clock=clock)
    elif reversal == "undo_creation":
        detail = undo_creation(root, repository, gap, clock=clock)
    else:
        detail = not_this_belief(repository, gap, clock=clock)
    with repository.atomic():
        store.insert_reversal(
            repository.connection(), gap_id=gap_id, reversal=reversal, actor=actor,
            created_at=utc_now_iso(clock), detail=detail,
        )
    repository.bump_queue_revision(clock=clock)
    return {"gap_id": gap_id, "reversal": reversal, "status": "reversed", "detail": detail}


__all__ = [
    "ActionOutcome",
    "REVERSALS",
    "UndoError",
    "add_prerequisite_edge",
    "advance_check",
    "commitment_row",
    "creations_today",
    "day_start",
    "declared_prerequisite",
    "delete_edge",
    "not_this_belief",
    "persist_check_advance",
    "prerequisite_graph",
    "record_belief",
    "reverse_gap",
    "seed_from_question",
    "slug",
    "sooner_check_active",
    "subject_for_creation",
    "undo_creation",
    "would_cycle",
    "write_created_prerequisite",
]
