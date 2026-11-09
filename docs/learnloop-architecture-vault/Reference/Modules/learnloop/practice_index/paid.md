---
title: "learnloop.practice_index.paid"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/paid.py"
source_paths:
  - "src/learnloop/practice_index/paid.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.paid module"
  - "src/learnloop/practice_index/paid.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.paid`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.paid` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Paid LLM calls for the practice index, admitted one by one under spend caps.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py) |
| Source lines | 687 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class UnboundedTransport(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 100) — A metered transport that cannot bound its physical requests.
- `transport_problem(route: PaidRoute, client: Any) -> str | None` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 104) — Why ``client`` cannot run this route's paid calls, or None.
- `billing_for(profile_type: str | None) -> Billing` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 120)
- `class PaidRoute` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 125) — The planned route of one paid role; resolved without any network call.
  - `available(self) -> bool` (line 140; public)
  - `as_dict(self) -> dict[str, Any]` (line 143; public)
- `plan_route(vault: LoadedVault, task: AITask, client: Any | None=None) -> PaidRoute` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 147) — The route a paid role will use: an injected client, or ai.routing.<task>.
- `resolve_client(vault: LoadedVault, route: PaidRoute) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 205) — Build the planned route's client, pinned: no silent fallback to another model.
- `planning_repository(paths: VaultPaths, *, dry_run: bool) -> Repository` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 240) — The repository a paid batch command plans with.
- `estimated_call_tokens(prompt: str, result_model: type[BaseModel], output_tokens: int) -> int` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 256) — UTF-8 bytes upper-bound ordinary tokenizer input; output is bounded.
- `class UsageTotals` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 263)
  - `as_dict(self) -> dict[str, Any]` (line 285; public)
- `checkpoint_key(route: PaidRoute, *, purpose: str, prompt: str, result_model: type[BaseModel], output_tokens: int) -> str` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 295) — A paid answer's request identity: purpose, prompt, schema, output budget, provider and model (the identity its destination rows are keyed by).
- `receipt_answer(connection: sqlite3.Connection, route: PaidRoute, *, purpose: str, prompt: str, result_model: type[BaseModel], output_tokens: int, validate: Callable[[Any], Any] | None=None) -> tuple[Any, BaseModel, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 313) — A paid answer left only on its completed receipt, or None.
- `receipt_answers(connection: sqlite3.Connection, *, purpose: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 347) — Every completed root receipt of one paid role that declared a request key (newest first): for roles whose rerun cannot rebuild the request, such as query-writer batches, which a rerun plans differently.
- `class PaidCalls` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 355) — Serial paid calls for one command, under one ``SpendBudget``.
  - `__init__(self, *, route: PaidRoute, budget: SpendBudget, price_per_million: float | None, repository: Repository | None, owner_kind: str, owner_id: str, admit: Callable[[SpendEstimate], None] | None=None)` (line 358; internal)
  - `subscription(self) -> bool` (line 376; public)
  - `estimate(self, tokens: int, *, candidates: int=0, pairs: int=0, calls: int=1, retries: int=0) -> SpendEstimate` (line 379; public) — What the budget is charged before sending ``calls`` calls of ``tokens`` total.
  - `plan(self, token_counts: list[int], *, candidates: int=0, pairs: int=0) -> dict[str, Any]` (line 390; public) — The dry-run view of a whole plan: the budget charge and the estimate.
  - `report(self) -> dict[str, Any]` (line 409; public)
  - `checkpoint_key(self, *, purpose: str, prompt: str, result_model: type[BaseModel], output_tokens: int) -> str` (line 419; public) — The full request identity a paid answer is checkpointed under.
  - `call(self, client: Any, *, purpose: str, prompt: str, result_model: type[BaseModel], output_tokens: int, metadata: Mapping[str, Any], candidates: int=0, pairs: int=0, validate: Callable[[Any], Any] | None=None, context: Mapping[str, Any] | None=None, deadline: float | None=None, request_timeout_seconds: float | None=None, images: tuple[tuple[str, bytes], ...]=(), isolated: bool=False) -> Any` (line 425; public) — One logical call, retried on provider failure within the retry cap.
  - `_retry_allowed(self) -> bool` (line 531; internal) — Whether one more attempt fits the retry caps (this budget's and the caller's).
  - `_recover(self, key: str, result_model: type[BaseModel], validate: Callable[[Any], Any] | None) -> Any` (line 543; internal)
  - `_recover_receipt(self, key: str, *, purpose: str, prompt: str, result_model: type[BaseModel], output_tokens: int, validate: Callable[[Any], Any] | None, context: Mapping[str, Any] | None) -> Any` (line 564; internal) — A paid answer whose receipt committed but whose checkpoint did not.
  - `_checkpoint(self, key: str, purpose: str, result: BaseModel, context: Mapping[str, Any] | None) -> None` (line 589; internal)
  - `_observer(self, metadata: Mapping[str, Any], events: list[dict[str, Any]], request_key: str, context: Mapping[str, Any] | None=None)` (line 600; internal)
  - `_reconcile(self, charge, tokens_estimate: int, events: list[dict[str, Any]]) -> None` (line 640; internal)

### Module constants

- `SUBSCRIPTION_PROFILE_TYPES` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 93)
- `FRAMING_TOKENS` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 95)
- `METERED_REQUESTS_PER_CALL` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 97)
- `_MISSING` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 291)
- `CHECKPOINT_PREFIX` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 292)
- `_UNUSABLE` ([src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py), line 310)

### Explicit exports

`__all__` declares:

- `CHECKPOINT_PREFIX`
- `FRAMING_TOKENS`
- `METERED_REQUESTS_PER_CALL`
- `SUBSCRIPTION_PROFILE_TYPES`
- `PaidCalls`
- `PaidRoute`
- `UnboundedTransport`
- `billing_for`
- `checkpoint_key`
- `estimated_call_tokens`
- `plan_route`
- `planning_repository`
- `receipt_answer`
- `receipt_answers`
- `resolve_client`
- `transport_problem`

## Internal implementation anchors

- `_routed_plan(vault: LoadedVault, task: AITask, selection: AIProviderSelection) -> bool` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 169) — Whether ``selection`` is a routed (not pinned) ChatGPT-plan route.
- `_granted_provider(vault: LoadedVault, task: AITask, selection: AIProviderSelection) -> str | None` ([source](../../../../../../src/learnloop/practice_index/paid.py), line 175) — The OpenRouter profile when the learner chose it for ``task`` and the plan cannot serve, else None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `plan_route`, `resolve_client`; statically calls `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `METERED_REQUESTS_PER_CALL`, `estimated_call_tokens`, `plan_route`; statically calls `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `plan_route`, `resolve_client`; statically calls `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `plan_route`, `resolve_client`; statically calls `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `PaidCalls`; statically calls `PaidCalls`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `planning_repository`; statically calls `planning_repository`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `FRAMING_TOKENS`, `estimated_call_tokens`, `plan_route`; statically calls `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `billing_for`; statically calls `billing_for`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `PaidCalls`, `PaidRoute`, `estimated_call_tokens`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `PaidCalls`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `PaidCalls`, `PaidRoute`, `SUBSCRIPTION_PROFILE_TYPES`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `FRAMING_TOKENS`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `CHECKPOINT_PREFIX`, `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `receipt_answers`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `receipt_answers`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`; statically calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `module`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `estimated_call_tokens`; statically calls `estimated_call_tokens`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `checkpoint_key`, `plan_route`, `receipt_answer`; statically calls `checkpoint_key`, `plan_route`, `receipt_answer`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`, `receipt_answers`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `receipt_answers`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SUBSCRIPTION_PROFILE_TYPES`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `PaidRoute`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`; statically calls `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `plan_route`; statically calls `plan_route`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; statically calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `plan_route`; statically calls `plan_route`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`; calls `AIInvalidOutput`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; calls `content_key`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TRUNCATION_RETRY_FACTOR`, `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `is_granted`, `offer_blocker`, `offer_profile`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AIProviderSelection`, `AITask`, `MANUAL_PROVIDER`, `fallback_provider_for`, `is_plan_profile`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; calls `fallback_provider_for`, `is_plan_profile`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `STRUCTURED_COMPLETION`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `completed_root_receipts`; calls `completed_root_receipts`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `pathlib`, `sqlite3`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] and 43 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
  - `test_the_worst_case_plans_the_permitted_truncation_retry`
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
  - `test_under_code_defaults_each_ad_route_is_the_plan_and_codex_is_refused`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_zero_model_calls`
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_the_route_falls_back_to_the_active_provider_and_an_override_keeps_the_cap`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_billing_class_is_subscription`
- [tests/test_codex_tool_lockdown.py](../../../../../../tests/test_codex_tool_lockdown.py) — direct import
- [tests/test_curriculum_c1_round5_followups.py](../../../../../../tests/test_curriculum_c1_round5_followups.py) — direct import
  - `test_c1_r5_followup_a_the_refresh_resolves_its_route_once_and_judge_sends_on_it`
- [tests/test_e0_review_round5.py](../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_the_service_copies_route_their_source_routes_to_openrouter_haiku`
- [tests/test_label_roles_cli.py](../../../../../../tests/test_label_roles_cli.py) — direct import
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_the_dry_run_bounds_the_live_verification`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_paid_calls_fail_on_a_second_truncation`
  - `test_paid_calls_retry_a_truncation_once_at_double_the_admitted_budget`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_grant_counts_only_in_the_learners_request_or_a_job_carrying_it`
  - `test_the_background_build_launcher_never_uses_the_grant`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p7_rw5b_figures_ask_as_the_rpc_that_asked`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_plan_first_transport_paid_roles.py](../../../../../../tests/test_plan_first_transport_paid_roles.py) — direct import
  - `test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first`
  - `test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_a_receipt_for_another_request_or_an_invalid_answer_is_not_recovered`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_find_dry_run_bounds_the_rerank_pool_the_query_vector_will_fill`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_the_plan_down_means_no_narrative_and_no_other_provider`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_dry_run_estimates_the_runs_own_output_budget_and_retry`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
  - `test_the_unset_t6_routes_follow_the_active_plan_profile`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request`
  - `test_paid_calls_reserve_and_record_the_real_increased_limit`

## Modification guidance

- Make changes here when the responsibility remains paid within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/paid.py](../../../../../../src/learnloop/practice_index/paid.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
