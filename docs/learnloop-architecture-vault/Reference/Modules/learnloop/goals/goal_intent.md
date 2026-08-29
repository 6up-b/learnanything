---
title: "learnloop.goals.goal_intent"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_intent.py"
source_paths:
  - "src/learnloop/goals/goal_intent.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_intent module"
  - "src/learnloop/goals/goal_intent.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_intent`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_intent` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Resolve a Goal's learner-facing quest without conflating every title with intent.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_intent.py](../../../../../../src/learnloop/goals/goal_intent.py) |
| Source lines | 56 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ResolvedGoalQuest` ([source](../../../../../../src/learnloop/goals/goal_intent.py), line 19)
- `resolve_goal_quest(goal: Goal) -> ResolvedGoalQuest | None` ([source](../../../../../../src/learnloop/goals/goal_intent.py), line 24) — Return the sentence teach-back authoring may use for transfer.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `resolve_goal_quest`; statically calls `resolve_goal_quest`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `resolve_goal_quest`; statically calls `resolve_goal_quest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_intent.py](../../../../../../tests/test_goal_intent.py) — direct import
  - `test_exam_goal_supplies_narrower_quest_when_intent_is_blank`
  - `test_explicit_learner_intent_wins_over_operational_goal`
  - `test_legacy_goal_preserves_title_as_quest`
  - `test_non_exam_learner_goal_supplies_problem_mastery_quest`
  - `test_source_ingestion_title_is_not_treated_as_learner_intent`

## Modification guidance

- Change goal intent policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_intent.py](../../../../../../src/learnloop/goals/goal_intent.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
