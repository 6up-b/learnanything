---
title: "learnloop.content.authoring.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/ai_contracts.py"
source_paths:
  - "src/learnloop/content/authoring/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.ai_contracts` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Structured AI contracts owned by content authoring features.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py) |
| Source lines | 193 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ExerciseAuthoredItem(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 20) — One selected textbook exercise completed into a full PracticeItem contract (reader exercise import).
- `class ExerciseAuthoringContext` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 68)
- `class ConceptAnimationContext` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 80)
- `class ExerciseAuthoring(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 90)
- `class ManimAnimation(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 95)
- `exercise_authoring_prompt(context: ExerciseAuthoringContext) -> str` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 180)
- `concept_animation_prompt(context: ConceptAnimationContext) -> str` ([source](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 188)

### Module constants

- `BANNED_RESPONSE_MODES` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 55)
- `LOW_MASTERY_RESPONSE_MODES` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 60)
- `EXERCISE_AUTHORING_PROMPT_VERSION` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 102)
- `CONCEPT_ANIMATION_PROMPT_VERSION` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 103)
- `EXERCISE_AUTHORING_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 105)
- `CONCEPT_ANIMATION_PROMPT` ([src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py), line 150)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `CONCEPT_ANIMATION_PROMPT_VERSION`, `ConceptAnimationContext`, `ManimAnimation`, `concept_animation_prompt`; statically calls `ConceptAnimationContext`, `concept_animation_prompt`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `ExerciseAuthoring`, `ExerciseAuthoringContext`, `exercise_authoring_prompt`; statically calls `ExerciseAuthoringContext`, `exercise_authoring_prompt`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `CriterionFacetWeightsPayload`, `FacetWeightPayload`, `RubricCriterionPayload`, `RubricPatchPayload`, `TaskFeaturesPayload`, `TraceContractPayload`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]], [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_authoring_contract.py](../../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_ladder_and_ban_cannot_overlap`
  - `test_prompt_interpolates_the_shared_vocabulary`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
- [tests/test_concept_animation_service.py](../../../../../../../tests/test_concept_animation_service.py) — direct import
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
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/ai_contracts.py](../../../../../../../src/learnloop/content/authoring/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
