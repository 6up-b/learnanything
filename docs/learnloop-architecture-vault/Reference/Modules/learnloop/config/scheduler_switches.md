---
title: "learnloop.config.scheduler_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/scheduler_switches.py"
source_paths:
  - "src/learnloop/config/scheduler_switches.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.config.scheduler_switches module"
  - "src/learnloop/config/scheduler_switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.scheduler_switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.scheduler_switches` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: The scheduler's surprise interval switch.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/scheduler_switches.py](../../../../../../src/learnloop/config/scheduler_switches.py) |
| Source lines | 16 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `interval_factor_removed(config: Any) -> bool` ([source](../../../../../../src/learnloop/config/scheduler_switches.py), line 11) — §5.1: True when the FSRS interval carries no surprise factor (the switch).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `interval_factor_removed`; statically calls `interval_factor_removed`
- [[Reference/Modules/learnloop/substrate/projection_switches|learnloop.substrate.projection_switches]] — imports `interval_factor_removed`; statically calls `interval_factor_removed`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/substrate/projection_switches|learnloop.substrate.projection_switches]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro1_interval_factor.py](../../../../../../tests/test_ro1_interval_factor.py) — direct import
  - `test_the_gate_is_the_tag_and_the_switch`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
  - `test_every_switch_combination_moves_exactly_its_own_part`
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_each_switch_is_classified_and_reads_off_or_below_the_tag`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/scheduler_switches.py](../../../../../../src/learnloop/config/scheduler_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
