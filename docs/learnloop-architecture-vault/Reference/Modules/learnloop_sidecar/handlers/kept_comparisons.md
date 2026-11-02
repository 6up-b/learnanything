---
title: "learnloop_sidecar.handlers.kept_comparisons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/kept_comparisons.py"
source_paths:
  - "src/learnloop_sidecar/handlers/kept_comparisons.py"
source_commit: "e6c892bdf22c782a897e0d775e31f83b70ad1e7a"
source_commit_timestamp: "2026-10-27T20:03:43-04:00"
source_worktree_state: "clean"
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
  - "learnloop_sidecar.handlers.kept_comparisons module"
  - "src/learnloop_sidecar/handlers/kept_comparisons.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.kept_comparisons`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.kept_comparisons` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW4d RPCs: keep a comparison, remove it, reopen it, its marks.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/kept_comparisons.py](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py) |
| Source lines | 246 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e6c892bdf22c782a897e0d775e31f83b70ad1e7a` |
| Commit timestamp | `2026-10-27T20:03:43-04:00` |

## Public API

- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 45) — What the Reader's prompt contract adds for RW4d (absent while off).
- `class TakeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 125)
  - `_one_target(self) -> 'TakeInput'` (line 134; internal)
- `class KeepInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 141)
- `reader_library_compare_keep(ctx: SidecarContext, params: KeepInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 158) — Keep this comparison: its claims and relations as proposals, with the learner's take (spec §7.8; G43).
- `class KeptAskInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 198)
- `reader_library_compare_remove(ctx: SidecarContext, params: KeptAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 206) — Remove: the keep's proposals are superseded, never deleted.
- `reader_library_compare_reopen(ctx: SidecarContext, params: KeptAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 219) — A kept comparison's table again (from ``⇄``), from the stored row; no model call.
- `class KeptMarksInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 230)
- `reader_kept_comparisons(ctx: SidecarContext, params: KeptMarksInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 235) — The ``⇄`` marks for the open reading (the learner's own; outside the cue budget).

### Module constants

- `KEPT_COMPARISON_RPCS` ([src/learnloop_sidecar/handlers/kept_comparisons.py](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 37)

### Explicit exports

`__all__` declares:

- `KEPT_COMPARISON_RPCS`
- `prompt_contract_fields`

## Internal implementation anchors

- `_require(ctx: SidecarContext, *, tutor: bool=False)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 56)
- `_error(exc: LA.LibraryAskError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 66)
- `_require_any(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 70) — Keeping is on for some surface (the library's or the tutor's); each row is then checked by its own caller (:func:`_row_guard`).
- `_is_tutor_row(row: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 80)
- `_switch_on(vault: Any, row: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 84) — The switch of the surface that kept ``row`` (its persisted caller).
- `_row_guard(vault: Any, repository: Any, row: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 90) — The availability rules of an existing keep's row, chosen by its persisted caller: the tutor keep's switch and cold check for a tutor keep, the library keep's switch and its ask's binding for a library keep.
- `_cold_guard(vault: Any, repository: Any, ask_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py), line 103) — Refuse while the ask's (or the tutor request's) item has a cold administration open.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `cold_administration_open`; calls `cold_administration_open`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; calls `by_point_enabled`, `keep`, `keep_enabled`, `keep_tutor`, `kept_ask`, `kept_marks`, `max_perspectives`, `remove`, `reopen`, `tutor_comparison`, `tutor_keep_enabled`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; calls `ask_row`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `follow_up_caller`; calls `follow_up_caller`
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

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw4d_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/kept_comparisons.py](../../../../../../src/learnloop_sidecar/handlers/kept_comparisons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
