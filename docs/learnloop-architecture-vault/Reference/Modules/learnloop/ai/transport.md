---
title: "learnloop.ai.transport"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/transport.py"
source_paths:
  - "src/learnloop/ai/transport.py"
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
  - "learnloop.ai.transport module"
  - "src/learnloop/ai/transport.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.transport`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.transport` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Small provider-neutral transport contract for structured AI work.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py) |
| Source lines | 343 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class StructuredRequest(Generic[WireResult])` ([source](../../../../../../src/learnloop/ai/transport.py), line 53) — One validated completion request independent of provider mechanics.
  - `model_type(self) -> type[WireResult]` (line 88; public) — Compatibility spelling for callers that describe a Pydantic type.
  - `wire_model(self) -> type[WireResult]` (line 94; public) — Make the request's wire contract explicit at call sites.
- `class OperationClient(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 101) — Common identity/capability surface for structured or legacy operations.
  - `supports(self, capability: str) -> bool` (line 108; public) — Declare optional transport capabilities without method probing.
- `class StructuredTransport(OperationClient, Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 115) — The complete provider protocol for shared structured operations.
  - `complete(self, request: StructuredRequest[WireResult]) -> WireResult` (line 118; public) — Return a response validated as ``request.result_model``.
- `class LegacyOperationTransport(OperationClient, Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 124) — Endpoint adapter that executes only explicitly supported operations.
  - `complete_legacy(self, request: StructuredRequest[WireResult], *, context: object) -> WireResult` (line 127; public) — Execute a feature-owned request over a legacy named endpoint.
  - `consume_usage(self) -> TokenUsage` (line 137; public) — Read and reset accumulated provider-reported usage.
- `class InterruptibleTransport(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 143) — Narrow typed view activated only after the capability check.
  - `interrupt(self) -> Any` (line 146; public)
- `class CapabilityTransport(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 151) — The minimum runtime surface needed for optional capabilities.
  - `supports(self, capability: str) -> bool` (line 154; public)
- `interrupt_callback(transport: object) -> Callable[[], Any] | None` ([source](../../../../../../src/learnloop/ai/transport.py), line 158) — Return the typed interrupt hook when the transport declares support.
- `execute_structured_operation(transport: OperationClient, *, purpose: str, prompt: str, result_model: type[WireResult], timeout_seconds: float | None=None, legacy_capability: str | None=None, legacy_context: object | None=None, workspace: Path | None=None, isolated: bool=False, images: tuple[tuple[str, bytes], ...]=(), check: Callable[[WireResult], WireResult] | None=None) -> WireResult` ([source](../../../../../../src/learnloop/ai/transport.py), line 166) — Execute one feature-owned structured operation.
- `prompt_safe(value: Any) -> Any` ([source](../../../../../../src/learnloop/ai/transport.py), line 282) — Convert an operation context value into bounded JSON prompt data.
- `render_structured_prompt(title: str, prompt_version: str, payload: Mapping[str, Any], *, context_tail_fields: tuple[str, ...]=()) -> str` ([source](../../../../../../src/learnloop/ai/transport.py), line 298) — Render the byte-stable envelope shared by feature-owned operations.

### Module constants

- `STRUCTURED_COMPLETION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 20)
- `BOUNDED_STRUCTURED_COMPLETION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 23)
- `MEDIA_TRANSCRIPTION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 24)
- `MEDIA_MARKDOWN` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 25)
- `INTERRUPT` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 26)
- `EMBEDDING` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 27)
- `READ_ONLY_WORKSPACE` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 35)
- `ISOLATED_TURN` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 40)
- `VIDEO_GENERATION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 42)
- `IMAGE_INPUT` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 46)
- `IMAGE_MEDIA_TYPES` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 48)
- `MAX_IMAGE_BYTES` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 49)

### Explicit exports

`__all__` declares:

- `EMBEDDING`
- `INTERRUPT`
- `ISOLATED_TURN`
- `CapabilityTransport`
- `InterruptibleTransport`
- `LegacyOperationTransport`
- `MEDIA_MARKDOWN`
- `MEDIA_TRANSCRIPTION`
- `OperationClient`
- `READ_ONLY_WORKSPACE`
- `STRUCTURED_COMPLETION`
- `StructuredRequest`
- `StructuredTransport`
- `WireResult`
- `execute_structured_operation`
- `interrupt_callback`
- `prompt_safe`
- `render_structured_prompt`

## Internal implementation anchors

- `_execute_request(transport, request, legacy_context, legacy_capability)` ([source](../../../../../../src/learnloop/ai/transport.py), line 251)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OperationClient`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `INTERRUPT`, `ISOLATED_TURN`, `READ_ONLY_WORKSPACE`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `IMAGE_INPUT`, `ISOLATED_TURN`, `MEDIA_MARKDOWN`, `MEDIA_TRANSCRIPTION`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `EMBEDDING`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `VIDEO_GENERATION`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `EMBEDDING`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `OperationClient`, `STRUCTURED_COMPLETION`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `BOUNDED_STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `VIDEO_GENERATION`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/content/pipeline/ai_contracts|learnloop.content.pipeline.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `INTERRUPT`, `MEDIA_TRANSCRIPTION`, `interrupt_callback`; statically calls `interrupt_callback`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `interrupt_callback`; statically calls `interrupt_callback`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `ISOLATED_TURN`, `STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `ISOLATED_TURN`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `prompt_safe`, `render_structured_prompt`; statically calls `prompt_safe`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `ISOLATED_TURN`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `ISOLATED_TURN`, `READ_ONLY_WORKSPACE`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `OperationClient`, `READ_ONLY_WORKSPACE`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `IMAGE_INPUT`, `ISOLATED_TURN`, `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/followup_run/contract_job|learnloop.followup_run.contract_job]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `BOUNDED_STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `ISOLATED_TURN`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `STRUCTURED_COMPLETION`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/projects/ai_contracts|learnloop.projects.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `ISOLATED_TURN`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `execute_structured_operation`, `render_structured_prompt`; statically calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../scripts/benchmark_chatgpt_plan_latency.py); calls `execute_structured_operation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `background_model_work_active`, `generation_ceiling`, `model_call`, `output_limit`, `reasoning_effort_request`; calls `background_model_work_active`, `generation_ceiling`, `model_call`, `output_limit`, `reasoning_effort_request`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/structured_contracts|learnloop.ai.structured_contracts]] — imports `correction_in_flight`; calls `correction_in_flight`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsage`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]], [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] and 108 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/ad_fakes.py](../../../../../../tests/ad_fakes.py) — direct import
- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/diagnosis_fakes.py](../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/e0_fakes.py](../../../../../../tests/e0_fakes.py) — direct import
- [tests/facet_identity_fakes.py](../../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/figure_fixtures.py](../../../../../../tests/figure_fixtures.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/hint_outcome_helpers.py](../../../../../../tests/hint_outcome_helpers.py) — direct import
- [tests/http_provider_double.py](../../../../../../tests/http_provider_double.py) — direct import
- [tests/notes_fixtures.py](../../../../../../tests/notes_fixtures.py) — direct import
- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/reader_active_reading_helpers.py](../../../../../../tests/reader_active_reading_helpers.py) — direct import
- [tests/reader_digest_narrative_helpers.py](../../../../../../tests/reader_digest_narrative_helpers.py) — direct import
- [tests/reader_passage_check_helpers.py](../../../../../../tests/reader_passage_check_helpers.py) — direct import
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/structured_contracts_helpers.py](../../../../../../tests/structured_contracts_helpers.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
- [tests/test_ai_single_request.py](../../../../../../tests/test_ai_single_request.py) — direct import
- [tests/test_authoring_create_ids.py](../../../../../../tests/test_authoring_create_ids.py) — direct import
  - `test_plan_repair_tells_the_model_the_python_validation_error`
- [tests/test_build_wait_detail.py](../../../../../../tests/test_build_wait_detail.py) — direct import
- [tests/test_chat_total_transport_deadline.py](../../../../../../tests/test_chat_total_transport_deadline.py) — direct import
  - `test_f2_rereview_a_prompt_upload_in_partial_sends_completes_unchanged`
  - `test_f2_rereview_partial_sends_inside_one_write_are_bounded_by_the_total_deadline`
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
- [tests/test_chatgpt_plan_deadline.py](../../../../../../tests/test_chatgpt_plan_deadline.py) — direct import
  - `test_background_flag_is_explicit_scoped_and_inherited_by_inventory_workers`
  - `test_endless_background_stream_hits_ceiling_without_job_retry`
  - `test_idle_cut_retries_once_and_records_failed_state`
  - `test_job_host_stops_long_background_stream`
- [tests/test_chatgpt_plan_deadline_socket.py](../../../../../../tests/test_chatgpt_plan_deadline_socket.py) — direct import
  - `test_background_blocked_read_wakes_on_idle_or_interrupt`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_capabilities_isolated_tool_free_and_bounded`
- [tests/test_chatgpt_plan_runaway.py](../../../../../../tests/test_chatgpt_plan_runaway.py) — direct import
  - `test_an_omitted_required_key_still_gets_one_schema_repair`
  - `test_every_try_runs_away_then_job_stays_failed`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_the_plan_serves_a_workspace_and_takes_the_callers_deadline`
- [tests/test_diagnose_review_spend.py](../../../../../../tests/test_diagnose_review_spend.py) — direct import
  - `test_a_json_repair_is_a_second_admitted_request_on_a_metered_route`
  - `test_admitted_repairs_are_charged_and_capped_by_the_admitted_output`
  - `test_subscription_requests_still_stop_on_cancellation`
  - `test_subscription_routes_have_no_physical_request_bound`
  - `test_the_call_count_cap_still_stops_subscription_work`
  - `test_the_route_allowance_is_enforced_when_the_profile_sets_no_limit`
  - `test_transport_retries_are_admitted_too`
- [tests/test_diagnosis_history_modes.py](../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_snapshot_is_unavailable_without_the_capability`
- [tests/test_diagnosis_replay.py](../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_replay_makes_zero_model_and_embedding_calls`
- [tests/test_e0_review_round2.py](../../../../../../tests/test_e0_review_round2.py) — direct import
- [tests/test_figure_region.py](../../../../../../tests/test_figure_region.py) — direct import
  - `test_an_image_request_is_refused_by_a_transport_that_cannot_read_images`
  - `test_the_openai_chat_transport_sends_image_parts_only_for_an_image_profile`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_a_provider_that_cannot_isolate_the_turn_is_refused_before_any_request`
- [tests/test_figure_rich_job_golden.py](../../../../../../tests/test_figure_rich_job_golden.py) — direct import
- [tests/test_figures_final_round.py](../../../../../../tests/test_figures_final_round.py) — direct import
- [tests/test_first_questions_arrive.py](../../../../../../tests/test_first_questions_arrive.py) — direct import
  - `test_the_plan_route_request_is_byte_identical_under_a_ceiling`
  - `test_the_plan_route_states_the_working_size_and_a_chat_route_is_capped_at_the_ceiling`
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_kill_switch_restores_the_pre_t5_request`
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_reader_drain_client_routes_via_canonical_ingest`
- [tests/test_ingest_ownership.py](../../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_replaced_attempt_interrupts_only_its_own_transport`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_public_import_inventory_dependency_resolves_extraction_and_units`
  - `test_same_vault_rebind_preserves_kill_codex_interrupt_handle`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_retry_policy_records_each_failed_request_with_unknown_usage`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_switched_off_the_narrative_prompt_is_todays_exactly`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
- [tests/test_one_ai_ok.py](../../../../../../tests/test_one_ai_ok.py) — direct import
  - `test_a_fallback_provider_is_held_to_the_same_ok`
  - `test_jobs_wait_for_the_ok_and_saying_it_resumes_each_once`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_extended_method_repairs_invalid_json_once`
  - `test_openai_chat_transport_runs_extended_requests`
- [tests/test_openrouter_video_client.py](../../../../../../tests/test_openrouter_video_client.py) — direct import
  - `test_submit_posts_model_prompt_and_options_with_bearer`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_a_profile_maximum_is_never_exceeded_by_the_retry`
  - `test_a_route_effort_reaches_openrouter_as_reasoning_effort`
  - `test_a_second_truncation_fails_and_is_never_accepted`
  - `test_an_admitting_caller_lets_the_transport_retry_a_truncation_at_double`
  - `test_an_owner_set_budget_is_never_exceeded_and_its_truncation_is_logged`
  - `test_inside_a_caller_budget_the_transport_leaves_the_retry_to_the_caller`
  - `test_slice1_review_spend_admits_the_transports_truncation_retry_at_double`
  - `test_the_route_effort_wins_over_a_profile_that_disables_thinking`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_plan_call_that_fails_for_availability_offers_openrouter_for_that_route`
  - `test_admission_equals_wire_and_every_body_keeps_the_grammar`
  - `test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input`
  - `test_the_stage_changes_transport_selection_only`
- [tests/test_practice_index_paid.py](../../../../../../tests/test_practice_index_paid.py) — direct import
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_chat_complete_and_declared_media_capabilities_share_one_contract`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_switch_off_keeps_the_lessons_prompt_and_turn_schema_without_the_visuals_paragraph`
- [tests/test_reading_hardening_review_fixes.py](../../../../../../tests/test_reading_hardening_review_fixes.py) — direct import
  - `test_f1_kill_codex_interrupts_nothing_when_its_settle_fails`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
- [tests/test_structured_contracts.py](../../../../../../tests/test_structured_contracts.py) — direct import
  - `test_a_send_that_skips_the_check_still_cannot_get_a_bad_answer_accepted`
  - `test_the_chat_providers_repair_is_separate_from_the_contract_recovery`
  - `test_without_a_contract_an_operation_and_its_receipt_are_as_before`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_a_joint_stuck_reading_survives_rebuild_with_no_model_call`
  - `test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_a_transport_that_cannot_isolate_the_turn_is_refused_before_any_call`
  - `test_llm_prepare_dry_run_then_fake_codex_then_cache_only_replay`
  - `test_the_t8_alias_and_the_v2_llm_arm_are_one_arm_paid_for_once`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_switch_off_keeps_the_lesson_without_the_episode_paragraph`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f2_rereview_a_transport_retry_is_refused_when_the_failed_attempt_used_the_room`
  - `test_f2_rereview_every_physical_attempt_is_admitted_retries_and_repairs_included`
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import
- [tests/workbench_help_fakes.py](../../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
