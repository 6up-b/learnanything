---
title: "learnloop.db.stores.ingest_queue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/ingest_queue.py"
source_paths:
  - "src/learnloop/db/stores/ingest_queue.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.db.stores.ingest_queue module"
  - "src/learnloop/db/stores/ingest_queue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.ingest_queue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.ingest_queue` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Durable ingest queue persistence.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/ingest_queue.py](../../../../../../../src/learnloop/db/stores/ingest_queue.py) |
| Source lines | 648 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class IngestQueueStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/ingest_queue.py), line 41) — Repository-compatible methods for the durable ingest queue family.
  - `connection(self) -> sqlite3.Connection` (line 44; public) — Return a configured SQLite connection from the concrete repository.
  - `insert_ingest_batch(self, *, id: str, workflow_type: str, subject_id: str | None=None, source_set_id: str | None=None, payload_schema_version: int=1, status: str='queued', priority: int=0, clock: Clock | None=None) -> None` (line 49; public)
  - `get_ingest_batch(self, batch_id: str) -> dict[str, Any] | None` (line 84; public)
  - `list_ingest_batches(self, limit: int | None=None) -> list[dict[str, Any]]` (line 91; public)
  - `update_ingest_batch_status(self, batch_id: str, status: str, *, mark_started: bool=False, mark_finished: bool=False, clear_finished: bool=False, clock: Clock | None=None) -> None` (line 101; public) — Update status timestamps without retaining stale terminal state.
  - `request_ingest_batch_cancel(self, batch_id: str) -> None` (line 135; public) — Flag the batch and every not-yet-terminal job for cancellation.
  - `clear_ingest_batch_cancel_requested(self, batch_id: str) -> None` (line 154; public) — Clear the batch cancellation latch before an explicit resume.
  - `insert_ingest_job(self, *, id: str, batch_id: str, ordinal: int, job_type: str, payload: Mapping[str, Any] | None=None, payload_schema_version: int=1, clock: Clock | None=None) -> None` (line 164; public)
  - `add_ingest_job_dependency(self, job_id: str, depends_on_job_id: str) -> None` (line 197; public)
  - `get_ingest_job(self, job_id: str) -> dict[str, Any] | None` (line 208; public)
  - `ingest_jobs_for_batch(self, batch_id: str) -> list[dict[str, Any]]` (line 215; public)
  - `ingest_jobs_for_batches(self, batch_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]` (line 218; public) — Bulk-load ordered jobs, including requested empty batches.
  - `ingest_job_dependency_ids(self, job_id: str) -> list[str]` (line 241; public)
  - `ingest_job_dependencies_for_jobs(self, job_ids: Iterable[str]) -> dict[str, list[str]]` (line 244; public) — Bulk-load dependency ids for job progress views.
  - `ingest_job_dependents(self, job_id: str) -> list[str]` (line 268; public)
  - `claim_next_ingest_job(self, *, worker_id: str, now_iso: str, lease_cutoff_iso: str, eligible_job_types: Sequence[str] | None=None, compatible_running_job_types: Sequence[str]=(), allow_parallel: bool=False, max_parallel: int | None=None) -> dict[str, Any] | None` (line 279; public) — Atomically claim the next eligible queued job for ``worker_id``.
  - `heartbeat_ingest_job(self, job_id: str, *, worker_id: str, phase: str | None=None, message: str | None=None, current_window: int | None=None, total_windows: int | None=None, clock: Clock | None=None) -> None` (line 392; public)
  - `finish_ingest_job(self, job_id: str, *, status: str, phase: str | None=None, message: str | None=None, result: Mapping[str, Any] | None=None, error: Mapping[str, Any] | None=None, usage: Mapping[str, Any] | None=None, release_lease: bool=True, clear_finished: bool=False, current_window: int | None=None, total_windows: int | None=None, clock: Clock | None=None) -> None` (line 419; public) — Move a job to a new state and optionally release its lease.
  - `requeue_ingest_job(self, job_id: str, *, message: str='Waiting to start', clock: Clock | None=None) -> None` (line 473; public)
  - `delete_finished_ingest_batches(self, batch_ids: Sequence[str]) -> dict[str, int]` (line 494; public) — Delete finished queue history without touching source artifacts.
  - `update_ingest_job_payload(self, job_id: str, payload: Mapping[str, Any]) -> None` (line 545; public) — Replace a durable job payload before an explicit retry.
  - `set_ingest_job_cancel_requested(self, job_id: str) -> None` (line 557; public)
  - `ingest_jobs_by_types(self, job_types: Sequence[str], *, limit: int | None=None) -> list[dict[str, Any]]` (line 564; public)
  - `active_ingest_jobs(self) -> list[dict[str, Any]]` (line 580; public) — Return every job that has not reached a terminal state.
  - `expired_running_ingest_jobs(self, lease_cutoff_iso: str) -> list[dict[str, Any]]` (line 593; public)
  - `rung_variant_batch_dead(self, batch_id: str | None) -> bool` (line 608; public) — Whether a rung-variant batch is absent or wholly terminal.
  - `concept_animation_batch_dead(self, batch_id: str | None) -> bool` (line 613; public) — Whether a concept-animation batch is absent or wholly terminal.
  - `_ingest_batch_dead(self, batch_id: str | None, *, job_type: str) -> bool` (line 618; internal)
  - `rung_variant_pending_source_ids(self) -> set[str]` (line 632; public) — Source item ids held by live durable rung-variant work.

## Internal implementation anchors

- `_json(data: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/ingest_queue.py), line 22)
- `_decode_ingest_batch(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/ingest_queue.py), line 26)
- `_decode_ingest_job(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/ingest_queue.py), line 32)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `IngestQueueStoreMixin`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_queue_store.py](../../../../../../../tests/test_ingest_queue_store.py) — direct import
  - `test_repository_queue_api_is_composed_from_the_store`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/ingest_queue.py](../../../../../../../src/learnloop/db/stores/ingest_queue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
