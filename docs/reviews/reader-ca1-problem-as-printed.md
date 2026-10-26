# Reader CA1: the problem as printed (stage `reader-ca1-problem-as-printed`)

Branch `reader/ca1-problem-as-printed` (worktree `learnanything-dl2`), base `main`
at `0db8291c1` (migration head 220, latest algorithm mvp-0.31). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §8 (all), §9 X13 and X14 (the two
as-printed rows), §11 K15, §1 C10, §12.4, §13's CA1 row and kill switch, §15
Q10 and Q12 (owner decisions 2026-10-25). Behaviour rules it leans on: the
workbench spec's §5.4 (the source visible = one hint-equivalent; "Original
page" behaves like any other source opening during practice) and D46/G61
(DL2: nothing that locates a check on your own until feedback).

**No migration, no successor, no model call, no exposure semantics changed.**

> Codex review fixes (F1-F8): `docs/reviews/reader-ca1-problem-as-printed-codex-review.md`.
> Where this record and that one differ, that one holds: the crop join compares areas,
> not centres (F2); every cold administration hides the print (F1); the switch also turns
> off the multi-block form and every host (F3); selection imports and region sub-boxes
> have their print (F4, §5 item 3 done); the workbench and feedback open the page itself,
> with *open in the Reader ↗* (F6, §5 item 4 done except before Submit).

## 1. What was built

| Surface | Before Submit (not a check on your own) | During a check on your own | After feedback |
|---|---|---|---|
| Practice screen (answer box) | header `From Strang: Exercise 6.1.12 · p.297 · … · original page ↗ · counts as a hint`; `▸ as printed (Strang p.297)` under the stem | `From Strang` only (DL2); `▸ the figure, as printed` when the item was imported with a figure block, open from the start, figure only | — (the screen moves to feedback) |
| Work in Steps on the practice screen | `▸ as printed` under the stem (the practice card's); **no original page** (this screen has no book: UX §5.1 "hidden while the book is hidden") | as the practice screen | — |
| Reader workbench | `▸ as printed` under the stem (item view when bound, the multi-block crop of the session's anchors before binding); `original page ↗` in the header only while the book is shown, opening the page in the book pane (it never costs more than the book already does) | the item view applies the cold rule | — |
| Feedback (both layouts) | — | — | `Exercise 6.1.12 · Strang p.297 · original page ↗` (free, unlabelled) and `▸ as printed`; `▸ your photo` for a photo card |
| Compare methods (RW2c) | — | — | `▸ the solution as printed` under the book's solution, when it came from a page |
| Reader exercise candidates (RW4b) | `▸ as printed` beside `open in the book ↗` | — | — |
| Phone | nothing (D20; CA7 is the owner's) | nothing | nothing |

Backend (`src/learnloop/reader/as_printed.py`, `src/learnloop_sidecar/handlers/as_printed.py`):

- **`practice.as_printed`** `{practiceItemId, render?}`: the server decides what may show.
  It reads DL2's served check itself (`intent.checks.served_check`, `locators_hidden`), so
  a check on your own gets `kind: "figure"` (figure blocks only; each crop is
  `{index, image}`: no page, label, box or span id) or `kind: "none"`, whatever the
  client asks. An error reading the check fails closed (treated as cold). Without
  `render` the view is the header's locator and labels (no images, one cheap read on
  serve); `render: true` adds the crop PNGs.
- **The crop (C10)**: `crop_boxes` joins the problem's own blocks, in reading order,
  page by page, into the union of their boxes, and joins two consecutive blocks only
  while the union holds no other block's **centre**. A worked example, a solution or
  another exercise sitting between two of the problem's blocks therefore splits the
  crop rather than showing in it (so a page may give two crops). Structural rule, no
  padding, no tolerance constant. A block with no page or box crops nothing (listed in
  `skipped_span_ids`); a crop that cannot be made is `no_original`, **never** the
  whole page (unlike the single-block form's `page_fallback`).
- **`reader.block_original_region`** gains the multi-block form `{extractionId,
  spanIds}` (one of `spanId`/`spanIds`, validated); the single-block form is unchanged.
- **Page label**: the PDF's own page label (`/PageLabels`, pypdfium2
  `get_page_label`) when the file has one, else the page's one-based position in the
  file.
- **A variant is not the book's problem**: `relation = "variant_of"` shows nothing
  (the parent's print would be another problem, with its neighbours).
- **Your photo**: `capture.photo_for_practice_item` is the reverse lookup the spec asks
  for (§12.4) over `capture_routes.result_refs_json` (routes `make_card` /
  `photo_to_item`, `$.practice_item_id`; an image capture not purged, no deletion
  pending; the latest). No index: the capture inbox is small and the read is one
  query per serve of a non-canonical item. The UI shows it through the existing
  `get_capture_media` (resolved from the stored hash only). Hidden during a check on
  your own.
- **The transcription doesn't match the page** (`practice.report_transcription`
  `{practiceItemId, note?}`): a maintenance notice, type `transcription_mismatch`
  (aging `auto_resolution`, severity `action_needed`), one per item: each report adds
  the learner's text (trimmed, when any) and counts; a report on a dismissed/resolved
  notice opens it again; the feed's collector keeps it while the item's prompt hash is
  the one reported and resolves it once the wording changes (a reword, a re-import or
  the item gone). It records nothing else: no evidence, no retirement, no item change.
  Only for a verbatim import (`validation_error` otherwise).
- **Kill switch** `practice.as_printed.enabled` (default true): off, `practice.as_printed`
  answers `{enabled: false, kind: "none", reason: "disabled"}`, the report refuses
  (`disabled`) and every screen is as before (no control renders).

## 2. Q12: the original page before Submit, and why it is not a successor

The spec's stop rule: "if that changes an attempt's classification beyond existing
hints_used/reveal meaning, stop and treat it as a successor". It does not:

- Opening the original page before Submit sets the practice screen's **book
  component**, the one the answer box already sends for a book counted in steps
  (`bookCounted`), so the submit carries `hintsUsed = authored + 1` and
  `bookCounted: true`: exactly spec §5.4's "source visible → `hints_used` += 1",
  the existing meaning (assisted: FSRS-fed, certifying nothing). The server's
  `combine_held` already treats `client_book` as one component, so the page and a
  book counted in steps are one hint-equivalent, never two. Going into steps it is
  carried as `carriedBook` (the workbench's existing `source_shown_at`).
- It is timed (the first-hint marker is marked when it is the attempt's first help)
  and kept with the draft as `pageSeen` under the retry key (the `hintSeen`
  pattern: `save_practice_draft.page_seen`, `checkpoint_dto.pageSeen`, the App
  mirror), so a restart before Submit still counts it.
- The view records the exposure where it opens (`get_span_view`, context
  `provenance`, entity `practice_item`), as every source opening does. No new
  exposure context (the column's CHECK would need a migration), no new reveal kind.
- It is not offered where a hint would void or is barred: a diagnostic block, a
  cold follow-up (`cold_retry`, `certification_cold_probe`), a check on your own
  (D46), teach-back, and in steps on the practice screen. *As printed* (the
  problem's own blocks) stays free there: it shows only the stem the learner has.
- After Submit (feedback) it is free and unlabelled.

## 3. Tests (fakes only; the crop on a PDF made in the test, no book text committed)

`tests/test_reader_ca1_as_printed.py` (20): the split rule and its union; blocks with
no geometry; the crops cut from a real two-page PDF drawn with PIL hold only the
problem's own ink (no neighbour, no caption pixels) at the reader's scale; no
original → geometry kept, no image; the practice view's locator, original page and
outline spans, and no exposure written; the cold rule (figure only, no locator keys)
with a stub and with a real DL2 due check (`cold_now` over `make_intent_vault`); a
check with no figure shows nothing; an unreadable check fails closed; a variant
shows nothing; no print, no photo; the switch off; your photo (and its media), cold
and purged; the report (count, notes, reopen, resolve on reword, verbatim only);
the multi-block RPC and its one-form validation; the draft's `pageSeen` under its
retry key.

Vitest: `src/screens/PracticeScreen.asPrinted.test.tsx` (9: the header and the
original page counting once, both layouts, Esc staying in the page, the exposure
call, the draft flag and the submit's `hintsUsed: 1, bookCounted: true`; as printed
free; a restored `pageSeen`; the cold check's figure only, both layouts; no page on a
cold follow-up; the switch off; the page carried into steps as `carriedBook`, and no
page in steps); `src/components/AsPrinted.test.tsx` (7: pending then "the page image
isn't available", the remembered open state and zoom, the report with its text, your
photo with its date, the multi-block crop, after-feedback locator, nothing when the
server shows nothing or the call is absent); `src/app/practiceDraft.test.ts` (+1).

## 4. Gate (this step; the full suites run once, in the landing gate)

Every Python/CLI command under `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR` (no routes reachable, no live calls); every pytest/vitest/npm/cargo
command in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`. **No paid
calls were made** (none was needed: no model route is touched); no manual run on vault
copies.

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, set 1 (`-n 6`, 36 files: the new file, the contract tests, the
  modules changed): **772 passed, 10 skipped**.
- Targeted pytest, set 2 (`-n 6`, 64 files: every other test file that reads the
  changed modules, incl. every defaults-fingerprint/upgrade test): **1318 passed, 6 skipped**.
- `npm run typecheck`: clean. `npm run frontend:build`: built.
- vitest (`--maxWorkers=2`, 61 files): **555 passed**. A first run at
  `--maxWorkers=4` while the machine's load average was ~100 failed 8 timing-dependent
  tests (vault-switch debounce, polls) in 6 files; the same files pass alone, on the base
  frontend and at 2 workers under lower load (checked by running the base `src/` against
  the same files): flakes from load, not this change.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- No migration, no schema change: no durability lane, no DB reference regeneration.
- Defaults fingerprints: all 22 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed with
  `defaults_fingerprint_for_version` (the effective config gains `practice.as_printed.enabled`);
  expect them to be recomputed again at landing after other stages' keys.

pytest set 1: tests/test_reader_ca1_as_printed.py tests/test_cli_help_snapshot.py tests/test_compare_keep_switch_off.py tests/test_config_refactor.py tests/test_coordinated_migrations.py tests/test_desktop_rpc_contract.py tests/test_figures_switch_off.py tests/test_public_tip_guards.py tests/test_reader_rw3b_switch_off.py tests/test_reader_tutor_switch_off.py tests/test_roles_switch_off_legacy_parity.py tests/test_roles_switch_off.py tests/test_rw2c_switch_off.py tests/test_sidecar_serializer_snapshot.py tests/test_tracked_fixture_databases.py tests/test_mobile_allowlist.py tests/test_architecture.py tests/test_table_roles.py tests/test_registry_audit.py tests/test_maintenance_feed.py tests/test_capture_desktop.py tests/test_capture_domain.py tests/test_capture_originals_race.py tests/test_capture_route_recovery.py tests/test_reader_render_views.py tests/test_figure_region.py tests/test_marker_pdfium_worker.py tests/test_span_view.py tests/test_sidecar_span_view.py tests/test_ad1_attempt_columns.py tests/test_ad1_fix_round5.py tests/test_stuck_prompt.py tests/test_hint_service.py tests/test_router_offer_log.py tests/test_router_r2a_serving.py tests/test_sidecar_contract.py

pytest set 2: tests/test_ad1_codex_review_fixes.py tests/test_ad1_reading_opportunities.py tests/test_ad23_owner_decisions.py tests/test_ad23_successor.py tests/test_coldness_receipt.py tests/test_constraint_engine.py tests/test_diagnosis_input_provenance.py tests/test_exam_protection.py tests/test_field_workbench_signals.py tests/test_glm_ocr.py tests/test_grading_cli.py tests/test_graph_edit_proposals.py tests/test_hint_telemetry.py tests/test_intent_codex_rereview.py tests/test_intent_orchestrator_rulings.py tests/test_kinship_feature.py tests/test_library_ask_review.py tests/test_library_exercises.py tests/test_method_explicit_upgrade.py tests/test_mobile_host_auth.py tests/test_mobile_host_coexistence.py tests/test_mobile_pairing.py tests/test_mvp010_upgrade.py tests/test_mvp011_upgrade.py tests/test_mvp013_upgrade.py tests/test_mvp014_upgrade.py tests/test_mvp015_upgrade.py tests/test_mvp016_upgrade.py tests/test_mvp017_upgrade.py tests/test_mvp018_upgrade.py tests/test_mvp020_upgrade.py tests/test_mvp021_upgrade.py tests/test_mvp022_upgrade.py tests/test_mvp023_upgrade.py tests/test_mvp024_upgrade.py tests/test_open_world_gate.py tests/test_p0_cutover_mvp08.py tests/test_placement_opening_probes.py tests/test_plan_determinism.py tests/test_prescription_passages.py tests/test_probe_pool_empty.py tests/test_reader_rw2b_review.py tests/test_reading_paths.py tests/test_reading_step_switch.py tests/test_recurrence_commands.py tests/test_regrade_contract_successor.py tests/test_regrade_contract_upgrade.py tests/test_retrieval_interventions_write_points.py tests/test_sensitivity_certificates.py tests/test_serve_eligibility_review.py tests/test_sidecar_append.py tests/test_sidecar_item_authoring.py tests/test_sidecar_teach_back.py tests/test_source_ingestion_v2lite.py tests/test_source_outcome_analytics.py tests/test_source_roles.py tests/test_teacher_te0_review_fixes.py tests/test_tutor_delivery_fixes.py tests/test_ux_phase2_shell.py tests/test_ux_phase4_feedback.py tests/test_intent_checks.py tests/test_canonical_exercise_serialization.py tests/test_source_inventory.py tests/test_compare_methods.py

vitest: src/app/classicIsBase.test.ts src/app/practiceDraft.test.ts src/app/shellChrome.test.ts src/components/AsPrinted.test.tsx src/components/AskOverlay.capture.test.tsx src/components/AskOverlay.reader.test.tsx src/components/AskOverlay.suggestion.test.tsx src/components/AskOverlay.test.tsx src/components/SourceOffers.test.tsx src/copy/denyList.phase4.test.tsx src/screens/FeedbackScreen.liveQueue.test.tsx src/screens/FeedbackScreen.phase4.test.tsx src/screens/FeedbackScreen.plan.test.tsx src/screens/FeedbackScreen.test.tsx src/screens/PracticeScreen.adaptiveDifficulty.test.tsx src/screens/PracticeScreen.adaptiveHandoff.test.tsx src/screens/PracticeScreen.adaptiveHints.test.tsx src/screens/PracticeScreen.adaptiveOff.test.tsx src/screens/PracticeScreen.asPrinted.test.tsx src/screens/PracticeScreen.firstHintRestore.test.tsx src/screens/PracticeScreen.hintTelemetry.test.tsx src/screens/PracticeScreen.intentCheck.test.tsx src/screens/PracticeScreen.phase4.test.tsx src/screens/PracticeScreen.test.tsx src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.branches.test.tsx src/screens/ReaderScreen.checkOffer.test.tsx src/screens/ReaderScreen.cuesSwitchOff.test.tsx src/screens/ReaderScreen.discoveredCues.test.tsx src/screens/ReaderScreen.discoveredCuesReview.test.tsx src/screens/ReaderScreen.doseOffer.test.tsx src/screens/ReaderScreen.followsLearner.test.tsx src/screens/ReaderScreen.guide.test.tsx src/screens/ReaderScreen.inquiry.test.tsx src/screens/ReaderScreen.inquiryOff.test.tsx src/screens/ReaderScreen.k7.test.tsx src/screens/ReaderScreen.marginMarks.test.tsx src/screens/ReaderScreen.marginMarksReview.test.tsx src/screens/ReaderScreen.parity.test.tsx src/screens/ReaderScreen.pdfSelection.test.tsx src/screens/ReaderScreen.preparing.test.tsx src/screens/ReaderScreen.quickcheck.test.tsx src/screens/ReaderScreen.recap.test.tsx src/screens/ReaderScreen.recapReview.test.tsx src/screens/ReaderScreen.review.test.tsx src/screens/ReaderScreen.rw2cExample.test.tsx src/screens/ReaderScreen.workbench.test.tsx src/screens/RepairOverFeedback.phase4.test.tsx src/screens/RepairScreen.phase4.test.tsx src/screens/feedback/CompareMethods.test.tsx src/screens/reader/exerciseCandidates.test.ts src/screens/reader/libraryExercises.test.tsx src/screens/reader/libraryExercisesReader.test.tsx src/screens/reader/tutorExercises.test.tsx src/screens/workbench/HelpLadder.test.tsx src/screens/workbench/RouteExample.test.tsx src/screens/workbench/Workbench.test.tsx src/screens/workbench/reviewFixes.test.tsx src/screens/workbench/rw2cFixRound2.test.tsx src/screens/workbench/switchOff.test.tsx src/screens/workbench/symbolicOff.test.tsx

## 5. Open questions / follow-ups

1. **"this question is wrong" does not exist in the code.** The spec says the existing
   practice `⋯` *this question is wrong* gains a first option; neither the card's
   controls nor any RPC has it. CA1 puts *the transcription doesn't match the page*
   under the crop (wireframe X13's line) and records it as a maintenance notice. If
   the owner wants it in `⋯` too, it is one more entry point to the same RPC.
2. **Page labels.** A PDF without `/PageLabels` shows the page's position in the file
   (`p.N`, one-based), which may differ from the printed number. No page-label data
   exists elsewhere.
3. **Region selections' sub-box** (§12.4, third bullet: a learner-drawn crop stored on
   the imported exercise) is not done: today's imports keep span ids only, so a
   region-selected exercise shows its whole blocks.
4. **"open in the Reader ↗" from the original page view** (§8.3) is not added;
   `OpenInSource` has no Reader-open callback today.
5. **The page's hint is counted by the client's book component** (with the draft
   flag), not re-derived on the server from the exposure row. The row is there to audit
   it; a server-side fold would be a change to the submit path's assistance count,
   which this stage avoided.
6. The image drop-in path is still only specced; *your photo* covers the capture-inbox
   card route.

## Landing onto main (2026-10-26)

The branch is `merge/ca1-onto-main` in `learnanything-merge2`, cut from `main` at `497169069`. At that point main held
`mvp-0.34` (rebuild equivalence, after the LP claim fixes' `mvp-0.33`), mobile PR-2, RW7b, C0a (migrations through
222, head fixture `fixtures/migration_head_222`), T1 and S0. Main was neither fast-forwarded nor pushed. **CA1 has no
migration and no successor; the latest algorithm stays `mvp-0.34`.**

### Commits and conflicts

- `c35ba8d9b`: the `--no-ff` merge of `reader/ca1-problem-as-printed` (`aef4ba12f`). Three files conflicted, each
  composed so that both sides survive:
  - `config/template.py` (22 hunks, the defaults snapshots): every entry keeps main's notes (RW7b, LP-min (a), C0a,
    rebuild equivalence) and gains CA1's `[practice.as_printed]` note. CA1 was built when `mvp-0.31` was the latest,
    so `mvp-0.31`, `mvp-0.32`, `mvp-0.33` and `mvp-0.34` got the note by hand (git had put CA1's `mvp-0.31` hunk on
    `mvp-0.34`). **All 25 fingerprints were recomputed** with `defaults_fingerprint_for_version` (the config `.pyc`
    cleared first). Every one moves only because the effective config gains `practice.as_printed.enabled`.
  - `FeedbackScreen.tsx` (3 hunks): LP's `ClaimCheckFeedback` import and both uses, then CA1's `PrintedAfterFeedback`.
  - `tests/test_mobile_allowlist.py`: the desktop-only list names both `CURRICULUM_C0A_RPCS` and `READER_CA1_RPCS`.
  - `schema.py`, `parameter_registry.py`, `repositories.py`, `context.py`, `handlers/practice.py`, `dto.ts`,
    `App.tsx`, `PracticeScreen.tsx` and `Workbench.tsx` merged cleanly.
- `510a3336b`: the references (below). Then this record.

Against main, the diff adds `src/learnloop/reader/as_printed.py`, `src/learnloop_sidecar/handlers/as_printed.py`, two
test files, five frontend files (`AsPrinted.tsx` and four test files), one generated reference note
(`Config - practice.md`) and the two review records. **It adds no database or binary file, and the root `.gitignore`
is unchanged.** `main` and `reader/ca1-problem-as-printed` are both ancestors of the tip.

### Interactions

- **The defaults-snapshot hashes and the field arms.** The arm version hashes in `field/predictors.py` and
  `field/success_head.py` read only `[mastery]` (with LP's inert key left out), and CA1's key is a new top-level
  `[practice]` section, so no arm hash moves. `test_eval_harness.py`, `test_success_head*.py` and the config tests
  pass as merged (465 passed in the first targeted run), and no pinned digest changed.
- **Rebuild equivalence (`mvp-0.34`).** CA1 touches no replay, projection or scheduling code. Its one write is a
  `maintenance_notices` row (`transcription_mismatch`), and that table is `WORKFLOW` in `table_roles.py`, so a
  rebuild neither replays nor drops it. Parity (a) below shows the shadow rebuild at **0/0/0** on both sides.
- **PR-2 content sync.** New imports write two extra keys on `provenance.source_refs` (`owned`, and `region` for a
  region selection). Existing items are not rewritten, so a sync of the owner's vaults sees no change (parity (a):
  every row identical after the primary load, which syncs). The transcription notice's collector resolves on a
  prompt-hash change, which is the same signal a synced reword gives.
- **C0a (source sets fail closed).** C0a's fail-closed rule guards what is *sent to a model*. CA1 makes no model
  call. Its crop shows only the item's own blocks. Its original page opens through `get_span_view`, the
  open-in-source path items already had (that handler applies no exam rule of its own). The multi-block
  `reader.block_original_region` form has the same reach as the single-block form it sits beside. So nothing in
  C0a needed composing. Whether the original page of an exam-role item should be offered is a question for the
  owner (open items).
- **LP claim fixes and RW7b.** CA1 reads no claim, mastery or plan. The plan, Today and certification are
  byte-identical between main and the merge (parity (a)).
- No break was found, so no fail-first test was needed.

### Regeneration

- `db_generate_reference.py` first refused the new section (`KeyError: 'practice'` in `CONFIG_SECTION_FUNCTIONS`). The
  script gained a `practice` description. The reference now holds **1,056 leaves in 73 sections**, with the new
  `Config - practice.md`. The prose counts in `Configuration.md` and `Database.md` were updated by hand.
  `db_validate_reference.py` reports **errors: []**. The other ~425 note changes are `source_commit` stamps.
- `validate_vault.py`: passed (1,159 notes).
- `module_validate.py` and `desktop_validate.py` still fail as they do on main: stale module notes (1,115 missing
  now against main's 1,111, the difference being CA1's new modules) and the unclassified `syntheticBook.ts`. That is
  left to the queued docs workflow.
- `tests/cli_help_snapshot.json`, the RPC contract and the serializer snapshot needed nothing; their tests pass as
  merged.

### Gate

Setup ran in 5G scopes: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`. The pytest lanes ran at
`510a3336b` under `flock /tmp/learnloop-fullsuite.lock` in 10G / 2G-swap scopes. Each ran with `env -i` and empty,
existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, which were still empty afterwards. Logs are in
`fixtures-local/landing-ca1/logs/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`pytest -n 8 -p no:cacheprovider --dist worksteal`, 1 h 38 min, load average 100-450 from other stages) | **21,710 passed, 15 failed**, 80 skipped, 41 xfailed (21,846 items). **10 are the installed Codex CLI 0.164.0** ("does not report feature realtime_conversation, worktrees off"): `test_codex_isolation_mcp_check` ×3, `test_codex_lockdown_round2` ×3, `test_codex_lockdown_round3` ×3 and `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled`. **The same 10 fail on main's tree** (`git archive main`, run alone: 10 failed, 85 passed, the same message). The other 5 are known load flakes, each **3/3 passed alone**: `test_plan_first_transport_offer_grants::test_p1_…`, `test_reading_hardening_2_fixes::test_f1_…` and `test_reading_request_sweep::test_b_…`/`test_d_…`/`test_e_…`. The worker that ran `test_reader_rw1c_review.py`'s 84 cases then held `test_reading_request_sweep.py`. It had ~800 leaked threads and was taking about 40 minutes per test. So it was killed (`SIGKILL`) during `test_e_…`, and xdist replaced it and ran the rest. `test_e_…` is one of the 5 rerun alone |
| an earlier, accidental full run at `c35ba8d9b` (`-n 6`, 5G scope; a targeted file list that the shell did not split) | 21,712 passed, the same 13 classes failed (10 Codex, `test_p1_…`, `test_f1_…`, `test_b_…`) |
| durability (`-m durability`) | **137 passed**, 1 skipped |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-ca1/`) | 83 passed, 6 failed. These are exactly the 6 known, pre-existing failures: `test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill` and `test_placement_fixture_copies[arxiv_v2]` |
| `npm install`; `npm run typecheck` (at `c35ba8d9b`; `510a3336b` changes only docs) | ok (esbuild's postinstall blocked, as before); clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **218 files, 1,873 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree | `git status` clean apart from `fixtures-local/` |

### Parity (backup-API copies of the mvp030 backups; no real model call)

**Setup** (`fixtures-local/landing-ca1/scripts/`: the rbeq landing's kit, re-pathed, plus `setup.sh`, `a34.sh`, `p34.sh`
and `ca1_probe.py`):
- `orig/` holds backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`.
- `u34/` is `orig` brought to **mvp-0.34 with main's code**: routes sent to a `127.0.0.1:9` blackhole (all 64
  tasks), `upgrade --to mvp-0.34` (mvp-0.30 → mvp-0.34), then `rebuild-derived-state` twice.
- `code_main` and `code_merge` are `git archive` exports of `497169069` and `510a3336b`.
- Every run went through `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. `run.py`'s audit hook
  refuses any Codex process start and any non-loopback socket.

**(a) Main vs merge at mvp-0.34** (`a34.sh`, with a second main copy as the noise control):
- **Whole databases** after the normal primary sidecar load: **every row of 357 tables is identical**: 18,806 rows
  on linear_algebra and 8,195 on probability. There are no schema diffs, `schema_migrations` is identical (head 222),
  integrity is ok, `foreign_key_check` is 0 and `model_call_receipts` is 0.
- **Certification, Today and the plan: byte-identical** main vs merge, and main vs main, on both vaults.
- **`rebuild --shadow`: 0/0/0** on both sides and both vaults, with live state unchanged.
- **`doctor`: identical**: 57 issues / 1 error on LA, and 101 / 48 on probability, which predate the stage.

**(b) CA1 used on every item changes no row** (`p34.sh`). Two copies of u34 had the merge's primary load. On one,
`practice.as_printed` then answered every practice item twice, as the header read and with `render: true`:
- linear_algebra: 99 items. 96 are `none` / `no_print` (generated or tutor items, with no print and no photo). 3 are
  `page` / `no_geometry`: their extraction keeps a page but no box, so no crop is made, and the original page is
  offered with its notice "the crop isn't available for this problem · the original page is".
- probability: 77 items, 69 `none` / `no_print` and 8 `page` / `no_geometry`.
- There were no errors and no crop images (none of these imports has block boxes).
- The two copies stay **row-identical** (357 tables, `model_call_receipts` 0). The view writes nothing: its exposure
  is recorded only where the page opens.

**Receipts and calls.** All 19 `state.sqlite` files under `fixtures-local/landing-ca1/` and
`fixtures-local/owner-lane-ca1/` have **0 `model_call_receipts`**. `run.py`'s audit log was never created, so no process
start and no socket connection happened. **Spend: $0.** Nothing under `~/learnloop-vaults` was opened or listed.

### Owner notes

- **No upgrade step.** CA1 has no migration and no successor, and vaults at `mvp-0.34` need nothing.
- On your current vaults, the *as printed* fold shows nothing for generated items. For the 3 (linear algebra) and 8
  (probability) imported exercises it offers the **original page** (one hint-equivalent before Submit, free after
  feedback) with "the crop isn't available for this problem". Those imports kept a page but no box, and they predate
  the `owned` mark. New Reader imports from a Marker/GLM extraction (block boxes) get the crop.
- **The kill switch** is `[practice.as_printed] enabled = false`. Every screen is then as before CA1, and the report
  refuses.

### Open items

- **Finding (Low, learner-visible): the header names "your book" for the owner's textbooks.** `_source_title` in
  `handlers/as_printed.py` reads only `source_artifacts.display_title`, which is NULL for both owner textbooks. On
  the copies the header reads "From your book · p.10" / "as printed (your book p.38)". The Reader and the source
  cards use `content.pipeline.add_source.learner_title` (the display title, else the file name in words). Switching
  to `learner_title` would name the book. It is not changed here: it is CA1's own behaviour, not a landing interaction.
- **Question (not a landing break):** `practice.as_printed` and `get_span_view` read no exam-material rule. For an
  item imported from an exam-role source, the original page would show that page's other problems. This is the
  open-in-source behaviour from before CA1, and CA1 now offers it before Submit too. If held-out pages must stay
  closed, `item_as_printed` could refuse the page when `exam_material.spans_withheld` names the item's spans.
- The exercise label is empty on those imports (`exerciseLabel: null`), so the header has no "Exercise N".
- `test_reader_rw1c_review.py` leaks about 9 threads per case, and they keep polling. When one worker gets both that
  file and `test_reading_request_sweep.py`, the sweep tests slow to about 40 minutes each. This is the second landing
  where it cost a full-suite run; fixing the test file's teardown would end it.
- Carried from the stage (§5): "this question is wrong" does not exist; page labels fall back to the file position;
  the page's hint is counted by the client's book component.
