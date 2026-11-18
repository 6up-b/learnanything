---
title: "learnloop.substrate.projection_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/projection_switches.py"
source_paths:
  - "src/learnloop/substrate/projection_switches.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.projection_switches module"
  - "src/learnloop/substrate/projection_switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.projection_switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.projection_switches` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Switches recorded on a whole-vault rebuild receipt.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/projection_switches.py](../../../../../../src/learnloop/substrate/projection_switches.py) |
| Source lines | 35 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `projection_switches(config: Any) -> dict[str, bool]` ([source](../../../../../../src/learnloop/substrate/projection_switches.py), line 22) — What a whole-vault rebuild derived persisted state under (§5.5): whether the factor was removed, and from the facet-belief successor (mvp-0.59) whether its fixes were on (the per-LO facet uncertainty and every attempt's stored reading of the belief follow a switch change only at…

### Module constants

- `INTERVAL_FACTOR_SNAPSHOT_KEY` ([src/learnloop/substrate/projection_switches.py](../../../../../../src/learnloop/substrate/projection_switches.py), line 16)
- `FACET_BELIEF_FIXES_SNAPSHOT_KEY` ([src/learnloop/substrate/projection_switches.py](../../../../../../src/learnloop/substrate/projection_switches.py), line 19)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `FACET_BELIEF_FIXES_SNAPSHOT_KEY`, `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `projection_switches`; statically calls `projection_switches`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `projection_switches`; statically calls `projection_switches`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FACET_BELIEF_FIX_VERSIONS`
- [[Reference/Modules/learnloop/config/scheduler_switches|learnloop.config.scheduler_switches]] — imports `interval_factor_removed`; calls `interval_factor_removed`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]], [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_belief_successor.py](../../../../../../tests/test_facet_belief_successor.py) — direct import
  - `test_a_rebuild_records_the_switch_only_at_the_tag`
  - `test_a_whole_vault_rebuild_reproduces_the_belief_and_the_uncertainty`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
  - `test_every_whole_vault_rebuild_records_the_factors_switch`

## Modification guidance

- Change projection switches policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/projection_switches.py](../../../../../../src/learnloop/substrate/projection_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
