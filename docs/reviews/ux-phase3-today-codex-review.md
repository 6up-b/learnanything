# UX Phase 3 (Today): Codex review, fix round 1

**Stage:** ux-phase3-today, branch `ux/phase3-today`, worktree `learnanything-ad1`, base `e9d4de1aa`.
**Review:** Codex job `20261025-022429-GJcOzo` (6 findings: 1 High, 5 Medium). The stage record is `docs/reviews/ux-phase3.md`; the reviewer looked for `ux-phase3-today.md`, which does not exist.
**This round:** each finding was reproduced first with a test that fails on the pre-fix code (checked by swapping the pre-fix file back in and running the test), then fixed. Nothing was rejected. No schema, migration, successor, config key, model call or new parameter was added.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | An implicit session start can cross a vault switch | fixed | `UX Phase 3 fix round 1 WIP: implicit sessions bound to the vault (F1)…` and the App-tests commit | `App.today.test.tsx` "fix round 1, F1" (3 tests: minutes still being read during the switch; `start_session` answering after the switch; B's first action starts its own session). `TodayPlace.test.tsx` "fix round 1, F1" (Begin's start answering after Today unmounted). All 4 failed before the fix. |
| F2 | Medium | Enter activates Begin instead of the focused secondary action | fixed | `…Today's keys, list minutes, count-free captures, list read failures (F2, F4, F5, F6)…` | `TodayPlace.test.tsx` "fix round 1, F2": a keydown on the focused why?, skip, resume ▸, Something new, and the full list's why? and back button. Each control keeps the event (not prevented) and no Begin, Keep going or pick runs. Enter on the page itself still begins. 3 of the 4 failed before the fix; the page-Enter test is the control case. |
| F3 | Medium | Resuming a problem loses its extraction identity | fixed | WIP commit 1 (F1, F3) and the App-tests commit | `readerWorkbenchResume.test.tsx`: an E1 problem with the book open on E2 asks the server nothing, forgets the request and says why (failed before the fix). On E1 itself it resumes with `extractionId: E1`. `test_ux_phase3_today.py::test_a_problem_on_an_earlier_reading_of_its_book_is_not_a_thread` (failed with the filter disabled), `::test_the_current_reading_is_the_one_the_reader_opens_a_source_on`. `App.today.test.tsx` threads: the Reader gets `reading` and the resume request gets `extractionId` (both failed before the fix). |
| F4 | Medium | With the plan disabled, a full-list pick ignores the selected minutes | fixed | F2/F4/F5/F6 commit | `TodayPlace.test.tsx` "fix round 1, F4": 40m chosen, then a pick from the list gives `start_session(40)`, then the question opens; with a session open, no start. This failed before the fix. `App.today.test.tsx` "fix round 1, F4" checks the same at App level: Practice opens in the new session and `start_session` runs once with 40. |
| F5 | Medium | Expanding captures brings back the forbidden waiting counts | fixed | F2/F4/F5/F6 commit | `TodayPlace.test.tsx` "fix round 1, F5" with the real `InboxStrip` and nonzero counts (3 new, 2 pending deletions): no "Inbox · 3", no "pending for 2", and every action stays (failed before the fix). Classic's strip still shows "Inbox · 3" and "pending for 2 purged captures". |
| F6 | Medium | A failed full-list read leaves a blank view with no way to recover | fixed | F2/F4/F5/F6 commit | `TodayPlace.test.tsx` "fix round 1, F6": a failed first read shows the reason and Try again, which reads the list again; a failed refresh keeps the rows, says they may be out of date and offers Try again; the first read shows a quiet loading frame. All 3 failed before the fix. |

### What changed

- **F1.** `App.tsx` adds `vaultGenRef`. `changeVault` bumps it and drops the pending `implicitStartRef` before the selection is sent: the sidecar pipe is serialized, so anything the old start sends after that point would reach the new vault. `implicitSession()` checks the generation after each await. Across a change it starts nothing, installs nothing, reports nothing and answers null. The `finally` clears the shared start only if it is still its own. Every implicit caller goes through `withImplicitSession(action)`, which runs the action only while the vault is unchanged. `pickCheckMe` takes a `stillOpen` and checks it after each request (implicit path only). `startQuickCheck` checks after the implicit start and after its RPC (implicit path only), and `openPassageNow` checks after its library read. Today's own Begin is also covered: `TodayPlace` is keyed on the vault and unmounts on a switch. Its `run` now marks each step with `stay()`, so after unmounting no follow-up request is sent with the old vault's session (`next_plan_item`, `plan_learner_pick`, `get_today_queue`), nothing is handed to the shell and no error appears. Classic's paths are unchanged, and the classicIsBase gate test now counts `withImplicitSession(` call sites.
- **F2.** `TodayPlace`'s page listener and the full list's listener leave Enter alone when it is aimed at an interactive element (`INTERACTIVE_SELECTOR` from `app/keymap.ts`), so the focused control activates natively. The other keys (l, ?, d, arrows, j/k, p) are unchanged.
- **F3.** Every thread's passage now carries its reading. `onOpenPassage(sourceId, spanId, reading)` gets `ReaderOpenSource.reading`, which the Reader's first open passes as `jumpReading`, so a span from another reading is translated through `reader.saved_place` and never taken as a span of the open reading. The resume request carries `extractionId`. `useReaderWorkbench` resumes only on that reading; on another reading it forgets the request and says *"This problem was started on an earlier reading of this book, so it can't be reopened on this one."* Server side, `workbench.open_problems` leaves out problems that are not on their source's current reading (`resolve_extraction_id(source_id)`, as `reader.render_view` resolves it). The Reader cannot reopen such a problem, and its own ✎ marks list only the open reading's problems, so Today no longer offers a resume it cannot keep. A validated re-anchoring flow for problems from earlier readings would be new behaviour; it is left as an open question below.
- **F4.** `openFromList` with the plan off and no session first starts the session with the minutes Today shows (chosen or remembered), as Begin does, and then opens the question. The shell's implicit start sees that session through `sessionRef` and starts no second one.
- **F5.** `InboxStrip` takes `countFree` (the learner's rendering): its heading is *New captures* and the pending-deletion line is *still pending for these purged captures*, with every row and action kept. Only Today passes it, and classic's strip renders exactly as before (new classicIsBase manifest entry).
- **F6.** `PlainList` shows a quiet loading frame on the first read. When a read fails it shows *Couldn't read today's list · Try again*, or when a refresh of rows already shown fails, *Couldn't refresh today's list; what's below may be out of date · Try again*. Try again uses the query's self-contained `retryReport()` retry.

### The other claims Codex disputed

- **"T4, as §11 measures it"** overstated the evidence. That claim is corrected: the section in `ux-phase3.md` is now "T4's frontend dispatch (not T4 itself)" and the test header says the same. T4 proper is still the usability walk (the record's open question 3).
- **"No count of waiting things anywhere"**, **"same arguments / remembered minutes"**, **"unfinished problems resume in their book"** and **"the key guard preserves control behaviour"** now hold, through F5, F4, F3 and F2.
- **Spec conformance** notes not raised as findings, left for the owner: three threads *plus* the wrap-up can appear, the backdrop move is deferred (already open question 1), and full-list estimates appear only for items in plan blocks.

### Open questions (new this round)

1. **Problems left on an earlier reading.** They no longer appear in Today, and the Reader never showed them. Bringing them back means re-anchoring the problem's spans onto the new reading through `span_aliases`, as is done for saved places. That changes a workbench session's persisted extraction, so it needs its own stage.
2. **Three threads plus the wrap-up.** Should the wrap-up count as one of the three (§7.1 "at most three, then more")? Recommended default: it does not count; it is the shell's armed offer, not a thread.

## Gate (fix round 1)

All test commands ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- …`, one at a time.

| command | result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **35 kept, 0 broken** |
| `uv run pytest -n 6` on `tests/test_ux_phase3_today.py`, `test_reader_workbench_rw2a.py`, `test_workbench_assistance.py`, `test_workbench_check.py`, `test_reader_rw2b_fix10.py`, `test_reader_rw2b_fix5.py`, `test_reader_rw2b_review.py`, `test_reader_rw4b_admission_idempotency.py`, `test_reader_rw4b_fix6.py`, `test_rw2c_fix_round3.py`, `test_architecture.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py` | **469 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npx vitest run --maxWorkers=4` on every test file that touches App, ReaderScreen, useReaderWorkbench, InboxStrip or TodayPlace (67 files, found with grep), plus `app/keymap.test.ts` and `app/todayPlan.test.ts` | **69 files, 524 passed** |
| `npx vitest run --maxWorkers=4 src/app/App.today.test.tsx` (rerun after a typing-only test edit) | **14 passed** |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed this round |
| durability tests, DB reference scripts | not run: no migration, DB or connection code, and no schema change |

The vitest files: `app/App.fixRound2/3/4/5.test.tsx`, `App.shell.test.tsx`, `App.today.test.tsx`, `App.wrapUpSkim.test.tsx`, `classicIsBase.test.ts`, `shellChrome.test.ts`, `keymap.test.ts`, `todayPlan.test.ts`, `components/InboxStrip.test.tsx`, `screens/attentionBudget.test.tsx`, `screens/TodayScreen.plan.test.tsx`, `screens/today/TodayPlace.test.tsx`, `screens/workbench/switchOff.test.tsx`, every `screens/ReaderScreen.*.test.tsx` (22 files), and the `screens/reader/*` files that mount the Reader or the workbench hook (31 files, including `readerWorkbenchResume`, `readerWorkbenchExercise`, `readerWorkbenchQueue`, `readerHooks.parity`, `figures/*`).

Not run here, by the owner's rule (2026-10-17): the full pytest suite, the whole durability lane and the whole vitest run. They run once, in the landing gate on the merged tree.

---

# Re-review: fix round 2

**Review:** Codex job `20261025-024425-llEFP5`. It confirmed F2, F4, F5 and F6 fixed, reopened F1 and F3, and raised F7 (Medium).
**This round:** F1 and F7 were reproduced first in `App.today.test.tsx`: 2 F1 tests and 2 F7 tests failed on the round-1 code. Both were then fixed with one change. F3 is rejected for this stage; the reason is below. No schema, migration, successor, config key, model call, backend code or new parameter was added. The change adds two counters to App and no tuning constant.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A start pressed during a vault change can reach the new vault (reopened) | fixed | `b81f5d14d` | `App.today.test.tsx` "fix round 2, F1". (a) A Reader check pressed on A while B's selection is held, with its minutes answering after B has loaded: `start_session` and `plan_learner_pick` are never called, and no error is shown. (b) Begin pressed on A's Today while B is being selected starts nothing, and nothing is served. (c) The control case: once B has loaded, B's check starts its own session. (a) and (b) failed before the fix: each called `start_session({availableMinutes: 25})`. |
| F2 | Medium | Enter activates Begin instead of the focused control | confirmed fixed (round 1) | `b927425c4` | (Codex confirmed) |
| F3 | Medium | Resuming a problem from an earlier reading of its book (reopened) | rejected (out of stage scope; open question kept) | n/a | See *F3* below. |
| F4 | Medium | A full-list pick with the plan off ignores the selected minutes | confirmed fixed (round 1) | `b927425c4` | (Codex confirmed) |
| F5 | Medium | Expanding captures shows waiting counts | confirmed fixed (round 1) | `b927425c4` | (Codex confirmed) |
| F6 | Medium | A failed full-list read leaves a blank view | confirmed fixed (round 1) | `b927425c4` | (Codex confirmed) |
| F7 | Medium | Leaving Today on the same vault discards the session Begin started | fixed | `b81f5d14d` | `App.today.test.tsx` "fix round 2, F7". Begin, then Reader, while `start_session` is pending; then it answers. The Reader stays on screen, Begin's serve is not sent from the unmounted Today, and the Reader's check uses `s_new` with exactly one `start_session`. The plan-off case is tested the same way (40 minutes chosen). Both failed before the fix with 2 starts. `TodayPlace.test.tsx` "fix round 2" covers the unit side: Begin asks the shell's start for the plan's minutes, and a start the shell refuses (null) stops quietly, with no RPC, no hand-off and no error. |

### What changed

- **The shell owns session starts (F1, F7).** `App.startSessionHere(minutes)` is now the only session start in the simple shell. It serves Today's Begin, Begin with the plan off, the full list's picks (TodayPlace's new required `onStartSession` prop) and the implicit start.
  - It sends nothing while a vault change is under way.
  - It captures the vault generation when it is called. If the generation has moved by the time the answer arrives, it installs nothing and answers null.
  - On the same vault it installs the session in App at once (`sessionRef`, `setSession`, notices resolved), before the caller's next step. It does not navigate: TodayPlace's `onBeginSession` still decides where the learner lands, and it only runs while Today is mounted.
  - So when the learner leaves Today on the same vault, the session survives, the obsolete navigation and the first-step serve are suppressed, and a later Reader check starts no second session. TodayPlace treats a null answer like its unmount: it stops quietly.
- **No start during a vault change (F1).** `changeVault` raises `vaultChangesRef` (a counter, so overlapping calls nest) and moves the generation before the selection is sent. In a `finally`, after the replacement vault has loaded or the change has failed, it moves the generation again and lowers the counter.
  - While the counter is raised, `implicitSession()`, `withImplicitSession()` and `startSessionHere()` start nothing.
  - Because the generation moves again at the end, anything asked during the change cannot act afterwards. That includes an action whose minutes read answers late.
  - Classic's StartScreen and TodayScreen keep their own starts unchanged. The classicIsBase gate passes.

### F3: rejected for this stage

The reviewer asks that a problem worked on an earlier reading of its book (E1, with the book now on E2) either open its original extraction or be re-anchored onto E2 through a validated flow. Neither exists in the product today, and neither is UX Phase 3's to add:

- **Today mirrors the Reader.** The UX spec §7.1 says Today's threads "come from the Reader doc". The Reader opens a book only on its current reading (`reader.render_view` resolves through `resolve_extraction_id`). Its own ✎ marks list only the open reading's problems. The workbench spec defines resume as "the same steps, the same anchor, the same book visibility" (`ux_reader_workbench_v1.md` resume rule), with no cross-reading case. So the Reader cannot resume an E1 problem from anywhere, Today included. Round 1 made Today consistent and honest about this: it offers no resume it cannot keep, and a stale request is refused with a sentence that says why.
- **Implementing either option would be new reader/workbench behaviour, not a Today surface.** Rendering a superseded extraction is a Reader feature. Re-anchoring would rewrite a workbench session's persisted `extraction_id` and `span_ids_json` through `span_aliases`, which needs validation of each step's anchors. Both belong in the Reader workbench (RW) track, in a stage with its own spec text and tests.
- The open question from round 1 stands: *Problems left on an earlier reading*, with the recommended follow-up being an RW stage for span-alias re-anchoring of open workbench sessions.

## Gate (fix round 2)

All test commands ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- …`, one at a time.

| command | result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **35 kept, 0 broken** |
| `uv run pytest -n 6 tests/test_ux_phase3_today.py` (the stage's backend read, unchanged this round, run for F3's evidence) | **5 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npx vitest run --maxWorkers=4` on the 17 files listed below | **17 files, 181 passed** |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| durability tests, DB reference scripts | not run: no migration, DB or connection code, and no schema change |
| contract tests (desktop RPC, mobile allowlist, CLI help, config defaults) | not run: no RPC, config key or Python changed this round |

Before the fix, `npx vitest run src/app/App.today.test.tsx -t "fix round 2"` showed 4 failures (F1 a and b, both F7 tests). The F1 control case also failed, but only because test (b) stopped before releasing its held selection.

The vitest files are every test file that mounts App or TodayPlace, or that pins App's or Today's source (found with `git grep`), plus their neighbours from round 1: `app/App.fixRound2/3/4/5.test.tsx`, `App.shell.test.tsx`, `App.today.test.tsx`, `App.wrapUpSkim.test.tsx`, `classicIsBase.test.ts`, `keymap.test.ts`, `todayPlan.test.ts`, `shellChrome.test.ts`, `screens/reader/readerWorkbenchQueue.test.tsx`, `screens/reader/readerWorkbenchResume.test.tsx`, `screens/today/TodayPlace.test.tsx`, `screens/attentionBudget.test.tsx`, `screens/TodayScreen.plan.test.tsx` and `components/InboxStrip.test.tsx`.

Not run here, by the owner's rule (2026-10-17): the full pytest suite, the whole durability lane and the whole vitest run. They run once, in the landing gate on the merged tree.
