"""Resolving an item's intent: the most recent choice wins (spec §5.3).

Several commitments can cover one item. One rule decides both whether the
item is served and at which depth and recall target:

1. **Covering commitments**: those whose current (head) targets include the
   item (``legacy_practice_item``) or its LO (``learning_object``; a subject or
   source control fans out to LO targets). Retired commitments drop out;
   ``satisfied`` ones stay (a completed check is how "Check once" ends). A
   commitment whose only targets are source locators covers no item.
2. **Disposition**: the covering commitment with the most recent *choice*
   decides. A choice is a commitment's creation, a version, or a disposition
   change; satisfying a check is not a choice, and neither is linking a
   deadline (§5.4). Ties (the same stored second) go to the item-level
   commitment, then to the higher recall target, then insertion order.
3. **Depth and target**, when served: the most recent ``active``
   intent-control commitment covering the item, else the decider. A request
   commitment therefore never lowers a depth the learner chose.
4. **No covering commitment**: uncommitted, today's behaviour at 0.90.

Pure over snapshots: :func:`load_resolution` reads them once per build.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from learnloop.scheduling.intent.model import (
    DEADLINE_CHANGE_REASON,
    EXCLUDING_DISPOSITIONS,
    INTENT_CONTROL_VIA,
    TIER_KEEP,
    TIER_LIGHT,
    TIER_PUSH,
    TIER_UNCOMMITTED,
    ChoiceStamp,
    CommitmentSnapshot,
    choice_for,
)

_DISPOSITIONS = frozenset({"active", "paused", "reference_only", "one_check_pending", "satisfied", "stopped"})


def _loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def snapshot_from_rows(
    commitment: Mapping[str, Any],
    versions: Sequence[Mapping[str, Any]],
    head_targets: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
) -> CommitmentSnapshot:
    """Fold one commitment's rows (versions in order, events in order).

    The disposition fold is ``commitments.resolve_disposition``'s exactly; the
    choice stamp is the latest of the creation, every version that is not a
    deadline link, and every disposition change that is not a satisfaction.
    """

    action = str(commitment["created_action"])
    ordered_versions = sorted(versions, key=lambda row: int(row["version"]))
    head = ordered_versions[-1]
    first = ordered_versions[0]
    disposition = "one_check_pending" if action == "test_me_later" else "active"
    retired = False
    satisfied_at: str | None = None
    stamps = [ChoiceStamp(str(commitment["created_at"]), str(first["id"]))]
    for version in ordered_versions[1:]:
        if version.get("change_reason") == DEADLINE_CHANGE_REASON:
            continue
        stamps.append(ChoiceStamp(str(version["created_at"]), str(version["id"])))
    for event in sorted(events, key=lambda row: (str(row["created_at"]), str(row["id"]))):
        kind = event["kind"]
        stamp = ChoiceStamp(str(event["created_at"]), str(event["id"]))
        if kind == "disposition_changed":
            new = _loads(event.get("detail_json")).get("disposition")
            if new in _DISPOSITIONS:
                disposition = new
                retired = False
                if new == "satisfied":
                    satisfied_at = str(event["created_at"])
                else:
                    stamps.append(stamp)
        elif kind == "paused":
            disposition, retired = "paused", False
            stamps.append(stamp)
        elif kind == "resumed":
            disposition, retired = "active", False
            stamps.append(stamp)
        elif kind == "retired":
            disposition, retired = "stopped", True
    provenance = _loads(first.get("provenance_json"))
    due_hint = next(
        (str(version["due_hint"]) for version in reversed(ordered_versions) if version.get("due_hint")),
        None,
    )
    items = frozenset(str(t["target_ref"]) for t in head_targets if t["target_kind"] == "legacy_practice_item")
    los = frozenset(str(t["target_ref"]) for t in head_targets if t["target_kind"] == "learning_object")
    return CommitmentSnapshot(
        id=str(commitment["id"]),
        action=action,
        created_at=str(commitment["created_at"]),
        depth_preset=str(head["depth_preset"]),
        disposition=disposition,
        retired=retired,
        choice=max(stamps, key=lambda s: (s.at, s.row_id)),
        item_targets=items,
        learning_object_targets=los,
        via=provenance.get("via") if isinstance(provenance.get("via"), str) else None,
        provenance=provenance,
        goal_id=str(head["goal_id"]) if head.get("goal_id") else None,
        due_hint=due_hint,
        satisfied_at=satisfied_at,
    )


def load_snapshots(connection: Any) -> list[CommitmentSnapshot]:
    """Every commitment that covers items, folded (one bulk read)."""

    from learnloop.db.stores import intent_reads as reads

    if not reads.commitment_tables_present(connection):
        return []
    commitments = reads.commitments_covering_items(connection)
    ids = [str(row["id"]) for row in commitments]
    versions_by: dict[str, list[dict[str, Any]]] = {}
    for row in reads.versions_for(connection, ids):
        versions_by.setdefault(str(row["commitment_id"]), []).append(row)
    heads = {cid: max(rows, key=lambda r: int(r["version"])) for cid, rows in versions_by.items()}
    targets_by: dict[str, list[dict[str, Any]]] = {}
    for row in reads.head_targets_for(connection, [str(head["id"]) for head in heads.values()]):
        targets_by.setdefault(str(row["commitment_version_id"]), []).append(row)
    events_by: dict[str, list[dict[str, Any]]] = {}
    for row in reads.events_for(connection, ids):
        events_by.setdefault(str(row["commitment_id"]), []).append(row)
    out = []
    for commitment in commitments:
        cid = str(commitment["id"])
        if cid not in heads:
            continue
        out.append(
            snapshot_from_rows(
                commitment,
                versions_by[cid],
                targets_by.get(str(heads[cid]["id"]), []),
                events_by.get(cid, []),
            )
        )
    return out


@dataclass(frozen=True)
class ItemIntent:
    """An item's (or an LO's) resolved intent."""

    disposition: str
    choice: str
    depth_preset: str | None
    recall_target: float
    decided_by: str | None = None
    depth_from: str | None = None
    #: "practice_item" | "learning_object" when a commitment decides; None uncommitted.
    level: str | None = None
    decider_action: str | None = None
    decider_intent_control: bool = False

    @property
    def uncommitted(self) -> bool:
        return self.decided_by is None

    @property
    def excluded(self) -> bool:
        return self.disposition in EXCLUDING_DISPOSITIONS

    @property
    def tier(self) -> int:
        """§6.3 / §7: Master and Learn first, then Keep, then uncommitted;
        Light touch last (and left out of re-entry and admission)."""

        if self.uncommitted:
            return TIER_UNCOMMITTED
        if self.choice in ("master", "learn"):
            return TIER_PUSH
        if self.choice == "keep":
            return TIER_KEEP
        if self.choice == "light_touch":
            return TIER_LIGHT
        return TIER_UNCOMMITTED

    def as_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "choice": self.choice,
            "depth_preset": self.depth_preset,
            "recall_target": self.recall_target,
            "decided_by": self.decided_by,
            "depth_from": self.depth_from,
            "level": self.level,
        }


def uncommitted_intent(targets: Mapping[str, float]) -> ItemIntent:
    return ItemIntent(
        disposition="active",
        choice="uncommitted",
        depth_preset=None,
        recall_target=float(targets.get("uncommitted", 0.90)),
    )


class Resolution:
    """§5.3 over a set of commitment snapshots."""

    def __init__(self, snapshots: Iterable[CommitmentSnapshot], targets: Mapping[str, float]) -> None:
        self.targets = dict(targets)
        self.snapshots: dict[str, CommitmentSnapshot] = {}
        self._by_item: dict[str, list[CommitmentSnapshot]] = {}
        self._by_lo: dict[str, list[CommitmentSnapshot]] = {}
        for snapshot in snapshots:
            if snapshot.retired or not snapshot.covers_items:
                continue
            self.snapshots[snapshot.id] = snapshot
            for item_id in snapshot.item_targets:
                self._by_item.setdefault(item_id, []).append(snapshot)
            for lo_id in snapshot.learning_object_targets:
                self._by_lo.setdefault(lo_id, []).append(snapshot)

    # -- reads -------------------------------------------------------------

    @property
    def empty(self) -> bool:
        return not self.snapshots

    def target_for(self, snapshot: CommitmentSnapshot) -> float:
        return float(self.targets.get(snapshot.depth_preset, self.targets.get("uncommitted", 0.90)))

    def covering(self, item_id: str, learning_object_id: str | None) -> list[tuple[CommitmentSnapshot, str]]:
        """Covering commitments with the level each covers the item at."""

        out: list[tuple[CommitmentSnapshot, str]] = []
        seen: set[str] = set()
        for snapshot in self._by_item.get(item_id, ()):
            out.append((snapshot, "practice_item"))
            seen.add(snapshot.id)
        if learning_object_id is not None:
            for snapshot in self._by_lo.get(learning_object_id, ()):
                if snapshot.id not in seen:
                    out.append((snapshot, "learning_object"))
        return out

    def _order_key(self, pair: tuple[CommitmentSnapshot, str]) -> tuple[Any, ...]:
        snapshot, level = pair
        return (
            snapshot.choice.at,
            1 if level == "practice_item" else 0,
            self.target_for(snapshot),
            snapshot.choice.row_id,
            snapshot.id,
        )

    def _resolve(self, covering: list[tuple[CommitmentSnapshot, str]]) -> ItemIntent:
        if not covering:
            return uncommitted_intent(self.targets)
        decider, level = max(covering, key=self._order_key)
        depth_source = decider
        controls = [
            pair
            for pair in covering
            if pair[0].intent_control and pair[0].disposition == "active" and pair[0].action == "help_me_remember"
        ]
        if controls:
            depth_source = max(controls, key=self._order_key)[0]
        return ItemIntent(
            disposition=decider.disposition,
            choice=choice_for(decider.action, depth_source.depth_preset, decider.disposition),
            depth_preset=depth_source.depth_preset,
            recall_target=self.target_for(depth_source),
            decided_by=decider.id,
            depth_from=depth_source.id,
            level=level,
            decider_action=decider.action,
            decider_intent_control=decider.intent_control,
        )

    def for_item(self, item_id: str, learning_object_id: str | None) -> ItemIntent:
        return self._resolve(self.covering(item_id, learning_object_id))

    def for_learning_object(self, learning_object_id: str) -> ItemIntent:
        """An LO's own intent: the commitments that target the LO itself."""

        return self._resolve([(snapshot, "learning_object") for snapshot in self._by_lo.get(learning_object_id, ())])

    def committed_item_ids(self) -> frozenset[str]:
        return frozenset(self._by_item)

    def committed_learning_object_ids(self) -> frozenset[str]:
        return frozenset(self._by_lo)

    def with_snapshot(self, snapshot: CommitmentSnapshot) -> "Resolution":
        """The resolution if ``snapshot`` were added (or replaced): the
        control's preview uses the very rule the queue uses (§5.2)."""

        others = [s for s in self.snapshots.values() if s.id != snapshot.id]
        return Resolution([*others, snapshot], self.targets)


def intent_control_commitments(snapshots: Iterable[CommitmentSnapshot]) -> list[CommitmentSnapshot]:
    return [snapshot for snapshot in snapshots if snapshot.via == INTENT_CONTROL_VIA]


def rechosen(snapshot: CommitmentSnapshot, *, at: str, row_id: str, **changes: Any) -> CommitmentSnapshot:
    """A snapshot as if chosen again at ``at`` (the preview's virtual choice)."""

    return replace(snapshot, choice=ChoiceStamp(at, row_id), retired=False, **changes)


__all__ = [
    "ItemIntent",
    "Resolution",
    "intent_control_commitments",
    "load_snapshots",
    "rechosen",
    "snapshot_from_rows",
    "uncommitted_intent",
]
