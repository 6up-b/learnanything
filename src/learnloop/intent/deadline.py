"""Goals as optional deadlines (spec §5.4).

"Add a deadline" on a commitment creates (or updates) a learner ``Goal`` with
``creation_source: "learner"``, the ``due_at`` and the commitment's LOs as its
scope (their concepts, as ``create_goal`` scopes a goal), then appends a
commitment version whose ``goal_id`` names it. The link already exists on
commitment versions, so no vault model or schema change is needed. The goal
machinery is reused unchanged: frontier, forecasts, exams, the goal report,
and the push lane's goal frontiers (§5.4: push takes items on active-goal
frontiers, as today).

The version appended for the link carries ``change_reason =
"intent_deadline"``: linking a deadline is not a choice, so it never moves the
commitment's choice time (``resolution.snapshot_from_rows``).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.curriculum import commitments as C
from learnloop.intent.control import IntentControlError, Scope, own_commitments, scope_contents
from learnloop.scheduling.intent.model import CHOICE_LABEL, DEADLINE_CHANGE_REASON, choice_for
from learnloop.scheduling.intent.resolution import load_snapshots
from learnloop.vault.models import Goal
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:48] or "deadline"


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
    with repository.connection() as connection:
        snapshots = load_snapshots(connection)
    own = [s for s in own_commitments(snapshots, scope) if s.action == "help_me_remember"]
    if not own or own[-1].disposition != "active":
        raise IntentControlError("choose Master, Learn, Keep or Light touch first; a deadline belongs to a setting")
    commitment = own[-1]
    concepts = sorted(
        {vault.learning_objects[lo_id].concept for lo_id in contents.learning_object_ids if lo_id in vault.learning_objects}
    )
    if not concepts:
        raise IntentControlError("nothing to put a deadline on")
    paths = VaultPaths(vault.root, vault.config)
    goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals = goals_data.setdefault("goals", [])
    now = utc_now_iso(clock)
    target = float(vault.config.intent.recall_targets.get(commitment.depth_preset, 0.90))
    existing = next(
        (goal for goal in goals if isinstance(goal, dict) and commitment.goal_id and goal.get("id") == commitment.goal_id),
        None,
    )
    created = existing is None
    if existing is not None:
        existing["due_at"] = due
        existing["status"] = "active"
        existing["facet_scope"] = {"concepts": concepts, "facets": []}
        existing["updated_at"] = now
        Goal.model_validate(existing)
        goal_id = str(existing["id"])
    else:
        choice = choice_for(commitment.action, commitment.depth_preset, commitment.disposition)
        title = f"{contents.title} ({CHOICE_LABEL.get(choice, choice)}) by {due[:10]}"
        ids = {str(goal.get("id")) for goal in goals if isinstance(goal, dict)}
        base = f"goal_{_slug(contents.title)}_by_{due[:10].replace('-', '')}"
        goal_id, suffix = base, 2
        while goal_id in ids:
            goal_id, suffix = f"{base}_{suffix}", suffix + 1
        entry = {
            "id": goal_id,
            "title": title,
            "intent_sentence": None,
            "creation_source": "learner",
            "status": "active",
            "priority": 0.5,
            "target_recall": target,
            "facet_scope": {"concepts": concepts, "facets": []},
            "due_at": due,
            "exam": {"enabled": False, "item_count": 20},
            "created_at": now,
            "updated_at": now,
        }
        Goal.model_validate(entry)
        goals.append(entry)
    goals_data["schema_version"] = 2
    write_yaml(paths.goals_path, goals_data)
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


__all__ = ["set_deadline"]
