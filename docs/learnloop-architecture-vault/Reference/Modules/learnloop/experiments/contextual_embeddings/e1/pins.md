---
title: "learnloop.experiments.contextual_embeddings.e1.pins"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/pins.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/pins.py"
source_commit: "92352889a9cd22c4b07169f68482a058c704033f"
source_commit_timestamp: "2026-10-23T23:25:08-04:00"
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
  - "learnloop.experiments.contextual_embeddings.e1.pins module"
  - "src/learnloop/experiments/contextual_embeddings/e1/pins.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.pins`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.pins` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: E1's frozen constants (spec §8, §9, D2): the local model, its files, the separate environment, the GPU and memory bounds, the $5 plan and the smoke.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py) |
| Source lines | 260 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `92352889a9cd22c4b07169f68482a058c704033f` |
| Commit timestamp | `2026-10-23T23:25:08-04:00` |

## Public API

- `class Assumptions` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 194)
  - `as_dict(self) -> dict[str, Any]` (line 211; public)
- `e1_pins_fingerprint() -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 218) — One hash of every E1 pin (part of the E1 plan id).
- `model_identity() -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 238) — The v2 model's identity in every E1 space id: repo, revision, weight precision.
- `v2_pin()` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 244) — The v2 model as an E0 ``EmbeddingPin`` (its identity fields feed the E0 space-id formula; it is never sent over HTTP and bills nothing).

### Module constants

- `E1_HARNESS_VERSION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 31)
- `MODEL_REPO` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 34)
- `MODEL_REVISION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 35)
- `MODEL_LICENSE` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 36)
- `MODEL_DIMENSIONS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 37)
- `MODEL_MATRYOSHKA` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 39)
- `MODEL_PARAMETERS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 40)
- `MODEL_FILES` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 45)
- `REMOTE_CODE_FILES` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 70)
- `MODEL_DISK_BYTES` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 71)
- `DOWNLOAD_FREE_DISK_GIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 73)
- `LOCAL_PYTHON` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 79)
- `LOCAL_REQUIREMENTS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 80)
- `LOCAL_MIN_TRANSFORMERS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 82)
- `PRECISION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 85)
- `DEFERRED_PRECISIONS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 86)
- `ATTENTION_IMPLEMENTATION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 88)
- `FP32_MODULES` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 90)
- `GPU_HOURS_CAP` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 95)
- `DEVICE_PEAK_TARGET_GIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 97)
- `SCOPE_MEMORY_MAX` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 100)
- `SCOPE_SWAP_MAX` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 101)
- `SCOPE_MEMORY_MAX_BYTES` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 102)
- `MIN_HOST_AVAILABLE_GIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 104)
- `MIN_FREE_VRAM_GIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 105)
- `MAX_OTHER_GPU_PROCESS_MIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 110)
- `MAX_OTHER_GPU_TOTAL_MIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 112)
- `FORBIDDEN_GPU_WORKLOADS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 115)
- `MAX_GPU_UTILIZATION_PCT` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 116)
- `HOST_FLOOR_GIB` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 119)
- `SAMPLE_INTERVAL_S` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 120)
- `HEARTBEAT_GRACE_S` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 123)
- `KILL_GRACE_S` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 125)
- `PROFILE_TOKENS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 130)
- `PROFILE_REPEATS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 131)
- `MAX_DOCUMENT_TOKENS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 133)
- `INDEX_BATCH_SIZE` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 135)
- `QUERY_BATCH_SIZE` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 136)
- `BATCH_INVARIANCE_MIN_COS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 138)
- `CONTEXT_SENSITIVITY_MAX_COS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 140)
- `SMOKE_CONTEXT` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 142)
- `SMOKE_QUERY` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 152)
- `SMOKE_PADDING_DOCUMENT` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 153)
- `E1_CAP_USD` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 156)
- `E1_ALLOCATION_USD` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 159)
- `E1_MAX_PAID_REQUESTS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 160)
- `E1_LEDGER_DIR` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 163)
- `E1_PLAN_PREFIX` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 164)
- `SUPPLEMENT_DEPTH` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 167)
- `SUPPLEMENT_PROMPT_VERSION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 168)
- `SUPPLEMENT_ADJUDICATE_VERSION` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 169)
- `FILLABLE_ARMS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 171)
- `V2_ARMS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 174)
- `E0_REPRESENTATION_ARMS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 181)
- `RETAIN_GAIN_MIN` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 186)
- `NONINFERIORITY_MARGIN` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 187)
- `SUPPLEMENT_KAPPA_MIN` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 189)
- `V2_COMPLETION_MIN` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 190)
- `ASSUMPTIONS` ([src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py), line 215)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/gpu_meter|learnloop.experiments.contextual_embeddings.e1.gpu_meter]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/ledger|learnloop.experiments.contextual_embeddings.e1.ledger]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `module`; statically calls `v2_pin`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `module`; statically calls `e1_pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `EmbeddingPin`; calls `EmbeddingPin`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/gpu_meter|learnloop.experiments.contextual_embeddings.e1.gpu_meter]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/ledger|learnloop.experiments.contextual_embeddings.e1.ledger]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_replay_reproduces_e0_without_any_call_and_the_plan_is_frozen`
  - `test_the_scoped_launcher_caps_memory_and_passes_no_key`
  - `test_the_separate_environment_must_carry_the_pinned_versions`
  - `test_the_whole_pilot_with_fakes`
- [tests/test_e1_worker.py](../../../../../../../../tests/test_e1_worker.py) — direct import
  - `test_the_pinned_remote_code_digests_are_the_reviewed_files`
- [tests/test_local_index.py](../../../../../../../../tests/test_local_index.py) — direct import
  - `test_the_moved_pins_equal_e1s`

## Modification guidance

- Make changes here when the responsibility remains pins within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/pins.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/pins.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
