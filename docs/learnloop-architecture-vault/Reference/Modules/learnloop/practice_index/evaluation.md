---
title: "learnloop.practice_index.evaluation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/evaluation.py"
source_paths:
  - "src/learnloop/practice_index/evaluation.py"
source_commit: "1ef2f14ebf6f15de8b60736f60650017d40712d3"
source_commit_timestamp: "2026-10-15T12:39:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.evaluation module"
  - "src/learnloop/practice_index/evaluation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.evaluation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.evaluation` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: The retrieval evaluation: two-level dossier search vs direct item search.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py) |
| Source lines | 897 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ef2f14ebf6f15de8b60736f60650017d40712d3` |
| Commit timestamp | `2026-10-15T12:39:41-04:00` |

## Public API

- `distinct_queries(query_set: Sequence[Mapping[str, Any]]) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 257) — One representative row per normalized request (whitespace and case), with every row that wrote it.
- `label_id(query: str, item_id: str, item_hash: str, prompt_version: str, model: str) -> str` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 280)
- `query_metrics(ranked: Sequence[str], gains: Mapping[str, float], relevant: set[str]) -> dict[str, float | None]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 382)
- `agreement(pairs: Sequence[tuple[str, str]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 400)
- `paired_bootstrap(differences: Sequence[float], *, samples: int, seed: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 411)
- `decide(ndcg: Mapping[str, Any], recall: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 422)
- `run_retrieval_evaluation(vault: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, queries: int=40, logged_queries: int=20, seed: int=0, bootstrap_samples: int=1000, price_per_million: float | None=None, embedding_price_per_million: float | None=None, output_dir: Path | None=None, query_client: Any | None=None, judge_client: Any | None=None, embedder: Any | None=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 442) — Plan (dry run: no clients, no writes) or run the evaluation end to end.

### Module constants

- `QUERY_PROMPT_VERSION` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 91)
- `LOGGED_PROMPT_VERSION` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 92)
- `LABEL_PROMPT_VERSIONS` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 93)
- `QUERY_BATCH` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 97)
- `TOP_K` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 98)
- `MIN_SCORED_QUERIES` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 99)
- `LABEL_PROMPT_CHARS` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 100)
- `_QUERY_INSTRUCTIONS` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 102)
- `_LABEL_INSTRUCTIONS` ([src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py), line 110)

### Explicit exports

`__all__` declares:

- `LABEL_PROMPT_VERSIONS`
- `LOGGED_PROMPT_VERSION`
- `MIN_SCORED_QUERIES`
- `QUERY_PROMPT_VERSION`
- `TOP_K`
- `agreement`
- `decide`
- `label_id`
- `paired_bootstrap`
- `query_metrics`
- `run_retrieval_evaluation`

## Internal implementation anchors

- `_stable(seed: int, *parts: str) -> str` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 124)
- `_clip(text: str | None, limit: int) -> str` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 128)
- `_seeds(vault: LoadedVault, corpus: Sequence[str], existing: set[tuple[str, str]], count: int, seed: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 136)
- `_query_batches(seeds: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], str]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 171)
- `_logged_queries(repository: Repository, existing: set[tuple[str, str]], limit: int) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 185)
- `_recovered_queries(sqlite_path: Path, existing: set[tuple[str, str]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 200) — Written queries whose paid batch was checkpointed but never committed.
- `_query_row_id(kind: str, seed_id: str) -> str` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 253)
- `_candidate(vault: LoadedVault, item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 271)
- `_pass_order(query: str, pool: Sequence[str], pass_index: int) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 284)
- `_label_prompt(request: str, pass_index: int, refs: Mapping[str, dict[str, Any]]) -> str` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 289)
- `_rankings(snapshot, repository, text: str, vector, corpus) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 298)
- `_pool(ranked: Mapping[str, Sequence[str]]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 305)
- `_pass_work(vault, repository, text: str, pool: Sequence[str], pass_index: int, judge_model: str) -> tuple[dict[str, str], list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 309) — Label ids, the unlabelled items in pass order, candidates and saved rows.
- `_upper_bound_tokens(output_tokens: int) -> int` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 323)
- `_label_plan(vault, repository, snapshot, corpus, query_set, new_queries: int, judge_model: str, judge_route) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 329) — Exact pending label work for queries that can be ranked now; a full-pool upper bound for queries not yet written or embedded.
- `_dcg(gains: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 378)
- `_kappa(pairs: Sequence[tuple[str, str]]) -> float | None` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 391)
- `_mean(values: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 435)
- `_evaluation_lock(root: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 582) — One paid evaluation per vault at a time, so no label is paid for twice.
- `_run(vault, repository, snapshot, corpus, batches, recovered, logged, writer, writer_route, judge, judge_route, judge_model, budget, report, *, query_client, judge_client, embedder, embedding_price_per_million, cancelled, seed, bootstrap_samples, run_id, clock) -> None` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 599)
- `_combined(*estimates: SpendEstimate) -> SpendEstimate` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 653)
- `class _Stop(Exception)` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 662)
- `_generate_queries(vault, repository, batches, recovered, logged, writer, route, client, run_id, report, clock) -> None` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 669)
- `_validate_labels(result: RelevanceLabels, refs: Mapping[str, Any]) -> RelevanceLabels` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 728)
- `_label_all(vault, repository, query_set, rankings, judge, client, judge_model, report, clock) -> dict[tuple[str, str], list[dict[str, Any] | None]]` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 734)
- `_score(vault, repository, query_set, groups, rankings, labels, snapshot, report, *, bootstrap_samples, seed, run_id, clock) -> None` ([source](../../../../../../src/learnloop/practice_index/evaluation.py), line 778)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `run_retrieval_evaluation`; statically calls `run_retrieval_evaluation`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `agreement`, `paired_bootstrap`, `query_metrics`; statically calls `agreement`, `paired_bootstrap`, `query_metrics`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `paired_bootstrap`; statically calls `paired_bootstrap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `checkpointed_keys`, `checkpoints_for_purpose`, `eval_queries`, `insert_eval_query`, `insert_evaluation`, `judgments_by_ids`, `proposals`; calls `checkpointed_keys`, `checkpoints_for_purpose`, `eval_queries`, `insert_eval_query`, `insert_evaluation`, `judgments_by_ids`, `proposals`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `facet_items`, `facet_label`, `registered_facets`; calls `facet_items`, `facet_label`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/contracts|learnloop.practice_index.contracts]] — imports `RELEVANCE_SCORE`, `RelevanceLabels`, `WrittenQueries`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `CHECKPOINT_PREFIX`, `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `receipt_answers`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `planning_repository`, `receipt_answer`, `receipt_answers`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `cached_query_vectors`, `embed_queries`, `normalize_query`, `plan_query_embedding`, `query_id`; calls `cached_query_vectors`, `embed_queries`, `normalize_query`, `plan_query_embedding`, `query_id`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeConstraints`, `admissible_corpus`, `load_snapshot`, `rank_direct`, `rank_dossier`; calls `PracticeConstraints`, `admissible_corpus`, `load_snapshot`, `rank_direct`, `rank_dossier`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `sweep_practice_usage`, `usage_summary`; calls `sweep_practice_usage`, `usage_summary`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `hashlib`, `json`, `math`, `pathlib`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_batch_dry_runs_never_migrate_an_older_rollback_database`
- [tests/test_practice_index_evaluation.py](../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_blocked_states_make_no_calls`
  - `test_caps_are_checked_against_the_whole_plan_first`
  - `test_dry_run_estimates_without_clients_or_writes`
  - `test_duplicate_queries_cannot_manufacture_a_winning_evaluation`
  - `test_end_to_end_with_fakes_persists_a_decision_and_reruns_free`
  - `test_label_agreement_reports_exact_and_kappa`
  - `test_paid_labels_and_queries_survive_a_failed_write`
  - `test_paid_labels_and_queries_whose_checkpoint_failed_are_recovered_from_receipts`
  - `test_paired_bootstrap_is_seeded`
  - `test_query_metrics_ndcg_and_recall`
  - `test_switch_off_and_caps_stop_before_a_decision`
  - `test_the_bar`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_an_alternative_embedding_model_takes_an_explicit_price`

## Modification guidance

- Make changes here when the responsibility remains evaluation within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/evaluation.py](../../../../../../src/learnloop/practice_index/evaluation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
