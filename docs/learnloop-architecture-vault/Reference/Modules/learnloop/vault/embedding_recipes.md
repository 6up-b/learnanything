---
title: "learnloop.vault.embedding_recipes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/embedding_recipes.py"
source_paths:
  - "src/learnloop/vault/embedding_recipes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.embedding_recipes module"
  - "src/learnloop/vault/embedding_recipes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.embedding_recipes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.embedding_recipes` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: Declared, versioned recipes for canonical text sent to embedding providers.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/embedding_recipes.py](../../../../../../src/learnloop/vault/embedding_recipes.py) |
| Source lines | 367 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class EmbeddingRecord` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 42)
- `class EmbeddingRecipe` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 51)
  - `name(self) -> str` (line 59; public)
  - `content_hash(self, text: str) -> str` (line 62; public)
  - `records(self, loaded: LoadedVault) -> Iterator[EmbeddingRecord]` (line 71; public)
  - `record(self, record_id: str, text: str) -> EmbeddingRecord` (line 77; public) — One record of this recipe's text, hashed exactly as a backfill would.
- `facet_definition_text(facet: Any) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 100) — Canonical ``facet/definition`` text of a facet model or proposal payload.
- `concept_definition_text(concept: Any) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 122) — Canonical ``concept/definition`` text: the LLM-written definition, not a bare label.
- `learning_object_statement_text(learning_object: Any, concept: Any=None) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 138) — Canonical ``learning_object/statement`` text: title, concept and statement.
- `repair_record_id(text: str) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 160) — A repair text's record id: its own digest, so one text is one record.
- `facet_content_hash(facet: EvidenceFacet) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 196) — Content address of a facet's authored meaning, excluding its provenance.
- `facet_dossier_candidates(loaded: LoadedVault) -> dict[str, list[object]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 210) — Every persisted dossier per non-retired facet's current revision, oldest first.
- `select_recipes(selectors: Iterable[str] | None=None, *, registry: Mapping[str, EmbeddingRecipe] | None=None) -> tuple[EmbeddingRecipe, ...]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 328) — Recipes named ``kind/field``, or every field of a bare ``kind``.
- `embedding_records(loaded: LoadedVault, recipes: Iterable[str] | None=None, *, registry: Mapping[str, EmbeddingRecipe] | None=None) -> list[EmbeddingRecord]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 360)

### Module constants

- `DOSSIER_FIELDS` ([src/learnloop/vault/embedding_recipes.py](../../../../../../src/learnloop/vault/embedding_recipes.py), line 207)
- `EMBEDDING_RECIPES` ([src/learnloop/vault/embedding_recipes.py](../../../../../../src/learnloop/vault/embedding_recipes.py), line 273)

## Internal implementation anchors

- `_value(source: Any, name: str) -> Any` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 86)
- `_text(source: Any, name: str) -> str` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 90)
- `_texts(source: Any, name: str) -> list[str]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 95)
- `_learning_object_statements(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 153)
- `_facet_definitions(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 165)
- `_concept_definitions(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 172)
- `_facet_repairs(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 177)
- `_item_stems(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 190)
- `_dossier_field(field: str) -> Callable[[LoadedVault], Iterator[tuple[str, str]]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 223)
- `_item_skeletons(loaded: LoadedVault) -> Iterator[tuple[str, str]]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 236) — PF-b's persisted LLM skeletons for each item's CURRENT text (Slice 2 §5.4).
- `_registry(*recipes: EmbeddingRecipe) -> Mapping[str, EmbeddingRecipe]` ([source](../../../../../../src/learnloop/vault/embedding_recipes.py), line 266)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `EMBEDDING_RECIPES`, `concept_definition_text`, `facet_definition_text`, `repair_record_id`; statically calls `concept_definition_text`, `facet_definition_text`, `repair_record_id`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `concept_definition_text`; statically calls `concept_definition_text`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `EmbeddingRecord`; statically calls `EmbeddingRecord`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `EmbeddingRecord`; statically calls `EmbeddingRecord`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `EMBEDDING_RECIPES`, `learning_object_statement_text`; statically calls `learning_object_statement_text`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `EMBEDDING_RECIPES`, `EmbeddingRecord`; statically calls `EmbeddingRecord`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `EMBEDDING_RECIPES`, `EmbeddingRecipe`; statically calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `EmbeddingRecipe`, `EmbeddingRecord`, `select_recipes`; statically calls `select_recipes`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `embedding_records`; statically calls `embedding_records`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `facet_content_hash`; statically calls `facet_content_hash`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `DOSSIER_FIELDS`, `EMBEDDING_RECIPES`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `EmbeddingRecipe`; statically calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `EmbeddingRecord`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `EMBEDDING_RECIPES`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `EmbeddingRecipe`, `EmbeddingRecord`; statically calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop_sidecar/handlers/item_text_neighbors|learnloop_sidecar.handlers.item_text_neighbors]] — imports `EMBEDDING_RECIPES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `skeletons_for_hashes`; calls `skeletons_for_hashes`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `dossier_candidates`; calls `dossier_candidates`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `skeleton_content_hash`; calls `skeleton_content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `EvidenceFacet`, `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]], [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_recipes_embed_only_the_model_text_and_stay_out_of_the_default_backfill`
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_content_reuse_covers_explicit_extra_and_registry_records`
  - `test_recipes_are_selected_by_kind_or_by_kind_and_field`
  - `test_recipes_declare_canonical_text_and_hash_only_their_inputs`
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_dossier_recipe_hashes_are_pinned`
  - `test_facet_definition_and_item_stem_hashes_are_pinned`
  - `test_phase_5a_item_skeleton_recipe_hashes_are_pinned`
  - `test_slice_2_t5_recipe_hashes_are_pinned`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_large_lo_embeddings_block_only_and_judge_different_never_groups`
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_candidate_payload_text_hashes_like_the_registry_record`
  - `test_concept_and_repair_recipes_embed_llm_written_definitions`
  - `test_content_addressed_lookup_and_complete_index`
  - `test_ranking_matches_phase_1_retrieval`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_learning_object_recipe_is_canonical_and_active_only`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_dossier_fields_are_embedding_recipes`
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_the_source_recipe_is_never_in_the_default_backfill`
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_explicit_backfill_records_must_be_canonical_recipe_texts`
  - `test_loader_clears_ambiguous_identities_and_reads_skeletons_for_current_text`
  - `test_loader_reads_phase_5a_skeletons_keyed_by_item_id`
  - `test_seen_stem_records_follow_the_seen_revision_and_scored_rows`

## Modification guidance

- Make changes here when the responsibility remains embedding recipes within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/embedding_recipes.py](../../../../../../src/learnloop/vault/embedding_recipes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
