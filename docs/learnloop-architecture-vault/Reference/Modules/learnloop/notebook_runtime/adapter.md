---
title: "learnloop.notebook_runtime.adapter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/adapter.py"
source_paths:
  - "src/learnloop/notebook_runtime/adapter.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.notebook_runtime.adapter module"
  - "src/learnloop/notebook_runtime/adapter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.adapter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.adapter` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: Every private marimo interface the notebook runtime relies on, and nothing else.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `marimo_edit_args(notebook: str, token_file: str, base_url: str) -> list[str]` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 90) — ``marimo edit``'s arguments: headless, token from a file, served under ``base_url``, no update check and no marimo-managed sandbox (bubblewrap is the sandbox).
- `server_token(index_html: str) -> str | None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 98) — The skew-protection token the server wrote into its index page.
- `kernel_ready_cells(message: str) -> tuple[dict[str, str], dict[str, str]] | None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 105) — From a WebSocket message: ``({cell name: cell id}, {cell id: code})`` when it is ``kernel-ready``.
- `ui_values(set_request_body: bytes) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 124) — The UI element values a ``set_ui_element_value`` request sets (object id to value).
- `instantiate_with_values(body: bytes, recorded: dict[str, Any]) -> bytes | None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 137) — An ``instantiate`` request filled with recorded UI values, or None to send it as it is.
- `cell_config_body(cell_ids: list[str], *, disabled: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 156)
- `run_body(cell_ids: list[str], codes: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 160)
- `pinned_version() -> str | None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 166) — The exact marimo version LearnLoop's ``notebook`` extra pins, from its installed metadata.
- `installed_version() -> str | None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 182)
- `interface_problems() -> list[str]` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 191) — Every private interface above that the installed marimo no longer has, said in words; empty when all hold.
- `launch(argv: list[str]) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 281) — ``argv``: ``[this file, SOCKET, "--", *marimo-args]``.

### Module constants

- `MARIMO` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 24)
- `NOTEBOOK_EXTRA` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 25)
- `HEALTH` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 28)
- `INDEX` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 29)
- `WEBSOCKET` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 30)
- `INSTANTIATE` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 31)
- `SET_UI_ELEMENT_VALUE` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 32)
- `SET_MODEL_VALUE` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 33)
- `FUNCTION_CALL` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 34)
- `SET_CELL_CONFIG` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 35)
- `RUN` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 36)
- `SHUTDOWN` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 37)
- `RESTART_SESSION` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 38)
- `SESSION_HEADER` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 41)
- `SERVER_TOKEN_HEADER` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 44)
- `_SERVER_TOKEN` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 45)
- `FRAME_ALLOWED` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 52)
- `FRAME_ALLOWED_GET_PREFIXES` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 57)
- `APP_VIEW_PARAMS` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 62)
- `KIOSK_PARAM` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 63)
- `SESSION_ID_PARAM` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 64)
- `KERNEL_READY_OP` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 67)
- `MARIMO_TOML` ([src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 71)

## Internal implementation anchors

- `_route_paths(routes: Any, prefix: str='') -> Any` ([source](../../../../../../src/learnloop/notebook_runtime/adapter.py), line 270)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `module`; statically calls `instantiate_with_values`, `kernel_ready_cells`, `ui_values`
- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `module`; statically calls `cell_config_body`, `run_body`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `module`; statically calls `marimo_edit_args`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `module`; statically calls `server_token`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `importlib`, `inspect`, `json`, `os`, `re`, `sys`, `typing`
- Third party: `marimo`, `uvicorn`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]], [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]], [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]], [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_recorded_values_fill_only_a_page_that_sends_none`
  - `test_release_and_run_need_a_frame_and_known_cells`
  - `test_the_adapter_reads_marimos_messages`
  - `test_the_frame_may_load_the_app_and_drive_its_widgets`
  - `test_the_frame_may_not_edit_release_run_scratch_save_or_restart`
- [tests/test_notebook_runtime_adapter.py](../../../../../../tests/test_notebook_runtime_adapter.py) — direct import
  - `test_every_private_marimo_interface_the_runtime_relies_on_holds`
  - `test_the_installed_marimo_is_the_pinned_one`

## Modification guidance

- Make changes here when the responsibility remains adapter within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/adapter.py](../../../../../../src/learnloop/notebook_runtime/adapter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
