---
title: "learnloop.source_retrieval.corpus"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/corpus.py"
source_paths:
  - "src/learnloop/source_retrieval/corpus.py"
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
  - "learnloop.source_retrieval.corpus module"
  - "src/learnloop/source_retrieval/corpus.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.corpus`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.corpus` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Which source text a search covers: current extractions, scopes and exclusions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py) |
| Source lines | 762 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SourceExtraction` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 54)
- `class Scope` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 62)
  - `allows(self, extraction_id: str, span_id: str) -> bool` (line 68; public)
  - `describe(self) -> dict[str, Any]` (line 71; public)
- `current_extractions(repository: Repository) -> dict[str, SourceExtraction]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 87) — Every source artifact's current extraction, keyed by extraction id.
- `library_scope(repository: Repository) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 106) — Today's library search scope: every reader-enabled source, nothing excluded.
- `extraction_scope(repository: Repository, extraction_id: str) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 114)
- `class Exclusions` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 170) — What a teaching context never reads: whole extractions and single spans.
- `teaching_exclusions(vault: LoadedVault, repository: Repository, *, readable_roles: frozenset[str]=frozenset()) -> Exclusions` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 226) — Everything a teaching context never reads, vault-wide.
- `exam_exclusions(vault: LoadedVault, repository: Repository) -> Exclusions` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 258) — Exam material only, by the one predicate (``content.sources.exam_material``): the narrow part of :func:`teaching_exclusions` the canonical-sources paths that read the whole library withhold (tutor pins, ``find_sources`` pools, comparisons); notes, problem sets and solutions keep…
- `source_exam_exclusions(vault: LoadedVault, repository: Repository, *, source_id: str, revision_id: str | None) -> Exclusions` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 268) — The exam material a book's automatic build must leave out (UX Phase 1: a book's scope is planned before its first study map exists), by the one predicate (``content.sources.exam_material``), so there is exactly one exam and held-out test.
- `exam_withheld(vault: LoadedVault, repository: Repository, keys: Iterable[tuple[str, str]]) -> frozenset[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 286) — The keys among ``keys`` that are exam material (the one predicate).
- `assessment_spans(vault: LoadedVault, repository: Repository) -> frozenset[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 293) — The span-level part of :func:`teaching_exclusions` (whole extractions aside).
- `effective_hint(row: HintRow, titles: Mapping[str, str]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 313) — The block's role hint, unless only a heading substring gave it.
- `role_keys(connection, extraction_ids: Iterable[str], roles: Iterable[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 334) — Blocks whose EFFECTIVE role hint is one of ``roles`` (a positive filter).
- `role_proposal_keys(vault: LoadedVault, repository: Repository, extraction_ids: Iterable[str], roles: Iterable[str]) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 356) — Spans a role proposal gives one of ``roles``: ``(confident, low)``.
- `block_roles(connection, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str | None]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 412) — Each block's EFFECTIVE role (:func:`effective_hint`), a solution region's body included: the unhinted text after a "Solution:" lead is ``solution``.
- `model_reader_withheld(vault: LoadedVault, repository: Repository, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 446) — The spans a result returned to a MODEL must drop, each with its reason.
- `exercise_and_solution_spans(repository: Repository, extraction_ids: Iterable[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 491) — Every exercise and solution block of these readings (a solution with the body after its lead), by effective role hint: what an item-bound scope drops (the same rule; curriculum C0a's coverage candidates drop it too).
- `item_exclusions(repository: Repository, item: PracticeItem) -> Exclusions` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 544) — Every passage the practice item is linked to, whatever the relation.
- `teaching_scope(vault: LoadedVault, repository: Repository, learning_object_ids: Iterable[str], *, item_bound: bool=False, item: PracticeItem | None=None) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 609) — The tutor's grounding scope: the LOs' subjects' teaching sources.
- `class Eligibility` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 681) — What one caller may be given: the one effective-eligibility rule.
  - `__init__(self, vault: LoadedVault, repository: Repository, scope: Scope, *, excluded: Iterable[tuple[str, str]]=(), admits: Callable[[tuple[str, str]], bool] | None=None, withheld: SpanKeys | None=None) -> None` (line 702; internal)
  - `__call__(self, keys: Iterable[tuple[str, str]]) -> list[tuple[str, str]]` (line 713; internal) — The eligible keys among ``keys``, in their order, deduplicated.
- `effective_eligibility(vault: LoadedVault, repository: Repository, scope: Scope, *, excluded: Iterable[tuple[str, str]]=(), admits: Callable[[tuple[str, str]], bool] | None=None, withheld: SpanKeys | None=None) -> Eligibility` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 728) — The caller's :class:`Eligibility`: the one rule every "does a stronger candidate remain?" decision reads (fix round 3).

### Module constants

- `ITEM_BOUND_EXCLUDED_ROLE_HINTS` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 160)
- `_REGION_ROLE_HINTS` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 161)
- `_ITEM_LEAD_REGION_HINTS` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 163)
- `_CUED_ROLES` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 166)
- `HELD_OUT_EVALUATION` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 196)
- `MODEL_WITHHELD_ROLES` ([src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py), line 442)

### Explicit exports

`__all__` declares:

- `Eligibility`
- `Exclusions`
- `ITEM_BOUND_EXCLUDED_ROLE_HINTS`
- `Scope`
- `SourceExtraction`
- `MODEL_WITHHELD_ROLES`
- `assessment_spans`
- `block_roles`
- `current_extractions`
- `effective_eligibility`
- `effective_hint`
- `extraction_scope`
- `item_exclusions`
- `library_scope`
- `exam_exclusions`
- `exam_withheld`
- `exercise_and_solution_spans`
- `model_reader_withheld`
- `role_keys`
- `role_proposal_keys`
- `source_exam_exclusions`
- `teaching_exclusions`
- `teaching_scope`

## Internal implementation anchors

- `_title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 76) — The library's display title (the same order the reader search uses).
- `_subjects(vault: LoadedVault, learning_object_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 124)
- `_linked_extractions(vault: LoadedVault, repository: Repository, learning_object_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 133) — Extractions the LOs' (and their facets') teaching provenance cites.
- `_teaches(role: str | None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 177) — A role whose sources may ground teaching: ``semantic_contract`` authority.
- `_withheld_besides_exams(role: str | None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 188) — A role without teaching authority that is not ``exam``: problem sets, notes and unknown roles (exams are the shared predicate's).
- `_link_exclusions(connection, link: AssessmentLink, whole: set[str], spans: set[tuple[str, str]]) -> None` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 199) — An ``exercise`` / ``assessment_alignment`` link's span, else its whole extraction.
- `_heading(row: HintRow, titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 299) — The block's nearest heading, a Marker header ref resolved to its text.
- `_role_hint_exclusions(connection, extraction_ids: Iterable[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 474) — Exercise and solution blocks (a solution with the body after its lead).
- `_ref_spans(extraction_id: str | None, span_ids: Sequence[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 503) — A YAML source ref's ``span_ids``: plain (``s4``) or namespaced (``ext/s4``, ``ext:s4``).
- `_same_text_elsewhere(connection, linked: set[tuple[str, str]]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 521) — The linked blocks' text in every other extraction of the same source.
- `_teaching_standing(vault: LoadedVault, repository: Repository) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/corpus.py), line 589) — Sources (and extractions) with a role: a source-set member, or cited by a learning object's, facet's or concept's teaching-relation link.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `role_keys`; statically calls `role_keys`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `effective_hint`, `extraction_scope`; statically calls `effective_hint`, `extraction_scope`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `source_exam_exclusions`; statically calls `source_exam_exclusions`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `effective_hint`; statically calls `effective_hint`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `exam_exclusions`; statically calls `exam_exclusions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `current_extractions`, `model_reader_withheld`; statically calls `current_extractions`, `model_reader_withheld`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `current_extractions`, `library_scope`; statically calls `current_extractions`, `library_scope`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `item_exclusions`; statically calls `item_exclusions`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `item_exclusions`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `Scope`, `teaching_scope`; statically calls `teaching_scope`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `role_keys`, `teaching_scope`; statically calls `role_keys`, `teaching_scope`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `teaching_scope`; statically calls `teaching_scope`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `teaching_scope`; statically calls `teaching_scope`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `MODEL_WITHHELD_ROLES`, `model_reader_withheld`; statically calls `model_reader_withheld`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `MODEL_WITHHELD_ROLES`, `item_exclusions`; statically calls `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `Scope`, `exam_withheld`, `item_exclusions`; statically calls `Scope`, `exam_withheld`, `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `Scope`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `Scope`, `library_scope`; statically calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `Eligibility`, `Scope`, `block_roles`, `effective_eligibility`, `exam_withheld`, `extraction_scope`, `item_exclusions`, `library_scope`, `teaching_scope`; statically calls `Scope`, `block_roles`, `effective_eligibility`, `exam_withheld`, `extraction_scope`, `item_exclusions`, `library_scope`, `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `block_roles`; statically calls `block_roles`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `Scope`, `library_scope`; statically calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `Scope`, `block_roles`, `effective_eligibility`, `extraction_scope`, `model_reader_withheld`, `teaching_exclusions`; statically calls `Scope`, `block_roles`, `effective_eligibility`, `extraction_scope`, `model_reader_withheld`, `teaching_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `block_roles`, `item_exclusions`; statically calls `block_roles`, `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `block_roles`, `model_reader_withheld`; statically calls `block_roles`, `model_reader_withheld`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `Eligibility`, `Scope`, `effective_eligibility`, `role_keys`, `role_proposal_keys`; statically calls `effective_eligibility`, `role_keys`, `role_proposal_keys`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `Scope`, `SourceExtraction`, `exercise_and_solution_spans`, `library_scope`, `teaching_exclusions`; statically calls `Scope`, `exercise_and_solution_spans`, `library_scope`, `teaching_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `Scope`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `Scope`, `exam_withheld`, `teaching_scope`; statically calls `exam_withheld`, `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `current_extractions`; statically calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `exam_exclusions`, `model_reader_withheld`; statically calls `exam_exclusions`, `model_reader_withheld`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `exam_withheld`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `exam_withheld`, `item_exclusions`, `teaching_exclusions`; statically calls `exam_withheld`, `item_exclusions`, `teaching_exclusions`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `exam_withheld`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `block_roles`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `library_scope`; statically calls `library_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `item_exclusions`; statically calls `item_exclusions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `is_exam_role`, `module`; calls `exam_material`, `exam_withheld`, `is_exam_role`, `role_material`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `role_authority`; calls `role_authority`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`; calls `CitationResolver`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `AssessmentLink`, `HintRow`, `REGION_BODY_HINTS`, `assessment_link_locators`, `block_content_hashes`, `entity_link_locators`, `extraction_hint_rows`, `extraction_source_ids`, `hinted_extraction_ids`, `lead_regions`, `revision_source_ids`, `section_header_titles`, `source_extraction_ids`, `spans_with_content_hashes`, `teaching_link_locators`; calls `AssessmentLink`, `assessment_link_locators`, `block_content_hashes`, `entity_link_locators`, `extraction_hint_rows`, `extraction_source_ids`, `hinted_extraction_ids`, `lead_regions`, `revision_source_ids`, `section_header_titles`, `source_extraction_ids`, `spans_with_content_hashes`, `teaching_link_locators`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `lead_role`, `unit_heading_role`; calls `lead_role`, `unit_heading_role`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `PROPOSAL_KIND_SQL`, `role_keys`; calls `role_keys`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] and 38 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it`
- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — direct import
  - `test_book_solution_reads_the_checked_span_ids_and_never_exam_material`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_a_syllabus_never_teaches_and_is_never_a_coverage_candidate`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_exam_material_in_any_revision_of_an_exam_source_is_exam_to_every_reader`
  - `test_held_out_and_exam_role_picks_count_outside_any_source_set`
  - `test_the_exam_half_of_a_split_unit_is_exam_material_and_its_theory_half_still_teaches`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading`
  - `test_f15_no_reading_order_offers_a_held_back_reading`
  - `test_identity_review_f6_the_kill_switch_restores_the_predecessors_reading_step`
- [tests/test_exam_protection_landing.py](../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_automatic_build_scope_is_the_one_predicate`
- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_the_positive_role_filter_keeps_only_effective_exercise_blocks`
- [tests/test_facet_locks_landing.py](../../../../../../tests/test_facet_locks_landing.py) — direct import
  - `test_a_held_out_split_child_withholds_its_whole_raw_parent`
  - `test_a_held_out_textbook_unit_is_exam_material_to_both_predicates`
  - `test_a_held_out_unit_that_does_not_resolve_withholds_its_whole_extraction`
  - `test_an_exam_members_material_is_exam_to_both_predicates`
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_a_figure_built_from_the_items_own_blocks_never_qualifies`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f1_rereview_a_builds_protection_is_read_on_the_vault_loaded_now`
  - `test_f4_a_build_rechecks_the_protection_before_it_starts`
  - `test_f4_a_cold_items_passage_and_its_neighbours_are_never_prebuilt`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_pass_also_protects_the_stored_plans_open_items`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
- [tests/test_passage_links.py](../../../../../../tests/test_passage_links.py) — direct import
  - `test_roles_are_kept_with_confidence_judge_and_ledger_and_never_exclude`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_2_an_option_that_is_now_the_items_own_passage_or_reproduces_its_answer_is_withheld`
- [tests/test_rw4d_rw3b_composition.py](../../../../../../tests/test_rw4d_rw3b_composition.py) — direct import
  - `test_every_passage_rw4ds_predicate_withholds_is_one_the_cues_never_surface`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_every_logged_learner_question_is_included`
  - `test_search_spans_builds_the_pool_and_ranks_it_dense_first`
  - `test_without_a_complete_dense_index_the_pool_is_todays_hybrid`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_a_unit_override_is_resolved_on_its_reading_and_an_unmarked_reimport_is_held_back_whole`
  - `test_an_assessment_link_that_names_no_block_excludes_its_whole_extraction`
  - `test_an_assessment_link_without_an_extraction_excludes_its_sources_extractions`
  - `test_an_exam_reimport_is_excluded_whatever_revision_the_set_pins`
  - `test_practice_and_feedback_drop_exercise_and_solution_blocks`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
  - `test_a_passage_linked_to_the_item_never_reaches_the_practice_tutor`
  - `test_a_source_in_no_set_never_grounds_the_tutor`
  - `test_an_item_link_into_an_older_run_is_matched_in_the_re_extraction`
  - `test_an_item_link_that_names_no_block_excludes_its_whole_extraction`
  - `test_an_items_yaml_source_ref_is_excluded_without_a_link_row`
  - `test_heading_cues_do_not_drop_teaching_sections_from_practice`
  - `test_the_body_after_an_item_linked_example_lead_is_excluded`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_a_failed_rewrite_degrades_to_the_unrewritten_search`
  - `test_a_metered_rewrite_without_a_price_is_skipped_not_guessed`
  - `test_a_new_import_leaves_meaning_search_on_for_the_embedded_sources`
  - `test_a_query_vector_of_another_width_is_noted_not_ranked`
  - `test_dense_ranking_is_the_phase_1_mean_centred_cosine`
  - `test_only_conceptual_questions_are_rewritten`
  - `test_teaching_scope_excludes_every_assessment_span`
  - `test_with_embeddings_off_the_index_is_not_read_and_nothing_is_embedded`
  - `test_without_a_complete_index_search_is_keyword_only_and_says_so`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_a_failed_query_hands_its_sources_to_an_available_fallback`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`
  - `test_the_fallback_serves_a_source_qwen_does_not_cover`
  - `test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook`
  - `test_the_logged_selection_probability_is_the_resolvers_joint_one`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_cached_verification_is_served_even_when_the_caps_are_spent`
  - `test_every_verification_attempt_is_admitted_under_the_shared_caps`
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_that_is_exam_material_builds_nothing`
  - `test_todays_plan_reads_mains_exam_predicate_for_the_reading_step`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_what_comes_back_is_filtered_and_the_route_stays_first`

## Modification guidance

- Make changes here when the responsibility remains corpus within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/corpus.py](../../../../../../src/learnloop/source_retrieval/corpus.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
