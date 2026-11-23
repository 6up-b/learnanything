---
title: "learnloop.notebook_runtime.proxy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/proxy.py"
source_paths:
  - "src/learnloop/notebook_runtime/proxy.py"
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
  - "learnloop.notebook_runtime.proxy module"
  - "src/learnloop/notebook_runtime/proxy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.proxy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.proxy` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: The frame proxy: the only way a notebook frame reaches its sandboxed marimo server.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py) |
| Source lines | 369 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `bridge_script() -> bytes` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 82)
- `frame_csp(port: int) -> str` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 86) — The notebook frame's CSP.
- `gate(host: str | None, path: str, *, port: int, base_url: str) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 109) — ``(refusal, rel)``: why the request is refused (``"host"``, ``"path"``) or None, and its path under the session's base URL.
- `frame_may(method: str, rel: str) -> bool` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 120) — Whether the frame may make this request (the bridge script is the proxy's own).
- `upstream_headers(headers: dict[str, str], *, token: str, server_token: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 128)
- `downstream_headers(headers: Any, *, port: int) -> list[tuple[bytes, bytes]]` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 136)
- `security_headers(port: int) -> list[tuple[bytes, bytes]]` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 142)
- `inject_bridge(html: bytes, base_url: str) -> bytes` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 148)
- `class FrameProxy` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 157) — The ASGI app in front of one session's server.
  - `__init__(self, session: Session, *, on_activity: Callable[[], None] | None=None) -> None` (line 160; internal)
  - `async start(self) -> int` (line 172; public)
  - `async stop(self) -> None` (line 189; public)
  - `_upstream(self) -> Any` (line 206; internal)
  - `async __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None` (line 222; internal)
  - `async _plain(self, send: Any, status: int, text: str) -> None` (line 228; internal)
  - `async _http(self, scope: dict[str, Any], receive: Any, send: Any) -> None` (line 235; internal)
  - `async _websocket(self, scope: dict[str, Any], receive: Any, send: Any) -> None` (line 300; internal)

### Module constants

- `LOG` ([src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 31)
- `_DROPPED_REQUEST_HEADERS` ([src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 35)
- `_DROPPED_RESPONSE_HEADERS` ([src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 39)
- `BRIDGE_JS` ([src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 45)
- `BRIDGE_PATH` ([src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 79)

## Internal implementation anchors

- `_headers(scope: dict[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/notebook_runtime/proxy.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `FrameProxy`; statically calls `FrameProxy`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] — imports `module`; calls `instantiate_with_values`, `kernel_ready_cells`, `ui_values`
- [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] — imports `module`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `READY`, `Session`

### Platform and third-party dependencies

- Standard library: `__future__`, `asyncio`, `json`, `logging`, `socket`, `typing`
- Third party: `httpx`, `uvicorn`, `websockets`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_downstream_drops_cookies_and_framing_headers_and_sets_the_csp`
  - `test_the_bridge_is_injected_and_names_only_the_workbench_origins`
  - `test_the_frame_csp_contains_the_page`
  - `test_the_frame_may_load_the_app_and_drive_its_widgets`
  - `test_the_frame_may_not_edit_release_run_scratch_save_or_restart`
  - `test_the_gate_refuses_another_host_and_another_path`
  - `test_the_proxy_refuses_before_reaching_the_server`
  - `test_the_proxy_serves_its_bridge_and_records_ui_values_as_they_pass`
  - `test_upstream_carries_the_token_and_never_the_frames_cookies`

## Modification guidance

- Make changes here when the responsibility remains proxy within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/proxy.py](../../../../../../src/learnloop/notebook_runtime/proxy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
