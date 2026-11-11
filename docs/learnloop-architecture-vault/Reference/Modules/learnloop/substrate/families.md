---
title: "learnloop.substrate.families"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/families.py"
source_paths:
  - "src/learnloop/substrate/families.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.families module"
  - "src/learnloop/substrate/families.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.families`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.families` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Recoverable authored-family application.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/families.py](../../../../../../src/learnloop/substrate/families.py) |
| Source lines | 507 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `family_operation_lock(root: Path)` ([source](../../../../../../src/learnloop/substrate/families.py), line 36)
- `family_item_input(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/families.py), line 40) — Exact authored item and effective rubric judged, excluding regrouping.
- `family_item_input_hash(vault: LoadedVault, item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/substrate/families.py), line 49)
- `apply_family(vault: LoadedVault, repository: Repository, family: ActivityFamily, members: Mapping[str, str], *, proposal_id: str, judge: str='owner', rationale: str='', judgment_ids: Sequence[str]=(), clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/families.py), line 147) — Accept an authored record or a complete-link two-pass judged group.
- `attach_to_family(vault: LoadedVault, repository: Repository, family_id: str, item_id: str, relation: str, *, proposal_id: str, judgment_ids: Sequence[str], rationale: str='', clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/families.py), line 282) — Add one unfamilied item to an EXISTING family (canonical sources S1, §7.4).
- `undo_family(vault: LoadedVault, repository: Repository, proposal_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 351)
- `recover_family_operations(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 380)
- `sync_authored_families(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 386) — Snapshot owner-edited revisions without minting another family identity.

### Module constants

- `FAMILY_JUDGE_PROMPTS` ([src/learnloop/substrate/families.py](../../../../../../src/learnloop/substrate/families.py), line 32)
- `GROUPING_POLICY_VERSION` ([src/learnloop/substrate/families.py](../../../../../../src/learnloop/substrate/families.py), line 33)

## Internal implementation anchors

- `_safe_path(root: Path, relative: str) -> Path` ([source](../../../../../../src/learnloop/substrate/families.py), line 53)
- `_write_atomic(path: Path, data: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 60)
- `_patch_data(path: Path, patch: dict[str, Any], undo: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/families.py), line 78)
- `_validate_judgments(connection: Any, vault: LoadedVault, family: ActivityFamily, members: Mapping[str, str], judgment_ids: Sequence[str]) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 96)
- `_validate_attach_judgments(connection: Any, vault: LoadedVault, family: ActivityFamily, item_id: str, relation: str, judgment_ids: Sequence[str]) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 227) — Complete-link: the new item judged ``same`` by both passes with every member.
- `_restore_proposals(connection: Any) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 398) — Rebuild disposable workflow cache from immutable decisions and completions.
- `_recover(vault: LoadedVault, repository: Repository, clock: Clock | None, *, proposal_id: str | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/families.py), line 443)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `undo_family`; statically calls `undo_family`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `attach_to_family`, `family_item_input`; statically calls `attach_to_family`, `family_item_input`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `FAMILY_JUDGE_PROMPTS`, `GROUPING_POLICY_VERSION`, `apply_family`, `family_item_input`, `sync_authored_families`; statically calls `apply_family`, `family_item_input`, `sync_authored_families`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `apply_family`, `family_operation_lock`, `sync_authored_families`; statically calls `apply_family`, `family_operation_lock`, `sync_authored_families`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/families|learnloop.db.stores.families]] — imports `append_membership`, `create_proposal`, `ensure_authored_identity`, `record_revision`, `restore_proposal`, `update_proposal_state`, `validate_authored_identity`; calls `append_membership`, `create_proposal`, `ensure_authored_identity`, `record_revision`, `restore_proposal`, `update_proposal_state`, `validate_authored_identity`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`, `resolve_legacy_item`; calls `canonical_hash`, `canonical_json`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `activity_family_hash`; calls `activity_family_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_to_string`; calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `itertools`, `json`, `os`, `pathlib`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/pf_fakes.py](../../../../../../tests/pf_fakes.py) — direct import
- [tests/test_activity_families.py](../../../../../../tests/test_activity_families.py) — direct import
  - `test_apply_idempotency_rejects_changed_payload`
  - `test_apply_undo_preserves_cards_and_owner_edits`
  - `test_authored_family_versions`
  - `test_authored_identity_cannot_claim_legacy_family`
  - `test_auto_family_rechecks_judged_content_from_disk`
  - `test_auto_family_requires_both_independent_passes`
  - `test_complete_link_cannot_chain_pair_judgments`
  - `test_interrupted_apply_can_abort_after_owner_edit`
  - `test_learner_edit_during_family_publication_is_not_lost`
  - `test_membership_replace_cannot_rewrite_history`
  - `test_recovery_after_partial_vault_write`
  - `test_retire_from_a_stale_snapshot_keeps_family_membership`
  - `test_stale_loaded_vault_cannot_regroup_an_accepted_member`
  - `test_undo_conflicting_membership_is_not_overwritten`
  - `test_undo_does_not_revert_owner_family_revision`
  - `test_undo_recovery_after_membership_file_write`
  - `test_undo_uses_immutable_plan_not_workflow`
  - `test_verifier_rejects_unbound_acceptance`
- [tests/test_attach_to_family.py](../../../../../../tests/test_attach_to_family.py) — direct import
  - `test_a_matching_family_is_joined_and_undone`
  - `test_attach_refuses_an_lo_mismatch_and_missing_judgments`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_selection_whose_parent_contract_changed_is_never_published`

## Modification guidance

- Change families policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/families.py](../../../../../../src/learnloop/substrate/families.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
