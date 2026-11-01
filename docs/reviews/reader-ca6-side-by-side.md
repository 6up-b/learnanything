# Reader CA6: side by side

Stage `reader-ca6-side-by-side`, branch `reader/ca6-side-by-side` (base `3a96d90b4`).
Spec: `docs/specs/ux_reader_compare_ask_v1.md` §6.4, §6.5 (Records), X9, K14, C5, §13 (kill switch), §15 Q14
(follow along on by default). Data: curriculum C0a's `reader.correspondents`; entry from CA5a's find-section list.

## What ships

- **Entry, three ways** (all behind `reader.side_by_side.enabled`):
  - `s` on a focused line of CA5a's find-section list, or the line's new *side by side* button
    (`FindSection` prop `onSideBySide`; CA5's judged list can pass the same hook later);
  - *read side by side (s)* in the peek's header;
  - `Ctrl+\` from reading: `reader.correspondents` (with the search fallback, since the learner pressed) for the
    Guide section in view, then the first correspondent in the API's order. Judged coverage comes first. With
    nothing judged, it opens the first unchecked hit, and the pane says *found by search, not checked*. With
    nothing at all, one dim line under the header reads *nothing in your other books matches this section
    yet*. It goes on the next click in the book.
- **A variant of the comparing posture, with a crumb.** Opening pushes a return-stack entry of the new kind
  `side_by_side`, so the strip reads `↩ <origin> › side by side with Axler §5.A`. Walking off it (a crumb press,
  `Alt+←`, opening another book) closes the second pane. Walking back onto it with `Alt+→` reopens it without
  pushing a new crumb. Closing with `Esc`, `Ctrl+\` or `✕` takes the crumb off the stack (`returnStack.dropCurrent`)
  and moves nothing: the first pane keeps its position and returns to full width.
- **Layout** (`SideBySidePane.tsx`): two source panes. The main pane gets a sticky header
  (*§ Strang · 6.2 …*, plus *lead* when it leads and the dim stays-put line). The second pane's header has
  *§ Axler · 5.C …*, *lead*, *follow along ● (^⇧L)* and *✕*. The split is resizable (a separator,
  pointer drag) and remembered per device (`localStorage`, clamped to 25–75 %, a layout bound). The rail
  folds to its 28 px gutter, and `\` (or the gutter) reopens it as an overlay at the right. A comparison
  started while side by side is open takes the right side. Side by side comes back when it closes, since both
  are the comparing posture.
- **The second pane** reads one section of the other book at a time through the new
  `reader.side_by_side_section`. That returns the whole section from its jump locator. Protection is read now:
  an exam, held-out or non-teaching reading, or a section with any withheld span, is refused, and the pane
  never runs on into the next unit. The response also names the reading's neighbouring readable sections,
  with protected ones skipped, as *‹ previous · next ›*. **Each block returned gets one `source_exposure` row**
  (context `library`, `span_view.record_span_exposures`, as CA5a's peek), recorded before the text is
  returned. No model call.
- **Follow along** (`useSideBySide.ts`; on by default, and the toggle turns it off for the session):
  - the leader is the pane the learner last scrolled (wheel, touch, scroll keys), clicked or selected in;
    F6 alone does not change it;
  - the follower moves **only when the leader crosses into a new section**. For the main pane that is the
    Guide section in view changing. For the second pane it is the learner moving it to another section.
    On a crossing, the follower moves once, to the first of its book's **judged** correspondents in the API's
    order (`reader.correspondents` with `search_fallback: false`; an unchecked search hit never moves a pane),
    at its jump locator. The main pane gets the jump and is then put at the passage instantly (no
    animation). The second pane loads the section at its top;
  - mid-section the leader moves nothing. A follow-along answer is dropped if, while it was in flight, the
    learner touched the follower, the leader crossed again, the pair changed or follow along went off
    (crossing and opening generations);
  - with no correspondent in the follower's book, the follower stays put and its header reads
    *no matching section here · stays put* (dim) until the learner moves it.
- **F6** moves focus between the panes. **Ctrl+Shift+L** toggles follow along. **Esc** aimed at either pane
  (never a field, never while a selection or the tag menu is open, never an Esc another handler took) closes
  the second pane. All of them are window keys under `screenLeavesKey`, outside text fields, and only while
  the switch is on. Ctrl+Shift+L does not clash: the command palette's Ctrl+L is element-scoped inside the
  modal palette.
- **CA3's selection verb in side by side:** in the main pane, *how do my other books treat this?* sends
  `sourceIds: [<the second pane's book>]`. A selection in the second pane shows the verb under the pane
  (*how do my other books treat this?* · *Strang*). It runs CA3's selection door anchored there (that book's
  reading and spans, `openSourceId` that book) with `sourceIds: [<the main pane's book>]`. Both require CA3's
  `compareScope`.
- **Narrow windows** (below 1,040 px; `SIDE_BY_SIDE_MIN_WIDTH`, the spec's layout bound): `s`, Ctrl+\ and
  *read side by side* open the section as a peek sheet over the lower half of the book. It has one dim line,
  *side by side needs a wider window*, no crumb, no follow along, and is recorded as
  `corresponding_section_peeked`.
- **Never lists exam material:** what can be opened comes from `reader.correspondents` (which reads coverage
  only through the protection predicate), and the section read refuses protected sections on its own,
  read again at each call.
- **Records** (salience only, through `reader.log_activity`): `side_by_side_opened`, `follow_along_moved`, and
  CA5a's deferred `corresponding_section_peeked` (a list peek, or the narrow sheet) and
  `corresponding_section_opened` (go there). They join `CLIENT_ACTION_EVENTS`. `ACTIVITY_FIELDS` gains ids
  only: `section_id`, `target_source_id`, `target_extraction_id`, `target_section_id`, `by` (judged or search)
  and `leader`. The learner's words are never kept.
- **Kill switch** `reader.side_by_side.enabled` (new `[reader.side_by_side]`, default on). The prompt contract
  carries `side_by_side: {enabled: true}` only while this switch, `curriculum.enabled` and the Reader are on.
  It does not depend on CA5a's `reader.correspondence.enabled`, because Ctrl+\ works without the list. Off:
  no key, no button and no read are added, `reader.side_by_side_section` refuses
  (`side_by_side_disabled`), and the Reader is today's exactly.
- **Plumbing:** Tauri passthrough `reader_side_by_side_section` (desktop only; pinned off the mobile
  allowlist as `READER_CA6_RPCS`); DTO `SideBySideSectionDto`; client `readerSideBySideSection`; contract key
  `sideBySide`; `DetourKind` gains `side_by_side`; `useReaderInquiry` gains `pushSideBySide` / `dropDetour`.
- **Config:** schema `ReaderSideBySideConfig`; parameter registry rule (structural, operational: a boolean
  kill switch, no weight, margin or threshold); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry
  (mvp-0.9 … mvp-0.38, 29) recomputed with `defaults_fingerprint_for_version`, with one comment line each and
  the paragraph on mvp-0.9 (0 mismatches).

No migration, no successor, no model call.

## Deviations and open questions

1. **The second pane shows one section at a time** (with *‹ previous · next ›*), not the whole book. That
   way the exposure rows are exactly the text displayed, and protection is read for every section shown
   (exam units inside a teaching book are never displayed, since the section read refuses them). A crossing
   in the second pane is the learner moving it to another section. Scrolling inside it is mid-section.
2. **Ctrl+\ falls back to the first unchecked search hit** when nothing is judged for the section (labelled
   in the pane). The spec says "the first correspondent in the API's order", and the API returns search hits
   only on a pressed read. Following stays judged-only (CA6's row in §13). If the owner prefers Ctrl+\ to
   open judged correspondents only, it is one line (`firstCorrespondent`).
3. **No ✕ on the main pane's header.** Closing is the second pane's ✕, Esc or Ctrl+\. A ✕ on the first pane
   would mean swapping the books, which the spec doesn't describe.
4. **Intent box, margin marks, notes and highlights in the second pane are not built.** The spec's
   "everything else works in both panes" lists them. CA6 builds the selection verb the stage brief names (CA3
   in side by side) as a one-line bar under the pane. The full intent box needs the Reader's capture and
   anchoring machinery per pane, which is a larger refactor of `ReaderScreen`. *After the Codex review (F1):*
   highlight and note in the second pane (saved to its own book) and its own margin marks are built. The
   intent box there is still open (see `reader-ca6-side-by-side-codex-review.md`).
5. **Records go through `reader.log_activity`**, so like every other Reader funnel event they are written only
   while `reader_inquiry` is on. The crumb also needs `reader_inquiry`: without it side by side opens with no
   crumb.
6. **The narrow-window peek pushes no crumb**, the same as CA5a's peek (CA5a deviation 2).
7. **A follow-along move of the main pane is a jump, not a detour**: it never pushes a crumb, and `Alt+←`
   returns to before side by side.

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`. Pytest ran with `-n 6`, under
`flock /tmp/learnloop-fullsuite.lock`; vitest ran with `--maxWorkers=4`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Targeted pytest, first run, 103 files: 7445 passed, 9 failed, 12 skipped, 3 xfailed** (38 min). The
  nine failures were the same five earlier stages' byte-for-byte contract pins that CA5a met, now seeing the
  new key `sideBySide`, which is on by default: `test_compare_keep_switch_off` (1), `test_figures_switch_off`
  (2), `test_reader_intent` (2), `test_reader_tutor_switch_off` (2), `test_reading_paths` (2). Each now
  registers the key the way they registered CA5a's: switched off, or popped with its value asserted.
  **Rerun of those five files plus `test_reader_ca6_side_by_side.py`: 104 passed.**
  The 103 files are the new `test_reader_ca6_side_by_side.py` (14), plus every test file naming the prompt
  contract, the default snapshots and fingerprints, the parameter registry, the activity vocabulary
  (`CLIENT_ACTION_EVENTS`, `ACTIVITY_FIELDS`, `record_activity`, `log_activity`), C0a's section coverage and
  correspondents, and the contract pins (`test_desktop_rpc_contract`, `test_cli_help_snapshot`,
  `test_architecture`, `test_table_roles`, `test_vault_template`, `test_sidecar_serializer_snapshot`,
  `test_mobile_allowlist`, `test_config_refactor`, `test_tracked_fixture_databases`,
  `test_coordinated_migrations`, `test_registry_audit`, `test_salience_firewall`). The full list: `test_ad1_codex_review_fixes.py`, `test_ad1_migration.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_approach_maps_schema.py`, `test_architecture.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_cli_help_snapshot.py`, `test_cold_retry_reschedule.py`, `test_compare_keep_switch_off.py`, `test_compare_sources_keep.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance.py`, `test_field_workbench_signals.py`, `test_figure_offers.py`, `test_figure_predictions.py`, `test_figure_region.py`, `test_figure_revisions.py`, `test_figures_rpc.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_grading_cli.py`, `test_help_assists_schema.py`, `test_intent_codex_rereview.py`, `test_kinship_feature.py`, `test_learner_claim_application_migration.py`, `test_learner_report_superseded.py`, `test_library_ask.py`, `test_library_ask_review.py`, `test_library_asks_migration.py`, `test_library_exercises.py`, `test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_plan_determinism.py`, `test_plan_follows_path.py`, `test_reader_activity.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca3_compare_anywhere.py`, `test_reader_ca3_landing_ca5a.py`, `test_reader_ca4_landing.py`, `test_reader_ca4_table_by_point.py`, `test_reader_ca5a_find_section.py`, `test_reader_ca6_side_by_side.py`, `test_reader_cues.py`, `test_reader_dialogue.py`, `test_reader_find_sources_callers.py`, `test_reader_inquiry_kill_switch.py`, `test_reader_intent.py`, `test_reader_reconstruct.py`, `test_reader_report.py`, `test_reader_rw2b_review.py`, `test_reader_rw3b_migration.py`, `test_reader_rw7a_migration.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_retrieval_spaces_migration.py`, `test_rw2c_switch_off.py`, `test_rw2d_receipts_migration.py`, `test_rw4_kill_switches.py`, `test_salience_firewall.py`, `test_section_coverage_migration.py`, `test_section_coverage.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_sidecar_reader.py`, `test_sidecar_serializer_snapshot.py`, `test_source_roles.py`, `test_t1_batch_origin_migration.py`, `test_table_roles.py`, `test_teacher_te0_review_fixes.py`, `test_tracked_fixture_databases.py`, `test_ux_phase2_shell.py`, `test_vault_template.py`.
- No migration and no DB/connection code changed, so no durability run was needed.
- **Frontend** (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean. Vitest on 39 files:
  **345 passed**. They were the new `useSideBySide.test.tsx` (13), `sideBySideReader.test.tsx` (11) and
  `findSectionSideBySide.test.tsx` (3); CA5a's `findSection`, `findSectionByPoint` and `findSectionReader`;
  `inquiryComponents`, `returnStack`, `readerHooks.parity`, `IntentBox`, `compareScope`,
  `compareScopeCodexReview`, `libraryAsk` and `libraryAskSwitchOff`; `app/keymap`, `app/classicIsBase` and
  `app/shellChrome`; and every `screens/ReaderScreen.*.test.tsx` (22 files). After that, `returnStack.test.ts`
  with the new `dropCurrent` case: 7 passed. `npm run frontend:build`: ok.
- **Mutation checks** (each reverted): dropping the leader check in follow along fails *the last-touched pane
  leads and is never moved* and *an answer that lands after the learner touched the follower is dropped*.
  Ignoring the contract key fails *switched off*. Dropping the other pane's book from the side pane's
  CA3 request fails the CA3 test.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok (one passthrough added).
- DB/config reference: `db_generate_reference.py` regenerated it (`Config - reader` gains the key; the
  catalog has 1074 effective leaves). The hand-written counts in `Configuration.md` and `Database.md` moved
  to 1074. `db_validate_reference.py`: **errors []**. `validate_vault.py`: passed (1163 notes). The
  regeneration also restamps `source_commit` in about 430 generated notes, as every stage's does. Take main's
  side at landing and regenerate.
- No paid or live call was made. The ad hoc Python (snapshot recomputation, reference scripts) ran under
  `env -i` with empty, existing HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR. No vault was opened, and no GUI was
  launched.

## Landing onto main

Landed in `learnanything-merge2` on `reader/ca6-side-by-side` (stage tip `49496362e`, base `3a96d90b4`). Main moved
twice during the landing, so there are three `--no-ff` merges and no rebase. No migration and no successor.

### Merges and conflicts

| Commit | What |
|---|---|
| `8a4f6ee5e` | Merge of main `2c3507003` (Reader CA5, RW5d P2 sketch tier, curriculum C0b migration 228). **Conflicts:** (1) `template.py`, every snapshot mvp-0.9 … mvp-0.38: CA6's note sits after C0b's, CA5's and RW5d's. All 29 fingerprints were recomputed with `defaults_fingerprint_for_version` after clearing the template `.pyc` (29 changed, then a recheck found 0). (2) `parameter_registry.py`: CA5's and C0b's rules plus CA6's. (3) `reader_inquiry.py`: **one** definition of `corresponding_section_peeked` / `corresponding_section_opened`, which CA5 and CA6 had both added. RW5d's `sketch_paused`/`sketch_error` and CA6's four session events sit beside them. In `ACTIVITY_FIELDS`, CA5's ids and RW5d's `error_kind` are joined by CA6's `leader`, `side_by_side_id` and `seconds_open`. (4) The `ReaderConfig` docstring. (5) `FindSection.tsx`: CA5's quiet read, `refreshKey`, `onPeekChange` and `closePeekToken` are kept beside CA6's `onSideBySide`. CA6's local `logHit` is dropped for CA5's `correspondenceEvents.ts`, which has the same payload keys. (6) `ReaderScreen.tsx`: the imports, and the reader-wide keys. With side by side open, `\` toggles the rail overlay and CA5's `x` opens the rail overlay (else uncollapses the rail). (7) `api/dto.ts` (CA5's `correspondence` fields and `CorrespondencePreferencesDto`, CA6's `sideBySide`, and the event union), `client.ts`, `commands.rs`, `main.rs`, `test_mobile_allowlist.py` (C0b's, CA5's and CA6's desktop-only RPCs) and the `test_reading_paths.py` contract pin. (8) 433 generated reference notes: main's copies were taken, then regenerated. `uv sync --extra dev --extra mobile` was rerun for RW5d's `wasmtime`. |
| `952a54d9d` | The interactions (i)-(iv) below. |
| `ec171598c` | DB/config reference regenerated: 1080 effective leaves (main's 1079 + `reader.side_by_side.enabled`). The prose counts in `Configuration.md` and `Database.md` moved to match. `db_validate_reference`: errors []. `validate_vault`: passes. |
| `1bcb185da` | Merge of main `90346980c` (Reader RW6b part 1: successor mvp-0.39, migration 227, `migration_head_228`). **Conflicts:** `template.py` only, every snapshot mvp-0.9 … mvp-0.38. RW6b's `[followups]` note is kept beside CA6's, and mvp-0.39 gains CA6's "is in it too" line. All 30 fingerprints were recomputed the house way (30 changed, then a recheck found 0). The migration pins came from main as merged (227 included). 436 reference notes: main's side taken, then regenerated. |
| `460f13280` | The RW6b interaction test (iii-b below). |
| `de921d605` | DB/config reference regenerated: 1085 leaves in 76 sections (main's 1084 + CA6's 1), prose counts moved. `db_validate_reference`: errors []. `validate_vault`: passes. |
| `28d2cd898` | Merge of main `e189ca7ae` (followups-oct31). **No conflicts.** Main changed `LibraryAnswer.tsx` and `useLibraryAsk.ts` (zero-hit comparison, pinned tutor), three vitest files, `test_codex_tool_lockdown.py`, the new `test_desktop_activation_audit.py`, the desktop catalog with `desktop_validate.py`'s counts, and review docs. |
| `e15f2de9d` | Desktop catalog regenerated with `desktop_generate.py`. `SideBySidePane.tsx`, `sideBySide.ts` and `useSideBySide.ts` are classified ACTIVE as entry-reachable: `ReaderScreen` imports them, and `src/main.tsx` reaches `ReaderScreen`. `desktop_validate.py`'s hard-coded counts moved to 293 TypeScript/TSX files, 285 entry-build and ACTIVE 298. `desktop_validate` passes byte-for-byte, and so does `validate_vault` (1360 notes). |

### Interactions

- **(i) AlsoInBooks' `onSideBySide` seam is wired.** `s` on a line of CA5's expanded "also in your books" list, and
  *side by side (s)* in its peek, open side by side with that section (`via: also_list`; `SideBySideVia` gains it),
  the same way as CA5a's find list. With side by side off, `s` does nothing there and the key bar doesn't offer it.
  Fail-first: before the wiring, the new vitest failed.
- **(ii) Peek crumb vs side by side crumb.** This was broken on the merge. Opening side by side from a peek (either
  list) left the peek open, so the detour strip showed both the stack's `side by side with …` and `› peek …`. Fix:
  `FindSection` and `AlsoInBooks` close their peek, without refocusing, before calling `onSideBySide`, so side by
  side's crumb replaces the peek's. Alt+← walks back to where the learner was (the pane closes, no peek comes back)
  and Alt+→ forward again. A peek is never a stack entry. Esc closes only what is shown: Esc in a peek opened in the
  rail overlay during side by side closes that peek and leaves the pane, and Esc in the pane then closes side by
  side. In a narrow window, side by side from a peek is the sheet and no crumb of either kind is left. All in
  `sideBySideCorrespondence.test.tsx`; the crumb case failed first.
- **(iii) Switch matrix.** `test_the_switch_matrix_each_switch_controls_only_its_own_key` covers all 8 cells of
  `reader.side_by_side.enabled` x `reader.correspondence.enabled` x `curriculum.enabled`. `sideBySide` is present
  iff its switch and curriculum are on, and `correspondence` iff its switch and curriculum are on. The two Reader
  switches move nothing else in the contract, and all off is the contract without either key (today). The
  frontend half is in vitest: correspondence off with side by side on (Ctrl+\ still opens it), CA5's line off with
  CA5a's find list on (`s` kept), and all off (no line, no action, no pane, no read).
  **(iii-b) RW6b:** `test_a_side_by_side_read_holds_a_follow_up_on_a_shown_span_and_only_there`. A follow-up whose
  item's canonical exercise is a block the second pane showed is held by RW6b's serve-time gate as
  `source_exposed`, citing the read's exposure ids. One on a block of a section that was not shown is not held.
  Mutation-checked: dropping the exposure write fails it.
- **(iv) One record per action.** The narrow window's sheet recorded its own `corresponding_section_peeked` payload.
  It now goes through CA5's `logCorrespondentAct`, extended with an optional extra payload (the visit's ids and the
  open book), so every record of the two events has the same keys. Vitest: peek → side by side records one
  `corresponding_section_peeked` (exactly CA5's eight keys), one `side_by_side_opened` and no `opened`. The sheet
  records one `corresponding_section_peeked` and no `side_by_side_opened`. Pytest:
  `test_one_definition_of_each_correspondence_event_and_field` (`CLIENT_ACTION_EVENTS` has no duplicates, and each
  of the two events appears once).

### Regeneration

DB/config reference: regenerated twice, as above (1085 leaves at the end). Desktop catalog: regenerated once
(above). CLI help and the RPC/serializer pins needed no change (`test_cli_help_snapshot`,
`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot` and `test_mobile_allowlist` pass).
`module_validate.py` reports 1265 missing module notes. That is the same on main (no stage regenerates the module
catalog), so it was left alone.

### Gate

Every pytest, vitest, npm and cargo command ran in a `systemd-run --user --scope` with MemoryMax 5G (the full suite
10G, under `flock /tmp/learnloop-fullsuite.lock`). Python outside pytest ran under `env -i` with empty, existing
HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR (`fixtures-local/landing-ca6/envrun.sh`).

| Run | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`; `lint-imports --no-cache` | ok; **36 kept, 0 broken** (after each merge) |
| pre-gate targeted, at `ec171598c` (42 files: contract pins, CA1-CA6, C0b, switch-off pins, CLI/RPC/mobile pins, public-tip guards) | 918 passed (2:02) |
| **full suite at `ec171598c`** (`-n 8 --dist worksteal`; lock wait 22:23 → 23:28) | **22,769 passed, 89 skipped, 47 xfailed, rc 0, wall 2,109 s (35:09)** |
| targeted after the RW6b merge, at `de921d605` (72 files: the above plus RW6b's `test_reader_followups*`/`test_reader_rw6b*`, every `test_mvp0*_upgrade`, migration/fixture/table-role/serializer/template/salience pins) | 6,752 passed (35:16) |
| **full suite at `de921d605`** (lock 01:09) | **22,901 passed, 89 skipped, 47 xfailed, rc 0, wall 2,108 s (35:08)** |
| durability (`-m durability`, `-n 6`) at `de921d605` | 177 passed, 1 skipped (0:57) |
| owner lane at `de921d605` (`-m owner_vaults`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-ca6/`) | 83 passed, **2 failed**, 4 skipped (0:52). The failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy. |
| after the followups-oct31 merge, at `e15f2de9d`: `test_desktop_activation_audit`, `test_codex_tool_lockdown`, `test_public_tip_guards` | 151 passed, 1 skipped |
| frontend at `ec171598c`: typecheck; whole vitest (`--maxWorkers=4`); `frontend:build`; `cargo check` | clean; 2,244 passed, **1 failed** = the known main flake *never draws a superseded frame…* in `SketchFigure.test.tsx` (failed alone 3/3 too; nothing under `figures/` differs from main); ok; ok |
| frontend at `de921d605` | clean; **242 files, 2,256 passed**; ok; ok |
| frontend at `e15f2de9d` (final code) | clean; **242 files, 2,261 passed**; ok; ok |

**Orchestrator ruling (recorded as given):** no further full pytest after the third merge (followups-oct31). The full
suite on the 90346980c merge was green, and that merge had no conflicts and touched only frontend, two Python test
files, the desktop catalog and review docs.

### Smoke on owner copies

Ran twice on fresh backup-API copies of the same three owner copies. The first run was at `ec171598c`, upgraded to
mvp-0.38 (`fixtures-local/smoke-ca6/`). The second was at `de921d605`, upgraded to mvp-0.39 (`smoke-ca6b/`); its
results were identical. Both used `env -i` with AI base URLs at `127.0.0.1:9`, `LEARNLOOP_COVERAGE_MODELS=off`, and
the sidecar under the audit-hook guard (no non-loopback socket, no process start: 0 guard log lines). Counts only.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `upgrade --to mvp-0.39` (+ `rebuild-derived-state`) | mvp-0.35 → mvp-0.39, rc 0 | same | same |
| contract `sideBySide` | `{enabled: true}` | same | same |
| two correspondents (CA5a search hits in another book; no judged coverage on the copies) | 2 found | 2 | 2 |
| `reader.side_by_side_section` blocks / all in that section / exposure rows / exposure ids | 222/yes/222/222; 145/yes/145/145 | 2/yes/2/2; 7/yes/7/7 | 193/yes/193/193; 423/yes/423/423 |
| a withheld section | refused `withheld`, 0 rows | same | same |
| switch off (`[reader.side_by_side] enabled = false`) | no contract key; refused `side_by_side_disabled`, 0 rows | same | same |
| `rebuild --shadow` before / after | 0/0/0 / 0/0/0 | same | same |
| model_call_receipts added | 0 | 0 | 0 |

None of the copies' readings is an exam reading, so the exam refusal is vacuous here.
`test_protected_sections_are_never_shown` covers it.

### Owner notes

- Kill switch: `reader.side_by_side.enabled` (default on). Side by side also needs `curriculum.enabled`: off, it is
  absent and the section read refuses. The records (`side_by_side_*`, `follow_along_*`, and the correspondence events)
  go through `reader.log_activity`, so they are written only while `reader_inquiry` is on. The crumb needs it too.
- `s` now opens side by side from both lists in the Guide: CA5a's find list and CA5's "also in your books".

### Open items

1. **CA6b:** the second pane's intent box and density cues (Codex review F1, the remaining part).
2. Ctrl+\ falls back to the first unchecked search hit when the section has no judged coverage (owner question;
   deviation 2).
3. No ✕ on the main pane (deviation 3).
4. One section at a time in the second pane (deviation 1).
