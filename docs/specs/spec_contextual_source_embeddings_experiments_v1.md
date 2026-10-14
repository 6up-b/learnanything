# Perplexity contextual source embedding experiments

**Status:** proposed experiment protocol; revised 2026-10-13 after two reviews. Code baseline: `4cf54a295` (this docs branch adds the owner's draft and reviews). No experiments have been run by this revision. See the [Opus review](../reviews/contextual-embeddings-spec-opus-review.md) and [independent Codex review](../reviews/contextual-embeddings-spec-codex-review.md).

**Decision to make:** does contextual encoding find canonical explanations and supporting evidence that LearnLoop otherwise misses, enough to justify another embedding space and, eventually, local Perplexity v2 9B residency? Answer three questions in order: do fixed delivery or direct reading suffice; does hosted contextualization beat cheap context using Qwen; only then, does `perplexity-ai/pplx-embed-v2-context-9b-preview` add enough to warrant local work? Vectors locate evidence; the tutor needs the actual text to reason and cite.

**Owner update, 2026-10-13:** proceed with the review direction and hosted-first experiment. The owner has added Perplexity and Voyage keys to LearnLoop's settings file. Perplexity contextual v1 through its API, and both `voyage-context-4` and `voyage-4-large` through Voyage's API, are required first-experiment arms. Proposed adapter settings `perplexity.api_key_env` and `voyage.api_key_env` default to `PERPLEXITY_API_KEY` and `VOYAGE_API_KEY`; both names are configurable. The [app config loader](../../src/learnloop/config/loader.py) loads these from its settings file into the environment (shell values take precedence). Adapters read the configured environment variable; manifests record only its name and availability, never its value. These adapters/settings are proposed experiment code, not existing app provider support. No credential files were opened for this revision.

## 1 Scope, ownership and constraints

The [Embedding Integration Map](../brainstorming/Embedding%20Integration%20Map.md), [Bitter Lesson Research Sweep](../brainstorming/Bitter%20Lesson%20Research%20Sweep.md), [embedding consumers spec](spec_embedding_consumers_v1.md), [sources spec](spec_source_practice_and_probes_v1.md) and [Reader spec](spec_reader_workbench_v1.md) remain the product basis. Expected value is a hypothesis, not a result.

| Consumer | Question and existing interface | Owner / comparison |
|---|---|---|
| Reader Ask | Why does this step follow? `find_sources(intent="explain")` is the planned retrieval seam | RW1c; fixed selection context, whole section, whole source |
| Canonical tutor grounding | Missing definition, theorem assumption or counterexample | T6 / `TutorSpanProvider`; same delivery for every retriever |
| Ask your library / compare | Unknown location or different source conventions; `find_sources`, `compare_sources`, `PinnedSpanProvider` | RW4a/RW4d; lexical/structural lookup and direct reading |
| Alternative / remediation | `alternative`, `remediate`; query an already-written gap, do not diagnose from similarity | RW1c/RW3b; existing correction links and role-aware judgment |
| Worked examples / source exercises | `worked_example`; distinguish finding an authored exercise from generating one | RW4b; deferred authoring pilot, direct known-section baseline |
| Local quick checks / margin roles | Passage/section views; authorial-role vocabulary | RW1a/RW1b/RW4e; no initial embedding replacement |

RW1c is Reader build order 5, after RW4a (order 3); RW3b and RW4d follow at order 5; RW4e is order 6. Reuse its role vocabulary without blocking this experiment on its classifier. Deliver a short decision memo to these owners before integration. Retrieval as context fits RW1c's existing ruling; offers still require learner action and a lookup is not an exposure. Reuse [typed instructional tools](../../src/learnloop/instructional/tools.py), server-derived policy and existing ledgers; do not build a parallel product orchestrator.

The October 11 one-embedding-model decision remains `qwen/qwen3-embedding-8b` via OpenRouter. Experimental spaces stay outside production. A second production source space requires an explicit owner amendment **and** the adoption bar in §7. The owner's go-ahead and keys authorize experiments, not that amendment. PF, diagnosis, router context, grading, identity and mastery remain outside this experiment. Embeddings nominate; verifiers and exact policy checks retain authority.

A separate **delivery fixes implementation stage**, starting now, owns the Reader neighbour correction, full blocks in place of tutor 240/600-character cuts, explicit reference resolution (for example “Theorem 3.2”), raising the 900-character label/verifier view, and automatic source-vector backfill after (re-)extraction when embeddings are enabled. This experiment consumes its pinned implementation and receipts as the D1 baseline; it does not reimplement those fixes. Record its commit and delivery policy before paired runs. Its implementation checks belong to that stage; experiment checks verify the consumed behavior.

## 2 Current baseline and evidence

| Code | Verified on this branch | Experiment consequence |
|---|---|---|
| [Embedding client](../../src/learnloop/ai/embedding.py), [OpenRouter adapter](../../src/learnloop/ai/providers/openai_embedding.py) | Flat inputs, one vector each; OpenRouter `data_collection="deny"`; no grouped-document contract | Hosted context needs a new adapter, not a model-name substitution; record provider identity or its absence |
| [Config](../../src/learnloop/config/schema.py), [backfill](../../src/learnloop/ops/embedding_backfill.py) | `embedding.enabled` and `backfill_enabled` default false; source recipe requires explicit selection; no automatic ingest backfill found | Distinguish today's effective baseline from an enabled, fully backfilled Qwen control; automatic backfill is the delivery-stage dependency |
| [Recipes](../../src/learnloop/source_retrieval/recipes.py) | Section header text plus independent block, 6,000-character body cap; skips furniture and blocks under 20 non-whitespace characters | “Independent Qwen” already has section context; preserve this production control and add matched-unit controls |
| [Store](../../src/learnloop/db/stores/embedding_vectors.py), [dense search](../../src/learnloop/source_retrieval/dense.py) | FP16 blobs; identity includes record/field/content hash/model/task; reuse by content; mean-centered cosine; partial coverage is possible across extractions | No contextual cache reuse by central text alone; exact ordinary cosine in matched comparisons; report coverage and fallbacks |
| [Search](../../src/learnloop/source_retrieval/search.py), [find_sources](../../src/learnloop/source_retrieval/find_sources.py) | `find_sources` exists with five intents, forces RRF for pagination, verifies 900-character views and returns up to 2,000 characters | Test this service itself, including a first-page pool variant without changing paging semantics |
| [Tutor provider](../../src/learnloop/source_retrieval/tutor.py), [compare](../../src/learnloop/source_retrieval/compare.py), [verifier](../../src/learnloop/source_retrieval/verify.py) | Retrieved and pinned tutor spans clip at 600; compare uses 2,400; verifier 900; tutor rewrite defaults off | Audit text at every delivery boundary; do not credit a changed rewrite or larger prompt to embeddings |
| [Span view](../../src/learnloop/reader/span_view.py), [Tutor QA](../../src/learnloop/tutor/tutor_qa.py) | Previous neighbours are ordered i−3, i−2, i−1. With a quoted single-block selection, the loop takes only the first two: i−3 and i−2, never i−1 or an after-block. Neighbours are 240-character previews; selected/in-view blocks are full | D0 preserves this observed defect for measurement; D1 consumes the separate fix. Without a quote or after filtering, counts can differ |
| [Quick-check views](../../src/learnloop/reader/reader_quick_check.py) | `section_view` and `passage_view` exist but are bounded; section view stops at 24,000 characters or 60 blocks. Helpers do not themselves apply model policy | Reuse section derivation, not an assumption that these return the whole permitted section |
| [Evaluation](../../src/learnloop/source_retrieval/evaluation.py) | T6 harness has two label passes, receipts and paired metrics; labels use 900-character views; no per-intent bank | Share the sources spec's planned per-intent bank; extend labels to evidence sets and full blocks |
| [Exam predicate](../../src/learnloop/content/sources/exam_material.py), [corpus policy](../../src/learnloop/source_retrieval/corpus.py) | Exam/held-out resolution spans revisions; `model_reader_withheld` also covers solutions and assessment-lane material | Apply policy before encoding and prompting, not just to returned hits (§4) |

[T6 corrected rerun §5.9](../reviews/t6-followup.md) reports 47 probability and 41 arxiv_v2 questions: verified dense-plus-BM25 nDCG@10 0.861/0.854 versus verified RRF 0.768/0.769. Differences on the **picked passages** were not significant; eight logged probability questions did not show a significant tutor gain. This supports a pool ablation, not a promised `find_sources` or answer-quality win. Historical query embedding p50 was about 4.5 s, verification about 7–8 s; remeasure current routes.

[B4](../reviews/slice-2-t6.md) found Gemini text below Qwen (nDCG@10 0.868 vs 0.915; 0.780 vs 0.855) and page images worse. Its labels and questions came from Marker text, with κ about 0.45–0.46: this does not settle image-dependent questions. Gemini and visual retrieval are deferred. Opus reports LFM2.5's 512-token limit and retention/training terms incompatible with the present data-collection requirement; those web claims are **unverified offline**. LFM is outside the first experiment pending verified context and retention compatibility.

Opus's inventory is about 20 sources, two short textbook excerpts, ten transcripts and 32 logged questions (15 Reader); largest source about 158k characters (~40k tokens). Its block/character counts were obtained from databases not opened here. Treat them as **reported inventory**, not a new census or a token-fit guarantee. The three tracked TOMLs have no `[embedding]` table; effective user settings and coverage remain unknown. Do not infer current production enablement from those TOMLs alone.

## 3 Research basis and offline limits

The following retains the owner's research basis and its reported findings. **External papers, model cards, endpoint availability, prices, licences and provider terms were not independently verified in this offline revision.** Recheck their contracts before execution; no external benchmark is evidence of a LearnLoop gain.

| Work | Relevant finding and limit | Consequence here |
|---|---|---|
| [Late Chunking](https://arxiv.org/abs/2409.04701), 2024, revised 2025 | Pooling chunks after encoding surrounding text preserves context lost by independent chunk encoding | Compare the same Perplexity model on independent chunks and grouped chunks to isolate contextualization |
| [Context is Gold / ConTEB](https://arxiv.org/abs/2505.24782), 2025 | Evaluates document-context-dependent retrieval and introduces in-sequence negative training | Include ambiguous passages and same-document distractors; defer a fixed public ConTEB slice until the local screen merits expansion |
| [Diffusion-Pretrained Dense and Contextual Embeddings](https://arxiv.org/abs/2602.11151), 2026 | Describes Perplexity v1's bidirectional representations and contextual document encoding | Supports the design lineage; does not establish v2 query compatibility with v1 models |
| [Contextual embedding beyond the gold passage](https://www.perplexity.ai/en-GB/hub/blog/contextual-embedding-beyond-the-gold-passage), September 2026 release | v2 uses a context-compression teacher to target supporting evidence; reported context-bench is privately held | Build an accessible LearnLoop evidence-set benchmark; do not depend on obtaining private context-bench |
| [Quantize by Drift](https://arxiv.org/html/2610.09227v1), October 2026 preprint | Measures module sensitivity through final embedding displacement. At the main budget, the allocation trails uniform precision on all three untouched models. Its study uses 2–4-bit weights, not this model | Treat drift as a diagnostic and candidate allocator; require uniform baselines, end-to-end retrieval and real packed-memory measurements |
| [Query Encoder Distillation via Embedding Alignment](https://aclanthology.org/2023.sustainlp-1.23/), 2023 | Direct precedent for pairing a lightweight aligned query encoder with a stronger document encoder | Establish alignment-only before adding a complex objective |
| [EmbedDistill](https://arxiv.org/abs/2301.12005), 2023 | Combines geometric matching with distillation and motivates asymmetric students | Compare vector alignment with ranking supervision against fixed teacher documents |
| [NanoVDR](https://arxiv.org/abs/2603.12824), 2026, v3 | A frozen document teacher and small query student; cosine alignment beats ranking alternatives in its visual-document experiments | Label-free query alignment is a serious baseline. Its retention and CPU speedups are not forecasts for mathematical source retrieval |
| [Learning Query Encoders Can Be Hard Even When Vector Retrieval Is Geometrically Easy](https://arxiv.org/abs/2610.02749), October 2026 preprint | A good frozen document geometry need not be easy for a learned query encoder to exploit | Test unseen sources and subjects; do not infer student quality from the teacher index alone |
| [RAG or Long-Context LLMs](https://arxiv.org/abs/2407.16833), 2024 | Sufficiently resourced long-context models won on average in its comparisons, while RAG reduced cost | Include direct section/document reading with the same frontier generator |
| [Beyond the Context Window](https://arxiv.org/abs/2603.04814), 2026 preprint | Full history beat fact-memory retrieval on some conversational benchmarks; prompt caching materially affects cost | Preserve the earlier brainstorm's full-context baseline and account for cached tokens; this is not a textbook benchmark |
| [BRIGHT](https://arxiv.org/abs/2407.12883), 2024, revised 2025 | Reasoning-intensive retrieval is difficult; explicit query reasoning can improve it | Compare raw questions with identical cached rewrites across embedding arms |
| [Are LLM-Based Retrievers Worth Their Cost](https://arxiv.org/abs/2604.03676), 2026 | Latency and robustness differ substantially; reasoning augmentation may reduce math/code retrieval quality | Report per-domain quality, end-to-end latency and rewriting ablations |

[Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) motivates 50–100-token generated chunk context, contextual BM25, and direct prompting for small knowledge bases (its reported guidance is under 200k tokens). Treat 150k-source/200k-scope sizes as revisit signals, not universal context or latency limits.

Hosted contracts to validate: [Perplexity contextualized embeddings](https://docs.perplexity.ai/api-reference/contextualized-embeddings-post), reportedly `/v1/contextualizedembeddings`, nested document/chunk inputs, contextual v1 4B/0.6B, 32K tokens/document, 120K/request and 16,000 chunks, int8/binary outputs; [Voyage contextual chunks](https://docs.voyageai.com/docs/contextualized-chunk-embeddings) and [pricing](https://docs.voyageai.com/docs/pricing), including `voyage-context-4` and `voyage-4-large`. Use int8 rather than binary for the initial Perplexity arm and implement the documented decoding/scoring. Validate each family's query method and query/document compatibility. No hosted v2 9B endpoint was established by the prior review; this is not a verified current absence.

The [v2 card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview) reportedly specifies separate query/document methods, fixed `[Q]`/`[D]` prefixes, 2048/1024 trained dimensions, unnormalized int8-valued outputs, preview incompatibility risk and an FP32 contextual projection. Opus also reports MIT licensing, a bundled vision tower, 24/32 linear-attention layers, ~33.6 GB FP32 checkpoint and no supported vLLM/SGLang/sentence-transformers path. These are loader-verification items, not tested guarantees; a large configured context is not a feasible 5090 workload. Do not carry the draft's untested `normalize_embeddings` call signature forward.

[Voyage 4](https://blog.voyageai.com/2026/01/15/voyage-4/) family compatibility does not establish compatibility with Perplexity. The [Perplexity late 0.6B](https://huggingface.co/perplexity-ai/pplx-embed-v2-late-0.6b) / late 9B pair reportedly uses 128-dimensional token vectors and MaxSim, a separate index rather than the contextual model's 2048-dimensional chunk space (§9).

## 4 Corpus, boundaries and representation

### 4.1 Extraction and candidate units

Build contextual indices **and labels on GLM-OCR extractions**, as `ingest/glm-ocr` becomes the main extractor, or explicitly pin a provisional extraction engine/revision. That branch's uncommitted code was not inspected here. All paired arms use identical snapshots; Marker results cannot be presented as GLM-OCR results. Record engine/model revision, extraction options, source bytes hash, extraction ID, ordered block text and structure. Re-extraction invalidates windows, vectors, generated headers, FTS variants, labels and cached evidence packets. Reanchors assist relabelling; they do not certify unchanged evidence.

Use outline/heading units and numbering where available; never invent missing heading depth. Inspect equations, captions, theorem leads, footnotes and references after extraction. Report lost content as an extraction failure, not a retriever miss. Opus's GLM footnote-discard, heading-flattening and layout-class claims need verification at ingestion handoff. The [block-role regex](../../src/learnloop/ingest/block_roles.py) identifies environment leads; it does not extract numbered references or resolve them. Consume the delivery stage's resolver and its unresolved/ambiguous statuses.

Freeze one common candidate map before comparing models: split oversized blocks deterministically with original character offsets; attach bare equations to their explanatory text; merge adjacent short transcript captions toward 300–600 tokens within one permitted section/time sequence. Do not merge across sources, policy boundaries or distinct theorem/exercise regions. Keep all original span IDs/offsets for labels and citations. Retain unmodified production blocks as a separate end-to-end control; its top-10 is not directly interchangeable with top-10 merged units. Report token-budget coverage too.

Start grouped encoding at 4,096 tokens/window, including markers, with section boundaries and no overlap. Assign every candidate exactly once. Freeze the tokenizer/boundary algorithm and stable ID tie-breaks. A secondary whole-source window is allowed only when the entire permitted segment fits the validated provider limit (reported Perplexity limit 32K); it is not the tutor's whole-source delivery arm. Split larger sources deterministically; report required support outside each window. Any later overlap arm emits a candidate once by a fixed ownership rule and never averages windows implicitly.

### 4.2 Policy and leakage

Use [exam_material](../../src/learnloop/content/sources/exam_material.py), `held_out_material` and [model_reader_withheld](../../src/learnloop/source_retrieval/corpus.py), plus caller/item-specific restrictions. **Windows never cross exam, held-out, solution or assessment-lane boundaries.** Do not remove forbidden blocks and join their former neighbours into one window. Teaching experiment inputs exclude these regions entirely, including from generated context, lexical headers, source summaries, rewrites, labels and full-section/source prompts. This experimental policy may be stricter than the current Reader's held-out-only neighbour filter; do not claim all current paths have identical filtering.

Persist policy verdicts and their dependencies with every artifact. When a unit is later marked `held_out_evaluation`, invalidate every dependent window/vector/header/label/packet, including old extraction references. Recheck current policy before retrieval and delivery; reject stale artifacts while rebuilding. Unresolvable marks fail closed. Source summaries depend on all text used to produce them, not only the central window. Do not embed exam material in this pilot; deciding whether to change existing independent exam indexing is outside it.

**Benchmark-held-out source families are not learner `held_out_evaluation` material.** Benchmark test documents remain permitted searchable source text; their questions, labels and development decisions are sealed. Learner-held-out exams must never enter the experiment. Split alternate editions, overlapping documents, questions/paraphrases, learner-profile variants and follow-up traces together; no test queries or gold support may enter headers, rewrites, prompts used for tuning, training or hard-negative mining.

### 4.3 Adapter, identity and receipts

The isolated adapter exposes `encode_documents(list[list[Chunk]]) -> list[list[Vector]]` and `encode_queries(list[PreparedQuery]) -> list[Vector]`. Preserve document/chunk IDs through response reordering and batching. Validate query mode, dimensions, output format, finite nonzero values, count/order, token limits and no silent truncation. Reject incompatible query/document spaces explicitly. Do not assume equal dimensions mean compatibility.

```text
document_space_id = hash(provider_endpoint, model_revision_or_alias_epoch,
                         serving_provider_or_unknown, precision_or_unknown,
                         tokenizer, extraction_engine_revision, recipe,
                         dimensions, output_format, decode_and_score_transform)
document_vector_key = hash(document_space_id, extraction_revision,
                           ordered_context_text_spans_offsets, target_offsets,
                           policy_fingerprint, all_generated_context_dependencies)
query_encoder_id = hash(provider_model_revision, query_mode_recipe,
                        precision, projection, dimensions, output_transform)
query_vector_key = hash(query_encoder_id, complete_effective_query)
run_id = hash(document_space_id, query_encoder_id, corpus_and_split_manifests,
              policy, prompts, retrieval_delivery_settings, budget, seed)
```

Keep vectors in research artifacts outside production `embedding_vectors`. Preserve raw provider responses/vectors privately; normalize a decoded FP32 scoring copy for exact cosine where supported. Raw integer values in [-127,127] are exactly representable in FP16, but normalized FP32 vectors are also valid evaluation artifacts: test the persistence round trip separately. Weight quantization, output quantization and stored dtype are different axes. Never substitute a different model's int8 vectors for an FP32 numerical reference.

Pin endpoint/provider where supported; otherwise record the alias, timestamp, returned model/provider and unknown numerics. A retry/resume checks manifest and canary vectors; changed aliases or incompatible outputs create a new epoch/index. Cache the first successful output, record tolerance for hosted nondeterminism, and report repeated canary drift. No claim of exact hosted reproducibility without immutable revisions. The current OpenRouter adapter does not expose provider pinning; pinning is proposed adapter work.

Reuse `model_call_receipts`, `judgment_ledger` and `source_tool_calls` for their existing roles. A research JSON manifest links grouped embedding jobs, labels and answer comparisons without inventing source-tool calls for operations that are not tools. Include request IDs, input hashes, usage, billed/estimated amounts, cache hits, retries, failures, elapsed time and resume status. Never log headers/keys or provider exception bodies. Local execution records zero provider billing and measured resources; reuse GLM-OCR's receipt convention when it lands, not an assumed current API.

## 5 Smallest first experiment: E0, hosted and no GPU

Target 3–5 working days, **≤ $25 billed and 0 GPU-hours**. This is a bounded pilot, not a promise that every arm and label will fit. Delivery-stage implementation and a full-book ingestion project are separate dependencies/budgets. All required hosted arms remain in scope even if direct reading wins; budget or endpoint failures produce an incomplete report, never a silent substitution.

### 5.1 Preparation and bank

1. In a later authorized execution, use [copy_tree_with_databases](../../src/learnloop/db/copies.py) for consistent vault copies, including WAL state. Keep private text/vectors/labels in gitignored `fixtures-local/contextual-embeddings/`; publish only permitted aggregates. This documentation task neither copies nor opens vault databases.
2. Capture a redacted effective-config allowlist (embedding enablement, model/route/dimensions, rewrite, pool, policy and caps), extraction inventory and coverage. Avoid a raw config/environment dump. Preserve today's baseline before enabling Qwen/backfill on copies. Consume the delivery stage's automatic backfill and wait for complete measured coverage, or label the baseline incomplete.
3. Freeze a 16-case smoke bank and **60–80 development questions**: roughly 20 Reader deictic selections, 20 distant same-source dependencies, 20 intent-stratified explain/remediate/alternative/worked-example/compare cases, plus direct lookup and no-support controls. Include all eligible logged questions as a separate real slice; 32 is the prior review's count, not a required yield. Tag transcripts, equations, extraction failures, long-range support and cross-source comparison. Preserve actual selection/history; a library question gets no oracle source location.
4. Reserve source families before question generation. This pilot has no credible 300-question sealed bank by assumption. Use leave-family-out exploratory checks where feasible, reporting independent-family counts. Later obtain permitted full books for confirmation, for example Axler LADR 4e and Grinstead–Snell; their reported CC BY-NC/GFDL licences and permitted uses need checking. Two books are two clusters, not hundreds of independent samples. Do not train from private excerpts/transcripts by default.

Strong writer: configured Sonnet 5.5 or GPT-6 Luna, with exact model/transport/prompt pinned; use a different strong model for adjudication. Source-derived questions must vary wording, include same-source distractors and propose support without revealing the reference label in every query. Generated questions, real questions and exact-reference lookups remain separate slices. No selection or reference is fabricated for a logged ambiguous question.

### 5.2 Labels and metrics

Record `query_id`, split/family/origin/intent/tags, question, selection and allowed history, allowed scope/policy, effective query, canonical evidence offsets, answerability, alternative sufficient sets and label provenance. A set expresses required answer AND support spans, with OR alternatives for other valid proofs; optional background never compensates for missing conditions. No-support cases have recall N/A and are scored for abstention/false attribution.

Pool top-20 candidates from every arm, reference targets, writer proposals and a seeded sample of non-hits. Use two independent strong-model passes, blinded to arm and ordered differently, reading full evidence and its needed context. The delivery stage's raised verifier cap does not itself guarantee full-block labels: record actual label input coverage and route oversize cases to an explicit bounded multi-pass review. Unjudged material stays unknown. Measure ordinal relevance agreement (Cohen's κ and confusion table) and separate agreement on required-support/set completeness.

A named strong adjudicator audits **all disagreements and every accepted sufficient set used by the primary endpoint**, plus a seeded 20% sample of agreements, negatives and unanswerable cases across strata. If the budget cannot cover that audit, reduce the scored bank before results or mark completeness pool-relative; do not call unaudited labels ground truth. Report model-only, adjudicated and any owner-reviewed counts. Owner review is optional. κ < 0.60 or unresolved sufficiency disagreements blocks a verdict; revise on development and relabel consistently.

Primary representation endpoint: **Complete Evidence@10 on context-dependent/support questions using common candidate units**. Also report Support Recall@10 (best-covered accepted set, fixed tie rule), Answer Recall, nDCG@10, MRR, role coverage, unknown-label share and coverage at a fixed evidence-token budget. Deduplicate citations by original span/offset; duplicated merged units do not earn extra recall. Measure evidence after filtering, verification, deduplication and final delivery, and report every clipping/omission reason.

Blind answer evaluation scores correctness, preserved assumptions, citation entailment and abstention in two randomized orders; adjudicate disagreements independently. Primary answer measure is the share passing all applicable criteria; retain component scores. Same tutor/version/effort and output policy for every arm; same permitted learner information. Bootstrap paired differences clustered by source and query family (10,000 resamples, fixed seed); report source-macro and query-weighted results, strata and failure counts. Too few independent families means exploratory intervals, not adoption evidence. Preselect one hosted finalist on development before confirmation; otherwise adjust for multiple comparisons and disclose selection. No repeated peeking or retuning after opening confirmation results.

### 5.3 Delivery arms first

| Arm | Context delivered to the same tutor |
|---|---|
| D0 today's context | Pinned baseline behavior, including the neighbour defect and current clips, on the common safe corpus |
| D1 fixed delivery | The separate delivery stage's full-block, corrected-neighbour and explicit-reference behavior; pinned implementation, policy and token limits |
| D2 whole section | Entire permitted section containing the known selection, with omissions/boundaries recorded; not the existing capped helper mislabeled “whole” |
| D3 whole source | Entire permitted selected source, or explicitly requested sources for a comparison, if within the actual generator context limit |

D0/D1 compare the same initial evidence where possible. D2/D3 apply directly to known-source/known-section questions. For unknown-location library questions, source/section choice must use the same non-oracle locator for all arms and its latency/errors count; a gold-location diagnostic is separately labelled oracle. If a section/source does not fit, record `does_not_fit` and run a separately named bounded fallback, never silent truncation.

Freeze a D1 retrieval evidence ceiling of 8,192 tutor tokens, with system/history/output reserves counted separately. Admit complete blocks in fixed order, recording any omission; oversize blocks use the shared offset-preserving split. D2/D3 use their actual full token sizes, so their extra tokens are a measured tradeoff, not an embedding gain. Report warm/cold cache tokens, p50/p95 latency, failures and billed/subscription usage. No Reader answer may receive solution or learner-held-out text even as a “direct” control.

### 5.4 Retrieval arms on the same bank

| Arm | Representation / purpose |
|---|---|
| R0 | Today's effective path, including keyword-only behavior if dense is disabled; descriptive production control |
| R1 | Fully covered Qwen with production recipe, centering and `pool_verify`; matched-unit ordinary-cosine Qwen control for representation comparisons |
| R1′ | Actual `find_sources` RRF/intent path versus first-page dense-plus-BM25 variant; record paging/deduplication separately |
| R2 | Matched Qwen + deterministic title, section path, preceding environment label and bounded preceding text; all policy-filtered |
| R3 | Matched Qwen + 50–100-token LLM chunk context from permitted source text, generated once without benchmark queries; contextual BM25 as a separately reported add-on |
| R4 | Perplexity API `pplx-embed-context-v1-4b`: grouped windows **and singleton-document control using that same contextual model**; independent `pplx-embed-v1-4b` sibling as a separate family baseline with its documented query encoder |
| R5 | Voyage API `voyage-context-4`: grouped windows and singleton control where supported; `voyage-4-large` via the same Voyage API as the required independent-family baseline |

R4 and R5 are **in E0**, not optional. Validate the independent Perplexity endpoint/query pairing before calls; failure blocks that subcomparison and is reported. Same-model grouped-minus-singleton isolates added document context more closely; different sibling models measure deployment alternatives, not a pure contextualization effect. Keep context generation separate from contextual BM25 to avoid confounding their gains. Generated headers aid indexing only; delivered citations are canonical text, never invented summaries.

For the representation screen use exact search, ordinary cosine where contract-valid, stable ID tie-breaking, identical units/scope/query information and no rewrite. For service comparisons preserve native scoring, rewrite defaults, pool and policy as explicitly named system arms. Cache identical rewrites if a later ablation enables them. Do not expand to every pool/window/rewrite combination. Run the D1 answer comparison only for the best one-model arm and hosted finalists selected on development; keep deterministic reference following identical across them and report pre- and post-reference coverage.

## 6 Budgets, determinism and execution records

Before calls, freeze `environment.json`, `corpus.json`, `splits.json`, `run_plan.json`, prompt hashes, seeds, candidate maps, provider/API contracts and the D0/D1 commits. Plan limits for total input/output tokens, paid calls, retries, per-request timeout, total wall time and evidence sizes from the actual inventory. No unset or infinite bound is executable. Default two retries for transient failures, zero for authentication/contract errors; every paid attempt counts. Randomize/interleave paired answer runs with a fixed schedule to reduce provider-load bias.

The hard E0 ceiling is $25 billed across **all** providers, vault copies and stages, including context generation, labels, embeddings, retries, verification and judging. Proposed allocation: $2 embeddings, $5 drafting/context, $10 labels/audits, $8 answers/verification. Free credits do not imply permanent zero cost. Report gross price estimates, credits, actual bills and subscription `estimated_only` tokens/quota/latency separately. A billed-only post-call check can overshoot: admit only when reconciled charges **plus conservative outstanding reservations** fit the remaining global budget. Unknown billing stays reserved until reconciliation. Keep the existing output-budget policy; do not lower generation limits just to shrink reservations. Dry-run estimates may require fewer cases or a revised plan, not bypassing admission.

The source-service daily guard defaults to $5 per vault and is distinct from this global cap. Only adjust it on experiment copies when the frozen plan requires it; preserve atomic reservation/accounting behavior. Hosted embeddings need equivalent admission/receipts even when they bypass the existing flat client. Missing prices or a changed endpoint stop the affected arm for contract review. Resume by complete input identity and saved successful results; never repay an entire batch to recover one completed item without recording it.

Use a separate experiment environment. This branch's `uv.lock` pins transformers **4.57.6**; the incoming local glmocr requires **≥5**, and pplx custom code reportedly **≥5.4**. Do not upgrade the app environment. Pin separate compatible dependencies/model code revisions after inspection; a common lower bound does not prove glmocr, vLLM, torch and pplx can share an environment. This revision ran no installs, downloads or API calls.

## 7 Stop rules and adoption

| Rule | Decision fixed before results |
|---|---|
| S1 labels / coverage | Stop verdicts for κ < 0.60, unresolved evidence sets, extraction/policy failures or materially incomplete arms. Report denominators and failures; fix development protocol before rerunning |
| S2 direct reading | If D2/D3 is superior, or non-inferior within a **2-point answer-pass margin with the paired 95% lower bound above −0.02**, and latency fits the pinned Reader budget, prefer it for known-location tasks. An interval merely including zero is inconclusive. Finish the required hosted screen, but do not expand local work for this stratum; unknown-location retrieval remains a separate question |
| S3 cheap context | Default no local escalation if contextual-minus-singleton gain is <3 points, or the best Qwen contextual recipe is within 2 points of the best hosted arm. A confidence interval must support an equivalence claim; otherwise say “insufficient evidence to expand,” not “context adds nothing.” Apply to both hosted families |
| S4 local experiment gate | Consider E1 only if the hosted finalist beats the best one-model arm by **≥5 absolute points Complete Evidence@10, paired 95% CI excluding 0**, and improves blind D1 answers. No Reader latency regression: paired p50/p95 and the frozen deadline must meet the incumbent budget. An underpowered pilot defers E1 until independent confirmation |
| Production adoption | Repeat the ≥5-point/CI bar on untouched permitted source families, with a blind answer-pass gain whose paired CI excludes 0, delivery/policy guardrails and no Reader latency regression. Then obtain the explicit one-model owner amendment. Passing E0 or E1 alone is not production authorization |
| Budget / futility | Stop at the declared spend/time/env/GPU bounds; report incomplete work. No post-hoc threshold changes or extra questions chosen after seeing failures; further tuning needs a new plan and fresh confirmation |

Direct-reading size triggers (~150k source / 200k scope tokens), actual context overflow, unacceptable latency, or repeated unknown-location failures justify revisiting retrieval. They do not automatically authorize GPU work. Compression's 2-point retrieval non-inferiority margin is separate from the second-space adoption bar. Better retrieval/answers do not establish better learning outcomes; Reader/practice specs own those evaluations.

## 8 E1: conditional local v2 batch pilot

Only after §7: ≤ one working day of environment work, ≤4 GPU-hours total including failed loads/profiling/indexing, and ≤$5 additional billed under a new frozen run plan. No persistent query residency. Use owner-chosen idle hours; no concurrent local GLM-OCR or substantial desktop/streaming GPU workload. Target ≤20 GiB process peak and explicit measured device headroom; if unavailable, stop or wait for a hosted v2 option.

The draft's old NVML mismatch is resolved: on the host (checked 2026-10-13 by the orchestrator), `nvidia-smi` reports an RTX 5090 with driver 615.78.08 and 32,607 MiB, about 2.2 GiB in use at idle. The Codex revision's sandbox had no device access, so its "could not communicate with the driver" result says nothing about the host. Host memory is the tighter limit: `free -h` showed 30 GiB RAM with about 9–11 GiB available and 19–26 GiB of swap in use while other work ran. Recheck both on the execution host before E1. No driver changes are part of this experiment. A ~33.6 GB FP32 checkpoint cannot be assumed loadable in host RAM; remove the local FP32-reference requirement.

On the reported Blackwell GPU, start **BF16**, loading shards directly with an explicit dtype and without materializing the full FP32 checkpoint. Preserve required higher-precision modules and inspect the real custom API. Then test supported **FP8 only if measured memory/latency pressure warrants it**; hardware support does not establish kernel/custom-model support. LLM.int8 is deferred behind FP8 failure (§9). No copied untested loader snippet is a deliverable.

Smoke: separate query/document methods, expected dimensions/order, context-sensitive vectors with fixed central text, correct output decoding, finite nonzero vectors, padding/batch invariance within tolerance and no truncation. Record module dtypes, unsupported kernels, disk/host/device peaks and unload completion. Measure batch-one query latency and serialized document indexing at 2k/4k/8k before longer windows; OOMs count. Cache BF16 reference outputs sequentially, exit the process before another precision, and evaluate grouped/singleton v2 against frozen hosted/Qwen finalists on common units and budgets. Hosted v1 is a model baseline, not a numerical reference for v2.

Do not extrapolate a hosted v1 gain to v2. Retain local work only for measured additional evidence/answer value or a prespecified non-inferior cost/latency benefit; otherwise stop. Any new full books require a new extraction/label manifest and all compared arms on that same corpus.

## 9 Deferred, with triggers

| Work | Trigger and retained protocol |
|---|---|
| One LLM evidence-completion round / 2×2 factorial | D1 leaves a material, audited unresolved-obligation slice after deterministic references/hydration. RW1c owns the option; compare best cheap vs contextual retriever, each with/without completion, same final token budget, max one round/two searches/one added verification round and frozen deadline. Separate retrieval, planning, assessment, delivery and generation failures |
| Completion assessor | Reuse `facet_span_support`/Decider infrastructure only after validating a new obligation-support task against strong labels; facet relevance is not proof of joint sufficiency. Planner sees question, allowed learner snapshot and delivered text, never gold labels. Use AND/OR evidence sets, optional scaffolding, contradictions and explicit `sufficient`, `no_progress`, `budget_exhausted`, `insufficient_source_support` exits. Check final claims against delivered evidence; budgets never imply success |
| Four-way precision matrix | E1 retained and a compressed deployment is actually needed: BF16 query/BF16 documents; compressed query/BF16 docs; BF16 query/compressed docs; both compressed. Freeze units and output transforms, exact scoring, 2-point non-inferiority margin; distinguish weight/output/storage precision |
| LLM.int8 | BF16 needs compression and working FP8 cannot meet requirements. Inspect supported modules, threshold, projection handling, packed bytes and latency on this actual GPU. No assumption that int8 is faster; stop at E1/new-plan resource bounds |
| Drift allocation | E1 has value and measured VRAM pressure remains after ordinary quantization. Freeze BF16 documents; perturb query layer bands first, compare uniform INT8/4-bit, simple mixed precision and drift allocation at equal packed-byte budgets. Use development/calibration data only, ≥3 resamples, actual kernels and combined-plan retrieval. For unit vectors, drift = 1−q0·q1 and score error ≤sqrt(2·drift); small drift does not guarantee rank/support retention |
| Query-only distillation | A retained 9B space has a measured online residency/latency bottleneck and permitted training sources exist. Freeze document teacher; compare projection-only, cosine alignment and ranking/relevance losses, then ≥3 seeds for the selected recipe. Retain nested 2k/10k/50k query budgets only as later costed learning curves, not available data. Split sources/paraphrases/traces before mining; no test teacher targets. Multi-positive loss must retain every required support, not only one easy answer span. Test unseen books/subjects and both replayed queries and final completion behavior; include CPU latency and teacher fallback |
| Late-interaction 9B-document/0.6B-query pair | Compare before expanding custom student training if online cost remains the bottleneck. Separate token-vector index/MaxSim, measured storage/scoring cost and compatible query API; no direct reuse of contextual chunk vectors or blanket visual-PDF superiority claim |
| Local Qwen query serving | Hosted query latency remains the bottleneck across source/router consumers; compare compatibility with the existing remote document space before choosing 9B residency. Same family is not proof of cross-provider equivalence |
| Public ConTEB, larger sealed bank / open books | Pilot merits confirmation and independently licensed/extracted source families exist. Freeze new sources and analysis before opening results. A 300-question target requires actual family diversity and a separate budget |
| Gemini / image / LFM arms | New image-grounded labels demonstrate extraction loss, or verified provider terms/context limits materially change. B4 does not justify routine image retrieval; LFM needs retention compatibility before any private text is sent |
| Source authoring pilot | Retrieval benefit established and sources/Reader owner schedules it. Compare known-section generation with retrieval; rubric criteria by fact, required methods stated in stems. Distinguish source-authored exercises from generated paraphrases; preserve provenance/correctness checks and authoring-only scope |

For deferred completion, key cached plans/packets by the full request, learner snapshot, extraction and policy revisions, prompts and budgets; keep parent-query/obligation IDs on traces and split them with their question family. Profile changes may alter optional scaffolding, not the mathematical requirements. Reuse the same planner/assessor across retrievers and validate final delivered claims.

Training uses only sources with verified permissions for the intended use; keep artifacts local by default. Open licensing is not an unrestricted training/publication licence. No legal conclusion about all embeddings or queries being derived works is assumed here.

## 10 Owner decisions D1–D14

“Answered” below records the October 13 instructions, not a fresh permission request. Defaults govern the proposed protocol unless changed; operational facts must still be measured.

| ID | Decision | Recommended default / status |
|---|---|---|
| D1 | Hosted or local first? | **Answered: hosted first; go ahead.** Local v2 only under S4/E1; no residency commitment |
| D2 | GPU schedule, memory and co-residency | E0 zero GPU; E1 ≤4 GPU-hours, ≤20 GiB target, batch exit, no local GLM-OCR contention. Owner's idle slot needed only if E1 is reached |
| D3 | Corpus | Permitted vault copies first; reported inventory must be checked at execution. Independently licensed full books for later confirmation, not an assumed 300-case sealed bank |
| D4 | Extraction baseline | **Answered: GLM-OCR is becoming main.** GLM extractions/labels, or explicit provisional engine/revision; invalidate on re-extraction |
| D5 | Success bar | ≥5 points Complete Evidence@10 with paired CI excluding 0, better blind answers and no Reader latency regression; independent confirmation for adoption (§7) |
| D6 | Second production space | **Not answered by go-ahead.** Explicit owner amendment after evidence. Keep production Qwen and isolated experimental namespaces meanwhile |
| D7 | Completion latency | Deterministic D1 only in E0. Later ≤one added verify round, only unresolved obligations, within a frozen measured Reader deadline; reference lookup still counts latency |
| D8 | Lookup versus offers | Retrieval as context is already permitted by RW1c. Deferred completion follows that contract; no unrequested learner-visible actions or exposure events |
| D9 | Training permissions | No E0 training; later verify source-specific permissions and keep artifacts private unless separately cleared |
| D10 | Evaluation models | Strong Sonnet 5.5/GPT-6 Luna routes, exact versions/transport recorded; independent strong adjudicator. No Decider label of record before validation |
| D11 | Delivery and Reader handoff | **Answered: separate delivery fixes stage starts now.** Consume its baseline and send per-consumer decision memos; Reader owns integration |
| D12 | Exam indexing | Exclude exam/learner-held-out/solution material from this experiment and invalidate on new marks. Existing independent exam indexing is not endorsed or changed here |
| D13 | Hosted keys/accounts | **Answered: keys added.** Configurable `PERPLEXITY_API_KEY` / `VOYAGE_API_KEY`; both hosted families required in E0, Voyage independent also via Voyage API. Never print secrets |
| D14 | Is dense live? | Unknown without effective-config/coverage receipt. Tracked configs lack `[embedding]`; check redacted settings at execution, enable/backfill copies for R1, preserve R0 as observed |

## 11 Deliverables and checks

| Package | Exit evidence |
|---|---|
| Baseline handoff | Delivery-stage commit, extraction engine/revision, safe scope and full coverage receipts; D0/D1 behavior reproduced |
| Hosted adapters | Perplexity/Voyage grouped and query smoke checks, contract/price pins, redacted credential availability, receipt/resume support |
| Corpus and labels | Candidate/dependency maps, splits, audit counts, label-quality gate and prohibited-material tests |
| E0 report | Paired delivery and retrieval results, blind answers for finalists, tokens/latency/bills, failure ledger and explicit S1–S4 decisions |
| Conditional work | Separate E1 plan/report only after gates; production proposal only after D6 amendment |

Reuse `learnloop embeddings compare --suite source_retrieval` as a baseline harness; its model flags do not implement grouped contextual APIs. Research code/commands remain proposed. No model download belongs in unit tests. Target checks: grouped response ordering, wrong query-method/mixed-space refusal, context and policy invalidation (including later held-out marks), full-source policy filtering, no truncation disguised as whole context, deterministic merge/offset maps and ties, nonfinite/zero vectors, budget admission with concurrent reservations, idempotent resume, alias drift and canonical citation support. Re-extraction tests must cover labels and generated context as well as vectors.

Reports under `docs/reviews/` contain aggregates and a failure ledger with IDs/reasons; private text remains in local artifacts. Report skipped/unavailable/error cases and budget stops with their original denominators. The first executable milestone is **the delivery-baseline handoff, frozen safe corpus and audited small bank, then D0–D3 plus Qwen and both required hosted families within E0's budget**. Neither local loading nor student training precedes it.
