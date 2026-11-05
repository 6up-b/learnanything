---
title: "learnloop.router_objective.assignments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/assignments.py"
source_paths:
  - "src/learnloop/router_objective/assignments.py"
source_commit: "84b890f02cd674436ba3b9ce3ab22628680d0783"
source_commit_timestamp: "2026-11-05T07:25:07-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.assignments module"
  - "src/learnloop/router_objective/assignments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.assignments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.assignments` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9: each arm's assignment in ``policy_experiment_assignments`` (migration 098), the one place policy experimentation lives, through its existing ``experiment_id`` (``daily_plan/measurement.py``'s ``experiment_id`` and ``scheduling/randomization_layer.py``'s are the same inte…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py) |
| Source lines | 117 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `84b890f02cd674436ba3b9ce3ab22628680d0783` |
| Commit timestamp | `2026-11-05T07:25:07-05:00` |

## Public API

- `present(connection: Any) -> bool` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 45)
- `insert(connection: Any, *, experiment_id: str, unit_id: str, variant: str, propensity: float, seed: str, draw: float | None, candidate_refs: Sequence[Any]=(), detail: Mapping[str, Any] | None=None, at: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 50) — One assignment on ``connection`` in its own savepoint; its id, or None (a warning) when refused.
- `record_pending(connection: Any, pending: Iterable[Mapping[str, Any]], *, unit_id: str, at: str) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 73) — The assignments a chooser froze on its record (``ro5_assignments``), written with the decision they belong to (``unit_id`` the router decision id).
- `rows(connection: Any, experiment_id: str, *, unit_like: str | None=None, unit_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 88) — Every assignment of one experiment, oldest first, with its JSON decoded (read-only).
- `by_unit(connection: Any, experiment_id: str, unit_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 111)

### Module constants

- `LOG` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 31)
- `STOP_COIN` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 33)
- `CHECK` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 34)
- `PICK` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 35)
- `EXPERIMENTS` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 36)
- `DESIGN` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 37)
- `TABLE` ([src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py), line 38)

### Explicit exports

`__all__` declares:

- `CHECK`
- `DESIGN`
- `EXPERIMENTS`
- `PICK`
- `STOP_COIN`
- `by_unit`
- `insert`
- `present`
- `record_pending`
- `rows`

## Internal implementation anchors

- `_canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/assignments.py), line 41)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `record_pending`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `rows`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; statically calls `by_unit`, `insert`, `present`, `rows`
- [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] — imports `module`; statically calls `by_unit`, `insert`, `rows`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; statically calls `rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `insert_assignment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]], [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]], [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
- [tests/test_ro5_codex_rereview.py](../../../../../../tests/test_ro5_codex_rereview.py) — direct import
  - `test_f10_a_past_completion_rate_never_moves_with_a_later_assignment`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session`
- [tests/test_ro5_picks.py](../../../../../../tests/test_ro5_picks.py) — direct import
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_serving_records_each_coin_with_its_exact_probability_and_availability`

## Modification guidance

- Make changes here when the responsibility remains assignments within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/assignments.py](../../../../../../src/learnloop/router_objective/assignments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
