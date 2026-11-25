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
| Source lines | 193 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `observe(sqlite_path: Path | str, tag: str | None) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 101) — This process loaded the vault whose database is ``sqlite_path`` at ``tag``: its connections write under it.
- `writing_under(sqlite_path: Path | str, *tags: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 111) — Connections to ``sqlite_path`` opened in this context write under ``tags`` (the activation's predecessor and successor together), whatever this process observed.
- `binding(sqlite_path: Path | str) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 124) — The tags a connection to ``sqlite_path`` opened now writes under (empty: unbound).
- `register(connection: sqlite3.Connection, sqlite_path: Path | str) -> frozenset[str]` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 140) — Register the marker and this context's binding on a writable connection; the binding registered.
- `recorded_tag(connection: sqlite3.Connection) -> str | None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 152) — The database's tag, or None while no fence-aware activation has set it (or before migration 275).
- `activate(connection: sqlite3.Connection, *, target: str, recorded_at: str) -> None` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 162) — Set the database's tag to ``target`` inside the activation's transaction: it commits with the activation's state and never before it, so a writer still at the predecessor is refused from that commit on.
- `is_refusal(error: BaseException) -> bool` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 173) — Whether ``error`` is the fence's refusal of a write (nothing of the write was saved; a retry after the process reloads the vault runs under the vault's tag).

### Module constants

- `TABLE` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 52)
- `TAG_FUNCTION_PREFIX` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 55)
- `MARKER_FUNCTION` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 58)
- `REFUSAL` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 61)
- `GUARDED` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 72)
- `_WRITING_UNDER` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 88)
- `_OBSERVED` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 93)
- `_OBSERVED_LOCK` ([src/learnloop/db/writer_fence.py](../../../../../../src/learnloop/db/writer_fence.py), line 94)

### Explicit exports

`__all__` declares:

- `GUARDED`
- `MARKER_FUNCTION`
- `REFUSAL`
- `TABLE`
- `TAG_FUNCTION_PREFIX`
- `activate`
- `binding`
- `is_refusal`
- `observe`
- `recorded_tag`
- `register`
- `writing_under`

## Internal implementation anchors

- `_key(sqlite_path: Path | str) -> str` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 97)
- `_present() -> int` ([source](../../../../../../src/learnloop/db/writer_fence.py), line 136)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `module`; statically calls `binding`, `register`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `module`; statically calls `activate`, `observe`, `writing_under`
- [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]] — imports `module`; statically calls `is_refusal`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `module`; statically calls `observe`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`; statically calls `is_refusal`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `pathlib`, `sqlite3`, `threading`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]], [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]], [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

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
