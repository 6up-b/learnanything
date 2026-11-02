---
title: "learnloop.local_embeddings.student_trainer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/student_trainer.py"
source_paths:
  - "src/learnloop/local_embeddings/student_trainer.py"
source_commit: "e4b7e3b9f05b64debba3cea19070d7b2327b2c64"
source_commit_timestamp: "2026-10-26T15:46:59-04:00"
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
  - "learnloop.local_embeddings.student_trainer module"
  - "src/learnloop/local_embeddings/student_trainer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.student_trainer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.student_trainer` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The query-student trainer: one run, one recipe, one seed, then exit (spec_local_contextual_retrieval_v1 §7.1, §7.2; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/student_trainer.py](../../../../../../src/learnloop/local_embeddings/student_trainer.py) |
| Source lines | 468 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e4b7e3b9f05b64debba3cea19070d7b2327b2c64` |
| Commit timestamp | `2026-10-26T15:46:59-04:00` |

## Public API

- `sha256_file(path: Path) -> str` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 83)
- `base_problems(base_dir: Path, base: Mapping[str, Any], *, verify_weights: bool=False) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 87) — Missing or wrong base files: sizes always, digests of the code and small files always, of every file when ``verify_weights``; an unpinned Python file is refused.
- `build_student(base_model: Any, *, hidden: int, dims: int, pooling: str, frozen_base: bool) -> Any` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 111)
- `hidden_size(model: Any, base: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 141) — The loaded model's own width (the pinned base's is 1024; a test's tiny model is smaller).
- `load_base(base_dir: Path, base: Mapping[str, Any], *, device: str) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 147) — The pinned base and its tokenizer, offline, FP32 master weights on ``device``.
- `tokenize(tokenizer: Any, texts: Sequence[str], *, prefix: str, max_tokens: int, device: str) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 160)
- `recipe_loss(student_vectors: Any, teacher_vectors: Any, *, recipe: str, documents: Any | None=None, topk: Any | None=None, positives: Sequence[Sequence[int]] | None=None, temperature: float=0.05, negatives: Sequence[Sequence[int]] | None=None) -> tuple[Any, dict[str, float]]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 166) — Spec §7.1's losses (all terms per-query means, summed unweighted).
- `encode(student: Any, tokenizer: Any, texts: Sequence[str], *, prefix: str, max_tokens: int, device: str, batch_size: int=64, dtype: Any=None) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 207)
- `agreement(student: np.ndarray, teacher: np.ndarray, documents: np.ndarray, k: int) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 225) — Per query: the share of the teacher's top-k over the whole index the student's top-k holds.
- `run_training(job: Mapping[str, Any], *, model_factory: Callable[..., tuple[Any, Any]]=load_base, device: str | None=None, sampler: Any=None, base_check: Callable[[Mapping[str, Any]], list[str]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 248) — One run: train, measure, save the checkpoint files; returns the output record.
- `save_checkpoint(student: Any, directory: Path, *, frozen_base: bool) -> dict[str, str]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 389) — The head (and the base unless it stayed frozen) as safetensors; ``{file: sha256}``.
- `checkpoint_digest(manifest: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 402) — The checkpoint's pin: SHA-256 over its manifest's identity fields and file digests.
- `main(argv: Sequence[str] | None=None) -> int` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 414)

### Module constants

- `TRAINER_VERSION` ([src/learnloop/local_embeddings/student_trainer.py](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 57)
- `W` ([src/learnloop/local_embeddings/student_trainer.py](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 80)

## Internal implementation anchors

- `_worker() -> Any` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 60) — The 9B worker's probes, sampler and network guard: imported as a package module when ``learnloop`` is importable (the tests), else loaded from the sibling file by path (the separate environment, where only this directory's two scripts exist).
- `_load_split(directory: Path, split: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 235)
- `_device_class(device: str) -> str` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 370)
- `_latency(student: Any, tokenizer: Any, texts: Sequence[str], prefix: str, max_tokens: int, device: str, dtype: Any, probes: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_trainer.py), line 374)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/local_embeddings/student_server|learnloop.local_embeddings.student_server]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `base_problems`, `checkpoint_digest`, `module`, `sha256_file`; statically calls `base_problems`, `checkpoint_digest`, `sha256_file`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/worker|learnloop.local_embeddings.worker]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `argparse`, `collections`, `hashlib`, `importlib`, `json`, `math`, `os`, `pathlib`, `platform`, `sys`, `threading`, `time`, `traceback`, `typing`
- Third party: `numpy`, `safetensors`, `torch`, `transformers`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/local_embeddings/student_server|learnloop.local_embeddings.student_server]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_an_unpinned_python_file_or_a_wrong_digest_refuses_the_base`
  - `test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint`
  - `test_only_the_current_producers_pinned_families_are_provenance`
  - `test_reevaluation_strata_come_from_the_checkpoint_training_families`
  - `test_the_default_base_loader_is_called_with_its_keyword_only_device`
  - `test_the_query_process_never_runs_a_changed_base`
  - `test_the_trainer_job_and_manifest_pin_the_training_families`
  - `test_the_trainer_refuses_a_base_that_fails_its_pins`
- [tests/test_query_student_gpu.py](../../../../../../tests/test_query_student_gpu.py) — direct import
  - `test_a_tiny_student_trains_on_the_gpu_under_the_lock_and_the_floors`

## Modification guidance

- Make changes here when the responsibility remains student trainer within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/student_trainer.py](../../../../../../src/learnloop/local_embeddings/student_trainer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
