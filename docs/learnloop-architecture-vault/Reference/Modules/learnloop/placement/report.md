---
title: "learnloop.placement.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/report.py"
source_paths:
  - "src/learnloop/placement/report.py"
source_commit: "18d1d1cba79de477a9785f48dd0592246d2e9138"
source_commit_timestamp: "2026-10-12T18:05:36-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.report module"
  - "src/learnloop/placement/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.report` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Report 3: the assumption report (learner field §7.3, after F2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py) |
| Source lines | 395 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `18d1d1cba79de477a9785f48dd0592246d2e9138` |
| Commit timestamp | `2026-10-12T18:05:36-04:00` |

## Public API

- `placement_report(connection: Any, vault: Any, *, now_iso: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/report.py), line 81) — Report 3 over one read-only snapshot, as of ``now_iso`` (default: now).
- `write_placement_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]` ([source](../../../../../../src/learnloop/placement/report.py), line 347)

### Module constants

- `REPORT_VERSION` ([src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py), line 28)
- `OBLIGATION_OUTCOMES` ([src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py), line 30)
- `SOURCES` ([src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py), line 37)
- `DEFAULT_MINUTES_PER_ITEM` ([src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py), line 39)
- `CONFOUNDS` ([src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py), line 41)

## Internal implementation anchors

- `_wilson(failures: int, n: int) -> list[float] | None` ([source](../../../../../../src/learnloop/placement/report.py), line 60)
- `_minutes_per_item(connection: Any) -> tuple[float, str]` ([source](../../../../../../src/learnloop/placement/report.py), line 69)
- `_full_marks_misses(rows: Any) -> int` ([source](../../../../../../src/learnloop/placement/report.py), line 312) — Resolved first reviews whose answer fell short of clean full marks: returned to learning, or kept by the diagnosis (an unassessed PF-c answer is no failure evidence, so it is not one).
- `_maintenance_outcomes(state: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/report.py), line 324) — Misses on LOs in maintenance, by how the diagnosis decided them.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]] — imports `placement_report`, `write_placement_report`; statically calls `placement_report`, `write_placement_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `PLACEMENT_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/placement/rules|learnloop.placement.rules]] — imports `RULES_VERSION`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `INTENT_ASSUMED`, `INTENT_MAINTENANCE`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_tables_present`; calls `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_tables_present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`, `pathlib`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_report3_counts_first_review_outcomes_by_reason`
  - `test_report3_keeps_the_raw_full_marks_miss_rate`
- [tests/test_placement_report.py](../../../../../../tests/test_placement_report.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/report.py](../../../../../../src/learnloop/placement/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
