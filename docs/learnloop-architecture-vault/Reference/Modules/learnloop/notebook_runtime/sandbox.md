---
title: "learnloop.notebook_runtime.sandbox"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/sandbox.py"
source_paths:
  - "src/learnloop/notebook_runtime/sandbox.py"
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
  - "learnloop.notebook_runtime.sandbox module"
  - "src/learnloop/notebook_runtime/sandbox.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.sandbox`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.sandbox` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: How one marimo server is launched: the shared hardened profile, the server's own mounts, and its scope.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py) |
| Source lines | 189 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RuntimeUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 38) — The notebook runtime cannot run here (no bubblewrap, no notebook extra); it refuses, never runs unsandboxed.
- `class Limits` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 43)
  - `from_config(cls, config: object) -> Limits` (line 48; public)
- `class Layout` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 53) — A session's host paths.
  - `socket(self) -> Path` (line 62; public)
  - `token_file(self) -> Path` (line 66; public)
- `missing_requirements() -> list[str]` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 70) — Why the runtime cannot run here, in words; empty when it can.
- `runtime_base_dir() -> Path` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 93) — Where sessions' run directories go: the user's runtime directory (short, private, gone at logout), else the temporary directory.
- `write_shared_files(base: Path) -> tuple[Path, Path]` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 110) — marimo's config directory and the hosts file, written once under ``base`` (both mounted read-only).
- `scope_available() -> bool` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 126) — Whether ``systemd-run --user --scope`` can start a scope here (probed once per process).
- `scope_prefix(unit: str, limits: Limits, *, scoped: bool) -> list[str]` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 144)
- `launch_command(layout: Layout, limits: Limits, *, base_url: str, unit: str, scoped: bool, python: str | None=None, bwrap: str | None=None) -> tuple[list[str], dict[str, str]]` ([source](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 154) — The argv and environment that start one marimo server on ``layout.socket``.

### Module constants

- `SESSION_BUS_VARS` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 26)
- `HOSTS_FILE_TEXT` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 30)
- `SANDBOX_NOTEBOOK` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 32)
- `SANDBOX_LAUNCHER` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 33)
- `SANDBOX_CONFIG` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 34)
- `SANDBOX_SCRATCH` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 35)
- `SOCKET_SUFFIX_BYTES` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 88)
- `SOCKET_PATH_MAX_BYTES` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 90)
- `_SCOPE_PROBE` ([src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py), line 123)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `Layout`, `Limits`, `RuntimeUnavailable`, `SOCKET_PATH_MAX_BYTES`, `missing_requirements`, `runtime_base_dir`, `scope_available`, `write_shared_files`; statically calls `Layout`, `RuntimeUnavailable`, `runtime_base_dir`, `scope_available`, `write_shared_files`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `Layout`, `Limits`, `launch_command`; statically calls `launch_command`
- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `Limits`, `RuntimeUnavailable`

### Repository tooling consumers

- [scripts/desk_harness/notebook.py](../../../../../../scripts/desk_harness/notebook.py); calls `Limits`, `missing_requirements`, `scope_available`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] — imports `module`; calls `marimo_edit_args`
- [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] — imports `module`
- [[Reference/Modules/learnloop/sandbox_profile|learnloop.sandbox_profile]] — imports `bwrap_path`, `sandboxed_command`; calls `bwrap_path`, `sandboxed_command`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `importlib`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]], [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]], [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/notebook_runtime_helpers.py](../../../../../../tests/notebook_runtime_helpers.py) — direct import
- [tests/test_notebook_rpcs.py](../../../../../../tests/test_notebook_rpcs.py) — direct import
  - `test_open_reads_the_notebook_snapshot_and_the_vaults_settings`
  - `test_runtime_refusals_are_stable_errors`
- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_a_refused_runtime_is_said_before_anything_starts`
  - `test_a_runtime_directory_too_deep_for_a_socket_is_passed_over`
  - `test_a_runtime_directory_too_deep_for_a_socket_is_refused`
  - `test_the_launch_uses_the_shared_hardened_profile_and_the_servers_mounts`
  - `test_the_scope_keeps_the_session_when_a_child_runs_out_of_memory`
- [tests/test_notebook_runtime_sandbox.py](../../../../../../tests/test_notebook_runtime_sandbox.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains sandbox within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/sandbox.py](../../../../../../src/learnloop/notebook_runtime/sandbox.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
