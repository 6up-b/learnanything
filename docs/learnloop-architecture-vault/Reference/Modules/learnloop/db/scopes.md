---
title: "learnloop.db.scopes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/scopes.py"
source_paths:
  - "src/learnloop/db/scopes.py"
source_commit: "c1619d0275bfe61eabe180738165ec480c6dc4fb"
source_commit_timestamp: "2026-09-23T13:02:20-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.scopes module"
  - "src/learnloop/db/scopes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.scopes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.scopes` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: Connection ownership and nested repository transaction scopes.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py) |
| Source lines | 354 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c1619d0275bfe61eabe180738165ec480c6dc4fb` |
| Commit timestamp | `2026-09-23T13:02:20-04:00` |

## Public API

- `class JobOwnershipLost(RuntimeError)` ([source](../../../../../../src/learnloop/db/scopes.py), line 17) — An expired or superseded job attempted to publish more state.
- `allow_late_model_records()` ([source](../../../../../../src/learnloop/db/scopes.py), line 64) — Let the model-call store record paid work after its job lost ownership.
- `guard_ingest_writes(path, job_id, worker_id, attempt_count)` ([source](../../../../../../src/learnloop/db/scopes.py), line 82) — Fence all repositories for this database on the current worker thread.
- `guarded_connection(connection, path)` ([source](../../../../../../src/learnloop/db/scopes.py), line 105)
- `class OwnedConnection` ([source](../../../../../../src/learnloop/db/scopes.py), line 199) — Close a borrowed repository connection at the end of its with block.
  - `__init__(self, connection: sqlite3.Connection)` (line 202; internal)
  - `__getattr__(self, name: str) -> Any` (line 205; internal)
  - `__setattr__(self, name: str, value: Any) -> None` (line 208; internal)
  - `__enter__(self)` (line 211; internal)
  - `__exit__(self, *exc)` (line 214; internal)
- `class AtomicConnection` ([source](../../../../../../src/learnloop/db/scopes.py), line 221) — Keep store methods' own commits inside an owning transaction.
  - `__init__(self, connection: sqlite3.Connection)` (line 230; internal)
  - `__getattr__(self, name: str) -> Any` (line 236; internal)
  - `isolation_level(self)` (line 240; public)
  - `isolation_level(self, value)` (line 244; public)
  - `_savepoint(self) -> str` (line 248; internal)
  - `__enter__(self)` (line 254; internal)
  - `__exit__(self, exc_type, exc, traceback)` (line 258; internal)
  - `execute(self, sql, parameters=())` (line 266; public)
  - `executescript(self, _script)` (line 279; public)
  - `cursor(self, *args, **kwargs)` (line 282; public)
  - `commit(self)` (line 285; public)
  - `rollback(self)` (line 290; public)
  - `close(self)` (line 300; public)
- `pinned_repository_call(function)` ([source](../../../../../../src/learnloop/db/scopes.py), line 325) — Reuse a connection for short local work, preserving each write commit.
- `atomic_repository_call(function)` ([source](../../../../../../src/learnloop/db/scopes.py), line 338) — Wrap a local operation with a named repository argument atomically.

### Module constants

- `_LEADING_COMMENTS` ([src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py), line 36)
- `_WRITE_VERBS` ([src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py), line 37)
- `_STRING_LITERALS` ([src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py), line 38)
- `_CTE_WRITE` ([src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py), line 43)

## Internal implementation anchors

- `class _JobGuard` ([source](../../../../../../src/learnloop/db/scopes.py), line 22)
- `_is_write_statement(sql: str) -> bool` ([source](../../../../../../src/learnloop/db/scopes.py), line 49) — Whether a statement can modify the database.
- `class _GuardedConnection` ([source](../../../../../../src/learnloop/db/scopes.py), line 112)
- `class _GuardedCursor` ([source](../../../../../../src/learnloop/db/scopes.py), line 180)
- `class _AtomicCursor` ([source](../../../../../../src/learnloop/db/scopes.py), line 304) — Cursor transaction statements must obey the same borrowing rules.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobOwnershipLost`, `guard_ingest_writes`; statically calls `JobOwnershipLost`, `guard_ingest_writes`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `guarded_connection`; statically calls `guarded_connection`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `AtomicConnection`, `OwnedConnection`; statically calls `AtomicConnection`, `OwnedConnection`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `allow_late_model_records`; statically calls `allow_late_model_records`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `atomic_repository_call`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `pinned_repository_call`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ingest_queue|learnloop.db.stores.ingest_queue]] — imports `JobOwner`, `owns_ingest_job`; calls `JobOwner`, `owns_ingest_job`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `guard_vault_mutations`; calls `guard_vault_mutations`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `dataclasses`, `functools`, `inspect`, `pathlib`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_ownership.py](../../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_cte_read_is_not_fenced_but_a_cte_write_is`
  - `test_a_replaced_attempt_still_saves_its_paid_checkpoint`
  - `test_a_replaced_ingest_cannot_create_a_subject`
  - `test_a_replaced_ingest_cannot_publish_its_source_note_or_goal_linkage`
  - `test_late_usage_is_retained_after_takeover_without_restoring_publication_authority`
  - `test_stale_worker_cannot_finish_or_publish_after_replacement`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_observer_control_exceptions_propagate_unchanged`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_content_recalibration_replay_cannot_lose_its_ingest_lease_midway`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/scopes.py](../../../../../../src/learnloop/db/scopes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
