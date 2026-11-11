---
title: "learnloop.daily_plan.policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/policy.py"
source_paths:
  - "src/learnloop/daily_plan/policy.py"
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
  - "learnloop.daily_plan.policy module"
  - "src/learnloop/daily_plan/policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.policy` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Which source/chooser pair serves Today (router R2a, plan_router_r2_v1 §3.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/policy.py](../../../../../../src/learnloop/daily_plan/policy.py) |
| Source lines | 196 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `router_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 36) — The router composes Today: the plan serves, the vault is at the R2a successor or later, and the router's kill switch (``router.enabled``) is on.
- `mixture_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 48) — The model mixture chooses Today's blocks: the router composes Today, the vault is at the R2b + R2c successor or later, and ``router.mode`` is ``mixture``.
- `objective_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 62) — Router objective RO4 (spec §8): the objective chooses Today's blocks: the mixture serves and the vault is at RO4's tag with ``[router_objective] enabled``.
- `policy_for(vault: Any, repository: Any, *, session_id: str | None=None, clock: Any=None, runtime: Any=None, serve: bool=False, start_only: bool=False) -> PlanPolicy` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 71) — Today's source/chooser pair for one plan env (one RPC).
- `prefetch_can_start(vault: Any, *, runtime: Any=None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 146) — Spec_instruct_handoff_v1 §3a: a boundary's objective job has something to ask: the objective chooses Today and a model is set up.

### Explicit exports

`__all__` declares:

- `mixture_active`
- `objective_active`
- `policy_for`
- `prefetch_can_start`
- `router_active`

## Internal implementation anchors

- `_lesson_offer_builder(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/policy.py), line 158) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the boundary's lesson offer, at TE3b's tag with its switch on (``router_objective_switches.lesson_offers_on``); None (the predecessor's boundary exactly) otherwise.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `router_active`; statically calls `router_active`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `objective_active`; statically calls `objective_active`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `mixture_active`; statically calls `mixture_active`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `router_active`; statically calls `router_active`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `mixture_active`, `objective_active`, `policy_for`, `router_active`; statically calls `mixture_active`, `objective_active`, `policy_for`, `router_active`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `mixture_active`; statically calls `mixture_active`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `policy_for`, `prefetch_can_start`; statically calls `policy_for`, `prefetch_can_start`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ROUTER_MIXTURE_VERSIONS`, `ROUTER_STAGED_FRAME_VERSIONS`
- [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]] — imports `LaneQuotaChooser`; calls `LaneQuotaChooser`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `DEFAULT_POLICY`, `PlanPolicy`, `plan_active`; calls `PlanPolicy`, `plan_active`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; calls `Offer`, `build`, `sweep_due`, `sweep_ignored`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `ObjectiveChooser`, `ObjectiveRestraintGate`; calls `ObjectiveChooser`, `ObjectiveRestraintGate`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `CardGatherer`; calls `CardGatherer`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `RestraintGate`, `RouterChooser`; calls `RestraintGate`, `RouterChooser`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `default_runtime`; calls `default_runtime`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `SOURCE_NAME`, `StagedChooser`, `StagedFrame`, `StagedFrameFactory`; calls `StagedChooser`, `StagedFrame`, `StagedFrameFactory`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `tables_present`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`; calls `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mcp_c1a_landing_helpers.py](../../../../../../tests/mcp_c1a_landing_helpers.py) — direct import
- [tests/ro5_calibration_helpers.py](../../../../../../tests/ro5_calibration_helpers.py) — direct import
- [tests/router_card_helpers.py](../../../../../../tests/router_card_helpers.py) — direct import
- [tests/router_mixture_helpers.py](../../../../../../tests/router_mixture_helpers.py) — direct import
- [tests/test_evsi_staged_binding.py](../../../../../../tests/test_evsi_staged_binding.py) — direct import
  - `test_a_committed_staged_forecast_joins_the_attempt_bound_to_its_presentation`
  - `test_an_unbound_attempt_on_the_chosen_item_is_never_the_forecasts_outcome`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
- [tests/test_intent_fix_round5.py](../../../../../../tests/test_intent_fix_round5.py) — direct import
  - `test_f16_contract_no_reserved_item_is_ever_planned_and_every_miss_is_named`
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_router_successor`
  - `test_the_router_serves_only_at_the_successor_with_its_switch_on`
  - `test_upgrade_from_mvp022_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_mixture_successor`
  - `test_the_mixture_serves_only_at_the_successor_in_mixture_mode`
  - `test_the_restraint_has_its_own_switch`
  - `test_upgrade_from_mvp023_flips_rebuilds_and_rewrites_nothing`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_the_switch_acts_only_where_the_router_composes_today`
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
  - `test_staged_plans_at_mvp024_are_the_same_in_every_session_and_at_start`
  - `test_the_mixture_draws_over_the_same_candidates_in_every_session`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
- [tests/test_router_card.py](../../../../../../tests/test_router_card.py) — direct import
- [tests/test_router_failure_records.py](../../../../../../tests/test_router_failure_records.py) — direct import
  - `test_a_prefetch_whose_key_changed_before_the_serve_leaves_unclaimed_calls`
  - `test_a_prefetched_decision_names_the_prefetching_and_the_serving_trace`
- [tests/test_router_g1_feasibility.py](../../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back`
  - `test_a_reserved_assessment_surface_is_refused_on_today`
  - `test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame`
  - `test_an_unseen_probe_stays_in_the_plan`
  - `test_the_staged_frame_keeps_refusals_through_the_projection`
- [tests/test_router_g4_restraint.py](../../../../../../tests/test_router_g4_restraint.py) — direct import
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_presentations_and_cards_survive_production_pragmas`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_an_unfinished_request_keeps_its_reservation_after_a_restart`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_a_matured_decision_from_an_earlier_day_is_shown_to_the_models`
- [tests/test_router_why_copy.py](../../../../../../tests/test_router_why_copy.py) — direct import
  - `test_every_why_the_staged_chooser_writes_on_a_plan_is_plain`
- [tests/test_te3b_codex_review.py](../../../../../../tests/test_te3b_codex_review.py) — direct import
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
  - `test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052`

## Modification guidance

- Make changes here when the responsibility remains policy within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/policy.py](../../../../../../src/learnloop/daily_plan/policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
