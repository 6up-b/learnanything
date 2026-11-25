# mvp-0.74 selected forecast receipts

The predecessor is mvp-0.73. H3-R6 and H3-R7 change the interpretation of an answer’s forecast. The upgrade uses the existing whole-vault rebuild. The schema and historical receipt ledgers need no migration.

## Replay boundary

At mvp-0.74, a bound plan answer reads the selection for its block, slot and chosen item. Surprise uses the threshold receipt for the selected subject or learning-object view, including the repeat forecaster. When the draw records the chosen probability, the receipt must match it at the draw’s stored precision. A slot with no draw recorded at all (every repeat) uses the subject view's receipt; a recorded draw that does not verify, or a missing selected receipt, yields the recorded `mastery` source (FR3-19). An unbound answer can use its own grade receipt. Under mvp-0.73, bound answers prefer the subject receipt and can fall through to the grade receipt.

New assessment contracts cite the full practice item's revision. A contract first frozen when the item is presented (the item view, a workbench check) also saves that revision in `practice_item_snapshots`, so opening a check freezes the revision used for its grade-time forecast; a contract frozen at a grade cites it only (H3-R25). The writer checks the recorded session and probe administration before consuming a plan presentation: a presentation still open in another session is left for that session's answer; one from the answer's own session, from an answer naming no session, or from a session that had ended by the answer's time binds (H3-R29). A rejected binding leaves the presentation available and records a mastery fallback. An answer to its own presentation at another revision keeps the link and records the mastery fallback, live and on replay (H3-R24). The answered revision is the one the answer's grade receipt names, on both sides; an answer without a grade receipt reads mastery (H3-R28). A slot with no serve draw recorded at all (every repeat) reads the subject view's receipt, as at mvp-0.73 (H3-R27). For inline answers whose contract froze no revision, the grade receipt can describe a later edit, so they read mastery.

The tag does not change the mastery calculation. The two-tag selection test checks the forecaster key, the marked fallback and the complete surprise records before and after rebuilding. The frozen-item and wrong-session tests exercise both tags. The upgrade test with an intervening item edit checks that a formerly accepted receipt loses its eligibility.

## Fixes independent of replay version

- An exam answer’s existing ID determines its attempt ID. A single transaction checks the link, applies the grade and links the result. Finishing resumes each linked answer’s completion work before publishing the report.
- Lesson checks and probes prepare a forecast before acquiring the outer write lock. They check the standing question and attempt again before writing. A concurrent withdrawal leaves the losing grade unapplied.
- Newly issued grade-time snapshots identify the graded attempt, item revision, evidence cutoff and protection epoch. Existing receipts retain their original bytes.
- Four-way arm (f) runs production replay at the input’s retirement-era tag, or mvp-0.71 for an earlier input. Its private rows retain mastery and scoring values separately. Synthetic .71 and .72 histories compare every surprise row and mastery row with production, with all three receipt sources represented.
- Shadow reports digest surprise rows, grade receipts and subject KL observations in identity order with canonical JSON. The doctor reads the recorded grading denominator or stored correctness. Historical feedback reads the values that triggered the gate when available.
- The probe-router chain test names its inline-check predecessor explicitly.

## Gate failures

The landing gate on the round's commit failed 18 tests. Two were defects of this tag, fixed before landing (ledger H3-R24, H3-R25); one was a test layout violation; two were decided by the orchestrator (H3-R26, H3-R27). Its follow-up fixed two more (H3-R28, H3-R29).

- H3-R24: the binding check dropped an answer's link to its own presentation when the item was edited between the serve and the answer, so an answer to a held-out revision became an unbound answer adaptive difficulty read. The link now stays; surprise compares the receipt's revision with the answered one live as on replay, and reads mastery. It fixed `test_ad23_fix_r9.py`, `test_ad23_contract.py` and `test_ad_projection.py` with H3-R25.
- H3-R25: every contract saved the item's revision in `practice_item_snapshots`, including contracts frozen by grading, so a protected answer's grade wrote a visible public-revision row. Only a contract first frozen at a presentation saves it now; an answer on a contract a grade froze first is forecast from the item while it is unchanged. It fixed the required-method tests (their setup could no longer delete the graded revision's snapshot), `test_facet_outcome_view.py`'s future-receipt case and `test_epp_repeat_receipts.py`'s snapshot-writer case.
- Layout: `test_selected_forecast.py` and `test_lesson_grade_forecast.py` imported test modules. The shared `_surprise`, `_open` and `_served` moved to `tests/surprise_reads_ad_forecast_helpers.py`, `tests/teacher_te1_lesson_helpers.py` and `tests/teacher_te2_review_fixes_helpers.py`.
- H3-R26, by decision: `test_ad_epoch.py::test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed` answered in session `s1` a presentation served in the still-open session `s2`, which H3-R7 leaves for its own session. The test now answers in the serving session (a setup change; every assertion as written).
- H3-R27, by decision: adaptive difficulty draws only at planned new-material slots, so a repeat never has a serve selection, and no repeat answer read its `ad_threshold_repeat@*` receipt. A slot with no serve draw recorded at all now reads the subject view's receipt, as at mvp-0.73; a recorded draw that does not verify still reads mastery. `test_selected_forecast.py`'s no-selection case expects the subject repeat receipt.
- H3-R28: live took the answered revision from today's item (or the contract frozen at open) and replay from the contract the grade froze (else the grade receipt). Both now read the revision the answer's grade receipt names, a row stored before the grade, and an answer without one reads mastery on both sides.
- H3-R29: the session rule refused the desktop after a restart, the workbench after its admission session ended and a draft naming no session. A presentation now binds once its session had ended by the answer's time, or for an answer naming no session; one still open in another session stays refused. `tests/test_answer_door_sessions.py` has one test per door that names a presentation and an inventory of the doors.

## Review round 3

The Astra review of tags 0.73-0.75 and three rows of the writer-fence review (ledger FR3-1 to FR3-22). Fixed in this
round, by class:

- Protection (FR3-1, FR3-2, FR3-14): `db.stores.answered_revision` is the one reader of the stored facts naming what an
  attempt answered (the presented contract, the plan presentation's frozen revision, the selection's, the grade
  receipt's). The material view withholds an attempt when any of them is withheld; the grade-time forecaster asks the
  view about every revision the answer names, so a held-out one yields no forecast, receipt, snapshot or hash; a
  presentation saves the revision it shows even after a grade froze the same contract. The A8 contract fixture gains
  the contract door (opened outside the plan, the item replaced, the source protected).
- One instant per grade (FR3-7, FR3-8): a live grade reads the clock once under the write lock; exam finish dates
  each answer by one read as it is applied, never ahead of now.
- The opening replay rule states both no-draw cases (FR3-19).

None of these needed a tag: they are protection fixes and live writes; replay of stored rows is unchanged.

Continued (the second worker of the round):

- A rebuild derives (FR3-6, owner decision b): the activity backfill creates administrations, exposures and
  observations only for history recorded before the substrate existed, i.e. before the vault's first administration
  written live (`legacy_backfilled = 0`, a stored fact; a vault that never wrote one has nothing to backfill). A later
  answer whose grade-channel write failed (no observation, or an observation without a raw grade) is never given one
  by a rebuild or an upgrade: replay writes a missing grade record only for pre-substrate history, a regrade's own
  answer and an explicit repair. The rebuild names it (the activity replayer's details and a warning), `learnloop
  doctor` reports `answers:grade_record_missing` in plain words, and `doctor --fix-state` records it through the same
  channel. The ordinary grade's dual-write failure is logged where it happens. One consequence by the decision: an
  exam answer regraded below mvp-0.61 and upgraded past it is recorded on the exam channel by the repair, not by the
  upgrade's rebuild. No tag: no stored row changes meaning; a rebuild stops writing rows no live write recorded (a
  vault with complete records rebuilds exactly as before).
- Atomic doors: a retried exam import replays the object it already wrote (FR3-9, FR3-21); exam finish applies an
  answer accepted while it runs before publishing completion, keeps the sitting open while such an answer is pending,
  and admission is checked in the answer's own write transaction (FR3-3); a retried finish counts the intervention
  slots earlier tries used and resumes an attempt's failed completion work (FR3-13); the lesson check's and lesson
  probe's answer turn commits with its grade (FR3-22). FR3-20 was verified fixed by `74ab78be7e`.
- FR3-23 (a rebuild after a two-answer sitting), owner decision (b): a live grade that reaches `apply_attempt` with
  criterion points and no evidence rows has the given points recorded as its rows (`local_grader_id` `given_points`,
  `grader_tier` 0, a tier no grader writes), so replay, which reads `grading_evidence`, applies what live applied;
  the tests' due item seeds through the seed door. No tag: every grader door already wrote its rows, and replay of
  stored rows is unchanged.

Third worker: FR3-23 by decision (b) (above); FR3-4 under mvp-0.76 and FR3-17 without a tag
([algorithm-mvp-0.76.md](algorithm-mvp-0.76.md)).

Fourth worker: FR3-5's timing half, FR3-11, FR3-15 and FR3-16 under mvp-0.76; FR3-5's protection half, FR3-10, FR3-12
and FR3-18 without a tag
([algorithm-mvp-0.76.md](algorithm-mvp-0.76.md)).

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
