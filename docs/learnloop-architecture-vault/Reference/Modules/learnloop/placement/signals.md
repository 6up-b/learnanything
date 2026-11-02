---
title: "learnloop.placement.signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/signals.py"
source_paths:
  - "src/learnloop/placement/signals.py"
source_commit: "54f2a35018a4027a8e36a89ed2b5c04f1cf59d8f"
source_commit_timestamp: "2026-10-24T14:49:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.signals module"
  - "src/learnloop/placement/signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.signals` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Interaction signals as placement routes them (field §3.1, live with F2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/signals.py](../../../../../../src/learnloop/placement/signals.py) |
| Source lines | 107 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `54f2a35018a4027a8e36a89ed2b5c04f1cf59d8f` |
| Commit timestamp | `2026-10-24T14:49:05-04:00` |

## Public API

- `blocking_signals_by_lo(connection: Any, vault: Any, answers_by_lo: Mapping[str, Iterable[AnswerFacts]]) -> dict[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/placement/signals.py), line 51) — Signal ids, per LO, that keep it out of fast-track (sorted, stable).
- `blocking_with_predecessor(connection: Any, vault: Any, answers_by_lo: Mapping[str, Iterable[AnswerFacts]]) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]` ([source](../../../../../../src/learnloop/placement/signals.py), line 61) — ``(blocking, predecessor_blocking)``: this derivation's per-LO blocking ids, and the ones the predecessor's derivation produces (RW2d's receipts).
- `taught_first_by_predecessor(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/placement/signals.py), line 82) — ``(taught_first, predecessor_taught_first)`` among these LOs (equal when RW2d is off).
- `taught_first_learning_objects(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/placement/signals.py), line 97) — Of these LOs, those with help or confusion signals: taught first.

## Internal implementation anchors

- `_attempt_rows(answers_by_lo: Mapping[str, Iterable[AnswerFacts]]) -> list[AttemptRow]` ([source](../../../../../../src/learnloop/placement/signals.py), line 24)
- `_by_lo(signals: Iterable[SignalRow]) -> dict[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/placement/signals.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `blocking_signals_by_lo`; statically calls `blocking_signals_by_lo`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `blocking_with_predecessor`; statically calls `blocking_with_predecessor`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `taught_first_by_predecessor`; statically calls `taught_first_by_predecessor`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `blocks_fast_track`, `load_interaction_signals`; calls `blocks_fast_track`, `load_interaction_signals`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `AttemptRow`, `ItemFeatures`, `SignalRow`; calls `AttemptRow`, `ItemFeatures`
- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `is_workbench_signal`, `workbench_field_signals_live`; calls `is_workbench_signal`, `workbench_field_signals_live`
- [[Reference/Modules/learnloop/placement/rules|learnloop.placement.rules]] — imports `AnswerFacts`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_answers`; calls `load_answers`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]], [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_confused_stuck_answer_keeps_its_topic_out_of_fast_track`

## Modification guidance

- Make changes here when the responsibility remains signals within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/signals.py](../../../../../../src/learnloop/placement/signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
