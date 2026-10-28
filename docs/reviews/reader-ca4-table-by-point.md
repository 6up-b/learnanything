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
