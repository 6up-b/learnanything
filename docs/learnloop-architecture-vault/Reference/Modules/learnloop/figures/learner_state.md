---
title: "learnloop.figures.learner_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/learner_state.py"
source_paths:
  - "src/learnloop/figures/learner_state.py"
source_commit: "8b967e3b7e1afd9d0eafa309cf6d9758bb647b57"
source_commit_timestamp: "2026-11-02T05:28:19-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.learner_state module"
  - "src/learnloop/figures/learner_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.learner_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.learner_state` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: What the figure author is told about the learner (learner data-relax 2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py) |
| Source lines | 464 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8b967e3b7e1afd9d0eafa309cf6d9758bb647b57` |
| Commit timestamp | `2026-11-02T05:28:19-05:00` |

## Public API

- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 102) — ``figures.author_learner_state`` under ``figures.enabled``.
- `excerpt(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 108)
- `anchored_learning_objects(vault: Any, repository: Any, *, extraction_id: str | None, span_ids: Sequence[str], keys: Sequence[tuple[str, str]]=()) -> list[str]` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 113) — The passage's learning objects (``reader_tutor.passage_learning_objects``): the anchor's spans on ``extraction_id``, then each grounding key's (a request with no passage: its kept passages, else where the learner was reading).
- `inputs_reason(past: Any, inputs: Inputs) -> str | None` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 291) — Why anything these inputs name is protected now, or None: the shared protection's leakage rule on their answers and items (``PastWork.evidence_reason``), each learner question's own check (``PastWork.question_reason``) and the passages they were written beside (``PastWork.source…
- `class LearnerStateRead` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 318) — One read: the ``state`` the author is sent (None: nothing to say, or unreadable) and the ``inputs`` behind what it shows (``Inputs.as_json``: the answers, items, questions and passages a later sender checks again, :func:`inputs_withheld`).
- `read_learner_state(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> LearnerStateRead` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 328) — The author's ``learner_state`` for these topics (module docstring) and what it was read from.
- `open_gap_statements(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 379) — RW5d P5 (spec §10b.2, the gap trigger): the open misconceptions and learner-text gaps on these topics, each with its id, topic and statement, read exactly as the figure author's state reads them (through ``learner_protection``: a statement written from protected work is left out…
- `learner_state(vault: Any, repository: Any, learning_object_ids: Iterable[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 409) — The state alone (:func:`read_learner_state`).
- `inputs_withheld(vault: Any, repository: Any, inputs: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 420) — Why a saved state (its :class:`LearnerStateRead` ``inputs``) may not be sent now, or None: anything it was read from is protected now (:func:`inputs_reason`, against the vault and the database as they are now), or its inputs cannot be read (fail closed).
- `state_hash(state: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 438) — The reuse key's name for a non-empty state (None for none).

### Module constants

- `_LOG` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 70)
- `MAX_TOPICS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 74)
- `MAX_STATEMENTS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 76)
- `STATEMENT_CHARS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 78)
- `RECENT_ANSWERS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 81)
- `ANSWER_CHARS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 83)
- `QUESTION_CHARS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 85)
- `ATTEMPTS_SCANNED` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 87)
- `STATUS_WORDS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 90)
- `WRITTEN_BY_DIAGNOSIS` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 97)
- `WRITTEN_BY_GAP_READING` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 98)
- `WRITTEN_BY_LEARNER` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 99)
- `INPUTS_UNKNOWN` ([src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py), line 417)

### Explicit exports

`__all__` declares:

- `ANSWER_CHARS`
- `ATTEMPTS_SCANNED`
- `INPUTS_UNKNOWN`
- `MAX_STATEMENTS`
- `MAX_TOPICS`
- `QUESTION_CHARS`
- `RECENT_ANSWERS`
- `STATEMENT_CHARS`
- `STATUS_WORDS`
- `LearnerStateRead`
- `anchored_learning_objects`
- `enabled`
- `excerpt`
- `inputs_reason`
- `inputs_withheld`
- `learner_state`
- `open_gap_statements`
- `read_learner_state`
- `state_hash`

## Internal implementation anchors

- `class _AnswerText` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 141) — The text rule (``learner_protection.TextRule``) once the shared protection has passed: the question as graded (the pinned contract's) and the learner's own answer, both shortened.
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 163)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 168)
- `_named(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 172)
- `_misconception_statements(connection: Any, repository: Any, past: Any, rule: _AnswerText, los: Sequence[str], titles: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 185)
- `_gap_inputs(connection: Any, row: Mapping[str, Any]) -> Inputs | None` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 212) — What a gap's words were written from and beside: its answer and item, and its write-time record's answers, items, questions and passages (a reading-derived gap has no answer or item: its record names the passage and topics; Codex review F1).
- `_gap_statements(connection: Any, past: Any, rule: _AnswerText, los: Sequence[str], titles: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 229)
- `_recent_answers(connection: Any, past: Any, rule: _AnswerText, los: Sequence[str], titles: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/learner_state.py), line 262)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `open_gap_statements`; statically calls `open_gap_statements`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `inputs_withheld`; statically calls `inputs_withheld`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`, `state_hash`; statically calls `anchored_learning_objects`, `enabled`, `read_learner_state`, `state_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `Inputs`, `stored_record`; calls `Inputs`, `stored_record`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `author_learner_state_enabled`; calls `author_learner_state_enabled`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PastWork`, `WITHHELD_UNREADABLE`, `attempt_result`, `past_work_text`, `statement_text`; calls `PastWork`, `attempt_result`, `past_work_text`, `statement_text`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `passage_learning_objects`; calls `passage_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `lo_statuses`; calls `lo_statuses`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_gap_trigger_sends_the_statement_and_a_passage_never_an_attempt`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f1_a_gap_judge_retry_is_not_sent_once_its_passage_is_held_out`
  - `test_f1_rereview_a_gap_judge_retry_revalidates_on_the_vault_loaded_now`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_a_reading_derived_gap_is_checked_against_the_passage_it_was_written_beside`
  - `test_no_state_keeps_todays_key_so_the_switch_reuses_todays_figure`
  - `test_protection_unreadable_sends_no_answer_and_no_statement`
  - `test_protection_unreadable_withholds_reading_derived_gaps_too`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`

## Modification guidance

- Make changes here when the responsibility remains learner state within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/learner_state.py](../../../../../../src/learnloop/figures/learner_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
