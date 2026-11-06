---
title: "learnloop.teacher.guards"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/guards.py"
source_paths:
  - "src/learnloop/teacher/guards.py"
source_commit: "b18685c89ea24659f1ed763ea937199a39a96fb8"
source_commit_timestamp: "2026-11-06T09:42:06-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.guards module"
  - "src/learnloop/teacher/guards.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.guards`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.guards` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The output guards (spec_teacher_v1 §9.3): every learner-facing field passes three (the message and its choices, a prediction, a check, plan statements and a close's recap: ``service._displayed``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py) |
| Source lines | 283 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b18685c89ea24659f1ed763ea937199a39a96fb8` |
| Commit timestamp | `2026-11-06T09:42:06-05:00` |

## Public API

- `class GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 41)
  - `as_dict(self) -> dict[str, Any]` (line 46; public)
- `key_sets(vault: Any, repository: Any, learning_object_ids: Iterable[str], exempt_items: Iterable[str]) -> tuple[list[Any], list[Any], bool]` ([source](../../../../../../src/learnloop/teacher/guards.py), line 60) — ``(lesson keys, vault keys, unreadable)`` from one read of the KeyBook: every recorded answer key on these LOs except the exempt items' (the displayed text's guard), and every answer key the vault records on any item, on any LO (the identifier guard's, :func:`identifier_guard`).
- `lesson_keys(vault: Any, repository: Any, learning_object_ids: Iterable[str], exempt_items: Iterable[str]) -> tuple[list[Any], bool]` ([source](../../../../../../src/learnloop/teacher/guards.py), line 78) — ``(keys, unreadable)``: every recorded answer key on these LOs except the exempt items'.
- `identifier_guard(text: str, vault_keys: Sequence[Any], unreadable: bool) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 86) — A model-supplied field a log row or a receipt copies (a plan node's id or ``lo_id``, a note's node and hypothesis, a forecast's node and its LO) against every answer key the vault records (TE2-log landing, ruling R1): an exam-reserved or held-out item's on any LO, a topic the le…
- `key_guard(message: str, keys: Sequence[Any], unreadable: bool) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 102)
- `class ReservedBook` ([source](../../../../../../src/learnloop/teacher/guards.py), line 132) — The questions still reserved for an exam or held out, read once per turn (``questions``: ``practice_leakage.ReservedQuestions``).
- `reserved_book(vault: Any, repository: Any) -> ReservedBook` ([source](../../../../../../src/learnloop/teacher/guards.py), line 140) — The reserved and held-out questions as the rest of LearnLoop reads them: ``withheld_items`` (exam pools, held-out units and the items made from them, live assessment reservations), then ``reserved_questions`` (their stems, keys and rubrics, and every held-out span).
- `quotes_reserved(text: str, reserved: ReservedBook) -> bool` ([source](../../../../../../src/learnloop/teacher/guards.py), line 157) — Whether ``text`` reproduces a reserved or held-out question by the matcher's span rule.
- `reserved_guard(text: str, reserved: ReservedBook) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 182) — A field that would show a question kept for an exam or held out.
- `shown_feedback(feedback: str | None, reserved: ReservedBook) -> str | None` ([source](../../../../../../src/learnloop/teacher/guards.py), line 196) — A grader's feedback as the lesson shows it: None when it reproduces a reserved or held-out question, or when those could not be read (the result itself stands).
- `solution_overlap(text: str, solution: str) -> float` ([source](../../../../../../src/learnloop/teacher/guards.py), line 205) — How much of a committed solution ``text`` exposes (0..1; the tutor's span measure).
- `open_check_guard(message: str, open_check: Mapping[str, Any] | None) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 215)
- `citation_guard(message: str, book: SourceBook) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 226)
- `check_all(message: str, *, keys: Sequence[Any], unreadable: bool, book: SourceBook, open_check: Mapping[str, Any] | None, help_reply: bool, reserved: ReservedBook, vault_keys: Sequence[Any] | None=None) -> GuardVerdict` ([source](../../../../../../src/learnloop/teacher/guards.py), line 241) — The guards in order, the first refusal named: keys; for a logged field (``vault_keys`` given) the identifier guard; reserved questions; the open check's (skipped for a reply to the learner's own question); citations.
- `cited_aliases(message: str) -> list[str]` ([source](../../../../../../src/learnloop/teacher/guards.py), line 261)

### Module constants

- `CITATION` ([src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py), line 35)
- `QUOTE_CITATION` ([src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py), line 37)
- `RESERVED_SPAN_KINDS` ([src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py), line 128)

### Explicit exports

`__all__` declares:

- `CITATION`
- `GuardVerdict`
- `RESERVED_SPAN_KINDS`
- `ReservedBook`
- `check_all`
- `citation_guard`
- `cited_aliases`
- `identifier_guard`
- `key_guard`
- `key_sets`
- `lesson_keys`
- `open_check_guard`
- `quotes_reserved`
- `reserved_book`
- `reserved_guard`
- `shown_feedback`
- `solution_overlap`

## Internal implementation anchors

- `_normalize(text: str) -> str` ([source](../../../../../../src/learnloop/teacher/guards.py), line 50)
- `_identity(value: Any) -> str` ([source](../../../../../../src/learnloop/teacher/guards.py), line 54)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; statically calls `reserved_book`, `shown_feedback`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `GuardVerdict`, `check_all`, `cited_aliases`, `key_guard`, `key_sets`, `lesson_keys`, `open_check_guard`, `reserved_book`, `reserved_guard`, `shown_feedback`, `solution_overlap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`; calls `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `key_book`, `leaks_key`; calls `key_book`, `leaks_key`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `SourceBook`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`, `span_leaks_expected`; calls `span_answer_overlap`, `span_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_exam_question_guard.py](../../../../../../tests/test_teacher_exam_question_guard.py) — direct import
  - `test_a_lesson_with_no_reserved_text_is_byte_identical_with_the_guard_off`
  - `test_a_reserved_question_split_between_message_and_check_is_withheld`
  - `test_a_short_reserved_question_counts_when_an_ordinary_item_shows_its_number`
  - `test_a_short_reserved_question_with_a_word_distinctive_in_the_vault_counts_wherever_it_stands`
  - `test_a_teacher_turn_holding_a_short_distinctive_reserved_question_inside_a_sentence_is_withheld`
  - `test_a_whole_short_reserved_question_with_a_distinctive_number_counts`
  - `test_distinctive_is_read_from_the_vaults_own_items_and_readable_passages`
  - `test_reserved_book_is_unreadable_when_withheld_items_is`
  - `test_the_matcher_reads_both_items_as_withheld_questions`

## Modification guidance

- Make changes here when the responsibility remains guards within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/guards.py](../../../../../../src/learnloop/teacher/guards.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
