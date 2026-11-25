---
title: "learnloop.tui.screens.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tui/screens/practice.py"
source_paths:
  - "src/learnloop/tui/screens/practice.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tui.screens"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.tui.screens.practice module"
  - "src/learnloop/tui/screens/practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui-screens"
---

# `learnloop.tui.screens.practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps practice behavior inside its owning package, [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]]. Its public surface centers on `PracticeScreen`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py) |
| Source lines | 596 |
| Owning package | [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class PracticeScreen(Screen)` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 51) — Focused practice card for a single Practice Item.
  - `__init__(self, state: TuiState, item: ScheduledItem)` (line 83; internal)
  - `_resolve_probe_contract(self) -> None` (line 108; internal)
  - `compose(self) -> ComposeResult` (line 174; public)
  - `on_mount(self) -> None` (line 219; public)
  - `on_screen_resume(self) -> None` (line 223; public)
  - `watch_hints_used(self, value: int) -> None` (line 227; public)
  - `answer(self) -> str` (line 235; public)
  - `set_answer(self, text: str) -> None` (line 238; public)
  - `reveal_hint(self) -> None` (line 242; public)
  - `async open_feedback(self, committed=None)` (line 254; public)
  - `press_stuck(self) -> None` (line 261; public) — "I'm stuck": one key turns the answer box into "write what you can".
  - `async submit_stuck_empty(self)` (line 272; public) — Record an empty stuck answer: an ordinary attempt scored 0, no model.
  - `_draft(self) -> AttemptDraft` (line 302; internal)
  - `async action_submit(self) -> None` (line 320; public)
  - `action_hint(self) -> None` (line 327; public)
  - `action_stop_diagnosing(self) -> None` (line 330; public) — `Stop diagnosing and teach me` (§3): end measurement.
  - `action_stuck(self) -> None` (line 345; public)
  - `action_skip(self) -> None` (line 348; public)
  - `action_back(self) -> None` (line 351; public)
  - `on_text_area_changed(self, event: TextArea.Changed) -> None` (line 355; public)
  - `on_button_pressed(self, event: Button.Pressed) -> None` (line 358; public)
  - `_refresh_answer_meta(self, text: str) -> None` (line 363; internal)
  - `_breadcrumb_content(self) -> Content` (line 370; internal)
  - `_breadcrumb_meta_content(self) -> Content` (line 379; internal)
  - `_card_title_content(self) -> Content` (line 386; internal)
  - `_card_pills_content(self) -> Content` (line 394; internal)
  - `_probe_content(self) -> Content` (line 402; internal)
  - `_stuck_content(self) -> Content` (line 431; internal)
  - `_hints_content(self) -> Content` (line 444; internal)
  - `_mastery_content(self) -> Content` (line 458; internal)
  - `_attempt_row_content(self) -> Content` (line 478; internal)
  - `_why_text_content(self) -> Content` (line 495; internal)
  - `_why_metrics_content(self) -> Content` (line 505; internal)
  - `_is_probe(self) -> bool` (line 527; internal)
  - `_primary_subject(self) -> str` (line 532; internal)
  - `_difficulty(self) -> float` (line 536; internal)
  - `_mastery_mean_sd(self) -> tuple[float, float]` (line 546; internal)
  - `_queue_position(self) -> tuple[int, int]` (line 554; internal)
  - `_attempt_number(self) -> int` (line 562; internal)

### Module constants

- `_RATING_CAPS` ([src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py), line 47)
- `_RATING_CAP_VARIANTS` ([src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py), line 48)

## Internal implementation anchors

- `_join(parts: list[Content], sep: str=' ') -> Content` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 569)
- `_relative(iso: str, now: datetime) -> str` ([source](../../../../../../../src/learnloop/tui/screens/practice.py), line 578)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `PracticeScreen`; statically calls `PracticeScreen`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `default_attempt_type`; calls `default_attempt_type`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `complete_empty_stuck_attempt`; calls `AttemptDraft`, `complete_empty_stuck_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `committed_submission_result`, `run_post_attempt_pipeline`; calls `committed_submission_result`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `STUCK_CONTROL_LABEL`, `STUCK_PROMPT_TEXT`
- [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]] — imports `STANDING`, `episode_contract`, `router_next`, `stop_diagnosing_and_teach`; calls `episode_contract`, `router_next`, `stop_diagnosing_and_teach`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_hypothesis_set`; calls `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `LearnerRefusedPin`, `ProtectedInstrument`, `RoutineDisplayCovered`, `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`, `serve_presentation`; calls `commit_item_presentation`, `probe_serving_block_reason`, `probe_value_block_reason`, `serve_presentation`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `episode_ignored`; calls `episode_ignored`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ScheduledItem`, `cold_check_serve_hold`; calls `cold_check_serve_hold`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `FeedbackScreen`; calls `FeedbackScreen`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `TuiState`
- [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] — imports `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`; calls `KeyBar`, `TextStatic`, `block_bar`, `mastery_token`, `mode_pill_color`, `pill`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`
- Third party: `textual`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_start_minutes.py](../../../../../../../tests/test_daily_loop_start_minutes.py) — direct import
  - `test_tui_next_opens_the_head_of_the_live_queue`
- [tests/test_difficulty_kinds_apart.py](../../../../../../../tests/test_difficulty_kinds_apart.py) — direct import
  - `test_scalar_display_uses_lo_prior_when_item_scalar_is_absent`
- [tests/test_e2e_tui.py](../../../../../../../tests/test_e2e_tui.py) — direct import
  - `test_tui_end_to_end_self_graded_practice`
- [tests/test_probe_router_continuation.py](../../../../../../../tests/test_probe_router_continuation.py) — direct import
  - `test_the_terminal_client_serves_the_routers_standing_question`
- [tests/test_serve_eligibility.py](../../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_tui_open_serves_a_cold_check_submit_would_prime_as_practice`
- [tests/test_stuck_prompt.py](../../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_tui_ctrl_d_opens_the_stuck_prompt_and_an_empty_submit_records_it`
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
  - `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`
- [tests/test_tui_practice.py](../../../../../../../tests/test_tui_practice.py) — direct import
  - `test_practice_screen_collects_answer_and_opens_feedback`
  - `test_practice_screen_submit_button_opens_feedback`
  - `test_practice_screen_submit_shortcut_opens_feedback`
  - `test_practice_screen_uses_item_allowed_attempt_type`
- [tests/test_tui_today.py](../../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`
- [tests/test_ux_phase4_feedback.py](../../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1k_the_tui_open_defers_a_cold_check_a_routine_display_covers`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tui/screens/practice.py](../../../../../../../src/learnloop/tui/screens/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
