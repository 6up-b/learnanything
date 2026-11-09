---
title: "learnloop.daily_plan.learner_action"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/learner_action.py"
source_paths:
  - "src/learnloop/daily_plan/learner_action.py"
source_commit: "f837a8a7b4070a36aa3288598d59a614f603e47a"
source_commit_timestamp: "2026-11-09T11:20:01-05:00"
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
  - "learnloop.daily_plan.learner_action module"
  - "src/learnloop/daily_plan/learner_action.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.learner_action`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.learner_action` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): "Something else would help".

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py) |
| Source lines | 638 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f837a8a7b4070a36aa3288598d59a614f603e47a` |
| Commit timestamp | `2026-11-09T11:20:01-05:00` |

## Public API

- `class PreferenceError(ValueError)` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 62)
  - `__init__(self, code: str, message: str) -> None` (line 63; internal)
- `class Option` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 69)
  - `view(self) -> dict[str, Any]` (line 82; public)
- `class Options` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 88)
  - `offered(self) -> dict[str, Any]` (line 106; public) — What ``offered_json`` keeps: the options as refs with the router's probabilities where known.
  - `view(self) -> dict[str, Any]` (line 120; public)
- `enabled(env: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 125) — IH3's gate (``router_objective.learner_preferences`` at the tag), and the ledger exists.
- `options(env: Any) -> Options` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 268) — The boundary's options without drawing (module docstring).
- `class Chosen` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 327) — What :func:`choose` did: the preference's id, how it was served, and the step (None when nothing is served).
- `choose(env: Any, *, kind: str, ref: str | None, surface: str, attempt_id: str | None, note_md: str | None, preference_id: str | None=None) -> Chosen` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 390) — Serve the learner's choice and log it, in one transaction (module docstring).

### Module constants

- `LOG` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 46)
- `PREFERENCE_VERSION` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 48)
- `DESKTOP_SURFACES` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 51)
- `PHONE_SURFACES` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 52)
- `WAITS_ON_DESKTOP` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 55)
- `DESKTOP_OPENS_LESSON` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 57)
- `SERVING_STOP` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 58)
- `SERVING_BLOCK` ([src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py), line 59)

### Explicit exports

`__all__` declares:

- `Chosen`
- `DESKTOP_SURFACES`
- `KINDS`
- `Option`
- `Options`
- `PHONE_SURFACES`
- `PREFERENCE_VERSION`
- `PreferenceError`
- `WAITS_ON_DESKTOP`
- `WORDS`
- `choose`
- `enabled`
- `kind_of`
- `options`

## Internal implementation anchors

- `_waiting_block(record: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 139) — The drawn block the next step would serve and nothing of which has been served, or None.
- `_logged(connection: Any, decision_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 153)
- `_logged_probabilities(row: Mapping[str, Any] | None) -> dict[str, float]` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 162) — The probability each ref was given by the decision (only where it logged a number).
- `_lesson_candidate(env: Any, record: Any) -> BlockCandidate | None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 176) — The router's own best lesson candidate, read without a draw.
- `_label(kind: str, candidate: BlockCandidate | None) -> str` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 196)
- `_plans_pick_label(kind: str, block: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 207) — The plan's own drawn pick in plain words: a lesson offer by its topic, a reading by its section, else the kind's.
- `_frozen_inputs(env: Any, record: Any, lesson: BlockCandidate | None, *, drawn: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 223) — IH4 (spec_instruct_handoff_v1 §7): what this preference's replay reads, as it stood here: the choice model's features and, with a lesson on offer, the acceptance model's context and candidate.
- `_phone_serves(env: Any, kind: str, candidate: BlockCandidate | None, *, block: Any=None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 249) — A phone serves a practice block whose first item it can show, and a reading its own Reader shows (V4).
- `_decision_row(env: Any, *, decision_id: str, preference_id: str, chosen: Option, parent_id: str | None, offered: Mapping[str, Any], block_id: str | None, serving: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 343)
- `_state_receipt(env: Any, live: Options, chosen: Option) -> Any` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 449) — RO0 rows 9 and 13, as for any learner pick (:func:`~learnloop.daily_plan.engine._pick_new_block`): the state and the VOI verdict in force, read before the choice's transaction opens.
- `_write_decision(env: Any, connection: Any, *, live: Options, state: Any, **row_args: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 462) — The learner_pick decision and its receipts, or None when the router's log is off (``router.log_decisions``).
- `_log_only(env: Any, live: Options, preference: Any, preference_id: str, chosen: Option, parent_id: str | None, offered: Mapping[str, Any], serving: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 481)
- `_stop(env: Any, live: Options, preference: Any, preference_id: str, chosen: Option, parent_id: str | None, offered: Mapping[str, Any]) -> Chosen` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 491)
- `_end_offer(env: Any, connection: Any, live: Options, decision_id: str | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 505) — An unanswered lesson offer the choice replaces ends ``superseded`` (the plan's act, as IH2's), in the same transaction.
- `_place(env: Any, live: Options, preference: Any, preference_id: str, chosen: Option, parent_id: str | None, offered: Mapping[str, Any]) -> Chosen` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 518)
- `_serve_step(env: Any, record: Any, block: Any, context: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 553) — Serve the placed block's first step, as :func:`~learnloop.daily_plan.engine.learner_pick` serves its block.
- `_lesson_view(env: Any, ref: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 569) — The lesson a chosen "learn this" opens.
- `_serving_of(env: Any, decision_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 577) — How an override's decision says it was served, or None (no such decision: an agreement, or the log off).
- `_replayed(env: Any, row: Mapping[str, Any]) -> Chosen` ([source](../../../../../../src/learnloop/daily_plan/learner_action.py), line 588) — A retry of a preference already written: answered as it was made, so a lost reply loses nothing.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `module`; statically calls `choose`, `enabled`, `options`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; calls `_close`, `_decision_state`, `_device_detail`, `_done_step`, `_event`, `_feasibility`, `_item_step`, `_live_context`, `_persist_block`, `_reading_step`, `_reload`, `_serve`, `_standing_presentation`, `get_or_create_today`, `plan_active`, `reconcile`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `module`; calls `build`, `offers_on`, `supersede`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `offer_card_view`; calls `offer_card_view`
- [[Reference/Modules/learnloop/daily_plan/records|learnloop.daily_plan.records]] — imports `ORIGIN_LEARNER_PICK`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `LESSON_OFFER_PREFIX`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `module`; calls `insert_learner_preference`, `insert_router_decision`, `learner_preference`, `preferences_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `module`; calls `_dumps`, `_hash`, `_surface`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `KINDS`, `LESSON`, `NEW`, `QUESTION`, `READ`, `REVIEW`, `STOP`, `WORDS`, `kind_of`, `module`; calls `features_at`, `kind_of`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `learner_preferences_on`, `preferences_inform_router_on`; calls `learner_preferences_on`, `preferences_inform_router_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih3_learner_preferences.py](../../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_a_phone_surface_is_for_the_phone_only`
  - `test_a_retry_with_the_same_key_writes_nothing_again`
  - `test_an_override_changes_no_score_and_is_never_evidence`
  - `test_an_override_serves_the_action_logs_both_rows_and_the_parent_reads_overridden`
  - `test_an_unknown_choice_is_refused_and_writes_nothing`
  - `test_below_the_tag_the_switch_does_nothing`
  - `test_choosing_what_the_plan_had_drawn_serves_nothing_new`
  - `test_stop_ends_the_plan_as_the_learners_own_choice`
  - `test_the_desktop_opens_a_chosen_lesson`
  - `test_the_ledger_is_append_only_and_classified`
  - `test_the_options_are_the_plans_own_candidates_and_the_waiting_draw_is_the_parent`
  - `test_the_override_and_the_preference_are_one_transaction`
  - `test_the_phone_logs_a_lesson_pick_and_hands_it_to_the_desktop`
  - `test_with_no_draw_the_options_are_what_the_plan_can_produce_and_say_so`
  - `test_with_the_switch_off_there_is_no_link_and_nothing_is_written`
- [tests/test_ih3_phone_host.py](../../../../../../tests/test_ih3_phone_host.py) — direct import
  - `test_a_crash_after_the_commit_is_finished_by_the_retry`
  - `test_a_key_is_one_act_another_option_on_it_is_refused_and_writes_nothing`
  - `test_a_lesson_kept_at_a_finished_block_draws_nothing_through_its_reply`
  - `test_a_phone_choosing_the_drawn_lesson_is_told_it_waits_and_it_stays_an_agreement`
  - `test_a_reading_is_servable_where_the_phones_reader_shows_it`
  - `test_a_retried_lesson_pick_opens_the_lesson`
  - `test_a_retried_stop_says_stopped`
  - `test_a_retry_of_a_kept_lesson_still_says_it_waits`
  - `test_a_retry_owes_no_serve_once_the_plan_has_closed`
  - `test_an_override_keeps_the_state_a_pick_keeps`
  - `test_the_desktop_choosing_the_drawn_lesson_still_agrees`
  - `test_with_no_reader_a_reading_waits`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_failed_sensor_leaves_the_numeric_policy_as_it_was`
  - `test_a_learner_asked_lesson_reaches_p_accept_flagged_unprompted`
  - `test_a_note_on_a_protected_attempt_shows_nothing_and_says_why`
  - `test_a_planted_w_pref_moves_the_argmax_and_leaves_the_tails_values`
  - `test_a_preference_with_no_draw_is_counted_apart`
  - `test_a_real_choice_freezes_its_inputs_and_the_next_decision_reads_it`
  - `test_a_row_written_with_the_switch_off_froze_nothing_and_is_not_read`
  - `test_an_agreement_and_a_preference_with_no_draw_each_count_as_a_choice`
  - `test_at_w_pref_zero_only_the_acceptance_channel_moves_a_lesson_offers_value`
  - `test_choosing_the_offer_the_plan_drew_is_no_request`
  - `test_picks_are_never_in_its_cohort_and_an_overridden_draw_is`
  - `test_protection_unreadable_hides_every_note`
  - `test_staged_reads_nothing`
  - `test_the_budget_holds_oldest_first_and_says_what_it_left_out`
  - `test_the_card_carries_the_learners_own_statements`
  - `test_the_kind_chosen_rises_and_nothing_reads_a_decision_where_the_link_was_not_used`
  - `test_the_kinds_are_the_plans_own_names`
  - `test_the_llm_reads_the_card_and_the_trace_names_it`
  - `test_the_mid_block_request_carries_them_for_the_llm_alone`
  - `test_the_phone_surfaces_are_the_same_list_in_both_modules`
  - `test_the_read_is_bounded_by_the_card_questions_limit_and_says_so`
  - `test_the_replay_reads_only_what_was_known_at_the_moment`
  - `test_the_report_section_says_each_thing_and_labels_it_self_selected`
  - `test_the_sensor_is_frozen_in_the_trace_and_w_pref_starts_at_zero`
  - `test_the_staged_pick_inside_the_objective_is_the_same_with_preferences_on_record`
  - `test_w_itself_never_reads_a_preference_or_a_pick`
  - `test_w_pref_at_zero_changes_nothing_bit_for_bit_with_preferences_on_record`
  - `test_with_nothing_on_record_every_kind_is_equal`
  - `test_with_the_learned_tail_off_the_sensor_freezes_and_w_pref_is_not_fitted`
  - `test_with_the_switch_off_or_none_on_record_the_card_is_the_predecessors_bytes`
- [tests/test_ih6_workbench_open_item.py](../../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_options_read_draws_nothing_and_a_choice_is_still_served`
- [tests/test_ih_numeric_seed.py](../../../../../../tests/test_ih_numeric_seed.py) — direct import
  - `test_the_learners_options_and_override_draw_nothing`

## Modification guidance

- Make changes here when the responsibility remains learner action within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/learner_action.py](../../../../../../src/learnloop/daily_plan/learner_action.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
