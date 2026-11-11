---
title: "learnloop.content.sources.source_outline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_outline.py"
source_paths:
  - "src/learnloop/content/sources/source_outline.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.source_outline module"
  - "src/learnloop/content/sources/source_outline.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.source_outline`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_outline` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Deterministic source outline view (spec_source_ingestion_v2 §3, §5.3, §8.6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py) |
| Source lines | 292 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `approx_token_count(text: str) -> int` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 34) — Deterministic approximate token count for a string (chars / 4, §3.1).
- `unit_inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, object]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 57) — Whether a unit already has a cached inventory (ING M4).
- `class OutlineUnit(BaseModel)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 69)
- `class SourceOutline(BaseModel)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 88)
- `build_source_outline(repo: Repository, extraction_id: str) -> SourceOutline` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 106) — Build the deterministic outline for one completed extraction run.
- `title_from_file_name(name: str) -> str` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 211)
- `title_from_local_uri(value: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 221) — A ``file:`` URI as its file name in words, decoded (a source with no display title carries one, from ``Path.as_uri``), or None for anything else: a title, or a web address.
- `resolve_extraction_id(repo: Repository, ref: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 239) — Resolve an extraction / revision / artifact reference to an extraction id.
- `class OutlineNotFound(ValueError)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 291) — The requested extraction run has no persisted IR to outline.

### Module constants

- `_CHARS_PER_TOKEN` ([src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py), line 31)
- `_SIGNAL_ROLES` ([src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py), line 46)

## Internal implementation anchors

- `_structural_signals(blocks) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 166)
- `_unit_health_flags(page_start: int | None, page_end: int | None, health) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 171)
- `_derive_title(artifact, revision, ir: DocumentIR) -> str` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 183) — Deterministic display title from artifact metadata, never an LLM guess.
- `_derive_authors(artifact, revision) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 204) — Authors from artifact metadata.
- `_basename(uri: object) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 231)
- `_completed_top_level(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 270)
- `_latest_completed(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 279)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `build_source_outline`, `resolve_extraction_id`; statically calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `build_source_outline`, `title_from_file_name`, `title_from_local_uri`; statically calls `build_source_outline`, `title_from_file_name`, `title_from_local_uri`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `OutlineUnit`, `build_source_outline`; statically calls `build_source_outline`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `OutlineNotFound`, `build_source_outline`; statically calls `build_source_outline`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `title_from_local_uri`; statically calls `title_from_local_uri`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `title_from_local_uri`; statically calls `title_from_local_uri`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `build_source_outline`; statically calls `build_source_outline`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `OutlineNotFound`, `build_source_outline`, `resolve_extraction_id`; statically calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]] — imports `analyze_extraction_health`; calls `analyze_extraction_health`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `inventory_marker`; calls `inventory_marker`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `normalize_semantic_text`; calls `normalize_semantic_text`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `pathlib`, `re`, `urllib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]], [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] and 29 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_a_book_picked_as_an_exam_in_its_outline_builds_nothing`
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_facet_authority_review.py](../../../../../../../tests/test_facet_authority_review.py) — direct import
- [tests/test_followups_batch7_note_titles.py](../../../../../../../tests/test_followups_batch7_note_titles.py) — direct import
  - `test_a_local_uri_reads_as_its_file_name_in_words`
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_approx_token_count_is_chars_over_four`
  - `test_boundary_override_camelcase_keys_are_normalized`
  - `test_declining_repair_leaves_a_usable_flagged_extraction`
  - `test_outline_determinism_zero_agent_runs`
  - `test_outline_reports_structural_signals_and_token_sizes`
  - `test_selection_survives_reextraction_via_reanchor`
  - `test_unit_selection_persists_and_validates`
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_the_reader_asks_about_a_book_carrying_the_retired_choice`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_select_relevant_units_whole_source_when_small`
- [tests/test_reading_hardening_verify_fixes.py](../../../../../../../tests/test_reading_hardening_verify_fixes.py) — direct import
  - `test_n2_a_retry_time_that_overflows_blocks_no_other_book`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_e1_a_failed_import_of_new_bytes_leaves_the_previous_revision_current`
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_e1_one_tap_repair_for_a_library_already_in_that_state`
  - `test_e1_the_reread_hands_the_import_the_stored_bytes_never_a_store_path`
  - `test_e1_the_reread_reads_the_stored_original_and_reuses_the_revision`
  - `test_every_reference_lands_on_the_same_text_or_is_flagged_never_another_block`
  - `test_f4_a_page_repair_never_becomes_the_next_rereads_scope`
  - `test_f6_an_import_that_reuses_an_older_reading_never_moves_annotations_backward`
  - `test_f7_a_carry_over_that_fails_is_finished_later_never_lost`
  - `test_f7_doctor_fix_state_finishes_a_carry_over_left_owed`
  - `test_f9_a_self_hosted_glm_ocr_reread_is_named_and_priced_as_local`
  - `test_rereview_f10_a_place_is_translated_onto_the_reading_the_reader_has_open`
  - `test_the_reread_keeps_the_page_scope_and_carries_the_selection`
- [tests/test_source_retrieval_search.py](../../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_quick_add_ranks_units_by_their_text_not_only_their_labels`
  - `test_quick_add_with_retrieval_off_plans_exactly_as_before`
- [tests/test_ux_phase1_add_source.py](../../../../../../../tests/test_ux_phase1_add_source.py) — direct import
  - `test_reading_progress_reaches_the_reading_order_build`
- [tests/test_ux_phase1_auto_build.py](../../../../../../../tests/test_ux_phase1_auto_build.py) — direct import
  - `test_auto_build_off_leaves_the_book_readable_only`
  - `test_jumping_ahead_builds_the_chapter_jumped_to`
  - `test_reading_does_nothing_while_auto_build_is_off`
  - `test_reading_into_the_next_chapter_builds_one_chapter_ahead`
- [tests/test_ux_phase1_landing.py](../../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_that_is_exam_material_builds_nothing`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f2_rereview_append_reconciliation_calls_are_admitted_one_by_one`
  - `test_f5_undo_cancels_a_build_still_waiting_to_run`
  - `test_f5_undo_while_a_chapter_builds_keeps_it_from_putting_content_back`
  - `test_f6_failed_chapters_are_built_again_by_build_the_whole_book`
  - `test_f7_a_position_that_waited_across_a_restart_is_acted_on_when_the_library_opens`
  - `test_f7_reading_ahead_while_a_build_runs_is_built_when_it_finishes`
- [tests/test_ux_phase1_round2_review.py](../../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
- [tests/test_ux_phase3_today.py](../../../../../../../tests/test_ux_phase3_today.py) — direct import
  - `test_the_current_reading_is_the_one_the_reader_opens_a_source_on`
- [tests/ux_phase1_landing_helpers.py](../../../../../../../tests/ux_phase1_landing_helpers.py) — direct import
- [tests/ux_phase1_round2_review_helpers.py](../../../../../../../tests/ux_phase1_round2_review_helpers.py) — direct import

## Modification guidance

- Change source outline policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
