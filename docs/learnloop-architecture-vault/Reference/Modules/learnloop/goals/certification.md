---
title: "learnloop.goals.certification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/certification.py"
source_paths:
  - "src/learnloop/goals/certification.py"
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
  - "learnloop.goals.certification module"
  - "src/learnloop/goals/certification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.certification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.certification` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Single certification threshold shared by every Demonstrated projection.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/certification.py](../../../../../../src/learnloop/goals/certification.py) |
| Source lines | 7 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `is_demonstrated_credit(credit: float) -> bool` ([source](../../../../../../src/learnloop/goals/certification.py), line 6)

### Module constants

- `DEMONSTRATED_CREDIT` ([src/learnloop/goals/certification.py](../../../../../../src/learnloop/goals/certification.py), line 3)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `is_demonstrated_credit`; statically calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `is_demonstrated_credit`; statically calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `is_demonstrated_credit`; statically calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `is_demonstrated_credit`; statically calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `is_demonstrated_credit`; statically calls `is_demonstrated_credit`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]], [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]], [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_exam_readiness_and_conflict.py](../../../../../../tests/test_exam_readiness_and_conflict.py) — imports consumer [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]]
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — imports consumer [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]]
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — imports consumer [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]]
- [tests/test_measurement_state_labels.py](../../../../../../tests/test_measurement_state_labels.py) — imports consumer [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]]
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]]

## Modification guidance

- Change certification policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/certification.py](../../../../../../src/learnloop/goals/certification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
