---
title: "learnloop.scheduling.reentry_summary"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/reentry_summary.py"
source_paths:
  - "src/learnloop/scheduling/reentry_summary.py"
source_commit: "eb4b8f642f1723b9cf054f625b06ac588bf7ccd2"
source_commit_timestamp: "2026-10-11T23:04:32-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.reentry_summary module"
  - "src/learnloop/scheduling/reentry_summary.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.reentry_summary`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.reentry_summary` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Welcome-back diff (spec §4.4, package F7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/reentry_summary.py](../../../../../../src/learnloop/scheduling/reentry_summary.py) |
| Source lines | 174 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `eb4b8f642f1723b9cf054f625b06ac588bf7ccd2` |
| Commit timestamp | `2026-10-11T23:04:32-04:00` |

## Public API

- `class SlippedFacet` ([source](../../../../../../src/learnloop/scheduling/reentry_summary.py), line 34)
  - `as_dict(self) -> dict[str, Any]` (line 40; public)
- `class ReentrySummary` ([source](../../../../../../src/learnloop/scheduling/reentry_summary.py), line 50)
  - `as_dict(self) -> dict[str, Any]` (line 60; public)
- `reentry_session_cap(vault: LoadedVault, repository: Repository, goal: Goal | None, *, clock: Clock | None=None) -> int | None` ([source](../../../../../../src/learnloop/scheduling/reentry_summary.py), line 73) — How many items the re-entry session serves, or ``None`` for no cap.
- `reentry_summary(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None, gap_days: int | None=None, top_n: int=3) -> ReentrySummary` ([source](../../../../../../src/learnloop/scheduling/reentry_summary.py), line 96) — Welcome-back diff for ``goal`` (§4.4).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `reentry_summary`; statically calls `reentry_summary`
- [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]] — imports `reentry_summary`; statically calls `reentry_summary`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `ReentrySummary`, `reentry_summary`; statically calls `reentry_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `reentry_summary`; statically calls `reentry_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `reentry_session_cap`; statically calls `reentry_session_cap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_projections_at`, `goal_report`; calls `facet_projections_at`, `goal_report`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `blueprint_weight_by_facet`; calls `blueprint_weight_by_facet`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]], [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_reentry_cap.py](../../../../../../tests/test_daily_loop_reentry_cap.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f9_reentry_panel_names_only_what_it_counts`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_reentry_below_threshold_does_not_show`
  - `test_reentry_splits_solid_slipped_and_excludes_held_flat`

## Modification guidance

- Change reentry summary policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/reentry_summary.py](../../../../../../src/learnloop/scheduling/reentry_summary.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
