---
title: "learnloop.content.facet_identity.dedupe"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/dedupe.py"
source_paths:
  - "src/learnloop/content/facet_identity/dedupe.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.dedupe module"
  - "src/learnloop/content/facet_identity/dedupe.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.dedupe`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.dedupe` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: ``learnloop facets dedupe``: one-off cleanup of an existing vault's facets.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/dedupe.py](../../../../../../../src/learnloop/content/facet_identity/dedupe.py) |
| Source lines | 247 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `facets_in_scope(vault: LoadedVault, subject_id: str | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/dedupe.py), line 48) — Registered, non-retired canonical facets (of one subject, if given).
- `plan_dedupe(vault: LoadedVault, *, subject_id: str | None=None) -> tuple[list[Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/facet_identity/dedupe.py), line 83) — The judge requests (one per bounded neighbourhood) and the grouping summary.
- `run_dedupe(root: Path, *, subject_id: str | None=None, dry_run: bool=False, caps_overrides: dict[str, Any] | None=None, price_per_million_input: float | None=None, price_per_million_output: float | None=None, client: Any=None, cancelled: Callable[[], bool] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/dedupe.py), line 117) — Plan, judge and apply.

### Explicit exports

`__all__` declares:

- `facets_in_scope`
- `plan_dedupe`
- `run_dedupe`

## Internal implementation anchors

- `_stored_vectors(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/dedupe.py), line 69) — Complete stored facet/definition vectors, or nothing (never a paid call).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]] — imports `run_dedupe`; statically calls `run_dedupe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendLimitExceeded`; calls `SpendBudget`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `HELD_BACK_NOTE`, `action_by_id`, `describe`, `facet_evidence`, `merge_registered_facets`, `recover_interrupted_actions`; calls `action_by_id`, `describe`, `facet_evidence`, `merge_registered_facets`, `recover_interrupted_actions`
- [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]] — imports `FacetNode`, `neighbourhood_groups`; calls `FacetNode`, `neighbourhood_groups`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `Member`, `build_judge`, `build_request`, `caps_from_config`, `plan_estimate`, `resolve_route`; calls `Member`, `build_judge`, `build_request`, `caps_from_config`, `plan_estimate`, `resolve_route`
- [[Reference/Modules/learnloop/content/facet_identity/views|learnloop.content.facet_identity.views]] — imports `judge_view`; calls `judge_view`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `FACET_RECIPE`, `GraphNominator`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_a_failing_judge_is_retried_within_the_cap_then_gives_up`
  - `test_an_undone_merge_is_an_owner_verdict_and_dedupe_never_reapplies_it`
  - `test_dedupe_dry_run_plans_calls_and_cost_with_no_client_or_change`
  - `test_dedupe_kill_switch_refuses`
  - `test_dedupe_regression_set_merges_the_agreed_pairs_and_keeps_the_distinct_ones`
  - `test_judge_writes_one_ledger_row_per_pair_and_never_pays_twice`
  - `test_spend_caps_stop_the_judge_before_a_call`
- [tests/test_facet_identity_actions.py](../../../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_dedupe_applies_a_set_whose_facets_carry_evidence`
  - `test_dedupe_reports_a_held_back_retiree_as_refused`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_an_undo_still_supersedes_the_judges_merged_rows`
  - `test_dedupe_applies_a_set_with_evidence`
  - `test_dedupe_through_a_decider_route_merges_and_writes_labelled_receipts`
  - `test_the_structured_judge_labels_its_receipts_llm`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_the_dedupe_dry_run_never_migrates_the_database`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_a_truncated_facet_judgment_is_retried_once_at_double_the_budget`
  - `test_the_facet_judge_asks_for_and_reserves_the_policy_budget`

## Modification guidance

- Change dedupe policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/dedupe.py](../../../../../../../src/learnloop/content/facet_identity/dedupe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
