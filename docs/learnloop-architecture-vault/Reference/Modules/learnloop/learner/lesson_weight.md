---
title: "learnloop.learner.lesson_weight"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/lesson_weight.py"
source_paths:
  - "src/learnloop/learner/lesson_weight.py"
source_commit: "49f359311a7daeac5245231bd6ef6e4c14cb2bfd"
source_commit_timestamp: "2026-11-05T23:30:15-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.lesson_weight module"
  - "src/learnloop/learner/lesson_weight.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.lesson_weight`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.lesson_weight` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: The learned lesson-check weight, the forecast pool and the tap/hedge recalibration (teacher TE1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py) |
| Source lines | 1091 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `49f359311a7daeac5245231bd6ef6e4c14cb2bfd` |
| Commit timestamp | `2026-11-05T23:30:15-05:00` |

## Public API

- `class WeightState` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 197) — The three posteriors as of some instant, with the per-update trace.
  - `_ensure_lo(self, learning_object_id: str) -> int` (line 213; internal)
  - `_h(self, learning_object_id: str, z_c: float, z_p: float) -> list[np.ndarray]` (line 229; internal)
  - `tau_weights(self) -> np.ndarray` (line 240; public)
  - `eta_moments(self, learning_object_id: str, z_c: float, z_p: float) -> list[tuple[float, float]]` (line 243; public) — ``(m, v)`` of η per τ point (an LO never seen has its offset at the prior, variance τ²).
  - `learned_mass(self, learning_object_id: str, z_c: float, z_p: float) -> float` (line 256; public) — §12.1's mass as of now: the posterior mean of σ(η) (in (0, 1) by the link).
  - `pool_lambda(self, family: str) -> float` (line 263; public) — λ̂, the pool weight's posterior mean for ``family`` (the seeded prior's mean before any update).
  - `tap_probability(self, tap: int) -> float` (line 272; public)
  - `hedge_probability(self, hedge: str) -> float` (line 276; public)
- `confidence_term(state: WeightState, tap: int | None, hedge: str | None) -> tuple[float, str]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 280) — ``(z_c, source)``: the tap's recalibrated probability on the logit scale (else the hedge read's, else 0, "neither"), centred on chance (``logit 0.5 = 0``: no confidence information).
- `prediction_term(p: float | None, band: tuple[float, float]) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 291) — ``z_p``: the predicted success on the logit scale, centred at the band's middle (§12.1).
- `class CheckSensitivity` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 303) — What the check left in the mastery model, recorded at the check, as a function of its mass.
  - `as_dict(self) -> dict[str, Any]` (line 314; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'CheckSensitivity'` (line 320; public)
- `posterior_after(sensitivity: CheckSensitivity, mass: float, mastery_config: Any) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 327) — ``(μ, P)`` after the check entered at ``mass`` (the mastery model's own update).
- `predicted_success(mu: float, variance: float, *, a: float, b: float, drift: float=0.0, days: float=0.0) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 348) — The mastery model's success probability with its uncertainty (the moderated logistic, the probit approximation ``σ(a(μ − b) / √(1 + π a² V / 8))``), ``V`` grown by ``drift`` per day.
- `class RecordedUpdate` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 367) — One mastery update on the check's LO as the attempt step made it: its grade, its item, and the observation factors it entered with (the observation weight the attempt step recorded, which carries coverage, grading reliability, hints, the error sharpening and the familiarity disc…
- `recorded_trajectory(connection: Any, vault: Any, mastery_config: Any, check: Mapping[str, Any], outcome: Mapping[str, Any]) -> list[RecordedUpdate] | None` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 407) — The check's own update and every update on its LO after it and before the outcome, in order, each with its recorded factors; None when one of them left no record to recompute it from.
- `trajectory_state(sensitivity: 'CheckSensitivity', updates: Sequence[RecordedUpdate], *, mass: float, recorded_mass: float, mastery_config: Any) -> Any` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 461) — The LO's mastery state just before the outcome, recomputed from the check's recorded prior with the check entered at ``mass`` and every other update as recorded.
- `trajectory_success(state: Any, *, a: float, b: float, at: str, mastery_config: Any) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 490) — The mastery model's predicted success at ``at`` from ``state`` (its drift since the last evidence, held to ``p_max`` as the model holds it).
- `pool_implied_mass(sensitivity: CheckSensitivity, target: float, mastery_config: Any, *, a: float | None=None, b: float | None=None, days: float=0.0) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 500) — The mass at which the mastery update makes the predicted success equal ``target`` (§12.2): the success on the committed cold item (``a``, ``b``; the check's own item when not given) at the forecast's horizon (``days`` of drift), the same item and horizon ``target``'s ``p_A`` was…
- `forecast_p_a(forecast: Mapping[str, Any], outcome: Mapping[str, Any], mastery_config: Any) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 604) — ``p_A`` for the outcome that resolves a forecast: the mastery prediction from the state the forecast was made at, for the resolving item at the outcome's horizon (both predictors of the same cold outcome, §12.2; review F5).
- `read_hedges(connection: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 668) — Each attempt's hedge read from its current grading evidence (``confidence_events.read_hedges``'s rule, read here so the evidence side imports no context module; a test pins the two equal).
- `qualifying_outcomes(connection: Any, learning_object_ids: Iterable[str], after: str | None, *, until: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 729) — Graded attempts that can resolve a lesson check (§12.1), in order: on one of the LOs, after ``after``, of a cold type (:data:`COLD_ATTEMPT_TYPES`), unprimed, with no hint, the item's first attempt, with no reveal row on the item before it.
- `replay_state(vault: Any, repository: Any, *, as_of: str | None=None, through: str | None=None, prior_shift: Mapping[str, float] | None=None) -> WeightState` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 797) — The three posteriors from the ledgers, in order, with every event strictly before ``as_of`` (all of them when None): the prequential filter both the live check and the replayer run.
- `lesson_check_mass(repository: Any, attempt_id: str, attempt_type: str) -> float | None` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 894) — The mass a lesson check's attempt enters mastery at, as recorded when it was graded; None for every other attempt (the type's configured mass applies).
- `write_state(repository: Any, state: WeightState) -> dict[str, int]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 950) — Replace the three DERIVED tables with ``state`` (in the caller's transaction).
- `any_lessons(repository: Any) -> bool` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 970)
- `tables_through(repository: Any) -> str | None` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 977) — The instant the DERIVED tables describe: the latest answered lesson check (the live path writes them right after each check, so the replayer bounds its replay at the same instant and the two agree row for row whatever happened since; review claim on rebuild equivalence).
- `rebuild_lesson_weight_state(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 989) — The replayer (``substrate.rebuild_orchestrator``): clear the three DERIVED tables and recompute them through the latest answered lesson check (:func:`tables_through`), exactly as the live path wrote them then.
- `mass_mismatches(state: WeightState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 1007) — Checks whose recorded mass a replay would not reproduce (the equivalence guard): the mass applied under its rule must equal the learned mass recomputed as of the check.
- `pool_trajectory(trace: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 1030) — The pool weight's trajectory per forecaster (teacher TE2-log, spec_teacher_v1 §11.10): λ̂ and its posterior sd from the seeded prior (``at`` None), then after each ``pool_update`` of the trace (what ``lesson_weight_trace`` holds), re-applied in order exactly as :func:`_resolve_f…

### Module constants

- `PRIORS_VERSION` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 91)
- `STATE_VERSION` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 93)
- `ETA0_PRIOR_MEAN` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 97)
- `ETA0_PRIOR_SD` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 99)
- `BETA_C_PRIOR_SD` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 102)
- `BETA_P_PRIOR_SD` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 103)
- `TAU_GRID` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 106)
- `POOL_GRID_POINTS` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 110)
- `POOL_PRIOR_ALPHA` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 112)
- `POOL_PRIOR_BETA` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 113)
- `TAP_PRIOR_MAP` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 118)
- `TAP_INTERCEPT_PRIOR` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 120)
- `TAP_SLOPE_PRIOR` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 121)
- `HEDGE_INTERCEPT_PRIOR` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 123)
- `HEDGE_VALUES` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 124)
- `COLD_ATTEMPT_TYPES` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 128)
- `LESSON_CHECK_ATTEMPT_TYPE` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 129)
- `_IMPLIED_ETA_BOUND` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 132)
- `_BISECTION_STEPS` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 133)
- `RULE_FIXED` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 136)
- `RULE_LEARNED` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 137)
- `RULE_POOL` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 138)
- `PRIOR_TERMS` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 794)
- `DERIVED_TABLES` ([src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py), line 947)

### Explicit exports

`__all__` declares:

- `BETA_C_PRIOR_SD`
- `BETA_P_PRIOR_SD`
- `CheckSensitivity`
- `COLD_ATTEMPT_TYPES`
- `DERIVED_TABLES`
- `ETA0_PRIOR_MEAN`
- `ETA0_PRIOR_SD`
- `POOL_GRID_POINTS`
- `POOL_PRIOR_ALPHA`
- `POOL_PRIOR_BETA`
- `PRIORS_VERSION`
- `RULE_FIXED`
- `RULE_LEARNED`
- `RULE_POOL`
- `RecordedUpdate`
- `TAP_PRIOR_MAP`
- `TAU_GRID`
- `WeightState`
- `any_lessons`
- `confidence_term`
- `lesson_check_mass`
- `pool_implied_mass`
- `pool_trajectory`
- `posterior_after`
- `predicted_success`
- `prediction_term`
- `qualifying_outcomes`
- `read_hedges`
- `rebuild_lesson_weight_state`
- `recorded_trajectory`
- `tables_through`
- `replay_state`
- `trajectory_state`
- `trajectory_success`
- `write_state`

## Internal implementation anchors

- `class _Bank` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 147) — One τ grid point's Gaussian over (η₀, β_c, β_p, u_L...).
- `_prior_bank(tau: float) -> _Bank` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 156)
- `_pool_grid() -> np.ndarray` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 162)
- `_pool_prior_log_w() -> np.ndarray` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 166) — Beta(1, 4) discretized on the grid (the endpoint λ = 1 has density 0: a tiny floor keeps it a point).
- `class _Calibration` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 177) — A Gaussian over a recalibration's coefficients and how many answers moved it.
- `_tap_prior() -> _Calibration` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 186)
- `_hedge_prior() -> _Calibration` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 191)
- `_days(start: str, end: str) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 356)
- `_interpretation_variance(mu: float, variance: float, last: str | None, at: str, *, a: float, b: float, weight: float, variance_after: float, config: Any) -> float` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 388) — The extra observation noise an update carried, recovered from its recorded variance step (``P_after = (1 − K·H)·P_pred``, ``K·H = H²P/(H²P + R)``), less the weight's own part of ``R``.
- `_soft_log_lik(p: np.ndarray, y: float) -> np.ndarray` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 538)
- `_resolve_check(state: WeightState, check: Mapping[str, Any], outcome: Mapping[str, Any], share: float, mastery_config: Any, trajectory: Sequence[RecordedUpdate] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 543) — One check's factor from its resolving outcome, at power ``share``.
- `_resolve_forecast(state: WeightState, forecast: Mapping[str, Any], outcome: Mapping[str, Any], share: float, mastery_config: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 619)
- `_calibrate(state: WeightState, attempt: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 638)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 663)
- `_checks(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 693)
- `_forecasts(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 713)
- `_calibration_attempts(connection: Any, hedges: Mapping[str, str], until: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 762)
- `_outcome_item_params(vault: Any, mastery_config: Any, outcome: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 782)
- `_mass_detail(state: WeightState, check: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 875) — The check's recorded mass beside what the posterior as of the check gives (the equivalence guard: :func:`mass_mismatches`), with the recalibrated confidence term recomputed too.
- `_state_rows(state: WeightState) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 912)
- `_pool_moments(log_w: np.ndarray) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/lesson_weight.py), line 1023)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `lesson_check_mass`; statically calls `lesson_check_mass`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `COLD_ATTEMPT_TYPES`, `predicted_success`; statically calls `predicted_success`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `predicted_success`; statically calls `predicted_success`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `qualifying_outcomes`; statically calls `qualifying_outcomes`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_lesson_weight_state`; statically calls `rebuild_lesson_weight_state`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `predicted_success`, `read_hedges`; statically calls `predicted_success`, `read_hedges`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; statically calls `CheckSensitivity`, `confidence_term`, `pool_implied_mass`, `posterior_after`, `predicted_success`, `prediction_term`, `replay_state`
- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `module`; statically calls `pool_trajectory`, `replay_state`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `predicted_success`, `read_hedges`, `replay_state`, `tables_through`, `write_state`; statically calls `predicted_success`, `replay_state`, `tables_through`, `write_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `NODES`, `WEIGHTS`, `adf_update`, `gaussian_sigmoid_mean`, `logit`, `normalized_log_weights`, `sigmoid`; calls `adf_update`, `gaussian_sigmoid_mean`, `logit`, `normalized_log_weights`, `sigmoid`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MasteryState`; calls `MasteryState`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `item_irt_params`, `update_mastery`; calls `MasteryObservation`, `item_irt_params`, `update_mastery`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f2_a_held_cold_grade_resolves_nothing_until_released`
  - `test_f5_a_forecast_agreeing_with_the_cold_prediction_leaves_the_mass_near_the_learned_one`
  - `test_f5_the_pool_inverts_on_the_committed_cold_item_not_the_check`
  - `test_f6_the_trajectory_at_the_recorded_mass_reproduces_the_outcomes_recorded_prior`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_the_whole_rebuild_owns_the_lesson_weight_tables_and_reproduces_them`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_a_later_cold_outcome_resolves_the_check_and_moves_the_weight`
  - `test_a_lessonless_vault_rebuilds_to_empty_tables`
  - `test_a_primed_or_hinted_or_seen_or_earlier_attempt_never_resolves_a_check`
  - `test_before_any_outcome_the_mass_is_the_seeded_prior_centre`
  - `test_planted_recovery_a_check_whose_cold_outcomes_agree_raises_the_mass`
  - `test_the_attempt_step_reads_the_recorded_mass_live_and_in_replay`
  - `test_the_derived_state_rebuild_reproduces_the_live_tables_exactly`
  - `test_the_hedge_reader_matches_confidence_events`
  - `test_the_pool_implied_mass_is_the_parametric_mass_at_lambda_zero`
  - `test_the_pool_mixes_in_the_teachers_forecast_and_learns_from_the_outcome`
  - `test_the_tap_map_and_the_hedge_read_are_the_existing_ones`
  - `test_the_tap_recalibration_learns_from_every_tapped_graded_answer`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`

## Modification guidance

- Change lesson weight policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/lesson_weight.py](../../../../../../src/learnloop/learner/lesson_weight.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
