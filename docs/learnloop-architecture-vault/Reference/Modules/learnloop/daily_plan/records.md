---
title: "learnloop.daily_plan.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/records.py"
source_paths:
  - "src/learnloop/daily_plan/records.py"
source_commit: "workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65"
source_commit_timestamp: "2026-11-09T12:16:08-05:00"
source_worktree_state: "modified"
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
| Source lines | 564 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD c8ed55f10b84fdce46fada919c39e9004aabff65` |
| Commit timestamp | `2026-11-09T12:16:08-05:00` |

## Public API

- `class PlannedItem` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 39)
  - `displaced(self) -> bool` (line 74; public)
  - `done(self) -> bool` (line 78; public)
  - `skipped(self) -> bool` (line 82; public)
  - `resolved(self) -> bool` (line 86; public)
  - `state(self) -> str` (line 90; public)
- `class PlannedBlock` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 121)
  - `is_reading(self) -> bool` (line 153; public)
  - `is_lesson_offer(self) -> bool` (line 157; public) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the block is a lesson offer's card (no items, no reading); it ends with the learner's answer (or ``ignored``).
  - `interrupts(self) -> bool` (line 164; public) — IH2 (spec_instruct_handoff_v1 §5 item 3): a lesson offer drawn after a miss with questions left in the block below it: it comes first while it is open, and the block resumes after its answer.
  - `followups_lost(self) -> tuple[str, ...]` (line 171; public) — IH2: the follow-ups this offer's draw beat: they wait while it is open, then a later decision has them.
  - `withdrawn_path_reading(self) -> bool` (line 179; public) — A path reading taken back unread (RW7b F1): a path switch turned off, or curriculum C1's fresh choice moved the plan's reading, before it was read.
  - `deferred_followups(self) -> set[str]` (line 186; public) — Follow-ups the restraint let wait for the next block (R2c).
  - `reading_target(self) -> ReadingTarget | None` (line 192; public)
  - `est_minutes(self) -> float` (line 205; public)
  - `finished(self) -> bool` (line 217; public)
  - `next_item(self) -> PlannedItem | None` (line 224; public) — The block's next item to serve: a served-but-unanswered item first (resume), then mid-plan follow-ups, then planned order.
- `class PlanRecord` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 241)
  - `stops(self) -> list[PlannedBlock]` (line 250; public)
  - `id(self) -> str` (line 254; public)
  - `kind(self) -> str` (line 258; public)
  - `status(self) -> str` (line 262; public)
  - `is_open(self) -> bool` (line 266; public)
  - `budget(self) -> float` (line 270; public)
  - `split(self) -> dict[str, Any]` (line 274; public)
  - `admission(self) -> dict[str, Any]` (line 278; public)
  - `lanes_allowed(self) -> tuple[str, ...]` (line 282; public)
  - `items(self) -> list[PlannedItem]` (line 286; public)
  - `active_items(self) -> list[PlannedItem]` (line 289; public)
  - `minutes_planned(self) -> float` (line 292; public)
  - `minutes_left(self) -> float` (line 295; public)
  - `current_block(self) -> PlannedBlock | None` (line 298; public)
  - `block_below_offer(self) -> PlannedBlock | None` (line 308; public) — IH2: the unfinished block an open offer interrupted, or None.
  - `followups_lost_to_open_offer(self) -> set[str]` (line 314; public) — IH2: what an unanswered offer's draw beat.
  - `open_lesson_offer(self) -> PlannedBlock | None` (line 319; public)
  - `open_lesson_offers(self) -> list[PlannedBlock]` (line 322; public) — Every unanswered offer's block.
  - `next_ordinal(self) -> int` (line 327; public)
  - `refused_followups(self) -> set[str]` (line 330; public) — Follow-ups a hard constraint refused in this plan (R2c): never placed again in it.
  - `planned_ids(self) -> set[str]` (line 337; public) — Items this plan has taken (displaced items go back to the pool).
  - `ad_deferrals(self) -> dict[str, dict[str, Any]]` (line 342; public) — Adaptive difficulty's active deferrals (spec §6.1 step 0), folded from the plan's own events: an item displaced with ``ad_ineligible`` joins, a later boundary that re-read its checks and cleared it (``block_chosen`` detail ``ad_deferrals.cleared``) releases it.
  - `exclusion_ids(self) -> set[str]` (line 360; public) — What a pool source never offers this plan whatever the switches say: its planned and skipped items.
  - `item_count(self) -> int` (line 371; public)
  - `ledger(self) -> tuple[dict[str, float], dict[str, float]]` (line 374; public) — (allotment, spent) per lane, §6.2 / §6.8 rule 1.
  - `lane_left(self) -> dict[str, float]` (line 431; public)
- `assemble(plan_rows: Sequence[Mapping[str, Any]], block_rows: Sequence[Mapping[str, Any]], event_rows: Sequence[Mapping[str, Any]]) -> list[PlanRecord]` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 436) — Fold persisted rows into records (events in ordinal order).
- `day_items(records: Iterable[PlanRecord]) -> list[PlannedItem]` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 543)

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

- `_apply_event(block: PlannedBlock, by_item: dict[str, PlannedItem], event: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/daily_plan/records.py), line 476)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `AD_INELIGIBLE`, `DELIVERABLE_PATH_MOVED`, `DELIVERABLE_PATH_OFF`, `ORIGIN_CHOOSER`, `ORIGIN_FOLLOWUP`, `ORIGIN_LEARNER_PICK`, `ORIGIN_REQUESTED`, `PlanRecord`, `PlannedBlock`, `PlannedItem`, `READING_PATH_OFF`, `RECEIPT_OPEN_LIST_PICK`, `RECEIPT_STOP`, `assemble`; statically calls `PlanRecord`, `PlannedBlock`, `PlannedItem`, `assemble`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `ORIGIN_LEARNER_PICK`
- [[Reference/Modules/learnloop/daily_plan/report|learnloop.daily_plan.report]] — imports `PlanRecord`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `PlanRecord`, `PlannedBlock`, `PlannedItem`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `assemble`; statically calls `assemble`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `LANES`, `LESSON_OFFER_SUBTYPE`, `ReadingTarget`; calls `ReadingTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/report|learnloop.daily_plan.report]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_block_chooser_interface.py](../../../../../../tests/test_block_chooser_interface.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f10_a_pick_after_the_plan_closed_is_recorded`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v1_the_open_items_are_the_plan_records_own`

## Modification guidance

- Make changes here when the responsibility remains records within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/records.py](../../../../../../src/learnloop/daily_plan/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
