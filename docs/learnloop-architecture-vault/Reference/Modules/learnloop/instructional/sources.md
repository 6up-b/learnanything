---
title: "learnloop.instructional.sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/sources.py"
source_paths:
  - "src/learnloop/instructional/sources.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.instructional.sources module"
  - "src/learnloop/instructional/sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.sources` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Passages and comparisons for real callers (spec_source_practice_and_probes_v1 §9.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/sources.py](../../../../../../src/learnloop/instructional/sources.py) |
| Source lines | 205 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ServiceDisabled(PolicyRefused)` ([source](../../../../../../src/learnloop/instructional/sources.py), line 31)
  - `__init__(self, switch: str) -> None` (line 32; internal)
- `active_misconceptions(repository: Repository, learning_object_id: str) -> list[Any]` ([source](../../../../../../src/learnloop/instructional/sources.py), line 44) — The LO's active misconceptions (the diagnoser's overlay as recorded).
- `resolve_misconceptions(repository: Repository, target_hypotheses: Sequence[Mapping[str, Any]], *, item: PracticeItem | None) -> list[Any]` ([source](../../../../../../src/learnloop/instructional/sources.py), line 50) — Remediation targets: named misconception refs (a named gap counts as the belief it names), else the item's LO's active ones.
- `tutor_intent_for(vault: LoadedVault, repository: Repository, *, context: str, item: PracticeItem | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/sources.py), line 72)
- `remediation_passage_provider(vault: LoadedVault, repository: Repository, *, misconception: Any, episode: Mapping[str, Any]) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/instructional/sources.py), line 83) — At most one ranked, verified passage per role the overlay shows.
- `propose_sources(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext, intent: str='explain', **kwargs: Any) -> SourceHits` ([source](../../../../../../src/learnloop/instructional/sources.py), line 115)
- `propose_comparison(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext, **kwargs: Any) -> Comparison` ([source](../../../../../../src/learnloop/instructional/sources.py), line 135)
- `current_contributors(caller: CallerContext | None, current: Comparison | Mapping[str, Any] | None) -> tuple[list[str], list[Any]]` ([source](../../../../../../src/learnloop/instructional/sources.py), line 150) — What the call acting now brings to a comparison, beyond what is stored (Codex review F1): the tutor question it was asked for, and its anchor, dropped pins and unverified sources.
- `refuse_withheld_comparison(vault: LoadedVault, repository: Repository, comparison_id: str | None, *, caller: CallerContext | None=None, current: Comparison | Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/instructional/sources.py), line 167) — RW4d's whole-comparison rule on the direct ``compare_sources`` RPC and the tutor's tool run (Reader follow-ups Nov 1; RW4d's queued follow-up).

### Module constants

- `COMPARISON_WITHHELD_MESSAGE` ([src/learnloop/instructional/sources.py](../../../../../../src/learnloop/instructional/sources.py), line 146)

### Explicit exports

`__all__` declares:

- `COMPARISON_WITHHELD_MESSAGE`
- `ServiceDisabled`
- `active_misconceptions`
- `current_contributors`
- `propose_comparison`
- `propose_sources`
- `refuse_withheld_comparison`
- `remediation_passage_provider`
- `resolve_misconceptions`
- `tutor_intent_for`

## Internal implementation anchors

- `_require(vault: LoadedVault, switch: str | None=None) -> None` ([source](../../../../../../src/learnloop/instructional/sources.py), line 36)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`; statically calls `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `propose_sources`, `resolve_misconceptions`; statically calls `propose_sources`, `resolve_misconceptions`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `propose_sources`; statically calls `propose_sources`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `propose_comparison`, `propose_sources`; statically calls `propose_comparison`, `propose_sources`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `propose_sources`; statically calls `propose_sources`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `propose_sources`, `resolve_misconceptions`; statically calls `propose_sources`, `resolve_misconceptions`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `remediation_passage_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`; statically calls `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `tutor_intent_for`; statically calls `tutor_intent_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `named_gap_target`; calls `named_gap_target`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `withheld_comparisons`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `Comparison`, `compare_sources`; calls `compare_sources`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `SourceHits`, `find_sources`, `find_sources_for_caller`; calls `find_sources`, `find_sources_for_caller`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `PolicyRefused`; calls `PolicyRefused`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]], [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/compare_sources_keep_helpers.py](../../../../../../tests/compare_sources_keep_helpers.py) — direct import
- [tests/test_compare_keep_switch_off.py](../../../../../../tests/test_compare_keep_switch_off.py) — direct import
  - `test_keep_off_every_rw4d_rpc_refuses_and_writes_nothing`
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
- [tests/test_find_sources_intents.py](../../../../../../tests/test_find_sources_intents.py) — direct import
  - `test_remediate_reads_correction_refs_and_reports_missing_sources`
  - `test_the_compare_switch_holds_on_every_entry_point`
- [tests/test_hypothesis_reference_contract.py](../../../../../../tests/test_hypothesis_reference_contract.py) — direct import
  - `test_named_gaps_map_to_their_targets_and_reversals_name_nothing`
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_a_compare_without_its_session_stays_the_items_practice`
  - `test_a_comparison_records_exposure_for_every_passage_it_shows`
  - `test_a_held_out_selection_is_refused_before_any_retrieval`
  - `test_the_table_carries_unchecked_sources_and_why`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_with_the_sources_service_faked_the_fallbacks_call_is_the_documented_one`
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_a_check_reserved_while_passages_are_retrieved_withholds_them`
- [tests/test_prescription_passages.py](../../../../../../tests/test_prescription_passages.py) — direct import
  - `test_ranked_and_verified_passages_replace_the_first_linked_span`
  - `test_switch_off_keeps_todays_prescription_byte_identical`
  - `test_the_tutor_provider_verifies_with_the_remediate_prompt`
  - `test_tutor_intent_is_remediate_only_with_an_active_misconception`
  - `test_verification_unavailable_falls_back_byte_identically`
- [tests/test_reader_ca3_codex_rereview.py](../../../../../../tests/test_reader_ca3_codex_rereview.py) — direct import
- [tests/test_reader_ca3_codex_review.py](../../../../../../tests/test_reader_ca3_codex_review.py) — direct import
- [tests/test_reader_ca3_codex_round3.py](../../../../../../tests/test_reader_ca3_codex_round3.py) — direct import
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
- [tests/test_reader_ca3_landing_ca5a.py](../../../../../../tests/test_reader_ca3_landing_ca5a.py) — direct import
- [tests/test_reader_ca4_landing.py](../../../../../../tests/test_reader_ca4_landing.py) — direct import
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
- [tests/test_reader_compare_table.py](../../../../../../tests/test_reader_compare_table.py) — direct import
  - `test_lines_that_failed_quote_verification_never_reach_the_table`
  - `test_the_table_has_a_row_per_source_with_its_own_quotes_and_no_consensus`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_with_the_sources_spec_faked_the_readers_calls_are_the_documented_ones`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_leaking_gap_statement_never_reaches_the_lookup`
  - `test_a_length_limit_never_cuts_a_statement_into_the_key`
  - `test_a_whitespace_variant_of_the_key_never_reaches_the_rewrite`
  - `test_another_way_excludes_what_the_inquirys_offers_showed`
  - `test_every_sent_model_written_fragment_was_checked`
  - `test_no_bound_model_call_receives_item_text_from_outside_the_plan`
  - `test_the_practice_question_is_a_planned_member_of_the_verification`
- [tests/test_reader_tutor_retrieval.py](../../../../../../tests/test_reader_tutor_retrieval.py) — direct import
  - `test_a_cold_attempt_retrieves_nothing`
  - `test_another_way_never_repeats_a_passage_the_inquiry_showed`
  - `test_personalized_queries_carry_the_open_gaps_and_the_bridge_sees_the_work`
  - `test_that_didnt_help_remediates_the_inquirys_named_gaps`
  - `test_the_tutor_forms_its_own_query_from_the_question_and_the_inquiry`
  - `test_with_the_service_faked_the_readers_calls_are_the_documented_ones`
  - `test_without_a_ready_verification_nothing_is_retrieved_or_claimed`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_comparison_pays_for_nothing_once_the_daily_cap_is_spent`
  - `test_a_verified_passage_request_respects_the_daily_cap`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
  - `test_rw4d_followup_find_sources_compare_intent_applies_the_rule`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_find_sources_compare_reads_a_reuses_persisted_exam_pin`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_the_default_search_is_the_sources_specs_worked_example_intent`

## Modification guidance

- Make changes here when the responsibility remains sources within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/sources.py](../../../../../../src/learnloop/instructional/sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
