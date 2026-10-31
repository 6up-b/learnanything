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

## Landing onto main (2026-10-27)

Landed in `learnanything-astrafix` on `reader/ca5a-find-section` (stage tip `31597f4e5`, base `1bcde2096`) by
merging `main` `5b3f66059`: the Oct 27 follow-ups (`dbc1559e7`), the docs-only RW5c design spec (`d2f10ef55`) and the
cold-retry successor mvp-0.38. Main was neither fast-forwarded nor pushed. No migration and no successor: CA5a stays
navigation and display only, at every version.

### Commits and conflicts

| Commit | What |
|---|---|
| `48333b292` | `--no-ff` merge of `main` `5b3f66059`. **Conflicts:** `src/learnloop/config/template.py` (every default snapshot, mvp-0.9 … mvp-0.37) and ~430 generated reference notes (`source_commit` stamps). The template keeps both sides: mvp-0.9's comment carries both new keys' paragraphs (`[practice] reschedule_cold_after_assist`, then `[reader.correspondence] enabled`), every later entry both one-line notes, and **mvp-0.38 gains CA5a's line** (its effective defaults include `[reader.correspondence] enabled = true`). **All 29 fingerprints** (mvp-0.9 … mvp-0.38) were recomputed with `defaults_fingerprint_for_version`, the template `.pyc` cleared, and rechecked (0 mismatches). The reference notes were taken from main and regenerated in the next commit. `schema.py`, `parameter_registry.py` and `db_generate_reference.py` auto-merged. |
| `9a7132897` | DB/config reference regenerated on the merge. The hand-written counts in `Configuration.md` and `Database.md` move to **1067 effective leaves in 75 sections** (main's 1066 + CA5a's key). `db_validate_reference.py`: **errors []**; `validate_vault.py` passes (1163 notes). |
| `95ec35cb4` | The interaction test (below). |

`git diff main` lists no binary, no tracked database and nothing under `fixtures-local/`; `.gitignore` is unchanged.

### Interaction with the cold-retry reschedule (mvp-0.38)

The reschedule's `coldness_receipt.repair_surface_hard_contamination` skips a candidate surface through the final
receipt's own exposure scan. A peek's rows (`span_view.record_span_exposures`, context `library`, no entity) reach it:
a recorded span that a candidate was authored from is `cold_item_source_span_viewed` (hard). New test
`test_reader_ca5a_find_section.py::test_a_peeked_paragraph_that_is_the_replacement_surfaces_source_is_skipped_by_the_reschedule`:
the repair's one spare surface is authored from Lay §5.2's paragraph `s6`. A peek of §5.2 between the primed attempt
and the due cold retry shows `s5` and `s6`. Then help is taken on the retry. The retry is withdrawn, the
`assisted_cold_retry` opportunity is `structurally_refused / no_uncontaminated_surface`, and the summary names the
spare with `cold_item_answer_revealed_post_primed` and exactly the `s6` exposure id. It passed first time, so no fix
was needed. **Mutation check:** with the peek's recording replaced by fake ids, the spare is scheduled and the test
fails.

### Regeneration

- DB/config reference: regenerated and validated as above.
- Defaults fingerprints: all 29 recomputed.
- CLI help snapshot, sidecar serializer snapshot, desktop RPC contract and the mobile allowlist (both new RPCs
  desktop-only) pass as merged; nothing else needed regenerating.
- Targeted run after the merge (163 files: everything naming the snapshots, fingerprints, parameter registry,
  `METHOD_REGISTRY`, CLI help, either new key or the reference validator, plus the cold-retry and CA5a files; `-n 6`,
  5G scope): **3501 passed**, 39 skipped, 3 xfailed (24 min 31 s). Earlier stages' contract pins needed no change.
- `docs/learnloop-architecture-vault/_scripts/desktop_validate.py` fails on main too (an unclassified
  `pdfSelection/testing/syntheticBook.ts`); no test runs it and this landing leaves it alone.

### Gate (at `95ec35cb4`; `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/ca5a/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`; `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,352 passed, 0 failed**, 89 skipped, 47 xfailed. pytest 2,019.8 s (33:39); wall 33 min 41 s from taking the lock. No reruns, no faulthandler dump. |
| durability (`-m durability`, flock, 5G scope, `-n 6`) | **176 passed**, 1 skipped (55.5 s; wall 56 s) |
| owner lane (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-ca5a/`) | 83 passed, **2 failed**, 4 skipped (49.5 s; wall 54 s): exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy (`conic-sections`, `arxiv` x2, `linear_algebra_legacy`) |
| frontend (`apps/learnloop-tauri`) | `npm install` ok; `npm run typecheck` clean; whole vitest (`--maxWorkers=4`, 5G): **223 files, 1953 passed** (42.3 s; wall 43 s); `npm run frontend:build` ok; `cargo check --manifest-path src-tauri/Cargo.toml` ok |

### Smoke on owner copies

Fresh backup-API copies of the same three mvp035 owner copies (`fixtures-local/smoke-ca5a-2/`, `-4/`). Each was
upgraded with `learnloop upgrade --to mvp-0.38` (prints `mvp-0.35 -> mvp-0.38`), then `rebuild-derived-state`, then
the RPCs through a real sidecar process (`python -m learnloop_sidecar` over stdio). Everything ran under `env -i`
with `LEARNLOOP_COVERAGE_MODELS=off`, AI base URLs at `127.0.0.1:9`, and audit hooks that refuse non-loopback
sockets and process starts; the hooks logged nothing. `curriculum.enabled` and `[reader.correspondence] enabled` are
both on (defaults) in all three copies. Only counts and refusal codes were recorded.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| library readings / readable sections / withheld sections | 3 / 49 / 13 | 2 / 11 / 5 | 12 / 20 / 20 |
| `reader.correspondents` (search fallback) on two sections: status, hits (books) | unchecked, 2 (2) and 2 (2) | unchecked, 3 (1) and 3 (1) | unchecked, 6 (5) and 5 (5) |
| hits that are withheld, protected, exam or in the open book | 0 | 0 | 0 |
| `reader.correspondent_peek` on one hit: blocks shown / exposure rows written | 3 / 3 | 2 / 2 | 3 / 3 |
| rows match the shown spans exactly (context `library`); blocks protected or outside the section | yes; 0 | yes; 0 | yes; 0 |
| `reader.correspondent_dismiss`: hit gone, repeat replayed, undo brings the same hits back | yes, yes, yes | yes, yes, yes | yes, yes, yes |
| withheld section as origin (3 each): `reader.correspondents` | status `withheld`, 0 hits | same | same |
| withheld section peeked (3 each): refusal, rows written | `withheld`, 0 | `withheld`, 0 | `withheld`, 0 |
| `rebuild --shadow` before / after (mastery/facet/schedule) | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 |
| `model_call_receipts` rows added | 0 | 0 | 0 |

### Owner notes

- Kill switch: `[reader.correspondence] enabled` (default true). Off, the Guide's *find this section in my other
  books* action, the peek and *not about this* are gone; C0a's data reads are unchanged.
- It needs `curriculum.enabled` (on by default) and the Reader (`tutor_qa.reader_enabled`).
- No upgrade is needed for CA5a itself. The owner vaults' pending `upgrade --to mvp-0.38` (cold-retry) is unchanged
  by it.

### Open items

- Peek detour crumb and the `reader_action_invoked` salience events (`corresponding_section_peeked` / `_opened`) go
  to CA5.
- Compare runs through the library ask (the section's title as the question) until CA3's anchor request lands.
- A per-section Library cache for the quiet read before CA5 (C0a's side), if its cost shows up in use.
