---
title: "learnloop.cli.placement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/placement.py"
source_paths:
  - "src/learnloop/cli/placement.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.placement module"
  - "src/learnloop/cli/placement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.placement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.placement` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop placement status` and `learnloop eval placement` (report 3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/placement.py](../../../../../../src/learnloop/cli/placement.py) |
| Source lines | 101 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `placement_status(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/placement.py), line 34) — Whether placement serves, and every open assumed-known LO with its check date.
- `placement_eval(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault copy; read-only, no model calls.')], output_dir: Annotated[Path, typer.Option('--output', '--output-dir', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/placement.py), line 76) — Report 3: first-review miss rate by source, returns to learning, minutes saved.

## Internal implementation anchors

- `_load(vault: Path)` ([source](../../../../../../src/learnloop/cli/placement.py), line 23)
- `_emit(payload: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/placement.py), line 29)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `placement_app`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `placement_eval`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]] — imports `placement_report`, `write_placement_report`; calls `placement_report`, `write_placement_report`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `assumption_summary`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`; calls `assumption_summary`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]], [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_append_units.py](../../../../../../tests/test_cli_append_units.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/placement.py](../../../../../../src/learnloop/cli/placement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
