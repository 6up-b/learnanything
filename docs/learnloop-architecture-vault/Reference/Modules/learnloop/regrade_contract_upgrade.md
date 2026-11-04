---
title: "learnloop.regrade_contract_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/regrade_contract_upgrade.py"
source_paths:
  - "src/learnloop/regrade_contract_upgrade.py"
source_commit: "a859b2f1e2456bd64eaabb8fbebdb920d2bd06c9"
source_commit_timestamp: "2026-10-25T18:55:55-04:00"
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
  - "learnloop.regrade_contract_upgrade module"
  - "src/learnloop/regrade_contract_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.regrade_contract_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.regrade_contract_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to mvp-0.26``: regrade contracts.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/regrade_contract_upgrade.py](../../../../../src/learnloop/regrade_contract_upgrade.py) |
| Source lines | 273 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a859b2f1e2456bd64eaabb8fbebdb920d2bd06c9` |
| Commit timestamp | `2026-10-25T18:55:55-04:00` |

## Public API

- `upgrade_to_mvp026(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/regrade_contract_upgrade.py), line 109) — mvp-0.25 (or mvp-0.9 to mvp-0.24, through the chain) -> mvp-0.26: regrade contracts.

### Module constants

- `_CHAINED_PREDECESSORS` ([src/learnloop/regrade_contract_upgrade.py](../../../../../src/learnloop/regrade_contract_upgrade.py), line 98)
- `_STEP_REFUSAL` ([src/learnloop/regrade_contract_upgrade.py](../../../../../src/learnloop/regrade_contract_upgrade.py), line 101)
- `_HELD_NOTE` ([src/learnloop/regrade_contract_upgrade.py](../../../../../src/learnloop/regrade_contract_upgrade.py), line 103)

### Explicit exports

`__all__` declares:

- `publish_algorithm_version`
- `upgrade_to_mvp026`
- `upgrade_to_regrade_contracts`

## Internal implementation anchors

- `_upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult` ([source](../../../../../src/learnloop/regrade_contract_upgrade.py), line 122)
- `_held_note(held: list[dict[str, Any]]) -> str` ([source](../../../../../src/learnloop/regrade_contract_upgrade.py), line 163)
- `_activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> list[dict[str, Any]] | None` ([source](../../../../../src/learnloop/regrade_contract_upgrade.py), line 167) — Activate ``target`` over the vault at ``root`` in one transaction.
- `_publish_algorithm_version(config_path: Path, from_version: str, to_version: str, *, renamed: Callable[[], None] | None=None) -> None` ([source](../../../../../src/learnloop/regrade_contract_upgrade.py), line 246) — The atomic config rename (``ops.vault_upgrade.rewrite_algorithm_version``), made durable before the caller commits: the temporary file is fsynced before the rename and the directory after it, so after a power loss the rename is never older than the commit.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_mvp026`; statically calls `upgrade_to_mvp026`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `upgrade_to_mvp026`; statically calls `upgrade_to_mvp026`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `publish_algorithm_version`; statically calls `publish_algorithm_version`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `METHOD_EXPLICIT_ALGORITHM_VERSION`, `REGRADE_CONTRACT_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `unrecorded_epoch_attempts`; calls `unrecorded_epoch_attempts`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `contract_unrecorded_attempts`; calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `upgrade_to_mvp025`; calls `upgrade_to_mvp025`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_all_derived_state`; calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `os`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]], [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]], [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_recap_review_r3.py](../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f1_r3_the_as_of_hold_agrees_with_the_upgrade_on_every_shape`
- [tests/test_regrade_contract_upgrade.py](../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_a_failed_activation_leaves_the_predecessor_exactly_as_it_was`
  - `test_a_failed_commit_after_publication_restores_the_predecessors_label`
  - `test_a_failed_publication_fsync_leaves_the_predecessors_label`
  - `test_after_the_upgrade_a_rebuild_settles_and_stays`
  - `test_an_upgrade_interrupted_after_publication_is_resumed`
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_no_writer_interleaves_between_the_scan_and_the_publication`
  - `test_the_upgrade_shadow_predicts_the_upgrade_exactly`
  - `test_upgrade_holds_exactly_the_unrecorded_epochs_and_rewrites_no_evidence`
  - `test_upgrade_refuses_older_versions_and_is_idempotent`
  - `test_upgrade_through_the_chain_from_earlier_successors`
  - `test_upgrade_with_nothing_to_reinterpret_replays_nothing`

## Modification guidance

- Make changes here when the responsibility remains regrade contract upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/regrade_contract_upgrade.py](../../../../../src/learnloop/regrade_contract_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
