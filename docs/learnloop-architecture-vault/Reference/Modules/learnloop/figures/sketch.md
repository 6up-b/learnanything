---
title: "learnloop.figures.sketch"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/sketch.py"
source_paths:
  - "src/learnloop/figures/sketch.py"
source_commit: "214c206ff1962566773d30b8b44f586d62ca383b"
source_commit_timestamp: "2026-11-08T22:42:42-05:00"
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
  - "learnloop.figures.sketch module"
  - "src/learnloop/figures/sketch.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.sketch`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.sketch` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: ``SketchProgramV1`` and its ``Scene``: the sketch tier's data (spec_reader_show_me_figures_v1 §9.1; RW5d P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py) |
| Source lines | 910 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `214c206ff1962566773d30b8b44f586d62ca383b` |
| Commit timestamp | `2026-11-08T22:42:42-05:00` |

## Public API

- `impersonates(name: str) -> bool` ([source](../../../../../../src/learnloop/figures/sketch.py), line 110)
- `class SketchError(ValueError)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 116) — A program outside the schema, the caps or the grammar; ``problems`` lists why.
  - `__init__(self, problems: Sequence[str]) -> None` (line 119; internal)
- `class SketchClaimQuote(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 134)
- `class Clock(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 139)
- `class Probe(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 144)
- `class Claim(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 150) — What code checks (spec §9.5), each over one probe.
- `class Binding(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 182)
- `class SketchObserve(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 187)
- `class SketchPrediction(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 194)
- `class SketchProgramV1(_Strict)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 201)
  - `dump(self) -> dict[str, Any]` (line 216; public)
  - `canonical_json(self) -> str` (line 219; public)
- `class CompiledClaim` ([source](../../../../../../src/learnloop/figures/sketch.py), line 224)
- `class CompiledSketch` ([source](../../../../../../src/learnloop/figures/sketch.py), line 232)
  - `parameters(self) -> list[S.Parameter]` (line 238; public)
  - `defaults(self) -> dict[str, float]` (line 242; public)
  - `steps(self) -> int` (line 246; public) — How many clock steps reach ``t_max`` (0 without a clock).
- `clock_steps(clock: Clock) -> int` ([source](../../../../../../src/learnloop/figures/sketch.py), line 253)
- `round_half_up(value: float) -> int` ([source](../../../../../../src/learnloop/figures/sketch.py), line 257) — JavaScript's ``Math.round`` (a tie goes up), exactly: the desktop and the sidecar compute the same steps from the same program (Python's ``round`` sends a tie to the even neighbour).
- `tick_steps(total: int) -> list[int]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 266) — The steps *play* reads from 0 to ``total``: every ``ceil(total / SKETCH_PLAY_TICKS)`` steps, and ``total`` itself.
- `sample_steps(compiled: CompiledSketch) -> list[int]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 276) — The step indices verification checks (``SKETCH_TIME_SAMPLES`` from 0 to t_max; only 0 without a clock).
- `prediction_step(compiled: CompiledSketch, index: int) -> int` ([source](../../../../../../src/learnloop/figures/sketch.py), line 287) — The clock step a prediction is graded at (Codex review F5): ``run_to`` the step nearest that time (at least 1, at most ``t_max``'s; a tie goes up, as the desktop's ``Math.round``); a parameter change ``t_max``'s step with a clock, 0 without.
- `read_steps(compiled: CompiledSketch) -> list[int]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 301) — **The read schedule** (Astra sandbox review, finding 1): the only steps at which any run of this sketch, in either host, calls ``view()`` and then ``probes()``, each exactly once per run.
- `control_value(parameter: S.Parameter, raw: float) -> float` ([source](../../../../../../src/learnloop/figures/sketch.py), line 324) — The value the desktop's slider and field set for ``raw`` (its ``clampStep``): within [min, max], on min plus a whole number of steps, to 12 significant digits.
- `expression_steps(node: G.Node, ranges: Mapping[str, tuple[float, float]]) -> int` ([source](../../../../../../src/learnloop/figures/sketch.py), line 349) — The most nodes one evaluation of ``node`` visits: a sum's body once per term (its bounds' widest reach, or :data:`.grammar.MAX_SUM_TERMS` when code can't tell), an integral's body once per integrand evaluation the grammar allows.
- `claim_entry_work(program: SketchProgramV1, claim: Claim, nodes: Mapping[str, G.Node], shape: str='series', var_reach: tuple[float, float] | None=None) -> int` ([source](../../../../../../src/learnloop/figures/sketch.py), line 384) — The most expression steps checking one entry of a claim's probe takes: one evaluation for ``equals`` and ``distribution``, twelve RK4 stages of ``dx`` and ``dy`` per path step for ``follows`` (the run and the half-step run), one step for an invariant.
- `canonical_numbers(value: Any) -> Any` ([source](../../../../../../src/learnloop/figures/sketch.py), line 438) — ``value`` with every ``-0.0`` made ``0.0`` (the sandbox review verify, Astra round 2).
- `parse_sketch(raw: str | Mapping[str, Any]) -> CompiledSketch` ([source](../../../../../../src/learnloop/figures/sketch.py), line 457) — Validate a program (step 1's static half).
- `parse_author_sketch(raw: Any) -> tuple[CompiledSketch, list[str]]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 638) — :func:`parse_sketch` for an author's answer (:func:`.spec.parse_salvaging_predictions`).
- `scene_problems(scene: Any, *, parameters: Sequence[str]=()) -> list[str]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 680) — Why a ``view()`` result can't be drawn (none: drawable).
- `probe_problems(values: Any, probes: Mapping[str, Probe]) -> list[str]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 823) — Why a ``probes()`` result does not match the declared probes (every declared one present, of its shape, every number finite; undeclared names are ignored, never shown).
- `probe_numbers(value: Any, shape: str) -> list[float]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 852) — A validated probe's values as one list (a pairs probe's y values).
- `element_index(scene: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 862)

### Module constants

- `SKETCH_VERSION` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 44)
- `SKETCH_MAX_SOURCE_BYTES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 46)
- `SKETCH_MAX_ELEMENTS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 48)
- `SKETCH_MAX_POINTS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 50)
- `SKETCH_MAX_CELLS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 52)
- `SKETCH_MAX_SERIES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 54)
- `SKETCH_TIME_SAMPLES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 56)
- `SKETCH_MAX_CLOCK_STEPS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 58)
- `SKETCH_PLAY_TICKS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 62)
- `SKETCH_FRAME_MS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 64)
- `SKETCH_WATCHDOG_FRAMES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 65)
- `CLAIM_REL_TOL` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 67)
- `ODE_SAFETY` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 69)
- `MC_FALSE_ALARM` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 71)
- `SKETCH_MAX_CLAIM_WORK` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 78)
- `SKETCH_MAX_VERIFY_OUTPUT_BYTES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 83)
- `SKETCH_VERIFY_SECONDS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 87)
- `MAX_VIEWPORT_SPAN` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 89)
- `MAX_PROBES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 90)
- `MAX_CLAIMS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 91)
- `MAX_BINDINGS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 92)
- `MAX_CHOICES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 93)
- `MAX_ID` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 94)
- `SHAPES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 95)
- `COLORS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 96)
- `ELEMENT_KINDS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 97)
- `INVARIANT_PROPERTIES` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 99)
- `TIME_NAME` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 101)
- `_ID` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 102)
- `CHECK_WORDS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 107)
- `_IDENT` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 113)
- `_STYLE_KEYS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 622)
- `_COMMON` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 623)
- `_ELEMENT_KEYS` ([src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py), line 624)

### Explicit exports

`__all__` declares:

- `CHECK_WORDS`
- `CLAIM_REL_TOL`
- `COLORS`
- `Claim`
- `CompiledClaim`
- `CompiledSketch`
- `ELEMENT_KINDS`
- `MC_FALSE_ALARM`
- `ODE_SAFETY`
- `Probe`
- `SKETCH_FRAME_MS`
- `SKETCH_MAX_CELLS`
- `SKETCH_MAX_CLAIM_WORK`
- `SKETCH_MAX_CLOCK_STEPS`
- `SKETCH_MAX_ELEMENTS`
- `SKETCH_MAX_POINTS`
- `SKETCH_MAX_SERIES`
- `SKETCH_MAX_SOURCE_BYTES`
- `SKETCH_MAX_VERIFY_OUTPUT_BYTES`
- `SKETCH_PLAY_TICKS`
- `SKETCH_TIME_SAMPLES`
- `SKETCH_VERIFY_SECONDS`
- `SKETCH_VERSION`
- `SKETCH_WATCHDOG_FRAMES`
- `SketchError`
- `SketchProgramV1`
- `claim_entry_work`
- `canonical_numbers`
- `clock_steps`
- `control_value`
- `element_index`
- `expression_steps`
- `impersonates`
- `parse_author_sketch`
- `parse_sketch`
- `prediction_step`
- `probe_numbers`
- `probe_problems`
- `read_steps`
- `round_half_up`
- `sample_steps`
- `tick_steps`
- `scene_problems`

## Internal implementation anchors

- `class _Strict(BaseModel)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 124)
- `_bound_reach(node: G.Node, ranges: Mapping[str, tuple[float, float]]) -> tuple[float, float] | None` ([source](../../../../../../src/learnloop/figures/sketch.py), line 339)
- `_ranges(program: SketchProgramV1) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/figures/sketch.py), line 377)
- `_parse_expr(where: str, source: str, allowed: set[str], problems: list[str]) -> G.Node | None` ([source](../../../../../../src/learnloop/figures/sketch.py), line 424)
- `_finite(value: Any) -> bool` ([source](../../../../../../src/learnloop/figures/sketch.py), line 644)
- `_describe(value: Any) -> str` ([source](../../../../../../src/learnloop/figures/sketch.py), line 648) — How a non-number is named in a problem (``sketchScene.ts``'s ``describe`` words it the same).
- `class _Problems(list)` ([source](../../../../../../src/learnloop/figures/sketch.py), line 660)
- `_numbers(problems: _Problems, where: str, value: Any, *, limit: int) -> list[float] | None` ([source](../../../../../../src/learnloop/figures/sketch.py), line 666)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `CLAIM_REL_TOL`, `SKETCH_MAX_CLAIM_WORK`, `expression_steps`, `impersonates`; statically calls `expression_steps`, `impersonates`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `module`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `parse_author_sketch`, `parse_sketch`
- [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]] — imports `module`; statically calls `claim_entry_work`, `element_index`, `prediction_step`, `probe_numbers`, `probe_problems`, `read_steps`, `sample_steps`, `scene_problems`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `check_names`, `free_names`, `is_name`, `parse`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `parse_salvaging_predictions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]], [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/figures/sketch_verify|learnloop.figures.sketch_verify]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/sketch_parity_corpus.py](../../../../../../tests/sketch_parity_corpus.py) — direct import
- [tests/sketch_scene_corpus.py](../../../../../../tests/sketch_scene_corpus.py) — direct import
- [tests/test_figure_author_predictions.py](../../../../../../tests/test_figure_author_predictions.py) — direct import
  - `test_a_sketch_gets_the_same_treatment`
  - `test_run_to_is_untouched`
- [tests/test_reader_rw5d_p4a_figures_follow.py](../../../../../../tests/test_reader_rw5d_p4a_figures_follow.py) — direct import
  - `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`
- [tests/test_sketch_hostile.py](../../../../../../tests/test_sketch_hostile.py) — direct import
  - `test_a_tautological_claim_speaks_only_for_what_it_checks`
  - `test_an_oversized_result_is_refused_by_the_engine_or_the_validator`
  - `test_prototype_pollution_stays_inside_the_engine`
  - `test_text_that_imitates_a_badge_never_reaches_the_check_lines`
- [tests/test_sketch_sandbox_review.py](../../../../../../tests/test_sketch_sandbox_review.py) — direct import
  - `test_a_claim_false_at_a_graded_step_fails_verification`
  - `test_a_graded_step_is_checked_counted_and_compared`
  - `test_a_program_that_changes_its_state_when_read_is_checked_under_the_playback_schedule`
  - `test_a_program_whose_reads_change_every_later_value_fails_as_not_deterministic`
  - `test_an_off_step_prediction_change_is_refused`
  - `test_an_on_step_prediction_change_is_graded_at_exactly_that_value`
  - `test_every_prediction_records_its_graded_read_in_tested`
  - `test_the_hostile_corpus_verify_cases_get_their_outcome_in_the_sidecar`
  - `test_the_read_schedule_has_plays_ticks_the_samples_and_every_graded_step`
  - `test_the_report_carries_the_schedule_and_the_digest_of_every_checked_read`
  - `test_the_reviewers_counting_program_fails_verification`
  - `test_the_signed_zero_program_is_graded_as_the_desktop_draws_it`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines`
  - `test_a_sketch_built_with_nothing_from_the_books_quotes_nothing`
- [tests/test_sketch_verify.py](../../../../../../tests/test_sketch_verify.py) — direct import
  - `test_a_follows_claim_is_charged_every_evaluation_it_runs`
  - `test_a_follows_claim_past_the_cap_is_stopped_where_the_cap_is`
  - `test_a_good_scene_has_no_problems`
  - `test_a_pairs_claim_is_charged_for_its_probes_own_x`
  - `test_a_pairs_claim_loop_stops_at_the_deadline`
  - `test_a_parameter_named_like_a_check_is_refused`
  - `test_a_program_outside_the_schema_is_refused`
  - `test_a_scene_over_the_caps_is_refused`
  - `test_a_small_pairs_claim_is_charged_at_least_its_evaluations`
  - `test_charged_work_is_at_least_the_evaluations_run_for_random_claims`
  - `test_claim_loops_look_at_the_clock_by_work_not_only_by_entry_count`
  - `test_claim_steps_are_counted_soundly`
  - `test_prediction_target_steps_are_where_the_answers_are_graded`
  - `test_probe_problems_check_every_declared_shape`
  - `test_scene_problems_name_what_cant_be_drawn`
  - `test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget`
  - `test_sketch_predictions_are_decided_by_code_in_the_engine`
  - `test_the_largest_legal_grid_is_verified_one_point_read_at_a_time`
  - `test_undecidable_predictions_are_dropped_not_failed`
  - `test_verification_stops_at_its_wall_clock`

## Modification guidance

- Make changes here when the responsibility remains sketch within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/sketch.py](../../../../../../src/learnloop/figures/sketch.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
