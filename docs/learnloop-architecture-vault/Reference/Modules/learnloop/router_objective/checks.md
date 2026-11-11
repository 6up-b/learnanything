---
title: "learnloop.router_objective.checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/checks.py"
source_paths:
  - "src/learnloop/router_objective/checks.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.checks` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 2: randomized cold checks, embedded by default.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py) |
| Source lines | 751 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `day_unit(local_date: str) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 90)
- `slot_unit(local_date: str, slot: int) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 94)
- `day_seed(local_date: str) -> str` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 98)
- `class Day` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 114)
  - `as_dict(self) -> dict[str, Any]` (line 125; public)
- `draw(local_date: str, mode: str, value: float, eligible: Mapping[str, Sequence[str]], topics: Iterable[str]) -> Day` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 132) — The pure draw: same date and eligible set, same draw; it reads no decision.
- `day_record(connection: Any, local_date: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 186)
- `draw_day(vault: Any, repository: Any, *, local_date: str, now_iso: str, topics: Mapping[str, float] | Any, eligible_items: Eligible, placeable: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 191) — The day's draw, once (idempotent: a drawn day returns its record).
- `administered(connection: Any) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 256) — Each administered slot's ``item_planned`` receipt (its block, item and frozen sensors), by assignment id.
- `class Placement` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 271)
- `place(vault: Any, repository: Any, *, local_date: str, session_id: str | None, pool: Sequence[Any], planned: Iterable[str], chooser_items: Sequence[Any], lane: str | None, eligible_items: Eligible) -> list[Placement]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 279) — The slots this boundary administers (before its decision): the day's undelivered checks, in the day's first session only.
- `class Resolved` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 355)
  - `assessment_key(self) -> str` (line 367; public) — One completed check counts once however many decisions' windows hold it (§8.9).
- `exclusion(connection: Any, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 422) — Why the check's answer carries no label as its grade stands NOW (Codex review F1), else None: the existing assessment rules, read as AD's slot reads them.
- `class Closure` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 458) — THE cutoff (landing ruling R1, Codex final verify F10).
  - `through(cls, local_date: str) -> 'Closure'` (line 478; public) — The end of ``local_date`` (local time): events before the next local midnight.
  - `at(cls, stamp: str) -> 'Closure'` (line 489; public) — ``stamp`` itself (a window's ``window_closes_at``): events at or before it.
  - `admits(self, occurred: Any, received: Any=None) -> bool` (line 498; public) — Whether an event that happened at ``occurred`` (and, for an answer, became known at ``received``, None where the two are one) is in the read: both at or before the closure.
- `class Ledger` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 529) — Every event a check's resolution counts, read once with its times, so many closures (one per scored window) read one snapshot; each read filters it through :meth:`Closure.admits` alone.
  - `__init__(self, connection: Any) -> None` (line 534; internal)
  - `_graded(self, attempt: Mapping[str, Any], assisted: bool) -> tuple[str | None, float | None]` (line 581; internal) — The answer's exclusion and label, as its grade stands NOW (Codex review F1; :class:`Closure`).
  - `sessions_by_day(self, closure: Closure) -> dict[str, list[str]]` (line 593; public)
  - `drawn_days(self, closure: Closure) -> list[dict[str, Any]]` (line 602; public)
  - `resolve(self, closure: Closure) -> list[Resolved]` (line 606; public) — Every slot assigned as of ``closure``, with its status (module docstring) as it stood then.
  - `completion(self, closure: Closure) -> dict[str, Any]` (line 655; public)
  - `r_for(self, local_date: str, closure: Closure) -> tuple[dict[str, float], str]` (line 685; public)
- `resolve(connection: Any, *, through: str | None=None, closure: Closure | None=None, ledger: Ledger | None=None) -> list[Resolved]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 695) — Every assigned slot as of its closure (``through`` a local date, its end; or ``closure``), with its status (module docstring), every event read through :meth:`Closure.admits` (landing ruling R1): an assignment, administration, skip, displacement or answer after the closure is no…
- `completion(connection: Any, *, through: str | None=None, closure: Closure | None=None, ledger: Ledger | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 705) — The running completion rate, pooled and never conditioned on an action: completed checks over the assigned ones plus the expected checks of every day with no session since the first draw (§8.7's completion gap).
- `r_for(connection: Any, *, local_date: str, closure: Closure | None=None, ledger: Ledger | None=None) -> tuple[dict[str, float], str]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 715) — ``r_L`` on ``local_date`` (the assignment probability alone): the day's record, or with no draw that day the last earlier one's (labelled: its eligible set stands for a day with no session), every draw as of ``closure`` (by default the end of ``local_date``).
- `support_at(connection: Any, at: str, *, days: Sequence[Mapping[str, Any]] | None=None) -> tuple[dict[str, float], str]` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 724) — RO6's landing ruling R7: each topic's check support for the days after ``at``, as known at ``at`` (a stop coin's draw): ``r_L`` of the latest day drawn as of ``Closure.at(at)``, every draw admitted through :meth:`Closure.admits` (RO1's availability predicate on its assignment ro…

### Module constants

- `LOG` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 60)
- `VERSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 62)
- `RESOLVER_VERSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 63)
- `ORIGIN` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 64)
- `DAY_PREFIX` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 65)
- `NEED_TRIGGER` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 66)
- `NEED_BLOCKED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 67)
- `NO_SESSION` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 69)
- `NO_PRACTICE_SLOT` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 70)
- `DISPLACED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 71)
- `SKIPPED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 72)
- `NOT_ANSWERED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 73)
- `DEVICE_DEFERRED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 77)
- `DEVICE_DEFERRED_EVENT` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 78)
- `OPEN` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 79)
- `COMPLETED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 80)
- `EXCLUDED_PREFIX` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 82)
- `EXCLUDED_TYPE` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 83)
- `EXCLUDED_UNASSESSED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 84)
- `EXCLUDED_QUARANTINED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 85)
- `EXCLUDED_UNGRADED` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 86)
- `EXCLUDED_LABEL` ([src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py), line 87)

### Explicit exports

`__all__` declares:

- `Closure`
- `DAY_PREFIX`
- `DEVICE_DEFERRED`
- `DISPLACED`
- `Day`
- `Ledger`
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
- `support_at`

## Internal implementation anchors

- `_raise_need(vault: Any, repository: Any, lo: str, now_iso: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 167) — A topic with no eligible item: one pending generation need through the existing path (deduplicated on the LO, intent and facets by ``upsert_intervention_need``).
- `_first_session_today(connection: Any, local_date: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 245)
- `_label(row: Mapping[str, Any], assisted: bool) -> float | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 373) — §6.2's label: AD's unassisted success (help of any kind makes it a non-success, as RO2's resolver reads it); None where AD excludes the attempt (no correctness): never read as a zero (Codex review F1).
- `_current_epoch_unassessed(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 386) — PF-c over the attempt's current grading epoch (``grading_epochs.current_epoch``), AD's own rule (``adaptive_difficulty.replay._current_grade_unassessed``): every criterion's latest live row in that epoch recorded unverified, so the grade measures nothing whatever it schedules as.
- `_quarantined(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 409) — The attempt's active grade interpretation (its newest observation's) is quarantined.
- `_local_date(stamp: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 447)
- `_closure(through: str | None, closure: Closure | None) -> Closure` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 515)
- `_moment(stamp: Any) -> datetime` ([source](../../../../../../src/learnloop/router_objective/checks.py), line 523)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `ORIGIN`, `module`; statically calls `append`, `day_record`, `draw_day`, `place`, `setdefault`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `administered`, `completion`, `resolve`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; statically calls `resolve`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; statically calls `Ledger`, `support_at`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `Ledger`, `administered`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `support_at`
- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `module`; statically calls `resolve`

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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ro5_checks_helpers.py](../../../../../../tests/ro5_checks_helpers.py) — direct import
- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_a_failed_check_draw_placement_and_lesson_builder_are_the_boundarys_children`
  - `test_the_days_check_block_writes_its_own_plan_block_record`
- [tests/test_mobile_v2_checks.py](../../../../../../tests/test_mobile_v2_checks.py) — direct import
  - `test_j6_a_check_the_phone_can_show_is_served_on_the_phone_as_an_ordinary_item`
  - `test_j6_an_unanswered_deferred_check_resolves_device_deferred_at_the_days_end`
  - `test_j6_the_check_waits_for_the_desktop_is_recorded_once_and_never_redrawn`
  - `test_j6_the_engine_and_the_resolver_name_one_event`
  - `test_j6_the_learner_may_skip_it_from_the_phone_as_from_the_desktops_skip_link`
- [tests/test_mobile_v2_rereview_fixes.py](../../../../../../tests/test_mobile_v2_rereview_fixes.py) — direct import
  - `test_f5_a_check_restored_from_its_checkpoint_the_next_day_stays_cold`
- [tests/test_mobile_v2_review_fixes.py](../../../../../../tests/test_mobile_v2_review_fixes.py) — direct import
  - `test_f5_the_open_randomized_check_is_named_cold_until_it_is_answered`
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
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r1_an_answer_received_after_the_closure_is_not_seen_at_it`
  - `test_r1_f10_a_closed_score_never_moves_with_an_answer_after_its_closure`
  - `test_r1_f10_a_later_skip_never_moves_a_past_completion_rate`
  - `test_r1_one_function_reads_every_counted_event_as_of_its_closure`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r10_one_function_classifies_every_term_of_a_window`
  - `test_r10_selectively_skipped_checks_never_move_w_hat`
  - `test_r10_the_ledger_gives_no_status_the_enumeration_misses`
  - `test_r7_a_served_decision_freezes_its_support_and_the_measurable_tail`
- [tests/test_teacher_te2log_report.py](../../../../../../tests/test_teacher_te2log_report.py) — direct import
  - `test_randomized_checks_are_scored_apart_with_their_r`

## Modification guidance

- Make changes here when the responsibility remains checks within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/checks.py](../../../../../../src/learnloop/router_objective/checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
