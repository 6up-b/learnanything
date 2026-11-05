---
title: "learnloop.router_objective_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective_switches.py"
source_paths:
  - "src/learnloop/router_objective_switches.py"
source_commit: "eff30f881a7d3ea5b06e0a10156b37049285cf52"
source_commit_timestamp: "2026-11-04T20:48:34-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective_switches module"
  - "src/learnloop/router_objective_switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.router_objective_switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective_switches` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Router objective RO1's switches and the availability time (spec_router_objective_v1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) |
| Source lines | 149 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `eff30f881a7d3ea5b06e0a10156b37049285cf52` |
| Commit timestamp | `2026-11-04T20:48:34-05:00` |

## Public API

- `interval_factor_removed(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 47) — §5.1: True when the FSRS interval carries no surprise factor (the tag and the switch).
- `available_at_reads_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 55) — §5.3: True when decision-time attempt reads use the availability time.
- `self_report_not_validated_on(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 62) — §5.4: True when a learner's pick is not counted as validated evidence.
- `available_at(row: Mapping[str, Any]) -> str | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 69) — ``coalesce(received_at, created_at)``: when the attempt became known to the system.
- `attempt_time_sql(config: Any, connection: Any=None, *, alias: str | None=None) -> str` ([source](../../../../../src/learnloop/router_objective_switches.py), line 82) — THE availability predicate's SQL form: the expression a decision-time read of ``practice_attempts`` compares its time cutoff with (``<expr> < ?``, ``<expr> <= ?``).
- `known_at(row: Mapping[str, Any], config: Any) -> str | None` ([source](../../../../../src/learnloop/router_objective_switches.py), line 104) — THE availability predicate over a loaded ``practice_attempts`` row: the time a decision-time cutoff compares with.
- `validated_resolution_ids(ids: Iterable[Any], config: Any) -> list[Any]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 119) — The resolution ids that count as validated evidence: all of them below the tag or with the switch off; otherwise all but a learner's own reports (§5.4).
- `projection_switches(config: Any) -> dict[str, bool]` ([source](../../../../../src/learnloop/router_objective_switches.py), line 129) — What a whole-vault rebuild derived persisted due dates under (§5.5): whether the factor was removed.

### Module constants

- `LEARNER_REPORT_PREFIX` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 28)
- `AVAILABLE_AT_SQL` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 31)
- `RECEIVED_AT_RECORDED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 35)
- `RECEIVED_AT_INFERRED` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 36)
- `INTERVAL_FACTOR_SNAPSHOT_KEY` ([src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py), line 39)

### Explicit exports

`__all__` declares:

- `AVAILABLE_AT_SQL`
- `INTERVAL_FACTOR_SNAPSHOT_KEY`
- `LEARNER_REPORT_PREFIX`
- `RECEIVED_AT_INFERRED`
- `RECEIVED_AT_RECORDED`
- `attempt_time_sql`
- `available_at`
- `available_at_reads_on`
- `interval_factor_removed`
- `known_at`
- `projection_switches`
- `self_report_not_validated_on`
- `validated_resolution_ids`

## Internal implementation anchors

- `_at_tag(config: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 42)
- `_has_received_at(connection: Any) -> bool` ([source](../../../../../src/learnloop/router_objective_switches.py), line 115)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `known_at`; statically calls `known_at`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `interval_factor_removed`; statically calls `interval_factor_removed`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `attempt_time_sql`, `known_at`, `validated_resolution_ids`; statically calls `attempt_time_sql`, `known_at`, `validated_resolution_ids`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `attempt_time_sql`; statically calls `attempt_time_sql`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `projection_switches`; statically calls `projection_switches`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `INTERVAL_FACTOR_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro1_availability.py](../../../../../tests/test_ro1_availability.py) — direct import
  - `test_available_at_is_received_at_else_created_at`
  - `test_exam_seeding_records_the_import_time_and_replay_keeps_it`
  - `test_the_router_cards_decision_time_reads_use_availability_at_the_tag`
- [tests/test_ro1_availability_reads.py](../../../../../tests/test_ro1_availability_reads.py) — direct import
  - `test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off`
- [tests/test_ro1_interval_factor.py](../../../../../tests/test_ro1_interval_factor.py) — direct import
  - `test_the_gate_is_the_tag_and_the_switch`
- [tests/test_ro1_projection.py](../../../../../tests/test_ro1_projection.py) — direct import
  - `test_every_switch_combination_moves_exactly_its_own_part`
  - `test_every_whole_vault_rebuild_records_the_factors_switch`
- [tests/test_ro1_self_report.py](../../../../../tests/test_ro1_self_report.py) — direct import
  - `test_a_probes_observation_still_counts_and_only_reports_are_dropped`
- [tests/test_ro1_successor.py](../../../../../tests/test_ro1_successor.py) — direct import
  - `test_each_switch_is_classified_and_reads_off_or_below_the_tag`

## Modification guidance

- Make changes here when the responsibility remains router objective switches within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective_switches.py](../../../../../src/learnloop/router_objective_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
