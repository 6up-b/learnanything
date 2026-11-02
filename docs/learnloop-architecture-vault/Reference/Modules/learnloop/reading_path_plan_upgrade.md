---
title: "learnloop.reading_path_plan_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reading_path_plan_upgrade.py"
source_paths:
  - "src/learnloop/reading_path_plan_upgrade.py"
source_commit: "49712bc6f1aa4fddf6356dd784057178faa27f9a"
source_commit_timestamp: "2026-10-25T11:47:25-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.reading_path_plan_upgrade module"
  - "src/learnloop/reading_path_plan_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.reading_path_plan_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reading_path_plan_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to <READING_PATH_PLAN_ALGORITHM_VERSION>``: RW7b.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reading_path_plan_upgrade.py](../../../../../src/learnloop/reading_path_plan_upgrade.py) |
| Source lines | 118 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `49712bc6f1aa4fddf6356dd784057178faa27f9a` |
| Commit timestamp | `2026-10-25T11:47:25-04:00` |

## Public API

- `upgrade_to_reading_path_plan(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/reading_path_plan_upgrade.py), line 72) — The predecessor (or mvp-0.9 onwards, through the chain) -> RW7b's tag: the plan follows the path.

### Module constants

- `PREDECESSOR` ([src/learnloop/reading_path_plan_upgrade.py](../../../../../src/learnloop/reading_path_plan_upgrade.py), line 62)
- `_CHAINED_PREDECESSORS` ([src/learnloop/reading_path_plan_upgrade.py](../../../../../src/learnloop/reading_path_plan_upgrade.py), line 66)
- `_STEP_REFUSAL` ([src/learnloop/reading_path_plan_upgrade.py](../../../../../src/learnloop/reading_path_plan_upgrade.py), line 69)

### Explicit exports

`__all__` declares:

- `PREDECESSOR`
- `upgrade_to_reading_path_plan`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `upgrade_to_reading_path_plan`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_reading_path_plan`; statically calls `upgrade_to_reading_path_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `READING_PATH_PLAN_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `upgrade_to_workbench_field_signals`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_plan_follows_path.py](../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw2d`
  - `test_upgrade_from_the_predecessor_and_through_the_chain`

## Modification guidance

- Make changes here when the responsibility remains reading path plan upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reading_path_plan_upgrade.py](../../../../../src/learnloop/reading_path_plan_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
