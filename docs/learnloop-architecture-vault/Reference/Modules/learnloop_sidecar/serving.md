---
title: "learnloop_sidecar.serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/serving.py"
source_paths:
  - "src/learnloop_sidecar/serving.py"
source_commit: "1c7b70f25d611bf447a429f94fcd65546c5d66ef"
source_commit_timestamp: "2026-10-13T17:53:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.serving module"
  - "src/learnloop_sidecar/serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.serving` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Sidecar refusal for serving an item of a put-away Learning Object.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py) |
| Source lines | 93 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1c7b70f25d611bf447a429f94fcd65546c5d66ef` |
| Commit timestamp | `2026-10-13T17:53:02-04:00` |

## Public API

- `refuse_inactive_learning_object(vault: LoadedVault, learning_object_id: str | None) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 47)
- `refuse_unservable_item(vault: LoadedVault, item: PracticeItem) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 69) — The item-level door: its LO's refusal, then the adoption kill switch.
- `refuse_held_out_item(vault: LoadedVault, repository: Any, item: PracticeItem) -> None` ([source](../../../../../src/learnloop_sidecar/serving.py), line 83) — A session serve of an item made from held-out material is refused.

### Module constants

- `INACTIVE_LEARNING_OBJECT_ERROR_CODE` ([src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py), line 43)
- `HELD_OUT_MATERIAL_ERROR_CODE` ([src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py), line 44)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `refuse_unservable_item`; statically calls `refuse_unservable_item`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`; statically calls `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `refuse_held_out_item`, `refuse_unservable_item`; statically calls `refuse_held_out_item`, `refuse_unservable_item`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `refuse_held_out_item`, `refuse_unservable_item`; statically calls `refuse_held_out_item`, `refuse_unservable_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_OUT_ITEM_REFUSAL`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`; calls `held_out_item_ids`, `held_out_material`, `held_out_selection_active`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `LEARNER_TEXT_GAP_DISABLED`, `REFERENCE_ADOPTION_DISABLED`, `learning_object_serving_block`, `practice_item_serving_block`; calls `learning_object_serving_block`, `practice_item_serving_block`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/rw2b_fix10_base_sequence.py](../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_approach_maps.py](../../../../../tests/test_approach_maps.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../tests/test_causal_repair_sidecar_rpcs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_followups_nov2_help_fold.py](../../../../../tests/test_followups_nov2_help_fold.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_help_fold_attach_successor.py](../../../../../tests/test_help_fold_attach_successor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_h2a_review_round2.py](../../../../../tests/test_hint_h2a_review_round2.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_h2a_review_round3.py](../../../../../tests/test_hint_h2a_review_round3.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_h2b_fix3.py](../../../../../tests/test_hint_h2b_fix3.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_h2b_fix4.py](../../../../../tests/test_hint_h2b_fix4.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_h2b_review.py](../../../../../tests/test_hint_h2b_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]
- [tests/test_hint_kill_switch.py](../../../../../tests/test_hint_kill_switch.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/serving.py](../../../../../src/learnloop_sidecar/serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
