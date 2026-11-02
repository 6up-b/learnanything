---
title: "learnloop.daily_plan.engine"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/engine.py"
source_paths:
  - "src/learnloop/daily_plan/engine.py"
source_commit: "0005dbcf6f675a98a3d3b0a58a1af1fa137931e3"
source_commit_timestamp: "2026-11-01T02:20:07-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.engine module"
  - "src/learnloop/daily_plan/engine.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.engine`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.engine` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The plan container (``spec_daily_loop_v1.md`` §6.1-§6.8, §6.10, §7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py) |
| Source lines | 5047 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0005dbcf6f675a98a3d3b0a58a1af1fa137931e3` |
| Commit timestamp | `2026-11-01T02:20:07-05:00` |

## Public API

- `class PlanInactiveError(RuntimeError)` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 118) — The plan is off: a pre-mvp-0.14 vault or ``plan.enabled = false``.
- `class PlanWaiting(Exception)` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 122) — The boundary found nothing to do now, but a routine-display hold on a planned cold check lifts later today (UX Phase 4 round 7).
  - `__init__(self, step: dict[str, Any]) -> None` (line 128; internal)
- `plan_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 133) — The plan serves only at a daily-plan version with the kill switch on.
- `reading_from_furthest_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 142) — The reading block continues from the furthest section read (UX Phase 1, U4) wherever the plan acts, with its kill switch ``plan.reading_from_furthest`` on; off, it is DL1's order, the first unfinished section in book order.
- `reading_step_rule(vault: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 170) — Which rule chooses the plan's reading step.
- `reading_path_plan_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 188) — Reader workbench RW7b (spec_reader_workbench_v1 §10.2): the plan's reading block follows the learner's reading path, at RW7b's tag (``READING_PATH_PLAN_VERSIONS``) wherever the plan acts, with its kill switch ``reading_paths.plan_uses_path`` on and the Guide's paths on (``readin…
- `deliverable_plan_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 211) — Curriculum C1 (spec_deliverable_curriculum_v1 §7.6, §8.1): the plan's reading block follows the nearest active deliverable's fresh path across books, at C1's tag (``DELIVERABLE_PLAN_VERSIONS``), with its kill switch ``curriculum.plan_uses_path`` and ``curriculum.enabled`` on (th…
- `local_date(clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 590) — The plan's day: the machine's local calendar date, like the streak (D9).
- `local_day_start_iso(clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 596) — The start of the plan's day (local midnight), as a UTC timestamp.
- `class PoolContext` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 608) — What a source may be built from at one boundary (§6.8).
- `class PlanPolicy` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 637) — The source and chooser pair.
  - `projection(self) -> 'PlanPolicy'` (line 658; public) — The pair the view projects with: this source, the projection chooser.
- `legacy_source(context: PoolContext) -> BlockSource` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 669)
- `staged_plans_deterministic(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 688) — A staged plan's pool is a fixed function of the vault state: the router composes Today (:func:`learnloop.daily_plan.policy.router_active`: ``mvp-0.23`` or later with ``router.enabled``) and the kill switch ``plan.deterministic_staged_plans`` is on.
- `plan_scheduler_session(vault: Any, session_id: str | None, minutes: float) -> SchedulerSession` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 708) — The scheduler session a plan's pool is built under (every plan build).
- `class PlanEnv` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 762)
  - `now(self) -> datetime` (line 770; public)
  - `now_iso(self) -> str` (line 773; public)
  - `today(self) -> str` (line 776; public)
  - `gap(self) -> ReentryGap` (line 779; public) — The break since the last real activity (§7, F1), sessions left open from an earlier day counting as activity (review F2).
  - `plan_config(self) -> Any` (line 791; public)
  - `build_eligible(self, minutes: float) -> list[Any]` (line 794; public)
- `load_records(repository: Any, plan_ids: Iterable[str] | None=None, *, local_date_value: str | None=None) -> list[PlanRecord]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 811)
- `load_records_from_connection(connection: Any, plan_ids: Iterable[str] | None=None, *, local_date_value: str | None=None) -> list[PlanRecord]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 816) — Fold the persisted plans (all, by id, or one day's) into records.
- `day_records(env: PlanEnv) -> list[PlanRecord]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 834)
- `latest_today(env: PlanEnv) -> PlanRecord | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 838)
- `remembered_minutes(env: PlanEnv) -> tuple[int, str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 851) — Today's default budget (§6.6): the latest plan's remembered minutes; before the first plan, the last session's minutes; on a fresh vault, 25.
- `class PlanBlockDecision` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 872) — One block-boundary decision as router R1 logs it (owner decision 2026-10-12).
- `register_plan_decision_logger(logger: PlanDecisionLogger) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 918) — Router R1's hook: log each plan block decision (DL1 builds no router table).
- `unregister_plan_decision_logger(logger: PlanDecisionLogger) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 925)
- `router_summary(record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 971)
- `intent_view(env: PlanEnv) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1292) — DL2's intent view for this build (None when intent changes nothing).
- `reading_allowed(env: PlanEnv, intent: Any, extraction_id: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1300) — §6.10 by intent (Codex review F7): a reading's source reads under Learn or Master, or uncommitted.
- `get_or_create_today(env: PlanEnv, *, create: bool=True) -> PlanRecord | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1496) — Today's latest plan, building the day's first one when there is none.
- `simulate_blocks(record: PlanRecord, context: PoolContext, policy: PlanPolicy, *, forced: Sequence[PoolItem]=(), max_blocks: int=12) -> list[tuple[Decision, PlannedBlock]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1855) — The blocks the plan would choose next if nothing changed.
- `build_plan(env: PlanEnv, *, kind: str, budget: float, remembered: int, minutes_source: str, parent_plan_id: str | None=None, override: str | None=None) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1957) — Build one plan: classify, admit, split, then choose its first block.
- `day_ad_deferrals(env: PlanEnv, record: PlanRecord | None=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2031) — The day's active AD deferrals (spec §6.1 step 0): every plan of the day, its blocks in creation order (a later plan of the same day starts with them).
- `class Decision` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2240)
- `new_material_candidates(intent: Any, pool: Iterable[PoolItem]) -> list[NewCandidate]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2275) — THE plan's new-material candidates from a pool (§6.3): its never-attempted new-lane items, in intent's admission order (Keep and Light touch add no new material of the system's choosing; requests stay exempt).
- `admitted_new_material_ids(env: PlanEnv, record: PlanRecord, *, scheduled: Sequence[Any], item_states: Mapping[str, Any], released: Iterable[str]=(), unclaimed: Iterable[str]=()) -> frozenset[str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2291) — The plan's admitted pool of new material at this boundary, as ids (the compose fix rounds 2 and 3): ``scheduled`` (the scheduler's queue this advance's build produced, after its per-item predicate and its set-level stages, teach-back value admission and caps among them) classifi…
- `decide(record: PlanRecord, context: PoolContext, policy: PlanPolicy, *, forced_minutes: float=0.0, forced_items: int=0, forced_allotment: Mapping[str, float] | None=None, forced_spent: Mapping[str, float] | None=None) -> Decision` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2474) — §6.8 at one boundary: redistribution, feasibility, choice, fallback.
- `reconcile(env: PlanEnv, record: PlanRecord) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3003) — Fold answers into the plan: done items, unservable items, finished blocks.
- `advance(env: PlanEnv, *, serve: bool, skip_practice_item_id: str | None=None) -> tuple[PlanRecord, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3923) — Reconcile, insert follow-ups, cross a boundary if needed, and name the next step.
- `advance_with_context(env: PlanEnv, *, serve: bool, skip_practice_item_id: str | None=None) -> tuple[PlanRecord, dict[str, Any], PoolContext | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3935)
- `learner_pick(env: PlanEnv, practice_item_id: str, *, offer_candidate_id: str | None=None, idempotency_key: str | None=None, within: WithinPick | None=None) -> tuple[PlanRecord | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4461) — §6.1, L3, G12: opening an item from the full list is a one-item block.
- `picked_under(env: PlanEnv, idempotency_key: str, practice_item_id: str) -> tuple[PlanRecord | None, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4720) — The learner pick already made under ``idempotency_key``, as :func:`learner_pick` returned it: its ORIGINAL block, candidate and presentation, found by its keyed receipt (``PICK_KEYED``) under any plan (today's, or one replaced since).
- `set_minutes(env: PlanEnv, minutes: int) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4772) — A chip tap (§6.6): sets the remembered budget and re-plans the rest.
- `keep_going(env: PlanEnv) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4853) — §6.5: one extension.
- `class PlanStillOpenError(RuntimeError)` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4869) — "More new material" is offered on the done screen: today's plan is still open.
- `more_new(env: PlanEnv, *, confirm: bool) -> tuple[PlanRecord | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4873) — §6.3: "more new material" bypasses the ceiling and the cap once.
- `reading_ended(env: PlanEnv, outcome: str) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4934) — §6.10: end the current reading block; its estimate counts as used.
- `note_reading_progress(env: PlanEnv, *, extraction_id: str, section_id: str, spans_seen: int | None, span_count: int | None, completed: bool) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4949) — ``reader.mark_section_progress`` while a reading block is current (§6.10).
- `stop_today(env: PlanEnv) -> PlanRecord | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4989) — The learner stops for today ("Done" mid-plan).

### Module constants

- `_EPS` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 114)
- `ENGINE_VERSION` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 115)
- `READING_RULE_FURTHEST` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 162)
- `READING_RULE_BOOK_ORDER` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 164)
- `READING_RULE_DL1` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 167)
- `READING_PATH_RECEIPT_VERSION` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 233)
- `READING_PATH_RECEIPT_VERSION_V2` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 237)
- `_INTENT_UNREAD` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 409)
- `DEFAULT_POLICY` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 680)
- `_PLAN_DECISION_LOGGERS` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 915)
- `ROUTER_SUMMARY_KEYS` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 963)
- `CHECK_MINUTES_EXHAUSTED` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1738)
- `CHECK_REFUSED_CANDIDATES` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1740)
- `CHECK_CANDIDATES_HELD` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1743)
- `CHECK_NOT_IN_POOL` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1746)
- `CHECK_NO_CANDIDATES` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1748)
- `NO_CANDIDATES_LINE` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 1750)
- `CHOOSER_CHOSEN_BY` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 2555)
- `WHY_KINDS` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 2556)
- `_AD_UNAVAILABLE` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 4049)
- `_AD_LOG` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 4053)
- `PICK_KEYED` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 4429)
- `READING_OUTCOMES` ([src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py), line 4931)

### Explicit exports

`__all__` declares:

- `DEFAULT_POLICY`
- `Decision`
- `ENGINE_VERSION`
- `EligibleBuilder`
- `PlanBlockDecision`
- `PlanDecisionLogger`
- `PlanEnv`
- `PlanInactiveError`
- `PlanPolicy`
- `PlanStillOpenError`
- `PoolContext`
- `READING_OUTCOMES`
- `READING_RULE_BOOK_ORDER`
- `READING_RULE_DL1`
- `READING_RULE_FURTHEST`
- `advance`
- `advance_with_context`
- `build_plan`
- `day_records`
- `decide`
- `get_or_create_today`
- `keep_going`
- `latest_today`
- `learner_pick`
- `PICK_KEYED`
- `legacy_source`
- `load_records`
- `load_records_from_connection`
- `local_date`
- `more_new`
- `note_reading_progress`
- `plan_active`
- `plan_scheduler_session`
- `reading_from_furthest_active`
- `reading_path_plan_active`
- `reading_step_rule`
- `reading_ended`
- `reconcile`
- `register_plan_decision_logger`
- `remembered_minutes`
- `set_minutes`
- `simulate_blocks`
- `staged_plans_deterministic`
- `stop_today`
- `unregister_plan_decision_logger`
- `deliverable_plan_active`

## Internal implementation anchors

- `_reading_on_path(env: Any, *, extraction_ids: list[str] | None, from_furthest: bool, exam: Any, allowed: Callable[[str], bool] | None=None) -> tuple[ReadingTarget | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 240) — The plan's reading step on a path: curriculum C1's first branch (:func:`_reading_on_deliverable`, with :func:`deliverable_plan_active`), else RW7b's per-book path (:func:`_reading_on_book_path`) unchanged.
- `_same_section(left: Any, right: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 257)
- `_deliverable_choice(env: Any, *, from_furthest: bool, exam: Any, allowed: Callable[[str], bool] | None) -> tuple[Any, list[Any], ReadingTarget | None, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 268) — C1's choice (spec §7.6): the deliverable the plan follows (the nearest active goal among goals with a fresh path, :func:`deliverable_path.plan_deliverable`), every deliverable consulted, and the next unfinished core or prerequisite section in its path's order, in whichever book…
- `_deliverable_entry(followed: Any, consulted: Sequence[Any], step: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 294) — The receipt's ``deliverable`` (spec §7.6): the deliverable followed (else the nearest one in play: stale or unreadable), its path state key and the rows read, the line the step came from, and every deliverable consulted on the way.
- `_reading_on_deliverable(env: Any, rw7b_reading: ReadingTarget | None, rw7b_receipt: dict[str, Any] | None, *, from_furthest: bool, exam: Any, allowed: Callable[[str], bool] | None) -> tuple[ReadingTarget | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 308) — C1's reading step and its v2 receipt.
- `_fresh_reading(env: Any, intent: Any) -> tuple[ReadingTarget | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 347) — The reading step a plan built now would take, with its path receipt: the build's own selection once it considers a reading (:func:`_prepare_plan`).
- `_fresh_reading_checked(env: Any, intent: Any) -> tuple[ReadingTarget | None, dict[str, Any] | None, bool]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 359) — :func:`_fresh_reading` and whether its protection could be read (False: no step, fail closed, and the memo never keeps it: the next read asks again).
- `_read_failed(receipt: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 393) — Whether a path the choice consulted could not be read (``unreadable``: a deliverable, or one of RW7b's per-book paths).
- `_fresh_reading_fingerprint(env: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 412) — The fingerprint of :func:`_fresh_reading`'s inputs (``reading_choice.fingerprint``; fix round 3): the vault database as a whole (any committed write invalidates), the config (a hash of all of it: the switches every branch reads are in it), the vault's goals (each dumped) with ea…
- `_remembered_fresh_reading(env: Any, intent: Any=_INTENT_UNREAD) -> tuple[ReadingTarget | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 446) — :func:`_fresh_reading`, memoized on :func:`_fresh_reading_fingerprint` (Codex review fix round 2, Low 6): C1's invariant re-derives the choice on each read of a C1 plan, and a plain read must not redo the library, coverage and learner-context reads when nothing they depend on ch…
- `_section_progress(repository: Any, reading: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 474) — The staged reading's section progress as it stands (C1's ``staged_progress``): the snapshot :func:`_reading_has_history` compares with, so a section read through the Library since it was staged is history (Codex review fix round 2, Medium 4).
- `_with_staged_progress(repository: Any, reading: Any, receipt: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 492) — A C1 receipt with ``staged_progress`` for the reading it stages (v1 and None unchanged).
- `_reading_on_book_path(env: Any, *, extraction_ids: list[str] | None, from_furthest: bool, exam: Any) -> tuple[ReadingTarget | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 501) — RW7b's reading step and its receipt.
- `_exam_material(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 571) — The one exam predicate (``content.sources.exam_material``, through ``source_retrieval.corpus.exam_exclusions``) for the reading step (UX Phase 1's selection never offers exam material, a ``held_out_evaluation`` unit included, as reading).
- `_reload(env: PlanEnv, plan_id: str) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 843)
- `_log_plan_decision(connection: Any, decision: PlanBlockDecision) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 930) — Hand one decision to the registered loggers; the first id written wins.
- `_event(connection: Any, block_id: str, kind: str, detail: Mapping[str, Any], at: str) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 975)
- `_titles(vault: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 984)
- `_deadlines(vault: Any, repository: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 988) — LOs on an active goal with a due date (§5.4: a deadline is a goal).
- `_estimator(env: PlanEnv) -> Estimator` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1008)
- `class _Pool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1015)
- `_open_problems(env: PlanEnv) -> tuple[frozenset[str] | None, str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1031) — The repair lane's LOs (owner decision 2026-10-12) and the rule used.
- `_select_requests(pool: Sequence[PoolItem], *, budget: float, per_session: int) -> tuple[list[PoolItem], float]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1049) — Requests first (L3): up to ``per_session`` requested items with a lane, in pool order, while their estimates fit the budget; they go in the first block and their minutes come off the budget before the split.
- `_request_candidate(item: PoolItem, lanes_allowed: Sequence[str]) -> PoolItem` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1068) — A pool item as the request rule sees it before the probes are valued.
- `_plan_availability(record: PlanRecord, held: Iterable[str]) -> Callable[[str], str | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1083) — Why a due project probe cannot join this plan on a refresh, or None (Codex review of voi-v2, F10).
- `_usable_probe_minutes(*, minutes: float, reserved: float, lanes_allowed: Sequence[str]) -> float` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1114) — The minutes due project probes are admitted against (final verify F10): the plan's minutes (its budget on a build, its minutes left on a refresh) less what is reserved before the split (the requested items), and none when the plan's lanes exclude maintain, the probes' lane.
- `_classified_pool(env: PlanEnv, *, minutes: float, lanes_allowed: Sequence[str], day: Sequence[PlanRecord], reentry: bool, record: PlanRecord | None=None, minutes_left: float | None=None, scheduled_items: Sequence[Any] | None=None, item_states: Mapping[str, Any] | None=None) -> _Pool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1128) — The scheduler's ranked list, classified into lanes (§6.1).
- `_check_once_checks(intent: Any, item_ids: Sequence[str]) -> dict[str, ScheduledCheck]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1322) — DL2's ``check_once`` provider (``lanes.ScheduledCheck``): the due "Check once" items among the pool, one per check, in pool order.
- `_project_probe_admission(env: PlanEnv, probes_planned: int, *, minutes_budget: float | None=None, preselected: Mapping[str, str] | Sequence[str]=(), availability: Callable[[str], str | None] | None=None) -> Callable[[Sequence[tuple[Any, float]]], list[tuple[str, Mapping[str, Any]]]] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1330) — mvp-0.21 (``voi_stopping``, site ``project_probe``): value today's due project probes instead of counting them; ``None`` keeps the former daily cap.
- `_review_items(env: PlanEnv, estimator: Estimator, intent: Any=None) -> list[ReviewItem]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1438) — The review-load population (§6.3): items with memory state, at their effective due (DL2, §5.3), in non-excluded intents.
- `_streak(env: PlanEnv) -> int` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1475)
- `_reading_used_today(day: Sequence[PlanRecord]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1482)
- `_new_planned_today(day: Sequence[PlanRecord]) -> int` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1487) — New items actually planned today, across plans and extensions (§6.3 cap).
- `class _Prepared` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1521) — A plan classified, admitted and split, not yet persisted.
- `_prepare_plan(env: PlanEnv, *, kind: str, budget: float, remembered: int, minutes_source: str, parent_plan_id: str | None=None, override: str | None=None) -> _Prepared` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1547) — Classify, admit and split one plan (§6.1-§6.3) without persisting it.
- `_check_commitment(intent: Any, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1753)
- `_refused_rows(check: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1758)
- `_select_checks(intent: Any, pool: Sequence[PoolItem], *, budget: float, taken: Iterable[str]) -> tuple[list[PoolItem], float, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1769) — DL2 fix round 4 (R2): the due "Check once" items, in pool order, while their estimates fit ``budget`` (what the requests left).
- `_forced_rows(split: Mapping[str, Any]) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1848) — The first block's forced items as the split recorded them: the requests (L3), then the due checks (R2).
- `_empty_extension(env: PlanEnv, prepared: _Prepared) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 1945) — Whether a prepared extension would plan nothing at all (no request, no feasible block at its first boundary).
- `_config_hash(config: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2016)
- `_context_from_build(env: PlanEnv, record: PlanRecord, built: _Pool) -> PoolContext` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2021)
- `_ad_selection(env: PlanEnv) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2025)
- `_context(env: PlanEnv, record: PlanRecord, built: _Pool, *, day: Sequence[PlanRecord], released: Iterable[str]=(), unclaimed: Iterable[str]=()) -> PoolContext` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2053) — The source's view at one boundary: the plan's universe minus what it took.
- `_routine_holds(env: PlanEnv, item_ids: Sequence[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2126) — The given items held back now by a routine-display hold on their cold check, with when each hold lifts (UX Phase 4 round 7).
- `_waiting_step(env: PlanEnv, record: PlanRecord, context: PoolContext, *, forced_minutes: float=0.0, forced_items: int=0, forced_allotment: Mapping[str, float] | None=None, forced_spent: Mapping[str, float] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2146) — What the plan waits for, or None (UX Phase 4 rounds 7 and 8).
- `_live_context(env: PlanEnv, record: PlanRecord, *, minutes_left: float | None=None) -> tuple[PoolContext, _Pool]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2221)
- `_items_left(record: PlanRecord, *, forced_items: int=0) -> int | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2259)
- `_intents(context: PoolContext) -> dict[str, IntentView]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2266)
- `_intent_admission_order(intent: Any, candidates: Sequence[NewCandidate]) -> list[NewCandidate]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2326) — §6.3 by intent: requests stay exempt and first; then Learn and Master, then uncommitted, each in the scheduler's (Phase 6's) order.
- `_intent_views(env: PlanEnv, built: _Pool, learning_object_ids: Iterable[str]) -> dict[str, IntentView]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2344) — §5: each LO's intent as the chooser may read it (committed LOs only; the rest keep DL1's uncommitted default).
- `class _Feasibility` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2370) — What a boundary may choose from (§6.8): the redistributed state, the source's candidates and the feasible ones, under the plan's minutes left, item allowance and lane rules.
- `_feasibility(record: PlanRecord, context: PoolContext, policy: PlanPolicy, *, forced_minutes: float=0.0, forced_items: int=0, forced_allotment: Mapping[str, float] | None=None, forced_spent: Mapping[str, float] | None=None) -> _Feasibility` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2383) — Redistribution and feasibility at one boundary, before any choice.
- `_malformed_choice(choice: BlockChoice) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2559) — Why a chooser's choice cannot be recorded as given, or None (review F7).
- `_state_row(state: PlanState) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2577)
- `_persist_block(env: PlanEnv, connection: Any, record: PlanRecord, *, lane: str | None, action: str, subtype: str | None, chosen_by: str, est_minutes: float, reading: ReadingTarget | None, reading_full: float | None, learning_object_ids: Sequence[str], detail: Mapping[str, Any], items: Sequence[tuple[PoolItem | PlannedItem, str]], decision_ref: str | None=None, ordinal: int | None=None, releases: Mapping[str, Mapping[str, Any] | None] | None=None, block_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2591)
- `_boundary(env: PlanEnv, record: PlanRecord, context: PoolContext, *, forced: Sequence[PoolItem]=(), forced_origin: str=ORIGIN_REQUESTED, ad_deferrals: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2674) — Choose and persist the next block, or close the plan.
- `_record_probe_value_forecasts(env: PlanEnv, detail: Mapping[str, Any], *, block_id: str, decision_ref: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2871) — mvp-0.21 composed with EVSI calibration: the block decision's due project probe receipts as ``voi_forecasts`` rows, after the block (and router R1's ``plan_block`` row, its ``decision_ref``) committed.
- `_persist_receipt(env: PlanEnv, connection: Any, record: PlanRecord, *, action: str, chosen_by: str, detail: Mapping[str, Any], decision_ref: str | None=None, est_minutes: float=0.0, learning_object_ids: Sequence[str]=(), receipt_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2889) — A plan-level receipt row: a decision that is not one of the plan's numbered blocks (a stop, a pick after the plan closed).
- `_close(env: PlanEnv, record: PlanRecord, *, status: str, reason: str, stop_detail: Mapping[str, Any] | None=None, log_decision: bool=False, router_record: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 2934) — Close the plan.
- `_end_reading_out_of_intent(env: PlanEnv, block: PlannedBlock, intent: Any, now: str, writes: list[tuple[str, str, dict[str, Any]]]) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3136) — DL2 (Codex review F7): a reading block not yet started whose source a later choice took out of reading (Pause, Reference, Let go, Keep, Light touch, "Check once") is ended unread; its minutes are not counted.
- `_path_split_reopens(split: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3152) — Whether a path move reopens a plan that closed for want of its reading: RW7b's ``transition.reopened``, or C1's latest move's.
- `_reading_path_switched_off(env: PlanEnv, record: PlanRecord, now: str, writes: list[tuple[str, str, dict[str, Any]]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3163) — RW7b (Codex review F1): the kill switch reaches a plan already built.
- `_live_reading_blocks(record: PlanRecord) -> list[PlannedBlock]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3228) — The plan's reading blocks that may hold history: every reading block except a path reading taken back unread (:attr:`PlannedBlock.withdrawn_path_reading`: a switch, or C1's fresh choice moving the reading, ended it before it started; C1 Codex review F1).
- `_move_plan_reading(env: PlanEnv, record: PlanRecord, now: str, writes: list[tuple[str, str, dict[str, Any]]], *, to: Any, withdraw: Sequence[PlannedBlock]) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3237) — Give the plan the reading ``to`` (a stored reading or None): each block in ``withdraw`` (unstarted, unended reading blocks; the caller decided there is no history) is ended unread (:data:`READING_PATH_OFF`, no minutes counted; appended to ``writes``), and the split's reading, it…
- `_reading_has_history(env: PlanEnv, record: PlanRecord) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3299) — Whether the plan's reading has reading history (C1's invariant): a live reading block (:func:`_live_reading_blocks`) that started, ended (completed, or ended any other way but DL2's intent ending of an unread block: kept as it is, as RW7b keeps it) or took reading progress (``no…
- `_bounded_moves(receipt: Mapping[str, Any], move: dict[str, Any]) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3325) — A C1 receipt's ``moves`` with ``move`` added, and ``move_count``: bounded by structure, no constant: the first move (from what the build staged) and the latest (where the reading is now); ``move_count`` counts every move.
- `_choice_fields(reading: ReadingTarget | None, receipt: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3335) — The v2 receipt's keys for a fresh choice (spec §7.6): C1's own receipt's where a deliverable path was in play; else RW7b's choice (its v1 receipt in ``rw7b``) or the order's, with ``deliverable`` None.
- `_reading_follows_fresh_choice(env: PlanEnv, record: PlanRecord, now: str, writes: list[tuple[str, str, dict[str, Any]]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3352) — Curriculum C1's one invariant (spec §7.6; Codex review fix round 2): **while the plan's reading block has no reading history, the plan's reading is whatever a fresh build would choose right now.** For a plan whose receipt is C1's (``reading_path_plan_v2``): with reading history…
- `_closed_for_want_of_path_reading(record: PlanRecord) -> bool` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3427) — RW7b (fix round 2): whether a closed plan closed by itself only because its reading path left no reading.
- `_open_cold_check_items(env: PlanEnv) -> frozenset[str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3449) — Items an open cold follow-up task selects (the measurement lanes).
- `_displaceable(record: PlanRecord, keep: Iterable[str]=()) -> list[PlannedItem]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3465) — The plan's tail, latest first: unserved, unresolved planned items.
- `_displacement_plan(record: PlanRecord, *, need_minutes: float, need_items: int, keep: Iterable[str]=()) -> list[PlannedItem] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3483) — The fewest tail items whose displacement frees ``need_minutes`` and ``need_items`` item slots, or None when the tail cannot free both.
- `_followup_release(lefts: Mapping[str, float], minutes_left: float, est: float, *, lane: str, lanes_allowed: Sequence[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3501) — What a follow-up's lane needs from the others to pay for it (review F4).
- `_displace_tail(env: PlanEnv, connection: Any, record: PlanRecord, need: float, *, by: str, keep: set[str]=frozenset()) -> tuple[float, list[str]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3543) — Free ``need`` minutes by displacing the latest unserved planned items.
- `_pending_followups(record: PlanRecord, built: _Pool) -> list[PoolItem]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3574) — Follow-ups produced by this session's answers: not in the plan's universe at build as follow-ups, and not planned yet (§6.1).
- `_insert_followups(env: PlanEnv, record: PlanRecord, built: _Pool) -> tuple[PlanRecord, list[PoolItem]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3587) — Plan mid-plan follow-ups next in the current block, displacing the tail.
- `_place_followup(record: PlanRecord, current: PlannedBlock, item: PoolItem, victims: Sequence[PlannedItem], *, position: int, now: str) -> tuple[str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3687) — Apply one follow-up's placement to the in-memory plan (its victims displaced, the follow-up appended to the current block); returns its lane and its lane release.
- `_write_followup(connection: Any, current: PlannedBlock, item: PoolItem, victims: Sequence[PlannedItem], *, lane: str, release: dict[str, Any] | None, position: int, decision_ref: str | None, now: str) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3711) — The events of one placed follow-up: its victims' displacement, then its ``item_planned``.
- `_restrained_followups(env: PlanEnv, record: PlanRecord, current: PlannedBlock, followups: Sequence[PoolItem], gate: Any, cap: Any) -> tuple[PlanRecord, list[PoolItem]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3746) — Router R2c: each placeable mid-block follow-up's ``plan_interrupt`` decision.
- `_log_interrupt(env: PlanEnv, connection: Any, record: PlanRecord, current: PlannedBlock, item: PoolItem, outcome: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3822) — Router R2c: the follow-up's ``plan_interrupt`` row, on the write's own connection.
- `_item_step(env: PlanEnv, record: PlanRecord, block: PlannedBlock, item: PlannedItem, *, boundary: bool, candidate_id: str | None, presentation_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3866)
- `_reading_step(env: PlanEnv, record: PlanRecord, block: PlannedBlock, *, boundary: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3897)
- `_done_step(record: PlanRecord) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 3919)
- `_code(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4056) — An AD failure's code (its only argument), never its text beyond that.
- `_ad_phase(run: Any, where: str) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4064) — An AD phase (``ad_slot``): its result, or None when AD is unavailable (logged with its code).
- `_incumbent_facts(run: Any, where: str) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4078) — Phase 2: the plan's own facts, or None.
- `_ad_deferrals_cleared(env: PlanEnv, record: PlanRecord, built: _Pool, active: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4096) — §6.1 step 0 by the four phases: the AD deferrals whose checks all pass now, each a member of the plan's admitted pool were it released; none on any failure (nothing re-admitted).
- `_ad_slot_serve(env: PlanEnv, record: PlanRecord, block: PlannedBlock, item: PlannedItem, built: _Pool, context: PoolContext, *, boundary: bool) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4127) — Adaptive difficulty AD2+AD3 (spec §6.1): the slot's support, AD's draw, its ``ad_selections`` row, any ``item_substituted`` event and ``item_served``, in one transaction (a propensity is never recomputed after the draw).
- `_held_cold_check(env: PlanEnv, block: PlannedBlock, item: PlannedItem) -> tuple[bool, Any]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4213) — Revalidate a cold check at the moment the plan would serve it (the one eligibility decision, ``scheduler.cold_check_serve_decision``): one whose hold time clears (a routine display, a reveal since it was scheduled) is displaced, with the reason; one submit would prime with no la…
- `_standing_presentation(env: PlanEnv, block: PlannedBlock, item: PlannedItem) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4239) — The presentation an already-served plan item was served under, if any.
- `_present(env: PlanEnv, connection: Any, *, block_id: str, decision_ref: str | None, practice_item_id: str, position: int | None, origin: str, candidate_id: str | None, served_at: str, strict: bool=False) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4254) — Router R2a: the served item's ``plan_presentations`` row, in the serve's own transaction (one per block and item: a reopen returns the first).
- `_serve(env: PlanEnv, block: PlannedBlock, item: PlannedItem, *, candidate_id: str | None, strict: bool=False) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4325) — Record the item as served; returns its presentation (router R2a).
- `_skip(env: PlanEnv, record: PlanRecord, practice_item_id: str) -> PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4383)
- `_offered_candidate(env: PlanEnv, candidate_id: str | None, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4398) — The full list's offer for this item, when ``candidate_id`` is one (F5).
- `_keyed_pick_scope(env: PlanEnv, idempotency_key: str | None) -> Any` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4436) — A keyed pick's one transaction (fix round 6, F13): the block, the serve, the keyed receipt and the caller's ``within`` commit together or not at all, so no reserved-but-unserved pick can exist.
- `_record_pick_key(env: PlanEnv, connection: Any, *, block_id: str, practice_item_id: str, presentation_id: str | None, idempotency_key: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4447) — The keyed receipt, only ever with the presentation it names (fix round 7): a keyed pick without one refuses, and its transaction rolls back.
- `_pick_new_block(env: PlanEnv, record: PlanRecord, item: PoolItem, *, practice_item_id: str, est: float, lane: str | None, lo_id: str, deductions: dict[str, float], lefts: Mapping[str, float], candidate_id: str | None, idempotency_key: str | None, within: WithinPick | None) -> tuple[PlanRecord, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/engine.py), line 4631) — The one-item learner-pick block (L3): its block, its serve and, for a keyed pick, its keyed receipt and ``within`` (one transaction then).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]] — imports `load_records_from_connection`, `local_date`, `plan_active`; statically calls `load_records_from_connection`, `local_date`, `plan_active`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `PlanEnv`, `latest_today`; statically calls `PlanEnv`, `latest_today`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `DEFAULT_POLICY`, `PlanPolicy`, `plan_active`; statically calls `PlanPolicy`, `plan_active`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `admitted_new_material_ids`; statically calls `admitted_new_material_ids`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `PlanEnv`, `PlanPolicy`, `PoolContext`, `day_records`, `simulate_blocks`; statically calls `day_records`, `simulate_blocks`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `load_records`; statically calls `load_records`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `PlanEnv`, `load_records`, `plan_active`; statically calls `PlanEnv`, `load_records`, `plan_active`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `PlanEnv`, `PlanInactiveError`, `PlanStillOpenError`, `advance_with_context`, `intent_view`, `keep_going`, `latest_today`, `learner_pick`, `more_new`, `picked_under`, `plan_active`, `plan_scheduler_session`, `reading_ended`, `set_minutes`, `stop_today`; statically calls `PlanEnv`, `advance_with_context`, `intent_view`, `keep_going`, `latest_today`, `learner_pick`, `more_new`, `picked_under`, `plan_active`, `plan_scheduler_session`, `reading_ended`, `set_minutes`, `stop_today`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `deliverable_plan_active`, `local_date`; statically calls `deliverable_plan_active`, `local_date`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `local_date`; statically calls `local_date`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `plan_active`; statically calls `plan_active`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `PlanEnv`, `note_reading_progress`; statically calls `PlanEnv`, `note_reading_progress`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `module`; calls `record_plan_serve`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `slot_applies`; calls `slot_applies`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `selection_on`; calls `selection_on`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DAILY_PLAN_VERSIONS`, `DELIVERABLE_PLAN_VERSIONS`, `READING_PATH_PLAN_VERSIONS`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `split_grading_active`; calls `split_grading_active`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_selection_active`; calls `held_out_selection_active`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `module`; calls `decide`, `deferrals_cleared`, `open_deferrals`, `open_slot`
- [[Reference/Modules/learnloop/daily_plan/admission|learnloop.daily_plan.admission]] — imports `NewCandidate`, `ReviewItem`, `admit_new_material`, `more_new_tradeoff`, `projected_review_load`; calls `NewCandidate`, `ReviewItem`, `admit_new_material`, `more_new_tradeoff`, `projected_review_load`
- [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]] — imports `CHOOSER_NAME`, `LaneQuotaChooser`; calls `LaneQuotaChooser`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/lanes|learnloop.daily_plan.lanes]] — imports `LegacyLanesSource`, `PoolItem`, `REPAIR_RULE_DIAGNOSIS`, `REPAIR_RULE_RECENT_ERROR`, `SOURCE_NAME`, `ScheduledCheck`, `classify_pool`, `reentry_order`, `scheduled_checks`; calls `LegacyLanesSource`, `PoolItem`, `ScheduledCheck`, `classify_pool`, `reentry_order`, `scheduled_checks`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `router_active`; calls `router_active`
- [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]] — imports `as_you_read_extraction_ids`, `next_listed_reading_target`, `next_reading_target`, `section_start_span`; calls `as_you_read_extraction_ids`, `next_listed_reading_target`, `next_reading_target`, `section_start_span`
- [[Reference/Modules/learnloop/daily_plan/reading_choice|learnloop.daily_plan.reading_choice]] — imports `module`; calls `fingerprint`, `recall`, `remember`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `AD_INELIGIBLE`, `DELIVERABLE_PATH_MOVED`, `DELIVERABLE_PATH_OFF`, `ORIGIN_CHOOSER`, `ORIGIN_FOLLOWUP`, `ORIGIN_LEARNER_PICK`, `ORIGIN_REQUESTED`, `PlanRecord`, `PlannedBlock`, `PlannedItem`, `READING_PATH_OFF`, `RECEIPT_OPEN_LIST_PICK`, `RECEIPT_STOP`, `assemble`; calls `PlanRecord`, `PlannedBlock`, `PlannedItem`, `assemble`
- [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]] — imports `ReentryGap`, `reentry_gap`; calls `ReentryGap`, `reentry_gap`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `FACTS_FAILED`, `module`; calls `accept`, `accept_cleared`, `for_deferrals`, `for_slot`
- [[Reference/Modules/learnloop/daily_plan/slot_facts_schema|learnloop.daily_plan.slot_facts_schema]] — imports `encode`; calls `encode`
- [[Reference/Modules/learnloop/daily_plan/split|learnloop.daily_plan.split]] — imports `redistribute`, `split_v1`; calls `redistribute`, `split_v1`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `AFTER_REENTRY_LANE_PRIORITY`, `BLOCK_MAX_MINUTES`, `BlockCandidate`, `BlockChoice`, `BlockChooser`, `BlockSource`, `CONTINUE_CURRENT`, `DecisionPending`, `IntentView`, `LANES`, `LANE_ACTIONS`, `PICK_DEDUCTION_ORDER`, `PlanState`, `REENTRY_LANES`, `ReadingTarget`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; calls `BlockChoice`, `IntentView`, `PlanState`, `ReadingTarget`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `abandon_open_plans_before`, `all_plans`, `append_block_event`, `block_events_for`, `daily_plan_tables_present`, `insert_plan`, `insert_plan_block`, `latest_plan`, `open_diagnosed_problem_learning_object_ids`, `plan_blocks`, `plan_by_id`, `plans_for_date`, `update_plan`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `module`; calls `insert_plan_presentation`, `plan_presentations_present`, `presentation_by_id`, `presentation_for`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `module`; calls `InformationEntry`, `MinutesEstimate`, `VoiContext`, `greedy_information_admission`, `not_in_plan_receipt`, `record_plan_value_forecasts`, `voi_stopping_active`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `diagnosis_waits_run_out`; calls `diagnosis_waits_run_out`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `source_learning_objects`; calls `source_learning_objects`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `log_plan_block_decision`, `log_plan_interrupt_decision`; calls `log_plan_interrupt_decision`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CHOICE_PRESET`, `TIER_KEEP`, `TIER_LIGHT`, `TIER_PUSH`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`, `build_due_queue`, `cold_check_hold_until`, `cold_check_serve_decision`, `cold_check_serve_hold`; calls `SchedulerSession`, `build_due_queue`, `cold_check_hold_until`, `cold_check_serve_decision`, `cold_check_serve_hold`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `exam_exclusions`; calls `exam_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `plan_deliverable`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; calls `PlanPath`, `plan_path`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_servable`; calls `practice_item_servable`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `copy`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/daily_plan_fakes.py](../../../../../../tests/daily_plan_fakes.py) — direct import
- [tests/router_mixture_helpers.py](../../../../../../tests/router_mixture_helpers.py) — direct import
- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_with_selection_off_the_projection_offers_a_once_deferred_item`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_ad_selection_withholds_held_out_material_with_held_out_selection_off`
  - `test_an_attempt_on_held_out_material_warms_nothing_and_is_invisible_to_the_replay`
  - `test_an_unreadable_predicate_makes_ad_unavailable_and_the_incumbent_serves`
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
  - `test_the_challengers_history_never_reads_a_withheld_items_answer`
  - `test_z_v1_calibration_never_reads_a_withheld_items_forecast`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_draw_reads_reading_recorded_since_the_last_serve`
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_f1_a_commitment_never_turns_the_slot_draw_off`
  - `test_f2_ad_never_serves_an_item_intent_withholds`
  - `test_property_ad_never_serves_or_clears_what_the_incumbent_withholds`
  - `test_the_incumbent_hands_ad_only_verdicts`
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_a_sentinel_the_plan_plants_never_reaches_ad`
  - `test_high1_a_malformed_stored_context_quoting_held_out_text_never_reaches_ad_or_the_log`
  - `test_property_a_buggy_deciders_pick_outside_the_facts_is_rolled_back`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
- [tests/test_ad23_pool_membership.py](../../../../../../tests/test_ad23_pool_membership.py) — direct import
  - `test_h_a_due_check_once_leaves_ad_drawing`
  - `test_m1_keep_and_light_touch_siblings_get_no_new_material_from_ad`
  - `test_m2_a_sibling_the_build_left_out_never_returns`
  - `test_property_every_ad_choice_is_a_member_of_the_plans_admitted_pool`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_ad_never_writes_evidence`
  - `test_overclaimed_features_do_not_lower_demand_estimate`
  - `test_pre_exposed_presentation_excluded_from_update_and_scoring`
  - `test_unknown_hint_timing_through_the_replay`
  - `test_warmth_uses_only_pre_serve_exposures`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_coordination_requires_envelope`
  - `test_deferral_readmits_after_the_reveal_window`
  - `test_deferral_switch_off_serves_the_item`
  - `test_draw_after_block_choice_with_pair_propensity`
  - `test_empty_support_makes_no_draw_and_displaces`
  - `test_exam_reserved_and_retired_items_never_selected`
  - `test_ineligible_displacement_defers_until_condition_clears`
  - `test_item_over_block_budget_not_in_support`
  - `test_joint_propensity_logged_with_router_block`
  - `test_propensity_recomputes_from_logged_row`
  - `test_serve_propensity_is_over_existing_items`
  - `test_support_rechecked_at_draw_slot_item_included`
  - `test_support_respects_constraints_reversibility_and_admission`
  - `test_switch_off_serves_the_planned_item_whatever_changed`
  - `test_why_this_item_names_the_draw_that_chose_it`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_coupling_is_prediction_only`
  - `test_shadow_report_names_what_a_new_version_reinterprets`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_forecast_receipt_written_in_serve_transaction`
  - `test_item_only_forecast_enters_inputs_only_if_received_before_serve`
- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
  - `test_a_candidate_larger_than_its_lanes_minutes_is_never_offered`
  - `test_a_candidate_larger_than_the_minutes_left_is_never_offered`
  - `test_a_valid_router_choice_is_kept_with_its_propensity`
  - `test_every_decision_is_logged_with_its_candidate_set`
  - `test_lane_quota_prefers_the_largest_unspent_share_then_repair_first`
  - `test_released_minutes_follow_the_flow_on_order`
  - `test_stopping_is_only_allowed_when_offered`
  - `test_unknown_ids_and_continue_at_a_boundary_fall_back_and_are_flagged`
- [tests/test_curriculum_c1_codex_review_fixes.py](../../../../../../tests/test_curriculum_c1_codex_review_fixes.py) — direct import
  - `test_f1_after_a_refresh_withdrew_the_staged_reading_the_switch_still_restores_rw7bs`
  - `test_f2_c1_back_on_moves_the_unread_reading_back_to_c1s_choice`
  - `test_f3_without_a_new_judgment_the_stale_plan_stays_and_reads_no_path`
- [tests/test_curriculum_c1_fix_round2.py](../../../../../../tests/test_curriculum_c1_fix_round2.py) — direct import
  - `test_l6_a_choice_made_while_a_read_failed_is_never_kept`
  - `test_l6_a_memo_hit_returns_exactly_what_the_choice_computed`
  - `test_l6_a_path_stale_after_its_refresh_is_not_chosen_afresh_on_every_read`
  - `test_l6_the_fingerprint_moves_with_a_judgment_a_switch_and_the_date`
- [tests/test_curriculum_c1_fix_round3.py](../../../../../../tests/test_curriculum_c1_fix_round3.py) — direct import
  - `test_m2_a_diagnosis_wait_running_out_invalidates_with_no_write`
  - `test_m2_a_write_from_another_connection_makes_the_next_read_choose_again`
  - `test_m2_a_write_to_the_diagnosis_or_job_rows_alone_invalidates`
  - `test_m2_the_memo_is_one_database_and_its_watcher_is_closed_on_forget`
  - `test_m2_the_plan_read_writes_nothing_when_nothing_moves_so_the_memo_hits`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m1_the_deadline_input_moves_strictly_after_the_deadline`
  - `test_m2_a_shadow_job_before_the_live_one_never_stands_for_its_deadline`
  - `test_m3_a_database_restored_at_the_same_path_is_watched_as_the_new_file`
  - `test_m3_a_vanished_database_is_never_trusted`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_reading_block_opens_the_paths_first_unfinished_section_and_the_receipt_names_rw7bs`
  - `test_the_receipts_predecessor_is_rw7bs_choice_with_its_own_receipt_kept`
  - `test_the_switch_is_on_by_default_classified_and_needs_the_curriculum_and_rw7b`
- [tests/test_curriculum_c1_round5_followups.py](../../../../../../tests/test_curriculum_c1_round5_followups.py) — direct import
- [tests/test_daily_plan_build.py](../../../../../../tests/test_daily_plan_build.py) — direct import
  - `test_a_3_5_minute_item_is_served_with_4_minutes_left`
  - `test_a_learner_pick_is_logged_without_propensity_and_displaces_the_tail`
  - `test_decide_is_pure`
  - `test_decisions_happen_at_block_boundaries_only`
  - `test_engine_rejects_work_while_the_plan_is_off`
  - `test_items_that_appear_mid_plan_do_not_join_it`
  - `test_mid_plan_followups_displace_the_tail_and_never_grow_the_plan`
  - `test_opening_a_planned_item_from_the_list_serves_it_without_a_new_block`
  - `test_project_probes_stay_outside_the_new_item_cap`
  - `test_requested_items_go_first_and_are_deducted_before_the_split`
  - `test_the_plan_never_exceeds_its_budget_or_a_lanes_allotment`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
  - `test_a_tutor_reveal_during_a_plan_item_leaves_the_item_flow_alone`
- [tests/test_daily_plan_kill_switch.py](../../../../../../tests/test_daily_plan_kill_switch.py) — direct import
  - `test_new_admission_switch_admits_no_system_chosen_new_material`
  - `test_plan_off_rows_serve_the_open_queue_whatever_the_router`
  - `test_plan_on_router_off_is_dl1s_deterministic_pair`
  - `test_plan_on_router_on_keeps_the_containers_invariants`
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_plan_served_attempts_have_the_daily_plan_serving_kind`
  - `test_reentry_stays_short_and_keep_going_leads_with_new_material`
  - `test_repair_falls_back_to_recent_error_only_while_the_split_is_off`
  - `test_repair_is_an_open_diagnosed_problem_not_a_recent_error`
  - `test_router_r1_logs_plan_block_decisions_through_the_boundary_hook`
- [tests/test_daily_plan_reentry.py](../../../../../../tests/test_daily_plan_reentry.py) — direct import
  - `test_no_reentry_within_the_gap`
  - `test_reentry_needs_no_goal_and_respects_its_minute_and_item_caps`
- [tests/test_daily_plan_replay.py](../../../../../../tests/test_daily_plan_replay.py) — direct import
  - `test_a_plan_runs_on_a_fresh_wal_vault`
  - `test_rebuild_ignores_the_plan_and_calls_no_model`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f10_a_crash_before_the_first_block_keeps_requests_first`
  - `test_f10_a_pick_after_the_plan_closed_is_recorded`
  - `test_f10_keep_going_with_nothing_left_is_idempotent`
  - `test_f10_more_new_on_an_open_plan_is_refused_and_keeps_the_plan`
  - `test_f11_a_followup_already_in_the_universe_is_forced_once`
  - `test_f11_a_requested_due_item_is_planned_once_and_served_to_the_end`
  - `test_f11_simulated_blocks_plan_a_forced_request_once`
  - `test_f11_the_crash_recovery_boundary_plans_a_request_once`
  - `test_f12_a_pick_after_the_plan_closed_adds_no_feedback_dwell`
  - `test_f13_a_pick_ignores_a_used_or_unshown_offer`
  - `test_f1_admission_off_serves_no_never_attempted_item`
  - `test_f1_an_open_diagnosis_repairs_the_failed_item_and_the_unseen_one_is_new`
  - `test_f1_reentry_never_plans_an_unseen_sibling_of_an_old_error`
  - `test_f2_a_stale_session_without_attempts_counts_from_its_start`
  - `test_f2_practice_in_a_session_left_open_yesterday_is_not_a_break`
  - `test_f2_the_break_still_shows_when_the_only_open_session_began_today`
  - `test_f3_plan_reads_never_call_the_live_chooser`
  - `test_f4_a_followup_that_cannot_fit_is_declined_not_appended`
  - `test_f4_followups_keep_a_reentry_plan_within_its_item_cap_and_lanes`
  - `test_f6_a_reopened_plan_that_stops_again_keeps_both_stop_receipts`
  - `test_f6_a_router_stop_keeps_its_propensity_and_candidates`
  - `test_f7_malformed_choices_fall_back_and_are_flagged`
  - `test_f9_extensions_hold_the_review_load_to_the_days_budget`
  - `test_f9_more_new_preview_is_what_confirming_plans`
  - `test_n1_an_item_whose_estimate_is_its_lanes_whole_load_is_planned`
- [tests/test_daily_plan_rpc.py](../../../../../../tests/test_daily_plan_rpc.py) — direct import
  - `test_g3_every_shown_number_is_what_the_plan_serves`
- [tests/test_dl2_rw4b_keyed_pick_check.py](../../../../../../tests/test_dl2_rw4b_keyed_pick_check.py) — direct import
  - `test_a_keyed_pick_of_a_due_check_the_plan_does_not_hold_is_a_one_item_block_and_answers_it`
  - `test_a_keyed_pick_of_a_planned_due_check_serves_the_check_once_and_its_answer_satisfies_it`
  - `test_a_keyed_pick_of_an_item_a_waiting_check_holds_is_served_and_answers_nothing`
- [tests/test_evsi_staged_binding.py](../../../../../../tests/test_evsi_staged_binding.py) — direct import
  - `test_a_committed_staged_forecast_joins_the_attempt_bound_to_its_presentation`
  - `test_an_unbound_attempt_on_the_chosen_item_is_never_the_forecasts_outcome`
- [tests/test_exam_protection_landing.py](../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_the_open_items_are_the_plan_records_own`
  - `test_v2_todays_read_never_retries_a_plan_wait`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_below_the_tag_commitments_change_nothing_with_the_switch_on`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f1_a_check_once_chosen_after_the_plan_holds_its_planned_item`
  - `test_f1_pausing_after_the_plan_was_built_keeps_its_items_unserved`
  - `test_f2_with_intent_off_commitments_change_nothing_in_the_ranked_list_or_the_plan`
  - `test_f3_an_exposure_after_planning_is_read_at_the_serve`
  - `test_f3_an_lo_check_planned_item_exposed_after_planning_is_displaced`
  - `test_f5_a_primed_retry_changes_neither_the_cost_preview_nor_the_review_load`
  - `test_f7_a_pause_after_the_plan_drops_its_pending_reading`
  - `test_f7_a_source_reads_only_under_learn_or_master`
- [tests/test_intent_exclusion.py](../../../../../../tests/test_intent_exclusion.py) — direct import
  - `test_excluded_items_are_left_out_of_the_review_load`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f14_a_check_the_minutes_cannot_hold_is_recorded_not_silent`
  - `test_f14_a_due_check_is_planned_first_within_the_minutes`
  - `test_f14_contract_a_due_check_is_planned_within_n_builds_or_every_miss_says_minutes`
- [tests/test_intent_fix_round5.py](../../../../../../tests/test_intent_fix_round5.py) — direct import
  - `test_f16_a_reservation_taken_after_planning_displaces_the_planned_check`
  - `test_f16_contract_no_reserved_item_is_ever_planned_and_every_miss_is_named`
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_intent_goal_deadline.py](../../../../../../tests/test_intent_goal_deadline.py) — direct import
  - `test_a_deadline_creates_a_learner_goal_linked_by_goal_id`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_a_due_check_is_a_maintain_lane_scheduled_check_not_a_request`
  - `test_a_waiting_check_and_a_pause_keep_their_items_out_of_the_plan`
  - `test_admission_takes_learn_first_and_keep_adds_no_new_material`
  - `test_an_assumed_lo_with_no_commitment_reads_as_keep_for_its_check`
  - `test_committed_los_reach_the_chooser_state_with_their_intent`
  - `test_learn_and_master_feed_push_with_items_not_yet_due`
  - `test_reentry_leaves_light_touch_out_and_orders_by_intent_tier`
  - `test_several_checks_due_on_one_day_are_bounded_by_the_minutes_not_a_count`
  - `test_with_no_commitment_the_plan_build_equals_intent_off`
- [tests/test_learner_pick_proposal.py](../../../../../../tests/test_learner_pick_proposal.py) — direct import
  - `test_the_delivery_carries_the_exact_decision_of_the_block_that_served_it`
- [tests/test_mcp_c1a_narrow.py](../../../../../../tests/test_mcp_c1a_narrow.py) — direct import
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_today_shows_the_stored_plan_and_writes_nothing`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_upgrade_from_mvp024_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_new_vaults_serve_the_plan`
  - `test_the_plan_serves_only_at_the_successor_with_the_switch_on`
  - `test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_that_admits_probe_ties`
  - `test_upgrade_from_mvp014_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_sooner_checks`
  - `test_upgrade_from_mvp015_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_upgrade_from_mvp016_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_each_version_keeps_its_predecessors_and_grades_as_mvp016`
  - `test_upgrade_from_mvp017_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_upgrade_from_mvp019_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_the_router_serves_only_at_the_successor_with_its_switch_on`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_the_mixture_serves_only_at_the_successor_in_mixture_mode`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_replay_never_reads_the_switch`
  - `test_the_plans_scheduler_session_is_greedy_only_where_the_router_composes_today`
  - `test_the_switch_acts_only_where_the_router_composes_today`
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
  - `test_different_seeds_still_draw_different_blocks_and_the_switch_leaves_the_draw_alone`
  - `test_staged_plans_at_mvp024_are_the_same_in_every_session_and_at_start`
  - `test_the_mixture_draws_over_the_same_candidates_in_every_session`
  - `test_the_plans_scheduler_session_at_mvp024`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_path_never_opens_a_held_out_section_even_where_dl1s_exact_selection_would`
  - `test_the_reading_block_opens_the_next_core_or_prerequisite_section_and_the_receipt_has_the_old_one`
  - `test_the_switch_is_on_by_default_classified_and_acts_only_at_the_tag_with_the_guide_on`
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
  - `test_a_pick_made_under_a_key_is_made_once`
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f13_a_failure_after_the_block_and_before_the_serve_leaves_nothing_and_the_retry_makes_all_once`
  - `test_f13_an_unkeyed_pick_keeps_its_own_transactions`
  - `test_f2_a_keyed_pick_of_a_planned_item_is_found_under_a_later_plan`
  - `test_r7_a_keyed_receipt_is_never_written_without_its_presentation`
  - `test_r7_an_open_list_keyed_pick_also_rolls_back_and_an_unkeyed_one_still_serves`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
  - `test_i_a_narrative_write_invalidates_c1s_memo_once_and_the_choice_is_the_same`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_new_vaults_read_on_from_the_furthest_section`
  - `test_replay_never_reads_the_switch`
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
- [tests/test_router_card.py](../../../../../../tests/test_router_card.py) — direct import
  - `test_g5_no_reference_reserved_stem_exam_text_or_held_score_reaches_the_card`
  - `test_payloads_older_than_the_retention_window_are_pruned`
  - `test_router_card_prints_a_decisions_stored_card`
  - `test_the_card_is_deterministic_for_the_same_ledger_and_instant`
  - `test_the_exam_predicate_failing_withholds_every_question_and_answer`
- [tests/test_router_g1_feasibility.py](../../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back`
  - `test_a_reserved_assessment_surface_is_refused_on_today`
  - `test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame`
  - `test_a_snapshot_failure_fails_closed_only_where_a_constraint_cannot_be_established`
  - `test_an_annotation_failure_keeps_every_refusal`
  - `test_an_unseen_probe_stays_in_the_plan`
  - `test_the_staged_frame_keeps_refusals_through_the_projection`
  - `test_without_the_constraints_inputs_every_item_is_refused`
- [tests/test_router_g4_restraint.py](../../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_a_follow_up_a_hard_constraint_refuses_is_declined_by_name`
  - `test_a_follow_up_joins_the_current_block_today_and_waits_with_a_decider_near_zero`
  - `test_a_follow_up_that_waiting_would_drop_joins_now`
  - `test_a_refused_follow_up_is_never_forced_into_the_next_block`
  - `test_a_waiting_follow_up_keeps_its_room_until_the_boundary`
  - `test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation`
  - `test_competing_follow_ups_log_only_the_insertions_that_happen`
  - `test_the_models_never_force_a_follow_up_the_rules_would_not_place`
  - `test_when_the_models_agree_to_interrupt_the_follow_up_joins_with_its_decision`
  - `test_with_no_model_set_up_a_placeable_follow_up_joins_deterministically`
  - `test_with_the_restraint_off_a_follow_up_joins_as_in_r2b`
- [tests/test_router_g7_fallback.py](../../../../../../tests/test_router_g7_fallback.py) — direct import
  - `test_a_timeout_reaches_the_staged_rule_with_fallback_llm`
  - `test_an_error_or_an_invalid_answer_falls_back`
- [tests/test_router_presentations.py](../../../../../../tests/test_router_presentations.py) — direct import
  - `test_a_learner_pick_and_an_open_list_pick_get_their_own_presentations`
  - `test_a_served_item_writes_one_presentation_with_its_block_and_decision`
  - `test_an_attempt_after_a_skip_binds_by_presentation_not_the_session_rule`
  - `test_presentations_are_append_only`
  - `test_the_session_rule_never_takes_an_attempt_bound_to_another_presentation`
  - `test_the_session_rule_stays_the_labelled_fallback_for_an_unbound_attempt`
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
  - `test_a_chooser_stop_is_a_stop_for_today_plan_block`
  - `test_a_choosers_own_decision_id_is_kept_and_not_logged_twice`
  - `test_a_malformed_choosers_fallback_block_gets_r1s_id`
  - `test_a_refused_plan_row_never_blocks_the_plan`
  - `test_router_logging_off_writes_no_plan_block_and_leaves_decision_ref_unset`
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_a_learner_pick_wins_with_no_propensity_and_logs_its_own_decision`
  - `test_an_irreversible_block_is_only_the_rules_deterministic_pick`
  - `test_presentations_and_cards_survive_production_pragmas`
  - `test_with_nothing_refused_the_staged_frame_serves_dl1s_blocks_in_dl1s_order`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_drawn_llm_pick_shows_its_rationale_and_its_cited_answers`
  - `test_a_json_repair_is_admitted_as_its_own_request`
  - `test_a_learner_pick_under_the_mixture_has_no_propensity`
  - `test_a_serve_waits_at_most_the_timeout_then_the_rule_takes_both_shares`
  - `test_an_unfinished_request_keeps_its_reservation_after_a_restart`
  - `test_with_no_model_set_up_the_rule_chooses_deterministically`
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
- [tests/test_router_r2c_teach_back.py](../../../../../../tests/test_router_r2c_teach_back.py) — direct import
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_an_unreadable_section_is_named_in_the_unknowns`
  - `test_the_plan_stores_the_card_with_its_reader_section`
  - `test_the_router_reads_the_section_and_the_kill_switch_restores_the_predecessor`
- [tests/test_router_why_copy.py](../../../../../../tests/test_router_why_copy.py) — direct import
  - `test_every_why_the_staged_chooser_writes_on_a_plan_is_plain`
- [tests/test_rw7b_codex_review_fixes.py](../../../../../../tests/test_rw7b_codex_review_fixes.py) — direct import
  - `test_f1_a_staged_unstarted_path_reading_is_ended_unread_and_the_predecessors_is_served`
  - `test_f1_switching_off_after_the_build_restores_the_predecessors_reading`
  - `test_f2_a_goal_change_invalidates_an_enrichment_judgment`
- [tests/test_rw7b_fix_round2.py](../../../../../../tests/test_rw7b_fix_round2.py) — direct import
  - `test_a_withdrawn_path_reading_leaves_the_predecessors_reading_in_the_projection`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_12_9_reproduction_is_served_as_practice_and_its_check_withdrawn`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_the_plan_serves_the_12_9_case_as_mvp_026_with_the_switch_off`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_todays_plan_is_byte_identical_with_a_suggestion_drawn`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1j_a_planned_cold_check_revealed_before_it_is_served_is_not_served`
  - `test_f1j_no_serve_path_serves_a_cold_check_submit_would_prime`
  - `test_f1k_a_non_routine_reveal_never_starves_the_plan`
  - `test_f1k_a_routine_display_hold_clears_by_itself`
  - `test_f1l_a_hold_that_lifts_after_today_finishes_the_plan_as_before`
  - `test_f1l_a_hold_that_lifts_today_waits_instead_of_finishing_the_plan`
  - `test_f1m_a_plan_waits_when_coverage_is_the_only_obstacle_then_serves_it`
  - `test_f1m_a_plan_with_no_minutes_left_finishes_instead_of_waiting`
  - `test_f1m_a_reentry_plan_with_no_item_slots_left_finishes_instead_of_waiting`
  - `test_f1m_a_valid_stop_with_work_feasible_is_kept`
  - `test_f1m_back_in_n_min_is_never_promised_for_an_item_that_will_not_fit`
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_waiting_plan_writes_nothing_and_the_served_item_binds_its_presentation`
  - `test_under_the_router_mixture_a_drawn_stop_stays_a_logged_stop_beside_a_lifting_hold`
  - `test_under_the_router_mixture_a_waiting_plan_asks_no_model_and_logs_no_decision`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_the_report_scores_a_project_probe_through_r1s_plan_block`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_minutes_change_values_probes_against_the_new_minutes_left`
  - `test_a_probe_outside_the_plans_universe_does_not_suppress_one_inside`
  - `test_a_refresh_admits_against_the_minutes_left_and_conditions_on_planned_probes`
  - `test_a_skipped_probe_does_not_suppress_its_alternative_on_refresh`
  - `test_requested_probes_and_requests_share_one_request_rule`
  - `test_the_usable_minutes_are_what_the_requests_and_lanes_leave`

## Modification guidance

- Make changes here when the responsibility remains engine within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/engine.py](../../../../../../src/learnloop/daily_plan/engine.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
