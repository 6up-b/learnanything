---
title: "learnloop.diagnosis.longform_trace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/longform_trace.py"
source_paths:
  - "src/learnloop/diagnosis/longform_trace.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.longform_trace module"
  - "src/learnloop/diagnosis/longform_trace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.longform_trace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.longform_trace` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Structured traces for long-form probes (spec_probe_eig_redesign.md §8.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py) |
| Source lines | 276 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TraceObligation` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 31) — One declared proof/derivation obligation, ordered as authored.
  - `as_dict(self) -> dict[str, Any]` (line 44; public)
- `class ObligationAssessment` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 54)
  - `as_dict(self) -> dict[str, Any]` (line 59; public)
- `class AssessedTrace` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 64) — The §8.2 structured trace over one long-form response.
  - `assessable_mass(self) -> float` (line 74; public) — Evidence mass actually carried by assessed elements — bounded by the task's total mass by construction (§7.7/§16 test 23).
  - `has_assessable_evidence(self) -> bool` (line 85; public)
  - `as_dict(self) -> dict[str, Any]` (line 90; public)
- `obligations_from_bindings(bindings: Mapping[str, Any] | None) -> list[TraceObligation]` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 101) — Parse the card's declared obligations (``bindings["obligations"]``).
- `outcomes_from_grading_evidence(obligations: Iterable[TraceObligation], evidence_rows: Iterable[Any], criteria_max_points: Mapping[str, float]) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 122) — Per-obligation raw outcomes from persisted criterion-level grading.
- `assess_trace(obligations: list[TraceObligation], outcomes: Mapping[str, str], *, total_task_evidence_mass: float=1.0) -> AssessedTrace` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 157) — Assess one long-form response against its declared obligations (§8.2).
- `classify_trace_outcome(trace: AssessedTrace, obligations: list[TraceObligation], alphabet: tuple[str, ...]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 239) — Map an assessed trace onto a long-form family's outcome alphabet.

### Module constants

- `_CORRECT_POINTS_RATIO` ([src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 22)
- `OUTCOME_CORRECT` ([src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 24)
- `OUTCOME_INVALID` ([src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 25)
- `OUTCOME_UNASSESSABLE` ([src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 26)
- `OUTCOME_UNASSESSED` ([src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py), line 27)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`; statically calls `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_longform_trace.py](../../../../../../tests/test_longform_trace.py) — direct import
  - `test_classifier_maps_selection_failure_to_wrong_strategy`
  - `test_eight_dependent_obligations_cannot_exceed_task_mass`
  - `test_first_error_preserves_prefix_and_marks_dependents_unassessable`
  - `test_independent_obligation_after_first_error_stays_assessable`
  - `test_mass_stays_bounded_with_partial_failure`
  - `test_obligations_from_bindings_roundtrip`
  - `test_outcomes_from_grading_evidence_thresholds_and_supersession`
  - `test_ungraded_obligation_carries_no_evidence`

## Modification guidance

- Change longform trace policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/longform_trace.py](../../../../../../src/learnloop/diagnosis/longform_trace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
