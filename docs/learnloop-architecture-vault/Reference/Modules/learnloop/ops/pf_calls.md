---
title: "learnloop.ops.pf_calls"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_calls.py"
source_paths:
  - "src/learnloop/ops/pf_calls.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.pf_calls module"
  - "src/learnloop/ops/pf_calls.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_calls`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_calls` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Role-routed, spend-admitted, checkpointed model calls for PF-b (Slice A §5 rule 6).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py) |
| Source lines | 645 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RoleClient` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 104)
- `class PFUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 114) — A route cannot serve its role (unready, unbounded metered transport).
- `role_providers(vault: LoadedVault, role: str, *, tier_routes: list[str] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 127) — The planned provider names for a role, before any client is built.
- `planned_role_clients(vault: LoadedVault, role: str, *, tier_routes: list[str] | None=None) -> list[RoleClient]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 137) — Profile-level view used by dry runs: no client is constructed.
- `resolve_role_clients(vault: LoadedVault, role: str, *, injected: Any | None=None, tier_routes: list[str] | None=None) -> list[RoleClient]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 152) — Pinned, ready clients for a role; ``injected`` replaces them in tests.
- `validate_pricing(price_per_million: float | None, input_price_per_million: float | None, output_price_per_million: float | None) -> None` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 202) — One single-rate price, or the input/output pair, or none.
- `pricing_basis(price_per_million: float | None, input_price_per_million: float | None, output_price_per_million: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 215) — How metered LLM tokens are priced for admission and cap accounting.
- `distinct_models(clients: list[RoleClient]) -> list[str]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 227)
- `class CallResult` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 232)
- `estimate_tokens(prompt: str, result_model: type[BaseModel], output_tokens: int) -> int` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 241)
- `class PFCaller` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 248) — One command's budget, receipts, checkpoints and ledger appends.
  - `__init__(self, vault: LoadedVault, repository: Repository, *, caps: SpendCaps, price_per_million: float | None, run_id: str, owner_kind: str='pf_generation', cancelled: Callable[[], bool] | None=None, input_price_per_million: float | None=None, output_price_per_million: float | None=None) -> None` (line 251; internal)
  - `_upper_rate(self) -> float | None` (line 280; internal) — Per million tokens when the input/output split is unknown.
  - `_price_per_token(self) -> float | None` (line 286; internal)
  - `usd(self, input_tokens: int, output_tokens: int) -> float | None` (line 290; public) — The owner's price for this many input and output tokens (None: unpriced).
  - `pricing(self) -> dict[str, Any]` (line 298; public)
  - `estimate(self, tokens: int, *, subscription: bool, calls: int=1, candidates: int=0, pairs: int=0, retries: int=0, output_tokens: int | None=None) -> SpendEstimate` (line 301; public) — ``tokens`` is input plus output; ``output_tokens`` its output share when known (priced at the output rate), else all at the higher rate.
  - `_shared_used(self, name: str) -> int` (line 316; internal)
  - `check_shared(self, estimate: SpendEstimate) -> None` (line 319; public)
  - `check_plan(self, metered: SpendEstimate, subscription: SpendEstimate) -> None` (line 326; public) — Admit a whole plan before any request (dry-run and pre-run check).
  - `charged(self) -> dict[str, Any]` (line 340; public) — Cap accounting: reservations (input bound plus the full output budget), raised to reported usage, never refunded.
  - `_bill(self, billing: str, event: Mapping[str, Any]) -> None` (line 345; internal)
  - `billed(self) -> dict[str, Any]` (line 351; public) — What the providers reported billing, per class (``provider_reported``).
  - `declared(self) -> dict[str, Any]` (line 372; public)
  - `output_tokens(self, entry: RoleClient) -> int` (line 376; public) — The role's output budget under the shared policy (``ai.output_budget``).
  - `reasoning_effort(self, entry: RoleClient) -> str | None` (line 380; public) — The role's route's requested reasoning effort, or None (the profile's).
  - `input_hash(self, entry: RoleClient, prompt: str, result_model: type[BaseModel], output_tokens: int) -> str` (line 384; public)
  - `call(self, entry: RoleClient, *, prompt: str, prompt_version: str, result_model: type[BaseModel], output_tokens: int | None=None, candidates: int=0, pairs: int=0, retry_invalid_output: bool=True, retry_truncation: bool | None=None) -> CallResult` (line 396; public) — One isolated, tool-free structured turn (never the vault, files or tools).
  - `embed(self, client: Any, texts: list[Any], *, task_prefix: str, price_per_million: float | None, estimated_tokens: int | None=None) -> list[list[float]]` (line 540; public) — One metered embedding request, admitted under the shared caps first.
  - `ledger(self, *, task: str, left_kind: str, left_id: str, judge: str, input_hash: str, verdict: str, right_kind: str | None=None, right_id: str | None=None, judge_model: str | None=None, prompt_version: str | None=None, score: float | None=None, rationale: Mapping[str, Any] | str='', supersede: bool=False) -> str` (line 595; public) — Append once per (task, subjects, judge, input); resumes never duplicate.
  - `report(self) -> dict[str, Any]` (line 626; public)

### Module constants

- `METERED_TYPES` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 67)
- `SCHEMA_ALLOWANCE` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 68)
- `CHECKPOINT_PREFIX` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 69)
- `ISOLATION_BOUNDARY` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 71)
- `ROLE_TASKS` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 74)
- `LIST_ROLES` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 94)
- `TIERED_ROLES` ([src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py), line 99)

### Explicit exports

`__all__` declares:

- `CallResult`
- `ISOLATION_BOUNDARY`
- `LIST_ROLES`
- `METERED_TYPES`
- `PFCaller`
- `PFUnavailable`
- `ROLE_TASKS`
- `RoleClient`
- `TIERED_ROLES`
- `distinct_models`
- `estimate_tokens`
- `planned_role_clients`
- `pricing_basis`
- `resolve_role_clients`
- `role_providers`
- `validate_pricing`

## Internal implementation anchors

- `_profile_settings(vault: LoadedVault, provider: str, model: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 118)
- `_injected_generation_settings(client: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_calls.py), line 197)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `ROLE_TASKS`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `planned_role_clients`, `resolve_role_clients`; statically calls `PFCaller`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `CallResult`, `METERED_TYPES`, `PFCaller`, `PFUnavailable`, `RoleClient`, `estimate_tokens`, `pricing_basis`, `validate_pricing`; statically calls `PFCaller`, `PFUnavailable`, `RoleClient`, `estimate_tokens`, `pricing_basis`, `validate_pricing`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `estimate_tokens`, `planned_role_clients`, `pricing_basis`, `resolve_role_clients`, `validate_pricing`; statically calls `PFCaller`, `PFUnavailable`, `estimate_tokens`, `planned_role_clients`, `pricing_basis`, `resolve_role_clients`, `validate_pricing`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `distinct_models`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`; statically calls `PFCaller`, `distinct_models`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `PFCaller`, `PFUnavailable`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`; statically calls `PFCaller`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `CallResult`, `PFCaller`, `RoleClient`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `PFUnavailable`; statically calls `PFUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `estimate_tokens`; statically calls `estimate_tokens`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `estimate_tokens`; statically calls `estimate_tokens`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`; calls `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`; calls `content_key`, `generation_limit`, `model_settings`, `observe_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `provider_list_for_task`, `ready_client_for_task`; calls `provider_for_task`, `provider_list_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `ISOLATED_TURN`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `decimal`, `json`, `math`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]], [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_benchmarks_helpers.py](../../../../../../tests/recurrence_benchmarks_helpers.py) — direct import
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_the_compare_harness_uses_the_policy_budget_and_retries_a_truncation`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_list_routes_resolve_in_order_and_fall_back_to_the_active_provider`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  - `test_b3_markdown_renders_its_table_on_the_harness`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_register_suites_is_idempotent_and_refuses_a_conflict`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_pf_caller_prices_a_truncation_retry_at_its_doubled_output_budget`
- [tests/test_t6_followup_rereview.py](../../../../../../tests/test_t6_followup_rereview.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_the_compare_harness_never_resends_a_profile_maximum`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains pf calls within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_calls.py](../../../../../../src/learnloop/ops/pf_calls.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
