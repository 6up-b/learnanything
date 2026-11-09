---
title: "learnloop.db.stores.embedding_vectors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/embedding_vectors.py"
source_paths:
  - "src/learnloop/db/stores/embedding_vectors.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.embedding_vectors module"
  - "src/learnloop/db/stores/embedding_vectors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.embedding_vectors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.embedding_vectors` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Vault-local paid vectors and exact retrieval; callers supply current identity.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/embedding_vectors.py](../../../../../../../src/learnloop/db/stores/embedding_vectors.py) |
| Source lines | 276 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class IncompleteEmbeddingIndex(ValueError)` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 22) — The requested model has not embedded the complete current manifest.
- `class EmbeddingMatch` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 27)
- `get_vector(connection: sqlite3.Connection, *, record_kind: str, record_id: str, field: str, content_hash: str, model_id: str, task_prefix: str) -> np.ndarray | None` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 47)
- `get_vector_by_content(connection: sqlite3.Connection, *, record_kind: str, field: str, content_hash: str, model_id: str, task_prefix: str) -> np.ndarray | None` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 57) — Any stored vector of exactly this recipe text, whatever record it was saved for.
- `current_vectors(connection: sqlite3.Connection, *, record_kind: str, field: str, model_id: str, task_prefix: str, expected_records: Mapping[str, str]) -> dict[str, np.ndarray]` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 74) — Vectors for every current record, by identity or else by identical content.
- `put_vector(connection: sqlite3.Connection, *, record_kind: str, record_id: str, field: str, content_hash: str, model_id: str, task_prefix: str, vector: Sequence[float] | np.ndarray, created_at: str | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 104) — Insert once by full identity, preserving the first paid result.
- `retrieve(connection: sqlite3.Connection, *, record_kind: str, field: str, model_id: str, task_prefix: str, query: Sequence[float] | np.ndarray, expected_records: Mapping[str, str], limit: int=10, candidate_ids: Collection[str] | None=None, dimensions: int | None=None) -> list[EmbeddingMatch]` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 126) — Mean-centered cosine over current vectors; exact filters precede ranking.
- `class EmbeddingVectorStore` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 189) — Short transactions for jobs; use module functions for atomic batches.
  - `__init__(self, sqlite_path: Path)` (line 192; internal)
  - `get(self, **identity) -> np.ndarray | None` (line 195; public)
  - `contains(self, **identity) -> bool` (line 201; public)
  - `put(self, **values) -> str` (line 204; public)
  - `retrieve(self, **query) -> list[EmbeddingMatch]` (line 208; public)
- `nearest_among_current(connection: sqlite3.Connection, *, record_kind: str, field: str, model_id: str, task_prefix: str, expected_records: Mapping[str, str], limit: int) -> dict[str, list[EmbeddingMatch]]` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 213) — Each current record's top ``limit`` neighbours among the other current ones.
- `current_records_by_model(connection: sqlite3.Connection, *, record_kind: str, field: str, task_prefix: str, expected_records: Mapping[str, str]) -> dict[str, frozenset[str]]` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 258) — Per stored model, the records of ``expected_records`` whose vector is current.

## Internal implementation anchors

- `_vector(value: Sequence[float] | np.ndarray) -> np.ndarray` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 33)
- `_unit_rows(matrix: np.ndarray) -> np.ndarray` ([source](../../../../../../../src/learnloop/db/stores/embedding_vectors.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `IncompleteEmbeddingIndex`, `current_vectors`, `get_vector_by_content`, `put_vector`; statically calls `current_vectors`, `get_vector_by_content`, `put_vector`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `get_vector`, `retrieve`; statically calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `get_vector`; statically calls `get_vector`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `put_vector`; statically calls `put_vector`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `get_vector`, `put_vector`, `retrieve`; statically calls `get_vector`, `put_vector`, `retrieve`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `get_vector`, `put_vector`, `retrieve`; statically calls `get_vector`, `put_vector`, `retrieve`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `get_vector`, `put_vector`; statically calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `get_vector`; statically calls `get_vector`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `current_records_by_model`; statically calls `current_records_by_model`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `EmbeddingMatch`, `get_vector`, `retrieve`; statically calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `get_vector`, `get_vector_by_content`, `put_vector`; statically calls `get_vector`, `get_vector_by_content`, `put_vector`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `get_vector`, `retrieve`; statically calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `get_vector`, `put_vector`; statically calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `retrieve`; statically calls `retrieve`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `put_vector`; statically calls `put_vector`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `get_vector`, `put_vector`; statically calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `IncompleteEmbeddingIndex`, `get_vector`, `retrieve`; statically calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `retrieve`; statically calls `retrieve`
- [[Reference/Modules/learnloop_sidecar/handlers/item_text_neighbors|learnloop_sidecar.handlers.item_text_neighbors]] — imports `current_records_by_model`, `nearest_among_current`; statically calls `current_records_by_model`, `nearest_among_current`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `pathlib`, `sqlite3`, `uuid`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
- [tests/test_embedding_backfill.py](../../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_content_reuse_covers_explicit_extra_and_registry_records`
- [tests/test_embedding_store.py](../../../../../../../tests/test_embedding_store.py) — direct import
  - `test_client_agnostic_storage_and_prefix_isolation`
  - `test_current_records_by_model_counts_current_identities_per_model`
  - `test_dimensions_fixed_per_model`
  - `test_empty_and_zero_centered_retrieval`
  - `test_exact_centered_retrieval_is_model_and_revision_isolated`
  - `test_invalid_mrl_dimensions`
  - `test_invalid_vectors_rejected`
  - `test_mrl_retrieval_truncates_before_centering_and_ranking`
  - `test_mrl_view_ranks_like_vectors_embedded_at_that_width`
  - `test_nearest_among_current_edges`
  - `test_nearest_among_current_ranks_like_retrieve_over_the_covered_records`
  - `test_paid_vector_identity_and_float16`
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_family_proposals.py](../../../../../../../tests/test_family_proposals.py) — direct import
  - `test_large_lo_embeddings_block_only_and_judge_different_never_groups`
- [tests/test_graph_nomination.py](../../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
  - `test_content_addressed_lookup_and_complete_index`
  - `test_ranking_matches_phase_1_retrieval`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_item_text_ranks_like_the_store_and_leaves_the_map_geometry_alone`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide`
- [tests/test_matching.py](../../../../../../../tests/test_matching.py) — direct import
  - `test_a_partially_backfilled_replacement_model_never_ranks`
  - `test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind`
- [tests/test_router_r2c_retrieval.py](../../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_only_matured_decisions_from_another_session_and_plan_are_similar`
- [tests/test_source_retrieval_search.py](../../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_dense_ranking_is_the_phase_1_mean_centred_cosine`
- [tests/test_success_head_cli.py](../../../../../../../tests/test_success_head_cli.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/embedding_vectors.py](../../../../../../../src/learnloop/db/stores/embedding_vectors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
