---
title: "learnloop_sidecar.handlers.hints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/hints.py"
source_paths:
  - "src/learnloop_sidecar/handlers/hints.py"
source_commit: "09380802a8e4a0b2693c22985b6bd8b291cc974e"
source_commit_timestamp: "2026-11-01T21:02:12-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop_sidecar.handlers.hints module"
  - "src/learnloop_sidecar/handlers/hints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.hints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.hints` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Adaptive hints H2a RPCs: hints written for the learner's work (spec_adaptive_hints_v1 §4.1, §5, §7.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py) |
| Source lines | 544 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `09380802a8e4a0b2693c22985b6bd8b291cc974e` |
| Commit timestamp | `2026-11-01T21:02:12-05:00` |

## Public API

- `class HintJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 92) — Hint jobs in flight and just finished (in memory, per sidecar).
  - `__init__(self) -> None` (line 95; internal)
  - `start(self, ctx: SidecarContext, practice_item_id: str, work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> _HintJob` (line 99; public)
  - `get(self, job_id: str) -> _HintJob | None` (line 155; public)
- `class RequestHintInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 181)
- `request_hint(ctx: SidecarContext, params: RequestHintInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 200) — Ask for a hint written for the learner's work (a job; see the module).
- `class HintJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 432)
- `hint_job(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 437) — A hint job's state, at once (never a wait on the request path).
- `cancel_hint(ctx: SidecarContext, params: HintJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 452) — Cancel a hint request before it is shown: it is never delivered, and its row stays ``shown = 0`` (it counts nothing).
- `class DiscriminateAnswerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 465)
- `answer_discriminating(ctx: SidecarContext, params: DiscriminateAnswerInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 476) — Record the learner's answer to a discriminating question (fire and forget: the screen never waits on it).
- `class SetHelpStyleInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 517)
- `set_help_style(ctx: SidecarContext, params: SetHelpStyleInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 522) — Write the one stored help-style preference every surface reads (``[hints] help_style``, spec D5): from the hint panel's "⋯" menu and from Settings.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 57)
- `HINT_SERVICE_RPCS` ([src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 60)
- `MAX_KEPT_JOBS` ([src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 67)
- `HINT_PANEL_RPCS` ([src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 513)
- `HELP_STYLES` ([src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 514)

### Explicit exports

`__all__` declares:

- `HELP_STYLES`
- `HINT_PANEL_RPCS`
- `HINT_SERVICE_RPCS`
- `HintJobs`

## Internal implementation anchors

- `class _HintJob` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 71)
- `_as_sidecar_error(exc: BaseException) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 160)
- `_jobs(ctx: SidecarContext) -> HintJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 169)
- `_immediate(result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 177)
- `_figure_provider(vault: Any, repository: Any, item: Any) -> Callable[[Any], Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 251) — Reader RW5d P3 (§11.4): the chooser's ``explore_figure`` precondition read, given to the hint service only while ``figures.help_kind_enabled`` is on, and never on a check on your own (as no hint is offered there unasked: G-SM17).
- `_job_payload(ctx: SidecarContext, job: _HintJob) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 286) — The job as the wire reads it; the read that returns a ready hint delivers it.
- `_figure_reveal(repository: Any, item: Any, figure_id: str) -> tuple[float, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 317) — A served figure's key overlap (its model-written text and readouts, :func:`learnloop.figures.help.reveal_text`) and its reveal basis.
- `_figure_deliverable(vault: Any, repository: Any, assist_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 329) — Whether a prepared row may be shown now: every row but a chooser's figure; that one only with ``figures.help_kind_enabled`` on, its figure not withheld now and its item not cold now (rechecked at delivery, as a figure build's delivery is).
- `class _RevealNotRecorded(Exception)` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 358) — The shown hint's reveal could not be written (rolls the delivery back).
- `_deliver(ctx: SidecarContext, practice_item_id: str, assist_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 362) — Show the prepared row and write its key overlap to the reveal ledger (§5: ``tutor_answer`` with basis ``hint:<kind>:L<level>``) in ONE transaction (review round 2, V4): a hint is never shown without its reveal.
- `_schedule_merge(ctx: SidecarContext, vault: Any, repository: Any, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 418) — H1's lazy learner-route merge after a hint is shown (H2a review F9): background, with H1's locks, claim, lease, envelope and kill switches; never delays or fails the delivery.
- `_require_job(ctx: SidecarContext, job_id: str) -> _HintJob` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 443)
- `_queue_learner_text(ctx: SidecarContext, vault: Any, repository: Any, assist_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/hints.py), line 499) — Queue a ``hint_feedback`` learner text (H2b, migration 212) and wake the post-attempt worker's ``gaps`` slot.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `HintJobs`, `_as_sidecar_error`; statically calls `HintJobs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal_strict`, `reveal_episode_id`; calls `record_reveal_strict`, `reveal_episode_id`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_hint_feedback`; calls `enqueue_hint_feedback`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `help_kind_enabled`; calls `help_kind_enabled`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `module`, `reveal_text`; calls `chain_root`, `offer_view`, `qualifying_figure`, `reveal_text`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `figure_withheld`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `schedule_merge_after_hint`; calls `schedule_merge_after_hint`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `HintRequestError`, `HintRequestV1`, `adaptive_enabled`, `module`; calls `HintRequestV1`, `HintResultV1`, `adaptive_enabled`, `deliver_hint`, `record_discriminate_answer`, `request_hint`, `reveal_amount`, `reveal_basis`, `reveal_exempt`, `shown_text`, `undelivered_result`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `apply_config_updates`; calls `apply_config_updates`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `_item_cold`; calls `_item_cold`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `_in_diagnostic_block`; calls `_in_diagnostic_block`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `require_owned_session`; calls `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `logging`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_the_sidecar_never_offers_a_figure_cold_or_switched_off`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f5_a_chooser_figure_line_switched_off_before_delivery_is_not_shown`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_hints_h2a_rpcs_are_all_of_them`
  - `test_the_pinned_hints_h2b_rpcs_are_all_of_them`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_hint_job_started_in_the_request_carries_its_grant_and_a_background_one_does_not`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`
  - `test_p2_a_relayed_offer_keeps_the_jobs_starting_method`
  - `test_s5_a_regrant_never_revives_a_token_a_waiting_worker_captured`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
  - `test_m1_every_relay_path_keeps_its_units_vault_and_epoch`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/hints.py](../../../../../../src/learnloop_sidecar/handlers/hints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
