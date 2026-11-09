---
title: "learnloop.source_retrieval.local_index"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/local_index.py"
source_paths:
  - "src/learnloop/source_retrieval/local_index.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.local_index module"
  - "src/learnloop/source_retrieval/local_index.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.local_index`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.local_index` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The local document index job (spec_local_contextual_retrieval_v1 §4.1, §4.3, §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py) |
| Source lines | 494 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `local_reason(vault: LoadedVault, root: Path | None=None) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 62) — ``(setup manifest, None)`` when the local space may be used, else ``(None, why)``.
- `epoch_of(manifest: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 79) — The software epoch setup recorded (part of the space id).
- `measured_epoch(load: Mapping[str, Any] | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 86) — The epoch the worker measured after loading (``torch.__version__``, ``transformers.__version__``, ``torch.version.cuda``).
- `local_spaces(manifest: Mapping[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 93) — ``{variant: (space_id, pins)}`` for the set-up environment's epoch.
- `owed(vault: LoadedVault, repository: Repository, local: Mapping[str, tuple[str, dict[str, Any]]], extraction_ids: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 104) — Every (extraction, variant) whose windows the cache does not fully hold.
- `build_job(items: Sequence[Mapping[str, Any]], *, manifest: Mapping[str, Any], plan_id: str, profile: Mapping[str, Any] | None=None) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 131) — The private job (carries book text) and ``{document id: [targets]}``.
- `canary_check(new: Mapping[str, Any] | None, stored: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 173) — Compare this batch's canaries with the space's stored ones (cos >= ``CANARY_MIN_COS``).
- `store_output(vault: LoadedVault, output: Mapping[str, Any], targets: Mapping[str, Sequence[Mapping[str, Any]]], *, job_id: str) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 191) — Validate and cache the worker's vectors; a wrong count or value stores nothing for that window.
- `preflight_problems(*, meminfo: Callable[[], Mapping[str, int]]=worker_module.read_meminfo, gpu: Callable[[], Mapping[str, Any] | None]=worker_module.gpu_state) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 223) — The worker's own start checks, measured now (no scope needed: this is the caller).
- `exclusive_gpu_yield(yielder: Callable[[], Any] | None, preflight: Callable[[], list[str]] | None) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 234) — Codex review F11: before an exclusive GPU job's start checks, a GPU-resident query student is asked to exit (it is a python GPU process the workload rule refuses, and its queries would otherwise keep it resident).
- `run_local_index(vault: LoadedVault, repository: Repository, *, root: Path | None=None, launcher: Callable[..., dict[str, Any]] | None=None, meter: GpuMeter | None=None, preflight: Callable[[], list[str]] | None=None, locks: Callable[[], Any]=gpu_locks, now: datetime | None=None, force: bool=False, extraction_ids: Sequence[str] | None=None, dry_run: bool=False, yielder: Callable[[], Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 262) — Index every owed window of the vault in one worker batch (aggregate report only).
- `replay_sample(vault: LoadedVault, root: Path | None, *, items_owed: bool, now: datetime | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 361) — Spec §9.3's nightly teacher replay: the logged queries the adopted student answered, re-encoded by the teacher in the batch that loads the 9B anyway (a replay-only batch at most once per REPLAY_EVERY_HOURS, keep).
- `store_replay(vault: LoadedVault, repository: Repository, space: str, output: Mapping[str, Any], replay: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 380) — Rank each replayed query by the teacher and by its stored student vector over the grouped space.
- `profile_pools(vault: LoadedVault, repository: Repository, extraction_id: str, sizes: Sequence[int]=pins.PROFILE_TOKENS) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 416) — P0: per size, a pool of consecutive TEACHING blocks the worker fits to the true token count (``worker.fit_window``).
- `run_profile(vault: LoadedVault, repository: Repository, extraction_id: str, *, root: Path | None=None, launcher: Callable[..., dict[str, Any]] | None=None, meter: GpuMeter | None=None, preflight: Callable[[], list[str]] | None=None, locks: Callable[[], Any]=gpu_locks, sizes: Sequence[int]=pins.PROFILE_TOKENS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 438) — P0's true 8,192-token profile: one metered worker (load, smoke, canaries, profile at each size by the model's own count, unload); nothing is indexed.
- `coverage_report(vault: LoadedVault, repository: Repository, root: Path | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 468) — Doctor's view: per local space, rows, covered extractions, epoch and canary status.

### Module constants

- `INDEX_JOB` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 55)
- `DEFERRED_STATUSES` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 57)
- `VARIANTS` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 58)
- `LIST_NAMES` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 59)
- `EPOCH_KEYS` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 72)
- `PROFILE_POOL_FACTOR` ([src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py), line 413)

### Explicit exports

`__all__` declares:

- `DEFERRED_STATUSES`
- `EPOCH_KEYS`
- `INDEX_JOB`
- `LIST_NAMES`
- `VARIANTS`
- `build_job`
- `canary_check`
- `coverage_report`
- `epoch_of`
- `local_reason`
- `local_spaces`
- `measured_epoch`
- `owed`
- `preflight_problems`
- `profile_pools`
- `run_local_index`
- `run_profile`
- `store_output`

## Internal implementation anchors

- `_epoch_value(value: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 75)
- `_document_id(chunks: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 127)
- `_cos(a: Sequence[float], b: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 167)
- `_completed_at(repository: Repository, extraction_id: str) -> datetime | None` ([source](../../../../../../src/learnloop/source_retrieval/local_index.py), line 252)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `coverage_report`, `run_local_index`, `run_profile`; statically calls `coverage_report`, `run_local_index`, `run_profile`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `DEFERRED_STATUSES`, `INDEX_JOB`, `run_local_index`; statically calls `run_local_index`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `build_job`, `canary_check`, `epoch_of`, `exclusive_gpu_yield`, `local_reason`, `measured_epoch`, `preflight_problems`; statically calls `build_job`, `canary_check`, `epoch_of`, `exclusive_gpu_yield`, `local_reason`, `measured_epoch`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `coverage_report`; statically calls `coverage_report`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `LIST_NAMES`, `local_reason`, `local_spaces`; statically calls `local_reason`, `local_spaces`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `local_reason`, `local_spaces`; statically calls `local_reason`, `local_spaces`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `register_space`, `set_space_canaries`, `set_space_status`, `spaces`; calls `register_space`, `set_space_canaries`, `set_space_status`, `spaces`
- [[Reference/Modules/learnloop/local_embeddings/cache|learnloop.local_embeddings.cache]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; calls `VectorCache`, `cache_path`
- [[Reference/Modules/learnloop/local_embeddings/gpu_meter|learnloop.local_embeddings.gpu_meter]] — imports `GpuBudgetExceeded`, `GpuMeter`; calls `GpuMeter`
- [[Reference/Modules/learnloop/local_embeddings/identity|learnloop.local_embeddings.identity]] — imports `local_space_pins`, `space_id`; calls `local_space_pins`, `space_id`
- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `LocksBusy`, `ScopedLauncher`, `gpu_locks`; calls `ScopedLauncher`
- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`; calls `data_root`, `limits`
- [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]] — imports `load_manifest`; calls `load_manifest`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/worker|learnloop.local_embeddings.worker]] — imports `module`; calls `check_vector`, `start_problems`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `documents`; calls `documents`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `pending_replay`, `record_replay`, `replay_due`, `yield_gpu_students`; calls `pending_replay`, `record_replay`, `replay_due`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `WINDOW_RULE`, `Window`, `expected_keys`, `extraction_windows`, `token_estimate`, `window_key`, `windows_by_extraction`; calls `expected_keys`, `extraction_windows`, `token_estimate`, `window_key`, `windows_by_extraction`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `hashlib`, `json`, `pathlib`, `typing`, `uuid`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_a_deferred_index_job_is_woken_at_its_retry_time`
  - `test_a_job_that_cannot_start_is_waiting_never_failed`
  - `test_a_moved_canary_stores_nothing_and_marks_epoch_drift`
  - `test_a_queued_index_job_whose_worker_never_started_is_started_by_the_sweep`
  - `test_a_rejected_window_leaves_the_run_partial_and_the_window_owed`
  - `test_a_worker_on_another_software_epoch_stores_nothing`
  - `test_the_index_job_caches_both_variants_and_registers_the_spaces`
  - `test_the_local_space_is_off_until_enabled_and_set_up`
  - `test_the_profile_pools_hold_teaching_text_only`
  - `test_the_worker_encodes_the_canaries_with_every_batch`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
  - `test_a_resident_gpu_student_yields_before_an_index_batch`
  - `test_the_nightly_index_batch_replays_the_queued_queries_with_the_teacher`
  - `test_the_worker_writes_teacher_targets_as_int8_shards`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains local index within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/local_index.py](../../../../../../src/learnloop/source_retrieval/local_index.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
