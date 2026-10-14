# Review: `spec_contextual_source_embeddings_experiments_v1.md`

Reviewed 2026-10-13 against `main` at `4cf54a295`. The spec was written against `3e59d8770`, which is an ancestor of `main`, 330 commits earlier. The in-flight work checked was the `ingest/glm-ocr` worktree (uncommitted), `router/r2a` (`264b5ed3c`) and `reader/rw3a` (still equal to `main`).

The review was read-only:
- Code and docs were read on `main` and in the worktrees.
- Vault sizes were counted with `immutable=1` SQLite reads of the tracked fixtures (their WAL files are empty) and of the `fixtures-local` T6 copies.
- `nvidia-smi`, `free` and the app environment's package versions were checked.
- Web sources were checked by a research subagent and by me.

No paid calls were made, no models were downloaded and no repo files were changed.

Spec line numbers below refer to the untracked spec file as it stands.

---

## Summary (verdict)

- **Verdict: the question is right, but the spec is three to four times too large, and it puts the GPU first and the delivery fixes last.** On the owner's current library the decisive comparison is **read the whole section or source vs retrieve**, not Perplexity vs Qwen.
  - Every current source fits comfortably in a frontier model's context. The largest is about 158k characters, roughly 40k tokens. Whole vaults are about 29k, 22k and 95k tokens (§A2).
  - Anthropic's own contextual-retrieval guidance says to put a knowledge base under 200k tokens straight into the prompt.
  - Today's delivery throws away context before any embedding can matter: the 600-character tutor clip, a Reader neighbour window that skips the block just before the selection and everything after it, and 900-character label and verifier clips.
- **No hosted endpoint serves `pplx-embed-v2-context-9b-preview`.** Perplexity's API does serve the contextual **v1** models (`pplx-embed-context-v1-0.6b`/`-4b`, nested chunks, 32K tokens per document, $0.05/M), and Voyage serves `voyage-context-4`. "Does contextualization help on our corpus?" can therefore be answered for under $1 with no GPU. The local 9B is only needed for the v2-specific increment.
- **Three facts in §2 are now stale.**
  - `find_sources` (with intents), `compare_sources`, the four retrieval policies, the source service's spend ledger and the typed tutor tool interface all exist on `main`.
  - Exam protection is one predicate (`content/sources/exam_material.py`), not `corpus.py`'s exclusions.
  - The NVML mismatch is gone. However, host RAM is 30 GiB with 19 GiB of swap in use, so the 33.6 GB FP32 checkpoint and the spec's FP32 reference check are not feasible locally.
- **Biggest missed cheap wins:**
  1. Fix delivery: full blocks, nearest-first neighbours, section hydration, and explicit "Theorem 3.2" reference resolution. The regex for numbered environments already exists in `ingest/block_roles.py`.
  2. Check that dense retrieval is even on in the owner's vaults. The tracked configs have no `[embedding]` table, and source-block backfill only runs from the CLI.
  3. Add cheap contextual baselines that keep the one-model decision: a deterministic section and label header, and LLM-written chunk context embedded with `qwen3-embedding-8b`.
  4. Merge undersized blocks. 4,061 of arxiv_v2's 4,717 blocks are 40–90-character transcript captions.
- **Main upstream conflicts:**
  - GLM-OCR becomes the main extractor. It changes segmentation and span ids, so it invalidates vectors and labels, and windows must be rebuilt.
  - The GPU is shared. vLLM's default `--gpu-memory-utilization` is 0.92, and the owner runs desktop streaming.
  - The software environments differ. The app has transformers 4.57.6; glmocr needs transformers ≥ 5 and Pillow ≥ 12; pplx needs transformers ≥ 5.4 plus custom code.
  - The owner's **one-embedding-model** decision versus a second, source-only production space.
  - The Reader spec owns the consumers: RW1c is build order 5 and promises "offers, not actions".
  - Exam and held-out text would leak into contextual windows.
  - Licensing: the probability excerpt (Blitzstein & Hwang) and the YouTube transcripts are not openly licensed.
- **The corpus cannot support the sealed design.** There are about 20 sources in total, two of them textbook excerpts (Axler, 26 pages; Blitzstein, 47 pages), and 32 logged learner questions, 15 of them from the Reader. The "300 questions from held-out source families" and the 2k/10k/50k student banks need new, openly licensed full books. Axler's LADR 4e (CC BY-NC) and Grinstead & Snell (GFDL) would serve, and they also contain the distant cross-references the hypothesis is about.
- **Recommended first experiment (§E):** about 3–5 agent-days, ≤ $25 billed, **0 GPU-hours**. It covers delivery arms, cheap contextual-recipe arms, and hosted contextual-v1 against independent-v1 on a 60–80-question context-dependent bank, judged by strong models. Run the local 9B only if a contextual arm beats the best one-model arm by a pre-set margin. Defer drift allocation (Phase 3), distillation (Phase 4), LLM.int8, the 4-way precision matrix, the late 0.6B pair and the LFM and Gemini arms, each behind an explicit trigger.

---

## A. High-ROI additions (ranked)

Each item gives why it matters, its cost, and where it goes in the spec.

### A1. Fix delivery first, as a standalone win (no GPU, small code)
**Why:** the evidence the tutor receives is cut before any retriever can help.
- **Reader Ask (the spec's top use case, "why does this step follow?"):** the tutor gets the selection, the primary block and **at most 2 more neighbours**, each truncated to **240 characters** (`reader/span_view.py:29-31`, `:63-65`; `tutor/tutor_qa.py:128`, `:1468-1482`).
  - The neighbour list is ordered `[i-3, i-2, i-1]` followed by the next blocks (`span_view.py:113-115`), and the loop stops at `max(4, len(spans)+2)`.
  - So for a quoted single-block selection the tutor gets blocks **i-3 and i-2**. It never gets the block just before the selection or any block after it.
  - This is a defect independent of embeddings. A two-line ordering fix plus a test closes it.
- **Tutor spans:** retrieved and pinned spans are cut to 600 characters (`source_retrieval/tutor.py:63`, `:105`, `:395`). This covers practice, feedback and library questions, and RW4a's "Ask the tutor about these".
- **Other clips:**
  - The verifier sees 900 characters (`verify.py:38`; `find_sources.py:68`).
  - Relevance labels see 900 characters (`evaluation.py:131`, `:646`), so the benchmark itself cannot credit a theorem condition past that point.
  - `find_sources` returns 2,000 characters (`find_sources.py:69`) and `compare_sources` 2,400 (`compare.py:70`).
- **Hydration already exists.** `reader/reader_quick_check.py:398-424` (`section_view`, up to 24,000 characters) and `:490-531` (`passage_view`) use the guide's section derivation (`reader/reader_guidance.py:261`).

**Cost:** S. Swap the clips for token-bounded full blocks; give the Reader nearest-first neighbours or a `passage_view`/`section_view` (exam-filtered as `_reader_source_spans` already does); label from full blocks.

**Where:** promote §8.2's "600-character cap ablation" (spec lines 334) to a new **Phase 0b "delivery fixes"** ahead of Phase 1, measured with a blind answer judge. Ship it through RW1c, or a small fix stage before RW1c, whatever the embedding verdict.

### A2. Make "whole section / whole source in context" the first question
**Why:** the owner's corpus is small.

| Vault | Sources | Blocks | Characters | Roughly |
|---|---|---|---|---|
| probability | 4 | 579 | 114k | 29k tokens |
| linear_algebra | 4 | 1,074 | 89k | 22k tokens |
| arxiv_v2 | 12 | 4,717 | 378k | 95k tokens |

These are `immutable=1` counts of `fixtures/*/state.sqlite`. The largest single source is the arxiv PDF at about 158k characters (~40k tokens). B4 says the textbook vaults are excerpts: Axler at 26 pages and Blitzstein plus two MIT problem sets at 47 pages (`docs/reviews/slice-2-t6.md:465-466`, `:544`).

- Anthropic: "If your knowledge base is smaller than 200,000 tokens … you can just include the entire knowledge base in the prompt" (https://www.anthropic.com/news/contextual-retrieval).
- The tutor route is Codex `gpt-5.6-sol` at low effort on the subscription (`fixtures/probability/learnloop.toml:497`, `:504`), so the marginal cost of a long prompt is latency, not dollars.
- Metered judges are cheap with caching: Sonnet 5.5 cache hits are 0.05× ($0.10/M), and Haiku 5.5 is $0.01/M cached (https://platform.claude.com/docs/en/build-with-claude/prompt-caching; OpenRouter passes `cache_control` through, https://openrouter.ai/docs/features/prompt-caching).

**Cost:** S. It reuses `section_view` and adds an extraction-text loader.

**Where:** §8's "Direct selected section" and "Direct document" arms (spec lines 303-304) move into the first experiment. The spec should also state the trigger at which retrieval is needed at all: a source over about 150k tokens, or a question scope over about 200k.

### A3. Make sure dense retrieval is actually on, and backfill it automatically
**Why:**
- None of the three tracked vault configs has an `[embedding]` table. `EmbeddingConfig.enabled` defaults to false (`config/schema.py:2000-2004`), and `search_spans` then marks the dense index `disabled` (`source_retrieval/search.py:344-346`).
- The source-block recipe never joins the default backfill (`source_retrieval/recipes.py:10-17`), and backfill is "explicit, bounded embedding work. Never called by sync or rebuild" (`ops/embedding_backfill.py:1`).
- So unless the owner's user-level config enables embeddings, today's real "production" is BM25 plus provenance plus verification.
- Every new extraction loses dense coverage until someone runs a CLI command. That will include every GLM-OCR re-extraction (`dense.py` docstring: partial coverage).
- T6 measured keyword alone at 0.632/0.465 nDCG@10 against meaning at 0.791/0.806 (`docs/reviews/t6-followup.md:521-522`).

**Cost:** about $0.002 per full re-index. The T6 backfill of 4,715 blocks cost $0.0017 (`t6-followup.md:303`). An automatic post-extraction backfill job is M.

**Where:** add to §2 and to Phase 0 step 1: run `learnloop config effective --vault <copy>` to record the true production baseline. Add an "automatic source-block backfill" item to §11, owned by the embedding consumers or by the GLM-OCR stage.

### A4. Cheap contextual baselines inside the one-model decision
**Why:** the spec compares Perplexity against independently encoded Qwen. Contextualization is also available as text, which keeps `qwen3-embedding-8b`, the existing store and the existing harness.
- **(i) A deterministic contextual recipe.** Source title, the section path with depth recovered from numbering, the nearest preceding numbered-environment label, and the head of the previous block. It uses the existing regex for leads such as "Definition 4.2." or "Theorem 1" (`ingest/block_roles.py:58-63`).
- **(ii) LLM-written chunk context.** Anthropic's Contextual Retrieval prepends 50–100 tokens per chunk.
  - Contextual embeddings alone cut top-20 failures by 35%, and by 49% with contextual BM25.
  - It costs about $1.02 per million document tokens with caching (https://www.anthropic.com/news/contextual-retrieval).
  - For this corpus that is well under $1 on Haiku or Sonnet 5.5 with the source cached, or free on the ChatGPT plan.
- Contextual BM25 comes free with (ii): index the same context in FTS.

**Cost:** S–M. Add a recipe variant plus a script, then run `learnloop embeddings compare --suite source_retrieval --model …` (`cli/embeddings.py:181-204`; `--embedding-price-per-million` exists).

**Where:** new §8 arms "Qwen + structural header" and "Qwen + LLM chunk context", next to "Matched independent Qwen" (spec line 297). If (ii) captures most of the contextual gain, the local track stops (§E S3).

### A5. Measure contextualization through hosted contextual APIs before any GPU work
**Why:** no host serves the v2 9B.
- The Hugging Face card says "This model isn't deployed by any Inference Provider".
- OpenRouter's `/embeddings` input has no per-document grouping (https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings.md).
- The Perplexity blog says only "working on making the model available through the Perplexity API" (https://www.perplexity.ai/hub/blog/contextual-embedding-beyond-the-gold-passage).

But two hosted contextual models do exist:
- **Perplexity `POST /v1/contextualizedembeddings`** (https://docs.perplexity.ai/api-reference/contextualized-embeddings-post; https://docs.perplexity.ai/docs/embeddings/contextualized-embeddings):
  - models `pplx-embed-context-v1-0.6b` and `pplx-embed-context-v1-4b`;
  - input is `array[array[string]]`, with at most 32K tokens per document, 120K per request and 16,000 chunks;
  - output is int8 or binary only;
  - $0.008/M and $0.05/M. Its independent sibling `perplexity/pplx-embed-v1-4b` is on OpenRouter at $0.03/M.
- **Voyage `voyage-context-4`** ($0.12/M, 200M free tokens) against `voyage-4-large` on OpenRouter (https://docs.voyageai.com/docs/contextualized-chunk-embeddings; https://docs.voyageai.com/docs/pricing). The blog names voyage-context-4 as its main contextual baseline.

"Same model, context vs no context" is then measurable in two model families for well under $1, since the whole corpus is under 1M tokens.

**Cost:** S. It needs a small grouped-document adapter, which is the spec's own `encode_documents(list[list[Chunk]])` (spec line 115), plus a Perplexity API key and a Voyage key.

**Where:** replace the opening of Phase 1 (§7) with "Phase 1a: hosted contextual screen". The local 9B in Phase 1b runs only if contextualization helps (A4/A5) and the v2-specific increment is the open question.

### A6. A deterministic explicit-reference resolver
**Why:** "by Theorem 3.2", "Lemma 4", "(3.1)" and "the previous lemma" are the spec's motivating case (spec lines 7, 19).
- Explicit references are a lookup, not a similarity problem.
- Numbered-environment leads are already classified at ingest (`ingest/block_roles.py:58-80`), and GLM-OCR keeps equations as `$$…$$` LaTeX, including any `\tag`s (glm worktree `ingest/extractors/glm_ocr.py:718-726`).
- A per-extraction label index plus a mention regex delivers the referenced block directly.
- The spec lists "explicit reference following" as a baseline arm (spec line 296) as if it existed. Nothing on `main` resolves references.

**Cost:** S.

**Where:** the §4.4 step 2 "follow explicit source references", built as a reusable function (and as a tutor tool, A8). It is a standalone win for RW1c.

### A7. Merge undersized blocks (transcripts, bare equations)
**Why:**
- 4,061 of arxiv_v2's 4,717 blocks are `Caption` blocks from ten YouTube transcripts, each 40–90 characters (`fixtures/arxiv_v2`, block-type counts).
- 74 of probability's 579 blocks are `Equation` blocks. `MIN_BLOCK_CHARS = 20` (`recipes.py:47`) keeps most of these fragments as independent records.
- A 40-character caption is a poor unit for both embedding and delivery. Grouping by time or size, and attaching display equations to their surrounding text, is deterministic and model-independent.
- Transcript fragments will dominate any block-level or source-macro metric unless they are handled separately.

**Cost:** S.

**Where:** §4.1 (spec lines 86-88) says only how to split *oversized* blocks. Add a minimum unit (for example 300–600 tokens for transcripts) and report transcripts as their own slice in §5.3.

### A8. Reuse what the sources track built: intents, the tool interface, the planned per-intent bank
- **Strata.** `find_sources` intents (`explain`, `remediate`, `alternative`, `worked_example`, `compare`; `source_retrieval/find_sources.py:63-64`) map one-to-one onto the spec's §1.1 rows and §5.1 strata.
  - The sources spec already plans "a per-intent query set in the T6 harness" (`docs/specs/spec_source_practice_and_probes_v1.md:1206`). It is not built: `evaluation.py` has no intent.
  - Build that bank once and let both specs use it.
- **The pool.** `find_sources` always uses `POOL_HYBRID_RRF` (`find_sources.py:504-512`, because of paging). T6 measured that pool as the weaker one (pool_verify 0.861/0.854 against hybrid_verify 0.768/0.769; `t6-followup.md:526-527`).
  - RW1c and RW4a will retrieve through `find_sources` (`docs/specs/spec_reader_workbench_v1.md:403`).
  - So test `dense_plus_bm25` for the first page of `find_sources`. This is a cheap, model-independent win.
- **Tools.** The typed tool interface (`instructional/tools.py:1-19`, `:136-145`) is the natural home for "source navigation plus full sections" (spec line 305). Add `read_section` and `resolve_reference` tools under the same server-derived policy, instead of a new orchestrator.

**Cost:** S–M. **Where:** §1.1, §2, §5.1, §8 and §11.

### A9. Openly licensed full textbooks as the scale and independence corpus
**Why:**
- The current vaults cannot support held-out source families, distant cross-references at book scale, or licence-clean training data (§B7, §C7).
- Axler's *Linear Algebra Done Right* 4e is CC BY-NC 4.0 (https://linear.axler.net/; OAPEN PDF https://library.oapen.org/bitstream/20.500.12657/85067/1/978-3-031-41026-0.pdf). The owner already reads an Axler excerpt.
- Grinstead & Snell's *Introduction to Probability* is GFDL (https://open.umn.edu/opentextbooks/textbooks/21).
- Ingesting each through GLM-OCR also tests the new extractor's structure.

**Cost:** M. Two imports, at $0.03 per million tokens on hosted z.ai (https://docs.z.ai/api-reference/tools/layout-parsing), or free locally.

**Where:** §5.1 (spec lines 160-172). Use them for the sealed set and for any later Phase 4 training; the owner's vaults stay the real-question slice.

### A10. Take what GLM-OCR gives for free, and know what it does not give
- **What it gives:**
  - `$$LaTeX$$` equation blocks.
  - Markdown tables (LearnLoop converts HTML to GFM).
  - Heading-based or outline-based units. "Embedded outlines win" (glm worktree `docs/reviews/glm-ocr-primary-ingestion.md`; `glm_ocr.py:820-935`).
  - `Caption` blocks from `figure_title`.
- **The limits:**
  - Every `paragraph_title` is flattened to `##`, so section depth must be recovered from numbering.
  - The hosted z.ai API reports only `image | text | formula | table`, so captions and titles come only from a self-hosted `native_label`, which is inferred from code, not observed.
  - **There is no theorem, definition or proof class.** PP-DocLayoutV3's 25 classes are visual.
  - By default it **discards** footnotes, references and aside text, so a footnoted assumption would never reach any index (https://github.com/zai-org/GLM-OCR; https://huggingface.co/zai-org/GLM-OCR).
- **Window recipe:** use outline or heading units as window boundaries, recover depth from numbering, attach captions to figures, keep display equations inline with their text, and mark theorem boundaries with the `block_roles` lead regex.
- The footnote-discard default is an ingest issue to raise with the GLM-OCR stage.

**Where:** §4.1.

### A11. Cheapen evidence-completion assessment, not labelling
- The Decider already runs a per-span content check (`facet_span_support`, `decider_judgments.py:50-52`) at $0.02/M input. A "does this passage support this obligation" `ChoiceQuestion` with LLM fallback is the cheap assessor for §4.4 step 3.
- If its verdicts are logged to `judgment_ledger` under the same input hash, it also feeds the Decider tier-2 agreement data.
- **Do not cheapen the relevance labels.** The labels are already cheap: the whole T6 evaluation billed $1.18 (`t6-followup.md:301-310`). The owner wants strong judges for evaluation (memory `eval-model-quality.md`), and the Haiku labels had κ of only 0.66–0.69 (`t6-followup.md:316`, `:511`), falling to 0.45 on B4 (`slice-2-t6.md:563-564`).
- Spend on Sonnet 5.5 or GPT-6 Luna labels that read full blocks, and use the Decider as a third, disagreement-finding vote.

**Where:** §4.4 and §5.2.

### A12. Pin embedding provider numerics (a small identity fix that affects production)
- OpenRouter routes `qwen/qwen3-embedding-8b` across Nebius, DeepInfra and SiliconFlow. SiliconFlow serves fp8 (OpenRouter models API, per the research subagent).
- The client sends only `provider: {data_collection: "deny"}` (`ai/providers/openai_embedding.py:108`), and the store keys vectors by `model_id` only (`db/stores/embedding_vectors.py:47-70`).
- So query and document vectors can come from different numerics under one identity.
- The spec's §4.2 identity scheme already includes precision and quantizer. Apply the same rule to the current route: pin the provider order with fallbacks off, or record the serving provider.

**Where:** §4.2 (spec lines 96-111) and §2.

### A13. (Alternative use of the GPU) A local Qwen3-Embedding query encoder for latency
- Query embedding is the slowest cheap step: p50 4,478 ms, maximum 6.8 s (`t6-followup.md:468`). Router R2 flags the same latency (`docs/specs/plan_router_r2_v1.md:43`, `:574` on `router/r2a`).
- Serving Qwen3-Embedding locally would help every consumer (tutor, R2c, `find_facets`) within the one-model family. It needs its own model identity, or a cross-encoding compatibility test using the spec's own query/document identity matrix.
- Weigh this against 9B residency before committing the GPU.

**Where:** §1 or §12, as a competing option for "justify local GPU residency" (spec line 5).

---

## B. Revisions (stale or wrong statements)

| # | Spec location | What is stale or wrong | Fix |
|---|---|---|---|
| B1 | §2 lines 55, 154, 450; §11 line 423 | "Neither that spec file nor `source_retrieval/find_sources.py` is present … Do not assume the planned `find_sources` service exists." Both exist (added in `1124b863b`; `docs/specs/spec_source_practice_and_probes_v1.md`). Also on `main`: `compare.py`, `policy.py` (the four policies, `:19-20`), `service_spend.py` (daily guard, `:1-37`), `instructional/tools.py` (typed tools, S4), `instructional/needs.py` (source-first needs, VOI site `source_need_selection`, `scheduling/voi_forecasts.py:59`) | Rewrite §2's last paragraph. Run Reader and library questions through `find_sources(policy="reading")` / `find_sources_for_caller` (`find_sources.py:669-684`), tutor questions through `TutorSpanProvider`, pinned asks through `PinnedSpanProvider`, and comparisons through `compare_sources`. Map §1.1 rows to intents (A8) |
| B2 | §4.3 line 119 | Cites `corpus.py` teaching and item exclusions. Exam protection is now **one predicate**: `content/sources/exam_material.py` (docstring `:1-80`; `exam_material` `:533`, `exam_withheld` `:571`, `held_out_material` `:587`). Exam members count in every revision; `held_out_evaluation` units count whatever their role; unresolvable marks fail closed. Model readers also drop solutions and the assessment lane (`corpus.model_reader_withheld`, `:419-444`) | Cite the predicate. Windows never cross an exam, held-out or solution boundary. Exam extractions are never windowed with teaching text. The window's dependency key includes the predicate's verdicts, because a later held-out mark must invalidate windows built before it. Re-check the predicate at serve time (§C6) |
| B3 | §2 table, the Tutor provider row, line 46 | Correct but incomplete. The 600-character clip also hits pinned spans (`tutor.py:395`). The verifier sees 900 characters (`verify.py:38`), labels see 900 (`evaluation.py:131`), `find_sources` returns 2,000 (`find_sources.py:69`) and compare uses 2,400 (`compare.py:70`). The Reader gets 240-character neighbours in the wrong order (A1) | List every clip. State that labels and verification must read full blocks before "delivered evidence" (§5.3) is meaningful |
| B4 | §2 table, the Search row, line 45 | It does not mention that `find_sources`, the API RW1c and RW4a will use, forces `hybrid_rrf` (`find_sources.py:504-512`) | Add the row. Evaluate the `find_sources` path itself, not only `TutorSpanProvider` (A8) |
| B5 | §8 "Current production" arm, line 295 | It assumes the Qwen dense route is live. The vault configs have no `[embedding]` (A3) | Phase 0 records `config effective` and the dense coverage status per copy. The production baseline may be "BM25 + provenance + verify" |
| B6 | §6 step 1, line 213 | "NVML driver/library mismatch … check current health." `nvidia-smi` now works: RTX 5090, driver 615.78.08, CUDA UMD 13.4, 29.8 GB free at 22:04, with about 2.4 GB used by the desktop and `sunshine` streaming and 54% utilization. **Host RAM is 30 GiB, with 12 GiB available and 19 GiB of swap in use** (`free -g`) | Replace the NVML note. Add a host-RAM constraint: load shard by shard straight to GPU in BF16, never materialize the FP32 checkpoint. Drop §7.3's "small FP32 check where resources permit" (spec line 285): 33.6 GB exceeds both the 32 GB of VRAM and the host RAM. If FP32 is wanted, use hosted int8 or v1 outputs as the external reference instead |
| B7 | §5.1 lines 160-172, §5.1 sealed bank, §10 data | It treats three vaults as "candidate domains" and plans a 300-question sealed set from held-out families, plus 2k/10k/50k training banks. Actual inventory: about 20 sources, two of them short textbook excerpts and ten YouTube transcripts; 32 logged questions (probability 10, linear_algebra 21, arxiv_v2 1; 15 from the Reader) | State the inventory. The sealed set becomes held-out open books (A9) plus leave-one-source-out within vaults, labelled exploratory. Drop the 50k bank until open books exist |
| B8 | §3 line 80; §8 lines 298, 308 | "Gemini Embedding 2 … LFM2.5" arms, and the late 0.6B as "particularly for visual PDFs". B4 already measured gemini-embedding-2 **text** below qwen3-8b on both copies (0.868 vs 0.915; 0.780 vs 0.855) and page images worse (`slice-2-t6.md:542-574`). LFM2.5 has a 512-token context, and its OpenRouter page says "Successful OpenRouter requests and embeddings may be retained and used to train Liquid models", against the client's `data_collection: "deny"` (`openai_embedding.py:108`). Gemini's context is 8,192 | Cite B4. Drop LFM. Drop or demote Gemini. Drop "visual PDFs" as a motivation (B4's verdict, `spec_source_practice_and_probes_v1.md:1097`) |
| B9 | §7.1 lines 227-256 and §6 step 2 | LLM.int8 is the first deployment. BF16 is about 16.8 GB (8.40B parameters, Hugging Face API) and fits on 32 GB when nothing else is resident. Blackwell has native FP8: transformers lists on-the-fly `FINEGRAINED_FP8`, `FBGEMM_FP8` and torchao 8-bit (https://huggingface.co/docs/transformers/quantization/overview). LLM.int8's default threshold cut throughput by 55–76% in a reported benchmark (https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1867). No public LLM.int8 report exists for sm_120. `llm_int8_skip_modules=["contextual_projection"]` is redundant: the model declares `_keep_in_fp32_modules`, which transformers' bnb-8bit quantizer honours, per the code read. The card says outputs are **unnormalized** int8-valued floats; check whether `encode(normalize_embeddings=…)` is a real parameter in `modeling_pplx_contextual.py` before relying on it | Reorder Phase 1b: BF16 first (also the reference), then FP8, then LLM.int8 only if FP8 fails. Profile with `threshold` noted. Correct the snippet |
| B10 | §4.2 lines 113, 115 | "Store normalized FP32" and "do not invent a local execution type". The v2 output is `round(tanh(x)*127)`, integers in [-127, 127], which FP16 stores **exactly**. Normalizing first is what loses precision. The in-flight GLM-OCR stage already defines local zero-cost receipts ("local calls cost zero", glm worktree `docs/reviews/glm-ocr-primary-ingestion.md`) | Store the raw int8-valued vector (exact in the existing FP16 blob, or a true int8 blob) and normalize at read. Reuse GLM-OCR's local-receipt convention |
| B11 | §6 step 5 and run plan, lines 217, 221 | "Freeze frontier tutor/judge model IDs" and `max_cost_usd`. The tutor is Codex `gpt-5.6-sol` low on the subscription (`fixtures/probability/learnloop.toml:497`, `:504`), so direct-reading cost is latency and quota, not dollars. The harness's caps are **reservations at the full 16,384-token output budget**: T6 planned $11.57 and $10.10 against $0.29 billed (`t6-followup.md:289-291`). The source service guard is $5 per day per vault (`config/schema.py:2267`) | Cap on **billed** spend through a driver hook, as T6 did (`t6-followup.md:292-297`). Raise the copy's daily guard explicitly. Report Codex usage as `estimated_only` (`ai/spend.py:66`) |
| B12 | §5.2 line 182 | "Two independent LLM labeling passes … following the existing harness." The existing harness used Haiku 5.5 with κ 0.66–0.69, on 900-character clips | Use Sonnet 5.5 or GPT-6 Luna (memory `eval-model-quality.md`) on full blocks. Set a κ gate (§E S1) |
| B13 | §8.2 authoring pilot, line 336 | It predates the owner's rubric rule (memory `rubric-criteria-by-fact.md`, Oct 13) | Authored questions phrase criteria by fact; a required method is stated in the stem |
| B14 | §3 line 66; §4.2 line 94 | Correct, with additions from the card (https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview): MIT licence; fixed `[Q]`/`[D]` prefixes; a bundled Qwen3.5 vision tower (333 `visual.*` tensors) inside the 33.6 GB; 24 of 32 layers are linear attention; the blog evaluates documents of up to 32,768 tokens; there is no vLLM, SGLang or sentence-transformers support | Add these. Most current sources fit one 32k window, so add a "whole source ≤ 32k" window arm. Skip loading the vision tower if the code allows |

Verified correct as written:
- the T6 numbers (`t6-followup.md:524-529`, `:464-470`);
- the 2048/1024 Matryoshka dimensions and the preview-compatibility warning;
- FP32 `contextual_projection`;
- the late 0.6B pair (128-dimensional MaxSim, shares the 9B's space);
- all six cited arXiv papers and their characterizations (the "can hurt" wording for 2604.03676 is slightly stronger than the paper's "may reduce");
- the Voyage cross-size compatibility claim.

---

## C. Conflicts with upstream work

| # | Conflict | Resolution | Owner |
|---|---|---|---|
| C1 | **GLM-OCR replaces Marker** (worktree `learnanything-glmocr`, uncommitted). New extraction keys (`map1` version), positional span ids `s{ordinal}` (`glm_ocr.py:884`), different text (LaTeX, GFM tables, discarded footnotes), flat headings. "Reader rereads prefer GLM-OCR" (glm review). Every window, vector key, evidence label and span id built on Marker extractions dies on re-extraction | (a) Run the delivery and recipe arms (E0) now on frozen Marker copies; they barely depend on the extractor. (b) Build the contextual index, the window recipe and the sealed bank **after GLM-OCR lands**, on re-extracted copies, or carry the `source_span_reanchors` map. (c) Make the extractor and its version part of `document_space_id` (spec line 99 already has `extraction_revision`). (d) Ask the GLM-OCR stage for automatic source-block backfill (A3) and to keep footnotes | GLM-OCR stage (ingest), then this spec's corpus package |
| C2 | **One GPU, three tenants.** Local GLM-OCR runs under vLLM, whose default `--gpu-memory-utilization` is **0.92** (https://docs.vllm.ai/en/latest/configuration/engine_args.html), plus PP-DocLayoutV3 on CUDA. The 9B embedder needs about 16–19 GB in BF16. The owner's desktop and streaming are live (`nvidia-smi`). The spec's targets (≤ 16 GiB, ≥ 12 GiB free; spec line 270) ignore GLM-OCR | Policy: hosted z.ai is GLM-OCR's default (`backend = "auto"` in the glm config diff). Any local GPU service is a **batch job** with an explicit memory fraction (vLLM `--gpu-memory-utilization ≈ 0.15–0.2` for the 0.9B GLM-OCR; about 2.65 GB of weights per https://huggingface.co/zai-org/GLM-OCR). The 9B indexer never runs while local GLM-OCR or the owner's GPU workload is active. Nothing stays resident for interactive queries until a residency decision (D2) | Owner (D2); this spec's runtime package; GLM-OCR stage's deployment notes |
| C3 | **Environment pins.** The app has transformers 4.57.6 (`uv.lock:2787-2804`, pulled by marker-pdf), torch 2.12.1+cu130. glmocr needs transformers ≥ 5 and Pillow ≥ 12, while marker pins Pillow < 11 (glm worktree `pyproject.toml` diff). The GLM local server needs vLLM ≥ 0.19 and transformers ≥ 5.3. vLLM 0.31.0 needs transformers ≥ 5.10.4, < 5.18 and torch 2.13.0. pplx needs transformers ≥ 5.4 with `trust_remote_code` | Never the app env (the spec says so already). Either one pinned "gpu-services" uv project (transformers inside vLLM 0.31's range, which also satisfies pplx ≥ 5.4) with separate processes, or two envs. Pin the model **revision** because custom code changes with it. The app talks to both over local HTTP, as the glm local backend already does | This spec's runtime package; GLM-OCR stage |
| C4 | **One embedding model (owner, Oct 11, memory `oct11-plan-review-bitter-lesson.md`).** Dense coverage and ranking use `embedding.model` (`dense.py:259`, `:275`). R2c's `decision/context` embeddings use the same route (`plan_router_r2_v1.md:104`, `:231-237`). §11's "explicit source-only encoder selection" (spec line 435) is a second production space by another name | Make it an explicit owner decision (D6) with an adoption bar. If adopted, add `source_retrieval.embedding_model` and a source-only space. Never change `embedding.model`, and leave R2c, diagnosis and PF on Qwen. A4 keeps everything within one model if it suffices | Owner; embedding-consumers spec |
| C5 | **The Reader spec owns the consumers.** RW1c (build order 5, after RW4a; `spec_reader_workbench_v1.md:1745-1751`) already designs retrieval as `find_sources(policy="reading", verify=True)` (`:403`). RW3b's shortlist is `search_spans` with RRF (`:697`). RW4e builds the role labeller (`:848-862`), whose roles (definition, theorem, counterexample, prerequisite…) are §4.4's "obligation roles". RW1c's rule is "**Offers, not actions**" (`:397`). An autonomous follow-up search before answering is new behaviour, which costs about +8 s per verify round (`t6-followup.md:549`) | Deliver findings as a **memo to RW1c before it starts** (it follows RW1b and RW4a), not as a parallel research orchestrator. Evidence completion becomes an RW1c option: reference following plus hydration (deterministic) first, then at most one LLM-planned follow-up. Reuse RW4e's role vocabulary. Latency budget per D7 | Reader spec (RW1c/RW3b/RW4a/RW4e) |
| C6 | **Exam and held-out text in encoding context.** The source recipe embeds every block of every current extraction with no exam filter (`recipes.py:99-106`). That is harmless today because encoding is independent and retrieval filters later (`find_sources.py:520-523`). Contextual windows would make teaching vectors depend on exam text. The predicate can change after indexing | Windows split at predicate, solution and assessment-lane boundaries. Exam extractions are excluded from teaching windows (B2). Add a test: marking a unit `held_out_evaluation` invalidates every window that contained it. Confirm with the owner that embedding exam text independently, as today, is acceptable (D12) | Exam-protection owner; this spec's window builder |
| C7 | **Licensing of training artifacts (Phase 4).** The probability vault holds Blitzstein & Hwang (`slice-2-t6.md:466`), which is not openly licensed. The transcripts are third-party YouTube content. Query banks and teacher vectors derived from them are derived works | Phase 4 (if ever) trains only on openly licensed corpora (A9: Axler CC BY-NC, Grinstead & Snell GFDL); artifacts stay local and unpublished. Evaluation on the owner's private sources stays local (the spec says so already, line 160) | Owner (D9) |
| C8 | **Spend machinery.** Per-operation caps are off; the daily guard is $5 per vault (`schema.py:2265-2267`); the harness reserves 16,384 output tokens per call (B11) | Run on copies with an explicit billed-spend driver cap and a raised per-copy guard. Planner and assessor calls use the shared output-budget policy (≥ 16,384), never a smaller custom budget | This spec's run plan |
| C9 | **Decider tier 2** may take on relevance labelling after the agreement report (memory `implementation-queue-oct13.md`) | Log the experiment's strong-model labels and any Decider votes as ledger pairs with a shared input hash. That gives tier 2 free agreement data on `source_relevance`. Do not let the Decider be the label of record | Decider tier-2 stage |
| C10 | **R2c latency.** It shares the 4.5 s OpenRouter query-embedding problem (`plan_router_r2_v1.md:43`). A local 9B for sources would not help R2c | Consider A13 alongside the 9B residency decision | Owner / router R2c |
| C11 | **Evidence-completion records versus existing ledgers.** §4.4's proposed records (spec lines 134-141) duplicate `source_tool_calls` (request and run rows), `judgment_ledger` and `model_call_receipts` | Store completion steps as tool requests and runs plus ledger rows. A research-only packet JSON is fine for the experiment; product integration reuses the existing tables | Sources spec (tools); this spec |

---

## D. Clarifications and owner decisions needed before starting

| # | Question | Recommended default |
|---|---|---|
| D1 | Is local GPU residency for embeddings wanted at all? The owner accepted text leaving the machine and chose one hosted model (Oct 11) | **Hosted-first.** Local only for batch indexing if no hosted v2 endpoint appears and the v2 increment is proven. Watch the Perplexity API for a v2 release |
| D2 | GPU budget, schedule and co-residency with local GLM-OCR and the owner's own GPU use | Batch only: ≤ 4 GPU-hours for the whole first run, owner-chosen hours, never concurrent with local GLM-OCR or interactive desktop use, ≤ 20 GB, and the process exits when done |
| D3 | Which corpus? | Owner vault copies for the real-question slice, plus two openly licensed full books (A9) for scale and the sealed set |
| D4 | Marker snapshots or GLM-OCR re-extraction? | Delivery and recipe arms now on Marker copies. The contextual index and sealed bank after GLM-OCR lands (C1) |
| D5 | Success thresholds | Primary: Complete Evidence@10 on context-dependent strata. Adopt a second embedding space only if it gains **≥ 5 points over the best one-model arm (A4), with a paired 95% CI excluding 0**, **and** a blind answer-quality gain, **and** no latency regression for Reader Ask. Keep the spec's 2-point non-inferiority margin for compression decisions only |
| D6 | Will the owner amend "one embedding model" for a source-only space if D5 is met? | Ask now; it decides whether E1 is worth running |
| D7 | Reader Ask latency budget for evidence completion (today's tutor path is about 15 s p50 total; `t6-followup.md:470`) | ≤ +1 verify round. Reference following and hydration are free; an LLM follow-up only when an obligation is unresolved |
| D8 | Does an autonomous lookup before answering fit RW1c's "offers, not actions"? | Yes, as context (T6's ruling, `spec_reader_workbench_v1.md:412`). Nothing learner-visible changes. Record this in the Reader spec |
| D9 | Licence policy for derived training artifacts | Train only on open licences; artifacts local only |
| D10 | Evaluation judges | Sonnet 5.5 or GPT-6 Luna for labels and answer judging (GPT-6 Luna on the ChatGPT plan has no marginal cost). Haiku only for bulk question drafting, named in reports |
| D11 | How results reach the Reader phases | A one-page decision memo per consumer (RW1c, RW3b, RW4a, RW4d) before RW1c starts. Delivery fixes ship as a small stage or inside RW1c |
| D12 | Is embedding exam material independently (today's behaviour) acceptable? Should contextual windows exclude it? | Yes to the first; windows exclude it (C6) |
| D13 | New provider accounts: a Perplexity API key (contextual v1) and a Voyage key (context-4; not on OpenRouter) | Approve both for the experiment only, at well under $1 of embedding spend |
| D14 | Is dense retrieval enabled in the owner's real use? | Check `learnloop config effective`. If off, enable it and add automatic backfill (A3) before any model comparison |

**Unclear protocol points to settle in the spec:**
- **Primary endpoint versus labels.** Complete Evidence needs audited, accepted evidence sets. With model-only labels it is pool-relative. Say how many cases are audited and by whom: a strong-model adjudicator by default, with owner review optional per the frictionless rule.
- **The completion planner's model and inputs.** Is it the tutor (Codex) or a judge? Does it see the learner snapshot? What latency is acceptable?
- **The rewrite.** `tutor_query_rewrite` is off by default (`schema.py:2172`), so "current production" has no rewrite on the tutor path. Say so in the arm definitions.
- **Window rules for undersized blocks and transcripts** (A7), and for sources over 32k tokens (the Perplexity API limit and the blog's evaluated length).
- **Missing stop rules.** There is no GPU-hour or env-work stop, no label-quality gate, no "direct reading wins" exit and no "cheap context suffices" exit. See §E.

---

## E. Proposed smallest first experiment

**Core question:** on the owner's material, does the tutor need better retrieval at all, and if so, does contextualization beat cheap context?

**E0: no GPU, about 3–5 agent-days, ≤ $25 billed (expected under $10), 0 GPU-hours**

1. **Snapshot and baseline (0.5 day, $0).**
   - Make backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of all three vaults under `fixtures-local/contextual-embeddings/`.
   - Record `learnloop config effective`.
   - Enable `[embedding]` on the copies and backfill source blocks (about $0.002).
   - Record the environment, the GPU state and `max_billed_usd`.
2. **Bank (1 day, about $2–4).**
   - 60–80 development questions, stratified:
     - about 20 Reader-deictic, with a stored selection ("why does this step follow?");
     - about 20 same-source distant-dependency, where the writer is shown a block plus the referenced definition, assumption or theorem and must name both;
     - about 20 intent-stratified across alternative, remediate, compare and worked_example, aligned with `find_sources` intents (A8).
   - Add all 32 logged questions as a separate real slice.
   - Writer: Sonnet 5.5 or GPT-6 Luna. Required-support spans are proposed, then checked by a second strong model reading **full blocks**.
   - Keep transcripts as their own slice.
3. **Delivery arms (1 day; tutor on Codex at no marginal cost, judging about $5).** Use the same questions and the same tutor:
   - D0, today's context (600-character clip; Reader neighbour window as built);
   - D1, full blocks plus nearest-first neighbours plus the reference resolver (A1, A6);
   - D2, `section_view`;
   - D3, the whole source (every source is ≤ about 40k tokens).
   
   Judge blind, in two passes with a strong judge, on correctness, preserved assumptions, citation support and abstention. Record latency.
4. **Retrieval arms (1 day, about $2–5).** Same bank. Labels come from a strong model reading full blocks. Measure Complete Evidence@10, Support Recall@10 and nDCG@10, plus the T6 verify systems.

| Arm | Representation |
|---|---|
| R1 | `pool_verify`, Qwen independent, the existing harness |
| R1′ | The `find_sources` path (RRF) and `dense_plus_bm25` on its first page |
| R2 | Qwen + structural header (A4 i) |
| R3 | Qwen + LLM chunk context, plus contextual BM25 (A4 ii) |
| R4 | `pplx-embed-context-v1-4b` (hosted) vs `pplx-embed-v1-4b` independent (OpenRouter) |
| R5 | Optional: `voyage-context-4` vs `voyage-4-large` |

**Stop rules (fixed before results are seen):**
- **S1, label gate.** If the label passes agree below κ 0.6 on development, fix labelling before any verdict.
- **S2, direct reading wins.** If D2 or D3 is at least as good as the best retrieval-fed arm on answer quality for the Reader-deictic and distant-dependency strata (paired CI includes 0 or favours direct reading), and latency is acceptable:
  - ship A1, A3 and A6, and use direct reading for known-source questions;
  - stop the embedding track until a source exceeds about 150k tokens or a scope exceeds 200k (re-check when the open books land).
- **S3, cheap context suffices.** If R4's contextual-minus-independent gain is under 3 points, or R3 is within 2 points of R4, contextualization adds nothing worth a second space on this corpus. Stop the local track.
- **S4, go to E1** only if a contextual arm beats the best of R1–R3 by ≥ 5 points (paired 95% CI excluding 0) on the context-dependent strata, **and** D1 with that arm's evidence beats D1 with R1's evidence on answer quality.

**E1: conditional, ≤ 4 GPU-hours, ≤ 1 day of env work, about $5**
- Local BF16 `pplx-embed-v2-context-9b-preview` at a pinned revision, in an isolated env, run as a batch job with nothing else resident.
- Index the copies plus two openly licensed books (A9; about 1M tokens; whole-source windows ≤ 32k).
- Rerun the R-arms on the bank, extended to the open books (now including held-out-book questions).
- Stop if the model does not load and pass the spec's smoke checks (spec line 260) within the env budget. Wait for a hosted v2 instead.
- Quantization (FP8 first) only if D2 requires co-residency.

**Deferred, with triggers:**
- Phase 3 drift allocation: trigger is E1 adopted **and** measured VRAM pressure under D2.
- Phase 4 distillation and student banks: trigger is a resident 9B adopted, query latency or residency the measured bottleneck, and openly licensed training corpora in place.
- The 4-way precision matrix (§7.3).
- The late 0.6B pair.
- The LFM and Gemini arms (drop).
- The 2×2 completion factorial. Keep only D1's deterministic completion in E0; add one LLM follow-up round only if D1 leaves many unresolved obligations.
- The 300-question sealed set: replace with the held-out open books.

---

## F. Suggested spec edits (not applied)

- **Header and Decision (lines 3-7).**
  - Update the baseline to `4cf54a295`.
  - Restate the decision as three gated questions:
    1. Do delivery fixes or direct reading suffice?
    2. Does contextualization beat cheap context (A4/A5)?
    3. Only then, does the v2 9B justify local residency?
  - Note that there is no hosted v2.
- **§1.1 (lines 17-25).** Map rows to `find_sources` intents and `compare_sources`. Name the consumers' owners (RW1c, RW3b, RW4a, RW4d, RW4e) and their build order.
- **§1.2 (line 33).** Add the one-embedding-model decision as an explicit constraint and decision point (D6).
- **§2 (lines 39-55).**
  - Remove "not present" (B1).
  - Add rows for `find_sources` (RRF pool; 2,000/900 clips), `PinnedSpanProvider`, `compare_sources`, `instructional/tools.py`, `exam_material.py`, `section_view`/`passage_view`, the Reader neighbour window and its ordering defect, `embedding.enabled` defaulting to off, CLI-only backfill, and the corpus inventory (B7).
- **§3 (lines 59-80).**
  - Add Anthropic Contextual Retrieval (A4) and its 200k-token guidance.
  - Add the hosted Perplexity contextual v1 API and voyage-context-4 (A5).
  - Add B4's verdict on Gemini and images (B8).
  - Add the card facts (B14).
  - Drop LFM.
- **§4.1 (lines 84-90).**
  - Add a minimum unit and transcript or equation merging (A7).
  - Recover section depth from numbering, and use outline or heading units (A10).
  - Add a whole-source ≤ 32k window arm.
  - Windows never cross exam, held-out or solution boundaries (B2).
- **§4.2 (lines 92-115).**
  - Store raw int8-valued vectors and normalize at read (B10).
  - Add the provider and quantization to identity for hosted routes too (A12).
  - Reuse GLM-OCR's local-receipt convention.
- **§4.3 (lines 117-121).** Cite `exam_material.py`, `model_reader_withheld` and `held_out_material`. Add predicate-change invalidation and the serve-time re-check (B2, C6).
- **§4.4 (lines 123-154).**
  - Make step 2's reference following deterministic (A6) and hydration `section_view`-based (A1).
  - Use RW4e roles for obligations.
  - Use the Decider span-support check as the cheap assessor (A11).
  - Store steps as `source_tool_calls` and ledger rows (C11).
  - Frame the whole as an RW1c option (C5).
- **§5.1 (lines 158-176).**
  - Add the real inventory and the openly licensed books (A9).
  - Replace the 300-question sealed set and the 2k/10k/50k banks (B7).
  - Align strata with intents and build the sources spec's per-intent set (A8).
  - Add the transcript slice.
- **§5.2 (lines 178-186).** Strong judges on full blocks, a κ gate, an audited subset with a named adjudicator (B12).
- **§5.3 (lines 188-209).** Add the D5 adoption bar alongside the 2-point compression margin. Add per-clip delivered-evidence accounting.
- **§6 (lines 211-221).**
  - Replace the NVML note with current health and the host-RAM constraint (B6).
  - Name `copy_tree_with_databases`.
  - Run `config effective`.
  - Cap on billed spend and raise the copy guard (B11, C8).
  - Record the Codex tutor as subscription.
- **§7 (lines 223-287).**
  - Split into 7a (hosted contextual screen, A5) and 7b (local, conditional).
  - In 7b: BF16, then FP8, then LLM.int8 (B9); drop the FP32 check; add the GPU tenancy rules (C2) and env pins (C3); fix the snippet.
- **§8 (lines 289-338).**
  - Add arms R1′, R2 and R3 and delivery arms D0–D3 (§E).
  - Drop LFM and Gemini.
  - Move direct reading to first position.
  - Fold §8.2's clip ablation into Phase 0b.
  - Apply the rubric-by-fact rule to the authoring pilot (B13).
- **§9–§10 (lines 340-419).** Move to an appendix, "Deferred, with triggers" (§E), and add the licence rule for training (C7).
- **§11 (lines 421-452).**
  - Add work packages: delivery fixes, reference resolver, automatic source-block backfill, contextual recipe variants, the hosted grouped-document adapter.
  - Mark "Product integration" as contingent on D6.
  - Add the env/GPU tenancy package shared with GLM-OCR.
- **§12 (lines 454-469).**
  - Add decision rows for "direct reading suffices" and "cheap context suffices".
  - Replace the first milestone (line 469) with §E's E0.
