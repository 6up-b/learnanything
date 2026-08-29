---
title: "learnloop.cli.diagnosis"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/diagnosis.py"
source_paths:
  - "src/learnloop/cli/diagnosis.py"
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
  - "learnloop.cli.diagnosis module"
  - "src/learnloop/cli/diagnosis.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.diagnosis`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps diagnosis behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `diagnosis_queue`, `diagnosis_adjudicate`, `diagnosis_scoreboard`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/diagnosis.py](../../../../../../src/learnloop/cli/diagnosis.py) |
| Source lines | 267 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `diagnosis_queue(learning_object: Annotated[str | None, typer.Option('--learning-object', help='Restrict to one learning object.')]=None, reason: Annotated[str | None, typer.Option('--reason', help='Comma-separated queue strata: learner_contest, system_abstention, anchor_disagreement, incomplete_repair_mapping, sampled.')]=None, limit: Annotated[int, typer.Option('--limit')]=20, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnosis.py), line 11) — Attempts owed a diagnosis verdict, highest information first.
- `diagnosis_adjudicate(attempt_id: Annotated[str, typer.Argument(help='Attempt id (from `diagnosis queue`).')], verdict: Annotated[str, typer.Option('--verdict', help='correct | wrong_anchor | wrong_repair | should_have_abstained | correctly_abstained | should_not_have_abstained')], anchor_kind: Annotated[str | None, typer.Option('--anchor-kind', help="span|between_spans|missing_required_step|whole_answer|none. Omit on `correct`/`wrong_repair` to inherit the system's anchor.")]=None, anchor_criterion: Annotated[str | None, typer.Option('--anchor-criterion', help='Rubric criterion the anchor sits in.')]=None, anchor_quote: Annotated[str | None, typer.Option('--anchor-quote', help="Verbatim span from the learner's answer.")]=None, anchor_checkpoint: Annotated[str | None, typer.Option('--anchor-checkpoint', help='Required for anchor kind missing_required_step.')]=None, anchor_start: Annotated[int | None, typer.Option('--anchor-start', help='Character offset into the answer.')]=None, anchor_end: Annotated[int | None, typer.Option('--anchor-end')]=None, repair: Annotated[str | None, typer.Option('--repair', help='The minimal repair, in prose.')]=None, repair_class: Annotated[str | None, typer.Option('--repair-class', help='Repair class id, when the episode offered the right one.')]=None, queue_reason: Annotated[str | None, typer.Option('--queue-reason', help='Defaults to the stratum this attempt is in.')]=None, source: Annotated[str, typer.Option('--source', help='human_owner|independent_expert|deterministic_verifier')]='human_owner', rationale: Annotated[str | None, typer.Option('--rationale')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnosis.py), line 70) — Record one considered verdict on one diagnosis, append-only (A4).
- `diagnosis_scoreboard(group_by: Annotated[str, typer.Option('--group-by', help='version | queue_reason | none')]='version', vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnosis.py), line 197) — The §3 B5 metrics this store owns, over the active verdicts.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`; calls `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`

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

1. Modify [src/learnloop/cli/diagnosis.py](../../../../../../src/learnloop/cli/diagnosis.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
