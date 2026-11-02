---
title: "learnloop.local_embeddings.pins"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/pins.py"
source_paths:
  - "src/learnloop/local_embeddings/pins.py"
source_commit: "c05eae57933f963158a782836b8d6b88af5d80a2"
source_commit_timestamp: "2026-10-24T15:05:22-04:00"
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
  - "learnloop.local_embeddings.pins module"
  - "src/learnloop/local_embeddings/pins.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.pins`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.pins` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The local space's pins (spec_local_contextual_retrieval_v1 §4.1, §4.2, §7.2, §9.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c05eae57933f963158a782836b8d6b88af5d80a2` |
| Commit timestamp | `2026-10-24T15:05:22-04:00` |

## Public API

- `data_root() -> Path` ([source](../../../../../../src/learnloop/local_embeddings/pins.py), line 126) — ``$XDG_DATA_HOME/learnloop`` (default ``~/.local/share/learnloop``; Q11).
- `model_dir(root: Path | None=None) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/pins.py), line 133)
- `env_dir(root: Path | None=None) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/pins.py), line 137)
- `manifest_path(root: Path | None=None) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/pins.py), line 144) — The setup record (written only by ``learnloop embeddings local setup``).
- `limits(*, deadline_unix: float | None=None) -> dict` ([source](../../../../../../src/learnloop/local_embeddings/pins.py), line 150) — The worker's limits (every one a ``keep`` guardrail above).

### Module constants

- `MODEL_REPO` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 21)
- `MODEL_REVISION` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 22)
- `MODEL_DIMENSIONS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 23)
- `MODEL_FILES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 24)
- `REMOTE_CODE_FILES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 48)
- `MODEL_DISK_BYTES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 49)
- `DOWNLOAD_FREE_DISK_GIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 51)
- `LOCAL_PYTHON` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 54)
- `LOCAL_REQUIREMENTS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 55)
- `PRECISION` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 57)
- `ATTENTION_IMPLEMENTATION` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 58)
- `FP32_MODULES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 59)
- `OUTPUT_FORMAT` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 60)
- `SCORE_TRANSFORM` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 62)
- `QUERY_METHOD` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 63)
- `SCOPE_MEMORY_MAX` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 66)
- `SCOPE_SWAP_MAX` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 67)
- `SCOPE_MEMORY_MAX_BYTES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 68)
- `MIN_HOST_AVAILABLE_GIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 69)
- `MIN_FREE_VRAM_GIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 70)
- `MAX_OTHER_GPU_PROCESS_MIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 71)
- `MAX_OTHER_GPU_TOTAL_MIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 72)
- `FORBIDDEN_GPU_WORKLOADS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 73)
- `MAX_GPU_UTILIZATION_PCT` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 74)
- `HOST_FLOOR_GIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 75)
- `DEVICE_PEAK_TARGET_GIB` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 76)
- `SAMPLE_INTERVAL_S` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 77)
- `HEARTBEAT_GRACE_S` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 78)
- `KILL_GRACE_S` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 79)
- `MIN_SLOT_S` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 81)
- `MAX_DOCUMENT_TOKENS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 88)
- `INDEX_BATCH_SIZE` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 89)
- `QUERY_BATCH_SIZE` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 90)
- `BATCH_INVARIANCE_MIN_COS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 91)
- `CONTEXT_SENSITIVITY_MAX_COS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 92)
- `CANARY_MIN_COS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 95)
- `PROFILE_TOKENS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 97)
- `PROFILE_REPEATS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 98)
- `SMOKE_CONTEXT` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 102)
- `SMOKE_QUERY` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 112)
- `SMOKE_PADDING_DOCUMENT` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 113)
- `CANARY_DOCUMENTS` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 114)
- `CANARY_QUERIES` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 121)
- `WORKER_VERSION` ([src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py), line 123)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/local_embeddings/gpu_meter|learnloop.local_embeddings.gpu_meter]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/identity|learnloop.local_embeddings.identity]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `module`
- [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]] — imports `module`; statically calls `data_root`, `env_dir`, `manifest_path`, `model_dir`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `module`; statically calls `data_root`, `limits`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `module`; statically calls `data_root`, `limits`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `module`; statically calls `data_root`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `module`; statically calls `data_root`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/local_embeddings/gpu_meter|learnloop.local_embeddings.gpu_meter]], [[Reference/Modules/learnloop/local_embeddings/identity|learnloop.local_embeddings.identity]], [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]], [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/local_embeddings_fakes.py](../../../../../../tests/local_embeddings_fakes.py) — direct import
- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_an_interrupted_setup_resumes_the_install_and_the_download`
  - `test_setup_verifies_the_files_records_the_epoch_and_adopts_without_moving`
  - `test_the_commands_dry_run_without_starting_anything`
  - `test_the_moved_pins_equal_e1s`
  - `test_the_worker_encodes_the_canaries_with_every_batch`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_the_query_process_answers_over_its_unix_socket_and_exits_idle`
  - `test_the_worker_writes_teacher_targets_as_int8_shards`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains pins within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/pins.py](../../../../../../src/learnloop/local_embeddings/pins.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
