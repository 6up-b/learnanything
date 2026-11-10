---
title: "learnloop.teacher.notes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/notes.py"
source_paths:
  - "src/learnloop/teacher/notes.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.notes` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Curriculum C4: the learner's linked notes in a lesson (spec_deliverable_curriculum_v1 §8.2, §10.2, §10.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/notes.py](../../../../../../src/learnloop/teacher/notes.py) |
| Source lines | 118 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `your_notes(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/teacher/notes.py), line 25) — Per LO, headers of the learner's linked notes (title, heading, date, one line): their own voice (C4).
- `read_note(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/notes.py), line 52)
- `notes_still_deliverable(vault: Any, repository: Any, note_refs: Sequence[str]) -> bool` ([source](../../../../../../src/learnloop/teacher/notes.py), line 84) — Whether every note a lesson was given (``n:<link id>``: a ``your_notes`` header or a ``read_note`` text) could still be given now, so an earlier lesson's recap may carry what it took from them (followups batch 5, Codex review F2; :func:`learnloop.teacher.brief.recap_admissible`…

### Explicit exports

`__all__` declares:

- `notes_still_deliverable`
- `read_note`
- `your_notes`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `notes_still_deliverable`, `read_note`; statically calls `read_note`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `notes_still_deliverable`, `your_notes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/learner_notes|learnloop.db.stores.learner_notes]] — imports `module`; calls `links`, `links_by_id`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; calls `available`, `effective`, `enabled`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `module`; calls `anchor_sources`, `snapshot_protected_keys`, `split_key`
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

- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../tests/test_followups_batch5_recap_dependencies.py) — direct import
  - `test_f2_a_recap_after_read_note_is_left_out_once_only_the_note_s_source_is_protected`
  - `test_f2_the_note_dependency_outlives_a_later_link_change`
  - `test_f2_without_the_notes_check_a_lesson_that_was_given_notes_fails_closed`

## Modification guidance

- Make changes here when the responsibility remains notes within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/notes.py](../../../../../../src/learnloop/teacher/notes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
