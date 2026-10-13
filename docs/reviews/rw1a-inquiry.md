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
