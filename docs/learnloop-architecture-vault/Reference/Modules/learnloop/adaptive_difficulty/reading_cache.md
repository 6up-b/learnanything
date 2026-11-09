---
title: "learnloop.adaptive_difficulty.reading_cache"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/reading_cache.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/reading_cache.py"
source_commit: "workspace/uncommitted @ HEAD 09d65a0994a7955cb1d38cc40405a35cf5cc5220"
source_commit_timestamp: "2026-11-08T22:51:11-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.reading_cache module"
  - "src/learnloop/adaptive_difficulty/reading_cache.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.reading_cache`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.reading_cache` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router speed stage 2, item 1: AD's section → LO map held within ONE objective job (no successor).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py) |
| Source lines | 182 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 09d65a0994a7955cb1d38cc40405a35cf5cc5220` |
| Commit timestamp | `2026-11-08T22:51:11-05:00` |

## Public API

- `held_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 42) — ``[router_objective] held_reading_map`` at the follow-up batch's tag with the objective serving (router speed stage 2's Codex review F2): the map's values are the same either way, but held they cost less, so the objective job's input builds finish sooner and a deadline-bound ref…
- `class JobHold` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 54) — One objective job's held reading map (:func:`job_scope`): values per database, each under the protection epoch it was computed at.
  - `__init__(self) -> None` (line 59; internal)
  - `at_epoch(self, database: str, epoch: str) -> None` (line 64; public) — Landing ruling R1: a protection change within the job (another epoch for this database than the one the job holds values at) drops everything the job held for the database.
  - `get(self, key: Hashable, vault: Any) -> Any` (line 76; public)
  - `put(self, key: Hashable, vault: Any, value: Any) -> None` (line 87; public)
  - `discard(self) -> None` (line 97; public)
- `job_scope() -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 108) — One objective job's hold (landing ruling R1), opened by ``objective_inputs.decision_reads``: what AD's reading map holds inside lives until the scope ends and is discarded then.
- `class HeldReads` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 128) — What one view may read of the job's hold: keys carry the database, the view's epoch and, for a vault-derived value, the raw vault object (with whether the map reads the operation's projection of it).
  - `__init__(self, hold: JobHold, database: str, epoch: str) -> None` (line 132; internal)
  - `_key(self, vault: Any, parts: tuple[Any, ...]) -> tuple[Any, ...]` (line 137; internal)
  - `get(self, vault: Any, *parts: Any) -> Any` (line 142; public) — The value the job holds for ``parts`` (and this vault object; None: a value no vault is read for).
  - `put(self, vault: Any, value: Any, *parts: Any) -> None` (line 147; public)
  - `document_ir(self, view: Any, repository: Any, extraction_id: str) -> Any` (line 150; public) — The reading's IR as of the job's first read of it (``view.document_ir``, the chokepoint), the withheld rule asked of ``view`` fresh before a held IR is returned; None (never held) for a withheld or unreadable one.
- `job_hold(view: Any, repository: Any) -> HeldReads | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 164) — The objective job's hold as ``view`` reads it, or None: outside a job, while the view is unavailable or has no epoch, or with no database to key by.

### Module constants

- `_JOB` ([src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 104)

### Explicit exports

`__all__` declares:

- `HeldReads`
- `JobHold`
- `held_on`
- `job_hold`
- `job_scope`

## Internal implementation anchors

- `_owner(vault: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py), line 124)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`; statically calls `held_on`, `job_hold`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `module`; statically calls `held_on`, `job_hold`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `job_scope`; statically calls `job_scope`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `followup_on`; calls `followup_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `pathlib`, `threading`, `typing`, `weakref`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_the_pool_and_the_held_map_follow_their_switches`
  - `test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`
- [tests/test_rospeed2_section_map.py](../../../../../../tests/test_rospeed2_section_map.py) — direct import
  - `test_switched_off_the_map_is_mains_and_reads_nothing_of_the_hold`

## Modification guidance

- Make changes here when the responsibility remains reading cache within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/reading_cache.py](../../../../../../src/learnloop/adaptive_difficulty/reading_cache.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
