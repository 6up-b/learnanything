---
title: "learnloop.local_embeddings.cache"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/cache.py"
source_paths:
  - "src/learnloop/local_embeddings/cache.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.cache module"
  - "src/learnloop/local_embeddings/cache.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.cache`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.cache` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The local space's vector cache (spec_local_contextual_retrieval_v1 §4.4, Q11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/cache.py](../../../../../../src/learnloop/local_embeddings/cache.py) |
| Source lines | 173 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CacheUnreadable(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/cache.py), line 46) — The cache file exists but cannot be read as a vector cache.
- `cache_path(vault_root: Path, space_id: str) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/cache.py), line 50)
- `class VectorCache` ([source](../../../../../../src/learnloop/local_embeddings/cache.py), line 65) — One space's cache file.
  - `__init__(self, path: Path) -> None` (line 68; internal)
  - `exists(self) -> bool` (line 72; public)
  - `_read(self)` (line 75; internal)
  - `present(self, keys: Iterable[str]) -> set[str]` (line 85; public) — Which of ``keys`` have a vector (no vector bytes read).
  - `vectors(self, keys: Iterable[str]) -> dict[str, np.ndarray]` (line 101; public)
  - `meta(self) -> dict[str, Any]` (line 116; public)
  - `report(self) -> dict[str, Any]` (line 123; public)
  - `_writable(self)` (line 136; internal)
  - `write(self, rows: Sequence[Mapping[str, Any]], *, job_id: str, meta: Mapping[str, Any] | None=None) -> int` (line 151; public) — Insert ``{key, extraction_id, span_id, vector, split_mean}`` rows (first write wins).

### Module constants

- `CACHE_DIR` ([src/learnloop/local_embeddings/cache.py](../../../../../../src/learnloop/local_embeddings/cache.py), line 34)
- `_SCHEMA` ([src/learnloop/local_embeddings/cache.py](../../../../../../src/learnloop/local_embeddings/cache.py), line 35)

### Explicit exports

`__all__` declares:

- `CACHE_DIR`
- `CacheUnreadable`
- `VectorCache`
- `cache_path`

## Internal implementation anchors

- `_blob(vector: Sequence[float] | np.ndarray) -> tuple[int, bytes]` ([source](../../../../../../src/learnloop/local_embeddings/cache.py), line 56)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; statically calls `VectorCache`, `cache_path`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; statically calls `VectorCache`, `cache_path`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; statically calls `VectorCache`, `cache_path`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_a_moved_canary_stores_nothing_and_marks_epoch_drift`
  - `test_a_worker_on_another_software_epoch_stores_nothing`
  - `test_the_index_job_caches_both_variants_and_registers_the_spaces`

## Modification guidance

- Make changes here when the responsibility remains cache within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/cache.py](../../../../../../src/learnloop/local_embeddings/cache.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
