# Curriculum C0b: scope resolution and the deliverable path

**Stage:** `curriculum-c0b-scope-path`, branch `curriculum/c0b-scope-path` (worktree `learnanything-docs`), base
`5b3f66059`. **Spec:** `docs/specs/spec_deliverable_curriculum_v1.md` §5, §7.1-§7.5, §8.5, §9, §11 and the §12 C0
row (the second half of C0; C0a, section coverage and `reader.correspondents`, is on main). **No paid or live call
was made**: every model is a fake (`StructuredClientFake` doubles); every ad-hoc script ran with an empty, existing
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault was opened, `~/.config/learnloop` was not read, and
nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`. Display only: **no
successor** (C1, the plan following the path, is the successor).

## What was built

| Piece | Where |
|---|---|
| Migration **228** (one migration; RW6b part 1 owns 227): `deliverable_scope_inputs` (RAW_LEDGER: text, topic list, passage refs, correction, depth), `deliverable_scope_resolutions` (WORKFLOW: the needed LOs with the phrase each answers, the unmatched phrases with a proposed LO and their state, the facet scope written, `origin` resolver or learner), `deliverable_path_sections` (WORKFLOW: §7.4's columns plus `commitment_id` for *check me later*; one judge row per (goal, depth, state_key, LO, section)). All append-only by trigger | `migrations/228_deliverable_curriculum.sql`; store `src/learnloop/db/stores/deliverables.py` |
| Classification: `table_roles` (RAW_LEDGER, WORKFLOW, WORKFLOW; no DERIVED table, so no replayer); AD `protected_tables` (path rows and scope inputs PROTECTED and READING, resolutions NEUTRAL; derived columns unread), `column_classes` | `db/table_roles.py`, `adaptive_difficulty/protected_tables.py`, `column_classes.py` |
| The deliverable is a learner goal (§5.1): `create_deliverable` writes it to `goals.yaml` under the vault mutation lock with the learner's sentence as `intent_sentence` and first scope input; kind shown, never stored (exam when `exam.enabled`, else quest) | `source_retrieval/deliverables.py` |
| Scope inputs (§5.2): `add_input`; a passage is read through the one predicate first and an exam, held-out or held-back span is **refused before a row is written**, in plain words (G-C2) | `deliverables.add_input`, `passage_texts` |
| Resolution (§5.3): one call (route `deliverable_scope_resolver`) over the inputs in order and the vault's active LOs as compact records (id, title, statement, concept, prerequisites; never items); ids validated; the resolution row and a `deliverable_scope` ledger verdict; then the goal's `facet_scope` written under the lock (`write_facet_scope`). Same inputs over the same LOs: answered from the row, no call. Re-resolution only when an input is added | `deliverables.resolve` |
| Unmatched phrases never create an LO without the learner's yes: `decide_unmatched` (*add it* / *no*), a `learner` resolution row and a `learner_card` verdict | `deliverables.decide_unmatched` |
| `create_goal_lo`, built once to TE §11.5 (nothing on main had it): the text-gap write's ids-from-the-request idempotency, the vault lock, the undo (dormant), the daily cap shared with text-gap creations plus one a day for an explicit goal; `origin = codex_proposal`, `mechanism = deliverable_scope_v1` (TE2 passes `teacher_goal_v1`) | `src/learnloop/goals/goal_lo.py` |
| Depth (§5.4): a `depth` input, the newest standing, asked once | `deliverables.depth_of` |
| "Also about…" (§6.5): the learner's words resolved by the same resolver (no new route), kept as C0a's `is_about` correction with the words | `deliverables.also_about` |
| The deliverable path (§7.1-§7.4): one call per deliverable and depth (route `deliverable_path_judge`) over the needed LOs, the prerequisite closure (depth 1 for *get the idea*, 2 otherwise; and what primary-eligible sections assume), statuses, C0a's standing coverage across books (titles, treatment, roles, notation, minutes: **no passage text**) and the learner's context. Code: one primary per LO, primary-eligible (`introduces`/`develops`) or code's fallback with code's line; honest labels after the model and at display; alternates only from the LO's own coverage; prerequisites ordered first; one exercise per core section (RW7a's statement reader); rows and `deliverable_path_role` verdicts in one transaction | `source_retrieval/deliverable_path.py` |
| Overrides (§7.3): *use this one instead*, *read it anyway*, *skip it*, *I know this, check me later* (a `test_me_later` commitment, `provenance = {via: "deliverable_path", goal_id}`; the line is off the path while the check is pending, back with its honest label once answered), `none`; the newest learner row per (goal, depth, LO) stands across re-judgments | `deliverable_path.override`, `effective_lines` |
| The Guide's slice (§7.5): this book's core, prerequisite and alternate lines, the other-book lines ("on your path in Strang §6.1"), "not needed for <deliverable>", "not in your books yet"; `status: none` leaves the card to RW7a. The deliverable is RW7a's `goal_for_source` pick when it is a deliverable (so the two never disagree), else the deliverable whose path names this book | `deliverable_path.guide_goal`, `guide_slice` |
| "Am I ready?" (§8.5): a pressed button. One Check once per needed LO not demonstrated and without a pending check; the item chosen by code (unattempted, no reveal, never protected through `learner_protection.withheld_items`, fail closed) or the LO (DL2's serving picks after its routine exclusions); dated by retrievability, never after the deadline. The answer per LO: demonstrated / likely (AD's labelled prediction, injected by the sidecar) / untested, with the dated checks | `deliverable_path.readiness`, `ready_checks`, `check_due`, `check_item` |
| `curriculum.coverage_on_extract` (§6.3): every path that establishes an extraction (`queue_source_vectors`) queues one `curriculum_coverage_on_extract` job while both switches are on and some LO is covered, coalesced only with a job still queued (one queued, one running: an extraction completed during a run queues one more pass; Codex review F7); the job reads both switches when it runs and before each LO (F3) and judges every covered LO again under `plan_fallback.quiet()` (no offer, no grant), coalesced per LO (a fresh state pays nothing), protection read from the vault's files before each LO; plan down: `waiting`, nothing asks | `section_coverage.rejudge_on_extract`; `content/pipeline/jobs.py` `queue_coverage_on_extract`, `handle_curriculum_coverage_on_extract`; `runner.KNOWN_JOB_TYPES` |
| RPCs (desktop only, pinned): `curriculum.deliverables`, `create_deliverable`, `set_scope` (§5.3's new RPC), `scope`, `scope_decide`, `set_depth`, `path`, `guide_slice`, `path_override`, `ready`, `ready_check`, `also_about`. A scope change spawns the coverage its LOs owe (never judged), and a path read starts the judgment once no coverage runs; both in the background under the spawning request's unit (T1) | `src/learnloop_sidecar/handlers/deliverables.py` |
| CLI `learnloop curriculum report` (§11): the coverage row (corrections per judged row), the choice row (swaps and skips per path line), the time row (the path's minutes against book order, labelled an estimate); aggregates only, never sections read or completion as success | `cli/curriculum.py`, `deliverable_path.report` |
| Config: `[curriculum] coverage_on_extract` (true); routes `ai.routing.deliverable_scope_resolver` and `ai.routing.deliverable_path_judge`; both in `METERED_PRICE_SETTINGS` (`source_retrieval.llm_price_per_million`) and sharing C0a's `curriculum.max_daily_cost_usd` (C0a's envelope now counts all three routes); disclosures for both routes (the resolver reads the learner's words; the path judge their reading context); the switch classified in `parameter_registry` | `config/schema.py`, `ai/routing.py`, `ai/plan_fallback.py`, `ai/disclosures.py`, `params/parameter_registry.py` |
| Frontend: `GuidePathSlot` in the Guide's path slot (the slice when one names the book, RW7a's card otherwise or when `curriculum_disabled`; "this book alone" shows RW7a's card); `DeliverableSliceCard` (depth asked once, lines with why, alternates with *use this one instead*, *skip it*, *I know this — check me later*, undo, *not what I need…* to the resolver, other-book lines, not needed, not in your books, "Am I ready?"); DTOs, client calls, Rust passthroughs | `apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.tsx`, `deliverableSlice.ts`, `ReaderScreen.tsx`, `api/dto.ts`, `api/client.ts`, `src-tauri/src/commands.rs`, `main.rs` |
| Head fixture `migration_head_228` (renamed from 226; only 228 applied to a backup-API copy; rollback mode, header 1/1, integrity ok, FK check empty; exactly 228's 17 objects added, only `schema_migrations` gained a row) | `fixtures/migration_head_228/README.md` |

## T1 (plan-first)

- Both routes resolve like every routed task (the ChatGPT plan by default); `test_plan_first_transport_paid_roles`
  enumerates `get_args(AITask)`, so they are covered by construction.
- In-request calls (the resolver in `create_deliverable`, `set_scope`, `also_about`) are pressed actions: a plan
  failure offers OpenRouter keyed by that RPC through the request's collector (redesign D).
- Spawned work (a scope change's coverage, a path judgment) captures `unit_token` / `unit_origin` / `unit_stamp`
  in the request (RW7a's and C0a's pattern) and runs under `plan_fallback.unit`; a failed job keeps its offer and
  the next read relays it once.
- `coverage_on_extract` runs under `plan_fallback.quiet()`: no offer, no grant
  (`test_the_job_runs_quiet_and_never_offers_openrouter`).

## Protection (§9)

- **G-C1:** `test_gc1_no_exam_or_held_out_text_reaches_the_resolver`,
  `test_gc1_no_exam_or_held_out_text_reaches_the_path_judge_and_no_row_names_them` (the exam question and the
  held-out sentinel never appear in a captured prompt; no path row names the exam or the held-out section), plus
  the RPC flow's check on every path prompt.
- **G-C2:** `test_gc2_an_exam_passage_is_refused_as_a_scope_input_and_nothing_is_written` (exam and held-out spans;
  nothing written), `test_set_scope_refuses_an_exam_passage_and_writes_nothing`.
- **G-C3:** `test_am_i_ready_creates_one_check_per_untested_lo_never_an_exam_reserved_item`,
  `test_g_c3_held_out_items_are_never_picked` (and unreadable protection picks no item).
- Exam-role sources have no teaching authority, so C0a's library never lists them: never a primary or an
  alternate. A section withheld since a judgment is never shown, and that judgment's model lines are replaced by
  code's (RW7a's rule; `test_a_section_withheld_since_judging_is_never_shown_and_reasons_are_codes`).
- AD reads none of the three tables (`test_ad_protected_tables`, `test_ad_protected_readings`).

## Display only

No plan, scheduling, projection, grading, serving or replay path reads the three tables. The writes beyond them
are the learner's own acts: the goal's facet scope (`curriculum.set_scope`, as `create_goal` and DL2's deadline
write a goal), an LO created on the learner's yes, Check once commitments the learner pressed for (served by DL2's
unchanged rule, the RW1b reconstruct precedent), C0a coverage rows and ledger verdicts. With
`curriculum.enabled = false` every C0b RPC refuses (`curriculum_disabled`), nothing is called or written, and
`reader.reading_path` is byte-identical whatever deliverables exist
(`test_switched_off_rw7a_is_byte_identical_whatever_the_deliverables`); the frontend slot is RW7a's card.

## Decisions taken here (open to the owner or the landing)

1. **The goal's scope names facets, not concepts** (DL2's `set_deadline` rule, Codex review F8): a concept pulls in
   every LO on it. An LO with no evidence facet is named by its concept, its only handle (the spec's "concepts,
   plus facets where narrower" read the other way round).
2. **The resolver runs in the pressed request** (synchronously), not as a job: one call, the learner waits on
   their own action; the desktop's per-request timeout bounds it.
3. **The Guide's slice has its own RPC** (`curriculum.guide_slice`) instead of riding `reader.reading_path`, so
   RW7a's RPC is byte-identical whatever the switch; the T1 origin of a Guide-started path judgment is therefore
   `curriculum.guide_slice` (the spec names `reader.reading_path`). The slice lives in the Guide's path card, so it
   shows where that card does (`reading_paths.enabled`, on by default).
4. **Depth and DL2's intent:** DL2's intent scopes are LO, item, subject and source; there is no goal scope yet, so
   §5.4's `INTENT_DEPTH` mapping has nothing to read. The depth is asked once (`curriculum.set_depth`).
5. **The learner context** sent to the path judge is the books read (named, not counted: the context is in the
   cache key, and a count would re-judge the path after every section), the earlier *use this one instead* /
   *skip* choices, the days left and, since the Codex review (F11), the path's sections the learner said didn't
   help (RW1c's `remediate` follow-ons), their kept comparisons and takes on these LOs (RW4d), and the minutes
   available before the deadline (DL1's remembered daily minutes times the days left). Section minutes are DL1's
   (`plan.read_words_per_minute`), so the path's and the available minutes are comparable.
6. **"Am I ready?" creates the checks when pressed** and answers with the lines (one button, never a prompt). The
   item rule is TE §13's minus two conditions with nothing to read on main: "never served to a chat host" (no
   chat-host serve record yet) and "not from a family shown on the path's exercises" (the path's exercises are
   source exercises, not items).
7. **"Likely"** is AD's `lo_readiness` (every cell "likely ready"), injected by the sidecar: `source_retrieval`
   importing AD breaks the frozen-cycles contract.
8. **No durable claim** per path judgment (C0a's decision 6): one sidecar never judges the same (goal, depth,
   state) twice at once; two processes could pay twice on the plan (no money; proportionate-protection bar).
9. **Coverage owed** (LOs never judged) is spawned by a scope change and by a path or slice read; the path judge
   waits while coverage runs, so a path is not paid for twice on partial coverage.
10. **On-extract with the plan down** completes `waiting` (no retry timer): the next extraction or a pressed check
    judges again, and nothing asks.
11. **Passage inputs are built in C0** (the C0 row names text and topic lists) so that G-C2 is enforced and tested
    now; the `syllabus` source role stays C3's.
12. **The report has no "alternates opened" count** (nothing records an open yet).
13. **Creating a deliverable and reviewing its scope live in the Guide** (Codex review F4): under the path card,
    while no deliverable names the open book, *learning this for something?* (the learner's sentence, an optional
    topic list, a deadline, exam) and *your deliverables* (each one's topics with their phrases, *add it* / *no*
    on phrases not in the library, *not this…* / *add…* text boxes, the receipt, the depth); on the slice, *what
    it covers* opens the same panel. The Goals screen could host it too later.

## Constants

Structural bounds, each labelled in its module: `INPUT_CHARS`, `PHRASE_CHARS`, `STATEMENT_CHARS`,
`PROPOSAL_CHARS`, `REASON_CHARS`, the prompt's chars-per-token and overhead (as `compare_sources`), the paid-call
runaway caps (as RW7a). `CLOSURE_DEPTH` (1 / 2 / 2) is `keep`, with RW7a's depth semantics as the reason.
`EXPLICIT_GOAL_ALLOWANCE = 1` is `keep` (TE §11.5's "by one a day", a burden guardrail). "Am I ready?" dates
(Codex review F13): no new number. The retrievability target is DL2's `intent.recall_targets.keep_in_touch` (the
check's own depth preset) and the no-state delay DL2's `capture.test_me_later_days`, both registered decision
parameters read from the vault's configuration; `READY_MAX_WAIT_DAYS = 14` stays `keep` (a promised check is never
dropped). The path judge's prompt bound is `curriculum.max_prompt_tokens` (F12), made smaller by structural steps
(`PROMPT_LEVELS`: drop roles and notation, then non-eligible sections), never by a number. Config: one switch
(`coverage_on_extract`, classified structural); the two routes add no number (they share C0a's `keep` caps). No
weight, margin or threshold.

## Gate (this step; targeted, memory-capped)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G
-p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time (the 86-file sweep also
under `flock /tmp/learnloop-fullsuite.lock`). The full suite, the whole durability lane and the whole vitest run
were **not** run (owner rule 2026-10-17: once, at landing).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (a first draft imported AD's readiness into `source_retrieval`, breaking the frozen-cycles contract; the prediction is injected by the sidecar instead) |
| Fail-first: `test_coverage_on_extract.py` before its implementation | 5 failed (then 5 passed) |
| Targeted sweep, 86 files: every test file added or changed (the five new C0b files, the head-path rename and the migration-chain diffs in 49 files, `test_mobile_allowlist`, `test_judge_routes`, `test_architecture`, `test_cli_help_snapshot`), the changed modules' consumers and the contract tests (listed below) | **1,936 passed, 4 skipped** (14 min 57 s) |
| After the sweep, two guards (an LO with no candidate is searched once per session, not on every read; no path call when no LO has a primary-eligible section) and their tests: the five C0b files | 51 passed |
| `-m durability` on `test_deliverable_curriculum_migration`, `test_section_coverage_migration`, `test_session_ownership_migration`, `test_migrations`, `test_tracked_fixture_databases`, `test_reader_rw7a_migration`, `test_retrieval_spaces_migration`, `test_ad1_migration`, `test_approach_maps_schema`, `test_help_assists_schema`, `test_library_asks_migration`, `test_learner_claim_application_migration`, `test_learner_claim_superseded_migration`, `test_reader_rw3b_migration`, `test_rw2d_receipts_migration` | 11 passed |
| `--durable-sqlite` on the five C0b files | 51 passed |
| Defaults fingerprints: all 29 recomputed with `defaults_fingerprint_for_version` (after clearing `config/__pycache__/template*.pyc`); dropping `curriculum.coverage_on_extract` and the two routes from each version's effective config reproduces main's hash at **every** version | ok |
| CLI help snapshot regenerated (`<root>`, `curriculum`, new `curriculum report`) | ok |
| `db_generate_reference.py`, `db_validate_reference.py` (head 228) | 0 errors; 357 table notes, 1,069 configuration leaves (prose counts updated in `Configuration.md` and `Database.md`); `validate_vault.py` passes (1,165 notes, 1,163/1,163 reachable) |
| Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4` on `DeliverableSliceCard.test.tsx`, `ReadingPathCard.test.tsx`, `readingPathsReader.test.tsx`, `readingPathsRefresh.test.tsx`, `readingPathsSwitchOff.test.tsx`, `figuresWithReadingPath.test.tsx` | 6 files, 31 passed |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok |

**Test files in the sweep** (for reading the landing gate against): `test_ad1_migration.py`, `test_ad23_migration.py`, `test_ad23_t1_routes.py`, `test_ad_guard.py`, `test_ad_protected_readings.py`, `test_ad_protected_tables.py`, `test_approach_maps_schema.py`, `test_architecture.py`, `test_codex_tool_lockdown.py`, `test_config_refactor.py`, `test_coordinated_migrations.py`, `test_coverage_on_extract.py`, `test_decider_landing.py`, `test_deliverable_curriculum_migration.py`, `test_deliverable_path.py`, `test_deliverable_rpcs.py`, `test_deliverable_scope.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_replay.py`, `test_eval_harness.py`, `test_exam_protection_review.py`, `test_field_config.py`, `test_help_assists_schema.py`, `test_hint_telemetry.py`, `test_import_split_parity.py`, `test_ingest_jobs.py`, `test_ingest_runner.py`, `test_judge_routes.py`, `test_label_roles_cli.py`, `test_learner_claim_application_migration.py`, `test_learner_claim_superseded_migration.py`, `test_library_asks_migration.py`, `test_local_index.py`, `test_method_explicit_upgrade.py`, `test_migrations.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_pfc_unverified_unassessed.py`, `test_plan_determinism.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_paid_roles.py`, `test_plan_first_transport.py`, `test_plan_first_transport_today_quiet.py`, `test_plan_follows_path.py`, `test_provider_resolution_parity.py`, `test_public_tip_guards.py`, `test_reader_ca2_fix_orchestrator.py`, `test_reader_rw3b_migration.py`, `test_reader_rw7a_migration.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_orchestrator.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_upgrade.py`, `test_retrieval_spaces_migration.py`, `test_roles_concurrency.py`, `test_roles_judges.py`, `test_roles_switch_off.py`, `test_route_rules_in_grader.py`, `test_rw2d_receipts_migration.py`, `test_rw7b_codex_review_fixes.py`, `test_section_coverage_migration.py`, `test_section_coverage.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`, `test_session_ownership_migration.py`, `test_shadow_rebuild.py`, `test_sidecar_serializer_snapshot.py`, `test_source_roles.py`, `test_t1_batch_origin_migration.py`, `test_table_roles.py`, `test_tracked_fixture_databases.py`, `test_voyage_fallback.py`.

## Landing notes

- **Migration number.** 228 on main's 226; RW6b part 1 holds 227. Either order works (the runner is set-based).
  If RW6b lands first, rebuild `migration_head_228` from main's head at 227 with 228 applied, and add 227's objects
  to the chain diffs; if this lands first, RW6b applies 227 on top.
- **Expected conflicts:** `config/template.py` (one comment line per version and the hashes: recompute),
  `tests/cli_help_snapshot.json` (`<root>`), the head path in ~50 tests and the two reference scripts, the
  migration-chain lists, `src-tauri` command lists and `api/client.ts` / `dto.ts` (CA5a, CA3, CA4 add Reader
  calls beside these), `ReaderScreen.tsx` (the Guide's path slot), the reference notes (regenerate).
- **No successor**, no algorithm version, no replayer.

## Open questions

1. ~~Where does a learner create a deliverable and review its scope lines?~~ Built in the Guide by the Codex
   review fixes (F4, decision 13); the Goals screen could host the same panel later.
2. Should the slice also show where the Guide has **no path card** (`reading_paths.enabled` off)? Today it does
   not: the goal card stays, exactly.
3. The spec names `reader.reading_path` as the origin of a Guide-started path judgment's OpenRouter offer; here it
   is `curriculum.guide_slice` (decision 3). A grant given on one does not cover the other.
4. Should **DL2's intent** gain a goal scope, so the depth and the deliverable's intent are one setting (§5.4,
   §8.4)? Not built: that changes DL2's commitments.
5. ~~The learner context omits RW1c's rows, kept comparisons and DL1's minutes.~~ Added by the Codex review fixes
   (F11, decision 5).

## Landing onto main (2026-10-31)

Landed in `learnanything-docs` on `curriculum/c0b-scope-path` (stage tip `68d9c2f60`, base `5b3f66059`) by merging
`main` twice: `e668f7121` (Reader CA5a, Reader CA3, the Codex CLI 0.165 lockdown; mvp-0.38; migrations through 226),
then `3a96d90b4` (Reader CA4, which reached main during the gate). Main was neither fast-forwarded nor pushed.
Migration **228** keeps its number: RW6b part 1 owns 227 and lands after. The runner is set-based, as
`migration_head_217` held 215/216/217 without 214. No successor.

### Commits and conflicts

| Commit | What |
|---|---|
| `f2a2fa37e` | `--no-ff` merge of `e668f7121`. **Conflicts:** `config/template.py`: every default snapshot mvp-0.9 … mvp-0.38 keeps main's CA5a/CA3 notes and C0b's note. **All 29 fingerprints** were recomputed with `defaults_fingerprint_for_version`, with the template `.pyc` cleared before and after; a recheck found 0 mismatches. `params/parameter_registry.py`: CA5a's `reader.correspondence.enabled` rule and C0b's `curriculum.coverage_on_extract` rule are both kept. `src-tauri/src/commands.rs` and `main.rs`: CA5a's four passthroughs and C0b's twelve. `tests/test_mobile_allowlist.py`: C0b's, CA5a's and CA3's RPCs are all desktop-only, joined in one union in the parametrized list. 432 generated reference notes were taken from the branch and regenerated in the next commit. **Auto-merged:** `ReaderScreen.tsx` (C0b's `GuidePathSlot` wraps RW7a's card, beside CA3/CA5a's Guide changes), `api/dto.ts`, `api/client.ts`, `ai/disclosures.py`, `ai/routing.py`, `config/schema.py`, `section_coverage.py`, the sidecar handler list and `tests/test_judge_routes.py`. No test on main names `migration_head_226`, so the head path stays `migration_head_228` everywhere. |
| `45c24303e` | DB/config reference regenerated: 1074 effective leaves in 75 sections, 357 table notes. The auto-merged prose counts in `Configuration.md` and `Database.md` were corrected by hand. `db_validate_reference.py`: errors []; `validate_vault.py` passes. |
| `fbf37405f` | The interaction tests: `tests/test_curriculum_c0b_landing.py`, 7 tests (below). **Gate head.** |
| `b5ae99886` | `--no-ff` merge of `3a96d90b4` (Reader CA4). **Conflicts:** `template.py` only. Every snapshot keeps CA4's and C0b's notes, and all 29 fingerprints were recomputed again (0 mismatches). The 433 reference notes were regenerated in the next commit. |
| `e45dd3125` | DB/config reference regenerated: **1076 effective leaves in 75 sections** (main's 1073 + C0b's 3), 357 table notes. `db_validate_reference.py`: **errors []**; `validate_vault.py` passes (1166 notes, 1164/1164 reachable). |

`git diff main` lists no binary or tracked database besides the head fixture, and nothing under `fixtures-local/`.
`.gitignore` is unchanged.

### Interactions (`tests/test_curriculum_c0b_landing.py`; every model a fake)

All 7 tests passed on their first run against the product code. The only edits were to my own harness: a column
name, and the item's own rubric for the self-graded attempts. Nothing needed fixing.

**(i) CA5a's *not about this* with C0b's *also about…* on one section.**
- On C0a's coverage vault, CA5a's dismissal of the Lay hit `lay_eigen` from Chapter 5 writes `not_about` for
  `lo_eigen`. On the same section, *also about* "determinants" resolves through the scope resolver to `lo_det` and
  writes `is_about`.
- After a C0a re-judgment of both LOs (the correction made `lo_det`'s state new), both learner rows still stand.
- The deliverable "eigenvalues and determinants" is then path-judged at `learn_to_use_it` and judged again at
  `fluency`. Both judgments send `lay_eigen` for Determinants and never for Eigenvalues.
- Both paths show it only under Determinants, and the newest corrections are unchanged after each judgment.

**(ii) CA3's `compare_scope` and C0b's resolver are separate routes with separate caps; `curriculum.enabled` off.**
- **Routes.** `compare_scope`, `deliverable_scope_resolver` and `deliverable_path_judge` are distinct `AITask`s.
  `compare_scope` is not one of the curriculum envelope's owner kinds.
- **CA3's cap.** With `reader_compare.scope_max_calls_per_day = 1` used up (the second reading falls back as
  `capped`), the resolver still makes its call, and `calls_today` stays 1.
- **The curriculum's cap.** With the curriculum's dollar cap exhausted for a metered resolver (refused before its
  call), CA3's Decider still reads, with one call.
- **Switch off.** With `curriculum.enabled = false`, a vault with a deliverable and its twin without one give the
  same `reader.prompt_contract`. CA5a's `correspondence` is absent: its data belongs to `curriculum.enabled`, as on
  main. CA3's reading is the same on both, and `reader.correspondents`, `curriculum.guide_slice` and
  `curriculum.path` refuse.
- **Against main's own code** (the smoke below): with curriculum off, `reader.reading_path` for every extraction and
  `reader.prompt_contract` are byte-identical to main's. With curriculum as the copies have it (on by default), the
  prompt contract is identical to main's too.

**(iii) Check once commitments vs the mvp-0.38 cold-retry reschedule.**
- Setup: on a vault at mvp-0.38 with CA2's rule on, a *check me later* on a path line plus *Am I ready?* on a second
  deliverable create three `test_me_later` commitments (`via` `deliverable_path` / `deliverable_ready`).
- An assisted attempt (a hint) is then made on each check's item.
- With the reschedule **on** (`reschedule_cold_after_assist_active` true) and **off**, the folded commitments and the
  `followup_tasks` are identical. There is no `cold_retry` and no `assisted_cold_retry` opportunity, and the checks
  keep their targets, action and dates.
- `shadow_rebuild` is **0/0/0** (live database unchanged) with the checks present, both before and after the help is
  taken. The vault is synced at the tag first, as `test_cold_retry_reschedule.py` builds its rebuild-equivalent
  vault: the deliverable vault as built shows a mastery 6 diff before anything C0b does.

### Regeneration

- **DB/config reference:** regenerated and validated after each merge, as above. **Defaults fingerprints:** all 29
  recomputed after each merge.
- **The CLI help snapshot, sidecar serializer snapshot, desktop RPC contract and mobile allowlist** (all
  `curriculum.*` desktop-only) pass as merged. Nothing else needed regenerating.

### Gate (`env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/c0b/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`; `lint-imports --no-cache` | **36 kept**, 0 broken |
| After the first merge, targeted contract run (58 files: snapshots, fingerprints, config refactor, registry audit, CLI help, serializer/RPC pins, mobile allowlist, table_roles, migrations, switch-off pins, AD protection, judge routes, public-tip guards, the C0b/C0a/CA3/CA5a files, the upgrade chain files, shadow; `-n 6`, 5G) | **1179 passed**, 6 skipped (14 min 15 s) |
| Full suite at `fbf37405f` (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,522 passed, 1 failed**, 89 skipped, 47 xfailed. pytest 2,065.8 s (34:26); wall 34 min 28 s after an 8 min 22 s wait for the lock. The failure is `test_codex_tool_lockdown::test_a_workspaces_own_project_layer_never_reaches_the_turn`, deterministic alone (3/3). It comes from **this worktree's name**: the test rejects any launch override containing the substring `docs`, and `TMPDIR` (`…/learnanything-docs/fixtures-local/landing/tmp`) lands in the catalog path of a permissions override. With the same `env -i` and a `TMPDIR` outside the worktree it passes 3/3. This is not a C0b defect, and the test is main's (the Codex 0.165 lockdown); it is not changed here. |
| Durability (`-m durability`, flock, 5G, `-n 6`) | **176 passed**, 1 skipped (54.1 s; wall 55 s after a 43 s wait for the lock) |
| Owner lane (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-c0b/`) | 83 passed, **2 failed**, 4 skipped (45.1 s; wall 45 s). The failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy. |
| After the second merge (CA4) | Targeted contract run (the same 58 files): **1179 passed**, 6 skipped (13 min 14 s). The CA4, keep and compare files with the landing tests (`test_reader_ca4_landing`, `test_reader_ca4_table_by_point`, `test_compare_sources_keep`, `test_reader_ca3_codex_review`, `test_curriculum_c0b_landing`, `test_codex_tool_lockdown`): 245 passed, 1 skipped, 1 failed, the lockdown test above (40 s). **The full suite was not rerun:** CA4 changed `compare.py`, `library_ask.py`, `kept_comparisons.py` (keep writes, by-point cards) and config. C0b changes none of them, and it reads only `kept_comparisons_for_card`, whose body CA4 left unchanged. |
| Frontend (`apps/learnloop-tauri`, after the second merge) | `npm install` ok; `npm run typecheck` clean; whole vitest (`--maxWorkers=4`, 5G): **229 files, 2029 passed** (44.3 s; wall 45 s); `npm run frontend:build` ok; `cargo check --manifest-path src-tauri/Cargo.toml` ok |

### Parity and smoke on owner copies

**Setup.**
- Fresh backup-API copies of the three mvp035 owner copies were made twice, in `fixtures-local/smoke-c0b/run2/`: one
  set for the merged branch's code, one for main's code (`git archive 3a96d90b4`).
- Everything ran under `env -i` with an empty `HOME`, `CODEX_HOME` and config dir. AI base URLs pointed at
  `127.0.0.1:9`, and `LEARNLOOP_COVERAGE_MODELS=off` was set (the CA3 smoke's setting).
- The sidecar ran as a real process with audit hooks that refuse non-loopback sockets and process starts. They
  **logged nothing**.
- Only counts and status or refusal codes were recorded. Drivers: `fixtures-local/landing/smoke_c0b/smoke.py`,
  `followup.py`.

**Results.**
- **Upgrade.** `learnloop upgrade --to mvp-0.38` prints `mvp-0.35 -> mvp-0.38` on both sides, followed by
  `rebuild-derived-state`.
  - Migration 228 is applied on the branch's copies, and the three new tables are empty.
  - No table lost rows, except arxiv_v2's FTS5 internal `source_block_fts_data`/`_idx` (−87/−86), the same on
    main's copy.
  - Branch and main differ only in `schema_migrations` (+1) and the three new tables. Integrity is ok.
- **`doctor`** is identical to main's: 57/1, 102/48 and 83/47 (issues/errors), all known content errors
  (`layout:missing_directory`, `criterion:unknown_dependency`, `yaml:invalid`).
- **`rebuild --shadow`: 0/0/0** on all three after the upgrade, after *Am I ready?*, and at the end.
- **Curriculum off = main.** `reader.reading_path` (judge off) for every extraction plus `reader.prompt_contract`:
  **5/5, 5/5 and 13/13 byte-identical** to main's code on main's copy.
  - After a deliverable was added on the branch's copy, 2/1/2 of the reading paths differed. That is RW7a's goal card
    showing the new learner goal.
  - With the same `goals.yaml` copied to main's copy, all are **byte-identical again (5/5, 5/5, 13/13)**. The
    difference is the data, not the code.
  - Curriculum on (as the copies have it): the prompt contract is identical to main's.
- **Curriculum on, models unavailable.**
  - `curriculum.deliverables` 0, and `curriculum.guide_slice` is `none` on every reading. Probability's two readings
    whose source reader is off refuse `reader_disabled_for_source`, as RW7a's RPC does on main.
  - `learnloop curriculum report --json` returns rc 0 with empty rows.
  - With a deliverable and a depth, `curriculum.path` shows `failed` / `models_off` with its message. Each call takes
    0.4–1.0 s and there is no hang; `guide_slice` on that deliverable's books shows the same `failed` state.
- **"Am I ready?"** One deliverable per copy was created and resolved in-process with a **fake** resolver: 4/3/3
  needed LOs, 1/0/0 of them demonstrated. Then `curriculum.ready_check` was pressed through the real sidecar.
  - It created 3/3/3 `test_me_later` commitments (`one_check_pending`, `via` `deliverable_ready`), **all for
    undemonstrated LOs and none for a demonstrated one**.
  - 1/3/3 are on items and 2/0/0 are LO-level. **0** are on a withheld item and **0** on a reserved exam item
    (protection readable).
  - Pressing again creates 0. Shadow is 0/0/0 before and after.
- **Receipts.** **0 real `model_call_receipts` rows.** The only new row per copy is the in-process fake resolver's
  (provider `fake_deliverable`). Spend: $0. Nothing under `~/learnloop-vaults`, `~/learnloop-retired` or
  `~/learnloop-books` was opened or listed.

### Owner notes

1. **Kill switches:** `curriculum.enabled` (everything C0b, and C0a's data with it) and `curriculum.coverage_on_extract`
   (the background re-judgment after an extraction completes).
2. **Spend:** the two paid routes (`deliverable_scope_resolver`, `deliverable_path_judge`) share C0a's daily cap,
   `curriculum.max_daily_cost_usd`. On the ChatGPT plan they cost nothing; metered routes are held to that cap.
3. **Where to create a deliverable:** in the Guide, under the path card (*learning this for something?*); *what it
   covers* on the slice opens the same panel.
4. **Upgrade:** `learnloop upgrade --to mvp-0.38` applies 228 (no new tag), then `rebuild-derived-state`.

### Open items

- A Goals-screen panel for deliverables (today the Guide only).
- The slice when `reading_paths.enabled` is off (no path card, so no slice).
- OpenRouter grants are keyed to `curriculum.guide_slice`, not `reader.reading_path` (decision 3).
- DL2's intent gaining a goal scope, so the depth and the deliverable's intent are one setting.
- The path judge's learner context before C1.
- Per-section reading time before C1 (today DL1's estimate).
- The readiness target reuses DL2's governed settings (`intent.recall_targets.keep_in_touch`,
  `capture.test_me_later_days`).
- A goal-creation tombstone (an undone deliverable leaves its goal).
- Migration 227 (RW6b part 1) lands after 228: rebuild its head fixture on main's 228 head.
- `test_codex_tool_lockdown::test_a_workspaces_own_project_layer_never_reaches_the_turn` matches the substring
  `docs` anywhere in a launch override, so it fails when `TMPDIR` sits under a path containing `docs`, such as this
  worktree. This belongs to the lockdown's owner; it is not C0b's.
