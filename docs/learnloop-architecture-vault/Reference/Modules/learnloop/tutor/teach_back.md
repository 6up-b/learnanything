---
title: "learnloop.tutor.teach_back"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/teach_back.py"
source_paths:
  - "src/learnloop/tutor/teach_back.py"
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
  - "learnloop.tutor.teach_back module"
  - "src/learnloop/tutor/teach_back.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.teach_back`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.teach_back` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Teach-back conversations: the learner teaches, an AI naive student asks.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py) |
| Source lines | 1246 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `request_teach_back_question(client: OperationClient, context: TeachBackQuestionContext) -> TeachBackQuestion` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 82) — Run the feature-owned teach-back question operation.
- `request_teach_back_authoring(client: OperationClient, context: TeachBackAuthoringContext) -> TeachBackAuthoring` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 98) — Run the feature-owned teach-back item-authoring operation.
- `class TeachBackError(ValueError)` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 136)
- `class TeachBackTurn` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 145)
- `class TeachBackState` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 152) — Serializable conversation state (JSON round-trippable).
  - `to_dict(self) -> dict[str, Any]` (line 174; public)
  - `to_json(self) -> str` (line 184; public)
  - `from_dict(cls, payload: Mapping[str, Any]) -> 'TeachBackState'` (line 188; public)
  - `from_json(cls, text: str) -> 'TeachBackState'` (line 210; public)
- `class TeachBackFinishResult` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 215)
  - `as_dict(self) -> dict[str, Any]` (line 221; public)
- `plan_followups(vault: LoadedVault, repository: Repository, item: PracticeItem, *, config: LearnLoopConfig | None=None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 230) — Ordered follow-up plan: ``[{criterion_id, tier, facet_targets}]``.
- `begin_teach_back(vault: LoadedVault, repository: Repository, item: PracticeItem, *, opening_md: str, config: LearnLoopConfig | None=None, clock: Clock | None=None) -> TeachBackState` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 333) — Start a conversation: plan the follow-ups and record the opening turn.
- `next_question(vault: LoadedVault, state: TeachBackState, client: Any, *, config: LearnLoopConfig | None=None) -> tuple[TeachBackState, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 355) — Generate the next naive-student question via the AI provider.
- `record_answer(state: TeachBackState, answer_md: str) -> TeachBackState` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 418) — Append the learner's answer to the most recent AI question.
- `asked_criterion_ids(state: TeachBackState) -> list[str]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 433) — Criteria whose question was asked AND answered, in ask order.
- `render_transcript_md(state: TeachBackState, item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 453) — Render the conversation to Markdown (the graded ``learner_answer_md``).
- `finish_teach_back(vault: LoadedVault, repository: Repository, state: TeachBackState, client: Any, *, session_id: str | None=None, latency_seconds: int | None=None, agent_run_id: str | None=None, clock: Clock | None=None) -> TeachBackFinishResult` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 484) — Grade the whole transcript as ONE ``teach_back`` attempt.
- `core_criteria(rubric: Rubric) -> list[RubricCriterion]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 603) — Core-tier criteria of a rubric (the fallback graded set).
- `restrict_grading_context_to_criteria(context: Any, item: PracticeItem, rubric: Rubric, criteria: list[RubricCriterion]) -> Any` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 609) — Restrict a grading context's rubric + facet weights to ``criteria``.
- `asked_rubric_score(rubric: Rubric, asked_criteria: list[RubricCriterion], criterion_points: Mapping[str, float], fatal_errors: list[str]) -> int` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 648) — Rubric score normalized over the asked criteria's points.
- `ensure_teach_back_item(root, vault: LoadedVault, repository: Repository, learning_object_id: str, *, source_practice_item_id: str | None=None, authoring_client: Any | None=None, quest_sentence: str | None=None, clock: Clock | None=None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 681) — Find or mint a learner-requested teach-back card.

### Module constants

- `TEACH_BACK_ATTEMPT_TYPE` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 74)
- `TEACH_BACK_PRACTICE_MODE` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 75)
- `TEACH_BACK_COMPILER_VERSION` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 76)
- `STATE_VERSION` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 78)
- `LOG` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 79)
- `_ANSI_SEQUENCE` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 119)
- `_UNSAFE_CONTROL` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 122)
- `_STATE_RANK` ([src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py), line 133)

## Internal implementation anchors

- `_sanitize_ai_markdown(value: str) -> str` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 125)
- `_criterion_tier(criterion: RubricCriterion) -> str` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 140)
- `_teach_back_rubric(vault: LoadedVault, item: PracticeItem) -> Rubric` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 674)
- `_active_quest_for_learning_object(vault: LoadedVault, repository: Repository, learning_object_id: str) -> tuple[str | None, str | None, str | None]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 831) — Highest-priority relevant active goal with a resolvable learner quest.
- `_teach_back_authoring_context(vault: LoadedVault, source_item: PracticeItem, learning_object, *, quest_sentence: str | None) -> tuple[TeachBackAuthoringContext, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 860)
- `_run_teach_back_authoring(client: Any | None, context: TeachBackAuthoringContext, *, source_criteria: list[dict[str, Any]], allowed_facet_ids: set[str], learning_object_title: str) -> TeachBackAuthoring | None` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 923)
- `_validate_teach_back_authoring(authored: TeachBackAuthoring, *, source_criteria: list[dict[str, Any]], allowed_facet_ids: set[str], quest_sentence: str | None, learning_object_title: str) -> None` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 950)
- `_fallback_teach_back_authoring(source_item: PracticeItem, source_criteria: list[dict[str, Any]], *, quest_sentence: str | None) -> TeachBackAuthoring` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 1011) — Conservative source-specific fallback: useful wording, zero false facet links.
- `_compiled_teach_back_criteria(authored: TeachBackAuthoring) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 1069)
- `_ensure_lo_wide_teach_back_item(root, vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 1113) — Compatibility path for direct LO requests with no source item.
- `_facet_ranks(vault: LoadedVault, repository: Repository, item: PracticeItem, *, clock: Clock | None) -> dict[str, tuple[int, float, str]]` ([source](../../../../../../src/learnloop/tutor/teach_back.py), line 1218) — Uncertainty rank per item facet, from the diagnostic read path.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `TEACH_BACK_ATTEMPT_TYPE`, `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`; statically calls `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `TEACH_BACK_PRACTICE_MODE`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `TEACH_BACK_ATTEMPT_TYPE`, `TEACH_BACK_PRACTICE_MODE`, `begin_teach_back`, `finish_teach_back`, `next_question`, `record_answer`; statically calls `begin_teach_back`, `finish_teach_back`, `next_question`, `record_answer`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `TEACH_BACK_PRACTICE_MODE`, `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`; statically calls `TeachBackError`, `TeachBackState`, `asked_criterion_ids`, `begin_teach_back`, `ensure_teach_back_item`, `finish_teach_back`, `next_question`, `plan_followups`, `record_answer`, `render_transcript_md`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `TEACH_BACK_PRACTICE_MODE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; calls `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `build_grading_context`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_intent|learnloop.goals.goal_intent]] — imports `resolve_goal_quest`; calls `resolve_goal_quest`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `mastery_diagnostic_view`, `required_facets`; calls `mastery_diagnostic_view`, `required_facets`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `criterion_facet_weights_for_item`; calls `criterion_facet_weights_for_item`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestion`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`; calls `TeachBackAuthoring`, `TeachBackAuthoringContext`, `TeachBackCriterionDraft`, `TeachBackQuestionContext`, `teach_back_authoring_prompt`, `teach_back_question_prompt`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `RubricCriterion`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_ai_question_control_sequences_are_removed_from_live_and_restored_state`
  - `test_ensure_teach_back_item_authors_from_exact_source_and_active_quest`
  - `test_ensure_teach_back_item_mints_transfer_criterion`
  - `test_finish_and_rebuild_replay_reproduce_derived_state`
  - `test_finish_partial_grading_only_asked_criteria_produce_evidence`
  - `test_finish_with_no_answered_followup_grades_opening_against_core`
  - `test_fractional_asked_subset_is_a_view_not_an_authored_rubric`
  - `test_low_scoring_answers_are_just_low_scores`
  - `test_next_question_conditions_on_transcript_and_exhausts`
  - `test_plan_escalates_to_transfer_when_everything_is_solid`
  - `test_plan_followups_keeps_declared_item_local_criteria_targetless`
  - `test_plan_is_deterministic_and_capped`
  - `test_plan_orders_uncertain_core_first_then_escalates`
  - `test_plan_reserves_final_slot_for_transfer_when_core_would_crowd_it_out`
  - `test_regrade_teach_back_attempt_restricts_to_graded_criteria`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`
  - `test_replay_teach_back_attempt_survives_practice_mode_change`
  - `test_source_scoped_teach_back_does_not_reuse_lo_wide_card`
  - `test_state_json_round_trip`
  - `test_transfer_tier_evidence_mass_is_discounted_symmetrically`

## Modification guidance

- Change teach back policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/teach_back.py](../../../../../../src/learnloop/tutor/teach_back.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
