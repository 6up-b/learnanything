---
title: "learnloop.router_objective.picks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/picks.py"
source_paths:
  - "src/learnloop/router_objective/picks.py"
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
  - "learnloop.router_objective.picks module"
  - "src/learnloop/router_objective/picks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.picks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.picks` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 6 (owner decision, Nov 4): testing misconception picks.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py) |
| Source lines | 144 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `84b890f02cd674436ba3b9ce3ab22628680d0783` |
| Commit timestamp | `2026-11-05T07:25:07-05:00` |

## Public API

- `seed_for(factor_id: str) -> str` ([source](../../../../../../src/learnloop/router_objective/picks.py), line 37)
- `assign(connection: Any, *, factor_id: str, share: float, report_id: str, at: str, eligibility: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/picks.py), line 41) — The pick's arm: an existing assignment for the factor (a retry), else a fresh one on the factor's seed, written on ``connection`` (the report's transaction).
- `section(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/picks.py), line 66) — ``learnloop data-capture report``'s open-picks section (module docstring), read-only.

### Module constants

- `VERSION` ([src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py), line 30)
- `OPEN` ([src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py), line 31)
- `RESOLVE` ([src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py), line 32)
- `AGREEMENT_LABEL` ([src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py), line 33)
- `DELAYED_LABEL` ([src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py), line 34)

### Explicit exports

`__all__` declares:

- `AGREEMENT_LABEL`
- `DELAYED_LABEL`
- `OPEN`
- `RESOLVE`
- `VERSION`
- `assign`
- `section`
- `seed_for`

## Internal implementation anchors

- `_present(connection: Any, table: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/picks.py), line 61)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `module`; statically calls `assign`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `section`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] — imports `DELAYED_LABEL`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `uniform`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `by_unit`, `insert`, `rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_picks.py](../../../../../../tests/test_ro5_picks.py) — direct import
  - `test_a_resolving_pick_resolves_as_before_with_its_arm_logged`
  - `test_a_retry_reuses_the_factors_assignment`
  - `test_an_open_pick_is_recorded_as_opinion_opens_no_belief_and_leaves_the_factor_open`

## Modification guidance

- Make changes here when the responsibility remains picks within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/picks.py](../../../../../../src/learnloop/router_objective/picks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
