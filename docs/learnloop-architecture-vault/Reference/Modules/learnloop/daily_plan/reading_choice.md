---
title: "learnloop.daily_plan.reading_choice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/reading_choice.py"
source_paths:
  - "src/learnloop/daily_plan/reading_choice.py"
source_commit: "0005dbcf6f675a98a3d3b0a58a1af1fa137931e3"
source_commit_timestamp: "2026-11-01T02:20:07-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.reading_choice module"
  - "src/learnloop/daily_plan/reading_choice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.reading_choice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.reading_choice` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Curriculum C1 (spec_deliverable_curriculum_v1 §7.6): the memo of the plan's fresh reading choice.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0005dbcf6f675a98a3d3b0a58a1af1fa137931e3` |
| Commit timestamp | `2026-11-01T02:20:07-05:00` |

## Public API

- `class Remembered` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 57) — A memoized choice: the reading (a ``ReadingTarget`` or None) and its path receipt.
- `fingerprint(repository: Any, parts: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 118) — The fingerprint of the choice's inputs: the database's commit version as the watcher sees it, the watcher's own changes and the caller's ``parts``.
- `recall(repository: Any, vault: Any, fingerprint_: str) -> Remembered | None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 158) — The choice remembered for this database, vault object and fingerprint, else None.
- `remember(repository: Any, vault: Any, fingerprint_: str, reading: Any, receipt: Mapping[str, Any] | None) -> None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 169) — Keep the choice computed for this fingerprint (replacing the previous one).
- `forget() -> None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 183) — Drop the memo and close its watcher.

### Module constants

- `_LOCK` ([src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 72)
- `_DATABASE` ([src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 74)
- `_IDENTITY` ([src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 75)
- `_WATCHER` ([src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 76)
- `_ENTRY` ([src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 77)

### Explicit exports

`__all__` declares:

- `Remembered`
- `fingerprint`
- `forget`
- `recall`
- `remember`

## Internal implementation anchors

- `class _Entry` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 65)
- `_key(repository: Any) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 80)
- `_close_locked() -> None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 85)
- `_watcher_locked(database: str, identity: tuple[int, int]) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 95) — The watcher on ``database`` (opened read-only on first use; another database, or another file at its path, closes the previous one and drops its entry).
- `_identity(database: str) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 108) — The database file's identity (device, inode); None when it is gone.
- `_vault_ref(vault: Any) -> weakref.ReferenceType[Any] | None` ([source](../../../../../../src/learnloop/daily_plan/reading_choice.py), line 151)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `fingerprint`, `recall`, `remember`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`; statically calls `forget`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `dataclasses`, `hashlib`, `json`, `os`, `pathlib`, `sqlite3`, `threading`, `typing`, `weakref`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c1_fix_round3.py](../../../../../../tests/test_curriculum_c1_fix_round3.py) — direct import
  - `test_m2_the_memo_is_one_database_and_its_watcher_is_closed_on_forget`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m3_a_closing_context_drops_the_memo_and_its_watcher`
  - `test_m3_a_database_restored_at_the_same_path_is_watched_as_the_new_file`
  - `test_m3_a_vanished_database_is_never_trusted`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
  - `test_i_a_narrative_write_invalidates_c1s_memo_once_and_the_choice_is_the_same`

## Modification guidance

- Make changes here when the responsibility remains reading choice within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/reading_choice.py](../../../../../../src/learnloop/daily_plan/reading_choice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
