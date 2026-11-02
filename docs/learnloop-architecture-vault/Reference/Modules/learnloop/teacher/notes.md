---
title: "learnloop.teacher.notes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/notes.py"
source_paths:
  - "src/learnloop/teacher/notes.py"
source_commit: "6975ac1949e79b05a13f0cf392d617aa1d91fc25"
source_commit_timestamp: "2026-11-02T03:56:28-05:00"
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
  - "learnloop.teacher.notes module"
  - "src/learnloop/teacher/notes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.notes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.notes` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Curriculum C4: the learner's linked notes in a lesson (spec_deliverable_curriculum_v1 §8.2, §10.2, §10.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/notes.py](../../../../../../src/learnloop/teacher/notes.py) |
| Source lines | 85 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6975ac1949e79b05a13f0cf392d617aa1d91fc25` |
| Commit timestamp | `2026-11-02T03:56:28-05:00` |

## Public API

- `your_notes(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/teacher/notes.py), line 25) — Per LO, headers of the learner's linked notes (title, heading, date, one line): their own voice (C4).
- `read_note(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/notes.py), line 52)

### Explicit exports

`__all__` declares:

- `read_note`
- `your_notes`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `read_note`; statically calls `read_note`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `your_notes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/learner_notes|learnloop.db.stores.learner_notes]] — imports `module`; calls `links`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; calls `available`, `effective`, `enabled`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `STEM_CHARS`, `c4_active`; calls `c4_active`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — imports consumer [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]]
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_curriculum_c4.py](../../../../../../tests/test_teacher_te1_curriculum_c4.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_lesson.py](../../../../../../tests/test_teacher_te1_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]

## Modification guidance

- Make changes here when the responsibility remains notes within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/notes.py](../../../../../../src/learnloop/teacher/notes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
