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
