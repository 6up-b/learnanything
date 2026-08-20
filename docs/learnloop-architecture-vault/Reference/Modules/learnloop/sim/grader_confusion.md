---
title: "learnloop.sim.grader_confusion"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/grader_confusion.py"
source_paths:
  - "src/learnloop/sim/grader_confusion.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.grader_confusion module"
  - "src/learnloop/sim/grader_confusion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.grader_confusion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.grader_confusion` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Planted grader-confusion injection for the sim harness (spec §9.7.1, §4.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class GraderConfusion` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 28) — Asymmetric confusion over observed response classes given the TRUE class.
  - `observed_distribution(self, true_class: str) -> dict[str, float]` (line 40; public)
  - `draw_observed(self, true_class: str, rng: random.Random) -> str` (line 52; public)
- `load_confusion(name: str) -> GraderConfusion` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 76)
- `apply_confusion(*, true_criterion_points: Mapping[str, float], max_points_by_criterion: Mapping[str, float], grader_confidence: float, confusion: GraderConfusion, rng: random.Random) -> dict[str, object]` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 92) — Draw an observed coarse class per the asymmetric matrix and remap criterion points to that class, keeping the truth for scoring.
- `class PlantedMisgradeResult` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 135)
  - `as_dict(self) -> dict[str, object]` (line 143; public)
- `run_planted_misgrade_acceptance(*, confusion: GraderConfusion, prior_concentration: float=2.0, trials: int=200, seed: int=20260718, agreement_threshold: float=rc.ENSEMBLE_ACTION_AGREEMENT_THRESHOLD) -> PlantedMisgradeResult` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 200) — Drive the planted-misgrade acceptance (§9.7.1).
- `choose_prior_concentration_for_budget(*, confusion: GraderConfusion, budget_fraction: float, candidates: Sequence[float]=(1.0, 1.5, 2.0, 3.0, 5.0, 8.0), trials: int=200, seed: int=20260718) -> dict[str, object]` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 295) — The §4.2 abstention-budget loop: sweep prior concentration and choose the lowest (widest-interval) value whose abstention rate stays <= the budget while ``silent_flip_count`` stays 0.

### Module constants

- `COARSE_CLASSES` ([src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py), line 24)
- `MISGRADED_PARTIAL_OVERCALL` ([src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py), line 66)
- `BUILTIN_CONFUSIONS` ([src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py), line 71)
- `_HYPOTHESES` ([src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py), line 157)

## Internal implementation anchors

- `_true_coarse_class(rubric_score: float) -> str` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 82) — Map a fractional rubric score to the coarse true class.
- `_instrument_rows() -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 160)
- `_heuristic_channel(prior_concentration: float) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 169) — The WIDE HEURISTIC calibration channel P(E | Z) the robust path actually uses.
- `_point_diagnosis(observed_class: str, rows: Mapping[str, Mapping[str, float]]) -> str` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 188) — The naive point-estimate diagnosis: treat the observed class as Z and pick the hypothesis whose instrument row makes it most likely.
- `_draw_from(dist: Mapping[str, float], rng: random.Random) -> str` ([source](../../../../../../src/learnloop/sim/grader_confusion.py), line 284)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `apply_confusion`; statically calls `apply_confusion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `build_ensemble`, `decision_context_hash`, `observed_update`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
  - `test_abstention_budget_loop_chooses_or_alarms`
  - `test_apply_confusion_is_a_noop_for_success_truth`
  - `test_apply_confusion_overcalls_partial_as_success_asymmetrically`
  - `test_clean_grades_do_not_flip_and_do_not_silently_flip`
  - `test_overconfident_point_channel_does_silently_flip`
  - `test_planted_confusion_never_silently_flips_under_wide_authority`
  - `test_runner_planted_confusion_no_silent_diagnosis_flip_through_robust_path`

## Modification guidance

- Make changes here when the responsibility remains grader confusion within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/grader_confusion.py](../../../../../../src/learnloop/sim/grader_confusion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
