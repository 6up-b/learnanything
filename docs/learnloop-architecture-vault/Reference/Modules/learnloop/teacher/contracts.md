---
title: "learnloop.teacher.contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/contracts.py"
source_paths:
  - "src/learnloop/teacher/contracts.py"
source_commit: "463f9a3041ab918891db5aad0ebbb4b7f36e641c"
source_commit_timestamp: "2026-11-02T05:17:47-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.contracts module"
  - "src/learnloop/teacher/contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.contracts` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The lesson contracts (spec_teacher_v1 §8): the brief, the teacher's turn, the receipt, and the actions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py) |
| Source lines | 193 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `463f9a3041ab918891db5aad0ebbb4b7f36e641c` |
| Commit timestamp | `2026-11-02T05:17:47-05:00` |

## Public API

- `class CriterionV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 58) — One rubric criterion, named by the fact it establishes (owner rule 2026-10-13).
- `class PredictionV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 66) — A nudge before a step (§10 item 7): it arrives open and need not be answerable.
- `class CheckV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 74) — A check after a step (§8.2): answerable from the lesson, applied, its solution committed first.
- `class PlanNodeV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 87)
- `class ActionRequestV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 95) — One requested action (§9).
- `class TeacherTurnV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 122) — One model turn (§8.2).
- `class PlannedVisualV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 139) — A plan node's planned visual (spec §10.4): the goal written from the brief (which quantity the learner gets to move, which stays fixed, what to watch) and the delivered passages it rests on.
- `class TeacherVisualV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 147) — A turn's visual (spec §6.5): either ``planned_node`` (the node whose planned visual this step shows, so it is the identical request), or a ``goal`` with the passages it rests on.
- `class PlanNodeVisualsV1(PlanNodeV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 156)
- `class ActionRequestVisualsV1(ActionRequestV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 160)
- `class TeacherTurnVisualsV1(TeacherTurnV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 164) — One model turn with ``teacher.visuals`` on: TE1's turn plus the optional ``visual``.

### Module constants

- `BRIEF_VERSION` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 37)
- `TURN_VERSION` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 38)
- `RECEIPT_VERSION` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 39)
- `PROMPT_VERSION` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 41)
- `ACTIONS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 43)
- `READ_ACTIONS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 47)
- `CLOSE_REASONS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 48)
- `TEACHER_CLOSE_REASONS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 54)
- `FORECAST_KINDS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 55)
- `VISUAL_ANCHORS` ([src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py), line 136)

### Explicit exports

`__all__` declares:

- `ACTIONS`
- `BRIEF_VERSION`
- `CLOSE_REASONS`
- `FORECAST_KINDS`
- `PROMPT_VERSION`
- `READ_ACTIONS`
- `RECEIPT_VERSION`
- `TEACHER_CLOSE_REASONS`
- `TURN_VERSION`
- `ActionRequestV1`
- `ActionRequestVisualsV1`
- `CheckV1`
- `CriterionV1`
- `PlanNodeV1`
- `PlanNodeVisualsV1`
- `PlannedVisualV1`
- `PredictionV1`
- `TeacherTurnV1`
- `TeacherTurnVisualsV1`
- `TeacherVisualV1`
- `VISUAL_ANCHORS`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `ActionRequestV1`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `BRIEF_VERSION`, `READ_ACTIONS`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `CheckV1`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `ActionRequestV1`, `CheckV1`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TURN_VERSION`, `TeacherTurnV1`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `PROMPT_VERSION`, `PlannedVisualV1`, `TeacherTurnV1`, `TeacherTurnVisualsV1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]], [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_switch_off_keeps_te1s_prompt_and_turn_schema_byte_identical`

## Modification guidance

- Make changes here when the responsibility remains contracts within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
