---
title: "learnloop.figures.sketch_verify"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/sketch_verify.py"
source_paths:
  - "src/learnloop/figures/sketch_verify.py"
source_commit: "db1d84da96b008e4c02bf3e1feeada26bd30ba9b"
source_commit_timestamp: "2026-10-31T19:55:24-04:00"
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
  - "learnloop.figures.sketch_verify module"
  - "src/learnloop/figures/sketch_verify.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.sketch_verify`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.sketch_verify` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Headless verification of a sketch (spec_reader_show_me_figures_v1 §9.5; RW5d P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py) |
| Source lines | 814 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `db1d84da96b008e4c02bf3e1feeada26bd30ba9b` |
| Commit timestamp | `2026-10-31T19:55:24-04:00` |

## Public API

- `class SketchReport` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 101) — What verification found, as stored in ``verification_report_json``.
  - `as_dict(self) -> dict[str, Any]` (line 127; public)
- `tested_digest(scene_text: str, probes_text: str) -> str` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 233) — One read's digest, as the desktop's ``sceneDigest`` computes it: the SHA-256 of the scene text, a NUL and the probes text (UTF-8), the first :data:`TESTED_DIGEST_HEX` hex digits.
- `claim_entries(claim: K.CompiledClaim, probe: K.Probe, value: Any) -> int` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 406) — How many entries a claim's check at one point read evaluates (times :attr:`.sketch.CompiledClaim.entry_work`, the estimate an early refusal looks at before it runs).
- `check_claim(compiled: K.CompiledSketch, claim: K.CompiledClaim, sample: _Sample, budget: _Budget | None=None) -> str | None` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 419) — One claim at one point read: None when it holds, else why not.
- `prediction_target_step(compiled: K.CompiledSketch, index: int) -> int` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 517) — The clock step a prediction is graded at (Codex review F5), shared with the desktop so its playback stops exactly there (:func:`.sketch.prediction_step`).
- `prediction_outcome(compiled: K.CompiledSketch, engine: SketchEngine, index: int, *, seed: int=VERIFY_SEED, record: list[tuple[int, dict[str, float], int, str, str, str]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 525) — What a sketch's prediction observes and its answer, decided by code in the engine.
- `verify_sketch(compiled: K.CompiledSketch, *, engine_factory: EngineFactory=SketchEngine, span_texts: Mapping[str, str] | None=None) -> SketchReport` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 606) — Steps 2-5 on a parsed program (step 1's static half is :func:`.sketch.parse_sketch`): ``failed`` with the reason, or ``illustrative`` with its check lines.

### Module constants

- `VERIFY_SEED` ([src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py), line 75)
- `VERIFIER_REPORT_VERSION` ([src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py), line 89)
- `TESTED_DIGEST_HEX` ([src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py), line 92)
- `PROPERTY_WORDS` ([src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py), line 94)
- `_TICK_WORK` ([src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py), line 219)

### Explicit exports

`__all__` declares:

- `PROPERTY_WORDS`
- `SketchReport`
- `TESTED_DIGEST_HEX`
- `VERIFIER_REPORT_VERSION`
- `VERIFY_SEED`
- `check_claim`
- `claim_entries`
- `prediction_outcome`
- `prediction_target_step`
- `tested_digest`
- `verify_sketch`

## Internal implementation anchors

- `class _Failed(Exception)` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 139)
- `_point_text(point: Mapping[str, float]) -> str` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 147)
- `_env(compiled: K.CompiledSketch, point: Mapping[str, float], step: int) -> dict[str, float]` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 151)
- `class _Budget(G.Meter)` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 160) — Verification's own limits (Codex review F1, F2): the engine output it reads (:data:`.sketch.SKETCH_MAX_VERIFY_OUTPUT_BYTES`), the claim work it may do (:data:`.sketch.SKETCH_MAX_CLAIM_WORK`) and its wall clock (:data:`.sketch.SKETCH_VERIFY_SECONDS`, also every engine call's dead…
- `class _Sample` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 223) — One point read: the parsed scene and probes, held only while it is validated, bound and checked (never kept: Codex review F1).
- `_point_key(point: Mapping[str, float], step: int) -> tuple[str, int]` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 242)
- `_load(compiled: K.CompiledSketch, engine: SketchEngine, budget: _Budget) -> None` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 246)
- `_stream(compiled: K.CompiledSketch, engine: SketchEngine, grid: Sequence[Mapping[str, float]], steps: Sequence[int], budget: _Budget, *, extra_reads: bool=False) -> Iterator[tuple[_Sample, str]]` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 261) — Load, then at every grid point (in the given order) init (a freshly loaded program: :meth:`.SketchEngine.init`) and read each of ``steps`` (``view()`` then ``probes()``, as the desktop reads), validated, one at a time: each step read is yielded with its digest and dropped before…
- `_binding_problem(compiled: K.CompiledSketch, sample: _Sample, elements: Mapping[str, Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 308)
- `_bound_equal(element: Mapping[str, Any], value: Any, shape: str) -> bool` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 321)
- `_scope(claim: K.Claim, shape: str, kind: str, on_domain: bool) -> str | None | bool` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 345) — The attribute a passing claim speaks for on one bound element: ``None`` (all of it), an attribute name, or False (nothing: a series claim over an index the line is not drawn at).
- `_on_domain(claim: K.Claim, element: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 363) — A line bound to a series is drawn at the claim's index: its ``i``-th x is ``var_from + i * var_step`` (the claim's tolerance).
- `_close(value: float, expected: float) -> bool` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 371)
- `_z() -> float` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 375)
- `_rk4(dx: G.Node, dy: G.Node, names: Sequence[str], env: Mapping[str, float], x: float, y: float, h: float, steps: int, budget: _Budget | None=None) -> list[tuple[float, float]]` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 379) — The grammar's fixed-step RK4 (``spec._path``'s operation order); with a ``budget``, every stage's evaluations are metered to it.
- `_statement(claim: K.Claim) -> str` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 509)
- `_engine(factory: EngineFactory, budget: _Budget) -> SketchEngine` ([source](../../../../../../src/learnloop/figures/sketch_verify.py), line 795)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `VERIFIER_REPORT_VERSION`, `module`; statically calls `prediction_outcome`, `prediction_target_step`, `verify_sketch`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `evaluate`
- [[Reference/Modules/learnloop/figures/sketch|learnloop.figures.sketch]] — imports `module`; calls `claim_entry_work`, `element_index`, `prediction_step`, `probe_numbers`, `probe_problems`, `read_steps`, `sample_steps`, `scene_problems`
- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `ENGINE_SHA256`, `SketchEngine`, `SketchRunError`; calls `SketchRunError`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; calls `parameter_grid`, `quote_in`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `statistics`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/sketch_parity_corpus.py](../../../../../../tests/sketch_parity_corpus.py) — direct import
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`
- [tests/test_sketch_hostile.py](../../../../../../tests/test_sketch_hostile.py) — direct import
  - `test_a_tautological_claim_speaks_only_for_what_it_checks`
  - `test_text_that_imitates_a_badge_never_reaches_the_check_lines`
- [tests/test_sketch_sandbox_review.py](../../../../../../tests/test_sketch_sandbox_review.py) — direct import
  - `test_a_claim_false_at_a_graded_step_fails_verification`
  - `test_a_graded_step_is_checked_counted_and_compared`
  - `test_a_program_that_changes_its_state_when_read_is_checked_under_the_playback_schedule`
  - `test_a_program_whose_reads_change_every_later_value_fails_as_not_deterministic`
  - `test_an_on_step_prediction_change_is_graded_at_exactly_that_value`
  - `test_every_prediction_records_its_graded_read_in_tested`
  - `test_the_hostile_corpus_verify_cases_get_their_outcome_in_the_sidecar`
  - `test_the_report_carries_the_schedule_and_the_digest_of_every_checked_read`
  - `test_the_reviewers_counting_program_fails_verification`
  - `test_the_signed_zero_program_is_graded_as_the_desktop_draws_it`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_failed_reverification_is_recorded_as_failed`
  - `test_a_prediction_an_upgrade_dropped_is_refused`
  - `test_a_report_from_an_older_verifier_is_reverified_before_it_is_shown`
  - `test_a_report_from_this_verifier_and_engine_is_not_reverified`
  - `test_a_verifier_version_bump_reverifies_a_current_engines_report`
  - `test_an_engine_upgrade_reverifies_with_no_model_call`
- [tests/test_sketch_verify.py](../../../../../../tests/test_sketch_verify.py) — direct import
  - `test_a_follows_claim_is_charged_every_evaluation_it_runs`
  - `test_a_follows_claim_past_the_cap_is_stopped_where_the_cap_is`
  - `test_a_pairs_claim_is_charged_for_its_probes_own_x`
  - `test_a_pairs_claim_loop_stops_at_the_deadline`
  - `test_a_small_pairs_claim_is_charged_at_least_its_evaluations`
  - `test_charged_work_is_at_least_the_evaluations_run_for_random_claims`
  - `test_claim_loops_look_at_the_clock_by_work_not_only_by_entry_count`
  - `test_prediction_target_steps_are_where_the_answers_are_graded`
  - `test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget`
  - `test_sketch_predictions_are_decided_by_code_in_the_engine`
  - `test_the_largest_legal_grid_is_verified_one_point_read_at_a_time`
  - `test_the_meter_stops_one_evaluation_at_the_cap_and_at_the_clock`
  - `test_undecidable_predictions_are_dropped_not_failed`

## Modification guidance

- Make changes here when the responsibility remains sketch verify within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/sketch_verify.py](../../../../../../src/learnloop/figures/sketch_verify.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
