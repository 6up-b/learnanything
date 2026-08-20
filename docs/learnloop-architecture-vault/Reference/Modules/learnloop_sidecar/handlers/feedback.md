---
title: "learnloop_sidecar.handlers.feedback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/feedback.py"
source_paths:
  - "src/learnloop_sidecar/handlers/feedback.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
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

This module keeps feedback behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `AttemptInput`, `AnswerClarificationInput`, `TriggerRegradeInput`, `AddErrorEventInput`, `TriggerFollowupInput`, `RateFollowupInput`, `ReportUnresolvedCauseInput`, `ContestCausalDiagnosisInput` and 17 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/feedback.py](../../../../../../src/learnloop_sidecar/handlers/feedback.py) |
| Source lines | 843 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 16)
- `class AnswerClarificationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 20)
- `class TriggerRegradeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 25)
- `class AddErrorEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 29)
- `class TriggerFollowupInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 35)
- `class RateFollowupInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 39)
- `class ReportUnresolvedCauseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 44)
- `class ContestCausalDiagnosisInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 50)
- `class SubmitElicitingResponseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 55)
- `get_feedback(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 129)
- `get_attempt(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 157)
- `get_attempt_trace_evidence(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 163) — A6 trace observations on one attempt, plus the sentence they earned.
- `get_grading_clarification(ctx: SidecarContext, params: AttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 213) — The one A8 question this attempt is waiting on, or ``None``.
- `answer_grading_clarification(ctx: SidecarContext, params: AnswerClarificationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 241) — Record the learner's answer and re-grade the attempt with it in hand.
- `report_unresolved_cause(ctx: SidecarContext, params: ReportUnresolvedCauseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 324)
- `submit_eliciting_response(ctx: SidecarContext, params: SubmitElicitingResponseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 363) — The learner's unaided answer to an eliciting repair's question.
- `contest_causal_diagnosis(ctx: SidecarContext, params: ContestCausalDiagnosisInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 412)
- `trigger_regrade(ctx: SidecarContext, params: TriggerRegradeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 432)
- `trigger_followup(ctx: SidecarContext, params: TriggerFollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 466) — Manually force a diagnostic follow-up for one attempt.
- `class StartPrimedRetryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 537)
- `start_primed_retry(ctx: SidecarContext, params: StartPrimedRetryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 542) — Serve a sibling item for a primed retry from the source-review panel.
- `class StartGuidedRedoInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 747)
- `start_guided_redo_handler(ctx: SidecarContext, params: StartGuidedRedoInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 752) — Guided partial redo (Fix 3): serve the preserved-prefix redo context.
- `rate_followup(ctx: SidecarContext, params: RateFollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 791) — One-tap "was this follow-up useful?" label from the feedback screen.
- `add_error_event(ctx: SidecarContext, params: AddErrorEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 822)

## Internal implementation anchors

- `_attach_common_repair(repository: Any, attempt_id: str, bundle: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 61) — Journey B: surface the already-decided common-repair recommendation.
- `_debit_repair_display_reveals(vault: Any, repository: Any, attempt: dict[str, Any], stored_feedback: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 94) — Charge the reveal ledger for the repair suggestions this screen shows.
- `_pick_primed_sibling(vault, repository, attempt: dict[str, Any], need: dict[str, Any] | None) -> tuple[Any | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 632) — Sibling items on the same LO, best-first.
- `_primed_retry_unavailable(params: StartPrimedRetryInput, attempt: dict[str, Any], reason: str, *, unservable_skips: list[dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/feedback.py), line 716)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `answer_clarification`, `pending_clarification`; calls `answer_clarification`, `pending_clarification`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `regrade_attempt`; calls `regrade_attempt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_repair_display_reveals`; calls `record_repair_display_reveals`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `elicitation_reward`; calls `elicitation_reward`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`; calls `generate_diagnostic_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`; calls `record_causal_diagnosis_contest`, `record_eliciting_response`, `record_unresolved_cause_self_report`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `common_repair_recommendation`, `evaluate_attempt_intervention_followup`; calls `common_repair_recommendation`, `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `GuidedRedoUnavailable`, `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`; calls `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `RECENT_ATTEMPT_WINDOW`, `item_checkpoints`; calls `item_checkpoints`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_refusal`; calls `unservable_refusal`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `apply_proved_and_confirmed_promotion`; calls `apply_proved_and_confirmed_promotion`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`; calls `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `attempt_detail`, `feedback_bundle`, `practice_item_detail`; calls `attempt_detail`, `feedback_bundle`, `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `types`, `typing`
- Third party: none imported directly

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

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/feedback.py](../../../../../../src/learnloop_sidecar/handlers/feedback.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
