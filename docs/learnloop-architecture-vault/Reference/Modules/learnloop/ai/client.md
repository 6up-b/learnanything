---
title: "learnloop.ai.client"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/client.py"
source_paths:
  - "src/learnloop/ai/client.py"
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
  - "learnloop.ai.client module"
  - "src/learnloop/ai/client.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.client`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps client behavior inside its owning package, [[Reference/Modules/learnloop/ai/_package|learnloop.ai]]. Its public surface centers on `make_ai_provider_client`, `make_ai_provider_client_from_profile`, `make_video_generation_client`.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/client.py](../../../../../../src/learnloop/ai/client.py) |
| Source lines | 124 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `make_ai_provider_client(config: LearnLoopConfig, vault_root: Path, *, provider_name: str | None=None, timeout_seconds: int | None=None) -> AIProviderClient` ([source](../../../../../../src/learnloop/ai/client.py), line 18)
- `make_ai_provider_client_from_profile(provider_name: str, profile: AIProviderConfig, vault_root: Path, *, agent_harness_opt_in: bool=False) -> AIProviderClient` ([source](../../../../../../src/learnloop/ai/client.py), line 43) — Build one client for ``profile``: the single AI client factory.
- `make_video_generation_client(config: LearnLoopConfig, vault_root: Path, *, provider_name: str, http: Any=None) -> Any` ([source](../../../../../../src/learnloop/ai/client.py), line 99) — Build the text-to-video client for an OpenRouter profile.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `make_ai_provider_client`; statically calls `make_ai_provider_client`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `make_video_generation_client`; statically calls `make_video_generation_client`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `make_ai_provider_client_from_profile`; statically calls `make_ai_provider_client_from_profile`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `require_harness_opt_in`; calls `require_harness_opt_in`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `ChatGPTPlanProviderClient`; calls `ChatGPTPlanProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexSDKProviderClient`; calls `CodexSDKProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `HttpAdapterProviderClient`; calls `HttpAdapterProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex_lockdown|learnloop.ai.providers.codex_lockdown]] — imports `module`; calls `refuse_legacy_http_transport`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `DeciderProviderClient`; calls `DeciderProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `OpenAIChatProviderClient`; calls `OpenAIChatProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `OpenAIEmbeddingProviderClient`; calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] — imports `OpenRouterProviderClient`; calls `OpenRouterProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] — imports `OpenRouterVideoClient`; calls `OpenRouterVideoClient`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `VoyageContextualClient`; calls `VoyageContextualClient`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_config.py](../../../../../../tests/test_ai_config.py) — direct import
  - `test_global_ai_timeout_is_applied_to_codex_sdk_profiles`
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_placement_receipts_survive_rebuild_with_zero_model_calls`
- [tests/test_codex_lockdown_round2.py](../../../../../../tests/test_codex_lockdown_round2.py) — direct import
  - `test_an_http_profile_is_refused_by_the_lockdown`
- [tests/test_daily_plan_replay.py](../../../../../../tests/test_daily_plan_replay.py) — direct import
  - `test_rebuild_ignores_the_plan_and_calls_no_model`
- [tests/test_embedding_store.py](../../../../../../tests/test_embedding_store.py) — direct import
  - `test_client_agnostic_storage_and_prefix_isolation`
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
  - `test_projection_deterministic_cold_only_no_models_and_undo`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_the_llm_judge_runs_on_the_subscription_route_by_default`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_make_ai_provider_client_dispatches_openrouter`
- [tests/test_openrouter_video_client.py](../../../../../../tests/test_openrouter_video_client.py) — direct import
  - `test_factory_requires_an_openrouter_profile`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_harness_profile_without_the_opt_in_raises_before_any_process`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_rebuild_preserves_dossiers_and_calls_no_model`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_named_codex_profile_identity_survives_provider_construction`
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_router_r2a_serving.py](../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_router_outcomes_v2_replay_twice_with_no_model_call`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/client.py](../../../../../../src/learnloop/ai/client.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
