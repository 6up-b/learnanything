# Curriculum C2 (notes linked): Codex review fix step

**Review:** Codex (gpt-6.1-sol) of `2eb4bf6e61..fa762a6a2f`, job `20261101-090941-biskyH`: 12 findings (2 High, 10
Medium). **All 12 reproduced and fixed; none rejected.** Every finding testable on the server got a failing test first:
the 22 new backend tests were run against the original source (the five changed `src/` files checked out from
`fa762a6a2f`) and all 22 failed there; the server half of F4 already worked (its test passes on both), its defect was
the frontend's. The F10 Reader test fails on the original `ReaderScreen.tsx`. **No live or paid call**: fakes only (the
fake `tend` executable over synthetic notes, `NoteLinkFake`); the owner's `tend`, notes and vaults were never touched.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Tend failure bypasses its private-note restriction | fixed | `184d58b128` | The file fallback is gone: tend's `read` op is the only reader of note text (tend's `private` setting lives in tend's config, which LearnLoop cannot see, so no equivalent check exists). `tend serve` failing, stalling, answering unreadably or lacking the op raises `TendUnavailable`; linking waits. `test_f1_with_tends_read_down_no_file_is_read_and_linking_waits[no_read, serve_fail, serve_garbage, serve_slow]`, `test_f1_the_background_linking_waits_for_tends_read_and_sends_nothing` |
| F2 | High | Disabling notes does not stop a pending note-text request | fixed | `184d58b128` | `NotesGuard` (`note_links.py`): the notes authorization (`notes.enabled`, tend present, allowlist, Pocket Notes folders, `lexical_only` as the run started) read from the live vault at every request admission (request gate composed with C0a's `CoverageGuard`, and `PaidCalls`' attempt admission) and before every record (proposals, shown-state markers, refreshed snapshots); refusal is a `BaseException` no retry layer relabels. `test_f2_a_changed_notes_authorization_refuses_the_pending_request[notes off, lexical_only flip, allowlist shrunk]`, `test_f2_switching_notes_off_during_the_request_records_nothing` |
| F3 | Medium | Unlinked candidate notes are permanently stored in model receipts | fixed | `184d58b128` | `ai/execution.withhold_receipt_input()`: calls in its context keep `input_text` NULL; prompt/schema hashes, declared request identity (receipt recovery uses the prompt hash, not the text), usage and the verdicts (`output_text`) stay. The judge's call runs inside it. `test_f3_the_judges_receipts_keep_no_note_text` |
| F4 | Medium | Completed background links never reach the open UI | fixed | `b23e92d402` (server test `184d58b128`) | `usePathNotes` reads the path again every 3 s while `linking` is `running` and every 60 s while `waiting` (a waiting run is restarted only once its retry time has passed: Codex re-review F14); the transition to `done` calls the context's `onChanged`, so the margin marks and Compare's band read again. `NOTES_POLL_MS` is a UI cadence labelled `keep`. vitest "while the background linking runs the path is read again, and its end refreshes every surface (F4)", "a waiting linking is asked again later, quietly (F4)"; pytest `test_f4_background_linking_completes_and_the_next_read_shows_it` (real background job, not `notes_inline`) |
| F5 | Medium | Refresh removes Undo immediately after Hide | fixed | `b23e92d402` | The hidden links live in the notes context (`hidden`, `remember`, `forget`), outside the refreshed lists; `retainHidden`/`mergeMarks` keep a hidden card where it was, and the passage's `›` even when it was its last note, until *undo* (or another reading). vitest "a hidden note keeps its card and undo after the refresh its hide starts, even the passage's last note (F5)" (the server's second read omits the link), "retainHidden and mergeMarks keep only hidden cards a refresh dropped, where they were" |
| F6 | Medium | Undo freezes an obsolete snapshot and passage anchor | fixed | `184d58b128` | On a model proposal the learner's row is a decision only: `effective()` shows the topic's current proposal unless the learner's newest word is a hide; the historical copy is never shown. Hand-made passage links stay separate (shown with their note's newest snapshot). `test_f6_undo_shows_the_current_proposal_not_the_one_hidden`, `test_f6_a_kept_proposal_follows_the_topic_to_its_new_passage` |
| F7 | Medium | Returning to a cached state serves another state's links | fixed | `184d58b128` | Shown-state markers: `judgment_ledger` task `note_link_shown`, judge `exact_key`, per (goal, LO), appended when the current candidate state changes: newly judged, reused from the ledger (no repaid call), or no readable candidates (state `none`: nothing shows). `for_goal` shows its own goal's state; marks and Compare's band the states any goal's topic shows. No migration. `test_f7_returning_to_a_judged_state_shows_that_states_links_without_a_call` |
| F8 | Medium | Manual-link refresh can capture a different heading's text | fixed | `184d58b128` | The refresh first finds the heading again (`_resolve`: a words-only tend search by the note's title and heading, same file and heading path; `RESOLVE_K = 25`, a `keep` bound); not found, the link keeps its last snapshot. Every read also checks the hit's line (`line_is_hit`: a line opening another heading, normalized as tend does, drops the note). `test_f8_refresh_finds_the_heading_again_before_reading_it`, `test_f8_a_stale_line_that_opens_another_heading_is_never_read_as_the_note` |
| F9 | Medium | Background refresh resurrects a concurrently hidden link | fixed | `184d58b128` | Refreshing writes no link row at all (a hand link shows its note's newest snapshot), and inside the write transaction the learner's newest row for each identity is read again: refreshed only while the same accepted row stands. `test_f9_a_link_hidden_during_the_refresh_stays_hidden` |
| F10 | Medium | Library-page comparisons never receive the notes context | fixed | `b23e92d402` | `NotesContext.Provider` around the library page's ask pane, as RW4d's keep context. compareKeep.test "C2: the library page's comparison with no book open offers the notes' your-take band (F10)" (fails on the original `ReaderScreen.tsx`) |
| F11 | Medium | Failed "use as my take" actions show success and disable retry | fixed | `b23e92d402` | `onUse` returns `Promise<"kept" \| "drafted" \| "failed">`; the note is marked used only on `kept` (CompareKeep's `keep` and ComparePointTable's `send` now report success); a failure keeps the action (the parent shows why); `used` resets when the comparison's rows change. readerNotes.test "use as my take is marked used only once kept: a failure keeps the action, another comparison resets it (F11)" |
| F12 | Medium | Incomplete model output becomes invented, permanently cached verdicts | fixed | `184d58b128` | `verdict_problem`: exactly one verdict per candidate (none missing, none twice, no unknown id), `about` and `how` for each `discusses`; passed to `PaidCalls` as `validate` (via a new optional `ChatRoute.ask(validate=...)`), so an incomplete answer is retried, never checkpointed, and fails to `waiting` with no ledger or link write; a recovered checkpoint or receipt is validated too. `test_f12_an_incomplete_answer_is_never_recorded_or_cached[empty, omitted, duplicate, unknown, discusses_without_how]`, `test_f12_verdict_problem_names_each_defect` |

### The review's "claims that don't hold"

All addressed by the fixes above: receipts no longer hold candidate text (F3); "off" now also stops work already
between its authorization and its send (F2); undo survives the refresh (F5); undo re-shows the current proposal and the
refresh resolves the heading (F6, F8); a hidden link stays hidden during a refresh (F9); A, B, A shows A's links (F7).
The stage review's `GATE_TABLE` placeholder now points here. The `systemd-run` launcher worked in this step.

### Other changes in this step

- `tests/test_deliverable_rpcs.py::test_the_report_cli_prints_aggregates_and_refuses_when_off` expected the report's key
  set without C2's `notes` row (added by the stage, never updated): the expectation now includes it.
- `test_the_successor_is_one_constant_after_rw6bs_followups` failed on a **stale bytecode file**, not a defect:
  `src/learnloop/config/__pycache__/template.*.pyc` predated the stage's fingerprint recompute (the edit kept the file's
  size within the same second, so Python reused the old `.pyc` and read main's fingerprints). Deleted; all 31 recorded
  fingerprints equal `defaults_fingerprint_for_version` (checked under `env -i` with empty `HOME`/`CODEX_HOME`/
  `LEARNLOOP_CONFIG_DIR`). The landing gate builds fresh.
- `docs/reviews/curriculum-c2-notes-linked.md` updated: decisions 2, 6, 7 and 10, the constants, open questions 1
  (settled: no fallback) and 4.

## Gate (this step; targeted, memory-capped)

Every pytest/vitest/npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`,
one at a time, pytest `-n 6`, vitest `--maxWorkers=4`, `TMPDIR` outside the worktree.

| Step | Command | Result |
|---|---|---|
| Environment | `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| Import contracts | `uv run lint-imports --no-cache` | **37 kept, 0 broken** |
| Targeted pytest | `uv run pytest -n 6 <25 files below>` | **673 passed, 1 skipped** |
| Durability | `uv run pytest -n 6 -m durability tests/test_learner_notes_migration.py tests/test_notes_linked.py` | **1 passed** |
| Durability (production pragmas on the notes tests) | `uv run pytest -n 6 --durable-sqlite tests/test_notes_linked.py` | **37 passed** |
| Frontend | `npm install`; `npm run typecheck` | ok; typecheck clean |
| vitest | `npx vitest run --maxWorkers=4 src/screens/reader/readerNotes.test.tsx src/screens/reader/compareKeep.test.tsx` | **29 passed** (11 + 18) |
| Build | `npm run frontend:build` | ok |
| Desktop catalog | `desktop_generate.py`, then `desktop_validate.py` | passed: 297/297 TS/TSX + 5/5 Rust, ACTIVE=302, byte-for-byte reproducible |
| cargo | not run | nothing under `src-tauri` changed |
| DB reference | not run | no schema change (no migration touched; the F7 markers use `judgment_ledger`) |

Targeted pytest files (25): `tests/test_notes_linked.py` (37: 15 before + 22 for this review),
`tests/test_notes_never_read.py`, `tests/test_learner_notes_migration.py`, `tests/test_curriculum_c0b_landing.py`,
`tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_deliverable_codex_review.py`, `tests/test_deliverable_path.py`,
`tests/test_deliverable_rpcs.py`, `tests/test_deliverable_scope.py` (C0b's `ChatRoute`, which gained `validate`),
`tests/test_model_call_receipt_owners.py`, `tests/test_practice_index_paid.py`, `tests/test_receipt_exactness.py`,
`tests/test_ingestion_checkpoints.py` (receipts and `PaidCalls` recovery: `execution.py` changed),
`tests/test_ad_protected_tables.py`, `tests/test_ad_guard.py`, `tests/test_architecture.py`,
`tests/test_mobile_allowlist.py`, `tests/test_judge_routes.py`, `tests/test_public_tip_guards.py`,
`tests/test_tracked_fixture_databases.py`, `tests/test_cli_help_snapshot.py`, `tests/test_sidecar_serializer_snapshot.py`,
`tests/test_desktop_rpc_contract.py`, `tests/test_config_refactor.py`, `tests/test_table_roles.py`.

Vitest files: `apps/learnloop-tauri/src/screens/reader/readerNotes.test.tsx` (11: 6 before, 5 new or rewritten for
F4, F5, F11), `apps/learnloop-tauri/src/screens/reader/compareKeep.test.tsx` (18: one new for F10).

The full pytest suite, the whole durability lane and the whole vitest run were not run (owner rule 2026-10-17: once,
in the landing gate on the merged tree).

## Notes for the landing

- No migration added or changed (still 229); no successor.
- New ledger task `note_link_shown` (judge `exact_key`, left kind `deliverable_topic`): display state only.
- `ai/execution.py` gained `withhold_receipt_input()` (default off: every other route's receipts are unchanged) and
  `source_retrieval/deliverables.py`'s `ChatRoute.ask` an optional `validate` (default None: C0b/C1 unchanged).
- Delete stale `__pycache__` before the landing gate if the template's fingerprints were edited in place.

## Re-review (Codex gpt-6.1-sol, job `20261101-095420-8RRjte`, verdict REOPENED)

The re-review confirmed F1 fixed, reopened F2, and found F13 and F14 (Medium). **All three reproduced and fixed; none
rejected.** Each got a failing test first, run against `67e95a95b0` (before this step): the F2 admission test returned
`linked` with the notes off, the F2 record test wrote the proposals, F13's refresh back to A returned 0 and showed B,
and F14's polls ran tend's search 16 times where 4 were expected. **No live or paid call**: fakes only (the fake `tend`
over synthetic notes, `NoteLinkFake`, a synthetic generation-bound provider); no frontend, migration or schema change.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F2 | High | Notes authorization checked before, not with, the protection's snapshot | fixed | `4013aa95c0` | The coverage guard (`section_coverage.CoverageGuard`) takes an optional `also` authorization, judged on the **same** published snapshot as the protection and admitted only if that snapshot is still the published one (`still_published`, under the provider's lock; a reload meanwhile is read again, up to `RELOAD_RETRIES`, then refused). Its refusal raises `also_refusal` (`NotesSwitchedOff`). `NotesGuard.with_coverage(library, keys)` builds that guard with `also = the notes check`, so a request's final admission (`admit`), `PaidCalls`' attempt check and the record's check (`check`, inside the write transaction) each judge notes and protection on one snapshot. A refusal is kept for the rest of the judgment. The notes-only checks (shown-state markers, refreshed snapshots, `link_goal`) are generation-bound too (`published_snapshot`, `still_published`, shared with the coverage guard). With no `also`, the coverage guard is unchanged (C0a, C0b, C1 callers pass none). `test_re_f2_a_reload_during_the_requests_admission_refuses_it`, `test_re_f2_the_composed_gate_admits_on_one_snapshot`, `test_re_f2_a_reload_during_the_records_check_records_nothing`, `test_re_f2_an_unchanged_reload_still_links` |
| F13 | Medium | Reverting a manual note leaves an obsolete snapshot displayed | fixed | `4013aa95c0` | The snapshot a note shows is now tracked apart from snapshot creation order. A current-snapshot marker (`judgment_ledger` task `note_snapshot_current`, judge `exact_key`, left `learner_note` (the note's digest, never its path), right the snapshot's id) is appended by `_snapshot` whenever the text read is not the current snapshot's, including a text the note had before (its existing row is reused). `store.current_notes` reads the newest marker per note and falls back to the newest snapshot. The refresh and the display of hand links read it. No link row is written (no new acceptance) and no migration is needed. `test_re_f13_a_note_linked_by_hand_changed_and_changed_back_shows_its_text_now` (A, B, A shows A; then B again shows B; 2 snapshots, 1 link row) |
| F14 | Medium | Polling repeatedly restarts waiting jobs at the running cadence | fixed | `4013aa95c0` | Fixed in the handler, so any status read is safe: a run that ends `waiting` records `retry_at = now + NL.WAITING_RETRY_SECONDS` (60 s, labelled `keep` as a guardrail that bounds how often tend is searched again; it matches the Reader's `NOTES_POLL_MS.waiting`). `notes.path` restarts a waiting run only after that time, or at once with `retry` (the learner asking again). The frontend is unchanged: its 60 s waiting poll now reads `waiting` until the retry time, then starts one run. `test_re_f14_a_waiting_run_is_not_restarted_by_every_read` (3 polls start nothing, the passed wait starts one, `retry` starts one now, nothing metered is called) |

`WAITING_RETRY_SECONDS` is a module constant marked `keep`. It is not a config key, so it is not added to the
parameter registry: `note_links` is not in `MODULE_INVENTORY`, the same as the stage's other `keep` bounds
(`RESOLVE_K`, `LEAD_CHARS`).

### Re-review gate

| step | command | result |
|---|---|---|
| Sync | `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| Import contracts | `uv run lint-imports --no-cache` | **37 kept, 0 broken** |
| Targeted pytest (1) | `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 -q` + 19 files below | **645 passed** |
| Targeted pytest (2) | same scope, 7 files below | **57 passed** |
| Targeted pytest (3) | same scope, 5 files below | **66 passed** |
| Durability | not run | no migration or DB/connection code changed |
| Frontend (npm, vitest, build), cargo | not run | nothing under `apps/` changed |
| DB reference | not run | no schema change (the F13 markers use `judgment_ledger`) |

Files, run (1): `tests/test_notes_linked.py` (43: 37 before + 6 for this re-review), `tests/test_notes_never_read.py`,
`tests/test_learner_notes_migration.py`, `tests/test_section_coverage.py`, `tests/test_section_coverage_review.py`,
`tests/test_section_coverage_rpcs.py`, `tests/test_coverage_on_extract.py` (`CoverageGuard` changed),
`tests/test_deliverable_codex_review.py`, `tests/test_deliverable_path.py`, `tests/test_deliverable_rpcs.py`,
`tests/test_deliverable_scope.py`, `tests/test_curriculum_c1_plan_follows_path.py`, `tests/test_curriculum_c0b_landing.py`
(the other `CoverageGuard` callers), `tests/test_reader_ca5_also_in_books.py`, `tests/test_reader_ca5a_find_section.py`,
`tests/test_reader_ca6_side_by_side.py`, `tests/test_roles_judges.py`, `tests/test_mobile_allowlist.py`,
`tests/test_architecture.py`. Run (2): `tests/test_reader_ca2_fix_orchestrator.py`, `tests/test_reader_ca3_landing_ca5a.py`,
`tests/test_reader_ca4_landing.py`, `tests/test_reader_ca5_landing.py`, `tests/test_facet_reword_confirm_review.py`,
`tests/test_tracked_fixture_databases.py`, `tests/test_desktop_rpc_contract.py`. Run (3): `tests/test_ad_protected_tables.py`,
`tests/test_ad_guard.py` (new `judgment_ledger` writes), `tests/test_sidecar_serializer_snapshot.py`,
`tests/test_public_tip_guards.py`, `tests/test_table_roles.py`.

The full pytest suite, the whole durability lane and the whole vitest run were not run (owner rule 2026-10-17).

### Notes for the landing (re-review)

- New ledger task `note_snapshot_current` (judge `exact_key`, left kind `learner_note`, right kind
  `learner_note_snapshot`). It records display state only. No migration (still 229).
- `section_coverage.CoverageGuard` gained an optional `also` / `also_refusal` pair (default none, so existing callers
  are unchanged), plus the module functions `published_snapshot` and `still_published`, which it now uses itself.

## Round 3 (Codex job `20261101-101544-wk64cb`): F1, F2, F14 confirmed fixed; F13 reopened, fixed

Codex's round 3 confirmed F1, F2 and F14 fixed and every other round-1 finding fixed, and reopened F13: *a delayed
judgment reactivates an obsolete snapshot*. The learner links note A by hand; a background judgment reads A and is held;
the note changes to B and a concurrent refresh shows B; the judgment of A is then recorded, and `_snapshot` (called for
each AI proposal) reused A's row and appended a current-snapshot marker, making A current again; when the next topic is
unavailable, `link_goal` returns `waiting` before its final refresh, so A stays displayed.

**Fix (structural, as directed): snapshot storage is separate from advancing the current marker.**

- `_store_snapshot` stores a snapshot (once per content hash) and nothing else. Recording AI proposals calls only this:
  **a model's proposal never advances `note_snapshot_current`**, and it keeps the snapshot it judged through its link
  row's `note_id` (shown as such).
- `_show_read` is the only writer of the marker, called only by a read of the note made to show it: `link_by_hand` and
  `refresh_learner_links`. Each read captures the note's marker revision **before** asking tend
  (`store.current_revisions`: the newest marker's `rowid`, 0 with none) and, inside its write transaction, advances the
  marker only if the revision is unchanged (compare-and-set); otherwise a newer read stands and nothing is stored. A
  refresh whose write is dropped is not counted; a link by hand whose compare-and-set loses still writes its link row
  (naming the snapshot the learner linked), and the note shows the newer read.
- `store.current_notes` now reads markers only, in append order (marker `rowid`; markers are appended only under the
  compare-and-set inside a write transaction, so append order is record order). The fallback to the note's newest
  snapshot is gone: it would have let a snapshot stored for a proposal become what a note shows. Every note linked by
  hand has a marker (its link appends one, or a newer read already did).

Failing tests first (both failed on `bb4b647e7d` for the reported reason, both pass now):
`test_re3_f13_a_delayed_judgment_never_makes_its_snapshot_current_again` (the exact interleaving: hand link A, the
judgment of A held at the model while the note changes to B and a refresh shows B; after the judgment records, the
hand link shows B with no further refresh, the model's proposal shows A, and exactly 2 markers exist) and
`test_re3_f13_a_refresh_whose_marker_was_advanced_meanwhile_writes_nothing` (a refresh reads B slowly while the note
changes to C and another refresh shows C: the slow refresh writes nothing, C shows, and no B snapshot is stored).

Files: `src/learnloop/source_retrieval/note_links.py`, `src/learnloop/db/stores/learner_notes.py` (its store, used only
by `note_links`: `current_revisions`, marker-only `current_notes`), `tests/test_notes_linked.py`. No migration, schema,
frontend or config change.

`WAITING_RETRY_SECONDS` is not added to `parameter_registry`: the registry's module-constant audit
(`module_numeric_constants`) scans only `MODULE_INVENTORY`, which does not list `note_links` (nor any other C2 module),
so nothing expects it there; it stays a module constant labelled `keep`.

Targeted gate: `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run --no-sync pytest -n 6
tests/test_notes_linked.py tests/test_notes_never_read.py tests/test_learner_notes_migration.py`: **52 passed**.
