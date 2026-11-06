---
title: "learnloop.diagnosis.text_gaps.pipeline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/pipeline.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/pipeline.py"
source_commit: "2d11fc7113d296b712971538e8684e070ca2664d"
source_commit_timestamp: "2026-11-01T21:42:01-05:00"
source_worktree_state: "clean"
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
  - "learnloop.diagnosis.text_gaps.pipeline module"
  - "src/learnloop/diagnosis/text_gaps/pipeline.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.pipeline`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.pipeline` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: Read one learner text into a named gap and act on it (implementation_handoffs §4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py) |
| Source lines | 1203 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d11fc7113d296b712971538e8684e070ca2664d` |
| Commit timestamp | `2026-11-01T21:42:01-05:00` |

## Public API

- `class ReadingDeferred(Exception)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 132) — The reading cannot be finished now: no ledger row is written.
  - `__init__(self, reason: str, *, spend: bool=False) -> None` (line 142; internal)
- `class NoteReadingStopped(BaseException)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 148) — A note's reading may go no further (curriculum C5, Codex review F3): the learner switched the opt-in, the notes or gap reading off, its link was hidden or superseded, what it is linked to (or a passage its prepared request was built from) became protected material, the note was…
- `class NoteGate` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 162) — The request gate of one note's reading (curriculum C5, Codex review F3).
  - `__init__(self, root: Path, repository: Repository, text: LearnerText) -> None` (line 181; internal)
  - `_refusal(self) -> str | None` (line 199; internal)
  - `check(self, purpose: str='request') -> None` (line 211; public) — Raise :class:`NoteReadingStopped` when the reading may send or write nothing more.
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 220; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 231; public)
- `class PipelineClients` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 237) — Client factories, resolved only when a step needs one (None: unavailable).
  - `get(self, name: str) -> Any | None` (line 249; public)
- `default_clients(vault: LoadedVault) -> PipelineClients` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 269)
- `authoritative(chooser: str, reading: GapReading | None, decider: DeciderKind) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 287) — The kind the chooser switch makes authoritative (``unread`` without one).
- `process_learner_text(root: Path, repository: Repository, text: LearnerText, *, clients: PipelineClients | None=None, budget: TextBudget | None=None, clock: Clock | None=None, progress: Mapping[str, Any] | None=None, save_progress: Callable[[Mapping[str, Any]], None] | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 889) — Read, match, act and log one learner text; returns its ledger row.
- `stored_words(text: LearnerText) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 1114) — The words a ``learner_text_gaps`` row keeps: the learner's text, bounded (a linked note's too, C2b: note text is learner text).
- `failed_row(text: LearnerText, *, vault: LoadedVault, error: str, now_iso: str, progress: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 1121) — The ledger row for a learner text whose job gave up (no target).
- `named_gaps_for_card(connection: Any, *, learning_object_ids: Sequence[str] | None=None, before: str | None=None, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 1162) — Each named gap as a typed event (router spec §4), oldest first.

### Module constants

- `LOG` ([src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 117)
- `SEED_INPUT_TOKENS` ([src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 123)
- `TUTOR_ROUTE` ([src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 125)
- `SETTLED` ([src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 127)
- `_STOPS` ([src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 129)

### Explicit exports

`__all__` declares:

- `NoteGate`
- `NoteReadingStopped`
- `PipelineClients`
- `ReadingDeferred`
- `stored_words`
- `authoritative`
- `default_clients`
- `failed_row`
- `named_gaps_for_card`
- `process_learner_text`

## Internal implementation anchors

- `_ready(vault: LoadedVault, task: str, *, timeout: int | None=None) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 262)
- `_verdicts(results: Sequence[JudgedPair]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 297) — Settled verdicts only: a ``fenced`` pair's verdict was never appended.
- `_unsettled(results: Sequence[JudgedPair]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 306)
- `_stopped(results: Sequence[JudgedPair]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 313)
- `_judge_all(repository: Repository, kind: Any, pairs: list, *, budget: TextBudget, clients: PipelineClients, decider_on: bool, vault: LoadedVault | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 317) — Both judges on the same pairs; each verdict lands in ``judgment_ledger``.
- `_tier1(vault: LoadedVault, switch: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 354) — Tier 1 for a learner-text gap judgment: its ``[decider_routes]`` switch at mvp-0.22.
- `_pair_authority(vault: LoadedVault, chooser: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 365) — The authoritative pair judge before Tier 1: the chooser's (``llm`` for ``context_model``).
- `_require_settled(judged: Mapping[str, Any], authority: str) -> None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 378) — Every candidate pair has a verdict from the authoritative judge (F1).
- `_with_standing(repository: Repository, kind: Any, results: Sequence[JudgedPair], *, judge: str, producer: str) -> list[JudgedPair]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 387) — ``already_judged`` pairs take the producer's standing verdict from the ledger.
- `_embed_query(repository: Repository, budget: TextBudget, clients: PipelineClients, vault: LoadedVault, subject: Any, field_name: str, detail: dict[str, Any]) -> tuple[Any, str | None]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 411)
- `_prerequisite(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading, *, chooser: str, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None, progress: Mapping[str, Any], checkpoint: Checkpoint) -> actions.ActionOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 438)
- `_maybe_edge(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *, chooser: str, budget: TextBudget, clients: PipelineClients, clock: Clock | None, checkpoint: Checkpoint) -> None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 515)
- `_write_edge(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *, edge: Mapping[str, Any], clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 568) — Write the recorded edge (idempotent: an edge already on disk is ``added``).
- `_resume(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, *, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None, progress: Mapping[str, Any], checkpoint: Checkpoint) -> actions.ActionOutcome | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 589) — Finish the vault write an earlier attempt of this job recorded (F3, re-review F1); None when it recorded none.
- `_create(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading | None, *, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None, detail: dict[str, Any], progress: Mapping[str, Any], checkpoint: Checkpoint) -> actions.ActionOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 625)
- `_seed_route(budget: TextBudget) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 720) — The route the seed's promotion unit is admitted on (Codex review F12).
- `_seed(root: Path, text: LearnerText, learning_object_id: str, *, budget: TextBudget, clients: PipelineClients, clock: Clock | None) -> tuple[str | None, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 740)
- `_belief(vault: LoadedVault, repository: Repository, text: LearnerText, reading: GapReading, *, budget: TextBudget, clients: PipelineClients, clock: Clock | None) -> actions.ActionOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 770)
- `_decide(repository: Repository, text: LearnerText, vault: LoadedVault, *, budget: TextBudget, clients: PipelineClients, progress: Mapping[str, Any], checkpoint: Checkpoint) -> tuple[GapReading | None, DeciderKind, str, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 825) — The reading, the Decider's kind, the chooser and the authoritative kind.
- `_read_and_act(root: Path, vault: LoadedVault, repository: Repository, text: LearnerText, *, budget: TextBudget, clients: PipelineClients, now_iso: str, clock: Clock | None, state: dict[str, Any], checkpoint: Checkpoint) -> tuple[actions.ActionOutcome, GapReading | None, DeciderKind, str, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 951) — The reading and its action (inside the text's receipts).
- `_log(root: Path, repository: Repository, text: LearnerText, outcome: actions.ActionOutcome, *, reading: GapReading | None, decider: DeciderKind, chooser: str, kind: str, budget: TextBudget, now_iso: str, clock: Clock | None, before_write: Callable[[], None] | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 981) — Log the reading as one ``learner_text_gaps`` row (and its sooner check or commitment).
- `_record_written_texts(connection: Any, vault: LoadedVault, text: LearnerText, outcome: actions.ActionOutcome, *, gap_id: str, learner_words: str, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py), line 1049) — Diagnosis input provenance, in the ledger row's transaction: a question's words (the gap's), a created prerequisite's drafted title and a seeded item's question each record what they were written from (``text_gaps.provenance``).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `NoteReadingStopped`, `PipelineClients`, `ReadingDeferred`, `failed_row`, `process_learner_text`; statically calls `failed_row`, `process_learner_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `PipelineClients`, `ReadingDeferred`, `_stopped`, `_unsettled`, `_verdicts`, `_with_standing`, `authoritative`; statically calls `ReadingDeferred`, `_stopped`, `_unsettled`, `_verdicts`, `_with_standing`, `authoritative`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `gate_model_requests`; calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gap`, `gap_for_source`, `gaps`, `insert_commitment`, `insert_gap`, `reversals`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `WriteRecord`, `record_text_write`; calls `record_text_write`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `default_embedding_client`; calls `default_embedding_client`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `module`; calls `ActionOutcome`, `add_prerequisite_edge`, `advance_check`, `commitment_row`, `creation_ids`, `creations_today`, `day_start`, `declared_prerequisite`, `edge_id_for`, `edges_on_disk`, `persist_check_advance`, `record_belief`, `seed_from_question`, `subject_for_creation`, `write_created_prerequisite`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `belief_candidates`, `prerequisite_candidates`; calls `belief_candidates`, `prerequisite_candidates`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `DRAFT_ROUTE`, `GapReading`, `LearnerText`, `NON_SERVING_SOURCE_KINDS`, `NOTE_SOURCE_KINDS`, `NOTE_UNCHECKPOINTED_FIELDS`, `PIPELINE_VERSION`, `PrerequisiteDraft`, `UNREAD`; calls `GapReading`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `DeciderKind`, `DeciderPairExecutor`, `LLMPairExecutor`, `TextBudget`, `ask_needed`, `decider_kind`, `draft_prerequisite`, `log_reading`, `needed_context`, `query_vector`, `read_text`; calls `DeciderKind`, `ask_needed`, `decider_kind`, `draft_prerequisite`, `log_reading`, `needed_context`, `query_vector`, `read_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `BELIEF_FIELD`, `PREREQUISITE_FIELD`, `SAME_BELIEF`, `SAME_PREREQUISITE`, `belief_query`, `prerequisite_query`; calls `belief_query`, `prerequisite_query`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `TUTOR_UNRECORDED`, `drafter_record`, `formative_record`, `hint_feedback_record`, `note_record`, `question_record`; calls `drafter_record`, `formative_record`, `hint_feedback_record`, `note_record`, `question_record`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `learner_note_refusal`; calls `learner_note_refusal`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `module`; calls `ask_needed`, `decide_kind`, `judge_all`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `JudgedPair`, `judge_pairs`, `pair_input_hash`; calls `JudgedPair`, `judge_pairs`, `pair_input_hash`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `copy`, `dataclasses`, `logging`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text`
- [tests/test_figures_scope_redesign.py](../../../../../../../tests/test_figures_scope_redesign.py) — direct import
- [tests/test_hint_feedback_texts.py](../../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_the_gap_joins_the_next_hints_rivals`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_named_gaps_reach_the_learner_state_card`
  - `test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide`
- [tests/test_learner_text_gaps_composition.py](../../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`
- [tests/test_learner_text_gaps_flow.py](../../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_diagnosis_is_read_from_its_causes_without_a_call`
  - `test_diagnosis_kinds`
  - `test_stuck_text_is_read_through_the_source_interface`
  - `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f1_a_recorded_edge_is_finished_after_the_judges_the_chooser_and_the_switch_change`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f12_the_seed_unit_is_admitted_on_a_metered_tutor_route`
  - `test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version`
  - `test_f1_a_failed_pair_on_the_true_match_never_creates_and_the_retry_matches`
  - `test_f1_a_fenced_pair_is_not_a_verdict`
  - `test_f2_a_refused_draft_is_deferred_not_logged_unmatched`
  - `test_f3_a_job_that_gives_up_after_writing_names_the_creation_and_the_owner_can_undo_it`
  - `test_f3_a_matched_edge_retried_after_a_failed_sync_is_recorded_and_undoable`
  - `test_f4_without_a_grounded_subject_only_the_anchors_are_judged_and_nothing_is_created`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_note_is_read_on_the_ordinary_routes_with_the_decider`
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
- [tests/test_reader_formative_texts.py](../../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_reading_it_writes_only_gap_rows_and_names_the_observations_hypothesis`
- [tests/test_reader_rw1b_review.py](../../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_the_seed_unit_is_admitted_at_the_policy_budget`
- [tests/test_teacher_te2_lessons.py](../../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_a_gap_from_the_learners_words_goes_to_the_text_gap_pipeline_with_source_lesson`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_predecessor_second_opinion_is_never_reused_as_the_tier1_verdict`
  - `test_a_tied_gap_pair_goes_to_the_llm`
  - `test_gap_pairs`
  - `test_gap_pairs_reuse_the_deciders_verdict_and_defer_on_a_stopped_fallback`
  - `test_needed_is_the_deciders_and_its_refusal_falls_back`
  - `test_text_gap_kind_is_reused_never_paid_for_twice`
- [tests/test_workbench_text_gaps.py](../../../../../../../tests/test_workbench_text_gaps.py) — direct import
  - `test_reading_it_writes_only_gap_rows`

## Modification guidance

- Change pipeline policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/pipeline.py](../../../../../../../src/learnloop/diagnosis/text_gaps/pipeline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
