---
title: "learnloop.router.outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/outcomes.py"
source_paths:
  - "src/learnloop/router/outcomes.py"
source_commit: "37d71de7a06f49dbc71684c2e00fb3963deff7c8"
source_commit_timestamp: "2026-10-14T11:32:34-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.outcomes module"
  - "src/learnloop/router/outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.outcomes` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R1: ``router_outcomes`` (DERIVED, one replayer) per logged decision.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py) |
| Source lines | 860 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `37d71de7a06f49dbc71684c2e00fb3963deff7c8` |
| Commit timestamp | `2026-10-14T11:32:34-04:00` |

## Public API

- `servable_items_by_learning_object(vault: Any) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 472) — Each learning object's active, servable practice items (vault content).
- `derive_router_outcomes(connection: sqlite3.Connection, *, pfc_states: Mapping[str, str] | None=None, servable_items_by_lo: Mapping[str, set[str]] | None=None, retrievability_by_attempt: Mapping[str, float] | None=None, held_attempt_ids: frozenset[str] | set[str]=frozenset()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 659) — One outcome row per logged decision, from the ledgers alone (read-only).
- `rebuild_router_outcomes(connection: sqlite3.Connection, *, pfc_states: Mapping[str, str] | None=None, servable_items_by_lo: Mapping[str, set[str]] | None=None, retrievability_by_attempt: Mapping[str, float] | None=None, held_attempt_ids: frozenset[str] | set[str]=frozenset()) -> int` ([source](../../../../../../src/learnloop/router/outcomes.py), line 828) — Replace the derived cache; the caller owns the transaction.

### Module constants

- `OUTCOME_VERSION` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 98)
- `BINDING_PRESENTATION` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 101)
- `BINDING_CANDIDATE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 102)
- `BINDING_SESSION_RULE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 103)
- `S_ALPHA` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 106)
- `INDEPENDENT_ATTEMPT_TYPES` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 109)
- `_DELAY_REASONS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 114)
- `_ATTEMPT_COLUMNS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 116)
- `_OPTIONAL_ATTEMPT_COLUMNS` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 123)
- `R_COLD_RULE` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 126)
- `COLDNESS_CANDIDATE_CAP` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 128)
- `COVARIATE_NAMES` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 130)
- `_INTERRUPT_KIND` ([src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py), line 406)

### Explicit exports

`__all__` declares:

- `COLDNESS_CANDIDATE_CAP`
- `COVARIATE_NAMES`
- `INDEPENDENT_ATTEMPT_TYPES`
- `R_COLD_RULE`
- `OUTCOME_VERSION`
- `S_ALPHA`
- `derive_router_outcomes`
- `rebuild_router_outcomes`
- `servable_items_by_learning_object`

## Internal implementation anchors

- `_facet_ids(raw: Any) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 144) — Facet ids from an ``evidence_facets_json`` / ``facets_json`` value.
- `_table_present(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../src/learnloop/router/outcomes.py), line 164)
- `_seconds(later: str, earlier: str) -> int | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 170)
- `_exclusions(attempt: Mapping[str, Any], *, elapsed_seconds: int | None, source_session_id: str | None, pfc_states: Mapping[str, str]) -> list[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 177)
- `class _Ledger` ([source](../../../../../../src/learnloop/router/outcomes.py), line 206) — The attempt, reveal and exposure ledgers, indexed once for every decision.
- `_decision_block(decision: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/router/outcomes.py), line 409) — The block of a ``plan_block`` or ``plan_interrupt`` decision (its receipt key names it).
- `_presentation_is_the_decisions(decision: Mapping[str, Any], presentation: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/router/outcomes.py), line 422) — Whether ``presentation`` (of the decision's block) served this decision's action.
- `_action_attempt(decision: Mapping[str, Any], ledger: _Ledger, presentations: Mapping[str, list[dict[str, Any]]] | None=None) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 436) — The action attempt and how it was bound (module docstring, rules 1-3).
- `_r_next(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str], *, until_position: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 492) — The first fresh, unassisted, independent attempt after the action, at or before ``until_position`` (the R_cold attempt) when one is given.
- `_r_cold(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 532)
- `_not_applicable(decision: Mapping[str, Any], status: str, observed_through: str | None, *, pending: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 573)
- `_covariate_columns(prefix: str, covariates: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 606)
- `_coldness_candidates(action: Mapping[str, Any], considered: list[tuple[dict[str, Any], list[str]]], ledger: _Ledger, *, r_next_id: str | None, r_cold_id: str | None) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 610) — Every later attempt the R_cold rule considered, with its covariates.
- `_ended_sessions(connection: sqlite3.Connection, session_ids: set[str]) -> set[str]` ([source](../../../../../../src/learnloop/router/outcomes.py), line 642)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `derive_router_outcomes`, `servable_items_by_learning_object`; statically calls `derive_router_outcomes`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `derive_router_outcomes`, `servable_items_by_learning_object`; statically calls `derive_router_outcomes`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_router_outcomes`, `servable_items_by_learning_object`; statically calls `rebuild_router_outcomes`, `servable_items_by_learning_object`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `presentations_for_blocks`; calls `presentations_for_blocks`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `replace_router_outcomes`; calls `replace_router_outcomes`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `RETENTION_MIN_DELAY_SECONDS`, `retention_exclusions`; calls `retention_exclusions`

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_released_hold_is_an_ordinary_outcome_again`
- [tests/test_reader_rw3a_landing.py](../../../../../../tests/test_reader_rw3a_landing.py) — direct import
  - `test_the_answer_to_a_check_binds_by_the_picks_presentation`
- [tests/test_router_coldness_covariates.py](../../../../../../tests/test_router_coldness_covariates.py) — direct import
  - `test_an_unobserved_outcome_has_no_covariates`
  - `test_each_outcome_records_its_coldness_covariates`
- [tests/test_router_g4_restraint.py](../../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation`
- [tests/test_router_outcomes.py](../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_an_observed_cold_retrieval_finalizes_s_and_closes_r_next`
  - `test_r_cold_needs_a_day_since_the_last_exposure_including_reveals`
  - `test_r_next_is_not_applicable_on_a_single_item_learning_object_and_r_cold_finalizes_s`
  - `test_the_replayer_applies_the_vaults_servable_items`
- [tests/test_router_presentations.py](../../../../../../tests/test_router_presentations.py) — direct import
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_replay_never_asks_a_model_and_is_deterministic`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_replay_never_needs_a_vector`

## Modification guidance

- Make changes here when the responsibility remains outcomes within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/outcomes.py](../../../../../../src/learnloop/router/outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
