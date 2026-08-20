---
title: "learnloop.scheduling.intent_planner"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent_planner.py"
source_paths:
  - "src/learnloop/scheduling/intent_planner.py"
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
aliases:
  - "learnloop.scheduling.intent_planner module"
  - "src/learnloop/scheduling/intent_planner.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.intent_planner`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent_planner` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Intent-first session composition — SHADOW MODE ONLY (knowledge-model §11.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent_planner.py](../../../../../../src/learnloop/scheduling/intent_planner.py) |
| Source lines | 108 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `EVALUATION` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class SessionIntent(str, Enum)` ([source](../../../../../../src/learnloop/scheduling/intent_planner.py), line 29)
- `classify_intent(vault: LoadedVault, item: Any) -> SessionIntent` ([source](../../../../../../src/learnloop/scheduling/intent_planner.py), line 56) — Classify one scheduled candidate into a §11.2 session intent (shadow).
- `shadow_intent_plan(vault: LoadedVault, queue: list[Any], *, top_k: int=3) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/intent_planner.py), line 74) — Compute the shadow intent + within-intent rankings for a live queue.

### Module constants

- `_INTENT_PRIORITY` ([src/learnloop/scheduling/intent_planner.py](../../../../../../src/learnloop/scheduling/intent_planner.py), line 41)
- `_INTEGRATION_MODES` ([src/learnloop/scheduling/intent_planner.py](../../../../../../src/learnloop/scheduling/intent_planner.py), line 50)
- `_RESTORE_FORGETTING_THRESHOLD` ([src/learnloop/scheduling/intent_planner.py](../../../../../../src/learnloop/scheduling/intent_planner.py), line 53)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `shadow_intent_plan`; statically calls `shadow_intent_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
  - `test_classify_intent_maps_signals`
  - `test_shadow_intent_plan_does_not_reorder_queue`

## Modification guidance

- Change intent planner policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent_planner.py](../../../../../../src/learnloop/scheduling/intent_planner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
