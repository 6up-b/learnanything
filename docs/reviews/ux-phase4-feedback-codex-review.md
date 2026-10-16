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
- **Feedback:** showing "A full answer" calls the new `record_answer_display` RPC. It runs once per attempt (the screen sends once, and the existing idempotent `reveal_ledger.record_answer_display_reveal` writes once). *Re-review F1: now once per visit, §7.2. Final verification F1: once per exposure, §8.2.* The row is `answer_display`, amount 1.0, linked to the attempt, with basis `feedback_full_answer:desktop`.
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

## 7. Re-review

**Review:** Codex job `20261015-224218-0Dkp4w`, run read-only against `c8a4e6468` (§1 to §6 above). Verdict REOPENED: F1 reopened (High), and three new Medium findings (F8, F9, F10).
**Fix:** `86c0ab03f` (sidecar), `0fb2e6910` (desktop). The scope is unchanged: the Phase 4 screens and their handlers.

### 7.1 Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High (reopened) | Feedback reopened after the cold delay leaves no fresh exposure | **fixed** | `86c0ab03f`, `0fb2e6910` | `test_f1r_feedback_reopened_after_the_cold_delay_is_a_fresh_exposure`, `test_f1r_a_display_needs_its_visit`, `test_f1r_a_display_that_lapses_never_stands_in_for_one_that_does_not`; vitest "F1 (re-review): reopening the feedback is a fresh exposure…", "F1: … once per visit" |
| F8 | Medium | Frozen criterion metadata loses its original IDs | **fixed** | `86c0ab03f`, `0fb2e6910` | `test_f8_frozen_criteria_keep_their_original_ids_through_serialization`; vitest "F8: a frozen criterion with an underscored id…" |
| F9 | Medium | Regraded feedback shows a superseded answer key and rubric | **fixed** | `86c0ab03f`, `0fb2e6910` | `test_f9_a_regrade_under_the_corrected_item_shows_its_key_and_rubric[later/same_second]`, `test_f9_an_answer_not_regraded_keeps_the_key_and_maximum_it_was_graded_under`; vitest "F9: …" (2) |
| F10 | Medium | Retrying a contest silently discards an edited reason | **fixed** | `86c0ab03f`, `0fb2e6910` | `test_f10_a_contest_key_resent_with_an_edited_reason_is_refused_never_dropped`; vitest "F10: …" (2: an edited reason, cancel then a new contest) |

No finding was rejected. Four fixed, one of them High.

**Reproduced first.**
- **F1, the review's scenario,** as a script against `c8a4e6468`. The feedback's first display was stamped two days back, then the RPC was called again as the reopened visit. Result: one `answer_display` row, the next attempt `primed=False`, and a production right after the reopen `admissible=True`.
- **The new sidecar tests against `c8a4e6468`: all 6 failed.**
  - F1: the per-visit writer and the visit id don't exist.
  - F8: `answeredCriteria` came back keyed `criterionCorrectSelection`.
  - F9: after the regrade, `answeredExpectedAnswer` was still the superseded key. The F9 control failed on the old map shape.
  - F10: the edited reason under the same key returned success, and only the first reason was kept.
- **The per-basis test** failed under the old dedupe: one row, because the feedback visit's row suppressed the TUI's worked answer.
- **The F9 same-second case** failed under this fix's first version, which ordered epochs by their key as the regrade history does. It passed only when the regrade landed in a later second, so it was flaky at first. It is now ordered by written order (below).
- **The vitest file against `c8a4e6468`'s desktop** (new file copied in): **7 of 31 failed** (F1 ×2, F5's new shape, F8, the F9 maximum, F10 ×2). The 24 that passed are the existing tests and the F9 regrade case, which needs only the sidecar change: the screen already reads the item when nothing frozen is sent.

### 7.2 F1: every visit that shows the full answer is an exposure (High)

**What was wrong.** `record_answer_display` charged an attempt once. The routine display counts only within one day of its row's stamp (§1, the horizon). A learner who reopened the feedback two days later read the full answer again, but the write was skipped against the first visit's lapsed row. The next attempt was clean, and an unaided production was independent.

**The fix.**
- **The RPC** takes a required `display_id` (1 to 128 characters). It writes one row per visit through the new `reveal_ledger.record_feedback_answer_display_reveal`, with basis `feedback_full_answer:desktop:<display_id>`. Only a retry of the same visit's write is deduplicated.
- **The horizon runs from the latest exposure.** Each row is stamped when its visit showed the answer, and the horizon is applied per row, so the newest visit decides. The readers are unchanged.
- **The desktop** mints the visit id when the screen first shows the answer to an attempt. A remount (the feedback reopened) is a new visit. If the write fails, the next try on the same visit reuses its id. Re-renders, details and the bundle's re-reads charge nothing. *Superseded by §8.2: the id names an exposure, renewed while the screen stays mounted.*
- **`record_answer_display_reveal`** (the TUI's worked answer and the committed self-grade disclosure) now dedupes by basis, not by any row on the attempt. A lapsing routine row can no longer stand in for the worked answer, which never lapses. This hazard came from §1's horizon, which is why it is fixed here.
- **The plain self-grade** needs no change. Its row is written when the frozen draft is settled, at commit or abandonment. That is never earlier than the answer it showed.

### 7.3 F8: criteria are rows carrying their id

`answered_criteria` is now `[{criterion_id, description, points_possible}]`. The bundle's recursive camel-casing converts keys, never values, so `criterion_correct_selection` survives. The desktop matches each evidence row on `criterionId`.

### 7.4 F9: the key and rubric the grade stands on

- **The key, criteria and maximum** come from the contract cited by the grade's current epoch (`serializers._active_epoch_contract`). A first grade, and a method-explicit regrade, cite the contract they read. An ordinary regrade reads the item as it is now and cites none (canonical sources §7.3a). Then the three fields are null, and the screen reads the item and the regrade's own rows: what the regrade graded against. *Superseded by §8.3: the screen kept the item it loaded with, and a later edit of the item showed as what the regrade graded against. The bundle now sends the three fields itself and says when the question has changed since.*
- **The current epoch** is the one holding the most recently written evidence row, by `(created_at, id)`. The ids are ULIDs. A regrade row carries no `grading_revision`, so its epoch key (`legacy:<created_at>`) sorts before an original's `revision:0` when both share a second.
- **The question** stays the one presented (`answered_presentation`, from the contract the answer was first graded under).
- **New field `answered_max_points`:** the grading contract's maximum. The details' score line reads "4 / 4" for an answer still graded under its 4-point contract after the item moved to 8. Classic mode, the regrade receipt and the contest's "upheld" check still read the bundle's `max_points`, unchanged. *§8.3: the plain regrade history now scores each side out of its own grade's maximum; classic and the "upheld" check are unchanged.*

### 7.5 F10: a contest key is bound to its reason

- **The desktop** keeps `{key, reason}`. A send reuses the key only for the same trimmed reason. An edited reason is a new contest with a new key. *never mind* and opening a contest both reset the key.
- **The sidecar** refuses the same key with another reason: `contest_key_conflict`, not retryable, and nothing is recorded or regraded. Previously it answered success over the first reason. A retry of the same reason under the same key is still idempotent.

### 7.6 Claims corrected

- **§1, F1 "It runs once per attempt":** now once per visit (§7.2).
- **`docs/reviews/ux-phase4.md` §4.2 "the retry reuses the contest key":** now a retry of the same reason. An edited reason, or a contest opened again, gets a new key.

### 7.7 Outside this stage (recorded, not changed)

- **Regrade and replay of a model-graded answer after its maximum rose.** An ordinary regrade supersedes only the self-grade tier (`supersede_tiers=(1,)`), so a model-graded original's rows stay live. `attempts.replay_existing_attempt` takes the contract from the first live row that cites one, and `_resolve_attempt_target` scores against that contract's rubric. A regrade under a raised maximum is therefore replayed against the original one.
  - Probe (split vault, criteria 2+2 changed to 2+6, regraded to 6 points): the regrade's own replay failed the `correctness <= 1` CHECK (6 / 4).
  - This is core regrade code (`attempts`, `regrade`), not this stage's. The F9 tests use a self-graded original, whose rows the regrade supersedes.
  - *§8.4 reproduces it in full and answers whether it can fail `rebuild` (it can, by another route).*
- **Same-second epoch order.** `Repository.attempt_regrade_marker` and this stage's `_regrade_replaced_held` (F6) order epochs by (first timestamp, key), as the regrade history always has. So a regrade written in its original's second sorts before it. No AI regrade completes that fast. `_regrade_replaced_held` is left matching the marker, so the two never disagree.

### 7.8 Paid calls

None. Every test uses fakes, and the reproductions ran in test vaults under `fixtures-local/tmp` (since removed). Cost $0.

### 7.9 Gate (final tree)

Run on `0fb2e6910` in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11894 passed, 0 failed (11 min 54 s): the 11886 of §5 plus the 8 new sidecar tests |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11788 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 93 files, 680 passed (674 plus 6 new); the build succeeds (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `apps/learnloop-tauri/src-tauri` changed (`record_answer_display` is a passthrough of its `input`) |
| DB/config references | not regenerated: no schema or config change |
| `tests/test_coordinated_migrations.py` | in the full suite (no migration) |

The code was final at `0fb2e6910`; only this record and the claim in `docs/reviews/ux-phase4.md` changed after it.

### 7.10 Open question for the owner (default applied)

- **Q12 (F1).** A visit is one mount of the feedback screen. A feedback left open on screen across the one-day horizon, without being reopened, is charged once, when it first showed the answer. *Default: one charge per mount.* Re-charging on refocus would need a visibility signal the screen doesn't read today. *Settled by §8.2: the final verification reopened F1 on exactly this; the screen now reads it.*

## 8. Final verification reopen

**Verification:** the final Codex verification of §7's fixes. Verdict REOPENED: F1 (High) and F9 (Medium). Their text is quoted in §8.2 and §8.3.
**Fix:** `5b7d826a7` (sidecar), `a02519f3e` (desktop), `ece7ee132` (docstrings). The scope is unchanged: the Phase 4 screens and their handlers. Nothing in grading, scoring, scheduling or replay changed, and there is no migration, config change or new RPC. The replay mismatch is out of scope and reproduced in §8.4, as the brief for its own stage.

### 8.1 Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High (reopened) | Returning to still-mounted feedback records no fresh exposure | **fixed** | `a02519f3e` (`5b7d826a7`: the ledger tests) | vitest "F1 (final): …" (7); `test_f1f_*` (4) |
| F9 | Medium (reopened) | Ordinary regrades lack durable grading metadata; the desktop fallback can stay stale | **fixed** (live), **labelled** (historical) | `5b7d826a7`, `a02519f3e` | `test_f9f_*` (6 cases), `test_f9_*` (3 cases: two changed, one new), the F5 no-contract test (changed); vitest "F9 (final): …" (5) |

**Reproduced first.**
- **The new and changed sidecar tests, run against `8899a8ada`'s source** (`git archive 8899a8ada src migrations`, `PYTHONPATH` plus `-o pythonpath=`): 10 of 15 failed, every F9 one.
  - F9 live, as a plain regrade and as a contest: `answeredExpectedAnswer` was None, not the corrected key. The screen then read the item it had loaded before the regrade.
  - F9 historical, 6/8 then 6/10 (blind and joint): there was no way to say the question had changed (`answeredSource` absent), and `answeredMaxPoints` was None, so the screen fell back to the item's 10.
  - F9 unchanged, the no-contract answer and §7's corrected-item test (both orders): `answeredExpectedAnswer` was None, not the key graded against.
  - F9 blind recorded maximum: None, not the 4 recorded with the grade. The cannot-place case: no `answeredSource`.
  - The 5 that passed are the 4 F1 ledger tests and the F9 control (an answer not regraded keeps its contract). The F1 tests are contract tests: the sidecar already wrote one row per display id (§7.2). F1's defect was that the desktop never sent a second id while the screen stayed mounted.
- **The new vitest cases, run against `8899a8ada`'s desktop** (the new test cases added, and the new exposure module present but unused): 10 of 12 failed.
  - F1 ×6: returning after the delay (1 write, not 2), focus regained (1, not 2), left on screen for 50 hours (1 write, not 50 or more), the retry under the same id (1, not 2), an overlay closed (1, not 2), leaving after ten minutes (1, not 2).
  - F9 ×4: no label on a changed question; "6 / 10" where the grade recorded 8; the item loaded before the regrade still shown after it; "2 / 8 → 6 / 8" for a regrade from a 4-point grade.
  - The 2 that passed are the cadence pin (the new module already existed) and the unchanged-item control.

### 8.2 F1: an exposure lasts as long as the answer is on screen (High)

*Superseded by §9.2: the round-3 verification reopened this design (the closing row was the safety mechanism, a crash lost it, and a failed write was acknowledged). The gate in §9.2 replaces it.*

**The finding.** "Remounting now records a fresh exposure, but returning to still-mounted feedback does not." Feedback was opened, the app backgrounded without unmounting it, two days passed, and the learner came back and read the answer. Dispatching focus and visibility events wrote no second display. The production readers then returned `primed=False` and `admissible=True`. Remounting was the passing control.

**The design.** The routine display horizon (§1) runs from each row's stamp. So the ledger has to hold a row no older than the last moment the learner could read the answer. A row from when the screen first showed it is not enough. `screens/feedback/answerExposure.ts` (`AnswerExposure`, `useAnswerExposure`) keeps that true, using three rules:
- **A new exposure whenever the answer comes back on screen**, each with a new display id:
  - the surface mounts with the answer;
  - the document becomes visible again (`visibilitychange`);
  - the window regains focus;
  - the page is shown or resumed (`pageshow`, `resume`);
  - an overlay over it closes. App passes `answerCovered` for the repair step, the inspector and Ask.
- **Renewal at least hourly** while the answer stays on screen and the document is visible, each renewal under a new id. The check runs every minute on wall-clock time, so a machine that slept with the answer open renews within a minute of waking.
- **A closing row when the answer leaves the screen** after more than a minute: hidden, covered, or the screen unmounted (`pagehide` and `freeze` too). It is stamped then, so the delay runs from the last moment the answer was on screen.

Two more rules keep the writes in check:
- Within a minute of the latest row nothing new is written, because that row already covers the moment.
- A write that failed is retried under the same id (on the next tick, show or end) until it is confirmed. The sidecar records each id once.

**Why this design.** The brief offered two options: renew on a timer while the answer is visible, or charge when a retry or unaided attempt starts from a feedback screen that shows the answer. Charging at attempt start covers only attempts started from that screen. An answer read and then left behind (for the queue, a plan step that probes its learning object, or the Reader) would still lapse. The closing row covers every way off the screen, including a retry started from feedback, because that unmounts it. The hourly renewal covers what a closing row can't: the app closed or killed with the answer open.
- With a closing row, the delay runs from the last moment the answer was on screen, give or take a minute.
- Without one (the app quit), it runs from no more than an hour before that.

**What the extra rows do.** Every row is amount 1.0.
- Auto-prime compares the total against a threshold one row already crosses, so renewals change no `primed`.
- Admissibility is decided by the presence of a row within the delay.
- Receipts that sum amounts (the router's coldness covariates, the cold-task deferral receipt) count each renewal, as they already counted each visit (open question Q13).
- An open screen writes about one row an hour, plus one per return after more than a minute away, plus one when it closes.

**The sidecar.** No code change. The per-display writer (§7.2) already records each exposure once. Its docstrings now say exposure (`ece7ee132`).

**Tests.**
- vitest, fake timers plus visibility and focus events (`FeedbackScreen.phase4.test.tsx`, "F1 (final): …"):
  - returning after two days hidden writes a second display under a new id, and nothing is written while hidden;
  - focus regained after ten minutes renews, but not within a minute of the last row;
  - an answer left on screen for 50 hours writes at least 50 distinct displays, never more than an hour and a minute apart;
  - a failed write is retried under the same id, then nothing more until the next renewal;
  - an overlay closed after two days covered is a new exposure, and nothing is written while covered;
  - leaving after ten minutes closes the exposure with a row stamped then;
  - a pin that the cadences stay well inside the one-day delay.
- The remount control still passes: "F1 (re-review): reopening the feedback is a fresh exposure…", and `test_f1r_feedback_reopened_after_the_cold_delay_is_a_fresh_exposure`.
- sidecar, through the production readers (`auto_primed_draft`, `production_admissibility`):
  - `test_f1f_feedback_returned_to_after_the_cold_delay_is_a_renewed_exposure`: the verifier's control first (clean before the return), then primed and not admissible after the renewed display;
  - `test_f1f_a_full_answer_left_on_screen_past_the_cold_delay_stays_an_exposure[renewed_hourly|mount_only]`: hourly renewals over 50 hours stay primed and not admissible until the delay passes after the last one. With the mount's row alone, the exposure has lapsed (the finding);
  - `test_f1f_a_retry_within_one_exposure_writes_once`.

### 8.3 F9: what the grade stands on (Medium)

*Superseded by §9.3: the `item` and `changed` sources inferred which version a grade read from snapshot first-seen order, which the round-3 verification showed does not establish it. The sources are now `contract`, `live` and `unrecorded`, and the item snapshot `trigger_regrade` took for the inference is gone. What §8.3 lists the database records per epoch still holds.*

**The finding.** "Ordinary regrades still lack durable grading metadata, and the desktop fallback can remain stale."
- Live: after a successful regrade in place, the handler replaced `feedback` but never refetched `item`, so the original key stayed on screen.
- Historical: a regrade to 6 under an 8-point rubric, then the item changed again with no regrade. Feedback used the later, ungraded key and maximum: 6/8 became 6/10.

**What the database records per grading epoch** (the brief's question 3):
- **`grading_evidence` rows:** per criterion, `criterion_id`, `points_awarded`, `grader_tier`, `agent_run_id`, `created_at`, the supersession pointers, and `grading_revision` (first grades). They store no criterion maximum and no total maximum.
- **`assessment_contract_version_id`:** set on a first grade's rows (and only with contracts, mvp-0.7 on) and on a method-explicit regrade's rows. An adjudication carries over the contract of the rows it revises. An ordinary regrade and a legacy grade cite none.
- **`assessment_contract_versions`:** content-addressed snapshots of the item's contract: prompt, expected answer, criteria with their maxima, total maximum. Each is stamped when that content was first seen. They are written by every serve of the item (`practice_item_detail`, on canonical-state vaults) and by a first grade. Not by an ordinary regrade, and not linked to it.
- **`practice_attempts`:** only the current grade's `rubric_score` and `correctness`, and every replay rewrites `correctness` (§8.4). So it is not a record of what an epoch was graded out of.
- **`blind_grade_records`:** per blind-graded epoch (split vaults; linked by `agent_run_id`), the grade's total `max_points` and its points per criterion. No key, no criterion maxima.
- **`agent_runs`:** `input_context_hash`, a hash of the grading context, which includes the key and rubric but also the diagnostic history. It is a fingerprint, not content, and can't be recomputed later.
- **`practice_item_snapshots`:** item revisions the scheduler scored, first-seen stamps, not linked to grades. **`judgment_ledger`** reference bindings: a content hash, only when a grade was lowered.
- **Conclusion:** an epoch that cites a contract is exactly recoverable. An ordinary regrade's key, criteria and criterion maxima are not recoverable from anything stored. Its total maximum is recorded only in a blind record.

**The fix.**
- **The bundle sends what the grade stands on**, directly (`serializers._epoch_grading_record`). `answered_source` says where it comes from:
  - **`contract`:** the current epoch cites one. Its key, criteria and maximum, exactly (as §7.4).
  - **`item`:** it cites none, and the item's version in force at the epoch matches the item now, with nothing the epoch recorded contradicting that. The version in force is its latest snapshot first seen by the epoch's time. A contradiction would be a criterion the item no longer has, points above a criterion's current maximum, or a recorded maximum other than the item's. The item's key, criteria and maximum are sent, so the screen never reads them off an item it loaded earlier.
  - **`changed`:** otherwise. No key and no criteria, and `answered_max_points` only when a blind record kept one, never the item's.
- **The live part.** The regrade's own response is built from the vault it just graded with, so it carries what it graded against. A regrade from the feedback screen first snapshots the item it reads (`feedback._snapshot_item_regraded`, the same snapshot every serve takes), so later loads place it exactly, even when the item was edited after the screen last served it. The desktop also re-reads the item after every regrade in place, plain or contest, so nothing on the screen keeps the item it loaded with.
- **The historical part.** On `changed`, the surface says "This question has changed since it was graded, so the answer it was graded against isn't shown." It shows no full answer (so nothing is charged to the ledger) and no ✓/✗ lines. In details, the score reads "6 points", or "6 / 8" with a recorded maximum. Each criterion reads its points alone, with a neutral mark.
- **The regrade history** scores each side out of its own grade's maximum (`regrade.old_max_points`, `regrade.new_max_points`). A regrade under a corrected rubric reads "Looked at again: 2 / 4 → 6 / 8." A side with no known maximum shows its points alone. Before, both sides used the item's maximum.
- **Classic** is unchanged: it reads the item and the bundle's `max_points` (Q16).

**Limits, each on the cautious side unless said.**
- **An item edited and restored between a snapshot and a regrade.** The version in force then looks different from the item now, so the bundle says changed.
- **A regrade outside the feedback screen** (the CLI, the deferred self-grade regrades), under an item edited after its last serve. The latest snapshot by then is the earlier version, so the bundle says changed although the regrade read the item now. `test_f9_a_regrade_the_ledger_cannot_place_says_the_question_changed` pins it. The successor in §8.4 removes it.
- **An answer graded before contracts, or on a vault without snapshots** (mvp-0.6). Only the contradictions apply. A key-only edit since its grade can't be seen, and feedback shows the item's key, as every feedback before Phase 4 did (Q17).

**Tests.**
- sidecar:
  - `test_f9f_a_regrade_in_place_returns_the_key_criteria_and_maximum_it_graded_against[regrade|contest]` (live, through `trigger_regrade`, the item corrected after the screen loaded);
  - `test_f9f_a_question_changed_after_its_regrade_is_labelled_never_scored_out_of_the_later_maximum[blind|joint]` (6/8 then 6/10: `changed`, no key or criteria; the maximum is 8 from the blind record, or none for a joint regrade; never 10);
  - `test_f9f_an_item_unchanged_since_its_regrade_is_not_labelled`;
  - `test_f9f_a_blind_regrade_keeps_the_maximum_recorded_with_it_after_the_question_changed`;
  - `test_f9_a_regrade_the_ledger_cannot_place_says_the_question_changed` (new).
- Changed, because §7's expectations no longer hold:
  - `test_f9_a_regrade_under_the_corrected_item_shows_its_key_and_rubric[later|same_second]`: the corrected item served before the regrade, then the corrected key, criteria and 8 are sent, where §7 sent nulls;
  - `test_f5_an_answer_with_no_contract_carries_the_items_key_when_nothing_says_it_changed`: was `…_carries_no_frozen_key`, and now expects the item's key, not None.
- vitest ("F9 (final): …"):
  - a changed question says so, shows no full answer and charges nothing, and never shows "/ 10" (details "6 points", criterion "6.0 points", history "2 / 4 → 6 points.");
  - a recorded maximum scores it "6 / 8";
  - an unchanged item carries no label;
  - after a regrade in place the item is re-read, and the key it loaded with is gone;
  - the history reads "2 / 4 → 6 / 8."

### 8.4 Out of stage: the regrade and replay contract mismatch (the brief for its own stage)

Not fixed here: it is core regrade and replay code, and changing which contract replay reads changes persisted meaning, so it needs an algorithm successor (`docs/algorithm-change-playbook.md`). The saved-forecasts stage found the same gap. Reproduced with fakes in a split vault at the route-rules version: `pi_svd_compute_001`, criteria setup 2 + result 2, the scenarios run in `fixtures-local/tmp` and since removed.

1. **A model-graded original, then a regrade above the original maximum.**
   - Steps: the original is graded 2/4 under its contract (tier-3 rows citing the contract, `test_held_grade_evidence._graded_apply`). `result` is raised to 6 points (maximum 8). `regrade_attempt` then gives an assessed 6 (2 + 4).
   - What runs:
     - `regrade_attempt` reads the item (`regrade_reads_contract` is false) and writes rows citing no contract.
     - `_publish_regrade` → `Repository.insert_regrade_evidence(supersede_tiers=(1,))` supersedes only the self-grade tier, so the original's tier-3 rows stay live.
     - `update_attempt_grade` writes correctness 6/8. Then `replay_learning_object` → `replay_existing_attempt` takes `assessment_contract_version_id` from the first live row that cites one: the original's.
     - `_resolve_attempt_target` → `rubric_from_contract` gives maximum 4. `apply_attempt(replace_existing=True)` → `replace_attempt_derived_outcome` writes correctness 6/4 = 1.5.
   - Result: `IntegrityError: CHECK constraint failed: correctness … <= 1.0`. The publish transaction rolls back, so the regrade can't be made at all. From the screen, a contest says the grader couldn't look again, and a plain regrade shows an error.
2. **The same original, then a regrade within the original maximum** (3: 1 + 2). It commits, with both epochs' rows live. Replay still resolves the 4-point contract, so the recorded correctness is 0.75 (3/4), not the 0.375 (3/8) the regrade wrote.
3. **A self-graded original** (tier 1, which the regrade supersedes).
   - Steps: regraded to 6 under the raised rubric. It commits: no live row cites a contract, so replay reads the item, 6/8. Then `result` is lowered to 2 (maximum 4).
   - Result: `substrate.rebuild_orchestrator.rebuild_all_derived_state` fails the same CHECK (6/4). Its single transaction rolls back and live state is intact. Every later regrade of any attempt on that learning object fails too, because its `replay_learning_object` includes this attempt.
   - With `result` at 4 instead (maximum 6), the rebuild succeeds and silently rescores the regraded answer from 0.75 to 1.0.

**Can it make `rebuild` fail on `correctness <= 1`?** Yes. Not through case 1, because that regrade never commits. It fails through case 3: an answer regraded ordinarily, with no live row citing a contract, whose recorded score is above its item's later maximum. Replay then reads the item as it is at rebuild time.

**What the successor needs:** an ordinary regrade snapshots the contract it reads (`snapshot_for_presentation` of the item it grades, as `trigger_regrade` now does for display) and cites it on its rows. Replay takes the contract from the current grading epoch's rows, not the first live row. The stage also has to decide whether an ordinary regrade of a model grade supersedes the model tier. With that, §8.3's `item` and `changed` inference reduces to `contract` for every new regrade.

### 8.5 Claims corrected

- **§1, F1, "once per attempt" and §7.2 "a remount is a new visit":** now once per exposure (§8.2), annotated in place.
- **§7.4, "the three fields are null, and the screen reads the item":** the bundle sends them, or says the question changed (§8.3), annotated in place.
- **§7.4, the regrade receipt reading `max_points`:** the plain history now uses each side's own maximum, annotated in place.
- **§7.10, Q12:** settled by §8.2.
- **`docs/reviews/ux-phase4.md`:**
  - §1: the bundle's grading-record fields and the regrade's item snapshot.
  - §4.2: the full answer is the one the grade stands on, charged while on screen; the changed-question line; details' score and history maxima.

### 8.6 Paid calls

None. Every test uses fakes. The reproductions ran in test vaults under `fixtures-local/tmp`, since removed. No owner vault was opened. Cost $0.

### 8.7 Gate (final tree)

Run on `ece7ee132` in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11905 passed, 0 failed (13 min 32 s): §7.9's 11894 plus the 11 new sidecar cases (the 3 changed ones are counted in the 11894) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11799 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 93 files, 692 passed (680 plus 12 new); the build succeeds (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `apps/learnloop-tauri/src-tauri` changed |
| CLI help snapshot, RPC pins (`tests/test_mobile_allowlist.py`), DB/config references | unchanged: no CLI, RPC, schema or config change (both test files ran in the full suite) |

The code was final at `ece7ee132`; only this record and `docs/reviews/ux-phase4.md` changed after it. No run had a timing failure, so nothing needed a rerun alone.

### 8.8 Open questions for the owner (defaults applied)

- **Q13 (F1).** Each renewal is a 1.0 row, so summed reveal amounts in receipts (the router's coldness covariates, the cold-task deferral receipt) grow with how long feedback stays open. Should routine renewals count once per exposure chain in those sums? *Default: each row counts, as visits did.*
- **Q14 (F1).** The cadences: renew at least hourly, and close after a minute on screen. *Default: as built.* Hourly bounds the slack to an hour only when the app quits with the answer open.
- **Q15 (F9).** A regrade outside the feedback screen under an item edited after its last serve is labelled "changed" although it read the item now. *Default: the cautious label until regrades cite their contract (§8.4).*
- **Q16 (F9).** Classic still reads the item and its maximum, so the 6/8 then 6/10 case shows there. *Default: unchanged (classic restores the screens exactly).*
- **Q17 (F9).** An answer graded before contracts (or on an mvp-0.6 vault) whose key alone was edited since shows the current key. *Default: shown; nothing recorded says otherwise.*

## 9. Round 3

**Verification:** the Codex verification of `3caa7501d`. Verdict REOPENED: F1 (High) and F9 (Medium). F2 to F8 and F10 were confirmed, with no regressions.
**Fix:** `6978cde0a` (sidecar F1), `a5fa07b2c` (sidecar F9), `f01cffbc7` (desktop F1 and F9), `c4e450f1e` (docstrings). Nothing in grading, scoring, scheduling or replay changed. There is no migration, no config change and no new RPC (`record_self_grade_disclosure` takes an optional display id). The replay mismatch stays out of scope (§8.4; the verifier confirmed its numbers).
**How this round was done:** to stop the patch-per-case loop, F1 is designed to one invariant and tested as that invariant, and F9 stops inferring which version a grade read.

### 9.1 Findings

| ID | Severity | What the verifier found | Verdict | Commits | Tests |
|---|---|---|---|---|---|
| F1 | High (reopened) | The exposure ended before the delay after the last look (a crash before the closing row; a visit under a minute writes none; a sleep); a failed write was acknowledged; a pending self-grade disclosure was invisible to other windows | **fixed** | `6978cde0a`, `f01cffbc7` | `test_f1g_*` (16 cases incl. the 10-seed reader property test); `answerExposure.test.ts` (28, incl. the 24-seed gate property test); vitest "F1 (round 3): …" (7 + 3 self-grade) |
| F9 | Medium (reopened) | Snapshot first-seen order does not establish which version was in force (A/B/A/B); "no contradiction" was taken as proof | **fixed** | `a5fa07b2c`, `f01cffbc7` | `test_f9g_*` (2), the reworked `test_f9_*`/`test_f9f_*`/F5 tests (10 cases); vitest "F9 (round 3): …" (5) |

**Reproduced first** (runs recorded in this step):
- **Sidecar F1, against `3caa7501d`:** all 13 new tests failed.
  - The crash reproduction (renewals through hour 50, reading to 50:59, a read at 74:30): `primed=False`.
  - The short-visit reproduction (30 s, then an attempt 24 h 0 min 15 s after opening): `primed=False`.
  - The false acknowledgement: no error was raised, `{recorded: true}` was returned with no row written.
  - The pending disclosure and its refusal: the display id was not accepted.
  - The contract pin and the property test: the coverage constant did not exist.
  - The property test, rerun with the coverage defined locally (D + 1 h) against the old readers: **8 of 10 seeds failed**. The old readers lapse a row at D and ignore a row from before the last attempt.
- **Sidecar F9, against the unchanged serializer:** 10 of 12 failed. The verifier's A/B/A/B step 3 reproduced exactly: the regrade's own response said `changed` right after grading unchanged A. The 2 that passed are the contract controls.
- **Desktop, against `3caa7501d`'s desktop with the new tests copied in:**
  - `answerExposure.test.ts`: 28 of 28 failed. The old module has no gate, and the old screen showed the answer whatever the ledger held.
  - The two Phase 4 screen files: 12 of 62 failed: F1 ×7, the unrecorded label ×2, the self-grade display ×2, and the resumed draft's display row.
  - The 50 that passed include the controls: a contract or live grade with no label, the live response's key, the re-read item, the per-side history.
- **A mutation check of the gate property test:** loosening `covered()` by the margin (`+` instead of `-`) fails 12 of its 28 cases.

### 9.2 F1: one invariant

**The invariant.** For any attempt, or any other admissibility read, at time T: if the full answer was on screen in any window at some moment v in [T − D, T], the ledger already holds a committed row that the reader counts at T. Here D is the routine display horizon, one day, and the admissibility readers are auto-prime (`attempts.reveal_total_for_submission`) and `reveal_ledger.production_admissibility`. Those are the two whose verdict is recorded on a production (`primed`, `admissible_as_independent`).

It is the conjunction of two properties, each built and tested on its own side:
- **Q, the readers** (`6978cde0a`): a committed routine display row stamped s counts at every T with s ≤ T ≤ s + D + G, whatever attempts came between and whatever window a caller reads. G is the renewal grace, one hour (`ROUTINE_DISPLAY_RENEWAL_GRACE`; coverage `ROUTINE_ANSWER_DISPLAY_COVERAGE` = D + G).
  - Auto-prime now counts routine rows by their coverage instead of "since the last attempt". A full answer still on screen in another window after an attempt is an exposure for the next one; before, the row was absorbed into the attempt in between.
  - `production_admissibility` adds routine rows stamped before a caller's `since` (placement and field outcomes pass one).
  - The only exception is a plain self-grade's own disclosure: the commit of the trace frozen before its key was shown (§9.2.3).
- **P, the screen** (`f01cffbc7`, `AnswerExposureGate`): the full answer is on screen at v only while a committed row stamped s exists with s ≤ v and v < s + G − m, where m is a margin of one minute.

**Proof.** Let the answer be on screen at v, with v in [T − D, T]. By P there is a committed row s with s ≤ v and v < s + G − m. Then s ≤ v ≤ T, and T ≤ v + D < s + G + D. So T lies in the row's coverage, and by Q the reader counts it at T. The row was committed before v, so before T. ∎

What this argument does not need:
- **A closing row.** However the screen ends (a crash, a kill, a navigation to an attempt), the row that made the answer visible already covers the next D.
- **A flush before an attempt-leading action.** Every moment the answer is visible is already covered when it is visible, so there is nothing pending to flush. A retry started from feedback starts after a visible moment that is already covered.
- **Rows written on every return.** A return within the grace of the latest row is covered by that row. A return after it is not covered, so the gate writes first and shows only once the new row is committed.

**What P rests on, stated as assumptions:**
1. **One clock.** The desktop and its sidecar run on one machine. The gate compares its own clock with the stamp the sidecar returns (`recorded_at`), floored to the second and never taken later than the client's now.
2. **Timers run in a visible window.** The gate checks every tick (5 s, below m), so an answer can outlive its row's `G − m` by at most one tick: well inside G.
3. **A sleeping machine.** It shows its last frame until the page's first check after waking. That is one tick at most, since a check long after the last one is itself read as a wake, and it hides the answer until a new row is committed. This frozen frame is the one residual outside any page code's control.
4. **A hidden document is not on screen.** While hidden, the answer is not rendered. When the document becomes visible again, it is rendered only if a row still covers it.

**The screen's rules** (`screens/feedback/answerExposure.ts`; the numbers are in `exposureContract.json`, read by both sides and pinned equal by `test_f1g_the_screen_and_the_ledger_share_one_exposure_contract`):
- **When a row is written.** Each row has a new display id. One is written before the answer first appears, and whenever the answer is wanted again after its row stopped covering it: the document visible again, an overlay closed, the machine awake. While the answer stays on screen and the learner is present (input, focus or the page shown since the last row), it is renewed every 40 minutes.
- **An unattended screen.** It lets its row lapse and shows "Hidden while you were away. Show it ▸", so an idle window writes nothing more. This is the growth bound: about one row per 40 minutes of real use, and one row in total for a window left open unattended. The verifier counted 51 rows over 50 idle hours before.
- **Confirmation and failure.** A row counts as confirmed only once the ledger's stamp comes back. A failure keeps the answer hidden ("It can't be shown right now") and is retried under the same display id every tick. A refusal stops the retries.
- **Overlays.** App passes `answerCovered` for the repair step, the inspector and Ask.

**What the writer now reports.** The verifier's injected `sqlite3.OperationalError` produced `{recorded: true}` with no row. `record_answer_display` now returns `recorded_at` and `already_recorded`, the latter when a retry of the same display finds its row. A row that could not be written is `display_not_recorded` (retryable), never an acknowledgement (`reveal_ledger._record_routine_display` raises `DisplayNotRecorded`). The best-effort writers elsewhere are unchanged.

**9.2.3 The pending self-grade disclosure.** The key on a plain self-grade goes through the same gate.
- **How its rows are written.** `record_self_grade_disclosure` with a display id writes a row for the pending draft (`self_grade_disclosure:<retry key>:<display id>`, unlinked) before the key shows, and at each renewal. A display for a draft that is no longer pending is `disclosure_not_pending`, and the key stays hidden.
- **Other productions see it at once.** Every other production is judged against those rows straight away: an attempt in another window is primed, and an unaided answer on the learning object is not independent.
- **The frozen trace's own commit is exempt.** The exemption covers rows whose basis names its retry key (`own_disclosure_bases`):
  - in auto-prime, by the submitting draft's `submission_id`;
  - in `production_admissibility`, when the production judged is the attempt that committed that retry key on that item at that moment, unprimed.
  
  A trace changed after the key was shown is recorded primed, as before (§1), so it gets no exemption.
- **The settle rows** at commit or abandonment are kept. They are no longer the safety mechanism.

**Tests.**
- Sidecar (`tests/test_ux_phase4_feedback.py`, `test_f1g_*`), through the production writers and readers:
  - **The property test (Q):** `test_f1g_every_committed_display_row_counts_until_its_coverage_ends[0..9]`. Random timelines of attempts and display rows, with reads at random later moments; each read sees only what was written by then. It checks that a read is primed, and not independent with or without a `since`, exactly when some row covers it, whatever attempts came between.
  - **The verifier's reproductions:** the crash after reading to 50:59 (covered at 74:30); the 30-second visit with no closing row (covered at 24 h 0 min 15 s); the false acknowledgement (no ack and no row, then one row on the same-id retry and `already_recorded` on the next); the pending disclosure (another window primed, a production not independent, the frozen commit clean and admissible as its own production, the next attempt primed); and the refusal.
  - **The shared contract pin.**
- Desktop:
  - **The property test (P),** `answerExposure.test.ts`. The production gate runs against a simulated clock and ledger over 24 seeded runs of 2 to 4 days. Writes land late, fail, or land with their acknowledgement lost. The answer is wanted and not, the learner present and away, the machine asleep for up to two days with no ticks, and runs end in a crash. At every check, whenever the gate lets the answer be on screen, the ledger holds a committed row stamped s ≤ now with now + one tick < s + G.
  - The same file also checks liveness (an answer in use is on screen all but its first check for 50 hours, with 70 to 80 rows), the unattended screen (1 row, then away, then back), a refusal, and the shared numbers.
  - Component tests: the answer appears only once its row is committed; a failed write is never shown and is retried under the same id; a return after the grace writes first; a sleep hides the answer at the first check; 50 hours in use, always covered; unattended means away and no more rows; an overlay; and the self-grade's key (shown only after its display row; a refusal keeps it hidden).
  - The remount control still passes ("F1 (re-review): reopening the feedback is a fresh exposure…").

### 9.3 F9: no inference

**The sources** (`serializers.GRADING_RECORD_SOURCES`):
- **`contract`:** the grading epoch cites the contract it read (a first grade, a method-explicit regrade, an adjudication carrying its rows' contract). Exact.
- **`live`:** only in the response of a regrade that has just run. It is the content that regrade read: the item and its resolved rubric, taken from the vault it graded with (`serializers.live_grading_record`, captured by `trigger_regrade` before the regrade). It is never persisted as proof. The next load of the same feedback is `unrecorded`.
- **`unrecorded`:** every other epoch, such as an ordinary regrade reopened later or an answer graded before contracts. No key or criteria are presented as graded, and the only maximum given is one recorded with the grade, a blind record's.

The snapshot-order selector (`_item_version_in_force`, `_epoch_contradicts_item`) is gone, and so is the item snapshot `trigger_regrade` took for it.

**On the desktop:**
- **The label.** An unrecorded grade says "The version of this question it was graded against wasn't kept."
- **No graded criteria lines.** There are no ✓/✗ lines, and details give the points alone, or out of a recorded maximum.
- **The current answer.** It offers the current answer under "The answer as the question reads now", with "It may not be the one this was graded against." That display goes through the same gate as any answer display, so it is charged.
- **A contract or live grade** shows its own key, with no label.
- **The regrade history** keeps each side's own maximum, as recorded.
- **After a regrade in place** the item is still re-read (for an older sidecar).

**What this costs, and when it goes away.** Every ordinary regrade, and every answer graded before contracts, now reads as unrecorded once its feedback is reopened, even when the item never changed. Round 2 had asked that an unchanged item show no label; this round's direction supersedes that, since nothing recorded proves "unchanged". When the successor stage makes regrades cite the contract they read (§8.4), new regrades become `contract` and `unrecorded` becomes rare.

**Tests.**
- Sidecar:
  - `test_f9g_the_a_b_a_b_sequence_never_presents_a_version_as_graded_without_a_record` (the verifier's sequence with the production snapshot writer: `live` with A's key in the regrade's response, `unrecorded` after, and B never presented as graded);
  - `test_f9g_a_contract_cited_epoch_stays_exact_whatever_was_served_since`;
  - `test_f5_an_answer_with_no_contract_is_unrecorded` (the no-snapshot case);
  - the reworked live (`[regrade|contest]`), historical (`[blind|joint]`), unchanged-reopened, blind and outside-the-screen (`[later|same_second]`) cases.
- vitest:
  - an unrecorded grade (the label, the current answer labelled and charged, no "/ 10");
  - its recorded maximum;
  - a contract or live grade with no label (×2);
  - the live response's key.

### 9.4 Claims corrected

- **§8.2 and §8.3** are marked superseded in place.
- **§8.8 Q14** (the cadences): now 40-minute renewals while present, a one-hour grace, a one-minute margin and a 5-second tick, with no closing row. **Q15** (the cautious "changed" label) and **Q17** (a legacy key-only edit) are replaced by `unrecorded`, which claims neither.
- **`docs/reviews/ux-phase4.md`:**
  - §1: the bundle's sources, and no item snapshot on regrade.
  - §4.1: the self-grade key's display rows.
  - §4.2: the gate, the "away" state, and the unrecorded label and current answer.

### 9.5 Paid calls

None. Every test uses fakes. The fail-first runs used temporary copies of `3caa7501d`'s source, since removed. No owner vault was opened.

### 9.6 Gate (final tree)

Run on `c4e450f1e` in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (done in §8.7; no dependency changed since):

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11922 passed, 0 failed (13 min 25 s): §8.7's 11905, plus 16 `test_f1g_*` cases and 2 `test_f9g_*`, less the removed cannot-place test |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11816 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 94 files, 724 passed (692, plus the gate's 28 property and unit cases, plus the reworked and new screen cases); the build succeeds (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `apps/learnloop-tauri/src-tauri` changed (`record_self_grade_disclosure` passes its input through) |
| CLI help snapshot, RPC pins (`tests/test_mobile_allowlist.py`), DB/config references | unchanged: no CLI, RPC, schema or config change (both test files ran in the full suite) |

The code was final at `c4e450f1e`; only this record and `docs/reviews/ux-phase4.md` changed after it. No run had a timing failure.

### 9.7 Open questions for the owner (defaults applied)

- **Q18 (F1).** The coverage is the delay plus a one-hour grace, so a routine display primes for up to 25 hours after the row that last covered it, not 24. *Default: as built (conservative by construction).*
- **Q19 (F1).** An answer left on screen with no input for about an hour hides itself ("Hidden while you were away"), and one click shows it again. Shorter or longer? *Default: a 40-minute renewal and a 59-minute visible bound.*
- **Q20 (F1).** Auto-prime now counts a routine display by its coverage even across an attempt in between, so a retry the same day after a full answer stays "with help". *Default: as built (the invariant needs it).*
- **Q21 (F9).** Until regrades cite their contract, every reopened ordinary regrade, and every pre-contract answer, shows the unrecorded label and the current answer labelled as current. *Default: as built. The successor stage (§8.4) removes most of it.*
- **Q13 and Q16** stand: summed reveal amounts in receipts count each row, and classic is unchanged.

## 10. Round 4

**Verification:** the Codex verification of `4186c6cc3`. Verdict REOPENED, with five findings:
- F1-1, the frame left on screen after a wake (High);
- F1-2, an exemption wider than the frozen original (High);
- F1-3, the clock going back (Medium);
- F9, Details of an unrecorded grade (Medium);
- a new one (Medium): cold checks were served before the new coverage expired.

**Fix:** `76e6b97fb` (sidecar: F1-2, F1-3 readers, cold checks) and `e09935dc1` (desktop: F1-1, F1-3, F9). Nothing in grading, scoring or replay changed. The scheduler's cold follow-up deferral now reads routine displays by their coverage, as the orchestrator ruled. There is no migration and no config change. The RPCs are unchanged; `production_admissibility` gained a `production_id` argument.

### 10.1 The orchestrator's rulings (recorded as given)

1. **F1-2:** exemptions match exact identity: the frozen trace's content hash equals the submitted trace, and the exact attempt or production id. Never a retry key or a timestamp alone, and never checkpoint state that can be settled away.
2. **Cold checks:** ONE coverage definition, the routine-display coverage D + G. It is shared by the submit readers, by the scheduler's serving and deferral of cold follow-ups, and by every other server-side eligibility read that consults reveals. Other reveal kinds keep their rules. The scheduler never serves what submit would refuse.
3. **F9:** in `unrecorded`, Details shows only what the grade itself recorded (criterion ids and points awarded), labelled as recorded. Current rubric text appears only under the "as the question reads now" label, and is charged like the key.
4. **F1-3:** readers count a committed routine display row stamped in the future as covering T; a row is never invisible because the clock went back. On the desktop, a backwards clock jump is a discontinuity, treated like a wake.
5. **F1-1:** the answer hides on every lifecycle signal that precedes a suspend or a loss of attention, and reappears only after a fresh row is acknowledged. The remaining residual is accepted and documented (§10.3). No heartbeat or open-session machinery.

### 10.2 Findings

| ID | Severity | Verdict | Commit | Tests |
|---|---|---|---|---|
| F1-1 | High | **fixed** (residual documented, §10.3) | `e09935dc1` | vitest "F1-1 (round 4): …" (4: hidden, blur, pagehide, freeze); the gate property test with interruptions |
| F1-2 | High | **fixed** | `76e6b97fb` | `test_f1i_a_changed_trace_under_the_frozen_key_is_primed_once_the_checkpoint_moved_on`, `…_the_unchanged_frozen_trace_stays_exempt…` (control), `…_only_the_commit_itself_is_exempt_never_another_response_in_its_second` |
| F1-3 | Medium | **fixed** | `76e6b97fb`, `e09935dc1` | `test_f1i_a_display_stamped_ahead_of_the_clock_still_covers`, `…_a_display_after_a_production_does_not_count_against_it` (control); vitest "F1-3 (round 4): …"; the gate property test with clock jumps |
| F9 | Medium | **fixed** | `e09935dc1` | vitest "F9 (round 4): an unrecorded grade's details show only what the grade recorded…" |
| New | Medium | **fixed** | `76e6b97fb` | `test_f1i_the_scheduler_never_serves_a_cold_retry_that_submit_would_refuse[0..5]` (property), `test_f1i_an_independent_check_is_not_offered_inside_a_display_s_coverage` |

**Reproduced first:**
- **The new sidecar tests, against `4186c6cc3`:** 9 of 12 failed.
  - (a): a changed trace under the frozen key after the checkpoint moved was `primed=False`.
  - (b): another response in the commit's second was admissible.
  - A row two minutes ahead of the clock was invisible to `production_admissibility`.
  - The scheduler property failed on 5 of 6 seeds: the cold task was served while submit would prime it, in each display's last hour of coverage.
  - The independent check offered an item whose answer had been on screen 24 h 30 min earlier.
  - The 3 that passed are the two controls and seed 2.
- **The new component tests, against the round-3 desktop:** 6 of 6 failed: hidden, blur, pagehide, freeze, the backwards clock jump, and F9's Details.
- **The gate property test, extended with interruptions and clock jumps:** 23 of 28 failed against the round-3 gate. It has no interruption, and a clock jump left the answer shown.

### 10.3 F1-1: hidden before a suspend can keep it (High)

**The finding.** Mount, acknowledge, then let 26 hours pass with no timer or lifecycle event delivered. The DOM still shows the full answer before the first wake check, while the readers say clean.

**The fix.** These signals hide the answer synchronously (`flushSync`), so the frame a suspend keeps is the hidden one:
- the document becoming hidden;
- `pagehide` and `freeze`;
- window `blur`;
- the shell window losing focus or being minimized (Tauri `onFocusChanged` and `onResized` with `isMinimized`; no-ops outside the shell).

The gate counts interruptions as epochs. A row sent before an interruption never shows the answer again. The answer reappears only after a fresh row, sent after the interruption, is acknowledged. A return (focus, `pageshow`, `resume`, visible again) writes that row at once.

**The residual, accepted and documented.** An OS suspend that delivers none of those signals keeps the last frame on screen. It stays until the page's first check after waking, at most one tick (5 s), and that check reads the wall-clock gap as a wake and hides the answer until a fresh row is acknowledged. While the frame is on screen, the readers at T only count rows that existed before the suspend. So an attempt made from another window or the CLI in that interval, more than D + G after the last row, is not covered. There is no heartbeat or open-session machinery for it, per ruling 5.

**The cost.** Every return after a blur writes one row, and the answer shows "One moment…" until the row is acknowledged.

### 10.4 F1-2: the exemption is the frozen trace, exactly (High)

**The finding.**
- (a) Freeze and display `sub`, move the checkpoint (settling the disclosure as abandoned), then submit a changed trace under `sub`. Nothing compared it any more, and auto-prime exempted by retry key alone.
- (b) After the clean frozen commit, a different response assessed in the same second was admissible, because the exemption matched item and timestamp.

**The fix.**
- **The rows carry the trace's hash.** Every disclosure row now carries the hash of the trace its draft froze: `self_grade_disclosure:<retry key>:<trace hash>` for the settle row, `…:<display id>` for a display row (`reveal_ledger.disclosure_basis`). The hash is computed from the checkpoint's frozen trace when the row is written. It is durable in the ledger, the proof the checkpoint was not.
- **Auto-prime** exempts a submission only from rows naming its retry key and the hash of the trace it sends (`own_disclosure_bases(submission_id, learner_answer_md)`). A changed trace under the same key, or the same words under another key, is not exempt.
- **`production_admissibility`** exempts only the production named by its new `production_id`, and only when that attempt committed exactly the frozen trace (its retry key and trace hash). A timestamp is never used. The callers that judge an attempt pass its id: probe admissibility (`causal_orchestrator`), field outcomes, and placement. A caller with no id gets no exemption, the cautious side.

### 10.5 F1-3: a clock that goes back (Medium)

**The finding.** Acknowledge a row, then move the wall clock back 120 s. `covered()` stays true, while `production_admissibility(until=T)` excluded the now-future row.

**The fix, on the readers.** A routine display row stamped after the reader's own clock counts as covering. Auto-prime has no upper bound. `production_admissibility` adds routine rows stamped after `max(produced_at, now)`. A display stamped after a production but no later than now came after that production, and does not count against it (the control test).

**The fix, on the desktop.** A clock that went back since the last check is a discontinuity, like a wake. `covered()` is false at once, and the next check interrupts and writes a fresh row. Presence is a counter, never a clock time, so a rollback cannot strand the screen as "away".

**A note for derived reads.** Field outcomes call `production_admissibility` at rebuild. A rollback artifact (a row stamped ahead of the rebuild's clock) counts there until the clock passes it, on the cautious side.

### 10.6 F9: Details of an unrecorded grade (Medium)

**The finding.** Change a criterion's description to "The correct answer is B." and reopen an `unrecorded` grade. Details showed it under "What the grader looked for".

**The fix.** For `unrecorded`, Details shows only what the grade recorded: each criterion id with its points awarded (or "not judged"), under "What this grade recorded". It shows no description, no tier and no maximum. The current rubric text is not shown at all. The only current-version content is the answer key, under "The answer as the question reads now", charged through the gate (§9.3). Contract and live grades keep "What the grader looked for".

### 10.7 New: serving agrees with submit (Medium)

**The finding.** A routine display after a cold task was created. At 24 h 30 min the scheduler served the task (one-day delay), but submit auto-primed the item under the 25-hour coverage: "a cold retry must be unassisted and unprimed".

**One definition.** `learnloop/reveal_coverage.py`, stdlib only, so persistence, scheduling and instructional code all import it:
- the routine bases, the horizon D, the grace G and the coverage D + G;
- a routine-display SQL predicate;
- `routine_window_start(since)`: a reader whose window starts at T − D reads routine rows from T − D − G;
- `routine_counts_until`.

`reveal_ledger` re-exports its constants.

**Every reader of the reveal ledger (grep inventory) and what it does now:**

| Reader | What it decides | Routine displays |
|---|---|---|
| `attempts.reveal_total_for_submission` (auto-prime) | `primed`, the cold-retry refusal | by coverage, whatever attempts came between, also stamped ahead (§9.2, §10.5); exact-identity exemption (§10.4) |
| `reveal_ledger.production_admissibility` | independence of probes, eliciting answers, placement, field outcomes | by coverage, also before `since` and stamped ahead; exemption by `production_id` |
| `scheduler._cold_task_reveals` (deferral, and `deferred_cold_followups`) | serving a cold follow-up | **by coverage, whenever stamped**; pushed to the last reveal's end (a routine row's coverage, the lane delay for others). Other kinds keep "since the task's creation" |
| `practice_index.items_revealed_between` (serving exclusions) | items held back from serving | by coverage (from the grace before the window, and stamped ahead) |
| `instructional.exposure.independent_check_eligibility` | whether a candidate may stand as an independent check | by coverage |
| `source_service.serve_time_exposure` | serve-time eligibility of a source exercise | by coverage |
| `practice_index.retrieval` (`exclude_revealed_families`) | retrieval filter | by coverage |
| `source_service` shown items (exam protection) | any reveal ever | unchanged (no window) |
| `coldness_receipt` | a receipt over the cold attempt's explicit interval | unchanged (records what happened in it; the scheduler no longer serves inside a coverage) |
| `router.outcomes`, `substrate.intervention_outcomes`, `daily_plan.router_card`, `learner_context` | derived covariates and counts | unchanged (they count rows, Q13) |
| `diagnosis.remediation`, `diagnosis.split.card`, the ledger's own dedupe | by episode or basis | unchanged |

**Tests.**
- `test_f1i_the_scheduler_never_serves_a_cold_retry_that_submit_would_refuse[0..5]`, a property over display and cold-task timings: displays from 10 hours before the task's creation to 50 hours after, and queue builds at random later moments and inside each display's last hour of coverage. Whenever the cold lane serves the task, a submission then is not primed.
- `test_f1i_an_independent_check_is_not_offered_inside_a_display_s_coverage`.

### 10.8 Claims corrected

- **§9.2 "the readers covered are auto-prime and production_admissibility":** now every eligibility reader (§10.7).
- **§9.2 assumption 3 (a sleeping machine):** narrowed to the residual in §10.3.
- **§9.2.3 exemption "by the submitting draft's submission_id" and "at that moment, unprimed":** now by retry key and trace hash, and by `production_id`.
- **`docs/reviews/ux-phase4.md` §4.1 and §4.2:**
  - the answer hides on every lifecycle signal;
  - an unrecorded grade's Details show what it recorded;
  - the self-grade's exemption is the exact frozen trace.

### 10.9 Paid calls

None. Every test uses fakes. No owner vault was opened.

### 10.10 Gate (final tree)

Run on `e09935dc1` in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp` (dependencies unchanged since §8.7):

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken (`learnloop/reveal_coverage.py` is a stdlib-only leaf, imported by `db`, `scheduling`, `instructional` and `attempts`) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11934 passed, 0 failed (12 min 17 s): §9.6's 11922 plus the 12 `test_f1i_*` cases |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11828 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 94 files, 730 passed (724 plus the 6 round-4 component cases; the gate property test's cases are the same 28, now with interruptions and clock jumps); the build succeeds (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `apps/learnloop-tauri/src-tauri` changed (the Tauri window listeners are the existing `@tauri-apps/api` JS) |
| CLI help snapshot, RPC pins (`tests/test_mobile_allowlist.py`), DB/config references | unchanged: no CLI, RPC, schema or config change (both test files ran in the full suite) |

The code was final at `e09935dc1`; only this record and `docs/reviews/ux-phase4.md` changed after it. No run had a timing failure.

### 10.11 Open questions for the owner (defaults applied)

- **Q22 (F1-1).** Hiding on every window blur means a one-row write and a brief "One moment…" on each return to the app. *Default: as built (ruling 5).* A shell-only signal set (minimize and unfocus, without DOM blur) would cut the rows.
- **Q23 (F1-1).** The residual: an OS suspend that sends no signal keeps the last frame for at most one tick after waking. *Default: accepted and documented (ruling 5).*
- **Q24 (cold checks).** A routine display stamped before a cold task's creation now also holds it back until its coverage ends. A cold retry scheduled the day after a feedback that showed the answer can wait up to an hour longer. *Default: as built (serve agrees with submit).*
- **Q13, Q16 and Q18 to Q21** stand.
