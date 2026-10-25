# Local contextual source retrieval: pplx v2 9B documents, a distilled query student, a hosted Voyage fallback (v1)

**Status:** draft, revised 2026-10-24 with the owner's decisions: Q1 and Q3–Q15 decided (§15), and every fixed margin or weight replaced by a learned rule (§9). Queue placement: P0, P1a and P1b in Track P right after T1 lands; P2 as GPU time allows (§10). Branch `experiments/e1-local-v2`, base `eec2dd88d` (migration head 217). This is a specification only. No code changed, no model was loaded, no paid or model call was made and nothing was downloaded to write it. Public web pages were read for §3; each claim cites its URL and says what the page did not settle.

**Basis:** [the experiment spec](spec_contextual_source_embeddings_experiments_v1.md) (§7 adoption, §8 E1, §9 deferred work, D6); [the E1 harness review](../reviews/experiments-e1-local-v2.md) (model facts, the worker, the GPU runs); [the E1 report](../reviews/experiments-e1-report.md) (plan `e1_eaa8d20e4af40e3f`, aggregates only); [the embedding consumers spec](spec_embedding_consumers_v1.md); [the storage/sync spec](spec_storage_sync_v1.md) (the hub model); [the algorithm-change playbook](../algorithm-change-playbook.md).

## 0 The owner decision and what it does and does not change

**Owner, 2026-10-24 (verbatim):** "Let's have learnloop use local pplx v2 (distill into 0.9 version for retrieval similar to how voyage handles it in their ecosystem) since its free and a fun research extension, but allow fallback to the hosted setup of Voyage."

This is the **explicit D6 amendment** that the experiment spec's §7 and D6 required before a second production source embedding space could exist. It is recorded in that spec's amendment log (§12) with a pointer here.

**What the owner knew when deciding.** E0/E1 showed **no quality gain**:

- local v2 (grouped) against Qwen R1: **+0.000 [−0.037, +0.037]** CE@10;
- against the best frozen finalist, hosted Voyage `voyage-context-4` grouped: −0.017 [−0.074, +0.037].

Both figures are from the primary development slice: n = 58, 5 families, paired and family-clustered. **The motivation is cost and research value, not quality.** Local inference costs no provider bill, and building the student is the research extension.

**The decision's scope and limits.**

1. **It replaces §7's adoption bar for this space only.** The §7 bar asked for a ≥ 5-point gain and a blind-answer gain. For this space it becomes a **learned decision**: a posterior on the labelled bank stated as expected utility, plus online fusion weights learned from recorded signals (§9). The case for adoption is cost and research, not quality. Every other §7 rule still holds for any other space.
2. **Source retrieval only.** The space serves `source_block` retrieval and its queries. Item stems, the practice index, diagnosis split retrieval, PF freshness, graph nomination and map neighbours stay on `qwen/qwen3-embedding-8b`, under the October 11 one-model decision, until the owner extends this amendment (Q12).
3. **The model is a preview.**
   - Its card says weights, embeddings and interface "may change in later versions without backward compatibility" and that its embeddings "should not be mixed with embeddings from a future release" ([card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview)).
   - So the space is pinned to revision `e2c06a779d45e8db53066735be1b98ffe3412ca3`. Vectors are **never mixed** with another revision or release.
   - A model change, by revision, precision or software epoch (§4.2), is a new space. It needs a full re-index and a newly trained student.
4. **Nothing becomes ground truth.** Embeddings nominate; verifiers, policy checks and citation validation keep authority (experiment spec §1).
5. **E1 itself has no verdict.** Its decision is `no_verdict`: the supplementary labels' κ was 0.354 (linear algebra, n = 35) and 0.575 (probability, n = 31), under the 0.60 gate. The owner's decision does not need an E1 verdict. The posterior decisions in §9 do need a label of record, though (decided: Q3).

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

**Scores are never mixed raw.** Each space ranks on its own. Rankings are combined by rank with learned per-consumer, per-query-kind weights (§5, §9.2), and the receipt names every space, weight and propensity.

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
  - the batch is ≥ 15 minutes old or ≥ 1 source, whichever comes later, so a burst of re-extractions is not loaded one by one (`keep`: an operational default, §9.6);
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

  At ~2 minutes a book the second variant is cheap. Both enter the fusion as separate lists with learned weights. A variant is dropped only by expected utility (§9.1, §9.4), with no fixed rule.
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

## 5 The space resolver and learned fusion (the one new seam)

`search_spans()` asks one function, `resolve_source_spaces(vault, repository, scope, consumer, query_kind, deadline)`. It returns the **available spaces** and their **fusion weights** for this query. The weights are drawn from the learned posterior of §9.2. The result also records why each space was in or out. Scores from different spaces are **never mixed raw**. Each available space produces its own exact-cosine ranking, and the rankings are combined by rank (§5.2). The fused list is the `meaning` list that `search_spans` already pools. Keyword widening, `dense_plus_bm25`, verification and paging are unchanged downstream.

### 5.1 Availability (which spaces may contribute)

A space contributes to a query only if all of these hold:

1. **It is enabled.** Its switch is on (`embedding.local.enabled`, `embedding.fallback.enabled`) and, for the incumbent, it is not retired.
2. **It covers the scope.** Only its covered extractions rank (today's `partial` rule, applied per space). When another space covers an extraction that this one does not, that extraction is reached through the other space's list. A new import waiting for the GPU is therefore still found through Voyage or Qwen, and is never left to keyword search alone while any space covers it.
3. **Its query encoder answers within the remaining time box.** That is the existing `search_spans` deadline, which stays fixed (§9.6). For a cold-starting student, the resolver predicts its start time from the **measured** distribution of start times. It waits only when the predicted probability of answering in time beats the expected value of the other available spaces (§9.2). Otherwise it drops the student for this query. The spec sets no fixed wait.
4. **It is current.** It is not in `epoch_drift` and its rows pass the current policy check.

A hosted space's query is a paid request under the existing query caps and receipts. Its money cost enters the utility of §9.1.

If no space is available, the query is keyword only, as today's `disabled`/`incomplete` behaviour.

### 5.2 Rank-based fusion with learned weights

```text
fused(d) = Σ_{s ∈ available} w_{c,k,s} · 1 / (rrf_k + rank_s(d))
```

- **Lists.** Each space contributes one list `s`. The grouped and singleton local variants are separate lists, and so are student queries and (in a P1c session) teacher queries.
- **Weights.** `w_{c,k,s}` is a Thompson draw from the posterior for consumer `c` and query kind `k` (§9.2), renormalized over the available spaces.
- **`rrf_k`.** Seeded at the current config value of 60 (basis: legacy) and learned on the same likelihood over a grid.
- **Selector as a special case.** A **per-query selector** is the case where one weight is 1. When the posterior puts nearly all mass on one space, the draw behaves as a selector, and the hosted queries of near-zero-weight spaces are skipped. The probability of skipping a space is itself part of the recorded propensity.
- **Contexts.** Consumer `c` is one of Reader Ask by intent, tutor, library ask, compare, teacher, MCP or instructional. Query kind `k` comes from existing features: the `find_sources` intent, a selection present (deictic), the rewrite and conceptual-question gate, and an explicit reference lookup.

Every result records:

- `space_selection`, with each space's availability and its reason: `ok`, `incomplete`, `encoder_unavailable`, `encoder_late`, `disabled`, `epoch_drift` or `retired`;
- the drawn weights and their **propensities**;
- the RNG seed, keyed by query id so a replay is reproducible;
- every span's rank in every contributing list.

`learnloop doctor` and the result's on-demand detail say this in plain words (frictionless by default, glass box on demand).

**The kill switch** is `embedding.source_space.learned_fusion = false`. With it off, the weights are fixed at their seed, which is the current default space alone. With the default at Qwen, the path is today's, byte-for-byte on `find_sources` results for the same vectors (tested).

## 6 Consumers

Every consumer reaches the resolver through `search_spans`, so none needs its own integration. Each is listed with what changes for it.

| Consumer | Path | Change | Successor? |
|---|---|---|---|
| Reader Ask (`find_sources`, five intents) | `find_sources` → `search_spans` | Space per query; verification (900-char views) and paging unchanged | No (lookup, not exposure) |
| Tutor grounding | `TutorSpanProvider` / `tutor_pool` / `reader_tutor` | Same; the T6 time box covers the student's cold-start rule | No |
| Library ask / compare (RW4a/RW4d) | `library_ask`, `compare` | Same; a comparison across sources uses one weight draw for all of its searches | No, unless a library offer is recorded as an admission (check at Phase 3) |
| Teacher grounding (`retrieve_source`, spec_teacher_v1, not yet landed) | `TutorSpanProvider` / `find_sources` | The teacher spec already says "E1 … competes to sit behind" this seam | **Yes, if** placement or plan anchors are persisted from retrieval: then that consumer's switch is a successor |
| Passage cues, instructional sources and exercises, MCP `find_sources` | `search_spans` | Same; MCP's worst-case cost admission charges the fallback's query bound, since a local query is $0 | No |
| Practice index (`find_practice`, practice_item / practice_query) | Its own vectors through `practice_index.query_vectors` | **Unchanged: stays on Qwen** (§0.2). Items are short, non-contextual, and not in the E0/E1 bank | Not applicable (Q12) |

## 7 The query student, and GPU and memory safety

### 7.1 The student (Phase 2)

**Goal.** A query encoder of ≈ 0.6–0.9B parameters whose vectors land in the 9B's 2048-d space. The teacher's documents stay frozen. It is judged by §9.3's learned rule, not a fixed gate.

**Candidates.** The screen trains one seed each, cosine alignment only, then picks on development by §9.3's expected utility:

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
- A synthetic query within cosine 0.90 of any bank query (by the teacher) or with 5-gram overlap above 0.5 is dropped, and the count is reported (`keep`, §9.6: these guards may only tighten).
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

## 9 Learned decision rules (owner, 2026-10-24: no made-up margins or weights)

**Owner, 2026-10-24:** "all these weights/margin values need to be learned and dynamic and not just made up, priors can be seeded otherwise."

This revision removes every fixed point margin from the first draft:

- the 5-point bar for switching the default;
- the 3-point rule for grouped against singleton;
- the 2-point student gate;
- the 2-point bar for retiring Qwen;
- the 5% unknown trigger, the 0.95 and 0.90 fidelity bars, the 150 ms and 20 ms latency gates, the four-week and 10% fallback-rate rule, and the 3 s cold-start wait.

Two things replace them:

- **Offline posterior decisions on the labelled bank**, stated as expected utility (§9.1).
- **Online learned fusion weights**, updated from signals LearnLoop records (§9.2).

The student is judged by both (§9.3). Every seeded prior names its basis (§9.5). What stays fixed is labelled `keep` with its reason (§9.6).

### 9.1 Offline: posterior decisions on the labelled bank, stated as expected utility

**The data** is the frozen E0/E1 bank (plan `e1_eaa8d20e4af40e3f`): the primary development slice (n = 58, 5 families) and the logged slice. A later confirmation bank adds to it, and is never substituted for it.

**The outcome model.**

- Each question `i` in family `f` has a per-arm complete-evidence outcome. In the model it is the latent truth, not the label.
- A **hierarchical model** puts a family random effect on each arm's log-odds of completeness, partially pooled across families.
- Arm differences `δ_{a,b}` are posterior quantities. They are not paired bootstrap point estimates.
- Labels enter through a **Dawid–Skene label-noise model**. Its confusion matrices are learned from the two blinded passes and the Opus adjudications already recorded. Low agreement (E1's κ 0.354/0.575) therefore widens the posterior instead of blocking a verdict. κ is still reported (this is Q3's decision, made concrete).
- **Unknown labels are latent.** They are imputed from the label model, so a new unjudged candidate adds uncertainty rather than counting as a miss.
- **Fitting.** The posterior is fitted by MCMC, or by a grid-plus-importance sampler in numpy, which is small at this n. A fixed seed is recorded and posterior draws are kept for audit.

**Utility of an action `a`.** Examples of actions: make local the seed default; keep both variants; retire Qwen for sources; adopt the student.

```text
U(a) = q(a) + b(a) − λ · m(a) − μ · p_late(a)
```

| Term | Meaning | Learned how |
|---|---|---|
| `q(a)` | Posterior expected Complete Evidence@10 under `a` (offline); online, the posterior expected signal-hit rate (§9.2) | From the bank (and online signals) |
| `m(a)` | Measured monthly money cost: hosted backfills and queries, labels, generation | Measured from receipts |
| `p_late(a)` | Probability that the query misses the existing time box and falls to the next space or to keyword | Measured from timings |
| `μ` | Quality lost when a query misses the box | **Estimated, not chosen:** the bank's posterior difference between the dense arm and keyword-only (R1 against R0), updated online from fallback outcomes |
| `λ` | The owner's exchange rate, quality per dollar | **Learned from the owner's choices**: a Bayesian logistic choice model in which every owner decision between costed options is an observation |
| `b(a)` | The owner's preference for an option beyond quality and money (local is free and a research extension) | Learned the same way; seeded from the 2026-10-24 decision (§9.5) |

**The decision rule.**

- **Act** on `argmax_a E[U(a)]`. The output also gives `P(a is best)` for each action, i.e. the probability that one space is better than another, never a margin.
- **Value of information.** If the expected loss of acting now, `E[max_a U] − max_a E[U]`, exceeds `λ` × the cost of the next label batch, **buy labels first**, within the label cap (`keep`). Buy them where they reduce the loss most: the new-candidate strata the posterior is least sure about. This replaces the fixed "unknown above 5%" trigger.
- **Rerun.** The same rule runs again whenever new labels, a new space or a new student arrives.
- **The owner confirms** any action that removes a space (Q1) or changes the seed default. The rule recommends, and the owner's answer becomes another observation for `λ` and `b`.

**Applying it to each former margin:**

| Former fixed rule | Now |
|---|---|
| Q2: switch the default at 5 points | The seed default is `argmax E[U]` over {qwen, local, voyage}, with `P(best)` reported. E1's posterior on `q` is close to even between local and Qwen. The learned `b_local` and the smaller `m(local)` decide it. Online fusion (§9.2) then moves per consumer and query kind |
| Q4: grouped against singleton at 3 points | Both variants are lists in the fusion. Their weights are learned per context, and a variant is dropped only when `E[U(keep both)] < E[U(drop one)]`. Keeping one costs ≈ 2 GPU-minutes and ≈ 16 MB a book, so both may simply stay |
| P4: retire Qwen at 2 points | Retire Qwen's source list when its expected marginal contribution in the fusion, `E[Δq]` from removing it (offline and online posteriors), is worth less than `λ · m(qwen) + μ · Δp_late`. The owner confirms (Q1) |

### 9.2 Online: learned fusion weights from implicit relevance signals

**The signals**, all recorded by LearnLoop or added as append-only receipts:

| Signal | Where it is recorded | Status on this branch |
|---|---|---|
| **Validated citation** | The tutor's answer cites a delivered span after citation validation: `tutor_qa._validated_citations` → `source_context["citations"]`. Library ask answers keep `citations` and `grounded_keys` | Recorded today |
| **Learner opens a passage from a result** | Reader / library result open | **No dedicated event found.** P1a adds an append-only `retrieval_feedback` table (`RECEIPT`): query receipt id, span key, `opened`, time. No "not relevant" button is added; learner text and actions are the signals, not skip buttons |
| **Teacher grounded anchor** | `retrieve_source` anchors persisted by the teacher (spec_teacher_v1) | When the teacher lands |

**The model.** For consumer `c` and query kind `k`, a Bayesian logistic **examination-and-relevance model**:

```text
P(signal on delivered span d) = examined(pos_d) · σ( Σ_s β_{c,k,s} · 1/(rrf_k + rank_s(d)) + γ_signal )
```

- `examined(pos)` is a position-bias curve, learned (§9.5 gives its seed).
- `rank_s(d)` comes from every list, including lists whose weight did not deliver `d`.
- `γ_signal` is learned per signal type: citations, opens and anchors differ in how reliably they mark relevance.
- The fusion weights are `w ∝ β`, drawn by Thompson sampling.

**Partial pooling.**

- `β_{c,k} ~ N(β_c, Σ_c)` and `β_c ~ N(β_global, Σ_g)`, with `Σ` learned by empirical Bayes.
- A sparse context, such as MCP compare queries, borrows strength from its consumer and from the global weights. One learner produces few signals, and pooling is how n = 1 still learns.

**Exploration and bias.**

- A signal can only fall on a span that was delivered, so a space's unique finds earn credit only when its drawn weight delivers them.
- Thompson draws randomize delivery with **recorded propensities**, and updates are inverse-propensity weighted. This is the unbiased learning-to-rank correction ([Joachims et al. 2017](https://arxiv.org/abs/1608.04468)).
- Draws that would deliver a span the policy check rejects never happen: policy runs before fusion.

**Updates.**

- A nightly job, or one at sidecar start, refits from the signal receipts by Laplace or Pólya-gamma.
- The posterior lives in a `DERIVED` table, `retrieval_fusion_posteriors`. It has exactly one replayer in `substrate/rebuild_orchestrator.py`, which recomputes it from the receipts in order with the recorded seeds (the CLAUDE.md migration rule). This is the same migration as `embedding_spaces` and `retrieval_feedback`.

**Persisted meaning.** The weights change which spans are delivered, which is retrieval, not exposure (§4.5). A consumer that turns retrieval into admissions still mints its successor (§6).

**Signal reliability is checked against labels.**

- A periodic **audit sample** of signalled spans (cited, opened, anchored) is labelled under the bank protocol. The VOI rule of §9.1 decides when, within the label cap.
- The audit updates `P(relevant | signal type)` and, through it, `γ_signal`.
- This catches a feedback loop: a tutor that cites whatever is ranked first would otherwise teach the weights to agree with themselves.

### 9.3 The student: a learned weight against the 9B's queries, and a posterior check on the bank

- **Online.** Student queries are a list (`local:student`) in the fusion, next to the fallback spaces. Its weight per context is learned from the same signals (§9.2). That learned weight **is** the fallback weight: in contexts where the student's evidence is weak, Voyage and Qwen carry the weight.
- **Against the teacher.**
  - The nightly index batch already loads the 9B. It also re-encodes a sample of that day's logged queries with the teacher, so a `local:teacher` ranking exists for real traffic. The sample size comes from the VOI rule, within the GPU budget (`keep`).
  - Credit from this replay is biased toward the delivered (student) list, so it is used as a **lower bound** on the teacher's advantage.
  - In P1c sessions the teacher list is live in the fusion, with propensities, and gives unbiased credit.
- **Offline.**
  - The bank posterior (§9.1) gives `P(student ≥ teacher)` and the posterior difference, per stratum (Reader deictic, logged, unseen family).
  - The student is **adopted** when `E[U(student)] ≥ E[U(each alternative)]`. The alternatives are the fallback spaces for queries, and teacher sessions, whose cost is the 17 GB residency's GPU-hours and the load latency.
  - **Training continues** while the expected utility gain of another training round, read from the learning curve over the 2k/10k/50k budgets, beats its GPU-hours, within the Phase 2 cap (`keep`).
- **Diagnostics, never gates:** median cos(student, teacher), teacher top-10 recall, CPU and GPU latency, process RSS. Latency enters the utility only through `p_late`.

### 9.4 Grouped and singleton, Voyage and Qwen

All of them are lists in the same fusion. No fixed rule picks among them. The learned weights pick per context, and §9.1 decides which indexes are worth maintaining at all.

### 9.5 Seeded priors and their basis

| Prior | Seed | Basis |
|---|---|---|
| Arm-difference scale in the bank model (`δ`) | Centred at 0; scale from the spread of differences among E0's nine measured arms, by empirical Bayes | **Population** (the population of arms E0 measured) |
| Family random-effect variance | The between-family spread in E0/E1's per-family results | **Legacy** (E0/E1) |
| Label-noise confusion matrices | E0's relabel run (κ 0.657/0.648) and E1's supplement, with their adjudications | **Legacy** |
| Online fusion weights `β` | Prior mean at the **current default**: full weight on today's default space (Qwen before P3; the §9.1 seed default after), zero mean on the others. Prior covariance from the bank's posterior over arms, scaled by the bank's effective sample size after the family design effect | **Legacy** (current config and the E0/E1 bank) |
| Pooling variances `Σ_c`, `Σ_g` | Hyperpriors chosen by a simulation of synthetic signal streams generated from the bank's per-arm posteriors (`learnloop.sim` style), picking the scale under which the learner recovers the simulated weights | **Simulation** |
| `rrf_k` | 60, the current config | **Legacy** |
| Position examination curve | Monotone decreasing in delivered position, initialised to a 1/rank shape, learned through the randomized propensities | **Published** ([Joachims et al. 2017](https://arxiv.org/abs/1608.04468), not re-read) |
| `P(relevant \| cited)` | Labels of spans cited in E0's blind D1 answer runs | **Legacy** |
| `P(relevant \| opened)`, `P(relevant \| anchored)` | The citation posterior, discounted to a pseudo-count of 1 | **Legacy by analogy, weak** (no opens or anchors are recorded yet) |
| `b_local` (the owner's preference for local) | The smallest value that makes the 2026-10-24 choice optimal at E1's posterior | **Legacy** (owner decision) |
| `λ` (quality per dollar) | From the owner's recorded budget decisions: the E0 cap of $25 raised to $40, Qwen chosen at $0.01/M, E1's $5 | **Legacy** (owner decisions), weak |
| `μ` (cost of a missed time box) | The bank's R1 − R0 posterior | **Legacy** |

### 9.6 What stays fixed (`keep`)

| `keep` | Value | Reason |
|---|---|---|
| Money caps | Voyage backfill $1 per run; generator $5; label rounds under their own ledgers (≤ E1's $5 per plan); the existing query caps | Spending authority is the owner's, not a learned trade-off. Learned rules act inside the caps and never raise them |
| GPU budgets | P2 ≤ 6 GPU-hours; the E1 meter's cumulative caps | The owner's shared GPU; a budget, not a quality trade-off |
| Memory floors and scopes | 9B: scope 12G, swap 0, MemAvailable ≥ 14 GiB, free VRAM ≥ 22 GiB, utilization ≤ 15%, abort below 3 GiB or above the 20 GiB device target. Student: scope 4G, MemAvailable ≥ 6 GiB, ≥ 4 GiB VRAM to choose the GPU | Safety. oomd killed the owner's terminal three times this week; E1 measured these limits |
| The workload rule | Amended 2026-10-23 | The owner's desktop GPU use comes first |
| The query time box | The existing `search_spans` deadline | A product contract that consumers already rely on. Learned rules predict against it and never extend it |
| Canary tolerance | cos ≥ 0.999 | An identity check, not a quality margin: E1 measured padding and batch invariance at 0.99991, so a lower canary means a different computation |
| Leakage guards | Teacher cos ≥ 0.90 or 5-gram overlap > 0.5 to any bank query drops a synthetic query; family splits | Protecting the evaluation is a rule, not a trade-off. They may only tighten |
| Policy | Exam, held-out, solution and assessment-lane exclusions; windows never cross them | Learner-protection invariants |
| Preview isolation | Vectors never mixed across revisions; a new space on any change | The model card's own requirement |
| Index batching | ≥ 15 minutes or ≥ 1 source; idle exit after 20 minutes | Operational defaults the owner can tune. They affect only how soon a new book is indexed and how long the student stays loaded, never ranking |

## 10 Phases, kill switches and successors

**Queue placement (owner, DECIDED 2026-10-24):** P0, P1a and P1b go **in Track P, right after T1 lands**. P2 follows as GPU time allows.

| Phase | What lands | Kill switch / default | Exit (by the rules of §9, no fixed margins) |
|---|---|---|---|
| **P0 E1 closure** (no production code) | This spec and the E1 report (committed); a true 8,192-token profile run (metered, plan amendment); the bank posterior model of §9.1 fitted on E0/E1 (label-noise model included); the simulation behind the pooling hyperpriors | n/a | Posterior and simulation reports committed (aggregates only) |
| **P1a Local document index and learned fusion** | Production package `learnloop.local_embeddings` (worker, meter, windows, canaries, moved from E1); `learnloop embeddings local setup` (owner-run: separate env, 33.6 GB download to the pinned location, hash check); `local_source_index` jobs; vector cache; one migration: `embedding_spaces` (`WORKFLOW`), `retrieval_feedback` (`RECEIPT`), `retrieval_fusion_posteriors` (`DERIVED`, one replayer); the resolver and fusion of §5; doctor status | `embedding.local.enabled = false` until the owner runs setup. `embedding.source_space.learned_fusion = false` keeps the seed weights. With both off, today's path is unchanged | Owner vaults (outside the checkout after S1) fully indexed in both variants; canaries stable; fusion posteriors replay byte-identically; propensities logged |
| **P1b Voyage fallback** (parallel with P1a) | `voyage_contextual_embedding` profile; production adapter (moved from E0); window-keyed vectors; parallel backfill job | `embedding.fallback.enabled = false`, `maintain_index = true`, `max_cost_usd_per_run = 1.0` (`keep`) | Forced-unavailability tests serve through Voyage with receipts; owner vaults covered |
| **P1c Teacher session** (decided, opt-in) | `learnloop embeddings local session --idle-minutes 15`: owner-started 9B query residency (≈ 17 GB VRAM), auto-exit on idle, same checks; the teacher list is live in the fusion | Off by default; never started automatically | Ends its role when P2's student is adopted |
| **P2 Query student** (as GPU time allows) | Generation, teacher targets, the screen, recipes, seeds; the query process; the student checkpoint pinned by SHA-256 under the space; the nightly teacher replay sample | The student joins the fusion only after §9.3's adoption decision (`E[U(student)] ≥` alternatives); its weight is then learned | §9.3: adopted by expected utility on the bank posterior; training stops when another round's expected gain is worth less than its GPU-hours; ≤ 6 GPU-hours (`keep`) |
| **P3 Seed default** | §9.1 picks the seed default (`argmax E[U]`, `P(best)` reported); the owner confirms; consumer audit (§6) with any successors it needs; learned fusion on | `embedding.source_space.default = "qwen"` and `learned_fusion = false` restore today's path exactly | The seed decision recorded with its posterior; online weights then move per context |
| **P4 Retire Qwen for sources** (owner confirms) | Qwen source backfills stop; existing vectors stay readable until a later cleanup; non-source consumers keep Qwen | `embedding.source_space.incumbent = "qwen"` brings its list back | §9.1: Qwen's expected marginal contribution in the fusion is worth less than its cost and latency (offline and online posteriors, confirmation bank labels included) |

**Successors (each a new space, P1–P3 again, nothing mixed):**

- **S-a.** A non-preview or hosted pplx v2 context release.
- **S-b.** A Perplexity small query model published in the v2 context space. It joins the fusion as a list and replaces our student when §9.3 prefers it.
- **S-c.** A software epoch change that breaks canaries.
- **S-d.** A move to fast kernels.

Seed weights for a new space are its bank posterior (§9.5). A new space never inherits an old space's learned weights.

## 11 Mobile, MCP and storage (S0/S1)

- **The hub model holds.** Under the storage spec, carson holds each vault, and the phone (PWA and Shortcut over Serve), the laptop (browser, later the remote desktop mode) and chat (MCP over Funnel) are clients of that one copy. So **every query is resolved on carson**, against carson's local space and student. The phone and laptop hold no vectors and no model. When carson's GPU is busy, the student runs on carson's CPU, so CPU latency enters its utility through `p_late` (§9.3). Voyage is only needed when the student itself is unavailable or the index is incomplete.
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
| Posterior updates (P0–P4) | Label batches bought by the VOI rule (§9.1), ≈ $1 per 60 new candidates, inside the label caps (`keep`); the confirmation bank needs its own plan and cap, priced at plan time from E0's measured label rates | Owner review optional |
| Voyage fallback | ≈ $0.06–0.12 per book index; queries negligible; 200M free tokens not assumed | Opt-out of training (Q7) |
| Qwen while incumbent | ≈ $0.005–0.01 per book | — |

## 14 Risks

| Risk | Mitigation |
|---|---|
| The preview is withdrawn or changed upstream | Pinned revision with files kept locally (MIT permits retention); no re-download of another revision; a change is a successor space |
| Numeric drift across torch, driver or transformers updates | Software epoch in `space_id`; canaries every batch; `epoch_drift` blocks storage and the resolver falls back |
| Host RAM and oomd | Scopes everywhere; E1's floors and aborts; full-suite lock; the student's 4G scope; RssAnon sampling (page cache is reclaimable, E1 run 03) |
| GPU contention with the desktop | Workload rule; `waiting_for_gpu`; the student moves to CPU; the index is deferred, never forced |
| The student underperforms on Reader deictic queries or unseen books | Per-stratum posteriors and per-query-kind learned weights (§9.1–§9.3); real logged queries in training after deduplication; teacher session (P1c) as an interim |
| Leakage from the bank into training | Family splits; similarity and n-gram deduplication; counts reported; bank never in prompts |
| Space mixing | `space_id` in every key; resolver refuses mixed lists; tests |
| Stale or partial indexes | Window-level invalidation; resolver prefers a complete space; doctor coverage per space |
| Silent spending | Opt-in route, caps, receipts and `space_selection` reasons; free tier never assumed |
| Weak labels (E1 κ 0.354/0.575) and a small bank (5 families) | Q3: a label-noise model widens the posterior; VOI-driven label purchases; a confirmation bank of untouched families before P4 |
| Two Python environments to maintain (app transformers 4.57.6, local 5.18.0) | The separate env is lock-pinned and hash-checked; the app never imports torch; the env is rebuilt only as a new epoch |
| Persisted meaning through a consumer | §4.5/§6 audit at P3; a successor where retrieval output becomes admissions or placements |
| Feedback loops in learned weights (the tutor cites whatever ranks first) | Randomized Thompson draws with recorded propensities and IPS updates; periodic label audits of signalled spans recalibrate `γ_signal` (§9.2) |
| Sparse signals from one learner | Partial pooling across contexts, priors from the bank, a simulation-chosen hyperprior; the bank posterior keeps working while online evidence is thin |
| Owner-preference parameters (`λ`, `b`) learned from few choices | They stay weak priors updated by each recorded owner decision; the rule recommends and the owner confirms removals and seed changes |
| Quality is not better (known) | The decision is cost and research; Qwen and Voyage stay in the fusion; the learned weights move away from local wherever the signals say it is worse |

## 15 Owner questions

Q1 and Q3–Q14 are **DECIDED 2026-10-24** as recommended. Q2's fixed margin, and the fixed rules inside Q4 and the P2/P4 gates, were replaced by the owner's "learned and dynamic" rule (§9).

| ID | Question | Status and answer |
|---|---|---|
| Q1 | What happens to Qwen for sources? | **DECIDED 2026-10-24.** It stays the seed default until P3 and stays in the fusion. At P4 it is retired **for sources** when §9.1's rule says so and the owner confirms. It stays for items, diagnosis, PF freshness, map neighbours and graph nomination |
| Q2 | How is the default chosen, and when does it switch? | **REWORKED 2026-10-24 (owner: no made-up margins).** No point margin. The seed default is `argmax E[U]` on the bank posterior with `P(best)` reported (§9.1), confirmed by the owner. Online, learned fusion weights per consumer and query kind move from that seed (§9.2) |
| Q3 | E1's supplementary κ is 0.354/0.575. What is the label of record? | **DECIDED 2026-10-24.** The Opus-adjudicated labels, entered through a Dawid–Skene label-noise model so that low agreement widens the posterior (§9.1); κ disclosed |
| Q4 | Grouped or singleton? | **DECIDED 2026-10-24** (index both). The fixed 3-point rule is **replaced**: both are lists in the fusion with learned weights, and a variant is dropped only by expected utility (§9.1, §9.4) |
| Q5 | A 9B query session before the student lands? | **DECIDED 2026-10-24.** Yes: opt-in, off by default, idle exit (P1c) |
| Q6 | Voyage index: in parallel or on demand? | **DECIDED 2026-10-24.** In parallel, capped at $1 a run (`keep`), on vaults outside the checkout (after S1) |
| Q7 | Opt the Voyage organization out of training use? | **DECIDED 2026-10-24.** Yes, before P1b is enabled |
| Q8 | Synthetic query generator? | **DECIDED 2026-10-24.** GPT-6 Luna on `chatgpt_plan`. If the plan is down, report and ask before using OpenRouter (cap $5, `keep`). The owner's local books, personal use, artifacts local |
| Q9 | Student base and size? | **DECIDED 2026-10-24.** Screen `Qwen3.5-0.8B-Base` (873M, the "0.9"), `pplx-embed-v1-0.6b` and `Qwen3-Embedding-0.6B`; choose by §9.3's expected utility, in which latency counts through `p_late` |
| Q10 | Where does the student run? | **DECIDED 2026-10-24.** The GPU when ≥ 4 GiB is free and no exclusive job runs, else the CPU; its own 4G scope (`keep`) |
| Q11 | Where do vectors, models and env live? | **DECIDED 2026-10-24.** Vectors in `<vault>/.learnloop/vector-cache/`; models and env under `~/.local/share/learnloop/` |
| Q12 | Do the practice index and other consumers move? | **DECIDED 2026-10-24.** No. They stay on Qwen; revisit after P4 |
| Q13 | A small same-space Perplexity model, or a non-preview release? | **DECIDED 2026-10-24.** A new space through P1–P3, or a new list in the fusion (S-a/S-b) |
| Q14 | Fast linear-attention kernels? | **DECIDED 2026-10-24.** Deferred (S-d) |
| Q15 | Queue placement | **DECIDED 2026-10-24.** P0, P1a and P1b in Track P right after T1 lands; P2 as GPU time allows |

## Sources (read 2026-10-24)

- Voyage: [Voyage 4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/) · [embeddings docs](https://docs.voyageai.com/docs/embeddings) · [contextualized chunk embeddings](https://docs.voyageai.com/docs/contextualized-chunk-embeddings) · [FAQ (training opt-out)](https://docs.voyageai.com/docs/faq) · [voyage-4-nano card](https://huggingface.co/voyageai/voyage-4-nano) · [voyage-context-4 release](https://mongodb.com/company/blog/product-release-announcements/voyage-context-4-stop-worrying-about-chunking-with-our-best-performing-model) · [Vespa on asymmetric retrieval](https://blog.vespa.ai/asymmetric-retrieval-spend-on-docs-queries-for-free/)
- Perplexity: [model listing](https://huggingface.co/api/models?author=perplexity-ai&limit=100) · [collections](https://huggingface.co/api/collections?owner=perplexity-ai) · [v2 context 9B preview card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview) · [v2 late 0.6B card](https://huggingface.co/perplexity-ai/pplx-embed-v2-late-0.6b) · [pplx-embed-v1-0.6b](https://huggingface.co/api/models/perplexity-ai/pplx-embed-v1-0.6b)
- Student bases: [Qwen3.5-0.8B](https://huggingface.co/api/models/Qwen/Qwen3.5-0.8B) · [Qwen3-Embedding-0.6B](https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B)
- Learning to rank from implicit feedback: [Joachims, Swaminathan and Schnabel 2017, Unbiased Learning-to-Rank with Biased Feedback](https://arxiv.org/abs/1608.04468) (not re-read)
- Distillation: [NanoVDR](https://arxiv.org/abs/2603.12824) · [Query Encoder Distillation via Embedding Alignment](https://aclanthology.org/2023.sustainlp-1.23/) · [EmbedDistill](https://arxiv.org/abs/2301.12005) and [Learning Query Encoders Can Be Hard](https://arxiv.org/abs/2610.02749) (from the experiment spec §3, not re-read) · [vec2text](https://arxiv.org/abs/2310.06816) (not re-read)
