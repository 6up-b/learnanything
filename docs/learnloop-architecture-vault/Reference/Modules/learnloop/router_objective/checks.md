---
title: "learnloop.router_objective.checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/checks.py"
source_paths:
  - "src/learnloop/router_objective/checks.py"
source_commit: "054b8a0652045fad6cf66e7b53909f395070095d"
source_commit_timestamp: "2026-11-05T10:30:41-05:00"
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
  - "learnloop.router_objective.checks module"
  - "src/learnloop/router_objective/checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.checks` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 2: randomized cold checks, embedded by default.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py) |
| Source lines | 573 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `054b8a0652045fad6cf66e7b53909f395070095d` |
| Commit timestamp | `2026-11-05T10:30:41-05:00` |

## Public API

- `day_unit(local_date: str) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 82)
- `slot_unit(local_date: str, slot: int) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 86)
- `day_seed(local_date: str) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 90)
- `class Day` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 106)
  - `as_dict(self) -> dict[str, Any]` (line 117; public)
- `draw(local_date: str, mode: str, value: float, eligible: Mapping[str, Sequence[str]], topics: Iterable[str]) -> Day` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 124) — The pure draw: same date and eligible set, same draw; it reads no decision.
- `day_record(connection: Any, local_date: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 178)
- `draw_day(vault: Any, repository: Any, *, local_date: str, now_iso: str, topics: Mapping[str, float] | Any, eligible_items: Eligible, placeable: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 183) — The day's draw, once (idempotent: a drawn day returns its record).
- `administered(connection: Any) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 248) — Each administered slot's ``item_planned`` receipt (its block, item and frozen sensors), by assignment id.
- `class Placement` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 263)
- `place(vault: Any, repository: Any, *, local_date: str, session_id: str | None, pool: Sequence[Any], planned: Iterable[str], chooser_items: Sequence[Any], lane: str | None, eligible_items: Eligible) -> list[Placement]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 271) — The slots this boundary administers (before its decision): the day's undelivered checks, in the day's first session only.
- `class Resolved` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 347)
  - `assessment_key(self) -> str` (line 359; public) — One completed check counts once however many decisions' windows hold it (§8.9).
- `exclusion(connection: Any, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 425) — Why the check's answer carries no label as its grade stands NOW (Codex review F1), else None: the existing assessment rules, read as AD's slot reads them.
- `resolve(connection: Any, *, through: str) -> list[Resolved]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 457) — Every assigned slot through ``through`` (a local date), with its status (module docstring), as it stood at the end of that date (Codex re-review F10): an administration or an answer on a later date is not seen, so a historical read never moves with later activity (a grade's late…
- `completion(connection: Any, *, through: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 519) — The running completion rate, pooled and never conditioned on an action: completed checks over the assigned ones plus the expected checks of every day with no session since the first draw (§8.7's completion gap).
- `r_for(connection: Any, *, local_date: str) -> tuple[dict[str, float], str]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 554) — ``r_L`` on ``local_date`` (the assignment probability alone): the day's record, or with no draw that day the last earlier one's (labelled: its eligible set stands for a day with no session).

### Module constants

- `LOG` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 57)
- `VERSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 59)
- `RESOLVER_VERSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 60)
- `ORIGIN` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 61)
- `DAY_PREFIX` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 62)
- `NEED_TRIGGER` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 63)
- `NEED_BLOCKED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 64)
- `NO_SESSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 66)
- `NO_PRACTICE_SLOT` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 67)
- `DISPLACED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 68)
- `SKIPPED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 69)
- `NOT_ANSWERED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 70)
- `OPEN` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 71)
- `COMPLETED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 72)
- `EXCLUDED_PREFIX` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 74)
- `EXCLUDED_TYPE` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 75)
- `EXCLUDED_UNASSESSED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 76)
- `EXCLUDED_QUARANTINED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 77)
- `EXCLUDED_UNGRADED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 78)
- `EXCLUDED_LABEL` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 79)

### Explicit exports

`__all__` declares:

- `DAY_PREFIX`
- `DISPLACED`
- `Day`
- `NOT_ANSWERED`
- `NO_PRACTICE_SLOT`
- `NO_SESSION`
- `OPEN`
- `ORIGIN`
- `Placement`
- `RESOLVER_VERSION`
- `Resolved`
- `SKIPPED`
- `VERSION`
- `administered`
- `completion`
- `day_record`
- `day_seed`
- `day_unit`
- `draw`
- `draw_day`
- `place`
- `r_for`
- `resolve`
- `slot_unit`

## Internal implementation anchors

- `_raise_need(vault: Any, repository: Any, lo: str, now_iso: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 159) — A topic with no eligible item: one pending generation need through the existing path (deduplicated on the LO, intent and facets by ``upsert_intervention_need``).
- `_first_session_today(connection: Any, local_date: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 237)
- `_sessions_by_day(connection: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 365)
- `_label(row: Mapping[str, Any], assisted: bool) -> float | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 376) — §6.2's label: AD's unassisted success (help of any kind makes it a non-success, as RO2's resolver reads it); None where AD excludes the attempt (no correctness): never read as a zero (Codex review F1).
- `_current_epoch_unassessed(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 389) — PF-c over the attempt's current grading epoch (``grading_epochs.current_epoch``), AD's own rule (``adaptive_difficulty.replay._current_grade_unassessed``): every criterion's latest live row in that epoch recorded unverified, so the grade measures nothing whatever it schedules as.
- `_quarantined(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 412) — The attempt's active grade interpretation (its newest observation's) is quarantined.
- `_local_date(stamp: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 450)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `ORIGIN`, `module`; statically calls `append`, `draw_day`, `place`, `setdefault`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `administered`, `completion`, `resolve`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; statically calls `completion`, `r_for`, `resolve`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `administered`, `completion`, `resolve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `AttemptFacts`, `category`, `unassisted_success`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`; calls `current_epoch`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`, `unverified_evidence_row`; calls `unverified_evidence_row`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `uniform`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `by_unit`, `insert`, `present`, `rows`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `CHECKS_EMBEDDED`, `CHECKS_OFF`, `check_mode`; calls `check_mode`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]], [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_alpha_is_labelled_provisional_and_a_check_is_never_the_blocks_action`
  - `test_the_combiner_is_fitted_on_resolved_checks_and_is_its_prior_with_none`
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_a_closed_window_scores_from_a_completed_check_with_r_from_the_assignment_and_completion`
  - `test_a_topic_with_no_eligible_item_has_r_zero_and_raises_a_generation_need`
  - `test_completion_is_scored_by_the_label_and_help_makes_it_a_non_success`
  - `test_off_draws_nothing_and_a_day_with_no_session_counts_toward_the_completion_gap`
  - `test_the_check_takes_the_first_practice_slot_outside_the_mix_with_no_label`
  - `test_the_draw_does_not_change_with_the_action_or_either_policys_output`
  - `test_the_draw_is_uniform_over_topics_across_dates`
  - `test_the_same_date_and_eligible_set_draw_the_same_and_r_is_exact`
  - `test_the_score_is_unbiased_for_a_planted_delta_on_a_synthetic_log`
- [tests/test_ro5_codex_rereview.py](../../../../../../tests/test_ro5_codex_rereview.py) — direct import
  - `test_f10_a_past_completion_rate_never_moves_with_a_later_assignment`
  - `test_f10_an_answer_after_the_cutoff_is_not_a_completion_as_of_it`
  - `test_f2_the_draw_is_over_what_the_days_plan_can_serve_and_a_topic_outside_it_raises_no_need`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_a_closed_scores_completion_rate_is_the_one_at_its_close`
  - `test_f1_a_current_epoch_that_assesses_nothing_is_no_observation`
  - `test_f1_a_held_grade_is_no_check_observation_and_no_completion`
  - `test_f1_a_missing_label_is_excluded_never_a_zero`
  - `test_f2_the_check_is_administered_whatever_the_policy_chose`

## Modification guidance

- Make changes here when the responsibility remains checks within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
