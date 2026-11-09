---
title: "learnloop.text_canon"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/text_canon.py"
source_paths:
  - "src/learnloop/text_canon.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.text_canon module"
  - "src/learnloop/text_canon.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.text_canon`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.text_canon` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: One definition of how text is canonicalised before it is matched or sent (RW1c fix round 11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/text_canon.py](../../../../../src/learnloop/text_canon.py) |
| Source lines | 63 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `collapse_whitespace(text: str | None) -> str` ([source](../../../../../src/learnloop/text_canon.py), line 28) — Whitespace runs as one space, the ends trimmed.
- `canonical(text: str | None) -> str` ([source](../../../../../src/learnloop/text_canon.py), line 45) — NFKC, no invisible format characters, whitespace collapsed: a true fixed point, ``canonical(canonical(x)) == canonical(x)``.

### Module constants

- `_MAX_PASSES` ([src/learnloop/text_canon.py](../../../../../src/learnloop/text_canon.py), line 36)

### Explicit exports

`__all__` declares:

- `canonical`
- `collapse_whitespace`

## Internal implementation anchors

- `_pass(value: str) -> str` ([source](../../../../../src/learnloop/text_canon.py), line 39)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `collapse_whitespace`; statically calls `collapse_whitespace`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `collapse_whitespace`; statically calls `collapse_whitespace`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `canonical`; statically calls `canonical`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `canonical`; statically calls `canonical`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `canonical`; statically calls `canonical`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]], [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]], [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]], [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw1c_review.py](../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_canonical_is_a_fixed_point`
  - `test_every_sent_model_written_fragment_was_checked`
  - `test_the_verifys_cold_thread_case_delivers_what_was_scored`

## Modification guidance

- Make changes here when the responsibility remains text canon within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/text_canon.py](../../../../../src/learnloop/text_canon.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
