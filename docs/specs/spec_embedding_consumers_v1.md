# Embedding consumers across the pipeline — Slice 2 (v1)

**Status:** draft for owner review (2026-09-30; revised 2026-10-11).

**Revision 2026-10-11 (bitter-lesson review; citations in `docs/brainstorming/Bitter Lesson Research Sweep.md`):**
- **New track PF (practice families, §5)** absorbs the former T2 (grading support) and T3 (items) and runs **before Slice 1, as part of Slice A** (owner, 2026-10-11; originally planned in parallel with Slice 1 M2). It covers:
  - the family contract and an idea-level retention key (shadow);
  - generator programs;
  - verified references;
  - verifier filters (closed-book, provenance, figure-only, executed perturbation, solver panel);
  - the freshness gate;
  - a revised grader reference policy.

  The specs so far served "catch my mistakes" and "remember my mistake". PF serves the practice and retention intentions, which had no track before M3.
- **Synthetic per-item anchor sets are no longer built by default** (§5.5). Judges are about twice as wrong on real answers as on synthetic ones. The replacement is a verified reference, a valid-alternative path, and solve-first grading for items without a reference.
- **Order revised (owner, 2026-10-11):** PF-a and PF-b are built in Slice A (`spec_slice_a_practice_and_field_v1.md`), ahead of Slice 1. They take the embedding substrate from Slice A Phase 1. PF-c (§5.5) stays after Slice 1 S1.3, and its rules join Slice 1's blind prompt.
- **No calibrators anywhere (owner, 2026-10-11).** Embeddings shortlist candidates at a recall-oriented blocking cutoff set from a benchmark, and an LLM judge, a verifier, or an exact key decides every candidate above it (R4). Nothing learns a threshold for skipping the judge. `judgment_ledger` stays as evaluation data. `embedding_calibrators`, `learnloop embeddings calibrate`, conformal zones, and score-based auto-accept and auto-reject are not built.
- **T6 moves earlier (owner, 2026-10-11).** It needs only the embedding substrate, so it is built alongside the daily loop, after Slice A, instead of after T4 (§2).
- **Small follow-on edits:** T1's B1 compares OpenRouter embedding models through Slice 1's client (§3.3), and T8's difficulty prior comes from PF's solver panel (§11).
- **Not changed:** T1's recurrence design and T4–T7.
- **Ensemble generation (owner, 2026-10-11, later the same day).** A second generation path, `ensemble`, is added for quantitative and conceptual families (§5.3). Several different models propose candidates; the solver panel verifies them by solving first with an agreement requirement; an LLM judge selects among verified survivors. The judge never establishes correctness. Generator programs stay as the cheap path for procedural drill, and the pilot compares both paths (§5.6).
- **Recorded but not applied:** a thin router (sweep §10), awaiting owner decision.

**T1 runs after** `spec_blind_grading_diagnosis_split_v1.md` (Slice 1) has completed milestone M2 and its exit review; **PF is built in Slice A, before Slice 1** (`spec_slice_a_practice_and_field_v1.md`; §5.7). **T1 is milestone M3**, the third learner-signal checkpoint. It depends on these Slice 1 pieces:
- the `EmbeddingClient` interface with its one Slice 1 implementation: the OpenAI-compatible client pointed at OpenRouter, running `qwen/qwen3-embedding-8b`. It reaches every OpenRouter embedding model, so B1 needs no new client;
- `embedding_vectors`;
- `post_attempt_jobs` embed jobs;
- the diagnosis ledger and `diagnosis_feedback`;
- the would-merge log;
- the `recurrence_key` seam;
- the M1 review exports (the owner's pattern-link verdicts).

**Proceed only if the Slice 1 M1/M2 reports support the direction** (Slice 1 §12.1, §12.3).
- If M1 showed that embedding retrieval adds no confirmed patterns to the diagnoser (Slice 1 history mode stays `full`, `snapshot`, or `exact`), T1 still proceeds on validated citations and the LLM judge, and T4–T5 are deprioritized. T6 is unaffected: it serves source retrieval, not diagnosis, and runs earlier (§2).
- PF proceeds regardless. Its embedding uses (candidate blocking, variant distance) do not depend on the diagnoser's retrieval verdict.

**Source material:**
- `docs/brainstorming/Embedding Integration Map.md`: its codebase audit, verified literature, and "wrong tool" table. Paper citations below are abbreviated; full links are in the Integration Map's reference list.
- `docs/brainstorming/Bitter Lesson Research Sweep.md` (2026-10-11): arXiv IDs cited in §5 (PF).

**Plan mapping:** completes workstream A of `Pipeline Augmentation Plan.md` (trace memory, item freshness, and the verified contrast-set factory, which PF implements) and supplies retrieval and critic inputs that later rows (C, F, J) consume. PF also supplies workstream J's practice items.

---

## 0. Thesis

Slice 1 puts a frozen embedder behind one consumer, the diagnoser's context. The rest of LearnLoop still decides "is this the same thing?" with exact strings, Jaccard over tokens, n-gram shingles, and LLM-authored labels:
- 15 audited sites in the Integration Map;
- verified examples include `normalize_text` grouping, exact-`surface_family` history, exact-prompt dedup, bigram reveal detection, and 0.85-Jaccard facet gates.

These fail on paraphrase, notation variance, and prompt-version drift, and some of the failures silently corrupt cold measurement.

This slice replaces or supplements them with **one pattern**, applied consistently:

1. **The frontier LLM writes the text that gets embedded:**
   - a hypothesis statement;
   - a solution skeleton;
   - a definition;
   - a structured summary of the response.

   Not raw responses or bare labels: embedders cluster by surface wording, and problem content dominates response embeddings.
2. **The frozen embedder does recall:** blocking, shortlisting, ranking, and disagreement signals.
3. **An LLM judge, a verifier, or an exact key decides** anything that writes evidence, merges identity, or blocks an item.

**Every step-3 decision is logged, and nothing is distilled from it** (owner decision, 2026-10-11). An earlier draft had a "flywheel": per-task calibrators fit on the logged verdicts would let clear cases skip the LLM. That is dropped, for three reasons (sweep §2):
- distillation has won only with ~10⁴ labels and a closed label set;
- it underperforms on unseen items;
- LLM price per unit of capability falls 5–10× a year.

Every verdict still goes to `judgment_ledger`, which is evaluation data. It is used to score judges, to benchmark embedding models, and for the model-tier scaling check. Cost is controlled by the blocking cutoff, top-k limits, and spend caps, never by skipping the judge.

---

## 1. Standing rules

Inherited: Slice 1 S1–S7, plan invariants 1–15, and `spec_causal_attribution_v1.md` §2. In addition:

- **R1. Embeddings never create evidence, certify novelty, or decide identity alone.** They may nominate, rank, discount, flag, or supply context. Promotions from shadow to live name the deciding component (LLM judge, verifier, exact key, or owner).
- **R2. Wrong-tool list.** Embeddings are never the sole signal for:
  - mathematical isomorphism (MELD: R@1 2.8–25%);
  - numeric/parameter variants (numeracy ≈ 0.54);
  - difficulty (BEA'24: 0.299 vs 0.311 dummy);
  - answer equivalence;
  - prerequisite direction;
  - combinatorial set queries (LIMIT);
  - exact presentation identity: `surface_hash`, `semantic_fingerprint`, `probe_instrument_class`, `repair_equivalence_id`, provenance anchors.
- **R3. Embed LLM-written or canonical text.** Every `record_kind` declares its text recipe. Response embeddings are compared only within an item family, or via LLM-written deltas.
- **R4. Embeddings shortlist; judges decide** (revised 2026-10-11: no calibrators).
  - **Blocking cutoffs.** A recall-oriented cutoff per `(model_id, record_kind, view)` decides which candidates reach the judge. It is set from a benchmark's recall on confirmed matches (B2 for PF, B3 for T1) and recorded in that benchmark's report.
  - **Who decides.** Every candidate above the cutoff goes to an LLM judge, a verifier, or an exact key. There is no score-based auto-accept or auto-reject, and no learned skip threshold.
  - **Hand-set values.** Cosine cutoffs are never hand-set in code.
  - **Model changes.** Cutoffs are re-derived whenever the model changes.
- **R5. Grading stays learner-blind (Slice 1 S1).** PF's grading support (§5.5) uses item-side material only: verified references and valid-alternative regression traces. The owner's real answers are used to *evaluate* the grader, never as grader input. Neighbor-disagreement uncertainty is computed *after* grading, as a validator-side signal; it is never shown to the grader.
- **R6. Reports, not thresholds, until baselines exist.** As in Slice 1 §13: every shadow → live decision is made on a report with a noise floor.

---

## 2. Tracks

| Track | Consumer | Default authority at landing | Depends on |
|---|---|---|---|
| **PF** | Practice families (§5):<br>• family contract + idea-level retention key (shadow)<br>• generator programs and verified references<br>• verifier filters and freshness gate (**owns benchmark B2**)<br>• selection<br>• grading support (verified reference, valid-alternative path, solve-first) | *Revised 2026-10-11:* live (published verified items, capped per day); retention key live if its replay favours it (successor + kill switch); shadow (familiarity, uncertainty); grading support after Slice 1 | Slice 1 M1 (OpenRouter embedding client) + S1.1 (`embedding_vectors`); grading support after Slice 1 S1.3 |
| **T1 (= M3)** | Recurrence with authority, **including the foundations it needs**: the `same_cause` judge task in `judgment_ledger`, candidate blocking, Eedi + vault-replay benchmarks, recurrence groups, escalated-repair display | live after report | Slice 1 M2 |
| ~~T2~~ | Absorbed into PF (§6) | — | — |
| ~~T3~~ | Absorbed into PF (§6) | — | — |
| **T4** | Contamination: exam leakage, tutor answer leak, reader reveal | shadow flags; lexical floor stays | T1 framework |
| **T5** | Ingest/graph: append, mint, and merge nomination | live as nomination only | T1 framework |
| **T6** | Source retrieval: reader search, tutor spans, quick-add, PDF pages (**owns benchmark B4**) | live (retrieval is context) | substrate only |
| **T7** | Display: knowledge-map neighbors | live (display only) | substrate only |
| **T8** | Research: learner success head on new items | offline replay only | PF skeletons |

**Why the former T0 is split rather than done up front.** T0 bundled foundations for every track: the isomorph benchmark B2 only serves PF (formerly T3), and the PDF-page benchmark B4 only serves T6. Building all of that before any learner-facing result would delay the M3 signal for work that may not be needed.

So T1 carries exactly what recurrence needs. The ledger is task-keyed, so later tracks add a task, not a new mechanism. B2 and B4 move into the tracks that consume them.

**Order** (revised 2026-10-11, owner):
1. **PF** is built in Slice A, before Slice 1.
2. **T6** is built alongside the daily loop, after Slice A.
3. **After Slice 1 M2's exit review:** T1 (M3) → T4 → T5 → T7 → T8.

The reasoning:
- **PF does not wait for M3.** Practice and retention are the intentions Slice 1 and T1 don't serve, and PF's embedding uses don't depend on the M1 retrieval verdict.
- **T6 needs only the substrate.** It is the most learner-visible track, and it overlaps the daily loop: capture filing, "practice this", and tutor answers that cite sources.
- **T4 protects cold measurement cheaply.**
- **T7 can run in parallel with anything.**

*Revised 2026-10-12 (owner):* tracks are **built** without waiting for the previous track's report. Independent tracks (T4, T5, T6, T7) are built in parallel; T1 waits only for Slice 1 M2's code. Reports run once there is data, and they gate live switches, not building (`implementation_goal.md` §1a).

---

## 3. T1 — Recurrence with authority, and the foundations it needs (milestone M3)

**Current code:**
- Recurrence K=3 and promotion key on exact normalized statements, via the `recurrence_key` seam that Slice 1 added. The sites are listed in Slice 1 §7.6: `causal_factor_deferral.py:267-298`, `repositories.py:2346-2363` / `:2488-2518` / `:2541` / `:2674`, `tutor/durable_promotion.py`, `diagnosis/error_hunt.py`.
- Slice 1 logs validated-citation recurrence and would-merge pairs in shadow.
- The M1 review produced the owner's first "same mistake / different" verdicts.

### 3.1 Adjudication ledger (framework; task-keyed)

*Revised 2026-10-11:* the ledger is `judgment_ledger` (RAW_LEDGER). Slice A creates it as the single store for every LLM and owner verdict (§5.8); it was formerly named `embedding_adjudications`. T1 adds the task `same_cause`. Later tracks add `same_problem` | `isomorph` | `duplicate_facet` | `same_concept` | `leak` | `reveal` | `grounded`. The columns are defined in §5.8, and pairwise tasks use both `left_*` and `right_*`.

It is seeded by importing the M1 review's pattern-link verdicts (`judge='owner'`).

**Where `same_cause` labels come from:**
- **Diagnoser links.** A `pattern_claim` or `hypothesis_ref` to an existing hypothesis, *counted only when the citation validated* (Slice 1 §5.4), so the link is grounded in blind grades. This is the cheapest source, and it needs no new LLM call.
- **The same-cause judge.** A separate small LLM operation (`purpose="same_cause_judge"`, routed like `diagnosis`) runs only for embedding-found candidate pairs that were *not* in the diagnoser's context. It is more independent than the diagnoser, at the cost of one call per pair.
- **Owner verdicts** from the M1 export and later reviews.
- **Learner card taps.** "Not the same mistake" on a cited answer (Slice 1 §12.2) is recorded with `judge='learner_card'`.

**Authority when verdicts conflict:** owner > verifier > llm / diagnoser > learner_card. The same rule as `diagnosis_adjudications`, plus bounded trust for in-flow learner taps.

**Backlog.** Run `learnloop embeddings adjudicate --task same_cause --backlog` once, to judge the blocked candidate pairs in the existing hypothesis history. That way recurrence groups cover past mistakes, not only new ones. It runs under Slice A's spend controls, with `--dry-run` first.

### 3.2 Candidate blocking (no calibrator; owner, 2026-10-11)

- **Which pairs reach the judge.** Candidate pairs for the same-cause judge come from kNN over hypothesis embeddings, within the learner's history, facet-filtered as in Slice 1 §9.5. Two limits apply: a top-k per hypothesis, and a recall-oriented blocking cutoff that B3 sets from recall on confirmed matches and records in its report.
- **What the judge decides.** Every pair above the cutoff that the diagnoser's validated citations do not already settle goes to the same-cause judge.
- **Below the cutoff,** only exact `statement_normalized` equality and validated citations can link hypotheses.
- **No score-based decisions.** Nothing is merged or rejected by score. `embedding_calibrators` and `learnloop embeddings calibrate` are not built.
- **Cost** is bounded by the top-k and Slice A's spend caps.

### 3.3 Benchmarks owned by T1

Offline; results land in `docs/reviews/`.

- **B1 Misconception retrieval (Eedi 2024).**
  - Models, all via OpenRouter: `qwen/qwen3-embedding-8b` (the Slice 1 default) and `qwen/qwen3-embedding-4b`, `google/gemini-embedding-2`, `openai/text-embedding-3-large` and `-small`, plus BM25 and hybrid.
  - Query: raw response vs **LLM-written hypothesis** (the Eedi efficiency-prize pattern).
  - Metrics: recall@25, MAP@25.
  - Purpose: chooses the default embedding model on a public set. Slice 1 uses `qwen/qwen3-embedding-8b` alone (revised 2026-10-11), so this is the first multi-model comparison. It also settles whether any fine-tune question ever arises.
  - No new client is needed. A local sentence-transformers client is optional, for offline use. T6 uses Gemini Embedding 2's image input, through OpenRouter or a direct client if PDF pages need one. A model switch fully re-embeds before retrieval moves (Slice 1 §9.6).
- **B3 Vault replay.** Slice 1 E5 data and the imported M1 verdicts, re-scored under the candidate models, plus the blocking cutoff's recall on confirmed matches. This sets the cutoff (§3.2).
- **Harness:** `learnloop embeddings compare --models a,b,c --bench B1,B3`, on the harness PF built for B2. T6 adds B4.

### 3.4 Recurrence groups

`hypothesis_recurrence_groups` (DERIVED, one registered rebuild owner):
- Rebuilt deterministically from three sources:
  - exact `statement_normalized` equality;
  - validated diagnoser citations;
  - `same` verdicts in `judgment_ledger` for task `same_cause` (the highest-authority verdict per pair wins).
- **Replay makes no model call**: every merge is backed by a ledger row.

**No-chaining rule.** Groups are built by incremental union in adjudication order. A union is **refused** if it would place two hypotheses with a recorded `different` verdict (at equal or higher authority) in the same group. The refused pair is logged for review. This prevents A~B, B~C silently merging A with C against a judge's verdict.

**Switch.** `recurrence_key(h)` returns the group id. Singleton groups hash to the old `statement_normalized` key, so vaults with no merges rebuild identically.

**Consumers are unchanged in shape:**
- `_factor_signature` and `sweep_promotion_blocking_factors` count groups.
- Promotion keeps its independence rule: ≥2 distinct `surface_group_id`s or a probe reproduction (`misconceptions.py:302-355`).
- K=3 escalation now fires on reworded recurrences.

**Algorithm version.** Promotion and escalation change meaning, so the new successor is `mvp-0.11`, following `docs/algorithm-change-playbook.md`: an upgrade function, a shadow rebuild of the owner vault reviewed before the switch, and a new head fixture.

### 3.5 Registry agreement (reduced)

Slice 1 already retired `misconception_match`; the diagnoser's `registry_match` is the only registry decision. T1 therefore adds only a **disagreement log**: when the top-1 registry neighbour by embedding differs from the diagnoser's `registry_match`, record an adjudication case for review. There is no gating and no call-skipping.

### 3.6 Same-answer/different-cause guard

The planted pairs from Slice 1 S1.0 are a standing regression suite. **Any false merge blocks the `mvp-0.11` switch.**

### 3.7 Learner-facing deliverable and M3 signals

**Deliverable.** When a recurrence group reaches K=3, the escalated repair is shown with its evidence:
- "Third time with this one — trying a different approach";
- the cited earlier answers, with dates, each openable;
- the repair, which differs from the previous ones: a different operator or representation, per the existing escalation machinery.

A one-tap usefulness rating (**helped / didn't help / not sure**) is recorded in `diagnosis_feedback` with `response` prefixed `escalation:`.

**M3 signals** (report after ~2–4 weeks of use):

| Signal | Suggests reevaluating if |
|---|---|
| Escalation usefulness taps | Escalated repairs are mostly "didn't help" |
| Group precision: audited sample of merged groups + "not the same mistake" taps on cited answers | Merges are often wrong |
| Repeated diagnostic episodes per recurring cause, before vs after `mvp-0.11` | No reduction |
| Next / cold-retry outcomes after escalated repairs (slow; directional only) | Consistently worse than non-escalated repairs |
| Refused-union log volume | High volume means the judges disagree with each other; the judge prompts need work |

**Why:** "it remembers my mistake" — a recurring misconception gets escalated repair instead of a fresh episode each time.

---

## 4. Shared framework notes for later tracks

- Every later track that decides "same / different" registers a `task` in `judgment_ledger`, shortlists with a benchmark-set blocking cutoff, and lets a judge, verifier or exact key decide. None hand-sets a cosine cutoff or learns a skip threshold (R4).
- Benchmarks share one harness, `learnloop embeddings compare`. PF builds it first for B2 (isomorph / near-duplicate, §5.6); T1 adds B1/B3 (§3.3), and T6 adds B4 (multimodal pages, §9).
- A model switch triggers a full re-embed and a rerun of every registered benchmark, which re-derives the blocking cutoffs, before retrieval moves to the new `model_id`.

---

## 5. PF — Practice families (built in Slice A, before Slice 1; absorbs former T2 and T3)

**Why this track exists.** The intentions doc asks for:
- repeated engagement with knowledge rather than repeated presentation of the same question;
- cold recall of a whole solution, first step to last;
- transfer to problems with real structural differences;
- deep "why / what does this do / what if" questions about papers and the owner's own projects.

Slice 1 and T1 serve "catch my mistakes" and "remember my mistake". Practice and retention had no track before M3. PF implements the plan's verified contrast-set factory (Plan §A, Aug 31), under the 2026-10-11 evidence (sweep §3, §5, §6).

**Doctrine.** Generate many, verify, then select. This wins wherever a check that is not an LLM exists: execution, CAS, a solver panel, or a cited source span. Where the only check is an LLM judging depth, novelty, or counterfactual soundness, generating more mostly amplifies the judge's bias:
- the "novelty mirage";
- only about half of "high-order" items being high-order;
- premise drift in what-if answers;
- LLM difficulty labels at ρ = 0.06.

So hand-built effort goes into a small set of **verifier contracts** (§5.4), not into item templates.

**Current code:**
- **Memory state.** FSRS-6 state is kept per `practice_item_id` (`practice_item_state`; `scheduling/review_log.py`), with weights fitted on the learner's own log (`scheduling/fsrs_fitting.py`).
- **Item relation fields.**
  - `surface_family`;
  - `evidence_fingerprint` (`source_family`, `shared_stimulus_id`, `representation`, `solution_recipe_family`, `answer_structure`);
  - `variant_contract` (`easier` | `harder` | `rung_shift`, with preserved/deepened/dropped checkpoints);
  - `contrast_of` / `differing_component`;
  - an LLM-authored `transfer_distance`;
  - `difficulty` + `difficulty_source` (`vault/models.py:377-444, 626-700`).
- **Missing.** No field records which retrieval target an item shares with its siblings. So sibling variants are either independent memory items or are grouped by coarse labels.
- **Duplicate checks.** Near-duplicate checks are exact string: `diagnosis/probe_instance_generation.py:937-953`, `content/authoring/exercise_authoring.py:92,398`, `substrate/surface_mint.py:262-282`. `surface_group_id` takes the first LLM-authored label (`substrate/canonical_projection.py:167-186`).
- **Unwired familiarity input.** `learner/familiarity.py:92` has a `semantic_similarity` coefficient (0.9) with no live writer.

### 5.1 The family contract

A **practice family** is one idea with a fixed retrieval target, plus its variants. It is an activity family with purpose `practice` (P12, decided: one family concept, see "Where families live" below). Its authored content is a new vault model, `ActivityFamily` (vault content, hashed like items):

| Field | Meaning |
|---|---|
| `id` | The `activity_families` id (the idea id) |
| `learning_object_id` | Owning LO |
| `idea_statement` | LLM-written, owner-editable |
| `retrieval_target` | What a cold attempt must produce. Examples: "the full solution from setup to final answer"; "the reason the authors chose X over Y, as stated in §4 and the rebuttal" |
| `source_kind` | `generator` (a generator program, for procedural quantitative drill, §5.3), `ensemble` (several models propose, the solver panel verifies, a judge selects, §5.3), `source_anchored` (paper, textbook, or repo span, §5.3), or `authored` (owner-written). For a new quantitative or conceptual family, an LLM proposes `generator` or `ensemble` at family setup (one-tap override); the pilot (§5.6) sets the default |
| `reference` | The verified reference (§5.3), with `verification` ∈ {`verified`, `unverified`} and the check that verified it |
| `generator` | For `generator` families: program text + hash (§5.3) |
| `provenance` | As for items |

`PracticeItem` gains two optional fields:
- `family_id`;
- `variant_relation`, one of:
  - `same_target`: format or representation changes around the same target. This is a maintenance rep.
  - `isomorph`: same structure, new surface.
  - `near`: a declared change of required operation, reusing `VariantAuthoringContract`'s preserved/deepened/dropped checkpoints.
  - `far`

The generator declares `variant_relation`, and the isomorph judge checks it (§5.4). The measured `variant_distance` is DERIVED: mean-centered cosine of the skeleton view to the family's administered variants. It is stored beside the authored `transfer_distance`.

Items without a family keep today's behaviour. Vaults with no families load and rebuild unchanged (correctness gate, §13).

**Where families live** (P12, decided by the owner 2026-10-11: merge the terms). PF adds no parallel family table and no second identity. It builds on the activity-lineage substrate that is already live for mvp-0.8+ vaults (migrations 065, 075, 077, 078):

| Level | Existing substrate | PF meaning |
|---|---|---|
| Family | `activity_families` (purpose fixed for life; immutable versions) | The idea: one retrieval target. Its authored content is versioned with the family |
| Card | `activity_cards`, with the card lineage that owns scheduling state (075: "a surface never owns FSRS state") | What memory state attaches to |
| Surface | `activity_surfaces` (`surface_hash` and `fingerprint`) | One concrete question |

- **Today** every item resolves to its own family → card → surface (`substrate/activities.py` `resolve_legacy_item`, keyed on purpose and item id). PF groups the cards of existing items under one idea family. RAW_LEDGER rows are never rewritten; regrouping is recorded additively, and undo removes the grouping.
- **Each item keeps its own card** until Phase 3b. Whether family members share memory state is exactly the §5.2 replay question. If 3b goes live, the shared key reuses the card-lineage state machinery where it fits rather than adding a second scheduling authority, behind its kill switch. Published PF-b items are ordinary vault items, so they also get their own cards.
- **Reused instead of rebuilt:**
  - the fingerprint namespaces (077: `shared_stimulus`, `source_example`, `solution_recipe`, `parameter_template`, …) for the exact and structural keys of the freshness gate (§5.4);
  - the familiarity projection for warmth;
  - the durable mint-job pattern (078) for background generation.
- **Practice pools (085) are owner-admitted.** For PF families, auto-accept with undo (§5.2) replaces that admission step.
- **Diagnostic and assessment reuse** of an item keeps its own purpose-specific family, as today. The shared `surface_hash` already blocks manufactured novelty.

The Phase 3 agent confirms three mechanics first and stops for the owner only if the mapping doesn't fit:
1. whether `activity_card_state` or `practice_item_state` is the live scheduling authority for the owner's vaults (`substrate_cutover.purpose_adapters_live`);
2. how to record regrouping additively;
3. where the authored family content is stored: vault content keyed by the family id, or `activity_family_versions.family_spec_json`. The existing rule is that authored content lives in the vault and SQLite holds identity.

**Hash compatibility** (revised 2026-10-11):
- **Scheduling hash unchanged.** `family_id` and `variant_relation` are not in `practice_item_hash`'s field whitelist (`vault/hashes.py`), so scheduling hashes and lineage keep their meaning.
- **Byte-identical serialization.** Items without a family must serialize byte-identically: unset family fields are omitted, never written as null.
- **Expected difference.** Full-item snapshot hashes (`practice_item_snapshots`, keyed by the item JSON) change only for items that gained family fields. That is documented, not a rebuild-equivalence failure.
- **Separate versioning.** Family metadata is versioned on `ActivityFamily`.

**Evidence:**
- Spacing helped practiced items only when practice overlapped the earlier retrieval; distinct sibling questions removed the benefit (PsyArXiv g97u4, 1,050 students).
- Retrieval practice transfers strongly to isomorphs, weakly to near variants, and little to far ones (PsyArXiv sj3w7).

### 5.2 Idea-level retention key (shadow; promoted only on the replay report)

- **Shadow state.** A DERIVED projection, `family_memory_state` (rebuild owner registered), keeps FSRS memory state per `family_id`.
  - It is updated only by **graded cold attempts** on `same_target` and `isomorph` variants.
  - `near` and `far` attempts are logged as **transfer probes**: they update facet evidence as today, but not the family's memory state.
  - Live scheduling keeps per-item state in this track.
- **What never counts as a retrieval:** tutor or reader chat, assisted or primed attempts, and post-reveal attempts. This is the existing reveal-aware cold lane. Scheduled retrieval beat learner-directed AI study at 7 weeks (d = 0.92, 2606.22328).
- **Family backfill.** `learnloop families propose --vault` proposes families for existing items, LO by LO:
  - *Revised 2026-10-11:* within each LO, an LLM judge decides "same retrieval target?" for **every pair** of items. At n=1 that's at most a few hundred pairs per vault.
    - It needs no embedding cutoff, no skeletons, and nothing from B2. Skeletons and B2 arrive with PF-b.
    - LOs with more than `families.max_exhaustive_items` items (default 40) first block candidates with stem embeddings at a recall-oriented top-k. The judge still decides (R1).
  - Every judge verdict appends to `judgment_ledger` (task `same_target`, judge `llm`, §5.8). It is revised 2026-10-11 for frictionless defaults (owner):
    - **Auto-accept.** A family is applied automatically when the judge is confident: two passes with different prompts agree on every pair inside it.
    - **Ambiguous items** simply stay unfamilied. There is no review queue.
    - **Undo.** `family_proposals` (WORKFLOW) keeps the applied decisions so any family can be undone in one step, from the item or LO view or by `learnloop families undo`. An undo appends an owner verdict to the ledger, so the judge's error rate stays measurable without asking for reviews.
  - A rebuild reads applied vault content and never re-judges.
  - The judge runs under Slice A's spend controls: caps, dry-run estimate, resumable.
- **Replay report (the promotion gate).** On the owner's graded log, it reports time-ordered next-event log loss and Brier score, with memory state keyed:
  1. per item (today);
  2. per family;
  3. per LO.

  A variant-distance covariate discounts credit for distant variants. The same FSRS weights are used across all three keys; the run is reported with the current per-user fit and with `FSRS6_DEFAULT_WEIGHTS`.
- **Prediction from g97u4:** per family beats per item; per LO is worse; the distance discount helps.
  - **If confirmed:** an algorithm successor makes `family_memory_state` the live scheduling key for family items, following `docs/algorithm-change-playbook.md`, with kill switch `families.retention_key_live`. *Revised 2026-10-11:* this happens in this track (Slice A Phase 3b), not later. If the replay can't tell, the key stays per item.
  - **If not:** families still drive generation, freshness, and transfer probes.
  - **Either way, families also feed the learner field's `idea_hier` challenger** (`spec_learner_field_v1.md` §4.3). Each family's effect `u_F` is one of that model's few ability dimensions.
- **Not in PF:** population-pretrained memory models. Public srs-benchmark results favour population-trained sequence models over per-user fitting, but no model there uses card content. They stay a plan B/J question (sweep §5).

### 5.3 Generators and verified references

**Generator families (quantitative):**
- **The program.** The LLM writes one **generator program** per family. It maps parameters to (stem, worked reference solution, final answer). Unit tests assert that:
  - the solution's `TraceContract` checkpoint sequence is invariant across parameter draws;
  - the final answer verifies by sympy or exact evaluation.

  Evidence: EFAGen 2504.09763; Computational Blueprints 2511.07932, with 17.8% lower error than expert-authored items.
- **Sandbox** (revised 2026-10-11). Programs run inside the repository's existing Linux bubblewrap boundary, reused or extracted from generated-animation rendering (`content/authoring/concept_animation.py`, `_sandboxed_command`):
  - every namespace unshared, so no network;
  - read-only system and venv mounts;
  - the scratch directory as the only writable path;
  - an environment with no vault paths or API keys;
  - CPU, memory, and wall-clock limits;
  - `--die-with-parent`, so the whole process tree is killed.

  **Generation fails closed wherever bubblewrap is unavailable**, including macOS and Windows. Unlike animation rendering's consent-gated fallback, generators run unattended. `python -I` alone is not a sandbox. Acceptance tests show network denied, vault reads denied, and writes outside scratch denied.
- **Storage and publication** (revised 2026-10-11, owner: change what is served).
  - Candidates and their filter results live in `pf_candidates` (WORKFLOW).
  - Items whose reference is **verified** and that pass §5.4's filters **publish into their family as ordinary items** and enter the queue.
  - Publishing is capped at `pf.max_published_per_day` (default 10) until the daily-loop new-material policy (Q11) exists.
  - Items whose reference is unverified are **never published**.
  - Published items are stored instances, so **replay never executes a generator**. Solution skeletons are persisted in `item_skeletons` (WORKFLOW) and never regenerated on rebuild.
- **Variant sources:**
  - `same_target` variants change format or representation around the fixed target;
  - `isomorph` variants are parameter draws;
  - `near` and `far` variants are separate generator programs that declare which checkpoints they preserve, deepen, or drop.

  Solver-panel isomorphs only cover the "same capability, different surface" slot (2602.05114). The "different required operation" slot needs its own program.

**Ensemble families (direct generation; added 2026-10-11, owner).** This path is for topics that don't parameterize naturally:
- word problems and probability setups where the *story* changes but the structure stays;
- counterexamples, proof-shaped items, and conceptual twists.

These are often better isomorphs than number swaps, because a new surface tests transfer.

The pipeline:
1. **Propose.** At least two *different* models each propose candidates (route `pf_proposers`, a list of models). Different models matter, because samples from one model collapse toward the same question (Artificial Hivemind, §5.4).
   - **Inputs:** the parent item, the family's retrieval target, and the declared `variant_relation`.
   - **Each candidate carries:**
     - a stem;
     - the proposer's worked solution and final answer;
     - the declared relation;
     - one line on what changes (surface, story, representation) and what is preserved (the solution's checkpoint sequence).
2. **Verify by agreement, solve first.** The solver panel (§5.4) solves each candidate *without seeing the proposer's answer*.
   - The reference becomes `verified` only when **at least two independent panel solves agree** with the proposer's final answer.
   - Where the answer is numeric or symbolic, an LLM-written equivalence check (sympy) must also confirm the agreement. The check runs in the same bubblewrap sandbox as generator programs.
   - Disagreement leaves the candidate `unverified`, so it is never published.
   - The same panel run sets the candidate's difficulty (§5.4), so verification needs no extra panel.
3. **Structure check (mandatory for ensemble isomorphs).** With no program to guarantee invariance, the isomorph judge compares the candidate's solution skeleton with the parent's. A declared `isomorph` whose checkpoint sequence differs is relabelled `near`, or rejected. The freshness gate applies as usual.
4. **Select.** Among verified survivors of every filter, an LLM judge (route `pf_selection_judge`) picks the best for quality and diversity. It ranks the list as a whole, with the MMR/Vendi diversity scores as input. Every verdict is written to `judgment_ledger` (task `selection`).
   - **The judge only chooses among verified candidates; it never establishes correctness.** Best-of-N judges favour impressive-looking problems over well-posed ones, and they miss errors in a candidate's own answer key. A false key degrades grading (fMAE 0.065 → 0.249, 2603.14732).
   - The scheduler still decides when anything is served.

**Known bias.** The pool leans toward problems the panel can solve. That is acceptable for isomorphs of existing items, whose parent difficulty is known. The pilot reports the panel-disagreement rate per family, so a family where the panel can't agree shows up instead of silently producing nothing.

**When to use which.**
- **Generator programs** suit procedural drill: eigenvalues, derivatives, formula computation. Once written, every draw is free, CAS-checked and invariant by construction, which is what spaced maintenance reps want.
- **Ensemble** suits everything that doesn't parameterize naturally.
- The pilot (§5.6) decides whether ensemble becomes the default everywhere, with programs kept for drill.

**Source-anchored families (papers, textbooks, repos):**
- **Answer first.** The generator writes the answer with a cited span, then derives the question (Code-QA-Bench 2605.29277).
- **Provenance.**
  - Every "why did the authors… / why was this designed…" answer must cite a span: paper text, an OpenReview rebuttal, a commit, an issue, a code comment, or an ADR (RPC-Bench 2601.14289; IsComment 2506.14649).
  - Uncited rationale is labelled `inferred` and shown as "plausible interpretation". It is never the answer key. Most generated design rationale is plausible but unstated (2504.20781).
- **Novelty items.** The key is the paper's own contribution statements. An LLM judge never grades or selects for novelty (2606.12071; 2606.08251).
- **What-if items.**
  - Where the consequence is executable (math, code, a short training run, a shape check), run the perturbation and store the observed result as the key.
  - Otherwise, grade the causal chain step by step against the source. The best frontier model scores 64.6% on open what-if questions (2608.27953).
- **"Method does not apply" items** store the counterexample as part of the reference, because LLM graders are sycophantic too (BrokenMath 2510.04721).

**Verified reference (every family).**
- **How a reference becomes `verified`.** An independent check must agree with it:
  - CAS or exact evaluation (quantitative);
  - for `ensemble` candidates, at least two independent solve-first panel solves agreeing with the proposer's answer, plus the equivalence check where the answer is numeric or symbolic (above);
  - execution (code);
  - an independent high-effort, solve-first derivation by a strong model that matches the reference (proofs, explanations);
  - for source-anchored items, a quote-verified span that contains the answer.
- **Unverified references.** A reference that fails stays `unverified`, and its candidates are **not published** (revised 2026-10-11; previously they served as practice-only items graded solve-first). They stay in `pf_candidates` for regeneration or a later verification pass. A false reference actively degrades grading: fMAE 0.065 → 0.249 (2603.14732).
- **Cost.** Frontier compute is spent here, once per family, not on every grade. The reference explains most grading reliability; rubric criteria explain almost none (2608.17938).

### 5.4 Verifier filters, freshness, and selection

For each family cell (`variant_relation` × difficulty band), over-generate N candidates, then filter:

| Filter | Applies to | Effect | Evidence |
|---|---|---|---|
| Execution / CAS | generator families | Reject if the answer fails to verify, or if an `isomorph` changes the checkpoint sequence | EFAGen |
| Solve-first agreement | ensemble candidates | Reject unless at least two independent panel solves agree with the proposer's answer, plus the equivalence check where applicable (§5.3). Declared isomorphs also need the structure check | 2603.14732 (false keys degrade grading) |
| Closed-book | source-anchored items whose target is source-specific (not "teach me the concept") | Reject if a model without the source answers correctly against the verified reference: the item tests generic knowledge | Code-QA-Bench |
| Figure-only | "explain this figure" items | Reject if answerable from the figure alone | 2604.23733 |
| Provenance | why-items | Relabel `inferred` when no verified span is cited (not rejected) | IsComment; RPC-Bench |
| Freshness / isomorph | all | See below | former T3 |
| Solver panel | generator, ensemble and isomorph variants (for ensemble candidates the same solves are the verification) | 2–3 models at different tiers each solve the candidate several times. The solve rate sets a per-variant difficulty offset (`difficulty_source = "solver_panel"`, a new enum value); outliers are rejected. Variants are not assumed equally difficult | 2602.05114; 2601.09953 |

**Difficulty never comes from LLM self-labels.** They correlated at ρ = 0.06 with actual difficulty (2609.27063). The solver-panel prior is then updated by the learner's results, as `empirical` difficulty is today.

**Freshness gate (from former T3).**
- **Views.** Three per item:
  - the stem (multimodal when the item has a figure);
  - an **LLM solution skeleton**: technique sequence plus operation graph, written at mint time;
  - the facet definition.

  Plus a **symbolic fingerprint**: normalized answer, key quantities, sympy normal form where parseable, and the generator hash. It is stored in `item_fingerprints` (DERIVED, deterministic, rebuild owner registered).
- **Candidate pairs** come from kNN over administered surfaces of the same LO, in any view. A matching fingerprint marks a pair isomorph-suspect regardless of cosine.
- **Every pair above the blocking cutoff goes to the LLM isomorph judge** (R4).
- **The verdict is checked against the declared `variant_relation`:**
  - a declared `near` or `far` variant judged `isomorph` is relabelled;
  - a declared `isomorph` or `same_target` judged *the same surface* as an administered item is rejected as a duplicate.
- **Limits on embeddings.** They may block a candidate pending the judge, or add a familiarity discount. They never grant novelty (R1). `surface_hash` and hard namespaces stay exact.

**Selection.** From the survivors, select by MMR/Vendi diversity against administered history and against each other, weighted by verifier pass. For `ensemble` families, these scores are input to the selection judge, which makes the pick (§5.3). LLM samples collapse (Artificial Hivemind: 79% of same-model pairs have cosine > 0.8; NoveltyBench). The coverage axes stay LLM-labelled (QDAIF).

**Kept from former T3, shadow only:**
- **Exemplar retrieval** for distractor and probe generation: public banks plus the learner's logged errors, excluding anything structurally close to administered items (Feng et al., NAACL'24 Findings; MATH-Perturb).
- **Familiarity writer:** mean-centered cosine written into the existing `semantic_similarity` slot (`learner/familiarity.py:92`), behind `scheduling/kinship_feature.py`.
- **Transfer-distance sensor:** measured `variant_distance` logged beside the authored `transfer_distance` and `variant_relation`.

### 5.5 Grading support (replaces former T2's anchor sets; learner-blind)

These change the Slice 1 blind grader, so they land after S1.3. They come with a new `GRADING_PROMPT_VERSION` (`mvp-2.1-blind-reference-policy`) and the matching calibration-identity bump (Slice 1 §4.3).

- **Verified reference first.** The blind grader receives the family's verified reference. Rubric criteria stay, but they are not hand-tuned further (2608.17938).
- **No synthetic anchor sets by default.**
  - Judges are about twice as wrong on real responses as on synthetic ones, and restyling the synthetic text does not close the gap (MSE 2.96 vs ~1.2; 2606.10254).
  - Exemplar anchoring fixes the score level, not discrimination (2603.14732).
  - So `item_anchor_responses` is not built. Re-open it only if an E1-style grid shows anchors reduce error on the owner's *real* adjudicated answers.
  - The owner's real answers evaluate the grader; they are never grader input (S1).
- **Valid-alternative path (2608.28725: 75–85% false rejection of valid non-canonical traces).**
  - When the learner's trace diverges from the reference but the final answer verifies (CAS, exact key, or execution), the grader re-derives the learner's route independently instead of diffing it against the reference.
  - Negative evidence on a divergent-but-verifying answer requires the re-derivation to locate a concrete error. Otherwise the affected criteria are recorded `unverified`, not failed.
  - A per-family regression suite of canonical and valid-alternative traces (frontier-generated, CAS-checked) runs on every grader prompt or model change.
- **Solve-first when there is no verified reference** (teach-back, open "why", project defense).
  - The grader writes its own expected answer from the source before reading the learner's. This cut false accepts from 0.719 to 0.012 (2607.05904; 2607.12885).
  - It scores claims, not prose, because fluency and language bias run both ways (2607.28210).
- **One high-effort pass; no voting, juries, or debate** (Hard2Verify 2510.13744; 2604.26954; 2603.14732; 2608.00004). Where Slice 1's existing k-sampling runs, a shadow log records how often an asymmetric rule would differ from the modal fingerprint. The rule writes negative evidence only when every sample agrees (2608.00004).
- **Grade-uncertainty signal (shadow; from former T2).**
  - After grading, the new grade is compared with prior blind grades on the same family's variants, combined with the grader's verbal confidence.
  - The comparison stays within the family, because problem content dominates cross-item similarity (Borchers et al., LAK'26).
  - It feeds `manual_review_reason`, clarification eligibility, and regrade suggestions, in shadow. It is never an input to the grader.
  - Evidence: Cong et al., AIED'26; Ferrer et al. 2026.

### 5.6 Benchmark B2 and the pilot

- **B2 (isomorph / near-duplicate; owned by PF; runs before the freshness gate goes live).**
  - Positives: GSM-Symbolic templates.
  - Hard negatives: MATH-Perturb (MATH-P-Hard).
  - Equivalence pairs: MELD.
  - Compares stem vs LLM skeleton vs symbolic fingerprint vs LLM judge, sweeping MRL dims per domain. It uses `qwen/qwen3-embedding-8b`, and any other OpenRouter model, by config.
  - It sets the per-view blocking cutoffs (R4).
  - PF builds the shared `learnloop embeddings compare` harness (§4).
- **Pilot (PF-b's first run; its report tunes the filters and does not gate publishing, revised 2026-10-11).** One textbook chapter with quantitative families **generated both ways** (generator programs and ensemble), and one paper or repo with source-anchored families.
  - Sixty candidates each go through §5.4's filters, and survival is recorded per filter.
  - **Comparison against single-shot items** (revised 2026-10-11: no owner rating chore). An LLM judge compares 15 survivors against 15 single-shot items for depth and accuracy, blind and pairwise, with two passes and their agreement reported. Then, once published, usage signals: skips, "too easy", contests, retires and "unfair/ambiguous" taps per item source. An optional ≤ 10-minute owner rating can be added.
  - **Generation-path comparison** (added 2026-10-11). On the same quantitative families, three arms: single-shot items, generator-program survivors and ensemble survivors. Each arm reports:
    - survival per filter;
    - the panel-disagreement rate;
    - the blind pairwise LLM judge (two passes, agreement reported);
    - cost per published item;
    - once published, usage signals per item source.

    The report recommends the default path per topic type. If ensemble matches or beats programs, it becomes the default everywhere and programs remain the cheap path for procedural drill.
  - For a paper, its OpenReview rebuttal is the provenance anchor. For a repo, `git log` and issues are.
- **Scaling check: does quality rise with the model?** (added 2026-10-11). The pilot runs the generators (programs and ensemble proposers) and the LLM judges (family, isomorph, closed-book, selection) at **two configured model tiers**, a cheap route and a frontier route, on identical inputs. For each tier it reports:
  - filter survival rates;
  - judge agreement with the verifiers and with your undo / contest signals;
  - verified-reference pass rate;
  - an LLM judge's blind pairwise rating of 10 survivors per tier, interleaved and unlabeled (an optional owner spot-check);
  - cost.

  This is the bitter-lesson property tested directly. A component whose quality doesn't rise with model tier is where hand-built structure may beat more compute, and the report says so per component. Both tiers run under Slice A's spend caps, and every verdict and rating appends to `judgment_ledger`.

### 5.7 Rollout

| Step | Contents | Needs | Gate to proceed |
|---|---|---|---|
| **PF-a** | Family contract and fields (§5.1); `families propose` (exhaustive within-LO judge) + owner review; `family_memory_state`; replay report (§5.2). If the replay favours it: retention key live (successor, kill switch) | Slice A Phase 1 (embedding substrate; only needed for LOs above the exhaustive limit) | Correctness gates (§13); replay report reviewed |
| **PF-b** | Generator programs in bubblewrap and the ensemble path (proposers, solve-first agreement, structure check, selection judge), verified references, filters, freshness gate, solver panel, selection, **publication** (§5.3–5.4); B2; pilot (§5.6); **the practice index** (§5.9: dossiers, `find_practice`, coverage report, retrieval evaluation). Generation switch `pf.generation_enabled`, off in the template; Slice A spend controls | PF-a | Pilot and B2 reports reviewed |
| **PF-c** | Grading support (§5.5) | Slice 1 S1.3 (blind grader live) | E1-style report: valid-alternative false rejection, before vs after; error on real adjudicated answers |

**Why:** "I want to be able to transfer the concepts to other similar problems instead of having a fragile brittle memorization of the solution". Families separate the maintenance reps that keep a solution retrievable from the transfer probes that show it generalizes. Verified references and the source-span rules keep "why" items honest about what the authors (or past-you) actually said.

---

### 5.8 Judgments and model routes (added 2026-10-11)

**`judgment_ledger` (RAW_LEDGER, append-only)** is the single store for every verdict an LLM, verifier, or the owner makes in PF and later tracks. It provides the ground truth for evaluating learned components and for the scaling check. Columns:

| Column | Meaning |
|---|---|
| `id`, `created_at`, `supersedes_id` | Identity; a later verdict on the same question supersedes, never edits |
| `task` | e.g. `same_target` (family judge), `isomorph`, `closed_book`, `figure_only`, `provenance`, `reference_verified`, `pilot_rating`, `placement_override`, `selection`; T1 adds `same_cause` |
| `left_kind` / `left_id`, `right_kind` / `right_id` | Subjects; `right_*` is null for unary tasks |
| `judge` | `llm` \| `verifier` \| `owner` \| `diagnoser` \| `learner_card` \| `exact_key` |
| `judge_model`, `prompt_version`, `input_hash` | What produced the verdict and on exactly what input |
| `verdict`, `score` | A task-specific enum (`same` \| `different` \| `unsure`, `pass` \| `fail`, …) and an optional numeric score for ratings |
| `rationale` | Short text |

- **Who reads it.** Workflow tables (`family_proposals`, `pf_candidates`) hold queue and pipeline state only. Any report that needs a verdict reads the ledger.
- **What it never does.** A rebuild never re-runs a judge: the ledger is a persisted input. No verdict is evidence about the learner.

**Model routes.** Every paid PF component is its own config route, so tiers can be swapped and compared without code changes:
- `ai.routing.pf_generator`;
- `pf_proposers` (a list of models for the ensemble path; at least two different models), `pf_selection_judge`;
- `pf_family_judge`, `pf_isomorph_judge`, `pf_closed_book`;
- `pf_reference_verifier`, `pf_solver_panel`.

Receipts record model id and prompt version, and every PF report splits its results by model id.

### 5.9 Practice index: facet dossiers and `find_practice` (added 2026-10-11)

Facet dossiers moved here from the learner-field spec. That spec was reshaped and no longer uses them for prediction. Their real job is **organizing the vault's item–facet hypergraph for natural-language retrieval**: "which questions address this?" The pattern is the usual one: embeddings recall, an LLM decides, and the scheduler admits.

- **Facet dossiers.**
  - **Contents.** A frontier model writes one per active facet, grounded in its source spans, the items and rubric criteria that test it, and its structured fields. A dossier has four fields:
    - **scope:** covers and excludes;
    - **moves:** reasoning steps;
    - **errors:** typical mistakes;
    - **contrast:** how it differs from its nearest neighbours. Contrastive descriptions beat generic ones (FuDD, 2311.07593).
  - **Storage.** `facet_dossiers` (WORKFLOW), keyed by facet content hash, source hash, model and prompt version.
  - **Generation and cost.** Generated under Slice A's spend caps; regenerated only when the facet or its sources change, never on rebuild. That's cheap at 30–60 facets per vault.
  - **Embedding.** Each field is embedded as its own vector (`facet/dossier_scope`, `facet/dossier_moves`, `facet/dossier_errors`, `facet/dossier_contrast`). Embeddings use one short instruction, with the mean direction projected out under the same prefix and no whitening (2511.11041).
- **`find_practice(query, constraints)`**, a sidecar RPC and agent tool:
  1. **Which skill?** Facets ranked by dossier embeddings plus keyword (BM25) search over dossier text.
  2. **Which question?** Items tagged with those facets, ranked by item-outline embeddings (`item/skeleton`, §5.4) once they exist, otherwise by item text, plus keyword search over items. Facets are coarse (about 1.5–2 per LO), so the final ranking is always item-level.
  3. **Rerank.** An LLM picks and explains the best few. Verdicts go to `judgment_ledger` (task `practice_relevance`).
  4. **Admit.** Candidates pass the scheduler's eligibility rules: active status, LO lifecycle, freshness, the reveal ledger, reserved cold checks, exam reserves. **The tool proposes; it never serves directly.**
- **Consumers:**
  - the tutor or an agent asked "give me practice on X";
  - a "practice this" box in the daily loop;
  - **coverage:** facets with few eligible items become PF-b generation targets;
  - **capture routing:** filing a newly captured problem under facets;
  - **repair targeting:** diagnosis hypothesis text → facets → practice items (Slice 1 consumer).
- **Evaluation: retrieval, not prediction.**
  - **Labels** (revised 2026-10-11: no owner labelling chore). LLM relevance labels on held-out queries, in two passes with agreement reported, plus **usage signals**: which proposed items the learner actually practised, skipped, or marked "too easy" or "not what I asked for". All are stored in `judgment_ledger`. Owner labels are optional.
  - **Metrics.** Recall@10 and nDCG@10.
  - **The bar.** Two-level search through dossiers must beat **direct item search** (BM25 + item-outline or item-text embeddings) on held-out queries to stay in the path. Otherwise `find_practice` uses direct item search, and dossiers remain only as readable facet explanations for the tutor, diagnoser and map.
- **Not a router.** Block-level routing is `spec_action_router_v1.md`: Perplexity Decider v1.1 and a frontier LLM competing inside the P4 staged frame. Within a "practice on X" block, `find_practice` proposes the items. A learned router using dossier embeddings as features stays deferred (router spec §13).

---

## 6. Former T2 and T3 — disposition (2026-10-11)

| Former piece | Disposition |
|---|---|
| T2 §5.1 per-item synthetic anchor sets (`item_anchor_responses`) | **Not built by default** (§5.5). Re-open only on evidence from real answers |
| T2 §5.2 grade-uncertainty signal | Kept, shadow, within families (§5.5) |
| T3 three views + symbolic fingerprint (`item_fingerprints`) | Kept (§5.4) |
| T3 freshness gate | Kept. No calibrator dependency; the judge decides every blocked pair; the verdict is checked against the declared `variant_relation` (§5.4) |
| T3 familiarity writer, transfer-distance sensor | Kept, shadow (§5.4) |
| T3 novelty selection | Kept, after the verifier filters (§5.4) |
| T3 exemplar retrieval | Kept (§5.4) |
| B2 and the `isomorph` / `same_problem` calibrator tasks | B2 is owned by PF (§5.6). Calibrators are not built (owner, 2026-10-11); `isomorph` verdicts are ledger rows used for evaluation |
| Plan §A contrast-set factory (`ContrastSetV1`) | Its slots map onto `variant_relation`:<br>• same capability / different surface → `isomorph`<br>• different representation → `same_target` or `near`, as declared by the generator and checked by the judge<br>• same surface / different required operation → `near`, with declared checkpoint changes<br>• near transfer → `near`<br>• structurally isomorphic holdout → an `isomorph` reserved as a cold holdout |

---

## 7. T4 — Contamination detectors (shadow flags; lexical floor stays)

| Detector | Current | Addition |
|---|---|---|
| Held-out exam leakage — `content/authoring/practice_leakage.py:82-243` | 6-word shingle / distinctive numeric literal | Embedding kNN of generated practice vs held-out spans shortlists candidates; an LLM judge decides each `leak` flag, which goes for review |
| Tutor answer leak — `tutor/tutor_qa.py:685-721` | Substring / token recall ≥ 0.8 (its docstring admits it under-reports paraphrase) | Embedding similarity of tutor reply vs expected answer → shadow reveal flag. Math answers also go through the symbolic check (R2) |
| Reader reveal — `reader/reader_dialogue.py:333-387` | Word-bigram overlap ≥ 0.5 vs reserved assessment surfaces | Same as above. Flags propose reserve burns; they do not execute them until the report is reviewed |

**Why first-tier:** a missed paraphrased reveal silently contaminates exactly the cold evidence the plan calls scarce.

---

## 8. T5 — Ingest and graph nomination

**Current code:**
- `content/synthesis/append_neighborhood.py:198-270` — Jaccard with thresholds 0.5 / 0.25 / 0.4 / 0.12.
- `content/synthesis/synthesis_gates.py:653-692` and `facet_mint_gate.py:277-372`:
  - Jaccard ≥ 0.85;
  - `distinct_repair` / `separable` are set differences over normalized text, which biases the gate toward MINT.
- `content/synthesis/source_set_synthesis.py:597-631, 2376, 2458+` — concept identity by slug; the structuring LLM gets registry concepts as **ids only**.
- Review passes: `ops/doctor.py:1855, 2027`, `facet_doctor.py`, `facet_candidates.py`.

**Change (EDC pattern, EMNLP'24):**
- Embed **LLM-written definitions** of facets and concepts, not bare labels.
- Nominate the top-k neighbours, unioned with the existing lexical and provenance reasons.
- **The reconciliation/structuring LLM or the owner decides.**
- The structuring pass receives registry concept titles and definitions for the nominated candidates, not ids alone.
- Add a repair-equivalence shadow for `distinct_repair`.
- Doctor and review passes gain a cosine column next to Jaccard.

**Constraint:** `spec_knowledge_model.md:588` ("no embeddings for facet identity") holds. These are nominations, never identity. Embedding-merged KC sets under-merge relative to experts (Wang, Lin, Koedinger 2025), which is further reason to nominate, not merge.

---

## 9. T6 — Source retrieval

**Current code:**
- `tutor/tutor_qa.py:868-990` takes the top-4 LO-linked spans, independent of the question.
- Library search is `instr(lower(text), ?)` (`reader/source_search.py`; `db/repositories.py:11872`).
- Quick-add scope is a substring keyword match (`content/pipeline/quick_add.py:155-190`).
- Span → LO mapping returns `[]` without a provenance link (`reader/reader_progression.py:43`).

**Change:**
- **Hybrid retrieval.** SQLite FTS5 BM25 (`source_block_fts`, DERIVED, rebuildable from source blocks) plus dense retrieval over source blocks, fused by RRF.
- **LLM query rewriting** for conceptual questions (BRIGHT, ICLR'25: reasoning-rewritten queries beat raw dense retrieval; classic cross-encoders hurt).
- **LLM listwise rerank** only on consequential paths.
- **PDF pages.** Page-image embeddings alongside Marker text chunks, if B4 supports it. Gemini Embedding 2 accepts PDF and image input; the text-only candidates embed Marker chunks only.
- **Benchmark B4 (owned by T6).**
  - Compares page-image embeddings (Gemini Embedding 2) vs Marker text chunks (all candidates) on the owner's math-heavy PDFs (fixtures `probability`, `linear_algebra`, `arxiv_v2`).
  - Measured by retrieval on question → page pairs. An LLM labels them in two passes with agreement reported; owner labels are optional (frictionless defaults R1).
  - Runs in the shared `learnloop embeddings compare` harness (`--bench B4`), which PF built for B2.
- **Nearest-LO suggestion** for spans without provenance, labelled as a suggestion.
- **Grounding stays two-stage:** retrieve spans, then verify with an NLI checker or LLM.

---

## 10. T7 — Knowledge-map neighbors (display only)

`learnloop_sidecar/handlers/knowledge_map.py:670` blends facet-vector cosine (0.6) with concept-graph geodesic distance (0.4). Add item-text similarity as a third term, or as the source of the four shown neighbours. It has zero learner-state effect.

---

## 11. T8 — Learner success head (research, offline)

**Question:** does a frozen-embedding predictor of success on never-seen items beat a tags + base-rate + forgetting logistic for *this* learner? No published n=1 evaluation exists.

**Model:** a GP classifier (or Bayesian logistic) over:
- a fixed 16–32-d projection of the embedding of stem + LLM solution skeleton (PF §5.4) + KC/operation tags;
- a tag kernel;
- a time-decay kernel;
- a difficulty prior. *Revised 2026-10-11:* use PF's solver-panel difficulty rather than the LLM's own rating; LLM difficulty labels correlated at ρ = 0.06 with real difficulty in 2609.27063.

Predictive variance widens off-support. **The LLM never outputs the probability**; zero-shot LLM correctness prediction sat at the base rate (EDM'26).

*Note (2026-10-11):* 2610.11135 reports the opposite in LearnLoop's regime. A zero-data LLM probability call reached AUC 0.706, beating deep KT trained on 8 learners (single preprint, commercial model). Add it as a comparison arm in the replay; this does not change the rule above.

**Evaluation:** temporal replay on vault history; log-loss, Brier, and reliability plots versus the baseline; pre-registered before running. No live consumer in this slice. A positive result feeds plan workstream B/J.

**First arm, `emb_ridge`** (added 2026-10-12). This is the cheapest test, and it needs no new data.
- **Model:** ridge or logistic regression over the already-stored `qwen3-embedding-8b` vectors (stem, plus the skeleton once PF-b lands) concatenated with the learner-state features the explicit arms use. It is fit prequentially, as an arm in `learnloop eval` (field §7.2), against `mastery_ekf` and `lo_general`.
- **Decision rule.** *Revised 2026-10-12 (owner; T8 pre-registration v4, recorded in `docs/reviews/slice-2-t8.md`).* The earlier wording made an interval that includes 0 a kill; that no longer holds.
  - **Statistic:** the attempt-weighted mean per-attempt log-loss gain over the best explicit arm e*, Δ = loss(e*) − loss(`emb_ridge`).
  - **Interval:** a 95% cluster-robust t interval over items: CR1 standard error, t with (items − 1) degrees of freedom. There is no minimum number of attempts or items; with few items, t widens on its own.
  - **Constants:** the margin m = 0 (D9) and the smallest worthwhile gain δ = 0.005 nats per attempt, both fixed before the run. T8 takes only D9's *margin*: its interval is the registered t interval above, not the bootstrap interval D9 names for the field's switching rule (`spec_learner_field_v1.md` D9).
  - **`kill`** if the interval's upper bound is below δ. That includes a real gain below δ (the whole interval inside (0, δ), reason `real_gain_below_delta`). Embeddings then add no held-out predictive value worth building on, and the GP model above isn't built. An interval that includes 0 is a kill only if it also lies below δ. A `real_gain_below_delta` kill is provisional: the realized prequential gain includes the period in which the embedding block is still learning, so rerun when the data has grown.
  - **`embeddings_add_value`** otherwise, if the lower bound is above m.
  - **`insufficient_data`** otherwise: the interval reaches both m and δ, or no interval exists (one item, or no variation across items). It is no decision; rerun with more data.
  - **Every report records** the δ in force, with m, n, the item count, the interval and its method, so δ itself can be revisited.
- **Why it matters beyond T8:** its result is condition 3 of the learned-router trigger (`spec_action_router_v1.md` §13). That condition reads the lower bound, not the verdict name: `embeddings_add_value`, or a `real_gain_below_delta` kill, meets it (router D10). δ is the bar for the success head only.

---

## 12. Persistence summary

New tables use the next free migration numbers after Slice 1's 166, following the `CLAUDE.md` head-fixture procedure each time.

| Table | Role | Track |
|---|---|---|
| `judgment_ledger` | RAW_LEDGER | Slice A (PF §5.8); T1 adds `same_cause` (formerly `embedding_adjudications`) |
| `hypothesis_recurrence_groups` | DERIVED (rebuild owner registered) | T1 |
| ~~`item_anchor_responses`~~ | not built (§5.5) | — |
| `item_fingerprints` | DERIVED (rebuild owner registered) | PF |
| `family_memory_state` | DERIVED (rebuild owner registered; shadow) | PF |
| `family_proposals` | WORKFLOW (backfill review queue and judge verdicts) | PF |
| `pf_candidates` | WORKFLOW (generated candidates, filter results, verification status, cost) | PF |
| `item_skeletons` | WORKFLOW (LLM-written solution skeletons keyed by item content hash; never regenerated on rebuild) | PF |
| `facet_dossiers` | WORKFLOW (paid outputs; never regenerated on rebuild) | PF §5.9 |
| `source_block_fts` (FTS5) | DERIVED (rebuild owner registered) | T6 |

**Vault content changes (PF):**
- a new `ActivityFamily` model (the authored content of an activity family, P12), holding the generator program text and hash for `generator` families;
- optional `PracticeItem.family_id` and `PracticeItem.variant_relation`;
- a new `difficulty_source` value, `"solver_panel"`.

All are additive; vaults without families load and rebuild unchanged.

**New `record_kind`s** in `embedding_vectors`, each declaring its text recipe (R3):
- `item/stem`, `item/skeleton`, `facet/definition` (PF), `facet/dossier_scope`, `facet/dossier_moves`, `facet/dossier_errors`, `facet/dossier_contrast` (PF §5.9), `concept/definition`;
- `source_block/text`, `source_page/image`.

---

## 13. Evaluation

Report-based, with a noise floor, as in Slice 1 §13.

**Correctness gates:**
- R1 holds: no code path lets an embedding score alone write evidence, grant novelty, or merge identity. Asserted by tests that stub the judge to "different" and verify no merge or unblock happens.
- Replay makes no embedding calls.
- The same-answer/different-cause regression suite has zero false merges.
- The no-chaining rule: a fixture with A~B, B~C, and A≁C never yields one group.
- Singleton recurrence groups rebuild identically to the pre-T1 `statement_normalized` keys.
- Blocking cutoffs are keyed by `model_id` and re-derived on a model change. No code path merges, rejects, or skips the judge by score.
- **PF gates:**
  - Replay never executes a generator program.
  - Vaults with no families rebuild byte-identically.
  - `family_memory_state` rebuilds deterministically and is updated only by graded cold attempts on `same_target` / `isomorph` variants.
  - Every family traces to an auto-accept decision (two agreeing judge passes) or an authored record, and every decision can be undone in one step.
  - No learner answer or prior grade reaches `BlindGradingContext` through PF's grading support (S1; asserted on fixtures).
  - An item with an `unverified` reference is never published (so it can never certify).
  - **Ensemble path:**
    - a candidate whose panel solves disagree with its proposer is never published;
    - the selection judge is never offered an unverified candidate, which is asserted by a fake judge that would pick it;
    - a declared ensemble isomorph without a passing structure check is never published as `isomorph`;
    - `pf_proposers` with fewer than two distinct models is refused.
  - The generator sandbox runs under bubblewrap and fails closed without it. Tests show network, vault reads, and writes outside scratch are all denied.
  - Items without a family serialize byte-identically, and `practice_item_hash` is unchanged.
  - The publish cap holds per day.
  - Every LLM or owner verdict PF produces appears in `judgment_ledger` with model, prompt version, and input hash. A rebuild re-runs no judge.
  - Every PF report splits results by model id.

**Per-track reports:**
- **T1:** B1, B3, and M3 signals; merge precision and recall on replay.
- **PF:**
  - the idea-identity replay;
  - B2;
  - pilot filter survival and blind depth rating, split by generation path (single-shot, program, ensemble);
  - isomorph-suspect rates on replayed history;
  - declared-vs-judged `variant_relation` disagreement;
  - valid-alternative false rejection and real-answer error before vs after §5.5.
- **T4:** flag rates with audited samples.
- **T5:** nomination recall on doctor-found duplicates.
- **T6:** B4; retrieval recall on LLM-labelled question → span pairs (two passes, with agreement reported).
- **T8:** replay calibration.

---

## 14. Non-goals

- Fine-tuning any embedder. Revisit only if B1 shows a large gap to ceiling *and* an independent labelled corpus exists (plan H gate).
- Embeddings as learner state, evidence, or identity.
- ANN indices; brute force suffices at this scale.
- Cross-vault vector sharing. Vectors are near-plaintext (vec2text).
- A learned router or bandit over embedding features (plan G).

## 15. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| P1 | Track order | **Decided (owner, 2026-10-11):** PF in Slice A; T6 alongside the daily loop after Slice A; after Slice 1 M2's exit review, T1 (= M3) → T4 → T5 → T7 → T8, each after the previous report is reviewed |
| P2 | Auto-accept zone allowed for any task in this slice? | **Obsolete (2026-10-11):** calibrators are dropped, so nothing is auto-accepted by score. PF families are auto-accepted only when two judge passes agree (§5.2), with one-step undo |
| P13 | Calibrators and skip-the-LLM logic? | **Decided (owner, 2026-10-11): dropped.** Embeddings shortlist at benchmark-set blocking cutoffs, and judges decide everything above them (R4). `judgment_ledger` is evaluation data |
| P3 | ~~Anchor-set generation cost~~ | **Obsolete (2026-10-11):** synthetic anchor sets are not built (§5.5) |
| P4 | Page-image retrieval (T6) default on for PDFs? | Only if B4 shows a gain over text chunks |
| P5 | ~~Local model evaluation timing~~ | **Revised 2026-10-11 (owner):** Slice 1 uses `qwen/qwen3-embedding-8b` via OpenRouter, and learner text leaving the machine is acceptable. The comparison happens in T1's B1/B3, and local models are optional |
| P7 | ~~Generator sandbox~~ | **Resolved 2026-10-11:** reuse the bubblewrap boundary from animation rendering; fail closed without it (§5.3) |
| P8 | Family backfill: propose families for existing items, or only for newly generated items? | Existing items, with the exhaustive within-LO judge. *Revised 2026-10-11:* auto-accept confident families with one-step undo; ambiguous items stay unfamilied; no review queue |
| P9 | ~~May an `unverified` reference ever certify cold evidence?~~ | **Resolved 2026-10-11:** unverified candidates are never published |
| P10 | Solver panel composition and cost | 2–3 models at different tiers, ~3 solves each per candidate, at mint time only. Drop to one tier if the pilot shows the panel rarely changes selection |
| P12 | How does the practice family relate to the existing activity-lineage substrate (`migrations/065_activity_lineage_substrate.sql`: `activity_families` → `activity_cards` → `activity_surfaces`, with lineage, exposure and reservation tracking)? | **Decided (owner, 2026-10-11): merge the terms.** One family concept: a practice family is an `activity_families` row with purpose `practice`; cards carry memory state; surfaces are concrete questions. The vault model is `ActivityFamily`. Mapping and the three mechanics the Phase 3 agent confirms are in §5.1 "Where families live" |
| P11 | Does `isomorph` count as a maintenance rep in `family_memory_state`, or only `same_target`? | Both in the shadow state. The replay's variant-distance covariate tests whether isomorphs should be discounted |
| P6 | Same-cause judge: separate LLM call for out-of-context pairs, or rely on diagnoser links only? | Both, as specified. Drop the separate judge if B3 shows diagnoser links alone recover nearly all confirmed recurrences |

---

*Related: `spec_blind_grading_diagnosis_split_v1.md` · [[Embedding Integration Map]] · [[Pipeline Augmentation Plan]] · [[Bitter Lesson Research Sweep]] · `spec_knowledge_model.md` · `spec_causal_attribution_v1.md`*
