---
title: "learnloop.router_objective.price"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/price.py"
source_paths:
  - "src/learnloop/router_objective/price.py"
source_commit: "02ca6dafaccff31b2c68eff85db35ae8f38c69b5"
source_commit_timestamp: "2026-11-06T16:30:06-05:00"
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
  - "learnloop.router_objective.price module"
  - "src/learnloop/router_objective/price.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.price`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.price` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.6: the attention price ``κ(x) = κ0·x/m̄`` on session minutes, its daily seed, guard and posterior.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py) |
| Source lines | 264 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `02ca6dafaccff31b2c68eff85db35ae8f38c69b5` |
| Commit timestamp | `2026-11-06T16:30:06-05:00` |

## Public API

- `lesson_spans(connection: Any, *, since: str, until: str, received_by: str | None=None) -> list[tuple[datetime, datetime, float]]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 55) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): one span per lesson from TE2-log's ``lesson_activity_intervals`` whose intervals finished in ``[since, until]``: from its first interval's start to its last interval's end, with the union of its foreground intervals as its active seco…
- `activity_spans(connection: Any, *, since: str, until: str, lessons: bool=False, received_by: str | None=None) -> list[tuple[datetime, datetime, float]]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 95) — The objective's activity clock: ``(began, finished, active seconds)`` for each attempt (at its completion, with its latency) and each Reader visit (over its interval, its active seconds), finished in ``[since, until]``.
- `session_components(spans: Sequence[tuple[datetime, datetime, float]], *, gap_minutes: float) -> list[list[int]]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 129) — The objective's sessions over ``spans``: the connected components of activity, two spans in one session when less than ``gap_minutes`` lie between them (a Reader interval spanning two attempts joins them).
- `session_active_minutes(connection: Any, *, now: str, gap_minutes: float, lessons: bool=False) -> tuple[float, str | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 150) — The active minutes of the current objective session: activity (attempts at their completion with their latency, Reader visits over their interval) in the session holding ``now`` (:func:`session_components`: less than ``gap_minutes`` from its last activity).
- `guard_minutes(config: Any, remembered: float) -> float` ([source](../../../../../../src/learnloop/router_objective/price.py), line 185)
- `class Seeded` ([source](../../../../../../src/learnloop/router_objective/price.py), line 192)
  - `as_dict(self) -> dict[str, Any]` (line 202; public)
- `seed_from_gain(gain: Mapping[float, float], *, remembered: float, block_minutes: float, last_positive: float | None) -> tuple[float, str]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 214) — ``κ0`` from the day's gain curve: the marginal gain per minute at ``m̄``, floored at the last positive value; with none ever and no positive marginal, the tail's average marginal gain per minute.
- `choice_log_likelihood(kappa0: float, observations: Iterable[Mapping[str, float]]) -> float` ([source](../../../../../../src/learnloop/router_objective/price.py), line 230) — The stated likelihood: ``P(continue) = σ(gain − price)`` per frontier choice, the price at that choice's session minutes (``κ0·x/m̄`` over the block); a stop says only that the forecast gain was below the price.
- `grid_posterior(seed: float, observations: Sequence[Mapping[str, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 244) — The grid posterior over ``κ0``: a log-uniform grid around the seed, prior uniform on it.

### Module constants

- `PRICE_VERSION` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 32)
- `SEED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 33)
- `DAY_SEED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 35)
- `CARRIED_DAY` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 36)
- `CARRIED_LAST` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 37)
- `TAIL_AVERAGE` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 38)
- `FLOORED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 39)
- `GUARD_MULTIPLE` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 41)
- `GRID_MULTIPLES` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 43)
- `_STAMP` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 44)
- `LOOKBACK_DAYS` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 52)

### Explicit exports

`__all__` declares:

- `CARRIED_DAY`
- `CARRIED_LAST`
- `DAY_SEED`
- `FLOORED`
- `GRID_MULTIPLES`
- `GUARD_MULTIPLE`
- `PRICE_VERSION`
- `SEED`
- `Seeded`
- `TAIL_AVERAGE`
- `choice_log_likelihood`
- `grid_posterior`
- `guard_minutes`
- `seed_from_gain`
- `activity_spans`
- `lesson_spans`
- `session_active_minutes`
- `session_components`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/price.py), line 47)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `Seeded`, `guard_minutes`, `seed_from_gain`, `session_active_minutes`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `session_active_minutes`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; statically calls `activity_spans`, `session_components`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; statically calls `session_active_minutes`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]], [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]], [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
  - `test_f8_a_phone_visits_active_time_reaches_the_routers_activity_readers`
- [tests/test_ro4_price.py](../../../../../../tests/test_ro4_price.py) — direct import
  - `test_a_session_ends_after_a_gap_of_session_gap_minutes`
  - `test_the_grid_posterior_is_its_prior_with_nothing_fed_and_learns_from_choices`
  - `test_the_runaway_guard_is_three_remembered_minutes_unless_set`
  - `test_the_seed_is_the_days_marginal_gain_floored_at_the_last_positive_value`
- [tests/test_ro5_codex_rereview.py](../../../../../../tests/test_ro5_codex_rereview.py) — direct import
  - `test_f4_a_reader_interval_spanning_two_attempts_is_one_session_on_both_clocks`
  - `test_f4_the_shared_construction_serves_ro4s_session_minutes_exactly`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_the_probe_after_the_fix_pins_its_numbers_and_the_seed`
- [tests/test_te3b_binding.py](../../../../../../tests/test_te3b_binding.py) — direct import
- [tests/test_te3b_clock.py](../../../../../../tests/test_te3b_clock.py) — direct import
  - `test_kappa_counts_a_lessons_active_minutes_only_with_lessons_on`
  - `test_the_serving_clock_reads_only_lesson_intervals_received_by_now`
- [tests/test_te3b_features.py](../../../../../../tests/test_te3b_features.py) — direct import
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains price within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
