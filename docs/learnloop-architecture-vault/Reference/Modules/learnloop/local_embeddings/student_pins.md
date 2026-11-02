---
title: "learnloop.local_embeddings.student_pins"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/student_pins.py"
source_paths:
  - "src/learnloop/local_embeddings/student_pins.py"
source_commit: "f09c0c19b8fb81eeddeeb473a891531ed78e41fb"
source_commit_timestamp: "2026-10-26T14:02:54-04:00"
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
  - "learnloop.local_embeddings.student_pins module"
  - "src/learnloop/local_embeddings/student_pins.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.student_pins`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.student_pins` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The query student's pins (spec_local_contextual_retrieval_v1 §7.1, §7.2, §9.3, §9.6; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py) |
| Source lines | 202 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f09c0c19b8fb81eeddeeb473a891531ed78e41fb` |
| Commit timestamp | `2026-10-26T14:02:54-04:00` |

## Public API

- `students_root(data_root: Path) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 178) — Everything P2 makes lives under the data root (never in a vault or the repository, §11).
- `space_home(data_root: Path, space_id: str) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 184) — The student's home under the space it was trained for (a teacher change retires it).
- `bases_manifest_path(data_root: Path) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 192)
- `base_dir(data_root: Path, name: str) -> Path` ([source](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 196)

### Module constants

- `STUDENT_BASES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 32)
- `PRIMARY_BASE` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 92)
- `DROPPED_BASES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 94)
- `SCREEN_BASES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 96)
- `STUDENT_DIMENSIONS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 99)
- `STUDENT_PRECISION` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 100)
- `STUDENT_QUERY_METHOD` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 101)
- `TRAINER_VERSION` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 102)
- `SERVER_VERSION` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 103)
- `CHECKPOINT_FORMAT` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 104)
- `RECIPES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 107)
- `BUDGETS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 109)
- `QUERIES_PER_PASSAGE_MIN` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 111)
- `QUERIES_PER_PASSAGE_MAX` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 112)
- `PASSAGES_PER_CALL` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 114)
- `PASSAGE_TOKENS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 116)
- `TEACHER_TOP_K` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 118)
- `MAX_QUERY_TOKENS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 120)
- `LEAKAGE_MAX_TEACHER_COS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 122)
- `LEAKAGE_MAX_5GRAM_OVERLAP` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 123)
- `LEAKAGE_NGRAM` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 124)
- `EPOCHS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 126)
- `FINAL_SEEDS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 128)
- `LEARNING_RATE_FULL` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 132)
- `LEARNING_RATE_HEAD` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 133)
- `WEIGHT_DECAY` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 134)
- `WARMUP_FRACTION` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 135)
- `GRAD_CLIP_NORM` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 136)
- `TRAIN_BATCH_SIZE` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 139)
- `AGREEMENT_K` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 141)
- `LATENCY_PROBES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 143)
- `P2_GPU_HOURS_CAP` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 147)
- `TRAIN_SCOPE_MEMORY_MAX` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 149)
- `SERVE_SCOPE_MEMORY_MAX` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 151)
- `SERVE_SCOPE_MEMORY_MAX_BYTES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 152)
- `SERVE_SCOPE_SWAP_MAX` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 153)
- `SERVE_MIN_HOST_AVAILABLE_GIB` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 154)
- `SERVE_MIN_FREE_VRAM_GIB` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 155)
- `REPLAY_MAX_QUERIES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 158)
- `REPLAY_EVERY_HOURS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 160)
- `START_TIMES_KEPT` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 162)
- `STUDENT_CANARY_MIN_COS` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 164)
- `STUDENT_CANARY_QUERIES` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 165)
- `SOCKET_TIMEOUT_S` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 168)
- `YIELD_WAIT_S` ([src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py), line 172)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `REPLAY_EVERY_HOURS`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `module`; statically calls `base_dir`, `bases_manifest_path`, `space_home`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `module`; statically calls `space_home`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `module`; statically calls `bases_manifest_path`, `space_home`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]], [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_due_replay_is_scheduled_for_a_fully_indexed_library`
  - `test_a_newly_held_out_familys_older_rows_leave_training`
  - `test_a_run_is_reused_only_on_the_dataset_it_learned`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_a_targets_run_interrupted_before_the_bank_shards_admits_no_question`
  - `test_consecutive_owner_decisions_resolve_to_their_evaluation`
  - `test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint`
  - `test_only_the_current_producers_pinned_families_are_provenance`
  - `test_reevaluation_strata_come_from_the_checkpoint_training_families`
  - `test_targets_are_one_metered_query_batch_with_the_canaries_and_the_cosine_guard`
  - `test_targets_refuse_a_drifted_teacher_and_wait_for_a_busy_gpu`
  - `test_the_adopted_student_starts_lazily_serves_and_queues_the_teacher_replay`
  - `test_the_default_base_loader_is_called_with_its_keyword_only_device`
  - `test_the_pinned_families_are_every_family_the_run_consumed`
  - `test_the_query_process_never_runs_a_changed_base`
  - `test_the_query_process_refuses_outside_its_4g_scope_and_under_the_host_floor`
  - `test_the_schedule_screens_both_bases_then_recipes_then_seeds_by_expected_utility`
  - `test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal`
  - `test_the_serving_checkpoint_is_reevaluated_on_corrected_labels`
  - `test_the_student_is_0_6b_with_pplx_primary_and_qwen3_5_dropped`
  - `test_the_trainer_job_and_manifest_pin_the_training_families`
  - `test_the_trainer_refuses_a_base_that_fails_its_pins`
  - `test_the_whole_p2_dry_run_starts_nothing_and_estimates_time_gpu_and_plan_calls`
- [tests/test_query_student_gpu.py](../../../../../../tests/test_query_student_gpu.py) — direct import
  - `test_a_tiny_student_trains_on_the_gpu_under_the_lock_and_the_floors`

## Modification guidance

- Make changes here when the responsibility remains student pins within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/student_pins.py](../../../../../../src/learnloop/local_embeddings/student_pins.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
