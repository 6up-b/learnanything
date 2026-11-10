---
title: "learnloop.instructional.exercises"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/exercises.py"
source_paths:
  - "src/learnloop/instructional/exercises.py"
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
  - "learnloop.instructional.exercises module"
  - "src/learnloop/instructional/exercises.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.exercises`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.exercises` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: The source-exercise arm of ``find_practice`` (spec_source_practice_and_probes_v1 §7.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/exercises.py](../../../../../../src/learnloop/instructional/exercises.py) |
| Source lines | 323 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ExercisePool` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 56) — The arm's candidates for one request, best fused rank first.
  - `describe(self) -> dict[str, Any]` (line 67; public)
- `exercise_label(text: str, page: int | None) -> str` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 72) — "Exercise 4.12" when the lead names one, else the number, else the page.
- `imported_span_keys(vault: LoadedVault, repository: Repository) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 100) — Spans any item already presents: provenance refs, canonical exercises, written imports.
- `exercise_scope(vault: LoadedVault, repository: Repository, learning_object_ids: Sequence[str]) -> Scope` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 133)
- `exercise_region_count(vault: LoadedVault, repository: Repository, learning_object_ids: Sequence[str]=()) -> dict[str, int]` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 138) — Unimported exercise regions in the teaching scope (no search, no model call).
- `exercise_candidates(vault: LoadedVault, repository: Repository, query: str, constraints: Any, *, pool_size: int, embedder: Any | None=None, rewrite_client: Any | None=None, owner_id: str='', deadline: float | None=None, list_depth: int | Mapping[str, int] | None=None, exclude_keys: Sequence[str | Sequence[str]]=(), readmit: Sequence[Mapping[str, Any]] | None=None) -> ExercisePool` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 160) — Up to ``pool_size`` exercise regions for the request (a prompt-size bound).
- `exercise_key(extraction_id: str, span_ids: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 307) — A stable identity for an unimported exercise (ledger ids, receipts, impressions).

### Module constants

- `STATEMENT_CHARS` ([src/learnloop/instructional/exercises.py](../../../../../../src/learnloop/instructional/exercises.py), line 54)

### Explicit exports

`__all__` declares:

- `STATEMENT_CHARS`
- `ExercisePool`
- `ExerciseRegion`
- `exercise_candidates`
- `exercise_key`
- `exercise_label`
- `exercise_regions`
- `exercise_scope`
- `imported_span_keys`

## Internal implementation anchors

- `_ref_keys(ref: Any) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 84)
- `_same_text_keys(connection, keys: set[tuple[str, str]], extraction_ids: Sequence[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 116) — The imported blocks' text in the searched extractions (a re-extraction renumbers spans).
- `_records(connection, repository: Repository, scope: Scope, regions: Sequence[ExerciseRegion]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 237) — The proposal records of admitted regions (statement, label, page, source).
- `_readmitted(vault: LoadedVault, repository: Repository, scope: Scope, pool: ExercisePool, carried: Sequence[Mapping[str, Any]]) -> ExercisePool` ([source](../../../../../../src/learnloop/instructional/exercises.py), line 265) — A continuation's carried exercises, readmitted under the arm's rules now.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `exercise_region_count`; statically calls `exercise_region_count`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `exercise_candidates`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `STATEMENT_CHARS`, `exercise_label`, `imported_span_keys`; statically calls `exercise_label`, `imported_span_keys`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `ExerciseRegion`, `LABEL_RE`, `NUMBER_RE`, `PAGE_FURNITURE`, `exercise_regions`, `starts_exercise`; calls `exercise_regions`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `block_content_hashes`, `blocks_by_key`, `spans_with_content_hashes`; calls `block_content_hashes`, `blocks_by_key`, `spans_with_content_hashes`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `exercise_key`, `imported_regions`; calls `exercise_key`, `imported_regions`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `teaching_scope`; calls `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `POOL_HYBRID_RRF`, `SpanSearch`, `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]], [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]], [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_a_carried_exercise_imported_since_is_not_restored`
  - `test_a_continuation_with_other_constraints_is_refused`
  - `test_an_exposed_item_is_not_proposed_for_a_value_intent`
  - `test_discriminate_values_items_and_bounds_exercises`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_an_import_rechecks_a_stale_proposal_before_any_paid_call`
- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_an_already_imported_exercise_is_dropped`
  - `test_an_exercise_keeps_its_setup_and_its_unnumbered_lines`
  - `test_exercise_labels`
  - `test_exercise_paging_reaches_every_region_through_exhaustion`
  - `test_find_practice_judges_items_and_exercises_in_one_pool`
  - `test_kinds_items_skips_the_arm_and_source_exercises_skips_items`
  - `test_page_furniture_and_empty_blocks_never_form_an_exercise`
  - `test_the_arm_returns_regions_in_the_teaching_scope_only`
  - `test_the_positive_role_filter_keeps_only_effective_exercise_blocks`
  - `test_unjudged_exercises_are_never_proposed`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_long_exercise_opens_on_its_complete_statement_not_the_cards_preview`
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it`
  - `test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_an_exercise_pick_and_a_need_served_are_source_exercise_rows`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_imported_exercise_is_rechecked_for_independence_when_served`
  - `test_an_interactive_import_bounds_the_authored_drafts_own_duration`
  - `test_an_interactive_import_is_validated_against_its_proposal_and_corrected`

## Modification guidance

- Make changes here when the responsibility remains exercises within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/exercises.py](../../../../../../src/learnloop/instructional/exercises.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
