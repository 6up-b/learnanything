---
title: "learnloop.daily_plan.lanes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/lanes.py"
source_paths:
  - "src/learnloop/daily_plan/lanes.py"
source_commit: "49712bc6f1aa4fddf6356dd784057178faa27f9a"
source_commit_timestamp: "2026-10-25T11:47:25-04:00"
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
  - "learnloop.daily_plan.lanes module"
  - "src/learnloop/daily_plan/lanes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.lanes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.lanes` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Lanes (``spec_daily_loop_v1.md`` §6.1) and the ``legacy_lanes_v1`` source (§6.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py) |
| Source lines | 666 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `49712bc6f1aa4fddf6356dd784057178faa27f9a` |
| Commit timestamp | `2026-10-25T11:47:25-04:00` |

## Public API

- `class ScheduledCheck` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 86) — A fixed-date cold check the plan serves in the maintain lane (§6.1 rule 1).
- `register_scheduled_check_provider(provider: ScheduledCheckProvider) -> None` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 101)
- `unregister_scheduled_check_provider(provider: ScheduledCheckProvider) -> None` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 106)
- `scheduled_checks(vault: Any, repository: Any, item_ids: Sequence[str]) -> dict[str, ScheduledCheck]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 111)
- `class PoolItem` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 120) — One eligible item as the plan sees it.
  - `order_rank(self) -> int` (line 146; public) — The rank the plan orders by: ``plan_rank`` when set, else ``rank``.
  - `as_dict(self) -> dict[str, Any]` (line 151; public)
- `is_followup(scheduled: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 167)
- `classify_item(scheduled: Any, *, rank: int, state: Any, requested: bool, now: datetime, est_minutes: float, check: ScheduledCheck | None, probe_slot_available: bool, deadline: bool=False, open_problem: bool | None=None, probe_value: Mapping[str, Any] | None=None, due_override: bool | None=None, intent_push: bool=False) -> PoolItem` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 174) — §6.1: the first lane that matches, in order.
- `classify_pool(scheduled_items: Sequence[Any], *, item_states: Mapping[str, Any], requested_ids: Iterable[str], now: datetime, estimate: Callable[[str], float], checks: Mapping[str, ScheduledCheck], probe_cap_left: int, deadline_learning_object_ids: Iterable[str]=(), open_problem_learning_object_ids: Iterable[str] | None=None, project_probe_admission: Callable[[Sequence[tuple[Any, float]]], Sequence[tuple[str, Mapping[str, Any]]]] | None=None, is_due: Callable[[str, Any], bool] | None=None, push_ids: Iterable[str]=()) -> list[PoolItem]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 282) — Classify the scheduler's ranked list, in rank order (§6.1).
- `reentry_order(pool: Sequence[PoolItem], tiers: Mapping[str, int] | None=None) -> list[PoolItem]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 389) — §7: assumed-known checks that came due, then intent tier (Master, Learn and goals with deadlines; then Keep; then uncommitted), then rank.
- `class LegacyLanesSource` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 477) — ``legacy_lanes_v1``: deterministic block candidates from the lanes (§6.8).
  - `lane_items(self, lane: str) -> list[PoolItem]` (line 506; public)
  - `candidates(self, state: PlanState) -> list[BlockCandidate]` (line 514; public)
  - `_reading_candidate(self, limit: float) -> BlockCandidate | None` (line 559; internal)

### Module constants

- `SOURCE_NAME` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 51)
- `_EPS` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 52)
- `FOLLOWUP_COMPONENTS` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 55)
- `REPAIR_MIN_RECENT_ERROR` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 66)
- `REPAIR_RULE_DIAGNOSIS` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 69)
- `REPAIR_RULE_RECENT_ERROR` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 70)
- `ASSUMED_CHECK_REASON` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 74)
- `GAP_COMMITMENT_CHECK_REASON` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 79)
- `GAP_SOONER_CHECK_REASON` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 80)
- `INTENT_PUSH_REASON` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 82)
- `_CHECK_PROVIDERS` ([src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py), line 98)

### Explicit exports

`__all__` declares:

- `ASSUMED_CHECK_REASON`
- `FOLLOWUP_COMPONENTS`
- `GAP_COMMITMENT_CHECK_REASON`
- `GAP_SOONER_CHECK_REASON`
- `LegacyLanesSource`
- `PoolItem`
- `REPAIR_MIN_RECENT_ERROR`
- `REPAIR_RULE_DIAGNOSIS`
- `REPAIR_RULE_RECENT_ERROR`
- `SOURCE_NAME`
- `ScheduledCheck`
- `classify_item`
- `classify_pool`
- `is_followup`
- `register_scheduled_check_provider`
- `reentry_order`
- `scheduled_checks`
- `unregister_scheduled_check_provider`

## Internal implementation anchors

- `_order_probes_by_value(pool: list[PoolItem], admitted_order: Sequence[str]) -> list[PoolItem]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 366) — Admitted project probes take their own positions in admission order (the best conditional value per minute first); every other item keeps its place.
- `_candidate_id(lane: str, item_ids: Sequence[str], reading: ReadingTarget | None) -> str` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 423)
- `_group_by_lo(items: Sequence[PoolItem]) -> list[list[PoolItem]]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 429)
- `_lane_reason(lane: str, items: Sequence[PoolItem], titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 436)
- `_pack(items: Sequence[PoolItem], *, lane: str, limit: float, items_left: int | None, merge_small: bool, max_blocks: int) -> list[list[PoolItem]]` ([source](../../../../../../src/learnloop/daily_plan/lanes.py), line 598) — Greedy, rank-ordered packing of LO groups into blocks under ``limit``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `LegacyLanesSource`, `PoolItem`, `REPAIR_RULE_DIAGNOSIS`, `REPAIR_RULE_RECENT_ERROR`, `SOURCE_NAME`, `ScheduledCheck`, `classify_pool`, `reentry_order`, `scheduled_checks`; statically calls `LegacyLanesSource`, `PoolItem`, `ScheduledCheck`, `classify_pool`, `reentry_order`, `scheduled_checks`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `PoolItem`; statically calls `PoolItem`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `ASSUMED_CHECK_REASON`, `GAP_COMMITMENT_CHECK_REASON`, `GAP_SOONER_CHECK_REASON`, `LegacyLanesSource`, `PoolItem`; statically calls `LegacyLanesSource`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BLOCK_MAX_MINUTES`, `BLOCK_MIN_MINUTES`, `BlockCandidate`, `LANES`, `LANE_ACTIONS`, `Lane`, `PlanState`, `ReadingTarget`; calls `BlockCandidate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_plan_build.py](../../../../../../tests/test_daily_plan_build.py) — direct import
  - `test_a_single_due_item_is_a_complete_block`
  - `test_blocks_never_exceed_15_minutes_or_the_lane_or_the_plan`
  - `test_due_project_probes_are_scheduled_checks_under_their_daily_cap`
  - `test_each_item_takes_the_first_lane_that_matches`
  - `test_project_probes_stay_outside_the_new_item_cap`
  - `test_small_maintain_groups_merge_into_one_block_and_new_stays_on_one_lo`
- [tests/test_daily_plan_reentry.py](../../../../../../tests/test_daily_plan_reentry.py) — direct import
  - `test_reentry_orders_assumed_checks_then_deadlines_then_rank`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f1_repair_needs_a_recent_error_not_any_active_one`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f6_the_chooser_takes_the_master_block_first_in_re_entry`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_an_assumed_lo_with_no_commitment_reads_as_keep_for_its_check`
  - `test_committed_los_reach_the_chooser_state_with_their_intent`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_the_plan_labels_a_gap_check_as_what_it_is`
- [tests/test_router_why_copy.py](../../../../../../tests/test_router_why_copy.py) — direct import
  - `test_reason_codes_follow_the_lane_and_its_items`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_the_report_scores_a_project_probe_through_r1s_plan_block`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_probe_the_plan_cannot_fit_neither_takes_a_slot_nor_discounts_another`
  - `test_the_block_chooser_plans_the_best_probe_per_minute_first`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_minutes_change_values_probes_against_the_new_minutes_left`
  - `test_a_probe_outside_the_plans_universe_does_not_suppress_one_inside`
  - `test_a_refresh_admits_against_the_minutes_left_and_conditions_on_planned_probes`
  - `test_a_skipped_probe_does_not_suppress_its_alternative_on_refresh`
  - `test_project_probes_are_admitted_against_the_minutes_left_after_requests`
  - `test_requested_probes_and_requests_share_one_request_rule`

## Modification guidance

- Make changes here when the responsibility remains lanes within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/lanes.py](../../../../../../src/learnloop/daily_plan/lanes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
