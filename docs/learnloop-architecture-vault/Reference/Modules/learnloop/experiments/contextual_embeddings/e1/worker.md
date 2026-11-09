---
title: "learnloop.experiments.contextual_embeddings.e1.worker"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/worker.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/worker.py"
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
  - "learnloop.experiments.contextual_embeddings.e1.worker module"
  - "src/learnloop/experiments/contextual_embeddings/e1/worker.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.worker`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.worker` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: The E1 local worker: one batch process that loads pplx v2 BF16, runs the smoke checks, profiles, encodes every document and query, unloads and exits.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py) |
| Source lines | 853 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Refused(RuntimeError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 59) — A start condition failed: nothing was loaded.
- `class WorkerOOM(RuntimeError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 63) — The device ran out of memory (counted, never retried at a larger size).
- `class Aborted(RuntimeError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 67) — The sampler stopped the run (host floor, device target, deadline).
- `read_meminfo(text: str | None=None) -> dict[str, int]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 72) — ``/proc/meminfo`` in bytes (MemTotal, MemAvailable, SwapTotal, SwapFree).
- `own_cgroup(text: str | None=None) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 86) — This process's cgroup v2 path (``0::/...``), or None.
- `cgroup_value(path: str, name: str, *, root: Path=Path('/sys/fs/cgroup')) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 100)
- `scope_limits(*, cgroup_text: str | None=None, root: Path=Path('/sys/fs/cgroup')) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 107) — The worker's scope: its cgroup path, ``memory.max`` and ``memory.swap.max`` (None when unlimited or unreadable) and the current/peak usage.
- `run_nvidia_smi(arguments: Sequence[str]) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 124)
- `process_cmdline(pid: int) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 129) — A process's command line (for matching only; never recorded).
- `gpu_state(run: Callable[[Sequence[str]], str]=run_nvidia_smi, cmdline: Callable[[int], str]=process_cmdline) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 138) — Device 0's memory and utilization and every compute process (pid, executable name, MiB), from nvidia-smi; each process's command line is read for the workload match only.
- `disk_free_bytes(path: Path) -> int` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 164)
- `start_problems(limits: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any], gpu: Mapping[str, Any] | None, own_pids: Sequence[int]=(), require_scope: bool=True) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 169) — Why this process must not start (empty: it may).
- `workload_match(item: Mapping[str, Any], patterns: Sequence[str]) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 205) — The workload pattern a process's name or command line matches, else None.
- `other_processes(gpu: Mapping[str, Any], own_pids: Sequence[int]=()) -> list[dict[str, Any]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 216) — The other GPU processes as a receipt records them: name and MiB only.
- `workload_problems(gpu: Mapping[str, Any], limits: Mapping[str, Any], *, own_pids: Sequence[int]=()) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 223) — No concurrent SUBSTANTIAL GPU workload (spec §8, D2).
- `sha256_file(path: Path, *, chunk: int=16 * MIB) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 249)
- `model_dir_problems(model_dir: Path, files: Mapping[str, Sequence[Any]], remote_code: Sequence[str], *, verify_digests: bool=False) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 257) — Missing or wrong files: every size always, the remote code's digest always, every digest when ``verify_digests``.
- `class LoadedModel(Protocol)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 280)
  - `count_tokens(self, chunks: Sequence[str], *, task: str='document') -> int` (line 283; public)
  - `encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int=1) -> list[np.ndarray]` (line 284; public)
  - `encode_queries(self, queries: Sequence[str], *, batch_size: int=1) -> list[np.ndarray]` (line 285; public)
  - `device_memory(self) -> dict[str, int | None]` (line 286; public)
  - `reset_peak(self) -> None` (line 287; public)
  - `unload(self) -> dict[str, Any]` (line 288; public)
- `repair_loaded_model(model: Any, model_dir: Path, *, fp32_modules: Sequence[str], tokenizer_factory: Callable[[Path], Any], read_tensor: Callable[[Path, str], Any], restore_fp32: Callable[[Any, Any], bool]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 295) — Two post-load repairs for the pinned remote code under transformers 5.18 (found on the first GPU run and reproduced on CPU with a tiny random model): * **The tokenizer.** The remote ``tokenizer`` property calls ``AutoTokenizer.from_pretrained(config._name_or_path, revision=confi…
- `drop_page_cache(paths: Sequence[Path]) -> int` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 332) — Advise the kernel to drop the shards' cached pages once they are on the device (page cache counts toward the scope's memory.max).
- `class TransformersModel` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 352) — pplx v2 through its own reviewed ``encode``/``encode_queries`` (never a reimplementation), loaded BF16 with shards straight onto device 0.
  - `__init__(self, model_dir: Path, *, precision: str, attention: str, fp32_modules: Sequence[str]) -> None` (line 356; internal)
  - `_oom(self) -> type[BaseException]` (line 427; internal)
  - `count_tokens(self, chunks: Sequence[str], *, task: str='document') -> int` (line 430; public)
  - `encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int=1) -> list[np.ndarray]` (line 434; public)
  - `encode_queries(self, queries: Sequence[str], *, batch_size: int=1) -> list[np.ndarray]` (line 444; public)
  - `device_memory(self) -> dict[str, int | None]` (line 454; public)
  - `reset_peak(self) -> None` (line 461; public)
  - `unload(self) -> dict[str, Any]` (line 464; public)
- `load_model(model_dir: Path, job: Mapping[str, Any]) -> LoadedModel` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 480)
- `class Sampler(threading.Thread)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 486) — Peaks every interval, a heartbeat file, and the abort conditions.
  - `__init__(self, limits: Mapping[str, Any], *, heartbeat: Path | None, meminfo: Callable[[], Mapping[str, int]], scope: Callable[[], Mapping[str, Any]], gpu: Callable[[], Mapping[str, Any] | None], device: Callable[[], Mapping[str, int | None]] | None=None, interval: float=1.0, on_hard_abort: Callable[[str], None] | None=None) -> None` (line 489; internal)
  - `_max(self, key: str, value: Any) -> None` (line 510; internal)
  - `sample(self) -> None` (line 514; public)
  - `run(self) -> None` (line 555; public)
  - `stop(self) -> None` (line 563; public)
- `check_vector(vector: np.ndarray, dims: int) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 592) — Why a raw output row is not a valid int8-valued vector (None: valid).
- `smoke(model: LoadedModel, job: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 607) — Spec §8's smoke checks on PUBLIC text (each recorded with its values).
- `over_limit(tokens: int, job: Mapping[str, Any]) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 658) — The harness's own limit (never a truncation): None when it fits.
- `profile(model: LoadedModel, job: Mapping[str, Any], sampler: Sampler | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 664) — Serialized indexing at each size, smallest first; a failure stops the larger sizes.
- `encode_all(model: LoadedModel, job: Mapping[str, Any], output: dict[str, Any], sampler: Sampler | None, lock: threading.Lock) -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 694)
- `run_job(job: Mapping[str, Any], *, model_factory: Callable[[Path, Mapping[str, Any]], LoadedModel]=load_model, meminfo: Callable[[], Mapping[str, int]]=read_meminfo, scope: Callable[[], Mapping[str, Any]]=scope_limits, gpu: Callable[[], Mapping[str, Any] | None]=gpu_state, heartbeat: Path | None=None, write_partial: Callable[[Mapping[str, Any]], None] | None=None, hard_exit: Callable[[int], None]=os._exit, model_check: Callable[[Mapping[str, Any]], list[str]] | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 732) — One worker process's whole job; always returns the output record.
- `main(argv: Sequence[str] | None=None) -> int` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 834)

### Module constants

- `WORKER_VERSION` ([src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 54)
- `GIB` ([src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 55)
- `MIB` ([src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 56)
- `KERNEL_HINTS` ([src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 291)

## Internal implementation anchors

- `_own_rss(field: str='VmRSS:') -> int | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 567) — Resident memory (VmRSS includes mapped shard pages; RssAnon does not).
- `_atomic_json(path: Path, value: Any) -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 579)
- `_cos(a: np.ndarray, b: np.ndarray) -> float` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 586)
- `_guard_network() -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py), line 819) — Refuse every inet connection from this process (zero network).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `module`; statically calls `model_dir_problems`, `other_processes`, `start_problems`

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

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/e1_fakes.py](../../../../../../../../tests/e1_fakes.py) — direct import
- [tests/test_e1_worker.py](../../../../../../../../tests/test_e1_worker.py) — direct import
  - `test_a_concurrent_gpu_workload_is_refused_whatever_the_desktop`
  - `test_a_restore_that_does_not_match_the_checkpoint_is_reported`
  - `test_drop_page_cache_advises_existing_files_only`
  - `test_gpu_state_parses_nvidia_smi`
  - `test_main_writes_its_output_and_a_heartbeat`
  - `test_many_small_processes_past_the_total_are_refused`
  - `test_model_files_are_checked_by_size_and_the_remote_code_by_digest`
  - `test_scope_and_meminfo_probes_read_cgroup_v2`
  - `test_the_network_guard_refuses_inet_connections`
  - `test_the_owners_desktop_gpu_set_is_no_concurrent_workload`
  - `test_the_post_load_repairs_set_the_tokenizer_and_restore_the_fp32_projection`
  - `test_the_worker_itself_is_never_its_own_concurrent_workload`

## Modification guidance

- Make changes here when the responsibility remains worker within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/worker.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/worker.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
