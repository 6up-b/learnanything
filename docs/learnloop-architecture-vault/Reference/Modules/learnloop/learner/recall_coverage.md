---
title: "learnloop.learner.recall_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/recall_coverage.py"
source_paths:
  - "src/learnloop/learner/recall_coverage.py"
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
  - "learnloop.learner.recall_coverage module"
  - "src/learnloop/learner/recall_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.recall_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps recall coverage behavior inside its owning package, [[Reference/Modules/learnloop/learner/_package|learnloop.learner]]. Its public surface centers on `CoverageResult`, `ReliabilityResult`, `FamiliarityResult`, `ErrorImpactResult`, `resolve_coverage`, `scale_coverage_for_graded_criteria`, `resolve_reliability`, `derive_facet_outcomes` and 13 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py) |
| Source lines | 926 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 22)
- `class ReliabilityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 31)
- `class FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 37)
- `class ErrorImpactResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 43)
- `resolve_coverage(item: PracticeItem, rubric: Rubric | None, *, attempt_type: str, hints_used: int, learner_answer_md: str, evidence: EvidenceConfig | None=None) -> CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 49)
- `scale_coverage_for_graded_criteria(coverage: CoverageResult, item: PracticeItem, rubric: Rubric | None, *, criterion_points: Mapping[str, float], transfer_evidence_multiplier: float=1.0) -> CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 99) — Scale per-facet evidence mass by the graded (asked) criterion share.
- `resolve_reliability(item: PracticeItem, *, attempt_type: str, hints_used: int, grader_confidence: float, evidence: EvidenceConfig | None=None) -> ReliabilityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 196)
- `derive_facet_outcomes(item: PracticeItem, rubric: Rubric, *, criterion_points: Mapping[str, float], covered_facets: Mapping[str, float], correctness: float, attempt_type: str, error_attributions: Iterable[Any]=()) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 218)
- `familiarity_discount(repository: Repository, item: PracticeItem, *, learning_object_id: str, covered_facets: Mapping[str, float], config: LearnLoopConfig, exclude_attempt_id: str | None=None) -> FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 274)
- `familiarity_discount_from_attempts(recent: list[dict[str, Any]], item: PracticeItem, *, covered_facets: Mapping[str, float], config: LearnLoopConfig, exclude_attempt_id: str | None=None) -> FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 296)
- `resolve_error_impact(config: LearnLoopConfig, *, error_type: str | None, max_event_severity: float, effective_coverage: float, observation_reliability: float, independent_evidence_discount: float) -> ErrorImpactResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 363)
- `event_local_severity(vault: LoadedVault, repository: Repository, item: PracticeItem, *, error_type: str, learning_object_id: str, attempt_type: str, hints_used: int, correctness: float, expected_correctness: float, effective_coverage: float, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], prior_bad_item_suspicion: float, base_severity: float | None=None, exclude_attempt_id: str | None=None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 398)
- `event_local_severity_from_attempts(vault: LoadedVault, recent: list[dict[str, Any]], item: PracticeItem, *, error_type: str, attempt_type: str, hints_used: int, correctness: float, expected_correctness: float, effective_coverage: float, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], prior_bad_item_suspicion: float, base_severity: float | None=None, exclude_attempt_id: str | None=None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 435)
- `build_facet_recall_updates(repository: Repository, *, learning_object_id: str, practice_item_id: str, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], independent_evidence_discount: float, attempt_type: str, error_event_written: bool, algorithm_version: str, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 510)
- `build_facet_recall_updates_from_prior(prior_states: Mapping[tuple[str, str | None], Any], *, learning_object_id: str, practice_item_id: str, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], independent_evidence_discount: float, attempt_type: str, error_event_written: bool, algorithm_version: str, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 543)
- `build_quality_state_update(repository: Repository, *, item: PracticeItem, prior_mastery: MasteryState, correctness: float, grader_confidence: float, now_iso: str, algorithm_version: str, exclude_attempt_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 596)
- `build_quality_state_update_from_prior(prior: Any, *, recent_failures: int, item_id: str, prior_mastery: MasteryState, correctness: float, grader_confidence: float, now_iso: str, algorithm_version: str, assessment_side_error: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 626)
- `predicted_correctness(repository: Repository, item: PracticeItem, *, learning_object_id: str, prior_mastery: MasteryState, item_a: float, item_b: float, config: LearnLoopConfig, vault: LoadedVault | None=None) -> tuple[float, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 681)
- `predicted_correctness_from_prior(facet_states: Mapping[str, Any], item: PracticeItem, *, prior_mastery: MasteryState, item_a: float, item_b: float, config: LearnLoopConfig) -> tuple[float, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 717)
- `expected_facet_mass_gain(item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 785) — Nominal per-facet evidence mass one fresh attempt on ``item`` would add.
- `criterion_facet_weights_for_item(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 813)

### Module constants

- `_GENERIC_FACET_TOKENS` ([src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py), line 855)

## Internal implementation anchors

- `_resolve_error_impact_config(config: LearnLoopConfig, error_type: str)` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 342) — Look up an ``[error_impacts]`` entry, resolving legacy keys via §10.1.
- `_raw_coverage(item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None=None) -> tuple[dict[str, float], float, str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 753)
- `_error_attributed_facets(error_attributions: Iterable[Any]) -> set[str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 803)
- `_inferred_criterion_facet_weights(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 819) — Best-effort fallback for older/generated items missing facet metadata.
- `_facet_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 873)
- `_practice_mode_default(item: PracticeItem, evidence: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 891)
- `_normalize(weights: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 895)
- `_response_engagement_factor(attempt_type: str, learner_answer_md: str) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 903)
- `_component_discount(target_discount: float, recent_overlap_mass: float) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 913)
- `_hint_policy_product(mapping: Mapping[int | str, float], hints_used: int, *, default: float) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 917)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `build_facet_recall_updates`, `build_facet_recall_updates_from_prior`, `build_quality_state_update`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity`, `event_local_severity_from_attempts`, `familiarity_discount`, `familiarity_discount_from_attempts`, `predicted_correctness`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`; statically calls `build_facet_recall_updates_from_prior`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity_from_attempts`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `criterion_facet_weights_for_item`, `resolve_coverage`; statically calls `criterion_facet_weights_for_item`, `resolve_coverage`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `familiarity_discount`; statically calls `familiarity_discount`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `expected_facet_mass_gain`; statically calls `expected_facet_mass_gain`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `criterion_facet_weights_for_item`; statically calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`; statically calls `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `criterion_facet_weights_for_item`; statically calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `criterion_facet_weights_for_item`; statically calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `predicted_correctness`; statically calls `predicted_correctness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`, `attempt_surface_exposure`, `practice_mode_item_coverage`; calls `attempt_evidence_mass`, `attempt_surface_exposure`, `practice_mode_item_coverage`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `EvidenceConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MasteryState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_state_for_lo`; calls `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_mastery_reliability.py](../../../../../../tests/test_characterization_mastery_reliability.py) — direct import
  - `test_error_impact_turns_reliability_into_observation_weight`
  - `test_resolve_reliability_applies_per_hint_dampening_product`
  - `test_resolve_reliability_is_product_of_confidence_hint_and_attempt_mass`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_quality_state_pays_for_assessment_side_error`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_full_breadth_multi_facet_attempt_keeps_coverage_scale_at_one`
  - `test_tiny_authored_facet_share_does_not_earn_per_facet_coverage`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_attempts_to_certify_inverts_the_mass_equation`
  - `test_legacy_lo_without_a_contract_is_untouched`
- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_config_error_impacts_resolve_through_map`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_first_attempt_carries_familiarity_discount`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_derive_facet_outcomes_skips_ungraded_criteria`

## Modification guidance

- Change recall coverage policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
