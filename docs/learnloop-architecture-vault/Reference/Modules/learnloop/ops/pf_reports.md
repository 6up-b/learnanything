---
title: "learnloop.ops.pf_reports"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_reports.py"
source_paths:
  - "src/learnloop/ops/pf_reports.py"
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
  - "learnloop.ops.pf_reports module"
  - "src/learnloop/ops/pf_reports.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_reports`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_reports` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: PF-b pilot and scaling-check reports (Slice 2 §5.6), run through `learnloop eval`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py) |
| Source lines | 642 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `wilson(successes: int, total: int, z: float=1.96) -> list[float] | None` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 59)
- `usage_signals(repository: Repository, vault: LoadedVault, item_ids: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 132) — Attempts, retirements and affect taps on published items (aggregate).
- `frozen_inputs_key(row: Mapping[str, Any]) -> tuple[str, str | None, str | None]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 222) — (family, judged parent contract, family revision): rows comparable as identical inputs.
- `pilot_report(vault: LoadedVault, *, round_id: str, output_dir: Path, judge: bool=False, dry_run: bool=False, caps: SpendCaps | None=None, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, clients: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 325)
- `scaling_report(vault: LoadedVault, *, round_id: str, output_dir: Path, judge: bool=False, dry_run: bool=False, caps: SpendCaps | None=None, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, clients: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 434)

### Module constants

- `REPORT_VERSION` ([src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py), line 50)
- `PILOT_PAIRS` ([src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py), line 51)
- `SCALING_PAIRS` ([src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py), line 52)
- `MIN_AGREED_PAIRS` ([src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py), line 55)
- `ARMS` ([src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py), line 56)

### Explicit exports

`__all__` declares:

- `pilot_report`
- `scaling_report`
- `usage_signals`
- `wilson`

## Internal implementation anchors

- `_rate(successes: int, total: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 69)
- `_rows(repository: Repository, round_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 74)
- `_verdicts(repository: Repository, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 79) — Ledgered verdicts per candidate: the authority for every report metric (§5.8).
- `_survival(rows: list[dict[str, Any]], verdicts: Mapping[str, dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 85)
- `_panel_disagreement(rows: list[dict[str, Any]], verdicts: Mapping[str, dict[str, Any]], minimum: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 99)
- `_receipts_cost(repository: Repository, run_ids: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 109)
- `class _Judge` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 157) — The paid blind pairwise judge; two passes with the order swapped.
- `_admit(caller: PFCaller, entry: Any, estimate: SpendEstimate) -> None` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 199) — Whole-plan admission for one route's billing class (Codex: estimated only, not capped).
- `_judge_estimate(vault: LoadedVault, repository: Repository, pairs: int, *, caps: SpendCaps, price_per_million: float | None, clients: Mapping[str, Any] | None, cancelled: Callable[[], bool] | None) -> tuple[SpendEstimate, dict[str, Any], Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 206) — The blind judge's planned calls, tokens and dollars, admitted without building a client.
- `_pair_rows(left: list[dict[str, Any]], right: list[dict[str, Any]], limit: int, key: Callable[[Mapping[str, Any]], Any]=frozen_inputs_key) -> list[tuple[dict, dict]]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 231) — Pairs within the same family and frozen inputs only, spread across families.
- `_summarize_pairs(results: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 254)
- `_judge_plan(pairs: int, price_per_million: float | None, *, subscription: bool=False) -> SpendEstimate` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 274) — Two passes per pair; dollars from the owner price (None when metered and unknown).
- `_write(output_dir: Path, name: str, report: dict[str, Any], markdown: str) -> list[str]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 285)
- `_repository(vault: LoadedVault, writable: bool) -> Repository` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 294)
- `_arm_summary(repository: Repository, vault: LoadedVault, rows: list[dict[str, Any]], verdicts: Mapping[str, dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 299)
- `_recommend(report: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 378) — A default path only from usable, agreed blind comparisons on shared families (§5.6).
- `_pilot_markdown(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 415)
- `_judge_agreement(repository: Repository, vault: LoadedVault, rows: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 496) — Judge behaviour on this tier's own candidates, and usage signals (Slice 2 §5.6).
- `_labelled_judge_accuracy(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 542) — Each tier's freshness judge against B2's independent labels, on identical pairs.
- `_tier_verdict(cheap: dict[str, Any], frontier: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 589)
- `_components(report: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 599)
- `_scaling_markdown(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/ops/pf_reports.py), line 631)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `pilot_report`, `scaling_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/content/authoring/pf_contracts|learnloop.content.authoring.pf_contracts]] — imports `module`; calls `pairwise_prompt`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `module`; calls `candidate_verdicts`, `candidates`, `verdict_panel`, `verdict_survived`, `verdict_verified`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `judge_prediction`; calls `judge_prediction`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `PFCaller`, `PFUnavailable`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`; calls `PFCaller`, `estimate_tokens`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `FILTER_ORDER`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_quote_check_without_its_span_support_verdict_is_never_verified`
  - `test_pilot_report_verdicts_come_from_the_ledger_not_workflow_json`
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — direct import
  - `test_a_judge_that_answers_nothing_earns_no_accuracy_credit`
  - `test_judge_accuracy_comes_from_labelled_pairs_judged_at_both_tiers`
  - `test_pairs_never_cross_families_or_frozen_inputs`
  - `test_pilot_compares_all_three_arms_and_the_blind_judge_is_two_pass`
  - `test_pilot_never_recommends_a_path_without_usable_comparisons`
  - `test_pilot_recommends_only_from_agreed_comparisons_on_the_same_families`
  - `test_report_dry_runs_price_and_admit_the_blind_judge`
  - `test_scaling_check_reports_each_tier_and_component`
  - `test_suspect_acceptance_is_descriptive_and_never_ranks_a_tier`
  - `test_tiers_are_compared_only_on_identical_labelled_pairs`
  - `test_wilson_interval`

## Modification guidance

- Make changes here when the responsibility remains pf reports within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_reports.py](../../../../../../src/learnloop/ops/pf_reports.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
