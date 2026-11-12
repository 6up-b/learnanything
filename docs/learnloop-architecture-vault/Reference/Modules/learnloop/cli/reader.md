---
title: "learnloop.cli.reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/reader.py"
source_paths:
  - "src/learnloop/cli/reader.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.cli.reader module"
  - "src/learnloop/cli/reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.reader` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop reader report`: the Reader's workflow funnel (reader workbench RW1a).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/reader.py](../../../../../../src/learnloop/cli/reader.py) |
| Source lines | 220 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `reader_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], since: Annotated[str | None, typer.Option('--since', help='Only activity at or after this ISO time, or a span such as 7d or 24h.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/reader.py), line 38) — Workflows with denominators: selection -> action -> result -> back to reading, inquiries, detours (return rate, cost), proactive load, waiting behaviour, visits.
- `figure_checks(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], recheck: Annotated[bool, typer.Option('--recheck', help='Recheck stored grammar figures by code (no model client): those with no check at the current certification version.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='With --recheck: look at every stored grammar figure and report by reason key; write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/reader.py), line 96) — Reader RW5c: what "matches the book's equation (checked)" covers (spec §12).
- `cues_discover(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], source: Annotated[str, typer.Option('--source', help='The source (or extraction) to discover cue links for.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='List the targets, their keyword shortlists and a spend plan; call and write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/reader.py), line 149) — Find a source's discovered margin-cue links now (what opening it in the Reader does in the background): the open targets, each one's shortlist and one cue judgment each, under cues.max_calls_per_source_open (every request, a retry included) and cues.max_daily_cost_usd (query emb…
- `reader_label_roles(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], source: Annotated[str, typer.Option('--source', help='The source (or extraction) to label.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Give the batch plan, its estimated tokens and dollars and the cap; call and write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/reader.py), line 186) — Label a source's passages with instructional roles now (RW4e).

### Module constants

- `_RELATIVE` ([src/learnloop/cli/reader.py](../../../../../../src/learnloop/cli/reader.py), line 24)

## Internal implementation anchors

- `_since(value: str | None, now: datetime) -> str | None` ([source](../../../../../../src/learnloop/cli/reader.py), line 27)
- `_plan_providers(loaded: object) -> list[str]` ([source](../../../../../../src/learnloop/cli/reader.py), line 140) — RW5d P5: the vault's plan profiles (the prefetch block reads the plan's load from their receipts).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `reader_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `add_report_block`, `plan_providers`, `pressed_waits_on`; calls `add_report_block`, `plan_providers`, `pressed_waits_on`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `row_withheld`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `add_report_block`, `module`; calls `add_report_block`, `audit`, `coverage`, `enabled`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `planning_repository`; calls `planning_repository`
- [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]] — imports `build_reader_report`; calls `build_reader_report`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `discover`; calls `discover`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `skipped_section_learning_objects`; calls `skipped_section_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `label_roles`; calls `label_roles`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `pathlib`, `re`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

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

1. Modify [src/learnloop/cli/reader.py](../../../../../../src/learnloop/cli/reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
