---
title: "learnloop.substrate.rebuild_orchestrator"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/rebuild_orchestrator.py"
source_paths:
  - "src/learnloop/substrate/rebuild_orchestrator.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.rebuild_orchestrator module"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.rebuild_orchestrator`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.rebuild_orchestrator` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: R2 umbrella for rebuilding every declared derived-state family.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py) |
| Source lines | 471 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DerivedStateReplayer` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 31) — One ordered replay unit and the derived tables it exclusively owns.
- `class ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 40) — Observable accounting from one replay unit.
  - `as_dict(self) -> dict[str, Any]` (line 49; public)
- `class OrchestratedRebuildResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 60) — Whole-vault rebuild result plus the R3 completeness evidence.
  - `as_dict(self) -> dict[str, Any]` (line 73; public)
- `class ReplayerRegistryError(ValueError)` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 89) — The declarative replayer registry is incomplete or ambiguous.
- `class ReplayCompletenessError(RuntimeError)` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 93) — At least one raw attempt was not observed by any registered replayer.
  - `__init__(self, attempt_ids: Sequence[str])` (line 96; internal)
- `derived_table_owners(replayers: Sequence[DerivedStateReplayer]=DERIVED_STATE_REPLAYERS) -> dict[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 149) — Return all declared owners, retaining duplicates for validation.
- `validate_replayer_registry(replayers: Sequence[DerivedStateReplayer]=DERIVED_STATE_REPLAYERS) -> None` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 161) — Require exact, unique DERIVED ownership and valid dependency order.
- `rebuild_all_derived_state(vault: LoadedVault, repository: Repository, *, learning_object_ids: list[str] | None=None, clock: Clock | None=None, require_complete_attempt_coverage: bool=True) -> OrchestratedRebuildResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 386) — Run all registered replayers and append exactly one rebuild receipt.

### Module constants

- `DERIVED_STATE_REPLAYERS` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 107)
- `REPLAYER_REGISTRY` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 146)
- `_RUNNERS` ([src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 378)

### Explicit exports

`__all__` declares:

- `DERIVED_STATE_REPLAYERS`
- `REPLAYER_REGISTRY`
- `DerivedStateReplayer`
- `OrchestratedRebuildResult`
- `ReplayCompletenessError`
- `ReplayerRegistryError`
- `ReplayerResult`
- `derived_table_owners`
- `rebuild_all_derived_state`
- `rebuild_derived_state_umbrella`
- `validate_replayer_registry`

## Internal implementation anchors

- `class _ReplayContext` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 205)
- `_rows_in(repository: Repository, table_names: Sequence[str]) -> int` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 213)
- `_clear_tables(repository: Repository, table_names: Sequence[str]) -> dict[str, int]` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 221) — Delete a replayer's whole declared projection family atomically.
- `_run_activity_substrate(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 229) — Backfill the authoritative activity ledger before learner replay.
- `_run_learning_state(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 256)
- `_run_canonical_projection(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 317)
- `_run_identifiability(spec: DerivedStateReplayer, context: _ReplayContext) -> ReplayerResult` ([source](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py), line 338)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `OrchestratedRebuildResult`, `rebuild_all_derived_state`; statically calls `rebuild_all_derived_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `TableRole`, `tables_for_role`; calls `tables_for_role`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `graph_identifiability_report`; calls `graph_identifiability_report`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`; calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `backfill_activity_substrate`; calls `backfill_activity_substrate`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `rebuild_derived_state`; calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_replayer_registry_owns_each_derived_table_exactly_once`
  - `test_same_version_full_rebuild_is_semantically_idempotent_on_golden_fixture`
  - `test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt`

## Modification guidance

- Change rebuild orchestrator policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/rebuild_orchestrator.py](../../../../../../src/learnloop/substrate/rebuild_orchestrator.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
