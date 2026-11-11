---
title: "learnloop.ai.runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/runtime.py"
source_paths:
  - "src/learnloop/ai/runtime.py"
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
  - "learnloop.ai.runtime module"
  - "src/learnloop/ai/runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps runtime behavior inside its owning package, [[Reference/Modules/learnloop/ai/_package|learnloop.ai]]. Its public surface centers on `legacy_codex_status`, `OpenAIChatHealthcheck`, `AIRuntimeReport`, `check_ai_runtime`.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/runtime.py](../../../../../../src/learnloop/ai/runtime.py) |
| Source lines | 218 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `legacy_codex_status(status: str) -> str` ([source](../../../../../../src/learnloop/ai/runtime.py), line 27) — Translate a neutral runtime state at a legacy Codex-facing boundary.
- `class OpenAIChatHealthcheck(Protocol)` ([source](../../../../../../src/learnloop/ai/runtime.py), line 38)
  - `__call__(self, profile: AIProviderConfig) -> None` (line 39; internal)
- `class AIRuntimeReport` ([source](../../../../../../src/learnloop/ai/runtime.py), line 44)
  - `ready(self) -> bool` (line 59; public)
  - `actual_revision(self) -> str | None` (line 63; public)
  - `as_dict(self) -> dict[str, str | bool | None]` (line 66; public)
- `check_ai_runtime(vault_root: Path, config: LearnLoopConfig, *, provider_name: str | None=None, openai_chat_healthcheck: OpenAIChatHealthcheck | None=None) -> AIRuntimeReport` ([source](../../../../../../src/learnloop/ai/runtime.py), line 81)

### Module constants

- `_CODEX_COMPAT_STATUS` ([src/learnloop/ai/runtime.py](../../../../../../src/learnloop/ai/runtime.py), line 19)
- `_CHATGPT_PLAN_STATES` ([src/learnloop/ai/runtime.py](../../../../../../src/learnloop/ai/runtime.py), line 188)

## Internal implementation anchors

- `_chatgpt_plan_runtime(selected: str, profile: AIProviderConfig) -> AIRuntimeReport` ([source](../../../../../../src/learnloop/ai/runtime.py), line 198) — Local files only: the profile, the machine's sign-in and its pause state.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AIRuntimeReport`, `check_ai_runtime`; statically calls `AIRuntimeReport`, `check_ai_runtime`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AIRuntimeReport`, `legacy_codex_status`; statically calls `legacy_codex_status`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `legacy_codex_status`; statically calls `legacy_codex_status`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `check_ai_runtime`; statically calls `check_ai_runtime`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `check_ai_runtime`; statically calls `check_ai_runtime`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `check_ai_runtime`; statically calls `check_ai_runtime`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `harness_refusal`; calls `harness_refusal`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `resolved_decider_settings`; calls `resolved_decider_settings`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/http_provider_double.py](../../../../../../tests/http_provider_double.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_ai_runtime.py](../../../../../../tests/test_ai_runtime.py) — direct import
  - `test_ai_runtime_reports_missing_provider`
  - `test_openai_chat_runtime_ready_with_api_key`
  - `test_openai_chat_runtime_requires_api_key`
  - `test_openai_chat_runtime_uses_vault_dotenv`
  - `test_openrouter_runtime_defaults_to_openrouter_key_env`
  - `test_openrouter_runtime_ready_with_api_key`
  - `test_openrouter_runtime_requires_api_key`
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — direct import
  - `test_attempt_ai_flow_records_provider_model_and_ai_source`
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_readiness_reads_local_state_only`
  - `test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back`
- [tests/test_codex_attempt_flow.py](../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_attempt_orchestration_falls_back_when_runtime_not_ready`
- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_ai_regrade_records_provider_and_ai_origin`
  - `test_deferred_regrade_skips_when_runtime_not_ready`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_a_committed_joint_grade_carries_its_receipt_and_grading_record`
  - `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`
  - `test_c3_k1_leaves_no_sample_support_on_the_stored_attribution`
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_status_reports_readiness_without_probing_a_runtime`
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_readiness_factory_and_authoritative_embedding_model`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_readiness_of_a_codex_profile_is_the_refusal`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
  - `test_provider_resolution_config_matrix_is_uniform`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — direct import
  - `test_committed_model_grade_is_not_regraded_when_a_later_step_fails`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/runtime.py](../../../../../../src/learnloop/ai/runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
