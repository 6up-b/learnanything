# Reader CA4: the table by point (stage `reader-ca4-table-by-point`)

Branch `reader/ca4-table-by-point` (worktree `learnanything-dl1`), base CA3's verified tip
`d7850780b` (CA3 is not on `main` yet; it lands after CA5a). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §5 (all), §9 X3, X4 and X5, §11 K13, §12.2 (the
`source_compare.v2` request, `CompareKeep`'s mapping and the four-view bound), §13's CA4 row
and its kill switch, §15 Q7 (owner decisions 2026-10-25).

**No migration. No successor. No paid call was made** (every model in the tests is a fake;
nothing outside pytest called a route). Comparisons stay display, and a keep stays proposals in
the source-object layer: no scoring, scheduling, projection, serving or replay path reads a
comparison, its points, a kept cell or a hidden row. The successor ruling of §13 holds: I found
nothing that makes a comparison evidence.

## 1. What was built

### `source_compare.v2` (§12.2, K13)

`compare_sources(..., by_point=True)` (`src/learnloop/source_retrieval/compare.py`): the same
route (`source_compare`) and one call, prompt `source_compare.v2`, result model
`SourceComparisonV2`:

| Field | What it is |
|---|---|
| `points[].label` | a short label for one thing the books can be compared on |
| `points[].perspective` | one of the requested perspectives, exactly as written, or empty |
| `points[].cells[]` | per source: `status` `quoted` (a verbatim `quote` and one `line`) or `not_addressed` |
| `points[].relations[]` | per pair addressing the point: v1's `PairRelation` (the unchanged `RELATIONS`, no `complementary`) |

There is no consensus, summary or canonical field (pinned). The code, not the model, decides
what is shown (`_verified_points`):

- every quoted cell's quote is checked against its own source's passage with v1's `_quote_in`;
  a cell that fails is `not_addressed` and listed in `dropped_lines`, never repaired; a cell
  naming no compared source (or one twice) is dropped;
- every compared source has a cell on every point (one the model left out is not addressed);
  a quoted cell names the block that holds its quote (`span_key`; an anchor of several blocks
  names the right one);
- a relation stands only between two quoted cells of its point, with both quotes verified, one
  per pair; others are dropped;
- a requested perspective is a point labelled by the learner's words (`kind: perspective`), one
  per perspective (a second point the model gives for one is an ordinary point); one the model
  gave nothing for is appended with every cell not addressed ("not found in your library");
  the model's points come first, then the learner's views in their order;
- a model point no book quotes, or with no label, is dropped.

Stored in `source_comparisons.comparison_json` (no migration) as `contract`, `points`, and, so
every v1 reader reads a v2 row unchanged (the by-book table, Keep's v1 mapping, the tutor about
a comparison, the exam-withholding provenance), each quoted cell as its source's v1
`contribution` (naming its `point_id`) and each point's relations as v1 `relations` (naming
their point). `missing_perspectives` is the views no book fills. A v2 request is cached under
its own identity (its query hash names the contract), so it never reuses a v1 row and a v1
request never reuses it; v1's hash is unchanged.

### The Reader's request and table

`reader.library_compare` asks by point while `reader_compare.by_point` is on, from every door
(CA3's one request, plus `by_point`; with CA3 off the pinned request asks by point too).
`LA.compare_table(..., by_point=True)` adds `points` (`point_rows`: per point its id, label,
kind, the label's voice, one cell per column keyed by the by-book row's `key`, and its pairs'
relations by column key) and `contract`; `rows` stay the by-book view. The prompt contract adds
`libraryAsk.compareByPoint`.

### The grid (`ComparePointTable.tsx`; §5.1, X3, X4)

- A row per point, a column per book (the anchor's or open book's first, *your passage*), the
  learner's *› you* column last. The point column is sticky; a grid wider than its frame scrolls
  sideways inside the frame (`POINT_COLUMN_PX`, `READABLE_CELL_PX`, `YOU_COLUMN_PX`: layout
  bounds in CSS px, not learned constants).
- A row header is LearnLoop's (`◇`, dotted rule; *LearnLoop's point* the first time, then only
  `◇`) or, for a requested view, the learner's (`›`, amber rule).
- A cell is the book's verified words (`§ "…"`, two lines at most, `more`/`↵` to expand), then
  LearnLoop's line under a dotted rule; *— not addressed here*, or *— not here* on a requested
  view. A view no book fills reads *· not found in your library*, with *where else is this
  explained? ▸* where the host offers it.
- Chips (`comparePoints.ts` `rowChips`): exactly the relations the row's pairs returned, in the
  table's order, in the shipped plain words; *the same claim* only when every pair of the books
  quoted on the row said it; *only in Axler* when one book alone is quoted; no colour, no count.
  `↵` on the row header (or a press on a chip) opens the pairs: *Axler ⇄ Strang · different
  assumptions · ◇ statement § "…" / § "…"* (RW4d's band, on its row).
- The three voices never share a box; a screen reader hears *"Strang, on why eigenvalues exist.
  From the book: … LearnLoop's reading: …"*, *"…: not addressed here."*, chips as *"LearnLoop's
  reading of how they relate: …"*, and once the table is there *"Comparison ready: 4 points"*
  (Q7). Nothing takes focus on landing or animates (K16).

### Keep, takes and hidden rows (§5.2, §12.2)

The grid holds keep (`k`, *keep comparison ⇄*), *remove*, the takes and hide row; `CompareKeep`
renders nothing under a table by point. `reader.library_compare_keep` gains `hiddenPoints` and
takes by row (`pointId`) or on the whole comparison (`about: "comparison"`); exactly one target
per take.

`kept_comparisons.py`, a keep by point (`layout: "by_point"`), maps each quoted cell of every
row not hidden to **one claim** (`source_objects`, proposed, AI-authored, cited to the block
holding its quote, rechecked against the block as it is now), with the row's `point: {id, label,
kind}` and its line in `content_json`; each verified relation of a row becomes a relation
between that row's two claims by the same `RELATION_MAP`. A row take is a `learner_connects`
relation on the row's first two claims (a row no book fills is refused: nothing to hold it); a
take on the whole comparison relates its first two claims from different books. A take is
idempotent by its row and words. A hidden row before Keep is left out (and recorded); hiding a
kept row supersedes its claims, relations and takes (append-only; each successor recorded on
`hidden_rows`, which `relation_lineage` now reads with the removals); showing it again proposes
it again from the stored comparison. Reopening shows only kept cells and relations, hidden rows
folded with their stored cells (so *show* can propose them). A v1 comparison, or any keep while
the switch is off, is kept by source exactly as before.

### Keys (§5.5)

Checked against the comparing posture's keys. Roving focus starts on the first row header and
moves only on the learner's key: `↑↓←→`, `Home`/`End`; `Space` peeks the cell's passage (the
library answer's peek, now able to read any compared passage); `o` opens the book there in the
left pane (with a crumb); `↵` expands a quote or opens a chip's pairs; `t` your take; `-` hide
or show; `v` by point / by book; `k` keep. `/` (refine), `+` (*+ add a book*, new in
`useCompareControls`) and `Ctrl+↵` (the tutor about this comparison) are left to the
comparison's controls, as before; `Esc` closes pairs or a take box first, then belongs to the
posture.

### Narrow widths and by book (§5.6, X5)

- Below the app's 1,040 px breakpoint, or in a pane too narrow for the point column and two
  readable cells, the grid becomes cards by point (the label and chips, each book's cell under
  its name, *› you* at the foot) with the same keys (`↑↓` points, `←→` books).
- The comparing posture stacks below the breakpoint (the comparison above the book, UX §3.1), and
  a resized window re-clamps the remembered pane width (RW4a computed it once, at mount).
- *By book* (`v`, or the toggle in the header; remembered per device in `localStorage`,
  `ll.compare.layout`): one card per book with its cell on every point.

### Old comparisons (§5.3)

A comparison with no points (stored before v2, or any comparison while the switch is off)
renders by book exactly as today (three cells and the relations band), with no "old" label.
Where a library question hosts the table, *compare again by point ▸ · runs one comparison*
re-runs its passages by point (pins = its passages, its views kept).

### The kill switch

`[reader_compare] by_point = true`. Off, exactly today: the Reader requests v1 (no `by_point`
in the call, `source_compare.v1` stored), the table has no `points`, the prompt contract has no
`compareByPoint`, the posture does not stack or re-clamp, keep is by source, and `hiddenPoints`
and row takes are refused (`reader_compare_by_point_disabled`). A keep by point made while on
reopens by book while off.

## 2. Parameters (no made-up constants, owner 2026-10-24)

Classified in `src/learnloop/params/parameter_registry.py` (structural, display):

- `reader_compare.by_point`: a kill switch.
- `reader_compare.max_perspectives = 4` (`keep`: a stored-size bound, §12.2; `le=8`, the RPC's
  own request bound). It replaces CA3's module constant `MAX_PERSPECTIVES`; the RPC, the keep
  contract (`compareKeep.maxPerspectives`) and the refine box's limit read it.

No weight, margin or threshold was added. The chip rule is the spec's table; the clamp length
for *more* (140 characters) and the column widths are display bounds.

The defaults snapshot moves only because the effective config gains the two keys: all 28
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` values were recomputed from the composed defaults
(`defaults_fingerprint_for_version`), each with one comment. The DB/config reference was
regenerated (1,071 leaves) and validated (`errors: []`).

## 3. Tests changed to pin v1 with the switch off

Tests that pin RW4d's keep by source, RW1c's and RW4d's switch-off goldens and CA3's anchor
keep now set `reader_compare.by_point = false` (each with a comment), because the v1 path is
exactly what the switch restores: `test_compare_sources_keep.py` (its `library` fixture),
`test_compare_keep_switch_off.py`, `test_reader_tutor_switch_off.py`,
`test_reader_ca3_codex_review.py` (its `library` fixture), `test_reader_ca3_compare_anywhere.py`
(the switched-off request; the four doors now also send `by_point`), and
`test_rw4_kill_switches.py` (the on-contract gains `compareByPoint`). The shared fake
(`tests/source_service_fakes.py`) answers `SourceComparisonV2`.

## 4. Deviations and open points

1. **Column headers** show the book and page (*§ Strang p.12*), not the section locator
   (*§6.1*): the comparison's row carries no section today. Adding it is a read of the block's
   section path at table time; left for the owner to want.
2. **Pending** stays CA3's one line; the provisional *by book* layout of excerpts before the
   rows exist (§4.2) needs a progress signal from the job, which it doesn't have.
3. **Compare again by point** is offered where a library question hosts the table (a library
   answer's *you compared these on … · reopen ⇄*, the comparing pane). A kept comparison reopened
   from a `⇄` margin mark has no library question beside it, so it opens by book there with no
   re-run button.
4. **Hiding a kept row supersedes its takes too** (they are learner relations on that row's
   claims); showing the row again proposes its cells and relations again but not the takes,
   which stay superseded (their words are kept in the superseded rows and the hidden-row
   history).
5. **A v2 comparison viewed with the switch off** (a keep made while on) renders by book from
   the stored cells (each cell is its book's contribution there).
6. No real comparison call verified the v2 request (launch rule: no live calls). The schema is
   built from typed models, so the provider gets a strict schema; a minimal paid check on a
   backup copy is cheap if the owner wants one before the landing.

## 5. Gate (this step; the full suite runs once at the landing)

All test commands inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n 6` over the 110 files below: **2023 passed, 12 skipped,
  3 xfailed, 4 failed**. The four were contract goldens that pin the prompt contract's
  `libraryAsk` keys (`test_figures_switch_off.py` x2, `test_reading_paths.py` x2): they now pop
  CA4's `compareByPoint` as they pop CA3's `compareScope`; rerun, both files: **59 passed**.
- Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck`: **clean**;
  `npx vitest run --maxWorkers=4` over the 68 files below (every vitest file that imports
  the Reader screen, the library pane or answer, the comparison controls, keep or the new
  table): **68 files, 505 passed**; `npm run frontend:build`: **built**.
- No change under `src-tauri` (the keep RPC is a passthrough), so no `cargo check`.
- DB/config reference: `db_generate_reference.py` then `db_validate_reference.py` (under
  `env -i` with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR): **`errors: []`** (1,071 leaves; the
  two prose leaf counts updated).
- No migration and no DB/connection code, so no durability lane.

Pytest files run (new: `test_reader_ca4_table_by_point.py`):
`test_ad1_codex_review_fixes.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_architecture.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_cli_help_snapshot.py`, `test_compare_keep_switch_off.py`, `test_compare_sources_keep.py`, `test_compare_sources.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance.py`, `test_e0_review_round2.py`, `test_e0_review_round3.py`, `test_facet_locks_landing.py`, `test_field_workbench_signals.py`, `test_figure_offers.py`, `test_figure_predictions.py`, `test_figure_region.py`, `test_figure_revisions.py`, `test_figures_rpc.py`, `test_figures_rw5b_fix_round2.py`, `test_figures_rw5b_review.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_find_sources_intents.py`, `test_grading_cli.py`, `test_intent_codex_rereview.py`, `test_kinship_feature.py`, `test_learner_report_superseded.py`, `test_library_ask_expand.py`, `test_library_ask.py`, `test_library_ask_review.py`, `test_library_exercises.py`, `test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_output_budget.py`, `test_p0_cutover_mvp08.py`, `test_passage_links.py`, `test_plan_determinism.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport.py`, `test_plan_follows_path.py`, `test_public_tip_guards.py`, `test_reader_ca1_as_printed.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca3_codex_rereview.py`, `test_reader_ca3_codex_review.py`, `test_reader_ca3_codex_round3.py`, `test_reader_ca3_compare_anywhere.py`, `test_reader_ca4_table_by_point.py`, `test_reader_compare_table.py`, `test_reader_dialogue.py`, `test_reader_find_sources_callers.py`, `test_reader_inquiry_kill_switch.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_rw2b_review.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_retrieval_interventions_write_points.py`, `test_roles_judges.py`, `test_roles_switch_off.py`, `test_rw2c_switch_off.py`, `test_rw4d_rw3b_composition.py`, `test_rw4_kill_switches.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_sidecar_reader.py`, `test_sidecar_serializer_snapshot.py`, `test_source_roles.py`, `test_source_service_spend_accounting.py`, `test_source_service_spend_envelopes.py`, `test_sources_merge_composition.py`, `test_source_space_resolver.py`, `test_table_roles.py`, `test_teacher_te0_review_fixes.py`, `test_tool_registry.py`, `test_tool_results_withhold_answers.py`, `test_tools_cli.py`, `test_tracked_fixture_databases.py`, `test_tutor_tool_requests.py`, `test_ux_phase2_shell.py`.

Vitest files run (new: `screens/reader/comparePointTable.test.tsx`):
`app/App.fixRound2.test.tsx`, `app/App.fixRound3.test.tsx`, `app/App.fixRound4.test.tsx`, `app/App.fixRound5.test.tsx`, `app/App.shell.test.tsx`, `app/App.today.test.tsx`, `app/App.wrapUpSkim.test.tsx`, `app/classicIsBase.test.ts`, `app/shellChrome.test.ts`, `screens/attentionBudget.test.tsx`, `screens/reader/checkOffer.test.ts`, `screens/reader/compareKeepSwitchOff.test.tsx`, `screens/reader/compareKeep.test.tsx`, `screens/reader/comparePointTable.test.tsx`, `screens/reader/compareScopeCodexReview.test.tsx`, `screens/reader/compareScope.test.tsx`, `screens/reader/figures/advancedPanels.test.tsx`, `screens/reader/figures/libraryOfferSettle.test.tsx`, `screens/reader/figures/readerFigures.test.tsx`, `screens/reader/figures/showMe.test.tsx`, `screens/reader/figures/tutorOfferPress.test.tsx`, `screens/reader/figuresWithReadingPath.test.tsx`, `screens/reader/intentBoxInShell.test.tsx`, `screens/reader/IntentBox.test.tsx`, `screens/reader/intentSwitchOff.test.tsx`, `screens/reader/libraryAskJobs.test.tsx`, `screens/reader/libraryAskSwitchOff.test.tsx`, `screens/reader/libraryAsk.test.tsx`, `screens/reader/libraryExercisesReader.test.tsx`, `screens/reader/libraryExercises.test.tsx`, `screens/reader/libraryRoles.test.tsx`, `screens/reader/nextStepFold.test.tsx`, `screens/reader/paletteAskPostures.test.tsx`, `screens/reader/paletteAsk.test.tsx`, `screens/reader/readerHooks.parity.test.tsx`, `screens/reader/readingPathsReader.test.tsx`, `screens/reader/readingPathsRefresh.test.tsx`, `screens/reader/readingPathsSwitchOff.test.tsx`, `screens/reader/recapSwitchOff.test.tsx`, `screens/reader/rw1bReview.test.tsx`, `screens/ReaderScreen.branches.test.tsx`, `screens/ReaderScreen.checkOffer.test.tsx`, `screens/ReaderScreen.cuesSwitchOff.test.tsx`, `screens/ReaderScreen.discoveredCuesReview.test.tsx`, `screens/ReaderScreen.discoveredCues.test.tsx`, `screens/ReaderScreen.doseOffer.test.tsx`, `screens/ReaderScreen.followsLearner.test.tsx`, `screens/ReaderScreen.guide.test.tsx`, `screens/ReaderScreen.inquiryOff.test.tsx`, `screens/ReaderScreen.inquiry.test.tsx`, `screens/ReaderScreen.k7.test.tsx`, `screens/ReaderScreen.marginMarksReview.test.tsx`, `screens/ReaderScreen.marginMarks.test.tsx`, `screens/ReaderScreen.parity.test.tsx`, `screens/ReaderScreen.pdfSelection.test.tsx`, `screens/ReaderScreen.preparing.test.tsx`, `screens/ReaderScreen.quickcheck.test.tsx`, `screens/ReaderScreen.recapReview.test.tsx`, `screens/ReaderScreen.recap.test.tsx`, `screens/ReaderScreen.review.test.tsx`, `screens/ReaderScreen.rw2cExample.test.tsx`, `screens/ReaderScreen.workbench.test.tsx`, `screens/reader/tutorBoundAsk.test.tsx`, `screens/reader/tutorExercises.test.tsx`, `screens/reader/tutorReader.test.tsx`, `screens/reader/tutorSwitchOff.test.tsx`, `screens/reader/voices.test.tsx`, `screens/workbench/switchOff.test.tsx`.

## Landing onto main (2026-10-31)

Landed in `learnanything-dl1` on `reader/ca4-table-by-point` (stage tip `8aaceff1c`, base `d7850780b` = CA3's
verified tip) by merging `main` `5dbfd42b8`: Reader CA3's landing (with CA5a, the cold-retry successor mvp-0.38,
the Oct 27 follow-ups and the RW5c design spec already on main). Main was neither fast-forwarded nor pushed. No
migration and no successor: CA4 stays display and proposals at every version.

### Commits and conflicts

| Commit | What |
|---|---|
| `2d93d8ba6` | `--no-ff` merge of `main` `5dbfd42b8`. **Conflicts** (CA3-landing resolutions vs CA4 edits): `template.py`, every default snapshot mvp-0.9 … mvp-0.37, where CA4's note is kept beside main's CA5a and cold-retry notes, and mvp-0.38 (cold-retry's new snapshot) gains CA4's line. **All 29 fingerprints** (mvp-0.9 … mvp-0.38) were recomputed with `defaults_fingerprint_for_version`, the template `.pyc` was cleared, and a recheck found 0 mismatches. The as-built notes in `ux_reader_compare_ask_v1.md` (CA5a's and CA4's, both kept). The switch-off contract pins `test_compare_keep_switch_off.py` and `test_reader_tutor_switch_off.py` now turn off CA3's, CA4's **and** CA5a's additions; `test_figures_switch_off.py` and `test_reading_paths.py` auto-merged and already pop or strip all three (`compareScope`, `compareByPoint`, `correspondence`). 431 generated reference notes were taken from main and regenerated in the next commit. `useLibraryAsk.ts` (CA3's `runCompare` and CA5a's `runPinsCompare` beside CA4's `compareAgain`/`whereElse`/`peek`), `LibraryAnswer.tsx`, `ReaderScreen.tsx`, `CompareScope.tsx`, `api/dto.ts`, `api/client.ts`, `library_ask.py` (both), `schema.py`, the parameter registry and `db_generate_reference.py` auto-merged; `npm run typecheck` was clean on the merge. |
| `c1259ddf5` | DB/config reference regenerated on the merge. The hand-written counts in `Configuration.md` and `Database.md` move to **1073 effective leaves in 75 sections** (main's 1071 + CA4's 2). `db_validate_reference.py`: **errors []**; `validate_vault.py` passes (1163 notes). |
| `36e3f1892` | The interaction tests (below). |
| `43f50b271` | `--no-ff` merge of `main` `e668f7121` (the Codex CLI 0.165 lockdown fix), after the full suite ran; no conflicts. |

`git diff main` lists no binary, no tracked database and nothing under `fixtures-local/`; `.gitignore` is unchanged.

### Interactions with CA3 and CA5a

All of these passed the first time; nothing needed fixing. Each new test was mutation-checked: with
`CompareTable`'s by-point branch disabled the two by-point vitest cases fail; with the sidecar's `by_point`
forced off, the five by-point server cases fail.

**(i) CA5a's compare on a found section, by point and by book.** `findSectionByPoint.test.tsx` (vitest, the
whole Reader screen, the four cases `by_point` on/off x CA3 on/off): the first comparison fails and *try again ↵*
reruns it. With CA3 off it is CA5a's library-ask path: the rerun keeps the same two pins (CA5a F5/F8), no second
ask and no notes. With CA3 on it is CA3's selection door: the rerun sends the same request, and no library ask is
made. When the sidecar answers v2 (`by_point` on), the table by point renders (`data-compare-points`, the row's
label); when it answers v1 (`by_point` off), the by-book table renders, with no points and no *compare again by
point*. On the server (`tests/test_reader_ca4_landing.py`, C0a's coverage vault, from `reader.correspondents`' hit):
- CA5a's pinned compare asks `by_point=True` and returns a v2 table whose cells sit in the columns. Off, it asks
  without `by_point` and returns no `points` or `contract`. A rerun is the same comparison (cached; the same table
  apart from exposure ids and the `cached` status).
- CA3's selection door narrowed to the hit's book does the same. Off, the request and the table are CA3's
  landing's: no `by_point`, no points.

**(ii) CA3's tutor and named books with v2 tables.**
- A stored v2 comparison from the selection door: the tutor named by `comparisonId` gets every passage it
  compared, or says what it left out, and its prompt carries exactly the grounded passages.
- With `by_point` on, a one-book selection (`too_few_sources`, nothing compared, no points) is asked about by
  `passagesId`, as before.
- Named books narrow the v2 table: its columns are the anchor's book and the named book only, and no cell names
  the unnamed third book.
- *Compare again by point*: a v1 comparison of named books was shown while `by_point` was off. Then the
  frontend's request (CA3's pins door with the table's passages and the books it shows; the payload is pinned by
  `comparePointTableCodexReview.test.tsx` F6) returns a v2 table over exactly those books.

**(iii) The switch matrix** (`reader_compare.by_point` x `reader_compare.scope_enabled` x
`reader.correspondence.enabled`, all eight): `libraryAsk.compareByPoint` is present exactly when `by_point` is on.
`libraryAsk.compareScope` and the palette's `compare_books` are present exactly when scope is on.
`correspondence` is `{enabled, findSection}` exactly when correspondence is on. With those removed, the eight
contracts are identical to the all-off one. `by_point` off = v1 requested and the table by book exactly as CA3's
landing, as (i) shows on both paths. `test_switched_off_the_reader_requests_v1_and_renders_by_book_exactly`
covers the pins.

### Regeneration

- DB/config reference: regenerated and validated as above. Defaults fingerprints: all 29 recomputed.
- The CLI help snapshot, sidecar serializer snapshot, desktop RPC contract and mobile allowlist pass as merged.
  CA4 adds no RPC (`hiddenPoints` rides on the existing keep RPC), so nothing else needed regenerating.
- Targeted run after the merge (44 files: every switch-off pin, the CA3/CA4/CA5a files, library ask, compare keep,
  section coverage RPCs, the RPC/serializer/CLI/mobile pins, the upgrade and config tests; `-n 6`, 5G scope):
  **899 passed**, 6 skipped (11 min 4 s).

### Gate (`env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/ca4/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`; `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite at `36e3f1892` (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,435 passed, 3 failed**, 89 skipped, 47 xfailed. pytest 2,082.6 s (34:42); wall 34 min 46 s from taking the lock (it waited 30 min for another worktree's run, 15:55 to 16:26). The 3 failures were exactly the known environment pins for the installed Codex CLI 0.165.0: `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` and `test_codex_isolation_mcp_check::test_the_installed_codex_passes_the_launch_check[False/True]`. Main at the time (`5dbfd42b8`) failed the same three. |
| `main`'s Codex 0.165 lockdown fix (`e668f7121`), merged afterwards (`43f50b271`, no conflicts; CA4 touches no Codex file) | `test_codex_cli_0165_lockdown.py`, `test_codex_isolation_mcp_check.py`, `test_diagnosis_isolation.py` on the merged tip (5G, `-n 6`): **68 passed** (5.2 s; wall 7 s). The three failures above pass there. No full-suite rerun: the merge touched only the Codex lockdown and its tests. |
| durability at `43f50b271` (`-m durability`, flock, 5G scope, `-n 6`) | **176 passed**, 1 skipped (57.8 s; wall 59 s from the lock, which other worktrees held for about 33 min first) |
| owner lane at `36e3f1892` (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-ca4/`) | 83 passed, **2 failed**, 4 skipped (57.5 s; wall 59 s). The two failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy. |
| frontend (`apps/learnloop-tauri`, at `36e3f1892`) | `npm install` ok; `npm run typecheck` clean; whole vitest (`--maxWorkers=4`, 5G): **228 files, 2010 passed** (58.2 s; wall 59 s); `npm run frontend:build` ok (4 s); `cargo check --manifest-path src-tauri/Cargo.toml` ok (39 s) |

No timing-looking failure appeared, so nothing needed a rerun.

### Smoke on owner copies

The smoke ran on fresh backup-API copies of the same three mvp035 owner copies (`fixtures-local/smoke-ca4-fresh/`).
Each copy was upgraded with `learnloop upgrade --to mvp-0.38` (prints `mvp-0.35 -> mvp-0.38`), then
`rebuild-derived-state`. The RPCs ran through a real sidecar process (`python -m learnloop_sidecar` over stdio).
- Everything ran under `env -i` with an empty `HOME`, `CODEX_HOME` and config dir,
  `LEARNLOOP_COVERAGE_MODELS=off` and AI base URLs at `127.0.0.1:9`, so no comparison could be made.
- Audit hooks refused non-loopback sockets and process starts, and **logged nothing**.
- Only counts, statuses and booleans were recorded (driver: `fixtures-local/landing/smoke_ca4/smoke.py`, control:
  `control.py`).

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| stored comparisons / kept comparisons (v1) | 0 / 0 | 0 / 0 | 0 / 0 |
| a kept v1 comparison reopens by book | none to reopen (no copy has a comparison) | same | same |
| contract `compareByPoint`: on / off / on again | true / absent / true | same | same |
| selection door on one passage, `by_point` on: status, rows, points | `too_few_sources`, 1, 0 | same | same |
| ... `by_point` off | `too_few_sources`, 1, 0 (the same) | same | same |
| tables changed by the off/on toggle | none beyond `facet_capability_evidence` and `facet_recall_state`, which change in **every** sidecar session with no toggle too (control run: two plain sessions, then off, on, on; the same two tables move at every step); `source_comparisons`, `library_asks` and every other table unchanged | same | same |
| `rebuild --shadow` before / after (mastery/facet/schedule) | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 |
| `model_call_receipts` rows added | 0 | 0 | 0 |

### Owner notes

- Kill switch: `[reader_compare] by_point` (default true). With it off, v1 is requested and every comparison is
  by book exactly as CA3's landing (contract without `compareByPoint`, today's keep, rows and row takes refused).
- `[reader_compare] max_perspectives = 4` is a `keep` key: a bound on stored size, not a tuned number.
- No upgrade is needed for CA4 itself. The owner vaults' pending `upgrade --to mvp-0.38` (cold-retry) is unchanged
  by it. None of the owner copies holds a comparison, so no kept v1 comparison could be reopened on real data;
  the test `test_a_v1_comparison_kept_before_ca4_reopens_by_book` covers that path.

### Open items

- **Section locators in column headers**: the headers show the book and page, not the section.
- **The provisional by-book layout while the comparison runs** is not built (the job has no progress signal).
- **Rerun on a margin-mark reopen**: a kept comparison reopened from `⇄` has no library question beside it, so it
  opens by book with no *compare again by point*.
- **Hiding a kept row** supersedes its takes. Showing the row again re-proposes its cells, but not the takes.
- **Cross-block quotes** (a quote spanning two anchor blocks) show as not addressed.
- **No real v2 call has been checked** (no live calls at landing).
- **From this landing:**
  - In every sidecar session, the owner copies' `facet_capability_evidence` and `facet_recall_state` rows are
    rewritten, whether or not anything was toggled. `rebuild --shadow` still reads 0/0/0. This is not CA4's: it
    happens with the switch untouched. It is noted because a "nothing stored moved" check has to exclude those two
    tables.
  - CA5a's comparison (CA3 off) renders under the library answer's hits. If the section's ask returns no hits,
    the comparison runs but nothing shows it. This was true before CA4 too. The landing test gives the ask hits
    for both passages.
  - The installed Codex CLI's launch-check pins failed in the full suite, on main too. Main's own lockdown fix
    (`e668f7121`), merged here as `43f50b271`, makes them pass; see the gate.
