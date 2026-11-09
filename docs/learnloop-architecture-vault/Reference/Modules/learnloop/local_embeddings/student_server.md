---
title: "learnloop.local_embeddings.student_server"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/student_server.py"
source_paths:
  - "src/learnloop/local_embeddings/student_server.py"
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
  - "learnloop.local_embeddings.student_server module"
  - "src/learnloop/local_embeddings/student_server.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.student_server`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.student_server` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The query process: the adopted student, serving query vectors over a Unix socket (spec_local_contextual_retrieval_v1 §7.1 "Serving", §7.2; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/student_server.py](../../../../../../src/learnloop/local_embeddings/student_server.py) |
| Source lines | 342 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `gpu_lock_free(path: Path) -> bool` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 90) — Whether no exclusive GPU job holds the lock now (probed, never held).
- `choose_device(job: Mapping[str, Any], *, gpu: Callable[[], Mapping[str, Any] | None]=W.gpu_state, lock_free: Callable[[Path], bool]=gpu_lock_free) -> tuple[str, str]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 105) — ``(device, why)``: the GPU when >= the VRAM floor is free and the GPU lock is free, else the CPU.
- `start_problems(job: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 125)
- `checkpoint_problems(job: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 142) — The checkpoint's files against their SHA-256 pins and its own digest.
- `base_check(job: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 159) — The adopted base's pinned files, checked before ``load_base`` runs any of its code (``trust_remote_code``): Codex review F6.
- `startup_problems(job: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 166) — Everything checked before any model code is loaded: the scope and floor, the checkpoint pins and the base pins.
- `canary_check(service: Any, job: Mapping[str, Any], device_class: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 179)
- `class TorchService` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 190) — The checkpoint on its device, BF16, FP32 normalized output.
  - `__init__(self, job: Mapping[str, Any], device: str) -> None` (line 193; internal)
  - `encode(self, texts: Sequence[str]) -> list[list[float]]` (line 214; public)
- `load_service(job: Mapping[str, Any], device: str) -> Any` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 219)
- `serve_forever(service: Any, socket_path: Path, *, idle_s: float, timeout_s: float, meminfo: Callable[[], Mapping[str, int]]=W.read_meminfo, floor_gib: float=3.0, clock: Callable[[], float]=time.monotonic, ready: Callable[[], None] | None=None) -> str` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 223) — Answer JSON-line requests until idle, a shutdown request or the host floor; returns why it stopped.
- `main(argv: Sequence[str] | None=None) -> int` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 299)

### Module constants

- `SERVER_VERSION` ([src/learnloop/local_embeddings/student_server.py](../../../../../../src/learnloop/local_embeddings/student_server.py), line 54)
- `W` ([src/learnloop/local_embeddings/student_server.py](../../../../../../src/learnloop/local_embeddings/student_server.py), line 73)

## Internal implementation anchors

- `_worker() -> Any` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 57)
- `_trainer() -> Any` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 76)
- `_cos(a: Sequence[float], b: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 173)
- `_read_line(connection: socket.socket) -> bytes` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 267)
- `_answer(service: Any, raw: bytes) -> tuple[dict[str, Any], bool]` ([source](../../../../../../src/learnloop/local_embeddings/student_server.py), line 279)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/student_trainer|learnloop.local_embeddings.student_trainer]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/worker|learnloop.local_embeddings.worker]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `argparse`, `collections`, `fcntl`, `importlib`, `json`, `os`, `pathlib`, `socket`, `sys`, `time`, `typing`
- Third party: `numpy`, `safetensors`, `torch`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_client_that_gives_up_never_stops_the_query_process`
  - `test_the_query_process_never_runs_a_changed_base`
  - `test_the_query_process_refuses_outside_its_4g_scope_and_under_the_host_floor`

## Modification guidance

- Make changes here when the responsibility remains student server within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/student_server.py](../../../../../../src/learnloop/local_embeddings/student_server.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
