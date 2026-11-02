---
title: "learnloop.experiments.contextual_embeddings.system_arms"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/system_arms.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/system_arms.py"
source_commit: "92128ec6c8e9918f87386988c7330d4aca7c6440"
source_commit_timestamp: "2026-10-23T20:51:39-04:00"
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
  - "learnloop.experiments.contextual_embeddings.system_arms module"
  - "src/learnloop/experiments/contextual_embeddings/system_arms.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.system_arms`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.system_arms` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's named system arms on separate service copies (spec §5.4: R0, R1, R1').

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py) |
| Source lines | 911 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `92128ec6c8e9918f87386988c7330d4aca7c6440` |
| Commit timestamp | `2026-10-23T20:51:39-04:00` |

## Public API

- `class ProtectedTextRefused(E0BudgetExceeded)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 114) — A request would have carried protected text; nothing was sent.
- `make_service_copy(frozen_root: Path, destination: Path) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 118) — A backup-API copy of a frozen copy, for the system arms.
- `enable_embeddings_on_copy(root: Path) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 136) — Set ``ai.routing.embedding``, the ``[ai.providers.openrouter_embedding]`` profile and ``[embedding] enabled/backfill_enabled`` in a service copy's ``learnloop.toml`` (never a tracked vault: the path must be under fixtures-local).
- `route_source_llm_on_copy(root: Path) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 165) — Route a SERVICE copy's production source routes (``pins.SYSTEM_ARM_ROUTES``: source_rerank, source_query_rewrite, source_compare) to the experiment's OpenRouter profile for Claude Haiku 5.5 (re-plan 2026-10-22: E0 makes no Codex call), in the copy's ``learnloop.toml`` only (neve…
- `redact_service_copy(handle: Any, policy: PolicySnapshot) -> dict[str, int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 203) — Blank every withheld block's text in a SERVICE copy's database (never the frozen copy: the path must be under fixtures-local).
- `class ProtectedTextGuard` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 229) — An embedding client wrapper that refuses any batch carrying protected text.
  - `__init__(self, client: Any, probes: Sequence[str]) -> None` (line 236; internal)
  - `__getattr__(self, name: str) -> Any` (line 246; internal)
  - `carries_protected(self, text: str) -> bool` (line 249; public)
  - `embed(self, inputs: list[Any], task_prefix: str) -> Any` (line 257; public)
- `probe_plan(snapshot: CorpusSnapshot) -> tuple[list[str], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 308) — The guard's probes and their counts (relabel round, 2026-10-23).
- `protected_probes(snapshot: CorpusSnapshot) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 355) — The guard's probes (:func:`probe_plan`).
- `guarded_factory(factory: Callable[[], Any], snapshot: CorpusSnapshot) -> Callable[[], Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 361)
- `class SystemRequestGate` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 369) — Admits every physical request a production path makes on a service copy through the E0 ledger, once, billed by the RESOLVED client.
  - `__init__(self, ledger: E0Ledger, config: Any, *, arm: str) -> None` (line 390; internal)
  - `_admit_embedding(self, client: Any, prompt: Any) -> Any` (line 395; internal)
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 414; public)
  - `settle(self, admission: Any, usage: Mapping[str, Any]) -> None` (line 439; public)
- `observe_compare_searches() -> Iterator[list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 514) — Record every per-source ``search_spans`` a production comparison (``learnloop.source_retrieval.compare``) runs in this context.
- `rank_system(handle: Any, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], *, arm: str, ledger: E0Ledger, query_text: Mapping[str, str], clients: Mapping[str, Any] | None=None) -> tuple[dict[str, list[str]], dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 591) — ``{query_id: unit ids}`` for one system arm, and its report (pages, duplicates, verification, pool modes, dense use, dropped hits, missing).
- `withheld_records(handle: Any, extraction_id: str, policy: PolicySnapshot) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 709) — How many of the backfill's planned records for ``extraction_id`` are blocks the policy withholds (zero on a redacted copy: a blank block is not embeddable).
- `backfill_service_copy(handle: Any, ledger: E0Ledger, *, client_factory: Any=None, policy: PolicySnapshot | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 724) — The production source backfill on a REDACTED service copy, under the E0 ledger.
- `dense_coverage_complete(handle: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 794) — Whether every embeddable (permitted) block of every current extraction of the service copy has a vector: the condition for a fully covered arm.
- `open_service(root: Path) -> Any` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 806) — A service copy opened writable through the vault's own repository (production search writes its receipts there; never the frozen copy).
- `prepare_service_copies(frozen_root: Path, service_root: Path, ledger: E0Ledger, *, snapshot: CorpusSnapshot, client_factory: Callable[[], Any] | None=None, factory_for_config: Callable[[Any], Callable[[], Any]] | None=None, backfill: bool=True) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 876) — ``{"R0": handle, "R1_service": handle}`` and the preparation report (per copy: prepared or reopened, the redaction, the backfill reports and the dense coverage).

### Module constants

- `SYSTEM_ARMS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 101)
- `DENSE_ARMS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 108)
- `SERVICE_STATE` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 109)
- `GUARD_PROBE_CHARS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 111)
- `ENABLE_EMBEDDINGS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 128)
- `EMBEDDING_CONTRACT_ERRORS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 281)
- `BACKFILL_EXTRA_PASSES` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 293)
- `BACKFILL_REPORT_KEYS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 297)
- `GUARD_PROBE_STEP` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 303)
- `GUARD_MIN_CHARS` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 305)
- `COMPARISON_DONE` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 480)
- `_COMPARE_SEARCHES` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 508)
- `_OBSERVER_LOCK` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 509)
- `_OBSERVER` ([src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 510)

## Internal implementation anchors

- `_normalize(text: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 225)
- `class _SystemAdmission` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 452)
- `_keys(hits: Sequence[Any]) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 465)
- `_bump(counter: dict[str, int], key: str, amount: int=1) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 475)
- `_dense_ran(search: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 483) — Whether one production search actually ranked by meaning over a complete dense index: a ``meaning`` list AND dense status ``ready`` (``SpanSearch.describe()``'s ``lists`` and ``dense``).
- `_search_record(search: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 496) — What a per-source comparison search did (no text): lists, dense status and coverage, query vectors, hits.
- `_comparison_outcome(result: Any, searches: Sequence[Mapping[str, Any]] | None=None) -> tuple[str, str | None, bool]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 556) — ``(verification label, missing reason or None, dense used)`` for a delegated comparison (Codex re-review F20).
- `_current(handle: Any) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 788)
- `_write_state(path: Path, state: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 831)
- `_read_state(path: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 837)
- `_identity(frozen_root: Path, snapshot: CorpusSnapshot) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 844)
- `_prepare_one(frozen_root: Path, root: Path, name: str, snapshot: CorpusSnapshot, identity: Mapping[str, Any], state: dict[str, Any], state_path: Path, *, enable: bool) -> tuple[Any, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py), line 851) — One service copy, reopened when its completed preparation matches.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `prepare_service_copies`; statically calls `prepare_service_copies`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `DENSE_ARMS`, `SYSTEM_ARMS`, `rank_system`; statically calls `rank_system`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `gate_model_requests`; calls `gate_model_requests`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `copy_tree_with_databases`; calls `copy_tree_with_databases`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `quiet_provider_logs`; calls `quiet_provider_logs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0BudgetExceeded`, `E0Ledger`, `E0PriceUnverified`, `E0ProviderFailure`, `Request`, `reconciled_usd`; calls `E0BudgetExceeded`, `E0PriceUnverified`, `E0ProviderFailure`, `Request`, `reconciled_usd`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `estimate_input_tokens`, `role_cost`; calls `estimate_input_tokens`, `role_cost`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CopyHandle`, `CorpusSnapshot`, `PolicySnapshot`, `_inside_local_root`, `contained_database`, `contained_root`; calls `CopyHandle`, `_inside_local_root`, `contained_database`, `contained_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `qwen_factory`; calls `qwen_factory`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `latency_summary`; calls `latency_summary`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `price_problem`, `token_upper_bound`, `verified_role_for_model`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `units_from_blocks`; calls `units_from_blocks`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `tree_digest`; calls `tree_digest`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`, `library_scope`; calls `current_extractions`, `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `INTENTS`, `find_sources`; calls `find_sources`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `split_record_id`; calls `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `backfill_source_vectors`, `source_block_records`, `source_coverage`, `target_extraction`; calls `backfill_source_vectors`, `source_block_records`, `source_coverage`, `target_extraction`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `tutor_pool`; calls `tutor_pool`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `verify_spans`; calls `verify_spans`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `json`, `os`, `pathlib`, `threading`, `time`, `typing`
- Third party: `tomlkit`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_permitted_block_containing_a_withheld_blocks_text_is_embedded`
  - `test_an_unredacted_service_copy_is_refused_before_any_request`
  - `test_the_guard_still_refuses_withheld_text_even_past_its_first_characters`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f11_an_interrupted_service_copy_is_set_aside_and_prepared_again`
  - `test_f12_system_arms_use_find_sources_and_an_unverified_intent_is_no_ranking`
  - `test_f1_service_copy_preparation_never_sends_protected_text`
  - `test_f1_the_guard_refuses_a_batch_carrying_protected_text`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f19_a_qwen_arm_charges_embeddings_and_verification_once_each`
  - `test_f19_successful_production_verification_charges_once_per_physical_request`
  - `test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding`
  - `test_f20_a_failed_delegated_comparison_is_missing_not_ranked`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f20_the_comparison_outcome_needs_every_counted_source_search_dense`
  - `test_f20_the_search_observer_is_scoped_and_removed`
  - `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h1_a_service_copy_naming_an_outside_database_is_refused_before_any_open`
  - `test_h4_the_qwen_identity_is_in_cache_keys_and_receipts_and_the_service_gate`
  - `test_m9_the_qwen_route_is_canaried_before_its_service_backfill`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_the_service_copies_route_their_source_routes_to_openrouter_haiku`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_m1_no_e0_vault_load_reads_settings_env_or_a_copy_dotenv`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_refused_backfill_batch_is_reported_safely_and_sent_once_more`
  - `test_the_contract_error_reasons_are_the_production_clients_fixed_messages`

## Modification guidance

- Make changes here when the responsibility remains system arms within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/system_arms.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/system_arms.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
