---
title: "learnloop.content.pipeline.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/jobs.py"
source_paths:
  - "src/learnloop/content/pipeline/jobs.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.jobs` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Concrete ingest jobs and the durable host shared by CLI and sidecar (§6.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py) |
| Source lines | 3501 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `default_fetch(source: str, category: str, ctx: JobContext) -> FetchedBytes` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 87) — Read raw bytes for one acquisition.
- `default_extract(fetched: FetchedBytes, category: str, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 163) — Produce Document IR from fetched bytes using the M1 extractor providers.
- `default_extraction_identity(fetched: FetchedBytes, category: str, ctx: JobContext) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 253) — Describe the chosen extractor before running it, making cache hits cheap.
- `class NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 359) — A resolved native-multimodal route: which chat provider ingests media.
- `default_run_legacy_ingest(*, vault_root: Path, source: str, subject_id: str, mode: str, progress: Callable[[str, dict[str, Any]], None] | None, clock: Clock | None, ir_markdown: str | None=None, **_ignored: Any) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 764) — Run the legacy one-shot pipeline in-process with a ready provider client.
- `inventory_client_identity(client: Any) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 808)
- `default_inventory_identity(ctx: JobContext) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 815) — Resolve the primary inventory cache key without a runtime probe.
- `default_inventory_client(ctx: JobContext, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 837) — Resolve the unit-inventory/quick-check client through ai routing (§7).
- `default_synthesis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 870) — Resolve the canonical-ingest route for judgment-heavy synthesis.
- `default_animation_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 886) — Resolve the animation route (default: the medium-effort profile) — any configured provider works; run_concept_animation is getattr-discovered.
- `default_rung_variant_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 893) — Resolve the rung_variant route (default: the fast low-effort profile).
- `default_promotion_analysis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 903) — Fast classification/dedup pass for a durable promotion request.
- `default_promotion_authoring_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 917) — Judgment-heavy practice generation follows the configured authoring route.
- `handle_inventory(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1003) — inventory: role-aware per-unit inventories for the selected units (§7).
- `handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1359) — bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).
- `handle_append_synthesis(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1481) — append_synthesis: bounded reconciliation against an existing study map.
- `handle_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1519) — import: fetch -> register artifact/revision -> extract to IR -> persist -> health.
- `handle_legacy_ingest(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1671) — legacy_ingest: wrap the existing one-shot pipeline as one durable job so the current single-source UX keeps working (Quick add compatibility, §6.1).
- `handle_extraction_repair(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1746) — extraction_repair: a consent-gated, page-range re-extraction (§2.5).
- `handle_reader_quick_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1964) — Author one section-boundary quick check (reader producer slice).
- `handle_reader_exercise_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1989) — reader_exercise_import: author the learner's selected textbook exercise(s) into complete, schedulable PracticeItems.
- `handle_practice_expansion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2025) — practice_expansion: per-LO item generation (reader-first seeding).
- `handle_goal_population(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2073) — Generate and apply the missing practicable supply for one active goal.
- `handle_question_promotion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2164) — Run one persisted Open-question → practice request.
- `handle_rung_variant(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2263) — rung_variant: author one learner-requested easier/harder sibling item.
- `handle_concept_animation(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2295) — concept_animation: author + validate + render one explainer scene.
- `class ActiveIngestJobError(RuntimeError)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2383)
  - `__init__(self, job_id: str) -> None` (line 2384; internal)
- `class DurableIngestJobs` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2389) — Enqueues single-source ingests into the durable queue and reads their state.
  - `__init__(self) -> None` (line 2392; internal)
  - `bind(self, repository: Repository, vault_root: Path, *, clock: Clock | None=None, services: RunnerServices | None=None, lease_ttl_seconds: int=120, heartbeat_interval_seconds: float=15, poll_interval_seconds: float=1.0, background: bool | None=None, reader_synth_client_factory: Any=None) -> None` (line 2412; public) — Attach the wrapper to a loaded vault.
  - `_require_runner(self) -> IngestRunner` (line 2476; internal)
  - `start(self, vault_root: Path, source: str, subject_id: str, mode: Literal['canonical', 'exam'], pdf_engine: str | None=None) -> dict[str, Any]` (line 2483; public)
  - `get(self, job_id: str) -> dict[str, Any] | None` (line 2527; public)
  - `list(self) -> list[dict[str, Any]]` (line 2532; public)
  - `cancel(self, job_id: str) -> dict[str, Any] | None` (line 2537; public)
  - `needs_reload(self, job_id: str) -> bool` (line 2547; public)
  - `mark_reloaded(self, job_id: str) -> None` (line 2556; public)
  - `shutdown(self) -> None` (line 2559; public)
  - `enqueue_import(self, sources: list[str], *, subject_id: str | None=None, inventory: bool=False, estimate: dict[str, Any] | None=None, page_selection: list[int] | None=None, page_selections: dict[str, list[int]] | None=None, reader_disabled_sources: set[str] | frozenset[str] | None=None, pdf_engine: str | None=None, priority: int=0) -> str` (line 2572; public) — Enqueue an Import (or Import & inventory) batch (§6.1).
  - `enqueue_extraction_repair(self, *, revision_id: str, pages: list, repair_options: dict[str, Any] | None, consent: dict[str, Any], parent_extraction_id: str | None=None, subject_id: str | None=None) -> str` (line 2616; public) — Enqueue a consent-gated extraction-repair batch (§2.5).
  - `enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str) -> str` (line 2648; public) — Enqueue one section's quick-check authoring (reader producer slice).
  - `enqueue_reader_exercise_import(self, *, extraction_id: str, raw_selection: dict[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None) -> str` (line 2665; public) — Enqueue authoring of the learner's selected textbook exercise(s).
  - `enqueue_practice_expansion(self, *, learning_object_ids: list[str], subject_id: str | None=None, reason: str | None=None, source_refs: list[dict[str, Any]] | None=None) -> str` (line 2702; public) — Enqueue per-LO practice generation (reader-first progressive seeding).
  - `enqueue_goal_population(self, *, goal_id: str) -> str` (line 2733; public) — Enqueue durable goal-scoped practice authoring from the wizard.
  - `enqueue_rung_variant(self, *, request_id: str, subject_id: str | None=None) -> str` (line 2745; public) — Enqueue one learner-requested variant authoring (interactive band — the learner is waiting on it, like a quick-add build).
  - `enqueue_question_promotion(self, *, event_id: str, subject_id: str | None=None) -> str` (line 2759; public) — Enqueue a durable Open-question analysis/authoring request.
  - `enqueue_concept_animation(self, *, animation_id: str, subject_id: str | None=None) -> str` (line 2777; public) — Enqueue one explainer-animation generation (interactive band — the learner clicked generate and is watching the status).
  - `enqueue_inventory(self, *, extraction_id: str, units: list[dict[str, Any]], subject_id: str | None=None, source_set_id: str | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, priority: int=0) -> str` (line 2791; public) — Enqueue a role-aware unit-inventory batch (§7).
  - `enqueue_quick_add_build(self, *, extraction_id: str, units: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 2824; public) — Enqueue the Quick-add build batch (§1): inventory(selected units) then bootstrap_synthesis over the freshly-created source set, as one batch that drains ahead of bulk work.
  - `enqueue_source_set_build(self, *, members: list[dict[str, Any]], source_set_id: str, subject_id: str | None=None, brief: dict[str, Any] | None=None, mode: str='auto', input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 2874; public) — Enqueue a study-map build batch for an EXISTING source set (§1/§8): one inventory job per member (over its scoped units) followed by a bootstrap_synthesis job that depends on all of them, so gates only run once every member's units carry inventories.
  - `enqueue_source_set_append(self, *, members: list[dict[str, Any]], source_set_id: str, new_revision_ids: list[str] | None=None, change_kind: str='source_added', subject_id: str | None=None, brief: dict[str, Any] | None=None, input_budget_tokens: int | None=None, output_budget_tokens: int | None=None, synthesis_budgets: dict[str, int] | None=None, unlimited_token_budget: bool=False, priority: int=QUICK_ADD_PRIORITY) -> str` (line 2941; public) — Enqueue a bounded-neighborhood APPEND batch for a collection whose subject already carries a study map (§10).
  - `retry_synthesis(self, batch_id: str, *, synthesis_budgets: dict[str, int] | None=None, reuse_candidate: bool=False, repair_candidate: bool=False, repair_ops: list[dict[str, Any]] | None=None, unlimited_token_budget: bool=False) -> dict[str, Any]` (line 3008; public) — Retry only a failed synthesis stage with revised execution ceilings.
  - `get_batch(self, batch_id: str) -> dict[str, Any] | None` (line 3083; public)
  - `list_batches(self, limit: int=_RECENT_LIMIT) -> list[dict[str, Any]]` (line 3090; public)
  - `cancel_batch(self, batch_id: str) -> dict[str, Any] | None` (line 3118; public)
  - `interrupt_codex(self, job_id: str | None=None) -> dict[str, Any]` (line 3125; public) — Interrupt one live Codex call while keeping the sidecar process alive.
  - `resume_batch(self, batch_id: str) -> dict[str, Any] | None` (line 3155; public)
  - `drain_foreground(self) -> int` (line 3165; public) — Drain the queue synchronously (tests + CLI-less contexts).
  - `_ensure_worker(self) -> None` (line 3170; internal)
  - `_worker_loop(self) -> None` (line 3198; internal)
  - `_quick_check_worker_loop(self) -> None` (line 3226; internal) — Drain independent quick checks beside the serialized vault writer.
  - `kick_reader_drain(self) -> None` (line 3260; public) — Ensure queued demand-paged reader requests get drained.
  - `_drain_reader_requests(self, runner: IngestRunner) -> int` (line 3283; internal) — Drain queued reader requests with a real synthesize client.
  - `_resolve_reader_client(self, runner: IngestRunner) -> Any` (line 3303; internal)
  - `_legacy_job_for_batch(runner: IngestRunner, batch_id: str) -> dict[str, Any]` (line 3332; internal) — The synthesis job the frontend polls (the batch also holds an import job).
  - `_active_job_locked(self, runner: IngestRunner) -> dict[str, Any] | None` (line 3341; internal)

### Module constants

- `_MAX_INVENTORY_WORKERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 58)
- `INGEST_CODEX_TIMEOUT_SECONDS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 59)
- `_LEGACY_PHASE_TO_LADDER` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 61)
- `_LEGACY_PHASE_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 69)
- `_ROUTED_AUDIO_FORMAT_MESSAGE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 507)
- `_SYNTH_STAGE_PHASE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1455)
- `DEFAULT_HANDLERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2332)
- `_LEGACY_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2351)
- `APPLYING_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2356)
- `_ACTIVE_STATUSES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2372)
- `_RECENT_LIMIT` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2373)
- `QUICK_ADD_PRIORITY` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2378)
- `_PARALLEL_JOB_TYPES` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2379)
- `_QUICK_CHECK_WORKERS` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 2380)
- `_LADDER_BY_JOB_TYPE` ([src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3352)

## Internal implementation anchors

- `_optional_int(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 78)
- `_fetch_metadata(source: str, category: str) -> tuple[str | None, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 120) — Best-effort human-readable (title, authors) for the fetched source.
- `_pdf_payload_config(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 140) — The effective PDF extraction config for one import job.
- `_audio_ingest_config(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 346) — The vault's [ingest.audio] settings (defaults when the vault is gone).
- `_native_media_route(ctx: JobContext, modality: str) -> NativeMediaRoute | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 367) — PURE config decision: is native multimodal active for this modality?
- `_native_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 400)
- `_transcription_media_route(ctx: JobContext) -> NativeMediaRoute | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 421) — Resolve an explicitly configured chat-transcription route without I/O.
- `_transcription_media_client(ctx: JobContext, route: NativeMediaRoute) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 463) — Build the configured transcription client through the composition root.
- `_audio_filename(fetched: FetchedBytes) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 496)
- `_extract_audio(fetched: FetchedBytes, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 514) — Audio → timestamped transcript → the same time_range IR captions use.
- `_extract_audio_native(fetched: FetchedBytes, ctx: JobContext, route: NativeMediaRoute, chat_format: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 572)
- `_extract_audio_routed(fetched: FetchedBytes, ctx: JobContext, config: Any, route: NativeMediaRoute, chat_format: str | None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 601) — Transcribe through the dedicated task route with no endpoint fallback.
- `_chat_transcript_to_ir(transcript: Any, ctx: JobContext, *, provider_label: str, empty_code: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 652) — Chat-model MediaTranscript segments → the same time_range IR the endpoint transcription path produces (shared native/routed-chat tail).
- `_require_native_pdf_route(ctx: JobContext) -> NativeMediaRoute` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 685)
- `_extract_pdf_native(fetched: FetchedBytes, ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 698) — PDF → chat file part → Markdown → IR ([ingest.pdf] engine "native").
- `_caption_cues(text: str) -> list[dict[str, Any]] | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 729) — Decode fetched YouTube caption bytes ({"cues": [...]} or a bare list).
- `_html_to_markdown(raw_html: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 751) — Readable-body markdown from raw HTML (same engine as the legacy path).
- `_routed_task_client(ctx: JobContext, task: str, *, codex_timeout_seconds: int | None=None) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 931)
- `class _InventoryInterruptGroup` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 960) — One job-scoped interrupt hook covering its active inventory clients.
- `_ingest_budgets(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1250) — Load vault budgets, retaining service defaults for isolated workers/tests.
- `_inventory_inputs(ctx: JobContext, payload: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1262) — Resolve public import→inventory shorthand from the completed dependency.
- `_effective_inventory_inputs(repo: Repository, extraction_id: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1285) — Fold explicit same-role ``merge_with_next`` groups into one model input.
- `_synthesis_progress(ctx: JobContext)` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1463) — A ProgressFn bridging create_study_map to the durable job heartbeat.
- `_compose_display_title(title: str | None, authors: Sequence[str]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1659) — Assemble the artifact's stored label: "<title> — <author>" when both are known, the title alone when there is no author, and ``None`` (→ URL fallback) when the fetch captured no title at all.
- `_legacy_ir_markdown(ctx: JobContext) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1714) — Render the IR from this job's completed ``import`` dependency, if any (§2.3).
- `_repair_pdf_config(options: Mapping[str, Any], pages: list[int]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1859)
- `_validate_page_selection(raw_bytes: bytes, pages: list[int]) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1874) — Refuse out-of-range page selections BEFORE any expensive extraction.
- `_pdf_page_count(raw_bytes: bytes) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1897)
- `_normalize_pages(raw: Any) -> list[int]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1914)
- `_latest_completed_extraction(repo: Repository, revision_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1934)
- `_units_touching(ir: Any, pages: list[int]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1943)
- `_not_implemented_handler(job_type: str) -> Handler` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 1955)
- `_job_view(job: dict[str, Any], repo: Repository, *, depends_on: list[str] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3359) — One job as the Batch-progress screen needs it: the checkpoint ladder, live phase/window counts, actual usage, and any waiting_for_input payload (§5.7).
- `_batch_view(batch: dict[str, Any], jobs: list[dict[str, Any]], repo: Repository, *, dependencies_by_job: dict[str, list[str]] | None=None, rung_requests_by_id: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3419)
- `_failed_rung_request_id(job: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3459)
- `_compat_status(status: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3470) — Map the durable status vocabulary onto the legacy job vocabulary the existing frontend/handlers expect (queued|running|completed|failed|cancelled).
- `_compat(job: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/jobs.py), line 3477)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `DurableIngestJobs`; statically calls `DurableIngestJobs`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `module`; statically calls `append`, `get`, `values`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `IngestJobManager`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `APPLYING_JOB_TYPES`, `ActiveIngestJobError`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `APPLYING_JOB_TYPES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`; calls `MediaTranscriptionContext`, `PdfExtractionContextNative`, `chat_audio_format`, `supports_input_modality`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `INTERRUPT`, `MEDIA_TRANSCRIPTION`, `interrupt_callback`; calls `interrupt_callback`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AudioIngestConfig`, `IngestBudgetsConfig`; calls `AudioIngestConfig`, `IngestBudgetsConfig`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `ConceptAnimationError`, `generate_concept_animation`; calls `generate_concept_animation`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `module`; calls `import_exercises`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`; calls `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `RungVariantError`, `generate_rung_variant`; calls `generate_rung_variant`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `CHECKPOINT_LADDER`, `FetchedBytes`, `Handler`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobContext`, `JobSpec`, `RunnerServices`, `WaitingForInput`, `derive_batch_status`, `effective_ingest_job_status`; calls `FetchedBytes`, `IngestRunner`, `IngestRunnerError`, `JobCancelled`, `JobSpec`, `derive_batch_status`, `effective_ingest_job_status`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `ingest_canonical_source`, `module`; calls `fetch_source`, `ingest_canonical_source`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `default_inventory_profile`; calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `register_source_revision`; calls `register_source_revision`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `append_source`, `subject_has_applied_study_map`; calls `append_source`, `subject_has_applied_study_map`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `StudyMapError`, `create_study_map`, `revalidate_synthesis_candidate`; calls `create_study_map`, `revalidate_synthesis_candidate`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `InventoryExecution`, `InventoryResult`, `PreparedInventory`, `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`; calls `execute_prepared_inventory`, `normalize_profile`, `persist_prepared_inventory`, `prepare_unit_inventory`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_scope_groups`; calls `effective_scope_groups`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `exam_ingest_instructions`; calls `exam_ingest_instructions`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `MarkerUnavailableError`, `PyPdfDocumentExtractor`, `captions_to_ir`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`; calls `PyPdfDocumentExtractor`, `captions_to_ir`, `markdown_to_ir`, `pdf_extractor_for`, `transcript_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`; calls `ExtractionContext`
- [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] — imports `youtube_oembed_metadata`, `youtube_video_id`; calls `youtube_oembed_metadata`, `youtube_video_id`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `extraction_request_hash`, `extraction_result_hash`; calls `extraction_request_hash`, `extraction_result_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `IR_SCHEMA_VERSION`, `compose_extraction_runs`, `render_ir_markdown`; calls `compose_extraction_runs`, `render_ir_markdown`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] — imports `TranscriptionFailed`, `TranscriptionUnavailable`, `transcribe_audio`; calls `transcribe_audio`
- [[Reference/Modules/learnloop/ingest/transcripts|learnloop.ingest.transcripts]] — imports `TranscriptCue`, `detect_transcript_format`, `parse_transcript`; calls `TranscriptCue`, `detect_transcript_format`, `parse_transcript`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `author_quick_check`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `drain_requests`, `model_synthesis`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionError`, `PromotionNoItemError`, `promote_tutor_question`; calls `promote_tutor_question`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `dataclasses`, `io`, `json`, `os`, `pathlib`, `queue`, `re`, `threading`, `typing`, `urllib`
- Third party: `pypdf`, `trafilatura`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_jobs.py](../../../../../../../tests/test_ingest_jobs.py) — direct import
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
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_audio_extract_routes_transcription_to_time_range_ir`
  - `test_audio_extraction_identity_tracks_model_and_endpoint`
  - `test_audio_oversize_rejected_before_any_upload`
  - `test_audio_transcription_unavailable_is_typed_retryable`
  - `test_compose_display_title_variants`
  - `test_default_inventory_client_defaults_to_codex_and_errors_when_unavailable`
  - `test_default_inventory_client_routes_via_canonical_ingest`
  - `test_default_synthesis_client_gives_codex_sdk_an_eight_minute_timeout`
  - `test_default_synthesis_client_resolves_openrouter_in_inherited_new_vault`
  - `test_explicit_transcription_route_uses_named_profile_without_legacy_switch`
  - `test_fetch_metadata_only_resolves_youtube`
  - `test_native_audio_disabled_or_modality_absent_uses_endpoint`
  - `test_native_audio_failure_is_typed_and_never_switches_routes`
  - `test_native_audio_route_transcribes_via_chat_provider`
  - `test_native_audio_unsupported_container_falls_back_to_endpoint`
  - `test_native_pdf_engine_extracts_markdown_via_chat_provider`
  - `test_native_pdf_engine_rejects_page_selection`
  - `test_native_pdf_engine_without_capable_route_is_typed`
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
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_quick_add_batches_take_queue_priority`
- [tests/test_reader_progression.py](../../../../../../../tests/test_reader_progression.py) — direct import
  - `test_practice_expansion_queue_preserves_reader_source_refs`
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`

## Modification guidance

- Change jobs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/jobs.py](../../../../../../../src/learnloop/content/pipeline/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
