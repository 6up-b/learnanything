---
title: "learnloop.field.workbench_signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/workbench_signals.py"
source_paths:
  - "src/learnloop/field/workbench_signals.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.workbench_signals module"
  - "src/learnloop/field/workbench_signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.workbench_signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.workbench_signals` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: RW2d: workbench signals in the learner field (spec_reader_workbench_v1 §5.11, G41).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py) |
| Source lines | 352 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `workbench_field_signals_live(vault: Any) -> bool` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 94) — At the successor (or later) with ``workbench.field_signals_enabled`` on.
- `is_workbench_signal(signal: SignalRow) -> bool` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 105) — A row only the successor's derivation produces (the predecessor's are the rest).
- `derive_workbench_signals(sessions: Iterable[Mapping[str, Any]], steps: Iterable[Mapping[str, Any]], assists: Iterable[Mapping[str, Any]], *, attempts: Mapping[str, Mapping[str, Any]], contract_targets: Mapping[str, str], diagnostics: dict[str, Any] | None=None) -> tuple[SignalRow, ...]` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 173) — The two workbench sources as zero-mass signal rows (pure).
- `load_workbench_signals(connection: Any, vault: Any, *, diagnostics: dict[str, Any] | None=None) -> tuple[SignalRow, ...]` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 268) — The workbench rows for a live successor (empty otherwise).

### Module constants

- `WORKBENCH_SIGNAL_VERSION` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 74)
- `STUCK_CONFUSION_SIGNAL` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 77)
- `WORKBENCH_HELP_SIGNAL` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 80)
- `STUCK_PREFIX` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 81)
- `HELP_PREFIX` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 82)
- `HELP_ASSIST_KINDS` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 86)
- `SUBJECT_UNRECORDED` ([src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py), line 91)

### Explicit exports

`__all__` declares:

- `HELP_ASSIST_KINDS`
- `SUBJECT_UNRECORDED`
- `WORKBENCH_HELP_SIGNAL`
- `WORKBENCH_SIGNAL_VERSION`
- `derive_workbench_signals`
- `is_workbench_signal`
- `load_workbench_signals`
- `workbench_field_signals_live`

## Internal implementation anchors

- `_has_text(value: Any) -> bool` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 111)
- `_chain_roots(steps: Iterable[Mapping[str, Any]], wanted: Iterable[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 115) — The chain root of each ``wanted`` step row: an edit, tombstone or undo supersedes the head.
- `_snapshot_has_work(raw: Any, step_rows: Mapping[str, Mapping[str, Any]] | None=None) -> bool | None` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 139) — Whether a logged step snapshot holds an ordinary step with text.
- `_table_present(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 256)
- `_rows(connection: Any, sql: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 262)
- `_contract_targets(connection: Any, sessions: Iterable[Mapping[str, Any]], attempts: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/field/workbench_signals.py), line 308) — The LO per contract version an unsubmitted session froze (review F3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `is_workbench_signal`, `load_workbench_signals`; statically calls `is_workbench_signal`, `load_workbench_signals`
- [[Reference/Modules/learnloop/placement/field_receipts|learnloop.placement.field_receipts]] — imports `WORKBENCH_SIGNAL_VERSION`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `is_workbench_signal`, `workbench_field_signals_live`; statically calls `is_workbench_signal`, `workbench_field_signals_live`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `WORKBENCH_FIELD_SIGNALS_VERSIONS`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `SignalRow`; calls `SignalRow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]], [[Reference/Modules/learnloop/placement/field_receipts|learnloop.placement.field_receipts]], [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_g41_off_is_the_predecessor_on_fixture_copies`
  - `test_on_the_derivation_is_the_predecessors_plus_the_workbench_rows`
  - `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract`
  - `test_review_f1_a_worked_example_after_real_work_is_not_early_help`
  - `test_the_switch_is_on_by_default_and_classified`

## Modification guidance

- Make changes here when the responsibility remains workbench signals within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/workbench_signals.py](../../../../../../src/learnloop/field/workbench_signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
