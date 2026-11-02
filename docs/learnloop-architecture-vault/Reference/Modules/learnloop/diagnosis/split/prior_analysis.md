---
title: "learnloop.diagnosis.split.prior_analysis"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/prior_analysis.py"
source_paths:
  - "src/learnloop/diagnosis/split/prior_analysis.py"
source_commit: "adb862f63ee5e6e0705b38646577af78698897f2"
source_commit_timestamp: "2026-11-01T15:47:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.prior_analysis module"
  - "src/learnloop/diagnosis/split/prior_analysis.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.prior_analysis`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.prior_analysis` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The diagnoser's prior-analysis arm (learner-blindness relax; owner direction 2026-11-01).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py) |
| Source lines | 189 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `adb862f63ee5e6e0705b38646577af78698897f2` |
| Commit timestamp | `2026-11-01T15:47:44-05:00` |

## Public API

- `class Arm` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 60) — One diagnosis's arm and how it was assigned (recorded on its receipt).
  - `on(self) -> bool` (line 69; public)
  - `receipt(self) -> dict[str, Any]` (line 72; public)
- `configured(vault: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 80)
- `assign(setting: str, attempt_id: str) -> Arm` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 86) — The arm of one diagnosed attempt under ``setting``.
- `class PriorAnalysis` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 103) — What :func:`learnloop.diagnosis.split.context.assemble_diagnosis_context` is handed.
- `repository_reader(vault: Any, repository: Any) -> PriorReader` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 115) — The reader over the vault's ledger: per prior attempt, its latest completed live diagnosis written strictly before the cutoff (its ``analysis_md``, bounded, and the diagnosis id the provenance records) and, for a workbench attempt, its step trace with the symbolic switch read no…
- `for_attempt(vault: Any, repository: Any, attempt_id: str) -> PriorAnalysis` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 167) — The live diagnosis's prior-analysis input: its arm and the ledger reader.

### Module constants

- `ARM_ON` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 37)
- `ARM_OFF` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 38)
- `DESIGN` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 40)
- `EQUIPOISE` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 43)
- `SUFFIX` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 45)
- `ANALYSIS_CHARS` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 47)
- `TRACE_UNRECORDED` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 50)
- `NOTE` ([src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 51)

### Explicit exports

`__all__` declares:

- `ANALYSIS_CHARS`
- `ARM_OFF`
- `ARM_ON`
- `Arm`
- `DESIGN`
- `EQUIPOISE`
- `NOTE`
- `PriorAnalysis`
- `PriorReader`
- `SUFFIX`
- `TRACE_UNRECORDED`
- `assign`
- `configured`
- `for_attempt`
- `repository_reader`

## Internal implementation anchors

- `_excerpt(text: str, limit: int=ANALYSIS_CHARS) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py), line 110)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `NOTE`, `TRACE_UNRECORDED`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `ARM_ON`, `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `module`; statically calls `for_attempt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `WORKBENCH_SURFACES`, `trace_for_attempt`; calls `trace_for_attempt`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `switch_now`; calls `switch_now`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_arm_is_a_seeded_equipoise_draw_or_the_configured_arm`
  - `test_the_live_diagnosis_records_its_arm_and_the_grader_never_sees_it`
  - `test_the_off_arm_is_todays_context_and_the_on_arm_refeeds_earlier_analyses`
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
  - `test_an_earlier_workbench_trace_counts_its_item_and_leaves_the_record_incomplete`

## Modification guidance

- Change prior analysis policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/prior_analysis.py](../../../../../../../src/learnloop/diagnosis/split/prior_analysis.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
