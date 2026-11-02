---
title: "learnloop.experiments.contextual_embeddings.live"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/live.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/live.py"
source_commit: "a8f8b4917df76d513a0a2ba027f393a451d8a434"
source_commit_timestamp: "2026-10-23T21:01:53-04:00"
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
  - "learnloop.experiments.contextual_embeddings.live module"
  - "src/learnloop/experiments/contextual_embeddings/live.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.live`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.live` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: The paid E0 run's live wiring (never executed in the harness stage).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/live.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py) |
| Source lines | 270 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a8f8b4917df76d513a0a2ba027f393a451d8a434` |
| Commit timestamp | `2026-10-23T21:01:53-04:00` |

## Public API

- `class PlanMismatch(ValueError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 45) — The copies no longer rebuild to the frozen plan; nothing was spent.
- `qwen_factory(config: Any) -> Callable[[], Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 49) — The production OpenRouter embedding client for the copy's embedding route.
- `class LiveFactories` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 63) — Where the paid run's clients come from (real by default).
- `default_factories() -> LiveFactories` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 79)
- `rebuild_frozen(copies: Sequence[Path], plan: Mapping[str, Any]) -> tuple[list[Any], list[Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 85) — The copies' handles and snapshots rebuilt under the plan's own split and strata, refused unless their identity is the plan's.
- `reused_store(run_dir: Path, plan: Mapping[str, Any], snapshots: Sequence[Any], reuse_run: str) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 134) — The earlier run directory whose stores a plan reuses (relabel round).
- `run_live(copies: Sequence[Path], *, plan: Mapping[str, Any], run_dir: Path, key_envs: Mapping[str, str], reader_latency_budget_s: float | None=None, factories: LiveFactories | None=None, bind_receipts: Callable[[Any], None] | None=None, new_authorization: str | None=None, reuse_run: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 160) — The paid run (see the module docstring).

## Internal implementation anchors

- `_failure_outcome(plan: Mapping[str, Any], handle: Any, ledger: E0Ledger, exc: BaseException, preparation: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 109) — The aggregate failure report of a copy whose run stopped on an unexpected failure (fix round 4, Medium 12): its classification only (never the exception's text), the ledger, and every planned item as missing.
- `_write_outcome(vault_dir: Path, outcome: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py), line 126)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `run_live`; statically calls `run_live`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `PlanMismatch`; statically calls `PlanMismatch`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `qwen_factory`; statically calls `qwen_factory`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `OpenAIEmbeddingProviderClient`; calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_EMBEDDING_PROVIDER`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `Receipts`, `UrllibTransport`, `VectorStore`; calls `Receipts`, `UrllibTransport`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `logged_questions`; calls `logged_questions`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `classify`, `quiet_provider_logs`, `require_codex_lockdown`, `require_no_codex_roles`, `safe_message`; calls `classify`, `quiet_provider_logs`, `require_codex_lockdown`, `require_no_codex_roles`, `safe_message`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Ledger`, `authorized_ledger`; calls `authorized_ledger`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `Checkpoints`, `LiveRoleCaller`, `canary_models`; calls `Checkpoints`, `LiveRoleCaller`, `canary_models`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `_inside_local_root`, `build_snapshot`, `open_copy`; calls `_inside_local_root`, `build_snapshot`, `open_copy`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `PaidState`, `run_contracts`, `run_paid`; calls `PaidState`, `run_contracts`, `run_paid`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `ExperimentRecords`; calls `ExperimentRecords`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `assert_aggregate`, `render`; calls `assert_aggregate`, `render`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `freeze`, `plan_identity`; calls `freeze`, `plan_identity`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/stop_rules|learnloop.experiments.contextual_embeddings.stop_rules]] — imports `incomplete_rules`; calls `incomplete_rules`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `prepare_service_copies`; calls `prepare_service_copies`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results`
  - `test_a_reused_run_with_other_candidate_maps_is_refused_before_anything_is_sealed`
  - `test_the_paid_cli_passes_reuse_run_and_authorizes_on_the_cumulative_budget`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes`
  - `test_f5_the_paid_run_executes_the_frozen_split_or_refuses`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h3_two_paid_runs_with_different_run_directories_share_one_budget`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m12_an_unexpected_failure_still_writes_the_aggregate_report`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_paid_cli_refuses_when_the_lockdown_is_not_in_force`
  - `test_the_paid_run_refuses_when_the_lockdown_is_not_importable`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_l7_the_paid_run_refuses_a_run_directory_outside_fixtures_local`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains live within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/live.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/live.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
