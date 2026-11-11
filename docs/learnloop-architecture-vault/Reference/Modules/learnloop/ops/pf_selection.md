---
title: "learnloop.ops.pf_selection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_selection.py"
source_paths:
  - "src/learnloop/ops/pf_selection.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.pf_selection module"
  - "src/learnloop/ops/pf_selection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_selection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_selection` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Diversity scores for PF-b selection (Slice 2 §5.4 "Selection"); pure functions.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_selection.py](../../../../../../src/learnloop/ops/pf_selection.py) |
| Source lines | 88 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `tokens(text: str) -> frozenset[str]` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 26)
- `similarity(left: str, right: str) -> float` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 32)
- `kernel(texts: Sequence[str]) -> np.ndarray` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 39)
- `vendi_score(texts: Sequence[str]) -> float` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 48) — exp(Shannon entropy of the eigenvalues of K/n): the effective number of distinct items.
- `vendi_contributions(texts: Sequence[str]) -> list[float]` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 57) — Leave-one-out drop in the set's Vendi score for each member.
- `mmr_order(candidates: Sequence[tuple[str, float, str]], history: Sequence[str], *, lambda_: float=MMR_LAMBDA) -> list[dict[str, float | str]]` ([source](../../../../../../src/learnloop/ops/pf_selection.py), line 64) — Greedy MMR over ``(ref, relevance, text)`` against history and picks so far.

### Module constants

- `DIVERSITY_BASIS` ([src/learnloop/ops/pf_selection.py](../../../../../../src/learnloop/ops/pf_selection.py), line 21)
- `MMR_LAMBDA` ([src/learnloop/ops/pf_selection.py](../../../../../../src/learnloop/ops/pf_selection.py), line 22)
- `_WORD` ([src/learnloop/ops/pf_selection.py](../../../../../../src/learnloop/ops/pf_selection.py), line 23)

### Explicit exports

`__all__` declares:

- `DIVERSITY_BASIS`
- `MMR_LAMBDA`
- `kernel`
- `mmr_order`
- `similarity`
- `tokens`
- `vendi_contributions`
- `vendi_score`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `DIVERSITY_BASIS`, `mmr_order`, `similarity`, `vendi_contributions`, `vendi_score`; statically calls `mmr_order`, `similarity`, `vendi_contributions`, `vendi_score`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `re`, `typing`, `unicodedata`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/pf_generation_helpers.py](../../../../../../tests/pf_generation_helpers.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_pf_verify_extraction_parity.py](../../../../../../tests/test_pf_verify_extraction_parity.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — imports consumer [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]]

## Modification guidance

- Make changes here when the responsibility remains pf selection within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_selection.py](../../../../../../src/learnloop/ops/pf_selection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
