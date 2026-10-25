# Curriculum C0a: Codex review and fixes

**Stage:** `curriculum-c0a-section-coverage`, branch `curriculum/c0a-section-coverage` (worktree
`learnanything-lr1`). **Review:** codex-job `20261025-164604-aNx9Bp` (code tracing; its sandbox could not open a
systemd user scope, so it ran no tests). Stage record: `docs/reviews/curriculum-c0a-section-coverage.md`.

No paid or live call was made. Every model and embedder in the tests is a fake. The ad-hoc commands (the CLI help
snapshot writer and the DB reference scripts) ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. No owner vault was opened.

## Review

Every finding was reproduced by a failing test before it was fixed: commit `a5c364430` (13 failed, 9 passed in
`tests/test_section_coverage_review.py` and `tests/test_section_coverage_rpcs.py`). The fixes are in commit
`28c697869`. All nine findings are fixed; none was rejected.

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | High | Coverage jobs keep stale exam protection across model calls | fixed | `28c697869` | `test_f1_protection_marked_during_the_call_keeps_nothing`, `test_f1_a_retry_after_protection_changed_is_never_sent`, `test_f1_a_batch_reads_protection_again_before_each_lo` (with an unprotected control) |
| F2 | Medium | Query embeddings get around the command's spend caps | fixed | `28c697869` | `test_f2_query_embeddings_are_held_to_the_curriculum_caps` (with a generous-cap control), `test_f2_the_dry_run_estimates_the_query_embeddings` |
| F3 | Medium | A Qwen failure turns off the other retrieval spaces | fixed | `28c697869` | `test_f3_a_failed_qwen_query_still_searches_deep` |
| F4 | Medium | Going back to a cached state leaves coverage stale | fixed | `28c697869` | `test_f4_returning_to_a_judged_state_reads_its_rows_again` |
| F5 | Medium | A crash can lose the paid passage-role proposals | fixed | `28c697869` | `test_f5_a_crash_before_the_proposals_is_recovered_without_a_call` |
| F6 | Medium | Kept comparisons put relations on the wrong section pair | fixed | `28c697869` | `test_f6_kept_relations_join_only_their_own_endpoints`; `test_compare_sources_keep::test_the_router_cards_read_is_typed_and_pure` (endpoints) |
| F7 | Medium | The correspondent read API makes model calls and writes | fixed | `28c697869` | `test_f7_the_search_fallback_embeds_and_logs_nothing` (embeddings and `log_feedback` on, `deliver` patched to fail) |
| F8 | Medium | Coverage jobs are shared across vault switches | fixed | `28c697869` | `test_coverage_jobs_belong_to_the_vault_that_started_them`, `test_a_vault_switch_during_a_job_keeps_nothing_in_the_old_vault` |
| F9 | Low | Subscription runs drop their token-based cost estimates | fixed | `28c697869` | `test_f9_a_subscription_run_reports_tokens_and_estimated_dollars` |

### What changed

- **F1.** `read_protection` reads the predicate once: the exam material, the teaching exclusions, and the readings
  held back by rule 4 (`source_marks` is now read once, not once per reading). `Protection.key` digests what it
  withholds. `CoverageGuard` follows the `figure_admission.FiguresGate` pattern. It reads protection again from
  the vault that is loaded at the moment of each check:
  - before each attempt, through PaidCalls' `admit`, so a retry is checked too;
  - before each physical request, as the context's request gate composed with any outer gate;
  - before the role proposals;
  - before the rows, inside the write transaction.

  If a section the prompt reads is now protected, if the predicate cannot be read, or if another vault is open,
  the guard refuses the rest of the work. It raises `ProtectionChanged`, a `BaseException` so that no retry layer
  relabels it. The result is `stale` and nothing is kept. `Library.refreshed()` reads protection again before
  each LO of `cover`, `cover_source` and the sidecar job, so a change rebuilds the library and its cached readings.
  The sidecar passes `ctx.loaded_vault` as the live vault. `stale` stops a batch (`STOPPING`).
- **F2.** `cover_source` runs candidate discovery and judgment inside two envelopes: its own `SpendEnvelope`
  (`curriculum.cover_max_cost_usd`) and the daily `curriculum.max_daily_cost_usd`. Every metered request is held
  by its own billing. The query embedding is always metered. A subscription judge is `estimated_only` and is never
  refused for money. `judge()` opens the daily envelope around candidate discovery too, unless a caller already has
  it open, so the pressed path's embeddings count as well. The judge's pre-call check reads the run envelope's
  remainder. The dry run adds `query_embedding` to each LO (pending, tokens, dollars), counts it against the cap,
  and reports `planned_metered_usd`.
- **F3.** `_query_vectors` returns None when no Qwen query was attempted and `{}` when one was attempted and
  failed or was capped. `search_sections` keeps the caller's `deep` setting, so the space resolver's other spaces
  still answer, and it never retries Qwen once per source.
- **F4.** `standing` no longer reads the newest insertion (`store.latest_judged` is replaced by
  `store.judged_states`). It reads the newest judgment whose rows match the LO's statement and every judged section
  as they are now. If none matches completely, it falls back to the newest one that matches the statement, checked
  row by row. A → B → A therefore reads A's rows again, and A is the state `judge` reported as fresh. No migration.
- **F5.** `passages` is now a ledger field. `judge_listwise` dumps nested models to JSON (`_jsonable`; existing
  ledger fields are byte-identical). Claims are built from the ledger rows (`_proposal_claims`) on both the paid
  path and the ledger-cached path. They are applied before the coverage rows, which mark the state done.
  `propose_roles` is idempotent per passage, role and judge. A run that stopped before or between the two writes is
  therefore resumed from the ledger with no call.
- **F6.** `kept_comparisons_for_card` adds each relation's `left_source_object_id` and `right_source_object_id`
  (typed ids, no prose). `_kept_between` maps them to sections and shows only the relations that join the origin
  and that section. A section kept with the origin but related to neither shows the keep with no relation.
- **F7.** `search_sections(read_only=True)` searches by keyword only: no query embedding, no `deliver`, so no
  model call and no write. `_fallback` uses it.
- **F8.** `_jobs(ctx)` returns one registry per vault database: job ids, section keys and running LOs. A job of
  the vault that was left behind is fenced. Its loop stops when the open vault's root changes, and its guard
  refuses every later request and record.
- **F9.** `cover_source` reports `estimated_tokens` and `estimated_usd`. On a subscription the dollars are the
  tokens times `source_retrieval.llm_price_per_million`; the shape follows `role_labeller._usage`. It also reports
  `metered_usd`, what the run's envelope was charged. `marginal_usd` is unchanged.

The CLI help (`learnloop curriculum cover`) and the `[curriculum]` docstring now say that the caps cover the query
embeddings. The CLI help snapshot and the DB/config references were regenerated; line citations moved.

**Constants:** none added. `STOPPING` and `STALE_MESSAGE` are a vocabulary and a message. No new config key,
weight, margin or threshold. **Scope:** two small edits outside the module: `practice_index/listwise.py`
(`_jsonable` for ledger fields) and `kept_comparisons.py` (relation endpoints in the card read). No migration,
no successor, and no frontend or `src-tauri` change.

### Carried forward (not in this step's scope)

- The reviewer's spec-conformance notes "free-text LO resolution for *also about…*" and "extraction-completion
  refresh" remain deferred to C0b, as the stage record states (decisions 2 and 5).
- On a subscription route, the request gate runs before each physical request only in real transports. The fakes
  make no physical request, so the tests exercise the per-attempt admission and the record checks.

## Gate (this step: targeted, memory-capped)

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with
`-n 6`, one at a time.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| Reproduction before the fix (`test_section_coverage_review.py`, `test_section_coverage_rpcs.py`) | 13 failed, 9 passed (every new test failed for its finding's reason) |
| Targeted (35 files, listed below) | **966 passed** |
| `--durable-sqlite` on `test_section_coverage.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`, `test_section_coverage_migration.py` | 44 passed |
| `db_generate_reference.py`, `db_validate_reference.py` (env -i) | 0 errors; 352 table notes; 4,771 wikilinks checked |
| Frontend, `src-tauri` | unchanged (no npm, vitest or cargo needed) |

Targeted files:

- Coverage: `test_section_coverage`, `test_section_coverage_review` (new), `test_section_coverage_rpcs`,
  `test_section_coverage_migration`.
- Kept comparisons and the card read: `test_compare_sources_keep`, `test_compare_keep_switch_off`,
  `test_rw4d_rw3b_composition`, `test_figures_rw5b_fix_round2`.
- Listwise ledger fields: `test_library_ask`, `test_library_ask_expand`, `test_library_ask_review`.
- RW4e proposals: `test_source_roles`, `test_roles_judges`, `test_roles_concurrency`, `test_roles_switch_off`,
  `test_label_roles_cli`, `test_reading_paths`.
- Retrieval: `test_find_sources_intents`, `test_practice_index_find`, `test_source_retrieval_followup`,
  `test_source_retrieval_guards`.
- Contracts: `test_cli_help_snapshot`, `test_config_refactor`, `test_sidecar_serializer_snapshot`,
  `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`,
  `test_ad_protected_tables`, `test_ad_protected_readings`, `test_public_tip_guards`,
  `test_plan_first_transport_paid_roles`, `test_plan_first_transport`, `test_plan_first_transport_offer_grants`,
  `test_registry_audit`, `test_tracked_fixture_databases`.
