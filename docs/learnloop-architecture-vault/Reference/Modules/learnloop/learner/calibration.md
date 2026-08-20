---
title: "learnloop.learner.calibration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/calibration.py"
source_paths:
  - "src/learnloop/learner/calibration.py"
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
  - "learnloop.learner.calibration module"
  - "src/learnloop/learner/calibration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.calibration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.calibration` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Difficulty-miscalibration monitor (spec_irt_difficulty.md §7.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/calibration.py](../../../../../../src/learnloop/learner/calibration.py) |
| Source lines | 102 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MiscalibrationFlag` ([source](../../../../../../src/learnloop/learner/calibration.py), line 21)
  - `message(self) -> str` (line 29; public)
- `difficulty_miscalibration_flags(vault: LoadedVault, repository, *, min_attempts: int=DEFAULT_MIN_ATTEMPTS, threshold: float=DEFAULT_INNOVATION_THRESHOLD) -> list[MiscalibrationFlag]` ([source](../../../../../../src/learnloop/learner/calibration.py), line 39) — Per-item flags where the mean innovation ``y - p`` is persistently one-sided.

### Module constants

- `DEFAULT_MIN_ATTEMPTS` ([src/learnloop/learner/calibration.py](../../../../../../src/learnloop/learner/calibration.py), line 16)
- `DEFAULT_INNOVATION_THRESHOLD` ([src/learnloop/learner/calibration.py](../../../../../../src/learnloop/learner/calibration.py), line 17)

## Internal implementation anchors

- `_expected_correctness(predicted_score_dist_json: str | None) -> float | None` ([source](../../../../../../src/learnloop/learner/calibration.py), line 94)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `difficulty_miscalibration_flags`; statically calls `difficulty_miscalibration_flags`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
  - `test_balanced_innovation_is_not_flagged`
  - `test_below_min_attempts_is_not_flagged`
  - `test_persistent_overperformance_flags_too_hard`
  - `test_persistent_underperformance_flags_too_easy`
  - `test_pipeline_flags_an_item_rated_too_hard`
  - `test_samples_without_expected_correctness_are_skipped`
  - `test_threshold_and_min_attempts_are_configurable`
  - `test_unknown_items_are_ignored`

## Modification guidance

- Change calibration policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/calibration.py](../../../../../../src/learnloop/learner/calibration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
