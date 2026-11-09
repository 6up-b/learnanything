---
title: "learnloop.matching.kinds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/matching/kinds.py"
source_paths:
  - "src/learnloop/matching/kinds.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.matching.kinds module"
  - "src/learnloop/matching/kinds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-matching"
---

# `learnloop.matching.kinds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.matching.kinds` exists within [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] to own the behavior summarized by its module contract: What a "same or different?" question is about (Slice 2 R4, §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/matching/kinds.py](../../../../../../src/learnloop/matching/kinds.py) |
| Source lines | 115 |
| Owning package | [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Subject` ([source](../../../../../../src/learnloop/matching/kinds.py), line 30) — One thing that may be "the same" as another.
- `class EmbeddingIdentity` ([source](../../../../../../src/learnloop/matching/kinds.py), line 51) — Which stored vectors a side of a kind reads (``embedding_vectors`` keys).
- `class MatchKind` ([source](../../../../../../src/learnloop/matching/kinds.py), line 66)
  - `pool_identity(self) -> EmbeddingIdentity` (line 99; public)
  - `query_identity(self) -> EmbeddingIdentity` (line 102; public)
  - `symmetric(self) -> bool` (line 111; public)

### Module constants

- `VERDICTS` ([src/learnloop/matching/kinds.py](../../../../../../src/learnloop/matching/kinds.py), line 26)

### Explicit exports

`__all__` declares:

- `EmbeddingIdentity`
- `MatchKind`
- `Subject`
- `VERDICTS`

## Internal implementation anchors

- `_default_render(subject: Subject) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/matching/kinds.py), line 61)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `MatchKind`, `Subject`; statically calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `Subject`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `MatchKind`, `Subject`; statically calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `Subject`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `Subject`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `MatchKind`, `Subject`; statically calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] — imports `EmbeddingIdentity`, `MatchKind`, `Subject`, `VERDICTS`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `EmbeddingIdentity`, `MatchKind`, `Subject`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]], [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f1_a_fenced_pair_is_not_a_verdict`
- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains kinds within learnloop.matching; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/matching/kinds.py](../../../../../../src/learnloop/matching/kinds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
