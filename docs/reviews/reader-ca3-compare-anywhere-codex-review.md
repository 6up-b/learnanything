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
- Targeted pytest, `uv run pytest -n 6` over the 91 files below: **2005 passed, 10 skipped, 3 xfailed, 1 failed**; the one failure is the known load flake
  `test_plan_first_transport_offer_grants.py::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter` (named in the launch notes), which **passed** rerun alone (1 passed).
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

## Re-review (codex-job 20261027-184553-TESPOx, VERDICT: REOPENED)

F1 (High) was confirmed fixed by the re-review. Two new findings were raised; both
reproduced (a failing test first) and are fixed.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F10 | Medium | Multi-block tutor requests exceed the RPC limit | fixed | aacf2a129 (backend), 98d14d422 (frontend + bound) | `tests/test_reader_ca3_codex_rereview.py` (5 tests); vitest `compareScopeCodexReview.test.tsx` "re-review F10", F5 tests updated |
| F11 | Low | Extracting shared controls breaks shortcuts on the comparison region | fixed | 98d14d422 | vitest `compareScopeCodexReview.test.tsx` "re-review F11" (2 tests; both failed against the pre-fix `CompareScope.tsx`) |

### F10: what changed

- Reproduced: a selection anchor of 22 blocks in a synthetic book plus one counterpart
  gives a comparison of 23 passages. The old hook expanded them into `pinnedSpanKeys`,
  and `LibraryAskTutorInput` refused them (`max_length=20`). The new frontend test,
  run against the old hook, still sent the expanded keys.
- `reader.library_ask_tutor` takes `comparisonId`, accepted only while
  `reader_compare.scope_enabled` is on. The server reads every passage the comparison
  compared from the stored `source_comparisons.counterpart_keys`, through the new
  `library_ask.comparison_passage_keys`: every book's passage and every block of the
  anchor, anchor first. So the request's size never limits a stored comparison. Naming
  a comparison that is not the one this ask shows is refused (`validation_error`). A
  request with no pins and no comparison is refused.
- Request bounds: pins keep 20. A comparison that was not stored (`too_few_sources`, so
  fewer than two books) shows at most its anchor's blocks, so it still sends its keys.
  The tutor's `pinned_span_keys` therefore takes `ANCHOR_SPANS_MAX = 40`, the same named
  bound as `anchor_span_ids` (a request-size guardrail, not a model parameter). While
  CA3 is off, the request is validated as today's exactly (`_PinnedTutorInput`: at
  least 1 pin, at most 20, no `comparisonId`).
- Context budget: `tutor_qa.context_token_budget` still decides what the tutor is given
  (unchanged, from the F7 round). Every passage is either grounded, possibly trimmed, or
  listed in `droppedPins` with its reason; the tests pin this at the schema's floor of
  1,000 tokens. The comparison's tutor answer now shows what was left out, counted by
  reason ("left out 2 passages: over the tutor's context budget").
- Frontend: `askTutor` about a comparison sends `{askId, comparisonId, pinnedSpanKeys: []}`
  when the shown table has a `comparisonId`. Otherwise it sends the rows' keys,
  including every anchor block, as before.

### F11: what changed

- Reproduced: focusing the `compare your books` region and pressing `/` or Ctrl+Enter did
  nothing. Both new tests failed against `CompareScope.tsx` at 12989ee8e.
- The controls' state and shortcuts are now one hook, `useCompareControls`.
  `CompareScopeView` calls it and puts `onKeyDown` on its focusable section
  (`tabIndex=-1`), then passes the controls down to `CompareScopeBody`. Where the body
  is used alone (a library answer's "compare these books"), the body's own div is
  focusable and carries the same handler: focusability and keyboard handling stay
  together in both hosts.

### Gate (re-review round)

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 <31 files>`:
  **684 passed** (the known load flake in `test_plan_first_transport_offer_grants.py` passed too). Files:
  tests/test_reader_ca3_codex_rereview.py tests/test_reader_ca3_codex_review.py
  tests/test_reader_ca3_compare_anywhere.py tests/test_library_ask.py tests/test_library_ask_review.py
  tests/test_library_ask_expand.py tests/test_reader_compare_table.py tests/test_rw4_kill_switches.py
  tests/test_mobile_allowlist.py tests/test_plan_first_transport_offer_grants.py tests/test_batch3_landing.py
  tests/test_capture_desktop.py tests/test_capture_route_recovery.py tests/test_field_signal_production_paths.py
  tests/test_learner_text_gaps_flow.py tests/test_reader_ca2_astra_handoff.py tests/test_reader_ca2_codex_rereview.py
  tests/test_reader_ca2_codex_review.py tests/test_reader_ca2_fix_orchestrator.py tests/test_reader_ca2_one_ask.py
  tests/test_reader_find_sources_callers.py tests/test_sidecar_source_retrieval.py tests/test_sidecar_tutor_qa.py
  tests/test_tutor_delivery_fixes.py tests/test_tutor_practice_request.py tests/test_tutor_tool_requests.py
  tests/test_compare_keep_switch_off.py tests/test_reader_tutor_switch_off.py tests/test_architecture.py
  tests/test_desktop_rpc_contract.py tests/test_sidecar_serializer_snapshot.py
- Frontend (apps/learnloop-tauri, each command in the 5G scope): `npm install` ok;
  `npm run typecheck` clean. `npx vitest run --maxWorkers=4` on 11 files gave
  **102 passed**: src/screens/reader/compareKeep.test.tsx, compareKeepSwitchOff.test.tsx,
  compareScope.test.tsx, compareScopeCodexReview.test.tsx (12),
  figures/advancedPanels.test.tsx, figures/libraryOfferSettle.test.tsx,
  libraryAsk.test.tsx, libraryAskJobs.test.tsx, libraryExercises.test.tsx,
  libraryExercisesReader.test.tsx, libraryRoles.test.tsx.
  `npm run frontend:build` built.
- Not run: no migration, schema, config or src-tauri change, so no durability lane, DB
  reference scripts or cargo check. Following the owner rule, the full suite was not
  run; it runs once in the landing gate.
- No live calls: every model in these tests is a fake, and no paid command ran.

### For the landing (addendum)

- This round touched `CompareScope.tsx` (new `useCompareControls`, the `controls` prop,
  the tutor's left-out line), `useLibraryAsk.ts` (`askTutor`, `SCOPE_COPY.tutorLeftOut`),
  `api/client.ts` (`readerLibraryAskTutor` input), and
  `src/learnloop_sidecar/handlers/library_ask.py` (`ANCHOR_SPANS_MAX`,
  `_PinnedTutorInput`, `comparisonId`). Expect the CA5a merge there.
