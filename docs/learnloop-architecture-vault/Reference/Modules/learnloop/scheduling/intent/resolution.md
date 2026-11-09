---
title: "learnloop.scheduling.intent.resolution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/resolution.py"
source_paths:
  - "src/learnloop/scheduling/intent/resolution.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling.intent"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.intent.resolution module"
  - "src/learnloop/scheduling/intent/resolution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.resolution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.resolution` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: Resolving an item's intent: the most recent choice wins (spec §5.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/resolution.py](../../../../../../../src/learnloop/scheduling/intent/resolution.py) |
| Source lines | 335 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `snapshot_from_rows(commitment: Mapping[str, Any], versions: Sequence[Mapping[str, Any]], head_targets: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]]) -> CommitmentSnapshot` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 57) — Fold one commitment's rows (versions in order, events in order).
- `load_snapshots(connection: Any) -> list[CommitmentSnapshot]` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 127) — Every commitment that covers items, folded (one bulk read).
- `class ItemIntent` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 163) — An item's (or an LO's) resolved intent.
  - `uncommitted(self) -> bool` (line 178; public)
  - `excluded(self) -> bool` (line 182; public)
  - `tier(self) -> int` (line 186; public) — §6.3 / §7: Master and Learn first, then Keep, then uncommitted; Light touch last (and left out of re-entry and admission).
  - `as_dict(self) -> dict[str, Any]` (line 200; public)
- `uncommitted_intent(targets: Mapping[str, float]) -> ItemIntent` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 212)
- `class Resolution` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 221) — §5.3 over a set of commitment snapshots.
  - `__init__(self, snapshots: Iterable[CommitmentSnapshot], targets: Mapping[str, float]) -> None` (line 224; internal)
  - `empty(self) -> bool` (line 241; public)
  - `target_for(self, snapshot: CommitmentSnapshot) -> float` (line 244; public)
  - `covering(self, item_id: str, learning_object_id: str | None) -> list[tuple[CommitmentSnapshot, str]]` (line 247; public) — Covering commitments with the level each covers the item at.
  - `_order_key(self, pair: tuple[CommitmentSnapshot, str]) -> tuple[Any, ...]` (line 261; internal)
  - `_resolve(self, covering: list[tuple[CommitmentSnapshot, str]]) -> ItemIntent` (line 271; internal)
  - `for_item(self, item_id: str, learning_object_id: str | None) -> ItemIntent` (line 295; public)
  - `for_learning_object(self, learning_object_id: str) -> ItemIntent` (line 298; public) — An LO's own intent: the commitments that target the LO itself.
  - `committed_item_ids(self) -> frozenset[str]` (line 303; public)
  - `committed_learning_object_ids(self) -> frozenset[str]` (line 306; public)
  - `with_snapshot(self, snapshot: CommitmentSnapshot) -> 'Resolution'` (line 309; public) — The resolution if ``snapshot`` were added (or replaced): the control's preview uses the very rule the queue uses (§5.2).
- `intent_control_commitments(snapshots: Iterable[CommitmentSnapshot]) -> list[CommitmentSnapshot]` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 317)
- `rechosen(snapshot: CommitmentSnapshot, *, at: str, row_id: str, **changes: Any) -> CommitmentSnapshot` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 321) — A snapshot as if chosen again at ``at`` (the preview's virtual choice).

### Module constants

- `_DISPOSITIONS` ([src/learnloop/scheduling/intent/resolution.py](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 44)

### Explicit exports

`__all__` declares:

- `ItemIntent`
- `Resolution`
- `intent_control_commitments`
- `load_snapshots`
- `rechosen`
- `snapshot_from_rows`
- `uncommitted_intent`

## Internal implementation anchors

- `_loads(value: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/scheduling/intent/resolution.py), line 47)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `ItemIntent`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `Resolution`, `load_snapshots`; statically calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `ItemIntent`, `Resolution`, `load_snapshots`; statically calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `load_snapshots`; statically calls `load_snapshots`
- [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]] — imports `Resolution`, `load_snapshots`; statically calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `ItemIntent`, `Resolution`, `load_snapshots`; statically calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `load_snapshots`; statically calls `load_snapshots`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `load_snapshots`; statically calls `load_snapshots`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/intent_reads|learnloop.db.stores.intent_reads]] — imports `module`; calls `commitment_tables_present`, `commitments_covering_items`, `events_for`, `head_targets_for`, `versions_for`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `ChoiceStamp`, `CommitmentSnapshot`, `DEADLINE_CHANGE_REASON`, `EXCLUDING_DISPOSITIONS`, `INTENT_CONTROL_VIA`, `TIER_KEEP`, `TIER_LIGHT`, `TIER_PUSH`, `TIER_UNCOMMITTED`, `choice_for`; calls `ChoiceStamp`, `CommitmentSnapshot`, `choice_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]], [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]], [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c0b_landing.py](../../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
- [tests/test_intent_goal_deadline.py](../../../../../../../tests/test_intent_goal_deadline.py) — direct import
  - `test_linking_a_deadline_does_not_move_the_choice_time`
- [tests/test_intent_resolution.py](../../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_satisfying_a_check_does_not_move_its_choice_time`
  - `test_ties_go_to_the_item_level_then_the_higher_target`
- [tests/test_reader_followups.py](../../../../../../../tests/test_reader_followups.py) — direct import
  - `test_each_follow_up_is_a_test_me_later_commitment_with_its_provenance`

## Modification guidance

- Change resolution policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/resolution.py](../../../../../../../src/learnloop/scheduling/intent/resolution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
