---
title: "learnloop_sidecar.workbench_protection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/workbench_protection.py"
source_paths:
  - "src/learnloop_sidecar/workbench_protection.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.workbench_protection module"
  - "src/learnloop_sidecar/workbench_protection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.workbench_protection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.workbench_protection` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Passage provenance checked at the workbench's text-bearing destinations.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/workbench_protection.py](../../../../../src/learnloop_sidecar/workbench_protection.py) |
| Source lines | 134 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class PassageSelection(ParamsModel)` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 20)
- `reading_places(extraction_id: str | None, spans: Iterable[str | None]) -> list[tuple[str, str]]` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 25)
- `payload_places(payload: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 32)
- `repeats_protected_text(vault: Any, repository: Any, text: str) -> bool` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 53) — Whether words with no recorded passage repeat exam or held-out material: a run of :data:`QUOTE_RUN_WORDS` words (or, for a shorter quote, all of it) found verbatim in a protected passage.
- `check_placed_quote(vault: Any, repository: Any, origins: list[tuple[str, str]], text: str) -> None` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 77)
- `block_places(vault: Any, repository: Any, block_ids: Iterable[str]) -> list[tuple[str, str]]` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 84)
- `refuse_protected(vault: Any, repository: Any, places: Iterable[tuple[str, str]]) -> None` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 108)
- `check_selection(vault: Any, repository: Any, extraction_id: str, raw: Mapping[str, Any], render_view_id: str | None) -> None` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 113)

### Module constants

- `REFUSAL` ([src/learnloop_sidecar/workbench_protection.py](../../../../../src/learnloop_sidecar/workbench_protection.py), line 17)
- `QUOTE_RUN_WORDS` ([src/learnloop_sidecar/workbench_protection.py](../../../../../src/learnloop_sidecar/workbench_protection.py), line 45)
- `_WORD` ([src/learnloop_sidecar/workbench_protection.py](../../../../../src/learnloop_sidecar/workbench_protection.py), line 46)

## Internal implementation anchors

- `_words(text: str) -> list[str]` ([source](../../../../../src/learnloop_sidecar/workbench_protection.py), line 49)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]] — imports `block_places`, `reading_places`, `refuse_protected`; statically calls `block_places`, `reading_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `payload_places`, `refuse_protected`; statically calls `payload_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `block_places`, `refuse_protected`; statically calls `block_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `block_places`, `refuse_protected`; statically calls `block_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `block_places`, `reading_places`, `refuse_protected`; statically calls `block_places`, `reading_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `reading_places`, `refuse_protected`; statically calls `reading_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `block_places`, `check_placed_quote`, `payload_places`, `reading_places`, `refuse_protected`; statically calls `block_places`, `check_placed_quote`, `payload_places`, `reading_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `block_places`; statically calls `block_places`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `check_selection`, `reading_places`, `refuse_protected`; statically calls `check_selection`, `reading_places`, `refuse_protected`
- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `PassageSelection`, `block_places`, `reading_places`, `refuse_protected`; statically calls `block_places`, `reading_places`, `refuse_protected`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `exam_withheld`; calls `exam_material`, `exam_withheld`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`, `standing_anchors_for_blocks`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `context_blocks`; calls `context_blocks`
- [[Reference/Modules/learnloop/reader/source_identity|learnloop.reader.source_identity]] — imports `selection_span_ids`; calls `selection_span_ids`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]], [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mobile_allowlist.py](../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]]
- [tests/test_reader_rd3_fix_backend.py](../../../../../tests/test_reader_rd3_fix_backend.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]]
- [tests/test_reader_rd3a_companion_ask.py](../../../../../tests/test_reader_rd3a_companion_ask.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]]
- [tests/test_reader_rd0_rpcs.py](../../../../../tests/test_reader_rd0_rpcs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]]
- [tests/test_figure_build_golden.py](../../../../../tests/test_figure_build_golden.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figure_request_records.py](../../../../../tests/test_figure_request_records.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_codex_review.py](../../../../../tests/test_figures_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help.py](../../../../../tests/test_figures_help.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help_codex_review.py](../../../../../tests/test_figures_help_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me.py](../../../../../tests/test_figures_show_me.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me_codex_review.py](../../../../../tests/test_figures_show_me_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/workbench_protection.py](../../../../../src/learnloop_sidecar/workbench_protection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
