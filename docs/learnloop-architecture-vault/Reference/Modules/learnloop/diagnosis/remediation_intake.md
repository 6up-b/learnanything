---
title: "learnloop.diagnosis.remediation_intake"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/remediation_intake.py"
source_paths:
  - "src/learnloop/diagnosis/remediation_intake.py"
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
  - "learnloop.diagnosis.remediation_intake module"
  - "src/learnloop/diagnosis/remediation_intake.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.remediation_intake`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.remediation_intake` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Three-way learner-error intake: repair, diagnose, or read first.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/remediation_intake.py](../../../../../../src/learnloop/diagnosis/remediation_intake.py) |
| Source lines | 34 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `classify_intake(*, misconception: MisconceptionRecord | None=None, facet_state_label: str | None=None, has_source_exposure: bool=False, unresolved_cause: bool=False, repeated_failure_despite_coverage: bool=False, mechanism_is_misconception: bool=False) -> IntakeRoute` ([source](../../../../../../src/learnloop/diagnosis/remediation_intake.py), line 13) — Route without ever promoting a one-off mechanism event into a case.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MisconceptionRecord`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_misconception_transitions_intake.py](../../../../../../tests/test_misconception_transitions_intake.py) — direct import
  - `test_durable_row_wins_over_every_other_signal`
  - `test_lone_misconception_mechanism_event_is_not_a_repair_case`
  - `test_repair_requires_a_durable_active_or_resolving_registry_row`
  - `test_unexamined_facet_with_no_exposure_routes_to_read_first`
  - `test_unresolved_cause_and_repeated_failure_route_to_diagnose`

## Modification guidance

- Change remediation intake policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/remediation_intake.py](../../../../../../src/learnloop/diagnosis/remediation_intake.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
