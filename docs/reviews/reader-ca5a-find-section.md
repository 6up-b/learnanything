# Reader CA5a: find this section in my other books

Stage `reader-ca5a-find-section`, branch `reader/ca5a-find-section` (base `1bcde2096`).
Spec: `docs/specs/ux_reader_compare_ask_v1.md` §6.2 (the paragraph *A section with no coverage yet*), §6.3, §6.5,
X7, §12.3, §13; data and read API from curriculum C0a (`reader.correspondents`, `curriculum.coverage_correct`).

## What ships

- **The pressed action** in the Guide's footer: *find this section in my other books ▸*
  (`apps/learnloop-tauri/src/screens/reader/FindSection.tsx`, mounted through the new `GuideRail` prop
  `findSection` just above the cue footer). When the Guide section changes, a quiet read runs:
  `reader.correspondents` with `search_fallback: false`. That read makes no search, no model call and no
  write. The action shows only when that read reports no judged coverage (`none`). It is hidden when the
  section has judged coverage (CA5's one-line entry, not built yet), when the section is protected
  (`withheld`), and when the quiet read fails. A failed quiet read shows no error line.
- **Pressed:** `reader.correspondents` with the fallback on. The live `search_spans` hits come back grouped by
  book, one group per other book, in the API's order. Each line shows the section's own number and title
  (`§ 5.A Invariant subspaces`), then *found by search, not checked* (C0a's label), plus *read* if the learner
  has read it through. No line has treatment words and nothing shows a count. If coverage was judged in the
  meantime (the pressed read returns `judged`), the action hides itself instead of listing CA5's data.
  Nothing found: *Nothing in your other books matched this section by search.* Failure: one line with
  *try again*.
- **Peek** (Space, or the title/*peek*): the hit's `jump` passage and the next two blocks show in the rail,
  first block outlined, with *go there ↵ · compare with §… (c) · esc close*. Esc closes the peek and returns
  focus to the line it came from. A second Esc folds the list.
- **Go there** (↵): the existing `openLibraryHit`, so the other book opens at the `jump` span as a `source`
  detour and Alt+← comes back.
- **Compare** (c): through the library compare path (`useLibraryAsk.compareWith`). It runs a library ask
  anchored on the open section (the question is the section's title, the anchor is the passage in view if it
  is inside the section, otherwise the section's first passage). It pins two passages, this section's and
  the hit's `jump` passage, then runs `reader.library_compare`. The comparing pane opens as it does today.
  The organizer's notes are not started automatically: the learner asked to compare, so they stay behind
  *write the notes ↵*. Compare is offered only while `libraryAsk.compare` is on.
- **Not about this:** C0a's `curriculum.coverage_correct` with `choice = not_about`, for the hit section,
  once per LO of the open section (`search.correctable_learning_object_ids`). Each call writes one `learner`
  row and one `learner_card` verdict, and nothing else. The line is replaced by *… · not about this · undo ·
  ⓘ where this goes* (the spec's text). *Undo* sends `choice = none` for each LO, and the hit returns. If a
  correction fails part way, the LOs already written are taken back and the error is reported. A section with
  no LO has nothing to correct against, so its lines don't offer *not about this*.
- **Keys** (on the list only, never window-level): ↑↓ move between lines (wrapping), Space peek, ↵ go there,
  c compare, Esc close peek then fold. Space, ↵ and c act only when a line's title has focus, so the other
  buttons keep their own press.
- **Kill switch** `reader.correspondence.enabled` (new `[reader.correspondence]` section, default on).
  `reader.prompt_contract` carries `correspondence: {enabled, find_section}` only while this switch,
  `curriculum.enabled` and the Reader are all on. Off, the Reader never mounts the component, so the Guide
  and its reads are exactly today's. The switch gates only the presentation: C0a's RPCs keep their behaviour,
  and their data stays gated by `curriculum.enabled`.
- **Plumbing:** Tauri passthroughs `reader_correspondents` and `curriculum_coverage_correct` (desktop only;
  C0a already pins the RPCs off the mobile allowlist); DTOs `CorrespondentsDto`, `CorrespondentSectionDto`;
  client `readerCorrespondents`, `curriculumCoverageCorrect`.
- **Config:** schema `ReaderConfig` / `ReaderCorrespondenceConfig`; parameter registry rule (structural,
  operational: a boolean kill switch, no weight, margin or threshold); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entry (mvp-0.9 … mvp-0.37) recomputed with `defaults_fingerprint_for_version`, plus a comment line each.

No migration, no successor, no model call. CA5's judged list and CA6 are not built.

## Deviations and open questions

1. **Peek writes the standard exposure row.** The peek uses the library peek's read (`get_span_view`,
   context `library`), which records a `source_exposure` row on every view, as every peek in the Reader does.
   The find itself writes nothing. No other read-only span view exists. Leaving the row out would make this
   the one surface that shows source text without recording it.
2. **No detour crumb for a peek** (`› peek Axler §5.A`, §6.3). The return stack walks in-book peeks. A peek
   crumb into another book would make Alt+→ open that book. Go there does push the `source` detour, with the
   origin and Alt+←.
3. **No `reader_action_invoked` salience events** (`corresponding_section_peeked` / `_opened`, §6.5). The
   stage brief allows no write except the correction. CA5 can add the events with its own list.
4. **A correction on a hit covers every LO of the open section.** C0a's corrections are per (section, LO),
   and a search hit has no LO. *Not about this* (this section) is read as "about none of this section's LOs".
   It also overrides a later judge row for those (hit, LO) pairs until the learner undoes it.
5. **The compare question is the section's title.** CA3, running in parallel, builds an anchor request with
   no pins. When it lands, compare could move to it.
6. **The `x` key** and its clash check against the PDF surface and `LiveMarkdownEditor` belong to CA5 (the
   expanded one-line entry). CA5a's keys are scoped to the list.

## Gate (targeted; the full suite runs once at landing)

Recorded at the end of the stage; see the structured result for counts.
