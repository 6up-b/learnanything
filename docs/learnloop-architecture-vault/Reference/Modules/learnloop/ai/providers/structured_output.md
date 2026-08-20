---
title: "learnloop.ai.providers.structured_output"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/structured_output.py"
source_paths:
  - "src/learnloop/ai/providers/structured_output.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.providers.structured_output module"
  - "src/learnloop/ai/providers/structured_output.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.structured_output`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.structured_output` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: Provider-side repair prompts for malformed structured output.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/structured_output.py](../../../../../../../src/learnloop/ai/providers/structured_output.py) |
| Source lines | 47 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `structured_output_repair_prompt(text: str, model_type: type[BaseModel], *, reason: str='') -> str` ([source](../../../../../../../src/learnloop/ai/providers/structured_output.py), line 12) — Build the bounded second pass used after wire validation fails.
- `structured_output_regeneration_prompt(prompt: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/structured_output.py), line 35) — Retry a turn whose malformed JSON was rejected inside app-server.

### Explicit exports

`__all__` declares:

- `structured_output_regeneration_prompt`
- `structured_output_repair_prompt`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `structured_output_regeneration_prompt`, `structured_output_repair_prompt`; statically calls `structured_output_regeneration_prompt`, `structured_output_repair_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ai_config.py](../../../../../../../tests/test_ai_config.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_codex_attempt_flow.py](../../../../../../../tests/test_codex_attempt_flow.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_codex_http_client.py](../../../../../../../tests/test_codex_http_client.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_codex_runtime.py](../../../../../../../tests/test_codex_runtime.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_deferred_regrade.py](../../../../../../../tests/test_deferred_regrade.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_e2e_codex_mock.py](../../../../../../../tests/test_e2e_codex_mock.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]
- [tests/test_teach_back.py](../../../../../../../tests/test_teach_back.py) — imports consumer [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]]

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/structured_output.py](../../../../../../../src/learnloop/ai/providers/structured_output.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
