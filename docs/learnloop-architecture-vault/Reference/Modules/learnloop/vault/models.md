---
title: "learnloop.vault.models"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/models.py"
source_paths:
  - "src/learnloop/vault/models.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.models module"
  - "src/learnloop/vault/models.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.models`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps models behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultModel`, `SourceRef`, `Provenance`, `GoalFacetScope`, `GoalExamConfig`, `Goal`, `GoalsFile`, `SourceSetScope` and 44 more public symbols.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/models.py](../../../../../../src/learnloop/vault/models.py) |
| Source lines | 862 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class VaultModel(BaseModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 13)
- `class SourceRef(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 17)
- `class Provenance(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 33)
- `class GoalFacetScope(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 46)
  - `is_empty(self) -> bool` (line 52; public)
- `class GoalExamConfig(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 56)
- `class Goal(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 61) — A measurable commitment: target recall over a facet set by a due date.
  - `_convert_legacy_concept_anchors(cls, data)` (line 96; internal)
- `class GoalsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 109)
- `class SourceSetScope(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 114) — One unit in a member's scope, with an optional per-unit role override (spec_source_ingestion_v2 §4.3 — a textbook chapter's exercise section can act as a problem set).
- `class SourceSetMember(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 123) — A pinned source in a set.
- `class SourceSet(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 136) — A source collection with pinned revisions (§4.3).
- `class SourceSetsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 150)
- `class Concept(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 155)
- `class ConceptsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 166)
- `class ConceptEdge(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 171)
- `class RelationsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 182)
- `class SubjectMetadata(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 187)
- `class ConceptGraph(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 196)
- `class CriterionTarget(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 204) — What a rubric criterion observes (knowledge-model §5.1).
- `class RubricCriterion(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 217)
- `class RubricFatalError(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 237)
- `class Rubric(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 246)
  - `derive_max_points_from_criteria(self) -> 'Rubric'` (line 252; public) — Treat criterion weights as the scoring authority.
- `class RubricAppliesTo(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 272)
- `class DefaultRubric(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 276)
- `class RecipeComponent(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 288) — One facet-capability requirement inside a recipe (§7.2).
- `class BlueprintRecipe(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 296) — A valid method for satisfying a blueprint (§7.2).
- `class Blueprint(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 312) — A performance blueprint over one or more requirement recipes (§7.2).
- `class LearningObject(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 320)
- `recipe_components(recipe: 'BlueprintRecipe') -> list['RecipeComponent']` ([source](../../../../../../src/learnloop/vault/models.py), line 345) — Every facet-capability component of a recipe, integration included.
- `learning_object_facet_union(lo: 'LearningObject') -> list[str]` ([source](../../../../../../src/learnloop/vault/models.py), line 354) — Derived flat union of every facet referenced by an LO's blueprints (§7.2).
- `class HintPolicy(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 370)
- `class EvidenceFingerprint(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 377) — Global surface/correlation fingerprint (knowledge-model §6).
- `class TraceRecipe(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 392)
- `class TraceContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 398)
  - `validate_trace_contract(self) -> 'TraceContract'` (line 403; public)
- `class VariantManipulation(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 430)
- `class VariantAuthoringContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 436)
- `class DiscriminationProfile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 446) — What a holder of one candidate hypothesis visibly produces (Meas §3.A5).
- `class DifferingComponent(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 502) — The ONE requirement an A4 contrast pair's members differ on (Meas §3.A4).
- `class PlantedError(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 521) — One error planted into an A3 worked solution (Meas §3.A3).
- `class ErrorHuntContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 552) — A fully worked solution the learner must repair (Meas §3.A3).
  - `is_clean(self) -> bool` (line 573; public)
- `class LadderedStemContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 577) — One part of a stimulus whose parts climb the capability ladder (Meas §3.A2).
- `class TeachBackSourceContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 611) — Provenance for a teach-back transformed from one completed item.
- `class PracticeItem(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 626)
- `discriminates(item: 'PracticeItem', rubric: 'Rubric | None'=None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/vault/models.py), line 697) — Item-level view of which misconceptions this item's fatal errors catch.
- `class ErrorType(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 718)
- `class ErrorTypesFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 730)
- `class FacetProvenance(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 755) — Synthesis-time embedded provenance snapshot for a facet (§3.2).
- `class EvidenceFacet(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 766) — A registry entry for an assessable semantic atom (schema_version 2, §3.2).
- `class EvidenceFacetsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 798)
- `class Note(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 803)
- `class Subject` ([source](../../../../../../src/learnloop/vault/models.py), line 817)
- `class DoctorIssue` ([source](../../../../../../src/learnloop/vault/models.py), line 825)
- `class LoadedVault` ([source](../../../../../../src/learnloop/vault/models.py), line 832)
  - `learning_object_for_item(self, item: PracticeItem) -> LearningObject | None` (line 849; public)
  - `subjects_for_item(self, item: PracticeItem) -> list[str]` (line 852; public)
  - `canonical_facet_id(self, facet_id: str) -> str` (line 858; public)
  - `rubric_for_item(self, item: PracticeItem) -> Rubric | None` (line 861; public)

### Module constants

- `CAPABILITY_VOCABULARY` ([src/learnloop/vault/models.py](../../../../../../src/learnloop/vault/models.py), line 738)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `PracticeItem`
- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `PracticeItem`
- [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `CriterionTarget`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `CAPABILITY_VOCABULARY`, `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/coverage_rollup|learnloop.content.synthesis.coverage_rollup]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `Goal`, `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/study_map_diff|learnloop.content.synthesis.study_map_diff]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `LearningObject`, `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/curriculum/golden_path_compose|learnloop.curriculum.golden_path_compose]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning|learnloop.diagnosis.causal_probe_commissioning]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; statically calls `discriminates`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; statically calls `discriminates`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `DiscriminationProfile`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `LoadedVault`, `PlantedError`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `LoadedVault`, `PracticeItem`, `discriminates`; statically calls `discriminates`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `LearningObject`, `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `LearningObject`, `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `discriminates`; statically calls `discriminates`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `LearningObject`, `LoadedVault`
- [[Reference/Modules/learnloop/goals/exam_calibration|learnloop.goals.exam_calibration]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `Goal`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `LearningObject`, `LoadedVault`, `recipe_components`; statically calls `recipe_components`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/goals/goal_intent|learnloop.goals.goal_intent]] — imports `Goal`
- [[Reference/Modules/learnloop/goals/goal_pace|learnloop.goals.goal_pace]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `LearningObject`, `LoadedVault`, `PracticeItem`, `Rubric`, `RubricCriterion`, `RubricFatalError`, `recipe_components`; statically calls `Rubric`, `RubricCriterion`, `RubricFatalError`, `recipe_components`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `Blueprint`, `BlueprintRecipe`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RecipeComponent`
- [[Reference/Modules/learnloop/learner/calibration|learnloop.learner.calibration]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CAPABILITY_VOCABULARY`, `CriterionTarget`, `PracticeItem`, `Rubric`; statically calls `CriterionTarget`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CAPABILITY_VOCABULARY`, `LoadedVault`, `PracticeItem`, `recipe_components`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `LoadedVault`, `recipe_components`; statically calls `recipe_components`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/inference_precheck|learnloop.learner.inference_precheck]] — imports `ConceptEdge`, `LoadedVault`
- [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `LearningObject`, `PracticeItem`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `LoadedVault`, `recipe_components`; statically calls `recipe_components`
- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RelationsFile`, `learning_object_facet_union`, `recipe_components`; statically calls `learning_object_facet_union`, `recipe_components`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/decay_pressure|learnloop.scheduling.decay_pressure]] — imports `Goal`, `LoadedVault`; statically calls `Goal`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/intent_planner|learnloop.scheduling.intent_planner]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `Goal`, `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `LearningObject`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/scheduling/short_session|learnloop.scheduling.short_session]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CriterionTarget`, `LoadedVault`, `PracticeItem`; statically calls `CriterionTarget`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `LearningObject`, `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `RubricCriterion`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `Concept`, `ConceptEdge`, `LearningObject`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `Note`, `PracticeItem`, `RelationsFile`, `SourceSetsFile`, `Subject`, `SubjectMetadata`; statically calls `ConceptGraph`, `DoctorIssue`, `LoadedVault`, `Subject`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `Concept`, `ConceptEdge`, `ErrorType`, `EvidenceFacet`, `LearningObject`, `LoadedVault`, `PracticeItem`, `SourceSet`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `LoadedVault`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `LearningObject`, `recipe_components`; statically calls `recipe_components`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `Goal`, `LoadedVault`; statically calls `Goal`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `ErrorType`, `LearningObject`, `LoadedVault`, `PracticeItem`, `Rubric`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `AttemptType`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]], [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] and 142 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_blueprint_projection.py](../../../../../../tests/test_blueprint_projection.py) — direct import
  - `test_alternative_recipe_success_does_not_credit_bypassed_requirement`
  - `test_any_of_uses_strongest_alternative`
  - `test_compensatory_composition_is_geometric_mean`
  - `test_conjunctive_bottleneck_not_averaged_away`
  - `test_conjunctive_recipe_is_noisy_and_with_slip`
  - `test_facilitating_component_does_not_drag_readiness`
  - `test_integration_facet_enters_as_conjunct`
  - `test_lo_readiness_is_weight_normalized_sum`
  - `test_lo_without_blueprints_returns_none`
  - `test_path_specific_failure_affects_only_the_exercised_path`
  - `test_selected_response_adds_guess_floor`
- [tests/test_capability_mapping.py](../../../../../../tests/test_capability_mapping.py) — direct import
  - `test_authored_targets_override_defaults`
  - `test_legacy_criterion_compiles_to_mode_default_capability`
  - `test_supporting_role_gets_less_mass_than_primary`
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_missing_step_divergence_must_reference_authored_checkpoint`
  - `test_partial_credit_is_positive_projection_evidence_but_not_firewall_protection`
  - `test_passed_facet_and_repair_targets_are_blocked`
- [tests/test_characterization_mastery_reliability.py](../../../../../../tests/test_characterization_mastery_reliability.py) — direct import
- [tests/test_codex_grading_validation.py](../../../../../../tests/test_codex_grading_validation.py) — direct import
  - `test_codex_score_and_max_are_derived_from_criterion_points`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_delivered_passage_on_the_cold_items_own_source_span_is_hard`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_cell_observed_both_ways_is_a_primary_cell`
  - `test_a_facet_observed_at_two_capabilities_is_two_cells`
  - `test_authored_targets_compile_verbatim_including_supporting`
  - `test_conjunctive_fit_prefers_the_capstone_only_when_a_pass_is_likely`
  - `test_conjunctive_strength_saturates_at_the_ceiling`
  - `test_criterion_without_targets_still_compiles_to_all_primary_at_the_item_capability`
  - `test_partition_supporting_targets_splits_on_trace_evidence`
  - `test_single_cell_item_is_not_conjunctive_and_scores_exactly_zero`
- [tests/test_coverage_rollup.py](../../../../../../tests/test_coverage_rollup.py) — direct import
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_item_in_at_most_one_unreleased_pool`
- [tests/test_facet_candidates.py](../../../../../../tests/test_facet_candidates.py) — direct import
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_semantic_fingerprint_deterministic_and_ignores_naming`
- [tests/test_goal_intent.py](../../../../../../tests/test_goal_intent.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_goal_projection_reads_canonical_state`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_a_part_with_no_capability_cannot_be_placed_in_a_column`
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_bare_video_timestamp_resolves_single_cue`
  - `test_dangling_locator_falls_back_to_quote`
  - `test_feedback_resolves_current_ingest_span_and_filename`
  - `test_missing_note_falls_back_to_quote`
  - `test_missing_note_resolves_youtube_ingest_identity`
  - `test_non_displayable_ref_types_skipped`
  - `test_resolves_text_locator_to_section`
  - `test_resolves_video_time_range`
- [tests/test_probe_belief_posterior.py](../../../../../../tests/test_probe_belief_posterior.py) — direct import
- [tests/test_probe_eig.py](../../../../../../tests/test_probe_eig.py) — direct import
  - `test_probe_eig_is_deterministic_and_normalized`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
  - `test_resolve_self_tag_weight_only_fires_for_in_set_non_fatal_label`
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_practice_item_detail_displays_source_name_instead_of_id`
- [tests/test_source_refs.py](../../../../../../tests/test_source_refs.py) — direct import
  - `test_file_source_ref_uses_original_imported_filename`
  - `test_youtube_source_ref_uses_title_captured_during_ingest`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_fractional_asked_subset_is_a_view_not_an_authored_rubric`
  - `test_rubric_tier_defaults_to_core_for_existing_items`

## Modification guidance

- Make changes here when the responsibility remains models within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/models.py](../../../../../../src/learnloop/vault/models.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
