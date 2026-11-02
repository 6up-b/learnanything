---
title: "learnloop.ops.embedding_compare"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/embedding_compare.py"
source_paths:
  - "src/learnloop/ops/embedding_compare.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
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
  - "learnloop.ops.embedding_compare module"
  - "src/learnloop/ops/embedding_compare.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.embedding_compare`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.embedding_compare` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: `learnloop embeddings compare`: the shared benchmark harness (Slice 2 §4, §5.5, §5.6).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py) |
| Source lines | 899 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `va_trace_bytes(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 81) — A trace in the grading prompt is bounded by the writer's output (bytes upper-bound tokens).
- `class CompareRequest` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 91)
- `tier_routes(vault: LoadedVault, tier: str | None) -> list[str] | None` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 114)
- `class CompareContext` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 125)
  - `__init__(self, vault: LoadedVault, caller: PFCaller, *, clients: Mapping[str, Any] | None, embedding_clients: Mapping[str, Any] | None, embedding_price: float | None, output_dir: Path, tier: str | None=None) -> None` (line 126; internal)
  - `role(self, name: str) -> list[RoleClient]` (line 140; public)
  - `embedder(self, model: str, dims: int) -> Any` (line 146; public)
  - `price_for(self, model: str) -> float | None` (line 155; public)
  - `embedding_config(self, model: str) -> dict[str, Any]` (line 158; public) — What besides model, width and prefix identifies the vectors (cache key).
  - `vectors(self, model: str, texts: list[str], *, dims: int, task_prefix: str='similarity') -> dict[str, np.ndarray]` (line 168; public) — Unit vectors of width ``dims`` by text, embedding only uncached texts.
- `class VectorCache` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 208) — Content-addressed float32 unit vectors in the output directory, not the vault.
  - `__init__(self, root: Path, model: str, task_prefix: str, *, dims: int, config: Mapping[str, Any] | None=None) -> None` (line 215; internal)
  - `key(text: str) -> str` (line 235; public)
  - `get(self, text: str) -> np.ndarray | None` (line 238; public)
  - `put_many(self, texts: list[str], vectors: list[list[float]]) -> None` (line 242; public)
- `roc_auc(scores: list[float], labels: list[bool]) -> float | None` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 264)
- `blocking_cutoff(scores: list[float], labels: list[bool], target_recall: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 273) — The highest cutoff whose recall on positives reaches the target (R4).
- `binary_metrics(predictions: list[bool | None], labels: list[bool]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 288) — Confusion counts and rates; a ``None`` prediction is an abstention.
- `judge_prediction(verdict: str) -> bool | None` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 311) — A freshness verdict as a duplicate prediction; no verdict is an abstention (``None``).
- `centered_cosines(pairs: list[tuple[np.ndarray, np.ndarray]], dims: int) -> list[float]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 318) — Mean-centered cosine on MRL-truncated vectors, as retrieval scores them.
- `class CompareSuite(Protocol)` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 339)
  - `load(self, vault: LoadedVault, request: CompareRequest) -> Any` (line 343; public)
  - `plan(self, vault: LoadedVault, data: Any, request: CompareRequest) -> dict[str, Any]` (line 345; public)
  - `run(self, data: Any, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]` (line 347; public)
- `class B2Case` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 365)
- `class B2Data` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 375)
- `b2_case_identity(revision: str, case: B2Case) -> str` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 388) — A tier- and model-independent identity for one labelled pair.
- `class B2Suite` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 399)
  - `load(self, vault: LoadedVault, request: CompareRequest) -> B2Data` (line 404; public)
  - `_skeleton_texts(self, data: B2Data) -> list[str]` (line 437; internal)
  - `plan(self, vault: LoadedVault, data: B2Data, request: CompareRequest) -> dict[str, Any]` (line 441; public)
  - `run(self, data: B2Data, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]` (line 466; public)
- `class VAItem` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 564)
- `class VAData` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 572)
- `class ValidAlternativeSuite` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 577)
  - `load(self, vault: LoadedVault, request: CompareRequest) -> VAData` (line 582; public)
  - `plan(self, vault: LoadedVault, data: VAData, request: CompareRequest) -> dict[str, Any]` (line 593; public) — Calls and input-plus-output tokens per role, from the actual prompts (no request).
  - `run(self, data: VAData, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]` (line 617; public)
- `run_compare(vault: LoadedVault, *, request: CompareRequest, caps: SpendCaps, price_per_million: float | None=None, embedding_price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, clients: Mapping[str, Any] | None=None, embedding_clients: Mapping[str, Any] | None=None, input_price_per_million: float | None=None, output_price_per_million: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 695) — Plan (or run) one registered suite and write an aggregate report.
- `spend_lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 822) — The bill first, then cap accounting (owner batch 2: in the owner's B1 run "charged" overstated the provider's bill about 17x).

### Module constants

- `HARNESS_VERSION` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 73)
- `DEFAULT_TARGET_RECALL` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 74)
- `EMBED_BATCH` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 75)
- `EMBEDDING_PRICES_PER_MILLION` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 85)
- `B2_CASE_IDENTITY_VERSION` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 385)
- `SUITES` ([src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py), line 692)

### Explicit exports

`__all__` declares:

- `B2Suite`
- `B2_CASE_IDENTITY_VERSION`
- `CompareContext`
- `CompareRequest`
- `CompareSuite`
- `HARNESS_VERSION`
- `SUITES`
- `ValidAlternativeSuite`
- `VectorCache`
- `b2_case_identity`
- `binary_metrics`
- `blocking_cutoff`
- `centered_cosines`
- `judge_prediction`
- `roc_auc`
- `run_compare`
- `spend_lines`

## Internal implementation anchors

- `_embedding_client(vault: LoadedVault, model: str, dims: int) -> Any` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 196)
- `_read_manifest(directory: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 350)
- `_count(values) -> dict[str, int]` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 556)
- `_usd(value: Any) -> str` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 818)
- `_markdown(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/ops/embedding_compare.py), line 860)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `CompareRequest`, `SUITES`, `run_compare`; statically calls `CompareRequest`, `run_compare`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `judge_prediction`; statically calls `judge_prediction`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `EMBED_BATCH`, `VectorCache`; statically calls `VectorCache`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `OpenAIEmbeddingProviderClient`; calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BLIND_GRADING_PROMPT_VERSION`, `BlindGradingProposal`, `blind_grading_context`, `blind_grading_prompt`; calls `blind_grading_context`, `blind_grading_prompt`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `module`; calls `equivalence_prompt`, `freshness_prompt`, `skeleton_prompt`, `valid_alternative_prompt`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`; calls `equivalence_confirmations`, `run_equivalence_checks`, `sandbox_available`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `estimate_tokens`, `planned_role_clients`, `pricing_basis`, `resolve_role_clients`, `validate_pricing`; calls `PFCaller`, `PFUnavailable`, `estimate_tokens`, `planned_role_clients`, `pricing_basis`, `resolve_role_clients`, `validate_pricing`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `final_answer_text`, `fingerprint_keys`, `shared_keys`; calls `final_answer_text`, `fingerprint_keys`, `shared_keys`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `os`, `pathlib`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]], [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_embedding_compare.py](../../../../../../tests/test_embedding_compare.py) — direct import
  - `test_a_larger_dimension_sweep_never_reuses_narrower_cached_vectors`
  - `test_b2_dry_run_sends_nothing_and_writes_nothing`
  - `test_b2_reports_views_and_recall_oriented_cutoffs_and_caches_vectors`
  - `test_b2_requires_licensed_manifest_and_known_prices`
  - `test_compare_dry_runs_estimate_cost_and_admit_the_whole_plan`
  - `test_metric_helpers`
  - `test_valid_alternative_suite_is_cas_checked_and_graded_learner_blind`
  - `test_valid_alternative_suite_rejects_a_degenerate_equivalence_check`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_the_compare_harness_uses_the_policy_budget_and_retries_a_truncation`
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — direct import
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  - `test_b3_markdown_renders_its_table_on_the_harness`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_every_logged_learner_question_is_included`
  - `test_the_report_runs_the_production_verification_by_query_type`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_b4_compares_page_images_with_text_chunks_and_decides_conservatively`
  - `test_missing_labels_are_asked_again_then_left_as_abstentions`
  - `test_register_suites_is_idempotent_and_refuses_a_conflict`
  - `test_source_retrieval_dry_run_plans_every_paid_step_and_writes_nothing`
  - `test_source_retrieval_report_compares_against_todays_substring_search`
  - `test_without_a_backfill_the_dense_system_is_reported_unavailable`
- [tests/test_t6_followup_rereview.py](../../../../../../tests/test_t6_followup_rereview.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_failed_verification_is_never_scored_and_blocks_its_verdicts`
  - `test_insufficient_candidate_caps_fail_at_the_dry_run`
  - `test_the_report_verifies_the_tutors_own_pool_with_its_item_in_context`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains embedding compare within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/embedding_compare.py](../../../../../../src/learnloop/ops/embedding_compare.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
