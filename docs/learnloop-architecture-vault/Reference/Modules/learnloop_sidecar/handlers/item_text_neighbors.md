---
title: "learnloop_sidecar.handlers.item_text_neighbors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/item_text_neighbors.py"
source_paths:
  - "src/learnloop_sidecar/handlers/item_text_neighbors.py"
source_commit: "9cf5684a9b9f97c5651e6f839e63cf51815251a4"
source_commit_timestamp: "2026-10-12T01:14:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.item_text_neighbors module"
  - "src/learnloop_sidecar/handlers/item_text_neighbors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.item_text_neighbors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.item_text_neighbors` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Item-text neighbours for the knowledge map (Slice 2 T7; display only).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/item_text_neighbors.py](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9cf5684a9b9f97c5651e6f839e63cf51815251a4` |
| Commit timestamp | `2026-10-12T01:14:14-04:00` |

## Public API

- `class ItemTextNeighbors` ([source](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py), line 33) — Per-item ``(neighbour id, similarity)`` lists plus their coverage.
  - `summary(self) -> dict[str, object]` (line 51; public)
- `ranking_model(configured: str, coverage: Mapping[str, frozenset[str]]) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py), line 64) — The model whose stored vectors rank the spokes (Slice 2 §4).
- `item_text_neighbors(vault: LoadedVault, sqlite_path: Path, *, limit: int) -> ItemTextNeighbors` ([source](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py), line 79) — Top ``limit`` item-text neighbours of every item with a current stem vector.

### Module constants

- `_STEM` ([src/learnloop_sidecar/handlers/item_text_neighbors.py](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py), line 29)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `item_text_neighbors`; statically calls `item_text_neighbors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `current_records_by_model`, `nearest_among_current`; calls `current_records_by_model`, `nearest_among_current`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `TASK_PREFIX`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_ranking_model_moves_only_after_a_full_re_embed`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/item_text_neighbors.py](../../../../../../src/learnloop_sidecar/handlers/item_text_neighbors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
