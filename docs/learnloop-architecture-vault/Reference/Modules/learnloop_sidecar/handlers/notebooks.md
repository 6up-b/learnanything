---
title: "learnloop_sidecar.handlers.notebooks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/notebooks.py"
source_paths:
  - "src/learnloop_sidecar/handlers/notebooks.py"
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
  - "learnloop_sidecar.handlers.notebooks module"
  - "src/learnloop_sidecar/handlers/notebooks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.notebooks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.notebooks` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Notebook runtime RPCs: ``notebook.open``, ``notebook.status``, ``notebook.close``, ``notebook.release`` and ``notebook.run_cells`` (``docs/reviews/notebook-runtime-b1-b3.md``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py) |
| Source lines | 243 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class NotebookOpenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 34)
- `class NotebookSessionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 43)
- `class NotebookReleaseInput(NotebookSessionInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 47)
- `class NotebookCell(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 51)
- `class NotebookRunCellsInput(NotebookSessionInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 56)
- `pad_notebook(vault_root: Path, repository: Any, pad_id: str) -> tuple[bytes, str, dict[str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 91) — The pad's notebook (generated from its standing cells, in pad order) and its revision: the cells' names in order, so an edit to a cell's code keeps the session (it reaches the kernel through ``notebook.run_cells``) while an inserted, removed or moved cell makes a new one.
- `lesson_notebook(vault_root: Path, repository: Any, lesson_id: str, path: str | None) -> tuple[bytes, dict[str, Any], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 119) — A lesson's notebook (spec §11.2): its bytes, its commit points and held cells, and whether the lesson is closed (a review: nothing is released).
- `notebook_open_handler(ctx: SidecarContext, params: NotebookOpenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 183) — Open (or return) the owner's session on the notebook at ``path``, or on a pad's cells (``pad:<id>`` with no path): ``{sessionId, state, frameUrl, cellRuns, ...}``.
- `notebook_status_handler(ctx: SidecarContext, params: NotebookSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 213) — A session's state, frame URL, restarts, attached frames and memory.
- `notebook_close_handler(ctx: SidecarContext, params: NotebookSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 221) — Stop a session's server (graceful, then forced) and forget the session.
- `notebook_release_handler(ctx: SidecarContext, params: NotebookReleaseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 229) — Release held cells (shipped ``disabled=True``): marimo runs them at once.
- `notebook_run_cells_handler(ctx: SidecarContext, params: NotebookRunCellsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 238) — Run named cells with the given code (a pad cell's ⇧↵, later the teacher's edits).

### Module constants

- `NOTEBOOK_RPCS` ([src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 25)
- `OWNER_PATTERN` ([src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 30)
- `CELL_NAME_PATTERN` ([src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 31)
- `PAD_NOTEBOOKS` ([src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 88)
- `_VERBATIM_KEYS` ([src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 166)

## Internal implementation anchors

- `_runtime(ctx: SidecarContext) -> R.NotebookRuntime` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 60)
- `_vault_key(ctx: SidecarContext) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 66) — The vault a session belongs to: the context's open vault, resolved.
- `_source(vault_root: Path, relative: str) -> bytes` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 72)
- `_errors(exc: Exception) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 142)
- `_call(work: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notebooks.py), line 169)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] — imports `module`; calls `cell_name`, `notebook_from_cells`
- [[Reference/Modules/learnloop/notebook_runtime/lessons|learnloop.notebook_runtime.lessons]] — imports `lesson_contract`, `lesson_notebook_path`; calls `lesson_contract`, `lesson_notebook_path`
- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `module`; calls `NotebookRuntime`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `Limits`, `RuntimeUnavailable`
- [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] — imports `module`
- [[Reference/Modules/learnloop/pads/cells|learnloop.pads.cells]] — imports `pad_cells`; calls `pad_cells`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `Verbatim`, `versioned`; calls `Verbatim`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `os`, `pathlib`, `typing`
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
  - `test_the_pinned_notebook_runtime_rpcs_are_all_of_them`
- [tests/test_notebook_lessons.py](../../../../../../tests/test_notebook_lessons.py) — direct import
  - `test_a_refused_release_is_said_and_the_inputs_refuse_extra_fields`
- [tests/test_notebook_rpcs.py](../../../../../../tests/test_notebook_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/notebooks.py](../../../../../../src/learnloop_sidecar/handlers/notebooks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
