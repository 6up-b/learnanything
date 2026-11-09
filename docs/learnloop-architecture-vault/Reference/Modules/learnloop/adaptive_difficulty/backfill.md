---
title: "learnloop.adaptive_difficulty.backfill"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/backfill.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/backfill.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.backfill module"
  - "src/learnloop/adaptive_difficulty/backfill.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.backfill`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.backfill` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's owner-run backfills (spec_adaptive_difficulty_v1 §14 AD1, §7.2, §8.2, §5.11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/backfill.py](../../../../../../src/learnloop/adaptive_difficulty/backfill.py) |
| Source lines | 277 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `llm_plan(vault: Any, route_task: str, prompts: list[str], result_model: Any, *, role: str, retries: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 71) — The resolved LLM route's plan through the spend framework: tokens with the output allowance, the billing label, and a refusal when a metered route has no ``adaptive_difficulty.price_per_million``.
- `backfill(vault: Any, repository: Any, *, audit: bool, llm_v1: bool, reading: bool, dry_run: bool, limit: int | None=None, clients: Clients | None=None, decider_factory: Callable[[], Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 198)

### Explicit exports

`__all__` declares:

- `backfill`
- `llm_plan`

## Internal implementation anchors

- `_never_attempted(view: Any, connection: Any) -> list[Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 61) — The visible active items never attempted (read through the backfill's material view).
- `_decider_plan(vault: Any, route_task: str, bodies: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 108) — The Decider's plan: one admitted request per body at its listed input price (no output allowance: the Decider is exempt from the output-budget policy).
- `_metered_usd(*parts: Mapping[str, Any] | None) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 134) — The worst-case metered dollars of the plan's parts (None: one is unpriced).
- `_cap(vault: Any, repository: Any, worst: float | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 151)
- `_audit_plan(vault: Any, pending: list[tuple[Any, str, list[str]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 167)
- `_count(values: Any) -> dict[str, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/backfill.py), line 270)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `backfill`, `llm_plan`; statically calls `backfill`, `llm_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `DECIDER_ROUTE`, `DIMENSIONS`, `FeatureAuditV1`, `LLM_ROUTE`, `_CAPS`, `audit_revision`, `audit_state`, `canonical_audits`, `item_revision`, `llm_prompt`, `question_for`; calls `audit_revision`, `audit_state`, `canonical_audits`, `item_revision`, `llm_prompt`, `question_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `Clients`, `ItemForecastV1`, `LLM_ROUTE`, `_CAPS`, `forecast_item`, `item_prompt`; calls `forecast_item`, `item_prompt`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `sweep`; calls `sweep`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `ad_envelope`; calls `ad_envelope`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_V1`, `feature_audit_enabled`, `outside_forecasters`, `receipts_enabled`; calls `feature_audit_enabled`, `outside_forecasters`, `receipts_enabled`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TRUNCATION_RETRY_FACTOR`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `resolved_decider_settings`; calls `resolved_decider_settings`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `module`; calls `enabled`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_rereview_fixes.py](../../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
  - `test_the_worst_case_plans_the_permitted_truncation_retry`
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_historical_snapshots_of_held_out_material_are_never_audited`
  - `test_the_backfill_dry_run_plans_routes_through_the_spend_framework`
- [tests/test_ad1_fix_round9.py](../../../../../../tests/test_ad1_fix_round9.py) — direct import
  - `test_the_backfill_records_a_stopped_audit_as_failed`
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_a_real_reading_backfill_sweeps_the_history_with_no_model`
- [tests/test_ad1_send_guard.py](../../../../../../tests/test_ad1_send_guard.py) — direct import
  - `test_a_unit_held_out_while_the_backfill_runs_refuses_its_later_forecasts`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_ad1_switches_restore_predecessor`
  - `test_held_out_sentinel_never_reaches_ad_inputs`

## Modification guidance

- Make changes here when the responsibility remains backfill within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/backfill.py](../../../../../../src/learnloop/adaptive_difficulty/backfill.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
