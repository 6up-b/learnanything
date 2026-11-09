---
title: "learnloop.router_objective.miss_cause"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/miss_cause.py"
source_paths:
  - "src/learnloop/router_objective/miss_cause.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.miss_cause module"
  - "src/learnloop/router_objective/miss_cause.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.miss_cause`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.miss_cause` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: Slip or gap (SG; ``docs/specs/spec_slip_vs_gap_v1.md``): what the router knows about a miss's cause, per topic.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py) |
| Source lines | 804 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `latest_misses(connection: Any, config: Any, learning_object_ids: Iterable[str], now_iso: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 159) — Per topic, its latest missed cold check since its last lesson ended, known at ``now_iso`` (THE availability predicate); topics with none are absent.
- `diagnosis_state(connection: Any, attempt_id: str, now_iso: str) -> tuple[str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 205) — The miss's status and its live diagnosis in force (THE eligibility rule, ``DiagnosisStoreMixin._diagnosis_in_force``), both as known at ``now_iso``.
- `prior_weights(proposal: Mapping[str, Any]) -> tuple[dict[str, float], int] | None` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 240) — The diagnosis's normalized prior weights by causal class, averaged over its events (each event's candidate causes normalized as ``diagnosis.forecast_receipts`` does: a cause with no weight takes the mean of the others).
- `probe_posterior(connection: Any, attempt_id: str, now_iso: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 280) — A probe episode's posterior on the miss's factor, by causal class, as known at ``now_iso``: the latest of the episode's completion posterior and its observations' posteriors.
- `my_gap_marks(connection: Any, attempt_id: str, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 331) — Hypotheses the learner marked ``my_gap`` on the miss (the latest mark per hypothesis counts), as known at ``now_iso``: their key and causal class, never their statement.
- `stored_surprise(connection: Any, attempt_id: str, now_iso: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 363) — The attempt's stored surprise, as written by ``now_iso`` (None: whatever is on record).
- `record_for(connection: Any, miss: Mapping[str, Any], now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 379) — One topic's sensor, from its latest miss.
- `sensor(connection: Any, config: Any, learning_object_ids: Iterable[str], now_iso: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 414) — SG1: per candidate topic with a missed cold check since its last lesson, its record (module docstring).
- `mark(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 421) — What a prefetch boundary's identity names so a change in a sensor (a diagnosis landing, a probe answered) starts a new job.
- `ledger_mark(connection: Any) -> list[Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 430) — SG2 (Codex F1): what ``β``'s and the cause slopes' fits read beyond a new attempt (which the boundary's ``as_of`` already names): the live diagnoses on record, the lessons' openings and closes, and the stored surprises, each as a count and the latest write.
- `surprise_reference(connection: Any, config: Any, now_iso: str) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 449) — The Bayesian surprise of every missed cold check on record at ``now_iso`` (any topic): the learner's own distribution a miss's surprise is standardized and ranked against.
- `moments(reference: Sequence[float]) -> tuple[float, float] | None` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 465) — The reference's mean and standard deviation, computed once per decision (Codex F8); None with no spread.
- `standardized(value: float | None, reference: Sequence[float] | tuple[float, float] | None) -> float` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 475) — ``(value − mean) / sd`` over ``reference`` (the values, or their :func:`moments`); 0 when there is no spread to standardize by (then ``β`` has nothing to act on) or no value.
- `surprise_words(surprise: Mapping[str, Any] | None, reference: Sequence[float]) -> str` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 492) — The surprise in words: its direction (the surprise module's own label) and where its Bayesian surprise ranks among the learner's recorded misses (a rank, never a cut-off).
- `beta_rows(connection: Any, config: Any, now_iso: str) -> tuple[list[dict[str, Any]], dict[str, int]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 534) — ``β``'s data (module docstring): each diagnosed missed cold check known at ``now_iso`` whose topic's next attempt was a cold check, with nothing on the topic in between.
- `beta_fit(connection: Any, config: Any, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 588) — ``β``'s Laplace posterior: ``P(the next cold check is missed) = σ(logit p_gap + β·s)`` with the prior :data:`BETA_PRIOR`, by Newton's method (the log posterior is concave).
- `fit_beta(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 596) — :func:`beta_fit`'s arithmetic on its rows (each ``p_gap`` in (0, 1), ``s``, ``missed_again``): pure.
- `calibrated(record: Mapping[str, Any], beta: float, s: float) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 643) — ``(p̃_gap, p̃_slip, p̃_unknown)``: ``logit p̃_gap = logit p_gap + β·s``, the rest of the mass split between slip and unknown in the diagnosis's own proportion.
- `cause_slopes(connection: Any, gamma: tuple[float, float], now_iso: str, config: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 703) — ``(γ_gap, γ_slip)``'s posterior.
- `value_inputs(connection: Any, config: Any, records: Mapping[str, Mapping[str, Any]], gamma: tuple[float, float], now_iso: str) -> tuple[dict[str, tuple[float, float, float]], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 736) — SG2: each diagnosed topic's calibrated ``(p_gap, p_slip, p_unknown)`` and the record of how (``β``'s fit, each topic's ``s``, the cause slopes).
- `card_entry(record: Mapping[str, Any], *, topic: str, days_before: float | None, reference: Sequence[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 765) — What the LLM policy's card shows of one topic's sensor: the cause class probabilities, the surprise in words and the status.

### Module constants

- `VERSION` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 49)
- `CALIBRATION_VERSION` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 50)
- `SLOPES_VERSION` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 51)
- `GAP` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 54)
- `SLIP` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 55)
- `UNKNOWN` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 56)
- `CLASSES` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 57)
- `CLASS_WORDS` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 59)
- `DIAGNOSED` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 62)
- `PENDING` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 63)
- `FAILED` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 64)
- `NONE` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 65)
- `NOT_APPLICABLE` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 66)
- `STATUSES` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 67)
- `BASIS_POSTERIOR` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 70)
- `BASIS_PRIOR` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 71)
- `FULLY_RIGHT` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 76)
- `BETA_PRIOR` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 81)
- `_NEWTON_STEPS` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 84)
- `SELF_SELECTED` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 86)
- `OBSERVATIONAL` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 89)
- `_DIRECTION_WORDS` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 487)
- `CARD_NOTE` ([src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py), line 790)

### Explicit exports

`__all__` declares:

- `BASIS_POSTERIOR`
- `BASIS_PRIOR`
- `BETA_PRIOR`
- `CALIBRATION_VERSION`
- `CARD_NOTE`
- `CLASSES`
- `CLASS_WORDS`
- `DIAGNOSED`
- `FAILED`
- `FULLY_RIGHT`
- `GAP`
- `NONE`
- `NOT_APPLICABLE`
- `OBSERVATIONAL`
- `PENDING`
- `SELF_SELECTED`
- `SLIP`
- `SLOPES_VERSION`
- `STATUSES`
- `UNKNOWN`
- `VERSION`
- `beta_fit`
- `beta_rows`
- `calibrated`
- `card_entry`
- `cause_slopes`
- `diagnosis_state`
- `fit_beta`
- `latest_misses`
- `ledger_mark`
- `mark`
- `moments`
- `my_gap_marks`
- `prior_weights`
- `probe_posterior`
- `record_for`
- `sensor`
- `standardized`
- `stored_surprise`
- `surprise_reference`
- `surprise_words`
- `value_inputs`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 93)
- `_loads(raw: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 98)
- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 107)
- `_log_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 111) — ``log σ(x)``, stable on both tails.
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 117)
- `_cold_filter_sql() -> tuple[str, tuple[Any, ...]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 127)
- `_exposed(connection: Any) -> set[str]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 135)
- `_lessons_ended(connection: Any, now_iso: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 142) — Per LO, when its last lesson known at the decision ended (``router_suggestions.last_lesson_ended_by_learning_object``, bounded at the decision: a lesson opened after it is not there).
- `_pending(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 194)
- `_class(scope: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 235)
- `_factors(connection: Any, attempt_id: str) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 273)
- `_between(connection: Any, config: Any, lo: str, after: str, before: str, after_id: str, before_id: str, now_iso: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 509) — Whether anything happened on the topic strictly between two attempts: another attempt known at ``now_iso`` (RO1's availability predicate, landing ruling R1: an attempt imported later is not there yet; the window itself stays by when the work happened), or a lesson opened.
- `_offer_rows(connection: Any, config: Any, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/miss_cause.py), line 658) — Lessons that ran from an offer whose card froze this sensor (diagnosed), closed by ``now_iso``, with the first qualifying cold outcome after their close (``lesson_weight.qualifying_outcomes``), counted only once that outcome is known at the decision (THE availability predicate;…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; statically calls `sensor`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `CARD_NOTE`, `module`; statically calls `card_entry`, `sensor`, `surprise_reference`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `ledger_mark`, `mark`, `sensor`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `sensor`, `value_inputs`
- [[Reference/Modules/learnloop/router_objective/miss_cause_report|learnloop.router_objective.miss_cause_report]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `LESSON_PROBE_EXPOSED_SOURCE`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `DiagnosisStoreMixin`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `marks_for_attempt`, `present`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `attempts_classified_by`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `module`; calls `latest_marks`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `COLD_ATTEMPT_TYPES`, `qualifying_outcomes`; calls `qualifying_outcomes`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/miss_cause_report|learnloop.router_objective.miss_cause_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_a_diagnosis_written_after_the_decision_is_not_read`
  - `test_a_my_gap_mark_is_recorded_beside_the_probabilities_never_folded_in`
  - `test_a_probe_posterior_on_the_misss_factor_overrides_the_prior_weights`
  - `test_a_pure_gap_by_rounding_never_crashes_the_calibration`
  - `test_a_slip_a_gap_and_an_unknown_give_the_diagnosis_weights_by_class`
  - `test_an_episode_with_no_posterior_yet_leaves_the_prior_weights`
  - `test_an_observations_posterior_is_read_while_the_episode_is_open`
  - `test_at_beta_zero_the_sensor_is_the_diagnosiss`
  - `test_beta_moves_with_the_data_in_the_direction_the_outcomes_point`
  - `test_betas_fit_excludes_a_lesson_or_another_attempt_between_the_miss_and_the_check`
  - `test_betas_newton_converges_where_an_undamped_step_cycles`
  - `test_events_average_and_a_cause_with_no_weight_takes_the_mean_of_the_others`
  - `test_nothing_adds_a_threshold`
  - `test_nothing_protected_or_answer_restating_reaches_the_card_and_probe_attempts_gain_the_cause`
  - `test_pending_failed_and_absent_diagnoses_are_explicit_never_a_slip`
  - `test_sg1_freezes_the_sensor_and_every_number_is_the_predecessors`
  - `test_the_cause_slopes_learn_from_a_lesson_that_ran_from_a_diagnosed_offer`
  - `test_the_latest_miss_is_the_one_read_and_it_is_lesson_suggestions_own_miss`
  - `test_the_report_names_its_labels`
  - `test_with_no_data_beta_and_the_slopes_are_their_seeded_priors`

## Modification guidance

- Make changes here when the responsibility remains miss cause within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/miss_cause.py](../../../../../../src/learnloop/router_objective/miss_cause.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
