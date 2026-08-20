---
title: "learnloop.diagnosis.probe_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_coverage.py"
source_paths:
  - "src/learnloop/diagnosis/probe_coverage.py"
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
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_coverage module"
  - "src/learnloop/diagnosis/probe_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_coverage` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Hypothesis-contrast / family coverage report (spec §9.5, Checkpoint 3.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py) |
| Source lines | 174 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `family_coverage_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_coverage.py), line 35) — Per-LO coverage of instantiable hypothesis contrasts by admitted family/card bindings, with the §9.5 direct+shifted requirement.

### Module constants

- `DIRECT_KINDS` ([src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py), line 26)
- `SHIFTED_KINDS` ([src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py), line 27)
- `INTEGRATIVE_KINDS` ([src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py), line 30)
- `_PAIR_SEPARATION_THRESHOLD` ([src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py), line 32)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `family_coverage_report`; statically calls `family_coverage_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `InstrumentCard`, `ProbeFamilyTemplate`, `knowledge_type_tokens`, `map_episode_labels_to_slots`, `validate_and_compile_card`; calls `knowledge_type_tokens`, `map_episode_labels_to_slots`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `build_episode_hypothesis_set`; calls `build_episode_hypothesis_set`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_coverage.py](../../../../../../tests/test_probe_coverage.py) — direct import
  - `test_direct_plus_shifted_bindings_cover_a_contrast`
  - `test_report_flags_uncovered_contrasts_without_bindings`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_integrative_gap_clears_with_derivation_card`

## Modification guidance

- Change probe coverage policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_coverage.py](../../../../../../src/learnloop/diagnosis/probe_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
