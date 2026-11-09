---
title: "learnloop.workbench.symbolic"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/symbolic.py"
source_paths:
  - "src/learnloop/workbench/symbolic.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.symbolic module"
  - "src/learnloop/workbench/symbolic.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.symbolic`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.symbolic` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2b: symbolic checks of the learner's own written steps (spec_reader_workbench_v1 §5.3, G9, G38).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py) |
| Source lines | 1072 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SymbolicClaim` ([source](../../../../../../src/learnloop/workbench/symbolic.py), line 96) — One declared transformation of one written text.
  - `oversized(self) -> str | None` (line 122; public) — Which bound the claim exceeds (it is then never checked), or None.
  - `payload(self) -> dict[str, Any]` (line 141; public) — The claim as data, whole (:meth:`oversized` keeps a claim that would need clipping out of the sandbox altogether).
- `class SymbolicOutcome` ([source](../../../../../../src/learnloop/workbench/symbolic.py), line 152) — What the sandbox found for one claim.
  - `as_dict(self) -> dict[str, Any]` (line 167; public)
- `sandbox_ready() -> bool` ([source](../../../../../../src/learnloop/workbench/symbolic.py), line 1007)
- `run_checks(claims: Sequence[SymbolicClaim], *, limits: Any=None, run: Callable[..., Any] | None=None) -> tuple[list[SymbolicOutcome], str | None]` ([source](../../../../../../src/learnloop/workbench/symbolic.py), line 1013) — Run the declared claims in the sandbox; ``(outcomes, problem)``.

### Module constants

- `KINDS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 75)
- `CHECKABLE_KINDS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 80)
- `MAX_CHECKS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 88)
- `MAX_EXPRESSION_CHARS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 89)
- `MAX_TEXT_CHARS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 90)
- `MAX_EARLIER` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 91)
- `MAX_PROBLEM_CHARS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 92)
- `HARNESS` ([src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py), line 173)

### Explicit exports

`__all__` declares:

- `CHECKABLE_KINDS`
- `CHECKED`
- `CHECKED_NUMERICALLY`
- `HARNESS`
- `KINDS`
- `MODEL`
- `SymbolicClaim`
- `SymbolicOutcome`
- `run_checks`
- `sandbox_ready`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; statically calls `SymbolicClaim`, `run_checks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `SandboxLimits`, `SandboxUnavailable`, `run_sandboxed_python`, `sandbox_available`; calls `SandboxLimits`, `run_sandboxed_python`, `sandbox_available`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw2b_fix4.py](../../../../../../tests/test_reader_rw2b_fix4.py) — direct import
  - `test_item1_a_long_step_is_checked_whole_or_not_at_all`
  - `test_item1_an_overlong_definition_or_problem_is_never_read_in_part`
  - `test_item2_solving_against_a_written_restriction_is_never_checked`
  - `test_item6_odd_roots_and_fractional_powers_of_a_possibly_negative_base_are_never_checked`
- [tests/test_reader_rw2b_fix5.py](../../../../../../tests/test_reader_rw2b_fix5.py) — direct import
  - `test_items_1_2_a_restricted_name_is_not_used_by_any_kind_and_taints_names_that_write_it`
  - `test_items_1_2_a_solve_or_substitution_whose_own_text_restricts_a_domain_is_never_checked`
  - `test_items_1_2_a_solve_through_a_restricted_name_is_never_checked`
  - `test_items_1_2_a_substitution_into_a_restricted_name_is_never_checked`
  - `test_items_1_2_names_are_never_resolved_and_a_name_free_step_still_checks`
  - `test_items_1_2_two_definitions_differing_only_in_their_restriction_never_resolve`
- [tests/test_reader_rw2b_fix6.py](../../../../../../tests/test_reader_rw2b_fix6.py) — direct import
  - `test_a_fractional_power_redefinition_leaves_no_definition_in_force`
  - `test_a_greek_function_name_is_a_name_too`
  - `test_a_greek_parameter_never_lets_a_restricted_definition_through`
  - `test_a_name_free_correct_step_of_each_remaining_kind_still_checks`
  - `test_a_nested_redefinition_leaves_no_definition_in_force`
  - `test_a_solve_with_any_restriction_token_is_never_checked_greek_included`
- [tests/test_reader_rw2b_fix7.py](../../../../../../tests/test_reader_rw2b_fix7.py) — direct import
  - `test_a_primed_or_applied_identifier_anywhere_is_a_name`
  - `test_a_solve_checks_only_against_the_immediately_preceding_step`
  - `test_a_solve_never_skips_a_restricted_preceding_equation`
  - `test_a_subscripted_or_formatted_definition_still_makes_its_name_a_name`
  - `test_a_text_that_formats_or_subscripts_is_never_checked`
  - `test_name_free_steps_of_each_kind_still_check`
- [tests/test_reader_rw2b_fix8.py](../../../../../../tests/test_reader_rw2b_fix8.py) — direct import
  - `test_a_first_step_that_solves_is_never_checked_against_the_problem`
  - `test_a_spaced_grouped_or_left_dotted_definition_disables_the_problem`
  - `test_a_step_with_a_spacing_command_or_non_ascii_text_is_never_checked`
  - `test_a_unicode_or_prose_function_disables_the_problem`
  - `test_name_free_steps_on_a_function_free_problem_still_check`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f2_exact_identities_and_decimals_keep_their_labels`
  - `test_f2_false_or_domain_dependent_identities_are_never_checked_as_holding`
- [tests/test_workbench_check.py](../../../../../../tests/test_workbench_check.py) — direct import
  - `test_an_undeclared_kind_is_never_attempted`
- [tests/test_workbench_check_kinds.py](../../../../../../tests/test_workbench_check_kinds.py) — direct import
  - `test_a_definite_integral_with_other_declared_bounds_is_never_checked`
  - `test_a_root_of_an_equation_with_two_roots_is_checked_with_a_control_that_is_not_a_root`
  - `test_a_wrong_step_that_still_has_unknowns_is_never_said_not_to_follow`
  - `test_an_antiderivative_is_checked_up_to_a_constant_with_a_negative_control_that_bites`
  - `test_an_unparseable_wordy_chained_or_bare_step_stays_the_models_reading`
  - `test_each_supported_kind_checks_a_correct_written_step_and_catches_a_wrong_one`
  - `test_inequalities_and_boundaries_are_never_checked`
  - `test_substitution_and_a_primed_derivative_are_never_checked`
  - `test_without_bubblewrap_nothing_runs_and_every_claim_is_the_models_reading`

## Modification guidance

- Make changes here when the responsibility remains symbolic within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/symbolic.py](../../../../../../src/learnloop/workbench/symbolic.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
