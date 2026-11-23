---
title: "learnloop.companion.asks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/companion/asks.py"
source_paths:
  - "src/learnloop/companion/asks.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.companion"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.companion.asks module"
  - "src/learnloop/companion/asks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-companion"
---

# `learnloop.companion.asks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.companion.asks` exists within [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] to own the behavior summarized by its module contract: Where a companion question is asked (spec §8.6): the desk, the surface, the focused window, the selected pad blocks and the desk's goal, read before the question is sent and recorded with the exchange (``companion_exchange_context``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/companion/asks.py](../../../../../../src/learnloop/companion/asks.py) |
| Source lines | 98 |
| Owning package | [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CompanionAskError(ValueError)` ([source](../../../../../../src/learnloop/companion/asks.py), line 28)
  - `__init__(self, code: str, message: str) -> None` (line 29; internal)
- `class AskContext` ([source](../../../../../../src/learnloop/companion/asks.py), line 35)
  - `record(self) -> dict[str, Any]` (line 42; public) — The keyword arguments of ``record_exchange_context`` (besides the exchange).
- `ask_context(repository: Any, *, surface: str, desk_id: str | None, pad_block_ids: list[str] | None, notebook_ref: str | None) -> AskContext` ([source](../../../../../../src/learnloop/companion/asks.py), line 63) — Read and check where the question is asked; refusals raise :class:`CompanionAskError`.

### Module constants

- `ASK_SURFACES` ([src/learnloop/companion/asks.py](../../../../../../src/learnloop/companion/asks.py), line 23)
- `MAX_PAD_BLOCKS` ([src/learnloop/companion/asks.py](../../../../../../src/learnloop/companion/asks.py), line 25)

### Explicit exports

`__all__` declares:

- `ASK_SURFACES`
- `MAX_PAD_BLOCKS`
- `AskContext`
- `CompanionAskError`
- `ask_context`

## Internal implementation anchors

- `_focused_window(connection: Any, desk: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/companion/asks.py), line 49)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]] — imports `AskContext`, `CompanionAskError`, `MAX_PAD_BLOCKS`, `ask_context`; statically calls `ask_context`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/desks|learnloop.db.stores.desks]] — imports `module`; calls `desk`, `window`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd3a_companion_ask.py](../../../../../../tests/test_reader_rd3a_companion_ask.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Make changes here when the responsibility remains asks within learnloop.companion; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/companion/asks.py](../../../../../../src/learnloop/companion/asks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
