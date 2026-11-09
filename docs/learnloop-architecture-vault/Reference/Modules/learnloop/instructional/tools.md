---
title: "learnloop.instructional.tools"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/tools.py"
source_paths:
  - "src/learnloop/instructional/tools.py"
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
  - "learnloop.instructional.tools module"
  - "src/learnloop/instructional/tools.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.tools`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.tools` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: The typed tool interface (spec_source_practice_and_probes_v1 §10; S4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py) |
| Source lines | 689 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ToolArgumentsInvalid(ValueError)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 70)
  - `__init__(self, code: str, message: str, details: Any=None) -> None` (line 71; internal)
- `class HypothesisRefArg(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 81)
- `class FindPracticeArgs(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 86)
- `class FindSourcesArgs(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 102)
- `class CompareSourcesArgs(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 111)
- `class FindFacetsArgs(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 118)
- `class PracticeAvailabilityArgs(_Args)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 122)
- `class Tool` ([source](../../../../../../src/learnloop/instructional/tools.py), line 129)
- `tool_schemas() -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 154) — Every tool's declaration, as ``FIND_PRACTICE_TOOL`` publishes one.
- `validate_arguments(name: str, arguments: Mapping[str, Any]) -> _Args` ([source](../../../../../../src/learnloop/instructional/tools.py), line 162)
- `drop_unknown_ids(vault: LoadedVault, repository: Repository, args: _Args) -> tuple[_Args, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 173) — Unknown facet, LO and hypothesis ids are dropped; each drop is reported.
- `execute_tool(vault: LoadedVault, repository: Repository, name: str, args: _Args, *, caller: CallerContext, injections: Mapping[str, Any] | None=None, clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 399) — Run one validated tool under ``caller``; the model-reader view plus refs.
- `request_tool(vault: LoadedVault, repository: Repository, name: str, arguments: Mapping[str, Any], *, caller: CallerContext, model: str | None=None, prompt_version: str | None=None, refusal: tuple[str, str] | None=None, extra_dropped: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 493) — Validate a request and write its ``request`` row (``refused`` when it may not run).
- `run_requested_tool(vault: LoadedVault, repository: Repository, request_id: str, *, injections: Mapping[str, Any] | None=None, clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 545) — Run a stored request under its stored caller context; writes the ``run`` row.
- `run_tool(vault: LoadedVault, repository: Repository, name: str, arguments: Mapping[str, Any], *, caller: CallerContext, injections: Mapping[str, Any] | None=None, clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 592) — The dispatcher (§10.1): request row, then the run under the same caller.
- `tutor_tools_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/instructional/tools.py), line 612)
- `tutor_tool_requests(vault: LoadedVault, repository: Repository, *, event_id: str, requests: Sequence[Any], model: str | None, prompt_version: str | None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 617) — Validate a tutor answer's requests before anything is shown.
- `offered_tool_requests(repository: Repository, event_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 654) — The offers a tutor answer carried, re-read from their request rows (a recovered response says what the original said).
- `tutor_request_handler(vault: LoadedVault) -> Callable[..., list[dict[str, Any]]] | None` ([source](../../../../../../src/learnloop/instructional/tools.py), line 666) — What the adapters pass to ``ask_question(tool_request_handler=...)``; None when off.

### Module constants

- `TOOL_REQUEST_TASK` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 56)
- `RECORDED_CALLERS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 58)
- `MODEL_CALLERS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 60)
- `EAGER_TOOLS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 62)
- `PROMPT_CHARS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 63)
- `STATEMENT_CHARS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 64)
- `PASSAGE_CHARS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 65)
- `HYPOTHESIS_KINDS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 67)
- `TOOLS` ([src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py), line 136)

### Explicit exports

`__all__` declares:

- `EAGER_TOOLS`
- `HYPOTHESIS_KINDS`
- `TOOLS`
- `TOOL_REQUEST_TASK`
- `ToolArgumentsInvalid`
- `drop_unknown_ids`
- `execute_tool`
- `offered_tool_requests`
- `request_tool`
- `run_requested_tool`
- `run_tool`
- `tool_schemas`
- `tutor_request_handler`
- `tutor_tool_requests`
- `tutor_tools_active`
- `validate_arguments`

## Internal implementation anchors

- `class _Args(BaseModel)` ([source](../../../../../../src/learnloop/instructional/tools.py), line 77)
- `_clip(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/instructional/tools.py), line 230)
- `class _Withhold` ([source](../../../../../../src/learnloop/instructional/tools.py), line 235) — Drops any record whose text reproduces the bound item's answer (G3).
- `_practice_view(vault: LoadedVault, result: Mapping[str, Any], withhold: _Withhold) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 254)
- `_passage(hit: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 310)
- `_model_withheld(vault: LoadedVault, repository: Repository, keys: Sequence[tuple[str, str]], withhold: _Withhold) -> dict[tuple[str, str], str]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 316) — Solution regions and assessment-lane spans, for every caller (§5.3, SC3): a bound item's answer filter is not the only thing a model must not read.
- `_sources_view(vault: LoadedVault, repository: Repository, hits: Any, withhold: _Withhold) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 327)
- `_comparison_view(vault: LoadedVault, repository: Repository, comparison: Any, withhold: _Withhold) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 336)
- `_availability(vault: LoadedVault, repository: Repository, args: PracticeAvailabilityArgs, *, caller: CallerContext, estimator: Any | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/tools.py), line 365)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `ToolArgumentsInvalid`, `drop_unknown_ids`, `run_tool`, `tool_schemas`, `validate_arguments`; statically calls `drop_unknown_ids`, `run_tool`, `tool_schemas`, `validate_arguments`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `ToolArgumentsInvalid`, `request_tool`, `run_requested_tool`; statically calls `request_tool`, `run_requested_tool`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `tutor_request_handler`; statically calls `tutor_request_handler`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `ToolArgumentsInvalid`, `run_requested_tool`; statically calls `run_requested_tool`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `offered_tool_requests`, `tutor_request_handler`; statically calls `offered_tool_requests`, `tutor_request_handler`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `insert_tool_call`, `tool_call`, `tool_calls`; calls `insert_tool_call`, `tool_call`, `tool_calls`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `exercise_region_count`; calls `exercise_region_count`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for_question_event`, `cold_administration_open`, `cold_notes`; calls `caller_for_question_event`, `cold_administration_open`, `cold_notes`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `continuation_cursor`, `propose_practice`; calls `continuation_cursor`, `propose_practice`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`; calls `propose_comparison`, `propose_sources`, `refuse_withheld_comparison`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `HYPOTHESIS_ALIASES`, `REFERENCE_KINDS`, `named_gap_target`; calls `named_gap_target`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `ContinuationMismatch`, `INTENTS`, `IntentUnavailable`, `PracticeConstraints`, `admissible_corpus`, `facet_shortlist`; calls `PracticeConstraints`, `admissible_corpus`, `facet_shortlist`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `MODEL_WITHHELD_ROLES`, `model_reader_withheld`; calls `model_reader_withheld`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `INTENTS`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `answer_leaks_expected`, `span_leaks_expected`; calls `answer_leaks_expected`, `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`, `presented_prompt`; calls `fit_presented_prompt`, `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_the_tutors_comparison_is_kept_only_after_its_press_with_what_it_showed`
- [tests/test_hypothesis_reference_contract.py](../../../../../../tests/test_hypothesis_reference_contract.py) — direct import
  - `test_a_named_gap_runs_through_the_tool_as_what_it_names`
  - `test_schema_valid_references_run_through_the_tool`
- [tests/test_practice_availability.py](../../../../../../tests/test_practice_availability.py) — direct import
  - `test_availability_counts_without_calling_a_model`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_another_way_excludes_what_the_inquirys_offers_showed`
- [tests/test_reader_tutor_offers.py](../../../../../../tests/test_reader_tutor_offers.py) — direct import
  - `test_an_empty_lookup_shows_nothing_and_a_failed_one_runs_again`
- [tests/test_reader_tutor_retrieval.py](../../../../../../tests/test_reader_tutor_retrieval.py) — direct import
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_the_reader_quick_check_and_the_tutors_practice_tool_render_the_instruction`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f2_an_answer_carried_only_by_the_required_method_is_withheld`
  - `test_f5_the_practice_tool_keeps_the_instruction_of_a_long_stem`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_an_opened_offer_records_exposure_that_independence_reads`
  - `test_passages_and_comparisons_are_recorded_when_shown`
- [tests/test_tool_dispatch_policy.py](../../../../../../tests/test_tool_dispatch_policy.py) — direct import
  - `test_a_cold_administration_opened_after_the_request_narrows_the_run`
  - `test_a_cold_administration_refuses_every_tool`
  - `test_a_continuation_with_narrower_filters_is_refused`
  - `test_a_find_practice_tool_result_can_be_continued`
  - `test_a_request_cannot_name_an_item_or_widen_its_policy`
  - `test_each_caller_gets_its_policy_and_both_rows`
- [tests/test_tool_registry.py](../../../../../../tests/test_tool_registry.py) — direct import
  - `test_an_unknown_tool_is_refused`
  - `test_extra_fields_and_a_policy_are_refused`
  - `test_five_tools_publish_strict_schemas_without_a_policy`
  - `test_unknown_ids_are_dropped_and_reported`
- [tests/test_tool_results_withhold_answers.py](../../../../../../tests/test_tool_results_withhold_answers.py) — direct import
  - `test_an_unbound_agent_never_reads_a_solution_block_or_an_exam`
  - `test_no_tool_result_contains_an_expected_answer`
- [tests/test_tutor_tool_requests.py](../../../../../../tests/test_tutor_tool_requests.py) — direct import
  - `test_requests_are_validated_recorded_and_offered`
  - `test_the_switch_restores_s0s_tutor_byte_for_byte`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
  - `test_rw4d_followup_an_agent_callers_comparison_is_not_withheld_as_unresolvable`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains tools within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/tools.py](../../../../../../src/learnloop/instructional/tools.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
