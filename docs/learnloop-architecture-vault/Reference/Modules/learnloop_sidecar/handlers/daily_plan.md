---
title: "learnloop_sidecar.handlers.daily_plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/daily_plan.py"
source_paths:
  - "src/learnloop_sidecar/handlers/daily_plan.py"
source_commit: "d7ea71a54ada901931c101597697c88de081126d"
source_commit_timestamp: "2026-11-07T01:07:18-05:00"
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
  - "learnloop_sidecar.handlers.daily_plan module"
  - "src/learnloop_sidecar/handlers/daily_plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.daily_plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.daily_plan` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Daily-loop DL1 RPCs: the finite plan (``spec_daily_loop_v1.md`` §6, §7, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/daily_plan.py](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py) |
| Source lines | 733 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d7ea71a54ada901931c101597697c88de081126d` |
| Commit timestamp | `2026-11-07T01:07:18-05:00` |

## Public API

- `class PlanSessionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 76)
- `class NextPlanItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 80)
- `class PlanMinutesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 88)
- `class PlanReadingEndedInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 93)
- `class PlanKeepGoingInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 98)
- `class PlanMoreNewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 104)
- `class PlanLearnerPickInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 110)
- `class OwnerCheckedRepository` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 223) — The repository a session's plan write commits through (mobile v2 §5.6; Codex review of V2, F6): each transaction it begins runs the session's ownership check first, under the write lock it has just taken, so no adopt can commit between the check and the step's rows.
  - `__init__(self, repository: Any, check: Callable[[], None]) -> None` (line 231; internal)
  - `__getattr__(self, name: str) -> Any` (line 235; internal)
  - `base(self) -> Any` (line 239; public)
  - `atomic(self) -> Iterator[None]` (line 243; public)
- `get_daily_plan(ctx: SidecarContext, params: PlanSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 327) — Today's plan (built on first read of the day), its split, blocks and next step.
- `set_plan_minutes(ctx: SidecarContext, params: PlanMinutesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 435) — A minutes chip (§6.6): remembered, and the remaining blocks re-planned.
- `next_plan_item(ctx: SidecarContext, params: NextPlanItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 450) — The next step: ``{"kind": "item" | "reading" | "done", ...}`` (§6.10 typed steps).
- `plan_reading_ended(ctx: SidecarContext, params: PlanReadingEndedInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 506) — End the current reading block (left the reader, skipped, or completed).
- `plan_keep_going(ctx: SidecarContext, params: PlanKeepGoingInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 520) — Keep going (§6.5): one more block of minutes; or "Done" (``stop``).
- `plan_more_new(ctx: SidecarContext, params: PlanMoreNewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 536) — "More new material" (§6.3): the trade-off first, then a labelled extension.
- `plan_learner_pick(ctx: SidecarContext, params: PlanLearnerPickInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 552) — Open an item from the full list: a one-item learner-pick block (L3, G12).
- `select_on_open(ctx: SidecarContext, *, practice_item_id: str, session_id: str, proposal_id: str, source_exercise_import_id: str | None=None) -> tuple[PlanLearnerPickInput, dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 678) — The open list is about to serve a picked proposal's item (the plan off): its selection, re-checked BEFORE the serve (an item reserved for a held-out exam since it was proposed is refused).
- `deliver_on_open(ctx: SidecarContext, params: PlanLearnerPickInput, selection: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 689) — The open list served a picked proposal's item (the plan off): its delivery, recorded once after the serve (Codex re-review F10).
- `get_today_headline(ctx: SidecarContext, _params: PlanSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 712) — The optional one-line headline (§6.7, D7).

### Module constants

- `DAILY_PLAN_RPCS` ([src/learnloop_sidecar/handlers/daily_plan.py](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 64)

### Explicit exports

`__all__` declares:

- `DAILY_PLAN_RPCS`
- `PlanInactiveError`

## Internal implementation anchors

- `_env(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None, *, serve: bool=False) -> PlanEnv` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 130)
- `_step_filter(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 165) — Mobile v2 §2.2: the requesting device's step filter, from the request's origin (never a parameter); None for the desktop.
- `_require(ctx: SidecarContext, session_id: str | None, *, serve: bool=False, writes: bool=False) -> tuple[Any, Any, PlanEnv] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 195) — ``writes``: the call is a plan write naming a session, so the session's owner is checked first (mobile v2 §5.6).
- `_secondary(ctx: SidecarContext) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 251) — The phone host's attach (``load_secondary``): it runs only the phone's own work (D6).
- `_off(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 257)
- `_view(env: PlanEnv, record: Any, step: dict[str, Any] | None, context: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 263)
- `_router_decision_line(env: PlanEnv, record: Any, step: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 298) — FG1 §6.4: the router's decision on the block in hand, for debugging and calibration.
- `_current_view(env: PlanEnv) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 321)
- `_schedule_prefetch(ctx: SidecarContext, env: PlanEnv) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 340) — RW5d P5 (spec §10b.2): the stored plan's reading section and the open gaps on its topics are figure triggers.
- `_schedule_ad(ctx: SidecarContext, env: PlanEnv, *, step: Mapping[str, Any] | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 364) — Adaptive difficulty AD1 (spec §8.2, §7.2): after the response is built, the planned items' revisions are prepared for the pool in the background (feature audit, then ``llm_v1:item``), and a served step's presentation gets its ``llm_v3`` forecasts.
- `_commission_enqueue(ctx: SidecarContext) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 413) — How a commission's generation is queued: a test's injected callable, else the vault's durable ingest queue, and nothing with ``LEARNLOOP_AD_MODELS=off`` (the suite, a copy run).
- `_abandon_phone_served(env: PlanEnv) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 482) — Mobile v2 V3 (owner decision D3): a generated probe this plan served on the phone, still unanswered, when the desktop (which owns the session now, checked above) asks for its next step.
- `_refuse_held_pick(env: PlanEnv, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 622) — Mobile v2 §2.2 (Codex review of V2, F2): a by-id pick is a serving door too, so it refuses, before anything is served or written, what the device's step filter holds for the desktop (PR-6's rules, the diagnostic check this session left there, and a generated probe until V3).
- `_served_decision(record: Any, step: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 649) — The router decision of the block that served the pick (its ``decision_ref``, R1's row when R1 logs plan decisions), or None.
- `_proposal_selection(ctx: SidecarContext, params: PlanLearnerPickInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 660) — The learner's selection, validated before serving (S0, §6.3).
- `_proposal_delivery(ctx: SidecarContext, params: PlanLearnerPickInput, selection: dict[str, Any], *, router_decision_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py), line 696) — S5's intervention for a served pick (after serving succeeded).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `deliver_on_open`, `select_on_open`; statically calls `deliver_on_open`, `select_on_open`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `PlanLearnerPickInput`, `plan_learner_pick`; statically calls `PlanLearnerPickInput`, `plan_learner_pick`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `schedule_item_preparation`, `schedule_presentation_forecasts`; calls `schedule_item_preparation`, `schedule_presentation_forecasts`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `schedule_commission_generation`; calls `schedule_commission_generation`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `any_background_work`; calls `any_background_work`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `PlanInactiveError`, `PlanStillOpenError`, `advance_with_context`, `intent_view`, `keep_going`, `latest_today`, `learner_pick`, `more_new`, `picked_under`, `plan_active`, `plan_scheduler_session`, `reading_ended`, `set_minutes`, `stop_today`; calls `PlanEnv`, `advance_with_context`, `intent_view`, `keep_going`, `latest_today`, `learner_pick`, `more_new`, `picked_under`, `plan_active`, `plan_scheduler_session`, `reading_ended`, `set_minutes`, `stop_today`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `today_headline`; calls `today_headline`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `policy_for`; calls `policy_for`
- [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]] — imports `ReentryGap`, `reentry_panel`; calls `ReentryGap`, `reentry_panel`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `device_current`, `disabled_view`, `plan_view`; calls `device_current`, `disabled_view`, `plan_view`
- [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]] — imports `decision_view`, `show_router_decisions`; calls `decision_view`, `show_router_decisions`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `abandon`, `bind_plan_step`; calls `abandon`, `bind_plan_step`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `PHONE_SURFACE`, `SERVING_SURFACE`, `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `GENERATED_PROBE_RESERVED`, `module`, `served_elsewhere`; calls `is_generated_probe`, `served_elsewhere`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `imported_exercise_selection`, `record_proposal_delivery`, `record_proposal_selection`; calls `imported_exercise_selection`, `record_proposal_delivery`, `record_proposal_selection`
- [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] — imports `GENERATED_PROBE`, `PlanStepFilter`; calls `PlanStepFilter`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `build_due_queue`; calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `refresh_for_plan`; calls `refresh_for_plan`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `_nearest_active_goal`; calls `_nearest_active_goal`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `prepare_queue_build`, `revalidate_cold_check`; calls `prepare_queue_build`, `revalidate_cold_check`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `refuse_moved_session`; calls `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `filter_unready_teach_back_items`; calls `filter_unready_teach_back_items`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `notify`, `runs_here`; calls `notify`, `runs_here`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `host_mutation`, `phone_probes_on`, `plan_surface`; calls `phone_probes_on`, `plan_surface`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `DESKTOP_ONLY_ERROR_CODE`, `device_filter`, `device_policy`; calls `device_filter`, `device_policy`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_the_sidecar_queues_a_serve_commission_after_the_serve`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_todays_read_never_retries_a_plan_wait`
- [tests/test_learner_pick_proposal.py](../../../../../../tests/test_learner_pick_proposal.py) — direct import
  - `test_a_failed_pick_leaves_no_delivered_intervention`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r2_a_submit_whose_admission_fails_submits_nothing_and_stays_retryable`
  - `test_the_learner_pick_is_owed_durably_across_a_restart_and_acknowledged_only_after_delivery`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
- [tests/test_mobile_v2_plan.py](../../../../../../tests/test_mobile_v2_plan.py) — direct import
  - `test_a_none_origin_never_enters_the_device_branch`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
  - `test_the_plans_step_filter_holds_only_what_the_phone_may_not_open`
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f13_a_failure_after_the_serve_and_before_the_delivery_leaves_nothing_and_the_retry_makes_all_once`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_todays_plan_is_byte_identical_with_a_suggestion_drawn`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/daily_plan.py](../../../../../../src/learnloop_sidecar/handlers/daily_plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
