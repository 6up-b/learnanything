# Slice A: practice families and the learner field, ahead of Slice 1 (v1)

**Status:** implementation plan (2026-10-11). Revised the same day after an adversarial review by a Codex agent and two owner decisions.

**What this document is.** It sequences two existing specs into one implementation slice that lands **before** Slice 1:
- `spec_embedding_consumers_v1.md` §5, the practice-family track (PF);
- `spec_learner_field_v1.md`, the learner field.

It adds no new learning mechanism. It only:
- carves out the shared embedding substrate;
- fixes cross-spec dependencies;
- adds the engineering rules the review found missing (spend caps, sandboxing, fixture safety, integration);
- adds an evaluation layer that tests the bitter-lesson pivot itself (§1a);
- gives implementing agents a phase-by-phase contract and a prompt template (§6).

**Owner decisions (2026-10-11):**
1. **Order.** PF and the learner field come before Slice 1 (the blind grader / diagnoser split).
   - Both serve learning, retention and placement directly.
   - Slice 1's M1 waits on data anyway: it needs ≥ ~40 graded wrong answers across topics.
2. **Change what is served; no shadow periods.**
   - Generated items that pass verification are published.
   - Placement and probe targeting go live.
   - Each serving change is its own algorithm successor with a kill switch (§5.5), so it is reversible and measurable, not tentative.

---

## 0. What changes because of the new order

1. **The embedding substrate moves into Slice A** (Phase 1). This is the `EmbeddingClient`, the OpenRouter client and `embedding_vectors`, which Slice 1 §9 defined and which PF and the field both need. Slice 1 later adds only its own record kinds (hypotheses, registry).
2. **PF's grading support (Slice 2 §5.5, step PF-c) stays after Slice 1.** It changes the grader prompt, which Slice 1 rewrites into the blind grader. Its rules (verified reference, valid-alternative path, solve-first, one high-effort pass) are folded into Slice 1's blind prompt at S1.1. Slice A builds only the valid-alternative **regression suite**, as a harness.
3. **Slice A takes the next migration numbers and algorithm versions.**
   - **It mints successors** for each change to what is served or what persisted state means:
     - placement live (field S5);
     - probe targeting live (field S7);
     - PF's idea-level retention key, only if its replay favours it (Phase 3b).
   - **Publishing verified PF items is a content change**, like writing a card, not an algorithm change.
   - **Slice 1's labels shift.** Its "migration 166" and `mvp-0.10` become whatever is next free when it is implemented.

## 1. Scope and stop lines

**In:**

| Source | What Slice A builds |
|---|---|
| Slice 1 §9.1–9.2, §9.6, learner field §4.1 | The embedding substrate, subset only, plus the spend controls every paid command uses (§5.6) |
| Learner field | S1 outcome view, S2 field + replay report, S3 map layer, **S5 placement live**, **S7 probe targeting live**. The shadow stages S4 and S6 are dropped |
| Slice 2 PF | PF-a (§5.1–5.2), including the idea-key switch if the replay favours it, and PF-b (§5.3–5.4, §5.6), including **publication** of verified items |
| Slice 2 PF §5.5 | The valid-alternative regression suite, as a harness only |
| Evaluation layer (§1a) | The shared harness `learnloop eval` with pluggable predictor arms (field §8.3); the public-data benchmark and time-to-useful-vault, report 6 (field §8.4); the model-tier scaling check (PF §5.6); `judgment_ledger` and per-component model routes (PF §5.8) |

**Out (stop lines):**
- PF-c (grader changes), after Slice 1 S1.3.
- Everything in Slice 1, T1, and Slice 2 T4–T8.
- The transfer-gap alarm (field feature 3).
- The daily-loop work: capture box, single intent control, finite plan, the bugs. That has its own track, and Slice A defines minimal behaviour where it would otherwise depend on it (Phase 6).

## 1a. How Slice A tests the pivot

The pivot's claim: **model compute, pretrained components and principled uncertainty beat hand-built rules for this learner.** Slice A builds such components (an embedding-based graph model, generate-and-verify practice, LLM judges). Four pieces make the claim testable rather than assumed:

1. **One evaluation harness** (field §8.3). Every predictor, hand-built or learned, is a registered arm scored prequentially on the same per-facet outcome rows. The launch arms are:
   - the hand-built baselines (per-topic base rate, facet Beta, per-LO mastery, FSRS);
   - the learner field;
   - optionally, a frontier LLM giving P(correct).

   Later learned features join as arms, not as new scripts.
2. **A public-data benchmark** (field §8.4). Each learner of a public dataset is replayed as an independent n=1 vault. That gives the statistical power your own history can't, and it measures the plan's headline metric, time-to-useful-vault (`K_useful`).
3. **A scaling check** (PF §5.6). The generator and judges run at two model tiers on identical inputs. If quality rises with the model, the bitter-lesson bet holds for that component; if not, the report says where hand-built structure should stay.
4. **One judgment ledger** (PF §5.8). Every LLM, verifier and owner verdict is stored append-only with model, prompt version and input hash. It is the ground truth for all of the above, and it is never re-run on rebuild.

## 2. Phase 0: pre-flight (owner and housekeeping)

- [ ] **Base branch.** Migrations 159–165 and the PR #5 work exist only on `fix/review-recovery-and-telemetry`; `main` stops at 158. Merge that branch into `main` first (preferred), or base Slice A on it.
- [ ] **Commit the planning docs.** These specs and brainstorming docs are untracked, so an agent in a worktree or another checkout can't see them. The files are:
  - `docs/specs/spec_blind_grading_diagnosis_split_v1.md`
  - `docs/specs/spec_embedding_consumers_v1.md`
  - `docs/specs/spec_learner_field_v1.md`
  - this file
  - `docs/brainstorming/Bitter Lesson Research Sweep.md`
  - the user-intentions docs
  - the updated `CLAUDE.md`

  The project-understanding and mobile specs can ride along.
- [ ] **`OPENROUTER_API_KEY`** is available to the app before the Phase 1 backfill.
- [ ] **Data check.** The owner runs the attempt/error count query once now. Phase 2 ships it as a repeatable command (`learnloop field data-check`). Thin data never blocks building (§5.9).
- [ ] **Owner decisions, needed before the phase that uses them.** Defaults are each spec's recommendations; say "defaults" to accept them.

  | Phase | Decisions |
  |---|---|
  | 2 | Field D1 (facets only), D2 (heat kernel + EKF), D3 (confusables weighted 0), D8, D10, D13 (`llm_probability` arm on, $5 cap per run) |
  | 2b | Field D12 (which public dataset; the agent recommends, then stops for you), D14 (`K_useful` tolerance) |
  | 3 | **Slice 2 P12**: how `PracticeFamily` maps onto the existing `activity_families` → cards → surfaces substrate (migration 065). This one has no safe default: the Phase 3 agent's first task is a short investigation and recommendation, then it stops for the owner. Also P8 (family backfill) and P11 (isomorphs count as reps) |
  | 5 | P10 (solver panel); the two model tiers for the scaling check (default: your configured cheap and frontier routes). P7 and P9 are settled by this revision: bubblewrap sandbox; unverified references are never published |
  | 6 | Field D4–D6 |

## 3. Phases

Phase 1 merges first. Phases 2 and 3 then run in parallel, each branched from the merged Phase 1, and integrate one at a time (§5.2). Phase 2b starts once Phase 2's harness has merged, and runs alongside Phase 3.

| Phase | Builds (spec refs) | Depends on | Checkpoint before the next phase |
|---|---|---|---|
| **1. Embedding substrate + spend controls** | `ai/embedding.py` `EmbeddingClient` protocol; `ai/providers/openai_embedding.py` (OpenRouter base URL, `qwen/qwen3-embedding-8b`, batched input, provider routing via `extra_body={"provider": {"data_collection": "deny"}}`); `openai_embedding` profile, `embedding` `AITask` with no fallback to `active_provider`, readiness branch; `embedding_vectors` (WORKFLOW); `model_call(purpose="embedding")` receipts; `learnloop embeddings backfill` (idempotent via `content_hash`); record kinds `facet/definition` and `learning_object/summary` (field §4.1), with recipes that declare their text (Slice 2 R3). **The spend-control framework of §5.6**, used by every paid command in Slice A. **`judgment_ledger`** (RAW_LEDGER) and its append API (PF §5.8), used from Phase 3 on. Template defaults: `embedding.enabled = false`, `embedding.backfill_enabled = false` (Slice 1 §9.1–9.2, §9.6; field §4.1) | Phase 0 | Client, store and spend-cap tests; backfill idempotent on a `fixtures-local/` copy; replay makes zero embedding calls |
| **2. Field: outcome view + field + replay report** | Field S1–S2: `facet_outcome_observations` with authoritative inputs, revision status and serving origin (field §4.2, revised); graph, prior and EKF with zero-mass skipping, the per-attempt information budget and primed handling as in `mastery.py` (field §5.3, revised); `learner_field_graph`, `learner_field_snapshot`; **the shared harness `learnloop eval`** with the launch arms and the optional `llm_probability` arm (field §8.3); `learnloop field rebuild` / `data-check`; reports 1–2 on the harness. Authored-only fallback when no vectors exist | Phase 1 (embeddings optional) | Field gates G1–G5, G10, G11, G13. **The owner reviews the replay report once**, running it on a copy of their vault. This is a checkpoint, not a shadow period |
| **2b. Public-data benchmark** | Field §8.4: dataset recommendation, then an owner pick (D12); adapter into harness rows outside any vault; LLM-written KC definitions (spend-capped, persisted) embedded with the Phase 1 client; report 6, per-learner replay of every arm plus time-to-useful-vault (`K_useful`). Data stays in gitignored `fixtures-local/benchmarks/` | Phase 2 harness | Report 6 reviewed. Should finish before Phase 6, because it sets placement's starting `q` when your own data is thin; it doesn't block Phase 6 |
| **3. PF-a: families (+3b idea key)** | P12 investigation → owner decision. Then:<br>• the `PracticeFamily` vault model and `PracticeItem.family_id` / `variant_relation` (items without a family serialize byte-identically);<br>• `learnloop families propose`, using an **exhaustive LLM judge within each topic** (no embedding cutoff, no skeletons needed), with every judge verdict and your accept/reject decisions appended to `judgment_ledger`, and `family_proposals` (WORKFLOW) holding queue state only, so a rebuild never re-judges. The judge is its own model route, `ai.routing.pf_family_judge`;<br>• owner review in batches of 25 that can be deferred;<br>• `family_memory_state` (DERIVED);<br>• the idea-identity replay, as harness arms: memory keyed per item, per family, and per LO (Slice 2 §5.1–5.2, revised).<br>**3b:** if the replay clearly favours per-family memory state, switch it live for family items (algorithm successor, kill switch `families.retention_key_live`). If it can't tell, don't switch; families still drive generation and transfer probes | Phase 1; P12 | Owner reviews proposals and the replay report; 3b only after that review |
| **4. Field: map layer** | Field S3 (§6.1): fog for inferred facets, `?` for unknown ones; demonstrated beads and well depth untouched. **On by default**; a toggle hides it | Phase 2 checkpoint | Gate G6; report 5 after use |
| **5. PF-b: generate → verify → select → publish** | Generator programs in the **bubblewrap sandbox** (Slice 2 §5.3, revised); verified references; closed-book, figure-only and provenance filters; solution skeletons persisted in `item_skeletons` (WORKFLOW, never regenerated on rebuild); freshness/isomorph gate with `item_fingerprints`; solver panel (`difficulty_source = "solver_panel"`); diversity selection; candidates and their filter results in `pf_candidates` (WORKFLOW). **Items that pass verification and the filters publish into their family as ordinary items**, capped at `pf.max_published_per_day` (default 10) until the daily-loop new-material policy (Q11) exists. Items whose reference is unverified are never published. Also: B2 on the shared `learnloop embeddings compare` harness; the valid-alternative regression suite as a harness; the first run is the pilot (one chapter, one paper or repo), whose report tunes the filters. **The pilot includes the scaling check** (PF §5.6): generator and judges at two model tiers on identical inputs. Every paid component is its own model route, and every verdict and rating appends to `judgment_ledger` (PF §5.8). Generation has its own switch, `pf.generation_enabled`, off in the template | Phase 3 | B2 report; pilot report (survival per filter, the owner's blind rating of 15 filtered vs 15 single-shot items, and the per-tier scaling-check results) |
| **6. Field: placement live** | Field S5 (§6.2, revised): trigger, selection, results screen, `placement_decisions`. **Algorithm successor**; kill switch `placement.enabled`. Placement items come from imported exercises and PF-b's published items. With no eligible items, today's per-topic initial probes run. Until daily-loop Q7/Q11 exist, "likely known" means: no initial episode now, one confirm probe after `placement.confirm_after_days`. If the Phase 2 placement simulation couldn't run (thin data), start `q` from report 6's miss-rate curve, or at 0.9 if that isn't available, until confirm probes give a miss rate. "Actually, I don't know this" overrides append to `judgment_ledger` | Phase 2 checkpoint; Phase 5 (for item supply) | Gates G7, G8; report 3 (confirm-probe miss rate) after several imports |
| **7. Field: probe targeting live** | Field S7 (§6.3, revised): the field's score drives stale-uncertainty re-probes and the queue's probe-information input. **Algorithm successor**; kill switch `field.probe_targeting_enabled`. The old variance rule's choice is logged beside each decision | Phase 2 checkpoint | Report 4 |

**After Phase 7, stop.** The owner then decides:
- tuning from reports 3–5 (thresholds, publish cap, kill switches);
- the daily-loop track;
- Slice 1, starting with the two-stage M1.

## 4. Cross-spec notes (record when each phase merges)

- **Slice 1.**
  - §9.1–9.2 are delivered by Slice A Phase 1, and Slice 1 S1.4a adds only the `hypothesis` and `misconception` record kinds.
  - M1's pattern-link verdicts import into `judgment_ledger`.
  - The blind grader and diagnoser can be added as `learnloop eval` arms where they make predictions.
  - Its migration and algorithm-version labels follow Slice A's successors.
  - M1 arm (c) reuses the Phase 1 client.
  - PF-c's grading rules join the blind prompt at S1.1.
- **Slice 2 PF.**
  - PF-a and PF-b depend on Slice A Phase 1.
  - Family backfill uses the exhaustive within-topic judge.
  - Generator programs run under bubblewrap.
  - Verified items publish.
  - PF-c stays after Slice 1 S1.3.
  - B2 builds the shared compare harness.
  - T1's adjudication ledger is `judgment_ledger`, created in Slice A Phase 1 and formerly named `embedding_adjudications`. T1 adds the `same_cause` task. Its calibrators remain a pending owner decision.
- **Learner field.**
  - Its S0b is Slice A Phase 1.
  - S4 and S6 are dropped, and S5 and S7 are built here.
  - Its daily-loop dependencies are reduced to the minimal behaviour in Phase 6.

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
9. **Thin data never blocks building.** It only affects data-dependent decisions: the 3b switch, and placement's starting threshold. Every report states:
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
