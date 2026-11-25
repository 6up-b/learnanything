# mvp-0.74 selected forecast receipts

The predecessor is mvp-0.73. H3-R6 and H3-R7 change the interpretation of an answer’s forecast. The upgrade uses the existing whole-vault rebuild. The schema and historical receipt ledgers need no migration.

## Replay boundary

At mvp-0.74, a bound plan answer reads the selection for its block, slot and chosen item. Surprise uses the threshold receipt for the selected subject or learning-object view, including the repeat forecaster. When the draw records the chosen probability, the receipt must match it at the draw’s stored precision. A missing selection or selected receipt yields the recorded `mastery` source. An unbound answer can use its own grade receipt. Under mvp-0.73, bound answers prefer the subject receipt and can fall through to the grade receipt.

New assessment contracts cite the full practice item's revision. A contract first frozen when the item is presented (the item view, a workbench check) also saves that revision in `practice_item_snapshots`, so opening a check freezes the revision used for its grade-time forecast; a contract frozen at a grade cites it only (H3-R25). The writer checks the recorded session and probe administration before consuming a plan presentation. A rejected binding leaves the presentation available and records a mastery fallback. An answer to its own presentation at another revision keeps the link and records the mastery fallback, live and on replay (H3-R24). Replay checks the original presentation contract even after a regrade. Older ordinary answers can establish the revision from the grade receipt. For older inline answers with no frozen forecast revision, that receipt can describe a later edit, so replay uses mastery.

The tag does not change the mastery calculation. The two-tag selection test checks the forecaster key, the marked fallback and the complete surprise records before and after rebuilding. The frozen-item and wrong-session tests exercise both tags. The upgrade test with an intervening item edit checks that a formerly accepted receipt loses its eligibility.

## Fixes independent of replay version

- An exam answer’s existing ID determines its attempt ID. A single transaction checks the link, applies the grade and links the result. Finishing resumes each linked answer’s completion work before publishing the report.
- Lesson checks and probes prepare a forecast before acquiring the outer write lock. They check the standing question and attempt again before writing. A concurrent withdrawal leaves the losing grade unapplied.
- Newly issued grade-time snapshots identify the graded attempt, item revision, evidence cutoff and protection epoch. Existing receipts retain their original bytes.
- Four-way arm (f) runs production replay at the input’s retirement-era tag, or mvp-0.71 for an earlier input. Its private rows retain mastery and scoring values separately. Synthetic .71 and .72 histories compare every surprise row and mastery row with production, with all three receipt sources represented.
- Shadow reports digest surprise rows, grade receipts and subject KL observations in identity order with canonical JSON. The doctor reads the recorded grading denominator or stored correctness. Historical feedback reads the values that triggered the gate when available.
- The probe-router chain test names its inline-check predecessor explicitly.

## Gate failures

The landing gate on the round's commit failed 18 tests. Two were defects of this tag, fixed before landing (ledger H3-R24, H3-R25); one was a test layout violation; two are stopped for the orchestrator (H3-R26, H3-R27).

- H3-R24: the binding check dropped an answer's link to its own presentation when the item was edited between the serve and the answer, so an answer to a held-out revision became an unbound answer adaptive difficulty read. The link now stays; surprise compares the receipt's revision with the answered one live as on replay, and reads mastery. It fixed `test_ad23_fix_r9.py`, `test_ad23_contract.py` and `test_ad_projection.py` with H3-R25.
- H3-R25: every contract saved the item's revision in `practice_item_snapshots`, including contracts frozen by grading, so a protected answer's grade wrote a visible public-revision row. Only a contract first frozen at a presentation saves it now; an answer on a contract a grade froze first is forecast from the item while it is unchanged. It fixed the required-method tests (their setup could no longer delete the graded revision's snapshot), `test_facet_outcome_view.py`'s future-receipt case and `test_epp_repeat_receipts.py`'s snapshot-writer case.
- Layout: `test_selected_forecast.py` and `test_lesson_grade_forecast.py` imported test modules. The shared `_surprise`, `_open` and `_served` moved to `tests/surprise_reads_ad_forecast_helpers.py`, `tests/teacher_te1_lesson_helpers.py` and `tests/teacher_te2_review_fixes_helpers.py`.
- H3-R26, stopped: `test_ad_epoch.py::test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed` answers in session `s1` a presentation served in `s2`, which H3-R7 refuses, so `assert status() == "frozen"` fails before the protection step. Options: (a) the test answers in the serving session (`session_id="s2"`, a setup change; the whole test then passes with every assertion as written), recommended; (b) accept a draft from another session, which reverts H3-R7.
- H3-R27, stopped: adaptive difficulty draws only at planned new-material slots, so a repeat never has a serve selection, and at this tag no repeat answer reads its `ad_threshold_repeat@*` receipt. `test_epp_repeat_receipts.py::test_repeat_receipts_move_no_id_seed_receipt_score_or_state_under_a_frozen_clock` expects the subject repeat receipt; `test_selected_forecast.py::test_selection_view_and_missing_selection_live_and_rebuilt` expects mastery for a repeat with no selection. Options: (a) a slot with no serve selection at all reads the subject view's receipt, as mvp-0.73 did (a recorded draw that does not verify still reads mastery); this passes the repeat test and changes the selected-forecast test's no-selection expectation to the subject repeat receipt, recommended, since the view then never depends on today's configuration; (b) the slot's view from `promoted_predictor` at replay, which a later configuration change would move; (c) keep mastery and change the repeat test's expectation, leaving the repeat forecasters unread by surprise.

## Owner-copy verification

Use a disposable, backup-API copy of an mvp-0.73 vault for `COPY`, one fixed UTC instant for `AS_OF` and a new private directory outside the copy for `PRIVATE`. Run in the isolated environment from the repository root. The detailed snapshots, reports, and diagnostics stay in the private directory. Only the final command writes to stdout.

```sh
set -eu
umask 077
mkdir -p "$PRIVATE"
snapshot() {
  .venv/bin/python scripts/label_retirement_counts.py snapshot "$COPY" \
    --as-of "$AS_OF" --out "$PRIVATE/$1.json" > "$PRIVATE/$1-counts.json" 2>> "$PRIVATE/run.log"
}
snapshot before
.venv/bin/learnloop upgrade --vault "$COPY" --to mvp-0.74 > "$PRIVATE/upgrade.log" 2>&1
doctor_status=0
.venv/bin/learnloop doctor --vault "$COPY" > "$PRIVATE/doctor.log" 2>&1 || doctor_status=$?
snapshot after
for pass in 1 2; do
  .venv/bin/learnloop rebuild --shadow --json --vault "$COPY" > "$PRIVATE/shadow-$pass.json" 2>> "$PRIVATE/run.log"
done
.venv/bin/python scripts/label_retirement_counts.py compare "$PRIVATE/before.json" "$PRIVATE/after.json" \
  > "$PRIVATE/comparison.json" 2>> "$PRIVATE/run.log"
.venv/bin/python - "$PRIVATE" "$doctor_status" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
def read(name):
    return json.loads((root / name).read_text())

before, after = (read(name + "-counts.json") for name in ("before", "after"))
comparison = read("comparison.json")
a, b = (read(f"shadow-{i}.json")["shadow_rebuild"] for i in (1, 2))
counts = {
    "doctor_nonzero_exits": int(int(sys.argv[2]) != 0),
    "integrity_failures": int(not after["integrity_ok"]),
    "foreign_key_violations": after["foreign_key_violations"],
    "grade_receipts_before": before["grade_time_receipts"],
    "grade_receipts_after": after["grade_time_receipts"],
    "gate_records_before": before["attempts_with_gate_records"],
    "gate_records_after": after["attempts_with_gate_records"],
    "shadow_gate_records_changed": b["followup_gate_records"]["changed"],
    "trained_subject_rows": after["ad_trained_subject_rows"],
    "subject_rows_with_kl": after["ad_rows_with_kl"],
    "surprise_directions_changed": comparison["surprise_direction_changed"],
}
for name in ("mastery_changed", "surprise_changed", "due_items_moved"):
    counts[name] = int(comparison[name].split("/")[0])
for source in ("mastery", "serve_receipt", "grade_receipt"):
    for side, sample in (("before", before), ("after", after)):
        counts[f"{source}_{side}"] = sample["surprise_by_source"][source]
for family in ("surprise", "grade_receipts", "subject_kl"):
    left, right = (r["forecast_digests"] for r in (a, b))
    counts[f"{family}_shadow_differences"] = sum(
        x != y for x, y in ((left["before"][family], left["after"][family]),
                            (right["before"][family], right["after"][family]),
                            (left["after"][family], right["after"][family])))
print(json.dumps(counts, sort_keys=True))
PY
```

Expect zero mastery changes, integrity failures, foreign-key violations and shadow differences. Grade receipt counts and recorded gate counts should agree across the upgrade. Surprise values and sources can move when the selected view or recorded provenance changes the scoring input. Investigate doctor findings in the private log.

## Synthetic copy run

The procedure above ran on a synthetic mvp-0.73 history with 12 answers. It retained 12 grade receipts and all 8 subject KL details. The 9 bound answers had no AD selection row and moved from serve receipts to mastery. The 3 unbound answers kept their grade receipts. Mastery, due dates and surprise directions each had 0 changes. Doctor exited successfully, integrity and foreign-key checks reported 0 failures, and all three forecast digest comparisons reported 0 differences. Owner copies require a separate run.

## Generated baselines

The tag enters nine existing identity pins, the effective defaults, the CLI upgrade default and the placement manifest. The full-item revision serializer moved into `vault.hashes` with its canonical encoding preserved. The grade-application and diagnosis-journey writers capture the tag, grade metadata and frozen revisions. The CLI surface writer also captured the notebook check command and compatible options on workbench commands. The JSON size ceiling accounts for the 454 extra lines in the diagnosis journey and 61 in the CLI surface. H3-R25 removed 436 of the diagnosis journey's lines again: its four grade-time `practice_item_snapshots` rows (the golden regenerated with `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`; nothing else in it moved).

## Local verification

The sandbox regression command used the checkout venv, an isolated home and config directory, one worker and the following explicit targets. It finished with 547 passing tests. The separate chain check covered all 48 edited chain test functions. With two inline RPC tests and the counts reporter it finished with 55 passes. The import check kept all 55 contracts.

```sh
python -m pytest -q -n 1 -p no:cacheprovider \
  tests/test_selected_forecast.py \
  tests/test_exam_session.py \
  tests/test_lesson_grade_forecast.py \
  tests/test_surprise_reads_ad_forecast.py \
  tests/test_difficulty_four_way.py \
  tests/test_difficulty_receipt_arms.py \
  tests/test_calibration.py \
  tests/test_shadow_rebuild.py \
  tests/test_probe_router.py \
  tests/test_teacher_te1_lesson.py \
  tests/test_teacher_te2_review_fixes.py \
  tests/test_reader_rd7a_inline_checks.py::test_inline_forecast_uses_the_item_opened_before_an_edit \
  tests/test_structure_ratchets.py \
  tests/test_assessment_contracts.py \
  tests/test_effective_defaults_golden.py \
  tests/test_cli_help_snapshot.py::test_no_command_or_parameter_changed_incompatibly \
  tests/test_grade_application_golden.py \
  tests/test_diagnosis_journey_golden.py \
  tests/test_placement_diagnosis_decides.py::test_stored_misses_read_as_with_the_split_on \
  tests/test_upgrades.py::test_the_table_is_the_chain_from_the_floor_one_row_per_tag \
  'tests/test_upgrades.py::test_a_link_activates_from_its_predecessor_and_a_rerun_does_nothing[mvp-0.74]' \
  'tests/test_upgrades.py::test_a_jump_is_refused_and_nothing_changes[mvp-0.74]' \
  tests/test_post_attempt_pipeline.py \
  tests/test_identity_pins.py
```

The fail-first runs reproduced these outcomes in synthetic histories before the corresponding change.

| Finding | Observed before the fix |
| --- | --- |
| H3-R6 | The LO draw used the subject receipt. A separate inconsistent recorded probability still produced a serve score. Both runs gave 1 failure and 1 pass. |
| H3-R7 | A foreign session consumed the presentation and an edited item supplied the grade forecast. The first run gave 2 failures and 2 passes. The separate revision-mismatch upgrade regression failed on replay. |
| H3-R8 | The grade survived a failed link write. The first run gave 1 failure and 4 passes. A separate test failed because an already-linked answer’s completion was still pending after retry. |
| H3-R16 | Both preparation paths held the writer lock, giving 2 failures and 15 passes. In a second interleaving test, a probe retired by a second connection appeared as an unavailable grader, giving 1 failure and 1 pass. |
| H3-R17 | The grade snapshot named a serve. The run gave 1 failure and 2 passes. |
| H3-R13 and L4-2 | Arm (f) diverged from production on both .71 and .72. The run gave 2 failures and 1 pass. |
| H3-R20 and H3-R21 | The changed rubric and rebuilt gate values leaked into historical displays, and the shadow comparison missed the changed row contents. The run gave 3 failures and 8 passes. |
| L4-2 router chain | Swapping the predecessor made the explicit assertion fail. Restoring the chain made the test pass. |
