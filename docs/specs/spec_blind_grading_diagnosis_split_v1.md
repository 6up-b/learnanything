# Blind grading, history-aware diagnosis, and the embedding substrate — Slice 1 (v1)

**Status:** draft for owner review (2026-09-30; revised 2026-10-11). This is the first implementation slice of `docs/brainstorming/Pipeline Augmentation Plan.md`. **Followed by** `spec_embedding_consumers_v1.md` (Slice 2), which builds the wider embedding integration on the substrate this slice lands.

**Revision 2026-10-11 (bitter-lesson review; citations in `docs/brainstorming/Bitter Lesson Research Sweep.md`):**
- **M1 gains two history arms** (§12.1):
  - **(d)** the full exact-filtered history in long context;
  - **(e)** the diagnoser with read-only access to an as-of snapshot of the history.

  At ~10³ events a year, a frontier reader can read the whole filtered neighborhood. So kNN has to beat (d) and (e) to earn a place in the diagnosis context.
- **The four-model embedding bake-off leaves M1.** Forty items cannot separate embedding models. M1 builds one client (OpenAI-compatible, pointed at OpenRouter) and uses one model, `qwen/qwen3-embedding-8b`. The comparison moves to Slice 2 B1 (Eedi) and B3 (vault replay) (§9.1).
- **E1 gains two grader probes** (§13): valid-alternative false rejection and the real-vs-synthetic error gap.
- **M2's history mode defaults to `full`** (exact filters + the full filtered history) unless M1 shows hybrid kNN clearly beats it. Embedding hypotheses for the would-merge log stays in M2 regardless of the mode (§9.3, §12).
- **Order revised (owner, 2026-10-11):** Slice A (`spec_slice_a_practice_and_field_v1.md`) lands first.
  - It delivers this slice's embedding substrate (§9.1–9.2), so S1.4a here adds only the `hypothesis` and `misconception` record kinds.
  - "Migration 166" and `mvp-0.10` in this spec become the next free numbers at implementation time.
  - Slice 2's PF grading rules (§5.5 there) are folded into the blind prompt at S1.1.

**Owner decisions (2026-09-30):**
- **Diagnosis is asynchronous in this slice** (§11).
- **The diagnoser model is its own config route**, `ai.routing.diagnosis`, which defaults to the grading provider (§9.1).
- **Embeddings are enabled for the owner vault**, behind a model-agnostic interface. *Revised 2026-10-11 (owner):* M1 uses one API model through OpenRouter, `qwen/qwen3-embedding-8b`. Sending learner text to an embedding provider is acceptable. The model comparison moves to Slice 2 B1/B3 (§9.1). The original candidates were:
  - Qwen3-Embedding-4B (local);
  - Qwen3-Embedding-0.6B (local);
  - OpenAI `text-embedding-3-small`;
  - Gemini Embedding 2.
- **No numeric revert thresholds yet.** Evaluation measures and reports; thresholds get set later from observed baselines (§13).
- **Build just enough to get learner signal on the direction (§12).** Milestone **M1** is an offline, blinded review of new diagnoses over the owner's existing history, before any live change. **M2** is the live split with a diagnosis card. **M3** (recurrence with authority) lives in Slice 2. The in-app shadow period (formerly S1.2) is dropped: M1 answers its questions sooner.

**What it implements from the plan:**

| Plan item | What this slice builds |
|---|---|
| Row 0 (event contract) | The observation/hypothesis split: the blind grade becomes the plan's `ObservedResponseV1`; diagnosis becomes a separate ledger |
| Row 1 (workstream A MVP) | Trace-memory write path, diagnostic-memory consumer, shadow recurrence |
| Row 2 (B0) | A narrow slice: a diagnosis context rendered from existing projections — not a full `LearnerStateCardV1` |

**Relationship to other documents:**

| Document | Disposition |
|---|---|
| `spec_causal_attribution_v1.md` | Authority model (§2), producer–confirmer matrix, and causal-state ownership (§3) are inherited unchanged. This slice separates the "Grader/diagnostician" producer row into two producers with different inputs. |
| `spec_diagnostic_augmentation_v1.md` §C4 | **Relocated.** C4 specified "learner history in the *diagnosis* context". Because grading and diagnosis were one call, it landed in the grader. It moves to the diagnoser, together with its revert criterion (the changed-cause planted learner). |
| `spec_diagnostic_augmentation_v1.md` §C3 | **Split.** Grader k-sampling measures grade/localization agreement only; cause disagreement moves to diagnoser sampling (§4.4). |
| `docs/brainstorming/Embedding Integration Map.md` | Source of §9 and of the "LLM writes the text, the embedder recalls, the LLM/key decides" pattern. |
| Plan invariant 1 | Reworded (§15): the *grading role* is learner-blind; the diagnosis role may read history. |

---

## 0. Thesis

Today one LLM call (`grading_proposal`, `attempts/ai_contracts.py:367`) both **measures** the answer and **explains** it. It is handed the learner's prior traces (C4, `diagnostic_augmentation.py:331-379`) and told to "test recurrence". So the measurement that every downstream belief rests on is conditioned on history, and the explanation is limited to what fits in a grading prompt. This causes three problems:

1. **The measurement is not independent.** A grader primed by past traces can grade toward the recurring story. Every grade is evidence (authority level 3), so any anchoring becomes evidence.
2. **The explanation is too narrow.** History reaches the call only when facets overlap *and* `surface_family` matches exactly. So cross-surface recurrence — the most diagnostic kind — is excluded. There is no prerequisite context, no positive evidence, and no prior hypotheses with their status.
3. **Recurrence is exact-string.** `_factor_signature` (`causal_factor_deferral.py:267-282`) and `_projected_causal_candidates` (`repositories.py:2346-2363`) group hypotheses by `normalize_text(statement)`. A reworded cause never recurs, so K=3 escalation and promotion rarely fire on genuine recurrence.

This slice separates the roles:

- **Grader — learner-blind.** It measures *this* answer: score, criteria, where it first went wrong, the minimal repaired trace, and local error type. It never sees the learner's history or any prior verdict.
- **Diagnoser — history-aware.** It explains the failure, using retrieved past traces *with their blind grades* (successes as well as failures), prior hypotheses with their status, the prerequisite neighborhood, and the misconception registry. It proposes causes, cross-attempt patterns, prerequisite gaps, and repairs.
- **Router — unchanged authority.** It consumes the grade as evidence and the diagnosis as a typed hypothesis set through the existing causal machinery.

Separating the roles is what makes it safe for the diagnoser to see past *grades*: they were produced blind, so the self-confirming loop (grader → verdict → grader) cannot form.

**How the diagnoser gets its history is an empirical question, settled by M1, not assumed** (§5.2, §12.1). The candidates are:
- a short exact-filtered list;
- the whole exact-filtered history in long context;
- read-only access to an as-of snapshot of the history;
- hybrid kNN.

The default leans toward spending model compute (reading more), not toward hand-tuned similarity. Context rot beyond ~100K tokens is the known limit on that.

**The dividing line** is *localizing the error* vs *explaining its cause*, not "grade vs diagnosis". Several fields that look diagnostic synchronously drive mastery writes inside the attempt transaction: `error_type`, `severity`, `target_*`, `resolution_status`, and parts of `cause_scope`. They stay with the grader (§4.2).

---

## 1. Scope

**In scope:**
- A1. The `BlindGradingProposal` contract and blind grading prompt.
- A2. The `DiagnosisProposal` contract, the `DiagnosisContext` assembler, and validators.
- A3. The diagnosis ledger and context receipts (migration 166); a legacy adapter; replay reading both shapes.
- A4. Relocating causal-episode materialization and misconception normalization to after diagnosis. The `misconception_match` call is retired in split vaults.
- A5. Router consumption:
  - live: hypotheses, repairs, registry matches;
  - shadow: validated-citation recurrence and prerequisite-gap hypotheses.
- A6. The embedding substrate:
  - a model-agnostic `EmbeddingClient` interface with **one** implementation in this slice: an OpenAI-compatible client pointed at OpenRouter's `/embeddings` endpoint, running `qwen/qwen3-embedding-8b`. The same client reaches every OpenRouter embedding model, so Slice 2's B1/B3 comparison needs no new client. The local sentence-transformers client becomes optional (Slice 2);
  - a vector store;
  - embed-on-write for hypotheses and the registry (always, for the would-merge log), and for attempt divergences (only when the history mode is `hybrid`);
  - hybrid retrieval for the diagnosis context, as M1 arm (c). It goes live only if it beats the `full` arm (§12.1);
  - a shadow recurrence would-merge log.
- A11. Diagnosis history modes `full` and `snapshot` (§5.2, §5.6): the M1 arms (d) and (e), and the M2 candidates.
- A7. The evaluation harness and reports (§13), plus the `learnloop diagnose` dual-run command.
- A9. The **M1 offline review** (`learnloop diagnose review`) and the **M2 diagnosis card** — the learner-facing instruments that decide whether this direction is working (§12.1–12.2).
- A10. The `recurrence_key(hypothesis)` seam: every exact-statement grouping site is routed through one function, behaviour-neutral in this slice, so Slice 2 T1 only changes that function (§7.6).
- A8. Asynchronous post-attempt execution: a durable job queue and a sidecar worker, ordered diagnosis, bounded next-item waiting, and UI polling for pending diagnoses (§11).

**Out of scope (§16; the embedding items are specified in `spec_embedding_consumers_v1.md`):**
- live authority for validated recurrence;
- a prerequisite-descend route;
- per-item graded anchor sets for the grader;
- freshness, leak, ingest, and source-retrieval embedding consumers;
- a learner success-prediction head;
- a full `LearnerStateCardV1` projection.

---

## 2. Standing constraints

Inherited from `spec_causal_attribution_v1.md` and `spec_diagnostic_augmentation_v1.md` §1: bitter-lesson alignment, schema minimalism, no augmentation without a rejection criterion, deterministic-over-model-reported, facets stay, capture-now. In addition:

- **S1. The grading context carries no learner-derived material beyond the current answer.** That excludes:
  - prior traces, prior grades, prior diagnoses, hypotheses, the misconception registry, and state renderings;
  - retrieval results over learner data.

  Item-side material stays: prompt, reference solution, rubric, trace contract, taxonomy, facet registry, discrimination profiles, verifier observations, and the current attempt's own clarification exchange.

  This is enforced structurally: `BlindGradingContext` has no field that can hold it (§4.1). The blinding receipt records the grader mode (§10).
- **S2. The diagnoser never writes evidence.** Its output is authority level 4 (derived causal hypotheses). It may *group* existing blind observations; it may not create, re-grade, or re-weight them (plan invariant 2). Mastery, facet, and scheduling writes from an attempt come only from the blind grade.
- **S3. The diagnoser sees prior grades, never prior diagnosis prose.** Prior hypotheses appear only as typed records with their lifecycle status (candidate / probe-confirmed / refuted / withdrawn / superseded) and evidence counts. Free-text `analysis_md` from earlier diagnoses is never re-fed. This limits anchoring to structured claims that can be checked.
- **S4. Every cross-attempt claim cites blind evidence.** A pattern or recurrence claim lists attempt ids and verbatim quotes. It counts toward recurrence only if each cited attempt's *blind* grade independently shows a non-pass on an overlapping target (§5.4).
- **S5. The router's authority is unchanged.** Diagnosis enters through the existing `causal_hypotheses` → repair classes → factor → orchestrator → `decide_probe` path. New signals (validated recurrence, prerequisite gaps, retrieval sets) are shadow in this slice.
- **S6. No step depends on embeddings for correctness.** With the embedding provider unconfigured or failing, retrieval falls back to exact filters + recency (§5.2). Embeddings are an index, never learner state; replay never re-embeds (`docs/specs/open-questions.md:103-105`).
- **S7. Replay never calls an LLM or the embedding API.** Diagnosis is a raw ledger that replay reads, exactly as it reads `error_events` today.

---

## 3. Target architecture

```
submit_attempt (sidecar practice.py:489)
  │
  ├─ deterministic grade (grading.py:296)  ── no LLM; unchanged
  │
  ├─ BLIND GRADER  [sync, inside attempt txn path]
  │    BlindGradingContext  ──►  BlindGradingProposal
  │    validate (grading.py:806 validators, minus causal fields)
  │    apply_attempt: grading_evidence, error_events(local), mastery/facet writes,
  │                   feedback, clarification, exercised facets
  │    receipt: diagnostic_augmentation_receipts.grader_mode = 'blind'
  │
  ├─ run_post_attempt_pipeline, SYNC PART (post_attempt.py:73)  [outside txn]
  │    grade-dependent hooks only:
  │      record_cold_verification_from_task, auto_classify_pinned_probe,
  │      sweep_machine_checks, evaluate_intervention_followup (grade-keyed)
  │    enqueue post_attempt_jobs(kind='diagnose')      ← same step, resumable
  │
  └─ return feedback (grade, local feedback, repaired trace, diagnosis_status='pending')

POST-ATTEMPT WORKER  [sidecar daemon thread; own DB connection; serial in attempt order]
  job kind='diagnose' (only when the blind grade has a non-pass criterion or an
  error attribution; correct answers sampled at a configurable shadow rate)
       ├─ DiagnosisContext assembler ── as-of cutoff; history mode exact | full | snapshot | hybrid (§5.2)
       ├─ DIAGNOSER ── DiagnosisProposal ── validate (citations, ids, firewall, repairs)
       ├─ persist: attempt_diagnoses (RAW_LEDGER), diagnosis_context_receipts (RECEIPT)
       ├─ materialize_causal_episode  (relocated; reads diagnosis)       [live]
       ├─ misconception normalization (registry_match; no extra LLM call) [live]
       ├─ sweep_machine_checks, _consult_common_repair                    [live]
       ├─ validated-citation recurrence + prerequisite-gap log            [shadow]
       └─ enqueue kind='embed' jobs
  job kind='embed' (separate slot; best effort): traces, hypotheses, registry
```

| Stage | Authority level (causal-attribution §2) | Reads learner history? | Writes |
|---|---|---|---|
| Blind grader | 3 — measurement interpretation | **No** | evidence, local attribution, feedback |
| Diagnoser | 4 — derived causal hypotheses | Yes (blind grades, typed hypotheses, graph, registry) | diagnosis ledger only |
| Causal materialization | 5 — validated causal record | via diagnosis ledger | hypotheses, repair classes, factors, receipt |
| Router / orchestrator | 6 — policy | projections | decisions + receipts |

---

## 4. The grader contract

### 4.1 `BlindGradingContext`

This is today's `GradingContext` (`attempts/ai_contracts.py`, built at `grading.py:674-723`) **without** `diagnostic_history`. It is a new dataclass rather than an empty list, so S1 cannot be undone by a config value. `augment_grading_context` (`diagnostic_augmentation.py:382`) keeps attaching C2 `verifier_observations` and stops attaching C4.

`grading_context_hash` (`grading.py:783-803`) covers the new shape. `DiagnosticAugmentationConfig.history_limit` (`config/schema.py:1264`) is ignored in split vaults and deprecated in favour of `diagnosis.history_*` (§12).

**Non-practice grading call sites** already call without augmentation: regrade `attempts/regrade.py:198`, teach-back `tutor/teach_back.py:648`, exams (`handlers/exams.py:184`, `cli/exam.py:124`), probe audit, and taxonomy regrade. In split vaults they call the blind prompt and contract. Only practice attempts trigger the diagnoser in this slice.

### 4.2 Field disposition

Every current `GradingProposal` / `ErrorAttribution` / `RepairSuggestion` field maps as follows. "G" = blind grader, "D" = diagnoser.

| Current field | Owner | Notes |
|---|---|---|
| `criterion_evidence` (incl. `learner_confidence`) | G | Scoring authority; unchanged |
| `rubric_score`, `fatal_errors`, `grader_confidence`, `manual_review_recommended` | G | Unchanged |
| `feedback_md` | G | Answer-local feedback only; must not reference history |
| `diagnosis_md` | G, renamed **`local_analysis_md`** | Still written first. Explains what is wrong *in this answer*. This is also the history-free reading the anti-anchoring check compares against (§5.5) |
| `exercised_facets`, `clarification_request`, `error_hunt_report`, `discrimination_profile_match` | G | Item-local observations / pre-registered signature matches |
| `RepairSuggestion.repaired_trace` | G, moved to top-level **`repaired_traces[]`** (each with an id) | A minimal edit of *this* answer. Still validated by splice/prefix/checkpoints (`grading.py:1187-1413`) |
| `ErrorAttribution.error_type`, `severity`, `evidence` | G | Drive mastery weight, surprise, and error impact synchronously |
| `target_evidence_families`, `target_criterion_ids`, `target_ref` | G | Drive the passed-facet firewall, `derive_facet_outcomes`, and the `attribution_json` failure-mass allocation. Localization, not causation |
| `resolution_status`, `abstention_reason` | G | Now mean **localization** resolved/unresolved/abstained. The projection's unresolved-factor opening (`canonical_projection.py:450`) moves to diagnosis (§7) |
| `first_divergence`, `localization_confidence` | G | Local anchor; server-side re-anchoring unchanged |
| `facet_contrast` | G (**open decision O3**) | Which facet the answer evidences vs a confusable one — observational, but borderline |
| `cause_scope` | **Split** | G keeps **`validity_scope`** ∈ {`valid_measurement`, `item_contract`, `grader_interpretation`, `interaction_context`, `unknown`}; it gates negative evidence and manual review (`grading.py:1156-1162`, `attempts.py:1910-1937`). D owns **`causal_class`** ∈ {`learner_state`, `transient_execution`, `unknown`}, only for `valid_measurement` events. D can never set `item_contract` / `grader_interpretation`; per the producer matrix, only the grader flags those |
| `is_misconception` | **D** (**open decision O2**) | Slip-vs-misconception is the judgment history helps most. At grade time `error_events.is_misconception` takes the taxonomy prior `_is_misconception(vault, error_type)` (`attempts.py:3497`); the diagnoser's `causal_class` is authoritative for causal consumers. `raw_grade_events.signature_matched` (`attempts.py:1382`) switches to `discrimination_profile_match` |
| `misconception_statement`, `misconception_consistent_answer` | D | |
| `operation`, `candidate_causes[]`, `causal_confidence` | D | `CandidateCause` schema (`ai/schemas.py:156-209`) reused unchanged |
| `postdictive_claims`, `soft_postdictive_claims` | D | Still veto promotion (`misconceptions.py:280-311`) |
| `RepairSuggestion` instructional fields: `practice_mode`, `operator`, `target_refs`, `preserve_refs`, `expected_minutes`, `answer_reveal_budget`, `eliciting_question`, `expected_response_contract`, `rationale`, `learning_object_id`, `verification_request`, `target_*` | D | Each repair references a grader `repaired_trace_id` when it builds on one. `validate_repair_candidate` (`grading.py:1440-1449`) is reused |
| harness-set `diagnostic_sample_support`, `facet_write_blocked` | unchanged | |

### 4.3 Prompt

- The new `GRADING_PROMPT_VERSION` is `"mvp-2.0-blind-local-grader"`. The task text drops every causal instruction (candidate causes, misconception statements, repair operators) and the "test recurrence" sentence (`ai_contracts.py:410-412`).
- Generation order stays: `local_analysis_md` → `repaired_traces` → localization fields → `exercised_facets` last.
- **Calibration identity bumps too.** `attempts/grader_calibration.py:58-59` has its own `GRADING_PROMPT_VERSION = "grading_prompt_v1"` / `GRADER_OUTPUT_SCHEMA_VERSION = "grading_proposal_v1"`, which `grade_resolution.py:156-188` stamps into `raw_grade_events`. Both bump (`grading_prompt_v2_blind`, `blind_grading_proposal_v1`) so calibration never pools joint and blind graders.

### 4.4 Sampling

- `run_diagnosis_samples` (`diagnostic_augmentation.py:503`) keeps k-sampling for the grader. In split mode, the modal fingerprint is over (abstained, anchor, criterion outcomes) only. It no longer rewrites disagreement into `candidate_causes` (`:552-586`); there are none.
- Cause disagreement is measured by `diagnosis.sample_count` (default 1).
- The stale "k=3" comment at `attempts.py:1079` is corrected.

---

## 5. The diagnoser contract

### 5.1 When it runs

- **Practice attempts in split vaults (live):** when the blind grade has any criterion below full points, any fatal error, or any error attribution.
- **Correct answers:** sampled at `diagnosis.correct_answer_sample_rate` (default 0.0, shadow-only when > 0). "The Correct Answer Trap" (AIED'26 workshop) found about 8 false positives per true detection at realistic prevalence, so this never feeds routing in S1.
- **Skipped:** deterministic grades with no error; self-grades (no blind model grade to cite); diagnostic-block submissions still measuring (`post_attempt.py:198` `_defers_to_block_end`, same rule as today).
- **Shadow mode (optional; not a rollout step):** on joint vaults, `diagnosis.shadow = true` runs the same trigger and the same async worker. The diagnosis is persisted with `mode='shadow'` and none of the post-diagnosis steps run. It remains available for re-checking a new diagnoser model or prompt against live traffic.
- **Always a job.** The sync part of the post-attempt pipeline enqueues a `diagnose` job (§11). The submit request never calls the diagnoser.

### 5.2 `DiagnosisContext` (assembled deterministically; hash recorded)

**Current attempt:**
- item prompt, reference solution, rubric summary, trace contract;
- learner answer;
- the full blind grade: criteria, `local_analysis_md`, first divergences, error types, targets, `validity_scope`, `repaired_traces`.

**Failure history (≤ `history_error_limit`, default 6):**
- Prior attempts with any non-pass, on the same LO or on graph-neighbor LOs (prerequisite / confusable edges, one hop), whose facets overlap the current targets. **Any surface family.**
- Each rendered from its *blind-grade-equivalent* fields only: date, surface group, score, failed criteria, first-divergence quote, error type, assisted/primed flags.
- Legacy joint-graded attempts are rendered through the same projection, so their embedded causal fields are **stripped** (S3).

**Success history (≤ `history_success_limit`, default 4):**
- Prior passes on the same facets, from `facet_evidence_timeline.facet_evidence_timelines` (`learner/facet_evidence_timeline.py:828`; `TimelinePoint` carries attempt id, demonstrated capabilities, assisted/primed, surface group).
- Cold and unassisted first.
- This keeps the diagnoser from seeing only failures and over-diagnosing gaps.

**Prior hypotheses:** active `causal_hypotheses` for the LO, open `unresolved_cause_factors`, and durable `misconceptions`. Each is typed: id, statement, scope, status, validated evidence count, last-updated. No prose from past diagnoses.

**Registry candidates:** durable misconceptions plus holding-pen candidates for the LO and `confusable_with` neighbors — today's scope (`misconceptions.py:54-78`). From S1.4a, this adds the kNN shortlist over the whole vault registry (§9.4), in every history mode. `full` and `snapshot` also show the complete registry for the neighborhood LOs.

**Prerequisite neighborhood:**
- The LO's prerequisites (`LearningObject.prerequisites`, `vault/models.py:330`, plus `prerequisite` edges), with ids and titles.
- Your status on each prerequisite facet from `learner/capability_grid.capability_grid` (`:108`): Demonstrated / Ready / untested.

**Repair history:** repairs tried on these facets (from repair-class rows) and their cold-verification outcomes (`causal_factor_deferral.apply_cold_verification_to_factors` results).

**History modes (`diagnosis.history_mode`).** The blocks above are selected in one of four ways. Every mode applies the same as-of cutoff and closed-world validation, and S3 holds in all of them: blind-grade fields and typed hypotheses only, never prior diagnosis prose.

| Mode | Failure and success history | Other blocks | M1 arm |
|---|---|---|---|
| `exact` | ≤ `history_error_limit` failures and ≤ `history_success_limit` successes, chosen by the exact filters above, most recent first | as above | (b) |
| `full` | **Every** prior attempt on the LO and its one-hop graph neighbors (prerequisite and confusable), failures and successes, any surface family. **No facet-overlap filter:** the model judges relevance. Rendered chronologically with explicit timestamps; failed attempts include the learner's answer text | all prior hypotheses, factors, and registry entries for those LOs, plus the repair history | (d) |
| `snapshot` | The `exact` context inline, plus read-only file access to an as-of export of the typed history (§5.6) | as above | (e) |
| `hybrid` | `exact` ∪ kNN over the vault, fused by reciprocal rank (§9.4) | as above | (c) |

**Rules for `full`:**
- **Budget.** `diagnosis.full_history_token_budget` defaults to 100,000 tokens. Needle recall stays near ceiling up to ~100K and degrades sharply beyond it (sweep §1: 2605.12366, 2510.05381).
- **Truncation.** Oldest attempts drop first; prior hypotheses are never dropped before attempts. Dropped counts are disclosed in the context.
- **Layout for caching.** The stable part (neighborhood, registry, chronological history) comes first and the current attempt last, so consecutive diagnoses on one LO reuse the provider's prompt cache (2601.06007).

**Every mode except `exact` adds a recite-first rule.** The diagnoser writes `evidence_attempt_ids` (§5.3) before `analysis_md`. Reciting evidence before answering partly offsets length degradation (2510.05381), and it makes "references to history that doesn't exist" countable (§5.4).

The `exact` and `hybrid` modes keep a fixed token budget with deterministic truncation: oldest first within each block, with the counts of dropped items disclosed in the context.

**As-of cutoff (needed because diagnosis is async).** A backed-up queue can diagnose attempt N after attempts N+1… exist.
- Attempt history is restricted to attempts completed **before** the diagnosed attempt, so no future answers are shown.
- Hypothesis, factor, and registry records are restricted to those whose source attempt precedes it.
- Their *status* is read as of job start, because status history is not versioned. The receipt records `context_as_of_attempt_id` and `lagged_attempts` (how many later attempts existed when the job ran), so any lag is visible.
- Replay never re-assembles the context: it reads the ledger (S7). The receipt is the audit record of exactly what was shown.

**The diagnoser may see the repair chain's source attempt.** Judging whether a repair held requires it. Blinding constrains the grader only (§10).

### 5.3 `DiagnosisProposal` output

```
evidence_attempt_ids[]           # written FIRST in full/snapshot/hybrid modes: the prior attempts relied on (§5.2)
analysis_md                      # written first in exact mode, otherwise second: explanation across time
event_diagnoses[]:               # one per grader error_attribution (keyed by index + first_divergence id)
  causal_class                   # learner_state | transient_execution | unknown
  candidate_causes[]             # CandidateCause (ai/schemas.py:156), unchanged schema
  misconception_statement, misconception_consistent_answer
  operation                      # mechanism slug
  causal_confidence              # model-reported; receipt only (never used in computation, as today)
  postdictive_claims[], soft_postdictive_claims[]
  registry_match                 # {kind: durable|candidate|new|abstain, id?}  — replaces misconception_match
  history_changed_cause          # bool + note: "the prior hypothesis does not explain this trace"
repair_suggestions[]             # instructional fields (§4.2); optional repaired_trace_id reference
pattern_claims[]:                # shadow in S1
  hypothesis_ref                 # index into candidate_causes or an existing hypothesis id
  relation                       # same_mechanism | same_prerequisite_gap | disconfirming
  cited[]: {attempt_id, quote}   # verbatim quote from that attempt's learner answer
  counterevidence_attempt_ids[]  # successes the claim must explain away
prerequisite_gap_hypotheses[]:   # shadow in S1
  prerequisite_ref               # LO or facet id — must come from the provided neighborhood
  cited_attempt_ids[], demonstrated_counterevidence_ids[]
  suggested_discriminator_md     # a cheap probe on the prerequisite that would test it
abstentions[]
```

### 5.4 Validators (deterministic; failures are recorded in `validation_report_json`, not silently dropped)

- **Closed-world ids.** Every attempt, hypothesis, registry, LO, and facet id must appear in the `DiagnosisContext`. In `snapshot` mode, ids present in the exported snapshot count as well (§5.6). Unknown ids are rejected and counted in `validation_report_json.unknown_id_count`, which serves as the per-arm "invented history" metric in M1.
- **Evidence ids.** Every `evidence_attempt_ids` entry must be a known attempt id. Each cited attempt in `pattern_claims` should appear in `evidence_attempt_ids`. A miss is recorded, not rejected.
- **Verbatim quotes.** Each `cited[].quote` is re-anchored against that attempt's `learner_answer_md`, reusing the first-divergence re-anchoring (`grading.py:979-1047`). If it fails, the citation is dropped.
- **Citation validity (S4).** A citation counts toward recurrence only if the cited attempt's blind grade:
  - has a non-pass criterion or an error attribution whose targets overlap the hypothesis's `target_ref` / facets; and
  - has `validity_scope = valid_measurement`.

  Validated citations are grouped by `surface_group_id` (`canonical_projection.py:167`) for independence.
- **Passed-facet firewall** (causal-attribution §1.5) applies to diagnoser targets exactly as to grader targets.
- **Scope firewall.** A `causal_class` on an event whose grader `validity_scope ≠ valid_measurement` is rejected.
- **Repair validation.** `validate_repair_candidate` and a `repaired_trace_id` existence check.
- **Registry match.** The id must be in the provided candidate list; `new` requires a statement; `abstain` is always allowed.

### 5.5 Anti-anchoring rules

- **History-free baseline.** The grader's `local_analysis_md` and first divergence are a history-free reading of the same trace, produced blind at no extra cost.
- **Divergence as a signal.** When the diagnoser's primary cause is not supported by that local reading, `history_changed_cause=false`, and a prior hypothesis is reused, the diagnosis receipt records `anchoring_suspect=true`. The rate is an E2 metric (§13).
- **Prompt instruction.** "Explain this trace first; history can support or contradict a hypothesis, never replace evidence in this trace."
- **Revert path.** If E2 fails, `history_mode = "exact"` with `history_error_limit=0` restores a history-free diagnoser. The split itself is unaffected. E2 is reported per history mode, because a longer history may anchor more.

### 5.6 `snapshot` mode (M1 arm (e))

**Purpose.** The diagnoser explores the history itself with plain file tools, instead of LearnLoop choosing what it sees. This is test-time compute over the store (Recursive Language Models; "Is Grep All You Need?", sweep §1). It targets aggregation across many traces, which single-pass long context handles poorly (Oolong; PRAGMA).

**Export.**
- **What is exported.** At job start, the assembler writes an as-of snapshot of the **whole vault's** typed history (not only the LO neighborhood) into a per-job scratch directory outside the vault:
  - `attempts/<completed_at>_<attempt_id>.md`: the item stem, the learner answer, and blind-grade-equivalent fields, rendered with the §5.2 projection. Legacy causal fields are stripped (S3).
  - `hypotheses/<id>.md`: typed records with status and evidence counts.
  - `registry/<id>.md`
  - `graph/learning_objects.md`: titles, prerequisite and confusable edges.
  - `repairs/<facet>.md`: repair classes with their cold-verification outcomes.
  - `INDEX.md`
- **What is excluded.** The same as-of cutoff applies (§5.2), and nothing after the diagnosed attempt is written.
- **Size.** At ~10³ attempts a year the export is on the order of a megabyte.

**Transport.**
- New capability `READ_ONLY_WORKSPACE` in `ai/transport.py`. `StructuredRequest` gains an optional `workspace: Path | None`.
- The Codex SDK client honours it by starting the thread with `cwd=workspace` in Codex's read-only sandbox with no network. Today every thread starts with `cwd=vault_root` (`ai/providers/codex.py:282-308`). The snapshot workspace **replaces** that directory and is never added alongside it, so the diagnoser cannot read the live vault or later attempts.
- Providers without the capability report it as unsupported, and the mode is unavailable. M1 then skips arm (e) and the report says so.

**Bounds and receipts.**
- The job runs under the existing request timeout and `model_call_budgets`.
- `retrieval_json` records:
  - the snapshot manifest hash and file count;
  - the files the agent opened, when the transport reports them;
  - otherwise only `evidence_attempt_ids`.
- The scratch directory holds learner text, so it is deleted when the job finishes, whether it succeeds or fails.
- Replay never re-runs a snapshot diagnosis (S7).

**Validation is unchanged.** Ids the agent cites must exist in the snapshot, and S4 citation validity applies exactly as in the other modes.

---

## 6. Persistence and versioning

### 6.1 Migration `166_blind_grading_diagnosis_split.sql`

| Table | Role (`db/table_roles.py`) | Contents |
|---|---|---|
| `attempt_diagnoses` | RAW_LEDGER | `id`, `attempt_id`, `agent_run_id`, `diagnosis_prompt_version`, `provider`, `model`, `mode` (`shadow`\|`live`\|`legacy_view`\*), `status` (`completed`\|`failed`\|`skipped`\|`validation_rejected`), `proposal_json` (validated), `validation_report_json`, `supersedes_id`, `created_at`. Append-only; re-diagnosis appends with `supersedes_id` (the regrade pattern) |
| `diagnosis_context_receipts` | RECEIPT | `diagnosis_id` (unique), `context_hash`, `failure_attempt_ids_json`, `success_attempt_ids_json`, `hypothesis_ids_json`, `registry_candidate_ids_json`, `prerequisite_refs_json`, `retrieval_json` (history mode, context tokens, embedding `model_id`, per-item scores and ranks, exact-vs-kNN provenance, dropped counts, snapshot manifest hash and opened files), `anchoring_suspect`, `validated_citations_json` |
| `embedding_vectors` | WORKFLOW | §9.2. Not DERIVED: it cannot be rebuilt without a paid external call, and replay must not re-embed. Not RAW_LEDGER: it is not evidence |
| `diagnosis_feedback` | RAW_LEDGER | M2 diagnosis-card taps (§12.2): `id`, `diagnosis_id`, `attempt_id`, `response`, `cited_attempt_id`, `shown_at`, `responded_at`. Eval-only; confers no support authority |
| `post_attempt_jobs` | WORKFLOW | `id`, `attempt_id`, `kind` (`diagnose`\|`embed`), `state` (`queued`\|`leased`\|`done`\|`failed`\|`skipped`), `attempt_count`, `lease_owner`, `lease_expires_at`, `not_before`, `last_error`, `payload_json`, `created_at`, `updated_at`. `UNIQUE(attempt_id, kind)` for `diagnose`. The lease/fencing pattern is `reader_background_requests` (`migrations/093`) |
| `diagnostic_augmentation_receipts` | RECEIPT (existing, migration 144) | `ADD COLUMN grader_mode TEXT` (`joint`\|`blind`); null reads as `joint` |

\*`legacy_view` is never stored. It labels diagnoses synthesized on read for pre-split attempts (§6.3).

Following `CLAUDE.md`: upgrade and rename `fixtures/migration_head_165/` → `migration_head_166`, and update the five references:
- `tests/test_rebuild_orchestrator.py:25`
- `tests/test_shadow_rebuild.py:20`
- `tests/test_migrations.py:79`
- `docs/learnloop-architecture-vault/_scripts/db_validate_reference.py:39`
- `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py:40` (plus the string at `:1536` and the docstring at `:8`)

### 6.2 Algorithm version

- Split changes persisted meaning: `error_events` no longer carries causal fields, and hypotheses are sourced from the diagnosis ledger. So it gets a new successor, `DIAGNOSIS_SPLIT_ALGORITHM_VERSION = "mvp-0.10"`, in `algorithm_versions.py`, added to `P0_SUCCESSOR_VERSIONS` (the projection semantics are otherwise inherited).
- **The version, not a free config flag, gates split behaviour.** Vaults below `mvp-0.10` run joint grading (optionally with the diagnoser in shadow); vaults at `mvp-0.10` run split.
- Upgrade follows `docs/algorithm-change-playbook.md`:
  - an explicit upgrade function;
  - a default-fingerprint update;
  - table-role classification;
  - replay-completeness and rebuild-equivalence tests;
  - a shadow rebuild on a copied DB;
  - a head fixture exercising the predecessor → successor path.

### 6.3 Legacy adapter and replay

- **`diagnosis_for_attempt(repository, attempt_id)`** is the single read path. It returns:
  - the latest non-superseded `completed` live diagnosis if one exists;
  - otherwise, for joint-graded attempts, a **legacy view** synthesized from `error_events.repair_plan` + `attempt_feedback_metadata.repair_suggestions`, using the §4.2 mapping in reverse, with `mode='legacy_view'`;
  - otherwise none.
- **`replay_existing_attempt`** (`attempts.py:968-1048`) rebuilds `GradeAttribution` local fields from `error_events` (unchanged) and causal fields from `diagnosis_for_attempt`.
- **Materialization under replay.** `materialize_causal_episode`, when re-run under `replace_existing=True`, reads the same source.
- **Replay makes no LLM or embedding calls** (S7).
- **Required equivalence (acceptance):** on every tracked fixture vault, a same-version rebuild before and after S1.1 produces an identical semantic projection. Joint vaults must be byte-identical, because the legacy view is exact.

---

## 7. Pipeline relocation

**1. In-transaction materialization is gated.**
- In split vaults, `_apply_attempt_in_transaction` (`attempts.py:1610-1658`) stops calling `materialize_causal_episode`. There are no candidate causes or instructional repairs at that point.
- The canonical projection still opens nothing causal from `error_events`: `_open_candidate_causes` (`canonical_projection.py:439-501`) and `_sync_unresolved_cause_factors` (`:1120-1150`) read candidate causes through `diagnosis_for_attempt`.

**2. `run_post_attempt_pipeline` (`post_attempt.py:73-146`) splits into a sync part and a worker part.**
- **Sync (submit request) — grade-dependent steps only:**
  - `record_cold_verification_from_task` and `auto_classify_pinned_probe`: both certify or classify from the grade;
  - `sweep_machine_checks`;
  - the grade-keyed `evaluate_intervention_followup` (`followups.py:153-450`);
  - enqueueing the `diagnose` job.
- **Worker — diagnosis-dependent steps, after the diagnosis is persisted:**
  - `materialize_causal_episode`, with the diagnosis as its source;
  - `normalize_and_resolve_attempt` (`misconceptions.py:523-653`, which already re-materializes post-transaction today);
  - `sweep_machine_checks` again, since new factors may lack repair mappings;
  - `_consult_common_repair` (`followups.py:789-865`).
- **`_run_causal_orchestrator_hooks`** (`followups.py:686-786`) is split along the same line. Its never-raise behaviour is kept in both halves.

**3. `misconception_match` is retired in split vaults.**
- `normalize_attempt_misconceptions` (`misconceptions.py:154`) takes `registry_match` from the diagnosis instead of calling `_match_misconception` (`:97-138`).
- A failed diagnosis falls back to the existing deterministic path: exact normalized statement.
- **Net LLM calls per erroring attempt:** before, 1 grade (×k) + one `misconception_match` per misconception event; after, 1 grade (×k) + 1 diagnosis.

**4. Resumability.**
- Enqueueing the job is the last sync step recorded in `attempt_completion_work`, and `_resume_saved_completion` (`practice.py:718-743`) re-enqueues it if the process died before that step.
- After that, the job queue's leases own recovery (§11).

**5. The grade-keyed follow-up is unchanged and runs synchronously.** `evaluate_intervention_followup` keys on grader-owned fields (surprise, severity, failed facets, `grader_confidence`), so the live next-action channel (`scheduler.py:1115-1214`) works before, and without, a diagnosis.

**6. The `recurrence_key` seam (behaviour-neutral).** Add `recurrence_key(hypothesis) -> str` to `diagnosis/causal_factor_deferral.py`. In this slice it returns `statement_normalized`. Route every site that groups hypotheses by exact statement through it:
- `db/repositories.py`:
  - `_projected_causal_candidates` (`:2360`);
  - `misconception_candidate_by_normalized` (`:2489-2516`);
  - the projected-candidate filter (`:2541-2548`);
  - the misconception sync (`:2674-2691`);
  - the `causal_hypotheses_for_learning_object` statement filter (`:14216-14253`).
- `diagnosis/causal_factor_deferral.py`: `_factor_signature` / `_signature_hypotheses` (`:267-298`), and the recurrence count in `sweep_promotion_blocking_factors` (`:347+`).
- `tutor/durable_promotion.py`: `:183`, `:214`, `:294`, `:508`.
- `diagnosis/error_hunt.py`: `:463`, `:476`.

Correctness gate C1 (rebuild equivalence) covers the change. Slice 2 T1 then swaps the function's body for a recurrence-group id.

---

## 8. Router consumption

| Signal | Source | S1 authority | Consumer |
|---|---|---|---|
| Blind grade (criteria, targets, severity, error type) | grader | **live** (as today) | mastery/facet projection, follow-ups, scheduler |
| Candidate causes, `causal_class`, postdictive claims | diagnoser | **live** (replaces grader-sourced) | `materialize_causal_episode` → `causal_hypotheses`, factors, receipt |
| Repair suggestions | diagnoser | **live** | `select_minimal_repair`, repair classes, guided redo (`guided_redo.py:78/308`), reveal budget (`handlers/feedback.py:99`) |
| `registry_match` | diagnoser | **live** | misconception normalization / promotion (promotion rules unchanged: ≥2 independent surface groups or a probe reproduction, `misconceptions.py:302-355`) |
| Validated-citation recurrence count | validator | **shadow** | logged next to `_factor_signature` exact counting (`causal_factor_deferral.py:267-298`); K=3 still uses exact counting |
| `pattern_claims` | diagnoser | **shadow** | receipt + inspector only |
| `prerequisite_gap_hypotheses` | diagnoser | **shadow** | receipt + learner review feed (`learner_review_feed._working_hypotheses`, `learner/learner_review_feed.py:239`) marked "hypothesis"; no route exists yet (Slice 2) |
| History mode (`exact` / `full` / `snapshot` / `hybrid`) | config, chosen from the M1 report | **context only** (never evidence) | `DiagnosisContext` assembly. `hybrid`'s kNN set goes live only if M1/E6 shows it clearly beats `full` |

**What appears immediately vs after diagnosis.**
- **Immediately (grader-owned):** the feedback bundle (`serializers.py:809`) shows the grade, the local feedback, and the grader's repaired trace (the corrected version of your answer).
- **After diagnosis:**
  - repair suggestions and the guided-redo entry point (`guided_redo.py:78/308`);
  - the diagnosis summary;
  - any probe offer or common-repair card from the orchestrator.

  They appear when the diagnosis completes; the UI polls for them (§11).
- **Reveal accounting.** Reveal accounting for repair displays (`answer_reveal_budget`, `handlers/feedback.py:99`) is recorded when the repair is displayed, not when the attempt is submitted.
- **Failed diagnosis:** the repair-suggestion area stays empty and guided redo is unavailable for that attempt.

---

## 9. Embedding substrate

### 9.1 Provider

- **Interface (model-agnostic).** New `ai/embedding.py` defines an `EmbeddingClient` protocol:
  - `model_id`, `dims`, `modalities` (e.g. `{"text"}` or `{"text", "image", "pdf"}`), `max_input_tokens`;
  - `embed(inputs: list[EmbedInput], task_prefix: str) -> list[vector]`, where `EmbedInput` is text or `(mime_type, bytes)`.

  Everything downstream (store, retrieval, jobs) depends only on this protocol and on `model_id`. Later implementations need no schema change:
  - a local open-weight model behind an optional `[embeddings-local]` extra;
  - an OpenAI-compatible `/embeddings` endpoint (the `openai` SDK is already a dependency).
- **One implementation in this slice (revised 2026-10-11).** Forty M1 items cannot separate several embedding models, and the model choice matters only if kNN beats the `full` history mode at all. Sending learner text to an embedding provider is acceptable (owner, 2026-10-11). So Slice 1 builds one API client and uses one model:

| Client | Module | Model | Notes |
|---|---|---|---|
| OpenAI-compatible | `ai/providers/openai_embedding.py`, on the existing `openai` SDK (`pyproject.toml:20`). It reuses the `openrouter` profile's base URL and `OPENROUTER_API_KEY` (`ai/providers/openrouter.py:7-8`) | `qwen/qwen3-embedding-8b` via OpenRouter (4096-d; MRL truncation; instruction-prefixed queries; $0.01 per million tokens) | It was the top MTEB-multilingual model at release, which gives kNN its fairest test in M1. Backfilling the owner's whole history costs cents. Requests set OpenRouter's `provider.data_collection = "deny"`. `input` is batched as an array |

  **Switching models is a config change.** The same client reaches every OpenRouter embedding model, for example `google/gemini-embedding-2` (also accepts images), `openai/text-embedding-3-large`, and `qwen/qwen3-embedding-4b`.

  **Deferred to Slice 2:**
  - the B1/B3 model comparison, which runs through this same client;
  - an optional local sentence-transformers client for offline use;
  - page-image input for T6/B4. This uses Gemini Embedding 2's image input through OpenRouter, or a direct Gemini client if PDF pages need it.

  The `EmbeddingClient` protocol stays model-agnostic, so later clients need no schema change. Dimensions are stored per `model_id`, and MRL models may be truncated per consumer (§9.2).
- **Default model.** `qwen/qwen3-embedding-8b` until Slice 2 B1 (Eedi) and B3 (vault replay) compare the candidates. A model change fully re-embeds the affected record kinds before retrieval switches (§9.6). A partially re-embedded index recovers far less than a full re-embed (2609.05339).
- **Capability.** New constant `EMBEDDING` in `ai/transport.py:18-23`.
- **Routing.**
  - New `AITask` `"embedding"` (`ai/routing.py:18-29`) with **no fallback to `active_provider`**, the same opt-out as `canonical_ingest_retry` (`:116-117`); otherwise it would resolve to codex.
  - New `AITask` `"diagnosis"` with its own `ai.routing.diagnosis` field, defaulting to the resolved grading provider when unset. The diagnoser can be moved to a different or stronger model by config alone.
- **Config.**
  - New profile class `type: "openai_embedding"` in `config/schema.py` (union at `:953-959`), subclassing `OpenAICompatibleProviderConfig` like `OpenRouterProviderConfig` (`:947`), with a factory branch in `ai/client.py:35-57`.
  - Readiness branch in `ai/runtime.py:105-115`, keyed on the profile's API-key env var (`OPENROUTER_API_KEY` for the default).
  - Update `config/template.py:517-573` and `learnloop_sidecar/handlers/settings.py`.
- **Receipts.** Each request is wrapped in `model_call(purpose="embedding")` with `report_call_usage`, so embedding spend appears in `model_call_receipts` and budgets (migration 165).
- **Task prefixes.** Every client accepts only coarse task prefixes: retrieval-document, retrieval-query, similarity. Each client maps them to its model's convention: Qwen3 instruction-prefixed queries, Gemini Embedding 2 in-prompt instructions, and none for `text-embedding-3-small`. FollowIR (NAACL'25) shows retrievers ignore nuanced instructions.

### 9.2 `embedding_vectors`

- Columns: `id`, `record_kind`, `record_id`, `field`, `content_hash`, `model_id`, `task_prefix`, `dims`, `vector` (BLOB, float16), `created_at`.
- `UNIQUE(record_kind, record_id, field, model_id, task_prefix, content_hash)`.
- Search is exact brute-force in numpy per query, with no ANN index; at 10⁴–10⁵ vectors × 1–3k dims this takes milliseconds.
- Vectors are **mean-centered per vault × record_kind × model at query time** (derived, cheap). No PCA whitening: it hurt every model tested in arXiv 2511.11041.

### 9.3 What gets embedded in S1 — always LLM-written or canonical text, never raw responses alone

| `record_kind` / `field` | Text | Why | Embedded when |
|---|---|---|---|
| `attempt` / `divergence` | item stem + first-divergence quote + grader `local_analysis_md` excerpt | Retrieval of similar failures. Local analysis rather than the raw answer, because problem content dominates raw response embeddings (Borchers et al., LAK'26) | M1 arm (c); live only when `history_mode = "hybrid"` |
| `hypothesis` / `statement` | candidate-cause statement + mechanism slug | Would-merge recurrence log. Generate → retrieve → rerank (Mitton et al., L@S'26; Eedi 2024 winners). This is candidate blocking for an O(n²) "same cause?" comparison, the use the 2026-10-11 review keeps | always when `embedding.enabled` (S1.4a) |
| `misconception` / `statement` | durable + holding-pen statements | Registry shortlist beyond the LO/confusable scope | always when `embedding.enabled` (S1.4a) |

- **Embed-on-write** happens at the end of the post-attempt pipeline, best-effort. Failures enqueue a retry in a small WORKFLOW backlog, reusing the `reader_background_requests` lease pattern (`migrations/093`, `jobs.py:3548-3598`); they never block the attempt.
- **Backfill:** `learnloop embeddings backfill --vault` embeds existing records. It is idempotent via `content_hash`.

### 9.4 Retrieval (`diagnosis.history_mode = "hybrid"`; M1 arm (c))

For each context block:
1. Take the exact-filter candidate set (§5.2).
2. Take the kNN set over the vault, with filters applied *before* ranking: same or neighbor LO, facet overlap, `validity_scope = valid_measurement`, excluding the current attempt.
3. Fuse by reciprocal rank and keep the top N.

Both sets and all scores go to `diagnosis_context_receipts.retrieval_json`. Structured constraints ("facet A and B but not C") stay in SQL, never vectors (LIMIT, ICLR'26).

Hubness is monitored with the k-occurrence skew, reported by `learnloop doctor`.

### 9.5 Shadow recurrence would-merge log

When a hypothesis is minted, record its nearest prior hypotheses for this learner (facet-filtered) with cosine and rank, next to the exact-key group. Stored in `diagnosis_context_receipts.retrieval_json` under `would_merge`.

This produces E5's labelled pairs. Every later LLM or owner adjudication of "same cause?" is logged as a labelled pair; the calibrator itself is Slice 2.

### 9.6 Privacy and failure

- **Disclosure.** Embeddings approximate plaintext (vec2text EMNLP'23; vec2vec NeurIPS'25). `embedding_vectors` gets the same backup/export/sync policy as `practice_attempts`. It is never exported into cross-vault stores.
- **Config.**
  - `embedding.enabled` defaults to **false** in the template for new vaults.
  - The owner vault enables it (owner decision, 2026-09-30) with `qwen/qwen3-embedding-8b` via OpenRouter (revised 2026-10-11).
  - Learner-derived text (divergence excerpts, hypothesis statements, registry statements) is sent to OpenRouter and its upstream provider. The owner accepted this on 2026-10-11. The settings UI and `learnloop config effective` still state it, because new vaults may not want it, and requests ask OpenRouter to route only to providers that don't retain data (`data_collection = "deny"`).
  - Local models carry no disclosure.
- **Failure.** With the provider unconfigured or failing, `hybrid` silently degrades to `exact`, and the receipt records `method="exact_fallback"` (S6). `full` and `snapshot` do not use embeddings.
- **Model change.**
  - `embedding.model` selects the active `model_id` for retrieval.
  - Switching models runs `learnloop embeddings backfill` under the new id while the old vectors stay. Retrieval switches only when the backfill for every affected record kind is complete. Partial re-embeds are never used for retrieval.
  - Vectors from different `model_id`s are never compared.
  - Comparing candidate models is a Slice 2 benchmark (`spec_embedding_consumers_v1.md` §3.3, B1/B3).

---

## 10. Cold-verification blinding

`_context_blinding` (`attempts/coldness_receipt.py:1244-1305`):

- **Split vaults:** **pass** iff the cold attempt's grading receipt has `grader_mode='blind'` (C4 history is structurally empty). Otherwise, the existing source-in-history test applies.
- **Joint-graded attempts:** unchanged.
- `prior_diagnoses_in_context` stays `False`.

**New receipt field `diagnoser_saw_source`.** It is informational and expected to be true. Cold verification certifies from the *grade*; the diagnoser's view of the source never enters the verification verdict. `_run_separation` (`:1211-1241`) additionally requires the cold attempt's grader `agent_run_id` to differ from any diagnosis run for the source attempt.

**Why this matters.** Without the new receipt, moving history out of the grader would make this check pass vacuously on joint-mode attempts graded before the column existed. Hence null reads as `joint`.

---

## 11. Asynchronous execution, failure handling, and latency

**Worker**
- One `PostAttemptWorker`, owned by the sidecar context (`learnloop_sidecar/context.py`) and started with the sidecar.
- Built on the `ExamGradingManager` pattern (`learnloop_sidecar/exam_grading.py:20-103`): daemon threads that copy contextvars, so `model_call_receipts` still record.
- Two slots:
  - `diagnose`: concurrency **1**;
  - `embed`: concurrency 1.
- The worker opens its own SQLite connection via `learnloop.db.connection.connect` (WAL + `busy_timeout`). Each job runs in short transactions.
- The sidecar treats lock errors as non-retryable today, so the worker retries `SQLITE_BUSY` itself with a bounded backoff.

**Ordering**
- `diagnose` jobs run strictly in attempt completion order. Materialization, factors, and registry promotion depend on earlier diagnoses, so job N starts only after job N−1 is `done`, `failed`, or `skipped`.
- `embed` jobs are unordered.

**Queue semantics** (`post_attempt_jobs`, lease-fenced like `reader_background_requests`, `jobs.py:3548-3598`)
- Leases expire, so a crash mid-job leaves the job reclaimable on the next start.
- A failed attempt sets `not_before` with exponential backoff.
- After `diagnosis.max_attempts` (default 5) the job is `failed`.
- If no provider is ready, jobs stay `queued` rather than failing, as reader requests do.
- **Budget.** Diagnosis calls count toward `model_call_budgets`. When the budget is exhausted, the job is `skipped` with reason `budget`; the grade is never skipped.

**The router tolerates a late diagnosis**
- **Next action never needs a diagnosis to exist.** The scheduler's live channel runs on the grade-keyed follow-up (§7.5).
- Diagnosis-driven decisions for attempt N enter through the existing mechanisms whenever the job completes: hypotheses, factors, the orchestrator's common-repair/probe decisions, and pending follow-ups inserted at the head of the queue (`scheduler.py:165,507`).
- **Bounded wait for fast clicks.** When the learner requests the next item while a `diagnose` job for an attempt in the current session is queued or running, the next-item handler waits up to `diagnosis.next_item_wait_seconds` (default 10) on a completion event, like `wait_for_session`. It then proceeds regardless.
- A pick served without the latest diagnosis records `served_without_diagnosis=true` and the pending attempt id in its scheduling receipt, so the lag rate is measurable (E7).
- Usually the diagnosis finishes while you read the feedback, and no wait happens.

**UI**
- `submit_attempt` returns `diagnosis_status` (`pending` | `not_needed` | `done` | `failed`).
- New RPC: `diagnosis_status(attempt_id)` returns the status plus, when done, the diagnosis summary and repair suggestions (serialized as the feedback bundle serializes them today).
- The feedback view polls every 2–3 s while `pending` — the same polling pattern as `TodayScreen.tsx:341-363`. It shows a small "analyzing your pattern" placeholder in the repair area and fills it in place.
- Changes live in the Tauri frontend feedback view and `learnloop_sidecar/handlers/feedback.py` / `serializers.py`.

**CLI and TUI**
- `learnloop attempt` runs the diagnose job inline after printing the grade. There is no daemon in the CLI.
- `--no-diagnose` only enqueues the job.
- `learnloop diagnose --drain --vault` processes the queue.
- The TUI (`tui/screens/feedback.py`) runs inline and shows the diagnosis when it finishes.

**Diagnosis failure** (provider down past retries, timeout, validation rejected):
- the attempt is still complete and graded;
- `attempt_diagnoses.status='failed'`;
- no causal episode is materialized;
- follow-ups run on the grade;
- `learnloop doctor` lists failed and stale jobs;
- `learnloop diagnose --attempt <id>` retries.

Router behaviour is then identical to today's attempts that carry no candidate causes.

**Latency**
- Submit latency should **drop** relative to today: the blind prompt is shorter, and the `misconception_match` calls leave the request path.
- E7 measures:
  - grade-call and submit p50/p95;
  - diagnosis completion time after submit;
  - the `served_without_diagnosis` rate.

---

## 12. Rollout

Configuration surface:

```toml
[diagnosis]
history_mode = "full"             # exact | full | snapshot | hybrid; set from the M1 report (§12.1)
                                  # snapshot needs a READ_ONLY_WORKSPACE provider (§5.6); hybrid needs embedding.enabled
full_history_token_budget = 100000
history_error_limit = 6           # exact / snapshot (inline part) / hybrid
history_success_limit = 4
sample_count = 1
correct_answer_sample_rate = 0.0
shadow = false                    # joint vaults only: run the diagnoser in shadow alongside the joint grader
next_item_wait_seconds = 10
max_attempts = 5

[embedding]
enabled = false                   # template default; owner vault: true
profile = "openrouter_qwen3_8b"   # the only Slice 1 model; Slice 2 B1/B3 may change it
dims = 1024                       # MRL truncation where the model supports it

[ai.providers.openrouter_qwen3_8b]
type = "openai_embedding"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
model = "qwen/qwen3-embedding-8b"
data_collection = "deny"          # OpenRouter provider routing
# any OpenRouter embedding model works here, e.g. "google/gemini-embedding-2"

[ai.routing]
# diagnosis = "<profile>"         # unset → resolved grading provider
embedding = "openrouter_qwen3_8b" # = embedding.profile
```

**Principle: build just enough to learn whether the direction works.** The riskiest assumption is not the plumbing. It is whether a history-aware diagnoser gives explanations the learner recognizes as more accurate, and finds real cross-problem patterns. That is tested first, offline, on existing history (M1). Live plumbing (M2) is built only after M1 says the direction is worth it.

| Milestone | Build | Learner does | Decides |
|---|---|---|---|
| **M1 — Offline review** (no live change, no vault migration) | S1.0 harness, plus: `DiagnosisProposal` + context assembler (all four history modes) + validators; the blind grading prompt; `learnloop diagnose --dry-run` into a scratch DB; the OpenRouter embedding client with `qwen/qwen3-embedding-8b`; the `snapshot` export and the Codex `READ_ONLY_WORKSPACE` capability (§5.6); `learnloop diagnose review` (§12.1) | ~40 past wrong answers, blinded and shuffled (~1.5–2.5 h with five arms, split across sessions) | Whether to build M2 at all; **which history mode M2 uses**; whether the blind grader is ready, including the valid-alternative and real-vs-synthetic probes; whether pattern links are trustworthy enough to pursue M3 |
| **M2 — Live split + diagnosis card** | S1.1 (contracts, ledger, migration 166, queue/worker, `recurrence_key` seam) → S1.3 (split cutover, with the M1-chosen history mode; default `full`) → S1.4a (hypothesis and registry embeddings + would-merge log) → S1.4b (kNN diagnosis context, **only if M1 chose `hybrid`**) → diagnosis card (§12.2) | Normal study for ~2 weeks; one optional tap per diagnosis | Whether in-flow diagnoses hold up; whether async feels fine; whether to proceed to Slice 2 T1 (M3) |
| **M3 — Recurrence with authority** | Slice 2 T1 (`spec_embedding_consumers_v1.md`) | Sees escalated repairs with their evidence; rates usefulness | Whether recurrence-driven repair is worth the rest of Slice 2 |

The S-steps below remain the engineering breakdown. The in-app shadow step S1.2 is **dropped**: M1 answers its questions sooner and without live traffic.

| Step | Contents | Behaviour change | Gate to proceed |
|---|---|---|---|
| **S1.0 Harness** (M1) | Planted cases:<br>• a changed-cause learner (C4's revert control)<br>• paraphrased-recurrence learners<br>• same-answer/different-cause pairs<br>`learnloop diagnose --since/--attempt --dry-run` runs blind grader + diagnoser over historical attempts into a scratch DB (the copied-DB pattern from shadow rebuild) | none | harness runs on fixtures |
| **S1.1 Contracts + ledger + queue** | `BlindGradingProposal`, `DiagnosisProposal`, validators, migration 166, `diagnosis_for_attempt` + legacy view, replay reading both; `post_attempt_jobs` + `PostAttemptWorker` + `diagnosis_status` RPC + UI polling | none (joint vaults byte-identical on rebuild) | correctness gates C1–C6 (§13) |
| ~~S1.2 Diagnoser in shadow~~ | Dropped; replaced by M1. `diagnosis.shadow` remains as an optional tool | — | — |
| **S1.3 Split cutover** (M2) | Vault upgrade to `mvp-0.10`; blind grader + live async diagnoser with the M1-chosen `history_mode` (default `full`); `misconception_match` retired | yes | M1 report reviewed (E1–E4, E6); shadow rebuild of the owner vault reviewed |
| **S1.4a Hypothesis embeddings** (M2) | Store, backfill, and embed jobs for `hypothesis` and `misconception` records with `qwen/qwen3-embedding-8b`; would-merge log. `embedding.enabled = true` | none (shadow log only) | — |
| **S1.4b kNN diagnosis context** (M2, conditional) | `attempt/divergence` embeddings and `history_mode = "hybrid"`. **Built only if M1 chose `hybrid`** | diagnosis context uses hybrid retrieval | M1 E6 report |
| **Diagnosis card** (M2) | §12.2 | yes (UI) | — |
| **S1.5 Exit review** (end of M2) | Record baselines; review the M2 signals (§12.3); decide whether to start Slice 2 T1 | — | owner review |

### 12.1 M1 — offline review protocol (`learnloop diagnose review`)

**Sample.**
- About 40 past practice attempts with errors from the owner vault, stratified across LOs and time.
- Plus the harness's planted cases, mixed in unlabelled. They let the report check the reviewer against known truth.

**Candidates per attempt**, generated by `--dry-run` into a scratch DB:
- (a) today's joint-grader diagnosis, as stored;
- (b) the new diagnoser, `history_mode = "exact"`;
- (c) the new diagnoser, `hybrid`, with `qwen/qwen3-embedding-8b`;
- (d) the new diagnoser, `full`: the whole exact-filtered history in long context, capped at `full_history_token_budget`;
- (e) the new diagnoser, `snapshot`: read-only file access to the as-of export (§5.6). Skipped, with a note in the report, when the diagnosis provider lacks `READ_ONLY_WORKSPACE`.

(b)–(e) use the same diagnoser model, prompt, and effort, so only the history mode varies. All four use the blind grade produced by the dry-run blind grader for that attempt.

**What the reviewer sees and records:**
1. **Diagnoses.** The item, the answer, and up to five explanations, with labels hidden and order shuffled. Each gets one tap: **right / partly / wrong / not sure**. Then an optional "best" pick, including "none".
2. **Pattern links.** Each "this looks like the same mistake as [earlier answer]" claim from any arm, shown with both answers side by side: **same mistake / different / not sure**. A link proposed by several arms is shown once, and its verdict is credited to each of them.
3. **Grade disagreements.** Where the dry-run blind grade differs from the stored joint grade: **the blind grade is right / the stored grade is right / not sure**.

Every screen has a skip. With five arms the expected burden is about 1.5–2.5 hours, and the review can be split across sessions (O15).

**Automatic per-arm measures** (no reviewer time):
- **Planted truth:**
  - changed-cause recovery;
  - paraphrased recurrences found;
  - same-answer/different-cause pairs kept apart.
- **Invented history:** `unknown_id_count` per arm (§5.4).
- **Retrieval value, (c) only:** whether any trace that only kNN surfaced was cited, and whether that citation validated (S4).
- **Context-length sweep, (d) only:** planted cases rerun at 25K, 50K, and 100K tokens and at the full budget, to find where quality starts to drop. This sets `full_history_token_budget`.
- **Cost:** tokens (cached and uncached), cost, and latency per diagnosis.

**No embedding-model comparison runs in M1.** It moves to Slice 2 B1/B3 (§9.1).

**Storage.**
- Verdicts on (a) are genuine owner adjudications of real receipts. They are written to the vault's `diagnosis_adjudications` ledger with `adjudicator_source='human_owner'` and `queue_reason='sampled'` (migration 126). This is eval ground truth that survives M1.
- Verdicts on (b)–(e), pattern links, and grade disagreements refer to scratch-DB artifacts. They stay in the scratch DB's `review_judgments` table and are exported with the report as JSON.
- The pattern-link verdicts are later imported into `judgment_ledger` (created in Slice A; Slice 2 §5.8) as the first `same_cause` rows for Slice 2 T1.

**Surface.** A terminal review command. A Tauri screen is not built for M1 (see O13).

**What the M1 report must answer, and what changes the plan:**

| Question | Signal | If the answer is no |
|---|---|---|
| Is the history-aware diagnoser better? | (b)–(e) "right" rate vs (a); "best" picks; the noise floor from a repeat (b′) on a subset | Stop before M2. Iterate the diagnoser prompt/model, or rethink the diagnosis context |
| Which history mode should M2 use? | Paired per-item comparison of (b)–(e) against the (b′) noise floor; confirmed pattern links unique to one arm; the automatic per-arm measures | **Default `full` (d).** Use `hybrid` only if (c) is clearly better than (d), or finds confirmed links that (d) misses. Use `snapshot` if (e) is clearly better than (d). Fall back to `exact` only if (d) is clearly worse than (b). If (c) adds nothing, `hybrid` stays off; Slice 2 then uses embeddings only for blocking, freshness, and source search |
| Are "same mistake" links trustworthy? | Share of links judged "same", per arm | Recurrence authority (M3) is not ready; keep it shadow and improve citation rules |
| Is the blind grader at least as good? | Disagreement verdicts; E1's valid-alternative false-rejection rate and real-vs-synthetic gap (§13) | Prompt work before cutover (S1.3). If valid alternatives are often rejected, add a "re-derive a divergent path before marking it wrong" instruction to the blind prompt before cutover; the full valid-alternative path is Slice 2 §5.5 |

### 12.2 M2 — diagnosis card

Shown in the feedback view when the async diagnosis arrives:
- the diagnosis summary in plain language;
- the repair suggestion or suggestions;
- **"You've made this mistake before"**, listing the validated cited earlier answers with dates. Each opens that answer and its blind grade. The list is omitted when no citation validated.
- the prerequisite-gap hypothesis, if any, marked "possible cause — not yet checked".

**One optional tap, using the existing self-report vocabulary.** `SELF_REPORT_REASONS` (`diagnosis/causal_attribution.py:32-40`) already defines `slipped`, `believed_candidate`, `item_unclear`, `notation_confused`, `other_valid_approach`, and `diagnosis_wrong`. The card offers:

| Button | Recorded as |
|---|---|
| That's it | `believed_candidate` for the primary cause |
| Partly | the card-only value `partly` |
| I just slipped | `slipped` |
| That's wrong | `diagnosis_wrong` |
| Not sure | the card-only value `unsure` |

- The buttons are rendered in a fixed neutral order; the diagnosis is not visually privileged.
- The pattern list has its own "not the same mistake" tap per cited answer.

**Recording.**
- Every tap is written to a new eval-only table, `diagnosis_feedback` (RAW_LEDGER; migration 166): `diagnosis_id`, `attempt_id`, `response`, `cited_attempt_id?`, `shown_at`, `responded_at`.
- `diagnosis_feedback` carries no support authority.
- When the attempt has an **open unresolved-cause factor**, the tap is also forwarded to `record_unresolved_cause_self_report` (`causal_attribution.py:3437`), preserving today's semantics for that existing channel. Whether to forward is **O14**.

**Invariant 12 holds.** A tap is a claim-scoped learner report, never mastery evidence. The eval use of `diagnosis_feedback` is reported separately from owner adjudications.

### 12.3 M2 signals (end-of-M2 review)

| Signal | Source | Suggests reevaluating if |
|---|---|---|
| Card responses | `diagnosis_feedback` distribution over time | "That's wrong" is common, or "not sure" dominates (the diagnoses aren't legible) |
| Pattern-link confirmations | per-citation taps | Cited earlier answers are often "not the same mistake" |
| Repair uptake | guided-redo starts after the card | Repairs are rarely used |
| Async experience | E7: `served_without_diagnosis` rate, diagnosis delay; owner's qualitative note | Diagnoses routinely arrive too late to matter |
| Grade trust | regrade/dispute requests on blind grades vs the pre-split rate | Disputes rise after cutover |

**Rollback.**
- `history_mode`, S1.4a/S1.4b embeddings, and the diagnosis card are config flips.
- S1.3 rolls back by restoring the pre-upgrade vault (the playbook keeps the prior version readable if preparation fails), or by a forward `mvp-0.10 → joint` compatibility decision (**open decision O9**).
- Diagnosis rows written in split mode stay valid ledger records either way.

---

## 13. Evaluation

**Two kinds of check.**

- **Correctness gates** are pass/fail. They are about whether the code does what it claims, not about model quality, so they need no calibration:

| Id | Gate |
|---|---|
| C1 | Rebuild equivalence: same-version rebuild on every tracked fixture is identical before/after S1.1; joint vaults byte-identical |
| C2 | Structural blindness: `BlindGradingContext` has no history-capable field; the rendered blind prompt contains no prior attempt id, trace, or hypothesis (asserted on fixtures) |
| C3 | Replay makes zero LLM and zero embedding calls (fakes assert) |
| C4 | Every validator rule in §5.4 has a rejecting test case |
| C5 | Queue durability: crash mid-job → lease expiry → exactly-once diagnosis row per attempt; ordering preserved; the durability lane passes |
| C6 | Cold-verification blinding reports `pass` for blind grades and is unchanged for joint grades |

- **Quality evaluations are reports, not gates.** There are **no numeric thresholds in this slice**. Nothing yet establishes what size of change matters for this learner, grader, and content, so any threshold now would be a guess. Instead, every comparison report includes a **noise floor**: the same configuration run twice (joint vs joint; diagnoser vs itself with a different seed or sample). A difference counts as "real" only when it is clearly outside the run-to-run variation. The owner reviews each report at the step boundaries in §12. Thresholds are written into a later revision once M1 and M2 have produced baselines.

  Product metrics `S`/`Q`/`F` are monitored, not gated: at n=1 they lack statistical power (plan review, 2026-09-30).

| Id | Question | Report contents | Directional signal to act on (no threshold) |
|---|---|---|---|
| **E1** Blind parity | Does removing history and causal duties change measurement? | Blind vs joint vs joint-repeat on adjudicated anchors (`diagnosis_adjudications` ledger) and planted cases:<br>• criterion-level agreement (κ)<br>• first-divergence anchor accuracy<br>• fatal-error agreement<br>• `GradeFlipRate` under paraphrase<br>**Probes added 2026-10-11** (on ~40 reference-bearing items from the M1 sample):<br>• **Valid-alternative false rejection.** A frontier model writes a correct derivation that differs from the reference, checked by CAS/sympy or the exact key. The blind grader grades it with the reference in context. Report the share wrongly marked down (2608.28725: 75–85% for small models)<br>• **Real-vs-synthetic gap.** The blind grader's error on the owner's real answers where the owner has adjudicated the grade (M1 step 3, or the `diagnosis_adjudications` ledger), vs its error on synthetic responses to the same items whose grades are known by construction (planted errors). A large gap means any grader setting chosen on synthetic data overstates quality (2606.10254) | Blind grader clearly below joint *and* outside the joint-repeat spread → investigate the prompt before cutover. A high false-rejection rate → the valid-alternative instruction before cutover (§12.1). A large real-vs-synthetic gap → no synthetic anchors in Slice 2 (§5.5) |
| **E2** No anchoring | Does history help without locking onto old causes? | Changed-cause recovery per history mode vs no history (`exact` with `history_error_limit=0`) vs repeat; `anchoring_suspect` rate per mode over time | A mode recovers changed causes less often than no-history → don't use that mode; if every mode does, turn history off (the split stays) |
| **E3** Cause quality | Is a dedicated diagnoser at least as good as the joint grader? | `run_planted_diagnostic_evaluation` (`diagnostic_augmentation.py:896`) cause accuracy and repair-class agreement, diagnoser vs joint vs repeat; ConceptKT once plan D0 exists; per diagnoser model when `ai.routing.diagnosis` is varied | Diagnoser clearly worse → keep shadow, iterate the prompt or model |
| **E4** Registry match | Does `registry_match` replace `misconception_match`? | Agreement on replayed events; every disagreement listed for owner/LLM audit | Audited disagreements mostly favour legacy → revisit before retiring `misconception_match` |
| **E5** Recurrence (shadow) | Do validated citations and would-merge find recurrences exact strings split? | On replayed history + planted paraphrase learners:<br>• exact-key splits merged<br>• audited merge precision<br>• false merges on same-answer/different-cause pairs | Any planted false merge → fix before Slice 2 promotion |
| **E6** History mode | Which way of giving the diagnoser its history works best: `exact`, `full`, `snapshot`, or `hybrid`? | Per mode:<br>• whether the planted relevant history (including cross-surface) was **cited**, not just present<br>• E2/E3<br>• `unknown_id_count`<br>• kNN-only citations (`hybrid`)<br>• the context-length sweep (`full`)<br>• tokens, cost, and latency | Per the §12.1 decision rule: `full` unless another mode is clearly better; `hybrid` never by default |
| **E7** Operational | What does the split cost and how late is diagnosis? | Grade/submit p50/p95; diagnosis completion delay; `served_without_diagnosis` rate; calls, tokens, and embedding spend per attempt; job failure rate | Rising `served_without_diagnosis` → raise the wait or diagnose faster |

**When each report is produced:**
- **M1 report** (offline, §12.1): E1 (including the two probes), E2 and E3 per history mode, E4, and E6. The owner's review verdicts are the primary evidence; planted cases supply known truth.
- **End of M2:** E5 and E7, plus the §12.3 learner signals.

The report generator is `learnloop diagnose report --vault <path> [--json]`. It reads the receipts and ledgers and writes a markdown report under `docs/reviews/`.

---

## 14. Tests

**New test files:**
- `test_blind_grading_contract.py`: `BlindGradingContext` has no history-capable field; prompt contains no causal instructions; the §4.2 field mapping; validators.
- `test_diagnosis_contract.py`:
  - closed-world ids;
  - verbatim-quote anchoring;
  - citation validity, including the case where a cited *passed* attempt is dropped;
  - scope and passed-facet firewalls;
  - registry-match validation.
- `test_diagnosis_context.py`:
  - deterministic assembly and hash;
  - successes included;
  - legacy attempts stripped of causal fields;
  - truncation disclosure;
  - repair-chain source visible to the diagnoser.
- `test_diagnosis_history_modes.py`:
  - **`full`:**
    - every attempt on the LO and its one-hop neighbors is included regardless of facet overlap;
    - chronological order with timestamps;
    - the token budget truncates oldest attempts first and never drops hypotheses before attempts;
    - dropped counts are disclosed;
    - the stable prefix is byte-identical across two diagnoses on the same LO, so it can be cached.
  - **`snapshot`:**
    - the export contains no attempt at or after the diagnosed one;
    - legacy causal fields are stripped from the export;
    - the Codex request's `cwd` is the snapshot directory and never `vault_root`;
    - the directory is deleted on success and on failure;
    - the mode is unavailable on providers without `READ_ONLY_WORKSPACE`.
  - **All modes:**
    - S3 holds: no prior diagnosis prose appears in any mode;
    - `evidence_attempt_ids` is validated;
    - unknown ids raise `unknown_id_count`.
- `test_diagnosis_pipeline.py`:
  - post-attempt ordering;
  - materialization sourced from diagnosis;
  - `misconception_match` not called in split vaults;
  - failure → grade-only;
  - resume;
  - budget skip.
- `test_diagnosis_replay.py`: split rebuild equivalence; legacy-view byte equivalence on joint fixtures; no LLM/embedding calls during replay (fakes assert zero calls).
- `test_embedding_store.py`: content-hash idempotence; model-id isolation, including mixed dimensions across models; mean-centering; exact-fallback when disabled; a fake `EmbeddingClient` proves the store and retrieval are model-agnostic.
- Client tests: `test_openai_embedding_client.py`, with a fake `openai` module via `tests/openai_fakes.py`. It checks batching, the OpenRouter base URL and `data_collection` field, dimension truncation, and usage reporting into `model_call_receipts`.
- `test_diagnose_review.py`:
  - deterministic sampling and shuffling (seeded);
  - labels hidden from the rendered screens;
  - skip and resume across sessions;
  - (a)-verdicts land in `diagnosis_adjudications` with the correct `queue_reason` / `adjudicator_source`;
  - scratch-only verdicts never touch the vault DB.
- `test_diagnosis_card.py` (sidecar):
  - taps map to `diagnosis_feedback`;
  - forwarding to `record_unresolved_cause_self_report` happens only with an open factor;
  - the pattern list shows only validated citations.

  Plus a vitest test for the card's button order and pending → filled rendering.
- `test_post_attempt_worker.py`:
  - ordering of `diagnose` jobs;
  - lease expiry and reclaim;
  - backoff and `max_attempts`;
  - provider-not-ready stays queued;
  - budget skip;
  - `SQLITE_BUSY` retry;
  - contextvar propagation so `model_call_receipts` record.
- `test_diagnosis_async_router.py`:
  - next-item bounded wait with the completion event;
  - `served_without_diagnosis` receipt;
  - diagnosis-driven follow-ups appear after completion;
  - as-of cutoff excludes later attempts.
- Sidecar RPC tests for `diagnosis_status`; a vitest test for the feedback view's pending → filled polling.

**Updates to existing files:**
- `test_coldness_receipt.py`: blind-mode pass, `diagnoser_saw_source`, null `grader_mode` = joint.
- `test_diagnostic_augmentation.py`: split-mode sampling fingerprint.
- `test_table_roles.py`, `test_migrations.py`, `test_rebuild_orchestrator.py`, `test_shadow_rebuild.py`: head 166.

**Fakes:** `tests/structured_ai.py` gains a `"diagnosis"` purpose handler; `grading_json()` in `tests/openai_fakes.py` gains a blind variant.

**Durability:** the durability lane (`-m durability`) runs `test_diagnosis_pipeline.py` and `test_diagnosis_replay.py` against production pragmas and fresh vaults.

---

## 15. Document changes

- **Plan invariant 1** (`Pipeline Augmentation Plan.md`) becomes: *"The grading role is learner-blind: no prior traces, grades, diagnoses, hypotheses, or retrieved learner memory. Hypotheses and retrieved memory enter the diagnostician, tutor, and generator roles."*
- **`spec_diagnostic_augmentation_v1.md` §C4:** a disposition note pointing here.
- **Architecture vault:** a user-journey update (the attempt submission flow) and a decision record for the split. The DB reference is regenerated for migration 166.
- **`Embedding Integration Map.md`:** mark Tier 1 #1 and #3 as "Slice 1", #2 as "Slice 1 via registry_match".

---

## 16. Non-goals and Slice 2 candidates

Embedding items below are specified in **`spec_embedding_consumers_v1.md`** (Slice 2).

- **Validated-citation recurrence with K=3 authority.** Promotion depends on the E5 report (Slice 2 T1).
- **A prerequisite-descend route:**
  - one cheap probe on the hypothesized prerequisite before committing;
  - consuming `prerequisite_gap_hypotheses`;
  - through `decide_probe` as a new verb.
- **Grader reference policy for generated practice:** verified references, a valid-alternative path, and solve-first grading for items with no reference. This replaces the former "per-item synthetic anchor sets" plan, which is not built by default (Slice 2 §5.5; E1's real-vs-synthetic probe informs it).
- **Other embedding consumers:** freshness/isomorph gate, leak/reveal detectors, ingest nomination, knowledge-map neighbors.
- **The would-merge calibrator** fit from logged adjudications.
- **Learner success prediction** over frozen embeddings (Integration Map #10).
- **A full `LearnerStateCardV1` projection.** `DiagnosisContext` is its first consumer and a prototype of its content.
- **Fixing divergence classification to use `repair_equivalence_id`** instead of `repair_class_id`, which hashes model-reported `expected_minutes` (`causal_attribution.py:643-688`; `probe_targeting.py:262-360`). See O8.

---

## 17. Open decisions for review

| # | Decision | Recommendation |
|---|---|---|
| O1 | Does `validity_scope` (grader) vs `causal_class` (diagnoser) correctly split today's `cause_scope`? In particular, `interaction_context` as a validity judgment | Yes as drafted |
| O2 | `is_misconception` ownership: taxonomy prior at grade time, diagnoser authoritative for causal consumers; `raw_grade_events.signature_matched` switches to `discrimination_profile_match` | Adopt |
| O3 | `facet_contrast`: grader (observational) or diagnoser (causal)? | Grader; revisit if E3 shows loss |
| O4 | ~~Sync vs async diagnosis~~ | **Resolved 2026-09-30: async** (§11) |
| O5 | Diagnose correct answers at a shadow sample rate? | 0.0 in S1; start at 0.1 in shadow after S1.3 |
| O6 | ~~Diagnoser model~~ | **Resolved: its own `ai.routing.diagnosis` config**, defaulting to the grading provider |
| O7 | ~~Embeddings for the owner vault~~ | **Resolved: on.** *Revised 2026-10-11 (owner):* Slice 1 uses one OpenRouter model, `qwen/qwen3-embedding-8b`. Learner text leaving the machine is acceptable. The model comparison moves to Slice 2 B1/B3 and runs through the same client |
| O8 | Fold the `repair_class_id` → `repair_equivalence_id` divergence fix into S1, since repair sourcing changes anyway? | Yes, as a separate commit with its own test, if a spurious-divergence case reproduces |
| O9 | Rollback from `mvp-0.10`: restore-only, or a supported forward "joint compatibility" mode? | Restore-only; split rows remain valid |
| O10 | ~~Numeric thresholds~~ | **Resolved: none in S1**; reports with noise floors; thresholds set later from baselines (§13) |
| O12 | `diagnosis.next_item_wait_seconds` default (10 s) | Start at 10; tune from the E7 `served_without_diagnosis` rate |
| O13 | M1 review surface: terminal command vs a Tauri screen | Terminal (`learnloop diagnose review`). It's cheaper, and M1 is a one-off. Build UI only for the M2 card |
| O14 | Forward M2 card taps to the existing unresolved-cause self-report (which can open a provisional belief) when a factor is open? | Yes, to keep that channel's semantics. Watch for acquiescence: if "That's it" rates look implausibly high vs M1 owner adjudication, stop forwarding |
| O15 | M1 sample size and burden | ~40 attempts plus planted cases. Enough to separate "clearly better / clearly worse / can't tell", but only for large differences. "Can't tell" is itself a reason to rethink before M2. With five arms the review takes ~1.5–2.5 h; if that is too much, drop (b) to a random half of the items rather than dropping (c), (d), or (e) |
| O16 | M2 default history mode | `full`, unless the M1 report shows another mode clearly better (§12.1). `full` is the mode that improves with a better diagnoser model, with no code change |
| O17 | `snapshot` transport: Codex read-only workspace only, or also a minimal tool loop (`list` / `grep` / `read`) for OpenAI-compatible providers? | Codex only in M1, since it already runs as an agent. Add the tool loop only if (e) wins and the diagnoser needs to move off Codex |
| O11 | Should the diagnoser see *confirmed* durable misconceptions' prior repair outcomes? | Yes, as typed records (repair class, cold outcome), never prose |

---

*Related: [[Pipeline Augmentation Plan]] · [[Embedding Integration Map]] · [[Bitter Lesson Research Sweep]] · `spec_causal_attribution_v1.md` · `spec_diagnostic_augmentation_v1.md` · `spec_measurement_efficiency_v1.md` · `docs/algorithm-change-playbook.md`*
