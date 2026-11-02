---
title: "learnloop.one_ask_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/one_ask_upgrade.py"
source_paths:
  - "src/learnloop/one_ask_upgrade.py"
source_commit: "043463103e0d027baf5a33a62fe3948504d4ae03"
source_commit_timestamp: "2026-10-26T19:03:18-04:00"
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
  - "learnloop.one_ask_upgrade module"
  - "src/learnloop/one_ask_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.one_ask_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.one_ask_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to <ONE_ASK_ALGORITHM_VERSION>``: Reader CA2, one Ask.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/one_ask_upgrade.py](../../../../../src/learnloop/one_ask_upgrade.py) |
| Source lines | 295 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `043463103e0d027baf5a33a62fe3948504d4ae03` |
| Commit timestamp | `2026-10-26T19:03:18-04:00` |

## Public API

- `upgrade_to_one_ask(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 97) — The predecessor (or mvp-0.9 onwards, through the chain) -> Reader CA2's tag: one help rule.
- `complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None=None) -> str | None` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 107) — Finish any journalled activation of the chain a dead process left; None when there is none.

### Module constants

- `PREDECESSOR` ([src/learnloop/one_ask_upgrade.py](../../../../../src/learnloop/one_ask_upgrade.py), line 87)
- `_CHAINED_PREDECESSORS` ([src/learnloop/one_ask_upgrade.py](../../../../../src/learnloop/one_ask_upgrade.py), line 91)
- `_STEP_REFUSAL` ([src/learnloop/one_ask_upgrade.py](../../../../../src/learnloop/one_ask_upgrade.py), line 94)

### Explicit exports

`__all__` declares:

- `PREDECESSOR`
- `complete_interrupted_activation`
- `upgrade_to_one_ask`

## Internal implementation anchors

- `_journal_path(vault) -> Path` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 152) — The activation journal beside the vault database (``learnloop.activation_journal``).
- `_read_journal(path: Path) -> tuple[str, str] | str | None` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 158)
- `_upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 168)
- `_activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 213) — Activate ``target`` in one transaction.
- `_activation_committed(repository, target: str) -> bool` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 231) — Whether an activation of ``target`` committed: its projection receipt is on record.
- `_activate_as_writer(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../src/learnloop/one_ask_upgrade.py), line 243)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_one_ask`; statically calls `upgrade_to_one_ask`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `complete_interrupted_activation`, `upgrade_to_one_ask`; statically calls `complete_interrupted_activation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ONE_ASK_ALGORITHM_VERSION`, `REPLAY_LEDGER_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `write_activation_journal`; calls `write_activation_journal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`; calls `UpgradeResult`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `publish_algorithm_version`; calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `complete_interrupted_activation`, `upgrade_to_replay_ledger`; calls `complete_interrupted_activation`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_denial_log.py](../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_a_failed_upgrade_leaves_the_log_in_place`
  - `test_f1_a_denial_after_the_upgrade_returned_stays_live`
  - `test_v2_f1_an_unmarked_upgrade_leaves_the_log_live`
- [tests/test_batch3_landing.py](../../../../../tests/test_batch3_landing.py) — direct import
  - `test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal`
  - `test_a_real_death_after_the_publication_is_journalled_and_the_next_cli_command_completes_it`
  - `test_a_torn_journal_at_the_predecessor_is_removed_and_nothing_activates`
  - `test_an_mvp034_journal_is_handed_to_its_own_upgrade_then_the_tag_activates`
  - `test_mvp035_is_one_constant_after_mvp034_and_the_latest`
  - `test_the_upgrade_completes_its_own_journal`
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
  - `test_the_upgrade_moves_the_predecessor_and_refuses_twice`

## Modification guidance

- Make changes here when the responsibility remains one ask upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/one_ask_upgrade.py](../../../../../src/learnloop/one_ask_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
