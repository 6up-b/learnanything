---
title: "learnloop.figures.sketch_engine"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/sketch_engine.py"
source_paths:
  - "src/learnloop/figures/sketch_engine.py"
source_commit: "0789bfcbea576a16363b70c092fc6fdc7c47cfea"
source_commit_timestamp: "2026-10-31T19:50:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.sketch_engine module"
  - "src/learnloop/figures/sketch_engine.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.sketch_engine`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.sketch_engine` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: The sketch engine's sidecar runner (spec_reader_show_me_figures_v1 §9.2-9.4; RW5d P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py) |
| Source lines | 500 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0789bfcbea576a16363b70c092fc6fdc7c47cfea` |
| Commit timestamp | `2026-10-31T19:50:29-04:00` |

## Public API

- `class EngineUnavailable(RuntimeError)` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 98) — The engine artifact is missing, has the wrong digest or imports more than the deny-all shim answers.
- `class SketchRunError(RuntimeError)` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 103) — A call into the program failed: ``status`` (:data:`STATUS_NAMES`) and the engine's message (code-written, quoting the program's own error).
  - `__init__(self, status: int, message: str, *, trap: bool=False) -> None` (line 107; internal)
- `class EngineInfo` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 116)
- `artifact_digest(path: Path=ENGINE_PATH) -> str` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 121)
- `deadline_ticks(seconds: float) -> int` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 166) — A call's epoch deadline, in clock ticks from now: at least ``seconds`` (one more tick, as the first may come at once).
- `engine_info(*, path: Path=ENGINE_PATH, expected: str=ENGINE_SHA256) -> EngineInfo` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 233)
- `engine_ready(*, path: Path=ENGINE_PATH, expected: str=ENGINE_SHA256) -> bool` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 238)
- `class SketchEngine` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 248) — One sealed engine instance (one program at a time).
  - `__init__(self, *, path: Path=ENGINE_PATH, expected: str=ENGINE_SHA256, deadline: float | None=None) -> None` (line 256; internal)
  - `_define_shim(self, linker: Any) -> None` (line 295; internal)
  - `_call(self, name: str, function: Any, *args: int) -> Any` (line 329; internal) — One call with fresh backstops: fuel, and an epoch deadline of its own, :data:`CALL_SECONDS` (or what is left before :attr:`deadline`) in ticks of the engine's shared clock.
  - `_write(self, data: bytes) -> int` (line 357; internal)
  - `_output(self) -> str` (line 364; internal)
  - `_run(self, name: str, *args: int) -> str` (line 369; internal)
  - `limits(self) -> dict[str, Any]` (line 376; public)
  - `load(self, code: str) -> dict[str, bool]` (line 379; public)
  - `init(self, params: Mapping[str, float], seed: int) -> None` (line 386; public) — Start a run.
  - `step(self, params: Mapping[str, float], dt: float, *, index: int, count: int=1) -> None` (line 398; public)
  - `view(self, params: Mapping[str, float], *, index: int) -> Any` (line 402; public)
  - `probes(self, params: Mapping[str, float], *, index: int) -> Any` (line 406; public)
  - `view_text(self, params: Mapping[str, float], *, index: int) -> str` (line 410; public) — The scene exactly as the engine wrote it (the parity corpus compares text).
  - `probes_text(self, params: Mapping[str, float], *, index: int) -> str` (line 416; public)
  - `_release_clock(self) -> None` (line 420; internal)
  - `close(self) -> None` (line 425; public)
  - `__enter__(self) -> 'SketchEngine'` (line 435; internal)
  - `__exit__(self, *_exc: Any) -> None` (line 438; internal)

### Module constants

- `ENGINE_PATH` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 51)
- `LOCK_PATH` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 53)
- `ENGINE_SHA256` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 57)
- `ENGINE_VERSION` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 59)
- `SKETCH_MEMORY_BYTES` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 62)
- `SKETCH_FUEL_PER_CALL` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 67)
- `SKETCH_SERIALIZE_TICKS` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 71)
- `WASM_MEMORY_BYTES` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 74)
- `WASM_FUEL_PER_CALL` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 75)
- `CALL_SECONDS` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 76)
- `EPOCH_TICK_SECONDS` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 79)
- `WASM_STACK_BYTES` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 82)
- `STDERR_KEEP` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 84)
- `STATUS_NAMES` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 88)
- `ALLOWED_IMPORTS` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 91)
- `_EBADF` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 94)
- `_ENOSYS` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 95)
- `_COMPILED` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 175)
- `_COMPILED_GUARD` ([src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py), line 176)

### Explicit exports

`__all__` declares:

- `ALLOWED_IMPORTS`
- `CALL_SECONDS`
- `ENGINE_PATH`
- `ENGINE_SHA256`
- `ENGINE_VERSION`
- `EPOCH_TICK_SECONDS`
- `EngineInfo`
- `EngineUnavailable`
- `SKETCH_FUEL_PER_CALL`
- `SKETCH_MEMORY_BYTES`
- `SKETCH_SERIALIZE_TICKS`
- `STATUS_NAMES`
- `SketchEngine`
- `SketchRunError`
- `WASM_FUEL_PER_CALL`
- `WASM_MEMORY_BYTES`
- `artifact_digest`
- `deadline_ticks`
- `engine_info`
- `engine_ready`

## Internal implementation anchors

- `class _EpochClock` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 125) — The shared epoch of one ``wasmtime.Engine`` as a clock (Codex review F7).
- `_close_compiled() -> None` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 179) — Free the compiled modules and engines before the interpreter tears down wasmtime's own module (otherwise their finalizers run against a half-gone ffi).
- `_compiled(path_text: str, expected: str) -> tuple[Any, Any, str, _EpochClock]` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 197)
- `_compile(path_text: str, expected: str) -> tuple[Any, Any, str, _EpochClock]` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 208)
- `_label(name: str) -> str` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 442)
- `_canonical(value: Any) -> Any` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 446) — -0.0 as 0.0, everywhere in an input (Astra round 2: the desktop's JSON.stringify writes -0 as 0, so the sidecar must too).
- `_json(value: Any) -> bytes` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 459)
- `_is_exhaustion(exc: Exception) -> bool` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 463)
- `_trap_reason(exc: Exception) -> str` ([source](../../../../../../src/learnloop/figures/sketch_engine.py), line 468)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/katex_tree|learnloop.figures.katex_tree]] — imports `module`; statically calls `SketchEngine`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `ENGINE_SHA256`, `ENGINE_VERSION`, `SketchEngine`, `SketchRunError`, `engine_ready`; statically calls `SketchEngine`, `engine_ready`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `ENGINE_SHA256`, `SketchEngine`, `SketchRunError`; statically calls `SketchRunError`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `atexit`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `pathlib`, `threading`, `time`, `typing`
- Third party: `wasmtime`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/katex_tree|learnloop.figures.katex_tree]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/katex_meaning.py](../../../../../../tests/katex_meaning.py) — direct import
- [tests/sketch_parity_corpus.py](../../../../../../tests/sketch_parity_corpus.py) — direct import
- [tests/test_rw5c_katex_tree.py](../../../../../../tests/test_rw5c_katex_tree.py) — direct import
  - `test_the_engine_variant_is_pinned_and_differs_from_the_sketch_engine_by_its_defines`
  - `test_the_variant_runs_under_the_sketch_engines_caps_but_its_own_work_budget`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_a_check_loads_one_engine_however_many_segments_it_reads`
- [tests/test_sketch_engine.py](../../../../../../tests/test_sketch_engine.py) — direct import
  - `test_a_call_never_starts_past_the_callers_deadline`
  - `test_a_digest_mismatch_refuses_to_load`
  - `test_a_load_time_loop_is_capped_too`
  - `test_a_new_load_starts_from_nothing`
  - `test_a_thrown_error_is_reported_in_the_engines_words`
  - `test_a_trapped_instance_is_never_called_again`
  - `test_an_endless_loop_in_any_entry_point_hits_the_work_cap`
  - `test_another_stores_epoch_tick_does_not_trap_a_running_call`
  - `test_load_reports_entry_points_and_calls_return_json`
  - `test_memory_and_recursion_have_their_own_statuses`
  - `test_non_finite_numbers_cross_as_named_strings`
  - `test_one_sketchs_timeout_does_not_stop_a_concurrent_one`
  - `test_seeding_depends_on_seed_and_step_never_on_how_calls_are_chunked`
  - `test_the_artifact_hashes_to_the_pin_in_the_lock_file_and_the_runner`
  - `test_the_caps_are_compiled_in_and_match_the_constants`
  - `test_the_desktop_pins_the_same_digest`
  - `test_the_epoch_clock_runs_only_while_an_engine_is_open`
  - `test_the_module_imports_only_what_the_deny_all_shim_answers`
- [tests/test_sketch_hostile.py](../../../../../../tests/test_sketch_hostile.py) — direct import
  - `test_a_giant_string_hits_the_memory_cap`
  - `test_an_oversized_result_is_refused_by_the_engine_or_the_validator`
  - `test_cyclic_results_are_an_error_not_a_hang`
  - `test_dynamic_import_and_module_loading_fail_inside_the_engine`
  - `test_getters_and_tojson_run_under_a_budget`
  - `test_shared_hostile_corpus_runs_the_same_in_the_sidecar`
- [tests/test_sketch_parity.py](../../../../../../tests/test_sketch_parity.py) — direct import
  - `test_the_parity_corpus_is_what_the_pinned_engine_returns`
- [tests/test_sketch_sandbox_review.py](../../../../../../tests/test_sketch_sandbox_review.py) — direct import
  - `test_a_program_that_changes_its_state_when_read_is_checked_under_the_playback_schedule`
  - `test_an_on_step_prediction_change_is_graded_at_exactly_that_value`
  - `test_every_init_runs_on_a_freshly_loaded_program`
  - `test_neither_host_lets_a_program_see_negative_zero`
  - `test_reads_never_carry_over_into_the_next_run`
  - `test_the_signed_zero_program_is_graded_as_the_desktop_draws_it`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_report_from_an_older_verifier_is_reverified_before_it_is_shown`
  - `test_an_engine_reverification_is_a_verifier_judgment_recorded_once`
  - `test_off_never_loads_the_engine`
  - `test_the_tier_is_off_when_the_engine_cannot_run_here`
- [tests/test_sketch_verify.py](../../../../../../tests/test_sketch_verify.py) — direct import
  - `test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget`
  - `test_sketch_predictions_are_decided_by_code_in_the_engine`
  - `test_the_largest_legal_grid_is_verified_one_point_read_at_a_time`

## Modification guidance

- Make changes here when the responsibility remains sketch engine within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/sketch_engine.py](../../../../../../src/learnloop/figures/sketch_engine.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
