# Slice A: practice families and the learner field, ahead of Slice 1 (v1)

**Status:** implementation plan (2026-10-11). Revised the same day three times:
1. after an adversarial review by a Codex agent;
2. after two owner decisions;
3. after two independent architecture reviews (Codex and Opus 5.5), which reshaped the learner-field part. The pre-reshape plan is preserved at commit `936813f`.

**What this document is.** It sequences two specs into one implementation slice that lands **before** Slice 1:
- `spec_embedding_consumers_v1.md` §5, the practice-family track (PF), including the new practice index (§5.9);
- `spec_learner_field_v1.md`, the learner field, reshaped. It is now a low-dimensional predictor competition, an honest "untested" map state, and placement through calibration sessions.

It adds no new learning mechanism. It only:
- carves out the shared embedding substrate;
- fixes cross-spec dependencies;
- adds the engineering rules a review found missing (spend caps, sandboxing, fixture safety, integration);
- adds an evaluation layer that tests the bitter-lesson pivot (§1a);
- gives implementing agents a phase-by-phase contract and a prompt template (§6).

**Owner decisions (2026-10-11):**
1. **Order.** PF and the learner field come before Slice 1 (the blind grader / diagnoser split). Slice 1's M1 waits on data anyway: it needs ≥ ~40 graded wrong answers across topics.
2. **Change what is served; no shadow periods.**
   - Verified generated items are published.
   - Placement goes live.
   - Each serving change is its own algorithm successor with a kill switch (§5.5).
3. **Reshape the learner field** (after the architecture reviews):
   - **The simplest predictor is the incumbent.** That is the existing per-LO mastery filter, and challengers must earn activation.
   - **Facet dossiers move to PF** as a retrieval index.
   - **Deferred, each with a trigger** (field §11): the facet-level graph model, map fog, probe targeting, the LLM-prior hybrid and the public benchmark.
4. **Frictionless defaults: honest labels, generous defaults** (`docs/specs/daily_loop_frictionless_defaults.md`).
   - **No step for the learner exists to protect the model:**
     - no opening probe per topic;
     - "assumed known" from self-report or early answers, checked in the first review;
     - families auto-accepted with undo;
     - LLM judges and usage signals instead of owner rating chores.
   - **What LearnLoop claims stays honest:** untested, assumed, and demonstrated are always distinguished.

---

## 0. What changes because of the new order

1. **The embedding substrate moves into Slice A** (Phase 1). This is the `EmbeddingClient`, the OpenRouter client and `embedding_vectors`, which Slice 1 §9 defined.
   - **Its consumers are now PF's:** the practice index (§5.9), the freshness and isomorph gate, and blocking for very large LOs in family proposals.
   - The learner field no longer needs embeddings.
   - Slice 1 later adds only its own record kinds (hypotheses, registry).
2. **PF's grading support (Slice 2 §5.5, step PF-c) stays after Slice 1.** It changes the grader prompt, which Slice 1 rewrites into the blind grader. Its rules (verified reference, valid-alternative path, solve-first, one high-effort pass) are folded into Slice 1's blind prompt at S1.1. Slice A builds only the valid-alternative **regression suite**, as a harness.
3. **Slice A takes the next migration numbers and algorithm versions.**
   - **It mints successors only for:**
     - starting new material without ceremony (field F2: opening probes off, assumed known checked in review);
     - activating a challenger predictor, if one wins under field §7.4;
     - PF's idea-level retention key, if its replay favours it (Phase 3b).
   - **Publishing verified PF items is a content change**, like writing a card, not an algorithm change.
   - **Slice 1's labels shift.** Its "migration 166" and `mvp-0.10` become whatever is next free.

## 1. Scope and stop lines

**In:**

| Source | What Slice A builds |
|---|---|
| Slice 1 §9.1–9.2, §9.6 | The embedding substrate, subset only, plus the spend controls every paid command uses (§5.6) |
| Learner field | **F1:** the outcome view, `data-check`, the evaluation harness, the `LearnerPredictor` interface, the incumbent `mastery_ekf`, the challenger `lo_general` with extension arms (practice, capability, transfer, retrievability, hint depth, tutor-question signals), `idea_hier` after PF-a, and the explicit **untested** map state. **F2:** starting new material without ceremony (live): no opening probes per topic; "assumed known" from self-report, fast-track on early answers, or an activated predictor, checked in the first review; an optional quick check |
| Slice 2 PF | PF-a (§5.1–5.2), including the idea-key switch if the replay favours it; PF-b (§5.3–5.4, §5.6), including **publication** of verified items; the **practice index** (§5.9: facet dossiers, `find_practice`, coverage report, retrieval evaluation) |
| Slice 2 PF §5.5 | The valid-alternative regression suite, as a harness only |
| Evaluation layer (§1a) | The shared harness `learnloop eval` (field §7.2); the model-tier scaling check (PF §5.6); `judgment_ledger` and per-component model routes (PF §5.8) |

**Out (stop lines):**
- PF-c (grader changes), after Slice 1 S1.3.
- Everything in Slice 1, T1, and Slice 2 T4–T8.
- **The deferred learner-field items, each with its trigger** (field §11): the facet-level graph model, map fog, probe targeting, `idea_hier_llm_prior` and any live use of the LLM predictor, the public-data benchmark, prerequisite-directed coupling, and a learned action router.
- The daily-loop work: capture box, single intent control, finite plan, re-entry. That has its own track. Slice A needs only the dormant/resolved-LO serving fix before Phase 6.

## 1a. How Slice A tests the pivot

The pivot's claim: **model compute, pretrained components and principled uncertainty beat hand-built rules for this learner, where the data can tell.** Three pieces make it testable rather than assumed:

1. **One evaluation harness** (field §7.2). Every predictor is a registered arm scored prequentially on the same rows. The arms are:
   - the per-LO base rate;
   - facet Beta;
   - the incumbent `mastery_ekf`;
   - `lo_general` and its extensions (learning from practice, capability, transfer distance, FSRS retrievability);
   - `idea_hier` after PF-a;
   - optionally, an offline-only LLM predictor.

   Placement depends only on the `LearnerPredictor` interface. A challenger that wins under the switching rule (field §7.4) becomes the model underneath without redesign, and "can't tell" keeps the incumbent.
2. **A scaling check** (PF §5.6). The generator and judges run at two model tiers on identical inputs. If quality rises with the model, the bitter-lesson bet holds for that component; if not, the report says where hand-built structure should stay.
3. **One judgment ledger** (PF §5.8). Every LLM, verifier and owner verdict is stored append-only with model, prompt version and input hash: family judgments, practice relevance, placement overrides. It is the ground truth for the above, and it is never re-run on rebuild.

**The principle the reviews converged on:** nuance lives in text that LLM components read (dossiers, item outlines, attempt analyses). The numeric learner state stays low-dimensional.

## 2. Phase 0: pre-flight (owner and housekeeping)

- [x] **Base branch.** `fix/review-recovery-and-telemetry` was fast-forwarded into `main` on 2026-10-11 (migrations through 165).
- [x] **Planning docs committed** on `main`.
- [ ] **`OPENROUTER_API_KEY`** is available to the app before the Phase 1 backfill. LearnLoop reads the shell environment, `<vault>/.env`, or `~/.config/learnloop/settings.env`, not the repo-root `.env`.
- [ ] **Data check.** The owner runs the attempt/error count query once now. Phase 2 ships it as `learnloop field data-check`. Thin data never blocks building (§5.9).
- [ ] **Owner decisions, needed before the phase that uses them.** Defaults are each spec's recommendations; say "defaults" to accept them.

  | Phase | Decisions |
  |---|---|
  | 2 | Field D1 (`mastery_ekf` is the incumbent), D2 (general level only, no graph coupling), D3 (extension-arm constants), D8 (LLM predictor off by default), D9 (switching margin), D10 (missing revisions excluded), D12 (interaction-signal constants) |
  | 3 | **Slice 2 P12**: how `PracticeFamily` maps onto the existing `activity_families` → cards → surfaces substrate (migration 065). This one has no safe default: the Phase 3 agent's first task is a short investigation and recommendation, then it stops for the owner. Also P8 (family backfill) and P11 (isomorphs count as reps) |
  | 5 | P10 (solver panel); the two model tiers for the scaling check (default: your configured cheap and frontier routes); the practice-index retrieval bar (§5.9: dossiers must beat direct item search). P7 and P9 are settled: bubblewrap sandbox; unverified references are never published |
  | 6 | Field D4 (quick check optional), D5 (self-reports act immediately), D6 (fast-track rule; first review at 14 days), D7 (don't wait for Slice 1's grader probes), D11 (opening probes off by default) |

## 3. Phases

Phase 1 merges first. Phases 2 and 3 then run in parallel, each branched from the merged Phase 1, and integrate one at a time (§5.2). The former Phases 2b (public benchmark), 4 (map fog) and 7 (probe targeting) are deferred with triggers (field §11).

| Phase | Builds (spec refs) | Depends on | Checkpoint before the next phase |
|---|---|---|---|
| **1. Embedding substrate + spend controls + ledger** | `ai/embedding.py` `EmbeddingClient` protocol; `ai/providers/openai_embedding.py` (OpenRouter base URL, `qwen/qwen3-embedding-8b`, batched input, provider routing via `extra_body={"provider": {"data_collection": "deny"}}`); `openai_embedding` profile, `embedding` `AITask` with no fallback to `active_provider`, readiness branch; `embedding_vectors` (WORKFLOW); `model_call(purpose="embedding")` receipts; `learnloop embeddings backfill` (idempotent via `content_hash`), with record-kind recipes that declare their text (Slice 2 R3). **The spend-control framework of §5.6**, used by every paid command in Slice A. **`judgment_ledger`** (RAW_LEDGER) and its append API (PF §5.8). Template defaults: `embedding.enabled = false`, `embedding.backfill_enabled = false` | Phase 0 | Client, store, ledger and spend-cap tests; backfill idempotent on a `fixtures-local/` copy; replay makes zero embedding calls |
| **2. Learner field F1: predictors, harness, untested state** (no change to what is served) | Field §3–§4, §5.1, §7.2–7.3:<br>• `facet_outcome_observations` (authoritative inputs, revision status, serving origin) and attempt-level rows;<br>• `learnloop field data-check`;<br>• the `LearnerPredictor` interface;<br>• the `mastery_ekf` adapter (incumbent);<br>• **interaction signals** (field §3.1) derived from hints, their timing, tutor questions during practice and after feedback, and reader questions, with LLM classification only where the type is missing;<br>• `lo_general` and its extension arms (practice, capability, transfer, retrievability, `+hints`, `+tutor_signals`) plus the composite;<br>• the shared harness `learnloop eval` with its arms (the LLM predictor off by default);<br>• reports 1–2;<br>• the explicit **untested** state on the map in place of `ready = 0.5` | Phase 1 (ledger only; embeddings not needed) | Field gates G1–G6, G10–G13. **The owner reviews reports 1–2 once**, run on a copy of their vault. A challenger is activated only under field §7.4 |
| **3. PF-a: families (+3b idea key)** | P12 investigation → owner decision. Then:<br>• the `PracticeFamily` vault model and `PracticeItem.family_id` / `variant_relation`. Items without a family serialize byte-identically;<br>• `learnloop families propose`, using an **exhaustive LLM judge within each LO** (route `ai.routing.pf_family_judge`). Every verdict and every accept/reject goes to `judgment_ledger`; `family_proposals` (WORKFLOW) holds queue state only;<br>• **families auto-accepted** when two judge passes agree, with one-step undo; ambiguous items stay unfamilied, and there is no review queue;<br>• `family_memory_state` (DERIVED);<br>• the idea-identity replay as harness arms (memory per item / family / LO);<br>• the `idea_hier` challenger arm (field §4.3).<br>**3b:** if the replay clearly favours per-family memory state, switch it live for family items (algorithm successor, kill switch `families.retention_key_live`). If it can't tell, don't switch | Phase 1; P12 | Owner reviews the replay report (families are already applied and can be undone at any time); 3b only after that review |
| **5. PF-b: generate → verify → select → publish, plus the practice index** | Generator programs in the **bubblewrap sandbox** (Slice 2 §5.3); verified references; closed-book, figure-only and provenance filters; solution outlines persisted in `item_skeletons` (WORKFLOW, never regenerated on rebuild); freshness/isomorph gate with `item_fingerprints`; solver panel (`difficulty_source = "solver_panel"`); diversity selection; candidates in `pf_candidates` (WORKFLOW).<br>**Items that pass verification and the filters publish into their family as ordinary items**, capped at `pf.max_published_per_day` (default 10) until the daily-loop new-material policy (Q11) exists. Unverified references are never published.<br>Also:<br>• B2 on the shared `learnloop embeddings compare` harness;<br>• the valid-alternative regression suite as a harness;<br>• the pilot (one chapter, one paper or repo) **including the scaling check** at two model tiers, judged by blind pairwise LLM comparison and later usage signals, with an optional ≤ 10-minute owner rating;<br>• **the practice index** (§5.9): `facet_dossiers`, dossier-field embeddings, `find_practice` (two-level retrieval → LLM rerank → scheduler admission), the coverage report, and the retrieval evaluation against direct item search.<br>Every paid component is its own model route, and every verdict and rating appends to `judgment_ledger`. Generation has its own switch, `pf.generation_enabled`, off in the template | Phase 3 | B2 report; pilot report (survival per filter, the LLM judge's blind comparison of 15 filtered vs 15 single-shot items, per-tier scaling-check results); practice-index retrieval report (LLM labels plus usage signals) |
| **6. Learner field F2: starting new material without ceremony** | Field §5.2:<br>• **no opening probe per new topic** (`placement.initial_probes = false`); diagnosis only when a wrong answer leaves a real choice of repair;<br>• new material starts as learning, ordered by prerequisites and predicted difficulty. **Practice and your questions are the placement:** LOs you asked confused questions about or needed help on are taught first and never fast-tracked;<br>• **"assumed known (not tested)"** from "I know this" or "too easy", from fast-track (≥ 2 cold correct first answers above threshold, with no hints or confusion questions), or from an activated predictor. The LO enters maintenance, its first review (14 days) is the check, and a failure quietly returns it to learning;<br>• "I don't know this" acts immediately;<br>• an optional "Check what I already know" calibration session;<br>• `assumption_decisions` receipts, and the map's "assumed" label.<br>**Algorithm successor**; kill switch `placement.enabled` restores today's initial probes | Phase 2 checkpoint; the dormant/resolved-LO serving fix (daily-loop track) | Gates G4, G7–G9; report 3 (first-review miss rate by source) after several imports |

**After Phase 6, stop.** The owner then decides:
- tuning from report 3 (thresholds, publish cap, kill switches);
- whether any deferred learner-field item's trigger has fired (field §11);
- the daily-loop track;
- Slice 1, starting with the two-stage M1.

## 4. Cross-spec notes (record when each phase merges)

- **Slice 1.**
  - §9.1–9.2 are delivered by Slice A Phase 1, and Slice 1 S1.4a adds only the `hypothesis` and `misconception` record kinds.
  - M1's pattern-link verdicts import into `judgment_ledger`.
  - Its migration and algorithm-version labels follow Slice A's successors.
  - M1 arm (c) reuses the Phase 1 client.
  - PF-c's grading rules join the blind prompt at S1.1.
  - Slice 1's E1 grader probes also measure the risk behind fast-track's "assumed known".
  - The diagnoser can use `find_practice` for repair targeting.
- **Slice 2 PF.**
  - PF-a and PF-b depend on Slice A Phase 1.
  - Family backfill uses the exhaustive within-LO judge.
  - Generator programs run under bubblewrap.
  - Verified items publish.
  - Facet dossiers live in the practice index (§5.9).
  - PF-c stays after Slice 1 S1.3.
  - B2 builds the shared compare harness.
  - T1's adjudication ledger is `judgment_ledger`, created in Slice A Phase 1 and formerly named `embedding_adjudications`. T1 adds the `same_cause` task. Its calibrators remain a pending owner decision.
- **Learner field.**
  - Reshaped: F1 is Slice A Phase 2, and F2 is Phase 6.
  - Consumers depend on the `LearnerPredictor` interface.
  - The deferred items and their triggers are in its §11, with the full prior design at commit `936813f`.
  - It aligns with `spec_knowledge_model.md` §8.1 and §8.3.

## 5. Rules for implementing agents

1. **Read first:**
   - `CLAUDE.md`, especially the fixture and migration rules;
   - this file;
   - the cited sections of the phase's spec;
   - `db/table_roles.py`;
   - `docs/algorithm-change-playbook.md`;
   - `docs/learnloop-architecture-vault/Home.md` for orientation.
2. **Branching and integration.**
   - One phase per branch and PR, created from the **merged prerequisite phase**, not from the Phase 0 base. Never commit to `main` directly.
   - Integrate parallel phases one at a time. The second to merge rebases, takes the next free migration number if the first claimed its number, regenerates the head fixture, and reruns:
     - the table-roles check;
     - rebuild-registry/replayer checks;
     - the durability lane;
     - rebuild equivalence.
3. **Migrations.**
   - `ls migrations/` for the next free number at the time, and follow `CLAUDE.md`'s head-fixture procedure.
   - Every new table gets a role in `db/table_roles.py`. Every DERIVED table gets exactly one replayer and replay-completeness coverage.
4. **Invariants that must hold:**
   - **Replay** makes zero LLM and zero embedding calls. Paid outputs (vectors, judge verdicts, skeletons, generated items) are persisted inputs and are never regenerated on rebuild.
   - **The field acts only through its consumers:** episode entry, probe selection, display. It never writes evidence, mastery, certification, coldness or FSRS state.
   - **Embeddings** never decide identity, novelty or difficulty alone (Slice 2 R1/R2).
   - **Grading contexts** stay learner-blind.
   - **Rebuilds:** under the *previous* algorithm version, every fixture copy rebuilds identically. Under a new successor, the differences are exactly the documented serving changes.
   - **Vault model:** new fields are optional and additive. Items without a family serialize byte-identically. The scheduling hash (`vault/hashes.py` `practice_item_hash`) is unchanged, and full-item snapshot hashes change only for items that gained family fields.
5. **Serving changes are allowed.** Each must:
   - be its own algorithm successor under the playbook: upgrade function, shadow rebuild on a backup-API copy, head fixture;
   - sit behind a config kill switch that restores the previous behaviour exactly;
   - log receipts of what the new behaviour did, and what the old rule would have chosen where that is cheap to compute.
6. **Spend controls (every paid command):**
   - **Caps before requests:** explicit caps on candidates, pairs, retries, tokens and estimated cost, checked before any request is sent.
   - **Dry-run first:** `--dry-run` prints the estimated calls, tokens and cost.
   - **Resumable and cancellable:** checkpoints let an interrupted run continue without re-paying for finished work, and cancellation stops cleanly.
   - **Unknown prices** are treated as over budget unless the owner raises the cap.
   - **Separate switches:** embedding backfill and PF generation have independent switches, off in the template.
   - **Recording:** receipts record the caps in force (migration 165's `budget_json`).
7. **Verification before calling a phase done:**
   - the spec's listed tests;
   - `uv run pytest` on the touched and new test files, plus `uv run pytest -m durability` when a migration is added;
   - `uv run lint-imports --no-cache`;
   - for UI phases (4, 6): `npm run typecheck && npm test` in `apps/learnloop-tauri/`.

   The full suite (`uv run pytest -n auto`; ~17–33 min serial) runs before the PR is marked ready.
8. **Fixtures and owner data.**
   - Never run backfills, family proposals, generation, rebuilds or reports against tracked fixtures. `linear_algebra`, `probability` and `arxiv_v2` are the owner's working vaults. Use backup-API copies (`learnloop.db.copies`) under gitignored `fixtures-local/`.
   - Never revert, stash or commit changes in those working vaults. Only the migration-head fixture follows the upgrade procedure.
   - Never read `~/.config/learnloop/` or search for the owner's vault. Reports that need it are delivered as commands for the owner to run on a copy.
9. **Thin data never blocks building.** It only affects data-dependent decisions: the 3b switch, activating a challenger predictor (field §7.4), and placement's starting threshold. Every report states:
   - sample counts and exclusions (including field §4.2's revision status);
   - uncertainty intervals;
   - a version manifest (algorithm, kernel, embedding model, config hash);
   - that evaluation is prequential (only past data predicts each outcome).
10. **At every checkpoint, stop.** Write `docs/reviews/slice-a-phase-<n>.md` containing:
    - what was built;
    - deviations from the spec and why;
    - test results (summarized, with any failures in full);
    - commands for the owner to run;
    - the open questions.

    Don't start the next phase.
11. **Measurement.**
    - All evaluation runs through `learnloop eval`. Never write a one-off evaluation script.
    - Every paid component is its own config route (`ai.routing.<component>`). Receipts record model id and prompt version, and every report splits results by model id.
    - Every LLM, verifier or owner verdict appends to `judgment_ledger`. Workflow tables hold queue and pipeline state only.
    - Reports contain aggregates only, never learner text.
    - Public datasets stay under gitignored `fixtures-local/benchmarks/`, with source, version and licence in each manifest.
12. **Spec conflicts.** If the spec is wrong or contradicts the code, don't silently improvise. Record the conflict in the review file. Pick the conservative option if work can continue (kill switch off, no evidence writes), and otherwise stop.

## 6. Agent prompt template

Fill in `<n>`, the phase row from §3, and the prerequisite branch, then give it to a fresh agent in the repo.

```text
Implement Slice A Phase <n> of LearnLoop, as specified in
docs/specs/spec_slice_a_practice_and_field_v1.md (§3 row "<n>", §5 rules).

Before coding, read: CLAUDE.md; spec_slice_a_practice_and_field_v1.md in full; the spec
sections cited in the Phase <n> row; db/table_roles.py; docs/algorithm-change-playbook.md.
Then write a short plan (files to add or change, migrations, algorithm successor if any,
kill switches, spend caps, model routes, judgment_ledger writes, harness arms, tests) to
docs/reviews/slice-a-phase-<n>.md and proceed.

Work on a new branch slice-a/phase-<n> created from <merged prerequisite branch>.
Follow every rule in §5, especially: successors and kill switches only where §3 says,
replay makes no model calls, spend caps with dry-run on every paid command, the CLAUDE.md
migration and fixture rules (work on fixtures-local/ copies, never the working vaults),
and stop at the checkpoint.

Done means: all tests in the phase's spec list exist and pass; lint-imports passes; the
full suite passes; docs/reviews/slice-a-phase-<n>.md lists what was built, deviations,
test results, owner-run commands, and open questions. Commit with clear messages; do not
merge or push unless asked.
```

---

*Related: `spec_embedding_consumers_v1.md` §5 (PF) · `spec_learner_field_v1.md` · `spec_blind_grading_diagnosis_split_v1.md` · [[Bitter Lesson Research Sweep]] · [[Pipeline Augmentation Plan]]*
