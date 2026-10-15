# Adaptive difficulty and mastery: practice in the band, probes that discriminate, levels that mean something (v1)

**Status:** drafted 2026-10-14 at the owner's request, on branch `docs/adaptive-difficulty-spec` from main `4108e1ccd` (`mvp-0.24`). Spec only: no code changes. Decision-ready: every owner decision in §15 has a recommended default, which is accepted unless the owner overrides it at its checkpoint (owner decision 2026-10-12).

**Research appendix:** `docs/specs/research/adaptive_difficulty_sources_v1.md`. It holds the six research angles, every source with its verdict, the verification log, and the local measurement (appendix §4, summarized here in §3.3). Bracketed keys in this spec, such as `[watson2017]`, name rows of that appendix. Every external source cited here was opened at its primary record (DOI registry, arXiv abstract page, proceedings page or the paper itself) and its title and first author checked; anything that could not be verified was dropped.

**Relationship to other specs:**
- `spec_learner_field_v1.md`: this spec adds an arm family to its harness (§7.2), follows its constraints F1–F8 and its switching rule (§7.4), and reuses its interaction signals (§3.1).
- `spec_action_router_v1.md` and `plan_router_r2_v1.md`: the router keeps choosing blocks; this spec chooses the item and its feature point inside a block and logs exact propensities that compose with the router's (§10.1). It answers router §15.6 (exam and problem-set profiles seed difficulty and rigor).
- `spec_measurement_efficiency_v1.md`: certification keeps its ledger, its caps and its delayed cold probe (§5.7); this spec adds a level to each ledger cell (§9).
- `spec_probe_eig_redesign.md`: probes keep their hypothesis EIG and value-of-information stopping; this spec changes what goes into the conditionals and how probe items are authored (§6.3).
- `spec_storage_sync_v1.md` (branch `docs/storage-sync-spec`, not yet on main), §6.12 and requirement R13: the opt-in contribution export that n>1 priors would come from (§13).
- `docs/algorithm-change-playbook.md`: every serving change here is a successor with a kill switch (§11).

---

## 0. Summary

**The question.** When a learner answers easily, is that because they are skilled or because the item is trivial? A single response cannot tell. LearnLoop today mostly does not try. Its item difficulty is a number the authoring model writes after being told the band it should hit (§3, G1). The certification ledger gives the same credit to a heavily scaffolded item as to an exam-level one at the same capability (G4).

**The answer this spec builds.**
1. **Difficulty is a property of a feature point, learned from this learner's own history.** An item's difficulty is `b = (effect of its task features) + (an item offset with wide uncertainty)`. Feature effects are shared across items, so they can be learned from one learner (explanatory IRT, `[fischer1973]`, `[deboeck2008]`). The offset of a one-off item cannot be learned, so it is integrated out, never estimated (§5).
2. **The learner state is a posterior over ability per (facet, capability) cell, on the same scale as the feature ladder.** It changes as the learner learns. Updates are deterministic and replayable, with zero model calls (§5.6).
3. **Practice is chosen to land in the band.** The rule serves the existing item with the highest posterior probability that this learner's success chance lies in 70–80%. When no item can, it commissions one at the feature point most likely to. Near-ties and a small exploration share are randomized with exact, logged propensities (§6.1). The LLM writes a surface *at* the commissioned feature point and is no longer asked to hit a difficulty (§7).
4. **Probes are chosen to discriminate.** They keep the existing hypothesis EIG and stopping rules. The item offset's uncertainty is folded into each hypothesis's predictions, and probe authoring targets feature points where hypotheses disagree, not a 45–55% band (§6.3).
5. **Every forecast is logged before the attempt and scored after it.** This covers the model in use, the incumbent, and outside forecasters (solver panel, an LLM given the item, an LLM and the Decider given the learner's history). Trust in each is learned from proper scores. Item-side signals enter the item-offset prior with learned weights. Forecasts that already read the learner's history compete as experts and are never folded in a second time (§8).
6. **Certification says "demonstrated up to level k".** Credit counts only from items at or above the level, judged by the item's audited features. The features of practice-available exam and problem-set units define the top level, "full mastery". Held-out exams are never served and never steer practice (§9).
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

- **Where item difficulty comes from.** Practice generation inverts the mastery channel's 2PL link at the learner's estimated ability. It turns the target success interval into a difficulty band (`content/authoring/practice_generation.py:2133-2149` `_difficulty_for_success`, `:2152-2182` `success_band_difficulty`, called at `:403-410`), with bands from config (`config/schema.py:398-399`: practice `(0.70, 0.85)`, probe `(0.45, 0.55)`). The authoring prompt then tells the model to "Calibrate each item's difficulty to its target's recommended_difficulty_band (~70-85% expected success) … and set difficulty and difficulty_source='llm_estimate' accordingly" (`:1919`; also `:1062`, `:1922`). For probes it says "Set difficulty within the recommended_difficulty_band: it lies on the learner's boundary (~50% expected success)" (`:1984`).
- **How difficulty reaches the learner model.** `item_irt_params` maps the stored `difficulty ∈ [0,1]` to `b = 2.5·(2d − 1)` (`learner/mastery.py:356-378`). `resolve_item_irt_params` is "the single seam" through which the mastery EKF, surprise and prediction read it (`:381-397`). Primed attempts subtract a fixed `priming_b_offset = 2.0` (`config/schema.py:156-162`; `attempts/attempts.py:3402-3410`).
- **Empirical difficulty is dark.** An empirical-Bayes update of `b` exists (`mastery.py:400-447`) but ships disabled (`config/schema.py:163`). The config comment gives the reason: "theta and b are confounded at N=1" (`:150-155`). A monitor flags items with one-sided residuals after 5 attempts (`learner/calibration.py:1-7`, `:39-99`).
- **The solver panel.** For practice-family variants it sets a per-variant offset from the panel's solve rate *relative to the parent item's difficulty*, or 0.5 when the parent has none (`ops/pf_generation.py:183-198`). LLM self-labels are never requested there (`:37-42`).
- **Depth rungs.** A rung is one capability plus one task-feature point (`curriculum/depth_rungs.py:1-16`, schema `p1_launch@1`, `substrate/activity_patterns.py:71-89`). It is chosen by a mastery-band ladder with fixed cut points (`depth_rungs.py:228-307`) and an "optimism" step of one rung when evidence is thin (`:310-319`). A diagnosed hypothesis can override it (`:323-333`). The prompt is told that "Difficulty varies WITHIN the waypoint" (`practice_generation.py:1922`).
- **Prediction in serving.** On a canonical-state vault, an LO with blueprints predicts item success by a noisy-AND over component recall with slip and guess (`scheduling/selection_rewards.py:419-457` → `learner/blueprint_projection.py:370-392`). Item difficulty does not enter. Selection rewards an item by its fit to a target band per intent: practice `(0.55, 0.75)`, probe `(0.40, 0.60)`, repair `(0.75, 0.90)`, transfer `(0.60, 0.80)` (`selection_rewards.py:516-526`).
- **Certification.** Credit for one observation is its pseudo-mass if the observation is direct or embedded and unassisted, else zero (`learner/capability_mapping.py:246-266`). Credit accrues per `(facet, capability)` (`substrate/canonical_projection.py:920-950`). A cell is demonstrated at credit ≥ 1.0 (`goals/certification.py:1-7`; `goals/goal_certification.py:85-101`). A delayed cold probe per certified LO measures `false_certification_rate` (`goals/certification_cold_probe.py:1-40`; success at correctness ≥ 0.8, `:197`).
- **Learner difficulty reports.** An "easier/harder" request writes a self-graded `self_report` attempt at 0.3 evidence mass. It moves mastery, facet recall, the capability ledger and FSRS (`content/authoring/rung_variants.py:1-22`). A "too easy / too hard" retirement writes an LO claim at a fixed level (`content/authoring/item_authoring.py:317-365`).
- **Other signals.** `practice_attempts` records `hints_used`, `primed`, `latency_seconds` and a 1–5 pre-answer `answer_confidence` (`attempts.py:175`; mapping at `field/types.py:75`). Latency is used only to size the daily plan (`daily_plan/estimates.py:1-18`).
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
| Observations: correctness, partial credit, cold/primed, hints, time, optional rating; weights learned, never hand-picked | **Keep** | Ordinal outcome. Hints change the outcome category. Cold vs warm (recent exposure to the LO in any channel) is a learned warmth shift. A primed attempt (the answer was in view) is assisted: excluded from the update and never an unassisted success. Rating and timing are sub-arms with constrained, learned links that must earn activation (R9). |
| Probes target expected information gain between hypotheses, not the band | **Keep** | Item-offset uncertainty folded into the conditionals. Probe authoring stops using the 45–55% difficulty band (§6.3). |
| Certification "demonstrated up to rung k" from items at or above the rung; exam/pset defines the top rung; reconcile with the capability ledger | **Keep** | Rung credit uses the more conservative of stamped and audited features. LO certification keeps its structure, with an entry-level floor. Full mastery is a separate label (§9). |
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
  - `hints_used`, and whether help came before any work (field §3.1);
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

| Category `Y` | Condition |
|---|---|
| 2 **unassisted success** | `y ≥ 0.8`, `hints_used = 0`, not primed |
| 1 **partial, or success with help** | `0.40 ≤ y < 0.8` unassisted; or `y ≥ 0.8` with hints given after work began; or `y ≥ 0.8` primed |
| 0 **fail** | `y < 0.40`; or `y < 0.8` with any hint or primed; or success after help requested before any work (field §3.1's early-help cap); or an empty "I'm stuck" |

- The **forecast event** used everywhere (band, receipts, scoring) is `Y = 2` on a first presentation. A future hint or reveal is never a forecast covariate.
- **Primed attempts are assisted.** `primed` is set for a source-review retry and also, by `auto_primed_draft`, for any submission whose answer the reveal ledger shows was handed over, first attempts included (`attempts/attempts.py:1960-1990`). A primed attempt is therefore excluded from the update (§5.6). For scoring it takes the assisted categories above (1 at `y ≥ 0.8`, else 0), so it is never an unassisted success.
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
   - from the current grading epoch.

   Excluded: `self_report` rows, so that the rung-variant evidence package is not read twice (D8); primed attempts, whose answer was in view (§5.3); `teach_back` in v1 (§16); and any held-out exam unit (A8).
2. **Claims.** An allowlisted claim (§5.5) whose `created_at` falls before this row re-anchors `θ_f`'s mean first, if the facet has no eligible observation yet (mean-only, variance ≥ 2.0).
3. **Propagate.** For each touched cell, add `σ²_drift · Δdays` (since that cell's last update) to `Var(e_{f,k})`. There is no mean decay; forgetting stays with FSRS (field §4.3, "Time").
4. **One joint factor per attempt.**
   - **Dependence.** The attempt's likelihood (the outcome category, and, where the active arm has them, the rating and the timing) depends on the state only through a low-dimensional vector `v_t`. It holds the linear projection `ũ_tᵀs` that forms `η_t` (warmth included, §5.4), plus the sub-arm link coordinates (`c_1, d̃, ρ̃`; `ν, ω̃`). That is at most six coordinates, and exactly one in the base arm.
   - **The shared residual.** The item residual `ε_i` enters every factor through the same `η_t`, so it is integrated **once**, inside the joint factor: `Z_t = E_{v_t, ε_i}[ L_Y(η_t) · L_r(η_t) · L_ℓ(η_t) ]`, with `η_t = ũ_tᵀs − a·ε_i`.
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

**Serve candidates `S_c`.**
- Every never-attempted, servable pool item in the cell, with its audited features `x̂_i` and signals `z_i`.
- Excluded: exam-reserved items (`exam_pool.reserved_item_ids`), retired items, and anything derived from a held-out unit.
- Items authored above the depth envelope (`RungTarget.task_feature_bounds` "max") are excluded too. `coordination` items are served only behind a reviewed envelope (`depth_rungs.py:126-129`, `:176-182`).

**Serve rule (`ad_select_v1`):**
0. **Empty pool.** If `S_c` is empty, AD serves nothing for the cell. The lane keeps the predecessor's order for its other items, the row records `empty_pool`, and a commission draw runs (below).
1. Compute `P_band(i)` and `p̄(i)` for every `i ∈ S_c`.
2. **Calibrate instead** if `max_i P_band(i) < 0.35` (the posterior is too wide to target the band; typical in a new cell). Choose by §6.2.
3. Near-tie set `T = {i : P_band(i) ≥ max P_band − 0.05}`. Overlap set `O = {i ∈ S_c : p̄(i) ∈ [0.55, 0.90]}`.
4. Draw with exact propensity `π(i) = (1 − q)·1[i∈T]/|T| + q·1[i∈O]/|O|`, with overlap share `q = 0.10`.
   - If `O` is empty, `q = 0` for this draw.
   - The seed is `seed_for(decision key)`.
   - The candidate set, both scores, `π`, the seed and the chosen item are written to `ad_selections` **before** the item is served (A7).
**Commission candidates `X_c` and rule.**
- `X_c`: the cell's ladder rungs (§9.1) and their one-step neighbours on a single ordinal dimension, clipped to the depth envelope.
- A commission draw runs when the pool has no item with `P_band ≥ 0.35`, or no item at all. It uses the same rule as the serve draw: steps 1–4 over feature points with `z = 0`, with its own propensity, seed and `ad_selections` row (`kind = commission`).
- The chosen point is commissioned for generation (§7) and runs in the background. AD keeps at most one open commission per active cell.
- A commission changes only what can be served later. Its propensity is logged for completeness but never multiplied into a served item's weight.

**Why not Thompson sampling.**
- Sampling the joint state and picking the point nearest 0.75 explores in proportion to uncertainty (worker d).
- But its propensities need Monte Carlo over a ~20-dimensional Gaussian, so they are not exact.
- The rule above is exact, and its overlap share does the confound-breaking job.
- Thompson sampling is kept as a harness comparison (§10.4).


### 6.2 Calibration within acceptable difficulty

When the band cannot be targeted:
- choose `i ∈ O` maximizing `I_c(i)` (§5.7), with near-ties (within 5% of the maximum information, relative) broken uniformly;
- if `O` is empty, choose the item whose `p̄` is nearest the interval `[0.55, 0.90]`, ties by item id;
- apply the same `q` overlap mixture and log it identically, with `mode = calibrate`.

**Why bounded.** Unbounded information would push toward 50% predicted success `[eggen2006]`. Bounding to `[0.55, 0.90]` keeps a cold learner from a run of failures (frictionless defaults) while still choosing the most informative acceptable item.

This replaces the "optimism step" heuristic (`depth_rungs.py:310-319`) when AD selection is on. The learner sees ordinary practice.

**Exam-target calibration.** When an exam/pset target exists (§9.5) and the goal's due date is within its horizon, `I_c` may be replaced by expected predictive information about success at the target points `[bickfordsmith2023]`. This is the same computation with the target tuples as prediction inputs. Off by default (D12).

### 6.3 Probes: discriminate

Probes keep their episode model, hypothesis sets, actual and predictive EIG (`diagnosis/probe_families.py:467-534`, `:536-620`), and value-of-information stopping (mvp-0.21). AD5 changes three things:
1. **Item offsets in the conditionals.** Each hypothesis's predicted outcome distribution for a candidate integrates the item residual `ε` and the uncertainty of `β` at the item's features. EIG is then computed on the outcome distributions the learner will actually face, not on an idealized item. Integrating inside each hypothesis also stops the acquisition rewarding information about an expendable item rather than the learner (worker b). This usually lowers an uncertain item's EIG, but not always: near saturation, noise can separate predictions. The test is agreement with the marginalized EIG, not monotonicity (G-AD5-2).
2. **Capability-profile hypotheses get AD conditionals.**
   - Hypotheses that map to capability gaps (`_RUNG_BY_HYPOTHESIS`, `depth_rungs.py:323-333`; for example `procedure_without_selection`) are constraints on cell abilities, such as "`θ_{f,method_selection}` below the method-selection ladder entry while `θ_{f,procedure_execution}` is at or above its own".
   - AD supplies `P(Y | H, x)` by conditioning the cell posteriors on each constraint. Misconception hypotheses keep their discrimination profiles and contrast pairs (`PracticeItem.discrimination_profiles`, `contrast_of`).
3. **Probe authoring targets discrimination, not difficulty.**
   - The probe prompt's band instruction (`practice_generation.py:1984`) and the probe success band (`schema.py:399`) are retired under the AD5 successor.
   - The probe generator receives the feature point where the live hypotheses' predicted success differs most (for capability hypotheses), or the discrimination-profile target (for misconceptions).
   - An item whose conditionals are identical across hypotheses already scores zero EIG whatever its difficulty (`probe_families.py:476-478`). AD5 keeps that rule and stops paying to author such items.

### 6.4 What is not AD's job

- **Block choice** stays with the router (staged rule, Decider, LLM, mixture; `router/mixture.py`).
- **Review timing of already-attempted items** stays with FSRS and the scheduler. AD does not reorder due reviews.
- **Repair after a diagnosis** stays with the diagnosis track. Once repair practice is chosen for a cell, AD picks its feature point by §6.1 (repair is practice).
- **Selection-reward bands for due items** (`selection_rewards.py:516-526`) are unchanged.

---

## 7. Generation at a feature point

### 7.1 The contract to the generator (AD3 successor; switch `generation_contract`)

- The commissioned `RungTarget` carries `capability = k`, `task_features = x`, and `task_feature_bounds` with `max = x` on every dimension. The existing deterministic gate already rejects overshoot (`depth_rungs.py:204-208` point bounds; `validate_item_against_rung`, `:537-545`).
- The prompt **drops** every band instruction: `practice_generation.py:1062`, `:1919`, and the band clause of `:1922`. The waypoint clause ("NEVER change the waypoint") stays.
- It also drops the `recommended_difficulty_band` field from the target payload, and the band check `_check_difficulty_band` (`:1501-1537`).
- In their place: "Write the item so that it has exactly these features. Do not make it easier or harder than these features imply; difficulty is measured from the learner's answers. Separately, give your estimate `difficulty` in [0,1] of how hard this item is for a typical learner studying this topic. It is recorded as one weighted signal whose weight is learned from this learner's answers; it is not the item's difficulty."
- `difficulty_source = "llm_estimate"` stays on the item for the incumbent. Under AD it is only the signal `z_llm`.

### 7.2 Feature audit (AD1; switch `feature_audit`)

- After any item is generated or imported, one Tier-1-style Decider judgment per audited dimension (`complexity`, `transfer`, `scaffolding`, `span`, `response`) reads the item stem and reference answer only. It is never shown learner data or held-out text.
  - It answers a typed `ChoiceQuestion` over that dimension's vocabulary.
  - Argmax decides; a tie is no answer; the distribution is logged in `judgment_ledger` (task `ad_feature_audit`, version `ad-feature-audit-v1`), exactly as `decider_judgments.py:1-25` does.
  - On Decider failure, the existing LLM fallback runs and is recorded as such.
- **Uses of the audited tuple `x̂_i`:**
  - AD's likelihood and predictions use `x̂_i` where the audit answered, else the stamped `x_i`.
  - **Level credit (§9.2) uses the easier of `x_i` and `x̂_i` on every dimension.** An overclaimed feature can never raise a level.
  - The audit agreement rate per dimension is reported. Persistent disagreement is a generator finding, not a learner one.

### 7.3 Item-side signals and the offset prior

`z_i` is assembled from persisted values only, and **frozen per decision**:
- a selection or receipt uses exactly the signals whose `received_at` precedes it;
- an attempt's update uses the signals frozen at that attempt's serve time;
- the vector, each signal's availability, and the `z_v1` recalibration version are recorded on the `ad_selections` row and in `ad_attempt_trace`.

A signal that arrives later is used only by later decisions and updates. It never changes an earlier state, selection or score, so replay reproduces history exactly.

The signals:

| Signal | Value | Present when |
|---|---|---|
| `z_llm` | `2.5·(2d − 1)` from the item's own `difficulty` (the existing map, `mastery.py:377`) | `difficulty_source = "llm_estimate"` |
| `z_panel` | `logit(s_parent) − logit(s_item)`: the panel's relative offset, smoothed as in `pf_generation.py:190-197` | `difficulty_source = "solver_panel"` with the panel rates recorded |
| `z_v1` | `−logit(p_v1)`, where `p_v1` is an item-only LLM forecast of "probability a typical learner studying this topic answers correctly" (field V1 variant, no learner data), recalibrated on past items only. The sign makes it a difficulty, like the other signals | the AD1 receipt exists (§8.2) |
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

---

## 8. Forecasts: logging, scoring, trust

### 8.1 Receipts (AD1; switch `forecast_receipts`)

`item_forecasts` (RECEIPT, append-only), one row per (presentation, forecaster):
- **presentation reference:** `plan_presentation_id`, `probe_presentation_id`, `scheduler_candidate_id`, or an exam session's pooled item (written when `start_exam` freezes its predictions, `goals/exam_session.py:1-12`);
- `practice_item_id`;
- `forecaster` and `forecaster_version` (hash of code, priors and config);
- `event = "unassisted_success"`;
- `p` and optional `p_categories`;
- `inputs_hash` and `inputs_as_of` (the snapshot the forecaster read);
- `issued_at`, `received_at`, `status` (`ok | failed | refused_spend`);
- `algorithm_version`.

**Validity rule.** A forecast is valid iff `inputs_as_of ≤ served_at`, whenever it arrives. So outside forecasters never sit on the critical path, and a late answer is still a true forecast. In-process forecasters (AD, the incumbent, `lo_general`) write their rows in the serve transaction, beside `plan_presentations` (plan R2 §5.2). Raw responses from paid forecasters go to `item_forecast_payloads` (WORKFLOW, pruned like `router_decision_payloads`); the receipt keeps the hash.

### 8.2 Forecasters

| Forecaster | Reads | When on | Role |
|---|---|---|---|
| `ad_threshold` (and sub-arms) | the AD state (§5) | AD2 onward, computed in-process at serve time even before promotion | Served after AD3 promotion; otherwise scored only |
| `mastery_ekf` (incumbent) | `resolve_item_irt_params` and the EKF | AD1 onward | Incumbent |
| `lo_general+composite` | field §4.3 | AD1 onward | Challenger |
| `solver_panel` | `difficulty_source = solver_panel` items: panel rate mapped through the item's `b` at the learner's incumbent ability | when present | Item-side signal and scored forecaster |
| `llm_v1:item` | item stem, LO and facet names (field V1) | AD1, switch `outside_forecasters` | Item-side signal `z_v1` after recalibration; scored |
| `llm_v3:llm`, `llm_v3:decider` | field V3: item plus a `LearnerStateCardV1`-style card restricted to the LO and its prerequisites, plus similar past items with outcomes; Decider as a `noul` question | AD1, switch `outside_forecasters` (D4) | **Competing experts** (§8.4). Never an offset prior |

### 8.3 Scoring

- `item_forecast_scores` (DERIVED, one replayer) joins each valid receipt to its bound attempt through the exact chain `plan_presentations` → `practice_attempts.plan_presentation_id` (plan R2 §5.2). Unbound attempts fall back to the scheduler candidate, then the probe presentation; R1's session rule is never used.
- The outcome is the §5.3 event. Pending outcomes are right-censored, never failures.
- **Metrics per forecaster:**
  - log loss and Brier on the binary event;
  - ranked probability score on categories where given;
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

### 9.1 The cell ladder (`ad_ladder_v1`, deterministic)

- **Ordered dimensions:** `scaffolding` (worked < partial < cue < none), `transfer`, `complexity`, `span`, response class (recognize < constructed < performance), `tools` (open < closed).
- **Entry point `e_k`:** the default-trajectory waypoint for capability `k` (`depth_rungs.py:101-122`). `coordination` has no entry without a reviewed envelope.
- **Target point `t_c`**, in order of precedence:
  1. the exam/pset target for the cell (§9.5);
  2. else the active milestone contract's feature point (`RungTarget.source = "milestone_edge"`);
  3. else `e_k` stepped one level up in `complexity` and in `transfer`, bounded by the default trajectory.

  Any dimension where `t_c` is easier than `e_k` is raised to `e_k`.
- **Ladder:** walk from `e_k` to `t_c`, raising one dimension one level per rung in the fixed order above, cycling until every dimension reaches `t_c`. Rung 1 is `e_k`; rung `K_c` is `t_c`. The learner sees "level k of K" (§12).

### 9.2 An item's level

- An item's **conservative tuple** is the easier of its stamped and audited features, per dimension (§7.2).
- Its **level** is the largest `r` such that the conservative tuple is at least as hard as rung `r` on every ordered dimension. An item below rung 1 has level 0.
- Items with no `task_features` (legacy) get level 1 if their capability is known (stamped, or `default_capability_for(practice_mode)`), labelled "level not rated". They never get more than level 1.

### 9.3 The level ledger and "demonstrated up to level k" (AD4 successor; switch `rung_certification`)

- `facet_capability_rung_evidence` (DERIVED; owned by the replayer that owns `facet_capability_evidence`) accumulates certification credit per `(facet, capability, rung)`.
  - It uses exactly the existing credit rules: direct or embedded, unassisted, group budgets and caps (`capability_mapping.py:246-288`; `canonical_projection.py:920-1030`).
  - An observation's credit goes to every rung from 1 to its item's level. This is within-cell dominance, the feature-ladder analogue of capability dominance (measurement spec B1), with no discount because the item dominates on every dimension. The basis is recorded.
  - Level-0 items earn no rung credit.
- **"Demonstrated up to level k"** is the largest `k` whose rung credit is ≥ `DEMONSTRATED_CREDIT` (1.0, `certification.py:3`).
- Embedded credit from capability dominance (B1) reaches rung 1 only.
- **Never from the posterior.** No level is ever derived from AD's state (A2). The posterior predicts; the ledger demonstrates.

### 9.4 Reconciliation with capability-matched certification

`lo_certification` (`goal_certification.py:275+`) keeps its structure: some recipe with every hard component demonstrated, plus integration evidence. Under AD4:
- **A component is demonstrated** when its `(facet, capability)` has rung credit at its **required level** `ℓ_req`.
  - Default `ℓ_req = 1`: the entry point (D7).
  - The only change for an LO with no declared level is that level-0 items (heavily scaffolded, below the capability's entry point) stop counting. That is the "trivial item" fix.
- **A declared requirement** may set `ℓ_req` higher: an optional `level` on a blueprint `RecipeComponent` (`vault/models.py:288-293`; absent means 1), or the active milestone contract. Owner decision D7.
- **The delayed cold probe** for a certificate is served at level ≥ the certified level, so `false_certification_rate` is measured per level (`certification_cold_probe.py`).
- **Exam pool stratification** moves from LLM-label strata (`exam_pool.py:42-55`) to levels.
- **Kill switch** `rung_certification = false`: `facet_capability_evidence`, certification and the cold probe are byte-identical to the predecessor (G-AD4-4).
- **Upgrade.** Because a successor can reduce existing certificates on replay (level-0 items stop counting), the upgrade runs the playbook's shadow rebuild on copies and reports every certificate that would change before the version applies (playbook step 7).

### 9.5 Exam and problem-set targets: full mastery (AD4)

**Where target points come from.**
- The exam profile gains `target_feature_points`: per exam or problem-set unit, a `p1_launch@1` feature tuple.
- **Only units whose use mode is `blueprint_only` or `available_for_practice`** (`content/synthesis/source_unit_selection.py:333`) feed it, as router §15.6 requires for anything that steers generation or selection. Their text may be read, so the feature-audit judge classifies each one at ingest.
- Tuples are collapsed one vote per syllabus family (`exam_family_key`, `content/synthesis/exam_profile.py:35-54`).

**Mapping to cells.** Points map to cells by the unit's facet mapping where the inventory has one; otherwise to every facet of the goal scope at the unit's capability.

**The target.** `t_c` is the per-dimension 0.8-quantile of the cell's points (D12).

**Held-out units are evaluation only** (A8, D14).
- `held_out_evaluation` units are never served and never classified by an AD judge, and they never shape `t_c`, the ladder, selection or generation.
- Where the existing ingest inventory already records feature signals for them (as it records `held_out_task_families`, `exam_profile.py:64`), one evaluation report compares them with the ladder: "share of held-out exam tuples at or below the target level". A low share is an owner-visible finding ("practice aims below the exam") with no automatic action.
- The leakage gate (`content/authoring/practice_leakage.py`) is unchanged.

**Exam-session outcomes.**
- A goal's practice exam (`goals/exam_session.py:1-12`) serves reserved, never-practised pool items and freezes predictions before any answer is graded.
- Under AD, `start_exam` also writes an `item_forecasts` receipt per pooled item (§8.1), so exam-level calibration is scored on the same footing as the incumbent's frozen predictions.
- The answers then apply through the standard attempt pipeline, as today, and AD reads them like any first-surface attempt (§5.6).

**Two labels, never blended:**
- **Full mastery (demonstrated):** rung credit ≥ 1.0 at `K_c`, the target level.
- **Ready for exam level (predicted):** `p̄(t_c) ≥ 0.8`, labelled as a prediction (KM §9.6; `exam_readiness.py:5-12`).
  - It needs a predictor that can predict at a feature point, which the incumbent cannot. So it is shown only once AD is promoted for selection (AD3).
  - Before that, the line reads "exam level: not yet predicted". Demonstrated levels (AD4) do not depend on it.

**Without practice-available exams or problem sets,** the top level is the milestone or default target, and "full mastery" is shown as "top level for this goal".

### 9.6 Ground truth

- The delayed cold probe stays the external check. `false_certification_rate` is reported per level and per capability.
- AD3 and AD4 add one metric: the **trivial-success rate**, the share of successes on items whose `p̄ > 0.95` at serve time. It falls when AD works. A high rate before AD is G4 measured.

---

## 10. Integration

### 10.1 Router mixture and exact propensities

- The router picks a block with an exact propensity `π_router` (`router/mixture.py`). Within a practice or new-material block, AD picks the item with exact propensity `π_AD` (§6.1).
- The served item's joint propensity is `π_router · π_AD`. Both are logged before selection, so router R3's doubly-robust replay and an AD replay both have valid importance weights. They evaluate serving policies *conditional on the pool that existed*. Alternative commissioning policies are not evaluable from these weights (§6.1).
- AD registers its draw as a fifth admissible design, **`feature_overlap`**, in `scheduling/randomization_layer.py:57`. Like `model_mixture`, it declares its own floor (`q/|O|` on the overlap set), and the dormant 0.05 floor never clips it. Outcomes join at the next spaced cold review, as for the other designs (`randomization_layer.py:19-25`).
- **The router's card** (`LearnerStateCardV1`) gains, per LO, after AD3: demonstrated level / K, `P_band` of the next point, and `p̄` at the target. The card's version moves accordingly (plan R2 §3.6).

### 10.2 Daily-plan lanes

- Under AD3, the **new** and **push** lanes (`daily_plan/lanes.py:1-27`) order a cell's never-attempted items by AD's draw instead of the scheduler's order, one draw per served item.
- The **repair** lane uses AD for its practice items once diagnosis has chosen the cell.
- **maintain** (due reviews) is untouched.
- **Kill switch** `selection = false`: the lane order is the predecessor's exactly.

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
| AD1 measure and log | **No.** It adds receipts, a nullable rating column and audit judgments, but changes no persisted meaning and nothing served | `forecast_receipts`, `outside_forecasters`, `rating_tap`, `feature_audit` (Decider switch `ad_feature_audit`) |
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
| `item_forecasts` | RECEIPT (append-only) | §8.1 | never cleared |
| `item_forecast_payloads` | WORKFLOW | raw outside-forecaster responses; pruned after `router.payload_retention_days` | — |
| `judgment_ledger` rows, task `ad_feature_audit` | RAW_LEDGER (existing) | §7.2 | — |
| `ad_selections` | RAW_LEDGER (append-only) | decision id, `kind` (`serve` / `commission`), cell, mode (`band` / `calibrate`), candidates with `P_band`, `p̄`, `I_c`, `π`; seed; the chosen item (serve) or feature point (commission); `empty_pool`; state hash; versions | — |
| `ad_commission_results` | RECEIPT (append-only) | per landed commission: the `ad_selections` id, the generated item, its audited features, `p̄(i)`, in band or `realized_out_of_band` (§7.4) | never cleared |
| `ad_state` | DERIVED | current posterior: cell moments and shared parameters, sparse covariance | AD replayer |
| `ad_attempt_trace` | DERIVED | per eligible attempt: prior and posterior `η` moments, category probabilities, information gained | AD replayer |
| `item_forecast_scores` | DERIVED | §8.3 | forecast-score replayer |
| `facet_capability_rung_evidence` | DERIVED | §9.3 | canonical-projection replayer (same owner as `facet_capability_evidence`) |

- Each new table is classified in `db/table_roles.py`. Each DERIVED table has exactly one registered replayer in `substrate/rebuild_orchestrator.py`, and both facts are tested (CLAUDE.md).
- Migrations take the next free numbers at implementation time. The head is 202 at this base (`migrations/202_router_staged_frame.sql`). The migration-head fixture is renamed and its five hard-coded paths and references regenerated, per CLAUDE.md.

### 11.3 Replay invariants

- **Zero model calls in replay.** The AD state is a pure function of the attempt ledger, `judgment_ledger` audit rows, vault content and `ad_priors_v1`. Outside forecasts are read from receipts and never re-asked.
- **Deterministic rebuilds.** Two rebuilds are byte-identical.
- **AD never touches evidence.** Mastery, facet recall, FSRS, `grading_evidence` and `facet_capability_evidence` are byte-identical with AD on vs off. This is enforced by an import-linter contract forbidding the AD package from importing evidence writers. AD4's rung ledger is the one exception: it is written by the canonical projection, not by AD.

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
  - "Shown at level 2 of 4" (Demonstrated);
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
  - outcome categories (§5.3) with hint and primed flags;
  - optional ratings, and latency with the learner's own prior answer-time estimate beside it (§5.4), so the normalization can be rebuilt.

  These keep pooled estimation of feature effects possible without a retrofit.
- **Trigger** (§16): the S9 export is built and at least 20 consenting learners have at least 200 first-surface attempts each.

---

## 14. Phases, gates and fail-first tests

Each test below is written first, and fails on today's code for the stated reason. All tests use fakes. The paid forecasters' interfaces are verified by the existing route tests and one dry-run.

### AD1: measure and log (no successor)

**Builds:**
- migration: `item_forecasts`, `item_forecast_payloads`, `practice_attempts.difficulty_rating`;
- table roles;
- in-process forecasters `mastery_ekf` and `lo_general+composite` written at serve;
- outside forecasters behind `outside_forecasters`, async, spend-capped;
- the feature audit (§7.2);
- the rating tap (§12);
- `learnloop ad data-check`: the §3.3 tables on a backup copy, plus first-surface attempts per cell and coverage of latency and ratings.

**Gate:** G-AD1-1 to G-AD1-7.

| Id | Test (fails today because…) |
|---|---|
| G-AD1-1 | `test_forecast_receipt_written_in_serve_transaction`: serving a plan item writes one `item_forecasts` row per in-process forecaster in the same transaction as `plan_presentations`, with `inputs_as_of ≤ served_at` (no such table) |
| G-AD1-2 | `test_late_outside_forecast_is_valid_if_inputs_predate_serve` and `test_forecast_with_post_serve_inputs_is_invalid` (no validity rule) |
| G-AD1-3 | `test_rating_tap_optional_never_blocks_submit`: submit without a rating succeeds; the rating is stored only when tapped and only before feedback (no column) |
| G-AD1-4 | `test_feature_audit_ledgered_with_fallback`: Decider argmax per dimension, tie is no answer, LLM fallback recorded (no audit task) |
| G-AD1-5 | `test_ad1_switches_restore_predecessor`: all four switches false ⇒ no new rows, prompts byte-identical, no extra calls |
| G-AD1-6 | `test_held_out_sentinel_never_reaches_ad_inputs`: a sentinel in a held-out unit appears in no AD prompt, receipt, payload or audit input |
| G-AD1-7 | `test_replay_reads_receipts_zero_model_calls`: rebuild with model constructors forbidden |

### AD2: the arm (offline; pre-registered)

**Builds:** the AD replayer (`ad_state`, `ad_attempt_trace`); in-process `ad_threshold` receipts at serve time (scored, not served); arms in `learnloop eval` (§10.4); `learnloop ad report` (prequential metrics, band-region reliability, identifiability diagnostics, sensitivity); simulation recovery on `sim/` synthetic learners with known `θ_t`, `β`, `γ`.

**Gate:** G-AD2-1 to G-AD2-13, then the owner reads the report once on a backup copy (owner-run, field §7.3 style).

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
| G-AD3-8 | `test_serve_propensity_is_over_existing_items`; `test_empty_overlap_sets_q_zero`; `test_empty_pool_serves_nothing_and_commissions` |

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
| G-AD4-7 | `test_cold_probe_served_at_certified_level` |
| G-AD4-8 | Shadow rebuild on owner copies reports every certificate that changes (playbook step 7; owner-run) |

### AD5: probes that discriminate (successor; switch `probe_targeting`)

| Id | Test |
|---|---|
| G-AD5-1 | `test_probe_prompt_has_no_difficulty_band_under_successor` (**fail-first**: `practice_generation.py:1984`) |
| G-AD5-2 | `test_eig_matches_marginalized_conditionals`: candidate EIG equals a brute-force computation over the residual and `β` uncertainty within 1e-6; identical conditionals give zero |
| G-AD5-3 | `test_capability_hypotheses_get_ad_conditionals` |
| G-AD5-4 | `test_switch_off_probe_selection_identical` |

**Order.** AD1 now. AD2 in parallel with AD1, since it reads existing ledgers. AD4 can follow AD1 without waiting for AD3. AD3 waits for promotion. AD5 follows AD3.

---

## 15. Owner decisions, with recommended defaults

| # | Decision | Recommended default |
|---|---|---|
| D1 | Practice band and what "success" means | `[0.70, 0.80]`; success = first unassisted response at correctness ≥ 0.8 (the cold probe's definition). The research supports a band in this region without fixing a number (R5) |
| D2 | Outcome categories (§5.3): help-adjusted success counts as "partial"; early help counts as fail | Yes, aligned with field's hint arm (graded outcome by help depth) |
| D3 | Promotion rule for AD3 selection | **The harness's own rule (field §7.4: superiority on log loss, overall and on the first attempt at a never-seen LO; report 2's miss rate no worse), plus this spec's added cell-level and decision-level checks**, as the owner directed. Alternative: non-inferiority for *selection only*, since the incumbent cannot predict at feature points it has never authored. Revisit if "can't tell" persists after 300 first-surface attempts |
| D4 | Live outside forecasters per presentation | On: item-only LLM, LLM with history (Codex on the subscription) and Decider (OpenRouter, ~$0.50/day cap). Learning trust needs hundreds of outcomes (§8.3), so collection should start early. Off the critical path |
| D5 | Rating tap placement | Beside Submit, before feedback; optional; hideable per session |
| D6 | Overlap exploration share | `q = 0.10` over items with `[0.55, 0.90]` predicted success |
| D7 | Required level for certification | Level 1 (the capability's entry point) unless a milestone contract or an explicit component `level` sets more. Full mastery is a separate label, never a certification requirement by default |
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
| Pooled priors (§13) | The S9 export is built, and ≥ 20 consenting learners each have ≥ 200 first-surface attempts |
| Federated or differentially private estimation | Pooled priors are computed anywhere other than the contributor's own machines |

---

## 17. Open questions

1. **Q1. Current data.** The §3.3 numbers come from the two-month-old committed snapshot. The same measurement on backup copies of the current working vaults was not run in this stage. AD1's `learnloop ad data-check` reproduces it on the owner's copies (owner-run). Until then, the label-weight prior `α_llm` (§5.5) rests on one stale vault.
2. **Q2. Generator compliance.** How often does the generator realize the requested feature point, by the audit's reading? Unknown until AD1 audits run. A low rate would make the feature model weak and push the "several candidates" trigger.
3. **Q3. Unit-to-facet mapping for exam targets.** How many exam units carry a facet mapping in the inventory? Without one, targets apply at LO scope (§9.5). Measured by AD1's data-check.
4. **Q4. Rating timing.** Is a pre-feedback tap acceptable friction, or should the rating ride the existing post-feedback "too easy/too hard" controls (fewer taps, outcome-contaminated)? D5 recommends pre-feedback; the AD2 `+rating` arm will show whether it earns its place.
5. **Q5. Data volume for promotion.** With about 10³ attempts a year and the §8.3 illustration, superiority (D3) may take months to resolve. The owner may prefer to revisit D3 at AD2's first report.
6. **Q6. Motivation vs learning.** The research shows easier practice wins short-term engagement and harder practice wins learning `[papousek2016]`. Should the band move with the learner's session state (re-entry after a gap; frustration signals) before the band experiment reports? This spec keeps it fixed.

---

*Related: `spec_learner_field_v1.md` · `spec_action_router_v1.md` §15.5–15.6 · `plan_router_r2_v1.md` §5 · `spec_measurement_efficiency_v1.md` §3–5 · `spec_probe_eig_redesign.md` §2.3, §7 · `spec_storage_sync_v1.md` §6.12 (branch) · `docs/algorithm-change-playbook.md` · research appendix `docs/specs/research/adaptive_difficulty_sources_v1.md`*
