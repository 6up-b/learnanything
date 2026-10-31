# Reader CA6: side by side

Stage `reader-ca6-side-by-side`, branch `reader/ca6-side-by-side` (base `3a96d90b4`).
Spec: `docs/specs/ux_reader_compare_ask_v1.md` §6.4, §6.5 (Records), X9, K14, C5, §13 (kill switch), §15 Q14
(follow along on by default). Data: curriculum C0a's `reader.correspondents`; entry from CA5a's find-section list.

## What ships

- **Entry, three ways** (all behind `reader.side_by_side.enabled`):
  - `s` on a focused line of CA5a's find-section list, or the line's new *side by side* button
    (`FindSection` prop `onSideBySide`; CA5's judged list can pass the same hook later);
  - *read side by side (s)* in the peek's header;
  - `Ctrl+\` from reading: `reader.correspondents` (with the search fallback, since the learner pressed) for the
    Guide section in view, then the first correspondent in the API's order. Judged coverage comes first. With
    nothing judged, it opens the first unchecked hit, and the pane says *found by search, not checked*. With
    nothing at all, one dim line under the header reads *nothing in your other books matches this section
    yet*. It goes on the next click in the book.
- **A variant of the comparing posture, with a crumb.** Opening pushes a return-stack entry of the new kind
  `side_by_side`, so the strip reads `↩ <origin> › side by side with Axler §5.A`. Walking off it (a crumb press,
  `Alt+←`, opening another book) closes the second pane. Walking back onto it with `Alt+→` reopens it without
  pushing a new crumb. Closing with `Esc`, `Ctrl+\` or `✕` takes the crumb off the stack (`returnStack.dropCurrent`)
  and moves nothing: the first pane keeps its position and returns to full width.
- **Layout** (`SideBySidePane.tsx`): two source panes. The main pane gets a sticky header
  (*§ Strang · 6.2 …*, plus *lead* when it leads and the dim stays-put line). The second pane's header has
  *§ Axler · 5.C …*, *lead*, *follow along ● (^⇧L)* and *✕*. The split is resizable (a separator,
  pointer drag) and remembered per device (`localStorage`, clamped to 25–75 %, a layout bound). The rail
  folds to its 28 px gutter, and `\` (or the gutter) reopens it as an overlay at the right. A comparison
  started while side by side is open takes the right side. Side by side comes back when it closes, since both
  are the comparing posture.
- **The second pane** reads one section of the other book at a time through the new
  `reader.side_by_side_section`. That returns the whole section from its jump locator. Protection is read now:
  an exam, held-out or non-teaching reading, or a section with any withheld span, is refused, and the pane
  never runs on into the next unit. The response also names the reading's neighbouring readable sections,
  with protected ones skipped, as *‹ previous · next ›*. **Each block returned gets one `source_exposure` row**
  (context `library`, `span_view.record_span_exposures`, as CA5a's peek), recorded before the text is
  returned. No model call.
- **Follow along** (`useSideBySide.ts`; on by default, and the toggle turns it off for the session):
  - the leader is the pane the learner last scrolled (wheel, touch, scroll keys), clicked or selected in;
    F6 alone does not change it;
  - the follower moves **only when the leader crosses into a new section**. For the main pane that is the
    Guide section in view changing. For the second pane it is the learner moving it to another section.
    On a crossing, the follower moves once, to the first of its book's **judged** correspondents in the API's
    order (`reader.correspondents` with `search_fallback: false`; an unchecked search hit never moves a pane),
    at its jump locator. The main pane gets the jump and is then put at the passage instantly (no
    animation). The second pane loads the section at its top;
  - mid-section the leader moves nothing. A follow-along answer is dropped if, while it was in flight, the
    learner touched the follower, the leader crossed again, the pair changed or follow along went off
    (crossing and opening generations);
  - with no correspondent in the follower's book, the follower stays put and its header reads
    *no matching section here · stays put* (dim) until the learner moves it.
- **F6** moves focus between the panes. **Ctrl+Shift+L** toggles follow along. **Esc** aimed at either pane
  (never a field, never while a selection or the tag menu is open, never an Esc another handler took) closes
  the second pane. All of them are window keys under `screenLeavesKey`, outside text fields, and only while
  the switch is on. Ctrl+Shift+L does not clash: the command palette's Ctrl+L is element-scoped inside the
  modal palette.
- **CA3's selection verb in side by side:** in the main pane, *how do my other books treat this?* sends
  `sourceIds: [<the second pane's book>]`. A selection in the second pane shows the verb under the pane
  (*how do my other books treat this?* · *Strang*). It runs CA3's selection door anchored there (that book's
  reading and spans, `openSourceId` that book) with `sourceIds: [<the main pane's book>]`. Both require CA3's
  `compareScope`.
- **Narrow windows** (below 1,040 px; `SIDE_BY_SIDE_MIN_WIDTH`, the spec's layout bound): `s`, Ctrl+\ and
  *read side by side* open the section as a peek sheet over the lower half of the book. It has one dim line,
  *side by side needs a wider window*, no crumb, no follow along, and is recorded as
  `corresponding_section_peeked`.
- **Never lists exam material:** what can be opened comes from `reader.correspondents` (which reads coverage
  only through the protection predicate), and the section read refuses protected sections on its own,
  read again at each call.
- **Records** (salience only, through `reader.log_activity`): `side_by_side_opened`, `follow_along_moved`, and
  CA5a's deferred `corresponding_section_peeked` (a list peek, or the narrow sheet) and
  `corresponding_section_opened` (go there). They join `CLIENT_ACTION_EVENTS`. `ACTIVITY_FIELDS` gains ids
  only: `section_id`, `target_source_id`, `target_extraction_id`, `target_section_id`, `by` (judged or search)
  and `leader`. The learner's words are never kept.
- **Kill switch** `reader.side_by_side.enabled` (new `[reader.side_by_side]`, default on). The prompt contract
  carries `side_by_side: {enabled: true}` only while this switch, `curriculum.enabled` and the Reader are on.
  It does not depend on CA5a's `reader.correspondence.enabled`, because Ctrl+\ works without the list. Off:
  no key, no button and no read are added, `reader.side_by_side_section` refuses
  (`side_by_side_disabled`), and the Reader is today's exactly.
- **Plumbing:** Tauri passthrough `reader_side_by_side_section` (desktop only; pinned off the mobile
  allowlist as `READER_CA6_RPCS`); DTO `SideBySideSectionDto`; client `readerSideBySideSection`; contract key
  `sideBySide`; `DetourKind` gains `side_by_side`; `useReaderInquiry` gains `pushSideBySide` / `dropDetour`.
- **Config:** schema `ReaderSideBySideConfig`; parameter registry rule (structural, operational: a boolean
  kill switch, no weight, margin or threshold); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry
  (mvp-0.9 … mvp-0.38, 29) recomputed with `defaults_fingerprint_for_version`, with one comment line each and
  the paragraph on mvp-0.9 (0 mismatches).

No migration, no successor, no model call.

## Deviations and open questions

1. **The second pane shows one section at a time** (with *‹ previous · next ›*), not the whole book. That
   way the exposure rows are exactly the text displayed, and protection is read for every section shown
   (exam units inside a teaching book are never displayed, since the section read refuses them). A crossing
   in the second pane is the learner moving it to another section. Scrolling inside it is mid-section.
2. **Ctrl+\ falls back to the first unchecked search hit** when nothing is judged for the section (labelled
   in the pane). The spec says "the first correspondent in the API's order", and the API returns search hits
   only on a pressed read. Following stays judged-only (CA6's row in §13). If the owner prefers Ctrl+\ to
   open judged correspondents only, it is one line (`firstCorrespondent`).
3. **No ✕ on the main pane's header.** Closing is the second pane's ✕, Esc or Ctrl+\. A ✕ on the first pane
   would mean swapping the books, which the spec doesn't describe.
4. **Intent box, margin marks, notes and highlights in the second pane are not built.** The spec's
   "everything else works in both panes" lists them. CA6 builds the selection verb the stage brief names (CA3
   in side by side) as a one-line bar under the pane. The full intent box needs the Reader's capture and
   anchoring machinery per pane, which is a larger refactor of `ReaderScreen`.
5. **Records go through `reader.log_activity`**, so like every other Reader funnel event they are written only
   while `reader_inquiry` is on. The crumb also needs `reader_inquiry`: without it side by side opens with no
   crumb.
6. **The narrow-window peek pushes no crumb**, the same as CA5a's peek (CA5a deviation 2).
7. **A follow-along move of the main pane is a jump, not a detour**: it never pushes a crumb, and `Alt+←`
   returns to before side by side.

## Gate (targeted; the full suite runs once at landing)

(filled in below)
