# Plan-first transport T1: review fixes

Branch `ai/plan-first-transport` (worktree `learnanything-plan`). The review came from the stage
script's Opus fallback, because Codex is out of quota until 2026-10-27. It reported nine findings:
one High, three Medium, five Low. All nine were reproduced on the pre-fix tip `9753f38ce` and fixed.
None was rejected. No migration, no live or paid call, no sign-in, and no run on any vault copy.

## Review

### Reproduction on the pre-fix source

The pre-fix tree (`git archive 9753f38ce src`) was run from the scratchpad under `env -i` with an
empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR. The OpenRouter key was fake, the plan route was set
to `127.0.0.1:9`, and `tests.openai_fakes` was installed (zero requests recorded). Results:

| Finding | Pre-fix behaviour observed |
|---|---|
| F1 | `fallback_provider = "openrouter"` with the plan signed out: `grading`, `tutor_qa`, `diagnosis` and `hint_writer` all resolved to `openrouter`, `ready=True`, `fallback_available=None`. They did the same inside `quiet()`. `writer_names` returned `['chatgpt', 'openrouter']` |
| F2 | `hint_writer` was offered OpenRouter while `hints.price_per_million` was `None`, the setting that refuses the call before sending |
| F3 | The build route was `chatgpt_medium`, `ready=False`, with no hint. After `grant(["canonical_ingest"])` it was still `ready=False` |
| F4 | `LEARNLOOP_AI_FALLBACK=openrouter` with no CLI context: `grading` went to `openrouter` |
| F5 | `routing.canonical_ingest = "codex"` and `routing.authoring = "codex"` were rewritten to `chatgpt` (low effort), not `chatgpt_medium` |
| F6 | With the opt-in and `fallback_provider = "codex"`, `writer_names` returned `['chatgpt', 'codex']` |
| F7 | The client had no explicit-inline notion, so an oversized export with an explicit inline was served in tools mode (this was the old Q6) |
| F8 | Only `SidecarError` carried the offer (`server.py`); a job's offer was relayed on every read |
| F9 | `available_grading_providers` always added `codex`; the `ai latency` and `ai compare` help used Codex examples |

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A configured metered `fallback_provider` served unavailable plan routes without asking | fixed | `eb3be2bfb`, `4c89b615f`, `fac2e7343` | `test_plan_first_transport.py::test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`; `test_chatgpt_plan_provider.py::test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back` (now asks, and a grant serves); `test_method_phrasing_report.py::test_t1_a_plan_writer_never_falls_back_silently_to_a_metered_writer` |
| F2 | Medium | Offers were made for features that refuse an unpriced metered route, or that need the plan's workspace | fixed | `eb3be2bfb`, `4c89b615f` | `test_f2_openrouter_is_offered_only_when_the_feature_could_use_it`; `test_every_task_under_code_defaults_resolves_tool_free_and_never_codex` (blocked tasks make no offer and say why) |
| F3 | Medium | The add-source build never asked, and a grant could not unblock or price it | fixed | `eb3be2bfb`, `4c89b615f` | `test_f3_the_question_build_asks_and_a_grant_serves_it_priced_as_metered` |
| F4 | Medium | Grants were process-wide: the env variable applied to every host, grants survived a vault switch, and one click granted every offered task | fixed | `eb3be2bfb`, `4c89b615f` | `test_f4_grants_are_per_vault_per_offer_and_the_env_grant_is_the_cli_commands_only`; `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice` (`not_offered`); `PlanFallbackOffer.test.tsx` ("answers only the feature that asked last") |
| F5 | Low | `doctor --fix` moved a legacy `routing.<task> = "codex"` down a tier | fixed | `eb3be2bfb`, `4c89b615f` | `test_f5_doctor_fix_keeps_the_tier_of_a_legacy_codex_route_value` |
| F6 | Low | Codex could still be the fallback, through the build route and the method-phrasing writer | fixed | `eb3be2bfb`, `4c89b615f` | `test_f6_codex_is_never_a_fallback_through_the_direct_readers_opt_in_or_not` |
| F7 | Low | An explicit `workspace_mode = "inline"` was overridden, and a tools turn's resent input was unbounded | fixed | `eb3be2bfb`, `4c89b615f`, `fac2e7343` | `test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input`; `test_chatgpt_plan_workspace.py::test_inline_mode_serves_a_workspace_over_its_budget_in_tools_mode` |
| F8 | Low | Errors other than `SidecarError` lost the offer, the banner came back on every read, and there was no revoke | fixed | `eb3be2bfb`, `4c89b615f` | `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`; `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done` (relayed once); `PlanFallbackOffer.test.tsx` ("Stop using OpenRouter") |
| F9 | Low | Hard-coded Codex examples pointed at refused paths | fixed | `eb3be2bfb`, `fac2e7343`, `5e7822bbd`, this record's commit | `test_f9_refused_codex_profiles_are_not_offered_as_grading_providers`; `test_sidecar_contract.py` grading-provider tests; CLI help snapshot re-recorded (`ai latency` and `ai compare` only) |

### What changed

- **F1, F6: one rule for `ai.fallback_provider`** (`routing.configured_fallback`). It is never the
  primary itself and never an agent-harness profile, opt-in or not. When the primary is a plan
  profile, only `manual` or another plan profile is used as configured. A metered profile is reached
  only through the plan's offer and a grant. `fallback_provider_for`, `authoring_route_for` and both
  method-phrasing readers (`writer_names`, `_ready_writer`) use this rule. `learnloop doctor`
  reports a metered setting as `ai:plan_metered_fallback`. A non-plan primary keeps the owner's
  fallback as written.
- **F2: `plan_fallback.offer_blocker`.** Some tasks are refused before sending until their price
  setting is set. They are listed in `METERED_PRICE_SETTINGS`: hints, approach maps, outcome
  placement, the workbench check, figures, the AD LLM routes, the `source_retrieval`/`source_service`
  listwise and judge routes, and `practice_rerank`. `practice_rerank` was added in this step; its
  setting is `practice_index.rerank_price_per_million`. These tasks are offered OpenRouter only once
  the setting is set. A snapshot diagnosis needs a workspace that only the plan serves, so it is not
  offered either. In both cases the unavailable message says why, and a later availability failure
  on that route makes no offer.
- **F3: `authoring_route_for` resolves through `ready_client_for_task("canonical_ingest")`.** The
  build now raises the offer, and a grant routes the build to OpenRouter. The route names the
  profile that actually serves, so `decide_cost` and the consent key treat a granted build as
  metered (`subscription=False`). The build's own clients already resolve through the same path.
- **F4: grant scope.**
  - `LEARNLOOP_AI_FALLBACK` is read only by the CLI's entry callback (`command_grant`, a
    ContextVar). `learnloop mcp serve` is a long-lived host and takes no grant. The sidecar and the
    mobile host never call `command_grant`. A thread started in a fresh `Context()` does not
    inherit the grant.
  - Session grants are keyed by vault root. A vault switch in `SidecarContext.load` clears them.
  - `ai_use_fallback` grants only tasks that this vault was offered; the sidecar records each hint
    as it is sent. Anything else returns `not_offered` with `offered_tasks`.
  - The desktop banner answers only the feature that asked last; it no longer merges offers from
    different features.
  - In this step the RPC was also changed to report "OpenRouter isn't set up" before it checks
    which tasks were offered.
- **F5: `routing.<task> = "codex"`** now maps through `LEGACY_CODEX_TASK_ROUTES[task]` and then
  `CODEX_TO_PLAN_PROFILE`. Ingest, authoring and animation map to `chatgpt_medium`. A task outside
  that table maps to `chatgpt`.
- **F7: explicit inline.** `inline_explicit` is set only when the owner wrote `workspace_mode`
  (pydantic `model_fields_set`). The code default and the template, where the line is commented
  out, do not set it. An explicit inline refuses an oversized export, and no `tools` key is sent.
  The unwritten default still overflows to tools mode. A tools turn's resent input is capped at
  `TURN_INPUT_FACTOR` (4) × `max_workspace_chars`. Once a round crosses the cap, the next round
  tells the model to answer now, and a further call is invalid output. This adds no config key.
- **F8: offers on every error path.**
  - An error that is not a `SidecarError` keeps the offer in its `internal` error's details, and
    the offer is recorded for granting.
  - A job's offer is relayed once (`relay_job_offer`), and so is a failed reading path's offer
    (`offers.pop`).
  - The banner's chosen state has a "Stop using OpenRouter" button (`ai_use_fallback` with
    `stop: true`), which revokes this vault's grants.
- **F9: Codex examples removed.**
  - Codex profiles and the legacy `codex` name are listed as grading options only with the opt-in.
  - The `ai latency` and `ai compare` help no longer uses Codex as the example; it notes the opt-in.
  - The stage record's owner commands say that `ai compare --profiles codex,chatgpt` needs
    `ai.agent_harness_opt_in` on the copy.
  - In the stage record, Q2, Q3 and Q6 are updated to match.

### Claims in the stage record, corrected

- "Only a grant routes to OpenRouter": this now holds for a configured `fallback_provider` as well
  (F1). The env grant holds only for one CLI command (F4).
- "A grant never serves background work": a configured fallback no longer reaches quiet startup
  maintenance (F1). The env grant no longer reaches long-lived hosts or fresh-context threads (F4).
- "Codex is never a fallback, opt-in or not": this now holds for the direct readers too (F6).
- "`doctor --fix` rewrites to the same tier": this now holds for the legacy `"codex"` value (F5).

### Open questions (defaults in force)

| # | Question | Default |
|---|---|---|
| R1 | Some features hold metered calls to a price that is not tied to a single task, so `offer_blocker` does not cover them. Examples: learner-text gaps (`learner_text_gaps.metered_price_per_million`, which falls back to known model prices) and the reader passage check (`reader_inquiry.metered_price_per_million` on the shared `canonical_ingest` route). An offer there may still be refused | offered; the feature's own refusal message names the setting |
| R2 | Ingest consent recorded under "codex" does not carry over to "chatgpt" (noted in the review's conformance table), so builds ask for consent once more | ask again (consent is per provider family) |
| R3 | After "OK" on the chosen banner, there is no revoke control until the next offer appears. Grants end with the session or a vault switch | kept |

## Gate (fix step, 2026-10-23; targeted only, owner rule 2026-10-17)

Every pytest/vitest/npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G -- ...`, with pytest at `-n 6` at most, vitest at `--maxWorkers=4`, one run at a
time, and `TMPDIR=fixtures-local/tmp`. No full suite, no whole durability lane and no whole vitest
run. `/tmp/learnloop-fullsuite.lock` was present throughout; targeted runs need no lock, and nothing
of the other run was touched.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 30 kept, 0 broken |
| Batch 1 (22 files, listed below) | 654 passed (first run: 6 failed, all pinning the pre-fix behaviour; moved in `fac2e7343`) |
| Batch 2 (20 files) | 481 passed, 1 failed (`test_cli_help_snapshot`: `ai latency` help, F9). After re-recording: `test_cli_help_snapshot` + `test_plan_first_transport` 48 passed |
| Batch 3 (19 files) | 231 passed, 1 skipped |
| After the `ai compare` help edit: `test_cli_help_snapshot.py`, `test_ai_compare.py` | 32 passed |
| `tests/test_plan_first_transport.py` alone (final) | 47 passed (38 before, plus 9 new) |
| `npm install`; `npm run typecheck` | ok; exit 0 |
| `npx vitest run --maxWorkers=4 src/components/PlanFallbackOffer.test.tsx` | 1 file, 6 passed |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed in this step |
| `db_generate_reference.py`, then `db_validate_reference.py` | regenerated (1006 configuration leaves in 69 sections, schema head 217; only source lines, commit stamps and cited consumers moved: the `ChatGPTPlanProviderConfig` docstring and `plan_fallback.py` naming the price settings); `"errors": []` |
| Durability tests | none due (no migration, no DB or connection code) |

Test files run:

- Batch 1: `test_plan_first_transport`, `test_chatgpt_plan_provider`, `test_chatgpt_plan_workspace`,
  `test_chatgpt_plan_sidecar`, `test_chatgpt_plan_cli`, `test_chatgpt_plan_landing`,
  `test_chatgpt_plan_signin`, `test_config_refactor`, `test_embedding_route_isolation`,
  `test_family_proposals`, `test_ingest_runner`, `test_judge_routes`, `test_method_phrasing_report`,
  `test_openai_embedding_client`, `test_provider_resolution_parity`, `test_settings_store`,
  `test_sidecar_contract`, `test_sidecar_transport`, `test_doctor`, `test_codex_isolation_mcp_check`,
  `test_exam_protection_identity`, `test_ai_config`.
- Batch 2: `test_decider_landing`, `test_exam_protection_landing`, `test_question_promotion_jobs`,
  `test_ux_phase1_connect_ai`, `test_ux_phase1_landing`, `test_ux_phase1_review_fixes`,
  `test_mobile_allowlist`, `test_architecture`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`,
  `test_sidecar_serializer_snapshot`, `test_reading_paths`, `test_library_ask`,
  `test_library_ask_review`, `test_reader_rw3b_review_fixes`, `test_reader_rw3b_fix_round4`,
  `test_reader_rw3b_fix_round5`, `test_sqlite_file_copies`, `test_tracked_fixture_databases`,
  `test_coordinated_migrations`.
- Batch 3: `test_hint_service`, `test_hint_h2a_review`, `test_hint_h2a_review_round2`,
  `test_hint_h2a_review_round3`, `test_hint_kill_switch`, `test_hint_outcome`,
  `test_hint_h2b_review`, `test_hint_h2b_rereview`, `test_hint_h2b_fix3`, `test_hint_h2b_fix4`,
  `test_workbench_hint_service`, `test_workbench_assistance`, `test_approach_map_replay`,
  `test_reader_cue_holdout`, `test_reader_try_first`, `test_rw4d_rw3b_composition`,
  `test_reader_rw3b_protection`, `test_ai_compare`, `test_compare_keep_switch_off`.

The batches were chosen by `git grep` for the changed modules and functions: `plan_fallback`,
`authoring_route_for`, `writer_names`, `available_grading_providers`, `plan_transport`,
`ai_use_fallback`, `fallback_provider`, the four job handlers and `server`. They also cover the
contract pins.

**Process notes.**
- No live or paid call, no sign-in and no vault copy. No tracked fixture vault was opened, and
  `git stash` was not used.
- The reproduction, the CLI help snapshot write and the reference scripts all ran under `env -i`,
  with an empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR.
- Exception: one early edit script in this step ran with plain `python3`, without `env -i`. It
  edited `tests/test_plan_first_transport.py` and `handlers/chatgpt_plan.py` and imported only
  `pathlib`: no LearnLoop module, no network, no credential read.

**Commits** (on top of the stage record `9753f38ce`):

- `eb3be2bfb` T1 review fixes (WIP, from the session before the restart): code for F1 to F9.
- `4c89b615f` Tests for F1 to F9; `practice_rerank` joins the offer blockers; the order of the
  `ai_use_fallback` checks.
- `fac2e7343` Existing tests follow F1, F7 and F9.
- `5e7822bbd` CLI help snapshot (`ai latency`).
- This record's commit: `ai compare` help text (F9) and its snapshot, the regenerated references,
  and the stage record's Q2/Q3/Q6 and owner-command note.

## Re-review (2026-10-23)

The re-review (the stage script's Opus fallback; Codex is out of quota until 2026-10-27) confirmed
F1 [High] fixed and F2 to F9 checked out, and reopened for three new findings: one Medium, two Low.
Each was reproduced with a test that failed on `d20b33c5f` and passes on the fix. None was
rejected. No migration, no config key added, no live or paid call, no sign-in, no vault copy.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| RR-F1 | Medium | Every vault load raised the "Use OpenRouter instead" banner: `get_ai_connection` (and `connect_ai`'s readiness check) resolved the build's route without `quiet()` | fixed | `0142c7ef9` | `test_plan_first_transport.py::test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build` (failed before: `fallbackAvailable` was on the `get_ai_connection` result) |
| RR-F2 | Low | A `canonical_ingest` grant reached the paid passage checks and exercise imports, which refuse an unpriced metered route by their own setting; their offer could never be honoured | fixed | `0142c7ef9` | `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant` (failed before: no per-feature resolver) |
| RR-F3 | Low | "Stop using OpenRouter" was shown only right after granting | fixed | `0142c7ef9` | `test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop`; `ChatGPTPlanSettings.test.tsx` ("keeps Stop using OpenRouter in Settings while the session has a grant", failed before) |

### What changed

- **RR-F1.** `plan_fallback.quiet(honour_grants=True)` is a status read: it makes no offer, but a
  session grant still shows as the route that serves. `first_run._status_route` resolves the
  build's route this way for `get_ai_connection` and for `connect_ai`'s readiness check (the
  `"current"` branch and the payload it returns). The build itself (`add_source`'s job,
  `default_authoring_route`) still resolves without it and asks. Plain `quiet()` (startup
  maintenance, the health line) is unchanged: no offer and no grant.
- **RR-F2.** `plan_fallback.priced_by(*settings)` names the price settings of the feature that is
  resolving a route. `offer_blocker` checks them as well as the task's own setting. While one is
  unset, the route makes no offer and honours no grant (the blocker is checked before the grant),
  and the unavailable message names the setting. `jobs._paid_quick_check_client` resolves the
  inquiry and selection passage checks under `reader_inquiry.metered_price_per_million` (new
  constant `RQC.PASSAGE_CHECK_PRICE_SETTING`). `jobs._exercise_import_client` resolves both exercise
  imports under `source_service.llm_price_per_million`. Once the setting is set, a grant serves
  them as an ordinary metered request under their own caps. The section quick check is not
  admitted at a price, so it is unchanged. This closes open question R1 for these two features.
  Learner-text gaps still fall back to known model prices, as R1 said.
- **RR-F3.** `chatgpt_plan_status` (and the Settings payload's `chatgptPlan`) now carries
  `openrouterGrantedTasks`, the session's grants on the open vault. Settings → ChatGPT plan shows an
  "OpenRouter" row with "Stop using OpenRouter" while any grant exists. The banner's chosen state
  says where to find it. A vault switch or a sidecar restart still clears grants. This closes open
  question R3.

Residual (not a finding): under `quiet(honour_grants=True)` the unavailable message still ends with
the routing layer's offer sentence. The connection sheet may show it with no banner beside it;
the banner appears when the build itself runs. Left as is, so the health line's runtime payload
stays as the earlier fix left it.

### Gate (re-review fix step, 2026-10-23; targeted only, owner rule 2026-10-17)

Every pytest/vitest/npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G -- ...`, with pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time, and
`TMPDIR=fixtures-local/tmp`. There was no full suite, no whole durability lane and no whole vitest
run. `/tmp/learnloop-fullsuite.lock` was present: an empty file dated 2026-10-13. Targeted runs need
no lock, and nothing else was touched.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 30 kept, 0 broken |
| The three new tests before the fix | 3 failed |
| The three new tests after the fix | 3 passed |
| Batch A (20 files, listed below) | 676 passed |
| Batch B (29 files, listed below) | 538 passed |
| `npm install`; `npm run typecheck` | ok; exit 0 |
| `npx vitest run --maxWorkers=4` on `ChatGPTPlanSettings.test.tsx` before the component change | 1 failed, 8 passed |
| `npx vitest run --maxWorkers=4` on `ChatGPTPlanSettings.test.tsx`, `PlanFallbackOffer.test.tsx`, `copy/denyList.test.tsx`, `ConnectAI.test.tsx` | 4 files, 78 passed |
| `npm run frontend:build` | built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_validate_reference.py` | first run: errors, because source lines cited from `plan_fallback.py` had moved. Ran `db_generate_reference.py` (1006 configuration leaves; only source lines, commit stamps and cited consumers moved), then validated again: `"errors": []` |
| Durability tests | none due (no migration, no DB or connection code) |

Test files run:

- Batch A: `test_plan_first_transport`, `test_chatgpt_plan_provider`, `test_chatgpt_plan_sidecar`,
  `test_chatgpt_plan_workspace`, `test_method_phrasing_report`, `test_daily_loop_start_minutes`,
  `test_decider_landing`, `test_exam_protection_identity`, `test_mobile_allowlist`,
  `test_ux_phase1_auto_build`, `test_ux_phase1_connect_ai`, `test_ux_phase1_usability_round2`,
  `test_ux_phase1_landing`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`,
  `test_sidecar_contract`, `test_architecture`, `test_coordinated_migrations`,
  `test_tracked_fixture_databases`, `test_sqlite_file_copies`.
- Batch B: `test_attach_to_family`, `test_discriminating_search`, `test_exam_protection`,
  `test_exam_protection_review`, `test_import_split_parity`, `test_library_exercises`,
  `test_method_explicit_landing`, `test_reader_active_reading`, `test_reader_activity`,
  `test_reader_formative_texts`, `test_reader_intentions`, `test_reader_passage_check`,
  `test_reader_reconnect`, `test_reader_reconstruct`, `test_reader_report`, `test_reader_rw1b_review`,
  `test_reading_hardening_landing`, `test_reference_check_binding`, `test_reference_gate_imports`,
  `test_source_exercise_import`, `test_source_exercise_rpcs`, `test_source_first_needs`,
  `test_source_service_spend_envelopes`, `test_ad1_reading_opportunities`, `test_ingest_runner`,
  `test_reader_quick_check`, `test_required_method_round3`, `test_rw1a_composition`,
  `test_structured_transport_parity`.

The files were chosen by `git grep` over `tests/` for the changed modules and functions:
`plan_fallback`, `get_ai_connection`, `connect_ai`, `first_run`, `chatgpt_plan_status` and
`chatgpt_plan_payload`, `quick_check_client`, `exercise_import_client`, `import_source_exercise`,
the passage-check and selection jobs, and `reader_quick_check`. The contract pins were added on top.

**Process notes.**
- No live or paid call, no sign-in and no vault copy. No tracked fixture vault was opened, and
  `git stash` was not used.
- The edit scripts (`python3 -I`, importing only `pathlib`) and the reference scripts ran under
  `env -i`, with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR. The reference scripts also had
  `UV_CACHE_DIR` set.
- `lint-imports` ran under `env -i` with the real HOME, which uv needs for its cache. It only
  analyses imports and makes no model call.

**Commits** (on top of `d20b33c5f`):

- `0142c7ef9`: the fixes for RR-F1 to RR-F3 and their tests.
- This record's commit: the regenerated references and this section.

## Fix round (orchestrator, 2026-10-23)

The final re-review confirmed the High (no silent metered fallback) and RR-F1/RR-F3 fixed, and left
two Lows. Both are fixed, each with a test that failed on `b0bd99bdb` and passes on the fix. No
migration, no config key added, no live or paid call, no sign-in, no vault copy.

| id | severity | title | verdict | commit | test (failed before) |
|---|---|---|---|---|---|
| L1 | Low | The RPC gates of the priced features resolved `canonical_ingest` outside `priced_by(...)`: they offered "Use OpenRouter instead", the learner granted it, the gate passed, and the job then refused for a missing price | fixed | `bcab944c3` | `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse[exercise_import, inquiry_quick_check, selection_question]` (each failed: the gate's response carried the offer); `test_fix_l1_an_exercise_imports_own_authoring_route_is_held_to_its_price` (failed: the import offered `authoring`) |
| L2 | Low | Under `quiet()` (either kind) `_plan_unavailable` still appended `offer_sentence()` and the `fallback_available`/`fallback_profile` fields, so the connection sheet's message pointed at a banner that never appeared (the re-review's "residual") | fixed | `bcab944c3` | `test_fix_l2_a_quiet_status_read_never_points_at_an_offer_it_did_not_make` (failed: the sentence was in the quiet message) |

### What changed

- **L1.** Each gate resolves under its feature's price setting, as its job does
  (`jobs._paid_quick_check_client`, `jobs._exercise_import_client`):
  - `reader.enqueue_exercise_import` (behind `reader.import_exercise` and the workbench's "work
    through this") under `source_service.llm_price_per_million` (`SEI.PRICE_SETTING`);
  - `reader.reconnect_answer` with `quick_check` and `reader_intent`'s `reader.active_question`
    under `reader_inquiry.metered_price_per_million` (`RQC.PASSAGE_CHECK_PRICE_SETTING`);
  - `_import_source_exercise`'s own `ready_client_for_task(..., "authoring")` (a harvest or a need
    passes no authoring client) under `source_service.llm_price_per_million`.
  While the setting is unset, the gate makes no offer, takes no grant of `canonical_ingest` (or
  `authoring`), and its unavailable message names the setting. Once it is set, the offer is made
  and a grant opens the gate (an ordinary metered request under the feature's caps). The gates wrap
  the existing `ready_canonical_ingest_provider(vault)` call in `plan_fallback.priced_by(...)`
  rather than adding a parameter, so the tests that stub that resolver with `lambda vault: ...`
  keep working. The section quick check (`reader.author_section_question`) is not admitted at a
  price and is unchanged.
- **L2.** New `plan_fallback.offers_suppressed()` (true inside `quiet()` or
  `quiet(honour_grants=True)`). `_plan_unavailable` returns the plan's own unavailable resolution
  when offers are suppressed, after the blocker and grant checks: no offer sentence, no fallback
  fields. A granted route still serves under `honour_grants` (RR-F1 unchanged). Outside quiet the
  sentence and fields are still there. The health line (`context.py`, plain `quiet()`) reads neither,
  so its payload is unchanged.

### Gate (fix round, 2026-10-23; targeted only, owner rule 2026-10-17)

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G -- ...`, with pytest at `-n 6` at most, one run at a time, and
`TMPDIR=fixtures-local/tmp`. There was no full suite, no durability lane and no vitest run.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 30 kept, 0 broken |
| The five new tests on `b0bd99bdb` sources | 5 failed |
| `test_plan_first_transport.py` after the fix | 55 passed |
| Batch A (43 files, listed below) | 975 passed |
| Batch B (11 files, listed below) | 293 passed |
| `db_validate_reference.py` | first run: 2 errors (`source_exercise_import.py` lines cited for `source_service.unverified_imports` and `family_attachment` moved by 5). Ran `db_generate_reference.py` (only source lines and commit stamps moved), then validated again: `"errors": []` |
| vitest, typecheck, frontend build, cargo | not run: nothing under `apps/` changed |
| Durability tests | none due (no migration, no DB or connection code) |

Test files run:

- Batch A: `test_plan_first_transport`, `test_chatgpt_plan_workspace`, `test_method_phrasing_report`,
  `test_chatgpt_plan_provider`, `test_chatgpt_plan_sidecar`, `test_attach_to_family`,
  `test_decider_landing`, `test_discriminating_search`, `test_exam_protection`,
  `test_facet_locks_landing`, `test_keep_local_retired`, `test_library_exercises`,
  `test_method_explicit_landing`, `test_mobile_allowlist`, `test_reader_active_reading`,
  `test_reader_activity`, `test_reader_formative_texts`, `test_reader_observation_records`,
  `test_reader_reconnect`, `test_reader_reconstruct`, `test_reader_report`, `test_reader_rw1b_review`,
  `test_reading_hardening_landing`, `test_reference_check_binding`, `test_reference_gate_imports`,
  `test_sidecar_reader`, `test_source_exercise_import`, `test_source_exercise_rpcs`,
  `test_source_first_needs`, `test_source_service_spend_envelopes`, `test_ux_phase1_connect_ai`,
  `test_ux_phase1_landing`, `test_ux_phase1_auto_build`, `test_reader_guidance`,
  `test_reader_quick_check`, `test_reader_passage_check`, `test_reader_intentions`,
  `test_desktop_rpc_contract`, `test_sidecar_contract`, `test_sidecar_serializer_snapshot`,
  `test_architecture`, `test_tracked_fixture_databases`, `test_sqlite_file_copies`.
- Batch B (the rest of the re-review's batches, because L2 changes every quiet resolution):
  `test_daily_loop_start_minutes`, `test_exam_protection_identity`, `test_ux_phase1_usability_round2`,
  `test_coordinated_migrations`, `test_exam_protection_review`, `test_import_split_parity`,
  `test_ingest_runner`, `test_required_method_round3`, `test_rw1a_composition`,
  `test_structured_transport_parity`, `test_ad1_reading_opportunities`.

Batch A was chosen by `git grep` over `tests/` for `plan_fallback`, the changed RPCs
(`reader.import_exercise`, `reconnect_answer`, `reader.active_question`),
`ready_canonical_ingest_provider`, `import_source_exercise`, harvest and `get_ai_connection`, plus
the contract pins.

**Process notes.**
- No live or paid call, no sign-in and no vault copy. No tracked fixture vault was opened, and
  `git stash` was not used.
- The edit scripts (`python3 -I`, importing only `pathlib`) and the reference scripts ran with an
  empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR under `env -i` (reference scripts with
  `UV_CACHE_DIR`). `lint-imports` ran under `env -i` with the real HOME for uv's cache; it only
  analyses imports.

**Commits** (on top of `b0bd99bdb`):

- `bcab944c3`: the fixes for L1 and L2 and their tests.
- This record's commit: the regenerated references and this section.
