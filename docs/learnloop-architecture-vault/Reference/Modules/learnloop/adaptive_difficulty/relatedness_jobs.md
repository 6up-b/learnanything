---
title: "learnloop.adaptive_difficulty.relatedness_jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/relatedness_jobs.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/relatedness_jobs.py"
source_commit: "38c895e230ef534fc7b4a2eff18a51ca456a06a2"
source_commit_timestamp: "2026-10-24T10:23:24-04:00"
source_worktree_state: "clean"
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
  - "learnloop.adaptive_difficulty.relatedness_jobs module"
  - "src/learnloop/adaptive_difficulty/relatedness_jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.relatedness_jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.relatedness_jobs` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The relatedness proposal's re-proposals in the background (spec_adaptive_difficulty_v1 §5.10 "When").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/relatedness_jobs.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py) |
| Source lines | 99 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38c895e230ef534fc7b4a2eff18a51ca456a06a2` |
| Commit timestamp | `2026-10-24T10:23:24-04:00` |

## Public API

- `stale_subjects(vault: Any, repository: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py), line 41) — Subjects with an adopted coupling version and a unit (an LO or an item revision) whose fingerprint changed, or that is new, since its latest run.
- `schedule_reproposals(vault: Any, sqlite_path: Any, *, client: Any=None, builds: Any=None, live_vault: Callable[[], Any] | None=None) -> list[Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py), line 68) — Re-propose the stale subjects in the background; returns the threads started.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/relatedness_jobs.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py), line 35)
- `SUBJECTS_PER_TRIGGER` ([src/learnloop/adaptive_difficulty/relatedness_jobs.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py), line 37)

### Explicit exports

`__all__` declares:

- `SUBJECTS_PER_TRIGGER`
- `schedule_reproposals`
- `stale_subjects`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `schedule_reproposals`; statically calls `schedule_reproposals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `_launch`; calls `_launch`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; calls `propose_subject`, `subject_inputs`, `subjects`, `touched_units`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `coupling_on`; calls `coupling_on`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_the_background_scheduler_sees_a_run_whose_recorded_context_is_protected`

## Modification guidance

- Make changes here when the responsibility remains relatedness jobs within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/relatedness_jobs.py](../../../../../../src/learnloop/adaptive_difficulty/relatedness_jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
