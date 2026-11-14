---
title: "learnloop.diagnosis.text_gaps.sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/sources.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/sources.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.diagnosis.text_gaps.sources module"
  - "src/learnloop/diagnosis/text_gaps/sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.sources` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: The learner-text sources, each read into one :class:`LearnerText`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py) |
| Source lines | 1223 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `tutor_question_text(vault: LoadedVault, repository: Repository, event_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 69) — An answered tutor question; None when there is nothing to read.
- `resolve_prerequisite_ref(vault: LoadedVault, ref: str, anchor: str | None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 140) — A diagnoser's validated prerequisite ref as one LO id (a facet resolves only when exactly one of the anchor's declared prerequisite LOs owns it).
- `reading_from_diagnosis(vault: LoadedVault, proposal: Mapping[str, Any], *, anchor: str | None, model: str | None, prompt_version: str | None) -> GapReading` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 167) — The diagnoser's causes as a gap reading (deterministic; no call).
- `attempt_grade_held(repository: Repository, attempt_id: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 208) — Is the attempt's current grade held for review (mvp-0.17)?
- `diagnosis_text(vault: LoadedVault, repository: Repository, diagnosis_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 219) — A completed live diagnosis of a wrong answer; None otherwise.
- `class StuckText` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 275) — One non-empty stuck answer (the stuck-prompt stage's view).
- `class StuckTextSource(Protocol)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 287) — Where stuck answers come from (the stuck-prompt stage's read-only view).
  - `stuck_texts(self, connection: Any) -> Sequence[StuckText]` (line 296; public)
- `class StuckAnswersAdapter` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 299) — The stuck prompt's own views (``learnloop.attempts.stuck``).
  - `stuck_text(self, connection: Any, attempt_id: str) -> StuckText | None` (line 312; public)
  - `stuck_texts(self, connection: Any) -> Sequence[StuckText]` (line 317; public)
  - `_rows(rows: Any) -> list[StuckText]` (line 321; internal)
- `stuck_texts(repository: Repository, source: StuckTextSource | None=None) -> list[StuckText]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 342)
- `stuck_text_for(repository: Repository, attempt_id: str, source: StuckTextSource | None=None) -> StuckText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 347) — One attempt's non-empty stuck text, or None.
- `stuck_answer_text(vault: LoadedVault, repository: Repository, attempt_id: str, source: StuckTextSource | None=None) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 360)
- `is_figure_prediction(source_id: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 411)
- `figure_prediction_id(source_id: str) -> tuple[str, bool]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 415) — ``(prediction id, whether the source is its later explanation)``.
- `figure_prediction_row(repository: Repository, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 424) — A missed figure prediction with an answer, with its figure, or None (for an explanation source, also None until the explanation is written).
- `figure_input_manifest(row: Mapping[str, Any]) -> list[str] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 450) — Every span a figure was built from and its author was sent, or None when the stored lists are unreadable (a caller fails closed): the selection, the region's block, the crop's block and ``input_span_ids`` (the paragraphs around it).
- `figure_input_keys(row: Mapping[str, Any]) -> dict[str, list[str]] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 473) — Reader RW5d: the retrieved passages a figure was built from, in any source (``input_span_keys_json``), by extraction; None when unreadable (a caller fails closed).
- `class SourceWithheld(Exception)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 492) — A learner text whose context is held-out material now: nothing of it is built or sent, and its job is skipped (not retried) with this reason.
- `figure_prediction_withheld(vault: LoadedVault, repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 497) — Why a missed prediction's text may not be read now, or None: any span of its figure's complete input manifest is held out (the figure service's one predicate, ``exam_material.spans_withheld``), or the manifest is unreadable (fails closed).
- `figure_grounding_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 522) — Reader RW5d (Codex review F5): the passages a figure with no passage of its own was grounded in, ``(extraction_id, span_id)`` across sources: the kept ones its request recorded (the verified retrieval's picks, or a tutor answer's cited spans), else every retrieved key it was sen…
- `missed_prediction_ids(repository: Repository) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 550)
- `explained_predictions(repository: Repository) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 559) — ``(prediction id, its "what changed?" text)`` for every missed prediction with an answer and an explanation, oldest first: what the backlog sweep reconciles (fix round 2, F5).
- `figure_prediction_spans(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 573)
- `figure_prediction_text(vault: LoadedVault, repository: Repository, prediction_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 587) — RW5a: a missed figure prediction, read by the gap reader.
- `formative_row(repository: Repository, question_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 660) — A missed formative answer (``reader_authored_questions``), or None.
- `figures_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 681) — RW5a's kill switch, ``figures.enabled``: off, no figure prediction or explanation is discovered, reconciled, queued or read.
- `missed_formative_ids(repository: Repository, *, figures: bool=True) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 689) — Every missed formative answer (:func:`formative_row`'s rule), oldest first, then, with ``figures`` (:func:`figures_enabled`), every missed figure prediction (RW5a): what the backlog sweep may queue.
- `reader_formative_text(vault: LoadedVault, repository: Repository, question_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 731) — A missed next-step, why-step or assumption answer, read by the gap reader.
- `hint_feedback_row(repository: Repository, assist_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 790) — A practice-screen ``help_assists`` row whose learner text is a ``hint_feedback`` source (spec §9), with its role, or None: a "doesn't connect" reply with text (``request = 'feedback'``, role ``hint_feedback``) or an answer to a discriminating question (``assist_kind = 'discrimin…
- `hint_feedback_ids(repository: Repository) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 818) — Every ``help_assists`` row whose text is a ``hint_feedback`` source (:func:`hint_feedback_row`'s rule), oldest first: what the backlog sweep and the sidecar's start-up reconciliation may queue (H2b review F4: a row that committed while its job did not).
- `hint_feedback_text(vault: LoadedVault, repository: Repository, assist_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 867) — Adaptive hints H2b: a "doesn't connect" reply's text or a discriminating answer, read by the gap reader (``hint_feedback``).
- `workbench_text_row(repository: Repository, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 924) — A workbench learner text with its role, or None: a stuck step's version (``workbench_steps``, role ``stuck``, not deleted, non-empty), or a workbench ``help_assists`` row with text (a reply, role ``hint_feedback``; an answer to a discriminating question, role ``discriminate_answ…
- `workbench_text(vault: LoadedVault, repository: Repository, source_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 966) — Reader workbench RW2b: a workbench text read by the gap reader (``workbench_text``).
- `workbench_text_ids(repository: Repository) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1011) — Every workbench reply or discriminating answer with text, oldest first (the backlog sweep; stuck steps are queued when they are sent, by version, never swept).
- `learner_notes_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1031) — Curriculum C5's switches (``notes.gaps_enabled``, the learner's opt-in, default off; ``notes.enabled``; ``learner_text_gaps.enabled``).
- `learner_note_ids(vault: LoadedVault, repository: Repository) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1046) — Curriculum C5: the linked notes' current snapshots, oldest link first: what the backlog sweep may queue (empty while switched off; no note row is read then).
- `learner_note_text(vault: LoadedVault, repository: Repository, note_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1057) — Curriculum C5 (spec §10.2, §12 C5): a note the learner linked, read by the gap reader like any other learner text (C2b), tier 2 (``NON_SERVING_SOURCE_KINDS``).
- `learner_note_refusal(vault: LoadedVault, repository: Repository, note_id: str, *, prepared: LearnerText | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1092) — Curriculum C5 (Codex review F3): why the linked snapshot ``note_id`` may not be read for gaps now (None: it may), from ``vault`` as configured now.
- `lesson_gap_text(vault: LoadedVault, repository: Repository, source_id: str) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1118) — A teacher's ``propose_gap`` (spec_teacher_v1 §11.7): the learner's own words it names (their reply, an answer and its "your thinking" note), read in context by the teacher as the tutor reads a question (its reading names the gap), about the node's LO.
- `learner_text(vault: LoadedVault, repository: Repository, source_kind: str, source_id: str, *, stuck_source: StuckTextSource | None=None) -> LearnerText | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 1161)

### Module constants

- `_READABLE_DIAGNOSIS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 58)
- `DEFAULT_STUCK_SOURCE` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 339)
- `FORMATIVE_STYLES` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 392)
- `MISSED_SELF_CHECKS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 393)
- `FORMATIVE_PASSAGE_CHARS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 395)
- `FORMATIVE_EXPECTED_CHARS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 396)
- `FIGURE_PREDICTION_PREFIX` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 402)
- `FIGURE_EXPLANATION_SUFFIX` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 406)
- `_DIRECTION_WORDS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 408)
- `HINT_FEEDBACK_ROLES` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 785)
- `HINT_TEXT_CHARS` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 787)
- `WORKBENCH_TEXT_ROLES` ([src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 916)

### Explicit exports

`__all__` declares:

- `DEFAULT_STUCK_SOURCE`
- `StuckAnswersAdapter`
- `StuckText`
- `SourceWithheld`
- `StuckTextSource`
- `diagnosis_text`
- `FIGURE_EXPLANATION_SUFFIX`
- `FIGURE_PREDICTION_PREFIX`
- `explained_predictions`
- `figure_input_manifest`
- `figures_enabled`
- `figure_prediction_id`
- `figure_prediction_row`
- `figure_prediction_text`
- `figure_prediction_withheld`
- `formative_row`
- `is_figure_prediction`
- `hint_feedback_ids`
- `hint_feedback_row`
- `hint_feedback_text`
- `learner_note_ids`
- `learner_note_refusal`
- `learner_note_text`
- `lesson_gap_text`
- `learner_notes_enabled`
- `learner_text`
- `missed_formative_ids`
- `reader_formative_text`
- `reading_from_diagnosis`
- `resolve_prerequisite_ref`
- `stuck_answer_text`
- `stuck_text_for`
- `stuck_texts`
- `tutor_question_text`
- `WORKBENCH_TEXT_ROLES`
- `workbench_text`
- `workbench_text_ids`
- `workbench_text_row`

## Internal implementation anchors

- `_item_subject(vault: LoadedVault, item: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 64)
- `_diagnosis_row(repository: Repository, diagnosis_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 132)
- `_missed_answer_ids(repository: Repository) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 697)
- `_key_texts(repository: Repository, keys: Sequence[tuple[str, str]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 712) — The passages' texts in order, across sources (one source: :func:`_span_texts`).
- `_span_texts(repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 722)
- `_json_field(value: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 837)
- `_assist_text(repository: Repository, item: Any, assist_id: str | None) -> tuple[str, int | None]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 845) — The text a learner replied to (a hint, or a discriminating question) and its level.
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py), line 919)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `figure_prediction_withheld`; statically calls `figure_prediction_withheld`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `FIGURE_EXPLANATION_SUFFIX`, `SourceWithheld`, `StuckTextSource`, `attempt_grade_held`, `explained_predictions`, `figures_enabled`, `formative_row`, `hint_feedback_ids`, `hint_feedback_row`, `is_figure_prediction`, `learner_note_ids`, `learner_notes_enabled`, `learner_text`, `missed_formative_ids`, `stuck_text_for`, `stuck_texts`, `workbench_text_ids`, `workbench_text_row`; statically calls `attempt_grade_held`, `explained_predictions`, `figures_enabled`, `formative_row`, `hint_feedback_ids`, `hint_feedback_row`, `is_figure_prediction`, `learner_note_ids`, `learner_notes_enabled`, `learner_text`, `missed_formative_ids`, `stuck_text_for`, `stuck_texts`, `workbench_text_ids`, `workbench_text_row`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `learner_note_refusal`; statically calls `learner_note_refusal`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`; statically calls `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `module`; calls `stuck_answer`, `stuck_answers`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `spans_withheld`; calls `spans_withheld`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `lesson`, `turns`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `GapReading`, `LearnerText`; calls `GapReading`, `LearnerText`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `figure_home_keys`, `figures_enabled`; calls `figure_home_keys`, `figures_enabled`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `prerequisite_learning_objects`; calls `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `module`; calls `enabled`, `linked_note_ids`, `note_text`, `payload`, `refusal`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_input_provenance_helpers.py](../../../../../../../tests/diagnosis_input_provenance_helpers.py) — direct import
- [tests/learner_text_gaps_helpers.py](../../../../../../../tests/learner_text_gaps_helpers.py) — direct import
- [tests/learner_text_gaps_review_helpers.py](../../../../../../../tests/learner_text_gaps_review_helpers.py) — direct import
- [tests/test_figure_predictions.py](../../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_what_changed_is_kept_once_and_read_with_the_missed_prediction`
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f5_an_explained_source_with_no_explanation_reads_nothing`
  - `test_f5_an_explanation_after_the_reading_is_read_as_its_own_text`
- [tests/test_figures_fix_round2.py](../../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f1_a_later_explanation_of_a_held_out_figure_is_skipped_too`
  - `test_f5_off_save_on_sweep_reads_the_explanation_once`
- [tests/test_figures_fix_round3.py](../../../../../../../tests/test_figures_fix_round3.py) — direct import
  - `test_f5_an_explanation_repeating_the_answer_is_still_read`
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — direct import
  - `test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text`
- [tests/test_figures_show_me.py](../../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_missed_predictions_text_rechecks_the_retrieved_passages`
- [tests/test_figures_show_me_codex_review.py](../../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f4_a_home_held_out_after_construction_withholds_the_figure`
  - `test_f5_a_goal_only_figures_prediction_is_read_with_its_grounding_passages`
  - `test_f5_an_anchored_figures_text_is_unchanged`
  - `test_f5_the_gap_reader_is_sent_the_grounding_passage`
- [tests/test_figures_switch_off.py](../../../../../../../tests/test_figures_switch_off.py) — direct import
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
  - `test_switched_off_nothing_is_read_and_nothing_is_set_aside`
- [tests/test_held_grade_composition.py](../../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_diagnosis_of_a_held_attempt_is_never_read_as_a_wrong_answer`
- [tests/test_hint_feedback_texts.py](../../../../../../../tests/test_hint_feedback_texts.py) — direct import
  - `test_a_discriminating_answer_is_queued_with_its_role`
  - `test_a_hint_row_without_reply_text_is_no_source`
  - `test_the_reader_sees_the_reply_its_hint_and_question_never_an_answer_key`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_library_question_is_anchored_by_its_notes_single_learning_object`
  - `test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide`
- [tests/test_learner_text_gaps_composition.py](../../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_an_empty_stuck_answer_is_no_learner_text`
  - `test_t6_verified_spans_and_the_tutors_named_gap_both_hold`
  - `test_the_default_adapter_reads_mains_stuck_module_by_id_without_a_scan`
  - `test_the_gap_signal_changes_serving_only_with_its_switch`
- [tests/test_learner_text_gaps_flow.py](../../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_diagnosis_is_read_from_its_causes_without_a_call`
  - `test_diagnosis_kinds`
  - `test_stuck_text_is_read_through_the_source_interface`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f4_a_stuck_answer_is_read_by_its_id_with_its_current_reading`
  - `test_rr_f4_the_stuck_modules_own_per_attempt_reader_is_preferred`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version`
  - `test_f8_a_diagnosis_no_longer_scans_stuck_answers`
  - `test_f8_a_stuck_answer_is_queued_at_recording_without_a_diagnosis`
  - `test_f8_the_adapter_reads_the_marker_before_scanning`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_changed_note_is_read_with_its_current_snapshot_and_the_old_one_is_not`
  - `test_a_hidden_link_is_never_read_and_undo_queues_it_again`
  - `test_an_unlinked_note_never_feeds_gaps`
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
  - `test_c2b_a_reader_note_written_beside_material_protected_since_is_never_read`
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
  - `test_only_linked_notes_are_queued_with_their_snapshot_and_their_topics`
  - `test_step0_a_checkpointed_note_reading_is_never_reused_after_its_inputs_change`
  - `test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing`
- [tests/test_notes_c2b_review5.py](../../../../../../../tests/test_notes_c2b_review5.py) — direct import
  - `test_c2b_r5_f2_a_notes_reading_records_its_anchor_heading_and_every_section_span`
  - `test_c2b_r5_f2_the_note_gate_refuses_once_a_bound_source_is_protected`
- [tests/test_reader_formative_texts.py](../../../../../../../tests/test_reader_formative_texts.py) — direct import
  - `test_the_dispatcher_reads_the_answer_with_its_question_passage_and_expected_answer`
- [tests/test_reader_rw1b_review.py](../../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
- [tests/test_ro2_history_protection.py](../../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_the_registry_restates_the_figure_source_grammar`
- [tests/test_teacher_te2_lessons.py](../../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_a_gap_from_the_learners_words_goes_to_the_text_gap_pipeline_with_source_lesson`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_text_gap_kind_is_reused_never_paid_for_twice`
- [tests/test_workbench_text_gaps.py](../../../../../../../tests/test_workbench_text_gaps.py) — direct import
  - `test_a_reply_and_a_discriminating_answer_are_workbench_text_never_hint_feedback`
  - `test_a_stuck_step_is_read_with_its_role_item_and_anchor`
  - `test_an_empty_stuck_step_or_an_ordinary_step_is_no_source`

## Modification guidance

- Change sources policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/sources.py](../../../../../../../src/learnloop/diagnosis/text_gaps/sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
