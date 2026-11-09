---
title: "learnloop.daily_plan.types"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/types.py"
source_paths:
  - "src/learnloop/daily_plan/types.py"
source_commit: "867897f2287300fc9267644fd4cb983021f5e273"
source_commit_timestamp: "2026-11-08T21:16:02-05:00"
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
  - "learnloop.daily_plan.types module"
  - "src/learnloop/daily_plan/types.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.types`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.types` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The block-chooser interface (``spec_daily_loop_v1.md`` §6.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py) |
| Source lines | 247 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `867897f2287300fc9267644fd4cb983021f5e273` |
| Commit timestamp | `2026-11-08T21:16:02-05:00` |

## Public API

- `class IntentView` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 67) — An LO's intent as the chooser may read it (§5).
- `class PlanState` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 82) — Everything a chooser may read (§6.8).
- `class ReadingTarget` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 112) — A reading block's section (§6.10).
  - `as_dict(self) -> dict[str, Any]` (line 129; public)
- `class BlockCandidate` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 137)
  - `log_row(self) -> dict[str, Any]` (line 163; public)
- `class BlockSource(Protocol)` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 178)
  - `candidates(self, state: PlanState) -> list[BlockCandidate]` (line 181; public)
- `class BlockChoice` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 185)
- `class BlockChooser(Protocol)` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 203)
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 206; public)
- `class DecisionPending(Exception)` ([source](../../../../../../src/learnloop/daily_plan/types.py), line 209) — Router R2b: a chooser that may not wait (a read, a prefetch) found the decision's models still out.
  - `__init__(self, key: str='') -> None` (line 214; internal)

### Module constants

- `LANES` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 20)
- `FLOW_ORDER` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 24)
- `PICK_DEDUCTION_ORDER` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 26)
- `REENTRY_LANES` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 28)
- `AFTER_REENTRY_LANE_PRIORITY` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 32)
- `LANE_ACTIONS` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 35)
- `CONTINUE_CURRENT` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 46)
- `STOP_FOR_TODAY` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 47)
- `LESSON_OFFER_SUBTYPE` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 52)
- `LESSON_OFFER_PREFIX` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 53)
- `FOLLOWUP_CONTEST_PREFIX` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 56)
- `FOLLOWUP_CONTEST_NOTE` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 57)
- `STOP_OFFER_MINUTES` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 60)
- `BLOCK_MAX_MINUTES` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 62)
- `BLOCK_MIN_MINUTES` ([src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py), line 63)

### Explicit exports

`__all__` declares:

- `AFTER_REENTRY_LANE_PRIORITY`
- `BLOCK_MAX_MINUTES`
- `BLOCK_MIN_MINUTES`
- `BlockCandidate`
- `BlockChoice`
- `BlockChooser`
- `BlockSource`
- `CONTINUE_CURRENT`
- `ChosenBy`
- `DecisionPending`
- `FLOW_ORDER`
- `IntentView`
- `LANES`
- `LANE_ACTIONS`
- `FOLLOWUP_CONTEST_NOTE`
- `FOLLOWUP_CONTEST_PREFIX`
- `LESSON_OFFER_PREFIX`
- `LESSON_OFFER_SUBTYPE`
- `Lane`
- `PICK_DEDUCTION_ORDER`
- `PlanKind`
- `PlanState`
- `REENTRY_LANES`
- `ReadingTarget`
- `STOP_FOR_TODAY`
- `STOP_OFFER_MINUTES`
- `WhyKind`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]] — imports `BlockCandidate`, `BlockChoice`, `LANES`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; statically calls `BlockChoice`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `AFTER_REENTRY_LANE_PRIORITY`, `BLOCK_MAX_MINUTES`, `BlockCandidate`, `BlockChoice`, `BlockChooser`, `BlockSource`, `CONTINUE_CURRENT`, `DecisionPending`, `FOLLOWUP_CONTEST_NOTE`, `FOLLOWUP_CONTEST_PREFIX`, `IntentView`, `LANES`, `LANE_ACTIONS`, `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`, `PICK_DEDUCTION_ORDER`, `PlanState`, `REENTRY_LANES`, `ReadingTarget`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; statically calls `BlockCandidate`, `BlockChoice`, `IntentView`, `PlanState`, `ReadingTarget`
- [[Reference/Modules/learnloop/daily_plan/lanes|learnloop.daily_plan.lanes]] — imports `BLOCK_MAX_MINUTES`, `BLOCK_MIN_MINUTES`, `BlockCandidate`, `LANES`, `LANE_ACTIONS`, `Lane`, `PlanState`, `ReadingTarget`; statically calls `BlockCandidate`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `BlockCandidate`, `LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `BlockCandidate`, `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`; statically calls `BlockCandidate`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `BlockCandidate`, `BlockChoice`, `CONTINUE_CURRENT`, `DecisionPending`, `FOLLOWUP_CONTEST_NOTE`, `LESSON_OFFER_SUBTYPE`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; statically calls `BlockChoice`, `DecisionPending`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `BlockCandidate`, `FOLLOWUP_CONTEST_NOTE`, `LESSON_OFFER_SUBTYPE`, `PlanState`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]] — imports `ReadingTarget`; statically calls `ReadingTarget`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `LANES`, `LESSON_OFFER_SUBTYPE`, `ReadingTarget`; statically calls `ReadingTarget`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `BlockCandidate`, `PlanState`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `BlockCandidate`, `BlockChoice`, `CONTINUE_CURRENT`, `DecisionPending`, `LANES`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; statically calls `BlockCandidate`, `BlockChoice`, `DecisionPending`, `PlanState`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `DecisionPending`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `BLOCK_MAX_MINUTES`
- [[Reference/Modules/learnloop/daily_plan/split|learnloop.daily_plan.split]] — imports `FLOW_ORDER`, `LANES`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `BLOCK_MAX_MINUTES`, `BlockCandidate`, `BlockChoice`, `LANE_ACTIONS`, `PlanState`, `STOP_OFFER_MINUTES`; statically calls `BlockChoice`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `LANES`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lanes|learnloop.daily_plan.lanes]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
  - `test_stopping_is_only_allowed_when_offered`
  - `test_unknown_ids_and_continue_at_a_boundary_fall_back_and_are_flagged`
- [tests/test_daily_plan_build.py](../../../../../../tests/test_daily_plan_build.py) — direct import
- [tests/test_daily_plan_kill_switch.py](../../../../../../tests/test_daily_plan_kill_switch.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f6_a_reopened_plan_that_stops_again_keeps_both_stop_receipts`
  - `test_f6_a_router_stop_keeps_its_propensity_and_candidates`
  - `test_f7_malformed_choices_fall_back_and_are_flagged`
- [tests/test_daily_plan_split.py](../../../../../../tests/test_daily_plan_split.py) — direct import
  - `test_reentry_plans_use_only_repair_and_maintain`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_question_not_yet_written_takes_the_probe_interface_only_with_the_lesson_in_the_support`
- [tests/test_ih3_phone_host.py](../../../../../../tests/test_ih3_phone_host.py) — direct import
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_kinds_are_the_plans_own_names`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_lesson_ref_prefix_is_the_plans`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f6_the_chooser_takes_the_master_block_first_in_re_entry`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_an_assumed_lo_with_no_commitment_reads_as_keep_for_its_check`
  - `test_committed_los_reach_the_chooser_state_with_their_intent`
- [tests/test_mcp_c1a_landing.py](../../../../../../tests/test_mcp_c1a_landing.py) — direct import
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_a_reading_target_is_stored_as_the_predecessors_unless_the_path_chose_it`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
- [tests/test_ro2_ad_raw_document_reads.py](../../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_ro4s_reading_action_maps_its_section_through_the_chokepoint`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_protection_holds_on_the_llm_policys_card`
- [tests/test_router_g1_feasibility.py](../../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back`
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
  - `test_a_chooser_stop_is_a_stop_for_today_plan_block`
  - `test_a_choosers_own_decision_id_is_kept_and_not_logged_twice`
  - `test_a_malformed_choosers_fallback_block_gets_r1s_id`
  - `test_plan_block_decisions_get_router_decision_ids_end_to_end`
- [tests/test_router_r2c_teach_back.py](../../../../../../tests/test_router_r2c_teach_back.py) — direct import
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_drawn_offer_is_a_block_answered_on_its_own_decision`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1m_a_valid_stop_with_work_feasible_is_kept`
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_under_the_router_mixture_a_drawn_stop_stays_a_logged_stop_beside_a_lifting_hold`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_probe_the_plan_cannot_fit_neither_takes_a_slot_nor_discounts_another`
  - `test_the_block_chooser_plans_the_best_probe_per_minute_first`

## Modification guidance

- Make changes here when the responsibility remains types within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/types.py](../../../../../../src/learnloop/daily_plan/types.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
