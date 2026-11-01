# Reader RW6b part 2: the narrative and the router card (`reader/rw6b-p2-digest-card`, base `2b8b530279`)

> **Codex review fix round:** see `reader-rw6b-p2-digest-card-codex-review.md`. It supersedes this record where they
> differ. The card's Reader activity section is now rendered and hashed (F1). Narratives no longer need follow-ups
> (F2). One durable claim is taken per narration (F3). Open questions 2–4 below are closed. Fix round 3 (final
> verify): the claim's lease outlives the narration's longest request (F3), a figure's LO selects its session (F6),
> and the `as_of` contract is documented (R2). **Landed onto main** after curriculum C1 (mvp-0.40): see "Landing onto
> main" at the end (no successor, no migration; rulings R1–R3).

Builds `spec_reader_workbench_v1` §9.2 (with §9.5, §9.6; UX §4.8, W14; G25) on top of part 1 (mvp-0.39,
migration 227): the session narrative and reader activity for the router's learner-state card.

**Spend: $0. No model or paid calls.** Every test uses fakes (`NarrativeFake`, part 1's `FakeSearch` over the real
valuation). No manual run on a vault copy was needed: the narrative's one model call goes through the existing
routed, capped, receipted path (`PaidCalls`), which the fakes exercise end to end, and nothing in this stage needs
a paid command to verify an external interface. No owner vault, `~/learnloop-vaults`, `~/learnloop-retired` or
`~/learnloop-books` was opened. The reference scripts ran under `env -i` with empty, existing `HOME`, `CODEX_HOME`
and `LEARNLOOP_CONFIG_DIR` and `TMPDIR` outside the worktree; they read the tracked fixture and write docs.

**No migration, no successor.** The narrative uses part 1's narrative columns (`narrative_md`,
`cited_event_ids_json`, `model`, `prompt_version`). The card section is outside everything a decision or a stored
card reads (below), so no router decision, plan choice or persisted meaning changes and C1 keeps mvp-0.40.

## What was built, against the spec

| Spec | Where | Notes |
|---|---|---|
| §9.2 the narrative: optional, ≤ 120 words | `instructional/reader_digest.py` | `digest.narrative_enabled` (default on) under `digest.enabled`. `MAX_WORDS = 120` is the spec's structural bound in code, not a key. |
| written by route `reader_digest` from the typed summary only | `build_prompt`, `ai.routing.reader_digest` | The prompt is the digest row's stored `summary_json` (RW6a's `ReaderSessionSummaryV1`: ids, kinds, statuses, verdicts; no learner text), the titles of the LOs and sections the summary names, and the citable ids. Tested: the learner's question and answer text never appear in the prompt. Unset route = the active provider (the ChatGPT plan under T1). |
| citing event ids validated against the summary; invalid → drop, record why | `citable_ids`, `validate_narrative`, `_record` | Citable ids: the inquiries' root exchanges and question events, every Ask exchange, workbench sessions and attempts, formative records' source events, gaps named and their questions, and the claims' attempts. A narrative must cite at least one id, all of them in the summary, keep to 120 words and use none of the well's markers (● ◌ ○). A failing one is dropped. The digest row gets `prompt_version` (so it is never paid again) and `narrative_md` NULL, and a `judgment_ledger` verdict (task `reader_digest_narrative`, judge `verifier`, verdict `kept`/`dropped`, rationale with the reasons, the cited ids and the word count). A kept one is recorded `kept`. |
| labelled "summary written by LearnLoop's model" | `RDG.NARRATIVE_LABEL`, `DigestNarrative.tsx` | Same label on the card, in Wrap up and on the router section. Authority `salience_only` everywhere. |
| generated once per session in the background, routed, capped, receipted | `narrate_digest`, `narrate_waiting`, `NarrativeRoute`; sidecar `prepare_followups` | Runs in part 1's background job (`reader-followups`), after planning, for every digest row whose session ended and has no narrative attempt. `PaidCalls` writes receipts (owner kind `reader_digest`). Metered calls need `digest.price_per_million` and are held to `digest.max_daily_cost_usd` (`SharedDailyEnvelope`); subscription calls are `estimated_only`. "Once": `prompt_version` set marks a session as narrated; the setter writes only `WHERE prompt_version IS NULL` (two writers: the first wins, tested). Transient refusals (plan down, cap reached, no price, provider failure) write nothing and are retried at the next Today build. |
| plan down → no narrative, no OpenRouter offer unless the existing pattern does so | `resolve_client` (pinned) | The job runs in a background thread, where no grant exists (`plan_fallback`: a background thread never sees one), so a plan that is down means `unavailable`, no call and no offer. Tested: the client resolution is asked for the planned plan profile only and no receipt is written. `reader_digest` is registered in `METERED_PRICE_SETTINGS` (`digest.price_per_million`), so a foreground offer would follow the existing rule. |
| shown collapsed in the "Last time here" card and in Wrap up, with W14 states | `handlers/recap.py` → `narrative_view`; `DigestNarrative.tsx` in `RecapCard`, `WrapUpPanel` | States: `landed` (collapsed `▸ summary written by LearnLoop's model from what you did`, opens in the model's voice), `pending`, `failed` (dropped: no retry, one per session), `unreachable` (plan down, no route, no price, provider failure; "The lists above are complete without it."), `capped` (names the cap). Off: the key is absent from both payloads and nothing renders. A session with no digest row (still running, no activity, or not yet planned) shows nothing. |
| never a source of a filled mark, never evidence (tier 1) | contracts, tests | `learnloop.instructional.reader_digest` and `learnloop.daily_plan.router_reader` are added to the import-linter contract that keeps every evidence writer away from the reader summary. The narrative may not contain ● ◌ ○ (backend drop; the frontend also strips them). Rebuild `--shadow` with a narrative present is 0/0/0 and the digest table is unchanged (`test_rebuild_shadow_is_zero_with_a_narrative_present`). |
| the tutor's personalized context may use the latest narrative (§4.6 "Context it starts from") | — | **Not built: the hook does not exist.** The Reader tutor's context (`tutor/reader_modes.py`, `ReaderTutorQAContext.reader_tutor`) has no narrative field. Reported as an open question. |
| §9.2 router card: `reader_activity_for_card(lo_ids, as_of) -> ReaderActivityV1`, a pure read | `daily_plan/router_reader.py` | For the candidates' LOs, from RW6b's digest rows whose sessions touched them (strictly before `as_of`): open inquiries (root question excerpt, age in days, depth, exchange count; dropped once resolved); assisted-only work (facet, highest help level, hints, book, date; dropped once an unassisted success on the facet's Demonstrated curve answers it); pending reader follow-ups (purpose, date, the valuation's numbers and scale); missed predictions; open hypotheses (gaps named, rival explanations with their source rows); formative records; kept comparisons (RW4d's `kept_comparisons_for_card`); candidate actions with where each came from (pending follow-up with its valuation, continue reading where the session stopped, near-transfer practice `find_practice` proposed when nothing cleared the stop), never a choice; the latest narrative, labelled model-written, with its cited ids. Exam-anchored inquiries keep the entry and lose the words (fail closed). Tested pure: identical twice, no table count or `total_changes` moves. |
| added as a reader section of `LearnerStateCardV1`, no decision change | `router/card.py` (`CardInputs.reader_activity`, `LearnerStateCard.reader_activity`), `daily_plan/router_card.py` | The card builder reads it and puts it on the card object only, never in the typed card (`json`), its text, its hash, its token count, its stored payload or its equality. Router models read `card_text`/`card_json` (`router_chooser`, `router/requests.evidence_from_card`), so they read nothing new. Tested: card hash, text, JSON, tokens and payload are byte-identical with and without the section; the staged decision picks the same candidate with the same why; a plan built with the section present stores a card that does not contain it; an unreadable section is logged and never named in the hashed `unknowns`. |
| card switch | `router_reader.reader_activity_enabled` | The spec names `digest.enabled` among RW6b's switches; it is the part's switch here (the narrative and the card section). The section is also absent with `reader_inquiry.enabled` off. |
| kill switches | `DigestConfig` | `digest.narrative_enabled` off: no route call (tested: the fake is never called by narrate, the waiting scan, the RPCs or the queue build), no narrative in any payload, and `prepare_followups` takes part 1's exact path (no job is spawned when nothing else waits). |

### Part 1 changes (small, needed)

- `reader_followups._publish` and `_commit_revaluation` compared the whole digest row to detect a concurrent writer.
  A narrative written meanwhile would have superseded a plan or a re-valuation. Both now compare the row without
  its narrative columns (`RDG.without_narrative`). The narrative setter leaves `updated_at` alone. Tested
  fail-first: a narrative that lands during a re-asked search no longer supersedes the publication.
- `handlers/reader_followups.prepare_followups` keeps part 1's path exactly when the narrative is off. When it is
  on, the same job narrates after planning. A job starts for narration only if a narration could run now (the
  admission check: models off, no route, no price and the cap are read without a network call), so a Today build
  never starts an idle job.

## No made-up constants

- `digest.max_daily_cost_usd` (0.25, keep) is the owner's spending authority for metered narrative calls, like
  every other feature's daily cap. `digest.price_per_million` is unset by default, so a metered route is refused
  before sending. Both are registered `structural`/`operational` in `params/parameter_registry.py`; the two
  switches are registered as kill switches.
- `MAX_WORDS = 120` is the spec's bound. `_CAPS` (3 calls, 2 retries, 80k tokens per narrative) is a runaway
  bound, as in every other `PaidCalls` user. `EXCERPT_CHARS = 140` is the recap's own excerpt length.
- No weight, margin or threshold is added. Nothing is valued.

## Config, snapshots, reference

- `[digest]` (`enabled`, `narrative_enabled`, `price_per_million`, `max_daily_cost_usd`) and
  `ai.routing.reader_digest` are modelled defaults, left out of the decision-only template. All 30
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprints were recomputed with `defaults_fingerprint_for_version` (`.pyc`
  cleared before and after; a recheck found 0 mismatches). mvp-0.9's note describes the section; every other
  version notes it moves too ("is in it too" for mvp-0.39).
- The route is registered in `AITask`, `ROUTE_FOR_OPERATION`, `METERED_PRICE_SETTINGS` and the judge-route
  disclosures (the settings payload lists it; `test_judge_routes.py` updated). `tests/conftest.py` sets
  `LEARNLOOP_DIGEST_MODELS=off`.
- DB/config reference regenerated: `Config - digest.md` is new; 1090 effective leaves in 77 sections (prose counts
  corrected in `Configuration.md` and `Database.md`); `db_validate_reference.py` `errors: []`. The schema did not
  change. Most of the 436 regenerated notes move only by their source commit and line anchors.
- The desktop catalog (`desktop_generate.py`) was not regenerated in this step: CA6b changes the frontend in
  parallel and the landing regenerates it (as the Oct 31 landings did). `DigestNarrative.tsx` is reached from
  `src/main.tsx` through `RecapCard`, so the activation audit test passes.

## Gate (this step; targeted only, per the owner's 2026-10-17 rule)

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, pytest at `-n 6`, vitest at
`--maxWorkers=4`, one run at a time, `TMPDIR` outside the worktree.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` (before and after the contract change; final) | 36 kept, 0 broken |
| `pytest -n 6` over the contract and route-registry files (first pass, 21 files) | 1 failed (`test_judge_routes`: the new route's disclosure, expected; updated), 754 passed, 1 skipped |
| `pytest -n 6 tests/test_judge_routes.py` (after the update) | 25 passed |
| `pytest -n 6` over 169 files (list below) | **2995 passed, 19 skipped, 3 xfailed** (24 min) |
| `pytest -n 6 --durable-sqlite` over the 2 new files + `test_reader_session_digests_migration.py` | 38 passed |
| Mutation checks (temporary edits, reverted with `git checkout`): no citation/word check; no `prompt_version IS NULL` guard; whole-row compare in `_publish` | the new tests fail (4, then 2), then pass again (22) |
| `npm install`, `npm run typecheck` | ok, no errors |
| `npx vitest run --maxWorkers=4` over 11 files (list below) | 62 passed |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed (no new RPC) |
| `db_generate_reference.py`, `db_validate_reference.py` (`env -i`) | 358 table notes; validator `errors: []` after the prose counts |
| durability lane for a migration | not applicable: no migration and no connection code changed |

**The 169 files of the targeted pytest run:** `test_ad1_codex_review_fixes.py`, `test_ad1_migration.py`, `test_ad23_contract.py`, `test_ad23_inversion.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_ad23_t1_routes.py`, `test_ad3_subject_view.py`, `test_approach_maps_schema.py`, `test_architecture.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_card_lineage.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_workspace.py`, `test_cli_help_snapshot.py`, `test_codex_tool_lockdown.py`, `test_cold_retry_reschedule.py`, `test_compare_sources_keep.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_coverage_on_extract.py`, `test_daily_loop_reader_authored_practice.py`, `test_daily_loop_reader_retire.py`, `test_daily_plan_build.py`, `test_daily_plan_reading.py`, `test_decider_landing.py`, `test_deliverable_codex_review.py`, `test_desktop_activation_audit.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_context.py`, `test_diagnosis_history_modes.py`, `test_diagnosis_input_provenance.py`, `test_field_config.py`, `test_field_workbench_signals.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_followups.py`, `test_grading_cli.py`, `test_help_assists_schema.py`, `test_instructional_layering.py`, `test_intent_checks.py`, `test_intent_codex_rereview.py`, `test_intent_codex_review.py`, `test_intent_orchestrator_rulings.py`, `test_judge_routes.py`, `test_kinship_feature.py`, `test_learner_claim_application_migration.py`, `test_learner_claim_superseded_migration.py`, `test_learner_report_superseded.py`, `test_library_asks_migration.py`, `test_library_exercises.py`, `test_lp_claim_fixes.py`, `test_mcp_c1a_landing.py`, `test_mcp_tools.py`, `test_method_explicit_landing.py`, `test_method_explicit_upgrade.py`, `test_migration_coordinator.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_plan_determinism.py`, `test_plan_first_transport_grant_scope.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport_paid_roles.py`, `test_plan_first_transport.py`, `test_plan_first_transport_today_quiet.py`, `test_plan_follows_path.py`, `test_probability_cli.py`, `test_project_cli.py`, `test_provider_resolution_parity.py`, `test_public_tip_guards.py`, `test_reader_ca2_fix_orchestrator.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca4_table_by_point.py`, `test_reader_ca6_side_by_side.py`, `test_reader_digest_narrative.py`, `test_reader_followups.py`, `test_reader_followups_rereview.py`, `test_reader_followups_review.py`, `test_reader_followups_round3.py`, `test_reader_followups_round4.py`, `test_reader_followups_round5.py`, `test_reader_followups_round6.py`, `test_reader_followups_round7.py`, `test_reader_followups_round8.py`, `test_reader_followups_successor.py`, `test_reader_followup_valuation.py`, `test_reader_intent.py`, `test_reader_observation_records.py`, `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_reader_rw2b_review.py`, `test_reader_rw3a_landing.py`, `test_reader_rw3b_migration.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_rw6b_landing.py`, `test_reader_rw7a_migration.py`, `test_reader_session_digests_migration.py`, `test_reader_wrap_up.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_reread_safety_landing.py`, `test_retrieval_spaces_migration.py`, `test_router_card.py`, `test_router_coldness_covariates.py`, `test_router_g1_feasibility.py`, `test_router_g3_propensity.py`, `test_router_g4_restraint.py`, `test_router_g7_fallback.py`, `test_router_ladder_parity.py`, `test_router_offer_log.py`, `test_router_outcomes.py`, `test_router_p2_bridge.py`, `test_router_presentations.py`, `test_router_probe_ties.py`, `test_router_r1_composition.py`, `test_router_r2a_landing.py`, `test_router_r2a_serving.py`, `test_router_r2b_agreement.py`, `test_router_r2bc_landing.py`, `test_router_r2b_requests.py`, `test_router_r2b_serving.py`, `test_router_r2c_retrieval.py`, `test_router_r2c_teach_back.py`, `test_router_reader_activity.py`, `test_router_staged_p2.py`, `test_router_why_copy.py`, `test_rw2c_switch_off.py`, `test_rw2d_receipts_migration.py`, `test_rw7b_codex_review_fixes.py`, `test_section_coverage_migration.py`, `test_section_coverage_rpcs.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_shadow_rebuild.py`, `test_sidecar_serializer_snapshot.py`, `test_source_roles.py`, `test_sqlite_file_copies.py`, `test_t1_batch_origin_migration.py`, `test_table_roles.py`, `test_teacher_te0_confidence_events.py`, `test_teacher_te0_fix_round2.py`, `test_teacher_te0_review_fixes.py`, `test_tier1_decider.py`, `test_tracked_fixture_databases.py`, `test_ux_phase2_shell.py`.

Why these: the two new files; `test_judge_routes.py` (changed); every file that names the router card or its
builder, the reader follow-ups / digests / recap / wrap-up modules and RPCs, the defaults snapshots, the parameter
registry, plan fallback, disclosures or the route table (`git grep`); every `test_router_*.py`; the Today builds
after reader activity (`prepare_followups` runs in every queue build); and the contracts (config refactor, CLI help
snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, coordinated
migrations, migration coordinator, tracked fixture databases, public-tip guards, SQLite copies, desktop activation
audit, Codex tool lockdown, instructional layering, shadow rebuild).

**The 11 vitest files:** `screens/reader/DigestNarrative.test.tsx` (new), `RecapCard.test.tsx`, `WrapUp.test.tsx`,
`ComingUp.test.tsx`, `recapReview.test.tsx`, `recapSwitchOff.test.tsx`, `recapCopyBasis.test.ts`,
`modelActionStates.test.tsx`, `screens/ReaderScreen.recap.test.tsx`, `ReaderScreen.recapReview.test.tsx`,
`ReaderScreen.parity.test.tsx`.

Fail-first: the stage wrote the implementation before the tests, so fail-first is shown by mutation instead
(above): removing each guarded behaviour makes its test fail.

## Open questions

1. **The tutor's narrative context (§4.6).** The Reader tutor has no hook for a personalized narrative today, so
   it was not built. A later stage can add the latest narrative of the source, labelled model-written, to
   `ReaderTutorQAContext.reader_tutor` when `personalized` is on (a prompt change: its own prompt version).
2. **Narratives need part 1's digest row.** A narrative is written only for sessions RW6b part 1 planned (it
   writes the row at the first Today build after a session with activity ends). With `followups.enabled` off, or
   below mvp-0.39, there is no row and so no narrative. Creating a row from the narrative side would mean writing
   a part 1 receipt with no plan; the alternative is a narrative-only status, which needs a migration (next free
   229).
3. **Rendering the section for router models (R2).** Moving `ReaderActivityV1` into the hashed card (a "Reader
   activity" text section) changes what the router models read, so it needs its own successor (after C1's
   mvp-0.40) with plan parity under `digest.enabled = false`. Until then it rides on the card object only.
4. **The narrative and `as_of`.** The narrative columns carry no timestamp, so the card section can show a
   narrative written after `as_of` (its row was created before). Harmless while nothing reads the section; R2
   would want the narrative's time (a column, or the ledger verdict's `created_at`).
5. **Card build cost.** At each block boundary the section reads the digest rows, the Ask history of the
   extractions with relevant open inquiries and, for claims, the facets' Demonstrated curves. All are bounded by
   RW6b's digests on the candidate LOs, but the curves are the heaviest read; R2 can cache per plan if needed.

## Landing onto main

Main was `58e78a1d07` (curriculum C1, successor mvp-0.40, no migration, on top of `2b8b530279`). The branch was
prepared for a fast-forward; the orchestrator does the ff and the push. **RW6b part 2 still has no successor and no
migration**: the router card change rides on ruling R1. Spend: $0 (fakes only; the smoke's routes are at the
`127.0.0.1:9` blackhole).

### The merge (`6df601ebac`, a merge, no rebase)

- **`config/template.py`** was the only source conflict (31 snapshot blocks). Both sides' notes are kept in every
  defaults snapshot (RW6b part 2's `[digest]` + `ai.routing.reader_digest` note and C1's `plan_uses_path` note), and
  RW6b part 2's note is added to C1's new mvp-0.40 snapshot ("are in it too"). All **31 fingerprints were recomputed**
  with `defaults_fingerprint_for_version` after clearing every `.pyc` (under `env -i`; a second pass recomputed 0, so
  the values are stable). The digest keys are in the mvp-0.40 snapshot (its fingerprint moved with them).
- **The parameter registry** merged cleanly (C1's `curriculum.plan_uses_path` rule beside the digest rules).
- **`daily_plan/engine.py`** merged cleanly: the branch never touched it. Part 1's fixes to `_publish` and
  `_commit_revaluation` live in `instructional/reader_followups.py` (both compare rows through
  `RDG.without_narrative`), which main did not change; they are intact.
- **The generated references** (438 notes in conflict): main's side taken, then regenerated with
  `db_generate_reference.py` (**1091 effective leaves in 77 sections**: main's 1086 plus the five digest leaves; 358
  table notes). The prose counts in `Configuration.md` and `Database.md` moved from 1086/76 to 1091/77.
  `db_validate_reference.py`: **errors []**. `validate_vault.py`: passes (1362 notes, 1360/1360 reachable).
- **The desktop catalog** regenerated with `desktop_generate.py`: one new TypeScript file, `DigestNarrative.tsx`,
  classified **ACTIVE, entry-reachable build graph** (`ReaderScreen` → `RecapCard`/`WrapUpPanel` →
  `DigestNarrative`, from `src/main.tsx`). `desktop_validate.py`'s review counts moved to **294** TypeScript/TSX
  files, **286** entry-build and **ACTIVE 299**; it passes byte for byte.

### Interactions with C1 (`tests/test_reader_rw6b_p2_landing.py`, `317185da34`)

- **(i) The narrative job after a C1 plan.** A C1 vault (deliverable judged across two books) with an ended reader
  session's digest row waiting for its narrative. One Today build through the sidecar: the plan's receipt is
  `reading_path_plan_v2`, chosen by the deliverable (`ch_det`), and the background job narrates the session once. A
  second Today build (the narrative now written) chooses the same reading with the same receipt.
  **The memo:** `_remembered_fresh_reading` computes once and then remembers; the narrative's write (a committed DB
  write) makes exactly one miss, whose recomputation is the same reading and receipt; with nothing written since,
  it remembers again. So the narrative invalidates C1's memo once and harmlessly: no reading moves.
- **(ii) The router card on a C1 plan.** The block decision on the day's C1 plan (receipt v2, chosen by the
  deliverable): a session narrated an hour before on the block's candidate LOs adds the card's "Reader activity"
  section, and only it (the card's typed JSON without that section equals the plain card's). With
  `digest.enabled = false` the card is the plain card byte for byte: payload, `card_hash` and text.
- **(iii) The claims.** C1's deliverable judgments coalesce in process (`handlers/deliverables._claim_path`) and
  take no `judgment_work_claims` row; the claims C1's path relies on are RW7b's reading-path claims
  (`reading_path_judge:<extraction>:<depth>:<state>`). The narration's key (`reader_digest_narrative:<digest>`) and
  task are distinct from them. While the narration holds its claim (with its long lease and heartbeat), every other
  claim row is unchanged, a reading-path claim is taken and released beside it, the narration still holds its own
  lease afterwards, and a C1 Today build runs; that build's own narration finds the claim held and sends nothing.

### Gate (tree `317185da34`)

Every command ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR`
outside the worktree, after `uv sync --extra dev --extra mobile` (+ `pypdfium2`).

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…` | **23068 passed, 89 skipped, 47 xfailed, 0 failed** in 36 min 50 s |
| Durability: `pytest -m durability -n 6` (5G scope, under the flock) | **177 passed, 1 skipped** |
| Owner lane: `LEARNLOOP_OWNER_VAULTS=fixtures-local/landing-rw6b2/owner-lane` (fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/*` via `learnloop.db.copies.copy_tree_with_databases`), `pytest -m owner_vaults -n 6` (5G, under the flock) | **83 passed, 2 failed, 4 skipped**, as expected. The 2 are the known ones (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies[arxiv_v2]`); each rerun alone 3 times: fails every time, deterministically, as on main |
| Frontend (5G scope): `npm install`, `npm run typecheck`, the whole vitest at `--maxWorkers=4`, `npm run frontend:build` | install ok; typecheck ok; **244 files, 2272 passed**; built (the usual chunk-size warning only) |
| `cargo check` | not run: nothing under `src-tauri` differs from main |
| DB/config reference, desktop catalog, vault | `db_validate_reference` errors []; `desktop_validate` passes byte for byte; `validate_vault` passes |

No single test failed in the full suite, durability or vitest, so there was nothing to rerun there.

### Smoke on fresh copies (`fixtures-local/landing-rw6b2/`, drivers `scripts/smoke.sh`, `scripts/session_only.sh`)

**Setup.**
- Fresh backup-API copies (`copy_tree_with_databases`) of the three mvp035 owner copies (`linear_algebra`,
  `probability`, `arxiv_v2`), neutralized (`neutralize3.py`, run under each side's own code so each config names only
  its own routes: every route at the `127.0.0.1:9` blackhole, its key variable unset; rewrite, rerank, dense and
  embeddings off).
- Main's code is `git archive 58e78a1d07` (src, migrations); the branch's is `git archive 317185da34`.
- Each copy: bare `upgrade` (**mvp-0.35 -> mvp-0.40**, migrations to head 228), the desktop start (primary load),
  `rebuild-derived-state`.
- Every process ran under `env -i` with empty `HOME`, `CODEX_HOME` and config dir; an audit hook logged every process
  start and refused non-loopback sockets.

**Results.**
- **Today and the daily plan, branch vs main: identical byte for byte** on all three copies (Today 525,266, 740,827
  and 344,204 bytes; the plan dump, with every router decision and its stored card payload, 84,705, 124,030 and
  32,442 bytes). The copies have no reader activity on the block's candidates at the plan's time, so the card has no
  "Reader activity" section (0 occurrences in the branch's plans), and the card is main's.
- **`digest.enabled = false` and `digest.narrative_enabled = false`: each identical byte for byte to main's** Today
  and plan, on all three copies.
- **`rebuild --shadow`: 0/0/0** on all three branch copies (live database unchanged), and again after each session
  run below.
- **One ended reader session through product RPCs** on each copy (`reader.log_activity` open, `workbench.open` on
  an item with the book open, `workbench.save_step`, `reader.log_activity` close), then the desktop's Today build
  (`get_today_queue`) a day later, the background job joined, and `reader.recap` in the same process:
  - Part 1 wrote the session's digest row (activity true; `incomplete`: its valuation could not finish with every
    route at the blackhole), the recap's card is that session, and **no narrative and no `prompt_version` were written**.
  - **Default config (no `digest.price_per_million`, a metered blackhole route):** the narration is refused before
    any call; no claim, no request. The recap shows `unreachable` with "A metered narrative route needs
    digest.price_per_million." **0 new receipts.**
  - **Priced, key unset:** the claim is taken and released; client resolution fails before any request
    ("Environment variable LL_LANDING_NO_KEY is required."), and the recap shows `unreachable` with that message.
    **0 new receipts.**
  - **Priced, with a dummy key, so the request really goes to `127.0.0.1:9`:** 3 attempts (the call and its 2
    retries), each refused by the blackhole (3 loopback connects per copy, the only sockets in the audit log), nothing
    published; the recap shows `unreachable` with "AIProviderUnavailable: Connection error.", retried at the next
    Today build. This variant writes **6 `failed` receipt rows per copy, all `reader_digest`, cost null** (each
    attempt's logical and physical receipt), as every receipted route does for a failed attempt.
- **Receipts:** across the 33 smoke databases compared with their base copies, the only new `model_call_receipts`
  are the 18 `failed` rows of the dummy-key variant above. Every other run (Today, plans, both switches, the default
  and key-unset sessions) added **0**; probability's 56 historical rows are unchanged in each copy.
- The audit log has no non-loopback connection and no Codex process start.

### Rulings (verbatim)

> - R1 (F1 deviation accepted): reader activity now reaches the hashed router card the router models read. With digest.enabled off it is byte-identical. That goes beyond my launch brief ("must not change any router decision"), but it is what spec §9.2 and §9.6 describe, and it follows TE0's precedent: router input changes without a successor, and router decisions are serving-time and not persisted meaning. Accepted without a successor; flagged to the owner.
> - R2 (F5 ruled Low): no production caller reconstructs historical cards. as_of bounds event-timed rows; digest summaries are the latest version. Document that contract on reader_activity_for_card. Do not add digest versioning. Keep it as an open item for R2, the router rendering the section.

> ORCHESTRATOR RULING R3 on F3: ruled Low.
> - While the holder process is alive, its heartbeat renews the lease, so no successor can take over. Round 3 proved that, and the renew-before-send fence means a lost claim never sends or publishes.
> - A takeover therefore needs the holder's heartbeat to have stopped, which in practice means the process died or froze. Its request can then never publish (fenced), and the worst case is one duplicate narrative charge on a metered route. That is bounded by digest.max_daily_cost_usd and occurs only on a crash during a slow request. The default plan route is unmetered.
> - An abortable total transport deadline is an open item for the AI transport layer, not this stage.
> Add one sentence to the comment at the claim saying this.

### Owner notes

- **The narrative is on by default** (`digest.narrative_enabled = true` under `digest.enabled = true`) and goes on
  the plan route (`ai.routing.reader_digest` unset = the active provider; the ChatGPT plan under T1). One short
  summary per reader session with activity, written in the background at the next Today build, from the session's
  typed summary only (never your words), labelled "summary written by LearnLoop's model", collapsed in "Last time
  here" and Wrap up. With the plan down or signed out nothing is sent and the card says the model could not be
  reached; the lists are complete without it.
- **The router models now see reader activity** (R1, flagged to you): the card's "Reader activity" section (open
  questions, assisted-only work, pending checks, missed predictions, open hypotheses, formative records, kept
  comparisons, possible next actions, the narrative) is in the hashed card the router models read. It is routing
  only, never evidence. `digest.enabled = false` restores the predecessor's card byte for byte. If you want it
  behind a successor instead, it would be mvp-0.41.
- **`digest.max_daily_cost_usd` (0.25) matters only on a metered route with `digest.price_per_million` set.** Unset
  (the default), a metered route is refused before sending ("A metered narrative route needs
  digest.price_per_million"); the plan route is unmetered.
- No upgrade step: no successor and no migration. The desktop picks it up on restart.

### Open items

1. **R3: a total transport deadline.** The request timeout is per network operation, so a narrator that freezes or
   dies mid-request can be taken over while its response still arrives; it never publishes, and on a metered route
   the worst case is one duplicate charge within `digest.max_daily_cost_usd`. An abortable total deadline belongs to
   the AI transport layer.
2. **R2: historical card reconstruction.** `reader_activity_for_card(as_of)` bounds event-timed rows; a digest row's
   summary and valuation are its latest version (documented on the function). Digest versions would be needed only
   if router R2 (rendering, replay) ever rebuilds past cards.
3. **The tutor's narrative hook (§4.6).** The Reader tutor has no field for the latest narrative; adding it is a
   prompt change with its own prompt version.
4. **Narratives below mvp-0.39 or with follow-ups off.** Closed by the Codex review's F2: with `followups.enabled` off, or below
   mvp-0.39, the narration writes its own summary-only digest row (`incomplete`, `valuation_json.not_planned`), so
   those sessions are narrated with no migration. What remains is cosmetic: the row reuses part 1's `incomplete`
   status; a dedicated narrative-only status would need migration 229.
