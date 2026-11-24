---
title: "learnloop.teacher.contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/contracts.py"
source_paths:
  - "src/learnloop/teacher/contracts.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.contracts` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Public lesson contracts.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py) |
| Source lines | 178 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `capabilities(*, visuals: bool, episodes: bool, probes: bool) -> Capabilities` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 60)
- `lesson_capabilities(lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]]) -> Capabilities` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 71)
- `class ReadSource(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 83)
- `class FindSources(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 87)
- `class FindPractice(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 91)
- `class ReadHistory(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 95)
- `class ReadNote(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 99)
- `class WritePlan(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 103)
- `class Forecast(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 107)
- `class Close(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 111)
- `class NoteDetour(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 115)
- `class ServeProbe(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 119)
- `class ProposeGap(ActionRequestTE2VisualsEpisodesV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 123)
- `class CreateGoalLo(WireModel)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 127) — Offer a topic for a phrase the learner wants to study.
- `class TeacherTurnV2(TeacherTurnVisualsV1)` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 143) — The execution contract shared by live turns and interrupted turns.
  - `admitted(self, info: ValidationInfo) -> 'TeacherTurnV2'` (line 149; public)
- `parse_turn(data: Mapping[str, Any], allowed: Capabilities) -> TeacherTurnV2` ([source](../../../../../../src/learnloop/teacher/contracts.py), line 172)

### Explicit exports

`__all__` declares:

- `Capabilities`
- `TeacherTurnV2`
- `capabilities`
- `lesson_capabilities`
- `parse_turn`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `PlannedVisualV1`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `ActionRequestV1`, `CreateGoalLo`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `READ_ACTIONS`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `CheckV1`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `TeacherTurnEpisodesV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `lesson_capabilities`; statically calls `lesson_capabilities`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `ActionRequestV1`, `Capabilities`, `CheckV1`, `CreateGoalLo`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TURN_VERSION`, `TeacherTurnV1`, `TeacherTurnV2`, `capabilities`, `lesson_capabilities`, `parse_turn`; statically calls `ActionRequestV1`, `CreateGoalLo`, `capabilities`, `lesson_capabilities`, `parse_turn`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `CreateGoalLo`, `TeacherTurnEpisodesV1`, `TeacherTurnTE2EpisodesV1`, `TeacherTurnTE2V1`, `TeacherTurnTE2VisualsEpisodesV1`, `TeacherTurnTE2VisualsV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `PROMPT_VERSION`, `PlannedVisualV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/teacher/legacy_turns|learnloop.teacher.legacy_turns]] — imports `ACTIONS`, `ActionRequestEpisodesV1`, `ActionRequestTE2EpisodesV1`, `ActionRequestTE2V1`, `ActionRequestTE2VisualsEpisodesV1`, `ActionRequestTE2VisualsV1`, `ActionRequestV1`, `ActionRequestVisualsEpisodesV1`, `ActionRequestVisualsV1`, `BRIEF_VERSION`, `CLOSE_REASONS`, `CheckV1`, `CriterionV1`, `DETOUR_REPAIRS`, `EPISODE_ACTIONS`, `FORECAST_KINDS`, `GAP_KINDS`, `MAX_READINGS`, `PROMPT_VERSION`, `PlanNodeEpisodesV1`, `PlanNodeV1`, `PlanNodeVisualsEpisodesV1`, `PlanNodeVisualsV1`, `PlannedVisualV1`, `PredictionV1`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TE2_ACTIONS`, `TEACHER_CLOSE_REASONS`, `TURN_VERSION`, `TeacherTurnEpisodesV1`, `TeacherTurnTE2EpisodesV1`, `TeacherTurnTE2V1`, `TeacherTurnTE2VisualsEpisodesV1`, `TeacherTurnTE2VisualsV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`, `TeacherVisualV1`, `VISUAL_ANCHORS`, `__all__`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]], [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_switch_off_keeps_the_lessons_prompt_and_turn_schema_without_the_visuals_paragraph`
- [tests/test_teacher_structured_contracts.py](../../../../../../tests/test_teacher_structured_contracts.py) — direct import
  - `test_all_eight_turn_variants_check_inside_receipt`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_schema_refusal_names_fields_by_location_never_by_their_input`
  - `test_switch_off_keeps_the_lesson_without_the_episode_paragraph`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_switch_off_has_no_p_held_and_writes_no_forecast`
- [tests/test_teacher_te5_contracts.py](../../../../../../tests/test_teacher_te5_contracts.py) — direct import
  - `test_legacy_open_uses_its_journal_and_brief`
  - `test_recovery_keeps_the_predecessors_plan_and_read_payloads`
  - `test_wire_and_union_admit_the_same_inputs`
- [tests/test_teacher_te5_goal_topics.py](../../../../../../tests/test_teacher_te5_goal_topics.py) — direct import
  - `test_pre_offer_schema_and_executor_refuse_new_action`

## Modification guidance

- Make changes here when the responsibility remains contracts within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/contracts.py](../../../../../../src/learnloop/teacher/contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
