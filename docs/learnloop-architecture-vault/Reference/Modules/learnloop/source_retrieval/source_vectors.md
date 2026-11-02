---
title: "learnloop.source_retrieval.source_vectors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/source_vectors.py"
source_paths:
  - "src/learnloop/source_retrieval/source_vectors.py"
source_commit: "c05eae57933f963158a782836b8d6b88af5d80a2"
source_commit_timestamp: "2026-10-24T15:05:22-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.source_retrieval.source_vectors module"
  - "src/learnloop/source_retrieval/source_vectors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.source_vectors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.source_vectors` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Source-block vectors follow extraction (tutor delivery fixes, 2026-10-13).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py) |
| Source lines | 319 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c05eae57933f963158a782836b8d6b88af5d80a2` |
| Commit timestamp | `2026-10-24T15:05:22-04:00` |

## Public API

- `auto_backfill_reason(config: LearnLoopConfig) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 74) — None when a completed extraction queues its source's backfill, else why not.
- `target_extraction(repository: Repository, extraction_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 87) — ``(source id, its current extraction)`` for a completed extraction.
- `backfill_owed(config: LearnLoopConfig, repository: Repository, extraction_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 102) — ``(current extraction, None)`` when a completed ``extraction_id`` owes its source a backfill, else ``(current extraction or None, why not)``.
- `source_block_records(repository: Repository, extraction_id: str) -> list[EmbeddingRecord]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 133) — The ``source_block/text`` records of one extraction (the recipe's texts and hashes).
- `backfill_caps(config: LearnLoopConfig, records: list[EmbeddingRecord], batch_size: int=BATCH_SIZE) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 143) — Caps sized to this extraction (every record, its batches, a retry of the largest), the money bounded by ``embedding.source_backfill_max_cost_usd``.
- `backfill_source_vectors(loaded: LoadedVault, extraction_id: str, *, client_factory: Callable[[], Any] | None=None, cancelled: Callable[[], bool] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 157) — Embed the current extraction of ``extraction_id``'s source (missing vectors only).
- `source_coverage(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 204) — Per source: dense coverage of its current extraction, and whether dense retrieval is effectively on (the switches and at least one complete source).
- `source_spaces_note(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 255) — Doctor's per-space note: the local spaces' cache and canaries, the fallback's switch and coverage, and the feedback receipts' counts.
- `coverage_line(coverage: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 281) — One status line for ``learnloop doctor``'s text output.

### Module constants

- `SOURCE_VECTORS_JOB` ([src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 67)
- `LIVE_JOB_STATUSES` ([src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 69)
- `BATCH_SIZE` ([src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 70)
- `MAX_RETRIES` ([src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py), line 71)

### Explicit exports

`__all__` declares:

- `LIVE_JOB_STATUSES`
- `SOURCE_VECTORS_JOB`
- `auto_backfill_reason`
- `backfill_caps`
- `backfill_owed`
- `backfill_source_vectors`
- `coverage_line`
- `source_block_records`
- `source_coverage`
- `target_extraction`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `coverage_line`, `source_coverage`; statically calls `coverage_line`, `source_coverage`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `LIVE_JOB_STATUSES`, `SOURCE_VECTORS_JOB`, `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`; statically calls `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `source_coverage`; statically calls `source_coverage`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `backfill_source_vectors`, `source_block_records`, `source_coverage`, `target_extraction`; statically calls `backfill_source_vectors`, `source_block_records`, `source_coverage`, `target_extraction`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `BATCH_SIZE`, `backfill_caps`; statically calls `backfill_caps`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_blocks`, `section_header_titles`; calls `extraction_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `BackfillLockBusy`, `backfill_embeddings`, `estimated_tokens`; calls `backfill_embeddings`, `estimated_tokens`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `extraction_coverage`; calls `extraction_coverage`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `coverage`, `fallback_reason`; calls `coverage`, `fallback_reason`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `feedback_summary`; calls `feedback_summary`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `coverage_report`; calls `coverage_report`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `SOURCE_BLOCK_RECIPE`, `SOURCE_RETRIEVAL_RECIPES`, `block_record_id`, `embeddable`, `source_block_text`; calls `block_record_id`, `embeddable`, `source_block_text`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `resolver_active`; calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `windows_by_extraction`; calls `windows_by_extraction`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecord`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_r3_f2_a_switch_turned_off_between_batches_stops_the_embedding`
  - `test_c2b_r3_f3_one_money_cap_for_the_whole_run`
  - `test_c2b_re_f2_embedding_batches_drop_notes_protected_meanwhile`
- [tests/test_source_vector_backfill.py](../../../../../../tests/test_source_vector_backfill.py) — direct import
  - `test_a_backfill_that_cannot_be_queued_fails_the_import_retryably_and_the_retry_queues_it`
  - `test_a_job_queued_before_the_switch_went_off_sends_nothing`
  - `test_a_provider_failure_after_a_saved_batch_fails_retryably_and_the_retry_buys_only_the_rest`
  - `test_a_re_extraction_queues_the_backfill_of_the_new_current_extraction`
  - `test_an_import_queues_the_source_block_backfill_and_its_source_becomes_dense`

## Modification guidance

- Make changes here when the responsibility remains source vectors within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/source_vectors.py](../../../../../../src/learnloop/source_retrieval/source_vectors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
