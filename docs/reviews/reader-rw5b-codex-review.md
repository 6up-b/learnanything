# Reader workbench RW5b: review fixes (stage `reader-rw5b`)

Branch `reader/rw5b` (worktree `learnanything-dl2`), on the implement step's `a2cca3a9c`. The review ran read-only with
`codex=false` (Opus reviewer; Codex is out of quota until 2026-10-27). Stage notes: `reader-workbench-RW5b.md`.
**No migration, no successor, no new route, no new config key** (the registry and the defaults snapshots are unchanged).
No model was called: every test uses fakes, and nothing ran outside pytest/vitest except `lint-imports`.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | The tutor's "make this explorable" sends the interaction event as `offerRef`, so every real press is refused `not_offered` | fixed | `ff650510f` | `apps/.../figures/tutorOfferPress.test.tsx` (reader.ask's answer → press → `reader.figure_request` with `offerRef = eventId`; failed before, sending `readerAnswerEventId`); `advancedPanels.test.tsx` "no question event … no button"; server end to end `tests/test_figures_rw5b_review.py::test_a_reader_ask_answer_offers_and_its_press_builds_from_its_question_event` (the interaction event is refused, the question event builds) |
| F2 | Medium | The same block is built and paid for again per origin and per prompt version, and the duplicates show under the passage | fixed | `b11a992db` | `test_a_block_built_from_a_selection_is_reused_when_a_library_offer_names_it`, `test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys`, `test_a_figure_built_before_the_panels_came_on_is_reused_with_them_on` (each failed before); guards: `test_a_figure_that_cant_be_drawn_now_is_not_reused_across_the_switch`, `test_another_prompts_cant_draw_verdict_is_not_reused` |
| F3 | Medium | The explorable verdict never reaches `judgment_ledger`, and the offer trusts mutable JSON | fixed | `6d0527496` | `test_the_organizers_explorable_verdict_is_in_its_ledger_rows`, `test_with_offers_off_the_organizers_ledger_rationale_is_rw4as`, `test_a_library_note_edited_to_offer_without_its_ledger_yes_is_refused`, `test_a_tutor_view_naming_a_block_without_its_ledger_verdict_is_refused`, and the end-to-end test above (one `figure_explorable` row) |
| F4 | Low | Revising an RW5b figure while the panels are off pays two author calls and sends the hidden spec | fixed | `b11a992db` | `test_a_figure_using_a_switched_off_panel_is_not_revised` (refused `advanced_disabled`, no call; failed before) |
| F5 | Low | With the panels off, a chain whose newest version uses a new panel hides an earlier drawable version | fixed | `b11a992db` | `test_with_the_panels_off_a_chain_shows_its_newest_drawable_version` (failed before: "can't draw this yet") |
| F6 | Low | The library offer says "building it under the passage" when the press lapsed | fixed | `ff650510f` | `advancedPanels.test.tsx` "a library press that lapses goes back to its button …" and "… that builds keeps saying so" |
| F7 | Low | The tutor is not told which cited blocks are equations or figures | fixed | `6d0527496` | `test_the_tutor_context_marks_each_equation_and_figure_block` |
| C1 | claim | §1.5 "the tutor's outputs are RW1c's byte for byte" does not hold for Ask history | fixed | `6d0527496` | the end-to-end test reads `reader.ask_history`: no exchange's `tutor` carries `explorable` |
| C2 | claim | §3 "the tutor offer … builds with origin `tutor`" held only with a made-up id | fixed (F1) | `ff650510f` | the vitest harness now passes `exchangeId="ia_1" offerRef="qe_1"`; the screen-level test uses the real id chain |
| C3 | claim | §1.4 "Built figures … reused by input hash" held only within one origin and one prompt version | fixed (F2) | `b11a992db` | §1.4 of `reader-workbench-RW5b.md` corrected |

Nothing was rejected.

### What changed, finding by finding

- **F1.** `TutorOffers` takes `offerRef` (the exchange's `questionEventId`, i.e. `reader.ask`'s `eventId`, where
  `source_context.reader_tutor` is stored) and passes it on the press; `exchangeId` stays for the offer store and
  logging. Without a question event no `make_explorable` button renders. The server still reads only
  `question_events` (I did not add a resolver for interaction ids: one id chain, and the interaction id is now
  refused in a test).
- **F2.** `request_hash` names `REUSE_ORIGIN = "selection"` in place of the request's origin. RW5a's keys were all
  made under `selection`, so they are byte-identical; the row keeps its own `origin` (the report's `offered`
  counts builds, so a press that reuses a selection's figure adds no row). A build also reuses a **shown** figure
  of the same input under the other prompt version when it can be drawn now (RW5a figures with the panels on;
  panels-era figures that use none of the new kinds with them off). Another version's "can't draw this yet" is
  never reused (that prompt could not draw it; the panels may). The lock and generation logic are unchanged.
- **F3.** `ListwiseTask.ledger_fields` records further judgment fields in each ledger row's rationale; the
  organizer's two explorable twins record `explorable` (offers off, the rationale is RW4a's `text` + `pick_rank`,
  pinned). The Reader tutor appends one `judgment_ledger` row per judged block, task `figure_explorable`
  (`figure_admission.TUTOR_EXPLORABLE_TASK`; judge `llm`; left `question_event`, right `source_span`
  `extraction:span`; derived id `fxj_…`; best effort, logged on failure). `offered_spans` confirms a library note
  by its own ledger row (same block, same question, `explorable: yes`) and a tutor view's blocks by their rows; the
  organizer's notes take the yes from the ledger row on both the judged and the cached path. A new ledger task
  name: the spec's `judgment_ledger` task list does not name it yet (the landing's doc pass can add it next to `figure_verified`).
- **F4.** `check_request` refuses a revision whose base spec uses a panel kind that is switched off
  (`advanced_disabled`), whatever the base's verification (a failed attempt at a heat map included), before any
  job or call; `reader.figure_revise` goes through it.
- **F5.** `list_figures` picks the newest version that can still be drawn before one that would list as
  "can't draw this yet".
- **F6.** `makeExplorable` now resolves `true` once the build is requested and `false` when the press lapses
  (another book opened first, or the hit's book opened on another reading; a hit on another reading of the book
  already open lapses at once, since reopening it opens this reading). `LibraryAnswer`'s button goes back to the
  button with "not built: the book opened on another reading of this passage; select it there instead". I did not
  translate the hit's span to the opened reading: the judgment named the old reading's block, so the server would
  refuse the translated one `not_offered`, and translating judgments across readings is beyond this stage.
- **F7.** With an equation or figure among the delivered passages, the explorable context marks each such span
  `block: equation|figure` (from `offerable_blocks`, as the organizer marks its candidates). The prompt asks only
  about passages that carry `block`, noting that a figure's text may be only its caption. Off, or with nothing to
  judge, nothing is marked (RW1c's request, as pinned before).
- **C1.** `reader_dialogue.ask_history` never projects the tutor view's `explorable` (offers are this visit's
  only), so history is RW1c's whether figure offers are on or off. The live `reader.ask` response still carries it
  while on.

### Changed pins (this stage's keys only)

- `tests/test_figures_fix_round2.py::test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock`
  counted every `store.reusable` read. F2 adds one lookup per read under the other prompt version's key, so the
  test now counts this input's reads (`reads.count(reads[0]) == 2`). The property it pins, a reread inside the
  lock, is unchanged.
- `tests/test_figure_offers.py::_tutor_event` also records the tutor's verdicts in the ledger, as the answer path
  now does (`tutor_qa._record_explorable_verdicts`).

### Notes for the landing

- No window or document keydown listener was added (no `screenLeavesKey` guard needed).
- No config key, migration, route or RPC parameter changed. One new refusal code (`advanced_disabled`) and one new
  ledger task (`figure_explorable`).
- The user's report in this run: the window crashes that force the restarts. Nothing in these fixes bears on
  them. Every test command ran inside the 5G memory scope, one at a time.

## Gate (fix step; owner rule 2026-10-17: targeted only)

Run on `6d0527496` (this section's commit adds only the docs), with `TMPDIR=fixtures-local/tmp`. Every
pytest/npm/vitest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- …`,
pytest with `-n 6`, vitest with `--maxWorkers=4`, one test command at a time. The full-suite lock was free. No model
was called and no vault copy was run.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **30 kept, 0 broken** |
| targeted pytest, 80 files (list below) | **2,434 passed, 1 skipped** (the existing golden-writer skip in `test_figures_switch_off.py`), 249 s |
| `npm install`; `npm run typecheck` | ok, no errors |
| targeted vitest: `src/screens/reader` (all), `src/screens/ReaderScreen*`, `src/app/App.wrapUpSkim.test.tsx`, `src/screens/attentionBudget.test.tsx` | **80 files, 766 passed** |
| `npm run frontend:build` | ok (only the existing chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference generate/validate; durability lane | not run: no migration, no schema or connection change |
| defaults snapshots, CLI help, RPC pins | unchanged (run in the list: `test_config_refactor`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`) |

New tests: `tests/test_figures_rw5b_review.py` (13), `tutorOfferPress.test.tsx` (1), `advancedPanels.test.tsx` (+3).

Pytest files run (to check against the landing gate): `test_figure_grammar`, `test_figure_offers`, `test_figure_panels`,
`test_figure_predictions`, `test_figure_property`, `test_figure_region`, `test_figure_revisions`,
`test_figure_verification`, `test_figures_codex_review`, `test_figures_final_round`, `test_figures_fix_round2`..`5`,
`test_figures_migration`, `test_figures_rpc`, `test_figures_rw5b_review`, `test_figures_scope_redesign`,
`test_figures_switch_off`; library ask (`test_library_ask`, `test_library_ask_expand`, `test_library_ask_review`,
`test_library_asks_migration`); the Reader tutor (`test_reader_tutor_offers`, `test_reader_tutor_retrieval`,
`test_reader_tutor_switch_off`, `test_tutor_qa`, `test_tutor_citations`, `test_tutor_tool_requests`,
`test_tutor_delivery_fixes`, `test_source_retrieval_tutor`, `test_source_retrieval_search`, `test_reader_rw1c_review`);
Ask history (`test_reader_branches`, `test_reader_inquiry_status`, `test_reader_inquiry_kill_switch`, `test_sidecar_reader`);
the listwise users (`test_label_roles_cli`, `test_passage_links`, `test_source_retrieval_guards`,
`test_workbench_passage_draw`, `test_mcp_tools`, `test_mcp_c1a_review`, `test_codex_isolation_mcp_check`); the
organizer and roles (`test_roles_judges`, `test_roles_switch_off`, `test_rw4_kill_switches`, `test_source_roles`,
`test_reader_find_sources_callers`, `test_rw4d_rw3b_composition`, `test_compare_sources_keep`,
`test_compare_keep_switch_off`, `test_rw2c_switch_off`, `test_reading_paths`, `test_reading_step_switch`); the report
and sidecar (`test_reader_report`, `test_reader_cues_cli_report`, `test_sidecar_source_retrieval`,
`test_sidecar_registry`, `test_reader_intent`); exam protection and routes (`test_exam_protection`,
`test_exam_protection_review`, `test_judge_routes`, `test_codex_tool_lockdown`, `test_codex_lockdown_round2`,
`test_codex_lockdown_round3`, `test_codex_output_schema`, `test_ai_tool_isolation`,
`test_structured_transport_parity`); and the contract pins (`test_config_refactor`, `test_registry_audit`,
`test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`,
`test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`,
`test_sqlite_file_copies`).
