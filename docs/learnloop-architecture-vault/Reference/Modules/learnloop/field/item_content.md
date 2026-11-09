---
title: "learnloop.field.item_content"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/item_content.py"
source_paths:
  - "src/learnloop/field/item_content.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.item_content module"
  - "src/learnloop/field/item_content.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.item_content`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.item_content` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Read-only T8 content index: the text each attempt showed, and its stored vectors.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/item_content.py](../../../../../../src/learnloop/field/item_content.py) |
| Source lines | 174 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `mrl_view(vector: np.ndarray, dimensions: int) -> tuple[float, ...] | None` ([source](../../../../../../src/learnloop/field/item_content.py), line 38) — A fixed projection: the first ``dimensions`` MRL dimensions, L2-normalized.
- `seen_stem_records(connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow]) -> list[EmbeddingRecord]` ([source](../../../../../../src/learnloop/field/item_content.py), line 81) — ``item/stem`` records for the exact text each scored attempt showed.
- `load_content_index(connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow], *, dimensions: int=EMBEDDING_DIMENSIONS) -> tuple[ContentIndex, dict]` ([source](../../../../../../src/learnloop/field/item_content.py), line 101) — Return ``(index, aggregate coverage)`` for these replay rows, in one snapshot.

### Module constants

- `TASK_PREFIX` ([src/learnloop/field/item_content.py](../../../../../../src/learnloop/field/item_content.py), line 29)

## Internal implementation anchors

- `_table_exists(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../src/learnloop/field/item_content.py), line 32)
- `_kcs(loaded: LoadedVault, lo_id: str, item: PracticeItem | None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/item_content.py), line 47)
- `_seen_items(connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow])` ([source](../../../../../../src/learnloop/field/item_content.py), line 59) — Yield ``(row, item revision the attempt showed or None, source)``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `load_content_index`, `seen_stem_records`; statically calls `load_content_index`, `seen_stem_records`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`; calls `get_vector`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `_eligible`; calls `_eligible`
- [[Reference/Modules/learnloop/field/success_head|learnloop.field.success_head]] — imports `AttemptContent`, `ContentIndex`, `EMBEDDING_DIMENSIONS`, `SKELETON_VIEW`, `SOLVER_PANEL`, `STEM_VIEW`; calls `AttemptContent`, `ContentIndex`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`, `EmbeddingRecord`; calls `EmbeddingRecord`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_loader_clears_ambiguous_identities_and_reads_skeletons_for_current_text`
  - `test_loader_reads_phase_5a_skeletons_keyed_by_item_id`
  - `test_loader_uses_the_seen_text_and_never_substitutes_current_vectors`
  - `test_seen_stem_records_follow_the_seen_revision_and_scored_rows`

## Modification guidance

- Make changes here when the responsibility remains item content within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/item_content.py](../../../../../../src/learnloop/field/item_content.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
