# Reader CA1 (the problem as printed): Codex review and fixes

Stage `reader-ca1-problem-as-printed`, branch `reader/ca1-problem-as-printed` (worktree
`learnanything-dl2`), base `main` `0db8291c1`. The review was static (codex job
`20261025-165056-DlrZ7l`, against `ca2c638e8`). It found 8 defects, two of them High. I
reproduced each one with a failing test before fixing it: the new tests were run against the
pre-fix sources of `ca2c638e8` and the pre-fix frontend, and failed there (see "Reproduced"
below). All 8 are fixed. None was rejected.

**Still true after the fixes:** no migration, no successor, no model call, no new exposure
context, no new configuration key and no new decision parameter. The new rules are
structural: the crop join compares areas exactly, with no tolerance, and the region is clipped
to the block's own box. The only new limit is `detail_key.isidentifier()`, a guard on a SQL
JSON path, not a parameter. No paid calls were made and nothing ran on vault copies.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Standalone cold retries and diagnostic probes receive unrestricted crops | fixed | 078aed29d | `tests/test_reader_ca1_codex_review.py::test_a_standalone_cold_follow_up_hides_the_print_with_no_check_once`, `::test_a_certification_cold_probe_hides_the_print_and_nothing_locates_it`, `::test_an_active_diagnostic_presentation_hides_the_print_until_it_is_answered`; vitest `PracticeScreen.asPrinted.test.tsx` "a cold follow-up: only the figure…", "a diagnostic block: no original page…" |
| F2 | High | Centre-based crop merging includes neighbouring material | fixed | 078aed29d | `::test_a_neighbour_reaching_into_the_gap_splits_the_crop_though_its_centre_is_outside` (the review's own boxes), `::test_a_figure_only_crop_never_takes_in_the_stem_beside_it`, `::test_a_neighbour_touching_the_union_only_at_its_edge_does_not_split_it`, `::test_a_neighbour_already_inside_one_of_the_problems_boxes_does_not_block_the_join` |
| F3 | Medium | The kill switch leaves several CA1 surfaces operational | fixed | 078aed29d | `::test_the_switch_off_crops_nothing_through_the_multi_block_form_and_keeps_the_single_block`; vitest `AsPrinted.test.tsx` "…shows nothing when the server crops nothing (disabled / no_geometry / not_found)" (candidates and compare methods use this component), `workbench/asPrinted.test.tsx` "the switch off: a bound problem…" and "…a problem not yet bound…" |
| F4 | Medium | Selection-imported problems lose the crop after binding; the region selection's sub-box is ignored | fixed | 078aed29d, 93df11dc9 | `::test_a_reader_selection_import_shows_its_print_after_binding` (through `exercise_authoring.import_exercises`, the real write path, with a fake client), `::test_a_region_selection_s_sub_box_is_the_crop_shown`, `::test_the_workbench_session_carries_the_region_it_was_imported_with`, `::test_an_ai_proposal_over_the_same_blocks_is_not_the_book_s_problem`; vitest "a selection import: the page's locator and the original page, counted as the book", "a learner-drawn region rides with both reads", workbench "a problem not yet bound: … its region …" |
| F5 | Medium | Missing crop geometry also suppresses a usable original page | fixed | 078aed29d | `::test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop`; vitest "a page without a box: the crop says it can't be made, no picture" |
| F6 | Medium | The workbench's "original page" button does not open the original | fixed | 078aed29d | vitest `workbench/asPrinted.test.tsx` "a bound problem's original page opens the page itself…", "no original page where the server found no page image, and none while the book is hidden"; `AsPrinted.test.tsx` "after feedback the original page opens the page itself and offers the Reader" |
| F7 | Medium | Transcription reports lead to an inert repair action | fixed | 078aed29d | vitest `MaintenanceScreen.transcription.test.tsx` (3): the count, the learner's words, the wording beside the page, one working *Fix the wording* (edit_practice_item, then the feed is read again), the inspector link |
| F8 | Medium | Concurrent maintenance refreshes can erase report text | fixed | 078aed29d, 93df11dc9 | `::test_a_feed_refresh_reading_before_a_report_never_overwrites_it` (the review's interleaving, with a second connection committing between the refresh's read and its writes), `::test_a_reworded_card_resolves_but_a_report_on_the_new_wording_meanwhile_is_kept`, `::test_two_reports_on_two_connections_both_count` (4 threads, 4 connections), `::test_the_feed_upsert_of_other_notices_is_unchanged` |

### What each fix does

- **F1.** `practice.as_printed`'s `cold_now` now treats the item as on your own when any of
  these holds: a due cold follow-up (`cold_retry`, `certification_cold_probe`, read with
  `intent.checks.cold_followup_duty`), an active diagnostic presentation of the item (new
  `Repository.active_probe_presentation_for_item`, status `selected`/`served` in any episode),
  or DL2's served "Check once". None of them needs a commitment. Each gives the figure-only
  view (Q10) or nothing, and an error reading them still fails closed. The frontend cold
  follow-up test now expects what the server sends (figure only, no locator). The new
  diagnostic-block test covers what the review's last bullet said was missing.
- **F2.** `crop_boxes` joins two consecutive own boxes only when the joined rectangle shows no
  more of any other block than the two parts already did. It compares the other block's area
  inside the rectangle with its area inside the parts, using inclusion-exclusion over two
  rectangles in exact `Fraction` arithmetic. A neighbour that only reaches into the gap now
  splits the crop. A box that merely touches the edge does not. A sliver that one of the
  problem's own boxes already overlaps (a caption box drawn into a figure) does not block the
  join, because the join shows no more of it. The figure-only crop already treats the
  problem's own stem as another block, so two figures with text between them stay two crops.
- **F3.** The multi-block form of `reader.block_original_region` (CA1's own) answers
  `status: "disabled"` with no crops when `practice.as_printed.enabled` is off. The
  single-block form keeps its pre-CA1 behaviour. The form gains `render` (`false` is a cheap
  geometry read that draws nothing) and `region`. Both are refused on the single-block form.
  `BlocksAsPrinted`, used for exercise candidates, compare methods, the unbound workbench and
  the maintenance card, reads first with `render: false` and renders nothing unless a crop
  can be made. With the switch off, the workbench's original-page button also disappears,
  bound or not.
- **F4.** `reader.as_printed.printed_origin` is the one place that knows where an item's
  print is. It uses the `canonical_exercise`, or a Reader selection import. A selection
  import is identified by its `learner_item_authored` event (`mechanism =
  reader_exercise_import`, the existing `source_service.is_reader_import`); provenance alone
  is not enough, because AI proposals over sources share `canonical_extract`. Its blocks come
  from its `block_span_v1` source refs, or failing those from its `source_exercise_imports`
  rows. The view, the report and the practice-screen locator (a new `printed-locator` line
  for items without a canonical exercise) all use it.
  - **Region selections:** the Reader sends `selection.region` with the import's
    `rawSelection` (*import* and *work through this*). `exercise_authoring` stores it on that
    block's source ref (`region: {page, bbox}`), and the view crops it clipped to the block's
    box. Before the import binds, the workbench session view carries it as `printRegion`
    (present only when there is one), and the pending crop passes it through the multi-block
    form. Region parsing lives in `learnloop.ingest.ir` (`page_region`, `selection_region`),
    so `content.authoring` gains no new cross-domain edge.
- **F5.** When no own block has a box but one has a page and the original PDF is readable
  (a pypdf extraction), the view is `kind: "page"` with `crops: []`, `status:
  "no_geometry"` and the notice *the crop isn't available for this problem · the original
  page is*. It also carries the original-page target: the first paged block, with its page's
  blocks outlined. The free crop never substitutes the page. Without the PDF the view is
  still `none`.
- **F6.** The workbench's *original page ↗* now opens `OpenInSource`'s page view, outlining
  the problem's blocks on that page. It records its exposure as every source opening does;
  the book is already shown and counted there, so it costs nothing more. It appears only
  where the server found a page image: the item view's `originalPage` once bound, or the
  blocks' read before binding. `OpenInSource` gains *open in the Reader ↗* (§8.3):
  - in the workbench it takes the book pane to the block (`onPeekPassage`);
  - after feedback it navigates through the shell's existing `onOpenStudied`. The view's
    target now carries `sourceId`, which that navigation needs;
  - it is **not** offered on the practice screen before Submit, because that link would
    take the learner out of an attempt in progress. There the page stays a modal that
    counts as the book (Q12).
- **F7.** The Maintenance feed renders a `transcription_mismatch` notice as its own card:
  - how many reports there were;
  - the learner's notes;
  - the wording reported (the report's detail now keeps `prompt`), beside the page
    (`BlocksAsPrinted`);
  - a link to the inspector;
  - a working *Fix the wording*: an inline editor that saves through `edit_practice_item`
    (the card controls' reword) and reads the feed again, where the report resolves because
    the wording changed.

  The generic action button, which has no handler for any type, is not shown for this type.
- **F8.** A report's read of the stored detail, its append, the upsert and the reopening now
  run as one `BEGIN IMMEDIATE` transaction (`Repository.atomic()`), so concurrent reporters
  serialise. The feed refresh no longer re-upserts transcription reports from a snapshot, and
  the generic aging loop skips them. A report is resolved only by
  `Repository.resolve_maintenance_notice_if_detail`, a single guarded `UPDATE` that holds
  only while the stored `prompt_sha256` is still the one the refresh read. A report filed
  meanwhile is therefore never resolved: neither one on the new wording nor a reopening.
  `report_transcription_mismatch` now takes the item's `origin` from its caller (the sidecar
  handler), so `ops` gains no edge to `reader`.

### Claims that did not hold (from the review), now

- "Every screen is as before" with the switch off: true now for candidates, compare methods,
  the workbench (bound and unbound) and the multi-block RPC (F3).
- The crop contains only the problem's own material: it contains no area of another block
  beyond what the problem's own boxes already overlap (F2).
- The bound Reader workbench shows the item's print: true for selection imports now (F4).
- The workbench link opens the page: it does now (F6).
- Every report keeps its text and count: yes, even under concurrent refreshes and reporters (F8).
- The test named "during a diagnostic block or a cold follow-up" now has a separate
  diagnostic-block test.

### Reproduced (the new tests on the pre-fix code)

- **Backend:** the 18 tests of `tests/test_reader_ca1_codex_review.py` were run against the
  pre-fix sources of `ca2c638e8`, using a scratch copy that stubs the new `NO_CROP` import;
  the sources were restored from the WIP commit afterwards. **13 failed.** These cover the
  F2 gap and figure-only crops, F1 for a cold retry, a certification probe and a diagnostic
  presentation, F3, F4 for the selection import, the region and the session region, F5, and
  F8 for refresh-interleave, reword-race and two-connection. **5 passed there.** They pin
  behaviour that must not change: the edge-touch and overlapping-caption joins, the AI
  proposal with no print, the single-form validation, and the feed's own upserts.
- **Frontend:** the new and updated vitest files were run against the pre-fix frontend.
  **15 failed:**
  - all 3 Maintenance tests (F7);
  - all 5 workbench tests (F3, F4, F6);
  - 7 in `AsPrinted.test.tsx` (F3, F4 region, F5, F6).

## Gate (this step; the full suites run once, in the landing gate)

Every pytest, vitest and npm command ran in `systemd-run --user --scope --quiet -p
MemoryMax=5G -p MemorySwapMax=1G`, one at a time. pytest ran with `-n 6` and vitest with
`--maxWorkers=4`. Every Python/CLI command ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` in the session scratchpad (no routes reachable, no live
calls).

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, set 1 (51 files: the CA1 files, the contract tests and every test file of
  the modules changed): **1650 passed, 5 skipped**.
- Targeted pytest, set 2 (23 files: the workbench session view, the probe presentations and
  the authoring transport): **426 passed**.
- `--durable-sqlite` on `tests/test_reader_ca1_codex_review.py tests/test_reader_ca1_as_printed.py
  tests/test_maintenance_feed.py` (the new repository SQL and the two-connection reports under
  WAL + `synchronous=FULL`): **41 passed**.
- `npm install`: ok. `npm run typecheck`: clean. `npm run frontend:build`: built.
- vitest (122 files): **997 passed**.
- No change under `apps/learnloop-tauri/src-tauri`, so no cargo check. No migration and no
  schema change, so no durability lane beyond the above and no DB reference regeneration.

pytest set 1: tests/test_reader_ca1_as_printed.py tests/test_reader_ca1_codex_review.py tests/test_architecture.py tests/test_mobile_allowlist.py tests/test_sidecar_serializer_snapshot.py tests/test_desktop_rpc_contract.py tests/test_table_roles.py tests/test_coordinated_migrations.py tests/test_tracked_fixture_databases.py tests/test_cli_help_snapshot.py tests/test_config_refactor.py tests/test_public_tip_guards.py tests/test_registry_audit.py tests/test_sidecar_contract.py tests/test_maintenance_feed.py tests/test_graph_edit_proposals.py tests/test_placement_opening_probes.py tests/test_probe_pool_empty.py tests/test_sidecar_append.py tests/test_source_outcome_analytics.py tests/test_exercise_authoring.py tests/test_import_split_parity.py tests/test_required_method_authority.py tests/test_required_method_items.py tests/test_source_exercise_import.py tests/test_source_exercise_rpcs.py tests/test_library_exercises.py tests/test_facet_locks_landing.py tests/test_codex_output_schema.py tests/test_structured_transport_parity.py tests/test_reader_render_views.py tests/test_figure_region.py tests/test_span_view.py tests/test_sidecar_span_view.py tests/test_library_ask_review.py tests/test_intent_checks.py tests/test_intent_codex_rereview.py tests/test_intent_codex_review.py tests/test_intent_fix_round4.py tests/test_intent_fix_round5.py tests/test_intent_orchestrator_rulings.py tests/test_dl2_rw4b_keyed_pick_check.py tests/test_probe_episodes.py tests/test_hint_telemetry.py tests/test_ux_phase4_feedback.py tests/test_capture_desktop.py tests/test_compare_keep_switch_off.py tests/test_figures_switch_off.py tests/test_reader_rw3b_switch_off.py tests/test_rw2c_switch_off.py tests/test_compare_methods.py

pytest set 2: tests/test_hint_h2b_fix3.py tests/test_hint_h2b_fix4.py tests/test_hint_h2b_rereview.py tests/test_hint_h2b_review.py tests/test_plan_first_transport_offer_grants.py tests/test_reader_rw2b_fix12.py tests/test_reader_rw2b_fix4.py tests/test_reader_rw2b_fix5.py tests/test_reader_rw2b_review.py tests/test_reader_workbench_rw2a.py tests/test_ux_phase3_today.py tests/test_workbench_assistance.py tests/test_workbench_check.py tests/test_workbench_help_kill_switch.py tests/test_workbench_hints.py tests/test_workbench_route_example.py tests/test_workbench_text_gaps.py tests/test_evsi_router_composition.py tests/test_router_probe_ties.py tests/test_voi_merge_composition.py tests/test_voi_stopping.py tests/test_voi_v2.py tests/test_openrouter_client.py

vitest: src/app/App.fixRound2.test.tsx src/app/App.fixRound3.test.tsx src/app/App.fixRound4.test.tsx src/app/App.fixRound5.test.tsx src/app/App.shell.test.tsx src/app/App.today.test.tsx src/app/classicIsBase.test.ts src/app/practiceDraft.test.ts src/app/shellChrome.test.ts src/components/AsPrinted.test.tsx src/components/AskOverlay.capture.test.tsx src/components/AskOverlay.reader.test.tsx src/components/AskOverlay.suggestion.test.tsx src/components/AskOverlay.test.tsx src/components/SourceOffers.test.tsx src/copy/denyList.phase4.test.tsx src/screens/FeedbackScreen*.test.tsx src/screens/MaintenanceScreen.transcription.test.tsx src/screens/PracticeScreen*.test.tsx src/screens/ReaderScreen*.test.tsx src/screens/RepairOverFeedback.phase4.test.tsx src/screens/RepairScreen.phase4.test.tsx src/screens/feedback/*.test.tsx src/screens/reader/*.test.ts(x) src/screens/workbench/*.test.tsx (incl. the new asPrinted.test.tsx); 122 files in all.

## Open questions / follow-ups

1. *Open in the Reader ↗* is not offered on the practice screen before Submit, because it
   would leave an attempt in progress. The owner may want it, for example as "leave this
   problem and open the page in the Reader".
2. The page's hint before Submit is still counted by the client's book component, not
   re-derived on the server (the stage record's open question 5, unchanged).
3. Selection imports written before this fix carry no `region`. Their crop is their whole
   blocks; new region imports keep the sub-box.

## Re-review (codex-job 20261025-172851-2CmngR, VERDICT: REOPENED)

The re-review confirmed F1 and F2 fixed and found three defects introduced by the fix commits.
Each was reproduced first: the Python test failed on the fix commit `ce75b42b8`, and the
vitest cases failed against the pre-fix frontend sources (4 failed) before the fix was
restored (25 passed).

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | — | cold administrations without a commitment | confirmed fixed | `ce75b42b8` | (re-review) |
| F2 | — | exact-area crop joins | confirmed fixed | `ce75b42b8` | (re-review) |
| F9 | High | selection imports treat neighbouring exercises as owned material | fixed | `4103832cf` | `tests/test_reader_ca1_codex_review.py::test_two_exercises_split_from_one_selection_each_crop_only_their_own_block`, `::test_a_split_whose_ownership_cannot_be_read_offers_only_the_charged_page`, `::test_a_split_written_before_ownership_was_kept_withholds_the_free_crop` |
| F10 | High | Maintenance introduces an unrestricted cold-check crop path | fixed | `ee3cae019` | `src/screens/MaintenanceScreen.transcription.test.tsx`: "the reported item's print comes from its own view, and hides during a check on your own", "a reported item under a check on your own shows no print on the card" |
| F11 | Medium | Open in Reader uses the initial location after viewer navigation | fixed | `ee3cae019` | `src/components/AsPrinted.test.tsx`: "after next in the original page, the Reader opens the passage shown now"; `src/screens/workbench/asPrinted.test.tsx`: "after prev in the original page, the Reader opens the passage shown now" |

**F9.** `author_exercises` records where each part of the selection sits in the joined
exercise text. When the model splits one selection into several exercises, each item gets its
own copy of the selection's source refs. Every block stays a ref, because the provenance is
still the selection's, and each ref now carries `owned`: whether that block's part overlaps
the item's anchored statement. `printed_origin` crops only the owned blocks. Ownership is
unknown in two cases: a selection-level `editedText` replaced the text, so no part maps to a
block, or the split was written before `owned` existed. A split from before `owned` is
recognised by another item's `source_exercise_imports` row from the same Reader write (same
extraction, `created_at` and span list). In both cases `span_ids` is empty and no crop is
free. The original page (one hint before Submit) is still offered, located by every block of
the selection (`PrintedOrigin.page_span_ids`), with the existing `NO_CROP` notice. A check on
your own shows nothing. A single-item import is unchanged: the whole selection is its print,
as the F4 test pins.

**F10.** The Maintenance transcription card now reads the reported item's own view
(`useAsPrinted` → `practice.as_printed`) and renders it with `AsPrinted`. The server's cold
rule and figure-only rule therefore apply, and so does F9's ownership. The block form
(`reader.block_original_region`), which knows no item, is no longer called from there. A new
`report={false}` prop drops the second "doesn't match the page" link on that card.

**F11.** `OpenInSource`'s `onOpenInReader` callback is now given the passage on screen
(`currentSpanId`, and the extraction of the view showing it). `PrintedAfterFeedback` merges
it into its target, so `printedPageInReader` anchors at the displayed span. The workbench
peeks at the displayed span. The two other hosts that render `OpenInSource` don't pass the
callback.

No migration, no new config key or parameter, no new top-level module, nothing under
`src-tauri`.

### Re-review gate

Every pytest, vitest and npm command ran in `systemd-run --user --scope --quiet -p
MemoryMax=5G -p MemorySwapMax=1G`, one at a time. pytest ran with `-n 6` and vitest with
`--maxWorkers=4`. No live calls: every model-backed path in these tests uses fakes.

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (16 files): **930 passed**. Files: tests/test_reader_ca1_as_printed.py
  tests/test_reader_ca1_codex_review.py tests/test_exercise_authoring.py
  tests/test_import_split_parity.py tests/test_library_exercises.py
  tests/test_required_method_authority.py tests/test_required_method_items.py
  tests/test_source_exercise_rpcs.py tests/test_source_exercise_import.py
  tests/test_facet_locks_landing.py tests/test_codex_output_schema.py
  tests/test_structured_transport_parity.py tests/test_maintenance_feed.py
  tests/test_desktop_rpc_contract.py tests/test_mobile_allowlist.py tests/test_architecture.py.
- Contract pytest (4 files): **100 passed, 5 skipped**. Files:
  tests/test_sidecar_serializer_snapshot.py tests/test_sidecar_contract.py
  tests/test_public_tip_guards.py tests/test_tracked_fixture_databases.py.
- `npm install`: ok. `npm run typecheck`: exit 0. `npm run frontend:build`: built.
- vitest set 1 (21 files): **187 passed**. Files: src/components/AsPrinted.test.tsx
  src/screens/MaintenanceScreen.transcription.test.tsx src/screens/workbench/ (all 9)
  src/screens/PracticeScreen.asPrinted.test.tsx src/screens/PracticeScreen.workbench.test.tsx
  src/screens/RepairScreen.phase4.test.tsx src/screens/RepairOverFeedback.phase4.test.tsx
  src/components/AskOverlay.test.tsx src/components/AskOverlay.reader.test.tsx
  src/components/AskOverlay.capture.test.tsx src/components/AskOverlay.suggestion.test.tsx
  src/screens/reader/readerWorkbenchExercise.test.tsx.
- vitest set 2 (7 files, `src/screens/FeedbackScreen*` and `src/screens/feedback/`):
  **112 passed**.
- `git diff --check`: clean. No `src-tauri` change, so no cargo check. No migration, DB or
  connection change, so no durability tests and no DB reference regeneration.
