---
title: "learnloop.local_embeddings.launcher"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/launcher.py"
source_paths:
  - "src/learnloop/local_embeddings/launcher.py"
source_commit: "8cba03a7e83a7c265c84d68da164caacb76e4e25"
source_commit_timestamp: "2026-10-26T11:39:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.launcher module"
  - "src/learnloop/local_embeddings/launcher.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.launcher`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.launcher` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: Launching the local worker: its own capped scope, the locks, the meter (spec §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/launcher.py](../../../../../../src/learnloop/local_embeddings/launcher.py) |
| Source lines | 124 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8cba03a7e83a7c265c84d68da164caacb76e4e25` |
| Commit timestamp | `2026-10-26T11:39:57-04:00` |

## Public API

- `class LocksBusy(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 33) — Another big GPU job (or a full test gate) holds a lock: wait, never break it.
- `gpu_lock_path() -> Path` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 37)
- `gpu_locks(paths: tuple[Path, ...] | None=None) -> Iterator[None]` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 43) — Hold every lock non-blocking for the block, or raise :class:`LocksBusy`.
- `scope_command(env_python: Path, job: Path, out: Path, heartbeat: Path, *, unit: str, script: Path | None=None, memory_max: str=pins.SCOPE_MEMORY_MAX) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 65) — The worker (or P2's trainer, ``script``) inside its own transient scope with the memory caps (keep).
- `launch_environment(home: Path) -> dict[str, str]` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 75)
- `class ScopedLauncher` ([source](../../../../../../src/learnloop/local_embeddings/launcher.py), line 84) — The real launcher: the private job file, the scoped worker under the meter, its output.
  - `__init__(self, env_python: Path, *, popen: Callable[..., Any] | None=None, script: Path | None=None, memory_max: str=pins.SCOPE_MEMORY_MAX, unit_prefix: str='learnloop-local-index') -> None` (line 87; internal)
  - `__call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]` (line 95; internal)

### Module constants

- `FULL_SUITE_LOCK` ([src/learnloop/local_embeddings/launcher.py](../../../../../../src/learnloop/local_embeddings/launcher.py), line 30)

### Explicit exports

`__all__` declares:

- `FULL_SUITE_LOCK`
- `LocksBusy`
- `ScopedLauncher`
- `gpu_lock_path`
- `gpu_locks`
- `launch_environment`
- `scope_command`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `LocksBusy`, `ScopedLauncher`, `gpu_locks`; statically calls `ScopedLauncher`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `LocksBusy`, `ScopedLauncher`, `gpu_locks`; statically calls `ScopedLauncher`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `gpu_lock_path`, `launch_environment`; statically calls `gpu_lock_path`, `launch_environment`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/gpu_meter|learnloop.local_embeddings.gpu_meter]] — imports `GpuMeter`, `supervise`; calls `supervise`
- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/worker|learnloop.local_embeddings.worker]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `fcntl`, `json`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_a_job_that_cannot_start_is_waiting_never_failed`
  - `test_the_worker_runs_in_its_own_capped_scope_and_the_locks_are_never_broken`
- [tests/test_query_student_gpu.py](../../../../../../tests/test_query_student_gpu.py) — direct import
  - `test_a_tiny_student_trains_on_the_gpu_under_the_lock_and_the_floors`

## Modification guidance

- Make changes here when the responsibility remains launcher within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/launcher.py](../../../../../../src/learnloop/local_embeddings/launcher.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
