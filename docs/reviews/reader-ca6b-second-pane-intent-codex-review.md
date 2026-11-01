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
  has 36 tests (7 new and 3 rewritten in this round), `App.today.test.tsx` 24 (1 new), `readerWorkbench.test.ts`
  1 new and `returnStack.test.ts` 1 new. `npm run frontend:build`: ok.
- Open item 1 (desktop catalog at landing) is unchanged. No new TS/TSX file was added in this round.
