---
title: "learnloop.scheduling.fsrs_fitting"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/fsrs_fitting.py"
source_paths:
  - "src/learnloop/scheduling/fsrs_fitting.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.fsrs_fitting module"
  - "src/learnloop/scheduling/fsrs_fitting.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.fsrs_fitting`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.fsrs_fitting` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Pure-Python FSRS-6 weight fitting on the learner's own review log.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/fsrs_fitting.py](../../../../../../src/learnloop/scheduling/fsrs_fitting.py) |
| Source lines | 210 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FsrsFittingError(ValueError)` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 43) — Raised when the review log cannot support a fit.
- `class FsrsFitResult` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 48)
- `review_log_loss(review_log: ReviewLog, weights: tuple[float, ...], *, min_elapsed_days: float) -> tuple[float, int]` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 62) — Weighted mean binary cross-entropy of recall predictions, and its N.
- `fit_fsrs_weights(review_log: ReviewLog, *, config: FsrsFittingConfig, initial: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> FsrsFitResult` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 100)

### Module constants

- `FIT_INDICES` ([src/learnloop/scheduling/fsrs_fitting.py](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 25)
- `FIT_BOUNDS` ([src/learnloop/scheduling/fsrs_fitting.py](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 29)
- `_P_CLIP` ([src/learnloop/scheduling/fsrs_fitting.py](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 40)

## Internal implementation anchors

- `_clamp_relative(relative: list[float], defaults: list[float]) -> list[float]` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 194)
- `_project(weights: list[float]) -> tuple[float, ...]` ([source](../../../../../../src/learnloop/scheduling/fsrs_fitting.py), line 202) — Bounds + w0<=w1<=w2<=w3 ordering (initial stability must be monotone in rating).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `FIT_INDICES`, `FsrsFittingError`, `fit_fsrs_weights`; statically calls `fit_fsrs_weights`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `FsrsFittingConfig`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `forgetting_curve`; calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `ReviewLog`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_fsrs_fitting.py](../../../../../../tests/test_fsrs_fitting.py) — direct import
  - `test_bounds_and_ordering_projection`
  - `test_deterministic`
  - `test_recoverability_beats_defaults_on_perturbed_weights`
  - `test_refuses_below_min_reviews`
  - `test_review_log_loss_skips_short_gaps_and_zero_weight`
  - `test_shrinkage_dominates_at_tiny_n`

## Modification guidance

- Change fsrs fitting policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/fsrs_fitting.py](../../../../../../src/learnloop/scheduling/fsrs_fitting.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
