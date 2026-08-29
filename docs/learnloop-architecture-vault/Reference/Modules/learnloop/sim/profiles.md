---
title: "learnloop.sim.profiles"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/profiles.py"
source_paths:
  - "src/learnloop/sim/profiles.py"
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
  - "learnloop.sim.profiles module"
  - "src/learnloop/sim/profiles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.profiles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.profiles` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Student profile presets and YAML loading.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/profiles.py](../../../../../../src/learnloop/sim/profiles.py) |
| Source lines | 191 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `565100878e11bc9ac281139570040c118fbaf1a5` |
| Commit timestamp | `2026-07-08T11:43:16-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class ProfileError(ValueError)` ([source](../../../../../../src/learnloop/sim/profiles.py), line 111)
- `profile_from_mapping(payload: Mapping[str, Any]) -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 115)
- `load_profile(name_or_path: str) -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 175) — Resolve a built-in profile name or a YAML file path.

### Module constants

- `AUTO_FACET` ([src/learnloop/sim/profiles.py](../../../../../../src/learnloop/sim/profiles.py), line 35)
- `PLANTED_ERROR_TYPE` ([src/learnloop/sim/profiles.py](../../../../../../src/learnloop/sim/profiles.py), line 37)
- `BUILTIN_PROFILES` ([src/learnloop/sim/profiles.py](../../../../../../src/learnloop/sim/profiles.py), line 103)

## Internal implementation anchors

- `_novice() -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 40)
- `_intermediate_with_misconception() -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 54)
- `_strong_forgetter() -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 75)
- `_overconfident() -> StudentProfile` ([source](../../../../../../src/learnloop/sim/profiles.py), line 88)
- `_optional_float(value: Any) -> float | None` ([source](../../../../../../src/learnloop/sim/profiles.py), line 171)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `ProfileError`, `load_profile`; statically calls `load_profile`
- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `ProfileError`, `load_profile`; statically calls `load_profile`
- [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]] — imports `BUILTIN_PROFILES`, `load_profile`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `AUTO_FACET`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/sim/student|learnloop.sim.student]] — imports `FacetParams`, `Misconception`, `StudentProfile`; calls `FacetParams`, `Misconception`, `StudentProfile`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]], [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]], [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]], [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
  - `test_runner_confusion_is_byte_identical_when_none_vs_omitted`
  - `test_runner_planted_confusion_no_silent_diagnosis_flip_through_robust_path`
- [tests/test_sim_goals.py](../../../../../../tests/test_sim_goals.py) — direct import
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
  - `test_builtin_profiles_and_student_model`

## Modification guidance

- Make changes here when the responsibility remains profiles within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/profiles.py](../../../../../../src/learnloop/sim/profiles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
