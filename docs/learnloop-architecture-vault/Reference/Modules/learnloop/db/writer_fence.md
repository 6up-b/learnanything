---
title: "learnloop.db.writer_fence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/writer_fence.py"
source_paths:
  - "src/learnloop/db/writer_fence.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.db.writer_fence module"
  - "src/learnloop/db/writer_fence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.writer_fence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.writer_fence` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: The writer fence: a tag-dependent write commits only under the algorithm tag the vault's database is at.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py) |
| Source lines | 390 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class WriterFenceRefusal(BaseException)` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 140) — The fence refused a write: the vault was upgraded after the work's vault was loaded, so nothing of the write was saved.
- `class FenceMismatch(RuntimeError)` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 146) — An activation found the database at another tag than its predecessor: it would move the tag sideways or back.
- `class FencedCursor(sqlite3.Cursor)` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 154) — A cursor of a writable connection this code opened: the trigger's refusal comes out as :class:`WriterFenceRefusal`; every other error is untouched.
  - `execute(self, sql, parameters=(), /)` (line 158; public)
  - `executemany(self, sql, parameters, /)` (line 165; public)
  - `executescript(self, script, /)` (line 172; public)
- `class FencedConnection(sqlite3.Connection)` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 180) — A writable connection this code opened: its statements run on :class:`FencedCursor`s.
  - `cursor(self, factory=None)` (line 185; public)
  - `execute(self, sql, parameters=(), /)` (line 188; public)
  - `executemany(self, sql, parameters, /)` (line 191; public)
  - `executescript(self, script, /)` (line 194; public)
- `raise_refusal(cursor: sqlite3.Cursor, error: sqlite3.IntegrityError) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 198) — Raise ``error`` as :class:`WriterFenceRefusal` when it is the trigger's refusal (and count it for the host); return for any other integrity error.
- `refusals(sqlite_path: Path | str) -> int` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 211) — How many writes to the database at ``sqlite_path`` the fence refused in this process so far.
- `observe(sqlite_path: Path | str, tag: str | None) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 232) — This process loaded the vault whose database is ``sqlite_path`` at ``tag``: its connections write under it.
- `writing_under(sqlite_path: Path | str, *tags: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 242) — Connections to ``sqlite_path`` opened in this context write under ``tags`` (the tag of the vault the work was computed from; the activation's predecessor and successor together), whatever this process loaded last.
- `bound(sqlite_path: Path | str, tags: frozenset[str] | None)` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 254) — :func:`writing_under` ``tags`` when there are any, else nothing: a repository's connection under the binding it was made with (:class:`~learnloop.db.repositories.Repository`).
- `bind_scope(sqlite_path: Path | str, *tags: str) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 261) — From here to the end of the enclosing :func:`writing_under` (or the context), connections to ``sqlite_path`` write under ``tags``: what a host does when it publishes a newly loaded vault in the middle of a request.
- `current_scope() -> tuple[tuple[str, frozenset[str]], ...]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 273) — This context's scopes, to hand to a thread it starts (:func:`restored_scope`).
- `restored_scope(scope: tuple[tuple[str, frozenset[str]], ...]) -> Iterator[None]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 280) — Run under the scopes :func:`current_scope` read where the work was started.
- `scoped(sqlite_path: Path | str) -> frozenset[str] | None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 290) — The tags a scope of this context binds for ``sqlite_path``, or None outside every scope for it.
- `binding(sqlite_path: Path | str) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 300) — The tags a connection to ``sqlite_path`` opened now writes under (empty: unbound).
- `register(connection: sqlite3.Connection, sqlite_path: Path | str, tags: frozenset[str]) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 315) — Register the marker and ``tags`` (the checkout's one read of :func:`binding`) on a writable connection.
- `recorded_tag(connection: sqlite3.Connection) -> str | None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 328) — The database's tag, or None while no fence-aware activation has set it (or before migration 275).
- `advance(connection: sqlite3.Connection, *, predecessor: str, target: str, recorded_at: str) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 338) — Move the database's tag from ``predecessor`` to ``target`` inside the activation's transaction (it commits with the activation's state and never before it), or raise :class:`FenceMismatch` when the database is at any other tag: a vault no fence-aware activation touched has no ro…
- `is_refusal(error: BaseException) -> bool` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 357) — Whether ``error`` is the fence's refusal of a write (nothing of the write was saved; a retry after the process reloads the vault runs under the vault's tag).

### Module constants

- `TABLE` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 71)
- `TAG_FUNCTION_PREFIX` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 74)
- `MARKER_FUNCTION` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 77)
- `REFUSAL` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 80)
- `GUARDED` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 95)
- `GUARD_CONDITIONS` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 116)
- `REFUSAL_BOUNDARIES` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 125)
- `_REFUSALS` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 151)
- `_WRITING_UNDER` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 219)
- `_OBSERVED` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 224)
- `_OBSERVED_LOCK` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 225)

### Explicit exports

`__all__` declares:

- `GUARDED`
- `GUARD_CONDITIONS`
- `MARKER_FUNCTION`
- `REFUSAL`
- `REFUSAL_BOUNDARIES`
- `TABLE`
- `TAG_FUNCTION_PREFIX`
- `FenceMismatch`
- `FencedConnection`
- `FencedCursor`
- `WriterFenceRefusal`
- `advance`
- `bind_scope`
- `binding`
- `bound`
- `current_scope`
- `is_refusal`
- `observe`
- `raise_refusal`
- `recorded_tag`
- `refusals`
- `register`
- `restored_scope`
- `scoped`
- `writing_under`

## Internal implementation anchors

- `_key(sqlite_path: Path | str) -> str` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 228)
- `_with_binding(key: str, tags) -> tuple[tuple[str, frozenset[str]], ...]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 268)
- `_present() -> int` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 311)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `module`; statically calls `binding`, `register`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `module`; statically calls `binding`, `bound`, `writing_under`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `module`; statically calls `advance`, `observe`, `recorded_tag`, `writing_under`
- [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `module`; statically calls `observe`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `module`; statically calls `bind_scope`, `recorded_tag`, `scoped`, `writing_under`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `module`; statically calls `current_scope`, `restored_scope`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`; statically calls `is_refusal`, `recorded_tag`, `refusals`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `pathlib`, `sqlite3`, `threading`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/connection_reuse.py](../../../../../../tests/connection_reuse.py) — direct import
- [tests/test_connection_reuse.py](../../../../../../tests/test_connection_reuse.py) — direct import
  - `test_another_thread_opens_its_own_and_the_pool_closes_with_the_test`
  - `test_the_durability_lane_runs_production_connections_copies_and_fsync`
  - `test_the_marker_opens_real_connections`
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_a_write_the_writer_fence_refused_is_recorded_and_says_try_again`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_a_write_the_writer_fence_refused_reloads_the_vault_and_is_a_retryable_error`
- [tests/test_writer_fence.py](../../../../../../tests/test_writer_fence.py) — direct import
  - `test_a_death_after_the_publication_keeps_the_database_tag_until_the_completion`
  - `test_a_death_between_the_activation_and_the_publication_leaves_the_predecessor_in_force`
  - `test_a_fenced_writer_bound_to_no_tag_is_not_refused`
  - `test_a_pool_never_hands_a_connection_to_another_binding`
  - `test_a_stale_writer_of_this_code_is_refused_and_proceeds_after_a_reload`
  - `test_a_wal_reader_from_before_the_activation_cannot_commit_after_it`
  - `test_every_fenced_write_has_its_trigger_at_the_head`
  - `test_every_fenced_write_refuses_a_writer_bound_to_another_tag`
- [tests/test_writer_fence_scopes.py](../../../../../../tests/test_writer_fence_scopes.py) — direct import
  - `test_a_pool_checkout_reads_its_binding_once`
  - `test_a_refusal_is_not_an_exception_a_broad_except_could_take`
  - `test_a_refusal_on_a_connection_this_code_opened_is_the_fences_own_exception`
  - `test_a_stale_reader_cannot_first_complete_a_section_but_still_records_progress`
  - `test_a_stale_serve_presentation_probe_pin_or_adjudication_is_refused`
  - `test_an_activation_refuses_a_database_at_another_tag_than_its_predecessor`
  - `test_mcp_drops_its_cached_vault_on_a_refusal`
  - `test_no_handler_that_can_catch_a_refusal_swallows_it`
  - `test_the_forecast_receipt_writer_does_not_swallow_a_refusal`
- [tests/writer_fence_helpers.py](../../../../../../tests/writer_fence_helpers.py) — direct import
- [tests/writer_fence_migration_helpers.py](../../../../../../tests/writer_fence_migration_helpers.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
