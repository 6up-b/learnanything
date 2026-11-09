---
title: "learnloop.diagnosis.offline_review.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/report.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.report module"
  - "src/learnloop/diagnosis/offline_review/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.report` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: The M1 report: E1-E4 and E6 from one run's scratch copy (Slice 1 §12.1, §13).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/report.py](../../../../../../../src/learnloop/diagnosis/offline_review/report.py) |
| Source lines | 1068 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `wilson(successes: int, total: int, z: float=1.96) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 39)
- `cohen_kappa(pairs: Sequence[tuple[bool, bool]]) -> float | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 49)
- `load_run(run_dir: Path) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 88)
- `current_revisions(diagnosis_rows: Sequence[Mapping[str, Any]], targets: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, str]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 180) — Per target, the judgment revision of its CURRENT candidates (F10).
- `validated_span(divergence: Mapping[str, Any], answer: str | None) -> tuple[int, int] | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 710) — Where a first divergence sits in the learner's answer, VALIDATED, or None.
- `align_events(blind: Sequence[Mapping[str, Any]], stored: Sequence[Mapping[str, Any]], answer: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 768) — One-to-one blind -> stored event alignment by validated localization and target.
- `offline_review_report(run_dir: Path, *, vault: Any | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 912)
- `render_markdown(report: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 954) — The owner-facing report: aggregates only, no learner text.

### Module constants

- `REPORT_VERSION` ([src/learnloop/diagnosis/offline_review/report.py](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 27)
- `ARM_LABELS` ([src/learnloop/diagnosis/offline_review/report.py](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 28)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `cohen_kappa`
- `load_run`
- `offline_review_report`
- `render_markdown`
- `wilson`

## Internal implementation anchors

- `_percentile(values: Sequence[float], q: float) -> float | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 62)
- `_ledger(connection, task: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 70)
- `_keep_current_revisions(data: dict[str, Any]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 199) — Drop judge rows whose inputs are no longer the target's candidates.
- `_passes(rows: Iterable[Mapping[str, Any]]) -> dict[int, list[Mapping[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 226)
- `_arm_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 233)
- `_judge_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 282)
- `_planted_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 360)
- `_links_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 454) — Pattern-link trustworthiness per arm (§12.1), from the judge's two passes.
- `_knn_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 524)
- `_grade_summary(record: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 552)
- `_grader_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 563)
- `_stored(data: Mapping[str, Any], attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 672)
- `_owner_grade_errors(data: Mapping[str, Any], grades: Mapping[str, Mapping[str, Any]]) -> list[float]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 685)
- `_occurrences(haystack: str, needle: str) -> list[int]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 702)
- `_event_anchor(attribution: Mapping[str, Any], answer: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 740) — Validated localization and targets of one error event (blind attribution or stored plan).
- `_events_correspond(blind: Mapping[str, Any], stored: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 755) — Overlapping VALIDATED spans AND compatible targets (overlapping when both name any).
- `_registry_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 807) — E4: registry_match vs the legacy misconception match, on ALIGNED events.
- `_spot_check_section(data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 879)
- `_fmt_rate(value: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/report.py), line 948)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `offline_review_report`, `render_markdown`; statically calls `offline_review_report`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `current_revisions`; statically calls `current_revisions`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `wilson`; statically calls `wilson`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `wilson`; statically calls `wilson`
- [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]] — imports `wilson`; statically calls `wilson`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolve_quote_anchor`, `resolved_rubric`; calls `resolve_quote_anchor`, `resolved_rubric`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/diagnosis_review|learnloop.db.stores.diagnosis_review]] — imports `review_rows`; calls `review_rows`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `PAIRS_OF_INTEREST`, `RATINGS`, `module`; calls `cited_links`, `diagnosis_judgment_revision`, `judged_arm_rows`, `link_judgment_revision`, `planted_judgment_revision`, `planted_statements`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `MAIN_ARMS`, `RUN_FILE`, `SCRATCH_FILE`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `math`, `pathlib`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]], [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]], [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]], [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_a_diagnosis_repaired_on_resume_is_judged_and_only_the_current_revision_counts`
  - `test_e4_aligns_events_by_localization_and_target_not_list_position`
  - `test_e4_aligns_only_on_localization_validated_in_the_answer`
  - `test_failed_probes_are_retried_on_resume_without_regenerating_paid_inputs`
  - `test_one_judge_pass_is_never_reported_as_a_confirmed_link`
  - `test_report_is_aggregates_only`
  - `test_review_round_trip_under_production_durability`
  - `test_spot_check_hides_labels_and_is_deterministic`

## Modification guidance

- Change report policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/report.py](../../../../../../../src/learnloop/diagnosis/offline_review/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
