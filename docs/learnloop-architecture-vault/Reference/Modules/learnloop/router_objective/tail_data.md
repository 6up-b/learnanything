---
title: "learnloop.router_objective.tail_data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/tail_data.py"
source_paths:
  - "src/learnloop/router_objective/tail_data.py"
source_commit: "6efe5dc164bfe4323dd908b334a1913998f5f4e3"
source_commit_timestamp: "2026-11-05T12:03:38-05:00"
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
| Source lines | 600 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6efe5dc164bfe4323dd908b334a1913998f5f4e3` |
| Commit timestamp | `2026-11-05T12:03:38-05:00` |

## Public API

- `generator_payload(*, algorithm_version: str, objective: Any, tail: Any, terminal: Any, horizon_days: Any, llm_schema: Any, seeds: Mapping[str, Any] | None, epsilon: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 76)
- `generator_key(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 85)
- `generator(trace: Mapping[str, Any], algorithm_version: str) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 90) — A logged decision's generator version (module docstring).
- `class Logged` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 105)
- `nearest_goal_days(trace: Mapping[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 160) — Days to the nearest active dated goal the decision valued (RO5's ``goal_dates``, else the window's uses).
- `rebuilt_features(trace: Mapping[str, Any], receipt: Mapping[str, Any] | None) -> dict[str, tuple[float, ...]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 170) — Each candidate's features from the trace's frozen belief numbers and RO0's decision-time snapshot.
- `snapshot_mastery(snapshot: Mapping[str, Any], los: Sequence[str]) -> list[tuple[float, float]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 189) — RO0 row 9's mastery numbers of ``los`` (logit mean, logit variance), those it holds.
- `logged(connection: Any, config: Any, *, at: str) -> list[Logged]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 278) — Every ``plan_block`` trace known at ``at``, oldest first (module docstring).
- `class Steps` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 346)
- `transitions(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> Steps` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 357) — Every logged decision's step to the next one, with its reward (module docstring).
- `class Fits` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 453)
  - `for_serving(self, generator_now: str) -> tuple[LT.Fit | None, str]` (line 459; public) — The current version's own fit; with none of its transitions yet, the latest earlier version's ("version k+1 uses the result"); else none.
- `fits(connection: Any, config: Any, *, at: str, rows: Sequence[Logged] | None=None) -> Fits` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 471) — One fit per generator version from its own transitions as of ``at`` (frozen-logger evaluation).
- `contrasts(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> tuple[list[LT.Contrast], dict[str, int]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 504) — Every stop-coin decision with a frozen residual whose window closed before ``at``: its realized contrast (the coin's, times the window's observed return) and its frozen predicted ones (tail and residual).
- `improvement_ratio(row: Logged) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 536) — The improvement step's probability of the served action over the logger's: the mix with the numeric policy's argmax taken on ``Q_tail + ρ`` (the frozen residual at full weight), under the same coin.
- `cross_check(connection: Any, config: Any, rows: Sequence[Logged], *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 556) — The partial-history weights' estimate of the improvement step, beside the fit (report only).
- `predicted_improvement(rows: Sequence[Logged]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 573) — The fit's own forecast of the same step: ``Σ_a (μ_new − μ)(a)·(Q_tail + ρ)(a)``, the mean over decisions with a frozen residual (a projection, labelled; on the cutoff's horizon, not the window's).
- `is_finite(value: Any) -> bool` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 592)

### Module constants

- `VERSION` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 50)
- `STOP` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 51)
- `NO_LATER_DECISION` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 53)
- `CHANGE_POINT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 54)
- `VALUE_MISSING` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 55)
- `PAST_CUTOFF` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 56)
- `REWARD_OPEN` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 57)
- `NO_RESULT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 58)
- `_CACHE` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 62)
- `_CACHE_LIMIT` ([src/learnloop/router_objective/tail_data.py](../../../../../../src/learnloop/router_objective/tail_data.py), line 63)

### Explicit exports

`__all__` declares:

- `CHANGE_POINT`
- `Fits`
- `Logged`
- `NO_LATER_DECISION`
- `NO_RESULT`
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
- `predicted_improvement`
- `rebuilt_features`
- `transitions`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 66)
- `_round(value: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 70)
- `_topic_map(entry: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 134) — A candidate's topics as its trace froze them (its sensors: the value's ``Topic`` numbers), by LO.
- `_topics(entry: Mapping[str, Any]) -> tuple[LT.TopicNumbers, ...]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 148)
- `_candidate_topics(candidates: Mapping[str, Any]) -> dict[str, LT.TopicNumbers]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 152)
- `_served(trace: Mapping[str, Any]) -> tuple[dict[str, float], str]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 196)
- `_receipt(connection: Any, decision_id: str, config: Any, at: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 205) — RO0's decision-time snapshot of one decision, if it was known at ``at`` (the availability predicate).
- `_logged(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], config: Any, at: str, receipts: bool) -> Logged` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 223)
- `_next_links(connection: Any, logged_ids: set[str]) -> tuple[dict[str, str | None], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 315) — §4 row 12's links: from each logged decision, the next logged decision along the ledger's next-decision chain (None: censored, no later one), and the return's censoring for the report.
- `_exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 333) — A dated use's ``Y``: the results imported for the goal's date, known by ``at`` (THE availability predicate).
- `_local(stamp: str) -> str` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 353)
- `_frozen_residual(row: Logged) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 488)
- `_with_traces(connection: Any, rows: Sequence[Logged]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/tail_data.py), line 495)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `generator_key`, `generator_payload`
- [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]] — imports `module`; statically calls `contrasts`, `cross_check`, `fits`, `logged`, `predicted_improvement`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `contrasts`, `fits`, `logged`, `snapshot_mastery`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `administered`, `completion`, `resolve`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`; calls `ActionView`, `Contrast`, `TopicNumbers`, `Transition`, `WeightedRow`, `belief`, `coin_contrast`, `fit`, `partial_history`, `predicted_contrast`, `vector`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `_day_prices`, `dated_use_date`, `observed_returns`, `window_cost`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `served_distribution`
- [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] — imports `module`; calls `_round`
- [[Reference/Modules/learnloop/router_objective/trajectory|learnloop.router_objective.trajectory]] — imports `module`; calls `rows`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`, `known_at`; calls `attempt_time_sql`, `known_at`

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

- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_a_failed_residual_leaves_the_numeric_policy_as_the_predecessors`
  - `test_the_features_frozen_at_serve_equal_the_rebuild_from_the_trace_and_ro0s_receipt`
- [tests/test_ro6_tail_data.py](../../../../../../tests/test_ro6_tail_data.py) — direct import
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
