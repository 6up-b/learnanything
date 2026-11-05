---
title: "learnloop.claim_fixes_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/claim_fixes_upgrade.py"
source_paths:
  - "src/learnloop/claim_fixes_upgrade.py"
source_commit: "5563d696024e4e24fa6dcd4ce666edd369666f1e"
source_commit_timestamp: "2026-10-26T10:26:01-04:00"
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
  - "learnloop.claim_fixes_upgrade module"
  - "src/learnloop/claim_fixes_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.claim_fixes_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.claim_fixes_upgrade` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: ``learnloop upgrade --to <CLAIM_FIXES_ALGORITHM_VERSION>``: LP-min (a).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/claim_fixes_upgrade.py](../../../../../src/learnloop/claim_fixes_upgrade.py) |
| Source lines | 385 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5563d696024e4e24fa6dcd4ce666edd369666f1e` |
| Commit timestamp | `2026-10-26T10:26:01-04:00` |

## Public API

- `upgrade_to_claim_fixes(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 116) — The predecessor (or mvp-0.9 onwards, through the chain) -> LP-min (a)'s tag: the claim fixes.
- `complete_interrupted_activation(root: Path, *, vault=None, clock: Clock | None=None) -> _Activated | None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 166) — Finish an activation a dead process left journalled; None when there is none.
- `write_activation_journal(path: Path, predecessor: str, target: str) -> None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 332) — Write the journal durably (temporary file, fsync, rename, directory fsync).

### Module constants

- `PREDECESSOR` ([src/learnloop/claim_fixes_upgrade.py](../../../../../src/learnloop/claim_fixes_upgrade.py), line 106)
- `_CHAINED_PREDECESSORS` ([src/learnloop/claim_fixes_upgrade.py](../../../../../src/learnloop/claim_fixes_upgrade.py), line 110)
- `_STEP_REFUSAL` ([src/learnloop/claim_fixes_upgrade.py](../../../../../src/learnloop/claim_fixes_upgrade.py), line 113)

### Explicit exports

`__all__` declares:

- `PREDECESSOR`
- `complete_interrupted_activation`
- `upgrade_to_claim_fixes`
- `write_activation_journal`

## Internal implementation anchors

- `_upgrade(root: Path, *, clock: Clock | None) -> UpgradeResult` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 126)
- `_complete(root: Path, *, clock: Clock | None) -> _Activated | None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 184)
- `class _Activated(NamedTuple)` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 211)
- `_notes(activated: _Activated) -> list[str]` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 216)
- `_activate(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> _Activated` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 231) — Activate ``target`` in one transaction; ``publish``: the config still names ``predecessor``.
- `_activate_as_writer(root: Path, *, predecessor: str, target: str, publish: bool, clock: Clock | None) -> _Activated` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 243)
- `_journal_path(vault) -> Path` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 314) — The activation journal beside the vault database (``learnloop.activation_journal``).
- `_read_journal(path: Path) -> tuple[str, str] | None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 320)
- `_activation_committed(repository, target: str) -> bool` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 351) — Whether an activation of ``target`` committed: its projection receipt is on record.
- `_publish_algorithm_version(config_path: Path, from_version: str, to_version: str, *, renamed: Callable[[], None] | None=None) -> None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 363) — The durable config rename, as ``regrade_contract_upgrade`` publishes it.
- `_fsync_directory(directory: Path) -> None` ([source](../../../../../src/learnloop/claim_fixes_upgrade.py), line 377)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_claim_fixes`; statically calls `upgrade_to_claim_fixes`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `complete_interrupted_activation`, `upgrade_to_claim_fixes`, `write_activation_journal`; statically calls `complete_interrupted_activation`, `write_activation_journal`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `write_activation_journal`; statically calls `write_activation_journal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `CLAIM_FIXES_ALGORITHM_VERSION`, `READING_PATH_PLAN_ALGORITHM_VERSION`, `SUCCESSOR_CHAIN`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `learning_objects_with_covering_claims`; calls `initial_mastery_state_for_learning_object`, `learning_objects_with_covering_claims`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `upgrade_to_reading_path_plan`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `COLD_MASTERY_BASELINE_AT`, `rebuild_all_derived_state`; calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `os`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]], [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]], [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_lp_claim_fixes.py](../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor`
  - `test_upgrade_from_the_predecessor_replays_claimed_los_and_through_the_chain`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f2_an_activation_that_cannot_complete_stops_the_opener`
  - `test_f2_an_mcp_server_already_attached_stops_serving_when_a_journal_appears`
  - `test_f8_activation_reseeds_with_the_retained_variance_as_a_rebuild_does`
- [tests/test_lp_claim_fixes_review.py](../../../../../tests/test_lp_claim_fixes_review.py) — direct import
  - `test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal`
  - `test_f2_a_journal_left_after_the_commit_is_just_removed`
  - `test_f2_failures_before_or_after_the_rename_leave_the_predecessor_and_no_journal`
  - `test_f3_activation_reseeds_claimed_los_without_attempts_as_a_rebuild_does`

## Modification guidance

- Make changes here when the responsibility remains claim fixes upgrade within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/claim_fixes_upgrade.py](../../../../../src/learnloop/claim_fixes_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
