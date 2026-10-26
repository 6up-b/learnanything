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

## Landing onto main

Branch `merge/c0a-onto-main` in `learnanything-merge2`, cut from `main` at `19253f3da` (mobile PR-1, specs, the
owner-capture fixes, RW7b's `mvp-0.32`, LP-min (a)'s `mvp-0.33` with migration 221). Main then gained two docs-only
commits (`317dd4728`, `a58dae89f`: spec RW5d and an MCP spec amendment); they were merged in at the end
(`25961baf0`, no conflict, `db_validate_reference.py` still 0 errors), so main is an ancestor of the tip. Main was
neither fast-forwarded nor pushed. **No successor (display only). Migration 222 lands on main's head 221.**

### Commits and conflicts

- `259b73e49`: the `--no-ff` merge of `curriculum/c0a-section-coverage` (`da39ed762`). Every conflict was composed so
  that both sides survive:
  - `config/template.py`: each defaults-snapshot comment names RW7b's and LP-min (a)'s keys and C0a's
    `[curriculum]` + route (the hashes were recomputed in `8b0475658`);
  - `params/parameter_registry.py`: `reading_paths.plan_uses_path` beside the four `[curriculum]` rules;
  - the head-fixture paths in 36 tests, `scripts/sanitize_migration_head_fixture.py` and the two `db_*_reference.py`
    scripts (now 222);
  - the migration-chain tests: 221 and 222 both on the way to head (`[..., 220, 221, 222]`), with
    `CLAIM_POINT_ALTERED_TABLES` and `C0A_ADDED_OBJECTS` both subtracted (`test_ad1_migration`, `test_ad23_migration`,
    `test_approach_maps_schema`, `test_help_assists_schema`, `test_library_asks_migration`, `test_reader_rw3b_migration`,
    `test_reader_rw7a_migration`, `test_retrieval_spaces_migration`, `test_rw2d_receipts_migration`,
    `test_t1_batch_origin_migration`);
  - the 425 generated reference notes: main's text, then regenerated (`3ddd46cd8`).

  `config/schema.py`, `ai/routing.py`, `table_roles`, the sidecar handler registry, the mobile allowlist,
  `tests/cli_help_snapshot.json` and the serializer snapshot merged without a textual conflict and needed no change
  (their contract tests pass as merged).
- `45aba54ee`, `158067a70`: the F1 fix, test first (below).
- `fda701430`: the head fixture (below), plus the three tests the merge did not touch that name head 221 or the old
  chain: `test_learner_claim_application_migration` (head 222, `[221, 222]` from 220), `test_section_coverage_migration`
  (222 now built on 221, `221 in` the head) and RW7b's `test_plan_follows_path` (head path).
- `8b0475658`: defaults fingerprints. `3ddd46cd8`: references. `25961baf0`: main's docs-only commits. Then this record.

Against main, the diff adds migration 222, four modules, five test files and the two review records, and renames
the head fixture (`migration_head_221` -> `migration_head_222`, `state.sqlite` R099, 23 files R100/R096). **No other
database or binary file is added, and the root `.gitignore` is unchanged.**

### Landing F1 [High, reopened by the final verify]: an invalid source-sets file was used as a protection snapshot

The loader turns a nonempty `source_sets.yaml` it cannot parse or validate into a `yaml:invalid` issue and **no**
source sets; that load still settles (its files did not change under it), so `vault_on_disk()` accepted it and every
exam source lost its role.

- **Fail first** (`45aba54ee`, `tests/test_section_coverage_review.py`, `test_landing_f1_*`, each for an unparseable
  and a schema-invalid file): red on `da39ed762` (run in a scratch worktree) and on the merge, **13 failed, 2 passed**
  (the 2 are the premise: the corrupt file loads settled, with no source sets and one `yaml:invalid` issue). An
  `env -i` probe on the merge showed the harm. The CLI batch with the file corrupted after its first LO judged
  6 LOs, sent the exam question in 3 prompts and kept 3 rows naming the exam's extraction.
- **Fix** (`158067a70`): `read_protection` refuses (`CoverageError("withheld")`, fail closed) whenever the shared
  `learner_protection.protection_issues(vault)` names a problem with the source sets. That covers a load or validation
  issue on the source-sets file, and an empty file caught mid-rewrite. Every protection read in this stage goes
  through `read_protection`, so the one check covers all of these:
  - admission: the `Library` built by `judge`, `cover`, `cover_source` and `--dry-run`, and by `curriculum.cover`
    (`withheld`);
  - the batch refreshes before each LO: `cover` raises, `cover_source` stops `stale` with `protection_unreadable`,
    and the sidecar job fails with `protection_unreadable` and the message (a new `except SC.CoverageError`
    branch);
  - the guard's checks before each attempt, physical request and record, both the CLI's files on disk and the
    sidecar's published reload (`stale`, nothing kept);
  - the read API: `reader.correspondents` answers `withheld`.

  The message names the problem and the fix: "LearnLoop couldn't check this library's exam material: the source
  sets could not be read (yaml:invalid). Fix the file (learnloop doctor) and try again." The CLI prints it as
  `{"status": "invalid", ...}` with exit 1. The same pattern was searched for in the rest of the stage's code: no
  other source-set read gives protection (`source_learning_objects` reads source sets only for subjects, after the
  library has been built).
- After the fix: the 15 new tests pass, and so do the four coverage files (63 passed apart from the two migration
  tests, which were fixed with the head). `lint-imports`: 36 kept.

### Head fixture

`fixtures/migration_head_222` is a backup-API copy of main's tracked, sanitized `migration_head_221/state.sqlite`
with **only 222** applied (`UPGRADE_SCRATCH_COPY`):
- `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
  `foreign_key_check` empty, no companion files; copied into place with the backup API.
- The schema diff against 221 is exactly 222's seven objects: `section_coverage`, its autoindex, three indexes and
  two triggers. Nothing else changed, and every table's row count is equal except `schema_migrations` (208 -> 209).
  222's SQL applied cleanly on 221, with no column or table collision.

The other 23 files are byte-identical to `migration_head_221`'s, so the sanitized content carries over. The branch's
head (222 on 220, without 221) was dropped, and `migration_head_221` is removed by the rename. The README records the
landing. The hard-coded paths are now 222: 36 tests, the sanitizer, `db_generate_reference.py` (3 times) and
`db_validate_reference.py`, plus `test_learner_claim_application_migration` and `test_plan_follows_path`.

### Regeneration

- **Defaults snapshots**: after clearing `config/__pycache__/template*.pyc`, all **24** entries were recomputed with
  `defaults_fingerprint_for_version`, and all 24 moved (the effective config gains `[curriculum]` and the route).
  The LP landing's lesson was checked: dropping `curriculum` and `ai.routing.section_coverage_judge` from each
  version's effective config reproduces main's hash at every version, so nothing else moved.
  `tests/test_eval_harness.py` passes; the field-arm hashes are unaffected (`MasteryConfig` is untouched).
- **References**: `db_generate_reference.py` rewrote the notes on the new head. Line citations into `config/schema.py`
  moved, and the table notes' `schema_head` is now 222. `db_validate_reference.py` reported only the two hand-kept
  prose counts. They are now 1,054 leaves in 71 sections and 352 table notes (`Configuration.md`, `Database.md`), and
  the validator reports **0 errors**. `validate_vault.py` passes (1,157 notes, 1,155/1,155 reachable).
- **CLI help snapshot, RPC pins, serializer snapshot, mobile allowlist**: no change needed.
  `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_mobile_allowlist`,
  `test_config_refactor`, `test_registry_audit`, `test_judge_routes`, `test_plan_first_transport{,_paid_roles}`,
  `test_architecture`, `test_ad_protected_tables`, `test_ad_protected_readings`, `test_public_tip_guards` and
  `test_eval_harness`: 645 passed.

### Gate

Setup ran in 5G scopes (`uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`). The pytest lanes ran under
`flock /tmp/learnloop-fullsuite.lock` in 10G / 2G-swap scopes, with `env -i` and empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. Logs are in `fixtures-local/landing-c0a/logs/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`pytest -n 8`, at `3ddd46cd8`, 54 min) | **21,595 passed, 1 failed**, 80 skipped, 38 xfailed. The failure was `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`, a known load flake: **3/3 passed** alone |
| durability (`-m durability`) | **126 passed**, 1 skipped |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-c0a/`) | 83 passed, 6 failed. These are exactly the 6 known, pre-existing failures: 4 need the retired vaults (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests), plus `test_activity_backfill` and `test_placement_fixture_copies[arxiv_v2]` |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **214 files, 1,834 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree | `git status` clean apart from `fixtures-local/` |

The docs-only merge of main (`25961baf0`) was not re-gated. Its four spec files are outside the code and the
reference vault, and `db_validate_reference.py` (0 errors) and `validate_vault.py` (passed) were rerun after it.

### Parity (backup-API copies of the mvp030 backups; no real model call)

**Setup** (`fixtures-local/landing-c0a/scripts/`; the LP landing's scripts re-pathed, plus `c0a_*.py`):
- `orig/` holds backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`.
- `u33/` is `orig` brought to **mvp-0.33 with main's code**: routes sent to a `127.0.0.1:9` blackhole,
  `upgrade --to mvp-0.33` (rc 0, "mvp-0.30 -> mvp-0.33"), then `rebuild-derived-state` twice.
- `code_main` and `code_merge` are `git archive` exports of main and of `3ddd46cd8`.
- `run.py`'s audit hook refuses any Codex process start and any non-loopback socket.
- The clock is frozen at 2026-10-19 09:00 UTC, with deterministic ids.
- The merge's route check: all 64 tasks resolve to the blackhole (the embedding route stays off).

**(a) Main vs merge at mvp-0.33** (`a33.sh`, with a second main copy as the noise control):
- **Whole databases** after the normal primary sidecar load (the merge applies 222 there):
  - the only schema objects on just one side are 222's seven, and `section_coverage` has 0 rows;
  - there are no SQL diffs and no added columns;
  - **every row of 356 tables is identical**: 18,495 rows on linear_algebra and 8,128 on probability;
  - `schema_migrations` differs only by 222;
  - integrity ok, `foreign_key_check` 0 and `model_call_receipts` 0 on both sides.
- **`rebuild --shadow` and `doctor`: 0 differences** main vs merge. The shadow's 30 schedule differences on
  linear_algebra, and doctor's 57 / 1 error and 101 / 48 errors, are the same on both sides and predate the stage.
- **Certification, curves, Today and the plan: byte-identical** main vs merge, and main vs main, on both vaults.

**(b) The command and the RPCs on a copy** (merge code; the test fake `CoverageJudgeFake` as the client):
- **`learnloop curriculum cover --source <lecture> --dry-run --json`** on linear_algebra (the 1-section 3Blue1Brown
  lecture "Linear combinations, span, and basis vectors"):
  - It ran with rc 0 and **0 calls**, and every table's count and content digest is unchanged.
  - **The source lists 21 LOs**: every LO of the subject has a candidate section in that lecture.
  - On the neutral blackhole route (metered, no price) every LO shows `would_cap`. An unpriced metered route is
    refused, which is the fail-closed behaviour.
  - With `llm_price_per_million = 2.0` on the copy, all 21 are `planned`, at about 63k-72k estimated tokens and
    about $0.13 each, so `planned_metered_usd` is **$2.81**, under the $5 cap.
- **A real run through `cover_source`** (the CLI's seam) on the same lecture: 21 LOs `ready`, 21 fake calls and
  169 rows. No row names a withheld section (13 in the book) or a left-out reading.
- **The sidecar** (`SidecarContext.load`, inline jobs):
  - `reader.correspondents` on the lecture's section is `judged` and lists the other lecture's and the book's
    sections with treatment, roles, `jump` and `alsoLearningObjectIds`.
  - `curriculum.cover` and `cover_job` end `done` with no further call (every state is fresh).
  - `curriculum.coverage_correct(not_about)` writes a learner row. After a new sidecar load, the row is still there
    and that correspondent is gone from the read.
- **The fallback** (probability, the Wikipedia article's section with no judged rows): status `unchecked`, with three
  of the textbook's sections labelled *found by search, not checked*, `treatment` null and `by: search`. None of them
  is withheld.

**(c) Exam protection** (linear_algebra copy; the other lecture marked `exam` through the source-sets writer):
- The marked lecture is `left_out`. With `cover_source` and `curriculum.cover` over the subject, **no prompt
  contains its title**: 0 of 21, against 21 prompts that do contain the control lecture's title.
- No `section_coverage` row names it, and the correspondents never list it. Read as an origin, it answers
  `withheld`.
- **The F1 case:** `source_sets.yaml` was overwritten with a nonempty, schema-invalid file after the first LO.
  - `cover` raises `withheld` with the message.
  - `cover_source` stops `stale` (the first LO was `fresh`, every later one `stale`) with **0 calls**, and no exam
    text reaches any prompt.

**(d) The switch** (`[curriculum] enabled = false` on copies of both vaults):
- `reader.correspondents`, `curriculum.cover`, `curriculum.cover_job` and `curriculum.coverage_correct` each
  answer `curriculum_disabled`, with 0 judge calls and **no table changed**.
- The CLI answers `invalid` ("section coverage is off").
- Certification, Today and the plan are **byte-identical** to the switched-on merge copy (c33), on both vaults.

**Receipts and calls.** Over the 34 databases under `fixtures-local/landing-c0a/` and `owner-lane-c0a/`,
`model_call_receipts` holds only the fake's 42 rows (`fake_coverage_judge` / `fake-coverage-model`, from (b) and (c)).
The other databases have no rows; 11 are the 4 KB `.learnloop/state.sqlite` stubs the probability backup already
carries, with no tables. `run.py`'s audit log was never created, so no process start and no socket connection
happened. Spend: $0. Nothing under `~/learnloop-vaults` was opened or listed.

### Owner notes

- **What it does:** for a section you are reading, "where else is this treated" lists the sections of your other
  books that treat the same topics (introduces, develops, applies, mentions), with their roles and a jump.
  - These are judged by the model route `ai.routing.section_coverage_judge` (unset: the ChatGPT plan under T1).
  - With nothing judged yet it shows search hits labelled *found by search, not checked*.
  - *Not about this* and *also about…* corrections stay across re-judgments and mark nothing as known.
  - It is display only: no plan, schedule, grade or certification reads it (parity (a) and (d) above).
- **Upgrade:** none needed beyond the usual. Migration 222 adds one empty table the first time the app or a command
  opens the vault. There is no successor and no `learnloop upgrade` step.
- **Owner-run batch:** run `learnloop curriculum cover --vault <vault> --source <book> --dry-run` first. It calls
  nothing and writes nothing, and it lists each LO with its estimated tokens and dollars against the cap. Then run
  it without `--dry-run`.
  - Covering one small source judges every LO with a candidate there, across the whole library. On the
  linear-algebra copy, one lecture listed all 21 LOs, at about $2.81 at $2 per million tokens on a metered route.
  - On the ChatGPT plan the dollars are estimates only, and the run is not refused for money.
  - A metered route with no `source_retrieval.llm_price_per_million` is refused before any call.
- **Spend caps:** `[curriculum] cover_max_cost_usd = 5.0` (per batch) and `max_daily_cost_usd = 0.5` (a UTC day).
  Both cover the query embeddings too.
- **Kill switch:** `[curriculum] enabled = false`. Every coverage RPC then answers "off" and nothing else changes.
- **If `source_sets.yaml` is damaged:** coverage refuses everything (reads show "withheld", the batch stops)
  until the file loads cleanly. `learnloop doctor` names the problem.

### Open items

- Carried from the stage, deferred to C0b: free-text LO resolution for *also about…*, the on-extract refresh
  (`curriculum.coverage_on_extract`, which must run under `plan_fallback.quiet()`), and the durable per-LO claim
  (decision 6).
- The batch's per-LO estimate (63k-72k tokens on the blackhole profile's 16,384-token output budget) is dominated by
  the output budget. A real route's estimate depends on its own output budget. Read the dry run on the owner's actual
  route.
- Parity (a)'s main-vs-main control showed one tally difference in the plan dump's "rows the run added" count
  (`judgment_ledger` 30 on the second main copy against 20 on main and on the merge). The plan output itself was
  byte-identical, so this is noise within main's own runs, not a merge difference.
