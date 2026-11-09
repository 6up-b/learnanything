---
title: "learnloop.daily_plan.admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/admission.py"
source_paths:
  - "src/learnloop/daily_plan/admission.py"
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
  - "learnloop.daily_plan.admission module"
  - "src/learnloop/daily_plan/admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.admission` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: New-material pace (``spec_daily_loop_v1.md`` §6.3, Q11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/admission.py](../../../../../../src/learnloop/daily_plan/admission.py) |
| Source lines | 251 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NewCandidate` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 35)
- `class Admission` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 42)
  - `admitted_ids(self) -> tuple[str, ...]` (line 64; public)
  - `admitted_minutes(self) -> float` (line 68; public)
  - `as_dict(self) -> dict[str, Any]` (line 71; public)
- `class ReviewItem` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 100) — One item with memory state, for the review-load projection.
- `projected_review_load(items: Sequence[ReviewItem], *, now: datetime, horizon_days: int) -> float` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 109) — L: mean daily review minutes over the horizon (§6.3).
- `new_item_daily_cost(est_minutes: float, *, reviews: int, horizon_days: int) -> float` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 138)
- `admit_new_material(candidates: Sequence[NewCandidate], *, review_load_per_day: float, m: float, load_ceiling: float, horizon_days: int, reviews_per_new_item: int, cap_per_day: int, floor_per_day: int, planned_today: int, enabled: bool=True, reentry: bool=False, override: str | None=None, ceiling_basis: str='plan_minutes') -> Admission` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 142) — Admit new material for one plan (or one "more new material" extension).
- `more_new_tradeoff(candidates: Sequence[NewCandidate], *, reviews_per_new_item: int, horizon_days: int) -> float` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 222) — "adds about N min/day of reviews for two weeks" (§6.3).
- `class AdmissionContext` ([source](../../../../../../src/learnloop/daily_plan/admission.py), line 234) — What the engine hands the admission (kept for the plan's receipt).

### Module constants

- `ADMISSION_RULE` ([src/learnloop/daily_plan/admission.py](../../../../../../src/learnloop/daily_plan/admission.py), line 31)

### Explicit exports

`__all__` declares:

- `ADMISSION_RULE`
- `Admission`
- `AdmissionContext`
- `NewCandidate`
- `ReviewItem`
- `admit_new_material`
- `more_new_tradeoff`
- `new_item_daily_cost`
- `projected_review_load`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `new_item_daily_cost`; statically calls `new_item_daily_cost`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `NewCandidate`, `ReviewItem`, `admit_new_material`, `more_new_tradeoff`, `projected_review_load`; statically calls `NewCandidate`, `ReviewItem`, `admit_new_material`, `more_new_tradeoff`, `projected_review_load`
- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `ReviewItem`, `projected_review_load`; statically calls `ReviewItem`, `projected_review_load`
- [[Reference/Modules/learnloop/daily_plan/schedule_effects|learnloop.daily_plan.schedule_effects]] — imports `ReviewItem`, `projected_review_load`; statically calls `projected_review_load`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]], [[Reference/Modules/learnloop/daily_plan/schedule_effects|learnloop.daily_plan.schedule_effects]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_plan_admission.py](../../../../../../tests/test_daily_plan_admission.py) — direct import
  - `test_admission_stops_at_the_load_ceiling`
  - `test_learner_requests_are_exempt_and_take_the_first_slots`
  - `test_more_new_material_bypasses_the_ceiling_and_the_cap_once`
  - `test_review_load_counts_reviews_in_the_horizon`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f5_a_primed_retry_changes_neither_the_cost_preview_nor_the_review_load`
- [tests/test_ro1_upgrade_report.py](../../../../../../tests/test_ro1_upgrade_report.py) — direct import
  - `test_a_primed_retry_after_the_review_is_not_the_intervals_anchor`
  - `test_the_report_counts_the_queue_and_load_admission_counts`

## Modification guidance

- Make changes here when the responsibility remains admission within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/admission.py](../../../../../../src/learnloop/daily_plan/admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
