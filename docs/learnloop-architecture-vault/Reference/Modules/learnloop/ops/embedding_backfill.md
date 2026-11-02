---
title: "learnloop.ops.embedding_backfill"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/embedding_backfill.py"
source_paths:
  - "src/learnloop/ops/embedding_backfill.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.embedding_backfill module"
  - "src/learnloop/ops/embedding_backfill.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.embedding_backfill`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.embedding_backfill` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Explicit, bounded embedding work.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/embedding_backfill.py](../../../../../../src/learnloop/ops/embedding_backfill.py) |
| Source lines | 386 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `estimated_tokens(text: str) -> int` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 56) — Conservative UTF-8 byte bound, including coarse-prefix/framing allowance.
- `class BackfillLockBusy(ValueError)` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 131) — Another backfill holds the vault's advisory lock (nothing was sent).
- `backfill_embeddings(loaded: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, recipes: tuple[str, ...] | None=None, batch_size: int=32, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, client_factory: Callable[[], EmbeddingClient] | None=None, extra_records: Sequence[EmbeddingRecord]=(), extra_recipes: Sequence[str]=(), records: Iterable[EmbeddingRecord] | None=None, registry: Mapping[str, EmbeddingRecipe] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 159) — Plan without data changes, or checkpoint successful batches before continuing.

### Module constants

- `TASK_PREFIX` ([src/learnloop/ops/embedding_backfill.py](../../../../../../src/learnloop/ops/embedding_backfill.py), line 29)
- `PRICES_PER_MILLION` ([src/learnloop/ops/embedding_backfill.py](../../../../../../src/learnloop/ops/embedding_backfill.py), line 31)

## Internal implementation anchors

- `class _InvalidEmbeddingResponse(Exception)` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 34) — A paid batch came back unusable; it is reported, never retried or saved.
- `_explicit_records(records, selected) -> list[EmbeddingRecord]` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 42) — Canonical, de-duplicated explicit records of the selected recipes.
- `_identity(record: EmbeddingRecord, model_id: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 61)
- `_pending(sqlite_path: Path, records: list[EmbeddingRecord], model_id: str, dims: int) -> tuple[list[EmbeddingRecord], list[tuple[EmbeddingRecord, np.ndarray]]]` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 69) — Records still to pay for, and records whose exact input is already paid.
- `_materialize(repository: Repository, reusable: list[tuple[EmbeddingRecord, np.ndarray]], model_id: str) -> None` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 113) — Give each content-reused record its own identity row (no paid call).
- `_estimate(records: list[EmbeddingRecord], calls: int, price: float | None) -> SpendEstimate` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 123)
- `_backfill_lock(root: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/ops/embedding_backfill.py), line 140) — Serialize backfills, not learner activity; death releases the OS lock.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `PRICES_PER_MILLION`, `estimated_tokens`; statically calls `estimated_tokens`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `estimated_tokens`; statically calls `estimated_tokens`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `estimated_tokens`; statically calls `estimated_tokens`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `BackfillLockBusy`, `backfill_embeddings`, `estimated_tokens`; statically calls `backfill_embeddings`, `estimated_tokens`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `PRICES_PER_MILLION`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `BackfillLockBusy`, `TASK_PREFIX`, `backfill_embeddings`; statically calls `backfill_embeddings`
- [[Reference/Modules/learnloop_sidecar/handlers/item_text_neighbors|learnloop_sidecar.handlers.item_text_neighbors]] — imports `TASK_PREFIX`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EMBEDDING_PRICES_PER_MILLION`, `EmbeddingClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `observe_model_calls`; calls `content_key`, `observe_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendEstimate`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `get_vector_by_content`, `put_vector`; calls `get_vector`, `get_vector_by_content`, `put_vector`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecipe`, `EmbeddingRecord`, `select_recipes`; calls `select_recipes`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `json`, `math`, `pathlib`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]], [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_embed_uses_the_phase_1_backfill_with_the_t4_registry`
- [tests/test_e0_review_round8.py](../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_the_contract_error_reasons_are_the_production_clients_fixed_messages`
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_already_cancelled_never_constructs_client`
  - `test_caps_refuse_before_client_construction`
  - `test_concurrent_backfill_refused`
  - `test_content_reuse_covers_explicit_extra_and_registry_records`
  - `test_dry_run_does_not_construct_client_or_change_database`
  - `test_invalid_paid_response_keeps_the_report_and_is_not_retried`
  - `test_oversized_text_is_not_silently_truncated`
  - `test_provider_failure_reports_sdk_class_without_its_message`
  - `test_real_embedding_transport_retry_is_bounded_and_receipted`
  - `test_unknown_price_reason_names_the_remedy`
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_backfill_after_apply_reuses_the_vectors_paid_at_ingest`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_item_text_ranks_like_the_store_and_leaves_the_map_geometry_alone`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_r3_f3_one_money_cap_for_the_whole_run`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_an_alternative_embedding_model_takes_an_explicit_price`
  - `test_changed_index_content_voids_an_earlier_evaluation_approval`
  - `test_item_skeleton_vectors_rank_items_only_once_they_cover_every_item`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_student_that_misses_the_time_box_is_late_and_the_others_serve`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_source_retrieval_report_compares_against_todays_substring_search`
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_an_unknown_rewrite_is_planned_at_its_largest_encoding_and_never_found_cached`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_explicit_backfill_records_must_be_canonical_recipe_texts`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains embedding backfill within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/embedding_backfill.py](../../../../../../src/learnloop/ops/embedding_backfill.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
