---
title: "learnloop.source_retrieval.vault_notes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/vault_notes.py"
source_paths:
  - "src/learnloop/source_retrieval/vault_notes.py"
source_commit: "11b7268e6a6fb10695533ed8dc91ca659f6bd1db"
source_commit_timestamp: "2026-11-02T01:53:30-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.source_retrieval.vault_notes module"
  - "src/learnloop/source_retrieval/vault_notes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.vault_notes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.vault_notes` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Curriculum C2b: the learner's notes are the vault's own (spec_deliverable_curriculum_v1 §10.1 as built).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py) |
| Source lines | 778 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `11b7268e6a6fb10695533ed8dc91ca659f6bd1db` |
| Commit timestamp | `2026-11-02T01:53:30-05:00` |

## Public API

- `class MeaningUnavailable(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 85) — A meaning search was asked while it is not available (``reason`` says why).
  - `__init__(self, reason: str) -> None` (line 88; internal)
- `class VaultNote` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 94) — One note of the learner's in this vault.
  - `note_key(self) -> str` (line 114; public)
  - `content_hash(self) -> str` (line 118; public)
  - `origin(self) -> str` (line 123; public)
  - `snippet(self) -> str` (line 127; public)
  - `searchable(self) -> str` (line 131; public)
  - `view(self) -> dict[str, Any]` (line 134; public)
- `note_key(ref_kind: str, ref_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 140)
- `split_key(key: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 144)
- `beside_protected(vault: Any, repository: Repository, key: str, *, every_anchor: bool=False) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 374) — Whether the note ``key`` is an annotation anchored on protected material now (or the predicate cannot be read: fail closed).
- `protected_keys(vault: Any, repository: Repository, keys: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 386) — The annotation notes among ``keys`` anchored on protected material now (C0a's predicate read once; unreadable: every annotation is, fail closed).
- `snapshot_protected_keys(vault: Any, repository: Repository, keys: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 395) — The annotation notes among ``keys`` any of whose anchor versions (or their sections' headers) touch protected material now (Codex re-review C2b F1).
- `anchor_sources(repository: Repository, key: str) -> list[tuple[str, tuple[str, ...]]]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 429) — Every book span a Reader note's snapshot may carry text from (Codex review C2b round 5 F2): for each anchor version the annotation ever had (a snapshot was taken from one of them), its reading and its anchored spans plus the header blocks of their sections (the note's heading is…
- `notes(vault: Any, repository: Repository) -> list[VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 461) — Every note of the learner's in this vault, as it is now (annotations, then captures).
- `read(vault: Any, repository: Repository, key: str) -> VaultNote | None` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 467) — One note as it is now, by its key; None when it is gone (deleted, dismissed, purged, words removed) or is beside protected material.
- `read_many(vault: Any, repository: Repository, keys: Iterable[str]) -> dict[str, VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 480)
- `words_search(corpus: Sequence[VaultNote], query: str, *, limit: int) -> list[VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 500) — The notes holding the query's terms as whole words, most distinct terms first, then the newest; none for a query with no terms.
- `meaning_unavailable(vault: Any) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 522) — Why a meaning search is not offered now, or None (the vault's embedding switches).
- `meaning_available(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 533)
- `recipe_text(note: VaultNote) -> str` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 537) — What is embedded for a note: its title and heading line, then its text.
- `records(corpus: Sequence[VaultNote]) -> list[EmbeddingRecord]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 560)
- `ensure_vectors(vault: Any, corpus: Sequence[VaultNote], *, client_factory: Callable[[], Any] | None=None, repository: Repository | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 590) — Embed the notes that have no current vector yet (content-addressed: an unchanged note is never embedded again), through the vault's embedding backfill: its switches, lock, receipts and price, capped per run like a source's backfill.
- `class MeaningResult` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 672)
- `meaning_search(vault: Any, repository: Repository, corpus: Sequence[VaultNote], queries: Sequence[str], *, limit: int, embedder: Any | None=None, owner_id: str='notes', index: bool=True) -> MeaningResult` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 682) — The notes nearest each query by meaning, best first (each note once, the first query's ranking first).

### Module constants

- `ORIGIN` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 59)
- `KIND_ANNOTATION` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 60)
- `KIND_CAPTURE` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 61)
- `REF_KINDS` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 62)
- `NOTE_CHARS` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 65)
- `SNIPPET_CHARS` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 67)
- `SEARCH_LIMIT` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 69)
- `RECORD_KIND` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 71)
- `RECORD_FIELD` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 72)
- `RECIPE` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 73)
- `NOTE_ANNOTATION_TYPES` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 75)
- `DROPPED_CAPTURE_STATES` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 77)
- `CAPTURE_TITLE` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 78)
- `ANNOTATION_HEADINGS` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 79)
- `MODES` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 81)
- `_WORD` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 82)
- `NOTE_RECIPES` ([src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 548)

### Explicit exports

`__all__` declares:

- `CAPTURE_TITLE`
- `KIND_ANNOTATION`
- `anchor_sources`
- `beside_protected`
- `protected_keys`
- `snapshot_protected_keys`
- `KIND_CAPTURE`
- `MODES`
- `MeaningResult`
- `MeaningUnavailable`
- `NOTE_CHARS`
- `NOTE_RECIPES`
- `ORIGIN`
- `RECIPE`
- `RECORD_KIND`
- `SEARCH_LIMIT`
- `VaultNote`
- `ensure_vectors`
- `meaning_available`
- `meaning_search`
- `meaning_unavailable`
- `note_key`
- `notes`
- `read`
- `read_many`
- `records`
- `recipe_text`
- `split_key`
- `words_search`

## Internal implementation anchors

- `_bounded(text: str) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 149)
- `_day(value: Any) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 156)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 168)
- `_protection(vault: Any, repository: Repository) -> Any | None` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 172) — C0a's predicate as the vault says now, or None when it cannot be read (fail closed).
- `_source_titles(repository: Repository) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 183)
- `_standing_annotation_ids(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 192) — The annotations the Reader lists (no standing delete): the repository's own rule.
- `_segments(connection: Any, anchor_version_id: Any) -> list[tuple[str, list[str]]]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 198) — One anchor version's segments (span id, section path).
- `_anchor(connection: Any, annotation_id: str) -> tuple[str | None, list[tuple[str, list[str]]]]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 213) — The head anchor's reading and its segments (span id, section path).
- `_anchors(connection: Any, annotation_id: str) -> list[tuple[str, list[tuple[str, list[str]]]]]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 224) — Every anchor version the annotation ever had, oldest first: (reading, segments).
- `_out(protection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]], connection: Any=None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 232) — Whether an annotation's anchor touches protected material.
- `_header_spans(connection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 251) — The span ids of the section header blocks the anchored spans sit under.
- `_section_title(connection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]], headers: dict[str, dict[str, str]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 273) — The section the annotation sits in, by its header's text (the recorded section path names header blocks by id, ``/page/16/SectionHeader/2``).
- `_annotation_notes(vault: Any, repository: Repository, *, only: Iterable[str] | None=None) -> list[VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 301)
- `_capture_notes(repository: Repository, *, only: Iterable[str] | None=None) -> list[VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 346)
- `_protected(vault: Any, repository: Repository, keys: Iterable[str], *, every_anchor: bool) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 406)
- `_words(text: str) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 496)
- `_no_texts(_loaded: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 544)
- `_current(vault: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 565) — The vault as its files say now (switches and protection may have changed since ``vault`` was loaded); ``vault`` itself when it has no root on disk.
- `_authorized_now(vault: Any) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 577) — ``(the vault as it is now, None)``, or ``(None, why not)``: the notes and the vault's embeddings must still be on before any embedding request (Codex re-review C2b R3 F2).
- `_covered(repository: Repository, model_id: str, corpus: Sequence[VaultNote]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/vault_notes.py), line 652) — ``{note key: content hash}`` of the notes with a current vector for ``model_id``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `module`; statically calls `anchor_sources`, `beside_protected`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; statically calls `meaning_available`, `meaning_search`, `meaning_unavailable`, `notes`, `read`, `read_many`, `snapshot_protected_keys`, `split_key`, `words_search`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `retrieve`; calls `retrieve`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `query_terms`, `section_header_titles`; calls `query_terms`, `section_header_titles`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `BackfillLockBusy`, `TASK_PREFIX`, `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `embed_query_texts`; calls `embed_query_texts`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `read_protection`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `BATCH_SIZE`, `backfill_caps`; calls `backfill_caps`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EmbeddingRecipe`, `EmbeddingRecord`; calls `EmbeddingRecipe`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `json`, `re`, `types`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]], [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_c2b_a_reader_note_written_beside_material_protected_since_is_never_read`
- [tests/test_notes_c2b_review5.py](../../../../../../tests/test_notes_c2b_review5.py) — direct import
  - `test_c2b_final_verify_f1_an_embedding_batch_drops_a_note_from_a_now_protected_older_anchor`
  - `test_c2b_final_verify_f1_the_notes_guard_judges_a_candidate_by_every_anchor_it_ever_had`
  - `test_c2b_r5_rereview_f1_a_snapshot_from_an_older_anchor_is_withheld_once_that_anchor_is_protected`
- [tests/test_notes_linked.py](../../../../../../tests/test_notes_linked.py) — direct import
  - `test_a_capture_is_a_note_and_a_dismissed_one_is_not`
  - `test_f9_a_link_hidden_during_the_refresh_stays_hidden`
  - `test_r5_settings_lists_the_hidden_notes_and_show_again_unhides_through_decide`
  - `test_r6_an_unchanged_read_fences_off_an_older_refresh_in_flight`
  - `test_r6_two_concurrent_refreshes_resolve_to_the_newest_read`
  - `test_re_f14_a_waiting_run_is_not_restarted_by_every_read`
  - `test_switched_off_every_rpc_refuses_nothing_is_read_and_the_reader_is_todays`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_a_legacy_tend_table_in_an_existing_config_is_ignored`
  - `test_an_unreadable_protection_predicate_keeps_every_annotation_out`
  - `test_c2b_f1_a_note_under_a_protected_section_header_is_no_note`
  - `test_c2b_f2_a_candidate_protected_before_the_request_refuses_it`
  - `test_c2b_f3_a_restored_text_keeps_its_vector`
  - `test_c2b_r3_f2_a_switch_turned_off_between_batches_stops_the_embedding`
  - `test_c2b_r3_f3_one_money_cap_for_the_whole_run`
  - `test_c2b_re_f2_embedding_batches_drop_notes_protected_meanwhile`
  - `test_c2b_re_f3_exact_words_search_the_whole_note`
  - `test_captures_with_only_media_or_a_link_and_no_words_are_not_notes`
  - `test_exact_words_rank_by_distinct_terms_and_ignore_stopwords`
  - `test_meaning_search_embeds_notes_incrementally_and_finds_what_words_miss`
  - `test_meaning_search_needs_the_vaults_embeddings`
  - `test_the_corpus_is_the_learners_own_words_never_protected_or_deleted`
  - `test_the_link_judges_candidates_come_from_the_same_vault_search`

## Modification guidance

- Make changes here when the responsibility remains vault notes within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/vault_notes.py](../../../../../../src/learnloop/source_retrieval/vault_notes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
