---
title: "learnloop.attempts.attempts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/attempts.py"
source_paths:
  - "src/learnloop/attempts/attempts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.attempts module"
  - "src/learnloop/attempts/attempts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.attempts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps attempts behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `GradeAttribution`, `ResolvedGrade`, `AttemptResult`, `ApplyAttemptInput`, `AttemptPriorState` and 37 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py) |
| Source lines | 5743 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AttemptDraft` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 160)
- `class SelfGradeErrorAttribution` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 278) — One learner-attributed error from the self-grade form (spec §"self-grade").
- `class SelfGradeInput` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 293)
- `class GradeAttribution` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 303)
- `class ResolvedGrade` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 337)
- `class AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 365)
  - `as_dict(self) -> dict[str, object]` (line 405; public)
  - `from_dict(cls, saved: Mapping[str, Any]) -> AttemptResult` (line 433; public) — Rebuild a result saved with :meth:`as_dict`.
- `class ApplyAttemptInput` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 448) — Resolved attempt payload consumed by the shared attempt step.
- `class AttemptPriorState` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 527) — Prior learner/item state read once before computing one attempt.
  - `facet_recall_state(self, facet_id: str, practice_item_id: str | None=None) -> FacetRecallState | None` (line 541; public)
  - `facet_recall_by_scope(self, facets: Iterable[str], practice_item_id: str) -> dict[tuple[str, str | None], FacetRecallState | None]` (line 546; public)
- `class AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 555) — Computed attempt outputs before they are persisted.
- `class AttemptValidationError(ValueError)` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 596)
- `complete_attempt_with_codex_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime: AIRuntimeReport, codex_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 609)
- `complete_attempt_with_ai_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 633)
- `complete_attempt_with_codex_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime: AIRuntimeReport, codex_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 828)
- `complete_attempt_with_ai_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 849)
- `class GradingCallPlan` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 916) — The model grading one answer would send, computed with no call and no write.
  - `as_dict(self) -> dict[str, Any]` (line 930; public)
- `plan_grading_calls(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None, retimed_tasks: Mapping[str, str] | None=None) -> GradingCallPlan` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 939) — What the practice door would send to a grader for ``draft`` (read-only).
- `complete_self_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, grade: SelfGradeInput, *, fallback_reason: str | None=None, fallback_agent_run_id: str | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1106) — Record the learner's self-grade.
- `complete_empty_stuck_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1202) — Record an empty "I'm stuck" answer: an ordinary attempt scored 0.
- `complete_codex_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, proposal: GradingProposal, *, attempt_id: str | None=None, agent_run_id: str | None=None, grading_source: str='codex', diagnostic_sample_support: float | None=None, grader_mode: str | None=None, grader_identity: tuple[str, str] | None=None, manual_review_override: str | None=None, unverified_criterion_ids: Iterable[str]=(), grade_held_for_review: bool=False, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1267)
- `replay_reads_bounded_ledger(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1369) — Whether replay bounds its ledger reads at the replayed attempt (rebuild equivalence, ``REPLAY_LEDGER_VERSIONS`` and the kill switch ``replay.ledger_bounded``).
- `attempt_keeps_content_state(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1381) — Whether a live attempt writes only its item row's scheduling columns (mobile PR-4, ``ATTEMPT_CONTENT_STATE_VERSIONS`` and the kill switch ``practice.attempt_keeps_content_state``).
- `replay_existing_attempt(vault: LoadedVault, repository: Repository, attempt: dict, *, clock: Clock | None=None, error_event_ids: list[str] | None=None, error_events: list[dict[str, Any]] | None=None, error_attributions: list[GradeAttribution] | None=None, grader_identity: Any=_REPLAY_IDENTITY_FROM_LEDGER) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1393) — Recompute derived state for a persisted attempt without re-grading it.
- `class CurrentEpochReading` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1547) — What replay reads of an attempt's grade at ``mvp-0.26`` (regrade contracts).
- `current_epoch_reading(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], *, live_rows: Sequence[GradingEvidenceRecord] | None=None) -> CurrentEpochReading` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1567) — The current grading epoch of a persisted attempt as replay reads it at ``mvp-0.26`` (see :class:`CurrentEpochReading`; the epoch rule is :func:`learnloop.grading_epochs.current_epoch`).
- `snapshot_graded_contract(repository: Repository, vault: LoadedVault, item: PracticeItem, *, rubric: Rubric, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1612) — The assessment contract a regrade grades against (regrade contracts, mvp-0.26): the item it read with the rubric it graded under, snapshotted content-addressed in the caller's transaction (an unchanged item reuses its version).
- `unrecorded_epoch_attempts(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1625) — The persisted attempts replay at ``mvp-0.26`` holds because their current grading epoch's contract is unrecorded (:func:`current_epoch_reading`), as rows ``{attempt_id, learning_object_id, practice_item_id, recorded_max_points, correctness}`` in attempt order: what the upgrade t…
- `replay_grader_identity(repository: Repository, attempt_id: str, blind_record: Mapping[str, Any] | None) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1648) — The calibration identity a persisted grade replays under, from the ledgers.
- `agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1679) — Provider columns for a grading ``agent_runs`` row, client first, then runtime.
- `class GradedContract` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1847) — The assessment contract a recorded attempt was graded under (review F1).
  - `required_method(self) -> dict[str, Any] | None` (line 1854; public)
  - `rubric(self) -> Rubric` (line 1857; public)
  - `_froze(self, compiled: dict[str, Any]) -> bool` (line 1860; internal)
  - `graded_reference_contents(self, vault: LoadedVault, item: PracticeItem, connection: Any, attempt: Mapping[str, Any] | None=None) -> tuple[list[str], str, dict[str, str]]` (line 1864; public) — The answer-key revision(s) a regrade under this contract graded (review F13, F19).
- `attempt_graded_contract(repository: Repository, attempt_id: str) -> GradedContract | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2100) — The assessment contract a recorded attempt's evidence rows cite.
- `regrade_reads_contract(vault: LoadedVault, item: PracticeItem, graded: GradedContract | None) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2130) — Does a regrade grade the answer under its assessment contract (re-review F1)?
- `submit_eligibility_inputs(repository: Repository, practice_item_id: str, *, at: str, window_until: str | None=None, learning_object_id: str | None=None, submission_id: str | None=None, learner_answer_md: str | None=None, declared_primed: bool=False, auto_primed: bool=False, hints_used: int=0, attempt_type: str | None=None) -> serve_eligibility.EligibilityInputs` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2622) — The eligibility decision's inputs for a submission (the shell around ``serve_eligibility``): the ledger, the item's last attempt and its open follow-up tasks, with the draft's own disclosure exempt (rounds 4 and 5, F1-2: exactly the trace it froze; the one exemption, ``serve_eli…
- `reveal_total_for_submission(repository: Repository, practice_item_id: str, *, until: str | None=None, clock: Clock | None=None, submission_id: str | None=None, learner_answer_md: str | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2657) — Summed answer exposure on this item since the learner last attempted it.
- `auto_primed_draft(repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None, window_bounded: bool=False) -> tuple[AttemptDraft, float]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2703) — Force ``primed`` on a draft whose answer has already been handed over.
- `submit_decision(repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None, learning_object_id: str | None=None, retimed: Mapping[str, str | None] | None=None, window_bounded: bool=False, help_converts: bool=False) -> serve_eligibility.EligibilityDecision` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2752) — Submit's admissibility, asked of the one eligibility decision: a cold check (the first due task on the item is a cold one) must be unassisted and unprimed, and ANY primed draft is refused one (Codex review F1: an auto-primed draft is not exempt; its provenance only explains the…
- `validate_attempt_draft(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None, retimed_tasks: Mapping[str, str | None] | None=None) -> AttemptDraft` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2797) — Submit's validation of ``draft`` (read-only), raising :class:`AttemptValidationError` exactly as the completion doors would, so a door that asks the learner for an answer can ask it first (the CLI's attempt, §12.9).
- `publish_regraded_probe_grade(vault: LoadedVault, repository: Repository, *, attempt_id: str, grading_source: str, grader_identity: tuple[str, str] | None, fired_error_types: Iterable[str], held: bool, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3086) — A regrade's probe grade under the replacement grade's identity (TE2 landing ruling R1): the attempts package's door to :func:`learnloop.diagnosis.probe_episodes.dual_write_regraded_probe_grade` (the probe dual-writes live there, and this module already reads them), so the regrad…
- `apply_attempt(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3194) — Apply one resolved attempt through the shared learner-state pipeline.
- `compute_attempt_application(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, *, clock: Clock | None=None, prior_state: AttemptPriorState | None=None) -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3683) — Compute the rows and result for one resolved attempt without persisting.
- `unverified_attribution_json() -> str` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3900) — The persisted block of an unverified criterion (PF-c gate).
- `load_attempt_prior_state(vault: LoadedVault, repository: Repository, *, learning_object_id: str, practice_item_id: str, facets: Iterable[str], now_iso: str, ledger_before: tuple[str, str] | None=None) -> AttemptPriorState` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4269) — Read the prior-state snapshot used by one attempt computation.
- `resolved_codex_grade(validated: ValidatedCodexGrade, *, agent_run_id: str | None, clock: Clock | None, manual_review_reason: str | None=None) -> ResolvedGrade` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5469)
- `calculate_rubric_score(rubric: Rubric, criterion_points: dict[str, float], fatal_errors: list[str]) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5597)
- `assessed_rubric_score(rubric: Rubric, criterion_points: Mapping[str, float], fatal_errors: Iterable[str], *, unassessed_criterion_ids: Iterable[str], answer_validated: bool=True) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5610) — The grade over the ASSESSED criteria only (PF-c, owner decision 2026-10-12).
- `fsrs_rating_for_attempt(item: PracticeItem, rubric_score: int, max_points: int, hints_used: int) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5661) — FSRS rating for a graded attempt: score binning + the item's hint cap.

### Module constants

- `DONT_KNOW_ERROR_TYPE` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 138)
- `SCAFFOLD_FAILURE_ERROR_TYPE` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 139)
- `AUTO_PRIME_REVEAL_THRESHOLD` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 156)
- `DIFFICULTY_RATINGS` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 256)
- `FIRST_HINT_PROGRESS` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 257)
- `COLD_FOLLOWUP_TASK_KINDS` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 606)
- `_REPLAY_IDENTITY_FROM_LEDGER` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 1366)
- `_CURRENT_ITEM_METHOD` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 1763)

## Internal implementation anchors

- `_ad_logged_fields(vault: Any, draft: AttemptDraft) -> dict[str, str | None]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 260) — The AD1 columns this attempt records: each only with its switch on.
- `_complete_attempt_with_agent_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime, ai_client: AIProviderClient | None=None, grading_source: str, missing_client_reason: str, failure_prefix: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 657)
- `_finish_superseded_grading_run(repository: Repository, agent_run_id: str, ai_client: AIProviderClient, error: sqlite3.IntegrityError, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 777) — Close a grading run whose attempt the database refused.
- `_finish_run_after_grading_error(repository: Repository, agent_run_id: str, ai_client: AIProviderClient, attempt_id: str, error: Exception, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 799) — Close the grading run after an error; return whether its grade committed.
- `_try_deterministic_grade(vault: LoadedVault, repository: Repository, draft: AttemptDraft, item, rubric, *, clock: Clock | None=None) -> AttemptResult | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 870) — Grade an unambiguous option-letter selection without the model grader.
- `_complete_attempt_with_agent_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime, ai_client: AIProviderClient | None=None, grading_source: str, missing_client_reason: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1006)
- `_blind_record_identity(blind_record: Mapping[str, Any] | None) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1669)
- `_diagnostic_augmentation_setting(vault: LoadedVault, key: str, default: int | bool) -> int | bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1697) — Read the optional forward-compatible config block.
- `_augmented_grading_context(vault: LoadedVault, repository: Repository, item: PracticeItem, context: Any) -> Any` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1723)
- `class _BlindGradingPlan` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1752) — What a split vault's practice grading call is shown (§4.1, PF-c).
- `_graded_required_method(item: PracticeItem, contract: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1766) — The required method an answer is graded under (review F1).
- `_attempt_time_revision(connection: Any, attempt: Mapping[str, Any] | None, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1782) — The item revision the attempt's selection recorded, or None (method-explicit-3 review F8).
- `_blind_grading_plan(vault: LoadedVault, item: PracticeItem, context: Any, *, stuck: bool=False, required_method: Any=_CURRENT_ITEM_METHOD) -> _BlindGradingPlan` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2153) — The learner-blind context for one answer: item side + this answer only.
- `_grading_run_identity(context: Any, blind: _BlindGradingPlan | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2229)
- `_complete_joint_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, context: Any, *, ai_client: AIProviderClient, attempt_id: str, agent_run_id: str, grading_source: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2245) — Grade jointly (split off), apply it, and record its augmentation receipt.
- `_complete_blind_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, blind: _BlindGradingPlan, *, rubric: Rubric, ai_client: AIProviderClient, attempt_id: str, agent_run_id: str, grading_source: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2323) — Grade blind, apply the grade and its blind record in one transaction.
- `_client_model(client: Any) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2485) — The resolved model a client graded with (receipts record the same).
- `_record_blind_grading_receipt(repository: Repository, *, attempt_id: str, blind: _BlindGradingPlan, run: Any, client: AIProviderClient, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2491) — The grading-context receipt, with ``grader_mode='blind'`` (§10).
- `_blind_sample_count(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2541) — Blind grading samples per answer (one unless sampling is configured).
- `_joint_sample_count(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2549) — Joint grading (C3) samples per answer.
- `_run_augmented_diagnosis(vault: LoadedVault, client: AIProviderClient, context: Any) -> Any` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2571)
- `_record_diagnostic_augmentation(repository: Repository, *, attempt_id: str, context: Any, consensus: Any, client: AIProviderClient, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2581) — The Phase-C receipt, written in the grading transaction (Q14): a failure propagates and rolls the grade back, so a committed joint grade always has its receipt and a missing one means "not augmented".
- `_assessment_contract(repository: Repository, draft: AttemptDraft) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2607)
- `_resolve_attempt_target(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, replay: bool=False, clock: Clock | None=None, retimed_tasks: Mapping[str, str | None] | None=None, window_bounded: bool=False)` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2818)
- `_dual_write_grade_channel(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, application: 'AttemptApplication', *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2942) — P0.2 dual-write (spec_p0_measurement_correctness §4.1, §7.2): append a raw grade event + calibrated interpretation alongside the legacy attempt summary.
- `_record_lesson_probe(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, application: 'AttemptApplication', *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3028) — Teacher TE2 (spec_teacher_v1 rev 5 §11.3): a lesson probe's answer, which has no probe presentation, as evidence from the first serve.
- `_signature_matched(attempt: ApplyAttemptInput) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3115) — ``raw_grade_events.signature_matched`` for this grade.
- `_persist_repair_mapping_source(repository: Repository, result: AttemptResult, stored: Mapping[str, Any], *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3135) — Keep a replayed attempt's authored repair suggestions durable.
- `_persist_new_grade_feedback(repository: Repository, result: AttemptResult, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3173) — Write the feedback metadata of a newly applied grade.
- `_refold_server_hints(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput) -> ApplyAttemptInput` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3232) — Adaptive hints H2a (review round 2, V1): the submit's fold of shown server hints, taken again inside this ``BEGIN IMMEDIATE`` transaction.
- `_apply_attempt_in_transaction(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3267) — Compute and persist one attempt; the caller owns the transaction.
- `_record_grade_decision(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, application: AttemptApplication) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3549) — The live grade's decision record, and its hold's (refactor B7), last in the attempt's transaction.
- `_save_completion_work(vault: LoadedVault, repository: Repository, draft: AttemptDraft, result: AttemptResult, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3583) — Save the applied result in the attempt's own transaction.
- `_project_canonical_belief(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, before: tuple[str, str] | None=None, through: tuple[str, str] | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3627) — Recompute the canonical shared belief cache after an attempt (mvp-0.7).
- `_validate_probe_presentation(repository: Repository, application: AttemptApplication, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3652) — Pre-persist §5.4 validation: an invalid, mismatched, ended, or already consumed presentation reference is stripped so the attempt records as incidental evidence (and the unique presentation index never rejects the row).
- `_stamp_observation_lineage(vault: LoadedVault, repository: Repository, application: AttemptApplication, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3720) — Snapshot the assessment contract and stamp observation ids (KM §5.2).
- `_criterion_correlation_group(item: PracticeItem, criterion_id: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3926)
- `_persist_attempt_application(repository: Repository, application: AttemptApplication, *, replace_existing: bool, write_legacy_facet_state: bool=True, write_facet_uncertainty: bool=False, keep_content_state: bool=False) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3936)
- `_discrimination_profile_telemetry(match) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3989) — A5's per-attempt tally, from the ONE implementation of the arm vocabulary.
- `_record_discrimination_profile_match(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4002) — Persist the attempt's A5 judgement (Meas §3.A5, migration 143).
- `_record_error_hunt_outcome(repository: Repository, application: AttemptApplication, *, vault: LoadedVault | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4057) — Persist the attempt's A3 outcome and mint the §10 misconception candidate.
- `_record_exercised_facets(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4128) — Append the attempt's A6 trace observations (Meas §3.A6, migration 141).
- `_record_grading_clarification(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4169) — Persist the grader's clarification request, if it made a licensed one.
- `_auto_resolve_clean_error_events(vault: LoadedVault, repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4207) — Close the loop on stale error events (config ``[misconceptions]``).
- `_attempt_reference_status(vault: LoadedVault, repository: Repository, item: PracticeItem, draft: AttemptDraft, *, replay: bool) -> str` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4373) — The attempt-time answer-key signal (canonical sources S1, C3).
- `_compute_resolved_grade_application(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, attempt_id: str, grade: ResolvedGrade, clock: Clock | None=None, error_event_ids_override: list[str] | None=None, prior_state: AttemptPriorState | None=None, replay: bool=False, grading_source: str='self', agent_run_id: str | None=None, fallback_reason: str | None=None, grader_identity: tuple[str, str] | None=None, unassessed_criterion_ids: Iterable[str]=(), grade_held_for_review: bool=False, grade_contract_unrecorded: bool=False, unrecorded_correctness: float | None=None, reveal_window_bounded: bool=False, ledger_position: tuple[str, str] | None=None) -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 4390)
- `_fsrs_review_summary(rubric_score: Any, max_points: Any, hints_used: int, *, rating: Any, elapsed_days: float, previous_state: PracticeItemState | None, next_memory: Any, interval_days: float | None, interval_factor: Any, due_at: str | None, weights_fitted: bool, skipped: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5179) — What the FSRS review saw and did, for the grade's record: the rating and the one before the item's hint cap, the elapsed days, the state before and after, the interval and its factor, the due time; ``skipped`` names why no review applied.
- `_self_grade_attributions(vault: LoadedVault, fatal_errors: list[str], error_type: str | None, error_attributions: list[SelfGradeErrorAttribution] | None=None) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5207) — Resolve the learner's self-grade selections into the same flat ``GradeAttribution`` list Codex grading produces.
- `_canonicalized_grade_attributions(vault: LoadedVault, attributions: list[GradeAttribution]) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5260)
- `_primary_error_type(attributions: list[GradeAttribution]) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5308)
- `_attempt_manual_review_reason(existing: str | None, draft: AttemptDraft) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5314)
- `_dont_know_error_type(vault: LoadedVault, hints_used: int) -> str` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5326)
- `_error_event_repair_plan(vault: LoadedVault, attribution: GradeAttribution) -> dict[str, object] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5336)
- `_replay_error_attributions(vault: LoadedVault, error_type: str | None, *, error_events: list[dict[str, Any]] | None=None) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5380)
- `_validated_criterion_points(rubric: Rubric, points: dict[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5550)
- `_validated_self_grade_attributions(rubric: Rubric, attributions: list[SelfGradeErrorAttribution] | None) -> list[SelfGradeErrorAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5566) — Validate per-criterion self-grade error picks before they are resolved.
- `_validate_fatal_errors(rubric: Rubric, fatal_errors: list[str]) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5590)
- `_capped_rating(rating: Rating, item: PracticeItem, hints_used: int) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5671)
- `_hint_policy_value(mapping: dict[int | str, object], hints_used: int) -> object | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5679)
- `_rating_from_cap(value: object) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5697)
- `_memory_state(state: PracticeItemState | None) -> MemoryState | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5716)
- `_elapsed_days(state: PracticeItemState | None, observed_at) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5727)
- `_error_severity(vault: LoadedVault, error_type: str) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5736)
- `_is_misconception(vault: LoadedVault, error_type: str) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 5741)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `AttemptResult`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `GradeAttribution`, `_blind_grading_plan`, `assessed_rubric_score`, `attempt_graded_contract`, `publish_regraded_probe_grade`, `regrade_reads_contract`, `snapshot_graded_contract`, `unverified_attribution_json`; statically calls `GradeAttribution`, `_blind_grading_plan`, `assessed_rubric_score`, `attempt_graded_contract`, `publish_regraded_probe_grade`, `regrade_reads_contract`, `snapshot_graded_contract`, `unverified_attribution_json`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `attempt_graded_contract`, `regrade_reads_contract`; statically calls `attempt_graded_contract`, `regrade_reads_contract`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `plan_grading_calls`, `validate_attempt_draft`; statically calls `plan_grading_calls`, `validate_attempt_draft`
- [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]] — imports `resolved_codex_grade`; statically calls `resolved_codex_grade`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `AttemptDraft`, `AttemptValidationError`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `AttemptResult`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `unrecorded_epoch_attempts`; statically calls `unrecorded_epoch_attempts`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `AttemptResult`, `GradeAttribution`, `replay_existing_attempt`; statically calls `replay_existing_attempt`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `ApplyAttemptInput`, `AttemptDraft`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `apply_attempt`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`; statically calls `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `ApplyAttemptInput`, `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `agent_run_provider_fields`, `apply_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `resolved_codex_grade`; statically calls `resolved_codex_grade`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `attempt_graded_contract`; statically calls `attempt_graded_contract`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `AttemptValidationError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`; calls `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`, `legacy_codex_status`; calls `legacy_codex_status`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ATTEMPT_CONTENT_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `REPLAY_LEDGER_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `NON_RECORDING_ATTEMPT_TYPES`, `SUPPORTED_ATTEMPT_TYPES`, `unsupported_attempt_types`; calls `unsupported_attempt_types`
- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `estimate_ability_transition`; calls `estimate_ability_transition`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`, `GradingProposal`, `StuckGradingProposal`, `grading_prompt_version`; calls `grading_prompt_version`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BLIND_CALIBRATION_PROMPT_VERSION`, `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`, `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `split_grading_active`, `to_grading_proposal`, `validate_blind_grading_proposal`; calls `blind_context_from_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `split_grading_active`, `to_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `record_clarification`; calls `record_clarification`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/grade_records|learnloop.attempts.grade_records]] — imports `error_types_of`, `record_grade`; calls `error_types_of`, `record_grade`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`, `response_soft_score`; calls `record_grade_dual_write`, `response_soft_score`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `grading_context_hash`, `joint_grading_prompt_tokens`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `grading_context_hash`, `joint_grading_prompt_tokens`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading_admission|learnloop.attempts.grading_admission]] — imports `estimated_prompt_tokens`; calls `estimated_prompt_tokens`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `ITEM_REQUIRED_METHOD`, `REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION`, `family_key`, `gated_review_reason`, `grade_uncertainty_signal`, `method_rules_active`, `record_route_rule_judgment`, `reference_policy`, `request_blind_grading_run`, `revalidated_support`, `route_rules_suffix`, `route_rules_version`; calls `family_key`, `gated_review_reason`, `grade_uncertainty_signal`, `method_rules_active`, `record_route_rule_judgment`, `reference_policy`, `request_blind_grading_run`, `revalidated_support`, `route_rules_suffix`, `route_rules_version`
- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `ServerHintFold`, `attach_held`, `attach_keyed`, `attach_keyless`, `refolded_draft`; calls `attach_held`, `attach_keyed`, `attach_keyless`, `refolded_draft`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `reject_salience`; calls `reject_salience`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `EMPTY_STUCK_EVIDENCE`, `EMPTY_STUCK_FEEDBACK`, `EMPTY_STUCK_GRADER_TIER`, `EMPTY_STUCK_LOCAL_GRADER_ID`, `STUCK_READING_KEY`, `is_empty_stuck`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `stuck_prompt_active`, `verified_stuck_reading`; calls `is_empty_stuck`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `stuck_prompt_active`, `verified_stuck_reading`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `compute_surprise`; calls `compute_surprise`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `LESSON_PROBE_EVIDENCE_ORIGIN`, `LESSON_PROBE_EXPOSED_SOURCE`, `LESSON_PROBE_SOURCE`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `maybe_promote_self_tagged_fatal_error`; calls `maybe_promote_self_tagged_fatal_error`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `FacetRecallState`, `FacetUncertaintyState`, `GradingEvidenceRecord`, `ItemParameterState`, `MasteryState`, `PracticeItemQualityState`, `PracticeItemState`, `Repository`; calls `PracticeItemState`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `AMBIGUOUS_DEFAULT_REVISION`, `AMBIGUOUS_METHOD_REVISION`, `KEY_IDENTITY`, `KEY_IDENTITY_FIELD`, `checked_content_hashes`, `reference_content_hash`, `reference_status_for_item`; calls `checked_content_hashes`, `reference_content_hash`, `reference_status_for_item`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `grading_in_progress`, `record_grading`; calls `grading_in_progress`, `record_grading`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `classify_attempt_activity`; calls `classify_attempt_activity`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `materialize_causal_episode`; calls `materialize_causal_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `DEFAULT_DIAGNOSIS_SAMPLES`, `DEFAULT_HISTORY_LIMIT`, `PHASE_C_HYPOTHESES`, `PHASE_C_REVERT_CRITERIA`, `augment_grading_context`, `diagnostic_verifier_observations`, `record_phase_c_receipt`, `run_diagnosis_samples`; calls `augment_grading_context`, `diagnostic_verifier_observations`, `record_phase_c_receipt`, `run_diagnosis_samples`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `profile_match_telemetry`; calls `profile_match_telemetry`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`; calls `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `persist_unknown_error_type_proposals`; calls `persist_unknown_error_type_proposals`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`; calls `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `record_remediation_attempt`; calls `record_remediation_attempt`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `record_certification_cold_probe_attempt`; calls `record_certification_cold_probe_attempt`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`, `only_grade`; calls `current_epoch`, `only_grade`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`, `record_held_for_review`; calls `held_attempt_ids`, `record_held_for_review`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `compile_assessment_contract`, `contract_required_method`, `rubric_from_contract`, `snapshot_for_presentation`; calls `compile_assessment_contract`, `contract_required_method`, `rubric_from_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`; calls `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetStateReader`, `canonical_facet_uncertainty_on`, `canonical_uncertainty_rows`, `current_facet_uncertainty`, `is_canonical_state_vault`, `resolve_canonical_facet`; calls `CanonicalFacetStateReader`, `canonical_facet_uncertainty_on`, `canonical_uncertainty_rows`, `current_facet_uncertainty`, `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `lesson_check_mass`; calls `lesson_check_mass`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `MasteryObservationTrace`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`; calls `MasteryObservation`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `build_facet_recall_updates_from_prior`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity_from_attempts`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`; calls `build_facet_recall_updates_from_prior`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity_from_attempts`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`, `target_criterion_facet_weights`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_CONTRACT_UNRECORDED`, `HELD_ROW_KEY`, `grade_held_for_review`, `grade_is_held`; calls `grade_held_for_review`, `grade_is_held`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `servable_open_episode`; calls `servable_open_episode`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `interval_factor_removed`; calls `interval_factor_removed`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`; calls `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decide`, `decision_active`, `gather`, `help_converts_active`, `log_decision`, `submit_exposure`, `with_pending_writes`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `evidence_eligibility_for`; calls `evidence_eligibility_for`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `hot_path_applies_practice_review`; calls `hot_path_applies_practice_review`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `project_canonical_facet_state`, `unassessed_evidence_row`; calls `project_canonical_facet_state`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]], [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] and 32 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/assumed_known_helpers.py](../../../../../../tests/assumed_known_helpers.py) — direct import
- [tests/causal_cold_outcomes_helpers.py](../../../../../../tests/causal_cold_outcomes_helpers.py) — direct import
- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — direct import
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/certification_cold_probe_helpers.py](../../../../../../tests/certification_cold_probe_helpers.py) — direct import
- [tests/cold_retry_reschedule_helpers.py](../../../../../../tests/cold_retry_reschedule_helpers.py) — direct import
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — direct import
- [tests/diagnostic_augmentation_helpers.py](../../../../../../tests/diagnostic_augmentation_helpers.py) — direct import
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../tests/diagnostic_probe_single_use_helpers.py) — direct import
- [tests/durable_promotion_arms_helpers.py](../../../../../../tests/durable_promotion_arms_helpers.py) — direct import
- [tests/exam_session_helpers.py](../../../../../../tests/exam_session_helpers.py) — direct import
- [tests/facet_evidence_timeline_helpers.py](../../../../../../tests/facet_evidence_timeline_helpers.py) — direct import
- [tests/followup_journey_helpers.py](../../../../../../tests/followup_journey_helpers.py) — direct import
- [tests/followups_helpers.py](../../../../../../tests/followups_helpers.py) — direct import
- [tests/forecast_receipts_helpers.py](../../../../../../tests/forecast_receipts_helpers.py) — direct import
- [tests/graph_editor_reads_helpers.py](../../../../../../tests/graph_editor_reads_helpers.py) — direct import
- [tests/guided_redo_helpers.py](../../../../../../tests/guided_redo_helpers.py) — direct import
- [tests/held_grade_evidence_helpers.py](../../../../../../tests/held_grade_evidence_helpers.py) — direct import
- [tests/hint_h2b_review_helpers.py](../../../../../../tests/hint_h2b_review_helpers.py) — direct import
- [tests/km2_write_path_helpers.py](../../../../../../tests/km2_write_path_helpers.py) — direct import
- [tests/km3_projections_helpers.py](../../../../../../tests/km3_projections_helpers.py) — direct import
- [tests/learner_text_gaps_review_helpers.py](../../../../../../tests/learner_text_gaps_review_helpers.py) — direct import
- [tests/p2_acceptance_helpers.py](../../../../../../tests/p2_acceptance_helpers.py) — direct import
- [tests/pfc_unassessed_readers_helpers.py](../../../../../../tests/pfc_unassessed_readers_helpers.py) — direct import
- [tests/probe_block_end_helpers.py](../../../../../../tests/probe_block_end_helpers.py) — direct import
- [tests/probe_orchestration_remainder_helpers.py](../../../../../../tests/probe_orchestration_remainder_helpers.py) — direct import
- [tests/probe_robust_cutover_helpers.py](../../../../../../tests/probe_robust_cutover_helpers.py) — direct import
- [tests/reader_recap_review_r2_helpers.py](../../../../../../tests/reader_recap_review_r2_helpers.py) — direct import
- [tests/rebuild_equivalence_helpers.py](../../../../../../tests/rebuild_equivalence_helpers.py) — direct import
- [tests/reference_gate_imports_helpers.py](../../../../../../tests/reference_gate_imports_helpers.py) — direct import
- [tests/regrade_contract_replay_helpers.py](../../../../../../tests/regrade_contract_replay_helpers.py) — direct import
- [tests/remediation_cold_retry_helpers.py](../../../../../../tests/remediation_cold_retry_helpers.py) — direct import
- [tests/ro1_interval_factor_helpers.py](../../../../../../tests/ro1_interval_factor_helpers.py) — direct import
- [tests/ro1_self_report_helpers.py](../../../../../../tests/ro1_self_report_helpers.py) — direct import
- [tests/router_r2a_serving_helpers.py](../../../../../../tests/router_r2a_serving_helpers.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/split_live_helpers.py](../../../../../../tests/split_live_helpers.py) — direct import
- [tests/state_sync_scheduling_race_helpers.py](../../../../../../tests/state_sync_scheduling_race_helpers.py) — direct import
- [tests/stuck_prompt_helpers.py](../../../../../../tests/stuck_prompt_helpers.py) — direct import
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — direct import
  - `test_the_attempt_layer_validates_the_tap_and_the_marker`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — direct import
  - `test_answer_confidence_must_be_a_1_to_5_committed_tap`
  - `test_post_reveal_confidence_tap_cannot_land_on_a_graded_attempt`
- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_the_loader_reads_the_tap_and_the_graders_tone_reading`
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_legacy_attempt_records_no_observation_lineage`
  - `test_mvp07_attempt_stamps_observation_lineage`
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — direct import
  - `test_attempt_ai_flow_records_provider_model_and_ai_source`
- [tests/test_attempt_chain_records.py](../../../../../../tests/test_attempt_chain_records.py) — direct import
  - `test_a_live_held_attempt_writes_its_hold_record_in_the_attempt_step`
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_block_closing_diagnostic_answer_keeps_grader_provenance`
  - `test_committed_model_grade_keeps_its_provenance_through_recovery`
  - `test_grading_run_that_loses_a_submission_race_is_closed`
  - `test_pipeline_keeps_one_hypothesis_version_with_grader_provenance`
  - `test_saved_result_loads_across_field_changes`
  - `test_self_grade_fallback_records_why_and_which_run_failed`
- [tests/test_attempt_content_state_race.py](../../../../../../tests/test_attempt_content_state_race.py) — direct import
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_the_gate_is_the_tag_and_its_switch`
- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — direct import
  - `test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post`
- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — direct import
  - `test_attempt_links_to_scheduler_slate_and_later_retention_label`
  - `test_hinted_attempt_caps_fsrs_rating`
  - `test_self_graded_attempt_updates_attempt_evidence_state_and_surprise`
  - `test_unknown_attempt_type_fails_before_sqlite_insert`
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — direct import
  - `test_startup_records_one_recalibration_for_an_unstamped_practised_vault`
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — direct import
  - `test_exhibit_positive_control_preserves_genuine_multiplication_failure`
  - `test_exhibit_replay_blocks_false_targets_promotion_and_retry`
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_learner_confirmation_resolves_factor_to_provisional_belief`
  - `test_machine_review_scope_blocks_negative_observation_attribution`
  - `test_nonconfirming_self_report_is_recorded_once_without_reprompt`
  - `test_write_boundary_persists_firewall_telemetry`
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — direct import
- [tests/test_causal_attribution_p2.py](../../../../../../tests/test_causal_attribution_p2.py) — direct import
  - `test_cold_success_updates_repair_effect_not_diagnosis`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_an_auto_primed_attempt_can_never_resolve_a_factor`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_cold_verification_is_carried_through_the_followup_task`
  - `test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes`
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage`
  - `test_auto_classification_declines_a_sensor_it_cannot_read`
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_diagnosis_support_moves_only_on_independent_discriminating_evidence`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
  - `test_cold_verification_records_its_near_clone_basis`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_causal_trace_consistency_p2.py](../../../../../../tests/test_causal_trace_consistency_p2.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_a_queued_probe_refuses_an_assisted_attempt`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
- [tests/test_characterization_certification_ledger.py](../../../../../../tests/test_characterization_certification_ledger.py) — direct import
- [tests/test_characterization_probe_regrade.py](../../../../../../tests/test_characterization_probe_regrade.py) — direct import
- [tests/test_characterization_probe_replay.py](../../../../../../tests/test_characterization_probe_replay.py) — direct import
- [tests/test_characterization_probe_submission.py](../../../../../../tests/test_characterization_probe_submission.py) — direct import
- [tests/test_codex_attempt_flow.py](../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_attempt_orchestration_falls_back_and_marks_agent_run_failed`
  - `test_attempt_orchestration_falls_back_when_runtime_not_ready`
  - `test_attempt_orchestration_uses_codex_when_runtime_ready`
  - `test_codex_attempt_uses_highest_severity_error_for_observed_joint`
  - `test_codex_blank_attempt_is_flagged_for_manual_review`
  - `test_codex_graded_attempt_proposes_unknown_error_type`
  - `test_codex_graded_attempt_uses_same_update_path_with_tier_three_evidence`
  - `test_codex_recall_wording_uses_recall_failure_not_new_error_type`
- [tests/test_codex_transport_retired.py](../../../../../../tests/test_codex_transport_retired.py) — direct import
  - `test_an_attempt_graded_by_codex_replays_identically`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_exact_offer_survives_refresh_recovery_and_dataset_export`
  - `test_export_preserves_censored_repair_disposition_as_distinct_from_failure`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_learner_derived_hypothesis_defaults_learner_state_and_offer_survives`
  - `test_receipted_divergence_skips_the_consultation_entirely`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_apply_writes_one_boundary_and_a_rerun_writes_none`
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
  - `test_written_question_keeps_returning_after_it_is_answered`
- [tests/test_daily_loop_reentry_break.py](../../../../../../tests/test_daily_loop_reentry_break.py) — direct import
- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_ai_regrade_records_provider_and_ai_origin`
  - `test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed`
  - `test_deferred_regrade_preserves_blank_answer_manual_review`
  - `test_deferred_regrade_recomputes_downstream_attempts_for_learning_object`
  - `test_deferred_regrade_records_disagreement_event`
  - `test_deferred_regrade_replays_attempt_derived_state`
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
  - `test_deferred_regrade_skips_when_runtime_not_ready`
  - `test_deferred_regrade_supersedes_self_grade_and_updates_mastery`
  - `test_deferred_regrade_validates_repaired_trace_against_learner_answer`
  - `test_startup_maintenance_regrades_pending_self_grade_when_codex_ready`
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — direct import
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_diagnosis_pipeline.py](../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_a_self_graded_fallback_is_regraded_blind_and_queues_its_diagnosis`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_a_committed_joint_grade_carries_its_receipt_and_grading_record`
  - `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`
  - `test_c3_k1_leaves_no_sample_support_on_the_stored_attribution`
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_item_filters_and_the_required_estimator`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker`
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_gate_section_counts_manual_false_negatives`
  - `test_propensity_report_marks_composed_offers_unavailable_not_degenerate`
  - `test_report_on_real_session_flow`
- [tests/test_evsi_router_composition.py](../../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_only_never_attempted_items_are_reservable`
  - `test_uncovered_facets_reported_when_no_item_tests_a_facet`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_seeded_exam_interleaves_before_later_live_attempt`
- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_a_legacy_era_uncertainty_row_is_never_the_successors_prior_or_read`
  - `test_uncertainty_is_written_under_the_merged_facets_survivor`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_hedged_learner_confidence_opens_uncertainty_even_with_partial_credit`
  - `test_open_facet_restriction_makes_disjoint_correct_attempt_zero_weight`
  - `test_variance_floor_blocks_confidence_before_required_facet_breadth`
- [tests/test_facet_state_write_on_change.py](../../../../../../tests/test_facet_state_write_on_change.py) — direct import
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_real_receipt_from_apply_attempt_does_not_force_tier_two`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_review_f2_the_row_survives_the_submit_on_the_vault`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f6_a_crash_right_after_a_probe_answer_has_settled_its_workflow`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
- [tests/test_followups.py](../../../../../../tests/test_followups.py) — direct import
  - `test_negative_surprise_followup_stops_forcing_after_followup_attempt`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_f2_editing_todays_rubric_never_rewrites_a_regraded_self_grade`
- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_known_gap_and_uncertain_facets_are_both_on_frontier`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_known_gap_facet_is_never_on_track`
- [tests/test_goal_series.py](../../../../../../tests/test_goal_series.py) — direct import
  - `test_series_reflects_evidence_arriving_over_time`
  - `test_series_replays_past_an_adjudicated_attempt`
  - `test_series_replays_past_non_cascading_attempt_references`
  - `test_series_shares_one_replay_across_unchanged_checkpoints`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_bootstrap_frame_logs_inclusion_probabilities_and_is_deterministic`
  - `test_dual_write_failure_never_breaks_legacy_path`
  - `test_dual_write_mint_failure_is_logged_not_silent`
  - `test_exam_answer_dual_writes_assessment_grade`
  - `test_practice_attempt_dual_writes_raw_event_and_interpretation`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
  - `test_calibration_ordering_reverts_to_plain_rate`
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_an_empty_stuck_answer_never_reaches_the_grader`
  - `test_router_never_scores_a_held_attempt_and_its_fold_applies_no_review`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
- [tests/test_hint_evidence.py](../../../../../../tests/test_hint_evidence.py) — direct import
  - `test_levels_one_to_three_add_one_each_and_attach_to_the_attempt`
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f6_a_goal_reached_before_the_next_hint_counts_as_reached_without_more_help`
  - `test_f7_surface_filters_the_chooser_statistics_and_avoidance`
- [tests/test_hint_report.py](../../../../../../tests/test_hint_report.py) — direct import
- [tests/test_hot_path_eligibility_cutover.py](../../../../../../tests/test_hot_path_eligibility_cutover.py) — direct import
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_the_report_measures_marks_against_delayed_performance`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_r2_one_attributable_disclosure_function`
- [tests/test_intervention_outcomes_replayer.py](../../../../../../tests/test_intervention_outcomes_replayer.py) — direct import
  - `test_the_replayer_is_registered_deterministic_and_calls_nothing`
  - `test_the_replayer_reads_persisted_exposure`
- [tests/test_irt_end_to_end.py](../../../../../../tests/test_irt_end_to_end.py) — direct import
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
  - `test_upgrade_projects_existing_attempts_into_canonical_facet_state`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_explicit_failure_attribution_penalizes_only_selected_target`
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_blind_graders_context_is_byte_identical_in_every_arm_and_switch_setting`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_stuck_answer_reads_one_attempt_exactly_as_stuck_answers_does`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
  - `test_the_persisted_repair_class_is_the_structurally_selected_one`
- [tests/test_misconception_resolution.py](../../../../../../tests/test_misconception_resolution.py) — direct import
  - `test_low_correctness_attempt_does_not_count_as_clean`
- [tests/test_misconception_routing.py](../../../../../../tests/test_misconception_routing.py) — direct import
- [tests/test_missing_vocabulary_notes.py](../../../../../../tests/test_missing_vocabulary_notes.py) — direct import
  - `test_a_resolved_diagnosis_writes_no_note`
- [tests/test_model_grade_lane.py](../../../../../../tests/test_model_grade_lane.py) — direct import
  - `test_rebuild_moves_only_learning_objects_with_model_graded_attempts`
- [tests/test_mvp017_route_check_replay.py](../../../../../../tests/test_mvp017_route_check_replay.py) — direct import
  - `test_the_bounded_replay_corrects_the_copy_in_one_rebuild_and_then_changes_nothing`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_canonical_projection_bulk_loads_historical_contracts_once`
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_primed_provenance_reaches_projection_and_blocks_certification`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_cutover_delta_is_nonempty_and_inspectable_when_projections_differ`
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
  - `test_upgrade_does_not_rewrite_raw_history`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_complement_route_is_graded_on_its_assessed_criteria_only`
  - `test_a_located_error_beside_an_unverified_criterion_still_counts`
  - `test_joint_fixture_replays_through_the_unchanged_path`
  - `test_the_stamped_block_is_read_from_text_or_mapping`
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
- [tests/test_placement_unevidenced_return.py](../../../../../../tests/test_placement_unevidenced_return.py) — direct import
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_usage_signals_are_ledgered_and_joined_to_attempts`
- [tests/test_predictive_eig.py](../../../../../../tests/test_predictive_eig.py) — direct import
  - `test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero`
- [tests/test_probe_attempt_updates.py](../../../../../../tests/test_probe_attempt_updates.py) — direct import
  - `test_attempt_service_never_writes_legacy_probe_state`
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
  - `test_regrade_checks_record_agreement_and_confusion`
- [tests/test_probe_belief_posterior.py](../../../../../../tests/test_probe_belief_posterior.py) — direct import
  - `test_dont_know_outcome_does_not_break_posterior`
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_migration.py](../../../../../../tests/test_probe_migration.py) — direct import
  - `test_legacy_probe_history_replays_identically_after_migration`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_out_of_range_is_rejected`
- [tests/test_probe_policy.py](../../../../../../tests/test_probe_policy.py) — direct import
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import
  - `test_active_seconds_is_a_nullable_attempt_column_filled_after_the_row_and_never_blended_with_latency`
- [tests/test_reader_activity.py](../../../../../../tests/test_reader_activity.py) — direct import
  - `test_every_client_event_is_salience_only_and_never_evidence`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_a_hinted_cold_retry_is_practice_with_help_and_never_consumes_the_measurement`
  - `test_switched_off_a_hinted_cold_retry_is_refused_as_before`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_each_ca6_event_is_salience_only_keeps_ids_and_drops_words`
- [tests/test_reader_followup_valuation.py](../../../../../../tests/test_reader_followup_valuation.py) — direct import
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_without_fsrs_state_the_date_is_the_schedulers_first_interval`
- [tests/test_reader_recap.py](../../../../../../tests/test_reader_recap.py) — direct import
  - `test_claims_needing_an_independent_check_are_assisted_only_facets`
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_displayed_excerpt_is_debited_once`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_bad_item_suspicion_uses_prior_snapshot_not_current_attempt_update`
  - `test_blank_independent_attempt_is_damped_and_flagged_for_manual_review`
  - `test_diagnostic_generation_stales_resolved_repeat_failure_need`
  - `test_dont_know_keeps_full_coverage_and_updates_facet_recall`
  - `test_error_attribution_target_facets_are_canonicalized_before_facet_outcomes`
  - `test_error_attribution_targets_unmapped_facet_before_whole_item_fallback`
  - `test_facet_aliases_are_canonicalized_before_recall_updates`
  - `test_high_unfamiliar_probe_posterior_records_intervention_need`
  - `test_hinted_dont_know_is_scaffold_failure_and_dampens_coverage_only_from_surface_policy`
  - `test_intervention_need_targets_failed_facet_not_whole_item`
  - `test_intervention_needs_canonicalize_target_facets_for_dedup`
  - `test_repeated_failure_triggers_intervention_need_without_surprise`
  - `test_rubric_criterion_names_infer_targeted_facet_outcomes`
  - `test_second_same_facet_failure_counts_across_different_items`
  - `test_success_breaks_item_streak_before_a_later_failure`
  - `test_success_resets_repeat_failure_gate_and_coverage_is_not_failed`
  - `test_zero_score_independent_attempt_uses_rubric_coverage_and_confidence_as_reliability`
- [tests/test_recurrence_deferral.py](../../../../../../tests/test_recurrence_deferral.py) — direct import
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_upgrade_holds_exactly_the_unrecorded_epochs_and_rewrites_no_evidence`
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_exam_attempt_does_not_consume_the_cold_retry`
  - `test_served_cold_attempt_is_enforced_unassisted_and_unprimed`
- [tests/test_replay.py](../../../../../../tests/test_replay.py) — direct import
  - `test_compute_attempt_application_materializes_outputs_without_persisting`
  - `test_compute_attempt_application_uses_explicit_prior_snapshot`
  - `test_learning_object_replay_matches_live_state_and_is_idempotent`
  - `test_live_and_replay_drive_shared_apply_attempt_step`
  - `test_rebuild_derived_state_replays_attempt_logs`
  - `test_replay_error_attributions_preserve_misconception_fields`
  - `test_replay_preserves_targeted_error_attribution_facets`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_the_grader_reads_the_frozen_field_never_the_answered_statement`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_a_revealed_cold_item_cannot_burn_its_cold_measurement`
  - `test_an_auto_primed_attempt_replays_as_primed`
  - `test_reveal_over_threshold_forces_primed_and_records_why`
  - `test_reveal_under_threshold_leaves_the_attempt_unprimed`
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
- [tests/test_ro1_availability.py](../../../../../../tests/test_ro1_availability.py) — direct import
  - `test_an_ordinary_attempt_records_no_received_at`
- [tests/test_ro1_availability_reads.py](../../../../../../tests/test_ro1_availability_reads.py) — direct import
- [tests/test_ro1_interval_factor.py](../../../../../../tests/test_ro1_interval_factor.py) — direct import
- [tests/test_ro1_upgrade_report.py](../../../../../../tests/test_ro1_upgrade_report.py) — direct import
- [tests/test_ro5_picks.py](../../../../../../tests/test_ro5_picks.py) — direct import
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade`
- [tests/test_router_coldness_covariates.py](../../../../../../tests/test_router_coldness_covariates.py) — direct import
  - `test_the_replayer_records_the_fsrs_predicted_retrievability`
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_apply_attempt_chokepoint_rejects_salience`
  - `test_firewall_carve_out_admits_only_listed_kinds`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_uses_prospective_familiarity_discount`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_censored_learning_objects_are_reported_and_excluded_from_the_mean`
  - `test_certification_replay_prunes_past_an_adjudicated_attempt`
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
  - `test_no_promotion_when_label_already_rubric_fatal`
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_dont_know_allowed_when_not_in_attempt_types`
  - `test_self_grade_attribution_rejects_unknown_criterion`
  - `test_self_grade_per_criterion_attribution_writes_error_event`
  - `test_self_grade_uses_criterion_total_as_item_scale`
  - `test_self_grade_uses_default_rubric_when_inline_rubric_is_omitted`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_q33_an_exam_seeded_before_a_later_reveal_is_not_primed`
  - `test_q33_the_bounded_window_also_bounds_the_last_attempt`
  - `test_submit_exposure_is_the_sql_total_row_for_row`
  - `test_submit_refusal_names_the_change_since_the_serve`
  - `test_the_cold_delay_is_the_remediation_delay_and_the_constants_are_one`
  - `test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice_and_ends_it_honestly`
  - `test_the_real_serve_paths_agree_with_submit`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_withdrawn_when_its_item_can_no_longer_take_it_cold`
  - `test_f1_an_auto_primed_draft_is_refused_when_its_cold_task_falls_due_during_grading`
  - `test_f2_a_certification_probe_whose_answer_was_shown_expires_unmeasured`
  - `test_f3_a_cold_check_is_never_served_on_an_item_practised_since_it_was_set`
  - `test_f3_a_cold_check_served_unpractised_is_still_served`
  - `test_f3_a_delayed_open_and_submit_after_a_withdrawing_build_are_plain_practice`
  - `test_f4_below_the_tag_or_switched_off_a_practised_cold_check_is_served`
  - `test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026`
  - `test_f4_the_plan_serves_the_12_9_case_as_mvp_026_with_the_switch_off`
  - `test_f5_a_withdrawal_racing_a_consume_leaves_the_consume_time_disposition_free`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_attempt_includes_grading_and_surprise`
  - `test_show_inspects_every_deterministic_id`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_knowledge_field_is_recipe_topological_and_uses_pooled_ready`
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_finished_report_carries_per_item_feedback_and_repairs`
- [tests/test_sidecar_knowledge_model.py](../../../../../../tests/test_sidecar_knowledge_model.py) — direct import
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_auto_primed_reports_the_reveal_total_behind_the_reclassification`
  - `test_session_counts_cold_checks_answered_and_confirmed_separately`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_the_primed_retry_adapter_tries_sources_before_generating`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_deactivating_sync_keeps_an_attempt_committed_after_its_snapshot`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_stuck_draft_is_refused_where_the_control_is_not_offered`
  - `test_a_worked_answer_shown_in_the_attempts_own_second_still_primes_the_retry`
  - `test_an_empty_stuck_answer_carries_the_standard_mass_not_dont_knows`
  - `test_an_empty_stuck_answer_is_a_bare_zero_with_no_error_tag`
  - `test_an_empty_stuck_answer_needs_no_provider_and_ignores_a_self_grade`
  - `test_an_empty_stuck_probe_answer_is_the_unanswered_observation`
  - `test_only_post_attempt_displays_cross_the_same_second_boundary`
  - `test_the_fallback_door_also_skips_the_letter_shortcut_for_a_stuck_answer`
  - `test_the_tui_worked_answer_is_recorded_as_a_reveal_and_primes_the_retry`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_historical_dont_know_rows_replay_unchanged_under_the_successor`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_teacher_te1_lesson.py](../../../../../../tests/test_teacher_te1_lesson.py) — direct import
  - `test_read_source_find_sources_find_practice_and_read_history_return_safe_results`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_r3_f4_an_item_held_out_after_its_history_was_read_ends_the_lesson`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_shadow_rebuild_after_a_lesson_has_zero_projection_deltas`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_a_primed_or_hinted_or_seen_or_earlier_attempt_never_resolves_a_check`
  - `test_the_tap_recalibration_learns_from_every_tapped_graded_answer`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_the_candidate_reasons`
  - `test_the_outcome_is_r_cold_on_the_drawn_lo_shown_or_not`
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_the_forecast_report_resolves_it_on_the_first_cold_outcome`
- [tests/test_teacher_te2log_report.py](../../../../../../tests/test_teacher_te2log_report.py) — direct import
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — direct import
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1_a_review_after_the_cold_delay_is_recorded_unprimed_a_retry_before_it_primed`
  - `test_f1g_every_committed_display_row_counts_until_its_coverage_ends`
  - `test_f1i_the_scheduler_never_serves_a_cold_retry_that_submit_would_refuse`
  - `test_f1r_feedback_reopened_after_the_cold_delay_is_a_fresh_exposure`
- [tests/test_ux_phase4_landing.py](../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/ux_phase4_feedback_helpers.py](../../../../../../tests/ux_phase4_feedback_helpers.py) — direct import
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change attempts policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
