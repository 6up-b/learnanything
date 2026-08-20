---
title: "learnloop.sim.kinship_admission"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/kinship_admission.py"
source_paths:
  - "src/learnloop/sim/kinship_admission.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.kinship_admission module"
  - "src/learnloop/sim/kinship_admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.kinship_admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.kinship_admission` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: P4 step 5 -- planted-learner ADMISSION sim for the heuristic soft-kinship feature (spec_p4_controller_and_scale §8.4; design §B step 5, §E).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py) |
| Source lines | 116 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class KinshipAdmissionReport` ([source](../../../../../../src/learnloop/sim/kinship_admission.py), line 53) — A SweepReport-shaped object (``.results`` + ``.as_dict()``) the P0.5 certificate machinery consumes, plus the direction check (condition A).
  - `discount_shift(self) -> float` (line 64; public)
  - `moves_discount_correctly(self) -> bool` (line 68; public)
  - `no_decision_flip(self) -> bool` (line 72; public)
  - `as_dict(self) -> dict[str, Any]` (line 75; public)
- `run_admission_sim(*, threshold: float, discount_hi: float=0.9, plausible_low: float=0.01, plausible_high: float=0.2, grid_points: int=5) -> KinshipAdmissionReport` ([source](../../../../../../src/learnloop/sim/kinship_admission.py), line 88)

### Module constants

- `_REPEAT_SUBJECT` ([src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py), line 36)
- `_REPEAT_KIN` ([src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py), line 37)
- `_FRESH_SUBJECT` ([src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py), line 38)
- `_FRESH_KIN` ([src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py), line 39)

## Internal implementation anchors

- `_pair_discount(subject: dict[str, float], kin: dict[str, float], discount_hi: float) -> float` ([source](../../../../../../src/learnloop/sim/kinship_admission.py), line 42) — Mirror kinship_feature._default_judge's discount without a DB: the SHARED strength (element-wise min over the union) drives a bounded discount.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `run_admission_sim`; statically calls `run_admission_sim`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `warmth_score`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — imports consumer [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]]
- [tests/test_open_world_gate.py](../../../../../../tests/test_open_world_gate.py) — imports consumer [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]]

## Modification guidance

- Make changes here when the responsibility remains kinship admission within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/kinship_admission.py](../../../../../../src/learnloop/sim/kinship_admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
