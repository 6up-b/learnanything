---
title: "learnloop.learner.measurement_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/measurement_state.py"
source_paths:
  - "src/learnloop/learner/measurement_state.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.measurement_state module"
  - "src/learnloop/learner/measurement_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.measurement_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.measurement_state` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Measurement-provenance labels — measured / inferred / claimed / unknown.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py) |
| Source lines | 121 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `require_measurement_state(value: str) -> MeasurementState` ([source](../../../../../../src/learnloop/learner/measurement_state.py), line 64) — Gate for the closed vocabulary: an unrecognised label is a bug, not data.
- `classify_measurement_state(*, evidence_mass: float | None, min_evidence_mass: float, mastery_evidence_count: int=0, claim_present: bool | Callable[[], bool]=False) -> MeasurementState` ([source](../../../../../../src/learnloop/learner/measurement_state.py), line 81) — Which of the four labels a displayed facet-level number is licensed to carry.

### Module constants

- `MEASURED` ([src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py), line 55)
- `INFERRED` ([src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py), line 56)
- `CLAIMED` ([src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py), line 57)
- `UNKNOWN` ([src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py), line 58)
- `MEASUREMENT_STATES` ([src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py), line 61)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `UNKNOWN`, `classify_measurement_state`; statically calls `classify_measurement_state`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `classify_measurement_state`, `require_measurement_state`; statically calls `classify_measurement_state`, `require_measurement_state`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `require_measurement_state`; statically calls `require_measurement_state`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_measurement_state_labels.py](../../../../../../tests/test_measurement_state_labels.py) — direct import
  - `test_capability_grid_labels_the_ready_number`
  - `test_claim_lookup_is_only_consulted_on_the_arm_that_can_reach_claimed`
  - `test_claimed_is_licensed_only_by_absence_and_never_outranks_evidence`
  - `test_claimed_label_when_only_a_learner_claim_covers_the_cell`
  - `test_emission_boundary_rejects_a_label_outside_the_vocabulary`
  - `test_every_classified_label_is_in_the_vocabulary`
  - `test_ignorance_is_unknown_and_never_inferred`
  - `test_inferred_requires_something_real_to_pool_from`
  - `test_label_does_not_move_a_threshold_a_number_or_a_certification`
  - `test_labelling_writes_nothing`
  - `test_measured_label_on_a_facet_with_evidence_over_the_gate`
  - `test_measured_requires_direct_evidence_over_the_mass_gate`
  - `test_negative_mass_cannot_manufacture_a_label`
  - `test_pooled_prediction_that_rendered_unlabelled_now_carries_inferred`
  - `test_sub_threshold_direct_mass_is_inferred_not_measured`
  - `test_unknown_label_when_there_is_nothing_at_all`
  - `test_vocabulary_is_closed_and_unknown_labels_are_rejected`

## Modification guidance

- Change measurement state policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/measurement_state.py](../../../../../../src/learnloop/learner/measurement_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
