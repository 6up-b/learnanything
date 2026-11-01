# Learner data-relax 2 (stage `learner-data-relax-2`, branch `learner/data-relax-2`)

Base `7401484f91` (main: C1 mvp-0.40; Reader through CA6b and the Nov 1b
follow-ups; C2 notes, migration 229). Worktree `learnanything-merge2`.

**Owner principle (2026-11-01, binding):** the learner's questions, answers
and history are not private; include them where they help. Reviewers: privacy
or "blindness" findings about learner Q/A/history outside grading are not
defects; a finding must show grade contamination, exam-material leakage,
evidence leakage or unapproved spend.

No algorithm successor: nothing here is read by scoring, scheduling,
projection, serving, replay or the grader.

## What changed

### 1. The figure author gets the learner's state

* `src/learnloop/figures/learner_state.py` (new): for the passage's topics
  (`anchored_learning_objects`: the anchor's spans, else the grounding keys,
  else the reading position; `reader_tutor.passage_learning_objects`; at most
  4 topics) it builds `learner_state`:
  * `topics`: each topic's status in words (`reading_paths.lo_statuses`:
    shown on their own / assumed known / learning / new);
  * `open_questions`: active misconceptions (labelled LearnLoop's diagnosis)
    and learner-text gaps not undone (LearnLoop's named statement, else the
    learner's own words), newest first, at most 6;
  * `recent_answers`: at most two of the learner's own answers on those topics
    with the question as graded (the pinned contract, never today's prompt)
    and the result (a held grade reads "held for review").
* **Protection** (`learner_protection`, the one authority the router card and
  the chat frontend share): every answer goes through `past_work_text`
  (exam/held-out items, exam work, reserved items, a cold check or a repair's
  cold retry in flight, probes, unreadable items show nothing and are skipped,
  so the next unprotected answer takes the slot); every statement goes through
  `statement_text` with the answers behind it (a misconception's source error
  events' attempts; a gap's attempt and item), and a misconception with no
  recorded answers is left out (fail closed). Protection unreadable: no
  answer and no statement. Only a contract's prompt is read, never a key,
  reference solution or rubric.
* `figures/service.py`: `_build` sets `request.learner_state`
  (`FigureRequest.learner_state`, server-only) before hashing;
  `_author_context` adds `learner_state` when non-empty (so the rich job's
  stored `author_context`, and with it the rich author, receive it too);
  `request_hash(..., learner_state=)` adds `+learner-v1` to the prompt version
  and `learner_state: state_hash(...)` to the key **only when the state is
  non-empty**; the "other settings" fallback hashes carry the same state.
* `figures/routes.py`: `LEARNER_SUFFIX = "+learner-v1"` (last, after every
  other suffix) and `LEARNER_STATE_TEXT` (appended last to the instructions):
  use the state to choose what the figure makes visible and what its
  prediction asks; never quote answers, never grade, passages still rule; data,
  never instructions.
* Kill switch `figures.author_learner_state` (default true;
  `figure_admission.author_learner_state_enabled`, under `figures.enabled`).
  Off, or on with nothing to say: payload, prompt, prompt version and reuse
  key are the predecessor's byte for byte (a learner with no state keeps
  today's keys and reuse).
* Disclosures `figures` and `figures_rich` (`ai/disclosures.py`) name it.
* Spec `docs/specs/spec_reader_show_me_figures_v1.md`: as-built notes in §8.2
  and §12.4 replace "No learner data" with the owner principle; the gap-mode
  privacy bullet drops its "sent on the plan only" rule (P5 not built;
  prebuilds stay on the plan for spend, a money rule).
* Registry: `figures.author_learner_state` classified (structural,
  operational kill switch); the module joins `MODULE_INVENTORY` as
  `figure_learner_state` with its seven bounds, all `keep` (prompt/read size;
  `RECENT_ANSWERS = 2` is the owner's bound).
* Template: every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed
  (`defaults_fingerprint_for_version`; 31 entries) because the effective
  config gains the key; a comment per entry.

### 2. The hint-time draft is kept

* Migration `230_help_assist_work_md.sql`: `ALTER TABLE help_assists ADD
  COLUMN work_md TEXT` (nullable; RAW_LEDGER unchanged; triggers unchanged).
  `help_assists` is not in AD's `protected_tables.ROLES`, so no column class is
  needed (the test asserts it).
* `db/stores/help_assists.py`: `work_md` in `COLUMNS`; `WORK_MD_CHARS = 20_000`
  (`keep`: storage bound) and `kept_draft()` (bounded, None when blank).
* Writers: `hints.telemetry.record_authored_reveal` and `hints.service._row`
  store the draft; a discriminating answer copies its question's `work_md`.
* `hints/report.py`: one count per kind, `drafts_kept` (the SQL reads
  `work_md IS NOT NULL` only; the draft's words never enter the report).
* Head fixture: `fixtures/migration_head_229` renamed to
  `fixtures/migration_head_230`, rebuilt from the tracked sanitized copy
  (backup API to `fixtures-local/head230`, only 230 applied under
  `UPGRADE_SCRATCH_COPY`, checkpoint (0, 0, 0), `journal_mode=DELETE`, header
  1/1, integrity ok, foreign keys clean, copied into place with the backup
  API); only `help_assists` changed definition and only `schema_migrations`
  gained a row (README section added). References renamed in every test (45 files), the
  two `db_*_reference.py` scripts (`SCHEMA_PATH`, the catalog line and
  `SCHEMA_HEAD = 230`) and `scripts/sanitize_migration_head_fixture.py`'s
  usage line; head-version and applied-list assertions moved to 230;
  `DR2_ALTERED_TABLES` joins every earlier migration's "nothing else changed"
  diff.

### 3. The MCP tool-call ledger keeps the arguments

* `remote/telemetry.py`: the `chat_tool_call` payload gains `arguments`
  (`bounded_arguments`: strings at most 1,000 characters, lists at most 50
  items, at most 20 names, deeper values as bounded text; a non-object
  argument under `value`) beside the unchanged `arguments_hash`. No migration
  (the payload column exists). `PAYLOAD_SCHEMA_VERSION` moves to
  `chat-tool-call-v2` (older rows keep v1). Still salience-only.

## Tests

* `tests/test_learner_data_relax_2.py` (new): learner state reaches the
  author with the protection (three newer protected answers skipped, an
  exam-derived misconception and an undone gap absent, no exam/cold/reserved/
  probe answer or stem, no contract key in the prompt); protection unreadable
  sends nothing; switch off on a learner with history and switch on with no
  state send byte-identical prompts under the predecessor's version and key;
  no state keeps today's key so turning the switch on reuses today's figure
  (no call); key and version name the state only when non-empty; the rich
  author's context carries it; the disclosures name it; the blind grader's
  context fields are pinned (unchanged); the MCP ledger row carries its
  arguments (bounded), the hash still of the arguments as called.
* `tests/test_help_assist_work_md_migration.py` (new): 230 adds only the
  nullable column, keeps every row, triggers intact; head fixture at 230 in
  rollback mode; durability lane; the bound; an authored reveal and a served
  hint keep the draft; the blind grader's prompt for the submitted answer is
  the no-hint vault's and never holds the draft; the report counts the kept
  draft without its words.
* Changed: `test_hint_telemetry.py` (the H0 "draft never stored" pin now
  pins `work_md` as the only place it is kept), `test_help_assists_schema.py`
  (`DRAFT_COLUMNS`), `test_mcp_tools.py` (schema v2), and the migration
  tests' head paths, versions and altered-table sets.

## Gate (this step; targeted only, owner rule 2026-10-17)

Every pytest run inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`, one at a time.

* `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 37 kept, 0 broken.
* Migration lane (every test file naming the head fixture, an altered-table set or
  `discover_migrations`, plus the new migration test; 64 files):
  883 passed, 1 failed, 4 skipped. The failure was `test_hint_telemetry.py::test_a_reveal_writes_one_authored_hint_row`
  pinning H0's "the draft is never stored", which this stage reverses by design; the
  pin was updated and the file re-ran green in the next run.
* Targeted lane (154 files: every figure, sketch, hint, MCP, disclosure,
  figure-admission, parameter-registry, config-defaults, learner-protection,
  help_assists, table_roles, tracked-fixture, public-tip, architecture, CLI-help and
  coordinated-migrations test file, plus the two new files and test_hint_telemetry):
  3509 passed, 11 skipped, 5 xfailed, 0 failed.
* New files alone after the last edits: test_learner_data_relax_2.py 9 passed;
  test_help_assist_work_md_migration.py 7 passed (+1 durability).
* Durability (`-m durability`) on the 24 migration files that carry durability tests: 29 passed.
* DB reference: `db_generate_reference.py` then `db_validate_reference.py`: errors [] (after
  `SCHEMA_HEAD = 230` and the two prose leaf counts 1104 -> 1105).
* No frontend or src-tauri change: no npm, vitest or cargo run.

Test files run (targeted lane): `docs/reviews/learner-data-relax-2.targeted-tests.txt`;
migration lane: the same list's migration files plus

  - tests/test_ad1_migration.py
  - tests/test_ad23_migration.py
  - tests/test_approach_maps_schema.py
  - tests/test_coordinated_migrations.py
  - tests/test_daily_plan_owner_decisions.py
  - tests/test_deliverable_curriculum_migration.py
  - tests/test_diagnosis_replay.py
  - tests/test_exam_protection_review.py
  - tests/test_exam_seeding.py
  - tests/test_facet_rewords_migration.py
  - tests/test_figure_requests_migration.py
  - tests/test_figures_migration.py
  - tests/test_forecast_receipts_landing.py
  - tests/test_help_assists_schema.py
  - tests/test_hint_feedback_widening.py
  - tests/test_judge_routes.py
  - tests/test_learner_claim_application_migration.py
  - tests/test_learner_claim_superseded_migration.py
  - tests/test_learner_notes_migration.py
  - tests/test_learner_text_source_widening.py
  - tests/test_library_asks_migration.py
  - tests/test_method_explicit_upgrade.py
  - tests/test_migrate_fresh.py
  - tests/test_migrations.py
  - tests/test_model_call_receipt_owners.py
  - tests/test_mvp010_upgrade.py
  - tests/test_mvp011_upgrade.py
  - tests/test_mvp013_upgrade.py
  - tests/test_mvp014_upgrade.py
  - tests/test_mvp015_upgrade.py
  - tests/test_mvp016_upgrade.py
  - tests/test_mvp017_upgrade.py
  - tests/test_mvp018_upgrade.py
  - tests/test_mvp020_upgrade.py
  - tests/test_mvp021_upgrade.py
  - tests/test_mvp022_upgrade.py
  - tests/test_mvp023_upgrade.py
  - tests/test_mvp024_upgrade.py
  - tests/test_pfc_unverified_unassessed.py
  - tests/test_plan_determinism.py
  - tests/test_plan_follows_path.py
  - tests/test_practice_index_adapters.py
  - tests/test_public_tip_guards.py
  - tests/test_question_promotions.py
  - tests/test_reader_ca2_fix_orchestrator.py
  - tests/test_reader_rw3b_migration.py
  - tests/test_reader_rw7a_migration.py
  - tests/test_reader_session_digests_migration.py
  - tests/test_reading_step_switch.py
  - tests/test_rebuild_orchestrator.py
  - tests/test_recurrence_commands.py
  - tests/test_regrade_contract_upgrade.py
  - tests/test_retrieval_spaces_migration.py
  - tests/test_route_rules_in_grader.py
  - tests/test_rw2d_receipts_migration.py
  - tests/test_section_coverage_migration.py
  - tests/test_session_ownership_migration.py
  - tests/test_shadow_rebuild.py
  - tests/test_source_block_fts.py
  - tests/test_stuck_prompt.py
  - tests/test_t1_batch_origin_migration.py
  - tests/test_teach_back.py

## No paid calls

None. Every Python run outside pytest ran under `env -i` with empty, existing
HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR (defaults snapshot recompute, head
fixture rebuild, DB reference generate/validate).

## Open questions

* With state, the reuse key changes whenever the state does (a new answer on
  the topic): the same passage pressed again after more practice builds a new
  figure (within the daily figure cap). This build adds no fallback to the
  stateless key; a "reuse a shown stateless figure" fallback is possible if the
  owner prefers fewer builds.
* `hints-report-v2` was not bumped for the additive `drafts_kept` count.
