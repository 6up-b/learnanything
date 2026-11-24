---
title: "learnloop.teacher.te2"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/te2.py"
source_paths:
  - "src/learnloop/teacher/te2.py"
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
  - "learnloop.teacher.te2 module"
  - "src/learnloop/teacher/te2.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.te2`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.te2` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE2's switch, prompt and turn shape (spec_teacher_v1 rev 5 §9, §11.3, §11.5, §11.7, §11.8, §18.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py) |
| Source lines | 195 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `on(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/te2.py), line 53) — TE2 serves: lessons are on.
- `lesson_te2(state: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/te2.py), line 60) — The lesson was opened under TE2 (its brief is ``lesson_brief_v2``).
- `paragraph() -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 67)
- `goal_paragraph() -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 76)
- `instructions(text: str, te2: bool, goal_topics: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 80)
- `prompt_version(base: str, te2: bool, goal_topics: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 85)
- `doctrine_family(doctrine: str, te2: bool, goal_topics: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 90) — §12.2: a turn under the TE2 paragraph is a different forecaster (its own λ posterior).
- `turn_model(base: type[TeacherTurnV1], te2: bool, goal_topics: bool=False) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/te2.py), line 105) — The turn's strict schema: ``base`` off; with ``serve_probe`` and ``propose_gap`` on.
- `stored_turn(data: Mapping[str, Any] | None) -> TeacherTurnV1` ([source](../../../../../../src/learnloop/teacher/te2.py), line 120) — A stored accepted turn read back: TE1's widest shape when it validates (so a TE1 turn reads back exactly as before), else TE2's widest (a turn holding a TE2 request).
- `learner_ref(entry: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 130) — How the transcript names a learner's turn (``propose_gap``'s ``ref``).
- `delayed_check_words(vault: Any, repository: Any, learning_object_id: str, *, withheld: Any, attempted: set[str]) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 141) — Whether a delayed check could be committed on the LO now: an unseen, unrevealed, unwithheld question exists (the delayed checks' own candidate rule, before this lesson shows anything), or none yet.
- `where_you_left_off(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, exclude: str | None, notes_check: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/te2.py), line 152) — The newest earlier lesson on these LOs with a stored plan: its latest plan version, labelled "where you left off" (§11.8).

### Module constants

- `TE2_VERSION` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 41)
- `PROMPT_SUFFIX` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 42)
- `BRIEF_VERSION_V2` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 43)
- `LESSON_SURFACE` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 45)
- `UNSEEN_EXISTS` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 47)
- `UNSEEN_NONE` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 48)
- `WHERE_YOU_LEFT_OFF` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 49)
- `_PARAGRAPH` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 50)
- `GOAL_VERSION` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 71)
- `GOAL_SUFFIX` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 72)
- `_TE2_TURNS` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 97)

### Explicit exports

`__all__` declares:

- `BRIEF_VERSION_V2`
- `LESSON_SURFACE`
- `PROMPT_SUFFIX`
- `TE2_VERSION`
- `UNSEEN_EXISTS`
- `UNSEEN_NONE`
- `WHERE_YOU_LEFT_OFF`
- `delayed_check_words`
- `doctrine_family`
- `instructions`
- `learner_ref`
- `lesson_te2`
- `on`
- `paragraph`
- `prompt_version`
- `stored_turn`
- `turn_model`
- `where_you_left_off`

## Internal implementation anchors

- `_with_goal_topics(model: type[TeacherTurnV1]) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/te2.py), line 113) — Each provider shape has one class identity, however callers supplied its flags.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `on`; statically calls `on`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `delayed_check_words`, `module`; statically calls `delayed_check_words`, `where_you_left_off`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `LESSON_SURFACE`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `doctrine_family`, `instructions`, `learner_ref`, `lesson_te2`, `on`, `prompt_version`, `stored_turn`, `turn_model`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `lessons_on`, `plans`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `check_available`; calls `check_available`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `recap_admissible`; calls `recap_admissible`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `CreateGoalLo`, `TeacherTurnEpisodesV1`, `TeacherTurnTE2EpisodesV1`, `TeacherTurnTE2V1`, `TeacherTurnTE2VisualsEpisodesV1`, `TeacherTurnTE2VisualsV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `functools`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_check_credit_characterization.py](../../../../../../tests/test_check_credit_characterization.py) — direct import
  - `test_below_the_tag_an_offer_is_built_with_a_check_whether_or_not_a_question_exists`
  - `test_both_tags_an_offer_with_no_eligible_question`
- [tests/test_check_inputs.py](../../../../../../tests/test_check_inputs.py) — direct import
  - `test_the_adapters_write_nothing_and_call_no_model`
  - `test_the_brief_says_the_same_words_and_the_offer_reads_the_same_rule`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family`
  - `test_switch_off_keeps_the_lessons_prompt_and_turn_schema_without_the_visuals_paragraph`
- [tests/test_teacher_structured_contracts.py](../../../../../../tests/test_teacher_structured_contracts.py) — direct import
  - `test_all_eight_turn_variants_check_inside_receipt`
- [tests/test_teacher_te2_lessons.py](../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_on_the_brief_is_v2_and_the_turn_carries_te2s_actions`
  - `test_the_next_lesson_on_the_same_topics_starts_where_the_last_left_off`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_the_gate_reads_on_with_lessons_on_and_off_with_lessons_off`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_switch_off_keeps_the_lesson_without_the_episode_paragraph`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo`
  - `test_switch_off_has_no_p_held_and_writes_no_forecast`
- [tests/test_teacher_te5_contracts.py](../../../../../../tests/test_teacher_te5_contracts.py) — direct import
  - `test_recovery_keeps_the_predecessors_plan_and_read_payloads`

## Modification guidance

- Make changes here when the responsibility remains te2 within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
