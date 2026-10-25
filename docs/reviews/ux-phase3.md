# UX Phase 3: Today

**Stage:** `ux-phase3-today`, branch `ux/phase3-today` (worktree `learnanything-ad1`), base `e9d4de1aa` (main: T1, AD2+AD3 mvp-0.30, RW2d mvp-0.31, local retrieval P1, migration head 220).
**Spec:** `docs/specs/ux_learnloop_v1.md` §7.1 (Today, wireframe W4), §4.2 rules 9 and 10, §4.3, §10 Phase 3 (items 3.1–3.4), the findings Phase 1's usability rounds deferred to Phase 3 (§10 "Deferred", row 3), and §11 T4.
**Owner direction:** owner-queued; UX3 starts after T1 landed (it has). Frictionless by default, the glass box on demand; a live change behind the existing kill switch (`[ui] shell`), no shadow stage.
**No paid or live calls** were made in this stage (fakes only; no manual runs needed).

## 0. The plan

**The rule of the stage.** Display and navigation, on the UX2 simple shell only. No change to what is served: plan selection, scheduling, scoring, the plan's split and its blocks are the sidecar's, unchanged. Begin, the minutes, keep going, something new, skip and a pick from the full list call exactly the RPCs classic's Start and Today call, with the same arguments. **No algorithm successor**, no migration, no config key. `ui.shell = "classic"` keeps `StartScreen` and `TodayScreen` byte for byte (they are not edited).

**3.1 Start merged into Today.** A new `screens/today/TodayPlace.tsx`, mounted by `app/App.tsx` for the simple shell's Today (tab `start`, and tab `today` outside practice, feedback and a block review). One plan sentence in minutes, the blocks as *about N min* rows, Begin ↵, the minutes chips, the streak in the footer. Gone from the simple shell: *scheduler mode*, the *due now · probe queue · later today · follow-ups* tiles, the queue counts, the `11 concepts…` fallback, the backdrop and its `backdrop:` chip, the split line with lane names, the hero status grid, *Why this position*, the ranking formula, the algorithm version, ClaimSurface, `e` without confirmation, the session counter.
**3.2 Implicit sessions.** The first practice action with no session open starts one with the remembered minutes and carries on. No "Start a session first" notice in the simple shell.
**3.3 Threads.** Open questions (open in the Reader at the passage), unfinished workbench problems (resume in their book), the wrap-up the shell armed. No counts; at most three, then *more ▸*. The inbox shows one line only when there are captures.
**3.4 The goal card.** Plain words, *Practise for this goal*, *Practice exam*; GoalBanner's numbers behind *details ▸*.

## 1. What was built

| Commit | What |
|---|---|
| `ed0834a53` | `workbench.open_problems` (the one backend addition, §2). |
| `c7e2a82bd` | `TodayPlace`, `app/todayPlan.ts`, `components/GoalCard.tsx`, implicit sessions and the thread handlers in `App.tsx`, the workbench resume request; the six App-level test files follow Today into `TodayPlace`. |
| `ef0107313` | `TodayPlace.test.tsx`, `todayPlan.test.ts`, `App.today.test.tsx` (implicit sessions, T4, threads), `readerWorkbenchResume.test.tsx`, classicIsBase's UX3 manifest. |
| (this record) | `docs/reviews/ux-phase3.md`. |

### 1.1 Today (`screens/today/TodayPlace.tsx`, `app/todayPlan.ts`)

W4, as built:

```
Tuesday evening                                     10m  15m [25m] 40m  60m
25 minutes today: finish §5.4 Mixtures, then 2 short questions from earlier
days and a fix for a mix-up.                                        why? ▸
┌──────────────────────────────────────────────────────────────────────────┐
│ ▸ Continue §5.4 Mixtures                                  skip  about 12 min │
│   2 short questions · Eigenvalues                              about 7 min │
│   Fix a mix-up · Conditional probability                       about 4 min │
└──────────────────────────────────────────────────────────────────────────┘
                                                               [ Begin ↵ ]
Probability midterm · Nov 14 · on track
[Practise for this goal] [Practice exam]  details ▸
Pick up a thread
 ✎ Exercise 5.9: show that … — 3 steps written                    resume ▸
 ? “Why is the density of a sum a convolution?” · §5.4       open in book ▸
 Reading wrap-up ready — under a minute ▸
New captures ▸
─────────────────────────────────────────────────────────────────────────────
4 days · best 9                                        all of today's list (l)
```

- **The sentence** is composed from the plan DTO's blocks and projection only (gate G3: nothing estimated or summed on the client). Each lane is named by what it does: maintain → *N short questions from earlier days*, repair → *a fix for a mix-up*, new → *new: {topic}*, push → *a step further on {topic}*, a learner pick → *your pick, {topic}*, a reading block → *read / finish {section}*. Once the plan has begun it says *About N minutes left today: …*. Lane names never appear on the surface.
- **Rows:** the current block (▸, with a quiet *skip*, which ends a reading block or skips the next question exactly as the plan view's skip), the chosen blocks after it, then the projection. A block holding a follow-up says *· on your own*.
- **why? ▸** (and `?`): the split in words (*about 13 min for keeping what you know (maintain: …)*), each block's own reason with its receipts under *details ▸*, the re-entry's account, and the knowledge headline (it carries counts and a percentage, so it is behind *details ▸*, rule 9).
- **Re-entry** replaces the sentence: *Welcome back. A short catch-up today: 12 minutes of the most useful questions. Nothing else is waiting on you.* The old panel's *Still solid: N. Slipped below target: M (names)* is gone from the surface; *why?* says how long the learner was away and what the catch-up starts with.
- **Begin ↵** with no session: `start_session(minutes = the plan's budget)` then `next_plan_item(serve)`, handed to the shell's `beginSession` (Start's begin, exactly). With a session: `next_plan_item(serve)`; a question opens Practice, a reading step the Reader with the plan banner.
- **The minutes** (chips, ←/→): `set_plan_minutes`, as Start and the plan view.
- **States:** first run with no books (*Nothing to plan yet. Add a book, paper or lecture and LearnLoop will plan your days around it.* + Add, never *Nothing due today*); day one (*15 minutes today: read Chapter 1.*); waiting (*Nothing to do right now. Back in 9 min: …*, no Begin); done (*Done for today · 26 minutes.*, Keep going ↵, Something new with its trade-off in minutes, Done for today, which stops the plan and ends the session as the plan view's *done*); loading (the frame and a dim ellipsis, never *Loading today's queue*); error (*Couldn't plan today · Try again*, which reads the plan again).
- **The plan switched off** (`plan.enabled = false`, its own kill switch): *15 minutes today: starting with {topic}.* and Begin, which opens a session for those minutes and its queue's first question (classic Start then Today's Enter). No tiles, no counts here either.
- **The full list (`l`)** is a plain list: titles, *about N min* where the plan estimates the item, and why it is there in a few words (*time to bring it back*, *on your own · no hints* with a *why?* in the Reader doc's cold wording, *after a fix, once more*, …). No ids, mode slugs, mastery or priorities. `j/k` move, Enter opens, `p`/Esc go back. Opening one while the plan serves is a learner pick (`plan_learner_pick`), and with no session it begins the plan with that pick, exactly as Today's list did.
- **Keys:** one window listener, `screenLeavesKey` first (and the full list's own listener likewise). Enter, `l`, `?`, ←/→, `d` when done.

### 1.2 Implicit sessions (`app/App.tsx`)

`implicitSession()` starts one session with `implicitSessionMinutes()` (the plan's budget while the plan serves, as Begin uses; else the start summary's remembered minutes; if neither can be read, nothing starts and one error says so). One start at a time: a second action waits for the same one. The shell's `sessionRef` knows the session ahead of the render, so a continuation never starts a second. Simple-shell call sites: `openPractice`, `openPrimedRetry`, `openGuidedRedo`, `checkMeFromReader`, `exerciseFromReader`, `startQuickCheck` and the repair overlay's *practise*. Classic keeps every `needSession(...)` path unchanged (pinned in classicIsBase). Starting a session is the session the learner's Begin would have opened; what is then served is what that action served before.

### 1.3 Threads and the goal card

- Open questions come from `list_question_queue` (open only). A question with a passage opens the Reader at it (`open in book ▸`); one without continues in Ask (`continue ▸`, `targetForDialogue`).
- Unfinished problems come from the new `workbench.open_problems`. `resume ▸` opens the problem's book at its first span and hands the Reader workbench a resume request (`resumeProblem`, consumed by identity like a check or an exercise), which asks RW2a's one explicit resume once that book is open.
- The wrap-up line is RW6a's, armed by the shell for one view, unchanged; it sits with the threads.
- Captures: one line, *New captures ▸*, only when the inbox has something; it opens the existing inbox strip.
- The goal card (`components/GoalCard.tsx`): *Probability midterm · Nov 14 · on track* (standing from GoalBanner's own `statusOf`, now exported, mapped to *on track / getting there / needs more practice*), *Practise for this goal* (the first goal-frontier question of today's list, as a learner pick), *Practice exam* only when its pool is ready, and the whole GoalBanner under *details ▸*.

## 2. The backend addition, and why there is no successor

`workbench.open_problems` (desktop only; Rust passthrough, `main.rs`, `client.ts`, DTO; mobile allowlist pins it desktop-only): every source's **open** problems, newest first, each with the source it opens in. A pure read (`store.open_sessions` + RW2a's `_summary`; problems whose statement is held out now, or whose source cannot be found, are left out; switched off it refuses with `workbench_disabled` like every workbench RPC). The spec needs threads with unfinished work across books (§7.1, 3.3) and no existing read listed them across sources (`workbench.for_source` needs an extraction id, which library cards do not carry). Nothing about serving, grading, evidence, replay or the plan reads it: **no successor**, no migration, no config key, no reference regeneration.

## 3. Decisions and deviations

- **Captures without a number.** §7.1 sketches *2 new captures ▸*; the task's rule 10 says no count of waiting things anywhere. The line says *New captures ▸*.
- **The backdrop.** 3.1 says the backdrop moves to Settings → Appearance. The simple Today has no backdrop at all (W4 has none), so there is nothing for that setting to choose yet; classic Start keeps it. Left for Phase 6 (open question 1).
- **"6 short questions"** is the plan's own item count for a block (W4 shows it); it counts what the plan will do, not things waiting.
- **No made-up constants.** No model or decision parameter was added. `THREADS_SHOWN = 3` is the spec's layout bound; the day-part words are calendar convention; the standing words reuse GoalBanner's existing thresholds; the plan re-read cadence while a block is being chosen is TodayScreen's own. No config key, so nothing to classify in `parameter_registry.py`.
- **classicIsBase.** UX2's `BASE` and `UX2_LANDED` do not move. A UX3 manifest (`UX3_CHANGES`) lists the four files UX3 changed under `screens/` and `components/` with their simple-shell gates; UX3's files are found by its own commits (subjects starting "UX Phase 3") after `e9d4de1aa`, so a later landing needs no move. A second check pins classic's session-first notices and its two screens in `App.tsx`, and that every `implicitSession()` call sits in a simple-shell branch.
- **App tests.** The UX2 App-level tests that drove the real Start and Today in the simple shell (fix rounds 2, 4 and 5) now drive `TodayPlace` (the same chrome-isolation sweeps; the numbered-key pick became the plain list's `j`/Enter, as Today has no numbered keys now); the stub-based ones (shell, fix rounds 2 and 3) accept either stub at launch and expect `TodayPlace` on Alt+1.
- **Kept working:** AD2+AD3's *why this item* and DL2's intent controls and *Check once* live on the practice screen and in the Reader, which are not changed; their vitest files pass (§4).

## 4. Gate

Memory-capped scopes throughout (`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`), pytest `-n 6`, vitest `--maxWorkers=4`, one run at a time.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 35 kept, 0 broken |
| pytest (targeted, `-n 6`): `test_ux_phase3_today`, `test_reader_workbench_rw2a`, `test_library_exercises`, `test_workbench_*` (16 files), `test_reader_rw4b_admission_idempotency`, `test_reader_rw4b_fix6`, `test_reader_recap`, `test_reader_wrap_up`, `test_field_workbench_signals`, `test_rw4_kill_switches`, `test_architecture`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_sqlite_file_copies` | **650 passed** |
| `pytest --durable-sqlite tests/test_ux_phase3_today.py` (production pragmas on the new read) | 3 passed (no durability-marked tests in the workbench files: 71 deselected) |
| `npm install`; `npm run typecheck` | ok, 0 errors |
| vitest (Today, shell, keys, notices, plan, practice and workbench): `app/App.today`, `App.shell`, `App.fixRound2–5`, `App.wrapUpSkim`, `classicIsBase`, `todayPlan`, `dailyPlan`, `intentCheck`, `keymap`, `autoAdvance`, `notices`, `notices.shell`, `practiceOffer`, `readerCheck`, `readerWorkbench`, `shellChrome`, `shell`; `screens/today/*` (TodayPlace, DailyPlanView, reentry); `StartScreen`, `TodayScreen.plan`, `PracticeScreen.intentCheck`, `practice/WhyThisItem`, `reader/readerWorkbenchExercise`, `readerWorkbenchQueue`, `readerWorkbenchResume`, `ReaderScreen.workbench`; `copy/*` (deny-lists) | **34 files, 334 passed** |
| vitest, every Reader file (`screens/ReaderScreen*`, `screens/reader/*`; `useReaderWorkbench` changed) | **85 files, 787 passed** |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| DB reference scripts | not run: no schema change |

Not run here, by the owner's rule (2026-10-17): the full pytest suite, the whole durability lane and the whole vitest run; they run once in the landing gate on the merged tree.

### T4's frontend dispatch (not T4 itself)

Corrected in fix round 1 (`docs/reviews/ux-phase3-today-codex-review.md`): this is not T4 as §11 measures it. Tomorrow's plan is a mock and Practice a stub, so the test checks what the shell shows and sends on the next day's launch, not real next-day planning or unaided usability; T4 proper is the usability walk in open question 3.

`app/App.today.test.tsx`, "T4: it's tomorrow…": the App launched on the next day (system time advanced), no session, the day's plan. Today opens on the plan sentence in minutes; no dialog and no required choice; no count of waiting things, no lane names, no deny-list term; the streak in the footer. **One key (Enter) from launch to the first question**: `start_session(25)`, `next_plan_item(serve)`, Practice on the plan's first item in the new session, and no session-first notice. The re-entry variant (after nine days away): the welcome-back sentence, nothing about what slipped on the surface, and Enter starts the 12-minute catch-up.

## 5. Open questions for the owner

1. **The backdrop in the simple shell.** 3.1 moves the backdrop cycler to Settings → Appearance; the simple Today (W4) has no backdrop to choose. Recommended default: leave it to Phase 6 (Settings), where an *Appearance* choice could bring a quiet backdrop back to Today if wanted; classic Start keeps it meanwhile.
2. **Captures count.** §7.1's *2 new captures ▸* conflicts with rule 10. Recommended default (built): no number.
3. **Usability look.** This stage verified Today with fakes and vitest only; a real-UI walk through the usability harness on a backup copy (as Phase 1 and 2 did), with the tester's T4, is still to do.
