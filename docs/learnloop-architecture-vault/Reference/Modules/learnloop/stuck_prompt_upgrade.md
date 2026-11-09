---
title: "learnloop.stuck_prompt_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/stuck_prompt_upgrade.py"
source_paths:
  - "src/learnloop/stuck_prompt_upgrade.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.stuck_prompt_upgrade module"
  - "src/learnloop/stuck_prompt_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.stuck_prompt_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.stuck_prompt_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to mvp-0.13``: "Write what you can" replaces "I don't know".

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/stuck_prompt_upgrade.py](../../../../../src/learnloop/stuck_prompt_upgrade.py) |
| Source lines | 113 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `upgrade_to_mvp013(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/stuck_prompt_upgrade.py), line 66)

### Module constants

- `_CHAINED_PREDECESSORS` ([src/learnloop/stuck_prompt_upgrade.py](../../../../../src/learnloop/stuck_prompt_upgrade.py), line 59)

### Explicit exports

`__all__` declares:

- `upgrade_to_mvp013`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_mvp013`; statically calls `upgrade_to_mvp013`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `upgrade_to_mvp013`; statically calls `upgrade_to_mvp013`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`, `STUCK_PROMPT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `upgrade_to_mvp012`; calls `upgrade_to_mvp012`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mvp013_upgrade.py](../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_by_default_the_chain_reports_the_advisory_guard_and_proceeds`
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
  - `test_upgrade_refuses_older_and_repeated_targets`

## Modification guidance

- Make changes here when the responsibility remains stuck prompt upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/stuck_prompt_upgrade.py](../../../../../src/learnloop/stuck_prompt_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
