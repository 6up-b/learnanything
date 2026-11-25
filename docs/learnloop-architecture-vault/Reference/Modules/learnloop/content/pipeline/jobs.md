---
title: "learnloop.content.pipeline.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/jobs.py"
source_paths:
  - "src/learnloop/content/pipeline/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.jobs module"
  - "src/learnloop/content/pipeline/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.jobs` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Concrete ingest jobs and the durable host shared by CLI and sidecar (§6.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py) |
| Source lines | 2143 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReadingSweep` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 96) — What one pass of the reading sweep did (reading-hardening, part 1).
- `class ActiveIngestJobError(RuntimeError)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 149)
  - `__init__(self, job_id: str) -> None` (line 150; internal)
- `class DurableIngestJobs` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 155) — Enqueues single-source ingests into the durable queue and reads their state.
  - `__init__(self) -> None` (line 158; internal)
  - `reading_lock(self) -> threading.RLock` (line 213; public)
  - `bind(self, repository: Repository, vault_root: Path, *, clock: Clock | None=None, services: RunnerServices | None=None, lease_ttl_seconds: int=120, heartbeat_interval_seconds: float=15, poll_interval_seconds: float=1.0, background: bool | None=None, reader_synth_client_factory: Any=None, sweep_abandoned_synthesis: bool=True) -> None` (line 218; public) — Attach the wrapper to a loaded vault.
  - `_require_runner(self) -> IngestRunner` (line 330; internal)
  - `repository(self) -> Repository` (line 336; public)
  - `vault_root(self) -> Path` (line 340; public)
  - `enqueue_add_source(self, source: str, *, source_id: str | None=None, options: Any=None, auto_build: bool=True) -> str` (line 345; public) — Enqueue an Add: the import, then the automatic build planner that depends on it (``learnloop.content.pipeline.add_source``).
  - `enqueue_auto_build(self, source_id: str, *, approved: bool=False, chapter_ids: Sequence[str] | None=None, start_unit_id: str | None=None, answers_revision: int | None=None) -> str | None` (line 400; public) — Plan another automatic build for an already-readable source.
  - `reading_now(self) -> datetime` (line 449; public) — The instant the reading sweep and a failed request's backoff use.
  - `reading_advance_pending(self, extraction_id: str) -> bool` (line 454; public) — Whether the book's reading request failed and is not settled: the Reader's next report asks again instead of being coalesced.
  - `wake_reading_retries(self) -> None` (line 461; public) — Bring the reading sweep's next pass forward (a background host; a foreground host calls :meth:`sweep_reading_requests` itself).
  - `wake_blocking_work(self) -> None` (line 478; public) — A request waits behind its book's queued or running work: make sure the ingest worker runs it (after a restart nothing else may start it, Codex finish-verify F1).
  - `resume_contextual_index(self, *, now: datetime | None=None) -> str | None` (line 486; public) — Wake a deferred local index obligation (Codex review F4).
  - `refresh_fusion_posteriors(self, *, now: datetime | None=None) -> bool` (line 543; public) — Refit ``retrieval_fusion_posteriors`` from the feedback receipts (spec §9.2: "a nightly job, or one at sidecar start"; Codex review F11): only while a new embedding space is on, only when receipts arrived since the stored fit, and at most once per ``feedback.REFIT_EVERY_HOURS``…
  - `resume_book_preparation(self) -> bool` (line 573; public) — Start the ingest worker when a book's automatic preparation (an Add, a build planner, a planner's build) is queued, the worker could run it, and no worker is running.
  - `sweep_reading_requests(self, *, now: datetime | None=None) -> 'ReadingSweep'` (line 620; public) — One pass of the reading sweep at ``now`` (default :meth:`reading_now`): one query over the books' pending requests, and an act on each one due (``retry_at`` passed, or none) whose book's work is done (:func:`~learnloop.content.pipeline.add_source.act_on_reading_request`).
  - `retry_reading_advances(self, *, now: datetime | None=None) -> int` (line 661; public) — One sweep pass (tests and foreground hosts call it directly): returns how many requests settled (one still waiting on its book's work does not count).
  - `_ensure_reading_sweep(self) -> None` (line 668; internal)
  - `_reading_sweep_delay(self, sweep: 'ReadingSweep') -> float` (line 680; internal) — Until the next pass: the sweep's pace, sooner when a request's retry time comes first.
  - `_reading_sweep_loop(self) -> None` (line 689; internal) — The reading sweep, run on the calling thread (the sweep thread runs :func:`_run_reading_sweep`): a pass every :attr:`READING_SWEEP_SECONDS` (or at the next retry time, or when woken) for as long as this host runs in the background.
  - `_reading_sweep_pass(self, failures: int) -> tuple[int, float] | None` (line 702; internal) — One pass of the sweep thread: ``None`` when this host stopped (or runs in the foreground now), else the failures in a row and the wait until the next pass.
  - `_settle_reading_with_cancel(self, runner: IngestRunner, batch_id: str) -> Callable[[], object]` (line 760; internal) — A cancel answers the reading requests of the books whose work it stops: each is settled at the revision it has now (reading-hardening, part 1).
  - `start(self, vault_root: Path, source: str, subject_id: str, mode: Literal['canonical', 'exam'], pdf_engine: str | None=None) -> dict[str, Any]` (line 775; public)
  - `get(self, job_id: str) -> dict[str, Any] | None` (line 819; public)
  - `list(self) -> list[dict[str, Any]]` (line 824; public)
  - `cancel(self, job_id: str) -> dict[str, Any] | None` (line 829; public)
  - `_needs_content_reload(self, job: dict[str, Any]) -> bool` (line 839; internal)
  - `needs_reload(self, job_id: str) -> bool` (line 853; public)
  - `mark_reloaded(self, job_id: str) -> None` (line 857; public)
  - `completed_jobs_awaiting_reload(self, job_types: frozenset[str], *, limit: int) -> list[str]` (line 860; public) — Jobs with new content, including parts of a still-running section.
  - `halt(self) -> None` (line 868; public) — The host stopped serving the bound vault (``SidecarContext``'s refusal): let go of its runner and stop every loop, without joining (this runs on the request thread that met the refusal, and a join there waits for whatever provider call a job is in).
  - `shutdown(self) -> None` (line 887; public)
  - `enqueue_import(self, sources: list[str], *, subject_id: str | None=None, inventory: bool=False, estimate: dict[str, Any] | None=None, page_selection: list[int] | None=None, page_selections: dict[str, list[int]] | None=None, reader_disabled_sources: set[str] | frozenset[str] | None=None, pdf_engine: str | None=None, priority: int=0) -> str` (line 904; public) — Enqueue an Import (or Import & inventory) batch (§6.1).
  - `enqueue_extraction_repair(self, *, revision_id: str, pages: list, repair_options: dict[str, Any] | None, consent: dict[str, Any], parent_extraction_id: str | None=None, subject_id: str | None=None) -> str` (line 948; public) — Enqueue a consent-gated extraction-repair batch (§2.5).
  - `enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str, selection_span_ids: list[str] | None=None) -> str` (line 980; public) — Enqueue one section's quick-check authoring (reader producer slice).
  - `enqueue_reader_inquiry_check(self, *, extraction_id: str, inquiry_root_event_id: str, anchor_span_ids: list[str]) -> str` (line 1001; public) — Enqueue the reconnect line's passage-scoped quick check (RW1a).
  - `enqueue_reader_selection_check(self, *, extraction_id: str, anchor_span_ids: list[str], question_style: str) -> str` (line 1034; public) — Enqueue one active-reading question on a selection (RW1b).
  - `enqueue_reader_exercise_import(self, *, extraction_id: str, raw_selection: dict[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None) -> str` (line 1067; public) — Enqueue authoring of the learner's selected textbook exercise(s).
  - `enqueue_source_exercise_import(self, *, import_id: str, extraction_id: str, span_ids: list[str], proposal_id: str | None=None, label: str | None=None, learning_object_hint: str | None=None, request: dict[str, Any] | None=None) -> str` (line 1104; public) — Enqueue the import of a picked textbook exercise (canonical sources S1).
  - `enqueue_practice_expansion(self, *, learning_object_ids: list[str], subject_id: str | None=None, reason: str | None=None, source_refs: list[dict[str, Any]] | None=None, ad_commission_id: str | None=None, topic_keys: Mapping[str, str] | None=None, start: bool=True) -> str` (line 1135; public) — Enqueue per-LO practice generation (reader-first progressive seeding).
  - `run_queued_work(self) -> None` (line 1196; public) — Start the worker on what is queued (a foreground host drains it now): after a transaction that queued work with ``start=False`` has committed.
  - `enqueue_goal_population(self, *, goal_id: str) -> str` (line 1203; public) — Enqueue durable goal-scoped practice authoring from the wizard.
  - `enqueue_rung_variant(self, *, request_id: str, subject_id: str | None=None) -> str` (line 1215; public) — Enqueue one learner-requested variant authoring (interactive band — the learner is waiting on it, like a quick-add build).
  - `enqueue_question_promotion(self, *, event_id: str, subject_id: str | None=None) -> str` (line 1229; public) — Enqueue a durable Open-question analysis/authoring request.
  - `enqueue_concept_animation(self, *, animation_id: str, subject_id: str | None=None) -> str` (line 1247; public) — Enqueue one explainer-animation generation (interactive band — the learner clicked generate and is watching the status).
  - `enqueue_figure_rich(self, *, payload: Mapping[str, Any], grant: Any=None, origin: str | None=None) -> str` (line 1261; public) — Enqueue one rich figure build (Reader RW5d P2b; interactive band: the learner pressed "show me" and the quick figure, if any, is on the page).
  - `retry_figure_rich(self, job_id: str, *, error_code: str) -> bool` (line 1291; public) — Requeue a rich figure job that failed with ``error_code`` (the plan wait), unless it was cancelled (Reader RW5d P2b).
  - `enqueue_inventory(self, *, extraction_id: str, units: list[dict[str, Any]], subject_id: str | None=None, source_set_id: str | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, priority: int=0) -> str` (line 1304; public) — Enqueue a role-aware unit-inventory batch (§7).
  - `enqueue_quick_add_build(self, *, extraction_id: str, units: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, create_goal: bool=False, priority: int=QUICK_ADD_PRIORITY, batch_id: str | None=None) -> str` (line 1337; public) — Enqueue the Quick-add build batch (§1): inventory(selected units) then bootstrap_synthesis over the freshly-created source set, as one batch that drains ahead of bulk work.
  - `enqueue_source_set_build(self, *, members: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, create_goal: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 1395; public) — Enqueue a study-map build batch for an EXISTING source set (§1/§8): one inventory job per member (over its scoped units) followed by a bootstrap_synthesis job that depends on all of them, so gates only run once every member's units carry inventories.
  - `enqueue_source_set_append(self, *, members: list[dict[str, Any]], source_set_id: str, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None, change_kind: str='source_added', subject_id: str | None=None, brief: dict[str, Any] | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 1466; public) — Enqueue a bounded-neighborhood APPEND batch for a collection whose subject already carries a study map (§10).
  - `retry_synthesis(self, batch_id: str, *, synthesis_budgets: dict[str, int] | None=None, reuse_candidate: bool=False, repair_candidate: bool=False, repair_ops: list[dict[str, Any]] | None=None, unlimited_token_budget: bool=False) -> dict[str, Any]` (line 1537; public) — Retry only a failed synthesis stage with revised execution ceilings.
  - `get_batch(self, batch_id: str) -> dict[str, Any] | None` (line 1597; public)
  - `list_batches(self, limit: int=_RECENT_LIMIT) -> list[dict[str, Any]]` (line 1604; public)
  - `cancel_batch(self, batch_id: str) -> dict[str, Any] | None` (line 1632; public)
  - `_cancel_batch(self, runner: IngestRunner, batch_id: str) -> None` (line 1639; internal) — Cancel, and settle the reading requests of the books whose work this was, in one transaction (reading-hardening, part 1: a cancel answers the request, so the sweep never re-plans the work the learner just stopped; review F1: both commit or neither does).
  - `interrupt_codex(self, job_id: str | None=None) -> dict[str, Any]` (line 1649; public) — Interrupt one live Codex call while keeping the sidecar process alive.
  - `resume_waiting_for_ok(self) -> list[str]` (line 1693; public) — The jobs that waited for the learner's OK to use AI, queued again once and started.
  - `resume_batch(self, batch_id: str) -> dict[str, Any] | None` (line 1701; public)
  - `drain_foreground(self) -> int` (line 1711; public) — Drain the queue synchronously (tests + CLI-less contexts).
  - `_ensure_worker(self) -> None` (line 1716; internal)
  - `_worker_loop(self) -> None` (line 1748; internal)
  - `_quick_check_worker_loop(self) -> None` (line 1793; internal) — Drain independent quick checks beside the serialized vault writer.
  - `kick_reader_drain(self) -> None` (line 1827; public) — Ensure queued demand-paged reader requests get drained.
  - `_drain_reader_requests(self, runner: IngestRunner) -> int` (line 1850; internal) — Drain queued reader requests with a real synthesize client.
  - `_resolve_reader_client(self, runner: IngestRunner) -> Any` (line 1874; internal)
  - `_legacy_job_for_batch(runner: IngestRunner, batch_id: str) -> dict[str, Any]` (line 1903; internal) — The synthesis job the frontend polls (the batch also holds an import job).
  - `_active_job_locked(self, runner: IngestRunner) -> dict[str, Any] | None` (line 1912; internal)
- `retryable_synthesis_job(jobs: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2008) — The batch's one unfinished synthesis job a retry reruns, or ``None`` and the refusal's code.
- `preserved_candidate_run(synthesis_job: Mapping[str, Any], synthesis_run: Callable[[str], Mapping[str, Any] | None]) -> tuple[str | None, str | None]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2026) — The synthesis run whose preserved candidate a retry may revalidate (and repair) with no model call, or ``None`` and the refusal's code.
- `synthesis_recovery(jobs: list[dict[str, Any]], repo: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2042) — What :meth:`DurableIngestJobs.retry_synthesis` would accept for this batch, from its own checks, so the desktop offers exactly the retries the host takes.

### Module constants

- `_LEGACY_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 84)
- `_ACTIVE_STATUSES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 85)
- `_RECENT_LIMIT` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 86)
- `QUICK_ADD_PRIORITY` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 91)
- `_QUICK_CHECK_WORKERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 92)
- `_LADDER_BY_JOB_TYPE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1931)
- `SYNTHESIS_RECOVERY_REFUSALS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2000)

## Internal implementation anchors

- `_queue_due_replay(host: Any, runner: Any, newest: Mapping[str, Any] | None, now: datetime | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 46) — Local retrieval P2 (spec §9.3; Codex review F10): the nightly teacher replay for a library that is fully indexed.
- `_run_reading_sweep(host: 'weakref.ref[DurableIngestJobs]') -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 108) — The reading sweep thread.
- `_reading_due_at(retry_at: str | None) -> datetime | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 135) — When a pending reading request is due: its retry time, or ``None`` (due now) when it has none or one that does not parse or convert to UTC (``0001-01-01T00:00:00+01:00`` overflows, reading-hardening verify N2), so no stored value can keep a request from ever being due.
- `_iso(moment: datetime | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1919) — ``moment`` (default: now) as the ISO UTC text reading requests store.
- `_job_view(job: dict[str, Any], repo: Repository, *, depends_on: list[str] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1938) — One job as the Batch-progress screen needs it: the checkpoint ladder, live phase/window counts, actual usage, and any waiting_for_input payload (§5.7).
- `_batch_view(batch: dict[str, Any], jobs: list[dict[str, Any]], repo: Repository, *, dependencies_by_job: dict[str, list[str]] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2060)
- `_failed_rung_request_id(job: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2101)
- `_compat_status(status: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2112) — Map the durable status vocabulary onto the legacy job vocabulary the existing frontend/handlers expect (queued|running|completed|failed|cancelled).
- `_compat(job: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2119)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `DurableIngestJobs`; statically calls `DurableIngestJobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `IngestJobManager`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `ActiveIngestJobError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/authoring/jobs|learnloop.content.authoring.jobs]] — imports `AD_MODELS_OFF_CODE`, `_reader_source_sets`, `ad_commission_batch_id`; calls `_reader_source_sets`, `ad_commission_batch_id`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `ADD_SOURCE_PRIORITY`, `ADD_SOURCE_WORKFLOW`, `AUTO_BUILD_BATCH_PREFIX`, `AUTO_BUILD_WORKFLOW`, `AUTO_STUDY_MAP_JOB`, `AddSourceOptions`, `BUILD_PRIORITY`, `module`, `practice_expansion_payload`; calls `AddSourceOptions`, `act_on_reading_request`, `practice_expansion_payload`, `settle_reading_for_cancelled_batch`
- [[Reference/Modules/learnloop/content/pipeline/job_types|learnloop.content.pipeline.job_types]] — imports `applying_job_types`, `parallel_job_types`; calls `applying_job_types`, `parallel_job_types`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `CHECKPOINT_LADDER`, `IngestRunner`, `JobSpec`, `RunnerServices`, `derive_batch_status`, `effective_ingest_job_status`; calls `IngestRunner`, `JobSpec`, `derive_batch_status`, `effective_ingest_job_status`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `record_job_enqueued`; calls `record_job_enqueued`
- [[Reference/Modules/learnloop/db/writer_fence|learnloop.db.writer_fence]] — imports `module`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `selected_backend`; calls `selected_backend`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `refit_posteriors`; calls `refit_posteriors`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `REPLAY_EVERY_HOURS`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `selection_claim_key`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `drain_requests`, `model_synthesis`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `refresh_due`; calls `refresh_due`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `DEFERRED_STATUSES`, `INDEX_JOB`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `resolver_active`; calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `replay_due`; calls `replay_due`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `logging`, `os`, `pathlib`, `threading`, `types`, `typing`, `weakref`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/glm_ocr_helpers.py](../../../../../../../tests/glm_ocr_helpers.py) — direct import
- [tests/reading_request_sweep_helpers.py](../../../../../../../tests/reading_request_sweep_helpers.py) — direct import
- [tests/section_question_parts_helpers.py](../../../../../../../tests/section_question_parts_helpers.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished`
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`
  - `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_check_over_held_out_material_is_refused_before_any_model_call`
  - `test_a_reader_import_of_held_out_material_is_refused_before_any_model_call`
  - `test_a_reader_preset_fails_before_any_model_call_when_the_vault_config_disappears`
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
- [tests/test_ingest_eligibility_contract.py](../../../../../../../tests/test_ingest_eligibility_contract.py) — direct import
  - `test_a_completed_batch_offers_no_retry`
  - `test_candidate_reuse_is_offered_exactly_when_the_host_takes_it`
  - `test_the_batch_view_offers_retry_exactly_when_the_host_takes_it`
- [tests/test_ingest_jobs.py](../../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_a_build_asked_for_its_goal_carries_create_goal_to_the_synthesis_job`
  - `test_background_reader_drain_records_model_call_receipts`
  - `test_bind_premarks_previously_completed_apply_jobs`
  - `test_cancelled_job_reaches_terminal_state`
  - `test_import_batch_is_not_a_build_and_its_ladder_says_so`
  - `test_kick_reader_drain_leaves_requests_queued_without_provider`
  - `test_kick_reader_drain_runs_model_synthesis_foreground`
  - `test_list_batches_bulk_loads_failed_rung_requests`
  - `test_manager_alias_is_durable`
  - `test_only_one_ingest_can_write_a_vault_at_once`
  - `test_reader_drain_client_routes_via_canonical_ingest`
  - `test_resume_false_completed_rung_variant_reopens_request`
  - `test_source_set_append_snapshots_budget_overrides`
  - `test_source_set_build_enqueues_inventory_then_synthesis_with_budgets`
- [tests/test_ingest_latency_journey.py](../../../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_background_host_wakes_without_waiting_for_poll_timeout`
- [tests/test_ingest_m3.py](../../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_import_snapshots_build_plan_estimate_into_payload`
  - `test_import_snapshots_pdf_engine_choice_into_payload`
  - `test_import_snapshots_pdf_page_selection_into_payload`
  - `test_multi_source_import_assigns_page_selection_per_source`
- [tests/test_ingest_ownership.py](../../../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_busy_vault_lock_defers_lease_work_instead_of_failing`
  - `test_fast_restart_reconciles_later_expiry_without_replacing_live_work`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_same_vault_rebind_preserves_kill_codex_interrupt_handle`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged`
  - `test_use_this_one_on_a_fallback_exercise_runs_the_readers_import_unchanged`
- [tests/test_local_index.py](../../../../../../../tests/test_local_index.py) — direct import
  - `test_a_deferred_index_job_is_woken_at_its_retry_time`
  - `test_a_queued_index_job_whose_worker_never_started_is_started_by_the_sweep`
- [tests/test_mobile_v4_reader.py](../../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
- [tests/test_query_student.py](../../../../../../../tests/test_query_student.py) — direct import
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
- [tests/test_queue_revision_after_applying_jobs.py](../../../../../../../tests/test_queue_revision_after_applying_jobs.py) — direct import
  - `test_a_picked_source_exercise_written_as_practice_moves_the_revision`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_quick_add_batches_take_queue_priority`
- [tests/test_reader_passage_check.py](../../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_second_request_while_one_is_live_joins_its_job`
- [tests/test_reader_progression.py](../../../../../../../tests/test_reader_progression.py) — direct import
  - `test_practice_expansion_queue_preserves_reader_source_refs`
- [tests/test_reader_reconnect.py](../../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_reconnect_rpcs_round_trip`
  - `test_the_quick_check_read_reports_its_durable_jobs_state`
- [tests/test_reading_hardening_2_fixes.py](../../../../../../../tests/test_reading_hardening_2_fixes.py) — direct import
  - `test_f1_a_build_queued_just_before_the_process_ended_runs_at_the_next_start`
  - `test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone`
- [tests/test_reading_hardening_review_fixes.py](../../../../../../../tests/test_reading_hardening_review_fixes.py) — direct import
  - `test_f1_a_crash_between_the_cancel_and_its_settle_leaves_neither_after_a_restart`
  - `test_f2_a_wake_from_outside_the_sweep_still_brings_its_pass_forward`
  - `test_f2_on_the_real_threads_a_failing_unrecordable_act_does_not_spin`
  - `test_f2_planning_and_its_record_both_failing_back_off_through_the_sweeps_own_loop`
- [tests/test_reading_hardening_verify_fixes.py](../../../../../../../tests/test_reading_hardening_verify_fixes.py) — direct import
  - `test_n2_a_stored_retry_time_that_cannot_be_read_is_due_now`
- [tests/test_reading_request_sweep.py](../../../../../../../tests/test_reading_request_sweep.py) — direct import
  - `test_a_a_transient_scan_failure_is_retried_not_taken_for_nothing_due`
  - `test_a_request_waiting_on_the_books_work_is_not_replanned_by_the_sweep`
  - `test_a_scan_that_keeps_failing_backs_off_to_the_sweeps_pace`
  - `test_the_sweep_ends_with_a_host_nobody_uses`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_interactive_import_bounds_the_authored_drafts_own_duration`
  - `test_an_interactive_import_is_validated_against_its_proposal_and_corrected`
  - `test_picking_an_exercise_proposal_queues_its_import_and_records_the_pick`
- [tests/test_source_space_resolver.py](../../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
- [tests/test_synthesis_sweep_primary_only.py](../../../../../../../tests/test_synthesis_sweep_primary_only.py) — direct import
- [tests/test_ux_phase1_connect_ai.py](../../../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
  - `test_quick_add_reads_the_recorded_ok_instead_of_asking_per_build`
- [tests/test_ux_phase1_finish.py](../../../../../../../tests/test_ux_phase1_finish.py) — direct import
- [tests/test_ux_phase1_landing.py](../../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_with_the_retired_keep_local_gets_its_passage_check_when_asked`
- [tests/test_writer_fence_recovery.py](../../../../../../../tests/test_writer_fence_recovery.py) — direct import
  - `test_a_same_tag_reload_keeps_the_ingest_runner`
  - `test_a_same_vault_reload_after_an_upgrade_gives_new_ingest_claims_the_successors_repository`
- [tests/ux_phase1_auto_build_helpers.py](../../../../../../../tests/ux_phase1_auto_build_helpers.py) — direct import
- [tests/ux_phase1_landing_helpers.py](../../../../../../../tests/ux_phase1_landing_helpers.py) — direct import
- [tests/ux_phase1_review_fixes_helpers.py](../../../../../../../tests/ux_phase1_review_fixes_helpers.py) — direct import

## Modification guidance

- Change jobs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
