---
title: "learnloop.attempts.surprise"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/surprise.py"
source_paths:
  - "src/learnloop/attempts/surprise.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.surprise module"
  - "src/learnloop/attempts/surprise.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.surprise`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps surprise behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `SurpriseResult`, `compute_observation_variance`, `compute_surprise`, `predicted_error_type_distribution`, `score_bucket`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/surprise.py](../../../../../../src/learnloop/attempts/surprise.py) |
| Source lines | 229 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SurpriseResult` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 25)
  - `as_record(self, attempt_id: str, algorithm_version: str, created_at: str) -> dict[str, object]` (line 35; public)
- `compute_observation_variance(observation: MasteryObservation, config: LearnLoopConfig) -> float` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 53) — Legacy logit-space observation variance (used when IRT is disabled).
- `compute_surprise(*, prior: MasteryState, posterior: MasteryState, observation: MasteryObservation, observed_error_type: str | None, prior_active_errors: list[ActiveErrorEvent], config: LearnLoopConfig, item_a: float=1.0, item_b: float=0.0, forecast: Any=None, priming_offset: float=0.0, record_source: bool=False, direct: bool=False) -> SurpriseResult` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 66) — ``forecast`` (a :class:`~learnloop.attempts.surprise_forecast.SurpriseForecast`, from the label's retirement): adaptive difficulty's ``p̄`` made before the answer, which the predictive part is scored against (its innovation, variance and direction around ``b' = μ_prior − logit(p…
- `predicted_error_type_distribution(prior_active_errors: list[ActiveErrorEvent], *, observed_at: datetime) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 204)
- `score_bucket(rubric_score: int, max_points: int=4) -> str` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 223)

## Internal implementation anchors

- `_open_logit(p: float, clip: float) -> float` ([source](../../../../../../src/learnloop/attempts/surprise.py), line 59) — ``logit(p)``, exact inside (0, 1); a degenerate 0 or 1 is held at the configured clip.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `SurpriseResult`, `compute_surprise`; statically calls `compute_surprise`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `score_bucket`; statically calls `score_bucket`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `forecast_clipped_after_shift`; calls `forecast_clipped_after_shift`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MasteryState`
- [[Reference/Modules/learnloop/db/stores/learner_model|learnloop.db.stores.learner_model]] — imports `ActiveErrorEvent`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `irt_observation`, `irt_observation_at`, `logit`, `observation_weight`, `sigmoid`; calls `irt_observation`, `irt_observation_at`, `logit`, `observation_weight`, `sigmoid`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_surprise.py](../../../../../../tests/test_surprise.py) — direct import
- [tests/test_surprise_forecast_scoring.py](../../../../../../tests/test_surprise_forecast_scoring.py) — direct import
- [tests/test_teacher_te5_grade_curves.py](../../../../../../tests/test_teacher_te5_grade_curves.py) — direct import
  - `test_upgrade_labels_superseded_epochs_and_keeps_a_legacy_stamp`

## Modification guidance

- Change surprise policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/surprise.py](../../../../../../src/learnloop/attempts/surprise.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
