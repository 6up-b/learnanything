---
title: "learnloop.learner_protection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner_protection.py"
source_paths:
  - "src/learnloop/learner_protection.py"
source_commit: "workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a"
source_commit_timestamp: "2026-11-04T00:19:09-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner_protection module"
  - "src/learnloop/learner_protection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.learner_protection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner_protection` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: What of the learner's past work a model context may show: one authority.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py) |
| Source lines | 773 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD efd894886714472c5495a6a6b87e97e8a774701a` |
| Commit timestamp | `2026-11-04T00:19:09-05:00` |

## Public API

- `class Withheld` ([source](../../../../../src/learnloop/learner_protection.py), line 128) — Items whose question and answers never reach a model context, and why.
  - `reason(self, item_id: str | None) -> str | None` (line 145; public)
  - `item_ids(self) -> frozenset[str]` (line 155; public)
- `protection_issues(vault: Any) -> list[str]` ([source](../../../../../src/learnloop/learner_protection.py), line 159) — Why the vault's protection metadata cannot be trusted, or ``[]``.
- `withheld_items(vault: Any, repository: Any) -> Withheld` ([source](../../../../../src/learnloop/learner_protection.py), line 190) — Every item whose question and answers a model context never shows.
- `attempt_protection(withheld: Withheld, attempt: Mapping[str, Any] | None) -> str | None` ([source](../../../../../src/learnloop/learner_protection.py), line 250) — Why an attempt's question and answer are withheld, or None.
- `attempt_result(correctness: Any, held: bool) -> str` ([source](../../../../../src/learnloop/learner_protection.py), line 276) — An attempt's result class: a grade held for review (THE predicate, ``held_grades``) is ``held_for_review``, never a score.
- `held_attempts(connection: Any, attempt_ids: Sequence[Any]) -> frozenset[str]` ([source](../../../../../src/learnloop/learner_protection.py), line 292) — The attempts among ``attempt_ids`` whose grade is held for review (THE predicate).
- `frozen_method(value: Any) -> Any` ([source](../../../../../src/learnloop/learner_protection.py), line 304) — A contract's frozen ``required_method`` as ``json_extract`` returns it (a JSON text for an object), or None.
- `class PinnedContract` ([source](../../../../../src/learnloop/learner_protection.py), line 317) — The assessment contract an answer was graded against: its statement and the required method it froze.
  - `question(self, limit: int, clip: Callable[[str, int], str]) -> str | None` (line 326; public) — The question as graded, or None without a statement: the frozen statement, then the instruction of the method it froze, the statement shortened by ``clip`` so the instruction stays whole within ``limit`` (``vault.required_method.fit_presented_prompt``, the contract's pair ``answ…
- `pinned_contracts(connection: Any, items: Mapping[str, Any]) -> dict[str, PinnedContract]` ([source](../../../../../src/learnloop/learner_protection.py), line 344) — ``{attempt id: its pinned contract}`` for the attempts (``{attempt id: practice item}``) graded against exactly one assessment contract of their own item: the only affirmative record of the question revision an answer was graded against (router R2a review F6; the rule is ``db.st…
- `hypothesis_answers(connection: Any, hypothesis_ids: Iterable[Any]) -> dict[str, frozenset[str]]` ([source](../../../../../src/learnloop/learner_protection.py), line 376) — ``{hypothesis id: the answers its episode rests on}``: the attempt of every version of the hypothesis's episode.
- `class PastWork` ([source](../../../../../src/learnloop/learner_protection.py), line 406) — One read's protection, cached: the withheld items, the attempts read, their pinned contracts.
  - `__init__(self, connection: Any, vault: Any, repository: Any=None, *, withheld: Withheld | None=None, unknowns: list[str] | None=None) -> None` (line 415; internal)
  - `_note(self, unknown: str) -> None` (line 427; internal)
  - `withheld(self) -> Withheld` (line 432; public)
  - `load(self, attempt_ids: Iterable[Any]) -> None` (line 440; public) — Read these attempts (item, type, probe, topic, answer) and their pins.
  - `attempt(self, attempt_id: Any) -> dict[str, Any] | None` (line 464; public) — The attempt as read (``item``, ``type``, ``probe``, ``lo``, ``answer``), or None.
  - `attempt_reason(self, attempt_id: Any) -> str | None` (line 470; public) — Why this attempt's question and answer, and everything written about it, are protected (:func:`attempt_protection`), or None.
  - `pinned(self, attempt_id: Any) -> PinnedContract | None` (line 478; public) — The contract this answer was graded against, or None when the revision is not established (no contract, several, another item's).
  - `held(self, attempt_ids: Sequence[Any]) -> frozenset[str]` (line 485; public) — The attempts whose grade is held for review (THE predicate).
  - `evidence_reason(self, answers: Iterable[Any]=(), items: Iterable[Any]=()) -> str | None` (line 490; public) — The leakage rule for a text written from these answers and items: why any of them is protected (or protection is unreadable), or None.
  - `exam_reason(self, answers: Iterable[Any]=(), items: Iterable[Any]=(), sources: Iterable[Mapping[str, Any]]=()) -> str | None` (line 510; public) — The leakage rule for a reader that may see everything but exam material (FG1's author: a new question, on a topic the learner just answered): why a text written from these may quote exam or reserved material, or why that can't be ruled out.
  - `window_closed(self, item_id: Any) -> bool` (line 538; public) — Whether the item's attempt window is closed: its latest attempt is a correct submission whose grade is not held for review (the retrieval policy's rule for unlocking an item's own solution, ``instructional.policy.attempt_window_open``).
  - `solution_reason(self, item_ids: Iterable[Any]) -> str | None` (line 558; public) — Why a text written with these items' rubrics or reference solutions may not leave LearnLoop, or None: an item's own protection first, then an attempt window still open (:meth:`window_closed`): showing it would hand the learner the solution of a question they can still answer col…
  - `source_reason(self, refs: Iterable[Mapping[str, Any]]) -> str | None` (line 579; public) — Why a text written from these source refs may not leave LearnLoop: a ref that is (or may be) exam or held-out material (``exam_material.source_ref_protected``, conservative where it cannot place the text), or exam material that could not be read.
  - `reading_reason(self, source_kind: Any, source_id: Any) -> str | None` (line 605; public) — Why a learner text written on a reading may not leave LearnLoop (followups-nov1c E: exam-material protection, not privacy): the passage it was written on (a Reader question's, an active-reading answer's, a figure prediction's) is or may be exam or held-out material (:meth:`sourc…
  - `question(self, event_id: Any) -> dict[str, Any] | None` (line 626; public) — A learner question as recorded (``item``, ``attempt``, ``context``, ``contract``: the item contract it was asked about, Q10), or None.
  - `question_reason(self, event_id: Any, contracts: Iterable[Any]) -> str | None` (line 647; public) — Why a text written from this learner question may not leave LearnLoop: the question is not on record; on an item, the item or the attempt it was asked during is protected, or the question records no contract of that item, or not the one the writer read it under (Q10).
- `class TextRule(Protocol)` ([source](../../../../../src/learnloop/learner_protection.py), line 681) — How a reader's text leaves LearnLoop once the protection here has passed.
  - `question(self, attempt_id: str, lo_id: Any) -> tuple[str | None, str | None]` (line 689; public) — The question an unprotected attempt was graded against.
  - `answer(self, attempt_id: str, text: Any, limit: int) -> tuple[str | None, str | None]` (line 692; public) — The learner's own answer on an unprotected attempt.
  - `statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any]=(), items: Iterable[Any]=(), los: Iterable[Any]=()) -> tuple[str | None, str | None]` (line 695; public) — A statement (a diagnosis's, a hypothesis's, a learner-text gap's words) whose answers and items are unprotected.
- `class PastWorkText` ([source](../../../../../src/learnloop/learner_protection.py), line 702) — What one past attempt shows: ``withheld`` (why its question and answer are protected) or its question and answer as the text rule released them.
- `past_work_text(past: PastWork, rule: TextRule, attempt_id: Any, lo_id: Any, answer: Any, answer_limit: int) -> PastWorkText` ([source](../../../../../src/learnloop/learner_protection.py), line 713) — One past attempt's question and answer: the protection, then the reader's text rule.
- `statement_text(past: PastWork, rule: TextRule, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any]=(), items: Iterable[Any]=(), los: Iterable[Any]=()) -> tuple[str | None, str | None, str | None]` ([source](../../../../../src/learnloop/learner_protection.py), line 725) — A statement written from ``answers`` and ``items``: ``(text, note, withheld)``.

### Module constants

- `_LOG` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 74)
- `WITHHELD_EXAM` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 77)
- `WITHHELD_RESERVED` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 78)
- `WITHHELD_COLD` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 79)
- `WITHHELD_PROBE` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 80)
- `WITHHELD_UNREADABLE` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 81)
- `WITHHELD_UNKNOWN_ITEM` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 82)
- `WITHHELD_SOLUTION_OPEN` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 85)
- `QUESTION_UNRECORDED` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 87)
- `ANSWER_UNRECORDED` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 89)
- `STEM_UNRECORDED` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 91)
- `PINS_UNREADABLE` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 92)
- `SNAPSHOT_UNSETTLED` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 97)
- `PROTECTION_UNKNOWN` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 98)
- `EXAM_ATTEMPT_TYPES` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 100)
- `PROBE_MODES` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 101)
- `COLD_TASK_KINDS` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 102)
- `WINDOW_CLOSING_CORRECTNESS` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 106)
- `_CHUNK` ([src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py), line 107)

### Explicit exports

`__all__` declares:

- `ANSWER_UNRECORDED`
- `COLD_TASK_KINDS`
- `EXAM_ATTEMPT_TYPES`
- `PINS_UNREADABLE`
- `PROBE_MODES`
- `PROTECTION_UNKNOWN`
- `QUESTION_UNRECORDED`
- `SNAPSHOT_UNSETTLED`
- `STEM_UNRECORDED`
- `WITHHELD_COLD`
- `WITHHELD_EXAM`
- `WITHHELD_PROBE`
- `WITHHELD_RESERVED`
- `WITHHELD_SOLUTION_OPEN`
- `WITHHELD_UNKNOWN_ITEM`
- `WITHHELD_UNREADABLE`
- `WINDOW_CLOSING_CORRECTNESS`
- `PastWork`
- `PastWorkText`
- `PinnedContract`
- `TextRule`
- `Withheld`
- `attempt_protection`
- `attempt_result`
- `frozen_method`
- `held_attempts`
- `hypothesis_answers`
- `past_work_text`
- `pinned_contracts`
- `protection_issues`
- `statement_text`
- `withheld_items`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../src/learnloop/learner_protection.py), line 110)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../src/learnloop/learner_protection.py), line 116)
- `_ids(values: Iterable[Any]) -> frozenset[str]` ([source](../../../../../src/learnloop/learner_protection.py), line 120)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `attempt_result`, `module`; statically calls `attempt_protection`, `attempt_result`, `held_attempts`, `withheld_items`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `withheld_items`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `withheld_items`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `PastWork`, `Withheld`, `attempt_result`, `module`, `past_work_text`, `statement_text`; statically calls `PastWork`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `statement_text`, `withheld_items`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `module`; statically calls `attempt_protection`, `withheld_items`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `withheld_items`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `held_attempts`; statically calls `held_attempts`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `PastWork`, `module`; statically calls `PastWork`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `PastWork`, `WITHHELD_UNREADABLE`, `attempt_result`, `past_work_text`, `statement_text`; statically calls `PastWork`, `attempt_result`, `past_work_text`, `statement_text`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `PastWork`, `hypothesis_answers`, `withheld_items`; statically calls `PastWork`, `hypothesis_answers`, `withheld_items`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `ANSWER_UNRECORDED`, `PINS_UNREADABLE`, `PROTECTION_UNKNOWN`, `PastWork`, `QUESTION_UNRECORDED`, `SNAPSHOT_UNSETTLED`, `STEM_UNRECORDED`, `WITHHELD_COLD`, `WITHHELD_EXAM`, `WITHHELD_PROBE`, `WITHHELD_RESERVED`, `WITHHELD_SOLUTION_OPEN`, `WITHHELD_UNKNOWN_ITEM`, `WITHHELD_UNREADABLE`, `Withheld`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `protection_issues`, `statement_text`, `withheld_items`; statically calls `PastWork`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `statement_text`, `withheld_items`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `module`; statically calls `PastWork`, `attempt_result`, `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `withheld_items`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `protection_issues`; statically calls `protection_issues`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `attempt_protection`, `withheld_items`; statically calls `attempt_protection`, `withheld_items`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `WITHHELD_EXAM`, `WITHHELD_RESERVED`, `attempt_protection`, `withheld_items`; statically calls `attempt_protection`, `withheld_items`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `withheld_items`; statically calls `withheld_items`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `withheld_items`; statically calls `withheld_items`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`, `source_ref_protected`; calls `exam_material`, `held_out_items`, `item_exam_status`, `source_ref_protected`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `pinned_contract_ids`; calls `pinned_contract_ids`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `READING_SOURCE_KINDS`, `reading_sources`; calls `reading_sources`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `module`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`, `method_instruction`; calls `fit_presented_prompt`, `method_instruction`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `pathlib`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deliverable_path.py](../../../../../tests/test_deliverable_path.py) — direct import
  - `test_g_c3_held_out_items_are_never_picked`
- [tests/test_diagnosis_input_provenance.py](../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_a_correction_written_from_exam_material_is_held_back`
  - `test_a_question_that_records_its_contract_is_shown_when_safe`
  - `test_the_reasons_spelled_out_here_are_the_protection_s`
  - `test_the_solution_rule_is_the_retrieval_policy_s_window`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_rule_4_and_identity_bound_marks_reach_rule_c_through_learner_protection`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f1_rereview_a_builds_protection_is_read_on_the_vault_loaded_now`
  - `test_f4_a_build_rechecks_the_protection_before_it_starts`
  - `test_f4_a_cold_items_passage_and_its_neighbours_are_never_prebuilt`
  - `test_f4_unreadable_protection_prebuilds_nothing`
- [tests/test_followup_codex_review.py](../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f5_a_check_waiting_on_the_item_doesnt_stop_the_probe_lane`
  - `test_f5_exam_attempt_work_is_exam_material_whatever_its_item`
  - `test_f5_what_the_writer_recorded_reading_counts`
- [tests/test_followup_generate_e2e.py](../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_protected_and_reserved_items_never_reach_the_prompt`
  - `test_protection_that_cannot_be_read_sends_no_prompt`
- [tests/test_followups_batch6_review_fixes.py](../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f1_unreadable_protection_requeues_nothing_and_the_worker_fails_closed`
- [tests/test_learner_blindness_relax.py](../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_state_carries_no_stored_answer_and_unreadable_protection_carries_nothing`
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
  - `test_a_cross_item_feedback_chain_carries_no_answer`
- [tests/test_learner_data_relax_2.py](../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_protection_unreadable_sends_no_answer_and_no_statement`
  - `test_protection_unreadable_withholds_reading_derived_gaps_too`
- [tests/test_mcp_c1a_landing.py](../../../../../tests/test_mcp_c1a_landing.py) — direct import
  - `test_a_statement_written_from_protected_work_is_withheld_by_both`
  - `test_no_reader_keeps_a_protection_of_its_own`
  - `test_the_card_and_the_chat_withhold_the_same_past_work_for_the_same_reasons`
  - `test_the_text_rule_is_each_readers_own`
- [tests/test_reader_question_note_id_placement.py](../../../../../tests/test_reader_question_note_id_placement.py) — direct import
  - `test_a_legacy_reader_question_is_checked_against_exam_material`
  - `test_a_reader_question_that_still_cannot_be_placed_fails_closed`
- [tests/test_reread_safety_landing.py](../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path`
- [tests/test_router_card_reading_gaps.py](../../../../../tests/test_router_card_reading_gaps.py) — direct import
  - `test_a_delivered_span_without_an_extraction_is_placed_or_fails_closed`
  - `test_a_reader_question_asked_on_an_exam_passage_keeps_its_entry_and_never_its_words`
  - `test_a_reader_question_whose_passage_is_unreadable_or_missing_fails_closed`
  - `test_a_reading_derived_gap_whose_passage_cannot_be_established_fails_closed`
  - `test_an_active_reading_answer_on_an_exam_passage_is_withheld`
  - `test_an_extraction_named_without_a_block_is_checked_whole`
- [tests/test_router_r2c_teach_back.py](../../../../../tests/test_router_r2c_teach_back.py) — direct import
  - `test_exam_or_reserved_work_is_never_summarized`
- [tests/test_secondary_attach.py](../../../../../tests/test_secondary_attach.py) — direct import
  - `test_a_directory_alias_does_not_hide_a_truncated_source_sets_file_from_the_chat_runtime`
- [tests/test_teacher_te0_confidence_events.py](../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_hint_writers_events_fail_closed_when_the_protection_cannot_be_read`
- [tests/test_teacher_te0_fix_round2.py](../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_a_held_review_grade_reads_held_for_review_in_a_later_targets_history`
- [tests/test_teacher_te0_review_fixes.py](../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_a_held_current_attempt_reads_held_for_review_never_wrong`

## Modification guidance

- Make changes here when the responsibility remains learner protection within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/learner_protection.py](../../../../../src/learnloop/learner_protection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
