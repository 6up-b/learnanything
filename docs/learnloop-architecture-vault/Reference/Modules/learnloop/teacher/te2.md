---
title: "learnloop.teacher.te2"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/te2.py"
source_paths:
  - "src/learnloop/teacher/te2.py"
source_commit: "workspace/uncommitted @ HEAD a21f088b16f700d0b88634b19f64720fc58016ff"
source_commit_timestamp: "2026-11-06T03:32:49-05:00"
source_worktree_state: "untracked"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.te2` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE2's switch, prompt and turn shape (spec_teacher_v1 rev 5 §9, §11.3, §11.5, §11.7, §11.8, §18.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD a21f088b16f700d0b88634b19f64720fc58016ff` |
| Commit timestamp | `2026-11-06T03:32:49-05:00` |

## Public API

- `on(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/te2.py), line 54) — TE2 serves: the vault at its successor or later, lessons on and ``teacher.probes`` on.
- `lesson_te2(state: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/te2.py), line 64) — The lesson was opened under TE2 (its brief is ``lesson_brief_v2``).
- `paragraph() -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 71)
- `instructions(text: str, te2: bool) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 75)
- `prompt_version(base: str, te2: bool) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 79)
- `doctrine_family(doctrine: str, te2: bool) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 83) — §12.2: a turn under the TE2 paragraph is a different forecaster (its own λ posterior).
- `turn_model(base: type[TeacherTurnV1], te2: bool) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/te2.py), line 97) — The turn's strict schema: ``base`` off; with ``serve_probe`` and ``propose_gap`` on.
- `stored_turn(data: Mapping[str, Any] | None) -> TeacherTurnV1` ([source](../../../../../../src/learnloop/teacher/te2.py), line 103) — A stored accepted turn read back: TE1's widest shape when it validates (so a TE1 turn reads back exactly as before), else TE2's widest (a turn holding a TE2 request).
- `learner_ref(entry: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 113) — How the transcript names a learner's turn (``propose_gap``'s ``ref``).
- `delayed_check_words(vault: Any, repository: Any, learning_object_id: str, *, withheld: Any, attempted: set[str]) -> str` ([source](../../../../../../src/learnloop/teacher/te2.py), line 124) — Whether a delayed check could be committed on the LO now: an unseen, unrevealed, unwithheld question exists (the delayed checks' own candidate rule, before this lesson shows anything), or none yet.
- `where_you_left_off(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, exclude: str | None, notes_check: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/te2.py), line 136) — The newest earlier lesson on these LOs with a stored plan: its latest plan version, labelled "where you left off" (§11.8).

### Module constants

- `TE2_VERSION` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 42)
- `PROMPT_SUFFIX` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 43)
- `BRIEF_VERSION_V2` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 44)
- `LESSON_SURFACE` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 46)
- `UNSEEN_EXISTS` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 48)
- `UNSEEN_NONE` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 49)
- `WHERE_YOU_LEFT_OFF` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 50)
- `_PARAGRAPH` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 51)
- `_TE2_TURNS` ([src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py), line 89)

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

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `on`; statically calls `on`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `delayed_check_words`, `module`; statically calls `delayed_check_words`, `where_you_left_off`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `LESSON_SURFACE`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `doctrine_family`, `instructions`, `learner_ref`, `lesson_te2`, `on`, `prompt_version`, `stored_turn`, `turn_model`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `on`; statically calls `on`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `on`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `TEACHER_PROBES_VERSIONS`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `lessons_on`, `plans`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `candidates`, `revealed_items`; calls `candidates`, `revealed_items`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `recap_admissible`; calls `recap_admissible`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `TeacherTurnEpisodesV1`, `TeacherTurnTE2EpisodesV1`, `TeacherTurnTE2V1`, `TeacherTurnTE2VisualsEpisodesV1`, `TeacherTurnTE2VisualsV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`, `TeacherTurnVisualsV1`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `functools`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te2_lessons.py](../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_on_the_brief_is_v2_and_the_turn_carries_te2s_actions`
  - `test_switch_off_or_below_the_tag_gives_te1s_lesson_byte_for_byte`
  - `test_the_next_lesson_on_the_same_topics_starts_where_the_last_left_off`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_lessons_off`

## Modification guidance

- Make changes here when the responsibility remains te2 within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/te2.py](../../../../../../src/learnloop/teacher/te2.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
