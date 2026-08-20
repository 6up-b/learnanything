---
title: "learnloop.content.synthesis.source_unit_selection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/source_unit_selection.py"
source_paths:
  - "src/learnloop/content/synthesis/source_unit_selection.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.source_unit_selection module"
  - "src/learnloop/content/synthesis/source_unit_selection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.source_unit_selection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.source_unit_selection` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Unit selection persistence with re-anchoring (spec_source_ingestion_v2 §5.3).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py) |
| Source lines | 515 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SelectionValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 32) — A selection or boundary override references units/spans that don't exist.
- `class ReanchoredSelection` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 37)
- `normalize_overrides(boundary_overrides: list[dict] | None) -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 51) — Normalize free-form override dicts to canonical snake_case keys.
- `compute_effective_units(ir: DocumentIR, boundary_overrides: list[dict] | None) -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 84) — Deterministically compute the *effective* unit shape after boundary overrides.
- `effective_scope_groups(ir: DocumentIR, boundary_overrides: list[dict] | None, selected_unit_ids: list[str], *, role_by_unit: Mapping[str, str] | None=None, default_role: str='reference') -> list[dict]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 215) — Project a selected scope through the canonical effective-unit shape.
- `validate_unit_selection(ir: DocumentIR, selected_unit_ids: list[str], boundary_overrides: list[dict] | None=None) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 287) — App-level validation of a selection against its extraction's IR.
- `default_exam_use_modes(unit_ids: list[str], *, held_out_fraction: float=DEFAULT_HELD_OUT_FRACTION) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 322) — Deterministic default: the first ``held_out_fraction`` of units (by sorted id) are held-out evaluation, the rest blueprint_only (§4.2).
- `save_unit_selection(repo: Repository, extraction_id: str, selected_unit_ids: list[str], *, boundary_overrides: list[dict] | None=None, exam_use_modes: dict[str, str] | None=None, exam_paper_metadata: dict | None=None, role_override: str | None=None, clock: Clock | None=None) -> dict` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 332) — Validate and persist a selection for one extraction run.
- `reanchor_units(from_ir: DocumentIR, to_ir: DocumentIR) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 384) — Map each old unit id onto a new unit id (or ``None`` when unresolved).
- `reanchor_selection(from_ir: DocumentIR, to_ir: DocumentIR, selected_unit_ids: list[str], boundary_overrides: list[dict] | None=None) -> ReanchoredSelection` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 436) — Re-anchor a stored selection + overrides onto a fresh extraction (§5.3).
- `reanchor_selection_to(repo: Repository, from_extraction_id: str, to_extraction_id: str, *, clock: Clock | None=None) -> dict` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 465) — Re-anchor the stored selection of ``from`` onto ``to`` and persist it.

### Module constants

- `MERGE_WITH_NEXT` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 27)
- `SPLIT_AT_HEADING` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 28)
- `_OVERRIDE_OPS` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 29)
- `EXAM_USE_MODES` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 316)
- `DEFAULT_EXAM_USE_MODE` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 318)
- `DEFAULT_HELD_OUT_FRACTION` ([src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 319)

## Internal implementation anchors

- `_override_unit_id(override: dict) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 43)
- `_override_at_span(override: dict) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 47)
- `_override_op_by_unit(boundary_overrides: list[dict] | None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 68) — Map unit_id → op for the recognized boundary-override operations.
- `_approx_tokens(blocks: list) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 80)
- `_span_majority_unit(unit, span_result, to_unit_of_span) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py), line 418)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `SelectionValidationError`, `save_unit_selection`; statically calls `save_unit_selection`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `effective_scope_groups`; statically calls `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `effective_scope_groups`; statically calls `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `compute_effective_units`, `effective_scope_groups`; statically calls `compute_effective_units`, `effective_scope_groups`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `compute_effective_units`; statically calls `compute_effective_units`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SelectionValidationError`, `compute_effective_units`, `save_unit_selection`; statically calls `compute_effective_units`, `save_unit_selection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentIR`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `reanchor_spans`; calls `reanchor_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_effective_units.py](../../../../../../../tests/test_effective_units.py) — direct import
  - `test_merge_chain_fuses_three_units`
  - `test_passthrough_no_overrides`
  - `test_split_no_op_without_level2_headings`
  - `test_split_with_intro_blocks`
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_boundary_override_camelcase_keys_are_normalized`
  - `test_reanchor_flags_unresolved_units_for_review`
  - `test_selection_survives_reextraction_via_reanchor`
  - `test_unit_selection_persists_and_validates`
- [tests/test_inventory_merge_parallel.py](../../../../../../../tests/test_inventory_merge_parallel.py) — direct import
  - `test_exam_role_merge_group_does_not_fold`
  - `test_merged_inventory_marker_covers_member_units`
  - `test_merged_units_inventory_as_one_call_and_cache_composite`
  - `test_mixed_role_merge_group_does_not_fold`
  - `test_synthesis_gather_folds_merged_group_once_with_member_fallback`
- [tests/test_source_ingestion_v2lite.py](../../../../../../../tests/test_source_ingestion_v2lite.py) — direct import
  - `test_v2lite_synthesis_respects_persisted_unit_selection`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_exam_use_modes_persist_at_selection`

## Modification guidance

- Change source unit selection policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/source_unit_selection.py](../../../../../../../src/learnloop/content/synthesis/source_unit_selection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
