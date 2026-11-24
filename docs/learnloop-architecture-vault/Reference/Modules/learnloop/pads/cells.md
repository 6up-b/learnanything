---
title: "learnloop.pads.cells"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/cells.py"
source_paths:
  - "src/learnloop/pads/cells.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.cells module"
  - "src/learnloop/pads/cells.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.cells`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.cells` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: A pad's marimo cells (spec §10.4 ``cell``, §11.5): the standing ``cell`` blocks of one pad, in pad order.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/cells.py](../../../../../../src/learnloop/pads/cells.py) |
| Source lines | 29 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `pad_cells(repository: Any, pad_id: str) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/pads/cells.py), line 17) — ``[{block_id, version_id, code, provenance}]`` for the pad's standing cells in pad order; None for no pad.

### Module constants

- `CELL` ([src/learnloop/pads/cells.py](../../../../../../src/learnloop/pads/cells.py), line 14)

### Explicit exports

`__all__` declares:

- `CELL`
- `pad_cells`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `pad_cells`; statically calls `pad_cells`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `heads`, `pad`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]]
- [tests/test_notebook_lessons.py](../../../../../../tests/test_notebook_lessons.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]]
- [tests/test_notebook_rpcs.py](../../../../../../tests/test_notebook_rpcs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]]

## Modification guidance

- Make changes here when the responsibility remains cells within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/cells.py](../../../../../../src/learnloop/pads/cells.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
