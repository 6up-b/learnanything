---
title: "learnloop.field.decider"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/decider.py"
source_paths:
  - "src/learnloop/field/decider.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.decider module"
  - "src/learnloop/field/decider.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.decider`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.decider` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: The Decider's answer to ``learnloop field classify-questions`` (Tier 1, mvp-0.22).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/decider.py](../../../../../../src/learnloop/field/decider.py) |
| Source lines | 109 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `questions_for(row: Mapping[str, Any], catalog: list[Mapping[str, Any]]) -> dict[str, ChoiceQuestion]` ([source](../../../../../../src/learnloop/field/decider.py), line 32) — The typed questions for the metadata ``row`` is missing.
- `class Classifier` ([source](../../../../../../src/learnloop/field/decider.py), line 56) — ``classify_missing_questions``' Decider: one request per question, None to fall back.
  - `__init__(self, vault: Any, repository: Any, catalog: list[Mapping[str, Any]], prompt: Callable[[Mapping[str, Any]], str]) -> None` (line 59; internal)
  - `__call__(self, row: Mapping[str, Any], budget: Any) -> dict[str, Any] | None` (line 64; internal)
  - `log_fallback(self, raw: Mapping[str, Any], model: str) -> None` (line 93; public) — The fallback LLM's answer to each question the Decider failed, as real pairs.

### Module constants

- `TASK` ([src/learnloop/field/decider.py](../../../../../../src/learnloop/field/decider.py), line 28)
- `_FIELDS` ([src/learnloop/field/decider.py](../../../../../../src/learnloop/field/decider.py), line 29)

### Explicit exports

`__all__` declares:

- `Classifier`
- `TASK`
- `questions_for`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `Classifier`; statically calls `Classifier`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `MAX_QUESTIONS`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `Decision`, `decide_many`, `log_llm`; calls `decide_many`, `log_llm`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `QUESTION_TYPES`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_field_question_classification`

## Modification guidance

- Make changes here when the responsibility remains decider within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/field/decider.py](../../../../../../src/learnloop/field/decider.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
