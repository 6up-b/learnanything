---
title: "learnloop.cli.router"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/router.py"
source_paths:
  - "src/learnloop/cli/router.py"
source_commit: "96ba40f55c3587f2e716522918d4ae4d06b172ea"
source_commit_timestamp: "2026-11-05T05:31:58-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.router module"
  - "src/learnloop/cli/router.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.router`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.router` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop router log`, `card`, `report`, `trace`, `objective-report` and `embed-decisions`: the router's logged decisions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/router.py](../../../../../../src/learnloop/cli/router.py) |
| Source lines | 451 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `96ba40f55c3587f2e716522918d4ae4d06b172ea` |
| Commit timestamp | `2026-11-05T05:31:58-05:00` |

## Public API

- `router_log(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], limit: Annotated[int, typer.Option('--limit', min=1, help='Newest decisions to show.')]=20, candidates: Annotated[bool, typer.Option('--candidates', help="Include each decision's full candidate set.")]=False, decision: Annotated[str | None, typer.Option('--decision', help="Show this one decision in full: its candidates, the mixture's weights, both models' answers, sensors and similar decisions, and the payloads stored beside it (the receipt a block's details line names).")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 111) — The newest logged router decisions, with their R_next / R_cold / S outcomes.
- `router_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 207) — Lesson suggestions (teacher TE1b) by randomized arm (card shown or not): offered, accepted, opened and completed over every decision (intention to treat), and the mean R_cold on the drawn topic among outcomes observed so far (descriptive, not an ITT estimate), weighted by the lo…
- `router_card(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], decision: Annotated[str, typer.Option('--decision', help='A router decision id (learnloop router log).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 264) — The learner-state card a decision stored (router R2a): its text, or with --json the typed card.
- `router_trace(decision: Annotated[str, typer.Argument(help='A router decision id (learnloop router log), or a trace id.')], vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 312) — Router objective RO4's trace of one decision (spec §8.8): each sensor, the objective's terms, both policies, the mix and the output; in plain words, or with --json the whole trace (read-only).
- `router_objective_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 367) — Router objective RO4's report (spec §8.9): serving (stop's share at each boundary, session length, each policy's share, by day), and the forecast, action-value and recommendation-value evaluations kept apart, with counts and versioned comparators.
- `router_embed_decisions(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Count the decisions without a vector and estimate calls, tokens and cost; send and write nothing.')]=False, limit: Annotated[int | None, typer.Option('--limit', min=1, help='Embed at most this many decisions.')]=None, batch_size: Annotated[int, typer.Option('--batch-size', min=1, max=256)]=32, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=2000, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=2000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=0.25, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive USD input-token estimate for an unknown/changed model price; still subject to the cost cap.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 398) — Backfill the decision/context vectors similar-decision retrieval reads (router R2c).

## Internal implementation anchors

- `_reader_exposures(connection: sqlite3.Connection, loaded: Any, path: Path) -> list[tuple[str, str]] | None` ([source](../../../../../../src/learnloop/cli/router.py), line 40) — What this vault's outcome version reads of the Reader (read-only, like everything here).
- `_emit(payload: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/router.py), line 51)
- `_summary(row: dict[str, Any], outcome: dict[str, Any] | None, *, candidates: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/router.py), line 55)
- `_objective_forecasts(connection: Any, loaded: Any, path: Path, now: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/cli/router.py), line 348) — RO4 §8.9's forecast evaluation (the LLM policy's forecasts through RO2's resolver); None when it cannot be read here (the report says so), never a failed report.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `router_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `resolve_curves`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `module`; calls `backfill`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `for_version`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `router_decision_rows`, `router_payload`, `router_payloads_present`; calls `router_decision_rows`, `router_payload`, `router_payloads_present`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`, `trace`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `decisions`, `releases`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`; calls `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/router/suggestion_report|learnloop.router.suggestion_report]] — imports `itt_split`, `lines`; calls `itt_split`, `lines`
- [[Reference/Modules/learnloop/router_objective/forecast_resolve|learnloop.router_objective.forecast_resolve]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `module`; calls `build`, `lines`
- [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] — imports `explain`; calls `explain`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `held_for_review_attempts`, `pfc_assessments`; calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `logging`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/router.py](../../../../../../src/learnloop/cli/router.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
