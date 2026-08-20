---
title: "learnloop.content.proposals.apply_protocol"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/apply_protocol.py"
source_paths:
  - "src/learnloop/content/proposals/apply_protocol.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.apply_protocol module"
  - "src/learnloop/content/proposals/apply_protocol.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.apply_protocol`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.apply_protocol` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: Write-ahead apply protocol for proposal acceptance (source-ingestion §10.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/apply_protocol.py](../../../../../../../src/learnloop/content/proposals/apply_protocol.py) |
| Source lines | 515 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `compute_dependency_closure(repository: Repository, requested: list[dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 67) — Split the requested items into an applyable ordered closure and a blocked set (source-ingestion §10.2).
- `stage_target_contents(root: Path, vault: LoadedVault, ordered_items: list[dict[str, Any]], origin: str, patch_id: str, *, clock: Clock | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 158) — Replay the compiled writers against a throwaway staging copy and capture the final target file contents plus the DB side-effect plan.
- `materialize_targets(root: Path, targets: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 313) — Write each target via a staged fsynced temp file and an atomic rename.
- `perform_db_effects(repository: Repository, db_plan: list[dict[str, Any]], *, clock: Clock | None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 360) — Record proposal decisions, content events, and provenance links.
- `recover_apply_intents(root: Path, repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 494) — Complete any apply intent left mid-flight (startup/doctor recovery, §10.2).

### Module constants

- `_STAGING_IGNORE` ([src/learnloop/content/proposals/apply_protocol.py](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 44)
- `_VALID_LINK_RELATIONS` ([src/learnloop/content/proposals/apply_protocol.py](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 55)

## Internal implementation anchors

- `_sha256_bytes(data: bytes) -> str` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 60)
- `_topological_order(repository: Repository, requested_by_id: dict[str, dict[str, Any]], applyable: list[str], deps: dict[str, list[str]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 119)
- `_stamp_side_effect(side_effect: dict[str, Any] | None, patch_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 213) — Stamp the accepting patch id onto a specialized additive side effect (§10.2).
- `_diff_targets(real_root: Path, staging_root: Path) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 223)
- `_is_ignored(rel: Path) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 251)
- `_entity_source_link_rows(entity_type: str, entity_id: str, payload: Any, patch_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 258) — Map a created entity's YAML ``provenance.source_refs`` snapshot into entity_source_links rows (source-ingestion §9.1).
- `_fsync_dir(directory: Path) -> None` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 344)
- `_perform_side_effect(repository: Repository, side_effect: dict[str, Any] | None, created_at: str, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/proposals/apply_protocol.py), line 423) — Apply a specialized additive item's DB write (§10.2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`; statically calls `compute_dependency_closure`, `materialize_targets`, `perform_db_effects`, `stage_target_contents`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `recover_apply_intents`; statically calls `recover_apply_intents`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`; calls `PatchApplicationError`, `_proposal_apply_order`, `compile_proposal_item`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `os`, `pathlib`, `shutil`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_apply_write_ahead.py](../../../../../../../tests/test_apply_write_ahead.py) — direct import
  - `test_crash_between_intent_and_rename_recovers`
  - `test_crash_between_rename_and_applied_mark_recovers`
  - `test_recovery_is_idempotent_and_noop_when_clean`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_specialized_side_effects_recover_idempotently`

## Modification guidance

- Change apply protocol policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/apply_protocol.py](../../../../../../../src/learnloop/content/proposals/apply_protocol.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
