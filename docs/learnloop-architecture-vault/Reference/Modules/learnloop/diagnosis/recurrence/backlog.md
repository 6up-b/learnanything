---
title: "learnloop.diagnosis.recurrence.backlog"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/backlog.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/backlog.py"
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
  - "learnloop.diagnosis.recurrence.backlog module"
  - "src/learnloop/diagnosis/recurrence/backlog.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.backlog`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.backlog` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: ``learnloop embeddings adjudicate --task same_cause --backlog`` (Slice 2 §3.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/backlog.py](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py) |
| Source lines | 280 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `route_profile(vault: LoadedVault, route: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 56) — A route's provider, model and billing from config alone (no client).
- `command_spend(vault: LoadedVault, caps: SpendCaps, *, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, embedding: bool=True) -> ReviewSpend` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 78) — One budget for the command; routes classified from config (dry-run safe).
- `plan_backlog(vault: LoadedVault, repository: Repository, *, spend: ReviewSpend, max_pairs: int | None=None, producer: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 116) — ``producer``: the judge model (an injected client's, else the configured route's).
- `run_backlog(vault: LoadedVault, repository: Repository, *, caps: SpendCaps, price_per_million: float | None=None, max_pairs: int | None=None, dry_run: bool=False, cancelled: Callable[[], bool] | None=None, judge_client: Any=None, embedding_client: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 196)

### Module constants

- `MODEL_CALL_OWNER_KIND` ([src/learnloop/diagnosis/recurrence/backlog.py](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 49)

### Explicit exports

`__all__` declares:

- `command_spend`
- `plan_backlog`
- `route_profile`
- `run_backlog`

## Internal implementation anchors

- `_missing_records(repository: Repository, model_id: str) -> list[Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py), line 103)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `run_backlog`; statically calls `run_backlog`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `route_profile`; statically calls `route_profile`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `command_spend`; statically calls `command_spend`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `route_profile`; statically calls `route_profile`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SUBSCRIPTION_PROFILE_TYPES`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`; calls `get_vector`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `configured_judge_model`; calls `configured_judge_model`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `EMBEDDING_ROUTE`, `EMBED_BATCH`, `default_judge_client`, `embed_on_spend`, `estimate_tokens`, `judge_executor`, `learner_state`, `plan_shortlist`, `producer_label`, `receipt_sink`; calls `default_judge_client`, `embed_on_spend`, `estimate_tokens`, `judge_executor`, `learner_state`, `plan_shortlist`, `producer_label`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE`, `SAME_CAUSE_ROUTE`, `hypothesis_subjects`; calls `hypothesis_subjects`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `TASK_PREFIX`, `hypothesis_records`; calls `hypothesis_records`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `default_embedding_client`; calls `default_embedding_client`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`; calls `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `refresh_recurrence_groups`; calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_output_budget.py](../../../../../../../tests/test_output_budget.py) — direct import
  - `test_the_same_cause_judge_is_no_longer_held_to_600_tokens`
- [tests/test_recurrence_benchmarks.py](../../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b3_replays_the_vaults_labelled_pairs`
- [tests/test_recurrence_commands.py](../../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_rebuild_makes_no_model_call_and_is_a_fixed_point`
  - `test_the_backlog_dry_run_plans_and_sends_nothing`
  - `test_the_backlog_judges_merges_and_reruns_idempotently`
  - `test_the_backlog_needs_embeddings`
  - `test_the_backlog_refuses_over_its_caps`
  - `test_the_cli_report_and_groups_commands`
  - `test_the_m3_report_reads_ledgers_only`
- [tests/test_recurrence_merge_composition.py](../../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_a_codex_route_that_is_not_ready_skips_the_judge_and_leaves_the_backlog`
  - `test_failing_codex_judge_calls_release_their_claims_and_leave_the_backlog`

## Modification guidance

- Change backlog policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/backlog.py](../../../../../../../src/learnloop/diagnosis/recurrence/backlog.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
