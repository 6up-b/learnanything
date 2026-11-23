---
title: "learnloop.notebook_runtime.supervisor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/supervisor.py"
source_paths:
  - "src/learnloop/notebook_runtime/supervisor.py"
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
  - "learnloop.notebook_runtime.supervisor module"
  - "src/learnloop/notebook_runtime/supervisor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.supervisor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.supervisor` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: One notebook session and the supervisor that keeps its marimo server running.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py) |
| Source lines | 365 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Process(Protocol)` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 52)
  - `async wait(self) -> int` (line 56; public)
- `class Backend(Protocol)` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 59)
  - `async spawn(self, session: Session) -> Process` (line 60; public)
  - `async ready(self, session: Session) -> bool` (line 62; public)
  - `async server_token(self, session: Session) -> str | None` (line 64; public)
  - `async shutdown(self, session: Session) -> None` (line 66; public)
  - `signal_group(self, session: Session, signum: int) -> None` (line 68; public)
  - `async after_stop(self, session: Session) -> None` (line 70; public)
  - `async api(self, session: Session, rel: str, body: dict[str, Any]) -> tuple[int, str]` (line 72; public)
- `class Session` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 76)
  - `base_url(self) -> str` (line 107; public)
  - `touch(self) -> None` (line 110; public)
  - `view_dict(self) -> dict[str, Any]` (line 113; public)
- `notebook_revision(source: bytes) -> str` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 120)
- `class Supervisor` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 124) — Starts, watches and stops one session's server.
  - `__init__(self, session: Session, backend: Backend, *, restart_limit: int=settings.RESTART_LIMIT, backoff_seconds: float=settings.RESTART_BACKOFF_SECONDS, ready_timeout: float=settings.READY_TIMEOUT_SECONDS, stop_timeout: float=settings.STOP_TIMEOUT_SECONDS) -> None` (line 127; internal)
  - `async start(self) -> None` (line 142; public) — Start the server and wait until it answers on its socket (``ready``) or say why not (``failed``).
  - `async _launch(self) -> bool` (line 153; internal)
  - `async _wait_ready(self) -> bool` (line 178; internal)
  - `async _supervise(self) -> None` (line 193; internal)
  - `async stop(self, reason: str, *, graceful: bool=True) -> None` (line 218; public) — Stop the server (graceful first, forced after the timeout); the session ends ``stopped``.
  - `async _kill(self) -> None` (line 252; internal)
- `class SandboxBackend` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 268) — The real backend: a sandboxed ``marimo edit`` on a Unix socket, reached with httpx over the socket.
  - `__init__(self, *, scoped: bool) -> None` (line 271; internal)
  - `_client(self, session: Session, timeout: float=5.0) -> Any` (line 274; internal)
  - `async spawn(self, session: Session) -> Process` (line 281; public)
  - `async ready(self, session: Session) -> bool` (line 297; public)
  - `async server_token(self, session: Session) -> str | None` (line 304; public)
  - `async shutdown(self, session: Session) -> None` (line 309; public)
  - `async api(self, session: Session, rel: str, body: dict[str, Any]) -> tuple[int, str]` (line 314; public)
  - `signal_group(self, session: Session, signum: int) -> None` (line 322; public)
  - `async after_stop(self, session: Session) -> None` (line 326; public) — A stale socket goes; a scope systemd keeps listed as failed (a server killed by a signal) is reset by its own name, so nothing of a stopped session stays registered.
- `run_dir_bytes(run_dir: Path) -> int` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 357)

### Module constants

- `LOG` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 37)
- `STARTING` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 39)
- `READY` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 40)
- `RESTARTING` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 41)
- `STOPPING` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 42)
- `STOPPED` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 43)
- `FAILED` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 44)
- `LIVE_STATES` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 46)
- `OUTPUT_TAIL_BYTES` ([src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 49)

## Internal implementation anchors

- `async _drain(process: Any, session: Session) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/supervisor.py), line 341) — Keep the tail of the server's output in memory; the pipe never blocks the server.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `READY`, `Session`
- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `LIVE_STATES`, `READY`, `STARTING`, `STOPPED`, `SandboxBackend`, `Session`, `Supervisor`, `notebook_revision`, `run_dir_bytes`; statically calls `SandboxBackend`, `Session`, `Supervisor`, `notebook_revision`, `run_dir_bytes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] — imports `module`; calls `server_token`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `Layout`, `Limits`, `launch_command`; calls `launch_command`
- [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `asyncio`, `dataclasses`, `hashlib`, `logging`, `os`, `pathlib`, `secrets`, `signal`, `subprocess`, `time`, `typing`
- Third party: `httpx`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]], [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/notebook_runtime_helpers.py](../../../../../../tests/notebook_runtime_helpers.py) — direct import
- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_a_crashed_server_is_restarted_with_backoff`
  - `test_a_restart_waits_out_its_backoff_and_a_stop_ends_it`
  - `test_a_server_that_ignores_shutdown_is_terminated`
  - `test_a_server_that_never_answers_fails_and_is_killed`
  - `test_a_spawn_that_fails_is_said`
  - `test_a_start_ends_ready_with_the_servers_token`
  - `test_a_stop_is_graceful_first`
  - `test_a_stopped_session_starts_again`
  - `test_a_vault_switch_stops_and_forgets_the_other_vaults_sessions`
  - `test_open_answers_at_once_with_a_frame_url_on_its_own_port`
  - `test_past_the_restart_limit_the_session_fails`
  - `test_the_runtimes_http_only_ever_targets_its_sessions_unix_socket`
  - `test_the_session_limit_stops_the_least_recently_used_idle_session`

## Modification guidance

- Make changes here when the responsibility remains supervisor within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/supervisor.py](../../../../../../src/learnloop/notebook_runtime/supervisor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
