---
title: "learnloop.ai.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/errors.py"
source_paths:
  - "src/learnloop/ai/errors.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

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

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `AIInterrupted`, `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`; statically calls `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex_lockdown|learnloop.ai.providers.codex_lockdown]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`; statically calls `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CodexUnavailable`; statically calls `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `AIProviderUnavailable`, `VideoGenerationFailed`, `VideoGenerationTimeout`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `AIProviderUnavailable`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AITurnTimeout`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`; statically calls `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`; statically calls `AIInterrupted`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`; statically calls `AIInvalidOutput`, `AITurnTimeout`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIInterrupted`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `AIInterrupted`; statically calls `AIInterrupted`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `AIInterrupted`, `AIProviderUnavailable`; statically calls `AIInterrupted`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `AIInterrupted`, `AIInvalidOutput`; statically calls `AIInterrupted`, `AIInvalidOutput`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `AIInvalidOutput`; statically calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `CodexUnavailable`
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

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] and 106 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/diagnosis_fakes.py](../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/embedding_fakes.py](../../../../../../tests/embedding_fakes.py) — direct import
- [tests/facet_identity_fakes.py](../../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/passage_cue_fakes.py](../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
- [tests/test_ad1_send_guard.py](../../../../../../tests/test_ad1_send_guard.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable`
- [tests/test_ai_single_request.py](../../../../../../tests/test_ai_single_request.py) — direct import
  - `test_codex_single_request_disables_regeneration_and_repair_only_in_scope`
  - `test_codex_single_request_fails_closed_before_sdk_startup`
  - `test_openai_single_request_disables_retry_and_repair_only_in_scope`
- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_an_unconfinable_agent_is_refused_before_any_request`
  - `test_codex_refuses_an_isolated_request_without_bubblewrap`
- [tests/test_chat_total_transport_deadline.py](../../../../../../tests/test_chat_total_transport_deadline.py) — direct import
  - `test_f2_delayed_response_headers_are_cancelled_at_the_deadline_not_abandoned`
  - `test_f2_rereview_partial_sends_inside_one_write_are_bounded_by_the_total_deadline`
  - `test_f2_slow_connect_and_upload_count_against_the_same_deadline`
  - `test_nov1_r1_an_environment_proxy_no_longer_routes_metered_calls`
  - `test_rw6b2_f3_a_dribbling_response_is_aborted_at_the_total_deadline`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_a_deadline_that_passes_while_waiting_for_the_refresh_lock_sends_nothing`
  - `test_an_expired_deadline_is_never_extended_into_a_send`
  - `test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing`
  - `test_an_interrupt_while_waiting_for_the_refresh_lock_sends_nothing`
  - `test_incomplete_truncated_and_broken_streams`
  - `test_single_request_never_repairs_or_retries`
  - `test_the_deadline_shuts_a_stalled_stream`
- [tests/test_chatgpt_plan_signin.py](../../../../../../tests/test_chatgpt_plan_signin.py) — direct import
  - `test_a_refresh_that_drops_plan_usage_never_serves_a_restricted_token`
  - `test_transient_refresh_failure_keeps_credentials`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_call_without_a_call_id_is_invalid_output`
  - `test_a_workspace_turn_never_runs_under_a_single_request_budget`
  - `test_an_interrupt_mid_turn_stops_it_and_keeps_what_was_served`
  - `test_inline_mode_serves_a_workspace_over_its_budget_in_tools_mode`
  - `test_the_deadline_covers_every_round`
  - `test_the_round_budget_asks_for_the_answer_then_fails_closed`
- [tests/test_codex_isolation_mcp_check.py](../../../../../../tests/test_codex_isolation_mcp_check.py) — direct import
  - `test_a_check_that_fails_or_times_out_refuses_the_turn`
  - `test_a_check_the_sandbox_refuses_refuses_the_turn`
  - `test_a_feature_toggle_that_turns_an_isolation_feature_back_on_refuses_the_turn`
  - `test_a_missing_codex_cli_refuses_the_turn`
  - `test_a_server_nothing_disables_refuses_the_turn`
  - `test_an_argument_after_app_server_the_check_cannot_read_refuses_the_turn`
  - `test_an_interrupt_during_the_check_stops_it_and_nothing_launches`
  - `test_an_interrupt_stops_a_check_running_inside_the_sandbox`
  - `test_connectors_or_plugins_left_on_refuse_the_turn`
  - `test_the_check_runs_inside_the_request_deadline`
  - `test_the_installed_codex_addresses_path_characters_but_not_dots`
  - `test_the_turn_gets_only_what_the_check_left_of_the_deadline`
- [tests/test_codex_lockdown_round3.py](../../../../../../tests/test_codex_lockdown_round3.py) — direct import
  - `test_an_export_over_the_inline_budget_refuses_before_launch`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
  - `test_sdk_codex_turn_timeout_interrupts_and_returns`
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
- [tests/test_codex_tool_lockdown.py](../../../../../../tests/test_codex_tool_lockdown.py) — direct import
  - `test_a_failure_before_any_usage_reports_nothing_new`
  - `test_a_tool_item_refuses_the_answer`
  - `test_a_workspace_that_is_the_vault_is_refused`
  - `test_tokens_reported_before_an_ordinary_failure_reach_the_receipt_and_the_settle`
- [tests/test_concept_animation_service.py](../../../../../../tests/test_concept_animation_service.py) — direct import
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
- [tests/test_decider_client.py](../../../../../../tests/test_decider_client.py) — direct import
  - `test_a_transport_error_echoing_a_key_reaches_neither_receipt_nor_caller`
  - `test_an_unreachable_endpoint_is_recorded_as_network_without_a_status`
  - `test_missing_key_and_oversized_state_refuse_before_any_request`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f1_a_path_retry_after_protection_changed_is_never_sent`
  - `test_f6_a_failed_coverage_shows_failed_and_try_again_recovers`
- [tests/test_diagnosis_history_modes.py](../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_snapshot_is_unavailable_without_the_capability`
- [tests/test_diagnosis_isolation.py](../../../../../../tests/test_diagnosis_isolation.py) — direct import
  - `test_an_sdk_that_cannot_take_config_overrides_fails_closed`
  - `test_isolated_operations_are_refused_by_a_transport_that_cannot_isolate`
  - `test_the_blind_grader_always_asks_for_an_isolated_turn`
  - `test_unlisted_mcp_servers_fail_closed`
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
- [tests/test_embedding_route_isolation.py](../../../../../../tests/test_embedding_route_isolation.py) — direct import
  - `test_direct_provider_resolution_defaults_to_generation`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
- [tests/test_figure_region.py](../../../../../../tests/test_figure_region.py) — direct import
  - `test_an_image_request_is_refused_by_a_transport_that_cannot_read_images`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_without_a_grant_a_plan_down_job_waits_and_asks_nothing`
- [tests/test_figure_rich_review_fixes.py](../../../../../../tests/test_figure_rich_review_fixes.py) — direct import
  - `test_a_rich_only_tier_judgment_is_receipted_once_against_its_request`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_without_a_grant_the_job_belongs_to_no_action_waits_and_a_read_asks_again`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f17_a_plan_wait_is_not_retried_off_mains_or_switched_off`
  - `test_f17_a_speculative_prebuilds_plan_wait_is_retried_by_the_reader_read`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_c_an_opening_whose_teacher_call_fails_after_the_save_says_it_is_saved_and_carries_its_id`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_a_plan_wait_the_reader_stopped_retrying_is_retried_by_the_next_pass`
  - `test_the_pass_and_the_reader_share_one_pacing`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_the_worker_rechecks_before_the_store`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_hardcase_harness_retries_a_truncated_grade_once_at_double`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
- [tests/test_hint_h2b_fix4.py](../../../../../../tests/test_hint_h2b_fix4.py) — direct import
  - `test_f13_an_interrupted_placement_stops_the_pass_at_once`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_codex_timeout_releases_lease_and_continues_draining`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_codex_does_not_repair_when_reported_output_consumed_the_budget`
  - `test_inventory_retry_reuses_validated_window_after_interruption`
  - `test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_the_llm_judge_runs_on_the_subscription_route_by_default`
- [tests/test_label_roles_cli.py](../../../../../../tests/test_label_roles_cli.py) — direct import
- [tests/test_model_work_checkpoints.py](../../../../../../tests/test_model_work_checkpoints.py) — direct import
  - `test_inventory_window_checkpoint_that_no_longer_validates_is_discarded`
- [tests/test_multimodal_client.py](../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
  - `test_chat_gives_up_when_retry_after_outlasts_the_deadline`
  - `test_chat_retries_share_one_deadline`
  - `test_chat_retry_count_stays_bounded`
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_empty_batch_and_provider_failure_do_not_retry`
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
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_a_profile_maximum_is_never_exceeded_by_the_retry`
  - `test_a_second_truncation_fails_and_is_never_accepted`
  - `test_an_owner_set_budget_is_never_exceeded_and_its_truncation_is_logged`
  - `test_inside_a_caller_budget_the_transport_leaves_the_retry_to_the_caller`
  - `test_paid_calls_fail_on_a_second_truncation`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_quote_check_without_its_span_support_verdict_is_never_verified`
  - `test_an_interrupted_run_resumes_without_repaying_finished_work`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
  - `test_errors_never_quote_model_output`
- [tests/test_proposal_persistence.py](../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_timed_out_repair_fails_without_persisting_first_pass`
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_decider_that_cannot_answer_reads_nothing`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_a_provider_failure_is_retried_later_and_then_lands`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_a_decider_that_cannot_answer_routes_to_ask`
- [tests/test_reader_passage_check.py](../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_transport_that_cannot_isolate_the_passage_is_refused_before_any_request`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f2_an_unavailable_decider_spends_no_allowance`
- [tests/test_reader_rw3b_fix_round5.py](../../../../../../tests/test_reader_rw3b_fix_round5.py) — direct import
  - `test_the_daily_cap_refuses_a_retry_that_would_pass_it`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_a_failed_judgment_says_so_keeps_the_guide_and_try_again_judges_again`
  - `test_f4_raising_the_cap_or_pricing_the_route_lifts_the_refusal_in_the_same_context`
  - `test_f6_a_failed_judgment_gives_its_claim_back`
  - `test_fix_a_cached_reason_quoting_a_section_held_out_since_is_never_shown`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_a_transport_failure_of_the_writer_is_still_retried`
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f17_a_cancellation_during_the_judgment_is_not_swallowed`
  - `test_f17_a_failed_judgment_leaves_the_job_retryable_and_a_rerun_resumes_without_regenerating`
- [tests/test_required_method_rereview.py](../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f20_a_partial_judgment_resumes_without_any_paid_pipeline_work`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f20_a_missing_judgment_alone_fits_max_calls_one`
  - `test_f20_a_resumable_job_resolves_no_pipeline_route_and_plans_no_pipeline_work`
  - `test_f22_a_partial_selection_left_by_an_earlier_run_is_finished_first`
  - `test_f22_an_interrupted_selection_is_finished_before_any_judgment`
- [tests/test_required_method_round3_rereview.py](../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f9_the_resume_budgets_the_largest_judgment_estimates_not_the_longest_stems`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f6_a_job_whose_every_verdict_is_recorded_publishes_without_a_judge`
  - `test_f7_a_resume_is_estimated_from_the_persisted_unfinished_stem`
  - `test_f7_a_selection_to_finish_is_estimated_from_its_survivors`
- [tests/test_rw1a_composition.py](../../../../../../tests/test_rw1a_composition.py) — direct import
  - `test_a_second_truncation_fails_the_check_and_is_never_accepted`
  - `test_a_truncation_at_the_transports_ceiling_is_not_retried`
- [tests/test_section_coverage.py](../../../../../../tests/test_section_coverage.py) — direct import
  - `test_a_failed_judgment_writes_nothing`
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f1_a_retry_after_protection_changed_is_never_sent`
  - `test_f3_a_failed_qwen_query_still_searches_deep`
  - `test_rr_f1_a_retry_after_a_role_changed_on_disk_is_never_sent`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_evidence_pass_retry_reuses_first_paid_pass`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
- [tests/test_source_vector_backfill.py](../../../../../../tests/test_source_vector_backfill.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request`
  - `test_the_compare_harness_never_resends_a_profile_maximum`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_failed_teach_back_grading_closes_its_run_as_failed`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f10_deferred_read_results_are_kept_until_a_turn_consumes_them`
  - `test_f11_an_opening_failure_carries_the_saved_lesson_and_resume_runs_it`
  - `test_f12_three_provider_invalid_outputs_close_the_lesson_as_a_contract_failure`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_schema_refusal_names_fields_by_location_never_by_their_input`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_cancellation_is_never_a_fallback`
  - `test_a_decider_cancellation_in_misconception_matching_never_reaches_the_llm`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`
- [tests/test_tutor_promotion_service.py](../../../../../../tests/test_tutor_promotion_service.py) — direct import
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_errors_never_carry_the_key_or_the_body`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/errors.py](../../../../../../src/learnloop/ai/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
