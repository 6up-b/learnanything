---
title: "learnloop_sidecar.handlers.library_ask"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/library_ask.py"
source_paths:
  - "src/learnloop_sidecar/handlers/library_ask.py"
source_commit: "e54b064acd0205356eaa04ad3ec5d33dd420b9d4"
source_commit_timestamp: "2026-11-01T08:29:36-05:00"
source_worktree_state: "clean"
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
  - "learnloop_sidecar.handlers.library_ask module"
  - "src/learnloop_sidecar/handlers/library_ask.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.library_ask`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.library_ask` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW4a RPCs: ask your library, its notes, compare and the tutor.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py) |
| Source lines | 822 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e54b064acd0205356eaa04ad3ec5d33dd420b9d4` |
| Commit timestamp | `2026-11-01T08:29:36-05:00` |

## Public API

- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 64) — What the Reader's prompt contract adds for RW4a (absent while off).
- `reader_caller(vault: Any, repository: Any, *, extraction_id: str | None, workbench_session_id: str | None=None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 93) — The Reader's caller context, built on the server (spec §7.2, G19).
- `follow_up_caller(vault: Any, repository: Any, row: dict[str, Any], *, workbench_session_id: str | None=None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 118) — A follow-up's caller: the ask's own stored binding (its item, when it was asked inside a bound workbench session), rebuilt on the server so the cold status is today's.
- `fenced(job: _Job, write: Callable[[], Any]) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 204) — Run ``write`` (a job's binding of its result to its ask) unless the job is cancelled; False when it was.
- `class LibraryJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 217) — Library jobs in flight and just finished, kept for reading back (in memory).
  - `__init__(self) -> None` (line 227; internal)
  - `remember_passages(self, ask_id: str, keys: list[str]) -> str` (line 233; public)
  - `forget_passages(self, ask_id: str) -> None` (line 244; public) — The ask now shows a stored comparison: its unstored one is no longer shown.
  - `passages(self, ask_id: str) -> tuple[str, list[str]] | None` (line 250; public)
  - `start(self, ctx: SidecarContext, kind: str, ask_id: str | None, work: Work, *, deliver: Deliver | None=None, supersede: bool=False, on_job: Callable[[_Job], None] | None=None) -> _Job` (line 255; public) — ``supersede`` (Reader CA3, Codex final verify F12): this job replaces the unfinished jobs of its kind for the same ask (a refinement of a comparison): they are cancelled, so none of them answers or binds after this one started, even when the frontend's own cancel comes late.
  - `get(self, job_id: str) -> _Job | None` (line 319; public)
- `deliver_comparison(ctx: SidecarContext, ask_id: str, result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 363) — A comparison job's result as it may go out NOW (RW4d fix round 5, F2), at every delivery (the first one, and each cached read through ``reader.library_job``): a comparison any of whose contributing passages is withheld now, or whose provenance cannot be resolved, is refused whol…
- `class LibraryJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 387)
- `reader_library_job(ctx: SidecarContext, params: LibraryJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 395) — A library job's state, at once (never a wait on the request path).
- `class LibraryJobCancelInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 405)
- `reader_library_job_cancel(ctx: SidecarContext, params: LibraryJobCancelInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 410) — Cancel a library job: it never answers after this (the result is fenced).
- `class LibraryAskInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 427)
- `reader_library_ask(ctx: SidecarContext, params: LibraryAskInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 453) — Passages from the learner's library for a question, sources first (spec §7.3).
- `class LibraryAskIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 496)
- `reader_library_ask_notes(ctx: SidecarContext, params: LibraryAskIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 501) — The organizer's line per passage (one listwise call; cached per ask).
- `class LibraryCompareInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 536) — One comparison request for every door (Reader CA3, K12; §4.1).
- `scope_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 573) — Reader CA3 is on: its switch and the comparison it builds on.
- `reader_library_compare(ctx: SidecarContext, params: LibraryCompareInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 580) — How the pinned passages' sources treat the question (display only until RW4d).
- `class LibraryAskTutorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 727) — The tutor over the pins, or (Reader CA3) over the comparison shown.
- `reader_library_ask_tutor(ctx: SidecarContext, params: LibraryAskTutorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 748) — The tutor on request, answering only from the pinned passages (§3.4 item 11).

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 49)
- `LIBRARY_ASK_RPCS` ([src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 52)
- `MAX_KEPT_JOBS` ([src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 61)
- `ANCHOR_SPANS_MAX` ([src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 518)
- `_CA3_FIELDS` ([src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 570)

### Explicit exports

`__all__` declares:

- `LIBRARY_ASK_RPCS`
- `LibraryJobs`
- `follow_up_caller`
- `prompt_contract_fields`
- `reader_caller`

## Internal implementation anchors

- `_require(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 84)
- `_caller_record(caller: Any, *, workbench_session_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 146)
- `_ask_row(repository: Any, ask_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 157)
- `class _Job` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 176)
- `_as_sidecar_error(exc: BaseException) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 194)
- `_jobs(ctx: SidecarContext) -> LibraryJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 324)
- `_job_payload(job: _Job) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 332) — The job as the wire reads it; a failed job raises its error.
- `_start(ctx: SidecarContext, kind: str, ask_id: str | None, work: Work, *, deliver: Deliver | None=None, supersede: bool=False, on_job: Callable[[_Job], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 356)
- `_resolved_or_none(repository: Any, extraction_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 442) — A named reading as the handlers resolve it (a source names its current reading).
- `class _PinnedCompareInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 521) — RW4a/RW4d's request, exactly: what the RPC takes while ``reader_compare.scope_enabled`` is off (CA3 off = today).
- `_open_for_door(ctx: SidecarContext, vault: Any, repository: Any, params: LibraryCompareInput) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 671) — CA3: the ask this request binds by: the one it names, else (a door with no library answer) the comparison's own row, opened under the caller the server derives from the open book and workbench session (G19).
- `_door_scope(repository: Any, row: dict[str, Any], params: LibraryCompareInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 705) — CA3: the request's scope, from the ask row (its anchor, never one the follow-up names) and the books the request names.
- `class _PinnedTutorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/library_ask.py), line 718) — Today's request, exactly: what the RPC takes while ``reader_compare.scope_enabled`` is off (CA3 off = today).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `_require`, `_start`, `reader_caller`, `scope_enabled`; statically calls `_require`, `_start`, `reader_caller`, `scope_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `LibraryJobs`, `_job_payload`, `reader_caller`; statically calls `LibraryJobs`, `_job_payload`, `reader_caller`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `follow_up_caller`; statically calls `follow_up_caller`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `_job_payload`, `_jobs`, `reader_caller`; statically calls `_job_payload`, `_jobs`, `reader_caller`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `reader_caller`; statically calls `reader_caller`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_shown_spans`; calls `record_shown_spans`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_comparison`, `propose_sources`; calls `propose_comparison`, `propose_sources`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `withheld_comparisons`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `session_row`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; calls `by_point_enabled`, `clean_perspectives`, `compare_kept_state`, `compared_on`, `keep_enabled`, `max_perspectives`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; calls `OnlyPinned`, `ask_library`, `ask_row`, `ask_tutor`, `compare`, `compare_enabled`, `comparison_passage_keys`, `library_ask_enabled`, `open_comparison`, `organize`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`, `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `PinnedSpanProvider`; calls `PinnedSpanProvider`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `HeldOutMaterialRefused`, `QuestionLimitReached`, `TutorQAError`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `provider_label`, `ready_tutor_qa_provider`; calls `provider_label`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `books_payload`; calls `books_payload`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `queue_tutor_question_gap`; calls `queue_tutor_question_gap`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `require_identity`; calls `require_identity`

### Platform and third-party dependencies

- Standard library: `__future__`, `copy`, `dataclasses`, `logging`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]], [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_reading_a_pending_job_never_waits_on_the_serial_loop`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw4a_rpcs_are_all_of_them`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p7_rw5b_figures_ask_as_the_rpc_that_asked`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
  - `test_m1_a_figure_jobs_delayed_poll_after_a_vault_switch_mints_nothing`
  - `test_m1_a_relay_from_before_a_stop_mints_nothing`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_no_reader_input_names_a_policy_and_none_is_authoring`
  - `test_with_the_sources_spec_absent_the_library_ask_is_absent`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/library_ask.py](../../../../../../src/learnloop_sidecar/handlers/library_ask.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
