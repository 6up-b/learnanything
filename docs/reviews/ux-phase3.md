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

## Landing onto main

Landed in `learnanything-merge2` on `merge/ux3-onto-main`, cut from main `e9d4de1aa` (the local retrieval P1 landing:
`mvp-0.31`, migration head 220), which is also the stage's base: main had not moved. The stage tip is `71c19ac58`.
Orchestrator rulings under the owner's proportionate bar: Codex confirmed F1 (High), F2, F4, F5 and F6 fixed; **F7**
(Medium, reopened) is fixed here; **F3** (Medium, reopened) is non-blocking and recorded as a Low follow-up; the open
questions take their recommended defaults. **No algorithm successor, no migration, no config key.** Main was neither
fast-forwarded nor pushed.

### Commits and conflicts

- `19f74ffd0`: the `--no-ff` merge of `ux/phase3-today`. **No conflict** (main is the stage's base). All four RPC
  bridge layers of `workbench.open_problems` are on the merged tree (the Python handler, the Rust passthrough in
  `commands.rs`, `main.rs`, `client.ts`) with its desktop-only mobile allowlist entry.
- `102832cad`: the F7 fix (below). **The gate head for the Python lanes.**
- `2c2247de7`: a landing fix found by the whole vitest run (below; test-only).
- This record (docs only).

### The F7 fix (`102832cad`)

Today's Begin and an implicit start (a Reader *check me* pressed while its minutes read is pending) each issued their
own `start_session`, so in a narrow race the backend closed the first, seconds-old session.
- `App.startSessionHere` now keeps the one start in flight in `pendingStartRef`; a caller that arrives while it is
  pending gets that start's session (the learner has one session; the second caller's minutes are moot). It is still
  bound to the vault: nothing starts while a vault change is under way, a start whose vault changed installs nothing
  and answers null, and `changeVault` drops the pending start alongside `implicitStartRef`.
- `implicitSession()` re-checks the installed session after its awaited minutes read and carries on in it.
- **Fail-first tests** in `App.today.test.tsx`, "landing, F7": Begin held, Alt+3 to the Reader, *check me* with the
  minutes read held, then both released, in either order. Both failed before the fix (2 `start_session` calls) and
  pass after: exactly one `start_session`, and the check is picked in that session (`s_new`). The round-1 and round-2
  F1/F7 tests, `TodayPlace.test.tsx` and `classicIsBase.test.ts` pass unchanged.

### Landing fix (`2c2247de7`)

`screens/retryWiring.test.tsx` lists every non-test file that uses a query's `retryReport()` or
`useReportQueryError(`; the whole vitest run failed because `TodayPlace.tsx` (fix round 1, F6) now uses
`retryReport()`. Its retry is the full list's own in-place *Try again*, handed to no shell error, and its F6 tests
check that Try again reads the list again (after a failed first read and after a failed refresh). The manifest now
names it, with a comment saying why; the second check (no retry built from a hook's `refetch`) is unchanged and passes.
The stage's own gate ran a selected vitest subset, which did not include this file.

### Regeneration (nothing changed, nothing committed)

- **References.** `db_generate_reference.py` rewrote 422 notes, and every changed line was `source_commit` /
  `source_commit_timestamp` provenance; discarded. `db_validate_reference.py`: **0 errors** (351 table notes).
- **CLI help snapshot, RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist): their tests pass with
  no file changed (319 passed with `test_ux_phase3_today`, `test_plan_determinism`, `test_ad23_successor`,
  `test_architecture`).
- **Defaults snapshots.** All **22** recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared,
  `-B`, `env -i`): **0 mismatches**.
- **`validate_vault.py`**: passes (1,154 notes, 1,152/1,152 reachable).
- **Failing before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **1,189** issues (as at the local
  retrieval P1 landing: this stage adds no module).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0) in 5G scopes; `TMPDIR` = merge2's
`fixtures-local/tmp`. pytest lanes in 10G / 2G swap scopes at `-n 8` under `flock /tmp/learnloop-fullsuite.lock`;
everything else in 5G / 1G scopes. Python runs outside pytest used `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. Logs: `fixtures-local/ux3-landing/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **35 kept**, 0 broken |
| full suite (`pytest -n 8`, at `102832cad`, 60 min 42 s) | **22,453 passed**, 2 failed, 3 skipped, 38 xfailed |
| the 2 failures, alone, 3 times | `test_plan_first_transport_offer_grants::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter` and `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`: **2 passed** each time (45 s). Both are known load flakes (TE0 and S0 were running in parallel), in code this stage does not touch |
| durability (`-m durability`) | **122 passed** |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | first run: 1 failed (`retryWiring.test.tsx`, fixed in `2c2247de7`); then **210 files, 1,822 tests passed** (main: 206 files, 1,738) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean apart from `fixtures-local/`; the diff against main under `fixtures/linear_algebra`, `fixtures/probability`, `fixtures/arxiv_v2` and the root `.gitignore` is empty; no non-empty `-wal` beside a fixture |

### Parity (backup-API copies; no model call)

**Setup.** Scripts in `fixtures-local/landing-ux3/scripts/` (the local retrieval P1 landing's, re-pathed; new:
`ab_ux3.sh`, `c_ux3.sh`, `ux3_run.py`, `c_repeat.sh`, `plan_repeat.sh`, `E`).
- **Copies.** The owner's backups `fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`
  (`mvp-0.30`, schema 220) were each copied once with `copy_tree_with_databases` into `landing-ux3/orig/`; every other
  copy came from those through the same helper. **Not opened:** the main checkout's `fixtures/linear_algebra`,
  `fixtures/probability` and `fixtures/arxiv_v2`.
- **Code.** Main's is `git archive e9d4de1aa`, the merge's `git archive 102832cad`, each first on `sys.path`. The audit
  hook (every process start and every socket connection logged, Codex processes and non-loopback connections
  refused) **logged nothing**: no process start, no connection.
- **Environment and routes.** `env -i` with empty `HOME` / `CODEX_HOME` / `LEARNLOOP_CONFIG_DIR` (still empty
  afterwards). `neutralize3.py`: 60 route fields to `127.0.0.1:9` loopback profiles with unset keys (63 tasks resolved
  on both codes; only the disabled, keyless `embedding` profile is not a loopback), rewrite / rerank / dense /
  embeddings off, `build_on_serve` and outcome placement off. Clock frozen at 2026-10-19 09:00 UTC.

**(a) Main vs the merge, at `mvp-0.31`.**
- `upgrade --to mvp-0.31` plus `rebuild-derived-state` twice with main's code (`u31`) and with the merge's (`m31`):
  rc 0 on both vaults ("mvp-0.30 -> mvp-0.31"). `u31` opened by each code (`c31_main`, `c31_merge`): 0 migrations
  applied, head 220.
- **Schema:** identical on every pair (LA 1,503 objects, probability 1,502; none on one side only, no SQL differs).
  FK 0, integrity ok, journal WAL on all.
- **Rows** (356 tables; LA 18,301 rows, probability 8,208): `c31_main` vs `c31_merge` **identical, raw, row for row**
  (`schema_migrations` too). `u31` vs `m31` identical once the ids and timestamps each run mints are masked.
- **`rebuild --shadow`** (main on `u31`; the merge on `m31` and `c31_merge`): 0 / 0 / 0 (facet, mastery, schedule),
  live database unchanged, on both vaults. **`doctor`**: 0 differences (LA 57 issues / 1 error, probability 101 / 48).
- **Served reads at the frozen clock:** certification and curves (LA 129,651 bytes, probability 17,495) and the Today
  queue (no session, a session, greedy; LA 43 items, 528,665 bytes; probability 67, 741,269 bytes) are
  **byte-identical** on `c31_merge` and on `m31` against main's `c31_main`. The daily plan (read, serve, serve again,
  read) is identical except `card_hash`, `snapshot_hash` and the card hash inside `detail_json`; fresh copies run
  twice under each code (`plan_repeat.sh`) differ in exactly these three fields main vs main, merge vs merge and main
  vs merge (run-to-run noise, as at every landing since DL2). The first serve is the same item on every run.

**(b) The real sidecar** (stdio, `SystemClock` frozen; `ux3_run.py`), on fresh copies of `u31` under each code, in the
order a launch, Begin and the full list send them: `initialize`, `load_vault`, `get_daily_plan`, `get_start_summary`,
`goals_list`, `get_exam_status` (LA's goal), `get_today_headline`, `list_question_queue`, `workbench.open_problems`,
`get_inbox_summary`, `list_capture_inbox`, `get_review_counts`, `get_source_library`, `get_today_queue` (plan-off
minutes), `start_session` (the plan's minutes: LA 10, probability 15), `next_plan_item` (read, then serve),
`get_today_queue` (in the session), `get_daily_plan` (in the session), `get_practice_item` (the served step),
`plan_learner_pick` (another queued item), `workbench.open_problems` again, `shutdown`. Compared call by call with ids,
digests, timestamps and the vault path normalised (`ccmp_ux2.py`).
- **Every RPC Today calls answers identically** main vs merge. The only differences: `initialize` lists one more
  method (440 vs 439) and `workbench.open_problems` answers `{"problems": [], "version": 1}` on the merge where main
  has no such method. On probability, the in-session `get_today_queue` also differed in the order of two tied items;
  three more runs (`c_repeat.sh`) show this is run-to-run noise from the minted session id (main vs main: 8, 44 and 52
  differences in that call; merge vs merge: 16; a later main run vs the merge: identical).
- **`workbench.open_problems` returns a list** (empty on these copies, which hold no open workbench problem) and
  **writes nothing**: a whole-database digest (every table's row count and content hash, read from outside the
  sidecar) is unchanged across each of the two calls on both vaults.

**(c) The frontend.** The whole vitest run (210 files, 1,822 tests) covers both shells: the simple shell's Today
(`TodayPlace.test.tsx` 42, `App.today.test.tsx` 21, `todayPlan.test.ts`, `readerWorkbenchResume.test.tsx`) and classic
(`classicIsBase.test.ts` 9, `App.shell.test.tsx` 14, `StartScreen.test.tsx` 13, `TodayScreen.plan.test.tsx` 3).
`StartScreen.tsx` and `TodayScreen.tsx` are unchanged against main (empty diff).

**Calls.** `model_call_receipts`: 25 learner databases under `landing-ux3/`, **0 rows** in every one (no COMPLETED
row, no row at all); the other 14 databases (probability's `.learnloop/state.sqlite`) have no such table. No process
started, no connection opened. Spend: $0.

### New findings

1. **The AD feature audit once wrote its `unavailable` judgments twice (Low, main's, not this stage's).** In one of
   seven plan runs (the merge's code on `c31_merge` linear algebra) `judgment_ledger` gained 40 `ad_feature_audit`
   rows (4 per item-dimension pair) instead of 20; the four repeat runs (two per code) gained 20 each. The routes are
   loopback, so each row is an `unavailable` record; nothing served or dumped differs. It looks like two audit passes
   racing over the same work; UX3 changes no Python on that path. Worth a look in the AD track.
2. **Stage gates that select vitest files can miss the manifest tests** (`retryWiring.test.tsx`; earlier,
   `classicIsBase.test.ts`). The whole run in the landing gate caught it, as designed.

### For the owner

- **No migration, no successor, no config key.** Your vaults stay at `mvp-0.31`; nothing to run. Nothing served
  changes (parity (a)); the sidecar answers as main's (parity (b)).
- **What you see in the simple shell** (the default, `[ui] shell = "simple"`):
  - **Today is one place.** Start and Today are merged: one sentence in minutes (*25 minutes today: finish §5.4
    Mixtures, then 2 short questions from earlier days and a fix for a mix-up.*), the blocks as *about N min* rows,
    the minutes chips, **Begin ↵**, the streak in the footer. No tiles, counts, lane names, scores or algorithm words.
    After a break it says *Welcome back* with a short catch-up and nothing about what slipped.
  - **why? ▸** (or `?`) explains the split and each block's reason in words, with the receipts behind *details ▸*.
  - **The full list** (`l`): plain titles, *about N min* where the plan estimates them, and a few words on why each is
    there; Enter opens one (as your pick), `p`/Esc go back.
  - **Sessions are implicit.** The first practice action (a question, a Reader check, an exercise, a quick check)
    starts a session with your remembered minutes and carries on; there is no "start a session first" notice. Begin
    and such an action at the same moment now share one session (F7).
  - **Pick up a thread:** open questions (*open in book ▸*), unfinished workbench problems (*resume ▸* opens the book
    and the problem), the reading wrap-up; at most three, then *more ▸*. *New captures ▸* appears only when there is
    something, with no number.
  - **The goal card:** *Probability midterm · Nov 14 · on track*, *Practise for this goal*, *Practice exam* when its
    pool is ready, and the old banner's numbers behind *details ▸*.
- **Classic is unchanged.** `[ui] shell = "classic"` keeps Start, Today and their session notice exactly as before.

### Open items

1. **F3 (Low, follow-up for a Reader workbench stage).** A problem worked on an earlier reading of its book (E1, the
   book now on E2) is not offered by Today and is refused cleanly if a resume names it; nothing is lost. Validated
   restoration of E1 or re-anchoring onto E2 through `span_aliases` belongs to the RW track.
2. **The real-UI usability walk** (open question 3): Today with the tester's T4 on a backup copy through the
   usability harness, as Phases 1 and 2 did. Still owed.
3. **The backdrop** moves to Phase 6 (Settings → Appearance), as recommended (open question 1); classic Start keeps
   it meanwhile.
4. Captures show as *New captures ▸* with no number (open question 2, rule 10), as built.
5. New finding 1 (the AD feature audit's doubled `unavailable` rows) for the AD track.
6. `desktop_validate.py` and `module_validate.py` fail as before.
7. The parity copies' backup-API reads left empty `state.sqlite-wal` and refreshed `-shm` files beside both backup
   databases in the main checkout's `fixtures-local/vault-backups-20261025-mvp030/` (as at the previous landings; the
   databases are unchanged). Harmless; left in place.
