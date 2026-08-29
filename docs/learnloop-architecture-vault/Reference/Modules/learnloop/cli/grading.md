---
title: "learnloop.cli.grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/grading.py"
source_paths:
  - "src/learnloop/cli/grading.py"
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
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.grading module"
  - "src/learnloop/cli/grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps grading behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `grading_reviews`, `grading_adjudicate`, `grading_receipt`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/grading.py](../../../../../../src/learnloop/cli/grading.py) |
| Source lines | 133 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `grading_reviews(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 10) — List pending grade reviews, influence-ordered (§5).
- `grading_adjudicate(interpretation_id: Annotated[str, typer.Argument(help='Grade interpretation id (from `grading reviews`).')], resolved_class: Annotated[str | None, typer.Option('--resolved-class')]=None, source: Annotated[str, typer.Option('--source', help='human_owner|independent_expert|learner_clarification|deterministic_key')]='human_owner', rationale: Annotated[str | None, typer.Option('--rationale')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 33) — Adjudicate one grade append-only (§4.4/§5): appends a new interpretation head, repoints the observation, emits measurement events, and rebuilds projections.
- `grading_receipt(attempt_id: Annotated[str, typer.Argument(help='Attempt id to trace.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=True) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 88) — The §5 measurement receipt: response -> raw grade -> interpretation -> projection, plus the calibration lineage.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `append_adjudication`; calls `append_adjudication`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `record_reinterpretation_if_changed`; calls `record_reinterpretation_if_changed`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
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

1. Modify [src/learnloop/cli/grading.py](../../../../../../src/learnloop/cli/grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
