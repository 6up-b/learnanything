---
title: "learnloop.passage_union.promoted"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/passage_union/promoted.py"
source_paths:
  - "src/learnloop/passage_union/promoted.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.passage_union"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.passage_union.promoted module"
  - "src/learnloop/passage_union/promoted.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-passage-union"
---

# `learnloop.passage_union.promoted`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.passage_union.promoted` exists within [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] to own the behavior summarized by its module contract: ``passage.promoted`` (spec §9.1, §0 item 7): up to four rows at the top of the split menu, from what LearnLoop knows about the object the menu was opened on, each with its glyph, its label, its reason and an action.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/passage_union/promoted.py](../../../../../../src/learnloop/passage_union/promoted.py) |
| Source lines | 181 |
| Owning package | [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Row` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 36)
  - `wire(self) -> dict[str, Any]` (line 54; public)
- `object_key(object_kind: str, *, extraction_id: str | None=None, span_id: str | None=None, annotation_id: str | None=None, block_id: str | None=None, window_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 61) — The object a menu was opened on, as one string (what a row's id and its labels are keyed by).
- `row_id(key: str, kind: str, target: Any) -> str` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 72)
- `cheap_rows(key: str, places: Sequence[tuple[str, str, Mapping[str, Any]]], elsewhere: Sequence[Any]=()) -> list[Row]` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 81) — The rows the union read of the object's passages gives (``places``: each passage's reading, span and union entry), and another passage the cue judge tied to the same problem (``elsewhere``: passage-link findings).
- `finding_rows(key: str, findings: Iterable[Any]) -> list[Row]` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 140) — The judged rows: correspondents and search findings.
- `rank(rows: Iterable[Row], *, dismissed: Iterable[str]=(), cap: int=CAP) -> list[Row]` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 156) — Option A (an orchestrator default the owner may override): the learner's history most recent first; then the rest by their own judge's rank, checked before unchecked; one of each kind before a second; ties by row id; dismissed or "not this" rows left out; at most ``cap``.
- `dismissed_rows(labels: Iterable[Mapping[str, Any]]) -> set[str]` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 176)

### Module constants

- `CAP` ([src/learnloop/passage_union/promoted.py](../../../../../../src/learnloop/passage_union/promoted.py), line 30)
- `OBJECT_KINDS` ([src/learnloop/passage_union/promoted.py](../../../../../../src/learnloop/passage_union/promoted.py), line 31)
- `DISMISSING` ([src/learnloop/passage_union/promoted.py](../../../../../../src/learnloop/passage_union/promoted.py), line 32)

### Explicit exports

`__all__` declares:

- `CAP`
- `DISMISSING`
- `OBJECT_KINDS`
- `Row`
- `cheap_rows`
- `dismissed_rows`
- `finding_rows`
- `object_key`
- `rank`
- `row_id`

## Internal implementation anchors

- `_date(stamp: Any) -> str` ([source](../../../../../../src/learnloop/passage_union/promoted.py), line 77)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `module`; statically calls `cheap_rows`, `dismissed_rows`, `finding_rows`, `object_key`, `rank`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_menu_promoted_rows.py](../../../../../../tests/test_menu_promoted_rows.py) — direct import
  - `test_a_dismissed_or_wrong_row_is_left_out_on_that_object`
  - `test_a_due_check_is_never_a_row`
  - `test_the_order_learners_history_first_then_judges_rank_one_of_a_kind_first_at_most_four`

## Modification guidance

- Make changes here when the responsibility remains promoted within learnloop.passage_union; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/passage_union/promoted.py](../../../../../../src/learnloop/passage_union/promoted.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
