---
title: "learnloop.daily_plan.lesson_suggestion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/lesson_suggestion.py"
source_paths:
  - "src/learnloop/daily_plan/lesson_suggestion.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.lesson_suggestion` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Teacher TE1b: Today's lesson suggestion card (spec_teacher_v1 §15.1, §19).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py) |
| Source lines | 753 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `reason_words(entry: Mapping[str, Any] | LS.Candidate, *, as_of: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 84) — A candidate's reason in plain words.
- `class SuggestionError(ValueError)` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 100)
  - `__init__(self, code: str, message: str) -> None` (line 101; internal)
- `suggestions_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 106) — TE1b's suggestions are on: the successor's tag, its switch, the router and its log, and lessons.
- `offers_in_objective(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 120) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the objective serves the day's offers as plan blocks, so Today's open draws no card (``lesson_offer.offers_on``).
- `suggestions_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 129) — Today may draw a suggestion card at its open: TE1b's suggestions on (:func:`suggestions_enabled`), and, from TE3b's tag with its switch on, only where the objective does not serve the plan (§15.1a: TE1b exactly there).
- `missed_since(cold: Sequence[Mapping[str, Any]], last_lesson: str | None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 160) — The owner's decision 4 (Nov 9, spec_instruct_handoff_v1 §8): a cold check since the topic's last lesson ended (or ever, with none) that was not fully right; the latest one's ``created_at`` (for the words, :func:`reason_words`), None when there is none.
- `build_candidates(vault: Any, repository: Any, *, now_iso: str) -> tuple[list[LS.Candidate], dict[str, list[str]]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 210) — The ``instruct(lesson)`` candidates (without decline days) and why other LOs were left out.
- `card_view(connection: Any, decision: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 361) — The card a decision shows while it is unanswered; None when it showed none or was answered.
- `reservation_problem(vault: Any, repository: Any, view: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 429) — Why a pending card's reserved lesson can no longer open on the current vault, or None.
- `draw_inputs(config: Any, state: LS.AcceptanceState, context: LS.Context, scored: Sequence[LS.ScoredCandidate]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 504) — What the day's draw seed hashes with the day (``LS.seed_for``) and its row stores as ``snapshot_hash``: a byte that moves here at a fixed input draws a different card (``tests/test_identity_pins.py``).
- `today_suggestion(vault: Any, repository: Any, *, clock: Clock | None=None, session_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 518) — Today's suggestion card, drawing the day's decision on the first call; None when there is none.
- `respond(vault: Any, repository: Any, *, decision_id: str, response: str, candidate_ref: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 628) — Record the learner's one response to a shown card; a Start or an alternative names its lesson id.
- `offer_card_view(block: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 689) — Teacher TE3b: a plan block's offer card (the step's and the plan view's), from the card its decision drew: "Learn *X* now?

### Module constants

- `REASON_WORDS` ([src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 68)
- `WHY_LABEL` ([src/learnloop/daily_plan/lesson_suggestion.py](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 76)

### Explicit exports

`__all__` declares:

- `REASON_WORDS`
- `SuggestionError`
- `WHY_LABEL`
- `build_candidates`
- `missed_since`
- `reason_words`
- `card_view`
- `offer_card_view`
- `offers_in_objective`
- `reservation_problem`
- `respond`
- `suggestions_active`
- `suggestions_enabled`
- `today_suggestion`

## Internal implementation anchors

- `_local_day(at: str) -> datetime | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 79)
- `_goal_learning_objects(vault: Any) -> set[str]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 142)
- `_cold(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 155)
- `_predicted(vault: Any, repository: Any, learning_object_id: str, now_iso: str) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 173) — The mastery model's predicted unassisted success on the LO (its own prior while it has no evidence): the number the lesson brief shows (``teacher.brief.lo_prediction``; a test pins the two equal).
- `_band_positions(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 191) — Adaptive difficulty's prediction against the practice band per LO (``below_band``; codex review F6): AD's posterior, never the mastery model.
- `_shown(decision: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 287)
- `_model(connection: Any, *, with_offers: bool) -> tuple[LS.AcceptanceState, list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 291) — The daily draw's acceptance model, its decisions and responses.
- `_days(now: datetime, at: str | None) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 304)
- `_context(env: PlanEnv, decisions: Sequence[Mapping[str, Any]]) -> LS.Context` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 309)
- `_sweep_ignored(connection: Any, decisions: Sequence[Mapping[str, Any]], *, config: Any, today: str, now_iso: str) -> int` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 325) — Record each earlier day's shown card left unanswered as ``ignored`` (its day has ended).
- `_card_entry(entry: Mapping[str, Any], *, as_of: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 356)
- `_pending_from_earlier_day(connection: Any, decisions: Sequence[Mapping[str, Any]], *, today: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 394) — The newest earlier day's Start whose lesson never opened, as its card (codex re-review F2).
- `_protection_readable(vault: Any, repository: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 412) — The exam material can be checked: what a lesson's opening needs before its brief (``teacher.brief.protection_state`` is None otherwise and the opening refuses; read here without importing the teacher; a test pins the two equal).
- `_expire(connection: Any, view: Mapping[str, Any], problem: str, *, now_iso: str) -> None` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 445) — Let an unopenable reservation go: an ``expired`` row on its decision (nothing deleted).
- `_recovered(vault: Any, repository: Any, *, today: str, now_iso: str) -> tuple[bool, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 457) — Today's card before any draw: ``(True, card)`` when the day already has its decision or an earlier day's Start still waits to open (validated first; R2), else ``(False, None)`` (draw).
- `_target(vault: Any, scored: Sequence[LS.ScoredCandidate], seed: str) -> LS.Target` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 485) — The day's target, drawn the router's way (spec §15.1, codex re-review F5).
- `_release(connection: Any, decision: Mapping[str, Any], *, session_id: str | None, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 705) — Let a pending card's reservation go (the learner's "Not now" on it); idempotent.
- `_response_view(row: Mapping[str, Any], chosen: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_suggestion.py), line 728)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `offer_card_view`; statically calls `offer_card_view`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `offer_card_view`; statically calls `offer_card_view`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `card_view`, `module`; statically calls `build_candidates`, `card_view`, `reason_words`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `suggestions_enabled`; statically calls `suggestions_enabled`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `offer_card_view`; statically calls `offer_card_view`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `suggestions_enabled`; statically calls `suggestions_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `SuggestionError`, `respond`, `today_suggestion`; statically calls `respond`, `today_suggestion`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `band_positions`, `decision_state_fields`; calls `band_positions`, `decision_state_fields`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `subject_view_live`; calls `subject_view_live`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LESSON_SUGGESTIONS_VERSIONS`, `ROUTER_MIXTURE_VERSIONS`, `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `LESSON_PROBE_EXPOSED_SOURCE`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `latest_today`; calls `PlanEnv`, `latest_today`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `end_block`, `module`, `offers_on`; calls `end_block`, `never_on_screen`, `offers_on`, `release_never_shown`, `withdrawn`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `module`; calls `decision_row_material`, `record`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `ROUTER_LOG_VERSION`, `insert_router_decision`; calls `insert_router_decision`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `all_decisions`, `attempts_by_learning_object`, `attempts_classified_by`, `decision`, `decision_for_day`, `decisions`, `insert_response`, `last_lesson_ended_by_learning_object`, `last_lesson_opened_by_learning_object`, `lesson_exists`, `offer_decision`, `open_lesson_learning_objects`, `receipt_key`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `COLD_ATTEMPT_TYPES`, `predicted_success`; calls `predicted_success`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`; calls `Candidate`, `Context`, `canonical_hash`, `days_between`, `declines_by_learning_object`, `draw`, `lesson_ref`, `mixture_target`, `observations`, `replay`, `score`, `seed_for`, `tiebreak_target`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; calls `prepare`, `record`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `lesson_candidate_after_cold_miss_on`, `lesson_offers_on`; calls `lesson_candidate_after_cold_miss_on`, `lesson_offers_on`
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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/ih2_lessons_compete_helpers.py](../../../../../../tests/ih2_lessons_compete_helpers.py) — direct import
- [tests/te3b_offers_helpers.py](../../../../../../tests/te3b_offers_helpers.py) — direct import
- [tests/teacher_te1b_landing_r2_helpers.py](../../../../../../tests/teacher_te1b_landing_r2_helpers.py) — direct import
- [tests/teacher_te1b_suggestions_helpers.py](../../../../../../tests/teacher_te1b_suggestions_helpers.py) — direct import
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_followups_batch6_te1b_card.py](../../../../../../tests/test_followups_batch6_te1b_card.py) — direct import
  - `test_a_declined_suggestion_keeps_its_not_now_line`
  - `test_not_now_on_a_pending_card_is_its_own_line_after_the_start`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_probe_arriving_during_an_open_offer_gets_a_new_decision_holding_both`
  - `test_no_lesson_available_the_followup_decision_is_the_predecessors`
  - `test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes`
  - `test_not_now_leaves_a_ready_probe_available_to_the_next_decision`
  - `test_not_now_on_the_need_path_leaves_the_item_in_the_pool`
  - `test_not_now_with_the_ceiling_reached_the_followup_serves`
  - `test_taking_the_lesson_settles_the_followup_honestly`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
  - `test_the_need_paths_mid_block_decision_gains_the_lesson_arm`
- [tests/test_ih2_offer_ceiling_and_unseen.py](../../../../../../tests/test_ih2_offer_ceiling_and_unseen.py) — direct import
  - `test_an_offer_drawn_after_a_miss_and_never_rendered_is_no_decline`
  - `test_the_ceiling_still_binds_on_seen_offers_at_a_boundary_with_none_open`
  - `test_the_todays_card_sweep_agrees`
  - `test_what_counts_as_on_screen`
- [tests/test_ih2_one_open_offer.py](../../../../../../tests/test_ih2_one_open_offer.py) — direct import
  - `test_a_boundary_drawing_a_block_leaves_the_jobs_offer_first_and_its_own_block_next`
  - `test_a_need_decision_replacing_an_interrupting_offer_keeps_its_place_and_what_it_beat`
  - `test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer`
  - `test_an_unwritten_workflow_waits_on_the_offer_that_replaced_the_one_it_lost_to`
  - `test_at_most_one_open_offer_across_read_and_job_interleavings`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_learner_asked_lesson_reaches_p_accept_flagged_unprompted`
  - `test_an_answer_on_the_desktop_to_what_the_phone_asked_for_counts_once`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_a_topic_below_its_band_with_a_miss_keeps_below_band`
  - `test_an_old_miss_followed_by_right_answers_is_dated_as_old`
  - `test_off_or_below_the_tag_candidates_and_wording_are_the_predecessors`
  - `test_the_candidacy_condition_reads_no_score_magnitude_count_or_error_type`
  - `test_the_offer_block_and_the_llms_row_carry_the_dated_words`
  - `test_the_reason_reads_honestly`
  - `test_the_words_hold_for_every_grade_the_condition_admits`
  - `test_the_words_name_the_latest_miss_and_survive_the_record`
- [tests/test_instruct_handoff_ih1.py](../../../../../../tests/test_instruct_handoff_ih1.py) — direct import
  - `test_offer_shown_is_ignored_by_the_plan_and_changes_no_decision`
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_the_latest_miss_is_the_one_read_and_it_is_lesson_suggestions_own_miss`
- [tests/test_te3b_codex_review.py](../../../../../../tests/test_te3b_codex_review.py) — direct import
  - `test_f1_a_start_answered_before_the_plan_reads_again_keeps_the_lesson_and_the_probe_is_next`
  - `test_f1_an_answer_after_the_plan_took_the_offer_back_is_refused_and_the_probe_served`
  - `test_f2_switching_off_takes_back_a_prefetched_offer_and_its_card`
  - `test_f3_with_the_switch_off_the_daily_draw_never_learns_from_offer_responses`
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_a_drawn_offer_is_a_block_answered_on_its_own_decision`
  - `test_te1bs_daily_card_is_drawn_only_where_the_objective_does_not_serve`
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
  - `test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052`
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
