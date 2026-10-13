# EVSI calibration across simulator families (RankCert)

Stage `evsi-multisim`, branch `evsi/calibration` (on `2593ee75`). Owner
decision 2026-10-13: *multiple sim families for EVSI calibration*. The
single-family study ([`evsi-calibration.md`](evsi-calibration.md)) drew its
conclusions under one simulator, a three-class latent class model fitted to
Eedi. RankCert (arXiv 2609.26069): simulators that fit learner data equally
well can disagree about which policy is best, so a conclusion drawn under one
family is a statement about that family. This stage fits three more,
structurally different families to the same Eedi answers, scores all four on
held-out students, reruns every comparison of the study in each under common
seeds, counts a conclusion only when every family agrees, and turns what
survives into a ranked change proposal for the value-of-information successor
(`serving/voi-stopping`, mvp-0.17).

Offline only: no serving code or default changed, no paid call.

## Summary

**Four families, one Eedi.** A latent class model (the study's), a
cognitive diagnosis model (MC-DINA with DINO misconception triggers, the
Q-matrix from the misconception labels), a nominal-response IRT model with a
misconception trait, and a latent transition model (the learner learns
between encounters). All four are fitted to the same 111,096 Eedi triple
sequences, and all beat the item-marginal baseline on 8,516 held-out students
(log loss 0.721–0.748 against 0.796; every family passes RankCert's adequacy
gate). The study's own family fits worst; the other three fit about equally
well. Each family forecasts the designated distractor's share of wrong
answers within 0.6 points. The study was rerun in every family under common
seeds: 14 policy arms, 9 regimes, the system calibrated to every other
family, the parameter sweeps, the measured loss, and the pseudo-count stream.
94 minutes, no paid call; every unchanged arm reproduced the earlier run's
episodes exactly.

**The single-family claims, tested in every family** (`supported`: every
family's 95% CI agrees; `directional`: every point estimate does;
`family-dependent`: the families disagree in sign):

| Single-family claim | Single-family value | Across the four families | Range across families |
|---|---|---|---|
| The card is overconfident (consistency) | 0.83 vs 0.41 | **supported** | 0.25–0.46 |
| Under the card, checks realize negative information about the truth | −0.06 nats | **supported** (caps_only), directional (incumbent; `lta`'s CI reaches +0.02) | −0.05 to −0.16 nats per check |
| At Eedi's strength, value rules beat today's serving | 1.81 vs 3.77 min | **supported** at repairs of 3 and 10 min, directional at 30 | −1.52 to −2.10 min per episode |
| EVSI as built under-probes where checks are strong (0.9/30) | 17.9 vs 13.3 | directional (3/4 certified) | +0.19 to +5.85 |
| … because of the flip abstention | 17.9 → 12.5 | **supported** (0.9/30, 0.9/10, 0.7/30; also under every mis-calibrated system) | +1.28 to +7.21 at 0.9/30 |
| … and of one-step valuation (2–3 check lookahead) | 12.5 → 10.8 | family-dependent (no gain in `nrm`) | −2.59 to +0.03 |
| The lookahead beats today's serving | 10.8 vs 13.3 | directional at 0.9/30, 0.9/10, 0.7/30 | −0.37 to −3.10 |
| Today's robust completion gate costs minutes (0.9/30) | +3.7 | family-dependent: that was `lca`'s value; the gate **saves** 0.86–1.58 where checks are weak (supported) | −0.07 to +3.40 |
| `VALUE_PER_NAT_MINUTES = 60` is far too high | 4–500× | directional (60 is 3.8–8.6× the largest measured); **lowering it to 10 is supported** | 10 saves 1.56–2.81 min |
| The measured loss pays off above ~3.6 min | 3.6 | **supported** (never costs) | saves 0.22–0.53 at U = 3.55 |
| `ROBUST_QUANTILE` 0.10 → 0.25 | within noise | directional on minutes, family-dependent on the bias it corrects | −0.40 to 0.00 |
| `PERTURBATION_DELTA` 0.15 → 0.10 | no effect | no decision effect in any family | \|Δ\| ≤ 0.09 |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 → 2 | not simulated | **not supported**: no difference a CI separates from 0; counting at all is what matters | |

**Where the families disagree is where it matters.** With weak checks they
rank the policies alike (Kendall τ 0.76–0.91). With strong checks and
30-minute repairs, they disagree about the winner (τ 0.43, minimum 0.09), and
acting on one family's winner costs up to 3.9–4.9 minutes per episode in
another. That is exactly where the single-family study drew its strongest
conclusions.

**The successor** (`serving/voi-stopping` at `086c24c0`, modelled after its
review fixes). It beats today's serving wherever checks are weak or moderate
(supported: −1.86 to −2.01 minutes per episode at Eedi's strength, −0.49 to
−1.53 at 0.9/10). It is family-dependent where they are strong, because it
keeps today's robust completion gate and values one check at a time. The
**proposed package** keeps the successor's structure, drops the gate, never
hands a flip abstention to the nat scale, and adds the lookahead. It saves
another 1.44–3.23 minutes per episode at 0.9/30 in three families and has the
smallest worst-case regret of all 14 arms: 1.21 minutes per episode, against
3.86 for the successor as built and 3.60 for today's serving.

**Ranked proposal (§6):**

1. The robust completion gate must not end an episode while value decides
   (directional; never costs).
2. Add the 2–3 check lookahead (the minimax-regret choice).
3. Decide a flip abstention by the robust LCB, not the nat scale (neutral
   today; the prerequisite for 4).
4. Use a successor-scoped nat scale of 5 instead of 60.
5. Charge the measured unresolved cost (existing switch, off until the owner
   turns it on).

`ROBUST_QUANTILE`, the gate on the kill-switch path, and the card's rows wait
for live `voi_forecasts` data; `PERTURBATION_DELTA`, the pseudo count, the
burden and the draws stay. Offline only: no serving code or default changed,
no paid call.

## 1. The families

All four are fitted to the **same students on the same 370 misconception
triples** the single-family study found in Eedi NeurIPS 2020 task 1/2 (three
questions whose designated distractors the same students pick together far
more than chance; selected on even `UserId`s). The families are fitted on odd
`UserId`s with `UserId % 8 != 7` (**111,096** triple sequences) and scored on
`UserId % 8 == 7` (**37,105** sequences, 8,516 students), never seen by any
fit.

| Family | Latent learner | Fitted per | Item model | Holding a misconception | Learns? |
|---|---|---|---|---|---|
| `lca` (the study's) | one of three classes: knows / holds the triple's misconception / unsure | triple | free 3-category row per class and item (unsmoothed EM) | a class; at most one | no |
| `cdm` | MC-DINA with a DINO misconception trigger: a binary skill shared by the subject's items + one binary attribute per misconception, at most two held | **subject** (102; the triples of a subject are one test) | four response groups per item (skill × triggered), each a free 4-option row; Q-matrix = the misconception labelling (each item's designated distractor coded to its triple) | binary; co-occurs with the skill and with a second misconception | no |
| `nrm` | continuous ability θ and misconception trait η (independent normals) | triple | Bock nominal response over the 4 options; only the designated distractor's logit reads η (`z_d = a_d θ + λ η + b_d`); MML-EM on an 11×11 Gauss–Hermite grid, MAP with a N(0, 2.5²) prior | a matter of degree; "held" when the designated distractor is the learner's most likely answer on the subject's typical item | no |
| `lta` | the latent class states, moving between encounters in time order (hidden Markov / BKT-style) | emissions and start mix per triple, two transition matrices shared by all triples | as `lca`, smoothed (0.5) | a state; one at a time | **yes**: within a session (answers ≤ 60 min apart) and between sessions |
| `lta_reveal` (stress, not a fit) | `lta` | — | — | — | moves at the fitted **between-session** rates after every answer, as if each answer's reveal taught as much as the days of teaching between Eedi sessions |

Each family becomes a truth world over the Eedi 2024 bank (110 subjects,
1,869 questions; `evsi_calibration/families.py`): it draws a learner's state,
answers a 2024 question, maps the state to the decision-relevant **needs**
(the repairs that would be right; a `cdm` or `nrm` learner can need two) and,
for the learning families, moves the state after every answer. Each family
also supplies its **own calibrated single-cause system model** (the population
average `P(option | hypothesis)` and the prior it implies; the system never
knows a question's own parameters), so "the system calibrated to the truth"
means a different model in each family. Item parameters cannot transfer from
2020 to 2024 (different questions), so a 2024 question takes the parameters of
one fitted 2020 item of its subject (or of the pool), chosen by a seeded hash.

**Instrument strength** ("what if a check were as diagnostic as consistency
`c`") moves holders' response only, for truth and system alike, by a single
logit shift per family calibrated by bisection so that the family's own system
model puts exactly `c` on a held misconception's distractor over the bank.
False alarms, slips and prevalences do not move (tested).

## 2. Fit quality on held-out students

Each family predicts every held-out answer of a triple from the other two
answers (for `lta`, from the other two in time order). 8,516 held-out
students, 111,315 predictions; 95% CIs bootstrap students. "Gain over
marginal" is the log loss (3 categories) saved against each item's own option
frequencies. RankCert's adequacy gate: AUC ≥ 0.55, gain ≥ 0.002 nats,
ECE ≤ 0.08.

| Family | Log loss, 3 categories [95% CI] | Log loss, 4 options [95% CI] | Gain over marginal (nats) [95% CI] | ECE (3 cat.) | AUC P(correct) | Designated share given wrong: forecast / observed | Distractor-choice ECE | Log loss of the choice given wrong | Adequate |
|---|---|---|---|---:|---:|---|---:|---:|---|
| `marginal` | 0.7960 [0.7856, 0.8072] | 0.9452 [0.9314, 0.9601] | — | 0.0040 | 0.645 | 0.287 / 0.289 | 0.013 | 1.028 | baseline |
| `lca` | 0.7479 [0.7355, 0.7598] | 0.9110 [0.8954, 0.9260] | 0.0481 [0.0418, 0.0543] | 0.0138 | 0.762 | 0.285 / 0.289 | 0.051 | 1.104 | yes |
| `cdm` | 0.7209 [0.7099, 0.7311] | 0.8691 [0.8548, 0.8830] | 0.0751 [0.0717, 0.0790] | 0.0073 | 0.768 | 0.284 / 0.289 | 0.026 | 1.019 | yes |
| `nrm` | 0.7238 [0.7143, 0.7342] | 0.8719 [0.8591, 0.8851] | 0.0722 [0.0685, 0.0755] | 0.0078 | 0.766 | 0.285 / 0.289 | 0.029 | 1.021 | yes |
| `lta` | 0.7254 [0.7153, 0.7357] | 0.8886 [0.8759, 0.9022] | 0.0706 [0.0669, 0.0741] | 0.0076 | 0.765 | 0.291 / 0.289 | 0.034 | 1.069 | yes |

* **All four fit, and the study's own family fits worst.** Every family beats
  the item-marginal baseline on students no fit saw and passes the adequacy
  gate. The three new families save 0.071–0.075 nats per answer over the
  marginal; `lca` saves 0.048 (its CI, 0.042–0.054, is below all three). The
  three are indistinguishable from one another (overlapping CIs). This is
  RankCert's setting: several structurally different simulators that fit the
  same data about equally well.
* **Distractor choice.** Every family forecasts the designated distractor's
  share among wrong answers within 0.6 points of what students did (0.284–0.291
  against 0.289), with distractor-choice calibration error 0.026–0.051. Which
  distractor a wrong answer lands on is hardly predictable from the other two
  answers. `cdm` and `nrm` beat the item marginal there by about 0.01 nats.
  `lca` (unsmoothed rows) and `lta` are worse than the marginal on that
  sub-task. The misconception signal in Eedi is mostly in *whether* a learner
  errs and how often on the designated distractor, not in a sharp
  distractor-level fingerprint.

**What each family implies** (over the 2024 bank, under the family's own
calibrated system; *consistency* is P(designated distractor | holds), the
quantity today's card sets to 0.83):

| Family | Consistency | False alarm | Knower slip | Holder correct | Unsure correct | Knows / holds / other | Learners needing two repairs | Mean P(truth) before the episode: knows / holds / other |
|---|---:|---:|---:|---:|---:|---|---:|---|
| hand-set card | 0.83 | 0.28 | 0.03 | | 0.16 | | | |
| `lca` | 0.425 | 0.185 | 0.121 | 0.241 | 0.361 | 0.46 / 0.33 / 0.21 | 0.00 | 0.67 / 0.13 / 0.32 |
| `cdm` | 0.254 | 0.189 | 0.140 | 0.332 | 0.375 | 0.37 / 0.58 / 0.05 | 0.19 | 0.47 / 0.20 / 0.12 |
| `nrm` | 0.460 | 0.181 | 0.141 | 0.184 | 0.415 | 0.76 / 0.14 / 0.09 | 0.08 | 0.77 / 0.10 / 0.23 |
| `lta` | 0.373 | 0.200 | 0.147 | 0.275 | 0.322 | 0.47 / 0.36 / 0.16 | 0.00 | 0.66 / 0.13 / 0.23 |

The families disagree a lot about *who* holds a misconception: 14% (`nrm`) to
58% (`cdm`, where a holder can also have the skill and so is correct a third
of the time). They also disagree on how many learners need two repairs
(0–19%). They agree on the two numbers today's card gets wrong: consistency
0.25–0.46, not 0.83, and a knower's slip of 0.12–0.15, not 0.03.

## 3. The study, rerun in every family

`learnloop evsi multisim` (`evsi_calibration/multisim.py`,
`multifamily.py`). For every family, under **common seeds** (learner `i` has
the same subject in every family and the same question order and uniforms
within a family; arms within a cell are paired):

1. **Main** (fitted strength, repair 3 minutes): every policy with the
   family's calibrated system, with today's `hand_set` vocabulary, and with
   every *other* family's calibrated system (RankCert's rotation).
2. **Regimes**: instrument strength (fitted, 0.7, 0.9) × repair minutes (3,
   10, 30), each world on its own histories, 400 flagged learners.
3. **Rotation** at 0.9/10 and 0.9/30: the system calibrated to each other
   family.
4. **Sensitivities** at 0.9/10 (300 learners): the single-family study's
   sweeps of `PERTURBATION_DELTA`, `ROBUST_QUANTILE`,
   `INSTRUMENT_PERTURBATION_CONCENTRATION`, ensemble draws, `BURDEN_COST`,
   `VALUE_PER_NAT_MINUTES`, the assumed repair and check minutes.
5. **Part C** (the measured unresolved-cost loss) against minutes-only, at the
   fitted strength and 0.9, `U = 0.148 × encounters × 2` minutes.
6. **Pseudo count**: a stream of episodes in which the system starts from the
   hand-set card and folds every check into the card's posterior-weighted
   counts (`(pseudo × vocabulary + counts) / (pseudo + n)`, as
   `validate_and_compile_card` compiles them), at pseudo counts 0.5, 2, 8, 32,
   against the frozen card and the family's calibrated rows.

Policies (all on the real modules; `evsi_calibration/policies.py`):

| Arm | Selection and stop | What it stands for |
|---|---|---|
| `incumbent` | highest hypothesis-EIG check; `probe_episodes._evaluate_completion`'s stops in their order: the episode maximum (4), action equivalent, the mvp-0.8 **robust completion gate** (`couldnt_reliably_distinguish`), decision stable after 2 | today's serving (mvp-0.16) |
| `caps_only` | the same, without the robust completion gate | a cap-only comparator |
| `evsi` | `scheduling.evsi.rank_feasible` as built: robust EVSI per minute, LCB stop, **abstain on any member or ±0.15 stress flip** | EVSI as built |
| `evsi_lcb_only` | `rank_feasible` with the flip abstention ignored | |
| `evsi_lookahead` | `evsi_lcb_only`, and when no single check pays, the best 2–3 ranked checks valued jointly (`evsi_for_conditionals` over the product table) | the knowledge-gradient idea |
| `eig` | `robust_composition.evaluate_selection`: robust EIG × `VALUE_PER_NAT_MINUTES` (60), the 90% agreement gate | the EIG path as built |
| `eig_no_gate` | `eig` without the agreement gate | |
| `max_entropy`, `random` | the caps (with the maximum) and a naive chooser | floors |
| **`voi_successor`** | `serving/voi-stopping` at `086c24c0` (after its two review rounds): today's stops **with the episode maximum lifted onto value** (`episode_maximum_binds`), and on every next observation `voi_stopping.value_candidates`: `rank_feasible`'s LCB where the hypotheses *with posterior mass* route to two or more repairs (review F6), robust EIG × `VALUE_PER_NAT_MINUTES` where `rank_feasible` abstains on a flip (or nothing is at stake) | the successor as built |
| **`voi_proposed`** | the successor's structure (maximum lifted, decision stable / action equivalent kept) with three changes: **no robust completion gate**, **a flip abstention never handed to the nat scale** (the robust LCB decides), and **the 2–3 check lookahead** | the package this study proposes |
| `voi_p_with_gate`, `voi_p_with_fallback`, `voi_p_one_step` | `voi_proposed` with one piece of the successor put back: the robust completion gate / the abstention's nat-scaled fallback / no lookahead | leave-one-out ablations |

Value rules carry no count cap (a 25-check safety bound, never reached in a
cell's mean). Every arm ends by taking the loss table's argmin action. Every
hypothesis in the simulation routes to its own repair, so for the successor a
decision is always at stake and its nat-scaled EIG decides only where
`rank_feasible` abstains (§7 on what that leaves untested).

**Verdicts.** Each claim is a signed paired difference per family (or a
measured quantity), from the stored per-learner episodes (paired within a
cell, 400 bootstrap draws). `supported`: every family's 95% CI is on the
claim's side. `directional`: every family's point estimate is, not every CI.
`family-dependent`: the families disagree in sign. `contradicted`: no family
agrees. `no difference`: the two arms took identical episodes in every family.
Only `supported` counts as a conclusion; `directional` is a recommendation
that may ship behind a kill switch; `family-dependent` waits for live
`voi_forecasts` data, unless the change is RankCert's minimax-regret choice
with a bounded worst-case harm (§4.4, the shipping rule in §6). The `lta_reveal` stress world is reported beside the
fitted families and never votes. Rotation claims count cells (each truth
family × each other family's calibrated system), one claim per regime.

## 4. The single-family claims, family by family

Every table in this section is generated from the run's stored per-learner
episodes. A cell reads `effect [95% CI] mark`, with effect in minutes per
episode unless the claim says otherwise. ✓ means the family's CI is on the
claim's side, ~ that only its point estimate is, and ✗ that it is not. "Hold"
and "Certified" count fitted families. Regime `c/r` is instrument strength
`c` (the fitted consistency, or 0.7/0.9) and repair `r` minutes.

### 4.1 The card vocabulary is overconfident, and its checks mislead

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C1a` | **supported** | 4/4 | 4/4 | +0.42 ✓ | +0.25 ✓ | +0.46 ✓ | +0.37 ✓ |  |
| `C1b:incumbent` | **directional** | 4/4 | 3/4 | -0.10 [-0.18, -0.02] ✓ | -0.15 [-0.24, -0.05] ✓ | -0.14 [-0.22, -0.06] ✓ | -0.05 [-0.14, 0.02] ~ | -0.04 [-0.13, 0.05] ~ |
| `C1b:caps_only` | **supported** | 4/4 | 4/4 | -0.09 [-0.15, -0.01] ✓ | -0.16 [-0.24, -0.08] ✓ | -0.15 [-0.22, -0.08] ✓ | -0.07 [-0.14, -0.00] ✓ | -0.02 [-0.09, 0.06] ~ |
| `C1c` | **directional** | 4/4 | 3/4 | +0.10 [0.07, 0.13] ✓ | +0.10 [0.07, 0.12] ✓ | +0.03 [-0.00, 0.07] ~ | +0.09 [0.06, 0.12] ✓ |  |

Predicted information and realized information about the truth (nats per
check, fitted strength, repair 3), and the outcome log loss of the
incumbent's checks:

| Family | incumbent, hand-set: predicted EIG / realized truth gain [CI] | caps_only, hand-set | incumbent, family's model | outcome log loss hand-set / family (incumbent) |
|---|---|---|---|---|
| `lca` | 0.316 / -0.104 [-0.184, -0.020] | 0.307 / -0.087 [-0.150, -0.013] | 0.110 / +0.101 [0.073, 0.133] | 1.300 / 1.079 |
| `cdm` | 0.330 / -0.146 [-0.243, -0.047] | 0.332 / -0.157 [-0.240, -0.079] | 0.089 / +0.099 [0.066, 0.125] | 1.368 / 1.061 |
| `nrm` | 0.284 / -0.140 [-0.217, -0.056] | 0.287 / -0.150 [-0.225, -0.077] | 0.103 / +0.033 [-0.000, 0.067] | 1.278 / 0.924 |
| `lta` | 0.340 / -0.055 [-0.140, 0.022] | 0.327 / -0.074 [-0.139, -0.004] | 0.102 / +0.091 [0.059, 0.120] | 1.354 / 1.107 |
| `lta_reveal` | 0.338 / -0.037 [-0.126, 0.046] | 0.328 / -0.020 [-0.086, 0.062] | 0.102 / +0.096 [0.063, 0.125] | 1.331 / 1.066 |

* **Supported in every family: the card is overconfident.** Fitted
  consistency is 0.25–0.46 against the card's 0.83 (`C1a`).
* **Under the card, the checks move belief away from the truth** in every
  family. The checks the incumbent picks are forecast at 0.28–0.34 nats each
  and realize −0.04 to −0.15 nats about the truth (`C1b:caps_only` supported:
  every CI is below 0; `C1b:incumbent` directional: `lta`'s CI reaches
  +0.02). Under each family's own calibrated model, the same chooser realizes
  +0.03 to +0.10 nats (`C1c` directional: `nrm`'s CI touches 0, because the
  single-cause system approximates its continuous trait least well).
* **What the card costs in minutes** (hand-set minus the family's calibrated
  model, fitted strength, repair 3):

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` |
|---|---:|---:|---:|---:|---:|
| `incumbent` | +0.40 | +0.38 | +0.38 | +0.52 | +0.61 |
| `caps_only` | -0.12 | -0.55 | +0.05 | +0.02 | +0.12 |
| `evsi` | +0.19 | +0.22 | +0.13 | +0.19 | +0.17 |
| `evsi_lookahead` | +0.33 | +0.42 | +0.19 | +0.31 | +0.29 |
| `eig` | +0.53 | +0.44 | +0.34 | +0.47 | +0.48 |
| `voi_successor` | +0.33 | +0.46 | +0.19 | +0.28 | +0.27 |
| `voi_proposed` | +0.33 | +0.42 | +0.19 | +0.31 | +0.29 |

The card costs today's serving 0.38–0.52 minutes per episode, the successor
0.19–0.46 and the package 0.19–0.42. `caps_only` alone gains in two families:
the overconfident card makes its decision-stable stop fire sooner, and at
Eedi's strength fewer checks is cheaper.

### 4.2 Where checks are as weak as Eedi's, value rules stop, and win

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C7:3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.86 [-1.96, -1.74] ✓ | -2.01 [-2.08, -1.93] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `C7:10` | **supported** | 4/4 | 4/4 | -1.92 [-2.20, -1.66] ✓ | -1.52 [-1.88, -1.14] ✓ | -2.10 [-2.29, -1.86] ✓ | -1.90 [-2.09, -1.71] ✓ | -1.37 [-1.67, -1.08] ✓ |
| `C7:30` | **directional** | 4/4 | 3/4 | -1.87 [-2.71, -1.07] ✓ | -0.57 [-1.64, 0.57] ~ | -2.35 [-2.95, -1.66] ✓ | -1.80 [-2.34, -1.21] ✓ | -0.22 [-1.13, 0.67] ~ |
| `C3w:fitted/3` | **supported** | 4/4 | 4/4 | -1.34 [-1.46, -1.22] ✓ | -1.58 [-1.70, -1.45] ✓ | -0.86 [-1.00, -0.74] ✓ | -1.42 [-1.52, -1.32] ✓ | -1.19 [-1.28, -1.08] ✓ |
| `C8w:fitted/3` | **supported** | 4/4 | 4/4 | -6.56 [-7.09, -6.10] ✓ | -8.07 [-8.61, -7.58] ✓ | -5.61 [-6.12, -5.06] ✓ | -6.77 [-7.23, -6.30] ✓ | -6.42 [-6.91, -5.91] ✓ |
| `C4b:fitted/3` | **supported** | 4/4 | 4/4 | -6.59 [-7.11, -6.14] ✓ | -8.15 [-8.66, -7.66] ✓ | -5.61 [-6.12, -5.06] ✓ | -6.78 [-7.24, -6.30] ✓ | -6.43 [-6.92, -5.93] ✓ |
| `C4b:fitted/30` | **supported** | 4/4 | 4/4 | -6.21 [-7.75, -4.88] ✓ | -7.76 [-9.37, -6.08] ✓ | -6.67 [-8.09, -5.40] ✓ | -6.08 [-7.17, -5.07] ✓ | +0.01 [-1.14, 1.21] ✗ |

* `C7`: at the fitted strength, EVSI as built stops after the error that
  opened the episode. It beats the incumbent by 1.86–2.01 minutes per episode
  at repair 3 and by 1.52–2.10 at repair 10, in every family (supported). At
  repair 30 the result is directional (`cdm` −0.57 [−1.64, 0.57]). This
  confirms the single-family study's 3.77 vs 1.81.
* `C3w`: **here today's robust completion gate *saves* minutes**, 0.86–1.58
  per episode against the same caps without it, in every family
  (supported). It ends 176–329 of 400 incumbent episodes after the minimum two
  checks, and at Eedi's strength a third or fourth check is worth less than
  its minute.
* `C8w`, `C4b:fitted`: the EIG path with `VALUE_PER_NAT_MINUTES = 60`
  measures 5.5–8.3 checks per episode once its agreement gate is removed.
  Loss-derived EVSI beats it by 5.6–8.2 minutes, and so does the gate
  (supported).

### 4.3 Where checks are strong, EVSI as built under-probes

Consistency 0.9, repair 30 minutes (every regime is in Appendix A). Mean
minutes per episode (checks per episode; right-repair rate); the best per
family in bold:

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 13.13 (2.0; 0.72) | 13.30 (2.1; 0.83) | 11.45 (2.1; 0.83) | 13.12 (2.1; 0.72) | 12.58 (2.1; 0.73) |
| `caps_only` | 9.73 (2.8; 0.84) | 12.31 (2.6; 0.90) | 11.52 (2.7; 0.85) | 11.38 (2.8; 0.81) | 11.69 (2.8; 0.79) |
| `evsi` | 17.03 (0.0; 0.45) | 19.15 (0.0; 0.61) | 11.64 (0.0; 0.74) | 16.32 (0.0; 0.47) | 14.44 (0.0; 0.53) |
| `evsi_lcb_only` | 12.62 (0.8; 0.65) | 11.95 (1.6; 0.87) | 10.36 (0.3; 0.79) | 13.36 (0.8; 0.62) | 13.26 (0.7; 0.62) |
| `evsi_lookahead` | 10.04 (1.6; 0.78) | 10.95 (1.9; 0.91) | 10.39 (0.5; 0.80) | 11.40 (1.5; 0.74) | 11.48 (1.5; 0.73) |
| `eig` | 15.70 (0.3; 0.52) | 17.46 (0.4; 0.66) | 11.30 (0.1; 0.75) | 15.69 (0.2; 0.51) | 14.43 (0.2; 0.56) |
| `eig_no_gate` | **9.54 (4.4; 0.90)** | 13.13 (4.2; 0.91) | 12.70 (4.4; 0.86) | **10.02 (4.5; 0.89)** | 12.05 (5.2; 0.83) |
| `max_entropy` | 16.13 (3.2; 0.68) | 15.88 (3.1; 0.82) | 14.13 (2.8; 0.77) | 16.66 (3.2; 0.65) | 15.24 (3.2; 0.68) |
| `random` | 15.29 (3.2; 0.68) | 17.48 (3.2; 0.75) | 12.64 (2.8; 0.81) | 15.46 (3.2; 0.67) | 13.26 (3.1; 0.72) |
| `voi_successor` | 13.39 (0.7; 0.63) | 12.37 (1.3; 0.83) | **10.27 (0.3; 0.80)** | 13.26 (0.7; 0.62) | 13.17 (0.6; 0.62) |
| `voi_proposed` | 10.16 (1.5; 0.77) | 10.93 (1.9; 0.91) | 10.39 (0.5; 0.80) | 11.23 (1.5; 0.74) | 11.39 (1.5; 0.73) |
| `voi_p_with_gate` | 12.66 (1.1; 0.69) | 12.78 (1.4; 0.84) | 10.69 (0.4; 0.80) | 13.78 (1.0; 0.65) | 12.95 (1.0; 0.67) |
| `voi_p_with_fallback` | 9.95 (1.6; 0.78) | **10.55 (1.9; 0.92)** | 10.52 (0.5; 0.80) | 11.29 (1.4; 0.73) | **11.11 (1.4; 0.73)** |
| `voi_p_one_step` | 12.62 (0.8; 0.65) | 11.94 (1.6; 0.87) | 10.36 (0.3; 0.79) | 13.36 (0.8; 0.62) | 13.26 (0.7; 0.62) |

The refitted `lca` reproduces the single-family study's 0.9/30 row: incumbent
13.13 vs 13.32, caps_only 9.73 vs 9.63, evsi 17.03 vs 17.94, evsi_lcb_only
12.62 vs 12.52, evsi_lookahead 10.04 vs 10.76.

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C2a` | **directional** | 4/4 | 3/4 | +3.90 [2.15, 5.67] ✓ | +5.85 [4.25, 7.52] ✓ | +0.19 [-1.10, 1.55] ~ | +3.20 [1.47, 4.71] ✓ | +1.86 [0.11, 3.73] ✓ |
| `C2b:0.9/30` | **supported** | 4/4 | 4/4 | +4.41 [2.90, 5.95] ✓ | +7.21 [5.55, 8.98] ✓ | +1.28 [0.37, 2.28] ✓ | +2.96 [1.65, 4.15] ✓ | +1.18 [-0.08, 2.47] ~ |
| `C2c:0.9/30` | **family-dependent** | 3/4 | 3/4 | -2.59 [-3.83, -1.47] ✓ | -1.00 [-1.65, -0.42] ✓ | +0.03 [-0.45, 0.54] ✗ | -1.96 [-3.09, -0.68] ✓ | -1.77 [-2.99, -0.62] ✓ |
| `C2d:0.9/30` | **directional** | 4/4 | 3/4 | -3.10 [-4.71, -1.68] ✓ | -2.36 [-3.34, -1.24] ✓ | -1.06 [-2.06, 0.23] ~ | -1.71 [-3.28, -0.20] ✓ | -1.09 [-2.74, 0.39] ~ |
| `C2e:0.9/30` | **family-dependent** | 2/4 | 1/4 | +0.31 [-1.00, 1.44] ✗ | -1.36 [-2.34, -0.26] ✓ | -1.13 [-2.30, 0.10] ~ | +0.03 [-1.34, 1.56] ✗ | -0.20 [-1.74, 1.23] ~ |
| `C2b:0.9/10` | **supported** | 4/4 | 4/4 | +0.46 [0.03, 0.89] ✓ | +1.03 [0.65, 1.45] ✓ | +0.22 [0.00, 0.46] ✓ | +0.51 [0.16, 0.81] ✓ | +0.04 [-0.29, 0.38] ~ |
| `C2c:0.9/10` | **family-dependent** | 3/4 | 1/4 | -0.49 [-0.74, -0.23] ✓ | +0.06 [-0.11, 0.26] ✗ | -0.02 [-0.10, 0.07] ~ | -0.12 [-0.28, 0.02] ~ | -0.10 [-0.29, 0.06] ~ |
| `C2d:0.9/10` | **directional** | 4/4 | 3/4 | -1.00 [-1.47, -0.59] ✓ | -0.37 [-0.72, 0.03] ~ | -1.53 [-1.90, -1.15] ✓ | -0.93 [-1.41, -0.48] ✓ | -0.88 [-1.38, -0.35] ✓ |
| `C2e:0.9/10` | **directional** | 4/4 | 2/4 | -0.40 [-0.85, 0.01] ~ | -0.38 [-0.78, 0.06] ~ | -1.95 [-2.40, -1.53] ✓ | -0.84 [-1.39, -0.29] ✓ | -1.09 [-1.63, -0.52] ✓ |
| `C2b:0.7/30` | **supported** | 4/4 | 4/4 | +1.16 [0.09, 2.23] ✓ | +5.43 [3.78, 7.00] ✓ | +0.62 [0.08, 1.17] ✓ | +1.06 [0.32, 1.86] ✓ | +0.54 [-0.38, 1.46] ~ |
| `C2c:0.7/30` | **family-dependent** | 3/4 | 2/4 | -0.48 [-1.13, 0.27] ~ | -1.17 [-2.06, -0.30] ✓ | +0.08 [-0.19, 0.40] ✗ | -0.80 [-1.43, -0.23] ✓ | -0.81 [-1.46, -0.26] ✓ |
| `C2d:0.7/30` | **directional** | 4/4 | 3/4 | -0.89 [-2.17, 0.37] ~ | -2.04 [-3.39, -0.86] ✓ | -1.48 [-2.44, -0.56] ✓ | -1.26 [-2.37, -0.23] ✓ | -0.21 [-1.49, 1.12] ~ |
| `C2e:0.7/30` | **directional** | 4/4 | 1/4 | -0.42 [-1.95, 0.95] ~ | -0.34 [-1.86, 1.01] ~ | -2.79 [-3.77, -1.69] ✓ | -0.88 [-2.14, 0.45] ~ | +0.19 [-1.39, 1.58] ✗ |
| `C3:0.9/30` | **family-dependent** | 3/4 | 3/4 | +3.40 [2.05, 4.96] ✓ | +0.99 [0.13, 1.79] ✓ | -0.07 [-1.17, 0.95] ✗ | +1.74 [0.44, 3.13] ✓ | +0.89 [-0.33, 2.15] ~ |
| `C3:0.9/10` | **family-dependent** | 2/4 | 1/4 | +0.60 [0.16, 1.10] ✓ | -0.01 [-0.30, 0.25] ✗ | -0.42 [-0.78, -0.08] ✗ | +0.09 [-0.35, 0.54] ~ | -0.21 [-0.66, 0.22] ✗ |
| `C3:0.7/30` | **family-dependent** | 3/4 | 1/4 | +0.47 [-0.56, 1.61] ~ | +1.71 [0.68, 2.98] ✓ | -1.31 [-2.34, -0.37] ✗ | +0.38 [-0.86, 1.54] ~ | +0.40 [-0.87, 1.74] ~ |
| `C8:0.9/30` | **family-dependent** | 3/4 | 3/4 | +6.17 [4.49, 7.79] ✓ | +4.33 [2.71, 6.08] ✓ | -1.40 [-2.84, 0.28] ✗ | +5.67 [3.75, 7.36] ✓ | +2.37 [0.84, 4.22] ✓ |
| `C4b:0.9/10` | **supported** | 4/4 | 4/4 | -0.86 [-1.47, -0.34] ✓ | -1.82 [-2.38, -1.30] ✓ | -3.46 [-4.03, -2.87] ✓ | -1.41 [-1.99, -0.86] ✓ | -2.65 [-3.21, -2.05] ✓ |
| `C4b:0.9/30` | **family-dependent** | 2/4 | 2/4 | +3.09 [1.53, 4.65] ✗ | -1.19 [-2.43, -0.04] ✓ | -2.34 [-3.85, -1.02] ✓ | +3.34 [1.64, 4.94] ✗ | +1.21 [-0.34, 3.05] ✗ |

* `C2a` (directional): **EVSI as built costs more than the incumbent where
  checks are strong**, by +0.19 to +5.85 minutes at 0.9/30. The CI is above 0
  in three families; in `nrm` the difference is +0.19 [−1.10, 1.55].
* `C2b` (**supported** at 0.9/30, 0.9/10 and 0.7/30): **the flip abstention is
  the cause.** Ignoring it saves 1.28–7.21 minutes per episode at 0.9/30,
  0.22–1.03 at 0.9/10 and 0.62–5.43 at 0.7/30, with every family's CI above 0.
  At 0.9/30, `rank_feasible` abstains on a downstream-action flip (one
  ensemble member's best action changes after some answer) in 50–287 of 400
  episodes, each time where its robust value had already cleared the cost.
  It still holds with the system calibrated to the wrong family (§4.5).
* `C2c` (family-dependent): **the 2–3 check lookahead** saves 1.00–2.59 minutes
  over the one-step rule at 0.9/30 in `lca`, `cdm` and `lta`, and nothing in
  `nrm` (+0.03 [−0.45, 0.54]; +0.08 at 0.7/30). In these three regimes it
  never costs a measurable minute (inside the package it costs +0.18 in one
  weak-check cell, `A3` in §5). In `nrm` the one-step rule already stops near the best: checks there
  carry the least decision value (minutes per nat, §4.6).
* `C2d` (directional at all three regimes): the lookahead beats the incumbent
  in every family, by 0.37–3.10 minutes, with the CI below 0 in three of four
  families each time.
* `C2e` (family-dependent): against the same caps without the gate, the
  lookahead is no reliable improvement at 0.9/30 (`lca` +0.31, `lta` +0.03).
  Fixed caps of four checks happen to suit strong checks at 30-minute stakes.
  The lookahead is near the best everywhere, not only there (§4.4).
* `C3` (family-dependent): **the robust completion gate's cost is the
  single-family study's family speaking.** At 0.9/30 the gate costs +3.40
  minutes in `lca` (the study's 3.7), +0.99 in `cdm`, +1.74 in `lta` and
  nothing in `nrm` (−0.07). At 0.9/10 it costs minutes only in `lca`, and
  *saves* them in `nrm` (−0.42). Together with `C3w`, the gate helps where
  checks are weak and hurts where they are strong, by an amount the families
  do not agree on.
* `C8` (family-dependent): the EIG path's 90% agreement gate costs 4.3–6.2
  minutes at 0.9/30 in three families and saves 1.4 in `nrm`.
* `C4b` at 0.9: loss-derived EVSI beats the nat-scaled EIG rule at 0.9/10 in
  every family (supported). At 0.9/30 the nat-scaled rule wins in `lca` and
  `lta` (+3.09, +3.34): it over-measures, and at 30-minute repairs
  over-measuring beats the one-step rule's under-measuring.

### 4.4 Which policy wins, by how much, and how robustly

Per regime: each family's winner (lowest mean minutes per episode), top-1
agreement, the rank agreement of all 14 arms (Kendall's τ-b, mean and minimum
over the six family pairs), the arms that no family can distinguish from its
best (paired 95% CI), and the most a family loses by acting on another
family's winner:

| Regime | `lca` winner (min) | `cdm` winner (min) | `nrm` winner (min) | `lta` winner (min) | Top-1 agreement | Kendall τ mean (min) | In every family's co-winners | Max regret of acting on another family's winner |
|---|---|---|---|---|---|---|---|---:|
| fitted/3 | `evsi` (1.75) | `evsi` (2.48) | `eig` (1.18) | `evsi` (1.72) | 3/4 | 0.91 (0.83) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.08 |
| fitted/10 | `evsi` (5.83) | `voi_p_with_fallback` (8.23) | `voi_p_with_fallback` (3.90) | `evsi` (5.72) | 2/4 | 0.76 (0.62) | `evsi`, `evsi_lcb_only`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_successor` | 0.03 |
| fitted/30 | `evsi_lcb_only` (17.32) | `evsi_lookahead` (23.94) | `evsi_lcb_only` (11.66) | `evsi` (17.18) | 2/4 | 0.54 (0.35) | `voi_p_with_fallback`, `voi_successor` | 0.81 |
| 0.7/3 | `evsi` (1.73) | `evsi` (2.25) | `eig` (1.18) | `evsi` (1.70) | 3/4 | 0.84 (0.68) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.17 |
| 0.7/10 | `evsi_lcb_only` (5.52) | `evsi_lookahead` (6.71) | `evsi_lcb_only` (3.86) | `voi_p_with_fallback` (5.44) | 2/4 | 0.68 (0.42) | `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed` | 0.21 |
| 0.7/30 | `eig_no_gate` (15.15) | `evsi_lookahead` (15.90) | `evsi_lcb_only` (11.08) | `voi_p_with_fallback` (14.94) | 1/4 | 0.43 (0.19) | `evsi_lookahead`, `voi_p_with_fallback`, `voi_proposed` | 4.89 |
| 0.9/3 | `evsi` (1.70) | `voi_p_with_fallback` (1.92) | `evsi_lcb_only` (1.17) | `evsi` (1.65) | 2/4 | 0.83 (0.75) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.04 |
| 0.9/10 | `evsi_lookahead` (4.73) | `voi_p_with_fallback` (5.25) | `voi_p_with_fallback` (3.65) | `voi_p_with_fallback` (4.82) | 3/4 | 0.71 (0.55) | `evsi_lookahead`, `voi_p_with_fallback`, `voi_proposed` | 0.18 |
| 0.9/30 | `eig_no_gate` (9.54) | `voi_p_with_fallback` (10.55) | `voi_successor` (10.27) | `eig_no_gate` (10.02) | 2/4 | 0.43 (0.09) | `evsi_lookahead`, `voi_p_with_fallback`, `voi_proposed` | 3.86 |

* **Where checks are weak or cheap to skip** (the fitted strength with 3- or
  10-minute repairs, and repair 3 at any strength), every value rule stops and
  the rules tie. The families rank the
  arms alike (τ 0.76–0.91), and acting on another family's winner costs at most
  0.17 minutes.
* **Where checks are strong and the stakes high** (0.7/30, 0.9/30), the
  families disagree about the winner (1/4 and 2/4), their rankings decorrelate
  (τ 0.43, minimum 0.09–0.19), and acting on another family's winner costs up
  to 3.9–4.9 minutes per episode. This is exactly where the single-family study
  drew its strongest policy conclusions, and where one family's verdict is
  least safe.
* Two arms are among every family's co-winners at 0.7/30, 0.9/10 and 0.9/30:
  the lookahead-based `evsi_lookahead` and the proposed package
  (`voi_proposed`). The package with the successor's nat-scaled fallback kept
  (`voi_p_with_fallback`) is the only arm among every family's co-winners in
  all nine regimes; it and the package are indistinguishable (`A2`, §5).

**RankCert's robust choice.** When the families disagree, ship the policy
whose worst case is least bad. Each arm's regret (its mean minutes minus the
cell's best) in every family × regime cell (36 fitted cells; the
`lta_reveal` stress world reported apart):

| Rank | Policy | Worst-case regret (min/episode) | Where | Mean regret | Cells within 0.1 min of the best | max `lca` | max `cdm` | max `nrm` | max `lta` | Stress worst (cell) |
|---:|---|---:|---|---:|---|---:|---:|---:|---:|---|
| 1 | `voi_proposed` | 1.21 | lta 0.9/30 | 0.11 | 28/36 | 0.62 | 0.37 | 0.12 | 1.21 | 0.34 (lta_reveal fitted/30) |
| 2 | `voi_p_with_fallback` | 1.27 | lta 0.9/30 | 0.10 | 28/36 | 0.52 | 0.31 | 0.33 | 1.27 | 0.42 (lta_reveal fitted/30) |
| 3 | `evsi_lookahead` | 1.38 | lta 0.9/30 | 0.11 | 28/36 | 0.50 | 0.39 | 0.12 | 1.38 | 0.37 (lta_reveal 0.9/30) |
| 4 | `voi_p_one_step` | 3.33 | lta 0.9/30 | 0.34 | 26/36 | 3.09 | 1.39 | 0.09 | 3.33 | 2.15 (lta_reveal 0.9/30) |
| 5 | `evsi_lcb_only` | 3.34 | lta 0.9/30 | 0.34 | 26/36 | 3.09 | 1.39 | 0.09 | 3.34 | 2.15 (lta_reveal 0.9/30) |
| 6 | `incumbent` | 3.60 | lca 0.9/30 | 1.72 | 0/36 | 3.60 | 2.75 | 2.46 | 3.10 | 1.77 (lta_reveal fitted/3) |
| 7 | `caps_only` | 3.73 | nrm fitted/30 | 2.15 | 0/36 | 3.28 | 3.44 | 3.73 | 3.35 | 2.96 (lta_reveal fitted/3) |
| 8 | `voi_p_with_gate` | 3.76 | lta 0.9/30 | 0.38 | 24/36 | 3.13 | 2.22 | 0.42 | 3.76 | 1.83 (lta_reveal 0.9/30) |
| 9 | `voi_successor` | 3.86 | lca 0.9/30 | 0.42 | 24/36 | 3.86 | 2.19 | 0.14 | 3.24 | 2.06 (lta_reveal 0.9/30) |
| 10 | `max_entropy` | 6.64 | lta 0.9/30 | 3.20 | 0/36 | 6.59 | 5.33 | 3.86 | 6.64 | 4.13 (lta_reveal 0.9/30) |
| 11 | `eig` | 6.91 | cdm 0.9/30 | 0.96 | 16/36 | 6.17 | 6.91 | 1.03 | 5.67 | 3.31 (lta_reveal 0.9/30) |
| 12 | `random` | 6.92 | cdm 0.9/30 | 3.30 | 0/36 | 5.75 | 6.92 | 2.85 | 5.45 | 2.98 (lta_reveal fitted/3) |
| 13 | `eig_no_gate` | 8.15 | cdm fitted/3 | 4.25 | 3/36 | 6.59 | 8.15 | 6.67 | 6.78 | 6.43 (lta_reveal fitted/3) |
| 14 | `evsi` | 8.60 | cdm 0.9/30 | 1.13 | 18/36 | 7.49 | 8.60 | 1.37 | 6.29 | 3.33 (lta_reveal 0.9/30) |

**The proposed package has the smallest worst-case regret of the 14 arms: 1.21
minutes per episode** (worst cell `lta` 0.9/30). It is within 0.1 minutes of
the best in 28 of 36 cells, and its stress worst is 0.34. Today's incumbent
is never within 0.1 minutes of the best (0/36; mean regret 1.72, worst 3.60).
The successor as built improves the mean (0.42) but not the worst case
(3.86, `lca` 0.9/30). EVSI as built is the worst value rule (8.60).

### 4.5 The system calibrated to the wrong family (rotation)

Every truth family × every other family's calibrated system (12 cells per
regime): does the conclusion survive a mis-calibrated system?

| Claim @ regime | Verdict | Cells holding | Cells certified | Effect range (minutes) | Cells against (truth ← system: effect [CI]) |
|---|---|---|---|---|---|
| `evsi_lookahead-incumbent@fitted/3` | **supported** | 12/12 | 12/12 | -2.11 to -1.93 |  |
| `evsi_lookahead-incumbent@0.9/10` | **directional** | 12/12 | 7/12 | -1.79 to -0.17 |  |
| `evsi_lookahead-incumbent@0.9/30` | **family-dependent** | 7/12 | 6/12 | -3.69 to +1.01 | lca←nrm: +0.98 [-0.20, 2.09]; cdm←nrm: +0.68 [-0.46, 1.87]; cdm←lta: +0.69 [-0.50, 1.95]; nrm←cdm: +1.01 [-0.25, 2.22]; lta←nrm: +0.42 [-1.15, 1.80] |
| `evsi-evsi_lcb_only@fitted/3` | **no difference** | 0/12 | 0/12 | +0.00 to +0.00 | 12 cells |
| `evsi-evsi_lcb_only@0.9/10` | **directional** | 12/12 | 7/12 | +0.00 to +1.67 |  |
| `evsi-evsi_lcb_only@0.9/30` | **directional** | 12/12 | 9/12 | +0.45 to +7.50 |  |
| `incumbent-caps_only@fitted/3` | **contradicted** | 0/12 | 0/12 | -1.75 to -0.86 | 12 cells |
| `incumbent-caps_only@0.9/10` | **family-dependent** | 7/12 | 1/12 | -1.00 to +0.50 | cdm←lca: -0.04 [-0.42, 0.29]; cdm←nrm: -0.71 [-1.11, -0.31]; nrm←lca: -0.88 [-1.26, -0.52]; nrm←cdm: -1.00 [-1.37, -0.62]; nrm←lta: -0.59 [-0.98, -0.28] |
| `incumbent-caps_only@0.9/30` | **family-dependent** | 8/12 | 8/12 | -1.55 to +3.02 | cdm←nrm: -0.71 [-1.85, 0.45]; nrm←lca: -0.97 [-2.08, 0.10]; nrm←cdm: -1.55 [-2.63, -0.43]; nrm←lta: -0.34 [-1.49, 0.53] |
| `evsi-incumbent@fitted/3` | **contradicted** | 0/12 | 0/12 | -2.11 to -1.93 | 12 cells |
| `evsi-incumbent@0.9/10` | **family-dependent** | 6/12 | 3/12 | -1.85 to +1.47 | lca←nrm: -0.21 [-0.66, 0.24]; nrm←lca: -1.85 [-2.40, -1.31]; nrm←cdm: -0.88 [-1.30, -0.45]; nrm←lta: -1.69 [-2.16, -1.19]; lta←lca: -0.41 [-1.06, 0.21]; lta←nrm: -0.21 [-0.71, 0.34] |
| `evsi-incumbent@0.9/30` | **family-dependent** | 10/12 | 10/12 | -1.46 to +8.57 | nrm←lca: -1.46 [-3.10, 0.14]; nrm←lta: -0.99 [-2.33, 0.47] |
| `voi_proposed-voi_successor@fitted/3` | **no difference** | 0/12 | 0/12 | +0.00 to +0.00 | 12 cells |
| `voi_proposed-voi_successor@0.9/10` | **family-dependent** | 6/12 | 1/12 | -0.55 to +0.64 | lca←nrm: +0.10 [-0.05, 0.24]; cdm←lta: +0.03 [-0.14, 0.20]; nrm←lca: +0.16 [-0.13, 0.42]; nrm←cdm: +0.64 [0.31, 0.98]; nrm←lta: +0.10 [-0.15, 0.34]; lta←nrm: +0.19 [0.03, 0.37] |
| `voi_proposed-voi_successor@0.9/30` | **family-dependent** | 9/12 | 9/12 | -3.44 to +1.35 | nrm←lca: +0.14 [-0.92, 1.25]; nrm←cdm: +1.35 [0.20, 2.65]; nrm←lta: +0.21 [-0.86, 1.21] |

* The two `contradicted` rows at the fitted strength are the expected
  direction there (`C3w`, `C7`): the gate and EVSI as built save minutes
  where checks are weak, under every mis-calibrated system too.
* **The flip abstention costs minutes even under the wrong model**: in all 12
  cells at 0.9/10 and 0.9/30 (directional; 7 and 9 of 12 certified).
* The lookahead beats the incumbent in all 12 cells at the fitted strength
  and at 0.9/10. At 0.9/30 it fails in 5 of 12 cells, every one involving
  `nrm` (as truth or system) or `cdm`'s truth with `lta`'s system; none of
  those is certified against it.
* The gate's cost stays family-dependent: with `nrm` as the truth, the gate
  saves minutes whatever system is calibrated.
* The package against the successor as built: no difference at the fitted
  strength. At 0.9/30 it holds in 9 of 12 cells (9 certified); the three cells
  against it all have `nrm` as the truth (the worst +1.35 [0.20, 2.65], with
  `cdm`'s system). At 0.9/10 the comparison is mixed (6 of 12 cells, effects
  −0.55 to +0.64).


### 4.6 `VALUE_PER_NAT_MINUTES` = 60

Realized minutes per nat: the slope of a check's realized value on its
predicted EIG, under the family's calibrated model, on the incumbent's and
caps_only's checks:

| Regime | `lca` incumbent / caps_only | `cdm` incumbent / caps_only | `nrm` incumbent / caps_only | `lta` incumbent / caps_only |
|---|---|---|---|---|
| fitted/3 | -0.03 / 0.14 | 0.72 / 0.70 | -0.23 / -0.23 | 0.05 / -0.01 |
| fitted/10 | -0.09 / 0.46 | 2.39 / 2.35 | -0.76 / -0.78 | 0.17 / -0.03 |
| fitted/30 | -0.27 / 1.39 | 7.17 / 7.04 | -2.28 / -2.34 | 0.50 / -0.09 |
| 0.7/3 | 0.85 / 0.92 | 1.54 / 1.59 | 0.49 / 0.23 | 0.68 / 0.79 |
| 0.7/10 | 2.83 / 3.07 | 5.13 / 5.30 | 1.62 / 0.77 | 2.26 / 2.62 |
| 0.7/30 | 8.48 / 9.21 | 15.40 / 15.89 | 4.86 / 2.30 | 6.79 / 7.87 |
| 0.9/3 | 1.16 / 1.43 | 1.39 / 1.39 | 0.70 / 0.69 | 1.03 / 1.18 |
| 0.9/10 | 3.87 / 4.76 | 4.63 / 4.63 | 2.33 / 2.31 | 3.42 / 3.92 |
| 0.9/30 | 11.62 / 14.29 | 13.89 / 13.89 | 6.99 / 6.92 | 10.27 / 11.75 |

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C4` | **directional** | 4/4 | 2/4 | +14.29 [11.64, 17.07] ~ | +15.89 [12.15, 19.24] ~ | +6.99 [2.16, 11.15] ✓ | +11.75 [8.78, 14.24] ✓ |  |
| `C6:value_per_nat_minutes=10` | **supported** | 4/4 | 4/4 | -1.56 [-1.91, -1.13] ✓ | -2.07 [-2.52, -1.64] ✓ | -2.81 [-3.46, -2.29] ✓ | -1.62 [-2.01, -1.21] ✓ |  |

`robust_composition.VALUE_PER_NAT_MINUTES`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` eig/eig_no_gate | `cdm` eig/eig_no_gate | `nrm` eig/eig_no_gate | `lta` eig/eig_no_gate |
|---|---|---|---|---|
| 1 | 5.90 (+0.27 [0.01, 0.57]) / 5.90 (-0.47 [-1.18, 0.31]) | 6.33 (+0.30 [-0.04, 0.66]) / 6.33 (-0.73 [-1.45, -0.03]) | 4.00 (+0.11 [0.01, 0.24]) / 4.00 (-3.19 [-4.02, -2.40]) | 5.63 (+0.16 [-0.07, 0.43]) / 5.63 (-0.84 [-1.56, -0.08]) |
| 2.5 | 5.94 (+0.31 [0.04, 0.61]) / 5.74 (-0.63 [-1.32, 0.22]) | 6.24 (+0.21 [-0.05, 0.48]) / 5.87 (-1.19 [-1.92, -0.43]) | 3.90 (+0.01 [-0.04, 0.09]) / 3.77 (-3.41 [-4.17, -2.67]) | 5.63 (+0.16 [-0.05, 0.38]) / 5.61 (-0.86 [-1.56, -0.06]) |
| 5 | 5.61 (-0.02 [-0.03, -0.00]) / 4.75 (-1.62 [-2.20, -0.98]) | 6.01 (-0.03 [-0.09, 0.04]) / 4.74 (-2.32 [-2.85, -1.83]) | 3.88 (-0.01 [-0.02, 0.00]) / 3.86 (-3.33 [-4.00, -2.70]) | 5.46 (-0.01 [-0.02, 0.00]) / 5.00 (-1.47 [-2.03, -0.85]) |
| 10 | 5.61 (-0.01 [-0.03, -0.00]) / 4.81 (-1.56 [-1.91, -1.13]) | 5.98 (-0.05 [-0.08, -0.03]) / 4.99 (-2.07 [-2.52, -1.64]) | 3.88 (-0.01 [-0.02, 0.00]) / 4.38 (-2.81 [-3.46, -2.29]) | 5.46 (-0.01 [-0.02, 0.00]) / 4.85 (-1.62 [-2.01, -1.21]) |
| 20 | 5.62 (-0.01 [-0.02, 0.00]) / 5.29 (-1.08 [-1.31, -0.85]) | 6.00 (-0.03 [-0.06, -0.02]) / 5.90 (-1.16 [-1.44, -0.89]) | 3.88 (-0.01 [-0.02, 0.00]) / 5.31 (-1.88 [-2.37, -1.41]) | 5.46 (-0.01 [-0.02, 0.00]) / 5.41 (-1.06 [-1.30, -0.83]) |
| 40 | 5.62 (-0.00 [-0.01, 0.00]) / 6.09 (-0.28 [-0.35, -0.20]) | 6.02 (-0.01 [-0.03, -0.00]) / 6.70 (-0.36 [-0.51, -0.19]) | 3.89 (+0.00 [0.00, 0.00]) / 6.62 (-0.57 [-0.84, -0.36]) | 5.46 (-0.01 [-0.02, 0.00]) / 6.07 (-0.40 [-0.50, -0.32]) |
| 60 (current) | 5.63 / 6.37 | 6.04 / 7.06 | 3.89 / 7.19 | 5.47 / 6.47 |
| 120 | 5.64 (+0.01 [0.00, 0.03]) / 7.11 (+0.74 [0.61, 0.88]) | 6.05 (+0.01 [0.00, 0.03]) / 8.25 (+1.19 [0.83, 1.60]) | 3.90 (+0.01 [0.00, 0.02]) / 8.41 (+1.22 [0.94, 1.56]) | 5.48 (+0.01 [0.00, 0.02]) / 7.29 (+0.82 [0.68, 0.99]) |

* `C4` (directional): **60 is above every measured minutes-per-nat in every
  family**: 3.8–8.6 times the largest one anywhere (`cdm` 15.9 at 0.7/30,
  `lca` 14.3 at 0.9/30, `lta` 11.8, `nrm` 7.0). Under the strict test (60 ≥ 4×
  the largest value's upper CI) it is certified in `nrm` and `lta` only. At
  the fitted strength, measured minutes per nat are below 1.4 in three
  families (negative in `nrm`) and up to 7.2 in `cdm`. A nat is worth about
  0.23–0.48 × the repair minutes at consistency 0.9 (`nrm` 0.23, `lta`
  0.34–0.39, `lca` 0.39–0.48, `cdm` 0.46). The single-family "0.4–0.5 × repair" is again
  `lca`'s value; no constant fits every regime.
* `C6:value_per_nat_minutes=10` (**supported**): lowering the scale to 10
  saves 1.56–2.81 minutes per episode on the gate-free EIG rule at 0.9/10
  in every family. Each family's best value is 2.5–10, and **5 has the
  smallest worst-case regret across families** (0.15 minutes, against 0.61
  at 10 and 1.13 at 2.5); 5 also saves minutes with the CI below 0 in every
  family. With the agreement gate on, the scale hardly matters (|Δ| ≤ 0.31).

### 4.7 Part C: charging the measured unresolved cost

`U` = Eedi's excess repeat rate 0.148 × encounters × 2 minutes per repeated
error. Paired Δ = measured − minutes-only, for `evsi_lookahead` (the
`evsi_lcb_only` rows agree):

| Strength | Encounters | U (min) | `lca` lookahead Δ [CI] (checks) | `cdm` lookahead Δ [CI] (checks) | `nrm` lookahead Δ [CI] (checks) | `lta` lookahead Δ [CI] (checks) |
|---|---:|---:|---|---|---|---|
| fitted | 3 | 0.89 | -0.05 [-0.11, 0.01] (0.00→0.00) | -0.04 [-0.09, 0.02] (0.00→0.00) | +0.01 [0.00, 0.02] (0.00→0.00) | +0.00 [-0.03, 0.04] (0.00→0.00) |
| fitted | 6 | 1.78 | -0.01 [-0.10, 0.09] (0.00→0.00) | -0.04 [-0.14, 0.06] (0.00→0.00) | +0.01 [-0.03, 0.05] (0.00→0.00) | +0.00 [-0.05, 0.06] (0.00→0.00) |
| fitted | 12 | 3.55 | -0.25 [-0.46, -0.01] (0.00→0.00) | -0.09 [-0.29, 0.13] (0.00→0.00) | -0.02 [-0.10, 0.06] (0.00→0.00) | +0.01 [-0.11, 0.14] (0.00→0.00) |
| fitted | 24 | 7.10 | -0.57 [-1.04, -0.11] (0.00→0.03) | -0.68 [-1.10, -0.25] (0.00→0.01) | +0.04 [-0.15, 0.21] (0.00→0.01) | -0.18 [-0.52, 0.14] (0.00→0.01) |
| 0.9 | 3 | 0.89 | -0.05 [-0.14, 0.07] (0.07→0.17) | +0.03 [-0.03, 0.10] (0.05→0.11) | +0.01 [-0.02, 0.04] (0.00→0.02) | -0.01 [-0.09, 0.07] (0.04→0.16) |
| 0.9 | 6 | 1.78 | -0.11 [-0.27, 0.06] (0.07→0.24) | -0.06 [-0.18, 0.04] (0.05→0.19) | -0.04 [-0.11, 0.02] (0.00→0.04) | -0.06 [-0.19, 0.11] (0.04→0.26) |
| 0.9 | 12 | 3.55 | -0.53 [-0.80, -0.25] (0.07→0.46) | -0.25 [-0.47, -0.04] (0.05→0.44) | -0.22 [-0.37, -0.07] (0.00→0.14) | -0.25 [-0.49, -0.02] (0.04→0.43) |
| 0.9 | 24 | 7.10 | -1.54 [-2.05, -1.09] (0.07→0.86) | -1.18 [-1.63, -0.79] (0.05→0.89) | -0.55 [-0.88, -0.26] (0.00→0.28) | -1.28 [-1.69, -0.77] (0.04→1.09) |

`C5`'s value is the smallest `U` whose CI is below 0 at consistency 0.9; its
CI column is the `U` = 7.10 row's:

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C5` | **supported** | 4/4 | 4/4 | +3.55 [-2.05, -1.09] ✓ | +3.55 [-1.63, -0.79] ✓ | +3.55 [-0.88, -0.26] ✓ | +3.55 [-1.69, -0.77] ✓ |  |

* `C5` (**supported**): at consistency 0.9, charging the true `U` saves
  minutes in every family once it reaches 3.55 minutes (0.22–0.53 at 3.55,
  0.55–1.54 at 7.10). Below that nothing is distinguishable from 0, and it
  never costs more than 0.01 minutes. This confirms the single-family "pays off
  above ~3.6". At the fitted strength it pays only in `lca` (from 3.55)
  and `cdm` (at 7.10).

### 4.8 The robustness knobs

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C6a` | **family-dependent** | 3/4 | 1/4 | 8/8 under; q25 closer 6/8 ~ | 8/8 under; q25 closer 5/8 ~ | 0/5 under; q25 closer 0/5 ✗ | 6/6 under; q25 closer 6/6 ✓ |  |
| `C6:robust_quantile=0.25` | **directional** | 4/4 | 1/4 | -0.05 [-0.24, 0.17] ~ | -0.40 [-0.70, -0.13] ✓ | -0.01 [-0.12, 0.09] ~ | +0.00 [-0.25, 0.26] ~ |  |
| `C6:perturbation_delta=0.1` | **family-dependent** | 3/4 | 0/4 | -0.05 [-0.14, 0.02] ~ | -0.02 [-0.09, 0.02] ~ | +0.04 [0.00, 0.12] ✗ | -0.09 [-0.18, 0.00] ~ |  |
| `C6:burden_cost=0.5` | **family-dependent** | 1/4 | 0/4 | +0.23 [-0.01, 0.54] ✗ | -0.10 [-0.32, 0.12] ~ | +0.11 [-0.09, 0.31] ✗ | +0.19 [-0.02, 0.38] ✗ |  |
| `C6:repair_minutes=10` | **directional** | 4/4 | 3/4 | -1.01 [-1.52, -0.54] ✓ | -0.81 [-1.36, -0.30] ✓ | -0.26 [-0.54, 0.02] ~ | -0.69 [-1.09, -0.30] ✓ |  |
| `C6:instrument_concentration=4` | **family-dependent** | 2/4 | 0/4 | -0.27 [-0.69, 0.17] ~ | -0.26 [-0.65, 0.09] ~ | +0.03 [-0.16, 0.25] ✗ | +0.01 [-0.38, 0.38] ✗ |  |

* `ROBUST_QUANTILE` 0.10 → 0.25 (directional): it never costs minutes and
  saves 0.40 in `cdm` (`evsi_lookahead`). On `evsi_lcb_only` it saves 0.33
  in `lca` and 0.34 in `cdm`, and changes nothing in `nrm` or `lta` (sweep in
  Appendix B). Whether the 10th percentile under-predicts the value checks
  realize is **family-dependent** (`C6a`): yes in every cell with value in
  `lca`, `cdm` and `lta` (8/8, 8/8, 6/6), no in `nrm` (0/5). In `nrm` the
  mis-specified single-cause system *over*-predicts value, and a lower
  quantile is the right correction there.
* `PERTURBATION_DELTA` 0.15 → 0.10: no decision effect in any family
  (|Δ| ≤ 0.09 minutes, every CI touching 0). Delta only feeds the flip
  abstention, which §4.3 removes anyway, and on `evsi_lcb_only` and
  `evsi_lookahead` every delta gives identical episodes.
* `BURDEN_COST` > 0 costs the lookahead minutes: +0.11 to +0.23 at 0.5 in
  three families (`cdm` −0.10), and +0.27 to +0.92 at 2 in every family. Keep
  it at 0.
* Assumed repair minutes: knowing the true 10 instead of the default 3 saves
  0.26–1.01 minutes for the lookahead (directional; `nrm`'s CI touches 0).
  Assuming 20 does as well or better in every family: the under-probing of
  §4.3 shows through, so this is no reason to mis-state the cost.
* Assumed check minutes: the causal selector's 1.5 instead of the true 1
  costs the lookahead +0.10 to +0.59. `INSTRUMENT_PERTURBATION_CONCENTRATION`
  and the ensemble draw count move nothing consistently.

### 4.9 `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 → 2

A stream of 400 episodes per family and regime in which the system starts
from the hand-set card and folds every check into the card's
posterior-weighted counts. Log loss per check of the realized answers /
realized information about the truth per check (nats); the last column is
`C6c`'s per-check log-loss difference (each arm's loss over its own checks):

| Family | Regime | hand-set (frozen) | 0.5 | 2 | 8 (current) | 32 | family's rows (target) | 2 − 8 log loss [CI] |
|---|---|---|---|---|---|---|---|---|
| `lca` | 0.9/10 | 1.271 / +0.106 | 1.103 / +0.235 | 1.096 / +0.228 | 1.103 / +0.223 | 1.110 / +0.212 | 1.059 / +0.268 | -0.0073 [-0.0256, 0.0114] |
| `lca` | fitted/3 | 1.349 / -0.107 | 1.171 / +0.031 | 1.179 / +0.064 | 1.186 / +0.070 | 1.187 / +0.051 | 1.143 / +0.093 | -0.0069 [-0.0299, 0.0122] |
| `cdm` | 0.9/10 | 1.301 / +0.271 | 1.022 / +0.279 | 1.010 / +0.271 | 1.018 / +0.271 | 1.024 / +0.281 | 0.970 / +0.274 | -0.0090 [-0.0324, 0.0127] |
| `cdm` | fitted/3 | 1.375 / -0.144 | 1.104 / +0.050 | 1.098 / +0.042 | 1.086 / +0.007 | 1.094 / -0.012 | 1.075 / +0.092 | +0.0127 [-0.0091, 0.0350] |
| `nrm` | 0.9/10 | 1.261 / -0.081 | 1.079 / +0.098 | 1.089 / +0.099 | 1.066 / +0.091 | 1.080 / +0.064 | 0.993 / +0.115 | +0.0227 [-0.0061, 0.0568] |
| `nrm` | fitted/3 | 1.321 / -0.146 | 1.126 / +0.011 | 1.079 / -0.140 | 1.054 / -0.228 | 1.097 / -0.058 | 1.031 / +0.020 | +0.0257 [-0.0034, 0.0557] |
| `lta` | 0.9/10 | 1.271 / +0.154 | 1.175 / +0.202 | 1.146 / +0.244 | 1.134 / +0.239 | 1.127 / +0.232 | 1.125 / +0.277 | +0.0112 [-0.0037, 0.0279] |
| `lta` | fitted/3 | 1.378 / -0.080 | 1.241 / +0.053 | 1.199 / +0.058 | 1.184 / +0.072 | 1.194 / +0.046 | 1.169 / +0.095 | +0.0146 [-0.0074, 0.0369] |

* **Not supported.** After the fix to `C6c`'s bootstrap (§8), no family×regime
  row shows a log-loss difference between 2 and 8 that its CI separates from
  0. Pseudo count 2 is ahead in 3 of 8 rows and 8 in 5. The single-family
  recommendation (2) was never simulated there; here it makes no measurable
  difference.
* **What matters is counting at all.** Any pseudo count from 0.5 to 32 takes
  the log loss from the frozen card's 1.26–1.38 to 1.01–1.24, most of the way
  to each family's calibrated rows (0.97–1.17). It also turns the card's
  negative information about the truth (−0.08 to −0.15 at the fitted
  strength) positive in most rows. The rest of the gap is structural: the
  card has three role rows shared across items, the families have per-item
  rows.

### 4.10 When the learner learns during probing

* **`lta` behaves like `lca` within an episode.** The fitted within-session
  transitions are near identity. `lta` agrees with `lca` in sign on 52 of
  58 paired claims; the six exceptions are effects under 0.35 minutes per
  episode, and `lta` certifies only one of them (`S4` at 0.9/30, −0.17).
* **The reveal stress (`lta_reveal`)**: each answer's reveal teaches at the
  between-session rates (a holder moves on with probability 0.07, an unsure
  learner comes to know with 0.23). Learners then drift toward knowing during
  the episode, and a further check is worth less. The claims about EVSI as
  built weaken there: the flip abstention's cost, the gate's cost and the
  hand-set checks' negative information are no longer certified. The
  successor as built is no better than today's serving at the fitted strength
  with 30-minute repairs (−0.12 [−1.00, 0.73]). **The package's advantages
  hold**: against the successor −1.78 [−3.17, −0.55] at 0.9/30, the gate
  costing +1.55 [0.36, 2.74] and the lookahead saving −1.87 [−3.09, −0.70]
  inside it, with a worst-case regret of 0.34 minutes.

## 5. The successor, as built and as proposed

Minutes per episode for the incumbent / `voi_successor` / `voi_proposed` /
`evsi_lookahead` (checks per episode in brackets):

| Regime | `lca` inc / succ / prop / look | `cdm` inc / succ / prop / look | `nrm` inc / succ / prop / look | `lta` inc / succ / prop / look | `lta_reveal` inc / succ / prop / look |
|---|---|---|---|---|---|
| fitted/3 | 3.69 / 1.75 / 1.75 / 1.75 (1.9/0.0/0.0/0.0) | 4.33 / 2.48 / 2.48 / 2.48 (2.0/0.0/0.0/0.0) | 3.19 / 1.18 / 1.18 / 1.18 (2.0/0.0/0.0/0.0) | 3.65 / 1.72 / 1.72 / 1.72 (1.9/0.0/0.0/0.0) | 3.30 / 1.53 / 1.53 / 1.53 (1.9/0.0/0.0/0.0) |
| fitted/10 | 7.75 / 5.83 / 5.86 / 5.86 (1.9/0.0/0.0/0.0) | 9.78 / 8.23 / 8.26 / 8.26 (2.0/0.0/0.0/0.0) | 6.02 / 3.90 / 3.92 / 3.92 (2.0/0.0/0.0/0.0) | 7.62 / 5.72 / 5.72 / 5.72 (1.9/0.0/0.0/0.0) | 6.47 / 5.10 / 5.10 / 5.10 (1.9/0.0/0.0/0.0) |
| fitted/30 | 19.35 / 17.71 / 17.50 / 17.50 (1.9/0.1/0.1/0.1) | 25.32 / 24.20 / 23.94 / 23.94 (2.0/0.1/0.2/0.2) | 14.12 / 11.66 / 11.67 / 11.67 (2.0/0.0/0.0/0.0) | 18.98 / 17.20 / 17.27 / 17.27 (1.9/0.0/0.0/0.0) | 15.52 / 15.40 / 15.32 / 15.32 (1.9/0.0/0.0/0.0) |
| 0.7/3 | 3.48 / 1.73 / 1.73 / 1.73 (2.0/0.0/0.0/0.0) | 3.70 / 2.25 / 2.25 / 2.25 (2.1/0.0/0.0/0.0) | 3.06 / 1.18 / 1.18 / 1.18 (2.0/0.0/0.0/0.0) | 3.48 / 1.70 / 1.70 / 1.70 (2.0/0.0/0.0/0.0) | 3.24 / 1.52 / 1.52 / 1.52 (2.0/0.0/0.0/0.0) |
| 0.7/10 | 6.83 / 5.55 / 5.53 / 5.53 (2.0/0.2/0.2/0.2) | 7.39 / 6.97 / 6.71 / 6.71 (2.1/0.6/0.6/0.6) | 5.54 / 3.88 / 3.86 / 3.86 (2.0/0.0/0.0/0.0) | 6.84 / 5.46 / 5.53 / 5.53 (2.0/0.2/0.2/0.2) | 6.06 / 5.03 / 4.98 / 4.98 (2.0/0.2/0.2/0.2) |
| 0.7/30 | 16.43 / 16.39 / 15.55 / 15.55 (2.0/0.3/0.7/0.7) | 17.94 / 18.09 / 15.90 / 15.90 (2.1/1.0/1.7/1.7) | 12.64 / 11.23 / 11.16 / 11.16 (2.0/0.1/0.2/0.2) | 16.45 / 15.69 / 15.19 / 15.19 (2.0/0.3/0.5/0.5) | 14.11 / 14.42 / 13.90 / 13.90 (2.0/0.3/0.5/0.5) |
| 0.9/3 | 3.14 / 1.73 / 1.74 / 1.74 (2.0/0.1/0.1/0.1) | 3.18 / 1.92 / 1.93 / 1.93 (2.1/0.1/0.1/0.1) | 3.01 / 1.17 / 1.17 / 1.17 (2.1/0.0/0.0/0.0) | 3.19 / 1.66 / 1.66 / 1.66 (2.1/0.0/0.0/0.0) | 3.13 / 1.50 / 1.51 / 1.51 (2.1/0.0/0.0/0.0) |
| 0.9/10 | 5.73 / 5.19 / 4.73 / 4.73 (2.0/0.3/0.6/0.6) | 5.80 / 5.31 / 5.43 / 5.43 (2.1/0.9/1.1/1.1) | 5.20 / 3.67 / 3.67 / 3.67 (2.1/0.1/0.2/0.2) | 5.76 / 4.93 / 4.83 / 4.83 (2.1/0.4/0.6/0.6) | 5.58 / 4.75 / 4.70 / 4.70 (2.1/0.3/0.6/0.6) |
| 0.9/30 | 13.13 / 13.39 / 10.16 / 10.04 (2.0/0.7/1.5/1.6) | 13.30 / 12.37 / 10.93 / 10.95 (2.1/1.3/1.9/1.9) | 11.45 / 10.27 / 10.39 / 10.39 (2.1/0.3/0.5/0.5) | 13.12 / 13.26 / 11.23 / 11.40 (2.1/0.7/1.5/1.5) | 12.58 / 13.17 / 11.39 / 11.48 (2.1/0.6/1.5/1.5) |

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `S1:fitted/3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.86 [-1.96, -1.74] ✓ | -2.01 [-2.08, -1.93] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `S2:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S3:fitted/3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.86 [-1.96, -1.74] ✓ | -2.01 [-2.08, -1.93] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `S4:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S1:fitted/30` | **supported** | 4/4 | 4/4 | -1.64 [-2.38, -1.00] ✓ | -1.12 [-1.95, -0.26] ✓ | -2.46 [-2.97, -1.92] ✓ | -1.78 [-2.29, -1.18] ✓ | -0.12 [-1.00, 0.73] ~ |
| `S2:fitted/30` | **family-dependent** | 2/4 | 0/4 | -0.21 [-0.69, 0.34] ~ | -0.26 [-0.67, 0.10] ~ | +0.01 [-0.23, 0.31] ✗ | +0.07 [-0.01, 0.23] ✗ | -0.07 [-0.30, 0.01] ~ |
| `S3:fitted/30` | **supported** | 4/4 | 4/4 | -1.84 [-2.61, -1.09] ✓ | -1.38 [-2.35, -0.51] ✓ | -2.45 [-3.05, -1.83] ✓ | -1.70 [-2.20, -1.11] ✓ | -0.20 [-1.10, 0.71] ~ |
| `S4:fitted/30` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S1:0.7/30` | **family-dependent** | 3/4 | 1/4 | -0.05 [-1.04, 1.10] ~ | +0.15 [-0.75, 1.13] ✗ | -1.42 [-2.20, -0.51] ✓ | -0.76 [-1.68, 0.23] ~ | +0.31 [-0.99, 1.49] ✗ |
| `S2:0.7/30` | **directional** | 4/4 | 2/4 | -0.84 [-1.71, -0.00] ✓ | -2.19 [-3.29, -1.00] ✓ | -0.07 [-0.55, 0.39] ~ | -0.50 [-1.13, 0.19] ~ | -0.52 [-1.23, 0.13] ~ |
| `S3:0.7/30` | **directional** | 4/4 | 3/4 | -0.89 [-2.17, 0.37] ~ | -2.04 [-3.39, -0.86] ✓ | -1.48 [-2.44, -0.56] ✓ | -1.26 [-2.37, -0.23] ✓ | -0.21 [-1.49, 1.12] ~ |
| `S4:0.7/30` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S1:0.9/10` | **supported** | 4/4 | 4/4 | -0.54 [-1.05, -0.08] ✓ | -0.49 [-0.79, -0.12] ✓ | -1.53 [-1.91, -1.14] ✓ | -0.83 [-1.32, -0.42] ✓ | -0.83 [-1.34, -0.32] ✓ |
| `S2:0.9/10` | **family-dependent** | 2/4 | 1/4 | -0.46 [-0.76, -0.18] ✓ | +0.12 [-0.14, 0.40] ✗ | +0.01 [-0.14, 0.15] ✗ | -0.10 [-0.34, 0.15] ~ | -0.05 [-0.33, 0.21] ~ |
| `S3:0.9/10` | **directional** | 4/4 | 3/4 | -1.00 [-1.47, -0.59] ✓ | -0.37 [-0.72, 0.03] ~ | -1.53 [-1.90, -1.15] ✓ | -0.93 [-1.41, -0.48] ✓ | -0.88 [-1.38, -0.35] ✓ |
| `S4:0.9/10` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S1:0.9/30` | **family-dependent** | 2/4 | 2/4 | +0.26 [-0.93, 1.52] ✗ | -0.94 [-1.50, -0.44] ✓ | -1.18 [-2.18, -0.19] ✓ | +0.15 [-1.23, 1.23] ✗ | +0.59 [-0.67, 1.87] ✗ |
| `S2:0.9/30` | **family-dependent** | 3/4 | 3/4 | -3.23 [-4.67, -1.98] ✓ | -1.44 [-2.39, -0.49] ✓ | +0.12 [-0.52, 0.78] ✗ | -2.03 [-3.35, -0.65] ✓ | -1.78 [-3.17, -0.55] ✓ |
| `S3:0.9/30` | **directional** | 4/4 | 3/4 | -2.97 [-4.56, -1.61] ✓ | -2.38 [-3.35, -1.26] ✓ | -1.06 [-2.06, 0.23] ~ | -1.88 [-3.47, -0.36] ✓ | -1.19 [-2.81, 0.35] ~ |
| `S4:0.9/30` | **family-dependent** | 3/4 | 2/4 | +0.12 [-0.02, 0.40] ✗ | -0.02 [-0.04, -0.01] ✓ | -0.00 [-0.01, 0.00] ~ | -0.17 [-0.49, -0.01] ✓ | -0.10 [-0.27, -0.00] ✓ |

Each piece of the successor as built, put back into the package
(leave-one-out; effect = the arm with the piece minus the package):

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `A1:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A2:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A3:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A1:fitted/30` | **family-dependent** | 1/4 | 0/4 | -0.08 [-0.24, 0.00] ✗ | +0.06 [-0.02, 0.20] ~ | -0.01 [-0.01, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A2:fitted/30` | **family-dependent** | 2/4 | 0/4 | +0.33 [-0.17, 0.79] ~ | +0.01 [-0.26, 0.32] ~ | +0.00 [-0.30, 0.24] ✗ | -0.07 [-0.23, 0.01] ✗ | +0.08 [0.00, 0.30] ~ |
| `A3:fitted/30` | **family-dependent** | 1/4 | 0/4 | +0.18 [0.01, 0.49] ✗ | -0.11 [-0.34, 0.04] ~ | +0.01 [0.00, 0.02] ✗ | +0.00 [0.00, 0.01] ✗ | +0.00 [0.00, 0.01] ✗ |
| `A1:0.7/30` | **directional** | 4/4 | 1/4 | +0.14 [-0.49, 0.82] ~ | +1.71 [0.71, 2.87] ✓ | +0.03 [-0.22, 0.30] ~ | +0.30 [-0.14, 0.79] ~ | +0.30 [-0.20, 0.83] ~ |
| `A2:0.7/30` | **family-dependent** | 2/4 | 0/4 | -0.17 [-0.87, 0.44] ✗ | +0.31 [-0.43, 1.14] ~ | +0.24 [-0.05, 0.57] ~ | -0.25 [-0.70, 0.19] ✗ | -0.10 [-0.59, 0.32] ✗ |
| `A3:0.7/30` | **family-dependent** | 3/4 | 2/4 | -0.48 [-1.13, 0.27] ~ | -1.17 [-2.06, -0.30] ✓ | +0.08 [-0.19, 0.40] ✗ | -0.80 [-1.43, -0.23] ✓ | -0.81 [-1.46, -0.26] ✓ |
| `A1:0.9/10` | **family-dependent** | 3/4 | 2/4 | +0.20 [0.04, 0.42] ✓ | -0.01 [-0.14, 0.13] ✗ | +0.06 [-0.01, 0.17] ~ | +0.27 [0.06, 0.52] ✓ | +0.19 [-0.01, 0.43] ~ |
| `A2:0.9/10` | **family-dependent** | 1/4 | 0/4 | +0.03 [-0.19, 0.22] ~ | -0.18 [-0.46, 0.05] ✗ | -0.02 [-0.14, 0.10] ✗ | -0.02 [-0.22, 0.17] ✗ | -0.08 [-0.29, 0.16] ✗ |
| `A3:0.9/10` | **family-dependent** | 3/4 | 1/4 | -0.49 [-0.74, -0.23] ✓ | +0.06 [-0.11, 0.26] ✗ | -0.02 [-0.10, 0.07] ~ | -0.12 [-0.28, 0.02] ~ | -0.10 [-0.29, 0.06] ~ |
| `A1:0.9/30` | **directional** | 4/4 | 3/4 | +2.50 [1.32, 3.62] ✓ | +1.85 [0.91, 2.81] ✓ | +0.30 [-0.22, 0.83] ~ | +2.55 [1.24, 3.85] ✓ | +1.55 [0.36, 2.74] ✓ |
| `A2:0.9/30` | **family-dependent** | 2/4 | 0/4 | -0.21 [-0.99, 0.52] ✗ | -0.37 [-1.07, 0.35] ✗ | +0.13 [-0.23, 0.56] ~ | +0.06 [-0.88, 1.14] ~ | -0.28 [-1.07, 0.57] ✗ |
| `A3:0.9/30` | **family-dependent** | 3/4 | 3/4 | -2.46 [-3.58, -1.40] ✓ | -1.01 [-1.66, -0.43] ✓ | +0.03 [-0.45, 0.54] ✗ | -2.12 [-3.21, -0.87] ✓ | -1.87 [-3.09, -0.70] ✓ |

1. **The successor as built beats today's serving where checks are weak or
   moderate.** `S1` is supported at the fitted strength with 3- and
   30-minute repairs (−1.86 to −2.01 and −1.12 to −2.46 minutes per episode)
   and at 0.9/10 (−0.49 to −1.53). It stops after the opening error wherever
   a check is worth less than its minute, which at Eedi's strength is almost
   always. Its review fix F6 (a decision is at stake over the posterior
   support) matters. Before the fix, the arm measured 0.1–0.3 checks per
   episode at the fitted strength through the nat-scaled path and cost
   0.08–0.29 minutes more (the earlier run, §8).
2. **Where checks are strong and the stakes high, it is family-dependent
   against today's serving** (`S1` at 0.9/30: `cdm` −0.94 and `nrm` −1.18
   certified; `lca` +0.26 and `lta` +0.15). It keeps today's robust
   completion gate, which ends 17–92 of 400 episodes at 0.9/30 with
   `couldnt_reliably_distinguish` before value would stop them. It also values
   one check at a time. Its right-repair rate at 0.9/30 is 0.62–0.84, against
   0.74–0.91 for the package.
3. **The proposed package** costs the same as the successor where checks are
   weak (both stop: `no difference`). At 0.9/30 it saves 1.44–3.23 minutes per
   episode in `lca`, `cdm` and `lta` (`nrm` +0.12 [−0.52, 0.78]), and it is
   directional at 0.7/30 (`S2`). Against today's serving (`S3`) it is
   supported at the fitted strength and directional at 0.7/30, 0.9/10 and
   0.9/30: the only successor variant that beats today's serving in every
   family and regime on point estimates. Its worst-case regret is the
   smallest of all 14 arms (§4.4).
4. **Each piece, put back into the package:**
   * **Robust completion gate** (`A1`): directional at 0.9/30 (+0.30 to +2.55
     minutes; 3 of 4 certified) and at 0.7/30 (+0.03 to +1.71). It never
     saves a measurable minute anywhere (the most negative effect is −0.08
     [−0.24, 0.00]). The gate's saving where checks are weak (`C3w`) belonged
     to the cap-only rules; a value rule already stops there. With the gate,
     worst-case regret rises from 1.21 to 3.76.
   * **The abstention's nat-scaled fallback** (`A2`): no measurable effect in
     any family or regime (|Δ| ≤ 0.37, every CI spans 0). `rank_feasible`
     abstains only after its robust LCB has cleared the cost, and with 60
     minutes per nat the EIG fallback almost always agrees and measures. **It
     is neutral only because 60 is too high** (§4.6). With a corrected scale,
     an abstention would stop instead, which is EVSI as built and its 1–7
     minutes of under-probing (`C2b`).
   * **The lookahead** (`A3`): it saves 1.01–2.46 minutes at 0.9/30 in `lca`,
     `cdm` and `lta`, nothing in `nrm`, and 0.80–1.17 at 0.7/30 in `cdm` and
     `lta`. It costs +0.18 [0.01, 0.49] in `lca` and +0.01 [0.00, 0.02] in `nrm` at
     the fitted strength with 30-minute repairs. Its sign is family-dependent, and its worst case is
     lopsided: without it the package's worst-case regret almost triples
     (3.33 vs 1.21).
   * **The stability stops** (`S4`, decision stable and action equivalent, on
     top of the lookahead): no difference in four of five regimes, and
     −0.17 to +0.12 at 0.9/30. They are harmless and give each stop an
     honest label.
   * **The lifted episode maximum**: the package asks more than 4 checks in up
     to 33 of 400 episodes at 0.9/30 (at most 8–11). The successor as built
     never reaches 4, because its gate stops it first.

The decomposition is not exact: the successor serves the incumbent's
highest-EIG instrument when it pays, while the package serves
`rank_feasible`'s top-ranked one. So `S2` is not the sum of `A1`–`A3`.

## 6. Ranked change proposal for the value-of-information successor

For `serving/voi-stopping` (mvp-0.17, at `086c24c0`), which consumes this
study. **Shipping rule** (RankCert): a change ships as the successor's
default, behind its own switch, when every fitted family agrees on its sign
with no family harmed beyond noise (`supported` or `directional`). It also
ships when its sign is family-dependent but it is the minimax-regret choice
with a bounded worst-case harm (≤ 0.2 minutes per episode). Every other
change waits for live `voi_forecasts` data, with the measure that decides it
named. Ranked by robustness, then by the worst-case minutes at stake. Paths
are on the successor branch.

### 6.1 Ship (robust across the families)

| Rank | Change | Evidence | Code (file:function) | Switch |
|---:|---|---|---|---|
| 1 | **The robust completion gate does not stop an episode while value decides** | `A1` directional: +0.30 to +2.55 minutes per episode at 0.9/30 when put back into the package (3/4 certified), +0.03 to +1.71 at 0.7/30. It never saves a measurable minute (most negative −0.08 [−0.24, 0.00]). Worst-case regret 3.76 → 1.21. It still holds under the reveal stress (+1.55 [0.36, 2.74]) | `diagnosis/probe_episodes.py:_evaluate_completion`: in the unstable branch, call `_robust_completion_override` only when `not voi_probe_site_active(vault)` or the new switch is on. When value decides, record the gate's verdict on the value stop's receipt as a counterfactual (as `voi_stopping.former_cap` does for the caps) instead of completing. `diagnosis/voi_stopping.py:probe_episode_decision` carries it in `former_cap` | `voi_stopping.robust_gate_with_value: bool = False` (true restores today's gate) |
| 2 | **Value the best 2–3 checks jointly when no single check pays** (lookahead) | `A3` sign family-dependent: −1.01 to −2.46 at 0.9/30 in `lca`, `cdm` and `lta`, 0 in `nrm`; −0.80 to −1.17 at 0.7/30. Worst harm +0.18 [0.01, 0.49] (`lca`, fitted/30). Without it worst-case regret rises 1.21 → 3.33; it ships under the minimax rule | `scheduling/evsi.py`: a new `robust_batch_evsi(candidates, loss_table, *, k, quantile)`: per ensemble member, the product of the k candidates' tables (conditionally independent given the hypothesis), `evsi_for_conditionals`, then the robust quantile, as `evsi_calibration/policies.py:decide_lookahead` does. `diagnosis/voi_stopping.py:value_candidates`: when a decision is at stake, `rank` did not abstain and no candidate continues, value `rank.ranked[:k]` for k = 2..max. If one batch's robust value exceeds the sum of its candidates' `lambda_time × minutes + burden`, continue with the batch's first candidate, method `robust_evsi_lookahead_<k>`, reason `robust_evsi_batch_clears_minutes_cost`. The forecast body records the batch | `voi_stopping.lookahead_max_checks: int = 3` (1 turns it off) |
| 3 | **A flip abstention no longer hands the decision to the nat scale; the robust LCB decides**, labelled `value_uncertain` | `A2`: no measurable effect today (\|Δ\| ≤ 0.37, every CI spans 0), because 60 minutes per nat measures anyway. It is the **prerequisite for rank 4**: with a corrected scale the fallback would stop, which is EVSI as built's under-probing (`C2b` supported: 1.28–7.21 minutes at 0.9/30, every family, and under every mis-calibrated system) | `diagnosis/voi_stopping.py:value_candidates`: take the EVSI branch also when `rank.verdict == "abstain"`: `continues = rank.verdict in ("measure", "abstain") and robust > threshold`, `value_uncertain = rank.verdict == "abstain"`, reason `robust_evsi_clears_minutes_cost:flip_abstention_<rank.reason>`. Keep the nat-scaled path for an *excluded* candidate (no robust value exists for it). `scheduling/evsi.py:rank_feasible` is unchanged; the causal selector still reads its abstention | `voi_stopping.flip_abstention: Literal["robust_lcb", "eig_fallback"] = "robust_lcb"` |
| 4 | **The nat-to-minutes scale for "nothing at stake": 60 → 5**, scoped to the successor | `C4` directional: 60 is 3.8–8.6× the largest measured minutes per nat in every family. `C6` supported: 10 saves 1.56–2.81 minutes per episode on the EIG rule at 0.9/10 in every family; 5 has the smallest worst-case regret across families (0.15, against 0.61 at 10). *Not simulated at the follow-up, teach-back and project-probe sites, nor where hypotheses share a repair (§7).* Ship after rank 3 | `diagnosis/voi_stopping.py`: read the scale from config in `value_candidates`' `METHOD_EIG_VALUE` branch (`point`, `robust`) and report it from `heuristic_parameters` (provenance `evsi_multisim`, source the config key). `robust_composition.VALUE_PER_NAT_MINUTES` stays 60 for the mvp-0.8 paths (`evaluate_selection`, the incumbent's robust selection), which this proposal does not touch. `params/parameter_registry.py`: register the new parameter | `voi_stopping.value_per_nat_minutes: float = 5.0` (60 restores today's) |
| 5 | **Charge the measured unresolved cost in the successor's loss table** | `C5` supported: at consistency 0.9 it saves 0.22–0.53 minutes per episode once `U` ≥ 3.55 and 0.55–1.54 at 7.10, in every family, and never costs more than 0.01. Below 3.55 it changes nothing | After the successor takes main (Part C, `scheduling/unresolved_cost.py`, is on main since `3192d0c9`, not on the successor's base): `diagnosis/voi_stopping.py:VoiContext.loss_table` passes `unresolved_minutes=unresolved_minutes_for_hypotheses(repository, labels, pseudo_count=config.evsi.unresolved_cost_prior_pseudo_count)[0]` to `action_loss.build_loss_table` when `config.evsi.measured_loss_enabled`, and keys its cache on it. The receipt's `loss_model` parameter names the regime | the existing `evsi.measured_loss_enabled` (default off; the owner's history decides `U`) |
| 6 | Keep the stability stops and the lifted episode maximum as built | `S4`: no difference in four of five regimes, −0.17 to +0.12 at 0.9/30. The package uses the lifted maximum in up to 33/400 episodes at 0.9/30 | none | — |

Ranks 1–3 together are `voi_proposed`, the minimax-regret choice of the 14
arms (worst case 1.21 minutes per episode, against 3.86 for the successor as
built and 3.60 for today's serving). They are independent switches, so a
regression in one site can be switched off alone.

### 6.2 Wait for live `voi_forecasts` data (family-dependent)

| Change | Why it waits | The live measure that decides it |
|---|---|---|
| `ROBUST_QUANTILE` 0.10 → 0.25 | Never costs minutes and saves up to 0.40 (`cdm`), but whether the 10th percentile under-predicts realized value depends on the family (`C6a`: yes in `lca`, `cdm`, `lta`; no in `nrm`, whose mis-specified system over-predicts) | The successor's receipts carry each continue/stop's robust and point value. Add to `evsi_calibration/live_report.py:summarize_joined` the realized value against the members' quantiles on forecasts with later truth; move the quantile to the one realized value sits at |
| The robust completion gate on the **kill-switch path** (value off, mvp-0.16) | `C3` family-dependent where checks are strong (−0.07 to +3.40 at 0.9/30), `C3w` supported where they are weak (it saves 0.86–1.58) | The live outcome calibration of probe forecasts (`learnloop evsi calibration`, report (a)): the owner's realized instrument consistency says which side of the line his checks are on |
| The lookahead's depth beyond 3, and its value at the follow-up and teach-back sites | Simulated only for probe episodes, k ≤ 3 | Per-site action-change calibration (report (c)) of `robust_evsi_lookahead_<k>` decisions |
| Any change to the card vocabulary's rows | `C1` is supported in every family (the card is overconfident and its checks mislead), but which rows replace it depends on the instrument type (§7.2) | The per-family conditional counts the cards already fold in (§4.9: counting at all recovers most of the gap) |

### 6.3 No change

| Parameter | Why |
|---|---|
| `PERTURBATION_DELTA` 0.15 | No decision effect in any family (\|Δ\| ≤ 0.09). It only feeds the flip abstention, which rank 3 stops from deciding |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 | 8 → 2 is not supported (§4.9). Counting at all is what matters, and it is on |
| `BURDEN_COST` 0, `INSTRUMENT_PERTURBATION_CONCENTRATION` 40, `ROBUST_DRAW_COUNT` 128 | Positive burden costs minutes; the others move nothing consistently |
| `DEFAULT_INTERVENTION_MINUTES` 3.0 | Knowing the true repair minutes is worth 0.26–1.01 minutes per episode (directional), but that is a measurement (repair durations per repair class, the decision-value spec's Stage 2), not a better constant |

## 7. What the families do not cover

1. **One site.** The simulation drives the probe-episode site only.
   `voi_stopping.value_candidates` also decides follow-up interventions,
   teach-backs and project probes, whose information comes from the facet and
   misconception EIG of the follow-up slate and the selection reward's
   `probe_eig_total`; none of those is simulated. A change to
   `value_candidates` reaches all four sites; this evidence covers one. Each
   proposal in §6 therefore gets a per-change switch, not only the site
   switches.
2. **Forced-choice answers only.** Every family is fitted to Eedi
   multiple-choice answers. Free-text instruments, graded through a grader
   channel, are not covered; their consistency is whatever the owner's
   calibration counts say.
3. **Every hypothesis has its own repair.** In the simulation a misconception's
   repair targets that misconception, so under the successor's support rule a
   decision is always at stake and its nat-scaled EIG decides only after a
   `rank_feasible` abstention. In a vault, hypotheses often share a triage
   route, and there the nat scale decides on its own: the
   `VALUE_PER_NAT_MINUTES` result (§4.6) matters more there than here.
4. **A single-cause system.** In every family the system's model is that
   family's population-average single-cause model (it never knows a
   question's own parameters, and never represents two held misconceptions).
   In `cdm` (19% of learners) and `nrm` (8%) the truth can need two repairs;
   that mis-specification is part of what the families test, not an
   oversight.
5. **Item parameters do not transfer.** A 2024 question borrows one fitted 2020
   item's parameters (of its subject, else the pool) by a seeded hash; the
   bank's own item difficulties are not learned.
6. **Learning during probing is near zero in the data.** The fitted
   within-session transitions are close to identity (a holder moves to
   knowing with probability 0.0004 per answer inside a session; 0.014
   between sessions, with teaching in between), so `lta` behaves like `lca`
   within an episode. `lta_reveal` is the upper bound (each answer's reveal
   teaching as much as the days between Eedi sessions); it is a stress world
   and never votes.
7. **Approximate CIs where state accumulates.** The pseudo-count streams fold
   every check into shared counts, so their episodes are not exchangeable;
   their bootstrap CIs (by episode) are approximate.
8. **Precision.** 400 flagged learners per cell (300 per sensitivity arm);
   at 30-minute repairs a paired CI is about ±1–1.5 minutes per episode, so
   several `directional` verdicts there are power-limited, not
   contradictions.

## 8. Changes

All inside `src/learnloop/evsi_calibration/`, its CLI and tests. No serving
code, schema, migration or default changed. The single-family study's arms
(`policies.ALL_POLICIES`) and its results are unchanged.

| Commit | What |
|---|---|
| `32b2d57b` | `family_data.py` (triple and subject sequences, fit/held-out split by `UserId`), `family_fit.py` (the four families' EM fits, held-out validation, adequacy gate); `response_fit.assemble_response_fit` (pooling shared with the single-family fit) |
| `9cccf603` | `families.py` (each family as a truth world over the 2024 bank, its own calibrated system, the instrument-strength transform, the `lta_reveal` stress), `multisim.py` (the episode loop over family states and multi-need truth; reproduces `simulate.run_learner` draw for draw for `lca`), the successor arms in `policies.py` |
| `a839b9f9` | `multifamily.py` (the study in every family, the claims, winners and rank agreement), `learnloop evsi multisim` |
| `a62ab11a` | the successor arm follows `serving/voi-stopping` at `086c24c0`; each policy's worst-case regret; S4; rotation claims per regime; `--reanalyze`; two analysis fixes (below) |
| `e6cac56e` | the leave-one-out ablations (`decide_package`, A1–A3); the `no difference` verdict |

**Fixed while finishing the interrupted run** (each with a test):

1. `C6c`'s log-loss bootstrap divided *both* arms' summed log loss by the
   pseudo-8 arm's check count. The arms stop after different numbers of
   checks, so it could certify the wrong sign: the first analysis certified
   "2 beats 8" for `nrm` at the fitted strength while the point log losses
   said the opposite (1.079 vs 1.054). Each arm is now a ratio of sums over its
   own checks under shared resamples (`_per_check_log_loss`).
2. The rotation and pseudo-count claims iterated stored dicts. A report read
   back from JSON has sorted keys, so a re-scored report listed values in
   another order. Both now follow the study's family and regime order.
3. The `voi_successor` arm had been written against the successor before its
   review rounds: it kept the episode maximum of 4 and decided "at stake" over
   the plausible hypotheses. Both now follow `086c24c0`. `voi_proposed` was
   redefined to share the successor's structure, so the two compare like for
   like.
4. Rotation claims pooled the fitted/3 cells (where checks are worth nothing
   and every value rule stops) with the strong-check cells. They are now one
   claim per regime.

## 9. Reproduce

```bash
# Fit the four families (the 2020 answers, the single-family triples), then the study:
uv run learnloop evsi multisim --eedi-2024 fixtures-local/eedi-2024 \
    --eedi-2020 fixtures-local/eedi-neurips-2020 --task 1_2 \
    --fit fixtures-local/evsi-calibration-v2/response_fit.json \
    --output fixtures-local/evsi-multisim --workers 14
# This report: the stored fits, every family, every arm (≈ 94 minutes on a loaded 32-core machine):
uv run learnloop evsi multisim --eedi-2024 fixtures-local/eedi-2024 \
    --fits fixtures-local/evsi-multisim/family_fits.json \
    --output fixtures-local/evsi-multisim-v3 --workers 12
# Re-score a stored report (no fit, no simulation; seconds):
uv run learnloop evsi multisim --reanalyze fixtures-local/evsi-multisim-v3/multisim_report.json
```

Report: `fixtures-local/evsi-multisim-v3/multisim_report.json` (gitignored;
family fits `fixtures-local/evsi-multisim/family_fits.json`, source hash
`70a1c5606097637b`). Seed 20261012; 400 learners per cell, 300 per
sensitivity arm, 32 ensemble draws, 400 bootstrap draws.
Rerunning with the same seed reproduced the earlier run (made before the
successor arms changed) exactly for every unchanged arm: all 823
cell × policy per-learner episode vectors, the sensitivity sweeps, Part C,
the pseudo-count streams and the fits.

## 10. Paid calls and data

No paid call, no network, no vault: the study reads the Eedi 2024 Kaggle
files and the public Eedi NeurIPS 2020 archive from `fixtures-local/`
(gitignored, never committed), as the single-family stage did.

## 11. Gate

Run at `e6cac56e` (the last code commit; the review commit after it is
documentation only), in the worktree, `TMPDIR` under its `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8668 passed**, 0 failed, 0 skipped (6 min 17 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8574 deselected (1 min 38 s) |
| targeted: `tests/test_evsi_multisim.py`, `tests/test_evsi_calibration_sim.py`, `tests/test_cli_help_snapshot.py` | 30 passed |

No frontend, `src-tauri`, schema or migration change: the npm, cargo and DB
reference steps do not apply.

## 12. Open questions for the owner

1. **The shipping rule for a family-dependent change.** The lookahead (rank 2)
   gains nothing in `nrm` and costs 0.18 minutes per episode in one `lca`
   regime, but without it the worst case almost triples. Ship it under
   RankCert's minimax rule, behind `voi_stopping.lookahead_max_checks`?
   *Recommended: yes.*
2. **The robust completion gate.** Turn it off only where value decides (the
   successor path), and keep it on the kill-switch path, where it saves
   minutes at Eedi's strength? *Recommended: yes.*
3. **The nat scale where nothing is at stake.** The follow-up, teach-back and
   project-probe sites, and hypotheses that share a repair, were not
   simulated. Accept 5 there as a labelled heuristic until `voi_forecasts`
   measures it, or stop outright when no decision is at stake (the decision
   value is then zero by construction)? *Recommended: 5, labelled.*
4. **Part C in the successor.** Leave `evsi.measured_loss_enabled` off until
   the owner's recurrence history gives `U` ≥ ~3.6 minutes for his
   misconceptions? *Recommended: off until then; the switch is the owner's.*
5. **A small Part B addition.** Score the receipts' robust value against
   realized value by member quantile, so `ROBUST_QUANTILE` can be set from
   the owner's data. *Recommended: yes, in the successor's follow-up stage.*

## Appendix A. Every regime

Mean minutes per episode (checks per episode; right-repair rate); best per
family in bold. 0.9/30 is in §4.3.

**Fitted strength, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.69 (1.9; 0.46) | 4.33 (2.0; 0.43) | 3.19 (2.0; 0.73) | 3.65 (1.9; 0.45) | 3.30 (1.9; 0.56) |
| `caps_only` | 5.03 (3.3; 0.51) | 5.91 (3.6; 0.47) | 4.05 (2.8; 0.72) | 5.07 (3.4; 0.46) | 4.49 (3.3; 0.61) |
| `evsi` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `evsi_lcb_only` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `evsi_lookahead` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `eig` | 1.77 (0.0; 0.43) | 2.55 (0.1; 0.36) | **1.18 (0.0; 0.73)** | 1.73 (0.0; 0.43) | 1.54 (0.0; 0.49) |
| `eig_no_gate` | 8.34 (6.7; 0.55) | 10.62 (8.3; 0.51) | 6.79 (5.5; 0.73) | 8.50 (6.8; 0.50) | 7.96 (7.1; 0.75) |
| `max_entropy` | 5.08 (3.3; 0.47) | 5.89 (3.6; 0.47) | 4.11 (2.9; 0.74) | 5.07 (3.4; 0.45) | 4.45 (3.3; 0.61) |
| `random` | 5.09 (3.4; 0.47) | 6.12 (3.7; 0.41) | 4.03 (2.9; 0.76) | 5.11 (3.4; 0.44) | 4.51 (3.3; 0.61) |
| `voi_successor` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_proposed` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_with_gate` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_with_fallback` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_one_step` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.18 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |

**Fitted strength, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 7.75 (1.9; 0.46) | 9.78 (2.0; 0.43) | 6.02 (2.0; 0.73) | 7.62 (1.9; 0.45) | 6.47 (1.9; 0.56) |
| `caps_only` | 8.95 (3.3; 0.51) | 11.27 (3.6; 0.47) | 6.99 (2.8; 0.72) | 9.08 (3.4; 0.46) | 7.29 (3.3; 0.61) |
| `evsi` | **5.83 (0.0; 0.42)** | 8.25 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `evsi_lcb_only` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.74) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `evsi_lookahead` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.74) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `eig` | 5.85 (0.0; 0.43) | 8.31 (0.1; 0.36) | 3.92 (0.0; 0.73) | 5.74 (0.0; 0.43) | 5.11 (0.0; 0.49) |
| `eig_no_gate` | 12.28 (6.7; 0.55) | 16.12 (8.3; 0.51) | 9.78 (5.5; 0.73) | 12.35 (6.8; 0.50) | 9.87 (7.1; 0.75) |
| `max_entropy` | 9.18 (3.3; 0.47) | 11.20 (3.6; 0.47) | 6.94 (2.9; 0.74) | 9.05 (3.4; 0.45) | 7.18 (3.3; 0.61) |
| `random` | 9.13 (3.4; 0.47) | 11.86 (3.7; 0.41) | 6.67 (2.9; 0.76) | 9.20 (3.4; 0.44) | 7.31 (3.3; 0.61) |
| `voi_successor` | 5.83 (0.0; 0.43) | **8.23 (0.0; 0.37)** | **3.90 (0.0; 0.74)** | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_proposed` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.74) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_with_gate` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.74) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_with_fallback` | 5.83 (0.0; 0.43) | **8.23 (0.0; 0.37)** | **3.90 (0.0; 0.74)** | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_one_step` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.74) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |

**Fitted strength, repair 30**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 19.35 (1.9; 0.46) | 25.32 (2.0; 0.43) | 14.12 (2.0; 0.73) | 18.98 (1.9; 0.45) | 15.52 (1.9; 0.56) |
| `caps_only` | 20.15 (3.3; 0.51) | 26.57 (3.6; 0.47) | 15.39 (2.8; 0.72) | 20.53 (3.4; 0.46) | 15.29 (3.3; 0.61) |
| `evsi` | 17.48 (0.0; 0.42) | 24.75 (0.0; 0.36) | 11.78 (0.0; 0.73) | **17.18 (0.0; 0.43)** | 15.30 (0.0; 0.49) |
| `evsi_lcb_only` | **17.32 (0.1; 0.44)** | 24.05 (0.1; 0.39) | **11.66 (0.0; 0.74)** | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `evsi_lookahead` | 17.50 (0.1; 0.44) | **23.94 (0.2; 0.40)** | 11.67 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `eig` | 17.50 (0.0; 0.43) | 24.76 (0.1; 0.36) | 11.78 (0.0; 0.73) | 17.18 (0.0; 0.43) | 15.31 (0.0; 0.49) |
| `eig_no_gate` | 23.52 (6.7; 0.55) | 31.82 (8.3; 0.51) | 18.33 (5.5; 0.73) | 23.35 (6.8; 0.50) | 15.31 (7.1; 0.75) |
| `max_entropy` | 20.88 (3.3; 0.47) | 26.35 (3.6; 0.47) | 15.04 (2.9; 0.74) | 20.45 (3.4; 0.45) | **14.98 (3.3; 0.61)** |
| `random` | 20.68 (3.4; 0.47) | 28.26 (3.7; 0.41) | 14.22 (2.9; 0.76) | 20.90 (3.4; 0.44) | 15.31 (3.3; 0.61) |
| `voi_successor` | 17.71 (0.1; 0.43) | 24.20 (0.1; 0.39) | **11.66 (0.0; 0.74)** | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_proposed` | 17.50 (0.1; 0.44) | **23.94 (0.2; 0.40)** | 11.67 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `voi_p_with_gate` | 17.42 (0.1; 0.45) | 24.00 (0.1; 0.39) | 11.67 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `voi_p_with_fallback` | 17.84 (0.1; 0.44) | 23.95 (0.2; 0.40) | 11.67 (0.0; 0.74) | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_p_one_step` | **17.32 (0.1; 0.44)** | 24.05 (0.1; 0.39) | **11.66 (0.0; 0.74)** | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |

**0.7, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.48 (2.0; 0.61) | 3.70 (2.1; 0.68) | 3.06 (2.0; 0.79) | 3.48 (2.0; 0.57) | 3.24 (2.0; 0.65) |
| `caps_only` | 4.50 (3.2; 0.69) | 4.42 (3.1; 0.79) | 3.90 (2.8; 0.77) | 4.46 (3.2; 0.65) | 4.19 (3.1; 0.71) |
| `evsi` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `evsi_lcb_only` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `evsi_lookahead` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `eig` | 1.81 (0.1; 0.46) | 2.42 (0.3; 0.51) | **1.18 (0.0; 0.74)** | 1.72 (0.1; 0.47) | 1.57 (0.1; 0.52) |
| `eig_no_gate` | 6.38 (5.4; 0.79) | 7.13 (5.8; 0.80) | 6.12 (5.0; 0.80) | 6.78 (5.6; 0.73) | 6.75 (6.0; 0.81) |
| `max_entropy` | 4.79 (3.3; 0.60) | 4.64 (3.2; 0.76) | 3.98 (2.9; 0.77) | 4.85 (3.3; 0.56) | 4.51 (3.2; 0.63) |
| `random` | 4.83 (3.3; 0.57) | 5.23 (3.5; 0.63) | 3.88 (2.9; 0.80) | 4.84 (3.3; 0.56) | 4.43 (3.3; 0.65) |
| `voi_successor` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_proposed` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_with_gate` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_with_fallback` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_one_step` | **1.73 (0.0; 0.43)** | **2.25 (0.0; 0.48)** | 1.18 (0.0; 0.73) | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |

**0.7, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 6.83 (2.0; 0.61) | 7.39 (2.1; 0.68) | 5.54 (2.0; 0.79) | 6.84 (2.0; 0.57) | 6.06 (2.0; 0.65) |
| `caps_only` | 7.47 (3.2; 0.69) | 7.49 (3.1; 0.79) | 6.50 (2.8; 0.77) | 7.47 (3.2; 0.65) | 6.66 (3.1; 0.71) |
| `evsi` | 5.74 (0.0; 0.43) | 7.50 (0.0; 0.48) | 3.92 (0.0; 0.73) | 5.68 (0.0; 0.44) | 5.08 (0.0; 0.50) |
| `evsi_lcb_only` | **5.52 (0.2; 0.49)** | 6.75 (0.5; 0.59) | **3.86 (0.0; 0.74)** | 5.52 (0.2; 0.48) | 5.00 (0.2; 0.53) |
| `evsi_lookahead` | 5.53 (0.2; 0.49) | **6.71 (0.6; 0.59)** | **3.86 (0.0; 0.74)** | 5.53 (0.2; 0.48) | **4.98 (0.2; 0.53)** |
| `eig` | 5.71 (0.1; 0.46) | 7.42 (0.3; 0.51) | 3.90 (0.0; 0.74) | 5.50 (0.1; 0.47) | 5.02 (0.1; 0.52) |
| `eig_no_gate` | 8.65 (5.4; 0.79) | 10.19 (5.8; 0.80) | 8.68 (5.0; 0.80) | 9.44 (5.6; 0.73) | 8.52 (6.0; 0.81) |
| `max_entropy` | 8.24 (3.3; 0.60) | 7.95 (3.2; 0.76) | 6.58 (2.9; 0.77) | 8.54 (3.3; 0.56) | 7.56 (3.2; 0.63) |
| `random` | 8.33 (3.3; 0.57) | 9.35 (3.5; 0.63) | 6.24 (2.9; 0.80) | 8.45 (3.3; 0.56) | 7.18 (3.3; 0.65) |
| `voi_successor` | 5.55 (0.2; 0.49) | 6.97 (0.6; 0.56) | 3.88 (0.0; 0.74) | 5.46 (0.2; 0.48) | 5.03 (0.2; 0.53) |
| `voi_proposed` | 5.53 (0.2; 0.49) | **6.71 (0.6; 0.59)** | **3.86 (0.0; 0.74)** | 5.53 (0.2; 0.48) | **4.98 (0.2; 0.53)** |
| `voi_p_with_gate` | 5.53 (0.2; 0.49) | 6.71 (0.5; 0.59) | **3.86 (0.0; 0.74)** | 5.53 (0.2; 0.48) | **4.98 (0.2; 0.53)** |
| `voi_p_with_fallback` | 5.56 (0.2; 0.49) | 6.92 (0.6; 0.58) | 3.88 (0.0; 0.74) | **5.44 (0.2; 0.49)** | 4.99 (0.2; 0.53) |
| `voi_p_one_step` | **5.52 (0.2; 0.49)** | 6.75 (0.5; 0.59) | **3.86 (0.0; 0.74)** | 5.52 (0.2; 0.48) | 5.00 (0.2; 0.53) |

**0.7, repair 30**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 16.43 (2.0; 0.61) | 17.94 (2.1; 0.68) | 12.64 (2.0; 0.79) | 16.45 (2.0; 0.57) | 14.11 (2.0; 0.65) |
| `caps_only` | 15.97 (3.2; 0.69) | 16.24 (3.1; 0.79) | 13.96 (2.8; 0.77) | 16.07 (3.2; 0.65) | 13.71 (3.1; 0.71) |
| `evsi` | 17.19 (0.0; 0.43) | 22.50 (0.0; 0.48) | 11.70 (0.0; 0.74) | 17.05 (0.0; 0.44) | 15.24 (0.0; 0.50) |
| `evsi_lcb_only` | 16.03 (0.4; 0.53) | 17.07 (1.1; 0.68) | **11.08 (0.1; 0.76)** | 15.99 (0.3; 0.50) | 14.71 (0.3; 0.54) |
| `evsi_lookahead` | 15.55 (0.7; 0.56) | **15.90 (1.7; 0.75)** | 11.16 (0.2; 0.77) | 15.19 (0.5; 0.54) | 13.90 (0.5; 0.57) |
| `eig` | 16.86 (0.1; 0.46) | 21.72 (0.3; 0.51) | 11.71 (0.0; 0.74) | 16.30 (0.1; 0.47) | 14.87 (0.1; 0.52) |
| `eig_no_gate` | **15.15 (5.4; 0.79)** | 18.94 (5.8; 0.80) | 15.97 (5.0; 0.80) | 17.04 (5.6; 0.73) | **13.56 (6.0; 0.81)** |
| `max_entropy` | 18.09 (3.3; 0.60) | 17.40 (3.2; 0.76) | 14.04 (2.9; 0.77) | 19.09 (3.3; 0.56) | 16.26 (3.2; 0.63) |
| `random` | 18.33 (3.3; 0.57) | 21.09 (3.5; 0.63) | 12.99 (2.9; 0.80) | 18.75 (3.3; 0.56) | 15.03 (3.3; 0.65) |
| `voi_successor` | 16.39 (0.3; 0.52) | 18.09 (1.0; 0.63) | 11.23 (0.1; 0.76) | 15.69 (0.3; 0.50) | 14.42 (0.3; 0.55) |
| `voi_proposed` | 15.55 (0.7; 0.56) | **15.90 (1.7; 0.75)** | 11.16 (0.2; 0.77) | 15.19 (0.5; 0.54) | 13.90 (0.5; 0.57) |
| `voi_p_with_gate` | 15.69 (0.5; 0.55) | 17.61 (1.3; 0.68) | 11.19 (0.2; 0.76) | 15.48 (0.4; 0.52) | 14.20 (0.4; 0.56) |
| `voi_p_with_fallback` | 15.38 (0.7; 0.56) | 16.21 (1.8; 0.74) | 11.41 (0.2; 0.76) | **14.94 (0.5; 0.54)** | 13.79 (0.5; 0.58) |
| `voi_p_one_step` | 16.03 (0.4; 0.53) | 17.07 (1.1; 0.68) | **11.08 (0.1; 0.76)** | 15.99 (0.3; 0.50) | 14.71 (0.3; 0.54) |

**0.9, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.14 (2.0; 0.72) | 3.18 (2.1; 0.83) | 3.01 (2.1; 0.83) | 3.19 (2.1; 0.72) | 3.13 (2.1; 0.73) |
| `caps_only` | 3.52 (2.8; 0.84) | 3.53 (2.6; 0.90) | 3.56 (2.7; 0.85) | 3.68 (2.8; 0.81) | 3.73 (2.8; 0.79) |
| `evsi` | **1.70 (0.0; 0.45)** | 1.93 (0.0; 0.60) | 1.17 (0.0; 0.74) | **1.65 (0.0; 0.46)** | **1.47 (0.0; 0.52)** |
| `evsi_lcb_only` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `evsi_lookahead` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `eig` | 1.80 (0.3; 0.52) | 2.08 (0.4; 0.66) | 1.18 (0.1; 0.75) | 1.79 (0.2; 0.51) | 1.67 (0.2; 0.56) |
| `eig_no_gate` | 4.88 (4.4; 0.90) | 5.10 (4.2; 0.91) | 5.21 (4.4; 0.86) | 5.09 (4.5; 0.89) | 5.84 (5.2; 0.83) |
| `max_entropy` | 4.52 (3.2; 0.68) | 4.33 (3.1; 0.82) | 3.94 (2.8; 0.77) | 4.58 (3.2; 0.65) | 4.37 (3.2; 0.68) |
| `random` | 4.42 (3.2; 0.68) | 4.65 (3.2; 0.75) | 3.80 (2.8; 0.81) | 4.39 (3.2; 0.67) | 4.14 (3.1; 0.72) |
| `voi_successor` | 1.73 (0.1; 0.47) | **1.92 (0.1; 0.61)** | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.50 (0.0; 0.53) |
| `voi_proposed` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `voi_p_with_gate` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `voi_p_with_fallback` | 1.73 (0.1; 0.47) | **1.92 (0.1; 0.61)** | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.50 (0.0; 0.53) |
| `voi_p_one_step` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.17 (0.0; 0.74)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |

**0.9, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 5.73 (2.0; 0.72) | 5.80 (2.1; 0.83) | 5.20 (2.1; 0.83) | 5.76 (2.1; 0.72) | 5.58 (2.1; 0.73) |
| `caps_only` | 5.13 (2.8; 0.84) | 5.81 (2.6; 0.90) | 5.62 (2.7; 0.85) | 5.67 (2.8; 0.81) | 5.79 (2.8; 0.79) |
| `evsi` | 5.68 (0.0; 0.45) | 6.40 (0.0; 0.61) | 3.90 (0.0; 0.74) | 5.46 (0.0; 0.47) | 4.84 (0.0; 0.53) |
| `evsi_lcb_only` | 5.22 (0.3; 0.56) | 5.37 (0.9; 0.76) | 3.69 (0.1; 0.78) | 4.96 (0.4; 0.57) | 4.80 (0.4; 0.59) |
| `evsi_lookahead` | **4.73 (0.6; 0.63)** | 5.43 (1.1; 0.79) | 3.67 (0.2; 0.78) | 4.83 (0.6; 0.60) | 4.70 (0.6; 0.62) |
| `eig` | 5.40 (0.3; 0.52) | 6.07 (0.4; 0.66) | 3.80 (0.1; 0.75) | 5.39 (0.2; 0.51) | 4.97 (0.2; 0.56) |
| `eig_no_gate` | 6.09 (4.4; 0.90) | 7.18 (4.2; 0.91) | 7.15 (4.4; 0.86) | 6.37 (4.5; 0.89) | 7.45 (5.2; 0.83) |
| `max_entropy` | 7.53 (3.2; 0.68) | 7.33 (3.1; 0.82) | 6.58 (2.8; 0.77) | 7.71 (3.2; 0.65) | 7.19 (3.2; 0.68) |
| `random` | 7.24 (3.2; 0.68) | 7.98 (3.2; 0.75) | 6.09 (2.8; 0.81) | 7.26 (3.2; 0.67) | 6.51 (3.1; 0.72) |
| `voi_successor` | 5.19 (0.3; 0.56) | 5.31 (0.9; 0.76) | 3.67 (0.1; 0.78) | 4.93 (0.4; 0.57) | 4.75 (0.3; 0.59) |
| `voi_proposed` | **4.73 (0.6; 0.63)** | 5.43 (1.1; 0.79) | 3.67 (0.2; 0.78) | 4.83 (0.6; 0.60) | 4.70 (0.6; 0.62) |
| `voi_p_with_gate` | 4.93 (0.5; 0.61) | 5.42 (1.0; 0.77) | 3.73 (0.2; 0.78) | 5.10 (0.5; 0.57) | 4.89 (0.5; 0.60) |
| `voi_p_with_fallback` | 4.76 (0.6; 0.62) | **5.25 (1.2; 0.80)** | **3.65 (0.2; 0.78)** | **4.82 (0.5; 0.61)** | **4.62 (0.5; 0.62)** |
| `voi_p_one_step` | 5.22 (0.3; 0.56) | 5.37 (0.9; 0.76) | 3.69 (0.1; 0.78) | 4.96 (0.4; 0.57) | 4.80 (0.4; 0.59) |

Under the hand-set vocabulary (fitted strength, repair 3):

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` |
|---|---|---|---|---|---|
| `incumbent` | 4.08 (2.1; 0.53) | 4.71 (2.1; 0.45) | 3.56 (2.1; 0.70) | 4.17 (2.1; 0.50) | 3.92 (2.1; 0.55) |
| `caps_only` | 4.90 (2.8; 0.56) | 5.36 (2.7; 0.47) | 4.10 (2.6; 0.71) | 5.09 (2.8; 0.53) | 4.61 (2.8; 0.59) |
| `evsi` | 1.93 (0.0; 0.43) | 2.69 (0.0; 0.38) | 1.31 (0.0; 0.71) | 1.90 (0.0; 0.44) | 1.70 (0.0; 0.49) |
| `evsi_lcb_only` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.81 (0.1; 0.50) |
| `evsi_lookahead` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |
| `eig` | 2.31 (0.3; 0.43) | 3.00 (0.3; 0.38) | 1.52 (0.2; 0.71) | 2.19 (0.3; 0.46) | 2.02 (0.3; 0.50) |
| `eig_no_gate` | 6.69 (4.6; 0.59) | 7.10 (4.5; 0.48) | 5.39 (4.0; 0.75) | 7.11 (4.9; 0.58) | 6.51 (5.1; 0.69) |
| `max_entropy` | 4.83 (3.0; 0.53) | 5.64 (2.9; 0.41) | 3.95 (2.7; 0.75) | 4.98 (3.1; 0.50) | 4.56 (3.0; 0.58) |
| `random` | 4.93 (3.0; 0.55) | 5.52 (2.8; 0.42) | 4.14 (2.7; 0.72) | 5.08 (3.0; 0.52) | 4.63 (3.0; 0.60) |
| `voi_successor` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.00 (0.1; 0.45) | 1.80 (0.1; 0.50) |
| `voi_proposed` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |
| `voi_p_with_gate` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |
| `voi_p_with_fallback` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.01 (0.1; 0.45) | 1.81 (0.1; 0.50) |
| `voi_p_one_step` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.81 (0.1; 0.50) |

## Appendix B. Sensitivity sweeps (0.9/10)

`robust_composition.ROBUST_QUANTILE`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.05 | 5.90 (+0.00 [0.00, 0.00]) / 5.50 (+0.05 [-0.14, 0.27]) / 4.85 (+0.02 [-0.12, 0.17]) | 6.35 (-0.03 [-0.10, 0.01]) / 5.50 (+0.17 [-0.03, 0.40]) / 5.36 (-0.02 [-0.24, 0.25]) | 4.01 (+0.00 [0.00, 0.00]) / 3.70 (-0.06 [-0.21, 0.05]) / 3.65 (-0.06 [-0.21, 0.05]) | 5.55 (-0.03 [-0.10, 0.00]) / 5.31 (+0.26 [0.01, 0.55]) / 5.05 (+0.12 [-0.07, 0.36]) |
| 0.1 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 0.25 | 5.91 (+0.00 [0.00, 0.01]) / 5.12 (-0.33 [-0.66, -0.05]) / 4.77 (-0.05 [-0.24, 0.17]) | 6.28 (-0.11 [-0.23, -0.00]) / 4.99 (-0.34 [-0.58, -0.14]) / 4.98 (-0.40 [-0.70, -0.13]) | 4.01 (+0.00 [0.00, 0.01]) / 3.72 (-0.04 [-0.17, 0.09]) / 3.70 (-0.01 [-0.12, 0.09]) | 5.57 (-0.01 [-0.02, 0.01]) / 5.06 (+0.01 [-0.18, 0.21]) / 4.93 (+0.00 [-0.25, 0.26]) |
| 0.5 | 5.87 (-0.03 [-0.09, 0.00]) / 4.97 (-0.48 [-0.85, -0.17]) / 4.75 (-0.08 [-0.33, 0.19]) | 6.28 (-0.10 [-0.23, 0.00]) / 4.96 (-0.38 [-0.70, -0.08]) / 4.97 (-0.41 [-0.75, -0.07]) | 4.01 (+0.01 [0.00, 0.02]) / 3.71 (-0.05 [-0.21, 0.10]) / 3.66 (-0.05 [-0.20, 0.10]) | 5.54 (-0.04 [-0.10, 0.00]) / 5.17 (+0.12 [-0.19, 0.45]) / 5.01 (+0.09 [-0.27, 0.45]) |

`evsi.PERTURBATION_DELTA`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.05 | 5.94 (+0.03 [-0.10, 0.17]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.30 (-0.09 [-0.22, 0.02]) / 5.33 (+0.00 [0.00, 0.00]) / 5.38 (+0.00 [0.00, 0.00]) | 4.04 (+0.04 [0.00, 0.11]) / 3.76 (+0.00 [0.00, 0.00]) / 3.71 (+0.00 [0.00, 0.00]) | 5.37 (-0.21 [-0.36, -0.06]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.1 | 5.86 (-0.05 [-0.14, 0.02]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.36 (-0.02 [-0.09, 0.02]) / 5.33 (+0.00 [0.00, 0.00]) / 5.38 (+0.00 [0.00, 0.00]) | 4.05 (+0.04 [0.00, 0.12]) / 3.76 (+0.00 [0.00, 0.00]) / 3.71 (+0.00 [0.00, 0.00]) | 5.49 (-0.09 [-0.18, 0.00]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.15 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 0.25 | 5.90 (+0.00 [0.00, 0.00]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.31 (-0.07 [-0.19, 0.01]) / 5.33 (+0.00 [0.00, 0.00]) / 5.38 (+0.00 [0.00, 0.00]) | 4.01 (+0.00 [0.00, 0.01]) / 3.76 (+0.00 [0.00, 0.00]) / 3.71 (+0.00 [0.00, 0.00]) | 5.59 (+0.01 [-0.04, 0.08]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.35 | 5.90 (-0.00 [-0.01, 0.00]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.34 (-0.05 [-0.16, 0.08]) / 5.33 (+0.00 [0.00, 0.00]) / 5.38 (+0.00 [0.00, 0.00]) | 4.01 (+0.00 [-0.01, 0.01]) / 3.76 (+0.00 [0.00, 0.00]) / 3.71 (+0.00 [0.00, 0.00]) | 5.64 (+0.06 [-0.03, 0.18]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |

`robust_composition.BURDEN_COST`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 0.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.46 (+0.01 [-0.21, 0.25]) / 5.05 (+0.23 [-0.01, 0.54]) | 6.38 (+0.00 [0.00, 0.00]) / 5.53 (+0.19 [-0.03, 0.38]) / 5.28 (-0.10 [-0.32, 0.12]) | 4.01 (+0.00 [0.00, 0.00]) / 3.80 (+0.04 [-0.14, 0.23]) / 3.82 (+0.11 [-0.09, 0.31]) | 5.58 (+0.00 [0.00, 0.00]) / 5.27 (+0.22 [0.06, 0.38]) / 5.11 (+0.19 [-0.02, 0.38]) |
| 1 | 5.90 (+0.00 [0.00, 0.00]) / 5.55 (+0.10 [-0.14, 0.36]) / 5.43 (+0.61 [0.26, 0.97]) | 6.38 (+0.00 [0.00, 0.00]) / 5.69 (+0.36 [0.04, 0.67]) / 5.68 (+0.29 [-0.06, 0.60]) | 4.00 (-0.00 [-0.01, 0.00]) / 3.94 (+0.18 [-0.03, 0.40]) / 3.91 (+0.20 [-0.03, 0.43]) | 5.59 (+0.01 [-0.03, 0.08]) / 5.20 (+0.15 [-0.09, 0.37]) / 5.14 (+0.21 [-0.05, 0.46]) |
| 2 | 5.90 (-0.00 [-0.01, 0.00]) / 5.79 (+0.34 [-0.02, 0.66]) / 5.74 (+0.92 [0.48, 1.31]) | 6.34 (-0.05 [-0.16, 0.08]) / 6.15 (+0.81 [0.36, 1.28]) / 6.07 (+0.69 [0.18, 1.21]) | 4.00 (-0.01 [-0.02, 0.00]) / 3.98 (+0.22 [-0.02, 0.47]) / 3.98 (+0.27 [0.01, 0.55]) | 5.60 (+0.02 [-0.04, 0.13]) / 5.40 (+0.35 [0.03, 0.71]) / 5.42 (+0.50 [0.17, 0.88]) |

`action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 1.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.90 (+0.06 [-0.15, 0.31]) / 5.90 (+0.06 [-0.15, 0.31]) | 6.33 (+0.00 [0.00, 0.00]) / 6.33 (+0.14 [0.01, 0.30]) / 6.33 (+0.14 [0.01, 0.30]) | 4.00 (+0.00 [0.00, 0.00]) / 4.00 (+0.03 [0.00, 0.09]) / 4.00 (+0.03 [0.00, 0.09]) | 5.63 (+0.03 [0.00, 0.09]) / 5.63 (+0.02 [-0.10, 0.16]) / 5.63 (+0.02 [-0.10, 0.16]) |
| 3 (current) | 5.90 / 5.84 / 5.84 | 6.33 / 6.19 / 6.19 | 4.00 / 3.97 / 3.97 | 5.60 / 5.61 / 5.61 |
| 6 | 5.90 (+0.00 [0.00, 0.01]) / 5.48 (-0.36 [-0.66, -0.08]) / 5.45 (-0.39 [-0.80, 0.01]) | 6.38 (+0.05 [-0.07, 0.16]) / 5.57 (-0.63 [-1.04, -0.22]) / 5.61 (-0.59 [-1.01, -0.18]) | 4.00 (+0.00 [0.00, 0.01]) / 3.85 (-0.12 [-0.31, 0.08]) / 3.85 (-0.12 [-0.31, 0.08]) | 5.57 (-0.03 [-0.14, 0.03]) / 5.21 (-0.40 [-0.75, -0.11]) / 5.16 (-0.45 [-0.78, -0.14]) |
| 10 | 5.90 (+0.00 [0.00, 0.01]) / 5.45 (-0.39 [-0.78, -0.03]) / 4.83 (-1.01 [-1.52, -0.54]) | 6.38 (+0.05 [-0.07, 0.16]) / 5.33 (-0.86 [-1.33, -0.39]) / 5.38 (-0.81 [-1.36, -0.30]) | 4.01 (+0.01 [0.00, 0.02]) / 3.76 (-0.21 [-0.49, 0.07]) / 3.71 (-0.26 [-0.54, 0.02]) | 5.58 (-0.02 [-0.13, 0.04]) / 5.05 (-0.56 [-0.94, -0.21]) / 4.93 (-0.69 [-1.09, -0.30]) |
| 20 | 5.90 (+0.00 [0.00, 0.01]) / 5.19 (-0.65 [-1.12, -0.24]) / 4.52 (-1.32 [-1.88, -0.78]) | 6.38 (+0.05 [-0.07, 0.16]) / 5.10 (-1.09 [-1.64, -0.57]) / 4.89 (-1.31 [-1.90, -0.76]) | 3.98 (-0.02 [-0.07, 0.02]) / 3.58 (-0.39 [-0.66, -0.06]) / 3.57 (-0.40 [-0.72, -0.05]) | 5.58 (-0.02 [-0.13, 0.04]) / 5.04 (-0.57 [-0.99, -0.14]) / 4.91 (-0.70 [-1.25, -0.16]) |

`check minutes (probe burden; causal selector default 1.5)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.19 (-0.26 [-0.57, 0.00]) / 4.52 (-0.30 [-0.58, -0.00]) | 6.38 (+0.00 [0.00, 0.00]) / 5.10 (-0.23 [-0.63, 0.11]) / 4.89 (-0.50 [-0.91, -0.09]) | 3.98 (-0.02 [-0.08, 0.01]) / 3.58 (-0.18 [-0.34, -0.02]) / 3.57 (-0.14 [-0.35, 0.09]) | 5.58 (+0.00 [0.00, 0.00]) / 5.04 (-0.01 [-0.22, 0.20]) / 4.91 (-0.02 [-0.31, 0.32]) |
| 1 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 1.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.46 (+0.01 [-0.21, 0.25]) / 5.42 (+0.59 [0.28, 0.92]) | 6.38 (+0.00 [0.00, 0.00]) / 5.53 (+0.19 [-0.03, 0.38]) / 5.48 (+0.10 [-0.22, 0.39]) | 4.01 (+0.00 [0.00, 0.00]) / 3.80 (+0.04 [-0.14, 0.23]) / 3.81 (+0.10 [-0.11, 0.31]) | 5.58 (+0.00 [0.00, 0.00]) / 5.27 (+0.22 [0.06, 0.38]) / 5.22 (+0.29 [0.03, 0.52]) |
| 3 | 5.90 (-0.00 [-0.01, 0.00]) / 5.79 (+0.34 [-0.02, 0.66]) / 5.79 (+0.96 [0.52, 1.43]) | 6.34 (-0.05 [-0.16, 0.08]) / 6.15 (+0.81 [0.36, 1.28]) / 6.15 (+0.76 [0.26, 1.29]) | 4.00 (-0.01 [-0.02, 0.00]) / 3.98 (+0.22 [-0.02, 0.47]) / 3.98 (+0.27 [0.01, 0.55]) | 5.60 (+0.02 [-0.04, 0.13]) / 5.40 (+0.35 [0.03, 0.71]) / 5.40 (+0.47 [0.10, 0.88]) |

`robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 4 | 5.90 (-0.00 [-0.01, 0.00]) / 5.17 (-0.28 [-0.66, 0.05]) / 4.56 (-0.27 [-0.69, 0.17]) | 6.33 (-0.05 [-0.16, 0.07]) / 5.42 (+0.09 [-0.24, 0.38]) / 5.12 (-0.26 [-0.65, 0.09]) | 4.00 (-0.01 [-0.02, 0.00]) / 3.80 (+0.04 [-0.12, 0.18]) / 3.74 (+0.03 [-0.16, 0.25]) | 5.63 (+0.05 [-0.03, 0.18]) / 5.28 (+0.23 [-0.01, 0.48]) / 4.94 (+0.01 [-0.38, 0.38]) |
| 10 | 5.90 (-0.00 [-0.01, 0.00]) / 5.45 (+0.00 [-0.29, 0.31]) / 4.73 (-0.10 [-0.40, 0.25]) | 6.33 (-0.05 [-0.16, 0.07]) / 5.21 (-0.13 [-0.34, 0.10]) / 4.97 (-0.41 [-0.66, -0.14]) | 4.00 (-0.01 [-0.02, 0.00]) / 3.76 (-0.00 [-0.13, 0.14]) / 3.76 (+0.05 [-0.11, 0.21]) | 5.61 (+0.03 [-0.07, 0.16]) / 5.38 (+0.33 [0.09, 0.59]) / 4.85 (-0.08 [-0.32, 0.17]) |
| 40 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 160 | 5.92 (+0.01 [-0.08, 0.12]) / 5.28 (-0.17 [-0.44, 0.10]) / 4.88 (+0.06 [-0.17, 0.29]) | 6.30 (-0.08 [-0.22, 0.02]) / 5.12 (-0.21 [-0.52, 0.02]) / 5.07 (-0.31 [-0.60, -0.06]) | 3.98 (-0.02 [-0.09, 0.01]) / 3.71 (-0.05 [-0.17, 0.08]) / 3.69 (-0.02 [-0.13, 0.09]) | 5.61 (+0.03 [-0.11, 0.17]) / 5.22 (+0.17 [-0.06, 0.41]) / 5.09 (+0.16 [-0.09, 0.38]) |

`robust_composition.ROBUST_DRAW_COUNT (simulation draws)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 16 | 5.87 (-0.03 [-0.09, 0.00]) / 5.40 (-0.05 [-0.21, 0.08]) / 4.96 (+0.14 [-0.09, 0.39]) | 6.35 (-0.03 [-0.11, 0.01]) / 5.35 (+0.02 [-0.19, 0.18]) / 5.25 (-0.13 [-0.38, 0.07]) | 3.98 (-0.03 [-0.09, 0.00]) / 3.65 (-0.11 [-0.25, 0.00]) / 3.64 (-0.07 [-0.21, 0.04]) | 5.59 (+0.01 [-0.12, 0.15]) / 5.20 (+0.15 [-0.11, 0.41]) / 5.24 (+0.32 [0.09, 0.57]) |
| 32 (current) | 5.90 / 5.45 / 4.83 | 6.38 / 5.33 / 5.38 | 4.01 / 3.76 / 3.71 | 5.58 / 5.05 / 4.93 |
| 64 | 5.90 (+0.00 [0.00, 0.00]) / 5.43 (-0.02 [-0.17, 0.15]) / 4.79 (-0.04 [-0.21, 0.13]) | 6.35 (-0.03 [-0.11, 0.01]) / 5.22 (-0.11 [-0.35, 0.06]) / 5.14 (-0.24 [-0.48, -0.05]) | 4.00 (-0.00 [-0.01, 0.00]) / 3.70 (-0.06 [-0.20, 0.06]) / 3.69 (-0.02 [-0.17, 0.10]) | 5.57 (-0.01 [-0.10, 0.07]) / 5.16 (+0.11 [-0.09, 0.34]) / 4.99 (+0.06 [-0.19, 0.29]) |
| 128 | 5.91 (+0.00 [0.00, 0.01]) / 5.54 (+0.09 [-0.10, 0.32]) / 4.90 (+0.07 [-0.13, 0.31]) | 6.34 (-0.05 [-0.16, 0.08]) / 5.19 (-0.14 [-0.36, 0.02]) / 5.19 (-0.20 [-0.41, -0.01]) | 4.00 (-0.00 [-0.01, 0.00]) / 3.67 (-0.09 [-0.24, 0.03]) / 3.62 (-0.09 [-0.24, 0.03]) | 5.66 (+0.08 [-0.04, 0.22]) / 5.24 (+0.19 [-0.03, 0.42]) / 5.03 (+0.11 [-0.14, 0.34]) |

## Appendix C. Claim statements

- `C1a`: the hand-set card implies consistency 0.8333; every family's fitted consistency is far lower
- `C1b:incumbent`: under the hand-set vocabulary, incumbent's checks realize no information about the truth (mean log gain <= 0; certified when the CI is below 0)
- `C1b:caps_only`: under the hand-set vocabulary, caps_only's checks realize no information about the truth (mean log gain <= 0; certified when the CI is below 0)
- `C1c`: under the family's calibrated model, incumbent's checks realize positive information about the truth
- `C7:3`: fitted strength, repair 3: evsi as built costs fewer minutes than the incumbent
- `C7:10`: fitted strength, repair 10: evsi as built costs fewer minutes than the incumbent
- `C7:30`: fitted strength, repair 30: evsi as built costs fewer minutes than the incumbent
- `C2a`: 0.9/30: evsi as built costs more minutes than the incumbent (it under-probes)
- `C2b:0.9/30`: 0.9/30: the flip abstention costs minutes (evsi - evsi_lcb_only > 0)
- `C2c:0.9/30`: 0.9/30: the 2-3 check lookahead saves minutes over the one-step rule without abstention (evsi_lookahead - evsi_lcb_only < 0)
- `C2d:0.9/30`: 0.9/30: the lookahead beats the incumbent
- `C2e:0.9/30`: 0.9/30: the lookahead beats caps_only (the same caps without the gate)
- `C2b:0.9/10`: 0.9/10: the flip abstention costs minutes (evsi - evsi_lcb_only > 0)
- `C2c:0.9/10`: 0.9/10: the 2-3 check lookahead saves minutes over the one-step rule without abstention (evsi_lookahead - evsi_lcb_only < 0)
- `C2d:0.9/10`: 0.9/10: the lookahead beats the incumbent
- `C2e:0.9/10`: 0.9/10: the lookahead beats caps_only (the same caps without the gate)
- `C2b:0.7/30`: 0.7/30: the flip abstention costs minutes (evsi - evsi_lcb_only > 0)
- `C2c:0.7/30`: 0.7/30: the 2-3 check lookahead saves minutes over the one-step rule without abstention (evsi_lookahead - evsi_lcb_only < 0)
- `C2d:0.7/30`: 0.7/30: the lookahead beats the incumbent
- `C2e:0.7/30`: 0.7/30: the lookahead beats caps_only (the same caps without the gate)
- `C3:0.9/30`: 0.9/30: today's robust completion gate costs minutes (incumbent - caps_only > 0)
- `C3:0.9/10`: 0.9/10: today's robust completion gate costs minutes (incumbent - caps_only > 0)
- `C3:0.7/30`: 0.7/30: today's robust completion gate costs minutes (incumbent - caps_only > 0)
- `C3w:fitted/3`: fitted/3: where checks are weak the robust completion gate saves minutes (incumbent - caps_only < 0)
- `C8:0.9/30`: 0.9/30: the EIG path's agreement gate costs minutes (eig - eig_no_gate > 0)
- `C8w:fitted/3`: fitted/3: the agreement gate saves minutes because the nat-scaled rule over-measures (eig - eig_no_gate < 0)
- `S1:fitted/3`: fitted/3: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:fitted/3`: fitted/3: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:fitted/3`: fitted/3: the proposed package costs fewer minutes than the incumbent
- `S4:fitted/3`: fitted/3: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_proposed - evsi_lookahead < 0)
- `A1:fitted/3`: fitted/3: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:fitted/3`: fitted/3: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:fitted/3`: fitted/3: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S1:fitted/30`: fitted/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:fitted/30`: fitted/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:fitted/30`: fitted/30: the proposed package costs fewer minutes than the incumbent
- `S4:fitted/30`: fitted/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_proposed - evsi_lookahead < 0)
- `A1:fitted/30`: fitted/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:fitted/30`: fitted/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:fitted/30`: fitted/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S1:0.7/30`: 0.7/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.7/30`: 0.7/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.7/30`: 0.7/30: the proposed package costs fewer minutes than the incumbent
- `S4:0.7/30`: 0.7/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_proposed - evsi_lookahead < 0)
- `A1:0.7/30`: 0.7/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.7/30`: 0.7/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.7/30`: 0.7/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S1:0.9/10`: 0.9/10: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.9/10`: 0.9/10: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.9/10`: 0.9/10: the proposed package costs fewer minutes than the incumbent
- `S4:0.9/10`: 0.9/10: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_proposed - evsi_lookahead < 0)
- `A1:0.9/10`: 0.9/10: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.9/10`: 0.9/10: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.9/10`: 0.9/10: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S1:0.9/30`: 0.9/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.9/30`: 0.9/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.9/30`: 0.9/30: the proposed package costs fewer minutes than the incumbent
- `S4:0.9/30`: 0.9/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_proposed - evsi_lookahead < 0)
- `A1:0.9/30`: 0.9/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.9/30`: 0.9/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.9/30`: 0.9/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `C4b:fitted/3`: fitted/3: loss-derived EVSI costs fewer minutes than the EIG rule with VALUE_PER_NAT_MINUTES = 60 (evsi_lcb_only - eig_no_gate < 0)
- `C4b:fitted/30`: fitted/30: loss-derived EVSI costs fewer minutes than the EIG rule with VALUE_PER_NAT_MINUTES = 60 (evsi_lcb_only - eig_no_gate < 0)
- `C4b:0.9/10`: 0.9/10: loss-derived EVSI costs fewer minutes than the EIG rule with VALUE_PER_NAT_MINUTES = 60 (evsi_lcb_only - eig_no_gate < 0)
- `C4b:0.9/30`: 0.9/30: loss-derived EVSI costs fewer minutes than the EIG rule with VALUE_PER_NAT_MINUTES = 60 (evsi_lcb_only - eig_no_gate < 0)
- `R:evsi_lookahead-incumbent@fitted/3`: fitted/3, system calibrated to another family: the lookahead beats the incumbent (evsi_lookahead-incumbent, sign -1)
- `R:evsi_lookahead-incumbent@0.9/10`: 0.9/10, system calibrated to another family: the lookahead beats the incumbent (evsi_lookahead-incumbent, sign -1)
- `R:evsi_lookahead-incumbent@0.9/30`: 0.9/30, system calibrated to another family: the lookahead beats the incumbent (evsi_lookahead-incumbent, sign -1)
- `R:evsi-evsi_lcb_only@fitted/3`: fitted/3, system calibrated to another family: the flip abstention costs minutes (evsi-evsi_lcb_only, sign +1)
- `R:evsi-evsi_lcb_only@0.9/10`: 0.9/10, system calibrated to another family: the flip abstention costs minutes (evsi-evsi_lcb_only, sign +1)
- `R:evsi-evsi_lcb_only@0.9/30`: 0.9/30, system calibrated to another family: the flip abstention costs minutes (evsi-evsi_lcb_only, sign +1)
- `R:incumbent-caps_only@fitted/3`: fitted/3, system calibrated to another family: the robust completion gate costs minutes (incumbent-caps_only, sign +1)
- `R:incumbent-caps_only@0.9/10`: 0.9/10, system calibrated to another family: the robust completion gate costs minutes (incumbent-caps_only, sign +1)
- `R:incumbent-caps_only@0.9/30`: 0.9/30, system calibrated to another family: the robust completion gate costs minutes (incumbent-caps_only, sign +1)
- `R:evsi-incumbent@fitted/3`: fitted/3, system calibrated to another family: evsi as built costs more than the incumbent (evsi-incumbent, sign +1)
- `R:evsi-incumbent@0.9/10`: 0.9/10, system calibrated to another family: evsi as built costs more than the incumbent (evsi-incumbent, sign +1)
- `R:evsi-incumbent@0.9/30`: 0.9/30, system calibrated to another family: evsi as built costs more than the incumbent (evsi-incumbent, sign +1)
- `R:voi_proposed-voi_successor@fitted/3`: fitted/3, system calibrated to another family: the proposed package beats the successor as built (voi_proposed-voi_successor, sign -1)
- `R:voi_proposed-voi_successor@0.9/10`: 0.9/10, system calibrated to another family: the proposed package beats the successor as built (voi_proposed-voi_successor, sign -1)
- `R:voi_proposed-voi_successor@0.9/30`: 0.9/30, system calibrated to another family: the proposed package beats the successor as built (voi_proposed-voi_successor, sign -1)
- `C4`: VALUE_PER_NAT_MINUTES = 60 is above every measured minutes-per-nat (certified: 60 is >= 4x the largest measured value's upper CI)
- `C5`: 0.9: charging the measured unresolved cost saves minutes once it is about 3.6 minutes or more, and never costs minutes (value: the smallest U with a CI below 0)
- `C6a`: ROBUST_QUANTILE 0.10 under-predicts the realized value of checks wherever checks have value, and the 25th percentile is closer (caps_only's checks)
- `C6:robust_quantile=0.25`: robust_composition.ROBUST_QUANTILE = 0.25 (vs current) does not cost minutes for evsi_lookahead at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6:perturbation_delta=0.1`: evsi.PERTURBATION_DELTA = 0.1 (vs current) does not cost minutes for evsi at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6:burden_cost=0.5`: robust_composition.BURDEN_COST = 0.5 (vs current) does not cost minutes for evsi_lookahead at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6:repair_minutes=10`: action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes) = 10 (vs current) does not cost minutes for evsi_lookahead at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6:value_per_nat_minutes=10`: robust_composition.VALUE_PER_NAT_MINUTES = 10 (vs current) does not cost minutes for eig_no_gate at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6:instrument_concentration=4`: robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION = 4 (vs current) does not cost minutes for evsi_lookahead at 0.9/10 (certified when it saves minutes with a CI below 0)
- `C6c`: DEFAULT_CONDITIONAL_PSEUDO_COUNT 2 forecasts answers better than 8 over a stream that starts from the hand-set vocabulary (value: minutes per episode, 2 - 8; certified on log loss)
