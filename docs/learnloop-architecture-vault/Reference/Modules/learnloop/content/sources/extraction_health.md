---
title: "learnloop.content.sources.extraction_health"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/extraction_health.py"
source_paths:
  - "src/learnloop/content/sources/extraction_health.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.extraction_health module"
  - "src/learnloop/content/sources/extraction_health.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.extraction_health`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.extraction_health` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Deterministic extraction-health analysis (spec_source_ingestion_v2 §2.5, §5.3).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py) |
| Source lines | 196 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FlaggedPageRange` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 32)
- `class ExtractionHealthReport` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 38)
  - `difficult_page_count(self) -> int` (line 43; public)
  - `as_dict(self) -> dict` (line 46; public)
- `analyze_extraction_health(ir: DocumentIR) -> ExtractionHealthReport` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 57) — Analyze one IR into flagged page ranges with reasons (§2.5).

### Module constants

- `_REPLACEMENT_CHAR` ([src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 24)
- `_IMAGE_BLOCK_TYPES` ([src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 25)
- `_TABLE_BLOCK_TYPES` ([src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 26)
- `_NEAR_EMPTY_TABLE_CHARS` ([src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 27)
- `_LOW_DENSITY_RATIO` ([src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 28)

## Internal implementation anchors

- `_page_reasons(page, blocks, ph, text_counts, methods, pages) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 92)
- `_text_block_count(blocks) -> int` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 123)
- `_method(ph) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 133)
- `_has_heading_discontinuity(blocks) -> bool` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 137)
- `_is_low_density(page, text_counts, pages) -> bool` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 147)
- `_method_differs(page, methods, pages) -> bool` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 157)
- `_neighbors(page, pages) -> list[int]` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 168)
- `_merge_ranges(per_page: dict[int, list[str]]) -> list[FlaggedPageRange]` ([source](../../../../../../../src/learnloop/content/sources/extraction_health.py), line 179) — Merge contiguous flagged pages into ranges, unioning their reasons.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `analyze_extraction_health`; statically calls `analyze_extraction_health`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_declining_repair_leaves_a_usable_flagged_extraction`
  - `test_extraction_health_flags_image_only_and_replacement_chars`
  - `test_extraction_health_flags_method_differs_from_neighbors`

## Modification guidance

- Change extraction health policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/extraction_health.py](../../../../../../../src/learnloop/content/sources/extraction_health.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
