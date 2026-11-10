---
title: "learnloop_sidecar.logging"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/logging.py"
source_paths:
  - "src/learnloop_sidecar/logging.py"
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
  - "learnloop_sidecar.logging module"
  - "src/learnloop_sidecar/logging.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.logging`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps logging behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `JsonLineFormatter`, `debug_enabled`, `configure_logging`, `log_event`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/logging.py](../../../../../src/learnloop_sidecar/logging.py) |
| Source lines | 107 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class JsonLineFormatter(logging.Formatter)` ([source](../../../../../src/learnloop_sidecar/logging.py), line 22)
  - `format(self, record: logging.LogRecord) -> str` (line 23; public)
- `debug_enabled() -> bool` ([source](../../../../../src/learnloop_sidecar/logging.py), line 39) — True when the sidecar should emit verbose state-update events.
- `configure_logging() -> None` ([source](../../../../../src/learnloop_sidecar/logging.py), line 58)
- `log_event(event: str, *, level: int=logging.DEBUG, **fields: Any) -> None` ([source](../../../../../src/learnloop_sidecar/logging.py), line 86) — Emit a structured sidecar event.

### Module constants

- `EVENT_FIELDS_ATTR` ([src/learnloop_sidecar/logging.py](../../../../../src/learnloop_sidecar/logging.py), line 15)
- `LOG` ([src/learnloop_sidecar/logging.py](../../../../../src/learnloop_sidecar/logging.py), line 17)
- `_TRUTHY` ([src/learnloop_sidecar/logging.py](../../../../../src/learnloop_sidecar/logging.py), line 19)

## Internal implementation anchors

- `_resolve_level() -> int` ([source](../../../../../src/learnloop_sidecar/logging.py), line 51)
- `_show_warning(message, category, filename, lineno, file=None, line=None) -> None` ([source](../../../../../src/learnloop_sidecar/logging.py), line 100)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]] — imports `configure_logging`; statically calls `configure_logging`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `debug_enabled`, `log_event`; statically calls `debug_enabled`, `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `log_event`; statically calls `log_event`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `log_event`; statically calls `log_event`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `current_trace`; calls `current_trace`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `logging`, `os`, `pathlib`, `sys`, `typing`, `warnings`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
  - `test_sidecar_log_events_carry_the_trace`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/logging.py](../../../../../src/learnloop_sidecar/logging.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
