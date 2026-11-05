---
title: "learnloop.router_objective.tail_data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/tail_data.py"
source_paths:
  - "src/learnloop/router_objective/tail_data.py"
source_commit: "38b18de5c50643841eff57029fa2e8f6ef2cd89a"
source_commit_timestamp: "2026-11-05T17:36:03-05:00"
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
  - "learnloop.router_objective.tail_data module"
  - "src/learnloop/router_objective/tail_data.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.tail_data`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.tail_data` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO6 (spec_router_objective_v1 §10): the learned tail's data, read as of a moment.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py) |
| Source lines | 796 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38b18de5c50643841eff57029fa2e8f6ef2cd89a` |
| Commit timestamp | `2026-11-05T17:36:03-05:00` |

## Public API

- `generator_payload(*, algorithm_version: str, objective: Any, tail: Any, terminal: Any, horizon_days: Any, llm_schema: Any, seeds: Mapping[str, Any] | None, epsilon: Any, features: str | None=None, objective_definition: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 93) — ``features``: the features version the logger served with (None: this build's, :data:`LT.FEATURES_VERSION`).
- `objective_definition(goals: Mapping[str, Any] | None, horizon_days: Any, population: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 110) — RO6's landing rulings R2 and R11: what defines the objective a decision valued, as its trace froze it: the horizon; per active goal (``inputs_sources.goals``), its id, its date (``due_at``), its weights (the dated weight and the undated density) and its use weights (per LO), and…
- `objective_hash(goals: Mapping[str, Any] | None, horizon_days: Any, population: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 136) — The hash of :func:`objective_definition`.
- `trace_objective_hash(trace: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 143) — The objective a logged decision valued, from its trace: its frozen goals, horizon and population densities (``evaluation.uses.topics``).
- `served_features_version(trace: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 153) — The features version a decision's residual served with (Codex re-review F7): its record's, else its fit's (an earlier RO6 build's trace), else ``unversioned``; a decision with no applied residual never read features, so this build's version stands for it (its features are rebuil…
- `generator_key(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 165)
- `generator(trace: Mapping[str, Any], algorithm_version: str) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 170) — A logged decision's generator version (module docstring).
- `class Logged` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 186)
- `nearest_goal_days(trace: Mapping[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 255) — Days to the nearest active dated goal the decision valued (RO5's ``goal_dates``, else the window's uses).
- `rebuilt_features(trace: Mapping[str, Any], receipt: Mapping[str, Any] | None) -> dict[str, tuple[float, ...]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 265) — Each candidate's features from the trace's frozen belief numbers and RO0's decision-time snapshot.
- `snapshot_mastery(snapshot: Mapping[str, Any], los: Sequence[str]) -> list[tuple[float, float]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 285) — RO0 row 9's mastery numbers of ``los`` (logit mean, logit variance), those it holds.
- `use_moment(trace: Mapping[str, Any], created: datetime, use: Mapping[str, Any]) -> datetime` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 319) — The moment a frozen dated use falls at (Codex review of RO6, F2): the goal's ``due_at`` as the rollouts parse it (``clock.parse_utc``, the use's own or the goal's frozen in the trace), else the decision's moment plus the use's exact delay.
- `logged(connection: Any, config: Any, *, at: str) -> list[Logged]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 422) — Every ``plan_block`` trace known at ``at``, oldest first (module docstring).
- `class Steps` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 486)
- `transitions(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> Steps` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 493) — Every logged decision's step to the next one, with its reward (module docstring).
- `class Fits` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 617)
  - `for_serving(self, generator_now: str) -> tuple[LT.Fit | None, str]` (line 623; public) — The current version's own fit; with none of its transitions yet, the latest earlier version's ("version k+1 uses the result"); else none.
- `fits(connection: Any, config: Any, *, at: str, rows: Sequence[Logged] | None=None) -> Fits` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 635) — One fit per generator version from its own transitions as of ``at`` (frozen-logger evaluation).
- `contrasts(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> tuple[list[LT.Contrast], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 668) — Every stop-coin decision with a frozen residual whose window closed before ``at``: its realized contrast (the coin's, times the window's observed return) and its frozen predicted ones (tail and residual).
- `improvement_ratio(row: Logged) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 722) — The improvement step's probability of the served action over the logger's: the mix with the numeric policy's argmax taken on ``Q_tail + ρ`` (the frozen residual at full weight), under the same coin.
- `cross_check(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 742) — The partial-history weights' estimate of the improvement step, beside the fit (report only).
- `predicted_improvement(rows: Sequence[Logged]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 767) — The fit's own forecast of the same step: ``Σ_a (μ_new − μ)(a)·(Q_tail + ρ)(a)``, the mean over decisions with a frozen residual (a projection, labelled; on the cutoff's horizon, not the window's).
- `is_finite(value: Any) -> bool` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 786)

### Module constants

- `VERSION` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 62)
- `STOP` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 63)
- `NO_LATER_DECISION` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 65)
- `CHANGE_POINT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 66)
- `VALUE_MISSING` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 67)
- `PAST_CUTOFF` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 68)
- `REWARD_OPEN` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 69)
- `NO_RESULT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 70)
- `CUTOFF_UNMATCHED` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 71)
- `OBJECTIVE_CHANGED` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 72)
- `_SAME_CUTOFF_SECONDS` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 75)
- `_CACHE` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 79)
- `_CACHE_LIMIT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 80)
- `OBJECTIVE_DEFINITION_VERSION` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 107)

### Explicit exports

`__all__` declares:

- `CHANGE_POINT`
- `CUTOFF_UNMATCHED`
- `Fits`
- `Logged`
- `NO_LATER_DECISION`
- `NO_RESULT`
- `OBJECTIVE_CHANGED`
- `OBJECTIVE_DEFINITION_VERSION`
- `PAST_CUTOFF`
- `REWARD_OPEN`
- `Steps`
- `VALUE_MISSING`
- `VERSION`
- `contrasts`
- `cross_check`
- `fits`
- `generator`
- `generator_key`
- `generator_payload`
- `improvement_ratio`
- `logged`
- `nearest_goal_days`
- `objective_definition`
- `objective_hash`
- `predicted_improvement`
- `rebuilt_features`
- `trace_objective_hash`
- `transitions`
- `use_moment`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 83)
- `_round(value: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 87)
- `_topic_map(entry: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 229) — A candidate's topics as its trace froze them (its sensors: the value's ``Topic`` numbers), by LO.
- `_topics(entry: Mapping[str, Any]) -> tuple[LT.TopicNumbers, ...]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 243)
- `_candidate_topics(candidates: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 247)
- `_served(trace: Mapping[str, Any]) -> tuple[dict[str, float], str]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 292)
- `_receipt(connection: Any, decision_id: str, config: Any, at: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 301) — RO0's decision-time snapshot of one decision, if it was known at ``at`` (the availability predicate).
- `_logged(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], config: Any, at: str, receipts: bool) -> Logged` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 338)
- `_next_links(connection: Any, logged_ids: set[str]) -> tuple[dict[str, str | None], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 459) — §4 row 12's links: from each logged decision, the next logged decision along the ledger's next-decision chain (None: censored, no later one), and the return's censoring for the report.
- `_exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 477) — A dated use's ``Y``: the results imported for the goal's date, known by ``at`` (THE availability predicate; the one reader the contrasts' returns share, ``scores.exam_result_known``), and admitted through RO5's closure at ``at`` on its occurrence and received time (RO6's landing…
- `_frozen_residual(row: Logged) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 652)
- `_with_traces(connection: Any, rows: Sequence[Logged]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 659)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `generator_key`, `generator_payload`, `objective_hash`
- [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]] — imports `module`; statically calls `contrasts`, `cross_check`, `fits`, `logged`, `predicted_improvement`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `_parse`, `contrasts`, `fits`, `logged`, `snapshot_mastery`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `Ledger`, `administered`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `ActionView`, `CoinDraw`, `Ratio`, `TopicNumbers`, `Transition`, `WeightedRow`, `belief`, `coin_contrasts`, `fit`, `partial_history`, `predicted_contrast`, `vector`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `Bounded`, `_day_prices`, `_price_rows`, `dated_use_date`, `exam_result_known`, `observed_returns`, `window_cost`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `served_distribution`
- [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] — imports `module`; calls `_round`
- [[Reference/Modules/learnloop/router_objective/trajectory|learnloop.router_objective.trajectory]] — imports `module`; calls `rows`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `known_at`; calls `known_at`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `typing`, `zlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]], [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f1_the_contrasts_read_every_window_complete`
  - `test_f3_a_trimmed_value_alone_is_no_value_at_the_carried_cutoff`
  - `test_f3_the_backup_reads_the_values_and_features_at_the_carried_cutoff`
  - `test_f7_an_earlier_builds_thirteen_features_are_rebuilt`
  - `test_f7_the_served_features_version_is_part_of_the_generator`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f2_a_same_day_exam_after_the_decision_enters_its_reward`
  - `test_f2_a_same_day_exam_with_no_import_censors_the_transition`
  - `test_f2_the_use_moment_is_the_goals_due_at_else_the_exact_delay`
  - `test_f3_a_later_cutoff_with_no_value_at_the_earlier_one_is_censored`
  - `test_f3_a_shared_cutoff_needs_no_trim`
  - `test_f5_the_contrasts_return_reader_admits_an_import_only_once_known`
  - `test_f6_a_window_with_a_decision_of_unknown_ratio_is_censored`
  - `test_f6_a_windows_product_includes_a_decision_whose_own_window_is_open`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r11_a_retention_density_change_with_no_goal_censors_the_transition_objective_changed`
  - `test_r2_a_goal_added_between_two_decisions_censors_the_transition_objective_changed`
  - `test_r2_a_served_decision_logs_its_objective_under_the_generator_it_served`
  - `test_r3_the_no_model_branch_answers_within_the_first_pass_and_censors_the_carried_backup`
  - `test_r7_a_served_decision_freezes_its_support_and_the_measurable_tail`
- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_a_failed_residual_leaves_the_numeric_policy_as_the_predecessors`
  - `test_the_features_frozen_at_serve_equal_the_rebuild_from_the_trace_and_ro0s_receipt`
- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
  - `test_a_few_weeks_on_a_copy_shaped_synthetic_vault`
  - `test_a_row_received_after_the_moment_never_enters_a_feature`
  - `test_an_exam_imported_after_the_moment_is_no_reward_yet`
  - `test_refitting_on_a_later_version_does_not_change_version_ks_evaluation`
  - `test_the_transitions_carry_the_objectives_reward_with_named_censoring`

## Modification guidance

- Make changes here when the responsibility remains tail data within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
