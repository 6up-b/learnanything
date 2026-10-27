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
- **Peek** (Space, or the title/*peek*): `reader.correspondent_peek` (fix round, Codex review F1, F2) reads
  protection again, refuses a section protected now, and returns the hit's own section's first blocks from its
  `jump` locator (at most three, never the next unit's); each block shown gets a `source_exposure` row
  (context `library`) before the text is returned. They show in the rail, first block outlined, with *go there ↵ · compare with §… (c) · esc close*. Esc closes the peek and returns
  focus to the line it came from. A second Esc folds the list.
- **Go there** (↵): the existing `openLibraryHit`, so the other book opens at the `jump` span as a `source`
  detour and Alt+← comes back.
- **Compare** (c): through the library compare path (`useLibraryAsk.compareWith`). It runs a library ask
  anchored on the open section (the question is the section's title, the anchor is the passage in view if it
  is inside the section, otherwise the section's first passage). It pins two passages, this section's and
  the hit's `jump` passage, then runs `reader.library_compare`. The comparing pane opens as it does today.
  The organizer's notes are not started automatically: the learner asked to compare, so they stay behind
  *write the notes ↵*. Compare is offered only while `libraryAsk.compare` is on.
- **Not about this:** one durable operation, `reader.correspondent_dismiss` (fix round, Codex review F3, F6):
  in one transaction, a section-pair `learner_card` verdict (task `section_correspondence`, origin → hit; the
  operation's record) and C0a's `learner` row and verdict for each LO of the open section. A section with no
  LO gets the pair verdict only, so every unchecked hit can be corrected without inferring an LO. The client
  names the operation; the same id again answers from the record and writes nothing, so a lost reply is
  retried safely. The line is replaced by *… · not about this · undo · ⓘ where this goes* (the spec's text).
  *Undo* is an operation of its own over the one it names (pair verdict `none`, and `none` on that
  operation's LOs still standing as `not_about`). A failure is reported and the line stays; nothing is sent
  to take anything back.
- **Keys** (on the list only, never window-level): ↑↓ move between lines (wrapping), Space peek, ↵ go there,
  c compare, Esc close peek then fold. Space, ↵ and c act only when a line's title has focus, so the other
  buttons keep their own press.
- **Kill switch** `reader.correspondence.enabled` (new `[reader.correspondence]` section, default on).
  `reader.prompt_contract` carries `correspondence: {enabled, find_section}` only while this switch,
  `curriculum.enabled` and the Reader are all on. Off, the Reader never mounts the component, so the Guide
  and its reads are exactly today's. The switch gates only the presentation: C0a's RPCs keep their behaviour,
  and their data stays gated by `curriculum.enabled`.
- **Plumbing:** Tauri passthroughs `reader_correspondents`, `curriculum_coverage_correct`,
  `reader_correspondent_peek` and `reader_correspondent_dismiss` (desktop only; the two new RPCs are pinned off
  the mobile allowlist as `READER_CA5A_RPCS`, and refused while `reader.correspondence.enabled` is off); DTOs
  `CorrespondentsDto`, `CorrespondentSectionDto`, `CorrespondentPeekDto`, `CorrespondentOperationDto`; client
  `readerCorrespondents`, `readerCorrespondentPeek`, `readerCorrespondentDismiss`.
- **Config:** schema `ReaderConfig` / `ReaderCorrespondenceConfig`; parameter registry rule (structural,
  operational: a boolean kill switch, no weight, margin or threshold); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entry (mvp-0.9 … mvp-0.37) recomputed with `defaults_fingerprint_for_version`, plus a comment line each.

No migration, no successor, no model call. CA5's judged list and CA6 are not built.

## Deviations and open questions

1. **Peek writes exposure rows, one per block shown** (fix round: it used to read `get_span_view`, which
   records only the requested span and returns ordinal neighbours across unit boundaries). The find itself
   writes nothing.
2. **No detour crumb for a peek** (`› peek Axler §5.A`, §6.3). The return stack walks in-book peeks. A peek
   crumb into another book would make Alt+→ open that book. Go there does push the `source` detour, with the
   origin and Alt+←.
3. **No `reader_action_invoked` salience events** (`corresponding_section_peeked` / `_opened`, §6.5). The
   stage brief allows no write except the correction. CA5 can add the events with its own list.
4. **A correction on a hit covers every LO of the open section.** C0a's corrections are per (section, LO),
   and a search hit has no LO. *Not about this* (this section) is read as "about none of this section's LOs".
   It also overrides a later judge row for those (hit, LO) pairs until the learner undoes it. The pair verdict
   (fix round) is directional (origin → hit) and only hides the hit in this section's unchecked list.
5. **The compare question is the section's title.** CA3, running in parallel, builds an anchor request with
   no pins. When it lands, compare could move to it.
6. **The `x` key** and its clash check against the PDF surface and `LiveMarkdownEditor` belong to CA5 (the
   expanded one-line entry). CA5a's keys are scoped to the list.

7. **Cost of the quiet read.** It runs on each crossing into a new Guide section (not on scroll). C0a's
   `Library` reads every readable reading, so on a large library this read is not free on the serial
   sidecar. CA5's one-line entry needs the same read. If it shows up in use, a per-section cache keyed by the
   coverage state would be the fix (C0a's side).

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- **Targeted pytest** (`-n 6`) over 78 files: the new `tests/test_reader_ca5a_find_section.py`; C0a's
  `test_section_coverage.py`, `_review.py` and `_rpcs.py`; every test file naming the prompt contract
  (`test_compare_keep_switch_off`, `test_compare_sources_keep`, `test_figure_*`, `test_figures_*`,
  `test_library_ask_review`, `test_library_exercises`, `test_mobile_allowlist`, `test_reader_dialogue`,
  `test_reader_find_sources_callers`, `test_reader_inquiry_kill_switch`, `test_reader_intent`,
  `test_reader_tutor_offers`, `test_reader_tutor_switch_off`, `test_reading_paths`, `test_rw4_kill_switches`,
  `test_sidecar_reader`, `test_sidecar_serializer_snapshot`); every test file naming the default snapshots,
  fingerprints or the parameter registry (`test_architecture`, `test_config_refactor`, `test_registry_audit`,
  `test_table_roles`, every `test_mvp0*_upgrade`, the successor and landing pins, among others); plus
  `test_desktop_rpc_contract`, `test_vault_template`, `test_cli_help_snapshot`.
  First run: 1610 passed, 9 failed, 12 skipped, 3 xfailed. The nine failures were earlier stages'
  byte-for-byte contract pins seeing the new key, which is on by default. Each now registers it the way
  earlier stages registered theirs (switched off, or popped with its value asserted). The five files rerun
  with the new test: 96 passed.
- **Frontend** (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` clean; vitest (`--maxWorkers=4`)
  on `findSection.test.tsx` (16) and `findSectionReader.test.tsx` (5), plus 19 files touching the Guide rail,
  the library ask/compare hook and pane, and the Reader's guide (`classicIsBase`, `compareKeep`,
  `compareKeepSwitchOff`, `figures/advancedPanels`, `figures/libraryOfferSettle`, `libraryAsk`,
  `libraryAskJobs`, `libraryAskSwitchOff`, `libraryExercises`, `libraryExercisesReader`, `libraryRoles`,
  `readerHooks.parity`, `ReadingPathCard`, `readingPathsRefresh`, `readingPathsReader`,
  `readingPathsSwitchOff`, `splitRails`, `ReaderScreen.guide`, `attentionBudget`): 146 passed.
  `npm run frontend:build` ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok (two passthroughs added).
- DB/config reference: `db_generate_reference.py` regenerated it (the new `Config - reader` note, plus a
  section-function line in the generator). The hand-written leaf counts in `Configuration.md` and
  `Database.md` were moved to 1066. `db_validate_reference.py`: errors [].
- No paid or live call was made. The ad hoc Python (snapshot recomputation, reference scripts) ran under
  `env -i` with empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

The Codex review and its fix round: `docs/reviews/reader-ca5a-find-section-codex-review.md`.
