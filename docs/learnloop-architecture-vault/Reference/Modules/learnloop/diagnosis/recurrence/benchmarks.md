---
title: "learnloop.diagnosis.recurrence.benchmarks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/benchmarks.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/benchmarks.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.benchmarks module"
  - "src/learnloop/diagnosis/recurrence/benchmarks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.benchmarks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.benchmarks` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: Benchmarks B1 (Eedi 2024) and B3 (vault replay) for Slice 2 T1 (§3.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py) |
| Source lines | 1379 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `class BenchRequest` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 150) — The local runner's request: the fields of Phase 5a's ``CompareRequest`` the suites read, with the same types (``dims`` is a tuple of widths).
- `requested_dims(request: Any, default: int) -> tuple[int, ...]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 166) — The widths a request asks for: 5a's tuple, a bare int, or ``default``.
- `class VectorCache` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 179) — Content-addressed float32 unit vectors in the output directory.
  - `__init__(self, root: Path, model: str, task_prefix: str, dims: int) -> None` (line 182; internal)
  - `key(text: str) -> str` (line 195; public)
  - `get(self, text: str) -> np.ndarray | None` (line 198; public)
  - `put_many(self, texts: Sequence[str], vectors: Sequence[Sequence[float]]) -> None` (line 202; public)
- `class BenchContext` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 219) — The local runner's context: the 5a contract's ``vectors`` plus ``complete``.
  - `__init__(self, vault: LoadedVault, spend: ReviewSpend, *, output_dir: Path, embedding_clients: Mapping[str, Any] | None=None, writer_client: Any=None, embedding_price: float | None=None) -> None` (line 222; internal)
  - `_embedder(self, model: str, dims: int) -> Any` (line 241; internal)
  - `vectors(self, model: str, texts: Sequence[str], *, dims: int, task_prefix: str='similarity') -> dict[str, np.ndarray]` (line 261; public)
  - `writer_client(self, role: str) -> Any` (line 283; public)
  - `complete(self, role: str, prompt: str, result_model: type[WireModel], purpose: str, output_tokens: int | None=None) -> Any` (line 294; public)
- `writer_tokens(prompt: str, result_model: type[WireModel], output_tokens: int=B1_DEFAULT_WRITER_OUTPUT_TOKENS) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 330) — One writer call's input-plus-output bound, as 5a's harness counts it.
- `requested_writer_output_tokens(request: Any, config: Any | None=None) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 338) — The writer's output budget a request asks for.
- `writer_identity(model: str | None, settings: Mapping[str, Any], output_tokens: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 371) — Who writes B1's hypotheses: part of every hypothesis cache key (owner batch 2).
- `configured_writer(vault: LoadedVault, output_tokens: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 387) — The writer identity from config alone, as the harness plans the role.
- `roc_auc(scores: Sequence[float], labels: Sequence[bool]) -> float | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 418)
- `blocking_cutoff(scores: Sequence[float], labels: Sequence[bool], target_recall: float) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 427) — The highest cutoff whose recall on confirmed matches reaches the target (R4).
- `rank_metrics(ranks: Sequence[int | None], k: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 446)
- `class BM25` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 462) — Okapi BM25 over short documents, scored through postings.
  - `__init__(self, documents: Sequence[str], *, k1: float=1.5, b: float=0.75) -> None` (line 465; internal)
  - `scores(self, query: str) -> np.ndarray` (line 478; public)
- `class MisconceptionHypothesis(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 518)
  - `_not_blank(cls, value: str) -> str` (line 525; internal) — A blank hypothesis breaks the contract (Codex review F1).
- `b1_prompt(case: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 540)
- `class B1Data` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 576)
- `load_eedi(directory: Path, *, max_cases: int | None=None) -> tuple[dict[str, Any], list[tuple[str, str]], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 585) — Read the Kaggle files the owner downloaded (no network here).
- `raw_query(case: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 633)
- `class B1Suite` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 640)
  - `load(self, vault: LoadedVault, request: BenchRequest) -> B1Data` (line 645; public)
  - `_hypothesis_cache(self, request: BenchRequest) -> Path` (line 656; internal)
  - `_cached_hypotheses(self, request: BenchRequest) -> dict[str, str]` (line 659; internal) — Cached hypotheses by key.
  - `_case_key(case: Mapping[str, Any], writer: Mapping[str, Any]) -> str` (line 678; internal)
  - `plan(self, vault: LoadedVault, data: B1Data, request: BenchRequest) -> dict[str, Any]` (line 681; public)
  - `_write_hypotheses(self, data: B1Data, request: BenchRequest, ctx: Any) -> tuple[dict[str, str], dict[str, Any]]` (line 717; internal) — Each case's hypothesis, written or reused, and the writer's summary.
  - `run(self, data: B1Data, request: BenchRequest, ctx: Any) -> dict[str, Any]` (line 772; public)
  - `markdown_lines(self, results: Mapping[str, Any]) -> list[str]` (line 833; public) — The aggregate table the harness's Markdown report renders (owner batch 2).
- `b1_markdown_lines(results: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 839)
- `class B3Data` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 876)
- `class B3Suite` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 915)
  - `markdown_lines(self, results: Mapping[str, Any]) -> list[str]` (line 919; public) — The aggregate table the harness's Markdown report renders (owner batch 2).
  - `load(self, vault: LoadedVault, request: BenchRequest) -> B3Data` (line 924; public)
  - `plan(self, vault: LoadedVault, data: B3Data, request: BenchRequest) -> dict[str, Any]` (line 942; public)
  - `run(self, data: B3Data, request: BenchRequest, ctx: Any) -> dict[str, Any]` (line 962; public)
  - `_score(self, data: B3Data, by_id: Mapping[str, Any], vectors: Mapping[str, np.ndarray], texts: list[str], *, model: str, dims: int, target_recall: float) -> dict[str, Any]` (line 984; internal)
- `register_suites(registry: dict[str, Any], *, role_tasks: dict[str, str] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1159) — Register B1/B3 on Phase 5a's harness (call from the composition root).
- `run_bench(vault: LoadedVault, *, request: BenchRequest, caps: SpendCaps, price_per_million: float | None=None, embedding_price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, embedding_clients: Mapping[str, Any] | None=None, writer_client: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1178)
- `plan_admission(vault: LoadedVault, plan: Mapping[str, Any], spend: ReviewSpend, *, writer_client: Any=None, embedding_price_per_million: float | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1257) — The whole plan's estimate on ``spend``'s routes (no client built, nothing sent).
- `b3_markdown_lines(results: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1326)
- `render_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1343) — The local runner's report (the harness renders through ``markdown_lines``).

### Module constants

- `HARNESS_CONTRACT` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 102)
- `B1_PROMPT_VERSION` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 103)
- `B1_WRITER_ROLE` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 106)
- `B1_WRITER_TASK` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 107)
- `B1_WRITER_PURPOSE` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 108)
- `ROLE_TASKS` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 110)
- `B1_K` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 112)
- `DEFAULT_MODELS` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 113)
- `B1_DEFAULT_DIMS` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 122)
- `DEFAULT_TARGET_RECALL` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 123)
- `EMBED_BATCH` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 124)
- `EMBEDDING_ROUTE` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 125)
- `EMBEDDING_PRICES_PER_MILLION` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 128)
- `B1_DEFAULT_WRITER_OUTPUT_TOKENS` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 135)
- `WRITER_SETTING_KEYS` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 138)
- `MIN_CONFIRMED_FOR_RECOMMENDATION` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 142)
- `_TOKEN` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 143)
- `SUITES` ([src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1156)

### Explicit exports

`__all__` declares:

- `B1_DEFAULT_WRITER_OUTPUT_TOKENS`
- `B1_WRITER_ROLE`
- `B1Suite`
- `B3Suite`
- `BenchContext`
- `BenchRequest`
- `SUITES`
- `VectorCache`
- `b1_markdown_lines`
- `b3_markdown_lines`
- `blocking_cutoff`
- `configured_writer`
- `load_eedi`
- `plan_admission`
- `rank_metrics`
- `register_suites`
- `requested_dims`
- `requested_writer_output_tokens`
- `roc_auc`
- `run_bench`
- `writer_identity`
- `writer_tokens`

## Internal implementation anchors

- `_complete(ctx: Any, role: str, prompt: str, result_model: type[WireModel], purpose: str, prompt_version: str, output_tokens: int) -> tuple[Any, str | None]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 312) — Through the local context, or Phase 5a's PF caller (``ctx.role`` + ``ctx.caller.call``).
- `_settings_view(profile: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 354)
- `_client_settings(client: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 362) — An injected or resolved client's generation settings (its profile or config).
- `_run_writer(ctx: Any, output_tokens: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 402) — The writer identity of the client this run actually calls.
- `_tokens(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 458)
- `_rank_of(scores: np.ndarray, gold: int) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 489) — 1-based rank of ``gold``; ties broken by index (deterministic).
- `_ranks_from_order(scores: np.ndarray) -> np.ndarray` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 496)
- `_matrix(vectors: Mapping[str, np.ndarray], texts: Sequence[str], dims: int) -> np.ndarray` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 503)
- `_centred(matrix: np.ndarray) -> np.ndarray` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 509)
- `_read_manifest(directory: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 561)
- `_episode_labels(build: Any, *, exclude_nominations: Sequence[str]=(), only_nominations: Sequence[str]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 892) — One effective verdict per episode pair (highest authority; a tie is ``different``), over the labels of the chosen nominations.
- `_in_scope(by_id: Mapping[str, Any], pair: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1068)
- `_judge_load(subjects: Sequence[Any], score: Callable[[str, str], float], top_k: int, cutoff: float | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1074) — Judge calls the live rule would make over the whole history.
- `_config_lines(provenance: Mapping[str, Any], cutoff: float | None, top_k: int | None) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1091) — The [recurrence] lines; a cutoff always carries what it was measured on.
- `_merge_replay(build: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py), line 1107) — Merge precision/recall when the union is replayed from a subset of sources (P6).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `register_suites`; statically calls `register_suites`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `record_model_calls`; calls `content_key`, `generation_limit`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `DEFAULT_OUTPUT_TOKENS`, `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `OpenAIEmbeddingProviderClient`; calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `route_profile`; calls `route_profile`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `estimate_tokens`, `sum_estimates`; calls `estimate_tokens`, `sum_estimates`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE`, `compatible`, `hypothesis_subjects`, `scope_of`; calls `compatible`, `hypothesis_subjects`, `scope_of`
- [[Reference/Modules/learnloop/matching/union|learnloop.matching.union]] — imports `UnionEdge`, `effective_verdicts`, `union_with_refusals`; calls `UnionEdge`, `effective_verdicts`, `union_with_refusals`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `AUTHORITY`, `NOMINATED_BY_CITATION`, `NOMINATED_BY_M1_LINK`, `NOMINATED_BY_SHORTLIST`, `compute_groups`; calls `compute_groups`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `csv`, `dataclasses`, `hashlib`, `json`, `math`, `os`, `pathlib`, `re`, `typing`
- Third party: `numpy`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recurrence_benchmarks.py](../../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_a_blank_hypothesis_is_never_checkpointed_and_a_fresh_run_asks_again`
  - `test_b1_and_b3_run_through_phase_5as_harness_contract`
  - `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  - `test_b1_dry_run_then_run_with_fakes`
  - `test_b1_fails_closed_on_an_unknown_embedding_price`
  - `test_b1_ignores_cache_rows_without_a_writer`
  - `test_b1_writer_output_budget_defaults_to_the_policy_budget_and_is_planned`
  - `test_b3_markdown_renders_its_table_on_the_harness`
  - `test_b3_measures_the_shortlist_only_on_labels_the_shortlist_did_not_select`
  - `test_b3_recommends_only_at_the_serving_width_with_its_provenance`
  - `test_b3_replays_the_vaults_labelled_pairs`
  - `test_malformed_writer_json_is_one_failed_case_under_tight_caps`
  - `test_metrics`
  - `test_suites_register_on_a_harness_registry`
  - `test_the_b1_dry_run_prices_a_metered_writer_with_its_tokens`
  - `test_the_eedi_loader_reads_the_kaggle_files_and_needs_a_manifest`
  - `test_the_openrouter_writer_carries_its_effort_and_budget_and_the_bill_is_the_headline`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_b1_local_runner_never_lets_the_transport_retry_a_truncated_writer`

## Modification guidance

- Change benchmarks policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/benchmarks.py](../../../../../../../src/learnloop/diagnosis/recurrence/benchmarks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
