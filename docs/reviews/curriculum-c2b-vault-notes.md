# Curriculum C2b: vault-native notes, tend removed, past papers option A

Branch `curriculum/c2b-vault-notes` (worktree `learnanything-dl2`), base `6b9cb117ba`
(main: C1 mvp-0.40, C2 notes, C3 syllabus, C5 notes gaps, migration head 231).
Spec: `docs/specs/spec_deliverable_curriculum_v1.md` §5.3 (as built, option A) and §10.5 (as
built, the vault's own notes). No successor: display, learner-voice records and scoping
proposals only.

## What was built

1. **Vault-native notes** (`src/learnloop/source_retrieval/vault_notes.py`). "Your notes" are the
   learner's Reader notes and highlights with their own words (the head version of each
   `source_annotations` row: `learner_text` and `what_i_think_is_going_on`; a bare highlight,
   a deleted annotation, a disposition and a model's or author's annotation are not notes) and
   their capture-inbox items (`capture_inbox` text and note; never a dismissed or purged one).
   * **Exact words** (always): the library search's tokenizer and stopwords
     (`source_block_fts.query_terms`), whole-word match over title, heading and text, ranked by
     distinct terms, newest first among equals.
   * **By meaning** (only with `embedding.enabled` and `embedding.backfill_enabled`): the
     vault's embedding model and route; notes embedded incrementally as `learner_note/text`
     records through `ops.embedding_backfill` (content-addressed, capped per run with
     `source_vectors.backfill_caps`, priced at `source_retrieval.query_embedding_price_per_million`);
     queries through `queries.embed_query_texts` (the tutor's library query path, record kind
     `source_query`, one query per request inside its caps); mean-centred cosine
     (`embedding_vectors.retrieve`) over the notes with a current vector. The Reader's prompt
     contract carries `notes.meaning`; false hides the picker's toggle and the RPC refuses
     `mode = "meaning"` (`meaning_unavailable`).
   * **Exam protection kept**: an annotation anchored on protected material (C0a's predicate)
     is no note (never searched, embedded, linked or sent); an anchor without segments is judged
     by its reading (fail closed); unreadable predicate: no annotation is a note. A Reader note
     linked before its anchor became protected is not read for gaps (`VN.beside_protected` in
     `note_gaps.note_text`, so `NoteGate` refuses it too).
   * `note_link_judge`'s candidates come from the same search (meaning first, then words, at
     most `notes.max_candidates`); prompt `note_link_judge.v2`.
2. **tend removed**: `curriculum/notes_tend.py` deleted; `NotesTendConfig` and the
   `notes.tend.*` keys gone (a legacy `[notes.tend]` table is dropped by a `model_validator`:
   no crash); the fake-tend fixture, `LEARNLOOP_NOTES_TEND`, the two tend launch-site approvals
   (`tests/test_codex_lockdown_round3.py`), the tend parameter-registry rules and the tend copy
   (disclosures, Settings, Reader, docstrings) are gone. Notes are in every vault; `notes.enabled`
   stays the kill switch. `tests/test_notes_never_read.py::test_the_tend_adapter_is_gone` greps
   `src`, the desktop sources and the tests.
3. **Note text is learner text** (owner principle 2026-11-01):
   * `note_link_judge` left `plan_fallback.PLAN_ONLY_TASKS` (now empty) and runs on the ordinary
     quiet-route rules: the route as configured, `plan_fallback.quiet()` (no offer or grant from
     background work), a metered route only with `source_retrieval.llm_price_per_million`, inside
     the curriculum's daily envelope (`DL.daily_envelope`; `note_link_judge` joined
     `SC.CURRICULUM_OWNER_KINDS` so its spend counts toward `curriculum.max_daily_cost_usd`).
   * Receipts keep note prompts (`withhold_receipt_input` has no caller left; kept as a generic
     facility).
   * C5's note gap reading takes the learner-text-gaps pipeline's ordinary transport: the gap
     reader and judge routes, Tier 1's Decider, the embedding shortlist; the row keeps the note's
     words (`stored_words`), with a write-time provenance record (`provenance.note_record`: its
     topics and linked passages); a belief named from a note may become a holding-pen candidate.
     Removed: `note_reader_client`, `note_clients`, `ReadingWaits`, `READING_NOTE`/`gap_route`,
     `contract.NOTE_ROUTE`, the plan-outage waits. **Kept**: `NoteGate` (consent, link,
     protection, bound to the prepared text), never drafting a topic from a note (§10.2: a note is
     never a generation input), the no-checkpoint rule for a note's reading (landing step 0),
     exam-material protection, and the blind grader (untouched; no grading module changed).
4. **Snapshots point at vault notes** (migration `233_learner_notes_vault_origin.sql`, numbered
   233 because RW5d P3 claims 232; renumber at landing if needed): `learner_notes` rebuilt
   temp-then-rename under `foreign_keys = OFF`; `origin` gains `vault`; `path`/`line` nullable;
   `vault_ref_kind` (`annotation` | `capture`) and `vault_ref_id`, with CHECKs (a vault row needs
   its reference, any other row its path and line). `note_key` = `annotation:<id>` /
   `capture:<id>`. Tend-era rows stay readable (a Pocket Notes snapshot keeps its label). AD's
   column classes cover the two new columns. Head fixture renamed `migration_head_231` ->
   `migration_head_233` (rebuilt from the tracked sanitized 231 head with only 233 applied;
   README section), every head path and chain list composed, `SCHEMA_HEAD = 233`.
5. **Past papers option A** (`source_retrieval/deliverables.py`): known subject -> v2 flat list
   for that subject (unchanged); ambiguous -> `past_papers_by_subject` groups by subject name
   (`past_paper_groups`, each group computed for its own subject) and an instruction to use only
   the deliverable's subject's group (`deliverable_scope_resolver.v3`); the request guard re-reads
   each group for its own subject. Switch off: v1 byte-identical. C3's two Codex-review tests that
   pinned "ambiguous -> no papers" were updated to the owner's option A.

Frontend: `NotesContractDto.meaning` (replaces `lexicalOnly`), `NoteHitDto` (`noteKey`, `refKind`,
`refId`, ...), `NoteSearchDto`; the picker shows *exact words* / *by meaning* only when
`meaning` is true and links by `noteKey`; ChatGPT-plan-only copy removed. Desktop catalog
regenerated. No Rust change (passthrough RPCs).

Config: every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprint recomputed (31; the effective config
lost `notes.tend`); no new key.

## Owner decisions applied

Recommended defaults; frictionless; live behind kill switches (`notes.enabled`,
`embedding.enabled`/`backfill_enabled`, `curriculum.exam_units_in_scope`). No paid or live call
was made in this stage (fakes only; any script outside pytest ran under `env -i` with empty
HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR).

## Gate

Owner rule 2026-10-17: no full suite, durability lane or whole vitest here (the landing gate runs
them once on the merged tree). Every pytest/vitest/npm command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`.

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: **40 kept, 0 broken** (the notes contract now forbids
  `learnloop.source_retrieval.vault_notes` instead of `curriculum.notes_tend`).
* Head-fixture and migration set (every test naming `migration_head_233`, 48 files, plus
  `test_learner_notes_vault_origin_migration.py`, `test_ad_protected_tables.py`,
  `test_table_roles.py`, `test_tracked_fixture_databases.py`): first run 654 passed / 43 failed
  (the composed chain lists and head versions, expected), fixed; `--lf` reruns 36 + 7 passed.
* Affected set (328 test files exercising a changed module or contract: text_gaps, notes,
  deliverables, plan_fallback, disclosures, the parameter registry, config template fingerprints,
  prompt contracts, AD protected tables, head fixture, the contract tests): **12103 passed,
  12 failed, 29 skipped, 5 xfailed** (57 min). The 12 were fixed (base-contract switch-off pins
  now pop or switch off `notes`, the architecture contract's private-name refusal, the judge-routes
  disclosure, the composed-guard bug Codex round 2 found) and those 11 files rerun with the notes
  files: **211 passed**.
* After Codex rounds 3 and 4: the notes, past-papers and C3 files (7 files): **123 passed**;
  then every test file naming the notes/curriculum modules plus the contract tests (56 files:
  `git grep -l -E 'note_links|vault_notes|notes_fixtures|learner_note|deliverables as DL|deliverable_path|test_notes_linked'`
  plus `test_architecture`, `test_judge_routes`, `test_desktop_rpc_contract`,
  `test_mobile_allowlist`, `test_table_roles`, `test_tracked_fixture_databases`,
  `test_codex_lockdown_round3`): **955 passed, 0 failed**.
* Durability: `pytest -m durability tests/test_learner_notes_vault_origin_migration.py
  tests/test_learner_note_source_kind_migration.py tests/test_learner_notes_migration.py`:
  **3 passed**.
* Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck`: exit 0;
  `npx vitest run --maxWorkers=4 src/screens/reader/readerNotes.test.tsx
  src/screens/reader/compareKeep.test.tsx src/screens/reader/notesGaps.test.tsx`: **3 files,
  34 passed**; `npm run frontend:build`: built. No `src-tauri` change (no cargo check needed).
* Schema: `db_generate_reference.py` then `db_validate_reference.py`: errors `[]` (SCHEMA_HEAD
  233; 1105 effective config leaves after the prose counts 1111 -> 1105). Desktop catalog:
  `desktop_generate.py` / `desktop_validate.py`: passed (303 TS / 6 Rust, ACTIVE 309,
  reproducible). The references carry this branch's commit stamps; regenerate on the merged tree
  at landing.
* No live or paid call: every model and embedding client was a fake; scripts outside pytest ran
  under `env -i` with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR. Spend: $0.

New or changed test files: `test_notes_linked.py` (rewritten), `test_notes_vault_search.py`
(new), `test_notes_as_learner_text.py` (rewritten for the ordinary transport),
`test_notes_never_read.py` (vault_notes; tend-gone grep), `test_curriculum_c2b_past_papers.py`
(new), `test_learner_notes_vault_origin_migration.py` (new), `notes_fixtures.py` (rewritten),
`test_curriculum_c3_exam_scoping.py`, `test_curriculum_c3_codex_review.py`,
`test_codex_lockdown_round3.py`, `test_judge_routes.py`, `test_figures_switch_off.py`,
`test_compare_keep_switch_off.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`,
`test_reader_intent.py`, `conftest.py`, and the head-path/chain updates in the 48 migration files.

## Codex review

Round 1: `codex-agent` job `20261101-222621-2nmxEi`, `gpt-6.1-sol`, effort high, read-only, on
`git diff 6b9cb117ba..9c737d6245`, with the owner's reviewer rule (privacy/blindness findings about
learner text outside grading are not defects; only grade contamination, exam-material leakage,
evidence leakage, unapproved spend or correctness). Three findings, all fixed:

* **F1 (High, exam leakage)**: an annotation on an unprotected body span under a protected
  section header would carry the header's text as its heading (embedded and sent). Fixed:
  `vault_notes._out` also checks the header block of each anchored span's section
  (`_header_spans`); such a note is beside protected material (no note).
  Test: `test_notes_vault_search.py::test_c2b_f1_a_note_under_a_protected_section_header_is_no_note`.
* **F2 (High, exam leakage)**: the link run read the corpus once; an annotation protected while
  an earlier topic was judged could still be sent for a later topic whose passage is elsewhere.
  Fixed: the corpus is read per topic, and `NotesGuard.with_coverage(..., notes=...)` reads the
  candidates' protection (`VN.protected_keys`) on the live snapshot at every request's admission
  and before the record; a protected candidate refuses (nothing sent or written).
  Test: `test_c2b_f2_a_candidate_protected_before_the_request_refuses_it`.
  Not gated: an embedding request for a note between the corpus read and the request (a
  sub-second window; the note's text is the learner's, the anchor check ran on the read), per the
  proportionate-protection bar.
* **F3 (Medium, correctness)**: `_covered` collapsed stored vectors by note id, so a text
  restored after an edit looked uncovered. Fixed: matched by (record, hash).
  Test: `test_c2b_f3_a_restored_text_keeps_its_vector`.

Round 2 (job `20261101-225144-ycyvKs`, on `3e1a5cdbea`), all fixed in `d8a4d3fbe7`:

* **F1 (High)**: the F2 fix bound the original guard's refusal (empty candidate list) into the
  composed coverage guard. Fixed: `also=guard._refusal_in` (the composed guard's own); the F2 test
  now exercises it.
* **F2 (High)**: embedding requests were not re-checked for protection. Fixed: `ensure_vectors`
  embeds in batches and re-reads protection before each later batch (made stricter in round 3).
  Test: `test_c2b_re_f2_embedding_batches_drop_notes_protected_meanwhile`.
* **F3 (Medium)**: truncation to `NOTE_CHARS` hid exact-word matches and suffix edits. Fixed:
  `VaultNote.full_text` is searched and hashed; `text` stays the bounded stored/sent text.
  Test: `test_c2b_re_f3_exact_words_search_the_whole_note`.

Also from the affected-test run: the base-contract switch-off pins of RW1c, RW4d, RW5a, RW7a and
RW1b now pop or switch off `notes` (in every vault since C2b, pinned by `test_notes_linked.py`);
the architecture contract refused `repositories._STANDING_DELETE` across the boundary, so the rule
is exposed as `Repository.standing_annotation_ids()`; `test_judge_routes` checks the new
disclosure.

Round 3 (job `20261101-235140-VkDemI`, on `d8a4d3fbe7`), all fixed in `aa15858705`:

* **F1 (High)**: a later topic found notes with the run's stale vault and its first embedding
  batch skipped the check. Fixed: each topic finds notes with the vault as its files say now,
  and every batch (the first included) re-reads the vault.
* **F2 (Medium, spend)**: switches turned off during a run were not re-read. Fixed:
  `_authorized_now` (notes, `embedding.enabled`, `backfill_enabled` from the files) before every
  batch and before the query embedding; off stops the run.
  Test: `test_c2b_r3_f2_a_switch_turned_off_between_batches_stops_the_embedding`.
* **F3 (Medium, spend)**: each batch got a fresh money cap. Fixed: one cap per run, the remaining
  cap passed to each batch. Test: `test_c2b_r3_f3_one_money_cap_for_the_whole_run`.
* **F4 (Medium)**: several named subjects (a syllabus in two subjects' sets) took the flat v2
  list. Fixed: v2 only for exactly one subject; several named subjects take the grouped form over
  those subjects. Test: `test_c2b_r3_f4_several_named_subjects_send_the_grouped_form_for_those`.

Round 4 (job `20261101-235810-Ipsk9K`, on `aa15858705`):

* **F1 (High)**: a later topic's section titles (queries) came from the path read at the run's
  start. Fixed: the topic's queries come from its path as it is now (a section protected
  meanwhile drops out of the path view).
* **F3 (Medium, spend)**: the switches were read once before several query embeddings. Fixed:
  read before each query.
* **F2 (High) — accepted residual, not changed (proportionate-protection bar, owner 2026-10-24)**:
  inside one `backfill_embeddings` batch, its own retry after a provider failure is not re-gated.
  The window is one in-flight embedding request (at most 32 notes) that failed and is retried
  within seconds; the text is the learner's own note, whose anchor was checked against the
  protection read immediately before the batch, and the spend stays inside the run's cap and
  the switches read before the batch. Gating every physical request of the shared backfill would
  change `ops.embedding_backfill` for every consumer. Recorded as an open item.

Escalation note: rounds 3 and 4 were concurrency races with sub-second to seconds-long windows
(protection or switches changed while an earlier request is in flight); per the stuck-loop rule
no fifth round was started; the residual is above.

## Open items

* Round 4 F2's residual (a retry inside one embedding batch is not re-gated), above.
* Mean-centred cosine over a handful of notes ranks coarsely (a vault with one note scores zero);
  ranking is top-k only, no threshold, and words always run after meaning for the judge.

* Parallel stages: RW5d P3 (migration 232, head fixture rename) and teacher TE1+C4 (`read_note`
  uses C2's notes). The `note_links` / `learner_notes` APIs changed: `NL.tend_settings` ->
  `NL.notes_settings`, `NotesGuard(vault, live_vault=...)` (no settings arg), `judge_target`'s
  `settings` is optional, `link_by_hand(hit={"note_key": ...})`, snapshots carry
  `vault_ref_kind`/`vault_ref_id` and no path for vault notes. TE1's `read_note` should read a
  snapshot's `text_md` (unchanged) or `VN.read(vault, repository, note_key)`.
