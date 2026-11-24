---
title: "learnloop.pads.carried"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/carried.py"
source_paths:
  - "src/learnloop/pads/carried.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.carried module"
  - "src/learnloop/pads/carried.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.carried`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.carried` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Carried questions (spec §10.12): a question the learner carries, beside a passage or not, until it bears fruit or they let it go.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py) |
| Source lines | 139 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CarriedRefused(Exception)` ([source](../../../../../../src/learnloop/pads/carried.py), line 37)
  - `__init__(self, code: str, message: str, details: dict[str, Any] | None=None) -> None` (line 38; internal)
- `check_question(text: str, anchor: dict[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/pads/carried.py), line 50) — The question's words, or its own refusal (``empty_question``, ``bad_anchor``): checked before anything else about it (a caller's protection check comes after these, so they keep their codes).
- `carry(repository: Any, *, carried_id: str, text: str, origin_kind: str, origin_ref: str | None, anchor: dict[str, Any] | None, desk_id: str | None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/carried.py), line 62) — Carry one question; returns it (``created`` false on a retry).
- `mark(repository: Any, *, event_id: str, carried_id: str, event: str, expected_version: int | None, ref: str | None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/carried.py), line 85) — A label (``fruitful``, ``not_now``, ``let_go``: needs ``expected_version``) or a notice (``surfaced``, ``ignored``: changes nothing).
- `listing(repository: Any, *, which: str, desk_id: str | None, cursor: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/carried.py), line 115) — Carried questions, longest carried first, a page at a time: ``open`` (still carried), ``closed`` or ``all``.
- `history(repository: Any, carried_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/carried.py), line 130)

### Module constants

- `ORIGINS` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 25)
- `LABELS` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 26)
- `OPEN_STATES` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 27)
- `CLOSED_STATES` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 28)
- `NOTICES` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 30)
- `PAGE_SIZE` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 31)
- `SHELF_LIMIT` ([src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py), line 34)

### Explicit exports

`__all__` declares:

- `CLOSED_STATES`
- `CarriedRefused`
- `LABELS`
- `NOTICES`
- `OPEN_STATES`
- `ORIGINS`
- `PAGE_SIZE`
- `SHELF_LIMIT`
- `carry`
- `check_question`
- `history`
- `listing`
- `mark`

## Internal implementation anchors

- `_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/carried.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `module`; statically calls `carry`, `check_question`, `listing`, `mark`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/pad_ledgers|learnloop.db.stores.pad_ledgers]] — imports `module`; calls `insert_carried`, `insert_carried_event`, `set_carried_state`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `carried`, `carried_event_exists`, `carried_events`, `list_carried`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — direct import
  - `test_the_carried_list_pages_past_the_first_fifty_and_each_question_takes_its_labels`
- [tests/test_teacher_carried_questions.py](../../../../../../tests/test_teacher_carried_questions.py) — direct import
  - `test_a_lesson_carries_the_learners_open_questions_with_the_passages_they_sit_beside`
  - `test_a_lesson_with_no_open_carried_question_is_unchanged`

## Modification guidance

- Make changes here when the responsibility remains carried within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/carried.py](../../../../../../src/learnloop/pads/carried.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
