---
title: "learnloop.config.kill_switches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/kill_switches.py"
source_paths:
  - "src/learnloop/config/kill_switches.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.kill_switches module"
  - "src/learnloop/config/kill_switches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.kill_switches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.kill_switches` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: The kill switches that restore a predecessor, as one table: config path, the tag it serves past, its default.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/kill_switches.py](../../../../../../src/learnloop/config/kill_switches.py) |
| Source lines | 210 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class KillSwitch(NamedTuple)` ([source](../../../../../../src/learnloop/config/kill_switches.py), line 29)

### Module constants

- `OUTSIDE_LEARNLOOP_TOML` ([src/learnloop/config/kill_switches.py](../../../../../../src/learnloop/config/kill_switches.py), line 41)
- `TAGGED_SWITCHES` ([src/learnloop/config/kill_switches.py](../../../../../../src/learnloop/config/kill_switches.py), line 43)
- `UNTAGGED_SWITCHES` ([src/learnloop/config/kill_switches.py](../../../../../../src/learnloop/config/kill_switches.py), line 148)

## Internal implementation anchors

- `_untagged(path: str, default: bool | float | str) -> KillSwitch` ([source](../../../../../../src/learnloop/config/kill_switches.py), line 35)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

### Repository tooling consumers

- [scripts/vault_report.py](../../../../../../scripts/vault_report.py)

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_kill_switches.py](../../../../../../tests/test_kill_switches.py) — direct import
  - `test_a_switch_at_or_below_the_floor_is_gone_or_on_the_kept_because_list`
  - `test_each_path_is_in_the_table_once_and_each_tag_is_a_real_one`
  - `test_every_row_resolves_in_the_schema_with_the_schemas_default`
  - `test_the_kept_because_list_names_only_live_switches_at_or_below_the_floor`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/kill_switches.py](../../../../../../src/learnloop/config/kill_switches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
