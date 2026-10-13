# Codex review of route-check-in-grader: fixes

Stage `route-check-in-grader`, branch `grading/route-check-in-grader`,
worktree `learnanything-merge4`. The review (codex-job
`20261013-142216-WC0p8B`) read the diff `e238fa07a..516a5d4ee`. It found two
High and two Medium defects. All four reproduced, and all four are fixed. None
was rejected.

## Findings

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | An omitted criterion prevents a required hold | fixed | `ceae5937a` | `test_f1_an_omitted_criterion_is_unlocated_and_with_nothing_assessed_holds`; `test_f1_live_an_incomplete_grade_with_nothing_located_is_held[missing_row, empty_output]`; `test_f1_live_an_incomplete_regrade_keeps_an_existing_hold` |
| F2 | High | Explicit grader uncertainty is discarded on proofs | fixed | `ceae5937a` | `test_f2_a_criterion_the_grader_declares_unverified_is_unassessed_on_a_divergent_route`; `test_f2_live_declared_uncertainty_on_a_quoted_step_is_unassessed`; `tests/test_grading_hardcases.py::test_the_production_path_reads_the_graders_declared_uncertainty` |
| F3 | Medium | Errors quoted from clarification replies are erased | fixed | `ceae5937a` | `test_f3_a_quote_from_the_learners_clarification_reply_locates_an_error`; `test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals` |
| F4 | Medium | Serving route verdicts no longer reach the judgment ledger | fixed | `ceae5937a` | `test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`; `test_f4_no_route_verdict_without_the_rules` |

Tests are in `tests/test_route_rules_in_grader.py` unless another file is
named. `d877e1737` regenerates the DB/config reference at the code commit.

## Reproduction

Every new test was run on `516a5d4ee` (the reviewed tip) before any fix, and
all failed except one: 9 failed, 1 passed. The test that passed was
`test_f4_no_route_verdict_without_the_rules`. It is a negative test, and the
ledger was empty there too.

A probe with the same fakes, at mvp-0.18, gave these numbers before the fix:

| Finding | Scenario | Before the fix |
|---|---|---|
| F1 | `setup = 0`, `result` omitted, divergent route, nothing located | 0/4, `held_for_review = false`, `assessed_shortfall = false`, **schedule moved** (an FSRS failure) |
| F1 | empty `criterion_evidence`, divergent route | 0/4, not held, **schedule moved**; the rule did not apply at all |
| F2 | grader declares `setup` unverified, quotes a real step, `setup = 0, result = 2` | **2/4**, `unverified_criterion_ids = []` despite `grader_unverified_criterion_ids = ["setup"]` |
| F3 | clarification regrade quotes the learner's reply "All continuous functions are differentiable." against `setup` | **4/4**, `setup` unassessed as if the quote were fabricated |
| F4 | any ruled grade or regrade | no `judgment_ledger` row |

The hard-case test failed on the unfixed `gate_states` too: 6 wrong
rejections instead of 0.

## What changed

The fixes are all in `apply_route_rule` and its two callers. The rule still
reads only the grader's own output and makes no model call. The prompt, the
prompt version (`…+own-route-v1`) and the calibration identity are unchanged.

### F1: an omitted criterion

- **Before.** Validation scores a grade as the sum of the rows present, so an
  omitted criterion scores 0. The rule read the same omission as full points,
  so it was never "below", never unlocated, and never counted against the
  hold.
- **Now.** On a divergent route the rule reads an omitted criterion as 0,
  which is what validation scores it.
  - So it is a mark-down like any other: unlocated (unassessed) unless an
    attribution in force locates it. If one does, it stays an assessed 0.
  - The hold is computed over what is then actually assessed. A missing-row
    grade or an empty grade with nothing located is **held**: the grader's
    own 0/4, no FSRS review, the schedule untouched, no diagnosis, and replay
    keeps it.
- **Regrades.** An incomplete regrade of an existing hold holds again. It no
  longer releases the hold without assessing anything.
- **`revalidated_support`.** It now reads an omitted row as 0 too.
- **Why this option and not rejection.** The review offered rejecting
  incomplete coverage instead. Treating the omission as unassessed was
  preferred:
  - rejection would fail the learner's grading call over the grader's slip
    (owner principle: never add a learner step to protect the model);
  - a validator change would also change every earlier version's grading.

### F2: the grader's declared uncertainty

- **What changed.** `request_blind_grading_run` now passes the grader's own
  `unverified_criterion_ids` to the rule (`declared_unverified`). The
  hard-case production path does the same.
- **The rule.** On a divergent route, a criterion below full points that the
  grader declared it cannot verify is unassessed, whether or not it quotes a
  step.
  - Its evidence note reads "Not assessed: the grader could not verify this
    step of your own route."
  - Its attributions are rescoped to `grader_interpretation`.
  - With nothing else assessed and nothing validated, the grade is held.
- **The exceptions still stand.**
  - A conclusion that `differs_from_reference` keeps its mark-downs.
  - So does a fatal error.
  - A declared criterion at full points is not this rule's.
  - Unknown ids are ignored.
  - A route the grader does not read as divergent is not this rule's.
  - PF-c still owns the declaration on a verified final answer.
- **The record.** It lists these criteria as
  `declared_unverified_criterion_ids`, beside `unlocated_criterion_ids`.

### F3: the learner's clarification reply

- **What changed.** On a clarification regrade, the rule also searches the
  learner's reply (`clarification_exchange.answer_md`) for a quote, using the
  same case- and whitespace-insensitive match as for the answer. The machine's
  question is never passed to the rule, so quoting it locates nothing.
- **Which text supplied the quote.** The record lists, under
  `clarification_located_criterion_ids`, the criteria that stay assessed only
  because of a quote from the reply.

### F4: the ledger verdict

- **Task.** `grading_support.record_route_rule_judgment` appends one row per
  ruled grade to `judgment_ledger`, task `own_route_rule`. The task is free
  text, so no migration is needed.
  - The row is written in the transaction that records the grade and its blind
    record: `_complete_blind_graded_attempt` for live grades, the regrade's
    publication transaction for regrades.
  - It is written only when the rule ran (`status = checked`), so the kill
    switch, earlier versions and PF-c-off vaults write none.
- **Row fields.**
  - `left = attempt`, `judge = llm`.
  - `judge_model`: the grader's resolved model.
  - `prompt_version`: the grader's (`…+own-route-v1`).
  - `input_hash`: the blind grading context hash, the same as the blind
    record's `context_hash`.
  - `verdict`: the rule record plus `grader_unverified_criterion_ids` and
    `concrete_error_located`, as canonical JSON.
  - `rationale`: a one-line summary.
- **Regrades** supersede the attempt's current verdict (`supersedes_id`).
- **Replay** writes none. The test rebuilds and counts the rows again.
- **Model calls.** No additional model call.

## Not changed (scope)

- **PF-c's gate.** It is mvp-0.16 semantics, so it is not changed here. On a
  verified final answer it still searches only the answer and reads an
  omitted criterion as full points. See the open questions.
- **The record version.** It stays `route-rules-in-grader-v1`. The branch is
  unmerged, so no record under it exists outside tests and `fixtures-local`
  copies.
- **The mvp-0.17 replay fixture.** It replays unchanged. The new record keys
  appear only on new records.
- **Paid calls.** None were made. Every fix is deterministic server-side
  logic over the grader's output, and F4 needs no model call.

## Gate

Run on the tree at `d877e1737`, with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9425 passed**, 0 failed (5 min 27 s; 9414 at the reviewed tip plus the 11 new tests) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **96 passed**, 9329 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 186, 308 table notes, 763 configuration leaves in 46 sections, stamped at `ceae5937a` |

**Shadow rebuild (playbook item 7).** `learnloop rebuild --shadow` was rerun
on the existing backup-API copy `fixtures-local/shadow_la` (at mvp-0.18). It
made no model call.

- facets: 0 changes;
- schedule: 0 changes;
- mastery: 21 rows changed, and the only differing field is
  `algorithm_version` (mvp-0.17 → mvp-0.18), as in the stage record;
- the copy's database hash was unchanged.

Replay reads the records as written, so the fixes change only new grades.

**Not applicable:**

- No file under `apps/learnloop-tauri` changed, so the npm and cargo steps do
  not apply.
- No migration and no schema change.

Targeted runs before the gate:

- the new tests plus the held-grade, hard-case, replay, upgrade, ledger and
  stuck files: 183 passed;
- every grading, regrade, clarification, PF-c, held, split, upgrade and router
  test file (47 files): 644 passed.

## Open questions

1. **PF-c's gate has the same two blind spots on a verified final answer.**
   - It searches only the answer, so an error revealed only in a
     clarification reply is unassessed when the final answer matches the
     reference. That erases a real error.
   - It reads an omitted criterion as full points.
     - On a divergent route the rule now catches the omission.
     - On a route the grader does not call divergent, validation still scores
       the omission as an assessed 0. That can be a failure on a verified
       answer.

   Fixing either changes mvp-0.16/0.17 grading, so it needs the owner's call:
   under the mvp-0.18 successor only, or as its own successor.
2. **Omitted criteria elsewhere.** Outside this rule, validation still scores
   an omitted criterion 0 as an assessed failure, at every version. Should
   incomplete criterion coverage be unassessed (or rejected) generally?
3. **A ledger verdict with no successor.** A regrade that does not run the
   rule (kill switch flipped off later, or a joint regrade) writes no
   `own_route_rule` verdict. The attempt's previous verdict then stays current
   in the ledger, although the grade it describes was replaced. A reader can
   match the verdict's `input_hash` to the latest blind record's
   `context_hash`. The alternative is a superseding "not checked" row.
4. **Declared uncertainty on a route the grader does not call divergent** is
   still read only by PF-c, on a verified final answer. The prompt asks for
   the declaration on a different route, so this is consistent with the
   rules. A grader that declares uncertainty without setting
   `divergent_route` gets no protection on an undecidable answer.
5. **Carried over from the stage record:**
   - the mvp-0.18 relabel at merge;
   - the kill switch's name;
   - the `+own-route-v1` identity suffix;
   - Haiku 5.5's strict-schema refusals;
   - method-phrased criteria.

# Re-review

The re-review (codex-job `20261013-151129-qrDOcp`) confirmed F1, F2 and F3 as
fixed. It reopened F4: route verdicts reach the ledger and checked regrades
supersede them, but supersession was incomplete. That gap is filed as F5.
F5 reproduced and is fixed. Nothing was rejected.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | An omitted criterion prevents a required hold | confirmed fixed (re-review) | `ceae5937a` | unchanged; tests above |
| F2 | High | Explicit grader uncertainty is discarded on proofs | confirmed fixed (re-review) | `ceae5937a` | unchanged; tests above |
| F3 | Medium | Errors quoted from clarification replies are erased | confirmed fixed (re-review) | `ceae5937a` | unchanged; tests above |
| F4 | Medium | Serving route verdicts no longer reach the judgment ledger | reopened, closed by F5 | `681f25cea` | its supersession half is F5 |
| F5 | Medium | A regrade without the rule leaves a superseded grade's verdict current | fixed | `681f25cea` | `test_f5_a_regrade_with_the_rule_switched_off_supersedes_the_held_verdict`; `test_f5_a_joint_regrade_supersedes_a_route_verdict`; `test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict` |

The tests are in `tests/test_route_rules_in_grader.py`. `318bce262`
regenerates the DB/config reference at the code commit. Only the stamp and
one source-line anchor moved.

## Reproduction

All three tests were run on `f15d647d7`, the re-reviewed tip, before the fix.
All three failed:

- **Switched off.** A held, ruled grade was regraded with
  `proof_check.enabled = false`. One `own_route_rule` row was left, the held
  verdict, and it was still current.
- **Joint.** A joint regrade of an attempt with a current verdict appended
  nothing.
- **mvp-0.17.** Using a backup-API copy of
  `fixtures/mvp017_route_check_replay`, the `held` attempt was regraded at
  mvp-0.17. Its `proof_route_check` verdict was the only row and was still
  current.

## What changed

`grading_support.record_route_rule_judgment` is still called in the
transaction that records the grade. What it writes depends on whether the
own-route rule ran over the new grade.

- **When the rule ran** (`status = checked` on the new record), nothing
  changes. It appends the verdict, which supersedes the attempt's current one.
- **When the rule did not run**, and the attempt has a current
  `own_route_rule` verdict, it appends `{"status": "not_checked"}`
  superseding that verdict. This covers:
  - the kill switch;
  - PF-c turned off;
  - a version without the rules;
  - a joint grade.

  The row carries the regrade's own provenance: `judge = llm`, the grader's
  model, and the run's prompt version and input hash. So the current verdict
  always describes the current grade, and its `input_hash` matches the latest
  grade's context hash.
- **When the attempt has no verdict**, nothing is written. That is the
  normal case: live grades, and attempts that were never ruled.
- **Later regrades without the rule** restate `not_checked` each time, one
  row per regrade. This keeps the current row's provenance equal to the
  current grade.
- **Replay** writes none, and no model is called.

`regrade.regrade_attempt` now calls the writer on every successful regrade,
blind or joint, inside the publication transaction. A joint regrade passes
its run's `prompt_version` and `input_context_hash`.

- **A joint regrade cannot reach this today.** A verdict is written only
  beside a blind record, and an attempt with a blind record always regrades
  blind (`prior_blind is not None`). The test seeds the verdict directly, so
  the ledger invariant no longer depends on that coupling.
- **mvp-0.17's verdicts are the same gap.**
  - mvp-0.17 wrote the attempt's route verdict under task `proof_route_check`,
    and a checked regrade superseded it.
  - This stage deleted that writer. So a regrade of an mvp-0.17-checked
    attempt left that verdict current, at mvp-0.17 and after the upgrade
    alike.
  - Any grade that replaces such an attempt's grade now supersedes the
    verdict with a `not_checked` row in the same task. The ledger trigger
    requires supersession within one task.
  - The task's name is kept as one constant,
    `LEGACY_ROUTE_CHECK_JUDGMENT_TASK`.
- **Not touched: an owner adjudication.** It releases a hold through tier-4
  evidence rows. It does not replace the blind grade the verdict describes,
  so it writes no verdict, as before.

## Gate

Run on the tree at `318bce262`, with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9428 passed**, 0 failed (7 min 32 s; 9425 at the re-reviewed tip plus the 3 new tests) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **96 passed**, 9332 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 186, 308 table notes, 763 configuration leaves in 46 sections, stamped at `681f25cea` |

**Targeted run before the gate.** 51 grading, regrade, clarification, held,
split, upgrade, router, mvp-0.17-replay, stuck, judgment, route and proof
test files: **714 passed**.

**Not applicable:**

- No file under `apps/learnloop-tauri` changed, so the npm and cargo steps do
  not apply.
- No migration and no schema change.
- No paid call.
- The shadow rebuild was not rerun. The fix writes only `judgment_ledger`
  rows on a regrade, and replay neither reads nor writes them.

## Open questions after the re-review

1. **Restating `not_checked`.** Each later regrade without the rule restates
   `not_checked`, one row per regrade, so the current row's identity is the
   current grade's. The alternative is to close the verdict once and leave
   it. This also applies to mvp-0.17's `proof_route_check` verdicts.
2. **Earlier open questions 1, 2, 4 and 5 stand.** Open question 3 (a ledger
   verdict with no successor) is resolved by F5.
