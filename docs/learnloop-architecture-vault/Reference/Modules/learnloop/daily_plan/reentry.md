---
title: "learnloop.daily_plan.reentry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/reentry.py"
source_paths:
  - "src/learnloop/daily_plan/reentry.py"
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
  - "learnloop.daily_plan.reentry module"
  - "src/learnloop/daily_plan/reentry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.reentry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.reentry` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Goal-optional re-entry (``spec_daily_loop_v1.md`` §7, P6, Q13).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/reentry.py](../../../../../../src/learnloop/daily_plan/reentry.py) |
| Source lines | 194 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReentryGap` ([source](../../../../../../src/learnloop/daily_plan/reentry.py), line 33)
- `reentry_gap(repository: Any, *, now: datetime, threshold_days: int, stale_open_before: str | None=None) -> ReentryGap` ([source](../../../../../../src/learnloop/daily_plan/reentry.py), line 40) — The break since the last real activity (F1).
- `retrievability(stability: float | None, last_review: str | None, at: datetime, weights: Any) -> float | None` ([source](../../../../../../src/learnloop/daily_plan/reentry.py), line 64)
- `class ReentryPanel` ([source](../../../../../../src/learnloop/daily_plan/reentry.py), line 75)
  - `as_dict(self) -> dict[str, Any]` (line 84; public)
- `reentry_panel(vault: Any, repository: Any, *, now: datetime, gap: ReentryGap, goal: Any | None=None, top_n: int=3, clock: Any | None=None, intent: Any=None) -> ReentryPanel` ([source](../../../../../../src/learnloop/daily_plan/reentry.py), line 95) — Solid and slipped LOs since the last real activity (§7).

### Module constants

- `UNCOMMITTED_RECALL_TARGET` ([src/learnloop/daily_plan/reentry.py](../../../../../../src/learnloop/daily_plan/reentry.py), line 29)

### Explicit exports

`__all__` declares:

- `ReentryGap`
- `ReentryPanel`
- `UNCOMMITTED_RECALL_TARGET`
- `reentry_gap`
- `reentry_panel`
- `retrievability`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `ReentryGap`, `reentry_gap`; statically calls `ReentryGap`, `reentry_gap`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `ReentryGap`, `reentry_panel`; statically calls `ReentryGap`, `reentry_panel`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `reentry_summary`; calls `reentry_summary`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f9_reentry_panel_names_only_what_it_counts`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_committed_los_reach_the_chooser_state_with_their_intent`
  - `test_the_reentry_panel_counts_active_intents_against_their_own_targets`

## Modification guidance

- Make changes here when the responsibility remains reentry within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/reentry.py](../../../../../../src/learnloop/daily_plan/reentry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
