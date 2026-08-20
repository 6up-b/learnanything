---
title: "learnloop.content.sources.source_outline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_outline.py"
source_paths:
  - "src/learnloop/content/sources/source_outline.py"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_outline` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Deterministic source outline view (spec_source_ingestion_v2 §3, §5.3, §8.6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py) |
| Source lines | 252 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `approx_token_count(text: str) -> int` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 31) — Deterministic approximate token count for a string (chars / 4, §3.1).
- `unit_inventory_marker(repo: Repository, extraction_id: str, unit_id: str) -> dict[str, object]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 54) — Whether a unit already has a cached inventory (ING M4).
- `class OutlineUnit(BaseModel)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 66)
- `class SourceOutline(BaseModel)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 85)
- `build_source_outline(repo: Repository, extraction_id: str) -> SourceOutline` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 103) — Build the deterministic outline for one completed extraction run.
- `resolve_extraction_id(repo: Repository, ref: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 216) — Resolve an extraction / revision / artifact reference to an extraction id.
- `class OutlineNotFound(ValueError)` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 251) — The requested extraction run has no persisted IR to outline.

### Module constants

- `_CHARS_PER_TOKEN` ([src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py), line 28)
- `_SIGNAL_ROLES` ([src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py), line 43)

## Internal implementation anchors

- `_structural_signals(blocks) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 163)
- `_unit_health_flags(page_start: int | None, page_end: int | None, health) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 168)
- `_derive_title(artifact, revision, ir: DocumentIR) -> str` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 180) — Deterministic display title from artifact metadata, never an LLM guess.
- `_derive_authors(artifact, revision) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 201) — Authors from artifact metadata.
- `_basename(uri: object) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 208)
- `_latest_completed(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/source_outline.py), line 239)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `build_source_outline`, `resolve_extraction_id`; statically calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `OutlineUnit`, `build_source_outline`; statically calls `build_source_outline`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `OutlineNotFound`, `build_source_outline`; statically calls `build_source_outline`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/reader/source_search|learnloop.reader.source_search]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `OutlineNotFound`, `build_source_outline`, `resolve_extraction_id`; statically calls `build_source_outline`, `resolve_extraction_id`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `resolve_extraction_id`; statically calls `resolve_extraction_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/extraction_health|learnloop.content.sources.extraction_health]] — imports `analyze_extraction_health`; calls `analyze_extraction_health`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `inventory_marker`; calls `inventory_marker`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `normalize_semantic_text`; calls `normalize_semantic_text`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]], [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_approx_token_count_is_chars_over_four`
  - `test_boundary_override_camelcase_keys_are_normalized`
  - `test_declining_repair_leaves_a_usable_flagged_extraction`
  - `test_outline_determinism_zero_agent_runs`
  - `test_outline_reports_structural_signals_and_token_sizes`
  - `test_selection_survives_reextraction_via_reanchor`
  - `test_unit_selection_persists_and_validates`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_select_relevant_units_whole_source_when_small`

## Modification guidance

- Change source outline policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_outline.py](../../../../../../../src/learnloop/content/sources/source_outline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
