---
title: "learnloop_sidecar.handlers.pads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/pads.py"
source_paths:
  - "src/learnloop_sidecar/handlers/pads.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
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
  - "learnloop_sidecar.handlers.pads module"
  - "src/learnloop_sidecar/handlers/pads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.pads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.pads` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs: scratchpads (spec §3.4, §10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py) |
| Source lines | 80 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class PadGetInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 26)
- `class PadListInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 30)
- `class PadApplyInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 37)
- `pad_get_handler(ctx: SidecarContext, params: PadGetInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 45) — One pad: its metadata, its standing blocks in order (each with its head version) and their links.
- `pad_list_handler(ctx: SidecarContext, params: PadListInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 62) — Pads, most recently changed first, a page at a time: for the library, search and the drain.
- `pad_apply_handler(ctx: SidecarContext, params: PadApplyInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 71) — One batch of ops on one pad: ``{applied_seq, results, heads, pads}``.

### Module constants

- `PAD_RPCS` ([src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 23)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `ProtocolError`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `PadNotFound`, `PadOp`, `apply_pad_ops`, `pad_list`, `pad_view`; calls `apply_pad_ops`, `pad_list`, `pad_view`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `Verbatim`, `versioned`; calls `Verbatim`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `protocol_error`; calls `protocol_error`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd0_rpcs_are_all_of_them`
- [tests/test_reader_rd0_rpcs.py](../../../../../../tests/test_reader_rd0_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
