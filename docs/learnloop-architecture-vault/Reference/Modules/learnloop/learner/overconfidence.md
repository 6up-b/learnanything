---
title: "learnloop.learner.overconfidence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/overconfidence.py"
source_paths:
  - "src/learnloop/learner/overconfidence.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.overconfidence module"
  - "src/learnloop/learner/overconfidence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.overconfidence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.overconfidence` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Overconfidence list (spec §4.3, package F5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/overconfidence.py](../../../../../../src/learnloop/learner/overconfidence.py) |
| Source lines | 117 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `blueprint_weight_by_facet(vault: LoadedVault, report: GoalReport) -> dict[tuple[str, str], float]` ([source](../../../../../../src/learnloop/learner/overconfidence.py), line 26) — Per-(LO, facet) blueprint weight, defaulting to 1.0 with no blueprints.
- `class OverconfidentFacet` ([source](../../../../../../src/learnloop/learner/overconfidence.py), line 53)
  - `as_dict(self) -> dict[str, Any]` (line 63; public)
- `overconfidence_facets(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None, min_evidence_mass: float | None=None) -> list[OverconfidentFacet]` ([source](../../../../../../src/learnloop/learner/overconfidence.py), line 76) — Ready-high / Demonstrated-false facets for ``goal``, ranked (§4.3).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `overconfidence_facets`; statically calls `overconfidence_facets`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `blueprint_weight_by_facet`; statically calls `blueprint_weight_by_facet`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `blueprint_weight_by_facet`; statically calls `blueprint_weight_by_facet`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `overconfidence_facets`; statically calls `overconfidence_facets`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `GoalReport`, `goal_report`; calls `goal_report`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]], [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_blueprint_weight_by_facet_sums_referencing_blueprints`
  - `test_overconfidence_evidence_mass_gate`
  - `test_overconfidence_excludes_demonstrated_and_low_ready`
  - `test_overconfidence_ranks_by_ready_times_weight`

## Modification guidance

- Change overconfidence policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/overconfidence.py](../../../../../../src/learnloop/learner/overconfidence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
