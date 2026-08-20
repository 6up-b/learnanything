---
title: "learnloop.cli.fit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/fit.py"
source_paths:
  - "src/learnloop/cli/fit.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
  - "learnloop.cli.fit module"
  - "src/learnloop/cli/fit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.fit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps fit behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `fit_fsrs_command`, `fit_gate_command`, `fit_show_command`, `fit_deactivate_command`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/fit.py](../../../../../../src/learnloop/cli/fit.py) |
| Source lines | 212 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `fit_fsrs_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Fit and report without persisting.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/fit.py), line 8) — Fit FSRS weights to this learner's own review log (pure Python).
- `fit_gate_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Fit and report without persisting.')]=False, min_labels: Annotated[int, typer.Option('--min-labels', help='Minimum strong labels (overrides + ratings).')]=20, l2: Annotated[float, typer.Option('--l2')]=0.1, epochs: Annotated[int, typer.Option('--epochs')]=500, learning_rate: Annotated[float, typer.Option('--lr')]=0.5) -> None` ([source](../../../../../../src/learnloop/cli/fit.py), line 88) — Fit follow-up gate weights from manual-override + usefulness labels.
- `fit_show_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, scope: Annotated[str | None, typer.Option('--scope', help='Filter by scope.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/fit.py), line 166) — List fitted parameter sets (newest first).
- `fit_deactivate_command(scope: Annotated[str, typer.Argument(help='Fitted-parameter scope (e.g. fsrs_weights).')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, fitted_id: Annotated[str | None, typer.Option('--id', help='Deactivate only this set id.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/fit.py), line 195) — Deactivate the active fitted set for a scope; defaults apply afterwards.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] — imports `GateFitError`, `assemble_gate_training_set`, `fit_gate_weights`; calls `assemble_gate_training_set`, `fit_gate_weights`
- [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] — imports `GATE_FEATURE_VERSION`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `FOLLOWUP_GATE_SCOPE`, `FSRS_WEIGHTS_SCOPE`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] — imports `FIT_INDICES`, `FsrsFittingError`, `fit_fsrs_weights`; calls `fit_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `reconstruct_review_log`; calls `reconstruct_review_log`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

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
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/fit.py](../../../../../../src/learnloop/cli/fit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
