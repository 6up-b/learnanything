---
title: "learnloop.hint_window"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hint_window.py"
source_paths:
  - "src/learnloop/hint_window.py"
source_commit: "363fc7c1bd806d2f144610c830b8c3fac35e2170"
source_commit_timestamp: "2026-10-25T22:07:58-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.hint_window module"
  - "src/learnloop/hint_window.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.hint_window`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hint_window` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Which attempt a question counts toward: one definition of the hint window's session rule for every reader (RW1c fix rounds 4 and 5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hint_window.py](../../../../../src/learnloop/hint_window.py) |
| Source lines | 120 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `363fc7c1bd806d2f144610c830b8c3fac35e2170` |
| Commit timestamp | `2026-10-25T22:07:58-04:00` |

## Public API

- `workbench_bound(source_context: Mapping[str, Any] | str | None) -> bool` ([source](../../../../../src/learnloop/hint_window.py), line 53) — Whether a question's ``source_context`` (parsed, or its stored JSON) names the unfinished workbench it was asked from (Reader CA2's ``attempt_key.workbench_session_id``, written only by the server).
- `counts_in_session(*, context: str | None, question_session_id: str | None, attempt_session_id: str | None, bound: bool=False) -> bool` ([source](../../../../../src/learnloop/hint_window.py), line 69) — Whether a question in the item's window counts for an attempt (or a submit) in ``attempt_session_id``: the attempt is in no session, the question was asked in the same one, its context counts in the item's window whatever the session, or a workbench binds it (``bound``, :func:`w…
- `session_clause(session_id: str | None, *, item_window_only: bool=False) -> tuple[str, list[Any]]` ([source](../../../../../src/learnloop/hint_window.py), line 81) — :func:`counts_in_session` as SQL over ``question_events``: ``(clause, parameters)``.
- `following_attempt(asked: datetime, *, context: str | None, question_session_id: str | None, attempts: Sequence[tuple[datetime, str, str | None]], bound: bool=False) -> str | None` ([source](../../../../../src/learnloop/hint_window.py), line 97) — The attempt a question asked at ``asked`` counts toward, or None.

### Module constants

- `ITEM_WINDOW_QUESTION_CONTEXTS` ([src/learnloop/hint_window.py](../../../../../src/learnloop/hint_window.py), line 46)
- `WORKBENCH_BOUND_SQL` ([src/learnloop/hint_window.py](../../../../../src/learnloop/hint_window.py), line 50)

### Explicit exports

`__all__` declares:

- `ITEM_WINDOW_QUESTION_CONTEXTS`
- `WORKBENCH_BOUND_SQL`
- `counts_in_session`
- `following_attempt`
- `session_clause`
- `workbench_bound`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `module`; statically calls `session_clause`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `ITEM_WINDOW_QUESTION_CONTEXTS`, `following_attempt`, `workbench_bound`; statically calls `following_attempt`, `workbench_bound`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `counts_in_session`, `workbench_bound`; statically calls `counts_in_session`, `workbench_bound`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_ca2_codex_rereview.py](../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
  - `test_f13_the_field_link_reads_the_same_rule`

## Modification guidance

- Make changes here when the responsibility remains hint window within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hint_window.py](../../../../../src/learnloop/hint_window.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
