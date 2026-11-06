---
title: "learnloop.evsi_calibration.forecast_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/forecast_report.py"
source_paths:
  - "src/learnloop/evsi_calibration/forecast_report.py"
source_commit: "54da4d9c68a7e7cb49271ea97deeb431f758037b"
source_commit_timestamp: "2026-11-05T23:22:13-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.evsi_calibration.forecast_report module"
  - "src/learnloop/evsi_calibration/forecast_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.forecast_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.forecast_report` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: `learnloop diagnosis calibration`: how good were the saved forecasts?

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py) |
| Source lines | 871 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `54da4d9c68a7e7cb49271ea97deeb431f758037b` |
| Commit timestamp | `2026-11-05T23:22:13-05:00` |

## Public API

- `next_observation(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 451) — The frozen rule's observation: ``{attempt, intervening, facet}`` or a reason.
- `resolve_diagnosis(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 481)
- `resolve_repair(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 521)
- `resolve_lesson_check(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 581) — ``lesson_check_correct``: resolved on the check's own attempt (``lesson_checks`` by lesson and check ref) under its current grade; a withdrawn check is censored, a held grade waits, an ungraded one is pending, and a check never answered in a closed lesson is censored.
- `resolve_lesson_step(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 612) — ``lesson_step_retained``: resolved on the first qualifying cold outcome on the node's LO after the forecast (``learner.lesson_weight.qualifying_outcomes``: the outcome the pool weight learns from, held grades left out until released); pending until one exists.
- `check_outcome_rows(connection: sqlite3.Connection, vault: LoadedVault, *, since: str | None) -> list[tuple[dict[str, Any], dict[str, Any]]]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 634) — ``voi_forecasts`` as receipts of the family, each with its resolution.
- `summarize(rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 759) — Per kind, per forecaster: the honest n and the reliability tables.
- `resolved_receipts(vault: LoadedVault, *, since: str | None=None, include_checks: bool=False) -> list[tuple[dict[str, Any], dict[str, Any]]]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 806) — Every receipt with its read-time resolution (read-only, one snapshot).
- `forecast_calibration_report(vault: LoadedVault, *, since: str | None=None, include_checks: bool=True) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 818) — The report (read-only, one snapshot).

### Module constants

- `REPORT_VERSION` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 85)
- `SMALL_N` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 88)
- `RESOLVED` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 90)
- `PENDING` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 91)
- `HELD` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 92)
- `CENSORED` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 93)
- `_CHECK_PENDING` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 97)
- `_BINDINGS` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 423)
- `_MEASURED` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 518)
- `_LESSON_RIGHT` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 574)
- `_BINARY_EVENT` ([src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 678)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `SMALL_N`
- `check_outcome_rows`
- `forecast_calibration_report`
- `next_observation`
- `resolved_receipts`
- `resolve_diagnosis`
- `resolve_lesson_check`
- `resolve_lesson_step`
- `resolve_repair`
- `summarize`

## Internal implementation anchors

- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 100)
- `_has(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 109)
- `_resolution(state: str, reason: str, **extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 115)
- `class _Ledgers` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 122) — Lazy, read-only views every resolver shares (one snapshot).
- `_plan_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 354) — Why the attempt's plan presentation does not bind it (None: it does): router R2a's own write-time rule, read again (it exists, is of the item, no other attempt answered it).
- `_probe_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 366) — Why the attempt's probe presentation does not bind it: it must exist, be of the item, and this attempt be the one that answered it.
- `_scheduler_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 390) — Why the attempt's scheduler offer does not bind it: the exact offer link the attempt store writes (``_link_attempt_to_scheduler_candidate``) and the data-quality report checks: a returned candidate of the item, in the attempt's slate and session, generated no later than the answ…
- `_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 430) — The exact receipt the attempt answered (Codex review F4): the first of its references whose record verifies, ``(label, {})``; else ``(None, {label: why})`` for every reference it carries that establishes nothing.
- `_lesson_emission(correctness: Any) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 577)
- `_round(value: float | None, digits: int=4) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 673)
- `_score(kind: str, rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 683)
- `_splits(rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]], key: Callable[[Mapping[str, Any]], Any], event: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 741)
- `_resolve_all(connection: sqlite3.Connection, vault: LoadedVault, *, since: str | None, include_checks: bool) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], _Ledgers]` ([source](../../../../../../src/learnloop/evsi_calibration/forecast_report.py), line 783)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]] — imports `forecast_calibration_report`; statically calls `forecast_calibration_report`
- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `resolved_receipts`; statically calls `resolved_receipts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/facet_identity|learnloop.db.stores.facet_identity]] — imports `settled_merge_rows`; calls `settled_merge_rows`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `module`; calls `has_table`, `list_receipts`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `bindable_presentation`; calls `bindable_presentation`
- [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] — imports `module`; calls `has_table`, `list_forecasts`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `MEASURED_COLD_DISPOSITIONS`, `NON_LEARNER_VALIDITY`, `effective_cold_outcome`; calls `effective_cold_outcome`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `module`; calls `LedgerOutcomeAdapter`, `RouterOutcomeAdapter`, `_join`
- [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]] — imports `reliability`; calls `reliability`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `ROLE_WEIGHTS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `facet_outcome_bucket`; calls `facet_outcome_bucket`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `qualifying_outcomes`; calls `qualifying_outcomes`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`, `unassessed_evidence_row`; calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `module`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `contextlib`, `json`, `math`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnosis|learnloop.cli.diagnosis]], [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_held_grade_resolves_nothing_until_a_regrade_releases_it`
  - `test_a_repair_without_an_independent_surface_is_censored_at_birth`
  - `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task`
  - `test_the_calibration_report_on_a_seeded_vault`
  - `test_the_kill_switch_writes_no_receipt`
  - `test_the_report_reads_a_vault_without_receipts_as_empty`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_a_regraded_observation_resolves_its_graded_contract_in_the_forecast_reader`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f13_a_withdrawn_check_censors_its_forecast`
  - `test_f13_lesson_forecasts_have_resolvers`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_the_forecast_report_resolves_it_on_the_first_cold_outcome`

## Modification guidance

- Make changes here when the responsibility remains forecast report within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/forecast_report.py](../../../../../../src/learnloop/evsi_calibration/forecast_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
