---
title: "learnloop.experiments.contextual_embeddings.e1.local"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/local.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/local.py"
source_commit: "fd1a415b5345aba617996cc2f26de03dee41b69b"
source_commit_timestamp: "2026-10-24T00:02:19-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.local module"
  - "src/learnloop/experiments/contextual_embeddings/e1/local.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.local`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.local` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: The v2 local arms: the job, the scoped worker launch, the vector store and ranking.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/local.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py) |
| Source lines | 314 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fd1a415b5345aba617996cc2f26de03dee41b69b` |
| Commit timestamp | `2026-10-24T00:02:19-04:00` |

## Public API

- `class V2Space` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 50)
  - `query_space(self) -> str` (line 58; public)
- `v2_space(snapshot: CorpusSnapshot, arm: str) -> V2Space` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 62)
- `v2_documents(snapshot: CorpusSnapshot, space: V2Space) -> tuple[list[Document], dict[str, str]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 73)
- `limits(*, deadline_unix: float | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 77) — The worker's limits, from the pins (frozen into the plan).
- `profile_windows(snapshot: CorpusSnapshot) -> dict[str, list[str]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 91) — One document per profiling size: consecutive permitted units (token ESTIMATES; the worker measures the model's own count).
- `build_job(plan_id: str, copies: Sequence[tuple[str, CorpusSnapshot, Mapping[str, str]]], store: VectorStore, *, model_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 107) — The job (private: carries text) and its index (job ids -> store keys).
- `store_outputs(output: Mapping[str, Any], index: Mapping[str, Any], store: VectorStore) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 158) — Validate and store the worker's vectors; returns the counts by outcome.
- `measurements(output: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 203) — The worker output without vectors or ids: what the report may show.
- `class WorkerLauncher(Protocol)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 228)
  - `__call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]` (line 229; internal)
- `scope_command(env_python: Path, job: Path, out: Path, heartbeat: Path, *, unit: str) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 232) — The worker inside its own transient scope with the plan's memory caps.
- `launch_environment(home: Path) -> dict[str, str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 241) — ``env -i``-like: PATH, an empty private HOME, and what ``systemd-run --user`` needs to reach the user manager.
- `class ScopedLauncher` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 253) — The real launcher: the job file, the scoped worker under the meter, its output.
  - `__init__(self, env_python: Path, *, popen: Callable[..., Any] | None=None) -> None` (line 256; internal)
  - `__call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]` (line 260; internal)
- `rank_v2(snapshot: CorpusSnapshot, questions: Sequence[Any], texts: Mapping[str, str], store: VectorStore, arm: str, *, allowed: Callable[[Any], set[str]]) -> tuple[dict[str, list[str]], dict[str, int]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py), line 286) — One v2 arm's rankings from the store (exact cosine, id tie-breaks).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `ScopedLauncher`; statically calls `ScopedLauncher`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `v2_documents`, `v2_space`; statically calls `v2_documents`, `v2_space`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `build_job`, `limits`, `measurements`, `rank_v2`, `store_outputs`; statically calls `build_job`, `limits`, `measurements`, `rank_v2`, `store_outputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `AdapterError`, `Document`, `VectorStore`, `build_index`, `decode`, `document_space_id`, `query_encoder_id`, `query_vector_key`; calls `build_index`, `decode`, `document_space_id`, `query_encoder_id`, `query_vector_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`, `_inside_local_root`; calls `_inside_local_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/gpu_meter|learnloop.experiments.contextual_embeddings.e1.gpu_meter]] — imports `GpuMeter`, `supervise`; calls `supervise`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`; calls `v2_pin`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/worker|learnloop.experiments.contextual_embeddings.e1.worker]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `latency_summary`; calls `latency_summary`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `documents_for`, `exact_search`; calls `documents_for`, `exact_search`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `os`, `pathlib`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_scoped_launcher_caps_memory_and_passes_no_key`
- [tests/test_e1_worker.py](../../../../../../../../tests/test_e1_worker.py) — direct import
  - `test_a_concurrent_gpu_workload_is_refused_whatever_the_desktop`
  - `test_a_spent_gpu_allowance_refuses_the_start`
  - `test_many_small_processes_past_the_total_are_refused`
  - `test_the_owners_desktop_gpu_set_is_no_concurrent_workload`
  - `test_the_sampler_aborts_below_the_host_floor_and_keeps_partial_results`
  - `test_the_worker_itself_is_never_its_own_concurrent_workload`

## Modification guidance

- Make changes here when the responsibility remains local within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/local.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/local.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
