---
title: "learnloop.tutor.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/ai_contracts.py"
source_paths:
  - "src/learnloop/tutor/ai_contracts.py"
source_commit: "a2d2176b105ab0dc48837944ad2d6663280cc4d2"
source_commit_timestamp: "2026-11-01T16:13:42-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 794 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a2d2176b105ab0dc48837944ad2d6663280cc4d2` |
| Commit timestamp | `2026-11-01T16:13:42-05:00` |

## Public API

- `class TutorQAContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 21)
- `tutor_context_payload(context: 'TutorQAContext') -> dict` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 50) — The context as rendered and hashed; an absent confidence block or learner state is omitted.
- `reader_learner_state_on(context: 'TutorQAContext') -> bool` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 61) — Whether a Reader context carries the learner state (its own prompt version suffix and task wording; every other context renders as before).
- `class ReaderTutorQAContext(TutorQAContext)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 69) — Reader workbench RW1c: the Reader context of a tutor that looks things up.
- `class ReaderTutorExplorableQAContext(ReaderTutorQAContext)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 85) — RW5b: :class:`ReaderTutorQAContext` while figure offers are on (no new fields; the prompt adds the ``explorable`` judgment and carries its own version, and each delivered equation or figure block carries ``block``: Codex review F7).
- `class ReaderTutorShowMeQAContext(ReaderTutorQAContext)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 93) — Reader RW5d P1 (``figures.show_me_enabled`` with RW5b's offers): the Reader context whose answer may carry an optional ``figure_goal`` (no new fields; its own prompt version).
- `class ReaderTutorExplorableShowMeQAContext(ReaderTutorExplorableQAContext)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 101) — RW5d P1: RW5b's explorable context with the optional ``figure_goal``.
- `class TeachBackQuestionContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 106)
- `class TeachBackAuthoringContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 121)
- `class PromotionAnalysisContext` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 135)
- `class TutorCitation(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 145)
- `class LearnerGap(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 155) — What a learner's own text reveals, NAMED before it is classified.
- `class TutorAnswer(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 186)
- `class TutorAnswerWithTools(TutorAnswer)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 201) — The tutor's answer with typed source-tool requests (canonical sources S4, §10.3).
- `class ReaderExcerpt(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 210) — RW1c's "From your books": a verbatim piece of one provided passage.
- `class ReaderTutorAnswer(TutorAnswer)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 218) — The Reader tutor's answer in up to three labelled parts (RW1c, spec §4.6): ``excerpt`` ("From your books", quote-verified in code), ``answer_md`` (LearnLoop's grounded explanation) and ``bridge_md`` (connecting it to the learner's work, only when that work is in context).
- `class ReaderTutorAnswerWithTools(TutorAnswerWithTools)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 228) — :class:`ReaderTutorAnswer` with S4's tool requests (``source_service.tutor_tools`` on).
- `class ExplorableCitation(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 235) — RW5b: whether one cited equation or figure block could become an explorable figure (the tutor's judgment, in the call that answers).
  - `_tolerate(cls, data: Any) -> Any` (line 246; internal)
- `class ReaderTutorExplorableAnswer(ReaderTutorAnswer)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 252) — RW5b (``figures.offers_enabled``): :class:`ReaderTutorAnswer` with ``explorable`` on each cited equation or figure block; an output without the field reads as no offers.
- `class ReaderTutorExplorableAnswerWithTools(ReaderTutorAnswerWithTools)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 260)
- `class ReaderTutorShowMeAnswer(ReaderTutorAnswer, _FigureGoal)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 275) — RW5d P1 (``figures.show_me_enabled``): :class:`ReaderTutorAnswer` with the optional ``figure_goal``; an output without it reads as no goal.
- `class ReaderTutorShowMeAnswerWithTools(ReaderTutorAnswerWithTools, _FigureGoal)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 280)
- `class ReaderTutorExplorableShowMeAnswer(ReaderTutorExplorableAnswer, _FigureGoal)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 284)
- `class ReaderTutorExplorableShowMeAnswerWithTools(ReaderTutorExplorableAnswerWithTools, _FigureGoal)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 288)
- `class TeachBackQuestion(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 292)
- `class TeachBackCriterionDraft(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 296)
- `class TeachBackAuthoring(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 305)
- `class PromotionAnalysis(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 315)
- `tutor_qa_prompt(context: TutorQAContext, *, tools: bool=False) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 723)
- `teach_back_question_prompt(context: TeachBackQuestionContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 773)
- `teach_back_authoring_prompt(context: TeachBackAuthoringContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 781)
- `promotion_analysis_prompt(context: PromotionAnalysisContext) -> str` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 789)

### Module constants

- `LEARNER_GAP_KINDS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 152)
- `FIGURE_GOAL_CHARS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 265)
- `TUTOR_QA_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 322)
- `LEARNER_GAP_RULES_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 324)
- `TUTOR_QA_TOOLS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 329)
- `READER_TUTOR_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 333)
- `READER_TUTOR_TOOLS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 334)
- `READER_TUTOR_EXPLORABLE_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 337)
- `READER_TUTOR_EXPLORABLE_TOOLS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 338)
- `SHOW_ME_PROMPT_SUFFIX` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 341)
- `READER_TUTOR_SHOW_ME_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 342)
- `READER_TUTOR_SHOW_ME_TOOLS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 343)
- `READER_TUTOR_EXPLORABLE_SHOW_ME_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 344)
- `READER_TUTOR_EXPLORABLE_SHOW_ME_TOOLS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 345)
- `READER_LEARNER_STATE_SUFFIX` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 348)
- `TEACH_BACK_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 349)
- `TEACH_BACK_AUTHORING_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 350)
- `PROMOTION_ANALYSIS_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 351)
- `TUTOR_PROMOTION_PROMPT_VERSION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 352)
- `PROMOTION_ANALYSIS_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 354)
- `TUTOR_PROMOTION_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 379)
- `TUTOR_PROMOTION_PROMPT` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 429)
- `_TUTOR_QA_LEARNER_EXTRACTION` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 435)
- `LEARNER_GAP_RULES` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 453)
- `_TUTOR_QA_SHARED` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 468)
- `_READER_BLIND_SENTENCE` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 493)
- `_TUTOR_QA_CONTEXT_TASKS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 497)
- `_TUTOR_QA_READER_LEARNER_STATE_SENTENCE` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 530)
- `_TUTOR_QA_READER_MODE_TASKS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 539)
- `_TUTOR_QA_PRACTICE_MODE_TASKS` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 558)
- `TUTOR_QA_ANSWER_MODE_SUFFIX` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 575)
- `_TEACH_BACK_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 577)
- `_TEACH_BACK_AUTHORING_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 597)
- `_TUTOR_QA_DIAGNOSTIC_DECISION_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 635)
- `_TUTOR_QA_OPENING_SHARED` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 652)
- `_TUTOR_QA_TOOLS_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 666)
- `_TUTOR_QA_READER_LOOKUP_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 679)
- `_TUTOR_QA_READER_EXPLORABLE_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 703)
- `_TUTOR_QA_READER_SHOW_ME_TASK` ([src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py), line 714)

## Internal implementation anchors

- `class _FigureGoal(WireModel)` ([source](../../../../../../src/learnloop/tutor/ai_contracts.py), line 268)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `TEACH_BACK_AUTHORING_PROMPT_VERSION`, `teach_back_authoring_prompt`; statically calls `teach_back_authoring_prompt`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `LEARNER_GAP_KINDS`, `LEARNER_GAP_RULES`, `LearnerGap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `LearnerGap`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `ReaderTutorQAContext`, `TutorAnswer`, `TutorCitation`, `TutorQAContext`; statically calls `TutorAnswer`, `TutorCitation`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `TeachBackQuestion`, `TeachBackQuestionContext`; statically calls `TeachBackQuestion`, `TeachBackQuestionContext`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionAnalysis`, `PromotionAnalysisContext`, `TUTOR_PROMOTION_PROMPT`, `promotion_analysis_prompt`; statically calls `PromotionAnalysis`, `PromotionAnalysisContext`, `promotion_analysis_prompt`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `FIGURE_GOAL_CHARS`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestion`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`; statically calls `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `READER_LEARNER_STATE_SUFFIX`, `READER_TUTOR_EXPLORABLE_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_SHOW_ME_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_SHOW_ME_TOOLS_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_TOOLS_PROMPT_VERSION`, `READER_TUTOR_PROMPT_VERSION`, `READER_TUTOR_SHOW_ME_PROMPT_VERSION`, `READER_TUTOR_SHOW_ME_TOOLS_PROMPT_VERSION`, `READER_TUTOR_TOOLS_PROMPT_VERSION`, `ReaderTutorAnswer`, `ReaderTutorAnswerWithTools`, `ReaderTutorExplorableAnswer`, `ReaderTutorExplorableAnswerWithTools`, `ReaderTutorExplorableQAContext`, `ReaderTutorExplorableShowMeAnswer`, `ReaderTutorExplorableShowMeAnswerWithTools`, `ReaderTutorExplorableShowMeQAContext`, `ReaderTutorQAContext`, `ReaderTutorShowMeAnswer`, `ReaderTutorShowMeAnswerWithTools`, `ReaderTutorShowMeQAContext`, `TUTOR_QA_ANSWER_MODE_SUFFIX`, `TUTOR_QA_PROMPT_VERSION`, `TUTOR_QA_TOOLS_PROMPT_VERSION`, `TutorAnswer`, `TutorAnswerWithTools`, `TutorQAContext`, `reader_learner_state_on`, `tutor_context_payload`, `tutor_qa_prompt`; statically calls `TutorQAContext`, `reader_learner_state_on`, `tutor_context_payload`, `tutor_qa_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/ai/tool_requests|learnloop.ai.tool_requests]] — imports `ToolRequest`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `TraceContractPayload`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_authoring_contract.py](../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_prompt_interpolates_the_shared_vocabulary`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_tutor_answer_round_trips_extraction_fields_and_legacy_payloads`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_the_tutor_context_asks_for_explorable_only_with_a_block_to_judge`
  - `test_the_tutor_prompt_adds_explorable_only_in_its_own_version`
  - `test_the_tutor_view_keeps_a_yes_only_on_a_block_it_cites`
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
- [tests/test_figures_rw5b_fix_round2.py](../../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_the_tutors_explorable_rows_hash_the_input_not_the_verdict`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event`
  - `test_the_tutor_context_marks_each_equation_and_figure_block`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_the_show_me_tutor_prompt_is_rw5bs_plus_the_goal_clause`
- [tests/test_followups_batch5_c5_ledger.py](../../../../../../tests/test_followups_batch5_c5_ledger.py) — direct import
  - `test_a_notes_ledger_verdicts_have_the_shared_shape_and_the_report_reads_them`
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
- [tests/test_hint_feedback_texts.py](../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_the_gap_joins_the_next_hints_rivals`
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_an_edge_that_would_close_a_cycle_is_refused`
  - `test_declared_prerequisites_and_the_shortlist_share_the_judge_budget`
  - `test_slip_and_wording_are_signals_only_and_listed_for_batch_review`
  - `test_the_daily_creation_cap_holds`
  - `test_the_tutor_names_the_gap_in_the_answering_call_and_it_is_persisted`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_report_counts_per_kind_and_chooser_and_its_dry_run_writes_nothing`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f5_a_match_on_the_items_own_lo_is_no_prerequisite_target`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_hidden_link_is_never_read_and_undo_queues_it_again`
  - `test_a_note_is_read_on_the_ordinary_routes_with_the_decider`
  - `test_a_notes_receipts_keep_the_prompt_like_any_learner_text`
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
  - `test_c2b_a_notes_belief_is_handled_like_any_learner_texts`
  - `test_c2b_a_reader_note_written_beside_material_protected_since_is_never_read`
  - `test_f3_hiding_the_link_between_requests_stops_the_reading_and_writes_nothing`
  - `test_f3_rereview_a_payload_changed_after_preparation_is_not_sent`
  - `test_f3_rereview_the_gate_is_bound_to_the_prepared_passages`
  - `test_f3_revoking_consent_before_dispatch_sends_nothing`
  - `test_f3_switched_off_before_the_final_write_writes_nothing`
  - `test_f6_hidden_before_pair_dispatch_then_undo_resumes_without_an_abandoned_claim`
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
  - `test_reading_a_note_is_tier_2_only_and_keeps_its_words_like_any_learner_text`
  - `test_step0_a_checkpointed_note_reading_is_never_reused_after_its_inputs_change`
  - `test_step0_a_legacy_checkpointed_note_reading_is_cleared_on_requeue_and_ignored_on_retry`
- [tests/test_notes_c2b_review5.py](../../../../../../tests/test_notes_c2b_review5.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
- [tests/test_question_context.py](../../../../../../tests/test_question_context.py) — direct import
- [tests/test_question_promotion_jobs.py](../../../../../../tests/test_question_promotion_jobs.py) — direct import
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
- [tests/test_reader_branches.py](../../../../../../tests/test_reader_branches.py) — direct import
  - `test_branch_keeps_citation_allowlist_and_evidence_isolation`
- [tests/test_reader_ca2_codex_review.py](../../../../../../tests/test_reader_ca2_codex_review.py) — direct import
  - `test_a_cited_passage_carries_its_excerpt_as_provided_and_stores_it`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_a_practice_answer_mode_reaches_the_prompt_and_the_row`
  - `test_without_a_mode_the_practice_prompt_is_todays`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_answer_mode_is_honored_in_prompt_assembly`
- [tests/test_reader_formative_texts.py](../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_ai_question_control_sequences_are_removed_from_live_and_restored_state`
- [tests/test_teacher_te0_confidence_events.py](../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_tutor_reads_the_events_in_practice_contexts`
  - `test_with_no_confidence_data_the_tutor_context_renders_and_hashes_as_before`
- [tests/test_tutor_citations.py](../../../../../../tests/test_tutor_citations.py) — direct import
  - `test_citations_validated_against_provided_spans`
  - `test_no_links_degrades_to_no_citations`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_referenced_theorem_is_citable`
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
- [tests/test_tutor_tool_requests.py](../../../../../../tests/test_tutor_tool_requests.py) — direct import
  - `test_requests_are_validated_recorded_and_offered`
  - `test_the_switch_restores_s0s_tutor_byte_for_byte`
- [tests/test_workbench_text_gaps.py](../../../../../../tests/test_workbench_text_gaps.py) — direct import
  - `test_reading_it_writes_only_gap_rows`
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/ai_contracts.py](../../../../../../src/learnloop/tutor/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
