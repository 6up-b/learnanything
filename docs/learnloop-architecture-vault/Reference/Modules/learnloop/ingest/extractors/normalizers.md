---
title: "learnloop.ingest.extractors.normalizers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/normalizers.py"
source_paths:
  - "src/learnloop/ingest/extractors/normalizers.py"
source_commit: "02c3e6e10f5ca37e16cef05657ee693b33502fb7"
source_commit_timestamp: "2026-07-21T13:26:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.normalizers module"
  - "src/learnloop/ingest/extractors/normalizers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.normalizers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.normalizers` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Trivial IR for non-PDF sources (spec_source_ingestion_v2 §2.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py) |
| Source lines | 412 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `02c3e6e10f5ca37e16cef05657ee693b33502fb7` |
| Commit timestamp | `2026-07-21T13:26:14-04:00` |

## Public API

- `markdown_to_ir(markdown: str, *, title: str | None, extractor_name: str, extractor_version: str='2') -> DocumentIR` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 37) — Build trivial IR from a markdown body: blocks by paragraph, units by top-level heading, with a level-2 (##) fallback when the level-1 structure collapses to a single unit (heading-path section trail, no geometry).
- `captions_to_ir(cues: list[Any], *, title: str | None, extractor_name: str='youtube', extractor_version: str='2') -> DocumentIR` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 210) — Build trivial IR from caption cues: one caption block per cue, one unit covering the transcript's time range (no geometry).
- `transcript_to_ir(cues: list[Any], *, title: str | None, extractor_name: str='transcript', extractor_version: str='1') -> DocumentIR` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 303) — Build IR from parsed transcript cues (``learnloop.ingest.transcripts``).

### Module constants

- `_HEADING_RE` ([src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 29)
- `_TRANSCRIPT_GAP_SECONDS` ([src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 286)
- `_TRANSCRIPT_MIN_SEGMENT_SECONDS` ([src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 287)
- `_TRANSCRIPT_MAX_SEGMENT_SECONDS` ([src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 288)
- `_TRANSCRIPT_BLOCK_CHAR_CAP` ([src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 291)

## Internal implementation anchors

- `_slug(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 32)
- `_units_from_headings(blocks: list[DocumentBlock], *, title: str | None) -> list[DocumentUnit]` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 119)
- `_units_from_level2(blocks: list[DocumentBlock]) -> list[DocumentUnit] | None` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 167) — Derive units from the level-2 (##) section trail.
- `_format_clock(seconds: float) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/normalizers.py), line 294)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `captions_to_ir`, `markdown_to_ir`, `transcript_to_ir`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `classify_block_role`; calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `semantic_hash`; calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `IR_SCHEMA_VERSION`, `block_content_hash`; calls `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `block_content_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_import_snapshots_build_plan_estimate_into_payload`
  - `test_plain_import_performs_no_external_egress`
  - `test_reanchor_flags_unresolved_units_for_review`
  - `test_selection_survives_reextraction_via_reanchor`
- [tests/test_ingest_transcripts.py](../../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_transcript_ir_units_carry_time_range_locators`
- [tests/test_normalizer_units.py](../../../../../../../tests/test_normalizer_units.py) — direct import
  - `test_extractor_version_is_two`
- [tests/test_primed_attempts.py](../../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_feedback_resolves_current_ingest_span_and_filename`
- [tests/test_sidecar_ingest_m3.py](../../../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/normalizers.py](../../../../../../../src/learnloop/ingest/extractors/normalizers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
