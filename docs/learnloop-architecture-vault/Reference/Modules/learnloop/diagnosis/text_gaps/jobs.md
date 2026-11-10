---
title: "learnloop.diagnosis.text_gaps.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/jobs.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.jobs module"
  - "src/learnloop/diagnosis/text_gaps/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.jobs` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: The learner-text gap queue: one job per learner text, run off the request path.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py) |
| Source lines | 823 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GapJobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 80)
  - `as_dict(self) -> dict[str, Any]` (line 92; public)
- `pipeline_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 97)
- `enqueue(repository: Repository, *, source_kind: str, source_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 101)
- `enqueue_lesson_gap(vault: LoadedVault, repository: Repository, source_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 107) — Teacher TE2 (spec_teacher_v1 §11.7): a teacher's ``propose_gap`` (its ``lesson_turns`` entry) queued with ``source_kind = 'lesson'`` (switch on only); idempotent per entry.
- `enqueue_tutor_question(vault: LoadedVault, repository: Repository, event_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 117) — After the tutor answered: queue the question (switch on only).
- `enqueue_after_diagnosis(vault: LoadedVault, repository: Repository, *, attempt_id: str, diagnosis: Mapping[str, Any], clock: Clock | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 126) — After a live diagnosis is applied: queue it.
- `enqueue_stuck_answer(vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None, stuck_source: StuckTextSource | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 150) — When an attempt is recorded: queue it if it is a non-empty stuck answer.
- `enqueue_reader_formative(vault: LoadedVault, repository: Repository, *, question_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 169) — RW1b: a missed next-step, why-step or assumption answer (``reader_formative``).
- `enqueue_figure_prediction(vault: LoadedVault, repository: Repository, *, prediction_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 188) — Reader RW5a: a missed figure prediction (its answer and "what changed?" text) as a ``reader_formative`` text, on RW1b's rule: only with ``learner_text_gaps.enabled`` and ``reader_formative.enabled`` on, only a missed one with an answer; a matched prediction queues nothing.
- `enqueue_figure_explanation(vault: LoadedVault, repository: Repository, *, prediction_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 202) — RW5a: a missed figure prediction's "what changed?", once written.
- `enqueue_hint_feedback(vault: LoadedVault, repository: Repository, *, assist_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 233) — Adaptive hints H2b: text written back to a hint on the practice screen (``hint_feedback``): a "doesn't connect" reply's text or an answer to a discriminating question, queued when its ``help_assists`` row is written, so a gap named mid-attempt can join the next hint's rivals (sp…
- `enqueue_workbench_text(vault: LoadedVault, repository: Repository, *, source_id: str, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 253) — Reader workbench RW2b (spec §5.2 "in-session updates", §5.6): text the learner wrote while working in steps (``workbench_text``), queued when it is written or sent: a reply or a discriminating answer when its row is written, a stuck step's newest version when Help, Check, Leave…
- `workbench_text_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 271)
- `hint_feedback_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 277) — Whether ``hint_feedback`` texts are queued: the pipeline and adaptive hints both on.
- `reconcile_hint_feedback(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 283) — Queue every ``hint_feedback`` text whose job was never written (H2b review F4): the reply or discriminating answer committed, and the process ended, or the enqueue failed, before its job did.
- `enqueue_learner_notes(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 302) — Curriculum C5: queue every linked note's current snapshot that has no reading yet (and queue again one whose job was skipped while it was not linked or switched off, now that it is linked again).
- `retract_unlinked_notes(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 320) — Follow-ups Nov 2 (C5 ruling R2): every gap read from a linked note's snapshot (``source_kind = 'learner_note'``) whose snapshot is not linked now (C2's one rule, :func:`learner_note_ids`, C2b's link model over the vault's own notes: the learner hid the link, the proposal was sup…
- `sweep_backlog(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, stuck_source: StuckTextSource | None=None, include_history: bool=False, dry_run: bool=False, kinds: tuple[str, ...]=BACKLOG_KINDS + NOTE_BACKLOG_KINDS) -> dict[str, int]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 358) — Queue unread learner texts (``learnloop gaps run --backlog``).
- `calls_today(repository: Repository, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 493) — The pipeline's logical model calls since today's UTC midnight (receipts).
- `process_next_gap_job(root: Path, repository: Repository, *, owner: str, clients: PipelineClients | None=None, budget_factory: Callable[[LoadedVault], TextBudget] | None=None, clock: Clock | None=None, source: tuple[str, str] | None=None, stuck_source: StuckTextSource | None=None, cancelled: Callable[[], bool] | None=None) -> GapJobOutcome | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 501) — Lease and run the next runnable gap job (or ``source``'s); None when none is.
- `run_pending(root: Path, repository: Repository, *, owner: str, max_jobs: int=50, **kwargs: Any) -> list[GapJobOutcome]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 748)
- `pending_jobs(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 764)
- `plan(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 769) — A no-call plan of the queue: what would be read and the call ceiling.

### Module constants

- `LOG` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 71)
- `LEASE_SECONDS` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 74)
- `MAX_ATTEMPTS` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 75)
- `BACKOFF_SECONDS` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 76)
- `BACKLOG_KINDS` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 294)
- `NOTE_BACKLOG_KINDS` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 299)
- `UNLINKED` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 317)
- `_CONTEXT_JUDGE` ([src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 699)

### Explicit exports

`__all__` declares:

- `GapJobOutcome`
- `LEASE_SECONDS`
- `MAX_ATTEMPTS`
- `UNLINKED`
- `calls_today`
- `enqueue`
- `enqueue_figure_explanation`
- `enqueue_figure_prediction`
- `enqueue_after_diagnosis`
- `enqueue_learner_notes`
- `enqueue_stuck_answer`
- `enqueue_tutor_question`
- `enqueue_workbench_text`
- `pending_jobs`
- `pipeline_enabled`
- `plan`
- `process_next_gap_job`
- `run_pending`
- `reconcile_hint_feedback`
- `retract_unlinked_notes`
- `sweep_backlog`
- `workbench_text_enabled`

## Internal implementation anchors

- `_requeue(repository: Repository, job_id: str, *, clock: Clock | None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 440)
- `_reading_checkpointed(job: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 445) — Whether a job already holds a reading (its markers are checkpointed with it, fix round 4): a retry reuses that reading, so a later explanation is its own text.
- `_unread_figure_explanations(repository: Repository, job_rows: Mapping[tuple[str, str], Mapping[str, Any]], gap_rows: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 453) — The ``<prediction id>:explained`` sources the backlog owes (fix round 2, F5): a "what changed?" saved after its prediction's reading started or finished, while nothing queued it (gap reading was off then).
- `_later(seconds: float, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 484)
- `_next_day(clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 488)
- `_retry_or_fail(repository: Repository, job: Mapping[str, Any], text: Any, vault: LoadedVault, progress: Mapping[str, Any], *, owner: str, epoch: int, clock: Clock | None, outcome: GapJobOutcome, error: str) -> GapJobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 667) — Back off and retry; after the last attempt log the text as ``failed``, naming whatever its earlier attempts already wrote (F3).
- `_skip(repository: Repository, job: Mapping[str, Any], text: LearnerText | None, vault: LoadedVault, progress: Mapping[str, Any], *, owner: str, epoch: int, clock: Clock | None, outcome: GapJobOutcome, reason: str) -> GapJobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py), line 704) — The job reads nothing more: the pipeline is switched off, or the text is gone.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `plan`, `run_pending`, `sweep_backlog`; statically calls `plan`, `run_pending`, `sweep_backlog`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `enqueue_stuck_answer`; statically calls `enqueue_stuck_answer`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `enqueue_after_diagnosis`; statically calls `enqueue_after_diagnosis`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `enqueue_figure_explanation`, `enqueue_figure_prediction`; statically calls `enqueue_figure_explanation`, `enqueue_figure_prediction`
- [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] — imports `enqueue_reader_formative`; statically calls `enqueue_reader_formative`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `pending_jobs`, `pipeline_enabled`; statically calls `pending_jobs`, `pipeline_enabled`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `enqueue_lesson_gap`, `pipeline_enabled`; statically calls `enqueue_lesson_gap`, `pipeline_enabled`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `enqueue_workbench_text`; statically calls `enqueue_workbench_text`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `enqueue_learner_notes`, `pending_jobs`, `reconcile_hint_feedback`; statically calls `enqueue_learner_notes`, `pending_jobs`, `reconcile_hint_feedback`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `enqueue_hint_feedback`; statically calls `enqueue_hint_feedback`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `enqueue_tutor_question`; statically calls `enqueue_tutor_question`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `enqueue_learner_notes`; statically calls `enqueue_learner_notes`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `enqueue_workbench_text`; statically calls `enqueue_workbench_text`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `process_next_gap_job`; statically calls `process_next_gap_job`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `gate_model_requests`; calls `gate_model_requests`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `enqueue_job`, `finish_job`, `gap_for_source`, `gaps`, `holds_job`, `insert_gap`, `insert_reversal`, `job_for_source`, `jobs`, `lease_next_job`, `pipeline_calls_since`, `release_job`, `requeue_skipped_job`, `reversals`, `save_job_payload`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; calls `continue_job_trace`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `LearnerText`, `NOTE_SOURCE_KINDS`, `NOTE_UNCHECKPOINTED_FIELDS`; calls `LearnerText`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `TextBudget`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `NoteReadingStopped`, `PipelineClients`, `ReadingDeferred`, `failed_row`, `process_learner_text`; calls `failed_row`, `process_learner_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `FIGURE_EXPLANATION_SUFFIX`, `SourceWithheld`, `StuckTextSource`, `attempt_grade_held`, `explained_predictions`, `figures_enabled`, `formative_row`, `hint_feedback_ids`, `hint_feedback_row`, `is_figure_prediction`, `learner_note_ids`, `learner_notes_enabled`, `learner_text`, `missed_formative_ids`, `stuck_text_for`, `stuck_texts`, `workbench_text_ids`, `workbench_text_row`; calls `attempt_grade_held`, `explained_predictions`, `figures_enabled`, `formative_row`, `hint_feedback_ids`, `hint_feedback_row`, `is_figure_prediction`, `learner_note_ids`, `learner_notes_enabled`, `learner_text`, `missed_formative_ids`, `stuck_text_for`, `stuck_texts`, `workbench_text_ids`, `workbench_text_row`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `text_key`; calls `FiguresGate`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_predictions.py](../../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_the_backlog_sweep_queues_missed_predictions`
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f5_an_explanation_after_the_reading_is_read_as_its_own_text`
  - `test_f5_an_explanation_before_the_reading_is_read_with_it_once`
  - `test_f6_a_missed_prediction_and_its_explanation_wake_the_worker`
- [tests/test_figures_fix_round2.py](../../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f1_a_held_out_neighbour_keeps_a_missed_prediction_from_the_gap_reader`
  - `test_f5_a_prediction_never_read_is_swept_once_with_its_explanation`
  - `test_f5_an_explanation_the_first_reading_read_is_not_swept_again`
  - `test_f5_off_save_on_sweep_reads_the_explanation_once`
- [tests/test_figures_fix_round3.py](../../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_f5_an_explanation_repeating_the_answer_is_still_read`
  - `test_f5_the_reading_records_whether_it_read_the_explanation`
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text`
- [tests/test_figures_prefetch.py](../../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_the_gap_worker_fires_the_gap_trigger_after_a_drain`
- [tests/test_figures_scope_redesign.py](../../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_a_figure_reading_makes_no_request_after_figures_are_switched_off`
- [tests/test_figures_show_me_codex_review.py](../../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f5_the_gap_reader_is_sent_the_grounding_passage`
- [tests/test_figures_switch_off.py](../../../../../../../tests/test_figures_switch_off.py) — direct import
  - `test_an_already_queued_figure_job_with_figures_off_is_the_base_output`
  - `test_figures_off_queues_and_reads_no_figure_text`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_deferred_gap_drains_fire_passes_that_never_retry_a_plan_wait`
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
  - `test_a_note_changed_into_a_new_snapshot_sets_the_old_snapshots_gap_aside`
  - `test_a_note_linked_while_the_retraction_runs_keeps_its_gap`
  - `test_switched_off_nothing_is_read_and_nothing_is_set_aside`
  - `test_the_retraction_is_idempotent_and_keep_does_not_reopen_the_gap`
- [tests/test_held_grade_composition.py](../../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_diagnosis_of_a_held_attempt_is_never_read_as_a_wrong_answer`
- [tests/test_hint_feedback_texts.py](../../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_either_switch_off_queues_nothing`
  - `test_reading_it_writes_only_gap_rows_and_the_gap_joins_the_next_hints_rivals`
- [tests/test_hint_h2b_review.py](../../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f4_a_reply_whose_job_never_committed_is_queued_by_the_sweep_and_at_open`
  - `test_f4_nothing_is_reconciled_with_either_switch_off`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_cli_dry_runs_send_and_write_nothing`
- [tests/test_learner_text_gaps_composition.py](../../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_a_stuck_answer_keeps_its_confusion_signal_and_adds_one_gap_observation`
  - `test_a_stuck_answer_with_text_is_queued_at_recording_and_read`
  - `test_an_empty_stuck_answer_is_no_learner_text`
- [tests/test_learner_text_gaps_flow.py](../../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_job_that_keeps_failing_is_logged_as_failed_without_a_target`
  - `test_stuck_text_is_read_through_the_source_interface`
  - `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f1_a_job_stopped_after_a_write_logs_the_write_as_failed_and_undoable`
  - `test_rr_f1_a_job_switched_off_before_any_write_is_still_skipped`
  - `test_rr_f1_a_recorded_edge_is_finished_after_the_judges_the_chooser_and_the_switch_change`
  - `test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading`
  - `test_rr_f3_a_failed_pair_backs_off_one_text_and_the_run_goes_on`
  - `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`
  - `test_rr_f5_gaps_run_reads_on_a_command_budget`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f12_the_daily_cap_counts_the_pipelines_receipts`
  - `test_f12_the_live_daily_cap_defers_to_the_next_day_without_using_a_retry`
  - `test_f2_a_refused_draft_is_deferred_not_logged_unmatched`
  - `test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run`
  - `test_f3_a_belief_candidate_commits_with_its_ledger_row`
  - `test_f3_a_creation_retried_after_a_failed_sync_writes_once_and_is_logged`
  - `test_f3_a_job_that_gives_up_after_writing_names_the_creation_and_the_owner_can_undo_it`
  - `test_f3_a_matched_edge_retried_after_a_failed_sync_is_recorded_and_undoable`
  - `test_f3_a_sighting_is_counted_once_across_a_retry`
  - `test_f8_a_diagnosis_no_longer_scans_stuck_answers`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_note_is_read_on_the_ordinary_routes_with_the_decider`
  - `test_f3_rereview_a_payload_changed_after_preparation_is_not_sent`
  - `test_f3_rereview_the_gate_is_bound_to_the_prepared_passages`
  - `test_f3_revoking_consent_before_dispatch_sends_nothing`
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
  - `test_only_linked_notes_are_queued_with_their_snapshot_and_their_topics`
  - `test_step0_a_legacy_checkpointed_note_reading_is_cleared_on_requeue_and_ignored_on_retry`
  - `test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing`
  - `test_switched_off_the_pipeline_and_the_reader_are_todays`
- [tests/test_reader_formative_texts.py](../../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_a_missed_answer_is_queued_and_a_match_is_not`
  - `test_either_switch_off_queues_nothing`
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
  - `test_show_me_with_no_answer_queues_nothing`
- [tests/test_reader_rw1b_review.py](../../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f7_the_backlog_sweep_recovers_a_missed_answer_without_a_job`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_the_plan_says_when_background_work_can_still_name_a_target`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_a_stopped_worker_leases_no_gap_job`
- [tests/test_teacher_te2_lessons.py](../../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_a_gap_from_the_learners_words_goes_to_the_text_gap_pipeline_with_source_lesson`
- [tests/test_workbench_text_gaps.py](../../../../../../../tests/test_workbench_text_gaps.py) — direct import
  - `test_reading_it_writes_only_gap_rows`
  - `test_the_kind_is_readable_and_non_serving_and_the_switches_hold`

## Modification guidance

- Change jobs policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/jobs.py](../../../../../../../src/learnloop/diagnosis/text_gaps/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
