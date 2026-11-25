---
title: "learnloop.vault.copy_locators"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/copy_locators.py"
source_paths:
  - "src/learnloop/vault/copy_locators.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.copy_locators module"
  - "src/learnloop/vault/copy_locators.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.copy_locators`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault.copy_locators` exists within [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] to own the behavior summarized by its module contract: What a copy of a practice item keeps of its source's location, so the exam classifier sees it.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/copy_locators.py](../../../../../../src/learnloop/vault/copy_locators.py) |
| Source lines | 86 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `source_locators(source: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/copy_locators.py), line 26) — The source item's own locators a copy keeps: its canonical exercise (``canonical_exercise``) and its provenance source refs (``source_refs``), the two fields ``exam_material.item_source_keys`` reads to tell whether an item was made from exam or held-out material.
- `copies_missing_locators(vault: LoadedVault) -> list[tuple[PracticeItem, PracticeItem]]` ([source](../../../../../../src/learnloop/vault/copy_locators.py), line 39) — ``(remint, its source)`` for each remint made before copies kept their source's locators (:func:`source_locators`): the source names a canonical exercise or source refs the remint lacks, so the exam classifier cannot see that the copy was made from the same passage.
- `repair_copy_locators(root: Path, vault: LoadedVault, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/vault/copy_locators.py), line 62) — Copy each older remint's missing source locators in (:func:`remint_missing_locators`); returns the repaired remint ids.

### Module constants

- `REMINT_ORIGIN` ([src/learnloop/vault/copy_locators.py](../../../../../../src/learnloop/vault/copy_locators.py), line 23)

### Explicit exports

`__all__` declares:

- `REMINT_ORIGIN`
- `copies_missing_locators`
- `repair_copy_locators`
- `source_locators`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `REMINT_ORIGIN`, `source_locators`; statically calls `source_locators`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `copies_missing_locators`, `repair_copy_locators`; statically calls `copies_missing_locators`, `repair_copy_locators`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]]
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]]
- [tests/test_probe_router_protection.py](../../../../../../tests/test_probe_router_protection.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]]
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]]
- [tests/test_activity_backfill.py](../../../../../../tests/test_activity_backfill.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_apply_recovery.py](../../../../../../tests/test_apply_recovery.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_apply_write_ahead.py](../../../../../../tests/test_apply_write_ahead.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_codex_transport_retired.py](../../../../../../tests/test_codex_transport_retired.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]

## Modification guidance

- Make changes here when the responsibility remains copy locators within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/copy_locators.py](../../../../../../src/learnloop/vault/copy_locators.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
