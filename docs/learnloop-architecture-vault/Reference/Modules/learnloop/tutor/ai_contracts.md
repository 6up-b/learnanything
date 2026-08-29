---
title: "learnloop.tutor.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/ai_contracts.py"
source_paths:
  - "src/learnloop/tutor/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.ai_contracts module"
  - "src/learnloop/tutor/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.ai_contracts` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Structured AI contracts owned by tutor and teach-back features.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py) |
| Source lines | 420 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TutorQAContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 20)
- `class TeachBackQuestionContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 39)
- `class TeachBackAuthoringContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 54)
- `class PromotionAnalysisContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 68)
- `class TutorCitation(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 78)
- `class TutorAnswer(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 84)
- `class TeachBackQuestion(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 96)
- `class TeachBackCriterionDraft(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 100)
- `class TeachBackAuthoring(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 109)
- `class PromotionAnalysis(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 119)
- `tutor_qa_prompt(context: TutorQAContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 384)
- `teach_back_question_prompt(context: TeachBackQuestionContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 399)
- `teach_back_authoring_prompt(context: TeachBackAuthoringContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 407)
- `promotion_analysis_prompt(context: PromotionAnalysisContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 415)

### Module constants

- `TUTOR_QA_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 126)
- `TEACH_BACK_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 127)
- `TEACH_BACK_AUTHORING_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 128)
- `PROMOTION_ANALYSIS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 129)
- `TUTOR_PROMOTION_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 130)
- `PROMOTION_ANALYSIS_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 132)
- `TUTOR_PROMOTION_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 157)
- `TUTOR_PROMOTION_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 207)
- `_TUTOR_QA_LEARNER_EXTRACTION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 213)
- `_TUTOR_QA_SHARED` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 231)
- `_TUTOR_QA_CONTEXT_TASKS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 255)
- `_TUTOR_QA_READER_MODE_TASKS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 287)
- `_TEACH_BACK_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 302)
- `_TEACH_BACK_AUTHORING_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 322)
- `_TUTOR_QA_DIAGNOSTIC_DECISION_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 353)
- `_TUTOR_QA_OPENING_SHARED` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 370)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `TutorAnswer`, `TutorCitation`, `TutorQAContext`; statically calls `TutorAnswer`, `TutorCitation`, `TutorQAContext`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `TeachBackQuestion`, `TeachBackQuestionContext`; statically calls `TeachBackQuestion`, `TeachBackQuestionContext`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionAnalysis`, `PromotionAnalysisContext`, `TUTOR_PROMOTION_PROMPT`, `promotion_analysis_prompt`; statically calls `PromotionAnalysis`, `PromotionAnalysisContext`, `promotion_analysis_prompt`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestion`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`; statically calls `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `TUTOR_QA_PROMPT_VERSION`, `TutorAnswer`, `TutorQAContext`, `tutor_qa_prompt`; statically calls `TutorQAContext`, `tutor_qa_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `TraceContractPayload`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]], [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]], [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_authoring_contract.py](../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_prompt_interpolates_the_shared_vocabulary`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_codex_teach_back_authoring_schema_is_strict_response_format_compatible`
  - `test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_tutor_answer_round_trips_extraction_fields_and_legacy_payloads`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_question_context.py](../../../../../../tests/test_question_context.py) — direct import
- [tests/test_question_promotion_jobs.py](../../../../../../tests/test_question_promotion_jobs.py) — direct import
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_answer_mode_is_honored_in_prompt_assembly`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_ai_question_control_sequences_are_removed_from_live_and_restored_state`
- [tests/test_tutor_citations.py](../../../../../../tests/test_tutor_citations.py) — direct import
  - `test_citations_validated_against_provided_spans`
  - `test_no_links_degrades_to_no_citations`
- [tests/test_tutor_promotion_service.py](../../../../../../tests/test_tutor_promotion_service.py) — direct import
  - `test_accepting_reviewed_promotion_makes_original_request_schedulable`
  - `test_attach_to_existing_with_grounding_auto_applies`
  - `test_dedup_short_circuit_gap_writes_claim_no_need`
  - `test_dedup_short_circuit_practice`
  - `test_gap_inline_diagnostic_generation_when_available`
  - `test_gap_need_dedup_links_existing_need`
  - `test_gap_route_transfer_nature_biases_intent`
  - `test_gap_route_writes_claim_need_and_diagnostic_pending`
  - `test_grounding_fallback_forces_review`
  - `test_idempotent_returns_existing_row`
  - `test_library_gap_rejected`
  - `test_new_lo_batch_forced_review`
  - `test_practice_promotion_with_no_authored_item_fails_instead_of_claiming_review`
  - `test_reader_promotion_honors_persisted_learning_object_target`
  - `test_reader_promotion_uses_subject_facet_vocabulary_without_origin_item`
  - `test_rejecting_and_resetting_review_updates_promotion_request_state`
- [tests/test_tutor_qa.py](../../../../../../tests/test_tutor_qa.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
