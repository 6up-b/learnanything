---
title: "learnloop.scheduling.action_loss"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/action_loss.py"
source_paths:
  - "src/learnloop/scheduling/action_loss.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.action_loss module"
  - "src/learnloop/scheduling/action_loss.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.action_loss`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.action_loss` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 3 -- the minutes-denominated decision-loss table L(h, a) (U-023, spec §6.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/action_loss.py](../../../../../../src/learnloop/scheduling/action_loss.py) |
| Source lines | 358 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class LossDerivationError(ValueError)` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 49) — A loss cell was constructed without a minutes derivation (registration lint).
- `class LossTableIncompleteError(ValueError)` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 53) — The loss table is missing cells or hypotheses the decision needs.
  - `__init__(self, reason: str, detail: Sequence[str] | str=()) -> None` (line 64; internal)
- `class DurationEstimate` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 71) — One intervention's minutes estimate + its provenance (inspectable).
  - `as_dict(self) -> dict[str, Any]` (line 79; public)
- `class LossCell` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 89) — One L(h, a) entry with its expected-minutes derivation attached (§6.2).
  - `as_dict(self) -> dict[str, Any]` (line 97; public)
- `class LossTable` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 107) — A frozen, content-hashed, minutes-denominated loss table (§6.2).
  - `loss(self, hypothesis: str, action: str) -> float` (line 122; public)
  - `expected_loss(self, action: str, posterior: Mapping[str, float]) -> float` (line 132; public)
  - `argmin_action(self, posterior: Mapping[str, float]) -> str` (line 138; public) — The minimum-expected-loss action under ``posterior`` (§6.3 ``current_loss`` argmin).
  - `argmin_action_set(self, posterior: Mapping[str, float], *, tol: float=1e-09) -> frozenset[str]` (line 154; public) — All actions whose expected loss is within ``tol`` of the minimum -- the decision-space "same optimal action" set (§6.2), never closeness of values.
  - `as_dict(self) -> dict[str, Any]` (line 162; public)
- `attempt_minutes_by_intervention(interventions: Sequence[str], *, repository: Repository | None=None, overrides: Mapping[str, float] | None=None) -> dict[str, DurationEstimate]` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 197) — Per-intervention minutes estimate with provenance.
- `build_loss_table(*, routes: Sequence[Mapping[str, Any]], hypotheses: Sequence[str] | None=None, repository: Repository | None=None, duration_overrides: Mapping[str, float] | None=None, calibration_label: str='heuristic', scope: str='global') -> LossTable` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 235) — Derive L(h, a) from triage-route structure + logged attempt durations (§6.2).
- `assert_derived(table: LossTable) -> None` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 320) — Registration lint (U-023, spec §16.3): every loss cell must carry a minutes derivation.
- `raw_cell(hypothesis: str, action: str, minutes: float) -> LossCell` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 353) — Construct an UNDERIVED loss cell (a free constant).

### Module constants

- `LOSS_TABLE_VERSION` ([src/learnloop/scheduling/action_loss.py](../../../../../../src/learnloop/scheduling/action_loss.py), line 41)
- `DEFAULT_INTERVENTION_MINUTES` ([src/learnloop/scheduling/action_loss.py](../../../../../../src/learnloop/scheduling/action_loss.py), line 46)

## Internal implementation anchors

- `_pooled_attempt_minutes(repository: Repository) -> tuple[float | None, int]` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 181) — Median logged attempt duration in minutes + the sample count.
- `_routes_by_reason(routes: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/action_loss.py), line 226)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `module`; statically calls `build_loss_table`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`
- [[Reference/Modules/learnloop/sim/interval_width_viability|learnloop.sim.interval_width_viability]] — imports `module`; statically calls `LossCell`, `LossTable`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]], [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]], [[Reference/Modules/learnloop/sim/interval_width_viability|learnloop.sim.interval_width_viability]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_action_loss.py](../../../../../../tests/test_action_loss.py) — direct import
  - `test_argmin_action_and_shared_optimal_set`
  - `test_durations_fall_back_to_logged_pooled_then_heuristic`
  - `test_every_cell_carries_a_minutes_derivation`
  - `test_free_constant_entry_fails_registration`
  - `test_loss_table_is_derived_from_routes_and_durations`
  - `test_table_hash_is_order_invariant`
- [tests/test_evsi.py](../../../../../../tests/test_evsi.py) — direct import
- [tests/test_evsi_fail_closed.py](../../../../../../tests/test_evsi_fail_closed.py) — direct import
  - `test_incomplete_grid_fails_registration`
  - `test_missing_loss_cell_raises_instead_of_impersonating_the_effective_repair`
  - `test_routeless_hypothesis_fails_closed_instead_of_silently_dropping`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import

## Modification guidance

- Change action loss policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/action_loss.py](../../../../../../src/learnloop/scheduling/action_loss.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
