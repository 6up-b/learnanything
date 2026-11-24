---
title: "learnloop.notebook_runtime.runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/runtime.py"
source_paths:
  - "src/learnloop/notebook_runtime/runtime.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.notebook_runtime.runtime module"
  - "src/learnloop/notebook_runtime/runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.runtime` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: The notebook runtime a sidecar context owns: every open session, on one event loop thread of its own.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py) |
| Source lines | 430 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SessionNotFound(LookupError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 61) — No such session in the vault open now.
- `class SessionsFull(RuntimeError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 65) — As many sessions run as allowed and every one has a frame attached.
- `class NotConnected(RuntimeError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 69) — No frame has connected to the session yet, so marimo has no session to address.
- `class CellUnknown(KeyError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 73) — A cell name the session's notebook does not have.
- `class KernelRefused(RuntimeError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 77) — marimo answered a sidecar request with an error.
- `class ReleaseRefused(PermissionError)` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 81) — A lesson notebook's held cells are released only by the learner's commit, and never in a review.
- `class NotebookRuntime` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 93)
  - `__init__(self, *, backend: Any=None, base_dir: Path | None=None, requirements: Callable[[], list[str]]=missing_requirements, sweep_seconds: float=settings.SWEEP_SECONDS, supervisor_options: dict[str, Any] | None=None) -> None` (line 94; internal)
  - `_ensure_loop(self) -> asyncio.AbstractEventLoop` (line 113; internal)
  - `_call(self, make: Callable[[], Awaitable[T]], timeout: float=CALL_SECONDS) -> T` (line 132; internal)
  - `running(self) -> bool` (line 141; public)
  - `open(self, *, vault_key: str, owner: str, source: bytes, view: str, limits: Limits, idle_minutes: int, max_sessions: int, revision: str | None=None, contract: dict[str, Any] | None=None, review: bool=False) -> dict[str, Any]` (line 146; public) — ``revision`` names the notebook's identity when its bytes are not it: a pad's cells are one notebook while the same cells stand in the same order, whatever their code (an edit reaches the running kernel through ``run_cells``), so moving or reopening the pad keeps its kernel.
  - `status(self, *, vault_key: str, session_id: str) -> dict[str, Any]` (line 160; public)
  - `close_session(self, *, vault_key: str, session_id: str) -> dict[str, Any]` (line 163; public)
  - `release(self, *, vault_key: str, session_id: str, names: list[str]) -> dict[str, Any]` (line 166; public)
  - `run_cells(self, *, vault_key: str, session_id: str, cells: list[tuple[str, str]]) -> dict[str, Any]` (line 169; public)
  - `switch_vault(self, vault_key: str | None) -> None` (line 172; public) — A vault switch (or a refusal of the vault open now, with None): every session of another vault stops.
  - `close(self) -> None` (line 181; public) — Stop every session and the loop thread (the context closing).
  - `_backend_now(self) -> Any` (line 205; internal)
  - `_base(self) -> Path` (line 210; internal)
  - `_entry(self, vault_key: str, session_id: str) -> _Entry` (line 217; internal)
  - `_view(self, entry: _Entry) -> dict[str, Any]` (line 223; internal)
  - `async _open(self, vault_key: str, owner: str, source: bytes, view: str, limits: Limits, idle_minutes: int, max_sessions: int, revision: str | None=None, contract: dict[str, Any] | None=None, review: bool=False) -> dict[str, Any]` (line 232; internal)
  - `async _make_room(self, max_sessions: int, keep: _Entry | None=None) -> None` (line 277; internal)
  - `async _status(self, vault_key: str, session_id: str) -> dict[str, Any]` (line 289; internal)
  - `async _close_session(self, vault_key: str, session_id: str) -> dict[str, Any]` (line 292; internal)
  - `async _forget(self, entry: _Entry, reason: str) -> None` (line 299; internal)
  - `async _stop_where(self, select: Callable[[_Entry], bool], reason: str, *, forget: bool=False) -> None` (line 313; internal)
  - `_connected(self, entry: _Entry) -> None` (line 321; internal)
  - `_cell_ids(self, entry: _Entry, names: list[str]) -> list[str]` (line 328; internal)
  - `async _release(self, vault_key: str, session_id: str, names: list[str]) -> dict[str, Any]` (line 334; internal)
  - `async _run_cells(self, vault_key: str, session_id: str, cells: list[tuple[str, str]]) -> dict[str, Any]` (line 360; internal)
  - `async sweep(self, now: float | None=None) -> list[str]` (line 373; public) — Stop sessions idle past their limit, or whose run directory grew past its bound; their ids.
  - `async _sweep_forever(self) -> None` (line 390; internal)
  - `sessions(self) -> list[Session]` (line 400; public)
  - `run_on_loop(self, make: Callable[[], Awaitable[T]], timeout: float=CALL_SECONDS) -> T` (line 403; public)

### Module constants

- `LOG` ([src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 51)
- `T` ([src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 52)
- `CALL_SECONDS` ([src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 56)
- `CLOSE_SECONDS` ([src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 58)

## Internal implementation anchors

- `class _Entry` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 86)
- `async _cancel_other_tasks() -> None` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 407) — Every task left on the runtime's loop (the sweep, a draining pipe) ends before the loop stops.
- `_memory_bytes(session: Session) -> int | None` ([source](../../../../../../src/learnloop/notebook_runtime/runtime.py), line 417) — The session's scope memory (``memory.current``), when it runs in a scope of its own.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `module`; statically calls `NotebookRuntime`

### Repository tooling consumers

- [scripts/desk_harness/notebook.py](../../../../../../scripts/desk_harness/notebook.py); calls `NotebookRuntime`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] — imports `module`; calls `cell_config_body`, `run_body`
- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `FrameProxy`; calls `FrameProxy`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `Layout`, `Limits`, `RuntimeUnavailable`, `SOCKET_PATH_MAX_BYTES`, `missing_requirements`, `runtime_base_dir`, `scope_available`, `write_shared_files`; calls `Layout`, `RuntimeUnavailable`, `runtime_base_dir`, `scope_available`, `write_shared_files`
- [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] — imports `module`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `LIVE_STATES`, `READY`, `STARTING`, `STOPPED`, `SandboxBackend`, `Session`, `Supervisor`, `notebook_revision`, `run_dir_bytes`; calls `SandboxBackend`, `Session`, `Supervisor`, `notebook_revision`, `run_dir_bytes`

### Platform and third-party dependencies

- Standard library: `__future__`, `asyncio`, `collections`, `dataclasses`, `logging`, `os`, `pathlib`, `secrets`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_lessons.py](../../../../../../tests/test_notebook_lessons.py) — direct import
  - `test_a_refused_release_is_said_and_the_inputs_refuse_extra_fields`
- [tests/test_notebook_rpcs.py](../../../../../../tests/test_notebook_rpcs.py) — direct import
  - `test_runtime_refusals_are_stable_errors`
- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_a_refused_runtime_is_said_before_anything_starts`
  - `test_a_runtime_directory_too_deep_for_a_socket_is_refused`
  - `test_a_session_is_not_found_from_another_vault`
  - `test_a_vault_switch_stops_and_forgets_the_other_vaults_sessions`
  - `test_release_and_run_need_a_frame_and_known_cells`
  - `test_with_every_session_shown_a_new_one_is_refused`
- [tests/test_notebook_runtime_sandbox.py](../../../../../../tests/test_notebook_runtime_sandbox.py) — direct import
  - `test_a_lessons_held_cells_are_released_at_its_commit_point_and_not_before`
  - `test_a_review_of_a_finished_lesson_releases_nothing_and_commits_nothing`
  - `test_a_vault_switch_stops_the_other_vaults_server`

## Modification guidance

- Make changes here when the responsibility remains runtime within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/runtime.py](../../../../../../src/learnloop/notebook_runtime/runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
