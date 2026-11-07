---
title: "learnloop.cli.hints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/hints.py"
source_paths:
  - "src/learnloop/cli/hints.py"
source_commit: "3e98c165d53a3ded31844c9970bb462d0c71404e"
source_commit_timestamp: "2026-11-06T23:32:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.cli.hints module"
  - "src/learnloop/cli/hints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.hints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.hints` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop hints`: the hint-use report (adaptive hints H0; spec §6.3) and approach maps (H1; spec §4.3.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/hints.py](../../../../../../src/learnloop/cli/hints.py) |
| Source lines | 128 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3e98c165d53a3ded31844c9970bb462d0c71404e` |
| Commit timestamp | `2026-11-06T23:32:44-05:00` |

## Public API

- `hints_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], since: Annotated[str | None, typer.Option('--since', help='Only hints shown at or after this ISO time, or a span such as 7d or 24h.')]=None, surface: Annotated[str | None, typer.Option('--surface', help='Only one surface: practice, workbench, guided_redo, tutor or phone_practice.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/hints.py), line 46) — Hints by surface, kind and level (authored hints are the baseline): shown, items, sessions, timing, more help, the attempt's outcome and later independent success; "doesn't connect" by shortcut, outcome placements, the expertise-reversal split, help abuse and avoidance counts, a…
- `maps_build(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], item: Annotated[str | None, typer.Option('--item', help='Only this practice item.')]=None, family: Annotated[str | None, typer.Option('--family', help='Only the items of this practice family.')]=None, lo: Annotated[str | None, typer.Option('--lo', help='Only the items of this learning object.')]=None, limit: Annotated[int | None, typer.Option('--limit', min=1, help='Build at most this many maps in this run.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the plan and the estimate; retrieve, call and write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/hints.py), line 99) — Build approach maps for active items that have none for their current revision (all items, or one --item, --family or --lo).

### Module constants

- `_RELATIVE` ([src/learnloop/cli/hints.py](../../../../../../src/learnloop/cli/hints.py), line 31)
- `_SURFACES` ([src/learnloop/cli/hints.py](../../../../../../src/learnloop/cli/hints.py), line 32)

## Internal implementation anchors

- `_since(value: str | None, now: datetime) -> str | None` ([source](../../../../../../src/learnloop/cli/hints.py), line 35)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `hints_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `backfill`, `select_items`; calls `backfill`, `select_items`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `build_maps_report`; calls `build_maps_report`
- [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]] — imports `build_hints_report`, `item_caps`; calls `build_hints_report`, `item_caps`
- [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]] — imports `build_workbench_report`; calls `build_workbench_report`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `planning_repository`; calls `planning_repository`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `pathlib`, `re`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

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

1. Modify [src/learnloop/cli/hints.py](../../../../../../src/learnloop/cli/hints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
