---
title: "learnloop.ingest.reanchor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/reanchor.py"
source_paths:
  - "src/learnloop/ingest/reanchor.py"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.reanchor module"
  - "src/learnloop/ingest/reanchor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.reanchor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.reanchor` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Deterministic cross-run span re-anchoring (spec_source_ingestion_v2 §2.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/reanchor.py](../../../../../../src/learnloop/ingest/reanchor.py) |
| Source lines | 238 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Public API

- `class SpanAlias` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 25)
- `class ReanchorResult` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 33)
  - `alias_for(self, from_span_id: str) -> SpanAlias | None` (line 37; public)
- `reanchor_spans(from_ir: DocumentIR, to_ir: DocumentIR) -> ReanchorResult` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 41) — Re-anchor every span of ``from_ir`` onto ``to_ir`` deterministically.
- `class SubBlockAnchor` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 138)
- `reanchor_subblock(from_ir: DocumentIR, to_ir: DocumentIR, *, from_span_id: str, quote: str, prefix: str='', suffix: str='', block_result: ReanchorResult | None=None) -> SubBlockAnchor` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 201) — Re-anchor one annotation segment from ``from_ir`` onto ``to_ir``.

### Module constants

- `EXACT_HASH` ([src/learnloop/ingest/reanchor.py](../../../../../../src/learnloop/ingest/reanchor.py), line 19)
- `GEOMETRY_SECTION` ([src/learnloop/ingest/reanchor.py](../../../../../../src/learnloop/ingest/reanchor.py), line 20)
- `MANUAL` ([src/learnloop/ingest/reanchor.py](../../../../../../src/learnloop/ingest/reanchor.py), line 21)

## Internal implementation anchors

- `_neighbor_index(blocks: list[DocumentBlock]) -> dict[str, tuple[str, str]]` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 74)
- `_pick_unique(block: DocumentBlock, candidates: list[DocumentBlock], want_neighbors: tuple[str, str], to_neighbors: dict[str, tuple[str, str]]) -> DocumentBlock | None` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 84)
- `_context_score(block: DocumentBlock, candidate: DocumentBlock, want_neighbors: tuple[str, str], have_neighbors: tuple[str, str]) -> int` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 103)
- `_locate_with_context(text: str, quote: str, prefix: str, suffix: str) -> int | None` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 148) — Among duplicate quote occurrences, pick the one whose surrounding text best matches the stored prefix/suffix.
- `_fuzzy_locate(text: str, quote: str) -> tuple[int, int, float] | None` ([source](../../../../../../src/learnloop/ingest/reanchor.py), line 183) — Bounded fuzzy candidate when the source text changed and the exact quote is gone.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `EXACT_HASH`, `reanchor_spans`; statically calls `reanchor_spans`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `EXACT_HASH`, `reanchor_spans`; statically calls `reanchor_spans`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `reanchor_spans`; statically calls `reanchor_spans`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `reanchor_spans`, `reanchor_subblock`; statically calls `reanchor_spans`, `reanchor_subblock`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentIR`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `difflib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]], [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]], [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]], [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_span_reanchor.py](../../../../../../tests/test_span_reanchor.py) — direct import
  - `test_duplicate_hashes_disambiguate_by_section_and_page`
  - `test_geometry_section_fallback_when_text_changed`
  - `test_reanchor_aliases_persist`
  - `test_still_ambiguous_span_becomes_needs_reanchor`
  - `test_unique_exact_hash_match_wins`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/reanchor.py](../../../../../../src/learnloop/ingest/reanchor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
