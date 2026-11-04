---
title: "learnloop.daily_plan.schedule_effects"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/schedule_effects.py"
source_paths:
  - "src/learnloop/daily_plan/schedule_effects.py"
source_commit: "73f023834fc8cb13955f1a4681f90f09db9a5542"
source_commit_timestamp: "2026-11-04T18:44:13-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.daily_plan.schedule_effects module"
  - "src/learnloop/daily_plan/schedule_effects.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.schedule_effects`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.schedule_effects` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: What a schedule change does to serving: the upgrade's report (router objective RO1, spec §5.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/schedule_effects.py](../../../../../../src/learnloop/daily_plan/schedule_effects.py) |
| Source lines | 142 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `73f023834fc8cb13955f1a4681f90f09db9a5542` |
| Commit timestamp | `2026-11-04T18:44:13-05:00` |

## Public API

- `class ServingSchedule` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 31) — What serving reads of the item schedule at one instant (codex review F2, F3).
- `serving_schedule(vault: Any, repository: Any, *, as_of: datetime) -> ServingSchedule` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 45) — Serving's read of ``repository``'s schedule at ``as_of`` (a shadow rebuild's observer).
- `schedule_effects(before: Mapping[tuple[Any, ...], Mapping[str, Any]], after: Mapping[tuple[Any, ...], Mapping[str, Any]], *, as_of: datetime, horizon_days: int, serving_before: ServingSchedule, serving_after: ServingSchedule) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 82) — What a schedule change does to serving, from the two schedule snapshots and serving's reads.

### Module constants

- `_SCHEDULE_ANCHORS` ([src/learnloop/daily_plan/schedule_effects.py](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 27)

### Explicit exports

`__all__` declares:

- `ServingSchedule`
- `schedule_effects`
- `serving_schedule`

## Internal implementation anchors

- `_days(later: datetime, earlier: datetime) -> float` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 59)
- `_spread(values: Sequence[float]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 63)
- `_queue_due(before: ServingSchedule, after: ServingSchedule, as_of: datetime) -> dict[str, int]` ([source](../../../../../../src/learnloop/daily_plan/schedule_effects.py), line 69)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `schedule_effects`, `serving_schedule`; statically calls `schedule_effects`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/admission|learnloop.daily_plan.admission]] — imports `ReviewItem`, `projected_review_load`; calls `projected_review_load`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `review_population`; calls `review_population`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `load_anchors`; calls `load_anchors`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro1_upgrade_report.py](../../../../../../tests/test_ro1_upgrade_report.py) — direct import
  - `test_a_primed_retry_after_the_review_is_not_the_intervals_anchor`
  - `test_serving_reads_the_anchor_past_a_primed_retry_and_a_held_grade`
  - `test_the_observer_reads_the_live_database_read_only_with_commitments`
  - `test_the_report_counts_the_queue_and_load_admission_counts`
  - `test_with_the_factor_kept_the_shadow_reports_no_schedule_change`

## Modification guidance

- Make changes here when the responsibility remains schedule effects within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/schedule_effects.py](../../../../../../src/learnloop/daily_plan/schedule_effects.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
