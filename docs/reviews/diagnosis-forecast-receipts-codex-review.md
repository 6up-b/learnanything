# Saved diagnosis forecasts: Codex review and fixes

**Stage:** `diagnosis-forecast-receipts` (owner go-ahead 2026-10-15; the stage record is `docs/reviews/diagnosis-forecast-receipts.md`).
**Branch:** `diagnosis/forecast-receipts`, base `37a2a7e5f` (main, `mvp-0.25`, migrations to 204); reviewed range `37a2a7e5f..9633d992e`.
**Review:** Codex, job `20261015-174858-CqkWZQ`: four Medium findings, each reproduced by the reviewer with production functions on in-memory SQLite.
**Fix commits:** `880aef2b3` (code and tests), `4d3cdc9d2` (references, stage record corrected), this record.
**Migration:** none added or changed (230 stays the placeholder; its comments still hold). **Model calls:** none (fakes only). **Paid calls:** none.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | An error on another facet resolves the forecast as recurrence | fixed | `880aef2b3` | `test_f1_an_error_on_another_facet_is_not_the_forecast_facets_recurrence`, `test_f1_an_unassessed_target_facet_censors_whatever_errors_another_facet_shows` |
| F2 | Medium | Editing today's rubric rewrites historical forecast outcomes | fixed. One sub-item rejected: "preserve that reference when regrading" (reason in §F2) | `880aef2b3` | `test_f2_editing_todays_rubric_never_rewrites_a_regraded_self_grade` (the review's scenario), `test_f2_a_grade_that_cites_no_contract_is_never_read_against_todays_rubric`; `test_a_regrade_re_resolves_the_forecast` now runs on a method-explicit item |
| F3 | Medium | Repair predictions learn from outcomes that are now held or corrected | fixed | `880aef2b3` | `test_f3_a_cold_success_regraded_to_failure_is_measured_as_a_failure`, `test_f3_a_cold_success_whose_grade_is_now_held_is_not_measured` |
| F4 | Medium | A nonempty scheduler ID is accepted as an exact binding | fixed | `880aef2b3` | `test_f4_a_reference_that_establishes_no_administration_censors_the_forecast[dangling_candidate, another_items_candidate, dangling_probe]`; guard `test_f4_an_answer_to_a_scheduler_offer_resolves_through_it` |

No High finding was raised.

## F1: the recurrence is the facet's, and only once the facet is assessed

**Reproduced.** A forecast on `recall` (pattern: the diagnosed error type). The next presented answer earns full credit on `result` (recall). `setup` (compute) is marked down with the same error type, attributed to compute (`target_evidence_families = [compute]`, `target_criterion_ids = [setup]`). On `9633d992e` it resolved `same_error`, because `shows_pattern` searched every error on the attempt. A second case: PF-c records `result` unverified, so recall is unassessed, while the same pattern shows on compute. That also resolved `same_error`, so the unassessed censoring was bypassed.

**Fixed.** `resolve_diagnosis` now reads the facet's outcome under the graded contract first. Unassessed, unmapped or with no known contract, the forecast is censored (or pending when ungraded) before any pattern is read. Only then does `facet_shows_pattern` count an error event, and only when its recorded attribution names the facet. The attribution follows the grading's own rule (`attempts._attach_contract`'s `event_matches_criterion`):
* the facets it names (`target_evidence_families`, a `facet_capability` target);
* else the facets of the contract criteria it names (`target_criterion_ids`, a `criterion` target);
* an attribution the grader scoped off the learner (`cause_scope` item contract, grader interpretation or interaction context, the writer's own `NON_LEARNER_VALIDITY`), or whose facet write it blocked, names none;
* an error that names nothing counts for the facet only when the contract measures no other facet.

The resolution now carries `facet_outcome` for `same_error` too. The frozen rule is `next_unseen_qualifying_presented_attempt_on_facet_v2`, and the receipt's `emissions.same_error` text says "the facet is assessed and an error attributed to it shows the pattern".

**Tests.** The cross-facet answer resolves `pass` with facet outcome 1.0. The PF-c answer is censored `facet_unassessed`.

## F2: the contract the grade cites, or censored, never today's content

**Reproduced** (the review's scenario, on `9633d992e`): a self-graded next answer (it cites its presentation's contract) was regraded by AI. The item has no frozen method, so its tier-1 rows were superseded and the regrade's rows cite no contract. The resolver compiled today's item: `pass`, facet outcome 1.0. Editing the item's `result` criterion from 2 to 4 points, with no new answer, then gave `other_error`, facet outcome 0.5.

**A second case found while fixing.** An AI-graded answer regraded by AI keeps its original rows: regrades supersede only tier-1 rows. The resolver took "the first version any surviving row cites", so it read the regrade's points against the original presentation contract. The regrade never cited that contract; it read the item as it was at regrade time.

**Fixed.** `current_evidence` now applies the rule EVSI calibration's resolver already uses (`live_report`, review F5): the contract is the one version that the winning row of every criterion cites. Rows citing none, or citing different versions, give `graded_contract_unknown`. `_contract` never compiles the current item; the `compile_assessment_contract` fallback is gone. Consequences:
* a live grade cites its presentation's contract, so a later rubric edit changes nothing (tested);
* a method-explicit item's regrade cites the contract it read (`regrade_reads_contract`), so it re-resolves;
* any other regrade, including the one that releases a held grade, censors the forecast `graded_contract_unknown`. That is the honest label: what the grade was read under is not on record.

`test_a_held_grade_resolves_nothing_until_a_regrade_releases_it` now ends in that censoring. A hold cannot be made on a method item, because the method criterion stays assessed on a divergent route. `test_a_regrade_re_resolves_the_forecast` runs on a method-explicit item (`mvp-0.25` with a required method) and asserts that the regrade cites its contract.

**Rejected sub-item:** "Preserve that reference when grading or regrading". Live grading already cites its contract (`_attach_contract` snapshots one when none was frozen). Making regrades of items without a frozen method cite one is a grading change, outside this logging-only stage:
* `regrade_reads_contract` (method-explicit re-review F1) and canonical sources §7.3a deliberately have those regrades read the item as it is now and cite nothing;
* `attempt_graded_contract` and `answered_contracts` rely on that, reading the first cited version as the contract the learner answered;
* replay would read such regrades differently after a later edit;
* the parallel provenance landing touches the same grading transaction.

It is open question 1, with censoring as the default.

## F3: the repair forecaster's measured sample reads cold outcomes as they stand

**Reproduced.** After one repair cycle measured a `cold_success` (class `rc_stub`), the next repair forecast for the class predicted 7/9 (one measured success). That stayed 7/9 after the cold attempt was regraded to a failure, and after a regrade held its grade, where the held predicate confirmed the hold.

**Fixed.** `diagnosis.forecast_receipts.effective_cold_outcome(connection, cold_attempt_id, threshold)` is now the one rule for a measured disposition's outcome as the cold grade stands:
* held for review (THE held predicate) is no outcome;
* a grade that assesses nothing is no outcome;
* otherwise the correctness against the threshold decides.

The writer's `_measured_cold_outcomes` reads every `cold_success`/`cold_failure` row's cold attempt through it, at receipt time inside the primed attempt's transaction, so it is as of receipt creation. Excluded rows are counted by reason in `forecast.measured.excluded` and never sampled. The report's `resolve_repair` reads the same function. Issued receipts are unchanged. The forecaster version is now `repair_class_cold_rate_v2`.

**Tests.** Success regraded to failure: class 0/1, pooled 0/1, p = 2/9. Held: nothing measured, so the no-measurement prior p = 0.5.

## F4: a reference binds only when its record verifies

**Reproduced.** The next qualifying answer carried no presentation, and its `scheduler_candidate_id` was set to `NONEXISTENT_CANDIDATE`. The column has no foreign key, and an older or out-of-band writer can leave such a value. The forecast resolved `pass` through `scheduler_candidate`. A candidate of another item, and a dangling `probe_presentation_id` (no foreign key either), resolved the same way.

**Fixed.** `_binding` tries the attempt's references in order and binds through the first whose record verifies:
* `plan_presentation_id`: router R2a's own `bindable_presentation` (it exists, is of the item, no other attempt answered it);
* `probe_presentation_id`: it exists, is of the item, and this attempt answered it first;
* `scheduler_candidate_id`: the exact offer link the attempt store writes (`_link_attempt_to_scheduler_candidate`) and the data-quality report checks. That is a returned candidate of the item, in the attempt's slate and non-empty session, generated no later than the answer and chosen by this attempt.

Otherwise the forecast is censored `unbound_attempt` with `rejected_bindings: {label: why}`. It is never replaced by a later attempt.

**Tests.** A dangling candidate, another item's candidate and a dangling probe presentation are each censored with the rejection listed. A real offer, answered through the live door (which links it), resolves `pass` through `scheduler_candidate`.

## The review's claims, as they now stand

* "Each receipt resolves through its exact binding and nothing else": every reference is verified against its record (F4).
* "The report measures the next observation of the forecast's facet": the facet is assessed first, and the pattern counts only through errors attributed to it (F1).
* "The outcome uses the contract under which the current grade was read": the one version its winning rows cite, else `graded_contract_unknown` (F2).
* "The repair predictor uses measured cold successes": measured outcomes as their grades stand when the receipt is written (F3).

The stage record's Binding and Resolution sections were corrected to these rules (`4d3cdc9d2`).

## Fail-first

`tests/test_forecast_receipts.py` at `880aef2b3` was run against an isolated `git archive` of `9633d992e` (its own `src`, `migrations` and `pyproject.toml`, the current `tests`, run from that directory so its `pythonpath = ["src"]` wins): **11 failed, 15 passed**.
* The 9 new reproduction cases fail at their defect assertions:
  * F1: `same_error` where `pass` was expected; `resolved` where `censored`/`facet_unassessed` was expected.
  * F2 (both): `resolved` where `graded_contract_unknown` was expected.
  * F3: class `{successes: 1, n: 1}` where `{0, 1}` and `{0, 0}` were expected.
  * F4 (three cases): `resolved` where `censored` was expected.
* The F4 guard (a real offer) passes on both trees.
* The other two failures are the existing tests this fix changes: the presentation-bound resolution now carries `facet_outcome`, and the held-then-released test now ends `graded_contract_unknown`.

At `880aef2b3`: 26 passed, and 26 passed again with `--durable-sqlite`.

The edit dependence was also shown directly on the pre-fix tree (`fixtures-local/tmp/prefix-9633d992e/repro_f2.py`): the self-grade regraded by AI resolved `pass` (1.0, contract source `current_item`), then `other_error` (0.5) after the rubric edit.

## Manual re-read (backup-API copies, read-only, no network)

The stage's manual-run copies (`fixtures-local/forecast-manual/{linear_algebra,probability}_run3`, made with `learnloop.db.copies` and the fake diagnoser and grader) were re-read with the fixed report: `learnloop diagnosis calibration --json`, `LEARNLOOP_CONFIG_DIR` an empty directory, exit 0, database SHA-1 unchanged.

| Copy | Report | Resolutions |
|---|---|---|
| linear_algebra_run3 | `forecast_calibration_report_v2` | 5 receipts, 5 resolved on 2 attempts: 1 `pass`, 4 `other_error` (all through a verified `plan_presentation`); check kind 1 censored `not_administered` |
| probability_run3 | `forecast_calibration_report_v2` | 1 receipt, 1 resolved `pass` through a verified `plan_presentation` |

These match the stage's run: the fixes neither drop nor flip any real bound outcome there.

## Gate

Run on the final tree (`4d3cdc9d2` plus this record, a docs-only change) on 2026-10-15, after the `/tmp` clean-up. Runs from before the restarts were not counted. `TMPDIR` was the worktree's `fixtures-local/tmp`. Both suite runs held the shared lock (`flock /tmp/learnloop-fullsuite.lock`, `uv run --no-sync`).

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (178 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **22 kept, 0 broken** |
| `uv run pytest tests/test_forecast_receipts.py` | **26 passed**; with `--durable-sqlite`, **26 passed** |
| full suite, `pytest -n auto` | **11855 passed**, 0 failed, 0 skipped, 16 warnings (17:50) |
| durability lane, `pytest -m durability` | **106 passed**, 11749 deselected, 0 failed (1:56) |
| `db_validate_reference.py` | no errors (the references were regenerated in `4d3cdc9d2`; no schema change since) |
| `module_validate.py`, `validate_vault.py` | pass (508/508 catalog notes; 1108 notes, 1106/1106 reachable from Home) |
| frontend (`npm` typecheck, test, build) and `cargo check` | not run: nothing under `apps/learnloop-tauri` changed in the stage |

CLI help and RPC pins: the fix changed neither (the stage's `tests/cli_help_snapshot.json` update predates the review and passes in the suite).

## Open questions (default taken in brackets)

1. **Regrades of items without a frozen method cite no contract**, so a forecast whose observation was regraded that way is censored `graded_contract_unknown`. Releases of held grades are included. Should such regrades snapshot and cite the contract they read? That is a grading change, with its own successor, composed with the provenance landing. [Not in this stage: censoring is the honest label.]
2. **An error that names no target** counts as the facet's recurrence only when the observation's contract measures no other facet. The writer's own fallback forecasts an untargeted diagnosed error on every facet of its item, so on a multi-facet item such a recurrence resolves `pass` or `other_error`, never `same_error`. [Keep: only a recorded attribution, or an unambiguous one, counts.]
3. **The scheduler offer rule** requires the exact link the attempt store writes (`chosen_attempt_id` = the attempt, the attempt's slate and non-empty session). An attempt whose offer link was refused at write time carries none of it. [Keep: the store's own rule.]
