# Adaptive difficulty and mastery: practice in the band, probes that discriminate, levels that mean something (v1)

**Status:** drafted 2026-10-14 at the owner's request, on branch `docs/adaptive-difficulty-spec` from main `4108e1ccd` (`mvp-0.24`). Spec only: no code changes. Decision-ready: every owner decision in §15 has a recommended default, which is accepted unless the owner overrides it at its checkpoint (owner decision 2026-10-12).

**Research appendix:** `docs/specs/research/adaptive_difficulty_sources_v1.md`. It holds the six research angles, every source with its verdict, the verification log, and the local measurement (appendix §4, summarized here in §3.3). Bracketed keys in this spec, such as `[watson2017]`, name rows of that appendix. Every external source cited here was opened at its primary record (DOI registry, arXiv abstract page, proceedings page or the paper itself) and its title and first author checked; anything that could not be verified was dropped.

**Relationship to other specs:**
- `spec_learner_field_v1.md`: this spec adds an arm family to its harness (§7.2), follows its constraints F1–F8 and its switching rule (§7.4), and reuses its interaction signals (§3.1).
- `spec_action_router_v1.md` and `plan_router_r2_v1.md`: the router keeps choosing blocks; this spec chooses the item and its feature point inside a block, after the router's draw and only among items the chosen block admits, and logs exact propensities that compose with the router's (§10.1). It answers router §15.6 (exam and problem-set profiles seed difficulty and rigor).
- `spec_daily_loop_v1.md` §6: the plan container keeps its minutes, lanes, new-material admission and reconciliation. AD substitutes one admitted new-lane item for another inside a planned slot, within those rules (§10.1–10.2).
- `spec_measurement_efficiency_v1.md`: certification keeps its ledger, its caps and its delayed cold probe (§5.7); this spec records each credited observation's feature point beside the ledger, so a cell can be demonstrated *at a point* (§9).
- `spec_probe_eig_redesign.md`: probes keep their hypothesis EIG, value-of-information stopping and likelihood identity; this spec changes what goes into the conditionals of capability hypotheses, amending two of that spec's rules explicitly (§6.3), and how probe items are authored.
- `spec_storage_sync_v1.md` (branch `docs/storage-sync-spec`, not yet on main), §6.12 and requirement R13: the opt-in contribution export that n>1 priors would come from (§13).
- `docs/algorithm-change-playbook.md`: every serving change here is a successor with a kill switch (§11).

---

## 0. Summary

**The question.** When a learner answers easily, is that because they are skilled or because the item is trivial? A single response cannot tell. LearnLoop today mostly does not try. Its item difficulty is a number the authoring model writes after being told the band it should hit (§3, G1). The certification ledger gives the same credit to a heavily scaffolded item as to an exam-level one at the same capability (G4).

**The answer this spec builds.**
1. **Difficulty is a property of a feature point, learned from this learner's own history.** An item's difficulty is `b = (effect of its task features) + (an item offset with wide uncertainty)`. Feature effects are shared across items, so they can be learned from one learner (explanatory IRT, `[fischer1973]`, `[deboeck2008]`). The offset of a one-off item cannot be learned, so it is integrated out, never estimated (§5).
2. **The learner state is a posterior over ability per (facet, capability) cell, on the same scale as the feature ladder.** It changes as the learner learns. Updates are deterministic and replayable, with zero model calls (§5.6).
3. **Practice is chosen to land in the band.** Inside a block the router has already drawn, the rule serves, among the items that block admits, the one with the highest posterior probability that this learner's success chance lies in 70–80%. When no item in the cell can, it commissions one at the feature point most likely to. Near-ties and a small exploration share are randomized with exact, logged propensities (§6.1). The LLM writes a surface *at* the commissioned feature point and is no longer asked to hit a difficulty (§7).
4. **Probes are chosen to discriminate.** They keep the existing hypothesis EIG and stopping rules. The item offset's uncertainty is folded into each hypothesis's predictions, and probe authoring targets feature points where hypotheses disagree, not a 45–55% band (§6.3).
5. **Every forecast is logged before the attempt and scored after it.** This covers the model in use, the incumbent, and outside forecasters (solver panel, an LLM given the item, an LLM and the Decider given the learner's history). Trust in each is learned from proper scores. Item-side signals enter the item-offset prior with learned weights. Forecasts that already read the learner's history compete as experts and are never folded in a second time (§8).
6. **Certification says "demonstrated up to level k".** Credit counts only from items at or above the level, judged by the features of the revision the learner answered and its audit. The evidence is stored by feature point, not by level number. A level is always a level of one goal's ladder, and a requirement or certificate records the feature point it needs, so a new exam or milestone never changes what an existing one means. The features of practice-available exam and problem-set units define a goal's top level, "full mastery". Held-out exams are never served and never steer practice (§9).
7. **It ships in phases**, starting with logging that changes nothing served (AD1). The model follows as a gated harness arm with a-priori constants (AD2). It is promoted by the harness's own rule before it chooses anything (AD3). Levels follow in AD4 and probe targeting in AD5. Each serving change is a successor with a kill switch (§14).

**The honest limit, stated once.** One learner's history cannot separate "skill rose" from "items at this feature level are easier than assumed" when feature levels rise in step with time. The design reduces the confound by randomizing feature points across time, reports it when it remains, and never presents a per-item difficulty as measured (§5.8).

---

## 1. The owner's framing (binding) and what this spec takes from it

From the owner's request (2026-10-14):
- **A point difficulty is only an intermediate.** The deliverables are:
  1. **practice** items that improve the learner's skill, targeted at the desirable band (about 70–80% chance of success for *this* learner);
  2. **probes** that discriminate between live hypotheses, or elicit the most information for the next action.
- **Difficulty comes from this learner's traces:** history, cold and warm retrieval, hints, timing, optional ratings (easy / about right / hard, one tap, optional) and other variables. It does not come from an LLM labelling difficulty with no context.
- **Exam or problem-set questions can seed difficulty, best as the target** that defines "full mastery" where a vault has them. Held-out exam text is never served; only its features are used.

The direction agreed in conversation was evaluated against the research (§4.2). Most of it survives. Four parts change:
- the target becomes the expected response at a feature point (R1);
- the state becomes dynamic (R2);
- forecasts that already read the learner's history become competing experts rather than item-offset priors (R7);
- probes get their own objective, and calibration a bounded one (R4).

---

## 2. Standing constraints

| Id | Constraint | Source |
|---|---|---|
| A1 | **Derived and replayable.** Every posterior, score and level is rebuilt from ledgers, receipts and vault content, with zero LLM or embedding calls. | field F1; ADR-003 table roles |
| A2 | **Never evidence.** The model is a predictor. It never writes `grading_evidence`, mastery, facet recall, FSRS state or certification credit. Levels (§9) come from the observation ledger and the item's audited features, never from the posterior. | field F2; `goal_certification.py:1-15` |
| A3 | **Live changes through the playbook.** Each serving change is an immediate successor with a kill switch that restores the predecessor exactly, plus receipts. | playbook steps 1–8; field F3 |
| A4 | **Honest labels, generous defaults.** Untested, assumed, predicted and demonstrated are always distinguished; nothing predicted is shown as demonstrated (Ready vs Demonstrated, KM §9.6). | field F4; `exam_readiness.py:1-20` |
| A5 | **No per-learner-fitted hyperparameters; no hand-picked evidence weights.** Prior means and variances are set a priori and versioned (`ad_priors_v1`). Every effect that weighs an observation (feature effects, warmth, learning rate, trust in each outside signal, rating and timing links) is latent state with such a prior, learned with uncertainty. The few fixed measurement constants (§5.5) are versioned and swept in the harness. | field F5; owner 2026-10-14 |
| A6 | **Knowledge-model alignment.** No propagation along `part_of`, `related`, `analogous_to` or `confusable_with`. Sharing across LOs (feature effects, capability offsets) steers a live decision only after the harness shows held-out support. | field F6; KM §8.1, §8.3 |
| A7 | **Biased sampling is declared.** Every served item records its serving origin. Every randomized choice logs seed and exact propensity before selection. | field F7; `randomization_layer.py:1-25` |
| A8 | **Exam protection.** Held-out exam and problem-set units are never served. They are never quoted to any AD prompt (generation, feature audit, forecasting). They never update learner state, and they never steer selection, generation or the ladder (router §15.6). Where the existing ingest inventory already gives them feature tuples, those tuples feed one evaluation-only report (§9.5). | `exam_material.py:25-60`; ingestion §4.2, §8.5; router §15.5–15.6 |
| A9 | **Never blend.** AD's predictions change neither well depth nor the demonstrated beads. A level is a label beside them, never a second depth. | field F8; `apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx:8-26` (one continuous quantity owns the geometry; Demonstrated is a discrete marker) |
| A10 | **Asking for help is never penalized in the record.** Hints change the outcome category of one observation (§5.3). They never reduce certification credit beyond the existing unassisted rule, and never write extra evidence. | field G13 |

---

## 3. The current mechanism and its gaps

### 3.1 What exists (re-checked in this worktree at `4108e1ccd`)

- **Where item difficulty comes from.** Practice generation inverts the mastery channel's 2PL link at the learner's estimated ability. It turns the target success interval into a difficulty band (`content/authoring/practice_generation.py:2133-2149` `_difficulty_for_success`, `:2152-2182` `success_band_difficulty`, called at `:403-410`), with bands from config (`config/schema.py:398-399`: practice `(0.70, 0.85)`, probe `(0.45, 0.55)`). The authoring prompt then tells the model to "Calibrate each item's difficulty to its target's recommended_difficulty_band (~70-85% expected success) … and set difficulty and difficulty_source='llm_estimate' accordingly" (`practice_generation.py:1919`; also `practice_generation.py:1062`, `:1922`). For probes it says "Set difficulty within the recommended_difficulty_band: it lies on the learner's boundary (~50% expected success)" (`practice_generation.py:1984`).
- **How difficulty reaches the learner model.** `item_irt_params` maps the stored `difficulty ∈ [0,1]` to `b = 2.5·(2d − 1)` (`learner/mastery.py:356-378`). `resolve_item_irt_params` is "the single seam" through which the mastery EKF, surprise and prediction read it (`:381-397`). Primed attempts subtract a fixed `priming_b_offset = 2.0` (`config/schema.py:156-162`; `attempts/attempts.py:3402-3410`).
- **Empirical difficulty is dark.** An empirical-Bayes update of `b` exists (`mastery.py:400-447`) but ships disabled (`config/schema.py:163`). The config comment gives the reason: "theta and b are confounded at N=1" (`:150-155`). A monitor flags items with one-sided residuals after 5 attempts (`learner/calibration.py:1-7`, `:39-99`).
- **The solver panel.** For practice-family variants it sets a per-variant offset from the panel's solve rate *relative to the parent item's difficulty*, or 0.5 when the parent has none (`ops/pf_generation.py:183-198`). LLM self-labels are never requested there (`:37-42`).
- **Depth rungs.** A rung is one capability plus one task-feature point (`curriculum/depth_rungs.py:1-16`, schema `p1_launch@1`, `substrate/activity_patterns.py:71-89`). It is chosen by a mastery-band ladder with fixed cut points (`depth_rungs.py:228-307`) and an "optimism" step of one rung when evidence is thin (`:310-319`). A diagnosed hypothesis can override it (`:323-333`). The prompt is told that "Difficulty varies WITHIN the waypoint" (`practice_generation.py:1922`).
- **Prediction in serving.** On a canonical-state vault, an LO with blueprints predicts item success by a noisy-AND over component recall with slip and guess (`scheduling/selection_rewards.py:419-457` → `learner/blueprint_projection.py:370-392`). Item difficulty does not enter. Selection rewards an item by its fit to a target band per intent: practice `(0.55, 0.75)`, probe `(0.40, 0.60)`, repair `(0.75, 0.90)`, transfer `(0.60, 0.80)` (`selection_rewards.py:516-526`).
- **Certification.** Credit for one observation is its pseudo-mass if the observation is direct or embedded and unassisted, else zero (`learner/capability_mapping.py:246-266`). Credit accrues per `(facet, capability)` (`substrate/canonical_projection.py:920-950`). A cell is demonstrated at credit ≥ 1.0 (`goals/certification.py:1-7`; `goals/goal_certification.py:85-101`). A delayed cold probe per certified LO measures `false_certification_rate` (`goals/certification_cold_probe.py:1-40`; success at correctness ≥ 0.8, `:197`).
- **Learner difficulty reports.** An "easier/harder" request writes a self-graded `self_report` attempt at 0.3 evidence mass. It moves mastery, facet recall, the capability ledger and FSRS (`content/authoring/rung_variants.py:1-22`). A "too easy / too hard" retirement writes an LO claim at a fixed level (`content/authoring/item_authoring.py:317-365`).
- **Other signals.** `practice_attempts` records `hints_used`, `primed`, `latency_seconds` and a 1–5 pre-answer `answer_confidence` (`attempts.py:175`; mapping at `field/types.py:75`).
  - **Hints keep only their total.** Ordinary hints have no timing; the field's own judge is told so (`field/probability_states.py:98-101`). Only tutor questions log when help came (`question_events.attempt_progress`, `no_draft` or `draft_started`; read at `field/signals.py:351-359`).
  - **Latency is a time cost, never ability evidence.** It sizes the daily plan (`daily_plan/estimates.py:1-18`), the minutes of value-of-information stopping (`diagnosis/voi_stopping.py:421-449`) and the cost of an unresolved misconception (`scheduling/unresolved_cost.py:10-17`, `:131-145`). Probes log it as an observation feature only (`diagnosis/probe_episodes.py:2551-2560`).
- **Forecasts.** `attempt_surprise` holds a predicted score distribution but is DERIVED and recomputed (`db/table_roles.py:76`). Exams freeze item predictions (`goals/exam_calibration.py:1-15`). The field harness scores arms offline and prequentially (`spec_learner_field_v1.md` §7.2), and the T8 success-head arms are offline only (`field/success_head.py:1-15`). There is no per-presentation forecast receipt.
- **Exam profiles.** They carry task-family, capability, representation, format and point/time counts (`content/synthesis/exam_profile.py:57-80`), but no task-feature target.

### 3.2 Gaps

| Id | Gap | Consequence |
|---|---|---|
| G1 | **Difficulty is the requested band, echoed.** The model is told the band and asked to set `difficulty` inside it (`practice_generation.py:1919`). | The stored number mixes the learner estimate that produced the band with the model's view of the item. Feeding it back as `b` is circular. |
| G2 | **The one place difficulty is learned from outcomes is dark,** for a correct reason (θ and b confounded at n=1). | No mechanism learns anything about difficulty from this learner. |
| G3 | **The canonical prediction path is blind to item difficulty** (`blueprint_projection.py:370-392`). | A trivial item and a hard item on the same recipe get the same predicted success. The band fit in selection cannot tell them apart. |
| G4 | **Certification is blind to the item's feature point within a capability** (`capability_mapping.py:246-266`). | An unassisted success on a cued, near-recall item at `procedure_execution` earns the same credit as an exam-level one. This is "answered easily because the item is trivial". |
| G5 | **Four inconsistent target bands,** none logged as a forecast or checked against outcomes (`schema.py:398-399`; `selection_rewards.py:516-526`). | Generation aims at 70–85% while serving aims at 55–75% for the same intent. Nobody knows which is hit. |
| G6 | **Rung selection is a fixed threshold ladder** with a one-step optimism heuristic (`depth_rungs.py:228-319`). | There is no posterior, no information criterion and no propensity, so off-policy evaluation of rung choice is impossible. |
| G7 | **Learner reports are hand-weighted evidence** (0.3 mass; fixed claim levels) (`content/authoring/rung_variants.py:1-22`; `content/authoring/item_authoring.py:317-365`). | This conflicts with A5. A report counts as evidence with a weight nobody learned. |
| G8 | **No forecast receipt per presentation** (§3.1, Forecasts). | Trust in the solver panel or an LLM forecaster cannot be learned from live serving, only offline. |
| G9 | **Solver-panel difficulty is relative to a parent** whose own difficulty may be an LLM label (`pf_generation.py:183-198`). | The panel's information is a relative offset, which is right, but it is stored as an absolute number. |
| G10 | **Hints, priming and timing enter as fixed adjustments** (`priming_b_offset = 2.0` "provisional"; hint dampening `attempts.py:4461`). Latency is not evidence. | Ceiling effects go unaddressed. When most answers are correct, correctness alone says little about the margin, and the time taken or a rating could. |
| G11 | **No full-mastery target** (`exam_profile.py:57-80`). | The router §15.6 direction (exams seed rigor) has no level to aim at. |
| G12 | **The cited design doc does not exist.** `learner/mastery.py:1` and `learner/calibration.py:1` cite `spec_irt_difficulty.md`, which is not in `docs/`. | The IRT seam is undocumented. §5 of this spec documents its successor. |

### 3.3 Measurement on a backup copy (committed snapshot)

On backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the three working vaults *as committed at `4108e1ccd`*. That snapshot is dated 2026-08-16 and is at `mvp-0.8`, so it is two months stale. Aggregates only; the method is in the appendix.

| Vault | Items | `difficulty_source` | Items with `task_features` | Graded attempts (excl. self-report) | Items attempted once / ≥2 | Full-credit share |
|---|---|---|---|---|---|---|
| `linear_algebra` | 99 | `llm_estimate` 97, `author` 2 | 96 | 62 | 47 / 7 | 0.74 |
| `probability` | 77 | `llm_estimate` 46, none 31 | 46 | 2 | — | — |
| `arxiv_v2` | 32 | `llm_estimate` 1, none 31 | 32 | 0 | — | — |

**`linear_algebra`, first unassisted and unprimed attempt per item vs its LLM `difficulty` label (n = 53):**
- Spearman ρ = **−0.60** overall (approximate 95% interval −0.75 to −0.39, Fisher z). Harder labels went with lower first-attempt correctness.
- Within capability, the residual correlation is **−0.42** (approximately −0.63 to −0.16).
- Per capability: retrieval −0.30 (n = 33), schema_interpretation −0.67 (n = 11), procedure_execution −0.30 (n = 5), method_selection −0.87 (n = 3).
- Coverage: latency on 18% of attempts, `answer_confidence` on 47%, hints on 3%, primed on 0%.

**What this says.**
- In this learner's own data, the echoed labels carried real ordinal information. That differs from the population result that LLM Easy/Medium/Hard labels predicted empirical difficulty at ρ = 0.06 `[an2026]`.
- The labels were written with the learner's band in context (G1), so part of what they encode is the learner estimate, not only the item.
- The data are one learner, two months old, mostly retrieval items, and near ceiling (74% full credit).
- Both readings point the same way: **neither trust nor discard the label; learn its weight** (§7.3, α_llm).
- The same measurement on the current working vaults was not run in this stage (§17, Q1). AD1's `learnloop ad data-check` reproduces it.

---

## 4. Research synthesis

Six Codex research workers with live, unrestricted web search covered six angles:
- (a) QUEST/QUEST+/Psi and Bayesian adaptive psychometrics;
- (b) Bayesian optimal experimental design;
- (c) explanatory IRT and item generation;
- (d) desirable difficulty, curriculum bandits and knowledge tracing;
- (e) LLM difficulty estimation and conditioned generation;
- (f) n=1 identifiability, pooling and forecast scoring.

121 sources were verified (appendix). What follows is what they change.

### 4.1 Findings and the design changes they force

**R1. Target the family expected response at a feature point, not a point difficulty.**
- **Findings.**
  - Random-item IRT treats items as draws from a population and models unexplained item variation `[deboeck2008]`; LLTM with an error term does the same for feature-based difficulty `[janssen2004]`, `[fischer1973]`.
  - Item-cloning CAT chooses a family, then a random member `[glas2003]`.
  - The *family expected response function* summarizes "the probability of a correct response to an item randomly generated from an item family" `[sinharay2003]`.
  - Generating items during testing requires propagating item uncertainty into person estimates `[embretson1999]`.
  - On-the-fly generation is feasible, but imperfect equivalence within item models costs precision `[bejar2003]`.
- **Change.** The band applies to `p̄(x)`, the expected success over items generated at feature point `x` for this learner's state (§5.7). It does not apply to a point estimate for one item. The realized item is re-forecast before it is served (§7.4).

**R2. The learner changes during practice, so the state must be dynamic.**
- **Findings.**
  - QUEST/QUEST+/Psi assume a fixed observer `[watson1983]`, `[watson2017]`, `[kontsevich1999]`.
  - Work that measures perceptual learning makes the threshold trial-dependent `[zhang2019]`.
  - Dynamic IRT models growth as a state-space process `[wang2013]`, `[wilson2016]`.
  - Glicko propagates uncertainty for changing abilities `[glickman1999]`.
  - Adaptive training of a learning animal separates state estimation, learning dynamics and training utility `[bak2016]`.
- **Change.** Cell abilities carry a learning increment per graded opportunity and variance growth with time (§5.6). QUEST+ contributes its finite candidate enumeration and expected-utility selection, not its stationarity.

**R3. Nuisance parameters get "the attention they deserve, no more, no less".**
- **Findings.**
  - Psi-marginal keeps a joint posterior but selects stimuli by information gain on the parameters of interest only `[prins2013]`.
  - Lapses bias threshold and slope estimates `[wichmann2001]`, and freeing a lapse parameter alone does not remove the bias `[prins2012]`.
  - Adaptive designs induce small-sample bias, especially in slope `[kristensen2022]`.
- **Change.**
  - Feature effects, item offsets and outside-signal weights are nuisance for calibration selection (§6.2).
  - Lapse is a fixed small constant.
  - Slope (`a`) is fixed at 1 in v1; per-family slopes are deferred (§16).
  - Calibration of the whole adaptive loop is checked by simulation under the actual selection policy (AD2).

**R4. Practice and probes need different objectives; one POMDP could unify them, later.**
- **Findings.**
  - Bayesian design is expected utility, and different purposes need different utilities `[chaloner1995]`, `[rainforth2024]`.
  - Mutual information between competing models is the right probe objective `[cavagnaro2010]`, `[myung2013]`, `[cavagnaro2011]`, `[houlsby2011]`.
  - EVSI is right when the downstream decisions are known `[strong2015]`.
  - When the target is a prediction rather than all parameters, use targeted designs `[vanlier2012]` and expected predictive information gain `[bickfordsmith2023]`.
  - Teaching as a POMDP unifies diagnosis and instruction under one long-run objective `[rafferty2016]`.
  - A fixed weighted sum of information and band proximity has no principled exchange rate (worker b).
- **Change.**
  - Practice maximizes the posterior probability of being in the band (§6.1).
  - Probes keep hypothesis EIG and VOI stopping with item-offset uncertainty integrated (§6.3).
  - Calibration (when the posterior is too wide to target) maximizes information about the cell's ability, but only among items whose predicted success is acceptable (§6.2).
  - POMDP planning and amortized design policies `[foster2021]`, `[ivanova2021]` are deferred (§16).

**R5. The 70–80% band is a defensible engineering default, not a law.**
- **Findings.**
  - The "85% rule" is derived for gradient-descent learners on binary classification `[wilson2019]`.
  - Math Garden samples items at a mean success probability of .75 `[klinkenberg2011]`.
  - In a geography practice system, targets of 5–50% error showed easier questions better for short-term engagement and harder ones better for long-term engagement and learning `[papousek2016]`; see also `[papousek2015]`. That paper summarizes the Math Garden success-rate experiment as finding the easiest condition best for learning, mediated by the number of tasks solved `[jansen2013]`.
  - 50% is the information-optimal point for measurement, not learning `[eggen2006]`.
  - Desirable difficulties improve durable learning only while the learner can succeed with effort `[bjork2011]`.
- **Change.**
  - Keep the owner's 70–80% band.
  - Define success precisely (§5.3).
  - Evaluate by delayed cold outcomes, not immediate success (§10.4).
  - A band experiment is deferred with a trigger (§16).

**R6. What n=1 identifies.**
- **Findings.**
  - A response identifies an ability–difficulty *relationship*, not two quantities `[chen2021]`.
  - With unrestricted skill, `β' = β + v, θ'_t = θ_t + x_t·v` leaves every success probability unchanged (worker c).
  - Longitudinal designs need overlap and invariant anchors `[fu2016]`, `[le2026]`.
  - When an Elo system selects items adaptively from current ratings and updates item difficulties alongside abilities, the rating variance inflates artificially and the ratings do not converge `[bolsinova2025]`.
- **Change.** §5.8: the honest confound statement, randomized feature overlap, diagnostics, and no per-item difficulty presented as measured.

**R7. Outside estimates: item-side signals are priors; learner-conditioned forecasts are competing experts.**
- **Findings.**
  - Context-free LLM difficulty labels: ρ = 0.06 on 311 deployed questions `[an2026]`.
  - Systematic human–AI misalignment that model scale does not fix `[li2025]`.
  - Moderate ranking but systematic underestimation on 1,031 ENEM items `[brant2026]`.
  - Supervised text models barely beat a constant on USMLE difficulty: best RMSE 0.299 vs 0.311 for the baseline `[yaneva2024]`, `[bulut2024]`; see also the reviews `[benedetto2023]`, `[alkhuzaey2023]`.
  - Simulated solvers do better: up to r = 0.75/0.76/0.82 with NAEP when weaker models role-play classrooms `[acquaye2026]`; ρ up to 0.594 with floor and ceiling effects at the size extremes `[isophys2026]`. Model respondents have narrow ability distributions and are not humans `[liu2025]`, `[heyueya2024]`. Aligned simulators need human data `[scarlatos2025]`, `[hoyl2026]`.
  - History-conditioned LLM forecasting is plausible but unvalidated for this setting `[li2024fskt]`, `[srivastava2021]`, `[halawi2024]`.
  - Verbalized confidence needs recalibration `[tian2023]`, `[xiong2024]`.
  - Robust priors keep a vague component so conflict with history is survivable `[schmidli2014]`.
- **Change (to the agreed direction).**
  - Item-only signals (the LLM label, solver-panel offsets, an item-only LLM forecast, the item's source origin) enter the item-offset prior as a regression whose weights are latent and learned (§7.3).
  - A forecast that already read the learner's history (LLM or Decider given the card) is *not* folded into the item offset. Doing so would count the learner's history twice. It is logged, scored and weighted as a competing expert (§8.4).

**R8. Trust is learned from proper scores, and fit is not policy.**
- **Findings.**
  - Strictly proper scoring rules (log, Brier) separate calibration from sharpness `[gneiting2007]`.
  - Anytime-valid confidence sequences compare sequential forecasters without distributional assumptions `[choe2023]`.
  - Stacking `[yao2018]` and fixed-share expert weighting `[herbster1998]` combine forecasters chronologically.
  - Feature-rich logistic models are competitive with deep KT and should be checked for calibration `[gervet2020]`.
  - Fit statistics are a biased measure of a knowledge tracer's quality as a policy `[rachatasumrit2024]`.
- **Change.** §8.3–8.4, and promotion gates that include decision-level checks (band-hit rate, delayed cold success, false certification), not only log loss (§10.4).

**R9. Observations beyond correctness.**
- **Findings.**
  - Partial credit improves knowledge-tracing prediction over binary outcomes `[wang2013pc]`.
  - Math Garden scores accuracy and response time together `[klinkenberg2011]`.
  - Response time with accuracy supports mastery stopping `[sapountzi2021]`.
  - Transparent feature models (LFA/AFM, PFA, DAS3H, LKT) share history across unique items through skill and context features `[cen2006]`, `[pavlik2009]`, `[choffin2019]`, `[pavlik2021]`.
  - Per-item KT parameters `[pardos2011]` need repeated items.
  - Elo is a cheap baseline `[pelanek2016]`.
- **Change.**
  - The outcome is ordinal: fail, partial or help-adjusted success, and unassisted success (§5.3).
  - Rating and timing are separate sub-arms that must earn activation; they are never counted as extra votes (§5.4).
  - KT-IDEM-style per-item parameters are rejected.

**R10. Generate to a specification, audit, then re-forecast.**
- **Findings.**
  - Cognitive design systems and item models ground features in solution processes `[embretson1998]`, `[embretson2001]`, `[gierl2012]`, `[gierl2013]`.
  - Controllable generation can hit observable task demands `[jiao2023]`, `[wang2023skillqg]`, `[bi2024]`, but controlled demand is not personal difficulty (worker e).
  - State-conditioned generation's headline target control was judged by a KT model, not by learners `[srivastava2021]`.
  - LLM-rated item features can fill an LLTM design matrix. In one small study (15 items, 1,452 responses), the best LLM's ratings recovered item difficulty at r = 0.89, against 0.33 for an expert consensus whose agreement was at or below chance on half the features. Ratings still need audits for zero variance and collinearity `[bediwy2026]`.
  - Generated items need human validation `[bhandari2024]`, `[zelikman2023]`.
- **Change.** §7: feature-point contract, an independent feature audit, item-side signals, re-forecast, and certification that uses the more conservative of stamped and audited features.

**R11. Bandits and level-set search lend ideas, not guarantees.**
- **Findings.** ZPDES picks activities by learning progress under expert constraints `[clement2015]`. Thresholding bandits `[locatelli2016]` and level-set estimation `[gotovos2013]` focus sampling near a threshold. All three assume stationary arms, and practice breaks that.
- **Change.** The overlap exploration of §6.1 borrows "sample near the boundary". Learning-progress bandits over families are deferred.

**R12. Pooling across learners comes later, robustly and privately.**
- **Findings.**
  - Hierarchical adaptive design builds priors from earlier participants `[kim2014]`.
  - Explanatory IRT eases person cold start `[park2019]`.
  - Individualized BKT separates student from skill parameters `[yudelson2016]`.
  - N-of-1 Bayesian models aggregate individuals hierarchically `[schmid2022]`.
  - Privacy: release item parameters under differential privacy and keep abilities local `[steiner2018]`; federated IRT with differential privacy `[zhou2025]`, `[hridi2026]`; user-level rather than item-level privacy `[liu2020]`; secure aggregation `[bonawitz2016]`.
- **Change.** §13's staged path, plus requirements on the contribution export.

### 4.2 The agreed direction, item by item

| Agreed in conversation | Verdict | What changes |
|---|---|---|
| Explanatory IRT (LLTM): `b = f(features) + offset`, wide-variance offset | **Keep** | Add learned weights on item-side signals inside the offset (R7). Integrate the offset, never estimate it per item (R1, R6). |
| Per-item `b` unidentified at n=1, feature effects identifiable across items; state the confound honestly | **Keep, sharpen** | Identifiable only with feature–time overlap and a fixed scale. Randomized overlap and diagnostics (§5.8). |
| Per-(facet, capability) posterior over the learner's threshold on the feature ladder | **Keep, make dynamic** | Learning increment plus drift (R2). Hierarchical prior across capabilities of a facet (§5.5). |
| QUEST+/Psi Bayesian adaptive choice: band for practice, information for calibration | **Keep, refine** | Practice maximizes `P(p ∈ band)`, not distance of a point estimate (R1, R4). Calibration maximizes psi-marginal information only among acceptable items (R3, §6.2). |
| LLM writes a surface *at* the chosen feature point | **Keep** | Add an independent feature audit and a re-forecast before serving (R10). |
| Every forecast logged before the attempt and scored | **Keep** | Receipts per presentation and a DERIVED scorer (§8). |
| Outside estimates (solver panel; LLM forecast *with* the learner card) enter as priors on the item offset | **Split** | Item-only signals → offset prior with learned weights. Forecasts that read the learner's history → competing experts, never offset priors (R7). |
| Observations: correctness, partial credit, cold/primed, hints, time, optional rating; weights learned, never hand-picked | **Keep** | Ordinal outcome. Hints change the outcome category; unknown hint timing is censored, never guessed. Cold vs warm (recent exposure to the LO in any channel) is a learned warmth shift. A primed attempt (the answer was in view) is never an unassisted success: revealed during the presentation, it enters only as "not an unassisted success", its correctness unused; exposed before it, it is excluded. Rating and timing are sub-arms with constrained, learned links that must earn activation (R9). |
| Probes target expected information gain between hypotheses, not the band | **Keep** | Item-offset uncertainty folded into the conditionals. Probe authoring stops using the 45–55% difficulty band (§6.3). |
| Certification "demonstrated up to rung k" from items at or above the rung; exam/pset defines the top rung; reconcile with the capability ledger | **Keep** | Credit is stored by feature point, from the more conservative of stamped and audited features; a rung is a point on one goal's immutable ladder. LO certification keeps its structure, with an entry-level floor and requirements stated as feature points. Full mastery is a separate label (§9). |
| n>1: pooled consented data supply population priors for feature effects and item offsets | **Keep** | Robust mixture priors, held-out learners *and* item families, learner-level privacy (R12, §13). |

---

## 5. The model

### 5.1 Units and notation

- **Cell** `c = (f, k)`: a canonical facet `f` and a capability `k ∈ {retrieval, schema_interpretation, procedure_execution, method_selection, coordination}`.
- **Item** `i`:
  - capability `k_i`;
  - facet weights `w_{i,f}` (normalized `evidence_weights`, falling back to equal weights over `evidence_facets`);
  - a **feature tuple** `x_i` on schema `p1_launch@1`: `complexity` 0–4, `transfer`, `scaffolding`, `span`, `response`, `tools`. The `representation` and `time` dimensions are not modelled in v1;
  - surface group `s_i` (`canonical_projection.surface_group_id`, `:246`);
  - item-side signals `z_i` (§7.3).
- **Attempt** `t` on item `i` at time `τ_t`:
  - correctness `y_t ∈ [0,1]`;
  - `hints_used`, and the help timing `h_t ∈ {none, before_work, after_work, unknown}` (§5.3);
  - whether the answer was revealed during the presentation (`primed`, §5.3);
  - warmth `w_t ∈ [0,1]`: recent exposure to the item's LO in any logged channel (§5.4);
  - `latency_seconds`;
  - optional rating `r_t ∈ {easy, about_right, hard}` (new, §12).

### 5.2 State

A single Gaussian `N(μ, Σ)` over:
- **Cell abilities**, through a hierarchical decomposition: `θ_{f,k} = θ_f + ψ_k + e_{f,k}`.
  - `θ_f`: facet level.
  - `ψ_k`: a capability offset shared across facets in the vault; `ψ_retrieval ≡ 0` anchors the scale.
  - `e_{f,k}`: the cell deviation.
  - State dimensions are created lazily, when a cell is first observed or first asked about.
- **Shared feature effects** `β`: cumulative increments per ordinal level of each feature dimension, plus contrasts for `response` and `tools`. The reference tuple `x_ref` (the default trajectory's `recall` waypoint: complexity 0, `same_context`, `short_constructed`, `cue`, `atomic`, `closed_book`) has demand 0, which anchors the location.
- **Item-signal weights** `α` (§7.3).
- **Learning increment** `γ` and **warmth shift** `ζ`.
- **Sub-arm parameters**, present only when that sub-arm is on (§5.4), in unconstrained coordinates: rating `(c_1, d̃, ρ̃)`; timing `(ν, ω̃)`.

The item offset residual `ε_i` is *not* state. It is integrated out of every likelihood and prediction (R1).

### 5.3 Outcome categories (help-adjusted, ordinal)

One definition of success is shared with the certification cold probe (`certification_cold_probe.py:197`, success at correctness ≥ 0.8) and the partial threshold with the ledger (`canonical_projection.py:56`, `FAILURE_THRESHOLD = 0.40`):

**Help timing `h_t`.** Ordinary hints keep only their total today (§3.1), so timing is a per-attempt label with an explicit "unknown". A **help-equivalent question** is a practice-context tutor question during the presentation that field reads as help: `hint_equivalent` set, or a help type (`prerequisite`, `mechanism`, `clarification`, `strategy`) (`field/signals.py:217-221`, `:256-259`).
- `none`: `hints_used = 0` and no help-equivalent question;
- `before_work`: some help was **logged** before any work. That is a help-equivalent question logged with `attempt_progress = no_draft` or `seconds_into_attempt = 0` (field's own rule, `field/signals.py:351-359`), or, from AD1 on, ordinary hints with `first_hint_progress = no_draft` (§11.2);
- `after_work`: every source of help has its earliest event logged with work begun: `first_hint_progress = draft_started` when ordinary hints were used, and `attempt_progress = draft_started` on every help-equivalent question;
- `unknown`: anything else. That includes every ordinary hint recorded before AD1, a question with no progress marker, and a client that does not send `first_hint_progress`. **Missing timing is never read as "after work began".**

| Category `Y` | Condition |
|---|---|
| 2 **unassisted success** | `y ≥ 0.8`, `h_t = none`, not primed |
| 1 **partial, or success with help after work began** | `0.40 ≤ y < 0.8` with `h_t = none`, not primed; or `y ≥ 0.8` with `h_t = after_work`, not primed |
| 0 **fail** | not primed, and: `y < 0.40` with `h_t = none`; or `y < 0.8` with any help; or `h_t = before_work` (field §3.1's early-help cap); or an empty "I'm stuck" |
| `{0, 1}` **censored: not an unassisted success** | `y ≥ 0.8` with `h_t = unknown`, not primed; or any primed attempt, whatever its `y` and `h_t` |

Primed takes precedence over every other row, so each attempt has exactly one category.

**The forecast event and what counts as observed.** The event used everywhere (band, receipts, scoring and the update) is `Y = 2` on a first presentation that ends in a submitted, graded attempt. A future hint or reveal is never a forecast covariate.
- **The binary event is always observed** on a submitted attempt. Any help, or an answer revealed during the presentation, makes it 0, whatever the timing.
- **Censored categories** enter the update through `P(Y ≤ 1 | η) = 1 − P(Y ≥ 2 | η)`, and the ranked probability score skips them (§8.3). So training and scoring read the same event, and the model is never trained only on the presentations where the learner did not ask for help.
- **Primed attempts.** `primed` is set for a source-review retry and also, by `auto_primed_draft`, for any submission whose summed reveal amount on the item since its last attempt reaches `AUTO_PRIME_REVEAL_THRESHOLD = 0.35`, first attempts included (`attempts/attempts.py:149`, `:1937-1990`). AD splits them by when that sum was reached, using the same sum:
  - **Exposed before the presentation:** the item's reveal sum over `reveal_events` rows created before `served_at` already reaches the threshold. This is not a fresh first presentation. It is known at serve time, so the item is never in a draw's support (§6.1). A planned slot that holds it is served only as the predecessor serves it, with no draw (§6.1, step 0), and any receipt for it carries `pre_exposed = true`. Such presentations are excluded from the update and from scoring alike.
  - **Revealed during the presentation:** any other primed attempt with a bound presentation (the sum crossed the threshold after `served_at`, or the retry flow set the flag). The event did not occur. The attempt enters the update as the censored factor. Its correctness is never used, so revealed correctness is never ability evidence; only the fact that the learner needed the answer is.
  - **With no bound presentation,** the reveal's timing relative to serving is unknown, and the attempt is excluded from both.
- **Skipped or abandoned presentations** (no submission) have no outcome. They are right-censored in scoring and absent from training alike, so the estimand is explicitly "unassisted success, given an answer is submitted". The AD report gives the skip rate per forecast decile, so skips that concentrate where predictions are low are visible.
- Cold vs warm *without* the answer in view enters through the warmth covariate `w_t` (§5.4).

### 5.4 Likelihood

The linear predictor for attempt `t` on item `i`:

```
η_t = a · ( Σ_f w_{i,f} θ_{f,k_i}  −  β·φ(x_i)  −  α·z_i  −  ε_i )  +  ζ · w_t   =   ũ_tᵀ s  −  a·ε_i
ε_i ~ N(0, τ0²)        a = 1 (fixed in v1)
```

- `φ(x)` is the cumulative dummy coding of `x` relative to `x_ref`.
- **The projection `ũ_t`.** Every state coordinate enters `η_t` linearly, warmth included: `ũ_t` has `a·w_{i,f}` on the cell abilities, `−a·φ(x_i)` on `β`, `−a·z_i` on `α` and `w_t` on `ζ`. So `ζ`'s uncertainty and its covariances are carried through prediction and update like every other coordinate.
- **Warmth.** `w_t = exp(−Δh_t / h_w)`, with `h_w = 6` hours (a fixed, versioned constant swept by the harness), where `Δh_t` is the number of hours since the learner's last exposure to the item's LO in any logged channel. The channels are: an attempt on another item of the LO, a `reveal_events` row for the LO (`migrations/154_reveal_ledger.sql`), and, once router §15.2's covariate view exists, reading and tutor events. `w_t = 0` with no prior exposure. `w_t` is known when the item is served, so it is a valid forecast covariate. Its weight `ζ` is learned (router §15.2: "coldness is learned, not hard-coded").

Graded response, with guess floor `g_i = guess_floor_for_item` (`blueprint_projection.py:164`) and lapse `λ`:

```
P(Y ≥ 2 | η) = g_i + (1 − g_i − λ) · σ(η)
P(Y ≥ 1 | η) = g_i + (1 − g_i − λ) · σ(η + κ)
```

**Sub-arm likelihoods.** Each is a separate harness arm and is off in the base arm (§10.4).
- **`+rating`.** Ordinal logistic on the same predictor with its own link:
  - `P(r ≥ about_right) = σ(ρ·η − c_1)`;
  - `P(r = easy) = σ(ρ·η − c_2)`;
  - `ρ = exp(ρ̃)` and `c_2 = c_1 + exp(d̃)`, so `ρ > 0` and `c_1 < c_2` hold for every value of the latent coordinates `(c_1, d̃, ρ̃)`, and the category probabilities are always valid.
  - The rating is tapped after answering and before feedback (§12). It shares information with the outcome, so the arm earns activation only if it beats the base arm on held-out log loss. It is one factor of the attempt's joint likelihood (§5.6), never a free extra vote.
- **`+timing`.** For unassisted successes only, `log(ℓ_t / m̂_i) ~ N(ν − ω·η, σ_ℓ²)`.
  - `ω = exp(ω̃)`, with latent `(ν, ω̃)` and fixed `σ_ℓ`.
  - `ℓ_t` is `latency_seconds`. `m̂_i` is the plan estimator's `answer_minutes(item) × 60` (`daily_plan/estimates.py:1-18`), computed from latencies strictly before this attempt, with feedback dwell excluded.
  - Coverage is low today (18% of attempts in §3.3); the arm abstains where latency is missing.

All factors of one attempt (the outcome, and the rating and timing where present) share the same `η`, and so the same item residual `ε_i`. They form **one joint factor**, integrated over `ε_i` once (§5.6).

### 5.5 Priors (`ad_priors_v1`, a priori, versioned; field F5)

| Parameter | Prior | Basis |
|---|---|---|
| `θ_f` | `N(0, 2.0)` at the cell's creation. Self-assessment claims then **re-anchor the mean** of `θ_f` to `logit(claimed_level)` at the claim's `created_at`, in the same ordered stream as attempts, and only while the facet has no eligible AD observation. The variance is set to `max(current, claim_prior_min_variance = 2.0)`, mirroring today's claim seeding (`learner/mastery.py:172-201`), so a claim moves the mean and never shrinks uncertainty. Claims made after the facet's first eligible observation are not read by AD. **Allowlist:** the init wizard's global claim (`learner/learner_profile.py:61-80`, applied to every facet) and tutor gap declarations (`tutor/promotions.py:772-796`, applied to the facets or LO in scope). **Excluded:** claims written by easier/harder requests (`rung_variant_request`, `content/authoring/rung_variants.py:416-432`) and by too-easy/too-hard reports (`learner_report`, `content/authoring/item_authoring.py:317-365`), which AD does not read in v1 (D8). The EKF posterior is never used | Claims move the mean only; the variance never falls below 2.0. Applying them at their own time means a later claim never seeds earlier observations. Claims are mutable rows, so a replaced claim's earlier version is not replayed (stated in the AD report) |
| `ψ_k` | schema_interpretation `N(−0.3, 0.5²)`, procedure_execution `N(−0.5, 0.5²)`, method_selection `N(−0.8, 0.5²)`, coordination `N(−1.2, 0.5²)`; retrieval ≡ 0 | Ordering from capability dominance (measurement spec B1); magnitudes a priori. Field's `lo_general+capability` uses `N(0, 0.5²)`; the harness sweeps both |
| `e_{f,k}` | `N(0, 1.0)` | Fresh-cell total variance ≈ 3.25, matching the cold-start 3.0 (`schema.py` `cold_start_prior_logit_variance`) |
| `β` complexity, each step 0→1→2→3→4 | `N(0.5, 0.3²)` | Monotone ordering from the default trajectory; ~0.5 logit ≈ 10 points of success near 75% |
| `β` transfer, each step same_context→near→far→novel_combination | `N(0.5, 0.3²)` | Same |
| `β` scaffolding: cue→none `+`, cue→partial `−`, partial→worked `−` | `N(0.5, 0.3²)`, `N(−0.5, 0.3²)`, `N(−0.5, 0.3²)` | Less scaffolding is harder (`depth_rungs.py:41`) |
| `β` span, each step atomic→single_step→multi_step→whole_task | `N(0.4, 0.3²)` | Same |
| `β` response vs short_constructed | recognize `N(−0.7, 0.4²)`, long_constructed `N(0.3, 0.3²)`, structured_steps `N(0.3, 0.3²)`, performance `N(0.6, 0.4²)` | Selected response is easier and less informative (`depth_rungs.py:89-99`) |
| `β` tools: open_book/references vs closed_book | `N(−0.4, 0.3²)` | |
| `α_llm` (LLM label) | `N(0.2, 0.2²)` | Low prior trust (R7), above zero given §3.3 |
| `α_panel` (solver-panel relative offset) | `N(0.5, 0.3²)` | Moderate trust (R7) |
| `α_v1` (item-only LLM forecast, as a difficulty: `−logit p`) | `N(0.2, 0.2²)` | Low prior trust; learned |
| `α_origin` (generated vs canonical exercise) | `N(0, 0.5²)` | Neutral. This is the quantitative "surface gap" of router §15.5 |
| `γ` learning increment per graded first-surface opportunity in a cell | `N(0.2, 0.1²)` | Field `lo_general+practice` γ = 0.2 |
| `ζ` warmth shift (at `w_t = 1`) | `N(1.0, 0.5²)` | Half of today's `priming_b_offset` (2.0, an immediate re-read). Recent exposure in the session is weaker than a re-read |
| `+rating`: `ρ̃`, `c_1`, `d̃` | `N(log 0.5, 0.5²)`, `N(−1.0, 0.5²)`, `N(log 2.5, 0.3²)` | Rating is a noisy reading of the margin. Prior medians `ρ = 0.5`, `c_2 − c_1 = 2.5` |
| `+timing`: `ν`, `ω̃` | `N(0, 0.3²)`, `N(log 0.15, 0.6²)` | Faster when the margin is larger `[klinkenberg2011]`. Prior median `ω = 0.15` |
| **Fixed constants** (versioned, swept by the harness) | `a = 1`; `λ = 0.02`; `κ = 1.5`; `τ0 = 1.0`; `σ_ℓ = 0.6`; warmth decay `h_w = 6` h; drift `σ²_drift = 0.01`/day (`mastery.sigma2_drift`) | Not learnable at n=1 without misleading precision (R3, R6) |

Cross-dimension correlations in the prior are zero except as implied by the hierarchy.

### 5.6 Update rule (deterministic assumed-density filtering)

Rows are processed in fixed order (`created_at`, `attempt_id`) in float64. Rebuild is byte-identical (G1 of field §7.1).

1. **Eligibility.** A row updates the state only if it is all of the following:
   - a graded attempt of type `independent_attempt`, `open_text`, `diagnostic_probe` or `exam_attempt` (on reserved pool items, which are ordinary items);
   - the **first** graded attempt on its surface group `s_i` (repeat attempts on the same surface are FSRS's job, D10);
   - not held for review (`held_grades`);
   - not quarantined, unassessable or zero-mass;
   - from the current grading epoch;
   - with usable inputs: its frozen serve inputs, or a historical resolution whose status is not `excluded` (§7.5).

   Excluded: `self_report` rows, so that the rung-variant evidence package is not read twice (D8); presentations exposed before serving, and revealed attempts with no bound presentation (§5.3); `teach_back` in v1 (§16); and any held-out exam unit (A8). A primed attempt revealed *during* its presentation is not excluded: it enters as the censored factor (§5.3).
2. **Claims.** An allowlisted claim (§5.5) whose `created_at` falls before this row re-anchors `θ_f`'s mean first, if the facet has no eligible observation yet (mean-only, variance ≥ 2.0).
3. **Propagate.** For each touched cell, add `σ²_drift · Δdays` (since that cell's last update) to `Var(e_{f,k})`. There is no mean decay; forgetting stays with FSRS (field §4.3, "Time").
4. **One joint factor per attempt.**
   - **Dependence.** The attempt's likelihood (the outcome category, and, where the active arm has them, the rating and the timing) depends on the state only through a low-dimensional vector `v_t`. It holds the linear projection `ũ_tᵀs` that forms `η_t` (warmth included, §5.4), plus the sub-arm link coordinates (`c_1, d̃, ρ̃`; `ν, ω̃`). That is at most six coordinates, and exactly one in the base arm.
   - **The shared residual.** The item residual `ε_i` enters every factor through the same `η_t`, so it is integrated **once**, inside the joint factor: `Z_t = E_{v_t, ε_i}[ L_Y(η_t) · L_r(η_t) · L_ℓ(η_t) ]`, with `η_t = ũ_tᵀs − a·ε_i`.
   - **Censored categories.** For a censored attempt (§5.3), `L_Y = P(Y ≤ 1 | η_t)`, and the rating and timing factors are omitted: help or a reveal came between the learner and the answer.
   - **Inputs.** `ũ_t` is built from the attempt's frozen features and signals (§7.5), never from the item as it stands at rebuild time.
   - **Quadrature.** `Z_t` and the posterior mean and covariance of `v_t` come from tensor Gauss–Hermite quadrature: 32 nodes on the `η` coordinate, with the `ε` variance `a²·τ0²` folded into it, and 5 nodes on each link coordinate. In the base arm this is the one-dimensional assumed-density update TrueSkill uses `[herbrich2006]`.
   - **Back-projection.** The full state is updated by linear-Gaussian back-projection from the moment-matched `v_t`: the rest of the state is regressed on `v_t` through `Σ`. This is the standard assumed-density-filter projection for a factor on a linear subspace.
   - **Why it matters.** Unlike today's EKF (`mastery.py:450+`), which linearizes at the prior mean, this is exact moment matching of a non-Gaussian likelihood, which matters at the ceiling. Correlated observations of one attempt enter once.
5. **Learn.** After the update, apply the learning transition `e_{f,k} ← e_{f,k} + w_{i,f}·γ` for each touched cell. It is linear in the joint state, so the covariance propagates exactly.
6. **Record.** The per-attempt trace (prior and posterior moments of `η`, predicted category probabilities, information gained) is written to the DERIVED trace (§11.2).

### 5.7 Predictive quantities

For cell `c` and a candidate feature point `x` (a not-yet-written item; `z = 0`):
- **`p̄(x)`**: posterior predictive unassisted success, `E[g + (1 − g − λ)·σ(η)]` with `η ~ N(m(x), v(x))`. This is the family expected response `[sinharay2003]`. For a specific pool item, its own `z_i` enters `m`.
- **`p_θ(x)`**: the expected success *given* the epistemic state. The item residual `ε` is integrated and the state is held fixed. It is a monotone function `F_x` of the epistemic part `η_e = ũᵀs ~ N(m(x), v_e(x))`, `v_e = ũᵀΣũ`. The warmth at serve time sits inside `ũ` (§5.4).
- **`P_band(x)`** `= P(p_θ(x) ∈ [0.70, 0.80]) = Φ((F_x⁻¹(0.80) − m)/√v_e) − Φ((F_x⁻¹(0.70) − m)/√v_e)`. It is exact, because `F_x` is monotone.
  - `F_x` ranges over `(g, 1 − λ)`. A band edge outside that range makes its term 0 (below) or 1 (above); for example, a selected-response item with a guess floor above 0.70 can only reach the band from its lower edge.
  - The warmth `w_t` at the moment of serving enters through `ũ`, in both `m(x)` and `v_e(x)`.
- **`I_c(x)`**: psi-marginal information `I(θ_c; Y | x)` about the cell ability only, with every other state component treated as nuisance `[prins2013]`. Computed by two-level quadrature (outer over `θ_c`, inner over the conditional remainder plus `ε`).
- **`H(x)`**: hypothesis-conditional category probabilities for probes (§6.3).

### 5.8 Identifiability: what one learner's history can and cannot say

**Can be identified** (given the scale fixed by `a = 1`, `ψ_retrieval = 0` and `x_ref`):
- contrasts between cells;
- the feature effects `β`, but only along directions of the design that vary independently: of each other, of the item-side signals, and of time within a cell. If two feature columns always move together (the default trajectory raises `complexity` and `transfer` in the same steps, `depth_rungs.py:101-122`), only their sum is identified, however well randomized the timing;
- the weights `α` on item-side signals, which are a regression across many items, subject to the same rank condition against the features;
- the learning increment `γ`, to the extent the same feature points recur.

**Cannot be identified:**
- the offset of a one-off item (its posterior is the prior plus one response's worth, and it is never shown or used as "measured" difficulty);
- between-learner variance;
- whether `β` is universal or this learner's;
- growth versus feature effects when features rise with time. If `x_t` is a function of `t`, then `(β + v, θ_t + x_t·v)` fits every observation equally well (R6).

**The honest statement, shown in the AD report and in the glass-box view (not in the default UI).** "The estimated rise in your skill and the estimated hardness of each kind of question are conditional on two assumptions: that the hardness of a question kind is stable over time, and that generated questions really have the features they were asked for. Your answers alone cannot separate a rise in skill from questions at a level being easier than assumed."

**Design remedies:**
1. Randomized overlap: 10% of practice choices sample uniformly among items with acceptable predicted success, so feature level is not a function of time (§6.1). Commission candidates include one-step neighbours on a *single* dimension, so feature columns are varied one at a time and stop moving together.
2. Feature audits, so "the features it was asked for" is checked (§7.2).
3. The source-origin weight `α_origin`, so generated-vs-canonical differences are estimated, not absorbed into skill.

**Diagnostics** (AD report, every run):
- per-dimension correlation between served feature level and time, labelling `β` estimates "confounded" when `|r| > 0.6`;
- aliased directions: the eigenvectors of the data's contribution to the posterior precision of `(β, α)` with eigenvalue below 5% of the prior precision. Coefficients along them are labelled "prior-dependent";
- posterior contraction of each `β` relative to its prior;
- prior sensitivity: rerun with each prior mean shifted ±1 sd and report how many band decisions change;
- simulation recovery (AD2) under the actual policy versus a monotone policy.

---

## 6. Selection

### 6.1 Practice: land in the band

**Scope.** AD decides *which feature point and which item* for new material in a cell. *Which LO or facet to practise* is decided upstream (daily-plan lanes, router blocks, diagnosis repair).

AD makes two kinds of draw, logged separately: a **serve draw** over items that exist, and a **commission draw** over feature points to generate. Only the serve draw puts an item in front of the learner, so only its propensity enters off-policy evaluation of what was served.

**The cell pool `P_c`.** An item is in cell `(f, k)` when `k_i = k` and `w_{i,f} > 0`.
- Every never-attempted, servable item in the cell, with its features and signals resolved as of now (§7.5).
- Excluded: exam-reserved items (`exam_pool.reserved_item_ids`), retired items, anything derived from a held-out unit, and items whose answer was exposed before serving (§5.3).
- Items authored above the depth envelope (`RungTarget.task_feature_bounds` "max") are excluded too. `coordination` items are served only behind a reviewed envelope (`depth_rungs.py:126-129`, `:176-182`).

**When AD draws, and over what: the slot support `S`.** AD never builds or reorders blocks (§10.1).
- The plan's source packs blocks exactly as its predecessor does, and the block is chosen exactly as today: by the router's draw, or, with the router off, by DL1's deterministic chooser (`daily_plan/policy.py:1-20`).
- A serve draw happens when a **slot** of the chosen block comes up to be served. A slot is a planned item with `new_admitted = true`: an ordinary never-attempted new-lane item the chooser planned, never a learner pick, a request, a follow-up or a scheduled check (`daily_plan/engine.py:1555-1557`). A new-lane block stays on one LO (`daily_plan/lanes.py:444`).
- The **candidates** of that draw are the slot item and every other never-attempted item of the slot item's LO, at the slot item's capability. The support `S` is the candidates that pass **every** check below at the moment of the draw.
- **The slot item gets no exemption.** Its block was admitted at a boundary. The frame evaluates items only there (`daily_plan/staged_frame.py:9-16`) and keeps that material for the whole request (`:194-211`). Before a serve, reconciliation re-checks only status and serving blocks (`daily_plan/engine.py:1925-1931`, run at `:2424`, before the serve at `:2484`). So a reservation, a cold check, a reveal or a constraint can change between the block's admission and its slot's serve. Every check is re-read at the draw, never taken from the admission or from the frame's cached material:
  0. **are still eligible:**
     - in `P_c` now, for some facet of the slot item, with its exclusions re-read (exam reservation, retirement, held-out derivation, pre-exposure, the depth envelope);
     - with no serving block (`vault/lifecycle.py:162-163`);
     - outside the exclusions that a selector outside the scheduler's timing honours. These are the routine exclusions, the item an open cold follow-up holds, and any item revealed within the cold retrieval delay (`scheduling/serving_exclusions.py:18-27`, `:84-86`). They are read as the quick check reads them (`diagnosis/quick_check.py:193-196`);
  1. **pass the admission the slot item passed.** Under the staged frame (router on): the constraint engine admits them in the block's attention action, re-evaluated against a fresh controller snapshot exactly as the frame evaluates items at a boundary, and they are reversible: no open cold check and no reserved assessment surface, the condition R2b's mixture already places on anything it draws (`staged_frame.py:42-52`, `:498-523`). With the router off: the predecessor's pool rules for the new lane, plus the same reversibility condition;
  2. are not planned in any of today's plans, this block included (for the slot item: in no slot but its own);
  3. **fit the block:** `est_minutes(i) ≤ est_minutes(slot item) + slack`, where `slack = max(0, min(BLOCK_MAX_MINUTES − the block's planned minutes, the plan's minutes_left, the new lane's minutes_left))` (`daily_plan/types.py:52`, `:79`, `:81`). So the block stays within 15 minutes and the plan within its budget (daily loop P1), and the slot item always fits;
  4. **add no admission load the plan did not grant:** `new_item_daily_cost(i) ≤ new_item_daily_cost(slot item)`, or the day's admitted load with `i` in place of the slot item stays within the ceiling (`daily_plan/admission.py:138-139`, `:142-201`). A one-for-one substitution leaves the count unchanged, and a slot that came in by the floor or the "more new material" override is never replaced by a costlier item.

  Checks 2–4 hold for the slot item by construction. Checks 0 and 1 are where it can fail.
- **A slot item that fails a check** is not in `S`, and AD draws among the other candidates. With none, `S` is empty (step 0 below). A slot item that passes, with no other candidate, is `S` alone and is served with `π = 1`.
- **With `selection = false`** none of this runs. The predecessor serves the planned item exactly as today (§10.2).
- **One transaction, no recomputation.** The support, the draw, its `ad_selections` row, any substitution and `item_served` are one transaction (`daily_plan/engine.py:2566-2599`). Nothing can change between the checks and the exposure, so a propensity is never recomputed after the draw and a drawn item is never refused afterwards. An item that fails a check is simply not in `S`.

**Serve rule (`ad_select_v1`):**
0. **Empty support.** If `S` is empty, AD makes no draw. The row records `empty_support` and each candidate's failed check.
   - **Pre-exposure only.** If the slot item failed only the pre-exposure check (§5.3), it is served as the predecessor serves it, with no draw: the row's mode is `predecessor` with `π_AD = 1`, and its receipts carry `pre_exposed = true`, so it neither trains nor is scored. So a pre-exposed item is never in a randomized support, and the learner still gets the item the plan chose.
   - **Otherwise** the slot is displaced with the container's existing event, `item_displaced`, with reason `ad_ineligible` and the failed check. This is how reconciliation displaces an item that is no longer servable (`daily_plan/engine.py:1932-1936`), and the container's rules pick the next step. An item revealed within the delay comes back once the delay has passed; an item held by a cold follow-up is served by that follow-up.
1. Compute `P_band(i)` and `p̄(i)` for every `i ∈ S`.
2. **Calibrate instead** if `max_{i∈S} P_band(i) < 0.35` (the posterior is too wide to target the band; typical in a new cell). Choose by §6.2.
3. Near-tie set `T = {i ∈ S : P_band(i) ≥ max P_band − 0.05}`. Overlap set `O = {i ∈ S : p̄(i) ∈ [0.55, 0.90]}`.
4. Draw with exact propensity `π(i) = (1 − q)·1[i∈T]/|T| + q·1[i∈O]/|O|`, with overlap share `q = 0.10`.
   - If `O` is empty, `q = 0` for this draw.
   - The seed is `seed_for(decision key)`, where the key is the block id and the slot's position.
   - The support, both scores, `π`, the seed and the chosen item are written to `ad_selections` in the serve transaction, **before** the item is served (A7).
5. **Substitution.** If the drawn item is not the slot item, an `item_substituted` block event records both items, both estimates and the `ad_selections` id. It is written in the same transaction, before `item_served`. The plan record's fold (`daily_plan/records.py:357-410`) replaces the slot's item and estimate with the drawn item's, so from then on the plan's planned minutes use the drawn estimate. The displaced slot item is unplanned and returns to the pool.

**Commission candidates `X_c` and rule.**
- `X_c`: the rungs of every ladder instance that applies to the cell (each active goal's ladder and the default ladder, §9.1) and their one-step neighbours on a single ordinal dimension, clipped to the depth envelope.
- A commission draw runs in two places, for the cell of the slot or LO at hand (its highest-weight facet, ties by facet id, at its capability):
  - at a serve draw, when the cell pool `P_c` (not the slot support) has no item with `P_band ≥ 0.35`;
  - under `generation_contract`, wherever the existing generation path picks a waypoint for an LO (`select_rung`, `content/authoring/practice_generation.py:383-390`). That is how a cell whose pool is empty, and which so has no slot, gets new items.
- It uses the same rule as the serve draw: steps 1–4 over feature points with `z = 0`, with its own propensity, seed and `ad_selections` row (`kind = commission`).
- The chosen point is commissioned for generation (§7) and runs in the background. AD keeps at most one open commission per active cell.
- A commission changes only what can be served later. Its propensity is logged for completeness but never multiplied into a served item's weight.

**Why not Thompson sampling.**
- Sampling the joint state and picking the point nearest 0.75 explores in proportion to uncertainty (worker d).
- But its propensities need Monte Carlo over a ~20-dimensional Gaussian, so they are not exact.
- The rule above is exact, and its overlap share does the confound-breaking job.
- Thompson sampling is kept as a harness comparison (§10.4).


### 6.2 Calibration within acceptable difficulty

When the band cannot be targeted (always within the slot support `S` of §6.1):
- choose `i ∈ O` maximizing `I_c(i)` (§5.7), with near-ties (within 5% of the maximum information, relative) broken uniformly;
- if `O` is empty, choose the item of `S` whose `p̄` is nearest the interval `[0.55, 0.90]`, ties by item id;
- apply the same `q` overlap mixture and log it identically, with `mode = calibrate`.

**Why bounded.** Unbounded information would push toward 50% predicted success `[eggen2006]`. Bounding to `[0.55, 0.90]` keeps a cold learner from a run of failures (frictionless defaults) while still choosing the most informative acceptable item.

This replaces the "optimism step" heuristic (`depth_rungs.py:310-319`) when AD selection is on. The learner sees ordinary practice.

**Exam-target calibration.** When an exam/pset target exists (§9.5) and the goal's due date is within its horizon, `I_c` may be replaced by expected predictive information about success at the target points `[bickfordsmith2023]`. This is the same computation with the target tuples as prediction inputs. Off by default (D12).

### 6.3 Probes: discriminate

Probes keep their episode model, hypothesis sets, actual and predictive EIG (`diagnosis/probe_families.py:467-534`, `:536-620`), and value-of-information stopping (mvp-0.21). They also keep the probe spec's likelihood identity: candidate scoring and the posterior update use the same grader-composed conditionals, and the resolved snapshot is persisted with the presentation (`spec_probe_eig_redesign.md` §7.2, §9.3). Today that holds: `instrument_conditionals` composes the compiled rows with the grader channel (`probe_families.py:454-465`), the presentation stores `CompiledInstrument.snapshot()` (`:267-290`), and the update rebuilds the instrument from that snapshot (`diagnosis/probe_episodes.py:1828-1846`). AD5 adds one composition step *after* the grader channel, on the observed outcomes, and freezes its input in the same snapshot.

**Two probe-spec rules are amended, on purpose, under the AD5 successor only.** §7.2 requires the conditionals of admitted families to be compiled from the resolved card, and §9.3 says numbers change in exactly one place, the family Dirichlet posterior. For a *composed* slot (below), the card and its calibration keep every signature shape, and the success split comes from AD's frozen `q_h`. The identity rule (same conditionals for scoring and update) and the snapshot rule are kept exactly. With `probe_targeting = false`, both rules read as written.

**What AD5 changes in the conditionals (`ad_probe_compose_v1`).** AD supplies exactly one number per composed hypothesis slot: the probability `q_h(i)` that the learner, if `h` is true, gives an unassisted success on candidate `i`, **as graded**. AD learns `Y` from graded correctness and has no latent true response (§5.3–5.6). So `q_h` is the probability of an *observed* success, and grading error is already in it.
1. **Outcome-alphabet mapping.** The *success class* of an instrument is the outcome `classify_outcome` returns for an attempt at full rubric points (`probe_families.py:720-786`; for example `correct_target_reason`, `correct_strategy_complete`, or `high` for the legacy fallback). AD composes an instrument only when that class is exactly AD's event `Y = 2`. Two facts make it so:
   - a diagnostic block disables hints, the tutor, worked examples and answer reveal (`diagnosis/probe_episodes.py:70-77`), so a probe attempt is unassisted and unprimed;
   - correctness is `rubric_score / max_points` (`attempts/attempts.py:3295`), so with a rubric of at most 4 points, correctness ≥ 0.8 means full points.

   For any other rubric the rows stay exactly the card's, and the snapshot says `not_composed: rubric_points`.
2. **Row composition, on the observed outcomes.**
   - For a composed slot `h`, its **observed row** `G_h` is the compiled row `R_h` (true-outcome probabilities, after the family's Dirichlet calibration) composed with the family's grader channel, exactly as `instrument_conditionals` does today (`probe_families.py:454-465`).
   - Let `G_h(· | S)` and `G_h(· | S̄)` be `G_h` renormalized within the success class and within the other outcomes.
   - The composed row is `P(o | h, i) = q_h(i)·G_h(o | S) + (1 − q_h(i))·G_h(o | S̄)`. Its observed success probability is exactly `q_h(i)`, whatever the channel's reliability.
   - The card keeps its signatures (which wrong answer each hypothesis gives), and the channel keeps shaping how each is observed. AD replaces only the success split.
   - The ordinal table's floor (`negligible` = 0.01, `probe_families.py:28-34`) keeps both parts non-empty.
3. **Capability-hypothesis constraints.** A slot is composed only when its hypothesis is a constraint on cell abilities. "Below" and "at or above" a capability mean that the learner's success chance at that capability's entry point `e_k` (§9.1), with the item's facet weights and no warmth, is below 0.5 or at least 0.5:

   | Slot | Constraint |
   |---|---|
   | `unfamiliar` | retrieval below |
   | `recall_without_mechanism` | retrieval at or above; schema_interpretation below |
   | `procedure_without_selection` | procedure_execution at or above; method_selection below |
   | `robust_initial_grasp` | retrieval and the item's capability at or above |

   - `q_h(i)` is the posterior predictive success on `i` (the residual `ε` and the uncertainty of `β` and `α` integrated, §5.7) with the AD state conditioned on the constraint. The constraint truncates at most two linear functionals of the Gaussian state. The expectation is computed by deterministic quadrature over the truncated region, with the remainder conditional-Gaussian. If the constraint has probability below 1e-6 under the state, the slot is left uncomposed and the snapshot says so.
   - **Not composed:** `surface_only` and `schema_without_transfer` (transfer is a shared feature effect in v1, not a learner state AD can condition on), `other_or_unknown`, and every `misconception:*` and `confuses_with:*` slot. Their rows stay exactly the card's or the legacy fallback's, with their discrimination profiles and contrast pairs (`PracticeItem.discrimination_profiles`, `contrast_of`).
   - Card slot aliases (for example `surface_only` → `recall_without_mechanism` in the derivation family, `probe_families.py:1292-1294`) resolve before composition, so an aliased label reads its slot's composed row.
4. **Grader channel, applied once.** Uncomposed slots go through `compose_with_grader_channel` with the family's grader policy and reliability, exactly as today (§7.6 of the probe spec). A composed row is already observed and does not go through the channel again.
   - This is within the probe spec's own rule: evidence-strength fields "MUST either be explicitly post-grader quantities or be composed with this grader channel at runtime" (`spec_probe_eig_redesign.md` §7.6). `q_h` is a post-grader quantity. The card's signature shapes are still composed with the channel, as the probe spec's §7.2 requires.
   - Composing before the channel would apply grading error twice.
   - Take the contrast family: six outcomes (`probe_families.py:798-823`), reliability 0.90, so each other outcome receives 0.02 (`:59-62`, `:411-430`). There, `q_h = 0.80` would be observed as `0.90·0.80 + 0.02·0.20 = 0.724`. This composition keeps it at 0.80 (G-AD5-7).
5. **Calibration ownership.** The family and item Dirichlet counts (`probe_families.py:1722-1790`) keep accumulating as today and keep owning each slot's signature shapes. For a composed slot, only the within-class shapes `G_h(· | S)` and `G_h(· | S̄)` of the grader-composed calibrated row are used. The success split comes from AD alone, so it is never learned twice. This is the amendment stated above.
6. **The frozen snapshot.** When a candidate is scored, the composed instrument is built once. It is the instrument that candidate EIG and predictive EIG score, and it is the one `snapshot()` stores when the presentation commits.
   - The snapshot keeps the calibrated rows `R_h` as today and gains an `ad_composition` block. The block holds the composition version, the AD state hash and the priors version. Per slot, it holds `q_h` with the constraint and its probability, or the reason the slot was not composed.
   - `CompiledInstrument.from_snapshot` reads the block (`probe_families.py:291-300`), and `instrument_conditionals` applies it after the channel. So candidate scoring and the update compute the same composed rows from the same snapshot.
   - `compiled_likelihood_hash` covers the block when present (`probe_families.py:253-265`), and an instrument without one hashes exactly as today. So the probe audit's recomputation check covers `q_h` with no change (`diagnosis/probe_audit.py:311-320`).
   - The posterior update reads the snapshot, as today, and never recomputes `q_h` from a later AD state.
7. **Unchanged paths.** The incidental likelihoods of ordinary attempts (`probe_episodes.py:1884-1906`) and the legacy fallback's uncomposed slots keep today's `generic_bucket_marginals` (`diagnosis/probe_hypotheses.py:94-133`).

**Why this can lower or raise an item's EIG.** Integrating the residual inside each hypothesis computes EIG on the outcome distributions the learner will actually face, not on an idealized item. It also stops the acquisition rewarding information about an expendable item rather than the learner (worker b). This usually lowers an uncertain item's EIG, but not always: near saturation, noise can separate predictions. The test is agreement with a brute-force marginalized EIG, not monotonicity (G-AD5-2).

**Probe authoring targets discrimination, not difficulty.**
- The probe prompt's band instruction (`practice_generation.py:1984`) and the probe success band (`schema.py:399`) are retired under the AD5 successor.
- For capability hypotheses, the probe generator receives the feature point of `X_c` (§6.1) that maximizes the hypothesis EIG of the binary success event under the composed `q_h(x)` (with `z = 0`). For misconceptions it receives the discrimination-profile target.
- An item whose conditionals are identical across hypotheses already scores zero EIG whatever its difficulty (`probe_families.py:476-478`). AD5 keeps that rule and stops paying to author such items.

### 6.4 What is not AD's job

- **Block choice** stays with the router (staged rule, Decider, LLM, mixture; `router/mixture.py`).
- **Review timing of already-attempted items** stays with FSRS and the scheduler. AD does not reorder due reviews.
- **Repair after a diagnosis** stays with the diagnosis track, including the follow-ups it places and authors. The repair lane holds follow-ups and already-attempted items, never a new-material slot (`daily_plan/lanes.py:9-18`). A never-attempted item on a diagnosed LO is in the new lane, so AD's serve draw covers it as it covers any slot.
- **Selection-reward bands for due items** (`selection_rewards.py:516-526`) are unchanged.

---

## 7. Generation at a feature point

### 7.1 The contract to the generator (AD3 successor; switch `generation_contract`)

- The commissioned `RungTarget` carries `capability = k`, `task_features = x`, and `task_feature_bounds` with `max = x` on every dimension. The existing deterministic gate already rejects overshoot (`depth_rungs.py:204-208` point bounds; `validate_item_against_rung`, `:538-544`).
- The prompt **drops** every band instruction: `practice_generation.py:1062`, `:1919`, and the band clause of `:1922`. The waypoint clause ("NEVER change the waypoint") stays.
- It also drops the `recommended_difficulty_band` field from the target payload, and the band check `_check_difficulty_band` (`:1501-1537`).
- In their place: "Write the item so that it has exactly these features. Do not make it easier or harder than these features imply; difficulty is measured from the learner's answers. Separately, give your estimate `difficulty` in [0,1] of how hard this item is for a typical learner studying this topic. It is recorded as one weighted signal whose weight is learned from this learner's answers; it is not the item's difficulty."
- `difficulty_source = "llm_estimate"` stays on the item for the incumbent. Under AD it is only the signal `z_llm`.

### 7.2 Feature audit (AD1; switch `feature_audit`)

- After any item is generated or imported, one Tier-1-style Decider judgment per audited dimension (`complexity`, `transfer`, `scaffolding`, `span`, `response`) reads the item stem and reference answer only. It is never shown learner data or held-out text.
  - It answers a typed `ChoiceQuestion` over that dimension's vocabulary.
  - Argmax decides; a tie is no answer; the distribution is logged in `judgment_ledger` (task `ad_feature_audit`, version `ad-feature-audit-v1`), exactly as `decider_judgments.py:1-25` does.
  - Each judgment records the `content_hash` of the item revision it read (`practice_item_snapshots`, `migrations/164_item_snapshots_and_adjudication_fk.sql`). An edited item is a new revision and gets its own audit.
  - **The canonical audit** of a revision, per dimension and audit version, is the earliest judgment that answered. A later run of the same version never replaces it; a new audit version is a change of persisted meaning (§7.5).
  - On Decider failure, the existing LLM fallback runs and is recorded as such.
- **Backfill at AD1.** One owner-run pass, dry-run first and under the spend cap, audits every active item's current revision and every answered revision held in `practice_item_snapshots`. Without it, every existing item not already known below entry would stay "level pending" (§9.2) indefinitely.
- **Uses of the audited tuple `x̂_i`:**
  - AD's likelihood and predictions use `x̂_i` where the audit had answered *before the decision*, else the stamped `x_i`, as frozen at serve time (§7.5).
  - **Level credit (§9.2) uses the easier of `x_i` and `x̂_i` on every dimension**, from the answered revision and its canonical audit. An overclaimed feature can never raise a level.
  - The audit agreement rate per dimension is reported. Persistent disagreement is a generator finding, not a learner one.

### 7.3 Item-side signals and the offset prior

`z_i` is assembled from persisted values only, and **frozen per decision**:
- a selection or receipt uses exactly the signals whose `received_at` precedes it;
- an attempt's update uses the signals frozen at that attempt's serve time;
- the vector, each signal's receipt id and availability, and the `z_v1` recalibration version are written to the serve-input receipt (§7.5) and, for AD draws, to the `ad_selections` row. `ad_attempt_trace` repeats them for reading, but it is DERIVED and is not what freezes them.

A signal that arrives later is used only by later decisions and updates. It never changes an earlier state, selection or score. Together with the frozen features of §7.5, this is what lets replay reproduce history.

The signals:

| Signal | Value | Present when |
|---|---|---|
| `z_llm` | `2.5·(2d − 1)` from the item's own `difficulty` (the existing map, `mastery.py:377`) | `difficulty_source = "llm_estimate"` |
| `z_panel` | `logit(s_parent) − logit(s_item)`: the panel's relative offset, smoothed as in `pf_generation.py:190-197` | `difficulty_source = "solver_panel"` with the panel rates recorded |
| `z_v1` | `−logit(p_v1)`, where `p_v1` is an item-only LLM forecast of "probability a typical learner studying this topic answers correctly" (field V1 variant, no learner data), recalibrated on past items only. The sign makes it a difficulty, like the other signals | the item-scoped receipt, prepared with the pool before any serve (§8.1–8.2), was received before the serve |
| `z_origin` | 1 for generated items, 0 for canonical (textbook or problem-set) exercises (`PracticeItem.canonical_exercise`) | always |

`δ_i = α·z_i + ε_i`.

- The weights `α` are latent and shared (§5.5). Trust in each source is learned, and a useless source's weight shrinks toward 0 with no rule change.
- A missing signal contributes 0.
- Because the regression sits beside the features `β`, it captures what a signal says *beyond* the item's features.

### 7.4 Re-forecast and the serve decision

- When a commissioned item lands, AD computes its own `p̄(i)` with its audited features and `z_i`.
  - If `p̄(i) ∈ [0.55, 0.90]`, it joins the cell's pool and is eligible.
  - If not, it still joins the pool (it may suit the learner later) but is not served for this commission.
  - Either way, an `ad_commission_results` receipt is appended, linked to the commission's `ad_selections` row. It records the item, `p̄(i)`, and in band or `realized_out_of_band`. The selection row is never mutated; the combined status is derived.
- The realized miss rate per feature point is a generator-quality metric. If it stays above 40% after AD3, generating several candidates per commission becomes the trigger in §16.

### 7.5 Frozen serve inputs and historical attempts (AD1; switch `forecast_receipts`)

The features and signals an AD decision or update reads are fixed when the item is served. A later audit, re-audit, recalibration or item edit never rewrites them.

- **`item_serve_inputs`** (RECEIPT, append-only). One row per presentation of a never-attempted item, written in the serve transaction beside the in-process forecast receipts (§8.1). It holds:
  - the presentation reference and `practice_item_id`;
  - the served revision's `content_hash`, also written to `practice_item_snapshots` with `INSERT OR IGNORE` (migration 164);
  - the stamped tuple `x_i`; per audited dimension, the `judgment_ledger` id that had answered before the serve, or null; the resolved tuple AD reads (audit where answered, else stamped);
  - the signal vector `z_i` with each signal's receipt id and availability, and the `z_v1` recalibration version (§7.3);
  - `pre_exposed` (§5.3) and the resolution version `ad_feature_resolution_v1`.
- **Replay reads the receipt.** The update for an attempt uses exactly the row of the presentation it is bound to (the chain of §8.3).
- **Historical attempts** have no row: they predate AD1 or have no bound presentation. `ad_feature_resolution_v1` resolves them as of the attempt:
  - the answered revision follows the field's graded-revision rule (`spec_learner_field_v1.md` §3, "Historical revisions"; resolver `field/outcomes.py:154-233`): `exact` when the graded revision is found and matches; `reconstructed_current` only under `field.legacy_fallback = "current_content"`; otherwise `excluded`. Current content is never silently used;
  - from that revision: its stamped tuple, and its own `difficulty` for `z_llm`;
  - audits with `created_at` before the attempt (none exist before AD1), and no receipt-based signals.

  Each trace row carries `input_status` (`frozen`, `exact`, `reconstructed_current` or `excluded`). `excluded` attempts do not update the state. The AD report counts each status.
- **Reinterpretation is explicit.** Reading history with a new audit version, a new signal or a new resolution rule changes persisted meaning. It is a new `ad_feature_resolution` version, applied through the playbook with a shadow-rebuild report (§11.1), never a silent difference between two rebuilds.
- **Level credit reads differently, on purpose.** Certification describes the content the learner answered, not a decision taken before it. So an observation's level (§9.2) uses its answered revision and that revision's **canonical** audit (§7.2), whenever the audit landed. Until it lands, the readings already available bound the level from above. An observation whose stamped tuple is already below the entry point is level 0 for good. Any other is "level pending" and counts toward `e_k` only. The canonical audit is fixed once it exists, so the level resolves once and never changes after. An observation whose answered revision is `excluded` has no reading at all, and counts toward `e_k` only for good.

---

## 8. Forecasts: logging, scoring, trust

### 8.1 Receipts (AD1; switch `forecast_receipts`)

`item_forecasts` (RECEIPT, append-only), one row per (presentation, forecaster), or per (item revision, forecaster) for an item-only forecaster:
- **`scope`:** `presentation` or `item`;
- **presentation reference** (scope `presentation`): `plan_presentation_id`, `probe_presentation_id`, `scheduler_candidate_id`, or an exam session's pooled item (written when `start_exam` freezes its predictions, `goals/exam_session.py:1-12`);
- **item revision** (scope `item`): the revision's `content_hash`. An item-only forecast reads no learner data, so it is made once per revision, when the item is prepared for the pool, and never per presentation (§8.2);
- `practice_item_id`;
- `forecaster` and `forecaster_version` (hash of code, priors and config);
- `event = "unassisted_success"`;
- `p` and optional `p_categories`;
- `inputs_hash` and `inputs_as_of` (the snapshot the forecaster read);
- `issued_at`, `received_at`, `status` (`ok | failed | refused_spend`);
- `algorithm_version`.

**Validity rule.** A forecast is valid iff `inputs_as_of ≤ served_at`, whenever it arrives. So outside forecasters never sit on the critical path, and a late answer is still a true forecast *for scoring*. Whether it can also *inform* a decision is a separate rule: only a receipt received before the serve enters that serve's frozen inputs (§7.3, §7.5). An item-scoped receipt is scored against the item's first bound presentation. In-process forecasters (AD, the incumbent, `lo_general`) write their rows in the serve transaction, beside `plan_presentations` (plan R2 §5.2). Raw responses from paid forecasters go to `item_forecast_payloads` (WORKFLOW, pruned like `router_decision_payloads`); the receipt keeps the hash.

### 8.2 Forecasters

| Forecaster | Reads | When on | Role |
|---|---|---|---|
| `ad_threshold` (and sub-arms) | the AD state (§5) | AD2 onward, computed in-process at serve time even before promotion | Served after AD3 promotion; otherwise scored only |
| `mastery_ekf` (incumbent) | `resolve_item_irt_params` and the EKF | AD1 onward | Incumbent |
| `lo_general+composite` | field §4.3 | AD1 onward | Challenger |
| `solver_panel` | `difficulty_source = solver_panel` items: panel rate mapped through the item's `b` at the learner's incumbent ability | when present | Item-side signal and scored forecaster |
| `llm_v1:item` | item stem, LO and facet names (field V1) | AD1, switch `outside_forecasters`. Run once per item revision when it is prepared for the pool (after authoring or import and its feature audit, as a background job), and once as a backfill over the never-attempted items that exist at AD1. Never at presentation | Item-side signal `z_v1` after recalibration, which enters a serve only when received before it (§7.3); scored at the item's first presentation |
| `llm_v3:llm`, `llm_v3:decider` | field V3: item plus a `LearnerStateCardV1`-style card restricted to the LO and its prerequisites, plus similar past items with outcomes; Decider as a `noul` question | AD1, switch `outside_forecasters` (D4) | **Competing experts** (§8.4). Never an offset prior |

### 8.3 Scoring

- `item_forecast_scores` (DERIVED, one replayer) joins each valid receipt to its bound attempt through the exact chain `plan_presentations` → `practice_attempts.plan_presentation_id` (plan R2 §5.2). Unbound attempts fall back to the scheduler candidate, then the probe presentation; R1's session rule is never used.
- The outcome is the §5.3 event, read exactly as the update reads it.
  - Pending outcomes, and skipped or abandoned presentations, are right-censored, never failures.
  - Presentations with `pre_exposed = true` are not scored.
  - Any help, or a reveal during the presentation, makes the binary event 0.
- **Metrics per forecaster:**
  - log loss and Brier on the binary event;
  - ranked probability score on categories where given, over attempts whose category is fully observed (censored `{0, 1}` attempts are skipped);
  - the skip rate per forecast decile (§5.3);
  - reliability by decile and in the band region `[0.6, 0.9]`;
  - splits: first surface in a never-seen cell vs later, capability, coldness, serving origin.
- **Comparisons** between any two forecasters on the same presentations use anytime-valid confidence sequences on the score difference `[choe2023]`, so continuous monitoring is honest.
- **Planning illustration** (worker f; iid, not a guarantee): detecting a mean Brier advantage of 0.01 with score-difference sd 0.10 at 80% power needs about 784 outcomes. At n=1, promotions are slow by nature.

### 8.4 Learning trust

- **Item-side signals** earn trust through `α` inside the model (§7.3). This is Bayesian, so no separate weighting exists.
- **Learner-conditioned forecasters** (`llm_v3:*`, `lo_general`, `mastery_ekf`, `ad_threshold`) are combined in a DERIVED, reporting-only ensemble:
  - fixed-share exponential weights on Brier loss `[herbster1998]`, with learning rate 2 and share 0.05 (a priori);
  - chronological stacking `[yao2018]` as a second report.
- **The ensemble is never served** in this spec. Serving it would be a further successor, with its own trigger (§16).
- **What "trust" decides:**
  - which model is the active predictor for selection (§10.4);
  - whether the router's card shows an outside forecast (router §10, item 1).

---

## 9. Levels, certification and full mastery

### 9.1 Ladders: one per (target, capability), immutable (`ad_ladder_v1`, deterministic)

- **Ordered dimensions:** `scaffolding` (worked < partial < cue < none), `transfer`, `complexity`, `span`, response class (recognize < constructed < performance), `tools` (open < closed).
- **Entry point `e_k`:** the default-trajectory waypoint for capability `k` (`depth_rungs.py:101-122`). `coordination` has no entry without a reviewed envelope. It depends on `k` only, never on a goal.
- **A ladder instance** `L(k, t)` is a deterministic function of the capability `k` (so its entry `e_k`), a target point `t`, the feature schema (`p1_launch@1`) and the ladder version.
  - Its id is the hash of those four. Where the target came from (an exam profile hash, a milestone, the default) is recorded beside it for display and the glass box.
  - Instances are immutable. A new target makes a new instance; it never edits an old one.
- **Which target, per goal and cell.** A goal `g` reads, for a cell `c` in its scope, the target `t_{g,c}`, in order of precedence:
  1. the cell's exam/pset target (§9.5). It is the same for every goal: goals do not reference source sets yet (§16);
  2. else the goal's milestone target: the next reviewed milestone contract of the commitment that carries the goal (`goal_id` on the commitment head, `curriculum/commitments.py:186`; projected as in `depth_rungs.py:353-410`, `RungTarget.source = "milestone_edge"`). With several such commitments, the hardest point per dimension;
  3. else the **default target**: `e_k` stepped one level up in `complexity` and in `transfer`, bounded by the default trajectory. It depends on `k` only, so a cell outside every goal, or a goal with neither of the above, reads the **default ladder** of `k`.

  Any dimension where the target is easier than `e_k` is raised to `e_k`.
- **Walk:** from `e_k` to `t`, raising one dimension one level per rung in the fixed order above, cycling until every dimension reaches `t`. Rung 1 is `e_k`; rung `K` is `t`. Rung `r` of `L` is a feature point `L[r]`.
- **"Level k of K" always names a ladder instance.** Two goals sharing a cell can show different `K` and different levels. Both read the same evidence (§9.3), and neither changes it.

### 9.2 An observation's conservative tuple and its level on a ladder

- An observation's **conservative tuple** is the easier, per dimension, of the stamped features of the revision the learner answered and that revision's canonical audit (§7.2, §7.5).
- **Every reading is an upper bound.** The conservative tuple takes the easier reading on each dimension. So each reading available now bounds it from above: the stamped tuple, and each audited dimension whose canonical audit has answered. A reading that arrives later can only lower it. The observation's **bound** `u` is the easier, per dimension, of the readings available now.
- **Known below entry: level 0.** If `u` is easier than `e_k` on any ordered dimension, the observation has level 0 on every ladder. That holds now and after any audit, whether the audit is pending, has failed or has tied. Example: a retrieval item stamped `scaffolding = worked` is below retrieval's entry `cue`, whatever its audit will say.
- **Complete: its level.** When the stamped tuple exists and the canonical audit has answered on every audited dimension, `u` is the conservative tuple. Its **level on ladder `L`** is the largest `r` such that it is at least as hard as `L[r]` on every ordered dimension. Below rung 1 it has level 0.
- **Incomplete, and not known below entry: level 1 at most.** This is the legacy fallback, and it applies only where feature information is genuinely missing:
  - the audit is pending, or has failed or tied on some dimension (§7.2);
  - the item has no `task_features` (legacy);
  - the answered revision cannot be resolved (`excluded`, §7.5), so it has no reading at all.

  Such an observation gets level 1 if its capability is known (stamped, or `default_capability_for(practice_mode)`), and never more than level 1, on any ladder. It is labelled "level pending" while an audit can still complete it, and "level not rated" otherwise.
- **One resolution.** A level-pending observation resolves once. That happens when its canonical audit completes it, or earlier, when an answered dimension already shows it below entry.
  - Its level may rise. It may also fall to 0, if the audit reads the item below entry.
  - The canonical audit never changes afterwards (§7.2), so neither does the level.
  - Certification is derived on read. A certificate that rested on the provisional entry credit is re-derived, and a cold probe still pending for a certificate the LO no longer holds is handled exactly as today (§9.4).
  - The AD report counts provisional credits, and how many were later withdrawn.
  - Items are audited after generation or import (§7.2), and AD1's backfill covers existing ones, so an audit still pending when an item is answered is the exception.

### 9.3 The feature-qualified credit ledger (AD4 successor; switch `rung_certification`)

- **`facet_capability_feature_credit`** (DERIVED; owned by the replayer that owns `facet_capability_evidence`). One row per `(attempt, facet, capability)`:
  - the certification credit banked for that cell by exactly the existing rules: direct or embedded, unassisted, group budgets, repeat discounts and caps (`capability_mapping.py:246-288`; `canonical_projection.py:920-1030`), with its direct and embedded parts;
  - the observation's conservative tuple, or, while it is incomplete, its bound `u` and its status (pending, legacy or `excluded`, §9.2); the answered revision's `content_hash`; and the canonical audit ids.

  It stores no ladder and no level number, so no target change can rewrite it.
- **Demonstrated at a point.** A cell is *demonstrated at point `p`* when the credit of its observations whose conservative tuple is at least as hard as `p` on every ordered dimension sums to ≥ `DEMONSTRATED_CREDIT` (1.0, `certification.py:3`).
  - This is within-cell dominance, the feature-ladder analogue of capability dominance (measurement spec B1). There is no discount, because the observation dominates on every dimension. The basis is recorded.
  - Each row's credit is what the cell banked, so budgets and discounts computed over the whole cell are never relaxed for a harder subset. The sum is conservative by construction.
  - Embedded credit from capability dominance (B1) counts toward `e_k` only.
  - Incomplete observations (§9.2: an audit pending, failed or tied; legacy; `excluded`) count toward `e_k` only, unless they are known below entry.
  - Level-0 observations count toward no point at or above `e_k`. That includes observations known below entry while their audit is still missing.
- **"Demonstrated up to level k of `L`"** is the largest `k` such that the cell is demonstrated at `L[k]`. It is computed when read, for any ladder instance, and never stored as a bare number.
- **Never from the posterior.** No level is ever derived from AD's state (A2). The posterior predicts; the ledger demonstrates.

### 9.4 Reconciliation with capability-matched certification

`lo_certification` (`goal_certification.py:275+`) keeps its structure: some recipe with every hard component demonstrated, plus integration evidence. Under AD4:
- **A component is demonstrated** when its `(facet, capability)` is demonstrated at its **requirement point** `p_req`. A requirement is a feature point, never a level number.
  - Default `p_req = e_k`, the entry point (D7). It is the same for every goal.
  - The only change for an LO with no declared requirement is that level-0 observations (heavily scaffolded, below the capability's entry point) stop counting. That is the "trivial item" fix.
- **A declared requirement** may set a harder point (owner decision D7). `p_req` is the hardest point, per dimension, of `e_k` and:
  - an optional `min_task_features` on a blueprint `RecipeComponent` (`vault/models.py:288-293`): a partial `p1_launch@1` tuple whose unspecified dimensions take `e_k`'s value; absent means `e_k`;
  - the next reviewed milestone contract (projected as in §9.1, precedence 2) of every active commitment with a target naming the LO or one of its facets, where the contract's capability is the component's.

  It reads no goal, so `lo_certification` stays a function of the LO, and two goals sharing an LO never see two certification states. Goal-specific targets show as levels of each goal's ladder, never as certification requirements.
- **Certificates bind their requirement points.** Certification is derived on read; there is no durable certificate table. A certificate's id is the content hash of (LO, blueprint, recipe, certified cells), snapshotted onto its cold-probe task and outcome row (`goals/certification_cold_probe.py:46-55`, `:334`). Under AD4 the hashed content also holds, per component, `p_req`, the schema and the ladder version. So:
  - a changed requirement (a revised blueprint, or a commitment moving to its next milestone) yields a new certificate id, never a reinterpreted old one;
  - a cold-probe verdict already recorded keeps the `p_req` of the certificate it judged; a probe still pending for a certificate the LO no longer holds is cancelled or `indeterminate` as `certificate_withdrawn`, exactly as today (`goals/certification_cold_probe.py:1360-1361`, `:1476-1490`);
  - an imported exam or a re-classified unit changes a goal's ladder and its "level k of K" (§9.5), never a requirement: exam targets are not certification requirements (D7).
- **The delayed cold probe** for a certificate is served on an item whose conservative tuple dominates the certificate's recorded `p_req` (`certification_cold_probe.py`). `false_certification_rate` is reported by the level of `p_req` on the default ladder of `k`, which is the same index for every goal, and by capability.
- **Exam pool stratification** moves from LLM-label strata (`exam_pool.py:42-55`) to levels of the exam goal's ladder instance, and records the instance id.
- **Kill switch** `rung_certification = false`: `facet_capability_evidence`, certification and the cold probe are byte-identical to the predecessor (G-AD4-4).
- **Upgrade.** Because a successor can reduce existing certificates on replay (level-0 items stop counting), the upgrade runs the playbook's shadow rebuild on copies and reports every certificate that would change before the version applies (playbook step 7).

### 9.5 Exam and problem-set targets: full mastery (AD4)

**Where target points come from.**
- The exam profile gains `target_feature_points`: per exam or problem-set unit, a `p1_launch@1` feature tuple.
- **Only units whose use mode is `blueprint_only` or `available_for_practice`** (`content/synthesis/source_unit_selection.py:333`) feed it, as router §15.6 requires for anything that steers generation or selection. Their text may be read, so the feature-audit judge classifies each one at ingest.
- Tuples are collapsed one vote per syllabus family (`exam_family_key`, `content/synthesis/exam_profile.py:35-54`).

**Mapping to cells.** A unit's points map to cells only by the unit's own facet mapping, at the unit's capability. A unit without a facet mapping feeds no target in v1. Spreading it over every facet of a goal would let one hard unit raise targets on unrelated facets, and goals do not yet reference the source sets their exams come from (`vault/models.py:136-139` names `source_set_ids` as a future goal field; no goal has it). Unmapped units are counted in the AD report and in `learnloop ad data-check` (Q3); using them at goal scope is deferred (§16).

**The target.** The cell's exam target `t_c` is the per-dimension 0.8-quantile of the cell's family-collapsed points from every practice-available unit (D12). Every goal whose scope holds the cell reads it first (§9.1). A new import or a re-classified unit gives a new `t_c` and so a new ladder instance. Requirements and certificates never read `t_c`, so they are unchanged (§9.4).

**Held-out units are evaluation only** (A8, D14).
- `held_out_evaluation` units are never served and never classified by an AD judge, and they never shape `t_c`, the ladder, selection or generation.
- Where the existing ingest inventory already records feature signals for them (as it records `held_out_task_families`, `exam_profile.py:64`), one evaluation report compares them with the ladder: "share of held-out exam tuples at or below the target level". A low share is an owner-visible finding ("practice aims below the exam") with no automatic action.
- The leakage gate (`content/authoring/practice_leakage.py`) is unchanged.

**Exam-session outcomes.**
- A goal's practice exam (`goals/exam_session.py:1-12`) serves reserved, never-practised pool items and freezes predictions before any answer is graded.
- Under AD, `start_exam` also writes an `item_forecasts` receipt per pooled item (§8.1), so exam-level calibration is scored on the same footing as the incumbent's frozen predictions.
- The answers then apply through the standard attempt pipeline, as today, and AD reads them like any first-surface attempt (§5.6).

**Two labels, never blended,** both per goal and cell, and both naming the ladder instance they read:
- **Full mastery (demonstrated):** the cell is demonstrated at `t_{g,c}`, the top rung of the goal's ladder (§9.3).
- **Ready for exam level (predicted):** `p̄(t_{g,c}) ≥ 0.8`, labelled as a prediction (KM §9.6; `exam_readiness.py:5-12`).
  - It needs a predictor that can predict at a feature point, which the incumbent cannot. So it is shown only once AD is promoted for selection (AD3).
  - Before that, the line reads "exam level: not yet predicted". Demonstrated levels (AD4) do not depend on it.

**Without practice-available exams or problem sets,** the top level is the milestone or default target, and "full mastery" is shown as "top level for this goal".

### 9.6 Ground truth

- The delayed cold probe stays the external check. `false_certification_rate` is reported per requirement level (on the default ladder of `k`, §9.4) and per capability.
- AD3 and AD4 add one metric: the **trivial-success rate**, the share of successes on items whose `p̄ > 0.95` at serve time. It falls when AD works. A high rate before AD is G4 measured.

---

## 10. Integration

### 10.1 Router mixture and exact propensities

- **Order.** The router picks a block with an exact propensity `π_router` (`router/mixture.py`); with the router off, DL1's chooser is deterministic and `π_router = 1`. Later, when a new-material slot of that block is served, AD draws the item with exact propensity `π_AD(i | block, slot, S)` (§6.1). AD never changes how blocks are packed or which candidates the router sees, so `π_router` means exactly what it means today.
- **The joint action.** What is logged is the pair (block, served item), with propensity `π_router(block) · π_AD(i | block, slot, S)`. It is the propensity of that pair, not the marginal probability of the item across blocks. Both factors are logged before exposure, so router R3's doubly-robust replay and an AD replay both have valid importance weights for pair-level policies. They evaluate serving policies *conditional on the pool that existed*. Alternative commissioning policies are not evaluable from these weights (§6.1).
- **Later decisions.** A substitution changes the block's planned minutes, and so the `minutes_left` the router reads at its next decision. That decision logs its own propensity on the state it saw, so the sequential factorization stays exact.
- AD registers its draw as a fifth admissible design, **`feature_overlap`**, in `scheduling/randomization_layer.py:57`. Like `model_mixture`, it declares its own floor (`q/|O|` on the overlap set), and the dormant 0.05 floor never clips it. Outcomes join at the next spaced cold review, as for the other designs (`randomization_layer.py:19-25`).
- **The router's card** (`LearnerStateCardV1`) gains, per LO, after AD3: demonstrated level / K, `P_band` of the next point, and `p̄` at the target. The card's version moves accordingly (plan R2 §3.6).

### 10.2 Daily-plan lanes

- Under AD3, each **new**-lane slot (`new_admitted`, §6.1) is served by AD's draw over its support, one draw per served slot. A slot whose support is empty is displaced. The exception is a slot whose item only pre-exposure ruled out: the predecessor serves it, with no draw (§6.1, step 0). The lane's packing, order, minutes and admission are the predecessor's (`daily_plan/lanes.py:1-27`).
- **push** holds already-attempted items on goal frontiers, and **repair** holds follow-ups and already-attempted items. Neither has a new-material slot, so both are untouched (§6.4).
- **maintain** (due reviews and scheduled checks) is untouched.
- **Kill switch** `selection = false`: no draw and no substitution; every slot serves its planned item, exactly as the predecessor.

### 10.3 The Decider

- **Feature audit** (§7.2): a Tier-1 judgment pattern on the existing `tier1_decider` route, with a `[decider_routes] ad_feature_audit` switch, live at AD1.
- **Forecaster** `llm_v3:decider` (§8.2): a `noul` question. It is scored only, never served before promotion.
- **No new authority.** The Decider does not choose feature points or items. Its block-level role in the router is unchanged.

### 10.4 Field harness arms and promotion

**Arms** added to `learnloop eval` (field §7.2):
- `ad_threshold` (base);
- `ad_threshold+rating` and `ad_threshold+timing`;
- `ad_threshold+outside` (adds `z_v1`; `z_llm`, `z_panel` and `z_origin` are in the base);
- `ad_threshold:grid` (QUEST+-exact grid for `θ_c` with shared parameters at their posterior means, to expose non-Gaussian error near the ceiling);
- `ad_threshold:ts` (Thompson-sampled selection, for the decision-level simulation only).

Each arm's constants are pre-registered in `docs/reviews/adaptive-difficulty-ad2.md` before the first replay on owner data, as T8 did (`field/success_head.py:14-15`).

**Promotion to the active predictor for practice selection** (AD3 entry). The harness's own rule (field §7.4), applied as written, as the owner directed:
- `ad_threshold` (or one sub-arm) beats `mastery_ekf` on report 1's attempt-level log loss, overall *and* on field's first-attempt split (the first attempt on a never-seen LO);
- the bootstrap interval excludes 0, at the margin fixed before the run (field D9);
- report 2's fast-track miss rate, recomputed with AD as the predictor, is no worse;
- "can't tell" keeps the incumbent.

Added by this spec, as further conditions, never replacements:
- a first-surface-in-a-never-seen-*cell* split (a new cell can belong to a seen LO) is reported, and must not be worse;
- **decision-level conditions** (R8):
  - in the replay simulation (AD2), AD-selected practice lands in the band at least as often as the incumbent's waypoint choice;
  - the trivial-success rate is no worse;
  - the band-region reliability error is ≤ 0.05.
- D3 records the alternative (non-inferiority) and why the default follows the owner's direction.

**After promotion:**
- realized success on AD-selected practice (target 0.70–0.80);
- delayed cold success (`R_cold`, router §15.2);
- `false_certification_rate`;
- minutes per demonstrated level.

These are reported every 200 AD selections (`learnloop ad report`). A sustained miss (realized success outside 0.60–0.88 over 200 selections) is flagged at the top of the report and in the glass-box view, with the recommendation to set `selection = false`. The owner flips the switch; code never edits the vault config. The switch restores the predecessor exactly.

### 10.5 Probes, value of information and EVSI

§6.3. VOI stopping (mvp-0.21) and EVSI calibration (`evsi_calibration/`) are unchanged. AD5 changes only the conditionals they read and what is authored.

### 10.6 Exam protection

A8, §9.5. A test plants a sentinel string in a held-out unit. It asserts the sentinel reaches no AD prompt, receipt, payload, `ad_selections` row, audit input or `target_feature_points` entry, and that held-out units never change `t_c` (G-AD1-6, G-AD4-6).

### 10.7 Placement and "assumed known"

- **Placement is unchanged** (field §5.2): its sources (self-report, fast-track on early answers, an activated predictor, the quick check), and the first-review check that confirms an assumption.
  - That check stays in the maintain lane, whatever the item's attempt history (`daily_plan/lanes.py:6-8`), with placement's own item choice. This keeps §10.2's "maintain untouched" true.
  - Letting AD choose the check item at level ≥ 1, so that "assumed known" is checked at a level, is deferred (§16).
- **"Too easy / too hard" and "easier / harder" taps keep their existing effects** (D8). They happen after feedback, so they fail the rating contract (§5.4, a pre-feedback tap), and AD does not read them in v1. A separate post-feedback observation model is deferred (§16).

---

## 11. Replay, versioning, persistence

### 11.1 Successors and switches

| Phase | Successor? | Switch(es) under `[adaptive_difficulty]` (false = predecessor exactly) |
|---|---|---|
| AD1 measure and log | **No.** It adds receipts (forecasts and frozen serve inputs), two nullable attempt columns (rating, first-hint progress) and audit judgments, but changes no persisted meaning and nothing served | `forecast_receipts`, `outside_forecasters`, `rating_tap`, `feature_audit` (Decider switch `ad_feature_audit`) |
| AD2 the arm | No. An offline harness, plus `ad_threshold` receipts written at serve time; nothing served changes | `forecast_receipts` (shared with AD1) |
| AD3 practice in the band | **Yes** (next free tag at merge) | `selection`, `generation_contract` |
| AD4 levels and full mastery | **Yes** | `rung_certification` |
| AD5 probes that discriminate | **Yes** | `probe_targeting` |

- **Master switch.** `adaptive_difficulty.enabled = false` turns every AD behaviour off, logging included.
- **Version gating.** Successor gates follow the playbook: a serving change acts only at its tag or later (`algorithm_versions.successors_from`).
- **Upgrades.** Each upgrade function chains through the previous one, prepares the projection before the atomic version write, and leaves the prior version readable on failure (playbook step 3).
- **Defaults snapshots.** Each successor records one (playbook step 4).

### 11.2 Tables

| Table | Role | Contents | Rebuilt by |
|---|---|---|---|
| `practice_attempts.difficulty_rating` | RAW_LEDGER column (nullable) | `easy` / `about_right` / `hard`, tapped before feedback | — |
| `practice_attempts.first_hint_progress` | RAW_LEDGER column (nullable) | `no_draft` / `draft_started`: whether an answer had been started when the first ordinary hint was revealed (§5.3). The practice screen reads the same marker it already sends with tutor questions (`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:284-285`) at the first hint reveal (`:619`), keeps it in the saved draft, and sends it on submit. Null on every earlier row, from clients that do not send it, and while `forecast_receipts` is off; null reads as `unknown` | — |
| `item_forecasts` | RECEIPT (append-only) | §8.1, with `scope` (`presentation` / `item`) | never cleared |
| `item_forecast_payloads` | WORKFLOW | raw outside-forecaster responses; pruned after `router.payload_retention_days` | — |
| `item_serve_inputs` | RECEIPT (append-only) | §7.5: per presentation of a never-attempted item, the served revision's hash, stamped and resolved features with audit ids, the signal vector with receipt ids, `pre_exposed`, the resolution version | never cleared |
| `judgment_ledger` rows, task `ad_feature_audit` | RAW_LEDGER (existing) | §7.2, with the audited revision's `content_hash` | — |
| `ad_selections` | RAW_LEDGER (append-only) | decision id, `kind` (`serve` / `commission`), cell; for a serve draw, the block id, slot position and slot item; mode (`band` / `calibrate` / `predecessor`); the support (or commission candidates) with `P_band`, `p̄`, `I_c`, `π`, and each excluded candidate's failed check; seed; the chosen item (serve) or feature point (commission); `empty_support`; state hash; versions | — |
| `item_substituted` block event | a new `kind` in the existing `attention_block_events` ledger (migration 096; `kind` is free text, so no migration) | §6.1 step 5: slot item, drawn item, both estimates, the `ad_selections` id; folded by `daily_plan/records.py:357-410` | — |
| `ad_commission_results` | RECEIPT (append-only) | per landed commission: the `ad_selections` id, the generated item, its audited features, `p̄(i)`, in band or `realized_out_of_band` (§7.4) | never cleared |
| `ad_state` | DERIVED | current posterior: cell moments and shared parameters, sparse covariance | AD replayer |
| `ad_attempt_trace` | DERIVED | per eligible attempt: prior and posterior `η` moments, category probabilities, information gained, `input_status` (§7.5) | AD replayer |
| `item_forecast_scores` | DERIVED | §8.3 | forecast-score replayer |
| `facet_capability_feature_credit` | DERIVED | §9.3: per (attempt, facet, capability), banked credit and the conservative tuple; no level numbers | canonical-projection replayer (same owner as `facet_capability_evidence`) |

- Each new table is classified in `db/table_roles.py`. Each DERIVED table has exactly one registered replayer in `substrate/rebuild_orchestrator.py`, and both facts are tested (CLAUDE.md).
- Migrations take the next free numbers at implementation time. The head is 202 at this base (`migrations/202_router_staged_frame.sql`). The migration-head fixture is renamed and its five hard-coded paths and references regenerated, per CLAUDE.md.

### 11.3 Replay invariants

- **Zero model calls in replay.** The AD state is a pure function of the attempt ledger, the `item_serve_inputs` and `item_forecasts` receipts, `judgment_ledger` audit rows, `practice_item_snapshots`, and `ad_priors_v1`. Current vault content is read only for a historical attempt resolved `reconstructed_current` under the field's explicit fallback (§7.5). Outside forecasts are read from receipts and never re-asked.
- **Deterministic rebuilds.** Two rebuilds are byte-identical.
- **AD never touches evidence.** Mastery, facet recall, FSRS, `grading_evidence` and `facet_capability_evidence` are byte-identical with AD on vs off. This is enforced by an import-linter contract forbidding the AD package from importing evidence writers. AD4's feature-credit ledger is the one exception: it is written by the canonical projection, not by AD.

### 11.4 Config (new section)

```toml
[adaptive_difficulty]
enabled = true
forecast_receipts = true
outside_forecasters = ["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]   # D4; spend-capped
rating_tap = true
feature_audit = true
selection = true            # acts at the AD3 tag or later, after promotion
generation_contract = true  # AD3 tag
rung_certification = true   # AD4 tag
probe_targeting = true      # AD5 tag
practice_band = [0.70, 0.80]
overlap_band = [0.55, 0.90]
overlap_share = 0.10
near_tie_margin = 0.05
calibrate_below = 0.35
exam_target_quantile = 0.8
ready_threshold = 0.8
exam_target_calibration = false   # §6.2, D12
priors = "ad_priors_v1"
ladder = "ad_ladder_v1"
daily_spend_cap_usd = 0.50        # outside forecasters on paid routes
```

---

## 12. What the learner sees (frictionless defaults)

- **Practice feels right, and nothing new is required.** There is no placement ceremony and no difficulty slider.
- **The optional one-tap rating.** Next to Submit: "Felt: easy · about right · hard".
  - It is not preselected and never required.
  - It is captured before feedback, beside the existing pre-answer confidence tap (`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:211`).
  - It can be hidden for the session with one tap, and the choice is remembered (browser storage, per viewer).
- **"Why this item"** (one line, by the draw that chose it, like router §7.4):
  - band: "Picked to be challenging but doable for you (about a 3 in 4 chance)";
  - overlap: "A different kind of question, to keep LearnLoop's picture of you accurate";
  - calibrate: "A question to find your level here".
- **Levels on the map and the LO page:**
  - "Shown at level 2 of 4" (Demonstrated), on the ladder of the goal in view (§9.1); with no goal in view, the default ladder;
  - with an exam target: "Exam level: not yet shown · likely ready" (Ready, labelled as a prediction).
  - Well depth and beads are unchanged by AD; the level is a label beside them (A9).
- **No jargon.** "Level", not rung; "chance", not probability.
- **Glass box on demand:**
  - the items behind each level, with dates;
  - the forecast numbers from each forecaster;
  - the feature point an item was written for, and the audit's reading of it;
  - the identifiability statement (§5.8).
- **Too easy / too hard / easier / harder** keep working as today (D8).

---

## 13. n>1: pooled priors from consented data

- **What pooling can supply.** Population priors for `β`, `ψ_k`, `α`, `γ` and `ζ`, and the residual variance `τ0²` per generator family and version. These are exactly the quantities n=1 identifies weakly or not at all.
- **What stays local.** Personal cell abilities, always.
- **Staged path** (worker f, R12):
  1. **One learner (now).** A-priori priors, prior-predictive checks, sensitivity analysis and chronological scoring (§5.5, §8).
  2. **Opt-in pilot.**
     - Pool `β`, family residual variances, `γ`, `ζ` and `α` across consenting learners.
     - Validate on held-out learners *and* held-out item families.
     - Return the result as a versioned artefact (`ad_priors_v2`) through the playbook, like any change of persisted meaning (storage spec §6.12).
  3. **Transfer.** Robust mixture priors keep a vague component, so an unusual learner or a new generator escapes a misfitting population prior `[schmidli2014]`. Never count a learner's own history again through a pooled prior that includes it.
  4. **Private scale-up.**
     - Privacy at the learner level, not the item level `[liu2020]`.
     - Secure aggregation `[bonawitz2016]`.
     - Differentially private release of shared parameters with abilities kept local `[steiner2018]`, `[zhou2025]`.
- **Requirements this spec adds to the contribution export** (storage spec R13 / §6.12, phase S9). Structured fields only, no text:
  - audited and stamped feature tuples, and generator family and version;
  - `item_forecasts` (p values, forecaster ids and versions; payloads excluded);
  - `ad_selections` with propensities;
  - outcome categories (§5.3) with the help timing `h_t`, `primed` and `pre_exposed`;
  - optional ratings, and latency with the learner's own prior answer-time estimate beside it (§5.4), so the normalization can be rebuilt.

  These keep pooled estimation of feature effects possible without a retrofit.
- **Trigger** (§16): the S9 export is built and at least 20 consenting learners have at least 200 first-surface attempts each.

---

## 14. Phases, gates and fail-first tests

Each test below is written first, and fails on today's code for the stated reason. All tests use fakes. The paid forecasters' interfaces are verified by the existing route tests and one dry-run.

### AD1: measure and log (no successor)

**Builds:**
- migration: `item_forecasts` (with `scope`), `item_forecast_payloads`, `item_serve_inputs`, `practice_attempts.difficulty_rating`, `practice_attempts.first_hint_progress`;
- table roles;
- the serve-input receipt (§7.5) and the in-process forecasters `mastery_ekf` and `lo_general+composite`, written in the serve transaction;
- outside forecasters behind `outside_forecasters`, spend-capped: `llm_v1:item` once per item revision when it is prepared for the pool, plus its one-time backfill; `llm_v3:*` asynchronously per presentation (§8.2);
- the feature audit (§7.2) and its owner-run backfill;
- the rating tap (§12) and the first-hint progress marker (§11.2);
- `learnloop ad data-check`: the §3.3 tables on a backup copy, plus first-surface attempts per cell, coverage of latency, ratings and hint timing, exam units with and without a facet mapping (Q3), and historical attempts by revision status (§7.5).

**Gate:** G-AD1-1 to G-AD1-10.

| Id | Test (fails today because…) |
|---|---|
| G-AD1-1 | `test_forecast_receipt_written_in_serve_transaction`: serving a plan item writes one `item_forecasts` row per in-process forecaster in the same transaction as `plan_presentations`, with `inputs_as_of ≤ served_at` (no such table) |
| G-AD1-2 | `test_late_outside_forecast_is_valid_if_inputs_predate_serve` and `test_forecast_with_post_serve_inputs_is_invalid` (no validity rule) |
| G-AD1-3 | `test_rating_tap_optional_never_blocks_submit`: submit without a rating succeeds; the rating is stored only when tapped and only before feedback (no column) |
| G-AD1-4 | `test_feature_audit_ledgered_with_fallback`: Decider argmax per dimension, tie is no answer, LLM fallback recorded (no audit task) |
| G-AD1-5 | `test_ad1_switches_restore_predecessor`: all four switches false ⇒ no new rows, prompts byte-identical, no extra calls |
| G-AD1-6 | `test_held_out_sentinel_never_reaches_ad_inputs`: a sentinel in a held-out unit appears in no AD prompt, receipt, payload or audit input |
| G-AD1-7 | `test_replay_reads_receipts_zero_model_calls`: rebuild with model constructors forbidden |
| G-AD1-8 | `test_serve_inputs_frozen_against_later_audit_and_edit`: an audit that lands after the serve, a re-audit and an item edit change no `item_serve_inputs` row; the served revision is in `practice_item_snapshots` (no receipt today) |
| G-AD1-9 | `test_item_only_forecast_enters_inputs_only_if_received_before_serve`: an `llm_v1:item` receipt prepared with the pool appears in the first serve's `z_i`; one received after the serve is scored but absent from that serve's inputs (no item-scoped receipt today) |
| G-AD1-10 | `test_first_hint_progress_recorded_and_missing_is_null`: a first hint revealed with an empty answer stores `no_draft`, after typing `draft_started`; a restored draft keeps the marker; a client that sends none stores null (no column today; `field/probability_states.py:98-101`) |

### AD2: the arm (offline; pre-registered)

**Builds:** the AD replayer (`ad_state`, `ad_attempt_trace`); in-process `ad_threshold` receipts at serve time (scored, not served); arms in `learnloop eval` (§10.4); `learnloop ad report` (prequential metrics, band-region reliability, identifiability diagnostics, sensitivity); simulation recovery on `sim/` synthetic learners with known `θ_t`, `β`, `γ`.

**Gate:** G-AD2-1 to G-AD2-17, then the owner reads the report once on a backup copy (owner-run, field §7.3 style).

| Id | Test |
|---|---|
| G-AD2-1 | `test_trivial_success_barely_moves_ability` (**fail-first, the core question**): with `θ_c` posterior mean 1.0, an unassisted success on an item whose features put its demand at −3.0 moves the mean by < 0.02; a success at demand ≈ 1.0 moves it by ≥ 0.2; a failure on the trivial item moves it by ≥ 0.5 (no feature-based demand exists today; the canonical path is difficulty-blind, G3) |
| G-AD2-2 | `test_overclaimed_features_do_not_lower_demand_estimate`: audited features override stamped ones in the likelihood |
| G-AD2-3 | `test_rebuild_byte_identical` and `test_zero_model_calls` |
| G-AD2-4 | `test_ad_never_writes_evidence` (import-linter contract plus byte-identical evidence tables with AD on vs off) |
| G-AD2-5 | `test_self_report_and_held_grades_excluded`; `test_repeat_surface_attempts_excluded` |
| G-AD2-6 | `test_rating_subarm_off_is_identical_to_base` (no double counting) |
| G-AD2-7 | `test_confound_detected_under_monotone_schedule`: a simulated learner with true growth and **no** feature effect, served monotonically harder points, yields `β` labelled "confounded" by the diagnostic |
| G-AD2-8 | `test_feature_effects_recovered_under_overlap`: the same learner under `ad_select_v1` (`q = 0.10`, single-dimension commission neighbours) recovers each true `β` within 2 posterior sd in ≥ 90% of 200 seeds; directions aliased by design are reported "prior-dependent", not recovered |
| G-AD2-9 | `test_band_probability_exact`: `P_band` from §5.7 matches 10⁶-draw Monte Carlo within 1e-3, including band edges outside `F_x`'s range |
| G-AD2-10 | `test_joint_attempt_factor_integrates_residual_once`: with a rating and a timing present, the update matches brute-force joint integration over `ε_i` within 1e-6, and differs from the product of separately marginalized factors |
| G-AD2-11 | `test_link_parameters_always_valid`: for any values of `(c_1, d̃, ρ̃)`, rating category probabilities lie in [0,1] and sum to 1 |
| G-AD2-12 | `test_claims_applied_at_created_at_and_request_claims_excluded`: a claim never moves an attempt that precedes it; `rung_variant_request` and `learner_report` claims never enter the state |
| G-AD2-13 | `test_warmth_uses_only_pre_serve_exposures`: an exposure after the serve time never changes `w_t` or the receipt's `p` |
| G-AD2-14 | `test_help_and_reveal_are_censored_not_dropped` (**the estimand**): a simulated learner asks for help or reveals the answer more often the lower its ability. Over 200 seeds, AD's predicted unassisted-success rate matches the simulated rate within 2 posterior sd in ≥ 90%, while a variant that drops assisted attempts overestimates it. Changing the correctness of a revealed attempt never changes the update |
| G-AD2-15 | `test_unknown_hint_timing_never_read_as_after_work`: a success with ordinary hints and no marker, and one with a help-equivalent tutor question and no progress marker, both enter as censored `{0, 1}`; with `draft_started` they are category 1, with `no_draft` category 0 |
| G-AD2-16 | `test_replay_uses_frozen_inputs_and_explicit_history`: each attempt's factor is built from its `item_serve_inputs` row, never the current item; historical attempts resolve `exact`, `reconstructed_current` only under the field's fallback, else `excluded`, and `excluded` attempts never update |
| G-AD2-17 | `test_pre_exposed_presentation_excluded_from_update_and_scoring`: a reveal sum at the auto-prime threshold before `served_at` removes the item from `P_c`, sets `pre_exposed`, and the attempt neither updates nor is scored |

### AD3: practice in the band (successor; switches `selection`, `generation_contract`)

**Needs:** AD2 report read; the §10.4 promotion rule met on owner data.

**Builds:** `ad_selections` and `ad_commission_results`; the `feature_overlap` design; lane integration; serve and commission draws; the generation contract (§7.1); re-forecast (§7.4); "why this item"; card fields.

| Id | Test |
|---|---|
| G-AD3-1 | `test_propensity_recomputes_from_logged_row` and `test_seed_reproduces_draw` |
| G-AD3-2 | `test_generation_prompt_has_no_band_language_under_successor` (**fail-first**: `practice_generation.py:1919` contains the band instruction today) |
| G-AD3-3 | `test_selection_switch_off_restores_lane_order` (byte-identical plans on fixture copies) |
| G-AD3-4 | `test_exam_reserved_and_retired_items_never_selected`; `test_coordination_requires_envelope` |
| G-AD3-5 | `test_calibrate_mode_prefers_overlap_band`; `test_calibrate_with_empty_overlap_picks_nearest_to_band` |
| G-AD3-6 | `test_joint_propensity_logged_with_router_block` |
| G-AD3-7 | `test_commission_result_appended_never_mutates_selection`: an out-of-band landed item gets an `ad_commission_results` row and is not served for that commission |
| G-AD3-8 | `test_serve_propensity_is_over_existing_items`; `test_empty_overlap_sets_q_zero`; `test_empty_support_makes_no_draw_and_displaces`; `test_empty_pool_commissions_at_generation` |
| G-AD3-9 | `test_item_over_block_budget_not_in_support` (**fail-first**: no slot substitution exists today): an otherwise eligible item whose estimate exceeds the slot item's plus the block's, plan's or lane's slack is not in `S`; after any substitution the block is within 15 minutes and the plan within its budget |
| G-AD3-10 | `test_support_respects_constraints_reversibility_and_admission`: an item the constraint engine refuses, one holding an open cold check or a reserved surface, one planned elsewhere, and a costlier item for a floor-admitted slot are never in `S` |
| G-AD3-11 | `test_draw_after_block_choice_with_pair_propensity`: AD draws only at a `new_admitted` slot of the chosen block, inside the serve transaction; the logged pair propensity is `π_router · π_AD`; router candidates and `π_router` are byte-identical with AD on vs off; `item_substituted` folds into the plan record |
| G-AD3-12 | `test_support_rechecked_at_draw_slot_item_included` (**fail-first**: before a serve, reconciliation re-checks only status and serving blocks, `daily_plan/engine.py:1925-1931`). After a block is admitted and before its slot is served, the slot item becomes exam-reserved, gains an open cold follow-up, is revealed within the cold retrieval delay, reaches the pre-exposure threshold, or is refused on a fresh snapshot. The same is done, separately, to another candidate. None of them is in `S`. A slot item with no other candidate is displaced with `ad_ineligible`, except in the pre-exposure-only case, which is served with `mode = predecessor` and `π_AD = 1`. With `selection = false` the predecessor serves the planned item byte-identically |

### AD4: levels and full mastery (successor; switch `rung_certification`)

**Needs:** AD1 audits running (levels use audited features). It does **not** need AD3: demonstrated levels come from the ledger, not the predictor. The predicted "ready for exam level" line appears only after AD3 promotion (§9.5).

| Id | Test |
|---|---|
| G-AD4-1 | `test_level_2_not_demonstrated_by_level_1_successes` (**fail-first**: today any capability-matched success counts, G4) |
| G-AD4-2 | `test_level_uses_easier_of_stamped_and_audited` |
| G-AD4-3 | `test_level0_items_earn_no_certification_credit`; `test_legacy_items_capped_at_level_1` |
| G-AD4-4 | `test_switch_off_certification_byte_identical` |
| G-AD4-5 | `test_ready_and_demonstrated_never_blended` (vitest on the map and LO page) |
| G-AD4-6 | `test_exam_target_uses_practice_available_units_only`: `t_c` is unchanged when held-out units are added or removed; held-out tuples appear only in the evaluation report |
| G-AD4-7 | `test_cold_probe_served_at_certificate_requirement_point` |
| G-AD4-8 | Shadow rebuild on owner copies reports every certificate that changes (playbook step 7; owner-run) |
| G-AD4-9 | `test_two_goals_sharing_a_cell_read_their_own_ladders`: goals with different targets show different `K` and levels from the same feature-credit rows, and the shared LO has one certification state |
| G-AD4-10 | `test_target_revision_keeps_existing_certificate`: a new exam import or re-classified unit makes a new ladder instance and changes no requirement; a reached milestone makes a new certificate id; the earlier certificate's id, `p_req` and cold-probe verdict are unchanged |
| G-AD4-11 | `test_level_pending_until_canonical_audit`: an observation stamped at or above `e_k` counts toward `e_k` only until its revision's canonical audit lands. It is then counted once at its audited level, which may be 0. A later run of the same audit version changes nothing |
| G-AD4-12 | `test_known_below_entry_never_credited_while_audit_missing`. A retrieval item stamped `scaffolding = worked` earns no credit at `e_k` or above in three states: while its audit is pending, after the audit fails or ties on a dimension, and after it lands. A legacy item whose canonical audit reads below entry is level 0. Only observations with genuinely missing readings fall back to entry credit |

### AD5: probes that discriminate (successor; switch `probe_targeting`)

| Id | Test |
|---|---|
| G-AD5-1 | `test_probe_prompt_has_no_difficulty_band_under_successor` (**fail-first**: `practice_generation.py:1984`) |
| G-AD5-2 | `test_eig_matches_marginalized_conditionals`: candidate EIG equals a brute-force computation over the residual and `β` uncertainty within 1e-6; identical conditionals give zero |
| G-AD5-3 | `test_capability_hypotheses_get_ad_conditionals` |
| G-AD5-4 | `test_switch_off_probe_selection_identical` |
| G-AD5-5 | `test_composed_snapshot_scores_and_updates_identically` (**end to end**): candidate EIG, the committed snapshot's `compiled_likelihood_hash` and the posterior update after the answer use the same composed rows; an AD state change after the commit changes no update; the probe audit's hash check passes |
| G-AD5-6 | `test_composition_scope`: a rubric above 4 points, misconception, `confuses_with`, `surface_only`, `schema_without_transfer` and `other_or_unknown` slots keep the card's rows exactly; an aliased label reads its slot's composed row; a constraint with probability below 1e-6 is left uncomposed and recorded |
| G-AD5-7 | `test_composed_success_marginal_survives_grader_channel` (**non-identity channel**). Under the contrast family's channel (six outcomes, reliability 0.90), a composed slot with `q_h = 0.80` has an observed success probability of 0.80 within 1e-12; composing before the channel would give 0.724. Its within-class shapes are those of the grader-composed calibrated row. An instrument with no composed slot has conditionals and `compiled_likelihood_hash` byte-identical to today's |

**Order.** AD1 now. AD2 in parallel with AD1: its replayer and harness arms read existing ledgers and resolve attempts historically (§7.5) until AD1's receipts exist. Its serve-time `ad_threshold` receipts write into AD1's `item_forecasts`, so that part lands after AD1 merges. AD4 can follow AD1 without waiting for AD3. AD3 waits for promotion. AD5 follows AD3.

---

## 15. Owner decisions, with recommended defaults

| # | Decision | Recommended default |
|---|---|---|
| D1 | Practice band and what "success" means | `[0.70, 0.80]`; success = first unassisted response at correctness ≥ 0.8 (the cold probe's definition). The research supports a band in this region without fixing a number (R5) |
| D2 | Outcome categories (§5.3): help-adjusted success counts as "partial"; early help counts as fail; unknown help timing and answers revealed during the presentation are censored as "not an unassisted success" | Yes, aligned with field's hint arm (graded outcome by help depth). Training and scoring read the same event, so assisted presentations are never dropped from training |
| D3 | Promotion rule for AD3 selection | **The harness's own rule (field §7.4: superiority on log loss, overall and on the first attempt at a never-seen LO; report 2's miss rate no worse), plus this spec's added cell-level and decision-level checks**, as the owner directed. Alternative: non-inferiority for *selection only*, since the incumbent cannot predict at feature points it has never authored. Revisit if "can't tell" persists after 300 first-surface attempts |
| D4 | Live outside forecasters | On: the item-only LLM once per item revision when it is prepared for the pool, with a one-time backfill; the LLM with history (Codex on the subscription) and the Decider (OpenRouter, ~$0.50/day cap) per presentation. Learning trust needs hundreds of outcomes (§8.3), so collection should start early. Off the critical path |
| D5 | Rating tap placement | Beside Submit, before feedback; optional; hideable per session |
| D6 | Overlap exploration share | `q = 0.10` over items with `[0.55, 0.90]` predicted success |
| D7 | Required level for certification | The capability's entry point `e_k` (level 1 on every ladder), unless a commitment's milestone contract or a component's `min_task_features` sets a harder feature point (§9.4). Requirements are feature points, never level numbers. Full mastery is a separate label, never a certification requirement by default |
| D8 | Learner "easier/harder" and "too easy/too hard" | Keep today's owner-approved effects (self-report evidence package, claims). AD excludes the `self_report` rows and the claims these requests write (`rung_variant_request`, `learner_report`). It does not read the requests themselves in v1, because they come after feedback (§10.7). Nothing is counted twice. Replacing the 0.3-mass package is a separate decision (§16) |
| D9 | Feature-audit judge | Decider Tier-1 pattern, LLM fallback; certification uses the easier of stamped and audited features |
| D10 | AD observations | First graded attempt per surface group only; repeats stay FSRS's |
| D11 | Keep the generator's `difficulty` label | Yes, as signal `z_llm` with a learned weight (§3.3 shows it carried information here); never as the item's difficulty under AD |
| D12 | Exam target and exam-target calibration | Target = the per-dimension 0.8-quantile of family-collapsed tuples from practice-available exam/pset units; exam-target calibration (§6.2) off by default |
| D13 | Should the AD4 upgrade apply even if the shadow rebuild shows certificates changing? | Yes, after the owner reads the diff once. A certificate resting only on level-0 items was not a demonstration |
| D14 | Held-out exam features | Evaluation only. The target level comes from practice-available exam and problem-set units (router §15.6). Held-out tuples, where ingest already records them, feed only the coverage report (§9.5). The owner's 2026-10-14 framing ("only its features") is honoured without letting held-out units steer practice. Override: let held-out tuples define the *full-mastery label* (never the ladder, selection or generation), at the cost of a second target |

---

## 16. Deferred, with triggers

| Deferred | Trigger |
|---|---|
| Per-family discrimination `a` | ≥ 3 generator families with ≥ 30 first-surface attempts each, and harness misfit in the slope (reliability-curve tilt) |
| Several candidates per commission, pick by re-forecast | Realized out-of-band rate > 40% over 100 commissions after AD3 |
| Grid or particle filter replacing ADF | `ad_threshold:grid` beats the base arm on band-region reliability with an interval excluding 0 |
| POMDP planning or amortized design policies `[rafferty2016]`, `[foster2021]` | A simulator validated against this learner's held-out data, and ≥ 1,000 AD decisions |
| LLM simulated-student panels as an item-side signal `[acquaye2026]` | A panel reaching ρ ≥ 0.5 against this learner's first-surface outcomes on ≥ 100 items |
| Band experiment: randomize the band centre by cell (0.70 / 0.75 / 0.85) and compare delayed cold success and minutes per level | ≥ 300 AD-selected practice attempts with matured `R_cold` |
| Per-capability bands | The band experiment shows a capability interaction |
| Reference anchor families (fresh instances of a stable family at a fixed point) | The confound diagnostic labels any `β` dimension "confounded" in two consecutive reports |
| Repeat-attempt observations in AD (a joint FSRS + AD arm) | AD promoted, and the FSRS-plus-AD arm beats both in the harness |
| `teach_back` as an AD observation | A dialogue-to-outcome mapping validated in the harness (router §15.1 summaries exist) |
| Replace the 0.3-mass self-report package with rating-only evidence | Owner decision after AD2 shows `+rating` earning activation |
| Post-feedback request taps (easier/harder, too easy/too hard) as a separate, timestamped AD observation bound to their attempt | `+rating` earns activation, and ≥ 50 such taps exist |
| AD chooses placement's first-check item, restricted to level ≥ 1 | AD promoted (AD3), and the placement assumption report shows first-check misses on items below the entry level |
| Serving the forecast ensemble (§8.4) | An ensemble beats the active predictor on log loss with an interval excluding 0 |
| Learning-progress bandit over families `[clement2015]` | Families with ≥ 5 recurring members per cell exist in a vault |
| `representation`, `time` and other `tools` dimensions | Items in a vault vary on them (data-check shows ≥ 2 levels with ≥ 20 items each) |
| Per-goal exam targets: a goal reads only the exam and problem-set units of its own source sets (§9.1, §9.5) | Goals gain `source_set_ids` (named as future in `vault/models.py:136-139`) and exam units record their source set |
| Exam units without a facet mapping feeding targets at goal scope (§9.5) | Per-goal exam targets exist, and data-check shows unmapped units are ≥ 25% of a goal's practice-available exam units |
| A joint model of help-seeking (asking for help or the answer as its own outcome, sharing `η`), as a harness arm against the censored factor of §5.3 | The AD report shows help or a reveal on ≥ 20% of first presentations over 200 of them |
| Pooled priors (§13) | The S9 export is built, and ≥ 20 consenting learners each have ≥ 200 first-surface attempts |
| Federated or differentially private estimation | Pooled priors are computed anywhere other than the contributor's own machines |

---

## 17. Open questions

1. **Q1. Current data.** The §3.3 numbers come from the two-month-old committed snapshot. The same measurement on backup copies of the current working vaults was not run in this stage. AD1's `learnloop ad data-check` reproduces it on the owner's copies (owner-run). Until then, the label-weight prior `α_llm` (§5.5) rests on one stale vault.
2. **Q2. Generator compliance.** How often does the generator realize the requested feature point, by the audit's reading? Unknown until AD1 audits run. A low rate would make the feature model weak and push the "several candidates" trigger.
3. **Q3. Unit-to-facet mapping for exam targets.** How many exam units carry a facet mapping in the inventory? A unit without one feeds no target in v1 (§9.5); spreading it over a goal's facets is deferred (§16). Measured by AD1's data-check, which counts mapped and unmapped units.
4. **Q4. Rating timing.** Is a pre-feedback tap acceptable friction, or should the rating ride the existing post-feedback "too easy/too hard" controls (fewer taps, outcome-contaminated)? D5 recommends pre-feedback; the AD2 `+rating` arm will show whether it earns its place.
5. **Q5. Data volume for promotion.** With about 10³ attempts a year and the §8.3 illustration, superiority (D3) may take months to resolve. The owner may prefer to revisit D3 at AD2's first report.
6. **Q6. Motivation vs learning.** The research shows easier practice wins short-term engagement and harder practice wins learning `[papousek2016]`. Should the band move with the learner's session state (re-entry after a gap; frustration signals) before the band experiment reports? This spec keeps it fixed.

---

## 18. Agent prompt template (one per phase)

Fill in `<n>` (1–5), the base commit and the worktree path. Give it to a fresh agent in the repo. The Codex review and fix steps follow `implementation_goal.md` §2. This spec stage itself was docs-only: it changed no code, ran no paid call, and its record is `docs/reviews/adaptive-difficulty-spec.md`. Everything below is for the implementing phases.

```text
You are implementing LearnLoop stage "adaptive-difficulty-ad<n>" (AD1 | AD2 | AD3 | AD4 | AD5)
of docs/specs/spec_adaptive_difficulty_v1.md, in the worktree <path> on branch
adaptive-difficulty/ad<n> (base <commit>).

Read first: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules and
invariants); docs/algorithm-change-playbook.md; the spec's §2 (standing constraints),
§3.1 (code truth; re-check every citation you rely on), §5 (model), §11 (successors,
switches, tables, replay invariants) and your phase's row in §14 with every section it
cites; db/table_roles.py. Then write a short plan (files, migrations, successor and kill
switches, spend caps and model routes, judgment_ledger writes, tests) to
docs/reviews/adaptive-difficulty-ad<n>.md and proceed.

Prerequisites (§14 "Order"): AD1 and AD2 can start from main, but AD2's serve-time
receipts need AD1's item_forecasts merged; AD4 needs AD1 merged (audits); AD3 needs AD2
merged, its report read by the owner and the §10.4 promotion rule met on owner data; AD5
needs AD3. If yours is not met, stop and say so.

Build exactly your phase: its "Builds" list, its tests (each written first and failing
for the stated reason), its switches. AD1 and AD2 change nothing served. AD3, AD4 and AD5
are successors: each takes the next free mvp-0.N at merge, and with its switch false the
behaviour is byte-identical to the predecessor. Never write evidence, mastery, FSRS or
certification from AD's state (A2). AD2 pre-registers each arm's constants in
docs/reviews/adaptive-difficulty-ad2.md before the first replay on owner data.

Paid routes: the feature audit on the existing tier1_decider route (the Decider,
perplexity/pplx-decider-v1.1-27b on OpenRouter) with its LLM fallback; llm_v1:item and
llm_v3:llm (Codex on the owner's subscription, recorded estimated_only); llm_v3:decider.
All go through the spend framework with --dry-run, inside
adaptive_difficulty.daily_spend_cap_usd, and append to judgment_ledger.

Hard rules:
- Work only in your worktree; never edit the main checkout; never commit changes to
  fixtures/linear_algebra, fixtures/probability or fixtures/arxiv_v2.
- Tests use fakes (tests/structured_ai.py StructuredClientFake; tests/helpers.py builders).
- Paid calls only on backup-API copies (learnloop.db.copies.copy_tree_with_databases) under
  fixtures-local/, dry-run first, inside caps; record calls and cost in your review file.
  Never read ~/.config/learnloop or any .env file; the app loads keys itself.
- Migrations from the next free number; classify tables (a DERIVED table has exactly one
  replayer); upgrade the head fixture (CLAUDE.md).
- Pin new or extended sidecar RPCs desktop-only in tests/test_mobile_allowlist.py.
- If the spec contradicts the code, record it in the review file and take the conservative
  option (switch off, no evidence writes) if work can continue, else stop.
- Don't merge, push, rebase onto other branches, or delete branches or worktrees.
- End every commit message with: Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

Done means: your phase's gate tests pass; uv sync --extra dev --extra mobile;
TMPDIR=<path>/fixtures-local/tmp uv run pytest -n auto; uv run pytest -m durability;
uv run lint-imports --no-cache; npm run typecheck && npm test if the app changed; the DB
reference generate and validate scripts if the schema changed; a shadow rebuild on a
fixtures-local copy for any successor; git diff --check. Owner-run commands (the AD1
backfills, learnloop ad data-check and learnloop ad report on the owner's copies, AD4's
shadow rebuild) are listed in the review file, dry-run first, never run by you on the
working vaults.

Return: summary, final commit, review file path, gate results with pass counts, owner-run
commands, open questions.
```

---

*Related: `spec_learner_field_v1.md` · `spec_action_router_v1.md` §15.5–15.6 · `plan_router_r2_v1.md` §5 · `spec_measurement_efficiency_v1.md` §3–5 · `spec_probe_eig_redesign.md` §2.3, §7 · `spec_storage_sync_v1.md` §6.12 (branch) · `docs/algorithm-change-playbook.md` · research appendix `docs/specs/research/adaptive_difficulty_sources_v1.md`*
