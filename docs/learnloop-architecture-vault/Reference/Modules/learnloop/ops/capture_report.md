---
title: "learnloop.ops.capture_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/capture_report.py"
source_paths:
  - "src/learnloop/ops/capture_report.py"
source_commit: "17b7ef6614969edd7b4dd76d99075053c1639792"
source_commit_timestamp: "2026-11-09T17:22:45-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.capture_report module"
  - "src/learnloop/ops/capture_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.capture_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.capture_report` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: ``learnloop data-capture report``: is capture working?

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py) |
| Source lines | 657 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `17b7ef6614969edd7b4dd76d99075053c1639792` |
| Commit timestamp | `2026-11-09T17:22:45-05:00` |

## Public API

- `prefilter_section(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 44) — A1: receipts by decision kind against the decisions they cover, and what they cost.
- `measurement_section(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 97) — A2: objectives by arm, and each arm's measurement states (censoring by treatment, visible).
- `outcome_section(connection: sqlite3.Connection, vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 128) — A2, A4: the derived outcomes under the vault's outcome version, and A4's skip reasons.
- `time_section(connection: sqlite3.Connection, vault: Any, repository: Any, *, as_of: str, success_correctness: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 180) — A3: the first-delayed-success proxy.
- `floor_and_pick_section(connection: sqlite3.Connection) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 195) — A5, A6, A8: the not_ready floor's draws, the delayed picks' ties, the thin supports.
- `hypothesis_marks_section(connection: sqlite3.Connection, vault: Any, repository: Any, *, success_correctness: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 485) — FG1c (spec §7) and row 6 of the router objective's logging: the exposure table's coverage, and how far the marks can be trusted, each labelled as conditional on being observed.
- `build_report(connection: sqlite3.Connection, vault: Any, repository: Any, *, as_of: str, success_correctness: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 511)
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 557) — The plain-text report.

### Module constants

- `REPORT_VERSION` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 27)
- `_INHERITS_PARENT` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 29)
- `PROBE_AGREEMENT_LABEL` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 232)
- `DELAYED_AGREEMENT_LABEL` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 234)
- `_OPINIONS` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 238)
- `POSITION_LABEL` ([src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py), line 239)

### Explicit exports

`__all__` declares:

- `REPORT_VERSION`
- `build_report`
- `lines`

## Internal implementation anchors

- `_present(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 32)
- `_active_days(values: list[str]) -> int` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 36)
- `_per_day(total: float, days: int) -> float | None` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 40)
- `_row_count(connection: sqlite3.Connection, table: str) -> int` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 124)
- `_goals(vault: Any) -> list[Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 227)
- `_exposure_coverage(connection: sqlite3.Connection, exposures: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 243) — The coverage row: how many attempts with causes since the first display had a list displayed, and what it costs.
- `_latest_marks(marks: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 266)
- `_hypothesis_keys(connection: sqlite3.Connection) -> dict[str, str]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 273) — Each hypothesis version's stable identity.
- `_observations(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 279) — Per factor, its newest answered observation, with what it measured and classified as stable identities.
- `_probe_agreement(connection: sqlite3.Connection, latest: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 305) — Marks against what a probe's answer classified.
- `_rejected_the_whole_list(latest: Mapping[str | None, Mapping[str, Any]], rows: list[Mapping[str, Any]], keys: Mapping[str, str]) -> bool` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 365) — None of these, or Not it on every cause of the list as the newest mark displayed it.
- `_opinion_reading(rows: list[Mapping[str, Any]], keys: Mapping[str, str]) -> str | None` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 377) — One attempt's opinion in ``rows`` (oldest first), or None with nothing held: one of ``_OPINIONS``.
- `_delayed_agreement(connection: sqlite3.Connection, vault: Any, repository: Any, marks: list[dict[str, Any]], success_correctness: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 391) — Marks against delayed answers on the topic under the shared definition: the opinion held before the first delayed answer that had one, so the answer is what it predicted and hindsight replaces nothing.
- `_position_rates(exposures: list[dict[str, Any]], latest: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/capture_report.py), line 454) — Mark rates by the position each cause held on the marks panel: shown once per attempt and cause.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/data_capture|learnloop.cli.data_capture]] — imports `build_report`, `lines`; statically calls `build_report`, `lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `DISCRIMINATING_OUTCOMES`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`, `receipts_on`, `serving_on`; calls `objective_receipts_on`, `receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `for_version`, `not_yet_swept`, `read`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; calls `measurement_events`, `objectives`, `objectives_present`, `receipts_present`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `all_exposures`, `all_marks`, `decode_ids`, `present`, `probe_links`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `hypothesis_marks_on`; calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `module`; calls `latest_marks`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`, `pfc_assessments`; calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]] — imports `module`; calls `lines`, `section`
- [[Reference/Modules/learnloop/router/first_delayed_success|learnloop.router.first_delayed_success]] — imports `summary`, `trajectories`; calls `summary`, `trajectories`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `delayed_outcomes_after`, `derive_router_outcomes`, `fold_measurement`, `outcome_version_for`, `servable_items_by_learning_object`; calls `delayed_outcomes_after`, `derive_router_outcomes`, `fold_measurement`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/router_objective/miss_cause_report|learnloop.router_objective.miss_cause_report]] — imports `module`; calls `lines`, `section`
- [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] — imports `module`; calls `section`
- [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] — imports `module`; calls `lines`, `section`
- [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]] — imports `module`; calls `lines`, `section`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `calibration_tag`, `miss_cause_sensor_on`, `preferences_inform_router_on`; calls `calibration_tag`, `miss_cause_sensor_on`, `preferences_inform_router_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/data_capture|learnloop.cli.data_capture]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f1_the_report_counts_the_exposures_on_record`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f6_every_arm_is_reported_on_its_frozen_objective_and_action_outcomes_apart`
  - `test_f6_the_text_report_names_both`
  - `test_f7_the_report_counts_a_replaced_check_as_unavailable`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_derivation_metric_and_report_read_the_same_before_and_after_the_sweep`
  - `test_f1_the_report_says_what_is_on_record_and_what_is_not_yet`
- [tests/test_data_capture_report.py](../../../../../../tests/test_data_capture_report.py) — direct import
  - `test_the_report_lists_each_record_with_counts_and_coverage`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f3_a_fully_measured_no_match_supports_none_of_these`
  - `test_f3_a_matched_multiple_scores_nothing_and_stays_an_independent_answer`
  - `test_f3_an_incompletely_measured_no_match_doesnt_confirm_none_of_these`
  - `test_f3_independence_is_read_from_its_own_field`
  - `test_f3_the_report_and_the_orchestrator_share_one_contract`
  - `test_f4_a_later_success_disagrees_with_a_named_gap_and_the_plain_report_says_what_came_after`
  - `test_f5_each_opinion_has_one_reading`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_a_database_below_242_says_so`
  - `test_the_report_measures_marks_against_delayed_performance`
  - `test_the_report_measures_marks_against_the_probe_each_labelled_conditional`
  - `test_the_whole_report_carries_the_section_in_json_and_in_words`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_report_section_says_each_thing_and_labels_it_self_selected`
  - `test_the_report_with_nothing_on_record_and_with_the_switch_off`
- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import
  - `test_the_capture_report_carries_the_section_and_stays_read_only`
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`

## Modification guidance

- Make changes here when the responsibility remains capture report within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/capture_report.py](../../../../../../src/learnloop/ops/capture_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
