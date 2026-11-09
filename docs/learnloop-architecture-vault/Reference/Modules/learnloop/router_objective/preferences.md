---
title: "learnloop.router_objective.preferences"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/preferences.py"
source_paths:
  - "src/learnloop/router_objective/preferences.py"
source_commit: "3fff1f3022217d06c78dc20963746a11650aad19"
source_commit_timestamp: "2026-11-09T09:03:50-05:00"
source_worktree_state: "clean"
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
  - "learnloop.router_objective.preferences module"
  - "src/learnloop/router_objective/preferences.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.preferences`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.preferences` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: Instruct hand-off IH4 (spec_instruct_handoff_v1 §7): what the learner said would help, in the numeric policy.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py) |
| Source lines | 430 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3fff1f3022217d06c78dc20963746a11650aad19` |
| Commit timestamp | `2026-11-09T09:03:50-05:00` |

## Public API

- `kind_of(*, reading: Any, subtype: str | None, lane: str | None) -> str` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 98) — The plain kind of a block: a lesson offer, a reading, new material, a review, or another question (repair and push practice).
- `class Features` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 117) — What the choice model reads at a decision and froze at a preference: one function at both.
  - `vector(self) -> np.ndarray` (line 124; public)
  - `as_dict(self) -> dict[str, Any]` (line 131; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'Features'` (line 137; public)
- `features_at(connection: Any, config: Any, *, at: str, minutes_left: float | None) -> Features` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 148) — The features at ``at``: its local hour (read at hour resolution, as a lesson offer's context), the plan's minutes left, and how far the latest graded answer known by then fell short (0 with none; through THE availability predicate).
- `class ChoiceState` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 177) — The model's posterior as of some instant: per kind, the effects' Gaussian.
  - `observe(self, features: Features, offered: Sequence[str], chosen: str) -> None` (line 183; public) — One use of the link: the chosen kind and each other offered kind, one step each.
  - `predict(self, features: Features, kinds: Sequence[str]) -> dict[str, float]` (line 199; public) — ``P(kind | the link was used here)`` over ``kinds``: each kind's predictive, normalized over them.
- `replay(rows: Sequence[Mapping[str, Any]], *, at: str | None=None) -> tuple[ChoiceState, dict[str, int]]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 212) — The model as of ``at`` from ``router_learner_preferences`` rows, and what they were: ``on_record``, ``read``, ``no_frozen_features`` (written with the switch off), and of those read ``agreed`` and ``no_draw``.
- `mark(connection: Any, config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 236) — What a boundary's identity names so a new preference never reuses a job made before it: the ledger's size and latest row, or nothing (switch off, none on record, or the table absent), so every other key keeps its bytes.
- `scaled(p: Mapping[str, float], q: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 251) — ``V_pref`` per candidate: ``p`` standardized over the candidates, times the spread of their ``Q̄`` (uniform over the support: the mix's ``μ`` does not exist yet when the numeric policy answers, and depends on it).
- `with_values(preference: Mapping[str, Any], q: Mapping[str, float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 265) — The sensor with each candidate's ``V_pref`` at the evaluation that answered (the tail's ``Q̄``), frozen exactly, so the shift and the contrasts read one number.
- `frozen_values(row: Any) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 275) — A logged decision's frozen ``V_pref`` by ref, or None: no sensor, nothing on record then, or a candidate without one.
- `contrast(*, decision_id: str, decided_at: str, window_closes_at: str, served: str, distribution: Mapping[str, float], values: Mapping[str, float], tail: Mapping[str, float], found: S.Bounded) -> LT.Contrast | None` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 290) — One draw's contrast (module docstring): ``Ĉ = d(A)·Ĝ`` against ``Σπ·d·Q_tail`` and ``Σπ·d²``; None with no spread under ``π`` (every candidate one kind: nothing to test, known before the draw).
- `contrasts(connection: Any, config: Any, rows: Sequence[Any], *, at: str) -> tuple[list[LT.Contrast], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 312) — Every logged draw with a frozen sensor whose window closed before ``at`` (:class:`tail_data.Logged` rows: the mix's draws only; a pick has no trace), with its missing terms bounded (RO6's landing ruling R1).
- `weight(connection: Any, config: Any, rows: Sequence[Any], *, at: str) -> tuple[LT.WeightFit, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 343) — ``w_pref`` as of ``at``: RO6's :func:`learned_tail.residual_weight` over :func:`contrasts`, at RO6's labelled prior (``residual_weight_prior_sd``), with its clip to ``[0, 1]`` times ``P(rank > 0)``.
- `fitted(found: Sequence[LT.Contrast], *, prior_sd: float, at: str | None=None) -> LT.WeightFit` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 354) — :func:`learned_tail.residual_weight` over ``found``, its noise with the fit's degrees of freedom off: every row here is a draw, so with few of them a fit through the rows would otherwise report no noise and drop the prior.
- `record(repository: Any, config: Any, *, kinds: Mapping[str, str], minutes_left: float | None, now_iso: str, fit: bool=True) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 372) — A ``plan_block`` decision's sensor and ``w_pref``, or None with nothing to say (no preference with frozen features known at ``now_iso``), so its trace and every value are the predecessor's.
- `moves_the_value(preference: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 408) — ``w_pref`` has moved: only then does anything shift (at 0 the evaluation is handed on untouched, bit for bit).
- `shifted(evaluation: Any, preference: Mapping[str, Any], *, tail: Mapping[str, float]) -> Any` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 415) — The evaluation the numeric policy's argmax reads: each candidate's draws moved by ``w_pref·V_pref``, a constant per candidate, so the paired precision is the tail's (as ``tail_serve.shifted``).

### Module constants

- `LOG` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 71)
- `VERSION` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 73)
- `WEIGHT_VERSION` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 74)
- `CHOICE_VERSION` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 76)
- `PRIORS_VERSION` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 77)
- `FEATURES_KEY` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 79)
- `KINDS` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 83)
- `WORDS` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 84)
- `TERMS` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 94)
- `_LESSON_SUBTYPE` ([src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py), line 95)

### Explicit exports

`__all__` declares:

- `CHOICE_VERSION`
- `ChoiceState`
- `FEATURES_KEY`
- `Features`
- `KINDS`
- `LESSON`
- `NEW`
- `PRIORS_VERSION`
- `QUESTION`
- `READ`
- `REVIEW`
- `STOP`
- `TERMS`
- `VERSION`
- `WEIGHT_VERSION`
- `WORDS`
- `contrast`
- `contrasts`
- `features_at`
- `fitted`
- `frozen_values`
- `scaled`
- `with_values`
- `kind_of`
- `mark`
- `moves_the_value`
- `record`
- `replay`
- `shifted`
- `weight`

## Internal implementation anchors

- `_local_hour(at: str) -> float` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 143)
- `_prior() -> tuple[np.ndarray, np.ndarray]` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 167) — One kind's seeded Gaussian.
- `_exact(value: float) -> str` ([source](../../../../../../src/learnloop/router_objective/preferences.py), line 366) — As ``tail_serve._exact``: the trace rounds every float, and the shift must recompute.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `KINDS`, `LESSON`, `NEW`, `QUESTION`, `READ`, `REVIEW`, `STOP`, `WORDS`, `kind_of`, `module`; statically calls `features_at`, `kind_of`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `WORDS`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `mark`, `module`, `moves_the_value`; statically calls `kind_of`, `mark`, `moves_the_value`, `record`, `shifted`, `with_values`
- [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] — imports `KINDS`, `STOP`, `kind_of`; statically calls `kind_of`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `adf_update`, `gaussian_sigmoid_mean`, `sigmoid`; calls `adf_update`, `gaussian_sigmoid_mean`, `sigmoid`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; calls `learner_preference_rows`, `preferences_present`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`; calls `_centre_for`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `Contrast`, `calibration_summary`, `residual_weight`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `Bounded`, `observed_returns`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `_with_traces`, `logged`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`, `preferences_inform_router_on`; calls `attempt_time_sql`, `preferences_inform_router_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih3_phone_host.py](../../../../../../tests/test_ih3_phone_host.py) — direct import
  - `test_last_miss_reads_the_latest_graded_answer`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_decision_of_one_kind_has_nothing_to_test`
  - `test_a_failed_sensor_leaves_the_numeric_policy_as_it_was`
  - `test_a_planted_w_pref_moves_the_argmax_and_leaves_the_tails_values`
  - `test_a_real_choice_freezes_its_inputs_and_the_next_decision_reads_it`
  - `test_a_real_effect_in_the_randomized_draws_moves_it_and_the_null_much_less`
  - `test_a_row_written_with_the_switch_off_froze_nothing_and_is_not_read`
  - `test_an_agreement_and_a_preference_with_no_draw_each_count_as_a_choice`
  - `test_missing_terms_are_read_at_the_fill_least_favourable_to_it`
  - `test_no_contrast_is_exactly_zero`
  - `test_no_module_of_this_stage_branches_on_a_score_or_a_stuck_flag`
  - `test_one_draw_moves_nothing_where_a_fit_through_it_would`
  - `test_picks_are_never_in_its_cohort_and_an_overridden_draw_is`
  - `test_staged_reads_nothing`
  - `test_the_kind_chosen_rises_and_nothing_reads_a_decision_where_the_link_was_not_used`
  - `test_the_kinds_are_the_plans_own_names`
  - `test_the_replay_reads_only_what_was_known_at_the_moment`
  - `test_the_sensor_is_frozen_in_the_trace_and_w_pref_starts_at_zero`
  - `test_v_pref_is_on_the_tails_scale_and_zero_with_no_spread`
  - `test_with_nothing_on_record_every_kind_is_equal`

## Modification guidance

- Make changes here when the responsibility remains preferences within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/preferences.py](../../../../../../src/learnloop/router_objective/preferences.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
