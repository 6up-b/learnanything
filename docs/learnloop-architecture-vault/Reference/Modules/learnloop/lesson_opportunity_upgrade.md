---
title: "learnloop.lesson_opportunity_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/lesson_opportunity_upgrade.py"
source_paths:
  - "src/learnloop/lesson_opportunity_upgrade.py"
source_commit: "6cad8141ecef068e53fce83d54802d5a726e0b95"
source_commit_timestamp: "2026-11-06T08:54:29-05:00"
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
  - "learnloop.lesson_opportunity_upgrade module"
  - "src/learnloop/lesson_opportunity_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.lesson_opportunity_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.lesson_opportunity_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to <LESSON_OPPORTUNITY_ALGORITHM_VERSION>``: teacher TE3a, AD's lesson opportunity.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/lesson_opportunity_upgrade.py](../../../../../src/learnloop/lesson_opportunity_upgrade.py) |
| Source lines | 225 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6cad8141ecef068e53fce83d54802d5a726e0b95` |
| Commit timestamp | `2026-11-06T08:54:29-05:00` |

## Public API

- `upgrade_to_lesson_opportunity(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 61) — The predecessor (or mvp-0.9 onwards, through the chain) -> TE3a's tag.
- `complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None=None) -> str | None` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 71) — Finish any journalled activation of the chain a dead process left; None when there is none.

### Module constants

- `PREDECESSOR` ([src/learnloop/lesson_opportunity_upgrade.py](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 51)
- `_CHAINED_PREDECESSORS` ([src/learnloop/lesson_opportunity_upgrade.py](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 55)
- `_STEP_REFUSAL` ([src/learnloop/lesson_opportunity_upgrade.py](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 58)

### Explicit exports

`__all__` declares:

- `PREDECESSOR`
- `complete_interrupted_activation`
- `upgrade_to_lesson_opportunity`

## Internal implementation anchors

- `_journal_path(vault) -> Path` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 106)
- `_read_journal(path: Path) -> tuple[str, str] | str | None` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 110)
- `_upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 120)
- `_activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 159) — Activate ``target`` in one transaction (the predecessor's contract: the journal before the publication, the publication last, the journal removed once committed).
- `_activation_committed(repository, target: str) -> bool` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 167)
- `_activate_as_writer(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../src/learnloop/lesson_opportunity_upgrade.py), line 177)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_lesson_opportunity`; statically calls `upgrade_to_lesson_opportunity`
- [[Reference/Modules/learnloop/phone_probes_upgrade|learnloop.phone_probes_upgrade]] — imports `complete_interrupted_activation`, `upgrade_to_lesson_opportunity`; statically calls `complete_interrupted_activation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LESSON_OPPORTUNITY_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`, `TEACHER_PROBES_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `write_activation_journal`; calls `write_activation_journal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`; calls `UpgradeResult`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `publish_algorithm_version`; calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/teacher_probes_upgrade|learnloop.teacher_probes_upgrade]] — imports `complete_interrupted_activation`, `upgrade_to_teacher_probes`; calls `complete_interrupted_activation`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/phone_probes_upgrade|learnloop.phone_probes_upgrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_te3a_successor.py](../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_openers_install_this_links_completion`
  - `test_the_successor_is_one_constant_after_te2_and_the_latest`
  - `test_the_upgrade_chains_from_an_older_link`
  - `test_the_upgrade_publishes_the_tag_and_completes_once`
  - `test_the_upgrade_refuses_anything_older_than_the_chain`

## Modification guidance

- Make changes here when the responsibility remains lesson opportunity upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/lesson_opportunity_upgrade.py](../../../../../src/learnloop/lesson_opportunity_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
