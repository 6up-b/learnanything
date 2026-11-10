---
title: "learnloop.instructional.policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/policy.py"
source_paths:
  - "src/learnloop/instructional/policy.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.policy module"
  - "src/learnloop/instructional/policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.policy` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Server-side caller contexts (spec_source_practice_and_probes_v1 §5.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/policy.py](../../../../../../src/learnloop/instructional/policy.py) |
| Source lines | 182 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `cold_administration_open(repository: Repository, item_id: str | None) -> bool` ([source](../../../../../../src/learnloop/instructional/policy.py), line 33) — Whether ``item_id`` is reserved by an open cold follow-up task, or for a goal's held-out exam.
- `attempt_window_open(repository: Repository, item_id: str | None) -> bool | None` ([source](../../../../../../src/learnloop/instructional/policy.py), line 54) — False once the item's latest attempt was a correct submission; else True.
- `cold_notes(repository: Repository, item_id: str | None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/instructional/policy.py), line 78) — Why a cold administration is open, when it is for the exam's sake.
- `learning_objects_for_event(vault: LoadedVault, event: Mapping[str, Any]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/instructional/policy.py), line 84) — The LOs a tutor question is about: its item's, its note's or its span's.
- `caller_for_question_event(vault: LoadedVault, repository: Repository, event_id: str, *, post_attempt: bool=False) -> CallerContext` ([source](../../../../../../src/learnloop/instructional/policy.py), line 105) — The tutor's caller context, rebuilt from the stored question event.
- `caller_for(repository: Repository, kind: str, ref: str | None=None, *, item_id: str | None=None, attempt_id: str | None=None, learning_object_ids: Sequence[str]=(), post_attempt: bool=False, context: str | None=None) -> CallerContext` ([source](../../../../../../src/learnloop/instructional/policy.py), line 141) — A server-side caller with no question event (plan, Reader UI, need, agent).
- `policy_for(caller: CallerContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/policy.py), line 156)
- `check_named_ids(caller: CallerContext, *, item_id: str | None=None, attempt_id: str | None=None) -> None` ([source](../../../../../../src/learnloop/instructional/policy.py), line 161) — A request naming an item or attempt it was not called about is refused (G2).

### Module constants

- `WINDOW_CLOSING_CORRECTNESS` ([src/learnloop/instructional/policy.py](../../../../../../src/learnloop/instructional/policy.py), line 26)
- `EXAM_RESERVED_NOTE` ([src/learnloop/instructional/policy.py](../../../../../../src/learnloop/instructional/policy.py), line 30)

### Explicit exports

`__all__` declares:

- `EXAM_RESERVED_NOTE`
- `WINDOW_CLOSING_CORRECTNESS`
- `attempt_window_open`
- `caller_for`
- `caller_for_question_event`
- `check_named_ids`
- `cold_administration_open`
- `cold_notes`
- `learning_objects_for_event`
- `policy_for`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `caller_for_question_event`; statically calls `caller_for_question_event`
- [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]] — imports `learning_objects_for_event`; statically calls `learning_objects_for_event`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `PolicyRefused`, `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `caller_for_question_event`, `cold_administration_open`, `cold_notes`; statically calls `caller_for_question_event`, `cold_administration_open`, `cold_notes`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `caller_for`, `caller_for_question_event`; statically calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `cold_administration_open`; statically calls `cold_administration_open`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `caller_for`, `caller_for_question_event`; statically calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `caller_for`; statically calls `caller_for`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `caller_for`, `caller_for_question_event`; statically calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `cold_administration_open`; statically calls `cold_administration_open`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_reserved`; calls `exam_reserved`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `ITEM_BOUND_CONTEXTS`, `PolicyRefused`, `derive_policy`; calls `CallerContext`, `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]], [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_tutor_keep_takes_a_take_with_the_library_answer_off`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_the_solution_rule_is_the_retrieval_policy_s_window`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_pick_of_an_item_reserved_since_its_proposal_is_refused_before_anything_is_recorded`
  - `test_an_exam_reserved_item_is_a_cold_administration_for_every_caller`
  - `test_an_import_rechecks_a_stale_proposal_before_any_paid_call`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_pick_of_an_item_marked_held_out_since_its_proposal_is_refused`
- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_the_tutor_refuses_a_bound_ask_while_its_cold_administration_is_open`
- [tests/test_practice_availability.py](../../../../../../tests/test_practice_availability.py) — direct import
  - `test_availability_counts_without_calling_a_model`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_a_cold_administration_retrieves_nothing`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_reader_question_rebuilds_as_its_items_caller`
  - `test_a_cold_bound_question_keeps_the_items_guards`
  - `test_a_server_derived_cold_administration_refuses_every_tool`
  - `test_a_server_derived_cold_refuses_tools_whatever_the_retrieval_switch`
  - `test_an_explicitly_cold_question_rebuilds_cold`
  - `test_offers_only_the_bound_items_guards_hold`
  - `test_retrieval_off_a_bound_question_offers_nothing_and_rebuilds_as_its_item`
  - `test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_a_pick_records_the_impressions_shown_before_it`
  - `test_a_value_intent_pick_keeps_both_verdicts`
  - `test_an_exercise_pick_and_a_need_served_are_source_exercise_rows`
  - `test_an_opened_offer_records_exposure_that_independence_reads`
  - `test_passages_and_comparisons_are_recorded_when_shown`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_comparison_pays_for_nothing_once_the_daily_cap_is_spent`
  - `test_a_verified_passage_request_respects_the_daily_cap`
  - `test_an_ordinary_practice_request_respects_the_daily_cap`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_held_correct_grade_keeps_the_attempt_window_open`
- [tests/test_tool_dispatch_policy.py](../../../../../../tests/test_tool_dispatch_policy.py) — direct import
  - `test_a_cold_administration_opened_after_the_request_narrows_the_run`
  - `test_a_cold_administration_refuses_every_tool`
  - `test_a_continuation_with_narrower_filters_is_refused`
  - `test_a_find_practice_tool_result_can_be_continued`
  - `test_a_request_cannot_name_an_item_or_widen_its_policy`
  - `test_each_caller_gets_its_policy_and_both_rows`
- [tests/test_tool_results_withhold_answers.py](../../../../../../tests/test_tool_results_withhold_answers.py) — direct import
  - `test_an_unbound_agent_never_reads_a_solution_block_or_an_exam`
  - `test_no_tool_result_contains_an_expected_answer`
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_a_cold_administration_proposes_nothing`
  - `test_the_caller_is_rederived_on_the_server_and_cannot_widen`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`
  - `test_a_valued_pick_keeps_predicted_outcomes_regime_and_minutes`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
  - `test_rw4d_followup_an_agent_callers_comparison_is_not_withheld_as_unresolvable`

## Modification guidance

- Make changes here when the responsibility remains policy within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/policy.py](../../../../../../src/learnloop/instructional/policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
