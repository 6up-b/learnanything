---
title: "learnloop_sidecar.handlers.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/practice.py"
source_paths:
  - "src/learnloop_sidecar/handlers/practice.py"
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

This module keeps practice behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `PracticeDraftCheckpoint`, `PracticeSubmissionRecoveryInput`, `PracticeSubmissionAcknowledgementInput`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SubmitAttemptInput`, `DontKnowInput`, `SkipInput` and 15 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) |
| Source lines | 898 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PracticeDraftCheckpoint(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 51)
- `class PracticeSubmissionRecoveryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 61)
- `class PracticeSubmissionAcknowledgementInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 67)
- `class SelfGradeErrorAttributionDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 73)
- `class SelfGradeInputDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 78)
- `class SubmitAttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 87)
- `class DontKnowInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 109)
- `class SkipInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 121)
- `class ServePracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 126)
- `get_practice_item(ctx: SidecarContext, params: ServePracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 150) — Serve one item, carrying A6's elicitation decision for this serve.
- `class ProbeContractInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 191)
- `get_probe_contract(ctx: SidecarContext, params: ProbeContractInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 233) — The probe measurement contract for opening one item (§12).
- `stop_probe_diagnosing(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 321) — `Stop diagnosing and teach me` (§3): end the measurement block, persist the typed transition decision, and open a post-intervention state segment.
- `class NextProbeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 333)
- `get_next_probe_item(ctx: SidecarContext, params: NextProbeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 338) — The item that would continue this LO's open diagnostic block, if any.
- `class OverconfidenceProbeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 354)
- `start_overconfidence_probe(ctx: SidecarContext, params: OverconfidenceProbeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 360) — Launch a diagnostic episode from the F5 overconfidence list (§4.3).
- `save_practice_draft(ctx: SidecarContext, params: PracticeDraftCheckpoint) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 389)
- `recover_practice_submission(ctx: SidecarContext, params: PracticeSubmissionRecoveryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 406) — Recover a completed submit before trying to serve the item again.
- `acknowledge_practice_submission(ctx: SidecarContext, params: PracticeSubmissionAcknowledgementInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 440) — Clear only the checkpoint whose authoritative result was received.
- `submit_attempt(ctx: SidecarContext, params: SubmitAttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 468)
- `submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 581)
- `skip_practice_item(ctx: SidecarContext, params: SkipInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 680)

### Module constants

- `_OTHER_SESSION` ([src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 197)

## Internal implementation anchors

- `_require_active_item(vault, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 134) — One terminal lifecycle gate for every practice write/serve.
- `_committed_presentation(repository, episode, session_id: str | None)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 200) — The durable presentation this open of the item should consume.
- `_submission_id(client_id: str | None, presentation_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 622) — Return the stable retry key; old probe clients inherit one for free.
- `_cached_submission(repository, submission_id: str | None, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 632)
- `_store_submission_receipt(repository, submission_id: str | None, attempt_id: str, practice_item_id: str, payload: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 662)
- `_self_grade(payload: SelfGradeInputDto | None) -> SelfGradeInput | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 711)
- `_attempt_result(result, repository=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 729)
- `_log_attempt_recorded(repository, session_id: str, answer_md: str, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 751)
- `_latent_snapshot(vault, repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 776) — Capture pre-attempt latent state for a practice item, for debug deltas.
- `_log_state_update(vault, repository, method_name: str, session_id: str, before, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 805)
- `_display_mean(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 876)
- `_display_variance(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 884)
- `_require_open_session(repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 892)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `_log_attempt_recorded`; statically calls `_log_attempt_recorded`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptValidationError`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `run_post_attempt_pipeline`; calls `run_post_attempt_pipeline`
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

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
