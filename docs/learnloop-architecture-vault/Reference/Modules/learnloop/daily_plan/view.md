---
title: "learnloop.daily_plan.view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/view.py"
source_paths:
  - "src/learnloop/daily_plan/view.py"
source_commit: "84b890f02cd674436ba3b9ce3ab22628680d0783"
source_commit_timestamp: "2026-11-05T07:25:07-05:00"
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
  - "learnloop.daily_plan.view module"
  - "src/learnloop/daily_plan/view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.view` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The plan DTO (``spec_daily_loop_v1.md`` §6.7, G3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/view.py](../../../../../../src/learnloop/daily_plan/view.py) |
| Source lines | 331 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `84b890f02cd674436ba3b9ce3ab22628680d0783` |
| Commit timestamp | `2026-11-05T07:25:07-05:00` |

## Public API

- `project_blocks(record: PlanRecord, context: PoolContext | None, policy: PlanPolicy, *, max_blocks: int=MAX_PROJECTED_BLOCKS) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 40) — The blocks after the chosen ones, if nothing changes: a projection only.
- `minute_choices(presets: list[int], remembered: int) -> list[int]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 199)
- `plan_view(env: PlanEnv, record: PlanRecord, *, context: PoolContext | None, next_step: dict[str, Any] | None, reentry_panel: dict[str, Any] | None=None, streak: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 203)
- `disabled_view(vault: Any, *, reason: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 318)
- `now_payload(moment: datetime) -> str` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 327)

### Module constants

- `MAX_PROJECTED_BLOCKS` ([src/learnloop/daily_plan/view.py](../../../../../../src/learnloop/daily_plan/view.py), line 35)
- `PROMPT_PREVIEW_CHARS` ([src/learnloop/daily_plan/view.py](../../../../../../src/learnloop/daily_plan/view.py), line 37)

### Explicit exports

`__all__` declares:

- `MAX_PROJECTED_BLOCKS`
- `disabled_view`
- `minute_choices`
- `plan_view`
- `project_blocks`

## Internal implementation anchors

- `_item_row(env: PlanEnv, item: PlannedItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 67)
- `_why_details(block: PlannedBlock) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 92)
- `_block_row(env: PlanEnv, record: PlanRecord, block: PlannedBlock, current_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 108)
- `_actual_minutes(records: list[PlanRecord]) -> float` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 145)
- `_totals(records: list[PlanRecord]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 161)
- `_reentry_numbers(record: PlanRecord, panel: dict[str, Any] | None, projected: list[dict[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/view.py), line 184) — "Today: a short re-entry, about 12 min, 7 items": the chosen blocks plus the projected ones, the same figures the plan view shows (G3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `plan_view`; statically calls `plan_view`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `disabled_view`, `plan_view`; statically calls `disabled_view`, `plan_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `PlanPolicy`, `PoolContext`, `day_records`, `simulate_blocks`; calls `day_records`, `simulate_blocks`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `PlanRecord`, `PlannedBlock`, `PlannedItem`
- [[Reference/Modules/learnloop/daily_plan/split|learnloop.daily_plan.split]] — imports `display_lane_minutes`, `split_line`; calls `display_lane_minutes`, `split_line`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `LANES`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `DETAILS_STAGED`, `mixture_details`; calls `mixture_details`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f3_plan_reads_never_call_the_live_chooser`
  - `test_f9_more_new_preview_is_what_confirming_plans`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_plan_rows_preview_keeps_the_sentence_whole`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_why_surface_offers_the_trace_in_plain_words`
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_the_check_takes_the_first_practice_slot_outside_the_mix_with_no_label`
- [tests/test_router_g7_fallback.py](../../../../../../tests/test_router_g7_fallback.py) — direct import
  - `test_a_timeout_reaches_the_staged_rule_with_fallback_llm`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_drawn_llm_pick_shows_its_rationale_and_its_cited_answers`
  - `test_with_no_model_set_up_the_rule_chooses_deterministically`
- [tests/test_rw7b_fix_round2.py](../../../../../../tests/test_rw7b_fix_round2.py) — direct import
  - `test_a_withdrawn_path_reading_leaves_the_predecessors_reading_in_the_projection`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_a_hold_that_lifts_today_waits_instead_of_finishing_the_plan`

## Modification guidance

- Make changes here when the responsibility remains view within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/view.py](../../../../../../src/learnloop/daily_plan/view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
