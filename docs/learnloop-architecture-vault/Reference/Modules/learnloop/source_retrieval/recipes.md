---
title: "learnloop.source_retrieval.recipes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/recipes.py"
source_paths:
  - "src/learnloop/source_retrieval/recipes.py"
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
  - "learnloop.source_retrieval.recipes module"
  - "src/learnloop/source_retrieval/recipes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.recipes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.recipes` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The ``source_block/text`` embedding recipe (Slice 2 R3, §12) and its manifests.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py) |
| Source lines | 199 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `block_record_id(extraction_id: str, span_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 53)
- `split_record_id(record_id: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 57)
- `section_path(block: BlockRow, titles: Mapping[str, str] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 65) — The block's section path, each Marker header ref resolved to its text.
- `embeddable(block: BlockRow) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 86)
- `source_block_text(block: BlockRow, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 90) — The canonical embedded text of one block (recipe v1).
- `source_block_passage(block: BlockRow, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 102) — One block as a relevance labeller reads it: the recipe's "Section: <path>" line, then the complete canonical block text.
- `extraction_manifest(connection, sqlite_path: Path, extraction_id: str, fingerprint: tuple[int, int] | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 148) — ``{record_id: content_hash}`` of one extraction's embeddable blocks (cached).
- `scope_manifest(connection, sqlite_path: Path, extraction_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 176)

### Module constants

- `SOURCE_BLOCK_KIND` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 45)
- `SOURCE_BLOCK_FIELD` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 46)
- `SOURCE_BLOCK_RECIPE` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 47)
- `DOC_TASK_PREFIX` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 48)
- `MAX_BLOCK_CHARS` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 49)
- `MIN_BLOCK_CHARS` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 50)
- `MAX_SECTION_TITLE_CHARS` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 62)
- `SOURCE_RETRIEVAL_RECIPES` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 130)
- `_MANIFESTS` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 143)
- `_MANIFEST_LOCK` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 144)
- `_MANIFEST_CACHE_SIZE` ([src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py), line 145)

### Explicit exports

`__all__` declares:

- `DOC_TASK_PREFIX`
- `MAX_BLOCK_CHARS`
- `MIN_BLOCK_CHARS`
- `SOURCE_BLOCK_FIELD`
- `SOURCE_BLOCK_KIND`
- `SOURCE_BLOCK_RECIPE`
- `SOURCE_RETRIEVAL_RECIPES`
- `block_record_id`
- `embeddable`
- `extraction_manifest`
- `scope_manifest`
- `section_path`
- `source_block_passage`
- `source_block_text`
- `split_record_id`

## Internal implementation anchors

- `_source_block_texts(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/recipes.py), line 117)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `SOURCE_RETRIEVAL_RECIPES`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `section_path`; statically calls `section_path`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `split_record_id`; statically calls `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `embeddable`, `source_block_text`; statically calls `embeddable`, `source_block_text`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `extraction_manifest`, `split_record_id`; statically calls `extraction_manifest`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `block_record_id`, `embeddable`, `source_block_passage`, `source_block_text`, `split_record_id`; statically calls `block_record_id`, `embeddable`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `block_record_id`; statically calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `block_record_id`; statically calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `block_record_id`; statically calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `block_record_id`, `section_path`, `split_record_id`; statically calls `block_record_id`, `section_path`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `SOURCE_BLOCK_RECIPE`, `SOURCE_RETRIEVAL_RECIPES`, `block_record_id`, `embeddable`, `source_block_text`; statically calls `block_record_id`, `embeddable`, `source_block_text`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `block_record_id`, `split_record_id`; statically calls `block_record_id`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `block_record_id`; statically calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `SOURCE_BLOCK_RECIPE`, `SOURCE_RETRIEVAL_RECIPES`, `block_record_id`, `source_block_text`; statically calls `block_record_id`, `source_block_text`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `embeddable`, `section_path`, `source_block_text`; statically calls `embeddable`, `section_path`, `source_block_text`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `block_record_id`; statically calls `block_record_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`, `extraction_fingerprint`, `section_header_titles`; calls `extraction_blocks`, `extraction_fingerprint`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecipe`; calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `pathlib`, `threading`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]], [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_retrieval_tutor_helpers.py](../../../../../../tests/source_retrieval_tutor_helpers.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_slice_2_t6_source_block_recipe_hashes_are_pinned`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_student_that_misses_the_time_box_is_late_and_the_others_serve`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`
  - `test_the_serving_checkpoint_is_reevaluated_on_corrected_labels`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
  - `test_typing_searches_reuse_the_coverage_until_the_library_changes`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_dense_ranking_is_the_phase_1_mean_centred_cosine`
  - `test_recipe_text_resolves_section_headers_and_skips_furniture`
  - `test_split_record_id_round_trips`
  - `test_the_source_recipe_is_never_in_the_default_backfill`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_source_retrieval_report_compares_against_todays_substring_search`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_complete_passages_kill_switch_restores_the_judges_900_characters`

## Modification guidance

- Make changes here when the responsibility remains recipes within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/recipes.py](../../../../../../src/learnloop/source_retrieval/recipes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
