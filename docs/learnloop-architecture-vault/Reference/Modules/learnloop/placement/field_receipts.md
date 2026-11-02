---
title: "learnloop.placement.field_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/field_receipts.py"
source_paths:
  - "src/learnloop/placement/field_receipts.py"
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
  - "learnloop.placement.field_receipts module"
  - "src/learnloop/placement/field_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.field_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.field_receipts` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: RW2d's receipts: what the predecessor's derivation and rule would have decided.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/field_receipts.py](../../../../../../src/learnloop/placement/field_receipts.py) |
| Source lines | 69 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `54f2a35018a4027a8e36a89ed2b5c04f1cf59d8f` |
| Commit timestamp | `2026-10-24T14:49:05-04:00` |

## Public API

- `receipt_row(*, algorithm_version: str, decision_kind: str, decision_ref: str | None, learning_object_id: str, blocking: Sequence[str], predecessor_blocking: Sequence[str], verdict: Mapping[str, Any], predecessor_verdict: Mapping[str, Any], now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/field_receipts.py), line 28) — One ``field_signal_receipts`` row; its key repeats only for the same decision, LO, workbench signal set and predecessor verdict.
- `fast_track_side(verdict: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/field_receipts.py), line 63) — A ``FastTrackVerdict`` as a receipt side.

### Explicit exports

`__all__` declares:

- `fast_track_side`
- `receipt_row`

## Internal implementation anchors

- `_side(blocking: Sequence[str], verdict: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/field_receipts.py), line 24)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `fast_track_side`, `receipt_row`; statically calls `fast_track_side`, `receipt_row`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `WORKBENCH_SIGNAL_VERSION`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_placement_report.py](../../../../../../tests/test_placement_report.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — imports consumer [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]]

## Modification guidance

- Make changes here when the responsibility remains field receipts within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/field_receipts.py](../../../../../../src/learnloop/placement/field_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
