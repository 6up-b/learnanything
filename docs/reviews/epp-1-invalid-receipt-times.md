# EPp-1: unreadable receipt times; EPp-2: standalone helper registration

Base `8e5a98fcec`, branch `ep/epp-1-scorer-invalid-time`. Part A is implemented;
part B is stopped for the orchestrator's successor decision. EPp-2 is test-only.
No migration, configuration, switch, prompt, algorithm tag, identity pin or golden
is changed. No staging or commit is performed.

## Part A — scorer first

Before this change, `adaptive_difficulty.scoring.score_rows` called
`scheduling.forecast_receipts.valid_for_serve`, whose `parse_utc` raised on
unreadable text. One bad bound receipt aborted the complete scoring run.

The scorer now catches `ValueError` and `OverflowError` from that time check and
emits its existing `invalid` outcome, with the new adjacent reason
`unreadable_time`. It supplies no outcome, log loss or Brier score. Readable times
still execute the same validity comparison and all subsequent branches. Existing
invalid-status and unbound/pending precedence is preserved. Neither the shared
`valid_for_serve` function nor the clamp/writer changes in this part.

The former stop-condition characterization in
`tests/test_epp_receipt_repairs.py` is now
`test_epp1_unreadable_time_is_invalid_without_changing_other_scores`. Written and
run before the production edit, it failed with the expected `ValueError: Invalid
isoformat string: '!not a time'`. It first scores a real synthetic frozen AD
journey, then appends one synthetic unreadable bound receipt through SQL. The
append respects the existing lexical time constraint and changes no old row or
trigger. The mixed run must contain one invalid row; the complete JSON-encoded
bytes of all other score rows, including ordering and details, equal the run
without it. After `scoring.rebuild`, the complete stored rows for the readable
receipts are byte-equal to their earlier stored rows. The invalid row has NULL
outcome and losses, and a second rebuild reproduces every stored score row.

### Existing vaults and playbook ruling

Playbook rule **1** asks whether persisted meaning changes. For part A, no
successor is needed for histories produced by the current writer: no receipt
with an unreadable `inputs_as_of` can be emitted by it. This is a code-path proof,
not an inspection of private vaults:

- `scheduling/forecast_receipts.py::record_receipts` is the only production caller
  of `db/stores/forecast_receipts.py::insert_receipt`.
- In its `repository.atomic()` block, every receipt passes `clamped_as_of` before
  insertion. That clamp calls `parse_utc` without catching its parse error.
- An unreadable value therefore exits the transaction, rolls back any earlier
  receipts in that batch, and reaches the outer logged exception handler returning
  `[]`. The existing `test_the_status_check_of_the_unreadable_time` still proves
  the empty batch result. Missing and future values instead yield the readable
  issue-time fallback; their scoring does not change here.
- `db/table_roles.py` classifies `item_forecast_scores` as **DERIVED** and
  `forecast_receipts` as **RECEIPT**. The registered
  `substrate/rebuild_orchestrator.py::_run_item_forecast_scores` calls
  `scoring.rebuild`, which computes rows, clears just the derived score table,
  and writes the replacement scores. It neither repairs nor rewrites receipts.

Thus an existing supported vault rebuild changes no score values due to part A.
A manually inserted malformed receipt (as in the regression) gains an invalid
score instead of aborting the rebuild; this is outside the current writer's
reachable history. No claim is made about privately modified/corrupt vaults.

## Part B — stopped: a successor is required

The requested writer repair would persist previously dropped rows and score the
unreadable ones as unusable. That alters persisted meaning even though existing
writer-produced histories cannot contain them. Playbook rule **1** therefore
requires a new immediate-successor tag; the historical in-place amendments are
explicit exceptions, not authorization for this change. The 2026-11-16 owner rule
requires the tag, upgrade row and test row, without a new kill switch unless
requested. Scheduling that tag belongs to the orchestrator under this task's
explicit stop condition.

The clamp, writer, snapshot code, strict xfail
`test_an_unreadable_inputs_time_is_recorded_invalid`, and batch-drop
characterization remain unchanged. No part-B implementation or passing part-B
regression is claimed. In the successor, merely catching the clamp's exception
is insufficient: after fallback the stored time becomes readable, and today's
scorer does not inspect the snapshot's original cutoff. The successor must also
identify the original unreadable time from the snapshot and make it unusable,
without silently changing the interpretation of existing future-time snapshots.

The id contract to prove there is equality with the **readable-value
counterfactual**: the repaired receipt consumes the same one id slot it would
have consumed had its input time been readable, so subsequent receipt and
shared-stream decision ids line up with that counterfactual. They cannot be
claimed equal to today's failed-batch path: today the prefix may consume ids
before rollback, the failing receipt consumes none, and the suffix is never
visited. Neither rollback nor this scorer patch rewinds an id stream.

For the implemented part, no id-producing path changes. The existing frozen
journey `test_snapshots_move_no_id_seed_digest_score_or_state_under_a_frozen_clock`
is included in the passing filename-filter run. It compares every table across
readable journeys (with/without snapshot enrichment), including decision ids,
seeds, keys, digests, score rows and AD state. This is regression evidence for the
unchanged readable path, not a part-B counterfactual proof. Identity pins pass
without regeneration; receipt-body goldens are never regenerated.

## EPp-2 — explicit method registration

The alone run of `tests/test_ad1_fix_round5.py -q -n 1` reproduced both
`test_the_draft_keeps_hint_seen_under_its_retry_key[on/off]` failures with
`KeyError: 'start_session'`. The helper now imports `learnloop_sidecar.handlers`
before reading `METHOD_REGISTRY`, matching sidecar startup.

An AST audit of test helper modules found 21 registry-reading modules without an
explicit handler-package import. All now import it directly, including helpers
that happened to load a handler submodule conditionally later. The audit also
checked non-`test_` support/fixture/fake modules, which already import handlers.
The named UX-85 row is absent at this base, and
`ux_phase1_add_source_helpers.py` still lacked the import, so it is included:

```text
tests/ad1_attempt_columns_helpers.py
tests/daily_plan_kill_switch_helpers.py
tests/figures_help_helpers.py
tests/followup_journey_helpers.py
tests/followup_rival_factor_helpers.py
tests/hint_h2a_review_helpers.py
tests/hint_h2a_review_round2_helpers.py
tests/hint_h2b_review_helpers.py
tests/hint_telemetry_helpers.py
tests/learner_pick_proposal_helpers.py
tests/mobile_v2_plan_helpers.py
tests/mobile_v3_probes_helpers.py
tests/mobile_v4_reader_helpers.py
tests/owner_capture_1025_helpers.py
tests/plan_determinism_helpers.py
tests/reader_ca1_as_printed_helpers.py
tests/reader_ca2_codex_review_helpers.py
tests/reader_rw3a_landing_helpers.py
tests/reread_safety_helpers.py
tests/router_r2a_serving_helpers.py
tests/ux_phase1_add_source_helpers.py
```

The final audit covers all 33 non-test modules that read the registry by key:
none lacks an explicit handler-package import. Import dependencies through
helper modules select 120 test files; each is invoked separately, including
`test_ad1_fix_round5.py` alone at `-n 1`. This includes transitive helper consumers.

## Validation limitations discovered during the isolated runs

`tests/test_arcb_close_fixes.py::test_a_decisions_id_and_seed_are_the_same_whether_records_are_written_or_not`
fails at the same id/seed comparison with this patch and with every modified
Python file temporarily restored from `HEAD` (`8e5a98fcec`). The first differing
ids end in `D1V` versus `D1T`, and the same two seeds differ in both runs. The base
file run also fails
`test_an_async_hints_receipts_and_records_share_the_requests_trace` with
`KeyError: 'start_session'` in `hint_h2a_review_helpers`; this patch fixes that
second failure. All Python edits were restored byte-for-byte after the baseline
comparison. The remaining identity-test failure is not fixed or waived here.

The phone-contract file initially stalled after seven passing tests. A bounded
rerun with `faulthandler_timeout=10` showed the remaining test waiting in
`Starlette.TestClient.__enter__`, inside AnyIO's thread portal; the event-loop
thread was waiting in `selectors.select`. An independent smoke check containing
only `TestClient(Starlette())`, with no LearnLoop imports, also hung and was
terminated. Thus in-process TestClient tests cannot be verified in this sandbox,
in addition to the explicitly excluded loopback-server cases. No root cause for
the sandbox's portal hang is claimed.

A temporary pytest plugin skipped a test only when it instantiated Starlette's
TestClient, recording its exact node id. It changed no LearnLoop function and is
removed before handoff; these are unavailable tests, not passes. The resumed
commands use `-o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` to load this
run-only plugin, with a 120-second external timeout. The first attempted resume
omitted the root from pytest's initial import path: all 76 commands stopped at
plugin import, before collection. They were rerun with the corrected path. The
phone-contract smoke then reported `7 passed, 1 skipped in 3.24s`.

## Commands and results

All Python tools use the supplied wrappers; `t.sh` and `py.sh` below name those
wrappers without embedding machine paths. Every pytest command has explicit
files and at most two workers. The filename filter has seven files, so it fits
one chunk below the 30-file limit.

| Command | Last result line |
| --- | --- |
| `t.sh tests/test_epp_receipt_repairs.py -q -n 2 -k epp1 (test first, before production edit)` | `1 failed in 2.51s` |
| `t.sh tests/test_epp_receipt_repairs.py -q -n 2 (after scorer edit)` | `13 passed in 16.23s` |
| `t.sh tests/test_ad1_fix_round5.py -q -n 1 (before helper edits)` | `2 failed, 8 passed in 3.30s` |
| `t.sh tests/test_arcb_close_fixes.py -q -n 2 (HEAD Python sources, temporary comparison)` | `2 failed, 14 passed in 3.48s` |
| `t.sh tests/test_ad1_fix_round5.py -q -n 1` | `10 passed in 3.95s` |
| `t.sh tests/test_ad2_model.py tests/test_ad2_serving.py tests/test_epp_prediction_snapshots.py tests/test_epp_receipt_repairs.py tests/test_epp_repeat_receipts.py tests/test_forecast_receipts.py tests/test_forecast_receipts_landing.py -q -n 2 -m 'not arc_close'` | `141 passed, 1 xfailed in 30.08s` |
| `t.sh tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_public_tip_guards.py tests/test_test_layout.py tests/test_architecture.py -q -n 2` | `395 passed in 37.24s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` |
| `t.sh tests/test_ad1_attempt_columns.py -q -n 2` | `6 passed in 2.78s` |
| `t.sh tests/test_add_source_same_content.py -q -n 2` | `4 passed in 2.77s` |
| `t.sh tests/test_apply_recovery.py -q -n 2` | `27 passed, 16 warnings in 5.08s` |
| `t.sh tests/test_arcb_close_fixes.py -q -n 2` | `1 failed, 15 passed in 3.22s` |
| `t.sh tests/test_batch3_landing.py -q -n 2` | `5 passed in 4.57s` |
| `t.sh tests/test_certification_serving_reservation.py -q -n 2` | `19 passed in 3.04s` |
| `t.sh tests/test_coordinated_migrations.py -q -n 2` | `20 passed in 15.81s` |
| `t.sh tests/test_daily_plan_kill_switch.py -q -n 2` | `6 passed, 3 skipped, 1 xfailed in 2.79s` |
| `t.sh tests/test_diagnosis_journey_golden.py -q -n 2` | `21 passed in 6.40s` |
| `t.sh tests/test_empty_first_build.py -q -n 2` | `15 passed in 9.48s` |
| `t.sh tests/test_evidence_reading_successor.py -q -n 2` | `54 passed in 7.69s` |
| `t.sh tests/test_exam_protection_identity.py -q -n 2` | `60 passed in 7.40s` |
| `t.sh tests/test_exam_protection_landing.py -q -n 2` | `5 passed in 2.72s` |
| `t.sh tests/test_field_workbench_signals.py -q -n 2` | `23 passed, 3 skipped in 6.05s` |
| `t.sh tests/test_figure_build_golden.py -q -n 2` | `30 passed in 22.62s` |
| `t.sh tests/test_figure_rich_job_golden.py -q -n 2` | `16 passed in 15.18s` |
| `t.sh tests/test_figures_help.py -q -n 2` | `25 passed in 4.12s` |
| `t.sh tests/test_figures_help_codex_review.py -q -n 2` | `23 passed in 6.96s` |
| `t.sh tests/test_followup_authoring_retry.py -q -n 2` | `17 passed in 3.61s` |
| `t.sh tests/test_followup_fg1c_codex_review.py -q -n 2` | `29 passed in 4.22s` |
| `t.sh tests/test_followup_fg1c_r1_exposure_independence.py -q -n 2` | `36 passed in 5.05s` |
| `t.sh tests/test_followup_fg1d_panel_read.py -q -n 2` | `8 passed in 5.17s` |
| `t.sh tests/test_followup_fg1d_probe_shadow.py -q -n 2` | `12 passed in 7.15s` |
| `t.sh tests/test_followup_journey.py -q -n 2` | `19 passed in 4.11s` |
| `t.sh tests/test_followup_rival_factor.py -q -n 2` | `22 passed in 6.26s` |
| `t.sh tests/test_followups_nov2_help_fold.py -q -n 2` | `8 passed in 3.33s` |
| `t.sh tests/test_glm_ocr.py -q -n 2 --deselect tests/test_glm_ocr.py::test_the_local_backend_renders_pdf_pages_for_a_real_http_server --deselect tests/test_glm_ocr.py::test_the_local_backend_reads_an_image_as_one_page --deselect tests/test_glm_ocr.py::test_an_unanswering_local_server_is_not_selected` | `108 passed in 9.32s` |
| `t.sh tests/test_held_topic_work_review.py -q -n 2` | `4 passed in 8.61s` |
| `t.sh tests/test_help_fold_attach_successor.py -q -n 2` | `5 passed in 3.02s` |
| `t.sh tests/test_hint_h2a_review.py -q -n 2` | `24 passed in 3.71s` |
| `t.sh tests/test_hint_h2a_review_round2.py -q -n 2` | `19 passed in 5.01s` |
| `t.sh tests/test_hint_h2a_review_round3.py -q -n 2` | `14 passed in 3.94s` |
| `t.sh tests/test_hint_h2a_review_round4.py -q -n 2` | `3 passed in 2.55s` |
| `t.sh tests/test_hint_h2b_fix3.py -q -n 2` | `9 passed in 3.76s` |
| `t.sh tests/test_hint_h2b_fix4.py -q -n 2` | `6 passed in 6.19s` |
| `t.sh tests/test_hint_h2b_rereview.py -q -n 2` | `9 passed in 6.27s` |
| `t.sh tests/test_hint_h2b_review.py -q -n 2` | `14 passed in 5.19s` |
| `t.sh tests/test_hint_kill_switch.py -q -n 2` | `9 passed in 3.03s` |
| `t.sh tests/test_hint_telemetry.py -q -n 2` | `64 passed in 5.59s` |
| `t.sh tests/test_hypothesis_marks.py -q -n 2` | `37 passed in 6.11s` |
| `t.sh tests/test_hypothesis_marks_context.py -q -n 2` | `14 passed in 3.52s` |
| `t.sh tests/test_learner_claim_application_migration.py -q -n 2` | `3 passed in 3.68s` |
| `t.sh tests/test_learner_pick_proposal.py -q -n 2` | `17 passed in 3.37s` |
| `t.sh tests/test_mobile_phone_contract.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `7 passed, 1 skipped in 3.10s` |
| `t.sh tests/test_mobile_v2_landing_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 skipped in 3.13s` |
| `t.sh tests/test_mobile_v2_objective_stop.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `3 skipped in 3.08s` |
| `t.sh tests/test_mobile_v2_plan.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 passed, 12 skipped in 4.42s` |
| `t.sh tests/test_mobile_v2_rereview_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 passed, 6 skipped in 3.17s` |
| `t.sh tests/test_mobile_v2_review_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 passed, 11 skipped in 3.28s` |
| `t.sh tests/test_mobile_v3_carried.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 skipped in 3.29s` |
| `t.sh tests/test_mobile_v3_codex_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `13 passed, 3 skipped in 9.23s` |
| `t.sh tests/test_mobile_v3_probes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 passed, 2 skipped in 4.93s` |
| `t.sh tests/test_mobile_v4_codex_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `18 skipped in 3.34s` |
| `t.sh tests/test_mobile_v4_eligibility.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 passed in 3.17s` |
| `t.sh tests/test_mobile_v4_reader.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `20 skipped in 3.60s` |
| `t.sh tests/test_owner_capture_1025.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `15 passed in 6.07s` |
| `t.sh tests/test_part_read_first_set.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `24 passed in 43.39s` |
| `t.sh tests/test_plan_determinism.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `14 passed in 23.92s` |
| `t.sh tests/test_plan_determinism_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `16 passed in 18.98s` |
| `t.sh tests/test_plan_first_transport_offer_grants.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `19 passed in 31.11s` |
| `t.sh tests/test_plan_first_transport_offer_grants_r5.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `9 passed in 7.52s` |
| `t.sh tests/test_probe_router_authority.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `28 passed in 8.65s` |
| `t.sh tests/test_probe_router_report.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 passed in 5.34s` |
| `t.sh tests/test_protection_surface_matrix.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `164 passed in 38.78s` |
| `t.sh tests/test_reader_ca1_as_printed.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `20 passed in 3.43s` |
| `t.sh tests/test_reader_ca1_astra_codex_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed in 3.29s` |
| `t.sh tests/test_reader_ca1_astra_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `14 passed in 3.51s` |
| `t.sh tests/test_reader_ca1_astra_redesign.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `64 passed in 5.54s` |
| `t.sh tests/test_reader_ca1_astra_rereview.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `35 passed in 3.53s` |
| `t.sh tests/test_reader_ca1_codex_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `26 passed in 3.97s` |
| `t.sh tests/test_reader_ca1_unicode_containment.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 passed in 3.01s` |
| `t.sh tests/test_reader_ca2_astra_handoff.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed in 3.62s` |
| `t.sh tests/test_reader_ca2_astra_handoff_recovery.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `4 passed in 3.53s` |
| `t.sh tests/test_reader_ca2_codex_rereview.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `9 passed in 4.03s` |
| `t.sh tests/test_reader_ca2_codex_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `18 passed in 4.00s` |
| `t.sh tests/test_reader_ca2_fix_orchestrator.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed in 4.63s` |
| `t.sh tests/test_reader_pdf_selection.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `28 passed in 3.58s` |
| `t.sh tests/test_reader_rw2b_fix10.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 3 passed in 15.67s` |
| `t.sh tests/test_reader_rw2b_fix11.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 4 passed in 11.19s` |
| `t.sh tests/test_reader_rw2b_fix12.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 5 passed in 3.68s` |
| `t.sh tests/test_reader_rw2b_fix13.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `6 passed in 3.54s` |
| `t.sh tests/test_reader_rw2b_fix14.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 3 passed in 4.50s` |
| `t.sh tests/test_reader_rw2b_fix15.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 1 passed in 2.78s` |
| `t.sh tests/test_reader_rw2b_fix4.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `4 failed, 15 passed in 4.11s` |
| `t.sh tests/test_reader_rw2b_fix5.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `6 failed, 8 passed in 3.88s` |
| `t.sh tests/test_reader_rw2b_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 failed, 19 passed in 4.37s` |
| `t.sh tests/test_reader_rw3a_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 passed in 3.27s` |
| `t.sh tests/test_reader_rw4b_fix6.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `13 passed in 3.43s` |
| `t.sh tests/test_reader_seen_passages.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `3 passed, 13 skipped in 3.51s` |
| `t.sh tests/test_reading_hardening_2_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 passed in 8.59s` |
| `t.sh tests/test_reading_hardening_review_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 passed in 10.08s` |
| `t.sh tests/test_reading_hardening_verify_fixes.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 passed in 10.58s` |
| `t.sh tests/test_reading_request_sweep.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `14 passed in 22.17s` |
| `t.sh tests/test_refusal_records.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `19 passed in 4.55s` |
| `t.sh tests/test_reread_safety.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `67 passed in 7.85s` |
| `t.sh tests/test_reread_safety_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `..` |
| `t.sh tests/test_retrieval_spaces_migration.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `6 passed in 4.64s` |
| `t.sh tests/test_router_r2a_serving.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed, 3 skipped in 4.92s` |
| `t.sh tests/test_router_r2b_serving.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `32 passed, 3 skipped in 4.59s` |
| `t.sh tests/test_router_r2bc_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `6 passed in 4.98s` |
| `t.sh tests/test_section_coverage_migration.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `5 passed in 3.89s` |
| `t.sh tests/test_section_done_before_build.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `16 passed in 16.13s` |
| `t.sh tests/test_section_end.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `7 passed, 15 skipped in 14.35s` |
| `t.sh tests/test_status_line_waiting_turn.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `3 passed in 2.96s` |
| `t.sh tests/test_ux11_html_extraction.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed in 13.94s` |
| `t.sh tests/test_ux2_macros_protection.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `2 passed, 2 skipped in 3.32s` |
| `t.sh tests/test_ux2_source_macros.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `19 passed in 5.97s` |
| `t.sh tests/test_ux_phase1_add_source.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `11 passed in 4.56s` |
| `t.sh tests/test_ux_phase1_finish.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `12 passed in 14.47s` |
| `t.sh tests/test_ux_phase1_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `8 passed in 3.21s` |
| `t.sh tests/test_ux_phase1_round2_rereview.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `9 passed in 8.57s` |
| `t.sh tests/test_ux_phase1_round2_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `17 passed in 7.08s` |
| `t.sh tests/test_ux_phase1_usability_round1.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `17 passed in 9.05s` |
| `t.sh tests/test_ux_phase1_usability_round2.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `16 passed in 9.57s` |
| `t.sh tests/test_workbench_assistance.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `19 passed in 5.60s` |
| `t.sh tests/test_workbench_help_kill_switch.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 passed in 3.67s` |
| `t.sh tests/test_workbench_hint_service.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 passed in 3.72s` |
| `t.sh tests/test_workbench_in_session_gaps.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `2 passed in 3.51s` |
| `t.sh tests/test_workbench_trace.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `3 passed in 3.83s` |
| `py.sh python <temporary registry-import audit>` | `Registry readers audited: 33; missing explicit handler-package imports: []` |
| `py.sh python <temporary test-coupling measure>` | `private_patch_sites: 465; source_text_assertions: 23` |
| `git diff --check` | clean (exit 0, no output) |

The bounded phone-contract diagnostic (`-vv -n 1 -o faulthandler_timeout=10`)
was terminated with exit 137 after its thread dump; the original unbounded run
was interrupted with exit 130. The empty-Starlette smoke was also terminated
with exit 137. Neither produced a passing final summary. The failed initial
plugin-loading attempt ended each of its 76 commands with
`ImportError: Error importing plugin "tests._epp1_sandbox_plugin": No module named 'tests._epp1_sandbox_plugin'`;
no tests ran in that attempt. The table records every corrected rerun.

## Tests not verified

The following three tests in `tests/test_glm_ocr.py` require loopback sockets
and were explicitly deselected (the other 108 tests in that file passed):

- `test_the_local_backend_renders_pdf_pages_for_a_real_http_server`
- `test_the_local_backend_reads_an_image_as_one_page`
- `test_an_unanswering_local_server_is_not_selected`

The following 119 unique node ids reached the unavailable Starlette TestClient
and were skipped by the temporary run-only plugin. The orchestrator must run
them without that plugin in its supported test environment:

```text
tests/test_mobile_phone_contract.py::test_every_reply_carries_what_the_phone_reads
tests/test_mobile_v2_landing_fixes.py::test_r1_a_phones_sessionless_write_whose_session_was_replaced_by_its_own_commits_nothing
tests/test_mobile_v2_landing_fixes.py::test_r1_a_phones_sessionless_write_whose_session_was_taken_and_ended_commits_nothing
tests/test_mobile_v2_landing_fixes.py::test_r1_a_phones_sessionless_write_with_no_session_at_its_start_goes_through
tests/test_mobile_v2_landing_fixes.py::test_r1_the_desktops_sessionless_write_still_goes_through_with_the_phones_session_open
tests/test_mobile_v2_landing_fixes.py::test_r2_done_for_today_on_a_pending_stop_records_that_stop_accepted
tests/test_mobile_v2_landing_fixes.py::test_r2_keep_going_after_done_on_a_pending_stop_is_the_overridden_response
tests/test_mobile_v2_landing_fixes.py::test_r3_a_refused_keep_going_leaves_no_override_receipt
tests/test_mobile_v2_landing_fixes.py::test_r3_keep_going_commits_its_override_with_the_plan_update
tests/test_mobile_v2_objective_stop.py::test_objective_f7_done_for_today_on_the_pending_stop_leaves_the_held_work_for_the_desktop[]
tests/test_mobile_v2_objective_stop.py::test_objective_f7_keep_going_overrides_the_pending_stop_in_place_and_keeps_the_held_work[]
tests/test_mobile_v2_objective_stop.py::test_objective_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone[]
tests/test_mobile_v2_plan.py::test_j1_a_read_never_crosses_past_held_work_and_next_does_once
tests/test_mobile_v2_plan.py::test_j1_next_plan_item_is_long_capable_and_a_retry_answers_the_same_step
tests/test_mobile_v2_plan.py::test_j1_the_phone_never_gets_a_held_item_and_the_desktop_serves_it_next
tests/test_mobile_v2_plan.py::test_j1_the_phone_reads_the_shared_plan_with_its_device_line
tests/test_mobile_v2_plan.py::test_j1_the_phones_boundary_decisions_record_phone_plan_and_the_device_rules
tests/test_mobile_v2_plan.py::test_j1_the_phones_step_bumps_the_desktops_token
tests/test_mobile_v2_plan.py::test_j5_the_plan_ends_and_the_phone_stops_or_keeps_going
tests/test_mobile_v2_plan.py::test_meta_says_the_plan_is_on_by_default
tests/test_mobile_v2_plan.py::test_s5_6_an_ended_or_unknown_session_answers_as_before
tests/test_mobile_v2_plan.py::test_s5_6_plan_writes_refuse_the_device_that_does_not_own_the_session
tests/test_mobile_v2_plan.py::test_s5_6_tutor_and_lesson_writes_bound_to_a_moved_session_are_refused
tests/test_mobile_v2_plan.py::test_the_kill_switch_refuses_the_plan_and_meta_says_so
tests/test_mobile_v2_rereview_fixes.py::test_f5_the_phones_serve_of_a_check_restored_the_next_day_says_no_help
tests/test_mobile_v2_rereview_fixes.py::test_f6_a_phones_sessionless_write_whose_session_moved_and_came_back_commits_nothing
tests/test_mobile_v2_rereview_fixes.py::test_f6_a_phones_sessionless_write_with_its_session_where_it_was_goes_through
tests/test_mobile_v2_rereview_fixes.py::test_f7_done_for_today_on_the_pending_stop_leaves_the_held_work_for_the_desktop
tests/test_mobile_v2_rereview_fixes.py::test_f7_keep_going_overrides_the_pending_stop_in_place_and_keeps_the_held_work
tests/test_mobile_v2_rereview_fixes.py::test_f7_the_stop_drawn_past_held_work_is_offered_on_the_phone
tests/test_mobile_v2_review_fixes.py::test_f1_a_phone_write_naming_no_open_session_is_refused_while_the_desktop_owns_one
tests/test_mobile_v2_review_fixes.py::test_f1_the_desktops_sessionless_write_answers_as_before
tests/test_mobile_v2_review_fixes.py::test_f1_with_no_session_open_the_phones_minutes_chip_goes_through
tests/test_mobile_v2_review_fixes.py::test_f2_the_desktops_pick_of_the_same_item_is_served
tests/test_mobile_v2_review_fixes.py::test_f2_the_phones_pick_of_a_held_item_is_refused_before_anything_is_served
tests/test_mobile_v2_review_fixes.py::test_f4_a_stop_drawn_past_held_work_keeps_that_work_for_the_desktop_and_closes_after_it
tests/test_mobile_v2_review_fixes.py::test_f4_the_pending_stop_lapses_when_a_minutes_tap_re_plans
tests/test_mobile_v2_review_fixes.py::test_f5_the_phones_serve_of_the_check_says_no_help_and_the_desktops_is_unchanged
tests/test_mobile_v2_review_fixes.py::test_f6_a_desktop_step_whose_session_moved_during_its_work_commits_nothing
tests/test_mobile_v2_review_fixes.py::test_f6_nothing_changes_for_a_step_whose_session_stayed
tests/test_mobile_v2_review_fixes.py::test_f6_the_check_is_a_phone_origins_too
tests/test_mobile_v3_carried.py::test_an_items_own_hint_revealed_on_the_phone_records_the_phones_surface_and_the_desktops_stays_practice
tests/test_mobile_v3_carried.py::test_keep_going_on_a_finished_plan_commits_its_override_with_the_extension
tests/test_mobile_v3_carried.py::test_keep_going_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt
tests/test_mobile_v3_carried.py::test_more_new_confirmed_on_a_finished_plan_refused_mid_build_leaves_no_override_receipt
tests/test_mobile_v3_carried.py::test_the_desktops_keep_going_on_a_finished_plan_records_as_before
tests/test_mobile_v3_codex_review.py::test_f3_a_v2_app_gets_v2s_doors_from_a_v3_host_and_burns_nothing
tests/test_mobile_v3_codex_review.py::test_f3_a_v2_apps_plan_step_holds_a_generated_probe_for_the_desktop
tests/test_mobile_v3_codex_review.py::test_f3_the_v3_app_says_it_answers_probes_and_gets_v3s_door
tests/test_mobile_v3_probes.py::test_a_desktop_serving_next_with_no_phone_burn_abandons_nothing
tests/test_mobile_v3_probes.py::test_the_desktops_serving_next_moves_past_a_probe_the_phone_served_and_abandons_it
tests/test_mobile_v4_codex_review.py::test_f10_a_page_is_phone_eligible_exactly_when_the_page_endpoint_serves_it
tests/test_mobile_v4_codex_review.py::test_f10_a_stored_image_of_an_exam_source_is_not_phone_eligible
tests/test_mobile_v4_codex_review.py::test_f12_the_media_lift_admits_no_new_measurement_on_the_phone
tests/test_mobile_v4_codex_review.py::test_f13_a_question_anchored_on_a_protected_passage_is_refused_even_when_it_cites_a_safe_one
tests/test_mobile_v4_codex_review.py::test_f14_a_question_of_a_source_opted_out_of_the_reader_is_refused_on_the_phone
tests/test_mobile_v4_codex_review.py::test_f1_a_revalidated_page_is_checked_again_and_a_match_is_a_bodiless_304
tests/test_mobile_v4_codex_review.py::test_f3_a_page_named_by_an_ordinary_reading_is_withheld_when_another_reading_of_its_file_is_exam_material
tests/test_mobile_v4_codex_review.py::test_f4_ask_history_withholds_an_exchange_whose_selection_or_citation_is_protected
tests/test_mobile_v4_codex_review.py::test_f4_reopened_a_fresh_answer_is_judged_on_what_it_stored_before_the_phone_is_sent_it
tests/test_mobile_v4_codex_review.py::test_f4_reopened_a_protected_excerpt_is_withheld_with_both_tutor_switches_off
tests/test_mobile_v4_codex_review.py::test_f4_reopened_a_protected_selection_is_withheld_with_reader_inquiry_off
tests/test_mobile_v4_codex_review.py::test_f4_reopened_the_guide_plans_placed_question_is_judged_by_its_items_stored_source
tests/test_mobile_v4_codex_review.py::test_f5_a_dose_event_committed_before_a_crash_is_recorded_once_after_the_restart
tests/test_mobile_v4_codex_review.py::test_f5_activity_committed_before_a_crash_is_recorded_once_after_the_restart
tests/test_mobile_v4_codex_review.py::test_f5_the_desktop_writes_as_before
tests/test_mobile_v4_codex_review.py::test_f8_a_phone_visits_active_time_reaches_the_routers_activity_readers
tests/test_mobile_v4_codex_review.py::test_f9_the_phone_answers_an_extra_question_through_the_desktops_question_action
tests/test_mobile_v4_codex_review.py::test_landing_smoke_a_held_out_sections_heading_is_not_its_label_on_the_phone
tests/test_mobile_v4_reader.py::test_a_completed_phone_ask_is_withheld_when_its_passage_is_marked_since
tests/test_mobile_v4_reader.py::test_a_mark_made_after_a_page_was_cached_withholds_it_at_once
tests/test_mobile_v4_reader.py::test_a_page_is_a_png_under_the_app_token_immutable_and_cached_outside_the_vault
tests/test_mobile_v4_reader.py::test_a_page_showing_a_held_out_passage_is_never_served
tests/test_mobile_v4_reader.py::test_a_reading_exam_material_covers_whole_reaches_the_phone_not_at_all
tests/test_mobile_v4_reader.py::test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once
tests/test_mobile_v4_reader.py::test_a_section_range_is_its_blocks_in_the_same_shape
tests/test_mobile_v4_reader.py::test_a_stored_image_is_served_by_its_content_address_and_never_a_pdf
tests/test_mobile_v4_reader.py::test_activity_is_the_desktops_row_with_the_phones_surface
tests/test_mobile_v4_reader.py::test_an_image_that_is_a_protected_books_original_is_withheld
tests/test_mobile_v4_reader.py::test_an_outbox_replay_is_recorded_once
tests/test_mobile_v4_reader.py::test_doses_from_the_phone_are_the_desktops_draw_and_rows
tests/test_mobile_v4_reader.py::test_progress_is_monotonic_across_the_phone_and_the_desktop
tests/test_mobile_v4_reader.py::test_render_view_without_a_range_is_todays_reply_byte_for_byte
tests/test_mobile_v4_reader.py::test_the_page_endpoint_is_per_vault
tests/test_mobile_v4_reader.py::test_the_phone_is_never_sent_held_out_text
tests/test_mobile_v4_reader.py::test_the_phones_ask_and_save_refuse_protected_passages_before_any_model
tests/test_mobile_v4_reader.py::test_the_phones_ask_is_refused_while_its_check_on_your_own_is_open
tests/test_mobile_v4_reader.py::test_the_phones_ask_never_sends_exam_material_in_its_context_or_reply
tests/test_mobile_v4_reader.py::test_the_reader_switch_off_is_v3s_phone
tests/test_reader_seen_passages.py::test_a_count_or_a_completion_is_never_turned_into_passages
tests/test_reader_seen_passages.py::test_a_duplicate_report_and_an_outbox_replay_write_nothing_new
tests/test_reader_seen_passages.py::test_a_phone_completion_coalesced_with_passages_and_a_stranger_lands_whole
tests/test_reader_seen_passages.py::test_a_report_records_each_observed_passage_once_with_its_section_time_and_origin
tests/test_reader_seen_passages.py::test_an_end_is_recorded_only_when_its_last_passage_is_seen
tests/test_reader_seen_passages.py::test_an_id_that_is_not_a_passage_of_the_section_is_left_out_and_the_rest_of_the_report_lands[another_sections_passage]
tests/test_reader_seen_passages.py::test_an_id_that_is_not_a_passage_of_the_section_is_left_out_and_the_rest_of_the_report_lands[unknown_passage]
tests/test_reader_seen_passages.py::test_below_the_tag_reaching_the_end_is_recorded_with_its_origin_and_acted_on_by_nothing
tests/test_reader_seen_passages.py::test_on_an_unknown_section_or_reading_no_passage_is_recorded_and_the_report_is_mains[unknown_reading]
tests/test_reader_seen_passages.py::test_on_an_unknown_section_or_reading_no_passage_is_recorded_and_the_report_is_mains[unknown_section]
tests/test_reader_seen_passages.py::test_reports_union_and_a_smaller_report_removes_nothing_or_changes_a_first_observation
tests/test_reader_seen_passages.py::test_section_ends_are_read_on_their_own_reading_only
tests/test_reader_seen_passages.py::test_the_passages_survive_a_restart_and_later_reports_union_with_them
tests/test_section_end.py::test_below_the_tag_the_phones_end_finishes_nothing[mvp-0.62]
tests/test_section_end.py::test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate[check_closed-mvp-0.62]
tests/test_section_end.py::test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate[check_closed-mvp-0.63]
tests/test_section_end.py::test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate[idea_chosen-mvp-0.62]
tests/test_section_end.py::test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate[idea_chosen-mvp-0.63]
tests/test_section_end.py::test_both_tags_reading_to_the_end[mvp-0.62]
tests/test_section_end.py::test_both_tags_reading_to_the_end[mvp-0.63]
tests/test_section_end.py::test_both_tags_the_learner_says_they_read_it[None-mvp-0.62]
tests/test_section_end.py::test_both_tags_the_learner_says_they_read_it[None-mvp-0.63]
tests/test_section_end.py::test_both_tags_the_learner_says_they_read_it[learner-mvp-0.62]
tests/test_section_end.py::test_both_tags_the_learner_says_they_read_it[learner-mvp-0.63]
tests/test_section_end.py::test_no_end_no_finish
tests/test_section_end.py::test_the_end_and_the_explicit_completion_are_one_completion
tests/test_section_end.py::test_the_learner_first_then_the_end_keeps_the_learners_completion
tests/test_section_end.py::test_the_phones_end_finishes_the_section_once_for_the_desktop_to_write
tests/test_ux2_macros_protection.py::test_ux2_a_source_with_a_held_out_part_sends_no_macros_with_any_view
tests/test_ux2_macros_protection.py::test_ux2_an_unprotected_source_sends_its_macros_on_the_desktop_and_the_phone
```

Other pre-existing skips/xfails are reported in the command table; EPp-1 part B
remains a strict xfail deliberately. No full suite, arc-close gate, durability
lane, whole-vault shadow rebuild, owner data, network, or real model calls were
run. No successful part-B batch survival or repaired id-stream proof is claimed.
No identity pins or receipt-body goldens were regenerated or changed. The
orchestrator owns staging, commits, successor scheduling, and the landing gate.

Open question: what causes the pre-existing standalone `test_arcb_close_fixes`
id/seed mismatch, and should it be tracked as a separate ledger item?

## Socket-blocked symbolic checks and baseline comparisons

The 25 symbolic-check failures below are blocked by the environment's socket
policy. Calling the public `pf_sandbox.run_sandboxed_python` with a trivial
harness returned `ok=False`, `returncode=1`, and this exact diagnostic:

```text
bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted
```

These tests expected symbolic `checked` verdicts but received `model` or
`sandbox_failed`. Every one of their eight files was rerun alone with all modified
Python files temporarily restored to `HEAD`; **the same 25 failure nodes recur**.
All working edits were then restored byte-for-byte. No sandbox bypass was added.

| Command with HEAD Python sources | Last result line |
| --- | --- |
| `t.sh tests/test_reader_rw2b_fix10.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 3 passed in 15.18s` |
| `t.sh tests/test_reader_rw2b_fix11.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 4 passed in 11.48s` |
| `t.sh tests/test_reader_rw2b_fix12.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 5 passed in 3.62s` |
| `t.sh tests/test_reader_rw2b_fix14.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 3 passed in 4.55s` |
| `t.sh tests/test_reader_rw2b_fix15.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `1 failed, 1 passed in 2.83s` |
| `t.sh tests/test_reader_rw2b_fix4.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `4 failed, 15 passed in 4.27s` |
| `t.sh tests/test_reader_rw2b_fix5.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `6 failed, 8 passed in 3.71s` |
| `t.sh tests/test_reader_rw2b_review.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin` | `10 failed, 19 passed in 4.37s` |
| `t.sh tests/test_reread_safety_landing.py -q -n 2 -o 'pythonpath=src .' -p tests._epp1_sandbox_plugin -vv -o faulthandler_timeout=10` | `killed by external timeout (exit -9); no pytest result summary` |

Exact socket-blocked symbolic test nodes:

```text
tests/test_reader_rw2b_fix10.py::test_item1_enable_check_disable_then_resume_recheck_hint_and_report_never_read_checked
tests/test_reader_rw2b_fix11.py::test_item1_the_diagnosers_trace_reads_a_stored_checked_verdict_as_the_models_when_off
tests/test_reader_rw2b_fix12.py::test_item3_a_hint_in_flight_when_the_switch_goes_off_writes_and_stores_the_models_reading
tests/test_reader_rw2b_fix14.py::test_items_2_3_a_row_stored_checked_reads_as_the_models_everywhere_once_the_switch_is_off
tests/test_reader_rw2b_fix15.py::test_item2_a_switch_off_during_context_assembly_masks_the_rendered_trace
tests/test_reader_rw2b_fix4.py::test_item1_a_long_step_is_checked_whole_or_not_at_all
tests/test_reader_rw2b_fix4.py::test_item2_solving_against_a_written_restriction_is_never_checked
tests/test_reader_rw2b_fix4.py::test_item3_a_checked_claim_is_stored_exactly_as_it_was_verified
tests/test_reader_rw2b_fix4.py::test_item6_odd_roots_and_fractional_powers_of_a_possibly_negative_base_are_never_checked
tests/test_reader_rw2b_fix5.py::test_items_1_2_a_restricted_name_is_not_used_by_any_kind_and_taints_names_that_write_it
tests/test_reader_rw2b_fix5.py::test_items_1_2_a_solve_or_substitution_whose_own_text_restricts_a_domain_is_never_checked
tests/test_reader_rw2b_fix5.py::test_items_1_2_a_solve_through_a_restricted_name_is_never_checked
tests/test_reader_rw2b_fix5.py::test_items_1_2_a_substitution_into_a_restricted_name_is_never_checked
tests/test_reader_rw2b_fix5.py::test_items_1_2_names_are_never_resolved_and_a_name_free_step_still_checks
tests/test_reader_rw2b_fix5.py::test_items_1_2_two_definitions_differing_only_in_their_restriction_never_resolve
tests/test_reader_rw2b_review.py::test_f10_a_check_appends_the_models_and_the_verifiers_verdicts_with_the_row
tests/test_reader_rw2b_review.py::test_f14_a_claim_failing_twice_falls_to_the_next_step_without_it
tests/test_reader_rw2b_review.py::test_f14_a_claim_that_does_not_hold_is_reasked_once_naming_it
tests/test_reader_rw2b_review.py::test_f14_a_hints_checkable_claim_is_verified_and_labelled_checked
tests/test_reader_rw2b_review.py::test_f2_exact_identities_and_decimals_keep_their_labels
tests/test_reader_rw2b_review.py::test_f2_false_or_domain_dependent_identities_are_never_checked_as_holding
tests/test_reader_rw2b_review.py::test_f3_an_unrelated_checked_expression_never_validates_the_learners_step
tests/test_reader_rw2b_review.py::test_f3_the_learners_own_expression_is_checked_and_decides_the_step
tests/test_reader_rw2b_review.py::test_f3r_an_operator_is_checked_on_its_written_operand_and_names_on_their_definitions
tests/test_reader_rw2b_review.py::test_f3r_the_whole_written_relation_is_what_is_checked
```

The separate `tests/test_reread_safety_landing.py` run timed out after two tests
completed, both with this patch (120-second limit) and with HEAD Python sources
(45-second diagnostic limit). Its thread dump identifies
`test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path`,
waiting in `_call_all` / `anyio.run` / `selectors.select` through the in-process
MCP client. That case remains unverified; no socket-specific root cause is
claimed for this hang. The remaining three cases are rerun below without the
temporary TestClient plugin and with only this case deselected.

The temporary plugin has been removed. The initial 120 standalone-file runs'
completed summaries total **1,927 passed, 26 failed, 131 skipped, 1 xfailed**,
plus the timed-out reread file (not counted as passing). Of the 26 failures,
25 are the sandbox-blocked symbolic checks above and one is the pre-existing
`test_arcb_close_fixes` id/seed failure. Of the 131 skips, 119 are the explicitly
listed TestClient cases and 12 are pre-existing skips. This is not a clean
landing-gate claim.

| Final subset command, without the temporary plugin | Last result line |
| --- | --- |
| `t.sh tests/test_reread_safety_landing.py -q -n 2 --deselect tests/test_reread_safety_landing.py::test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path` | `3 passed in 4.14s` |

Including that completed subset, standalone-file summaries have 1,930 passes;
the blocked MCP case remains unverified. The final tracked diff passes
`git diff --check`; the new review note also has no whitespace errors. The only
untracked deliverable is this review note. No prohibited file or private vault
was opened, and no machine path was written into a deliverable.
