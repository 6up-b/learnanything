---
title: "learnloop.experiments.contextual_embeddings.runner"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/runner.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/runner.py"
source_commit: "91792831bdc8e9cad78ec4ac17ecb82fc599e87d"
source_commit_timestamp: "2026-10-23T21:11:25-04:00"
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
  - "learnloop.experiments.contextual_embeddings.runner module"
  - "src/learnloop/experiments/contextual_embeddings/runner.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.runner`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.runner` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0 execution: the dry run (this stage) and the paid run's frozen steps.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/runner.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py) |
| Source lines | 642 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `91792831bdc8e9cad78ec4ac17ecb82fc599e87d` |
| Commit timestamp | `2026-10-23T21:11:25-04:00` |

## Public API

- `class NetworkForbidden(RuntimeError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 55) — A network call was attempted where none is allowed.
- `network_guard() -> Iterator[_Guard]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 71) — Refuse every outbound connection and name lookup in this process.
- `tree_digest(root: Path) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 87) — Paths, sizes and content hashes of every file under ``root``.
- `config_allowlist(config: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 112) — The redacted effective-config allowlist (spec §5.1.2): embedding switches, model, route, dimensions, rewrite, pool, policy and caps.
- `dense_coverage(handle: CopyHandle) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 157) — Aggregate dense coverage (``source_vectors.source_coverage``), ids aliased.
- `split_strata(snapshots: Sequence[CorpusSnapshot], strata: Mapping[str, int] | None=None) -> dict[str, dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 172) — Divide the development strata across vaults by permitted units (largest remainder; deterministic).
- `plan_identity(handles: Sequence[CopyHandle], snapshots: Sequence[CorpusSnapshot], strata: Mapping[str, Mapping[str, int]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 191) — What a frozen plan is: the run id (pins, policy, units, the bank's smoke, logged and seed ids) and the family splits.
- `migration_head(handle: CopyHandle) -> int | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 208)
- `dry_run(copies: Sequence[Path], *, key_envs: Mapping[str, str] | None=None, env_file: Path | Sequence[Path] | None=None, reserve_share: float=0.0, environ: Mapping[str, str] | None=None, reuse_run: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 222) — The frozen plan and its estimate, with no network and no writes.
- `authorization_budget(roots: Sequence[Path], plan: Mapping[str, Any], *, reuse_run: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 363) — The plan's estimate against what is left of the cumulative E0 cap (relabel round): every other authorization's committed spend is carried (``budget.prior_spend``, read-only).
- `render_markdown(plan: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 445) — The dry-run aggregate as Markdown (no private text).
- `freeze(run_dir: Path, plan: Mapping[str, Any], snapshots: Sequence[CorpusSnapshot]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 515) — The paid run's private frozen manifests (spec §6), written before any call; returns their hashes.
- `require_paid_authorization(*, authorized: bool, dry_run_ok: bool, unverified_prices: Mapping[str, Sequence[str]] | None=None) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 542) — A paid run needs the orchestrator's explicit flag, a passing dry run and, for every metered pin, a verified price (fix round 4, High 2: the orchestrator fills ``price_verified`` from the providers' price pages before authorizing; admission refuses an unverified price anyway).
- `preflight(copies: Sequence[Path], *, key_envs: Mapping[str, str] | None=None, env_file: Path | Sequence[Path] | None=None, reserve_share: float=0.0, reuse_run: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 561) — ``--preflight-only``: everything the paid run checks before it spends, with ZERO network calls and no value printed (owner, 2026-10-22).

### Explicit exports

`__all__` declares:

- `NetworkForbidden`
- `config_allowlist`
- `dry_run`
- `freeze`
- `network_guard`
- `preflight`
- `render_markdown`
- `require_paid_authorization`
- `split_strata`
- `tree_digest`

## Internal implementation anchors

- `class _Guard` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 59)
- `_route(config: Any, task: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 101)
- `_count(values: Any) -> dict[str, int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 404)
- `_prompt_hash(snapshots: Sequence[CorpusSnapshot], seeds: Mapping[str, Sequence[Any]]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 411)
- `_by_provider(arms: Sequence[Mapping[str, Any]], systems: Sequence[Mapping[str, Any]], roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py), line 421)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `dry_run`, `preflight`, `render_markdown`, `require_paid_authorization`; statically calls `dry_run`, `preflight`, `require_paid_authorization`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `plan_identity`, `tree_digest`; statically calls `plan_identity`, `tree_digest`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `network_guard`, `tree_digest`; statically calls `network_guard`, `tree_digest`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `freeze`, `plan_identity`; statically calls `freeze`, `plan_identity`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `tree_digest`; statically calls `tree_digest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `logged_questions`, `plan_seeds`, `smoke_bank`, `writer_prompt`; calls `logged_questions`, `plan_seeds`, `smoke_bank`, `writer_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `require_codex_lockdown`, `require_no_codex_roles`; calls `require_codex_lockdown`, `require_no_codex_roles`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `canonical_ledger_dir`, `prior_spend`; calls `canonical_ledger_dir`, `prior_spend`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CopyHandle`, `CorpusSnapshot`, `_inside_local_root`, `alias`, `build_snapshot`, `open_copy`; calls `_inside_local_root`, `alias`, `build_snapshot`, `open_copy`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/credentials|learnloop.experiments.contextual_embeddings.credentials]] — imports `module`; calls `availability`, `load_env_files`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `pins_fingerprint`, `price_problem`, `unverified_prices`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `ASSUMPTIONS`, `EMBEDDING_ARMS`, `budget_check`, `embedding_arm_estimate`, `llm_estimates`, `query_token_sizes`, `reuse_estimate`, `run_id`, `subscription_requests`, `summarize`, `system_arm_estimates`; calls `budget_check`, `embedding_arm_estimate`, `llm_estimates`, `query_token_sizes`, `reuse_estimate`, `run_id`, `subscription_requests`, `summarize`, `system_arm_estimates`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `source_coverage`; calls `source_coverage`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `os`, `pathlib`, `socket`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_corpus.py](../../../../../../../tests/test_e0_corpus.py) — direct import
  - `test_wal_copies_are_converted_and_a_wal_copy_is_refused`
- [tests/test_e0_dry_run.py](../../../../../../../tests/test_e0_dry_run.py) — direct import
  - `test_split_strata_is_deterministic_and_complete`
  - `test_the_cli_dry_run_with_an_env_file_never_prints_the_key`
  - `test_the_dry_run_makes_no_network_call_and_writes_nothing`
  - `test_the_guard_blocks_and_counts_network_attempts`
  - `test_the_plan_has_every_arm_question_count_estimate_and_key_state`
  - `test_the_plan_is_aggregate_only_and_never_holds_a_key`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results`
  - `test_a_reused_run_with_other_candidate_maps_is_refused_before_anything_is_sealed`
  - `test_the_dry_run_budget_uses_the_reused_runs_ledger_and_fails_closed_without_it`
  - `test_the_paid_cli_passes_reuse_run_and_authorizes_on_the_cumulative_budget`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f5_the_paid_run_executes_the_frozen_split_or_refuses`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h2_the_dry_run_reports_unverified_prices_and_authorization_refuses_them`
  - `test_h3_two_paid_runs_with_different_run_directories_share_one_budget`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m10_the_dry_run_reports_the_planned_codex_requests`
  - `test_m12_an_unexpected_failure_still_writes_the_aggregate_report`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_paid_cli_refuses_when_the_lockdown_is_not_in_force`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_the_paid_preflight_passes_with_every_pin_verified_zero_codex_and_the_lockdown`
  - `test_the_plan_has_zero_codex_requests_and_the_paid_ledger_refuses_any`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains runner within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/runner.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/runner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
