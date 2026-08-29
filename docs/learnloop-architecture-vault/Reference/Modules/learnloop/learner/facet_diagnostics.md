---
title: "learnloop.learner.facet_diagnostics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/facet_diagnostics.py"
source_paths:
  - "src/learnloop/learner/facet_diagnostics.py"
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
  - "learnloop.learner.facet_diagnostics module"
  - "src/learnloop/learner/facet_diagnostics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.facet_diagnostics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps facet diagnostics behavior inside its owning package, [[Reference/Modules/learnloop/learner/_package|learnloop.learner]]. Its public surface centers on `entropy`, `normalize_distribution`, `candidate_facet_support`, `required_facets`, `scope_facets`, `coverage_denominator_version`, `contract_frontier`, `lo_relative_coverage` and 7 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py) |
| Source lines | 838 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 30)
- `normalize_distribution(distribution: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 34)
- `candidate_facet_support(item: PracticeItem) -> set[str]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 42)
- `required_facets(vault: LoadedVault, learning_object_id: str, repository: Repository | None=None) -> set[str]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 46) — Facets the LO's ACTIVE authored practice items actually measure.
- `scope_facets(vault: LoadedVault, learning_object_id: str, repository: Repository | None=None) -> set[str]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 71) — Facets an LO is RESPONSIBLE for: blueprint declarations ∪ measured facets.
- `coverage_denominator_version(vault: LoadedVault, repository: Repository | None=None) -> str` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 121) — The version stamped on a rebuild: semantics tag + effective-frontier hash.
- `contract_frontier(vault: LoadedVault, learning_object_id: str, repository: Repository | None=None) -> tuple[set[tuple[str, str]], bool]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 170) — The ``(facet, capability)`` cells this LO's contract actually requires.
- `lo_relative_coverage(vault: LoadedVault, repository: Repository, *, learning_object_id: str, normalized_facet_weights: Mapping[str, float], effective_item_coverage: float) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 227)
- `covered_required_fraction(vault: LoadedVault, repository: Repository, *, learning_object_id: str, aggregate_facet_recall: Mapping[str, FacetRecallState | Mapping[str, Any] | None] | None=None, inferred_cells: Mapping[tuple[str, str], float] | None=None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 279) — Fraction of the contract frontier that carries evidence (§5.2).
- `variance_floor(config: LearnLoopConfig, covered_fraction: float) -> float` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 459)
- `apply_mastery_variance_floor(state: MasteryState, config: LearnLoopConfig, *, covered_fraction: float) -> tuple[MasteryState, float]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 467)
- `build_facet_uncertainty_updates(vault: LoadedVault, *, item: PracticeItem, rubric: Rubric, learning_object_id: str, attempt_id: str, facet_outcomes: Mapping[str, float], normalized_facet_weights: Mapping[str, float], evidence_rows: Iterable[Mapping[str, Any] | Any], error_attributions: Iterable[Any], prior_uncertainties: Mapping[str, FacetUncertaintyState | None], prior_facet_recall: Mapping[str, FacetRecallState | None], observed_error_type: str | None, algorithm_version: str, now_iso: str) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 479)
- `facet_state_label(facet_id: str, uncertainty: FacetUncertaintyState | None, recall: FacetRecallState | None, min_evidence_mass: float) -> str` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 570) — Diagnostic bucket for one required facet.
- `unresolved_question_facet_counts(vault: LoadedVault, repository: Repository, learning_object_id: str, *, recall_states: Mapping[str, FacetRecallState] | None=None, clock: Clock | None=None) -> dict[str, int]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 608) — Recent unresolved tutor questions per facet for one LO.
- `mastery_diagnostic_view(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 658)

### Module constants

- `INFERRED_CELL_COVERAGE_DISCOUNT` ([src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 109)
- `COVERAGE_DENOMINATOR_SEMANTICS` ([src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 115)
- `COVERAGE_DENOMINATOR_VERSION` ([src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 118)
- `_QUESTION_BUMP_WINDOW_DAYS` ([src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 604)
- `_QUESTION_BUMP_MAX_COUNT` ([src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 605)

## Internal implementation anchors

- `_covered_frontier_fraction(vault: LoadedVault, repository: Repository, *, learning_object_id: str, frontier: set[tuple[str, str]], aggregate_facet_recall: Mapping[str, FacetRecallState | Mapping[str, Any] | None] | None, inferred_cells: Mapping[tuple[str, str], float] | None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 360) — Per-cell coverage over the contract frontier.
- `_open_reason(outcome: float, *, hedged: bool, prior_recall: FacetRecallState | None, config: Any) -> str | None` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 730)
- `_facet_uncertainty_id(learning_object_id: str, facet_id: str) -> str` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 748)
- `_initial_hypothesis_marginal(vault: LoadedVault, learning_object_id: str, facet_id: str, error_attributions: Iterable[Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 754)
- `_attribution_targets_facet(vault: LoadedVault, learning_object_id: str, attribution: Any, facet_id: str) -> bool` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 776)
- `_hedged_facets(evidence_rows: Iterable[Mapping[str, Any] | Any], criterion_facets: Mapping[str, Mapping[str, float]], item_facets: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 792)
- `_row_value(row: Mapping[str, Any] | Any, key: str) -> Any` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 811)
- `_facet_outcome_bucket(outcome: float) -> str` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 817)
- `_raise_entropy_floor(distribution: Mapping[str, float], floor: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/facet_diagnostics.py), line 825)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`; statically calls `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `candidate_facet_support`; statically calls `candidate_facet_support`
- [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] — imports `candidate_facet_support`; statically calls `candidate_facet_support`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `required_facets`; statically calls `required_facets`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_state_label`, `scope_facets`; statically calls `facet_state_label`, `scope_facets`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `required_facets`; statically calls `required_facets`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `mastery_diagnostic_view`; statically calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `mastery_diagnostic_view`; statically calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `coverage_denominator_version`; statically calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `entropy`, `facet_state_label`, `normalize_distribution`; statically calls `entropy`, `facet_state_label`, `normalize_distribution`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `mastery_diagnostic_view`, `required_facets`; statically calls `mastery_diagnostic_view`, `required_facets`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `required_facets`; statically calls `required_facets`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `mastery_diagnostic_view`; statically calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `mastery_diagnostic_view`; statically calls `mastery_diagnostic_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `FacetRecallState`, `FacetUncertaintyState`, `MasteryState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `apply_facet_observation`; calls `apply_facet_observation`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `required_capabilities_for_facet`; calls `required_capabilities_for_facet`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`; calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `criterion_facet_weights_for_item`; calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contract_frontier_coverage.py](../../../../../../tests/test_contract_frontier_coverage.py) — direct import
  - `test_a_canonical_vault_with_no_ledger_rows_credits_no_cell`
  - `test_an_lo_with_no_facets_at_all_still_reports_one`
  - `test_capability_axis_distinguishes_the_cells`
  - `test_declaring_a_contract_with_no_instruments_is_zero_not_one`
  - `test_frontier_is_the_blueprint_cells_not_the_authored_items`
  - `test_inference_relieves_the_floor_at_a_discount`
  - `test_legacy_vault_without_blueprints_keeps_current_behaviour`
  - `test_the_denominator_change_is_narrated_as_one_recalibration`
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_a_comment_or_timestamp_touch_does_not_change_the_version`
  - `test_a_null_version_is_not_reported_not_a_rollback`
  - `test_legacy_vault_hashes_the_empty_frontier`
  - `test_removing_a_cell_changes_the_version`
  - `test_version_is_semantics_plus_frontier_hash`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_full_breadth_multi_facet_attempt_keeps_coverage_scale_at_one`
  - `test_mastery_diagnostic_view_distinguishes_known_gap_from_unexamined`
  - `test_tiny_authored_facet_share_does_not_earn_per_facet_coverage`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
  - `test_blueprint_facets_count_when_no_items_are_authored`
  - `test_scope_facets_unions_rather_than_replaces`
- [tests/test_tutor_qa.py](../../../../../../tests/test_tutor_qa.py) — direct import
  - `test_question_raises_diagnostic_uncertainty_read_side`

## Modification guidance

- Change facet diagnostics policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/facet_diagnostics.py](../../../../../../src/learnloop/learner/facet_diagnostics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
