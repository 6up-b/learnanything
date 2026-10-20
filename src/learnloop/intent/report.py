"""Intent in ``learnloop plan report`` (spec §5.3): what is committed, and the
recall-target fallbacks.

Read-only over one connection. For every active item whose resolved recall
target is not 0.90 (with ``intent.recall_targets_enabled``), §5.3's effective
due is computed and its fallback counted: no item state, a null ``due_at``,
no qualifying (FSRS-eligible) attempt, or an anchor not before ``due_at``.
Uncommitted items at 0.90 never fall back (their ratio is exactly 1).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from learnloop.scheduling.intent.recall_targets import effective_due, load_anchors
from learnloop.scheduling.intent.resolution import Resolution, load_snapshots
from learnloop.scheduling.intent.serving import intent_enabled
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS


def intent_report(vault: Any, connection: Any) -> dict[str, Any]:
    config = vault.config
    if not intent_enabled(config):
        return {"enabled": False}
    targets = dict(config.intent.recall_targets)
    recall_on = bool(config.intent.recall_targets_enabled)
    snapshots = load_snapshots(connection)
    resolution = Resolution(snapshots, targets)
    states = {
        str(row["practice_item_id"]): row
        for row in connection.execute("SELECT practice_item_id, due_at FROM practice_item_state").fetchall()
    }
    anchors: dict[str, tuple[str, str]] | None = None
    choices: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    scaled = 0
    for item in vault.practice_items.values():
        if getattr(item, "status", "active") != "active":
            continue
        intent = resolution.for_item(item.id, getattr(item, "learning_object_id", None))
        if intent.uncommitted:
            continue
        choices[intent.choice if not intent.excluded else intent.disposition] += 1
        target = intent.recall_target if recall_on else 0.90
        if target == 0.90 or intent.excluded:
            continue
        if anchors is None:
            anchors = load_anchors(connection)
        state = states.get(item.id)
        anchor = anchors.get(item.id)
        result = effective_due(
            due_at=state["due_at"] if state is not None else None,
            anchor_at=anchor[0] if anchor else None,
            target=target,
            weights=FSRS6_DEFAULT_WEIGHTS,
            has_state=state is not None,
        )
        if result.fallback is None:
            scaled += 1
        else:
            fallbacks[result.fallback] += 1
    return {
        "enabled": True,
        "recall_targets_enabled": recall_on,
        "recall_targets": targets,
        "commitments_covering_items": len(resolution.snapshots),
        "committed_items_by_choice": dict(sorted(choices.items())),
        "recall_target_items_scaled": scaled,
        "recall_target_fallbacks": dict(sorted(fallbacks.items())),
    }


__all__ = ["intent_report"]
