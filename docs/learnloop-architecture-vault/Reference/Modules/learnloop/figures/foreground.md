---
title: "learnloop.figures.foreground"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/foreground.py"
source_paths:
  - "src/learnloop/figures/foreground.py"
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
  - "learnloop.figures.foreground module"
  - "src/learnloop/figures/foreground.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.foreground`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.foreground` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P5: what the learner is waiting for now (spec_reader_show_me_figures_v1 §10b.4, "Yield to the learner").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py) |
| Source lines | 87 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `foreground(kind: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/figures/foreground.py), line 32) — Mark one piece of foreground work (``kind``: a figure, a lesson turn, a tutor answer, grading).
- `busy() -> bool` ([source](../../../../../../src/learnloop/figures/foreground.py), line 48)
- `in_flight() -> dict[str, int]` ([source](../../../../../../src/learnloop/figures/foreground.py), line 53)
- `wait_idle(timeout: float, *, cancelled: Callable[[], bool] | None=None, poll: float=0.5) -> bool` ([source](../../../../../../src/learnloop/figures/foreground.py), line 58) — Wait up to ``timeout`` seconds for no foreground work; True when idle.

### Module constants

- `FOREGROUND_WAIT_SECONDS` ([src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py), line 24)
- `_LOCK` ([src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py), line 26)
- `_IN_FLIGHT` ([src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py), line 27)
- `_IDLE` ([src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py), line 28)
- `FOREGROUND_METHODS` ([src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py), line 76)

### Explicit exports

`__all__` declares:

- `FOREGROUND_METHODS`
- `FOREGROUND_WAIT_SECONDS`
- `busy`
- `foreground`
- `in_flight`
- `wait_idle`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `module`; statically calls `busy`, `wait_idle`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `wait_idle`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `foreground`, `module`; statically calls `foreground`, `wait_idle`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `foreground`; statically calls `foreground`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `FOREGROUND_METHODS`, `foreground`; statically calls `foreground`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `threading`, `time`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_queue_stopped_by_foreground_work_records_what_waits`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_prebuilds_yield_to_foreground_work_and_resume_on_the_next_pass`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f11_reader_figures_says_a_prebuild_is_coming_until_it_lands`
  - `test_f16_a_prebuilds_rich_request_rechecks_the_switch_after_waiting_for_foreground_work`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
  - `test_f1_rereview_a_builds_protection_is_read_on_the_vault_loaded_now`
  - `test_f4_a_build_rechecks_the_protection_before_it_starts`
  - `test_f6_a_resumed_build_spends_todays_cap`
  - `test_f7_a_prebuilds_rich_job_yields_to_foreground_work`
  - `test_f7_a_quick_prebuild_stops_before_its_request_while_the_learner_works`
  - `test_f7_the_judge_waits_for_foreground_work`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_every_background_guard_a_power_deferred_resume_rechecks_holds_a_capped_one`

## Modification guidance

- Make changes here when the responsibility remains foreground within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/foreground.py](../../../../../../src/learnloop/figures/foreground.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
