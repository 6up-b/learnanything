# UX fix stage 4: phone small fixes

Stage 4 of the UX journey audit's fix stages (`ux-journey-audit.md` §10, row 4): proposal P9 and findings F11, F13 and F19, with F9's labels carried to the phone. Branch `ux/stage4-phone-small-fixes`, from stage 3's branch at `97b21c6d26`, one commit per item. Judged against `ux-journey-audit-criteria.md`. Phone frontend only (`apps/learnloop-mobile/src`). No host, sidecar, schema, config, tag or prompt change, and nothing changes in what is sent to a model or what the host accepts. The service worker and the reader cache are untouched. The router's line on the phone's Today (F14) is not in this stage and is unchanged.

| Item | Commit | What |
|---|---|---|
| 1 | none: **stopped** | P9/F11: pairing at once after the scan needs a change outside `apps/learnloop-mobile/src` |
| 2 | `887ed20e40` | F13: capture says when it was sent, and keeps saying it; a look that didn't finish says what next |
| 3 | `5bdb0d0b35` | F19: the Today tab always opens the plan, a draft behind "Resume your answer" |
| 4 | `fef8dbaeca` | F9 on the phone: each duration says what it measures |

This record is the last commit.

## Item 1 (P9, F11): in after the scan. Stopped

**What the learner saw** (phone-1 #1-5, phone-2 #1-3). The QR link opened a page titled "Pair this device" that said "Run learnloop-mobile pair on your desktop. Scan its QR code or enter the manual code here.", with an empty "Manual code" box and a "Device label" of "Phone". Nothing said the scan had worked. Pair did work (the secret was in the link). Then came "Paired. Keep this token private; it is shown only once." and "Copy this token into your private Shortcut setup:", and only then "Open LearnLoop".

**What the QR link carries** (`src/learnloop_mobile/cli.py:68`, `pair`):

```python
url = f"{settings.base_url}/pair#s={result['secret']}"
```

`result` comes from `learnloop.capture.devices.create_pairing`. The secret is `secrets.token_urlsafe(32)`, and the manual code is 10 characters from a 32-character alphabet. Only their hashes are stored, in one `mobile_pairings` row with `expires = (at + timedelta(minutes=5))`. The command's default is `scope: str = "capture"` (`cli.py:58`). phone-2's step log shows the link as opened: `"open", "url": "http://127.0.0.1:43555/pair#s=…"`.

**What the host requires.** `GET /pair` serves the host's own packaged page, not the phone app (`src/learnloop_mobile/host.py:376-377`):

```python
if (method, path) == ("GET", "/pair"):
    return Response(self.assets["pair.html"], media_type="text/html")
```

The assets are `src/learnloop_mobile/static/pair.html` and `pair.js`, read at startup (`host.py:296`). `pair.js` reads `#s=` and replaces the address with `/pair`. When Pair is pressed, it posts `{device_label, secret}`. `POST /pair` accepts exactly one of `secret` or `code`, plus an optional `device_label`, each a string of at most 256 characters (`host.py:435-443`):

```python
if set(data) - {"secret", "code", "device_label"}:
    raise HostError(400, "invalid_request")
if sum(key in data for key in ("secret", "code")) != 1:
    raise HostError(400, "invalid_request")
```

`exchange_pairing` (`devices.py`) then refuses a pairing record that is unknown, consumed, expired, or has 5 failed attempts. It also refuses while the global lock is on. Otherwise it consumes the record and returns `{device_id, scope, token}`. For `scope == "app"`, `pair.js` then shows "Open LearnLoop", linked to `/app/#token=…&device=…`. The app picks that up in `store/credential.ts` (`pickUpFragmentToken`).

**Why pairing at once would change nothing the host accepts.** The link already carries everything the host needs: the one secret, which is single-use and lasts five minutes. Pairing at once is the page sending the same `POST /pair {secret, device_label}` on load, without waiting for a press. The record, the hash check, the expiry, the attempt cap and the lock stay the same, and so does the token returned. Pair is a press on the page, not a check the host makes.

**Why it stopped.** The page a scan opens is the host's `src/learnloop_mobile/static/pair.html` + `pair.js`, outside `apps/learnloop-mobile/src`. The phone app's own `PairScreen` (`/app/`) never sees a `#s=` link: it pairs only by the manual code. The brief's words ("Paired · this phone is "Phone"", the manual code under *no camera? enter a code*, "token" and "Shortcut" only on the Shortcut page) are all on that host page. They could be done in either of two places, both outside this stage's tree:

- (a) `static/pair.js` posts at once when `s` is present. On `scope == "app"` it goes straight to `/app/#token=…&device=…` (`location.replace`). `pair.html` gets the new words, with the code field under a disclosure. The token box and its words show only for `scope == "capture"`.
- (b) `cli.py` points the QR at `/app/#s=…`, and the app's `PairScreen` exchanges the secret itself.

Either way the host keeps accepting exactly what it accepts now.

Facts for whoever takes this on:
- The CLI's default scope is `capture`. A QR from plain `learnloop-mobile pair` hands over a Shortcut token, and pairing at once cannot open the app with it.
- With (a), on iOS a home-screen app keeps storage apart from Safari's (the `PairScreen` comment, mobile v2 §4.2). The fragment hand-off works in the browser tab the scan opened.

Nothing was changed for this item.

## Item 2 (F13): sure it arrived

**What the learner saw** (phone-2 #31-53, with UX-9). Stage 1 made capture say "Sent to your desktop.", but not when. The line was the screen's own state, so leaving Capture and coming back showed nothing about the last capture. On feedback (phone-2 #11), "The look into this answer didn't finish. Your grade stands." said what failed, not what to do.

**What the code did.** `capture/CaptureScreen.tsx` `CaptureScreen` kept `last` in `useState`, and Capture unmounts when another tab is chosen (`App.tsx`: `tab === "capture" ? <CaptureScreen …/> : null`). `practice/FeedbackScreen.tsx` printed the failed line as fixed text. The reply carries only `diagnosisStatus: "failed"`: no retry offered to the learner, and no reason.

**What they see now.**
- After a capture the desktop takes: **"Sent to your desktop · just now."**, then **"Sent to your desktop · 2 min ago."** and so on (**"· 1 hour ago"**, **"· N hours ago"**). It is a `role="status"` line that re-reads the clock every 30 s while Capture is on screen.
- The time comes from the record's own `capturedAt` when its first send took it. For a capture that waited on the phone, it is the moment this phone saw the desktop take it. That is memory only: nothing new is stored on the record.
- The app (`App.tsx`, `lastCapture`) now holds the last capture, not the screen. Leaving Capture and opening it again while the app is open shows the line again. The app's own flush (on open, on focus, every minute) settles it while Capture is closed (`settleLastCapture`).
- A capture known to be sent is never also counted in "N waiting to send." (the app's flush can learn it a moment before the screen reads the outbox).
- "Saved. Sending to your desktop…" and "Saved on this phone. It goes to your desktop when it's in reach." are unchanged.
- Feedback with a look that didn't finish: **"The look into this answer didn't finish. Your grade stands, and nothing is needed from you: Next goes on."** (`DIAGNOSIS_FAILED_LINE`, `role="status"`).

**Tests:**
- `src/capture/Capture.test.tsx` › capture and the desktop being away (§7) › `F13: the sent line says when, from the capture's own time, and is still there after leaving Capture and coming back`
- same › `F13: a capture that waited on the phone says it was sent when the desktop took it, not when it was saved`
- `src/practice/Feedback.diagnosis.test.tsx` › the diagnosis on the feedback screen › `F13: a look that didn't finish says nothing is needed and Next goes on, as a status line in plain words`
- changed to the new words: the two UX-9 tests (`SENT_NOW`) and `shows nothing extra without a diagnosis, and says so when one failed` (a prefix match); `src/shell/a11y.test.tsx` gains the row `capture, after a capture was sent` (deny-list and named controls).

**Fail-first.** 3 failed, 11 passed. Both capture tests failed with `Unable to find an element with the text: Sent to your desktop · just now.`. The feedback test failed with `Unable to find an element with the text: The look into this answer didn't finish. Your grade stands, and nothing is needed from you: Next goes on.`.

## Item 3 (P9, F19): the Today tab always opens the plan

**What the learner saw** (phone-2 #40-43). From Read, the Today tab opened the unfinished question. The person wanted "Something else would help", which is on the plan, and said "Today took me straight back to my draft…". They then had to press Back to Today to reach the plan.

**What the code did, and why.** `App.tsx` keeps Today's stack (`view`) mounted under the other places, hidden, so an open question keeps its editor, its serve and any submit in flight. That is M2a's design (`App.tsx` §4.2 comment; Recovery F5, "ordinary navigation keeps the draft, with no second serve"). The tab bar's `onSelect` was `setTab`, so Today showed whatever the stack held: the question. The chevron's Back set `view` to Today, which unmounted the question (saving its draft on the way out) and showed the plan.

**What they see now.**
- The Today tab, from another place, shows Today's own screen: the plan, or the queue with the plan off. The tab bar is visible and no Back covers it (`selectTab`, `planFront`).
- The question stays mounted under it, hidden, exactly as it was under Capture or Read. Its editor, its draft and its serve are untouched.
- When a draft waits (typed words, the phone's own copy or the checkpoint's), the plan shows **"Resume your answer ▸"** (accessible name "Resume your answer"). It is a full-width plain button in the thumb zone, above the primary action, which is unchanged. Pressing it shows the question again as it was, with no second serve.
- Back to Today from a question with a draft now also offers "Resume your answer". It reopens the same target on its draft (`parked`). Back still saves the draft at once, as before.
- The entry is shown in every state of the plan: open, the stop offer, a plan still reading, and a plan that couldn't be read. It is also on the queue's Today with the plan off.
- Not changed: while an answer or a skip is on its way (`questionBusy`), the Today tab still shows the question until the reply lands, as Back is disabled then (M2a's F1). Feedback and the grading wait are not drafts and keep their place.

**Can a draft be lost or hidden by this?** No. Via the tab, the question is never unmounted, so nothing is saved or discarded that wasn't before. Via Back, the path is the one that already existed, with an extra way back. The plan's Next is unchanged: phone-2 #26 shows it returning to the question with the draft kept.

**Tests** (`src/today/Today.plan.test.tsx` › the Today tab always opens the plan (F19)):
- `F19: from another place, the Today tab opens the plan with Resume your answer, which brings the draft back` (also: no `next_plan_item` or `get_practice_item` call from leaving or resuming; the answer submits under its plan presentation `pp_i1`)
- `F19: Back to Today from a question with a draft offers Resume your answer too, which reopens it on the draft`
- `F19: with nothing typed there is no draft to resume: the plan shows its Next only`
- `F19: an answer on its way is not left: the Today tab shows it until its reply lands` (a pin: it passed before the fix)
- changed, because they pinned the old tab behaviour:
  - `src/practice/Recovery.test.tsx` › F5 `a visit to Capture leaves the open question as it was, with no second serve` now goes through "Resume your answer" and still asserts no second serve and the draft kept.
  - `src/shell/Shell.test.tsx` › `a question covers the tab bar, with Back to Today and Capture in the top bar, …` now expects Today's own screen, no Back to Today, and the fragment `#/today`.

**Fail-first.** First run: 3 failed, 1 passed (the pin), e.g. `Unable to find an element by: [data-testid="today-sentence"]` and `Unable to find role="button" and name "Resume your answer"`. With the final test versions against the pre-fix code: 5 failed, 1 passed. The two changed tests also failed there (`Unable to find role="button" and name "Resume your answer"`, `Unable to find role="button" and name /^Next: Topic i1/`).

## Item 4 (F9 on the phone): one clock

**What the learner saw** (phone-2 #22-54). "About 8 minutes left" never changed across answers. It is not a countdown: `minutesLeft` is the budget less the estimates of the blocks chosen so far.

**What the code did.** `today/planWords.ts` `planSentence` and `doneLine` used the desktop's words from before stage 3. Nothing computed changes; the labels do, in the desktop's stage 3 words (`app/todayPlan.ts`).

| Where | What it measures | Old label | New label |
|---|---|---|---|
| Plan sentence, not begun | `minutesBudget`, an upper bound | "25 minutes today: 3 short questions from earlier days." | "Up to 25 minutes today. First: 3 short questions from earlier days." |
| Same, router objective (RO4) | `minutesBudget`, a suggestion | "About 25 minutes suggested today: …" | "About 25 minutes suggested today. First: …" |
| Plan sentence, begun | `minutesLeft`, the room not yet given to a block | "About 18 minutes left today: …" | "Room for about 18 more minutes today. Next: …" |
| Same, RO4 | the same | "About 18 minutes left of today's suggested time: …" | "Room for about 18 more minutes of today's suggested time. Next: …" |
| Same, RO4, past the suggestion | `minutesPastPlan` | "About 6 minutes past today's suggested time: …" | "About 6 minutes planned past today's suggested time. Next: …" |
| No block chosen yet, more projected | — | "25 minutes today: more to choose as you go." | "Up to 25 minutes today. The rest is chosen as you go." |
| Done and the stop offer | `day.actualMinutes`, time spent answering (and reading) | "Done for today · 26 minutes." | "Done for today · 26 minutes spent answering." (with reading blocks: "… spent answering and reading.") |
| Minute chips (plan, before a session) | the plan's minutes for today | "10 min 25 min 40 min" (group "Minutes today") | unchanged, as on the desktop |
| Queue mode (plan off) | the session's minutes | "How long have you got?" 10/15/25 min | unchanged (never beside the plan's sentence) |

The phone names only the block in hand, so it says "First:" / "Next:" where the desktop says "Planned so far:" over a list. Elsewhere it uses the desktop's words. The phone shows no session summary with minutes ("Session finished: N answers."), so there is no counterpart to the desktop's "N minutes this session".

**Tests:**
- `src/today/planWords.test.ts` (new) › UX fix stage 4, F9 on the phone: each duration says what it measures:
  - `before the plan is begun, its number is the plan's length, an upper bound, and the block is the first planned`
  - `once begun, the minutes not yet given to a block are room, not a countdown`
  - `the router objective's suggestion says it is one, before, during and past it`
  - `with no block chosen yet, the rest is said to be chosen as the plan goes`
  - `done says the time spent answering (and reading, when there was reading), not the session's length`
  - `every one of these sentences is in plain words` (a pin)
- `src/today/Today.plan.test.tsx` › Today is the plan (J1) › `F9: a begun plan names its room, not a countdown, and the done line the time spent answering and reading`. Changed to the new words: `says the plan in one sentence, and Begin starts a session and serves the plan's step`.

**Fail-first.** Unit tests: 5 failed, 1 passed (the plain-words pin), e.g. `expected 'About 18 minutes left today: 3 short …' to be 'Room for about 18 more minutes today.…'` and `expected 'Done for today · 26 minutes.' to be 'Done for today · 26 minutes spent ans…'`. Render tests against the pre-fix `planWords.ts`: 2 failed (`Unable to find an element with the text: /^Up to 25 minutes today\. First: …/`, `expected 'About 8 minutes left today: 1 short q…' to match /^Room for about 8 more minutes today\…/`).

## Plain words

Every new sentence is checked with the desktop's `findJargon` in its test, and the capture screen's plain-words row now renders a sent capture. "token" and "Shortcut" are not in any new phone word. The phone's `PairScreen` still says "That code is for the Shortcut." for a Shortcut-scope code: it is the only place the app meets one, and item 1 is stopped.

## Sidecar and host

No change. No ledger row: nothing found here is a defect outside the audit. The race between the app's flush and the capture screen's own read showed up in this stage's own change and was fixed before its commit.

## What was run

Every command ran through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME and config dir) inside `systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time, in `apps/learnloop-mobile`. No Python was changed. The only Python started was one accidental `python3 -` with an empty heredoc (no input, no effect), outside the wrapper. No model was called.

| Command | Result |
|---|---|
| `npm ci` | exit 0 (esbuild's install script blocked by allowScripts; vitest and the build run) |
| `npx vitest run --maxWorkers=4 <files>` while iterating | fail-first and passing runs per item, as above |
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=4` (the whole phone suite) | 32 files, 371 tests passed |
| `npm run build` | exit 0, `✓ built in 830ms`, with Vite's chunk-size warning (main chunk 706 kB; not compared with the base). It writes the gitignored `src/learnloop_mobile/static/app/` of this worktree. |

## What a phone walk must check

- **Item 2, phone-2 #31-53.** Save a capture: "Saved. Sending to your desktop…", then "Sent to your desktop · just now.". Go to Today or Read for a few minutes and come back: "Sent to your desktop · N min ago." Save one with the desktop away: the waiting line shows. Leave Capture, let the desktop come back (focus the app), then reopen Capture: it says sent, and when.
- **Item 2, phone-2 #11.** A feedback whose look didn't finish (needs real models, or a failed diagnosis): the new line, and Next goes on.
- **Item 3, phone-2 #26 and #40-43.**
  - Half-type an answer, go to Capture or Read, tap Today: the plan, with "Resume your answer ▸" above Next, the tab bar showing, and "Something else would help" reachable. Resume: the same question with the words as typed, the cursor where expected. Submit: graded as one answer.
  - Back to Today with a draft, then Resume.
  - Tap Today while an answer is being graded: the question or grading screen stays.
  - Check VoiceOver does not read the hidden question under the plan.
- **Item 3, the plan's Next with a draft waiting.** Press Next instead of Resume. It should return to the same question with its draft (as #26). If the plan serves another item instead, the draft stays on record but is no longer offered: report it.
- **Item 4, phone-2 #22-54.** Before Begin: "Up to N minutes today. First: …". After a block: "Room for about N more minutes today. Next: …". The done line or the stop offer: "Done for today · N minutes spent answering." Compare with the desktop's Today for the same plan: the same words for the same numbers.
- **Item 1** is not changed: the pairing page is as phone-1 #1-5 saw it.

## Not verified here

- Nothing was walked or launched: no app, browser, dev server or phone host. Rendering, layout, focus and VoiceOver were verified only in jsdom. That includes the hidden question under the plan, which is `display: none`, as under the other places.
- Whether the plan's Next, pressed while a draft waits, always returns to the same question. The engine was not read for every block state; phone-2 #26 is the evidence.
- The "· N min ago" line across a phone sleep. While hidden, the page does not tick; it reads the clock again on focus and on return.
- How `settleLastCapture` behaves when two captures are saved in quick succession. Only the last one is tracked, as in stage 1.
- The tests' timing uses a shifted `Date.now`. A real wait of minutes was not run.
- Item 1's options (a) and (b) were not built or tried.
