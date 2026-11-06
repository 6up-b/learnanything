---
title: "learnloop.adaptive_difficulty.protection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/protection.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/protection.py"
source_commit: "38c895e230ef534fc7b4a2eff18a51ca456a06a2"
source_commit_timestamp: "2026-10-24T10:23:24-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.protection module"
  - "src/learnloop/adaptive_difficulty/protection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.protection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.protection` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Exam protection for AD's model inputs (spec A8, G-AD1-6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/protection.py](../../../../../../src/learnloop/adaptive_difficulty/protection.py) |
| Source lines | 131 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38c895e230ef534fc7b4a2eff18a51ca456a06a2` |
| Commit timestamp | `2026-10-24T10:23:24-04:00` |

## Public API

- `class Protection` ([source](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 34) — The held-out predicate, evaluated once per pass.
  - `__contains__(self, practice_item_id: object) -> bool` (line 48; internal)
  - `covers(self, item: Any) -> bool` (line 51; public) — Whether this revision (a current item or a snapshot) is protected.
  - `covers_identity(self, identity: Any) -> bool` (line 64; public) — Whether a frozen revision identity (:func:`~learnloop.adaptive_difficulty.outside.source_identity`) is protected now: its item id is, or its own source references as frozen lie in held-out material (Codex re-review F11; the same rule as ``held_out_item_ids``).
- `protection(vault: Any, repository: Any) -> Protection` ([source](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 86) — The held-out predicate for one pass (fails closed).
- `guard(vault: Any, repository: Any, protected: Any=None) -> Protection` ([source](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 107) — A caller's :class:`Protection`, or a fresh one (a bare id set adds its ids).
- `protected_items(vault: Any, repository: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 118) — Items made from held-out material, or reserved for a held-out exam.
- `is_protected(vault: Any, repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 127)

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/protection.py](../../../../../../src/learnloop/adaptive_difficulty/protection.py), line 30)

### Explicit exports

`__all__` declares:

- `Protection`
- `guard`
- `is_protected`
- `protected_items`
- `protection`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `guard`; statically calls `guard`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `Protection`, `module`; statically calls `guard`, `protection`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `Protection`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `guard`; statically calls `guard`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `Protection`, `protection`; statically calls `Protection`, `protection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `Scope`, `scoped`; calls `scoped`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_item_ids`, `held_out_material`; calls `held_out_item_ids`, `held_out_material`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id`
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_an_exception_before_the_first_revision_keeps_the_whole_batch`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_any_change_to_the_protection_changes_the_epoch`
  - `test_the_epoch_changes_on_mark_unmark_reserve_and_release_and_not_on_unrelated_edits`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_held_out_sentinel_never_reaches_ad_inputs`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_codex_rereview_f1_a_lesson_is_judged_by_the_revision_it_showed_not_the_items_current_one`

## Modification guidance

- Make changes here when the responsibility remains protection within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/protection.py](../../../../../../src/learnloop/adaptive_difficulty/protection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
