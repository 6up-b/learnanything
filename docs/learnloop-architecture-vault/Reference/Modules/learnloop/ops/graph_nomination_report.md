---
title: "learnloop.ops.graph_nomination_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/graph_nomination_report.py"
source_paths:
  - "src/learnloop/ops/graph_nomination_report.py"
source_commit: "6c6416d3ca89094d26835f12605096415eb44ed9"
source_commit_timestamp: "2026-10-12T12:11:15-04:00"
source_worktree_state: "clean"
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
  - "learnloop.ops.graph_nomination_report module"
  - "src/learnloop/ops/graph_nomination_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.graph_nomination_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.graph_nomination_report` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Slice 2 T5 report (spec §13): nomination recall on doctor-found duplicates.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py) |
| Source lines | 361 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6c6416d3ca89094d26835f12605096415eb44ed9` |
| Commit timestamp | `2026-10-12T12:11:15-04:00` |

## Public API

- `ground_truth(loaded: LoadedVault) -> dict[str, dict[str, set[tuple[str, str]]]]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 67) — ``{"facet"|"concept": {source: {(a, b), ...}}}`` from the lexical review passes.
- `recall_block(index: RegistryIndex | None, status: str, sources: dict[str, set[tuple[str, str]]], *, top_k: int, ks: Iterable[int]=RECALL_KS) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 136) — Recall@k of each ground-truth source under the stored index.
- `repair_shadow_block(loaded: LoadedVault, nominator: GraphNominator) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 222) — The repair-equivalence shadow over the D2 re-run's comparable pairs.
- `ingest_records(loaded: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 259) — What ingest-time nominations did, from synthesis-run records.
- `nomination_report(loaded: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, stored_only: bool=False, batch_size: int=32, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, client_factory: Callable[[], EmbeddingClient] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 296) — Plan (``dry_run``), backfill what the report reads, then report.

### Module constants

- `REPORT_VERSION` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 55)
- `REPORT_RECIPES` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 56)
- `RECALL_KS` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 57)
- `RECALL_TARGETS` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 58)
- `MAX_LISTED` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 59)
- `LEDGER_TASKS` ([src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 60)

## Internal implementation anchors

- `_pair(left: str, right: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 63)
- `_ledger(loaded: LoadedVault) -> tuple[dict[str, set[tuple[str, str]]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 84) — Confirmed pairs between current registry records, and verdict counts.
- `_quantiles(values: Iterable[float]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/ops/graph_nomination_report.py), line 125)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `nomination_report`; statically calls `nomination_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `near_duplicate_facet_review`; calls `near_duplicate_facet_review`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `MintDisposition`, `judge_facet_mints`; calls `judge_facet_mints`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `CONCEPT_RECIPE`, `FACET_RECIPE`, `GraphNominator`, `NOMINATION_VERSION`, `RegistryIndex`, `annotate_mint_report`, `raw_cosine`, `repair_query`; calls `GraphNominator`, `annotate_mint_report`, `raw_cosine`, `repair_query`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `concept_merge_candidate_pairs`; calls `concept_merge_candidate_pairs`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `math`, `sqlite3`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_nomination_report.py](../../../../../../tests/test_graph_nomination_report.py) — direct import
  - `test_dry_run_plans_the_backfill_without_calls_or_changes`
  - `test_ledger_same_verdicts_join_the_ground_truth`
  - `test_report_measures_recall_cutoffs_noise_and_the_repair_shadow`
  - `test_stored_only_reports_without_paying`

## Modification guidance

- Make changes here when the responsibility remains graph nomination report within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/graph_nomination_report.py](../../../../../../src/learnloop/ops/graph_nomination_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
