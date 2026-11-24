---
title: "learnloop.notebook_runtime.hostfiles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/hostfiles.py"
source_paths:
  - "src/learnloop/notebook_runtime/hostfiles.py"
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
  - "learnloop.notebook_runtime.hostfiles module"
  - "src/learnloop/notebook_runtime/hostfiles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.hostfiles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.hostfiles` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: The only way the unsandboxed side touches the runtime's host files.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/hostfiles.py](../../../../../../src/learnloop/notebook_runtime/hostfiles.py) |
| Source lines | 206 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class UnsafePath(RuntimeError)` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 23) — A runtime host path that is not what trusted code made: refused, never followed.
- `open_private_dir(path: Path, *, create: bool=True) -> int` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 38) — A descriptor on ``path``: created (mode 0700) when missing, never through a link, owned by this user and private.
- `private_dir(path: Path) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 57) — Make (or check) a private directory and each missing parent of it below an existing private one.
- `write_private(directory: Path, name: str, data: bytes, mode: int=384) -> Path` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 80) — Write ``directory/name`` afresh: whatever stood there is removed (a link goes, never followed), then the file is created exclusively without following links, through the directory's descriptor.
- `remove_private(directory: Path, name: str) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 102) — Remove ``directory/name`` if it is there (a link is removed, never followed; a directory is refused).
- `remove_private_dir(directory: Path) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 115) — Remove an empty private directory (a link in its place is refused, not followed).
- `listening_socket(directory: Path, name: str, backlog: int=64) -> socket.socket` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 129) — A Unix socket bound at ``directory/name`` and listening, created by trusted code (whatever stood there is removed first).
- `write_beneath(root: Path, parts: tuple[str, ...], name: str, data: bytes) -> Path` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 150) — Write ``root/<parts...>/name`` without following a link below ``root`` (the vault: shared, not private).
- `check_socket(path: Path) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 194) — Before connecting: ``path`` itself (not a link's target) is a socket of this user, else refused.

### Module constants

- `_DIR_FLAGS` ([src/learnloop/notebook_runtime/hostfiles.py](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 27)

### Explicit exports

`__all__` declares:

- `UnsafePath`
- `check_socket`
- `listening_socket`
- `open_private_dir`
- `private_dir`
- `remove_private`
- `remove_private_dir`
- `write_beneath`
- `write_private`

## Internal implementation anchors

- `_checked_dir(fd: int, path: Path) -> int` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 30)
- `_remove(fd: int, name: str, where: Path) -> None` ([source](../../../../../../src/learnloop/notebook_runtime/hostfiles.py), line 71)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `module`; statically calls `check_socket`
- [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] — imports `module`; statically calls `remove_private`, `remove_private_dir`, `write_private`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `module`; statically calls `private_dir`, `write_private`
- [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] — imports `module`; statically calls `check_socket`, `listening_socket`, `private_dir`, `remove_private`, `write_private`
- [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]] — imports `module`; statically calls `write_beneath`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `errno`, `os`, `pathlib`, `secrets`, `socket`, `stat`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]], [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]], [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]], [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]], [[Reference/Modules/learnloop_sidecar/handlers/notebooks|learnloop_sidecar.handlers.notebooks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_the_runtimes_http_only_ever_targets_its_sessions_unix_socket`

## Modification guidance

- Make changes here when the responsibility remains hostfiles within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/hostfiles.py](../../../../../../src/learnloop/notebook_runtime/hostfiles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
