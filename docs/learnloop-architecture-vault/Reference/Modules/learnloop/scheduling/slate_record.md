---
title: "learnloop.scheduling.slate_record"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/slate_record.py"
source_paths:
  - "src/learnloop/scheduling/slate_record.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.slate_record module"
  - "src/learnloop/scheduling/slate_record.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.slate_record`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.slate_record` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: The slate's decision record (ADR-017): what a queue build put first, what it ranked below, and what never reached it.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py) |
| Source lines | 274 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `by_rule(exclusions: Mapping[str, Iterable[str]], *, ids_per_rule: int=IDS_PER_RULE) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 62) — ``{rule: {"n": count, "ids": [the first ids, sorted]}}``, plus ``unnamed`` for ids a record cannot carry.
- `merged_exclusions(withheld: Mapping[str, Iterable[str]], *, greedy_ids: Sequence[str], considered_ids: Sequence[str], teach_back_rule: str, cold_deferrals: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 78) — Every item the build kept off the slate, by rule: the candidate loop's, then the composition's and the cold lane's.
- `head_rule(head: Any | None, *, pinned_item_id: str | None, check_item_ids: Iterable[str], greedy_head_id: str | None) -> str` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 104) — The rule that put ``head`` (a ``ScheduledItem``) first.
- `slate_record(*, served: Sequence[Any], considered: Sequence[Any], greedy: Sequence[Any], exclusions: Mapping[str, Iterable[str]], placement_check_exclusions: Mapping[str, Iterable[str]], propensity: Mapping[str, float], limit: int | None, slate_id: str | None, session_id: str | None, pinned_item_id: str | None, check_item_ids: Iterable[str], probe_block_reason: str | None, algorithm_version: str, selection_policy: str) -> DecisionRecord` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 134) — The ``slate`` record of one build.
- `item_outcome(record: DecisionRecord, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 219) — What one slate record says about one item: ``chosen``, the rule it lost or was excluded by, or None.
- `record_slate(repository: Any, *, withheld: Mapping[str, Iterable[str]], teach_back_value: bool, cold_deferrals: Iterable[Mapping[str, Any]], **inputs: Any) -> str | None` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 238) — Build and write the slate's record; its id, or ``None``.

### Module constants

- `LOG` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 25)
- `KIND` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 27)
- `SUBJECT_KIND` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 28)
- `DETAIL_TABLE` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 29)
- `IDS_PER_RULE` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 34)
- `ALTERNATIVES_WITH_SLATE_ROW` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 41)
- `RULE_EMPTY` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 44)
- `RULE_PIN` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 45)
- `RULE_FOLLOWUP` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 46)
- `RULE_CHECK` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 47)
- `RULE_EXPLORATION` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 48)
- `RULE_GREEDY` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 49)
- `RULE_COMPOSITION` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 50)
- `LOST_RANKED_BELOW` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 53)
- `LOST_BEYOND_LIMIT` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 54)
- `COLD_FOLLOWUP_DEFERRED` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 57)
- `TEACH_BACK_SESSION_CAP` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 58)
- `TEACH_BACK_VALUE` ([src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py), line 59)

### Explicit exports

`__all__` declares:

- `IDS_PER_RULE`
- `KIND`
- `by_rule`
- `head_rule`
- `item_outcome`
- `merged_exclusions`
- `record_slate`
- `slate_record`

## Internal implementation anchors

- `_number(value: Any) -> float | None` ([source](../../../../../../src/learnloop/scheduling/slate_record.py), line 126)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `KIND`, `item_outcome`; statically calls `item_outcome`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `TEACH_BACK_SESSION_CAP`, `TEACH_BACK_VALUE`, `merged_exclusions`, `record_slate`; statically calls `merged_exclusions`, `record_slate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; calls `write_decision`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `current_trace`, `is_code`; calls `DecisionRecord`, `current_trace`, `is_code`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provenance.py](../../../../../../tests/test_provenance.py) — direct import
  - `test_a_rebuild_never_calls_the_record_and_keeps_its_rows`
- [tests/test_slate_record.py](../../../../../../tests/test_slate_record.py) — direct import
  - `test_a_placement_check_records_why_its_lo_items_were_not_candidates`
  - `test_a_recorded_slate_keeps_ten_alternatives_and_counts_the_rest`
  - `test_exclusions_are_counted_by_rule_with_ten_ids_each`
  - `test_the_composition_and_the_cold_lane_are_exclusions_too`
  - `test_the_rule_that_put_the_head_first`

## Modification guidance

- Change slate record policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/slate_record.py](../../../../../../src/learnloop/scheduling/slate_record.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
