# Embedding Integration Map

*Written 2026-09-30. Sources: a read-only audit of `src/learnloop/` and `src/learnloop_sidecar/`, plus four literature sweeps (grading/diagnosis, item generation/content structure, learner modeling, embedding-system technique). The research agents opened every cited paper on its arXiv or proceedings page and checked the quoted numbers; anything they could not verify was dropped. Venue status: **[PR]** = peer-reviewed, **[pre]** = preprint. This note specifies the MVP of workstream A in [[Pipeline Augmentation Plan]], and extends [[Embedding index]] and §2 of [[Diagnostic Pipeline Synthesis]].*

---

## The one pattern

Across all four sweeps, the successful systems split the work three ways.

1. **The frontier LLM writes the text that gets embedded.** That text is a hypothesis statement, a solution skeleton, a definition, or a structured method summary — never the raw response or bare stem.
2. **The frozen embedder handles recall.** It blocks candidates, ranks them, and flags disagreement among neighbors.
3. **An LLM, a verifier, or an exact key makes every decision that writes evidence or merges identity.**

Evidence that the LLM should write the embedded text:
- In the Eedi 2024 Kaggle, the efficiency-prize solution used off-the-shelf MiniLM, queried with an LLM-written misconception explanation.
- Generate → retrieve → rerank wins on tutor dialogue (Mitton et al., L@S'26 [PR]).
- KCQRL gets most of its gain from LLM-written solution steps and KC tags.
- EDC canonicalizes a schema by embedding LLM-written definitions (EMNLP'24 [PR]).
- A structured transcription of handwritten solutions beat verbatim LaTeX for embedding (Tauschhuber & Kortemeyer 2026 [pre]).
- FollowIR (NAACL'25 [PR]) shows retrievers don't follow nuanced instructions. So **factorize through text the LLM writes, not through embedding instructions.** Coarse task types (retrieval / similarity / classification) are fine.

Evidence that embeddings are for recall, not decisions:
- On Eedi, a BGE retriever reaches recall@25 ≈ 0.90 but MAP@25 ≈ 0.23. Reranking plus LLM reasoning brings MAP to ≈ 0.50 (Chaudhary et al. 2025 [PR workshop]).
- On rephrased benchmark contamination, embedding similarity F1 ranged 0.18–0.99 and no single threshold avoided both error types. An LLM judge held 0.94–1.0 (Yang et al. 2023 [pre]).
- Entity matching confirms the pattern: block with embeddings, let the LLM decide (Peeters et al., EDBT'25 [PR]).

**This is what bitter-lesson-pilled means at n=1.** The things that scale with compute are:
- the frontier LLM's semantics;
- a general embedder trained on everything;
- a growing pile of **logged LLM adjudications**.

Every "same misconception?", "same problem?" or "grounded?" judgment the LLM makes becomes a labeled pair in embedding space. Those labels are machine-generated, so the plan's n=1 volume ceiling does not apply to them. With tens of labels per class, penalized logistic regression on embeddings matches or beats large-LLM prompting (Buckmann & Hill 2024 [pre]). The Embedder's Dilemma (COLM'26 [PR]) puts the best LLM and best embedder 0.4 points apart on 37 tasks, at up to 1,431× the cost.

So the flywheel runs like this:
- **Today:** the LLM decides every case.
- **As labels accumulate:** a calibrated embedding probe handles the clear cases.
- **Always:** the LLM keeps the ambiguous middle band, and anchor audits catch LLM-label drift.

What migrates to cheap probes over time is judgment, not learner evidence.

---

## Where embeddings are the wrong tool (well-supported negatives)

| Job | Why not | Evidence | Use instead |
|---|---|---|---|
| Mathematical isomorph detection | Equivalent statements with different wording retrieve at R@1 2.8–25%; embedders cluster by terminology | MELD 2026 [pre] | Structural fingerprint + LLM isomorph judge |
| Numeric/parameter variants | 13 embedders average 0.54 accuracy (chance = 0.5) at telling apart texts that differ only in a number | Numeracy Gap 2025 [pre]; GSM-Symbolic ICLR'25 [PR] | Extracted answer, key quantities, sympy normal form, template hash |
| "High cosine ⇒ duplicate" | A small edit can make the original method stop working | MATH-Perturb ICML'25 [PR] | Never auto-reject on cosine alone |
| Difficulty prediction | Best BEA'24 system reached RMSE 0.299 vs 0.311 for a dummy regressor; repeated-CV R² ≈ 0.53 at population scale only | BEA'24 [PR]; Chen & Chen 2026 [pre] | LLM simulated attempts (SMART, EMNLP'25 [PR], r = 0.67 vs SBERT 0.40) plus the learner's own responses |
| Answer equivalence / valid alternative | General embedders handle LaTeX structure poorly | MathNLP'25 [PR] | Symbolic check → LLM judge |
| Grading one representative per cluster | Clusters are score-enriched but not score-equivalent (within-cluster SD ≈ 2.5 points); they group like novices | Tauschhuber & Kortemeyer 2026 [pre] | Neighbors as exemplars and uncertainty signal only |
| Discovering wrong-answer clusters | Clustering recovers correct-answer profiles and under-splits wrong ones | "Anna Karenina", BEA'24 [PR] | Over-split, then LLM-confirmed merges |
| "Same skill" | Cosine similarity is a weak skill proxy; LLM congruity is significantly better | KCluster EDM'25 [PR] | LLM-written operation/KC tags as their own channel |
| Combinatorial queries ("on A and B but not C") | A single vector can only express a limited number of top-k subsets, bounded by its dimension | LIMIT ICLR'26 [PR] | SQL / the concept graph |
| Prerequisite direction | No verified 2024–26 evidence that frozen embeddings predict it | — | LLM + learner evidence (workstream I) |
| Exact identity and replay | Needs determinism | `surface_hash`, `semantic_fingerprint`, `probe_instrument_class`, `repair_equivalence_id`, provenance anchors | Keep exact |

A further hazard: **problem content dominates response embeddings.** On ASSISTments, content-only SBERT predicted grades with AUC 0.626. Subtracting each problem's mean embedding (centering) dropped it to 0.59 (Borchers et al., LAK'26 [PR]). Compare responses **within an item family**, or compare the LLM-written delta/first-divergence text instead of the raw response.

---

## Ranked opportunities, mapped to code

Paths are relative to `src/learnloop/` unless noted. "Hot" means the code runs on every attempt, grade, or ingest.

### Tier 1: diagnosis and grading (hot; strongest evidence; feeds learner state)

**1. Misconception and hypothesis recurrence**

Current behavior:
- `db/repositories.py:2360` (`_projected_causal_candidates`) and `:2488` (`misconception_candidate_by_normalized`) group candidate beliefs by `normalize_text(statement)`.
- `normalize_text` (`diagnosis/misconceptions.py:31`) only lowercases, strips punctuation, and collapses whitespace.
- `diagnosis/causal_factor_deferral.py:267-298` keys `ESCALATION_RECURRENCE_K=3` on the same exact statements.

The problem:
- A paraphrase, or a grader prompt-version bump, starts a new group.
- Recurrence therefore never accumulates, promotion never fires, and deferral falls through to the 30-day TTL.
- This is the "it remembers my mistake" failure from the plan, confirmed in code.

The change:
- Embed each LLM-written hypothesis statement when it is minted.
- **Shadow sensor:** record the nearest prior hypothesis for this learner (filtered by facet), with its cosine and rank.
- Log "would-merge" pairs next to the exact key.
- Score those pairs against later `misconception_match` / adjudication verdicts before any similarity counts toward K.
- Merges stay proposal-only: `error_taxonomy_map.py:164-174` records that content-based diagnosis coercion shipped and was removed twice.
- Evidence: generate-retrieve-rerank (Mitton L@S'26 [PR]); the Eedi winners; Chaudhary 2025.

**2. Widen `_match_misconception`'s candidate set and gate its LLM call**

Current behavior:
- `diagnosis/misconceptions.py:97-138` makes a full LLM call per misconception event, purely to decide same vs new.
- Candidates are limited to the LO, the concept, and `confusable_with` neighbors (`:54-78`), so a recurring belief on another concept is never compared.

The change:
- kNN over the learner's misconception registry widens the candidates and pre-ranks them for the LLM.
- Log embedding/LLM agreement.
- Later, skip the call when a calibrated top-1 margin is unambiguous. That is the first instance of the flywheel above.

**3. Grader history context**

Current behavior:
- `diagnosis/diagnostic_augmentation.py:331-378` (`diagnostic_history_context`) passes prior traces only when facets intersect **and** `surface_family` matches exactly.
- Cross-surface recurrence — the most diagnostic kind — is structurally excluded.

The change:
- kNN over embedded prior traces (first-divergence step plus hypothesis text) on shared facets.
- Log the selected ids (`attempts/coldness_receipt.py:1298` already records `diagnostic_history_attempt_ids`).
- **The retrieval itself must exclude the repair chain's source attempt on a cold verification.** Today exact `surface_family` excludes it by accident; kNN would rank it first and fail the blinding check in `coldness_receipt.py`.
- Add a few **graded exemplars** to the grader prompt, chosen for both proximity and diversity (cluster centers, as SteLLA does). They come from a per-item anchor set (synthetic responses graded when the item is minted), not the learner's past grades (see open question 1).
- Evidence: kNN exemplars lifted GPT-4o grading r from 0.80 (random exemplars) to 0.88 (Zhao et al. 2025 [pre]).
- n=1 caveat: per-item history is thin, so seed with sibling items and public sets (SciEntsBank, Eedi).
- BEA'24 [PR] cautions that exemplars don't rescue a grader that is weak on domain reasoning, so the rubric and reference solution stay the primary anchor.
- This is prompt context, not evidence, so it can go live on retrieval-quality checks alone.

**4. Neighbor disagreement as grade uncertainty**

The mechanism:
- For each new grade, compare it with its neighbors in embedding space within the item family.
- Disagreement combines with the LLM's verbalized confidence.
- The combined signal feeds C's reliability head and the `Uncertainty × ActionSensitivity` escalation rule: regrade, second grader, or a follow-up probe.

Evidence:
- On SciEntsBank, Brier improved 0.172 → 0.138 and MCE 0.155 → 0.100.
- Rejecting the 40% least-confident grades raised accuracy from 0.70 to ≈ 0.90 (Cong et al., AIED'26 [PR]).
- Verbalized confidence is the best single cheap signal: ECE 0.166 vs 0.229 for self-consistency (Ferrer et al. 2026 [pre]).
- "The Correct Answer Trap" (AIED'26 workshop [PR]): flawed reasoning behind correct answers produced about 8 false positives per true detection at realistic prevalence. Suspicion routes to a **probe**, never a verdict.

### Tier 2: item freshness, diversity, contamination (validity-critical for cold measurement)

**5. Three-view freshness gate**

Current behavior:
- `substrate/canonical_projection.py:167-186` (`surface_group_id`) takes the first non-empty *LLM-authored* label: `shared_stimulus_id` / `source_family` / `solution_recipe_family` / `surface_family`.
- Evidence independence, `surface_novelty`, the reveal ledger's same-group check, exam-pool novelty, and `familiarity_discount_from_attempts` all consume it.
- Near-dup checks are exact-string:
  - `diagnosis/probe_instance_generation.py:937-953`
  - `content/authoring/exercise_authoring.py:92,398`
  - `substrate/surface_mint.py:262-282`
- A near-clone with a fresh label certifies as "cold".

The change:
- Embed three views of every administered item:
  - the stem (multimodal when the item has a figure);
  - an **LLM-extracted solution skeleton** — technique sequence and operation graph (structure-aware exemplar retrieval gains up to +6.7 points; Yang et al. 2024 [pre]);
  - the facet definition.
- Pair them with a symbolic fingerprint: normalized answer, key quantities, template hash.
- Close pairs go to an LLM isomorph judge; clearly far pairs skip it.
- **Embeddings may add warmth or a discount; they never grant novelty.** Hard namespaces and `surface_hash` stay exact.
- A ready slot exists: `learner/familiarity.py:92` has `V1_COEFFICIENTS["semantic_similarity"]=0.9` with **no live writer** (`record_soft_features` is never called). `scheduling/kinship_feature.py` is already a shadow firewall.
- A shadow sensor for the LLM-authored `transfer_distance` float (`vault/models.py:648`, used only as `> 0`): log measured embedding distance to the nearest exposed item on the same facet.

**6. Over-generate, then select for novelty**

- Same-model samples collapse: 79% of pairs had cosine > 0.8 at temperature 1.0 (Artificial Hivemind, NeurIPS'25 D&B [PR]).
- Frontier models give 1.8–2.9 functionally distinct outputs out of 10 (NoveltyBench 2025 [pre]).
- Generate N candidates per facet × difficulty × transfer cell. Choose by MMR or Vendi (TMLR'23 [PR]) against the administered history and the other candidates, weighted by verifier quality.
- Coverage axes stay LLM-labeled (QDAIF, ICLR'24 [PR]); embeddings handle within-cell novelty.

**7. Leakage and reveal detectors (lexical today, paraphrase-blind)**

Current detectors:

| Detector | Location | Method | Consequence of a miss |
|---|---|---|---|
| Held-out exam leakage | `content/authoring/practice_leakage.py:82-243` | 6-word shingle / numeric literal | a paraphrased held-out question passes |
| Tutor answer leak | `tutor/tutor_qa.py:685-721` | substring / token recall ≥ 0.8 | its own docstring admits it under-reports paraphrases |
| Reader reveal | `reader/reader_dialogue.py:333-387` | word-bigram overlap ≥ 0.5 | a paraphrased reveal silently contaminates the reserve |

The change:
- Add an embedding shadow flag to each; keep the lexical check as the hard floor.
- A missed reveal corrupts exactly the cold evidence the plan calls scarce, so these flags earn their keep quickly.

### Tier 3: ingest and graph identity (per ingest; errors persist)

**8. Neighbor nomination for append, facet mint, and concept merge**

Current behavior:
- `content/synthesis/append_neighborhood.py:198-270`: Jaccard with hand thresholds (0.5 / 0.25 / 0.4 / 0.12). "SVD" vs "singular value decomposition" is never shown to `append_reconciliation`, so the vault gains a duplicate facet.
- `content/synthesis/synthesis_gates.py:653-692` and `facet_mint_gate.py:277-372`:
  - Jaccard ≥ 0.85, which almost no real paraphrase reaches;
  - `distinct_repair` / `separable` are set differences over normalized free text, so paraphrased repairs always count as distinct and the gate is biased toward MINT over ALIAS.
- `content/synthesis/source_set_synthesis.py:597-631, 2376, 2458+`: concept identity by `snake_case(title)`. The structuring LLM receives registry concepts as **ids only**, which weakens new-vs-registered dedup.

The change:
- Follow EDC (EMNLP'24 [PR]): embed LLM-written definitions and nominate the top-k, unioned with the existing lexical and provenance reasons. The LLM or the owner decides.
- Embedding-merged KC sets still under-merge relative to experts: cosine 0.8 cut 569 → 428 KCs, still worse than the experts' 101 (Wang, Lin, Koedinger 2025 [pre]). So nomination, not auto-merge.
- Respects `spec_knowledge_model.md:588` ("no embeddings for facet identity"): these are hints, not identity.
- Low-risk first adopters: the offline review passes `ops/doctor.py:1855, 2027`, `facet_doctor.py`, and `facet_candidates.py` (MinHash). Add a cosine column next to Jaccard.

**9. Source retrieval for tutor, reader, and quick-add**

Current behavior:
- `tutor/tutor_qa.py:868-990` takes the top 4 LO-linked spans by relation priority, independent of the question.
- Library search is `instr(lower(text), ?)` (`reader/source_search.py`, `db/repositories.py:11872`).
- Quick-add scope is a substring keyword match (`content/pipeline/quick_add.py:155-190`).

The change:
- SQLite FTS5 BM25 plus dense retrieval, fused with reciprocal rank fusion (RRF).
- LLM query rewriting for conceptual queries: on reasoning-heavy retrieval, BM25 over a GPT-4-rewritten query beat every raw dense retriever, and classic cross-encoders *hurt* (BRIGHT, ICLR'25 [PR]).
- LLM listwise rerank only on consequential paths.
- For math- and diagram-heavy PDFs, embed page images alongside the Marker text chunks. ColPali scored 81.3 vs 67.0 nDCG@5 against the best text pipeline (ICLR'25 [PR]). Gemini Embedding 2's single-vector page embeddings are **untested** against this; benchmark before relying on them.
- Grounding stays two-stage: retrieve spans, then verify with an NLI checker or LLM (MiniCheck EMNLP'24 [PR], AlignScore ACL'23 [PR]). Cosine is not a faithfulness score.

### Tier 4: learner model (research, evaluated by replay)

**10. Predicting success on a new item: the "latent understanding" match**

What the evidence says:
- Text helps mostly in inductive, zero-shot, and early-data regimes.
- Frozen embeddings come within about 0.4 AUC of a fine-tuned 3B model out of domain: LRCD KDD'25 [PR] 79.67 vs EduEmbed WWW'26 [PR] 80.06, with overlapping error bars.
- Most of KCQRL's gain comes from LLM-written steps and KC tags (Eedi 75.15 → 78.96 AUC).
- The realistic ceiling is modest. Off-target unseen items reach about 0.58 AUC (Text-LENS, EDM'25 [PR]).
- Frozen embeddings bolted onto a sequence model added nothing: AKT-text 72.23 vs AKT 72.37 (NTKT 2025 [pre]).
- Zero-shot LLM correctness prediction sits at or below the majority baseline: Gemini-flash-lite 66.5 vs base rate 66.5 (EDM'26 [PR]).
- LLM difficulty ratings correlate with human difficulty at ρ ≈ 0.28–0.47 (ACL'26 [PR]).

Design:
- A GP classifier (or Bayesian logistic) over:
  - a fixed low-dimensional projection of the frozen embedding of the stem, LLM solution steps, and operation/KC tags;
  - a tag kernel;
  - a time-decay kernel;
  - the LLM difficulty rating as a weak prior.
- Exact inference is trivial at about 10³ events per year.
- Predictive variance widens off-support, which is the plan's DAEDL requirement with no extra machinery. SNGP (JMLR'23 [PR]) is the large-scale version we don't need.
- **The LLM never outputs the probability.**
- Baseline to beat: a tags + base-rate + forgetting logistic.
- Evaluate on temporal replay of real vault history with log-loss, Brier, and reliability plots. LLM-KT papers mostly report AUC only, and single splits inflate R² by 0.10–0.15.
- **No published evaluation exists of any frozen-embedding predictor for a single learner. We have to measure it ourselves.**

**11. Knowledge-map neighbors (display only)**

- `src/learnloop_sidecar/handlers/knowledge_map.py:670` blends facet-vector cosine (0.6) with concept-graph geodesic distance (0.4). It has no content semantics.
- Add item-text similarity as a third term or as the neighbor source.
- Display-only, so this is a zero-risk first consumer.

---

## System design

**Storage**
- An `embeddings` table keyed on `(record_kind, record_id, field, model_id, task_type, content_hash)`.
- float16 vectors (or int8 plus norm).
- Brute-force numpy search: 10⁴–10⁵ × 768 takes milliseconds, so no ANN index.
- Keep the source text so everything can be rebuilt.
- Embeddings are an index, not learner state. `open-questions.md:103-105` already says replay does not re-embed.

**Model**
- Gemini Embedding 2 (multimodal, 8k-token input, 128–3072 MRL dimensions, task instructions in the prompt) or `gemini-embedding-001` (text only, `task_type` parameter).
- The Gemini Embedding report shows one general model leading MMTEB by more than 5 points (68.32 vs 63.23; 2503.07891 [pre]). **No fine-tuning.**
- 768 dimensions for classify and cluster consumers; the first 25% of dimensions retain nearly everything (ACL Findings'25 [PR]). Test 768 vs 3072 for retrieval on vault data.

**Hygiene**
- Mean-center per vault and task type. This helped 29 of 38 models with no losses; full whitening hurt every model (2511.11041 [pre]).
- Monitor hubness: generic items that end up in everything's neighbor lists (NLDL'24 [PR]).
- Raw cosine is not a probability (WWW'24 Companion [PR]).

**Calibration and the flywheel**
- Log every LLM adjudication (same misconception, same problem, grounded, merge) as a labeled pair.
- Fit a per-`(model_id, task_type, record_kind)` logistic calibrator on centered cosine plus rank and hubness features.
- Set blocking thresholds from conformal recall targets, e.g. at least 95% of LLM-confirmed matches pass (TRAQ, NAACL'24 [PR]). Don't use intuited cosine cutoffs.
- Use three zones: auto-reject below the low threshold; LLM in the middle band; auto-accept above the high threshold, only for reversible actions.
- Refit on every model change.
- `open-questions.md:182` already proposes 0.85 merge / 0.92 dedup "validated against a small labeled set". This is how that set gets built.

**Versioning**
- Every vector carries `model_id`; never mix spaces.
- On upgrade: full re-embed (cents at this scale), refit the calibrators, and compare old vs new through the existing shadow-rebuild pattern.
- Drift adapters (EMNLP'25 [PR]) only pay off around 10⁶ items.

**Privacy**
- Embeddings are close to plaintext: vec2text recovers 92% of 32-token inputs (EMNLP'23 [PR]), and vec2vec translates between spaces without paired data (NeurIPS'25 [PR]).
- Give embeddings the same at-rest, backup, export, and sync policy as raw responses. The cross-vault store must never carry them.
- Sending learner text to Google is a new disclosure. Surface it in config next to the existing providers.

**Memory hygiene**
- Staleness is unsolved by retrieval: every method scored ≤ 28% on multi-hop selective forgetting (MemoryAgentBench, ICLR'26 [PR]).
- So keep validity intervals and `superseded_by` explicit at write time (Zep-style temporal validity).
- Retrieved memory is quoted as data, never instructions. Poisoning under 0.1% of memory reached over 80% attack success (AgentPoison, NeurIPS'24 [PR]).
- Structure-augmented RAG underperformed strong dense retrieval (HippoRAG 2, ICML'25 [PR]); the concept graph already lives in SQL.

---

## Proposed sequence

**Phase 0 — infrastructure plus three offline benchmarks (no product change)**
1. `embed()` in the `ai/` transport, the embeddings table, `model_id` stamping, a privacy config entry.
2. **Eedi misconception retrieval:** Gemini vs MiniLM vs BM25 vs hybrid, with and without an LLM-written hypothesis as the query; recall@25 and MAP@25. This settles the "do we ever need a fine-tune" question with data.
3. **Isomorph and near-duplicate benchmark:** GSM-Symbolic templates as positives, MATH-P-Hard as hard negatives, plus MELD pairs. Compare stem vs solution-skeleton vs fingerprint vs LLM judge, sweeping dimension and threshold per domain.
4. **Recurrence replay on real vault history:** embed past hypothesis statements; hand- or LLM-audit the would-merge pairs; count how often exact-key grouping split a real recurrence.

**Phase 1 — live-safe, context-only consumers**
- kNN in grader history context, plus retrieved exemplars (#3).
- A widened candidate set for `_match_misconception` (#2).
- Hybrid search for the reader, tutor, and quick-add (#9).
- Knowledge-map neighbors (#11).

**Phase 2 — shadow sensors with logged agreement**
- Recurrence would-merge (#1).
- Three-view freshness plus the `semantic_similarity` familiarity writer (#5).
- Leak and reveal flags (#7).
- Append, mint, and merge nomination (#8).
- Neighbor-disagreement grade uncertainty (#4).

**Phase 3 — calibrators and promotion**
- Fit calibrators from the logged adjudications.
- Promote shadow sensors whose agreement and product metrics pass.
- Run the replay evaluation of the learner success head (#10) against the tags + base-rate baseline.

---

## Non-embedding issues found by the audit (verify before acting)

- **`repair_class_id`** (`diagnosis/causal_attribution.py:~643-690`) is a content hash that includes `episode_id` and the model-reported `expected_minutes` / `answer_reveal_budget`. Consequences:
  - Cold verification cannot close a factor across episodes (`causal_factor_deferral.py:197-207` matches it exactly). This may be the intended `episode_repair_equivalence` scope.
  - `causal_probe_coherence.py:527-567` can see "divergent" repair classes that differ only in self-reported minutes, which may spend probes spuriously. The structural `repair_equivalence_id` already exists.
- **Within-attempt error → factor linking** (`causal_attribution.py:1783-1830`) keys on a JSON signature of the normalized statement. Wording drift between two outputs of one grading call breaks the link.
- **Eval `cause_correct`** (`diagnostic_augmentation.py:780-800`) counts a match when one normalized cause is a substring of the other, which gives false positives on short keys. It's also a cheap place to validate embedding thresholds.

## Spec constraints to respect

- `spec_knowledge_model.md:588`: no embeddings for facet identity. Hints and nominations only.
- `spec_causal_attribution_v1.md:877-884`: semantic embeddings stay a separate discovery view, never concatenated with the structured vector.
- `spec_diagnostic_augmentation_v1.md:167`: any taxonomy must survive re-derivation by a second model.
- Plan invariants 1, 2, and 7: never into the blind grader's *role* (retrieved exemplars go to the grader as rubric context, which needs an explicit decision against invariant 1 — see open questions); similarity never creates evidence; replay stays deterministic.

## Open questions

1. **Owner direction (2026-09-30): split grading from diagnosis.**
   - **Grading becomes fully learner-blind.** It sees the item, rubric, reference solution, verifier observations, and the per-item anchor set; it outputs the score, first divergence, repaired trace, and local error type.
   - **A separate diagnosis step becomes history-aware.** It sees retrieved past traces *with their blind grades* (successes as well as errors), prior hypotheses with their status, the state card, and the prerequisite neighborhood. It outputs causes, cross-attempt patterns, prerequisite-gap hypotheses, and repair suggestions.
   - **The router consumes both:** the grade as evidence, the diagnosis as a hypothesis set.
   - **Today one `grading_proposal` call does both jobs**, so this is a contract split. The C4 history moves out of the grader.

   The background below is kept for reference. **Invariant 1 vs retrieval-augmented grading.** The grading call already receives the learner's raw prior traces via C4 (`augment_grading_context`). What it never receives is prior grades or diagnoses, nor, on a cold verification, the repair chain's source attempt (checked in `coldness_receipt.py` ~1250). So the real contract is "no prior verdicts, no repair-chain source", which is narrower than the plan's wording ("retrieved memory never enters the grading role"); the plan's wording should be corrected. There are three kinds of material the grader could be shown:
   - **(A) Raw traces:** keep them, with kNN selection. This does not change the contract, but retrieval must *exclude* repair-chain attempts itself, because kNN would rank the source attempt first.
   - **(B) Per-item graded anchor set:** synthetic responses graded when the item is minted. These are not learner data, so this can be added.
   - **(C) The learner's own past graded answers:** defer. The one plausible later form is adjudicated grades only, with score and rubric rationale but no cause, never from the repair chain, and promoted only via the flip-rate audit.
2. Does embedding an LLM solution skeleton actually recover isomorphs with a different cover story? Phase 0 benchmark 3 answers this; the literature doesn't.
3. Gemini Embedding 2's quality on math-heavy PDF pages, and below 768 dimensions: unverified.
4. Label volume. Do LLM adjudications plus anchor audits reach the tens per class that probes and calibrators need, per vault? Or should calibrators pool across vaults, since calibrators aren't learner data and may cross vaults?
5. Should novelty be measured against everything administered, or only items within the retention window? The literature has no answer.
6. Is about 10³ events per year enough power to show the embedding term in #10 beats tags-only? Pre-register the replay comparison.

---

## Reference list (verified 2026-09-30)

**Grading and diagnosis**
- Zhao et al. 2025 [arXiv:2502.13337](https://arxiv.org/abs/2502.13337) [pre]
- Chamieh et al. [BEA'24](https://aclanthology.org/2024.bea-1.25/) [PR]
- SteLLA [arXiv:2501.09092](https://arxiv.org/abs/2501.09092) [PR IEEE BigData'24]
- Cong et al. [arXiv:2605.00200](https://arxiv.org/abs/2605.00200) [PR AIED'26]
- Ferrer et al. [arXiv:2603.29559](https://arxiv.org/abs/2603.29559) [pre]
- Borchers et al. [arXiv:2512.23941](https://arxiv.org/abs/2512.23941) [PR LAK'26]
- Tauschhuber & Kortemeyer [arXiv:2606.28872](https://arxiv.org/abs/2606.28872) [pre]
- Anna Karenina [arXiv:2406.06599](https://arxiv.org/abs/2406.06599) [PR BEA'24]
- Chaudhary et al. [SciProdLLM'25](https://aclanthology.org/2025.sciprodllm-1.5.pdf) [PR ws]
- Eedi Kaggle recap [blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- Mitton et al. [arXiv:2602.02414](https://arxiv.org/abs/2602.02414) [PR L@S'26]
- Correct Answer Trap [arXiv:2606.23205](https://arxiv.org/abs/2606.23205) [PR ws]
- Baral et al. [EDM'23](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-short-papers.36/index.html) [PR]

**Generation and content**
- Yang et al. [arXiv:2311.04850](https://arxiv.org/abs/2311.04850) [pre]
- GSM-Symbolic [arXiv:2410.05229](https://arxiv.org/abs/2410.05229) [PR ICLR'25]
- MATH-Perturb [arXiv:2502.06453](https://arxiv.org/abs/2502.06453) [PR ICML'25]
- MELD [arXiv:2606.23959](https://arxiv.org/abs/2606.23959) [pre]
- Numeracy Gap [arXiv:2509.05691](https://arxiv.org/abs/2509.05691) [pre]
- Learning by Analogy [arXiv:2411.16454](https://arxiv.org/abs/2411.16454) [pre]
- SSEmb [arXiv:2508.04162](https://arxiv.org/abs/2508.04162) [pre]
- SemDeDup [arXiv:2303.09540](https://arxiv.org/abs/2303.09540) [pre]
- D4 [arXiv:2308.12284](https://arxiv.org/abs/2308.12284) [PR NeurIPS'23 D&B]
- Vendi [arXiv:2210.02410](https://arxiv.org/abs/2210.02410) [PR TMLR'23]
- Artificial Hivemind [arXiv:2510.22954](https://arxiv.org/abs/2510.22954) [PR NeurIPS'25 D&B]
- NoveltyBench [arXiv:2504.05228](https://arxiv.org/abs/2504.05228) [pre]
- QDAIF [arXiv:2310.13032](https://arxiv.org/abs/2310.13032) [PR ICLR'24]
- BEA'24 difficulty task [ACL](https://aclanthology.org/2024.bea-1.39/) [PR]
- SMART [arXiv:2507.05129](https://arxiv.org/abs/2507.05129) [PR EMNLP'25]
- Feng et al. distractors [arXiv:2404.02124](https://arxiv.org/abs/2404.02124) [PR NAACL'24 Findings]
- Moore et al. KCs [arXiv:2405.20526](https://arxiv.org/abs/2405.20526) [PR L@S'24]
- Wang, Lin, Koedinger [arXiv:2511.09935](https://arxiv.org/abs/2511.09935) [pre]
- EDC [arXiv:2404.03868](https://arxiv.org/abs/2404.03868) [PR EMNLP'24]
- MiniCheck [arXiv:2404.10774](https://arxiv.org/abs/2404.10774) [PR EMNLP'24]
- AlignScore [arXiv:2305.16739](https://arxiv.org/abs/2305.16739) [PR ACL'23]

**Learner modeling**
- EduEmbed [arXiv:2604.04088](https://arxiv.org/abs/2604.04088) [PR WWW'26]
- LRCD [arXiv:2501.13943](https://arxiv.org/abs/2501.13943) [PR KDD'25]
- KCQRL [arXiv:2410.01727](https://arxiv.org/abs/2410.01727) [pre]
- NTKT [arXiv:2511.02599](https://arxiv.org/abs/2511.02599) [pre]
- Text-LENS [EDM'25](https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.poster-demo-papers.274/) [PR]
- KCluster [arXiv:2505.06469](https://arxiv.org/abs/2505.06469) [PR EDM'25]
- From Text to Parameters [arXiv:2607.07141](https://arxiv.org/abs/2607.07141) [pre]
- Specialised KT > LLMs [arXiv:2603.02830](https://arxiv.org/abs/2603.02830) [PR EDM'26]
- Student struggles [arXiv:2512.18880](https://arxiv.org/abs/2512.18880) [PR ACL'26]
- Sycophantic simulators [arXiv:2605.12748](https://arxiv.org/abs/2605.12748) [pre]
- MERIT [arXiv:2603.22289](https://arxiv.org/abs/2603.22289) [pre]
- RAG-KT [arXiv:2604.10960](https://arxiv.org/abs/2604.10960) [pre]
- Knowing When to Defer [arXiv:2509.21514](https://arxiv.org/abs/2509.21514) [PR ws]
- UKT [arXiv:2501.05415](https://arxiv.org/abs/2501.05415) [PR AAAI'25]
- SNGP [arXiv:2205.00403](https://arxiv.org/abs/2205.00403) [PR JMLR'23]

**Systems**
- Gemini Embedding [arXiv:2503.07891](https://arxiv.org/abs/2503.07891) [pre]
- NV-Embed [arXiv:2405.17428](https://arxiv.org/abs/2405.17428) [PR ICLR'25]
- FollowIR [arXiv:2403.15246](https://arxiv.org/abs/2403.15246) [PR NAACL'25]
- Embedder's Dilemma [arXiv:2608.12875](https://arxiv.org/abs/2608.12875) [PR COLM'26]
- LR on embeddings [arXiv:2408.03414](https://arxiv.org/abs/2408.03414) [pre]
- BRIGHT [arXiv:2407.12883](https://arxiv.org/abs/2407.12883) [PR ICLR'25]
- LIMIT [arXiv:2508.21038](https://arxiv.org/abs/2508.21038) [PR ICLR'26]
- ColPali [arXiv:2407.01449](https://arxiv.org/abs/2407.01449) [PR ICLR'25]
- Entity matching with LLMs [arXiv:2310.11244](https://arxiv.org/abs/2310.11244) [PR EDBT'25]
- TRAQ [arXiv:2307.04642](https://arxiv.org/abs/2307.04642) [PR NAACL'24]
- Cosine similarity [arXiv:2403.05440](https://arxiv.org/abs/2403.05440) [PR WWW'24 Companion]
- Mean bias [arXiv:2511.11041](https://arxiv.org/abs/2511.11041) [pre]
- Prompt-embedding redundancy [arXiv:2506.01435](https://arxiv.org/abs/2506.01435) [PR ACL Findings'25]
- Hubness [arXiv:2311.18364](https://arxiv.org/abs/2311.18364) [PR NLDL'24]
- vec2text [arXiv:2310.06816](https://arxiv.org/abs/2310.06816) [PR EMNLP'23]
- vec2vec [arXiv:2505.12540](https://arxiv.org/abs/2505.12540) [PR NeurIPS'25]
- Drift-Adapter [arXiv:2509.23471](https://arxiv.org/abs/2509.23471) [PR EMNLP'25]
- LongMemEval [arXiv:2410.10813](https://arxiv.org/abs/2410.10813) [PR ICLR'25]
- HippoRAG 2 [arXiv:2502.14802](https://arxiv.org/abs/2502.14802) [PR ICML'25]
- MemoryAgentBench [arXiv:2507.05257](https://arxiv.org/abs/2507.05257) [PR ICLR'26]
- AgentPoison [arXiv:2407.12784](https://arxiv.org/abs/2407.12784) [PR NeurIPS'24]

---

*Related: [[Pipeline Augmentation Plan]] · [[Embedding index]] · [[Diagnostic Pipeline Synthesis]] · [[EduEmbed]] · [[Agent dialogue on EduEmbed]] · [[Learner Field and Directional Models Augmentation]] · [[Knowledge Tracing]] · [[Datasets]] · [[RAG systems]]*
