---
title: "learnloop.scheduling.interleaving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/interleaving.py"
source_paths:
  - "src/learnloop/scheduling/interleaving.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.interleaving module"
  - "src/learnloop/scheduling/interleaving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.interleaving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.interleaving` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 4 -- stage-aware interleaving as a FEASIBLE-SET constraint (spec §9.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/interleaving.py](../../../../../../src/learnloop/scheduling/interleaving.py) |
| Source lines | 84 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `stage_violation(candidate: 'Candidate', snapshot: 'ControllerSnapshot', block: 'AttentionBlock | None') -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/interleaving.py), line 44) — Return a stage-interleaving violation descriptor, or None.

### Module constants

- `INTERLEAVING_POLICY_VERSION` ([src/learnloop/scheduling/interleaving.py](../../../../../../src/learnloop/scheduling/interleaving.py), line 31)
- `_COHERENT_STAGES` ([src/learnloop/scheduling/interleaving.py](../../../../../../src/learnloop/scheduling/interleaving.py), line 34)
- `_INTERLEAVE_STAGES` ([src/learnloop/scheduling/interleaving.py](../../../../../../src/learnloop/scheduling/interleaving.py), line 36)

## Internal implementation anchors

- `_block_neighborhood(block: 'AttentionBlock') -> str | None` ([source](../../../../../../src/learnloop/scheduling/interleaving.py), line 39)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `module`; statically calls `stage_violation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `Candidate`, `ControllerSnapshot`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `AttentionBlock`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_dispersion.py](../../../../../../tests/test_dispersion.py) — direct import
  - `test_discrimination_allows_interleaving`
  - `test_unstaged_block_leaves_interleaving_inert`

## Modification guidance

- Change interleaving policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/interleaving.py](../../../../../../src/learnloop/scheduling/interleaving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
