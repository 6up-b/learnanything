---
title: "learnloop.db.stores.source_block_fts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/source_block_fts.py"
source_paths:
  - "src/learnloop/db/stores/source_block_fts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.db.stores.source_block_fts module"
  - "src/learnloop/db/stores/source_block_fts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.source_block_fts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.source_block_fts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Keyword (FTS5 BM25) search over source blocks: ``source_block_fts`` (Slice 2 T6).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py) |
| Source lines | 577 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class BlockMatch` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 37)
- `query_terms(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 44) — Distinct lowercased word tokens of ``text`` in order, stopwords removed.
- `match_expression(text: str, *, prefix_last: bool=False) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 58) — A safe FTS5 MATCH expression for free text, or ``None`` when it has no terms.
- `search_blocks(connection: sqlite3.Connection, text: str, *, extraction_ids: Collection[str] | None=None, limit: int=200, prefix_last: bool=False) -> list[BlockMatch]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 75) — BM25-ranked blocks for ``text``, best first, optionally within extractions.
- `phrase_shown_outside(connection: sqlite3.Connection, phrase: str, covered: Callable[[str, str], bool]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 110) — Whether a block ``covered`` doesn't hold shows this contiguous phrase.
- `rebuild_source_block_fts(connection: sqlite3.Connection) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 128) — Replace the whole index from ``source_document_blocks`` (the replayer body).
- `class BlockRow` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 148)
- `section_header_titles(connection: sqlite3.Connection, extraction_id: str) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 169) — ``{extractor block id: header text}`` of one extraction's section headers.
- `extraction_blocks(connection: sqlite3.Connection, extraction_id: str) -> list[BlockRow]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 182) — Every block of one extraction in document order (page furniture included).
- `blocks_by_key(connection: sqlite3.Connection, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], BlockRow]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 191) — The named blocks, keyed ``(extraction_id, span_id)``; missing keys are absent.
- `extraction_fingerprint(connection: sqlite3.Connection, extraction_id: str) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 212) — ``(block count, max rowid)``: changes whenever a run's blocks are replaced.
- `extraction_fingerprints(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> dict[str, tuple[int, int]]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 222) — :func:`extraction_fingerprint` of many extractions in one grouped query (an extraction without blocks is ``(0, 0)``).
- `class AssessmentLink` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 240) — Where one provenance link points: its extraction, locator, source, revision.
- `assessment_link_locators(connection: sqlite3.Connection) -> list[AssessmentLink]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 255) — Every current assessment-lane provenance link (``exercise`` and ``assessment_alignment``), which never enters a teaching context (ING M8 §9.1).
- `entity_link_locators(connection: sqlite3.Connection, entity_type: str, entity_id: str) -> list[AssessmentLink]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 267) — Every provenance link of one entity, whatever its relation or status.
- `teaching_link_locators(connection: sqlite3.Connection) -> list[AssessmentLink]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 282) — Every current teaching-relation link of a learning object, facet or concept.
- `revision_source_ids(connection: sqlite3.Connection, revision_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 294) — ``{revision id: source id}`` for the given revisions.
- `extraction_source_ids(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 308) — ``{extraction id: source id}`` through each run's revision.
- `existing_spans(connection: sqlite3.Connection, keys: Iterable[tuple[str, str]]) -> set[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 324) — Which of ``keys`` (extraction, span) name a block that exists: keys only, never a block's text (RW4d fix round 5: a comparison's contributors are resolved before its protection is checked).
- `spans_with_content_hashes(connection: sqlite3.Connection, extraction_id: str, content_hashes: Collection[str]) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 344) — Span ids of one extraction's blocks whose text hashes to one of ``content_hashes``.
- `block_content_hashes(connection: sqlite3.Connection, extraction_id: str, span_ids: Collection[str]) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 360) — The content hashes of the named blocks of one extraction.
- `source_extraction_ids(connection: sqlite3.Connection, *, source_id: str | None=None, revision_id: str | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 376) — Every extraction run of a source (all its revisions), or of one revision.
- `class UnitRow` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 395)
- `extraction_units(connection: sqlite3.Connection, extraction_id: str) -> list[UnitRow]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 404) — One extraction's units in outline order (no block or asset read).
- `class HintRow` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 432) — One block's role-hint facts, in document order.
  - `key(self) -> tuple[str, str]` (line 443; public)
- `hinted_extraction_ids(connection: sqlite3.Connection, extraction_ids: Iterable[str], hints: Collection[str]) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 447) — The given extractions that have at least one block hinted with ``hints``.
- `extraction_hint_rows(connection: sqlite3.Connection, extraction_id: str) -> list[HintRow]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 467) — One extraction's blocks in document order, with what role hinting reads.
- `lead_regions(rows: Iterable[HintRow], mark: Callable[[HintRow], RegionMark]) -> set[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 484) — The blocks ``mark`` takes, plus each region's body.
- `fts_drift(connection: sqlite3.Connection) -> dict[str, int]` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 508) — How far ``source_block_fts`` has drifted from ``source_document_blocks``.
- `indexed_block_count(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> int` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 532)

### Module constants

- `EXCLUDED_BLOCK_TYPES` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 22)
- `MAX_QUERY_TERMS` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 24)
- `_WORD` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 26)
- `_STOPWORDS` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 28)
- `_BLOCK_COLUMNS` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 159)
- `TEACHING_LINK_ENTITY_TYPES` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 279)
- `REGION_BODY_HINTS` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 426)
- `MAX_REGION_BLOCKS` ([src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 428)

### Explicit exports

`__all__` declares:

- `AssessmentLink`
- `BlockMatch`
- `BlockRow`
- `EXCLUDED_BLOCK_TYPES`
- `HintRow`
- `MAX_QUERY_TERMS`
- `phrase_shown_outside`
- `MAX_REGION_BLOCKS`
- `REGION_BODY_HINTS`
- `TEACHING_LINK_ENTITY_TYPES`
- `UnitRow`
- `assessment_link_locators`
- `block_content_hashes`
- `blocks_by_key`
- `entity_link_locators`
- `extraction_blocks`
- `extraction_fingerprint`
- `extraction_fingerprints`
- `extraction_hint_rows`
- `extraction_source_ids`
- `extraction_units`
- `fts_drift`
- `hinted_extraction_ids`
- `indexed_block_count`
- `lead_regions`
- `match_expression`
- `query_terms`
- `rebuild_source_block_fts`
- `revision_source_ids`
- `search_blocks`
- `section_header_titles`
- `source_extraction_ids`
- `spans_with_content_hashes`
- `teaching_link_locators`

## Internal implementation anchors

- `_block(row) -> BlockRow` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 163)
- `_link(row) -> AssessmentLink` ([source](../../../../../../../src/learnloop/db/stores/source_block_fts.py), line 249)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `phrase_shown_outside`; statically calls `phrase_shown_outside`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `MAX_REGION_BLOCKS`, `REGION_BODY_HINTS`, `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`; statically calls `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `extraction_units`; statically calls `extraction_units`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `search_blocks`; statically calls `search_blocks`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `UnitRow`, `extraction_units`, `source_extraction_ids`; statically calls `extraction_units`, `source_extraction_ids`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `MAX_REGION_BLOCKS`, `REGION_BODY_HINTS`, `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`; statically calls `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`, `extraction_fingerprint`, `extraction_units`, `section_header_titles`; statically calls `extraction_blocks`, `extraction_fingerprint`, `extraction_units`, `section_header_titles`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `BlockRow`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `block_content_hashes`, `blocks_by_key`, `spans_with_content_hashes`; statically calls `block_content_hashes`, `blocks_by_key`, `spans_with_content_hashes`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `blocks_by_key`, `extraction_units`, `search_blocks`; statically calls `blocks_by_key`, `extraction_units`, `search_blocks`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `extraction_units`; statically calls `extraction_units`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `fts_drift`; statically calls `fts_drift`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `existing_spans`, `source_extraction_ids`; statically calls `existing_spans`, `source_extraction_ids`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `block_content_hashes`, `existing_spans`, `extraction_source_ids`; statically calls `block_content_hashes`, `existing_spans`, `extraction_source_ids`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`, `section_header_titles`; statically calls `extraction_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `blocks_by_key`, `search_blocks`; statically calls `blocks_by_key`, `search_blocks`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `AssessmentLink`, `HintRow`, `REGION_BODY_HINTS`, `assessment_link_locators`, `block_content_hashes`, `entity_link_locators`, `extraction_hint_rows`, `extraction_source_ids`, `hinted_extraction_ids`, `lead_regions`, `revision_source_ids`, `section_header_titles`, `source_extraction_ids`, `spans_with_content_hashes`, `teaching_link_locators`; statically calls `AssessmentLink`, `assessment_link_locators`, `block_content_hashes`, `entity_link_locators`, `extraction_hint_rows`, `extraction_source_ids`, `hinted_extraction_ids`, `lead_regions`, `revision_source_ids`, `section_header_titles`, `source_extraction_ids`, `spans_with_content_hashes`, `teaching_link_locators`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `extraction_fingerprints`; statically calls `extraction_fingerprints`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `blocks_by_key`, `extraction_blocks`, `search_blocks`, `section_header_titles`; statically calls `blocks_by_key`, `extraction_blocks`, `search_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `blocks_by_key`, `search_blocks`; statically calls `blocks_by_key`, `search_blocks`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `block_content_hashes`, `blocks_by_key`; statically calls `block_content_hashes`, `blocks_by_key`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `query_terms`; statically calls `query_terms`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `blocks_by_key`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `query_terms`; statically calls `query_terms`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`, `extraction_fingerprint`, `section_header_titles`; statically calls `extraction_blocks`, `extraction_fingerprint`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `extraction_blocks`, `extraction_source_ids`; statically calls `extraction_blocks`, `extraction_source_ids`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `BlockRow`, `blocks_by_key`, `search_blocks`, `section_header_titles`; statically calls `blocks_by_key`, `search_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `extraction_blocks`, `section_header_titles`; statically calls `extraction_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `blocks_by_key`, `section_header_titles`; statically calls `blocks_by_key`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `blocks_by_key`; statically calls `blocks_by_key`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `query_terms`, `section_header_titles`; statically calls `query_terms`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `extraction_blocks`, `section_header_titles`; statically calls `extraction_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_source_block_fts`; statically calls `rebuild_source_block_fts`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`; statically calls `extraction_blocks`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `blocks_by_key`; statically calls `blocks_by_key`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `sqlite3`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] and 35 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_compare_methods.py](../../../../../../../tests/test_compare_methods.py) — direct import
  - `test_book_solution_reads_the_checked_span_ids_and_never_exam_material`
- [tests/test_compare_sources_keep.py](../../../../../../../tests/test_compare_sources_keep.py) — direct import
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
  - `test_slice_2_t6_source_block_recipe_hashes_are_pinned`
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_passage_links.py](../../../../../../../tests/test_passage_links.py) — direct import
  - `test_every_discovered_link_has_a_ledger_verdict_and_a_verified_quote`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_a_cell_names_the_anchor_block_that_holds_its_quote`
  - `test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words`
- [tests/test_source_block_fts.py](../../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_a_delete_never_removes_another_blocks_index_row`
  - `test_queries_are_sanitized_stemmed_scoped_and_ranked`
  - `test_rebuild_reproduces_the_trigger_maintained_index`
  - `test_replacing_a_runs_blocks_replaces_its_index_rows`
- [tests/test_tutor_delivery_fixes.py](../../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_complete_passages_kill_switch_restores_the_judges_900_characters`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/source_block_fts.py](../../../../../../../src/learnloop/db/stores/source_block_fts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
