---
title: "learnloop.ops.vault_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/vault_upgrade.py"
source_paths:
  - "src/learnloop/ops/vault_upgrade.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.vault_upgrade module"
  - "src/learnloop/ops/vault_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.vault_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.vault_upgrade` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: mvp-0.7 activation: atomic vault upgrade + mixed-version guards (KM §15, §12.7).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py) |
| Source lines | 318 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 37)
- `validate_mvp07_readiness(vault: LoadedVault) -> list[str]` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 47) — Blocking reasons a vault cannot activate the mvp-0.7 knowledge model (§3.2).
- `upgrade_to_mvp07(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 74) — Atomically activate mvp-0.7 and project legacy attempts into its state.
- `upgrade_to_mvp08(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 125) — Activate the mvp-0.8 authority-propagation projection as the default read path (spec §7.2, P0.5 design §7).
- `upgrade_to_mvp09(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 187) — Activate cross-channel reveal accounting on the existing P0 projection.
- `class CompatibilityDelta` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 278) — Explicit, inspectable mvp-0.7 -> mvp-0.8 reinterpretation delta (§7.2/§9.6).
  - `as_dict(self) -> dict[str, Any]` (line 288; public)
- `compatibility_projection_delta(baseline_cells: dict, candidate_cells: dict) -> CompatibilityDelta` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 292) — Compare two projected facet-capability cell maps (``{key: (pos, neg, cred)}``) and report the explicit delta.

### Module constants

- `LEGACY_ALGORITHM_VERSION` ([src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py), line 30)
- `COMPATIBILITY_DELTA_FILENAME` ([src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py), line 33)

## Internal implementation anchors

- `_projected_cells(repository: Repository) -> dict[tuple[str, str], tuple[float, float, float]]` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 247) — The projected facet-capability cells as ``{(facet, capability): (direct_pos, direct_neg, cert_credit)}`` -- the comparable surface for the mvp-0.7 vs mvp-0.8 compatibility delta.
- `_persist_compatibility_delta(sqlite_path: Path, delta: 'CompatibilityDelta', *, from_version: str) -> Path` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 262) — Write the inspectable cutover delta as a JSON artifact next to the sqlite.
- `_rewrite_algorithm_version(config_path: Path, from_version: str, to_version: str) -> None` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 308) — Atomically flip the single algorithm_version field (write-temp + rename).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`; statically calls `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `KM_ALGORITHM_VERSION`, `LEGACY_ALGORITHM_VERSION`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
  - `test_upgrade_is_idempotent`
  - `test_upgrade_projects_existing_attempts_into_canonical_facet_state`
  - `test_upgrade_refuses_from_unknown_version`
  - `test_upgrade_refuses_when_facets_unregistered`
  - `test_upgrade_succeeds_when_registry_complete`
  - `test_validate_readiness_flags_incomplete_contract`
- [tests/test_mvp09_upgrade.py](../../../../../../tests/test_mvp09_upgrade.py) — direct import
  - `test_upgrade_to_mvp09_flips_rebuilds_and_preserves_raw_history`
  - `test_upgrade_to_mvp09_is_immediate_successor_only`
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_already_mvp08_is_a_noop`
  - `test_compatibility_delta_is_explicit_when_changed`
  - `test_compatibility_delta_matches_when_identical`
  - `test_cutover_delta_is_empty_when_projections_match`
  - `test_cutover_delta_is_nonempty_and_inspectable_when_projections_differ`
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
  - `test_upgrade_does_not_rewrite_raw_history`
  - `test_upgrade_freezes_legacy_manifests_immutably`
  - `test_upgrade_refuses_from_non_mvp07`
  - `test_upgrade_to_mvp08_flips_and_records_receipt`

## Modification guidance

- Make changes here when the responsibility remains vault upgrade within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
