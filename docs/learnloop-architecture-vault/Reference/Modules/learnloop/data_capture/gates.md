---
title: "learnloop.data_capture.gates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/data_capture/gates.py"
source_paths:
  - "src/learnloop/data_capture/gates.py"
source_commit: "1d242b25e2e9fd03cada602956254bdc2e51ed25"
source_commit_timestamp: "2026-11-03T16:06:38-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.data_capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.data_capture.gates module"
  - "src/learnloop/data_capture/gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-data-capture"
---

# `learnloop.data_capture.gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.data_capture.gates` exists within [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] to own the behavior summarized by its module contract: The two switches of data capture (``[data_capture]``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/data_capture/gates.py](../../../../../../src/learnloop/data_capture/gates.py) |
| Source lines | 32 |
| Owning package | [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1d242b25e2e9fd03cada602956254bdc2e51ed25` |
| Commit timestamp | `2026-11-03T16:06:38-05:00` |

## Public API

- `receipts_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/data_capture/gates.py), line 18)
- `serving_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/data_capture/gates.py), line 23)

### Module constants

- `OUTCOME_VERSION_V3` ([src/learnloop/data_capture/gates.py](../../../../../../src/learnloop/data_capture/gates.py), line 15)

### Explicit exports

`__all__` declares:

- `OUTCOME_VERSION_V3`
- `receipts_on`
- `serving_on`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `receipts_on`, `serving_on`; statically calls `receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `receipts_on`; statically calls `receipts_on`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `OUTCOME_VERSION_V3`, `receipts_on`, `serving_on`; statically calls `receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `receipts_on`, `serving_on`; statically calls `receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `OUTCOME_VERSION_V3`, `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `serving_on`; statically calls `serving_on`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `receipts_on`; statically calls `receipts_on`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DATA_CAPTURE_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a1_prefilter.py](../../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_the_voi_flag_follows_the_successors_switch`
- [tests/test_data_capture_successor.py](../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_switches_are_on_by_default_and_the_gate_reads_the_tag`

## Modification guidance

- Make changes here when the responsibility remains gates within learnloop.data_capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/data_capture/gates.py](../../../../../../src/learnloop/data_capture/gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
