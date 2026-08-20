---
title: "learnloop.attempts.attempts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/attempts.py"
source_paths:
  - "src/learnloop/attempts/attempts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps attempts behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `GradeAttribution`, `ResolvedGrade`, `AttemptResult`, `ApplyAttemptInput`, `AttemptPriorState` and 18 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py) |
| Source lines | 3313 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AttemptDraft` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 129)
- `class SelfGradeErrorAttribution` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 175) — One learner-attributed error from the self-grade form (spec §"self-grade").
- `class SelfGradeInput` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 190)
- `class GradeAttribution` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 200)
- `class ResolvedGrade` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 234)
- `class AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 262)
  - `as_dict(self) -> dict[str, object]` (line 302; public)
- `class ApplyAttemptInput` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 331) — Resolved attempt payload consumed by the shared attempt step.
- `class AttemptPriorState` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 352) — Prior learner/item state read once before computing one attempt.
  - `facet_recall_state(self, facet_id: str, practice_item_id: str | None=None) -> FacetRecallState | None` (line 366; public)
  - `facet_recall_by_scope(self, facets: Iterable[str], practice_item_id: str) -> dict[tuple[str, str | None], FacetRecallState | None]` (line 371; public)
- `class AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 380) — Computed attempt outputs before they are persisted.
- `class AttemptServiceNotReady(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 403)
- `class AttemptValidationError(ValueError)` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 407)
- `complete_attempt_with_codex_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime: CodexRuntimeReport, codex_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 421)
- `complete_attempt_with_ai_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 445)
- `complete_attempt_with_codex_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime: CodexRuntimeReport, codex_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 557)
- `complete_attempt_with_ai_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 578)
- `complete_self_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, grade: SelfGradeInput, *, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 720)
- `complete_codex_graded_attempt(vault: LoadedVault, repository: Repository, draft: AttemptDraft, proposal: GradingProposal, *, attempt_id: str | None=None, agent_run_id: str | None=None, grading_source: str='codex', diagnostic_sample_support: float | None=None, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 802)
- `replay_existing_attempt(vault: LoadedVault, repository: Repository, attempt: dict, *, clock: Clock | None=None, error_event_ids: list[str] | None=None, error_events: list[dict[str, Any]] | None=None, error_attributions: list[GradeAttribution] | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 868) — Recompute derived state for a persisted attempt without re-grading it.
- `reveal_total_for_submission(repository: Repository, practice_item_id: str, *, until: str | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1103) — Summed answer exposure on this item since the learner last attempted it.
- `auto_primed_draft(repository: Repository, draft: AttemptDraft, *, clock: Clock | None=None) -> tuple[AttemptDraft, float]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1117) — Force ``primed`` on a draft whose answer has already been handed over.
- `apply_attempt(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1350) — Apply one resolved attempt through the shared learner-state pipeline.
- `compute_attempt_application(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, *, clock: Clock | None=None, prior_state: AttemptPriorState | None=None) -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1623) — Compute the rows and result for one resolved attempt without persisting.
- `load_attempt_prior_state(vault: LoadedVault, repository: Repository, *, learning_object_id: str, practice_item_id: str, facets: Iterable[str], now_iso: str) -> AttemptPriorState` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2148) — Read the prior-state snapshot used by one attempt computation.
- `resolved_codex_grade(validated: ValidatedCodexGrade, *, agent_run_id: str | None, clock: Clock | None, manual_review_reason: str | None=None) -> ResolvedGrade` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3081)
- `calculate_rubric_score(rubric: Rubric, criterion_points: dict[str, float], fatal_errors: list[str]) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3209)
- `fsrs_rating_for_attempt(item: PracticeItem, rubric_score: int, max_points: int, hints_used: int) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3231) — FSRS rating for a graded attempt: score binning + the item's hint cap.

### Module constants

- `DONT_KNOW_ERROR_TYPE` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 108)
- `SCAFFOLD_FAILURE_ERROR_TYPE` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 109)
- `AUTO_PRIME_REVEAL_THRESHOLD` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 125)
- `COLD_FOLLOWUP_TASK_KINDS` ([src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py), line 416)

## Internal implementation anchors

- `_complete_attempt_with_agent_fallback(vault: LoadedVault, repository: Repository, draft: AttemptDraft, fallback_grade: SelfGradeInput, *, runtime, ai_client: AIProviderClient | None=None, grading_source: str, missing_client_reason: str, failure_prefix: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 469)
- `_try_deterministic_grade(vault: LoadedVault, repository: Repository, draft: AttemptDraft, item, rubric, *, clock: Clock | None=None) -> AttemptResult | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 599) — Grade an unambiguous option-letter selection without the model grader.
- `_complete_attempt_with_agent_required(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, runtime, ai_client: AIProviderClient | None=None, grading_source: str, missing_client_reason: str, clock: Clock | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 638)
- `_agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 951)
- `_diagnostic_augmentation_setting(vault: LoadedVault, key: str, default: int | bool) -> int | bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 967) — Read the optional forward-compatible config block.
- `_augmented_grading_context(vault: LoadedVault, repository: Repository, item: PracticeItem, context: Any) -> Any` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 993)
- `_run_augmented_diagnosis(vault: LoadedVault, client: AIProviderClient, context: Any) -> Any` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1021)
- `_record_diagnostic_augmentation(repository: Repository, *, attempt_id: str, context: Any, consensus: Any, client: AIProviderClient, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1049) — Telemetry must not be able to turn a committed grade into a failure.
- `_with_source(result: AttemptResult, *, grading_source: str, agent_run_id: str | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1080)
- `_with_fallback(result: AttemptResult, reason: str, *, agent_run_id: str | None=None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1084)
- `_assessment_contract(repository: Repository, draft: AttemptDraft) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1088)
- `_resolve_attempt_target(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, replay: bool=False, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1151)
- `_dual_write_grade_channel(vault: LoadedVault, repository: Repository, attempt: ApplyAttemptInput, application: 'AttemptApplication', *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1242) — P0.2 dual-write (spec_p0_measurement_correctness §4.1, §7.2): append a raw grade event + calibrated interpretation alongside the legacy attempt summary.
- `_persist_repair_mapping_source(repository: Repository, result: AttemptResult, stored: Mapping[str, Any], *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1308) — Make the authored repair suggestions durable on EVERY attempt path.
- `_project_canonical_belief(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1575) — Recompute the canonical shared belief cache after an attempt (mvp-0.7).
- `_validate_probe_presentation(repository: Repository, application: AttemptApplication, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1592) — Pre-persist §5.4 validation: an invalid, mismatched, ended, or already consumed presentation reference is stripped so the attempt records as incidental evidence (and the unique presentation index never rejects the row).
- `_stamp_observation_lineage(vault: LoadedVault, repository: Repository, application: AttemptApplication, attempt: ApplyAttemptInput, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1651) — Snapshot the assessment contract and stamp observation ids (KM §5.2).
- `_criterion_correlation_group(item: PracticeItem, criterion_id: str) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1829)
- `_persist_attempt_application(repository: Repository, application: AttemptApplication, *, replace_existing: bool, write_legacy_facet_state: bool=True) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1839)
- `_discrimination_profile_telemetry(match) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1885) — A5's per-attempt tally, from the ONE implementation of the arm vocabulary.
- `_record_discrimination_profile_match(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1898) — Persist the attempt's A5 judgement (Meas §3.A5, migration 143).
- `_record_error_hunt_outcome(repository: Repository, application: AttemptApplication, *, vault: LoadedVault | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 1953) — Persist the attempt's A3 outcome and mint the §10 misconception candidate.
- `_record_exercised_facets(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2024) — Append the attempt's A6 trace observations (Meas §3.A6, migration 141).
- `_record_grading_clarification(repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2065) — Persist the grader's clarification request, if it made a licensed one.
- `_auto_resolve_clean_error_events(vault: LoadedVault, repository: Repository, application: AttemptApplication, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2103) — Close the loop on stale error events (config ``[misconceptions]``).
- `_compute_resolved_grade_application(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, attempt_id: str, grade: ResolvedGrade, clock: Clock | None=None, error_event_ids_override: list[str] | None=None, prior_state: AttemptPriorState | None=None, replay: bool=False, grading_source: str='self') -> AttemptApplication` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2206)
- `_self_grade_attributions(vault: LoadedVault, fatal_errors: list[str], error_type: str | None, error_attributions: list[SelfGradeErrorAttribution] | None=None) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2823) — Resolve the learner's self-grade selections into the same flat ``GradeAttribution`` list Codex grading produces.
- `_canonicalized_grade_attributions(vault: LoadedVault, attributions: list[GradeAttribution]) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2876)
- `_primary_error_type(attributions: list[GradeAttribution]) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2924)
- `_attempt_manual_review_reason(existing: str | None, draft: AttemptDraft) -> str | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2930)
- `_dont_know_error_type(vault: LoadedVault, hints_used: int) -> str` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2938)
- `_error_event_repair_plan(vault: LoadedVault, attribution: GradeAttribution) -> dict[str, object] | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2948)
- `_replay_error_attributions(vault: LoadedVault, error_type: str | None, *, error_events: list[dict[str, Any]] | None=None) -> list[GradeAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 2992)
- `_validated_criterion_points(rubric: Rubric, points: dict[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3162)
- `_validated_self_grade_attributions(rubric: Rubric, attributions: list[SelfGradeErrorAttribution] | None) -> list[SelfGradeErrorAttribution]` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3178) — Validate per-criterion self-grade error picks before they are resolved.
- `_validate_fatal_errors(rubric: Rubric, fatal_errors: list[str]) -> None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3202)
- `_evidence_coverage(item: PracticeItem, criterion_points: dict[str, float]) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3222)
- `_hint_dampening(item: PracticeItem, hints_used: int) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3226)
- `_capped_rating(rating: Rating, item: PracticeItem, hints_used: int) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3241)
- `_hint_policy_value(mapping: dict[int | str, object], hints_used: int) -> object | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3249)
- `_rating_from_cap(value: object) -> Rating` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3267)
- `_memory_state(state: PracticeItemState | None) -> MemoryState | None` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3286)
- `_elapsed_days(state: PracticeItemState | None, observed_at) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3297)
- `_error_severity(vault: LoadedVault, error_type: str) -> float` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3306)
- `_is_misconception(vault: LoadedVault, error_type: str) -> bool` ([source](../../../../../../src/learnloop/attempts/attempts.py), line 3311)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `GradeAttribution`; statically calls `GradeAttribution`
- [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]] — imports `resolved_codex_grade`; statically calls `resolved_codex_grade`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `AttemptDraft`, `AttemptValidationError`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `fsrs_rating_for_attempt`; statically calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`, `calculate_rubric_score`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `AttemptResult`, `GradeAttribution`, `replay_existing_attempt`; statically calls `replay_existing_attempt`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`; statically calls `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `ApplyAttemptInput`, `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`; statically calls `ApplyAttemptInput`, `AttemptDraft`, `AttemptValidationError`, `GradeAttribution`, `ResolvedGrade`, `apply_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `resolved_codex_grade`; statically calls `resolved_codex_grade`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `AttemptDraft`, `AttemptValidationError`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`; statically calls `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `AttemptValidationError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`; calls `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`, `legacy_codex_status`; calls `legacy_codex_status`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `NON_RECORDING_ATTEMPT_TYPES`, `SUPPORTED_ATTEMPT_TYPES`, `unsupported_attempt_types`; calls `unsupported_attempt_types`
- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `estimate_ability_transition`; calls `estimate_ability_transition`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`, `GradingProposal`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `record_clarification`; calls `record_clarification`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`, `response_soft_score`; calls `record_grade_dual_write`, `response_soft_score`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `ValidatedCriterionEvidence`, `ValidatedErrorAttribution`, `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `evidence_coverage`, `grading_context_hash`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `build_grading_context`, `confidence_to_grader_confidence`, `deterministic_recognition_grade`, `enforce_passed_target_firewall`, `evidence_coverage`, `grading_context_hash`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `reject_salience`; calls `reject_salience`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `compute_surprise`; calls `compute_surprise`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `maybe_promote_self_tagged_fatal_error`; calls `maybe_promote_self_tagged_fatal_error`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `FacetRecallState`, `FacetUncertaintyState`, `ItemParameterState`, `MasteryState`, `PracticeItemQualityState`, `PracticeItemState`, `Repository`; calls `PracticeItemState`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `classify_attempt_activity`; calls `classify_attempt_activity`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `materialize_causal_episode`; calls `materialize_causal_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `DEFAULT_DIAGNOSIS_SAMPLES`, `DEFAULT_HISTORY_LIMIT`, `augment_grading_context`, `record_phase_c_receipt`, `run_diagnosis_samples`; calls `augment_grading_context`, `record_phase_c_receipt`, `run_diagnosis_samples`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `profile_match_telemetry`; calls `profile_match_telemetry`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`; calls `FalsePositiveReport`, `PlantOutcome`, `PlantResult`, `ValidatedErrorHunt`, `record_error_hunt_outcome`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `persist_unknown_error_type_proposals`; calls `persist_unknown_error_type_proposals`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`; calls `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `record_remediation_attempt`; calls `record_remediation_attempt`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `record_certification_cold_probe_attempt`; calls `record_certification_cold_probe_attempt`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `rubric_from_contract`, `snapshot_for_presentation`; calls `rubric_from_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`; calls `apply_mastery_variance_floor`, `build_facet_uncertainty_updates`, `covered_required_fraction`, `lo_relative_coverage`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetStateReader`, `is_canonical_state_vault`; calls `CanonicalFacetStateReader`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `MasteryObservationTrace`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`; calls `MasteryObservation`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `build_facet_recall_updates`, `build_facet_recall_updates_from_prior`, `build_quality_state_update`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity`, `event_local_severity_from_attempts`, `familiarity_discount`, `familiarity_discount_from_attempts`, `predicted_correctness`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`; calls `build_facet_recall_updates_from_prior`, `build_quality_state_update_from_prior`, `derive_facet_outcomes`, `event_local_severity_from_attempts`, `familiarity_discount_from_attempts`, `predicted_correctness_from_prior`, `resolve_coverage`, `resolve_error_impact`, `resolve_reliability`, `scale_coverage_for_graded_criteria`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`; calls `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `evidence_eligibility_for`; calls `evidence_eligibility_for`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `hot_path_applies_practice_review`; calls `hot_path_applies_practice_review`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/observations|learnloop.attempts.observations]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/exam|learnloop.cli.exam]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] and 15 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — direct import
  - `test_answer_confidence_must_be_a_1_to_5_committed_tap`
  - `test_post_reveal_confidence_tap_cannot_land_on_a_graded_attempt`
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_legacy_attempt_records_no_observation_lineage`
  - `test_mvp07_attempt_stamps_observation_lineage`
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — direct import
  - `test_attempt_ai_flow_records_provider_model_and_ai_source`
- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — direct import
  - `test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post`
- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — direct import
  - `test_attempt_links_to_scheduler_slate_and_later_retention_label`
  - `test_hinted_attempt_caps_fsrs_rating`
  - `test_self_graded_attempt_updates_attempt_evidence_state_and_surprise`
  - `test_unknown_attempt_type_fails_before_sqlite_insert`
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — direct import
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
- [tests/test_causal_cold_outcomes.py](../../../../../../tests/test_causal_cold_outcomes.py) — direct import
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
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_learner_derived_hypothesis_defaults_learner_state_and_offer_survives`
  - `test_receipted_divergence_skips_the_consultation_entirely`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_apply_writes_one_boundary_and_a_rerun_writes_none`
- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
  - `test_deactivate_locked_learning_object_is_invalid`
  - `test_locked_semantic_merge_is_invalid`
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
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_c3_k1_leaves_no_sample_support_on_the_stored_attribution`
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_gate_section_counts_manual_false_negatives`
  - `test_report_on_real_session_flow`
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_only_never_attempted_items_are_reservable`
  - `test_uncovered_facets_reported_when_no_item_tests_a_facet`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_seeded_exam_interleaves_before_later_live_attempt`
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_hedged_learner_confidence_opens_uncertainty_even_with_partial_credit`
  - `test_open_facet_restriction_makes_disjoint_correct_attempt_zero_weight`
  - `test_variance_floor_blocks_confidence_before_required_facet_breadth`
- [tests/test_facet_evidence_timeline.py](../../../../../../tests/test_facet_evidence_timeline.py) — direct import
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_real_receipt_from_apply_attempt_does_not_force_tier_two`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_followups.py](../../../../../../tests/test_followups.py) — direct import
  - `test_negative_surprise_followup_stops_forcing_after_followup_attempt`
- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_known_gap_and_uncertain_facets_are_both_on_frontier`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_known_gap_facet_is_never_on_track`
- [tests/test_goal_series.py](../../../../../../tests/test_goal_series.py) — direct import
  - `test_series_reflects_evidence_arriving_over_time`
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
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
- [tests/test_hot_path_eligibility_cutover.py](../../../../../../tests/test_hot_path_eligibility_cutover.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_irt_end_to_end.py](../../../../../../tests/test_irt_end_to_end.py) — direct import
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
  - `test_upgrade_projects_existing_attempts_into_canonical_facet_state`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_explicit_failure_attribution_penalizes_only_selected_target`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
  - `test_the_persisted_repair_class_is_the_structurally_selected_one`
- [tests/test_misconception_resolution.py](../../../../../../tests/test_misconception_resolution.py) — direct import
  - `test_low_correctness_attempt_does_not_count_as_clean`
- [tests/test_misconception_routing.py](../../../../../../tests/test_misconception_routing.py) — direct import
- [tests/test_missing_vocabulary_notes.py](../../../../../../tests/test_missing_vocabulary_notes.py) — direct import
  - `test_a_resolved_diagnosis_writes_no_note`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_canonical_projection_bulk_loads_historical_contracts_once`
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_primed_provenance_reaches_projection_and_blocks_certification`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_cutover_delta_is_nonempty_and_inspectable_when_projections_differ`
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
  - `test_upgrade_does_not_rewrite_raw_history`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_post_attempt_pipeline.py](../../../../../../tests/test_post_attempt_pipeline.py) — direct import
- [tests/test_predictive_eig.py](../../../../../../tests/test_predictive_eig.py) — direct import
  - `test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero`
- [tests/test_probe_attempt_updates.py](../../../../../../tests/test_probe_attempt_updates.py) — direct import
  - `test_attempt_service_never_writes_legacy_probe_state`
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
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
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
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
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_a_revealed_cold_item_cannot_burn_its_cold_measurement`
  - `test_an_auto_primed_attempt_replays_as_primed`
  - `test_reveal_over_threshold_forces_primed_and_records_why`
  - `test_reveal_under_threshold_leaves_the_attempt_unprimed`
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_apply_attempt_chokepoint_rejects_salience`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_uses_prospective_familiarity_discount`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_censored_learning_objects_are_reported_and_excluded_from_the_mean`
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
  - `test_no_promotion_when_label_already_rubric_fatal`
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_dont_know_allowed_when_not_in_attempt_types`
  - `test_self_grade_attribution_rejects_unknown_criterion`
  - `test_self_grade_per_criterion_attribution_writes_error_event`
  - `test_self_grade_uses_criterion_total_as_item_scale`
  - `test_self_grade_uses_default_rubric_when_inline_rubric_is_omitted`
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
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — direct import
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import

## Modification guidance

- Change attempts policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/attempts.py](../../../../../../src/learnloop/attempts/attempts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
