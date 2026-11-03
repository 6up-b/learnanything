---
title: "learnloop.content.authoring.pf_sandbox"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/pf_sandbox.py"
source_paths:
  - "src/learnloop/content/authoring/pf_sandbox.py"
source_commit: "ee60904dcae6ec66a487d8f6e6b1d10ca3e2db9e"
source_commit_timestamp: "2026-10-20T22:01:38-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.pf_sandbox module"
  - "src/learnloop/content/authoring/pf_sandbox.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.pf_sandbox`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.pf_sandbox` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: The PF-b sandbox for LLM-written Python (Slice 2 §5.3, P7).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py) |
| Source lines | 420 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `ee60904dcae6ec66a487d8f6e6b1d10ca3e2db9e` |
| Commit timestamp | `2026-10-20T22:01:38-04:00` |

## Public API

- `class SandboxUnavailable(RuntimeError)` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 48) — Bubblewrap is missing: PF generation refuses rather than running unsandboxed.
- `class SandboxLimits` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 53)
  - `from_config(cls, pf_config: Any) -> SandboxLimits` (line 61; public)
- `class SandboxResult` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 70)
- `sandbox_available() -> bool` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 80)
- `require_sandbox() -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 84)
- `run_sandboxed_python(harness: str, payload: Mapping[str, Any], *, modules: Mapping[str, str] | None=None, limits: SandboxLimits | None=None, run: Callable[..., Any]=subprocess.run) -> SandboxResult` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 120) — Run ``harness`` (Python source) on JSON ``payload`` inside bubblewrap.
- `run_generator_tests(code: str, *, seeds: list[int], limits: SandboxLimits | None=None, run: Callable[..., Any]=subprocess.run) -> SandboxResult` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 343) — Draw ``seeds`` and self-check each draw, with negative controls.
- `check_generator_answers(code: str, pairs: list[dict[str, Any]], *, limits: SandboxLimits | None=None, run: Callable[..., Any]=subprocess.run) -> SandboxResult` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 354) — Verify each ``{"draw", "answer"}`` pair with the program's own ``check``.
- `run_equivalence_checks(programs: Mapping[str, str], pairs: list[dict[str, str]], *, normal_forms: Mapping[str, str] | None=None, limits: SandboxLimits | None=None, run: Callable[..., Any]=subprocess.run) -> SandboxResult` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 365) — Run LLM-written ``check(reference, answer)`` programs on their pairs.
- `equivalence_confirmations(result: SandboxResult, count: int, *, program: str='check') -> tuple[list[bool | None], bool]` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 390) — Per-pair confirmations of one LLM-written check, and whether it is degenerate.

### Module constants

- `GENERATOR_PROTOCOL` ([src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 43)
- `EQUIVALENCE_PROTOCOL` ([src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 44)
- `_OUTPUT_MARKER` ([src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 45)
- `_HARNESS` ([src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 183)
- `NEGATIVE_CONTROLS` ([src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 340)

### Explicit exports

`__all__` declares:

- `EQUIVALENCE_PROTOCOL`
- `equivalence_confirmations`
- `GENERATOR_PROTOCOL`
- `NEGATIVE_CONTROLS`
- `SandboxLimits`
- `SandboxResult`
- `SandboxUnavailable`
- `check_generator_answers`
- `require_sandbox`
- `run_equivalence_checks`
- `run_sandboxed_python`
- `sandbox_available`
- `run_generator_tests`

## Internal implementation anchors

- `_environment(workdir: Path) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 95)
- `_limit_resources(limits: SandboxLimits) -> Callable[[], None]` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 109)
- `_limit_dict(limits: SandboxLimits) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py), line 177)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `EQUIVALENCE_PROTOCOL`, `GENERATOR_PROTOCOL`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `SandboxLimits`
- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `module`; statically calls `SandboxLimits`, `run_sandboxed_python`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `SandboxLimits`, `sandbox_available`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`; statically calls `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `GENERATOR_PROTOCOL`, `SandboxLimits`, `SandboxUnavailable`, `check_generator_answers`, `equivalence_confirmations`, `require_sandbox`, `run_equivalence_checks`, `run_generator_tests`, `sandbox_available`; statically calls `check_generator_answers`, `require_sandbox`, `run_generator_tests`, `sandbox_available`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `SandboxLimits`, `SandboxUnavailable`, `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`; statically calls `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`
- [[Reference/Modules/learnloop/workbench/symbolic|learnloop.workbench.symbolic]] — imports `SandboxLimits`, `SandboxUnavailable`, `run_sandboxed_python`, `sandbox_available`; statically calls `SandboxLimits`, `run_sandboxed_python`, `sandbox_available`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `_sandbox_bwrap_path`, `_sandboxed_command`; calls `_sandbox_bwrap_path`, `_sandboxed_command`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `resource`, `shutil`, `subprocess`, `sys`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]], [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figure_fixtures.py](../../../../../../../tests/figure_fixtures.py) — direct import
- [tests/test_embedding_compare.py](../../../../../../../tests/test_embedding_compare.py) — direct import
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — direct import
- [tests/test_figures_fix_round2.py](../../../../../../../tests/test_figures_fix_round2.py) — direct import
  - `test_f4_pf_equivalence_confirms_nothing_when_a_control_is_answered_with_no_boolean`
  - `test_f4_pf_generator_tests_count_an_inconclusive_answer_as_not_passing`
- [tests/test_figures_fix_round3.py](../../../../../../../tests/test_figures_fix_round3.py) — direct import
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — direct import
- [tests/test_figures_fix_round5.py](../../../../../../../tests/test_figures_fix_round5.py) — direct import
- [tests/test_item_fingerprints.py](../../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_rebuild_recomputes_fingerprints_without_any_model_or_generator`
- [tests/test_key_ladder_labels.py](../../../../../../../tests/test_key_ladder_labels.py) — direct import
  - `test_a_numeric_key_without_a_sandbox_is_panel_agrees_unconfirmed`
  - `test_a_panel_that_agrees_on_another_answer_disputes_the_key`
  - `test_a_quote_not_in_the_passage_falls_to_the_panel`
- [tests/test_manim_sandbox_hostile.py](../../../../../../../tests/test_manim_sandbox_hostile.py) — direct import
  - `test_hostile_python_reaches_nothing_outside_the_sandbox`
- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_check_recorded_on_main_still_verifies_and_the_fresh_check_label_needs_a_change`
- [tests/test_pf_generation.py](../../../../../../../tests/test_pf_generation.py) — direct import
- [tests/test_pf_reports.py](../../../../../../../tests/test_pf_reports.py) — direct import
- [tests/test_pf_sandbox.py](../../../../../../../tests/test_pf_sandbox.py) — direct import
  - `test_command_is_wrapped_in_bubblewrap_with_limits`
  - `test_cpu_limit_stops_a_runaway_program`
  - `test_degenerate_equivalence_checks_are_detected_by_negative_controls`
  - `test_equivalence_harness_runs_model_written_checks`
  - `test_generation_fails_closed_without_bubblewrap`
  - `test_generator_harness_checks_invariance_and_negative_controls`
  - `test_network_vault_reads_and_outside_writes_are_denied`
  - `test_the_prompt_templates_accept_their_own_tuple_answers`
  - `test_wall_clock_limit_kills_a_sleeping_program`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
  - `test_a_failed_sympy_run_is_disagreement_for_pf_but_reported_apart`
  - `test_combined_agreement_and_ledger_rows_are_pf_s`
  - `test_pf_still_raises_without_a_sandbox_and_the_ladder_reports`
- [tests/test_reader_rw2b_fix10.py](../../../../../../../tests/test_reader_rw2b_fix10.py) — direct import
  - `test_item1_enable_check_disable_then_resume_recheck_hint_and_report_never_read_checked`
- [tests/test_reader_rw2b_fix11.py](../../../../../../../tests/test_reader_rw2b_fix11.py) — direct import
- [tests/test_reader_rw2b_fix12.py](../../../../../../../tests/test_reader_rw2b_fix12.py) — direct import
  - `test_item3_a_hint_in_flight_when_the_switch_goes_off_writes_and_stores_the_models_reading`
- [tests/test_reader_rw2b_fix13.py](../../../../../../../tests/test_reader_rw2b_fix13.py) — direct import
- [tests/test_reader_rw2b_fix14.py](../../../../../../../tests/test_reader_rw2b_fix14.py) — direct import
  - `test_items_2_3_a_row_stored_checked_reads_as_the_models_everywhere_once_the_switch_is_off`
- [tests/test_reader_rw2b_fix15.py](../../../../../../../tests/test_reader_rw2b_fix15.py) — direct import
- [tests/test_reader_rw2b_fix3.py](../../../../../../../tests/test_reader_rw2b_fix3.py) — direct import
- [tests/test_reader_rw2b_fix4.py](../../../../../../../tests/test_reader_rw2b_fix4.py) — direct import
- [tests/test_reader_rw2b_fix5.py](../../../../../../../tests/test_reader_rw2b_fix5.py) — direct import
- [tests/test_reader_rw2b_fix6.py](../../../../../../../tests/test_reader_rw2b_fix6.py) — direct import
- [tests/test_reader_rw2b_fix7.py](../../../../../../../tests/test_reader_rw2b_fix7.py) — direct import
- [tests/test_reader_rw2b_fix8.py](../../../../../../../tests/test_reader_rw2b_fix8.py) — direct import
- [tests/test_reader_rw2b_review.py](../../../../../../../tests/test_reader_rw2b_review.py) — direct import
- [tests/test_reference_gate_imports.py](../../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_regrade_after_the_tag_binds_an_attempt_recorded_before_it`
  - `test_below_the_tag_a_regrade_changes_nothing`
  - `test_below_the_tag_the_gate_never_runs`
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published`
  - `test_pf_judges_each_selected_variant_once_and_publication_reads_the_verdict`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f17_a_cancellation_during_the_judgment_is_not_swallowed`
  - `test_f17_a_failed_judgment_leaves_the_job_retryable_and_a_rerun_resumes_without_regenerating`
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f20_a_partial_judgment_resumes_without_any_paid_pipeline_work`
- [tests/test_required_method_round3.py](../../../../../../../tests/test_required_method_round3.py) — direct import
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
- [tests/test_rw5c_labels.py](../../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_figure_with_no_book_element_is_drawn_exactly_as_before`
- [tests/test_rw5c_recheck.py](../../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_certification_bump_rechecks_at_no_paid_cost`
  - `test_a_recheck_with_the_switch_off_or_turned_off_before_its_write_writes_nothing`
  - `test_dry_run_writes_nothing_and_the_cli_reports_by_reason_key`
  - `test_rebuild_of_a_figure_with_no_difference_is_refused`
- [tests/test_rw5c_source_check.py](../../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_a_held_out_block_later_withholds_the_figure_and_its_check`
  - `test_a_quote_across_two_blocks_points_at_no_candidate`
  - `test_a_sandbox_that_raises_unavailable_checks_nothing`
  - `test_the_switch_off_at_the_store_writes_nothing`
  - `test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build`
- [tests/test_source_exercise_import.py](../../../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_a_need_is_never_fulfilled_by_an_unverified_key`
  - `test_an_unverified_key_is_written_labelled_or_refused_by_the_switch`
- [tests/test_source_first_needs.py](../../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_an_unverifiable_key_never_fulfils_and_generation_proceeds`
- [tests/test_workbench_check.py](../../../../../../../tests/test_workbench_check.py) — direct import
  - `test_a_checked_step_says_checked_only_when_the_sandbox_ran_and_its_controls_behaved`
  - `test_a_harness_verdict_without_the_learners_parse_is_never_shown_as_checked`
  - `test_without_bubblewrap_every_verdict_reads_as_the_models_reading`
- [tests/test_workbench_check_kinds.py](../../../../../../../tests/test_workbench_check_kinds.py) — direct import
  - `test_without_bubblewrap_nothing_runs_and_every_claim_is_the_models_reading`

## Modification guidance

- Change pf sandbox policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/pf_sandbox.py](../../../../../../../src/learnloop/content/authoring/pf_sandbox.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
