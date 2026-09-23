---
title: "learnloop.attempts.completion_lock"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/completion_lock.py"
source_paths:
  - "src/learnloop/attempts/completion_lock.py"
source_commit: "ccb50a726a7a679ba9b0a876a776342f05057d46"
source_commit_timestamp: "2026-09-23T12:51:27-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.completion_lock module"
  - "src/learnloop/attempts/completion_lock.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.completion_lock`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.completion_lock` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Cross-process serialization of post-attempt completion.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/completion_lock.py](../../../../../../src/learnloop/attempts/completion_lock.py) |
| Source lines | 91 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ccb50a726a7a679ba9b0a876a776342f05057d46` |
| Commit timestamp | `2026-09-23T12:51:27-04:00` |

## Public API

- `class AttemptCompletionBusy(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/completion_lock.py), line 33) — Another process kept the completion lock past the timeout.
- `completion_lock_path(sqlite_path: Path) -> Path` ([source](../../../../../../src/learnloop/attempts/completion_lock.py), line 37) — One lock per database file, however its path is spelled.
- `attempt_completion_lock(sqlite_path: Path, *, timeout_s: float | None=None) -> Iterator[None]` ([source](../../../../../../src/learnloop/attempts/completion_lock.py), line 48) — Hold the database's completion lock for the block.

### Module constants

- `COMPLETION_LOCK_TIMEOUT_S` ([src/learnloop/attempts/completion_lock.py](../../../../../../src/learnloop/attempts/completion_lock.py), line 27)
- `_POLL_INTERVAL_S` ([src/learnloop/attempts/completion_lock.py](../../../../../../src/learnloop/attempts/completion_lock.py), line 28)

## Internal implementation anchors

- `_acquire(descriptor: int, path: Path, timeout_s: float) -> None` ([source](../../../../../../src/learnloop/attempts/completion_lock.py), line 78)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `attempt_completion_lock`; statically calls `attempt_completion_lock`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `AttemptCompletionBusy`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `errno`, `fcntl`, `os`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_completion_lock_contention_raises_busy`
  - `test_completion_lock_is_shared_by_every_spelling_of_the_database_path`

## Modification guidance

- Change completion lock policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/completion_lock.py](../../../../../../src/learnloop/attempts/completion_lock.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
