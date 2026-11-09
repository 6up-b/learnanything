---
title: "learnloop_sidecar.handlers.workbench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/workbench.py"
source_paths:
  - "src/learnloop_sidecar/handlers/workbench.py"
source_commit: "workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.workbench module"
  - "src/learnloop_sidecar/handlers/workbench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.workbench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.workbench` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW2a RPCs: the resumable scratchpad (spec_reader_workbench_v1 §5.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py) |
| Source lines | 1402 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a` |
| Commit timestamp | `2026-11-09T16:01:49-05:00` |

## Public API

- `record_line(vault, repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 107) — A problem's record line and save time, with no statement (a step's save, the help ladder's record): not a statement-bearing response, so a problem whose region was held out since keeps saving its steps.
- `class WorkbenchSourceExerciseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 418)
- `class WorkbenchExercisePickInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 427) — A fallback exercise the learner picked (Reader RW4b): the ``pick`` its listing returned, sent back as it came.
- `class WorkbenchOpenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 435)
- `class WorkbenchSessionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 482)
- `class WorkbenchSaveStepInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 486)
- `class WorkbenchSetBookInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 496)
- `class WorkbenchBindInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 501)
- `class WorkbenchSubmitInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 506)
- `class WorkbenchAdmitInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 518)
- `class WorkbenchAttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 524)
- `class WorkbenchItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 528)
- `class WorkbenchSourceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 532)
- `class WorkbenchOpenProblemsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 536) — No parameters: every source's open problems.
- `workbench_open(ctx: SidecarContext, params: WorkbenchOpenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 576) — Open a problem at once (or resume the open one for the same item or selection).
- `class ReaderImportSelection(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 816) — The two fields of a fallback's ``reader.import_exercise`` request the workbench reads (the request is otherwise passed on unchanged).
- `workbench_get(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 844)
- `workbench_save_step(ctx: SidecarContext, params: WorkbenchSaveStepInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 850) — One change to the work, saved as it is typed (idempotent by key).
- `workbench_set_book(ctx: SidecarContext, params: WorkbenchSetBookInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 864)
- `workbench_leave(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 872)
- `workbench_abandon(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 911)
- `workbench_reopen(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 918)
- `workbench_refresh_import(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 925) — Bind the problem when its import has landed: one item binds; several ask which part (``parts``); none, or a failed job, is ``failed`` with the steps kept and "try again".
- `workbench_bind(ctx: SidecarContext, params: WorkbenchBindInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 960) — Bind a multi-part import to the part the learner picked (one of its own).
- `workbench_retry_import(ctx: SidecarContext, params: WorkbenchSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 977) — "Try again" on a failed setup: the same request, enqueued again.
- `admission_key(session_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1138) — The learner pick's durable idempotency identity for a picked exercise's admission (fix round 5, R1): derived from the workbench session id, kept with the pick's plan receipt, so a retried admission finds its pick.
- `workbench_admit(ctx: SidecarContext, params: WorkbenchAdmitInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1147) — Make a picked exercise's owed learner pick, for the problem named (Reader RW4b fix round 4, R1): see ``_admit``.
- `workbench_submit(ctx: SidecarContext, params: WorkbenchSubmitInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1162) — Submit the work through the ordinary attempt path (spec §5.4).
- `workbench_session_for_attempt(ctx: SidecarContext, params: WorkbenchAttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1336) — The submitted problem behind an attempt, for back-from-feedback (UX S6); ``null`` for every attempt the workbench did not write.
- `workbench_for_item(ctx: SidecarContext, params: WorkbenchItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1346) — The item's open or abandoned problems ("resume your steps" on its card).
- `workbench_for_source(ctx: SidecarContext, params: WorkbenchSourceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1356) — The source's open or abandoned problems: the ``✎`` marks, the rail and RW6a's recap (``unfinished`` past ``workbench.open_session_days``).
- `workbench_open_problems(ctx: SidecarContext, params: WorkbenchOpenProblemsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1368) — UX Phase 3 (spec ux_learnloop_v1 §7.1, §10 3.3): Today's unfinished problems ("Exercise 5.9 -- 3 steps written · resume"), newest first, each with the source it opens in.

### Module constants

- `T` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 41)
- `EXERCISE_ADMISSION_RPCS` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 45)
- `_IMPORT_RUNNING` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 48)
- `SOURCE_EXERCISE_KIND` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 326)
- `_DRAFT_HANDOFF_ORIGINS` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 667)
- `EXERCISE_WITHHELD` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 778)
- `EXERCISE_WITHHELD_MESSAGE` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 779)
- `ADMISSION_PENDING` ([src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1036)

## Internal implementation anchors

- `_require(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 51)
- `_run(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 58)
- `_question_hints(vault, repository, session: dict[str, Any]) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 65) — The tutor questions the submit's existing fold will add (G62).
- `_earlier_hints(vault, repository, session: dict[str, Any]) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 85) — Reader CA2 (Codex review F1; orchestrator fix F1/F15): the earlier attempt's opened help the submit's server side will add, its own component in the record line: carried onto an open problem of the item (``earlier_opened_at``), or still on the answer box's draft.
- `_source_id(repository, extraction_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 119)
- `_current_reading(repository, source_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 130) — The reading the Reader opens a source on (its latest completed extraction, as ``reader.render_view`` resolves a source id).
- `_ensure_contract(vault, repository, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 142) — Snapshot the assessment contract a bound session shows, once (the practice screen's serve does the same), so the submit grades the problem against what the learner saw even if the item changes before it.
- `_presentation(vault, repository, row: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 169) — The bound problem as the learner must see it to answer it: the item's presentation blocks (a required method's instruction, a shared stimulus, an error hunt's worked solution), with the statement and required method the session's contract froze.
- `_source_exercise_view(vault, repository, row: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 207) — A textbook exercise picked from a proposal (Reader RW4b): its import and the answer key's honest status (the sources service's effective status of the item as written, so a later check or an edit shows).
- `_view(vault, repository, session_id: str, *, parts: list[dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 247) — THE one builder of every workbench response that carries a problem's statement (Reader RW4b fix round 5, R2): a picked textbook exercise's statement is revalidated through the one statement reader here, before anything of it is built, and a withheld one refuses (``exercise_withh…
- `_carried_server_hints(repository, session: dict[str, Any]) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 283) — The answer box's shown server hints the problem's submit will fold (H2b fix round 3, ruling R1), every level: what the record line names before Submit.
- `_answer(payload: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 316)
- `_is_source_exercise(request: dict[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 329)
- `_enqueue_import(ctx: SidecarContext, vault, repository, request: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 333) — Queue the exercise import exactly as ``reader.import_exercise`` does, or, for a picked textbook exercise proposal, exactly as ``import_source_exercise`` does (the same helper: the import row, the pick's usage verdict, the job).
- `_import_job(ctx: SidecarContext, repository, batch_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 368) — The import batch's job, reloading the vault once when it completed (as ``reader.exercise_import_status`` does), so its items schedule.
- `_job_parts(job: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 387)
- `_job_error(job: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 401)
- `_start_import(ctx: SidecarContext, vault, repository, request: dict[str, Any]) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 408)
- `_require_open_identity(repository: Any, params: WorkbenchOpenInput) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 543) — Reader CA6b fix round 5: a problem's passages are the reading it opens on, its import request is that reading's own selection (source, revision, reading and nodes agree), and a source exercise's passages are its reading's.
- `_draft_earlier(repository, params: WorkbenchOpenInput, practice_item_id: str | None) -> tuple[str | None, int]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 670) — Codex re-review F1: ``(practice session, 1)`` when the practice screen's draft of the item, handed to the steps now, opened an earlier attempt's help under its current key (``sessions.draft_earlier_opened``), else ``(None, 0)``.
- `_handed_draft_keys(repository, params: WorkbenchOpenInput, practice_item_id: str | None) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 700) — Astra batch review (Medium): the answer box's draft keys an open from the practice screen or the plan hands to the steps: the key the screen names, and the key of the draft its practice session holds on the item (the one the screen names while open, else the most recent open one…
- `_carry_earlier(repository, draft_session: str | None, earlier: int, row: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 730) — Record on the draft that its opening now lives on the problem (its own component, ``earlier_opened_at``: never the authored reveals' ``carried_hints``, orchestrator fix F15), so the checkpoint never counts it again.
- `_picked_exercise(vault, repository, params: WorkbenchOpenInput, request: dict[str, Any], stem: str) -> tuple[str, str, dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 749) — What a textbook exercise the learner picked opens as (Reader RW4b), decided here rather than by the card that offered it: its complete statement, read through the one statement reader (fix round 4, R4: an exercise held out since its card was shown is refused before anything of i…
- `_exercise_region(params: WorkbenchOpenInput, request: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 782) — The picked exercise's extraction, spans and the pick's record to keep.
- `_selection_spans(raw_selection: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 796)
- `_picked_region(request: dict[str, Any] | None) -> tuple[str, list[str]] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 802) — A picked exercise's region from an import request (None for every other problem).
- `_refuse_withheld_exercise(vault, repository, row: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 808) — A picked exercise's statement is built only while its region may be shown (fix rounds 4 and 5): every status, a submitted problem's too.
- `_named_serve(params: ParamsModel) -> dict[str, str | None] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 826) — The serve a request names, as one pair (review F15): ``None`` when it names neither identifier (keep the pair the session holds), else both, an explicit null included (replace the pair).
- `_key_exists(repository, key: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 836)
- `_queue_stuck_texts(ctx: SidecarContext, vault, repository, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 879) — RW2b in-session updates (§5.2): a stuck step's newest text goes to learner-text gaps when Leave or Submit sends it.
- `_schedule_map(ctx: SidecarContext, vault, repository, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 894) — RW2b (§5.2): the bound item's approach map is built in the background (H1's ``build_on_serve``, its switches, locks and envelope).
- `_kept_offer(repository, candidate_id: str | None, practice_session_id: str, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 995) — The scheduler offer kept on the session, when it is still an unanswered offer of this item in the session the submit runs in; a stale one (answered elsewhere, another session after a restart) is dropped, so the attribution it carried never fails the submit (review F13).
- `_session_open(repository, practice_session_id: str | None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1009)
- `_practice_session(ctx: SidecarContext, repository, requested: str | None) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1016) — The practice session a workbench submit runs in: the app's open one, else the most recent open one, else a new one (``start_session``).
- `_admit(ctx: SidecarContext, session_id: str, requested_practice_session: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1039) — Admit a picked exercise's item as the learner's pick, for THIS problem (Reader RW4b fix round 4, R1).
- `_close_answer_box_draft(repository, practice_session_id: str, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1278) — Owner capture 2026-10-25 (B3, B4): the steps answered the item, so the practice screen's draft of it in this session (the answer box the learner left for steps: its retry key, its hints, its offer binding) is superseded, as an answer-box submit acknowledges its own.
- `_stamp_help_rows(repository, session_id: str, latency_seconds: int | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1297)
- `_bind_help_rows(repository, session_id: str, plan, *, attempt_id: str, practice_session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1314) — RW2b: the practice session (set at Submit, the schema's rule) and the attempt on the problem's help rows, after the attempt committed.
- `_cleared(vault, repository, summaries: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench.py), line 1396) — A list's problems whose statement may be shown (fix round 5, R2): a picked exercise whose region is held out now is left out of the list (its steps are kept; it cannot be resumed while it is withheld).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `_practice_session`; statically calls `_practice_session`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `_refuse_withheld_exercise`, `_run`, `record_line`; statically calls `_refuse_withheld_exercise`, `_run`, `record_line`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `_refuse_withheld_exercise`; statically calls `_refuse_withheld_exercise`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_batch_offer`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`; calls `stuck_attempt_type`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `bind_workbench_rows`, `fold_row_count`, `keyless_window_start`, `stamp_submitted`; calls `bind_workbench_rows`, `fold_row_count`, `keyless_window_start`, `stamp_submitted`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `import_row`; calls `effective_key_status`, `import_row`
- [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] — imports `module`; calls `session_by_key`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; calls `schedule_map`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `snapshot_for_presentation`; calls `snapshot_for_presentation`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/reader/source_identity|learnloop.reader.source_identity]] — imports `MISMATCH_CODE`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `earlier_hints`, `exercise_pick`, `exercise_pick_due`, `exercise_request_region`, `import_request`, `open_problems`, `open_session_days`, `resumable_session`, `session_for_attempt`, `sessions_for_item`, `sessions_for_source`, `statement_cleared`, `submission_id_for`, `workbench_enabled`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; calls `fields`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `hint_equivalents_for_submission`; calls `hint_equivalents_for_submission`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `method_instruction`; calls `method_instruction`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; calls `help_enabled`, `queue_stuck_texts`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `session_snapshot`; calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`; calls `to_camel`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `PlanLearnerPickInput`, `plan_learner_pick`; calls `PlanLearnerPickInput`, `plan_learner_pick`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `module`; calls `pick_entry`, `pick_exposure`, `read_exercise_statement`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ServePracticeItemInput`, `SubmitAttemptInput`, `_cached_submission`, `_earlier_opened_hint`, `get_practice_item`, `submit_attempt_on`; calls `ServePracticeItemInput`, `SubmitAttemptInput`, `_cached_submission`, `_earlier_opened_hint`, `get_practice_item`, `submit_attempt_on`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `ReaderImportExerciseInput`, `_source_id_for_extraction`, `enqueue_exercise_import`; calls `_source_id_for_extraction`, `enqueue_exercise_import`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `item_presentation`; calls `item_presentation`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SessionStartInput`, `carry_earlier_opened`, `draft_earlier_opened`, `start_session`; calls `SessionStartInput`, `carry_earlier_opened`, `draft_earlier_opened`, `start_session`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `queue_source_exercise_import`; calls `queue_source_exercise_import`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `require_identity`; calls `require_identity`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_h2b_fix3.py](../../../../../../tests/test_hint_h2b_fix3.py) — direct import
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f1_the_open_request_names_no_submission`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw4b_rpcs_are_all_of_them`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_hint_asked_before_any_practice_session_counts_once`
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
  - `test_r1_a_lost_pick_record_is_found_by_its_key_in_the_plans_receipt`
  - `test_r1_a_lost_serve_record_repeats_no_pick_and_no_presentation`
  - `test_r1_a_retry_after_a_locked_final_write_makes_no_second_pick`
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f13_the_admissions_serve_and_its_served_record_share_one_transaction`
  - `test_f2_verify_sequence_planned_pick_locked_picked_write_retry_under_a_later_plan`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_an_import_that_cannot_start_opens_the_session_failed_with_the_steps_writable`
- [tests/test_ux_phase3_today.py](../../../../../../tests/test_ux_phase3_today.py) — direct import
  - `test_the_current_reading_is_the_one_the_reader_opens_a_source_on`
- [tests/test_workbench_assistance.py](../../../../../../tests/test_workbench_assistance.py) — direct import
  - `test_a_row_is_never_shown_once_its_submission_is_admitted`
- [tests/test_workbench_check.py](../../../../../../tests/test_workbench_check.py) — direct import
  - `test_check_and_help_wait_for_setup_and_refuse_while_switched_off`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/workbench.py](../../../../../../src/learnloop_sidecar/handlers/workbench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
