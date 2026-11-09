---
title: "learnloop.followup_serve.identity"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/identity.py"
source_paths:
  - "src/learnloop/followup_serve/identity.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_serve"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_serve.identity module"
  - "src/learnloop/followup_serve/identity.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.identity`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.identity` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: The one durable single-use identity of a generated probe (spec §4.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py) |
| Source lines | 324 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `item_revision(payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 47) — The content revision a claim is keyed to: the question as authored.
- `register(repository: Repository, *, practice_item_id: str, revision: str, source: str, workflow_id: str | None=None, probe_episode_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 61) — Give an item the identity, once, committed before its file exists (no crash publishes a question without it).
- `is_generated_probe(repository: Repository, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 81)
- `generated_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 88)
- `closed_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 93) — Every generated probe with a burn or a retirement.
- `retired_probe_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 100)
- `class Claim` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 111) — A first-serve claim's verdict.
- `claim_serve(repository: Repository, practice_item_id: str, *, surface: str, presentation_id: str | None, workflow_id: str | None=None, reason: str='first_serve', clock: Clock | None=None) -> Claim` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 121) — The atomic first-serve burn; an item with no identity needs no claim.
- `retire(repository: Repository, practice_item_id: str, *, reason: str, workflow_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 170) — Close a generated probe for any further administration, and keep it for history.
- `withdraw(repository: Repository, practice_item_id: str, *, reason: str, workflow_id: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 198) — Everything that could still serve a generated probe, closed in one commit: it retires, its open presentations end, and its candidate stops being one, since serving accepts any ``active`` candidate and a live one blocks its factor's next question (``duplicate_instrument_class``).
- `retire_unbound(repository: Repository, workflow_id: str, *, reason: str='publication_interrupted', keep: str | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 227) — What an interrupted run of this workflow published and never bound is withdrawn, unused, before the retry writes its own question or the workflow ends.
- `door_refusal(repository: Repository, practice_item_id: str, *, workflow_id: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 242) — Why a door may not open this generated probe now, or None.
- `served_surface(repository: Repository, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 267) — The surface whose door burned this generated probe at its first serve, or None (unserved, or no identity).
- `served_elsewhere(repository: Repository, practice_item_id: str, surface: str) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 279) — Burned at its first serve by another surface's door: its one administration is that device's.
- `door_sets(repository: Repository) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 286) — (closed, reserved): what every selector leaves out, read once.
- `exclude_ids(repository: Repository, item_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 305) — The ones in ``item_ids`` that carry the identity.
- `replay_inactive_ids(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 312) — Rebuild replay: an item the ledger closed stays closed, attempt or no attempt.

### Module constants

- `GENERATED_PROBE_CLOSED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 35)
- `GENERATED_PROBE_RESERVED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 36)
- `SERVED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 38)
- `RETIRED` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 39)
- `LESSON_SOURCE` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 41)
- `MACHINE_REVIEWER` ([src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py), line 44)

### Explicit exports

`__all__` declares:

- `Claim`
- `GENERATED_PROBE_CLOSED`
- `GENERATED_PROBE_RESERVED`
- `LESSON_SOURCE`
- `MACHINE_REVIEWER`
- `RETIRED`
- `SERVED`
- `claim_serve`
- `closed_probe_ids`
- `door_refusal`
- `door_sets`
- `exclude_ids`
- `generated_probe_ids`
- `is_generated_probe`
- `item_revision`
- `register`
- `replay_inactive_ids`
- `retire`
- `retire_unbound`
- `retired_probe_ids`
- `served_elsewhere`
- `served_surface`
- `withdraw`

## Internal implementation anchors

- `_present(connection: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/identity.py), line 57)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `closed_probe_ids`, `generated_probe_ids`, `retired_probe_ids`; statically calls `closed_probe_ids`, `generated_probe_ids`, `retired_probe_ids`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `door_sets`; statically calls `door_sets`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `item_revision`, `register`; statically calls `item_revision`, `register`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `is_generated_probe`; statically calls `is_generated_probe`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `module`; statically calls `item_revision`, `register`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `closed_probe_ids`, `is_generated_probe`, `served_elsewhere`, `withdraw`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; statically calls `is_generated_probe`, `retire_unbound`, `withdraw`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `door_sets`, `generated_probe_ids`; statically calls `door_sets`, `generated_probe_ids`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `closed_probe_ids`; statically calls `closed_probe_ids`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `closed_probe_ids`; statically calls `closed_probe_ids`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `generated_probe_ids`; statically calls `generated_probe_ids`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; statically calls `claim_serve`, `retire`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `GENERATED_PROBE_RESERVED`, `module`, `served_elsewhere`; statically calls `is_generated_probe`, `served_elsewhere`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `served_elsewhere`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `module`; statically calls `claim_serve`, `closed_probe_ids`, `door_refusal`, `is_generated_probe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `administration_ended`, `burns_for_item`, `closed_generated_probe_ids`, `generated_probe`, `generated_probe_ids`, `insert_burn`, `insert_generated_probe`, `live_candidates_of_item`, `present`, `unclosed_probes_of_workflow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]], [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f10_a_failed_workflow_withdraws_what_its_last_run_left`
  - `test_f10_an_interrupted_withdrawal_is_redone_whole`
  - `test_f10_recovery_redoes_a_withdrawal_a_crash_cut_at_the_job_boundary`
  - `test_f3_a_crash_after_the_file_leaves_an_identified_parked_item`
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_a_failed_file_write_serves_nothing_and_the_retry_goes_on`
  - `test_f3_the_mint_and_the_batch_write_the_identity_before_the_file`
  - `test_f3_the_retry_retires_the_orphan_and_serves_its_own_question`
  - `test_f4_a_burn_before_any_presentation_ends_when_one_has_ended`
  - `test_f4_a_workflowless_probe_skipped_is_never_served_again`
  - `test_f4_skipping_one_the_plan_listed_abandons_it_unserved_too`
  - `test_f4_the_burn_binds_to_the_open_presentation_and_ends_with_it`
  - `test_f4_the_claim_has_no_wildcard_for_a_missing_presentation`
  - `test_f7_a_prepared_probe_closes_with_the_switch`
  - `test_f7_a_standing_plan_doesnt_strand_next_on_a_switched_off_probe`
  - `test_f7_next_through_the_sidecar_after_the_switch`
  - `test_f7_rereview_a_crash_in_cleanup_leaves_the_workflow_open_for_recovery`
  - `test_f7_rereview_a_startup_crash_doesnt_leave_a_standing_plan_holding_the_item`
  - `test_f7_rereview_skipping_a_workflows_probe_through_the_sidecar_closes_it`
  - `test_f7_verify_a_crash_in_the_exit_leaves_all_of_it_open_for_the_next_run`
  - `test_f7_verify_a_late_generator_closes_the_episode_it_pinned`
  - `test_f7_verify_an_answer_keeps_its_own_question_and_closes_only_the_leftovers`
  - `test_f7_verify_the_settled_exit_adds_no_question_of_its_own`
  - `test_f9_a_refusal_that_arrives_during_authoring_stops_the_offer`
  - `test_f9_a_refused_retry_doesnt_leave_what_the_crash_pinned`
  - `test_f9_a_retry_rechecks_the_hard_refusals_and_keeps_the_draw`
  - `test_f9_verify_a_check_on_the_object_that_arrives_during_authoring_stops_the_offer`
  - `test_f9_verify_a_retry_is_refused_by_a_check_on_the_whole_learning_object`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_a_late_generator_adds_nothing_after_a_skip`
  - `test_a_mint_under_fg1_is_model_written_single_use_and_needs_no_review`
  - `test_a_miss_with_two_rivals_generates_one_pinned_probe`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_probe_whose_hypotheses_closed_first_is_retired_unused`
  - `test_a_reserved_probe_refuses_every_door_until_its_workflow_is_ready`
  - `test_a_wait_releases_now_labels_the_probe_exposed_and_its_answer_cant_close_the_factor`
  - `test_continue_without_it_retires_the_probe_and_next_goes_on`
  - `test_no_intervention_generates_nothing_and_releases_what_was_held`
  - `test_the_whole_journey_and_never_again`
  - `test_with_no_plan_a_ready_probe_heads_todays_queue`
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
  - `test_a_queue_miss_with_a_plan_open_opens_the_probe_and_the_plan_doesnt_serve_it_again`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_an_authored_question_echoing_a_reserved_one_is_refused_with_nothing_served`
  - `test_f20_what_a_crashed_run_pinned_closes_with_the_exhausted_job`
  - `test_r10_a_second_match_takes_the_practice_lane`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_each_shape_opens_a_factor_serves_a_question_and_its_answer_closes_it`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_a_closed_factor_retires_a_waiting_probe_at_the_boundary`
- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — direct import
  - `test_an_exam_never_reserves_one`
  - `test_an_item_with_no_identity_needs_no_claim`
  - `test_remint_refuses_the_identity`
  - `test_reserved_until_served_then_closed_for_every_selector`
  - `test_retired_while_unused_stays_retired_after_sync_and_rebuild`
  - `test_the_first_serve_is_one_atomic_claim`
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_generated_probe_attempt_opens_no_workflow`
- [tests/test_mobile_v2_followup.py](../../../../../../tests/test_mobile_v2_followup.py) — direct import
  - `test_f3_a_ready_question_says_on_the_phone_that_it_waits_for_the_desktop_and_no_phone_door_opens_it`
- [tests/test_mobile_v3_codex_review.py](../../../../../../tests/test_mobile_v3_codex_review.py) — direct import
  - `test_f1_a_phone_that_doesnt_own_the_session_never_burns_the_desktops_ready_probe`
  - `test_f1_reopened_a_handoff_and_back_between_the_check_and_the_claim_refuses_the_named_burn`
  - `test_f1_reopened_a_sessionless_phone_door_keeps_the_session_it_started_against`
  - `test_f1_the_owning_phone_still_burns_it_as_its_own`
  - `test_f2_the_desktops_next_keeps_a_phone_probe_whose_answer_is_being_graded`
  - `test_f2_with_no_answer_on_its_way_the_desktops_next_still_moves_past_the_phones_probe`
  - `test_f3_a_v2_app_gets_v2s_doors_from_a_v3_host_and_burns_nothing`
  - `test_f3_a_v2_apps_plan_step_holds_a_generated_probe_for_the_desktop`
  - `test_f3_the_v3_app_says_it_answers_probes_and_gets_v3s_door`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
  - `test_a_desktop_serving_next_with_no_phone_burn_abandons_nothing`
  - `test_a_question_the_desktop_served_is_refused_on_the_phone_and_the_phones_next_goes_on`
  - `test_the_desktops_serving_next_moves_past_a_probe_the_phone_served_and_abandons_it`
  - `test_the_phone_opens_its_question_burns_it_as_the_phones_and_the_desktop_is_refused`
  - `test_the_phones_answer_releases_the_held_feedback_and_the_question_is_never_served_again`
  - `test_without_phone_probes_the_phone_is_v2s`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_late_question_is_retired_as_it_lands`
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
  - `test_a_probe_still_preparing_is_retired_at_the_close`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again`
  - `test_f3_a_view_after_a_half_recorded_answer_delivers_its_result_instead_of_dropping_the_probe`

## Modification guidance

- Make changes here when the responsibility remains identity within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/identity.py](../../../../../../src/learnloop/followup_serve/identity.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
