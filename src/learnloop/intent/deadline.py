"""Goals as optional deadlines (spec §5.4).

"Add a deadline" on a commitment creates (or updates) a learner ``Goal`` with
``creation_source: "learner"``, the ``due_at`` and the commitment's LOs as its
scope, then appends a commitment version whose ``goal_id`` names it.

**Scope** (Codex review F8): the goal names the commitment's LOs' canonical
scope facets (``facet_scope.facets``), never their concepts: a concept would
pull in every other LO on it, which the learner did not choose. An LO that
shares a facet with the commitment's LOs still meets the goal on that shared
facet, as the goal model counts facets.

**Recovery** (Codex review F9): the goal's id is derived from the commitment
(``goal_intent_<commitment id>``), and the read-modify-write of
``goals.yaml``, its atomic replace and the link run under the vault mutation
lock. A crash after the goal is published and before the link is appended
is recovered by the next "Add a deadline": it finds the goal by that id,
updates it and links it, so no orphan goal keeps an earlier deadline active;
two writers serialize on the lock. The link already exists on
commitment versions, so no vault model or schema change is needed. The goal
machinery is reused unchanged: frontier, forecasts, exams, the goal report,
and the push lane's goal frontiers (§5.4: push takes items on active-goal
frontiers, as today).

The version appended for the link carries ``change_reason =
"intent_deadline"``: linking a deadline is not a choice, so it never moves the
commitment's choice time (``resolution.snapshot_from_rows``).
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.curriculum import commitments as C
from learnloop.intent.control import IntentControlError, Scope, own_commitments, scope_contents
from learnloop.learner.facet_diagnostics import scope_facets
from learnloop.scheduling.intent.model import CHOICE_LABEL, DEADLINE_CHANGE_REASON, choice_for
from learnloop.scheduling.intent.resolution import load_snapshots
from learnloop.vault.models import Goal
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, yaml_to_string
from learnloop.vault_lock import vault_mutation_lock


def goal_id_for(commitment_id: str) -> str:
    """The deadline goal's stable identity: one per commitment (F9)."""

    return f"goal_intent_{commitment_id.lower()}"


def _write_goals(path: Path, data: dict[str, Any]) -> None:
    """Publish ``goals.yaml`` whole: a temporary file, then an atomic replace,
    so a crash never leaves it half written."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.intent-{os.getpid()}.tmp")
    temporary.write_text(yaml_to_string(data), encoding="utf-8")
    os.replace(temporary, path)


def _normalize_due(due_at: str) -> str:
    value = due_at.strip()
    if len(value) == 10:
        date.fromisoformat(value)
        return f"{value}T23:59:59Z"
    from learnloop.clock import parse_utc

    parsed = parse_utc(value)
    if parsed is None:
        raise IntentControlError("a deadline needs a date")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def set_deadline(
    vault: Any, repository: Any, scope: Scope, due_at: str, *, clock: Clock | None = None
) -> dict[str, Any]:
    """Add or move the deadline of the scope's own depth commitment.

    Returns ``{"goal_id", "due_at", "created"}``. The caller reloads the vault
    (the goal lives in ``goals.yaml``)."""

    try:
        due = _normalize_due(due_at)
    except ValueError as error:
        raise IntentControlError(f"not a date: {due_at}") from error
    contents = scope_contents(vault, repository, scope)
    facets = sorted(
        {
            vault.canonical_facet_id(str(facet))
            for lo_id in contents.learning_object_ids
            if lo_id in vault.learning_objects
            for facet in scope_facets(vault, lo_id, repository)
        }
    )
    if not facets:
        raise IntentControlError("nothing to put a deadline on")
    paths = VaultPaths(vault.root, vault.config)
    with vault_mutation_lock(Path(vault.root), purpose="intent_deadline"):
        # Read the commitment inside the lock: a concurrent "Add a deadline"
        # has either linked it already or not started.
        with repository.connection() as connection:
            snapshots = load_snapshots(connection)
        own = [s for s in own_commitments(snapshots, scope) if s.action == "help_me_remember"]
        if not own or own[-1].disposition != "active":
            raise IntentControlError("choose Master, Learn, Keep or Light touch first; a deadline belongs to a setting")
        commitment = own[-1]
        goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
        goals = goals_data.setdefault("goals", [])
        now = utc_now_iso(clock)
        target = float(vault.config.intent.recall_targets.get(commitment.depth_preset, 0.90))
        # The linked goal, else the commitment's own (published by an
        # attempt that did not get to link it: F9).
        wanted = [goal_id for goal_id in (commitment.goal_id, goal_id_for(commitment.id)) if goal_id]
        existing = next(
            (
                goal
                for goal_id in wanted
                for goal in goals
                if isinstance(goal, dict) and goal.get("id") == goal_id
            ),
            None,
        )
        created = existing is None
        if existing is not None:
            existing["due_at"] = due
            # DL2 verify F17 (fix round 5): the goal targets the commitment's
            # current depth (a Keep made Master, then moved, targets Master's).
            existing["target_recall"] = target
            existing["status"] = "active"
            existing["facet_scope"] = {"concepts": [], "facets": facets}
            existing["updated_at"] = now
            Goal.model_validate(existing)
            goal_id = str(existing["id"])
        else:
            choice = choice_for(commitment.action, commitment.depth_preset, commitment.disposition)
            goal_id = goal_id_for(commitment.id)
            entry = {
                "id": goal_id,
                "title": f"{contents.title} ({CHOICE_LABEL.get(choice, choice)}) by {due[:10]}",
                "intent_sentence": None,
                "creation_source": "learner",
                "status": "active",
                "priority": 0.5,
                "target_recall": target,
                "facet_scope": {"concepts": [], "facets": facets},
                "due_at": due,
                "exam": {"enabled": False, "item_count": 20},
                "created_at": now,
                "updated_at": now,
            }
            Goal.model_validate(entry)
            goals.append(entry)
        goals_data["schema_version"] = 2
        _write_goals(paths.goals_path, goals_data)
        if commitment.goal_id != goal_id:
            C.append_commitment_version(
                repository,
                commitment_id=commitment.id,
                goal_id=goal_id,
                change_reason=DEADLINE_CHANGE_REASON,
                clock=clock,
            )
    repository.bump_queue_revision(clock=clock)
    return {"goal_id": goal_id, "due_at": due, "created": created, "commitment_id": commitment.id}


__all__ = ["goal_id_for", "set_deadline"]
