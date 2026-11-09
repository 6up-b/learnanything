---
title: "learnloop_sidecar.handlers.lesson"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/lesson.py"
source_paths:
  - "src/learnloop_sidecar/handlers/lesson.py"
source_commit: "fb0b1dc801f2dd925d9f48c997e7de4fd77def8e"
source_commit_timestamp: "2026-11-09T12:07:21-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.lesson module"
  - "src/learnloop_sidecar/handlers/lesson.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.lesson`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.lesson` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Teacher TE1 RPCs: a lesson (spec_teacher_v1 §6, §17, §19).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/lesson.py](../../../../../../src/learnloop_sidecar/handlers/lesson.py) |
| Source lines | 358 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fb0b1dc801f2dd925d9f48c997e7de4fd77def8e` |
| Commit timestamp | `2026-11-09T12:07:21-05:00` |

## Public API

- `class LessonSelection(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 76)
- `class LessonTurnInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 81)
- `class LessonViewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 107)
- `class LessonGoalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 111) — TE2 (§11.5): the typed goal to resolve (C0b's resolver; no lesson is written).
- `class LessonOpenLessonsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 117)
- `class LessonActivityInterval(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 121) — One interval of the lesson screen (TE2-log, spec §11.6): on the client's clock, foreground with input or not.
- `class LessonActivityInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 131)
- `route_unavailable_message(label: str, *, saved: bool) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 145) — The unavailable route's line, true to what exists (followups batch 5, C: an opening that failed before its lesson was saved said "your lesson is saved").
- `class LessonSuggestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 154)
- `class LessonSuggestionRespondInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 158)
- `lesson_turn(ctx: SidecarContext, params: LessonTurnInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 216) — One step of a lesson; see the module docstring.
- `lesson_view(ctx: SidecarContext, params: LessonViewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 274) — The lesson as the screen shows it (no model call).
- `lesson_goal(ctx: SidecarContext, params: LessonGoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 286) — Teacher TE2 (§11.5): a typed goal resolved by C0b's resolver (one plan call; none when the same words over the same topics were resolved before): the topics it needs, each with the phrase it answers, and what nothing matched with a proposed topic.
- `lesson_open_lessons(ctx: SidecarContext, params: LessonOpenLessonsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 307) — Teacher TE2 (§11.8): Today's *Continue your lesson on X* (no model call; empty unless TE2 serves).
- `lesson_activity(ctx: SidecarContext, params: LessonActivityInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 315) — Teacher TE2-log (spec §11.6): append the lesson screen's activity intervals (no model call, never evidence, never a decision).
- `lesson_suggestion(ctx: SidecarContext, params: LessonSuggestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 333) — Today's suggestion card, or ``null`` (TE1b; no model call).
- `lesson_suggestion_respond(ctx: SidecarContext, params: LessonSuggestionRespondInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 343) — The learner's one response to the card (TE1b); a Start returns the lesson to open.

### Module constants

- `LESSON_RPCS` ([src/learnloop_sidecar/handlers/lesson.py](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 67)
- `LESSON_ACTIVITY_RPCS` ([src/learnloop_sidecar/handlers/lesson.py](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 70)
- `LESSON_TE2_RPCS` ([src/learnloop_sidecar/handlers/lesson.py](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 73)

## Internal implementation anchors

- `class _RouteUnavailable(SidecarError)` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 139) — The teacher's route is not ready; :func:`lesson_turn` words it by whether the lesson exists yet.
- `_error(exc: S.LessonError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 166)
- `_figure_builder(ctx: SidecarContext, vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 172) — Reader RW5d P4b: how a lesson builds its teacher's visual (inline: the turn waits on it).
- `_clients(ctx: SidecarContext, vault: Any) -> S.Clients` ([source](../../../../../../src/learnloop_sidecar/handlers/lesson.py), line 188)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `SuggestionError`, `respond`, `today_suggestion`; calls `respond`, `today_suggestion`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `build_figure`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; calls `record_intervals`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; calls `Clients`, `open_lesson`, `open_lessons`, `require_active`, `take_turn`, `view_lesson`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `module`; calls `on`
- [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `MANUAL_PROVIDER`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`; calls `grading_source_for_provider`, `provider_label`, `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `refuse_moved_session`; calls `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `notify`; calls `notify`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_c_a_step_of_a_saved_lesson_whose_route_is_down_says_it_is_saved`
  - `test_c_an_opening_whose_route_is_down_says_nothing_was_saved`
  - `test_c_an_opening_whose_teacher_call_fails_after_the_save_says_it_is_saved_and_carries_its_id`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_a_lessons_turn_carries_learner_activity`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_sidecar_passes_the_learn_this_preference_to_the_opening`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_teacher_rpcs_are_all_of_them`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_lesson_turn_builds_the_visual_through_the_figure_service`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f11_the_sidecar_error_carries_the_lesson_id`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_lesson_turn_refuses_with_the_switch_off`
  - `test_lesson_turn_runs_a_lesson_and_lesson_view_resumes_it`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_start_opens_a_lesson_whose_origin_is_the_decision`
- [tests/test_teacher_te2_sidecar.py](../../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_below_the_tag_the_goal_rpc_refuses_and_the_config_carries_no_te2_key`
  - `test_lesson_goal_and_open_lessons_through_the_handlers`
  - `test_the_rpcs_are_registered_desktop_only`
- [tests/test_teacher_te2log_activity.py](../../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_lesson_activity_is_a_desktop_only_rpc_that_records_intervals`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/lesson.py](../../../../../../src/learnloop_sidecar/handlers/lesson.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
