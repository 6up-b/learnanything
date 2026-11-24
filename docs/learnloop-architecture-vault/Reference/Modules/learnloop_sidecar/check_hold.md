---
title: "learnloop_sidecar.check_hold"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/check_hold.py"
source_paths:
  - "src/learnloop_sidecar/check_hold.py"
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
  - "learnloop_sidecar.check_hold module"
  - "src/learnloop_sidecar/check_hold.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.check_hold`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.check_hold` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: While an inline check is open (mvp-0.69, spec §12.6.4), work that would show or send what its veils hold waits.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/check_hold.py](../../../../../src/learnloop_sidecar/check_hold.py) |
| Source lines | 47 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `open_check(repository: Any) -> str | None` ([source](../../../../../src/learnloop_sidecar/check_hold.py), line 15) — The open inline administration's token, or None.
- `refuse_while_check_open(repository: Any) -> None` ([source](../../../../../src/learnloop_sidecar/check_hold.py), line 25)
- `drain_after_check(ctx: Any, vault: Any, repository: Any) -> None` ([source](../../../../../src/learnloop_sidecar/check_hold.py), line 32) — After an inline check closes: the pad words held back while it was open are emitted (the reconcile a vault's open runs).

### Explicit exports

`__all__` declares:

- `drain_after_check`
- `open_check`
- `refuse_while_check_open`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `open_check`; statically calls `open_check`
- [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]] — imports `refuse_while_check_open`; statically calls `refuse_while_check_open`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `refuse_while_check_open`; statically calls `refuse_while_check_open`
- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `refuse_while_check_open`; statically calls `refuse_while_check_open`
- [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] — imports `drain_after_check`; statically calls `drain_after_check`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `refuse_while_check_open`; statically calls `refuse_while_check_open`
- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `open_check`; statically calls `open_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/check_administrations|learnloop.db.stores.check_administrations]] — imports `module`; calls `open_administration`, `table_present`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `module`; calls `reconcile`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]], [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_attempt_columns_helpers.py](../../../../../tests/ad1_attempt_columns_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/capture_desktop_helpers.py](../../../../../tests/capture_desktop_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/daily_plan_kill_switch_helpers.py](../../../../../tests/daily_plan_kill_switch_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/device_eligibility_helpers.py](../../../../../tests/device_eligibility_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/facet_reword_paths_helpers.py](../../../../../tests/facet_reword_paths_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/figures_help_helpers.py](../../../../../tests/figures_help_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/followup_fg1d_probe_shadow_helpers.py](../../../../../tests/followup_fg1d_probe_shadow_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/followup_journey_helpers.py](../../../../../tests/followup_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/graph_editor_reads_helpers.py](../../../../../tests/graph_editor_reads_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2a_review_helpers.py](../../../../../tests/hint_h2a_review_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2a_review_round2_helpers.py](../../../../../tests/hint_h2a_review_round2_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2b_review_helpers.py](../../../../../tests/hint_h2b_review_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/check_hold.py](../../../../../src/learnloop_sidecar/check_hold.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
