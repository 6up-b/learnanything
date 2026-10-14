# Grading hard cases (gold set v3)

The ITS sweep's P2 gold set (owner decision 2026-10-13), read by
`learnloop grading hardcases` (`src/learnloop/diagnosis/grading_hardcases.py`) and by
`tests/test_grading_hardcases.py` with fakes. Not a vault: no database, no
learner data. The cases were written for this stage and checked by hand.

**Synthetic smoke coverage.** Every case is `synthetic_hand_checked`. P2 asks
for real traces in cells 3-4 (the Bitter Lesson rule "validate the grader only
on real traces"), so until some are added every report says the rates are
smoke coverage, not P2/R2 estimates (Codex review F8).

`cases_v3.json` (the default, harness `grading-hardcases-v4`) holds 20 cases
in the owner's subjects (linear algebra and probability), each an item
(prompt, reference solution, rubric, and for cell 5 a required method) and one
answer. A valid alternative's cell follows from the deterministic final-answer
check, not from a label:

| Cell | Cases | A correct judge |
|---|---:|---|
| 1 `valid_alternative_checkable`: a valid route other than the reference's, final answer verified by the check | 3 | gives full credit; any mark-down is a **wrong rejection** |
| 2 `valid_alternative_proof`: a valid proof by a route other than the reference's, no verifiable final answer | 7 | the same |
| 3 `correct_flawed`: the right final answer from invalid reasoning | 4 | marks down the labelled criteria; full credit there is a **wrong acceptance** |
| 4 `wrong_looks_right`: a fluent proof that is wrong | 4 | the same |
| 5 `required_method_bypassed`: the statement requires a method (`item.required_method`), the answer reaches the result correctly by another valid method | 2 | fails exactly the method criteria (labelled) and credits every other criterion on the facts: full credit on a method criterion is a requirement **not enforced**, a mark-down elsewhere a **fact rejected**; the requirement counts as **enforced** only when the method criteria failed and every other criterion has full credit (a criterion left unassessed makes the case unassessed) |

Cell 5 (method-explicit items, owner rule 2026-10-13) is reported apart from
P2's rates (`required_method` in each summary). Each of its cases is paired
with the same mathematics without a required method and with criteria phrased
by fact, a cell 1-2 valid alternative that any valid method passes:

| Required method (cell 5) | Same mathematics, no required method |
|---|---|
| `la-det-required-cofactor-by-row-reduction` (cofactor expansion required, row reduction used) | `la-det-no-required-method-row-reduction` (cell 1) |
| `pr-at-least-one-six-required-inclusion-exclusion-by-complement` (inclusion-exclusion required, complement used) | `pr-at-least-one-six-no-required-method-complement` (cell 2) |

The loader checks that a required method's prompt requires it (naming the
method is not enough), that its
criteria are in the rubric, and that a cell 5 case's labelled criteria are
exactly the method's criteria.

`cases_v2.json` is the 16-case set (cells 1-4) of the route-rules live run, and
`cases_v1.json` the 14-case set the stage's first live run used (cells 2-4
only); both are kept so those runs' reports stay reproducible.

Each answer is labelled by `label.failing_criteria`, the criteria a correct
grader marks down (empty for valid alternatives), and `notes` says why. Each
case names its `provenance`: `synthetic_hand_checked`, or `real_trace` with a
`source` (the loader refuses a real trace without one).

Adding a case: keep the reference solution on a different route from a valid
alternative's answer (that is what makes it hard), label only criteria whose
failure is unambiguous, and bump the file's `version` (a new file,
`cases_v4.json`, keeps reports comparable).

Real traces: the owner's own adjudicated proofs from the vaults are the
first source (R5's flagged cases too). The Eedi MAP Kaggle rows labelled
`True_Misconception` (a correct choice explained with a misconception) could
fill the `correct_flawed` cell with real student text; see the harness's
`EEDI_MAP_NOTE` for the limits. None are included.
