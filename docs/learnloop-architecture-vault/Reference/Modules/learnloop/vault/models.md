---
title: "learnloop.vault.models"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/models.py"
source_paths:
  - "src/learnloop/vault/models.py"
source_commit: "1ef2f14ebf6f15de8b60736f60650017d40712d3"
source_commit_timestamp: "2026-10-15T12:39:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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

This module keeps models behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultModel`, `SourceRef`, `Provenance`, `GoalFacetScope`, `GoalExamConfig`, `Goal`, `GoalsFile`, `SourceSetScope` and 48 more public symbols.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/models.py](../../../../../../src/learnloop/vault/models.py) |
| Source lines | 1032 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ef2f14ebf6f15de8b60736f60650017d40712d3` |
| Commit timestamp | `2026-10-15T12:39:41-04:00` |

## Public API

- `class VaultModel(BaseModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 14)
- `class SourceRef(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 18)
- `class Provenance(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 34)
- `class GoalFacetScope(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 47)
  - `is_empty(self) -> bool` (line 53; public)
- `class GoalExamConfig(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 57)
- `class Goal(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 62) — A measurable commitment: target recall over a facet set by a due date.
  - `_convert_legacy_concept_anchors(cls, data)` (line 97; internal)
- `class GoalsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 110)
- `class SourceSetScope(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 115) — One unit in a member's scope, with an optional per-unit role override (spec_source_ingestion_v2 §4.3 — a textbook chapter's exercise section can act as a problem set).
- `class SourceSetMember(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 124) — A pinned source in a set.
  - `_omit_unrecorded_scope_reading(self, handler: Any) -> Any` (line 153; internal)
- `class SourceSet(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 162) — A source collection with pinned revisions (§4.3).
- `class SourceSetsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 176)
- `class Concept(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 181)
- `class ConceptsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 192)
- `class ConceptEdge(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 197)
- `class RelationsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 208)
- `class SubjectMetadata(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 213)
- `class ConceptGraph(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 222)
- `class CriterionTarget(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 230) — What a rubric criterion observes (knowledge-model §5.1).
- `class RubricCriterion(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 243)
- `class RubricFatalError(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 263)
- `class Rubric(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 272)
  - `derive_max_points_from_criteria(self) -> 'Rubric'` (line 278; public) — Treat criterion weights as the scoring authority.
- `class RubricAppliesTo(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 298)
- `class DefaultRubric(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 302)
- `class RecipeComponent(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 314) — One facet-capability requirement inside a recipe (§7.2).
- `class BlueprintRecipe(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 322) — A valid method for satisfying a blueprint (§7.2).
- `class Blueprint(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 338) — A performance blueprint over one or more requirement recipes (§7.2).
- `class LearningObject(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 346)
- `recipe_components(recipe: 'BlueprintRecipe') -> list['RecipeComponent']` ([source](../../../../../../src/learnloop/vault/models.py), line 371) — Every facet-capability component of a recipe, integration included.
- `learning_object_facet_union(lo: 'LearningObject') -> list[str]` ([source](../../../../../../src/learnloop/vault/models.py), line 380) — Derived flat union of every facet referenced by an LO's blueprints (§7.2).
- `class HintPolicy(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 396)
- `class EvidenceFingerprint(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 403) — Global surface/correlation fingerprint (knowledge-model §6).
- `class TraceRecipe(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 418)
- `class TraceContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 424)
  - `validate_trace_contract(self) -> 'TraceContract'` (line 429; public)
- `class VariantManipulation(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 456)
- `class VariantAuthoringContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 462)
- `class DiscriminationProfile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 472) — What a holder of one candidate hypothesis visibly produces (Meas §3.A5).
- `class DifferingComponent(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 528) — The ONE requirement an A4 contrast pair's members differ on (Meas §3.A4).
- `class PlantedError(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 547) — One error planted into an A3 worked solution (Meas §3.A3).
- `class ErrorHuntContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 578) — A fully worked solution the learner must repair (Meas §3.A3).
  - `is_clean(self) -> bool` (line 599; public)
- `class LadderedStemContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 603) — One part of a stimulus whose parts climb the capability ladder (Meas §3.A2).
- `class TeachBackSourceContract(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 637) — Provenance for a teach-back transformed from one completed item.
- `class FamilyReference(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 655) — Minimal reference status; verification must name its performed check.
  - `_verified_check(self) -> FamilyReference` (line 662; internal)
- `class ActivityFamily(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 668) — Versioned authored content of a purpose-practice activity family.
- `class RequiredMethod(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 687) — The method an item's own statement requires (owner rule, 2026-10-13).
- `class CanonicalExercise(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 735) — The textbook exercise a practice item presents (canonical sources S1, §7.4).
- `class PracticeItem(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 752)
  - `_family_relationship(self) -> PracticeItem` (line 850; internal)
  - `_omit_absent_family_fields(self, handler: Any) -> dict[str, Any]` (line 858; internal)
- `discriminates(item: 'PracticeItem', rubric: 'Rubric | None'=None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/vault/models.py), line 866) — Item-level view of which misconceptions this item's fatal errors catch.
- `class ErrorType(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 887)
- `class ErrorTypesFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 899)
- `class FacetProvenance(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 924) — Synthesis-time embedded provenance snapshot for a facet (§3.2).
- `class EvidenceFacet(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 935) — A registry entry for an assessable semantic atom (schema_version 2, §3.2).
- `class EvidenceFacetsFile(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 967)
- `class Note(VaultModel)` ([source](../../../../../../src/learnloop/vault/models.py), line 972)
- `class Subject` ([source](../../../../../../src/learnloop/vault/models.py), line 986)
- `class DoctorIssue` ([source](../../../../../../src/learnloop/vault/models.py), line 994)
- `class LoadedVault` ([source](../../../../../../src/learnloop/vault/models.py), line 1001)
  - `learning_object_for_item(self, item: PracticeItem) -> LearningObject | None` (line 1019; public)
  - `subjects_for_item(self, item: PracticeItem) -> list[str]` (line 1022; public)
  - `canonical_facet_id(self, facet_id: str) -> str` (line 1028; public)
  - `rubric_for_item(self, item: PracticeItem) -> Rubric | None` (line 1031; public)

### Module constants

- `CAPABILITY_VOCABULARY` ([src/learnloop/vault/models.py](../../../../../../src/learnloop/vault/models.py), line 907)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `CanonicalExercise`, `PracticeItem`, `SourceRef`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `PracticeItem`
- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `PracticeItem`
- [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `CriterionTarget`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/draft_validation|learnloop.content.authoring.draft_validation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/laddered_stems|learnloop.content.authoring.laddered_stems]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `EvidenceFacet`, `EvidenceFacetsFile`, `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `EvidenceFacet`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `EvidenceFacet`, `LoadedVault`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `CAPABILITY_VOCABULARY`, `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/coverage_rollup|learnloop.content.synthesis.coverage_rollup]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `Goal`, `LoadedVault`, `SourceSet`
- [[Reference/Modules/learnloop/content/synthesis/study_map_diff|learnloop.content.synthesis.study_map_diff]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_manifests|learnloop.content.synthesis.synthesis_manifests]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/golden_path_compose|learnloop.curriculum.golden_path_compose]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
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
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `LoadedVault`
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
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `ConceptEdge`, `LoadedVault`, `RelationsFile`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
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
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/instructional/offers|learnloop.instructional.offers]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `Goal`
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
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RelationsFile`, `learning_object_facet_union`, `recipe_components`; statically calls `learning_object_facet_union`, `recipe_components`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`; statically calls `ActivityFamily`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `ActivityFamily`, `FamilyReference`, `LoadedVault`, `PracticeItem`; statically calls `ActivityFamily`, `FamilyReference`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/placement/claim_check|learnloop.placement.claim_check]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `EvidenceFacet`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `EvidenceFacet`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/practice_index/tool|learnloop.practice_index.tool]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `DoctorIssue`, `LoadedVault`; statically calls `DoctorIssue`
- [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
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
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `LoadedVault`, `PracticeItem`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `Goal`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CriterionTarget`, `LoadedVault`, `PracticeItem`; statically calls `CriterionTarget`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `LearningObject`, `LoadedVault`, `learning_object_facet_union`; statically calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `RubricCriterion`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EvidenceFacet`, `LoadedVault`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `ActivityFamily`, `Concept`, `ConceptEdge`, `LearningObject`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `ActivityFamily`, `ConceptGraph`, `ConceptsFile`, `DefaultRubric`, `DoctorIssue`, `ErrorTypesFile`, `EvidenceFacetsFile`, `GoalsFile`, `LearningObject`, `LoadedVault`, `Note`, `PracticeItem`, `RelationsFile`, `SourceSetsFile`, `Subject`, `SubjectMetadata`, `recipe_components`; statically calls `ConceptGraph`, `DoctorIssue`, `LoadedVault`, `Subject`, `recipe_components`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `ActivityFamily`, `Concept`, `ConceptEdge`, `ErrorType`, `EvidenceFacet`, `LearningObject`, `LoadedVault`, `PracticeItem`, `SourceSet`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `LoadedVault`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `LearningObject`, `recipe_components`; statically calls `recipe_components`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `Goal`, `LoadedVault`; statically calls `Goal`
- [[Reference/Modules/learnloop_sidecar/handlers/item_text_neighbors|learnloop_sidecar.handlers.item_text_neighbors]] — imports `LoadedVault`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `ErrorType`, `LearningObject`, `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `LoadedVault`, `PracticeItem`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `AttemptType`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/vault/scope_seal|learnloop.vault.scope_seal]] — imports `scope_seal`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]], [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] and 291 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/passage_cue_fakes.py](../../../../../../tests/passage_cue_fakes.py) — direct import
- [tests/pf_fakes.py](../../../../../../tests/pf_fakes.py) — direct import
- [tests/test_activity_families.py](../../../../../../tests/test_activity_families.py) — direct import
  - `test_absent_fields_are_byte_identical_to_pre_family_model`
  - `test_ensemble_source_kind_loads_and_round_trips`
  - `test_family_schema_and_loader_relationships`
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id`
  - `test_historical_snapshots_of_held_out_material_are_never_audited`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_stale_run_never_answers_for_a_re_proposal`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_surface_group_mirrors_the_projection`
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_relatedness_proposal_reads_no_learner_or_held_out_data`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_held_out_sentinel_never_reaches_ad_inputs`
- [tests/test_attach_to_family.py](../../../../../../tests/test_attach_to_family.py) — direct import
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
- [tests/test_canonical_exercise_serialization.py](../../../../../../tests/test_canonical_exercise_serialization.py) — direct import
  - `test_a_pf_variant_of_a_textbook_exercise_points_at_it`
  - `test_an_empty_span_list_is_refused`
  - `test_round_trip_and_hash_independence`
- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
  - `test_the_fold_reads_no_vault_field_its_fingerprint_leaves_out`
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
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_exam_leakage_shortlists_nearest_held_out_spans_for_the_judge`
- [tests/test_coverage_rollup.py](../../../../../../tests/test_coverage_rollup.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f8_out_of_range_expected_minutes_reach_the_writer_bounded`
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_teach_back_source_on_any_mode_is_the_multi_turn_reason`
  - `test_each_contract_reason_is_returned_for_the_phone_and_never_for_the_desktop`
  - `test_item_kinds_landed_since_the_spec_keep_the_ordinary_answer`
- [tests/test_duration_estimates.py](../../../../../../tests/test_duration_estimates.py) — direct import
  - `test_expected_minutes_is_optional_omitted_when_null_and_outside_the_hash`
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
- [tests/test_embedding_recipe_hash_pins.py](../../../../../../tests/test_embedding_recipe_hash_pins.py) — direct import
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_item_in_at_most_one_unreleased_pool`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_an_item_made_from_held_out_material_is_exam_material`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading`
  - `test_f14_a_refresh_never_drops_signal_only_protection`
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_pf_never_forwards_a_held_out_parent_quote`
- [tests/test_facet_candidates.py](../../../../../../tests/test_facet_candidates.py) — direct import
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_a_merge_rekeys_evidence_and_undo_restores_facets_and_evidence_exactly`
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
- [tests/test_facet_outcome_view.py](../../../../../../tests/test_facet_outcome_view.py) — direct import
  - `test_partial_fractional_criterion_uses_assessed_denominator`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_semantic_fingerprint_deterministic_and_ignores_naming`
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
  - `test_library_question_targets_only_its_notes_learning_objects`
- [tests/test_goal_intent.py](../../../../../../tests/test_goal_intent.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
  - `test_concept_queries_carry_their_linked_definitions`
- [tests/test_graph_nomination_report.py](../../../../../../tests/test_graph_nomination_report.py) — direct import
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_goal_projection_reads_canonical_state`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_a_part_with_no_capability_cannot_be_placed_in_a_column`
- [tests/test_library_ask_expand.py](../../../../../../tests/test_library_ask_expand.py) — direct import
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_check_recorded_on_main_still_verifies_and_the_fresh_check_label_needs_a_change`
  - `test_a_plan_rows_preview_keeps_the_sentence_whole`
  - `test_check_me_keeps_the_sentence_whole_when_it_clips`
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
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
- [tests/test_reader_ca5a_find_section.py](../../../../../../tests/test_reader_ca5a_find_section.py) — direct import
  - `test_a_peeked_paragraph_that_is_the_replacement_surfaces_source_is_skipped_by_the_reschedule`
  - `test_f2_a_peeked_paragraph_that_is_a_cold_items_source_makes_the_receipt_see_it`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_transcript_passage_carries_a_cue_like_any_source`
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — direct import
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_a_claim_needing_an_independent_check_is_a_try_first_target`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_source_statement_is_valid_by_its_recorded_decision_not_its_wording`
  - `test_the_sentence_is_rendered_from_the_field_never_read_from_the_statement`
  - `test_validation_reads_no_statement_and_only_flags_the_rest`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_item_without_a_required_method_serializes_and_hashes_as_before`
  - `test_validation_names_each_problem`
  - `test_validation_reads_no_sentence_and_flags_a_contradiction`
- [tests/test_required_method_rereview.py](../../../../../../tests/test_required_method_rereview.py) — direct import
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_the_reader_quick_check_and_the_tutors_practice_tool_render_the_instruction`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f1_the_reference_key_identity_carries_the_required_method`
  - `test_f2_an_answer_carried_only_by_the_required_method_is_withheld`
  - `test_f4_model_readers_and_review_exports_render_the_instruction`
  - `test_f4_the_practice_index_result_presents_the_question`
  - `test_f4_the_teach_back_author_reads_the_task_as_it_was_set`
  - `test_f5_the_practice_tool_keeps_the_instruction_of_a_long_stem`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f2_a_criterion_the_grader_declares_unverified_is_unassessed_on_a_divergent_route`
  - `test_fatal_errors_keep_their_mark_downs`
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
