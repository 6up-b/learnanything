---
title: "learnloop.sim.student"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/student.py"
source_paths:
  - "src/learnloop/sim/student.py"
source_commit: "565100878e11bc9ac281139570040c118fbaf1a5"
source_commit_timestamp: "2026-07-08T11:43:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.student module"
  - "src/learnloop/sim/student.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.student`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.student` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Synthetic student: parameterized ground-truth learner model.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/student.py](../../../../../../src/learnloop/sim/student.py) |
| Source lines | 481 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `565100878e11bc9ac281139570040c118fbaf1a5` |
| Commit timestamp | `2026-07-08T11:43:16-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class Misconception` ([source](../../../../../../src/learnloop/sim/student.py), line 55) — A planted, systematic, confident error tied to one evidence facet.
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `class FacetParams` ([source](../../../../../../src/learnloop/sim/student.py), line 82) — Per-facet ground-truth overrides; unset fields inherit profile defaults.
- `class StudentProfile` ([source](../../../../../../src/learnloop/sim/student.py), line 91)
  - `as_dict(self) -> dict[str, Any]` (line 118; public)
- `class SimAttribution` ([source](../../../../../../src/learnloop/sim/student.py), line 149)
- `class SimOutcome` ([source](../../../../../../src/learnloop/sim/student.py), line 158) — One generated attempt outcome, ready to be resolved into a grade.
- `class SimTeachBackAnswer` ([source](../../../../../../src/learnloop/sim/student.py), line 172) — One synthesized learner answer to a teach-back follow-up question.
- `class SyntheticStudent` ([source](../../../../../../src/learnloop/sim/student.py), line 195)
  - `__init__(self, profile: StudentProfile, seed: int)` (line 196; internal)
  - `_state(self, facet_id: str) -> _FacetState` (line 212; internal)
  - `mastery_at(self, facet_id: str, day: float) -> float` (line 230; public) — Current true mastery, applying lazy exponential forgetting.
  - `projected_mastery(self, facet_id: str, day: float, extra_days: float) -> float` (line 241; public) — True mastery ``extra_days`` after ``day`` with no intervening practice.
  - `learn(self, facet_weights: Mapping[str, float], day: float) -> None` (line 257; public) — Apply practice gains (feedback was shown) after an attempt.
  - `truth_snapshot(self, day: float) -> dict[str, float]` (line 267; public)
  - `attempt(self, *, day: float, item_facet_weights: Mapping[str, float], criteria: Sequence[tuple[str, float, Mapping[str, float]]], hints_available: int, primed: bool=False) -> SimOutcome` (line 272; public) — Generate one attempt outcome.
  - `teach_back_answer(self, *, day: float, tier: str, criterion_weights: Mapping[str, float], item_facet_weights: Mapping[str, float], max_points: float) -> SimTeachBackAnswer` (line 414; public) — Answer one teach-back follow-up targeting a single rubric criterion.
  - `_confidence(self, rng, correctness: float, *, misconception_fired: bool) -> int` (line 457; internal)
  - `_latency(self, rng, p_know: float) -> int` (line 468; internal)

### Module constants

- `_MISCONCEPTION_MIN_WEIGHT` ([src/learnloop/sim/student.py](../../../../../../src/learnloop/sim/student.py), line 191)
- `_PARTIAL_CREDIT_PROBABILITY` ([src/learnloop/sim/student.py](../../../../../../src/learnloop/sim/student.py), line 192)

## Internal implementation anchors

- `class _FacetState` ([source](../../../../../../src/learnloop/sim/student.py), line 182)
- `_normalize(weights: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/sim/student.py), line 473)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `SyntheticStudent`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `FacetParams`, `Misconception`, `StudentProfile`; statically calls `FacetParams`, `Misconception`, `StudentProfile`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `StudentProfile`, `SyntheticStudent`, `_normalize`; statically calls `SyntheticStudent`, `_normalize`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `StudentProfile`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]], [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]], [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_priming_floors_effective_knowledge`
  - `test_shallow_misconception_repaired_by_priming`
  - `test_sticky_misconception_survives_priming`
- [tests/test_sim_goals.py](../../../../../../tests/test_sim_goals.py) — direct import
  - `test_projected_mastery_matches_forgetting_model`
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_teach_back_answer_respects_mastery_and_transfer_delta`
  - `test_teach_back_transfer_delta_lowers_success_statistically`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
  - `test_builtin_profiles_and_student_model`

## Modification guidance

- Make changes here when the responsibility remains student within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/student.py](../../../../../../src/learnloop/sim/student.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
