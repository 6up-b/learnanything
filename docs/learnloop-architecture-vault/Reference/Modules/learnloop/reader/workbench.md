---
title: "learnloop.reader.workbench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/workbench.py"
source_paths:
  - "src/learnloop/reader/workbench.py"
source_commit: "2079aa1eb02ced81c4ed4449672db9e2e437e45b"
source_commit_timestamp: "2026-11-04T16:51:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.workbench module"
  - "src/learnloop/reader/workbench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.workbench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.workbench` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1 §5.1, §5.4, §5.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py) |
| Source lines | 1617 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2079aa1eb02ced81c4ed4449672db9e2e437e45b` |
| Commit timestamp | `2026-11-04T16:51:26-05:00` |

## Public API

- `class WorkbenchError(ValueError)` ([source](../../../../../../src/learnloop/reader/workbench.py), line 110) — A refused workbench request (nothing was written).
  - `__init__(self, code: str, message: str, details: Mapping[str, Any] | None=None) -> None` (line 113; internal)
- `workbench_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 124) — RW2a's kill switch (``workbench.enabled``, default on).
- `open_session_days(vault: Any) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 131)
- `default_book_visible(entry: str, origin: str) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 140) — Whether a new session starts with the book shown (UX S7, D9).
- `class ComposedAnswer` ([source](../../../../../../src/learnloop/reader/workbench.py), line 147) — What a submit sends: the ordinary steps in order, or "I'm stuck".
  - `empty_stuck(self) -> bool` (line 154; public)
- `live_steps(rows: Sequence[Mapping[str, Any]], *, include_deleted: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 199) — The work as it stands: each step's newest version, in list order.
- `compose_answer(steps: Iterable[Mapping[str, Any]]) -> ComposedAnswer` ([source](../../../../../../src/learnloop/reader/workbench.py), line 208) — The answer a submit sends (spec §5.1): the live ``step`` bodies in order, stuck steps and tombstones left out.
- `book_counted(session: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 222) — Whether the book counts as one hint-equivalent on the submitted attempt.
- `book_hints(session: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 234)
- `carried_hints(session: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 238) — The answer box's authored hints the learner revealed before working in steps: the answer box's reveal index on the way back, so nothing else is ever added to it (orchestrator fix F15).
- `earlier_opened(session: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 246) — Whether the answer box's draft carried an earlier attempt's opened help onto this problem (migration 221; Reader CA2 §7.3, Q2): its own component, one hint-equivalent like the book, never an authored reveal.
- `earlier_hints(session: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 254)
- `session_hints(session: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 258) — Every hint-equivalent the session itself holds (the submit's ``hints_used``).
- `record_line(*, counted: bool, visible: bool, question_hints: int, composed: ComposedAnswer, carried: int=0, help_fold: WorkbenchFold | None=None, earlier: int=0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 279) — What the attempt will record, stated before Submit (spec §5.1, G62).
- `session_row(repository: Any, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 398)
- `resumable_session(repository: Any, *, practice_item_id: str | None=None, extraction_id: str | None=None, span_ids: Sequence[str]=(), stem_md: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 403) — The open session an "open" would resume: the item's, else the same selection's (so a second "work through this" never starts a second one).
- `held_parts_on(connection: Any, practice_item_id: str) -> tuple[tuple[tuple[int, int, tuple[str, ...]], ...], bool]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 486) — The help each of the item's open problems holds, read on ``connection`` (a submit's own write transaction may pass its connection: RW2b fix round 1, F1), kept in its parts (fix round 5, items 4-5): ``(book, carried, assist_ids)``, where ``book`` is 1 when the problem counted the…
- `held_on(connection: Any, practice_item_id: str) -> tuple[int, bool]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 512) — The help the item's open problems hold (:func:`held_parts_on`): the largest hint-equivalents one problem holds (its book, carried hints, shown checks and level 1-3 hints) and whether any showed worked help.
- `held_hints(repository: Any, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop/reader/workbench.py), line 521) — The hint-equivalents the item's open problems hold (review F2): the book one counted and the answer-box hints it carried.
- `held_earlier(repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 532) — Whether an open problem of the item carries an earlier attempt's opened help (:func:`earlier_opened`): every submit for the item counts it once, as it counts a book an open problem counted.
- `held_primed(repository: Any, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 544) — Whether an open problem of the item showed worked help (a level 4-5 hint): every submit for the item is then primed (RW2b, §5.4).
- `open_session(repository: Any, *, origin: str, entry: str, stem_md: str, practice_item_id: str | None=None, extraction_id: str | None=None, span_ids: Sequence[str]=(), parent_session_id: str | None=None, source_visible: bool | None=None, client_idempotency_key: str | None=None, import_status: str='none', import_batch_id: str | None=None, import_request: Mapping[str, Any] | None=None, import_error: str | None=None, carried: int=0, carried_book: bool=False, serve: Mapping[str, str | None] | None=None, clock: Clock | None=None, carried_earlier: bool=False, draft_submission_ids: Iterable[str]=(), exposure_fields: Mapping[str, Any] | None=None) -> tuple[dict[str, Any], bool]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 628) — Open a session (or resume the open one for the same item or selection).
- `resume_session(repository: Any, session_id: str, *, origin: str, entry: str='resume', extraction_id: str | None=None, span_ids: Sequence[str]=(), carried: int=0, carried_book: bool=False, serve: Mapping[str, str | None] | None=None, clock: Clock | None=None, carried_earlier: bool=False, draft_submission_ids: Iterable[str]=(), exposure_fields: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 742) — Resume a named session on the surface asking ("resume your steps", the ``✎`` mark, the rail): an abandoned one is reopened, and a move to another surface is the same explicit transition :func:`open_session` makes.
- `record_draft_handoff(repository: Any, session_id: str, submission_ids: Iterable[str], clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 789) — Astra batch review (Medium): the practice screen handed its answer box's draft (keyed by ``submission_ids``, the draft's retry keys) into this unfinished problem.
- `attempt_identities(repository: Any, *, practice_item_id: str | None, submission_id: str | None, workbench_session_id: str | None) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 827) — Every identity of the one attempt in progress that ``submission_id`` and ``workbench_session_id`` name: ``(submission ids, workbench ids)`` (Astra batch review, Medium; ``tutor_qa.AttemptAliases`` carries them).
- `save_step(repository: Any, session_id: str, *, op: str, client_idempotency_key: str, step_id: str | None=None, after_step_id: str | None=None, kind: str='step', body_md: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 871) — Save one change to the work, as typed (spec §5.1).
- `set_book(repository: Any, session_id: str, visible: bool, *, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 950) — Show or hide the book (``Ctrl+Shift+B``).
- `leave(repository: Any, session_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 979) — "Leave for now" (``Esc`` twice, navigating away, a restart): the session stays open.
- `abandon(repository: Any, session_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 990) — Close the problem at once, steps kept; reversible by :func:`reopen` (UX S13).
- `reopen(repository: Any, session_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1006) — An abandoned session back to ``open`` (it never wrote an attempt).
- `import_request(session: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1025)
- `exercise_pick(session: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1050) — The picked exercise's record, or None for every other problem.
- `exercise_pick_due(session: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1057) — The import bound the problem to the item it wrote and the learner pick of that item was not delivered yet: the shell owes it, once.
- `exercise_region(session: Mapping[str, Any]) -> tuple[str, list[str]] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1073) — A picked textbook exercise's region (its extraction and spans), from its stored request; None for every other problem.
- `exercise_request_region(request: Mapping[str, Any] | None) -> tuple[str, list[str]] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1080) — The same, from an import request (a stored one, or one about to be queued).
- `statement_cleared(vault: Any, repository: Any, session: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1092) — Whether a problem's statement may be shown now (Reader RW4b fix round 5, R2): every problem but a picked textbook exercise, and a picked one only while the one statement reader still reads its region (not exam or held-out material now, the predicate readable).
- `record_admission_stage(repository: Any, session_id: str, stage: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1105) — Keep a step of a picked exercise's admission on the problem (fix round 5, R1): ``picked`` (the learner pick made, with its serve and practice session) and ``served``.
- `admit_exercise_pick(repository: Any, session_id: str, *, practice_item_id: str, exposure: Mapping[str, Any] | None, serve: Mapping[str, str | None] | None=None, practice_session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1124) — Record that the learner pick of the exercise's item was made and served for THIS problem, in one transaction (RW4b fix round 4, R1): the pick's serve (its scheduler offer and plan presentation) stored on this problem, the practice session it was made in, the exposure read again…
- `mark_import(repository: Any, session_id: str, *, status: str, batch_id: str | None=None, error: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1164) — Record the import's progress: ``pending`` on a batch, or ``failed``.
- `ensure_contract(repository: Any, session_id: str, version_id: str | None, *, subject_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1195) — Record the assessment contract the session shows, once: a resumed problem keeps the contract it was opened (or bound) with.
- `bind(repository: Any, session_id: str, practice_item_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1216) — Bind the session to the item its import made (UX S2).
- `class SubmissionPlan` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1242) — What a workbench submit sends through the ordinary attempt path.
  - `hints_used(self) -> int` (line 1265; public) — The session's hint-equivalents: the book's, the carried hints, an earlier attempt's opened help, and each shown check and level 1-3 hint (§5.4).
  - `client_hints(self) -> int` (line 1273; public) — What the submit sends as the client's count: the session's RW2a counts only (the book's, the carried hints).
  - `primed(self) -> bool` (line 1282; public) — Worked help (a shown level 4-5 hint) primes the attempt (§5.4).
  - `submission_id(self) -> str` (line 1288; public)
- `submission_id_for(session_id: str) -> str` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1292) — One submit per session, so the session names its retry key: a response lost after the commit is answered from the receipt.
- `submission_plan(repository: Any, session_id: str) -> SubmissionPlan` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1299)
- `help_fold(repository: Any, session_id: str) -> WorkbenchFold` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1326) — The problem's shown checks and hints (the record line's count).
- `set_help_style(repository: Any, session_id: str, help_style: str | None, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1335) — The workbench header's help style for this problem (D31): one of the three styles, or None to follow the stored preference again.
- `log_help_offered(repository: Any, session_id: str, *, about_step_id: str | None, offered_level: int, kind: str, chooser: str, suggestion_id: str | None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1356) — The rung the ladder suggested when Help opened (§5.5): the Reader's fallback progression reads it ("one rung above the last offered").
- `mark_submitted(repository: Any, session_id: str, *, attempt_id: str, practice_session_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1367)
- `session_view(repository: Any, session_id: str, *, question_hints: int=0, server_hints: int=0, earlier: int | None=None, extra: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1394) — Everything the workbench shows for one session (snake_case; the adapter camel-cases it).
- `session_for_attempt(repository: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1508)
- `sessions_for_item(repository: Any, practice_item_id: str, *, now: datetime | None=None, open_days: int=30) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1520) — The item's practice card: "resume your steps" (open) or "reopen" (abandoned).
- `sessions_for_source(repository: Any, extraction_id: str, *, now: datetime | None=None, open_days: int=30) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1527) — The problems worked on a source and not submitted: the ``✎`` marks, the rail, and RW6a's recap (open sessions past ``open_days`` are ``unfinished``, shown without alarm and never closed).
- `open_problems(repository: Any, *, now: datetime | None=None, open_days: int=30) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1536) — UX Phase 3 (spec ux_learnloop_v1 §7.1, §10 3.3): the open problems on every source, newest first, for Today's "Pick up a thread".

### Module constants

- `WORKBENCH_VERSION` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 65)
- `ORIGINS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 67)
- `ENTRIES` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 69)
- `STATUSES` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 73)
- `IMPORT_STATUSES` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 74)
- `STEP_KINDS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 75)
- `HELP_STYLES` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 76)
- `STEP_OPS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 77)
- `BOOK_OPEN_ENTRIES` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 83)
- `ENTRY_SURFACE_READER` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 86)
- `ENTRY_SURFACE_PRACTICE` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 87)
- `SERVER_WORKBENCH_EVENTS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 90)
- `HELP_WORKBENCH_EVENTS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 97)
- `SUBJECT_TYPE` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 98)
- `DRAFT_HANDOFF_EVENT` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 100)
- `STUCK_NOTE` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 103)
- `OWN_ATTEMPT_LINE` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 104)
- `MAX_STEM_CHARS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 106)
- `MAX_STEP_CHARS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 107)
- `SERVE_COLUMNS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 468)
- `EXERCISE_PICK_KEY` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 1045)
- `EXERCISE_WORKBENCH_EVENTS` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 1047)
- `SOURCE_EXERCISE_KIND` ([src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py), line 1070)

### Explicit exports

`__all__` declares:

- `BOOK_OPEN_ENTRIES`
- `ComposedAnswer`
- `ENTRIES`
- `ENTRY_SURFACE_PRACTICE`
- `ENTRY_SURFACE_READER`
- `EXERCISE_PICK_KEY`
- `EXERCISE_WORKBENCH_EVENTS`
- `HELP_STYLES`
- `HELP_WORKBENCH_EVENTS`
- `IMPORT_STATUSES`
- `ORIGINS`
- `SERVER_WORKBENCH_EVENTS`
- `DRAFT_HANDOFF_EVENT`
- `record_draft_handoff`
- `attempt_identities`
- `STATUSES`
- `STEP_KINDS`
- `STEP_OPS`
- `STUCK_NOTE`
- `SubmissionPlan`
- `WorkbenchError`
- `abandon`
- `open_problems`
- `SOURCE_EXERCISE_KIND`
- `admit_exercise_pick`
- `exercise_region`
- `exercise_request_region`
- `record_admission_stage`
- `statement_cleared`
- `bind`
- `book_counted`
- `book_hints`
- `carried_hints`
- `compose_answer`
- `earlier_hints`
- `earlier_opened`
- `default_book_visible`
- `ensure_contract`
- `exercise_pick`
- `exercise_pick_due`
- `held_earlier`
- `held_hints`
- `held_on`
- `held_parts_on`
- `held_primed`
- `help_fold`
- `import_request`
- `log_help_offered`
- `leave`
- `live_steps`
- `mark_import`
- `mark_submitted`
- `open_session`
- `open_session_days`
- `record_line`
- `reopen`
- `resumable_session`
- `resume_session`
- `save_step`
- `session_for_attempt`
- `session_hints`
- `session_row`
- `session_view`
- `sessions_for_item`
- `sessions_for_source`
- `set_book`
- `set_help_style`
- `submission_id_for`
- `submission_plan`
- `workbench_enabled`

## Internal implementation anchors

- `_chains(rows: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 158) — Each step's versions, oldest first (rows are append-only, linear chains).
- `_step_payload(chain: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 176)
- `_help_parts(fold: WorkbenchFold) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 264) — The workbench's own assists in plain words (UX §5.5, §5.9; G62).
- `_spans(session: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 351)
- `_log(repository: Any, session: Mapping[str, Any], event: str, clock: Clock | None=None, **extra: Any) -> str` ([source](../../../../../../src/learnloop/reader/workbench.py), line 359)
- `_require(connection: Any, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 382)
- `_require_open(session: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/reader/workbench.py), line 389)
- `_record_book_exposure(repository: Any, session: Mapping[str, Any], clock: Clock | None=None, *, exposure_fields: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 425) — The book shown beside the problem exposes its anchored spans (spec §5.4, G10): one ``source_exposure_events`` row per span, context ``reader``, as opening the source records today.
- `_serve_changes(serve: Mapping[str, str | None] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 471) — The serve a request names, to store on the session (review F13, F15).
- `_resume_existing(repository: Any, connection: Any, existing: Mapping[str, Any], *, origin: str, entry: str, extraction_id: str | None, span_ids: Sequence[str], source_visible: bool | None, carried: int, now: str, clock: Clock | None, carried_book: bool=False, serve: Mapping[str, str | None] | None=None, carried_earlier: bool=False, exposure_fields: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 552) — Resume an existing session on the surface asking for it.
- `_draft_keys(submission_ids: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 806)
- `_handed(repository: Any, connection: Any, session: Mapping[str, Any], submission_ids: Iterable[str], clock: Clock | None) -> list[str]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 811) — Record the draft keys handed into ``session`` inside the caller's transaction (:func:`record_draft_handoff`); a failure fails it whole.
- `_ordinal_after(live: Sequence[Mapping[str, Any]], after: Mapping[str, Any] | None) -> float` ([source](../../../../../../src/learnloop/reader/workbench.py), line 862)
- `_print_region(session: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1465) — Reader CA1 (§12.4): the learner-drawn sub-box a problem opened from a region selection was imported with, so its crop is the learner's before the import binds it; present only when there is one.
- `_summary(session: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], *, now: datetime | None, open_days: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1482)
- `_listed(repository: Any, *, column: str, value: str, now: datetime | None, open_days: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/workbench.py), line 1513)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; statically calls `book_counted`, `carried_hints`, `open_session_days`, `session_hints`, `session_row`, `sessions_for_source`, `statement_cleared`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `live_steps`; statically calls `live_steps`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `module`; statically calls `live_steps`, `statement_cleared`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; statically calls `live_steps`, `workbench_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `attempt_identities`, `session_row`, `submission_id_for`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `session_row`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `held_earlier`, `held_parts_on`; statically calls `held_earlier`, `held_parts_on`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `module`; statically calls `session_row`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `module`; statically calls `attempt_identities`, `session_row`, `submission_id_for`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `earlier_hints`, `exercise_pick`, `exercise_pick_due`, `exercise_request_region`, `import_request`, `open_problems`, `open_session_days`, `resumable_session`, `session_for_attempt`, `sessions_for_item`, `sessions_for_source`, `statement_cleared`, `submission_id_for`, `workbench_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; statically calls `log_help_offered`, `session_row`, `set_help_style`, `submission_id_for`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `session_row`, `submission_id_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `read_exercise_statement`; calls `read_exercise_statement`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `WorkbenchFold`, `module`; calls `WorkbenchFold`, `workbench_assist_ids`, `workbench_fold`
- [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] — imports `module`; calls `fetch_session`, `handed_submission_ids`, `insert_session`, `insert_step`, `open_session_for_item`, `open_session_for_selection`, `open_sessions`, `session_by_key`, `session_for_attempt`, `session_ids_for_item`, `sessions_where`, `step_by_key`, `steps_for_session`, `steps_for_sessions`, `update_session`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]], [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]], [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — direct import
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_rereview_f3_the_sidecar_records_the_subject_with_the_contract`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_problem_opened_on_another_item_leaves_the_attempt_reached`
  - `test_rebinding_an_imported_problem_to_another_item_never_flips_the_attempt`
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_the_workbench_session_carries_the_region_it_was_imported_with`
- [tests/test_reader_ca2_astra_handoff.py](../../../../../../tests/test_reader_ca2_astra_handoff.py) — direct import
  - `test_a_new_attempt_still_gets_a_fresh_allowance`
  - `test_a_reader_open_hands_no_draft`
  - `test_raw_question_rows_keep_the_key_they_were_asked_under`
  - `test_the_budget_spent_in_the_answer_box_stays_spent_in_the_reader`
  - `test_the_draft_key_is_read_from_the_checkpoint_when_the_screen_names_none`
  - `test_the_handoff_is_recorded_once_and_salience_only`
  - `test_the_production_counting_functions_read_one_attempt_across_the_handoff`
- [tests/test_reader_ca2_astra_handoff_recovery.py](../../../../../../tests/test_reader_ca2_astra_handoff_recovery.py) — direct import
  - `test_a_failed_handoff_write_fails_the_open_and_exposes_no_problem`
  - `test_a_resume_that_cannot_record_its_handoff_leaves_the_problem_as_it_was`
  - `test_after_a_restart_the_reader_still_reads_the_answer_box_s_questions`
- [tests/test_reader_ca2_fix_orchestrator.py](../../../../../../tests/test_reader_ca2_fix_orchestrator.py) — direct import
  - `test_f16_the_session_view_reads_the_problems_own_opening_by_default`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
- [tests/test_reader_recap.py](../../../../../../tests/test_reader_recap.py) — direct import
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
  - `test_f8_an_abandoned_problem_is_in_the_recap_with_a_reopen`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_hint_asked_before_any_practice_session_counts_once`
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
  - `test_r1_a_lost_pick_record_is_found_by_its_key_in_the_plans_receipt`
  - `test_r1_a_lost_serve_record_repeats_no_pick_and_no_presentation`
  - `test_r1_a_retry_after_a_locked_final_write_makes_no_second_pick`
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f13_the_admissions_serve_and_its_served_record_share_one_transaction`
  - `test_f2_verify_sequence_planned_pick_locked_picked_write_retry_under_a_later_plan`
  - `test_f7_a_finished_help_job_on_a_problem_held_out_since_is_never_delivered`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_an_open_session_past_open_session_days_is_unfinished_and_never_closed`
  - `test_every_workbench_event_is_salience_only`
  - `test_migration_207_creates_both_tables_with_every_check_value`
  - `test_the_default_book_visibility_follows_the_entry`
  - `test_the_kill_switch_and_open_session_days_default_on_and_30`
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_l6_the_compare_rpcs_refuse_a_problem_whose_exercise_is_withheld_now`
- [tests/test_workbench_hint_service.py](../../../../../../tests/test_workbench_hint_service.py) — direct import
  - `test_every_workbench_hint_comes_from_request_hint_and_the_suggestion_from_the_service`
  - `test_help_events_are_salience_only`

## Modification guidance

- Change workbench policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/workbench.py](../../../../../../src/learnloop/reader/workbench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
