"""What serving reads from intent (spec §5.2, §5.3, §6.1): one object per build.

:func:`intent_serving` returns ``None`` when intent changes nothing: the
vault is below the successor ``mvp-0.29``, the kill switch ``intent.enabled``
is off, or no commitment covers any item and the
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

A check is **answered** by an attempt *on your own* (one the activity
policy does not count as assisted: :func:`on_your_own`) on an item it decides at or after its date, which the
one eligibility decision would have served cold at that attempt
(``serve_eligibility.check_once_at_attempt``: a sibling's reveal holding the
LO, or a routine display covering it, makes it practice although submit did
not prime it; DL2 Codex re-review F3); resolution then reads it as
``satisfied`` (deriving it keeps serving right before
``checks.settle_answered_checks`` writes the event). Any other attempt is
practice: it answers nothing and dates the check again,
``capture.test_me_later_days`` after it (DL2 Codex review F3).

**Cold eligibility** (DL2 Codex review F3): a due check is a measurement of
the item alone, so each candidate asks the one eligibility decision
(``serve_eligibility.decide(..., CHECK_ONCE)``). Eligible candidates are the
check's; when none is, a time-bounded hold (a routine display, a reveal
since the check was chosen) makes the check wait, and standing exposure
(the answer shown, which only an attempt absorbs) serves the item as
practice, labelled so (``CheckState.servable``, ``eligible``). Nothing is
persisted: the decision is recomputed at every build and every serve.

**Admission first** (orchestrator ruling R1): the cold-over-practice choice is
made only among the candidates the scheduler's one admission predicate
admits (``serving_exclusions.admission_reason``: the routine gate, the
diagnostic freshness reserve, placement, the cold-start gate and the
probe-episode gates, a candidate asked as the request it becomes). A
candidate the build would not serve (retired, held out, a fresh diagnostic
surface outside its probe episode, ...) can neither be the check nor
suppress one that can (DL2 Codex re-review F11, verify reopening). The split
is made on first use: ``build_due_queue`` binds its own admission
(:meth:`IntentServing.bind_admission`) before it reads a check; any other
view (the plan, the practice view, settling) gets the same predicate over its
own reads (``scheduler.check_admission``).

**The successor** (DL2 Codex re-review F2): intent is ``mvp-0.29``, behind
the kill switch ``intent.enabled``. Below the tag, or switched off,
:func:`intent_enabled` is False, :func:`intent_serving` returns None and
every scheduler and plan path runs the predecessor's code; the desktop
control answers ``enabled: false``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from typing import Any

from learnloop.clock import parse_utc
from learnloop.diagnosis.causal_activity_policy import attempt_counts_as_assisted
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.scheduling.intent.model import CommitmentSnapshot
from learnloop.scheduling.intent.recall_targets import EffectiveDue, effective_due, load_anchors
from learnloop.scheduling.intent.resolution import ItemIntent, Resolution, load_snapshots

DATE_FROM_DUE_HINT = "due_hint"
DATE_FROM_DEFAULT = "test_me_later_days"
#: Dated again after an attempt that was not on your own (F3).
DATE_FROM_PRACTICE = "after_practice"

#: Eligibility verdicts a check reads (``serve_eligibility``'s, as strings so
#: this module stays free of it; :func:`intent_serving` passes the decision).
_SERVE = "serve"
_SERVE_AS_ORDINARY = "serve_as_ordinary"


def on_your_own(row: Mapping[str, Any]) -> bool:
    """An attempt that can answer a "Check once": one the activity policy does
    not count as assisted (``causal_activity_policy.attempt_counts_as_assisted``,
    the one classification the projection, the facet timeline and
    certification read: a primed attempt, one with hints, a hinted attempt, a
    guided walkthrough or a reconstruction after one, an instructional
    diagnostic). Anything assisted is practice: it answers nothing and dates
    the check again (DL2 verify F13, orchestrator ruling R1 of fix round 4)."""

    return not attempt_counts_as_assisted(
        attempt_type=str(row.get("attempt_type") or ""),
        primed=bool(row.get("primed") or 0),
        hints_used=int(row.get("hints_used") or 0),
    )


def intent_enabled(config: Any) -> bool:
    """Is intent live for this config: at the successor (``mvp-0.29``) or a
    later tag, with ``intent.enabled`` on (DL2 Codex re-review F2)?"""

    from learnloop.algorithm_versions import INTENT_VERSIONS

    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    intent = getattr(config, "intent", None)
    return version in INTENT_VERSIONS and bool(getattr(intent, "enabled", False))


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
    #: Due candidates the eligibility decision lets serve cold (F3).
    eligible: tuple[str, ...] = ()
    #: Due candidates under a time-bounded hold (they wait).
    held: tuple[str, ...] = ()
    #: Due candidates with standing exposure (practice only).
    exposed: tuple[str, ...] = ()
    created_at: str = ""
    #: Due candidates holding a live assessment reservation (DL2 verify F16,
    #: fix round 5): never this check's item, whatever else admits them.
    reserved: tuple[str, ...] = ()

    @property
    def servable(self) -> tuple[str, ...]:
        """The candidates this check may serve now: the eligible ones; with
        none, nothing while a hold lasts; else the exposed ones, as practice."""

        if not self.due or self.answered_by is not None:
            return ()
        if self.eligible:
            return self.eligible
        if self.held:
            return ()
        return self.exposed

    def cold(self, item_id: str) -> bool:
        return item_id in self.eligible


@dataclass
class IntentServing:
    resolution: Resolution
    now: datetime
    item_learning_objects: Mapping[str, str]
    recall_targets_enabled: bool
    weights: tuple[float, ...]
    #: Every pending check, dated and answered, before the split (R1).
    raw_checks: dict[str, CheckState]
    _anchor_loader: Any = None
    _anchors: dict[str, tuple[str, str]] | None = None
    _intents: dict[str, ItemIntent] = field(default_factory=dict)
    _fallback_items: dict[str, set[str]] = field(default_factory=dict)
    #: ``eligibility(item_id, check_created_at)``: the one eligibility decision's verdict.
    _eligibility: Any = None
    #: ``admitted(item_id)``: the build's admission predicate (R1).
    _admission: Any = None
    #: Builds the admission for a view no queue build bound (``scheduler.check_admission``).
    _admission_factory: Any = None
    _checks: dict[str, CheckState] | None = None
    #: ``reserved_items()``: the items a live assessment reservation holds (F16).
    _reserved_loader: Any = None

    # -- the checks, split among admitted candidates (R1) ----------------------

    def bind_admission(self, admitted: Any) -> None:
        """Split the due checks with this admission (``build_due_queue``'s own)."""

        self._admission = admitted
        self._checks = None

    @property
    def checks(self) -> dict[str, CheckState]:
        if self._checks is None:
            if self._admission is None and self._admission_factory is not None:
                self._admission = self._admission_factory(self)
            reserved = self._reserved_loader() if self._reserved_loader is not None else frozenset()
            self._checks = {
                commitment_id: split_check(
                    check, eligibility=self._eligibility, admitted=self._admission, reserved=reserved
                )
                for commitment_id, check in self.raw_checks.items()
            }
        return self._checks

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
            if item_id in check.reserved:
                # F16: kept for an assessment; never a check's item.
                return "intent_check_reserved"
            if item_id not in check.servable:
                # F3: a hold on this candidate, or another can be taken cold.
                return "intent_check_held"
        return None

    def is_check_candidate(self, item_id: str) -> bool:
        check = self.check_for(item_id)
        return check is not None and item_id in check.servable

    def _anchor(self, item_id: str) -> str | None:
        if self._anchors is None:
            self._anchors = self._anchor_loader() if self._anchor_loader is not None else {}
        found = self._anchors.get(item_id)
        return found[0] if found is not None else None

    def last_review_at(self, item_id: str, state: Any) -> str | None:
        """The review that set ``due_at`` (the anchor), for the review-load
        interval (§6.3, F5); an item with no qualifying attempt (imported
        state) falls back to its ``last_attempt_at``, as DL1 reads it."""

        anchor = self._anchor(item_id)
        if anchor is not None:
            return anchor
        return getattr(state, "last_attempt_at", None) if state is not None else None

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
            for item_id in check.servable:
                if item_id not in seen:
                    kept.append(item_id)
                    seen.add(item_id)
        return kept

    def due_checks(self) -> list[CheckState]:
        return sorted(
            (check for check in self.checks.values() if check.servable),
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
                (item_id for item_id in check.servable if item_id in positions),
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
            if check is None or item_id not in check.servable:
                continue
            if check.commitment_id in claimed:
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
    cold_at: Any = None,
) -> tuple[dict[str, CheckState], Resolution]:
    """Every pending "Check once" with its date and the items it decides;
    answered ones are folded to ``satisfied`` in the returned resolution.
    Not yet split (:func:`split_check` does that among admitted candidates).

    ``attempts_since(item_ids, since)`` returns attempt rows (``id``,
    ``created_at``, ``primed``, ``hints_used``, ``attempt_type``), oldest
    first; ``cold_at(row, check_created_at)`` the eligibility verdict at an
    attempt on your own (only ``serve`` answers the check; None: every such
    attempt does, F3)."""

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
        answer: Mapping[str, Any] | None = None
        for row in attempts:
            at = parse_utc(str(row["created_at"]))
            if at is None or at < when:
                continue
            if at > now:
                break
            if on_your_own(row) and (cold_at is None or cold_at(row, snapshot.created_at) == _SERVE):
                answer = row
                break
            # Practice, not a check on your own (help taken, or the answer
            # seen first): it answers nothing, and the check waits its delay
            # again from this attempt (F3).
            when, source = at + timedelta(days=int(default_days)), DATE_FROM_PRACTICE
        answered_by = str(answer["id"]) if answer is not None else None
        checks[snapshot.id] = CheckState(
            commitment_id=snapshot.id,
            date=when,
            date_source=source,
            candidates=decided,
            due=when <= now,
            answered_by=answered_by,
            item_level=bool(snapshot.item_targets),
            provenance=dict(snapshot.provenance),
            created_at=snapshot.created_at,
        )
        if answer is not None:
            answered.append(replace(snapshot, disposition="satisfied", satisfied_at=str(answer["created_at"])))
    for snapshot in answered:
        resolution = resolution.with_snapshot(snapshot)
    return checks, resolution


def split_check(
    check: CheckState, *, eligibility: Any = None, admitted: Any = None, reserved: frozenset[str] = frozenset()
) -> CheckState:
    """A due, unanswered check's candidates split by the eligibility decision
    (``eligibility(item_id, check_created_at)``; None: every one eligible),
    among those the build admits (``admitted(item_id)``; None: every one).

    A candidate the build would not serve is left out before the split, so
    it can neither be the check nor suppress one that can be served (R1).
    A candidate on a live assessment reservation (``reserved``) is set aside
    the same way, into ``reserved`` (DL2 verify F16, fix round 5): a check is
    exempt from value and count composition, never from a mandatory
    constraint, so an LO check takes an eligible sibling by its own rule, and
    a check left with none says why."""

    if not check.due or check.answered_by is not None:
        return check
    eligible: list[str] = []
    held: list[str] = []
    exposed: list[str] = []
    set_aside: list[str] = []
    for item_id in check.candidates:
        if admitted is not None and not admitted(item_id):
            continue
        if item_id in reserved:
            set_aside.append(item_id)
            continue
        verdict = _SERVE if eligibility is None else eligibility(item_id, check.created_at)
        if verdict == _SERVE:
            eligible.append(item_id)
        elif verdict == _SERVE_AS_ORDINARY:
            exposed.append(item_id)
        else:
            held.append(item_id)
    return replace(
        check, eligible=tuple(eligible), held=tuple(held), exposed=tuple(exposed), reserved=tuple(set_aside)
    )


def reserved_assessment_items(repository: Any) -> frozenset[str]:
    """The practice items whose surface holds a live assessment reservation
    (``activity_surface_reservations``; the staged frame's own read, which
    refuses them on Today): F16."""

    return frozenset(
        str(row["legacy_practice_item_id"])
        for row in repository.reserved_assessment_surfaces()
        if row.get("legacy_practice_item_id")
    )


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

    now_iso = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def eligibility(item_id: str, check_created_at: str) -> str:
        # F3: the one eligibility decision, as every measurement asks it.
        from learnloop import serve_eligibility

        inputs = serve_eligibility.gather(
            repository,
            practice_item_id=item_id,
            learning_object_id=item_los.get(item_id),
            at=now_iso,
            check_created_at=check_created_at,
        )
        return serve_eligibility.decide(inputs, serve_eligibility.CHECK_ONCE).verdict

    def cold_at(row: Mapping[str, Any], check_created_at: str) -> str:
        # F3 (re-review): the decision as it stood when the attempt was
        # submitted; only a cold one answers the check.
        from learnloop import serve_eligibility

        item_id = str(row["practice_item_id"])
        return serve_eligibility.check_once_at_attempt(
            repository,
            practice_item_id=item_id,
            learning_object_id=item_los.get(item_id),
            attempt_id=str(row["id"]),
            attempt_at=str(row["created_at"]),
            check_created_at=check_created_at,
        ).verdict

    def default_admission(view: IntentServing) -> Any:
        # R1: the scheduler's one admission predicate over this view's own
        # reads (a queue build binds its own instead).
        from learnloop.scheduling.scheduler import check_admission

        return check_admission(vault, repository, now=now, intent_view=view)

    checks, resolution = build_checks(
        resolution,
        by_lo=by_lo,
        item_los=item_los,
        now=now,
        default_days=int(config.capture.test_me_later_days),
        attempts_since=attempts_since,
        cold_at=cold_at,
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
        raw_checks=checks,
        _anchor_loader=anchors,
        _eligibility=eligibility,
        _admission_factory=default_admission,
        # Looked up at call time, so a test can stand in for the read.
        _reserved_loader=lambda: reserved_assessment_items(repository),
    )


__all__ = [
    "CheckState",
    "DATE_FROM_DEFAULT",
    "DATE_FROM_DUE_HINT",
    "DATE_FROM_PRACTICE",
    "IntentServing",
    "build_checks",
    "check_date",
    "intent_enabled",
    "intent_serving",
    "on_your_own",
    "reserved_assessment_items",
    "split_check",
]
