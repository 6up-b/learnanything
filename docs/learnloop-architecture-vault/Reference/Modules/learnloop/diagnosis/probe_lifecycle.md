---
title: "learnloop.diagnosis.probe_lifecycle"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_lifecycle.py"
source_paths:
  - "src/learnloop/diagnosis/probe_lifecycle.py"
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
  - "learnloop.diagnosis.probe_lifecycle module"
  - "src/learnloop/diagnosis/probe_lifecycle.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_lifecycle`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_lifecycle` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Family-version and instance lifecycle transitions (§9.7, Checkpoint 4.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_lifecycle.py](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py) |
| Source lines | 299 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class LifecycleTransitionError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 33)
- `class FamilyLifecycleMetrics` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 38)
- `class FamilyLifecycleAssessment` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 49)
  - `as_dict(self) -> dict[str, Any]` (line 57; public)
- `family_lifecycle_metrics(repository: Repository, family_id: str, version: int) -> FamilyLifecycleMetrics` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 76) — Real-learner evidence for one family version (synthetic rows excluded).
- `evaluate_family_lifecycle(vault: LoadedVault, repository: Repository, family_id: str, version: int) -> FamilyLifecycleAssessment` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 108) — Recommend a transition for one family version against the §9.7 gates.
- `apply_family_lifecycle_transition(repository: Repository, *, family_id: str, version: int, to_status: str, reason: dict[str, Any] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 190) — Apply one explicit transition and persist its lifecycle event.
- `revise_family_version(repository: Repository, family_id: str, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 223) — Create the next version as a draft copy of the latest template (§9.7).
- `retire_probe_instance(repository: Repository, practice_item_id: str, *, reason: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 263) — Retire one generated instance: deactivate the item and mark every family link's review status.
- `family_lifecycle_overview(vault: LoadedVault, repository: Repository) -> list[FamilyLifecycleAssessment]` ([source](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 291) — Assessment for every stored family version, for the CLI report.

### Module constants

- `ALLOWED_TRANSITIONS` ([src/learnloop/diagnosis/probe_lifecycle.py](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py), line 25)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `LifecycleTransitionError`, `apply_family_lifecycle_transition`, `evaluate_family_lifecycle`, `family_lifecycle_overview`, `revise_family_version`; statically calls `apply_family_lifecycle_transition`, `evaluate_family_lifecycle`, `family_lifecycle_overview`, `revise_family_version`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `eig_calibration_report`, `grading_confusion_report`; calls `eig_calibration_report`, `grading_confusion_report`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `ProbeFamilyTemplate`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_lifecycle.py](../../../../../../tests/test_probe_lifecycle.py) — direct import
  - `test_instance_retirement_deactivates_without_touching_history`
  - `test_provisional_family_needs_evidence_before_trust`
  - `test_regrade_disagreement_recommends_retirement`
  - `test_revision_creates_next_draft_version`
  - `test_transitions_follow_the_allowed_graph`

## Modification guidance

- Change probe lifecycle policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_lifecycle.py](../../../../../../src/learnloop/diagnosis/probe_lifecycle.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
