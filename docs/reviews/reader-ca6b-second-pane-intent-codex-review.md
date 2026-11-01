# Reader CA6b: Codex review and fix round

Stage `reader-ca6b-second-pane-intent`, branch `reader/ca6b-second-pane-intent`, worktree `learnanything-merge2`.
Review: gpt-6.1-sol, job `20261101-012253-owBGpm` (static tracing only; its typecheck could not start). Base for
this round: `83b3abf672` (stage record).

Owner decisions in force (2026-10-12): the spec's recommended defaults, and frictionless defaults (honest labels,
generous defaults, live changes behind kill switches). No migration, no config key, no new parameter (nothing to
classify in `parameter_registry.py`), and no schema change. No paid or live call was made. No vault was opened and
no GUI was launched.

## Review

Each finding was reproduced first with a test that fails on the pre-fix sources. Those sources were checked out
temporarily from the previous commit while the test file was kept, and then restored. Each finding was then fixed.

| id | severity | title | verdict | commit | test (fails before, passes after) |
|---|---|---|---|---|---|
| F1 | High | Inquiry commitments persist under the wrong book | **fixed** | `8ed8659c2e` | `sideBySideIntent.test.tsx`: *F1: a thread about the second pane's book keeps its commitments and status on that book*, *F1: dismissing a thread …* |
| F2 | Medium | Empty Enter can ask about an existing main-book thread | **fixed** | `8ed8659c2e` | *F2: after a main-book Ask, an empty Enter in the second pane starts a new thread about that book* |
| F3 | Medium | Retrying a failed second-pane Ask loses its book | **fixed** | `8ed8659c2e` | *F3: try again after a failed second-pane Ask asks the same request* (reject once, both calls identical) |
| F7 | Medium | Hidden actions remain available to the Decider | **fixed** | `f3c261b029` | `tests/test_reader_ca6b_side_pane_intent.py` (backend); *F7: a routing naming work_through / what_matters_here …* (vitest, both) |
| F4 | Medium | Opening the second book never starts cue discovery | **fixed** | `35dccfe3e9` | *F4: opening the second book runs cue discovery for it …* (the plan starts empty and fills in after discovery) |
| F5 | Medium | Second-pane cue interactions bypass RW3b receipts | **fixed** | `35dccfe3e9` | *F5: the second pane's discovered marks write RW3b receipts in that book's own visit; taps name it; try this step first records its tap* |
| F6 | Medium | Resizing the split can violate the cue attention budget | **fixed** | `35dccfe3e9` | *F6: widening the second pane places its marks again (one per screenful), and a scroll never does* (geometry-backed) |
| F8 | Medium | Second-pane cues cannot offer "check me" | **fixed** | `35dccfe3e9` | *F8: check me on a second-pane mark opens that book's item …*; `App.today.test.tsx` *CA6b, F8* (2) |
| F9 | Medium | Cue navigation keys act on the wrong pane | **fixed** | `35dccfe3e9` | *F9: Alt+down / Alt+up move among the focused pane's own marks*, *F9: with marks only in the second pane …* |

Rejected: none.

### What changed

- **F1.** `AskAbout` now carries the second book's `sourceId` and `revisionId`. *revisit once* and *make it something
  I can do* on a thread about that book call `reader.invoke_preset` with that book's source, revision and reading
  (`renderViewId` null, as for the pane's captures). The funnel event names that book. *resolved*, *dismiss*,
  *reopen*, the quick check, its poll and the reconnect answers name the reading the exchange was asked in
  (`exchange.extractionId`, through `extractionOf(rootId)`), never the open book's. Nothing is attributed to the open
  book.
- **F2.** An empty Enter in the second pane clears the reply parent (`setParentExchange(null)`) before it anchors
  the composer there. Its question is a new thread about that book.
- **F3.** `useReaderInquiry` keeps the failed request (its words, parent and override: anchor, routed answer mode,
  meta). *try again* on the same words asks exactly that request. The record is dropped on the next submit, and
  when the selection or the thread changes.
- **F7.** `reader.route_intent` takes `side_pane` (default false). When it is true, the Decider's availability has
  neither `workbench` nor `reading_paths`, so the second pane's routings are never offered *work through this* or
  *what matters here?*. The second pane's `useIntentBox` sends `sidePane: true`, and the main pane's payload is
  unchanged. If a routed action is still not on the box's palette, Ask runs, the routing is recorded as
  `discarded` (not `used`), no routing id is carried, and the box says *(that isn't on offer here, so this asks)*.
- **F4-F6, F8, F9: one change.** The second pane no longer has its own cue code. It runs the Reader's own
  `useReaderCues` on its book: that book's plan, the text surface, `data-sbs-span` passages and the pane's body.
  Small optional inputs were added to `useReaderCues` (`spanAttribute`, `ownsKey`, `cueVisitId`,
  `reloadAfterPreference`) and to `useCueImpressions` (`spanAttribute`). Its `render` type narrows to
  `{ extractionId, sourceId }`. The main pane passes none of the new inputs except `ownsKey`, so its behaviour is
  unchanged. As a result:
  - **F4:** `useCueDiscovery` runs for the second book with its own source-open id. The sidecar applies its per-open
    call budget (the existing spend control), and the pane's plan is re-read when a job found something. It runs
    only while the plan carries `discovery`, which is RW3b's switch.
  - **F5:** impression receipts are written for shown, held-out and set-aside cues, under the plan each was first
    seen on, in the book's own cue visit. That visit is minted per open of the book. It is not the open book's
    funnel visit. Taps go through `reader.cue_tap` with that visit and the first-seen plan. *try this step first*
    records its `try_first` tap and opens RW1b's next-step question in the pane. *fewer marks like this* records its
    response.
  - **F6:** a `ResizeObserver` on the pane's body changes the placement's `layoutKey` when the pane's size changes
    (the splitter, the rail overlay, the window), so marks are placed again. A scroll changes no size and places
    nothing.
  - **F8:** *check me* is offered. `checkMeFromSideCue` hands the shell the cue's book card (from the library), and
    only while the pane still shows the reading the request was made on. In the shell, a workbench check whose
    card is not the open Reader source opens the Reader on that book at the mark's passage, where the working
    posture shows it with the book hidden (the `fromStart` path). Without the workbench, the practice screen's
    *back* returns to that book at that passage (`readerReturn`, unchanged). Side by side itself is not reopened
    after the check. That is also what happens to a main-pane check while side by side is open, because the working
    posture closes side by side.
  - **F9:** each controller's Alt+↓ / Alt+↑ listener checks pane ownership. The main pane leaves keys whose target
    is inside `[data-side-by-side-pane]`, and the second pane takes only those. A mark moved to in the second pane
    is placed by scrolling the pane, never by reading.
- The stage record's deviation 2 is marked superseded, and deviation 1 notes the router change.

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`. One test run at a time. TMPDIR was outside the worktree.

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`), 15 files: **6041 passed**.
  - New: `tests/test_reader_ca6b_side_pane_intent.py`.
  - Files on the changed handler (`reader.route_intent`): `test_reader_intent.py`, `test_reader_reconstruct.py`,
    `test_reader_rw1b_review.py`.
  - Contract pins and the Reader backend files the frontend calls: `test_reader_ca6_side_by_side.py`,
    `test_reader_cues.py`, `test_reader_activity.py`, `test_reader_rw3b_protection.py`,
    `test_desktop_activation_audit.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`,
    `test_architecture.py`, `test_public_tip_guards.py`, `test_salience_firewall.py`,
    `test_tracked_fixture_databases.py`.
- No migration, no DB or connection code, no schema change: no durability run and no DB reference regeneration.
  `src-tauri` is unchanged, so no cargo check was needed.
- Frontend (`apps/learnloop-tauri`): `npm install` ok, `npm run typecheck` clean. Vitest (`--maxWorkers=4`),
  **115 files, 1163 passed**. The set is every test file that imports `ReaderScreen`, `SideBySidePane`,
  `useIntentBox`, `IntentBox`, `intentPalette`, `AskRail`, `ReaderAskBranches`, `useReaderInquiry`,
  `useReaderCues`, `useCueImpressions`, `useCueDiscovery`, `useSidePane`, `MarginMark` or `App`, plus every
  `src/screens/reader/**` and `src/screens/ReaderScreen.*` test, `attentionBudget`, `workbench/switchOff`, `keymap`,
  `shellChrome`, `classicIsBase` and every `src/app/App.*` test. That covers all 83 files of the stage gate, including
  `sideBySideIntent.test.tsx`, now 31 tests (12 new), and `App.today.test.tsx`, now 23 tests (2 new).
  `npm run frontend:build`: ok.

## Open items

1. Desktop catalog at landing (unchanged from the stage record): `desktop_generate.py` on the merged tree.
2. Discovery in the second pane makes the same background cue-judge calls as opening that book alone, within the
   sidecar's per-open budget and only while RW3b's discovery is on. It is noted here for the owner's spend view, not
   as a new default.
3. ~~After a check from the second pane, the way back is the mark's passage in that book, not side by side.~~
   Resolved in the re-review (F8, below).

## Re-review (Codex job `20261101-015859-Igj9Tl`)

The re-review confirmed F1–F6 and F9 as fixed. It reopened F7 and F8 and raised two new Mediums, F10 and F11.
Each was reproduced first with a vitest test that fails on the pre-fix sources: the changed source files were checked
out from the previous commit, the test files were kept, and the sources were then restored from `HEAD`. Each was then
fixed. No migration, no config key, no new parameter (nothing to classify in `parameter_registry.py`), no schema
change, no paid or live call, no vault opened and no GUI launched.

| id | severity | title | verdict | commit | test (fails before, passes after) |
|---|---|---|---|---|---|
| F7 | Medium (reopened) | Work through and reading path omitted from the second pane | **fixed** | `0c5bc9546b` | `sideBySideIntent.test.tsx`: *the second pane's palette is the main pane's …*, *F7: work through this in the second pane takes that book to the main pane …*, *F7: what matters here? in the second pane shows that book's reading path in the pane …*, *F7: a routed action the box does not offer (work through with the workbench off) …* |
| F8 | Medium (reopened) | Returning from a second-pane check does not restore side by side | **fixed** | `0c5bc9546b`, `d93e5563df` | *F8: check me on a second-pane mark takes that book to the main pane … with the way back to side by side*, *F8: the Reader opened again with that way back … Alt+← reopens side by side*; `App.today.test.tsx` *CA6b re-review, F8 …*; `readerWorkbench.test.ts` *the way back to side by side goes with a submit …*; `returnStack.test.ts` *besideTrail …* |
| F10 | Medium | Failed Ask grounding survives a source reset | **fixed** | `d803a1ab59` | *F10: a failed second-pane Ask is forgotten when another book opens …*, *F10: a new composer opened in the second pane is not the failed request …* |
| F11 | Medium | Reopening the second book skips a fresh discovery lifecycle | **fixed** | `d803a1ab59` | *F11: closing the second pane and opening the same book again is a fresh discovery …* |

Rejected: none.

### What changed

- **F7.** The second pane's palette is the main pane's. The stage's `hiddenKinds` was removed (`intentPalette.ts` is
  back to base), and the second box gets `canWorkThrough` from the workbench switch, as the main box does. The fix
  round's `reader.route_intent` `sidePane` restriction was removed: the handler is back to base, its client parameter
  is gone, and `tests/test_reader_ca6b_side_pane_intent.py` was deleted, since nothing is left for it to test. The
  Decider is offered the same actions in both panes. The fix round's honest fallback stays: a routed action a box does
  not offer runs Ask, is recorded as `discarded` and says *(that isn't on offer here, so this asks)*.
  - *work through this* in the second pane: the working posture is the open book's. So `takeBesideBook` opens that
    book in the main pane at the selected passage through `openLibraryHit`. This is a source detour pushed after side
    by side's crumb, which stays one step back. Once that book is open, the handoff runs `wbCtl.openSelection` with
    the selection's stem, passages and import request (that book's source, revision and reading, and the open
    render's view), the same call the main pane makes. It runs only when the open reading is the one the passages
    were selected on. Alt+← or the crumb reopens side by side.
  - *what matters here?* in the second pane shows that book's reading path in the pane, headed *WHAT MATTERS IN
    AXLER* with *close*. It is the Guide's own `ReadingPathCard` on that reading. A section on it opens in the pane
    through the card's new optional `onJumpSection`, which is absent for the main Guide, so the main Guide is
    unchanged. *try it* takes the book to the main pane as work through does. The card stays while the pane moves
    among that book's sections. It goes when the pane closes or shows another book.
- **F8.** *check me* on a second-pane mark takes that book to the main pane at the mark's passage (the same source
  detour), and then hands the shell the check with that book's card. The shell opens it there (book hidden) without
  remounting the Reader, so the return stack keeps side by side one step back. The shell's own screens unmount the
  Reader: the practice screen (workbench off) and feedback after a workbench submit. For those, the way back travels
  as `besideTrail`, which is the return stack while a `side_by_side` entry comes before the current one
  (`returnStack.besideTrail`; otherwise nothing is carried, and every other return is as before). The path is
  `ReaderCheckMeRequest.besideTrail` → `ReaderReturn` → `readerTargetBack` → `ReaderOpenSource`. A workbench submit
  carries it the same way through the Reader's wrapped `onSubmitted` → `workbenchReturn`. A Reader opened with a trail
  seeds its stack once the book opens (`seedReturnStack`). The learner lands on the mark's passage in that book, and
  Alt+← reopens side by side. With `reader_inquiry` off there is no return stack, so there is no crumb and no trail,
  as in CA6.
- **F10.** `resetInquiryState` (every source reset) forgets the failed request. A new composer also forgets it: the
  second pane's empty Enter, or *ask about this book instead*, through `forgetFailedAsk` on each change of the
  composer's anchor. *try again* is now an explicit `retryAsk` that replays the failed request. ↵ on the same words
  still replays it, but only while that failure belongs to this source and this composer.
- **F11.** `useCueDiscovery` treats a null extraction as the end of an open. It drops the open id and the
  asked/re-asked records, so the same book opened again (the second pane closed and reopened, or the main book left
  for the library and reopened) is a new open. It gets a new `sourceOpenId`, so the sidecar gives it a fresh per-open
  budget, and it is asked again for unchanged targets. Within an open nothing changes.

### Interactions and limits

- The handoff is a source detour, which the return stack already supported. Since CA6, walking back onto a
  `side_by_side` entry reopens its pair once the main pane holds the book it was opened beside. Opening the second
  book ends the pair (`via: "source"`), so `side_by_side_closed` is recorded as before. Reopening it records
  `side_by_side_opened` with `via: "crumb"`.
- A workbench submit made after any detour from side by side carries the trail. This includes another book opened
  from the library while the crumb was current. A main-pane check or work through made while side by side is open
  (the crumb current, nothing after it) carries none. Its way back is the passage, as before.
- The workbench submit wrapper (`wbProps.onSubmitted` in `ReaderScreen`) has no ReaderScreen-level test. Its parts
  are tested: `besideTrail`, `workbenchReturn` / `readerTargetBack` with a trail, and the Reader seeding a trail
  handed back.
- RW6b part 2 also edits `ReaderScreen`. This round's changes there are the side-pane router cases, the handoff state
  and effect next to the side pane, the side pane's card slot, `wbProps`, and the initial open.

## Gate (re-review; targeted, the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`. One test run at a time. TMPDIR was outside the worktree.

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`), 14 files: **6040 passed**. These are the reverted `reader.route_intent` handler's files
  (`test_reader_intent.py`, `test_reader_reconstruct.py`, `test_reader_rw1b_review.py`), the contract pins and the
  Reader backend files the frontend calls: `test_reader_ca6_side_by_side.py`, `test_reader_cues.py`,
  `test_reader_activity.py`, `test_reader_rw3b_protection.py`, `test_desktop_activation_audit.py`,
  `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_architecture.py`, `test_public_tip_guards.py`,
  `test_salience_firewall.py`, `test_tracked_fixture_databases.py`. The handler is identical to base, and
  `tests/test_reader_ca6b_side_pane_intent.py` was deleted.
- No migration, no DB or connection code, no schema change: no durability run and no DB reference regeneration.
  `src-tauri` is unchanged, so no cargo check was needed.
- Frontend (`apps/learnloop-tauri`): `npm install` ok, `npm run typecheck` clean. Vitest (`--maxWorkers=4`),
  **122 files, 1303 passed**. The set is every test file that imports `ReaderScreen`, `SideBySidePane`,
  `useIntentBox`, `IntentBox`, `intentPalette`, `AskRail`, `ReaderAskBranches`, `useReaderInquiry`,
  `useReaderCues`, `useCueImpressions`, `useCueDiscovery`, `useSidePane`, `MarginMark`, `ReadingPathCard`,
  `returnStack`, `useReaderWorkbench`, `readerWorkbench`, `readerCheck` or `App`, plus every `src/screens/reader/**`
  and `src/screens/ReaderScreen.*` test, every `src/app/App.*` test, `attentionBudget`, `workbench/switchOff`,
  `keymap`, `shellChrome`, `classicIsBase`, `readerWorkbench` and `readerCheck`. In it, `sideBySideIntent.test.tsx`
  has 36 tests (6 new, and 3 rewritten: the palette test, the not-offered fallback, which replaces the two-case F7 table, and F8), `App.today.test.tsx` 24 (1 new), `readerWorkbench.test.ts`
  1 new and `returnStack.test.ts` 1 new. `npm run frontend:build`: ok.
- Open item 1 (desktop catalog at landing) is unchanged. No new TS/TSX file was added in this round.

## Fix round 3 (final verify)

The stage's final Codex verify (job `20261101-023146-5YAMhu`, on `257684b592`) confirmed F1 and F7 as fixed. It
reopened F8, F10 and F11 and raised F12, all Medium. Each was reproduced first with a vitest test that fails on
`257684b592`: the tests were committed alone (`aaa5a0d1d0`) and run against the unchanged sources, and all five
ReaderScreen-level tests and two of the three hook tests failed for the reported reason. The fixes are in
`d21ef7b959`. No migration, no config key, no new parameter (nothing to classify in `parameter_registry.py`), no
schema change, no Python change, no paid or live call, no vault opened and no GUI launched.

### Verbatim findings

> Reviewed `3056566ca7..reader/ca6b-second-pane-intent` at `257684b592`.
>
> | Finding | Result |
> |---|---|
> | F1 [High] | **CONFIRMED-FIXED**: live commitments retain the second book's context; history projection remains scoped to its extraction. |
> | F7 | **CONFIRMED-FIXED**: both missing actions have handlers and palette/router availability. |
> | F8 | **REOPENED**: returning can restore the wrong second-pane section. |
> | F10 | **REOPENED**: a late failure can restore grounding after a new composer opens. |
> | F11 | **REOPENED**: direct source detours still suppress discovery when returning. |
>
> **F8 [Medium]: returning restores the initial second-pane section.**
> **Location:** [ReaderScreen.tsx:1550](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/ReaderScreen.tsx:1550), consuming the crumb maintained by [useSideBySide.ts:430](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/reader/useSideBySide.ts:430).
> **Reproduction:** Open Strang beside Axler section A. Move Axler to section B, then start "check me" there. Return from practice/feedback and press Alt+←. `goSide` updates the displayed target without updating the crumb; the final handoff preserves that stale crumb. An isolated hook reproduction showed **B before the check, A after returning**. Work-through uses the same trail.
> **Fix:** Snapshot the current pair and passage into its return entry before the handoff, or update the crumb whenever either pane moves.
>
> **F10 [Medium]: a pending failure repopulates forgotten grounding.**
> **Location:** [useReaderInquiry.ts:815](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts:815), [useReaderInquiry.ts:855](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts:855).
> **Reproduction:** Start a routed second-pane Ask on passage A and leave its promise pending. Open a new composer on passage B, then reject the old request. Although `forgetFailedAsk()` ran, the old catch restores its request and question. Submit those words from the new composer: `ask()` replays A's grounding and routed answer mode. The isolated hook reproduction sent **A twice**, despite the current composer pointing to B.
> **Fix:** Give composers a generation identity. A failure may populate retry state only while its composer generation remains current.
>
> **F11 [Medium]: returning through a source detour skips fresh discovery.**
> **Location:** [useCueDiscovery.ts:66](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts:66).
> **Reproduction:** Complete discovery on main book A, open B through a source detour, then return to A with unchanged targets. `openSource` replaces the render directly; extraction never becomes null. The new open ID is minted, but A's completed-target cache survives and suppresses the request. An isolated hook reproduction of **A → B → A**, including plan-loading intervals, observed discovery calls only for **A → B**. Explicit close/reopen does work.
> **Fix:** Reset deduplication state on every actual source-open transition, including direct source replacement.
>
> ### F12 [Medium] Section navigation replenishes the discovery budget
>
> **Location:** [useCueDiscovery.ts:66](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/reader/useCueDiscovery.ts:66), reached through [ReaderScreen.tsx:1488](/home/saturn/Documents/thinking/learnanything-merge2/apps/learnloop-tauri/src/screens/ReaderScreen.tsx:1488).
>
> **Scenario:** Move the second pane to another section, manually or through follow-along. While it loads, `sbsSection` becomes null, so discovery interprets ordinary navigation as closing the book. The isolated reproduction issued two requests with unchanged extraction/targets but **different `sourceOpenId`s**. Each section change can therefore replenish the per-open judge-call budget; the separate daily cap still applies.
>
> **Fix:** Track source-open lifetime separately from section availability. Pause during section loading while retaining the open ID, completed targets, and budget.
>
> Validation: TypeScript checking passed; four isolated React hook reproductions confirmed the failures above. Suite tests and build were not run. No files were edited, and no prohibited files or vault databases were read.
>
> VERDICT: REOPENED
> codex-job: /home/saturn/.cache/codex-agent/jobs/20261101-023146-5YAMhu

### Closures

| id | severity | verdict | commit | test (fails on `257684b592`, passes after) |
|---|---|---|---|---|
| F8 | Medium (reopened) | **fixed** | `d21ef7b959` | `sideBySideIntent.test.tsx`: *F8 round 3: check me after the second pane moved to 7.B keeps 7.B as the way back …* (the shell's trail names 7.B at the mark's passage; Alt+← here and in the Reader the shell opens again both reopen 7.B), *F8 round 3: work through this after the second pane moved to 7.B …* |
| F10 | Medium (reopened) | **fixed** | `d21ef7b959` | *F10 round 3: a failure that lands after a new composer opened leaves no retry …* (A pending, a new composer on another passage, A rejects, submit: the second call is that composer's passage and an ordinary question; `readerAsk` is called twice in all) |
| F11 | Medium (reopened) | **fixed** | `d21ef7b959` | *F11 round 3: back on the main book after a source detour (A, then B, then A) is a fresh discovery for A, under a new open*; `rw3bReview.test.tsx` *CA6b F11: A, then B, then A again … is three opens* |
| F12 | Medium | **fixed** | `d21ef7b959` | *F12 round 3: moving the second pane among its book's sections keeps its open …* (no ask for unchanged targets; a new target names the same open id); `rw3bReview.test.tsx` *CA6b F12: a section loading within one open … pauses discovery …* (also: a job still running is read to its end) and *CA6b F12: a job left running when the open ends is not read on* (a control that passes before and after) |

Rejected: none.

### What changed

- **F8 (a snapshot at the handoff, the brief's first option).** Just before a handoff leaves side by side (*check
  me* on a second-pane mark, *work through this* from the second pane, and the reading path's *try it*, which all go
  through `takeBesideBook`), the crumb takes the pair as it is now. The second pane's target is the section it shows
  now (moved by hand or by follow along since side by side opened), with the handoff's passage as its `spanId`. The
  main pane's passage is the one read now. This uses `useReaderInquiry.snapshotSideBySide`, which acts only while a
  `side_by_side` entry is the current one. `replaceCurrent` now also accepts `spanId`. The stack is what
  `besideTrail` carries, so the same pair comes back in this Reader (Alt+← or the crumb) and in a Reader the shell
  opens again after its practice or feedback screen. The crumb is not updated on every pane move: other detours
  taken from side by side (a peek, a branch, a library hit) still return to the pair as it was last opened or
  replaced, as before this stage.
- **F10.** `useReaderInquiry` keeps a composer generation (`composerGenRef`). `submitAsk` records the generation it
  was asked from. Its failure leaves the retry record only while that generation is still current. The words are
  still put back in the composer, as before. The generation moves on with every new composer (`forgetFailedAsk`), a
  source reset, and a change of selection or thread. In `ReaderScreen`, the new composer is now a generation at once:
  the empty Enter in the second pane, *ask about this book instead*, and the composer going back to the open book
  (the second pane's selection gone, or a routed Ask with words while a second-pane composer was open) all call
  `openComposer`, which forgets the failed request and bumps the generation in the same handler. This replaces the
  re-review's effect on the composer anchor. That effect ran after the render, and it could not tell a pending
  request from a new one.
- **F11 and F12 (one structural fix).** `useCueDiscovery` tracks the source open apart from the reading shown. Its
  new optional `openKey` names the open. When it is absent, the reading itself is the open (the main pane). A new open
  (a new `sourceOpenId`, nothing asked yet, and so a fresh per-open budget at the sidecar) comes only when `openKey`
  changes. That happens when the open source's identity changes, direct replacement included (A, then B, then A is
  three opens), or when the open ends (`openKey` null: closed). A reading that is briefly absent while `openKey`
  stays the same pauses discovery. No new ask is made, and the open id, what was asked, the re-ask counts and any job
  being read are kept. A job running across a pause is read to its end, and the reading coming back asks nothing
  again. The open ending (or the Reader unmounting) stops every job of that open. The second pane passes its book
  (`sbs.target.extractionId`, through `useSidePane`'s new `openBook` and `useReaderCues`' new `discoveryOpenKey`).
  That value stays set while a section loads (by hand or by follow along) and while the pane is hidden by a comparison
  or a narrow window. It goes to null when side by side closes (closed, walked off, switched off, or another book in
  the main pane).
- **ReaderScreen-level wrapper test** (the re-review's open limit): `ReaderScreen.workbench.test.tsx` *CA6b: a submit
  made on a Reader opened with the way back to side by side hands that way back to the shell*. It is coverage for
  existing behaviour, so it passes before and after.

### Interactions and limits

- A selection or thread change while an Ask is pending now drops that Ask's retry when it fails (a new generation).
  The record already listed both as ending the retry. The only difference is timing: a failure that lands after the
  change no longer brings the retry back.
- Within one open of the second book, the pane's discovery request names the book's reading, as before. Section
  changes therefore never ask again for unchanged targets, and a new target asks within the same open and budget.
- RW6b part 2 also edits `ReaderScreen`. This round's changes there are the handoff snapshot next to
  `takeBesideBook`, `openBook` on `useSidePane`, and `openComposer` replacing direct anchor sets (four places).

### Gate (fix round 3; targeted, the full suite runs once at landing)

Every vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
one test run at a time, with TMPDIR outside the worktree.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- No Python changed: no pytest. No migration, DB or connection code, or schema change: no durability run and no DB
  reference regeneration. `src-tauri` is unchanged: no cargo check.
- Frontend (`apps/learnloop-tauri`): `npm run typecheck` clean. Vitest (`--maxWorkers=4`) on the re-review's set
  (the same selection rule, with no new test file this round): **122 files, 1312 passed** (1303 + 9 new: 5 in
  `sideBySideIntent.test.tsx`, 3 in `rw3bReview.test.tsx`, 1 in `ReaderScreen.workbench.test.tsx`). In a first run of
  the set, the unrelated `figures/sketch/sketchSandboxReview.test.tsx` *keeps the checks … played to t_max* failed
  once on timing under load (`t = 0 / 100`, 12 s). It passed alone (9/9) and in the full rerun. `npm run
  frontend:build`: ok.
- Open item 1 (desktop catalog at landing) is unchanged. No new TS/TSX file was added.

## Fix round 4 (Sol verify of round 3)

The Sol verify of round 3 (job `20261101-025113-5pWHQR`, on `8389f3a791`) returned NOT CLEAN with one High and three
Mediums. The orchestrator ruled that finding 1 and the earlier F1 are one class: something begun in the second pane
is persisted or opened under the main book. So this round fixes the handler and also audits every action reachable
from the second pane, or from an object that came from it (table below).

Every new test was committed alone (`7591dc68a1`, plus the show-passage test in the fix commit) and run against
the unchanged sources of `8389f3a791` (source files checked out from `HEAD`, test files kept, then restored).
12 of the 13 new tests failed there, each for the reported reason. The exception is the reconnect test, which
covers an F1-era fix and passes before and after. Fixes: `1f78f64af4`. No migration, no config key, no new parameter
(nothing to classify in `parameter_registry.py`), no schema change, no Python change, no paid or live call, no vault
opened and no GUI launched.

### Verbatim findings

> 1. High — ReaderScreen.tsx:2381: imported second-pane exercises open under the main book. Import an Axler exercise beside Strang, then press the completed import's "work through this" in Notes. The import state keeps Axler's spans but drops its source identity. The handler at line 4132 calls the Strang-bound `wbCtl.openItem`, persisting a workbench session with Strang's extraction and Axler's spans. Fix: retain the import's source and reading, and hand off to that book before opening the item.
> 2. Medium — App.tsx:984: F8 remains open when a check requires starting a session. In the classic shell with no session, start "check me" from the second pane, then begin the session. `fromStart` remounts the Reader with only `{ card, spanId }`, discarding `request.besideTrail`, so Alt+← can no longer restore side by side. Fix: carry the trail into every Reader remount performed here.
> 3. Medium — useSidePane.ts:235: discovery results disappear when completion occurs during a pause. Hide the pane with a comparison while discovery runs. Completion invokes a reload whose extraction is null, so it returns without refreshing. Resuming uses the still-fresh cached plan, while discovery's completed-target record suppresses another request. An isolated reproduction returned without the newly discovered marks. Fix: retain a pending refresh across pauses, or refresh the open book's plan independently of its visibility.
> 4. Medium — useReaderInquiry.ts:776: a late successful Ask takes over a fresh composer. Start an Ask on passage A, then open a new composer on B while it is pending. A's success unconditionally installs A as the parent and clears B's draft, so the next question follows A despite the composer's B anchor (reproduced in memory). Fix: apply the composer-generation check to successful composer updates as well as failure retry state, while keeping the answer in history.

### Closures

| finding | severity | verdict | test (fails on `8389f3a791`, passes after) |
|---|---|---|---|
| 1 | High | **fixed** (with the audit below) | `sideBySideIntent.test.tsx` *finding 1: an exercise imported from the second pane is worked through in that book …* (Axler opens in the main pane; `workbench.open` names `ext_axler`, `ax7a_1`, once; never the main reading) |
| 2 | Medium | **fixed** | `App.today.test.tsx` *CA6b fix round 4, finding 2*: *classic: Begin, then the Reader opens on the check's book with the trail* and *simple: the implicit start, then the Reader reopened … carries the trail* |
| 3 | Medium | **fixed** | *finding 3: what discovery found while the second pane was loading another section is drawn when it shows (the plan re-read past the cache)*. The test turns on the mock's plan cache, as `readGuidePlan`'s is. |
| 4 | Medium | **fixed** | *finding 4: an answer that lands after a new composer opened goes into history, and leaves that composer's draft and thread alone* |

Rejected: none.

### What changed

- **Finding 1.** `ExerciseImportState` now carries the book and reading the exercise was imported from
  (`sourceId`, `extractionId`). An import made in the second pane names that book; one made in the main pane names
  the open book. *work through this* on a completed import (`workThroughImported`) opens the item directly only
  when that reading is the open one. Otherwise it takes the book to the main pane through the beside handoff (a new
  `item` run) and opens the item there with its own passages.
- **Finding 2.** In `pickCheckMe`, the Reader the shell reopens (`fromStart`, or a check whose book is not the open
  one) gets `besideTrail` with `{ card, spanId }`. This is the only Reader remount there.
- **Finding 3.** `useSidePaneCues` keeps a forced re-read asked for while no reading is shown (`reloadPending`). Such
  a request comes from discovery finishing during a pause, or from a preference change. When the reading comes back,
  the plan is read past the cache.
- **Finding 4.** `useReaderInquiry` now has a second counter, `composerOpenRef`. It moves on only with a new composer
  (`forgetFailedAsk`, through `openComposer`) and with a source reset; a selection or thread change does not move it.
  An answer that lands after that counter moved goes into history (and the return stack's branch entries). It does
  not become the thread, empty the box, remount the composer or move focus. A failure from an older composer no longer
  writes its words into the newer one. The retry gate is round 3's counter, unchanged. Selecting in the main pane
  while a second-pane composer is open is a new composer too (`openComposer(null)`).
- **The handoff runs once.** While testing finding 1, the beside handoff effect ran up to four times for one handoff.
  Clearing it is a state update, and a render already under way at a higher priority may not include that update yet,
  so the effect saw the same handoff again. A check or a work through could therefore be handed on more than once. A
  ref (`besideRanRef`) now runs each handoff id once. The finding 1 test asserts a single `workbench.open` after the
  handoff settles.

### Audit: the second book's identity

Rule applied: an action begun in the second pane, or on an object that came from it, takes its book, revision and
reading from the pane or the object, never from the main render. Where the object outlives the moment, the identity
is stored on it: the exchange's `about` (since F1), the import (finding 1), and the library ask's request (`sourceId`,
new). What needs the open book takes that book to the main pane first, through `takeBesideBook`, with side by side
one step back. What the second pane can show runs there while it shows that passage.

| # | action | persists or opens | identity from | test |
|---|---|---|---|---|
| 1 | Ask (routed, or the composer the pane opened) | `reader.ask` | the pane's section (`AskAnchor.about`) | *a routed ask acts on the second pane's book …*; *an empty Enter in the second pane opens the composer …* |
| 2 | Follow-up, *another way*, *that didn't help* on a thread about that book | `reader.ask` | the parent exchange's `about` | *audit: a reconnect answer …* (asserts the follow-up's `ext_axler`) |
| 3 | *resolved* / *dismiss* / *reopen* | `reader.set_inquiry_status` | `exchange.extractionId` | *F1: dismissing a thread …*, *F1: a thread about the second pane's book keeps its commitments and status …* |
| 4 | *revisit once* / *make it something I can do* | `reader.invoke_preset` | `exchange.about` (source, revision, reading) | *F1: a thread about …* |
| 5 | Branch *done* | `resolve_question_event` | the question event's id (no book) | *audit: a reconnect answer …* |
| 6 | Reconnect answers, quick check, its poll and answers | `reader.reconnect_answer`, `reader.inquiry_question(_action)` | `extractionOf(root)` = the exchange's reading | *audit: a reconnect answer on a thread about the second book names that book's reading* (the quick check uses the same `extractionOf`) |
| 7 | Preset (*explain differently*, …) | `reader.invoke_preset` | the pane's capture target | *a routed preset (explain differently) goes to the second pane's book …* |
| 8 | Highlight or note (box; CA6's bar with the box off) | `reader.capture` | the pane's capture target / section | *a routed highlight and an exercise import go to the second pane's book*; `sideBySideReader.test.tsx` (bar captures) |
| 9 | Import exercise | `reader.import_exercise` | the pane's capture target | as 8, and *finding 1* |
| 10 | *work through this* on that import | `workbench.open` | the import's own `sourceId`/`extractionId` (new), handed to that book | *finding 1 …* |
| 11 | *work through this* (box) and the reading path's *try it* | `workbench.open` (through the import) | the pane's target / the path's exercise, handed to that book; crumb snapshot (round 3) | *F7: work through this in the second pane …*; *F8 round 3: work through this …* |
| 12 | Reading path in the pane: read, depth, override | `reader.reading_path(_set_depth/_override)` | `ReadingPathCard`'s `extractionId` (the pane's reading) | *F7: what matters here? in the second pane …* |
| 13 | Active reading, *another way*, *try this step first* from a mark | `reader.active_question` | the pane's own `useActiveReading` | *active reading and another way run on the second pane's reading …*; *F5 …* |
| 14 | Figures (*make this explorable*, *show me* with words) | `reader.figure_request` / `figure.request` | the pane's own `useFigures` | *make this explorable builds a figure on the second pane's reading* |
| 15 | Cue marks: impressions, taps, *fewer*, discovery, preferences | `reader.cue_*`, `reader.set_cue_preferences` | the pane's render (`useReaderCues`) | *F4*, *F5*, *F12 round 3*, *cue marks follow the density setting per pane …* |
| 16 | *check me* on a mark | the shell's check (card) | the mark's book, handed to that book | *F8 …*, *F8 round 3 …* |
| 17 | Library ask (*where else is this explained?*, Transfer) | `reader.library_ask` | the pane's reading, and now its book on the request (`sourceId`) | *where else is this explained? asks the library anchored on the second pane's reading* |
| 18 | That answer's comparisons (*compare these books*, compare all, refine, pins, compare again) | `reader.library_compare` | `openSourceId` = the ask's book (`useLibraryAsk.openOf`, new; was the open book) | *audit: a library answer asked from the second pane compares with that book leading* |
| 19 | That answer's *practice this question* and its pick | `find_practice`; the shell's check | the ask's reading (`caller.ref`); the ask's book and anchor passage, handed to that book (new; was the open book's card and reading position) | *audit: a practice pick from a library answer asked in the second pane opens in that book …* |
| 20 | *how do my other books treat this?* | `reader.library_compare` | the pane's reading; `openSourceId` the pane's book | *how do my other books treat this? in the second pane …* |
| 21 | Tutor offers on an answer about that book: *try the next step first* | `reader.active_question` | `exchange.about`: in the pane when it shows the passage, else in that book (handoff `next_step`) | *audit: the tutor's offers …* (pane); *audit: try the next step … with side by side closed …* (handoff) |
| 22 | … *show me* (the tutor's goal) | `figure.request` (`readingAt`) | `exchange.about`: the pane's figures, else that book (handoff `show_me`) | *audit: the tutor's offers …* |
| 23 | … *make this explorable* | `reader.figure_request` after opening that book | `exchange.about` (was the open book) | *audit: make this explorable on an answer about the second book …* |
| 24 | … *how do your books treat this?* | `reader.library_compare` | `extractionId` the exchange's; `openSourceId` `exchange.about` (was the open book) | *audit: the tutor's offers …* |
| 25 | … *practice this* pick | the shell's check | `exchange.about` and the exchange's passage, handed to that book (`checkBeside`, as 19) | the same `checkBeside` path as 19 (no separate test) |
| 26 | … textbook exercises (RW4b) | `workbench` / open in book | each candidate's own `sourceId` (unchanged) | existing RW4b tests |
| 27 | *show me ▸* from the Ask rail on a thread about that book, or from the composer the pane opened | `figure.request` | the parent's `about` / the composer's anchor (was the open book's figures) | *audit: show me from the Ask rail on a thread about the second book …* |
| 28 | A show-me line's *open* for a figure of that book | opens the figure | `figure.extractionId`: the pane's figures | none (UI only) |
| 29 | *show passage*: button, `p`, *show inherited passage* | a return-stack peek in the open book | not offered on a thread about that book (the button was hidden since F1; `p` and *show inherited passage* now too) | *audit: on a thread about the second book, `p` (show passage) opens nothing in the main book …* |
| 30 | Citations on such an answer | opens their book | the citation's own `sourceId` (RW1c) | existing RW1c tests |

Not covered by a new test: 25 (it shares `checkBeside` with 19), 28 (UI only), and the quick check in 6 (it shares
`extractionOf` with the reconnect answer).

### Interactions and limits

- A thread about the second book exists only while the main pane holds another book. A source reset clears the
  history, so `about` never names the open book.
- An import from another reading of the open book has the same source but a different reading. Its *work through
  this* is dropped (the handoff effect sees the reading differ) rather than opened on the wrong reading.
- Taking the book to the main pane closes side by side (`via: "source"`), with its crumb one step back, as in rounds 2
  and 3. A *show me* line whose handoff did not open its book is marked failed.
- RW6b part 2 also edits `ReaderScreen`. This round's changes there are the handoff kinds and their runner, the audit
  helpers before `showMeFromAsk`, the tutor and show-me wiring in the Ask rail props, `workThroughImported`,
  `askLibraryHere`'s anchor, and `pickLibraryPractice`.

### Gate (fix round 4; targeted, the full suite runs once at landing)

Every vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
one test run at a time, with TMPDIR outside the worktree.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- No Python changed: no pytest. No migration, DB code or schema change: no durability run and no DB reference
  regeneration. `src-tauri` is unchanged: no cargo check.
- Frontend: `npm run typecheck` clean. Vitest (`--maxWorkers=4`), the same 122-file set (no new test file):
  **122 files, 1325 passed** (1312 + 13 new: 11 in `sideBySideIntent.test.tsx`, 2 in `App.today.test.tsx`). The
  `App.today.test.tsx` StartScreen stub gained a *begin stub* button (the classic shell's Begin). `npm run
  frontend:build`: ok.
- Open item 1 (desktop catalog at landing) is unchanged. No new TS/TSX file was added.

## Fix round 5 (structural)

The Sol verify of round 4 (job `20261101-031642-6VAQ0f`, on `9dbc966d87`) returned NOT CLEAN with two Highs and one
Medium. Wrong-book attribution had then produced Highs in four rounds. The orchestrator therefore directed a
structural change, so that the class cannot happen rather than being patched case by case. It has four parts:
(a) a fail-closed backend guard in one shared helper; (b) one client `SourceIdentity` type, required wherever a
passage is persisted or handed on; (c) an honest UI state for the typed refusal; (d) active-reading state and drafts
kept outside the conditionally mounted card.

Commits:
- `1b9868358f`: the backend guard and its pytests, plus the test fixtures it needed.
- `9ed381bc37`: the client type, findings 1-3, (c) and the vitests.

Each new vitest was run against the round-4 sources of `9dbc966d87` (the source files checked out from `HEAD`, the
test files kept, then restored). The six new frontend tests and the new App assertion all failed there. The pytests are new and call the guard.
No migration, no config key, no new parameter (nothing to classify in `parameter_registry.py`), and no schema change.
No DB write path changed shape: the guard refuses before any write. No paid or live call, no vault opened and no GUI
launched.

### Verbatim findings

> 1. High — useLibraryAsk.ts:903: "where else" drops the originating book. Compare from Axler's second pane beside Strang, then press "where else is this explained?" on an unfilled view. The new request keeps Axler's reading but drops `sourceId`, so later comparisons name Strang and a practice pick falls through to Strang's card and workbench. Reproduced the lost identity and `openSourceId: "src_strang"`. Fix: preserve the originating request's source identity when building the follow-on ask.
> 2. High — ReaderScreen.tsx:1584: checks bypass the handoff's reading guard. If Axler's second pane shows reading A but opening its source resolves newer reading B, "check me" dispatches before the extraction check at line 1592. The shell drops the reading identity, and the workbench persists B with A's passage ids. An isolated reproduction emitted `extractionId: "ext_axler_NEW"` with `spanIds: ["ax7a_OLD"]`. Fix: validate the reading before dispatching checks and carry it through the shell, the session-start remount and the workbench request; refuse mismatches or open the original reading.
> 3. Medium — useSidePane.ts:158: temporarily hiding the pane destroys learner input. Answer an active-reading question in the second pane, type an unfinished proof, then open the library comparison and return. The visibility change sets the hook's extraction to null, which clears the question, and unmounting `QuestionBody` destroys its draft. Reproduced: "My unfinished proof" became an empty answer when the same question reopened. Fix: keep active-reading state through pauses and store drafts outside the conditionally mounted card.

### Closures

| finding | severity | verdict | how | test (fails on `9dbc966d87`, passes after) |
|---|---|---|---|---|
| 1 | High | **fixed** (structurally) | `LibraryAskRequest.identity` and `CompareRequest.identity` are required. *where else* builds its request with `identity: current.request.identity`. TypeScript found this omission and every other construction. | `comparePointTableCodexReview.test.tsx` *CA6b round 5, finding 1: where else after a comparison begun on the second book keeps that book for every follow-on* (the state keeps Axler; *compare these books* leads with `src_axler` while Strang is open) |
| 2 | High | **fixed** (structurally) | (i) The beside handoff checks the reading before it dispatches anything: a check whose book opened on another reading is not handed on, and the learner is told. (ii) Checks carry their reading (`CueCheckMeRequest.reading`, `ReaderWorkbenchCheck.reading`, required), and so do the shell's way back (`ReaderReturn.reading`) and the session-start remount (`reading`). (iii) The workbench refuses a check whose reading is not the one open and sends nothing. (iv) `workbench.open` refuses another reading's passage ids server-side. | `sideBySideIntent.test.tsx` *finding 2: a check whose book opens on another reading than the mark's is refused honestly, never handed on* and *finding 2: a check the mark hands on carries the mark's reading …*; `ReaderScreen.workbench.test.tsx` *CA6b round 5: a check whose reading is not the one open is refused honestly …*; `App.today.test.tsx` (classic Begin: the remount carries `data-reading="ext_prob"`); pytest `test_workbench_open` (B's reading with A's spans, an import of another reading, an import naming a source its reading is not of, a check at another reading's passage) |
| 3 | Medium | **fixed** | `useActiveReading` takes an `openKey`; the second pane passes its book. The question, "another way" and their in-flight requests are reset only when the book changes, never on a pause. The learner's draft lives in the controller (`ActiveReadingState.draft`, `setDraft`), not in `QuestionBody`'s state. | *finding 3: an unfinished answer in the second pane's active reading survives a comparison hiding the pane* (same question, "My unfinished proof" kept, no second `reader.active_question`) |

Rejected: none.

### (a) The backend guard

`learnloop.reader.source_identity` holds the rule:
- `require_source_identity` checks span ids against the reading's blocks, and the reading against the named revision
  and source;
- `require_span_keys` checks library pins (`extraction:span` keys) key by key;
- `require_exchange_in_extraction` checks an exchange against the reading it was asked in;
- `selection_span_ids` and `subject_span_id` collect the span ids a request names.

`learnloop_sidecar.source_identity.require_identity` is the one call every guarded handler makes, before it writes
anything. A mismatch raises `SidecarError("span_extraction_mismatch", …, details={extraction_id, reason, span_ids})`,
and nothing is written.

Fail closed: if span ids name a reading that does not exist, the request is refused (`reason: "unknown_extraction"`).
A request that names no passage is not checked. The guard is backward compatible: a valid call (its passages are its
reading's own) is unchanged.

Changes to existing tests:
- Two workbench test fixtures (`test_reader_workbench_rw2a.py`, one test in `test_workbench_check.py`) used reading
  ids with no reading behind them (`ext_wb`, `ext`). They now seed the reading their problems name.
- `test_figures_rpc.py::test_validation_refusals` now expects the typed code (`span_extraction_mismatch`) for a span
  the reading does not have, where it expected `validation_error`.

Deliberately cross-reading flows do not go through the guard, and each names both readings explicitly:
- `reader.reanchor` (an annotation moved to `new_extraction_id`);
- `reader.saved_place` (`to_extraction_id`, a read);
- library pins, whose keys each name their own reading (checked key by key, not against the ask's reading);
- a source exercise in `workbench.open`, checked against its own reading, which may be another book than the
  problem's.

Not guarded, because they write nothing about passages or only read:
- `reader.block_health`, `reader.span_learning_objects`, `reader.translate_selection`, `get_span_view`;
- `reader.restore_source` and `reader.retrieval_open` (they log by receipt);
- outside the Reader: `curriculum.set_scope`, `import_source_exercise`, `compare_sources`, `ask_tutor_question`.

These are listed for a follow-up if wanted.

### (b) The client type

`SourceIdentity` (`api/dto.ts`) is `{ sourceId: string; revisionId: string | null; extractionId: string }`.
- `revisionId` is null only where the client does not know it (a library hit, which has no revision). The sidecar
  then checks the reading and the source.
- There is no optional field and no fallback to the main render: each value comes from where the passage is (the
  pane's section, the mark's render, the exchange's `about`, the import, the request).

It is required in these places:
- **Persisting requests:** `ReaderCaptureInput`, `ReaderInvokePresetInput` and `ReaderImportExerciseInput` all extend
  it. The import's `sourceId` and `revisionId` are no longer optional. The server-built import requests already
  carried both.
- **Checks and handoffs:** `CueCheckMeRequest.reading`, `ReaderCheckMeRequest` (through it),
  `ReaderWorkbenchCheck.reading`, `readerWorkbenchCheck`'s input, and the beside handoff (`{ book: SourceIdentity }`).
- **Objects that outlive the moment:** `ExerciseImportState.identity`, `AskAbout extends SourceIdentity`,
  `LibraryAskRequest.identity`, `CompareRequest.identity` (client-side only; `comparePayload` is unchanged).
- **The shell:** `ReaderReturn.reading` and `ReaderWorkbenchOrigin.reading`. A workbench submit's comes from its
  session. The session-start remount carries the check's reading. The `besideTrail` entries already carry
  `sourceId`/`extractionId`.

Wrappers whose wire format takes only a reading (`workbench.open`, figure requests, `reader.library_ask`, the
inquiry RPCs) keep it. The sidecar derives the source and revision from the reading and checks the passages. Adding
fields the backend models do not accept would have changed the wire format. On the client, their identity comes from
the objects above.

### (c) The typed refusal in the UI

`errorMessage` turns `span_extraction_mismatch` into *That passage belongs to another reading; reopen it.*
(`SPAN_MISMATCH_COPY`; `isSpanMismatch`). Every Reader failure path that reports through `onError(errorMessage(…))`
says it in place of a raw message. A refused handoff or check says it directly. Test: *(c) a write the sidecar
refuses as another reading's is said honestly* (a refused second-pane highlight).

### The audit, round 5 (each row: the backend guard, and where its SourceIdentity comes from)

| # | action | backend guard | SourceIdentity from | test |
|---|---|---|---|---|
| 1 | Ask (routed, the pane's composer) | `reader.ask`: span + selection spans in the reading | `AskAnchor.about` (the pane's section) | existing side Ask tests; pytest `test_ask_and_answer_mode` |
| 2 | Follow-up, another way, that didn't help | `reader.ask`: also `parent_exchange_id` asked in the reading | the parent's `about` | round 4 reconnect test; pytest (parent of another reading) |
| 3 | resolved / dismiss / reopen | `reader.set_inquiry_status`: exchange in the reading | `exchange.extractionId` | F1 tests; pytest `test_inquiry_status_reconnect_and_quick_check` |
| 4 | revisit once / make it something I can do | `reader.invoke_preset`: selection + subject + source/revision | `exchange.about` | F1 test; pytest `test_invoke_preset_commitments_and_requests` |
| 5 | Branch done | none (a question event id, no passage) | — | round 4 reconnect test |
| 6 | Reconnect answers, quick check, its read-back | `reader.reconnect_answer`, `reader.inquiry_question`: exchange in the reading | `extractionOf(root)` | round 4 reconnect test; pytest |
| 7 | Preset | `reader.invoke_preset` | the pane's capture target (`PaneCaptureTarget`, its section) | existing; pytest |
| 8 | Highlight / note (box; CA6 bar) | `reader.capture` / `reader.create_annotation`: selection + source/revision | the pane's target / section | existing; *(c)*; pytest `test_capture_and_create_annotation` (+ matching case unchanged) |
| 9 | Import exercise | `reader.import_exercise` (and the workbench's import): selection + source/revision | the pane's target | existing; pytest `test_import_exercise` |
| 10 | Work through an imported exercise | `workbench.open`: spans in the reading | `ExerciseImportState.identity` (required) | round 4 *finding 1*; pytest `test_workbench_open` |
| 11 | Work through this (box), the path's *try it* | `workbench.open`: spans, import selection, import reading = problem reading, import source/revision | the pane's target / the path exercise's import request | F7, F8 round 3; pytest |
| 12 | Reading path depth / override | none (no passage ids) | `ReadingPathCard`'s reading prop | F7 |
| 13 | Active reading, another way, try first | `reader.active_question`: spans in the reading | the pane's `useActiveReading` (kept through pauses, finding 3) | existing; *finding 3*; pytest `test_route_intent_and_active_question` |
| 14 | The intent routing | `reader.route_intent`: spans in the reading | the pane's reading | existing; pytest |
| 15 | Figures (box; show me) | `reader.figure_request` / `figure.request`: anchor spans + region, reading place | the pane's `useFigures` | existing; pytest `test_figure_requests` |
| 16 | Cue marks: impressions, taps, fewer, discovery, preferences | none (cue ids and the reading; no passage ids written as identity) | the pane's render (`{sourceId, revisionId, extractionId}`) | F4, F5, F12 round 3 |
| 17 | check me on a mark | handoff reading guard (client) + `workbench.open` (server) | `CueCheckMeRequest.reading` = the mark's render | F8 rounds; *finding 2* tests; pytest |
| 18 | Library ask from the pane | `reader.library_ask`: anchor spans in the reading | `LibraryAskRequest.identity` (the pane's section) | existing; pytest `test_library_ask_compare_and_tutor_pins` |
| 19 | That answer's comparisons; *where else* | `reader.library_compare`: anchor spans in the reading, the leading source the reading's, pins key by key | `LibraryAskRequest.identity` / `CompareRequest.identity` (kept by every follow-on) | round 4 audit test; *finding 1*; pytest |
| 20 | That answer's practice pick | `workbench.open` via the shell's check | the request's identity → `checkBeside` | round 4 audit test |
| 21 | how do my other books treat this? | `reader.library_compare` | `CompareRequest.identity` = the pane's section | existing; pytest |
| 22 | Tutor offers: next step, show me, make explorable, compare, practice | `reader.active_question`, `figure.request`, `reader.figure_request`, `reader.library_compare`, `workbench.open` | `exchange.about` (`AskAbout extends SourceIdentity`) | round 4 audit tests |
| 23 | show me ▸ from the Ask rail | `figure.request` (reading place in its reading) | the parent's `about` / the composer's anchor | round 4 audit test |
| 24 | Library pins and the pinned tutor | `reader.library_compare`, `reader.library_ask_tutor`: each key's span in its reading | the keys themselves | pytest |
| 25 | show passage, citations | none (navigation) | not offered for another book; citations open their own book | round 4 audit test |
| 26 | The shell's way back, the session-start remount | — | `ReaderReturn.reading`, `ReaderOpenSource.reading` (the check's reading) | `App.today.test.tsx`; `readerWorkbench.test.ts` |

### Gate (fix round 5)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`; pytest also under `flock /tmp/learnloop-fullsuite.lock`. One test run at a time, with TMPDIR
outside the worktree.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`): every test file that calls a guarded RPC or handler, plus `test_desktop_rpc_contract.py`,
  `test_mobile_allowlist.py`, `test_architecture.py` and the new `test_reader_source_identity_guard.py`: 82 files,
  **7235 passed**. A first run, before the two workbench fixtures seeded their reading, had 51 failures: 49 in
  `test_reader_workbench_rw2a.py`, 1 in `test_workbench_check.py` and 1 in `test_figures_rpc.py`, all fixed as
  described in (a).
- No DB write path changed shape (the guard refuses before writing), so no durability run. No migration, so no DB
  reference regeneration. `src-tauri` is unchanged, so no cargo check.
- Frontend: `npm run typecheck` clean. Vitest (`--maxWorkers=4`), the same 122-file set (no new test file):
  **1330 passed of 1331**. The one failure, `figures/sketch/SketchFigure.test.tsx` *draws a new sample with another
  seed*, is the known timing flake of the QuickJS sketch sandbox under load: it passed alone (19/19), and it does not
  touch any changed file. The set is 1325 + 6 new (4 in `sideBySideIntent.test.tsx`, 1 in
  `comparePointTableCodexReview.test.tsx`, 1 in `ReaderScreen.workbench.test.tsx`; the App assertion was added to an
  existing test). `npm run frontend:build`: ok.
- Open item 1 (desktop catalog at landing) is unchanged. No new TS/TSX file was added. Two Python modules were added:
  `src/learnloop/reader/source_identity.py` and `src/learnloop_sidecar/source_identity.py`.
