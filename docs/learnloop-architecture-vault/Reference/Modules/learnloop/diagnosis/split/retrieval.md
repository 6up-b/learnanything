---
title: "learnloop.diagnosis.split.retrieval"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/retrieval.py"
source_paths:
  - "src/learnloop/diagnosis/split/retrieval.py"
source_commit: "af8676ad77113f6c3c74c4efb7bb820b138a8d66"
source_commit_timestamp: "2026-10-12T11:23:36-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.retrieval module"
  - "src/learnloop/diagnosis/split/retrieval.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.retrieval`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.retrieval` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Hybrid kNN retrieval for the diagnosis context (Slice 1 §9.3–9.4; M1 arm (c)).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py) |
| Source lines | 400 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `af8676ad77113f6c3c74c4efb7bb820b138a8d66` |
| Commit timestamp | `2026-10-12T11:23:36-04:00` |

## Public API

- `divergence_text(*, item_prompt: str, first_divergence_quotes: Iterable[str], error_types: Iterable[str], local_analysis_md: str | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 52)
- `attempt_divergence_text(attempt: HistoryAttempt) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 70)
- `current_divergence_text(current: CurrentAttempt) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 79)
- `content_hash(text: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 94)
- `estimated_embedding_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 98) — Same conservative bound the Phase 1 backfill uses.
- `class EmbeddingHistoryRetriever` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 105) — kNN over ``attempt/divergence`` vectors in one (scratch) database.
  - `__post_init__(self) -> None` (line 118; internal)
  - `model_id(self) -> str` (line 123; public)
  - `_admit(self, purpose: str, tokens: int) -> AbstractContextManager` (line 126; internal)
  - `_embed(self, texts: list[str], prefix: str, purpose: str) -> list[list[float]]` (line 129; internal)
  - `prepare(self, attempts: Sequence[HistoryAttempt]) -> int` (line 137; public) — Embed missing divergences; returns how many were newly embedded.
  - `knn(self, current: CurrentAttempt, candidates: Sequence[HistoryAttempt], *, limit: int) -> RetrievalResult` (line 178; public)
  - `registry_knn(self, current: CurrentAttempt, records: Sequence[RegistryRecord], *, limit: int) -> RegistryShortlist` (line 215; public) — Rank the as-of registry by the current failure (S1.4a shortlist).
- `planned_retrieval_requests(sqlite_path: Path, model_id: str, current: CurrentAttempt, *, registry: Sequence[RegistryRecord]=(), failures: Sequence[HistoryAttempt]=(), seen: set[tuple[str, str, str]] | None=None, batch_size: int=32) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 300) — Upper bound on one diagnosis's embedding requests: (requests, input tokens).

### Module constants

- `RECORD_KIND` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 40)
- `FIELD` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 41)
- `DOCUMENT_PREFIX` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 42)
- `QUERY_PREFIX` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 43)
- `RECIPE_VERSION` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 44)
- `_EXCERPT_CHARS` ([src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py), line 45)

### Explicit exports

`__all__` declares:

- `DOCUMENT_PREFIX`
- `EmbeddingHistoryRetriever`
- `FIELD`
- `QUERY_PREFIX`
- `RECIPE_VERSION`
- `RECORD_KIND`
- `attempt_divergence_text`
- `content_hash`
- `current_divergence_text`
- `divergence_text`
- `estimated_embedding_tokens`
- `planned_retrieval_requests`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `EmbeddingHistoryRetriever`; statically calls `EmbeddingHistoryRetriever`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `attempt_divergence_text`, `content_hash`; statically calls `attempt_divergence_text`, `content_hash`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `EmbeddingHistoryRetriever`, `planned_retrieval_requests`; statically calls `EmbeddingHistoryRetriever`, `planned_retrieval_requests`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `QUERY_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `DOCUMENT_PREFIX`, `QUERY_PREFIX`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `put_vector`, `retrieve`; calls `get_vector`, `put_vector`, `retrieve`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `CurrentAttempt`, `RegistryNeighbor`, `RegistryShortlist`, `RetrievalMatch`, `RetrievalResult`, `registry_key`; calls `RegistryNeighbor`, `RegistryShortlist`, `RetrievalMatch`, `RetrievalResult`, `registry_key`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `MISCONCEPTION_FIELD`, `MISCONCEPTION_KIND`, `TASK_PREFIX`, `misconception_record`; calls `misconception_record`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `HistoryAttempt`, `RegistryRecord`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `hashlib`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]], [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_every_mode_keeps_s3_and_validates_evidence_ids`
  - `test_hybrid_degrades_to_exact_when_embeddings_fail`
  - `test_hybrid_fuses_exact_and_knn_and_records_provenance`
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_database_backed_recipe_hashes_are_pinned`

## Modification guidance

- Change retrieval policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/retrieval.py](../../../../../../../src/learnloop/diagnosis/split/retrieval.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
