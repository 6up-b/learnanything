---
title: "learnloop.diagnosis.split.reports"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/reports.py"
source_paths:
  - "src/learnloop/diagnosis/split/reports.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.reports module"
  - "src/learnloop/diagnosis/split/reports.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.reports`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.reports` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: End-of-M2 report: E5, E7 and the §12.3 learner signals (Slice 1 §13).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/reports.py](../../../../../../../src/learnloop/diagnosis/split/reports.py) |
| Source lines | 350 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `m2_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 258)
- `render_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 296)

### Module constants

- `REPORT_VERSION` ([src/learnloop/diagnosis/split/reports.py](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 22)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `m2_report`
- `render_markdown`

## Internal implementation anchors

- `_seconds(start: str | None, end: str | None) -> float | None` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 25)
- `_quantiles(values: Sequence[float]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 33)
- `_rows(repository: Repository, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 45)
- `_e5(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 50) — Would-merge (shadow): do validated citations / kNN neighbours find recurrences exact strings split, and are they right when audited?
- `_e7(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 95)
- `_signals(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 182)
- `_e2_prior_analysis_arms(repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 235) — E2's ``anchoring_suspect`` rate per prior-analysis arm (learner-blindness relax): completed live diagnoses, grouped by the arm their context receipt records (``unassigned``: written before the arm existed).
- `_fmt(rate: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/reports.py), line 290)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `m2_report`, `render_markdown`; statically calls `m2_report`, `render_markdown`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `wilson`; calls `wilson`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_async_router.py](../../../../../../../tests/test_diagnosis_async_router.py) — direct import
  - `test_the_lag_rate_is_over_every_serve_that_followed_a_diagnosed_answer`
- [tests/test_diagnosis_reports.py](../../../../../../../tests/test_diagnosis_reports.py) — direct import
  - `test_m2_report_aggregates_without_learner_text`
  - `test_m2_report_counts_logical_diagnosis_calls_and_their_turns`
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_report_reads_anchoring_suspect_per_arm`

## Modification guidance

- Change reports policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/reports.py](../../../../../../../src/learnloop/diagnosis/split/reports.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
