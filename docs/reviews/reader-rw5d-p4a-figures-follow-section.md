# Reader RW5d P4a: figures follow the section, plus the reading-provenance follow-up (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, phase P4a (§10.2; table row "P4a — figures follow
  the section"; Q8 = no `source_objects` mirroring).
- **Branch:** `reader/rw5d-p4a-figures-follow-section` in `learnanything-ad1`, base `de73fbda51`.
- **Migration:** none. **Successor:** none (display only: nothing in scoring, scheduling, projection or serving reads
  anything P4a adds).
- **Switch:** CA5's `reader.correspondence.enabled` (which already respects `curriculum.enabled` and the Reader),
  together with `figures.enabled`. Either one off: the correspondents read is byte-identical to before (tested).
- **Live calls:** none. Every test uses fakes. No paid command or CLI ran against any vault, and no manual run was
  needed (the code paths are read-only and fully covered by synthetic vaults).

## Part 1: RW5d P4a, figures follow the section

### Backend (the correspondents read)
- `learnloop.figures.service.section_figures(vault, repository, extraction_id, section_of)` returns one reading's kept
  figures grouped by the section their anchor sits in. It reads the rows `list_figures` picks (`_listed`), so it lists
  what the Reader would list on that reading now (Codex review F3: without `list_figures`' presentation, so a sketch
  built under another engine is not re-verified and nothing reaches `judgment_ledger`; opening the figure does that):
  - per version chain, the newest shown version;
  - held-out figures (`row_withheld`) left out, which covers the home spans, the input manifest, the retrieved
    passages' keys, the homes of figures with no passage, and stored learner state;
  - show-me figures left out while show me is off; panel, sketch and rich switches applied.
  
  Of those, only shown figures are kept (`verified` or `illustrative`, never a failed or unsupported line), at most
  once per figure and section. Each entry carries `figure_id`, its home (`extraction_id`, `anchor_span_id`), `label`,
  `kind`, `verification` and `created_at`. Nothing is copied and nothing is written (tested with an outdated sketch,
  Codex review F3).
- `learnloop_sidecar/handlers/correspondents.py` adds `figures_follow_enabled(vault)` and `_with_figures`. When the
  read is `judged` and the switch is on, each judged correspondent section gets `figures`, and only when it has at
  least one. The join goes through the section: the anchor span is mapped with the protected library's reading
  (`all_spans`), and a span in a withheld section maps to no section. Search-fallback hits (CA5a's unchecked list)
  never carry figures: P4a is the judged line.
- **Protection on both sides:**
  - A protected open section returns `withheld`, with no correspondents and so no figures.
  - A correspondent section with any withheld span is not in the library.
  - A figure is listed only while nothing it was built from, or lands on, is held out now.
  - Protection is read again on every call (through `LibraryCache.get` and `list_figures`).
- **Fail closed:** if the figures can't be read, no figure is listed and the rest of the read stands (logged warning).

### Frontend
- `dto.ts`: `CorrespondentSectionDto.figures?: CorrespondentFigureDto[]`.
- `AlsoInBooks.tsx`: on a judged line whose section has figures, the expanded list offers
  `◇▸ interactive version from Lay §5.1` (`ALSO_COPY.figureFrom`, `figureOfferWords`; numbered when there are
  several). It is shown only while the Reader passes `onOpenFigure`, i.e. figures are on and the Reader is online. The
  collapsed line is unchanged.
- `useFigures.ts`: adds `follow(ref, home, at)` and `followed`. Pressing the offer:
  - reads the figure's own book's listing now (`reader.figures` on that extraction, so protection and switches are
    checked again at the press);
  - shows the figure under the passage in view in this section (else the section's first passage), expanded;
  - clears it when the book changes, and patches predictions on it like any other figure.
  
  A ready fuller version comes along; one still being built stays with its own book.
- `FigureInline.tsx`: a followed figure always names its home, collapsed or open: `from your reading of Lay § 5.1 …`
  (`FIGURE_COPY.fromYourReading`, `figureHomeLine`). It has no "not right?", because a new version belongs to its own
  book. If its own book no longer lists it (held out, switched off, gone, unreadable), the Reader says
  `ALSO_COPY.figureGone` and shows nothing; a copy shown by an earlier press leaves too (Codex review F1). With CA5's
  switch off (`followEnabled`, from the contract's `correspondence.alsoInBooks`) followed figures are cleared, not
  rendered, and a follow still in flight never lands (Codex review F2).
- `ReaderScreen.tsx`: `openFollowedFigure`. It reuses the CA5a "passage in view, else the section's first" rule, logs
  `figure_opened`, jumps to that passage (with the usual crumb) only when it is not the passage in view, and includes
  followed figures in the PDF pane's inline notes.
- Desktop catalog regenerated (`desktop_generate.py`; `desktop_validate.py` passes: 305/305 TS + 6/6 Rust, ACTIVE=311).

### Decisions taken (defaults; the owner may override)
1. Only judged correspondents carry figures, not CA5a's unchecked search hits: the spec names the *also in your
   books* line, and an unchecked hit is not an established correspondence.
2. The figure opens in place here (the spec's "shows the figure in place with its home named"), not through a jump to
   the other book. *go there* (↵) still opens the other book's section, where the figure is also listed as usual.
3. A followed figure offers no revision. Predictions on it work as usual (`reader.figure_predict` checks the figure by
   id).

## Part 2: the provenance follow-up (`diagnosis/text_gaps/provenance.reading_sources`)
- A Reader question (`question_events.context = 'reader'`) whose `source_context_json` is NULL, i.e. recorded before
  migration 117, is placed from its `note_id` when that parses as `span:<extraction>/<span>`
  (`tutor_qa.reader_span_key`, parsed by `ingest.locators.parse_block_span`, both parts non-empty). It returns
  `({"extraction_id", "span_ids": [span]},)` with complete=True. The caller (`learner_protection.reading_reason`, used
  by the router card) then checks it against exam material like any other placed span.
- **Still fails closed** (`((), False)`):
  - no key, a note id, `span:ext` (no block), `span:ext/` or `span:/s`;
  - any *recorded* context that names nothing (`{}`) or is unreadable. A recorded context is what the question was
    asked on, and the key never stands in for it.
- **Unchanged:** questions outside the Reader (library and practice), and every question with a readable recorded
  context.
- `_question_row` now also selects `note_id` (guarded by `PRAGMA table_info`) and reports whether a source context was
  recorded. `question_record` is unchanged.

## Tests (fail-first)
- `tests/test_reader_rw5d_p4a_figures_follow.py` (5): offered from the corresponding section; no write, no model
  call, no `source_objects` mirror; off byte-identical (both switches); held-out or exam inputs and held-out homes
  never offered; protection read again on the figure's side and on the open section's side; an unreadable store
  offers no figure and keeps the read. Against the base code, 4 of 5 fail (the switch-off test passes there, as
  expected).
- `tests/test_reader_question_note_id_placement.py` (4): placed from `note_id`; checked against exam material
  (withheld vs shown); unplaceable cases fail closed; non-Reader questions unchanged. The first test failed before the
  fix (`complete is False`).
- `apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx` (4): the offer's words and press;
  no offer without figures or without `onOpenFigure`; the followed figure under the passage here, expanded, home
  named, no "not right?", still named when collapsed; not shown when its own book no longer lists it, or lists it as
  failed.
- `apps/learnloop-tauri/src/screens/reader/alsoInBooksReader.test.tsx` (+2): in the Reader, the offer opens the
  figure under a passage of this book with its home named; with figures off, no offer and no `reader.figures` read.

## Gate (this step; targeted only, per the owner's 2026-10-17 rule)
Commands run:
- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`
- `uv run lint-imports --no-cache`: 40 kept, 0 broken
- targeted pytest (`-n 6`, memory-capped) over the 35 files listed below: 1070 passed, 0 failed (202 s)
- `npm install`, `npm run typecheck` (clean), vitest (`--maxWorkers=4`) over `alsoInBooks*.test.tsx`,
  `figures/` (whole folder), `findSectionReader`, `figuresWithReadingPath` and `readerCorrespondenceSettings`:
  21 files, 464 passed
- `npm run frontend:build` (built)
- no Rust, schema or migration change, so no cargo, DB reference or durability run is needed

Pytest files: the two new files; `test_reader_ca5_also_in_books`, `test_reader_ca5_landing`,
`test_reader_ca5a_find_section`, `test_section_coverage_rpcs`, `test_section_coverage`, `test_section_coverage_review`,
`test_curriculum_c0b_landing`, `test_reader_ca3_landing_ca5a`, `test_reader_ca4_landing`, `test_mobile_allowlist`,
`test_figures_rpc`, `test_figures_switch_off`, `test_figures_show_me`, `test_figures_show_me_codex_review`,
`test_figures_codex_review`, `test_figure_label_wording`, `test_figure_rich_job`, `test_figure_predictions`,
`test_router_card_reading_gaps`, `test_diagnosis_input_provenance`, `test_question_signal`,
`test_reader_ca2_astra_handoff`, `test_source_retrieval_tutor`, `test_ux_phase4_landing`,
`test_learner_blindness_relax_codex_review`, `test_ad_protected_readings`, `test_question_promotions`,
`test_interaction_signals`, `test_reader_ca2_fix_orchestrator`, `test_ad23_contract`, `test_architecture`,
`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`.

## Open items
- Reviewers: the correspondents read now also calls `list_figures` for each correspondent reading on every section
  crossing. Each figure gets one exam-predicate check, and the list is short. The cost is bounded, but it is not
  cached (protection must be read every time).
- A followed figure is not remembered across book switches or reloads (by design: it is a view, not a copy). Pressing
  the offer again shows it again.

## Landing onto main

Worktree `learnanything-ad1`, branch `reader/rw5d-p4a-figures-follow-section`, from the review tip `e54d9d7521`. No
migration, no successor, no config key. No live model call. Every Python/CLI run outside pytest used `env -i` with an
empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and `TMPDIR` outside the worktree. Only the mvp035
owner copies were opened, never a live vault.

### Orchestrator scoped verify (Sol, job `20261101-233122-LneCUu`)

CLEAN on `e54d9d7521`. F1, F2 and F3 are closed, with no regressions. `list_figures`' main behaviour and the
protection checks are preserved, and book switches clear the followed state. The verify also ran 240 synthetic
old/new listing comparisons.

### Rulings

- **R1:** "Only judged correspondents carry figures; CA5a's unchecked search hits never do (an unchecked hit is not an established correspondence). Accepted."
- **R2:** "A followed figure shows in place in the current book with its home named and no 'not right?'; the quiet listing offers outdated sketches on their stored verdict and opening re-verifies. Accepted under the proportionate bar."

### Merges

- Main was still `de73fbda51`, the branch's base, so `git merge main` was already up to date and nothing conflicted.
  Main was read again after the gate and the smoke and had not moved, so no second merge was needed.
- `config/template.py` is untouched by this branch. All 31 fingerprints were checked with
  `defaults_fingerprint_for_version` after clearing `.pyc`: 0 changed.
- Generated references were regenerated (`9a31b58866`). The stage had not regenerated them, and its code moved
  `correspondents.py`'s line cites and added `figures/service.py` and the P4a test file to the source lists. The rest
  is `source_commit` metadata. `db_validate_reference.py` errors `[]`; `validate_vault.py` passes.
- Desktop catalog: `desktop_generate.py` produced no change; `desktop_validate.py` passes (305/305 TS + 6/6 Rust,
  ACTIVE=311).

### Gate (on `9a31b58866`)

| Lane | Result |
|---|---|
| `lint-imports --no-cache` | 40 kept, 0 broken |
| Full pytest (`flock` + 10G scope, `env -i`, `-n 8 --dist worksteal`) | **23626 passed, 0 failed**, 90 skipped, 47 xfailed (38:54) |
| Durability (`-m durability -n 6`) | 182 passed, 1 skipped |
| Owner lane (`-m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies of `fixtures-local/owner-copies-mvp035` in gitignored `fixtures-local/landing-p4a/`) | **83 passed, 2 failed, 4 skipped**. Both failures are the known ones (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies::…[arxiv_v2]`) |
| Frontend (`npm install`, `typecheck`, whole `vitest --maxWorkers=4` in a 5G scope, `frontend:build`) | ok; 254 files, 2423 tests passed; build ok |
| `cargo check` | not run: nothing under `src-tauri` differs from main |

There was no unexpected failure, so nothing needed a rerun.

### Smoke (fresh owner copies, gitignored `fixtures-local/landing-p4a-smoke/`)

**Setup:**

- Fresh backup-API copies of the three mvp035 owner copies.
- Every AI route at the `127.0.0.1:9` blackhole, with the key variables unset.
- `env -i` with an empty `HOME`, `CODEX_HOME` and config directory, and `LEARNLOOP_NOTES_TEND=off`.
- An audit hook logs every process start and socket connect, and refuses non-loopback connects and Codex process
  starts. A self-test afterwards logged both of its events.
- Main's code (`de73fbda51`) against the branch's (`9a31b58866`), each a `git archive` with `migrations/`.
- On each copy: `upgrade` mvp-0.35 -> mvp-0.40, a primary load, `rebuild-derived-state`. Both heads are 231.

**Results:**

- **Today and the daily plan** are byte-identical, main against branch. linear_algebra: 525266 / 84699 bytes;
  probability: 740827 / 124024 bytes; arxiv_v2: 344204 / 32436 bytes.
- **Router card** byte-identical too (23376 / 15151 / 14233 bytes).
- **Quiet `reader.correspondents`** (`search_fallback=False`, through the sidecar handler) on every readable section
  of every reading in the library: 49 / 11 / 20 sections, all `none`, byte-identical main against branch
  (23914 / 4937 / 9097 bytes).
  - On the branch, `figures_follow_enabled` is true, so the P4a path was armed.
  - These copies have no `section_coverage` rows and no stored figures, so no section is judged and no `figures`
    key can appear. The tests cover the judged path.
  - The read writes nothing. A monitor connection opened after the load saw `PRAGMA data_version` 2 before and after
    the reads, and a sha256 of every table's rows did not change, on both sides.
- **The 9 July Reader questions** (8 in linear_algebra, 1 in arxiv_v2; `source_context_json` NULL) went through
  `PastWork.reading_reason`. All 9 are now placed through `note_id`: one span each, complete. On main they were
  `WITHHELD_UNREADABLE` ("the protection rules could not be read").
  - Exam verdict: all 9 shown. None of the placed spans is exam or held-out material.
  - Every other recorded question's verdict is unchanged (37 / 23 / 2 checked).
- `learnloop rebuild --shadow --json` on each branch copy: **facet 0 / mastery 0 / schedule 0** changed, live database
  unchanged.
- `model_call_receipts`: **0 new** across 6 databases compared against their base copies. probability's 56 are
  inherited.
- Process and socket audit: **0 events**. No process started and no socket connected, loopback included.

### Open items

The stage's open items stand:

- the uncached per-crossing `list_figures` call;
- followed figures are not remembered across book switches or reloads.

The followups-nov1c open item 5 (old Reader questions without a source context) is resolved by Part 2 here, as the
smoke shows.
