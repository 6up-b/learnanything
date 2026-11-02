---
title: "learnloop.source_retrieval.fallback_space"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/fallback_space.py"
source_paths:
  - "src/learnloop/source_retrieval/fallback_space.py"
source_commit: "944cae2748d7f9d5a4a085f398084586615b50fa"
source_commit_timestamp: "2026-10-24T20:56:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.fallback_space module"
  - "src/learnloop/source_retrieval/fallback_space.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.fallback_space`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.fallback_space` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The hosted Voyage fallback space (spec_local_contextual_retrieval_v1 §8; P1b).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py) |
| Source lines | 465 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `944cae2748d7f9d5a4a085f398084586615b50fa` |
| Commit timestamp | `2026-10-24T20:56:30-04:00` |

## Public API

- `token_upper_bound(text: str) -> int` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 78) — UTF-8 bytes plus a special-token allowance: no tokenizer emits more (E0's bound).
- `fallback_reason(config: LearnLoopConfig) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 84) — None when the fallback space may be used, else why not (nothing sent).
- `fallback_space(config: LearnLoopConfig) -> tuple[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 102) — ``(space_id, pins)`` of the configured fallback profile (grouped windows).
- `fallback_client(vault: LoadedVault) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 113) — The fallback space's client, or ``(None, why not)``; nothing is sent here.
- `window_vectors(connection, space_id: str, extraction_id: str, keys: Mapping[str, Sequence[tuple[str, int]]]) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 136) — ``{span_id: vector}`` for the blocks whose every key is stored (a split block's parts are averaged, weighted by their tokens: ``split_mean``); a block missing any part is left out.
- `backfill_caps(config: LearnLoopConfig, batches: Sequence[Sequence[Window]]) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 178)
- `run_budget(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str], *, cancelled: Callable[[], bool] | None=None) -> SpendBudget` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 197) — ONE budget for a backfill run over many sources (Codex review F3): its calls and tokens are the run's whole plan, its dollars the per-run cap (``embedding.fallback.max_cost_usd_per_run``, keep), so a command over many sources never spends more than one run's cap.
- `backfill_fallback_run(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str], *, client: Any | None=None, cancelled: Callable[[], bool] | None=None, dry_run: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 210) — Backfill several sources under one run budget; the aggregate estimate and charge.
- `backfill_fallback_vectors(vault: LoadedVault, repository: Repository, extraction_id: str, *, client: Any | None=None, cancelled: Callable[[], bool] | None=None, dry_run: bool=False, budget: SpendBudget | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 231) — Embed the windows of ``extraction_id`` the fallback space lacks (aggregate report only).
- `plan_query(vault: LoadedVault, repository: Repository, texts: Mapping[str, str], *, unknown: int=0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 341) — The dry run of :func:`query_vectors` at its worst case (Codex review F2): whether the fallback space may be queried for this search, and the one request's token and dollar bound.
- `query_vectors(vault: LoadedVault, repository: Repository, texts: Mapping[str, str], *, client: Any | None, owner_id: str='', deadline: float | None=None, budget: SpendBudget | None=None) -> tuple[dict[str, np.ndarray], dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 369) — Query vectors in the fallback space (cached by text; one capped, paid request for the rest).
- `coverage(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str], windows_for: Callable[[str], Sequence[Window]]) -> dict[str, dict[str, np.ndarray]]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 431) — ``{extraction_id: {span_id: vector}}`` for the extractions every block of which the fallback space covers under the current windows (others left out).

### Module constants

- `NAME` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 67)
- `QUERY_RECORD_KIND` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 68)
- `QUERY_TASK_PREFIX` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 69)
- `FALLBACK_JOB` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 71)
- `MAX_WINDOWS_PER_REQUEST` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 73)
- `MAX_RETRIES` ([src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 75)

### Explicit exports

`__all__` declares:

- `FALLBACK_JOB`
- `NAME`
- `backfill_caps`
- `backfill_fallback_run`
- `backfill_fallback_vectors`
- `coverage`
- `fallback_client`
- `fallback_reason`
- `fallback_space`
- `plan_query`
- `query_vectors`
- `run_budget`
- `window_vectors`

## Internal implementation anchors

- `_batches(windows: Sequence[Window]) -> list[list[Window]]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 160)
- `_missing(vault: LoadedVault, repository: Repository, space: str, extraction_id: str) -> tuple[list[Window], list[Window]]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 186) — ``(windows, the windows the fallback space lacks)`` under the current policy.
- `_query_hash(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 319)
- `_query_text(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 325)
- `_cached_queries(repository: Repository, space: str, wanted: Mapping[str, str]) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/source_retrieval/fallback_space.py), line 329)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `backfill_fallback_run`; statically calls `backfill_fallback_run`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `FALLBACK_JOB`, `backfill_fallback_vectors`, `fallback_reason`; statically calls `backfill_fallback_vectors`, `fallback_reason`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `plan_query`; statically calls `plan_query`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `coverage`, `fallback_reason`; statically calls `coverage`, `fallback_reason`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `module`; statically calls `fallback_client`, `fallback_reason`, `fallback_space`, `query_vectors`, `window_vectors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `make_ai_provider_client_from_profile`; calls `make_ai_provider_client_from_profile`
- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `embedding_request_timeout`; calls `embedding_request_timeout`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `MAX_CHUNKS_PER_REQUEST`, `MAX_INPUTS_PER_REQUEST`, `MAX_TOKENS_PER_REQUEST`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `check_ai_runtime`; calls `check_ai_runtime`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`, `VOYAGE_CONTEXTUAL_PROFILE_TYPE`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `put_vector`; calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `has_tables`, `register_space`; calls `has_tables`, `register_space`
- [[Reference/Modules/learnloop/local_embeddings/identity|learnloop.local_embeddings.identity]] — imports `hosted_space_pins`, `space_id`; calls `hosted_space_pins`, `space_id`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `LARGEST_QUERY_TEXT`, `QUERY_EMBEDDING_CAPS`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `block_record_id`; calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `WINDOW_RULE`, `Window`, `expected_keys`, `extraction_windows`, `mean_vector`, `window_key`; calls `expected_keys`, `extraction_windows`, `mean_vector`, `window_key`
- [[Reference/Modules/learnloop/text_canon|learnloop.text_canon]] — imports `collapse_whitespace`; calls `collapse_whitespace`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_the_tutor_records_as_delivered_only_the_spans_it_was_given`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_challenger_learns_its_way_up_from_resolver_receipts`
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_a_failed_query_hands_its_sources_to_an_available_fallback`
  - `test_a_successor_space_never_inherits_its_predecessors_weights`
  - `test_an_unknown_rewrite_is_planned_at_its_largest_encoding_and_never_found_cached`
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`
  - `test_the_fallback_serves_a_source_qwen_does_not_cover`
  - `test_the_logged_selection_probability_is_the_resolvers_joint_one`
  - `test_the_seed_serves_while_the_learned_rule_is_only_logged`
  - `test_with_the_default_at_qwen_the_fallback_changes_nothing_served`
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_nothing_is_sent_while_a_switch_is_off`
  - `test_one_command_is_one_run_under_the_per_run_cap`
  - `test_the_backfill_is_capped_receipted_and_window_keyed`
  - `test_the_hosted_space_is_registered_when_its_first_vectors_land`
  - `test_the_run_cap_stops_the_spend`

## Modification guidance

- Make changes here when the responsibility remains fallback space within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/fallback_space.py](../../../../../../src/learnloop/source_retrieval/fallback_space.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
