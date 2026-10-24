# Local contextual source retrieval: pplx v2 9B documents, a distilled query student, a hosted Voyage fallback (v1)

**Status:** draft for owner review, 2026-10-24. Branch `experiments/e1-local-v2`, base `eec2dd88d` (migration head 217). This is a specification only. No code changed, no model was loaded, no paid or model call was made and nothing was downloaded to write it. Public web pages were read for §3; each claim cites its URL and says what the page did not settle.

**Basis:** [the experiment spec](spec_contextual_source_embeddings_experiments_v1.md) (§7 adoption, §8 E1, §9 deferred work, D6); [the E1 harness review](../reviews/experiments-e1-local-v2.md) (model facts, the worker, the GPU runs); [the E1 report](../reviews/experiments-e1-report.md) (plan `e1_eaa8d20e4af40e3f`, aggregates only); [the embedding consumers spec](spec_embedding_consumers_v1.md); [the storage/sync spec](spec_storage_sync_v1.md) (the hub model); [the algorithm-change playbook](../algorithm-change-playbook.md).

## 0 The owner decision and what it does and does not change

**Owner, 2026-10-24 (verbatim):** "Let's have learnloop use local pplx v2 (distill into 0.9 version for retrieval similar to how voyage handles it in their ecosystem) since its free and a fun research extension, but allow fallback to the hosted setup of Voyage."

This is the **explicit D6 amendment** that the experiment spec's §7 and D6 required before a second production source embedding space could exist. It is recorded in that spec's amendment log (§12) with a pointer here.

**What the owner knew when deciding.** E0/E1 showed **no quality gain**:

- local v2 (grouped) against Qwen R1: **+0.000 [−0.037, +0.037]** CE@10;
- against the best frozen finalist, hosted Voyage `voyage-context-4` grouped: −0.017 [−0.074, +0.037].

Both figures are from the primary development slice: n = 58, 5 families, paired and family-clustered. **The motivation is cost and research value, not quality.** Local inference costs no provider bill, and building the student is the research extension.

**The decision's scope and limits.**

1. **It replaces §7's adoption bar for this space only.** The §7 bar asked for a ≥ 5-point gain and a blind-answer gain. For this space it becomes a **non-inferiority** bar (§9), because the case for adoption is cost, not quality. Every other §7 rule still holds for any other space.
2. **Source retrieval only.** The space serves `source_block` retrieval and its queries. Item stems, the practice index, diagnosis split retrieval, PF freshness, graph nomination and map neighbours stay on `qwen/qwen3-embedding-8b`, under the October 11 one-model decision, until the owner extends this amendment (Q12).
3. **The model is a preview.**
   - Its card says weights, embeddings and interface "may change in later versions without backward compatibility" and that its embeddings "should not be mixed with embeddings from a future release" ([card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview)).
   - So the space is pinned to revision `e2c06a779d45e8db53066735be1b98ffe3412ca3`. Vectors are **never mixed** with another revision or release.
   - A model change, by revision, precision or software epoch (§4.2), is a new space. It needs a full re-index and a newly trained student.
4. **Nothing becomes ground truth.** Embeddings nominate; verifiers, policy checks and citation validation keep authority (experiment spec §1).
5. **E1 itself has no verdict.** Its decision is `no_verdict`: the supplementary labels' κ was 0.354 (linear algebra, n = 35) and 0.575 (probability, n = 31), under the 0.60 gate. The owner's decision does not need an E1 verdict. The switching gates in §9 do need a label of record, though (Q3).

## 1 What exists today (verified on this branch)

| Piece | Today | Consequence |
|---|---|---|
| Production model | `qwen/qwen3-embedding-8b` via OpenRouter, 4096-d, `$0.01`/M (`config/schema.py` `EmbeddingConfig`, `ai/providers/openai_embedding.py`) | The incumbent. `embedding.enabled` and `backfill_enabled` default false; `backfill_sources_on_extract` queues a capped source backfill after each extraction (`source_retrieval/source_vectors.py`) |
| Route | `ai/routing.py`: the `embedding` task accepts only an explicit `openai_embedding` profile and is refused while `embedding.enabled` is false. `LEARNLOOP_AI_PROVIDER` does not override it (CLAUDE.md) | T1 already makes embeddings an explicit opt-in route that never falls back to a chat provider. A Voyage profile has to keep that property |
| Store | `embedding_vectors` (migration 166; role `WORKFLOW`): `(record_kind, record_id, field, content_hash, model_id, task_prefix)`, FP16 blob of `2·dims` bytes; `get_vector_by_content` reuses a vector of identical recipe text across records | **Reuse by content is wrong for contextual vectors.** The same central text in a different window gives a different vector. §4.3 keys contextual vectors by their window |
| Dense index | `source_retrieval/dense.py`: an extraction is searched densely only when every embeddable block has a vector for `embedding.model`; status `ready`/`partial`/`incomplete`; mean-centred cosine; per-process cache keyed by db, model, manifest and vector fingerprint | One model per vault today. §5 adds a space resolver above it |
| The seam | `source_retrieval/search.py` `search_spans()` → `load_dense_index()` + `queries.embed_query_texts()` → `practice_index.query_vectors.embed_queries()` → `ready_client_for_task("embedding")` | **Every source consumer goes through `search_spans`:** `find_sources`, `TutorSpanProvider`/`tutor_pool`, `library_ask`, `compare`, `reader_tutor`, `passage_cues`, `instructional/sources.py`, `instructional/exercises.py` and the MCP server. Changing the space behind this seam changes them all at once (§6) |
| E1 worker | `experiments/contextual_embeddings/e1/worker.py`: a standalone batch process in a separate env (Python 3.12, torch 2.14.0, transformers 5.18.0), launched in its own `systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0`, with start refusals, a 1 s sampler, smoke checks, encode, unload and exit | It is the production indexer's starting point. It **moves** into a production package and is not imported from `experiments` (the import-linter contract `experiments-stay-outside-production`) |
| E0 Voyage adapter | `experiments/contextual_embeddings/adapters.py` `VoyageContextualAdapter`: `POST /v1/contextualizedembeddings`, nested inputs, `input_type` `document`/`query`, 1024-d float, admission at $0.12/M (never assuming the free tier) | It is the fallback adapter's starting point, under the same rule: it moves, it is not imported |

**Measured on the 5090 (E1 run 03, BF16, pure-torch linear-attention fallback, [report](../reviews/experiments-e1-report.md)):**

- load 24.7 s; device memory 16.85 GB after load, 18.43 GB reserved at peak;
- anon RSS 1.96 GiB; host MemAvailable never below 20.7 GB;
- 734 documents (87,179 tokens) at per-document p50 0.019 s;
- profile windows of 1,351, 2,926 and 5,603 real tokens took 0.149 s, 0.310 s and 0.65 s. A true 8,192-token profile has not been run;
- batch-one query latency p50 0.018 s, p95 0.027 s, with the model resident;
- clean unload (0 bytes left).

The 9B is fast once loaded. The 25 s load, and the 17–18 GB it holds on a GPU shared with the desktop, are why it cannot serve interactive queries without residency.

## 2 Architecture in one picture

```text
                 indexing (batch, deferred)                        query time (interactive)
extraction ──► local_index job ──► 9B worker (own scope,          search_spans(query, scope)
  done          (batched, GPU checks,   load → encode → unload)         │
                 flock)                        │                  space resolver (§5)
                                               ▼                   │        │          │
                         <vault>/.learnloop/vector-cache/       local    voyage     qwen (incumbent,
                         <space_id>.sqlite  (derived, §4.4)     space    fallback   until retired)
                                                                  │        │          │
  extraction ──► voyage backfill (opt-in, capped) ──► state.sqlite │     Voyage API  OpenRouter
                 qwen backfill (today's job)    ──►  embedding_vectors  (query)     (query)
                                                                  │
                                                     query student (own scope, GPU or CPU,
                                                     lazily started, idle exit; §7)
```

**One query uses one space.** Scores from two spaces are never compared or mixed in one dense list. The resolver picks the space per query (§5) and the receipt names it.

## 3 Research answers

### 3.1 How Voyage's ecosystem does asymmetric retrieval

- **One shared space across four sizes.** The Voyage 4 family has `voyage-4-large` (mixture-of-experts), `voyage-4`, `voyage-4-lite` and the open-weight `voyage-4-nano`, and they "produce compatible embeddings" ([Voyage 4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/)). The docs say "All embeddings created with the 4 series are compatible with each other" ([embeddings docs](https://docs.voyageai.com/docs/embeddings)). The recommended pattern is to index documents once with `voyage-4-large`, query with a smaller model, and later change the query model without re-embedding.
- **The small model is very small.** `voyage-4-nano` has 180M non-embedding plus 160M embedding parameters (about 0.34B). It is Apache-2.0 and Qwen3-based (bidirectional, `VoyageQwen3BidirectionalEmbedModel`), supports 2048/1024/512/256 Matryoshka widths, and uses fixed query/document prompts ([nano card](https://huggingface.co/voyageai/voyage-4-nano)). Vespa reports nano queries "in single-digit milliseconds on CPU" against `voyage-4-large` documents ([Vespa](https://blog.vespa.ai/asymmetric-retrieval-spend-on-docs-queries-for-free/)).
- **What Voyage does not publish.** None of these pages describes how the shared space was trained (distillation, alignment or otherwise). None gives asymmetric-versus-symmetric numbers in text: the blog's are in charts and a linked spreadsheet.
- **`voyage-context-4` is not documented as part of the shared space.** The contextual-chunk docs ([docs](https://docs.voyageai.com/docs/contextualized-chunk-embeddings)) and MongoDB's release post ([post](https://mongodb.com/company/blog/product-release-announcements/voyage-context-4-stop-worrying-about-chunking-with-our-best-performing-model)) only call it "a drop-in replacement for voyage-context-3". So the fallback (§8) queries `voyage-context-4` with itself (`input_type="query"`), exactly as E0 did. It does not query with `voyage-4-lite` or nano.
- **What "0.9" maps to.** Voyage's pattern is a large document model plus a smaller query model in the same space. For us that is a sub-1B query student trained into the 9B's space. The nearest size is **`Qwen/Qwen3.5-0.8B`, 873,438,784 parameters (≈ 0.9B)**, Apache-2.0, with a `-Base` variant ([HF API](https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B)). It is the same Qwen3.5 family and 248,320-token vocabulary as the teacher (E1 review §1). This spec reads "0.9" as that size class (Q9 confirms).

### 3.2 Does Perplexity publish a small pplx-embed v2 model in the same space?

**No, not for the contextual model.**

- Perplexity's Hugging Face listing has three v2 embedding models: `pplx-embed-v2-context-9b-preview`, `pplx-embed-v2-late-9b` and `pplx-embed-v2-late-0.6b` ([API listing](https://huggingface.co/api/models?author=perplexity-ai&limit=100); the [pplx-embed-v2 collection](https://huggingface.co/api/collections?owner=perplexity-ai) holds exactly these three).
- The context card names no smaller model, no planned query model and no hosted endpoint. It says the model "isn't deployed by any Inference Provider".
- **The late pair is not our space.** Its card says "The 0.6B and 9B models share an embedding space, allowing the 0.6B model to query an index built with the 9B model". Both were "distilled from an internal 18B ColBERT teacher". It produces 128-d vectors per token, scored by MaxSim ([late 0.6B card](https://huggingface.co/perplexity-ai/pplx-embed-v2-late-0.6b)). That is a separate token-vector index and does not mention the context model. It stays the deferred alternative of experiment spec §9.
- `pplx-embed-v1-0.6b` and `pplx-embed-context-v1-0.6b` are v1, not the v2 space.

So, as the brief said for this case, **we train our own query student**. If Perplexity later ships a small model in the v2 context space, it is preferred over our student, subject to the same gate (§10, successor S-b).

### 3.3 The distillation evidence we build on

- **[NanoVDR](https://arxiv.org/abs/2603.12824).** A frozen 2B document teacher with a 69M text-only query student. "Pointwise cosine alignment on query text consistently outperforms ranking-based and contrastive alternatives". The student retains 95.1% of teacher quality, with 50× lower CPU query latency and under 13 GPU-hours of training, using pre-cached teacher query embeddings and no document processing. Its domain is visual documents, so these are not forecasts for mathematics.
- **[Query Encoder Distillation via Embedding Alignment](https://aclanthology.org/2023.sustainlp-1.23/)** (Wang and Hong, SustaiNLP 2023). It establishes the method as a strong baseline. Its abstract page was read; its body was not.
- **[EmbedDistill](https://arxiv.org/abs/2301.12005)** (geometric matching with score distillation) and **[Learning Query Encoders Can Be Hard Even When Vector Retrieval Is Geometrically Easy](https://arxiv.org/abs/2610.02749)** are carried from experiment spec §3 and were not re-read here. The second is why §9 tests unseen sources and Reader deictic queries, rather than trusting teacher-space geometry.

## 4 The local space: identity, indexing, storage

### 4.1 Document indexing on the 9B: batch jobs, no residency

- **Job kind.** A completed extraction (an import, a re-extraction, a page repair) queues a `local_source_index` job for its source's current extraction. This mirrors today's `source_embedding_backfill`, including the `backfill_owed` survival rule (a retry re-queues an owed index). The job runs only while `embedding.local.enabled` is true.
- **Batching.** Jobs accumulate. One worker process takes every owed extraction across vaults: it loads, smoke-checks, encodes everything, unloads and exits. The 25 s load is paid once per batch. The worker may start when:
  - the start checks of §7.2 pass and the locks are free;
  - the batch is ≥ 15 minutes old or ≥ 1 source, whichever comes later, so a burst of re-extractions is not loaded one by one;
  - or the owner forces it (`learnloop embeddings local index --now`).
- **Status.** An index job that cannot start is `waiting_for_gpu` (with its reason, e.g. `host_memory 10.5 GiB < 14`), never `failed`. Coverage for that extraction stays partial, and the resolver uses another space meanwhile (§5).
- **Units and windows.**
  - **Units are production blocks**, the `source_block/text` recipe. They are not E0's merged units, because production ranks blocks.
  - **Grouped windows** use E0's corpus rules, moved into the production package: at most 4,096 tokens including markers, section boundaries, no overlap, every block exactly once, deterministic tie-breaks.
  - **Windows never cross exam, held-out, solution or assessment-lane boundaries**, and withheld blocks are not joined across (experiment spec §4.2).
  - Furniture and blocks under 20 non-whitespace characters are skipped as today.
  - An oversized block is split with offsets; its vector is the token-weighted mean of its parts, recorded as `split_mean`.
- **Variants.** Phase 1 encodes **both** `grouped` (the E1-selected arm) and `singleton` (one block per document), because E1 split by copy:
  - linear algebra CE@10 0.862 grouped against 0.724 singleton;
  - probability 0.793 grouped against 0.862 singleton;
  - pooled context gain +0.034 [−0.069, +0.182].

  At ~2 minutes a book the second variant is cheap. Phase 3 keeps one by a rule fixed now (§9.3) and drops the other.
- **Software stays the E1 worker's.** BF16 with shards loaded straight to the GPU, the FP32 projection restored from its checkpoint and checked equal, the tokenizer loaded from the model directory, offline flags and a socket block. The remote code is pinned by SHA-256 and anything else is refused. Smoke checks run before every batch.
- **Every batch encodes the fixed public canary set.** If any canary cosine to the space's stored canaries is < 0.999, nothing is stored and the space is marked `epoch_drift`. The owner then chooses between re-indexing under a new epoch and pinning the old environment back.
- **Cost of a book (estimate).** Today's config comment puts a 4,000-block book at about 1M recipe tokens. At E1's measured ≈ 8.6k tokens/s on 5.6k-token windows, one variant takes ≈ 2 minutes plus the 25 s load, and both ≈ 4 minutes. Measure it on the first full book; the 8,192-token profile is still owed (Phase 0).

### 4.2 Identity

The space follows experiment spec §4.3. Every field below is part of the id, so a change to any of them is a new space:

```text
space_id = hash("local", repo="perplexity-ai/pplx-embed-v2-context-9b-preview",
                revision="e2c06a779d45e8db53066735be1b98ffe3412ca3", code_sha256s,
                precision="bf16", fp32_modules=["contextual_projection"],
                software_epoch=(torch, transformers, cuda),        # e.g. 2.14.0+cu130, 5.18.0, 13.0
                variant="grouped"|"singleton", window_rule="w4096-section-policy-v1",
                recipe="source_block/text v?", dims=2048, output="int8_valued",
                score_transform="l2_normalize_cosine")              # ordinary cosine, as E1 measured
vector_key = hash(space_id, extraction_id, window_block_ids_and_offsets,
                  target_block_id, policy_fingerprint)
query_encoder_id = hash(space_id, encoder="teacher"|"student:<checkpoint_sha256>",
                        query_method="[Q] prefix, mean pool", precision, device_class)
```

- **The query encoder is not part of `space_id`.** A new student does not invalidate documents; that is the point of the design.
- **A teacher change does invalidate the student.** The student is trained for one `space_id`, and a teacher change retires it.
- **Scoring transform.** E1 measured ordinary cosine. Production's mean-centring (`dense.py`) is the Qwen space's transform. The local space records `l2_normalize_cosine`, and centring is not applied unless a Phase 3 measurement prefers it.

### 4.3 Invalidation

A contextual vector depends on its whole window. Each of these invalidates **every vector of the affected windows**:

- a re-extraction;
- a new held-out or exam mark on any block of the window;
- a policy fingerprint change;
- a split-rule change.

The resolver checks the current policy before scoring and rejects stale rows. While a rebuild is pending, the extraction is uncovered in that space and is never served from stale vectors.

### 4.4 Storage: derived local state outside `state.sqlite`

**Recommended (Q11):** local vectors live in a per-vault cache, `<vault>/.learnloop/vector-cache/<space_id>.sqlite`.

- `.learnloop/` is already gitignored, and it already holds the disposable source cache.
- Rows hold the vector key, block id, extraction id, the int8-valued vector as FP16 (exact for values in [−127, 127]), a canary digest and the job id. Like `embedding_vectors`, the vector is stored as `2·dims` bytes.
- A 4,000-block book takes ≈ 16 MB per variant (2048 × 2 bytes per block).

Why there rather than `embedding_vectors`:

1. **They are derived.** A rebuild costs ≈ 2–4 minutes of local GPU a book and no money, given the pinned model files. That is a cache, not a paid input. Keeping them out of `state.sqlite` keeps them out of snapshots, out of the table-role registry (no new `DERIVED` replayer is owed) and out of the tracked fixture databases in the public repository (§11).
2. **Contextual keys differ.** Reuse by content (`get_vector_by_content`) must never apply to them, and a separate store makes that structural instead of a flag.

The cache is opened read-only by the resolver and written only by the index job. It is copied, when ever needed, through `learnloop.db.copies` (backup API), never `shutil`. A missing or corrupt cache counts as uncovered and is rebuilt; it is never repaired in place. `learnloop doctor` reports the cache per space: rows, coverage, epoch and canary status.

**Registry.** A small `embedding_spaces` table in `state.sqlite` records each space a vault has used: id, kind (`local`/`hosted`), the pins above, status (`active`, `fallback`, `incumbent`, `retired`, `epoch_drift`), and created/retired times. Role `WORKFLOW`: it is mutable and preserved across replay. This needs one migration (the next free number at implementation, `ls migrations/`), its classification in `db/table_roles.py`, the migration-head fixture procedure of CLAUDE.md, and the reference regeneration. Receipts cite the space id, so a retired space stays interpretable.

### 4.5 Replay and the playbook

- **No algorithm successor is minted by this spec.** Source retrieval does not change persisted meaning: a lookup is not an exposure (RW1c), replay never re-runs retrieval, and `source_tool_calls` and receipts record what was found.
- **Every retrieval result records** `space_id`, `query_encoder_id`, the resolver's choice and its reason (`space_selection`), alongside today's `dense` description.
- **Where a successor is owed.** If a consumer turns retrieval output into persisted meaning, switching that consumer's space mints a successor with a kill switch, under the playbook's 2026-10-17 rule ("a change to which items are served … is a successor … even when replay is unchanged"). Examples: teacher placement anchors, AD reading opportunities, figure or library offers recorded as admissions. Phase 3 lists each consumer and states which applies (§6).

## 5 The space resolver (the one new seam)

`search_spans()` asks one function, `resolve_source_space(vault, repository, scope, deadline)`. It returns the dense index and the query encoder to use, or a typed refusal. Its order is fixed and recorded on every result:

1. **The default space**, when its index is `ready` for the whole scope **and** its query encoder answers within the remaining time box.
   - The query time box is the existing one: the deadline `search_spans` already carries.
   - A cold student start counts against it. If the student is starting, the query waits at most `min(time left, 3 s)` before moving to step 2.
2. **The fallback space** (`voyage_context_4`), when it is enabled and its index is `ready` for the whole scope. Its query costs a Voyage request under the existing query caps and receipts (§8).
3. **The incumbent** (Qwen), while not retired, when `ready`.
4. **The best partial index**, by today's `partial` rule (its complete extractions rank densely; the rest go to keyword), from the default space first.
5. **Keyword only.** This is today's `disabled`/`incomplete` behaviour.

**Rules.**

- **A complete space beats a partial one.** A new import still waiting for the GPU therefore moves the query to Voyage or Qwen rather than leaving that source to keyword search.
- **Never mixed.** Two spaces' scores are never fused, and the RRF keyword widening stays as today. A test pins this: a mixed-space list is refused.
- **The rewrite query uses the chosen space too.** It is embedded by the same space's encoder.
- **Caching.** Query vectors are cached by `(query_encoder_id, text)`: student queries in the vector cache, hosted queries in `embedding_vectors` as today.
- **Fallback is visible.** `space_selection.reason` is one of:
  - `default`;
  - `default_incomplete`;
  - `student_unavailable` (not trained, failed health, or refused by memory checks);
  - `student_timeout`;
  - `local_disabled`;
  - `epoch_drift`;
  - `fallback_disabled`.

  `learnloop doctor` and the result's on-demand detail show it in plain words (frictionless by default, glass box on demand).

## 6 Consumers

Every consumer reaches the resolver through `search_spans`, so none needs its own integration. Each is listed with what changes for it.

| Consumer | Path | Change | Successor? |
|---|---|---|---|
| Reader Ask (`find_sources`, five intents) | `find_sources` → `search_spans` | Space per query; verification (900-char views) and paging unchanged | No (lookup, not exposure) |
| Tutor grounding | `TutorSpanProvider` / `tutor_pool` / `reader_tutor` | Same; the T6 time box covers the student's cold-start rule | No |
| Library ask / compare (RW4a/RW4d) | `library_ask`, `compare` | Same; a comparison across sources uses one space for all of its searches | No, unless a library offer is recorded as an admission (check at Phase 3) |
| Teacher grounding (`retrieve_source`, spec_teacher_v1, not yet landed) | `TutorSpanProvider` / `find_sources` | The teacher spec already says "E1 … competes to sit behind" this seam | **Yes, if** placement or plan anchors are persisted from retrieval: then that consumer's switch is a successor |
| Passage cues, instructional sources and exercises, MCP `find_sources` | `search_spans` | Same; MCP's worst-case cost admission charges the fallback's query bound, since a local query is $0 | No |
| Practice index (`find_practice`, practice_item / practice_query) | Its own vectors through `practice_index.query_vectors` | **Unchanged: stays on Qwen** (§0.2). Items are short, non-contextual, and not in the E0/E1 bank | Not applicable (Q12) |

## 7 The query student, and GPU and memory safety

### 7.1 The student (Phase 2)

**Goal.** A query encoder of ≈ 0.6–0.9B parameters whose vectors land in the 9B's 2048-d space. The teacher's documents stay frozen.

**Candidates.** The screen trains one seed each, cosine alignment only, then picks on development:

| Base | Size | Why |
|---|---|---|
| `Qwen/Qwen3.5-0.8B-Base` | 873M | The "0.9" ([HF](https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B)): same family and tokenizer as the teacher; Apache-2.0. Causal and multimodal: load text-only, turn off causal masking (the teacher has `is_causal: false`), and test both mask settings |
| `perplexity-ai/pplx-embed-v1-0.6b` | 596M | Already a bidirectional embedding model from Perplexity's v1 lineage; MIT ([HF](https://huggingface.co/api/models/perplexity-ai/pplx-embed-v1-0.6b)) |
| `Qwen/Qwen3-Embedding-0.6B` | 596M | A strong general embedding start; Apache-2.0 ([HF](https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B)) |
| Projection-only baseline | the base plus a `Linear(d→2048)` | Experiment spec §9's first rung: base frozen, only the map trained |

Every student ends in a `Linear(hidden→2048)` and is compared after L2 normalization. Its output is FP32 and is not rounded to int8. The teacher's int8-valued query vector, normalized, is the target.

**Data, all local.**

1. **Synthetic queries from permitted sources.** An LLM writes 8–12 varied questions per passage over the owner's local books in the vaults: the intents of `find_sources` (explain, remediate, alternative, worked example, compare), deictic Reader shapes with a selection, definition and theorem lookups, and paraphrases with no shared vocabulary.
   - The prompt sees only permitted text: no exam, held-out, solution or assessment-lane material (experiment spec §4.2).
   - It records `source_family`, `passage_ids` and the intended supporting blocks.
   - Generator: Q8.
   - Nested budgets of 2k/10k/50k queries make the learning curve (spec §9).
2. **Teacher targets.** A teacher batch job (§4.1's worker in query mode) encodes every training query with `encode_queries` (`[Q]`, mean pool). At E1's 18 ms per query, 50k queries take ≈ 15 minutes plus load.
   - The same job stores each query's teacher top-50 over the local document index, from cosine scores, for the ranking losses.
   - **Teacher and student are never resident together.**
3. **Real queries.** The owner's logged Reader and tutor queries, read from vault copies, can be added after deduplication (below). They are learner text and stay local. They also give the best measure of deictic shapes.

**Leakage rules** (experiment spec §4.2, §9):

- The frozen E0/E1 bank's questions, paraphrases and gold supports never enter training, generation prompts or hard-negative mining.
- A synthetic query within cosine 0.90 of any bank query (by the teacher) or with 5-gram overlap above 0.5 is dropped, and the count is reported.
- Splits are by source family. A held-out family, never trained on, is the unseen-source test. Where a second subject exists, a held-out subject is the unseen-subject test.

**Losses, in the order spec §9 sets.**

1. Projection-only.
2. Cosine alignment, `1 − cos(student(q), teacher(q))`.
3. Alignment plus listwise score distillation: KL between the teacher's and the student's softmax over the teacher's top-50 documents, temperature fixed on development.
4. Alignment plus a **multi-positive** contrastive term. Every required support of the query's intended set is a positive, so no required support is dropped in favour of one easy answer span. In-sequence same-source hard negatives are mined from training families only.

The chosen recipe is then run on ≥ 3 seeds.

**Training budget (5090, within the memory caps).**

- A full fine-tune of 0.87B in BF16 with FP32 AdamW states is ≈ 14 GB, plus small activations for queries of ≤ 512 tokens. That fits the 20 GiB device target.
- Gradient checkpointing, or freezing the lower half, is the fallback if a measurement needs it.
- Host side: the same 12G scope and floors as the worker (§7.2); data loaders run in-process with ≤ 2 workers.
- Wall-time estimate: minutes per run at 50k queries × 3 epochs. The cap is **≤ 6 GPU-hours in total for Phase 2**: teacher target jobs, the screen, recipes, seeds and failed runs, all metered by a production copy of E1's GPU meter.

**Serving.**

- The student runs in the separate env as a **query process**, which the sidecar starts lazily on the first local query:
  - `systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0`;
  - JSON over a Unix socket in `$XDG_RUNTIME_DIR`;
  - offline flags and a socket block, so it has no network;
  - it exits after 20 idle minutes.
- **Device:** the GPU when ≥ 4 GiB is free and no exclusive GPU job holds the lock, else the CPU. BF16 is ≈ 1.75 GB on either.
- **Health:** a canary query at start (cosine ≥ 0.999 to its stored vector) and a refusal under the host floor.
- **The app process never imports torch.** An ONNX/CPU export for a GPU-less host is deferred (§12).

### 7.2 GPU scheduling and memory safety

The rules extend what E1 built and measured.

- **Scopes, always.** Every model process runs in its own `systemd-run --user --scope` with `MemoryMax` (12G for the 9B and for training, 4G for the student) and `MemorySwapMax=0`. The worker refuses to load outside a scope whose `memory.max` is at most its plan's. Host RAM is the binding constraint: 32 GB shared, oomd killed the owner's terminal three times this week, and E1 saw 10.5 GiB available with 20.7 GiB of swap in use.
- **Start checks (E1's, unchanged):**
  - MemAvailable ≥ 14 GiB and free VRAM ≥ 22 GiB for the 9B;
  - utilization ≤ 15%;
  - `workload_problems` as amended on 2026-10-23: no other process over 1 GiB or 3 GiB in total, and no python, torch or GLM-OCR/marker worker;
  - pinned model file sizes and code digests.

  For the student: MemAvailable ≥ 6 GiB, and free VRAM ≥ 4 GiB to choose the GPU.
- **Runtime aborts (E1's):** below 3 GiB MemAvailable, over the 20 GiB device target, or at the meter's cap. Partial results are kept and the job is resumable.
- **Locks.**
  - **An exclusive GPU lock**, `flock $XDG_RUNTIME_DIR/learnloop-gpu.lock`, is held by every big GPU job: 9B indexing, teacher targets, student training and local GLM-OCR. It is waited for, never broken. The student query process does not take it; it is counted by the VRAM checks and moves to the CPU when it is short.
  - **The full-suite lock**, `flock /tmp/learnloop-fullsuite.lock`, is held by big GPU jobs too, as E1's runs did. A full pytest gate (a 5G scope at `-n 6`) and a 12G worker are never co-resident.
- **Never during the owner's GPU use.** A game or stream fails the workload check, and the job waits as `waiting_for_gpu`. An owner-chosen quiet window (`embedding.local.index_window`, default any time the checks pass) is available.
- **Metering.** One cumulative GPU-hours meter per phase (E1's `gpu_meter`, moved): a refusal under 15 minutes left, children killed at the cap, crashed workers charged to their heartbeat. Production indexing has no cap but is metered and reported per book.

## 8 The Voyage fallback

**Which setup.** E0's R5 grouped arm: `voyage-context-4` through `POST https://api.voyageai.com/v1/contextualizedembeddings`.

- Grouped windows by the same window rule as §4.1, `input_type="document"`.
- Queries as one single-chunk input with `input_type="query"`.
- 1024-d float, L2-normalized, ordinary cosine.
- Limits from the docs: 32K tokens per chunk, 1,000 inputs and 16K chunks per request, 120K total with auto-chunking ([docs](https://docs.voyageai.com/docs/contextualized-chunk-embeddings)). Production stays well under them with 4,096-token windows.
- This is the numerically best frozen arm (probability CE@10 0.862; linear algebra 0.828). Voyage's shared-space trick does not extend to it (§3.1), so its query encoder is itself.

**It is a separate index in a separate space.** It needs its own vectors for every extraction it may serve. **Recommended (Q6): maintain it in parallel.**

- Each extraction queues a Voyage backfill next to the local index job, capped at `embedding.fallback.max_cost_usd_per_run` (default $1.00).
- Each run is admitted at the full $0.12/M. The 200M-token free tier is never assumed (E0's rule), though it is likely to absorb the real bill.
- Rows go to `embedding_vectors` in `state.sqlite` with `model_id = space_id` and the window-keyed content hash of §4.2. They are paid inputs, so they are `WORKFLOW` rows as today, and they stay in snapshots.
- The alternative, building on demand when the first fallback query finds the space incomplete, leaves that query on keyword search or Qwen and buys the index then. It is cheaper only for books the owner never needs offline from the GPU.

**When it serves** (the resolver, §5):

- the student is not trained, not healthy or refused by memory checks;
- the student misses its time box;
- the local index is incomplete for the scope, for example a new book waiting for the GPU;
- the local space is disabled or in epoch drift;
- a host without the local model runs its own vault. The hub model makes that rare (§11).

**T1 and money.**

- Embeddings stay an **explicit opt-in route**. A new embedding-only profile type, `voyage_contextual_embedding`, serves only the `embedding` task and is refused for generation, exactly as `openai_embedding` is. The serving route switch to `chatgpt_plan` (T1) does not touch it, and `LEARNLOOP_AI_PROVIDER` does not override it.
- Nothing is sent while `embedding.enabled` or `embedding.fallback.enabled` is false.
- Every request is admitted against caps and leaves `model_call_receipts` (owner kind `source_query_embedding` or `embedding_backfill`).
- A fallback query is never silently paid: the receipt says so, and so does `space_selection`.

**Keys.**

- `voyage.api_key_env` defaults to `VOYAGE_API_KEY`, loaded by the existing config loader from the settings file, with shell values taking precedence.
- Receipts and manifests record only the name and its availability. A key value is never printed, logged or put in an exception body (E0's credential tests carry over).

**Data terms (Q7).** Voyage's FAQ lets an organization opt out of "storing and using their data for future model training", which gives "zero-day retention". It needs a payment method on file and Admin access, and "You won't be able to opt-in again in the dashboard" ([FAQ](https://docs.voyageai.com/docs/faq)). The page does not say what the default is. Recommended: the owner opts out before enabling the fallback, since book and query text leave the machine.

**Cost.**

| Item | Estimate |
|---|---|
| One 4,000-block book (≈ 0.5–1M tokens, grouped) | ≈ $0.06–0.12 per index build, again on every re-extraction |
| One query (30–600 tokens with a selection) | ≤ $0.0001 |
| Fallback index for today's owner vaults (the E0/E1 copies' sources) | cents |
| Qwen incumbent, for comparison | $0.01/M: ≈ $0.005–0.01 per book |

## 9 Evaluation bars

All bars run on the frozen E0/E1 bank (plan `e1_eaa8d20e4af40e3f`): the primary development slice (n = 58, 5 families) and the logged slice reported apart. They use paired, family-clustered bootstraps (10,000 resamples, fixed seed) and exact search with stable tie-breaks. A new top-10 candidate that no pass ever judged is `unknown`.

- If unknowns exceed 5% of the scored top-10 slots, a supplementary label round runs under E1's protocol before the verdict. That is E1's frozen rubric, two blinded Sonnet 5.5 passes and an Opus 5.5 audit, under its own ledger (≈ $1 per 60 candidates; E1 spent $0.72 for 66).
- Five families is underpowered. Every Phase 2–3 verdict is labelled exploratory; Phase 4's needs untouched families.

### 9.1 Student gate (Phase 2 exit)

| Measure | Bar |
|---|---|
| CE@10, student queries against 9B-teacher queries, same local documents | **Non-inferior by ≤ 2 points**: paired 95% lower bound of (student − teacher) > −0.02 |
| Support@10, nDCG@10, MRR | Reported; none below teacher by > 3 points |
| Fidelity on held-out synthetic queries (label-free) | Median cos(student, teacher) ≥ 0.95; teacher top-10 recall@10 ≥ 0.90 |
| Unseen family / subject | The same fidelity bars on the held-out family; reported separately and gating |
| Reader deictic slice (queries with a selection) | Reported separately; no stratum more than 5 points below teacher |
| Latency (batch one, at the bank's p95 query length, warm) | GPU p95 ≤ 20 ms; **CPU p95 ≤ 150 ms with ≤ 4 threads**; cold start ≤ 5 s |
| Memory | Student process anon RSS ≤ 3 GiB; device ≤ 2.5 GiB |

### 9.2 Switching the default (Phase 3 exit)

The full local path (9B documents and student queries) against Qwen R1. The margin is owner question Q2.

- **Recommended: non-inferior by ≤ 5 points**, i.e. a lower bound > −0.05, to switch the default while Qwen stays available.
  - E1's teacher-query result (+0.000 [−0.037, +0.037]) passes that margin and fails a 2-point one.
  - A 2-point margin is not reachable on 58 questions in 5 families unless v2 is actually better.
- **No Reader latency regression.** The paired end-to-end `find_sources` p50 and p95 must be at or under the incumbent's (whose hosted query p50 was ≈ 4.5 s historically). A local query in tens of milliseconds should clear this easily; the bar is measured, not assumed.
- The fallback is exercised. Forced `student_unavailable`, `default_incomplete` and `epoch_drift` runs each serve from Voyage, with receipts, and the never-mixed test passes.

### 9.3 Grouped or singleton (fixed now)

At Phase 3, keep `grouped` unless `singleton`'s pooled CE@10 is higher by ≥ 3 points with the student. Then drop the other variant's vectors.

### 9.4 Retiring Qwen for sources (Phase 4 exit)

- **Non-inferior by ≤ 2 points** on a **confirmation bank**:
  - untouched permitted families (e.g. the open books named in experiment spec §5.1: Axler LADR 4e and Grinstead–Snell, after their licences are checked);
  - labels at κ ≥ 0.60.
- Four weeks as the default, with a fallback rate under 10% of queries outside owner-forced runs.
- No open epoch drift.

## 10 Phases, kill switches and successors

| Phase | What lands | Kill switch / default | Exit |
|---|---|---|---|
| **P0 E1 closure** (no production code) | This spec; the E1 report (committed with it); a true 8,192-token profile run (metered, plan amendment); the label-of-record decision (Q3) | n/a | Report committed; Q1–Q14 answered |
| **P1a Local document index** | Production package `learnloop.local_embeddings` (worker, meter, windows, canaries, moved from E1); `learnloop embeddings local setup` (owner-run: the separate env, the 33.6 GB download to a pinned location, hash check); `local_source_index` jobs; vector cache; `embedding_spaces` migration; resolver with the local space allowed only when its encoder is available; doctor status | `embedding.local.enabled = false` until the owner runs setup and turns it on. Off: nothing is queued, nothing is loaded, the resolver never picks local | Owner vaults (out of the repo after S1) fully indexed in both variants; canaries stable over two batches; per-book time and peaks measured |
| **P1b Voyage fallback** (parallel with P1a) | `voyage_contextual_embedding` profile; production adapter (moved from E0); window-keyed vectors; parallel backfill job; resolver step 2 | `embedding.fallback.enabled = false`, `embedding.fallback.maintain_index = true`, `max_cost_usd_per_run = 1.0` | Forced-fallback tests pass; receipts complete; owner's vaults covered |
| **P1c (optional) teacher session** | `learnloop embeddings local session --idle-minutes 15`: owner-started 9B query residency (≈ 17 GB VRAM), auto-exit on idle, refused by the same checks | Off by default; never started automatically (Q5) | n/a; ends when P2 lands |
| **P2 Query student** | Generation, teacher-target jobs, screen, recipes, seeds; the query process; student checkpoint pinned by SHA-256 under the space | Student is used only once it passes §9.1; `embedding.local.query_encoder = "student"` | §9.1 met; ≤ 6 GPU-hours; generator spend within its cap |
| **P3 Switch the default** | `embedding.source_space.default = "local"`; consumer audit (§6) with any successors it requires | `embedding.source_space.default = "qwen"` restores today's path exactly (tested byte-for-byte on `find_sources` results with the same vectors) | §9.2 and §9.3 met |
| **P4 Retire Qwen for sources** (owner decision) | Source backfills stop for Qwen; existing Qwen source vectors remain readable until a later cleanup; non-source consumers keep Qwen | `embedding.source_space.incumbent = "qwen"` re-enables it as the third resolver step | §9.4 met, owner confirms (Q1) |

**Successors (each a new space, P1–P3 again, nothing mixed):**

- **S-a.** A non-preview or hosted pplx v2 context release.
- **S-b.** A Perplexity small query model published in the v2 context space. It is preferred over our student if it passes §9.1.
- **S-c.** A software epoch change that breaks canaries.
- **S-d.** A move to fast kernels (flash-linear-attention / causal-conv1d), which is a new pinned env and must pass canaries or start a new epoch.

## 11 Mobile, MCP and storage (S0/S1)

- **The hub model holds.** Under the storage spec, carson holds each vault, and the phone (PWA and Shortcut over Serve), the laptop (browser, later the remote desktop mode) and chat (MCP over Funnel) are clients of that one copy. So **every query is resolved on carson**, against carson's local space and student. The phone and laptop hold no vectors and no model. When carson's GPU is busy, the student runs on carson's CPU, which is why §9.1 gates CPU latency. Voyage is only needed when the student itself is unavailable or the index is incomplete.
- **A host with its own vault and no model** (a contributor, or a future offline laptop vault, which no S-spec mode supports today) uses the fallback space, or Qwen while it is the incumbent. Vector caches are never synced: SQLite is never file-synced (storage spec R4). A copy of a cache would be valid only for the same `space_id` and policy fingerprints, and rebuilding it needs the 9B.
- **MCP.** Admission charges the fallback's query bound (local is $0). `find_sources` results over MCP carry `space_selection` like the desktop's.
- **Backups and S1.** The vector cache is excluded from snapshots: it is derived and rebuildable at ≈ 2–4 GPU-minutes a book. The model files (33.6 GB) and the env (≈ 6 GB) are needed for any rebuild, so they live outside the repository and vaults at `~/.local/share/learnloop/models/<repo>@<revision>/` and `~/.local/share/learnloop/envs/local-embed-<lockhash>/` (Q11), each verified by hash.
- **S0, the public repository.**
  - Local caches live under `.learnloop/` (gitignored) and never reach the tip.
  - Hosted vectors (Voyage, and Qwen today) live in `state.sqlite`. In the tracked fixture vaults (`linear_algebra`, `probability`, `arxiv_v2`) they would be published until S0. Embeddings can partly reveal their text ([vec2text, Morris et al. 2023](https://arxiv.org/abs/2310.06816); cited from memory, not re-read).
  - So P1b's parallel maintenance is enabled **only on vaults outside the checkout**, i.e. after S1 moves the live vaults. Tests use `fixtures-local/` copies. No book text, synthetic query or student checkpoint is committed: training data and checkpoints stay in the data root or `fixtures-local/`.

## 12 Deferred

- ONNX/CPU export of the student for GPU-less hosts.
- FP8 or int8 for the 9B (experiment spec §9's precision matrix, only if VRAM pressure is measured).
- The late-interaction pair (v2-late 9B documents with 0.6B queries, MaxSim).
- Moving item, practice or diagnosis vectors to the local space.
- Training on learner-text queries beyond deduplicated logged Reader queries.
- Publishing the student, which needs a licence review of every training source.

## 13 Costs

| Item | Money | Other |
|---|---|---|
| Model and env setup | $0 | 33.6 GB download (public, ungated); ≈ 40 GB disk |
| Local indexing | $0 billed | ≈ 2–4 GPU-minutes per 4,000-block book (both variants) plus 25 s load per batch; electricity negligible |
| Student (P2) | Generator: $0 billed on `chatgpt_plan` (quota), else ≤ $5 cap on OpenRouter (Q8); gate labels ≤ $3 | ≤ 6 GPU-hours |
| Gates (P3/P4) | Supplementary labels ≈ $1 per 60 new candidates; the confirmation bank needs its own plan and cap, priced at plan time from E0's measured label rates | Owner review optional |
| Voyage fallback | ≈ $0.06–0.12 per book index; queries negligible; 200M free tokens not assumed | Opt-out of training (Q7) |
| Qwen while incumbent | ≈ $0.005–0.01 per book | — |

## 14 Risks

| Risk | Mitigation |
|---|---|
| The preview is withdrawn or changed upstream | Pinned revision with files kept locally (MIT permits retention); no re-download of another revision; a change is a successor space |
| Numeric drift across torch, driver or transformers updates | Software epoch in `space_id`; canaries every batch; `epoch_drift` blocks storage and the resolver falls back |
| Host RAM and oomd | Scopes everywhere; E1's floors and aborts; full-suite lock; the student's 4G scope; RssAnon sampling (page cache is reclaimable, E1 run 03) |
| GPU contention with the desktop | Workload rule; `waiting_for_gpu`; the student moves to CPU; the index is deferred, never forced |
| The student underperforms on Reader deictic queries or unseen books | Separate gating strata (§9.1); real logged queries in training after deduplication; teacher session (P1c) as an interim |
| Leakage from the bank into training | Family splits; similarity and n-gram deduplication; counts reported; bank never in prompts |
| Space mixing | `space_id` in every key; resolver refuses mixed lists; tests |
| Stale or partial indexes | Window-level invalidation; resolver prefers a complete space; doctor coverage per space |
| Silent spending | Opt-in route, caps, receipts and `space_selection` reasons; free tier never assumed |
| Weak labels (E1 κ 0.354/0.575) and a small bank (5 families) | Q3; exploratory labelling; Phase 4 needs a confirmation bank at κ ≥ 0.60 |
| Two Python environments to maintain (app transformers 4.57.6, local 5.18.0) | The separate env is lock-pinned and hash-checked; the app never imports torch; the env is rebuilt only as a new epoch |
| Persisted meaning through a consumer | §4.5/§6 audit at P3; a successor where retrieval output becomes admissions or placements |
| Quality is not better (known) | The decision is cost and research; Qwen and Voyage stay as kill-switch targets; the bars are non-inferiority |

## 15 Owner questions (recommended answers)

| ID | Question | Recommended |
|---|---|---|
| Q1 | What happens to Qwen for sources? | Keep it as the default until P3, then as the third resolver step. At P4, retire it **for sources** after §9.4; keep it for items, diagnosis, PF freshness, map neighbours and graph nomination (Q12). Keeping it longer as a third fallback costs ≈ $0.01 a book, so "keep" is also cheap |
| Q2 | Margin for switching the default (P3)? | **5 points** (lower bound > −0.05) with Qwen still available; **2 points** on a confirmation bank to retire Qwen (P4) |
| Q3 | E1's supplementary κ is 0.354/0.575 (no verdict). What is the label of record for P2/P3 gates? | Accept the Opus-adjudicated labels (every disagreement and every new set was audited; 1 unresolved candidate stays unknown) as the label of record for P2/P3, disclosed as below-κ; require κ ≥ 0.60 on the P4 confirmation bank |
| Q4 | Grouped or singleton? | Index both in P1; decide by §9.3's fixed rule at P3 (grouped unless singleton wins by ≥ 3 points) |
| Q5 | Until the student lands, may the 9B serve queries in an owner-started session (≈ 17 GB VRAM, 15-minute idle exit)? | Yes, opt-in and off by default (P1c). Otherwise Qwen serves queries until P3 |
| Q6 | Voyage index: maintained in parallel or on demand? | In parallel, capped $1 per run, on vaults outside the checkout (after S1) |
| Q7 | Opt the Voyage organization out of training use (zero-day retention; irreversible in the dashboard)? | Yes, before P1b is enabled |
| Q8 | Synthetic query generator? | GPT-6 Luna on `chatgpt_plan` (T1 transport; $0 billed, quota). If the plan is down, report and ask before using OpenRouter (DeepSeek or Sonnet 5.5, cap $5). Sources: the owner's local books in the vaults, for personal use only; artifacts stay local |
| Q9 | Does "0.9" mean a ≈ 0.9B student specifically? | Read it as the size class. Screen `Qwen3.5-0.8B-Base` (873M, the literal "0.9"), `pplx-embed-v1-0.6b` and `Qwen3-Embedding-0.6B`, and keep the best that passes §9.1. Ties go to the smaller one (CPU latency) |
| Q10 | Where does the student run? | GPU when ≥ 4 GiB is free and no exclusive job runs, else CPU; its own 4G scope; idle exit after 20 minutes |
| Q11 | Where do the vectors, models and env live? | Vectors in `<vault>/.learnloop/vector-cache/` (derived, not in `state.sqlite`, not in snapshots); models and env under `~/.local/share/learnloop/` |
| Q12 | Do the practice index and other embedding consumers move? | No. They stay on Qwen; revisit after P4 with `practice_index/evaluation.py` |
| Q13 | If Perplexity ships a small same-space query model or a non-preview release? | A new space through P1–P3 (S-a/S-b); prefer their small model over ours if it passes §9.1 |
| Q14 | Install fast linear-attention kernels? | Not needed (≈ 2 minutes a book on the fallback path); deferred as successor S-d |

## Sources (read 2026-10-24)

- Voyage: [Voyage 4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/) · [embeddings docs](https://docs.voyageai.com/docs/embeddings) · [contextualized chunk embeddings](https://docs.voyageai.com/docs/contextualized-chunk-embeddings) · [FAQ (training opt-out)](https://docs.voyageai.com/docs/faq) · [voyage-4-nano card](https://huggingface.co/voyageai/voyage-4-nano) · [voyage-context-4 release](https://mongodb.com/company/blog/product-release-announcements/voyage-context-4-stop-worrying-about-chunking-with-our-best-performing-model) · [Vespa on asymmetric retrieval](https://blog.vespa.ai/asymmetric-retrieval-spend-on-docs-queries-for-free/)
- Perplexity: [model listing](https://huggingface.co/api/models?author=perplexity-ai&limit=100) · [collections](https://huggingface.co/api/collections?owner=perplexity-ai) · [v2 context 9B preview card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview) · [v2 late 0.6B card](https://huggingface.co/perplexity-ai/pplx-embed-v2-late-0.6b) · [pplx-embed-v1-0.6b](https://huggingface.co/api/models/perplexity-ai/pplx-embed-v1-0.6b)
- Student bases: [Qwen3.5-0.8B](https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B) · [Qwen3-Embedding-0.6B](https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B)
- Distillation: [NanoVDR](https://arxiv.org/abs/2603.12824) · [Query Encoder Distillation via Embedding Alignment](https://aclanthology.org/2023.sustainlp-1.23/) · [EmbedDistill](https://arxiv.org/abs/2301.12005) and [Learning Query Encoders Can Be Hard](https://arxiv.org/abs/2610.02749) (from the experiment spec §3, not re-read) · [vec2text](https://arxiv.org/abs/2310.06816) (not re-read)
