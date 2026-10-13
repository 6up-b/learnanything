# Reader workbench RW1a: Inquiry (stage `rw1a-inquiry`)

Branch `reader/rw1a-inquiry`, base `main` at `09c9f8d3` (`mvp-0.16`,
migration head 183). Spec: `docs/specs/spec_reader_workbench_v1.md` (RW1a
scope, §4.1, §4.3, §13 row RW1a, §14 gates G1, G2, G4, G51, G52, G54-G57),
presentation in `docs/specs/ux_reader_workbench_v1.md` (§3.1-3.5, §4.0,
§4.2, §4.12, §7; wireframes W1, W3, W4).

## 0. Plan

Order (each step lands with fail-first tests, Python and vitest):

1. **The friction audit of today's Reader** (§1 below), written before any UI
   change (G52).
2. **K7 first** (`docs/specs/ux_learnloop_v1.md` §12.2): a bare Alt press
   clears the capture on *keydown*, so every Alt chord (`Alt+←`, `Alt+drag`
   on the text column, `Alt+Tab`) loses it. The clear moves to the Alt
   *keyup* and only when no other key or pointer button was pressed while Alt
   was held.
3. **Port `origin/feat/reader-clarification-branches` (`cf2cbe77`)** onto
   `main`, keeping its contract (`reader.ask.parentExchangeId` is the
   parent's `readerAnswerEventId`; the parent's saved selection overrides the
   current one; only ancestors enter the prompt, the latest 12, with omitted
   counts in the manifest; the rail shows the tree with search, expand, new
   thread and return-to-passage). It composes with what landed since:
   - T6: the Reader context still uses no retrieval provider (that is
     RW1c), so a follow-up's "retrieval" is today's selection-and-neighbours
     set of the inherited anchor; the T6 `learning_object_suggester` and its
     `suggested_learning_objects` pass through unchanged;
   - learner-text gaps: `learner_gap` is still read from the answer and
     queued by the handler (`queue_tutor_question_gap`) for every exchange,
     follow-ups included;
   - the T6 follow-up's output-budget policy and tutor timing: untouched
     (they live in the provider transport and `_provided_source_spans`,
     which the reader path does not call).
4. **The rail split** as a move: `screens/reader/AskRail.tsx`,
   `GuideRail.tsx`, `NotesRail.tsx`. The existing `ReaderScreen` tests pass
   unchanged, plus the branch's.
5. **Inquiry status, the detour strip and reconnect.** Status is the root's
   `question_events.resolution` (reopen included); the return stack is visit
   state with `Alt+←`/`Alt+→`; the reconnect line shows inline under the root
   passage (on a return the learner started) and at the top of the inquiry,
   with *yes · still unclear… · quick check*.
6. **The one migration** on `reader_authored_questions` (`scope_kind`,
   `question_style` with all five values, `anchor_span_ids_json`,
   `inquiry_root_event_id`, `self_check`); the section lookups filter
   `scope_kind = 'section'`.
7. **The shared pieces**: voice components (source `§`, model `◇`, learner
   `›`), evidence and check markers, the seven-state model-action component,
   the static `◆ n` quick-check marker (the pulse, blink and strip removed for
   every learner), meaning-bearing copy on `--dim`.
8. **`learnloop reader report`**: the workflow funnel with denominators.
9. **Transcript and notes parity**: every RW1a behaviour on the extracted
   text, the original-PDF surface, a video transcript and a text-file
   source.

Kill switch `reader_inquiry.enabled` (default on). Off: today's flat rail and
byte-identical results from every RPC RW1a touches. No algorithm successor
(content and display). No new `interaction_events` kind and no new reveal
kind: payload `event` fields on existing kinds.

## 1. Friction audit, before (today's Reader, `main` at `09c9f8d3`)

Read from the code (`screens/ReaderScreen.tsx`, `components/PdfReaderPane.tsx`,
`components/QuestionQueue.tsx`, `app/App.tsx`, the reader RPCs). No funnel
data exists yet: the Reader logs no visit, selection or detour events today
(`reader_view_opened`, `reader_selection` and `reader_action_invoked` are in
the firewall vocabulary but nothing writes the first two from the UI). Keys
are checked against the UX key map (UX §3.5). "Step" counts each distinct
learner act (a drag, a click, a typed text, a key).

| # | Workflow | Steps | Keyboard (UX §3.5) | Waits on a model | Focus moves / rail changes without the learner's act | Context lost |
|---|---|---|---|---|---|---|
| 1 | **Ask about a selection and get back to reading** | 5-6: select (drag) · the rail flips to Notes · click the *ask* tab · click the box and type · click *ask ↵* · read · keep reading | **No.** A keyboard selection (Shift+arrows) is never captured: only `onMouseUp` and the ctrl-marquee commit a selection. No key switches rail tabs (`[`/`]` absent). The *ask ↵* label promises Enter, but the box has no key handler: Enter types a newline | The tutor answer (provider wall time, typically several seconds). Pending shows only as a disabled button; nothing says what is happening | **Rail:** selecting text flips the rail to Notes unless Ask is open (`ReaderScreen.tsx:1094`, `:1237`, `:2127`). **Focus:** when the answer lands, focus jumps back into the composer (`requestAnimationFrame(() => askComposerRef.current?.focus())`) | None in the source (the page does not move). The answer lands at the top of a flat "Previous asks" list |
| 2 | **Follow one prerequisite and return** | 8-12: ask (as 1) · find the prerequisite (Contents click, or scroll) · select it · ask · scroll or click Contents back to the original passage · re-find the original exchange in the flat list. In another source: *← library* · type a search · Enter · click a hit · ask · *← library* · click the first source | **No** back key: `Alt+←` is unbound, and pressing Alt clears the capture (K7). Contents rows are buttons (Tab-reachable); library cards are `div`s with `onClick` (not focusable) | Each ask; the library's deep search on Enter (query rewrite and embedding) | Rail flips to Notes on each selection (as 1). Opening another source resets the rail to Guide | **Yes.** The two questions are unrelated siblings: a follow-up is not linked to its question (history is flat; the tutor sees every earlier exchange on the same span, related or not). Scrolling to the prerequisite overwrites the saved reading position, so there is no way back to "where I was" except scrolling. Leaving for another source drops the selection, the Ask draft and the expanded exchanges (`resetSourceState`) |
| 3 | **Import and work an exercise** | 6+: select the exercise (ctrl-drag boxes) · rail flips to Notes · click *add exercise to practice* · wait for the cards · leave the Reader (top nav) · find the item on Today when it is scheduled · work it on the practice screen | Selection by keyboard: no. Notes actions have no keys (Tab-reachable buttons only) | The import (a background authoring job, tens of seconds; shown as "◐ authoring practice…" and polled every 2 s); then grading after submit | Rail flips to Notes on selection | **Yes.** Working happens on the practice screen away from the book (RW2a's problem); nothing links the item back to the passage from the Reader |
| 4 | **Find where else an idea is explained** | 5-7: *← library* · type a query · Enter (deep) · click a hit · read · *← library* · click the first source | Search box: yes (typing, Enter, Esc). Hits and library cards: mouse only (`Card onClick`, not focusable). No `Ctrl+Shift+F` | The deep search (rewrite + embedding) | Opening a source resets the rail to Guide | **Yes.** Search exists only on the library screen, so leaving the open source is required: selection, Ask draft, expanded exchanges and the rail tab are reset; returning restores only the saved reading position |
| 5 | **Capture "test me later"** | 2-3: select · (rail flips to Notes) · optional note · click *test me later* | Selection: mouse only. The preset is a Tab-reachable button; no key | None (local capture; any synthesis is queued in the background) | Rail flips to Notes on selection (here it helps, but it is not the learner's act) | None. The receipt and the "You'll see this again" card appear in Notes |
| 6 | **Resume after a restart** | 2: open the Reader (top nav) · click the source card | Top nav keys exist; the source card is a `div` with `onClick` (not keyboard-reachable) | None | Rail resets to Guide | **Partly.** The open source lives in App state only (`App.tsx:86`), so a restart lands on the library picker. The reading position comes back (localStorage per source); the selection, rail tab, Ask draft and which exchanges were open do not. Ask history rehydrates collapsed |

Also found while auditing:
- **The quick-check signal animates without end** for every learner (the
  Guide tab's `ll-reader-guide-alert` pulse, the blinking `◆` and the pinned
  uppercase strip; stopped only under reduced motion), against the attention
  budget (UX §4.12). The PDF pane's block paint also has a 120 ms transition.
- **Much meaning-bearing microcopy is `--faint`** (about 3.5:1 on `--bg`):
  "optional · self-check, never a grade", "answers now, grounded in the
  selected passage", the request status lines.
- **Open reader questions on Today open in the global Ask overlay**, not in
  the Reader at their passage (UX K6; not RW1a's to change, recorded).
- **Inquiry status has no UI in the Reader.** `resolve_question_event`
  already accepts `open`, so reopen exists in the backend (the spec said it
  did not; §3.1 "there is no reopen" is wrong for the service, right for the
  UI). Today's queue offers only *resolved* and *dismissed*.

## 2. What was built

Commits on `reader/rw1a-inquiry` (base `09c9f8d3`), each behaviour with its
fail-first tests committed before it:

| Commit | What |
|---|---|
| `fb3d98e7` | This plan and the friction audit (§1), before any UI change (G52) |
| `beec8db6`, `5442c95d` | **K7.** `screens/reader/bareAlt.ts`: a bare Alt clears the capture on *keyup*, and never when a key, a pointer press or a window blur happened while Alt was held, nor while typing. Alt+←, Alt+drag sweeps and Alt+Tab keep the capture |
| `1f8003df`, `42d27406` | **The port** of `cf2cbe77` behind the new `[reader_inquiry] enabled` (default on): `reader.ask.parentExchangeId`, server-resolved ancestors (latest 12 in the prompt, omitted count in the manifest), the parent's saved selection, fail-closed parents, `ask_history` with parents, saved selections and each exchange's question id and resolution, `ReaderAskBranches` (tree, search, expand, new thread, return to passage). Composition with main: T6's `learning_object_suggester` / `suggested_learning_objects` pass through; learner-text gaps' `learnerGap` is queued for every exchange, follow-ups included; the reader context still has no retrieval provider (RW1c), so a follow-up's spans are its inherited anchor's selection and neighbours; the T6 follow-up's output-budget policy and tutor timing live in code the reader path does not call and are untouched |
| `fb3b8493` | **The rail split**, a move: `AskRail.tsx`, `GuideRail.tsx` (with the section cards and the boundary offer), `NotesRail.tsx`, `readerShared.ts`. `ReaderScreen.tsx` 3,996 → 2,851 lines at that commit. Every existing `ReaderScreen` test passes unchanged, plus the branch's |
| `2c341597`, `73394530` | **The backend**: migration 189; `learnloop.reader.reader_inquiry` (status, reconnect, activity); the passage-scoped quick check in the producer and its job; five RPCs; `learnloop reader report`; head fixture, references, snapshots, CLI help, mobile pins |
| `dd19009d`, `84f52bee`, `abd9d008`, `f8de369f`, `a0930bbe` | **The Reader**: the return stack and detour strip, the reconnect line (inline and rail) and its quick check, status chips and branch "done", the shared voices / markers / model-action states, the static quick-check marker, `--dim` microcopy, the funnel activity, transcript and notes parity, the explicit-jump guard, a landing line for a check set aside earlier |
| `09423569` | Today's "continue the dialogue" overlay keeps its Reader thread under branches (item 7 in §5) |
| `40aa971e`, `12aa35a3`, `01273100` | The registry entry for the ported 12-ancestor prompt bound (`reader_dialogue:READER_BRANCH_PROMPT_ANCESTORS`, structural), the references regenerated after it, a durability-lane test for migration 189 |

**Data (spec §4.3).** Migration `189_reader_authored_question_scopes.sql`
(184-188 held for branches in flight; expect renumbering): `scope_kind`
(`section` \| `inquiry` \| `selection`, default `section`), `question_style`
(all five values, default `recall`), `anchor_span_ids_json`,
`inquiry_root_event_id`, `self_check` (`matches` \| `partly` \| `no`), and a
partial index on (`inquiry_root_event_id`, `prompt_version`). Columns only; no
rebuild; `reader_authored_questions` stays WORKFLOW. `latest_reader_authored_question`
and the guide's per-section read filter `scope_kind = 'section'`. Section rows
are written with exactly today's columns (the new ones take their defaults),
and their RPC payload is unchanged; scoped rows add their fields.

**Events (no new kind, no rebuild).** On `reader_action_invoked` with a payload
`event`: `action_invoked`, `detour_opened`, `detour_returned`,
`reconnect_shown`, `proactive_shown`, `back_to_reading` (recorded by the
Reader through `reader.log_activity`), and `inquiry_status_set`,
`reconnect_answered` (written by the sidecar). Plus `reader_view_opened`,
`reader_view_closed`, `reader_selection`, `reader_job_queued`,
`reader_job_completed` (the last two were in the envelope's CHECK since 091 but
never written; they join the firewall vocabulary), and `reader_source_restored`
through the existing `reader.restore_source` when a walk reaches its origin.
Activity payloads keep only ids, kinds, counts and timings; the learner's words
and quotes are dropped server-side. Every row is `salience_only`; the
salience-firewall cases are in `tests/test_reader_activity.py` (one per kind
and per event value).

**RPCs** (desktop only, pinned in `tests/test_mobile_allowlist.py`; all gated
on `reader_inquiry.enabled`, refused with `inquiry_disabled` when off):
`reader.set_inquiry_status`, `reader.reconnect_answer`,
`reader.inquiry_question`, `reader.inquiry_question_action`,
`reader.log_activity`. Extended (pinned too): `reader.ask` (parent; the
answering model, for the report), `reader.ask_history`,
`reader.prompt_contract` (`inquiryEnabled`).

**The passage quick check.** Same operation (`reading_quick_check`), route
and caps as the section check, prompt `rw1a-reading-passage-check-v1`, context
= the root's anchor spans plus one block before and two after inside the
anchor's section (no learner text). Reuse per (root exchange, prompt version);
a dismissed row suppresses re-authoring. Answering stamps the response, the
learner's verdict lands in `self_check`; nothing else is written. "Partly" and
"no" become `reader_formative` learner text in RW1b, not here.

**The Reader (reader_inquiry on).** The return stack (`returnStack.ts`):
branches, peeks at shown or cited passages, and another source opened from a
library search push entries; `Alt+←`/`Alt+→` and the strip's crumbs walk it;
reaching the origin restores its passage, capture and rail tab, records
`reader_source_restored`, ends the open detours (`detour_returned`) and asks
the reconnect line. While a detour is open the saved reading position stays at
the root, so a restart restores only the root (P3 §12). The reconnect line
quotes the learner's question, inline under the root passage on the extracted
text, the original PDF page (drawn under the block's box) and the video
transcript (under the transcript passage), and at the top of the inquiry in
the rail; after a branch is marked done, in the rail only. *yes* resolves the
root (a self-report); *still unclear…* starts a branch from the root (empty:
opens the composer on the root); *quick check* lands the passage check in the
rail. A screen of the learner's own scrolling removes it, recording nothing.
Status chips on each root (resolved · revisit once · make it something I can
do · dismiss; reopen), "done" on a branch, the inquiry keys (`↑ ↓` move, `↵`
expand, `f` follow-up, `r` resolved/done, `o` reopen, `p` passage),
`Ctrl+↵` to ask, `[`/`]` rail tabs, `\` collapses the rail. The Ask's model
states render in place (pending with cancel, unreachable, capped, sidecar
down). Skim mutes the reconnect line and the section-boundary offer.

**For every learner (spec §12: display fixes, no switch).** The Guide tab's
static `◆ n` replaces the endless pulse, the blinking diamond and the pinned
uppercase strip (their CSS is gone); the PDF pane's paint transition is gone;
the shared components (`voices.tsx`: `SourceVoice`, `ModelVoice`,
`LearnerVoice`, `LearnerQuote`, `EvidenceMarker`, `CheckMarker`,
`MeaningLabel`; `ModelActionState.tsx`); model text in the rails (Ask answers,
quick-check questions and intended answers, request results) renders through
`ModelVoice`; meaning-bearing microcopy moved from `--faint` to `--dim`.

**The report.** `learnloop reader report --vault <path> [--json] [--since
<ISO time | 7d | 24h>]`, read-only (the database is opened read-only; the CLI
test checks the file's hash is unchanged), no model, no learner text:
`selection_to_reading` (selections, actions by kind, model-backed jobs with
queued / completed / failed with reasons / cancelled and latency and model
wait p50/p95, back to reading with its denominator), `inquiry` (opened,
branches, depth and breadth, resolved, dismissed, reopened, still open after 7
days, reconnect answers, quick checks with self-checks), `detours` (return
rate, by kind, cost in minutes, model wait), `proactive_load` (per reading
hour), `waiting` (share of model waits with learner activity), `visits`
(active minutes, time to first action), `routes` (per job kind, model and
prompt version).

## 3. Friction audit, after (RW1a, `reader_inquiry` on)

The same six workflows on this branch. Differences from §1 in bold.

| # | Workflow | Steps | Keyboard (UX §3.5) | Waits on a model | Focus / rail moves without the learner's act | Context lost |
|---|---|---|---|---|---|---|
| 1 | Ask about a selection and get back to reading | 5: select · (rail flips to Notes) · **`]` or click Ask** · type · **`Ctrl+↵`** · keep reading | **Yes after the selection**: `[`/`]` switch tabs, `Ctrl+↵` asks. The selection itself is still mouse-only (keyboard selection arrives with RW1b's intent box) | The answer; **now said in place**: *◐ writing an answer… · cancel*, and *couldn't reach LearnLoop's model · your question is kept · try again*, *today's tutor budget is used* | Rail flip on selection unchanged (RW1b, `reader_intent`). **A landed answer no longer moves focus** (it stays in the composer only if the learner was still there) | None |
| 2 | Follow one prerequisite and return | 6-8: ask · **`f`** on the exchange (or *ask follow-up*) · type · `Ctrl+↵` · **`p`** or a § citation to peek · **`Alt+←` (or the strip's first crumb)** · **answer the reconnect line** | **Yes after the selection**: `f`, `p`, `↑`/`↓`, `↵`, `r`, `o`, `Alt+←`/`Alt+→`; crumbs and reconnect answers are buttons | Each ask, in place as in 1 | **None**: the strip and the reconnect line appear in place; nothing takes focus | **None within the source**: the follow-up is durably linked to its question and sees only its ancestors; the strip shows `↩ origin › question › follow-up`; `Alt+←` restores the passage, the capture and the tab; while the detour is open the saved position stays at its root. Across sources: **a search hit opened after leaving a source is a detour; `Alt+←` reopens the first source at its passage with its capture** |
| 3 | Import and work an exercise | 6+ (unchanged; RW2a) | Unchanged | The import; now **counted in the funnel** (queued, completed, failed) | Unchanged | Unchanged (working still happens away from the book) |
| 4 | Find where else an idea is explained | 5-6 + **1 back key**: *← library* · search · Enter · open a hit · read · **`Alt+←`** | Search box yes; **back by key**; hits and cards still mouse-only | The deep search | Opening resets the rail to Guide (unchanged) | **No longer lost**: the way back restores the passage and capture |
| 5 | Capture "test me later" | 2-3 (unchanged), **or from an inquiry: *revisit once* on its root** | Buttons are Tab-reachable | None | Rail flip on selection unchanged | None |
| 6 | Resume after a restart | 2 (unchanged) | Unchanged | None | Rail resets to Guide | Reading position restored; **a detour open at the restart returns to its root, not to wherever the detour had scrolled**; threads come back as a tree with their status |

Also changed for every learner: the Guide tab's quick-check signal is a
static `◆ n` (no pulse, no blink, no pinned strip); nothing in the Reader
animates (the PDF pane's paint transition is gone; a lint holds it).
Proactive load is now measurable (`proactive_shown`, `reconnect_shown`).

## 4. Kill-switch parity (`reader_inquiry.enabled = false`)

Verified two ways:

1. **Against main's own code.** `parity_probe.py` (scratchpad, not committed)
   ran the same sequence -- `reader.ask` twice (the second with a two-block
   selection), `reader.ask_history`, `reader.prompt_contract`,
   `reader.author_section_question` (an existing section check),
   `reader.authored_question_action`, `reader.guide_plan` -- once with
   `main`'s source tree (`git archive 09c9f8d3 src tests migrations`) and once
   with this branch, each on a fresh fixture vault with `[reader_inquiry]
   enabled = false` and a stub tutor. After replacing ULIDs and timestamps
   with placeholders, **the RPC results and every stored reader event payload
   are identical** (`RPC-IDENTICAL`, `EVENTS-IDENTICAL`).
2. **In the suite.** `tests/test_reader_inquiry_kill_switch.py` pins main's
   key sets and values (the flat per-span thread, the `p2-reader-v1`
   manifest, no parent fields on any payload or response, the prompt
   contract without `inquiryEnabled`), a parent refused before any write,
   and that the on-mode wire adds only the branch fields;
   `ReaderScreen.inquiryOff.test.tsx` shows today's flat rail and an Ask
   sent without `parentExchangeId` and no activity logged. The five new RPCs
   answer `inquiry_disabled`.

The display fixes (static marker, voices, `--dim`) apply with the switch off
too, as spec §12 rules; the flat rail's structure and behaviour are today's.

## 5. Deviations and decisions taken (each recorded; the spec wins until the owner rules)

1. **Reopen already existed in the service.** `resolve_question_event` and
   `question_queue.set_question_resolution` accept `open` on `main` (spec §3.1
   says there is no reopen; that is true of the UI only). RW1a leaves that RPC
   byte-identical and adds `reader.set_inquiry_status`, which resolves the
   inquiry's root from any of its exchanges and logs `inquiry_status_set` so
   reopens are countable.
2. **The branch's screen test needed two composition edits** (its tests
   otherwise unchanged, G1): the contract mock names `inquiryEnabled` (the
   sidecar names the switch only when on, so an absent flag must read as off
   to keep the switched-off rail byte-identical), and its `queryCache` mock
   stubs `peek()`, which main's guide-overlay fix reads.
3. **An unexpected Ask failure still reaches the app's error line** besides the
   in-place state, because the ported branch's retry test requires it (G1).
   Model unreachable, capped and sidecar down render in place only (W14).
4. **A branch's "done" resolves that branch's own question** through the
   existing `resolve_question_event` (status chips stay on roots only). It
   removes the branch question from Today's queue, and asks the reconnect line
   in the rail.
5. **The passage check sees the passage only**, never the learner's question
   (no learner text on the producer's route); its own prompt version,
   `rw1a-reading-passage-check-v1`, on the same operation, route and caps.
6. **"Opening another source" is a detour only from a search hit** opened
   after leaving a source; a plain library card starts new reading with no
   crumb back.
7. **Today's "continue the dialogue" overlay keeps its thread.** Under
   branches a parentless Ask is a new root with no prior conversation, which
   would have emptied the overlay's context; with the switch on, the overlay
   continues the span's newest exchange, then its own answers.
8. **Skim muting and the Reader-wide keys are gated on `reader_inquiry`**;
   the static marker, the voices and `--dim` are not (spec §12 row 2). The
   voices also style today's flat rail (switch off): structure and behaviour
   unchanged.
9. **Still RW1b's**: the rail flips to Notes on selection (G57's "never
   changes the rail tab" holds only with `reader_intent.enabled`), and a
   keyboard-made selection is not captured (the intent box).
10. **"usually about N s" is never shown yet**: the component supports it,
    but no measured p50 is fed back from the report to the UI (W14: show it
    only when measured).
11. **The PDF page's inline reconnect line** (drawn under the block's box on
    its page) has no vitest: pdf.js does not load in jsdom. Covered by review;
    the text view and the transcript have screen tests.
12. **`reader.ask` names the answering model** (with the switch on) so the
    report's funnel reads per route; absent when off.
13. **`ReaderScreen.tsx` is 3,617 lines** after RW1a (3,996 on `main`; 2,851
    right after the split): the rails are out, but RW1a's orchestration (the
    return stack, reconnect, status and the funnel) lives in the screen.
    Moving it into a hook would shrink later merges; not done here to keep
    the stage's risk down (open question 6).
14. **Migration 189**, numbered past the 184-188 placeholders; expect
    renumbering at the merge.

## 6. Spec-vs-code findings

- §3.1 "there is no reopen": the service already accepts `open` (item 1 above).
- §4.3 lists `reader_job_queued` / `reader_job_completed` as existing kinds: they
  were in the envelope's CHECK since migration 091 but absent from the
  firewall vocabulary and never written; RW1a adds them to
  `READING_EVENT_KINDS` so `log_interaction_event` stamps them.
- CLAUDE.md says the head fixture has "5 hard-coded paths"; there were 15
  (12 tests, 2 scripts, the Database Catalog note). All updated.
- `ReaderScreen.tsx` was 3,996 lines on `09c9f8d3` (spec: 3,987 on `f2f02e32`).

## 7. Owner commands (no paid calls; run on a backup copy, never a tracked vault)

```sh
# A backup-API copy of a working vault to try RW1a on:
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/probability'), Path('fixtures-local/probability-rw1a'))"
LEARNLOOP_VAULT=$PWD/fixtures-local/probability-rw1a npm --prefix apps/learnloop-tauri run dev

# The funnel after a week of reading (read-only, no model, no learner text):
uv run learnloop reader report --vault fixtures-local/probability-rw1a --json --since 7d

# The kill switch, in the vault's learnloop.toml (off: today's flat rail):
#   [reader_inquiry]
#   enabled = false
uv run learnloop config effective --vault fixtures-local/probability-rw1a | grep -A1 reader_inquiry
```

The checkpoint (spec §13): a week of reading, then the funnel (return rate and
proactive load) and this audit. The optional timed walkthrough (spec §15):
ask → branch → return.

## 8. Open questions for the owner

1. Should opening a book from the library card (not a search hit) after
   leaving another also leave a crumb back? Default here: no; it is new
   reading.
2. A branch marked "done" resolves its own question, which leaves Today's
   queue. Keep, or leave branch questions open until their inquiry closes?
3. An unexpected Ask failure still shows the app's error line (the ported
   branch's contract) as well as the in-place state. Drop the error line?
4. The passage quick check does not see the learner's question. Should it, to
   check what they asked about rather than the passage in general (learner
   text would then reach the producer's route)?
5. Funnel activity is recorded only with `reader_inquiry` on. Record visits
   and selections with it off too (a tier-1 signal, no behaviour change)?
6. Move RW1a's orchestration out of `ReaderScreen.tsx` into a hook before
   RW3a/RW6a/RW2a land (smaller merges), or leave it?

## 9. Manual run on a backup copy (no model calls, no spend)

`fixtures-local/probability-rw1a`: a backup-API copy
(`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked
`fixtures/probability` at `09c9f8d3` (never the owner's live checkout), at
migration 155.

- `learnloop reader report --json` on the unmigrated copy (read-only; the
  report tolerates a database without the 189 columns): its 3 legacy Reader
  asks read as roots, open, older than 7 days; no visits or detours yet.
- A headless sidecar session (`initialize` migrated the copy 155 → 189):
  `reader.prompt_contract` reports `p3-reader-branches-v1` and
  `inquiryEnabled`; `reader.ask_history` returns the legacy exchanges with
  null parents, their question ids and `open` status; `set_inquiry_status`
  resolved then reopened the root (Today's open count 9 → 10);
  `reconnect_answer` (still unclear) recorded only its event;
  `inquiry_question` returned none; `log_activity` recorded 4 events; the
  guide plan still answers. The report then read: 3 opened, 1 resolved, 1
  reopened, 1 still-unclear answer, return rate 1/1, 1 visit, 10 active
  minutes, `learner_text: false`.

No paid call was made anywhere in this stage: every test uses fakes, and the
passage check, the only new model-backed action, was exercised with a fake
client.

## 10. Gate (exact results)

Run in this worktree with `TMPDIR=fixtures-local/tmp`; the suite and the
durability lane under `flock /tmp/learnloop-fullsuite.lock` (both waited for
other stages' runs).

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (the sync removes `pypdfium2`; reinstalled) |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| `flock … uv run pytest -n auto` | **9091 passed**, 46 warnings, 0 failed (6 min 41 s; at `12aa35a3`). The first run (at `abd9d008`) had 7 failures, all the registry audit's one unregistered constant, fixed in `40aa971e`. The one test added after this run (`01273100`, durability-marked) passed in the lane below |
| `flock … uv run pytest -m durability` | **96 passed**, 8995 deselected (at `01273100`; 95 before the new migration-189 case) |
| `npm install`; `npm run typecheck` | ok; exit 0 |
| `npm test` (vitest) | **254 passed** in 50 files. One full run of three hit a timing flake in `FeedbackScreen.test.tsx` ("drops a pending advance…", a file this stage does not touch) under the loaded machine; 5 of 5 passed alone |
| `npm run frontend:build` | built (Vite's existing large-chunk warning only) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | **exit 0** (after the five passthroughs; `src-tauri` unchanged since) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated; **errors: []** (schema head 189, 307 table notes, 756 effective leaves in 44 sections) |

Spec gates: **G1** (the branch's 8 backend tests -- 12 cases with its
parametrisation -- and 9 frontend tests pass; a follow-up's prompt holds only
its ancestors; legacy flat histories read as roots; with no retrieval provider
in the reader context, the follow-up's own question is the only query text),
**G2** (status flips, reopen, reconnect answers and the activity write no
attempt, observation, mastery or FSRS row: table-count diffs; a firewall case
per event value and kind), **G4** (scoped rows never shadow a section; reuse
keys; section quick checks byte-identical), **G51** (transcript and notes
cases in every RW1a test file, Python and vitest), **G52** (§1 before, §3
after), **G54** (focus on selection and on landing, the CSS and component
lints, the static marker, skim), **G55** (voices, markers, `--dim` in five
palettes, the two lints), **G56** (the seven states), **G57** (the return
stack, `Alt+←` to the exact passage and capture, a restart restores only the
root, the keys). G57's "selecting never changes the rail tab" and "the intent
box never takes focus" are RW1b's (`reader_intent`).

New tests: Python `test_reader_branches.py` (ported + transcript/notes),
`test_reader_inquiry_kill_switch.py`, `test_reader_inquiry_status.py`,
`test_reader_reconnect.py`, `test_reader_activity.py`,
`test_reader_report.py`, `reader_fixtures.py`; vitest `bareAlt.test.ts`,
`ReaderScreen.k7.test.tsx`, `ReaderAskBranches.test.tsx` and
`ReaderScreen.branches.test.tsx` (ported), `ReaderScreen.inquiryOff.test.tsx`,
`splitRails.test.tsx`, `ReaderScreen.inquiry.test.tsx`,
`ReaderScreen.parity.test.tsx`, `attentionBudget.test.tsx`,
`voices.test.tsx`, `paletteContrast.test.ts`, `modelActionStates.test.tsx`,
`returnStack.test.ts`, `inquiryComponents.test.tsx`,
`AskOverlay.reader.test.tsx`.
