# Cold-retry reschedule (mvp-0.38): Codex review fixes

Review: Codex (gpt-6.1-sol), job `20261027-181705-78qbol`, on branch `sched/cold-retry-after-assist` at `ab635975f`.
Stage record: `docs/reviews/cold-retry-after-assist.md` (§2 items 3 and 7 and §8 updated for these fixes).

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Replacement selection can schedule an already contaminated surface | fixed | 09be911f9 | `tests/test_cold_retry_reschedule.py::test_a_surface_answered_since_the_primed_attempt_is_never_the_fresh_retry` (failed first: the fresh retry was scheduled on the surface answered at t₀+12h) |
| F2 | Medium | Replacement outcomes disappear from repair forecast calibration | fixed | 09be911f9 | `tests/test_cold_retry_reschedule.py::test_the_fresh_retry_records_its_own_repair_forecast_which_resolves_when_it_is_measured` (failed first: one repair forecast, bound to the withdrawn task only) |
| C1 | claim | "The fresh retry measures the repair cold" not established by the test | fixed (test) | 09be911f9 | the F2 test fires the verification on the consumed fresh retry with a repair class and asserts a measured `cold_success` disposition on it and a resolved forecast |
| C2 | claim | Another surface is not an independent measurement opportunity | fixed (by F1) | 09be911f9 | the F1 test |

### F1: what changed

The fresh retry keeps the episode's primed source attempt, so its final coldness receipt scans from that attempt. Before
the fix the selection excluded only the primed and withdrawn surfaces and shown material, so a surface the learner
answered between the primed and assisted attempts was chosen and would later hard-fail (`cold_item_answer_reveal`,
`contaminated_or_assisted`).

- `coldness_receipt.repair_surface_hard_contamination` (new, exported) runs the final receipt's own scan
  (`_scan_exposures`, repair lane, from the primed attempt to the assisted attempt, primed attempt excluded) for one
  candidate and reads it through `_hard_contamination`. It covers the candidate's own answer, administrations of its
  surface group, a suspected tutor leak on it, and a remediation passage revealing its source span. It is the same
  rule the final receipt uses, so the check cannot drift from it.
- `remediation.reschedule_assisted_cold_retry` takes the candidates `_independent_cold_item` accepts
  (`_independent_cold_candidates`, the same rule as a list in rank order) and picks the first clean one. The surfaces
  it skips go in the candidate summary (`contaminated`: item -> reason, event ids). If none is left, it records the
  structural refusal `no_uncontaminated_surface`, or `no_independent_surface` when no independent surface existed at
  all, with its schedule-refusal receipt. Nothing is scheduled.
- Treatment's first pick is unchanged: it happens before the primed attempt, so there is no interval to scan.

### F2: what changed

In the same scheduling transaction, the replacement now records its own repair forecast (`_repair_forecast` ->
`record_repair_expectation`). The forecast is for the primed attempt, using the repair class and hypotheses carried in
the context, and is bound to the fresh task. The receipt key carries the task id, so the original forecast stays
unchanged: the test asserts that it is identical and resolves `censored / unmeasurable_no_held_out_surface`. The
replacement's forecast resolves `realized / cold_success` once the fresh retry is measured. The forecast is skipped if
the primed attempt cannot be loaded, and it never raises (the receipt writer's own contract).

No new weight, margin or threshold. No new table, migration, config key or CLI change.

## Gate (this step)

Per the 2026-10-17 owner rule, the full suite, the whole durability lane and vitest were not run. No migration,
DB/connection, frontend or Tauri change, so there were no durability, npm, cargo or DB-reference runs.

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**. The function-local import edges used already exist in
  `tests/architecture_function_local_domain_imports.txt`.
- Fail-first: `uv run pytest tests/test_cold_retry_reschedule.py -k "answered_since or own_repair_forecast"`. Both new
  tests failed before the fix.
- `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -q tests/test_cold_retry_reschedule.py`
  after the fix: **31 passed**.
- `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 -q <34 files>`:
  **1208 passed, 2 skipped**. The files are every test file that imports or exercises `diagnosis.remediation` or
  `attempts.coldness_receipt` (git grep), plus the forecast-receipt and architecture/table-roles contract tests:

  test_assumed_known.py test_causal_attribution_p0.py test_causal_attribution_p2.py test_causal_cold_outcomes.py
  test_causal_factor_deferral.py test_causal_orchestrator.py test_causal_p2_acceptance.py
  test_certification_cold_probe.py test_cold_retry_reschedule.py test_coldness_receipt.py test_collection_dataset.py
  test_exam_protection.py test_exam_protection_review.py test_family_memory_projection.py test_forecast_receipts.py
  test_forecast_receipts_landing.py test_guided_redo.py test_held_grade_evidence.py test_hypothesis_surface_wiring.py
  test_instrument_servability_journeys.py test_intervention_outcomes_replayer.py
  test_misconception_transitions_intake.py test_pfc_unassessed_readers.py test_prescription_passages.py
  test_probe_remint.py test_reader_ca2_one_ask.py test_remediation_cold_retry.py test_reveal_ledger.py
  test_serve_eligibility.py test_serve_eligibility_review.py test_sidecar_remediation_surfaces.py
  test_ux_phase4_feedback.py test_architecture.py test_table_roles.py

No live or paid calls; all tests use fakes and synthetic vaults.
