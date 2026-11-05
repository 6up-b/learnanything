---
title: "learnloop.daily_plan.lesson_suggestion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/lesson_suggestion.py"
source_paths:
  - "src/learnloop/daily_plan/lesson_suggestion.py"
source_commit: "2079aa1eb02ced81c4ed4449672db9e2e437e45b"
source_commit_timestamp: "2026-11-04T16:51:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.lesson_suggestion module"
  - "src/learnloop/daily_plan/lesson_suggestion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.lesson_suggestion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.lesson_suggestion` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Teacher TE1b: Today's lesson suggestion card (spec_teacher_v1 §15.1, §19).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py) |
| Source lines | 592 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2079aa1eb02ced81c4ed4449672db9e2e437e45b` |
| Commit timestamp | `2026-11-04T16:51:26-05:00` |

## Public API

- `class SuggestionError(ValueError)` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 75)
  - `__init__(self, code: str, message: str) -> None` (line 76; internal)
- `suggestions_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 81) — Today may suggest a lesson: the successor's tag, its switch, the router and its log, and lessons.
- `build_candidates(vault: Any, repository: Any, *, now_iso: str) -> tuple[list[LS.Candidate], dict[str, list[str]]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 154) — The ``instruct(lesson)`` candidates (without decline days) and why other LOs were left out.
- `card_view(connection: Any, decision: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 262) — The card a decision shows while it is unanswered; None when it showed none or was answered.
- `reservation_problem(vault: Any, repository: Any, view: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 327) — Why a pending card's reserved lesson can no longer open on the current vault, or None.
- `today_suggestion(vault: Any, repository: Any, *, clock: Clock | None=None, session_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 401) — Today's suggestion card, drawing the day's decision on the first call; None when there is none.
- `respond(vault: Any, repository: Any, *, decision_id: str, response: str, candidate_ref: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 508) — Record the learner's one response to a shown card; a Start or an alternative names its lesson id.

### Module constants

- `REASON_WORDS` ([src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 67)
- `WHY_LABEL` ([src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 72)

### Explicit exports

`__all__` declares:

- `REASON_WORDS`
- `SuggestionError`
- `WHY_LABEL`
- `build_candidates`
- `card_view`
- `reservation_problem`
- `respond`
- `suggestions_active`
- `today_suggestion`

## Internal implementation anchors

- `_goal_learning_objects(vault: Any) -> set[str]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 99)
- `_cold(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 112)
- `_predicted(vault: Any, repository: Any, learning_object_id: str, now_iso: str) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 117) — The mastery model's predicted unassisted success on the LO (its own prior while it has no evidence): the number the lesson brief shows (``teacher.brief.lo_prediction``; a test pins the two equal).
- `_band_positions(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 135) — Adaptive difficulty's prediction against the practice band per LO (``below_band``; codex review F6): AD's posterior, never the mastery model.
- `_shown(decision: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 205)
- `_model(connection: Any) -> tuple[LS.AcceptanceState, list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 209)
- `_days(now: datetime, at: str | None) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 216)
- `_context(env: PlanEnv, decisions: Sequence[Mapping[str, Any]]) -> LS.Context` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 221)
- `_sweep_ignored(connection: Any, decisions: Sequence[Mapping[str, Any]], *, today: str, now_iso: str) -> int` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 237) — Record each earlier day's shown card left unanswered as ``ignored`` (its day has ended).
- `_card_entry(entry: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 257)
- `_pending_from_earlier_day(connection: Any, decisions: Sequence[Mapping[str, Any]], *, today: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 294) — The newest earlier day's Start whose lesson never opened, as its card (codex re-review F2).
- `_protection_readable(vault: Any, repository: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 310) — The exam material can be checked: what a lesson's opening needs before its brief (``teacher.brief.protection_state`` is None otherwise and the opening refuses; read here without importing the teacher; a test pins the two equal).
- `_expire(connection: Any, view: Mapping[str, Any], problem: str, *, now_iso: str) -> None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 343) — Let an unopenable reservation go: an ``expired`` row on its decision (nothing deleted).
- `_recovered(vault: Any, repository: Any, *, today: str, now_iso: str) -> tuple[bool, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 355) — Today's card before any draw: ``(True, card)`` when the day already has its decision or an earlier day's Start still waits to open (validated first; R2), else ``(False, None)`` (draw).
- `_target(vault: Any, scored: Sequence[LS.ScoredCandidate], seed: str) -> LS.Target` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 382) — The day's target, drawn the router's way (spec §15.1, codex re-review F5).
- `_release(connection: Any, decision: Mapping[str, Any], *, session_id: str | None, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 549) — Let a pending card's reservation go (the learner's "Not now" on it); idempotent.
- `_response_view(row: Mapping[str, Any], chosen: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 572)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `suggestions_active`; statically calls `suggestions_active`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `suggestions_active`; statically calls `suggestions_active`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `SuggestionError`, `respond`, `today_suggestion`; statically calls `respond`, `today_suggestion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `band_positions`, `decision_state_fields`; calls `band_positions`, `decision_state_fields`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `subject_view_live`; calls `subject_view_live`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LESSON_SUGGESTIONS_VERSIONS`, `ROUTER_MIXTURE_VERSIONS`, `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `latest_today`; calls `PlanEnv`, `latest_today`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `module`; calls `decision_row_material`, `record`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `ROUTER_LOG_VERSION`, `insert_router_decision`; calls `insert_router_decision`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `attempts_by_learning_object`, `decision`, `decision_for_day`, `decisions`, `insert_response`, `last_lesson_opened_by_learning_object`, `lesson_exists`, `open_lesson_learning_objects`, `receipt_key`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `COLD_ATTEMPT_TYPES`, `predicted_success`; calls `predicted_success`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`; calls `Candidate`, `Context`, `canonical_hash`, `days_between`, `declines_by_learning_object`, `draw`, `lesson_ref`, `mixture_target`, `observations`, `replay`, `score`, `seed_for`, `tiebreak_target`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; calls `prepare`, `record`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `module`; calls `epsilon_tiebreak`, `tied_set`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `CoverageError`, `read_protection`; calls `read_protection`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_followups_batch6_te1b_card.py](../../../../../../tests/test_followups_batch6_te1b_card.py) — direct import
  - `test_a_declined_suggestion_keeps_its_not_now_line`
  - `test_not_now_on_a_pending_card_is_its_own_line_after_the_start`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_a_reservation_is_set_aside_when_the_exam_material_cannot_be_checked`
  - `test_an_expired_reservation_cannot_then_be_released`
  - `test_not_now_on_a_pending_card_releases_the_reservation`
  - `test_release_needs_a_pending_lesson`
  - `test_the_protection_check_matches_the_lessons_opening`
- [tests/test_teacher_te1b_rereview_fixes.py](../../../../../../tests/test_teacher_te1b_rereview_fixes.py) — direct import
  - `test_a_reserved_lesson_is_dropped_once_teach_me_opened_one_on_it`
  - `test_a_start_left_unopened_overnight_is_offered_the_next_day`
  - `test_an_overnight_alternative_start_keeps_the_alternative`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_a_provider_failure_before_the_lesson_is_saved_leaves_an_idempotent_open`
  - `test_a_start_interrupted_before_its_lesson_opened_stays_on_the_card`
  - `test_an_accepted_alternatives_delayed_check_reaches_its_decision`
  - `test_an_alternative_start_interrupted_keeps_the_alternative`
  - `test_below_band_reads_adaptive_difficultys_posterior_not_the_mastery_model`
  - `test_the_learners_answers_are_preference_lines_on_the_router_card`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_a_closed_suggested_lessons_receipt_names_the_decision`
  - `test_every_response_is_logged_once`
  - `test_not_now_mutes_the_goal_per_the_recovery_prior`
  - `test_off_or_below_the_tag_nothing_is_drawn_or_written`
  - `test_responses_move_the_acceptance_model`
  - `test_the_candidate_reasons`
  - `test_the_card_comes_at_most_once_a_day`
  - `test_the_outcome_is_r_cold_on_the_drawn_lo_shown_or_not`
  - `test_the_shell_reads_lessons_and_room_to_learn_as_the_teacher_does`
  - `test_todays_plan_is_byte_identical_with_a_suggestion_drawn`

## Modification guidance

- Make changes here when the responsibility remains lesson suggestion within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
