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
from typing import TYPE_CHECKING, Any

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
    REPAIR_RULE_DIAGNOSIS,
    REPAIR_RULE_RECENT_ERROR,
    LegacyLanesSource,
    PoolItem,
    SOURCE_NAME,
    classify_pool,
    reentry_order,
    scheduled_checks,
)
from learnloop.daily_plan.reading import next_reading_target, section_start_span
from learnloop.daily_plan.records import (
    AD_INELIGIBLE,
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
    AFTER_REENTRY_LANE_PRIORITY,
    BLOCK_MAX_MINUTES,
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
    DecisionPending,
    IntentView,
    PlanState,
    ReadingTarget,
)
from learnloop.db.stores import daily_plans as store
from learnloop.ids import new_ulid
from learnloop.router.plan_log import log_plan_block_decision

if TYPE_CHECKING:
    from learnloop.scheduling.scheduler import SchedulerSession

_EPS = 1e-6
ENGINE_VERSION = "daily_plan_v1"


class PlanInactiveError(RuntimeError):
    """The plan is off: a pre-mvp-0.14 vault or ``plan.enabled = false``."""


class PlanWaiting(Exception):
    """The boundary found nothing to do now, but a routine-display hold on a
    planned cold check lifts later today (UX Phase 4 round 7). The plan is not
    finished: it stays open without a block, and the step says what it waits
    for and until when. Nothing is written; the next call decides again."""

    def __init__(self, step: dict[str, Any]) -> None:
        super().__init__(step.get("until"))
        self.step = step


def plan_active(vault: Any) -> bool:
    """The plan serves only at a daily-plan version with the kill switch on."""

    return (
        vault.config.algorithms.algorithm_version in DAILY_PLAN_VERSIONS
        and bool(vault.config.plan.enabled)
    )


def reading_from_furthest_active(vault: Any) -> bool:
    """The reading block continues from the furthest section read (UX Phase 1,
    U4) wherever the plan acts, with its kill switch
    ``plan.reading_from_furthest`` on; off, it is DL1's order, the first
    unfinished section in book order. Either way the one exam predicate keeps
    exam and held-out material off the step (the setting orders it only;
    exam protection by extraction identity, final verify F15); in DL1's order
    that is behind the serving rules' kill switch (:func:`reading_step_rule`).

    A live change behind a kill switch, not a successor tag (owner ruling at
    the UX Phase 1 merge, docs/reviews/ux-phase1.md "Landing onto main"): the
    selection is a serving choice that replay never reads. A plan block
    records the section it chose as workflow state (``attention_blocks``), and
    no replayer or projection reads it back."""

    return plan_active(vault) and bool(vault.config.plan.reading_from_furthest)


#: The rule that chose a plan's reading step (``split_json["reading_rule"]``).
#: U4's order (``plan.reading_from_furthest``), exam material never the step.
READING_RULE_FURTHEST = "furthest"
#: DL1's order, exam material never the step (exam protection by extraction identity, F15).
READING_RULE_BOOK_ORDER = "book_order"
#: DL1's selection exactly: ``plan.reading_from_furthest`` and the serving
#: rules' kill switch ``goals.held_out_selection`` both off (identity review F6).
READING_RULE_DL1 = "dl1"


def reading_step_rule(vault: Any) -> str:
    """Which rule chooses the plan's reading step. Exam protection in DL1's
    order (``book_order``) is a live serving change behind the serving rules'
    kill switch, ``goals.held_out_selection`` (Codex review of exam
    protection by extraction identity, F6): off, with
    ``plan.reading_from_furthest`` off too, the step is DL1's selection
    exactly (``dl1``), as before the change. U4's order (``furthest``) kept
    its own exam filter from the start, behind ``plan.reading_from_furthest``.
    Not a successor tag: replay never reads the selection (the owner's ruling
    at the UX Phase 1 merge)."""

    from learnloop.content.sources.exam_material import held_out_selection_active

    if reading_from_furthest_active(vault):
        return READING_RULE_FURTHEST
    return READING_RULE_BOOK_ORDER if held_out_selection_active(vault) else READING_RULE_DL1


def _exam_material(vault: Any, repository: Any) -> Any:
    """The one exam predicate (``content.sources.exam_material``, through
    ``source_retrieval.corpus.exam_exclusions``) for the reading step (UX Phase
    1's selection never offers exam material, a ``held_out_evaluation`` unit
    included, as reading).
    None when it cannot be read: the plan then offers no reading step (fail
    closed) rather than one that might be exam material."""

    from learnloop.source_retrieval.corpus import exam_exclusions

    try:
        return exam_exclusions(vault, repository)
    except Exception:  # noqa: BLE001 - the plan never fails on the reading step's filter
        import logging

        logging.getLogger(__name__).warning("could not read exam material for the reading step", exc_info=True)
        return None


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
    #: UX Phase 4 round 7: pool items held back now by a routine-display hold
    #: on their cold check, with when the hold lifts. They stay in the plan's
    #: universe and return to the pool once it lifts.
    held_until: Mapping[str, str] = field(default_factory=dict)
    #: The pool with those items still in it, in pool order (round 8: what
    #: the boundary could choose from once a hold lifts).
    pool_with_held: tuple[PoolItem, ...] = ()
    #: Adaptive difficulty AD2+AD3: the day's active AD deferrals this view
    #: excluded (spec §6.1 step 0); the projection holds them fixed.
    ad_deferred: frozenset[str] = frozenset()


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
    #: Router R2c: the restraint gate on mid-block follow-ups (``plan_interrupt``;
    #: ``daily_plan.router_chooser.RestraintGate``). None: DL1's follow-up
    #: rules alone (a placeable follow-up always joins the current block).
    restraint: Any = None

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


def staged_plans_deterministic(vault: Any) -> bool:
    """A staged plan's pool is a fixed function of the vault state: the router
    composes Today (:func:`learnloop.daily_plan.policy.router_active`:
    ``mvp-0.23`` or later with ``router.enabled``) and the kill switch
    ``plan.deterministic_staged_plans`` is on.

    A live change behind its kill switch, not a successor tag (the owner's
    standing ruling: live changes behind kill switches, not successors, for
    serving changes replay never reads; plan-determinism Codex review F2).
    Replay never reads a plan (migration 180), and a logged plan keeps its
    blocks; off, the staged plan's pool is as ``mvp-0.23`` and ``mvp-0.24``
    landed. At ``mvp-0.24`` the same pool gives the model mixture its
    candidates (the staged pick and the support); the mixture keeps its own
    seeded draw, floor and logged propensities."""

    from learnloop.daily_plan.policy import router_active  # policy imports this module

    return router_active(vault) and bool(vault.config.plan.deterministic_staged_plans)


def plan_scheduler_session(vault: Any, session_id: str | None, minutes: float) -> SchedulerSession:
    """The scheduler session a plan's pool is built under (every plan build).

    The pool is the scheduler's ranked list, and its order is the plan's: the
    lanes group it, the blocks pack it, and ``planner_value`` (the chooser's
    tie-break) is its rank. Two session-seeded draws reorder that list:

    * the scheduler's seeded exploration (router R1's
      ``scheduler_seeded_exploration``, hashed from the session id and the UTC
      date) moves a near-tie to the front;
    * a contrast pair's member order (Meas §3.A4, hashed from the session id
      and the pair) swaps the two members' slots, so when both fit a block its
      order differs, and when only one fits the plan chooses a different one.

    Either would make a plan depend on which session asked for it while its
    ``plan_block`` decision logs a deterministic choice (propensity one).

    Owner rule (2026-10-13): staged plans are deterministic; the router's
    exploration comes only from the mixture's logged floor. So where
    :func:`staged_plans_deterministic` holds, the pool is the scheduler's
    greedy order (``seeded_exploration`` off) and a contrast pair's order is
    the pair's own draw (``contrast_order_seed = "pair"``: seeded on the pair
    alone, still drawn across pairs and recorded on its serving rows for A4's
    order-effect check), and the same vault state plans the same blocks
    whatever the session, or with none (Start builds the plan before a
    session opens: the pair's draw applies there too, unrecorded; Codex
    re-review F1). That order's tie-break is stable: selection reward,
    then priority (both descending), then the practice item id; then
    placement's new-material order and the build's composition. A4's
    per-session draw keeps its own path: every other queue build (Today's
    full list, the CLI and TUI queues, DL1's plan) is unchanged.

    DL1's own pair (below ``mvp-0.23``, or the router switched off), and the
    staged plan with ``plan.deterministic_staged_plans`` off, build under the
    predecessor's session exactly (``SchedulerSession(session_id,
    available_minutes)``; G8: the router off equals ``mvp-0.22``). Only future
    builds change: replay never reads a plan (migration 180), and a logged
    plan keeps its blocks.
    """

    from learnloop.scheduling.scheduler import SchedulerSession

    available = int(round(minutes))
    if not staged_plans_deterministic(vault):
        return SchedulerSession(session_id=session_id, available_minutes=available)
    return SchedulerSession(
        session_id=session_id,
        available_minutes=available,
        seeded_exploration=False,
        contrast_order_seed="pair",
    )


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
        from learnloop.scheduling.scheduler import build_due_queue

        return build_due_queue(
            self.vault,
            self.repository,
            clock=self.clock,
            session=plan_scheduler_session(self.vault, self.session_id, minutes),
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


# -- router R1's hook ----------------------------------------------------------------


@dataclass(frozen=True)
class PlanBlockDecision:
    """One block-boundary decision as router R1 logs it (owner decision 2026-10-12).

    R1 (merging after DL1) records every plan decision as a
    ``router_decisions`` row of kind ``plan_block``. ``detail`` is the
    ``block_chosen`` receipt the container writes: the candidate set, source,
    chooser, ``chosen_by``, propensity, why, fallback, the state the chooser
    saw, the redistribution and forced items. ``block_id`` is the block the
    decision made, or the stop receipt's id for a chooser's stop.

    Added when R1 merged (its logger reads them): ``chosen_by`` is the block
    row's own (``learner_pick`` for a block of requested items only, where the
    chooser's own choice was no block), ``items`` the block's planned
    ``(practice_item_id, learning_object_id)`` in serving order, ``decided_at``
    the plan clock's time of the decision and ``config`` the vault
    configuration it was made under (the router's kill switch and the
    algorithm version).
    """

    plan_id: str
    plan_kind: str
    local_date: str
    block_id: str
    session_id: str | None
    detail: Mapping[str, Any]
    stop: bool = False
    kind: str = "plan_block"
    chosen_by: str | None = None
    items: tuple[tuple[str, str], ...] = ()
    decided_at: str | None = None
    config: Any = field(default=None, repr=False, compare=False)
    #: Router R2a: the router chooser's record (``BlockChoice.router_record``),
    #: written by the logger with the row: the card into the payload table,
    #: its hash, mode and policy onto the decision. None from DL1's chooser.
    router_record: Mapping[str, Any] | None = field(default=None, repr=False, compare=False)


#: ``(connection, decision) -> router_decisions id or None``. The logger runs on
#: the block's own connection, inside its transaction, so R1's row commits or
#: rolls back with the block. The id becomes the block's ``decision_ref`` (on
#: its row and its ``block_chosen`` receipt) unless the chooser already set one
#: (R2's choosers log their own decisions).
PlanDecisionLogger = Callable[[Any, PlanBlockDecision], "str | None"]
_PLAN_DECISION_LOGGERS: list[PlanDecisionLogger] = []


def register_plan_decision_logger(logger: PlanDecisionLogger) -> None:
    """Router R1's hook: log each plan block decision (DL1 builds no router table)."""

    if logger not in _PLAN_DECISION_LOGGERS:
        _PLAN_DECISION_LOGGERS.append(logger)


def unregister_plan_decision_logger(logger: PlanDecisionLogger) -> None:
    if logger in _PLAN_DECISION_LOGGERS:
        _PLAN_DECISION_LOGGERS.remove(logger)


def _log_plan_decision(connection: Any, decision: PlanBlockDecision) -> str | None:
    """Hand one decision to the registered loggers; the first id written wins.

    Router R1 registers its ``plan_block`` logger below. With no logger
    registered this is a no-op. A logger that fails never blocks the plan: its
    decision goes unlogged and is reported.
    """

    ref: str | None = None
    for logger in list(_PLAN_DECISION_LOGGERS):
        try:
            written = logger(connection, decision)
        except Exception:  # noqa: BLE001 - logging never blocks the learner's plan
            import logging

            logging.getLogger(__name__).warning("plan decision logger failed", exc_info=True)
            continue
        if ref is None and written:
            ref = str(written)
    return ref


# Router R1 (merged after DL1; owner decision 2026-10-12): every block decision
# and chooser stop is a ``plan_block`` router decision, so plan decisions get
# router decision ids. Registered at import so every entry point that builds a
# plan (the sidecar, the CLI, the reader's plan hook) logs it; the logger
# honours ``router.log_decisions`` and leaves a chooser's own decision (R2) to
# that chooser.
register_plan_decision_logger(log_plan_block_decision)


#: The keys of a router chooser's record copied onto the ``block_chosen``
#: receipt (the card itself is stored beside the router decision).
ROUTER_SUMMARY_KEYS = (
    "mode", "policy", "card_version", "card_hash", "why_code", "controller_decision_id",
    # Router R2b: who drew and why the models did not answer (the "details" line).
    "decided_by", "drawn_component", "option_count", "fallback", "fallback_reasons", "rationale_hidden",
    "evidence_labels",
)


def router_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: record[key] for key in ROUTER_SUMMARY_KEYS if record.get(key) is not None}


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
    repair_rule: str = REPAIR_RULE_DIAGNOSIS
    #: A build's requests (L3), selected once before the due project probes
    #: are valued (Codex review of voi-v2, F14): requested probes and ordinary
    #: requests under one rule, in pool order. None: the split selects them
    #: from the classified pool (no probe valuation, as before).
    request_ids: tuple[str, ...] | None = None


def _open_problems(env: PlanEnv) -> tuple[frozenset[str] | None, str]:
    """The repair lane's LOs (owner decision 2026-10-12) and the rule used.

    With the diagnosis split on, repair means an open diagnosed problem (an
    unresolved hypothesis or an open unresolved-cause factor). While the split
    is off (a vault below mvp-0.10, or ``diagnosis.split_enabled = false``)
    there is no live diagnosis to read, and the lane falls back to DL1's
    recency rule (``lanes.REPAIR_MIN_RECENT_ERROR``).
    """

    from learnloop.attempts.blind_grading import split_grading_active

    if not split_grading_active(env.vault):
        return None, REPAIR_RULE_RECENT_ERROR
    with env.repository.connection() as connection:
        return store.open_diagnosed_problem_learning_object_ids(connection), REPAIR_RULE_DIAGNOSIS


def _select_requests(pool: Sequence[PoolItem], *, budget: float, per_session: int) -> tuple[list[PoolItem], float]:
    """Requests first (L3): up to ``per_session`` requested items with a lane,
    in pool order, while their estimates fit the budget; they go in the first
    block and their minutes come off the budget before the split."""

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
    return requests, requested_minutes


def _request_candidate(item: PoolItem, lanes_allowed: Sequence[str]) -> PoolItem:
    """A pool item as the request rule sees it before the probes are valued.

    A requested project probe is a learner request like any other (L3: the
    learner's explicit choice is honoured, and lane eligibility never blocks
    it): it is eligible in the maintain lane, its lane, whenever the plan
    allows maintain, whatever the probes' value or the former daily count
    (Codex review of voi-v2, F14). Every other item keeps its classification.
    """

    if item.requested and item.check_kind == "project_probe":
        return replace(item, lane="maintain" if "maintain" in set(lanes_allowed) else None)
    return item


def _plan_availability(record: PlanRecord, held: Iterable[str]) -> Callable[[str], str | None]:
    """Why a due project probe cannot join this plan on a refresh, or None
    (Codex review of voi-v2, F10).

    The refresh's admission values only probes the plan can still take, the
    same ones :func:`_context` leaves in the pool: in the plan's frozen
    universe, and neither skipped nor answered in it. ``held`` (planned, not
    yet answered, or a request a crash left unplaced) are conditioned on, not
    excluded. A skipped or answered probe, or one outside the universe, would
    otherwise be admitted, suppress an overlapping probe the plan can take,
    and then be dropped by the context, leaving neither."""

    universe = set(record.split.get("universe") or [])
    keep = set(held)
    skipped = {item.practice_item_id for item in record.items() if item.skipped}
    answered = {item.practice_item_id for item in record.items() if item.done and not item.displaced}

    def why(item_id: str) -> str | None:
        if item_id in keep:
            return None
        if item_id in skipped:
            return "skipped_in_this_plan"
        if item_id in answered:
            return "answered_in_this_plan"
        if item_id not in universe:
            return "outside_plan_universe"
        return None

    return why


def _usable_probe_minutes(*, minutes: float, reserved: float, lanes_allowed: Sequence[str]) -> float:
    """The minutes due project probes are admitted against (final verify F10):
    the plan's minutes (its budget on a build, its minutes left on a refresh)
    less what is reserved before the split (the requested items), and none
    when the plan's lanes exclude maintain, the probes' lane. The maintain
    lane's share is not a bound: idle lanes release their minutes to maintain
    first (``redistribute``), so a probe that fits these minutes can be
    planned."""

    if "maintain" not in set(lanes_allowed):
        return 0.0
    return max(float(minutes) - float(reserved), 0.0)


def _classified_pool(
    env: PlanEnv,
    *,
    minutes: float,
    lanes_allowed: Sequence[str],
    day: Sequence[PlanRecord],
    reentry: bool,
    record: PlanRecord | None = None,
    minutes_left: float | None = None,
) -> _Pool:
    """The scheduler's ranked list, classified into lanes (§6.1).

    ``record`` is the open plan on a refresh (None on a build). At mvp-0.21
    the due project probes are valued together against the minutes the plan
    can use (final verify F10): on a build, the budget less the requested
    items reserved before the split; on a refresh, the plan's minutes left
    (``minutes_left`` when a minutes change is re-planning the rest), with the
    probes it already holds (planned, not yet answered) conditioned on and not
    charged again.

    Codex review of voi-v2: on a build the requests are selected first, once,
    requested probes and ordinary requests under the one rule (F14,
    :func:`_request_candidate`); a requested probe chosen as a request is
    conditioned on, not valued or charged again, and the split uses exactly
    these requests (``_Pool.request_ids``). On a refresh only probes the plan
    can still take are valued (F10, :func:`_plan_availability`).
    """

    scheduled = env.build_eligible(minutes)
    # UX Phase 4 rounds 5 to 7: a cold check a routine display covers stays in
    # the pool (and the plan's universe); the boundary leaves it out while the
    # hold lasts (``_context``), and waits for it when it is all that is left
    # and the hold lifts today (``PlanWaiting``).
    estimator = _estimator(env)
    states = env.repository.practice_item_states()
    requested = env.repository.requested_practice_item_ids()
    ids = [item.practice_item_id for item in scheduled]
    checks = scheduled_checks(env.vault, env.repository, ids)
    probes_planned = sum(
        1 for record_ in day for item in record_.active_items() if item.check_kind == "project_probe"
    )
    deadlines = _deadlines(env.vault, env.repository)
    open_problems, repair_rule = _open_problems(env)

    def classify(admission: Any) -> list[PoolItem]:
        classified = classify_pool(
            scheduled,
            item_states=states,
            requested_ids=requested,
            now=env.now(),
            estimate=lambda item_id: estimator.item_minutes(env.vault, item_id),
            checks=checks,
            probe_cap_left=max(int(env.plan_config.project_probes_max_per_day) - probes_planned, 0),
            deadline_learning_object_ids=deadlines,
            open_problem_learning_object_ids=open_problems,
            project_probe_admission=admission,
        )
        if reentry:
            classified = reentry_order(classified)
        return [item if item.lane in lanes_allowed else replace(item, lane=None) for item in classified]

    admission = None
    request_ids: tuple[str, ...] | None = None
    from learnloop.diagnosis import voi_stopping as voi

    if voi.voi_stopping_active(env.vault.config, voi.SITE_PROJECT_PROBE):
        held: dict[str, str] = {}
        availability: Callable[[str], str | None] | None = None
        if record is None:
            # A build: requests first (L3), before the probes are valued, so
            # they do not depend on the probes' value. Requested probes and
            # ordinary requests share the rule, the order and the limit (F14);
            # each request is charged once, here.
            requests, reserved = _select_requests(
                [_request_candidate(item, lanes_allowed) for item in classify(None)],
                budget=float(minutes),
                per_session=int(env.vault.config.tutor_promotion.requested_items_per_session),
            )
            request_ids = tuple(item.practice_item_id for item in requests)
            usable = _usable_probe_minutes(minutes=minutes, reserved=reserved, lanes_allowed=lanes_allowed)
            held = {
                item.practice_item_id: voi.REASON_LEARNER_REQUEST
                for item in requests
                if item.check_kind == "project_probe"
            }
        else:
            # A refresh: the minutes left already exclude every planned block;
            # requests a crash left unplaced (the plan row without its first
            # block) are still to come off them, and a requested probe among
            # them is conditioned on as the build would have.
            pending = 0.0
            if not record.blocks and not record.receipts:
                for row in record.split.get("requested") or []:
                    pending += float(row.get("est_minutes") or 0.0)
                    held[str(row.get("practice_item_id"))] = voi.REASON_LEARNER_REQUEST
            usable = _usable_probe_minutes(
                minutes=record.minutes_left() if minutes_left is None else float(minutes_left),
                reserved=pending,
                lanes_allowed=lanes_allowed,
            )
            for item in record.items():
                if item.check_kind == "project_probe" and not item.resolved:
                    held.setdefault(item.practice_item_id, voi.REASON_ALREADY_PLANNED)
            availability = _plan_availability(record, held)
        admission = _project_probe_admission(
            env,
            probes_planned,
            minutes_budget=usable,
            preselected=held,
            availability=availability,
        )
    pool = classify(admission)
    return _Pool(
        scheduled=list(scheduled),
        pool=pool,
        estimator=estimator,
        deadlines=deadlines,
        repair_rule=repair_rule,
        request_ids=request_ids,
    )


def _project_probe_admission(
    env: PlanEnv,
    probes_planned: int,
    *,
    minutes_budget: float | None = None,
    preselected: Mapping[str, str] | Sequence[str] = (),
    availability: Callable[[str], str | None] | None = None,
) -> Callable[[Sequence[tuple[Any, float]]], list[tuple[str, Mapping[str, Any]]]] | None:
    """mvp-0.21 (``voi_stopping``, site ``project_probe``): value today's due
    project probes instead of counting them; ``None`` keeps the former daily
    cap.

    A project probe has no locked hypothesis set, so no next-action decision
    is at stake: its information is the scheduler's ``probe_eig_total`` for
    the item (LO-mastery and facet-recall entropy reduction, familiarity
    discounted), decomposed from the item's reward body so each probe is
    valued given the belief the probes admitted before it are expected to
    leave, converted to minutes and set against the plan's own estimate of its
    minutes. Probes are admitted greedily by robust value per minute while the
    best remaining one pays (``voi_stopping.greedy_information_admission``),
    the first included. The former cap's counterfactual counts the probes
    already planned today plus those admitted before each step.

    Feasibility is part of the selection (review F10): with the plan's
    ``minutes_budget``, a probe is admissible only while it fits the minutes
    the probes admitted before it leave, and only when it fits one block
    (``BLOCK_MAX_MINUTES``, never more than the budget), so a probe the plan
    could not hold neither takes a slot nor discounts the probes after it.
    ``minutes_budget`` is what the plan can use (final verify F10,
    :func:`_usable_probe_minutes`): after the requested items and on a
    refresh the minutes left, never the plan's whole budget; ``preselected``
    are the probes the plan already holds, conditioned on and not charged
    (a mapping names each one's reason: ``already_planned``, or
    ``learner_request`` for a requested probe chosen as a request, F14).
    ``availability`` (a refresh, F10) names why a probe cannot join the plan:
    such a probe is neither valued nor conditioned on, and its receipt says
    ``not_available_to_this_plan``. The lanes' shares are not a bound: the
    maintain lane can receive the plan's whole minutes when the other lanes
    are idle.
    """

    from learnloop.diagnosis import voi_stopping as voi

    if not voi.voi_stopping_active(env.vault.config, voi.SITE_PROJECT_PROBE):
        return None
    context = voi.VoiContext(env.vault, env.repository)
    cap = int(env.plan_config.project_probes_max_per_day)

    reasons = (
        {str(ref): str(reason) for ref, reason in preselected.items()}
        if isinstance(preselected, Mapping)
        else {str(ref): voi.REASON_ALREADY_PLANNED for ref in preselected}
    )

    def admit(probes: Sequence[tuple[Any, float]]) -> list[tuple[str, Mapping[str, Any]]]:
        entries = []
        unavailable: list[tuple[str, str]] = []
        for order, (scheduled, est_minutes) in enumerate(probes):
            why = availability(scheduled.practice_item_id) if availability is not None else None
            if why is not None:
                unavailable.append((scheduled.practice_item_id, why))
                continue
            components = getattr(scheduled, "components", {}) or {}
            eig = float(components.get("probe_eig_total", 0.0) or 0.0)
            entries.append(
                voi.InformationEntry(
                    ref=scheduled.practice_item_id,
                    learning_object_id=scheduled.learning_object_id,
                    eig_nats=eig,
                    minutes=voi.MinutesEstimate(float(est_minutes), "plan_estimate"),
                    predicted_correct=components.get("predicted_correctness"),
                    terms=voi.InformationTerms.from_reward_debug(
                        scheduled.learning_object_id,
                        getattr(scheduled, "reward_debug", None),
                        total_nats=eig,
                        hypothesis_channel=getattr(scheduled, "hypothesis_channel", None),
                    ),
                    detail={"former_order": order},
                )
            )
        # A requested probe chosen as a request is not planned yet; the former
        # cap's counterfactual counts it with the probes planned today.
        refs = {entry.ref for entry in entries}
        requested = sum(1 for ref, reason in reasons.items() if ref in refs and reason == voi.REASON_LEARNER_REQUEST)
        admission = voi.greedy_information_admission(
            context,
            voi.SITE_PROJECT_PROBE,
            entries,
            cap_value=cap,
            cap_count=int(probes_planned) + requested,
            context={"probes_planned_today": int(probes_planned)},
            minutes_budget=minutes_budget,
            max_item_minutes=(
                None if minutes_budget is None else min(float(BLOCK_MAX_MINUTES), float(minutes_budget))
            ),
            preselected=tuple(reasons),
            preselected_reasons=reasons,
        )
        first = list(admission.preselected) + list(admission.admitted)
        ordered = first + [entry.ref for entry in entries if entry.ref not in set(first)]
        decided = [(ref, receipt) for ref in ordered if (receipt := admission.receipt_for(ref)) is not None]
        return decided + [
            (ref, voi.not_in_plan_receipt(voi.SITE_PROJECT_PROBE, ref, why)) for ref, why in unavailable
        ]

    return admit


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
    # Owner decision 2026-10-12: re-entry stays short (repair and maintain
    # only), and the plan "keep going" builds after it (for the day's
    # remaining minutes, or the keep-going extension when none remain) leads
    # with new material: new takes its admitted minutes first in the split
    # (ordinary admission, ceiling and cap kept) and its blocks win the
    # chooser's ties.
    after_reentry = (
        kind in ("normal", "keep_going")
        and override is None
        and parent_plan_id is not None
        and any(record.id == parent_plan_id and record.kind == "reentry" for record in day)
    )
    built = _classified_pool(env, minutes=budget, lanes_allowed=lanes_allowed, day=day, reentry=reentry)
    pool = built.pool
    # Requests first (L3): up to requested_items_per_session go in the first
    # block, their estimates deducted from the budget before the split.
    per_session = int(env.vault.config.tutor_promotion.requested_items_per_session)
    if built.request_ids is not None:
        # Selected once, before the due project probes were valued (F14): the
        # same requests whose minutes the probes' admission left out.
        by_id = {item.practice_item_id: item for item in pool}
        requests = [
            by_id[item_id] for item_id in built.request_ids if item_id in by_id and by_id[item_id].lane is not None
        ]
        requested_minutes = sum(item.est_minutes for item in requests)
    else:
        requests, requested_minutes = _select_requests(pool, budget=budget, per_session=per_session)
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
    reading_rule: str | None = None
    if bool(config.reading_blocks) and not reentry and override is None and not _reading_used_today(day):
        from_furthest = reading_from_furthest_active(env.vault)
        reading_rule = reading_step_rule(env.vault)
        # Protection whatever the reading order (exam protection by extraction
        # identity, final verify F15): the setting orders the step, the one
        # exam predicate decides what may be one; unreadable, no step. With
        # the serving rules' kill switch off, DL1's order is DL1's selection
        # exactly, as before (identity review F6).
        protected = reading_rule != READING_RULE_DL1
        exam = _exam_material(env.vault, env.repository) if protected else None
        if not (protected and exam is None):
            reading = next_reading_target(env.repository, from_furthest=from_furthest, exam=exam)
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
        new_first=override == "more_new" or after_reentry,
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
        # Which rule chose the reading step (identity review F6): U4's order,
        # DL1's order with exam protection, or DL1's selection exactly (the
        # serving rules' kill switch off); None when no step was considered.
        "reading_rule": reading_rule,
        "reading_full_minutes": round(reading_full, 4) if reading_full is not None else None,
        # The plan's universe: nothing new joins mid-plan (§6.1), except
        # follow-ups produced by this session's answers.
        "universe": [item.practice_item_id for item in pool],
        "followups_at_build": [item.practice_item_id for item in pool if item.followup],
        "pool": [item.as_dict() for item in pool if item.lane is not None][:400],
        "reentry_gap": {"due": gap.due, "gap_days": gap.gap_days, "threshold_days": gap.threshold_days, "last_activity_at": gap.last_activity_at},
        "items_cap": int(config.reentry_max_items) if reentry else None,
        "replans": [],
        # Owner decision 2026-10-12: which rule decided the repair lane (an
        # open diagnosed problem; the recency fallback while the split is off).
        "repair_rule": built.repair_rule,
        "new_first": "more_new" if override == "more_new" else ("after_reentry" if after_reentry else None),
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
        # The plan's planned and skipped items, plus adaptive difficulty AD2+AD3's
        # deferrals (spec §6.1 step 0) only as the switch-aware context states them:
        # none with ``selection`` off, less what a boundary released (Codex verify
        # F13). Held fixed by the projection.
        taken = sim.exclusion_ids() | set(context.ad_deferred)
        taken |= {item.practice_item_id for item in pending}  # forced: never packed again (re-review F11)
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
    try:
        _boundary(env, record, context, forced=prepared.requests, forced_origin=ORIGIN_REQUESTED)
    except DecisionPending:
        # Router R2b: the first block's models are still out (Today's open is a
        # read). The plan stands without a block; the next call decides it
        # (``advance`` crosses the open boundary, placing the requests first).
        pass
    except PlanWaiting:
        # UX Phase 4 round 7: nothing to do until a hold lifts later today.
        # The plan stands open without a block; ``advance`` says what it waits for.
        pass
    return _reload(env, plan_id)


def _config_hash(config: Any) -> str:
    payload = json.dumps(config.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _context_from_build(env: PlanEnv, record: PlanRecord, built: _Pool) -> PoolContext:
    return _context(env, record, built, day=day_records(env))


def _ad_selection(env: PlanEnv) -> bool:
    from learnloop.adaptive_difficulty.successor import selection_on

    return selection_on(env.vault.config)


def day_ad_deferrals(env: PlanEnv, record: PlanRecord | None = None) -> dict[str, dict[str, Any]]:
    """The day's active AD deferrals (spec §6.1 step 0): every plan of the day, its blocks in
    creation order (a later plan of the same day starts with them)."""

    plans = list(day_records(env))
    if record is not None and all(plan.id != record.id for plan in plans):
        plans.append(record)
    plans = [record if record is not None and plan.id == record.id else plan for plan in plans]
    blocks = sorted(((block.created_at, block.ordinal, block) for plan in plans for block in plan.blocks),
                    key=lambda entry: (entry[0], entry[1]))
    active: dict[str, dict[str, Any]] = {}
    for _created, _ordinal, block in blocks:
        for item_id in ((block.chosen or {}).get("ad_deferrals") or {}).get("cleared") or ():
            active.pop(str(item_id), None)
        for item in block.items:
            if item.displaced and item.displaced_reason == AD_INELIGIBLE and item.displaced_at:
                detail = item.displaced_detail or {}
                active.setdefault(item.practice_item_id, {"since": item.displaced_at,
                                                          "failed": list(detail.get("failed") or [])})
    return active


def _context(env: PlanEnv, record: PlanRecord, built: _Pool, *, day: Sequence[PlanRecord],
             released: Iterable[str] = ()) -> PoolContext:
    """The source's view at one boundary: the plan's universe minus what it took."""

    split = record.split
    universe = set(split.get("universe") or [])
    taken = record.planned_ids()
    # Skipped items stay out of this plan (the learner skipped them).
    taken |= {item.practice_item_id for item in record.items() if item.skipped}
    # Adaptive difficulty AD2+AD3 (spec §6.1 step 0): an item AD displaced as
    # ineligible stays out of every pool of the day's plans until a boundary
    # re-reads its checks and clears it (none exist with ``selection`` off).
    deferred = frozenset(day_ad_deferrals(env, record) if _ad_selection(env) else ()) - frozenset(released)
    taken |= deferred
    pool = tuple(
        item
        for item in built.pool
        if item.practice_item_id in universe and item.practice_item_id not in taken
    )
    # UX Phase 4 round 7: a cold check under a routine-display hold is not a
    # candidate while the hold lasts (``scheduler.cold_check_hold_until``).
    held_until = _routine_holds(env, [item.practice_item_id for item in pool])
    pool_with_held = pool
    if held_until:
        pool = tuple(item for item in pool if item.practice_item_id not in held_until)
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
        held_until=held_until,
        pool_with_held=pool_with_held if held_until else (),
        ad_deferred=deferred,
    )


def _routine_holds(env: PlanEnv, item_ids: Sequence[str]) -> dict[str, str]:
    """The given items held back now by a routine-display hold on their cold
    check, with when each hold lifts (UX Phase 4 round 7). A read: the
    deferral itself is persisted where the item would be served."""

    cold = _open_cold_check_items(env)
    if not cold:
        return {}
    from learnloop.scheduling.scheduler import cold_check_hold_until

    holds: dict[str, str] = {}
    for item_id in item_ids:
        if item_id not in cold:
            continue
        until = cold_check_hold_until(env.vault, env.repository, item_id, clock=env.clock, persist=False)
        if until is not None:
            holds[item_id] = until
    return holds


def _waiting_step(
    env: PlanEnv,
    record: PlanRecord,
    context: PoolContext,
    *,
    forced_minutes: float = 0.0,
    forced_items: int = 0,
    forced_allotment: Mapping[str, float] | None = None,
    forced_spent: Mapping[str, float] | None = None,
) -> dict[str, Any] | None:
    """What the plan waits for, or None (UX Phase 4 rounds 7 and 8).

    Called only when nothing is feasible now. The plan waits only when a
    held item would become feasible solely because its routine-display
    coverage lifts later TODAY (the plan's local day), under the plan's real
    constraints: the same redistribution and feasibility rule as the boundary
    (minutes left, the item allowance, the lanes and their minutes, the
    plan's admitted universe and every other exclusion already applied to the
    pool), evaluated with the pool as it will be at that moment (holds that
    lift later stay out). None of these depends on the clock except the
    holds. Otherwise None: the boundary closes as it did before round 7.
    """

    if not context.held_until or not context.pool_with_held:
        return None
    plan_day = str(record.row.get("local_date") or env.today())
    today: dict[str, str] = {}
    for item_id, until in context.held_until.items():
        try:
            moment = parse_utc(until)
        except ValueError:
            continue
        if moment is not None and moment.astimezone().date().isoformat() == plan_day:
            today[item_id] = until
    for until in sorted(set(today.values())):
        lifted = {item_id for item_id, at in context.held_until.items() if at <= until}
        at_lift = replace(
            context,
            pool=tuple(
                item
                for item in context.pool_with_held
                if item.practice_item_id not in context.held_until or item.practice_item_id in lifted
            ),
            held_until={item_id: at for item_id, at in context.held_until.items() if item_id not in lifted},
        )
        computed = _feasibility(
            record,
            at_lift,
            env.policy,
            forced_minutes=forced_minutes,
            forced_items=forced_items,
            forced_allotment=forced_allotment,
            forced_spent=forced_spent,
        )
        admitted = [
            candidate for candidate in computed.feasible if lifted & set(candidate.item_ids)
        ]
        if not admitted:
            continue
        item_id = next(item for item in admitted[0].item_ids if item in lifted)
        seconds = max((parse_utc(until) - env.now()).total_seconds(), 0.0)
        item = env.vault.practice_items.get(item_id)
        learning_object_id = getattr(item, "learning_object_id", None) if item is not None else None
        return {
            "kind": "waiting",
            "plan_id": record.id,
            "until": until,
            "minutes": max(math.ceil(seconds / 60.0), 1),
            "practice_item_id": item_id,
            "learning_object_id": learning_object_id,
            "learning_object_title": context.titles.get(learning_object_id) if learning_object_id else None,
        }
    return None


def _live_context(
    env: PlanEnv, record: PlanRecord, *, minutes_left: float | None = None
) -> tuple[PoolContext, _Pool]:
    built = _classified_pool(
        env,
        minutes=record.budget,
        lanes_allowed=record.lanes_allowed,
        day=day_records(env),
        reentry=record.kind == "reentry",
        record=record,
        minutes_left=minutes_left,
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
    #: Router R2a: the source's own record of this boundary (the staged
    #: frame's snapshot hash, refusals and annotations); None from DL1's source.
    source_record: Mapping[str, Any] | None = None
    #: Router R2a: the chooser's own record (its card, mode, policy), kept
    #: even when its choice fell back; None from DL1's chooser.
    router_record: Mapping[str, Any] | None = None


def _items_left(record: PlanRecord, *, forced_items: int = 0) -> int | None:
    cap = record.split.get("items_cap")
    if cap is None:
        return None
    return max(int(cap) - record.item_count() - int(forced_items), 0)


def _intents(context: PoolContext) -> dict[str, IntentView]:
    los = {item.learning_object_id for item in context.pool}
    return {lo: IntentView(deadline=context.deadlines.get(lo)) for lo in sorted(los)}


@dataclass(frozen=True)
class _Feasibility:
    """What a boundary may choose from (§6.8): the redistributed state, the
    source's candidates and the feasible ones, under the plan's minutes left,
    item allowance and lane rules."""

    state: PlanState
    source: Any
    candidates: list[Any]
    feasible: list[Any]
    minutes_left: float
    redistribution: dict[str, Any] | None


def _feasibility(
    record: PlanRecord,
    context: PoolContext,
    policy: PlanPolicy,
    *,
    forced_minutes: float = 0.0,
    forced_items: int = 0,
    forced_allotment: Mapping[str, float] | None = None,
    forced_spent: Mapping[str, float] | None = None,
) -> _Feasibility:
    """Redistribution and feasibility at one boundary, before any choice. Pure."""

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
        lane_priority=(
            AFTER_REENTRY_LANE_PRIORITY if record.split.get("new_first") == "after_reentry" else LANES
        ),
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
    return _Feasibility(
        state=state,
        source=source,
        candidates=candidates,
        feasible=feasible,
        minutes_left=minutes_left,
        redistribution=redistribution,
    )


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

    computed = _feasibility(
        record,
        context,
        policy,
        forced_minutes=forced_minutes,
        forced_items=forced_items,
        forced_allotment=forced_allotment,
        forced_spent=forced_spent,
    )
    state, source, candidates, feasible = computed.state, computed.source, computed.candidates, computed.feasible
    minutes_left, redistribution = computed.minutes_left, computed.redistribution
    stop_offered = minutes_left < STOP_OFFER_MINUTES or not feasible
    describe = getattr(source, "decision_record", None)
    source_record = describe() if callable(describe) else None
    reason: str | None = None
    try:
        choice = policy.chooser.choose(state, feasible)
    except DecisionPending:
        # Router R2b: a read found the decision's models still out. Nothing
        # is decided; the boundary stays open for the next call.
        raise
    except Exception as exc:  # noqa: BLE001 - a broken chooser falls back (rule 2)
        choice = BlockChoice(candidate_id=f"<error: {type(exc).__name__}>", chosen_by="lane_quota", propensity=None, why="", why_kind="computed")
        reason = "chooser_error"
    router_record = getattr(choice, "router_record", None)
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
        source_record=source_record,
        router_record=router_record,
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
        **({"lane_priority": list(state.lane_priority)} if tuple(state.lane_priority) != tuple(LANES) else {}),
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
    block_id: str | None = None,
) -> str:
    block_id = block_id or new_ulid()
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
    ad_deferrals: Mapping[str, Any] | None = None,
) -> str | None:
    """Choose and persist the next block, or close the plan. Returns the block id."""

    forced = list(forced)
    forced_ids = {item.practice_item_id for item in forced}
    if forced_ids:
        # Forced items (requests, follow-ups) are placed whatever is chosen, so
        # the source never sees them: a candidate packing one again would plan
        # it twice in one block, and the copy would never resolve (re-review F11).
        context = replace(context, pool=tuple(item for item in context.pool if item.practice_item_id not in forced_ids))
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
    if ad_deferrals:
        # Adaptive difficulty (spec §6.1 step 0): the AD deferrals this boundary
        # applied and the ones it cleared, so each decision's pool rebuilds.
        detail["ad_deferrals"] = {"applied": list(ad_deferrals.get("applied") or []),
                                  "cleared": list(ad_deferrals.get("cleared") or [])}
    voi_decisions = [dict(item.voi) for item in context.pool if item.voi is not None]
    if voi_decisions:
        # mvp-0.21: the value-of-information decisions on today's due project
        # probes (admitted or held back), logged with the block decision.
        detail["voi_decisions"] = voi_decisions
    router_record = decision.router_record
    if decision.source_record:
        # Router R2a: the staged frame's refusals (each item a named hard
        # constraint refused, with its reason) and its snapshot hash.
        detail["staged_frame"] = dict(decision.source_record)
    if router_record:
        # Router R2a: the router chooser's summary (its learner-state card is
        # stored beside the router decision, not on this receipt).
        detail["router"] = router_summary(router_record)
    candidate = decision.candidate
    if candidate is None and not forced:
        # UX Phase 4 rounds 7 and 8: a temporary routine-display hold never
        # finishes the plan. Only when nothing is feasible now, and a held
        # item would be feasible once its hold lifts later today, the plan
        # waits; otherwise it closes with the chooser's decision, as before
        # (a stop the chooser chose with work feasible is that stop).
        waiting = (
            _waiting_step(
                env,
                record,
                context,
                forced_minutes=forced_minutes,
                forced_items=len(forced),
                forced_allotment=forced_allotment,
                forced_spent=forced_spent,
            )
            if not decision.feasible
            else None
        )
        if waiting is not None:
            raise PlanWaiting(waiting)
        _close(
            env, record, status="complete", reason=choice.why or "nothing more worth doing today",
            stop_detail=detail, log_decision=True, router_record=router_record,
        )
        return None
    items: list[tuple[PoolItem | PlannedItem, str]] = [(item, forced_origin) for item in forced]
    by_id = {item.practice_item_id: item for item in context.pool}  # forced ids are not in it
    if candidate is not None:
        items.extend(
            (by_id[item_id], ORIGIN_CHOOSER)
            for item_id in candidate.item_ids
            if item_id in by_id and item_id not in forced_ids
        )
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
        block_id = new_ulid()
        # Router R1's hook (owner decision 2026-10-12): the decision is logged
        # as a ``plan_block`` router decision in this block's transaction.
        logged = _log_plan_decision(
            connection,
            PlanBlockDecision(
                plan_id=record.id,
                plan_kind=record.kind,
                local_date=str(record.row.get("local_date") or ""),
                block_id=block_id,
                session_id=env.session_id,
                detail=detail,
                chosen_by=chosen_by,
                items=tuple((item.practice_item_id, item.learning_object_id) for item, _origin in items),
                decided_at=env.now_iso(),
                config=env.vault.config,
                router_record=router_record,
            ),
        )
        if decision_ref is None and logged is not None:
            decision_ref = logged
            detail["decision_ref"] = logged
        _persist_block(
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
            block_id=block_id,
        )
    _record_probe_value_forecasts(env, detail, block_id=block_id, decision_ref=decision_ref)
    return block_id


def _record_probe_value_forecasts(
    env: PlanEnv, detail: Mapping[str, Any], *, block_id: str, decision_ref: str | None
) -> None:
    """mvp-0.21 composed with EVSI calibration: the block decision's due
    project probe receipts as ``voi_forecasts`` rows, after the block (and
    router R1's ``plan_block`` row, its ``decision_ref``) committed. Logging
    only, behind ``evsi.forecast_logging``."""

    receipts = detail.get("voi_decisions") or ()
    if not receipts:
        return
    from learnloop.diagnosis import voi_stopping as voi

    voi.record_plan_value_forecasts(
        env.vault, env.repository, list(receipts), block_id=block_id, decision_ref=decision_ref
    )


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
    receipt_id: str | None = None,
) -> str:
    """A plan-level receipt row: a decision that is not one of the plan's
    numbered blocks (a stop, a pick after the plan closed). Append-only: an
    ``attention_blocks`` row of the plan with no ordinal, and its
    ``block_chosen`` event (§6.8 rule 6; review F6, F10)."""

    receipt_id = receipt_id or new_ulid()
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


def _close(
    env: PlanEnv,
    record: PlanRecord,
    *,
    status: str,
    reason: str,
    stop_detail: Mapping[str, Any] | None = None,
    log_decision: bool = False,
    router_record: Mapping[str, Any] | None = None,
) -> None:
    """Close the plan. A chooser's stop (``stop_detail``: the candidate set,
    chooser, propensity and fallback) is appended as a stop receipt, so a plan
    reopened by a minutes tap and stopped again keeps both decisions (F6).
    ``log_decision``: the stop is a block-boundary decision (``_boundary``),
    handed to router R1's hook like a block."""

    now = env.now_iso()
    with env.repository.atomic(), env.repository.connection() as connection:
        if stop_detail is not None:
            detail = {**dict(stop_detail), "stop_reason": reason, "status": status}
            receipt_id = new_ulid()
            decision_ref = detail.get("decision_ref")
            if log_decision:
                logged = _log_plan_decision(
                    connection,
                    PlanBlockDecision(
                        plan_id=record.id,
                        plan_kind=record.kind,
                        local_date=str(record.row.get("local_date") or ""),
                        block_id=receipt_id,
                        session_id=env.session_id,
                        detail=detail,
                        stop=True,
                        chosen_by=str(stop_detail.get("chosen_by") or "lane_quota"),
                        decided_at=now,
                        config=env.vault.config,
                        router_record=router_record,
                    ),
                )
                if decision_ref is None and logged is not None:
                    decision_ref = logged
                    detail["decision_ref"] = logged
            _persist_receipt(
                env,
                connection,
                record,
                action=RECEIPT_STOP,
                chosen_by=str(stop_detail.get("chosen_by") or "lane_quota"),
                decision_ref=decision_ref,
                detail=detail,
                receipt_id=receipt_id,
            )
        store.update_plan(
            connection,
            record.id,
            status=status,
            stop_reason=reason,
            updated_at=now,
            completed_at=now,
        )
    if stop_detail is not None and log_decision:
        # The chooser's stop is a block-boundary decision too: its due project
        # probes' value decisions are forecasts (after the stop committed).
        _record_probe_value_forecasts(env, detail, block_id=receipt_id, decision_ref=decision_ref)


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
    # UX Phase 4 rounds 5 and 6: a planned cold check is revalidated before it
    # is served; one a routine display covers is displaced (its task deferred
    # until that coverage ends, when the queue serves it again).
    cold_items = _open_cold_check_items(env)
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
                continue
            if item.served_at is None and item.practice_item_id in cold_items:
                from learnloop.scheduling.scheduler import cold_check_serve_hold

                hold = cold_check_serve_hold(vault, env.repository, item.practice_item_id, clock=env.clock)
                if hold is not None:
                    writes.append(
                        (item.block_id, "item_displaced", {"practice_item_id": item.practice_item_id, "reason": hold})
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


def _open_cold_check_items(env: PlanEnv) -> frozenset[str]:
    """Items an open cold follow-up task selects (the measurement lanes)."""

    from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS

    try:
        return frozenset(
            str(task.get("selected_item_id"))
            for kind in sorted(COLD_FOLLOWUP_TASK_KINDS)
            for task in env.repository.open_followup_tasks_of_kind(kind)
            if task.get("selected_item_id")
        )
    except Exception:  # noqa: BLE001 - a read that fails holds nothing back here; submit still guards
        return frozenset()


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

    Router R2c's restraint (``env.policy.restraint``) decides each placeable
    follow-up in turn against the plan as the earlier ones left it (Codex
    review F6): an insertion is applied before the next follow-up is
    considered, so every ``insert_now`` it logs is placed. A follow-up that
    waits keeps its minutes (and its item slot) for the boundary, and waiting
    is offered only when that room exists: otherwise it joins now (Codex
    review F8), since the restraint decides only now or at the boundary,
    never whether.

    Returns the follow-ups to force into the next block when none is current.
    """

    followups = _pending_followups(record, built)
    if not followups or not record.is_open:
        return record, []
    # Router R2c: the restraint gate (None: DL1's rules alone, unchanged).
    gate = getattr(env.policy, "restraint", None)
    if gate is not None:
        refused = record.refused_followups()
        followups = [item for item in followups if item.practice_item_id not in refused]
        if not followups:
            return record, []
    cap = record.split.get("items_cap")
    current = record.current_block()
    if current is None or current.is_reading:
        fitted: list[PoolItem] = []
        refused_now: list[tuple[PoolItem, Any]] = []
        free = record.minutes_left()
        slots = None if cap is None else max(int(cap) - record.item_count(), 0)
        # A follow-up the restraint let wait was promised the next block: it
        # takes the room kept for it before any other, and is placed in that
        # room even when its estimate has grown since (Codex review F8).
        waiting: dict[str, float | None] = {}
        for block in record.blocks:
            for item_id in block.deferred_followups():
                waiting[item_id] = block.followup_kept.get(item_id)
        followups = sorted(followups, key=lambda item: item.practice_item_id not in waiting)
        for item in followups:
            if slots is not None and len(fitted) >= slots:
                break
            if gate is not None:
                reasons = gate.refusals(item)
                if reasons:
                    # Router R2c: a follow-up a hard constraint refuses is
                    # never forced into the next block (G1 on follow-ups).
                    refused_now.append((item, gate.declined(reasons)))
                    continue
            kept = waiting.get(item.practice_item_id)
            if kept is not None and item.est_minutes > kept:
                item = replace(item, est_minutes=kept)
            if item.est_minutes <= free + _EPS:
                fitted.append(item)
                free -= item.est_minutes
        # The refusal is logged once, on the block whose answer produced the
        # follow-up (or the current reading block), and never rechecked.
        anchor = current or (record.blocks[-1] if record.blocks else None)
        if refused_now and anchor is not None:
            now = env.now_iso()
            with env.repository.atomic(), env.repository.connection() as connection:
                for item, outcome in refused_now:
                    decision_ref = _log_interrupt(env, connection, record, anchor, item, outcome)
                    _event(connection, anchor.id, "followup_refused",
                           {"practice_item_id": item.practice_item_id, "decision_ref": decision_ref,
                            "propensity": outcome.propensity}, now)
            record = _reload(env, record.id)
        return record, fitted
    if gate is not None:
        return _restrained_followups(env, record, current, followups, gate, cap)
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
            position += 1
            lane, release = _place_followup(record, current, item, victims, position=position, now=now)
            _write_followup(connection, current, item, victims, lane=lane, release=release, position=position,
                            decision_ref=None, now=now)
            protected.add(item.practice_item_id)
    return _reload(env, record.id), []


def _place_followup(
    record: PlanRecord, current: PlannedBlock, item: PoolItem, victims: Sequence[PlannedItem], *, position: int,
    now: str,
) -> tuple[str, dict[str, Any] | None]:
    """Apply one follow-up's placement to the in-memory plan (its victims
    displaced, the follow-up appended to the current block); returns its lane
    and its lane release. The caller writes the matching events."""

    for victim in victims:
        victim.displaced_at = now
    lane = item.lane or "repair"
    release = _followup_release(
        record.lane_left(), record.minutes_left(), item.est_minutes, lane=lane, lanes_allowed=record.lanes_allowed
    )
    current.items.append(
        PlannedItem(
            block_id=current.id, position=position, practice_item_id=item.practice_item_id,
            learning_object_id=item.learning_object_id, lane=lane, est_minutes=item.est_minutes,
            origin=ORIGIN_FOLLOWUP, planned_at=now, lane_release=release,
        )
    )
    return lane, release


def _write_followup(
    connection: Any, current: PlannedBlock, item: PoolItem, victims: Sequence[PlannedItem], *, lane: str,
    release: dict[str, Any] | None, position: int, decision_ref: str | None, now: str,
) -> None:
    """The events of one placed follow-up: its victims' displacement, then its ``item_planned``."""

    for victim in victims:
        _event(
            connection,
            victim.block_id,
            "item_displaced",
            {"practice_item_id": victim.practice_item_id, "reason": "displaced", "by": item.practice_item_id},
            now,
        )
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
            **({"decision_ref": decision_ref} if decision_ref is not None else {}),
        },
        now,
    )


def _restrained_followups(
    env: PlanEnv, record: PlanRecord, current: PlannedBlock, followups: Sequence[PoolItem], gate: Any, cap: Any,
) -> tuple[PlanRecord, list[PoolItem]]:
    """Router R2c: each placeable mid-block follow-up's ``plan_interrupt`` decision.

    Decided one at a time, outside any write (no lock is held on a model),
    each against the plan the earlier decisions left (Codex review F6): a
    joining follow-up's placement is applied in memory before the next is
    considered, and a waiting one keeps its minutes and item slot. Then one
    write logs every decision with exactly the placement it describes. A
    follow-up the rules would not place now is not decided (G4); one whose
    models are still out on a read is left for the next call."""

    now = env.now_iso()
    # A follow-up the current block's restraint already let wait is forced into
    # the next block (the end-of-block path); its room (its estimate when it
    # was deferred) stays kept until then (Codex review F8).
    deferred = current.deferred_followups()
    kept = {
        item.practice_item_id: current.followup_kept.get(item.practice_item_id, item.est_minutes)
        for item in followups if item.practice_item_id in deferred
    }
    kept_minutes = sum(kept.values())
    kept_items = len(kept)
    protected = {item.practice_item_id for item in record.items() if item.origin == ORIGIN_FOLLOWUP}
    position = max((item.position for item in current.items), default=0)
    decided: list[tuple[PoolItem, Any, list[PlannedItem], str | None, dict[str, Any] | None, int | None]] = []
    for item in followups:
        if item.practice_item_id in deferred:
            continue
        free = record.minutes_left() - kept_minutes
        count = record.item_count() + kept_items
        need_items = 0 if cap is None else max(count + 1 - int(cap), 0)
        victims = _displacement_plan(record, need_minutes=item.est_minutes - free, need_items=need_items,
                                     keep=protected)
        if victims is None:
            # The rules would not place it now: never forced (G4).
            continue
        # Waiting is a choice only when the boundary will still have room for
        # it after the current block's own items (Codex review F8).
        wait_room = item.est_minutes <= free + _EPS and (cap is None or count + 1 <= int(cap))
        try:
            outcome = gate.decide(record, current, item, wait_feasible=wait_room)
        except DecisionPending:
            continue
        if outcome.insert:
            position += 1
            lane, release = _place_followup(record, current, item, victims, position=position, now=now)
            protected.add(item.practice_item_id)
            decided.append((item, outcome, list(victims), lane, release, position))
            continue
        if outcome.wait:
            kept_minutes += item.est_minutes
            kept_items += 1
        decided.append((item, outcome, [], None, None, None))
    if not decided:
        return record, []
    with env.repository.atomic(), env.repository.connection() as connection:
        for item, outcome, victims, lane, release, placed_at in decided:
            decision_ref = _log_interrupt(env, connection, record, current, item, outcome)
            if not outcome.insert:
                _event(
                    connection,
                    current.id,
                    "followup_refused" if outcome.refused else "followup_deferred",
                    {"practice_item_id": item.practice_item_id, "decision_ref": decision_ref,
                     "propensity": outcome.propensity,
                     **({"kept_minutes": round(item.est_minutes, 4)} if outcome.wait else {})},
                    now,
                )
                continue
            _write_followup(connection, current, item, victims, lane=str(lane), release=release,
                            position=int(placed_at or 0), decision_ref=decision_ref, now=now)
    return _reload(env, record.id), []


def _log_interrupt(
    env: PlanEnv, connection: Any, record: PlanRecord, current: PlannedBlock, item: PoolItem, outcome: Any
) -> str | None:
    """Router R2c: the follow-up's ``plan_interrupt`` row, on the write's own connection."""

    from learnloop.router.plan_log import log_plan_interrupt_decision

    try:
        return log_plan_interrupt_decision(
            connection,
            {
                "plan_id": record.id,
                "plan_kind": record.kind,
                "local_date": str(record.row.get("local_date") or ""),
                "block_id": current.id,
                "parent_decision_id": None,
                "session_id": env.session_id,
                "followup": {
                    "practice_item_id": item.practice_item_id,
                    "learning_object_id": item.learning_object_id,
                    "lane": item.lane,
                    "est_minutes": round(float(item.est_minutes), 4),
                    "reason": item.reason,
                },
                "chosen_ref": outcome.chosen_ref,
                "propensity": outcome.propensity,
                "refused": outcome.refused,
                "wait_feasible": bool(getattr(outcome, "wait_feasible", True)),
                "router_record": outcome.record,
                "why": outcome.why,
                "decided_at": env.now_iso(),
                "config": env.vault.config,
            },
        )
    except Exception:  # noqa: BLE001 - logging never blocks the learner's plan
        import logging

        logging.getLogger(__name__).warning("plan_interrupt decision not logged", exc_info=True)
        return None


# -- the next step -------------------------------------------------------------------


def _item_step(
    env: PlanEnv,
    record: PlanRecord,
    block: PlannedBlock,
    item: PlannedItem,
    *,
    boundary: bool,
    candidate_id: str | None,
    presentation_id: str | None = None,
) -> dict[str, Any]:
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
        # Router R2a: the receipt an answer binds to (``plan_presentation_id``
        # on submit); None until the item is served.
        "presentation_id": presentation_id,
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
        record=record,
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
        ad_deferrals = None
        if _ad_selection(env):
            # Adaptive difficulty (spec §6.1 step 0): at each boundary the day's
            # AD deferrals are re-read with the draw's own checks; those that
            # pass rejoin the pool here, and the decision records both.
            active = day_ad_deferrals(env, record)
            if active:
                from learnloop.daily_plan import ad_slot

                cleared = ad_slot.deferrals_to_clear(env, active, built=built)
                ad_deferrals = {"applied": sorted(set(active) - set(cleared)), "cleared": sorted(cleared)}
                context = _context(env, record, built, day=(), released=cleared)
        try:
            block_id = _boundary(env, record, context, forced=forced, forced_origin=forced_origin,
                                 ad_deferrals=ad_deferrals)
        except DecisionPending:
            # Router R2b: the decision's models are still out on a read. No
            # step yet: the view says the next block is being chosen.
            return record, None, context  # type: ignore[return-value]
        except PlanWaiting as waiting:
            # UX Phase 4 round 7: the plan waits for a hold that lifts today.
            return record, waiting.step, context
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
    if serve and item.served_at is None and _ad_selection(env):
        from learnloop.adaptive_difficulty.serving import slot_applies

        if slot_applies(env.vault.config, item):
            served = _ad_slot_serve(env, record, block, item, built, context, boundary=boundary)
            if served is None:
                # Displaced as ineligible (spec §6.1 step 0): the plan's rules pick the next step.
                return advance_with_context(env, serve=serve)
            if served is not _AD_UNAVAILABLE:
                return served
            # AD is unavailable for this slot (A8, fail closed; Codex verify F22): the planned item
            # is served below exactly as the incumbent serves it.
    eligibility = None
    if serve and item.served_at is None:
        held, eligibility = _held_cold_check(env, block, item)
        if held:
            # Displaced at the serve itself (a block planned in this very call is
            # not reconciled first): plan the next step instead (round 5). The
            # pool no longer holds it, so the next step is another item.
            return advance_with_context(env, serve=serve)
    candidate_id = context.candidate_ids.get(item.practice_item_id)
    step = _item_step(
        env, record, block, item, boundary=boundary, candidate_id=candidate_id,
        presentation_id=_standing_presentation(env, block, item) if item.served_at is not None else None,
    )
    if eligibility is not None:
        # One eligibility decision: its cold check cannot be taken now, so the
        # item is served as practice (its task re-timed), and the step says so.
        step["eligibility"] = {
            "verdict": eligibility.verdict, "reason": eligibility.reason,
            "message": eligibility.message, "check_due_at": eligibility.until,
        }
    if serve:
        step["presentation_id"] = _serve(env, block, item, candidate_id=candidate_id)
        record = _reload(env, record.id)
    return record, step, context


#: ``_ad_slot_serve``'s answer when AD cannot decide the slot safely (the held-out predicate or
#: the routine exclusions could not be computed): the incumbent serves the planned item.
_AD_UNAVAILABLE: Any = object()


def _ad_slot_serve(
    env: PlanEnv, record: PlanRecord, block: PlannedBlock, item: PlannedItem, built: _Pool, context: PoolContext,
    *, boundary: bool,
) -> Any:
    """Adaptive difficulty AD2+AD3 (spec §6.1): the slot's support, AD's draw, its
    ``ad_selections`` row, any ``item_substituted`` event and ``item_served``, in one
    transaction (a propensity is never recomputed after the draw). None when the slot
    was displaced as ineligible; :data:`_AD_UNAVAILABLE` (nothing written) when AD is
    unavailable for it."""

    from learnloop.adaptive_difficulty.serving import decide_slot
    from learnloop.daily_plan import ad_slot

    import logging

    with env.repository.atomic():
        try:
            # One AD operation for the support and the draw (the AD23 redesign); a refusal inside it
            # rolls its savepoint back, so nothing of AD's is written and the planned item is served.
            with ad_slot.slot_operation(env) as view:
                request = ad_slot.build_request(env, record, block, item, built, day=day_records(env),
                                                router_propensity=ad_slot.router_propensity(record, block), view=view)
                decision = decide_slot(env.vault, env.repository, request, view=view)
        except ad_slot.AdUnavailable:
            logging.getLogger(__name__).warning(
                "adaptive difficulty unavailable for slot %s/%s: the planned item is served", block.id,
                item.position, exc_info=True)
            return _AD_UNAVAILABLE
        now = env.now_iso()
        with env.repository.connection() as connection:
            if decision.action == "displace":
                _event(connection, block.id, "item_displaced", {
                    "practice_item_id": item.practice_item_id, "reason": AD_INELIGIBLE,
                    "failed": list(decision.slot_failed), "selection_id": decision.selection_id,
                }, now)
                return None
            if decision.action == "substitute" and decision.chosen_item_id:
                drawn = next((c for c in request.candidates if c.practice_item_id == decision.chosen_item_id), None)
                _event(connection, block.id, "item_substituted", {
                    "practice_item_id": decision.chosen_item_id, "slot_item_id": item.practice_item_id,
                    "learning_object_id": item.learning_object_id,
                    "est_minutes": round(float(drawn.est_minutes if drawn else item.est_minutes), 4),
                    "slot_est_minutes": round(float(item.est_minutes), 4),
                    "selection_id": decision.selection_id,
                }, now)
        record = _reload(env, record.id)
        block = next(b for b in record.blocks if b.id == block.id)
        served = next((planned for planned in block.items
                       if planned.position == item.position and not planned.resolved), None)
        if served is None:  # pragma: no cover - the slot always holds the drawn item
            return None
        candidate_id = context.candidate_ids.get(served.practice_item_id)
        step = _item_step(env, record, block, served, boundary=boundary, candidate_id=candidate_id)
        detail = decision.step_detail()
        if detail is not None:
            step["adaptive_difficulty"] = detail
        step["presentation_id"] = _serve(env, block, served, candidate_id=candidate_id)
    record = _reload(env, record.id)
    return record, step, context


def _held_cold_check(env: PlanEnv, block: PlannedBlock, item: PlannedItem) -> tuple[bool, Any]:
    """Revalidate a cold check at the moment the plan would serve it (the one
    eligibility decision, ``scheduler.cold_check_serve_decision``): one whose
    hold time clears (a routine display, a reveal since it was scheduled) is
    displaced, with the reason; one submit would prime with no lapse is
    served as practice, its task re-timed. Returns ``(displaced, decision)``,
    the decision only when it is not a plain serve."""

    if item.practice_item_id not in _open_cold_check_items(env):
        return False, None
    from learnloop import serve_eligibility
    from learnloop.scheduling.scheduler import cold_check_serve_decision

    decision = cold_check_serve_decision(env.vault, env.repository, item.practice_item_id, clock=env.clock)
    if decision.verdict == serve_eligibility.SERVE:
        return False, None
    if decision.verdict == serve_eligibility.SERVE_AS_ORDINARY:
        return False, decision
    with env.repository.atomic(), env.repository.connection() as connection:
        _event(
            connection, block.id, "item_displaced",
            {"practice_item_id": item.practice_item_id, "reason": decision.reason}, env.now_iso(),
        )
    return True, decision


def _standing_presentation(env: PlanEnv, block: PlannedBlock, item: PlannedItem) -> str | None:
    """The presentation an already-served plan item was served under, if any."""

    from learnloop.db.stores import plan_presentations as presentations

    try:
        with env.repository.connection() as connection:
            if not presentations.plan_presentations_present(connection):
                return None
            row = presentations.presentation_for(connection, block.id, item.practice_item_id)
    except Exception:  # noqa: BLE001 - a receipt read never blocks the plan
        return None
    return str(row["id"]) if row is not None else None


def _present(
    env: PlanEnv,
    connection: Any,
    *,
    block_id: str,
    decision_ref: str | None,
    practice_item_id: str,
    position: int | None,
    origin: str,
    candidate_id: str | None,
    served_at: str,
) -> str | None:
    """Router R2a: the served item's ``plan_presentations`` row, in the serve's
    own transaction (one per block and item: a reopen returns the first).

    The router decision that placed the item (its block's, or the
    ``plan_interrupt`` decision that inserted a follow-up: Codex review F1)
    and the staged controller decision it named are copied from the ledger,
    so a decision id the ledger does not hold (a chooser's own reference) is
    never written. Logging: a refused row rolls
    back alone with a warning and the item is still served."""

    from learnloop.db.stores import plan_presentations as presentations

    if not presentations.plan_presentations_present(connection):
        return None
    connection.execute("SAVEPOINT plan_presentation")
    try:
        router_decision_id = controller_decision_id = None
        if decision_ref:
            row = connection.execute(
                "SELECT id, controller_decision_id FROM router_decisions WHERE id = ?", (decision_ref,)
            ).fetchone()
            if row is not None:
                router_decision_id, controller_decision_id = row["id"], row["controller_decision_id"]
        presentation_id = presentations.insert_plan_presentation(
            connection,
            {
                "id": new_ulid(),
                "block_id": block_id,
                "router_decision_id": router_decision_id,
                "controller_decision_id": controller_decision_id,
                "practice_item_id": practice_item_id,
                "position": position,
                "origin": origin,
                "scheduler_candidate_id": candidate_id,
                "probe_presentation_id": None,
                "session_id": env.session_id,
                "served_at": served_at,
            },
        )
    except Exception:  # noqa: BLE001 - the receipt never blocks serving
        connection.execute("ROLLBACK TO plan_presentation")
        connection.execute("RELEASE plan_presentation")
        import logging

        logging.getLogger(__name__).warning("plan presentation of %s not recorded", practice_item_id, exc_info=True)
        return None
    connection.execute("RELEASE plan_presentation")
    return presentation_id


def _serve(env: PlanEnv, block: PlannedBlock, item: PlannedItem, *, candidate_id: str | None) -> str | None:
    """Record the item as served; returns its presentation (router R2a)."""

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
        from learnloop.db.stores import plan_presentations as presentations

        # Adaptive difficulty AD1 records only the serve that inserts the
        # presentation (Codex review F3): a reopen keeps the first serve's
        # served_at, and AD's inputs are what that serve saw, never today's.
        fresh = presentations.plan_presentations_present(connection) and presentations.presentation_for(
            connection, block.id, item.practice_item_id) is None
        presentation_id = _present(
            env,
            connection,
            block_id=block.id,
            # An inserted follow-up's presentation names the plan_interrupt
            # decision that placed it, not its block's (Codex review F1).
            decision_ref=item.decision_ref or block.decision_ref,
            practice_item_id=item.practice_item_id,
            position=item.position,
            origin=item.origin,
            candidate_id=candidate_id,
            served_at=item.served_at or now,
        )
        if presentation_id is not None and fresh:
            # Adaptive difficulty AD1 (spec §7.5, §8.1, §5.11): the reading
            # sweep, the frozen serve inputs and the in-process forecasts, in
            # this transaction and after the presentation. Logging only: it
            # rolls back alone on failure and never changes what is served.
            from learnloop.adaptive_difficulty import serve as ad_serve

            ad_serve.record_plan_serve(
                env.vault, env.repository, presentation_id=presentation_id,
                practice_item_id=item.practice_item_id, served_at=item.served_at or now,
            )
        return presentation_id


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
    build's unpublished slate. Only a live, shown offer counts: one in a
    published offer receipt and not yet answered. A used offer from a stale
    list, or a plan build's candidate (never published), falls back to the
    plan's own (re-review F13).
    """

    if not candidate_id:
        return None
    with env.repository.connection() as connection:
        row = connection.execute(
            "SELECT r.returned_candidate_ids_json AS shown FROM scheduler_slate_candidates c "
            "JOIN scheduler_slates s ON s.id = c.slate_id "
            "JOIN scheduler_offer_receipts r ON r.slate_id = c.slate_id "
            "WHERE c.id = ? AND c.practice_item_id = ? AND c.was_returned = 1 AND c.chosen_attempt_id IS NULL "
            "AND (s.session_id IS ? OR ? IS NULL)",
            (candidate_id, practice_item_id, env.session_id, env.session_id),
        ).fetchone()
    if row is None or candidate_id not in json.loads(row["shown"] or "[]"):
        return None
    return candidate_id


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
        presentation_id = _serve(env, block, planned, candidate_id=candidate_id)
        record = _reload(env, record.id)
        block = next(b for b in record.blocks if b.id == planned.block_id)
        return record, _item_step(
            env, record, block, planned, boundary=False, candidate_id=candidate_id, presentation_id=presentation_id
        )
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
            presentation_id = _present(
                env,
                connection,
                block_id=receipt_id,
                decision_ref=None,
                practice_item_id=practice_item_id,
                position=None,
                origin="open_list",
                candidate_id=candidate_id,
                served_at=env.now_iso(),
            )
        return _reload(env, record.id), {
            "kind": "item",
            "plan_id": None,
            "block_id": None,
            "practice_item_id": practice_item_id,
            "learning_object_id": practice_item.learning_object_id,
            "scheduler_candidate_id": candidate_id,
            "presentation_id": presentation_id,
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
        detail: dict[str, Any] = {
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
        }
        # Router R2a (G9; Codex review F4): the pick is the learner's own block
        # decision, logged (no propensity) in this block's transaction before
        # it is served, so its presentation and a proposal's delivery name it.
        block_id = new_ulid()
        decision_ref = _log_plan_decision(
            connection,
            PlanBlockDecision(
                plan_id=record.id,
                plan_kind=record.kind,
                local_date=str(record.row.get("local_date") or ""),
                block_id=block_id,
                session_id=env.session_id,
                detail=detail,
                chosen_by="learner_pick",
                items=((practice_item_id, lo_id),),
                decided_at=env.now_iso(),
                config=vault.config,
            ),
        )
        if decision_ref is not None:
            detail["decision_ref"] = decision_ref
        _persist_block(
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
            detail=detail,
            items=[(item, ORIGIN_LEARNER_PICK)],
            decision_ref=decision_ref,
            block_id=block_id,
        )
    record = _reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block_id)
    planned_item = block.items[0]
    presentation_id = _serve(env, block, planned_item, candidate_id=candidate_id)
    record = _reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block_id)
    return record, _item_step(
        env, record, block, block.items[0], boundary=False, candidate_id=candidate_id, presentation_id=presentation_id
    )


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
        # The pool the new split is sized from; due project probes are valued
        # against the minutes the NEW budget leaves (final verify F10).
        context, built = _live_context(env, record, minutes_left=max(budget - record.minutes_planned(), 0.0))
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
    "PlanBlockDecision",
    "PlanDecisionLogger",
    "PlanEnv",
    "PlanInactiveError",
    "PlanPolicy",
    "PlanStillOpenError",
    "PoolContext",
    "READING_OUTCOMES",
    "READING_RULE_BOOK_ORDER",
    "READING_RULE_DL1",
    "READING_RULE_FURTHEST",
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
    "plan_scheduler_session",
    "reading_from_furthest_active",
    "reading_step_rule",
    "reading_ended",
    "reconcile",
    "register_plan_decision_logger",
    "remembered_minutes",
    "set_minutes",
    "simulate_blocks",
    "staged_plans_deterministic",
    "stop_today",
    "unregister_plan_decision_logger",
]
