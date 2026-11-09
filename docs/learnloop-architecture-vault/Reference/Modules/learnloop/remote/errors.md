---
title: "learnloop.remote.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/errors.py"
source_paths:
  - "src/learnloop/remote/errors.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.remote.errors module"
  - "src/learnloop/remote/errors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.errors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.errors` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: Refusals a remote frontend may show the host verbatim (spec_mcp_frontend_c1 §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/errors.py](../../../../../../src/learnloop/remote/errors.py) |
| Source lines | 29 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RemoteRequestError(Exception)` ([source](../../../../../../src/learnloop/remote/errors.py), line 10) — A request LearnLoop refuses, with a learner-readable reason.
  - `__init__(self, message: str, *, code: str | None=None) -> None` (line 15; internal)
- `class NotFound(RemoteRequestError)` ([source](../../../../../../src/learnloop/remote/errors.py), line 21)
- `class InvalidRequest(RemoteRequestError)` ([source](../../../../../../src/learnloop/remote/errors.py), line 25)

### Explicit exports

`__all__` declares:

- `InvalidRequest`
- `NotFound`
- `RemoteRequestError`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `InvalidRequest`, `NotFound`, `RemoteRequestError`; statically calls `InvalidRequest`, `NotFound`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `NotFound`; statically calls `NotFound`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — imports consumer [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]]
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — imports consumer [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]]

## Modification guidance

- Make changes here when the responsibility remains errors within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/errors.py](../../../../../../src/learnloop/remote/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
