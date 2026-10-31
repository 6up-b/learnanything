# Reader CA5: also in your books

Stage `reader-ca5-also-in-your-books`, branch `reader/ca5-also-in-your-books` (base `6a8256517`).
Spec: `docs/specs/ux_reader_compare_ask_v1.md` §6.2–§6.3 (and §6.5's records, §12.3, §13); data and read API from
curriculum C0a/C0b (`reader.correspondents` over judged `section_coverage`, `curriculum.also_about`).

## What ships

- **The one line** (`apps/learnloop-tauri/src/screens/reader/AlsoInBooks.tsx`, mounted through the new `GuideRail`
  slot `alsoInBooks`, directly under the section's progress bar inside the section card): *also in Axler §5.A,
  Lay §5.1 ▸*. Names, never counts: the book's title before any subtitle (clipped) and the section's own number
  (else its clipped title). When the names do not fit one rail line (a display bound, `LINE_CHARS`) it ends
  *and others ▸*. It shows only when the quiet read (`reader.correspondents`, `search_fallback: false`) answers
  `judged`. `none`, `unchecked`, `withheld` or a failed read render nothing at all (no ghost line, no error).
  A search hit inside any answer is never listed. CA5a's footer action stays for the no-coverage case and is
  still hidden when the section has judged coverage.
- **Expanded** (a click, or `x`): grouped by LO in the API's order. Each line shows the book and `§` with the
  section's own number and title, then the treatment in plain words (*introduces it · develops it · uses it ·
  mentions it*, or *you linked it* for a learner-linked section). The coverage judge's notation line is in the
  model voice (purple, spoken prefix *LearnLoop's note (AI-written)*, `◇` when focused). The learner's keep
  reads *you compared these: different notation* (RW4d's fine labels, underscores as spaces). *read* marks a
  section read through. A section under several shared LOs shows once, under its first LO, with *also: …* (the
  other LOs' titles) on focus. No line carries a pair relation.
- **Keys** (on the list): ↑↓ move (wrapping), Space peek, ↵ go there, `s` side by side, `c` compare, Esc closes
  the peek, then menus, then folds back to the one line (focus returns to it). Space, ↵, `s` and `c` act only
  when a line's title has focus.
  - **Peek** reuses CA5a's protected `reader.correspondent_peek`: protection is read again, only the section's
    own first blocks are returned, and each block shown gets a `source_exposure` row. The blocks render in the
    rail, first block outlined. The detour strip gains the display-only crumb `› peek Axler §5.A`. With no
    detour, the strip shows the current section, the crumb and *close peek*. The crumb is never a
    return-stack entry (CA5a's reason: Alt+→ must never open that book).
  - **Go there** is the Reader's `openLibraryHit`: a `source` detour with the origin, the crumb and Alt+←.
  - **`c`** is `compareFoundSection`: CA3's one request anchored on this section and narrowed to the other
    section's book, or the library compare path while CA3 is off, exactly as CA5a's compare.
  - **`s`** is a seam. CA6 is not on main, so the Reader passes no `onSideBySide`. `s` does nothing and the
    key hint omits it. CA6 passes its entry through the same prop name its WIP gives `FindSection`.
  - **`x`** joins the Reader-wide keys while the line is on screen. It is off in text fields and
    contentEditable, while the intent box shows, and in the working posture. The key bar offers *x also in your
    books* then. Clash check: nothing else in the Reader binds a bare `x`. The PDF pane binds only modifier
    chords (Ctrl/⌘ `f`, `=`, `-`, `0`). `LiveMarkdownEditor` is a textarea, which the guard skips.
- **Corrections**, in each line's `⋯`:
  - *not about this* is CA5a's one durable operation, `reader.correspondent_dismiss`, now naming the LOs the line
    is listed under (`learning_object_ids`, new and optional; each must be one of the open section's LOs). In one
    transaction it writes C0a's `learner` row and verdict for each of those LOs plus the pair verdict. It is
    idempotent by the client's operation id, and a failed request resends the same id. The line becomes *… · not
    about this · undo · ⓘ where this goes* (the spec's text). Undo is its own operation.
  - *also about…* is a one-line box that calls C0b's `curriculum.also_about` on the other section. It answers
    *noted: also about orthogonal projection*, the resolver's *None of your topics matches those words yet.*, or
    its unavailable message, and the list is read again.
  - A landed correction asks CA5a's quiet read again (`refreshKey`), so its action appears if no judged
    correspondent is left.
- **Hide for this book · hide everywhere**, in the block's `⋯` (on the line and in the list's header): the new
  `[reader.correspondence] hidden_sources` (source ids) and `hide_everywhere` config keys. They are written by
  the new `reader.set_correspondence_preferences`, the same pattern as the margin marks' per-book switch (vault
  config, so it holds across devices; no change, no write). Hidden leaves nothing behind: no line, no list, no
  peek, no crumb, no `x`. **Settings brings it back**: `ReaderCorrespondenceSettings` lists what is hidden (by
  book title) with *show again*, and is absent when nothing is hidden or the feature is off. The Reader updates
  at once (a local override, then the cached prompt contract set from the sidecar's answer; it goes back on a
  failure).
- **Skim mode:** shown (the component is not gated by skim). **Working posture and offline:** not mounted.
- **Records** (CA5a's deferred events): `corresponding_section_peeked` / `corresponding_section_opened`, from
  either list (`via` `also_list` / `find_list`). They are salience-only client events through
  `reader.log_activity`, with ids and kinds only: `section_id`, `target_source_id`, `target_extraction_id`,
  `target_section_id` and `by` (judged / search) join `ACTIVITY_FIELDS`. A title is dropped.
- **Exam material is never listed:** the presentation adds no read of its own. C0a's read goes through
  `exam_withheld` / `reading_held_back` / `spans_withheld`. A test writes judge rows naming a held-out section and
  the exam's question straight into `section_coverage`: neither is listed. A section held out after it was judged
  leaves the list on the next read, and the peek is refused.
- **Per-section cache** (CA5a open item 7): `SC.LibraryCache`, one per vault database on the sidecar context, is
  used by `reader.correspondents` and the peek. Crossing sections reuses the parsed readings and the LO map while
  the loaded vault object, the protection key and the readings (`scope_signature`: ids, books, titles, reader
  switch) are unchanged. A reload, an exam mark, a held-back reading, an import or a re-extraction rebuilds it.
  Protection is read afresh on every call (fail closed, as a fresh library would). Coverage rows, corrections,
  keeps and read marks are never cached. On the client, the quiet read is one request per crossing, shared by
  CA5's line and CA5a's action (`correspondentsRead.ts`: in flight only, nothing kept). A test counts IR loads:
  crossing every section of the open book and back parses it no more than the first read did (one build).
- **Kill switch** `reader.correspondence.enabled` (CA5a's). `reader.prompt_contract`'s `correspondence` gains
  `also_in_books`, `hidden_everywhere` and `hidden_sources` while the switch, `curriculum.enabled` and the
  Reader are on. Off, there is no key: the Reader mounts neither component and reads nothing. The data stays
  gated by `curriculum.enabled`.
- **Plumbing:** Tauri passthroughs `reader_correspondence_preferences` and `reader_set_correspondence_preferences`
  (desktop only, pinned off the mobile allowlist as `READER_CA5_RPCS`, refused while off). The DTOs are
  `CorrespondencePreferencesDto` and `CorrespondentKeptDto`, plus the judged fields on `CorrespondentSectionDto`.
  The client gains `readerCorrespondencePreferences` and `readerSetCorrespondencePreferences`, and
  `readerCorrespondentDismiss` gains `learningObjectIds`.
- **Config:** schema `ReaderCorrespondenceConfig.hide_everywhere` / `hidden_sources`. They are classified in the
  parameter registry as structural and operational: preferences, with no weight, margin or threshold (no
  numeric leaf is added). All 29 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (mvp-0.9 … mvp-0.38) were recomputed
  with `defaults_fingerprint_for_version` (rechecked: 0 changed), each with its comment line.

No migration, no successor, no model call.

## Deviations and open questions

1. **Hide preferences are config keys** (not a table), as the margin marks' per-book switch is. The cost is the
   fingerprint recompute. CA6 (running in parallel) adds `reader.side_by_side.enabled` and recomputes the same
   snapshots, so the landing that comes second recomputes all of them again.
2. **The peek renders in the rail** (CA5a's peek), not in the right side as a library hit's peek does (§6.3). The
   rail is the right side in the reading posture, so this matches; the comparing posture's pane is not used.
3. **Kept relations are read as RW4d's fine labels with underscores as spaces** (*different notation*). A label
   vocabulary with its own words would be RW4d's to add.
4. **Hiding the line does not hide CA5a's pressed action.** That action is pressed, never unasked, and it is
   still hidden on a section with judged coverage. So with the line hidden, a judged section shows no
   correspondence UI at all. The owner may prefer the action to stay available then.
5. **CA6 overlap.** CA6's WIP (`reader/ca6-side-by-side`, read only through git objects, never its worktree) adds
   the same two events, the same `ACTIVITY_FIELDS` names (plus `leader`) and the same logging in `FindSection`.
   This branch uses the same names and payload keys, through one helper (`correspondenceEvents.ts`). The landing
   that comes second keeps one copy (both write the same events). CA6 wires `s` by passing `onSideBySide` to
   `AlsoInBooks`, as it does for `FindSection`.
6. **`desktop_validate.py`** may need the new frontend files classified. It already failed on main (CA5a
   landing note), and no test runs it.

## Gate (targeted; the full suite runs once at landing)

GATE_PLACEHOLDER
