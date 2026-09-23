---
title: "learnloop.cli.data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/data.py"
source_paths:
  - "src/learnloop/cli/data.py"
source_commit: "50b84bb1b401a44d65419807c17d886fb50dc8f3"
source_commit_timestamp: "2026-09-23T16:09:38-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
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
  - "learnloop.cli.data module"
  - "src/learnloop/cli/data.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.data`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.data` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Local collection inspection and reproducible dataset artifacts.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/data.py](../../../../../../src/learnloop/cli/data.py) |
| Source lines | 219 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `50b84bb1b401a44d65419807c17d886fb50dc8f3` |
| Commit timestamp | `2026-09-23T16:09:38-04:00` |

## Public API

- `data_quality(vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/data.py), line 37) — Read-only JSON coverage report, with current-version denominators.
- `usage(vault: Annotated[Path | None, typer.Option('--vault')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the stable JSON report.')]=False, since: Annotated[str | None, typer.Option('--since', help='Only operations started at or after this ISO date or time (UTC when no offset).')]=None, purpose: Annotated[str | None, typer.Option('--purpose', help='Only operations whose root purpose starts with this prefix.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/data.py), line 53) — Read-only token and cost report from model-call receipts, with synthesis budget ratios.
- `render_usage_report(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/cli/data.py), line 80) — A terminal-width summary of the JSON report, section by section.
- `dataset_export(output: Annotated[Path, typer.Argument(help='New local output directory.')], split_policy: Annotated[str, typer.Option('--split-policy', help=_SPLIT_POLICY_HELP)]=DEFAULT_SPLIT_POLICY, embargo: Annotated[str, typer.Option('--embargo', help='Temporal policy only: a duration such as 7d, 36h, 90m, 30s or 0 (no embargo).')]='7d', vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/data.py), line 179) — Back up an active database and export evidence, labels and split metadata.
- `adjudicate_remediation(attempt_id: Annotated[str, typer.Argument()], false_remediation: Annotated[bool, typer.Option('--false-remediation/--appropriate-remediation')], evidence: Annotated[Path, typer.Option('--evidence', help="JSON list of retained {table, id} evidence references; id is the table's primary-key value.")], verifier_version: Annotated[str, typer.Option('--verifier-version')], author_kind: Annotated[str, typer.Option('--author-kind', help='human or machine')]='human', vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/data.py), line 201) — Append an evidence-backed label; corrections append another adjudication.

### Module constants

- `_SPLIT_POLICY_HELP` ([src/learnloop/cli/data.py](../../../../../../src/learnloop/cli/data.py), line 44)
- `_TOKEN_LABELS` ([src/learnloop/cli/data.py](../../../../../../src/learnloop/cli/data.py), line 71)

## Internal implementation anchors

- `_loaded_vault(vault: Path | None) -> LoadedVault` ([source](../../../../../../src/learnloop/cli/data.py), line 23)
- `_sqlite_path(loaded: LoadedVault) -> Path` ([source](../../../../../../src/learnloop/cli/data.py), line 27)
- `_fail(exc: BaseException) -> typer.Exit` ([source](../../../../../../src/learnloop/cli/data.py), line 31)
- `_usage_heading(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/cli/data.py), line 89)
- `_number(value: Any) -> str` ([source](../../../../../../src/learnloop/cli/data.py), line 96)
- `_render_purposes(groups: list[dict[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/cli/data.py), line 104)
- `_ratio_text(value: int | None, ratio: float | None, budget: int | None, name: str) -> str` ([source](../../../../../../src/learnloop/cli/data.py), line 129)
- `_render_synthesis_runs(section: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/cli/data.py), line 138)
- `_render_coverage(rows: list[dict[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/cli/data.py), line 163)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `app`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `_dump`, `_load_vault_or_exit`, `_root`; calls `_dump`, `_load_vault_or_exit`, `_root`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `data_quality_report`; calls `data_quality_report`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `DEFAULT_SPLIT_POLICY`, `export_dataset`, `parse_embargo`; calls `export_dataset`, `parse_embargo`
- [[Reference/Modules/learnloop/substrate/model_usage|learnloop.substrate.model_usage]] — imports `SYNTHESIS_BUDGET_FIELDS`, `model_usage_report`; calls `model_usage_report`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `VaultLockError`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/data.py](../../../../../../src/learnloop/cli/data.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
