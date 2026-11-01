# Reader RW6b part 2: the narrative and the router card (`reader/rw6b-p2-digest-card`, base `2b8b530279`)

> **Codex review fix round:** see `reader-rw6b-p2-digest-card-codex-review.md`. It supersedes this record where they
> differ. The card's Reader activity section is now rendered and hashed (F1). Narratives no longer need follow-ups
> (F2). One durable claim is taken per narration (F3). Open questions 2–4 below are closed. Fix round 3 (final
> verify): the claim's lease outlives the narration's longest request (F3), a figure's LO selects its session (F6),
> and the `as_of` contract is documented (R2).

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
