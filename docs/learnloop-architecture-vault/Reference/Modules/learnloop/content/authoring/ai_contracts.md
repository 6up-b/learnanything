---
title: "learnloop.content.authoring.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/ai_contracts.py"
source_paths:
  - "src/learnloop/content/authoring/ai_contracts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.ai_contracts module"
  - "src/learnloop/content/authoring/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.ai_contracts` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Structured AI contracts owned by content authoring features.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py) |
| Source lines | 454 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FigureRolePayload(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 31)
- `class ExerciseAuthoredItem(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 36) — One selected textbook exercise completed into a full PracticeItem contract (reader exercise import).
- `class ExerciseAuthoringContext` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 99)
- `class ConceptAnimationContext` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 121)
- `class ExerciseAuthoring(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 139)
- `class ManimAnimation(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 144)
- `class VideoStoryboardContext` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 152)
- `class VideoShot(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 169)
- `class VideoStoryboard(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 175)
- `exercise_authoring_prompt(context: ExerciseAuthoringContext) -> str` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 425)
- `concept_animation_prompt(context: ConceptAnimationContext) -> str` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 441)
- `video_storyboard_prompt(context: VideoStoryboardContext) -> str` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 449)

### Module constants

- `BANNED_RESPONSE_MODES` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 86)
- `LOW_MASTERY_RESPONSE_MODES` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 91)
- `EXERCISE_AUTHORING_PROMPT_VERSION` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 185)
- `CONCEPT_ANIMATION_PROMPT_VERSION` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 186)
- `VIDEO_STORYBOARD_PROMPT_VERSION` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 187)
- `EXERCISE_AUTHORING_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 189)
- `EXERCISE_AUTHORING_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 237)
- `FIGURE_ROLE_INSTRUCTIONS` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 243)
- `CONCEPT_ANIMATION_SCENE_SCAFFOLD` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 257)
- `CONCEPT_ANIMATION_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 313)
- `VIDEO_STORYBOARD_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 380)

## Internal implementation anchors

- `_exercise_context(context: ExerciseAuthoringContext) -> dict` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 433)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `CONCEPT_ANIMATION_PROMPT_VERSION`, `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, `ConceptAnimationContext`, `ManimAnimation`, `VIDEO_STORYBOARD_PROMPT_VERSION`, `VideoStoryboard`, `VideoStoryboardContext`, `concept_animation_prompt`, `video_storyboard_prompt`; statically calls `ConceptAnimationContext`, `VideoStoryboardContext`, `concept_animation_prompt`, `video_storyboard_prompt`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `ExerciseAuthoredItem`, `ExerciseAuthoring`, `ExerciseAuthoringContext`, `FIGURE_ROLE_INSTRUCTIONS`, `exercise_authoring_prompt`; statically calls `ExerciseAuthoringContext`, `exercise_authoring_prompt`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `CONCEPT_ANIMATION_PROMPT`, `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, `ManimAnimation`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `CriterionFacetWeightsPayload`, `FacetWeightPayload`, `RequiredMethodPayload`, `RubricCriterionPayload`, `RubricPatchPayload`, `TaskFeaturesPayload`, `TraceContractPayload`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `CRITERIA_BY_FACT_GUIDANCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]], [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/concept_animation_service_helpers.py](../../../../../../../tests/concept_animation_service_helpers.py) — direct import
- [tests/exercise_authoring_helpers.py](../../../../../../../tests/exercise_authoring_helpers.py) — direct import
- [tests/required_method_authority_helpers.py](../../../../../../../tests/required_method_authority_helpers.py) — direct import
- [tests/source_service_fakes.py](../../../../../../../tests/source_service_fakes.py) — direct import
- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_authoring_contract.py](../../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_ladder_and_ban_cannot_overlap`
  - `test_prompt_interpolates_the_shared_vocabulary`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
- [tests/test_concept_animation_validator.py](../../../../../../../tests/test_concept_animation_validator.py) — direct import
  - `test_scaffold_passes_validator`
- [tests/test_exercise_authoring.py](../../../../../../../tests/test_exercise_authoring.py) — direct import
  - `test_coordination_without_whole_task_is_left_unstamped`
  - `test_edited_capture_quote_becomes_the_exercise_surface`
  - `test_invalid_depth_and_rubric_degrade_without_blocking_the_item`
  - `test_missing_weights_are_not_uniformly_backfilled_and_smears_are_flagged`
  - `test_multi_exercise_split_skips_paraphrased_statement`
  - `test_selection_level_edited_text_overrides_combined_surface`
  - `test_single_item_paraphrase_falls_back_to_full_selection`
  - `test_unknown_facets_fall_back_and_unknown_lo_uses_hint`
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_openrouter_client.py](../../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_supports_exercise_authoring`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_selection_level_edit_of_the_whole_passage_never_crops_the_solution`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_a_duplicate_answer_claim_is_never_lost`
  - `test_a_selection_without_a_figure_sends_no_figure_context`
  - `test_a_sibling_never_owns_a_figure_one_item_calls_its_answer_among_duplicates`
  - `test_a_split_never_gives_one_item_a_figure_another_calls_its_answer`
  - `test_the_author_sees_the_selections_figures_and_their_instructions`
  - `test_two_claims_for_one_figure_resolve_away_from_stimulus`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_split_over_disjoint_and_shared_blocks_withholds_only_the_sharing_items_crop`
  - `test_a_split_with_an_unanchored_sibling_owns_nothing`
  - `test_two_exercises_split_from_one_block_get_no_free_crop_and_keep_the_page`
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_imported_exercise_keeps_a_required_method_only_by_its_one_time_judgment`
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`
- [tests/test_sources_merge_composition.py](../../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_authoring_runs_at_the_policy_budget_and_retries_a_truncation_once_at_double`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
