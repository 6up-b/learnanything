---
title: "learnloop.ai.routing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/routing.py"
source_paths:
  - "src/learnloop/ai/routing.py"
source_commit: "61a3174ae5b08fa15e51e7c348e88ddc91c9504b"
source_commit_timestamp: "2026-11-01T18:37:05-05:00"
source_worktree_state: "clean"
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
  - "learnloop.ai.routing module"
  - "src/learnloop/ai/routing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.routing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.routing` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Provider selection and the single AI client composition root.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py) |
| Source lines | 877 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `61a3174ae5b08fa15e51e7c348e88ddc91c9504b` |
| Commit timestamp | `2026-11-01T18:37:05-05:00` |

## Public API

- `class AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 318)
- `class ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 325) — Typed outcome of provider selection, readiness, fallback, and build.
  - `ready(self) -> bool` (line 343; public)
  - `__iter__(self) -> Iterator[Any]` (line 346; internal)
- `provider_for_task(config: LearnLoopConfig, task: AITask, *, explicit_provider: str | None=None, allow_env: bool=True) -> AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 352) — Select a configured name with explicit > environment > route precedence.
- `route_names(value: Any) -> list[str]` ([source](../../../../../../src/learnloop/ai/routing.py), line 419) — The profile names one route value names: a single profile or a list route.
- `provider_list_for_task(config: LearnLoopConfig, task: AITask, *, allow_env: bool=True) -> list[AIProviderSelection]` ([source](../../../../../../src/learnloop/ai/routing.py), line 425) — Every configured profile of a list route, in order, duplicates removed.
- `provider_for_operation(config: LearnLoopConfig, operation: str, *, explicit_provider: str | None=None, allow_env: bool=True) -> AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 448)
- `fallback_provider_for(config: LearnLoopConfig, selection: AIProviderSelection) -> str | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 467) — The configured readiness fallback for ``selection``, or ``None``.
- `configured_fallback(config: LearnLoopConfig, primary: str | None) -> str | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 481) — ``ai.fallback_provider`` as a fallback for ``primary``, or ``None`` when it may not be one.
- `is_plan_profile(config: LearnLoopConfig, provider_name: str | None) -> bool` ([source](../../../../../../src/learnloop/ai/routing.py), line 508) — Whether ``provider_name`` is a ChatGPT-plan (``chatgpt_plan``) profile.
- `route_profile_mismatch(config: LearnLoopConfig, provider_name: str, task: AITask | None) -> str | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 515) — Why ``provider_name`` cannot serve ``task``, or ``None`` when it can.
- `is_embedding_profile(config: LearnLoopConfig, provider_name: str) -> bool` ([source](../../../../../../src/learnloop/ai/routing.py), line 564)
- `is_decider_profile(config: LearnLoopConfig, provider_name: str) -> bool` ([source](../../../../../../src/learnloop/ai/routing.py), line 569)
- `serves_read_only_workspace(config: LearnLoopConfig, provider_name: str | None) -> bool` ([source](../../../../../../src/learnloop/ai/routing.py), line 574) — Whether the profile ``provider_name`` can serve a read-only workspace (by its type).
- `is_generation_profile(config: LearnLoopConfig, provider_name: str) -> bool` ([source](../../../../../../src/learnloop/ai/routing.py), line 581) — Whether a configured name can serve a chat/generation route.
- `runtime_for_provider(vault_root: Path, config: LearnLoopConfig, provider_name: str, *, task: AITask | None=None) -> AIRuntimeReport` ([source](../../../../../../src/learnloop/ai/routing.py), line 595) — Return one provider-neutral readiness report for any configured name.
- `client_for_provider(vault_root: Path, config: LearnLoopConfig, provider_name: str, *, timeout_seconds: int | None=None, task: AITask | None=None) -> Any | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 627) — Build a configured provider client, returning no client for manual mode.
- `ready_client_for_task(vault_root: Path, config: LearnLoopConfig, task: AITask, *, explicit: str | None=None, allow_env: bool=True, timeout_seconds: int | None=None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 661) — Resolve selection, readiness, fallback, and construction exactly once.

### Module constants

- `MANUAL_PROVIDER` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 22)
- `EMBEDDING_PROFILE_TYPE` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 23)
- `WORKSPACE_PROFILE_TYPES` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 29)
- `TURN_DEADLINE_PROFILE_TYPES` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 32)
- `DECIDER_TASKS` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 159)
- `DECIDER_ACCEPTING_TASKS` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 168)
- `ROUTE_FOR_OPERATION` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 173)
- `LIST_ROUTE_TASKS` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 408)

### Explicit exports

`__all__` declares:

- `DECIDER_ACCEPTING_TASKS`
- `DECIDER_TASKS`
- `EMBEDDING_PROFILE_TYPE`
- `MANUAL_PROVIDER`
- `LIST_ROUTE_TASKS`
- `ROUTE_FOR_OPERATION`
- `AIProviderSelection`
- `AITask`
- `ResolvedClient`
- `TURN_DEADLINE_PROFILE_TYPES`
- `WORKSPACE_PROFILE_TYPES`
- `client_for_provider`
- `configured_fallback`
- `fallback_provider_for`
- `is_decider_profile`
- `is_plan_profile`
- `is_embedding_profile`
- `is_generation_profile`
- `provider_for_operation`
- `provider_for_task`
- `provider_list_for_task`
- `route_names`
- `ready_client_for_task`
- `route_profile_mismatch`
- `runtime_for_provider`
- `serves_read_only_workspace`

## Internal implementation anchors

- `_route_list(value: Any) -> list[str]` ([source](../../../../../../src/learnloop/ai/routing.py), line 411)
- `_plan_unavailable(vault_root: Path, config: LearnLoopConfig, selection: AIProviderSelection, primary: ResolvedClient, *, task: AITask, timeout_seconds: int | None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 727) — The plan cannot serve ``task``: ask about OpenRouter, or use it when the learner chose so.
- `_resolve_selected_provider(vault_root: Path, config: LearnLoopConfig, selection: AIProviderSelection, provider_name: str, *, task: AITask, timeout_seconds: int | None, fallback_from: str | None=None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 786)
- `_manual_resolution(selection: AIProviderSelection, *, fallback_from: str | None=None, message: str='Manual mode selected; AI is disabled for this workflow.') -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 827)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `route_names`; statically calls `route_names`
- [[Reference/Modules/learnloop/ai/disclosures|learnloop.ai.disclosures]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `AITask`, `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `client_for_provider`, `route_profile_mismatch`, `runtime_for_provider`; statically calls `client_for_provider`, `route_profile_mismatch`, `runtime_for_provider`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `client_for_provider`, `is_generation_profile`, `runtime_for_provider`, `serves_read_only_workspace`; statically calls `client_for_provider`, `is_generation_profile`, `runtime_for_provider`, `serves_read_only_workspace`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `MANUAL_PROVIDER`, `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `WORKSPACE_PROFILE_TYPES`, `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `provider_for_task`, `ready_client_for_task`, `route_profile_mismatch`, `runtime_for_provider`; statically calls `provider_for_task`, `ready_client_for_task`, `route_profile_mismatch`, `runtime_for_provider`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; statically calls `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `module`, `ready_client_for_task`; statically calls `is_decider_profile`, `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `is_plan_profile`, `ready_client_for_task`; statically calls `is_plan_profile`, `ready_client_for_task`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `MANUAL_PROVIDER`, `configured_fallback`, `is_decider_profile`, `is_generation_profile`, `ready_client_for_task`; statically calls `configured_fallback`, `is_decider_profile`, `is_generation_profile`, `ready_client_for_task`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; statically calls `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `client_for_provider`; statically calls `client_for_provider`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `runtime_for_provider`; statically calls `runtime_for_provider`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `provider_for_task`, `provider_list_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `provider_list_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `MANUAL_PROVIDER`, `is_plan_profile`; statically calls `is_plan_profile`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `ready_client_for_task`, `runtime_for_provider`; statically calls `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `AITask`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `AIProviderSelection`, `AITask`, `MANUAL_PROVIDER`, `fallback_provider_for`, `is_plan_profile`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; statically calls `fallback_provider_for`, `is_plan_profile`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `MANUAL_PROVIDER`, `provider_for_task`, `runtime_for_provider`; statically calls `provider_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `is_embedding_profile`, `is_generation_profile`, `provider_for_task`, `ready_client_for_task`, `route_names`, `runtime_for_provider`; statically calls `is_embedding_profile`, `is_generation_profile`, `provider_for_task`, `ready_client_for_task`, `route_names`, `runtime_for_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `MANUAL_PROVIDER`, `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`; statically calls `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `provider_for_task`; statically calls `provider_for_task`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `is_generation_profile`, `runtime_for_provider`; statically calls `is_generation_profile`, `runtime_for_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `provider_for_task`; statically calls `provider_for_task`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `harness_refusal`, `is_agent_harness_profile`; calls `harness_refusal`, `is_agent_harness_profile`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `make_ai_provider_client`; calls `make_ai_provider_client`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `is_granted`, `note_plan_route`, `note_unavailable`, `offer_blocker`, `offer_profile`, `offer_sentence`, `offers_suppressed`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`, `check_ai_runtime`; calls `AIRuntimeReport`, `check_ai_runtime`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_PLAN_PROFILE_TYPE`, `DECIDER_PROFILE_TYPE`, `DEFAULT_DECIDER_PROVIDER`, `DEFAULT_EMBEDDING_PROVIDER`, `VOYAGE_CONTEXTUAL_PROFILE_TYPE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]], [[Reference/Modules/learnloop/ai/disclosures|learnloop.ai.disclosures]], [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] and 53 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_ads_routes_are_in_the_plan_first_table`
  - `test_under_code_defaults_each_ad_route_is_the_plan_and_codex_is_refused`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_zero_model_calls`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_recommendations_never_act`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_replay_reads_receipts_zero_model_calls`
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_each_request_carries_the_output_budget_its_estimate_reports`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_paused_plan_never_falls_back_to_codex`
  - `test_the_plan_serves_a_workspace_and_takes_the_callers_deadline`
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_ii_compare_scope_and_the_scope_resolver_are_separate_routes`
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_nothing_in_tier1_reads_the_deleted_route_check`
- [tests/test_embedding_route_isolation.py](../../../../../../tests/test_embedding_route_isolation.py) — direct import
  - `test_direct_provider_resolution_defaults_to_generation`
  - `test_embedding_profile_primary_falls_back_to_a_generation_provider`
  - `test_generation_never_resolves_an_embedding_profile`
  - `test_master_switch_is_enforced_where_the_client_is_obtained`
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_a_decider_profile_may_serve_the_facet_identity_judge_route_only`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_unset_pf_routes_fall_back_to_active`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_field_paid_routes_are_explicit_not_global`
  - `test_retired_numeric_probability_route_loads_with_a_deprecation_note`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_no_code_path_can_store_or_render_verified_or_checked`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_decider_profiles_never_serve_other_work`
  - `test_decider_readiness_is_key_presence_without_network`
  - `test_decider_routes_are_explicit_ignore_the_env_and_never_fall_back`
  - `test_llm_routes_are_ordinary_chat_routes`
  - `test_profiles_come_from_code_defaults_for_configs_that_predate_them`
  - `test_the_llm_judge_runs_on_the_subscription_route_by_default`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_custom_key_and_endpoint`
  - `test_embedding_route_defaults_but_a_vault_that_never_enables_embeddings_sends_nothing`
  - `test_explicit_embedding_route_never_uses_env_active_or_fallback`
  - `test_readiness_factory_and_authoritative_embedding_model`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_list_routes_resolve_in_order_and_fall_back_to_the_active_provider`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
  - `test_a_plan_call_that_fails_for_availability_offers_openrouter_for_that_route`
  - `test_every_fallback_provider_and_env_override_never_resolves_to_codex`
  - `test_every_routing_value_for_every_task_never_resolves_to_codex`
  - `test_every_task_under_code_defaults_resolves_tool_free_and_never_codex`
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f2_openrouter_is_offered_only_when_the_feature_could_use_it`
  - `test_f4_grants_are_per_vault_per_offer_and_the_env_grant_is_the_cli_commands_only`
  - `test_f6_codex_is_never_a_fallback_through_the_direct_readers_opt_in_or_not`
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_fix_l2_a_quiet_status_read_never_points_at_an_offer_it_did_not_make`
  - `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant`
  - `test_the_cli_json_carries_the_hint`
  - `test_the_opt_in_admits_codex_and_codex_is_still_never_a_fallback`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
  - `test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_grant_counts_only_in_the_learners_request_or_a_job_carrying_it`
  - `test_a_manual_fallback_is_never_replaced_by_a_grant`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p2_a_relayed_offer_keeps_the_jobs_starting_method`
  - `test_p3_a_batch_asks_on_its_own_and_its_answer_tokens_it`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
  - `test_m1_every_relay_path_keeps_its_units_vault_and_epoch`
  - `test_m2_a_batch_resumed_after_a_restart_asks_again_as_its_origin`
  - `test_m3_any_response_that_reports_a_batch_shows_its_offer_once`
- [tests/test_plan_first_transport_paid_roles.py](../../../../../../tests/test_plan_first_transport_paid_roles.py) — direct import
  - `test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first`
  - `test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter`
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_project_route_defaults_to_grading_then_active`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_composition_root_uses_fallback_and_preserves_requested_selection`
  - `test_config_matrix_executes_all_six_production_resolution_paths`
  - `test_explicit_and_environment_selections_suppress_fallback`
  - `test_manual_is_a_typed_no_client_outcome`
  - `test_operation_routes_include_semantic_diagnostic_grading`
  - `test_provider_resolution_config_matrix_is_uniform`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_an_unready_route_is_never_a_chat_fallback`
- [tests/test_recurrence_merge_composition.py](../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_a_codex_route_that_is_not_ready_skips_the_judge_and_leaves_the_backlog`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_the_deciders_route_never_resolves_to_a_chat_model`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_every_ai_task_refuses_the_fallback_profile`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
