# Router R2: router live for the daily plan — implementation plan

**Status:** read-only planning pass, 2026-10-13. No repository file was edited.
**Spec:** `docs/specs/spec_action_router_v1.md` (§3–§12, §15). The daily-loop seam is `docs/specs/spec_daily_loop_v1.md` §6.8.
**Citations:**
- Unprefixed `path:line` is main at `e238fa07`.
- A branch prefix is that branch's tip: `serving/voi-stopping` `af9b35c9f`, `merge/sources-onto-main` `e3aed5057`, `merge/facet-locks` `5a5e1e8ee`, `ux/phase1-first-run` `f74797d66`, `evsi/calibration` `95d51782f`.
- R2 starts only after VOI v2, the Decider migration and UX Phase 1 have landed, and those landings will move many of these lines. Re-verify every citation when the stage starts.

---

## 0. Summary

**What R2 is now.** Most of the plumbing R2 needs is already on main:
- **DL1** built the seam R2 plugs into. A source proposes block candidates, a chooser picks one, and the container enforces feasibility, closed choice and learner picks (`src/learnloop/daily_plan/types.py:146-168`, `src/learnloop/daily_plan/engine.py:150-189`, `:965-1090`).
- **R1** built the decision ledger and already logs every plan block as a `plan_block` row (`src/learnloop/router/plan_log.py:92-270`). The R2 columns are reserved and still NULL (`migrations/181_router_decisions.sql:53-62`).
- **R0** built both model clients (`src/learnloop/ai/decisions.py:153`, `src/learnloop/ai/providers/decider.py:177-256`) and declared the routes (`src/learnloop/config/schema.py:1162-1165`).

**What R2 has to build:**
- the staged frame source;
- the router chooser, with its mixture and exact propensities;
- the state card, the request builders, retrieval, and the payload table;
- an **exact decision → presentation → attempt receipt**, which nothing has today;
- the P2 bridge wiring (D13);
- plain-language "why" copy;
- the switch, its successors and the spend admission.

**Proposed sub-stages.** Each is one implement → review → fix stage. Section 9 has the detail.

| Stage | Builds | Serving change | Successor | Switch |
|---|---|---|---|---|
| **R2a**: staged frame on Today, exact receipts, the card (no model calls) | The `staged_frame_v1` source and `staged_v1` chooser, with the P4 constraint engine vetoing on Today. Presentation receipts and attempt binding. Outcome and EVSI joins through them. The P2 bridge wired (D13). The card, built and stored, with no model. Plain staged "why". The `router_decisions` CHECK extended once | Yes, but small: Today's blocks lose items the P4 hard constraints refuse. Order is unchanged (the staged component is DL1's `lane_quota_v1`, §3.1) | **A** (label at merge) | `router.enabled`, `router.mode = "staged"` |
| **R2b**: both models live, the mixture | Request builders `router_qs_v1` / `router_llm_v1`, `model_mixture`, fallback, spend admission, `router_decision_payloads`, the "why" for model picks, readiness, disclosures | Yes: the mixture chooses blocks (D1: 1/3 each) | **B** | `router.mode = "mixture"` (B's default) |
| **R2c**: restraint, sensors, retrieval | The `intervene_now` restraint at mid-block follow-up insertion (G4); the `teach_first` / `will_pass_next` sensors, logged; `decision/context` embeddings with similar-decision retrieval, included on a logged random half of decisions; §15.1's teach-back summary in the card | Yes: restraint only | Shares B if R2b and R2c land together (recommended); otherwise **C** | `router.restraint`, `router.similar_decisions` |

**Why this differs from the "R2a = logging-only decisions" example.**
- A stage that asks both models on every decision without acting on the answers is a shadow stage, and the owner's principle (prefer-live-changes-over-shadow) rules that out. It would also spend money and latency for nothing served.
- R2a can be live instead. On Today, it is exactly what the P4 bridge already is for P2 runs: the incumbent choice stands unless a named constraint vetoes it (`src/learnloop/scheduling/controller_cutover.py:1-21`, `:166-204`).
- R2a also delivers the exact receipt the owner chose (Q10), which unblocks calibration of the EVSI staged forecasts.
- R2a does not need Perplexity (D6), so it can land while the owner checks retention terms. That check blocks only R2b.

**Top risks** (§10 has the full list):
1. **Latency.** Codex on the subscription and OpenRouter query embeddings (p50 4.5 s, merge-queue notes) can both blow `router.timeout_seconds = 8` on blocking waits. The cost is fallbacks rather than wrong choices. Decide at prefetch and give it a longer budget.
2. **What "staged" means on Today.** The P4 ladder is commitment-scoped (`src/learnloop/scheduling/state_signals.py:45-80`), and three of its signals are never derived live (`:178-192`). This plan makes DL1's `lane_quota_v1` over the P4-feasible set the staged component (§3.1). That is an owner decision.
3. **Engine-seam gaps.**
   - `BlockChooser.choose(state, feasible)` has no repository, card or session (`types.py:165-168`).
   - The chooser's own row must commit with the block, not before it (`engine.py:1320-1359`).
   - Projections must never call a sampled chooser (DL1 F3, `engine.py:150-175`).
4. **Merge collisions in `daily_plan/engine.py`.**
   - VOI v2 rewires the pool and admission (`serving/voi-stopping:src/learnloop/daily_plan/engine.py:460-663`, `:1448-1452`, `:2006`, `:2301`).
   - UX Phase 1 touches `_prepare_plan` and `reading.py`.
   - So R2 starts only after both land, as the queue already says.
5. **Spend.**
   - **The output-budget default.** The shared policy reserves 16,384 output tokens by default (`src/learnloop/ai/output_budget.py:70`; `config/schema.py:1190`). With a $1/day guard on a metered route, that reservation would refuse calls almost at once. The `router_llm` route needs its own budget.
   - **No daily dollar admission on main.** It doesn't exist yet (§8.4).

**Owner questions**, each with a recommended default. Section 11 has the full list.
- Q1: the staged component is `lane_quota_v1` over the P4-feasible set.
- Q2: no staged diagnostic blocks; VOI v2 stays the one authority on probes.
- Q3: two successors.
- Q4: Codex for `router_llm`, a 45 s prefetch budget and 8 s for blocking waits.
- Q5: a 4,096-token `router_llm` output budget.
- Q6: a $1.00/day metered guard, with subscription routes uncapped.
- Q7: restraint as a logged mixture, not the 0.3 threshold.
- Q8: retrieval in R2c, with randomized inclusion.
- Q9: decide the first block at Today-open prefetch.
- Q10: D13 bridge semantics.
- Q11: D6 gates the R2b merge.
- Q12: the copy for exploration draws.

---

## 1. Starting point and landing order

**The queue** (merge-queue notes, "LANDING ORDER" and "OWNER QUEUE ADDITIONS"; memory `implementation-queue-oct13.md`):
1. The sources track (mvp-0.18 / mvp-0.19, migrations 187–195).
2. Facet locks (196–197, no successor).
3. The Decider migration, in parallel with exam protection.
4. EVSI multisim.
5. The proof route check folded into the grader (a placeholder successor).
6. UX Phase 1 (the reading step, a placeholder successor).
7. VOI v2 (a successor, with migrations renumbered).
8. **R2.**

R2's labels are assigned at its merge, after whatever is LATEST then; mvp-0.2x is likely. Its migrations take the next free numbers.

**Preconditions on main before R2a starts.** VOI v2, the Decider migration and UX Phase 1 are merged. R2a can start without D6.

**Preconditions before R2b merges.** The owner has recorded D6, Perplexity's retention terms (spec `:386`; `docs/reviews/router-r0.md:535-539`). The R2b review records where the owner wrote it down.

**What R2 is not:**
- R3 (`learnloop router report`, switching per §10.4);
- §15.3 / sources §10.6 retrieval tools for the router;
- §15.5 / §15.6 (see §6);
- item-level routing.

---

## 2. Each §11 R2 item: what exists and what is new

| §11 item | Exists on main (file:function) | New in R2 |
|---|---|---|
| **`LearnerStateCardV1`** | Nearest prototypes:<br>• R0 V3 renderer `field/probability_states.py:163` (`StateRenderer`), `render` `:349`, `_card` `:450`, `_hypotheses` `:585`, `_strip_private` `:712`, `_fit` `:742`; past-only rules `:1-53`; `CARD_TOKEN_BUDGET = 16_000` `:80`, already labelled as the router default.<br>• Session fields: `PlanState` (`daily_plan/types.py:72-92`).<br>• Intent: `IntentView` (`types.py:57-68`).<br>• Leakage sources: no cold-answer material in the snapshot (`scheduling/controller_snapshot.py:13-14`); `source_retrieval/corpus.py:269` `teaching_exclusions`; `content/authoring/practice_leakage.py:127` `held_out_spans`.<br>• Held grades: `held_grades.py:49` `held_for_review_attempts`; `outcome_contract.py:126` `grade_is_held`.<br>• **Not reusable as the card:** `diagnosis/split/context.py:608` `assemble_diagnosis_context`. Its current block carries `reference_solution` and the learner's answer (`:146`, `:150`), so it is post-grade | `router/card.py`: a deterministic builder from the ledger, with typed JSON plus text sections, the budget truncation order of §4, and a hash. It reuses the V3 renderer's history and hypothesis sections. The rest is new: the typed session block from `PlanState`, the per-candidate LO block (predictor mean and interval, untested / assumed / demonstrated, FSRS R, evidence summary), the 7-day interaction signals, open learner-text gaps (migration 182) and a registry of typed evidence sections (the hook for §15.1 and §15.5). Built in R2a |
| **`decision/context` embeddings and retrieval** | • Store: mean-centred cosine `db/stores/embedding_vectors.py:126` `retrieve`, with the `candidate_ids` filter after centring (`:183-185`), `IncompleteEmbeddingIndex` (`:159-161`), and `nearest_among_current` for partial coverage (`:213`).<br>• The DB-backed recipe pattern: `diagnosis/split/embeddings.py:46` (`DB_RECIPES`), `:169` `db_records`, `:241` `embed_records` (`LIVE_CAPS` `:49`).<br>• The static recipe registry `vault/embedding_recipes.py:273`, which forbids learner state (`:3`), so it isn't usable.<br>• Gate `embedding.enabled = false` (`config/schema.py:1892`); route default `openrouter_embedding` (`:1077`) | The record kind `decision/context`, a DB recipe over the logged decision's canonical typed state, a maturity-filtered retrieval, an inclusion coin per decision, and `similar_decision_ids_json` (the column exists). Built in R2c |
| **Both model requests** | • The Decider client contract (`ai/decisions.py:50-163`, `parse_response` `:273` fails closed).<br>• The OpenRouter transport `/alpha/decisions` (`ai/providers/decider.py:48-53`, `:216`; 30 s default timeout `:61`).<br>• Routes `router_decider` / `router_llm` (`config/schema.py:1162-1165`; `ai/routing.py:76-79`, `:88`, `:234-238`, `:496`: no chat fallback for the Decider).<br>• Receipts `ai/execution.py:38-43`, `:246` (judge, question_set_version and state_hash labels); migration 175.<br>• **There is no router request builder.** The only builder is the V1–V3 harness `field/probability_prep.py:69`, `:406-432` | `router/requests.py`:<br>• the `router_qs_v1` question set (`choose_block` as a `ChoiceQuestion` over at most k options, `intervene_now`, `teach_first_<lo>`, `will_pass_next_<lo>` as `NoulQuestion`s);<br>• the `router_llm_v1` structured schema (a distribution over every candidate id, renormalized; unknown ids rejected; at most 3 sentences of rationale; `evidence_ids` validated against the card);<br>• a per-call timeout override, because the provider defaults to 30 s.<br>Built in R2b |
| **The two modes and `model_mixture`** | • `ChosenBy` already includes `staged` and `mixture` (`types.py:43`), and `WhyKind` includes `model_written` and `model_no_rationale` (`:44`).<br>• The engine validates a chooser's `chosen_by`, propensity and why kind (`engine.py:1093-1114`).<br>• `randomization_layer` has three designs (`scheduling/randomization_layer.py:149`, `:200`, `:241`), a dormant `PROPENSITY_FLOOR = 0.05` (`:47`) and `EPSILON_TIE_MARGIN = 0.05` (`:42`).<br>• The ledger's design registry is `db/stores/router.py:39-42`, refused at `:85` | • `router/chooser.py`: `RouterChooser` (`staged` and `mixture`); top-k selection; the floor; the two-stage draw; fallback.<br>• `model_mixture` registered both in `randomization_layer` (as the fourth design) and in `ROUTER_DESIGNS`.<br>• Config: `router.enabled`, `router.mode`, `router.weights`, `router.k`, `router.epsilon_min`, `router.ties_only`, `router.timeout_seconds`, `router.prefetch_timeout_seconds`. None exist yet: `RouterConfig` has only `log_decisions` and `probe_tie_admission` (`config/schema.py:2179-2193`) |
| **`router_decisions` / payloads / outcomes** | • `router_decisions` is a RAW_LEDGER: append-only, with a `decision_kind` CHECK that admits `today_offer`, `staged_p2`, `learner_pick` and `plan_block` only (`migrations/181_router_decisions.sql:17-19`, `:67-73`). Every R2 column exists and is NULL.<br>• The `plan_block` row builder is `router/plan_log.py:92-248`. It skips the row when the chooser set its own `decision_ref` (`:263-264`).<br>• `router_outcomes` is DERIVED, with one replayer and a held-grade exclusion (`router/outcomes.py:182-193`, `:564`; callers `substrate/rebuild_orchestrator.py:517`, `:526-531`) | • `router_decision_payloads` (WORKFLOW): the card text and both raw responses, pruned after `router.payload_retention_days`. Created in R2a, because the card is stored there from R2a on.<br>• `plan_presentations` plus the attempt binding (§5).<br>• Outcome join v2 (§5.4).<br>• The CHECK extension (`plan_interrupt`), as one table rebuild in R2a |
| **The staged frame composing Today's plan blocks** (the P4 cutover extended to Today) | • DL1's `PlanPolicy(source, chooser)` (`engine.py:150-189`). The router's policy is selected in the sidecar's `_env` (DL1 deviation 1, `docs/reviews/daily-loop-dl1.md:453-456`; `learnloop_sidecar/handlers/daily_plan.py:97-116`).<br>• P4 pieces: the constraint engine (`scheduling/constraint_engine.py:301`, `:326`); the ladder (`staged_policy.py:216-286`); `ladder_eligibility` (`:294-367`); `IRREVERSIBLE_RUNGS` (`:289-291`).<br>• The P2 bridge `controller_cutover.py:134-319`, which has no production caller. The desktop calls `GPR.advance` directly (`learnloop_sidecar/handlers/golden_path.py:260-276`; `GoldenPathScreen.tsx:225`) | • `router/staged_frame.py`: `StagedFrameSource`. It wraps `legacy_lanes_v1`'s packing, the P4 constraint engine per item, per-candidate ladder annotations, irreversibility and plain reasons (§3.1).<br>• The P2 bridge wiring (§5.5) |
| **The learner-facing "why"** | • `BlockChoice.why` / `why_kind` (`types.py:153-162`), surfaced by `view.py:89-97` and rendered in `DailyPlanView.tsx` `PlanBlockLine` (`:71-95`).<br>• Today's reasons carry lane prefixes (`lanes.py:315-346`).<br>• The staged `_why_copy` is jargon: "{action} on {ref} because {staged_rule}" (`staged_policy.py:1040-1048`) | `router/why.py`, plain copy built from reason codes (§7). A ◇ model-written label, evidence links, and copy deny-list tests |
| **Kill switch `router.enabled`** | The switch table exists in the spec (`spec_daily_loop_v1.md:631-638`). Parity tests already cover the router-on rows with a fake chooser (`tests/test_daily_plan_kill_switch.py`; spec `:781`, `:805`) | The switch itself; the policy selection in `_env`; the successor gates; G8 on fixture copies |

---

## 3. Design decisions this plan makes

### 3.1 The staged frame on Today (the source, and the staged component)

**The problem.**
- The P4 ladder picks one canonical action per *commitment* (`staged_policy.py:191-199`, `:222-223`).
- Its live signals are commitment-scoped (`state_signals.py:45-80`).
- Three of its rungs' inputs (pending triage route, fragile capability, failing integration) are caller-supplied and default to off (`state_signals.py:178-192`). Only five signals are derived live (`:15-28`).
- A Today plan spans many LOs, and most of them are under no commitment.
- The plan never plans `assess_terminal` or depth edges (`spec_daily_loop_v1.md:438`).

**Proposal.** Use the P2 cutover's own rule: under identical inputs the staged path is decision-equivalent to the incumbent, unless a named constraint or EVSI reason vetoes (`controller_cutover.py:1-12`, `:101-117`, `:189-204`).

**`StagedFrameSource`** (`staged_frame_v1`):
1. **Candidates.** It takes DL1's packing unchanged (`lanes.py:350-463`), over the pool VOI v2 has already admitted. VOI decides the probe set before `decide()`: `serving/voi-stopping:src/learnloop/daily_plan/engine.py:583-663`, `:493-580`.
2. **Constraint veto.** For each candidate's items it runs `ce.feasible_set` (`constraint_engine.py:326`) against one bounded `ControllerSnapshot` per boundary. The snapshot builder's query budget is independent of the number of candidates (`controller_snapshot.py:269-286`).
   - An item a hard constraint refuses is dropped before packing.
   - The constraints are: active, stimulus renderable, purpose, hard exposure, assessment reservation, fatigue, same-facet dispersion and stage interleaving (`constraint_engine.py:121-290`).
   - The refusal is logged as a typed exclusion with its named reason, in `exclusions_json` under `named.<constraint key>`.
3. **Annotations.** Each candidate carries:
   - `ladder`: the rungs eligible for its LOs, from per-LO signals derived from lane classification plus the five live adapters;
   - `reversible`: false when the block contains an item whose serve burns a reserved assessment surface or opens a cold administration. The reserved-surface case is the P4 rule (`constraint_engine.py:196-208`); the cold-administration case needs a new predicate built from the existing cold-administration check. **Verify the exact predicate at stage start.**
   - `reason_code`: the source of the plain "why", §7.
4. **The staged component's argmax** (`staged_v1`) is `lane_quota_v1` over the staged-feasible candidates (`daily_plan/chooser.py:36-74`).
   - In `staged` mode, ties go through `epsilon_tiebreak` as spec §7.3 says: candidates sharing the top lane-quota key whose planner values fall within `EPSILON_TIE_MARGIN`. The draw is seeded from the snapshot hash and the decision id, and its exact propensity is logged.
   - Otherwise the choice is deterministic (p = 1).

**Why not order by the ladder?**
- It would change Today's block order (repair and diagnosis first, maintain last) on the strength of signals the code doesn't derive on Today.
- It would measure the models against a rule nobody serves today.

With lane quota as the staged component, the replay compares the models against the real incumbent, and G8 parity stays simple. The ladder still matters in three ways: it annotates candidates, it gates the irreversible ones, and it feeds the card. Owner Q1.

**Two parity jobs before relying on the ladder:**
- Add a parity test between `ladder_eligibility` and `evaluate_staged_rule`. They are two copies of the ladder (`docs/reviews/router-r1-codex-review.md:287-292`).
- Use VOI v2's `voi_stopping.robust_quantile` (0.25) wherever the frame calls `rank_feasible`. The staged selector uses 0.10 (VOI report §7.7). Under Q2's default (no diagnostic blocks), the frame never calls it.

**Diagnostic blocks: not in R2 (owner Q2).**
- VOI v2 decides in-episode probes per observation: it withholds them at queue build, refuses at the commit door, and stops after each answer (`serving/voi-stopping:src/learnloop/diagnosis/voi_stopping.py:1903`; `scheduler.py:531-549`; `probe_episodes.py:1364`).
- A staged `measure_diagnostic` block, ranked by `staged_policy._select_diagnostic` (`:573-627`), would add a second decider over the same probes, at a different quantile.
- So R2 keeps probes where the lanes put them and annotates rung 3 only.

### 3.2 The router chooser and the engine seam

1. **Construction per env.** `_env` (`learnloop_sidecar/handlers/daily_plan.py:97-116`) builds `PlanPolicy(source_name="staged_frame_v1", make_source=StagedFrameSource.factory(vault, repository, snapshot cache), chooser=RouterChooser(vault, repository, session_id, clock, prefetch_cache), projection_chooser=LaneQuotaChooser())` when `router_active(vault)`. That function is true when the version is in `ROUTER_VERSIONS`, `plan_active` holds and `router.enabled` is on.
   - The protocol `choose(state, feasible)` stays unchanged. Everything else comes through the closure.
   - The projection chooser stays `lane_quota_v1` (DL1 F3: `engine.py:150-160`; `docs/reviews/daily-loop-dl1-codex-review.md:80-91`). Projected later blocks are therefore lane-quota projections, labelled "about" as today.
   - The other entry points that build `PlanEnv` (`handlers/daily_plan.py:279`; `handlers/reader.py:1501`; the CLI) go through one helper: `daily_plan.policy.policy_for(vault, repository, ...)`.
2. **One row, inside the block's transaction.**
   - Add `BlockChoice.router_record: Mapping[str, Any] | None = None` (`types.py:153-162`). The chooser fills it with the mixture weights, both model distributions, sensor answers, the seed, the card hash, the similar-decision ids, the question-set version, model ids, latency, cost, `fallback`, and the payload ids to write.
   - `_boundary` copies it into `PlanBlockDecision.detail` (`engine.py:1263-1284`). The plan_block logger, extended in `plan_log.py`, writes the row on the block's own connection (`engine.py:1320-1341`). The payload rows are written in the same transaction.
   - The chooser **never** writes rows itself. A model call happens inside `decide()`, which runs before the transaction opens (`engine.py:1253` versus `:1320`). So a block that fails to persist leaves no orphaned decision, and no lock is held during network calls.
   - R1's rule that "a chooser that set `decision_ref` logs its own row" (`plan_log.py:263-264`) remains for compatibility, but R2 doesn't use it.
3. **The closed choice still guards.** The engine already refuses unknown or infeasible ids, `continue_current` at a boundary, and a malformed propensity or why kind, falling back to `lane_quota_v1` (`engine.py:1055-1077`, `:1099-1114`). R2's selection is restricted to the feasible top-k before sampling, so this guard is G1's backstop, not its mechanism.
4. **Learner picks** go through `learner_pick` (`engine.py:1944`) as `learner_pick` blocks with no propensity. That is G9, unchanged.

### 3.3 Selection math (`model_mixture`)

1. **Feasible set.** It is the container's (`engine.py:1043-1053`). `stop_for_today` is included when `stop_offered` holds (`:1053`). `continue_current` never appears at a boundary.
2. **Irreversible first.** If the staged argmax is irreversible (§3.1 item 3), it is chosen deterministically (p = 1, `policy = staged_v1`). The models' probabilities for irreversible candidates are logged and can't select (§7.1, G2).
3. **Top-k reversible** (`router.k = 6`, D3), in a deterministic order: the staged argmax first; then each lane's best remaining candidate, in lane-quota order; then the rest, by the lane-quota key; then `stop_for_today` if offered.
   - Feasible candidates beyond k are logged with propensity 0. R3 evaluates on top-k support only, and that limit has to be documented.
4. **Distribution.** π = (1 − k·ε)·(w_s·δ_staged + w_d·p_decider + w_l·p_llm) + ε, with ε = `router.epsilon_min` = 0.02. Mixing with uniform keeps every top-k candidate at ε or above and the propensity exact.
   - The randomization layer's dormant 0.05 floor (`randomization_layer.py:47`) must not clip this; `model_mixture` documents its own floor.
   - With the defaults, k·ε = 0.12.
5. **A two-stage draw**, so the "why" can name which draw chose the block (§7.4).
   - The seed is `hash(snapshot_hash, decision id)`. The first draw picks uniform with probability k·ε, otherwise a component by weight. The second draw picks a candidate from that component's distribution.
   - The marginal is π, and the logged propensity is π(chosen). G3 recomputes it.
   - The row also logs `drawn_component ∈ {staged, decider, llm, uniform}`, which is display-only.
6. **Fallback.**
   - A component that times out, errors or is refused for spend gives its weight to staged for that decision, and `fallback = decider | llm | both` is set.
   - With both models down, π = (1 − k·ε)·δ_staged + ε. Recommended: keep the floor on fallback too, so support never collapses.
   - Owner sub-question in Q7: the spec says "the staged choice is used" with both down, which would make the choice deterministic.
7. **`ties_only`** (default false, D1). It applies the mixture only when several candidates share the staged argmax's lane-quota key. Planner values are not comparable across lanes (`lanes.py:420` is `1/(1+rank)`, and VOI v2 makes it `order_rank`, `serving/voi-stopping:src/learnloop/daily_plan/lanes.py:502`), so a cross-lane δ margin would not be honest.
8. **Mode `staged`.** `w_s = 1`. The models are still asked, for logging and sensor scoring (spec §7.3). This mode is R2a's only mode until R2b lands; in R2a no model is called at all.

### 3.4 Timing

- The engine's prefetch is `advance(serve=False)`, which already makes the boundary decision while feedback shows (`engine.py:1808-1817`). The router uses `router.prefetch_timeout_seconds` there (recommended 45). Blocking waits use `router.timeout_seconds` (8; spec §8).
- **The first block.** UX Phase 1 makes Begin call `start_session` and then `next_plan_item(serve=true)` (`ux/phase1-first-run:apps/learnloop-tauri/src/screens/TodayScreen.tsx:641-656`). That puts the first decision's model latency on the Begin click.
  - Recommended (owner Q9): Today calls `next_plan_item(serve=false)` when it mounts with an open plan, without a session.
  - This is safe because outcomes bind through presentations (§5), not sessions.
  - If the decision hasn't finished when Begin is pressed, Begin waits up to 8 s, then takes the staged choice with `fallback` flagged.
- The Decider's provider default is 30 s (`ai/providers/decider.py:61`). The router passes its own timeout.

### 3.5 The restraint gate on Today (G4)

- At a plan boundary nothing is in progress, so `intervene_now` has nothing to gate.
- The plan's one mid-block interruption is `_insert_followups`: a follow-up from this session's answer joins the **current** block and displaces its tail (`engine.py:1674-1757`).
- R2c makes that a router decision of kind `plan_interrupt`:
  - **candidates:** `insert_now` (allowed only when the follow-up rules place it, so it can never be forced) and `continue_current` (the follow-up waits and is forced into the next block, as the `current is None` path already does, `:1690-1700`);
  - the same mixture: staged = `insert_now`, the Decider's P(yes) and the LLM's P(yes) on `intervene_now`.
- That keeps spec §7.2's asymmetry without the spec's hand-set 0.3 threshold. The owner has rejected hand-set thresholds for the Decider (the facet span-support note in the merge-queue notes). Owner Q7.
- VOI v2 decides *whether* a follow-up is worth serving (`followup_value_decisions`). The restraint decides only *now or at the boundary*. They compose and do not overlap.

### 3.6 `LearnerStateCardV1`

- **Typed fields**, as in spec §4:
  - the session from `PlanState` plus `ReentryGap`;
  - per candidate LO: `placement.predictor.active_predictor` (`placement/predictor.py:164`) for the mean and interval; untested, assumed or demonstrated; FSRS R; the evidence summary;
  - 7-day interaction signals;
  - intent from `IntentView`.
- **Text sections:**
  - recent graded work, reusing the V3 renderer's history with a past-only cutoff;
  - open hypotheses, including open learner-text gaps and unresolved cause factors;
  - retention risks and explicit unknowns;
  - self-reports.
- **Leakage rules** (G5). Each is a test:
  - no `reference_solution` or answer key;
  - nothing from `teaching_exclusions` or `held_out_spans`;
  - after the sources track, any source text goes through `model_reader_withheld` (`merge/sources-onto-main:src/learnloop/source_retrieval/corpus.py:457`) and `exam_withheld` (`:310`);
  - nothing about a candidate item beyond its LO, minutes and kind (no stems of unattempted items);
  - a grade held for review renders as "held for review", never as a score (`held_grades.py:49`).
- **After the sources merge,** imported exercises are ordinary practice items with a key status (`merge/sources-onto-main:src/learnloop/db/stores/source_service.py:148`, `:309`). The card states "answer key not verified" where that applies.
- **Budget and hash.** The token budget is `router.card_token_budget` = 16,000 (D8). The truncation order is: older successes first, then older excerpts; typed fields are never dropped. The card hash goes on the row (`card_hash`) and in the receipt label `state_hash` (`ai/execution.py:38`).
- **Read-only CLI** for the owner: `learnloop router card --vault V --decision ID` prints the stored card, from R2a on.

### 3.7 `decision/context` retrieval (R2c)

- **The recipe.** A canonical rendering of the decision's typed state: the candidates' LOs and their statuses, the error families present, the session phase and re-entry. It is a DB recipe, following `diagnosis/split/embeddings.py`.
- **When it embeds.** A decision's vector is written after the decision, off the hot path. The *current* decision's query vector is computed at prefetch.
- **Maturity filter** (G5). It needs outcomes observed before the decision time, from a different session. `router_outcomes` is a cache that only `learnloop rebuild` refreshes (`docs/reviews/evsi-calibration.md:690-693`). So retrieval derives outcomes on the fly for the shortlisted past decisions (`router/outcomes.py:564`), as `learnloop router log` already does (`docs/reviews/router-r1.md:281-282`).
- **MemDelta discipline** (spec §5). Each decision flips a logged coin (`router.similar_include_rate = 0.5`) for whether the models see similar decisions. R3 can then compare with and without on the same policy, because a replay can never re-ask.
- **Gating.** It needs `embedding.enabled`, which defaults to off. Without it, retrieval is a logged no-op (`similar: disabled`).

---

## 4. Collisions with in-flight work, and the order they imply

| Work | Files and decisions it shares with R2 | What R2 must do | Order |
|---|---|---|---|
| **VOI v2** (`serving/voi-stopping`) | **Files:**<br>• `daily_plan/engine.py`: `_select_requests` `:460`, `_usable_probe_minutes` `:479`, `_classified_pool` `:493-580` (build / refresh / chip, with `record=` plumbing), `_project_probe_admission` `:583-663`, `voi_decisions` on the block detail `:1448-1452`, `advance_with_context` `:2006`, `set_minutes` `:2301`.<br>• `lanes.py:317-346`, `:502` (`order_rank` → `planner_value`).<br>• `router/plan_log.py:217-220`, which copies `voi_decisions`.<br>**Decision:** admission is deterministic and happens before `decide()`. Probes are decided per observation | • The staged frame consumes the admitted pool and never re-decides probe admission (§3.1).<br>• Keep `voi_decisions` on the `plan_block` row. The propensity is conditional on that deterministic admission, so log it.<br>• Keep `BLOCK_MAX_MINUTES` and the lane semantics: admission relies on `redistribute` handing maintain its idle minutes (VOI report §7.3).<br>• Use `voi_stopping.robust_quantile` for any `rank_feasible` call.<br>• Composition check at stage start: a planned probe refused at the commit door (`serving/voi-stopping:src/learnloop_sidecar/handlers/practice.py:353`) must resolve in the plan and leave an unbound presentation, not a stuck block | R2 after VOI v2 (queue) |
| **Decider migration** (not started; merge-queue notes, "OWNER-APPROVED … Decider migration") | **Files:** `ai/routing.py` (`DECIDER_TASKS` `:88`, fallback resolution `:234-238`, `:496`), `ai/decisions.py`, `ai/providers/decider.py`, `ai/disclosures.py`, and the agreement report.<br>**Decision:** tier-1 routes default to the Decider with an LLM fallback | • `router_decider` must keep **no** chat fallback. Its failure moves weight to staged. Add a test that the migration's generic fallback helper never applies to `router_decider`.<br>• Reuse any typed-question helpers the migration adds.<br>• The agreement report gets a router adapter. It reads `model_distributions_json` / `sensor_answers_json` (argmax agreement, P(yes) agreement) instead of duplicating rows into `judgment_ledger` | R2 after the migration (queue) |
| **UX Phase 1** (`ux/phase1-first-run`) | • `engine.py` `reading_from_furthest_active` `:114-124`, `_prepare_plan` `:652`.<br>• `reading.py:62-152`.<br>• `TodayScreen.tsx` begin and pick without a session (`:520-537`, `:641-656`).<br>• `App.tsx` `beginSession` (`:475-495`).<br>• The reading-step successor placeholder (`algorithm_versions.py:107-119`). R1 conflicts are recorded as Q-I (`docs/reviews/ux-phase1.md:171`) | • The source consumes `next_reading_target` as built.<br>• The first-block prefetch (§3.4) is one frontend call in `TodayScreen`.<br>• The why stays inside the existing why toggle (`DailyPlanView.tsx:71-95`); UX Phase 3 restructures Today after R2 (`ux_learnloop_v1.md:1343-1350`).<br>• The copy deny-list (`ux/phase1-first-run:apps/learnloop-tauri/src/copy/denyList.ts:19-69`) gets a server-side twin for R2's why strings | R2 after UX Phase 1. UX Phase 3 after R2b (it needs model "why"s to design around) |
| **Sources track** (`merge/sources-onto-main`) | **No daily_plan or router file changes.**<br>• Proposals are not plan candidates (`merge/sources-onto-main:docs/specs/spec_source_practice_and_probes_v1.md:360`). A proposal pick is a `learner_pick` block via `plan_learner_pick(proposal_id, …)` (`handlers/daily_plan.py:264-310`), and `record_proposal_delivery` stores the block's `decision_ref` (`:302-310`).<br>• The `router` caller and tool kinds are pre-built (`source_retrieval/policy.py:23`, `:88-89`; `instructional/tools.py:57-59`, `:121`, `:355-388`; `migrations/192_source_tool_calls.sql:11`).<br>• `mvp-0.18`: unverified-key attempts earn no certification credit (`algorithm_versions.py:164-180`).<br>• `source_need_selection` forecasts carry no chosen item (`instructional/needs.py:159-170`)<br>• Spend: `service_spend` envelope `source_retrieval/service_spend.py:310`; `SERVICE_OWNER_KINDS` `db/stores/source_service.py:588-589` | • Learner-pick blocks keep their `decision_ref` semantics, because the delivery receipt points at it.<br>• Card: key status, plus `model_reader_withheld` for any source text.<br>• Outcomes: record `reference_status` as a covariate, and count unverified-key grades for R_next/R_cold (owner Q13).<br>• R2 leaves sources' §10.6 deferred wiring alone (`tool_requests`, `find_practice` within blocks, reading blocks ranked against gaps with **their own successor**, `:938-953`). That is a follow-up (§6).<br>• R2 uses its own spend owner kind and envelope, not the source service's | Sources lands first (queue) |
| **Facet locks + reword confirm** (`merge/facet-locks`) | **No code overlap:** the diff on `daily_plan`, `router` and `scheduling` is empty (facet-locks report §4). The reword confirm card lives in Registry / Proposals, not Today. It records D14/D15 and §15.5/§15.6 in the router spec (`docs/specs/spec_action_router_v1.md:451-479` on that branch) | Carry the spec text forward. §15.5 and §15.6 are not in R2 (§6) | — |
| **Held grades / proof fold-in** (`grading/route-check-in-grader`) | `outcome_contract.grade_is_held` (`:126`), `held_grades.held_for_review_attempts` (`:49`). Router outcomes already exclude held attempts (`router/outcomes.py:160`, `:182-193`) | • The presentation-bound join keeps the exclusion: a held action attempt is *taken*, but its grade is no outcome until resolved.<br>• The card shows "held for review".<br>• The proof fold-in deletes the item-kind reading and the re-derivation but keeps the predicate. No R2 change | — |
| **EVSI calibration** (main) / **multisim** (`evsi/calibration`) | `evsi_calibration/live_report.py:179-205` `_staged_attempt` → `no_attempt_binding`; `VOI_SITES` (`scheduling/voi_forecasts.py:51-57`) | R2a's receipt replaces `no_attempt_binding` with an exact join (§5.3). `live_report` gains a presentation adapter, and the report version moves | Multisim lands before R2 (queue). No overlap beyond the CLI help snapshot |
| **R1** (main) | `plan_log.py`; `outcomes.py:364-377` (the session rule); `today_head_served` (`learnloop_sidecar/handlers/queue.py:347`) | Extend; don't fork. Section 5.4 covers the session rule | — |
| **Learner-text gaps** (main) | Migration 182 tables; the reasons in `lanes.py:330-335` | Open gaps go into the card as open hypotheses and unknowns. Their check copy maps to plain "why"s | — |
| **T6 output budget** (main) | `ai/output_budget.py:70`, `:148`; the Decider is exempt (`:33`) | `router_llm` runs inside `TruncationRetry(output_budget(config, "router_llm", provider=…))`, with `ai.route_output_tokens.router_llm` set to 4,096 by default (owner Q5) | — |

---

## 5. The Today cutover (D13) and the exact receipt chain

### 5.1 Today

- **Switch on, at the R2a successor** (`router.enabled = true`):
  - `_env` selects `staged_frame_v1` with `staged_v1` (R2a), or with `RouterChooser` (R2b).
  - Every block is a `plan_block` row with `mode = staged | mixture` and `policy = staged_v1 | router_mixture_v1`. The `mode` column has no CHECK (`migrations/181_router_decisions.sql:24-26`).
- **Switch off, or a predecessor version:** DL1's pair exactly (G8; `spec_daily_loop_v1.md:633-638`).
- With `plan.enabled = false`, the router has nothing to fill (spec `:636`).

### 5.2 The exact chain: decision → presentation → attempt

**Today's chain** (main):
1. The decision row: `receipt_key = plan_block:<block>` (`plan_log.py:219`). `chosen_practice_item_id` is the block's first planned item (`:173`). `chosen_scheduler_candidate_id` is NULL (`:239`).
2. The block: `attention_blocks.decision_ref` holds the row id (`engine.py:1339-1341`, `:1180`).
3. The serve: `item_served` events carry the item, the session, and a scheduler candidate id from that call's own build (`engine.py:1881-1899`).
4. The attempt: a submit binds to that candidate through `bind_submission_offer` (`db/stores/collection.py:99-170`).

The outcome join doesn't use any of this. It takes the first attempt on the chosen item at or after the decision in the same session (`router/outcomes.py:364-377`). That is R1's **session rule**.

**R2a adds** (one migration):
- **`plan_presentations`** (RAW_LEDGER, append-only triggers). Columns:
  - `id`, `block_id`, `router_decision_id`, `controller_decision_id` (nullable);
  - `practice_item_id`, `position`, `origin`;
  - `scheduler_candidate_id`, `probe_presentation_id` (nullable, when the item is a committed probe presentation);
  - `session_id`, `served_at`.

  The row is written in `_serve`, in the same transaction as the `item_served` event (`engine.py:1883-1899`). It is unique on `(block_id, practice_item_id)`. The plan step DTO returns `presentation_id` (`_item_step` `engine.py:1763-1779`, extended).
- **`practice_attempts.plan_presentation_id`**: nullable, with a partial unique index. This mirrors `probe_presentation_id` (`migrations/028_probe_episodes.sql:113-116`; `attempts/attempts.py:167`, `:1324`).
  - The submit and draft RPCs accept `plan_presentation_id`.
  - Validation: same item, same vault, not consumed.
  - **On mismatch the attempt still submits, unbound, with a warning.** Binding never fails a submit, the same rule as R1's pick logging (`collection.py:150-170`).
  - The frontend passes `step.presentationId` wherever it passes `step.schedulerCandidateId` today (`TodayScreen.tsx:525` and the practice open path).
- **The `router_decisions` CHECK extension** (`plan_interrupt`) goes in this migration, so the append-only table is rebuilt once. R1 already flagged that a later CHECK change means a table rebuild (`docs/reviews/router-r1.md:541-544`). Migration 175's rebuild of `judgment_ledger` is the precedent.
- Roles: `plan_presentations` is RAW_LEDGER and `router_decision_payloads` is WORKFLOW, both in `db/table_roles.py`. The head fixture is renamed and the references regenerated, per CLAUDE.md.

**The chain:** `router_decisions.id` → `attention_blocks.decision_ref` → `plan_presentations.block_id` (and `router_decision_id`) → `practice_attempts.plan_presentation_id`.

**Learner picks** (`engine.py:1944`) and proposal picks (sources) get presentations the same way, so a pick's outcome binds exactly too.

### 5.3 Staged forecasts (owner Q10: exact receipts)

- `_staged_attempt` (`evsi_calibration/live_report.py:179-205`) follows this path: the forecast's `decision_ref` (a `controller_decisions.id`) → the `router_decisions` row whose `controller_decision_id` matches → that row's block → the `plan_presentations` row for `forecast.chosen_practice_item_id` → the bound attempt.
- **Statuses:** `presented_unanswered` (pending, right-censored) and `not_presented`.
- **The session rule is never used for a forecast** (Q10, option a).
- **Who fills `controller_decision_id`:**
  - for Today, the staged frame, whenever it persists a controller decision (only if Q2 is reversed);
  - for P2, the bridge (§5.5).
- **Tests use a staged decision that commits diagnostic work through a fake `DiagnosticSelector`.** No production caller passes one today (`docs/reviews/evsi-calibration.md:666-669`). So the chain is proven before any real staged forecast exists.

### 5.4 R1's session rule: retired where an exact receipt exists, kept as a labelled fallback

- **`router/outcomes.py` `_action_attempt` precedence** (`outcome_version` moves to `router_outcomes_v2`):
  1. **Presentation:** the decision's block's first bound presentation (`action_binding = presentation`). The action is what the learner was actually served first, not the first planned item.
  2. **Scheduler candidate:** R1's offer and pick binding (`action_binding = candidate`).
  3. **Session rule:** R1's rule (`action_binding = session_rule`). It stays for pre-R2 `plan_block` rows, for `staged_p2` rows, and for attempts made without a presentation id (an older client, the TUI, which keeps DL0's queue per DL1 deviation 11).
- `action_binding` becomes a `router_outcomes` column (DERIVED, so the one replayer rebuilds it).
- R3 must report the binding mix and may exclude `session_rule` rows.
- G6 holds: zero model calls, deterministic on two rebuilds. The existing test with model constructors forbidden extends to this.

### 5.5 The P2 bridge (D13)

- **Wiring.** `golden_path.advance` (`learnloop_sidecar/handlers/golden_path.py:260-276`) calls `controller_cutover.advance_live` (`:266-319`) when `router.enabled` is on and the version is R2a's or later.
- **When the requested state is not the canonical successor.** The client passes `to_state`; the bridge resolves the canonical successor (`:153`). If they differ, the request is the learner's explicit choice. It goes through `choose_block(explicit_choice=…)` (`staged_policy.py:397-408`) and is logged as a learner pick.
- **On a staged veto** the RPC returns the deferral (`advance_live` already writes the marker artifact, `:283-309`). `GoldenPathScreen` shows it in plain words (one sentence).
- **Logging and binding.** `_log_staged_decision` already writes `staged_p2` rows (`controller_cutover.py:207-263`). Their outcome binding stays R1's session rule (§5.4) until P2 practice opens write presentations, which is out of scope.
- **Scope.** P2-owned items stay out of the plan, through the existing staged-owned exclusion in `build_due_queue`. Folding P2 runs into Today's plan is a separate decision (owner Q10).
- **Switch off:** `GPR.advance` is called directly, exactly as today.

---

## 6. §15.5 (surface-gap signal) and §15.6 (exam and problem-set rigor): R2 follow-ups

- **§15.5** (`merge/facet-locks:docs/specs/spec_action_router_v1.md:454-469`).
  - Its spec trigger is "after S1 lands and R2 is live". The owner queue says "the router decides, with or after R2".
  - It needs canonical exercises as surfaces of the same practice family (S1), the held-out exclusion, typed evidence in the card, and new candidate actions:
    - probing with more source exercises;
    - proposing a refined facet through the confirm path;
    - hardening the generated family.
  - Two of those actions are content operations, not plan blocks.
- **What R2 itself does for §15.5:**
  - the card's typed-evidence registry (§3.6), so the `surface_gap` section drops in without changing the card version scheme;
  - `BlockCandidate.action` stays open-ended, so "more source exercises" becomes an ordinary candidate later.
- **What a follow-up stage ("R2-S") does.** It runs after R2b is live and S1 is on main. Merging it with sources' §10.6 deferred wiring fits, because both share the trigger "R2 live and S4 merged" (`merge/sources-onto-main:docs/specs/spec_source_practice_and_probes_v1.md:938-953`):
  1. compute the signal (failed canonical exercise, passed generated surfaces of the same facets, never `held_out_evaluation`);
  2. add it to the card;
  3. add the probe-more candidate;
  4. route refine / harden proposals to the facet confirm path and PF generation as non-plan actions.

  That stage needs its own successor, as reading-block ranking does.
- **§15.6** (`:471-479`) is not a router change. It is PF generation's next revision plus S1's exercise selection. The queue places it after the exam-protection stage. R2's only contact is G5: the card never reads held-out units.

---

## 7. The learner-facing "why"

**Rules** (`docs/specs/ux_learnloop_v1.md`):
- the `why?` pattern: a short plain paragraph, with `details ▸` inside (`:253`);
- the why of each block is behind `why? ▸`, and lanes are not named on the surface (`:685-698`);
- model-written text carries ◇ (`:1461`);
- no probabilities, IDs or versions on the surface (`:239`);
- the glossary hides probe, EIG, lanes and similar terms (`:1273`, `:1291-1298`);
- the frictionless principle.

**What each block's `why?` says.** It is built by `router/why.py` from the candidate's `reason_code`, not from the prefixed lane strings (`lanes.py:315-346`, which stay as the logged `reason`).

| Who chose | `why_kind` | Copy (examples) |
|---|---|---|
| **The rule** (staged) | `computed` | • "Questions from last week, before they slip."<br>• "A fix for the mix-up from Tuesday."<br>• "Following up this morning's mistakes on eigenvectors."<br>• "Next: §5.5 Mixtures."<br>• "A step toward your midterm."<br>• "To check you still know this, without hints."<br>• The cold check copy is UX's "to see whether last week's fix held" (`:717`) |
| **The Decider** | `model_no_rationale` | D7 verbatim: "LearnLoop's model picked this among 4 close options," followed by the rule's reason for this block. The number is a count of options, not a probability |
| **The LLM** | `model_written` | "◇ {rationale}", labelled as written by LearnLoop's model. Evidence ids render as links: "your answer to Exercise 5.14 on Saturday" |
| **A uniform draw** (the ε floor) | `computed` | "Picked to vary the order today," followed by the rule's reason (owner Q12) |
| **Fallback** | as staged | Same as the rule. `details ▸` adds: "The model didn't answer in time, so the usual rule chose." |
| **Learner pick** | `computed` | "Your pick." (as today, `engine.py:2051`) |

**`details ▸`** holds the receipts: which component drew, the propensity, the model ids, the decision id, and the owner command `learnloop router log --decision`. It's collapsed by default (`:256`).

**Guards:**
- A server-side deny-list test covers every string `why.py` can produce: lane names, probe, EVSI, facet, LO, mvp, propensity, Decider, staged, queue, due and the rest of UX §9.
- The LLM's rationale is prompted for plain words and no jargon.
- A rationale that hits the deny-list, or cites an evidence id not on the card, is not shown. The block shows the Decider-style label and the rule's reason instead, and the raw text stays in the payload and `details ▸`. This keeps honest labels while protecting the learner's copy.

**Where it shows.** Only in the existing why toggle of `PlanBlockLine` (`DailyPlanView.tsx:71-95`) and in the block DTO (`view.py:89-97`, `why` / `why_kind`). The ◇ glyph is added for `model_written`. The Today restructure (plan sentence, no lane names) is UX Phase 3's, after R2.

---

## 8. Versioning, gates, replay, spend, privacy

### 8.1 Successors and switches

**Successor A** (R2a): `ROUTER_STAGED_FRAME_ALGORITHM_VERSION`, a placeholder relabelled at merge.
- The chain is linear. Successor A means every predecessor's features plus the staged frame on Today, plus the D13 bridge.
- Projection is unchanged (another tag on the mvp-0.8 namespace). `rebuild --shadow` reports 0/0/0 on fixture copies, the same check R1 recorded.
- `upgrade_to_<label>` chains from LATEST.

**Successor B** (R2b, plus R2c if they land together): `ROUTER_MIXTURE_ALGORITHM_VERSION`. `router.mode` defaults to `mixture` at B and to `staged` at A.

**Config** (modelled defaults, kept out of the 80-line template):

| Key | Default | Notes |
|---|---|---|
| `router.enabled` | true | The kill switch |
| `router.mode` | staged (at A) / mixture (at B) | |
| `router.weights` | {staged 1/3, decider 1/3, llm 1/3} | |
| `router.k` | 6 | |
| `router.epsilon_min` | 0.02 | |
| `router.ties_only` | false | |
| `router.timeout_seconds` | 8 | |
| `router.prefetch_timeout_seconds` | 45 | |
| `router.card_token_budget` | 16000 | |
| `router.similar_decisions` | true | Needs `embedding.enabled` |
| `router.similar_k` | 6 | |
| `router.similar_include_rate` | 0.5 | |
| `router.sensor_source` | decider | |
| `router.restraint` | true | |
| `router.max_daily_cost_usd` | 1.00 | Metered routes only |
| `router.payload_retention_days` | 365 | |

**Existing keys:** `router.log_decisions` and `router.probe_tie_admission` are unchanged. Defaults snapshots are recomputed for every version.

### 8.2 G1–G9 as tests

Each gate is written to fail first, against a fake chooser or a fixture copy.

| Gate | Test (new file) | Fail-first setup |
|---|---|---|
| **G1** Infeasible can't win | `test_router_g1_feasibility.py` | • A fake Decider (`choice` all on an infeasible id) and a fake LLM (an unknown id) can't select it. The LLM's unknown id is rejected at parse.<br>• The staged frame drops an item refused by a hard constraint, and the refusal is logged under its named reason |
| **G2** Irreversible never sampled | `test_router_g2_irreversible.py` | A fixture with a block containing a reserved or cold-check item: chosen only as the staged argmax with p = 1; π = 0 when it isn't the argmax, whatever the models say |
| **G3** Exact propensities | `test_router_g3_propensity.py` | • π(chosen) recomputed from the logged weights and distributions equals the logged propensity.<br>• The seed reproduces the two-stage draw.<br>• Every top-k candidate is ≥ ε.<br>• A failed component's weight goes to staged.<br>• The `exact` / `deterministic` CHECKs hold (`migrations/181_router_decisions.sql:67-71`) |
| **G4** Restraint asymmetry | `test_router_g4_restraint.py` | • `insert_now` exists only when the follow-up rules place the follow-up.<br>• The models can defer, never force.<br>• Off, behaviour is DL1's `_insert_followups` |
| **G5** No leakage | `test_router_g5_card_leakage.py` | • A planted reference solution, an unattempted reserved stem, a held-out span, an exam-role span and a held grade never appear in the card text or JSON.<br>• Similar decisions are only those matured before the decision time, in another session |
| **G6** Replay | Extend `test_router_outcomes.py` | Zero model calls on rebuild (constructors forbidden); `router_outcomes` v2 deterministic over two rebuilds; the presentation join |
| **G7** Fallback | `test_router_g7_fallback.py` | Timeout, error, `DecisionResponseInvalid` and a spend refusal each fall back to staged, flagged on the row |
| **G8** Kill switch | Extend `test_daily_plan_kill_switch.py` | • `router.enabled = false` at A and at B equals the predecessor on fixture copies (block sequence and every `block_chosen` detail except ids).<br>• The `plan.enabled = false` rows are unchanged |
| **G9** Learner pick wins | Extend `test_router_g9_picks.py` | A pick logs `learner_pick` with no propensity; a proposal pick (sources) keeps its `decision_ref` |

**Also:**
- the receipt chain (`test_router_presentations.py`), including binding refusals that never fail a submit;
- the EVSI adapter (`test_evsi_staged_binding.py`);
- the D13 bridge (`test_router_p2_bridge.py`);
- the why deny-list (`test_router_why_copy.py`);
- the Decider request shape and typed parsing against a fake endpoint, and LLM renormalization and evidence-id validation (spec §12 test list);
- card determinism and budget truncation;
- `ladder_eligibility` / `evaluate_staged_rule` parity;
- the durability lane under production pragmas, for both new tables.

### 8.3 Replay and rebuild

| Table | Role and replay behaviour |
|---|---|
| `router_decisions` | RAW_LEDGER. Never re-run |
| `router_decision_payloads` | WORKFLOW. Pruned after the retention window; hashes stay on the row |
| `plan_presentations` | RAW_LEDGER |
| `practice_attempts.plan_presentation_id` | Attempt metadata. Not evidence: it changes no grade or projection |
| `router_outcomes` | DERIVED, with one replayer, extended |
| `voi_forecasts` | RECEIPT. Untouched |
| `decision/context` vectors | A cache. Replay never needs them, because `similar_decision_ids_json` is stored on the row |

- **Rebuild never re-asks a model** (spec §9). The replay has to score staged, Decider and LLM from the logged distributions alone. That is why R2c randomizes retrieval inclusion rather than re-asking later.
- **The plan's own replay rule holds:** estimates, the split and the plan never write evidence, and replay never reads them (`engine.py:24-28`).

### 8.4 Spend

- **The Decider.** About $0.0004 per decision (spec §6.1). It's estimated on input only (`ai/providers/decider.py:211`) and exempt from the output budget (`ai/output_budget.py:33`).
- **The LLM.**
  - It uses `router_llm`, resolving to the active provider (`ai/routing.py:242-273`), which is Codex on the subscription by default (D9).
  - Subscription routes are uncapped: caps are not enforced (`ai/spend.py:178-185`), and the sources branch reserves $0 for them (`merge/sources-onto-main:src/learnloop/ai/spend.py:473-474`).
  - Metered routes run under `TruncationRetry(output_budget(...))` with a route budget of 4,096 tokens (Q5).
- **Daily admission.** Main has no daily dollar admission; every existing daily cap counts calls (substrate report §3). R2b adds `router.max_daily_cost_usd` on metered spend:
  - It follows `reader/reader_quick_check.py:228-345`'s atomic reservation in the start-receipt observer.
  - It sums today's `model_call_receipts` cost for `owner_kind = router_decision`, plus the reserved estimate.
  - A refusal is a G7 fallback.
  - It is separate from the source service's envelope. The OpenRouter key limit is the backstop, per the owner's 2026-10-13 direction for sources.
- **Receipts.** `model_call(..., purpose="router_decision", labels judge=decider|llm, question_set_version, state_hash=card hash)` (`ai/execution.py:38-43`, `:246`).
- **No `--dry-run`?** Spec §6.2 asks for one on every batch command; R2's only batch command, the `decision/context` backfill, gets it.

### 8.5 Privacy (D6)

- **What leaves the machine.** Learner text (card excerpts, answers, gaps, tutor questions) goes to OpenRouter, then Perplexity, and to the LLM route's provider. The owner accepts text leaving the machine, but checks Perplexity's retention terms before R2. Don't request `data_collection: "deny"` unless a compliant provider is listed (spec `:207`).
- **What R2b changes:**
  - `ai/disclosures.py:29-33` currently says "Nothing is sent yet". It gets live text.
  - The Settings health chip stops skipping `router_decider` / `router_llm` when the router is on (`learnloop_sidecar/context.py:520-525`).
  - Readiness moves from key-present (`ai/runtime.py:136-157`) to the free endpoint probe (`ai/providers/decider.py:260`).
- **R2b does not merge** until the owner has recorded D6.

---

## 9. Sub-stages

### R2a: staged frame on Today, exact receipts, the card

**Scope:**
- `router/staged_frame.py` (`StagedFrameSource`, `staged_v1`);
- `daily_plan/policy.py`: policy selection, used by every `PlanEnv` builder;
- `BlockChoice.router_record` and its copy in `_boundary`;
- the `plan_block` row builder extended for `mode = staged`, the ladder annotations and the constraint exclusions;
- the migration: `plan_presentations`, `practice_attempts.plan_presentation_id`, `router_decision_payloads`, and the `router_decisions` rebuild for `plan_interrupt`;
- `_serve` writes presentations;
- the step DTO and submit/draft RPC parameters, plus the frontend pass-through;
- outcomes v2 (§5.4) and the `live_report` adapter (§5.3);
- the D13 bridge wiring;
- `router/card.py`: built at each boundary and stored in payloads;
- `router/why.py` for computed reasons;
- `learnloop router card`;
- successor A; `router.enabled` and `router.mode`.

**Gate:** G1 (constraints), G2, G5, G6, G8, G9; the receipt chain, the EVSI adapter, the bridge, why copy, card determinism and ladder parity. Full suite, plus `-m durability`, `lint-imports`, and the references regenerated.

**Fail-first tests to write first:**
1. A staged forecast committed through a fake selector reports `no_attempt_binding` on main. After R2a it joins its bound attempt.
2. Under R1, an attempt on the second planned item, made after a skip, is mis-bound by the session rule. After R2a it binds by presentation.
3. A hard-exposure item is served in a DL1 block today; under A it is refused with its named reason.
4. `golden_path.advance` bypasses the bridge today.

**Manual runs** (backup-API copies under `fixtures-local/`):
- `upgrade`, then `rebuild --shadow` (expect 0/0/0);
- 60 seeded sessions comparing A with switch-off: veto counts per constraint, and block sequences identical where no veto fires;
- one boundary with its card printed, and the card read for leakage by eye.

**Out of scope:** model calls, the mixture, retrieval, restraint, and diagnostic blocks.

### R2b: both models live, the mixture

**Scope:**
- `router/requests.py` (`router_qs_v1`, `router_llm_v1`);
- `router/chooser.py` `RouterChooser`: top-k, the mixture, the two-stage draw, fallback, prefetch caching per boundary snapshot hash, and timeouts;
- `model_mixture` registered (`randomization_layer`, `ROUTER_DESIGNS`);
- spend admission (§8.4); the `router_llm` output budget;
- payloads holding both raw responses;
- model "why"s with ◇ and evidence links, plus the rationale guard;
- disclosures, readiness and the health chip;
- the Today first-block prefetch call (one frontend change);
- the agreement-report adapter for the Decider migration's report;
- successor B, with `mode = mixture` as its default.

**Gate:**
- G1, G3, G7 and G9 under the mixture; G8 at B;
- the request shape against a fake endpoint (the 400 on unknown fields, typed parsing); LLM renormalization and unknown-id rejection; evidence-id validation;
- the spend cap; the subscription route uncapped;
- the Decider never falling back to chat.

**Fail-first tests:**
1. A fake LLM returning an unknown id is rejected at parse (no parser exists today).
2. The logged propensity is reproducible from the logged components (G3).
3. A timeout reaches staged with `fallback = llm`.

**Manual runs:**
- Copies with fake models, then **one owner-run live session**: real Decider plus Codex, spend-capped, on a copy, with latency recorded per component.
- Cost per decision measured.

**Precondition:** D6 recorded.

### R2c: restraint, sensors, retrieval

**Scope:**
- **Restraint.** The `plan_interrupt` decision at `_insert_followups` (§3.5), with its own request, a single `intervene_now` noul per model.
- **Sensors.** `teach_first_<lo>` and `will_pass_next_<lo>`, added to the boundary question set (`router_qs_v2`) and logged only.
- **Teach-back summary (§15.1).** An LLM summarizer whose output enters the card as typed evidence with its source attempt. It is post-grade, async, and joins the next card.
- **Retrieval.** `decision/context` DB recipe, embedding after the decision, prefetch query embedding, the maturity filter derived on the fly, the inclusion coin, and a backfill CLI with `--dry-run`.

**Gate:**
- G4 and G5 (retrieval maturity);
- G6 (vectors never needed by replay);
- G3, still exact with the inclusion coin logged;
- restraint off equals R2b.

**Fail-first test:** today a follow-up always joins the current block. With a fake Decider P(yes) near 0, it waits for the boundary with an exact propensity.

**Lands with R2b** under B (recommended), or alone under C.

---

## 10. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | **Latency.** Codex turns, the 30 s Decider default and OpenRouter embeddings (p50 4.5 s) can exceed 8 s, so the LLM component is starved and fallbacks are frequent | Decide at prefetch with 45 s. The first block is prefetched at Today open. Embeddings run off the hot path. Report fallback rates per component in the stage review. Owner Q4: a faster metered LLM if Codex starves the mixture |
| 2 | **The staged component's meaning** (§3.1). The P4 ladder signals are not derived per LO on Today | `lane_quota_v1` over the P4-feasible set (Q1). The ladder is annotation only, with a parity test (`router-r1-codex-review.md:287-292`) |
| 3 | **Top-k truncation.** OPE has no support outside the top-k | Log every feasible candidate with π = 0. R3 evaluates on top-k support and reports it |
| 4 | **The candidate set moves** between boundaries (VOI admission, follow-ups, picks) | Propensities are conditional on the logged candidate set, and the `voi_decisions` context stays on the row. That is acceptable for OPE when logged |
| 5 | **A row written outside the block transaction** would orphan decisions | `BlockChoice.router_record` and in-transaction logging (§3.2). The chooser never writes |
| 6 | **The receipt chain depends on the client** passing `presentation_id` | Fall back to the session rule, labelled (§5.4). R3 reports the binding mix. The TUI stays unbound |
| 7 | **The append-only table rebuild** for the CHECK change | Do it once in R2a, with the migration 175 precedent; integrity and FK checks; the durability lane |
| 8 | **The 16k default output reservation** against a $1 metered cap | Route budget of 4,096 tokens (Q5) |
| 9 | **Model rationale with jargon, or wrong claims** about the learner | Prompt rules, the deny-list guard, evidence ids validated against the card, ◇ label, rationale behind `why?` only |
| 10 | **D6 unresolved** | R2a ships without it; the R2b merge is blocked |
| 11 | **Evaluation power.** About 3–6 decisions per session, so 200 decisions take weeks | Fixed by design: no shadow wait. R3's switching rule handles "can't tell" (spec §10.4) |
| 12 | **The Decider's alpha endpoint** (`/alpha/decisions`) could change | It fails closed (`ai/decisions.py:273`), and fallback moves weight to staged (G7) |
| 13 | **UX Phase 3** may redesign the why surface | R2 keeps the why behind the existing toggle, and the copy lives in `why.py`, which Phase 3 can call |

---

## 11. Owner questions, each with a recommended default

| # | Question | Recommended default |
|---|---|---|
| Q1 | What is the "staged" component on Today: P4 ladder order, or DL1's `lane_quota_v1` over the P4-feasible set (the P2-bridge rule)? | `lane_quota_v1` over the P4-feasible set. The ladder annotates, gates irreversibles and feeds the card |
| Q2 | Should the staged frame compose `measure_diagnostic` blocks ranked by staged EVSI? | No. VOI v2 stays the single authority on probes. R2 builds the receipt, so any future staged forecast binds exactly |
| Q3 | One successor for R2, or two (staged frame / mixture)? | Two. R2a lands without D6, and R2b+c share B |
| Q4 | Which model for `router_llm`, and with which timeouts? | The active provider (Codex on the subscription); 45 s at prefetch, 8 s blocking. Revisit if the stage review shows LLM fallback above about 20% |
| Q5 | What output budget for `router_llm`? | `ai.route_output_tokens.router_llm = 4096` |
| Q6 | What daily cap for the router? | `router.max_daily_cost_usd = 1.00` on metered spend only. No per-decision cap; subscription routes uncapped; the OpenRouter key limit is the backstop |
| Q7 | Restraint: the spec's hand-set 0.3 gate, or a logged mixture over {insert now, wait for the boundary}? And when both models fail at a boundary, keep the ε floor or use the staged choice deterministically? | The mixture, with no threshold. Keep the floor on full fallback |
| Q8 | Should retrieval randomize, per decision, whether similar decisions are shown? | Yes: 50%, logged. It is the only way R3 can test MemDelta without re-asking |
| Q9 | When is the first block decided: at Today open (prefetch, no session), or on Begin (up to 8 s)? | At Today open, with Begin falling back to staged after 8 s |
| Q10 | D13: should a `golden_path.advance` whose `to_state` differs from the canonical successor be the learner's explicit choice? And should P2-owned items stay out of the plan? | Yes, and yes |
| Q11 | D6: may R2b merge before Perplexity's retention terms are recorded? | No. R2a may |
| Q12 | What copy for an exploration-floor draw? | "Picked to vary the order today", followed by the rule's reason |
| Q13 | Unverified-key attempts (sources S1): are they router outcomes? | Yes, with `reference_status` recorded as a covariate. R3 decides |
| Q14 | §15.5 and sources §10.6: should they be one follow-up stage ("R2-S") after R2b is live and S1/S4 are on main? | Yes, with its own successor |
