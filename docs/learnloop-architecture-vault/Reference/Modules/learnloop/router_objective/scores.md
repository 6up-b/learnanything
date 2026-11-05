---
title: "learnloop.router_objective.scores"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/scores.py"
source_paths:
  - "src/learnloop/router_objective/scores.py"
source_commit: "workspace/uncommitted @ HEAD 7f0d6dab15ed0523d22d635b677243892431ba12"
source_commit_timestamp: "2026-11-05T12:54:13-05:00"
source_worktree_state: "modified"
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
  - "learnloop.router_objective.scores module"
  - "src/learnloop/router_objective/scores.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.scores`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.scores` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 2 into §8.7: each closed decision's comparison score ``D̂_i`` from the randomized checks, so ``w`` can move off its prior (RO4's weight posterior, :mod:`learnloop.router_objective.weight`, unchanged).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py) |
| Source lines | 361 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 7f0d6dab15ed0523d22d635b677243892431ba12` |
| Commit timestamp | `2026-11-05T12:54:13-05:00` |

## Public API

- `class Detail` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 48) — One decision's score and how it was formed (the report's row).
- `class WindowSession` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 77) — One objective session's share of an evaluation window: its local date (its first activity's), the active minutes it had accumulated before the window opened (``carried``) and inside the window (``minutes``).
- `window_cost(connection: Any, *, start: str, end: str, gap_minutes: float, prices: Mapping[str, tuple[float, float]], own: tuple[float, float]) -> float` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 107) — ``C_i``: the attention cost the objective charges (§8.6) over ``(start, end]``, integrated from each session's minutes at the window's start, ``κ0·((m + d)² − m²)/(2m̄)``, at the ``(κ0, m̄)`` in force on the session's day (``own``, the decision's, on a day with no trace).
- `goal_date(due_at: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 121) — A goal's date as written (the date of its ``due_at`` in the offset it carries; ``goals/exam_seeding`` stamps an import on that date), or None.
- `dated_use_date(trace: Mapping[str, Any], row: Mapping[str, Any], dated: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 133) — The calendar date a frozen dated use is scored on (Codex review F6): the goal's own date, frozen in the trace with its ``due_at`` (the goal's sources, or the use's own ``due_at`` at RO5's tag), never one rebuilt from truncated elapsed days; failing both, the decision's moment pl…
- `exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 169) — RO6: a dated use's ``Y`` as known at ``at``: the results imported for the goal's date that THE availability predicate (``router_objective_switches.attempt_time_sql``) admits by ``at``, their mean.
- `score_decision(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]], gap_minutes: float) -> Detail` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 182) — ``D̂_i`` for one decision whose window has closed, or why it carries none.
- `window_uses(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], exam_result: Callable[[Any, str, str], float | None] | None=None) -> tuple[list[W.Use], list[str]] | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 213) — The frozen uses of one decision's window with what the randomized checks observed of them (and the completed assessments' keys), or None when a dated use in the window has no imported result (``no_result``).
- `observed_return(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]], gap_minutes: float, exam_result: Callable[[Any, str, str], float | None] | None=None) -> tuple[float | None, str | None]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 268) — RO6 (§10): §8.7's bracket alone for one closed window, ``Σ_u v·(R/r)·(Y − m⁰) − (C − C⁰)``, with no action contrast: the observed return a randomized contrast multiplies (the stop coin's, or an importance ratio's).
- `observed_returns(connection: Any, config: Any, *, at: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, tuple[float | None, str | None]]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 316) — RO6: :func:`observed_return` for each of ``rows`` (a trace's columns with its parsed ``trace``) whose window closed before ``at``, keyed by decision id, as of ``at`` as :func:`scores` reads it, except that an imported result counts only once THE availability predicate admits it…
- `scores(connection: Any, config: Any, *, at: str) -> list[Detail]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 337) — Every decision's score from the traces whose windows closed before ``at`` (no peeking), RO5's checks the observations.

### Module constants

- `VERSION` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 38)
- `ANSWERED` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 39)
- `_STAMP` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 40)

### Explicit exports

`__all__` declares:

- `Detail`
- `VERSION`
- `WindowSession`
- `dated_use_date`
- `exam_result_known`
- `goal_date`
- `observed_return`
- `observed_returns`
- `score_decision`
- `scores`
- `window_cost`
- `window_uses`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 43)
- `_distribution(trace: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, float], str | None, float | None]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 61)
- `_sessions(connection: Any, *, start: str, end: str, gap_minutes: float) -> list[WindowSession]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 86) — The window's sessions on the objective's own clock (Codex review F4): the activity the serving price reads (``price.activity_spans``: attempts and Reader visits), split into sessions by the serving clock's own construction (``price.session_components``, Codex re-review F4: a Rea…
- `_day_prices(connection: Any) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 149) — ``(κ0, m̄)`` in force each local date: the day's first trace's.
- `_exam_result(connection: Any, lo: str, on: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 160) — A dated use's ``Y``: the imported results on the goal's date (``goals/exam_seeding``), their mean.
- `_window_cost_and_baseline(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, prices: Mapping[str, tuple[float, float]], gap_minutes: float) -> tuple[float, float]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 255) — ``C_i`` over the decision's window and its frozen ``C⁰_i``.
- `_context(connection: Any, *, at: str) -> tuple[dict[tuple[str, str], C.Resolved], Callable[[str], float | None], Callable[[str], dict[str, float]], dict[str, tuple[float, float]]]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 289) — What every closed window's score reads as of ``at``: the resolved checks, the completion rate as it stood when a window closed, each day's assignment probabilities and each day's price.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `scores`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `scores`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; statically calls `goal_date`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `_day_prices`, `dated_use_date`, `exam_result_known`, `observed_returns`, `window_cost`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `completion`, `r_for`, `resolve`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `activity_spans`, `session_components`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `Scored`, `Use`, `carries_score`, `score`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]], [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_a_closed_window_scores_from_a_completed_check_with_r_from_the_assignment_and_completion`
  - `test_a_coin_forced_decision_a_fallback_and_agreement_carry_no_score`
  - `test_the_score_is_unbiased_for_a_planted_delta_on_a_synthetic_log`
- [tests/test_ro5_codex_rereview.py](../../../../../../tests/test_ro5_codex_rereview.py) — direct import
  - `test_f4_a_reader_interval_spanning_two_attempts_is_one_session_on_both_clocks`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_a_closed_scores_completion_rate_is_the_one_at_its_close`
  - `test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated`
  - `test_f6_a_fractional_delay_is_scored_on_the_goals_own_date`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f5_the_contrasts_return_reader_admits_an_import_only_once_known`

## Modification guidance

- Make changes here when the responsibility remains scores within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
