---
title: "learnloop.diagnosis.text_gaps.provenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/provenance.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/provenance.py"
source_commit: "f3d6aba0ae47c99d0d4344e00c87287e27318f1c"
source_commit_timestamp: "2026-11-02T02:00:30-05:00"
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
  - "learnloop.diagnosis.text_gaps.provenance module"
  - "src/learnloop/diagnosis/text_gaps/provenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.provenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.provenance` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: What the learner-text pipeline's writers read (spec_mcp_frontend_c1 §4.8).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py) |
| Source lines | 413 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f3d6aba0ae47c99d0d4344e00c87287e27318f1c` |
| Commit timestamp | `2026-11-02T02:00:30-05:00` |

## Public API

- `question_record(connection: Any, event_id: str, *, topics: Iterable[Any]=()) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 96) — What a learner question's words carry (see the module doc).
- `reading_sources(connection: Any, source_kind: str, source_id: str) -> tuple[tuple[Mapping[str, Any], ...], bool]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 206) — The passages a learner text was written on, for a reading-derived source (:data:`READING_SOURCE_KINDS`), and whether they could all be read: a Reader question's passage (``question_events.source_context``; a question asked outside the Reader names none), an active-reading answer…
- `text_record(connection: Any, text: Any) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 241) — What a learner text and its context show any reader of it.
- `note_record(text: Any) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 265) — Curriculum C5 (C2b): what a linked note shows its reader -- the learner's own words (no attempt, so no answer contract), the topics it is linked to, the passages it is linked to, and every book span its text and context carry text from, frozen when the reading was prepared (Code…
- `formative_record(connection: Any, question_id: str, *, topics: Iterable[str]=()) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 284) — RW1b: what a missed active-reading answer shows its reader -- the learner's answer (not an attempt, so no answer contract), the book's passage and the cited spans of the expected answer, and the topics.
- `figure_prediction_record(connection: Any, prediction_id: str, *, topics: Iterable[str]=()) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 308) — RW5a: what a missed figure prediction shows its reader -- the learner's answer (not an attempt), every span the figure was built from (the selection, a region's block and the paragraphs the author was sent around it: the figure's prediction and readouts derive from all of them;…
- `hint_feedback_record(connection: Any, text: Any) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 348) — Adaptive hints H2b: what a reply to a hint shows its reader -- the learner's words (no attempt's answer contract while the attempt is open), the item's question, and the hint or question it answered.
- `reading_record(connection: Any, text: Any, reading: Any=None) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 363) — What wrote a reading's named gap (a belief statement, a prerequisite name and line): its reader's inputs (see the module doc).
- `drafter_record(connection: Any, vault: Any, text: Any, reading: Any, *, subject_id: str | None, shown_concept_titles: Iterable[str]=()) -> WriteRecord` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 376) — What the prerequisite drafter read: the reading, the learner text and its context, the asking topic, and the topics whose concept titles it was shown (``shown_concept_titles``).

### Module constants

- `TUTOR_UNRECORDED` ([src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 44)
- `READING_SOURCE_KINDS` ([src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 122)
- `READER_QUESTION_CONTEXT` ([src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 127)
- `_NOTE_FIELDS` ([src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 173)

### Explicit exports

`__all__` declares:

- `TUTOR_UNRECORDED`
- `drafter_record`
- `figure_prediction_record`
- `formative_record`
- `hint_feedback_record`
- `question_record`
- `reading_record`
- `text_record`

## Internal implementation anchors

- `_question_row(connection: Any, event_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 47)
- `_revealed_before(connection: Any, item_id: str, at: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 74)
- `_reader_sources(source_context: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 85)
- `_question_passages(source_context: Mapping[str, Any]) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 130) — The passages a question's source context names, and whether every one could be placed (Codex review F1).
- `_identified_note(value: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 176)
- `_located_without_extraction(value: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 180) — A delivered span with no ``extraction_id`` that still places a book passage: a block the shared parser places (``exam_material.source_ref_keys``: a namespaced span id ``ext:span`` or ``ext/span``, a block locator), or a source or revision id (checked against every extraction of…
- `_reader_span_key(note_id: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py), line 196) — The passage a Reader question's ``note_id`` names (``span:<extraction>/<span>``, ``tutor_qa.reader_span_key``), else None (no key, a note id, no block).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `reading_record`; statically calls `reading_record`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `TUTOR_UNRECORDED`, `drafter_record`, `formative_record`, `hint_feedback_record`, `note_record`, `question_record`; statically calls `drafter_record`, `formative_record`, `hint_feedback_record`, `note_record`, `question_record`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `READING_SOURCE_KINDS`, `reading_sources`; statically calls `reading_sources`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `source_ref_keys`; calls `source_ref_keys`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `GRADING`, `Inputs`, `WriteRecord`, `answer_inputs`, `closure`, `fold_topic_records`, `source_ref`; calls `WriteRecord`, `answer_inputs`, `closure`, `fold_topic_records`, `source_ref`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`; calls `figure_input_keys`, `figure_input_manifest`, `figure_prediction_id`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f2_the_drafter_folds_a_generated_topic_only_under_the_name_it_was_shown`
  - `test_rereview_f2_the_drafter_checks_its_anchor_and_prerequisite_names`
- [tests/test_figure_predictions.py](../../../../../../../tests/test_figure_predictions.py) — direct import
  - `test_what_changed_is_kept_once_and_read_with_the_missed_prediction`
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f1_a_context_neighbour_held_out_after_authoring_withholds_the_figure`
  - `test_f5_an_explanation_after_the_reading_is_read_as_its_own_text`
- [tests/test_figures_show_me.py](../../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_missed_predictions_text_rechecks_the_retrieved_passages`
- [tests/test_reader_question_note_id_placement.py](../../../../../../../tests/test_reader_question_note_id_placement.py) — direct import
  - `test_a_question_outside_the_reader_is_unchanged`
  - `test_a_reader_question_that_still_cannot_be_placed_fails_closed`
  - `test_a_reader_question_with_no_source_context_is_placed_from_its_note_id`
- [tests/test_ux_phase4_landing.py](../../../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_routine_display_marks_a_later_question_solution_seen_beyond_its_coverage`

## Modification guidance

- Change provenance policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/provenance.py](../../../../../../../src/learnloop/diagnosis/text_gaps/provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
