---
title: "learnloop.ops.content_fixes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/content_fixes.py"
source_paths:
  - "src/learnloop/ops/content_fixes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.content_fixes module"
  - "src/learnloop/ops/content_fixes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.content_fixes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.content_fixes` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: ``learnloop doctor --fix-content``: repair vault content doctor can fix safely.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/content_fixes.py](../../../../../../src/learnloop/ops/content_fixes.py) |
| Source lines | 194 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `fix_criterion_dependencies(root: Path, *, dry_run: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/content_fixes.py), line 81) — Remove criterion ``depends_on`` entries that name no criterion of the item.

### Module constants

- `FIX` ([src/learnloop/ops/content_fixes.py](../../../../../../src/learnloop/ops/content_fixes.py), line 38)

### Explicit exports

`__all__` declares:

- `FIX`
- `fix_criterion_dependencies`

## Internal implementation anchors

- `_sibling_filter(criteria: list[Any]) -> tuple[list[dict[str, Any]], list[str]]` ([source](../../../../../../src/learnloop/ops/content_fixes.py), line 41) — Per-criterion ``{criterion_id, removed, kept}`` for criteria that change, and the ids of criteria that depend on themselves (kept, reported).
- `_plain(value: Any) -> Any` ([source](../../../../../../src/learnloop/ops/content_fixes.py), line 73)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `fix_criterion_dependencies`; statically calls `fix_criterion_dependencies`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `materialize_targets`, `text_hash`; calls `materialize_targets`, `text_hash`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_to_string`; calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_synthesis_criterion_dependencies.py](../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_fix_content_dry_run_lists_the_edits_and_writes_nothing`
  - `test_fix_content_keeps_a_self_dependency_because_removing_it_changes_failure_attribution`
  - `test_fix_content_never_changes_localization_for_the_entries_it_removes`
  - `test_fix_content_removes_invalid_entries_and_keeps_the_rest_of_the_file`
  - `test_fix_content_skips_unparseable_items_and_reports_them`

## Modification guidance

- Make changes here when the responsibility remains content fixes within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/content_fixes.py](../../../../../../src/learnloop/ops/content_fixes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
