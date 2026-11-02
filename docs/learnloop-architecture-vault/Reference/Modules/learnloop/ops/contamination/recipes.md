---
title: "learnloop.ops.contamination.recipes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/recipes.py"
source_paths:
  - "src/learnloop/ops/contamination/recipes.py"
source_commit: "21908854ed88d29871e6eafad7cfde70eb708dcb"
source_commit_timestamp: "2026-10-12T12:43:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops.contamination"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.contamination.recipes module"
  - "src/learnloop/ops/contamination/recipes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.recipes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.recipes` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: Declared embedding recipes for Slice 2 T4's contamination record kinds (R3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/recipes.py](../../../../../../../src/learnloop/ops/contamination/recipes.py) |
| Source lines | 146 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `21908854ed88d29871e6eafad7cfde70eb708dcb` |
| Commit timestamp | `2026-10-12T12:43:16-04:00` |

## Public API

- `expected_answer_text(item: PracticeItem) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 28) — The canonical expected answer: authored text, or sorted JSON for a dict.
- `read_only_repository(loaded: LoadedVault) -> Repository | None` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 37) — Attach without migrating; ``None`` before the vault has a database.
- `answered_question_events(repository: Repository) -> list[dict]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 46) — Answered tutor turns T4 scans: item-bound, or in the reader context.
- `assessment_reservations(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 70) — Every assessment reservation, live or closed, with its immutable surface.

### Module constants

- `CONTAMINATION_RECIPES` ([src/learnloop/ops/contamination/recipes.py](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 115)

## Internal implementation anchors

- `_expected_answers(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 56)
- `_question_event_answers(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 62)
- `_assessment_surfaces(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 94)
- `_held_out_exam_spans(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../../src/learnloop/ops/contamination/recipes.py), line 106)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `CONTAMINATION_RECIPES`
- [[Reference/Modules/learnloop/ops/contamination/__init__|learnloop.ops.contamination]] — imports `CONTAMINATION_RECIPES`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `CONTAMINATION_RECIPES`, `answered_question_events`, `assessment_reservations`, `expected_answer_text`; statically calls `answered_question_events`, `assessment_reservations`, `expected_answer_text`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `CONTAMINATION_RECIPES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `held_out_spans`; calls `held_out_spans`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `surface_statement_text`; calls `surface_statement_text`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`, `EmbeddingRecipe`; calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]], [[Reference/Modules/learnloop/ops/contamination/__init__|learnloop.ops.contamination]], [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]], [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
  - `test_cli_embed_dry_run_plans_every_t4_recipe`
  - `test_embed_uses_the_phase_1_backfill_with_the_t4_registry`
  - `test_exam_leakage_shortlists_nearest_held_out_spans_for_the_judge`
  - `test_recipes_embed_only_the_model_text_and_stay_out_of_the_default_backfill`
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_contamination_recipe_hashes_are_pinned`

## Modification guidance

- Make changes here when the responsibility remains recipes within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/recipes.py](../../../../../../../src/learnloop/ops/contamination/recipes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
