---
title: "learnloop.adaptive_difficulty.protected_tables"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/protected_tables.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
source_commit: "6cad8141ecef068e53fce83d54802d5a726e0b95"
source_commit_timestamp: "2026-11-06T08:54:29-05:00"
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
  - "learnloop.adaptive_difficulty.protected_tables module"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.protected_tables`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.protected_tables` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The AD guard's table registry (the AD23 redesign, step 2; ``operation`` enforces it).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py) |
| Source lines | 769 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6cad8141ecef068e53fce83d54802d5a726e0b95` |
| Commit timestamp | `2026-11-06T08:54:29-05:00` |

## Public API

- `role(table: str) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 740)
- `read_verdict(table: str, *, rules: str | None, reader: str='', stack: tuple[str, ...]=()) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 744) — None when the read is allowed, else why it is refused.
- `write_verdict(table: str) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 761)

### Module constants

- `NEUTRAL` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 28)
- `PROTECTED` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 29)
- `PREDICATE` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 30)
- `DENIED` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 31)
- `_ROLES` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 33)
- `ROLES` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 225)
- `VALUE` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 235)
- `DERIVED` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 244)
- `COLUMNS` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 279)
- `EPOCH` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 567)
- `ENTITY_KINDS` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 588)
- `GAP_SOURCES` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 605)
- `AD_WRITABLE` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 627)
- `CARVE_OUTS` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 639)
- `_CHOKEPOINT` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 648)
- `DERIVED_TREATMENT` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 650)
- `READING` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 708)
- `ITEM_PROVENANCE` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 731)
- `_WHY` ([src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 735)

### Explicit exports

`__all__` declares:

- `AD_WRITABLE`
- `CARVE_OUTS`
- `COLUMNS`
- `DENIED`
- `DERIVED`
- `DERIVED_TREATMENT`
- `ENTITY_KINDS`
- `EPOCH`
- `GAP_SOURCES`
- `ITEM_PROVENANCE`
- `READING`
- `NEUTRAL`
- `PREDICATE`
- `PROTECTED`
- `ROLES`
- `VALUE`
- `read_verdict`
- `role`
- `write_verdict`

## Internal implementation anchors

- `_table(refs: Mapping[str, str], *, values: str, derived: str='') -> Mapping[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py), line 230)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `module`; statically calls `read_verdict`, `role`, `write_verdict`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `types`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_an_unclassified_table_is_refused_in_every_scope`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_fix_changes_serving_on_the_affected_shape_and_the_switches_restore_the_refusal_state`
  - `test_the_receipt_stays_refused_outside_the_rules`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_the_scan_reports_a_table_the_registry_drops`
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — direct import
  - `test_every_protected_table_reads_as_in_the_absent_copy`
- [tests/test_ad_protected_tables.py](../../../../../../tests/test_ad_protected_tables.py) — direct import
  - `test_every_ad_owned_table_ad_reads_has_an_epoch_rule`
  - `test_every_column_of_every_protected_table_is_classified`
  - `test_every_column_of_every_readable_table_is_metadata_or_content`
  - `test_every_derived_column_has_a_treatment`
  - `test_every_table_with_a_reading_reference_is_a_reading_or_item_provenance`
  - `test_the_registry_names_real_tables_and_roles`
- [tests/test_deliverable_curriculum_migration.py](../../../../../../tests/test_deliverable_curriculum_migration.py) — direct import
  - `test_228_is_c0bs_migration_classified_with_no_derived_table`
- [tests/test_figure_prefetch_migration.py](../../../../../../tests/test_figure_prefetch_migration.py) — direct import
  - `test_237_is_p5s_migration_and_every_table_is_classified`
- [tests/test_help_assist_figures_migration.py](../../../../../../tests/test_help_assist_figures_migration.py) — direct import
  - `test_232_is_the_figures_migration_and_help_assists_stays_a_raw_ledger`
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_230_is_the_work_md_migration_and_help_assists_stays_a_raw_ledger`
- [tests/test_learner_note_source_kind_migration.py](../../../../../../tests/test_learner_note_source_kind_migration.py) — direct import
  - `test_231_classifies_nothing_new`
- [tests/test_learner_notes_migration.py](../../../../../../tests/test_learner_notes_migration.py) — direct import
  - `test_229_is_c2s_migration_classified_with_no_derived_table`
- [tests/test_learner_notes_vault_origin_migration.py](../../../../../../tests/test_learner_notes_vault_origin_migration.py) — direct import
  - `test_233_classifies_nothing_new`
- [tests/test_ro2_history_migration.py](../../../../../../tests/test_ro2_history_migration.py) — direct import
  - `test_245_is_the_head_and_its_table_a_receipt_ad_classifies`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_the_registry_restates_the_figure_source_grammar`
- [tests/test_rw5c_migration.py](../../../../../../tests/test_rw5c_migration.py) — direct import
  - `test_238_is_applied_and_the_table_is_classified`
- [tests/test_rw5c_never_evidence.py](../../../../../../tests/test_rw5c_never_evidence.py) — direct import
  - `test_the_table_is_protected_and_unread_by_ad`
- [tests/test_section_coverage_migration.py](../../../../../../tests/test_section_coverage_migration.py) — direct import
  - `test_table_role_and_ad_classification`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_the_guard_refuses_raw_and_unclassified_reads_of_lesson_tables`
- [tests/test_te3a_migration.py](../../../../../../tests/test_te3a_migration.py) — direct import
  - `test_249_is_the_head_and_the_table_stays_a_receipt_ad_reads_by_its_rules`
- [tests/test_teacher_te1_migration.py](../../../../../../tests/test_teacher_te1_migration.py) — direct import
  - `test_234_is_te1s_migration_and_every_table_is_classified`
- [tests/test_teacher_te1b_migration.py](../../../../../../tests/test_teacher_te1b_migration.py) — direct import
  - `test_236_is_te1bs_migration_and_its_table_is_classified`
- [tests/test_teacher_te2log_migration.py](../../../../../../tests/test_teacher_te2log_migration.py) — direct import
  - `test_247_is_the_head_and_its_tables_receipts_denied_to_ad`

## Modification guidance

- Make changes here when the responsibility remains protected tables within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/protected_tables.py](../../../../../../src/learnloop/adaptive_difficulty/protected_tables.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
