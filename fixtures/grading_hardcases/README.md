# Grading hard cases (gold set v2)

The ITS sweep's P2 gold set (owner decision 2026-10-13), read by
`learnloop grading hardcases` (`src/learnloop/diagnosis/grading_hardcases.py`) and by
`tests/test_grading_hardcases.py` with fakes. Not a vault: no database, no
learner data. The cases were written for this stage and checked by hand.

**Synthetic smoke coverage.** Every case is `synthetic_hand_checked`. P2 asks
for real traces in cells 3-4 (the Bitter Lesson rule "validate the grader only
on real traces"), so until some are added every report says the rates are
smoke coverage, not P2/R2 estimates (Codex review F8).

`cases_v2.json` (the default) holds 16 cases in the owner's subjects (linear
algebra and probability), each an item (prompt, reference solution, rubric)
and one answer, in P2's four cells. A valid alternative's cell follows from
the deterministic final-answer check, not from a label:

| Cell | Cases | A correct judge |
|---|---:|---|
| 1 `valid_alternative_checkable`: a valid route other than the reference's, final answer verified by the check | 2 | gives full credit; any mark-down is a **wrong rejection** |
| 2 `valid_alternative_proof`: a valid proof by a route other than the reference's, no verifiable final answer | 6 | the same |
| 3 `correct_flawed`: the right final answer from invalid reasoning | 4 | marks down the labelled criteria; full credit there is a **wrong acceptance** |
| 4 `wrong_looks_right`: a fluent proof that is wrong | 4 | the same |

`cases_v1.json` is the 14-case set the stage's first live run used (cells 2-4
only); it is kept so that run's report stays reproducible.

Each answer is labelled by `label.failing_criteria`, the criteria a correct
grader marks down (empty for valid alternatives), and `notes` says why. Each
case names its `provenance`: `synthetic_hand_checked`, or `real_trace` with a
`source` (the loader refuses a real trace without one).

Adding a case: keep the reference solution on a different route from a valid
alternative's answer (that is what makes it hard), label only criteria whose
failure is unambiguous, and bump the file's `version` (a new file,
`cases_v3.json`, keeps reports comparable).

Real traces: the owner's own adjudicated proofs from the vaults are the
first source (R5's flagged cases too). The Eedi MAP Kaggle rows labelled
`True_Misconception` (a correct choice explained with a misconception) could
fill the `correct_flawed` cell with real student text; see the harness's
`EEDI_MAP_NOTE` for the limits. None are included.
