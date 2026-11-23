---
title: "learnloop.pads.quoting"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/quoting.py"
source_paths:
  - "src/learnloop/pads/quoting.py"
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
  - "learnloop.pads.quoting module"
  - "src/learnloop/pads/quoting.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.quoting`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.quoting` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Whether a pad block of the learner's carries someone else's words (spec §10.9, §10.11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/quoting.py](../../../../../../src/learnloop/pads/quoting.py) |
| Source lines | 44 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `quote_sentences(quote: str) -> list[str]` ([source](../../../../../../src/learnloop/pads/quoting.py), line 28) — A quote's sentences, normalized, each long enough to count.
- `includes_quote(block_text: str, quotes: Iterable[str]) -> bool` ([source](../../../../../../src/learnloop/pads/quoting.py), line 35) — Whether ``block_text`` contains, word for word, a whole sentence of any of ``quotes``.

### Module constants

- `MIN_SENTENCE_CHARS` ([src/learnloop/pads/quoting.py](../../../../../../src/learnloop/pads/quoting.py), line 19)
- `_SENTENCE_END` ([src/learnloop/pads/quoting.py](../../../../../../src/learnloop/pads/quoting.py), line 20)
- `_WORD` ([src/learnloop/pads/quoting.py](../../../../../../src/learnloop/pads/quoting.py), line 21)

### Explicit exports

`__all__` declares:

- `MIN_SENTENCE_CHARS`
- `includes_quote`
- `quote_sentences`

## Internal implementation anchors

- `_normalized(text: str) -> str` ([source](../../../../../../src/learnloop/pads/quoting.py), line 24)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `includes_quote`; statically calls `includes_quote`
- [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] — imports `includes_quote`; statically calls `includes_quote`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]], [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd4_emission.py](../../../../../../tests/test_reader_rd4_emission.py) — direct import
  - `test_a_quote_is_a_whole_sentence_of_it_word_for_word`

## Modification guidance

- Make changes here when the responsibility remains quoting within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/quoting.py](../../../../../../src/learnloop/pads/quoting.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
