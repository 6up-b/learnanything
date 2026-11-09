---
title: "learnloop.experiments.contextual_embeddings.evaluate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/evaluate.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/evaluate.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.evaluate module"
  - "src/learnloop/experiments/contextual_embeddings/evaluate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.evaluate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.evaluate` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: Scoring E0: per-question metrics per arm, paired comparisons, S1-S4 inputs.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/evaluate.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py) |
| Source lines | 94 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `question_rows(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], rankings: Mapping[str, Mapping[str, Sequence[str]]], labels: Mapping[str, QuestionLabels], *, k: int=pins.TOP_K) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py), line 19) — One row per question: ``{query_id, family, stratum, arm metrics...}``.
- `arm_summary(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py), line 56)
- `paired(rows: Sequence[Mapping[str, Any]], a: str, b: str, metric: str='ce10') -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py), line 69)
- `completion(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, float]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py), line 75) — The share of answerable, resolved questions each arm scored (S1).
- `agreement(all_labels: Sequence[QuestionLabels]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py), line 84)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]] — imports `arm_summary`, `completion`, `paired`; statically calls `arm_summary`, `completion`, `paired`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `agreement`, `question_rows`; statically calls `agreement`, `question_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `question_rows`; statically calls `question_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `agreement`, `arm_summary`, `completion`, `paired`, `question_rows`; statically calls `agreement`, `arm_summary`, `completion`, `paired`, `question_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `QuestionLabels`, `RELEVANCE_ORDER`, `unit_refs`; calls `unit_refs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `module`; calls `answer_recall`, `cohen_kappa`, `complete_evidence`, `mrr`, `ndcg`, `paired_bootstrap`, `support_recall`, `unknown_share`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f16_finalists_come_from_the_primary_development_slice_only`

## Modification guidance

- Make changes here when the responsibility remains evaluate within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/evaluate.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/evaluate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
