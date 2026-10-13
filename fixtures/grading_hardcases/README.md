# Grading hard cases (gold set v1)

The ITS sweep's P2 gold set (owner decision 2026-10-13), read by
`learnloop grading hardcases` (`src/learnloop/diagnosis/grading_hardcases.py`) and by
`tests/test_grading_hardcases.py` with fakes. Not a vault: no database, no
learner data. The cases were written for this stage and checked by hand.

`cases_v1.json` holds 14 cases in the owner's subjects (linear algebra and
probability), each an item (prompt, reference solution, rubric) and one answer:

| Category | Cases | A correct judge |
|---|---:|---|
| `valid_alternative`: a valid proof by a route other than the reference's | 6 | gives full credit; any mark-down is a **wrong rejection** |
| `correct_flawed`: the right final answer from invalid reasoning | 4 | marks down the labelled criteria; full credit there is a **wrong acceptance** |
| `wrong_looks_right`: a fluent proof that is wrong | 4 | the same |

Each answer is labelled by `label.failing_criteria`, the criteria a correct
grader marks down (empty for valid alternatives), and `notes` says why.

Adding a case: keep the reference solution on a different route from a valid
alternative's answer (that is what makes it hard), label only criteria whose
failure is unambiguous, and bump the file's `version` (a new file,
`cases_v2.json`, keeps reports comparable).

Real traces: the Eedi MAP Kaggle rows labelled `True_Misconception` (a
correct choice explained with a misconception) could fill the
`correct_flawed` cell with real student text; see the harness's
`EEDI_MAP_NOTE` for the limits. None are included.
