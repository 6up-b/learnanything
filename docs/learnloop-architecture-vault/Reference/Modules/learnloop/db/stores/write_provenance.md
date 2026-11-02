---
title: "learnloop.db.stores.write_provenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/write_provenance.py"
source_paths:
  - "src/learnloop/db/stores/write_provenance.py"
source_commit: "cbbeee14aab0c7e4dca6a8b44cadc2efd8baa758"
source_commit_timestamp: "2026-10-15T14:02:51-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.write_provenance module"
  - "src/learnloop/db/stores/write_provenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.write_provenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.write_provenance` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Write-time provenance of model-written text (spec_mcp_frontend_c1 §4.8).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py) |
| Source lines | 858 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cbbeee14aab0c7e4dca6a8b44cadc2efd8baa758` |
| Commit timestamp | `2026-10-15T14:02:51-04:00` |

## Public API

- `text_sha256(text: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 93) — The hash a record keeps of the text it covers (exactly as stored).
- `source_ref(ref: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 120) — A source ref as a record keeps it: where its text lies (extraction, spans, locator, revision, source), from a mapping or a vault model.
- `class Inputs` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 145) — What a writer read (see the module doc).
  - `of(cls, *, answers: Mapping[str, Any] | Iterable[tuple[str, Any]]=(), items: Iterable[Any]=(), solution_items: Iterable[Any]=(), topics: Iterable[Any]=(), sources: Iterable[Any]=(), questions: Mapping[str, Any] | Iterable[tuple[str, Any]]=()) -> Inputs` (line 158; public)
  - `union(self, other: Inputs) -> Inputs` (line 191; public)
  - `empty(self) -> bool` (line 209; public)
  - `as_json(self) -> dict[str, Any]` (line 213; public)
  - `from_json(cls, value: Any) -> Inputs` (line 224; public)
- `class WriteRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 239) — A writer's closed record: its inputs, whether it could account for everything it read (``complete``; ``missing`` names what it could not), and the derived texts whose records were folded in (``derived_from``).
  - `incomplete(cls, reason: str, *, inputs: Inputs | None=None) -> WriteRecord` (line 250; public)
  - `join(self, *others: WriteRecord) -> WriteRecord` (line 253; public)
  - `with_inputs(self, inputs: Inputs) -> WriteRecord` (line 264; public)
  - `as_json(self) -> dict[str, Any]` (line 267; public) — A JSON form (a job's progress keeps a record across retries).
  - `from_json(cls, value: Any) -> WriteRecord` (line 274; public)
  - `as_row(self) -> dict[str, Any]` (line 288; public)
- `class StoredRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 298) — A text's provenance as stored: the union of every row written for it, and the hash of the text the LATEST row covers.
- `record_text_write(connection: Any, *, kind: str, record_id: str, text: Any, writer: str, record: WriteRecord, created_at: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 308) — Append one record for one text write, on the writer's own connection (so it commits, or rolls back, with the text).
- `stored_record(connection: Any, kind: str, record_id: str) -> StoredRecord | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 356) — The union of every row written for one text, or None when none was.
- `attempt_items(connection: Any, attempt_ids: Iterable[Any]) -> dict[str, tuple[str | None, str | None]]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 376) — ``{attempt: (practice item, learning object)}`` for the attempts on record.
- `pinned_contract_ids(connection: Any, items: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 391) — ``{attempt: contract version}`` for the attempts (``{attempt: item}``) graded against exactly one assessment contract of their own item: the only affirmative record of the revision an answer was graded against (``learner_protection.pinned_contracts`` reads the same rule).
- `answer_inputs(connection: Any, attempt_ids: Iterable[Any], *, solution: bool=False) -> Inputs` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 422) — The inputs of reading these answers: each answer under its pinned contract (``None`` without one), its item (named whether or not its question was read, so its keys filter the text), its topic, and with ``solution`` the item's rubric and reference solution.
- `grading_inputs(connection: Any, attempt_id: str, *, shown_history: Iterable[Any]=()) -> Inputs` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 472) — What one grading read: the answer under its contract, its item's question, rubric and reference solution, its topic, and the prior answers it was shown (C4).
- `grading_in_progress(attempt_id: str, *, shown_history: Iterable[Any]=()) -> Iterator[None]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 490) — Declare the grading of ``attempt_id`` the caller is writing (with the C4 history its grader was shown) for the length of its transaction.
- `grading_record(connection: Any, attempt_id: str) -> WriteRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 503) — What the grader(s) of ``attempt_id`` read, for a text written from their output: the grading being written now (:func:`grading_in_progress`) and the recorded gradings (every grading since migration 205 records one in its own transaction), else what the grading's own ledger estab…
- `record_grading(connection: Any, *, attempt_id: str, writer: str, shown_history: Iterable[Any]=(), clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 535) — Record one grading of ``attempt_id`` in the grading's own transaction (call it on that transaction's connection, after the grade is written so its contract is pinned).
- `grading_mark(identity: Mapping[str, Iterable[Any]] | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 570) — The identity of one attempt's grading as a reader saw it (``{part: values}``, :data:`_IDENTITY`); no rows at all is the ungraded mark.
- `grading_marks(connection: Any, attempt_ids: Iterable[Any] | None=None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 584) — ``{attempt: grading_mark}`` as they stand now: for ``attempt_ids`` (every one, the ungraded mark when it has no grading), or with None for every attempt that has any grading row.
- `read_snapshot(connection: Any) -> Iterator[Any]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 613) — One read transaction across the block, so every read in it sees one state of the database (codex re-review F3: a grading's payload and its identity are read together).
- `attempt_statement_refs(connection: Any, attempt_id: str, *, diagnosis_id: str | None=None, every_diagnosis: bool=False) -> tuple[Ref, ...]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 635) — Where an attempt's error-event causes were written: its grading, and the diagnosis whose causal view lies over them (``diagnosis_id``), or with ``every_diagnosis`` every completed live diagnosis of the attempt (an unresolved-cause factor's candidate set was drawn from whichever…
- `closure(connection: Any, refs: Iterable[Ref], *, texts: Mapping[Ref, Any] | None=None) -> WriteRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 656) — The joined records of the derived texts in ``refs`` (a writer that read them folds this into its own record).
- `fold_topic_records(connection: Any, record: WriteRecord, *, titles: Mapping[str, Iterable[Any]] | None=None) -> WriteRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 684) — ``record`` with the record of every topic it names that has one of its own folded in (a generated topic: its name was drafted, so a text that read it read what it was drafted from).
- `record_error_event_lineage(connection: Any, *, attempt_id: str, replaced: Iterable[Any], reminted: Iterable[Any], clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 741) — Record what a regrade did to ``attempt_id``'s error events (Q9): every event it retired (one of the attempt's events before the regrade that is gone after it) is replaced by each event it minted, or, when it minted none (codex review F4: the regrade found no error), by nothing:…
- `replaced_error_event_attempts(connection: Any) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 769) — ``{retired error-event id: its attempt}`` for every event a regrade retired, re-minted or not (Q9): a belief listing one still names its answer.
- `retired_error_event_ids(connection: Any, event_ids: Iterable[Any]) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 780) — The listed ids a regrade retired with no replacement: the answer they belonged to has no error now (codex review F4).
- `current_error_event_ids(connection: Any, event_ids: Iterable[Any]) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 796) — ``{listed id: the error events it stands for now}``: an event still on record stands for itself; a replaced one for the events that replaced it, followed through every later regrade (Q9).

### Module constants

- `PROVENANCE_VERSION` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 64)
- `TEXT_KINDS` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 67)
- `GRADING` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 78)
- `KINDS` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 79)
- `NO_RECORD` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 82)
- `TEXT_CHANGED` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 83)
- `GRADING_UNRECORDED` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 84)
- `NAME_UNCOVERED` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 87)
- `_CHUNK` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 90)
- `_COLUMNS` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 342)
- `_PENDING_GRADINGS` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 486)
- `_IDENTITY` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 557)
- `UNIDENTIFIED_GRADING` ([src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 567)

### Explicit exports

`__all__` declares:

- `GRADING`
- `GRADING_UNRECORDED`
- `KINDS`
- `NAME_UNCOVERED`
- `NO_RECORD`
- `PROVENANCE_VERSION`
- `TEXT_CHANGED`
- `TEXT_KINDS`
- `UNIDENTIFIED_GRADING`
- `Inputs`
- `Ref`
- `StoredRecord`
- `WriteRecord`
- `answer_inputs`
- `attempt_items`
- `attempt_statement_refs`
- `closure`
- `current_error_event_ids`
- `fold_topic_records`
- `grading_in_progress`
- `grading_inputs`
- `grading_mark`
- `grading_marks`
- `grading_record`
- `pinned_contract_ids`
- `read_snapshot`
- `record_error_event_lineage`
- `record_grading`
- `record_text_write`
- `replaced_error_event_attempts`
- `retired_error_event_ids`
- `source_ref`
- `stored_record`
- `text_sha256`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 101)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 107)
- `_contracts(values: Iterable[Any]) -> tuple[str | None, ...]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 111)
- `_source_key(ref: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 116)
- `_decode(row: Mapping[str, Any]) -> WriteRecord` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 345)
- `_has_model_grade(connection: Any, attempt_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 442)
- `_c4_history(connection: Any, attempt_id: str) -> list[str] | None` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 454)
- `_columns(connection: Any, table: str) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/write_provenance.py), line 580)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `grading_in_progress`, `record_grading`; statically calls `grading_in_progress`, `record_grading`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `grading_in_progress`, `record_error_event_lineage`, `record_grading`; statically calls `grading_in_progress`, `record_error_event_lineage`, `record_grading`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `read_snapshot`; statically calls `read_snapshot`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `read_snapshot`; statically calls `read_snapshot`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `closure`, `pinned_contract_ids`, `record_text_write`, `stored_record`; statically calls `closure`, `pinned_contract_ids`, `record_text_write`, `stored_record`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `attempt_statement_refs`, `closure`, `fold_topic_records`; statically calls `attempt_statement_refs`, `closure`, `fold_topic_records`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `GRADING`, `closure`; statically calls `closure`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `Inputs`, `WriteRecord`, `attempt_statement_refs`, `closure`, `fold_topic_records`; statically calls `WriteRecord`, `attempt_statement_refs`, `closure`, `fold_topic_records`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `UNIDENTIFIED_GRADING`, `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`; statically calls `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `WriteRecord`, `record_text_write`; statically calls `record_text_write`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `grading_marks`, `read_snapshot`; statically calls `grading_marks`, `read_snapshot`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `GRADING`, `Inputs`, `UNIDENTIFIED_GRADING`, `WriteRecord`, `answer_inputs`, `attempt_statement_refs`, `closure`, `fold_topic_records`, `grading_mark`, `grading_marks`, `read_snapshot`; statically calls `WriteRecord`, `answer_inputs`, `attempt_statement_refs`, `closure`, `fold_topic_records`, `grading_mark`, `grading_marks`, `read_snapshot`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `WriteRecord`, `record_text_write`; statically calls `record_text_write`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `GRADING`, `Inputs`, `WriteRecord`, `answer_inputs`, `closure`, `fold_topic_records`, `source_ref`; statically calls `WriteRecord`, `answer_inputs`, `closure`, `fold_topic_records`, `source_ref`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `Inputs`, `stored_record`; statically calls `Inputs`, `stored_record`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `stored_record`, `text_sha256`; statically calls `stored_record`, `text_sha256`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `pinned_contract_ids`; statically calls `pinned_contract_ids`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] and 12 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_replay_never_reads_the_switch_or_the_records`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_diagnostic_augmentation.py](../../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_a_committed_joint_grade_carries_its_receipt_and_grading_record`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_press_of_the_same_input_never_backfills_the_marked_row_and_builds_afresh`
- [tests/test_learner_data_relax_2.py](../../../../../../../tests/test_learner_data_relax_2.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/write_provenance.py](../../../../../../../src/learnloop/db/stores/write_provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
