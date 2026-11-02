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

## Landing onto main

Worktree `learnanything-merge2`, branch `learner/data-relax-2`, from `3ddfd2d0d4`. Codex job
20261101-182023-REgLcd: F1 CONFIRMED-FIXED; F2 reopened twice, remainder ruled Low (R1 below).
No F2 code change was made in the landing.

### Merges

1. **Main `02614cfddd`** (curriculum C3, Reader RW5d P2 sketch compartment with
   `sketch_enabled` on, Reader follow-ups Nov 1b) -> `984be9a89f`.
   - `config/template.py` conflicted only in the 31 snapshot notes and hashes. Main's C3 notes
     are kept beside this branch's notes. Every fingerprint was recomputed with
     `defaults_fingerprint_for_version` after clearing `.pyc` (31 changed, second pass 0).
     `sketch_enabled` stays true.
   - Generated references: main's side taken, then regenerated. The two prose leaf counts
     moved 1105 -> 1106. `db_validate_reference.py` errors `[]`; `validate_vault.py` passes.
   - Parameter registry, `schema.py` and the spec auto-merged with both sides' entries.
   - Desktop catalog regenerated after the merge commit (`6662b42c3b`), so source commits
     resolve through main's history; `desktop_validate.py` passes.
2. **Main `a2c26e4525`** (learner/blindness-relax, which landed while the first gate ran; the
   gate was stopped and rerun on the result) -> `16787892b3`.
   - `template.py` conflicted the same way: blindness-relax notes kept beside data-relax-2's,
     so every key from both sides is in. 31 recomputed, second pass 0; `sketch_enabled` and
     `author_learner_state` stay true.
   - `ai/disclosures.py`, `config/schema.py`, the parameter registry and `pyproject.toml`
     (two new import contracts) auto-merged.
   - References: main's side taken and regenerated. Prose leaf counts 1109 -> 1110;
     `db_validate_reference.py` errors `[]`; `validate_vault.py` passes; desktop and module
     catalogs regenerate with no change, and both validate.
   - `lint-imports`: 40 kept, 0 broken.
- **Migration:** main's last migration is still 229, so this branch's stays
  **`230_help_assist_work_md.sql`** (no renumber). Main's tracked `migration_head_229` did not
  change after this branch's base. A check rebuilt it with the backup API plus 230 only: the
  schema matches `fixtures/migration_head_230` exactly, and every table count matches except
  `schema_migrations` (+1, the runner's row). The fixture is `journal_mode=delete`, header 1/1,
  `integrity_check` ok. The tracked fixture was not rebuilt again.

### Gate (on `16787892b3`)

| Lane | Result |
|---|---|
| `lint-imports --no-cache` | 40 kept, 0 broken |
| Full pytest (`flock` + 10G scope, `env -i`, `-n 8 --dist worksteal`) | **23547 passed, 0 failed**, 90 skipped, 47 xfailed (39:33) |
| Durability (`-m durability -n 6`) | 180 passed, 1 skipped |
| Owner lane (`-m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035` in gitignored `fixtures-local/landing-dr2/`) | **83 passed, 2 failed, 4 skipped**. Both failures are the known ones (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies::…[arxiv_v2]`) |
| Frontend (`npm install`, `typecheck`, whole `vitest --maxWorkers=4` in a 5G scope, `frontend:build`) | ok; 250 files, 2397 tests passed; build ok. Run on the first merge's tree; `apps/` is identical to main `a2c26e4525` and to the tip |
| cargo | not run: `src-tauri` does not differ from main |

No unexpected failure, so nothing needed a rerun. No live model call.

### Smoke (fresh owner copies, `fixtures-local/landing-dr2-smoke/`)

**Setup:**

- Fresh backup-API copies of the three mvp035 owner copies.
- Every AI route at the `127.0.0.1:9` blackhole, with the key variables unset.
- `env -i` with an empty `HOME`, `CODEX_HOME` and config directory.
- An audit hook logs every process start and socket connect, and refuses non-loopback connects
  and Codex process starts.
- Main's code (`a2c26e4525`) against the branch's (`16787892b3`), each a `git archive` with
  `migrations/`.
- On each copy: `upgrade` mvp-0.35 -> mvp-0.40, a primary load, `rebuild-derived-state`. Main's
  head is 229; the branch's is 230, applied cleanly.
- Nothing was requested, rendered or built. No Manim or bwrap ran.

**Results:**

- **Today and the daily plan** are byte-identical, main against branch:
  - linear_algebra: 525266 B and 84699 B;
  - probability: 740827 B and 124024 B;
  - arxiv_v2: 344204 B and 32436 B.
- **Figure author payload.** Four real text passages per vault, chosen from current LO source
  links on reader-enabled readings. For each, the payload, prompt, prompt version and reuse key
  were built as `_build` builds them for an anchored request, without asking a model and with no
  table changed.
  - **Switch on:** all 12 carry `learner_state` and `+learner-v1`, and the reuse key changes.
    - linear_algebra: topic statuses (learning/new) and two recent answers per passage ("held
      for review" + correct; correct + partial). 33 of its 70 answered attempts are protected
      now (30 exam/held-out, 2 checks waiting in the app, 1 diagnostic check), and none shows.
      An answer with no pinned contract carries no question.
    - probability: two open statements (a named misconception and a named prerequisite, both
      labelled LearnLoop's reading of the learner's words) and two partial answers with their
      questions.
    - arxiv_v2: one partial answer with its question.
    - `inputs_withheld` on every state's recorded inputs: None, meaning nothing it was read from
      is protected now.
  - **Switch off (in process) vs main's code:** byte-identical on all 12 (4630, 7097 and
    10366 B per vault).
- **`help_assists.work_md`** exists on every branch copy (head 230). These copies have no
  `help_assists` rows, so "NULL on old rows" is vacuous on owner data. It is covered by
  `test_help_assist_work_md_migration.py` (every row kept, column NULL).
- **`rebuild --shadow`** on the branch's copies: facet, mastery and schedule are 0/0/0 on all
  three, and the live database is unchanged.
- **Receipts:** 0 new `model_call_receipts` across the 6 databases compared with base.
- **Audit log:** 0 process starts and 0 socket connects from the smoke, so no non-loopback
  socket. A separate self-test of the hook logged its `true` start and its `127.0.0.1:9`
  connect.

### Rulings (orchestrator)

- R1: "F2 remainder (cached fuller delivery, pre-branch rich rows, revision inheritance) is ruled Low under the proportionate protection bar and the stuck-loop rule (third round on the same class). Every path needs an item or passage to be reclassified as exam material AFTER a figure was built from the learner's own state, and the figure's text is an author's explanation, not exam text. The recovery and direct-delivery checks shipped. Stored quick figures were never rechecked either. Queued follow-up: record inputs on quick rows and reconstruct fuller views from current rows at delivery."
- R2: "With learner state present, the figure reuse key follows the state, so a re-press after new practice builds a new figure within the daily figure cap. Accepted (owner principle: include learner state when beneficial); no stateless fallback reuse for now."
- R3: "hints-report-v2 keeps its version for the additive drafts_kept count; the MCP payload_schema_version moves to chat-tool-call-v2. Accepted."
- R4: "daily_plan/router_card.py checks reading-derived gaps only by attempt and item (pre-existing; the pattern F1 fixed here). Queued follow-up: reuse learner_state.inputs_reason there."

### Open items

- R1 follow-up: record learner-state inputs on quick figure rows. Reconstruct fuller views from
  current rows at delivery, which covers cached fuller delivery, pre-branch rich rows and
  revision inheritance.
- R4 follow-up: `daily_plan/router_card.py` should reuse `learner_state.inputs_reason` for
  reading-derived gaps.
- Owner: the figure author now receives "held for review" answers as well as graded ones, per
  the spec's text rule. With state, a re-press after new practice builds a new figure (R2).
- The two known owner-lane failures are unchanged.
