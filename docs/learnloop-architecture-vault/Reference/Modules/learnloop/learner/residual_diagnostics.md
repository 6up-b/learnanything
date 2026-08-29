---
title: "learnloop.learner.residual_diagnostics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/residual_diagnostics.py"
source_paths:
  - "src/learnloop/learner/residual_diagnostics.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.residual_diagnostics module"
  - "src/learnloop/learner/residual_diagnostics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.residual_diagnostics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.residual_diagnostics` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Residual-dependence diagnostics (knowledge-model §8.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py) |
| Source lines | 309 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `residual_dependence_report(vault: LoadedVault, repository: Repository, *, subject_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 260) — The §8.4 residual-dependence diagnostics report (report-only, deterministic).

### Module constants

- `MIN_JOINT_ATTEMPTS` ([src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 36)
- `RESIDUAL_DEPENDENCE_THRESHOLD` ([src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 38)
- `COMBINED_FAILURE_THRESHOLD` ([src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 40)
- `COMPONENT_STRONG_THRESHOLD` ([src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 41)
- `CONTEXT_DIVERGENCE_THRESHOLD` ([src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 43)

## Internal implementation anchors

- `_facet_outcomes_per_attempt(vault: LoadedVault, repository: Repository, scoped_los: set[str] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 46) — Per-attempt facet pass/fail + surface group (deterministic, ledger order).
- `_residual_dependence_suggestions(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 86) — Positive residual co-failure between co-tasked facets (missing factor).
- `_integration_suggestions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 133) — Systematic combined-task failure with strong components (missing integration).
- `_context_divergence_suggestions(vault: LoadedVault, repository: Repository, scoped_facets: set[str] | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 183) — Capability-sliced belief spread within a facet (transfer / capability hint).
- `_identifiability_referrals(vault: LoadedVault, repository: Repository, subject_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/residual_diagnostics.py), line 223) — Indistinguishable response signatures -> hand off to the §11.3 doctor.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `residual_dependence_report`; statically calls `residual_dependence_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`; calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_registry_view`; calls `analyze_identifiability`, `build_registry_view`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `FAILURE_THRESHOLD`, `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `recipe_components`; calls `recipe_components`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_residual_diagnostics.py](../../../../../../tests/test_residual_diagnostics.py) — direct import
  - `test_capability_divergence_hint`
  - `test_positive_residual_dependence_flags_missing_factor`

## Modification guidance

- Change residual diagnostics policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/residual_diagnostics.py](../../../../../../src/learnloop/learner/residual_diagnostics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
