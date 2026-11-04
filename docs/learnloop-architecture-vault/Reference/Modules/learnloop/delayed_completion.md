---
title: "learnloop.delayed_completion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/delayed_completion.py"
source_paths:
  - "src/learnloop/delayed_completion.py"
source_commit: "1e2d89e34a3f41bfb4a25f2c08a283cbd81161c9"
source_commit_timestamp: "2026-11-03T12:14:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.delayed_completion module"
  - "src/learnloop/delayed_completion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.delayed_completion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.delayed_completion` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: One versioned delayed-completion definition (data capture A4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1e2d89e34a3f41bfb4a25f2c08a283cbd81161c9` |
| Commit timestamp | `2026-11-03T12:14:40-05:00` |

## Public API

- `class Presentation` ([source](../../../../../src/learnloop/delayed_completion.py), line 62) — What one presentation was, from frozen facts only.
- `class Completion` ([source](../../../../../src/learnloop/delayed_completion.py), line 85)
  - `is_outcome(self) -> bool` (line 93; public)
- `delay_seconds(presentation: Presentation) -> int | None` ([source](../../../../../src/learnloop/delayed_completion.py), line 104) — Seconds since the last exposure or practice (and since ``not_before`` when named), or None.
- `classify(presentation: Presentation) -> Completion` ([source](../../../../../src/learnloop/delayed_completion.py), line 114) — THE definition (module docstring).
- `other_exclusions(row: Mapping[str, Any]) -> tuple[str, ...]` ([source](../../../../../src/learnloop/delayed_completion.py), line 133) — The outcome contract's reasons for ``row`` (its ``retention_exclusions`` keys) other than help and delay, which :func:`classify` decides itself.
- `help_question(row: Mapping[str, Any]) -> bool` ([source](../../../../../src/learnloop/delayed_completion.py), line 144) — Whether a question event reads as requested help during its attempt (AD's §5.3 rule).
- `last_before(times: Iterable[str], moment: str) -> str | None` ([source](../../../../../src/learnloop/delayed_completion.py), line 152) — The newest of ``times`` strictly before ``moment``.

### Module constants

- `DELAYED_COMPLETION_VERSION` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 38)
- `MIN_DELAY_SECONDS` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 40)
- `COMPLETED` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 42)
- `FAILED_WITH_HELP` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 43)
- `PRE_EXPOSED` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 44)
- `ABANDONED` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 45)
- `NOT_DELAYED` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 46)
- `EXCLUDED` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 47)
- `OUTCOME_STATUSES` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 49)
- `HELP_TYPES` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 52)
- `_HELP_REASONS` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 54)
- `_DELAY_REASONS` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 56)
- `HINTED_ATTEMPT_TYPE` ([src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py), line 58)

### Explicit exports

`__all__` declares:

- `ABANDONED`
- `COMPLETED`
- `Completion`
- `DELAYED_COMPLETION_VERSION`
- `EXCLUDED`
- `FAILED_WITH_HELP`
- `HELP_TYPES`
- `HINTED_ATTEMPT_TYPE`
- `MIN_DELAY_SECONDS`
- `NOT_DELAYED`
- `OUTCOME_STATUSES`
- `PRE_EXPOSED`
- `Presentation`
- `classify`
- `delay_seconds`
- `help_question`
- `last_before`
- `other_exclusions`

## Internal implementation anchors

- `_seconds(later: str, earlier: str) -> int | None` ([source](../../../../../src/learnloop/delayed_completion.py), line 97)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `HELP_TYPES`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `Presentation`, `classify`, `last_before`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`
- [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]] — imports `module`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `module`; statically calls `Presentation`, `classify`, `help_question`, `other_exclusions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `RETENTION_MIN_DELAY_SECONDS`, `retention_exclusions`; calls `retention_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]], [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a4_delayed_completion.py](../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
  - `test_requested_help_on_a_delayed_unexposed_presentation_is_r_cold_zero`
  - `test_the_definition_reuses_the_contracts_delay_and_no_new_number`
  - `test_the_delay_is_since_the_exposure_and_since_a_named_decision_never_only_the_offer`
  - `test_the_lesson_suggestion_adapter_reads_the_same_definition`
  - `test_the_one_definition`
- [tests/test_data_capture_codex_review.py](../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f2_a_check_already_due_is_not_shared_with_a_decision_it_cannot_measure`
  - `test_f2_a_new_check_with_a_short_interval_is_dated_past_the_window`
  - `test_f2_a_warm_answer_consumes_the_check_but_keeps_the_measurement_duty`
  - `test_f2_the_date_is_never_before_the_delay_whatever_truncation_does`
- [tests/test_data_capture_landing_review.py](../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_the_warm_answer_is_not_delayed_with_no_sweep_having_run`
  - `test_f1_with_no_section_read_the_same_answer_is_the_cold_success`
  - `test_finding2_coverage_named_after_the_sweep_is_an_exposure_too`

## Modification guidance

- Make changes here when the responsibility remains delayed completion within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/delayed_completion.py](../../../../../src/learnloop/delayed_completion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
