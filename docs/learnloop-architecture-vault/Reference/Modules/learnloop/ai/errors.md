---
title: "learnloop.ai.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/errors.py"
source_paths:
  - "src/learnloop/ai/errors.py"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.errors module"
  - "src/learnloop/ai/errors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.errors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.errors` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Provider-neutral AI error taxonomy with legacy Codex aliases.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/errors.py](../../../../../../src/learnloop/ai/errors.py) |
| Source lines | 62 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0395ae32f9e2e40d1cb98b38402631299a94003f` |
| Commit timestamp | `2026-09-07T12:49:13-04:00` |

## Public API

- `class AIProviderUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/ai/errors.py), line 4) — The selected provider could not produce a usable completion.
- `class AIInvalidOutput(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/errors.py), line 8) — A provider response failed its declared wire contract after repair.
- `class AIInterrupted(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/errors.py), line 12) — A LearnLoop-owned provider turn was explicitly interrupted.
- `class AIOutputTruncated(AIInvalidOutput)` ([source](../../../../../../src/learnloop/ai/errors.py), line 16) — Generation exhausted its output budget; JSON repair cannot recover it.
- `class AITurnTimeout(AIProviderUnavailable, TimeoutError)` ([source](../../../../../../src/learnloop/ai/errors.py), line 20) — A provider turn exceeded its wall-clock deadline.
- `class VideoGenerationFailed(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/errors.py), line 24) — A video-generation job ended in a terminal non-success state.
  - `__init__(self, message: str, *, status: str='failed', job_id: str | None=None, shot_index: int | None=None) -> None` (line 27; internal)
- `class VideoGenerationTimeout(AITurnTimeout)` ([source](../../../../../../src/learnloop/ai/errors.py), line 41) — A storyboard did not finish within its wall-clock budget.

### Explicit exports

`__all__` declares:

- `AIInterrupted`
- `AIInvalidOutput`
- `AIProviderUnavailable`
- `AITurnTimeout`
- `VideoGenerationFailed`
- `VideoGenerationTimeout`
- `CodexInterrupted`
- `CodexTurnTimeout`
- `CodexUnavailable`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `AIInterrupted`, `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`; statically calls `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CodexUnavailable`; statically calls `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `AIProviderUnavailable`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `CodexUnavailable`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] and 17 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
  - `test_sdk_codex_turn_timeout_interrupts_and_returns`
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
- [tests/test_concept_animation_service.py](../../../../../../tests/test_concept_animation_service.py) — direct import
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_codex_timeout_releases_lease_and_continues_draining`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_codex_does_not_repair_when_reported_output_consumed_the_budget`
  - `test_inventory_retry_reuses_validated_window_after_interruption`
  - `test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_model_work_checkpoints.py](../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_inventory_window_checkpoint_that_no_longer_validates_is_discarded`
- [tests/test_multimodal_client.py](../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
  - `test_chat_gives_up_when_retry_after_outlasts_the_deadline`
  - `test_chat_retries_share_one_deadline`
  - `test_chat_retry_count_stays_bounded`
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_missing_key_raises`
- [tests/test_openrouter_video_client.py](../../../../../../tests/test_openrouter_video_client.py) — direct import
  - `test_factory_requires_an_openrouter_profile`
  - `test_missing_key_and_model_are_typed`
  - `test_poll_retries_once_on_5xx_then_surfaces_errors`
  - `test_poll_retries_transport_errors_a_few_times_with_a_pause`
  - `test_submit_rejection_is_typed_and_never_retried`
  - `test_transport_maps_socket_errors_to_provider_unavailable`
  - `test_wait_all_failure_carries_the_shot_index`
  - `test_wait_all_times_out_and_checkpoint_exceptions_stop_polling`
  - `test_wait_all_treats_an_error_payload_as_terminal_even_with_an_unknown_status`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_proposal_persistence.py](../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_timed_out_repair_fails_without_persisting_first_pass`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_evidence_pass_retry_reuses_first_paid_pass`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest`
- [tests/test_tutor_promotion_service.py](../../../../../../tests/test_tutor_promotion_service.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/errors.py](../../../../../../src/learnloop/ai/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
