---
title: "learnloop_sidecar.server"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/server.py"
source_paths:
  - "src/learnloop_sidecar/server.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.server module"
  - "src/learnloop_sidecar/server.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.server`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps server behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `serve`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py) |
| Source lines | 340 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `serve(stdin: TextIO, stdout: TextIO) -> None` ([source](../../../../../src/learnloop_sidecar/server.py), line 34)

### Module constants

- `LOG` ([src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py), line 26)
- `_INTERNAL_ERROR_MESSAGE` ([src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py), line 28)
- `_BATCH_KEYS` ([src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py), line 179)

## Internal implementation anchors

- `_handle(ctx: SidecarContext, request: Any, *, trace_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/server.py), line 57) — One RPC under its trace (ADR-017): a new one per request, or the phone host's, which it births first.
- `_handle_request(ctx: SidecarContext, request: Any) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/server.py), line 69)
- `_offered(ctx: SidecarContext, offers: plan_fallback.OfferCollector, method_name: str) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/server.py), line 157) — Mint this response's offer (redesign D): the action that asked, its units, the vault's epoch.
- `_reported_batches(value: Any, depth: int=0) -> list[str]` ([source](../../../../../src/learnloop_sidecar/server.py), line 183) — The ingest batch ids a response reports, in order (bounded walk).
- `_attach_fallback_offer(exc: SidecarError, hint: dict[str, Any] | None) -> None` ([source](../../../../../src/learnloop_sidecar/server.py), line 204) — Plan-first transport T1: an unavailable ChatGPT-plan route offers OpenRouter.
- `_with_fallback_offer(result: Any, hint: dict[str, Any] | None) -> Any` ([source](../../../../../src/learnloop_sidecar/server.py), line 216) — The same hint on a result that degraded instead of failing (a dict result only).
- `_foreground(method_name: str)` ([source](../../../../../src/learnloop_sidecar/server.py), line 228) — RW5d P5 (spec §10b.4): a learner-facing method in flight is foreground work, which background figure prebuilds yield to (no prebuild starts while it runs).
- `_observed_model_calls(ctx: SidecarContext, method_name: str, params: Any)` ([source](../../../../../src/learnloop_sidecar/server.py), line 238) — Record every model call the handler makes, owned by its submission or RPC.
- `_busy_error(exc: Exception) -> SidecarError | None` ([source](../../../../../src/learnloop_sidecar/server.py), line 250) — Map lock contention to a retryable error; None for any other failure.
- `_internal_error(request_id: Any, method_name: str, started: float, *, offer: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/server.py), line 274)
- `_elapsed_ms(started: float) -> float` ([source](../../../../../src/learnloop_sidecar/server.py), line 292)
- `_write(stdout: TextIO, response: dict[str, Any]) -> None` ([source](../../../../../src/learnloop_sidecar/server.py), line 296)
- `_request_id(request: Any) -> Any` ([source](../../../../../src/learnloop_sidecar/server.py), line 320)
- `_safe_validation_errors(exc: ValidationError) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop_sidecar/server.py), line 324) — Return actionable Pydantic diagnostics without echoing request values.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]] — imports `serve`; statically calls `serve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `collecting`, `mint_offer`, `relay_batch_offers`, `request`, `take_offer`
- [[Reference/Modules/learnloop/attempts/completion_lock|learnloop.attempts.completion_lock]] — imports `AttemptCompletionBusy`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `SourceSetsUnreadable`
- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `FOREGROUND_METHODS`, `foreground`; calls `foreground`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `trace_scope`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`; calls `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `to_camel`; calls `to_camel`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`, `json_rpc_error`, `sidecar_error`; calls `SidecarError`, `json_rpc_error`, `sidecar_error`
- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `submission_key`; calls `submission_key`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `METHOD_REGISTRY`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `logging`, `sqlite3`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/plan_first_transport_offer_grants_helpers.py](../../../../../tests/plan_first_transport_offer_grants_helpers.py) — direct import
- [tests/settings_sidecar_helpers.py](../../../../../tests/settings_sidecar_helpers.py) — direct import
- [tests/sidecar_contract_helpers.py](../../../../../tests/sidecar_contract_helpers.py) — direct import
- [tests/sidecar_reader_helpers.py](../../../../../tests/sidecar_reader_helpers.py) — direct import
- [tests/sidecar_reader_p3_helpers.py](../../../../../tests/sidecar_reader_p3_helpers.py) — direct import
- [tests/sidecar_tutor_qa_helpers.py](../../../../../tests/sidecar_tutor_qa_helpers.py) — direct import
- [tests/source_service_fakes.py](../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_approach_maps.py](../../../../../tests/test_approach_maps.py) — direct import
  - `test_m4_shutdown_and_eof_drain_within_their_bound`
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
- [tests/test_diagnosis_async_router.py](../../../../../tests/test_diagnosis_async_router.py) — direct import
- [tests/test_diagnosis_card.py](../../../../../tests/test_diagnosis_card.py) — direct import
- [tests/test_facet_identity_ingest.py](../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_the_desktop_lists_a_runs_merges_and_undoes_one`
- [tests/test_k1_unreadable_adapters.py](../../../../../tests/test_k1_unreadable_adapters.py) — direct import
  - `test_a_method_that_reads_no_exam_material_is_unaffected`
  - `test_the_sidecar_answers_a_typed_error_where_exam_material_is_read`
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p5_scrolling_after_a_build_yes_queues_nothing_that_carries_a_grant`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_plan_first_transport_today_quiet.py](../../../../../tests/test_plan_first_transport_today_quiet.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../tests/test_probe_orchestration_remainder.py) — direct import
- [tests/test_probe_remint.py](../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
  - `test_a_phone_request_births_its_trace_and_hands_it_to_the_sidecar`
  - `test_each_sidecar_rpc_runs_under_a_trace_of_its_own`
- [tests/test_provenance_service.py](../../../../../tests/test_provenance_service.py) — direct import
- [tests/test_question_queue.py](../../../../../tests/test_question_queue.py) — direct import
  - `test_sidecar_queue_roundtrip`
  - `test_sidecar_reader_question_transcript_can_be_resumed`
- [tests/test_reveal_ledger.py](../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_reopening_feedback_does_not_charge_again`
- [tests/test_sidecar_animation.py](../../../../../tests/test_sidecar_animation.py) — direct import
- [tests/test_sidecar_append.py](../../../../../tests/test_sidecar_append.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_the_sidecars_eof_cancels_a_running_discovery`
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
- [tests/test_sidecar_idle_threads.py](../../../../../tests/test_sidecar_idle_threads.py) — direct import
  - `test_the_sidecars_eof_closes_its_context`
- [tests/test_sidecar_ingest_m3.py](../../../../../tests/test_sidecar_ingest_m3.py) — direct import
- [tests/test_sidecar_item_authoring.py](../../../../../tests/test_sidecar_item_authoring.py) — direct import
- [tests/test_sidecar_knowledge_model.py](../../../../../tests/test_sidecar_knowledge_model.py) — direct import
- [tests/test_sidecar_probe.py](../../../../../tests/test_sidecar_probe.py) — direct import
- [tests/test_sidecar_quick_add.py](../../../../../tests/test_sidecar_quick_add.py) — direct import
- [tests/test_sidecar_registry.py](../../../../../tests/test_sidecar_registry.py) — direct import
- [tests/test_sidecar_source_retrieval.py](../../../../../tests/test_sidecar_source_retrieval.py) — direct import
- [tests/test_sidecar_span_view.py](../../../../../tests/test_sidecar_span_view.py) — direct import
- [tests/test_sidecar_synthesis.py](../../../../../tests/test_sidecar_synthesis.py) — direct import
- [tests/test_sidecar_teach_back.py](../../../../../tests/test_sidecar_teach_back.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_non_serializable_handler_result_becomes_a_protocol_error_response`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`
- [tests/test_source_deletion.py](../../../../../tests/test_source_deletion.py) — direct import
- [tests/test_source_space_resolver.py](../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_the_open_rpc_records_nothing_with_the_switches_off`
- [tests/test_ux_phase1_first_run.py](../../../../../tests/test_ux_phase1_first_run.py) — direct import
- [tests/test_version_floor.py](../../../../../tests/test_version_floor.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/server.py](../../../../../src/learnloop_sidecar/server.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
