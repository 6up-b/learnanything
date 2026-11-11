---
title: "learnloop.experiments.contextual_embeddings.plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/plan.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/plan.py"
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
  - "learnloop.experiments.contextual_embeddings.plan module"
  - "src/learnloop/experiments/contextual_embeddings/plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.plan` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's frozen run plan and its cost estimate (spec §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py) |
| Source lines | 493 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `embedding_arm_estimate(arm: str, snapshots: Sequence[CorpusSnapshot], query_tokens: Sequence[int]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 96)
- `llm_estimates(snapshots: Sequence[CorpusSnapshot], seeds: Mapping[str, Sequence[Seed]], questions: Mapping[str, Mapping[str, int]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 167) — The paid LLM roles.
- `system_arm_estimates(snapshots: Sequence[CorpusSnapshot], config_allowlists: Mapping[str, Mapping[str, Any]], query_counts: Mapping[str, int]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 264) — R0 (today's effective path) and R1_service (find_sources on a copy with Qwen enabled and backfilled): what they would spend.
- `system_llm_rows(vault: str, allowlist: Mapping[str, Any], queries: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 305) — The system arms' production source-route requests (verification, rewrite, comparison) on the service copies, re-routed from Codex to OpenRouter's Claude Haiku 5.5 (re-plan 2026-10-22): an UPPER-BOUND count per query (R0 and R1' ``find_sources``: two pages, each with its rewrite…
- `summarize(arms: Sequence[Mapping[str, Any]], systems: Sequence[Mapping[str, Any]], roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 333)
- `run_id(snapshots: Sequence[CorpusSnapshot], bank_ids: Sequence[str]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 357)
- `query_token_sizes(bank: Sequence[BankQuestion], development_target: int) -> list[int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 363)
- `subscription_requests(roles: Sequence[Mapping[str, Any]], systems: Sequence[Mapping[str, Any]], config_allowlists: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 369) — The planned Codex (subscription) requests (re-plan 2026-10-22: there are none).
- `reuse_estimate(predecessor_ledger: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 413) — The offline estimate of a relabel that reuses an earlier run (what the dry run cannot price from the inventory: most work is reused).
- `budget_check(estimate: Mapping[str, float], prior: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 475) — Whether ``estimate`` (``{category: usd}``) fits the CUMULATIVE cap and allocations after ``prior`` (``budget.prior_spend``: every other authorization's committed spend).

### Module constants

- `ASSUMPTIONS` ([src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 35)
- `EMBEDDING_ARMS` ([src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 67)
- `RELABEL_ROLES` ([src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 391)
- `REUSE_ASSUMPTIONS` ([src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 393)

## Internal implementation anchors

- `_sha(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 71)
- `_chunk_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 75)
- `_batches(documents: Sequence[Sequence[int]], pin: pins.EmbeddingPin) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 79) — Requests the adapter batching makes for documents of these chunk token sizes.
- `_role(role: str, calls: int, input_tokens: int, output_tokens: int, *, arm: str | None=None, detail: str='') -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 145) — One role's estimate.
- `_average_section_tokens(snapshot: CorpusSnapshot) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 247)
- `_average_source_tokens(snapshot: CorpusSnapshot) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py), line 257)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `ASSUMPTIONS`, `EMBEDDING_ARMS`, `budget_check`, `embedding_arm_estimate`, `llm_estimates`, `query_token_sizes`, `reuse_estimate`, `run_id`, `subscription_requests`, `summarize`, `system_arm_estimates`; statically calls `budget_check`, `embedding_arm_estimate`, `llm_estimates`, `query_token_sizes`, `reuse_estimate`, `run_id`, `subscription_requests`, `summarize`, `system_arm_estimates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `RELEVANCE_RUBRIC`, `Seed`, `writer_prompt`; calls `writer_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `SCHEMA_ALLOWANCE_TOKENS`, `role_cost`; calls `role_cost`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`, `token_estimate`; calls `pins_fingerprint`, `price_problem`, `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `context_prompt`, `recipe_text`; calls `context_prompt`, `recipe_text`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_reuse_estimate_reprices_every_label_request_at_todays_pins`

## Modification guidance

- Make changes here when the responsibility remains plan within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/plan.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
