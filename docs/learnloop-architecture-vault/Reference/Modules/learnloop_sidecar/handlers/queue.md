---
title: "learnloop_sidecar.handlers.queue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/queue.py"
source_paths:
  - "src/learnloop_sidecar/handlers/queue.py"
source_commit: "43bcc8fac4be9bfc864222dd8821769f1ee74d88"
source_commit_timestamp: "2026-11-03T19:34:35-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop_sidecar.handlers.queue module"
  - "src/learnloop_sidecar/handlers/queue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.queue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps queue behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `QueueInput`, `PracticeItemInput`, `QueueRevisionInput`, `get_queue_revision`, `prepare_queue_build`, `get_today_queue`, `record_diagnosis_serve`, `explain_practice_item_handler` and 6 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/queue.py](../../../../../../src/learnloop_sidecar/handlers/queue.py) |
| Source lines | 674 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `43bcc8fac4be9bfc864222dd8821769f1ee74d88` |
| Commit timestamp | `2026-11-03T19:34:35-05:00` |

## Public API

- `class QueueInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 65)
- `class PracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 72)
- `class QueueRevisionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 88)
- `get_queue_revision(ctx: SidecarContext, params: QueueRevisionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 96) — Cheap durable high-water mark for asynchronous Today invalidation.
- `prepare_queue_build(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 117) — What every Today queue build does first (``get_today_queue`` and the plan).
- `get_today_queue(ctx: SidecarContext, params: QueueInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 152)
- `record_diagnosis_serve(ctx: SidecarContext, repository: Any, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 269) — E7: one receipt per serve that follows a diagnosis-bearing answer.
- `explain_practice_item_handler(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 299)
- `open_queue_item(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 311) — Open one item by id, or refuse with the reason it cannot be rendered.
- `revalidate_cold_check(vault, repository, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 360) — A serve revalidates a cold check (UX Phase 4 rounds 5 and 6; the one eligibility decision, ``scheduler.cold_check_serve_decision``).
- `eligibility_dto(decision) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 382) — The served item's honest label, when its cold check could not be taken.
- `offer_trace_for(vault: Any, session_id: str | None) -> OfferTrace | None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 423) — A trace to fill when this build's offer will be logged, else None.
- `today_head_served(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 435) — Whether Today serves the queue's head (router R1's chosen candidate).
- `publish_offer(ctx: SidecarContext, vault: Any, repository: Any, queue: list[ScheduledItem], *, trace: OfferTrace | None, surface: str, removed_ids: frozenset[str]=frozenset(), alongside: Callable[[], None] | None=None) -> tuple[list[ScheduledItem], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 548) — Filter, serialize and publish one Today offer; returns (items, dtos).

### Module constants

- `_QUEUE_RELOAD_JOB_TYPES` ([src/learnloop_sidecar/handlers/queue.py](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 83)
- `_RELOAD_BATCH_WINDOW` ([src/learnloop_sidecar/handlers/queue.py](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 85)
- `_SECTION_SPECS` ([src/learnloop_sidecar/handlers/queue.py](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 397)

## Internal implementation anchors

- `_wait_for_session_diagnoses(ctx: SidecarContext, vault: Any, repository: Any, session_id: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 245) — Slice 1 §11: a bounded wait so a fast click still gets the diagnosis.
- `_sections(items: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 404)
- `_served_head(dtos: list[dict[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 413)
- `class _TeachBackReadiness` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 450) — One teach-back readiness probe per published offer, run only if needed.
- `class _OfferHeadRule` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 470) — Which item an offer shows first, for any composed order of the build.
- `_in_progress_draft(repository: Any, session_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 530) — The session's saved, unsubmitted draft, if any (router R1's "continue").
- `_offer_prefilter(vault: Any, decision: Mapping[str, Any], trace: Any, queue: Any) -> Callable[[Any], Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/queue.py), line 650) — Data capture A1: the build's prefilter, ready to link in the transaction that commits the offer's decision (Codex review F8: apart from it, a crash between the two left the decision no receipt, and the build's trace is in memory only).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `prepare_queue_build`, `revalidate_cold_check`; statically calls `prepare_queue_build`, `revalidate_cold_check`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `PracticeItemInput`, `_sections`, `eligibility_dto`, `offer_trace_for`, `publish_offer`, `record_diagnosis_serve`, `revalidate_cold_check`; statically calls `_sections`, `eligibility_dto`, `offer_trace_for`, `publish_offer`, `record_diagnosis_serve`, `revalidate_cold_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `APPLYING_JOB_TYPES`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `queue_accepted_diagnostic_followups`; calls `queue_accepted_diagnostic_followups`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `plan_active`; calls `plan_active`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; calls `settle`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `receipts_on`; calls `receipts_on`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `module`; calls `record`, `today_offer_material`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `session_diagnosis_availability`; calls `session_diagnosis_availability`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `FORECAST_VERSION`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `settle_answered_checks`; calls `settle_answered_checks`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `auto_sweep`; calls `auto_sweep`
- [[Reference/Modules/learnloop/router/decisions|learnloop.router.decisions]] — imports `build_today_offer_decision`, `logging_enabled`, `record_decision`; calls `build_today_offer_decision`, `logging_enabled`, `record_decision`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `reentry_session_cap`; calls `reentry_session_cap`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `OfferTrace`, `SELECTION_POLICY`, `ScheduledItem`, `SchedulerSession`, `build_due_queue`, `cold_check_serve_decision`, `deferred_cold_followups`, `explain_practice_item`; calls `OfferTrace`, `SchedulerSession`, `build_due_queue`, `cold_check_serve_decision`, `deferred_cold_followups`, `explain_practice_item`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decision_active`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `UNSERVABLE_ERROR_CODE`, `unservable_refusal`; calls `unservable_refusal`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `_nearest_active_goal`; calls `_nearest_active_goal`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `prepare_followups`; calls `prepare_followups`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `_due_status`, `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`; calls `_due_status`, `latest_scheduler_explanation_dto`, `practice_item_detail`, `scheduled_item_dtos`, `scheduler_explanation_dto`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`, `filter_unready_teach_back_items`, `teach_back_offerable`; calls `filter_unready_teach_back_items`, `teach_back_offerable`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `offer_surface`; calls `offer_surface`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `device_filter`, `device_policy`, `refuse_device_ineligible_item`, `refuse_held_out_item`, `refuse_unservable_item`; calls `device_filter`, `device_policy`, `refuse_device_ineligible_item`, `refuse_held_out_item`, `refuse_unservable_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_the_reentry_cap_is_applied_after_the_filter_too`
- [tests/test_diagnosis_async_router.py](../../../../../../tests/test_diagnosis_async_router.py) — direct import
  - `test_a_failed_or_budget_skipped_diagnosis_is_unavailable_at_the_serve`
- [tests/test_mobile_rpc.py](../../../../../../tests/test_mobile_rpc.py) — direct import
  - `test_a_desktop_only_item_is_refused_at_each_door_and_counted`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_logging_failure_never_fails_the_offer`
  - `test_an_offer_row_the_ledger_refuses_is_warned_and_the_offer_still_publishes`
  - `test_teach_back_readiness_is_probed_once_per_offer`
  - `test_the_full_list_seam_follows_dl1s_plan_once_it_lands`
  - `test_the_head_rule_and_the_served_list_read_one_state_snapshot`
  - `test_while_the_plan_serves_the_full_list_logs_no_system_choice_and_every_bind_is_a_pick`
- [tests/test_router_r1_composition.py](../../../../../../tests/test_router_r1_composition.py) — direct import
  - `test_the_full_list_seam_reads_the_plan`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_a_learners_pick_of_a_cold_check_submit_would_prime_is_served_as_practice`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/queue.py](../../../../../../src/learnloop_sidecar/handlers/queue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
