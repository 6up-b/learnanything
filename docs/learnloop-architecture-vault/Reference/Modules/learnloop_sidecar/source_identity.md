---
title: "learnloop_sidecar.source_identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/source_identity.py"
source_paths:
  - "src/learnloop_sidecar/source_identity.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop_sidecar.source_identity module"
  - "src/learnloop_sidecar/source_identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.source_identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.source_identity` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: The sidecar's one call into the Reader's passage-identity guard (Reader CA6b fix round 5): every persisting handler that takes passage ids with a reading calls ``require_identity`` before it writes anything, and a mismatch becomes the typed ``span_extraction_mismatch`` error (no…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/source_identity.py](../../../../../src/learnloop_sidecar/source_identity.py) |
| Source lines | 56 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `require_identity(repository: Any, *, extraction_id: str | None, span_ids: Iterable[str | None]=(), raw_selection: Mapping[str, Any] | None=None, subject_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, span_keys: Iterable[str]=(), exchange_id: str | None=None, render_view_id: str | None=None, annotation_id: str | None=None, reading_span_keys: Iterable[str] | None=None) -> None` ([source](../../../../../src/learnloop_sidecar/source_identity.py), line 13) — Refuse with ``span_extraction_mismatch`` unless the passages (span ids, a raw selection's nodes and region, a preset's subject), the source and revision named, an exchange, and each pin key all belong to the reading.

### Explicit exports

`__all__` declares:

- `require_identity`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `require_identity`; statically calls `require_identity`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `require_identity`; statically calls `require_identity`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `require_identity`; statically calls `require_identity`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `require_identity`; statically calls `require_identity`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `require_identity`; statically calls `require_identity`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/reader/source_identity|learnloop.reader.source_identity]] — imports `module`; calls `require_annotation_source`, `require_exchange_in_extraction`, `require_reading_span_keys`, `require_selection_provenance`, `require_source_identity`, `require_span_keys`, `selection_span_ids`, `subject_span_id`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_figures_codex_review.py](../../../../../tests/test_figures_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help.py](../../../../../tests/test_figures_help.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help_codex_review.py](../../../../../tests/test_figures_help_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me.py](../../../../../tests/test_figures_show_me.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me_codex_review.py](../../../../../tests/test_figures_show_me_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_followups_nov2_figure_provenance.py](../../../../../tests/test_followups_nov2_figure_provenance.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_mobile_allowlist.py](../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_library_ask_review.py](../../../../../tests/test_library_ask_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]]
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]]
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]]
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/source_identity.py](../../../../../src/learnloop_sidecar/source_identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
