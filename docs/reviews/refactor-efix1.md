# Fix round after the arc E review, part 1: grading

Branch `fix/arc-e-review-grading`, from main `8804080fcf`. The adversarial review of arc E (`914145d0b9..8804080fcf`, read-only) reported eleven findings; this part takes findings 1, 2, 3 and 6, the holes it found in the second K5 fix batch ([refactor-k5-fixes-2.md](refactor-k5-fixes-2.md)). The reviewer ran nothing, so each scenario was first turned into a failing test. Ledger rows ER-1, ER-2, ER-3 and ER-6 are in [refactor-bug-ledger.md](refactor-bug-ledger.md). No algorithm tag, migration or config switch.

## ER-1: full marks with nothing assessed (review finding 1) — reproduced

- **Verified.** On the review's rubric (`form` 0 points, `setup` 2, `result` 2) a divergent-route grade with `setup` and `result` at 0 and nothing located scored 4/4 (correctness 1.0, not held, reason `valid_alternative_unverified`). The same grade with `result` left out also scored 4/4. A regrade to the first grade was not held either (its score was not separately probed). `tests/test_blind_grading_contract.py` pinned 2/2 on `setup` beside a wrong, omitted `result` as 4/4.
- **Contract checked first.** The structured-output schema lets `criterion_evidence` be any list (`default_factory=list`); the own-route prompt says "Grade EVERY criterion", and for a step it cannot verify, "explain why in its evidence and list it in `unverified_criterion_ids`". No prompt lets the grader leave a criterion out, so refusing omission matches what the grader is asked for.
- **Rule now.** An ordinary-practice proposal (the blind validator and the practice door) must carry a row for every criterion of a nonempty rubric. Otherwise it is refused with the same validation error as an empty one, so the required door fails, the optional door falls back, and a regrade fails its run and keeps the live rows and due date. Teach-back stays sparse. Where a grade is taken over the assessed criteria (PF-c's gate, the own-route rule, a regrade through them), criteria worth no points that would be the only ones left assessed become unverified with the rest (`grading_support.weightless_remainder`). The grade is then what nothing assessed makes it: held for review when nothing validated the answer, and PF-c's verified answer (full marks for scheduling, no evidence) when the final answer was verified. `assessed_rubric_score` has no zero-denominator default.
- **Diff.** `attempts/grading.py`: the omission check replaces the empty check and the rescale, and `omitted_criterion_ids` and `evidence_for_storage` go. Callers in `attempts/attempts.py` and `attempts/regrade.py` store only what was reported. `attempts/grading_support.py`: the post-run block that added omitted criteria to the unverified set goes. `weightless_remainder` is applied in the gate and the rule, and its rows get their own note. `assessed_rubric_score` scores over the criteria with points.
- **Feedback.** A row is labelled "not assessed (a different route)" only when it carries the unassessed marker, and only the gate or the rule writes that marker now (the live test asserts the marked rows equal the rule's unverified set). A zero-point criterion folded in by the rule carries the rule's note "worth no points, and no criterion worth points was assessed", but desktop and terminal still show the generic label.
- **Fail-first.** `tests/test_route_rules_in_grader.py`: `test_er1_a_grade_that_leaves_out_a_criterion_is_refused` (did not raise), `test_er1_nothing_with_points_assessed_is_held_not_full_marks[live, regrade]` (`held_for_review` False), `test_er1_the_rules_treat_a_weightless_remainder_as_nothing_assessed` (unverified lacked `form`). The rewritten `test_blind_grading_contract.py::test_ordinary_grade_requires_every_criterion[partial]` did not raise. All pass after.
- **Assertions changed.** `test_blind_grading_contract.py`: the partial case's old expectation (4/4, `result` marked unassessed) was the defect itself: the full grade was 0/2 on `result`, and the omission decided the grade. It now expects refusal. `test_route_rules_in_grader.py`: `test_f1_live_an_incomplete_grade_with_nothing_located_is_held[missing_row]` expected a hold for a grade missing a row. It is now `test_f1_live_an_incomplete_grade_is_refused` (both cases refused, nothing stored, schedule kept). `test_f1_live_an_incomplete_regrade_keeps_an_existing_hold` now expects the omitting regrade to raise too, and checks the evidence is untouched. The pure `test_f1_an_omitted_criterion_is_unlocated...` is unchanged, because the rule still reads an omission as unlocated before validation refuses the grade.

## ER-2: diagnosis reads an unassessed row as an assessed zero (finding 2) — reproduced, left open

- **Verified.** ER-1 removes the synthetic rows. Rows the own-route rule or PF-c marks unassessed are real rows with the same marker. For a hypothesis whose only claim is that `result` fell short, beside `setup` at 2/2:
  - against a row marked unassessed, trace consistency said `consistent_with_claims` (`every_attributed_claim_held`), and the criterion receipt made `result` an assessable failed criterion;
  - against a genuinely assessed zero, the answer is the same, as it should be.
- **Why it stays open.** Replay rematerializes the receipt from the stored rows (`materialize_causal_episode` in the attempt apply path). A spy showed one rebuild of the test vault calling the trace-consistency reader for the attempt. Skipping marked rows in both readers, with `canonical_projection.unassessed_evidence_row`, therefore changes what a rebuild computes for stored diagnosed attempts, so it waits for the next algorithm tag.
- **Test.** `tests/test_causal_trace_consistency_p2.py::test_a_criterion_left_unassessed_neither_holds_nor_fails_a_claim` is a strict xfail. Before it was marked, it failed on `consistent_with_claims`. Its control is `test_an_assessed_zero_holds_a_shortfall_claim`.

## ER-3: `grading adjudicate` could commit another head (finding 3) — reproduced

- **Verified through the CLI.**
  - At `mvp-0.60`, a zero-point answer ruled `success` (A) and then confirmed `success` (B): B skipped its evidence revision (direction unchanged), so the current grade was A's revision. Replay compared that grade with B's reviewed raw event, read a regrade, missed B's marker and appended an automatic interpretation as head. The command printed B.
  - At `mvp-0.59` the command's replay re-minted the observation and printed "downstream state rebuilt"; the ruling was off the observation the ledger reads.
- **Rule now.**
  - A ruling that confirms an earlier ruling's revised grade writes that grade again as its own revision (`append_adjudication`), so replay's existing protection holds.
  - The command replays only when the grade channel fixes are on (`mvp-0.60` or later). Below that it prints "Derived state was not rebuilt: this vault is at mvp-0.59, below mvp-0.60. The upgrade to mvp-0.60 rebuilds it with this ruling; a rebuild before then keeps a revised grade but drops the ruling's head (refactor bug ledger D-52)." Saying "the next rebuild" would have been false there, since D-52 drops the head.
  - Before it commits, the command requires the ruling to be the head of its observation and that observation to be the one the ledger reads for the attempt. Otherwise it raises inside the transaction, rolls back and exits 1 ("Adjudication rolled back: …").
  - The JSON output gains `derived_state_rebuilt`.
- **Fail-first.** In `tests/test_grading_cli.py`:
  - `test_a_confirmation_of_an_adjudicated_grade_stays_the_head` failed with the head being an automatic interpretation, not B;
  - `test_below_the_grade_channel_fixes_adjudicate_does_not_replay` failed because "downstream state rebuilt" was printed;
  - `test_adjudicate_refuses_to_commit_a_head_its_replay_displaced` failed with exit 0.

  All pass after. `test_adjudicate_rolls_back_a_replay_that_fails_after_its_reset` re-applies one attempt after the reset and then throws: the existing outer transaction already rolled that back, and the test passed before and after (the old test threw on entry).
- **Measured, not changed.** The command holds `BEGIN IMMEDIATE` from the ruling to its commit. The measurement used production SQLite settings (outside pytest), one learning object of self-graded answers on three items, timing the whole command and its replay:

  | Attempts in the learning object | Command (s) | Replay (s) |
  |---|---|---|
  | 10 | 0.27 | 0.08 |
  | 100 | 1.56 | 1.38 |
  | 300 | 7.83 | 7.62 |
  | 1,000 | 69.31 | 69.07 |

  The growth is superlinear. Past roughly 250 answers in one learning object, a competing writer's five-second busy timeout runs out while the command holds the lock. The largest synthetic learning object a test builds was not identified. These are vaults built for the measurement.

## ER-6: legacy exam imports could reach the grader (finding 6) — reproduced

- **Verified.** A seeded score-only import whose answer was set to "\t\n", "  " or "\r\x0b\x0c　", with NULL notes as written before K5-15, was selected for deferred regrade and was not score-only for the explicit regrade. An import with no import rows (what an empty rubric left before K5-15) was not score-only (NULL read as "has work").
- **Rule now.** The legacy fallback trims the code points `str.isspace` accepts, the rule `seed_exam_attempts` uses. The list is a constant pinned to Python's by a test, and SQLite's `trim(x, char(...))` applies it. `is_score_only_exam_import` reads the attempt's own type: an `exam_evidence` attempt (written by exam seeding alone) is score-only unless an import row says `learner_work`, or a legacy row passes the fallback. Any other attempt is never score-only.
- **Fail-first.** In `tests/test_deferred_regrade.py`, `test_a_legacy_import_whose_answer_is_only_whitespace_is_score_only` failed in all three cases and `test_a_legacy_import_with_no_import_rows_is_score_only` failed; both pass after. They are joined by `test_the_legacy_whitespace_rule_is_pythons` and the control `test_an_attempt_that_is_not_an_import_is_never_score_only_by_absence`.

## Left open

- **ER-2** waits for the next algorithm tag.
- **Lock duration (ER-3)** was measured and not changed.
- **The hard-case harness.** `diagnosis/grading_hardcases.py` models the production path with the gate and the rule but no validation. It still scores a grade that leaves a criterion out as unlocated or held, where production now refuses it. That affects only its report's fidelity, so it waits for the harness's next version (ER-1's row).
- **Behaviour change for new grades (ER-1).** A divergent-route grade that leaves a criterion out used to be held (or, after K5 batch 2, scored over the rest). It is now refused, so the practice door's fallback or failure applies. This follows the ruling, with no tag, as intake behaviour. Under the 2026-10-17 eligibility rule it changes which new answers become measurements, which is worth a look.
