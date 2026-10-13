# Proof alternatives and the confidence arm: Codex review fixes

Stage: `grading/proof-alternatives` (worktree `learnanything-grading-proofs`).
Reviewed: `f2f02e32..46bd019f` (the stage record is
`proof-alternatives-and-confidence-arm.md`).
Review: Codex job `20261013-021054-mX9nZ8` (gpt-6-astra, effort high), 8
findings (3 High, 5 Medium). All 8 reproduced and were fixed; none was
rejected. F8's last step, real traces in cells 3-4, needs the owner's data and
is open (below).

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Unlocated proof failures still become negative evidence | fixed | `17c17b44` | `test_proof_route_check.py`: `test_p1_an_unlocated_mark_down_on_a_divergent_route_is_unassessed[×3]`, `test_p1_a_located_error_still_counts_from_either_judge`, `test_p1_applies_only_to_a_divergent_route_without_fatal_errors`, `test_p1_nothing_assessed_and_nothing_validated_is_held_for_review`, `test_p1_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed`, `test_p1_live_nothing_located_and_nothing_validated_is_held_for_review` |
| F2 | High | The checker can override a deterministic wrong answer | fixed | `17c17b44` | `test_proof_route_check.py`: `test_a_conclusion_that_differs_from_the_reference_is_never_restored_or_unassessed`, `test_f2_live_the_checker_never_restores_a_wrong_final_answer[policy on, policy off]` |
| F3 | High | Additional paid calls bypass the practice command's spend controls | fixed | `c7bb7c65` | `test_proof_route_check.py`: `test_the_reading_and_the_check_are_admitted_on_their_own_route`, `test_a_refused_check_stops_the_grade_and_is_never_sent`, `test_cli_dry_run_plans_the_route_check_with_the_grade`, `test_cli_a_metered_check_without_a_price_is_refused_before_any_call`, `test_cli_admits_and_meters_the_check_on_its_route` |
| F4 | Medium | Checker-adjusted grades reuse the old calibration identity | fixed | `12e017ed` | `test_proof_route_check.py`: `test_a_checked_grade_is_calibrated_under_its_own_identity`, `test_a_regrade_records_the_identity_of_the_grade_it_produced` |
| F5 | Medium | Undamped Newton iteration silently returns an unconverged confidence fit | fixed | `32140dfc` | `test_answer_signal_arms.py`: `test_the_fit_converges_where_an_undamped_newton_step_oscillates`, `test_a_fit_that_cannot_converge_says_so` |
| F6 | Medium | Hard-case results bypass the production item-kind gate | fixed | `d9b14f02`, `ba562671` (reading budget) | `test_grading_hardcases.py`: `test_the_gate_follows_the_production_path`, `test_the_gate_applies_p1_to_a_divergent_route`, `test_a_failed_case_is_counted_never_a_crashed_run` |
| F7 | Medium | Hard-case verdicts never enter `judgment_ledger` | fixed | `d9b14f02` | `test_grading_hardcases.py`: `test_a_run_scores_both_error_rates_per_route_and_the_gate_per_pair` (ledger rows, content keys, a rerun adds none), `test_repetitions_are_fresh_and_give_a_noise_floor` |
| F8 | Medium | The evaluation cannot answer the specified P2/R2 questions | fixed (harness, cell 1, labels); real traces open | `d9b14f02` | `test_grading_hardcases.py`: `test_the_tracked_gold_set_is_valid_and_covers_every_cell`, `test_a_set_without_real_traces_is_labelled_smoke_coverage`, `test_the_grader_arms_cross_the_reference_and_the_check`, `test_repetitions_are_fresh_and_give_a_noise_floor`, `test_a_dry_run_plans_every_role_and_builds_no_client`, `test_the_cli_dry_run` |

**Reproduction first.** Each finding was reproduced before its fix:

- **F1, F2, F3, F4, F5.** The new tests were run against the code just
  before each fix: `src/` stashed for F1-F3, and a `git archive` of
  `17c17b44` on pytest's path for F4. All failed:
  - F1/F2: 11 of 11. Through the live practice door, "Name a prime" answered
    "…so the answer is 4" was restored from 0/4 to **4/4** (`(4, 1.0) ==
    (0, 0.0)`), with PF-c's policy on and off. An unlocated, unvalidated
    mark-down on a divergent route stayed assessed.
  - F3: 5 of 5. The admission log saw only `blind_grading`. The denying
    guard did not stop the check. With a metered checker route and no price,
    `learnloop attempt` sent both calls and exited 0. It charged 1 call, not 3.
  - F4: 2 of 2. A checked grade's blind record and raw grade event carried
    `grading_prompt_v2_1_blind_reference_policy`.
  - F5: the saturated case returned `b = -2.5e-07`, not −2.713.
- **F6, F7.** These were reproduced against the reviewed harness (`git show
  46bd019f:…/grading_hardcases.py`) with the same fakes, on the v1 cases:
  - F6: a strict grader checked by a route whose own reading is not
    proof-like scored **0/6** wrong rejections. Production skips the check
    there and keeps 6/6.
  - F7: 84 calls left **0** `judgment_ledger` rows.
- **F8.** All six v1 valid alternatives check `undecidable`, so cell 1 was
  absent. The harness had no arm, repetition or provenance input.

### What changed

**F1: P1's located-error rule, scoped as P1 scopes it.** The gate now
receives the grader's own `route_check.divergent_route` (P1's trigger).
On a divergent route whose conclusion is not shown to differ, a criterion
marked down with no error located verbatim by either judge is `unlocated`.
That covers the grader's attribution and the checker's quote, and it holds
whether the check abstained or refuted without a quote. `unlocated` means
unverified, so unassessed.

- A located error from either judge still counts.
- Fatal errors keep their mark-downs.
- Off a divergent route nothing changes. An incomplete answer that follows
  the reference's route is still marked down.
- **Held for review.** PF-c's "nothing assessed schedules as correct" rule
  rests on a verified final answer, and a dispute rests on the checker's
  affirmative validation. When every criterion ends unlocated and nothing
  validated the answer, the grade is also held for review
  (`proof_route_check_flag`) so it does not rest on nothing. See open
  question 1.

**F2: the machine check outranks the checker.** `gate_inputs` passes the
deterministic `final_answer_check` status into the gate. It comes from PF-c's
policy, or is computed when `diagnosis.grading_support` is off. When the
conclusion `differs_from_reference`:

- nothing is restored, disputed or left unassessed (the outcome is
  `answer_differs`, counted as a disagreement);
- a flag still stands.

The gate version is now `proof-route-check-v2`.

**F3: planned, admitted and metered.**

- **Admission.** The reading and the check run inside `admit_grading_call` on
  their own spend route (`proof_check`), with the checker's client. A
  command's guard can therefore classify a metered or subscription checker
  before it admits a call. A refusal or cancellation propagates: the grade
  stops with nothing recorded, as a refused grading sample does. The check no
  longer swallows it as `unavailable`.
- **Planning.** `plan_grading_calls` plans the check calls as an upper bound:
  one reading, then a check only if proof-like. A cached reading decides.
- **The attempt command.** `learnloop attempt` registers the checker's route
  before sending anything. Its dry run and up-front admission estimate the
  grade and the check together, and the help text says so.

**F4: a checked grade has its own calibration identity.** A grade with
`status = checked` is calibrated under
`grading_prompt_v2_1_blind_reference_policy+proof-route-check-v2:proof-route-check-v1@<checker model>`.
That identity is on the blind record (where replay reads it) and on the raw
grade event, and a regrade records the identity of the grade it produced.
Every grade the grader produced alone keeps the base identity: predecessors,
the kill switch, a non-proof-like item and an unavailable check.

**F5: damped Newton.** Each Newton direction is backtracked on the log
posterior (Armijo). Convergence is checked on the gradient, and a fit that
does not converge raises `ArithmeticError` instead of returning a wrong
optimum. `FIT = logistic-map-damped-newton-v2`, so the arms' version hashes
move. The saturated case now returns b = −2.713 (p = 0.123), the MAP
optimum.

**F6: the production path.** For each (grader route, checker route, arm),
the gate runs PF-c's gate with the real deterministic check. It then runs
the route-check gate only where the checker route's own item reading is
proof-like and its check returned, passing the final-answer status and the
grader's divergent-route reading. Otherwise PF-c's grade stands, as live
grading does:

- `unclassified`: the reading failed;
- `not_proof_like`: the reading said no;
- `unavailable`: the check failed.

Each gate row reports how often the check ran, and a failed check is no
longer a failed gate case.

**F7: every verdict in the ledger.** After scoring, each grader, checker and
item-kind verdict is appended through `PFCaller.ledger`:

- task `grading_hardcase_<role>`, left `grading_hardcase` /
  `<case id>@<content digest>`, the judge model, the prompt version (with the
  arm) and the call's input hash;
- the verdict: the outcome and the per-criterion points or verdicts;
- the score: the rubric fraction (grader) or the established share
  (checker).

The id is content-keyed, so a cached or resumed call ensures its judgment
without duplicating it. A rerun of the fake run ensured 96 and left 96 rows.

**F8: four cells, crossed arms, fresh repetitions, honest labels.**

- **Gold set v2.** `fixtures/grading_hardcases/cases_v2.json` (16 cases) adds
  P2's cell 1: two valid alternatives whose final answer the deterministic
  check verifies. One computes a determinant by row reduction against a
  cofactor reference; the other finds a dice probability by the complement
  against a direct count. Both were checked by hand. A case's cell now
  follows from the check, not a label. Each case names its `provenance`; a
  `real_trace` must name its `source`. v1 is kept for the recorded run.
- **Labels.** Every report (JSON and markdown) carries `gold_set.kind =
  "synthetic smoke coverage"` while cells 3-4 hold no real traces, plus a
  `limitations` list. That list names the missing real traces, a run with no
  repeat-run noise floor, and the arms not run.
- **Arms.** `--ablations` crosses the reference shown or withheld
  (`solve_first`, C2) with the final-answer check shown to the grader or
  withheld from it (C3's "or not at all" variant). A withheld check also
  withholds the C2 verifier observations, which compare the answer with the
  reference. The gate still applies the real check, and the production arm's
  prompt is byte-identical to before, so its checkpoints still hit. R2's
  remaining factor, with or without the re-derivation rule, is the grader
  row against the gate row.
- **Repetitions.** `--repeats N` runs separately identified fresh
  repetitions. Repetition 0 is the plain call; later repetitions carry their
  index in the call settings, so each has its own checkpoint and no
  repetition reuses another's answer. A resumed run still pays nothing twice.
  Every judge row reports `noise_floor`: how often its outcome on a case
  changed between repetitions.

## Live verification

### F5 on the owner's data (no model calls)

`learnloop eval --section field --legacy-fallback current_content` ran on a
backup-API copy of the stage's `linear_algebra` evaluation copy
(`fixtures-local/proofs-eval/linear_algebra-field-f5`) with the damped fit.
For every arm in the stage record's Part 2 table, the log loss, Brier,
reliability and resolution agree with the recorded values to about 1e-11.
The owner's rows never reached the oscillating case, so the recorded table
stands. Only the arms' version hashes moved.

### F6-F8: the v2 hard-case run (OpenRouter, on the backup-API copy)

**Setup.**

- **Where.** Gold set v2 on `fixtures-local/proofs-eval/linear_algebra`, the
  stage's backup-API copy.
- **Judges.** `or_haiku` (`anthropic/claude-haiku-5.5`) and `or_luna`
  (`openai/gpt-6-luna`, `reasoning_effort = low`).
- **Prices.** $0.10 / $0.50 per million input / output tokens.
- **Scope.** All four grader arms, two repetitions.
- **Dry run first:** 384 calls, upper bound $1.78, inside the $3 cap
  (`hardcases-v2-dry-run.json`).

**How it ran.**

1. The first combined run was stopped when Haiku truncated an item reading at
   the harness's 600-token budget. The live door would have completed that
   reading, so the budget is now 2000 (`ba562671`), and the dry run was
   repeated.
2. The second combined run was stopped so the two routes could run in
   parallel, one process each with the same caps. Every completed call was
   checkpointed, so nothing was paid twice.
3. A final combined run rebuilt the report from the checkpoints. It sent 6
   grader calls: retries of calls that had failed.

**Spend.** Provider-reported cost from the copy's receipts: **350 requests,
$0.5056**.

- Haiku: 183 requests, $0.4068.
- Luna: 165 requests, $0.0988.
- Two requests cut off by the stops report no usage.

With the stage's first run ($0.0808, 85 requests), the stage has billed
**$0.586** in total. Keys were loaded by the app, and no tracked vault was
opened.

**Ledger (F7).** The run ensured 382 `grading_hardcase_*` judgments: 384
calls less 2 failed ones. Rerunning from the checkpoints added none.

**Results.** This is synthetic smoke coverage, as the report says.

| Judge (production arm, rep 0) | Haiku: wrong rejection | Luna: wrong rejection | Wrong acceptance | Changed across repeats |
|---|---|---|---|---|
| grader | 1/8 | 1/8 | 0/8 both | Haiku 1/16, Luna 0/16 |
| checker | 1/8 | 1/8 | 0/8 both | 0/16 both |
| gate, all four (grader, checker) pairs | 0/8 (1 unassessed) | 0/8 (1 unassessed) | 0/8 | 0-1/16 |

- **The new cell-1 case did its job.** In the determinant computed by row
  reduction, the `minors` criterion is phrased in the reference's method.
  Every grader and every checker marked it down, in every arm. The checker
  did so against its own rule: a criterion phrased in one method is
  established by any valid method.
  - **The gate.** PF-c's gate (the final answer verifies) makes the unlocated
    mark-down unassessed. In the repetitions where the grader quoted a step,
    it stays a rejection: that is the gate's 1/16 noise floor.
- **The arms (C2, C3) do not separate on this set.**
  - Solve-first with the check withheld added one Haiku wrong rejection (the
    tail-sum proof) and one failed case.
  - Solve-first with the check shown left one Luna-grader gate rejection.
  - No arm differs from production by more than one case in eight.
- **The production path (F6) shows up.** Haiku's item reader read the dice
  case as a computation (not proof-like) once, so the gates with a Haiku
  checker report `checked 15, not_proof_like 1`. Luna read all 16 as
  proof-like.
- **Failures.** The Haiku grader failed 2 calls, each in one repetition: a
  truncation at 6000 output tokens (solve-first, check shown) and an invalid
  output (solve-first, check withheld). They count as failed cases, never as
  acceptances.

Reports: `fixtures-local/proofs-eval/reports-v2/` (combined), plus
`reports-v2-haiku/` and `reports-v2-luna/`. They are not committed.

## Gate

The gate ran on the branch tree at `ba562671`, the last code commit (later
commits are docs only), with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| Setup: `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **14 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8766 passed**, 0 failed (the stage gate had 8741; this step adds 25 tests) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8672 deselected |
| DB reference: `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: 299 table notes, 354 owned notes, 3941 wikilinks checked. The schema did not change (no migration); the reference was regenerated because it cites source lines (`8a159cac`), and validated again after `ba562671` |
| CLI help snapshot | regenerated for `attempt` (`--max-calls` and the spend paragraph) and `grading hardcases` (`--ablations`, `--repeats`, the v2 default) |

- **Not applicable.** No file under `apps/learnloop-tauri` changed, so the
  npm and cargo steps do not apply.
- **Mobile allowlist.** No sidecar RPC was added, so
  `tests/test_mobile_allowlist.py` is unchanged.
- **Test flags.** Both pytest runs also passed `-q -p no:cacheprovider`.

## Open questions

1. **Held for review, but still scheduled as correct.** When every criterion
   ends unassessed, `assessed_rubric_score` still schedules the attempt as
   correct, the PF-c rule. F1's fix adds a review flag when nothing validated
   the answer, but leaves the scheduling alone: that is a change to PF-c's
   shared rule. It is the stage record's open question 2 in a second case.
   Should a fully unassessed attempt with no verified answer schedule as
   neither correct nor failed?
2. **P1 is scoped to the grader's own `divergent_route`.** That is P1's
   trigger, but it is the grader's reading, and a grader that misses a
   divergence keeps its unlocated mark-downs. Should the checker's restated
   route also count as evidence of divergence?
3. **Real traces (F8).** The harness can now answer P2/R2 once cells 3-4
   hold real traces. The sources are the owner's adjudicated proofs from the
   vaults, R5's flagged correct-answer cases, and the MAP
   `True_Misconception` rows after a licence check. None can be written by
   an agent.
4. **C3's "late" variant.** The check is withheld from the grader, not
   revealed after `local_analysis_md`. A two-turn reveal would need a second
   call per case. Is the "not at all" arm enough for C3?
5. **Not findings, recorded from the review's conformance table.** Neither
   is built in this fix step:
   - R4's family/month decomposition and the reliability-trend report;
   - the duel's within-bin residual for continuous forecasts.
