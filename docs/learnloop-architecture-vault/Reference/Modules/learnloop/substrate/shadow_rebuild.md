---
title: "learnloop.substrate.shadow_rebuild"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/shadow_rebuild.py"
source_paths:
  - "src/learnloop/substrate/shadow_rebuild.py"
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
  - "learnloop.substrate.shadow_rebuild module"
  - "src/learnloop/substrate/shadow_rebuild.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.shadow_rebuild`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.shadow_rebuild` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Evaluate a whole-vault rebuild without writing to the live database.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/shadow_rebuild.py](../../../../../../src/learnloop/substrate/shadow_rebuild.py) |
| Source lines | 433 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ShadowRebuildError(RuntimeError)` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 33) — Base error for a shadow rebuild that could not be evaluated safely.
- `class ConfigOverrideError(ShadowRebuildError, ValueError)` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 37) — A ``--set dotted.path=value`` assignment is malformed or invalid.
- `class LiveDatabaseChangedError(ShadowRebuildError)` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 41) — The live SQLite file changed while a shadow rebuild was running.
  - `__init__(self, before: str, after: str)` (line 44; internal)
- `class ShadowRebuildResult` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 54) — Candidate replay result, semantic deltas, and live-isolation proof.
  - `live_database_unchanged(self) -> bool` (line 66; public)
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `build_candidate_config(config: LearnLoopConfig, assignments: Sequence[str]=()) -> tuple[LearnLoopConfig, dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 175) — Return a validated config with repeated dotted assignments applied.
- `shadow_rebuild(vault: LoadedVault, *, assignments: Sequence[str]=()) -> ShadowRebuildResult` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 229) — Replay all history on a scratch DB and compare learner projections.

### Module constants

- `_PROJECTION_SPECS` ([src/learnloop/substrate/shadow_rebuild.py](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 96)

### Explicit exports

`__all__` declares:

- `ConfigOverrideError`
- `LiveDatabaseChangedError`
- `ShadowRebuildError`
- `ShadowRebuildResult`
- `build_candidate_config`
- `shadow_rebuild`

## Internal implementation anchors

- `class _ProjectionSpec` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 86)
- `_parse_override_value(raw_value: str) -> Any` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 294)
- `_sha256_file(path: Path) -> str` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 301)
- `_backup_database(source: Repository, destination: Repository) -> None` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 309) — Make a transactionally consistent copy using the requested attach APIs.
- `_learner_state_snapshot(repository: Repository) -> dict[str, dict[tuple[Any, ...], dict[str, Any]]]` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 319)
- `_semantic_diff(before: Mapping[str, Mapping[tuple[Any, ...], Mapping[str, Any]]], after: Mapping[str, Mapping[tuple[Any, ...], Mapping[str, Any]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 345)
- `_key_fields_for_projection(projection: str) -> frozenset[str]` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 398)
- `_numeric_delta(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> dict[str, int | float]` ([source](../../../../../../src/learnloop/substrate/shadow_rebuild.py), line 405)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `ShadowRebuildError`, `shadow_rebuild`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `OrchestratedRebuildResult`, `rebuild_all_derived_state`; calls `rebuild_all_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `copy`, `dataclasses`, `hashlib`, `json`, `pathlib`, `tempfile`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_shadow_rebuild.py](../../../../../../tests/test_shadow_rebuild.py) — direct import
  - `test_shadow_rebuild_rejects_unknown_override_without_touching_live_db`
  - `test_shadow_rebuild_reports_semantic_diff_and_proves_live_db_isolation`

## Modification guidance

- Change shadow rebuild policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/shadow_rebuild.py](../../../../../../src/learnloop/substrate/shadow_rebuild.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
