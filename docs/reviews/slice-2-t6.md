# Slice 2 T6: source retrieval

> **Integration note (merge into main, 2026-10-12, merge branch `merge/t6`
> from main `1acf79b2`).** Main had gained router R0 (175: `judgment_ledger`
> rebuilt, judge CHECK `llm`, `verifier`, `owner`, `diagnoser`,
> `learner_card`, `exact_key`, `decider`), the PF-c fix, T8 v4, the Phase 6
> owner decisions (new vaults at `LATEST_ALGORITHM_VERSION`, snapshots via
> `defaults_fingerprint_for_version`) and Slice 2 T1 (176, `mvp-0.12`, B1/B3
> on the shared `register_suites` seam). Where this record and
> `slice-2-t6-codex-review.md` say otherwise, this note is current: migrations
> 175 and 176, `migration_head_175`/`_176` and `SCHEMA_HEAD = 175`/`176` below
> describe the branch as built.
>
> - **Migration: T6's 175 is 177** (`migrations/177_source_block_fts.sql`; the
>   SQL is unchanged, with a numbering comment added). **The branch's 176
>   (re-review F20) is folded into 177, not kept as 178.** It only recreated
>   the delete and update triggers, unchanged, for vaults that had applied 175
>   before its in-place edit. Renumbered, no vault can hold an earlier 177. A
>   vault that applied the branch's 175/176 recorded the version numbers main
>   uses for R0 and T1, so main's runner cannot upgrade it either way (the
>   `t6_*` fixtures-local copies in the T6 worktree are such vaults; rebuild
>   them from fresh copies).
> - **Tests for the fold.** F20's
>   `test_a_vault_that_applied_the_earlier_175_gets_the_identity_delete_paths`
>   is retired with the migration. Two tests replace it:
>   - `test_a_fresh_vault_has_the_identity_delete_paths_through_177`;
>   - `test_migration_177_indexes_a_176_vaults_existing_blocks`: a vault at
>     176 that holds blocks upgrades by 177 alone, and the backfill indexes its
>     blocks.
>
>   F14's renumbered-rowid test is unchanged.
> - **Head fixture `migration_head_177`.** A backup-API copy of main's
>   `migration_head_176` with only 177 applied, then
>   `wal_checkpoint(TRUNCATE)` and `journal_mode=DELETE`. `integrity_check` is
>   ok, `foreign_key_check` is empty, and the README is updated. Updated to the
>   new head:
>   - the eight test paths;
>   - the generator's three mentions and the validator's path;
>   - `SCHEMA_HEAD = 177` in both scripts.
>
>   The references were regenerated with `errors: []`: 298 table notes
>   (`source_block_fts` is the 17th `DERIVED` table) and 656 configuration
>   leaves in 38 sections. The prose counts in `Database.md` and
>   `Configuration.md` are fixed to match, as is the latest fingerprint in
>   `Configuration.md`.
> - **Table roles.** `source_block_fts` is `DERIVED` with exactly one replayer
>   (`source_block_fts`). Its FTS5 shadow tables stay excluded from the
>   table-role walkers (`fts5_shadow_table_names`).
> - **Ledger.** Both writers of `source_relevance` verdicts use
>   `judge = 'llm'`, with `judge_model` and `prompt_version`. That is one of
>   R0's seven judges, so the CHECK is unchanged. The writers are the live
>   verification (`practice_index.listwise`) and the evaluation's labels
>   (`source_retrieval.bench`).
> - **`embeddings compare`.** The one composition root registers both T1's
>   `b1`/`b3` and T6's `source_retrieval`/`b4`. The option help texts keep
>   both sides' wording (`--suite` and `--view` name all of them).
>   `recurrence bench` is unchanged.
> - **`tutor_qa`.** Main's question-time facet → LO mapping (F4/F11) is
>   intact, as is the help-before-work marker (`seconds_into_attempt` and
>   `attempt_progress` on the pending row). T6's retrieved spans, item
>   exclusions and cited-span reveal debit sit beside them, and
>   `test_the_question_time_facet_mapping_is_unchanged_by_retrieval` passes.
> - **Defaults fingerprints.** All four snapshots were recomputed with
>   `defaults_fingerprint_for_version`:
>   - `mvp-0.9`: `a12da8c2…`
>   - `mvp-0.10`: `4d1e7237…`
>   - `mvp-0.11`: `1e58dd67…`
>   - `mvp-0.12`: `d6c9d70d…`
>
>   `DEFAULT_CONFIG_TEXT` is 79 lines, and T6 adds no template line.
> - **Codex out (exhausted until 2026-10-18).** T6's routes are unset, so the
>   rewrite and the verification follow `ai.active_provider = "codex"`.
>   `tests/test_source_retrieval_codex_unavailable.py` routes them through the
>   real `plan_route`/`resolve_client` to a fake Codex. That Codex either
>   refuses every turn with `CodexUnavailable` or is not ready:
>   - **Tutor, Codex exhausted.** The rewrite and the verification are each
>     tried (one call and one retry) and fail. The tutor answers on the
>     learning object's linked spans, and the manifest records
>     `lo_provenance` with verification `failed`. No `source_relevance` rows
>     are written, and the question is `answered`.
>   - **Tutor, Codex not ready.** Verification is `unavailable`, so nothing is
>     retrieved or called.
>   - **Deep library search.** It keeps its keyword and meaning hits (basis
>     `keyword+meaning`), with the rewrite `failed` or `unavailable`.
>   - **Typing.** It never routes to Codex.
> - **Mobile.** `tests/test_mobile_allowlist.py` pins one new RPC and five
>   extended ones as registered and never phone-allowed. The new one is
>   `reader.span_learning_objects`. The extended ones are
>   `reader.search_sources`, `reader.ask`, `ask_tutor_question`,
>   `plan_quick_add` and `confirm_quick_add`.
> - The CLI help snapshot is regenerated (`sources`, `recurrence`).

Branch `slice-2/t6`, worktree `learnanything-t6`, base `e9ced35e` (main, with all
of Slice A including Phase 5a's `learnloop embeddings compare` harness).
Spec: `spec_embedding_consumers_v1.md` §1 (R1–R6), §4, §9 (T6), §12–§13 (T6
entries), §15 P4. Daily loop: `spec_daily_loop_v1.md` §4.3 (capture filing) and
§4.4 ("Practice this") may consume this retrieval, so the core API is a plain
library call.

## 1. Plan (written before coding)

**What T6 changes.** Four consumers stop deciding "where in my sources is this?"
by substring or by a fixed, question-independent list:

| Consumer | Today | T6 |
|---|---|---|
| Library search (`reader.search_sources`) | `instr(lower(text), ?)`, document order | FTS5 BM25 + today's substring list fused by RRF while typing; on Enter ("deep"), also dense source-block retrieval and, for conceptual questions, an LLM-rewritten query. Display only: no rerank |
| Tutor spans (`tutor_qa`, practice/feedback/library contexts) | top-4 LO-linked spans, same for every question | question-dependent: hybrid retrieval (+ rewrite for conceptual questions) over the subject's teaching sources, then an LLM listwise rerank that **verifies** each candidate; only verified spans reach the tutor, and the existing citation allowlist keeps citations inside them |
| Quick Add scope (`select_relevant_units`) | unit label contains a brief keyword | units ranked by FTS5 BM25 over their blocks fused (RRF) with the label match; still pure (no model, no write) |
| Span → LO for spans without provenance (`learning_objects_for_span` returns `[]`) | nothing | a nearest-LO **suggestion** (stored facet-definition vectors + keyword match over LO text, RRF), labelled `suggestion`, never written as a candidate or target |

**Files to add**
- `migrations/175_source_block_fts.sql`: `source_block_fts` (FTS5, porter +
  unicode61; `extraction_id`, `span_id` UNINDEXED; rowid = the block's rowid),
  insert/delete/update triggers on `source_document_blocks`, and a backfill.
- `src/learnloop/db/stores/source_block_fts.py`: query sanitizing, BM25 search
  scoped to extractions, the rebuild used by the replayer.
- `src/learnloop/source_retrieval/` (new package, imported only by adapters —
  sidecar, CLI — and by `content`; tutor and reader receive it by injection, so
  no new package cycle):
  - `recipes.py`: `source_block/text` v1 (current extraction of every source;
    section path + block text; header/footer/TOC and tiny blocks excluded), in
    its own registry, **not** in the default backfill (see below);
  - `corpus.py`: current extractions, block metadata, scopes (library =
    reader-enabled sources; tutor = the subject's teaching sources minus every
    assessment span: held-out exam spans, exam-role units, `exercise` /
    `assessment_alignment` links);
  - `dense.py`: complete-scope vector index with the Phase 1 mean-centred
    cosine (a test pins it to `retrieve()`), cached per process;
  - `queries.py`: conceptual-question gate, cached query embeddings
    (`source_query` record kind), the LLM rewrite (route `source_query_rewrite`);
  - `search.py`: the hybrid core `search_spans(...)` (BM25, dense, substring,
    rewrite lists fused by Phase 5b's `reciprocal_rank_fusion`), returning hits
    with per-list ranks and an honest `basis` label;
  - `verify.py`: the listwise rerank/verify (route `source_rerank`, Phase 5b's
    `PaidCalls`), verdicts to `judgment_ledger` (task `source_relevance`);
  - `library.py`, `tutor.py`, `suggest.py`: the consumers;
  - `evaluation.py`: compare-harness suite `source_retrieval` (the T6 report:
    substring vs BM25 vs dense vs hybrid vs hybrid+rewrite on LLM-labelled
    question → span pairs, two passes, agreement reported);
  - `b4.py`: compare-harness suite `b4` (page-image embeddings vs Marker text
    chunks, question → page pairs, two LLM label passes);
  - `suites.py`: `register_suites(SUITES, role_tasks=ROLE_TASKS)`.
- Tests (fakes only): FTS/triggers/replayer, recipes and hash pins, dense maths,
  search, library, tutor spans (incl. F4/F11 mapping intact), Quick Add, LO
  suggestion, both suites with fake clients on a fixtures-local style copy,
  CLI and sidecar wiring.

**Files to change**
- `db/table_roles.py`: `source_block_fts` DERIVED; FTS5 shadow tables are owned
  by their virtual table and excluded from `user_table_names`.
- `substrate/rebuild_orchestrator.py`: the `source_block_fts` replayer (sole owner).
- `ai/routing.py`, `config/schema.py`: routes `source_query_rewrite`,
  `source_rerank`, `source_query_writer`, `source_relevance_judge`; section
  `[source_retrieval]` (kill switch `enabled`, plus `query_rewrite`,
  `tutor_rerank`, `suggest_learning_objects`, caps and prices). Fingerprint
  snapshots recomputed with a recorded decision; parameter-registry rule.
- `ai/providers/openai_embedding.py`: image input (`(mime, bytes)`) for
  multimodal OpenRouter models (gemini-embedding-2), for B4 only.
- `practice_index/query_vectors.py`: optional `record_kind` (default unchanged).
- `ops/embedding_compare.py`: suites may render their own Markdown;
  `ops/pf_calls.py`: `embed` accepts a token estimate for non-text inputs.
- `tutor/tutor_qa.py`: optional injected span provider (None = today's spans);
  reader asks record a suggested LO when the span has no provenance.
  `_grounded_facet_targets` and the facet → LO mapping are untouched.
- `reader/reader_dialogue.py`: passes the suggester through.
- `tutor/promotions.py`: the "not mapped" error names the stored suggestion.
- `content/pipeline/quick_add.py`: BM25 unit ranking.
- Sidecar `reader.search_sources` (`deep` flag), `reader.ask`,
  `ask_tutor_question`, new `reader.span_learning_objects`; CLI `embeddings
  backfill --record-kind source_block`, `embeddings compare --suite
  source_retrieval|b4`, `sources search`.
- Frontend: Enter in the library search box runs the deep search; the hit
  count line says which basis was used.
- Head fixture → `migration_head_175`, DB/config references, CLI help snapshot.

**Migrations.** One: 175 (`source_block_fts`), DERIVED. Takes the next free
number now; T1, R0 and the stuck prompt take 175–178 at merge, so expect to
renumber.

**Algorithm successor and kill switch.** None. Retrieval is context: it
changes which source text the tutor, the library list and the Quick Add preview
show, never scoring, scheduling, projections, evidence, certification or what
is served. No persisted meaning changes: `source_block_fts` is a rebuildable
index, verdicts are new ledger rows, suggestions are labelled and never become
targets. Kill switch: `source_retrieval.enabled = false` restores every
consumer's current behaviour exactly; finer switches `query_rewrite`,
`tutor_rerank`, `suggest_learning_objects`.

**Default backfill decision.** `source_block/text` stays out of the default
`embeddings backfill` and is embedded only when named
(`--record-kind source_block`). A source-block corpus is one or two orders of
magnitude larger than the item and facet corpora; added to the default it
would make every bare backfill plan exceed its default caps (100 candidates,
100 calls) and stop with `over_budget`, so the existing recipes would stop
backfilling, and an owner who raised the caps would pay for the whole library
without asking for it.

**Spend caps and routes.**
- Live: query embedding (1 call, ≤ $0.01, cached by text), rewrite (1 call +
  1 retry, `rewrite_max_cost_usd` $0.01), tutor verify (1 call + 1 retry,
  `rerank_max_cost_usd` $0.03). Metered routes need
  `source_retrieval.llm_price_per_million` or the step is skipped with a label;
  Codex runs `estimated_only`. Every failure degrades (keyword-only search, or
  the LO-linked tutor spans), never raises into the consumer.
- Batch: the source-block backfill (Phase 1 backfill, its caps and
  `--dry-run`); the two suites through the compare harness (whole-plan
  admission, `--dry-run`, checkpoints, receipts). Routes:
  `source_query_writer`, `source_relevance_judge`, `source_query_rewrite`, all
  unset → active provider. Embedding route never falls back.

**judgment_ledger writes.** `source_relevance` (live tutor verification and
both suites' two label passes; judge `llm`, model, prompt version, input hash).

**Tests.** Listed above; plus R1 (no embedding score writes anything), replay
makes no embedding or model call, kill switch byte-identity for each consumer,
and the F4/F11 tutor mapping tests unchanged.

## 2. What was built

### 2.1 The keyword index (migration 175, DERIVED)

- `source_block_fts`: FTS5 (`porter unicode61 remove_diacritics 2`) over the
  `text` of every `source_document_blocks` row except page furniture
  (`PageHeader`, `PageFooter`, `TableOfContents`, the exclusions the library
  search always had). `extraction_id` and `span_id` are UNINDEXED identity
  columns; each row's rowid is its block's rowid, so the three triggers
  (insert, delete, update) keep the index in step with every writer, including
  `persist_document_ir`'s replace-a-run path. The migration backfills existing
  blocks.
- `db/stores/source_block_fts.py`: `match_expression` turns free text into
  quoted, ORed terms (FTS operators, quotes and column filters are inert; a
  query of only stopwords has no terms), `search_blocks` (BM25, scoped to
  extractions, optional prefix on the last word for type-ahead), block reads,
  section-header resolution, and `rebuild_source_block_fts`, the body of the
  one registered replayer (`source_block_fts` in `rebuild_orchestrator`;
  whole-vault, block ledger only, no model or embedding).
- FTS5 creates five shadow tables per virtual table. They are storage of the
  registered virtual table, not tables with a policy of their own, so
  `table_roles.user_table_names` (and the two reference scripts, the debug-time
  store and the goal-series scratch store, which walked `sqlite_master` and
  looked up every name's role) now exclude them via `fts5_shadow_table_names`.
- Head fixture `migration_head_174` → `migration_head_175` (backup-API copy,
  upgraded through 175 only, `wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`,
  `integrity_check` ok, `foreign_key_check` empty); README, the seven test
  references and both reference scripts (`SCHEMA_HEAD = 175`) updated.

### 2.2 The dense side

- Recipe **`source_block/text` v1** (`source_retrieval/recipes.py`): one record
  per substantive block of every source's current extraction, record id
  `<extraction_id>/<span_id>`, text `Section: <header path>` + the block text
  (whitespace collapsed, capped at 6000 characters). Marker records section
  paths as header block ids (`/page/16/SectionHeader/2`), so the recipe
  resolves them to the header's text; blocks under 20 non-whitespace characters
  and page furniture are not embedded. Pinned in
  `tests/test_embedding_recipe_hash_pins.py`; every existing pin is unchanged.
- **Not in the default backfill.** It lives in `SOURCE_RETRIEVAL_RECIPES`, a
  consumer registry like T4's, and `learnloop embeddings backfill` embeds it
  only when named, alone (`--record-kind source_block`). Why: on the three
  owner vault copies the corpus is 456, 699 and 4259 records, against default
  caps of 100 candidates and 100 calls. Joined to the default it would make
  every bare backfill plan exceed its caps and stop with `over_budget` (so the
  item and facet recipes would stop backfilling), and an owner who raised the
  caps would buy the whole library without asking for it.
- `source_retrieval/dense.py`: a source is searched densely only when every
  embeddable block of its extraction has a vector for `embedding.model` (by
  identity or by identical recipe text, the Phase 1 rule). *(Review F2: this
  was a whole-scope rule, so one new import switched meaning search off for the
  library; the index now covers the complete extractions and labels the result
  `partial`. See `slice-2-t6-codex-review.md`.)* Scores are the Phase 1 mean-centred cosine over the whole
  scope, exclusions applied after centring; a test pins ranking and scores to
  `retrieve()`. The centred matrix is cached per process (keyed by database,
  model and manifest digest; float32, about 70 MB for the 4259-block arxiv
  copy at 4096 dimensions).
- Query vectors go through the practice index's cached, capped query embedder
  (`embed_queries` gained an optional `record_kind`; T6 uses `source_query`,
  the practice index's default is unchanged): one request for the question and
  its rewrite, at most a cent.

### 2.3 Rewrite, fusion, verification

- **Conceptual gate** (`queries.is_conceptual`): a question word, a question
  mark, or at least five content terms. Keyword searches are never rewritten.
- **Rewrite** (route `source_query_rewrite`, prompt `source_query_rewrite.v1`):
  at most 80 words in the register of a passage that would answer, plus up to
  12 search terms. Phase 5b's `PaidCalls` (one capped call and one retry,
  checkpointed; a metered route without `source_retrieval.llm_price_per_million`
  is skipped). Used as two more lists (`rewrite_keyword`, `rewrite_meaning`).
- **Fusion** (`search.search_spans`): `keyword`, `substring` (library only),
  `meaning`, the two rewrite lists and caller lists (the tutor's `provenance`)
  are fused by Phase 5b's `reciprocal_rank_fusion` (ranks only; no BM25 or
  cosine cutoff anywhere, R4). Every hit keeps its per-list ranks and the
  result names its `basis` (`keyword`, `keyword+meaning`, `+rewrite`, ...).
  Every paid step degrades to a status; nothing raises into a consumer.
- **Verification** (`verify.verify_spans`, route `source_rerank`, prompt
  `source_span_verify.v1`), used on the one consequential path, the tutor's
  grounding: the LLM judges every candidate `answers` / `related` /
  `unrelated` and picks at most `tutor_spans`, best first; a pick it also
  called `unrelated` is dropped. Every verdict appends to `judgment_ledger`
  (task `source_relevance`, judge `llm`, model, prompt version, input hash,
  `right_kind = source_span`), under ids derived from the exact request, so the
  same question over the same pool is served from the ledger without a call.

### 2.4 Consumers

1. **Library search** (`source_retrieval/library.py`, sidecar
   `reader.search_sources`, `learnloop sources search`). Typing: BM25 with the
   last word as a prefix, fused with today's substring list (so a block the old
   search found can still rank). Enter (`deep`): also `meaning` and, for a
   conceptual question, the rewrite. Display only, no verification. Hits keep
   today's shape plus `matched_by`, and sections show header text instead of
   Marker block ids. The response's `basis` reaches the UI: the hit count reads
   "· keyword match · Enter also searches by meaning", "· keyword + meaning" or
   "· keyword + meaning + rewritten question" (`screens/reader/searchBasis.ts`,
   tested). *(Review F3: the typing hint was shown whatever the index state and
   a meaning-only basis was labelled "keyword + meaning"; both are fixed, the
   hint now follows the response's `meaning_search`.)*
2. **Tutor spans** (`source_retrieval/tutor.py`, injected into
   `tutor_qa.ask_question` by the sidecar's `ask_tutor_question`). Teaching
   scope = the LOs' subjects' source-set sources plus any source their teaching
   provenance cites, with every assessment span excluded (whole exam-role
   units, which covers held-out exam questions, and spans cited by `exercise`
   or `assessment_alignment` links). Retrieval uses the question plus the
   practice question in context; the LOs' own linked spans are one more ranked
   list. In the practice context a candidate that reproduces the item's
   expected answer (`answer_leaks_expected`) is withheld before anyone sees
   it. *(Review F1, High: this let the item's own worked solution rank first and
   be cited, and short answers were never withheld. Fixed: the query is the
   learner's question alone, problem sets, notes and exams never ground the
   tutor, exercise and solution blocks are dropped in practice and feedback,
   short answers are measured, and a cited span's overlap is a reveal. See
   `slice-2-t6-codex-review.md`.)* Verification then picks at most four; the existing citation allowlist
   keeps citations inside them. If verification cannot run (switch off, no
   route, metered route without a price, over budget, provider failure, empty
   pool) the tutor gets exactly the LO-linked spans it gets today. Each
   question records how its spans were chosen in
   `source_context.source_retrieval` (basis, lists, rewrite/dense/verification
   status, counts; never span text). The kill switch records nothing.
   **F4/F11 intact:** `_grounded_facet_targets`, the candidate facets and the
   persisted `facet_learning_object_ids` / `learning_object_subject_ids` are
   computed from the item or note exactly as before; a test asks the same
   question with and without retrieval and compares them.
3. **Quick Add scope** (`content/pipeline/quick_add.py`). Units are ranked by
   two lists fused by RRF: each unit's summed FTS5 BM25 over its own blocks
   (stemmed, so "symmetric" finds "symmetry") and today's label keyword match.
   Selection takes them best first under the cap and returns them in outline
   order; still no model, no write. The plan reports `scope_basis`
   (`whole_source`, `unit_text_bm25+label_keywords`, or `label_keywords` when
   retrieval is off, which selects exactly as before).
4. **Nearest-LO suggestion** (`source_retrieval/suggest.py`). For a span whose
   `learning_objects_for_span` is empty: active LOs ranked by BM25 of the span
   text over each LO's title, summary and facet titles/claims, and by the
   span's stored `source_block/text` vector against the stored
   `facet/definition` index (each LO by its best facet), fused by RRF; no paid
   call. Every entry is `"label": "suggestion"`. Reader questions record them as
   `source_context.suggested_learning_objects` (never in
   `candidate_learning_object_ids`, which promotion, filing and the learner
   field read); the reader ask response carries them; the "not mapped"
   promotion error names them as "a suggestion and not a provenance link";
   sidecar `reader.span_learning_objects` and `learnloop sources suggest-lo`
   expose them. No UI picker yet (open question 3).

### 2.5 The T6 report and B4 on the shared harness

`source_retrieval/suites.register_suites(SUITES, role_tasks=ROLE_TASKS)` adds
two suites and three roles (`source_question_writer` → `source_query_writer`,
`source_relevance` → `source_relevance_judge`, `source_rewrite` →
`source_query_rewrite`); `learnloop embeddings compare` calls it before
`run_compare`. Suites may now render their own Markdown body
(`markdown_lines`), and `PFCaller.embed` accepts a token bound for non-text
inputs.

- **`source_retrieval`** (the T6 report, §13): LLM-written questions seeded
  from sampled blocks (the seed is a known relevant span: a label-free hit
  rate) plus logged tutor questions (a reader question's anchored span is its
  seed); systems `substring` (today's library search, literally), `keyword`,
  `meaning`, `hybrid` (the production deep search without a rewrite) and
  `hybrid_rewrite` (with the production rewrite prompt); pooled top 10;
  two-pass LLM labels with agreement; nDCG@10, Recall@10, MRR@10, seed hit@10,
  paired bootstrap intervals and a stated bar.
- **`b4`** (benchmark B4, P4): every PDF source whose original is stored in
  the vault; per-page Marker text; questions per seed page; systems
  `text:<model>` (each model embeds the page's chunks, a page scores its best
  chunk), `image:<model>` (each image-capable model embeds the page rendered by
  pypdfium2 at a 1024 px longest side), `keyword` (BM25 over page text),
  `hybrid_text` (keyword + the vault model's chunks) and `hybrid_image` (that
  plus the page image); two-pass labels on (question, page text).
  `page_image_default` is true only when `hybrid_image` beats `hybrid_text`
  (nDCG@10 interval above zero, Recall@10 not worse, at least ten scored
  questions). Page vectors are cached in the output directory, never in the
  vault.
- The embedding client sends an image as OpenRouter's multimodal input
  (`{"content": [{"type": "image_url", ...}]}`) for image-capable models
  (`google/gemini-embedding-2`); the receipt hashes a digest, never the bytes.
  Verified with real calls (below).

### 2.6 Configuration, routes, CLI

- `[source_retrieval]` (modelled defaults only, not in the decision-only
  template): `enabled` (kill switch), `dense`, `query_rewrite`, `tutor_rerank`,
  `suggest_learning_objects`, `llm_price_per_million`, `rewrite_max_cost_usd`
  ($0.01), `rerank_max_cost_usd` ($0.05), `query_embedding_price_per_million`,
  `rrf_k` (60), `tutor_candidate_pool` (12), `tutor_spans` (4). Parameter
  registry rule (structural, operational). All three defaults snapshots
  recomputed with a recorded decision in `config/template.py`.
- Routes `source_query_rewrite`, `source_rerank`, `source_query_writer`,
  `source_relevance_judge` (unset → `ai.active_provider`); the embedding route
  never falls back.
- CLI: `learnloop sources search | suggest-lo`; `embeddings backfill
  --record-kind source_block`; `embeddings compare --suite source_retrieval|b4`.
  Help snapshot regenerated.
- Docs: DB and configuration references regenerated (292 table notes, 631
  leaves in 37 sections; `source_block_fts` has a written purpose), validator
  clean.

## 3. Algorithm successor: none

Retrieval is context. T6 changes which source text the library list, the
tutor's prompt and the Quick Add preview show, and offers a labelled
suggestion. It changes no scoring, scheduling, projection, evidence,
certification or serving. Nothing persisted changes meaning:
`source_block_fts` is a rebuildable index of the block ledger, the verdicts
are new `judgment_ledger` rows, the tutor's retrieval manifest is new
descriptive metadata on new questions, and a suggestion is never a candidate,
target or filing. Replay and rebuild make zero model and embedding calls
(tested). Kill switch `source_retrieval.enabled = false` restores every
consumer's previous behaviour (tested for the library search byte for byte,
the tutor's spans with nothing recorded, the Quick Add selection, and no
suggestion). *(Review: the Quick Add test and two byte-identity gaps, the
plan's `scope_basis` and the ask responses' empty `suggested_learning_objects`,
were missing at this commit; both fields are now absent with the switch off,
and the Quick Add plan is tested.)*

## 4. Deviations from the plan and the prompt

1. **Injection instead of imports into the tutor and reader.** The new
   package needs Phase 5b's `PaidCalls`, fusion and query embedder, and the
   practice index sits above the tutor in the package graph, so a direct
   `tutor → source_retrieval → practice_index → … → tutor` import would add a
   cycle the "frozen cross-package cycles" contract forbids. The sidecar (the
   composition root) injects `TutorSpanProvider` and the LO suggester instead;
   `tutor_qa` and `reader_dialogue` gained optional parameters whose `None`
   default is today's behaviour. `lint-imports`: 12 contracts kept, no new
   exemption. Quick Add needs no paid piece and reads the FTS store directly.
2. **Production page-image retrieval is not built**; B4 decides whether it
   should be (P4). Section 6 has B4's result.
3. **The library search is never verified**: it is display, not grounding,
   and runs as the learner types. The LLM rewrite runs only on Enter, so typing
   never pays.
4. **Verification is an LLM listwise judge**, not an NLI model: the spec allows
   either, and the judge's verdicts are ledgered evaluation data.
5. **Quick Add uses keyword relevance only.** Dense unit ranking would need a
   paid query embedding, and the plan step is pure by contract (no model, no
   write before the single confirmation).
6. **B4's labels read the page's Marker text, not its image.** A text judge is
   cheaper and the same for every system, but it cannot credit a page whose
   relevant content Marker garbled; the review flags this bias (open question
   4).
7. **Copies.** One practice item of the `probability` copy
   (`pi_exercise_01kyn22qcffk7sae9ttxvz4j5n`) does not parse (multi-line YAML
   keys), so the vault refused to load; on the copy only it was moved to
   `fixtures-local/t6_set_aside/`. The tracked fixture is untouched. The
   `arxiv_v2` library has only one stored PDF (ten YouTube cue files and one
   arXiv HTML page), so B4 ran on `linear_algebra` (Axler) and `probability`
   (Blitzstein and two MIT problem sets).
8. **Reference scripts and two table walkers** learned about FTS5 shadow
   tables (above); `test_embedding_compare`'s exact-set assertion on `SUITES`
   became a subset check, because the CLI registers consumer suites into that
   module-level map (T1's B1/B3 will too).
9. `[source_retrieval].llm_price_per_million` is one price for both live
   routes, like `practice_index.rerank_price_per_million`.

## 5. Results on the fixtures-local copies

All runs used backup-API copies under `fixtures-local/` (`t6_probability`,
`t6_linear_algebra`, `t6_arxiv_v2`, plus `t6_probability_fakes` for the
fakes run), migrated to 175 on the copy, with embeddings and the T6 routes
enabled on the copy only (the config block in section 7). LLM roles ran on
OpenRouter `openai/gpt-4.1-mini`; embeddings on `qwen/qwen3-embedding-8b`
(4096) and, for B4, `google/gemini-embedding-2` (3072). Reports (aggregate
only) are in `fixtures-local/reports/`.

### 5.1 The T6 report: retrieval vs today's substring search

**With fakes** (required; no network): `fixtures-local/t6_probability_fakes`,
40 questions, fake writer and labeller, no source-block vectors. Complete:
`substring` 0.000 nDCG@10, `keyword` 0.988, `hybrid` 0.988, `hybrid_rewrite`
0.990; `meaning` reported unavailable ("414 of 414 blocks in scope have no
qwen/qwen3-embedding-8b vector; run `learnloop embeddings backfill
--record-kind source_block`"). The fake judge grades by word overlap, so this
proves the plumbing on real source data, not quality.

**Real**, 30 questions each, two label passes, pooled top 10:

| Copy (blocks) | System | nDCG@10 | Recall@10 | MRR@10 | seed hit@10 |
|---|---|---|---|---|---|
| probability (414) | substring (today) | 0.000 | 0.000 | 0.000 | 0.00 |
| | keyword | 0.719 | 0.689 | 0.971 | 0.88 |
| | meaning | 0.826 | 0.857 | 0.944 | 1.00 |
| | hybrid | 0.794 | 0.792 | 0.975 | 0.88 |
| | hybrid_rewrite | 0.801 | 0.823 | 0.958 | 0.84 |
| arxiv_v2 (4259) | substring (today) | 0.000 | 0.000 | 0.000 | 0.00 |
| | keyword | 0.494 | 0.405 | 0.752 | 0.79 |
| | meaning | 0.793 | 0.689 | 0.983 | 0.93 |
| | hybrid | 0.710 | 0.617 | 0.917 | 0.93 |
| | hybrid_rewrite | 0.814 | 0.712 | 0.967 | 0.90 |

Paired differences, nDCG@10 with 95% bootstrap intervals:

| Comparison | probability | arxiv_v2 |
|---|---|---|
| hybrid − substring | +0.794 [0.726, 0.849] | +0.710 [0.639, 0.777] |
| hybrid_rewrite − substring | +0.801 [0.742, 0.852] | +0.814 [0.773, 0.858] |
| hybrid − keyword | +0.074 [0.046, 0.105] | +0.215 [0.161, 0.283] |
| hybrid_rewrite − hybrid | +0.007 [−0.022, 0.037] | +0.105 [0.041, 0.183] |
| hybrid − meaning | −0.032 [−0.101, 0.032] | **−0.083 [−0.132, −0.037]** |
| hybrid_rewrite − meaning | −0.025 [−0.082, 0.031] | +0.022 [−0.023, 0.084] |

Label agreement between the two passes: probability 523 pairs, exact 0.71,
Cohen's κ 0.52 (binary κ 0.54); arxiv_v2 645 pairs, exact 0.71, κ 0.53
(binary κ 0.59). Question origins: probability 23 generated, 7 logged (2
reader, 3 practice, 2 feedback); arxiv_v2 29 generated, 1 logged reader.

Reading:
- Today's library search finds nothing for a question in natural language
  (it matches the whole query as one substring). Every T6 system beats it by a
  wide margin, on both copies.
- Dense retrieval carries most of the gain. Fusing it with BM25 without a
  rewrite is never better than dense alone and is worse on the large, mostly
  transcript library (arxiv_v2). With the rewrite, which is what production
  runs for a conceptual question, the hybrid is indistinguishable from dense
  alone on both copies. Production keeps the spec's hybrid: it also serves
  keyword-style searches (which these generated questions do not test, all
  being conceptual), exact phrases, and an incomplete index. Whether to drop
  the keyword list once the index is complete is open question 1.
- The rewrite helps where the library is large and noisy (+0.105 on arxiv_v2)
  and is neutral on the small textbook copy.

### 5.2 Benchmark B4: page images vs Marker text chunks

| Copy (pages, questions) | System | nDCG@10 | Recall@10 | MRR@10 | seed hit@10 |
|---|---|---|---|---|---|
| linear_algebra (Axler; 26 pages, 26 q, 25 scored) | text: qwen3-embedding-8b | 0.915 | 0.855 | 1.000 | 1.00 |
| | text: gemini-embedding-2 | 0.868 | 0.825 | 1.000 | 1.00 |
| | image: gemini-embedding-2 | 0.835 | 0.814 | 0.980 | 1.00 |
| | keyword | 0.816 | 0.784 | 0.940 | 0.92 |
| | hybrid_text | 0.892 | 0.837 | 1.000 | 0.96 |
| | hybrid_image | 0.901 | 0.865 | 1.000 | 1.00 |
| probability (Blitzstein + 2 MIT psets; 47 pages, 30 q) | text: qwen3-embedding-8b | 0.855 | 0.773 | 0.983 | 0.97 |
| | text: gemini-embedding-2 | 0.780 | 0.682 | 0.928 | 0.97 |
| | image: gemini-embedding-2 | 0.667 | 0.583 | 0.950 | 0.93 |
| | keyword | 0.801 | 0.713 | 1.000 | 0.97 |
| | hybrid_text | 0.865 | 0.783 | 0.983 | 1.00 |
| | hybrid_image | 0.824 | 0.736 | 0.983 | 1.00 |

| Comparison (nDCG@10) | linear_algebra | probability |
|---|---|---|
| hybrid_image − hybrid_text (the decision) | +0.008 [−0.007, 0.024] | **−0.041 [−0.060, −0.024]** |
| image − text, same model (gemini) | −0.033 [−0.080, 0.006] | **−0.113 [−0.153, −0.071]** |
| image (gemini) − text (qwen) | **−0.080 [−0.123, −0.049]** | **−0.188 [−0.230, −0.148]** |
| text (qwen) − keyword | +0.099 [0.050, 0.151] | +0.054 [0.026, 0.086] |

Label agreement: linear_algebra 401 pairs, κ 0.46; probability 546 pairs,
κ 0.45.

**Decision (P4, provisional; review F5): `page_image_default = false` on both copies.** Adding page
images to the text hybrid shows no gain on Axler and a significant loss on
the probability pages; a page image alone is worse than text chunks from the
same model, and much worse than qwen3 text. Text chunks stay the only PDF
representation, so production page-image retrieval is not built. Caveat:
labels read Marker text (section 4, item 6), which cannot credit a page whose
relevant content Marker lost; the questions are also written from Marker text.
A labeller that reads the page image is the fair test if the owner wants one
(open question 4).

### 5.3 Real calls and cost

Every call went through the app's own key loading; dry runs first; caps on
every run. Costs are OpenRouter's reported `cost` from `model_call_receipts`.

| Copy | Run | Calls | Input / output tokens | Billed |
|---|---|---|---|---|
| probability | source-block backfill (456 blocks) | 15 | 38,230 / 0 | $0.0005 |
| linear_algebra | source-block backfill (699) | 22 | 29,562 / 0 | $0.0003 |
| arxiv_v2 | source-block backfill (4259) | 134 | 114,646 / 0 | $0.0012 |
| probability | eval smoke with `deepseek/deepseek-v4.1-flash` (rewrite truncated at 600 output tokens: led to the 80-word, 1200-token rewrite) | 12 | 14,671 / 14,227 | $0.0115 |
| probability | eval smoke, 2 questions, gpt-4.1-mini (interface check) | 8 | 9,414 / 2,226 | $0.0072 |
| probability | T6 report, 30 questions | 104 | 179,854 / 39,308 | $0.1328 |
| arxiv_v2 | T6 report, 30 questions | 131 | 141,831 / 44,752 | $0.1265 |
| probability, arxiv_v2 | T6 report reruns (new comparisons) | 0 | all from checkpoints | $0 |
| linear_algebra | live deep library search (rewrite + query embedding) | 2 | 471 / 142 | $0.0003 |
| linear_algebra | live tutor spans (rewrite + query embedding + verification: 12 judged, 3 answers / 8 related / 1 unrelated, 4 picked, each on the question when read) | 3 | 1,703 / 530 | $0.0014 |
| linear_algebra | B4 (incl. 26 page images, 258 tokens each) | 166 | 583,174 / 32,780 | $0.2719 |
| probability | B4 (incl. 47 page images) | 210 | 900,687 / 43,663 | $0.4063 |
| **Total** | | **807** | | **$0.960** |

Verified external interfaces: OpenRouter's multimodal embedding input for
`google/gemini-embedding-2` (`{"content": [{"type": "image_url", "image_url":
{"url": "data:image/png;base64,..."}}]}`, billed as image tokens at
$0.45/M), and gpt-4.1-mini structured output through the bounded
`openrouter` transport for all four T6 roles.

## 6. Tests and gate

New tests (all fakes): `test_source_block_fts.py` (triggers, replace path,
rebuild, query sanitizing, stemming, scoping, prefix, header resolution, role
and shadow tables, umbrella rebuild with no model or embedding client),
`test_source_retrieval_search.py` (recipe outside the default backfill, recipe
text, dense maths pinned to `retrieve()`, incomplete index, deep search and
query cache, conceptual gate, metered-without-price skip, failed rewrite,
typing search vs `instr`, kill switch byte-identity, teaching-scope assessment
exclusion, Quick Add ranking, embeddings-off and width guards),
`test_source_retrieval_tutor.py` (retrieved-then-verified spans, assessment
material never reaches the verifier or the tutor, citations inside verified
spans, ledger rows, F4/F11 mapping unchanged, fallback to linked spans,
expected-answer withholding, kill switch records nothing, failing provider,
ledger-served repeat verification, labelled suggestions, the reader question
records them and promotion names them, switches),
`test_source_retrieval_suites.py` (registration, dry run writes nothing, the
report vs substring with resumable checkpoints, dense unavailable without a
backfill, missing labels, B4 with real pypdfium2 rendering and a fake
multimodal embedder, the bar, CLI), `test_sidecar_source_retrieval.py`,
`test_source_retrieval_cli.py`, image-input tests in
`test_openai_embedding_client.py`, the `source_block/text` pin in
`test_embedding_recipe_hash_pins.py`, and `searchBasis.test.ts`.

Gate (final commit; `uv sync --extra dev --extra mobile`, `uv pip install
pypdfium2`):

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7906 passed**, 0 failed, 0 skipped (225.7 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7822 deselected (62.2 s) |
| `npm install`, `npm run typecheck`, `npm test` (apps/learnloop-tauri) | install ok; typecheck clean; 24 files, **106 tests passed** |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated; validator `errors: []` (schema head 175, 292 table notes, 631 config leaves, 3832 wikilinks checked) |

The first full run on this branch failed 8 tests, all fixed before the gate:
the SQL-owner registry (the new store), the CLI help snapshot, and six
debug-advance, goal-series and scoreboard tests whose table walkers looked up
a role for FTS5 shadow tables (section 2.1).

## 7. Owner-run commands

Runs meant for the live vaults are the owner's. Open each vault once with this
branch (any `learnloop` command) so migration 175 builds its keyword index;
planning commands never migrate.

**Configuration** (the vault configs predate Phase 1). Add to the vault's
`learnloop.toml`, merging into existing tables:

```toml
[ai.routing]
embedding = "openrouter_embedding"
# Optional: unset, the four T6 routes follow ai.active_provider (Codex).
source_query_rewrite = "openrouter_t6"
source_rerank = "openrouter_t6"
source_query_writer = "openrouter_t6"
source_relevance_judge = "openrouter_t6"

[ai.providers.openrouter_embedding]
type = "openai_embedding"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[ai.providers.openrouter_t6]   # what the copies used; any bounded chat profile works
type = "openrouter"
model = "openai/gpt-4.1-mini"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"

[embedding]
enabled = true
backfill_enabled = true

[source_retrieval]
llm_price_per_million = 1.6   # only for metered live rewrite/verification routes
```

**1. Source-block backfill** (paid; dry-run first). The default backfill never
includes it; name it, alone:

```bash
uv run learnloop embeddings backfill --vault <vault> --record-kind source_block --dry-run
uv run learnloop embeddings backfill --vault <vault> --record-kind source_block \
  --max-candidates 5000 --max-calls 200 --max-tokens 2000000 --max-cost-usd 0.05
```

On the copies: 456, 699 and 4259 blocks, estimated $0.002, $0.002 and $0.010;
OpenRouter billed $0.00046, $0.00030 and $0.0012. Reruns embed only new or
changed blocks.

**2. The T6 report** (retrieval vs today's substring search; paid labels):

```bash
uv run learnloop embeddings compare --vault <vault> --suite source_retrieval --dry-run \
  --max-cases 30 --price-per-million 1.6 --output fixtures-local/reports/t6-eval
uv run learnloop embeddings compare --vault <vault> --suite source_retrieval \
  --max-cases 30 --price-per-million 1.6 --max-tokens 10000000 --max-cost-usd 10 \
  --max-calls 400 --output fixtures-local/reports/t6-eval
```

The caps admit the harness's conservative plan (UTF-8 bytes as tokens, the
output price for every token, every system's full pool): about $9 planned for
30 questions, against $0.13 billed on the probability copy. Without step 1 the
`meaning` system is reported unavailable and the hybrids are keyword only.

**3. Benchmark B4** (page images vs text chunks; paid):

```bash
uv run learnloop embeddings compare --vault <vault> --suite b4 --dry-run \
  --max-cases 30 --max-items 60 --price-per-million 1.6 --embedding-price-per-million 0.45 \
  --output fixtures-local/reports/t6-b4
uv run learnloop embeddings compare --vault <vault> --suite b4 \
  --max-cases 30 --max-items 60 --price-per-million 1.6 --embedding-price-per-million 0.45 \
  --max-tokens 30000000 --max-cost-usd 40 --max-calls 1500 --output fixtures-local/reports/t6-b4
```

`--embedding-price-per-million 0.45` is Gemini Embedding 2's image price, used
as an upper bound for every candidate model. Add `--model` (repeatable) to
compare other text models; the image system needs `google/gemini-embedding-2`.
Needs pypdfium2 (`uv pip install pypdfium2`) and the PDFs' stored originals.

**4. Try it.**

```bash
uv run learnloop sources search "why is the variance of a sum the sum of variances" --vault <vault> --deep
uv run learnloop sources suggest-lo --vault <vault> --extraction <ext_id> --span <span_id>
```

In the app: type in the library search (keyword), press Enter (meaning and the
rewrite); ask the tutor during practice (verified spans, citations).

## 8. Files and migrations

**Migration:** `migrations/175_source_block_fts.sql` (`source_block_fts`,
DERIVED, three triggers on `source_document_blocks`). It takes the next free
number on this base (174 was head); T1, R0 and the stuck prompt also claim
175-178, so whichever merges later renumbers it and regenerates the head
fixture (`fixtures/migration_head_175`).

**Added:** `src/learnloop/source_retrieval/` (`__init__`, `b4`, `bench`,
`contracts`, `corpus`, `dense`, `evaluation`, `library`, `queries`,
`recipes`, `search`, `suggest`, `suites`, `tutor`, `verify`),
`src/learnloop/db/stores/source_block_fts.py`, `src/learnloop/cli/sources.py`,
`apps/learnloop-tauri/src/screens/reader/searchBasis.ts` (+ test), the test
files in section 6, `tests/source_retrieval_fakes.py`.

**Changed:** `ai/providers/openai_embedding.py` (image input), `ai/routing.py`,
`config/schema.py`, `config/template.py` (snapshots), `params/parameter_registry.py`,
`db/table_roles.py`, `substrate/rebuild_orchestrator.py`,
`ops/debug_time_store.py`, `goals/goal_series_store.py` (shadow tables),
`ops/embedding_compare.py` (suite Markdown hook), `ops/pf_calls.py` (embed token
bound), `practice_index/query_vectors.py` (`record_kind`),
`content/pipeline/quick_add.py`, `tutor/tutor_qa.py`, `tutor/promotions.py`,
`reader/reader_dialogue.py`, sidecar `handlers/reader.py` and
`handlers/tutor_qa.py`, `cli/embeddings.py`, `cli/__init__.py`, the frontend
`client.ts`, `dto.ts`, `ReaderScreen.tsx`, both reference scripts and the
regenerated references, the CLI help snapshot, and the head-fixture tests.

## 9. Open questions for the owner

1. **Hybrid vs dense alone.** On both copies dense retrieval alone is as good
   as the production hybrid with the rewrite, and better than the hybrid
   without it (significantly on arxiv_v2). Keep the spec's hybrid (robust to
   keyword searches and an incomplete index), or use dense alone whenever the
   scope's index is complete? A keyword-style query set would settle it.
2. **Tutor latency.** A conceptual tutor question now waits for up to three
   extra calls before the answer: the rewrite, a query embedding and the
   verification (on Codex when the routes are unset). Measured on the
   linear_algebra copy with gpt-4.1-mini: rewrite 1.8 s, query embedding
   0.8 s, verification 3.9 s, about 7 s in all. Keep both live by default
   (`query_rewrite`, `tutor_rerank`), or route them to a faster model?
3. **Accepting a suggestion.** Reader questions on unmapped spans now carry a
   labelled nearest-LO suggestion, and the promotion error names it, but the
   Ask overlay has no picker to promote under it. Add one?
4. **B4's judge reads Marker text.** Page images lost clearly on these copies.
   If the owner suspects Marker garbles the pages that matter most, a
   multimodal labeller pass (reading the rendered page) is the fair rematch.
5. **Short transcript blocks.** Transcript blocks are single caption lines;
   verified spans from them are fragments. Embed (and show) small windows of
   adjacent blocks for transcripts?
6. **Label agreement is moderate** (κ 0.45–0.53 between two framings of the
   same model). Owner labels on a sample would calibrate it; they stay
   optional.
