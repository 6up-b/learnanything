---
title: "learnloop.source_retrieval.dense"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/dense.py"
source_paths:
  - "src/learnloop/source_retrieval/dense.py"
source_commit: "0fa0ec1b46c210a01cbe5f1a8fe23f1c53d0a3d7"
source_commit_timestamp: "2026-10-13T23:11:35-04:00"
source_worktree_state: "clean"
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
  - "learnloop.source_retrieval.dense module"
  - "src/learnloop/source_retrieval/dense.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.dense`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.dense` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Dense retrieval over stored ``source_block/text`` vectors (no provider call).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py) |
| Source lines | 339 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0fa0ec1b46c210a01cbe5f1a8fe23f1c53d0a3d7` |
| Commit timestamp | `2026-10-13T23:11:35-04:00` |

## Public API

- `class DenseIndex` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 63)
  - `ready(self) -> bool` (line 76; public) — Every block in scope has a vector (the Phase 1 complete-index rule).
  - `usable(self) -> bool` (line 82; public)
  - `describe(self) -> dict[str, Any]` (line 85; public)
  - `rank(self, query: np.ndarray, *, limit: int, allow: Callable[[str], bool] | None=None) -> list[tuple[str, float]]` (line 90; public) — ``(record_id, score)`` best first; ``allow`` filters after centring.
- `clear_cache() -> None` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 137)
- `extraction_coverage(connection, sqlite_path: Path, model_id: str, extraction_id: str) -> tuple[int, int]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 191) — ``(covered, embeddable)`` blocks of one extraction for ``model_id`` (no vector bytes read).
- `dense_coverage(vault: LoadedVault, repository: Repository, scope: Scope) -> DenseIndex` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 268) — The scope's dense status and counts without reading any vector bytes.
- `load_dense_index(vault: LoadedVault, repository: Repository, scope: Scope) -> DenseIndex` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 284) — The scope's dense index over its complete extractions, or a labelled reason.
- `record_keys(record_id: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 334)

### Module constants

- `USABLE` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 58)
- `BACKFILL_HINT` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 59)
- `_CACHE` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 128)
- `_COVERAGE` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 129)
- `_BY_FINGERPRINT` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 131)
- `_CACHE_LOCK` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 132)
- `_CACHE_SIZE` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 133)
- `_COVERAGE_SIZE` ([src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py), line 134)

### Explicit exports

`__all__` declares:

- `BACKFILL_HINT`
- `USABLE`
- `DenseIndex`
- `clear_cache`
- `dense_coverage`
- `extraction_coverage`
- `load_dense_index`
- `record_keys`

## Internal implementation anchors

- `class _Coverage` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 118)
- `_vectors_fingerprint(connection, model_id: str) -> tuple[int, int]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 144) — Changes whenever a source-block vector for the model is added or removed.
- `_covering_rows(connection, *, model_id: str, extraction_id: str, manifest: Mapping[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 158) — The current vector row per manifest record: by identity, else by content.
- `_remember(cheap: tuple[Any, ...], coverage: _Coverage | None, key: tuple[Any, ...]) -> tuple[_Coverage | None, tuple[Any, ...]]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 205)
- `_coverage(connection, sqlite_path: Path, model_id: str, extraction_ids: list[str]) -> tuple[_Coverage | None, tuple[Any, ...]]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 214)
- `_label(coverage: _Coverage) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/dense.py), line 257)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `clear_cache`; statically calls `clear_cache`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `dense_coverage`, `load_dense_index`; statically calls `dense_coverage`, `load_dense_index`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `dense_coverage`; statically calls `dense_coverage`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `DenseIndex`, `load_dense_index`; statically calls `DenseIndex`, `load_dense_index`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `extraction_coverage`; statically calls `extraction_coverage`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_fingerprints`; calls `extraction_fingerprints`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `extraction_manifest`, `split_record_id`; calls `extraction_manifest`, `split_record_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `pathlib`, `threading`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]], [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
  - `test_typing_searches_reuse_the_coverage_until_the_library_changes`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_dense_ranking_is_the_phase_1_mean_centred_cosine`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_the_tutor_records_as_delivered_only_the_spans_it_was_given`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_a_failed_query_hands_its_sources_to_an_available_fallback`
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`
  - `test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook`
- [tests/test_t6_followup_rereview.py](../../../../../../tests/test_t6_followup_rereview.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains dense within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/dense.py](../../../../../../src/learnloop/source_retrieval/dense.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
