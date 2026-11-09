---
title: "learnloop_sidecar.handlers.compare_scope"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/compare_scope.py"
source_paths:
  - "src/learnloop_sidecar/handlers/compare_scope.py"
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
  - "learnloop_sidecar.handlers.compare_scope module"
  - "src/learnloop_sidecar/handlers/compare_scope.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.compare_scope`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.compare_scope` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader CA3 RPCs: reading the ask box's words for a comparison, and the learner's change of it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/compare_scope.py](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py) |
| Source lines | 137 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `books_payload(vault: Any, repository: Any, caller: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 63) — The library's books for *+ add a book* (titles only).
- `class CompareScopeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 69)
- `reader_compare_scope(ctx: SidecarContext, params: CompareScopeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 80) — Read the words for a comparison (one Decider request, off the request path).
- `class CompareScopeCorrectionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 119)
- `reader_compare_scope_correction(ctx: SidecarContext, params: CompareScopeCorrectionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 126) — The learner's change of a reading (a ``learner_card`` row).

### Module constants

- `COMPARE_SCOPE_RPCS` ([src/learnloop_sidecar/handlers/compare_scope.py](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 36)

### Explicit exports

`__all__` declares:

- `COMPARE_SCOPE_RPCS`
- `books_payload`

## Internal implementation anchors

- `_require_scope(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 39)
- `_books(vault: Any, repository: Any, caller: Any) -> list[CS.Book]` ([source](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py), line 48) — The books the caller's comparison may read (its policy's scope).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `books_payload`; statically calls `books_payload`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `module`; calls `Reading`, `library_books`, `read`, `record_correction`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `scope_for`; calls `scope_for`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `_require`, `_start`, `reader_caller`, `scope_enabled`; calls `_require`, `_start`, `reader_caller`, `scope_enabled`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_ca3_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/compare_scope.py](../../../../../../src/learnloop_sidecar/handlers/compare_scope.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
