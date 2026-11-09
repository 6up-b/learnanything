---
title: "learnloop.diagnosis.split.embeddings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/embeddings.py"
source_paths:
  - "src/learnloop/diagnosis/split/embeddings.py"
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
  - "learnloop.diagnosis.split.embeddings module"
  - "src/learnloop/diagnosis/split/embeddings.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.embeddings`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.embeddings` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: S1.4a/S1.4b embeddings for the diagnoser (Slice 1 §9.3, §9.5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py) |
| Source lines | 416 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `hypothesis_text(row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 67) — Statement + mechanism slug (§9.3).
- `hypothesis_records(repository: Repository, *, attempt_ids: Iterable[str] | None=None) -> list[EmbeddingRecord]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 79) — Current heads of every concrete hypothesis (open-set arms excluded).
- `misconception_record(record_id: str, statement: str) -> EmbeddingRecord | None` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 116) — The ``misconception/statement`` record of one registry entry.
- `misconception_records(repository: Repository) -> list[EmbeddingRecord]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 130) — Durable beliefs plus legacy holding-pen rows (§9.3).
- `divergence_records(vault: LoadedVault, repository: Repository, *, attempt_ids: Iterable[str] | None=None) -> list[EmbeddingRecord]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 148) — ``attempt/divergence`` for blind-graded non-pass attempts (S1.4b).
- `db_records(vault: LoadedVault, repository: Repository, selectors: Sequence[str]) -> list[EmbeddingRecord]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 169) — Records for the DB-backed recipes a backfill selector names.
- `is_db_selector(selector: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 185)
- `backfill_with_db_recipes(loaded: LoadedVault, *, recipes: Sequence[str] | None=None, **kwargs: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 189) — ``learnloop embeddings backfill`` with Slice 1's DB-backed recipes.
- `pending_records(repository: Repository, records: Sequence[EmbeddingRecord], model_id: str) -> list[EmbeddingRecord]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 228)
- `class EmbedResult` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 234)
- `embed_records(client: EmbeddingClient, repository: Repository, records: Sequence[EmbeddingRecord], *, caps: SpendCaps=LIVE_CAPS, batch_size: int=32) -> EmbedResult` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 241) — Embed missing records under a per-job budget; saved batches persist.
- `record_would_merge(repository: Repository, *, diagnosis_id: str | None, attempt_id: str, model_id: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 302) — §9.5: nearest prior hypotheses for each hypothesis this attempt minted.

### Module constants

- `LOG` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 40)
- `TASK_PREFIX` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 42)
- `DB_RECIPES` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 46)
- `WOULD_MERGE_LIMIT` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 47)
- `LIVE_CAPS` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 49)
- `PRICES_PER_MILLION` ([src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 57)

### Explicit exports

`__all__` declares:

- `DB_RECIPES`
- `EmbedResult`
- `LIVE_CAPS`
- `db_records`
- `divergence_records`
- `embed_records`
- `hypothesis_records`
- `hypothesis_text`
- `backfill_with_db_recipes`
- `is_db_selector`
- `misconception_records`
- `pending_records`
- `record_would_merge`

## Internal implementation anchors

- `_record(kind: str, field: str, version: int, record_id: str, text: str) -> EmbeddingRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 60)
- `_identity(record: EmbeddingRecord, model_id: str) -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 217)
- `_hypothesis_rows(repository: Repository, episode_keys: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 286)
- `_facets(row: Mapping[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/embeddings.py), line 295)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `backfill_with_db_recipes`; statically calls `backfill_with_db_recipes`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `TASK_PREFIX`, `hypothesis_records`; statically calls `hypothesis_records`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `TASK_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `HYPOTHESIS_FIELD`, `HYPOTHESIS_KIND`, `HYPOTHESIS_VERSION`, `TASK_PREFIX`, `hypothesis_records`; statically calls `hypothesis_records`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `hypothesis_records`, `pending_records`; statically calls `hypothesis_records`, `pending_records`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `LIVE_CAPS`, `PRICES_PER_MILLION`, `divergence_records`, `embed_records`, `hypothesis_records`, `misconception_records`, `pending_records`, `record_would_merge`; statically calls `divergence_records`, `embed_records`, `hypothesis_records`, `misconception_records`, `pending_records`, `record_would_merge`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `MISCONCEPTION_FIELD`, `MISCONCEPTION_KIND`, `TASK_PREFIX`, `misconception_record`; statically calls `misconception_record`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `MISCONCEPTION_FIELD`, `MISCONCEPTION_KIND`, `misconception_record`; statically calls `misconception_record`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `put_vector`, `retrieve`; calls `get_vector`, `put_vector`, `retrieve`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `live_history_store`; calls `live_history_store`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `attempt_divergence_text`, `content_hash`; calls `attempt_divergence_text`, `content_hash`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/recurrence|learnloop.recurrence]] — imports `recurrence_key`; calls `recurrence_key`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecord`; calls `EmbeddingRecord`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]], [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_embeddings.py](../../../../../../../tests/test_diagnosis_embeddings.py) — direct import
  - `test_backfill_embeds_db_recipes_only_when_named`
  - `test_embed_on_write_is_idempotent_and_logs_would_merge_against_earlier_hypotheses`
- [tests/test_embedding_backfill.py](../../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_content_reuse_covers_explicit_extra_and_registry_records`
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_database_backed_recipe_hashes_are_pinned`

## Modification guidance

- Change embeddings policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/embeddings.py](../../../../../../../src/learnloop/diagnosis/split/embeddings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
