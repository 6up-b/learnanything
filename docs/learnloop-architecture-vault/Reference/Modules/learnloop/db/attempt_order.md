---
title: "learnloop.db.attempt_order"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/attempt_order.py"
source_paths:
  - "src/learnloop/db/attempt_order.py"
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
  - "learnloop.db.attempt_order module"
  - "src/learnloop/db/attempt_order.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.attempt_order`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.attempt_order` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: The order the attempt ledger folds in, and the boundaries of its prefixes.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py) |
| Source lines | 191 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class AttemptOrder` ([source](../../../../../../src/learnloop/db/attempt_order.py), line 49) — One policy for ordering the attempt ledger, with its SQL and Python forms.
  - `by_sequence(self) -> bool` (line 58; public)
  - `key(self, created_at: Any, attempt_id: Any, sequences: Mapping[str, int]) -> tuple` (line 63; public) — The sort key of one attempt; ``sequences`` maps attempt ids to their sequence (ignored by the legacy policy).
  - `within(self, created_at: Any, attempt_id: Any, bound: Position, sequences: Mapping[str, int], *, inclusive: bool) -> bool` (line 71; public) — Whether the attempt lies before ``bound`` (or, ``inclusive``, at it).
  - `sorted(self, rows: Iterable[_Row], sequences: Mapping[str, int], *, created_at: str='created_at', attempt_id: str='id') -> list[_Row]` (line 81; public) — ``rows`` (mappings) oldest first.
  - `sequence_sql(self, attempt_id: str='practice_attempts.id') -> str` (line 99; public) — The sequence of the attempt whose id column is ``attempt_id`` (qualify it where the query aliases the table), :data:`UNBOUND_SEQUENCE` when it has no row.
  - `order_sql(self, *, created_at: str='created_at', attempt_id: str='practice_attempts.id', descending: bool=False) -> str` (line 109; public) — The ``ORDER BY`` terms, oldest first (or newest first with ``descending``).
  - `before_sql(self, bound: Position, *, created_at: str='created_at', attempt_id: str='practice_attempts.id') -> tuple[str, tuple[Any, ...]]` (line 119; public) — ``(predicate, parameters)``: the attempts strictly before ``bound`` in this order.
- `attempt_order_for_version(algorithm_version: str | None) -> AttemptOrder` ([source](../../../../../../src/learnloop/db/attempt_order.py), line 149) — The order a vault at ``algorithm_version`` folds its ledger in.
- `attempt_order_for(config: Any) -> AttemptOrder` ([source](../../../../../../src/learnloop/db/attempt_order.py), line 157) — The order a vault folds its ledger in, by its config's tag (``algorithm_versions.application_order_on``).
- `application_sequences(connection: Any) -> dict[str, int]` ([source](../../../../../../src/learnloop/db/attempt_order.py), line 168) — Every attempt's sequence, by attempt id (the Python form's map).

### Module constants

- `APPLICATION_ORDER_TABLE` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 33)
- `BASIS_APPLIED` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 35)
- `BASIS_LEGACY_ORDER_UNKNOWN` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 37)
- `UNBOUND_SEQUENCE` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 40)
- `LEGACY_POLICY` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 140)
- `APPLICATION_POLICY` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 141)
- `LEGACY_ORDER` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 144)
- `APPLICATION_ORDER` ([src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py), line 146)

### Explicit exports

`__all__` declares:

- `APPLICATION_ORDER`
- `APPLICATION_ORDER_TABLE`
- `APPLICATION_POLICY`
- `AttemptOrder`
- `BASIS_APPLIED`
- `BASIS_LEGACY_ORDER_UNKNOWN`
- `LEGACY_ORDER`
- `LEGACY_POLICY`
- `Position`
- `UNBOUND_SEQUENCE`
- `application_sequences`
- `attempt_order_for`
- `attempt_order_for_version`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `UNBOUND_SEQUENCE`, `attempt_order_for`; statically calls `attempt_order_for`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `attempt_order_for`; statically calls `attempt_order_for`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `APPLICATION_ORDER_TABLE`, `AttemptOrder`, `BASIS_APPLIED`, `BASIS_LEGACY_ORDER_UNKNOWN`, `LEGACY_ORDER`
- [[Reference/Modules/learnloop/db/stores/facet_projection|learnloop.db.stores.facet_projection]] — imports `AttemptOrder`, `LEGACY_ORDER`
- [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] — imports `AttemptOrder`, `LEGACY_ORDER`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `attempt_order_for`; statically calls `attempt_order_for`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `AttemptOrder`, `LEGACY_ORDER`, `application_sequences`, `attempt_order_for_version`; statically calls `application_sequences`, `attempt_order_for_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `AttemptOrder`, `LEGACY_ORDER`, `application_sequences`, `attempt_order_for_version`; statically calls `application_sequences`, `attempt_order_for_version`
- [[Reference/Modules/learnloop/substrate/family_memory|learnloop.substrate.family_memory]] — imports `AttemptOrder`, `application_sequences`, `attempt_order_for`; statically calls `application_sequences`, `attempt_order_for`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `attempt_order_for`; statically calls `attempt_order_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `APPLICATION_ORDER_VERSIONS`, `application_order_on`; calls `application_order_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]], [[Reference/Modules/learnloop/db/stores/facet_projection|learnloop.db.stores.facet_projection]], [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_order.py](../../../../../../tests/test_attempt_order.py) — direct import
  - `test_a_bound_without_a_row_is_keyed_as_its_rows_are`
  - `test_a_reservation_is_the_next_sequence_and_a_second_one_returns_it`
  - `test_occurrence_time_stays_first`
  - `test_on_a_ledger_with_no_rows_the_application_order_is_the_legacy_order`
  - `test_ranking_legacy_attempts_fills_only_the_unbound_in_the_predecessor_order_after_every_sequence`
  - `test_the_application_order_breaks_ties_by_sequence_and_unbound_rows_last_by_id`
  - `test_the_legacy_boundary_is_the_predecessor_expression_on_every_pair`
  - `test_the_legacy_order_is_created_at_then_id_whatever_the_sequences_say`
  - `test_the_sql_and_python_boundaries_agree_on_every_pair`
- [tests/test_facet_evidence_timeline.py](../../../../../../tests/test_facet_evidence_timeline.py) — direct import
  - `test_bulk_timelines_read_grading_history_once`
- [tests/test_same_second_order.py](../../../../../../tests/test_same_second_order.py) — direct import
  - `test_a_rolled_back_application_leaves_no_reservation_and_its_retry_takes_the_next`
  - `test_at_the_tag_each_live_attempt_reserves_the_next_sequence_in_application_order`
  - `test_distinct_seconds_replay_alike_at_both_tags`
  - `test_the_facet_timeline_walks_the_attempts_in_the_projections_order`
  - `test_the_family_memory_fold_breaks_a_tie_by_the_ledgers_order`
  - `test_the_tag`
  - `test_the_upgrade_ranks_legacy_attempts_in_id_order_then_new_ones_follow_in_application_order`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/attempt_order.py](../../../../../../src/learnloop/db/attempt_order.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
