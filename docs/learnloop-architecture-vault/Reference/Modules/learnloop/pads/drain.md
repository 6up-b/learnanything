---
title: "learnloop.pads.drain"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/drain.py"
source_paths:
  - "src/learnloop/pads/drain.py"
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
  - "learnloop.pads.drain module"
  - "src/learnloop/pads/drain.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.drain`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.drain` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: The desk drain's read (spec §10.12): closing a desk lists the pads it worked on today, and gives before it asks.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/drain.py](../../../../../../src/learnloop/pads/drain.py) |
| Source lines | 65 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `local_day(clock: Any=None) -> str` ([source](../../../../../../src/learnloop/pads/drain.py), line 26)
- `desk_drain(repository: Any, desk_id: str, *, day: str | None=None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/drain.py), line 38) — The pads homed on ``desk_id`` that changed on ``day`` (the learner's local calendar day; today by default).

### Explicit exports

`__all__` declares:

- `desk_drain`
- `local_day`

## Internal implementation anchors

- `_lines(heads: list[dict[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/pads/drain.py), line 17)
- `_day_bounds(day: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/pads/drain.py), line 32)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `desk_drain`; statically calls `desk_drain`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `heads`, `list_pads`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd4_carried_and_proposals.py](../../../../../../tests/test_reader_rd4_carried_and_proposals.py) — direct import
  - `test_the_drain_lists_todays_pads_and_offers_to_carry_a_closing_question`

## Modification guidance

- Make changes here when the responsibility remains drain within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/drain.py](../../../../../../src/learnloop/pads/drain.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
