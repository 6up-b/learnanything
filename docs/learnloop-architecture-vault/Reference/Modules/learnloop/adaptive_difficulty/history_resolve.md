---
title: "learnloop.adaptive_difficulty.history_resolve"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/history_resolve.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/history_resolve.py"
source_commit: "8d1272482fc14d002b0c0671f74e5f37d2427af9"
source_commit_timestamp: "2026-11-04T21:28:27-05:00"
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
  - "learnloop.adaptive_difficulty.history_resolve module"
  - "src/learnloop/adaptive_difficulty/history_resolve.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.history_resolve`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.history_resolve` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router objective RO2's versioned resolver for ``lo_cold_success`` (spec_router_objective_v1 §6.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py) |
| Source lines | 208 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8d1272482fc14d002b0c0671f74e5f37d2427af9` |
| Commit timestamp | `2026-11-04T21:28:27-05:00` |

## Public API

- `interpolate(curve: Mapping[str, Any], lag_days: float) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 66) — The curve's probability at ``lag_days``: linear in log time between the stated lags; the first lag's value below it; None past the last (censored ``beyond_measured_lag``).
- `resolve(connection: Any, vault: Any, repository: Any, *, now: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 105) — Every ``lo_cold_success`` curve resolved under both bindings (pure reads; zero model calls).

### Module constants

- `RESOLVER_VERSION` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 50)
- `PER_PROTOCOL` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 51)
- `INTENTION_TO_TREAT` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 52)
- `BINDINGS` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 53)
- `MAX_LAG_DAYS` ([src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 56)

### Explicit exports

`__all__` declares:

- `BINDINGS`
- `INTENTION_TO_TREAT`
- `MAX_LAG_DAYS`
- `PER_PROTOCOL`
- `RESOLVER_VERSION`
- `interpolate`
- `resolve`

## Internal implementation anchors

- `_days(later: Any, earlier: Any) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 59)
- `_groups(receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 82) — One forecast curve per presentation and forecaster (the receipts of one call).
- `_log_loss(p: float | None, y: float | None) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py), line 201)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `resolve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `CENSORED`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `unassisted_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `log_loss`; calls `log_loss`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `LO_COLD_SUCCESS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_log_time_interpolation`

## Modification guidance

- Make changes here when the responsibility remains history resolve within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/history_resolve.py](../../../../../../src/learnloop/adaptive_difficulty/history_resolve.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
