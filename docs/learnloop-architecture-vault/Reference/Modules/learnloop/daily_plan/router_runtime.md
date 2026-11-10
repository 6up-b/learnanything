---
title: "learnloop.daily_plan.router_runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_runtime.py"
source_paths:
  - "src/learnloop/daily_plan/router_runtime.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_runtime` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2b/R2c: the models behind the mixture, asked off the hot path.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py) |
| Source lines | 803 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_disabled() -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 103)
- `class ComponentResult` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 111) — One model's answer to one decision (or why there is none).
  - `summary(self) -> dict[str, Any]` (line 128; public)
- `class Prefetch` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 141) — One decision's model requests, from its first prefetch to its answers.
  - `answered(self, name: str) -> bool` (line 162; public)
  - `complete(self) -> bool` (line 167; public)
  - `remaining(self, now: float) -> float` (line 170; public)
  - `wait(self, timeout: float) -> None` (line 173; public)
  - `results(self) -> dict[str, ComponentResult]` (line 181; public) — Every component's result; one still out is a timeout (its late answer is ignored).
- `class RouteModels` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 202) — The production model source: the vault's ``router_decider`` / ``router_llm`` routes.
  - `__init__(self, *, probe_http: Any=None) -> None` (line 205; internal)
  - `readiness(self, vault: Any) -> dict[str, str | None]` (line 211; public) — ``{component: None (ready) | reason}``; cached for a few seconds per vault.
  - `client(self, vault: Any, name: str, *, timeout_seconds: float) -> Any` (line 239; public)
  - `decider_reachable(self, client: Any) -> tuple[bool, str]` (line 250; public) — Once per process (an hour's cache): the Decider's free endpoint listing.
  - `embedding_client(self, vault: Any) -> Any | None` (line 274; public)
- `receipt_usd(config: Any, row: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 317) — What one router receipt counts against the daily guard: the provider's cost, else its reported tokens at the route's price; nothing for a subscription call.
- `request_estimate_usd(config: Any, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 339) — One physical request's reservation: its input (~4 bytes a token) plus its output room, at the route's price.
- `class SpendRefused(SpendLimitExceeded)` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 358) — The router's daily guard refused a request before it was sent.
- `class RouterSpend` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 393) — The router's daily guard on metered spend (thread- and process-safe).
  - `spent_today(self, repository: Any, config: Any, now_iso: str) -> float` (line 396; public)
  - `metered(self, repository: Any, config: Any, *, owner_kind: str, owner_id: str) -> Iterator[None]` (line 404; public) — Record every model call in this context under ``owner_kind`` / ``owner_id`` and admit each metered physical request against ``router.max_daily_cost_usd``.
- `class RouterRuntime` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 464) — Process-wide router state: the prefetch cache, the model source, the spend guard.
  - `__post_init__(self) -> None` (line 478; internal)
  - `seed_for(self, key: str, decision_id: str) -> str` (line 482; public)
  - `lookup(self, scope: str, key: str) -> Prefetch | None` (line 487; public)
  - `forget(self, scope: str, key: str) -> None` (line 494; public)
  - `start(self, scope: str, key: str, *, kind: str, budget: float, material: dict[str, Any], job: Callable[[Prefetch], None], components: tuple[str, ...]) -> Prefetch` (line 498; public) — Register a decision's requests and start them (once per key).
  - `readiness(self, vault: Any) -> dict[str, str | None]` (line 524; public)
- `default_runtime() -> RouterRuntime` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 547) — The process's runtime (the sidecar's), created on first use.
- `seen(entry: Any, *, may_defer: bool, decided_wall: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 580) — What a decision's record needs from its prefetch that no persisted row carries: the trace that started it and the wall time its answers were taken (``BlockChoice.provenance``).
- `note_failure(exc: BaseException, entry: Any, *, may_defer: bool, waited_ms: int | None, extra: Mapping[str, Mapping[str, Any]] | None=None) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 588) — Hang each model's result summary on a chooser's exception (``boundary_records.FAILURE_NOTE``): the chooser's own record dies with the exception, and ``engine.decide`` falls back to the rule, so this is how the fallback's record still names what the models answered.
- `call_decider(runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float, purpose: str=rq.PURPOSE) -> tuple[ComponentResult, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 605) — Ask the Decider one decision's typed questions.
- `call_llm(runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float, purpose: str=rq.PURPOSE) -> tuple[ComponentResult, Any]` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 675) — Ask the router LLM one decision's structured question.

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 74)
- `DECIDER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 76)
- `LLM` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 77)
- `COMPONENT_ROUTES` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 78)
- `RECEIPT_OWNER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 79)
- `SUMMARY_RECEIPT_OWNER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 80)
- `FOLLOWUP_GENERATION_OWNER` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 82)
- `GUARDED_OWNERS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 84)
- `LLM_OUTPUT_FLOOR` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 86)
- `MODELS_ENV` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 88)
- `PROBE_TTL_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 89)
- `READINESS_TTL_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 90)
- `EMBEDDING_TIMEOUT_SECONDS` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 92)
- `ANSWERED` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 94)
- `TIMEOUT` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 95)
- `FAILED` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 96)
- `INVALID` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 97)
- `SPEND` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 98)
- `NOT_READY` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 99)
- `UNREACHABLE` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 100)
- `RESERVATION_KEY` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 292)
- `_BYTES_PER_TOKEN` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 294)
- `_DEFAULT` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 543)
- `_DEFAULT_LOCK` ([src/learnloop/daily_plan/router_runtime.py](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 544)

### Explicit exports

`__all__` declares:

- `ANSWERED`
- `ComponentResult`
- `DECIDER`
- `DecisionPending`
- `FAILED`
- `FOLLOWUP_GENERATION_OWNER`
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

- `class _NotReady(Exception)` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 283)
- `_day_start(now_iso: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 297)
- `_price_per_million(config: Any, provider: str | None) -> float` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 301)
- `_reserved_usd(budget_json: Any) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 306)
- `class _RouterGate` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 362) — The router's request gate (``ai.execution.RequestGate``): consulted immediately before EACH physical request; it prices the request and hands the estimate to the start-receipt observer on the same thread, which admits and reserves it (:meth:`RouterSpend.metered`).
- `_run_job(job: Callable[[Prefetch], None], entry: Prefetch) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 528)
- `_now_iso() -> str` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 560)
- `_finish(entry: Prefetch, result: ComponentResult) -> None` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 566)
- `_ms(started: float) -> int` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 574)
- `_llm_budget(vault: Any, client: Any) -> int` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 669)
- `_accepts_timeout(method: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 757)
- `_supports_isolation(client: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_runtime.py), line 766)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `FAILED`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `TIMEOUT`, `call_decider`, `call_llm`, `seen`, `wall_now`; statically calls `ComponentResult`, `seen`, `wall_now`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `default_runtime`; statically calls `default_runtime`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `call_decider`, `call_llm`, `note_failure`, `seen`, `wall_now`; statically calls `ComponentResult`, `note_failure`, `seen`, `wall_now`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `EMBEDDING_TIMEOUT_SECONDS`, `SpendRefused`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `LLM`, `SUMMARY_RECEIPT_OWNER`, `SpendRefused`, `_supports_isolation`, `default_runtime`; statically calls `_supports_isolation`, `default_runtime`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `FOLLOWUP_GENERATION_OWNER`, `default_runtime`; statically calls `default_runtime`
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
- [[Reference/Modules/learnloop/daily_plan/boundary_records|learnloop.daily_plan.boundary_records]] — imports `FAILURE_NOTE`, `wall_now`; calls `wall_now`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `DecisionPending`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `current_trace`; calls `current_trace`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `module`; calls `router_spend_record`, `write`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `seed_for`; calls `seed_for`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `llm_result_model`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `decimal`, `inspect`, `json`, `logging`, `math`, `os`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f1_a_failed_generation_keeps_its_reservation`
  - `test_f1_an_in_flight_generation_reserves_against_the_next`
  - `test_f1_generation_receipts_are_in_the_daily_total`
  - `test_f1_generation_spend_refuses_the_routers_own_next_request`
- [tests/test_instruct_handoff_ih0.py](../../../../../../tests/test_instruct_handoff_ih0.py) — direct import
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
- [tests/test_refusal_records.py](../../../../../../tests/test_refusal_records.py) — direct import
  - `test_a_guard_record_that_cannot_be_built_still_refuses`
  - `test_a_refused_router_request_leaves_a_record_though_no_call_row_exists`
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
- [tests/test_rofu_switch_key.py](../../../../../../tests/test_rofu_switch_key.py) — direct import
- [tests/test_router_failure_records.py](../../../../../../tests/test_router_failure_records.py) — direct import
  - `test_the_store_names_the_routers_receipt_owner`
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
