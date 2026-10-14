# Independent review: contextual source embedding experiment spec

Reviewed offline on 2026-10-13 in `docs/contextual-embeddings-spec`, HEAD `8fd0208da`, whose parent is code baseline `4cf54a295`. Locations below refer to the owner's original draft at HEAD and the unchanged [Opus review](contextual-embeddings-spec-opus-review.md); fixes are incorporated in the [revised spec](../specs/spec_contextual_source_embeddings_experiments_v1.md).

Only repository source/docs, the tracked fixture TOMLs' embedding-table presence, and read-only hardware commands were inspected. No network, installs, model calls, credential/config-directory reads, vault database reads, other-worktree inspection or commits. No effective-config command was run: its normal loader can read settings/credential files. External research, API, licence, price and model-card claims remain **unverified offline**, even where Opus says it checked them. Its other-worktree and database observations are attributed, not independently reproduced.

## Summary

The core question is worthwhile, but the draft begins with a costly local implementation before establishing whether evidence is missing because of retrieval or delivery. Opus correctly identifies most stale baseline claims and the need for cheap context and direct-reading controls. Its proposed small experiment is the right direction, with several corrections: separate models are not a contextualization ablation; lack of statistical significance is not equivalence; whole-section helpers are bounded and not intrinsically policy-safe; and model-only relevance labels cannot establish complete evidence without explicit set audits.

The owner has now authorized hosted-first E0 with both Perplexity and Voyage keys, including Voyage's independent model through Voyage's own API. The delivery fixes are a separate implementation stage. Local work, a second production embedding space, and later training still have distinct gates. No result in either prior document establishes the proposed second-space adoption bar.

## Findings against the draft and current code

### F1 — Stale service baseline hides the actual consumer

**Location:** draft §2 final paragraph, §4.4 final paragraph, §11; Opus B1/B4/A8.

**Evidence:** [find_sources.py](../../src/learnloop/source_retrieval/find_sources.py) defines the five intents at lines 63–64 and calls RRF at 504–512 explicitly for paging. [policy.py](../../src/learnloop/source_retrieval/policy.py) defines four server-derived learner policies; [compare.py](../../src/learnloop/source_retrieval/compare.py), [service_spend.py](../../src/learnloop/source_retrieval/service_spend.py), [instructional/tools.py](../../src/learnloop/instructional/tools.py) and the [sources spec](../specs/spec_source_practice_and_probes_v1.md) all exist. T6 `pool_verify` is not identical to the service's intent verifier or pagination.

**Fix:** replace the absent/future claims; evaluate the real `find_sources` path and a bounded first-page pool variant, preserving paging behavior. Share the sources spec §17 per-intent bank instead of creating another incompatible bank. Keep the service and matched-representation comparisons separate. The draft also links a missing `Decision and embedding models.md`; the revision links the existing Embedding Integration Map instead.

### F2 — Delivery dominates the motivating Reader case

**Location:** draft §2 tutor rows and late §8.2 clip ablation; Opus A1/B3.

**Evidence:** [span_view.py](../../src/learnloop/reader/span_view.py) lines 29–31/63–65 cap neighbours at 240 characters; lines 113–115 build previous blocks in ascending order. [tutor_qa.py](../../src/learnloop/tutor/tutor_qa.py) lines 1468–1482 concatenates previous then next and breaks at `max(4, len(spans)+2)`. With a quoted single-block selection and three eligible predecessors, the two additions are i−3 and i−2. [tutor.py](../../src/learnloop/source_retrieval/tutor.py) lines 63/105/395 clips retrieved and pinned text to 600. Verification and labels use 900; `find_sources` returns 2,000 and compare uses 2,400.

**Fix:** consume the owner's separate delivery fixes stage as D1 before attributing any answer gain to retrieval. D0 records actual baseline behavior, D1 the fixed implementation, D2/D3 direct section/source. Qualify Opus's “at most two” generalization: without a quote, after filtering, or with other selections, the count can differ. All delivered text and omissions require receipts.

### F3 — Whole-section hydration is neither whole nor policy-safe by itself

**Location:** draft §8 direct arms; Opus A1/A2/E0 step 3.

**Evidence:** [reader_quick_check.py](../../src/learnloop/reader/reader_quick_check.py) lines 75–76 set 60 blocks/24,000 characters. `section_view` (398–424) breaks at those limits; `passage_view` (490–531) has its own cap. These helpers load IR and return text without invoking `model_reader_withheld`. Existing caller guards must not be assumed when reusing helpers elsewhere.

**Fix:** reuse section derivation, apply explicit model policy before prompting, count actual tokens and label any bounded fallback. A full-source control cannot concatenate forbidden solution/held-out regions. Known-section/source controls are fair for Reader selections; gold source choice for unknown-location library questions is an oracle diagnostic and must not decide product adoption.

### F4 — Effective dense coverage is unknown, and backfill is not automatic

**Location:** draft §2/§6/§8 “current production”; Opus A3/B5/D14.

**Evidence:** [schema.py](../../src/learnloop/config/schema.py) lines 2000–2004 default both embedding and backfill off; lines 2172 default tutor rewrite off. No `[embedding]` table appears in the three named tracked TOMLs. [recipes.py](../../src/learnloop/source_retrieval/recipes.py) lines 10–17 excludes sources from default backfill. [embedding_backfill.py](../../src/learnloop/ops/embedding_backfill.py) is explicit bounded work; no ingest source-vector backfill call was found. [search.py](../../src/learnloop/source_retrieval/search.py) records disabled dense and [dense.py](../../src/learnloop/source_retrieval/dense.py) lines 243–251 exposes partial extraction coverage.

**Fix:** later capture a redacted effective-config allowlist and measured coverage. Preserve actual R0 and compare a fully covered Qwen R1. Automatic post-extraction backfill belongs to the delivery stage. Do not assert user-level settings from fixture TOMLs or run effective-config during this restricted review.

### F5 — Context dependencies extend beyond vectors

**Location:** draft §4.1–4.3/§6; Opus C1/C6/F.

**Evidence:** [exam_material.py](../../src/learnloop/content/sources/exam_material.py) defines exam/held-out resolution across revisions, including unresolved-mark fail-closed behavior. [corpus.py](../../src/learnloop/source_retrieval/corpus.py) lines 419–444 additionally withholds effective solution regions and assessment-lane material for model readers. Independent source recipes enumerate current extraction blocks without that policy filter. Contextual headers, full-source summaries and BM25 expansions would also depend on excluded text.

**Fix:** partition before any merging, encoding, context generation or label prompting; never join across a removed forbidden region. Store dependency/policy hashes for windows, generated context, lexical variants, labels and packets. Invalidate all of them on a later held-out mark or re-extraction, and recheck policy at serve time. A source-wide LLM header has source-wide dependencies. Reanchor maps cannot automatically validate old evidence labels. The owner's GLM-OCR handoff controls engine/revision pinning.

### F6 — Two meanings of “held out” create a leakage trap

**Location:** draft §5.1/§10; Opus B7/C6/E1.

**Evidence:** the benchmark proposes indexing held-out books, while the current [exam predicate](../../src/learnloop/content/sources/exam_material.py) treats `held_out_evaluation` as learner-protected material. They are different concepts. Source-family test splits, unlike learner exams, must remain searchable for retrieval evaluation.

**Fix:** name benchmark test families separately. Seal their questions/labels/tuning decisions; permit frozen encoders to index their eligible text. Never use learner-held-out exams for questions, labels, headers, model input or training. Group editions, overlapping sources, paraphrases, profiles and completion traces before splitting. No gold evidence in the effective query or generated context.

### F7 — Corpus size and independence are assumptions, not an available sealed bank

**Location:** draft §5.1 and §10's 2k/10k/50k banks; Opus A2/A7/A9/B7.

**Evidence:** the tracked [B4 report](slice-2-t6.md) §5.2 verifies 26-page Axler and 47-page probability/problem-set samples. Opus's ~20-source/32-question/4,061-caption counts require database access forbidden here; its ~40k-token maximum is a character-based estimate. Two additional books cannot establish hundreds of independent source clusters.

**Fix:** attribute inventory numbers, recount only in a later authorized execution, start at 60–80 development cases with real questions separately reported, and defer the 300-case sealed target/training curves. Confirm on new permitted source families with explicit independence limits. Merge tiny captions/equations on common deterministic units; preserve offsets and compare token-budget coverage so changing units cannot manufacture a top-10 win.

### F8 — Complete Evidence requires set labels and independent auditing

**Location:** draft §5.2–5.3; Opus D protocol points/E S1.

**Evidence:** [evaluation.py](../../src/learnloop/source_retrieval/evaluation.py) has 900-character passage relevance labels; these do not certify a conjunction of theorem conditions or alternative proofs. Two passes of the same rubric can agree on the same omission. Retrieval-pool labels have unknown recall outside the pool.

**Fix:** define AND-required/OR-alternative sufficient evidence sets and full-block inputs. Pool every arm's top-20 plus references, proposals and seeded misses; keep unjudged unknown. Audit every primary accepted set and all disagreements with a named independent strong adjudicator, plus 20% of agreements/negatives/no-support cases. Report κ/confusion and set-level agreement; distinguish adjudicated from model-only and pool-relative outcomes. Source-macro paired intervals and multiplicity/selection controls precede claims. If budget prevents audit, report incomplete evidence rather than silently using weak labels.

### F9 — Research and product interventions are otherwise confounded

**Location:** draft §8; Opus A4/A5/E0 R1–R5.

**Evidence:** production [recipe](../../src/learnloop/source_retrieval/recipes.py) already prepends section titles; [dense.py](../../src/learnloop/source_retrieval/dense.py) centers vectors. R3 changes embedding text and BM25; the hosted sibling models differ in training and potentially providers. Native services also differ in rewrites and verification.

**Fix:** retain production controls but hold units, query preparation, scope and scoring fixed for representation tests. Add grouped-versus-singleton calls to the **same contextual model**; sibling comparisons are deployment baselines. Split R3 embedding-only and contextual-BM25 addition, reuse generated text, and never cite it as canonical evidence. Required hosted E0 includes both Voyage models via Voyage API; provider differences must not be silently attributed to context.

### F10 — Cache identity and nondeterminism need executable rules

**Location:** draft §4.2/§6/§11; Opus A12/B10.

**Evidence:** [embedding_vectors.py](../../src/learnloop/db/stores/embedding_vectors.py) lines 47–70 keys by kind/field/content/model/task (and record for direct lookup), not literally “model_id only.” It has no provider/revision/context-boundary field. [openai_embedding.py](../../src/learnloop/ai/providers/openai_embedding.py) sends a data-collection preference, not pinned provider order. Hosted revision pinning is not established by this repository.

**Fix:** research namespace, full ordered-context/policy/extraction identity, separate query compatibility, raw output and decoded score transforms. Record unknown serving precision/provider honestly; alias epochs, canaries and cached first-success outputs make resume auditable. Test batching/order, nonfinite/zero vectors, truncation and stable ties. Do not equate same dimensions or model-family names with compatible vectors.

### F11 — Billed-only caps can overshoot; subscription calls still cost time

**Location:** draft §6; Opus B11/C8/E0 budget.

**Evidence:** [service_spend.py](../../src/learnloop/source_retrieval/service_spend.py) describes atomic daily reservations shared across processes and receipt reconciliation. [ai/spend.py](../../src/learnloop/ai/spend.py) distinguishes subscription `estimated_only`; a subscription is not infinite latency/quota. [T6 §5.9](t6-followup.md) reports $3.59/$3.06 for the corrected rerun, distinct from Opus A11's earlier $1.18 evaluation figure. Neither is a quote for full-block multi-arm E0.

**Fix:** global $25 ceiling across providers/copies, reconciled bills plus conservative in-flight/unknown reservations before admission, finite retries/timeouts and resumable identities. Keep normal output-budget policy; scale work when reservation bounds do not fit. Separate estimates, bills, credits and subscription usage. No promise of under-$1 embedding spend without token inventory and verified prices. Raise only copy-specific daily guards if the plan requires it.

### F12 — Upstream ownership prevents duplicate implementation

**Location:** draft §4.4/§11; Opus C1/C3/C4/C5/C9/C11/F.

**Evidence:** [Reader spec](../specs/spec_reader_workbench_v1.md) §7.2 already permits retrieval as context, distinguishes background fetching from exposure, and schedules RW1c at order 5. [instructional/tools.py](../../src/learnloop/instructional/tools.py) records request/run rows. [decider_judgments.py](../../src/learnloop/decider_judgments.py) lists `facet_span_support`, not a generic complete-evidence assessor. `uv.lock` pins transformers 4.57.6; no GLM-OCR extractor exists on this baseline. The owner supplies the incoming GLM-OCR/delivery-stage decisions; other worktree code and private queue memories were not inspected.

**Fix:** consume delivery fixes, extraction and receipts through pinned handoffs; isolate experiment dependencies (glmocr ≥5 and pplx ≥5.4 are incoming/reported requirements). Use existing tool/ledger contracts where applicable, not fake tool rows for every research event. Defer LLM completion and validate any new Decider obligation task before trusting sufficiency. Keep second-space adoption separate from experiment authorization and require the owner's explicit amendment.

### F13 — Local feasibility and precision order are not established

**Location:** draft §6/§7; Opus B6/B9/B14/C2/E1.

**Evidence:** this session's `nvidia-smi --query-gpu=...` failed with “couldn't communicate with the NVIDIA driver.” `free -h` reported 30 GiB RAM, 11 GiB available, 19 GiB swap used. This neither reproduces Opus's healthy-driver observation nor proves the draft's old NVML mismatch. The 33.6 GB checkpoint, kernel support, custom API and exact architecture are external claims not testable here.

**Fix:** no current healthy-GPU claim; record the failed probe and recheck on the actual execution host. Hosted E0 uses zero GPU. Conditional E1 starts BF16, then supported FP8 if pressure warrants, with LLM.int8 deferred behind FP8 failure. Bound env work/GPU-hours including failures, prohibit GLM contention, remove local FP32 loading and the untested code snippet. A BF16 weight estimate is not a total-memory budget; custom-code and kernel checks are required.

## Explicit disagreements with Opus

| Location | Disagreement and evidence | Applied correction |
|---|---|---|
| A5 “same model, context vs no context” | Contextual v1 vs its independent sibling, and Voyage context-4 vs 4-large, are different models. The review provides no evidence that only input context changes | Same-contextual-model singleton control; siblings remain useful required deployment baselines |
| E S2 | A CI including zero does **not** show direct reading is at least as good; it may include material harm | Prespecified 2-point answer non-inferiority margin with lower bound above −0.02, or demonstrated superiority. Inconclusive pilots stop expansion without proving equivalence |
| E S3/S4 | A point estimate “within 2” is not equivalence; R4-only gates ignore Voyage, and a development-selected winner is not a confirmed adoption result | Both hosted families considered; uncertainty reported; development selection followed by untouched-family confirmation for production |
| E S2 / D1 | Direct reading winning on known-source cases cannot close unknown-location library retrieval; owner now explicitly requires both hosted arms | Complete hosted E0; constrain the direct-reading decision to its task/scope, then stop unnecessary local expansion |
| A1/A2 | Section helpers are bounded (60 blocks/24k characters), and reference following is not literally free or already implemented | Full permitted-context accounting, measured resolver latency and separate delivery-stage ownership; no duplicate resolver implementation here |
| A6 | The existing environment-lead regex matches words such as “Theorem,” not the number or referenced target; a lookup may be ambiguous across chapters | Consume a resolver with extraction-local numbering, ambiguity/unresolved receipts; avoid “two-line” implementation promises |
| A11 / F §4.4 | `facet_span_support` is not an established joint mathematical-obligation assessor | Reuse infrastructure only after a new task's agreement/false-sufficiency evaluation; strong labels remain authoritative for this experiment |
| B6 | Hosted int8/v1 output cannot serve as an FP32 numerical reference for another v2 model | Drop infeasible local FP32 check; BF16 is an operational reference, hosted siblings are model comparisons |
| B8 / F §3 | B4's image result does not eliminate visual retrieval generally: its own caveat says labels/questions read Marker text | Defer image/Gemini work unless image-grounded labels justify it; no broad “images cannot help” conclusion |
| B10 | Raw bounded integers are exact in FP16, but storing normalized FP32 in an isolated evaluator is not wrong. B10 also quotes “do not invent a local execution type,” which the draft does not say (it says not to invent a positive token price) | Preserve raw vectors and normalized scoring copies; test storage separately; retain truthful local zero billing |
| A12 | Production identity is broader than model ID, though missing provider/revision is real. Listed upstream providers/precisions are unverified web observations | Describe the exact current key and missing dimensions; do not claim provider pinning exists |
| C5/D8 | “Offers, not actions” is not a blanket ban on pre-answer retrieval: Reader explicitly says retrieval is context | No new permission for deterministic context lookup; completion remains a deferred Reader-owned option with latency accounting |
| C6/D12 | “Harmless today” and acceptance of independent exam embedding are broader policy claims than code establishes | Do not change existing policy in this docs task; exclude protected material from all experiment inputs |
| C7/A9 | An assertion that all generated query banks/vectors are legally derived works is not established here; “openly licensed” also does not mean unrestricted | Verify source-specific permitted uses later, keep training gated/private, make no legal conclusion offline |
| D6 | Asking now whether a second production model will be allowed is unnecessary to run the now-authorized isolated comparison | Defer amendment until there is concrete adoption evidence; do not reinterpret go-ahead as production approval |

## Unverified observations and external claims

- All cited paper results, publication dates, model-card dimensions/numerics/licences/architecture, API availability/limits/query pairings/prices/free credits, data-retention terms and public-book licences remain **unverified offline**. In particular, “no hosted v2,” LFM's 512-token/retention issue, Blackwell FP8 kernel support and vLLM defaults are not independently established by this audit. Preserve their research motivation with explicit validation gates.
- Opus's detailed GLM-OCR layout/footnote behavior, GPU-service package versions, route settings from private/local configuration, local-receipt design and private queue/memory instructions cannot be reproduced from this baseline. The owner's explicit GLM-OCR and delivery-stage updates are authoritative planning inputs; implementation details need handoff checks.
- Fixture counts/logged questions and exact token fits were not independently measured. The tracked reports support excerpt-scale evaluation and the historical T6/B4 numbers, not a new database census. Runtime hardware readings are session observations, not a permanent machine state.

## Revision outcome and remaining decisions

The revised spec puts delivery and direct-reading evaluation before representation claims; includes required hosted Perplexity/Voyage with configurable key-variable names; retains research references while marking offline uncertainty; specifies GLM/exam invalidation, audited evidence sets, paired comparisons, budget admission and identity/resume rules; and moves local precision, drift, distillation, late interaction and completion expansion behind triggers.

D1–D14 are retained with owner answers distinguished from defaults and unknown facts. No new owner answer is needed to finish this documentation revision. Before execution, the runner needs a pinned delivery/extraction handoff, redacted effective-config/coverage inventory and validated API contracts. Only if local E1 qualifies is a GPU schedule needed; only if adoption qualifies is the explicit one-model amendment needed. These are not approvals to request again for the already-authorized hosted experiment.
