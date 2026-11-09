---
title: "learnloop.section_map"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/section_map.py"
source_paths:
  - "src/learnloop/section_map.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.section_map module"
  - "src/learnloop/section_map.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.section_map`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.section_map` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Which learning objects a section or span holds: the Reader's mapping, as a dependency-light leaf.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py) |
| Source lines | 381 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `normalize_text(value: str | None) -> str` ([source](../../../../../src/learnloop/section_map.py), line 31)
- `canonical_note_ids(vault: LoadedVault, artifact: dict[str, Any]) -> set[str]` ([source](../../../../../src/learnloop/section_map.py), line 35) — Resolve legacy note-id provenance to the source-library artifact.
- `span_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str, note_ids: set[str], blocks: list[Any], translator: Any=None, accept_moved: bool=False) -> str | None` ([source](../../../../../src/learnloop/section_map.py), line 58) — The span of the viewed reading a provenance ref names, or None.
- `anchor_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str, note_ids: set[str], blocks: list[Any], translator: Any=None) -> tuple[str, str] | None` ([source](../../../../../src/learnloop/section_map.py), line 79) — ``(span id, "current" | "needs_reanchor")`` for a ref on the viewed reading.
- `extraction_sections(ir: Any) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]` ([source](../../../../../src/learnloop/section_map.py), line 140) — Derive the Reader's guide sections from one extraction's IR.
- `section_id_in_ir(ir: Any, span_id: str) -> str | None` ([source](../../../../../src/learnloop/section_map.py), line 188) — The normalized section of ``ir`` holding one reader span.
- `section_id_for_span(repository: Repository, *, extraction_id: str, span_id: str) -> str | None` ([source](../../../../../src/learnloop/section_map.py), line 196) — Resolve one reader span to its containing normalized section (loads the IR; outside AD).
- `learning_objects_for_span_in_ir(vault: LoadedVault, repository: Repository, ir: Any, *, extraction_id: str, span_id: str) -> list[str]` ([source](../../../../../src/learnloop/section_map.py), line 207) — :func:`learning_objects_for_span` over a given IR.
- `learning_objects_for_span(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str) -> list[str]` ([source](../../../../../src/learnloop/section_map.py), line 224) — Provenance-linked Learning Objects available as promotion targets (loads the IR; outside AD).
- `learning_objects_for_section(vault: LoadedVault, repository: Repository, *, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../src/learnloop/section_map.py), line 239) — Active Learning Objects whose provenance cites spans inside the section (loads the IR; outside AD).
- `learning_objects_for_section_in_ir(vault: LoadedVault, repository: Repository, ir: Any, *, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../src/learnloop/section_map.py), line 259) — Active Learning Objects whose provenance cites spans inside the section of ``ir``.
- `learning_objects_by_section(vault: LoadedVault, repository: Repository, *, extraction_id: str) -> dict[str, list[str]]` ([source](../../../../../src/learnloop/section_map.py), line 319) — Every section of an extraction with its provenance-linked Learning Objects.

### Module constants

- `SPAN_LOCATOR_RE` ([src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py), line 21)
- `_TIME_LOCATOR_RE` ([src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py), line 22)
- `_FURNITURE_TYPES` ([src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py), line 23)
- `ANCHOR_CURRENT` ([src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py), line 75)
- `ANCHOR_MOVED` ([src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py), line 76)

## Internal implementation anchors

- `_extras(value: Any) -> dict[str, Any]` ([source](../../../../../src/learnloop/section_map.py), line 26)
- `_ref_matches_source(ref: SourceRef, source_id: str, note_ids: set[str]) -> bool` ([source](../../../../../src/learnloop/section_map.py), line 49)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `extraction_sections`, `learning_objects_for_section_in_ir`, `learning_objects_for_span_in_ir`; statically calls `extraction_sections`, `learning_objects_for_section_in_ir`, `learning_objects_for_span_in_ir`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `learning_objects_for_section`; statically calls `learning_objects_for_section`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; statically calls `learning_objects_for_section`, `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `ANCHOR_CURRENT`, `ANCHOR_MOVED`, `SPAN_LOCATOR_RE`, `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`, `normalize_text`, `span_for_ref`; statically calls `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`, `normalize_text`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_by_section`, `learning_objects_for_section`, `learning_objects_for_span`, `section_id_for_span`; statically calls `learning_objects_for_section`, `section_id_for_span`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `extraction_sections`; statically calls `extraction_sections`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `SpanTranslator`; calls `SpanTranslator`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]], [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]], [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_ad_raw_document_reads.py](../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_the_raw_loading_wrappers_stay_for_callers_outside_ad`
- [tests/test_rospeed2_section_map.py](../../../../../tests/test_rospeed2_section_map.py) — direct import
  - `test_a_failed_mapping_is_not_held`
  - `test_a_mapping_computed_across_a_source_write_is_not_held`
  - `test_r1_nothing_is_held_outside_or_across_jobs`
  - `test_switched_off_the_map_is_mains_and_reads_nothing_of_the_hold`

## Modification guidance

- Make changes here when the responsibility remains section map within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/section_map.py](../../../../../src/learnloop/section_map.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
