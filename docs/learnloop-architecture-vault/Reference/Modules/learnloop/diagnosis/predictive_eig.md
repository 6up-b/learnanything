---
title: "learnloop.diagnosis.predictive_eig"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/predictive_eig.py"
source_paths:
  - "src/learnloop/diagnosis/predictive_eig.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.predictive_eig module"
  - "src/learnloop/diagnosis/predictive_eig.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.predictive_eig`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.predictive_eig` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Predictive facet EIG (Adaptive Elicitation, arXiv 2504.04204).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/predictive_eig.py](../../../../../../src/learnloop/diagnosis/predictive_eig.py) |
| Source lines | 231 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TargetItemModel` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 36) — Precomputed static per-item inputs, built once per slate and reused across all candidates.
- `class PredictiveEigResult` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 48)
- `build_target_models(vault: LoadedVault, *, learning_object_id: str, exclude_item_ids: set[str], facet_ids: set[str], cap: int) -> dict[str, list[TargetItemModel]]` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 55) — Per open facet: the LO's items whose candidate support probes the facet, excluding the source attempt's item, capped at ``cap``.
- `predictive_facet_eig(hypothesis_marginal: dict[str, float], *, facet_id: str, candidate_support: set[str], candidate_fatal_error_ids: set[str], candidate_a: float, candidate_b: float, targets: list[TargetItemModel], candidate_item_id: str | None=None, irt: ProbeIRTConfig | None=None) -> PredictiveEigResult` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 130)

## Internal implementation anchors

- `_stratified_cap(candidates: list[TargetItemModel], strata: dict[str, tuple[str, str]], cap: int) -> list[TargetItemModel]` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 109) — Round-robin the cap across strata (deterministic: strata and members id-sorted).
- `_normalized(marginal: dict[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 218)
- `_entropy(distribution: dict) -> float` ([source](../../../../../../src/learnloop/diagnosis/predictive_eig.py), line 226)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `TargetItemModel`, `build_target_models`, `predictive_facet_eig`; statically calls `build_target_models`, `predictive_facet_eig`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `ProbeIRTConfig`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `apply_facet_observation`, `facet_conditional_distribution`, `resolve_item_irt`; calls `apply_facet_observation`, `facet_conditional_distribution`, `resolve_item_irt`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `candidate_facet_support`; calls `candidate_facet_support`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_round_robin_across_strata`
  - `test_under_cap_returns_all`
- [tests/test_predictive_eig.py](../../../../../../tests/test_predictive_eig.py) — direct import

## Modification guidance

- Change predictive eig policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/predictive_eig.py](../../../../../../src/learnloop/diagnosis/predictive_eig.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
