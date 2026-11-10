---
title: "learnloop.experiments.contextual_embeddings.paid"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/paid.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/paid.py"
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
  - "learnloop.experiments.contextual_embeddings.paid module"
  - "src/learnloop/experiments/contextual_embeddings/paid.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.paid`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.paid` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: The E0 paid run's steps (orchestrator-authorized, after review; never in this stage).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py) |
| Source lines | 687 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PaidState` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 117) — What a paid run has done (aggregates for the report, failures for the ledger).
  - `fail(self, item: str, kind: str, reason: str, denominator: Any=None) -> None` (line 127; public)
  - `missing(self, kind: str, count: int) -> None` (line 130; public)
  - `stop(self, step: str, exc: Exception) -> None` (line 134; public)
- `effective_query(question: BankQuestion, snapshot: CorpusSnapshot) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 158) — The complete query every arm encodes: the question's frozen context (``bank.freeze_context``), never an oracle location for a library question.
- `allowed_units(question: BankQuestion, snapshot: CorpusSnapshot) -> set[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 165)
- `make_adapter(arm: str, snapshot: CorpusSnapshot, *, ledger: E0Ledger, transport: Transport | None, receipts: Receipts, store: VectorStore, qwen_client_factory: Callable[[], Any] | None, key_envs: Mapping[str, str] | None=None, environ: Mapping[str, str] | None=None) -> EmbeddingAdapter` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 172)
- `run_contracts(snapshot: CorpusSnapshot, state: PaidState, **adapter_kwargs: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 191) — One public canary per embedding route, Qwen included, BEFORE any bulk work (the service backfill included: fix round 4, Medium 9): the document AND query contracts, their compatibility and the returned identity.
- `contracts_state(contracts: Mapping[str, Any]) -> PaidState` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 218) — A state carrying contracts already run (``run_live`` runs them before the service backfill), with their blocked arms.
- `rank_arm(arm: str, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], adapter: EmbeddingAdapter, *, headers: Mapping[str, str] | None=None, top: int=pins.POOL_DEPTH, indexes: dict[str, tuple[EmbeddingAdapter, SpaceVectors]] | None=None) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 231)
- `rank_bm25(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], headers: Mapping[str, str]) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 254)
- `label_all(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], rankings: Mapping[str, Mapping[str, Sequence[str]]], caller: Any, state: PaidState | None=None) -> dict[str, QuestionLabels]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 267) — Labels for every question, then the audits.
- `primary_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 326) — The prespecified selection slice: development, context-dependent/support strata.
- `slice_summaries(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 332) — Every slice reported apart with its own denominator (``total`` rows, ``scored`` per arm).
- `pick_finalists(summary: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 355) — On the primary development slice only: the best one-model (Qwen) arm and each hosted family's best arm, by Complete Evidence@10 (ties by arm name).
- `latency_check(answers: Sequence[ScoredAnswer], arm: str | None, incumbent: str | None, budget_s: float | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 391) — Whether ``arm`` meets the frozen deadline AND shows no paired p50/p95 regression against ``incumbent`` (within the pinned tolerance).
- `run_paid(snapshot: CorpusSnapshot, *, ledger: E0Ledger, caller: Any, run_dir: Path | None, transport: Transport | None=None, qwen_client_factory: Callable[[], Any] | None=None, logged: Sequence[BankQuestion]=(), strata: Mapping[str, int] | None=None, key_envs: Mapping[str, str] | None=None, environ: Mapping[str, str] | None=None, latency_budget_s: float | None=None, system_handles: Mapping[str, Any] | None=None, system_preparation: Mapping[str, Any] | None=None, system_clients: Mapping[str, Any] | None=None, contracts: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 418) — One vault copy's paid E0 run (see the module docstring).
- `snapshot_sqlite(snapshot: CorpusSnapshot) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 668)

### Module constants

- `QWEN_ARMS` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 104)
- `QUESTION_FAILURES` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 108)
- `HOSTED_FAMILIES` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 109)
- `NON_PRIMARY_STRATA` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 112)
- `DELIVERY_ARMS` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 113)
- `QWEN_ROUTE_ARMS` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 153)
- `CANARY_ARMS` ([src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 155)

## Internal implementation anchors

- `_time_up(state: PaidState, ledger: E0Ledger, step: str) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 139) — Stop cleanly at the run's wall-time bound (Codex review F14), and at once when the ledger is halted by an overage (fix round 4, High 2).
- `_online_retrieval(arm: str, question: BankQuestion, snapshot: CorpusSnapshot, source: BlockSource, indexes: Mapping[str, tuple[EmbeddingAdapter, SpaceVectors]], measured: Checkpoints) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 366) — One question's online retrieval-through-delivery time for a retrieval arm: a FRESH query embedding (never the cache), the exact search and the D1 delivery.
- `_answer_rows(answers: Sequence[ScoredAnswer], questions: Sequence[BankQuestion]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 675)
- `_paired_answers(rows: Sequence[Mapping[str, Any]], a: str, b: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py), line 684)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]] — imports `primary_rows`; statically calls `primary_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `QUESTION_FAILURES`, `effective_query`, `make_adapter`, `rank_arm`, `slice_summaries`; statically calls `effective_query`, `make_adapter`, `rank_arm`, `slice_summaries`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `NON_PRIMARY_STRATA`, `allowed_units`, `make_adapter`, `rank_arm`; statically calls `allowed_units`, `make_adapter`, `rank_arm`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `PaidState`, `run_contracts`, `run_paid`; statically calls `PaidState`, `run_contracts`, `run_paid`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `ADAPTERS`, `AdapterError`, `EmbeddingAdapter`, `PreparedQuery`, `QwenAdapter`, `Receipts`, `SpaceVectors`, `Transport`, `VectorStore`, `build_index`; calls `AdapterError`, `PreparedQuery`, `QwenAdapter`, `Receipts`, `VectorStore`, `build_index`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `ScoredAnswer`, `answer_and_judge`, `summarize_answers`; calls `answer_and_judge`, `summarize_answers`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `QuestionLabels`, `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `plan_seeds`, `pool_for`, `smoke_bank`, `stable_order`, `write_questions`; calls `accept_agreed`, `adjudicate`, `audit_plan`, `evidence_sets_from_labels`, `freeze_context`, `label_question`, `plan_seeds`, `pool_for`, `smoke_bank`, `stable_order`, `write_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Ledger`, `E0ProviderFailure`, `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `Checkpoints`; calls `Checkpoints`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `deliver`, `retrieved_d1`; calls `deliver`, `retrieved_d1`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `agreement`, `arm_summary`, `completion`, `paired`, `question_rows`; calls `agreement`, `arm_summary`, `completion`, `paired`, `question_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `latency_summary`, `paired_bootstrap`; calls `latency_summary`, `paired_bootstrap`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `BM25`, `documents_for`, `exact_search`, `generate_contexts`, `recipe_text`; calls `documents_for`, `exact_search`, `generate_contexts`, `recipe_text`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/stop_rules|learnloop.experiments.contextual_embeddings.stop_rules]] — imports `decide`; calls `decide`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `DENSE_ARMS`, `SYSTEM_ARMS`, `rank_system`; calls `rank_system`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockSource`; calls `BlockSource`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `pathlib`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
  - `test_resume_pays_only_for_what_is_missing`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f12_an_incompletely_covered_service_copy_blocks_the_qwen_system_arms`
  - `test_f14_a_run_past_its_wall_time_stops_cleanly_and_reports_incomplete`
  - `test_f16_finalists_come_from_the_primary_development_slice_only`
  - `test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator`
  - `test_f17_an_answer_stop_keeps_the_planned_denominator`
  - `test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs`
  - `test_f9_finalist_latency_includes_a_fresh_online_query_and_the_search`
  - `test_f9_latency_needs_the_deadline_and_no_paired_regression_against_the_incumbent`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f6_a_permitted_quote_is_still_delivered`
  - `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges`
  - `test_f6_delivery_refuses_a_protected_quote_even_from_an_unfrozen_selection`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once`
  - `test_h7_a_quote_without_complete_canonical_coverage_is_dropped`
  - `test_m12_a_provider_failure_records_incomplete_work_instead_of_aborting`
  - `test_m13_an_arm_that_fails_every_logged_question_stops_verdicts`
  - `test_m9_the_qwen_route_is_canaried_before_its_service_backfill`
- [tests/test_e0_review_round7.py](../../../../../../../tests/test_e0_review_round7.py) — direct import
  - `test_a_canary_failure_reaches_the_contracts_result_with_its_reason`
  - `test_the_three_perplexity_canaries_pass_against_the_documented_contract`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_non_item_failure_still_stops_the_labels`
  - `test_one_questions_unusable_labels_skip_that_question_only`

## Modification guidance

- Make changes here when the responsibility remains paid within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/paid.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/paid.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
