# Learned parameters: from hand constants to fitted values, utilities and liquid time constants (v1)

**Status:** first draft for owner review (2026-10-23). Nothing here is implemented. Code truth audited at `558e85ab1`.
- **Revised 2026-10-24 by owner decisions.** §0a records them, and they supersede the phase plan where they differ.
- **Revision 4 (2026-10-24):** "all these weights/margin values need to be learned and dynamic and not just made up, priors can be seeded otherwise. yes to defaults for all other open questions." LP-min therefore has no keep or switch margins and no activation thresholds (§0a, §4.6). Every open question is decided (§10).
- **Section references.** References to `spec_teacher_v1.md` below are to its revision 1. Revision 3 of that spec renumbered its sections, cut its sensor-rendering section (§11) and moved its router sensor mode (§15.1) to the router spec, deferred.

**Owner direction (2026-10-23):**
- Make the fixed constants and thresholds **learned variables**, or **LTC-style (liquid time-constant) quantities**, instead of static, arbitrary hyperparameters.
- Pay particular attention to the time constants.
- The owner pointed to CVPR 2026 work coupling LTC encoders with a modern Hopfield memory, and asked how directly it applies (§7).

**Sources:**
- `src/learnloop/params/parameter_registry.py`: the P0.5 registry and its audit (`spec_p0_measurement_correctness.md` §6).
- `src/learnloop/scheduling/fsrs_fitting.py`, `src/learnloop/cli/fit.py` and `migrations/016_fitted_parameters.sql`: the existing fitting path.
- `src/learnloop/learner/mastery.py`: the EKF.
- `src/learnloop/attempts/surprise.py`.
- `docs/specs/spec_learner_field_v1.md` §7.4: the switching rule.
- `docs/specs/spec_teacher_v1.md` §15.1: the router's H0/H1/sensor arms.
- `docs/brainstorming/Teacher Research Sweep 2026-10.md`: entries A8 (Bayes Factor Surprise), A11, B1, B12.
- `docs/algorithm-change-playbook.md`.

---

## 0. Thesis

LearnLoop already has the machinery to stop guessing:
- a registry that classifies every production number;
- a promotion ladder (`heuristic` → `simulation_validated` → `live_calibrated`);
- a fitting command (`learnloop fit`);
- a table for fitted sets (`fitted_parameters`).

It has used almost none of it. **All 343 decision parameters are `heuristic`.** Only FSRS has a fitter, and the owner's working vault has no fitted set (`fitted_parameters`: 0 rows).

Not every constant should be learned. The 343 sort into five treatments:

| Treatment | What it is | What happens |
|---|---|---|
| **L — learn** | A parameter of a predictive model, observed by every attempt: priors, likelihoods, evidence masses, noise variances, **time constants** | Latent state with a versioned a-priori prior, updated online on every attempt the way AD2/AD3 update their effects; structural ones are a posterior over an a-priori grid (§3) |
| **T — liquid time constant** | A rate or half-life that should depend on what happened: teaching, surprise, repair, the gap length | Re-parameterize as an input-dependent time constant with a few fitted weights (§4) |
| **D — delay → retrievability target** | A "wait N days" constant | Derive it from the forgetting model plus a target recall per purpose (§5) |
| **U — threshold → utility** | A cut-off that stands in for a decision rule | Replace with calibrated probability × explicit utility; the free numbers become a small, visible set of preferences (§6) |
| **K — keep** | Guardrails, budgets, operational limits | Fixed, with bind logging as today |

Shaping weights (the staged-policy and scheduler weights) are **R — retire**. They are replaced by sensor-mode probabilities, or tuned slowly by off-policy replay as the router's H1 arm (`spec_teacher_v1.md` §15.1).

The only set numbers left are **priors**, drawn from population data, published effects and LLM content proposals and overtaken by data within a few answers (§3.0), and **utilities**, which are the owner's preferences. Neither is arbitrary.

---

## 0a. Owner decisions, 2026-10-24: LP-min

The Opus review of 2026-10-24 recommended keeping only the four claim fixes and a trimmed LP0, and dropping LP1–LP3. **The owner keeps one learned family in addition, because lesson checks have a clean delayed-outcome signal.** That revises "drop LP1–3" for this case only.

**LP-min is:**
1. **The lesson-check weight.** It is specified in `spec_teacher_v1.md` §12.1 (revision 4).
   - The mass of a lesson check is `m = σ(η)`, with seeded prior centre 0.5 (basis `legacy`, 1 logit wide).
   - Its terms: a global effect; per-LO offsets whose scale is a grid posterior; a confidence interaction; an interaction with AD's prediction.
   - It is learned only from later cold checks on unseen items of the same LO, prequentially, with AD §5.6's assumed-density filtering, on the evidence side (AD A2 keeps it out of AD).
   - There is no resolution window: time between the check and the outcome enters through the mastery predictor.
   - It changes only how much mastery moves. A lesson check never certifies and never answers a Check once.
   - **Mixed with the teacher's forecast by a learned pool weight** (`spec_teacher_v1.md` §12.2):
     - the pool is `λ·p_forecast + (1 − λ)·p_parametric`;
     - λ is inferred on a grid by `W_t(λ) ∝ W_{t−1}(λ)·p_λ(y)`, AD's `ad_hyper` rule, from the seeded prior Beta(1, 4) (basis `legacy`: the parametric weight starts ahead);
     - there is no margin, no ≥100-pair rule and no switch. That is the path that retires the parametric weight, continuously.
2. **The tap/hedge → probability recalibration it needs.** The two-parameter logistic of §4.4.
   - It is learned online from every tapped (or hedge-read) graded attempt.
   - Its seeded prior is today's fixed map (`goals/exam_calibration.py:30`), basis `legacy`, ≥1 logit wide on slope and intercept. Eedi (basis `population`) is used only after a licence and scale check (LPQ1).
   - **Data caveat:** all of the owner's taps so far are 4–5, so the slope stays at its prior until taps vary. There is no prompting to tap differently (LPQ10).
3. **The four claim-defect fixes** (§3.0b item 1), as their own small successor after AD23 lands.
4. **Optional: liquid stability** (§4.6), the one liquid-time-constant use kept.

**Numbers in LP-min** (revision 4). Each is one of three things:
- **A seeded prior,** with its `prior_basis` and width stated. The data move it.
- **A structural form:** the logistic link bounds a mass below 1, and `w = 0` is plain FSRS.
- **`keep`, with a reason:** kill switches and context budgets. They are operational, never statistical gates.

§3.3's auto-flag "over a declared window" does not apply to LP-min. A family that doesn't help shrinks under its learned prior width, and the report still shows it. Numbers elsewhere in this spec belong to dropped or deferred families, and are not live.

**The review's other verdicts stand:**
- **LP0:** trimmed. Register the 7-day decay and `REPAIR_MIN_RECENT_ERROR`, with a narrow inline-literal audit, in the LAST architecture stage. No 343 treatment tags.
- **LP1's general machinery:** built only as far as LP-min needs.
- **LP2:** dropped.
  - **Liquid drift (§4.2) is dropped,** because AD §5.5 fixes the drift as not learnable at n=1. "Teaching changes the learner" goes to AD §5.11's opportunity kinds (`spec_teacher_v1.md` §14.2) and to liquid stability's lesson input (§4.6).
  - **The 7-day error decay (§4.3) is only registered as a named setting, not made liquid,** because error recurrences are too rare to fit. It is labelled `keep` for that reason. It is an existing value (basis `legacy`) and is not new.
- **LP3:** dropped, except the lesson-check family above.
- **LP4:** folded into RW6b's purpose dating.
- **LP5:** deferred to the EVSI-calibration track.
- **LP6:** dropped. A trained LTC, CfC or CVPR LTC+Hopfield network stays dropped. The bitter-lesson stand-in is the LLM reading the state plus retrieved episodes.
- **§3.0a:** measure-only, as an `llm_v3+reading` outside forecaster in AD.
- **Reading-attention time constants** (dwell, scroll) are excluded by AD A12.

---

## 1. Code truth (audited 2026-10-23)

**The registry** (`params/parameter_registry.py`). 623 entries: 343 `decision` and 280 `structural`. By class, the decision entries are:

| Class | Count |
|---|---|
| `threshold` | 191 |
| `constraint` | 62 |
| `prior` | 30 |
| `evidence_mass` | 29 |
| `shaping_weight` | 19 |
| `likelihood` | 12 |

- **Every one has `default_status = heuristic`.**
- The registry already supports `simulation_validated` (promotion gates `sim/diagnostic_validation.py::planted_learner_suite`, `sim/grader_confusion.py::planted_misgrade_suite`) and `live_calibrated` (gated by the activated real-outcome manifest), plus frozen manifests per algorithm version and bind-event logging for dormant constraints.

**Audit gap.** The audit walks config leaves and *named* module-level constants. Inline literals escape it. The clearest case is the **7-day error-recency decay** `severity · exp(−Δt/7)`, hard-coded in:
- `attempts/surprise.py:149`, the predicted error-type distribution;
- `scheduling/scheduler.py:3537`, the `recent_error` score;
- `diagnosis/probes.py:1470`;
- and described in `daily_plan/lanes.py:61`.

It is a decision-relevant time constant, and it is unregistered.

**The EKF time model** (`learner/mastery.py:342–353`):
- `P_pred = min(P + sigma2_drift · Δt, p_max)`: variance grows **linearly at one constant rate** for every LO, regardless of what happened in the interval.
- `sigma2_drift = 0.01` and `p_max = 4.0` are registered heuristics.
- The mean does not move between observations.

**Fitting.**
- `learnloop fit fsrs` (`cli/fit.py`, `scheduling/fsrs_fitting.py`) fits FSRS weights by review log-loss with L2 toward the defaults. Settings: `[fitting.fsrs] min_reviews = 50`, `l2_lambda = 1.0`.
- `fitted_parameters` stores `scope`, `params_json`, `training_rows_count`, `training_data_through`, `metrics_json` and an `active` flag with `deactivated_at`.
- `item_parameter_state` is a per-item empirical-Bayes difficulty posterior, shrunk toward the authored difficulty.

**Switching rule** (`spec_learner_field_v1.md` §7.4). A challenger must beat the incumbent on attempt-level log-loss, overall and on first attempts, with a bootstrap interval excluding 0 and a margin fixed in advance. "Can't tell keeps the incumbent". Activation is a successor with a kill switch.

**Utility-like constants already exist:**
- `robust_composition:VALUE_PER_NAT_MINUTES`
- `robust_composition:BURDEN_COST`
- `action_loss:DEFAULT_INTERVENTION_MINUTES`
- `intent.recall_targets`

**Data at hand.** The owner's linear_algebra vault copy has 70 practice attempts. Most fits will stay at their priors for months. With shrinkage that is the correct outcome, not a failure.

---

## 2. Registry change: a learnability tag

Add `treatment: Literal["learn", "liquid", "delay", "utility", "keep", "retire"]` to `ParameterSpec`, plus, where it applies:
- `learn_family`, naming the §3 family that owns it, and `mechanism: latent | grid`;
- `prior_scale`, the prior's width in the parameter's natural scale, and `prior_basis: population | published | llm_content | claim | simulation | legacy` (§3.0);
- `utility_ref`, the §6 utility a threshold derives from.

**Audit extension:**
- Every `decision` entry must carry a treatment.
- A new AST rule flags numeric literals inside `exp(…/k)`, `timedelta(days=k)` and `* k` expressions in decision paths (`attempts/`, `scheduling/`, `diagnosis/`, `daily_plan/`, `learner/`), so inline time constants like the 7-day decay get registered.
- The rule fails loudly on new unregistered literals. It has an explicit allowlist only for unit conversions (86400, 60, ln 2).

**Initial classification.** This is a proposal, to be confirmed in the LP0 audit commit. The families are illustrative, not exhaustive:

| Treatment | Families (registry prefixes) |
|---|---|
| learn | `evidence.attempt_types`, `evidence.blueprints`, `evidence.item_coverage_*`, `mastery.irt` priors, `mastery.base_observation_variance`, `mastery.cold_start_prior_logit_variance`, `probe.irt`, `probe_families:GRADER_CHANNEL_RELIABILITY`, `grader_calibration:*` priors, `recall_coverage.*` discounts, `rung_variants.*`, `teach_back.transfer_evidence_multiplier`, `exam_seeding.*` confidences, the tap/hedge → probability maps |
| liquid | `mastery.sigma2_drift`, the 7-day error recency (new: `recency.error_tau_days`), `reader_dialogue:ROUTING_PRIOR_HALFLIFE_DAYS`, `progression:DIMINISHING_MASS_DECAY`, `hypothesis.decay_pressure_*` |
| delay | `learner_text_gaps.seed_check_delay_days`, `.sooner_check_delay_hours`, `placement.assumed_first_interval_days`, `progression:POST_LAPSE_FOLLOWUP_DAYS`, `progression_policy:ORTHOGONAL_NEXT_DELAY_DAYS`, `pattern_ladder:STAGE_DELAY_DAYS`, `capture.test_me_later_days`, `hypothesis.claim_cooldown_days`, `hypothesis.reentry_gap_days`, the teacher's `recheck.near_miss_days` |
| utility | `scheduler.followup.tau_*`, `scheduler.surprise.theta_*` and `epsilon_error_surprise`, `probe.episode.*_threshold`, `placement.fast_track_q` and `known_probability`, `misconceptions.tau_misconception_resolved`, `facet_diagnostic.tau_*`, `grade_resolution:REVIEW_CONFIDENCE_THRESHOLD`, `grading:CLARIFICATION_CONFIDENCE_CEILING`, `voi_stopping.*` |
| keep | every `constraint`; `plan.*` budgets; `diagnosis.*` and `diagnostic_augmentation.*` sample and history limits; `teacher.*` caps; `misconceptions.sim_gate_*` (validation gates are not learned from the data they validate) |
| retire | `scheduler.*_weight`, `router.weights`, `router.k`, `router.epsilon_min`, `familiarity:V1_COEFFICIENTS`, `reader_requests:PRIORITY_BAND`, `progression_policy:SIBLING_SUCCESS_SHRINKAGE` |

---

## 3. Learning online, AD-style (treatment L)

**Revision (2026-10-23, the same day as the first draft).** The first draft fitted each family offline, refit it monthly, and activated it by a held-out test. That is slow, and it conflicts with the adaptive-difficulty spec's constraint A5: "no point-fitted or hand-set hyperparameters". Under A5, every effect that weighs an observation is latent state with an a-priori, versioned prior, learned with uncertainty, and vault-level hyperparameters are a posterior over an a-priori grid.

This spec adopts AD's mechanism wholesale. The owner wants these quantities to adapt quickly, as AD2/AD3 were built to, and AD's machinery is what does that.

### 3.0 Where priors come from (not the learner's history)

Each learnable family gets a versioned prior set (`lp_priors_v1`, alongside `ad_priors_v1`). A prior's **mean** says what to expect; its **width** decides how fast this learner's data take over. Sources, in order of preference:

1. **Population distributions.** The prior should be the distribution of the parameter *across learners*: its mean is the typical learner, and its spread is how different a learner can be. That width is what makes adaptation fast for an atypical learner without making it noisy for a typical one.
   - **FSRS defaults** are already a population prior, fit on many users' review logs.
   - **Public datasets** give between-learner distributions for learning rates, slip/guess, forgetting and error recurrence: EdNet, ASSISTments, Eedi (which carries per-answer confidence, so it can calibrate the tap and hedge maps), and the KT benchmarks listed in the research sweeps.
   - **Later, LearnLoop's own contributors.** The repo stays public for future n>1 data contributions. Once others contribute, the population prior can come from LearnLoop itself.
2. **Published effect sizes,** where no dataset fits:
   - learning rate per opportunity (AD's `γ ≈ 0.2` logits, from field's `+practice` arm);
   - surprise-modulated forgetting (A8);
   - high-confidence errors returning (A1).
3. **The frontier LLM, reading content, never learner data** (AD §5.5, §5.10).
   - It proposes item-side and topic-side prior means: difficulty, the soft Q-matrix, couplings.
   - Its trust is itself latent (AD's `α_llm ~ N(0.2, 0.2²)`) and is learned.
   - This is the most informative cold-start prior available for content-side parameters. It improves as models do.
4. **The learner's own words, as claims.** "I know this", a goal statement, prior coursework. Claims re-anchor *means* in the stream, never variances (AD §5.5).
5. **Simulation.**
   - Every prior set is checked by planted-learner suites: does the filter recover planted values, and how many answers does it take?
   - Fixed measurement constants are swept in the harness (AD §5.5).

### 3.0a The LLM reading the learner's reading traces (owner, 2026-10-23; proposed amendment to AD R13)

The owner adds a source: **the frontier LLM reads the learner's reading traces and proposes difficulty, Q-matrix and coupling priors.**

This amends two AD rules:
- **AD R13:** the relatedness LLM "reads the vault's content, never learner data".
- **AD §4.2's split:** "forecasts that read the learner's history → competing experts, never offset priors".

The amendment is worth making: your words while reading are among the most informative cold-start signals available. But three hazards have to be designed out.

1. **Double counting.**
   - Reading events already enter the state as learning opportunities (AD §5.11).
   - Self-check verdicts already enter as their own term (D22).
   - Tutor questions already enter as question signals.

   An LLM that reads those same traces and also sets a prior would count them twice, so the posterior would be overconfident.
2. **Confounding.** "You struggled reading section X" is evidence about *your* level on X, not about the items' difficulty. Fold it into item difficulty and the model starts explaining your gap as a hard item. The data only see sums (AD §5.8).
3. **The reading-signal firewall** (AD A12 limit 1): no dwell, scroll, highlight or skip count reaches the state. Routing magnitudes through an LLM would breach it indirectly.

**The proposal: one target per quantity, one path per input.**

| What the LLM proposes from reading traces | Where it enters | Why that's safe |
|---|---|---|
| **Your level on topics you have not answered yet** | An **inferred claim**. It re-anchors the facet or subject mean through AD's existing claims channel (§5.5): mean-only, variance kept at least at the prior, only for scopes with no eligible observation yet, shrunk by a learned trust `λ_inferred ~ N(0.5, 0.25²)` on [0, 1] | Claims precede observations by construction, so the first answers overwrite them: no double count. Trust is learned from how well inferred claims predict first answers |
| **Couplings and Q-matrix loadings** | The **proposal**: candidate pairs and prior means, merged with the content-based proposal. Example: going back to the definition of A while reading B, or asking "what was A again?" on B's page, nominates or strengthens the A–B pair | Strengths are still learned from answers through the `χ` grid. Reading traces choose candidates; answers set strengths. Different data, one path each |
| **Item difficulty** | **Not from learner traces.** It stays content-only (LLM label, solver panel, source origin), as AD R7 has it | Learner-informed difficulty is confounded with ability. Your part is already your ability state |

**What the LLM may read:**
- the learner's **text**: intent box, questions, self-explanations, annotations, self-check answers;
- **discrete events**: which passage was opened from which, what was looked up.

It may not read magnitudes (dwell, scroll, highlight counts) unless the owner also amends A12. Text is where the signal is anyway (the owner's "learner text over skip buttons" principle).

**The order of steps: measure before trusting.**
1. **As an outside forecaster first.** Before it touches any prior, the LLM given reading traces forecasts your first answers on topics you have read but not yet answered (AD §8.2 forecasters, `forecast_receipts`). It is scored against the content-only prior. This changes no state and is cheap.
2. **Promote to inferred claims and coupling proposals** only if it beats the content-only prior on first-attempt log-loss. Otherwise keep it as a scored expert.
3. **Kill switch:** `priors.reading_trace_llm`. Auto-flag (AD §10.4) when inferred claims predict first answers worse than no claim.

### 3.0b Cold-start seeds: claims, tutoring questions, confidence probes (owner, 2026-10-23)

**Code truth** (audited 2026-10-23 at `b7e0444b5`). Today nothing that happens before practice moves an LO's prior at runtime.
- **Claims.**
  - The init wizard writes one global claim per vault, and it acts only when a mastery row is created. Sync creates a row for every LO, so in effect the claim acts once.
  - A tutor gap declaration writes a claim but never calls `reanchor_mastery_from_claim` (`tutor/promotions.py:773-795`), so it is inert on existing LOs.
  - On replay, rows reseed from the claims in force *now*, not from those in force at each claim's own time.
  - A claim merged into an LO that already has evidence (`apply_claim_evidence`) has no variance floor, so it can shrink variance. That contradicts AD's "claims never lower a variance".
  - Rank ties are broken toward the higher claimed level.
- **"I know this"** writes a routing decision only.
- **Confidence taps, reader self-checks and the D12 question masses** are logged or offline only.
- **Tutor questions affect live decisions only by:**
  - blocking fast-track;
  - putting "taught first" ahead in ordering;
  - targeting follow-ups after a failure.
- **Each LO is independent.** The first answer on one LO informs no other LO; sharing waits on AD2/AD3.
- **The owner's own vault copies are still at mvp-0.8,** so F2 placement has never run on them.

**Rule: every cold-start signal enters by exactly one of three paths, each with learned trust.**

| Signal | Path | What it does | Learned quantity | Evidence |
|---|---|---|---|---|
| **Level claims** ("I know this", "too easy", the init wizard, gap declarations) | **Mean re-anchor** (AD claims channel) | Moves the mean only, at the claim's own time, only for scopes with no eligible observation yet. The variance never drops below the prior's | Per-learner claim reliability `λ_claim ~ N(0.4, 0.2²)` on [0, 1], learned from first-review outcomes on claimed scopes | Self-assessment ρ ≈ .34–.44 for level claims; ≈ 0 for "gain" claims, which are therefore not accepted (D1, D12) |
| **Inferred claims from text** (reading traces §3.0a, tutoring questions, goal and self-description text) | **Mean re-anchor**, as above | The LLM returns a mean and SD per facet, pooled over prompt variants, capped at about 2 items' worth of precision | Trust `λ_inferred`; kept only if it beats no claim on first-attempt log-loss | LLM-elicited priors beat flat priors at small n, and beat direct LLM prediction (D7, D8) |
| **Confidence on a quick probe** | **Likelihood term** (an AD sub-arm, like `+rating`) | A 1–5 tap becomes evidence beside the outcome, through a per-learner calibration slope and intercept | Calibration `(a_conf, b_conf)` with population priors from Eedi's confidence data | About 1.5–2× item-equivalents per rated answer; mixed replications (D9) |
| **Tutoring-question facet and type** | **Routing + uncertainty** | The question's facet is where the next quick probe goes, and the question is a liquid-drift input (§4.2: `u_question` inflates that facet's variance). It sets no level directly | The drift weight `w_question` (latent, prior `N(0, 0.5²)`) | Questions say *which* facet, weakly *how much* (D3–D6) |

**What changes compared with today:**
1. **Fix the four claim defects** (one small successor):
   - gap claims re-anchor;
   - replay applies claims as of their own time;
   - a warm claim merge keeps a variance floor;
   - ties break by recency, then pseudo-count, never by level.

   *Built 2026-10-25 (LP-min (a); `docs/reviews/lp-min-claim-fixes.md`):* one successor, `CLAIM_FIXES_ALGORITHM_VERSION` (built as `mvp-0.32`, renumbered at landing), with one kill switch for all four, `mastery.claim_fixes_enabled`. A gap declaration re-anchors through `reanchor_mastery_from_claim` at the claim's own stamp. Replay seeds each LO from the claims made by its first attempt and re-anchors each later claim from a re-anchoring source (rung-variant requests, too-easy/too-hard reports, gap declarations) at its own `created_at`, before any attempt stamped after it. A warm merge moves the mean by the same precision weights and keeps the state's own variance (`max(merged, current)`: structural, no new number). Ties: specificity, then recency, then pseudo-count, then the id. Off, or below the tag, every path is the predecessor's byte for byte. *Codex review (2026-10-25; `docs/reviews/lp-claim-fixes-codex-review.md`):* claims and attempts replay in one order, `(created_at, id)`, so a claim stamped in the same second as an attempt keeps the order it was written in (F5); a claim seed under the tag is floored at the cold-start variance, and a zero-evidence re-anchor keeps the row's own variance, so no claim ever makes an estimate more certain (F4; this supersedes the earlier note that the cold seed stayed at `max(1/pseudo-count, 2.0)`); a gap claim is applied once per question event, atomically with its mastery effect (F1); the upgrade's activation is journalled and completed on the next start or upgrade if the process dies between the config's publication and the commit (F2), and it re-seeds claim-covered LOs without attempts as a full rebuild does (F3). *Codex re-review (2026-10-25):* a re-anchoring claim records, in its own transaction, how many of its LO's attempts were already applied (`learner_claims.applied_after_attempts`, migration 221), and replay applies it after that many, because an attempt's id is minted before grading and cannot place it (F7; `(created_at, id)` remains the order for a claim without the record); a zero-evidence seed keeps the largest variance any earlier re-anchoring claim's seed left, as live does (F8); every opener that may write completes an interrupted activation or raises, and every other attach (a read-only report, the MCP server, the phone host) refuses it (F2); the claim line reads placement as it stands now, so a miss the diagnosis wait decides carries it (F9).
2. **Retire the D12 question masses** (prerequisite 0.15, mechanism 0.1). They become the learned `w_question` drift weight plus question text inside inferred claims. No hand table by question type (D4, D5).
3. **"Got it" or "I understand" is never evidence** (D3).
4. **Quick probes without ceremony** (F2 holds). Probes are served on vault items, so they carry full evidence, with the confidence tap, worded "How likely…" as today (D10). They are offered:
   - at lesson open (`spec_teacher_v1.md` §8);
   - from the goal-scoped quick check;
   - as router `measure_diagnostic` blocks of 2–3 items when their EVSI is positive;
   - as Reader self-checks with the tap (the D22 term).
5. **Point probes where priors are unsure or extreme.** Aim them at facets whose claim or inferred prior is far from the subject level, or whose variance is high. That is where an informative prior saves items, and where an "assumed known" is most likely to be wrong (D2).
6. **Monitor tap reactivity.** Omit the tap at random on a fraction of probes (`tap_shown`, teacher spec §11.1), and compare outcomes with and without it for this learner (D10).
7. **Claim feedback, not trait labels.** When a first review resolves a claimed scope, the review's feedback line may say so: "You marked this as known; this check: missed". Accuracy feedback is what raised self-assessment validity to .51 (D1). No calibration score or trait label is ever shown (ITS sweep P4).
8. **Optional, low value for one owner-learner:** overclaiming foils in bulk-claim lists (D11).

**Expected effect.**
- With a calibrated claim, an inferred prior, and 2–4 confidence-rated probes, a new subject starts near the learner instead of at the cold-start mean.
- AD's sharing (§5.9–5.10) then makes about 10–13 answers per subject enough for band mode, and fewer on coupled topics.
- None of this reaches the owner's vaults until they are upgraded past mvp-0.8. That upgrade is owner-run.

**A prior is never "today's hand value" by default.** Where today's value is the only basis, the prior is centred on it with a **wide** width (sd ≥ 50% of the value, or 1 logit), and the registry labels it `prior_basis: legacy`. That label marks the prior as debt to be replaced from sources 1–3.

### 3.1 Two kinds of learnable quantity, two online mechanisms

| Kind | Examples | Mechanism | Adapts |
|---|---|---|---|
| **Latent effects** (continuous, observed every attempt) | Evidence masses per attempt type; slip and guess; the tap/hedge → probability map; per-error-type recency offsets `b_e`; the teaching shift `w_shift`; liquid-drift weights `w` | Latent state in the filter with a Gaussian (or log/logit-Gaussian) prior, updated by assumed-density filtering on every attempt, exactly as AD updates `γ`, feature effects and trust weights (AD §5.6) | **Every attempt.** No refit, no activation step |
| **Structural hyperparameters** (few, set how strongly things share) | The liquid-drift base `σ²₀` and change-point jump `σ²_cp`; the recency base `τ₀`; how much error recency is shared across types | A posterior over an a-priori grid, re-weighted by each attempt's marginal likelihood: `W_t(ξ) ∝ W_{t−1}(ξ) · Z_t(ξ)`. This is AD's `ad_hyper_v1` mechanism (AD §5.6 step 5, §5.10). Predictions average over the grid | **Every attempt.** The weights move as soon as the data favour a point |

**Why this feels fast:**
- **Per-attempt updating.** There is no waiting for a monthly refit or a held-out test.
- **Sharing.** Each answer informs every shared quantity: the subject level, `γ`, the trust weights, the drift weights. AD §5.9's arithmetic applies. A usable subject estimate comes after about 10–13 answers, and a coupled new topic needs about 3–8 of its own.
- **Liquid time constants** (§4). After a lesson or a surprise, the state's variance inflates, so the next answer moves the estimate a lot. This is the fast response to *the learner changing*, which complements AD's learning transition (`γ`).
- **Wide priors.** After about 12 answers on a quantity, AD's priors carry about a sixth of the weight. A wrong prior costs answers, not direction.

**Fast and slow are different layers.** The *user-visible* sense that LearnLoop "adapts to me" comes from the learner state: AD2/AD3's subject level, couplings, `γ` and band selection. The machinery parameters here (evidence masses, half-lives, drift weights) adapt per attempt too, but they move more slowly because each attempt carries less information about them. That's fine: errors in them cost little, and their uncertainty is carried into predictions rather than hidden.

### 3.2 Replay and persisted meaning (supersedes the first draft's epochs)

- **Online posteriors are DERIVED state.** They are recomputed by replay from the immutable attempt stream, the versioned prior set (`lp_priors_v1`) and the versioned grid. So rebuild-equivalence holds without fitted-set epochs, activation receipts or refit cadences.
- **A new family, a changed prior set, or a changed grid** is an algorithm successor, per the playbook.
- **The data moving the posterior is not.** It is the same algorithm reading more data.
- **`fitted_parameters` stays for FSRS's existing offline fitter.** FSRS's online variant (its weights as latent state) is a later option under the same rules.

### 3.3 Monitoring instead of activation

There is no activation gate: a family is live when its successor lands, behind its kill switch. AD treats field §7.4 the same way, as "a monitor, not a precondition". Per family, the report shows:
- **prior → posterior contraction** (how much the data have said);
- **prior sensitivity:** rerun with each prior mean shifted ±1 sd and count how many decisions change (AD §5.8);
- **prequential log-loss** against the family switched off;
- **`prior_basis: legacy` debt,** listed until each is replaced from §3.0 sources 1–3.

A family whose prequential loss is worse than switched off over a declared window raises an auto-flag (AD §10.4) that recommends the kill switch.

## 4. Liquid time constants (treatment T)

### 4.1 The idea, from LTCs

Liquid Time-Constant networks (Hasani, Lechner, Amini, Rus & Grosu, AAAI 2021) are continuous-time recurrent units whose effective time constant depends on the input:

```
dx/dt = −[1/τ + f(x, I; θ)] · x + f(x, I; θ) · A        τ_sys = τ / (1 + τ · f(x, I; θ))
```

The state forgets fast or slow depending on what is arriving. Closed-form continuous-time networks (CfC; Hasani et al., *Nature Machine Intelligence* 2022) approximate the same dynamics without an ODE solver.

**For LearnLoop the transferable part is the parameterization, not the network.**
- A full LTC or CfC has thousands of weights. One learner gives about 10³ events a year.
- What *can* be fit at n=1 is a time constant with a handful of input weights: `τ(u) = τ₀ · exp(wᵀu)`, with `w` shrunk toward 0. With `w = 0`, the model is exactly today's constant τ₀.
- **FSRS is already this pattern.** Its memory stability is a state-dependent time constant learned from reviews.

### 4.2 Liquid drift in the EKF

**Dropped (owner, 2026-10-24; §0a).** AD §5.5 fixes drift as not learnable at n=1. This subsection is kept for the record.

Today, `P_pred = min(P + σ²·Δt, p_max)`: one drift rate for everything. Replace it with an input-dependent drift integrated over the interval:

```
P_pred = min(P + ∫ σ²(t) dt, p_max),
σ²(t)  = σ²₀ · exp(w_teach·taught(t) + w_read·read(t) + w_surp·S_BF(t) + w_gap·log(1+Δt)) + σ²_cp · 1[change point]
```

| Input u | Source | Expected sign | Why |
|---|---|---|---|
| `taught` | `reveal_events` (`lesson`, `guided_redo`, `repair_display`) on the LO in the interval | + | Teaching is a change point: the old estimate is stale and should be trusted less (research A8) |
| `read` | `reveal_events` `source_review` / Reader time on the LO | + (smaller) | As above, weaker |
| `S_BF` | the Bayes Factor Surprise of the last observation (A8): prior predictive vs. current-belief predictive | + | Surprise signals the state may have changed; forgetting is modulated by surprise |
| `log(1+Δt)` | the gap length | ± | Lets drift be concave or convex in time, not forced linear |
| `σ²_cp` | a learned jump added once at a detected change point (a teaching event or `S_BF` above its fitted level) | + | A discrete reset, as in a change-point filter |

- **Variance only.** Liquid drift changes how much the old estimate is *trusted*, never what it *says*. Teaching does not raise mastery by itself.
- **A separate, prediction-only teaching shift** in the learner predictor (field §4) may move the predicted mean: `μ_pred += w_shift · taught`, fit on the next cold attempt.
  - It never writes evidence.
  - It never certifies.
  - It is not read by the EKF evidence path (knowledge model §9.1, §9.3; the adaptive-difficulty rule "reading raises predicted level, never certification").
- **Learning.**
  - The four `w`'s are latent effects with priors `N(0, 0.5²)`, updated online (§3.1).
  - `σ²₀` and `σ²_cp` are a grid posterior (§3.1). `σ²₀` ∈ {0.005, 0.01, 0.02} (today's 0.01 in the middle) and `σ²_cp` ∈ {0, 0.5, 1.0}, re-weighted by each attempt's marginal likelihood.
  - All are global, with optional per-LO offsets on σ²₀ only.
- **Kill switch:** `mastery.liquid_drift.enabled`. Off means exactly today's linear drift.

### 4.3 Liquid error recency

**Register only (owner, 2026-10-24; §0a).** `recency.error_tau_days` = 7 becomes a named setting; it is not made liquid, because error recurrences are too rare to fit. The design below is kept for the record.

Replace the hard-coded `severity · exp(−Δt/7)` in all its sites with one registered function:

```
weight_e(Δt) = severity · exp(−Δt / τ_e),     τ_e = τ₀ · exp(b_e + w_repair · repaired + w_recur · prior_recurrences)
```

| Term | Meaning |
|---|---|
| `τ₀` | Prior 7 days (today's value) |
| `b_e` | Hierarchical per-error-type offset (slips should fade fast, misconceptions slowly) |
| `repaired` | A repair or lesson resolved this error since it occurred (expected to shorten τ) |
| `prior_recurrences` | How often this error type has come back for this learner (expected to lengthen τ: the hypercorrection "errors return" finding, research A1) |

- **Objective:** the predictive likelihood of the error type recurring on the next attempt that exercises its facet.
- **Sites:** one function, registered as `recency.error_tau_days` plus its weights, replaces the inline literal in `surprise.py`, `scheduler.py`, `probes.py` and the `lanes.py` description.
- **Kill switch:** `recency.liquid.enabled`.

### 4.4 Other time constants

- `reader_dialogue:ROUTING_PRIOR_HALFLIFE_DAYS`, `progression:DIMINISHING_MASS_DECAY` and `hypothesis.decay_pressure_*` get the same treatment: a registered τ₀ (today's value) with input weights. Each is fit only if it has an outcome to predict. Otherwise it stays `keep`, which the LP0 audit decides.
- **Confidence and hedge maps** are not time constants, but they are learned the same way (treatment L). The 1–5 tap → probability and the hedge read → probability get a two-parameter logistic recalibration, learned online as latent effects (§3.1), with its prior from Eedi's per-answer confidence data where the scale maps (§3.0). Until it activates, `learner_surprise` (`spec_teacher_v1.md` §11.1) uses today's mapping.

### 4.5 Why not a full LTC or CfC predictor now

A neural continuous-time learner model (CfC or LTC encoder over the attempt stream) is a legitimate **challenger predictor** under field §7.4, but not a v1 component:
- **It needs population pretraining** (EdNet, ASSISTments, Eedi; Eedi carries per-answer confidence). That makes it a narrow population model, which the owner's bitter-lesson stance argues against unless it wins.
- **It can't be fit at n=1**, only adapted: a few output scalars could be fit on the owner's data.
- **The bar is clear and already defined:** it must beat `mastery_ekf` with liquid drift on attempt-level log-loss under §7.4.

It is listed as optional phase LP6 (§9). **LP6 is dropped (owner, 2026-10-24; §0a).**

### 4.6 Liquid stability (LP-min, optional; owner, 2026-10-24)

**The one liquid-time-constant use kept.** Reviews are the densest outcome, the evaluation is clean, and calibrated retention timing is infrastructure that a frontier model does not replace. That makes this the honest successor to §4.1's idea.

- **Formula:** `S_eff = S_fsrs · exp(ŵᵀu)`, where `ŵ` is the posterior mean of a few latent weights, updated online (§3.1).
  - With `ŵ = 0`, this is exactly plain FSRS. That is a property of the form, and it is where every prior starts.
  - **Seeded prior:** each `w_k` ~ N(0, s²). Its centre has basis `published`: no change to FSRS.
  - **The width `s` is not fixed** (owner, 2026-10-24). It is a grid posterior, AD's `ad_hyper` mechanism: `W_t(s) ∝ W_{t−1}(s) · Z_t(s)`, where `Z_t(s)` is review `t`'s marginal likelihood under width `s`.
    - The support is {0.05, 0.15, 0.5, 1.0}, from uniform weights (basis `simulation`: the planted-recovery suite must tell the points apart).
    - When the inputs don't help, the posterior moves to the narrowest widths, and `ŵ` stays at 0.
- **Inputs `u`** are what FSRS does not see:
  - **How the item or LO was learned:** lesson exposure (`reveal_events` with basis `lesson:<id>`, `spec_teacher_v1.md` §12), worked example or guided redo, the hint depth reached, or cold practice;
  - **The confidence tap or hedge read on the last attempt,** through LP-min's recalibration, with confident misses as a separate sign;
  - **The last attempt's surprise:** Bayes Factor Surprise, or predictive surprise, logged.
- **Objective:** review-outcome log-loss, prequential.
- **No activation threshold and no keep margin** (owner, 2026-10-24; revision 3's ≥50-review switch-on and 0.01-nat margin are removed).
  - It learns from the first review. With few reviews, the width and weight posteriors stay at their priors, which is plain FSRS.
  - The report shows prequential review log-loss beside plain FSRS's, with no gate.
- **Kill switch:** `scheduling.liquid_stability.enabled`, an operational off-switch (`keep`), not a statistical gate.
- **Logging.** The inputs are logged from the teacher's TE1 onward (the lesson receipt's `stability_inputs`), so the data are there when the family is built.
- **Interfaces.** It feeds retrievability, and so the lesson's delayed-check dates (`spec_teacher_v1.md` §13) and the retrievability targets (§5, folded into RW6b).
- **Successor.** One algorithm successor when the family is introduced: it changes scheduling, which is persisted meaning (playbook step 1). After that, the weights moving with the data is the same algorithm reading more data (§3.2), so it is not a successor. No other activation step exists.

---

## 5. Delays become retrievability targets (treatment D)

Many "wait N days" constants answer the same question: *when will a cold check be informative and not trivially passed?* That is a forgetting-model question.

**Rule.** A delayed check for purpose `k` is due when the FSRS-predicted retrievability of the target falls to `R*_k`:

| Purpose | Today | Proposed target `R*_k` (utility-type, §6) |
|---|---|---|
| Gap seed check (`learner_text_gaps.seed_check_delay_days`) | fixed days | 0.85 |
| Near-miss recheck after a confident error (teacher `recheck.near_miss_days`) | 2 days | 0.90 (early, because high-confidence errors return; A1) |
| Assumed-known first review (`placement.assumed_first_interval_days` = 14) | 14 days | 0.80 |
| Post-lapse follow-up (`progression:POST_LAPSE_FOLLOWUP_DAYS`) | fixed days | 0.85 |
| Lesson delayed cold check (teacher receipt) | FSRS first interval | `intent.recall_targets` for the LO's intent |

- **Effect.** About ten separate day constants collapse into one learned forgetting model (FSRS: today's offline fitter, later its online variant, §3.2) plus a few target recalls, which are preferences.
- **Floors and ceilings stay `keep`:** never sooner than `delay.min_hours`, never later than `delay.max_days`.
- **Fallback:** where FSRS has no state yet, today's constants remain the defaults.

---

## 6. Thresholds become utilities (treatment U)

A threshold such as "diagnose when Bayesian surprise > τ nats" encodes a decision. With calibrated probabilities, the decision follows from expected utility:

```
act  ⇔  P(state | signals) · V(act | state) − C(act) > V(default)
```

The threshold disappears. What remains are **utilities in learner-time units**, and most already exist as constants:

| Utility | Meaning | Existing anchor |
|---|---|---|
| `u.minute` | Cost of one learner minute | `action_loss:DEFAULT_INTERVENTION_MINUTES`, `robust_composition:BURDEN_COST` |
| `u.nat` | Value of one nat of information about the learner | `robust_composition:VALUE_PER_NAT_MINUTES` |
| `u.missed_gap` | Cost of leaving a real gap undiagnosed until the next lapse | new |
| `u.false_known` | Cost of treating an unknown LO as known (an assumed-known error) | new |
| `u.false_certify` | Cost of certifying something not learned | new (expected large) |
| `R*_k` | Target recall per purpose (§5) | `intent.recall_targets` |

**Conversion order.** One family at a time. Each conversion must pass replay non-inferiority against the threshold it replaces, under a pessimistic bound (B12). Expected order:
1. `placement.fast_track_q`. Assume known iff `P(not known) · u.false_known < cost to teach`.
2. `scheduler.followup.tau_*`. Follow up iff the diagnosis's expected action change × value exceeds its cost. EVSI already computes the numerator.
3. `probe.episode.*_threshold`. Most are already superseded in spirit by value-of-information stopping. Delete those that are.
4. `scheduler.surprise.theta_pos/neg`. These become routing sensors (`spec_teacher_v1.md` §11) rather than cut-offs.
5. `misconceptions.tau_misconception_resolved`. Resolve iff P(resolved) from the learned recurrence model (§4.3) clears the `u.missed_gap`-implied bound.

**Calibration first.** A utility rule is only as good as its probabilities. Each family converts only after its probability source is calibrated: the learned family (§3), or a sensor that passed the probability scoreboard (`spec_teacher_v1.md` §15.1).

**Eliciting utilities.**
- The owner sets them once, in a short `learnloop utilities` dialogue that asks comparisons ("is missing a real gap worse than 3 wasted probe minutes, or 10?").
- They are stored in config, shown in the report, and versioned with the algorithm.
- They are preferences, so they are never fitted.

---

## 7. Relation to LTC + modern Hopfield memory (CVPR 2026)

**The paper.** Swain, Cheoi & Ko, "Coupling Liquid Time-Constant Encoders with Modern Hopfield Memory", CVPR 2026 poster ([CVPR page](https://cvpr.thecvf.com/virtual/2026/poster/37795); [paper](https://openaccess.thecvf.com/content/CVPR2026/html/Swain_Coupling_Liquid_Time-Constant_Encoders_with_Modern_Hopfield_Memory_CVPR_2026_paper.html)). Paraphrasing the abstract:
- **The problem:** continuous-time networks keep fast input dynamics and slow context in one hidden state, so new inputs overwrite useful past information.
- **The method:** at each step the LTC state is projected to a query, a modern Hopfield network retrieves a stored memory vector, and the two are concatenated before readout.
- **The results:** a bounded representation, lower loss curvature (Hessian trace about an order of magnitude below a standalone LTC), and a +2.3% mean accuracy gain over recurrent and continuous-time baselines on public time-series benchmarks, mostly in classification.
- **Code:** not yet released.
- We read only the abstract page and secondary summaries, not the full text.

**How directly it applies.**
- **As a model: not directly.** It is a trained neural encoder evaluated on generic time-series benchmarks, and it needs far more sequences than one learner produces. It belongs in the LP6 challenger slot (§4.5), pretrained on population data, at best.
- **As a design pattern: closely, and LearnLoop already half-implements it.**
  - **Fast state:** the per-LO latent state with its time constants. §4 makes those liquid.
  - **Content-addressable memory:** a modern Hopfield retrieval step is softmax attention over stored patterns (Ramsauer et al., "Hopfield Networks is All You Need", ICLR 2021). LearnLoop's equivalents are retrieval of similar past episodes:
    - the router's similar-past-decisions retrieval (`spec_action_router_v1.md` §5);
    - embedding-keyed attempt and idea retrieval;
    - the teacher's sensor track records (`spec_teacher_v1.md` §11.2: "of the last 12 times this happened…").
  - **Their failure mode is ours.** One hidden state that new inputs overwrite is exactly what a single EKF mean and variance per LO is. A confident error that will return is information the state forgets and a memory keeps.
- **The concrete translation.** The **readout** that combines state and retrieved episodes is the frontier LLM, reading the rendered state plus retrieved episodes in context. Attention over retrieved history is what it does natively. So the paper's architecture maps onto LearnLoop as:
  - liquid-drift EKF (§4.2) = the LTC state;
  - an episode memory = the Hopfield store;
  - an LLM in context = the readout.
- **What follows for this spec:**
  1. Make the state's time constants liquid (§4).
  2. Keep an explicit **episode memory**: past attempts, errors, repairs and their outcomes, keyed by embeddings, with fixed retrieval rules so it is replayable.
  3. Measure whether retrieved episodes improve the model's forecasts, using the same ablation as `spec_teacher_v1.md` §11.3, with "episodes" as one context family.
- **A trained LTC+memory network** stays a possible LP6 challenger.

---

## 8. Interfaces with other specs

- **Router** (revision 1's `spec_teacher_v1.md` §15.1; now deferred in the router spec):
  - **H1 ("tuned hyperparameters") is defined by this spec:** the live posteriors of the L, T and D families plus utility-derived thresholds (U). No refit cadence: the posteriors update on every attempt (§3).
  - H0 stays today's constants.
  - The probability scoreboard scores H1's implied probabilities against the sensor arms.
  - **2026-10-24:** with only LP-min kept, H1 would be today's constants plus LP-min. It waits with sensor mode for ≥600 router decisions.
- **Teacher** (revision 3):
  - the lesson-check weight family (§0a item 1; teacher §12.1) and its forecast challenger (teacher §12.2);
  - the tap/hedge recalibration feeds that weight, and the confidence events on the router card (teacher §15.2);
  - liquid stability's inputs are logged in the lesson receipt from TE1 (teacher §8.3), and `S_eff` feeds the delayed-check dates once RW6b dates by retrievability (teacher §13);
  - `learner_surprise` stays deferred (teacher §22);
  - the teacher's caps stay `keep`.
- **Learner field:** liquid drift and the teaching shift are predictor changes evaluated under §7.4. A neural challenger (LP6) enters there.
- **Knowledge model:**
  - nothing here propagates evidence structurally;
  - the teaching shift is prediction-only;
  - `part_of` and `related` edges never carry fitted couplings.
- **Adaptive difficulty:**
  - the target band (`practice_generation.*_success_band`) is a **utility** (a preference about difficulty), not learned;
  - AD's predicted P(success) is the calibrated input that makes band selection a utility rule.

---

## 9. Phases

**As decided 2026-10-24 (§0a):**

| Phase | Contents | Persisted meaning? | Status |
|---|---|---|---|
| **LP-min (a): claim fixes** | The four claim-defect fixes (§3.0b item 1), with a rebuild-equivalence fixture showing owner-copy mastery deltas | Yes → own small successor | **Kept.** Right after AD23 lands |
| **LP-min (b): lesson-check weight, forecast pool, tap/hedge recalibration** | `lp_priors_v1` (these families only, every prior labelled with its basis and width); AD §5.6's ADF and grid code factored into a neutral module; DERIVED state, with mastery replay as its owner; planted-recovery sim checks; report lines (§3.3, no auto-flag gate) | Yes. It ships inside the teacher's TE1 successor, at its seeded priors, because lesson checks exist only from TE1. Posteriors moving afterwards are not successors | **Kept** (owner) |
| **LP-min (c): liquid stability** (optional) | §4.6. Inputs logged from TE1; the prior width is a grid posterior; no review threshold and no keep margin | Yes → successor when the family is introduced | **Kept, optional** |
| **LP0** | Register the 7-day decay and `REPAIR_MIN_RECENT_ERROR`, plus a narrow inline-literal audit (exp literals, `timedelta` literals, time-delta divisions) | No | **Trimmed.** In the LAST architecture stage; no 343 treatment tags |
| **LP1** | General machinery beyond LP-min | — | **Not built** beyond LP-min (b) |
| **LP2** | Liquid drift and liquid error recency | — | **Dropped** (§4.2, §4.3) |
| **LP3** | Other evidence-mass, likelihood and prior families | — | **Dropped** (conflicts with AD A2, field F2 and KM §9.1; not identifiable at n=1) |
| **LP4** | Delays → retrievability targets | — | **Folded** into RW6b's purpose dating |
| **LP5** | Utilities and threshold conversions | — | **Deferred** to the EVSI-calibration track. Trigger: an EVSI calibration report exists, and ≥100 RW6b undo reasons are recorded |
| **LP6** | Neural continuous-time challenger | — | **Dropped** |

**Deferred, with triggers.** The trigger thresholds are `keep`: they decide when to build something, and are never parameters of the learner model.
- **A within-session fatigue time constant** (owner, 2026-10-24). Accuracy decay within a session, as a function of minutes on task, error streak and time of day, for the router's `burden_or_fatigue_cap` stop decision. Trigger: the router's replay report covers ≥600 logged decisions and ≥60 sessions of ≥10 attempts.
- **Tap/hedge recalibration beyond its LP-min role** (for example `learner_surprise`). Trigger: ≥200 tapped attempts with ≥20% of taps ≤ 3.

**The first draft's phase table, kept for the record:**

| Phase | Contents | Persisted meaning? |
|---|---|---|
| **LP0** | Registry `treatment` tag + classification of all 343 + the inline-literal audit rule + registering the 7-day recency decay (value unchanged) | No (registry and audit only) |
| **LP1** | `lp_priors_v1` + online latent-effect and grid machinery on AD2/AD3's filter (§3.1) + planted-recovery sim suites + the monitoring report (§3.3). First family: tap/hedge recalibration (feeds `learner_surprise`), with its prior from Eedi's confidence data | Yes → successor (after AD23 lands) |
| **LP2** | Liquid drift (§4.2) + liquid error recency (§4.3) + Bayes Factor Surprise logging | Yes → successor; kill switches restore today exactly |
| **LP3** | Evidence masses, likelihoods and priors families (`evidence.*`, `mastery.irt`, `probe.irt`, grader calibration) as latent effects | Yes → successor |
| **LP4** | Delays → retrievability targets (§5) | Yes → successor |
| **LP5** | Utilities dialogue + threshold conversions, one family at a time, each with replay non-inferiority (§6) | Each conversion → successor, or one batched successor per release |
| **LP6** (optional) | Neural continuous-time challenger (CfC/LTC + episode memory), population-pretrained, evaluated under field §7.4 | Only if activated |

Every phase is behind its own kill switch. Tests stay targeted during iteration, with the full suite once in the landing gate. Each successor follows the playbook: shadow rebuild on a copy, defaults snapshot, head fixture.

---

## 10. Owner decisions (all decided 2026-10-24; formerly open questions)

The owner, 2026-10-24: "yes to defaults for all other open questions". **None remains open.**

- **LPQ1 — population prior sources** (§3.0). Should population priors come from public datasets now (EdNet, ASSISTments, Eedi; licences to check), or wait for LearnLoop contributor data and use wide `legacy` priors until then? **Decided 2026-10-24, for LP-min:** today's fixed map as a wide `legacy` prior. Eedi (`population`) is used only after a licence and scale check (teacher spec Q17).
- **LPQ2 — dependency on AD23.** **Settled by LP-min's design (2026-10-24).** LP-min reuses AD §5.6's filter code, factored into a neutral module once AD23 lands. LP-min (b) ships with the teacher's TE1, which already waits for AD23.
- **LPQ3 — utilities.** **Decided 2026-10-24: deferred** with LP5.
- **LPQ4 — the teaching shift** (§4.2). **Superseded (2026-10-24).** The predicted level after a lesson is AD's `lesson` opportunity kind (teacher spec §14.2, Q5). Liquid drift is dropped, and lesson exposure is an input to liquid stability (§4.6).
- **LPQ5 — LP6.** **Decided 2026-10-24: dropped.** The LLM readout over state plus retrieved episodes is the stand-in.
- **LPQ7 — reading-trace priors** (§3.0a). Do you accept the shape?
  - Inferred claims for unseen topics; candidate couplings from reading navigation; item difficulty stays content-only.
  - Text and discrete events only, with no dwell or scroll unless A12 is also amended.
  - Scored as a forecaster before it touches priors.

  This amends AD R13, which is recorded in the AD spec at the AD23 landing.

  **Decided 2026-10-24: measure-only.** A `llm_v3+reading` outside forecaster scored on first attempts. No inferred claims and no amendment to R13, R7 or A12 for now.
- **LPQ8 — cold-start claim fixes** (§3.0b item 1). Land the four claim-defect fixes as their own small successor now, ahead of AD23? They are independent of it. **Decided 2026-10-24: yes, as LP-min (a).** They land right after AD23, as the review recommended.
- **LPQ9 — claim feedback** (§3.0b item 7). Is per-review "you marked this as known" feedback acceptable under the frictionless rule? It is not a trait label. **Decided 2026-10-24 (default): yes.** One quiet line on the review that resolves a claimed scope, with no score or trait label. It ships with the claim fixes (LP-min (a)). *Built 2026-10-25 (Codex review F6):* `placement.claim_check` reads the placement ledger after grading; `get_feedback` carries `claimCheck` ("You marked this as known; this check: passed/missed.") on the one review that resolved an "I know this" or "too easy" assumption, and the feedback screen shows it as a quiet line. It is under the same successor and kill switch, never an input to grading or mastery.
- **LPQ6 — retire list.** Can the 19 shaping weights be retired outright once sensor mode is live, or should they be kept as the H0/H1 baseline indefinitely? **Decided 2026-10-24 (default):** keep them as the baseline, never as the served policy once a sensor arm wins. The work is deferred with sensor mode, to the router spec.
- **LPQ10 — the confidence term's data.** **Decided 2026-10-24 (default):** the tap terms stay at their priors until the taps vary, with no prompting to tap differently. Asking would bias the taps. The hedge read may give spread sooner.
- **LPQ11 — liquid stability's keep margin.** **Decided 2026-10-24: there is no margin.** The prior width of `w` is a grid posterior (§4.6), and there is no review-count threshold.
