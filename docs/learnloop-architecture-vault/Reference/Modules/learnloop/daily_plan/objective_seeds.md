---
title: "learnloop.daily_plan.objective_seeds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_seeds.py"
source_paths:
  - "src/learnloop/daily_plan/objective_seeds.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_seeds module"
  - "src/learnloop/daily_plan/objective_seeds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_seeds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_seeds` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The objective router's seeds, in one place: what each depends on, and why they differ.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_seeds.py](../../../../../../src/learnloop/daily_plan/objective_seeds.py) |
| Source lines | 100 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `numeric_seed(identity: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_seeds.py), line 27) — The numeric policy's random seed for one boundary (router speed stage 2, landing ruling R2): derived from the boundary identity the prefetch key hashes, less ``SEED_NEUTRAL_SWITCHES`` in its switch snapshot.
- `mix_seed(runtime: Any, boundary_key: str, decision_id: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/objective_seeds.py), line 92) — The seed of one decision's mix (and of its stop coin): the runtime's own when it pins one, else ``mix.seed_for(boundary_key, decision_id)``.

### Explicit exports

`__all__` declares:

- `mix_seed`
- `numeric_seed`

## Internal implementation anchors

- `_without_miss_cause(identity: Mapping[str, Any]) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_seeds.py), line 55) — Slip or gap: the identity less what it names only so a flip or a changed sensor starts a new job (both switches, the sensor's mark, the sensor on an offer's card record): a decision is valued on the same draws whatever they are (``router_objective_switches.COMMON_DRAW_OBJECTIVE_…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `mix_seed`, `numeric_seed`; statically calls `mix_seed`, `numeric_seed`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `_hash`; calls `_hash`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; calls `seed_for`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `COMMON_DRAW_IDENTITY_KEYS`, `COMMON_DRAW_OBJECTIVE_KEYS`, `MISS_CAUSE_OFFER_KEY`, `SEED_NEUTRAL_IDENTITY_KEYS`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_SWITCHES`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_check_credit_activation.py](../../../../../../tests/test_check_credit_activation.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains objective seeds within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_seeds.py](../../../../../../src/learnloop/daily_plan/objective_seeds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
