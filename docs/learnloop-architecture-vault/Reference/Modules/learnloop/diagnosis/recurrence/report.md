---
title: "learnloop.diagnosis.recurrence.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/report.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/report.py"
source_commit: "171ae5a5ed15b7627add8b2e512d0c0e91c5f3da"
source_commit_timestamp: "2026-10-13T09:11:59-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.report module"
  - "src/learnloop/diagnosis/recurrence/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.report` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The M3 signals report (Slice 2 §3.7), after ~2-4 weeks at ``mvp-0.12``.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/report.py](../../../../../../../src/learnloop/diagnosis/recurrence/report.py) |
| Source lines | 295 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `171ae5a5ed15b7627add8b2e512d0c0e91c5f3da` |
| Commit timestamp | `2026-10-13T09:11:59-04:00` |

## Public API

- `m3_report(vault: LoadedVault, repository: Repository, *, audit_sample: int=10) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 217)
- `render_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 241)

### Module constants

- `REPORT_VERSION` ([src/learnloop/diagnosis/recurrence/report.py](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 33)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `m3_report`
- `render_markdown`

## Internal implementation anchors

- `_rows(repository: Repository, sql: str, params: tuple[Any, ...]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 36)
- `_switch_time(repository: Repository) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 41)
- `_escalation_taps(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 50)
- `_sample(groups: Mapping[str, list[dict[str, Any]]], size: int) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 72)
- `_group_precision(repository: Repository, *, audit_sample: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 77)
- `_repeated_episodes(repository: Repository, switch_at: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 117) — Unresolved-cause factors (diagnostic episodes) per recurring cause.
- `_next_outcomes(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 167) — The next attempt on the same LO after a diagnosed failure (directional).
- `_review_volume(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 204)
- `_fmt(value: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/report.py), line 233)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `m3_report`, `render_markdown`; statically calls `m3_report`, `render_markdown`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `wilson`; calls `wilson`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/recurrence|learnloop.recurrence]] — imports `key_for_statement`; calls `key_for_statement`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recurrence_commands.py](../../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_m3_report_reads_ledgers_only`

## Modification guidance

- Change report policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/report.py](../../../../../../../src/learnloop/diagnosis/recurrence/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
