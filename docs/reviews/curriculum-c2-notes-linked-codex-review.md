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
| F4 | Medium | Completed background links never reach the open UI | fixed | `b23e92d402` (server test `184d58b128`) | `usePathNotes` reads the path again every 3 s while `linking` is `running` and every 60 s while `waiting` (which restarts a waiting run); the transition to `done` calls the context's `onChanged`, so the margin marks and Compare's band read again. `NOTES_POLL_MS` is a UI cadence labelled `keep`. vitest "while the background linking runs the path is read again, and its end refreshes every surface (F4)", "a waiting linking is asked again later, quietly (F4)"; pytest `test_f4_background_linking_completes_and_the_next_read_shows_it` (real background job, not `notes_inline`) |
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
