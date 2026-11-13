---
title: "learnloop.source_retrieval.policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/policy.py"
source_paths:
  - "src/learnloop/source_retrieval/policy.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.policy module"
  - "src/learnloop/source_retrieval/policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.policy` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Retrieval policies: what a caller's context may receive (spec_source_practice_and_probes_v1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/policy.py](../../../../../../src/learnloop/source_retrieval/policy.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PolicyRefused(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/policy.py), line 31) — A request the caller's context does not allow (G2).
  - `__init__(self, code: str, message: str) -> None` (line 34; internal)
- `class CallerContext` ([source](../../../../../../src/learnloop/source_retrieval/policy.py), line 40) — Where a call comes from, built on the server (never from arguments).
  - `as_dict(self) -> dict[str, Any]` (line 62; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'CallerContext'` (line 69; public)
- `derive_policy(caller: CallerContext) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/policy.py), line 80) — ``(policy, how it was derived)`` for ``caller`` (§5.2).
- `assert_policy(caller: CallerContext, requested: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/policy.py), line 98) — The derived policy; a requested policy that differs is refused (G2).

### Module constants

- `POLICIES` ([src/learnloop/source_retrieval/policy.py](../../../../../../src/learnloop/source_retrieval/policy.py), line 20)
- `CALLER_KINDS` ([src/learnloop/source_retrieval/policy.py](../../../../../../src/learnloop/source_retrieval/policy.py), line 25)
- `ITEM_BOUND_CONTEXTS` ([src/learnloop/source_retrieval/policy.py](../../../../../../src/learnloop/source_retrieval/policy.py), line 28)

### Explicit exports

`__all__` declares:

- `CALLER_KINDS`
- `ITEM_BOUND_CONTEXTS`
- `POLICIES`
- `CallerContext`
- `PolicyRefused`
- `RetrievalPolicy`
- `assert_policy`
- `derive_policy`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `PolicyRefused`, `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `CallerContext`, `derive_policy`; statically calls `CallerContext`, `derive_policy`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `CallerContext`; statically calls `CallerContext`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]] — imports `ITEM_BOUND_CONTEXTS`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `CallerContext`, `ITEM_BOUND_CONTEXTS`, `PolicyRefused`, `derive_policy`; statically calls `CallerContext`, `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; statically calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `CallerContext`, `PolicyRefused`; statically calls `PolicyRefused`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; statically calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `PolicyRefused`, `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; statically calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `CallerContext`, `POLICIES`, `PolicyRefused`, `derive_policy`; statically calls `CallerContext`, `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `CallerContext`, `PolicyRefused`; statically calls `CallerContext`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `PolicyRefused`, `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `PolicyRefused`, `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `derive_policy`; statically calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `PolicyRefused`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]], [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]], [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]] and 18 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_compare_sources.py](../../../../../../tests/test_compare_sources.py) — direct import
  - `test_a_cold_caller_is_refused_and_a_wider_policy_too`
  - `test_every_source_is_considered_and_uncompared_ones_are_listed`
  - `test_pins_obey_the_policy_in_a_practice_context`
- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_the_discriminating_search_switch_refuses_value_intents`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_an_exam_reserved_item_is_a_cold_administration_for_every_caller`
- [tests/test_find_sources_intents.py](../../../../../../tests/test_find_sources_intents.py) — direct import
  - `test_a_low_confidence_proposal_counts_only_when_nothing_better_exists`
  - `test_a_policy_argument_cannot_widen_the_callers`
  - `test_a_proposal_never_admits_a_block_into_an_item_bound_scope`
  - `test_cold_attempt_returns_nothing_and_authoring_is_not_a_policy`
  - `test_facet_ids_target_retrieval_and_verification`
  - `test_find_sources_compare_delegates_to_compare_sources`
  - `test_post_attempt_opens_the_solution_only_after_the_window_closes_and_records_a_reveal`
  - `test_reader_consumer_contract_calls`
  - `test_remediate_reads_correction_refs_and_reports_missing_sources`
  - `test_roles_match_an_rw4e_proposal`
  - `test_the_compare_switch_holds_on_every_entry_point`
- [tests/test_hypothesis_reference_contract.py](../../../../../../tests/test_hypothesis_reference_contract.py) — direct import
  - `test_a_named_gap_runs_through_the_tool_as_what_it_names`
  - `test_schema_valid_references_run_through_the_tool`
- [tests/test_p4_tutor_tool_withhold.py](../../../../../../tests/test_p4_tutor_tool_withhold.py) — direct import
  - `test_the_compare_sources_tool_never_sends_an_assessment_lane_passage_to_verification`
  - `test_the_find_sources_tool_never_sends_an_assessment_lane_passage_to_verification`
- [tests/test_reader_ca3_codex_review.py](../../../../../../tests/test_reader_ca3_codex_review.py) — direct import
  - `test_f3_a_pin_from_a_book_not_named_is_dropped_before_verification`
  - `test_f3_the_anchor_stays_the_one_exception`
  - `test_f3_without_named_books_a_pin_is_compared_as_today`
  - `test_f4_a_one_block_anchor_is_stored_as_before`
  - `test_f4_the_stored_entry_and_cache_identity_name_every_anchor_block`
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_named_book_outside_the_scope_is_refused_before_anything_is_read`
  - `test_an_anchor_needs_no_pin_and_leads_as_its_books_passage`
  - `test_an_anchor_obeys_the_pins_filters`
  - `test_named_books_only_narrow_and_the_others_are_listed_never_sent`
  - `test_without_the_ca3_arguments_the_manifest_is_todays`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_a_cell_names_the_anchor_block_that_holds_its_quote`
  - `test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words`
  - `test_a_v2_request_never_reuses_a_v1_row_and_reuses_its_own`
  - `test_an_invented_quote_is_dropped_never_shown`
  - `test_compare_sources_by_point_is_one_call_on_the_same_route_and_stores_v2`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_reader_question_rebuilds_as_its_items_caller`
  - `test_a_server_derived_cold_refuses_tools_whatever_the_retrieval_switch`
  - `test_an_explicitly_cold_question_rebuilds_cold`
  - `test_retrieval_off_a_bound_question_offers_nothing_and_rebuilds_as_its_item`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_the_teacher_origin_is_the_lesson_services_only`
- [tests/test_roles_switch_off.py](../../../../../../tests/test_roles_switch_off.py) — direct import
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_a_proposal_held_out_later_is_never_returned`
  - `test_a_proposal_never_admits_a_block_nor_removes_an_exclusion`
  - `test_a_stronger_proposal_the_caller_excluded_never_blocks_the_low_confidence_one_under_roles`
  - `test_a_stronger_proposal_the_roles_filter_rejects_never_blocks_the_low_confidence_one`
  - `test_a_stronger_proposal_the_scope_excludes_never_blocks_the_low_confidence_one`
  - `test_an_intent_list_takes_a_low_confidence_proposal_only_when_no_stronger_one_is_in_scope`
  - `test_roles_filters_match_ingest_hints_and_proposals_with_the_low_confidence_rule`
  - `test_the_roles_filter_falls_back_when_the_caller_excluded_every_stronger_passage`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_comparison_is_capped_only_when_the_owner_sets_a_cap`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_find_sources_and_compare_never_hand_exam_material_to_a_model`
- [tests/test_tool_dispatch_policy.py](../../../../../../tests/test_tool_dispatch_policy.py) — direct import
  - `test_a_cold_administration_opened_after_the_request_narrows_the_run`
  - `test_a_cold_administration_refuses_every_tool`
  - `test_a_find_practice_tool_result_can_be_continued`
  - `test_a_request_cannot_name_an_item_or_widen_its_policy`
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_a_cold_administration_proposes_nothing`
  - `test_the_caller_is_rederived_on_the_server_and_cannot_widen`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_rereview_a_reuse_for_an_unknown_question_is_not_persisted`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_after_a_level_three_hint_the_example_takes_the_learners_route`
  - `test_the_default_search_is_the_sources_specs_worked_example_intent`
- [tests/workbench_route_example_helpers.py](../../../../../../tests/workbench_route_example_helpers.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains policy within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/policy.py](../../../../../../src/learnloop/source_retrieval/policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
