---
title: "learnloop.reader.reader_progression"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_progression.py"
source_paths:
  - "src/learnloop/reader/reader_progression.py"
source_commit: "6df9761722934fe9a15e17c92a3b74cb50b9425c"
source_commit_timestamp: "2026-11-03T19:25:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_progression module"
  - "src/learnloop/reader/reader_progression.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_progression`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_progression` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader-driven progressive practice seeding (reader-first bootstrap).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py) |
| Source lines | 239 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6df9761722934fe9a15e17c92a3b74cb50b9425c` |
| Commit timestamp | `2026-11-03T19:25:26-05:00` |

## Public API

- `source_refs_for_span(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str, learning_object_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 37) — Canonical, path-backed grounding bundles for a selected reader target.
- `section_generation_candidates(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, target_items_per_lo: int=3, max_new_per_lo: int=3) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 61) — LOs in the section that actually need items (dry-run of the expansion plan with the probe gate waived).
- `source_refs_for_section(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str, learning_object_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 103) — Build bounded, proposal-local citation bundles for reader seeding.

### Module constants

- `_SOURCE_BUNDLE_RADIUS` ([src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py), line 33)
- `_MAX_SOURCE_BUNDLES_PER_LO` ([src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py), line 34)

## Internal implementation anchors

- `_merged_context_intervals(anchor_indices: list[int], span_count: int) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/reader/reader_progression.py), line 225)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `learning_objects_for_section`, `learning_objects_for_span`; statically calls `learning_objects_for_section`, `learning_objects_for_span`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `learning_objects_for_section`; statically calls `learning_objects_for_section`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_observations|learnloop.reader.reader_observations]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `learning_objects_by_section`, `learning_objects_for_span`; statically calls `learning_objects_by_section`, `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `learning_objects_by_section`; statically calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `learning_objects_by_section`; statically calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `learning_objects_by_section`; statically calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `learning_objects_for_span`, `source_refs_for_span`; statically calls `learning_objects_for_span`, `source_refs_for_span`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `learning_objects_for_span`, `section_generation_candidates`, `source_refs_for_section`; statically calls `learning_objects_for_span`, `section_generation_candidates`, `source_refs_for_section`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `learning_objects_for_span`; statically calls `learning_objects_for_span`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_practice_expansion_plan`; calls `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `SpanTranslator`; calls `SpanTranslator`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`; calls `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `learning_objects_by_section`, `learning_objects_for_section`, `learning_objects_for_span`, `section_id_for_span`; calls `learning_objects_for_section`, `section_id_for_span`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] and 16 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — direct import
  - `test_a_mixed_reading_gives_no_reading_signal_as_if_deleted`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it`
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_mapped_lo_does_not_suppress_the_attribution`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_the_guide_and_lo_highlights_survive_with_moved_passages_flagged`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it`
  - `test_a_real_missed_prediction_reaches_the_section_through_its_figure`
  - `test_a_session_that_touched_the_lo_only_through_a_figure_is_kept_for_its_prediction`

## Modification guidance

- Change reader progression policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_progression.py](../../../../../../src/learnloop/reader/reader_progression.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
