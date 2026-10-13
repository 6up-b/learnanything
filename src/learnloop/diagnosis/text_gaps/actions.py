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
* **A sooner check (``mvp-0.16``):** a matched prerequisite on an LO assumed
  known or in maintenance brings its next check forward.

Undo: an edge is deleted; a created LO goes dormant (its items stop being
served) and its edge is deleted; "not what I meant" on a belief is a
``learner_card`` ``different`` verdict and withdraws a candidate this gap
created. Every reversal is also a verdict in ``judgment_ledger`` (judge
``learner_card``, or ``owner`` for ``learnloop gaps undo``): an undone edge or
creation is a ``no`` on ``prerequisite_needed`` (Codex review F9). Nothing
here writes evidence, mastery or certification (G13).

Vault writes are crash-safe (F3): ids derive from the learner text (and the
draft), so a retried job finds what an earlier attempt wrote instead of
writing a second copy; the edge cycle check is re-run on the file inside the
vault lock (F10).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from contextlib import closing
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
import re
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.algorithm_versions import LEARNER_TEXT_GAP_VERSIONS
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.text_gaps.contract import (
    NEEDED_TASK,
    PROVENANCE_MECHANISM,
    SAME_BELIEF_TASK,
    LearnerText,
)
from learnloop.ids import new_ulid
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.promotions import PromotionNoItemError, promote_tutor_question
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ConceptEdge, LoadedVault, RelationsFile
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml
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
    #: Database writes that commit in the ledger row's transaction (F3).
    writes: list[Callable[[], Any]] = field(default_factory=list)


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def day_start(now_iso: str) -> str:
    return parse_utc(now_iso).strftime("%Y-%m-%dT00:00:00Z")


# -- the prerequisite graph ----------------------------------------------------------------


def prerequisite_graph(vault: LoadedVault, edges: Iterable[ConceptEdge] | None = None) -> dict[str, set[str]]:
    """Concept -> concepts that build on it (``prerequisite`` edges and LO declarations).

    ``edges`` defaults to the loaded vault's (which a switched-off
    learner-text gap edge is not part of); the cycle check passes the file's.
    """

    graph: dict[str, set[str]] = defaultdict(set)
    for edge in vault.edges if edges is None else edges:
        if edge.relation_type == "prerequisite":
            graph[edge.source].add(edge.target)
    for learning_object in vault.learning_objects.values():
        for prerequisite in learning_object.prerequisites:
            graph[prerequisite].add(learning_object.concept)
    return graph


def edges_on_disk(vault: LoadedVault) -> list[ConceptEdge]:
    """Every edge in ``concepts/relations.yaml`` as it is now, including the
    learner-text gap edges a switch keeps out of the loaded vault."""

    path = VaultPaths(vault.root, vault.config).relations_path
    if not path.exists():
        return []
    return list(RelationsFile.model_validate(read_yaml(path)).edges)


def would_cycle(
    vault: LoadedVault, prerequisite_concept: str, dependent_concept: str, *, edges: Iterable[ConceptEdge] | None = None,
) -> bool:
    """Would ``prerequisite -> dependent`` close a cycle (or point a concept at itself)?"""

    if prerequisite_concept == dependent_concept:
        return True
    graph = prerequisite_graph(vault, edges)
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


def _hash(*parts: Any) -> str:
    return content_key(list(parts))[:12]


def edge_id_for(text: LearnerText, prerequisite_lo: str, dependent_lo: str) -> str:
    """The edge a learner text adds (deterministic: a retry finds it, F3)."""

    return f"edge_ltg_{_hash(text.subject_key, prerequisite_lo, dependent_lo)}"


def add_prerequisite_edge(
    root: Path, vault: LoadedVault, *, prerequisite_lo: str, dependent_lo: str, text: LearnerText,
    rationale: str, clock: Clock | None = None, edge_id: str | None = None, origin: str = "match",
) -> tuple[str | None, str]:
    """Write the edge; returns (edge id, status) with status ``added`` or why not.

    Inside the vault lock the vault is reloaded and the cycle re-checked on
    the relations file as it is now (F10): the reading started minutes
    earlier, and the graph editor, the CLI or another worker may have added
    an edge since. An edge this text already wrote (same id) is ``added``.
    ``origin`` (``match`` | ``creation``) names the switch that keeps it in
    effect (``vault.lifecycle.learner_text_gap_edge_in_effect``).
    """

    from learnloop.vault.writer import upsert_concept_edge

    edge_id = edge_id or edge_id_for(text, prerequisite_lo, dependent_lo)
    now = utc_now_iso(clock)
    with vault_mutation_lock(vault.root, purpose="learner_text_gap_edge"):
        fresh = load_vault(root)
        on_disk = edges_on_disk(fresh)
        if any(edge.id == edge_id for edge in on_disk):
            return edge_id, "added"
        prerequisite = fresh.learning_objects.get(prerequisite_lo)
        dependent = fresh.learning_objects.get(dependent_lo)
        if prerequisite is None or dependent is None:
            return None, "missing_learning_object"
        if would_cycle(fresh, prerequisite.concept, dependent.concept, edges=on_disk):
            return None, "refused_cycle"
        upsert_concept_edge(
            root,
            {
                "id": edge_id,
                "relation_type": "prerequisite",
                "source": prerequisite.concept,
                "target": dependent.concept,
                "strength": 1.0,
                "rationale": f"Added from your question ({PROVENANCE_MECHANISM}): {rationale}"[:500],
                "provenance": {"mechanism": PROVENANCE_MECHANISM, "learner_text": text.subject_key,
                               "origin": origin},
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


def subject_for_creation(vault: LoadedVault, text: LearnerText) -> str | None:
    """The asking item's subject; never a new or an inferred one.

    Only a grounded subject was searched for duplicates (candidates are
    restricted to it), so a text without one creates nothing (F4).
    """

    if text.subject_id and text.subject_id in vault.subjects:
        return text.subject_id
    return None


def creation_ids(text: LearnerText, draft: Any, *, dependent_lo: str | None) -> dict[str, Any]:
    """The concept, LO and edge ids a creation writes: derived from the text
    and the draft, so a retry of the same job names the same entities (F3)."""

    suffix = _hash(text.subject_key)[:8]
    learning_object_id = f"lo_ltg_{slug(draft.learning_object_title)}_{suffix}"
    return {
        "concept_id": f"{slug(draft.concept_title)}_{suffix}",
        "learning_object_id": learning_object_id,
        "edge_id": edge_id_for(text, learning_object_id, dependent_lo) if dependent_lo else None,
    }


def write_created_prerequisite(
    root: Path, repository: Repository, *, draft: Any, subject_id: str, concept_id: str,
    learning_object_id: str, edge_id: str | None, dependent_lo: str | None, text: LearnerText,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Write the concept, the LO and (when there is an asking LO) the edge.

    Idempotent: each entity is looked up by its id first, so a retry after a
    partial write (a failed edge write or state sync) completes it instead of
    writing a second copy. Returns ``edge_id`` and ``edge_status``.
    """

    from learnloop.vault.writer import upsert_concept, upsert_learning_object

    now = utc_now_iso(clock)
    provenance = {"origin": "codex_proposal", "source_refs": [], "mechanism": PROVENANCE_MECHANISM,
                  "learner_text": text.subject_key}
    with vault_mutation_lock(root, purpose="learner_text_gap_create"):
        vault = load_vault(root)
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
    done: dict[str, Any] = {"edge_id": None, "edge_status": "no_asking_learning_object"}
    if dependent_lo is not None:
        written_id, status = add_prerequisite_edge(
            root, load_vault(root), prerequisite_lo=learning_object_id, dependent_lo=dependent_lo, text=text,
            rationale=draft.edge_rationale, clock=clock, edge_id=edge_id, origin="creation",
        )
        done.update(edge_id=written_id, edge_status=status)
    sync_vault_state(load_vault(root), repository, clock=clock)
    return done


def seed_from_question(
    root: Path, *, question_event_id: str, learning_object_id: str, tutor_client: Any, authoring_client: Any,
    clock: Clock | None = None,
) -> tuple[str | None, str]:
    """One practice item made from the question and the tutor's answer.

    Through the existing question-promotion path (``tutor/promotions.py``),
    targeted at the created LO. The created LO has no source notes of its
    own, and the asking LO's notes cover the material that builds on it, not
    the missing prerequisite (that is why it is missing): nothing grounds the
    item authoritatively, so the promotion path's own rule sends it to review
    (Codex review F7). Returns (practice item id, ``auto_apply`` |
    ``review_required`` | ``already_promoted`` | ``no_item``).
    """

    try:
        row = promote_tutor_question(
            root, tutor_client, event_id=question_event_id, intent="practice",
            learning_object_id=learning_object_id, authoring_client=authoring_client, clock=clock,
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
    """A sighting on the matched entry, or a new holding-pen candidate.

    Nothing is written here: the outcome's ``writes`` run in the ledger
    row's transaction, so a retried job never inserts a second candidate or
    counts a sighting twice (F3).
    """

    from learnloop.diagnosis.misconceptions import normalize_text

    anchor = text.anchor
    if anchor is None or anchor not in vault.learning_objects:
        return ActionOutcome("unplaced", detail={"reason": "no single learning object to hold the belief"})
    subject = vault.learning_objects[anchor].subjects[0] if vault.learning_objects[anchor].subjects else None
    if matched is not None:
        registry_kind = str(matched["registry_kind"])
        registry_id = str(matched["registry_id"])
        detail: dict[str, Any] = {"sighting_of": f"{registry_kind}:{registry_id}"}
        outcome = ActionOutcome(
            "belief_sighting", target_kind=registry_kind, target_id=registry_id, target_subject_id=subject,
            match_basis="judge", detail=detail,
        )
        if registry_kind == "candidate" and repository.causal_hypothesis(registry_id) is None:
            row = repository.misconception_candidate_by_id(registry_id)
            if row is not None and str(row.get("status") or "candidate") == "candidate":
                detail["occurrence_count"] = int(row.get("occurrence_count") or 0) + 1

                def sighting() -> None:
                    current = repository.misconception_candidate_by_id(registry_id) or {}
                    repository.update_misconception_candidate(
                        registry_id, occurrence_count=int(current.get("occurrence_count") or 0) + 1, clock=clock,
                    )

                outcome.writes.append(sighting)
        return outcome
    learning_object = vault.learning_objects[anchor]
    candidate_id = new_ulid()

    def candidate() -> None:
        repository.insert_misconception_candidate(
            id=candidate_id,
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
        match_basis="new", detail={"holding_pen": "new_candidate", "created_by_gap": True}, writes=[candidate],
    )


def _reversal_judge(actor: str) -> str:
    return "owner" if actor == "owner" else "learner_card"


def not_this_belief(
    repository: Repository, gap: Mapping[str, Any], *, actor: str = "learner", clock: Clock | None = None,
) -> dict[str, Any]:
    """"Not what I meant": a ``different`` verdict (``learner_card``, or ``owner``)."""

    target_kind, target_id = gap.get("target_kind"), gap.get("target_id")
    detail: dict[str, Any] = {}
    if target_kind in ("durable", "candidate") and target_id:
        who = "The owner reversed it" if actor == "owner" else "The learner tapped \"not what I meant\""
        with repository.atomic():
            detail["judgment_id"] = append_judgment(
                repository.connection(), task=SAME_BELIEF_TASK, left_kind="learner_gap",
                left_id=f"{gap['source_kind']}:{gap['source_id']}", right_kind="misconception",
                right_id=f"{target_kind}:{target_id}", judge=_reversal_judge(actor),
                input_hash=content_key({"gap": gap["id"], "target": [target_kind, target_id]}),
                verdict="different", rationale=f"{who}.",
                created_at=utc_now_iso(clock),
            )
        if target_kind == "candidate" and (gap.get("detail") or {}).get("created_by_gap"):
            row = repository.misconception_candidate_by_id(str(target_id))
            if row is not None and str(row.get("status") or "") == "candidate" and repository.causal_hypothesis(str(target_id)) is None:
                repository.update_misconception_candidate(str(target_id), status="withdrawn", clock=clock)
                detail["candidate"] = "withdrawn"
    return detail


# -- the sooner check (mvp-0.16) ---------------------------------------------------------


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
    # A ``failed`` row names what an earlier attempt of its job had already
    # written (F3), so the owner can still take it back.
    "undo_edge": ("matched_prerequisite", "failed"),
    "undo_creation": ("created_prerequisite", "failed"),
    "not_this_belief": ("belief_sighting", "belief_candidate"),
}


def reversal_verdict(gap: Mapping[str, Any], reversal: str, *, actor: str, created_at: str) -> dict[str, Any] | None:
    """The ``judgment_ledger`` row an undo is (F9): a ``no`` on ``prerequisite_needed``.

    An undone edge says the matched LO is not needed for the asking item; an
    undone creation says the created LO is not. Right side: the practice
    item, else the learner text itself. "Not what I meant" is written by
    :func:`not_this_belief`.
    """

    if reversal == "undo_edge":
        learning_object_id = gap.get("target_id") if gap.get("target_kind") == "learning_object" else None
        learning_object_id = learning_object_id or (gap.get("detail") or {}).get("edge_prerequisite")
        rationale = "removed the link added from the learner's text"
    elif reversal == "undo_creation":
        learning_object_id = gap.get("created_learning_object_id")
        rationale = "undid the prerequisite created from the learner's text"
    else:
        return None
    if not learning_object_id:
        return None
    right = (("practice_item", str(gap["practice_item_id"])) if gap.get("practice_item_id")
             else ("learner_gap", f"{gap['source_kind']}:{gap['source_id']}"))
    who = "The owner" if actor == "owner" else "The learner"
    return {
        "task": NEEDED_TASK, "left_kind": "learning_object", "left_id": str(learning_object_id),
        "right_kind": right[0], "right_id": right[1], "judge": _reversal_judge(actor),
        "input_hash": content_key({"gap": gap["id"], "reversal": reversal}), "verdict": "no",
        "rationale": f"{who} {rationale}.", "created_at": created_at,
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
    if reversal == "undo_creation" and not gap.get("created_learning_object_id"):
        raise UndoError("this gap created nothing")
    if existing:
        return {"gap_id": gap_id, "reversal": reversal, "status": "already_reversed"}
    if reversal == "undo_edge":
        detail = {"edge_deleted": delete_edge(root, str(gap["edge_id"]))}
        sync_vault_state(load_vault(root), repository, clock=clock)
    elif reversal == "undo_creation":
        detail = undo_creation(root, repository, gap, clock=clock)
    else:
        detail = not_this_belief(repository, gap, actor=actor, clock=clock)
    now = utc_now_iso(clock)
    verdict = reversal_verdict(gap, reversal, actor=actor, created_at=now)
    with repository.atomic():
        connection = repository.connection()
        if verdict is not None:
            detail["judgment_id"] = append_judgment(connection, **verdict)
        store.insert_reversal(
            connection, gap_id=gap_id, reversal=reversal, actor=actor, created_at=now, detail=detail,
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
    "creation_ids",
    "creations_today",
    "day_start",
    "declared_prerequisite",
    "delete_edge",
    "edge_id_for",
    "edges_on_disk",
    "not_this_belief",
    "persist_check_advance",
    "prerequisite_graph",
    "record_belief",
    "reversal_verdict",
    "reverse_gap",
    "seed_from_question",
    "slug",
    "sooner_check_active",
    "subject_for_creation",
    "undo_creation",
    "would_cycle",
    "write_created_prerequisite",
]
