---
title: "learnloop.ai.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/errors.py"
source_paths:
  - "src/learnloop/ai/errors.py"
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
| Source lines | 35 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AIProviderUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/ai/errors.py), line 4) — The selected provider could not produce a usable completion.
- `class AIInvalidOutput(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/errors.py), line 8) — A provider response failed its declared wire contract after repair.
- `class AIInterrupted(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/errors.py), line 12) — A LearnLoop-owned provider turn was explicitly interrupted.
- `class AITurnTimeout(AIProviderUnavailable, TimeoutError)` ([source](../../../../../../src/learnloop/ai/errors.py), line 16) — A provider turn exceeded its wall-clock deadline.

### Explicit exports

`__all__` declares:

- `AIInterrupted`
- `AIInvalidOutput`
- `AIProviderUnavailable`
- `AITurnTimeout`
- `CodexInterrupted`
- `CodexTurnTimeout`
- `CodexUnavailable`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexInterrupted`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `AIInvalidOutput`, `CodexUnavailable`; statically calls `AIInvalidOutput`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `AIProviderUnavailable`; statically calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CodexUnavailable`; statically calls `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `CodexTurnTimeout`, `CodexUnavailable`
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

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
  - `test_sdk_codex_turn_timeout_interrupts_and_returns`
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_codex_timeout_releases_lease_and_continues_draining`
- [tests/test_multimodal_client.py](../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_missing_key_raises`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_proposal_persistence.py](../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_timed_out_repair_fails_without_persisting_first_pass`
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
