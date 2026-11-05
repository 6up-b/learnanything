---
title: "learnloop.adaptive_difficulty.history_audit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/history_audit.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/history_audit.py"
source_commit: "8af1a25c40d715fd86ddaddf7e4191b6e7b30d4b"
source_commit_timestamp: "2026-11-05T00:29:18-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.history_audit module"
  - "src/learnloop/adaptive_difficulty/history_audit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.history_audit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.history_audit` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router objective RO2's owner-run audit, ``learnloop ad forecast-audit`` (spec_router_objective_v1 §6.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/history_audit.py](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py) |
| Source lines | 203 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8af1a25c40d715fd86ddaddf7e4191b6e7b30d4b` |
| Commit timestamp | `2026-11-05T00:29:18-05:00` |

## Public API

- `plan_audit(vault: Any, repository: Any, *, mode: str, limit: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 92) — The dry run: what ``mode`` would send and what it would cost; no call, no write.
- `run_audit(vault: Any, repository: Any, *, mode: str, limit: int | None=None, clients: Clients | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 131) — The paid run (``permuted``) or the free sweep (``prior-sweep``).

### Module constants

- `PERMUTED` ([src/learnloop/adaptive_difficulty/history_audit.py](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 39)
- `PRIOR_SCALES` ([src/learnloop/adaptive_difficulty/history_audit.py](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 41)
- `MODES` ([src/learnloop/adaptive_difficulty/history_audit.py](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 42)

### Explicit exports

`__all__` declares:

- `MODES`
- `PERMUTED`
- `PRIOR_SCALES`
- `plan_audit`
- `run_audit`

## Internal implementation anchors

- `_decoded(row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 45)
- `_plan(connection: Any, view: Any, *, limit: int | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 55) — The permuted pairs: each frozen H3 card with a donor of a similar level served no later.
- `_version_points(vault: Any, repository: Any) -> dict[str, list[tuple[float, float]]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py), line 183)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `plan_audit`, `run_audit`; statically calls `plan_audit`, `run_audit`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `LeaseLost`, `claimed`, `history_key`; calls `claimed`, `history_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `INCUMBENT`, `receipt_key`; calls `receipt_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `module`; calls `_done`, `_forecast_rung`, `call_tokens`, `forecaster_name`, `prompt_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `Clients`, `ForecastOutcome`; calls `Clients`, `ForecastOutcome`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `calibration_slopes`, `score_rows`; calls `calibration_slopes`, `score_rows`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `SendGuard`, `refusal_status`; calls `SendGuard`, `refusal_status`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_audit_dry_run_calls_and_writes_nothing`
  - `test_the_dry_run_estimates_the_runs_own_output_budget_and_retry`
  - `test_the_permuted_run_sends_another_presentations_history`

## Modification guidance

- Make changes here when the responsibility remains history audit within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/history_audit.py](../../../../../../src/learnloop/adaptive_difficulty/history_audit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
