---
title: "learnloop.daily_plan.chooser"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/chooser.py"
source_paths:
  - "src/learnloop/daily_plan/chooser.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.chooser module"
  - "src/learnloop/daily_plan/chooser.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.chooser`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.chooser` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: ``lane_quota_v1``: DL1's deterministic block chooser (``spec_daily_loop_v1.md`` §6.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/chooser.py](../../../../../../src/learnloop/daily_plan/chooser.py) |
| Source lines | 77 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `unspent_share(lane: str, state: PlanState) -> float` ([source](../../../../../../src/learnloop/daily_plan/chooser.py), line 27)
- `class LaneQuotaChooser` ([source](../../../../../../src/learnloop/daily_plan/chooser.py), line 36)
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 39; public)

### Module constants

- `CHOOSER_NAME` ([src/learnloop/daily_plan/chooser.py](../../../../../../src/learnloop/daily_plan/chooser.py), line 24)

### Explicit exports

`__all__` declares:

- `CHOOSER_NAME`
- `LaneQuotaChooser`
- `unspent_share`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `CHOOSER_NAME`, `LaneQuotaChooser`; statically calls `LaneQuotaChooser`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `LaneQuotaChooser`; statically calls `LaneQuotaChooser`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `LaneQuotaChooser`, `unspent_share`; statically calls `unspent_share`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `LaneQuotaChooser`; statically calls `LaneQuotaChooser`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `BlockChoice`, `LANES`, `PlanState`, `STOP_FOR_TODAY`, `STOP_OFFER_MINUTES`; calls `BlockChoice`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
  - `test_lane_quota_prefers_the_largest_unspent_share_then_repair_first`
  - `test_released_minutes_follow_the_flow_on_order`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f3_plan_reads_never_call_the_live_chooser`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f6_the_chooser_takes_the_master_block_first_in_re_entry`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_the_block_chooser_plans_the_best_probe_per_minute_first`

## Modification guidance

- Make changes here when the responsibility remains chooser within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/chooser.py](../../../../../../src/learnloop/daily_plan/chooser.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
