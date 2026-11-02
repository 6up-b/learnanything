---
title: "learnloop.daily_plan.router_runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_runtime.py"
source_paths:
  - "src/learnloop/daily_plan/router_runtime.py"
source_commit: "bf85487372ed056f27d0209e7b8517b8097c8aa0"
source_commit_timestamp: "2026-10-14T11:32:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.daily_plan.router_runtime module"
  - "src/learnloop/daily_plan/router_runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_runtime` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2b/R2c: the models behind the mixture, asked off the hot path.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py) |
| Source lines | 751 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `bf85487372ed056f27d0209e7b8517b8097c8aa0` |
| Commit timestamp | `2026-10-14T11:32:05-04:00` |

## Public API

- `models_disabled() -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 96)
- `class ComponentResult` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 104) — One model's answer to one decision (or why there is none).
  - `summary(self) -> dict[str, Any]` (line 121; public)
- `class Prefetch` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 134) — One decision's model requests, from its first prefetch to its answers.
  - `answered(self, name: str) -> bool` (line 152; public)
  - `complete(self) -> bool` (line 157; public)
  - `remaining(self, now: float) -> float` (line 160; public)
  - `wait(self, timeout: float) -> None` (line 163; public)
  - `results(self) -> dict[str, ComponentResult]` (line 171; public) — Every component's result; one still out is a timeout (its late answer is ignored).
- `class RouteModels` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 192) — The production model source: the vault's ``router_decider`` / ``router_llm`` routes.
  - `__init__(self, *, probe_http: Any=None) -> None` (line 195; internal)
  - `readiness(self, vault: Any) -> dict[str, str | None]` (line 201; public) — ``{component: None (ready) | reason}``; cached for a few seconds per vault.
  - `client(self, vault: Any, name: str, *, timeout_seconds: float) -> Any` (line 229; public)
  - `decider_reachable(self, client: Any) -> tuple[bool, str]` (line 240; public) — Once per process (an hour's cache): the Decider's free endpoint listing.
  - `embedding_client(self, vault: Any) -> Any | None` (line 264; public)
- `receipt_usd(config: Any, row: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 307) — What one router receipt counts against the daily guard: the provider's cost, else its reported tokens at the route's price; nothing for a subscription call.
- `request_estimate_usd(config: Any, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 329) — One physical request's reservation: its input (~4 bytes a token) plus its output room, at the route's price.
- `class SpendRefused(SpendLimitExceeded)` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 348) — The router's daily guard refused a request before it was sent.
- `class RouterSpend` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 383) — The router's daily guard on metered spend (thread- and process-safe).
  - `spent_today(self, repository: Any, config: Any, now_iso: str) -> float` (line 386; public)
  - `metered(self, repository: Any, config: Any, *, owner_kind: str, owner_id: str) -> Iterator[None]` (line 394; public) — Record every model call in this context under ``owner_kind`` / ``owner_id`` and admit each metered physical request against ``router.max_daily_cost_usd``.
- `class RouterRuntime` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 441) — Process-wide router state: the prefetch cache, the model source, the spend guard.
  - `__post_init__(self) -> None` (line 455; internal)
  - `seed_for(self, key: str, decision_id: str) -> str` (line 459; public)
  - `lookup(self, scope: str, key: str) -> Prefetch | None` (line 464; public)
  - `forget(self, scope: str, key: str) -> None` (line 471; public)
  - `start(self, scope: str, key: str, *, kind: str, budget: float, material: dict[str, Any], job: Callable[[Prefetch], None], components: tuple[str, ...]) -> Prefetch` (line 475; public) — Register a decision's requests and start them (once per key).
  - `readiness(self, vault: Any) -> dict[str, str | None]` (line 500; public)
- `default_runtime() -> RouterRuntime` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 523) — The process's runtime (the sidecar's), created on first use.
- `call_decider(runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float, purpose: str=rq.PURPOSE) -> tuple[ComponentResult, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 554) — Ask the Decider one decision's typed questions.
- `call_llm(runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float, purpose: str=rq.PURPOSE) -> tuple[ComponentResult, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 624) — Ask the router LLM one decision's structured question.

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 69)
- `DECIDER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 71)
- `LLM` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 72)
- `COMPONENT_ROUTES` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 73)
- `RECEIPT_OWNER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 74)
- `SUMMARY_RECEIPT_OWNER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 75)
- `GUARDED_OWNERS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 77)
- `LLM_OUTPUT_FLOOR` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 79)
- `MODELS_ENV` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 81)
- `PROBE_TTL_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 82)
- `READINESS_TTL_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 83)
- `EMBEDDING_TIMEOUT_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 85)
- `ANSWERED` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 87)
- `TIMEOUT` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 88)
- `FAILED` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 89)
- `INVALID` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 90)
- `SPEND` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 91)
- `NOT_READY` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 92)
- `UNREACHABLE` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 93)
- `RESERVATION_KEY` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 282)
- `_BYTES_PER_TOKEN` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 284)
- `_DEFAULT` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 519)
- `_DEFAULT_LOCK` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 520)

### Explicit exports

`__all__` declares:

- `ANSWERED`
- `ComponentResult`
- `DECIDER`
- `DecisionPending`
- `FAILED`
- `GUARDED_OWNERS`
- `INVALID`
- `LLM`
- `LLM_OUTPUT_FLOOR`
- `MODELS_ENV`
- `NOT_READY`
- `Prefetch`
- `RECEIPT_OWNER`
- `RouteModels`
- `RouterRuntime`
- `RESERVATION_KEY`
- `RouterSpend`
- `SPEND`
- `SUMMARY_RECEIPT_OWNER`
- `SpendRefused`
- `TIMEOUT`
- `UNREACHABLE`
- `call_decider`
- `call_llm`
- `default_runtime`
- `models_disabled`
- `receipt_usd`
- `request_estimate_usd`

## Internal implementation anchors

- `class _NotReady(Exception)` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 273)
- `_day_start(now_iso: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 287)
- `_price_per_million(config: Any, provider: str | None) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 291)
- `_reserved_usd(budget_json: Any) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 296)
- `class _RouterGate` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 352) — The router's request gate (``ai.execution.RequestGate``): consulted immediately before EACH physical request; it prices the request and hands the estimate to the start-receipt observer on the same thread, which admits and reserves it (:meth:`RouterSpend.metered`).
- `_run_job(job: Callable[[Prefetch], None], entry: Prefetch) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 504)
- `_now_iso() -> str` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 536)
- `_finish(entry: Prefetch, result: ComponentResult) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 542)
- `_ms(started: float) -> int` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 550)
- `_llm_budget(vault: Any, client: Any) -> int` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 618)
- `_accepts_timeout(method: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 706)
- `_supports_isolation(client: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 715)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `default_runtime`; statically calls `default_runtime`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `call_decider`, `call_llm`; statically calls `ComponentResult`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `EMBEDDING_TIMEOUT_SECONDS`, `SpendRefused`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `LLM`, `SUMMARY_RECEIPT_OWNER`, `SpendRefused`, `_supports_isolation`, `default_runtime`; statically calls `_supports_isolation`, `default_runtime`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `models_disabled`; statically calls `models_disabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `request_body`; calls `request_body`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `gate_model_requests`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`; calls `call_labels`, `gate_model_requests`, `generation_limit`, `observe_model_calls`, `requested_reasoning_effort`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `estimate_input_tokens`, `probe_decider_endpoint`; calls `estimate_input_tokens`, `probe_decider_endpoint`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; calls `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`, `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `ISOLATED_TURN`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `DecisionPending`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `seed_for`; calls `seed_for`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `llm_result_model`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `decimal`, `inspect`, `json`, `logging`, `math`, `os`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_replay_never_asks_a_model_and_is_deterministic`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_json_repair_is_admitted_as_its_own_request`
  - `test_a_read_leaves_the_decision_open_and_a_serve_decides_it`
  - `test_the_daily_guard_counts_todays_router_receipts`
  - `test_the_deciders_route_never_resolves_to_a_chat_model`
  - `test_the_test_suite_routes_ask_no_model`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
  - `test_router_embeddings_and_the_source_backfill_each_answer_to_their_own_guard`
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_the_query_embedding_is_admitted_by_the_daily_guard`

## Modification guidance

- Make changes here when the responsibility remains router runtime within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
