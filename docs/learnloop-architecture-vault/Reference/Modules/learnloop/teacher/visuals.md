---
title: "learnloop.teacher.visuals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/visuals.py"
source_paths:
  - "src/learnloop/teacher/visuals.py"
source_commit: "c301f12a6fb3c4eee8ec28f70ccc8e9e185849ce"
source_commit_timestamp: "2026-11-06T01:16:17-05:00"
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
  - "learnloop.teacher.visuals module"
  - "src/learnloop/teacher/visuals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.visuals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.visuals` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Reader RW5d P4b: the teacher's manipulatives (``spec_reader_show_me_figures_v1`` §6.5, §10.4; ``spec_teacher_v1`` §8.2, §10 "Instruments over description").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py) |
| Source lines | 375 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c301f12a6fb3c4eee8ec28f70ccc8e9e185849ce` |
| Commit timestamp | `2026-11-06T01:16:17-05:00` |

## Public API

- `active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 61) — ``teacher.visuals``, under ``figures.enabled`` and ``figures.show_me_enabled`` (a teacher's figure is a goal, which "show me" governs: spec §7.1).
- `on(vault: Any, builder: Builder | None) -> bool` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 70) — Whether this lesson call offers visuals: the switches, and a host that can build a figure.
- `paragraph() -> str` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 77) — The doctrine's visuals paragraph (versioned; appended to the doctrine only when on).
- `instructions(doctrine: str, visuals: bool) -> str` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 83)
- `prompt_version(visuals: bool) -> str` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 87)
- `turn_model(visuals: bool) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 91) — The strict output schema of a turn: TE1's off, with the ``visual`` on.
- `stored_turn(data: Mapping[str, Any] | None) -> TeacherTurnV1` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 97) — A stored accepted turn, read back (TE1's shape, the visuals shape and TE2-log's episode fields all validate: the widest stored shape).
- `resolve(state: Any, turn_obj: TeacherTurnV1) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 126) — The turn's visual as code builds it: ``{goal, anchors, node, planned}``, or None (none asked).
- `contract_problem(state: Any, turn_obj: TeacherTurnV1) -> str | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 157) — A visual or planned visual the lesson cannot build, as a correctable refusal (None: fine), naming the field by its location (request and node index), never by the model's text.
- `displayed(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 185) — The visual goals a turn may show the learner (the figure's line quotes its goal): the turn's own and every planned one, so each passes the lesson's guards before it is stored.
- `figure_request(state: Any, resolved: Mapping[str, Any], *, caller: Any) -> Any` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 202) — The ``FigureRequestV1`` code completes from the teacher's words (module docstring).
- `not_built_for_protection(resolved: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 240) — The record of a visual not built because the lesson's protection state changed since its brief (Codex review F1): its saved goal may carry words of a passage that is now exam or held-out material, which the figure service's check of the visual's own anchors cannot see, so nothin…
- `build(vault: Any, repository: Any, state: Any, resolved: Mapping[str, Any], builder: Builder, *, caller: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 249) — Build the step's figure: ``{status, figure_id?, reason?, code?}`` (never raises a refusal; a spend refusal of the lesson's envelope propagates, so the lesson closes with ``budget``).
- `figure_row(repository: Any, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 283)
- `figure_text(row: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 293) — The figure's words and displayed values as the lesson shows it (P3's reveal text over the stored spec or program **without its predictions**: a lesson suppresses them, :func:`lesson_view`), so a hidden prediction's prompt is neither exposure nor a reason to withhold the figure (…
- `summary(row: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 312) — What the teacher is told a shown figure is: its tier, what it demonstrates and what the learner can move (names, labels, ranges and defaults), read from the stored spec or program.
- `lesson_view(vault: Any, repository: Any, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 327) — A lesson figure as the lesson shows it NOW, or None (gone, held out since, switched off): the figure service's view with **no predictions** (suppressed in a lesson) and no fuller version (a lesson host is grammar and sketch only).

### Module constants

- `VISUALS_VERSION` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 44)
- `VISUALS_PROMPT_VERSION` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 46)
- `_PARAGRAPH` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 47)
- `SHOWN` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 50)
- `FAILED` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 51)
- `WITHHELD` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 52)
- `UNAVAILABLE` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 53)
- `STATUSES` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 54)
- `_UNAVAILABLE` ([src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py), line 220)

### Explicit exports

`__all__` declares:

- `Builder`
- `FAILED`
- `SHOWN`
- `STATUSES`
- `UNAVAILABLE`
- `VISUALS_PROMPT_VERSION`
- `VISUALS_VERSION`
- `WITHHELD`
- `active`
- `build`
- `contract_problem`
- `displayed`
- `figure_request`
- `figure_row`
- `figure_text`
- `instructions`
- `lesson_view`
- `not_built_for_protection`
- `on`
- `paragraph`
- `prompt_version`
- `resolve`
- `stored_turn`
- `summary`
- `turn_model`

## Internal implementation anchors

- `_plan_visual(state: Any, turn_obj: TeacherTurnV1, node_id: str) -> Any | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 109) — The planned visual of ``node_id``: this turn's own ``write_plan`` first, else the stored plan.
- `_anchor_problem(state: Any, anchors: Sequence[str], where: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 145) — By location (TE2-log landing, ruling R1 (b)): the anchors' indices, never their text.
- `_budget_refused(state: Any, exc: BaseException) -> bool` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 223) — The LESSON's spend envelope refused a request of the build (§17): the lesson closes ``budget``.
- `_base(resolved: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/visuals.py), line 235)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `figure_request`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `active`, `build`, `contract_problem`, `displayed`, `figure_row`, `figure_text`, `instructions`, `lesson_view`, `not_built_for_protection`, `on`, `prompt_version`, `resolve`, `summary`, `turn_model`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`, `has_tables`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `reveal_text`; calls `reveal_text`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `FigureRequest`, `module`; calls `FigureRequest`, `enabled`, `figure_view`, `figure_withheld`, `rich_row`, `show_me_enabled`, `teacher_visuals_switch`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `PROMPT_VERSION`, `PlannedVisualV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `functools`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_r5_a_planned_visual_is_prebuilt_and_the_lesson_step_reuses_it_with_no_author_call`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_e_the_visual_builder_decides_by_the_lesson_gate_alone`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_shown_figure_held_out_since_is_no_longer_shown`
  - `test_a_shown_figures_words_count_as_the_lessons_displayed_text`
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_figure_words_that_give_the_open_checks_solution_away_are_not_shown`
  - `test_held_out_inputs_are_refused_before_any_call`
  - `test_lesson_turn_builds_the_visual_through_the_figure_service`
  - `test_lesson_view_never_builds_a_pending_figure`
  - `test_review_f1_a_visual_after_protection_changed_mid_action_is_not_built`
  - `test_review_f2_a_suppressed_prediction_is_never_counted_as_shown`
  - `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family`
  - `test_switch_off_keeps_te1s_prompt_and_turn_schema_byte_identical`
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`
  - `test_the_figure_never_reaches_the_grader_and_is_never_a_help_row`

## Modification guidance

- Make changes here when the responsibility remains visuals within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/visuals.py](../../../../../../src/learnloop/teacher/visuals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
