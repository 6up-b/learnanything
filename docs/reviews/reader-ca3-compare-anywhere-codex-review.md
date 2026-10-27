# Reader CA3: compare from anywhere — Codex review and fix round

Stage `reader-ca3-compare-anywhere`, branch `reader/ca3-compare-anywhere` (worktree
`learnanything-merge2`). Codex review of `1bcde2096..a33997aa4` (codex-job
`20261027-181031-WuQtZY`, gpt-6.1-sol). Each finding was reproduced first by a failing test
(pytest for F3/F4, vitest for the rest; the new vitest file failed 9 of 9 against the pre-fix
frontend, the new pytest Keep test failed against the pre-fix Keep), then fixed.

**No migration. No successor. No paid call was made** (every model in the tests is a fake;
nothing outside pytest called a route). No new weight, margin or threshold: the views' bound
is the existing `reader_compare` keep maximum (`keep.maxPerspectives`, RW4d's stored-size
`keep` guardrail), now enforced by asking instead of evicting.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Selection comparisons lose the active workbench's practice policy | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F1: the payload names the bound workbench session…", "F1: the selection verb while working runs nothing until the learner leaves the problem" |
| F2 | Medium | Removing the final book restores every book | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F2: removing the last book stops the comparison and keeps the picker…" |
| F3 | Medium | Pins can override the named-book restriction | fixed | `99b70a225` | `test_reader_ca3_codex_review.py::test_f3_a_pin_from_a_book_not_named_is_dropped_before_verification`, `::test_f3_the_anchor_stays_the_one_exception`, `::test_f3_without_named_books_a_pin_is_compared_as_today` |
| F4 | Medium | Multi-block anchors are represented as a single-block passage | fixed | `99b70a225`, `fa78dbb0c` | `test_reader_ca3_codex_review.py::test_f4_the_stored_entry_and_cache_identity_name_every_anchor_block`, `::test_f4_a_one_block_anchor_is_stored_as_before`, `::test_f4_keep_rechecks_and_cites_a_quote_from_the_anchors_later_block`; vitest "F5: a comparison's tutor uses every block of an anchor of several blocks" |
| F5 | Medium | The library-answer door lacks the shared comparison controls | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F5: compare these books has refine, previous and the tutor over the compared passages, whatever is pinned" |
| F6 | Medium | Changing books leaves the previous tutor answer current | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F6: changing the books clears (and cancels) the tutor's answer…" |
| F7 | Medium | Failed or cancelled refinement makes the earlier table inaccessible | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F7: the earlier table stays reachable when its replacement fails or is cancelled" |
| F8 | Medium | A fifth perspective silently deletes the first | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F8: a view past the bound waits for the learner to remove one…" |
| F9 | Low | Corrections after refinement are attributed to the original reading | fixed | `fa78dbb0c` | `compareScopeCodexReview.test.tsx`: "F9: after a refinement, an × corrects the refinement's reading and change the ask box's" |

Rejected: none.

### What changed, per finding

- **F1.** `CompareRequest`/`CompareRequestDto`/`comparePayload` carry `workbenchSessionId`
  (one more key, the same for every door; the follow-ups from the chips and the refine box
  pass the request's own). The selection verb sends the bound session when one is active,
  and while a problem is open in the workbench it starts nothing: the comparing posture is
  hidden there, so nothing is paid for. A line in the workbench says *Your comparison opens
  beside the book. Leave for now (your steps are kept) and it starts.*
  (`ReaderWorkingPosture`'s `compareWaiting`, the pattern of the palette's Ask while
  working); on leaving, the comparison opens beside the book (same book only), under the
  policy then in force. The tutor's offer was already today's inline table while working.
- **F2.** An empty choice is no longer "every book": removing the last chip (or a
  refinement that removes every book) cancels the comparison, moves the shown table to
  *previous*, marks the chips `emptied`, says *no books chosen · add one to compare* and keeps
  the picker open. Adding a book re-runs the same row with that book. The server is
  unchanged: an absent `sourceIds` keeps meaning discovery, and the client never sends an
  empty one for a learner's empty choice.
- **F3.** In `compare_sources`, with `source_ids`, a pin whose book is neither named nor the
  anchor's is dropped (`dropped_pins`, *its book is not among the books you chose*) before
  any verification candidate is built; the anchor stays the one exception. Without named
  books, pins are as before.
- **F4.** The anchor's blocks travel with it: the stored source entry has `span_ids` (every
  block, its first naming it; absent for a one-block anchor, so those rows are unchanged);
  `counterpart_keys` (the cache identity, and what `comparison_passages` reads for the
  whole-comparison withholding) lists the later blocks after the anchor's key, so `[A1,A2]`
  and `[A1,A3]` are two comparisons. Keep rechecks each quote against the block of the
  passage that holds it and cites that block (`kept_comparisons._entry_keys`, `_holder`);
  its learning objects come from every block. The table row carries `span_keys`, and the
  tutor about the comparison grounds on every block.
- **F5.** `CompareScopeBody` holds every door's comparison controls (routed line, table,
  keep, refine, previous, the tutor about the comparison shown). `CompareScopeView` (doors
  with no library answer) and the library answer's *compare these books ▸* both render it;
  pins keep RW4a/RW4d's table, whose tutor is the pinned tutor (the pins are what was
  compared). `askTutor(question, "comparison")` grounds on the displayed comparison's
  passages, whatever is pinned; the pinned tutor names `"pins"`.
- **F6.** The tutor's answer records its basis. Re-running a comparison (chips, refine,
  retry, an emptied choice) cancels a pending tutor job about the comparison and clears its
  answer; a late answer never lands (the stage epoch drops it). A pins answer is untouched.
- **F7.** *previous ▸* renders outside the replacement's `ModelActionState`, whenever an
  earlier table exists: while the replacement is pending, after it failed, and after it was
  cancelled (which now also shows *cancelled · compare again ↵*).
- **F8.** At `keep.maxPerspectives`, a new view is not added and nothing is evicted: the
  refine box shows *four views is the most a comparison keeps · remove one to add this*
  (§5.4's words) with one *× view* button per kept view and *keep these*; choosing one
  removes it and adds the waiting view in one re-run.
- **F9.** The chips keep two readings: `judgmentId` (the reading that set the books shown:
  the ask box's, then a refinement's) is what `×` and *+ add a book* correct;
  `askJudgmentId` (the ask box's) is what *change* (rewording) corrects.

## Gate (this step; the full suite runs once at the landing)

All commands inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n 6` over the 91 files below: **2005 passed, 10 skipped, 3 xfailed, 1 failed**; the one failure is the known load flake  (named in the launch notes), which **passed** rerun alone (1 passed).
- Frontend (`apps/learnloop-tauri`): `npm install`: done; `npm run typecheck`:
  **clean**; `npx vitest run --maxWorkers=4 src/screens/reader src/screens/ReaderScreen`:
  **88 files, 823 passed**; `npx vitest run --maxWorkers=4 src/app/classicIsBase.test.ts`
  (imports the touched modules): **1 file, 9 passed**; `npm run frontend:build`: **built**.
- Nothing under `src-tauri` changed: no cargo check. No schema change: no DB reference run.
  No migration or connection code: no durability lane.

Pytest files run (new: `tests/test_reader_ca3_codex_review.py`; the stage's 83 files plus
every file that exercises `source_retrieval.compare`, `kept_comparisons`, `library_ask`'s
`compare_table`/`compare`, or `comparison_passages`):

```
tests/test_ad1_migration.py tests/test_ad23_successor.py tests/test_ad23_t1_routes.py
tests/test_architecture.py tests/test_attempt_content_state_successor.py tests/test_batch3_landing.py
tests/test_cli_help_snapshot.py tests/test_compare_keep_switch_off.py tests/test_compare_sources_keep.py
tests/test_compare_sources.py tests/test_config_refactor.py tests/test_coordinated_migrations.py
tests/test_decider_client.py tests/test_decider_landing.py tests/test_desktop_rpc_contract.py
tests/test_e0_review_round2.py tests/test_facet_identity_composition.py tests/test_figure_offers.py
tests/test_figure_predictions.py tests/test_figure_region.py tests/test_figure_revisions.py
tests/test_figures_migration.py tests/test_figures_rpc.py tests/test_figures_rw5b_fix_round2.py
tests/test_figures_rw5b_review.py tests/test_figures_scope_redesign.py
tests/test_figures_show_me_codex_review.py tests/test_figures_show_me.py tests/test_figures_switch_off.py
tests/test_find_sources_intents.py tests/test_help_assists_schema.py tests/test_hint_service.py
tests/test_intent_codex_rereview.py tests/test_judge_routes.py tests/test_learner_report_superseded.py
tests/test_library_ask_expand.py tests/test_library_ask.py tests/test_library_ask_review.py
tests/test_library_asks_migration.py tests/test_library_exercises.py tests/test_lp_claim_fixes.py
tests/test_mobile_allowlist.py tests/test_output_budget.py tests/test_passage_links.py
tests/test_plan_first_transport_offer_grants.py tests/test_plan_first_transport_offer_grants_r5.py
tests/test_plan_first_transport_paid_roles.py tests/test_plan_first_transport.py
tests/test_practice_proposal_caller_columns.py tests/test_probability_prep.py
tests/test_reader_ca1_as_printed.py tests/test_reader_ca2_one_ask.py tests/test_reader_ca3_codex_review.py
tests/test_reader_ca3_compare_anywhere.py tests/test_reader_compare_table.py tests/test_reader_dialogue.py
tests/test_reader_find_sources_callers.py tests/test_reader_inquiry_kill_switch.py
tests/test_reader_intentions.py tests/test_reader_intent.py tests/test_reader_reconstruct.py
tests/test_reader_rw1b_final_verify.py tests/test_reader_rw1b_fix_round4.py
tests/test_reader_rw1b_rereview.py tests/test_reader_rw1b_review.py tests/test_reader_rw1c_review.py
tests/test_reader_tutor_offers.py tests/test_reader_tutor_retrieval.py tests/test_reader_tutor_switch_off.py
tests/test_reading_paths.py tests/test_rebuild_equivalence_review.py tests/test_registry_audit.py
tests/test_retrieval_interventions_write_points.py tests/test_roles_judges.py tests/test_roles_switch_off.py
tests/test_router_r2b_requests.py tests/test_router_r2b_serving.py tests/test_rw4d_rw3b_composition.py
tests/test_rw4_kill_switches.py tests/test_sidecar_reader.py tests/test_sidecar_serializer_snapshot.py
tests/test_source_service_spend_envelopes.py tests/test_sources_merge_composition.py
tests/test_source_space_resolver.py tests/test_table_roles.py tests/test_teacher_te0_review_fixes.py
tests/test_tool_registry.py tests/test_tool_results_withhold_answers.py tests/test_tools_cli.py
tests/test_tracked_fixture_databases.py tests/test_tutor_tool_requests.py
```

Vitest files: new `src/screens/reader/compareScopeCodexReview.test.tsx` (9 tests); the run
covered every file under `src/screens/reader` and `src/screens/ReaderScreen*.test.tsx`
(including `compareScope.test.tsx`, `paletteAskPostures.test.tsx` and the
`ReaderWorkingPosture` tests).

## For the landing

- CA5a runs beside this stage: besides `ReaderScreen.tsx` and `LibraryAnswer.tsx`, this
  round touched `CompareScope.tsx` (split into `CompareScopeView` + `CompareScopeBody`),
  `useLibraryAsk.ts` and `ReaderWorkingPosture.tsx` (one optional prop).
- The owner question of the stage review (the ask box with the Decider unavailable) is
  unchanged.
