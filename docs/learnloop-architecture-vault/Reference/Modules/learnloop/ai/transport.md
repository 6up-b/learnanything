---
title: "learnloop.ai.transport"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/transport.py"
source_paths:
  - "src/learnloop/ai/transport.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.transport` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Small provider-neutral transport contract for structured AI work.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py) |
| Source lines | 211 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class StructuredRequest(Generic[WireResult])` ([source](../../../../../../src/learnloop/ai/transport.py), line 24) — One validated completion request independent of provider mechanics.
  - `model_type(self) -> type[WireResult]` (line 39; public) — Compatibility spelling for callers that describe a Pydantic type.
  - `wire_model(self) -> type[WireResult]` (line 45; public) — Make the request's wire contract explicit at call sites.
- `class OperationClient(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 52) — Common identity/capability surface for structured or legacy operations.
  - `supports(self, capability: str) -> bool` (line 59; public) — Declare optional transport capabilities without method probing.
- `class StructuredTransport(OperationClient, Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 66) — The complete provider protocol for shared structured operations.
  - `complete(self, request: StructuredRequest[WireResult]) -> WireResult` (line 69; public) — Return a response validated as ``request.result_model``.
- `class LegacyOperationTransport(OperationClient, Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 75) — Endpoint adapter that executes only explicitly supported operations.
  - `complete_legacy(self, request: StructuredRequest[WireResult], *, context: object) -> WireResult` (line 78; public) — Execute a feature-owned request over a legacy named endpoint.
  - `consume_usage(self) -> TokenUsage` (line 88; public) — Read and reset accumulated provider-reported usage.
- `class InterruptibleTransport(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 94) — Narrow typed view activated only after the capability check.
  - `interrupt(self) -> Any` (line 97; public)
- `class CapabilityTransport(Protocol)` ([source](../../../../../../src/learnloop/ai/transport.py), line 102) — The minimum runtime surface needed for optional capabilities.
  - `supports(self, capability: str) -> bool` (line 105; public)
- `interrupt_callback(transport: object) -> Callable[[], Any] | None` ([source](../../../../../../src/learnloop/ai/transport.py), line 109) — Return the typed interrupt hook when the transport declares support.
- `execute_structured_operation(transport: OperationClient, *, purpose: str, prompt: str, result_model: type[WireResult], timeout_seconds: float | None=None, legacy_capability: str | None=None, legacy_context: object | None=None) -> WireResult` ([source](../../../../../../src/learnloop/ai/transport.py), line 117) — Execute one feature-owned structured operation.
- `prompt_safe(value: Any) -> Any` ([source](../../../../../../src/learnloop/ai/transport.py), line 164) — Convert an operation context value into bounded JSON prompt data.
- `render_structured_prompt(title: str, prompt_version: str, payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/ai/transport.py), line 180) — Render the byte-stable envelope shared by feature-owned operations.

### Module constants

- `STRUCTURED_COMPLETION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 17)
- `MEDIA_TRANSCRIPTION` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 18)
- `MEDIA_MARKDOWN` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 19)
- `INTERRUPT` ([src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py), line 20)

### Explicit exports

`__all__` declares:

- `INTERRUPT`
- `CapabilityTransport`
- `InterruptibleTransport`
- `LegacyOperationTransport`
- `MEDIA_MARKDOWN`
- `MEDIA_TRANSCRIPTION`
- `OperationClient`
- `STRUCTURED_COMPLETION`
- `StructuredRequest`
- `StructuredTransport`
- `WireResult`
- `execute_structured_operation`
- `interrupt_callback`
- `prompt_safe`
- `render_structured_prompt`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OperationClient`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `INTERRUPT`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `StructuredRequest`, `WireResult`, `prompt_safe`; statically calls `prompt_safe`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `MEDIA_MARKDOWN`, `MEDIA_TRANSCRIPTION`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/content/pipeline/ai_contracts|learnloop.content.pipeline.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `INTERRUPT`, `MEDIA_TRANSCRIPTION`, `interrupt_callback`; statically calls `interrupt_callback`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `interrupt_callback`; statically calls `interrupt_callback`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `prompt_safe`, `render_structured_prompt`; statically calls `prompt_safe`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `STRUCTURED_COMPLETION`, `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `StructuredTransport`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `render_structured_prompt`; statically calls `render_structured_prompt`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `OperationClient`, `execute_structured_operation`; statically calls `execute_structured_operation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsage`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] and 33 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_reader_drain_client_routes_via_canonical_ingest`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_public_import_inventory_dependency_resolves_extraction_and_units`
  - `test_same_vault_rebind_preserves_kill_codex_interrupt_handle`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_extended_method_repairs_invalid_json_once`
  - `test_openai_chat_transport_runs_extended_requests`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_chat_complete_and_declared_media_capabilities_share_one_contract`
  - `test_legacy_http_declares_exactly_its_endpoint_operations`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/transport.py](../../../../../../src/learnloop/ai/transport.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
