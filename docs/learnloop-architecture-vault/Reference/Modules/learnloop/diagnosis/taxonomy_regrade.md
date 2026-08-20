---
title: "learnloop.diagnosis.taxonomy_regrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/taxonomy_regrade.py"
source_paths:
  - "src/learnloop/diagnosis/taxonomy_regrade.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.diagnosis.taxonomy_regrade module"
  - "src/learnloop/diagnosis/taxonomy_regrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.taxonomy_regrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.taxonomy_regrade` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Non-destructive taxonomy regrade-check (knowledge-model §16 Taxonomy row).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/taxonomy_regrade.py](../../../../../../src/learnloop/diagnosis/taxonomy_regrade.py) |
| Source lines | 118 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `run_taxonomy_regrade_checks(vault: LoadedVault, repository: Repository, client: Any, *, limit: int=20) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/taxonomy_regrade.py), line 36) — Re-grade a sample of graded attempts and report attribution regressions.

## Internal implementation anchors

- `_mechanisms(error_types: list[str | None]) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/taxonomy_regrade.py), line 28)
- `_grading_prompt_version() -> str` ([source](../../../../../../src/learnloop/diagnosis/taxonomy_regrade.py), line 117)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `run_taxonomy_regrade_checks`; statically calls `run_taxonomy_regrade_checks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`; calls `build_grading_context`, `request_grading_proposal`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_km4_taxonomy.py](../../../../../../tests/test_km4_taxonomy.py) — direct import
  - `test_taxonomy_regrade_check_no_attribution_regressions`

## Modification guidance

- Change taxonomy regrade policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/taxonomy_regrade.py](../../../../../../src/learnloop/diagnosis/taxonomy_regrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
