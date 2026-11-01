"""``create_goal_lo``: a learning object a learner's goal names that the vault does not have yet
(spec_teacher_v1 §11.5; spec_deliverable_curriculum_v1 §5.3).

Built once, here, to TE §11.5's design: the deliverable curriculum (C0b) uses it first, for a
phrase of the learner's scope the resolver could not match, and the teacher's TE2 takes it over.

* **The learner's request is the decision.** No judge: the learner pressed *add it* on a phrase of
  their own words; the resolver's proposed title and statement are what is written, labelled
  "from LearnLoop's model".
* It **reuses the text-gap write** (``diagnosis.text_gaps.actions``): ids derived from the request
  (a retry names the same entities, so a crash mid-write is completed, never duplicated), the
  concept and LO written under the vault mutation lock, the state synced after; and its **undo**
  (the LO goes dormant: its items stop being served). No prerequisite edge is written, so the
  cycle check has nothing to refuse (an edge, when a later stage adds one, goes through
  ``add_prerequisite_edge`` and its cycle check).
* **The daily cap** is the text gaps' (``learner_text_gaps.max_creations_per_day``), counted over
  both: the text-gap creations kept today and the goal LOs created today. An explicit goal may
  exceed it by one a day (TE §11.5).
* **Provenance:** ``origin = codex_proposal``, ``mechanism`` the caller's (``deliverable_scope_v1``
  for C0b, ``teacher_goal_v1`` for TE2), ``source_refs`` the anchors (empty when the goal has no
  source: the LO is then unsourced, labelled so), and the goal id and the learner's phrase.

Nothing here writes evidence, mastery, certification or a plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.diagnosis.text_gaps import actions as TGA
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault_lock import vault_mutation_lock

#: The mechanisms whose LOs this action wrote (the cap counts them).
DELIVERABLE_MECHANISM = "deliverable_scope_v1"
TEACHER_MECHANISM = "teacher_goal_v1"
MECHANISMS: frozenset[str] = frozenset({DELIVERABLE_MECHANISM, TEACHER_MECHANISM})
#: How far past the daily cap an explicit goal may go, per day (TE §11.5: "by one a day"; a
#: burden guardrail labelled ``keep``, never a model parameter).
EXPLICIT_GOAL_ALLOWANCE = 1
#: The written title and statement at most (the text-gap write's bounds).
TITLE_CHARS = 200
STATEMENT_CHARS = 2000


class GoalLoError(ValueError):
    """A creation refused (``code``: validation_error | capped | no_subject)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class GoalLoRequest:
    """What the learner asked for: the phrase of their own words, and the LO proposed for it."""

    goal_id: str
    phrase: str
    title: str
    statement: str
    subject_id: str
    mechanism: str = DELIVERABLE_MECHANISM
    knowledge_type: str = "concept"
    anchors: tuple[dict[str, Any], ...] = ()

    @property
    def key(self) -> str:
        """The request's identity: one goal, one phrase (a retry names the same LO)."""

        return f"{self.mechanism}:{self.goal_id}:{' '.join(self.phrase.casefold().split())}"


def creation_ids(request: GoalLoRequest) -> tuple[str, str]:
    """``(concept_id, learning_object_id)``, derived from the request."""

    suffix = TGA._hash(request.key)[:8]
    return f"{TGA.slug(request.title)}_{suffix}", f"lo_goal_{TGA.slug(request.title)}_{suffix}"


def goal_los_created_today(vault: Any, *, now_iso: str) -> list[str]:
    """Active LOs this action created since today's UTC midnight (any mechanism)."""

    start = TGA.day_start(now_iso)
    out = []
    for learning_object in vault.learning_objects.values():
        provenance = getattr(learning_object, "provenance", None)
        mechanism = getattr(provenance, "mechanism", None) if provenance is not None else None
        if isinstance(provenance, dict):
            mechanism = provenance.get("mechanism")
        created = str(getattr(learning_object, "created_at", "") or "")
        if mechanism in MECHANISMS and learning_object.status == "active" and created >= start:
            out.append(learning_object.id)
    return sorted(out)


def creations_today(vault: Any, repository: Any, *, now_iso: str) -> int:
    """The cap's count: text-gap creations kept today plus the goal LOs created today."""

    return TGA.creations_today(repository, now_iso=now_iso) + len(goal_los_created_today(vault, now_iso=now_iso))


def cap(vault: Any) -> int:
    return int(vault.config.learner_text_gaps.max_creations_per_day) + EXPLICIT_GOAL_ALLOWANCE


def create_goal_lo(root: Path | str, repository: Any, request: GoalLoRequest, *,
                   clock: Clock | None = None) -> dict[str, Any]:
    """Create the concept and the LO (idempotent per request). Returns ``{"learning_object_id",
    "concept_id", "created"}``; ``created`` is False when an earlier attempt wrote it already."""

    from learnloop.vault.writer import upsert_concept, upsert_learning_object

    title = " ".join(request.title.split())[:TITLE_CHARS]
    statement = " ".join(request.statement.split())[:STATEMENT_CHARS]
    if not title or not statement or not request.phrase.strip():
        raise GoalLoError("validation_error", "A new topic needs a title, a statement and your phrase.")
    if request.mechanism not in MECHANISMS:
        raise GoalLoError("validation_error", f"unknown mechanism {request.mechanism!r}")
    root = Path(root)
    concept_id, learning_object_id = creation_ids(request)
    now = utc_now_iso(clock)
    with vault_mutation_lock(root, purpose="create_goal_lo"):
        vault = load_vault(root)
        if request.subject_id not in vault.subjects:
            raise GoalLoError("no_subject", "That subject is not in your vault.")
        existing = vault.learning_objects.get(learning_object_id)
        if existing is not None and existing.status == "active":
            return {"learning_object_id": learning_object_id, "concept_id": concept_id, "created": False}
        if existing is None and creations_today(vault, repository, now_iso=now) >= cap(vault):
            raise GoalLoError("capped", "LearnLoop has added as many new topics as it adds in a day. "
                                        "Try again tomorrow, or name one your books already have.")
        provenance = {"origin": "codex_proposal", "source_refs": [dict(anchor) for anchor in request.anchors],
                      "mechanism": request.mechanism, "goal_id": request.goal_id,
                      "learner_text": request.phrase.strip()[:TITLE_CHARS]}
        if concept_id not in vault.concepts:
            upsert_concept(root, concept_id, {
                "title": title, "type": "concept", "aliases": [], "description": statement,
                "tags": [request.mechanism], "created_at": now, "updated_at": now,
            }, clock=clock)
        upsert_learning_object(root, {
            "id": learning_object_id, "title": title, "subjects": [request.subject_id], "concept": concept_id,
            "knowledge_type": request.knowledge_type, "status": "active", "summary": statement,
            "prerequisites": [], "confusables": [], "tags": [request.mechanism], "provenance": provenance,
            "created_at": now if existing is None else str(getattr(existing, "created_at", now) or now),
            "updated_at": now,
        }, clock=clock)
    sync_vault_state(load_vault(root), repository, clock=clock)
    return {"learning_object_id": learning_object_id, "concept_id": concept_id, "created": True}


def undo_goal_lo(root: Path | str, repository: Any, learning_object_id: str, *,
                 clock: Clock | None = None) -> dict[str, Any]:
    """The created LO goes dormant (its items are no longer served), as a text-gap creation's undo."""

    from learnloop.vault.writer import upsert_learning_object

    root = Path(root)
    with vault_mutation_lock(root, purpose="undo_goal_lo"):
        vault = load_vault(root)
        learning_object = vault.learning_objects.get(learning_object_id)
        provenance = getattr(learning_object, "provenance", None) if learning_object is not None else None
        mechanism = provenance.get("mechanism") if isinstance(provenance, dict) else getattr(
            provenance, "mechanism", None)
        if learning_object is None or mechanism not in MECHANISMS:
            raise GoalLoError("validation_error", "Only a topic added for one of your goals can be undone here.")
        upsert_learning_object(root, {"id": learning_object_id, "status": "dormant",
                                      "subjects": learning_object.subjects}, clock=clock)
    sync_vault_state(load_vault(root), repository, clock=clock)
    return {"learning_object_id": learning_object_id, "status": "dormant"}


__all__ = [
    "DELIVERABLE_MECHANISM",
    "EXPLICIT_GOAL_ALLOWANCE",
    "GoalLoError",
    "GoalLoRequest",
    "MECHANISMS",
    "TEACHER_MECHANISM",
    "cap",
    "create_goal_lo",
    "creation_ids",
    "creations_today",
    "goal_los_created_today",
    "undo_goal_lo",
]
