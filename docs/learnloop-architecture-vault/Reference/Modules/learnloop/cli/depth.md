---
title: "learnloop.cli.depth"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/depth.py"
source_paths:
  - "src/learnloop/cli/depth.py"
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
  - "learnloop.cli.depth module"
  - "src/learnloop/cli/depth.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.depth`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps depth behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `depth_template_add`, `depth_template_review`, `depth_templates_list`, `depth_edges_author`, `depth_edges_list`, `depth_backfill_rungs`, `depth_edges_confirm`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/depth.py](../../../../../../src/learnloop/cli/depth.py) |
| Source lines | 155 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `depth_template_add(slug: Annotated[str, typer.Argument(help='Stable template slug (snake case).')], body_file: Annotated[Path, typer.Argument(help='JSON template body: step_deltas, exit_gate_kind, fresh_proof_kind, eligible_pattern_slugs, optional capability_transitions.')], vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 11) — Create a depth-edge template (version 1, status draft).
- `depth_template_review(version_id: Annotated[str, typer.Argument(help='Template version id.')], status: Annotated[str, typer.Option('--status', help='reviewed|retired')]='reviewed', vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 31) — Mark a template version reviewed (only reviewed versions parent instances).
- `depth_templates_list(vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 49) — List depth-edge templates and their versions.
- `depth_edges_author(commitment_id: Annotated[str, typer.Argument(help='Commitment id.')], template_version_ids: Annotated[list[str], typer.Option('--template-version', help='Reviewed template version id (repeatable).')], count: Annotated[int, typer.Option('--count')]=1, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 62) — LLM-author edge instances from reviewed templates; each is gated and stored admitted/rejected with its admission report.
- `depth_edges_list(commitment_id: Annotated[str, typer.Argument(help='Commitment id.')], status: Annotated[str | None, typer.Option('--status', help='proposed|admitted|rejected|confirmed|pinned')]=None, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 93) — List edge instances (with admission reports) for one commitment.
- `depth_backfill_rungs(subject: Annotated[str | None, typer.Option('--subject', help='Limit to one subject id.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Report classifications without writing.')]=False, vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 107) — LLM-classify legacy items into capability + task_features (deterministic validators admit each entry) and stamp the vault YAML in place.
- `depth_edges_confirm(commitment_id: Annotated[str, typer.Argument(help='Commitment id.')], instance_ids: Annotated[list[str], typer.Option('--instance', help='Admitted instance id (repeatable).')], vault: Annotated[Path | None, typer.Option('--vault')]=None) -> None` ([source](../../../../../../src/learnloop/cli/depth.py), line 135) — Confirm admitted instances and PIN them into a new immutable envelope version + milestone rows.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `DepthEdgeAuthoringError`, `author_edge_instances`, `create_edge_template`, `pin_admitted_edges`, `review_edge_template`; calls `author_edge_instances`, `create_edge_template`, `pin_admitted_edges`, `review_edge_template`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `RungBackfillError`, `backfill_item_rungs`; calls `backfill_item_rungs`

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

1. Modify [src/learnloop/cli/depth.py](../../../../../../src/learnloop/cli/depth.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
