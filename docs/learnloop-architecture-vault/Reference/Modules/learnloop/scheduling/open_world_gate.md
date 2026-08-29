---
title: "learnloop.scheduling.open_world_gate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/open_world_gate.py"
source_paths:
  - "src/learnloop/scheduling/open_world_gate.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
operational_scope: "ACTIVE dependency-gate reporter; open-world expansion workers, schema, and successor UI are NOT_IMPLEMENTED"
concepts:
  - "Learning System"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.scheduling.open_world_gate module"
  - "src/learnloop/scheduling/open_world_gate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.open_world_gate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.open_world_gate` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 open-world expansion -- the §14.1 DEPENDENCY GATE (executable check only).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/open_world_gate.py](../../../../../../src/learnloop/scheduling/open_world_gate.py) |
| Source lines | 216 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |
| Operational scope | `ACTIVE dependency-gate reporter; open-world expansion workers, schema, and successor UI are NOT_IMPLEMENTED` |

> [!important] Active gate, inactive feature
> This module is live because it reports/enforces the dependency gate. The open-world feature behind that gate is not implemented or serving learners.

## Public API

- `class Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 32)
  - `as_dict(self) -> dict[str, Any]` (line 39; public)
- `class GateReport` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 50)
  - `as_dict(self) -> dict[str, Any]` (line 55; public)
- `evaluate_gate(vault: Any, repository: Repository) -> GateReport` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 204) — Evaluate the six §14.1 conditions and return a truthful per-condition report.

### Module constants

- `_CONDITIONS` ([src/learnloop/scheduling/open_world_gate.py](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 199)

## Internal implementation anchors

- `_has_attrs(module_name: str, attrs: tuple[str, ...]) -> tuple[bool, str]` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 71)
- `_table_exists(repository: Repository, name: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 82)
- `_c1_p0(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 95)
- `_c2_p1(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 114)
- `_c3_p2(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 133)
- `_c4_p3(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 146)
- `_c5_controller(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 159)
- `_c6_dispersion_kernel(repository: Repository) -> Condition` ([source](../../../../../../src/learnloop/scheduling/open_world_gate.py), line 177)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/controller|learnloop.cli.controller]] — imports `module`; statically calls `evaluate_gate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `module`; calls `is_admitted`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `importlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/controller|learnloop.cli.controller]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_open_world_gate.py](../../../../../../tests/test_open_world_gate.py) — direct import
  - `test_condition_six_clears_only_after_kernel_admission`
  - `test_gate_enumerates_the_six_conditions`
  - `test_gate_is_currently_not_met_blocked_by_kernel_admission`

## Modification guidance

- Change open world gate policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/open_world_gate.py](../../../../../../src/learnloop/scheduling/open_world_gate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
