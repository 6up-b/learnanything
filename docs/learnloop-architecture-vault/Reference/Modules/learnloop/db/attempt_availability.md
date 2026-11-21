---
title: "learnloop.db.attempt_availability"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/attempt_availability.py"
source_paths:
  - "src/learnloop/db/attempt_availability.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.attempt_availability module"
  - "src/learnloop/db/attempt_availability.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.attempt_availability`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.attempt_availability` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Availability and evidence admission for attempt-ledger readers.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py) |
| Source lines | 93 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `available_at_reads_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 30) — §5.3: True when decision-time attempt reads use the availability time.
- `self_report_not_validated_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 37) — §5.4: True when a learner's pick is not counted as validated evidence.
- `available_at(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 44) — ``coalesce(received_at, created_at)``: when the attempt became known to the system.
- `attempt_time_sql(config: Any, *, alias: str | None=None) -> str` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 57) — THE availability predicate's SQL form: the expression a decision-time read of ``practice_attempts`` compares its time cutoff with (``<expr> < ?``, ``<expr> <= ?``).
- `known_at(row: Mapping[str, Any], config: Any) -> str | None` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 76) — THE availability predicate over a loaded ``practice_attempts`` row: the time a decision-time cutoff compares with.
- `validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]` ([source](../../../../../../src/learnloop/db/attempt_availability.py), line 87) — The resolution ids that count as validated evidence: all of them with the switch off; otherwise all but a learner's own reports (§5.4).

### Module constants

- `LEARNER_REPORT_PREFIX` ([src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py), line 19)
- `AVAILABLE_AT_SQL` ([src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py), line 22)
- `RECEIVED_AT_RECORDED` ([src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py), line 26)
- `RECEIVED_AT_INFERRED` ([src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py), line 27)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `known_at`; statically calls `known_at`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/daily_plan/check_inputs|learnloop.daily_plan.check_inputs]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `known_at`; statically calls `known_at`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `attempt_time_sql`, `known_at`, `validated_resolution_ids`; statically calls `attempt_time_sql`, `known_at`, `validated_resolution_ids`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `known_at`; statically calls `known_at`
- [[Reference/Modules/learnloop/teacher/check_delivery|learnloop.teacher.check_delivery]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `attempt_time_sql`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]], [[Reference/Modules/learnloop/daily_plan/check_inputs|learnloop.daily_plan.check_inputs]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
  - `test_available_at_is_received_at_else_created_at`
  - `test_blank_received_at_stores_null_and_agrees_at_cutoffs`
  - `test_exam_seeding_records_the_import_time_and_replay_keeps_it`
  - `test_the_router_cards_decision_time_reads_use_availability_at_the_tag`
- [tests/test_ro1_availability_reads.py](../../../../../../tests/test_ro1_availability_reads.py) — direct import
  - `test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
  - `test_every_switch_combination_moves_exactly_its_own_part`
- [tests/test_ro1_self_report.py](../../../../../../tests/test_ro1_self_report.py) — direct import
  - `test_a_probes_observation_still_counts_and_only_reports_are_dropped`
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_each_switch_is_classified_and_reads_off_or_below_the_tag`
- [tests/test_rofu_learning.py](../../../../../../tests/test_rofu_learning.py) — direct import
  - `test_the_join_rows_count_one_outcome_once_per_protocol_and_only_when_known`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/attempt_availability.py](../../../../../../src/learnloop/db/attempt_availability.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
