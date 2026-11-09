---
title: "learnloop.ai.review_spend"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/review_spend.py"
source_paths:
  - "src/learnloop/ai/review_spend.py"
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
  - "learnloop.ai.review_spend module"
  - "src/learnloop/ai/review_spend.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.review_spend`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.review_spend` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Shared per-route spend admission and usage accounting.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py) |
| Source lines | 445 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `is_subscription_client(client: Any) -> bool` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 59)
- `admitted_output_limit(route: str, profile_max_tokens: Any, config: Any | None=None) -> int` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 63) — The route's output budget under the shared policy (0 for an embedding).
- `class RouteInfo` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 85)
  - `as_dict(self) -> dict[str, Any]` (line 96; public)
- `class CallUsage` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 110)
  - `add(self, event: dict[str, Any]) -> None` (line 118; public)
- `class UsageCollector` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 142) — Observes model calls: admits physical requests, forwards receipts, meters.
  - `__call__(self, action: str, event: dict[str, Any]) -> None` (line 154; internal)
  - `unit(self, *, admit: Callable[[dict[str, Any]], None] | None=None) -> Iterator[_Unit]` (line 186; public)
  - `observing(self) -> Iterator['UsageCollector']` (line 196; public)
- `class AdmittedCall` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 202)
- `class ReviewSpend` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 213) — One budget for the whole run; per-route billing decides what counts.
  - `__init__(self, caps: SpendCaps, *, cancelled: Callable[[], bool] | None=None, price_per_million: float | None=None, config: Any | None=None) -> None` (line 216; internal)
  - `_output_limit(self, route: str, profile_max_tokens: Any) -> int` (line 235; internal)
  - `register(self, route: str, client: Any, *, model_id: str | None=None) -> RouteInfo` (line 238; public)
  - `register_profile(self, route: str, *, provider: str | None, model: str | None, subscription: bool, max_tokens: int | None=None) -> RouteInfo` (line 256; public) — Classify a route from configuration alone (a dry run builds no client).
  - `output_limit(self, route: str) -> int` (line 278; public)
  - `_usd(self, info: RouteInfo, tokens: int) -> float | None` (line 282; internal)
  - `estimate(self, route: str, *, calls: int, input_tokens: int, output_tokens: int, candidates: int=0, pairs: int=0) -> SpendEstimate` (line 287; public)
  - `check(self, estimate: SpendEstimate) -> SpendEstimate` (line 300; public)
  - `request(self, route: str, purpose: str, *, input_tokens: int, output_tokens: int | None=None, retry: bool=False, retry_truncation: bool=True, candidates: int=0, pairs: int=0) -> Iterator[AdmittedCall]` (line 304; public) — Admit one unit of paid work on ``route``, then meter what it used.
  - `_accumulate(self, route: str, info: RouteInfo, usage: CallUsage, input_estimate: int, output_estimate: int) -> None` (line 391; internal)
  - `call_cost(self, route: str, usage: CallUsage, input_estimate: int, output_estimate: int) -> float | None` (line 404; public)
  - `summary(self) -> dict[str, Any]` (line 410; public)

### Module constants

- `SUBSCRIPTION_CLIENT_TYPES` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 37)
- `ESTIMATED_ONLY` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 38)
- `REPORTED` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 39)
- `KNOWN_PRICES_PER_MILLION` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 41)
- `NO_OUTPUT_ROUTES` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 43)
- `OUTPUT_ALLOWANCE` ([src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py), line 50)

### Explicit exports

`__all__` declares:

- `ESTIMATED_ONLY`
- `KNOWN_PRICES_PER_MILLION`
- `OUTPUT_ALLOWANCE`
- `AdmittedCall`
- `CallUsage`
- `ReviewSpend`
- `RouteInfo`
- `UsageCollector`
- `admitted_output_limit`
- `is_subscription_client`

## Internal implementation anchors

- `class _Unit` ([source](../../../../../../src/learnloop/ai/review_spend.py), line 129) — One admitted unit of work and the physical requests seen inside it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `RouteInfo`; statically calls `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `__all__`, `module`
- [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `ReviewSpend`; statically calls `ReviewSpend`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`; calls `generation_limit`, `observe_model_calls`, `truncation_retry_allowed`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCancelled`, `SpendCaps`, `SpendCharge`, `SpendEstimate`; calls `SpendBudget`, `SpendCancelled`, `SpendEstimate`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_OUTPUT_TOKENS`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]], [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]], [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_nothing_in_tier1_reads_the_deleted_route_check`
  - `test_the_decider_requests_no_output_budget_and_a_fallback_route_keeps_the_shared_policy`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_decider_receipt_and_spend_ignore_llm_output_budget`
  - `test_link_judgments`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`
  - `test_route_decision_fallback_and_switch`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/review_spend.py](../../../../../../src/learnloop/ai/review_spend.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
