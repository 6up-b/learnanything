---
title: "learnloop.ops.upgrades"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/upgrades.py"
source_paths:
  - "src/learnloop/ops/upgrades.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.upgrades module"
  - "src/learnloop/ops/upgrades.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.upgrades`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.upgrades` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: ``learnloop upgrade``: the vault upgrade table, from the oldest supported tag up.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/upgrades.py](../../../../../../src/learnloop/ops/upgrades.py) |
| Source lines | 396 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class UpgradeResult` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 51)
- `class Activation` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 61) — How a link activates: ``run`` derives the tag's state inside the activation's transaction, and ``committed`` reads the receipt that transaction writes, so it is true exactly when an activation committed.
- `class Link` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 102)
  - `predecessor(self) -> str` (line 107; public)
- `targets(links: Sequence[Link] | None=None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 118) — The tags ``learnloop upgrade --to`` accepts.
- `upgrade(root: Path, *, to: str=LATEST_ALGORITHM_VERSION, clock: Clock | None=None, links: Sequence[Link] | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 124) — Bring the vault at ``root`` to ``to`` through the table, one activation per row from its own tag.
- `complete_interrupted_activation(root: Path, *, vault: LoadedVault | None=None, clock: Clock | None=None, links: Sequence[Link] | None=None) -> str | None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 196) — Finish an activation a dead process left journalled; the tag it completed, or None.
- `write_activation_journal(path: Path, predecessor: str, target: str) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 315) — Write the journal durably: temporary file, fsync, rename, directory fsync.
- `publish_algorithm_version(config_path: Path, from_version: str, to_version: str, *, renamed: Callable[[], None] | None=None) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 331) — The config's durable publication: the rename lands before the caller commits, and after a power loss it is never older than the commit (the temporary file is fsynced before the rename, the directory after it).
- `rewrite_algorithm_version(config_path: Path, from_version: str, to_version: str, *, durable: bool=False) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 346) — Atomically replace the config's one ``algorithm_version = "<from_version>"`` line (write-temp + rename).

### Module constants

- `UPGRADES` ([src/learnloop/ops/upgrades.py](../../../../../../src/learnloop/ops/upgrades.py), line 112)

### Explicit exports

`__all__` declares:

- `UPGRADES`
- `Activation`
- `Link`
- `UpgradeResult`
- `complete_interrupted_activation`
- `idempotent_projection`
- `publish_algorithm_version`
- `rewrite_algorithm_version`
- `targets`
- `upgrade`
- `whole_vault_rebuild`
- `write_activation_journal`

## Internal implementation anchors

- `_project(vault: LoadedVault, repository: Repository, predecessor: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 70)
- `_projection_committed(repository: Repository, tag: str) -> bool` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 74)
- `_rebuild(vault: LoadedVault, repository: Repository, predecessor: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 84)
- `_rebuild_committed(repository: Repository, tag: str) -> bool` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 88)
- `_upgrade(root: Path, *, to: str, clock: Clock | None, links: Sequence[Link]) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 142)
- `_walk(links: Sequence[Link], original: str, to: str) -> list[Link] | None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 177) — The rows from the one whose predecessor is ``original`` through ``to``; None when there is no such path (a jump: ``original`` is no predecessor in the table, or is past ``to``).
- `_unknown_journal(sqlite_path: Path) -> str` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 189)
- `_activate(root: Path, link: Link, *, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 240) — Activate ``link`` in one transaction; ``publish``: the config still names its predecessor.
- `_activate_as_writer(root: Path, link: Link, *, publish: bool, clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 250)
- `_journal_path(vault: LoadedVault) -> Path` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 301)
- `_read_journal(path: Path) -> tuple[str, str] | str | None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 305)
- `_fsync_directory(directory: Path) -> None` ([source](../../../../../../src/learnloop/ops/upgrades.py), line 375)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `targets`, `upgrade`; statically calls `targets`, `upgrade`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `complete_interrupted_activation`; statically calls `complete_interrupted_activation`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `complete_interrupted_activation`; statically calls `complete_interrupted_activation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `completing_activation`, `journal_path`, `message`, `pending`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FACET_BELIEF_FIX_ALGORITHM_VERSION`, `LATEST_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_all_derived_state`; calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/version_floor|learnloop.version_floor]] — imports `BelowOldestSupported`, `refuse_journal_below_floor`; calls `refuse_journal_below_floor`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followups_nov2_help_fold_helpers.py](../../../../../../tests/followups_nov2_help_fold_helpers.py) — direct import
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_a_failed_upgrade_leaves_the_log_in_place`
  - `test_f1_a_denial_after_the_upgrade_returned_stays_live`
  - `test_v2_f1_an_unmarked_upgrade_leaves_the_log_live`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_i_a_figure_goal_from_the_ask_rail_or_the_tutor_never_spends_an_ask_question`
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict`
- [tests/test_upgrades.py](../../../../../../tests/test_upgrades.py) — direct import
  - `test_a_failure_before_the_commit_leaves_the_predecessor_readable_and_no_journal`
  - `test_a_journal_left_after_the_commit_is_just_removed`
  - `test_a_jump_is_refused_and_nothing_changes`
  - `test_a_link_activates_from_its_predecessor_and_a_rerun_does_nothing`
  - `test_a_real_death_after_the_journal_before_the_publication_leaves_the_predecessor`
  - `test_a_real_death_after_the_publication_is_completed_by_the_next_command`
  - `test_a_vault_born_at_the_tag_completes_its_activation_once`
  - `test_an_activation_that_cannot_complete_stops_the_opener`
  - `test_an_mcp_server_already_attached_stops_serving_when_a_journal_appears`
  - `test_each_activation_kind_commits_its_own_receipt_once`
  - `test_the_floor_reaches_each_tag_through_the_table`
  - `test_the_journal_is_written_before_the_publication_and_the_commit_follows_it`
  - `test_the_table_is_the_chain_from_the_floor_one_row_per_tag`
  - `test_the_upgrade_command_completes_its_own_interrupted_activation`

## Modification guidance

- Make changes here when the responsibility remains upgrades within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/upgrades.py](../../../../../../src/learnloop/ops/upgrades.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
