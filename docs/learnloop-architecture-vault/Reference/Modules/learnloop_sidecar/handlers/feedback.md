---
title: "learnloop_sidecar.handlers.feedback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/feedback.py"
source_paths:
  - "src/learnloop_sidecar/handlers/feedback.py"
source_commit: "0a3288aa453d7ae2afb8142a7acf2c641d163333"
source_commit_timestamp: "2026-10-25T12:56:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.feedback module"
  - "src/learnloop_sidecar/handlers/feedback.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.feedback`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps feedback behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `AttemptInput`, `FeedbackInput`, `AnswerClarificationInput`, `TriggerRegradeInput`, `AnswerDisplayInput`, `AddErrorEventInput`, `TriggerFollowupInput`, `RateFollowupInput` and 20 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/feedback.py](../../../../../../src/learnloop_sidecar/handlers/feedback.py) |
| Source lines | 1173 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0a3288aa453d7ae2afb8142a7acf2c641d163333` |
| Commit timestamp | `2026-10-25T12:56:29-04:00` |

## Public API

- `class AttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 24)
- `class FeedbackInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 28)
- `class AnswerClarificationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 35)
- `class TriggerRegradeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 40)
- `class AnswerDisplayInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 55)
- `class AddErrorEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 64)
- `class TriggerFollowupInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 70)
- `class RateFollowupInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 74)
- `class ReportUnresolvedCauseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 79)
- `class ContestCausalDiagnosisInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 85)
- `class SubmitElicitingResponseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 90)
- `get_feedback(ctx: SidecarContext, params: FeedbackInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 186)
- `get_attempt(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 230)
- `get_attempt_trace_evidence(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 236) — A6 trace observations on one attempt, plus the sentence they earned.
- `get_grading_clarification(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 286) — The one A8 question this attempt is waiting on, or ``None``.
- `answer_grading_clarification(ctx: SidecarContext, params: AnswerClarificationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 314) — Record the learner's answer and re-grade the attempt with it in hand.
- `report_unresolved_cause(ctx: SidecarContext, params: ReportUnresolvedCauseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 397)
- `submit_eliciting_response(ctx: SidecarContext, params: SubmitElicitingResponseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 436) — The learner's unaided answer to an eliciting repair's question.
- `contest_causal_diagnosis(ctx: SidecarContext, params: ContestCausalDiagnosisInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 485)
- `trigger_regrade(ctx: SidecarContext, params: TriggerRegradeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 505)
- `record_answer_display(ctx: SidecarContext, params: AnswerDisplayInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 717) — Feedback's plain surface is about to show, or keeps showing, the full answer (UX Phase 4, Codex review F1, round 3): one routine display row.
- `trigger_followup(ctx: SidecarContext, params: TriggerFollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 756) — Manually force a diagnostic follow-up for one attempt.
- `class StartPrimedRetryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 827)
- `start_primed_retry(ctx: SidecarContext, params: StartPrimedRetryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 832) — Serve a sibling item for a primed retry from the source-review panel.
- `class StartGuidedRedoInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 1077)
- `start_guided_redo_handler(ctx: SidecarContext, params: StartGuidedRedoInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 1082) — Guided partial redo (Fix 3): serve the preserved-prefix redo context.
- `rate_followup(ctx: SidecarContext, params: RateFollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 1121) — One-tap "was this follow-up useful?" label from the feedback screen.
- `add_error_event(ctx: SidecarContext, params: AddErrorEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 1152)

### Module constants

- `GRADE_CONTEST_CLAIM_TYPE` ([src/learnloop_sidecar/handlers/feedback.py](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 647)

## Internal implementation anchors

- `_attach_common_repair(repository: Any, attempt_id: str, bundle: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 96) — Journey B: surface the already-decided common-repair recommendation.
- `_debit_repair_display_reveals(vault: Any, repository: Any, attempt: dict[str, Any], stored_feedback: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 129) — Charge the reveal ledger for the repair suggestions this screen shows.
- `_run_regrade(ctx: SidecarContext, vault, repository, attempt: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 516) — The existing regrade (learner-blind), or ``ai_unavailable``.
- `_contest_grade(ctx: SidecarContext, vault, repository, attempt: dict[str, Any], params: TriggerRegradeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 552) — "I think I was right" (spec §7.5): keep the learner's reason, look again in place, and send what the look did not settle to the owner's review.
- `_contest_upheld(bundle: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 618) — The answer now reads right (the learner's claim holds): full marks and not held for review.
- `_request_grade_review(repository, attempt_id: str, contest_id: str, presentation_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 629) — Queue the contested grade in the existing grade-review intake.
- `_record_grade_contest(repository, attempt_id: str, reason: str, *, contest_id: str, session_id: str | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 650) — Keep a learner's grade contest in the claim ledger (presented, then answered); returns the presentation id.
- `class _ContestKeyConflict(Exception)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 703) — A contest key already keeps another reason.
- `_kept_contest_reason(payload: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 707)
- `_source_first(ctx: SidecarContext, vault: Any, repository: Any, need: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 934) — S2b's step in the primed-retry adapter; None when it is not active.
- `_record_need_served(vault: Any, repository: Any, need: dict[str, Any], outcome: dict[str, Any], attempt: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 947) — S5: a need fulfilled from the sources and served (best effort).
- `_pick_primed_sibling(vault, repository, attempt: dict[str, Any], need: dict[str, Any] | None) -> tuple[Any | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 962) — Sibling items on the same LO, best-first.
- `_primed_retry_unavailable(params: StartPrimedRetryInput, attempt: dict[str, Any], reason: str, *, unservable_skips: list[dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 1046)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `answer_clarification`, `pending_clarification`; calls `answer_clarification`, `pending_clarification`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `flag_observation_for_review`; calls `flag_observation_for_review`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `regrade_attempt`; calls `regrade_attempt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `DisplayNotRecorded`, `record_feedback_answer_display_reveal`, `record_repair_display_reveals`; calls `record_feedback_answer_display_reveal`, `record_repair_display_reveals`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `elicitation_reward`; calls `elicitation_reward`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`; calls `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`; calls `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `common_repair_recommendation`, `evaluate_attempt_intervention_followup`; calls `common_repair_recommendation`, `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `GuidedRedoUnavailable`, `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`; calls `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/display|learnloop.diagnosis.recurrence.display]] — imports `displayed_repair_suggestions`, `is_escalation_suggestion`; calls `displayed_repair_suggestions`, `is_escalation_suggestion`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `RECENT_ATTEMPT_WINDOW`, `item_checkpoints`; calls `item_checkpoints`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `debit_escalated_repairs`, `diagnosis_repairs_debited`; calls `debit_escalated_repairs`, `diagnosis_repairs_debited`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_need_served`; calls `record_need_served`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `fulfil_need_from_sources`, `source_first_active`; calls `fulfil_need_from_sources`, `source_first_active`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `answered_check`; calls `answered_check`
- [[Reference/Modules/learnloop/learner/hypothesis_claims|learnloop.learner.hypothesis_claims]] — imports `present_claims`, `record_response`; calls `present_claims`, `record_response`
- [[Reference/Modules/learnloop/placement/claim_check|learnloop.placement.claim_check]] — imports `claim_check`; calls `claim_check`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_refusal`; calls `unservable_refusal`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `apply_proved_and_confirmed_promotion`; calls `apply_proved_and_confirmed_promotion`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`; calls `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `attempt_detail`, `feedback_bundle`, `live_grading_record`, `practice_item_detail`; calls `attempt_detail`, `feedback_bundle`, `live_grading_record`, `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `types`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_attempt_without_factors_is_untouched`
  - `test_divergent_causes_get_no_common_repair_card`
  - `test_feedback_bundle_carries_the_recommendation_and_stamps_durable_beliefs`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_repair_display_budget_debits_the_ledger_once_per_attempt`
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_the_primed_retry_adapter_tries_sources_before_generating`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/feedback.py](../../../../../../src/learnloop_sidecar/handlers/feedback.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
