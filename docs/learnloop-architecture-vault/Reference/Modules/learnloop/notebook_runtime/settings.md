---
title: "learnloop.notebook_runtime.settings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/settings.py"
source_paths:
  - "src/learnloop/notebook_runtime/settings.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.notebook_runtime.settings module"
  - "src/learnloop/notebook_runtime/settings.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.settings`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.settings` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: The notebook runtime's named settings that are not vault config.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py) |
| Source lines | 39 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

No public top-level function or class definition is declared in this file.

### Module constants

- `LEARNER_CELLS_SANDBOXED` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 11)
- `CPU_ONLY` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 14)
- `FRAME_HOST` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 17)
- `WORKBENCH_ORIGINS` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 20)
- `CPU_QUOTA` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 24)
- `TASKS_MAX` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 25)
- `READY_TIMEOUT_SECONDS` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 28)
- `STOP_TIMEOUT_SECONDS` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 29)
- `RESTART_LIMIT` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 30)
- `RESTART_BACKOFF_SECONDS` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 31)
- `SWEEP_SECONDS` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 33)
- `NOTEBOOK_MAX_BYTES` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 35)
- `REQUEST_MAX_BYTES` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 38)
- `UI_VALUES_MAX_BYTES` ([src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py), line 39)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `module`
- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `module`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `module`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `module`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]], [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]], [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]], [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]], [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_pad_cells.py](../../../../../../tests/test_notebook_pad_cells.py) — direct import
  - `test_a_generated_notebook_larger_than_a_notebook_may_be_is_refused`
- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_an_oversized_request_is_refused_and_nothing_is_recorded_before_the_server_accepts_it`
  - `test_recorded_values_are_only_known_controls_within_a_bound`
  - `test_the_app_frames_notebooks_from_any_loopback_port`
  - `test_the_bridge_and_the_paper_theme_are_injected_and_the_bridge_names_only_the_workbench_origins`
  - `test_the_frame_csp_contains_the_page`
  - `test_the_runtimes_http_only_ever_targets_its_sessions_unix_socket`
  - `test_the_scope_keeps_the_session_when_a_child_runs_out_of_memory`
  - `test_the_settings_defaults_and_their_dump`

## Modification guidance

- Make changes here when the responsibility remains settings within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/settings.py](../../../../../../src/learnloop/notebook_runtime/settings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
