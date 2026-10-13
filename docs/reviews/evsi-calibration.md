# EVSI calibration: measuring what value of information runs on

Stage `evsi-calibration`, branch `evsi/calibration` (base `57d31c63`).
Owner question (2026-10-12): *is there any way we could better calibrate the
EVSI instead of just having it run based off of uncalibrated baseless
assumptions?* Value of information is about to become the only limit on probes
and follow-ups (the four count caps are being lifted onto it), so this stage
measures what it can, labels what it cannot, and instruments the live
decisions so the rest gets measured from the owner's own data.

## Addendum (2026-10-13): rerun without the count bound

Every episode below ran under `PolicySettings.safety_bound = 25`, a bound
the multi-family review found binding there (its F4). The study was rerun
without it, with the same seeds and the stored fit:
[`evsi-single-family-unbounded.md`](evsi-single-family-unbounded.md),
report in `fixtures-local/evsi-calibration-v3-unbounded/`.

* **What the bound stopped:** 2 of 400 episodes, both `eig_no_gate` at
  Eedi's fitted strength (learners 42 and 206; unbounded they stop at 26 and
  34 checks, with the same wrong action).
* **Everything else is identical:** every other arm in every cell
  reproduces number for number. No number moved beyond its CI, and no
  conclusion, recommendation (§5, §9) or ranking of the arms changes.
* **Superseded numbers** (struck through and marked † in place): the
  `eedi_fitted` `eig_no_gate` rows of §4.1 and §4.2, and the `eig_no_gate`
  column of §4.3's Eedi rows.
  * Minutes per episode: 8.44 → **8.46** [7.89, 9.07] at repair 3, 12.39 →
    12.41 at 10, 23.69 → 23.71 at 30.
  * Checks: 6.74 → 6.77.
  * Value stops: 317 → 319.
  * Log loss: 1.212 → 1.213.
  * Predicted EIG: 0.069 → 0.068.
  * Realized gain CI: [0.063, 0.085] → [0.063, 0.084].

The study now runs unbounded by default; `learnloop evsi simulate
--safety-bound 25` reproduces this file's run, and `learnloop evsi compare`
lines two reports up.

## Summary

Revised after the Codex review
([`evsi-calibration-codex-review.md`](evsi-calibration-codex-review.md)): the
study was rerun with each response world's own pre-episode histories (F2) and
with an `incumbent` arm that includes today's robust completion gate (F8); the
old `caps` arm is kept as `caps_only`, a simplified comparator. The live
report's truth, follow-up and staged joins and Part C's missing-time handling
were corrected (F1, F3–F7).

1. **The hand-set response model is badly overconfident, and it is what EIG and
   EVSI run on.** Fitted to 15.9M real Eedi answers, a learner who holds a
   misconception picks the distractor that diagnoses it **41%** of the time
   (95% CI 40–43%), not the **83%** today's contrast card implies (80% in
   `probe.irt.err_low_frac`, 60% in the bridge default). Learners who know the
   material slip **12%** of the time, not 3–5%. In the simulation, the checks
   today's incumbent policy chooses under the hand-set vocabulary are forecast
   to be worth 0.38 minutes and 0.33 nats each; they realize **−0.02 minutes
   and −0.06 nats** about the truth: on average they move belief *away* from
   it. Under the Eedi-fitted model the same forecasts are calibrated (expected
   calibration error 0.01, predicted EIG 0.110 nats vs 0.103 realized about the
   truth).
2. **At Eedi's measured signal strength, one more multiple-choice check is
   almost never worth a minute.** Every value-based rule stops after the error
   that opened the episode. Today's incumbent (the probe-episode caps plus the
   mvp-0.8 robust completion gate, which ends 74% of episodes as soon as the
   minimum two checks are in) spends 2.0 checks per episode for a marginally better
   outcome (right repair 44% vs 40%): **3.77 vs 1.81 minutes per episode**
   (repair 3 min). This holds at repair costs of 10 and 30 minutes too (7.98 vs
   6.03, 20.03 vs 18.08).
3. **When checks *are* valuable, EVSI as built under-probes, and so does
   today's robust completion gate.** With a strong instrument (consistency 0.9)
   and 30-minute repairs, today's `rank_feasible` costs **17.9 minutes per
   episode vs 13.3 for the incumbent** (and 9.6 for the same caps without the
   gate): it abstains whenever any ensemble member or the ±0.15 stress changes
   the action after *any* answer (even an improbable one), and its one-step
   value misses checks that only pay off in pairs. Ignoring the flip abstention
   (12.5) and valuing the best 2–3 checks jointly (10.8, 2.6 below the
   incumbent) close most of that gap; the lookahead is the best rule at
   moderate value (4.99 vs incumbent 5.82 and caps-only 5.13 at repair 10;
   means, per-policy CIs in §4.3). The incumbent's gate (the EIG path's 90%
   agreement abstention) costs 3.7 minutes per episode at 0.9/30 against the
   same caps without it (95% CIs 11.7–15.0 vs 8.1–11.3). **Lifting the caps onto today's
   EVSI would stop diagnosis exactly where it matters.**
4. **The EIG path's `VALUE_PER_NAT_MINUTES = 60` is 4–500× too high**
   (measured: about 0.4–0.5 × the repair minutes per nat at consistency 0.9,
   0.04 × at Eedi's), and its 90% agreement gate abstains in 89% of episodes,
   so the gate, not value, is what stops it.
5. **The robustness knobs barely matter; the stakes and the model do.**
   `PERTURBATION_DELTA`, `INSTRUMENT_PERTURBATION_CONCENTRATION`,
   `ROBUST_DRAW_COUNT` and `BURDEN_COST` change rankings but not minutes
   (all paired 95% CIs include 0, or a positive burden only hurts). Knowing the
   true repair minutes is worth 0.7–1.1 minutes per episode. The 10th-percentile
   ensemble member under-predicts realized value in every regime with value; a
   quantile of 0.25 or higher matches it better (minutes effect within noise).
6. **Part B is live (logging only):** every value-of-information decision now
   writes a `voi_forecasts` receipt, and `learnloop evsi calibration` scores
   them against realized answers and later independent diagnostic truth.
   **Part C is built and off:** the cost of leaving a misconception unresolved,
   measured from the owner's recurrence history and shrunk toward an Eedi
   prior; in simulation charging it pays off once it reaches about 3.6 minutes.

No paid calls. No serving default changed.

## 1. What is hand-set today (verified in code)

| Number or rule | Where | Value | Role | Provenance today |
|---|---|---|---|---|
| Loss `L(h,a) = minutes(a) + minutes(e)` | `scheduling/action_loss.py` | structural | EVSI's loss; ignores what an unresolved misconception costs later | structural assumption |
| `DEFAULT_INTERVENTION_MINUTES` | `action_loss` | 3.0 | repair minutes when no logged duration exists | heuristic |
| repair-class `expected_minutes` | causal selector | model self-report | repair minutes in the causal shadow | `authored_prior` (cells mislabel it `logged_attempt_durations`, see §7) |
| probe burden default | `causal_diagnostic_selector` | 1.5 min (was an inline `or 1.5`) | check cost when the live receipt has none | heuristic (now `DEFAULT_PROBE_BURDEN_MINUTES`) |
| `PERTURBATION_DELTA` | `scheduling/evsi.py` | 0.15 | ±per-row stress; a winner/action flip abstains | heuristic |
| `ROBUST_QUANTILE` | `diagnosis/robust_composition.py` | 0.10 | the LCB used to rank and stop | heuristic |
| `LAMBDA_TIME` | `robust_composition` | 1.0 | minutes numeraire | structural |
| `BURDEN_COST` | `robust_composition` | 0.0 | global stop margin (dormant) | heuristic |
| `VALUE_PER_NAT_MINUTES` | `robust_composition` | 60 | the EIG path's nats → minutes | heuristic |
| `ROBUST_DRAW_COUNT` | `robust_composition` | 128 | ensemble size | heuristic |
| `INSTRUMENT_PERTURBATION_CONCENTRATION` | `robust_composition` | 40 | how far ensemble members move instrument rows | heuristic |
| `ENSEMBLE_ACTION_AGREEMENT_THRESHOLD` | `robust_composition` | 0.90 | EIG path abstains below this agreement | heuristic |
| Flip abstention | `evsi.rank_feasible` | rule | abstain if any member/stress changes the action after any emission | design rule |
| One-step (myopic) EVSI | `evsi.rank_feasible` | rule | values one check at a time | design rule |
| `ORDINAL_VOCABULARY` | `diagnosis/probe_families.py` | dominant .60, likely .25, occasional .10, rare .04, negligible .01 | every card's `P(outcome \| hypothesis)` | authored, "never fitted" |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` | `probe_families` | 8 | weight of the vocabulary against observed counts | heuristic |
| `GRADER_CHANNEL_RELIABILITY` | `probe_families` | 0.9 (legacy) | point grader channel | heuristic |
| `probe.irt.*` | config | θ_mastered 2, θ_unfamiliar −2, cuts ±1, `unfamiliar_error_leak` 0.20, `err_low_frac` 0.80, `err_mid_frac` 0.50 | facet response model (follow-ups, predictive EIG) | heuristic |
| `_BRIDGE_SENSITIVITY` / `_SPECIFICITY` | `diagnosis/probes.py` | 0.6 / 0.9 | a rubric-linked misconception's fire channel | heuristic |
| `probe.episode.*` stops and caps | config | max 4 observations, session cap 4, min 2 independent, stop at 0.85 with ambiguity 0.30, action-equivalence 0.10, open-set prior 0.10 | when a probe episode stops | heuristic |
| follow-up ranking | config | `predictive_eig_weight` 0.0, `kappa_uncertain` 2.0, 1 intervention per LO per session | follow-up choice and cap | heuristic |
| selection extras | config | `selection_overhead_seconds` 10, `family_redundancy_penalty` 0.6, predictive target cap 6 / minimum 2 | probe ranking | heuristic |

The stage added to this list (all registered in `params/parameter_registry.py`,
all labelled on receipts): `unresolved_cost.EEDI_EXCESS_REPEAT_RATE` (Eedi
population prior), `ENCOUNTERS_UNTIL_CAUGHT`, `CENSOR_DAYS`,
`MIN_TIMED_ATTEMPTS`, `LATENCY_CAP_MINUTES` (heuristics) and the config leaf
`evsi.unresolved_cost_prior_pseudo_count`.

## 2. Data

* **Eedi 2024** ("Mining Misconceptions in Mathematics", Kaggle; the owner's
  download, read from the main checkout's `fixtures-local/eedi-2024`, not
  modified): 1,869 four-option questions in 163 subjects, 1,604
  misconceptions labelled on distractors (2,587 in the mapping). No responses.
* **Eedi NeurIPS 2020** (public challenge archive,
  `https://dqanonymousdata.blob.core.windows.net/neurips-public/data.zip`,
  657 MB, MD5 matched the server's `Content-MD5`): task 1/2, 15,867,850 answers
  by 118,971 students to 27,613 questions, with the chosen option and the
  answer time. No misconception labels. Extracted (no images) into the
  worktree's `fixtures-local/eedi-neurips-2020/`; no licence file in the
  archive, the challenge guide (arXiv:2007.12061) governs; used locally, never
  committed. Only aggregates leave the machine (this file, the registry
  constant).
* **Join:** the two releases share Eedi's subject taxonomy (`SubjectId` 33 is
  "BIDMAS" in both); 162 of the 163 2024 subjects are 2020 level-3 subjects.
* **Simulation bank:** 110 subjects with at least 6 questions and at least two
  misconceptions labelled on two or more questions (mean 6.3 hypotheses, 15.5
  questions); 61 use their own subject's fit, 49 the pooled one.

## 3. The response model fitted to Eedi

**Method** (`evsi_calibration/response_fit.py`). 2020 has answers but no
labels, so misconceptions are found: within a subject, two distractors the
*same* students pick together far more than chance (co-selection lift ≥ 2)
are taken to diagnose one misconception; three questions whose designated
distractors are pairwise linked form a **misconception triple**. On each
triple a three-class latent class model (knows / holds / unsure) over the three
answers (correct, designated, other) is identified and fitted by EM. Even
`UserId`s select the triples, odd ones fit them, so high-lift selection does
not inflate the fit. On synthetic data with a planted consistency of 0.65 the
fit recovers 0.63–0.69 at 3,000 students per triple (tests:
`tests/test_evsi_calibration_sim.py`). Result: **370 triples in 102 subjects**
(median 372 fit students per triple, median lift 2.47).

| Quantity | Eedi 2020, median of 370 triples [95% CI] | What live code assumes |
|---|---|---|
| Consistency: P(designated distractor \| holds the misconception) | **0.41** [0.40, 0.43] | 0.83 (contrast card "dominant", normalized); 0.80 `err_low_frac`; 0.60 bridge |
| Holder answers correctly | 0.24 [0.22, 0.25] | 0.11 (card) |
| False alarm: P(designated \| unsure) | **0.13** [0.13, 0.14] | 0.28 (card `other_or_unknown`); 0.20 `unfamiliar_error_leak`; 0.10 bridge |
| Unsure answers correctly | 0.35 [0.33, 0.36] (4 options: guessing floor 0.25) | 0.16 (card); 0.05 (IRT θ_unfamiliar) |
| Knower slip: P(wrong \| knows) | **0.12** [0.11, 0.13] | 0.03 (card); 0.05 (IRT θ_mastered) |
| Knower picks the designated distractor | 0.026 [0.024, 0.028] | 0.014 (card) |
| Prevalence: knows / holds this misconception / unsure | 0.61 / 0.11 / 0.26 | open-set prior 0.10 |
| Between-question spread of consistency (Beta concentration κ) | **≈ 3.7** (approximate, sampling noise removed by moments) | 40 (`INSTRUMENT_PERTURBATION_CONCENTRATION`) |
| Repeat rate after a designated error, per later encounter | 0.22 [0.20, 0.23] vs 0.06 after a correct first answer | — |
| **Excess repeat-error rate** (Part C prior) | **0.151** [0.138, 0.162] per encounter | not modelled |

Caveats inside Eedi: a triple whose distractors target related but different
misconceptions pulls consistency down, a "holds" class mixing partial holders
also pulls it down, and per-triple estimates are noisy (the pooled median is
not). Read 0.41 as "well under one half", not as a precise constant.

## 4. The simulation (Part A)

`learnloop evsi simulate` (`src/learnloop/evsi_calibration/`):

* **A learner** draws a true hypothesis (`knows`, one of the subject's
  misconceptions, or `other`) from the fitted prevalences, then answers Eedi
  questions of that subject under the fitted response model, with each
  question's consistency drawn around the subject mean (κ = 3.7). The episode
  opens at the first wrong answer (as a live episode opens after an error); the
  system's belief starts from **everything it saw** (3.05 answers on average,
  the correct ones included). 400 flagged learners per world: 160 know it, 159
  hold a labelled misconception, 81 something else.
* **Each response world draws its own histories.** A stronger instrument
  (§4.3–4.5) changes how learners answered before the episode too, so each
  world draws its learners with the same per-learner seeds (common truths,
  subjects, question orders and uniforms) and shares them across its policies.
  Holders' mean starting probability on their true misconception is 0.128 at
  Eedi's consistency, 0.152 at 0.7 and 0.194 at 0.9 (it would be 0.125 at 0.9
  had the fitted world's histories been reused, the Codex review's F2).
* **The system** believes either `hand_set` (today's contrast-card rows read
  from `probe_families`, mapped onto four options) or `eedi_fitted` (the
  subject means, without knowing each question's own consistency).
* **The real selectors** choose: `evsi` is `scheduling.evsi.rank_feasible`;
  `eig` is `robust_composition.evaluate_selection`, both over ensembles built by
  `robust_composition.build_ensemble` with an identity grading channel (a
  multiple-choice answer is read exactly). Baselines: **`incumbent`** (today's
  serving probe episode: the highest hypothesis-EIG question, stopped as
  `probe_episodes._evaluate_completion` stops it, in its order, including the
  mvp-0.8 robust completion gate that ends an unstable episode after the
  minimum observations when the robust selector abstains; thresholds read from
  `ProbeEpisodeConfig`), `caps_only` (the same without the gate: a simplified
  comparator, what a legacy unpinned episode does, not today's serving),
  `random` and `max_entropy` (cap-only rules). What-if readings of the same
  outputs: `evsi_lcb_only` (measure whenever the robust value clears the cost,
  ignoring flips), `evsi_lookahead` (also value the top 2–3 checks jointly, the
  knowledge-gradient* idea) and `eig_no_gate` (ignore the agreement gate).
* **Costs:** a check 1 minute, a repair `DEFAULT_INTERVENTION_MINUTES` = 3
  (continue = 0), wrong action = the true loss table's minutes. All arms in a
  world see the same learners and the same answer to the same question (common
  random numbers), so differences are paired. Ensembles use 32 draws (live 128;
  the sweep shows no minutes effect).
* Four design defects were found and fixed. Two during the stage (the first
  full run was discarded): the starting belief conditioned on the error alone
  (biasing it against `knows`), and a stronger-instrument override left a
  holder zero probability of the other distractors (log-score blow-ups). Two in
  the Codex review: stronger worlds reused the fitted world's histories (F2),
  and the arm standing for today's caps lacked the robust completion gate (F8).
  The numbers below are from the rerun (`fixtures-local/evsi-calibration-v2/`,
  711 s on 12 workers, saved fit reused). In the fitted world only the
  incumbent rows are new: every other policy there is unchanged.

### 4.1 Forecast quality: (1) outcome calibration, (2) information, (3) action change

Fitted world, repair 3 minutes, checks pooled over each policy's episodes.

| System model | Policy | Log loss (uniform = 1.386) | ECE | Predicted EIG (nats) | Realized entropy drop | Realized gain about the truth [95% CI] | P(action change) predicted / realized | EVSI per check predicted / realized (min) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| hand_set | incumbent | 1.356 | 0.107 | 0.328 | 0.208 | **−0.058** [−0.142, 0.030] | 0.254 / 0.266 | 0.383 / **−0.022** |
| hand_set | caps_only | 1.401 | 0.107 | 0.317 | 0.209 | −0.042 [−0.113, 0.027] | 0.260 / 0.262 | 0.377 / −0.016 |
| hand_set | max_entropy | 1.303 | 0.069 | 0.156 | 0.117 | 0.039 [−0.012, 0.086] | 0.116 / 0.120 | 0.113 / 0.049 |
| hand_set | evsi_lcb_only | 1.683 | 0.139 | 0.584 | 0.378 | −0.276 [−0.703, 0.136] | 0.625 / 0.526 | 1.432 / **−0.553** |
| eedi_fitted | incumbent | 1.109 | **0.013** | 0.110 | 0.105 | **0.103** [0.071, 0.133] | 0.058 / 0.061 | 0.024 / 0.000 |
| eedi_fitted | caps_only | 1.162 | 0.011 | 0.097 | 0.096 | 0.097 [0.077, 0.119] | 0.070 / 0.064 | 0.027 / 0.004 |
| eedi_fitted | max_entropy | 1.176 | 0.010 | 0.088 | 0.096 | 0.092 [0.072, 0.109] | 0.053 / 0.058 | 0.017 / 0.013 |
| eedi_fitted | eig_no_gate | ~~1.212~~ 1.213† | 0.003 | ~~0.069~~ 0.068† | 0.073 | 0.073 ~~[0.063, 0.085]~~ [0.063, 0.084]† | 0.067 / 0.067 | 0.023 / 0.017 |

† Superseded by the unbounded rerun (addendum, 2026-10-13).

Reliability of the answer forecasts (incumbent): under `hand_set`, answers
given 0.7–0.8 happen 28% of the time and answers given 0.0–0.1 happen 11%;
under `eedi_fitted` every decile with 100 or more answers is within 0.07 of its
rate. By predicted EIG quintile, the hand-set model's most "informative" checks
(0.62 nats predicted) move belief 0.18 nats *away* from the truth; the fitted
model's quintiles track it (top quintile 0.20 predicted, 0.18 entropy drop,
0.12 about the truth). The action-change forecast is the one thing the
hand-set model gets roughly right on average (0.25 vs 0.27), but not by bin
(0.85 predicted → 0.58 realized).

### 4.2 (4) Checks, minutes, identification, waste

Fitted world, repair 3 minutes. Total = check minutes + the true loss of the
action taken; wasted = checks after the last change of action + wrong-action
minutes.

| System | Policy | Checks | Total minutes [95% CI] | Right action | Misconception identified | Wasted minutes | Main stop |
|---|---|---:|---:|---:|---:|---:|---|
| eedi_fitted | **incumbent** | 1.96 | 3.77 [3.59, 3.92] | 0.44 | 0.15 | 3.59 | can't reliably distinguish 296, decision stable 78 |
| eedi_fitted | caps_only | 3.38 | 5.18 [4.97, 5.45] | 0.46 | 0.23 | 4.78 | budget exhausted 266, decision stable 97 |
| eedi_fitted | random | 3.38 | 5.17 [4.93, 5.39] | 0.45 | 0.17 | 4.79 | budget 260 |
| eedi_fitted | max_entropy | 3.36 | 5.12 [4.87, 5.36] | 0.47 | 0.16 | 4.72 | budget 259 |
| eedi_fitted | eig | 0.01 | 1.82 [1.70, 1.95] | 0.40 | 0.03 | 1.82 | abstain (agreement gate) 354 |
| eedi_fitted | eig_no_gate | ~~6.74~~ 6.77† | ~~8.44 [7.88, 9.02]~~ 8.46 [7.89, 9.07]† | 0.53 | 0.31 | ~~6.96~~ 6.99† | value stop ~~317~~ 319† |
| eedi_fitted | evsi | 0.00 | 1.81 [1.67, 1.96] | 0.40 | 0.03 | 1.81 | LCB below cost 396 |
| eedi_fitted | evsi_lookahead | 0.00 | 1.81 [1.67, 1.95] | 0.40 | 0.03 | 1.81 | LCB below cost 396 |
| hand_set | **incumbent** | 2.05 | 4.17 [3.96, 4.45] | 0.50 | 0.20 | 3.48 | can't reliably distinguish 193, decision stable 178 |
| hand_set | caps_only | 2.84 | 4.96 [4.64, 5.28] | 0.55 | 0.23 | 3.79 | decision stable 224 |
| hand_set | evsi | 0.01 | 2.09 [1.93, 2.26] | 0.40 | 0.05 | 2.09 | LCB below cost 368, flip abstain 28 |
| hand_set | evsi_lcb_only | 0.10 | 2.23 [2.02, 2.42] | 0.41 | 0.06 | 2.17 | LCB below cost 396 |

† Superseded by the unbounded rerun (addendum, 2026-10-13).

With Eedi's signal, today's two checks lift the right-action rate from 0.40 to
0.44 and identify the exact misconception 15% of the time (four checks without
the gate: 0.46 and 23%); neither is worth its minutes when a wrong repair costs
3–6.

### 4.3 Regimes: instrument strength × stakes

Mean total minutes per episode (checks; right-action rate), `eedi_fitted`
system. "Consistency" overrides the holder's designated-distractor rate for
truth and model alike (the other answers keep their fitted ratio), and each
world runs on its own histories.

| Consistency | Repair min | **incumbent** | caps_only | eig (as built) | eig_no_gate | **evsi (as built)** | evsi_lcb_only | evsi_lookahead |
|---|---:|---|---|---|---|---|---|---|
| Eedi 0.41 | 3 | 3.77 (2.0; .44) | 5.18 (3.4; .46) | 1.82 (0.0; .40) | ~~8.44 (6.7; .53)~~ 8.46 (6.8; .53)† | **1.81** (0.0; .40) | 1.81 | 1.81 |
| Eedi 0.41 | 10 | 7.98 (2.0; .44) | 9.36 (3.4; .46) | 6.04 | ~~12.39~~ 12.41† | 6.03 (0.0) | **6.00** | **6.00** |
| Eedi 0.41 | 30 | 20.03 (2.0; .44) | 21.31 (3.4; .46) | 18.09 | ~~23.69~~ 23.71† | 18.08 (0.0) | 18.06 | **18.02** (0.1) |
| 0.7 | 3 | 3.53 (2.0; .58) | 4.53 (3.2; .67) | 1.90 | 6.54 | **1.80** (0.0) | 1.80 | 1.80 |
| 0.7 | 10 | 7.05 (2.0; .58) | 7.53 (3.2; .67) | 6.01 | 8.85 | 6.04 (0.0) | **5.96** (0.2) | 6.02 (0.2) |
| 0.7 | 30 | 17.10 (2.0; .58) | 16.07 (3.2; .67) | 17.76 | **15.45** (5.5; .77) | 18.17 (0.0; .41) | 17.11 (0.4; .49) | 16.25 (0.7; .53) |
| 0.9 | 3 | 3.20 (2.1; .72) | 3.56 (2.9; .84) | 1.91 | 4.99 | **1.79** (0.0) | 1.81 | 1.81 |
| 0.9 | 10 | 5.82 (2.1; .72) | 5.13 (2.9; .84) | 5.76 | 6.18 | 5.99 (0.0; .43) | 5.29 (0.4; .55) | **4.99** (0.6; .60) |
| 0.9 | 30 | 13.32 (2.1; .72) | 9.63 (2.9; .84) | 16.76 | **9.58** (4.5; .90) | 17.94 (0.0; .43) | 12.52 (0.9; .65) | 10.76 (1.7; .77) |

Per-policy 95% CIs at 0.9/30: incumbent [11.65, 15.05], caps_only [8.14,
11.28], evsi [16.44, 19.36], evsi_lcb_only [11.11, 14.02], evsi_lookahead
[9.09, 12.59], eig_no_gate [7.77, 11.17]. † Superseded by the unbounded
rerun (addendum, 2026-10-13); every other cell is unchanged.

Where checks are weak or cheap to skip, every value rule beats the incumbent
by 1.1–2.0 minutes per episode (and the cap-only comparator by 1.6–3.4). Where
they are strong and the stakes high, `evsi` as built is the worst rule (+4.6
minutes vs the incumbent, +8.3 vs caps-only at 0.9/30): ignoring the flip
abstention recovers 5.4 of those minutes, valuing 2–3 checks jointly another
1.8, and 1.1–1.2 remain against caps-only and `eig_no_gate`. Today's robust
completion gate stops too early in exactly that regime: the incumbent's 13.3
minutes against 9.6 for the same caps without it (the gate ends 190 of 400
episodes at 0.9 and 296 at Eedi's consistency). No rule beats a well-placed
cap everywhere; the lookahead is never far from the best, and is the best at
0.9/10.

### 4.4 (5) Sensitivity to each hand-set number

Regime where measuring matters (consistency 0.9, true repair 10 min, true
check 1 min; 300 learners, the 0.9 world's own histories). Each row moves
**what the system assumes**; the world stays fixed. Mean total minutes
(checks; Kendall τ of the first decision's ranking vs the current value;
paired Δ vs current [95% CI]).

| Parameter | Value | evsi (as built) | evsi_lcb_only | evsi_lookahead |
|---|---|---|---|---|
| `PERTURBATION_DELTA` | 0.05 … 0.35 (current 0.15) | 6.15–6.18, Δ ≤ 0.03 | identical (delta only feeds abstention) | identical |
| `ROBUST_QUANTILE` | 0.05 | 6.21 (τ .85) | 5.61, Δ +0.14 [−0.09, 0.39] | 5.19, Δ +0.06 [−0.21, 0.32] |
| | **0.10 (current)** | 6.18 | 5.47 | 5.13 |
| | 0.25 | 6.17 (τ .79) | 5.37, Δ −0.10 [−0.30, 0.12] | 4.97, Δ −0.15 [−0.38, 0.08] |
| | 0.50 | 6.18 (τ .63) | 5.23, Δ −0.24 [−0.50, 0.06] | 4.82, Δ −0.30 [−0.63, 0.04] |
| `INSTRUMENT_PERTURBATION_CONCENTRATION` | 4 (≈ Eedi κ) | 6.17 (τ .56) | 5.65, Δ +0.18 [−0.13, 0.48] | 4.94, Δ −0.18 [−0.62, 0.25] |
| | 10 | 6.17 (τ .71) | 5.71, Δ +0.24 [−0.05, 0.56] | 5.08, Δ −0.04 [−0.39, 0.29] |
| | **40 (current)** | 6.18 | 5.47 | 5.13 |
| | 160 | 6.20 (τ .78) | 5.53, Δ +0.06 [−0.17, 0.35] | 5.22, Δ +0.09 [−0.15, 0.36] |
| Ensemble draws | 16 / **32** / 64 / 128 | 6.22 / 6.18 / 6.18 / 6.17 (τ .85–.89) | 5.57 / 5.47 / 5.57 / 5.65 | 5.23 / 5.13 / 5.16 / 5.27 (all Δ CIs include 0) |
| `BURDEN_COST` | **0 (current)** / 0.5 / 1 / 2 | ≈ 6.18 | 5.47 / 5.77 / 5.94 / 6.00 (Δ +0.30 [0.05, 0.53] at 0.5) | 5.13 / 5.44 / 5.64 / 5.92 (Δ +0.51 [0.22, 0.83] at 1) |
| Assumed repair minutes (`DEFAULT_INTERVENTION_MINUTES`; truth 10) | 1.5 | 6.17 | 6.17, Δ −0.02 | 6.17, Δ −0.02 |
| | **3 (current default)** | 6.17 | 6.18 | 6.18 |
| | 6 | 6.18 | 5.87, Δ −0.31 [−0.60, 0.03] | 5.75, Δ −0.43 [−0.76, −0.03] |
| | 10 (the truth) | 6.18 | **5.47, Δ −0.71 [−1.10, −0.29]** | **5.13, Δ −1.06 [−1.47, −0.58]** |
| | 20 | 6.18 | 5.17, Δ −1.01 [−1.48, −0.48] | 4.95, Δ −1.24 [−1.77, −0.64] |
| Assumed check minutes (truth 1) | 0.5 | 6.18 | 5.17, Δ −0.30 [−0.56, −0.04] | 4.95, Δ −0.18 [−0.53, 0.16] |
| | **1 (the truth)** | 6.18 | 5.47 | 5.13 |
| | 1.5 (causal default) | 6.18 | 5.77, Δ +0.30 [0.05, 0.53] | 5.57, Δ +0.44 [0.20, 0.71] |
| | 3 | 6.17 | 6.00, Δ +0.53 [0.13, 0.86] | 6.00, Δ +0.87 [0.42, 1.27] |

Over-stating the repair (20 minutes) or under-stating the check (0.5) beats the
truth: both push an under-probing rule toward measuring more, which is the
myopia of §4.3 showing through, not a reason to mis-state costs.

`VALUE_PER_NAT_MINUTES` (EIG path, same regime): with the agreement gate the
EIG path barely measures whatever the value (5.97–6.17 minutes, Δ ≤ 0.19).
Without the gate:

| `VALUE_PER_NAT_MINUTES` | 1 | 2.5 | 5 | **10** | 20 | 40 | **60 (current)** | 120 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| eig_no_gate total minutes (checks) | 6.17 (0.0) | 5.90 (0.3) | 5.10 (1.7) | **4.75 (2.8)** | 5.52 (3.6) | 6.28 (4.4) | 6.64 (4.7) | 7.32 (5.5) |
| Δ vs current [95% CI] | −0.48 [−1.38, 0.27] | −0.74 [−1.62, 0.07] | −1.54 [−2.21, −0.83] | **−1.89 [−2.26, −1.52]** | −1.12 [−1.32, −0.97] | −0.36 [−0.48, −0.27] | 0 | +0.68 [0.55, 0.83] |

Realized minutes per nat (regression of a check's realized value on its
predicted EIG, calibrated model; on the incumbent's checks / on caps-only's):
−0.01 [−0.39, 0.40] / 0.12 at Eedi/3 min, 1.22 [0.90, 1.59] /
1.53 at 0.9/3, **4.06 [2.88, 5.20] / 5.10 [4.17, 5.91] at 0.9/10**, 12.19
[8.95, 15.72] / 15.31 at 0.9/30. The minutes a nat is worth scale with the
stakes (≈ 0.4–0.5 × repair minutes at consistency 0.9, ≈ 0.04 × at Eedi's); no
single constant fits.

Robust quantile against realized value (calibrated model): the 10th-percentile
member under-predicts the realized value in every regime with value (by
0.04–0.55 minutes on the incumbent's checks, 0.05–1.22 on caps-only's). On the
incumbent's checks the 25th percentile is within 0.01–0.14 minutes below
realized and the 50th over-predicts (by 0.03–0.30); on caps-only's later checks
the 50th is the closer one at 0.9 (0.03–0.27 below). Realized value sits
between the members' 25th and 50th percentiles; 0.10 is too conservative
everywhere.

### 4.5 Part C in simulation: charging the unresolved cost

True `U` = Eedi excess repeat rate 0.151 × encounters × 2 minutes per repeated
error. "Measured" = the system's loss charges the true `U`; "minutes-only" =
today's loss. Paired Δ = measured − minutes-only, minutes per episode; each
world's own histories.

| Consistency | Encounters | True U | evsi_lcb_only: Δ [95% CI] (checks) | evsi_lookahead: Δ [95% CI] (checks) |
|---|---:|---:|---|---|
| Eedi 0.41 | 3 | 0.91 | +0.03 [−0.03, 0.10] (0 → 0) | same |
| Eedi 0.41 | 6 | 1.81 | +0.08 [−0.01, 0.18] (0 → 0) | same |
| Eedi 0.41 | 12 | 3.63 | −0.07 [−0.28, 0.16] (0 → 0) | same |
| Eedi 0.41 | 24 | 7.25 | −0.27 [−0.71, 0.18] (0 → 0.02) | same |
| 0.9 | 3 | 0.91 | −0.05 [−0.15, 0.05] (0.05 → 0.16) | −0.05 [−0.15, 0.05] |
| 0.9 | 6 | 1.81 | −0.09 [−0.25, 0.07] (0.05 → 0.23) | −0.10 [−0.27, 0.06] (→ 0.25) |
| 0.9 | 12 | 3.63 | **−0.54 [−0.89, −0.26]** (0.05 → 0.44) | **−0.56 [−0.93, −0.26]** (→ 0.49) |
| 0.9 | 24 | 7.25 | **−1.53 [−2.10, −1.09]** (0.05 → 0.89) | **−1.47 [−1.99, −1.04]** (→ 1.00) |

Charging the true cost pays off once it is large next to a repair and a check
(clearly from about 3.6 minutes); below that no difference is distinguishable
from zero. So the measured loss is worth having exactly when the owner's
history says misconceptions linger, and costs nothing measurable when they do
not.

## 5. Recommended values

Confidence: **high** = measured with tight CIs and the decision effect is
clear; **medium** = measured, transfer uncertain; **low** = direction only.

| Parameter | Current | Recommended | Evidence | Confidence |
|---|---|---|---|---|
| Card vocabulary as a likelihood (`ORDINAL_VOCABULARY`, default rows) | "dominant" ≈ 0.83 consistency, slip ≈ 0.03 | Keep as a **prior only**, and let real counts take over fast: lower `DEFAULT_CONDITIONAL_PSEUDO_COUNT` from 8 to ≈ 2 so a family's own observations dominate after a handful | §3, §4.1: the vocabulary is 2× overconfident in consistency, 4× in slip; its checks lose information about the truth | high (direction), low (the value 2: count updating was not simulated) |
| `probe.irt.err_low_frac` / `unfamiliar_error_leak` / bridge sensitivity–specificity | 0.80 / 0.20 / 0.6–0.9 | For multiple-choice-like items: 0.41 / 0.13 / 0.41–0.87 (Eedi). For free text: unchanged until the owner's calibration counts exist (§6) | §3 | high for MCQ, low for transfer |
| `PERTURBATION_DELTA` | 0.15 | **0.10** (the measured per-row error of a calibrated model: p90 0.098; hand-set rows are off by 0.52 at p90, which no delta can cover) | §4.4: no minutes effect at any value while flips abstain on members | medium (value), high (no decision effect) |
| `ROBUST_QUANTILE` | 0.10 | **0.25** (0.5 would match some checks better; 0.25 keeps a margin) | §4.4: the 10th percentile under-predicts realized value in every regime with value; realized sits between the 25th and 50th; minutes Δ at 0.25: −0.10 [−0.30, 0.12] / −0.15 [−0.38, 0.08] | low–medium (direction consistent, minutes within noise) |
| `INSTRUMENT_PERTURBATION_CONCENTRATION` | 40 | keep 40; note Eedi's between-question κ ≈ 3.7 | rankings move (τ 0.56 at 4), minutes do not | low |
| `ROBUST_DRAW_COUNT` | 128 | keep | flat; draws only add ranking noise (τ ≈ 0.85) | high |
| `BURDEN_COST` | 0 | keep 0 (dormant) | any positive value only adds minutes | high |
| `VALUE_PER_NAT_MINUTES` | 60 | **retire** for EVSI computed from the loss table on the EIG path; if a constant must stay, ≈ 0.4–0.5 × the repair minutes (≈ 1.5 at the 3-minute default, 4–5 at 10) | §4.4: 60 is 4–500× the measured minutes per nat; best in sweep 10 vs measured 4.1–5.1 at 0.9/10 | high (60 is wrong), medium (the replacement) |
| `ENSEMBLE_ACTION_AGREEMENT_THRESHOLD` (and the robust completion gate built on it) | 0.90 | do not let it stop diagnosis on its own | §4.2/§4.3: it abstained in 89% of episodes on the EIG path; as today's robust completion gate it ends 48–74% of episodes after two checks and costs 3.7 minutes per episode at 0.9/30 (incumbent 13.3 vs caps-only 9.6) | medium |
| `DEFAULT_INTERVENTION_MINUTES` | 3.0 | keep as the fallback, but measure repair durations per repair class (decision-value spec Stage 2); Eedi cannot | §4.4: knowing the true 10 minutes is worth 0.71 [0.29, 1.10] to 1.06 [0.58, 1.47] minutes per episode | high (it matters), n/a (value) |
| Causal probe burden default | 1.5 | the live receipt's measured burden; 1.5 over-states a 1-minute check | §4.4: +0.30 [0.05, 0.53] to +0.44 [0.20, 0.71] | medium |
| Flip abstention (`rank_feasible`) | any member/stress flip abstains | abstain only when the robust value fails to clear the cost, or when the flipping emissions carry real probability mass | §4.3: +5.4 minutes per episode at 0.9/30 (17.9 vs 12.5) | high (as built is wrong), medium (the replacement) |
| One-step EVSI | myopic | value the best 2–3 checks jointly when no single check clears the cost (`evsi_lookahead`) | §4.3: best rule at 0.9/10, 2.6 below the incumbent at 0.9/30 | medium |

## 6. Where Eedi does not transfer, and how personal data takes over

* **Population vs one learner.** Eedi's numbers are a population of 119k
  school students; the owner is one adult. Population values are priors.
* **Multiple choice vs free text.** A distractor choice is a weak, noisy
  signature (41%); a free-text explanation graded by a model plausibly
  separates misconceptions better, and has no 25% guessing floor. The study
  therefore shows behaviour across consistencies (0.41, 0.7, 0.9) rather than
  porting 0.41.
* **Maths only, school curriculum, teaching in between.** The repeat-error rate
  is measured under Eedi's ordinary teaching, so it is a lower bound on what an
  unrepaired misconception costs; the owner's subjects differ.
* **What takes over, and how:**
  1. **Likelihoods:** the per-family Dirichlet counts already kept
     (`record_real_observation_counts`, `item_shrinkage_pseudo_count` 25)
     replace the vocabulary as observations accrue; lowering
     `DEFAULT_CONDITIONAL_PSEUDO_COUNT` (§5) makes that happen after a handful
     of answers instead of dozens. `learnloop evsi calibration` shows whether
     the forecasts became calibrated (reliability, log loss, EIG vs realized).
  2. **The unresolved cost (Part C):** `U = (k·U_prior + n·Ū_personal)/(k+n)`,
     `k` = `evsi.unresolved_cost_prior_pseudo_count` (5) recurrence classes:
     the Eedi prior dominates until the learner has about five persistent
     misconception classes of their own, then their repeated-error minutes do.
  3. **Durations:** pooled attempt latency replaces the 3-minute default once
     20 timed attempts exist (a single break is capped at 15 minutes).

## 7. Part B: live calibration (built, on, logging only)

**Ledger.** Migration `184_voi_forecasts.sql` adds `voi_forecasts` (RECEIPT,
append-only by trigger, never re-run on rebuild; classified in
`db/table_roles.py`; written only by `db/stores/voi_forecasts.py`). Kill switch
`[evsi] forecast_logging = false`. Every write is swallowed on failure and
skipped on a read-only repository: logging can never change or break a
decision.

**Sites** (idempotent receipt key `<site>:<decision ref>`):

| Site | Where | Forecast |
|---|---|---|
| `probe_selection` | `probe_episodes.commit_presentation` and the scheduler's committed presentation | the card's grader-composed rows over the episode labels, under the selection-time posterior; EIG = the presentation's |
| `probe_robust_selection` | `_robust_completion_override` (the mvp-0.8 stop/abstain gate) | the chosen candidate's ensemble mean; robust EIG, `VALUE_PER_NAT × EIG`, the stop threshold, the agreement fraction, the verdict |
| `followup_selection` | `evaluate_intervention_followup` when a follow-up is queued | the facet response model over the primary facet's marginal; the target facet's scoring contract frozen with it (criterion → facet share read from the assessment contract's own targets, fatal errors, item and rubric hashes, the criteria's hash, the item's evidence facets) |
| `causal_shadow_selection` | `causal_diagnostic_selector.record_shadow_selection` (`rank_feasible`) | EVSI point/LCB/UCB of every candidate, the loss table, emission keys per hypothesis |
| `staged_diagnostic_selection` | `staged_policy.decide`, once the decision is persisted (`rank_feasible`) | same, for the candidate actually committed after the near-tie randomization (`forecast_of: committed`, its assignment id and propensity), keyed by the decision id; the ranking's nominal best kept apart (`nominal_best_ref`, `nominal`); stops and abstentions `forecast_of: nominal_best` |

Each forecast body is self-contained: the chosen check's mean-member
likelihood `P(e | h)`, the belief, predicted answers, EIG, the action before
and after each answer (the loss table's argmin; for probes the triage route of
the most probable label, or the label itself when a route is missing, recorded
as `action_proxy`), `P(action change)`. **Every parameter carries a provenance**
(`measured`, `population_prior`, `heuristic`, `structural`) and its fine source
(decision-value spec §4.1 vocabulary). This exposed one mislabel: the causal
loss cells call every duration override `logged_attempt_durations`, including
model-reported `authored_prior` minutes; the receipts carry the estimator's
own source instead.

**Join (read time, `learnloop evsi calibration`).** Outcome adapters in order:
R1's `router_decisions`/`router_outcomes` when the tables exist (the decision's
chosen scheduler candidate → the attempt that took it; since the merge onto
main, §15, only R1's `taken` joins: its other statuses judge the offer and
defer to the ledgers), else the ledgers:
`practice_attempts.probe_presentation_id` → `probe_observations` for probes;
for a queued follow-up, the first attempt on the item after its queue, taken
only when it answered the offer this decision's queue produced (the offer is a
slate candidate inserted as an intervention follow-up, not served by a delayed
task, and built while this decision's queue was the one the scheduler
served), with `superseded`, `answered_earlier_offer`, `not_taken`,
`unbound_attempt` and `pending` kept apart; for a staged decision, `not_administered` (stop/abstain),
`shadow_not_administered` (shadow mode composes no work) or
`no_attempt_binding` (live, no attempt receipt exists yet); else the first
later attempt on the chosen item (causal shadow, joined through its
discriminating observation). The realized answer is mapped into the
forecast's own alphabet (probe outcome label, the robust coarse emission, the
**target facet's** `bucket|error` for follow-ups, scored from the attempt's
grading evidence under the contract frozen at selection, facet map
included, the matched
hypothesis's declared emission for the causal shadow, the graded probe outcome
for a staged check); anything else is `unmapped` with its reason, never
guessed. **Truth adapters** need explicit linkage (the evidence names the
forecast's own hypothesis ids, which belong to one episode; a shared repair
class is not linkage) and independent diagnostic evidence: a cold
verification's diagnosis-support update whose cited observation resolves to
an admitted, independent `matched_single` on one of the verification's own
hypotheses and carries the authority its basis grants
(`SUPPORT_BASIS_AUTHORITY`), an admitted, independent `matched_single`
discriminating observation that is not the forecast's own answer, a later
teach-back whose diagnosis names the same cause. What a repair did
(cold-check success or failure, `repair_confirmed` /
`escalated_unrepaired`) is reported apart as `repair_effect`, one outcome per
cold verification: it neither confirms nor rules out a cause. The system's own posterior resolving a
misconception is not truth.

**Report:** per site, reliability of answer forecasts (log loss, Brier, ECE,
bins), predicted EIG vs realized entropy drop, action-change calibration, EVSI
forecasts, and for forecasts with known truth the probability placed on it and
the regret of the action taken vs the forecast's expected loss; plus Part C's
current estimate (read-only). The successor that moves the four caps onto
value of information reads these sites (and adds its own to `VOI_SITES`).

Backup-copy check: the committed snapshots of `linear_algebra`, `probability`
and `arxiv_v2` (backup-API copies under the worktree's
`fixtures-local/evsi-copies/`) have no probe observations and 0–3 causal
hypotheses, so there is no live forecast or history to score yet; the owner's
live vaults (not read) will fill the ledger from the first decision after the
upgrade.

## 8. Part C: the loss from measurements (built, **off**)

`scheduling/unresolved_cost.py`, behind `[evsi] measured_loss_enabled = true`:

* **Personal:** each recurrence class of a persistent cause (`learner_state` or
  `unknown`; a merged Slice 2 T1 group, else the statement) is one
  misconception's history; the minutes of its attempts after the first
  (latency capped at 15 per attempt) are what it cost. A class first seen
  within 14 days with no repeat is right-censored and counted, not averaged.
  Missing time is never a measured zero: an untimed repeat is imputed from the
  learner's own pooled latency (`imputed_classes`, labelled), or, with nothing
  timed to impute from, its class is left out of the mean and the sample count
  (`unmeasurable_classes`).
* **Prior:** `0.151 × 6 encounters × minutes per repeat` (the learner's median
  attempt minutes once 20 attempts are timed, else 3.0). Six encounters is a
  labelled heuristic: Eedi does not say how often a misconception comes back.
* **Shrinkage** toward personal data with `k = 5` classes (above).
* **Use:** `build_loss_table(..., unresolved_minutes=...)` adds `U` to every
  off-diagonal cell, carried on the cell (`unresolved_minutes`,
  `unresolved_source`) and so on every EVSI receipt; transient, item-contract,
  grader and context causes get 0 (`not_a_persistent_cause`). Off, every table
  and hash is byte-identical (tested). Today only the causal **shadow** reads
  EVSI, so turning it on changes shadow receipts and forecasts, not serving.

## 9. What the owner should decide

1. **Turn on the measured loss (Part C)?** Recommended: **yes, now**: today it
   changes only the causal shadow and its receipts, so the cap-lifting
   successor starts from audited measured-loss receipts (in simulation it pays
   off from about 3.6 minutes of unresolved cost and costs nothing measurable
   below). `learnloop evsi calibration` shows the estimate first.
2. **Before the caps move onto value of information,** replace the flip
   abstention (abstain only when the robust value does not clear the cost) and
   add the 2–3 check lookahead. Recommended: yes, as part of the successor
   (a serving change, so behind its kill switch).
3. **Retire `VALUE_PER_NAT_MINUTES`** in favour of loss-derived EVSI on the EIG
   path, and stop the agreement gate from ending diagnosis alone, including
   today's robust completion gate (it costs 3.7 minutes per episode at 0.9/30
   against the same caps without it, §4.3). Recommended: yes, same successor.
4. **Lower `DEFAULT_CONDITIONAL_PSEUDO_COUNT` (8 → 2)** so cards learn from the
   owner's answers quickly. Recommended: yes (an algorithm successor: it changes
   posteriors).
5. **`ROBUST_QUANTILE` 0.10 → 0.25 and `PERTURBATION_DELTA` 0.15 → 0.10.**
   Recommended: yes with the successor. `PERTURBATION_DELTA` is read only by
   EVSI (the causal shadow, the dormant staged selector); `ROBUST_QUANTILE`
   also feeds today's robust completion gate, so it is a serving change and
   goes behind the successor's kill switch.
6. **Measure repair durations per repair class** (decision-value spec Stage 2):
   worth ≈ 0.7–1.1 minutes per diagnosed error in the simulation.

## 10. Owner commands

```bash
# Offline study (no vault, no network, no paid call). Data: Eedi 2024 from Kaggle
# (train.csv, misconception_mapping.csv); Eedi 2020 public archive extracted
# (data/train_data, data/metadata).
uv run learnloop evsi simulate --eedi-2024 fixtures-local/eedi-2024 \
  --eedi-2020 fixtures-local/eedi-neurips-2020 --output fixtures-local/evsi-calibration \
  --workers 12 --json            # ~1 min fit + ~10 min simulation; --fit <response_fit.json> skips the fit
uv run learnloop evsi simulate --eedi-2024 fixtures-local/eedi-2024 \
  --fit fixtures-local/evsi-calibration/response_fit.json --quick --json   # smoke run

# Live calibration of a vault (read-only), after `learnloop upgrade`/open applies migration 184
uv run learnloop evsi calibration --vault <vault> --json
uv run learnloop evsi calibration --vault <vault> --since 2026-10-13T00:00:00Z

# Turn on the measured loss (Part C); kill the forecast log if ever needed
#   learnloop.toml:
#   [evsi]
#   measured_loss_enabled = true
#   forecast_logging = true
```

## 11. Changes

* `src/learnloop/evsi_calibration/`: `eedi.py` (loaders, `.npz` cache),
  `response_fit.py` (triples + latent class EM + persistence),
  `world.py` (scenarios, truth, `hand_set`/`eedi_fitted` models),
  `policies.py` (real-module policies and what-ifs), `simulate.py`,
  `metrics.py`, `experiments.py` (the study), `live_report.py` (Part B report).
  A new top-level package so no frozen import cycle grows; only the CLI imports it.
* `src/learnloop/scheduling/voi_forecasts.py` (ledger writer, forecast
  arithmetic, provenance), `src/learnloop/diagnosis/voi_forecasting.py` (probe,
  robust-gate and follow-up forecasts), `src/learnloop/db/stores/voi_forecasts.py`.
* Hooks (logging only): `probe_episodes.py`, `scheduler.py`, `followups.py`,
  `causal_diagnostic_selector.py` (+ Part C wiring, `vault` threaded from
  `causal_orchestrator`), `staged_policy.py`.
* Part C: `scheduling/unresolved_cost.py`; `action_loss.build_loss_table`
  gains `unresolved_minutes` (byte-identical when absent).
* Config `[evsi]` (`forecast_logging`, `measured_loss_enabled`,
  `unresolved_cost_prior_pseudo_count`); all six defaults snapshots recomputed
  (they move only because the effective config gains the section).
* Registry: `unresolved_cost` in the module inventory, five constants
  registered; `probes.BRIDGE_SENSITIVITY/SPECIFICITY` public read-only aliases.
* Migration 184 (`voi_forecasts`); head fixture `migration_head_180` →
  `migration_head_184` (only 184 applied, checkpointed, rollback journal,
  `integrity_check` ok, `foreign_key_check` clean; 181–183 are the merge chain's
  router R1, learner-text gaps and facet identity: **expect renumbering**);
  DB and config references regenerated (300 table notes, 681 config leaves).
* CLI `learnloop evsi simulate|calibration` (help snapshot refreshed); no
  sidecar RPC (nothing to pin in `test_mobile_allowlist.py`).
* Tests: `tests/test_evsi_calibration_sim.py` (10), `tests/test_voi_forecasts.py`
  (29); `tests/test_architecture.py` registers the new SQL owner.
* Codex review fixes (F1–F8, `evsi-calibration-codex-review.md`): linked,
  independent truth with repair effect apart; target-facet follow-up outcomes
  under a frozen contract; follow-up and staged joins through explicit
  bindings; the staged forecast written after the decision, behind the kill
  switch; untimed recurrences never measured zeros; the `incumbent` arm and
  per-world histories, with the study rerun. Re-review fixes (F1, F5/F9, F6,
  F10): cited diagnosis support resolved to its observation; the facet map
  part of the frozen follow-up contract; a follow-up taken only through the
  offer its own queue produced; one repair outcome per cold verification.
  Forecast body `voi_forecast_v3`, report `voi_calibration_report_v3`.

## 12. Paid calls and data

None: no model route, no OpenRouter or Codex call, $0.00. One free public
download (the Eedi 2020 archive, 657 MB). No tracked working vault was read
directly or written; the three backup-API copies live in the worktree's
gitignored `fixtures-local/evsi-copies/`.

## 13. Gate

After the Codex review fixes (source and tests as of `e1f5b98f`; the
original stage gate, at `bd49ed56`, was 8,635 / 94). `TMPDIR` = the
worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,645 passed**, 0 failed, 0 skipped (257 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8,551 deselected (85 s) |
| `db_generate_reference.py` then `db_validate_reference.py` | not rerun: the review fixes change no schema or config (stage run: `errors: []`, 300 table notes, 681 config leaves) |
| New tests | `tests/test_evsi_calibration_sim.py` 10 passed, `tests/test_voi_forecasts.py` 25 passed |
| Frontend | unchanged (not run) |
| `learnloop evsi simulate` (full study) | ok, 711 s on 12 workers, report in `fixtures-local/evsi-calibration-v2/` |

## 14. Open questions

* How strong are the owner's free-text checks? The study brackets 0.41–0.9;
  the live ledger will measure it (the probe sites' answer reliability).
* Which non-myopic rule should the successor adopt: the 2–3 check lookahead
  shown here, or a full sequential policy (the router's planner)?
* `ENCOUNTERS_UNTIL_CAUGHT = 6` has no data behind it yet; the personal
  recurrence history replaces it as classes accrue, but a direct measurement
  (how often an LO's items come back before a misconception is caught) would
  be better.
* Teach-back can confirm a cause but not rule one out (a later success may
  follow a repair); a truth adapter for "ruled out" needs the teach-back
  diagnosis to say which causes it tested.
* Today's robust completion gate (mvp-0.8) is itself a stop rule the
  simulation finds too eager where checks are strong and stakes high (§4.3).
  The cap-lifting successor should decide whether value of information
  replaces it or it stays as an abstention signal only.
* Staged diagnostic decisions have no decision-to-attempt receipt: a live
  staged forecast stays right-censored (`no_attempt_binding`) until the staged
  controller records which attempt administered it. No production caller
  passes a `DiagnosticSelector` today, so nothing is lost yet.

## 15. Merge onto main (2026-10-13)

Merged onto main at `09c9f8d3`, after the Guide fix, docs, router R1
(mvp-0.15, migration 181), learner-text gaps (mvp-0.16, 182), facet identity
(183) and the T6 follow-up's output-budget policy. No serving default change
and no successor: main touched none of the branch's diagnosis or EVSI modules,
and the only readers of `evsi.measured_loss_enabled` remain the
zero-authority causal shadow and the offline report. The branch makes no model
call, so the T6 follow-up's output-budget policy has nothing to govern here.

* Migration 184 kept its number (main's head was 183). `migration_head_184` was
  rebuilt from main's `migration_head_183` with the backup API and only 184
  applied (checkpointed, `journal_mode=DELETE`, `integrity_check` ok,
  `foreign_key_check` clean, no `-wal`/`-shm`); head 183 removed. All eight
  defaults snapshots (mvp-0.9 to mvp-0.16) recomputed; they move only because
  the effective config gains `[evsi]`. References regenerated (308 table
  notes, 758 config leaves, `errors: []`).
* R1's tables are now on every migrated vault, so the router adapter reads
  the real `router_decisions`/`router_outcomes`. Composed (report
  `voi_calibration_report_v4`): the adapter joins only an offer R1 says was
  `taken`. R1's other statuses judge the offer, not the probe: a queue
  refresh supersedes an offer whose committed presentation stays in front
  under a new scheduler candidate, and `router_outcomes` is a DERIVED cache
  rebuilt only by `learnloop rebuild`, so `open` can be stale. Before the fix
  either case reported a presentation that had been answered as `superseded`
  or `open`; now the ledgers' presentation binding decides.
* A probe the Today queue's seeded exploration drew (R1 admits probe
  near-ties at mvp-0.15) carries R1 review F4's `scheduler_exploration`
  marker on its presentation; its forecast now records the same marker in
  its `selection` block (forecast body `voi_forecast_v4`), so the receipt
  never presents a drawn check as the EIG choice.
* Tests: `tests/test_evsi_router_composition.py` (5: the real R1 path end to
  end through the sidecar's Today offer and the router replayer; the
  superseded and stale cases and the explored-probe marker failed first);
  `test_probe_selection_forecast_joins_its_realized_answer` now expects
  `router_outcomes then ledgers`.
* Still open (owner): R1 logs every staged P2 decision (`staged_p2`, with
  `controller_decision_id`) and binds its outcome to the chosen item's next
  attempt in the session at or after the decision. That is a session rule,
  not an explicit receipt, so the report does not use it for staged
  diagnostic forecasts (they stay `no_attempt_binding`, review F3/F6's rule);
  the owner may accept R1's binding instead.
* Gate at the composition commit (`TMPDIR` = the worktree's
  `fixtures-local/tmp`): `lint-imports` 15 kept, 0 broken; full suite
  `-n auto` 9,047 passed, 0 failed, 0 skipped (325 s); `-m durability` 95
  passed (27 s); `db_validate_reference.py` `errors: []`; `validate_vault.py`
  passed; frontend unchanged (not run). No paid call.
