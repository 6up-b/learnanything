---
title: "learnloop.daily_plan.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/records.py"
source_paths:
  - "src/learnloop/daily_plan/records.py"
source_commit: "0e7320843be3da31fd4eb62d04eadd3794d27e25"
source_commit_timestamp: "2026-11-01T01:03:41-04:00"
source_worktree_state: "clean"
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
  - "learnloop.daily_plan.records module"
  - "src/learnloop/daily_plan/records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.records` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: A daily plan as persisted: ``daily_plans`` + its blocks + their event receipts.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py) |
| Source lines | 515 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0e7320843be3da31fd4eb62d04eadd3794d27e25` |
| Commit timestamp | `2026-11-01T01:03:41-04:00` |

## Public API

- `class PlannedItem` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 39)
  - `displaced(self) -> bool` (line 74; public)
  - `done(self) -> bool` (line 78; public)
  - `skipped(self) -> bool` (line 82; public)
  - `resolved(self) -> bool` (line 86; public)
  - `state(self) -> str` (line 90; public)
- `class PlannedBlock` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 121)
  - `is_reading(self) -> bool` (line 153; public)
  - `withdrawn_path_reading(self) -> bool` (line 157; public) — A path reading taken back unread (RW7b F1): a path switch turned off, or curriculum C1's fresh choice moved the plan's reading, before it was read.
  - `deferred_followups(self) -> set[str]` (line 164; public) — Follow-ups the restraint let wait for the next block (R2c).
  - `reading_target(self) -> ReadingTarget | None` (line 170; public)
  - `est_minutes(self) -> float` (line 183; public)
  - `finished(self) -> bool` (line 191; public)
  - `next_item(self) -> PlannedItem | None` (line 198; public) — The block's next item to serve: a served-but-unanswered item first (resume), then mid-plan follow-ups, then planned order.
- `class PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 215)
  - `stops(self) -> list[PlannedBlock]` (line 224; public)
  - `id(self) -> str` (line 228; public)
  - `kind(self) -> str` (line 232; public)
  - `status(self) -> str` (line 236; public)
  - `is_open(self) -> bool` (line 240; public)
  - `budget(self) -> float` (line 244; public)
  - `split(self) -> dict[str, Any]` (line 248; public)
  - `admission(self) -> dict[str, Any]` (line 252; public)
  - `lanes_allowed(self) -> tuple[str, ...]` (line 256; public)
  - `items(self) -> list[PlannedItem]` (line 260; public)
  - `active_items(self) -> list[PlannedItem]` (line 263; public)
  - `minutes_planned(self) -> float` (line 266; public)
  - `minutes_left(self) -> float` (line 269; public)
  - `current_block(self) -> PlannedBlock | None` (line 272; public)
  - `next_ordinal(self) -> int` (line 278; public)
  - `refused_followups(self) -> set[str]` (line 281; public) — Follow-ups a hard constraint refused in this plan (R2c): never placed again in it.
  - `planned_ids(self) -> set[str]` (line 288; public) — Items this plan has taken (displaced items go back to the pool).
  - `ad_deferrals(self) -> dict[str, dict[str, Any]]` (line 293; public) — Adaptive difficulty's active deferrals (spec §6.1 step 0), folded from the plan's own events: an item displaced with ``ad_ineligible`` joins, a later boundary that re-read its checks and cleared it (``block_chosen`` detail ``ad_deferrals.cleared``) releases it.
  - `exclusion_ids(self) -> set[str]` (line 311; public) — What a pool source never offers this plan whatever the switches say: its planned and skipped items.
  - `item_count(self) -> int` (line 322; public)
  - `ledger(self) -> tuple[dict[str, float], dict[str, float]]` (line 325; public) — (allotment, spent) per lane, §6.2 / §6.8 rule 1.
  - `lane_left(self) -> dict[str, float]` (line 382; public)
- `assemble(plan_rows: Sequence[Mapping[str, Any]], block_rows: Sequence[Mapping[str, Any]], event_rows: Sequence[Mapping[str, Any]]) -> list[PlanRecord]` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 387) — Fold persisted rows into records (events in ordinal order).
- `day_items(records: Iterable[PlanRecord]) -> list[PlannedItem]` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 494)

### Module constants

- `_EPS` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 18)
- `ORIGIN_CHOOSER` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 21)
- `ORIGIN_REQUESTED` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 22)
- `ORIGIN_FOLLOWUP` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 23)
- `ORIGIN_LEARNER_PICK` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 24)
- `LANE_ORIGINS` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 27)
- `AD_INELIGIBLE` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 30)
- `RECEIPT_STOP` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 34)
- `RECEIPT_OPEN_LIST_PICK` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 35)
- `READING_PATH_OFF` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 106)
- `DELIVERABLE_PATH_OFF` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 113)
- `DELIVERABLE_PATH_MOVED` ([src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py), line 117)

### Explicit exports

`__all__` declares:

- `AD_INELIGIBLE`
- `LANE_ORIGINS`
- `ORIGIN_CHOOSER`
- `ORIGIN_FOLLOWUP`
- `ORIGIN_LEARNER_PICK`
- `ORIGIN_REQUESTED`
- `PlanRecord`
- `DELIVERABLE_PATH_OFF`
- `DELIVERABLE_PATH_MOVED`
- `READING_PATH_OFF`
- `RECEIPT_OPEN_LIST_PICK`
- `RECEIPT_STOP`
- `PlannedBlock`
- `PlannedItem`
- `assemble`
- `day_items`

## Internal implementation anchors

- `_apply_event(block: PlannedBlock, by_item: dict[str, PlannedItem], event: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 427)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `AD_INELIGIBLE`, `DELIVERABLE_PATH_MOVED`, `DELIVERABLE_PATH_OFF`, `ORIGIN_CHOOSER`, `ORIGIN_FOLLOWUP`, `ORIGIN_LEARNER_PICK`, `ORIGIN_REQUESTED`, `PlanRecord`, `PlannedBlock`, `PlannedItem`, `READING_PATH_OFF`, `RECEIPT_OPEN_LIST_PICK`, `RECEIPT_STOP`, `assemble`; statically calls `PlanRecord`, `PlannedBlock`, `PlannedItem`, `assemble`
- [[Reference/Modules/learnloop/daily_plan/report|learnloop.daily_plan.report]] — imports `PlanRecord`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `PlanRecord`, `PlannedBlock`, `PlannedItem`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `LANES`, `ReadingTarget`; calls `ReadingTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/report|learnloop.daily_plan.report]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f10_a_pick_after_the_plan_closed_is_recorded`

## Modification guidance

- Make changes here when the responsibility remains records within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
