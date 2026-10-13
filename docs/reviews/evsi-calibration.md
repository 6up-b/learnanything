# EVSI calibration: measuring what value of information runs on

Stage `evsi-calibration`, branch `evsi/calibration` (base `57d31c63`).
Owner question (2026-10-12): *is there any way we could better calibrate the
EVSI instead of just having it run based off of uncalibrated baseless
assumptions?* Value of information is about to become the only limit on probes
and follow-ups (the four count caps are being lifted onto it), so this stage
measures what it can, labels what it cannot, and instruments the live
decisions so the rest gets measured from the owner's own data.

## Summary

1. **The hand-set response model is badly overconfident, and it is what EIG and
   EVSI run on.** Fitted to 15.9M real Eedi answers, a learner who holds a
   misconception picks the distractor that diagnoses it **41%** of the time
   (95% CI 40–43%), not the **83%** today's contrast card implies (80% in
   `probe.irt.err_low_frac`, 60% in the bridge default). Learners who know the
   material slip **12%** of the time, not 3–5%. In the simulation, checks chosen
   under the hand-set vocabulary are forecast to be worth 0.38 minutes and
   0.32 nats each; they realize **−0.02 minutes and −0.04 nats**: on average
   they move belief *away* from the truth. Under the Eedi-fitted model the same
   forecasts are calibrated (expected calibration error 0.01, predicted EIG
   0.097 nats vs 0.097 realized about the truth).
2. **At Eedi's measured signal strength, one more multiple-choice check is
   almost never worth a minute.** Every value-based rule stops after the error
   that opened the episode; today's caps spend 3.4 checks per episode for a
   marginally better outcome (right repair 46% vs 40%, wrong-action minutes
   1.79 vs 1.81): **5.18 vs 1.81 minutes per episode** (repair 3 min). This
   holds at repair costs of 10 and 30 minutes too.
3. **When checks *are* valuable, EVSI as built under-probes.** With a strong
   instrument (consistency 0.9) and 30-minute repairs, today's `rank_feasible`
   costs **18.8 minutes per episode vs 11.9 for the caps**: it abstains
   whenever any ensemble member or the ±0.15 stress changes the action after
   *any* answer (even an improbable one), and its one-step value misses checks
   that only pay off in pairs. Ignoring the flip abstention (14.8) and valuing
   the best 2–3 checks jointly (13.0) close most of that gap; the lookahead is
   the best rule at moderate value (5.63 vs caps 5.92 at repair 10). **Lifting
   the caps onto today's EVSI would stop diagnosis exactly where it matters.**
4. **The EIG path's `VALUE_PER_NAT_MINUTES = 60` is 5–500× too high**
   (measured: about 0.43 × the repair minutes per nat at consistency 0.9,
   0.04 × at Eedi's), and its 90% agreement gate abstains in 89% of episodes,
   so the gate, not value, is what stops it.
5. **The robustness knobs barely matter; the stakes and the model do.**
   `PERTURBATION_DELTA`, `INSTRUMENT_PERTURBATION_CONCENTRATION`,
   `ROBUST_DRAW_COUNT` and `BURDEN_COST` change rankings but not minutes
   (all paired 95% CIs include 0, or a positive burden only hurts). Knowing the
   true repair minutes is worth 0.7 minutes per episode; a quantile of 0.25
   instead of 0.10 matches realized value better.
6. **Part B is live (logging only):** every value-of-information decision now
   writes a `voi_forecasts` receipt, and `learnloop evsi calibration` scores
   them against realized answers and later truth. **Part C is built and off:**
   the cost of leaving a misconception unresolved, measured from the owner's
   recurrence history and shrunk toward an Eedi prior.

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
  the correct ones included). 400 flagged learners: 160 know it, 159 hold a
  labelled misconception, 81 something else.
* **The system** believes either `hand_set` (today's contrast-card rows read
  from `probe_families`, mapped onto four options) or `eedi_fitted` (the
  subject means, without knowing each question's own consistency).
* **The real selectors** choose: `evsi` is `scheduling.evsi.rank_feasible`;
  `eig` is `robust_composition.evaluate_selection`, both over ensembles built by
  `robust_composition.build_ensemble` with an identity grading channel (a
  multiple-choice answer is read exactly). Baselines: `caps` (today's
  probe-episode rules, thresholds read from `ProbeEpisodeConfig`), `random`,
  `max_entropy`. What-if readings of the same outputs: `evsi_lcb_only`
  (measure whenever the robust value clears the cost, ignoring flips),
  `evsi_lookahead` (also value the top 2–3 checks jointly, the
  knowledge-gradient* idea) and `eig_no_gate` (ignore the agreement gate).
* **Costs:** a check 1 minute, a repair `DEFAULT_INTERVENTION_MINUTES` = 3
  (continue = 0), wrong action = the true loss table's minutes. All arms see the
  same learners and the same answer to the same question (common random
  numbers), so differences are paired. Ensembles use 32 draws (live 128; the
  sweep shows no minutes effect).
* Two design defects were found and fixed during the stage; the first full run
  was discarded: the starting belief conditioned on the error alone (biasing it
  against `knows`), and a stronger-instrument override left a holder zero
  probability of the other distractors (log-score blow-ups). The numbers below
  are from the corrected run (`fixtures-local/evsi-calibration/`, 607 s on 12
  workers).

### 4.1 Forecast quality: (1) outcome calibration, (2) information, (3) action change

Fitted world, repair 3 minutes, checks pooled over each policy's episodes.

| System model | Policy | Log loss (uniform = 1.386) | ECE | Predicted EIG (nats) | Realized entropy drop | Realized gain about the truth [95% CI] | P(action change) predicted / realized | EVSI per check predicted / realized (min) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| hand_set | caps | 1.401 | 0.107 | 0.317 | 0.209 | **−0.042** [−0.113, 0.027] | 0.260 / 0.262 | 0.377 / **−0.016** |
| hand_set | max_entropy | 1.303 | 0.069 | 0.156 | 0.117 | 0.039 [−0.008, 0.090] | 0.116 / 0.120 | 0.113 / 0.049 |
| hand_set | evsi_lcb_only | 1.683 | 0.139 | 0.584 | 0.378 | −0.276 [−0.703, 0.136] | 0.625 / 0.526 | 1.432 / **−0.553** |
| eedi_fitted | caps | 1.162 | **0.011** | 0.097 | 0.096 | **0.097** [0.077, 0.119] | 0.070 / 0.064 | 0.027 / 0.004 |
| eedi_fitted | max_entropy | 1.176 | 0.010 | 0.088 | 0.096 | 0.092 [0.070, 0.112] | 0.053 / 0.058 | 0.017 / 0.013 |
| eedi_fitted | eig_no_gate | 1.212 | 0.003 | 0.069 | 0.073 | 0.073 [0.063, 0.085] | 0.067 / 0.067 | 0.023 / 0.017 |

Reliability of the answer forecasts (caps): under `hand_set`, answers given
0.7–0.8 happen 32% of the time and answers given 0.0–0.1 happen 11%; under
`eedi_fitted` every decile is within 0.06 of its rate. By predicted EIG
quintile, the hand-set model's most "informative" checks (0.61 nats predicted)
move belief 0.19 nats *away* from the truth; the fitted model's quintiles track
the truth (0.19 predicted, 0.18 realized). The action-change forecast is the one
thing the hand-set model gets roughly right on average (0.26 vs 0.26), but not
by bin (0.85 predicted → 0.61 realized).

### 4.2 (4) Checks, minutes, identification, waste

Fitted world, repair 3 minutes. Total = check minutes + the true loss of the
action taken; wasted = checks after the last change of action + wrong-action
minutes.

| System | Policy | Checks | Total minutes [95% CI] | Right action | Misconception identified | Wasted minutes | Main stop |
|---|---|---:|---:|---:|---:|---:|---|
| eedi_fitted | caps | 3.38 | 5.18 [4.97, 5.45] | 0.46 | 0.23 | 4.78 | budget exhausted 266, decision stable 97 |
| eedi_fitted | random | 3.38 | 5.17 [4.92, 5.41] | 0.45 | 0.17 | 4.79 | budget 260 |
| eedi_fitted | max_entropy | 3.36 | 5.12 [4.88, 5.37] | 0.47 | 0.16 | 4.72 | budget 259 |
| eedi_fitted | eig | 0.01 | 1.82 [1.70, 1.95] | 0.40 | 0.03 | 1.82 | abstain (agreement gate) 354 |
| eedi_fitted | eig_no_gate | 6.74 | 8.44 [7.88, 9.02] | 0.53 | 0.31 | 6.96 | value stop 317 |
| eedi_fitted | evsi | 0.00 | 1.81 [1.67, 1.96] | 0.40 | 0.03 | 1.81 | LCB below cost 396 |
| eedi_fitted | evsi_lookahead | 0.00 | 1.81 [1.67, 1.95] | 0.40 | 0.03 | 1.81 | LCB below cost 396 |
| hand_set | caps | 2.84 | 4.96 [4.64, 5.28] | 0.55 | 0.23 | 3.79 | decision stable 224 |
| hand_set | evsi | 0.01 | 2.09 [1.93, 2.26] | 0.40 | 0.05 | 2.09 | LCB below cost 368, flip abstain 28 |
| hand_set | evsi_lcb_only | 0.10 | 2.23 [2.02, 2.42] | 0.41 | 0.06 | 2.17 | LCB below cost 396 |

With Eedi's signal, four checks lift the right-action rate from 0.40 to 0.46
and identify the exact misconception 23% of the time; that is not worth 3.4
minutes when a wrong repair costs 3–6.

### 4.3 Regimes: instrument strength × stakes

Mean total minutes per episode (checks; right-action rate), `eedi_fitted`
system. "Consistency" overrides the holder's designated-distractor rate for
truth and model alike (the other answers keep their fitted ratio).

| Consistency | Repair min | caps | eig (as built) | eig_no_gate | **evsi (as built)** | evsi_lcb_only | evsi_lookahead |
|---|---:|---|---|---|---|---|---|
| Eedi 0.41 | 3 | 5.18 (3.4; .46) | 1.82 (0.0; .40) | 8.44 (6.7; .53) | **1.81** (0.0; .40) | 1.81 | 1.81 |
| Eedi 0.41 | 10 | 9.36 (3.4; .46) | 6.04 | 12.39 | **6.03** (0.0) | 6.00 | 6.00 |
| Eedi 0.41 | 30 | 21.31 (3.4; .46) | 18.09 | 23.69 | **18.08** (0.0) | 18.06 | 18.02 |
| 0.7 | 3 | 4.64 (3.3; .65) | 1.93 | 6.69 | **1.81** (0.0) | 1.81 | 1.81 |
| 0.7 | 10 | 7.84 (3.3; .65) | 6.11 | 9.23 | **6.07** (0.0) | 6.16 | 6.19 |
| 0.7 | 30 | 16.99 (3.3; .65) | 18.06 | **16.48** (5.6; .76) | 18.25 (0.0; .41) | 17.86 | 17.00 (0.7; .51) |
| 0.9 | 3 | 3.84 (2.9; .80) | 2.03 | 5.33 | **1.88** (0.0) | 1.90 | 1.90 |
| 0.9 | 10 | 5.92 (2.9; .80) | 6.20 | 7.01 | 6.29 (0.0; .41) | 5.95 (0.4) | **5.63** (0.6; .56) |
| 0.9 | 30 | 11.87 (2.9; .80) | 18.10 | **11.81** (4.6; .86) | 18.84 (0.0; .41) | 14.77 (0.9; .61) | 13.04 (1.7; .72) |

Where checks are weak or cheap to skip, every value rule beats the caps by
2.0–3.4 minutes per episode. Where they are strong and the stakes high, `evsi`
as built is the worst rule (+7.0 minutes vs caps at 0.9/30): ignoring the flip
abstention recovers 4.1 of those minutes, valuing 2–3 checks jointly another
1.7, and 1.2 remain. No rule beats a well-placed cap everywhere; the lookahead
is never far from the best, and is the best at 0.9/10.

### 4.4 (5) Sensitivity to each hand-set number

Regime where measuring matters (consistency 0.9, true repair 10 min, true
check 1 min; 300 learners). Each row moves **what the system assumes**; the
world stays fixed. Mean total minutes (checks; Kendall τ of the first
decision's ranking vs the current value; paired Δ vs current [95% CI]).

| Parameter | Value | evsi (as built) | evsi_lcb_only | evsi_lookahead |
|---|---|---|---|---|
| `PERTURBATION_DELTA` | 0.05 … 0.35 (current 0.15) | 6.49–6.52, Δ ≤ 0.03 | identical (delta only feeds abstention) | identical |
| `ROBUST_QUANTILE` | 0.05 | 6.55 (τ .85) | 6.25, Δ +0.14 [−0.08, 0.38] | 5.94, Δ +0.19 [−0.01, 0.41] |
| | **0.10 (current)** | 6.52 | 6.11 | 5.75 |
| | 0.25 | 6.51 (τ .78) | **5.95, Δ −0.16 [−0.33, −0.00]** | 5.66, Δ −0.09 [−0.29, 0.12] |
| | 0.50 | 6.51 (τ .64) | 5.90, Δ −0.21 [−0.46, 0.11] | 5.56, Δ −0.19 [−0.50, 0.10] |
| `INSTRUMENT_PERTURBATION_CONCENTRATION` | 4 (≈ Eedi κ) | 6.50 (τ .55) | 6.33, Δ +0.22 [−0.06, 0.52] | 5.80, Δ +0.05 [−0.44, 0.53] |
| | 10 | 6.50 (τ .70) | 6.32, Δ +0.20 [−0.08, 0.46] | 5.86, Δ +0.12 [−0.18, 0.43] |
| | **40 (current)** | 6.52 | 6.11 | 5.75 |
| | 160 | 6.56 (τ .77) | 6.09, Δ −0.03 [−0.27, 0.20] | 5.83, Δ +0.09 [−0.18, 0.34] |
| Ensemble draws | 16 / **32** / 64 / 128 | 6.56 / 6.52 / 6.51 / 6.51 (τ .84–.88) | 6.08 / 6.11 / 6.15 / 6.27 | 5.86 / 5.75 / 5.78 / 5.92 (all Δ CIs include 0) |
| `BURDEN_COST` | **0 (current)** / 0.5 / 1 / 2 | ≈ 6.51 | 6.11 / 6.40 / 6.50 / 6.35 (Δ +0.29 [0.03, 0.56] at 0.5) | 5.75 / 5.98 / 6.28 / 6.29 (Δ +0.53 [0.21, 0.90] at 1) |
| Assumed repair minutes (`DEFAULT_INTERVENTION_MINUTES`; truth 10) | 1.5 | 6.50 | 6.50, Δ +0.06 | 6.50, Δ +0.06 |
| | **3 (current default)** | 6.50 | 6.44 | 6.44 |
| | 10 (the truth) | 6.52 | **6.11, Δ −0.33 [−0.71, 0.06]** | **5.75, Δ −0.70 [−1.15, −0.22]** |
| | 20 | 6.52 | 5.85, Δ −0.59 [−1.06, −0.05] | 5.59, Δ −0.85 [−1.44, −0.24] |
| Assumed check minutes (truth 1) | 0.5 | 6.52 | 5.85, Δ −0.26 [−0.54, 0.02] | 5.59, Δ −0.16 [−0.54, 0.25] |
| | **1 (the truth)** | 6.52 | 6.11 | 5.75 |
| | 1.5 (causal default) | 6.51 | 6.40, Δ +0.29 [0.03, 0.56] | 6.24, Δ +0.49 [0.19, 0.83] |

`VALUE_PER_NAT_MINUTES` (EIG path, same regime): with the agreement gate the
EIG path barely measures whatever the value (6.41–6.50 minutes, Δ ≤ 0.07).
Without the gate:

| `VALUE_PER_NAT_MINUTES` | 1 | 2.5 | 5 | **10** | 20 | 40 | **60 (current)** | 120 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| eig_no_gate total minutes (checks) | 6.50 (0.0) | 6.33 (0.3) | 5.87 (1.8) | **5.56 (2.8)** | 6.43 (3.8) | 7.14 (4.5) | 7.51 (4.9) | 8.10 (5.7) |
| Δ vs current [95% CI] | −1.01 [−1.91, −0.30] | −1.18 | −1.64 | **−1.94 [−2.36, −1.53]** | −1.08 | −0.37 | 0 | +0.59 [0.41, 0.78] |

Realized minutes per nat (regression of a check's realized value on its
predicted EIG, calibrated model): 0.12 [−0.17, 0.40] at Eedi/3 min, 1.31
[1.05, 1.53] at 0.9/3, **4.35 [3.50, 5.12] at 0.9/10**, 13.06 [10.51, 15.34]
at 0.9/30. The minutes a nat is worth scale with the stakes (≈ 0.43 × repair
minutes at consistency 0.9, ≈ 0.04 × at Eedi's); no single constant fits.

Robust quantile against realized value (calibrated model, the caps' checks):
the 10th-percentile member under-predicts the realized value in every regime
with value (by 0.07–0.73 minutes), the 50th over-predicts, and the **25th is
within ±0.09 minutes** of realized at 0.7–0.9 and repairs of 3–30 minutes.

### 4.5 Part C in simulation: charging the unresolved cost

True `U` = Eedi excess repeat rate 0.151 × encounters × 2 minutes per repeated
error. "Measured" = the system's loss charges the true `U`; "minutes-only" =
today's loss. Paired Δ = measured − minutes-only, minutes per episode.

| Consistency | Encounters | True U | evsi_lcb_only: Δ [95% CI] (checks) | evsi_lookahead: Δ [95% CI] (checks) |
|---|---:|---:|---|---|
| Eedi 0.41 | 3 | 0.91 | +0.03 [−0.03, 0.10] (0 → 0) | same |
| Eedi 0.41 | 12 | 3.63 | −0.07 [−0.28, 0.16] (0 → 0) | same |
| Eedi 0.41 | 24 | 7.25 | −0.27 [−0.71, 0.18] (0 → 0.01) | same |
| 0.9 | 3 | 0.91 | +0.12 [0.03, 0.22] (0.04 → 0.13) | +0.12 [0.03, 0.22] |
| 0.9 | 6 | 1.81 | +0.11 [−0.04, 0.26] | +0.10 [−0.05, 0.24] |
| 0.9 | 12 | 3.63 | −0.23 [−0.55, 0.03] (0.04 → 0.42) | −0.25 [−0.57, 0.04] |
| 0.9 | 24 | 7.25 | **−1.11 [−1.60, −0.64]** (0.04 → 0.88) | **−1.04 [−1.52, −0.58]** (→ 0.99) |

Charging the true cost pays off once it is large next to a repair and a check
(clearly at 7 minutes, borderline at 3.6); below that it costs a few seconds per
episode (slightly more checking than the value repays). So the measured loss is
worth having exactly when the owner's history says misconceptions linger.

## 5. Recommended values

Confidence: **high** = measured with tight CIs and the decision effect is
clear; **medium** = measured, transfer uncertain; **low** = direction only.

| Parameter | Current | Recommended | Evidence | Confidence |
|---|---|---|---|---|
| Card vocabulary as a likelihood (`ORDINAL_VOCABULARY`, default rows) | "dominant" ≈ 0.83 consistency, slip ≈ 0.03 | Keep as a **prior only**, and let real counts take over fast: lower `DEFAULT_CONDITIONAL_PSEUDO_COUNT` from 8 to ≈ 2 so a family's own observations dominate after a handful | §3, §4.1: the vocabulary is 2× overconfident in consistency, 4× in slip; its checks lose information about the truth | high (direction), low (the value 2: count updating was not simulated) |
| `probe.irt.err_low_frac` / `unfamiliar_error_leak` / bridge sensitivity–specificity | 0.80 / 0.20 / 0.6–0.9 | For multiple-choice-like items: 0.41 / 0.13 / 0.41–0.87 (Eedi). For free text: unchanged until the owner's calibration counts exist (§6) | §3 | high for MCQ, low for transfer |
| `PERTURBATION_DELTA` | 0.15 | **0.10** (the measured per-row error of a calibrated model: p90 0.098; hand-set rows are off by 0.52 at p90, which no delta can cover) | §4.4: no minutes effect at any value while flips abstain on members | medium (value), high (no decision effect) |
| `ROBUST_QUANTILE` | 0.10 | **0.25** | §4.4: realized value sits at the members' 25th percentile; lcb_only Δ −0.16 [−0.33, −0.00] | medium |
| `INSTRUMENT_PERTURBATION_CONCENTRATION` | 40 | keep 40; note Eedi's between-question κ ≈ 3.7 | rankings move (τ 0.55 at 4), minutes do not | low |
| `ROBUST_DRAW_COUNT` | 128 | keep | flat; draws only add ranking noise (τ ≈ 0.85) | high |
| `BURDEN_COST` | 0 | keep 0 (dormant) | any positive value only adds minutes | high |
| `VALUE_PER_NAT_MINUTES` | 60 | **retire** for EVSI computed from the loss table on the EIG path; if a constant must stay, ≈ 0.4 × the repair minutes (≈ 1.3 at the 3-minute default, 4 at 10) | §4.4: 60 is 5–500× the measured minutes per nat; best in sweep 10 vs measured 4.35 [3.50, 5.12] | high (60 is wrong), medium (the replacement) |
| `ENSEMBLE_ACTION_AGREEMENT_THRESHOLD` | 0.90 | do not let it stop diagnosis on its own (it abstained in 89% of episodes) | §4.2 | medium |
| `DEFAULT_INTERVENTION_MINUTES` | 3.0 | keep as the fallback, but measure repair durations per repair class (decision-value spec Stage 2); Eedi cannot | §4.4: knowing the true 10 minutes is worth 0.70 [0.22, 1.15] minutes per episode | high (it matters), n/a (value) |
| Causal probe burden default | 1.5 | the live receipt's measured burden; 1.5 over-states a 1-minute check | §4.4: +0.49 [0.19, 0.83] | medium |
| Flip abstention (`rank_feasible`) | any member/stress flip abstains | abstain only when the robust value fails to clear the cost, or when the flipping emissions carry real probability mass | §4.3: +4 minutes per episode at 0.9/30 | high (as built is wrong), medium (the replacement) |
| One-step EVSI | myopic | value the best 2–3 checks jointly when no single check clears the cost (`evsi_lookahead`) | §4.3 | medium |

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
| `followup_selection` | `evaluate_intervention_followup` when a follow-up is queued | the facet response model over the primary facet's marginal |
| `causal_shadow_selection` | `causal_diagnostic_selector.record_shadow_selection` (`rank_feasible`) | EVSI point/LCB/UCB of every candidate, the loss table, emission keys per hypothesis |
| `staged_diagnostic_selection` | `staged_policy._select_diagnostic` (`rank_feasible`) | same |

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
chosen scheduler candidate → the attempt that took it; `pending` and
`not_taken` stay right-censored), else the ledgers
(`practice_attempts.probe_presentation_id` → `probe_observations`; the first
later attempt on the chosen item). The realized answer is mapped into the
forecast's own alphabet (probe outcome label, the robust coarse emission,
`bucket|error` for follow-ups, the matched hypothesis's declared emission for
the causal shadow); anything else is `unmapped`, never guessed. **Truth
adapters** count only independent evidence: a cold verification of a repair
(success confirms the repaired causes, failure rules them out), a factor's
resolution (`repair_confirmed` / `escalated_unrepaired`), and a later
teach-back whose diagnosis names the same cause. The system's own posterior
resolving a misconception is not truth.

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
   successor starts from audited measured-loss receipts.
   `learnloop evsi calibration` shows the estimate first.
2. **Before the caps move onto value of information,** replace the flip
   abstention (abstain only when the robust value does not clear the cost) and
   add the 2–3 check lookahead. Recommended: yes, as part of the successor
   (a serving change, so behind its kill switch).
3. **Retire `VALUE_PER_NAT_MINUTES`** in favour of loss-derived EVSI on the EIG
   path, and stop the agreement gate from ending diagnosis alone. Recommended:
   yes, same successor.
4. **Lower `DEFAULT_CONDITIONAL_PSEUDO_COUNT` (8 → 2)** so cards learn from the
   owner's answers quickly. Recommended: yes (an algorithm successor: it changes
   posteriors).
5. **`ROBUST_QUANTILE` 0.10 → 0.25 and `PERTURBATION_DELTA` 0.15 → 0.10.**
   Recommended: yes with the successor; neither changes today's serving
   (only shadow EVSI and the robust gate read them).
6. **Measure repair durations per repair class** (decision-value spec Stage 2):
   worth ≈ 0.7 minutes per diagnosed error in the simulation.

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
* Tests: `tests/test_evsi_calibration_sim.py` (8), `tests/test_voi_forecasts.py`
  (17); `tests/test_architecture.py` registers the new SQL owner.

## 12. Paid calls and data

None: no model route, no OpenRouter or Codex call, $0.00. One free public
download (the Eedi 2020 archive, 657 MB). No tracked working vault was read
directly or written; the three backup-API copies live in the worktree's
gitignored `fixtures-local/evsi-copies/`.

## 13. Gate

Source and tests as of `bd49ed56` (later commits are this file and
regenerated references only). `TMPDIR` = the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8,635 passed**, 0 failed, 0 skipped (261 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8,541 deselected (98 s) |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []` (300 table notes, 681 config leaves, 3,951 wikilinks) |
| New tests | `tests/test_evsi_calibration_sim.py` 8 passed, `tests/test_voi_forecasts.py` 17 passed |
| Frontend | unchanged (not run) |
| `learnloop evsi simulate` (full study) | ok, 607 s on 12 workers, report in `fixtures-local/evsi-calibration/` |

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
