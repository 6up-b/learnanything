# UX Phase 4: the Codex review and its fixes

**Stage:** `ux-phase4-feedback`, branch `ux/phase4-feedback` (worktree `learnanything-merge4`), base `37a2a7e5f` (main, mvp-0.25, migrations to 204). Not merged with main (main is `2c23afe3f`, a spec decision since `ea7054044`).
**Review:** Codex job `20261015-174650-jAuW01`, run read-only against `5d687eff3` (the implementer's final tree, recorded in `docs/reviews/ux-phase4.md`). It found seven defects (one High, six Medium), a list of claims that don't hold and a spec-conformance table.
**Fix step:** interrupted three times by a full `/tmp`. Uncommitted work from the earlier runs was kept and finished, not redone. The gate was run once, on the final tree (§5).

## 1. Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Full-answer display bypasses reveal accounting | **fixed** | `6b908901e`, `ca63162c2`, `5b603d911` | `tests/test_ux_phase4_feedback.py::test_f1_*` (27 cases); `FeedbackScreen.phase4.test.tsx` "F1: …" (2); `PracticeScreen.phase4.test.tsx` "F1: …" (5); `practiceDraft.test.ts` "restores the trace frozen…" |
| F2 | Medium | Enter advances both the repair overlay and the feedback underneath | **fixed** | `ca63162c2` | `RepairOverFeedback.phase4.test.tsx` (5: feedback and the short check's results mounted under the step, the async queue read settled) |
| F3 | Medium | Grade contests never enter the existing review/adjudication flow | **fixed** | `6b908901e` | `test_f3_an_unresolved_contest_is_queued_for_review_and_adjudication_clears_it`, `test_f3_a_contest_the_regrade_upholds_needs_no_review`, `test_f3_a_contest_the_regrade_does_not_uphold_is_queued` |
| F4 | Medium | Session summaries credit a held or failed answer with another topic's credit | **fixed** | `6b908901e` | `test_f4_a_shared_facet_credits_only_the_topic_whose_answer_earned_it[missed/held/assisted]`, `test_f4_the_learning_diff_names_the_attempts_whose_points_raised_a_demonstrated_facet` |
| F5 | Medium | Historical feedback pairs the frozen question with today's answer key | **fixed** | `6b908901e`, `ca63162c2` | `test_f5_historical_feedback_shows_the_frozen_question_answer_key_and_rubric`, `test_f5_a_method_explicit_answer_keeps_its_question_key_and_rubric_together`, `test_f5_an_answer_with_no_contract_carries_no_frozen_key`; vitest "F5: …" |
| F6 | Medium | Releasing a held grade exposes its former provisional score | **fixed** | `6b908901e`, `ca63162c2` | `test_f6_the_regrade_history_says_the_grade_it_replaced_was_held`, `test_f6_an_ordinary_regrade_history_was_not_held`; vitest "F6: …" (3: in place, reopened, ordinary) |
| F7 | Medium | Failed contest requests claim the reason was saved | **fixed** | `6b908901e`, `ca63162c2` | `test_f7_a_contest_that_fails_before_any_write_reports_not_recorded`; vitest "F7: …" (2: failure keeps the box and the reason and the retry reuses the key; a new contest gets a new key) |

No finding was rejected. Seven fixed, one of them High.

**Reproduced first.** Every finding has a test that fails without its fix:
- The new sidecar tests, run against the reviewed tree's source (`git archive 5d687eff3 src migrations`, `PYTHONPATH` plus `-o pythonpath=`): **27 of 29 failed**. The two that passed are controls: the unaided answer when no answer was shown, and the on-your-own credit for a topic's own answer.
- The horizon tests (F1 below), run against `ca63162c2`, the charge without the horizon: **12 of 14 failed**. The two that passed are the controls proving other reveals keep their window.
- The new and changed vitest files, run against the reviewed desktop (`5d687eff3`'s `apps/learnloop-tauri`, with the new tests copied in): **18 of 50 failed**. The 32 that passed are the files' existing tests and the controls: no full answer means no charge, an ordinary regrade keeps its numbers, a short check never freezes, and Enter advances when the step is closed.
- F2 and F4 also reproduce exactly as the review describes: one Enter produced one repair prescription and one feedback advance, and a held answer on a shared facet was named "● on your own".

### F1: the full answer is an exposure (High)

**What was wrong.** The plain surface shows the expected answer on feedback and on the plain self-grade. Neither display wrote the reveal ledger. An unaided answer written right after reading the solution ("One question, unaided") was admitted as independent, and a retry with the answer in view was clean. The self-grade's lock was component state: it reset on remount and didn't cover the optional line.

**The fix.**
- **Feedback:** showing "A full answer" calls the new `record_answer_display` RPC. It runs once per attempt (the screen sends once, and the existing idempotent `reveal_ledger.record_answer_display_reveal` writes once). The row is `answer_display`, amount 1.0, linked to the attempt, with basis `feedback_full_answer:desktop`.
- **Plain self-grade:** before any full answer shows, `record_self_grade_disclosure` freezes the whole trace in the session checkpoint: the answer exactly as Submit sends it, and the optional line apart, under the draft's retry key. Only a confirmed freeze shows the full answer. An unconfirmed one grades without it.
  - The answer and the line stay locked, across navigation (the draft mirror) and a restart (the checkpoint, `checkpoint_dto.selfGradeDisclosure`). Submit sends exactly the frozen trace.
  - A submit whose trace differs from the frozen one is recorded primed.
  - The exposure is settled when the draft is done with. Committed: a row linked to the attempt, counting against the next attempt. Abandoned (another item, a new retry key, a cleared checkpoint, the session's end, a new session): an unlinked row. Exam protection counts an unlinked row as shown (`source_service.shown_items`).
- **The horizon (`5b603d911`).** This goes past what the review asked, and it is the one judgement call in this step. The plain surface shows the full answer on *every* feedback, by default. Two of the ledger's readers had no time bound:
  - auto-prime: `attempts.reveal_total_for_submission`, from the item's last attempt;
  - `reveal_ledger.production_admissibility`, open-ended when no `since` is given. Causal probes and placement checks call it that way, widened to the learning object.

  Charging the display alone would have:
  - marked every later attempt on a shown item primed. A review a week later would be labelled "◌ with help", recorded as a repair activity with the b-offset, and never advance `last_evidence_at` or certify;
  - made every later causal probe and placement answer on its learning object non-independent, forever.

  In the default UI, that means no item ever yields clean evidence again after its first feedback. That contradicts the owner's "honest labels, generous defaults" and the stage's display-only scope. So a **routine display** (basis `feedback_full_answer:` or `self_grade_disclosure:`) counts only within `ROUTINE_ANSWER_DISPLAY_HORIZON`. That is one day, the cold retrieval delay (`remediation.COLD_RETRIEVAL_DELAY`, pinned equal by a test). Every other exposure reader already uses that delay: the serving exclusions, the cold-task deferral and the independent-check rule (`instructional.exposure`).
  - Within the day, a retry is primed and an unaided answer is not independent. On the item and on its learning object: the review's scenario.
  - After it, a review is a retrieval, as every feedback before Phase 4 left it.
  - Every other reveal keeps its window exactly, including the stuck answer's worked answer (`worked_answer:stuck_empty:tui`, stuck-prompt F8) and tutor answers (`test_f1_other_reveals_keep_their_window`).
  - It applies at write time only: replay keeps the recorded `primed` and admissibility. No vault holds a row with these bases from before this stage, so no recorded meaning changes. There is no migration and no new table.
- **Classic mode** shows no full answer by default and records nothing new.

### F2: one key, one screen

App keeps feedback, or the short check's results, mounted under the repair step's overlay.
- **The screen underneath:** `FeedbackScreen` and `DiagnosticReviewScreen` take `keysSuspended`. App sets it while the repair step is open, and none of their shortcuts run.
- **The step itself:** it handles Enter and Esc first (capture) and stops them, so no listener underneath sees them.

The tests mount both screens together and let the queue read resolve. Both mechanisms are tested: App's suspension, and the step's capture with nothing suspended.

### F3 and F7: the contest

`trigger_regrade` with a `learner_reason` now runs in three steps (`feedback._contest_grade`):
1. **The reason is recorded first,** under the client's `contest_id`, so a retry finds the same presentation and its response. If nothing can be recorded, the call fails with `contest_not_recorded` (retryable).
2. **The existing regrade runs,** still blind to the reason. A grader that can't run is no longer an error once the reason is kept: the bundle's `contest.regraded` is false.
3. **Unless the answer now reads right** (full marks and not held), the grade enters the existing grade-review intake. The new `grade_resolution.flag_observation_for_review` appends a copy of the active interpretation head with `review_flag = 1` and makes it the head. That changes no posterior, certainty or state, so nothing projected moves. The grade then lists in `Repository.pending_grade_reviews` (`learnloop grading reviews`) until `append_adjudication` (`learnloop grading adjudicate`) appends the next head. The test checks that adjudication clears it.

On the desktop, "Your note is kept" shows only on a confirmed record. A failed or unknown delivery says "Your note couldn't be sent. Try again.", keeps the box and the reason, and the retry reuses the same key. A queued grade adds "It's marked for review."

### F4: credit by the attempts that earned it

`session_learning_diff` now also returns `demonstrated_attempt_ids`: the unassisted, unprimed attempts whose own points raised a facet the session demonstrated. `_session_topics` names a topic ● only for one of its own attempts in that set. A held answer is never credited, a missed one is never credited, and an assisted one stays ◌. Neither id list reaches the payload.

### F5: one contract for the question, its key and its rubric

The feedback bundle reads the assessment contract the grade was given under (`attempt_graded_contract`). It returns:
- `answered_presentation`: the frozen statement and the method instruction, or the frozen statement of an item edited since;
- `answered_expected_answer`;
- `answered_criteria` (description and points per criterion).

The desktop's full answer and criterion lines read these. An answer graded before contracts carries none, and the screen reads the item as before.

### F6: a released hold

`regrade.old_held` says whether the grade the latest regrade replaced was held. It uses THE held predicate on that epoch: a blind record held it and nothing in the epoch was assessed. The desktop's regrade receipt carries the hold on both sides. Details then read "Looked at again: Held for review → Right", in place and when reopened, never the provisional score. An ordinary regrade keeps its numbers.

## 2. Claims that don't hold

Each one is corrected in `docs/reviews/ux-phase4.md`:
- **"Display only" (§1):** the switch is read only by the display, but the full answer the simple screens show is an exposure, now recorded (F1).
- **"The answer is locked first" (§4.1):** the lock is now the frozen trace's, in the checkpoint, and it covers the optional line.
- **"A topic only tried, missed, skipped or held is not named" (§1):** now true for shared facets (F4).
- **Held grades show "no number anywhere" (§4.2):** now true after a release too (F6).
- **"Your note is kept" (§4.2):** now said only on a confirmed record (F7).
- **Classic restores every screen "exactly" (§1):** reworded. One rubric row per criterion after a regrade, and the m13 prompt copy (D11), reach classic too.
- **D14 and Q2** now describe the grade-review intake (F3).

The review also noted that the requested `ux-phase4-feedback.md` is absent. The stage's implementer record is `docs/reviews/ux-phase4.md`, and this file is its review record.

## 3. Spec conformance: what stays open

None of these was a finding, and none is in this fix step's scope. Each is recorded for the owner:
- **4.1:** Skip still returns through `onBack` rather than the next step. The origin and progress header ("Today's plan · 2 of 6") and the measured grading wait and fallback are not built (D5, Q6).
- **4.2:** A hinted attempt isn't labelled ◌ on feedback (D13). There is no return to Progress, and no direct book link from feedback (D3, the Reader stage's screens).
- **4.3:** The short check's results have no per-question "I think I was right".
- **4.4:** No "Next time: finish §N" (D2, Q3).
- **Scope:** The new contest event type now feeds the existing grade-review intake (F3).

## 4. Paid calls

None. Every test uses fakes. No real provider was called, no vault outside a test `tmp_path` was opened, and no manual run was needed. Cost $0.

## 5. Gate (final tree)

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11886 passed, 0 failed (12 min 13 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11780 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 93 files, 674 passed; the build succeeds (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, no errors (`commands.rs` and `main.rs` gained two passthroughs) |
| DB/config references | not regenerated: no schema or config change |
| `tests/test_coordinated_migrations.py` | in the full suite (no migration in this step) |

The code was final at `5b603d911`; only this record changed after it. One earlier `npm test` run, made while the full suite and other stages' suites loaded the machine, had 4 timing failures in `PracticeScreen.test.tsx` (vault-switch draft tests) and `ReaderScreen.branches.test.tsx`. Both files passed alone (29 of 29), and the counts above are from a clean rerun of the whole vitest suite.

## 6. Open questions for the owner (defaults applied)

- **Q8 (F1).** Should a full answer shown on routine feedback count beyond the cold retrieval delay? Counting it forever primes every later attempt on the item and every later probe or placement answer on its learning object. *Default applied: within the delay only.* A related, still-open question: should every other reveal kind get the same horizon in auto-prime and probe admissibility? (Stuck-prompt open question 6 asked whether to charge the TUI's ordinary "Expected: …" too.) *Default: unchanged.*
- **Q9 (F1).** Under `"simple"`, a short check started within a day of seeing a full answer on its learning object is not independent evidence. The flow is honest, but it means the plain feedback's full answer delays what a causal probe can settle. Should feedback hold the full answer behind a click while a diagnosis is pending on the learning object? *Default: shown, as the spec's W5b draws it.*
- **Q10 (F3).** Should the desktop list the grade-review queue? *Default: the CLI only (`learnloop grading reviews`).*
- **Q11.** The open conformance items in §3.
