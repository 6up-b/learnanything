"""What serving reads from intent (spec §5.2, §5.3, §6.1): one object per build.

:func:`intent_serving` returns ``None`` when intent changes nothing: the kill
switch ``intent.enabled`` is off, or no commitment covers any item and the
uncommitted target is 0.90 (or recall targets are off). The scheduler and the
plan then take exactly their pre-DL2 paths, which is how byte-identity with no
commitments is kept by construction rather than by coincidence.

Otherwise :class:`IntentServing` answers, per item:

- **exclusion** (§5.3 step 2): ``paused``, ``reference_only``, ``stopped`` and
  ``satisfied`` items are not served and are not requests; a "Check once"
  holds its items back until its date;
- **the effective due** (recall targets, ``recall_targets``);
- **push** (§5.4, §6.1): attempted items under Learn and Master that are not
  yet due;
- **requests** (§5.3 "Requests follow the same rule"): the existing branches
  minus intent-control commitments and minus excluded or pending items, plus
  the **dated "Check once" branch**: one item per due check, its date the
  commitment's ``due_hint`` when present, else ``created_at +
  capture.test_me_later_days`` (no ``followup_tasks``, nothing persisted).
  An item-target check serves that item; an LO check serves the scheduler's
  top-ranked item of the LO (:meth:`IntentServing.pick_checks`, after the
  sort). Held-out and reserved exam items never reach it: the scheduler's
  routine exclusions run before the intent gate.

A check is **answered** by an attempt on an item it decides at or after its
date; resolution then reads it as ``satisfied`` (deriving it keeps serving
right before ``checks.settle_answered_checks`` writes the event).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from typing import Any

from learnloop.clock import parse_utc
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.scheduling.intent.model import CommitmentSnapshot
from learnloop.scheduling.intent.recall_targets import EffectiveDue, effective_due, load_anchors
from learnloop.scheduling.intent.resolution import ItemIntent, Resolution, load_snapshots

DATE_FROM_DUE_HINT = "due_hint"
DATE_FROM_DEFAULT = "test_me_later_days"


def intent_enabled(config: Any) -> bool:
    intent = getattr(config, "intent", None)
    return bool(getattr(intent, "enabled", False))


def check_date(snapshot: CommitmentSnapshot, *, default_days: int) -> tuple[datetime, str]:
    """When a "Check once" comes due (RW6b's request: ``due_hint`` first).

    A date-only ``due_hint`` (``YYYY-MM-DD``, as the Reader writes it) means
    that local calendar day, the plan's day (D9)."""

    hint = (snapshot.due_hint or "").strip()
    if hint:
        try:
            if len(hint) == 10:
                day = date.fromisoformat(hint)
                return datetime(day.year, day.month, day.day).astimezone().astimezone(UTC), DATE_FROM_DUE_HINT
            parsed = parse_utc(hint)
            if parsed is not None:
                return parsed, DATE_FROM_DUE_HINT
        except ValueError:
            pass
    created = parse_utc(snapshot.created_at) or datetime.now(UTC)
    return created + timedelta(days=int(default_days)), DATE_FROM_DEFAULT


@dataclass(frozen=True)
class CheckState:
    """One pending "Check once"."""

    commitment_id: str
    date: datetime
    date_source: str
    #: Items it decides (§5.3 step 2), in id order. Empty: replaced everywhere.
    candidates: tuple[str, ...]
    due: bool
    answered_by: str | None = None
    item_level: bool = False
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class IntentServing:
    resolution: Resolution
    now: datetime
    item_learning_objects: Mapping[str, str]
    recall_targets_enabled: bool
    weights: tuple[float, ...]
    checks: dict[str, CheckState]
    _anchor_loader: Any = None
    _anchors: dict[str, tuple[str, str]] | None = None
    _intents: dict[str, ItemIntent] = field(default_factory=dict)
    _fallback_items: dict[str, set[str]] = field(default_factory=dict)

    # -- per item ------------------------------------------------------------

    def intent(self, item_id: str) -> ItemIntent:
        cached = self._intents.get(item_id)
        if cached is None:
            cached = self.resolution.for_item(item_id, self.item_learning_objects.get(item_id))
            self._intents[item_id] = cached
        return cached

    def check_for(self, item_id: str) -> CheckState | None:
        intent = self.intent(item_id)
        if intent.disposition != "one_check_pending" or intent.decided_by is None:
            return None
        return self.checks.get(intent.decided_by)

    def withhold_reason(self, item_id: str) -> str | None:
        """Why the build leaves this item out, or None (served as usual)."""

        intent = self.intent(item_id)
        if intent.uncommitted:
            return None
        if intent.excluded:
            return f"intent_{intent.disposition}"
        if intent.disposition == "one_check_pending":
            check = self.check_for(item_id)
            if check is None or not check.due:
                return "intent_check_waiting"
        return None

    def is_check_candidate(self, item_id: str) -> bool:
        check = self.check_for(item_id)
        return check is not None and check.due and item_id in check.candidates

    def _anchor(self, item_id: str) -> str | None:
        if self._anchors is None:
            self._anchors = self._anchor_loader() if self._anchor_loader is not None else {}
        found = self._anchors.get(item_id)
        return found[0] if found is not None else None

    def effective(self, item_id: str, state: Any) -> EffectiveDue:
        """§5.3's effective due (the stored ``due_at`` at 0.90 or with recall
        targets off)."""

        target = self.target_for(item_id)
        due_at = getattr(state, "due_at", None) if state is not None else None
        if target == 0.90:
            parsed = parse_utc(due_at)
            return EffectiveDue(parsed, None if parsed is not None else ("no_state" if state is None else "no_due_at"))
        result = effective_due(
            due_at=due_at,
            anchor_at=self._anchor(item_id) if due_at is not None else None,
            target=target,
            weights=self.weights,
            has_state=state is not None,
        )
        if result.fallback is not None:
            # Counted once per item (``learnloop plan report``).
            self._fallback_items.setdefault(result.fallback, set()).add(item_id)
        return result

    def target_for(self, item_id: str) -> float:
        return self.intent(item_id).recall_target if self.recall_targets_enabled else 0.90

    @property
    def fallbacks(self) -> dict[str, int]:
        return {kind: len(items) for kind, items in sorted(self._fallback_items.items())}

    def effective_due_or_none(self, item_id: str, state: Any) -> datetime | None:
        """For ``_forgetting_risk``: an override only when it differs."""

        if state is None or getattr(state, "due_at", None) is None:
            return None
        return self.effective(item_id, state).due

    def due(self, item_id: str, state: Any) -> bool:
        effective = self.effective(item_id, state).due
        return effective is not None and effective <= self.now

    def pushes(self, item_id: str, state: Any) -> bool:
        """§6.1: an attempted item under Learn or Master that is not yet due."""

        intent = self.intent(item_id)
        if intent.uncommitted or intent.disposition != "active" or intent.choice not in ("master", "learn"):
            return False
        if state is None or getattr(state, "last_attempt_at", None) is None:
            return False
        return not self.due(item_id, state)

    # -- requests and checks ---------------------------------------------------

    def intent_control_request_commitments(self) -> tuple[str, ...]:
        """Intent-control ``help_me_remember`` commitments: choosing Master or
        Keep on an item is not a request (§5.3)."""

        return tuple(
            sorted(
                snapshot.id
                for snapshot in self.resolution.snapshots.values()
                if snapshot.intent_control and snapshot.action == "help_me_remember"
            )
        )

    def filter_requests(self, base: Sequence[str]) -> list[str]:
        """The existing branches, minus excluded or pending items, plus every
        due check's candidates (trimmed to one per check after the sort)."""

        kept = [
            item_id
            for item_id in base
            if (intent := self.intent(item_id)).uncommitted or intent.disposition == "active"
        ]
        seen = set(kept)
        for check in self.due_checks():
            for item_id in check.candidates:
                if item_id not in seen:
                    kept.append(item_id)
                    seen.add(item_id)
        return kept

    def due_checks(self) -> list[CheckState]:
        return sorted(
            (check for check in self.checks.values() if check.due and check.candidates and check.answered_by is None),
            key=lambda check: (check.date, check.commitment_id),
        )

    def pick_checks(self, queue: Sequence[Any]) -> tuple[list[Any], list[str]]:
        """One item per due check: the first (top-ranked) candidate in the
        built order; the other candidates leave this build."""

        chosen: dict[str, str] = {}
        drop: set[str] = set()
        positions = {getattr(entry, "practice_item_id", None): index for index, entry in enumerate(queue)}
        for check in self.due_checks():
            ranked = sorted(
                (item_id for item_id in check.candidates if item_id in positions),
                key=lambda item_id: positions[item_id],
            )
            if not ranked:
                continue
            chosen[check.commitment_id] = ranked[0]
            drop.update(ranked[1:])
        kept = [entry for entry in queue if getattr(entry, "practice_item_id", None) not in drop]
        ordered = [chosen[check.commitment_id] for check in self.due_checks() if check.commitment_id in chosen]
        return kept, ordered

    def check_item_ids(self, item_ids: Iterable[str]) -> dict[str, CheckState]:
        """The due checks' items among ``item_ids`` (the plan's pool), one per
        check: the first in the given order."""

        found: dict[str, CheckState] = {}
        claimed: set[str] = set()
        for item_id in item_ids:
            check = self.check_for(item_id)
            if check is None or not check.due or check.answered_by is not None:
                continue
            if check.commitment_id in claimed or item_id not in check.candidates:
                continue
            claimed.add(check.commitment_id)
            found[item_id] = check
        return found


def _items_by_learning_object(vault: Any) -> tuple[dict[str, str], dict[str, list[str]]]:
    item_los: dict[str, str] = {}
    by_lo: dict[str, list[str]] = {}
    for item in vault.practice_items.values():
        lo_id = getattr(item, "learning_object_id", None)
        if lo_id is None:
            continue
        item_los[item.id] = str(lo_id)
        by_lo.setdefault(str(lo_id), []).append(item.id)
    for ids in by_lo.values():
        ids.sort()
    return item_los, by_lo


def build_checks(
    resolution: Resolution,
    *,
    by_lo: Mapping[str, list[str]],
    item_los: Mapping[str, str],
    now: datetime,
    default_days: int,
    attempts_since: Any,
) -> tuple[dict[str, CheckState], Resolution]:
    """Every pending "Check once" with its date and the items it decides;
    answered ones are folded to ``satisfied`` in the returned resolution."""

    checks: dict[str, CheckState] = {}
    answered: list[CommitmentSnapshot] = []
    for snapshot in resolution.snapshots.values():
        if snapshot.action != "test_me_later" or snapshot.disposition != "one_check_pending":
            continue
        when, source = check_date(snapshot, default_days=default_days)
        covered = set(snapshot.item_targets)
        for lo_id in snapshot.learning_object_targets:
            covered.update(by_lo.get(lo_id, ()))
        decided = tuple(
            sorted(
                item_id
                for item_id in covered
                if resolution.for_item(item_id, item_los.get(item_id)).decided_by == snapshot.id
            )
        )
        when_iso = when.strftime("%Y-%m-%dT%H:%M:%SZ")
        attempts = attempts_since(list(decided), when_iso) if decided and when <= now else []
        answered_by = str(attempts[0]["id"]) if attempts else None
        checks[snapshot.id] = CheckState(
            commitment_id=snapshot.id,
            date=when,
            date_source=source,
            candidates=decided,
            due=when <= now,
            answered_by=answered_by,
            item_level=bool(snapshot.item_targets),
            provenance=dict(snapshot.provenance),
        )
        if answered_by is not None:
            answered.append(replace(snapshot, disposition="satisfied", satisfied_at=str(attempts[0]["created_at"])))
    for snapshot in answered:
        resolution = resolution.with_snapshot(snapshot)
    return checks, resolution


def intent_serving(
    vault: Any,
    repository: Any,
    *,
    now: datetime,
    weights: tuple[float, ...] | None = None,
    force: bool = False,
) -> IntentServing | None:
    """The build's intent view, or None when intent changes nothing."""

    config = vault.config
    if not intent_enabled(config):
        return None
    targets = dict(config.intent.recall_targets)
    recall_on = bool(config.intent.recall_targets_enabled)
    with repository.connection() as connection:
        snapshots = load_snapshots(connection)
    covering = [snapshot for snapshot in snapshots if not snapshot.retired and snapshot.covers_items]
    if not covering and not force and (not recall_on or float(targets.get("uncommitted", 0.90)) == 0.90):
        return None
    if weights is None:
        weights = resolve_fsrs_weights(repository)
    resolution = Resolution(covering, targets)
    item_los, by_lo = _items_by_learning_object(vault)

    def attempts_since(item_ids: list[str], since: str) -> list[dict[str, Any]]:
        from learnloop.db.stores import intent_reads as reads

        with repository.connection() as connection:
            return reads.attempts_since(connection, item_ids, since)

    checks, resolution = build_checks(
        resolution,
        by_lo=by_lo,
        item_los=item_los,
        now=now,
        default_days=int(config.capture.test_me_later_days),
        attempts_since=attempts_since,
    )

    def anchors() -> dict[str, tuple[str, str]]:
        with repository.connection() as connection:
            return load_anchors(connection)

    return IntentServing(
        resolution=resolution,
        now=now,
        item_learning_objects=item_los,
        recall_targets_enabled=recall_on,
        weights=tuple(weights),
        checks=checks,
        _anchor_loader=anchors,
    )


__all__ = [
    "CheckState",
    "DATE_FROM_DEFAULT",
    "DATE_FROM_DUE_HINT",
    "IntentServing",
    "build_checks",
    "check_date",
    "intent_enabled",
    "intent_serving",
]
