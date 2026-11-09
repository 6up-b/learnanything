---
title: "learnloop.learner.recall_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/recall_coverage.py"
source_paths:
  - "src/learnloop/learner/recall_coverage.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps recall coverage behavior inside its owning package, [[Reference/Modules/learnloop/learner/_package|learnloop.learner]]. Its public surface centers on `CoverageResult`, `ReliabilityResult`, `FamiliarityResult`, `ErrorImpactResult`, `resolve_coverage`, `scale_coverage_for_graded_criteria`, `resolve_reliability`, `derive_facet_outcomes` and 14 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py) |
| Source lines | 1026 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 24)
- `class ReliabilityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 33)
- `class FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 39)
- `class ErrorImpactResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 45)
- `resolve_coverage(item: PracticeItem, rubric: Rubric | None, *, attempt_type: str, hints_used: int, learner_answer_md: str, evidence: EvidenceConfig | None=None, declared_stuck: bool=False) -> CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 51)
- `scale_coverage_for_graded_criteria(coverage: CoverageResult, item: PracticeItem, rubric: Rubric | None, *, criterion_points: Mapping[str, float], transfer_evidence_multiplier: float=1.0, criterion_facet_weights: Mapping[str, Mapping[str, float]] | None=None) -> CoverageResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 104) — Scale per-facet evidence mass by the graded (asked) criterion share.
- `resolve_reliability(item: PracticeItem, *, attempt_type: str, hints_used: int, grader_confidence: float, evidence: EvidenceConfig | None=None, attempt_type_mass: float | None=None) -> ReliabilityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 209) — ``attempt_type_mass``: this attempt's own mass when one was recorded for it (a lesson check's learned mass, teacher TE1 §12.1); None uses the type's configured mass.
- `derive_facet_outcomes(item: PracticeItem, rubric: Rubric, *, criterion_points: Mapping[str, float], covered_facets: Mapping[str, float], correctness: float, attempt_type: str, error_attributions: Iterable[Any]=(), criterion_facet_weights: Mapping[str, Mapping[str, float]] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 237)
- `familiarity_discount(repository: Repository, item: PracticeItem, *, learning_object_id: str, covered_facets: Mapping[str, float], config: LearnLoopConfig, exclude_attempt_id: str | None=None) -> FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 308)
- `familiarity_discount_from_attempts(recent: list[dict[str, Any]], item: PracticeItem, *, covered_facets: Mapping[str, float], config: LearnLoopConfig, exclude_attempt_id: str | None=None) -> FamiliarityResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 330)
- `resolve_error_impact(config: LearnLoopConfig, *, error_type: str | None, max_event_severity: float, effective_coverage: float, observation_reliability: float, independent_evidence_discount: float) -> ErrorImpactResult` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 400)
- `event_local_severity(vault: LoadedVault, repository: Repository, item: PracticeItem, *, error_type: str, learning_object_id: str, attempt_type: str, hints_used: int, correctness: float, expected_correctness: float, effective_coverage: float, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], prior_bad_item_suspicion: float, base_severity: float | None=None, exclude_attempt_id: str | None=None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 435)
- `event_local_severity_from_attempts(vault: LoadedVault, recent: list[dict[str, Any]], item: PracticeItem, *, error_type: str, attempt_type: str, hints_used: int, correctness: float, expected_correctness: float, effective_coverage: float, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], prior_bad_item_suspicion: float, base_severity: float | None=None, exclude_attempt_id: str | None=None) -> tuple[float, dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 474)
- `build_facet_recall_updates(repository: Repository, *, learning_object_id: str, practice_item_id: str, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], independent_evidence_discount: float, attempt_type: str, error_event_written: bool, algorithm_version: str, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 550)
- `build_facet_recall_updates_from_prior(prior_states: Mapping[tuple[str, str | None], Any], *, learning_object_id: str, practice_item_id: str, covered_facets: Mapping[str, float], facet_outcomes: Mapping[str, float], independent_evidence_discount: float, attempt_type: str, error_event_written: bool, algorithm_version: str, now_iso: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 583)
- `build_quality_state_update(repository: Repository, *, item: PracticeItem, prior_mastery: MasteryState, correctness: float, grader_confidence: float, now_iso: str, algorithm_version: str, exclude_attempt_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 636)
- `build_quality_state_update_from_prior(prior: Any, *, recent_failures: int, item_id: str, prior_mastery: MasteryState, correctness: float, grader_confidence: float, now_iso: str, algorithm_version: str, assessment_side_error: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 669)
- `predicted_correctness(repository: Repository, item: PracticeItem, *, learning_object_id: str, prior_mastery: MasteryState, item_a: float, item_b: float, config: LearnLoopConfig, vault: LoadedVault | None=None) -> tuple[float, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 725)
- `predicted_correctness_from_prior(facet_states: Mapping[str, Any], item: PracticeItem, *, prior_mastery: MasteryState, item_a: float, item_b: float, config: LearnLoopConfig) -> tuple[float, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 772)
- `expected_facet_mass_gain(item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 840) — Nominal per-facet evidence mass one fresh attempt on ``item`` would add.
- `criterion_facet_weights_for_item(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 868)
- `target_criterion_facet_weights(item: PracticeItem, rubric: Rubric, *, resolve: Callable[[str], str] | None=None) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 874) — Each criterion's item facets, read from the rubric's observation contract.

### Module constants

- `_GENERIC_FACET_TOKENS` ([src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py), line 956)
- `_FACET_TOKEN_STOP_WORDS` ([src/learnloop/learner/recall_coverage.py](../../../../../../src/learnloop/learner/recall_coverage.py), line 974)

## Internal implementation anchors

- `_with_held_marked(repository: Repository, rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 300) — ``rows`` with THE held predicate's mark (held-grade-evidence).
- `_resolve_error_impact_config(config: LearnLoopConfig, error_type: str)` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 379) — Look up an ``[error_impacts]`` entry, resolving legacy keys via §10.1.
- `_raw_coverage(item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None=None) -> tuple[dict[str, float], float, str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 808)
- `_error_attributed_facets(error_attributions: Iterable[Any]) -> set[str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 858)
- `_inferred_criterion_facet_weights(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 920) — Best-effort fallback for older/generated items missing facet metadata.
- `_facet_tokens(value: str) -> set[str]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 977) — Lower-case alphanumeric words of a facet id or text, without stop words.
- `_practice_mode_default(item: PracticeItem, evidence: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 984)
- `_normalize(weights: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 988)
- `_response_engagement_factor(attempt_type: str, learner_answer_md: str, *, declared_stuck: bool=False) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 996)
- `_component_discount(target_discount: float, recent_overlap_mass: float) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 1013)
- `_hint_policy_product(mapping: Mapping[int | str, float], hints_used: int, *, default: float) -> float` ([source](../../../../../../src/learnloop/learner/recall_coverage.py), line 1017)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `build_facet_recall_updates`, `build_facet_recall_updates_from_prior`, `build_quality_state_update`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity`, `event_local_severity_from_attempts`, `familiarity_discount`, `familiarity_discount_from_attempts`, `predicted_correctness`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`; statically calls `build_facet_recall_updates_from_prior`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity_from_attempts`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `criterion_facet_weights_for_item`, `resolve_coverage`; statically calls `criterion_facet_weights_for_item`, `resolve_coverage`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `familiarity_discount`; statically calls `familiarity_discount`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `derive_facet_outcomes`, `familiarity_discount_from_attempts`, `resolve_coverage`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`; statically calls `derive_facet_outcomes`, `familiarity_discount_from_attempts`, `resolve_coverage`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `expected_facet_mass_gain`; statically calls `expected_facet_mass_gain`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `familiarity_discount`; statically calls `familiarity_discount`
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
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `mark_held_attempts`; calls `mark_held_attempts`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `ROLE_WEIGHTS`, `compile_criterion_targets`; calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetStateReader`, `facet_recall_state_for_lo`, `is_canonical_state_vault`; calls `CanonicalFacetStateReader`, `facet_recall_state_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] and 6 more.

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
- [tests/test_learner_read_model_pinning.py](../../../../../../tests/test_learner_read_model_pinning.py) — direct import
  - `test_predicted_correctness_with_one_shared_reader_is_byte_identical`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_an_ordinary_item_gives_the_unverified_criterion_s_facet_nothing`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_first_attempt_carries_familiarity_discount`
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_facet_tokens_split_ids_into_words_without_stop_words`
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
