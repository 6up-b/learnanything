# UX fixes: broken controls, third round (group A)

The defects the third wave of persona walks found on Today, practice, feedback and the session end (`ux-journey-audit-3.md` §5.1, §2.3, F39 and F45), and one flaky test. Ledger ids UX-46 to UX-49, UX-52 and UX-53 (`refactor-bug-ledger.md`, "From the UX journey audit's walks"). Group B (the Reader and the Library: UX-50, UX-51, UX-54 to UX-57) is another branch's. Branch `ux/broken-controls-3a` from the audit branch (main `1f9c8de1b3` plus the audit's third part and its ledger rows), one commit per defect. Desktop, simple shell unless said; the phone only where it says the same line through shared code. Two small sidecar changes, each said under its defect (UX-49, UX-53).

| Defect | Sev | Commit | What |
|---|---|---|---|
| UX-47 | S2 | `9935c6ad99` | A topic that failed while the rest are written is said under the writing line; Try again once the writing stops |
| UX-52 | S3 | `db5bed557c` | Today offering questions says no "Nothing planned for today.", and only the control Enter activates shows ↵ |
| UX-49 | S2 | `155fa4d00c` | The session end says "partly on your own, finished with help" (sidecar: a display field) |
| UX-48 | S2 | `72d7e77e5f` | The guided redo's "What to fix" is the rubric lines the answer missed, never the repair's rationale |
| UX-53 | S3 | `0052487c92`, `1c4b5c576f` | A quick check whose writing failed is said with Try again, at the next poll and after reopening (sidecar: a read of the job queue); the second commit sends the key only when there is a failed check |
| UX-46 | — | `1c273e26d3` | The phone-plan tests' desktop starts no post-attempt slots (tests only) |

This record and the ledger cells are the last commit.

## UX-47 (S2): "Couldn't write the questions…" with a Try again that does nothing, while the writing goes on

**What the person saw** (firstq-7 #60-70). With no question offered yet, topic 1's questions refused (empty ids) while topics 2 to 8 were still being written: Today said "Couldn't write the questions from what you read in “…”. Try again, or keep reading: nothing is lost." with Try again and "Keep going ↵"; Try again, pressed twice, changed nothing visible; the person gave up while the writing went on.

**Cause.** `app/todayCause.ts` `todayCause`: a book whose fact had any `questions.failed` entry pushed the `section_failed` rank, and `ORDER` puts `section_failed` above `section_writing`; the `section_failed` case took `failed[0].resumeId`. The fact lists a failed topic while its section's job still runs (`ux-first-questions-progress.md`, step 0), and `runner.resume_batch` requeues only stopped jobs, so the resume was a no-op. The progress record's rule (no Try again while that section is still being written) was applied only to the offer's line (`questions_ready_with_section_work`), not to the nothing-ready state.

**What they see now.**
- Nothing offered, a topic failed, the section still being written: the writing line, with its amount, and the failed topic under it with no Try again:
  "◐ Writing questions from what you read in “…” · 0 of 8 topics done" (or "… from “Section”, the part you read · 2 of 8 topics done") with **Continue reading**, then **Not every topic's questions could be written.**, then "Keep reading meanwhile." (`today-cause-failed`, as on the offer's line).
- Once that section's writing stops (Today rereads every 5 s and on the shell's queue-changed signal while the writing shows), nothing else written: the stopped section's unchanged line "Couldn't write the questions from … Try again, or keep reading: nothing is lost." with **Try again** (resumes the stopped batch) and what's sent.
- A stopped section beside another still being written: the stopped one's line, and its Try again resumes **its own** batch (it took the first entry's, which could be the running one's), and its part is named from the stopped entries only.
- The phone (shared `causeSentence`): "Writing questions from “Conditional probability”, the part you read · 1 of 8 topics done. Not every topic's questions could be written. Keep reading meanwhile." (Keep going stays its one action).

Only an entry whose section is no longer being written (`stoppedEntries`, the same label rule `stillWriting` the offer's line uses) makes the `section_failed` rank; `section_writing` gains `failedTopics`; `causeTopicsFailed` answers for it too.

**The progress record's table** (`ux-first-questions-progress.md`, "States, words and actions"): the row "All failed, nothing ready (unchanged)" now holds only once the failed entry's section has stopped; with it still being written the state is the writing row (with or without its amount) plus the line "Not every topic's questions could be written." and no Try again (this record's row above). The other rows are unchanged.

**Tests** (fail first on the base, `ec18ef6fcd`):
- `screens/today/TodayPlace.test.tsx` › "Broken controls, third round: a topic that failed while the rest are still written (UX-47)": `nothing offered yet: the writing line with its amount, the failed topic beside it with no Try again; Try again once the writing stops` (failed: `Unable to find an element with the text: Writing questions from what you read in “Symmetric Matrices and Variance” · 0 of 8 topics done`); `a stopped section beside another still being written: the stopped one's Try again resumes its own batch, never the running one's` (failed: the line said "from what you read" and the resume went to the running batch); `its words are plain` (control, passed on both).
- `apps/learnloop-mobile/src/today/Today.plan.test.tsx` › `nothing written yet and a topic failed while the rest are written: … (UX-47)` (failed: received "Couldn't write the questions from “Conditional probability: Bayes' rule”. Try again, …").
- `copy/denyList.test.tsx`: the new `ROUND_3A_SENTENCES` (the writing-with-a-failed-topic causes' sentences, goal sentences and failed line; failed on the base: the failed line was empty).

No existing assertion changed.

## UX-52 (S3): "Nothing planned for today." above an offer, and two ↵

**What the person saw** (firstq-10 #58, #78; firstq-9 #56, #101). "Nothing planned for today." above "3 questions … are ready. More are being written (1 of 8 topics done). [Begin ↵]" and "[Keep going ↵]"; read as "my reading produced no work", and still there after practice.

**Cause.** `screens/today/TodayPlace.tsx`: the done branch's heading is "Nothing planned for today." for an empty plan (`planWasEmpty`; picks from the list leave the day's plan empty, so it stays after practice), and Keep going is always labelled "Keep going ↵", while the Enter handler sends Enter to the offer's Begin when the cause offers a book's questions. The open-plan branch says the same heading when it has no sentence.

**What they see now.** While Today offers a book's questions (`questions_ready` or `questions_ready_with_section_work`):
- no "Nothing planned for today." heading, in the done branch and in an open plan with nothing in it: the offer's line is the first thing under the day ("3 questions from what you read in “…” are ready. More are being written (1 of 8 topics done). **Begin ↵**");
- ↵ only on the control Enter activates: the offer's **Begin ↵**; the buttons read **Keep going** · Something new · Done for today. Where nothing is offered, Keep going keeps its ↵ (Enter is Keep going there), and the plan's own Begin/Continue keeps its ↵ unless an offer is on screen.

Every other heading is unchanged ("Nothing planned for today." above a writing line or a stopped one, "Done for today · …", "Catch-up done."); F45's set of "nothing" sentences is the next stage's.

**Tests** (`TodayPlace.test.tsx` › "Broken controls, third round: Today offering questions says no 'nothing planned', and one control shows Enter (UX-52)"), fail first: 3 failed, 1 control passed:
- `an empty, finished plan with questions offered: …` (failed: `expected [ 'Begin ↵', 'Keep going ↵' ] to deeply equal [ 'Begin ↵' ]`; then Enter picks the offer's question, Keep going not called)
- `after practice outside the plan: the plan stays empty, and still no 'nothing planned' while questions are offered` (failed: `expected 'Tuesday eveningNothing planned for to…' not to match /Nothing planned/`)
- `an open plan with nothing in it and questions offered: …` (failed the same way)
- `an empty, finished plan with nothing offered: the heading stays, and Keep going is the one control with ↵ (Enter is Keep going)` (control, passed on both)

No existing assertion changed (stage 3's "Nothing planned for today." tests have no offer).

## UX-49 (S2): "(on your own)" for a topic finished with help

**What the person saw** (firstq-9 #102 and report). "● Construct a diagonalization from an eigenvector basis (on your own)" after a partly right answer of their own and a redo the feedback marked "◌ Practice with help."; read as contradicting the redo.

**Cause.** `learnloop_sidecar/handlers/sessions.py` `_session_topics`: a topic is `on_your_own` once any own answer in the session earned credit (the session diff's `demonstrated_attempt_ids`; here the partly right answer's right parts), and the loop skipped every later answer of the topic, so help after it was never seen; `components/SessionFinishHud.tsx` showed one mark from `evidence`.

**The sidecar change (the smallest that can say it).** The desktop has only the session end's `topics`; which of a topic's answers were partly right and what came after is in the session's attempts, read only by the sidecar. `_session_topics` now also sets `finished_with_help: true` on an `on_your_own` topic when none of its credited own answers was fully right and an answer with help (hints, primed, a walkthrough) earned points after the last of them (held answers skipped, as before). Display only: `evidence`, the credit, the session diff and everything stored are unchanged; the key is absent otherwise, so the existing payload assertions stand.

**What they see now.** "● Construct a diagonalization from an eigenvector basis **(partly on your own, finished with help)**"; "● Topic (on your own)" and "◌ Topic (with help)" as before. (`sessionTopicLine`.)

**Tests:**
- `tests/test_ux_phase4_feedback.py`: `test_a_partly_right_answer_on_your_own_then_finished_with_help_says_both` (failed: `('lo_svd_definition', 'on_your_own', None) != (…, True)`); `test_on_your_own_stays_plain_unless_help_finished_a_partly_right_answer[fully_right_then_help|partly_right_no_help|help_then_partly_right]` (3 controls, passed on both). Fail-first run: 1 failed, 3 passed.
- `components/SessionFinishHud.phase4.test.tsx` › `a topic answered partly right on your own and finished with help says both, never only 'on your own' (UX-49)` (failed: the line said "(on your own)").
- `copy/denyList.test.tsx`: the three marks.

## UX-48 (S2): "What to fix" written for the system

**What the person saw** (firstq-9 #95-96). "Redo the part you missed / What to fix: Preserve the correct setup and elicit the omitted computations before revealing the repaired trace. Separating inverse verification from multiplication tests whether the second omission is merely downstream of the first."; "I do not know what I am meant to do with that wording".

**Cause.** `diagnosis/guided_redo.py:350` sends the selected repair suggestion's `rationale` (the diagnosis model's reason for its repair, `RepairSuggestion.rationale`, emitted after the edit it explains) as `redo_instruction`; `screens/PracticeScreen.tsx` printed it under "What to fix:" (simple shell) and "what to fix:" (classic).

**What they see now** (frontend only; the sidecar still sends the field, now documented as system-facing in `GuidedRedoDto`). The feedback screen hands the redo the rubric lines it marked ✗ or ◐, in the words it showed (`missedRubricLines`: assessed criteria below full points, from the frozen rows the feedback shows; none for a held grade or an unrecorded version), and the practice screen lists them:

```
Redo the part you missed
What to fix:
✗ Establishes P^{-1}=[[1,-2],[0,1]].
✗ Establishes A=PDP^{-1}=[[4,-10],[0,-1]].
Your work so far, kept
…
```

The classic shell shows the same lines under "what to fix:". The rationale is never shown. A redo opened where no lines were on show (the probe block review, `ProbeBlockResult`, whose released feedback carries no criterion rows) shows no "What to fix" line. No new TypeScript file (`RedoContext`, `MissedRubricLine` and `missedRubricLines` live in `screens/feedback/FeedbackSurface.tsx`).

**Tests** (fail first: 4 failed):
- `screens/PracticeScreen.phase4.test.tsx`: `the redo's 'What to fix' is the rubric lines the answer missed, in the feedback's words, never the system's rationale (UX-48)` (failed: `Unable to find an element by: [data-testid="redo-what-to-fix"]`), `a redo with no missed lines to show says no 'What to fix' rather than the rationale (UX-48)` (failed: the page contained the rationale), `classic: the redo shows the missed lines too, never the rationale (UX-48)` (failed as the first).
- `screens/FeedbackScreen.phase4.test.tsx`: `the guided redo carries the rubric lines the answer missed, as the feedback showed them (UX-48)` (failed: `onGuidedRedo` was called without `missedLines`).

### Every other place that prints a repair suggestion's `rationale`, or another system-facing field, to the learner

Found by reading every `rationale` read in `apps/learnloop-tauri/src` and `apps/learnloop-mobile/src` (the phone prints none) and the sidecar fields behind them, and the walks' screens.

| # | Where | Field | Surface | Fixed here? |
|---|---|---|---|---|
| 1 | `PracticeScreen.tsx`, redo, simple shell | `redoInstruction` = the selected repair suggestion's `rationale` | the redo, default | **yes** |
| 2 | `PracticeScreen.tsx`, redo, classic shell | the same | the redo, classic | **yes** |
| 3 | `components/DiagnosisCard.tsx` "repair · …" list and the escalation's repair line | `repairSuggestions[].rationale`, `escalation.repair.rationale` (the same field) | the feedback's "details ▸" (simple), the classic feedback | no (UX-48b) |
| 4 | `components/CausalAttribution.tsx` `CausalFeedbackPanel`: "verified · Checked repair" and "suggested next step" | `verifiedCorrection.rationale`, `proposedNextAction.rationale` (both the selected suggestion's `rationale`, `diagnosis/causal_attribution.py` 3092, 3201) | the feedback's "details ▸" ("Why it went wrong"), the classic feedback, the probe block review | no (UX-48b) |
| 5 | `screens/ExamScreen.tsx` "suggested repair" | `repairSuggestions[0].rationale`, beside the raw `practiceMode` | an exam answer's review | no (UX-48b) |
| 6 | `components/CausalAttribution.tsx` `CausalEpisodeInspector` "repair decision"; `components/InspectorOverlay.tsx` repairs | the suggestion's `rationale` with its class id and practice mode | the inspector (receipts, ids by design) | no: a receipts view |
| 7 | `PracticeScreen.tsx`, classic redo, "failed steps" | `failedCheckpointIds` as pills (checkpoint ids) | the redo, classic | no (another field; UX-48b names it) |
| 8 | `screens/feedback/FeedbackSurface.tsx`, the sentence under the ✓/✗ lines | the diagnosis card's `summaryMd`; in firstq-9 #94 a third-person analysis ("The current answer correctly constructs P and D … the trace cannot establish whether…") | the feedback, default | no: another field (F38's "third person about the learner") |
| 9 | `screens/feedback/FollowupPanel.tsx` `RouterDecisionLine` "details" | the decision's `rationale` ("Why: …"), model names with raw JSON answers, "Decision {id}" | the feedback, behind "details" | no: another field |
| 10 | `components/SourceOffers.tsx` (Ask) | a proposed item's or exercise's `rationale` as its detail line | Ask's offers | no: another field; its audience not traced |

Rows 3 to 5 are the same field. They are left as they are here because each is a glass-box or review panel whose content the rationale is (its tests read it as such, `DiagnosisCard.test.tsx`), and taking it out empties the panel: what belongs there instead is a design call beyond this defect. Ledger row UX-48b (added) carries them, with rows 7 and 8's words for the same pass.

## UX-53 (S3): a quick check whose writing failed is never said

**What the person saw** (student-3 #54-63, #96; the walk's vault: the check's job failed at 3:29). "◐ writing a quick check for this section…" for over a minute after the failure; after leaving and coming back, only "Keep reading at your own pace."; no failure, no Try again.

**Cause.** `screens/reader/useReadingProgress.ts`: while a section's check is written the Reader polls `reader.guide_plan` every 4 s until the section has a question or 45 polls pass (3 minutes), and only then says "Couldn't write a check". The plan carried no failed state (the job's state is in the job queue, `ingest_jobs`), so a failed job read as writing; `resetProgress` clears the authoring and timed-out sets when the Reader reopens, and the section's state came back as nothing.

**The sidecar change (the smallest that carries the fact).** `reader.guide_plan` adds `check_failed_section_ids` (`checkFailedSectionIds`): the sections with no question whose newest section-check job (`reader_quick_check` with this extraction and a `section_id`; passage and selection checks carry none) failed. A newer job for the section (Try again) replaces the failure. The key is present only when there is such a section, so a plan with none keeps its bytes (two stage pins hold the whole plan: `tests/test_reading_paths.py`'s `a76c8358a` and `tests/test_reader_rw3b_switch_off.py`'s `c9ad9cce1`; a first version that always sent the key failed three of their tests and was changed, not the pins). It reads the queue through a new store read, `ingest_jobs_by_payload` (`db/stores/ingest_queue.py`, the list form of the existing `newest_ingest_job_by_payload`). Nothing stored, sent to a model or computed about the learner changes.

**What they see now.**
- The poll stops the writing line at its next read after the job fails (within 4 s) and says **Couldn't write a check for this section · Try again** (the existing words and action).
- Reopening the Reader at that section says the same, with Try again; the Reader no longer asks for a failed section's check again on its own when the learner reads on (it did, silently, after a reopen): only Try again does.
- Try again: "◐ writing a quick check for this section…" again, as before.

**Tests:**
- `tests/test_reader_quick_check_failed.py` (new): `test_a_section_whose_check_failed_is_named`, `test_a_newer_try_for_the_section_replaces_the_failure`, `test_other_checks_failing_name_no_section` (a passage check, the same section id in another reading, a completed job; no key in the plan). Fail-first (as first written, every case reading the key): 3 failed (`KeyError: 'checkFailedSectionIds'`); with the key absent when empty, the first is the fail-first test and the other two are its controls.
- `screens/ReaderScreen.quickcheck.test.tsx`: `a check whose writing failed is said at the next look at the plan, with Try again, not after the poll gives up` (failed: the writing line was still there after two polls), `reopened at a section whose check failed: the failure and Try again, and no check asked for again on its own` (failed: `Unable to find … Couldn't write a check for this section`). The two existing tests (the 45-poll timeout, no check on the reopened passage) pass unchanged.

## UX-46: a phone-plan test that does not wait for its worker

**The race.** `tests/test_mobile_v2_plan.py`'s desktop (`_desktop`, a `SidecarContext`) answers questions; each `submit_dont_know` calls `post_attempt_worker.notify`, which starts all four post-attempt slots. At teardown `SidecarContext.close` shuts the worker down with a 2 s join, then the thread guard gives 2 s more; a slot still inside its work (a claim retrying a locked database: `_with_busy_retry` sleeps 0.5 s doubling, each try up to `busy_timeout`) outlives both under load: "left 1 thread(s) running after a 2s join grace … 'learnloop-post-attempt-diagnose'".

**Shown with a test-only delay** (a scratch test file, not kept): `PostAttemptWorker.run_pending("diagnose")` patched to sleep 8 s, then j5 and the None-origin test called as they are: on the base both errored at teardown with exactly the ledger's message (thread `learnloop-post-attempt-diagnose`, started in `post_attempt_worker.py:111 notify`); with the fix, the same delayed run: 2 passed.

**Why not a wait on the queue.** The other suites' wait (`PostAttemptWorker.wait_for` on the durable queue, `tests/test_post_attempt_worker.py`) returns at once here: these journeys queue no diagnosis (measured: `post_attempt_jobs` is empty after the None-origin journey), and a slot can be inside its claim with nothing queued. The suites that do not read post-attempt work keep the slots unstarted (`ctx.post_attempt_worker.autostart = False`, 23 helpers, `tests/test_mobile_v2_followup.py` among the phone's): the fix is that, in a helper `_desktop_without_worker` (`tests/mobile_v2_plan_helpers.py`) that `test_mobile_v2_plan.py` now uses for its desktop. `_desktop` itself is unchanged (seven other files share it, two of them about diagnoses).

**No behaviour change in what the tests check** (compared on the None-origin journey, base helper against the new one, same vault and frozen clock): the eight steps served were identical (`pi_b2, pi_a1, pi_a2, pi_svd_define_001, pi_b1, pi_eig_easy, pi_eig_mid, pi_diag_easy`); the only difference is that the follow-up generation jobs the answers queue (8) were worked by the desktop's slot before (5 done, 1 leased, 2 queued at the end, each failing for want of a model) and now stay queued; nothing in these tests reads them. The file runs in about 40 s instead of 57 (`next_plan_item` no longer waits on them).

**Test** (fail first): j5 and the None-origin test now end with `post_attempt_jobs() == []` and `not ctx.post_attempt_worker.running`; on the base helper both failed (`assert not True`, `PostAttemptWorker.running`), 11 passed.

## What I ran

All through the scratch wrapper (`env -i`, empty `HOME`, `CODEX_HOME` and config dir, the shared uv and npm caches), npm and vitest in a `systemd-run --user --scope` of 5G, pytest from script files in a 3G scope at `-n 1`, one command at a time.

- `npm ci`, desktop and phone: exit 0 (install scripts not run, as npm reports by default here).
- Fail-first runs: as listed under each defect (each new test on the base code, by restoring the base's source files in the worktree for the run, then the fix).
- Final, at the tip (the record and ledger change no code):
  - desktop `npm run typecheck`: exit 0; `npx vitest run --maxWorkers=4`: Test Files 315 passed (315), Tests 3299 passed (3299); `npm run frontend:build`: exit 0, "✓ built in 3.16s".
  - phone `npm run typecheck`: exit 0; `npx vitest run --maxWorkers=4`: Test Files 42 passed (42), Tests 428 passed (428); `npm run build`: exit 0, "✓ built in 903ms".
  - `tests/test_mobile_v2_plan.py` five times in a row: 13 passed each (39.8 s, 40.8 s, 39.7 s, 40.4 s, 39.9 s).
  - `tests/test_ux_phase4_feedback.py`: 159 passed. `tests/test_reader_quick_check_failed.py`: in the runs below.
  - `scripts/affected_tests.py --files` the three changed Python sources: 1,327 files, so a name filter: every test file whose name contains today, session, guided_redo, quick_check, reading_progress, guide_plan, reader_guid, ingest_queue, ingest_job, post_attempt or ux_phase4 (27 files, `tests/test_first_questions_today.py` among them): 409 passed, 3 skipped; the affected files about the guide plan's readers (reader cues, RW3a/RW3b, mobile V4, the phone contract, the protection surfaces: 19 files): 434 passed, 1 failed (`test_reader_rw3b_switch_off.py`, a stage pin of the plan's keys: the always-sent key; fixed by `1c4b5c576f`); then every test file that reads the guide plan (29, plus the two pins' files, `test_sidecar_reader.py` and the phone's two): 861 passed. All at `-m "not arc_close"`.
  - each alone: `test_identity_pins.py` 345 passed (also after every source commit: no pin moved); `test_structure_ratchets.py` 3 passed (no number rose); `test_mobile_allowlist.py` 332 passed; `test_test_layout.py` 3 passed; `test_architecture.py` 18 passed; `test_effective_defaults_golden.py` 3 passed; `test_cli_help_snapshot.py` 26 passed; `test_kill_switches.py` 8 passed; `test_sqlite_file_copies.py` 1 passed.
  - `ruff check`: All checks passed! `lint-imports --no-cache`: Contracts: 43 kept, 0 broken. `scripts/check_gate_partition.py`: collected 31999: landing 31934 + arc_close 65.
- Not run: the whole pytest suite, the durability lane, the arc-close gate; the vault references (the landing regenerates them). No new TypeScript file: `desktop_validate.py`'s counts do not move.

## What a walk must check

The patient first-day persona (one web chapter, the live route, a fresh library), as firstq-9 and firstq-10, and the exam student for the quick check:

1. **UX-52** (firstq-10 #58, #78; firstq-9 #56, #101). Before any question is ready, Today keeps "Nothing planned for today." above the writing line, and **Keep going ↵**. Once "N questions from … are ready." shows: **no "Nothing planned for today."** anywhere on Today; the line's **Begin ↵** is the only control with ↵, the buttons read "Keep going · Something new · Done for today"; Enter opens a question. Back on Today after answering (the plan still empty): the same.
2. **UX-47** (firstq-7 #60-70), only where a topic fails while the others are written (it cannot be forced on the live route): with nothing ready yet, Today shows "◐ Writing questions from … · N of 8 topics done" with Continue reading and, under it, "Not every topic's questions could be written." with **no Try again**; it never says "Couldn't write the questions…" while the count still moves. If the writing ends with nothing written: "Couldn't write the questions from …" with **Try again**, and pressing it turns the line back to the writing line (a resume that does something).
3. **UX-48** (firstq-9 #93-96). A partly right answer, then "Redo the part you missed": "What to fix:" lists the ✗ (or ◐) lines the feedback showed, in the same words; **no sentence about eliciting, revealing or a "repaired trace"**. Note whether the lines are enough to know what to write.
4. **UX-49** (firstq-9 #97-102). Answer that redo right, then "Done for today": the session line reads "● … **(partly on your own, finished with help)**" for that topic, and "(on your own)" only for a topic answered fully right without help.
5. **UX-53** (student-3 #54-63, #96), only where a quick check's writing fails (an overloaded plan; it cannot be forced): within a few seconds of the failure the Reading guide says "Couldn't write a check for this section · Try again" (not "◐ writing a quick check…" for minutes); leave and reopen the Reader at that section: the same line, and nothing is written again until Try again is pressed; Try again shows "◐ writing a quick check for this section…".
6. UX-46 is not a walk matter.

## Not verified

- No app, browser, server or model ran; every screen state is from vitest on fake RPCs, every sidecar state from pytest on fixture vaults. WebKitGTK rendering, the polite regions and the real timing of a failed topic or check are not seen.
- UX-47 relies on the label rule the progress record already uses (`stillWriting`: an entry belongs to a section still being written when its label is a writing label or starts with one and ": "); its known limit stands (`ux-first-questions-progress.md`, "Not verified").
- UX-49: "finished" means an answer with help that earned points after the last credited own answer; a topic whose own credited answers were all partly right and whose help came only before them stays "(on your own)". The session diff decides which answers earned credit (unchanged); a held answer is skipped as before.
- UX-48: a redo opened from the probe block review (or any screen without the feedback's rubric lines) shows no "What to fix" line; the rationale is still sent by the sidecar (unused by the redo now) and still shown in the places of UX-48b.
- UX-53: a failed batch requeued from elsewhere (the Library's Activity resume) while the Reader shows the failure: the next plan read no longer lists it, so the guide says "Keep reading at your own pace." rather than the writing line until the Reader is reopened (the poll has stopped by then). A provider that is unavailable before anything is queued is still the author call's silent refusal (unchanged, not this defect).
- UX-46: the race is shown with a test-only delay, not reproduced under real load; the fix removes the slots' threads from these journeys rather than waiting for them.
