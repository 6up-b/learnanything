---
title: "learnloop.substrate.canonical_projection_rollout"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/canonical_projection_rollout.py"
source_paths:
  - "src/learnloop/substrate/canonical_projection_rollout.py"
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
  - "learnloop.substrate.canonical_projection_rollout module"
  - "src/learnloop/substrate/canonical_projection_rollout.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.canonical_projection_rollout`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.canonical_projection_rollout` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Startup ownership for the canonical projection-version boundary.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py) |
| Source lines | 268 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `refresh_canonical_projection_on_startup(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 62) — Refresh the cache and stamp a changed projection baseline exactly once.
- `fold_inputs_fingerprint(vault: LoadedVault, repository: Repository) -> str | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 231) — The fingerprint of every input the canonical fold reads (see the module doc): the database's commit version, the vault fields it reads and the code's versions.
- `forget_fold_memo() -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 263) — Drop the remembered fingerprint and close the watcher (a context closing or switching vault): the next refresh folds.

### Module constants

- `FOLD_VAULT_FIELDS` ([src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 142)
- `_MEMO` ([src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 158)
- `_MEMO_LOCK` ([src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 159)

## Internal implementation anchors

- `class _Memo` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 148) — The database the memo is for, its watcher connection and the fingerprint the last fold that wrote nothing was taken with.
- `_database(repository: Repository) -> str | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 162)
- `_identity(database: str) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 167)
- `_close_locked() -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 175)
- `_commit_version(database: str) -> tuple[tuple[int, int], int, int] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 184) — The database's commit version as the watcher sees it: (identity, ``data_version``, the watcher's own ``total_changes``), or None when it cannot be watched.
- `_vault_digest(vault: LoadedVault) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 214) — One digest over every field of the loaded vault the fold reads (:data:`FOLD_VAULT_FIELDS`), each whole.
- `_remembered(repository: Repository) -> str | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 252)
- `_remember(repository: Repository, fingerprint: str) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 257)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `forget_fold_memo`, `refresh_canonical_projection_on_startup`; statically calls `forget_fold_memo`, `refresh_canonical_projection_on_startup`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `os`, `pathlib`, `sqlite3`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
  - `test_a_fold_racing_a_commit_is_not_remembered`
  - `test_a_noop_refresh_skips_the_fold_and_commits_nothing`
  - `test_a_projection_version_change_forces_the_fold`
  - `test_a_sidecar_reload_after_nothing_happened_skips_the_fold`
  - `test_the_fold_reads_no_vault_field_its_fingerprint_leaves_out`

## Modification guidance

- Change canonical projection rollout policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
