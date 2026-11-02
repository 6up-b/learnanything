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

(filled at the end of the stage)

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

## Open items

* Parallel stages: RW5d P3 (migration 232, head fixture rename) and teacher TE1+C4 (`read_note`
  uses C2's notes). The `note_links` / `learner_notes` APIs changed: `NL.tend_settings` ->
  `NL.notes_settings`, `NotesGuard(vault, live_vault=...)` (no settings arg), `judge_target`'s
  `settings` is optional, `link_by_hand(hit={"note_key": ...})`, snapshots carry
  `vault_ref_kind`/`vault_ref_id` and no path for vault notes. TE1's `read_note` should read a
  snapshot's `text_md` (unchanged) or `VN.read(vault, repository, note_key)`.
