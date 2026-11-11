---
title: "learnloop.intent.checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/checks.py"
source_paths:
  - "src/learnloop/intent/checks.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.checks module"
  - "src/learnloop/intent/checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.checks` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: Serving "Check once" (spec §5.2) and how a served check looks (Reader §9.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py) |
| Source lines | 272 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `settle_answered_checks(vault: Any, repository: Any, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/intent/checks.py), line 65) — Satisfy every pending check an attempt has answered.
- `restoration_link(provenance: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/checks.py), line 87) — The way back to where it was studied, or None (rendered only when present).
- `cold_followup_duty(repository: Any, practice_item_id: str, *, now: datetime) -> str | None` ([source](../../../../../../src/learnloop/intent/checks.py), line 122) — ``"cold_followup"`` when a due cold follow-up selects the item (the task submit answers and refuses help for), else None.
- `served_check(vault: Any, repository: Any, practice_item_id: str, *, now: datetime, duty: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/checks.py), line 161) — The practice view of ``practice_item_id`` when it is a due check now: cold only when the one eligibility decision says so at this serve (F3: an exposure after the check was planned is read here).
- `cold_followup_view(vault: Any, repository: Any, practice_item_id: str, *, now: datetime) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/checks.py), line 201) — Reader CA2 (mvp-0.34, §15 Q4, ``ask.cold_help_converts``): the practice view of a due cold follow-up served without a "Check once": the cold banner, the help ladder's header (choose, then take) and no locators until feedback, exactly as a check's cold view.
- `answered_check(vault: Any, repository: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/checks.py), line 223) — The check an attempt answered (its feedback shows the restoration link), or None.

### Module constants

- `COLD_BANNER` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 42)
- `HELP_LADDER_HEADER` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 45)
- `PLAN_LINE` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 47)
- `PRACTICE_BANNER` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 50)
- `MEASURED_BANNER` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 56)
- `DUTY_COLD_FOLLOWUP` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 58)
- `DUTY_DIAGNOSTIC` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 59)
- `_COLD_FOLLOWUP_KINDS` ([src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py), line 62)

### Explicit exports

`__all__` declares:

- `COLD_BANNER`
- `DUTY_COLD_FOLLOWUP`
- `DUTY_DIAGNOSTIC`
- `HELP_LADDER_HEADER`
- `MEASURED_BANNER`
- `PLAN_LINE`
- `PRACTICE_BANNER`
- `answered_check`
- `cold_followup_duty`
- `cold_followup_view`
- `restoration_link`
- `served_check`
- `settle_answered_checks`

## Internal implementation anchors

- `_measured_view(check: CheckState, *, duty: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/checks.py), line 104) — F15 (R3): a cold check served under the item's stricter duty, whose safeguards refuse help; the view promises none and offers no ladder header.
- `_view(check: CheckState, *, cold: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/checks.py), line 133)
- `_help_converts(vault: Any) -> bool` ([source](../../../../../../src/learnloop/intent/checks.py), line 195)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `cold_followup_duty`, `served_check`; statically calls `cold_followup_duty`, `served_check`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `answered_check`; statically calls `answered_check`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `cold_followup_view`, `served_check`; statically calls `cold_followup_view`, `served_check`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `DUTY_DIAGNOSTIC`, `cold_followup_view`, `served_check`; statically calls `cold_followup_view`, `served_check`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `settle_answered_checks`; statically calls `settle_answered_checks`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `cold_followup_duty`, `served_check`; statically calls `cold_followup_duty`, `served_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`; calls `SystemClock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`, `satisfy_single_check`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `CheckState`, `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `help_converts_active`; calls `help_converts_active`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_ca1_as_printed_helpers.py](../../../../../../tests/reader_ca1_as_printed_helpers.py) — direct import
- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f10_a_check_answered_between_settles_keeps_one_due_and_is_terminal`
  - `test_f10_a_check_answered_between_settles_reads_the_same_whatever_the_wall_clock`
  - `test_f10_a_check_satisfied_before_any_settlement_saw_it_due_gets_its_one_due_at_the_answer`
- [tests/test_dl2_rw4b_keyed_pick_check.py](../../../../../../tests/test_dl2_rw4b_keyed_pick_check.py) — direct import
  - `test_a_keyed_pick_of_a_due_check_the_plan_does_not_hold_is_a_one_item_block_and_answers_it`
  - `test_a_keyed_pick_of_a_planned_due_check_serves_the_check_once_and_its_answer_satisfies_it`
  - `test_a_keyed_pick_of_an_item_a_waiting_check_holds_is_served_and_answers_nothing`
- [tests/test_intent_checks.py](../../../../../../tests/test_intent_checks.py) — direct import
  - `test_a_served_check_is_cold_help_stays_with_its_consequence_and_nothing_locates_it`
  - `test_an_attempt_before_the_date_does_not_answer_the_check`
  - `test_an_ordinary_attempt_answers_no_check`
  - `test_settling_writes_the_satisfaction_once_and_only_for_answered_checks`
  - `test_the_way_back_is_rendered_only_when_the_provenance_carries_it`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f11_a_retired_cold_sibling_never_suppresses_the_servable_candidate`
  - `test_f3_a_cold_attempt_still_answers_the_check_its_own_feedback_notwithstanding`
  - `test_f3_an_attempt_under_a_siblings_hold_is_practice_not_the_check`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f3_a_check_whose_answer_the_tutor_revealed_is_not_served_as_a_check_on_your_own`
  - `test_f3_a_hinted_attempt_does_not_use_up_the_check`
  - `test_f3_a_routine_display_makes_the_check_wait_until_it_is_cold_again`
  - `test_f3_an_exposure_after_planning_is_read_at_the_serve`
  - `test_f3_an_lo_check_prefers_a_candidate_that_can_be_taken_cold`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f13_an_assisted_reconstruction_leaves_the_check_pending_and_dates_it_again`
  - `test_f13_an_independent_attempt_still_answers`
  - `test_f15_a_check_under_an_active_diagnostic_is_served_under_that_duty`
  - `test_f15_a_check_with_a_cold_follow_up_is_served_under_that_duty`
  - `test_f15_a_pure_diagnostic_answer_satisfies_the_check`
  - `test_f15_a_seen_check_with_a_cold_follow_up_stays_practice`
  - `test_f15_an_ordinary_check_still_offers_help`
  - `test_f15_the_serve_chooses_the_variant_server_side_and_one_completion_satisfies_both`
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_f11_a_fresh_diagnostic_probe_never_suppresses_the_servable_candidate`
  - `test_f12_a_frozen_self_grade_answers_the_check`
  - `test_f12_a_repeated_self_grade_never_postpones`
  - `test_f12_an_unrelated_disclosure_still_holds`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_card_written_from_a_photo_shows_the_photo_outside_a_check`
  - `test_an_unreadable_check_fails_closed`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
  - `test_the_legacy_residual_an_old_mark_on_an_unmarked_answer_graph_keeps_mains_rule`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_a_due_cold_follow_up_is_served_with_the_take_step`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_the_provenance_carries_the_way_back_and_dl2_renders_it`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f10_the_workbench_session_carries_the_way_back_without_an_inquiry`

## Modification guidance

- Make changes here when the responsibility remains checks within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/checks.py](../../../../../../src/learnloop/intent/checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
