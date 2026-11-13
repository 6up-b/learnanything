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
| Source lines | 5836 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `default_fetch(source: str, category: str, ctx: JobContext) -> FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 96) — Read raw bytes for one acquisition.
- `glm_upload_estimate(ctx: JobContext, fetched: FetchedBytes) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 315) — Pages and the estimated cost of reading this file with hosted GLM-OCR (``glm_ocr.estimate``), for the card's z.ai OK line (re-read safety item 5): the pages the import asks for, else every page of the file.
- `default_extract(fetched: FetchedBytes, category: str, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 442) — Produce Document IR from fetched bytes using the M1 extractor providers.
- `default_extraction_identity(fetched: FetchedBytes, category: str, ctx: JobContext) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 535) — Describe the chosen extractor before running it, making cache hits cheap.
- `class NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 653) — A resolved native-multimodal route: which chat provider ingests media.
- `default_run_legacy_ingest(*, vault_root: Path, source: str, subject_id: str, mode: str, progress: Callable[[str, dict[str, Any]], None] | None, clock: Clock | None, ir_markdown: str | None=None, resume_extraction_id: str | None=None, **_ignored: Any) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1123) — Run the legacy one-shot pipeline in-process with a ready provider client.
- `inventory_client_identity(client: Any) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1169)
- `default_inventory_identity(ctx: JobContext) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1176) — Resolve the primary inventory cache key without a runtime probe.
- `default_inventory_client(ctx: JobContext, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1190) — Resolve the unit-inventory/quick-check client through ai routing (§7).
- `default_synthesis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1223) — Resolve the canonical-ingest route for judgment-heavy synthesis.
- `default_animation_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1239) — Resolve the animation route (default: the medium-effort profile) — any configured provider works; run_concept_animation is getattr-discovered.
- `default_video_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1246) — Resolve [ai.routing] video_generation to an OpenRouter video client.
- `default_rung_variant_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1270) — Resolve the rung_variant route (default: the fast low-effort profile).
- `default_promotion_analysis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1280) — Fast classification/dedup pass for a durable promotion request.
- `default_promotion_authoring_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1294) — Judgment-heavy practice generation follows the configured authoring route.
- `handle_inventory(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1457) — inventory: role-aware per-unit inventories for the selected units (§7).
- `handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1806) — bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).
- `handle_append_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1938) — append_synthesis: bounded reconciliation against an existing study map.
- `handle_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2046) — import: fetch -> register artifact/revision -> extract to IR -> persist -> health.
- `queue_source_vectors(ctx: JobContext, extraction_id: str, *, title: str | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2262) — Queue the source-block embedding backfill a completed extraction owes.
- `queue_coverage_on_extract(ctx: JobContext, config: Any, extraction_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2311) — Deliverable curriculum C0b (spec §6.3): a completed extraction queues one ``curriculum_coverage_on_extract`` job, which judges the already-covered LOs again so the new reading's sections join their coverage (quiet: the plan only).
- `queue_contextual_indexes(ctx: JobContext, config: Any, extraction_id: str, *, title: str | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2343) — Local contextual retrieval P1a/P1b (spec §4.1, §8): a completed extraction queues the local index job and the Voyage fallback backfill.
- `handle_local_source_index(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2441) — local_source_index: index every owed window in one 9B worker batch.
- `handle_source_fallback_backfill(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2467) — source_fallback_backfill: the Voyage fallback space's windows for one source (capped, receipted; an aggregate report, never block text).
- `handle_curriculum_coverage_on_extract(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2505) — curriculum_coverage_on_extract: judge the covered LOs again after an extraction (C0b, §6.3).
- `handle_source_embedding_backfill(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2522) — source_embedding_backfill: embed a source's current extraction's blocks.
- `handle_legacy_ingest(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2616) — legacy_ingest: wrap the existing one-shot pipeline as one durable job so the current single-source UX keeps working (Quick add compatibility, §6.1).
- `handle_extraction_repair(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2703) — extraction_repair: a consent-gated, page-range re-extraction (§2.5).
- `handle_reader_quick_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2925) — Author one section-boundary quick check (reader producer slice).
- `handle_reader_exercise_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3212) — reader_exercise_import: author the learner's selected textbook exercise(s) into complete, schedulable PracticeItems.
- `handle_source_exercise_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3322) — source_exercise_import: a learner picked a textbook exercise proposal (canonical sources S1, §7.2).
- `ad_commission_batch_id(commission_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3369) — The one durable batch of an adaptive difficulty commission's generation (the store's name for it: a commission's expiry reads its job, Codex review F5).
- `ad_commission_skip_record(*, commission_id: Any, job_id: Any, rule: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3388) — Why a commission's job generated nothing (pure): ``commission_closed`` (it landed or expired), ``view_unavailable`` (AD's held-out predicate couldn't be read) or ``guard_denied`` (AD's guard refused a read; the denial itself is in ``ad_guard_denials.jsonl``).
- `handle_practice_expansion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3501) — practice_expansion: per-LO item generation (reader-first seeding).
- `handle_goal_population(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3551) — Generate and apply the missing practicable supply for one active goal.
- `handle_question_promotion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3642) — Run one persisted Open-question → practice request.
- `handle_rung_variant(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3741) — rung_variant: author one learner-requested easier/harder sibling item.
- `handle_concept_animation(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3773) — concept_animation: author + validate + render one explainer scene.
- `handle_figure_rich(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3849) — figure_rich (Reader RW5d P2b): write, check, render and store one rich figure (a Manim animation) from the figure author's brief.
- `handle_auto_study_map(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3877) — auto_study_map: plan the automatic question build after an Add (UX Phase 1).
- `class ReadingSweep` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3951) — What one pass of the reading sweep did (reading-hardening, part 1).
- `class ActiveIngestJobError(RuntimeError)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 4004)
  - `__init__(self, job_id: str) -> None` (line 4005; internal)
- `class DurableIngestJobs` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 4010) — Enqueues single-source ingests into the durable queue and reads their state.
  - `__init__(self) -> None` (line 4013; internal)
  - `reading_lock(self) -> threading.RLock` (line 4062; public)
  - `bind(self, repository: Repository, vault_root: Path, *, clock: Clock | None=None, services: RunnerServices | None=None, lease_ttl_seconds: int=120, heartbeat_interval_seconds: float=15, poll_interval_seconds: float=1.0, background: bool | None=None, reader_synth_client_factory: Any=None, sweep_abandoned_synthesis: bool=True) -> None` (line 4067; public) — Attach the wrapper to a loaded vault.
  - `_require_runner(self) -> IngestRunner` (line 4147; internal)
  - `repository(self) -> Repository` (line 4153; public)
  - `vault_root(self) -> Path` (line 4157; public)
  - `enqueue_add_source(self, source: str, *, source_id: str | None=None, options: Any=None, auto_build: bool=True) -> str` (line 4162; public) — Enqueue an Add: the import, then the automatic build planner that depends on it (``learnloop.content.pipeline.add_source``).
  - `enqueue_auto_build(self, source_id: str, *, approved: bool=False, chapter_ids: Sequence[str] | None=None, start_unit_id: str | None=None, answers_revision: int | None=None) -> str | None` (line 4217; public) — Plan another automatic build for an already-readable source.
  - `reading_now(self) -> datetime` (line 4266; public) — The instant the reading sweep and a failed request's backoff use.
  - `reading_advance_pending(self, extraction_id: str) -> bool` (line 4271; public) — Whether the book's reading request failed and is not settled: the Reader's next report asks again instead of being coalesced.
  - `wake_reading_retries(self) -> None` (line 4278; public) — Bring the reading sweep's next pass forward (a background host; a foreground host calls :meth:`sweep_reading_requests` itself).
  - `wake_blocking_work(self) -> None` (line 4295; public) — A request waits behind its book's queued or running work: make sure the ingest worker runs it (after a restart nothing else may start it, Codex finish-verify F1).
  - `resume_contextual_index(self, *, now: datetime | None=None) -> str | None` (line 4303; public) — Wake a deferred local index obligation (Codex review F4).
  - `refresh_fusion_posteriors(self, *, now: datetime | None=None) -> bool` (line 4360; public) — Refit ``retrieval_fusion_posteriors`` from the feedback receipts (spec §9.2: "a nightly job, or one at sidecar start"; Codex review F11): only while a new embedding space is on, only when receipts arrived since the stored fit, and at most once per ``feedback.REFIT_EVERY_HOURS``…
  - `resume_book_preparation(self) -> bool` (line 4390; public) — Start the ingest worker when a book's automatic preparation (an Add, a build planner, a planner's build) is queued, the worker could run it, and no worker is running.
  - `sweep_reading_requests(self, *, now: datetime | None=None) -> 'ReadingSweep'` (line 4437; public) — One pass of the reading sweep at ``now`` (default :meth:`reading_now`): one query over the books' pending requests, and an act on each one due (``retry_at`` passed, or none) whose book's work is done (:func:`~learnloop.content.pipeline.add_source.act_on_reading_request`).
  - `retry_reading_advances(self, *, now: datetime | None=None) -> int` (line 4478; public) — One sweep pass (tests and foreground hosts call it directly): returns how many requests settled (one still waiting on its book's work does not count).
  - `_ensure_reading_sweep(self) -> None` (line 4485; internal)
  - `_reading_sweep_delay(self, sweep: 'ReadingSweep') -> float` (line 4497; internal) — Until the next pass: the sweep's pace, sooner when a request's retry time comes first.
  - `_reading_sweep_loop(self) -> None` (line 4506; internal) — The reading sweep, run on the calling thread (the sweep thread runs :func:`_run_reading_sweep`): a pass every :attr:`READING_SWEEP_SECONDS` (or at the next retry time, or when woken) for as long as this host runs in the background.
  - `_reading_sweep_pass(self, failures: int) -> tuple[int, float] | None` (line 4519; internal) — One pass of the sweep thread: ``None`` when this host stopped (or runs in the foreground now), else the failures in a row and the wait until the next pass.
  - `_settle_reading_with_cancel(self, runner: IngestRunner, batch_id: str) -> Callable[[], object]` (line 4577; internal) — A cancel answers the reading requests of the books whose work it stops: each is settled at the revision it has now (reading-hardening, part 1).
  - `start(self, vault_root: Path, source: str, subject_id: str, mode: Literal['canonical', 'exam'], pdf_engine: str | None=None) -> dict[str, Any]` (line 4592; public)
  - `get(self, job_id: str) -> dict[str, Any] | None` (line 4636; public)
  - `list(self) -> list[dict[str, Any]]` (line 4641; public)
  - `cancel(self, job_id: str) -> dict[str, Any] | None` (line 4646; public)
  - `needs_reload(self, job_id: str) -> bool` (line 4656; public)
  - `mark_reloaded(self, job_id: str) -> None` (line 4665; public)
  - `completed_jobs_awaiting_reload(self, job_types: frozenset[str], *, limit: int) -> list[str]` (line 4668; public) — Recent completed jobs of ``job_types`` this process has not reloaded for.
  - `shutdown(self) -> None` (line 4688; public)
  - `enqueue_import(self, sources: list[str], *, subject_id: str | None=None, inventory: bool=False, estimate: dict[str, Any] | None=None, page_selection: list[int] | None=None, page_selections: dict[str, list[int]] | None=None, reader_disabled_sources: set[str] | frozenset[str] | None=None, pdf_engine: str | None=None, priority: int=0) -> str` (line 4705; public) — Enqueue an Import (or Import & inventory) batch (§6.1).
  - `enqueue_extraction_repair(self, *, revision_id: str, pages: list, repair_options: dict[str, Any] | None, consent: dict[str, Any], parent_extraction_id: str | None=None, subject_id: str | None=None) -> str` (line 4749; public) — Enqueue a consent-gated extraction-repair batch (§2.5).
  - `enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str) -> str` (line 4781; public) — Enqueue one section's quick-check authoring (reader producer slice).
  - `enqueue_reader_inquiry_check(self, *, extraction_id: str, inquiry_root_event_id: str, anchor_span_ids: list[str]) -> str` (line 4798; public) — Enqueue the reconnect line's passage-scoped quick check (RW1a).
  - `enqueue_reader_selection_check(self, *, extraction_id: str, anchor_span_ids: list[str], question_style: str) -> str` (line 4831; public) — Enqueue one active-reading question on a selection (RW1b).
  - `enqueue_reader_exercise_import(self, *, extraction_id: str, raw_selection: dict[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None) -> str` (line 4864; public) — Enqueue authoring of the learner's selected textbook exercise(s).
  - `enqueue_source_exercise_import(self, *, import_id: str, extraction_id: str, span_ids: list[str], proposal_id: str | None=None, label: str | None=None, learning_object_hint: str | None=None, request: dict[str, Any] | None=None) -> str` (line 4901; public) — Enqueue the import of a picked textbook exercise (canonical sources S1).
  - `enqueue_practice_expansion(self, *, learning_object_ids: list[str], subject_id: str | None=None, reason: str | None=None, source_refs: list[dict[str, Any]] | None=None, ad_commission_id: str | None=None) -> str` (line 4932; public) — Enqueue per-LO practice generation (reader-first progressive seeding).
  - `enqueue_goal_population(self, *, goal_id: str) -> str` (line 4987; public) — Enqueue durable goal-scoped practice authoring from the wizard.
  - `enqueue_rung_variant(self, *, request_id: str, subject_id: str | None=None) -> str` (line 4999; public) — Enqueue one learner-requested variant authoring (interactive band — the learner is waiting on it, like a quick-add build).
  - `enqueue_question_promotion(self, *, event_id: str, subject_id: str | None=None) -> str` (line 5013; public) — Enqueue a durable Open-question analysis/authoring request.
  - `enqueue_concept_animation(self, *, animation_id: str, subject_id: str | None=None) -> str` (line 5031; public) — Enqueue one explainer-animation generation (interactive band — the learner clicked generate and is watching the status).
  - `enqueue_figure_rich(self, *, payload: Mapping[str, Any], grant: Any=None, origin: str | None=None) -> str` (line 5045; public) — Enqueue one rich figure build (Reader RW5d P2b; interactive band: the learner pressed "show me" and the quick figure, if any, is on the page).
  - `retry_figure_rich(self, job_id: str, *, error_code: str) -> bool` (line 5067; public) — Requeue a rich figure job that failed with ``error_code`` (the plan wait), unless it was cancelled (Reader RW5d P2b).
  - `enqueue_inventory(self, *, extraction_id: str, units: list[dict[str, Any]], subject_id: str | None=None, source_set_id: str | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, priority: int=0) -> str` (line 5080; public) — Enqueue a role-aware unit-inventory batch (§7).
  - `enqueue_quick_add_build(self, *, extraction_id: str, units: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY, batch_id: str | None=None) -> str` (line 5113; public) — Enqueue the Quick-add build batch (§1): inventory(selected units) then bootstrap_synthesis over the freshly-created source set, as one batch that drains ahead of bulk work.
  - `enqueue_source_set_build(self, *, members: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 5165; public) — Enqueue a study-map build batch for an EXISTING source set (§1/§8): one inventory job per member (over its scoped units) followed by a bootstrap_synthesis job that depends on all of them, so gates only run once every member's units carry inventories.
  - `enqueue_source_set_append(self, *, members: list[dict[str, Any]], source_set_id: str, new_revision_ids: list[str] | None=None, new_unit_ids: Mapping[str, Sequence[str]] | None=None, change_kind: str='source_added', subject_id: str | None=None, brief: dict[str, Any] | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 5232; public) — Enqueue a bounded-neighborhood APPEND batch for a collection whose subject already carries a study map (§10).
  - `retry_synthesis(self, batch_id: str, *, synthesis_budgets: dict[str, int] | None=None, reuse_candidate: bool=False, repair_candidate: bool=False, repair_ops: list[dict[str, Any]] | None=None, unlimited_token_budget: bool=False) -> dict[str, Any]` (line 5303; public) — Retry only a failed synthesis stage with revised execution ceilings.
  - `get_batch(self, batch_id: str) -> dict[str, Any] | None` (line 5378; public)
  - `list_batches(self, limit: int=_RECENT_LIMIT) -> list[dict[str, Any]]` (line 5385; public)
  - `cancel_batch(self, batch_id: str) -> dict[str, Any] | None` (line 5413; public)
  - `_cancel_batch(self, runner: IngestRunner, batch_id: str) -> None` (line 5420; internal) — Cancel, and settle the reading requests of the books whose work this was, in one transaction (reading-hardening, part 1: a cancel answers the request, so the sweep never re-plans the work the learner just stopped; review F1: both commit or neither does).
  - `interrupt_codex(self, job_id: str | None=None) -> dict[str, Any]` (line 5430; public) — Interrupt one live Codex call while keeping the sidecar process alive.
  - `resume_batch(self, batch_id: str) -> dict[str, Any] | None` (line 5465; public)
  - `drain_foreground(self) -> int` (line 5475; public) — Drain the queue synchronously (tests + CLI-less contexts).
  - `_ensure_worker(self) -> None` (line 5480; internal)
  - `_worker_loop(self) -> None` (line 5510; internal)
  - `_quick_check_worker_loop(self) -> None` (line 5553; internal) — Drain independent quick checks beside the serialized vault writer.
  - `kick_reader_drain(self) -> None` (line 5587; public) — Ensure queued demand-paged reader requests get drained.
  - `_drain_reader_requests(self, runner: IngestRunner) -> int` (line 5610; internal) — Drain queued reader requests with a real synthesize client.
  - `_resolve_reader_client(self, runner: IngestRunner) -> Any` (line 5630; internal)
  - `_legacy_job_for_batch(runner: IngestRunner, batch_id: str) -> dict[str, Any]` (line 5659; internal) — The synthesis job the frontend polls (the batch also holds an import job).
  - `_active_job_locked(self, runner: IngestRunner) -> dict[str, Any] | None` (line 5668; internal)

### Module constants

- `_MAX_INVENTORY_WORKERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 63)
- `INGEST_CODEX_TIMEOUT_SECONDS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 64)
- `_INVENTORY_CANCEL_POLL_SECONDS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 68)
- `_LEGACY_PHASE_TO_LADDER` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 70)
- `_LEGACY_PHASE_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 78)
- `_UPLOAD_FLOW_MESSAGES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 359)
- `_PLAIN_IMPORT_UPLOAD_MESSAGES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 369)
- `_PLAIN_IMPORT_IMAGE_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 375)
- `_PLAIN_IMPORT_SCAN_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 379)
- `GLM_NEEDS_UPLOAD_OK` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 384)
- `_LOCAL_REPAIR_IMAGE_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 386)
- `_ROUTED_AUDIO_FORMAT_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 850)
- `_SYNTH_STAGE_PHASE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1912)
- `_LOCAL_INDEX_DONE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2399)
- `_SOURCE_VECTORS_DONE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2502)
- `INQUIRY_HELD_POLL_SECONDS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3046)
- `INQUIRY_HELD_MAX_POLLS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3047)
- `_ENDED_JOB_STATUSES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3049)
- `AD_MODELS_OFF_CODE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3381)
- `AD_COMMISSION_SKIP` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3385)
- `DEFAULT_HANDLERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3890)
- `_LEGACY_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3916)
- `APPLYING_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3921)
- `_ACTIVE_STATUSES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3939)
- `_RECENT_LIMIT` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3940)
- `QUICK_ADD_PRIORITY` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3945)
- `_PARALLEL_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3946)
- `_QUICK_CHECK_WORKERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3947)
- `_LADDER_BY_JOB_TYPE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5687)

## Internal implementation anchors

- `_optional_int(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 87)
- `_fetch_metadata(source: str, category: str) -> tuple[str | None, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 130) — Best-effort human-readable (title, authors) for the fetched source.
- `_pdf_payload_config(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 150) — The effective PDF extraction config for one import job.
- `_local_repair(ctx: JobContext) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 186) — Whether this reading must stay on this computer: an extraction repair whose consent is local (GLM-OCR third review F10, set by :func:`handle_extraction_repair`).
- `_repair_is_local(consent: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 196) — A repair consent that approved no external service: OutlineAndPlan's repair without "external VLM" and ``learnloop repair-extraction`` without ``--use-llm`` both send ``external: false`` and provider ``local``.
- `_glm_settings(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 205) — The vault's ``[ingest.pdf.glm_ocr]`` settings (not hashed); loading the config also loads the machine's settings.env, where the key lives.
- `_glm_backend(ctx: JobContext, pdf_config: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 217)
- `_hosted_marker_selected(pdf_config: Mapping[str, Any], *, glm_selected: bool=False) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 225) — The explicit Datalab debug runtime: Marker runs on Datalab's servers (only when GLM-OCR, which ``auto`` prefers, is not selected).
- `_is_document(fetched: FetchedBytes, category: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 237) — A PDF, PNG or JPG: read by the document extractors (GLM-OCR, Marker, pypdf), whatever page or link it came from.
- `_image_config(pdf_config: dict[str, Any], fetched: FetchedBytes) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 249) — Only GLM-OCR reads a PNG/JPG: a PDF-only engine choice (the native PDF model, Marker, pypdf) reads an image the automatic way.
- `_document_extractor(ctx: JobContext, pdf_config: Mapping[str, Any], fetched: FetchedBytes) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 260) — The extractor for a PDF/PNG/JPG import, its upload guarded.
- `_extraction_interrupt(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 335) — Checked before each request GLM-OCR sends (every window, every retry; second review F4): a cancelled import stops there (never a fallback; the runner records the job as cancelled).
- `_upload_allowed(ctx: JobContext, flow: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 352)
- `_refuse_local_repair_of_an_image() -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 392)
- `_guard_file_upload(ctx: JobContext, flow: str, *, plain_message: str | None=None, details: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 398) — Before a whole file leaves the computer (UX Phase 1 review F1): an Add (which asked the learner nothing per book) uploads only after the separate OK for whole files (spec §6.6: the connection's OK covers passages and answers only).
- `_extract_pdf_locally(fetched: FetchedBytes, extractor: Any, pdf_config: Mapping[str, Any], context: Any) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 418) — Run the extractor with the registry's fallback chain (§2.9): under ``auto``, GLM-OCR degrades to local Marker or pypdf and Marker to pypdf, each with a health flag; an explicitly chosen engine fails as itself.
- `_found_no_text(exc: BaseException) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 435) — A local reading that found no text layer at all (a scanned PDF).
- `_audio_ingest_config(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 640) — The vault's [ingest.audio] settings (defaults when the vault is gone).
- `_native_readiness(ctx: JobContext, modality: str, *, requested: bool | None=None) -> tuple[Any, bool] | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 662) — The shared readiness judgement (learnloop.ai.native_media) for this vault plus the ``fallback_when_unavailable`` opt-in, read from ONE config load so the two can never come from different versions of learnloop.toml.
- `_route_from_readiness(readiness: Any) -> NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 681)
- `class _NativeDecision` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 690) — What happens to media whose modality is routed natively.
- `_decide_native(ctx: JobContext, modality: str, *, requested: bool | None=None, unavailable_code: str) -> _NativeDecision | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 702) — PURE config decision shared by identity and extraction.
- `_add_health_flag(ir: Any, flag: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 736)
- `_native_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 742)
- `_transcription_media_route(ctx: JobContext) -> NativeMediaRoute | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 764) — Resolve an explicitly configured chat-transcription route without I/O.
- `_transcription_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 806) — Build the configured transcription client through the composition root.
- `_audio_filename(fetched: FetchedBytes) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 839)
- `_extract_audio(fetched: FetchedBytes, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 857) — Audio → timestamped transcript → the same time_range IR captions use.
- `_extract_audio_transcription(fetched: FetchedBytes, ctx: JobContext, chat_format: str | None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 890) — The non-native audio path: the dedicated transcription route, else the endpoint.
- `_extract_audio_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute, chat_format: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 934)
- `_extract_audio_routed(fetched: FetchedBytes, ctx: JobContext, config: Any, route: NativeMediaRoute, chat_format: str | None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 963) — Transcribe through the dedicated task route with no endpoint fallback.
- `_chat_transcript_to_ir(transcript: Any, ctx: JobContext, *, provider_label: str, empty_code: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1014) — Chat-model MediaTranscript segments → the same time_range IR the endpoint transcription path produces (shared native/routed-chat tail).
- `_extract_pdf_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1047) — PDF → chat file part → Markdown → IR ([ingest.pdf] engine "native").
- `_caption_cues(text: str) -> list[dict[str, Any]] | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1088) — Decode fetched YouTube caption bytes ({"cues": [...]} or a bare list).
- `_html_to_markdown(raw_html: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1110) — Readable-body markdown from raw HTML (same engine as the legacy path).
- `_routed_task_client(ctx: JobContext, task: str, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1308)
- `class _InventoryInterruptGroup` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1337) — One job-scoped interrupt hook covering its active inventory clients.
- `class _RunnerMailbox` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1380) — Carry inventory workers' requests to the runner thread and back.
- `_ingest_budgets(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1697) — Load vault budgets, retaining service defaults for isolated workers/tests.
- `_inventory_inputs(ctx: JobContext, payload: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1709) — Resolve public import→inventory shorthand from the completed dependency.
- `_effective_inventory_inputs(repo: Repository, extraction_id: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1732) — Fold explicit same-role ``merge_with_next`` groups into one model input.
- `_synthesis_progress(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1920) — A ProgressFn bridging create_study_map to the durable job heartbeat.
- `_record_import_source(ctx: JobContext, source_id: str, revision_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2006) — Name the book on its import once the book exists (GLM-OCR third review F2): a link Add's or a plain import's job learns its book only here, and a failed one has no result, so without it the book's card never finds the import that waits for an OK.
- `_note_carry_owed(ctx: JobContext, revision_id: str, extraction_id: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2023) — Before a reading of a revision that already has one completes (or a cached one is carried again): the job's payload names the carry-over it owes (re-read safety, Codex review F7; ``reread.carry_owed``).
- `_carry_noted(ctx: JobContext, extraction_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2039)
- `_actual_model_versions(identity: Mapping[str, Any], ir: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2242) — The model versions of the extractor that really read the document.
- `_queue_due_replay(host: Any, runner: Any, newest: Mapping[str, Any] | None, now: datetime | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2403) — Local retrieval P2 (spec §9.3; Codex review F10): the nightly teacher replay for a library that is fully indexed.
- `_source_vectors_failure(status: str, report: Mapping[str, Any]) -> IngestRunnerError` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2567) — The workflow failure for an unsuccessful source backfill (Codex review F4).
- `_compose_display_title(title: str | None, authors: Sequence[str]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2604) — Assemble the artifact's stored label: "<title> — <author>" when both are known, the title alone when there is no author, and ``None`` (→ URL fallback) when the fetch captured no title at all.
- `_legacy_ir_extraction_id(ctx: JobContext) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2667)
- `_legacy_ir_markdown(ctx: JobContext, extraction_id: str | None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2682) — Render the IR from this job's completed ``import`` dependency, if any (§2.3).
- `_repair_pdf_config(options: Mapping[str, Any], pages: list[int]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2829)
- `_validate_page_selection(raw_bytes: bytes, pages: list[int]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2844) — Refuse out-of-range page selections BEFORE any expensive extraction.
- `_pdf_page_count(raw_bytes: bytes) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2867)
- `_normalize_pages(raw: Any) -> list[int]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2884)
- `_latest_completed_extraction(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2904)
- `_units_touching(ir: Any, pages: list[int]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2913)
- `_reader_source_sets(vault_root: Path) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2955) — The vault's source sets, read when a Reader request is sent (the held-out partition reads them; exam protection, Codex review F3).
- `_refuse_held_out_reader_material(ctx: JobContext, extraction_id: str, span_ids: Sequence[str]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2968) — Exam protection (2026-10-13): a Reader check over held-out material (the one held-out partition, read with the vault's source sets) is refused before any model call, and before a check authored before the mark is handed back (code ``exam_material``).
- `_section_span_ids(repository: Repository, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2983) — Every block of one guide section (the quick check's own derivation), or [].
- `_passage_span_ids(repository: Repository, extraction_id: str, anchors: Sequence[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2993) — The anchors and every block of the passage check's view of them.
- `_paid_quick_check_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3003) — The client of a paid passage check (an inquiry's or a selection's), resolved for that feature.
- `_exercise_import_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3018) — The authoring client of an exercise import, resolved for that feature (re-review F2).
- `_passage_check_spend(ctx: JobContext) -> RQC.PassageCheckSpend` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3033) — The vault's admission settings for one passage check ([reader_inquiry]).
- `_pause_while_inquiry_held(ctx: JobContext, seconds: float) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3052) — Wait between polls of a held inquiry claim (a seam for tests).
- `_inquiry_owner_ended(repo: Repository, owner: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3058) — True when the claim's owner is an ingest job that has finished: it was expired, failed or cancelled after claiming, so its claim is abandoned.
- `_handle_reader_inquiry_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3067) — RW1a: author the reconnect line's quick check for one inquiry's root passage.
- `_handle_reader_selection_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3141) — RW1b: author one active-reading question on a selection (next step, why step, assumptions, reconstruct).
- `_record_reader_import_keys(ctx: JobContext, result: dict[str, Any], *, extraction_id: str, raw_selection: dict[str, Any], source_id: str | None, revision_id: str | None) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3275) — Canonical sources S1 (§7.3a): the Reader's import records its key status.
- `_verify_quietly(root: Path, repository: Repository, rows: list[dict[str, str]], trigger: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3310)
- `_record_commission_skip(ctx: JobContext, commission_id: str, rule: str) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3414) — Write :func:`ad_commission_skip_record` in a short transaction of its own, outside every AD operation; never raises.
- `_handle_ad_commission(ctx: JobContext, lo_ids: list[str], commission_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3430) — One item at an open AD commission's point, through the ordinary generation path and its gates (spec_adaptive_difficulty_v1 §6.1 "runs in the background", §7.1, §7.4).
- `_run_reading_sweep(host: 'weakref.ref[DurableIngestJobs]') -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3963) — The reading sweep thread.
- `_reading_due_at(retry_at: str | None) -> datetime | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3990) — When a pending reading request is due: its retry time, or ``None`` (due now) when it has none or one that does not parse or convert to UTC (``0001-01-01T00:00:00+01:00`` overflows, reading-hardening verify N2), so no stored value can keep a request from ever being due.
- `_iso(moment: datetime | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5675) — ``moment`` (default: now) as the ISO UTC text reading requests store.
- `_job_view(job: dict[str, Any], repo: Repository, *, depends_on: list[str] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5694) — One job as the Batch-progress screen needs it: the checkpoint ladder, live phase/window counts, actual usage, and any waiting_for_input payload (§5.7).
- `_batch_view(batch: dict[str, Any], jobs: list[dict[str, Any]], repo: Repository, *, dependencies_by_job: dict[str, list[str]] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5754)
- `_failed_rung_request_id(job: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5794)
- `_compat_status(status: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5805) — Map the durable status vocabulary onto the legacy job vocabulary the existing frontend/handlers expect (queued|running|completed|failed|cancelled).
- `_compat(job: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 5812)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `DurableIngestJobs`; statically calls `DurableIngestJobs`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `_pdf_page_count`; statically calls `_pdf_page_count`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `module`; statically calls `append`, `get`, `values`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `IngestJobManager`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `APPLYING_JOB_TYPES`, `ActiveIngestJobError`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `APPLYING_JOB_TYPES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `contract_on`; calls `contract_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `ad_operation`, `is_denial`; calls `ad_operation`, `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `make_video_generation_client`; calls `make_video_generation_client`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`; calls `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`
- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `native_modality_readiness`; calls `native_modality_readiness`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `priced_by`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`; calls `SpendCancelled`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `INTERRUPT`, `MEDIA_TRANSCRIPTION`, `interrupt_callback`; calls `interrupt_callback`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AudioIngestConfig`, `IngestBudgetsConfig`; calls `AudioIngestConfig`, `IngestBudgetsConfig`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `ConceptAnimationError`, `generate_concept_animation`; calls `generate_concept_animation`
- [[Reference/Modules/learnloop/content/authoring/draft_validation|learnloop.content.authoring.draft_validation]] — imports `draft_validator`, `duration_estimator`; calls `draft_validator`, `duration_estimator`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `module`; calls `import_exercises`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`; calls `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `RungVariantError`, `generate_rung_variant`; calls `generate_rung_variant`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `PRICE_SETTING`, `module`; calls `import_source_exercise`, `record_reader_import`, `verify_item_key`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `ADD_SOURCE_PRIORITY`, `ADD_SOURCE_WORKFLOW`, `AUTO_BUILD_BATCH_PREFIX`, `AUTO_BUILD_WORKFLOW`, `AUTO_STUDY_MAP_JOB`, `AddSourceOptions`, `BUILD_PRIORITY`, `admit_auto_build_job`, `after_auto_build`, `auto_apply_allowed`, `file_upload_allowed`, `module`, `pdf_metadata_title`, `run_auto_study_map`; calls `AddSourceOptions`, `act_on_reading_request`, `admit_auto_build_job`, `after_auto_build`, `auto_apply_allowed`, `file_upload_allowed`, `pdf_metadata_title`, `run_auto_study_map`, `settle_reading_for_cancelled_batch`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `CARRY_DONE_KEY`, `CARRY_OWED_KEY`, `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`; calls `adopt_revision`, `carry_over`, `mark_carried`, `original_bytes`, `owes_carry`, `revision_bytes`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `CHECKPOINT_LADDER`, `FetchedBytes`, `Handler`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobContext`, `JobSpec`, `RunnerServices`, `derive_batch_status`, `effective_ingest_job_status`; calls `FetchedBytes`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobSpec`, `derive_batch_status`, `effective_ingest_job_status`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `ingest_canonical_source`, `module`; calls `fetch_source`, `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`, `scope_only_among`; calls `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`, `scope_only_among`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `default_inventory_profile`; calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `register_source_revision`; calls `register_source_revision`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `APPEND_INPUT_OVER_CEILING`, `append_source`, `subject_has_applied_study_map`; calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `create_study_map`, `revalidate_synthesis_candidate`; calls `create_study_map`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `InventoryResult`, `PreparedInventory`, `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`; calls `current_inventory_identity`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`, `window_checkpoint`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_scope_groups`; calls `effective_scope_groups`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `commission_batch_id`; calls `commission_batch_id`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `write_decision`; calls `write_decision`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `RichJobStopped`, `run_rich_job`; calls `run_rich_job`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `exam_ingest_instructions`; calls `exam_ingest_instructions`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `ExtractionFallbackFailed`, `MarkerUnavailableError`, `captions_to_ir`, `extract_with_fallback`, `fallback_model_versions`, `local_pdf_extractor`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`; calls `captions_to_ir`, `extract_with_fallback`, `fallback_model_versions`, `local_pdf_extractor`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`; calls `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `UNAVAILABLE_MESSAGE`, `estimate`, `is_image_document`, `selected_backend`; calls `estimate`, `is_image_document`, `selected_backend`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `youtube_oembed_metadata`, `youtube_video_id`; calls `youtube_oembed_metadata`, `youtube_video_id`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `extraction_request_hash`, `extraction_result_hash`; calls `extraction_request_hash`, `extraction_result_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `IR_SCHEMA_VERSION`, `compose_extraction_runs`, `render_ir_markdown`; calls `compose_extraction_runs`, `render_ir_markdown`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] — imports `TranscriptionFailed`, `TranscriptionUnavailable`, `transcribe_audio`; calls `transcribe_audio`
- [[Reference/Modules/learnloop/ingest/transcripts|learnloop.ingest.transcripts]] — imports `TranscriptCue`, `detect_transcript_format`, `parse_transcript`; calls `TranscriptCue`, `detect_transcript_format`, `parse_transcript`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `refit_posteriors`; calls `refit_posteriors`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `REPLAY_EVERY_HOURS`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `current_trace`, `is_code`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `author_inquiry_quick_check`, `author_quick_check`, `author_selection_question`, `extraction_sections`, `passage_check_spend`, `passage_view`, `selection_claim_key`, `selection_question`, `selection_view`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `drain_requests`, `model_synthesis`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `clear_cache`; calls `clear_cache`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `FALLBACK_JOB`, `backfill_fallback_vectors`, `fallback_reason`; calls `backfill_fallback_vectors`, `fallback_reason`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `refresh_due`; calls `refresh_due`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `DEFERRED_STATUSES`, `INDEX_JOB`, `run_local_index`; calls `run_local_index`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `ON_EXTRACT_JOB`, `covered_learning_objects`, `module`, `on_extract_reason`; calls `covered_learning_objects`, `on_extract_reason`, `rejudge_on_extract`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `LIVE_JOB_STATUSES`, `SOURCE_VECTORS_JOB`, `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`; calls `auto_backfill_reason`, `backfill_owed`, `backfill_source_vectors`, `target_extraction`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `resolver_active`; calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `replay_due`; calls `replay_due`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionError`, `PromotionNoItemError`, `promote_tutor_question`; calls `promote_tutor_question`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `contextvars`, `dataclasses`, `datetime`, `hashlib`, `io`, `json`, `logging`, `os`, `pathlib`, `queue`, `re`, `threading`, `time`, `types`, `typing`, `urllib`, `weakref`
- Third party: `pypdf`, `trafilatura`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/glm_ocr_helpers.py](../../../../../../../tests/glm_ocr_helpers.py) — direct import
- [tests/reading_request_sweep_helpers.py](../../../../../../../tests/reading_request_sweep_helpers.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished`
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`
  - `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires`
- [tests/test_coverage_on_extract.py](../../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_an_extraction_queues_the_job_only_while_both_switches_are_on`
  - `test_one_live_job_at_a_time`
  - `test_the_handler_is_registered_and_known`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call`
- [tests/test_deliverable_codex_review.py](../../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f7_a_running_job_does_not_swallow_a_new_extraction`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_check_over_held_out_material_is_refused_before_any_model_call`
  - `test_a_reader_import_of_held_out_material_is_refused_before_any_model_call`
- [tests/test_exam_protection_review.py](../../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_reader_import_of_a_held_out_signal_is_refused`
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other`
  - `test_an_image_import_needs_glm_and_reads_with_it`
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
  - `test_identity_hashes_the_choice_not_endpoints_prices_or_timeouts`
  - `test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer`
  - `test_r2_f4_cancelling_stops_the_windows_not_yet_sent`
  - `test_remote_documents_download_raw_so_nothing_is_read_before_the_ok`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged`
- [tests/test_ingest_jobs.py](../../../../../../../tests/test_ingest_jobs.py) — direct import
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
  - `test_audio_extract_routes_transcription_to_time_range_ir`
  - `test_audio_extraction_identity_tracks_model_and_endpoint`
  - `test_audio_oversize_rejected_before_any_upload`
  - `test_audio_transcription_mode_uses_endpoint_without_native_route`
  - `test_audio_transcription_unavailable_is_typed_retryable`
  - `test_compose_display_title_variants`
  - `test_default_inventory_client_defaults_to_codex_and_errors_when_unavailable`
  - `test_default_inventory_client_routes_via_canonical_ingest`
  - `test_default_synthesis_client_resolves_openrouter_in_inherited_new_vault`
  - `test_explicit_transcription_route_uses_named_profile_without_legacy_switch`
  - `test_fetch_metadata_only_resolves_youtube`
  - `test_native_audio_failure_is_typed_and_never_switches_routes`
  - `test_native_audio_route_transcribes_via_chat_provider`
  - `test_native_audio_unready_fails_closed_by_default`
  - `test_native_audio_unready_falls_back_when_opted_in`
  - `test_native_audio_unready_route_is_irrelevant_for_non_chat_containers`
  - `test_native_audio_unsupported_container_falls_back_to_endpoint`
  - `test_native_pdf_engine_extracts_markdown_via_chat_provider`
  - `test_native_pdf_engine_rejects_a_repair_page_range`
  - `test_native_pdf_engine_rejects_page_selection`
  - `test_native_pdf_engine_without_capable_route_is_typed`
  - `test_native_pdf_fallback_when_unavailable_uses_local_with_health_flag`
  - `test_native_pdf_rejects_oversized_file`
  - `test_native_route_takes_precedence_over_openrouter_transcription_setting`
  - `test_openrouter_transcription_missing_key_is_typed`
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
  - `test_openrouter_transcription_unsupported_container_errors`
  - `test_routed_transcription_keeps_the_chat_upload_size_cap`
  - `test_same_vault_rebind_preserves_kill_codex_interrupt_handle`
  - `test_transcription_route_never_falls_back_to_an_unconsented_provider`
  - `test_web_import_routes_html_normalizer_not_raw_text`
  - `test_youtube_import_routes_caption_cues_to_time_range_ir`
- [tests/test_ingest_transcripts.py](../../../../../../../tests/test_ingest_transcripts.py) — direct import
  - `test_default_extract_routes_caption_text_to_transcript_ir`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_parallel_inventory_drains_checkpoints_and_stops_new_units_after_failure`
- [tests/test_inventory_runner_mailbox.py](../../../../../../../tests/test_inventory_runner_mailbox.py) — direct import
  - `test_keyboard_interrupt_during_parallel_inventory_releases_waiting_workers`
  - `test_parallel_inventory_notices_cancellation_without_polling_the_database_constantly`
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_an_import_the_retired_choice_refused_offers_to_get_it_ready`
  - `test_whole_file_extraction_is_no_longer_narrowed_for_the_retired_choice`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged`
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r6_verify_f7_a_finished_exercise_job_read_after_its_region_is_held_out_never_delivers_it`
  - `test_use_this_one_on_a_fallback_exercise_runs_the_readers_import_unchanged`
- [tests/test_local_index.py](../../../../../../../tests/test_local_index.py) — direct import
  - `test_a_deferred_index_job_is_woken_at_its_retry_time`
  - `test_a_queued_index_job_whose_worker_never_started_is_started_by_the_sweep`
  - `test_an_index_obligation_that_cannot_be_queued_fails_the_extraction_retryably`
  - `test_extraction_queues_the_index_jobs_only_while_their_switches_are_on`
- [tests/test_mobile_v4_reader.py](../../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
  - `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_the_reader_imports_background_key_check_never_uses_the_grant`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_query_student.py](../../../../../../../tests/test_query_student.py) — direct import
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_quick_add_batches_take_queue_priority`
- [tests/test_reader_active_reading.py](../../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_the_job_refuses_held_out_material_before_any_call`
  - `test_the_job_writes_the_question_once`
- [tests/test_reader_passage_check.py](../../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_check_held_by_a_live_job_waits_for_it_and_returns_its_question`
  - `test_a_check_held_past_the_wait_fails_retryably_and_never_completes_without_a_question`
  - `test_a_claim_left_by_a_crashed_job_is_taken_over_by_the_next_job_at_once`
  - `test_a_second_request_while_one_is_live_joins_its_job`
  - `test_a_spend_refusal_says_whether_the_price_is_missing_or_the_check_is_over_its_cap`
  - `test_the_job_fails_closed_with_a_named_reason_when_isolation_is_unavailable`
  - `test_the_job_reports_a_refusal_as_its_error_code_and_sends_nothing`
  - `test_the_vaults_spend_settings_reach_the_check`
- [tests/test_reader_progression.py](../../../../../../../tests/test_reader_progression.py) — direct import
  - `test_practice_expansion_queue_preserves_reader_source_refs`
- [tests/test_reader_reconnect.py](../../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_quick_check_job_authors_the_inquiry_row`
  - `test_reconnect_rpcs_round_trip`
  - `test_the_quick_check_read_reports_its_durable_jobs_state`
- [tests/test_reading_hardening_2_fixes.py](../../../../../../../tests/test_reading_hardening_2_fixes.py) — direct import
  - `test_f1_a_build_queued_just_before_the_process_ended_runs_at_the_next_start`
  - `test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone`
- [tests/test_reading_hardening_landing.py](../../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_the_section_check_job_still_refuses_held_out_material`
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
- [tests/test_remaining_decision_records.py](../../../../../../../tests/test_remaining_decision_records.py) — direct import
  - `test_a_commission_job_that_generated_nothing_says_why`
  - `test_every_b8_builder_passes_the_prose_check_with_learner_text_planted`
- [tests/test_rw1a_composition.py](../../../../../../../tests/test_rw1a_composition.py) — direct import
  - `test_the_vaults_route_effort_reaches_the_check`
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`
  - `test_video_renderer_request_completes_through_the_queue`
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
  - `test_a_queued_passage_check_runs_for_a_book_with_the_retired_keep_local`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f1_sending_a_whole_recording_out_waits_for_its_own_ok`
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
