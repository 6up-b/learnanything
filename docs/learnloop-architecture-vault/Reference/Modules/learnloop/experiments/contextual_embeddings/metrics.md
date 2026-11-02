---
title: "learnloop.experiments.contextual_embeddings.metrics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/metrics.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/metrics.py"
source_commit: "34d2068e151f70ab52d394226c810fdc208b9dee"
source_commit_timestamp: "2026-10-21T14:16:05-04:00"
source_worktree_state: "clean"
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
  - "learnloop.experiments.contextual_embeddings.metrics module"
  - "src/learnloop/experiments/contextual_embeddings/metrics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.metrics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.metrics` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0 metrics (spec §5.2): evidence sets, rankings, agreement, paired intervals.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/metrics.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py) |
| Source lines | 181 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `34d2068e151f70ab52d394226c810fdc208b9dee` |
| Commit timestamp | `2026-10-21T14:16:05-04:00` |

## Public API

- `dedupe(pieces: Sequence[SpanRef]) -> list[SpanRef]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 42) — Original spans and offsets once each (merged units never count twice).
- `complete_evidence(pieces: Sequence[SpanRef], evidence_sets: Sequence[Sequence[SpanRef]]) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 48)
- `support_recall(pieces: Sequence[SpanRef], evidence_sets: Sequence[Sequence[SpanRef]]) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 55)
- `answer_recall(pieces: Sequence[SpanRef], answer_spans: Sequence[SpanRef]) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 69)
- `ndcg(ranked: Sequence[str], labels: Mapping[str, str], *, k: int=pins.TOP_K) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 76)
- `mrr(ranked: Sequence[str], labels: Mapping[str, str], *, k: int=pins.TOP_K) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 87)
- `unknown_share(ranked: Sequence[str], labels: Mapping[str, str], *, k: int=pins.TOP_K) -> float` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 97)
- `cohen_kappa(pairs: Sequence[tuple[str, str]], categories: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 102) — Unweighted and linear-weighted κ with the confusion table.
- `paired_bootstrap(rows: Sequence[Mapping[str, Any]], *, a: str, b: str, cluster: str='family', resamples: int=pins.BOOTSTRAP_RESAMPLES, seed: int=pins.SEED) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 134) — Paired difference ``b - a`` on rows ``{cluster, a, b}`` with both scored; clusters (source families) are resampled with replacement.
- `latency_summary(values: Sequence[float]) -> dict[str, float | None]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 171)

## Internal implementation anchors

- `_covered(required: SpanRef, pieces: Sequence[SpanRef]) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 31)
- `_mean(values: Sequence[float]) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py), line 130)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `latency_summary`; statically calls `latency_summary`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `cohen_kappa`; statically calls `cohen_kappa`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `module`; statically calls `answer_recall`, `cohen_kappa`, `complete_evidence`, `mrr`, `ndcg`, `paired_bootstrap`, `support_recall`, `unknown_share`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `latency_summary`, `paired_bootstrap`; statically calls `latency_summary`, `paired_bootstrap`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `latency_summary`; statically calls `latency_summary`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_metrics_stop_rules.py](../../../../../../../tests/test_e0_metrics_stop_rules.py) — direct import
  - `test_an_unpinned_reader_latency_budget_fails_closed`
  - `test_cohen_kappa_and_confusion`
  - `test_complete_evidence_needs_every_required_span_of_one_set`
  - `test_duplicates_never_earn_extra_recall_and_ties_take_the_first_set`
  - `test_offsets_count_and_cuts_do_not_cover_the_rest`
  - `test_paired_bootstrap_is_deterministic_and_clustered`
  - `test_ranking_metrics`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_m14_s4_counts_only_the_paired_evidence_families_and_honours_exploratory`

## Modification guidance

- Make changes here when the responsibility remains metrics within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/metrics.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/metrics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
