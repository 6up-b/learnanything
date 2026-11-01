# Fix: grader tests that failed from 12:00 UTC on 2026-11-01

Branch `fix/grader-date-nov1`, from main `6a218dfd82`. Test-only change: no production code,
no persisted meaning, no migration, no algorithm version.

## Symptom

Four tests failed every time on `6a218dfd82` and `06f54da975`. The same tests had passed a few
hours earlier in the full suite on `317185da34` (23068 passed), and the code had not changed
in between:

- `tests/test_route_rules_in_grader.py::test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals`
- `tests/test_route_rules_in_grader.py::test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`
- `tests/test_route_rules_in_grader.py::test_f5_a_joint_regrade_supersedes_a_route_verdict`
- `tests/test_required_method_grading.py::test_a_regrade_at_the_successor_keeps_the_method_rule_and_a_full_credit_regrade_clears_it`

## Cause

Both files define `CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))`. When they were
written on 2026-10-13, that instant was in the future. Each failing test does the same two things:

1. It submits the attempt with `tests.split_live_helpers.submit(...)` and no `when=`, so the
   attempt, its blind grade record and its route verdict are stamped with the **wall clock**.
2. It regrades with `clock=CLOCK`, so the regrade's blind record and judgment rows are stamped
   **2026-11-01T12:00Z**.

The "current" grade is the latest one by `created_at`: `latest_blind_grade_record` orders by
`created_at DESC, id DESC`, and the tests' `_route_judgments` orders by `created_at, rowid`.
That held while the wall clock was before 12:00 UTC on 2026-11-01. Once the wall clock passed it,
each regrade sorted *before* the grade it replaced, so the tests read the original grade:
`clarification_located_criterion_ids == []` and `method_route_criterion_ids == ['setup']`.
In f4 and f5 the supersession order came out reversed. In f5 (joint), `append_judgment` stamps the
seeded verdict with `datetime.now()`, which also landed after the regrade.

`test_f5_a_regrade_with_the_rule_switched_off_supersedes_the_held_verdict` regrades at
`CLOCK + 1 day` and `+ 2 days`. It would have started failing at 12:00 UTC on 2026-11-02.

Production code is not affected. A real regrade runs on the system clock, so it always comes
after the grade it replaces. Only a test that mixes wall-clock writes with a frozen clock that
has fallen into the past can reorder them.

## Evidence

All runs used the required memory-capped scope (`env -i`, empty HOME/CODEX_HOME/config dir,
TMPDIR outside the worktree). To move the whole process's wall clock (`datetime.now`,
`time.time`, ...), a scratch pytest plugin started `time_machine.travel(<instant>, tick=True)`.
time-machine was loaded as an ephemeral `uv run --with time-machine` overlay, so the project
venv and lockfile were not touched. Results on the unfixed tree, both files:

| wall clock              | result                         |
|-------------------------|--------------------------------|
| 2026-11-01T11:00Z       | 66 passed                      |
| 2026-11-01T12:30Z       | the 4 tests above fail         |
| 2026-11-02T13:00Z       | those 4 + f5 switched-off fail |
| 2027-01-15T12:00Z       | the same 5 fail                |
| real (12:42Z)           | the 4 tests above fail         |

## Fix

- `tests/test_route_rules_in_grader.py`: new `SUBMITTED = CLOCK.now() - timedelta(hours=1)`, with
  a comment saying why. The f3-live, f4 (route verdict), f5 (switched off) and f5 (joint) tests now
  submit with `when=SUBMITTED`. f5 (joint) also gives its seeded judgment an explicit
  `created_at` between the grade and the regrade.
- `tests/test_required_method_grading.py`: the same `SUBMITTED`, used by the
  successor-regrade test.
- No assertion was changed or loosened. The submit → regrade order the tests describe is now
  fixed instead of depending on the wall clock.

## Sweep for the same pattern

Two groups of test files were run with the wall clock at real now, 2026-11-02T13:00Z and
2027-01-15T12:00Z:

- the other files with a hard-coded `FrozenClock` on or after 2026-11-01:
  `test_ad23_fix_review`, `test_deliverable_codex_review`, `test_pfc_unverified_unassessed` and
  `test_regrade_contract_upgrade` (2026-12-01);
- every test file with a quoted date in 2026-11/12 or later (24 files).

That is 632 tests. All passed at real now and at 2026-11-02. At 2027-01-15, one more failed:

- `tests/test_deliverable_path.py::test_am_i_ready_creates_one_check_per_untested_lo_never_an_exam_reserved_item`
  creates a goal with `due_at="2026-12-01"` on the wall clock and asserts
  `due_hint <= "2026-12-01"`. `check_due` never schedules before now: for a deadline already
  passed it returns today, which is correct product behaviour. So this test would fail from
  2026-12-02. Fix: the deadline is now 30 days after the wall clock, and the assertion compares
  against that deadline. The 14-day cap was already the binding bound when the test was written,
  so the assertion is just as strong.

## Tests run (after the fix)

- `test_route_rules_in_grader.py`, `test_required_method_grading.py` and `test_deliverable_path.py`
  under time travel to real now, 2026-11-01T11:00Z, 2026-11-02T13:00Z and 2027-01-15T12:00Z:
  83 passed each time.
- Without time travel, the same three files plus every file importing from them
  (`test_forecast_receipts`, `test_held_grade_composition`, `test_forecast_receipts_landing`,
  `test_regrade_contract_replay`, `test_held_grade_evidence`, `test_ux_phase4_landing`,
  `test_required_method_authority`, `test_ux_phase4_feedback`, `test_ai_compare`,
  `test_regrade_contract_successor`): 468 passed.

Left as is: a few other tests in these two files also submit on the wall clock and then regrade
at `CLOCK`, for example the method-rule regrades. None of them asserts on the order between the
two, and they passed at every instant tried.
