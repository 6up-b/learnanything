---
title: "learnloop.cli.exam"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/exam.py"
source_paths:
  - "src/learnloop/cli/exam.py"
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
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.cli.exam module"
  - "src/learnloop/cli/exam.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.exam`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps exam behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `exam_reserve_command`, `exam_start_command`, `exam_answer_command`, `exam_finish_command`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/exam.py](../../../../../../src/learnloop/cli/exam.py) |
| Source lines | 192 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `exam_reserve_command(goal: Annotated[str, typer.Option('--goal', help='Goal id to reserve a held-out exam pool for.')], item_count: Annotated[int | None, typer.Option('--item-count', help="Override the goal's exam item_count.")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/exam.py), line 8)
- `exam_start_command(goal: Annotated[str, typer.Option('--goal', help='Goal id to start a held-out exam for.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/exam.py), line 32)
- `exam_answer_command(session: Annotated[str, typer.Option('--session', help='Exam session id.')], practice_item_id: Annotated[str, typer.Argument(help='Practice item id being answered.')], answer: Annotated[str | None, typer.Option('--answer', help='Learner answer markdown.')]=None, criterion_points: Annotated[str | None, typer.Option('--criterion-points', help='REFUSED: a held-out exam is not self-graded.')]=None, fatal_errors: Annotated[str | None, typer.Option('--fatal-errors', help='REFUSED: a held-out exam is not self-graded.')]=None, confidence: Annotated[int | None, typer.Option('--confidence', min=1, max=5, help='REFUSED: a held-out exam is not self-graded.')]=None, error_type: Annotated[str | None, typer.Option('--error-type', help='REFUSED: a held-out exam is not self-graded.')]=None, ai_provider: Annotated[str | None, typer.Option('--ai-provider', help='AI provider profile to use for grading.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/exam.py), line 59) — Answer one held-out exam item.
- `exam_finish_command(session: Annotated[str, typer.Option('--session', help='Exam session id to finish.')], json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/exam.py), line 167)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `resolved_codex_grade`; calls `resolved_codex_grade`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

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

1. Modify [src/learnloop/cli/exam.py](../../../../../../src/learnloop/cli/exam.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
