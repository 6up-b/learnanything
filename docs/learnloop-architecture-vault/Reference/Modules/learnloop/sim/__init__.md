---
title: "learnloop.sim"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/__init__.py"
source_paths:
  - "src/learnloop/sim/__init__.py"
source_commit: "b0b0834ba8577623dad59e6a171029f6b7970b50"
source_commit_timestamp: "2026-07-06T20:57:41-04:00"
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
  - "learnloop.sim module"
  - "src/learnloop/sim/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Synthetic-student simulation harness for the LearnLoop belief pipeline.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/__init__.py](../../../../../../src/learnloop/sim/__init__.py) |
| Source lines | 20 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `b0b0834ba8577623dad59e6a171029f6b7970b50` |
| Commit timestamp | `2026-07-06T20:57:41-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

No public top-level function or class definition is declared in this file.

### Explicit exports

`__all__` declares:

- `BUILTIN_PROFILES`
- `load_profile`
- `SimReport`
- `run_simulation`
- `run_sweep`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `BUILTIN_PROFILES`, `load_profile`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SimReport`, `run_simulation`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `run_sweep`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/__init__.py](../../../../../../src/learnloop/sim/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
