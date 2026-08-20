---
title: "learnloop.goals.exam_readiness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/exam_readiness.py"
source_paths:
  - "src/learnloop/goals/exam_readiness.py"
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
  - "learnloop.goals.exam_readiness module"
  - "src/learnloop/goals/exam_readiness.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.exam_readiness`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.exam_readiness` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Exam-readiness-by-task-family report (source-ingestion §15).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/exam_readiness.py](../../../../../../src/learnloop/goals/exam_readiness.py) |
| Source lines | 245 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TaskFamilyReadiness` ([source](../../../../../../src/learnloop/goals/exam_readiness.py), line 41)
  - `as_dict(self) -> dict[str, Any]` (line 53; public)
- `class ExamReadinessReport` ([source](../../../../../../src/learnloop/goals/exam_readiness.py), line 68)
  - `as_dict(self) -> dict[str, Any]` (line 77; public)
- `exam_readiness_report(vault: LoadedVault, repository: Repository, *, subject_id: str | None=None, exam_profile: dict[str, Any] | None=None, total_exam_items: int | None=None) -> ExamReadinessReport` ([source](../../../../../../src/learnloop/goals/exam_readiness.py), line 111) — Build the deterministic exam-readiness table + predicted score distribution (§15).

## Internal implementation anchors

- `_recipe_component_groups(blueprint) -> list[list[tuple[str, str]]]` ([source](../../../../../../src/learnloop/goals/exam_readiness.py), line 88) — The blueprint's requirement slots, each as the cells that can fill it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `exam_readiness_report`; statically calls `exam_readiness_report`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `exam_readiness_report`; statically calls `exam_readiness_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/exam_calibration|learnloop.goals.exam_calibration]] — imports `calibration_report`; calls `calibration_report`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `project_blueprint`; calls `project_blueprint`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_readiness_and_conflict.py](../../../../../../tests/test_exam_readiness_and_conflict.py) — direct import
  - `test_exam_readiness_predicted_score_distribution_is_analytic`
  - `test_exam_readiness_report_is_deterministic_and_labels_ready_vs_demonstrated`

## Modification guidance

- Change exam readiness policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/exam_readiness.py](../../../../../../src/learnloop/goals/exam_readiness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
