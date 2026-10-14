# Perplexity contextual source embedding experiments

**Status:** proposed experiment protocol, 2026-10-13. Research and code audit complete; deployments, benchmarks and training remain to be run. Code baseline: `3e59d8770`. This spec defines experiments and their implementation seams; it does not change live routes or embedding defaults.

**Decision to make:** whether `perplexity-ai/pplx-embed-v2-context-9b-preview` improves LearnLoop's retrieval of canonical explanations and supporting evidence enough to justify local GPU residency. Start with an 8-bit deployment on the RTX 5090 and establish quality against a BF16 reference. Then measure its incremental value when competing retrievers share an evidence-completion stage. Investigate drift-guided precision allocation and query-only distillation only after establishing that value; a student would retain the strong document index with much lower online memory use.

The most promising use is finding a distant definition, theorem assumption, counterexample or alternative explanation when the learner does not know its location. For a short passage or a known section already available to the tutor, a frontier model receiving that context directly is a strong baseline. Contextual vectors help locate evidence; the tutor still needs the actual source text to reason and cite.

## 1 Intended uses and expected value

This prioritization applies the [embedding brainstorm](../brainstorming/Decision%20and%20embedding%20models.md), [Reader brainstorm](../brainstorming/Improving%20Reader%27s%20design.md), [Embedding Integration Map](../brainstorming/Embedding%20Integration%20Map.md), [Bitter Lesson Research Sweep](../brainstorming/Bitter%20Lesson%20Research%20Sweep.md), [pipeline plan](../brainstorming/Pipeline%20Augmentation%20Plan.md), [embedding consumers spec](spec_embedding_consumers_v1.md), and [Reader workbench spec](spec_reader_workbench_v1.md). Expected value below is a hypothesis to test, not a measured gain.

### 1.1 Product hypotheses

These estimates concern contextual retrieval's incremental value over independently encoded passages. Perplexity's advantage over another contextual model must be measured separately. Evidence completion may provide a larger product gain than the embedding upgrade, particularly when all retrievers already find the answer-bearing passage.

| LearnLoop feature | Expected value from contextual retrieval | Contribution of evidence completion | Strong comparison |
|---|---|---|---|
| First: Reader tutor, “Why does this step follow?”, RW1c | High potential when notation, assumptions or a referenced theorem appear elsewhere | Builds the chain from definitions and assumptions to the disputed step | Selection plus whole section; section plus explicit reference following |
| First: canonical tutor grounding, T6 | High potential when answer and support are dispersed across teaching sources | Checks that the delivered passages jointly support the explanation | Current rewrite, dense plus BM25/provenance and verification, with identical completion tools |
| First: ask your library and compare sources, RW4a/RW4d | High potential when similar vocabulary hides different definitions or conventions | Preserves each source's assumptions and identifies what actually differs | Lexical/structural navigation followed by reading full sections |
| Second: “That didn't help”; alternative explanation, RW1c | Moderate potential for finding a supporting passage or counterexample whose role is implicit | Selects a different instructional role: example, counterexample, geometric view or prerequisite | Existing correction/concept links and the same role-aware judge |
| Second: personalized margin cues, RW3b | Moderate potential for locating passages related to a recorded difficulty | Determines whether the passage addresses that difficulty and whether showing it is timely | Existing gap targets and listwise cue judgment; no new diagnosis by embeddings |
| Second: canonical-source questions and exercises, RW4b and authoring | Moderate potential when locating exercises or dispersed supporting material | Checks source support, explicit assumptions and whether the answer follows | Directly supply the known section; retain correctness/provenance verifiers |
| Low initial value: selected-paragraph explanations and local quick checks, RW1a/RW1b | Low when the relevant section is already known and bounded | Can assemble support directly from that section | Existing passage/section context supplied to the tutor or question writer |

Keep existing authored-practice retrieval (`find_practice` and PF) separate: item/dossier embeddings have little document context to recover. Source-authored exercise discovery is a different task and may benefit when notation is defined earlier. Diagnosis history (T1 and Slice 1) remains a separate experiment over learner traces. Identity, grading, novelty, prerequisite direction and learner-success prediction remain outside this pilot; similarity does not establish those properties.

### 1.2 Retrieval and instructional decisions

For remedial retrieval, embed the already-written gap or misconception statement. Do not expect an embedder to diagnose the learner from a raw reasoning trace. For syntopic reading, encode each source independently and retrieve across sources afterward; concatenating different books into one contextual document would blur attribution.

The earlier Integration Map's proposed learned judge-skipping calibrators were superseded by the embedding-consumer spec's October 11 decisions. Here, **quantization calibration** means selecting numerical precision, and **query distillation** means approximating a retrieval representation. Neither trains a judge substitute or grants embeddings authority over evidence, identity or learning state. The user's October 13 request authorizes investigating these retrieval experiments.

## 2 Current implementation and existing evidence

Use the implementation and recent review as the baseline; the older T6 spec's “current code” paragraph predates T6's implementation.

| Location | Observed behavior | Implication for the experiment |
|---|---|---|
| [EmbeddingClient](../../src/learnloop/ai/embedding.py) and [OpenRouter adapter](../../src/learnloop/ai/providers/openai_embedding.py) | Flat batches, one vector per input; default Qwen3 embedding route | A contextual batch needs explicit document grouping; a model-name change is insufficient |
| [Source recipes](../../src/learnloop/source_retrieval/recipes.py) | Independent block text plus section path, capped at 6,000 characters | Build a separate contextual recipe from complete canonical blocks; hold candidate units fixed for controlled comparisons |
| [Vector store](../../src/learnloop/db/stores/embedding_vectors.py) | FP16 blobs; content-based vector reuse | Contextual identity must include the surrounding window, not just the central block |
| [Dense retrieval](../../src/learnloop/source_retrieval/dense.py) | Mean-centered cosine; coverage by extraction | Use ordinary normalized cosine for the Perplexity reference; test centering separately |
| [Search](../../src/learnloop/source_retrieval/search.py) | Dense candidates widened by BM25/provenance, or RRF; records fallbacks | Preserve these as competing production baselines; do not assume RRF is strongest |
| [Tutor provider](../../src/learnloop/source_retrieval/tutor.py) | Question-dependent retrieval, listwise verification and policy exclusions; `span_context` clips returned text to 600 characters | Measure evidence after final text delivery as well as before reranking; clipping can remove a theorem's conditions |
| [Tutor QA](../../src/learnloop/tutor/tutor_qa.py) | Reader branch bypasses the source-span provider and uses selection plus neighbors | Reader retrieval requires a deliberate integration change, not just a new embedder |
| [Quick checks](../../src/learnloop/reader/reader_quick_check.py) | Section and passage views already supply bounded source context | Keep direct authoring as the baseline when location is known |
| [Evaluation](../../src/learnloop/source_retrieval/evaluation.py), [bench](../../src/learnloop/source_retrieval/bench.py), [suite registration](../../src/learnloop/source_retrieval/suites.py) | Generated and logged questions, two-pass relevance labels, paired metrics, production verification | Reuse budgets, receipts and resume behavior; add evidence sets and independent source splits |

The [T6 follow-up report, corrected rerun in section 5.9](../reviews/t6-followup.md) evaluated 47 probability and 41 arxiv_v2 questions. Its verified dense-plus-BM25 pool scored nDCG@10 of 0.861 and 0.854, versus 0.768 and 0.769 for verified RRF. These are reranked retrieval metrics, not tutor-answer accuracy. The eight logged probability questions did not show a significant tutor-ranking gain and favored RRF on the display ranking. Synthetic and real questions must therefore remain separate report slices.

The same report records remote query embedding at p50 4.5 seconds on its timing sample, and verification around 7–8 seconds. Local embedding could reduce one component; it will not remove verification latency. Re-measure on the current routes rather than projecting that historical timing forward.

The Reader spec references `spec_source_practice_and_probes_v1.md` and a future `find_sources` service. Neither that spec file nor `source_retrieval/find_sources.py` is present in this checkout. Treat them as planned dependencies. The offline experiment can run through existing `search_spans` and `TutorSpanProvider` seams; it must not claim the planned intents are already implemented.

## 3 Research basis

Sources were checked on 2026-10-13. Results describe their own benchmarks and models; each experiment below tests transfer to LearnLoop. The v2 model's release materials are distinct from the v1 technical report.

| Work | Relevant finding and limit | Consequence here |
|---|---|---|
| [Late Chunking](https://arxiv.org/abs/2409.04701), 2024, revised 2025 | Pooling chunks after encoding surrounding text preserves context lost by independent chunk encoding | Compare the same Perplexity model on independent chunks and grouped chunks to isolate contextualization |
| [Context is Gold / ConTEB](https://arxiv.org/abs/2505.24782), 2025 | Evaluates document-context-dependent retrieval and introduces in-sequence negative training | Include ambiguous passages and same-document distractors; use a fixed public ConTEB slice as a secondary benchmark |
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
| [Are LLM-Based Retrievers Worth Their Cost](https://arxiv.org/abs/2604.03676), 2026 | Latency and robustness differ substantially; reasoning augmentation can hurt math/code retrieval | Report per-domain quality, end-to-end latency and rewriting ablations |

Two released alternatives matter before undertaking student training:

- [Voyage 4](https://blog.voyageai.com/2026/01/15/voyage-4/) explicitly supports cross-size query/document compatibility within its family. It motivates the serving architecture, not a claim that its vectors align with Perplexity's.
- [Perplexity v2 late 0.6B](https://huggingface.co/perplexity-ai/pplx-embed-v2-late-0.6b) already supports querying its late 9B sibling's index. It uses 128-dimensional token vectors and MaxSim. This is an optional separate-index comparison, particularly for visual PDFs; it cannot query the contextual model's 2048-dimensional chunk index. Measure its larger index and scoring costs before preferring it to distillation.

## 4 Representation and integration contract

### 4.1 Canonical context windows

Preserve extraction order, mathematical notation, source revision and original span identifiers. Start with one canonical block per candidate; deterministically split oversized blocks at paragraph or sentence boundaries, retaining character offsets. Every comparison using these units gets the same splits. Also retain the unmodified current production recipe as an end-to-end baseline.

Group adjacent candidates from a single source into token-bounded windows. Start at 4,096 tokens including markers, then compare 2,048 and 8,192; try 16,384 only after profiling. Prefer section boundaries. An overlap arm can repeat context around a central region, but emit each candidate once from its assigned window. Do not average embeddings from different windows in the first experiment. Record which required dependencies lie outside the window: local contextualization cannot encode an unseen lemma.

The candidate passage used for citation and the wider context used to encode it are distinct. Store both. Record the complete context dependency list so any changed block invalidates all affected vectors. Never combine independent documents in a single row merely to fill a batch.

### 4.2 Model and vector identity

The [model card](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview) specifies separate query/document encoding methods, 2048 and 1024 trained dimensions, native INT8-valued outputs, and potentially incompatible future preview releases. Freeze 2048 dimensions and normalized cosine initially; dimension reduction and index storage compression are later independent ablations. Weight precision is a separate setting from output-vector quantization.

Use these explicit identities in the experiment manifest:

```text
document_space_id = hash(model_revision, document_weight_precision, quantizer,
                         tokenizer_revision, document_recipe, dimensions,
                         output_transform, scoring_transform)
document_vector_key = hash(document_space_id, extraction_revision,
                           ordered_context_text_and_spans, target_span_offsets)
query_encoder_id = hash(model_or_student_revision, weight_precision,
                        query_recipe, projection, output_transform)
query_vector_key = hash(query_encoder_id, complete_effective_query)
retrieval_run_id = hash(document_space_id, query_encoder_id, corpus_manifest,
                        scope, retrieval_settings)
```

Record tested query/document compatibility explicitly. Distilled queries must not impersonate the teacher's `model_id` to bypass the current shared-model assumption. A new student can reuse a frozen compatible document index; a changed document encoder or contextual recipe requires a new index and renewed compatibility evaluation.

Keep experiment vectors outside the production `embedding_vectors` namespace initially. Store normalized FP32 vectors for exact-search evaluation, and separately test the existing FP16 persistence round trip. If packed INT8 storage is later tested, cast and record it explicitly; an array containing integer-valued floats does not itself occupy one byte per element.

The research adapter should expose `encode_documents(documents: list[list[Chunk]]) -> list[list[Vector]]` and `encode_queries(queries: list[PreparedQuery]) -> list[Vector]`. A document row is one context window, and each result keeps its input chunk ID. Do not flatten this interface into the existing `embed(inputs)` contract until document grouping and cache dependencies have explicit owners. Local calls should record tokens, GPU time and zero provider billing under a local execution type; do not invent a positive token price to bypass the current unknown-model pricing guard.

### 4.3 Scope and evidence rules

Use Reader/library questions first. For a later practice or feedback integration, apply the [existing teaching and item exclusions](../../src/learnloop/source_retrieval/corpus.py) to **encoding context as well as returned passages**. A permitted passage contextualized together with an excluded worked solution has still depended on that solution. A library index must not silently become an assisted-practice index.

Persist context dependencies; reject affected windows for a restricted request or build a policy-appropriate index from permitted text. Item-specific restrictions may require a different context recipe or lexical fallback. Validate this before enabling those consumers. Cold attempts continue to refuse source assistance. Citation allowlists, actual quote checking, exposure accounting and learner-blind grading remain the deciding contracts.

### 4.4 Evidence completion and tutor delivery

Build evidence completion independently of the embedding provider. It consumes initial candidates, identifies missing support for a provisional explanation, and returns a bounded set of canonical passages for the tutor. It can also operate over an already-known section. Context represented inside a vector does not make the corresponding source text available for inspection or citation.

For the passage “Since X and Y are independent, their covariance vanishes,” separate:

- **Required mathematical support:** the covariance identity, expectation factorization under independence, and applicable existence assumptions. Finite second moments are a sufficient condition. An accepted alternative derivation can have a different support set.
- **Learner-specific scaffolding:** an explanation of independence or expectation, an intuitive example, or a counterexample to the converse. Select this from existing learner evidence and the current request; uncertain inferred needs remain hypotheses.

The learner's familiarity can shorten the displayed explanation without deleting its necessary support. Retain required passages in the evidence packet even when the tutor summarizes them briefly. Optional background should not recursively expand into every prerequisite of the subject.

Proposed records, initially in the research package rather than new production tables:

| Record | Required content |
|---|---|
| Completion request | Question, anchor selection, permitted inquiry context, versioned learner-needs snapshot, source scope and policy, encoder identities, token/call/deadline budgets |
| Support obligation | Stable ID, proposed claim or inference, role, required versus optional status, origin, dependencies and acceptable alternative support groups |
| Evidence candidate | Canonical source revision, span IDs/offsets, hydrated text, retrieval query/round, proposed role, provenance and semantic-assessment results |
| Evidence packet | Selected passages, obligation-to-span links, unresolved obligations, citations, tokens, stop reason and complete retrieval/assessment receipts |

Use these steps:

1. **Plan support.** From the question and initial evidence, propose an explanation and its obligations. The plan is revisable: search for applicability limits and contrary evidence as well as confirmation of a candidate answer.
2. **Retrieve missing support.** Follow explicit source references and inspect nearby text first where appropriate. Search remaining obligations with dense, lexical and structural tools under the original scope. Each follow-up query names the needed definition, assumption, theorem or instructional role. Initial and follow-up queries use the same selected query encoder in a deployment arm.
3. **Hydrate and assess.** Load complete bounded passages by canonical IDs before the final context is assembled. Exact quote/provenance checks and semantic judgments are separate fields; a matching quote does not establish entailment or mathematical validity. Preserve source-local definitions and report unresolved contradictions.
4. **Select sufficient evidence.** Minimize tokens and redundancy subject to required support and citation constraints; score optional scaffolding against the recorded learner need. Preserve conjunctions: a covariance definition AND factorization may be required, with an alternative valid derivation as an OR branch. Several similar definitions cannot compensate for a missing theorem. Cosine scores nominate candidates; they do not certify coverage.
5. **Prune and stop.** Remove a passage only if required coverage and selected instructional value survive. This is operational minimality under the chosen plan, not proof of a global optimum. Stop with `sufficient`, `no_progress`, `budget_exhausted` or `insufficient_source_support`. Model-assessed sufficiency remains auditable. Unresolved cases may use a budgeted full-section fallback or an explicitly qualified answer; spending the budget never means success.
6. **Deliver and validate.** Pass the packet to the tutor with its citation allowlist and unresolved gaps. Check final claims against delivered support; material new claims require remaining-budget completion, revision or omission. Account for all retrieval, assessment and repair calls. Reading a passage does not itself update mastery.

For the initial pilot, allow one follow-up round with at most two targeted search calls after the initial retrieval; freeze planner/assessor prompts and paid-call/deadline caps in the run plan. All completion arms receive the same limits. A wider loop is a separate development experiment. Cache source hydration by revision and offsets, reapplying scope policy when serving cached text; key learner-dependent plans/packets by the full request, learner snapshot, policy and prompt versions.

Implement the offline orchestrator over `search_spans` and canonical block hydration. For later product integration, adapt `TutorSpanProvider` to assemble and verify the packet before conversion into tutor context; extend the Reader branch in `tutor_qa.py` explicitly. Replace or parameterize `span_context`'s 600-character clipping only in the controlled hydration arm. Do not assume the planned `find_sources` service exists. The tutor and authoring verifiers retain their existing authority.

## 5 Benchmark and measurement design

### 5.1 Data and splits

Start from backup copies of `probability`, `linear_algebra` and `arxiv_v2`, then inventory independent books/papers and source families. These are candidate domains, not three guaranteed independent samples. Copy SQLite through its backup API so WAL state is included. Keep source text, queries and vectors under gitignored `fixtures-local/contextual-embeddings/`; commit only aggregate reports and protocol code.

Create these separate banks before fitting anything:

| Bank | Initial size and use |
|---|---|
| Smoke | 16 explicit question/passage cases, including equations, ambiguous references, unequal document lengths and empty/oversized inputs |
| Quantization calibration | 128 representative queries and 32 contextual windows from development sources; expand only if sensitivity rankings are unstable |
| Development retrieval | 120 questions, balanced across the task strata below; tune windows, precision, losses and retrieval settings here |
| Sealed evaluation | Initially 300 questions from held-out source families, plus a separately reported real-question slice; increase only through a new prespecified evaluation if precision is insufficient |
| Student training | Later: nested 2k, 10k and 50k query banks, budget permitting, excluding evaluation source families and paraphrase groups |

Sizes are starting compute budgets, not statistical guarantees. If there are too few independent sources, label results exploratory. Reserve whole source families before generation, including alternate editions and overlapping papers. Add leave-subject-out evaluation if enough subjects exist. Indexing held-out documents with the frozen teacher is allowed: student training, precision allocation and hyperparameter selection may not use their queries, labels or context windows.

Cover six strata: direct lookup; context-dependent proof/definition; multi-passage support; cross-source comparison; alternative or remedial explanation; no adequate source support. Tag exact-term and procedural questions as well. Include dependencies beyond one context window and diagram-dependent cases; score the latter separately as extraction/modality limitations. Preserve the Reader selection and permitted inquiry history for deictic questions such as “why does this step work?”

Use logged learner questions where available, without rewriting away their ambiguity. Generate additional questions from source sections with diverse wording and explicit supporting-span proposals. A proposed seed is not automatically a verified relevant passage. Teacher top hits are candidates, not relevance labels.

### 5.2 Evidence labels

For each question record answer-bearing spans, required supporting spans and their roles, acceptable alternative evidence sets, source scope, and whether the permitted corpus can answer it. A definition and a theorem may both be necessary; an equivalent proof elsewhere may be a valid alternative. Distinguish useful background from necessary evidence.

Build a label pool from every arm's candidates, explicit source references, proposed support, and sampled misses. Use two independent LLM labeling passes with blinded system identity and different order, following the existing harness. Audit disagreements and a stratified sample of complete evidence sets against source text. Log whether labels are model-only, adjudicated or owner-reviewed. Two model passes measure agreement, not ground truth. Unjudged hits remain unknown, never automatic negatives. Pool-relative recall must be labeled as such; use the audited sets for complete-evidence claims.

A case record must contain `query_id`, `split`, `source_family`, `query_origin`, `task_tags`, `question`, `selection_span_keys`, `allowed_scope`, `effective_query`, `evidence_sets`, `answerability` and `label_provenance`. Each evidence set lists passage keys/offsets and `answer` or `required_support` roles. Score completeness against any accepted set, not the union of alternative proofs. For support recall, report coverage of the best-covered accepted set under a fixed rule shared by all arms. Questions with no required support have support recall marked N/A; unanswerable questions have evidence recall marked N/A and are evaluated for correct abstention and false source attribution.

Completion cases also record the learner-needs snapshot and provenance, support dependencies, optional scaffolding labels and why each passage is necessary or optional. Pair selected questions with different learner profiles while holding mathematical obligations fixed. Keep all profiles of a question in the same split. Save follow-up queries with parent IDs and obligation roles; audited evaluation labels are never planner inputs.

### 5.3 Required metrics

| Measurement | Definition or purpose |
|---|---|
| Answer Recall at k, nDCG at k, MRR | Rank answer-bearing material; report k = 5, 10, 20 and the deployed candidate limit |
| Support Recall at k | Fraction of required supporting evidence covered; report roles separately |
| Complete Evidence at k | Whether at least one accepted sufficient evidence set is fully covered |
| Teacher support retention | Of required supporting spans in teacher top-k, fraction retained by the candidate; denominator zero is N/A |
| Lost and recovered evidence | Count teacher hits lost and teacher misses recovered, with query-level examples and ranks |
| Delivered evidence coverage | Evidence surviving filtering, reranking, deduplication, clipping and the final context-token budget |
| Evidence completion quality | Audited sufficient-set coverage after the full loop; missing assumptions, unresolved contradictions, unnecessary passages and appropriateness of learner scaffolding |
| Completion efficiency | Follow-up calls and total latency/tokens at matched quality; rounds to sufficient support, budget exits, false sufficiency and full-section fallbacks |
| Tutor answer quality | Correctness, preservation of assumptions, citation support and appropriate abstention, judged without knowing the retrieval arm |
| Drift diagnostics | Mean, p95 and maximum cosine displacement; score/margin changes and teacher top-k overlap |
| Resource use | Process/device VRAM, PyTorch allocated/reserved peaks, host RAM, packed bytes, load/unload time, query p50/p95, indexing throughput |
| End-to-end cost | Embedding, rewrite, verification and generation timings/tokens; actual cache hits; local GPU time and indexing amortization |

Measure retrieval with exact search before introducing ANN approximation. Stable document-ID tie-breaking is required. Report source-macro averages, per-task and per-subject results, and real versus generated queries. Bootstrap paired differences by source family and query family when sample counts support it; ordinary query bootstrap alone can overstate certainty for many paraphrases of one theorem.

Predeclare the primary endpoint as Complete Evidence at 10 on contextual/support tasks, with answer recall and delivered evidence as guardrails. For compression, the proposed non-inferiority margin is 2 absolute percentage points on primary retrieval metrics; report a 95% paired interval. This is an engineering tolerance, not a learned cosine threshold. If the interval crosses the margin, the verdict is inconclusive, not “no quality loss.” A small pilot will often be inconclusive.

That endpoint measures the representation at a fixed retrieval cutoff. The separate product decision in Phase 2 uses audited complete evidence **delivered within the fixed token and call budgets**, with answer quality and appropriate scaffolding as guardrails. Prespecify both decisions; additional searches must not be credited as an embedding-only gain. Retrieval and scaffolding judgments do not establish improved learner comprehension.

## 6 Phase 0 Prepare a reproducible run

1. Record code commit, source manifests, model commit, OS/driver/CUDA, GPU, CPU/RAM and dependency versions. Earlier session inspection returned an NVML driver/library mismatch; check current health before scheduling GPU work. This spec does not presume that issue persists or authorize driver changes.
2. Create an isolated experiment environment. The model requires Transformers at least 5.4.0 and custom code; pin the exact working versions after the smoke test. Do not upgrade the app environment for this trial.
3. Cache only the needed model files, retaining an immutable revision. The published FP32 checkpoint is about 33.6 GB, so plan disk and host-memory loading separately from GPU residency. [Checkpoint files](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/tree/main)
4. Build backup vault copies and the banks in section 5. Record resource and paid-call caps in a run manifest before calls. Reuse existing model-call receipts, output-budget policy and resumable checkpoints. Run the spending plan first; report incomplete work when a cap is reached.
5. Freeze prompt versions and the currently configured frontier tutor/judge model IDs. Compare the same generator and reasoning settings across context arms. Do not substitute an old or cheap generator only for the full-context arm.

Deliverables: `environment.json`, `corpus.json`, `splits.json`, `run_plan.json`, and the smoke cases. No live retrieval switch changes in this phase.

The run plan must specify `stage`, `seed`, `model_revision`, `dependency_lock_hash`, `corpus_manifest_hash`, `split_manifest_hash`, `query_recipe`, `document_recipe`, `precision`, `dimensions`, `window_tokens`, `batch_size`, `candidate_limit`, `evidence_token_budget`, `generator_and_judge_routes`, `max_gpu_hours`, `max_paid_calls`, `max_paid_tokens`, `max_cost_usd` and `output_directory`. Completion runs also fix `completion_policy_version`, planner/assessor prompt versions, `learner_snapshot_hash`, `max_completion_rounds`, `max_followup_search_calls` and `request_deadline_ms`. Set finite compute/spend bounds before execution; a larger run is a new plan. Reserve dataset splits at preparation time, but defer large-scale labeling and target generation until the INT8 smoke test passes. Inspect source licenses before pooling material into reusable student-training artifacts; preserve per-source provenance.

## 7 Phase 1 Try an 8-bit local deployment

### 7.1 Load and validate

The first candidate is bitsandbytes LLM.int8 with higher-precision exceptions. Its documented Transformers integration is a starting point, not evidence that this custom model works unchanged. [Bitsandbytes documentation](https://huggingface.co/docs/transformers/quantization/bitsandbytes)

The following is a **candidate smoke-test recipe**, not a tested serving command. Resolve the revision and dependency pins in Phase 0. Run BF16 and INT8 in separate processes so their memory does not overlap.

```python
import torch
from transformers import AutoModel, BitsAndBytesConfig

model = AutoModel.from_pretrained(
    "perplexity-ai/pplx-embed-v2-context-9b-preview",
    revision=PINNED_REVISION,
    trust_remote_code=True,
    dtype=torch.bfloat16,
    device_map={"": 0},
    quantization_config=BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_skip_modules=["contextual_projection"],
    ),
).eval()

assert model.contextual_projection.weight.dtype == torch.float32
document_vectors = model.encode(
    [["First source chunk", "Its following chunk"]],
    batch_size=1, normalize_embeddings=True,
)
query_vectors = model.encode_queries(
    [["A question about that source"]],
    batch_size=1, normalize_embeddings=True,
)
```

Inspect actual module classes, dtypes and placement. Log which weights were quantized, skipped, or offloaded. The [custom implementation](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/blob/main/modeling_pplx_contextual.py) keeps its projection in FP32 and directly reads that weight in pooling. Preserve that behavior. Do not subsequently move the quantized model with a blanket `.to(...)` or pass `device=` to `encode`. If a hybrid-attention module is unsupported, record the exception and resulting memory; do not silently relabel a largely unquantized model as INT8.

Check finite nonzero outputs, correct chunk counts/order, approximately unit norms, query/document API separation, repeated-call tolerance, and padding/batch invariance. A smoke case must prove that adding source context can change a chunk's representation while its central text stays fixed. Inspect token counts including model markers; no silent truncation.

### 7.2 Profile the working range

1. Measure load, idle and inference memory. CUDA synchronization surrounds timed GPU sections. Keep cold startup, warm execution and cached-query latency separate.
2. Queries: batch one at representative 32, 128 and 512-token lengths, then actual contextualized queries. Warm up and take at least 100 timed calls across inputs. Report the batch-one interactive path before throughput batching.
3. Documents: batch one at 2k, 4k, 8k and optionally 16k tokens. Advance only while headroom remains; an OOM is an outcome. After selecting a safe window, test batch two. Do not use the library's default batch of 32 documents.
4. Profile a BF16 reference on the same inputs. Explicit BF16 matters because the [checkpoint configuration](https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview/blob/main/config.json) specifies FP32. The approximate weight-only conversion is 16.8 GB, or 15.6 GiB; buffers and retained precision add to it. A 262k configured input limit is not a feasible 5090 memory promise.
5. Save BF16 teacher document/query vectors sequentially; unload the reference process before loading the candidate. If the full corpus is too costly, freeze a prespecified subset and label conclusions accordingly.

Proposed shared-GPU targets are at most 16 GiB peak for the selected document workload and at least 12 GiB free at the device level during warm query serving under the recorded desktop baseline. Query p95 below one second is an aspiration to test, not an assumed result or a reason to drop accuracy cases. Also report the remaining memory for the user's actual concurrent workload. Weight quantization does not impose a total-memory cap.

Use a separate worker with one document job at a time, interactive-query priority, and explicit unload/idle release. Queries can wait for a current indexing window; record that contention. Unloading means freeing the model/process, not merely calling `empty_cache`. CPU offload is a separately labeled fallback with its own latency measurements.

### 7.3 Compare numerical deployment choices

Using identical source windows and exact cosine scoring, run:

| Query encoder | Document encoder | Question answered |
|---|---|---|
| BF16 teacher | BF16 teacher | Reference quality |
| INT8 candidate | BF16 teacher | Can online memory shrink while retaining the teacher index? |
| BF16 teacher | INT8 candidate | How much does cheaper indexing alter the document space? |
| INT8 candidate | INT8 candidate | Quality of the straightforward 8-bit deployment |

Cache each side once; the cross-comparisons require no extra encoding. BF16 is an operational reference, not FP32 ground truth. If numerical issues appear, run a small FP32 check where host/device resources permit; do not call BF16 “full precision.”

Exit with a hardware report, quality deltas, failing queries and a reproducible loader. Advance to use-case evaluation if a viable local candidate exists; keep BF16-only as an experimental reference if INT8 fails. Do not infer a quality win from successful loading.

## 8 Phase 2 Determine whether contextual retrieval earns its place

First screen on development queries; evaluate only frozen finalists on the sealed set. This keeps the experiment from becoming a Cartesian product of every window, rewrite, pool and generator setting.

| Arm | Candidate or context construction | Purpose |
|---|---|---|
| Current production | Existing Qwen route, recipe, scoring, pool and verification | Actual replacement baseline |
| Lexical and structure | BM25 plus section headings, exact links and explicit reference following | Cheap source navigation baseline |
| Matched independent Qwen | Same candidate units as Perplexity, ordinary cosine | Separates model differences from recipe/scoring changes |
| Alternative hosted embeddings | Screen Liquid LFM2.5-Embedding-350M, Gemini Embedding 2 and ordinary Voyage on matched passages | Tests whether an available hosted model suffices; pin exact model/provider and query/document recipes |
| Contextual Voyage | Same canonical candidates grouped through Voyage's contextual interface | Separates Perplexity's advantage from contextualization available elsewhere |
| Independent Perplexity | Each candidate encoded as a one-chunk document | Measures the same model without surrounding context |
| Contextual Perplexity | Ordered grouped chunks, chosen precision/window | Measures contextualization's incremental value |
| Contextual plus existing pool | Substitute only the dense list; retain BM25/provenance and the same verification | Measures value in the current retrieval pipeline |
| Direct selected section | Entire known section or selected sections, subject to the explicit context budget | Tests whether retrieval is unnecessary for a local Reader question |
| Direct document | Entire currently open source when it fits | Strong long-context baseline with real scope information |
| Source navigation plus full sections | Same frontier model chooses sections through lexical/outline tools, then reads them | Tests whether tool use and larger evidence spans explain the gain |
| Oracle evidence | Audited sufficient evidence set | Diagnoses generator failure versus evidence-selection failure; not deployable |

Use the [Liquid](https://openrouter.ai/liquid/lfm-2.5-embedding-350m:free), [Gemini](https://openrouter.ai/google/gemini-embedding-2) and [Voyage](https://openrouter.ai/voyageai/voyage-4-large) listings to pin hosted routes at execution. [Voyage Context 4](https://docs.voyageai.com/docs/contextualized-chunk-embeddings) has a separate contextualized-embeddings interface; include its native API where necessary. Check input limits before splitting and never silently truncate. Keep a common-unit comparison within every candidate's limits and label provider-specific context recipes separately. Gemini image retrieval is a separate modality slice, not evidence of a text-only embedding win.

For unknown-source library questions, do not give the direct-document arm the gold book. Use a reproducible source-selection step and charge its cost, or label gold-source selection as oracle. If the permitted corpus exceeds the model's context window, report that arm as infeasible for that scope rather than silently truncating it or counting it as a wrong answer.

Run raw questions first, then the same cached LLM rewrite for the finalists. Include permitted selection/inquiry context consistently. Rewrites must be produced from query-side information, never from gold supporting passages. A hypothesis that rewrite helps must survive math/proof and real-question slices independently.

Keep two explicit context-delivery comparisons:

1. **Controlled retrieval comparison:** identical candidate units, scope, reranker, source-text expansion policy and final 4k/8k-token evidence budgets. Hold the anchor selection first for all Reader arms.
2. **Deployment comparison:** each method gets its intended context policy; direct reading may use 16k/32k/64k when supported. Report quality, prompt-cache behavior, total tokens and latency as a tradeoff curve. Actual uncached and cached costs are both relevant.

### 8.1 Separate embedding gains from evidence completion

After development screening, run the section 4.4 completion protocol as a factorial comparison. Select the affordable baseline on development data and retain contextual Voyage as a distinct comparator where feasible.

| Retriever | One retrieval pass | Retrieval plus evidence completion |
|---|---|---|
| Best affordable baseline | A | B |
| Contextual Perplexity at the selected precision | C | D |

`B - A` measures completion's product contribution; `D - B` measures Perplexity's remaining value once completion exists. Also report `C - A` and `D - C` to show interaction. Use the same source scope, initial hydration policy, generator, citation checks, final evidence-token budget and permitted learner context. Completion arms share planner/assessor prompts and identical search/call budgets; log their actual consumption. Keep direct-section reading as an additional baseline.

Run both full trajectories and a diagnostic subset with identical starting answer passages. The latter asks whether the model finds missing support better when initial answer retrieval is already solved; it cannot establish end-to-end retrieval quality. Attribute failures to initial retrieval, obligation planning, support retrieval, assessment, delivery or generation. Compare latency and search calls at matched evidence/answer quality: completion may erase a final-quality difference while Perplexity still reaches sufficient support faster.

### 8.2 Delivery and adoption

The 600-character tutor span cap deserves its own ablation. Report current behavior and a bounded complete-passage hydration variant. Apply the latter to every competing retriever; preserve canonical offsets and quotation checks. Otherwise a better index may appear useless because its evidence is clipped, or a larger prompt may be credited to the embedding model.

For a subsequent authoring pilot, use a fixed set of concept-to-question tasks and the same question writer and correctness/provenance verifiers. Compare retrieved evidence with a directly supplied known section. Measure whether the question is answerable from its supplied material, whether assumptions and source attribution are preserved, and whether the verifier accepts it. Evaluate discovery of an existing source-authored exercise separately from generation of a new one; a paraphrase must not be labeled source-authored. This pilot uses authoring scope and does not expose answers during a learner's practice attempt.

Advance to custom compression or training if Perplexity retains a credible evidence/answer gain with completion on priority tasks, or non-inferior quality with a useful measured cost/latency tradeoff. If completion supplies most of the gain with an affordable retriever, prioritize shipping that path. If full-section reading wins for known-section queries, retain it for that task. A library retrieval win need not justify replacing local quick checks.

## 9 Phase 3 Investigate quantization by drift

Run this after ordinary INT8 is characterized and Phase 2 supports retaining Perplexity. The trigger is remaining VRAM pressure, identifiable precision failures, or a worthwhile lower-bit target. If ordinary INT8 already meets the quality and resource goals, a small sensitivity study may suffice.

### 9.1 Profile interventions

1. Freeze the BF16 document index and a calibration-query bank. The first drift experiment changes only query weights, matching the intended asymmetric serving path.
2. Enumerate actual modules and tensor sizes. Begin with a small number of layer bands separating feed-forward, full-attention and hybrid/linear-attention projections. Keep normalization, special numerical state and the contextual projection at their working precision. Use layer-level refinement only where a band shows material sensitivity.
3. Quantize one unit at a time at supported 8-bit and 4-bit settings, restoring the same pristine reference between interventions. Record the exact algorithm, grouping, scales, unquantized tensors and packed bytes. Do not treat NF4, INT4 and INT8 as interchangeable precision labels.
4. Re-encode the calibration queries and compute final-vector drift, score perturbations and top-k changes against the frozen document index. Measure after the deployed output transformation. Pre-output activations may aid debugging but are not the principal target.
5. Repeat the sensitivity ranking on at least three resamples spanning domains and query lengths. Record unstable units and outlier queries. A mean alone can hide severe theorem-specific failures.

For normalized teacher query `q0`, candidate `q1` and fixed normalized document `d`, use:

```text
drift(q) = 1 - dot(q0, q1)
score_change(q, d) = dot(q1 - q0, d)
abs(score_change) <= sqrt(2 * drift(q))
positive_negative_margin_change = dot(q1 - q0, d_positive - d_negative)
```

These identities explain why drift is relevant but do not guarantee rank retention when competing scores are close. Log the relevant passage's rank and margin to the competing top-k boundary. The loss of a required lemma matters more than a swap between two interchangeable background passages.

### 9.2 Construct and test precision plans

Compare uniform INT8, uniform supported 4-bit, a simple 4-bit plan with selected units restored to 8-bit/BF16, and a drift-allocated plan under a declared packed-byte budget. Start with a greedy benefit-per-byte proposal or an additive constrained allocator; fully evaluate the resulting plan because unit effects need not add. Include an equal-budget simple baseline, counting skipped tensors and metadata, rather than comparing a larger mixed model to a smaller uniform one without disclosure.

Keep a label-free allocation arm selected only by calibration drift. A second, explicitly supervised arm may select plans using **development** evidence recall and top-k losses. Neither sees sealed evaluation results. This distinguishes reproducing the paper's premise from using LearnLoop's available relevance judgments to optimize a deployment.

Packed deployment is mandatory for a memory claim. Simulated rounding followed by BF16 execution is a quality diagnostic only. A precision assignment with no supported kernels is not a deployable winner. Measure real memory, conversion/load time and query latency; mixed precision may save bytes while slowing execution.

Only after query-side results, optionally profile document-side interventions on the calibration windows. Evaluate document compression with frozen teacher queries, then both compressed sides. Keep this separate from the fixed-teacher-index experiment. A good query precision plan need not be a good long-document plan.

Exit with `sensitivity.jsonl`, deployable precision manifests, resource measurements and the section 5 metrics. Adopt a more complex plan only if it improves the measured quality/resource frontier over ordinary quantization. Stop if kernel work or profiling costs outweigh the available headroom gain.

## 10 Phase 4 Optional query encoder distillation

This stage addresses persistent online residency after the contextual index has demonstrated value. Document indexing remains a scheduled 9B job. Changing a student should not force re-indexing as long as it remains compatible with the frozen document space.

### 10.1 Data and training

1. Freeze the best teacher document space and teacher query pipeline. Prefer BF16-generated teacher targets; if an 8-bit teacher is used, name that changed target explicitly.
2. Begin with a pretrained small text encoder, for example [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), plus a learned projection to 2048 dimensions and normalization. Save the projection as part of the inference artifact. Architecture and tokenizer need not match the teacher; the output space must be learned. A larger student is a capacity ablation, not a prerequisite.
3. Build nested query datasets from training sources, mixing natural logged phrasing, section-grounded synthetic questions, reformulations, proof conditions, comparisons and contextual Reader questions. Plot results at 2k/10k/50k examples rather than assuming a required data volume. Those counts are experimental budgets, not claims of sufficiency.
4. Cache normalized teacher query vectors offline using the exact deployment query preparation. The student sees only information available at query time. Keep teacher/generator access to answer passages out of the student's input. Unload the teacher before training.
5. First train cosine alignment alone. Compare a frozen student backbone with projection-only training against updating the backbone. If using LoRA or another restricted update, label it separately from full fine-tuning.
6. Add score-distribution or relevance supervision only as controlled ablations. Hard negatives come from teacher, lexical and student retrieval over training sources. Adjudicate likely supporting passages before treating them as negatives. Keep held-out sources out of mining.

Include initial questions and evidence-completion queries in these banks. Generate completion traces using only training sources and permitted learner snapshots; retain parent question, obligation role and round. Split whole traces with their source/query families. The student must learn queries for missing assumptions, definitions, counterexamples and prerequisites, including short targeted follow-ups. Cache teacher vectors for these exact prepared queries; do not supply gold evidence or hidden teacher reasoning as extra student input.

Candidate objectives, with weights and temperatures chosen on development data:

```text
alignment = 1 - cosine(student_query, teacher_query)
teacher_scores = teacher_query @ fixed_teacher_documents.T
student_scores = student_query @ fixed_teacher_documents.T
score_distillation = KL(softmax(teacher_scores / temperature),
                        softmax(student_scores / temperature))
loss = alignment_weight * alignment
     + score_weight * score_distillation
     + relevance_weight * multi_positive_retrieval_loss
```

For multiple necessary passages, use a loss that trains each required positive against known negatives or graded relevance targets. A numerator summing all positives can be satisfied by one easy answer passage while ignoring its prerequisite. Known positives must not become in-batch negatives for the same query. Relevance labels can correct teacher mistakes, so retain both teacher agreement and independent retrieval quality in the report.

Start with a floating-point student output. Matching teacher directions does not require rounding student outputs to INT8. Student weight quantization and output compression are later independent experiments.

For the first training sweep, hold the backbone architecture fixed while comparing projection-only training to one economical backbone-update method. Record optimizer, learning rate, effective batch size, sequence limit, gradient accumulation, epoch/step cap and all seeds. Start with a small development-only learning-rate sweep; stop on development retrieval rather than alignment loss alone. Run at least three seeds for the selected recipe before sealed evaluation. Keep training-query budgets and teacher precision fixed when comparing losses. This measures whether a more complex objective helps rather than whether it received more data or tuning.

### 10.2 Evaluation and alternatives

Compare teacher queries, the best quantized teacher queries, projection-only student, alignment-trained student, and additional-loss finalists against the **same** document index. Test new documents from unseen source families without retraining the student. Include unseen-subject and longer contextual-query slices. Use retrieval and delivered-evidence metrics; low training loss and high average cosine agreement are insufficient.

Evaluate initial and follow-up query roles separately. First replay identical held-out queries to isolate encoder changes, then rerun the frozen completion policy with each encoder: changed retrieval can change the next obligation and query. Report final evidence retention, false sufficiency, extra search calls and total latency under identical budgets. Apply the same final-loop checks to drift finalists. Preserved answer recall must not hide a lost prerequisite or a student that needs more retrieval work to recover it.

Cache teacher targets so training needs only the student and minibatch vectors. A 0.6B–1B student's BF16 weights are roughly 1.2–2 GB before activations; training adds gradients and optimizer state. Profile actual memory and gradient accumulation. Do not infer training feasibility from weight size alone. Measure CPU query serving as well as GPU serving if it could release the 5090 entirely.

Before expanding beyond the first training pilot, compare the ready-made Perplexity late 9B-document/0.6B-query family on a small separate index. Keep its MaxSim scoring and token-vector storage explicit. If it meets quality and resource needs without custom training, that may be the better deployment despite different indexing costs.

Adopt a student only if it meets the prespecified retrieval tolerance on held-out material and materially improves online memory or latency. Retain a selectable teacher-query fallback; do not invent a cosine-confidence threshold for deciding when it is needed. If alignment plateaus on unfamiliar subjects, retain the teacher or the existing source-search baseline rather than specializing the whole app to the pilot books.

## 11 Implementation work packages

The following files and commands are proposed, not currently implemented. Keep the first implementation in an isolated research package, then integrate only the winning source-retrieval path.

| Package | Required deliverable | Completion condition |
|---|---|---|
| Environment and snapshots | Pinned loader, backup/export tool, immutable manifests | Re-running uses identical revisions and source snapshots |
| Contextual corpus | Window builder, span/offset maps and dependency hashes | Changing adjacent context invalidates affected vectors; source order and policy boundaries are preserved |
| Local runtime | Query/document methods, serialized indexing, memory/latency recorder, unload | Phase 1 smoke and measured resource report succeed |
| Retrieval evaluation | Adapter to existing compare receipts plus contextual/evidence-set metrics | Exact search, frozen splits, complete label coverage reporting and resume without duplicate paid work |
| Context delivery | Controlled passage hydration and direct-reading baselines | Same frontier generator, audited evidence after clipping and valid citations |
| Evidence completion | Provider-independent obligation planner, scoped follow-up search, packet assembler and receipts | A/B/C/D comparison, bounded stopping, support dependencies, source citations and learner-profile cases |
| Drift profiler | Single-unit interventions and executable precision manifests | Equal-budget comparisons and final combined-plan evaluation |
| Student trainer | Cached targets, projection artifact, alignment/loss ablations | Held-out retrieval into the unchanged teacher index |
| Product integration | Explicit source-only encoder selection and compatibility identity | Existing diagnosis/PF embeddings keep their routes; Reader can use the tested span-provider path |

Suggested future command interface:

```text
python -m research.contextual_embeddings prepare --config RUN_CONFIG
python -m research.contextual_embeddings smoke --config RUN_CONFIG --precision int8
python -m research.contextual_embeddings profile --config RUN_CONFIG
python -m research.contextual_embeddings encode --config RUN_CONFIG --precision bf16
python -m research.contextual_embeddings evaluate --config RUN_CONFIG --split dev
python -m research.contextual_embeddings drift --config RUN_CONFIG
python -m research.contextual_embeddings distill --config RUN_CONFIG
python -m research.contextual_embeddings evaluate --config FROZEN_FINALISTS --split test
```

Each command must expose a planning mode, resource/cost bounds, resumable outputs and the manifest it consumed. The current `learnloop embeddings compare --suite source_retrieval` is a reusable baseline; its model flags currently name OpenRouter models and do not already deploy this contextual model. Avoid presenting a Hugging Face ID as a working CLI integration.

Targeted implementation checks should cover grouped document ordering, wrong query-method rejection, context-sensitive cache invalidation, mixed-space refusal, deterministic overlap assignment, zero/nonfinite vectors, padding invariance, and exact teacher/student scoring. Completion checks must cover joint versus alternative support, learner-specific optional scaffolding, removal of a required passage, contradictions, budget/no-progress exits, stale packet caches and final claims lacking delivered support. Before product use, add policy tests proving excluded content cannot enter contextual windows or delivered evidence, plus Reader citation/exposure and fallback tests. No full model download belongs in ordinary unit tests.

## 12 Reports and decision rules

Each stage writes machine-readable per-query results and a concise aggregate report under `docs/reviews/`. Persist a failure ledger with source/span IDs, old/new ranks, evidence roles and reasons; keep private source text in local artifacts. Record actual skipped cases, errors, OOMs and fallbacks rather than removing them from denominators without a coverage report.

| Decision | Evidence required | Outcome if not supported |
|---|---|---|
| Use local INT8 | Working kernels, useful memory headroom, acceptable retrieval against BF16 | Keep BF16 for offline reference or current remote retrieval |
| Use evidence completion | Better delivered support/answer quality or useful context reduction within declared latency/cost limits | Retain simpler retrieval or full-section delivery for the relevant consumer |
| Use contextual source retrieval | Increment over affordable retrieval with the same completion policy on priority tasks, or useful cost-quality tradeoff versus direct reading | Keep completion with the cheaper retriever, whole-section context or current search |
| Adopt drift allocation | Better measured quality per memory/latency than simple quantization at comparable budgets | Retain ordinary INT8; do not ship a custom allocator merely because drift correlates with damage |
| Adopt query student | Compatible held-out retrieval, delivered evidence retained, material residency/latency improvement | Keep teacher queries or evaluate the released late-interaction pair |
| Enable Reader retrieval | Provider integration, context hydration, citation/quote checks and scope/exposure tests | Leave offline findings as experiments until these are implemented |

Freeze finalists and tolerances before opening sealed results. A failed test is reported as a failure; further tuning needs a fresh held-out evaluation. Retrieval gains do not establish improved learning outcomes. Existing Reader and practice specifications own any later learning-effect evaluation.

The first executable milestone is deliberately bounded: **load INT8, profile a small contextual corpus, compare it with sequentially cached BF16 outputs, and run the existing/current-context baselines on the development questions**. Next, run the bounded evidence-completion comparison before investing in drift allocation or student training. These reports determine which retrieval consumers benefit and whether retaining Perplexity's document space earns the additional compression work.
