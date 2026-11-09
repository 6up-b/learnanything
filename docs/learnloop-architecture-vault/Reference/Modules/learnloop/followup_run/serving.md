---
title: "learnloop.followup_run.serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/serving.py"
source_paths:
  - "src/learnloop/followup_run/serving.py"
source_commit: "workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.serving module"
  - "src/learnloop/followup_run/serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.serving` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: What the learner's screen and Next read from a workflow (spec §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py) |
| Source lines | 298 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65` |
| Commit timestamp | `2026-11-09T12:16:08-05:00` |

## Public API

- `class NextAction` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 49)
- `is_holding(row: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 56)
- `held_bundle(bundle: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 60) — The bundle with what is held taken out, on the server, so nothing can show it.
- `view(vault: Any, repository: Repository, attempt_id: str, *, phone: bool=False) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 83) — The screen's read of the attempt's workflow, or None (the bundle stays as it was).
- `source_of_probe_attempt(repository: Repository, attempt_id: str) -> str | None` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 118) — The miss whose held feedback this probe answer released, or None.
- `router_wait() -> str` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 130)
- `plan_will_place(vault: Any, repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 136) — R12, R13: a plan serves a workflow's probe only if the miss came from the plan, which the attempt's own validated ``plan_presentation_id`` records, and placement itself says this probe has a live placement or gets one at the next step.
- `next_action(vault: Any, repository: Repository, attempt_id: str, *, plan_serves: bool, clock: Clock | None=None, surface: str=SERVING_SURFACE) -> NextAction` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 152) — §6.1: what Next does.
- `continue_without(repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 228) — §6.1: logged, it retires the probe, and §5.1 records today's *Teach me now* authorisation.
- `show_anyway(repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 251) — §6.0: releases what's held and marks the probe's answer not independent.
- `bind_plan_step(repository: Repository, step: Mapping[str, Any] | None, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 263) — The plan served it: the decision's second presentation joins its binding.
- `abandon(repository: Repository, practice_item_id: str, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 275) — A generated probe skipped: abandonment closes it, for every generated probe, with or without a workflow, and what its workflow held is released.

### Module constants

- `PREPARING` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 21)
- `FAILED_LINE` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 22)
- `NO_PLAN_LINE` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 23)
- `READY_LINE` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 24)
- `PHONE_HANDOFF_LINE` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 28)
- `HELD_KEYS` ([src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py), line 33)

### Explicit exports

`__all__` declares:

- `FAILED_LINE`
- `HELD_KEYS`
- `NO_PLAN_LINE`
- `NextAction`
- `PREPARING`
- `abandon`
- `bind_plan_step`
- `continue_without`
- `held_bundle`
- `is_holding`
- `next_action`
- `show_anyway`
- `source_of_probe_attempt`
- `view`

## Internal implementation anchors

- `_line(vault: Any, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 66)
- `_served(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 113)
- `_administration_over(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 207)
- `_diagnosis_timed_out(vault: Any, repository: Repository, row: Mapping[str, Any], now: str) -> bool` ([source](../../../../../../src/learnloop/followup_run/serving.py), line 212) — Only while the diagnosis itself is what's outstanding; generation has *Continue without it*.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `is_holding`, `source_of_probe_attempt`; statically calls `is_holding`, `source_of_probe_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `abandon`, `bind_plan_step`; statically calls `abandon`, `bind_plan_step`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `is_holding`; statically calls `is_holding`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `held_bundle`, `is_holding`, `source_of_probe_attempt`, `view`; statically calls `held_bundle`, `is_holding`, `source_of_probe_attempt`, `view`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `continue_without`, `next_action`, `plan_will_place`, `show_anyway`, `view`; statically calls `continue_without`, `next_action`, `plan_will_place`, `show_anyway`, `view`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `abandon`; statically calls `abandon`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `FOLLOWUP_GONE`, `PlanEnv`, `followup_placement`, `latest_today`, `plan_active`; calls `PlanEnv`, `followup_placement`, `latest_today`, `plan_active`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `record_learner_preference`; calls `record_learner_preference`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `PENDING`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]] — imports `module`; calls `decision_view`, `show_router_decisions`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `recover_workflow`; calls `recover_workflow`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `module`; calls `settle_practice_lane`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `WAIT`, `module`; calls `append_outcome`, `bind_plan_presentation`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `SERVING_SURFACE`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `closed_probe_ids`, `is_generated_probe`, `served_elsewhere`, `withdraw`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `attempt_workflow`, `finish`, `get`, `lost_offer_decision`, `lost_to_lesson`, `retire_waiting`, `set_fields`, `waiting_still_valid`, `workflow_of_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f2_details_leave_out_the_held_causes_until_they_are_released`
  - `test_f4_a_skip_of_an_ordinary_item_changes_nothing`
  - `test_f4_skipping_one_the_plan_listed_abandons_it_unserved_too`
  - `test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`
  - `test_f6_a_job_that_ended_with_its_workflow_pending_says_it_failed`
  - `test_f7_rereview_continue_without_commits_its_preference_and_outcome_with_the_move`
  - `test_f7_verify_an_episode_another_presentation_still_holds_stays_open`
  - `test_f7_verify_every_exit_closes_what_an_interrupted_run_prepared`
- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
  - `test_a_door_on_a_held_screen_keeps_the_causes_held`
  - `test_an_exposure_while_held_is_recorded_and_counts`
  - `test_the_same_door_with_nothing_held_returns_the_whole_bundle`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_lesson_win_after_a_miss_generates_nothing_and_the_offer_page_opens_from_next`
  - `test_a_lesson_win_over_a_ready_probe_releases_what_was_held_and_the_probe_waits`
  - `test_a_probe_win_serves_as_before_and_releases_nothing`
  - `test_not_now_after_a_miss_goes_back_to_a_new_decision_and_the_block_resumes`
  - `test_taking_the_lesson_settles_the_followup_honestly`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
- [tests/test_mobile_v2_followup.py](../../../../../../tests/test_mobile_v2_followup.py) — direct import
  - `test_f3_a_ready_question_says_on_the_phone_that_it_waits_for_the_desktop_and_no_phone_door_opens_it`
- [tests/test_mobile_v3_codex_review.py](../../../../../../tests/test_mobile_v3_codex_review.py) — direct import
  - `test_f2_the_desktops_next_keeps_a_phone_probe_whose_answer_is_being_graded`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
  - `test_the_phone_opens_its_question_burns_it_as_the_phones_and_the_desktop_is_refused`
  - `test_without_phone_probes_the_phone_is_v2s`

## Modification guidance

- Make changes here when the responsibility remains serving within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/serving.py](../../../../../../src/learnloop/followup_run/serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
