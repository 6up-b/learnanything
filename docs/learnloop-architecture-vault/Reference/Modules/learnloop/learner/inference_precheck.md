---
title: "learnloop.learner.inference_precheck"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/inference_precheck.py"
source_paths:
  - "src/learnloop/learner/inference_precheck.py"
source_commit: "fa47105485871d148098d0025ab42e8da7ba6c29"
source_commit_timestamp: "2026-09-23T12:36:54-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.inference_precheck module"
  - "src/learnloop/learner/inference_precheck.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.inference_precheck`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.inference_precheck` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Static cells-converted precheck for measurement inference rules.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/inference_precheck.py](../../../../../../src/learnloop/learner/inference_precheck.py) |
| Source lines | 578 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fa47105485871d148098d0025ab42e8da7ba6c29` |
| Commit timestamp | `2026-09-23T12:36:54-04:00` |

## Public API

- `class PrerequisiteDisposition(StrEnum)` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 48) — Why one declared prerequisite can or cannot convert upstream cells.
- `class DominanceConversion` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 64) — One baseline-unreachable cell B1 could fill downward.
  - `substitutable_for_certification(self) -> bool` (line 72; public)
  - `as_dict(self) -> dict[str, Any]` (line 78; public)
- `class EntailmentSource` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 90) — A typed prerequisite edge plus the direct downstream observation.
  - `conditional_on_path(self) -> bool` (line 103; public)
  - `as_dict(self) -> dict[str, Any]` (line 106; public)
- `class EntailmentConversion` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 121) — One upstream cell B3 could fill from direct downstream evidence.
  - `substitutable_for_certification(self) -> bool` (line 130; public)
  - `as_dict(self) -> dict[str, Any]` (line 133; public)
- `class PrerequisiteAudit` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 145) — One LO prerequisite declaration and its static eligibility verdict.
  - `as_dict(self) -> dict[str, Any]` (line 158; public)
- `class InferencePrecheckReport` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 173) — B1/B3 counterfactual conversion counts over one reachability baseline.
  - `hard_entailment(self) -> tuple[EntailmentConversion, ...]` (line 184; public)
  - `conditional_entailment(self) -> tuple[EntailmentConversion, ...]` (line 188; public)
  - `_keys(rows: Iterable[DominanceConversion | EntailmentConversion]) -> set[tuple[str, str, str]]` (line 192; internal)
  - `combined_cells_converted(self) -> int` (line 196; public) — Guaranteed static union: B1 plus hard-edge B3, without double count.
  - `combined_maximum_cells_converted(self) -> int` (line 202; public) — Union including path-specific candidates if their paths are exercised.
  - `_share(numerator: int, denominator: int) -> float | None` (line 208; internal)
  - `_rule_summary(self, rows: tuple[DominanceConversion | EntailmentConversion, ...]) -> dict[str, Any]` (line 211; internal)
  - `summary(self) -> dict[str, Any]` (line 226; public)
  - `as_dict(self) -> dict[str, Any]` (line 266; public)
- `analyze_inference_precheck(vault: LoadedVault, *, reachability: ContractReachabilityReport | None=None) -> InferencePrecheckReport` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 558) — Price B1 and B3 against the current static contract-cell baseline.

## Internal implementation anchors

- `_edge_modality(edge: ConceptEdge) -> str` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 276) — Return the explicit edge modality, failing closed when it is absent.
- `_ineligible_disposition(modality: str) -> PrerequisiteDisposition | None` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 285)
- `_dominance_conversions(vault: LoadedVault, baseline: ContractReachabilityReport) -> tuple[DominanceConversion, ...]` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 297)
- `_reachable_by_learning_object(baseline: ContractReachabilityReport) -> dict[str, tuple[CellReachability, ...]]` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 331)
- `_contract_by_learning_object(baseline: ContractReachabilityReport) -> dict[str, tuple[CellReachability, ...]]` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 344)
- `class _DeclaredPrerequisite` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 357) — One downstream LO's declared prerequisite concept and the cells around it.
- `class _EntailmentAnalysis(NamedTuple)` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 398)
- `_declared_prerequisites(vault: LoadedVault, baseline: ContractReachabilityReport) -> Iterator[_DeclaredPrerequisite]` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 405) — Every (downstream LO, prerequisite concept) pair, in LO id then concept order.
- `_edge_disposition(modality: str, prerequisite: _DeclaredPrerequisite) -> PrerequisiteDisposition` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 442) — Whether one typed prerequisite edge can convert its upstream gaps, and if not why.
- `_entailment_conversions(vault: LoadedVault, baseline: ContractReachabilityReport) -> _EntailmentAnalysis` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 459)
- `_merged_conversions(hard_sources: dict[tuple[str, str, str], list[EntailmentSource]], conditional_sources: dict[tuple[str, str, str], list[EntailmentSource]], baseline: ContractReachabilityReport) -> tuple[EntailmentConversion, ...]` ([source](../../../../../../src/learnloop/learner/inference_precheck.py), line 521) — One conversion per upstream cell, conditional only when no hard edge reaches it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `analyze_inference_precheck`; statically calls `analyze_inference_precheck`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `analyze_inference_precheck`; statically calls `analyze_inference_precheck`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CAPABILITY_RANK`, `CONTRACT_MODALITIES`, `CellReachability`, `ContractCell`, `ContractReachabilityReport`, `ReachabilityVerdict`, `analyze_contract_reachability`, `build_instrument_pool`; calls `analyze_contract_reachability`, `build_instrument_pool`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ConceptEdge`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_inference_precheck.py](../../../../../../tests/test_inference_precheck.py) — direct import
  - `test_b1_counts_exactly_mismatch_above_and_combined_union_deduplicates`
  - `test_b3_requires_a_directly_reachable_downstream_anchor`
  - `test_declared_prerequisite_without_a_graph_edge_is_reported_missing`
  - `test_fully_reachable_upstream_contract_has_no_gap_to_convert`
  - `test_hard_edge_sources_name_the_edge_anchor_and_both_learning_objects`
  - `test_path_specific_is_conditional_not_a_guaranteed_conversion`
  - `test_report_is_static_deterministic_and_empty_contracts_are_not_perfect`
  - `test_untyped_and_instructional_edges_convert_nothing`
  - `test_upstream_without_a_contract_converts_nothing`

## Modification guidance

- Change inference precheck policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/inference_precheck.py](../../../../../../src/learnloop/learner/inference_precheck.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
