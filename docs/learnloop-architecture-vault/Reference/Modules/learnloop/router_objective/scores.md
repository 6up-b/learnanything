---
title: "learnloop.router_objective.scores"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/scores.py"
source_paths:
  - "src/learnloop/router_objective/scores.py"
source_commit: "e133e961a7f9f88dd3c1d1c2b3d220ff03af0ec4"
source_commit_timestamp: "2026-11-06T13:49:27-05:00"
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
| Source lines | 637 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e133e961a7f9f88dd3c1d1c2b3d220ff03af0ec4` |
| Commit timestamp | `2026-11-06T13:49:27-05:00` |

## Public API

- `class Detail` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 48) — One decision's score and how it was formed (the report's row).
- `class Bounded` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 62) — RO6's landing ruling R1: a window's return with its missing terms carried as missing.
- `class WindowSession` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 96) — One objective session's share of an evaluation window: its local date (its first activity's), the active minutes it had accumulated before the window opened (``carried``) and inside the window (``minutes``).
- `window_cost(connection: Any, *, start: str, end: str, gap_minutes: float, prices: Mapping[str, tuple[float, float]], own: tuple[float, float], lessons: bool=False) -> float` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 128) — ``C_i``: the attention cost the objective charges (§8.6) over ``(start, end]``, integrated from each session's minutes at the window's start, ``κ0·((m + d)² − m²)/(2m̄)``, at the ``(κ0, m̄)`` in force on the session's day (``own``, the decision's, on a day with no trace).
- `goal_date(due_at: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 142) — A goal's date as written (the date of its ``due_at`` in the offset it carries; ``goals/exam_seeding`` stamps an import on that date), or None.
- `dated_use_date(trace: Mapping[str, Any], row: Mapping[str, Any], dated: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 154) — The calendar date a frozen dated use is scored on (Codex review F6): the goal's own date, frozen in the trace with its ``due_at`` (the goal's sources, or the use's own ``due_at`` at RO5's tag), never one rebuilt from truncated elapsed days; failing both, the decision's moment pl…
- `exam_result_known(connection: Any, config: Any, lo: str, on: str, at: str, closure: C.Closure | None=None) -> float | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 208) — RO6: a dated use's ``Y`` as known at ``at``: the results imported for the goal's date that THE availability predicate (``router_objective_switches.attempt_time_sql``) admits by ``at``, their mean.
- `score_decision(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]], gap_minutes: float, closure: C.Closure | None=None, lessons: bool=False) -> Detail` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 228) — ``D̂_i`` for one decision whose window has closed, or why it carries none.
- `class Term` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 281) — One term of a window's realized return and its class (RO6's landing ruling R10).
  - `bounds(self) -> tuple[float, float]` (line 304; public) — R1: a missing term's range in the bounded return: performance in ``[0, 1]`` times its weight, less its baseline, inverse weighted as the observed term would have been (``1/r`` for a drawn check; a day with no draw also admits zero, the topic perhaps not drawn; unweighted where `…
- `classify_window(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], r_lookup: Callable[[str], dict[str, float]], exam_result: Callable[[Any, str, str], float | None] | None=None, support: Mapping[str, float] | None=None, drawn: Callable[[str], bool] | None=None) -> list[Term]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 317) — RO6's landing ruling R10: THE classification of every term of one decision's window, observed, a design zero, excluded at the draw (R7) or missing (:class:`Term`).
- `window_uses(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], exam_result: Callable[[Any, str, str], float | None] | None=None) -> tuple[list[W.Use], list[str]] | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 375) — RO5's reading of one decision's window (its scores, the cross-check): the frozen uses with what the randomized checks observed of them (and the completed assessments' keys), or None when a dated use in the window has no imported result (``no_result``).
- `observed_return(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, resolved: Mapping[tuple[str, str], C.Resolved], completion_rate: float | None, r_lookup: Callable[[str], dict[str, float]], prices: Mapping[str, tuple[float, float]], gap_minutes: float, exam_result: Callable[[Any, str, str], float | None] | None=None, complete: bool=False, support: Mapping[str, float] | None=None, drawn: Callable[[str], bool] | None=None, lessons: bool=False) -> tuple[float | None, str | None] | Bounded` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 420) — RO6 (§10): §8.7's bracket alone for one closed window, ``Σ_u v·(R/r)·(Y − m⁰) − (C − C⁰)``, with no action contrast: the observed return a randomized contrast multiplies (the stop coin's, or an importance ratio's).
- `class AsOf` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 492) — What one closed window's score reads, all as of one :class:`checks.Closure` (landing rulings R1, R11 of RO5; R4 of RO6): the resolved checks, the completion rate in its ``r``, each day's assignment probabilities and each day's price.
- `frozen_support(trace: Mapping[str, Any]) -> Mapping[str, float] | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 548) — R7: the check support a decision froze at its draw (``residual.measurable.support``), or None.
- `observed_returns(connection: Any, config: Any, *, at: str, rows: Sequence[Mapping[str, Any]], complete: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 557) — RO6: :func:`observed_return` for each of ``rows`` (a trace's columns with its parsed ``trace``) whose window closed before ``at``, keyed by decision id.
- `scores(connection: Any, config: Any, *, at: str) -> list[Detail]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 604) — Every decision's score from the traces whose windows closed before ``at`` (no peeking), RO5's checks the observations.

### Module constants

- `VERSION` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 38)
- `ANSWERED` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 39)
- `_STAMP` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 40)
- `OBSERVED` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 267)
- `DESIGN_ZERO` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 268)
- `EXCLUDED_AT_DRAW` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 269)
- `MISSING` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 270)
- `RO6_NOT_DRAWN` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 273)
- `RO6_NO_DRAW_DAY` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 274)
- `RO6_UNSUPPORTED_AT_DRAW` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 275)
- `RO6_COMPLETED` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 276)
- `RO6_DATED_RESULT` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 277)
- `RO6_DATED_MISSING` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 487)
- `RO6_NO_CHECK_SUPPORT` ([src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py), line 488)

### Explicit exports

`__all__` declares:

- `AsOf`
- `Bounded`
- `DESIGN_ZERO`
- `Detail`
- `EXCLUDED_AT_DRAW`
- `MISSING`
- `OBSERVED`
- `RO6_DATED_MISSING`
- `RO6_NO_CHECK_SUPPORT`
- `RO6_NO_DRAW_DAY`
- `RO6_NOT_DRAWN`
- `RO6_UNSUPPORTED_AT_DRAW`
- `Term`
- `VERSION`
- `WindowSession`
- `classify_window`
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
- `_distribution(trace: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, float], str | None, float | None]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 80)
- `_sessions(connection: Any, *, start: str, end: str, gap_minutes: float, lessons: bool=False) -> list[WindowSession]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 105) — The window's sessions on the objective's own clock (Codex review F4): the activity the serving price reads (``price.activity_spans``: attempts and Reader visits), split into sessions by the serving clock's own construction (``price.session_components``, Codex re-review F4: a Rea…
- `_price_rows(connection: Any) -> list[tuple[Any, Any, Any, Any]]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 170) — Every price-source trace, ``(local_date, κ0, m̄, created_at)``, in the order the day's first one is read.
- `_day_prices(connection: Any, closure: C.Closure | None=None, rows: Sequence[tuple[Any, Any, Any, Any]] | None=None) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 178) — ``(κ0, m̄)`` in force each local date as of a window's ``closure``: the day's first trace's, every price-source trace admitted through :meth:`checks.Closure.admits` on its created time (landing ruling R11: a trace written after the window closed never prices it).
- `_exam_result(connection: Any, lo: str, on: str, closure: C.Closure | None=None) -> float | None` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 194) — A dated use's ``Y``: the imported results on the goal's date (``goals/exam_seeding``), their mean, each admitted by the window's closure on its occurrence and its received time (landing ruling R1: an import after the window closed is not seen, and the use is censored ``no_result…
- `_window_cost_and_baseline(connection: Any, row: Mapping[str, Any], trace: Mapping[str, Any], *, prices: Mapping[str, tuple[float, float]], gap_minutes: float, lessons: bool=False) -> tuple[float, float]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 406) — ``C_i`` over the decision's window and its frozen ``C⁰_i``.
- `_context(connection: Any, *, at: str | None=None) -> Callable[[str], AsOf]` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 506) — The as-of reader every closed window's score and return share: ``as_of(closes_at)`` is the window's :class:`AsOf`, through the closure at ``closes_at`` (no later than ``at``, the reading moment, when given), over one snapshot of the checks' events (:class:`checks.Ledger`) and of…
- `_lessons_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/router_objective/scores.py), line 595) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the objective's clock counts lessons' active minutes (its tag and switch: ``router_objective_switches.lesson_offers_on``); off, or below the tag, the predecessor's clock.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `scores`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `_lessons_on`, `scores`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; statically calls `goal_date`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `Bounded`, `_day_prices`, `_lessons_on`, `_price_rows`, `dated_use_date`, `exam_result_known`, `observed_returns`, `window_cost`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `Ledger`, `support_at`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `activity_spans`, `session_components`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `Scored`, `Use`, `carries_score`, `score`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`, `lesson_offers_on`; calls `attempt_time_sql`, `lesson_offers_on`

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
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r11_a_price_trace_appended_after_the_closure_never_moves_a_closed_score_or_the_weight`
  - `test_r1_f10_a_closed_score_never_moves_with_an_answer_after_its_closure`
  - `test_r1_one_function_reads_every_counted_event_as_of_its_closure`
- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f1_a_complete_return_leaves_an_unknown_dated_use_out_and_keeps_a_window_with_no_checkable_use`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f5_the_contrasts_return_reader_admits_an_import_only_once_known`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r10_one_function_classifies_every_term_of_a_window`

## Modification guidance

- Make changes here when the responsibility remains scores within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/scores.py](../../../../../../src/learnloop/router_objective/scores.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
