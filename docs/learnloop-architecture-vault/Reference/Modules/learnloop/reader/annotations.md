---
title: "learnloop.reader.annotations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/annotations.py"
source_paths:
  - "src/learnloop/reader/annotations.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.annotations module"
  - "src/learnloop/reader/annotations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.annotations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.annotations` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Annotation service (spec_p3_reader_integration §4, design B step 3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py) |
| Source lines | 585 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AnnotationError(ValueError)` ([source](../../../../../../src/learnloop/reader/annotations.py), line 35) — Domain error for the annotation service.
- `translate_selection(repository: Repository, *, extraction_id: str, raw_selection: Mapping[str, Any], render_view_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 217) — Translate a raw display-coordinate selection through the crosswalk into ordered source-block anchor segments.
- `append_annotation(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, annotation_type: str, learner_text: str='', what_i_think_is_going_on: str | None=None, translation: Mapping[str, Any], render_view_id: str | None=None, privacy_locality: str='local_private', client_idempotency_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 315) — Create a new annotation (version 1) + its anchor + a ``create`` event.
- `edit_annotation(repository: Repository, *, annotation_id: str, learner_text: str | None=None, what_i_think_is_going_on: str | None=None, annotation_type: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 355) — Append an edited version, carrying the existing anchor forward unchanged.
- `delete_intent_annotation(repository: Repository, *, annotation_id: str, reason: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/annotations.py), line 414) — Deletion is a tombstone disposition event -- never a hard delete (§4.1).
- `reanchor_annotation(repository: Repository, *, annotation_id: str, new_extraction_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 425) — Re-anchor an annotation's segments onto a new extraction.
- `reanchor_annotations_for_source(repository: Repository, *, source_id: str, new_extraction_id: str, review_batch: int=MANUAL_REVIEW_BATCH, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 513) — Re-anchor every annotation on a source onto a new extraction, honoring the review-volume budget (§A.3.5).
- `manual_anchor(repository: Repository, *, annotation_id: str, source_id: str, revision_id: str, extraction_id: str, segments: list[Mapping[str, Any]], clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 547) — Append a learner-supplied manual anchor successor (§4.4 step 6).

### Module constants

- `ALGO_VERSION` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 25)
- `SUBBLOCK_CONFIDENCE_MIN` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 29)
- `MANUAL_REVIEW_BATCH` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 30)
- `ANNOTATION_TYPES` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 32)
- `FUZZY_COVERAGE_MIN` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 56)
- `FUZZY_WINDOW_SLACK` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 57)
- `CONTEXT_SCORE_MIN` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 99)
- `CONTEXT_MARGIN_MIN` ([src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py), line 100)

## Internal implementation anchors

- `_hash(text: str) -> str` ([source](../../../../../../src/learnloop/reader/annotations.py), line 39)
- `_neighbor_hashes(ir: Any, span_id: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 43)
- `_fuzzy_locate(text: str, quote: str) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/reader/annotations.py), line 60) — Tolerant alignment for quotes captured off a *rendered* surface (pdf.js text layer, rendered MathML): rendered glyphs and extraction text disagree wherever the extractor dropped math or stored it as LaTeX, so exact and whitespace-normalized matching both fail.
- `_context_score(text: str, start: int, end: int, prefix: str | None, suffix: str | None) -> float` ([source](../../../../../../src/learnloop/reader/annotations.py), line 103) — Similarity between the extraction text around an occurrence and the rendered-surface context the capture arrived with (0..1).
- `_disambiguate(text: str, candidates: list[tuple[int, int]], prefix: str | None, suffix: str | None) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/reader/annotations.py), line 122) — Pick among several occurrences of the same quote using surrounding context — only on a clear win; otherwise refuse (§3.2).
- `_locate_quote(text: str, quote: str | None, *, prefix: str | None=None, suffix: str | None=None) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/reader/annotations.py), line 143) — Locate a quote in source-block text: exact unique match first, else a unique whitespace-normalized match, else a fuzzy token alignment.
- `_segment_from_block(block: Any, ir: Any, start: int, end: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 192)
- `_anchor_payload(*, source_id: str, revision_id: str, extraction_id: str, render_view_id: str | None, translation: Mapping[str, Any], status: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/annotations.py), line 298)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `translate_selection`; statically calls `translate_selection`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `translate_selection`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `append_annotation`, `delete_intent_annotation`, `edit_annotation`, `manual_anchor`, `reanchor_annotation`, `translate_selection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/math_text|learnloop.content.sources.math_text]] — imports `locate_by_canonical`; calls `locate_by_canonical`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `reanchor_spans`, `reanchor_subblock`; calls `reanchor_spans`, `reanchor_subblock`

### Platform and third-party dependencies

- Standard library: `__future__`, `difflib`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_annotations.py](../../../../../../tests/test_annotations.py) — direct import
  - `test_ambiguous_selection_becomes_needs_reanchor_and_keeps_text`
  - `test_duplicate_quote_uses_context_or_needs_reanchor`
  - `test_duplicate_quote_with_glyph_context_anchors_the_right_occurrence`
  - `test_edit_appends_version_and_delete_is_tombstone`
  - `test_glyph_quote_with_divergent_math_anchors_fuzzy`
  - `test_manual_anchor_appends_successor`
  - `test_marker_rerender_same_extraction_does_not_change_anchors`
  - `test_multi_block_selection_stores_multiple_segments`
  - `test_reanchor_across_reextraction_preserves_old_anchor`
  - `test_removed_block_never_silently_steals_annotation`
  - `test_review_volume_budget_parks_over_budget`
  - `test_single_block_roundtrip_exact_source_text`
  - `test_whitespace_normalized_match_still_requires_uniqueness`
  - `test_whitespace_normalized_quote_still_anchors_exact`
- [tests/test_math_text.py](../../../../../../tests/test_math_text.py) — direct import
  - `test_locate_quote_anchors_unicode_math_onto_latex`
  - `test_locate_quote_exact_match_unaffected`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_annotation_survival_across_reextraction`
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_orphaned_annotation_shows_quote_without_false_attachment`

## Modification guidance

- Change annotations policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/annotations.py](../../../../../../src/learnloop/reader/annotations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
