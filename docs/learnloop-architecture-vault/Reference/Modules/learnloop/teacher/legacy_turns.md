---
title: "learnloop.teacher.legacy_turns"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/legacy_turns.py"
source_paths:
  - "src/learnloop/teacher/legacy_turns.py"
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
  - "learnloop.teacher.legacy_turns module"
  - "src/learnloop/teacher/legacy_turns.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.legacy_turns`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.legacy_turns` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The lesson contracts (spec_teacher_v1 §8): the brief, the teacher's turn, the receipt, and the actions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py) |
| Source lines | 325 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CriterionV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 58) — One rubric criterion, named by the fact it establishes (owner rule 2026-10-13).
- `class PredictionV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 66) — A nudge before a step (§10 item 7): it arrives open and need not be answerable.
- `class CheckV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 74) — A check after a step (§8.2): answerable from the lesson, applied, its solution committed first.
- `class PlanNodeV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 87)
- `class ActionRequestV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 95) — One requested action (§9).
- `class TeacherTurnV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 122) — One model turn (§8.2).
- `class PlannedVisualV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 139) — A plan node's planned visual (spec §10.4): the goal written from the brief (which quantity the learner gets to move, which stays fixed, what to watch) and the delivered passages it rests on.
- `class TeacherVisualV1(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 147) — A turn's visual (spec §6.5): either ``planned_node`` (the node whose planned visual this step shows, so it is the identical request), or a ``goal`` with the passages it rests on.
- `class PlanNodeVisualsV1(PlanNodeV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 156)
- `class ActionRequestVisualsV1(ActionRequestV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 160)
- `class TeacherTurnVisualsV1(TeacherTurnV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 164) — One model turn with ``teacher.visuals`` on: TE1's turn plus the optional ``visual``.
- `class PlanNodeEpisodesV1(PlanNodeV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 183)
- `class ActionRequestEpisodesV1(ActionRequestV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 188) — TE1's request plus ``note_detour`` (§11.7): its node is ``node``, its belief in the hypothesis ``p``.
- `class TeacherTurnEpisodesV1(TeacherTurnV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 199) — One model turn with ``teacher.episode_log`` on: TE1's turn plus ``note_detour`` and ``p_held``.
- `class PlanNodeVisualsEpisodesV1(PlanNodeVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 205)
- `class ActionRequestVisualsEpisodesV1(ActionRequestVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 209)
- `class TeacherTurnVisualsEpisodesV1(TeacherTurnVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 216) — Both switches on: the visuals turn plus ``note_detour`` and ``p_held`` (the widest stored shape).
- `class ActionRequestTE2V1(_TE2Fields, ActionRequestV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 250)
- `class TeacherTurnTE2V1(TeacherTurnV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 254)
- `class ActionRequestTE2EpisodesV1(_TE2Fields, ActionRequestEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 258)
- `class TeacherTurnTE2EpisodesV1(TeacherTurnV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 262)
- `class ActionRequestTE2VisualsV1(_TE2Fields, ActionRequestVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 266)
- `class TeacherTurnTE2VisualsV1(TeacherTurnVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 270)
- `class ActionRequestTE2VisualsEpisodesV1(_TE2Fields, ActionRequestVisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 274)
- `class TeacherTurnTE2VisualsEpisodesV1(TeacherTurnVisualsV1)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 278) — Every switch on: the widest stored shape.

### Module constants

- `BRIEF_VERSION` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 37)
- `TURN_VERSION` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 38)
- `RECEIPT_VERSION` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 39)
- `PROMPT_VERSION` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 41)
- `ACTIONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 43)
- `READ_ACTIONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 47)
- `CLOSE_REASONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 48)
- `TEACHER_CLOSE_REASONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 54)
- `FORECAST_KINDS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 55)
- `VISUAL_ANCHORS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 136)
- `DETOUR_REPAIRS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 174)
- `EPISODE_ACTIONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 176)
- `TE2_ACTIONS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 226)
- `GAP_KINDS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 227)
- `MAX_READINGS` ([src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py), line 229)

### Explicit exports

`__all__` declares:

- `ACTIONS`
- `ActionRequestTE2EpisodesV1`
- `ActionRequestTE2V1`
- `ActionRequestTE2VisualsEpisodesV1`
- `ActionRequestTE2VisualsV1`
- `GAP_KINDS`
- `MAX_READINGS`
- `TE2_ACTIONS`
- `TeacherTurnTE2EpisodesV1`
- `TeacherTurnTE2V1`
- `TeacherTurnTE2VisualsEpisodesV1`
- `TeacherTurnTE2VisualsV1`
- `ActionRequestEpisodesV1`
- `ActionRequestVisualsEpisodesV1`
- `BRIEF_VERSION`
- `CLOSE_REASONS`
- `DETOUR_REPAIRS`
- `EPISODE_ACTIONS`
- `FORECAST_KINDS`
- `PlanNodeEpisodesV1`
- `PlanNodeVisualsEpisodesV1`
- `TeacherTurnEpisodesV1`
- `TeacherTurnVisualsEpisodesV1`
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

- `class _TE2Fields(WireModel)` ([source](../../../../../../src/learnloop/teacher/legacy_turns.py), line 240) — ``serve_probe {node, readings, p}`` (``p``: the teacher's forecast of a right answer) and ``propose_gap {ref, gap_kind, gap}`` (``ref``: the learner's turn, as the transcript names it).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `ACTIONS`, `ActionRequestEpisodesV1`, `ActionRequestTE2EpisodesV1`, `ActionRequestTE2V1`, `ActionRequestTE2VisualsEpisodesV1`, `ActionRequestTE2VisualsV1`, `ActionRequestV1`, `ActionRequestVisualsEpisodesV1`, `ActionRequestVisualsV1`, `BRIEF_VERSION`, `CLOSE_REASONS`, `CheckV1`, `CriterionV1`, `DETOUR_REPAIRS`, `EPISODE_ACTIONS`, `FORECAST_KINDS`, `GAP_KINDS`, `MAX_READINGS`, `PROMPT_VERSION`, `PlanNodeEpisodesV1`, `PlanNodeV1`, `PlanNodeVisualsEpisodesV1`, `PlanNodeVisualsV1`, `PlannedVisualV1`, `PredictionV1`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TE2_ACTIONS`, `TEACHER_CLOSE_REASONS`, `TURN_VERSION`, `TeacherTurnEpisodesV1`, `TeacherTurnTE2EpisodesV1`, `TeacherTurnTE2V1`, `TeacherTurnTE2VisualsEpisodesV1`, `TeacherTurnTE2VisualsV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`, `TeacherVisualV1`, `VISUAL_ANCHORS`, `__all__`

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

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_teacher_structured_contracts.py](../../../../../../tests/test_teacher_structured_contracts.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_teacher_te5_contracts.py](../../../../../../tests/test_teacher_te5_contracts.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]
- [tests/test_teacher_te5_goal_topics.py](../../../../../../tests/test_teacher_te5_goal_topics.py) — imports consumer [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]]

## Modification guidance

- Make changes here when the responsibility remains legacy turns within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/legacy_turns.py](../../../../../../src/learnloop/teacher/legacy_turns.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
