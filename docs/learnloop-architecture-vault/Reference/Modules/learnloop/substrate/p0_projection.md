---
title: "learnloop.substrate.p0_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/p0_projection.py"
source_paths:
  - "src/learnloop/substrate/p0_projection.py"
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
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.p0_projection module"
  - "src/learnloop/substrate/p0_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.p0_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.p0_projection` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P0.3 projection cutover + reinterpretation receipts (spec §4.2, §7.2).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/p0_projection.py](../../../../../../src/learnloop/substrate/p0_projection.py) |
| Source lines | 128 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `activate_p0_projection(vault: LoadedVault, repository: Repository, *, from_version: str=KM_ALGORITHM_VERSION, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 33) — Rebuild + record activation of the mvp-0.8 projection (§7.2).
- `leading_conclusion(interpretation: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 78) — The leading actionable conclusion of an interpretation: the top true class of its response posterior (§2.3).
- `record_reinterpretation_if_changed(repository: Repository, *, administration_id: str, observation_id: str, from_interpretation: Mapping[str, Any] | None, to_interpretation: Mapping[str, Any] | None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 90) — Append a ``measurement_reinterpretation`` event when the leading actionable conclusion changed between two interpretations (§2.3).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `record_reinterpretation_if_changed`; statically calls `record_reinterpretation_if_changed`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]], [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_activation_records_derived_state_rebuild`
  - `test_adjudication_reverses_projection_and_preserves_history`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`

## Modification guidance

- Change p0 projection policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/p0_projection.py](../../../../../../src/learnloop/substrate/p0_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
