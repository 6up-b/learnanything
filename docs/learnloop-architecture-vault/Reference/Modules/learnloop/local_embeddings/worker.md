---
title: "learnloop.local_embeddings.worker"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/worker.py"
source_paths:
  - "src/learnloop/local_embeddings/worker.py"
source_commit: "af9ec88af572c4404210a4175d02dc4a840dc6e2"
source_commit_timestamp: "2026-10-27T02:32:10-04:00"
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
  - "learnloop.local_embeddings.worker module"
  - "src/learnloop/local_embeddings/worker.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.worker`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.worker` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The local index worker: one batch process that loads pplx v2 BF16, runs the smoke checks and the canaries, profiles, encodes every owed window, unloads and exits (spec_local_contextual_retrieval_v1 §4.1, §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py) |
| Source lines | 966 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `af9ec88af572c4404210a4175d02dc4a840dc6e2` |
| Commit timestamp | `2026-10-27T02:32:10-04:00` |

## Public API

- `class Refused(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 53) — A start condition failed: nothing was loaded.
- `class WorkerOOM(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 57) — The device ran out of memory (counted, never retried at a larger size).
- `class Aborted(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 61) — The sampler stopped the run (host floor, device target, deadline).
- `read_meminfo(text: str | None=None) -> dict[str, int]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 66) — ``/proc/meminfo`` in bytes (MemTotal, MemAvailable, SwapTotal, SwapFree).
- `own_cgroup(text: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 80) — This process's cgroup v2 path (``0::/...``), or None.
- `cgroup_value(path: str, name: str, *, root: Path=Path('/sys/fs/cgroup')) -> str | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 94)
- `scope_limits(*, cgroup_text: str | None=None, root: Path=Path('/sys/fs/cgroup')) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 101) — The worker's scope: its cgroup path, ``memory.max`` and ``memory.swap.max`` (None when unlimited or unreadable) and the current/peak usage.
- `run_nvidia_smi(arguments: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 118)
- `process_cmdline(pid: int) -> str` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 123) — A process's command line (for matching only; never recorded).
- `gpu_state(run: Callable[[Sequence[str]], str]=run_nvidia_smi, cmdline: Callable[[int], str]=process_cmdline) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 132) — Device 0's memory and utilization and every compute process (pid, executable name, MiB), from nvidia-smi; each process's command line is read for the workload match only.
- `disk_free_bytes(path: Path) -> int` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 158)
- `start_problems(limits: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any], gpu: Mapping[str, Any] | None, own_pids: Sequence[int]=(), require_scope: bool=True) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 163) — Why this process must not start (empty: it may).
- `workload_match(item: Mapping[str, Any], patterns: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 199) — The workload pattern a process's name or command line matches, else None.
- `other_processes(gpu: Mapping[str, Any], own_pids: Sequence[int]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 210) — The other GPU processes as a receipt records them: name and MiB only.
- `workload_problems(gpu: Mapping[str, Any], limits: Mapping[str, Any], *, own_pids: Sequence[int]=()) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 217) — No concurrent SUBSTANTIAL GPU workload (spec §8, D2).
- `sha256_file(path: Path, *, chunk: int=16 * MIB) -> str` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 243)
- `model_dir_problems(model_dir: Path, files: Mapping[str, Sequence[Any]], remote_code: Sequence[str], *, verify_digests: bool=False) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 251) — Missing or wrong files: every size always, the remote code's digest always, every digest when ``verify_digests``.
- `class LoadedModel(Protocol)` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 274)
  - `count_tokens(self, chunks: Sequence[str], *, task: str='document') -> int` (line 277; public)
  - `encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int=1) -> list[np.ndarray]` (line 278; public)
  - `encode_queries(self, queries: Sequence[str], *, batch_size: int=1) -> list[np.ndarray]` (line 279; public)
  - `device_memory(self) -> dict[str, int | None]` (line 280; public)
  - `reset_peak(self) -> None` (line 281; public)
  - `unload(self) -> dict[str, Any]` (line 282; public)
- `repair_loaded_model(model: Any, model_dir: Path, *, fp32_modules: Sequence[str], tokenizer_factory: Callable[[Path], Any], read_tensor: Callable[[Path, str], Any], restore_fp32: Callable[[Any, Any], bool]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 289) — Two post-load repairs for the pinned remote code under transformers 5.18 (found on the first GPU run and reproduced on CPU with a tiny random model): * **The tokenizer.** The remote ``tokenizer`` property calls ``AutoTokenizer.from_pretrained(config._name_or_path, revision=confi…
- `drop_page_cache(paths: Sequence[Path]) -> int` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 326) — Advise the kernel to drop the shards' cached pages once they are on the device (page cache counts toward the scope's memory.max).
- `class TransformersModel` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 346) — pplx v2 through its own reviewed ``encode``/``encode_queries`` (never a reimplementation), loaded BF16 with shards straight onto device 0.
  - `__init__(self, model_dir: Path, *, precision: str, attention: str, fp32_modules: Sequence[str]) -> None` (line 350; internal)
  - `_oom(self) -> type[BaseException]` (line 421; internal)
  - `count_tokens(self, chunks: Sequence[str], *, task: str='document') -> int` (line 424; public)
  - `encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int=1) -> list[np.ndarray]` (line 428; public)
  - `encode_queries(self, queries: Sequence[str], *, batch_size: int=1) -> list[np.ndarray]` (line 438; public)
  - `device_memory(self) -> dict[str, int | None]` (line 448; public)
  - `reset_peak(self) -> None` (line 455; public)
  - `unload(self) -> dict[str, Any]` (line 458; public)
- `load_model(model_dir: Path, job: Mapping[str, Any]) -> LoadedModel` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 474)
- `class Sampler(threading.Thread)` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 480) — Peaks every interval, a heartbeat file, and the abort conditions.
  - `__init__(self, limits: Mapping[str, Any], *, heartbeat: Path | None, meminfo: Callable[[], Mapping[str, int]], scope: Callable[[], Mapping[str, Any]], gpu: Callable[[], Mapping[str, Any] | None], device: Callable[[], Mapping[str, int | None]] | None=None, interval: float=1.0, on_hard_abort: Callable[[str], None] | None=None) -> None` (line 483; internal)
  - `_max(self, key: str, value: Any) -> None` (line 504; internal)
  - `sample(self) -> None` (line 508; public)
  - `run(self) -> None` (line 549; public)
  - `stop(self) -> None` (line 557; public)
- `check_vector(vector: np.ndarray, dims: int) -> str | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 586) — Why a raw output row is not a valid int8-valued vector (None: valid).
- `smoke(model: LoadedModel, job: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 601) — Spec §8's smoke checks on PUBLIC text (each recorded with its values).
- `over_limit(tokens: int, job: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 652) — The harness's own limit (never a truncation): None when it fits.
- `fit_window(model: LoadedModel, pool: Sequence[str], target: int) -> tuple[list[str], int]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 658) — The longest prefix of ``pool`` whose MODEL token count fits ``target``, its last chunk trimmed by whole words to fill the remainder (P0's true 8,192-token profile).
- `profile(model: LoadedModel, job: Mapping[str, Any], sampler: Sampler | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 691) — Serialized indexing at each size, smallest first; a failure stops the larger sizes.
- `canaries(model: LoadedModel, job: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 738) — The fixed public canary set, encoded like any batch (int-valued rows).
- `encode_all(model: LoadedModel, job: Mapping[str, Any], output: dict[str, Any], sampler: Sampler | None, lock: threading.Lock) -> None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 754)
- `encode_query_shards(model: LoadedModel, job: Mapping[str, Any], output: dict[str, Any], sampler: Sampler | None, lock: threading.Lock) -> None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 793) — P2's teacher targets: large query sets written as int8 ``.npy`` shards, never as JSON.
- `run_job(job: Mapping[str, Any], *, model_factory: Callable[[Path, Mapping[str, Any]], LoadedModel]=load_model, meminfo: Callable[[], Mapping[str, int]]=read_meminfo, scope: Callable[[], Mapping[str, Any]]=scope_limits, gpu: Callable[[], Mapping[str, Any] | None]=gpu_state, heartbeat: Path | None=None, write_partial: Callable[[Mapping[str, Any]], None] | None=None, hard_exit: Callable[[int], None]=os._exit, model_check: Callable[[Mapping[str, Any]], list[str]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 843) — One worker process's whole job; always returns the output record.
- `main(argv: Sequence[str] | None=None) -> int` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 947)

### Module constants

- `WORKER_VERSION` ([src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py), line 48)
- `GIB` ([src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py), line 49)
- `MIB` ([src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py), line 50)
- `KERNEL_HINTS` ([src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py), line 285)

## Internal implementation anchors

- `_own_rss(field: str='VmRSS:') -> int | None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 561) — Resident memory (VmRSS includes mapped shard pages; RssAnon does not).
- `_atomic_json(path: Path, value: Any) -> None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 573)
- `_cos(a: np.ndarray, b: np.ndarray) -> float` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 580)
- `_guard_network() -> None` ([source](../../../../../../src/learnloop/local_embeddings/worker.py), line 932) — Refuse every inet connection from this process (zero network).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]] — imports `model_dir_problems`; statically calls `model_dir_problems`
- [[Reference/Modules/learnloop/local_embeddings/student_server|learnloop.local_embeddings.student_server]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/student_trainer|learnloop.local_embeddings.student_trainer]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `module`; statically calls `check_vector`, `start_problems`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `argparse`, `collections`, `gc`, `hashlib`, `json`, `logging`, `os`, `pathlib`, `platform`, `socket`, `subprocess`, `sys`, `threading`, `time`, `traceback`, `typing`, `warnings`
- Third party: `numpy`, `safetensors`, `torch`, `transformers`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]], [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]], [[Reference/Modules/learnloop/local_embeddings/student_server|learnloop.local_embeddings.student_server]], [[Reference/Modules/learnloop/local_embeddings/student_trainer|learnloop.local_embeddings.student_trainer]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/local_embeddings_fakes.py](../../../../../../tests/local_embeddings_fakes.py) — direct import
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_the_production_worker_imports_only_the_standard_library_and_numpy`
  - `test_the_profile_is_fitted_to_the_true_token_count`
  - `test_the_worker_runs_in_its_own_capped_scope_and_the_locks_are_never_broken`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_the_query_process_refuses_outside_its_4g_scope_and_under_the_host_floor`
- [tests/test_query_student_gpu.py](../../../../../../tests/test_query_student_gpu.py) — direct import
  - `test_a_tiny_student_trains_on_the_gpu_under_the_lock_and_the_floors`

## Modification guidance

- Make changes here when the responsibility remains worker within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/worker.py](../../../../../../src/learnloop/local_embeddings/worker.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
