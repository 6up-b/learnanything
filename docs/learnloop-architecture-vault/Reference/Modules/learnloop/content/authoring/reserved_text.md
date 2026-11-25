---
title: "learnloop.content.authoring.reserved_text"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/reserved_text.py"
source_paths:
  - "src/learnloop/content/authoring/reserved_text.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.reserved_text module"
  - "src/learnloop/content/authoring/reserved_text.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.reserved_text`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.reserved_text` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: The questions kept for an exam, in text: one predicate for every reader that must not show or send one.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/reserved_text.py](../../../../../../../src/learnloop/content/authoring/reserved_text.py) |
| Source lines | 90 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReservedBook` ([source](../../../../../../../src/learnloop/content/authoring/reserved_text.py), line 40) — The questions still reserved for an exam or held out, read once per turn (``questions``: ``practice_leakage.ReservedQuestions``).
- `reserved_book(vault: Any, repository: Any) -> ReservedBook` ([source](../../../../../../../src/learnloop/content/authoring/reserved_text.py), line 48) — The reserved and held-out questions as the rest of LearnLoop reads them: ``withheld_items`` (exam pools, held-out units and the items made from them, live assessment reservations), then ``reserved_questions`` (their stems, keys and rubrics, and every held-out span).
- `quotes_reserved(text: str, reserved: ReservedBook) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/reserved_text.py), line 65) — Whether ``text`` reproduces a reserved or held-out question by the matcher's span rule.

### Module constants

- `RESERVED_SPAN_KINDS` ([src/learnloop/content/authoring/reserved_text.py](../../../../../../../src/learnloop/content/authoring/reserved_text.py), line 36)

### Explicit exports

`__all__` declares:

- `RESERVED_SPAN_KINDS`
- `ReservedBook`
- `quotes_reserved`
- `reserved_book`

## Internal implementation anchors

- `_normalized_words(text: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/reserved_text.py), line 17)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `quotes_reserved`, `reserved_book`; statically calls `quotes_reserved`, `reserved_book`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `RESERVED_SPAN_KINDS`, `ReservedBook`, `quotes_reserved`, `reserved_book`; statically calls `quotes_reserved`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`; calls `distinctive_words`, `inventory_for_texts`, `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]], [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te5_review_protection.py](../../../../../../../tests/test_teacher_te5_review_protection.py) — direct import
  - `test_typed_goal_catalog_is_screened_and_fails_closed`

## Modification guidance

- Change reserved text policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/reserved_text.py](../../../../../../../src/learnloop/content/authoring/reserved_text.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
