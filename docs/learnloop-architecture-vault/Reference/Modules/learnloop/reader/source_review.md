---
title: "learnloop.reader.source_review"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_review.py"
source_paths:
  - "src/learnloop/reader/source_review.py"
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
  - "learnloop.reader.source_review module"
  - "src/learnloop/reader/source_review.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_review`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_review` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Resolve practice-item source refs into displayable canonical-source sections.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_review.py](../../../../../../src/learnloop/reader/source_review.py) |
| Source lines | 232 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `resolve_source_refs(vault, item, repository=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_review.py), line 35) — Resolve an item's source refs for display.

### Module constants

- `CAPTION_CONTEXT_CUES` ([src/learnloop/reader/source_review.py](../../../../../../src/learnloop/reader/source_review.py), line 30)
- `_DISPLAYABLE_REF_TYPES` ([src/learnloop/reader/source_review.py](../../../../../../src/learnloop/reader/source_review.py), line 32)

## Internal implementation anchors

- `_resolve_block_span_ref(repository, ref, *, kind: str, note, canonical: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/source_review.py), line 81) — Resolve current-ingest ``block_span_v1`` refs from the persisted IR.
- `_base_entry(ref, kind: str | None, note, canonical: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_review.py), line 132)
- `_quote_fallback(ref, *, kind: str | None, note, canonical: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_review.py), line 149)
- `_resolve_text_ref(ref, note, canonical: dict[str, Any], kind: str, chunks: list[SourceChunk]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_review.py), line 156)
- `_resolve_video_ref(ref, note, canonical: dict[str, Any], chunks: list[SourceChunk]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_review.py), line 176)
- `_parse_time_locator_loose(locator: str | None) -> tuple[float, float | None] | None` ([source](../../../../../../src/learnloop/reader/source_review.py), line 213) — ``t=start-end`` -> (start, end); bare ``t=start`` -> (start, None).
- `_parse_cue_range(locator: str) -> tuple[float, float] | None` ([source](../../../../../../src/learnloop/reader/source_review.py), line 228)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `resolve_source_refs`; statically calls `resolve_source_refs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `SourceChunk`, `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`; calls `caption_chunks_for_time_range`, `child_chunks_for_locator`, `chunks_for_note_body`, `locator_hash_for_ref`, `source_youtube_video_id`
- [[Reference/Modules/learnloop/content/sources/source_refs|learnloop.content.sources.source_refs]] — imports `source_ref_presentation`; calls `source_ref_presentation`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_bare_video_timestamp_resolves_single_cue`
  - `test_dangling_locator_falls_back_to_quote`
  - `test_feedback_resolves_current_ingest_span_and_filename`
  - `test_missing_note_falls_back_to_quote`
  - `test_missing_note_resolves_youtube_ingest_identity`
  - `test_non_displayable_ref_types_skipped`
  - `test_resolves_text_locator_to_section`
  - `test_resolves_video_time_range`

## Modification guidance

- Change source review policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_review.py](../../../../../../src/learnloop/reader/source_review.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
