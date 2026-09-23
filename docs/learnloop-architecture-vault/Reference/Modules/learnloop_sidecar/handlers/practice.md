---
title: "learnloop_sidecar.handlers.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/practice.py"
source_paths:
  - "src/learnloop_sidecar/handlers/practice.py"
source_commit: "7353a4204e5cc8ca4a15010a78ac3f84b8295617"
source_commit_timestamp: "2026-09-23T12:27:35-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.practice module"
  - "src/learnloop_sidecar/handlers/practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps practice behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `PracticeDraftCheckpoint`, `PracticeSubmissionRecoveryInput`, `PracticeSubmissionAcknowledgementInput`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SubmitAttemptInput`, `DontKnowInput`, `SkipInput` and 16 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) |
| Source lines | 1008 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7353a4204e5cc8ca4a15010a78ac3f84b8295617` |
| Commit timestamp | `2026-09-23T12:27:35-04:00` |

## Public API

- `class PracticeDraftCheckpoint(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 57)
- `class PracticeSubmissionRecoveryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 68)
- `class PracticeSubmissionAcknowledgementInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 74)
- `class SelfGradeErrorAttributionDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 80)
- `class SelfGradeInputDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 85)
- `class SubmitAttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 94)
- `class DontKnowInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 117)
- `class SkipInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 130)
- `class ServePracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 135)
- `get_practice_item(ctx: SidecarContext, params: ServePracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 159) — Serve one item, carrying A6's elicitation decision for this serve.
- `class ProbeContractInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 200)
- `get_probe_contract(ctx: SidecarContext, params: ProbeContractInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 242) — The probe measurement contract for opening one item (§12).
- `stop_probe_diagnosing(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 330) — `Stop diagnosing and teach me` (§3): end the measurement block, persist the typed transition decision, and open a post-intervention state segment.
- `class NextProbeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 342)
- `get_next_probe_item(ctx: SidecarContext, params: NextProbeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 347) — The item that would continue this LO's open diagnostic block, if any.
- `class OverconfidenceProbeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 363)
- `start_overconfidence_probe(ctx: SidecarContext, params: OverconfidenceProbeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 369) — Launch a diagnostic episode from the F5 overconfidence list (§4.3).
- `save_practice_draft(ctx: SidecarContext, params: PracticeDraftCheckpoint) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 398)
- `recover_practice_submission(ctx: SidecarContext, params: PracticeSubmissionRecoveryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 427) — Recover a completed submit before trying to serve the item again.
- `acknowledge_practice_submission(ctx: SidecarContext, params: PracticeSubmissionAcknowledgementInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 462) — Clear only the checkpoint whose authoritative result was received.
- `submit_attempt(ctx: SidecarContext, params: SubmitAttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 490)
- `submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 615)
- `submission_key(params: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 678) — The retry key a request's attempt, receipt and model calls are keyed on.
- `skip_practice_item(ctx: SidecarContext, params: SkipInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 791)

### Module constants

- `_OTHER_SESSION` ([src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 206)

## Internal implementation anchors

- `_require_active_item(vault, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 143) — One terminal lifecycle gate for every practice write/serve.
- `_committed_presentation(repository, episode, session_id: str | None)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 209) — The durable presentation this open of the item should consume.
- `_bind_offer(repository, params, submission_id)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 415)
- `_submission_id(client_id: str | None, presentation_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 668) — Return the stable retry key; old probe clients inherit one for free.
- `_cached_submission(ctx: SidecarContext, vault, repository, submission_id: str | None, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 687) — The response for a submission that was already committed, if any.
- `_resume_saved_completion(ctx: SidecarContext, vault, repository, work: dict[str, Any], submission_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 718) — Complete a committed attempt from its saved result and store the receipt.
- `_normalization_client(ctx: SidecarContext, vault) -> Any | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 741)
- `_open_session_id(repository, session_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 746)
- `_require_same_item(recorded_item_id: str, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 755)
- `_submission_committed(attempt: dict[str, Any]) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 760)
- `_store_submission_receipt(repository, submission_id: str | None, attempt_id: str, practice_item_id: str, payload: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 773)
- `_self_grade(payload: SelfGradeInputDto | None) -> SelfGradeInput | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 825)
- `_attempt_result(result, repository=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 843)
- `_log_attempt_recorded(repository, session_id: str, answer_md: str, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 861)
- `_latent_snapshot(vault, repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 886) — Capture pre-attempt latent state for a practice item, for debug deltas.
- `_log_state_update(vault, repository, method_name: str, session_id: str, before, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 915)
- `_display_mean(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 986)
- `_display_variance(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 994)
- `_require_open_session(repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1002)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `_log_attempt_recorded`; statically calls `_log_attempt_recorded`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `submission_key`; statically calls `submission_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `CompletionRouteUnknown`, `probe_route`, `run_post_attempt_pipeline`; calls `probe_route`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`; calls `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; calls `calibration_cap_lifted`, `routine_planner_shadow`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`; calls `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `probe_posterior`; calls `probe_posterior`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`, `build_due_queue`; calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `hint_equivalents_for_submission`; calls `hint_equivalents_for_submission`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_grading_provider`; calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `PracticeItemInput`, `_sections`; calls `_sections`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `practice_item_detail`, `scheduled_item_dtos`; calls `practice_item_detail`, `scheduled_item_dtos`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SessionCheckpointInput`, `patch_checkpoint`; calls `SessionCheckpointInput`, `patch_checkpoint`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `filter_unready_teach_back_items`; calls `filter_unready_teach_back_items`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `debug_enabled`, `log_event`; calls `debug_enabled`, `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]], [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_interrupted_submission_resumes_saved_result_once`
  - `test_recovery_normalizes_with_the_configured_grading_provider`
  - `test_submission_that_loses_a_commit_race_answers_with_the_winner`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
