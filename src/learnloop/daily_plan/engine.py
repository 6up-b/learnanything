"""The plan container (``spec_daily_loop_v1.md`` §6.1-§6.8, §6.10, §7).

A **daily plan** belongs to one local calendar date (D9) and one vault. The
container owns minutes, lanes, finiteness, re-entry and the streak; at each
block boundary a source proposes candidates and a chooser picks one (§6.8).
What the container enforces, whatever the chooser prefers:

1. **Redistribution, then feasibility, before every choice.** A lane without a
   candidate under its minutes releases them in §6.2 step 4's order; a
   candidate is feasible only when its estimate fits both the plan's and its
   lane's remaining minutes. The chooser sees only feasible candidates.
2. **Closed choice.** An unknown or infeasible choice falls back to
   ``lane_quota_v1`` and is flagged ``fallback`` on the block event, as does a
   malformed one: a chooser never claims ``learner_pick``, and its propensity
   is a number in (0, 1] (review F7).
3. **Learner picks win** (``learner_pick``, no propensity) and displace the
   plan's tail rather than growing it.
4. **STOP_FOR_TODAY** is offered only below five minutes left or with nothing
   feasible.
5. **Decisions happen at block boundaries only.**
6. **Every decision is logged** as a ``block_chosen`` receipt with its
   candidate set.

The plan is finite (P1): its planned estimate never exceeds its budget.
Nothing new joins mid-plan except follow-ups produced by this session's
answers, which displace later planned items. "Keep going" is the only
extension. Estimates, the split and the plan never write evidence, mastery,
certification, coldness or FSRS state (L4), and replay never reads them (L5).
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from learnloop.algorithm_versions import DAILY_PLAN_VERSIONS
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.daily_plan.admission import (
    NewCandidate,
    ReviewItem,
    admit_new_material,
    more_new_tradeoff,
    projected_review_load,
)
from learnloop.daily_plan.chooser import CHOOSER_NAME, LaneQuotaChooser
from learnloop.daily_plan.estimates import Estimator, load_duration_evidence
from learnloop.daily_plan.lanes import (
    LegacyLanesSource,
    PoolItem,
    SOURCE_NAME,
    classify_pool,
    reentry_order,
    scheduled_checks,
)
from learnloop.daily_plan.reading import next_reading_target, section_start_span
from learnloop.daily_plan.records import (
    ORIGIN_CHOOSER,
    ORIGIN_FOLLOWUP,
    ORIGIN_LEARNER_PICK,
    ORIGIN_REQUESTED,
    PlanRecord,
    PlannedBlock,
    PlannedItem,
    RECEIPT_OPEN_LIST_PICK,
    RECEIPT_STOP,
    assemble,
)
from learnloop.daily_plan.reentry import ReentryGap, reentry_gap
from learnloop.daily_plan.split import redistribute, split_v1
from learnloop.daily_plan.types import (
    CONTINUE_CURRENT,
    LANE_ACTIONS,
    LANES,
    PICK_DEDUCTION_ORDER,
    REENTRY_LANES,
    STOP_FOR_TODAY,
    STOP_OFFER_MINUTES,
    BlockCandidate,
    BlockChoice,
    BlockChooser,
    BlockSource,
    IntentView,
    PlanState,
    ReadingTarget,
)
from learnloop.db.stores import daily_plans as store
from learnloop.ids import new_ulid

_EPS = 1e-6
ENGINE_VERSION = "daily_plan_v1"


class PlanInactiveError(RuntimeError):
    """The plan is off: a pre-mvp-0.12 vault or ``plan.enabled = false``."""


def plan_active(vault: Any) -> bool:
    """The plan serves only at a daily-plan version with the kill switch on."""

    return (
        vault.config.algorithms.algorithm_version in DAILY_PLAN_VERSIONS
        and bool(vault.config.plan.enabled)
    )


def local_date(clock: Clock | None = None) -> str:
    """The plan's day: the machine's local calendar date, like the streak (D9)."""

    return (clock or SystemClock()).now().astimezone().date().isoformat()


def local_day_start_iso(clock: Clock | None = None) -> str:
    """The start of the plan's day (local midnight), as a UTC timestamp."""

    local_now = (clock or SystemClock()).now().astimezone()
    midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- the source/chooser seam ---------------------------------------------------


@dataclass(frozen=True)
class PoolContext:
    """What a source may be built from at one boundary (§6.8)."""

    pool: tuple[PoolItem, ...]
    lanes_allowed: tuple[str, ...]
    admitted_new_ids: frozenset[str]
    admitted_new_minutes: float
    reading: ReadingTarget | None
    reading_full_minutes: float | None
    titles: Mapping[str, str]
    gap: ReentryGap
    streak_days: int
    candidate_ids: Mapping[str, str | None] = field(default_factory=dict)
    deadlines: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanPolicy:
    """The source and chooser pair. Router R2 supplies its own (§6.8 table).

    ``chooser`` makes the logged block decisions, at block boundaries only.
    ``projection_chooser`` is what the plan view runs forward to project the
    blocks after the chosen ones ("Block 2 of about 3", the re-entry figures,
    G3). It runs on every plan read and logs nothing, so it must be cheap,
    pure and deterministic: never a sampled or model-backed chooser (review F3).
    The source is shared; sources are pure already (the container probes them
    for redistribution).
    """

    source_name: str
    chooser: BlockChooser
    make_source: Callable[[PoolContext], BlockSource]
    projection_chooser: BlockChooser = field(default_factory=LaneQuotaChooser)

    def projection(self) -> "PlanPolicy":
        """The pair the view projects with: this source, the projection chooser."""

        return PlanPolicy(
            source_name=self.source_name,
            chooser=self.projection_chooser,
            make_source=self.make_source,
            projection_chooser=self.projection_chooser,
        )


def legacy_source(context: PoolContext) -> BlockSource:
    return LegacyLanesSource(
        pool=context.pool,
        lanes_allowed=context.lanes_allowed,
        admitted_new_ids=context.admitted_new_ids,
        reading=context.reading,
        reading_full_minutes=context.reading_full_minutes,
        titles=context.titles,
    )


DEFAULT_POLICY = PlanPolicy(source_name=SOURCE_NAME, chooser=LaneQuotaChooser(), make_source=legacy_source)

#: ``(minutes) -> the scheduler's ranked eligible list``. The sidecar supplies
#: Today's own build (teach-back filter, offer finalization) so a served plan
#: item carries the candidate id of the slate that ranked it.
EligibleBuilder = Callable[[float], Sequence[Any]]


@dataclass
class PlanEnv:
    vault: Any
    repository: Any
    clock: Clock | None = None
    session_id: str | None = None
    eligible: EligibleBuilder | None = None
    policy: PlanPolicy = DEFAULT_POLICY

    def now(self) -> datetime:
        return (self.clock or SystemClock()).now().astimezone(UTC)

    def now_iso(self) -> str:
        return utc_now_iso(self.clock)

    def today(self) -> str:
        return local_date(self.clock)

    def gap(self) -> ReentryGap:
        """The break since the last real activity (§7, F1), sessions left open
        from an earlier day counting as activity (review F2)."""

        return reentry_gap(
            self.repository,
            now=self.now(),
            threshold_days=int(self.vault.config.hypothesis.reentry_gap_days),
            stale_open_before=local_day_start_iso(self.clock),
        )

    @property
    def plan_config(self) -> Any:
        return self.vault.config.plan

    def build_eligible(self, minutes: float) -> list[Any]:
        if self.eligible is not None:
            return list(self.eligible(minutes))
        from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue

        return build_due_queue(
            self.vault,
            self.repository,
            clock=self.clock,
            session=SchedulerSession(session_id=self.session_id, available_minutes=int(round(minutes))),
            limit=None,
        )


# -- loading -----------------------------------------------------------------


def load_records(repository: Any, plan_ids: Iterable[str] | None = None, *, local_date_value: str | None = None) -> list[PlanRecord]:
    with repository.connection() as connection:
        return load_records_from_connection(connection, plan_ids, local_date_value=local_date_value)


def load_records_from_connection(
    connection: Any, plan_ids: Iterable[str] | None = None, *, local_date_value: str | None = None
) -> list[PlanRecord]:
    """Fold the persisted plans (all, by id, or one day's) into records. Read-only."""

    if not store.daily_plan_tables_present(connection):
        return []
    if local_date_value is not None:
        rows = store.plans_for_date(connection, local_date_value)
    elif plan_ids is not None:
        rows = [row for plan_id in plan_ids if (row := store.plan_by_id(connection, plan_id)) is not None]
    else:
        rows = store.all_plans(connection)
    blocks = store.plan_blocks(connection, [row["id"] for row in rows])
    events = store.block_events_for(connection, [block["id"] for block in blocks])
    return assemble(rows, blocks, events)


def day_records(env: PlanEnv) -> list[PlanRecord]:
    return load_records(env.repository, local_date_value=env.today())


def latest_today(env: PlanEnv) -> PlanRecord | None:
    records = day_records(env)
    return records[-1] if records else None


def _reload(env: PlanEnv, plan_id: str) -> PlanRecord:
    (record,) = load_records(env.repository, [plan_id])
    return record


# -- minutes -----------------------------------------------------------------


def remembered_minutes(env: PlanEnv) -> tuple[int, str]:
    """Today's default budget (§6.6): the latest plan's remembered minutes;
    before the first plan, the last session's minutes; on a fresh vault, 25."""

    with env.repository.connection() as connection:
        latest = store.latest_plan(connection) if store.daily_plan_tables_present(connection) else None
    if latest is not None:
        return int(latest["remembered_minutes"]), "carried"
    last = env.repository.latest_session_minutes()
    if last is not None and int(last[0]) > 0:
        return int(last[0]), "last_session"
    return int(env.plan_config.default_minutes), "first_run"


# -- events ----------------------------------------------------------------------


def _event(connection: Any, block_id: str, kind: str, detail: Mapping[str, Any], at: str) -> None:
    store.append_block_event(
        connection, event_id=new_ulid(), block_id=block_id, kind=kind, detail=detail, created_at=at
    )


# -- the pool --------------------------------------------------------------------


def _titles(vault: Any) -> dict[str, str]:
    return {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}


def _deadlines(vault: Any, repository: Any) -> dict[str, str]:
    """LOs on an active goal with a due date (§5.4: a deadline is a goal)."""

    from learnloop.goals.goal_projection import resolve_goal_scope

    deadlines: dict[str, str] = {}
    for goal in vault.goals:
        if getattr(goal, "status", None) != "active" or not getattr(goal, "due_at", None):
            continue
        try:
            scope = resolve_goal_scope(vault, goal, repository)
        except Exception:  # noqa: BLE001 - a malformed goal never blocks the plan
            continue
        for lo_id in scope:
            current = deadlines.get(lo_id)
            if current is None or str(goal.due_at) < current:
                deadlines[lo_id] = str(goal.due_at)
    return deadlines


def _estimator(env: PlanEnv) -> Estimator:
    config = env.plan_config
    evidence = load_duration_evidence(env.repository, latency_cap_minutes=float(config.latency_cap_minutes))
    return Estimator(evidence=evidence, read_words_per_minute=int(config.read_words_per_minute))


@dataclass
class _Pool:
    scheduled: list[Any]
    pool: list[PoolItem]
    estimator: Estimator
    deadlines: dict[str, str]


def _classified_pool(
    env: PlanEnv,
    *,
    minutes: float,
    lanes_allowed: Sequence[str],
    day: Sequence[PlanRecord],
    reentry: bool,
) -> _Pool:
    scheduled = env.build_eligible(minutes)
    estimator = _estimator(env)
    states = env.repository.practice_item_states()
    requested = env.repository.requested_practice_item_ids()
    ids = [item.practice_item_id for item in scheduled]
    checks = scheduled_checks(env.vault, env.repository, ids)
    probes_planned = sum(
        1 for record in day for item in record.active_items() if item.check_kind == "project_probe"
    )
    deadlines = _deadlines(env.vault, env.repository)
    pool = classify_pool(
        scheduled,
        item_states=states,
        requested_ids=requested,
        now=env.now(),
        estimate=lambda item_id: estimator.item_minutes(env.vault, item_id),
        checks=checks,
        probe_cap_left=max(int(env.plan_config.project_probes_max_per_day) - probes_planned, 0),
        deadline_learning_object_ids=deadlines,
    )
    if reentry:
        pool = reentry_order(pool)
    pool = [item if item.lane in lanes_allowed else replace(item, lane=None) for item in pool]
    return _Pool(scheduled=list(scheduled), pool=pool, estimator=estimator, deadlines=deadlines)


def _review_items(env: PlanEnv, estimator: Estimator) -> list[ReviewItem]:
    from learnloop.vault.lifecycle import practice_item_servable

    vault = env.vault
    items: list[ReviewItem] = []
    for item_id, state in env.repository.practice_item_states().items():
        if not state.active or state.due_at is None or state.stability is None:
            continue
        item = vault.practice_items.get(item_id)
        if item is None or item.status != "active" or not practice_item_servable(vault, item):
            continue
        items.append(
            ReviewItem(
                practice_item_id=item_id,
                due_at=state.due_at,
                last_review_at=state.last_attempt_at,
                est_minutes=estimator.item_minutes(vault, item_id),
            )
        )
    return items


def _streak(env: PlanEnv) -> int:
    try:
        return int(env.repository.session_day_streak(clock=env.clock).get("current") or 0)
    except Exception:  # noqa: BLE001 - display only
        return 0


def _reading_used_today(day: Sequence[PlanRecord]) -> bool:
    return any(block.is_reading for record in day for block in record.blocks)


def _new_planned_today(day: Sequence[PlanRecord]) -> int:
    """New items actually planned today, across plans and extensions (§6.3 cap)."""

    return sum(1 for record in day for item in record.active_items() if item.new_admitted)


# -- building a plan --------------------------------------------------------------


def get_or_create_today(env: PlanEnv, *, create: bool = True) -> PlanRecord | None:
    """Today's latest plan, building the day's first one when there is none."""

    if not plan_active(env.vault):
        raise PlanInactiveError("the daily plan is off")
    today = env.today()
    with env.repository.connection() as connection:
        stale = store.daily_plan_tables_present(connection) and connection.execute(
            "SELECT 1 FROM daily_plans WHERE status = 'open' AND local_date < ? LIMIT 1", (today,)
        ).fetchone() is not None
    if stale:
        with env.repository.atomic(), env.repository.connection() as connection:
            store.abandon_open_plans_before(connection, today, now=env.now_iso())
    record = latest_today(env)
    if record is not None or not create:
        return record
    minutes, _source = remembered_minutes(env)
    gap = env.gap()
    if gap.due:
        budget = float(min(minutes, int(env.plan_config.reentry_minutes)))
        return build_plan(env, kind="reentry", budget=budget, remembered=minutes, minutes_source="carried")
    return build_plan(env, kind="normal", budget=float(minutes), remembered=minutes, minutes_source="carried")


@dataclass
class _Prepared:
    """A plan classified, admitted and split, not yet persisted."""

    built: _Pool
    requests: list[PoolItem]
    admission: Any
    row: dict[str, Any]
    day: list[PlanRecord]

    def record(self, plan_id: str = "preview") -> PlanRecord:
        """The plan as it would be loaded, with no blocks (a dry run)."""

        row = {key: value for key, value in self.row.items() if key not in ("split_json", "admission_json")}
        row.update(id=plan_id, split=dict(self.row["split_json"]), admission=dict(self.row["admission_json"]))
        return PlanRecord(row=row)


def _prepare_plan(
    env: PlanEnv,
    *,
    kind: str,
    budget: float,
    remembered: int,
    minutes_source: str,
    parent_plan_id: str | None = None,
    override: str | None = None,
) -> _Prepared:
    """Classify, admit and split one plan (§6.1-§6.3) without persisting it."""

    config = env.plan_config
    reentry = kind == "reentry"
    lanes_allowed = REENTRY_LANES if reentry else LANES
    day = day_records(env)
    built = _classified_pool(env, minutes=budget, lanes_allowed=lanes_allowed, day=day, reentry=reentry)
    pool = built.pool
    # Requests first (L3): up to requested_items_per_session go in the first
    # block, their estimates deducted from the budget before the split.
    per_session = int(env.vault.config.tutor_promotion.requested_items_per_session)
    requests: list[PoolItem] = []
    requested_minutes = 0.0
    for item in pool:
        if len(requests) >= per_session:
            break
        if not item.requested or item.lane is None:
            continue
        if requested_minutes + item.est_minutes > budget + _EPS:
            continue
        requests.append(item)
        requested_minutes += item.est_minutes
    request_ids = {item.practice_item_id for item in requests}
    rest = [item for item in pool if item.practice_item_id not in request_ids]
    loads = {lane: 0.0 for lane in LANES}
    for item in rest:
        if item.lane in loads and item.lane != "new":
            loads[item.lane] += item.est_minutes
    m = max(budget - requested_minutes, 0.0)
    new_candidates = [
        NewCandidate(item.practice_item_id, item.est_minutes, requested=item.requested)
        for item in rest
        if item.lane == "new" and item.never_attempted
    ]
    review_load = projected_review_load(
        _review_items(env, built.estimator), now=env.now(), horizon_days=int(config.load_horizon_days)
    )
    # L is a daily load, so its ceiling is 0.80 of a daily budget: the plan's
    # own M for the day's plan, the remembered budget for an extension or the
    # plan after re-entry (whose own minutes are only what is left; F9).
    extension = parent_plan_id is not None
    admission = admit_new_material(
        new_candidates,
        review_load_per_day=review_load,
        m=float(remembered) if extension else m,
        ceiling_basis="remembered_minutes" if extension else "plan_minutes",
        load_ceiling=float(config.load_ceiling),
        horizon_days=int(config.load_horizon_days),
        reviews_per_new_item=int(config.new_item_reviews_14d),
        cap_per_day=int(config.max_new_items_per_day),
        floor_per_day=int(config.min_new_items_per_day),
        planned_today=_new_planned_today(day),
        enabled=bool(config.new_admission_enabled),
        reentry=reentry,
        override=override,
    )
    reading: ReadingTarget | None = None
    reading_full: float | None = None
    if bool(config.reading_blocks) and not reentry and override is None and not _reading_used_today(day):
        reading = next_reading_target(env.repository)
        if reading is not None:
            reading_full = built.estimator.reading_minutes(reading.words_left)
    admitted_new_minutes = admission.admitted_minutes + (reading_full or 0.0)
    loads["new"] = admitted_new_minutes
    split = split_v1(
        budget=budget,
        requested_minutes=requested_minutes,
        loads=loads,
        admitted_new_minutes=admitted_new_minutes,
        push_candidates=any(item.lane == "push" for item in rest),
        repair_max_share=float(config.repair_max_share),
        maintain_max_share=float(config.maintain_max_share),
        lanes_allowed=lanes_allowed,
        new_first=override == "more_new",
    )
    gap = env.gap()
    split_json = {
        **split.as_dict(),
        "epoch_ordinal": 1,
        "kind": kind,
        "requested": [
            {"practice_item_id": item.practice_item_id, "est_minutes": round(item.est_minutes, 4)}
            for item in requests
        ],
        "admitted_new_minutes": round(admitted_new_minutes, 4),
        "reading": reading.as_dict() if reading is not None else None,
        "reading_full_minutes": round(reading_full, 4) if reading_full is not None else None,
        # The plan's universe: nothing new joins mid-plan (§6.1), except
        # follow-ups produced by this session's answers.
        "universe": [item.practice_item_id for item in pool],
        "followups_at_build": [item.practice_item_id for item in pool if item.followup],
        "pool": [item.as_dict() for item in pool if item.lane is not None][:400],
        "reentry_gap": {"due": gap.due, "gap_days": gap.gap_days, "threshold_days": gap.threshold_days, "last_activity_at": gap.last_activity_at},
        "items_cap": int(config.reentry_max_items) if reentry else None,
        "replans": [],
    }
    now = env.now_iso()
    row = {
        "local_date": env.today(),
        "kind": kind,
        "parent_plan_id": parent_plan_id,
        "minutes_budget": float(budget),
        "remembered_minutes": int(remembered),
        "minutes_source": minutes_source,
        "split_json": split_json,
        "admission_json": admission.as_dict(),
        "estimator_version": built.estimator.version,
        "source": env.policy.source_name,
        "chooser": getattr(env.policy.chooser, "name", CHOOSER_NAME),
        "status": "open",
        "stop_reason": None,
        "algorithm_version": env.vault.config.algorithms.algorithm_version,
        "config_hash": _config_hash(config),
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    return _Prepared(built=built, requests=requests, admission=admission, row=row, day=list(day))


def simulate_blocks(
    record: PlanRecord,
    context: PoolContext,
    policy: PlanPolicy,
    *,
    forced: Sequence[PoolItem] = (),
    max_blocks: int = 12,
) -> list[tuple[Decision, PlannedBlock]]:
    """The blocks the plan would choose next if nothing changed. Pure.

    Always runs ``policy.projection()``: the source with the deterministic
    projection chooser, never the live one (review F3). ``forced`` items (a
    fresh plan's requests) join the first simulated block, as at the build.
    The record is copied; nothing is persisted or logged.
    """

    import copy

    policy = policy.projection()
    sim = PlanRecord(row=copy.deepcopy(record.row), blocks=copy.deepcopy(record.blocks))
    out: list[tuple[Decision, PlannedBlock]] = []
    reading_used = any(block.is_reading for block in sim.blocks)
    pending = list(forced)
    for _ in range(max_blocks):
        taken = sim.planned_ids() | {item.practice_item_id for item in sim.items() if item.skipped}
        view = replace(
            context,
            pool=tuple(item for item in context.pool if item.practice_item_id not in taken),
            reading=None if reading_used else context.reading,
        )
        decision = decide(
            sim, view, policy, forced_minutes=sum(item.est_minutes for item in pending), forced_items=len(pending)
        )
        candidate = decision.candidate
        if candidate is None and not pending:
            break
        ordinal = sim.next_ordinal()
        block = PlannedBlock(
            id=f"projected-{ordinal}",
            ordinal=ordinal,
            lane=candidate.lane if candidate is not None else pending[0].lane,
            action=candidate.action if candidate is not None else "maintain",
            subtype=candidate.subtype if candidate is not None else None,
            chosen_by=decision.choice.chosen_by,
            budget_minutes=(candidate.est_minutes if candidate is not None else 0.0)
            + sum(item.est_minutes for item in pending),
            created_at=str(record.row.get("updated_at") or ""),
            reading=candidate.reading.as_dict() if candidate is not None and candidate.reading is not None else None,
            chosen={"redistribution": decision.redistribution},
            simulated=True,
        )
        by_id = {item.practice_item_id: item for item in view.pool}
        members = [(item, ORIGIN_REQUESTED) for item in pending]
        if candidate is not None:
            members += [(by_id[item_id], ORIGIN_CHOOSER) for item_id in candidate.item_ids if item_id in by_id]
        for position, (pool_item, origin) in enumerate(members, start=1):
            block.items.append(
                PlannedItem(
                    block_id=block.id,
                    position=position,
                    practice_item_id=pool_item.practice_item_id,
                    learning_object_id=pool_item.learning_object_id,
                    lane=pool_item.lane,
                    est_minutes=pool_item.est_minutes,
                    origin=origin,
                    planned_at="",
                    new_admitted=bool(
                        origin == ORIGIN_CHOOSER
                        and pool_item.lane == "new"
                        and pool_item.never_attempted
                        and not pool_item.requested
                    ),
                )
            )
        pending = []
        sim.blocks.append(block)
        if candidate is not None and candidate.reading is not None:
            reading_used = True
        out.append((decision, block))
    return out


def _empty_extension(env: PlanEnv, prepared: _Prepared) -> bool:
    """Whether a prepared extension would plan nothing at all (no request, no
    feasible block at its first boundary). Decided by the container's
    feasibility, never by asking the live chooser."""

    if prepared.requests:
        return False
    record = prepared.record()
    context = _context(env, record, prepared.built, day=prepared.day)
    return not decide(record, context, env.policy.projection()).feasible


def build_plan(
    env: PlanEnv,
    *,
    kind: str,
    budget: float,
    remembered: int,
    minutes_source: str,
    parent_plan_id: str | None = None,
    override: str | None = None,
) -> PlanRecord:
    """Build one plan: classify, admit, split, then choose its first block."""

    prepared = _prepare_plan(
        env,
        kind=kind,
        budget=budget,
        remembered=remembered,
        minutes_source=minutes_source,
        parent_plan_id=parent_plan_id,
        override=override,
    )
    if kind == "keep_going" and prepared.day:
        # "Keep going" with nothing left to plan is idempotent: one empty
        # extension says so, and further taps return it rather than adding
        # an empty plan row each time (review F10).
        latest = prepared.day[-1]
        if (
            latest.kind == "keep_going"
            and not latest.is_open
            and not latest.blocks
            and _empty_extension(env, prepared)
        ):
            return latest
    plan_id = new_ulid()
    today = prepared.row["local_date"]
    with env.repository.atomic(), env.repository.connection() as connection:
        # Another builder (a second device, a retried RPC) may have made today's
        # first plan meanwhile: keep that one.
        if kind != "keep_going" and parent_plan_id is None:
            existing = store.plans_for_date(connection, today)
            if existing:
                return _reload(env, str(existing[-1]["id"]))
        store.insert_plan(connection, {"id": plan_id, **prepared.row})
    record = _reload(env, plan_id)
    context = _context_from_build(env, record, prepared.built)
    _boundary(env, record, context, forced=prepared.requests, forced_origin=ORIGIN_REQUESTED)
    return _reload(env, plan_id)


def _config_hash(config: Any) -> str:
    payload = json.dumps(config.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _context_from_build(env: PlanEnv, record: PlanRecord, built: _Pool) -> PoolContext:
    return _context(env, record, built, day=day_records(env))


def _context(env: PlanEnv, record: PlanRecord, built: _Pool, *, day: Sequence[PlanRecord]) -> PoolContext:
    """The source's view at one boundary: the plan's universe minus what it took."""

    split = record.split
    universe = set(split.get("universe") or [])
    taken = record.planned_ids()
    # Skipped items stay out of this plan (the learner skipped them).
    taken |= {item.practice_item_id for item in record.items() if item.skipped}
    pool = tuple(
        item
        for item in built.pool
        if item.practice_item_id in universe and item.practice_item_id not in taken
    )
    admission = record.admission
    admitted_ids = frozenset(
        [row["practice_item_id"] for row in admission.get("admitted") or []]
        + [row["practice_item_id"] for row in admission.get("exempt_requests") or []]
    )
    reading_row = split.get("reading")
    reading = None
    reading_full = None
    if reading_row and not any(block.is_reading for block in record.blocks):
        reading = ReadingTarget(**{key: reading_row[key] for key in ("source_id", "extraction_id", "section_id", "section_title", "words_left")})
        reading_full = float(split.get("reading_full_minutes") or 0.0)
    gap_row = split.get("reentry_gap") or {}
    gap = ReentryGap(
        bool(gap_row.get("due")), int(gap_row.get("gap_days") or 0), int(gap_row.get("threshold_days") or 0), gap_row.get("last_activity_at")
    )
    return PoolContext(
        pool=pool,
        lanes_allowed=record.lanes_allowed,
        admitted_new_ids=admitted_ids,
        admitted_new_minutes=float(split.get("admitted_new_minutes") or 0.0),
        reading=reading,
        reading_full_minutes=reading_full,
        titles=_titles(env.vault),
        gap=gap,
        streak_days=_streak(env),
        candidate_ids={
            item.practice_item_id: getattr(item, "scheduler_candidate_id", None) for item in built.scheduled
        },
        deadlines=built.deadlines,
    )


def _live_context(env: PlanEnv, record: PlanRecord) -> tuple[PoolContext, _Pool]:
    built = _classified_pool(
        env,
        minutes=record.budget,
        lanes_allowed=record.lanes_allowed,
        day=day_records(env),
        reentry=record.kind == "reentry",
    )
    return _context(env, record, built, day=()), built


# -- one block decision ------------------------------------------------------------


@dataclass
class Decision:
    candidate: BlockCandidate | None
    choice: BlockChoice
    state: PlanState
    candidates: list[BlockCandidate]
    feasible: list[BlockCandidate]
    redistribution: dict[str, Any] | None
    fallback: bool
    fallback_from: str | None
    stop_offered: bool
    fallback_reason: str | None = None


def _items_left(record: PlanRecord, *, forced_items: int = 0) -> int | None:
    cap = record.split.get("items_cap")
    if cap is None:
        return None
    return max(int(cap) - record.item_count() - int(forced_items), 0)


def _intents(context: PoolContext) -> dict[str, IntentView]:
    los = {item.learning_object_id for item in context.pool}
    return {lo: IntentView(deadline=context.deadlines.get(lo)) for lo in sorted(los)}


def decide(
    record: PlanRecord,
    context: PoolContext,
    policy: PlanPolicy,
    *,
    forced_minutes: float = 0.0,
    forced_items: int = 0,
    forced_allotment: Mapping[str, float] | None = None,
    forced_spent: Mapping[str, float] | None = None,
) -> Decision:
    """§6.8 at one boundary: redistribution, feasibility, choice, fallback. Pure.

    ``forced_*`` are the items the container places in this block whatever is
    chosen (requests first, mid-plan follow-ups): they come out of the plan's
    minutes and a re-entry plan's item allowance before the choice, and
    follow-ups out of their lane (``forced_spent``, after the minutes other
    lanes release to it, ``forced_allotment``; review F4).
    """

    allotment, spent = record.ledger()
    for lane, delta in (forced_allotment or {}).items():
        if lane in allotment:
            allotment[lane] = max(allotment[lane] + float(delta), 0.0)
    for lane, minutes in (forced_spent or {}).items():
        if lane in spent:
            spent[lane] += float(minutes)
    lanes = context.lanes_allowed
    lefts = {lane: max(allotment[lane] - spent[lane], 0.0) if lane in lanes else 0.0 for lane in LANES}
    minutes_left = max(record.minutes_left() - forced_minutes, 0.0)
    items_left = _items_left(record, forced_items=forced_items)
    base = PlanState(
        plan_id=record.id,
        kind=record.kind,  # type: ignore[arg-type]
        minutes_budget=record.budget,
        minutes_left=minutes_left,
        lane_minutes_left=lefts,
        days_since_last_activity=context.gap.gap_days,
        streak_days=context.streak_days,
        current_block_id=None,
        intents=_intents(context),
        items_left=items_left,
        lane_minutes_allotted=dict(allotment),
    )
    source = policy.make_source(context)

    def has_candidate(lane: str, minutes: float) -> bool:
        probe = replace(base, lane_minutes_left={**lefts, lane: minutes})
        return any(
            candidate.lane == lane and candidate.est_minutes <= min(minutes, minutes_left) + _EPS
            for candidate in source.candidates(probe)
        )

    new_room = max(context.admitted_new_minutes - allotment.get("new", 0.0), 0.0)
    moved, releases = redistribute(lefts, has_candidate=has_candidate, new_room=new_room, lanes_allowed=lanes)
    redistribution = None
    allotted = dict(allotment)
    if releases:
        released = [record_ for record_ in releases if record_.get("from") in LANES]
        target = next((record_.get("to") for record_ in released if record_.get("to")), None)
        given = 0.0
        if target is not None:
            # What the target received: its new minutes less what it kept of
            # its own (it may have released its own minutes into the pool).
            own = sum(float(r["minutes"]) for r in released if r["from"] == target)
            given = moved[target] - (lefts[target] - own)
        for record_ in released:
            allotted[record_["from"]] -= float(record_["minutes"])
        if target is not None:
            allotted[target] += given
        redistribution = {
            "released": [{"from": r["from"], "minutes": r["minutes"]} for r in released],
            "to": target,
            "given": round(given, 6),
        }
    state = replace(base, lane_minutes_left=moved, lane_minutes_allotted=allotted)
    candidates = source.candidates(state)
    feasible = [
        candidate
        for candidate in candidates
        if candidate.lane in lanes
        and candidate.est_minutes <= minutes_left + _EPS
        and candidate.est_minutes <= moved.get(candidate.lane, 0.0) + _EPS
        and (items_left is None or len(candidate.item_ids) <= items_left)
        and (items_left is None or items_left > 0)
    ]
    stop_offered = minutes_left < STOP_OFFER_MINUTES or not feasible
    reason: str | None = None
    try:
        choice = policy.chooser.choose(state, feasible)
    except Exception as exc:  # noqa: BLE001 - a broken chooser falls back (rule 2)
        choice = BlockChoice(candidate_id=f"<error: {type(exc).__name__}>", chosen_by="lane_quota", propensity=None, why="", why_kind="computed")
        reason = "chooser_error"
    feasible_ids = {candidate.candidate_id for candidate in feasible}
    valid = choice.candidate_id in feasible_ids or (choice.candidate_id == STOP_FOR_TODAY and stop_offered)
    if reason is None and not valid:
        reason = "not_offered"
    if choice.candidate_id == CONTINUE_CURRENT:
        # Decisions happen at block boundaries, where nothing is in progress.
        valid = False
        reason = "continue_current_at_boundary"
    malformed = _malformed_choice(choice)
    if valid and malformed is not None:
        # A sampled choice recorded as the learner's, or with no usable
        # propensity, would corrupt L3 and the router's logging (G9).
        valid = False
        reason = malformed
    fallback_from = None
    if not valid:
        fallback_from = choice.candidate_id
        choice = LaneQuotaChooser().choose(state, feasible)
    candidate = next((c for c in feasible if c.candidate_id == choice.candidate_id), None)
    return Decision(
        candidate=candidate,
        choice=choice,
        state=state,
        candidates=candidates,
        feasible=feasible,
        redistribution=redistribution,
        fallback=not valid,
        fallback_from=fallback_from,
        fallback_reason=reason if not valid else None,
        stop_offered=stop_offered,
    )


#: Who may be named on a chooser's choice (§6.8): never ``learner_pick``,
#: which only the container records, for the learner's own choices (rule 3).
CHOOSER_CHOSEN_BY = frozenset({"lane_quota", "staged", "mixture"})
WHY_KINDS = frozenset({"computed", "model_written", "model_no_rationale"})


def _malformed_choice(choice: BlockChoice) -> str | None:
    """Why a chooser's choice cannot be recorded as given, or None (review F7)."""

    if choice.chosen_by not in CHOOSER_CHOSEN_BY:
        return "chosen_by_not_allowed"
    propensity = choice.propensity
    if (
        isinstance(propensity, bool)
        or not isinstance(propensity, (int, float))
        or not math.isfinite(float(propensity))
        or not 0.0 < float(propensity) <= 1.0
    ):
        return "propensity_out_of_range"
    if choice.why_kind not in WHY_KINDS:
        return "why_kind_unknown"
    return None


def _state_row(state: PlanState) -> dict[str, Any]:
    return {
        "minutes_budget": round(state.minutes_budget, 4),
        "minutes_left": round(state.minutes_left, 4),
        "lane_minutes_left": {lane: round(value, 4) for lane, value in state.lane_minutes_left.items()},
        "lane_minutes_allotted": {lane: round(value, 4) for lane, value in state.lane_minutes_allotted.items()},
        "items_left": state.items_left,
        "days_since_last_activity": state.days_since_last_activity,
        "streak_days": state.streak_days,
        "kind": state.kind,
    }


def _persist_block(
    env: PlanEnv,
    connection: Any,
    record: PlanRecord,
    *,
    lane: str | None,
    action: str,
    subtype: str | None,
    chosen_by: str,
    est_minutes: float,
    reading: ReadingTarget | None,
    reading_full: float | None,
    learning_object_ids: Sequence[str],
    detail: Mapping[str, Any],
    items: Sequence[tuple[PoolItem | PlannedItem, str]],
    decision_ref: str | None = None,
    ordinal: int | None = None,
    releases: Mapping[str, Mapping[str, Any] | None] | None = None,
) -> str:
    block_id = new_ulid()
    now = env.now_iso()
    reading_row = None
    if reading is not None:
        reading_row = {
            **reading.as_dict(),
            "full_minutes": round(reading_full or est_minutes, 4),
            "start_span_id": section_start_span(env.repository, reading.extraction_id, reading.section_id),
        }
    hash_material = json.dumps(
        {"plan": record.id, "lane": lane, "items": [item.practice_item_id for item, _ in items], "reading": reading_row},
        sort_keys=True,
    )
    store.insert_plan_block(
        connection,
        {
            "id": block_id,
            "session_id": env.session_id,
            "action": action,
            "subtype": subtype,
            "budget_minutes": est_minutes,
            "neighborhood": {"learning_object_ids": list(learning_object_ids)},
            "short_circuit_reason": "learner_pick" if chosen_by == "learner_pick" else None,
            "content_hash": hashlib.sha256(hash_material.encode("utf-8")).hexdigest(),
            "created_at": now,
            "daily_plan_id": record.id,
            "plan_ordinal": ordinal if ordinal is not None else record.next_ordinal(),
            "lane": lane,
            "chosen_by": chosen_by,
            "decision_ref": decision_ref,
            "reading": reading_row,
        },
    )
    _event(connection, block_id, "block_chosen", detail, now)
    for position, (item, origin) in enumerate(items, start=1):
        lane_value = item.lane
        _event(
            connection,
            block_id,
            "item_planned",
            {
                "practice_item_id": item.practice_item_id,
                "learning_object_id": item.learning_object_id,
                "lane": lane_value,
                "est_minutes": round(float(item.est_minutes), 4),
                "origin": origin,
                "position": position,
                "new_admitted": bool(
                    origin == ORIGIN_CHOOSER and lane_value == "new" and getattr(item, "never_attempted", False) and not getattr(item, "requested", False)
                ),
                "check_kind": getattr(item, "check_kind", None),
                "serving_origin": "learner_pick" if origin == ORIGIN_LEARNER_PICK else "daily_plan",
                **(
                    {"lane_release": dict(release)}
                    if (release := (releases or {}).get(item.practice_item_id)) is not None
                    else {}
                ),
            },
            now,
        )
    return block_id


def _boundary(
    env: PlanEnv,
    record: PlanRecord,
    context: PoolContext,
    *,
    forced: Sequence[PoolItem] = (),
    forced_origin: str = ORIGIN_REQUESTED,
) -> str | None:
    """Choose and persist the next block, or close the plan. Returns the block id."""

    forced = list(forced)
    forced_minutes = sum(item.est_minutes for item in forced)
    releases: dict[str, dict[str, Any] | None] = {}
    forced_allotment = {lane: 0.0 for lane in LANES}
    forced_spent = {lane: 0.0 for lane in LANES}
    if forced_origin == ORIGIN_FOLLOWUP and forced:
        # Follow-ups are charged to their lane, with minutes released to it by
        # the other lanes when it has too few left (review F4).
        lefts = record.lane_left()
        minutes_left = record.minutes_left()
        for item in forced:
            lane = item.lane or "repair"
            release = _followup_release(lefts, minutes_left, item.est_minutes, lane=lane, lanes_allowed=record.lanes_allowed)
            releases[item.practice_item_id] = release
            if release is not None:
                for entry in release["released"]:
                    forced_allotment[entry["from"]] -= entry["minutes"]
                    lefts[entry["from"]] = max(lefts[entry["from"]] - entry["minutes"], 0.0)
                forced_allotment[lane] += release["given"]
                lefts[lane] += release["given"]
            forced_spent[lane] += item.est_minutes
            lefts[lane] = max(lefts[lane] - item.est_minutes, 0.0)
            minutes_left = max(minutes_left - item.est_minutes, 0.0)
    decision = decide(
        record,
        context,
        env.policy,
        forced_minutes=forced_minutes,
        forced_items=len(forced),
        forced_allotment=forced_allotment,
        forced_spent=forced_spent,
    )
    choice = decision.choice
    detail: dict[str, Any] = {
        "source": env.policy.source_name,
        "chooser": getattr(env.policy.chooser, "name", "unknown"),
        "chosen_by": choice.chosen_by,
        "candidate_id": choice.candidate_id,
        "propensity": choice.propensity,
        "why": choice.why,
        "why_kind": choice.why_kind,
        "decision_ref": choice.decision_ref,
        "fallback": decision.fallback,
        "fallback_from": decision.fallback_from,
        "fallback_reason": decision.fallback_reason,
        "stop_offered": decision.stop_offered,
        "candidate_set": [candidate.log_row() for candidate in decision.candidates],
        "feasible_ids": [candidate.candidate_id for candidate in decision.feasible],
        "state": _state_row(decision.state),
        "redistribution": decision.redistribution,
        "forced": [
            {"practice_item_id": item.practice_item_id, "origin": forced_origin, "est_minutes": round(item.est_minutes, 4)}
            for item in forced
        ],
    }
    candidate = decision.candidate
    if candidate is None and not forced:
        _close(env, record, status="complete", reason=choice.why or "nothing more worth doing today", stop_detail=detail)
        return None
    items: list[tuple[PoolItem | PlannedItem, str]] = [(item, forced_origin) for item in forced]
    by_id = {item.practice_item_id: item for item in context.pool}
    if candidate is not None:
        items.extend((by_id[item_id], ORIGIN_CHOOSER) for item_id in candidate.item_ids if item_id in by_id)
        lane = candidate.lane
        action, subtype = candidate.action, candidate.subtype
        est = candidate.est_minutes + forced_minutes
        reading = candidate.reading
        los = list(candidate.learning_object_ids)
        chosen_by = choice.chosen_by
        decision_ref = choice.decision_ref
    else:
        # Nothing feasible but forced items (requests) wait: they are the
        # learner's own block (L3).
        lane = forced[0].lane
        action, subtype = LANE_ACTIONS.get(lane or "maintain", ("maintain", None))
        est = forced_minutes
        reading = None
        los = list(dict.fromkeys(item.learning_object_id for item in forced))
        chosen_by = "learner_pick" if forced_origin == ORIGIN_REQUESTED else "lane_quota"
        decision_ref = None
        detail["why"] = "your requested item comes first" if forced_origin == ORIGIN_REQUESTED else "a follow-up from this session's answer"
    for item, origin in items[: len(forced)]:
        los = list(dict.fromkeys([item.learning_object_id, *los]))
    with env.repository.atomic(), env.repository.connection() as connection:
        block_id = _persist_block(
            env,
            connection,
            record,
            lane=lane,
            action=action,
            subtype=subtype,
            chosen_by=chosen_by,
            est_minutes=est,
            reading=reading,
            reading_full=candidate.reading_full_minutes if candidate is not None else None,
            learning_object_ids=los,
            detail=detail,
            items=items,
            decision_ref=decision_ref,
            releases=releases,
        )
    return block_id


def _persist_receipt(
    env: PlanEnv,
    connection: Any,
    record: PlanRecord,
    *,
    action: str,
    chosen_by: str,
    detail: Mapping[str, Any],
    decision_ref: str | None = None,
    est_minutes: float = 0.0,
    learning_object_ids: Sequence[str] = (),
) -> str:
    """A plan-level receipt row: a decision that is not one of the plan's
    numbered blocks (a stop, a pick after the plan closed). Append-only: an
    ``attention_blocks`` row of the plan with no ordinal, and its
    ``block_chosen`` event (§6.8 rule 6; review F6, F10)."""

    receipt_id = new_ulid()
    now = env.now_iso()
    material = json.dumps({"plan": record.id, "receipt": receipt_id, "action": action}, sort_keys=True)
    store.insert_plan_block(
        connection,
        {
            "id": receipt_id,
            "session_id": env.session_id,
            "action": action,
            "subtype": None,
            "budget_minutes": float(est_minutes),
            "neighborhood": {"learning_object_ids": list(learning_object_ids)},
            "short_circuit_reason": action,
            "content_hash": hashlib.sha256(material.encode("utf-8")).hexdigest(),
            "created_at": now,
            "daily_plan_id": record.id,
            "plan_ordinal": None,
            "lane": None,
            "chosen_by": chosen_by,
            "decision_ref": decision_ref,
            "reading": None,
        },
    )
    _event(connection, receipt_id, "block_chosen", detail, now)
    return receipt_id


def _close(env: PlanEnv, record: PlanRecord, *, status: str, reason: str, stop_detail: Mapping[str, Any] | None = None) -> None:
    """Close the plan. A chooser's stop (``stop_detail``: the candidate set,
    chooser, propensity and fallback) is appended as a stop receipt, so a plan
    reopened by a minutes tap and stopped again keeps both decisions (F6)."""

    now = env.now_iso()
    with env.repository.atomic(), env.repository.connection() as connection:
        if stop_detail is not None:
            _persist_receipt(
                env,
                connection,
                record,
                action=RECEIPT_STOP,
                chosen_by=str(stop_detail.get("chosen_by") or "lane_quota"),
                decision_ref=stop_detail.get("decision_ref"),
                detail={**dict(stop_detail), "stop_reason": reason, "status": status},
            )
        store.update_plan(
            connection,
            record.id,
            status=status,
            stop_reason=reason,
            updated_at=now,
            completed_at=now,
        )


# -- reconciliation ---------------------------------------------------------------


def reconcile(env: PlanEnv, record: PlanRecord) -> PlanRecord:
    """Fold answers into the plan: done items, unservable items, finished blocks.

    An item is done once any attempt on it is recorded after it was planned,
    whichever surface served it (the plan, the full list, the TUI).
    """

    from learnloop.vault.lifecycle import practice_item_servable
    from learnloop.substrate.instrument_serving import unservable_reason

    open_items = [item for item in record.items() if not item.resolved]
    now = env.now_iso()
    writes: list[tuple[str, str, dict[str, Any]]] = []
    if open_items:
        earliest = min(item.planned_at for item in open_items)
        ids = sorted({item.practice_item_id for item in open_items})
        marks = ",".join("?" for _ in ids)
        with env.repository.connection() as connection:
            rows = connection.execute(
                f"SELECT id, practice_item_id, created_at, latency_seconds FROM practice_attempts "
                f"WHERE practice_item_id IN ({marks}) AND created_at >= ? ORDER BY created_at, id",
                (*ids, earliest),
            ).fetchall()
        attempts: dict[str, list[Any]] = {}
        for row in rows:
            attempts.setdefault(str(row["practice_item_id"]), []).append(row)
        vault = env.vault
        for item in open_items:
            attempt = next(
                (row for row in attempts.get(item.practice_item_id, []) if str(row["created_at"]) >= item.planned_at),
                None,
            )
            if attempt is not None:
                done_at = str(attempt["created_at"])
                wall_ms = None
                served = parse_utc(item.served_at) if item.served_at else None
                done = parse_utc(done_at)
                if served is not None and done is not None and done >= served:
                    wall_ms = int((done - served).total_seconds() * 1000)
                elif attempt["latency_seconds"] is not None:
                    wall_ms = int(attempt["latency_seconds"]) * 1000
                writes.append(
                    (
                        item.block_id,
                        "item_done",
                        {
                            "practice_item_id": item.practice_item_id,
                            "attempt_id": str(attempt["id"]),
                            "done_at": done_at,
                            "wall_ms": wall_ms,
                            "est_minutes": round(item.est_minutes, 4),
                            "serving_origin": "learner_pick" if item.origin == ORIGIN_LEARNER_PICK else "daily_plan",
                        },
                    )
                )
                item.done_at = done_at
                continue
            practice_item = vault.practice_items.get(item.practice_item_id)
            servable = (
                practice_item is not None
                and practice_item.status == "active"
                and practice_item_servable(vault, practice_item)
                and unservable_reason(practice_item) is None
            )
            if not servable:
                writes.append(
                    (item.block_id, "item_displaced", {"practice_item_id": item.practice_item_id, "reason": "no_longer_servable"})
                )
                item.displaced_at = now
    for block in record.blocks:
        if block.ended_at is None and not block.is_reading and block.items and all(item.resolved for item in block.items):
            writes.append((block.id, "block_ended", {"outcome": "completed", "minutes_counted": round(block.est_minutes(), 4)}))
            block.ended_at = now
    if writes:
        with env.repository.atomic(), env.repository.connection() as connection:
            for block_id, kind, detail in writes:
                _event(connection, block_id, kind, detail, now)
        return _reload(env, record.id)
    return record


def _displaceable(record: PlanRecord, keep: Iterable[str] = ()) -> list[PlannedItem]:
    """The plan's tail, latest first: unserved, unresolved planned items.

    Served, answered, skipped items, learner picks and the ones in ``keep`` are
    never displaced.
    """

    kept = set(keep)
    return [
        item
        for block in sorted(record.blocks, key=lambda b: b.ordinal, reverse=True)
        if not block.finished
        for item in sorted(block.items, key=lambda i: i.position, reverse=True)
        if not item.resolved and item.served_at is None and item.practice_item_id not in kept
        and item.origin != ORIGIN_LEARNER_PICK
    ]


def _displacement_plan(
    record: PlanRecord, *, need_minutes: float, need_items: int, keep: Iterable[str] = ()
) -> list[PlannedItem] | None:
    """The fewest tail items whose displacement frees ``need_minutes`` and
    ``need_items`` item slots, or None when the tail cannot free both."""

    victims: list[PlannedItem] = []
    freed = 0.0
    for item in _displaceable(record, keep):
        if freed >= need_minutes - _EPS and len(victims) >= need_items:
            break
        victims.append(item)
        freed += item.est_minutes
    if freed >= need_minutes - _EPS and len(victims) >= need_items:
        return victims
    return None


def _followup_release(
    lefts: Mapping[str, float],
    minutes_left: float,
    est: float,
    *,
    lane: str,
    lanes_allowed: Sequence[str],
) -> dict[str, Any] | None:
    """What a follow-up's lane needs from the others to pay for it (review F4).

    The follow-up is charged to its lane. When that lane has fewer minutes left
    than the follow-up's estimate, the other lanes release the shortfall from
    their remaining minutes in a learner pick's order (push, new, maintain),
    then from the plan's minutes no lane holds. None when the lane can pay.
    """

    short = est - float(lefts.get(lane, 0.0))
    if short <= _EPS:
        return None
    released: list[dict[str, Any]] = []
    for other in PICK_DEDUCTION_ORDER:
        if other == lane or other not in lanes_allowed or short <= _EPS:
            continue
        take = min(max(float(lefts.get(other, 0.0)), 0.0), short)
        if take > _EPS:
            released.append({"from": other, "minutes": round(take, 6)})
            short -= take
    unallotted = 0.0
    if short > _EPS:
        slack = max(minutes_left - sum(max(float(value), 0.0) for value in lefts.values()), 0.0)
        unallotted = min(slack, short)
        short -= unallotted
    given = sum(entry["minutes"] for entry in released) + unallotted
    return {
        "to": lane,
        "released": released,
        "unallotted": round(unallotted, 6),
        "given": round(given, 6),
        "uncovered": round(max(short, 0.0), 6),
    }


def _displace_tail(
    env: PlanEnv,
    connection: Any,
    record: PlanRecord,
    need: float,
    *,
    by: str,
    keep: set[str] = frozenset(),  # type: ignore[assignment]
) -> tuple[float, list[str]]:
    """Free ``need`` minutes by displacing the latest unserved planned items.

    Displaced items go back to the pool; they are not debt (§6.1). Served,
    answered, skipped items and the ones in ``keep`` are never displaced.
    """

    displaced: list[str] = []
    now = env.now_iso()
    candidates = _displaceable(record, keep)
    for item in candidates:
        if need <= _EPS:
            break
        _event(connection, item.block_id, "item_displaced", {"practice_item_id": item.practice_item_id, "reason": "displaced", "by": by}, now)
        item.displaced_at = now
        need -= item.est_minutes
        displaced.append(item.practice_item_id)
    return need, displaced


# -- follow-ups ---------------------------------------------------------------------


def _pending_followups(record: PlanRecord, built: _Pool) -> list[PoolItem]:
    """Follow-ups produced by this session's answers: not in the plan's universe
    at build as follow-ups, and not planned yet (§6.1)."""

    at_build = set(record.split.get("followups_at_build") or [])
    taken = {item.practice_item_id for item in record.items()}
    return [
        item
        for item in built.pool
        if item.followup and item.practice_item_id not in at_build and item.practice_item_id not in taken
    ]


def _insert_followups(env: PlanEnv, record: PlanRecord, built: _Pool) -> tuple[PlanRecord, list[PoolItem]]:
    """Plan mid-plan follow-ups next in the current block, displacing the tail.

    A follow-up joins only when the plan still holds it: within the plan's
    minutes and a re-entry plan's item cap (G2, G10), displacing unserved tail
    items to make room. Earlier follow-ups are never displaced by later ones.
    A follow-up that cannot fit is declined and waits in the pool (not debt).
    Each is charged to its lane, with a recorded release from the other lanes
    when its lane has too few minutes left (review F4).

    Returns the follow-ups to force into the next block when none is current.
    """

    followups = _pending_followups(record, built)
    if not followups or not record.is_open:
        return record, []
    cap = record.split.get("items_cap")
    current = record.current_block()
    if current is None or current.is_reading:
        fitted: list[PoolItem] = []
        free = record.minutes_left()
        slots = None if cap is None else max(int(cap) - record.item_count(), 0)
        for item in followups:
            if slots is not None and len(fitted) >= slots:
                break
            if item.est_minutes <= free + _EPS:
                fitted.append(item)
                free -= item.est_minutes
        return record, fitted
    now = env.now_iso()
    protected = {item.practice_item_id for item in record.items() if item.origin == ORIGIN_FOLLOWUP}
    with env.repository.atomic(), env.repository.connection() as connection:
        position = max((item.position for item in current.items), default=0)
        for item in followups:
            need_items = 0 if cap is None else max(record.item_count() + 1 - int(cap), 0)
            victims = _displacement_plan(
                record,
                need_minutes=item.est_minutes - record.minutes_left(),
                need_items=need_items,
                keep=protected,
            )
            if victims is None:
                continue
            for victim in victims:
                _event(
                    connection,
                    victim.block_id,
                    "item_displaced",
                    {"practice_item_id": victim.practice_item_id, "reason": "displaced", "by": item.practice_item_id},
                    now,
                )
                victim.displaced_at = now
            lane = item.lane or "repair"
            release = _followup_release(
                record.lane_left(), record.minutes_left(), item.est_minutes, lane=lane, lanes_allowed=record.lanes_allowed
            )
            position += 1
            _event(
                connection,
                current.id,
                "item_planned",
                {
                    "practice_item_id": item.practice_item_id,
                    "learning_object_id": item.learning_object_id,
                    "lane": lane,
                    "est_minutes": round(item.est_minutes, 4),
                    "origin": ORIGIN_FOLLOWUP,
                    "position": position,
                    "new_admitted": False,
                    "check_kind": None,
                    "serving_origin": "daily_plan",
                    **({"lane_release": release} if release is not None else {}),
                },
                now,
            )
            current.items.append(
                PlannedItem(
                    block_id=current.id, position=position, practice_item_id=item.practice_item_id,
                    learning_object_id=item.learning_object_id, lane=lane, est_minutes=item.est_minutes,
                    origin=ORIGIN_FOLLOWUP, planned_at=now, lane_release=release,
                )
            )
            protected.add(item.practice_item_id)
    return _reload(env, record.id), []


# -- the next step -------------------------------------------------------------------


def _item_step(env: PlanEnv, record: PlanRecord, block: PlannedBlock, item: PlannedItem, *, boundary: bool, candidate_id: str | None) -> dict[str, Any]:
    practice_item = env.vault.practice_items.get(item.practice_item_id)
    learning_object = env.vault.learning_objects.get(item.learning_object_id)
    return {
        "kind": "item",
        "plan_id": record.id,
        "block_id": block.id,
        "block_ordinal": block.ordinal,
        "practice_item_id": item.practice_item_id,
        "learning_object_id": item.learning_object_id,
        "learning_object_title": learning_object.title if learning_object is not None else item.learning_object_id,
        "practice_mode": getattr(practice_item, "practice_mode", None),
        "est_minutes": round(item.est_minutes, 4),
        "origin": item.origin,
        "scheduler_candidate_id": candidate_id,
        "boundary": boundary,
    }


def _reading_step(env: PlanEnv, record: PlanRecord, block: PlannedBlock, *, boundary: bool) -> dict[str, Any]:
    reading = dict(block.reading or {})
    return {
        "kind": "reading",
        "plan_id": record.id,
        "block_id": block.id,
        "block_ordinal": block.ordinal,
        "reading": {
            "source_id": reading.get("source_id"),
            "extraction_id": reading.get("extraction_id"),
            "section_id": reading.get("section_id"),
            "section_title": reading.get("section_title"),
            "words_left": reading.get("words_left"),
            "partial": bool(reading.get("partial")),
            "start_span_id": reading.get("start_span_id"),
            "full_minutes": reading.get("full_minutes"),
        },
        "est_minutes": round(block.est_minutes(), 4),
        "boundary": boundary,
    }


def _done_step(record: PlanRecord) -> dict[str, Any]:
    return {"kind": "done", "plan_id": record.id, "status": record.status, "stop_reason": record.row.get("stop_reason")}


def advance(env: PlanEnv, *, serve: bool, skip_practice_item_id: str | None = None) -> tuple[PlanRecord, dict[str, Any]]:
    """Reconcile, insert follow-ups, cross a boundary if needed, and name the next step.

    ``serve`` records the step as served (``item_served`` / ``block_started``);
    without it this is the prefetch the client makes while feedback shows (the
    boundary decision itself is made then, §6.8 rule 5).
    """

    record, step, _context = advance_with_context(env, serve=serve, skip_practice_item_id=skip_practice_item_id)
    return record, step


def advance_with_context(
    env: PlanEnv, *, serve: bool, skip_practice_item_id: str | None = None
) -> tuple[PlanRecord, dict[str, Any], PoolContext | None]:
    record = get_or_create_today(env)
    assert record is not None
    record = reconcile(env, record)
    if skip_practice_item_id:
        record = _skip(env, record, skip_practice_item_id)
    if not record.is_open:
        return record, _done_step(record), None
    # One scheduler build per call: follow-up detection, the boundary decision
    # and the served item's candidate id all read the same ranked list.
    built = _classified_pool(
        env,
        minutes=record.budget,
        lanes_allowed=record.lanes_allowed,
        day=day_records(env),
        reentry=record.kind == "reentry",
    )
    record, forced = _insert_followups(env, record, built)
    context = _context(env, record, built, day=())
    block = record.current_block()
    if block is None:
        forced_origin = ORIGIN_FOLLOWUP
        if not record.blocks and not record.receipts and record.split.get("requested"):
            # The plan row was written but its first block was not (a crash
            # between the two writes): place its requests first now, as the
            # build would have (L3; review F10). Follow-ups wait one step.
            by_id = {item.practice_item_id: item for item in context.pool}
            forced = [
                by_id[row["practice_item_id"]]
                for row in record.split.get("requested") or []
                if row.get("practice_item_id") in by_id
            ]
            forced_origin = ORIGIN_REQUESTED
        block_id = _boundary(env, record, context, forced=forced, forced_origin=forced_origin)
        record = _reload(env, record.id)
        context = _context(env, record, built, day=())
        if block_id is None:
            return record, _done_step(record), context
        block = next(b for b in record.blocks if b.id == block_id)
    boundary = block.started_at is None
    if block.is_reading:
        step = _reading_step(env, record, block, boundary=boundary)
        if serve:
            with env.repository.atomic(), env.repository.connection() as connection:
                if block.started_at is None:
                    _event(connection, block.id, "block_started", {"session_id": env.session_id}, env.now_iso())
            record = _reload(env, record.id)
        return record, step, context
    item = block.next_item()
    if item is None:  # pragma: no cover - an unfinished item block has an open item
        return record, _done_step(record), context
    candidate_id = context.candidate_ids.get(item.practice_item_id)
    step = _item_step(env, record, block, item, boundary=boundary, candidate_id=candidate_id)
    if serve:
        _serve(env, block, item, candidate_id=candidate_id)
        record = _reload(env, record.id)
    return record, step, context


def _serve(env: PlanEnv, block: PlannedBlock, item: PlannedItem, *, candidate_id: str | None) -> None:
    now = env.now_iso()
    with env.repository.atomic(), env.repository.connection() as connection:
        if block.started_at is None:
            _event(connection, block.id, "block_started", {"session_id": env.session_id}, now)
        if item.served_at is None:
            _event(
                connection,
                block.id,
                "item_served",
                {
                    "practice_item_id": item.practice_item_id,
                    "scheduler_candidate_id": candidate_id,
                    "session_id": env.session_id,
                    "est_minutes": round(item.est_minutes, 4),
                    "serving_origin": "learner_pick" if item.origin == ORIGIN_LEARNER_PICK else "daily_plan",
                },
                now,
            )


def _skip(env: PlanEnv, record: PlanRecord, practice_item_id: str) -> PlanRecord:
    target = next(
        (item for item in record.items() if item.practice_item_id == practice_item_id and not item.resolved),
        None,
    )
    if target is None:
        return record
    with env.repository.atomic(), env.repository.connection() as connection:
        _event(connection, target.block_id, "item_skipped", {"practice_item_id": practice_item_id, "est_minutes": round(target.est_minutes, 4)}, env.now_iso())
    return reconcile(env, _reload(env, record.id))


# -- learner picks -----------------------------------------------------------------


def _offered_candidate(env: PlanEnv, candidate_id: str | None, practice_item_id: str) -> str | None:
    """The full list's offer for this item, when ``candidate_id`` is one (F5).

    A pick from the full list is served with the offer the learner picked it
    from (``get_today_queue`` published that list as shown), not with the plan
    build's unpublished slate. Anything else falls back to the plan's own.
    """

    if not candidate_id:
        return None
    with env.repository.connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM scheduler_slate_candidates c JOIN scheduler_slates s ON s.id = c.slate_id "
            "WHERE c.id = ? AND c.practice_item_id = ? AND c.was_returned = 1 "
            "AND (s.session_id IS ? OR ? IS NULL)",
            (candidate_id, practice_item_id, env.session_id, env.session_id),
        ).fetchone()
    return candidate_id if row is not None else None


def learner_pick(
    env: PlanEnv, practice_item_id: str, *, offer_candidate_id: str | None = None
) -> tuple[PlanRecord | None, dict[str, Any]]:
    """§6.1, L3, G12: opening an item from the full list is a one-item block.

    Its estimate comes out of the minutes left and the lanes (push, new,
    repair, maintain); planned items that no longer fit are displaced. A
    planned item opened from the list is simply served. A plan that is no
    longer open does not grow: the item is served as an open-list pick.
    ``offer_candidate_id`` is the full list's offer it was picked from.
    """

    vault = env.vault
    if practice_item_id not in vault.practice_items:
        raise KeyError(practice_item_id)
    record = get_or_create_today(env)
    assert record is not None
    record = reconcile(env, record)
    planned = next(
        (item for item in record.items() if item.practice_item_id == practice_item_id and not item.resolved),
        None,
    )
    context, built = _live_context(env, record)
    candidate_id = _offered_candidate(env, offer_candidate_id, practice_item_id) or context.candidate_ids.get(
        practice_item_id
    )
    if planned is not None:
        block = next(b for b in record.blocks if b.id == planned.block_id)
        _serve(env, block, planned, candidate_id=candidate_id)
        record = _reload(env, record.id)
        block = next(b for b in record.blocks if b.id == planned.block_id)
        return record, _item_step(env, record, block, planned, boundary=False, candidate_id=candidate_id)
    if not record.is_open:
        # The plan does not grow ("keep going" is the only extension), but the
        # pick is still the learner's choice: an open-list pick receipt keeps
        # its learner_pick / serving_origin record (review F10).
        practice_item = vault.practice_items[practice_item_id]
        est = built.estimator.item_minutes(vault, practice_item_id)
        with env.repository.atomic(), env.repository.connection() as connection:
            receipt_id = _persist_receipt(
                env,
                connection,
                record,
                action=RECEIPT_OPEN_LIST_PICK,
                chosen_by="learner_pick",
                est_minutes=est,
                learning_object_ids=[practice_item.learning_object_id],
                detail={
                    "source": "learner",
                    "chooser": "learner",
                    "chosen_by": "learner_pick",
                    "candidate_id": f"pick:{practice_item_id}",
                    "practice_item_id": practice_item_id,
                    "propensity": None,
                    "why": "you picked this from the full list after today's plan closed",
                    "why_kind": "computed",
                    "fallback": False,
                    "plan_status": record.status,
                    "candidate_set": [],
                },
            )
            _event(
                connection,
                receipt_id,
                "item_served",
                {
                    "practice_item_id": practice_item_id,
                    "learning_object_id": practice_item.learning_object_id,
                    "scheduler_candidate_id": candidate_id,
                    "session_id": env.session_id,
                    "est_minutes": round(est, 4),
                    "serving_origin": "learner_pick",
                },
                env.now_iso(),
            )
        return _reload(env, record.id), {
            "kind": "item",
            "plan_id": None,
            "block_id": None,
            "practice_item_id": practice_item_id,
            "learning_object_id": practice_item.learning_object_id,
            "scheduler_candidate_id": candidate_id,
            "origin": "open_list",
            "boundary": False,
        }
    pool_item = next((item for item in built.pool if item.practice_item_id == practice_item_id), None)
    est = pool_item.est_minutes if pool_item is not None else built.estimator.item_minutes(vault, practice_item_id)
    practice_item = vault.practice_items[practice_item_id]
    learning_object = vault.learning_object_for_item(practice_item)
    lo_id = learning_object.id if learning_object is not None else practice_item.learning_object_id
    lane = pool_item.lane if pool_item is not None else None
    lefts = record.lane_left()
    deductions: dict[str, float] = {}
    remaining = est
    for name in PICK_DEDUCTION_ORDER:
        if name not in record.lanes_allowed or remaining <= _EPS:
            continue
        take = min(lefts.get(name, 0.0), remaining)
        if take > _EPS:
            deductions[name] = round(take, 6)
            remaining -= take
    item = pool_item or PoolItem(
        practice_item_id=practice_item_id,
        learning_object_id=lo_id,
        rank=-1,
        priority=0.0,
        lane=None,
        reason="your pick",
        est_minutes=est,
        never_attempted=False,
    )
    with env.repository.atomic(), env.repository.connection() as connection:
        need = record.minutes_planned() + est - record.budget
        overrun = 0.0
        displaced: list[str] = []
        if need > _EPS:
            overrun, displaced = _displace_tail(env, connection, record, need, by=practice_item_id)
        action, subtype = LANE_ACTIONS.get(lane or "maintain", ("maintain", None))
        block_id = _persist_block(
            env,
            connection,
            record,
            lane=lane,
            action=action,
            subtype=subtype,
            chosen_by="learner_pick",
            est_minutes=est,
            reading=None,
            reading_full=None,
            learning_object_ids=[lo_id],
            detail={
                "source": "learner",
                "chooser": "learner",
                "chosen_by": "learner_pick",
                "candidate_id": f"pick:{practice_item_id}",
                "propensity": None,
                "why": "you picked this from the full list",
                "why_kind": "computed",
                "fallback": False,
                "deductions": deductions,
                "displaced": displaced,
                # L3 wins: a pick larger than everything still displaceable is
                # served anyway; this is how far it runs past the budget.
                "overrun_minutes": round(max(overrun, 0.0), 4),
                "candidate_set": [],
                "state": {"minutes_left": round(record.minutes_left(), 4), "lane_minutes_left": {k: round(v, 4) for k, v in lefts.items()}},
            },
            items=[(item, ORIGIN_LEARNER_PICK)],
        )
    record = _reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block_id)
    planned_item = block.items[0]
    _serve(env, block, planned_item, candidate_id=candidate_id)
    record = _reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block_id)
    return record, _item_step(env, record, block, block.items[0], boundary=False, candidate_id=candidate_id)


# -- minutes, keep going, more new, reading ----------------------------------------


def set_minutes(env: PlanEnv, minutes: int) -> PlanRecord:
    """A chip tap (§6.6): sets the remembered budget and re-plans the rest.

    On a re-entry plan the tap still sets the remembered value, but the plan
    keeps its cap; a "keep going" extension keeps its generated size.
    """

    if minutes <= 0:
        raise ValueError("minutes must be positive")
    record = get_or_create_today(env, create=False)
    if record is None:
        gap = env.gap()
        if gap.due:
            return build_plan(env, kind="reentry", budget=float(min(minutes, int(env.plan_config.reentry_minutes))), remembered=minutes, minutes_source="chip")
        return build_plan(env, kind="normal", budget=float(minutes), remembered=minutes, minutes_source="chip")
    record = reconcile(env, record)
    if record.kind == "reentry":
        budget = float(min(minutes, int(env.plan_config.reentry_minutes)))
    elif record.kind == "keep_going":
        budget = record.budget
    else:
        budget = float(minutes)
    now = env.now_iso()
    split = record.split
    if abs(budget - record.budget) > _EPS and record.status in ("open", "complete"):
        context, built = _live_context(env, record)
        allotment, spent = record.ledger()
        pool_loads = {lane: 0.0 for lane in LANES}
        for item in context.pool:
            if item.lane in pool_loads and item.lane != "new":
                pool_loads[item.lane] += item.est_minutes
        loads = {lane: spent[lane] + pool_loads[lane] for lane in LANES}
        admitted_new = float(split.get("admitted_new_minutes") or 0.0)
        loads["new"] = admitted_new
        requested_minutes = sum(float(row.get("est_minutes") or 0.0) for row in split.get("requested") or [])
        new_split = split_v1(
            budget=budget,
            requested_minutes=requested_minutes,
            loads=loads,
            admitted_new_minutes=admitted_new,
            push_candidates=any(item.lane == "push" for item in context.pool),
            repair_max_share=float(env.plan_config.repair_max_share),
            maintain_max_share=float(env.plan_config.maintain_max_share),
            lanes_allowed=record.lanes_allowed,
        )
        replans = list(split.get("replans") or [])
        replans.append({"at": now, "from_budget": record.budget, "to_budget": budget, "previous_lanes": split.get("lanes"), "epoch_ordinal": record.next_ordinal()})
        updated = {
            **split,
            **new_split.as_dict(),
            "epoch_ordinal": record.next_ordinal(),
            "epoch_at": now,
            "replans": replans,
        }
        with env.repository.atomic(), env.repository.connection() as connection:
            status = record.status
            if budget < record.minutes_planned() - _EPS:
                record.row["minutes_budget"] = budget
                _displace_tail(env, connection, record, record.minutes_planned() - budget, by="minutes_change")
            if status == "complete" and budget > record.budget + _EPS and record.row.get("stop_reason") != "learner_stopped":
                status = "open"
            store.update_plan(
                connection,
                record.id,
                minutes_budget=budget,
                remembered_minutes=int(minutes),
                minutes_source="chip",
                split_json=updated,
                status=status,
                completed_at=None if status == "open" else record.row.get("completed_at"),
                stop_reason=None if status == "open" else record.row.get("stop_reason"),
                updated_at=now,
            )
    else:
        with env.repository.atomic(), env.repository.connection() as connection:
            store.update_plan(connection, record.id, remembered_minutes=int(minutes), minutes_source="chip", updated_at=now)
    return _reload(env, record.id)


def keep_going(env: PlanEnv) -> PlanRecord:
    """§6.5: one extension. After re-entry, a normal plan for the day's remaining minutes."""

    record = get_or_create_today(env)
    assert record is not None
    record = reconcile(env, record)
    if record.is_open:
        return record
    remembered = int(record.row["remembered_minutes"])
    if record.kind == "reentry":
        remaining = remembered - record.minutes_planned()
        if remaining >= 1.0:
            return build_plan(env, kind="normal", budget=float(round(remaining, 2)), remembered=remembered, minutes_source="generated", parent_plan_id=record.id)
    return build_plan(env, kind="keep_going", budget=float(env.plan_config.keep_going_minutes), remembered=remembered, minutes_source="generated", parent_plan_id=record.id)


class PlanStillOpenError(RuntimeError):
    """"More new material" is offered on the done screen: today's plan is still open."""


def more_new(env: PlanEnv, *, confirm: bool) -> tuple[PlanRecord | None, dict[str, Any]]:
    """§6.3: "more new material" bypasses the ceiling and the cap once.

    Without ``confirm`` it only shows the trade-off; with it, it builds a
    labelled "keep going" extension that admits new material first. The
    preview is the extension itself, dry-run: the new items its blocks would
    plan (the deterministic pair, as the view projects), so "N new items,
    adds about M min/day" is what confirming serves (review F9). Confirming
    while today's plan is still open is refused: it would drop the plan's
    remaining items (review F10).
    """

    config = env.plan_config
    record = get_or_create_today(env)
    assert record is not None
    record = reconcile(env, record)
    budget = float(config.keep_going_minutes)
    prepared = _prepare_plan(
        env,
        kind="keep_going",
        budget=budget,
        remembered=int(record.row["remembered_minutes"]),
        minutes_source="generated",
        parent_plan_id=record.id,
        override="more_new",
    )
    draft = prepared.record()
    context = _context(env, draft, prepared.built, day=prepared.day)
    simulated = simulate_blocks(draft, context, env.policy, forced=prepared.requests)
    new_items = [item for _decision, block in simulated for item in block.items if item.new_admitted]
    chosen = [NewCandidate(item.practice_item_id, item.est_minutes) for item in new_items]
    preview = {
        "items": len(chosen),
        "est_minutes": round(sum(item.est_minutes for item in chosen), 4),
        "adds_minutes_per_day": round(
            more_new_tradeoff(chosen, reviews_per_new_item=int(config.new_item_reviews_14d), horizon_days=int(config.load_horizon_days)),
            4,
        ),
        "horizon_days": int(config.load_horizon_days),
        "available": bool(chosen),
        "practice_item_ids": [item.practice_item_id for item in new_items],
    }
    if not confirm or not chosen:
        return record, preview
    if record.is_open:
        raise PlanStillOpenError("today's plan is still open; more new material is offered when it is done")
    plan = build_plan(
        env,
        kind="keep_going",
        budget=budget,
        remembered=int(record.row["remembered_minutes"]),
        minutes_source="generated",
        parent_plan_id=record.id,
        override="more_new",
    )
    return plan, preview


READING_OUTCOMES = ("section_completed", "left_reader", "skipped")


def reading_ended(env: PlanEnv, outcome: str) -> PlanRecord:
    """§6.10: end the current reading block; its estimate counts as used."""

    if outcome not in READING_OUTCOMES:
        raise ValueError(f"unknown reading outcome {outcome!r}")
    record = get_or_create_today(env)
    assert record is not None
    block = record.current_block()
    if block is None or not block.is_reading:
        return record
    with env.repository.atomic(), env.repository.connection() as connection:
        _event(connection, block.id, "block_ended", {"outcome": outcome, "minutes_counted": round(block.est_minutes(), 4)}, env.now_iso())
    return _reload(env, record.id)


def note_reading_progress(
    env: PlanEnv,
    *,
    extraction_id: str,
    section_id: str,
    spans_seen: int | None,
    span_count: int | None,
    completed: bool,
) -> bool:
    """``reader.mark_section_progress`` while a reading block is current (§6.10).

    Appends a ``reading_progress`` event; a completion ends the block with
    ``section_completed``. Returns whether a plan block took the progress.
    """

    if not plan_active(env.vault):
        return False
    record = latest_today(env)
    if record is None or not record.is_open:
        return False
    block = record.current_block()
    if block is None or not block.is_reading:
        return False
    reading = block.reading or {}
    if reading.get("extraction_id") != extraction_id or reading.get("section_id") != section_id:
        return False
    now = env.now_iso()
    with env.repository.atomic(), env.repository.connection() as connection:
        _event(
            connection,
            block.id,
            "reading_progress",
            {"spans_seen": int(spans_seen or 0), "span_count": int(span_count or 0), "completed": bool(completed)},
            now,
        )
        if completed:
            _event(connection, block.id, "block_ended", {"outcome": "section_completed", "minutes_counted": round(block.est_minutes(), 4)}, now)
    return True


def stop_today(env: PlanEnv) -> PlanRecord | None:
    """The learner stops for today ("Done" mid-plan)."""

    record = latest_today(env)
    if record is None:
        return None
    if record.is_open:
        _close(env, record, status="stopped", reason="learner_stopped")
    return _reload(env, record.id)


__all__ = [
    "DEFAULT_POLICY",
    "Decision",
    "ENGINE_VERSION",
    "EligibleBuilder",
    "PlanEnv",
    "PlanInactiveError",
    "PlanPolicy",
    "PlanStillOpenError",
    "PoolContext",
    "READING_OUTCOMES",
    "advance",
    "advance_with_context",
    "build_plan",
    "day_records",
    "decide",
    "get_or_create_today",
    "keep_going",
    "latest_today",
    "learner_pick",
    "legacy_source",
    "load_records",
    "load_records_from_connection",
    "local_date",
    "more_new",
    "note_reading_progress",
    "plan_active",
    "reading_ended",
    "reconcile",
    "remembered_minutes",
    "set_minutes",
    "simulate_blocks",
    "stop_today",
]
