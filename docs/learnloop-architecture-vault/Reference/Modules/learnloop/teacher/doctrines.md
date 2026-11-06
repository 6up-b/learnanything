---
title: "learnloop.teacher.doctrines"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/doctrines.py"
source_paths:
  - "src/learnloop/teacher/doctrines.py"
source_commit: "beaea47c7cbfc3c34dfa2d418977b26cf4d8ce88"
source_commit_timestamp: "2026-11-01T18:59:57-05:00"
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
  - "learnloop.teacher.doctrines module"
  - "src/learnloop/teacher/doctrines.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.doctrines`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.doctrines` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The doctrine: the teacher's policy, a versioned prompt set (spec_teacher_v1 §10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/doctrines.py](../../../../../../src/learnloop/teacher/doctrines.py) |
| Source lines | 38 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `beaea47c7cbfc3c34dfa2d418977b26cf4d8ce88` |
| Commit timestamp | `2026-11-01T18:59:57-05:00` |

## Public API

- `doctrine_text() -> str` ([source](../../../../../../src/learnloop/teacher/doctrines.py), line 21) — The doctrine's files in order, joined.
- `doctrine_hash() -> str` ([source](../../../../../../src/learnloop/teacher/doctrines.py), line 30)
- `doctrine_identity() -> dict[str, str]` ([source](../../../../../../src/learnloop/teacher/doctrines.py), line 34)

### Module constants

- `DOCTRINE_VERSION` ([src/learnloop/teacher/doctrines.py](../../../../../../src/learnloop/teacher/doctrines.py), line 16)
- `_DIRECTORY` ([src/learnloop/teacher/doctrines.py](../../../../../../src/learnloop/teacher/doctrines.py), line 17)

### Explicit exports

`__all__` declares:

- `DOCTRINE_VERSION`
- `doctrine_hash`
- `doctrine_identity`
- `doctrine_text`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `doctrine_identity`; statically calls `doctrine_identity`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `DOCTRINE_VERSION`, `doctrine_identity`, `doctrine_text`; statically calls `doctrine_identity`, `doctrine_text`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `functools`, `hashlib`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_switch_off_keeps_te1s_prompt_and_turn_schema_byte_identical`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_switch_off_keeps_te1s_lesson_byte_identical`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`

## Modification guidance

- Make changes here when the responsibility remains doctrines within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/doctrines.py](../../../../../../src/learnloop/teacher/doctrines.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
