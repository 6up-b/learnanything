# Curriculum C0a: section coverage and `reader.correspondents`

**Stage:** `curriculum-c0a-section-coverage`, branch `curriculum/c0a-section-coverage` (worktree
`learnanything-lr1`), base `0db8291c1`. **Spec:** `docs/specs/spec_deliverable_curriculum_v1.md` §6, §9, §12
(C0a, Q15 DECIDED 2026-10-25: C0a first); presentation `docs/specs/ux_reader_compare_ask_v1.md` §6, §12.3
(CA5a, CA5, CA6 read this). **No paid or live call was made** (every model is a fake; ad-hoc scripts ran under
`env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`). No owner vault was opened.

## What was built

| Piece | Where |
|---|---|
| Migration **222** `section_coverage` (WORKFLOW, append-only by trigger): one judged row per (reading, section, LO) with `treatment` (introduces, develops, applies, mentions, not_about), `roles_json`, `assumes_json`, `notation_md`, `origin` (provenance, retrieval, learner), `candidate_rank`, the learner's `learner_override` (is_about, not_about, none) and `learner_text`, `section_hash`, `lo_hash`, `state_key`, `ledger_id`, model, prompt version. A judge row is unique per (LO, state_key, reading, section) | `migrations/222_section_coverage.sql`; store `src/learnloop/db/stores/section_coverage.py` |
| The library a model may read, protection first: current reader-enabled readings minus exam material (the one predicate), held-back readings (rule 4) and sources without teaching authority (`teaching_exclusions`); a section with any withheld span is never a candidate; exercise and solution blocks dropped (`corpus.exercise_and_solution_spans`, the item-bound rule made public) | `source_retrieval/section_coverage.py` `Library` |
| Candidates without a model: provenance (`learning_objects_by_section`), one `search_spans(consumer="coverage")` per source with a shared query vector (keyword always; meaning when embeddings are on), hits grouped to sections, at most 3 per source (§12.1), and the learner's own links (`is_about` corrections, RW4d keeps on the LO) | `candidates_for`, `search_sections` |
| One listwise judgment per LO (route `section_coverage_judge` through the shared `judge_listwise`, ledger task `section_coverage`, left `learning_object`, right `reader_section`): every candidate judged (an answer that skips one is retried, then stored as nothing), refs validated, `assumes` only from the sent related topics; each passage's roles become RW4e proposals (fourth judge `section_coverage_judge`, `roles.on_demand_enabled`) | `judge`, `build_prompt`, `COVERAGE_TASK`; `reader/source_roles.py` `JUDGE_COVERAGE` |
| Cache: `state_key` = prompt version + the LO's title and statement + every candidate with its block hashes; a stored state makes no call; a read drops a row whose section (`section_hash`) or LO (`lo_hash`) changed since | `state_key`, `standing` |
| `reader.correspondents(extraction_id, section_id, search_fallback=true)`: per LO and per other book, the standing sections with treatment other than not_about, ordered by treatment then candidate rank, with treatment words, roles, the notation line (labelled AI-written), the kept relation (RW4d, held-out keeps out), `read`, a `jump` locator, the section's own title, and `also_learning_object_ids`. No model call, no coverage write. With no judged correspondent and `search_fallback`, the live hits per book labelled *found by search, not checked* (no treatment), the sections the learner dismissed left out, and `correctable_learning_object_ids`. A protected origin returns `withheld` | `correspondents`, `_fallback`; RPC in `learnloop_sidecar/handlers/correspondents.py` |
| The pressed check `curriculum.cover` (judges the section's LOs in a background job), `curriculum.cover_job` (state; relays the job's OpenRouter offer once), `curriculum.coverage_correct` (*not about this* / *also about…* / none: a `learner_card` ledger verdict and a learner row) | `handlers/correspondents.py` |
| Owner-run `learnloop curriculum cover --source <id> [--dry-run]`: the book's LOs (provenance, named, then its subjects'), each judged once across the library unless fresh, `curriculum.cover_max_cost_usd` checked before each call; dry run makes zero calls and writes nothing (keyword candidates only) | `cover_source`, `cli/curriculum.py` |
| Config `[curriculum]` `enabled` (true), `max_daily_cost_usd` (0.5), `cover_max_cost_usd` (5.0), `max_prompt_tokens` (24000); route `ai.routing.section_coverage_judge`; price gate `source_retrieval.llm_price_per_million` in `METERED_PRICE_SETTINGS`; every key classified in `parameter_registry` (switch structural, the rest `keep`) | `config/schema.py`, `ai/routing.py`, `ai/plan_fallback.py`, `params/parameter_registry.py` |
| Classification: `table_roles` WORKFLOW; AD `protected_tables` PROTECTED + READING (refs `extraction`, `section@extraction_id`, every judged column DERIVED/unread with its treatment), `column_classes` | `db/table_roles.py`, `adaptive_difficulty/protected_tables.py`, `column_classes.py` |
| Head fixture `migration_head_222` (renamed from 220; 222 applied to a backup-API copy, rollback mode, header 1/1, integrity ok, FK check empty; no 221) | `fixtures/migration_head_222/README.md` |

## T1 (plan-first)

- The route resolves like every routed task (the ChatGPT plan by default); `test_plan_first_transport_paid_roles`
  covers it with every other paid role.
- `curriculum.cover` is the only spawner and it is pressed: the job captures `unit_token` / `unit_origin` /
  `unit_stamp` in the request (RW7a's pattern), so a plan failure offers OpenRouter keyed by
  `curriculum.cover` (redesign D), relayed once by `curriculum.cover_job`
  (`test_a_failed_job_relays_an_openrouter_offer_keyed_by_curriculum_cover`; nothing sent).
- The admission check runs in the request too (an unrouted plan or a capped metered route answers
  `unavailable` without starting a job). No background work spawns coverage in C0a, so there is nothing to make
  quiet; `curriculum.coverage_on_extract` (C0b) must run under `plan_fallback.quiet()`.

## Protection (G-C1 for C0a)

- `test_no_exam_or_held_out_text_reaches_the_judge`: the exam source's question and a held-out unit's sentinel
  never appear in any `section_coverage_judge` prompt, and no row names their sections.
- `test_the_library_leaves_out_exam_and_held_out_material`, `test_a_protected_section_has_no_correspondents`,
  `test_a_correction_on_protected_material_is_refused`, the fallback test (no exam or held-out section listed).
- Fail closed: an unreadable predicate raises `CoverageError("withheld")`; the read API then answers `withheld`.

## Display only

No plan, scheduling, projection, grading, serving or replay path reads `section_coverage`; nothing writes
provenance, `entity_source_links`, `relations.yaml` or LO status; no successor. The only writes besides the
table are the ledger verdicts and the RW4e role proposals (their own switch). A search inside the read API
writes only what every search writes (the query-vector cache, and retrieval receipts while a new embedding space
is on).

## Decisions taken here (open to the owner or the landing)

1. **Rows carry `candidate_rank`, `section_hash` and `lo_hash`** beyond §6.1's list: the order the read API
   needs ("then retrieval rank") and a cheap freshness check at read without re-searching.
2. **Standing rows per LO are its newest judgment's**, each kept only while its section and the LO are
   unchanged. A book added after a judgment is not in it until the LO is judged again (pressed check or
   `cover`); C0b's on-extract job closes that gap.
3. **The origin's LOs** are its standing coverage that is about them, plus its provenance-linked LOs no standing
   row denies. Correspondents themselves are always judged coverage (never provenance alone).
4. **The search fallback** shows whenever no judged correspondent exists (also when the origin has rows but no
   other book does), so CA5a's pressed action is never empty-handed. Its query is the section's title, its LOs'
   titles and its lead passage.
5. **"Also about…" takes an LO id** plus the learner's words, kept verbatim (bounded). Resolving free text to
   an LO is C0b's scope resolver (§6.5 "the same resolver"); until then the client names the LO.
6. **No durable claim** (`judgment_work_claims`) per LO judgment: one sidecar never judges an LO twice at once
   (an in-memory set), and the ledger cache answers a repeated prompt; two processes could pay twice for one
   LO on the plan (no money; proportionate-protection bar).
7. **No route disclosure entry**: the judge sends book text only, never learner text (as `role_labeller`).
8. **No prompt-contract field and no frontend**: CA5a/CA5/CA6 wire the client; `reader.correspondents`
   refuses with `curriculum_disabled` while the switch is off.

## Constants

Structural bounds only, each labelled in the module: `SECTIONS_PER_SOURCE = 3` (spec §12.1), `HITS_PER_SOURCE
= 20` (the retrieval list's depth before grouping, not a cutoff), `PASSAGE_CHARS`, `STATEMENT_CHARS`,
`NOTE_CHARS`, `MAX_TEXT_CHARS`, the prompt's chars-per-token and fixed overhead (as `compare_sources`). The
ledger `score` column is an is-about indicator (1/0), never read as a weight. Config: the switch, two `keep`
spend caps and the `keep` prompt bound. No weight, margin or threshold.

## Gate (this step; targeted, memory-capped)

Every pytest inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`, one at a time.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (a first placement under `learnloop.curriculum` broke the frozen-cycles contract; the module moved to `learnloop.source_retrieval`) |
| Contracts: `test_cli_help_snapshot`, `test_config_refactor` (22 defaults snapshots), `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_ad_protected_tables`, `test_ad_protected_readings`, `test_public_tip_guards`, `test_migrations`, `test_judge_routes`, `test_plan_first_transport_paid_roles`, `test_plan_first_transport` | 649 passed |
| Every test file changed (42: the three new files, the head-path rename in 36, the migration-chain diffs) plus the modules' consumers (`test_label_roles_cli`, `test_reading_paths`, `test_roles_concurrency`, `test_roles_judges`, `test_roles_switch_off`, `test_source_roles`, `test_registry_audit`, `test_ad23_t1_routes`, `test_decider_landing`, `test_field_config`, `test_provider_resolution_parity`, `test_voyage_fallback`, `test_codex_tool_lockdown`, `test_plan_first_transport_offer_grants`, `test_plan_first_transport_today_quiet`, `test_ad_guard`): 58 files | 1,279 passed, 1 skipped, 1 failed: `test_plan_first_transport_offer_grants::test_p1...` (a `KeyError` on a drained batch under -n 6 load; untouched code, passed on the rerun below) |
| After the module move: `test_section_coverage`, `test_section_coverage_rpcs`, `test_section_coverage_migration`, `test_architecture`, `test_mobile_allowlist`, `test_cli_help_snapshot`, `test_config_refactor`, `test_plan_first_transport_offer_grants`, `test_ad_protected_tables`, `test_desktop_rpc_contract` | 385 passed |
| `-m durability` on `test_section_coverage_migration`, `test_retrieval_spaces_migration`, `test_rw2d_receipts_migration`, `test_reader_rw7a_migration`, `test_migrations`, `test_tracked_fixture_databases` | 4 passed |
| `--durable-sqlite` on the three new files | 31 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | 0 errors; head 222; 352 table notes; 1,052 configuration leaves in 71 sections (counts in `Configuration.md` and `Database.md` updated) |
| Frontend, `src-tauri` | unchanged (no npm, vitest or cargo needed) |
