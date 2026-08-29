---
title: "learnloop.content.sources.block_health"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/block_health.py"
source_paths:
  - "src/learnloop/content/sources/block_health.py"
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
  - "learnloop.content.sources.block_health module"
  - "src/learnloop/content/sources/block_health.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.block_health`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.block_health` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Per-block extraction health (spec_p3_reader_integration §3.4, design B step 2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py) |
| Source lines | 146 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `analyze_block_health(block: DocumentBlock, page_health: PageHealth | None, *, equation_confidence: float | None=None, analyzer_version: str=ANALYZER_VERSION) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/block_health.py), line 66) — Compute per-block health from a block + its page health.
- `recommended_view(status: str, has_geometry: bool, flags: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/sources/block_health.py), line 137) — §3.4 four behaviors.

### Module constants

- `ANALYZER_VERSION` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 20)
- `EQUATION_LOW_CONFIDENCE_THRESHOLD` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 23)
- `TEXT_DENSITY_ANOMALY_THRESHOLD` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 24)
- `OCR_ANOMALY_THRESHOLD` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 25)
- `REASON_FLAGS` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 28)
- `_PAGE_FLAG_MAP` ([src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py), line 40)

## Internal implementation anchors

- `_ocr_anomaly_fraction(text: str) -> float` ([source](../../../../../../../src/learnloop/content/sources/block_health.py), line 49)
- `_text_density(block: DocumentBlock) -> float | None` ([source](../../../../../../../src/learnloop/content/sources/block_health.py), line 56)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `analyze_block_health`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `PageHealth`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — direct import
  - `test_block_health_statuses_and_recommended_views`

## Modification guidance

- Change block health policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/block_health.py](../../../../../../../src/learnloop/content/sources/block_health.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
