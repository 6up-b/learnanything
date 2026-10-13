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
seeds, counts a conclusion only when every adequate family agrees, and turns
what survives into a ranked change proposal for the value-of-information
successor (`serving/voi-stopping`, mvp-0.17).

**This is the report after the Codex review** (job `20261013-094805-rur4XA`,
fixes in [`evsi-multisim-codex-review.md`](evsi-multisim-codex-review.md)).
Its five fixes changed the study, and the study was rerun: the package now
differs from the successor by exactly the changes it names (F1), only
adequate families vote and a missing cell is `insufficient evidence` (F2), the
`nrm` and `cdm` systems average responses over the item pool (F3), no
episode has a count bound (F4), and artifacts are written atomically (F5).
**The proposal changed with the rerun** (§6): keep the successor's handling
of a flip abstention, which the first report proposed to change.

Offline only: no serving code or default changed, no paid call.

## Summary

**Four families, one Eedi.** A latent class model (the study's), a
cognitive diagnosis model (MC-DINA with DINO misconception triggers, the
Q-matrix from the misconception labels), a nominal-response IRT model with a
misconception trait, and a latent transition model (the learner learns
between encounters). All four are fitted to the same 111,096 Eedi triple
sequences, and all beat the item-marginal baseline on 8,516 held-out students
(log loss 0.721–0.748 against 0.796; every family passes RankCert's adequacy
gate, so all four vote). The study's own family fits worst; the other three
fit about equally well. Each family forecasts the designated distractor's
share of wrong answers within 0.6 points. The study was rerun in every family
under common seeds: 15 policy arms, 9 regimes, the system calibrated to every
other family, the parameter sweeps, the measured loss, and the pseudo-count
stream. 99 minutes, no paid call. In `lca`, `lta` and `lta_reveal` (with any
system not calibrated to `cdm` or `nrm`, whose systems F3 changed) every arm
reproduced the first run's episodes exactly except where the review changed
them: `eig_no_gate`, only for learners the old bound had stopped, and the
package arms, whose serving rule changed.

**The single-family claims, tested in every family** (`supported`: every
family's 95% CI agrees; `directional`: every point estimate does;
`family-dependent`: the families disagree in sign):

| Single-family claim | Single-family value | Across the four families | Range across families |
|---|---|---|---|
| The card is overconfident (consistency) | 0.83 vs 0.41 | **supported** (now through each family's CI) | 0.25–0.44 |
| Under the card, checks realize negative information about the truth | −0.06 nats | **supported** (caps_only), directional (incumbent; `lta`'s CI reaches +0.02) | −0.05 to −0.16 nats per check |
| Under a calibrated model they realize positive information | +0.10 nats | **supported** (was directional: `nrm`'s miss was F3) | +0.04 to +0.10 nats per check |
| At Eedi's strength, value rules beat today's serving | 1.81 vs 3.77 min | **supported** at repairs of 3 and 10 min, directional at 30 | −0.79 to −1.95 min per episode |
| EVSI as built under-probes where checks are strong (0.9/30) | 17.9 vs 13.3 | directional (3/4 certified) | +0.78 to +5.71 |
| … because of the flip abstention | 17.9 → 12.5 | **supported** (0.9/30, 0.9/10, 0.7/30; directional under every mis-calibrated system at 0.9/30) | +1.27 to +7.12 at 0.9/30 |
| … and of one-step valuation (2–3 check lookahead) | 12.5 → 10.8 | **directional** at 0.9/30 and 0.7/30 (was family-dependent) | −0.18 to −2.59 at 0.9/30 |
| The lookahead beats today's serving | 10.8 vs 13.3 | **supported** at 0.9/10, directional at 0.9/30 and 0.7/30 | −0.67 to −3.10 at 0.9/30 |
| Today's robust completion gate costs minutes (0.9/30) | +3.7 | family-dependent: that was `lca`'s value; the gate **saves** 0.81–1.55 where checks are weak (supported) | −0.41 to +3.40 |
| `VALUE_PER_NAT_MINUTES = 60` is far too high | 4–500× | directional (60 is 3.8–6.2× the largest measured); **lowering it to 10 is supported** on the EIG rule | 10 saves 1.56–2.62 min |
| The measured loss pays off above ~3.6 min | 3.6 | **supported** (never costs) | saves 0.21–0.53 at U = 3.55 |
| `ROBUST_QUANTILE` 0.10 → 0.25 | within noise | **directional** on minutes and on the bias it corrects (was family-dependent) | −0.32 to 0.00 |
| `PERTURBATION_DELTA` 0.15 → 0.10 | no effect | no decision effect in any family | \|Δ\| ≤ 0.09 |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 → 2 | not simulated | **not supported**: no difference a CI separates from 0; counting at all is what matters | |

**Where the families disagree is where it matters.** With weak checks they
rank the policies alike (Kendall τ 0.85–0.98 at repair 3). With strong checks
and 30-minute repairs, they disagree about the winner (τ 0.48–0.52, minimum
0.24), and acting on one family's winner costs up to 2.5–4.1 minutes per
episode in another. That is exactly where the single-family study drew its
strongest conclusions.

**The successor** (`serving/voi-stopping` at `086c24c0`, modelled after its
review fixes). It beats today's serving wherever checks are weak or moderate
(supported: −1.87 to −1.95 minutes per episode at Eedi's strength, −0.42 to
−1.35 at 0.9/10). It is family-dependent where they are strong, because it
keeps today's robust completion gate and values one check at a time.
**Dropping the gate and adding the lookahead** (`voi_p_with_fallback`: the
successor's abstention handling and serving rule kept) saves another
1.97–3.46 minutes per episode at 0.9/30 in three families (`nrm` −0.23
[−0.68, 0.23]), beats today's serving in every regime (supported in four of
five, directional in the fifth), is the only arm among every family's
co-winners at 0.9/30, and has the lowest mean regret of the 15 arms (0.09
minutes per episode; worst case 1.28, against 3.86 for the successor as
built and 3.60 for today's serving).

**Ranked proposal (§6):**

1. The robust completion gate must not end an episode while value decides
   (directional; never costs beyond noise).
2. Add the 2–3 check lookahead (directional where checks are strong; costs
   ≤ 0.20 minutes where they are weak; the minimax-regret choice).
3. `ROBUST_QUANTILE` 0.10 → 0.25 in the successor's value gate (directional
   now in every family).
4. Charge the measured unresolved cost (existing switch, off until the owner
   turns it on).

**Withdrawn from the first report:** handing a flip abstention to the robust
LCB instead of the nat scale (it buys nothing in any family, costs 0.56
[0.02, 1.14] minutes in one cell, and raises the worst case), and with it the
successor-scoped nat scale of 5, which would turn the kept fallback into EVSI
as built's under-probing. Serving `rank_feasible`'s top-ranked check
instead of the successor's choice is not proposed either: it costs 0.48–0.54
minutes at 0.9/30 in `cdm` and `nrm`. The gate on the kill-switch path, the
nat scale where nothing is at stake and the card's rows wait for live
`voi_forecasts` data; `PERTURBATION_DELTA`, the pseudo count, the burden and
the draws stay. Offline only: no serving code or default changed, no paid call.

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
means a different model in each family. The average is over the learners
holding each hypothesis **and** over the item pool a question's parameters
come from: every item's response probabilities are averaged, never its
parameters (Codex review F3; the first run took `nrm`'s softmax of the mean
item parameters, which put 0.59 instead of 0.51 on a holder's distractor in
one checked cell, and `cdm`'s rows from the mean item). Item parameters cannot transfer from
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
| `cdm` | 0.255 | 0.183 | 0.140 | 0.331 | 0.375 | 0.37 / 0.58 / 0.05 | 0.19 | 0.47 / 0.20 / 0.12 |
| `nrm` | 0.439 | 0.181 | 0.183 | 0.204 | 0.413 | 0.76 / 0.14 / 0.09 | 0.08 | 0.79 / 0.09 / 0.21 |
| `lta` | 0.373 | 0.200 | 0.147 | 0.275 | 0.322 | 0.47 / 0.36 / 0.16 | 0.00 | 0.66 / 0.13 / 0.23 |

The families disagree a lot about *who* holds a misconception: 14% (`nrm`) to
58% (`cdm`, where a holder can also have the skill and so is correct a third
of the time). They also disagree on how many learners need two repairs
(0–19%). They agree on the two numbers today's card gets wrong: consistency
0.25–0.44, not 0.83, and a knower's slip of 0.12–0.18, not 0.03. (After F3,
`nrm`'s system puts 0.18 on a knower's slip, not 0.14: averaging the item
parameters had made its knowers look surer than its items make them.)

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
| **`voi_proposed`** | the successor's structure (maximum lifted, decision stable / action equivalent kept, **its serving rule**: the highest-EIG check when it pays, else the best paying one) with exactly three changes: **no robust completion gate**, **a flip abstention never handed to the nat scale** (the robust LCB decides), and **the 2–3 check lookahead** (a paying batch's checks all pay) | the package this study proposes |
| `voi_p_with_gate`, `voi_p_with_fallback`, `voi_p_one_step` | `voi_proposed` with one piece of the successor put back: the robust completion gate / the successor's whole value gate (a flip abstention, or nothing at stake, decided by the nat scale) / no lookahead. With all three put back the package **is** `voi_successor`, decision for decision (tested) | leave-one-out ablations |
| `voi_p_top_value` | `voi_proposed` serving `rank_feasible`'s top-ranked paying check (a paying batch's first) instead of the successor's choice | the serving change the first run's package carried unawares (Codex review F1), now ablated on its own (`A4`) |

**No count bound.** The first run inherited the single-family study's
25-check safety bound, and it bound: an `nrm` learner's `eig_no_gate`
episode stopped at 25 checks that its rule would have continued (Codex
review F4). Every arm now runs without a bound: the bank is finite, so an
episode ends by its own rule or when its subject's questions run out, and
every cell counts the episodes the bank ended (Appendix A). The incumbent's,
`caps_only`'s and the floors' episode maximum (4) is today's serving rule,
not a bound. Every arm ends by taking the loss table's argmin action. Every
hypothesis in the simulation routes to its own repair, so for the successor a
decision is always at stake and its nat-scaled EIG decides only where
`rank_feasible` abstains (§7 on what that leaves untested).

**Verdicts.** Each claim is a signed paired difference per family (or a
measured quantity), from the stored per-learner episodes (paired within a
cell, 400 bootstrap draws). Only families that pass the adequacy gate on
held-out students vote (all four do; a failing or unvalidated family would be
excluded and listed), and a claim must cover every voting family's cell; one
with a cell missing, or with fewer than two voting families, is
`insufficient evidence` (Codex review F2). A family the study requires that
passed the gate but is absent from the report stays in that coverage, so its
absence leaves every claim `insufficient evidence` and every winner and regret
row incomplete (re-review F2). `supported`: every family's 95% CI
is on the claim's side; a value without a CI is never certified (the first
run certified `C1a` by a fixed 0.2 margin; it now carries a CI over the
bank's subjects). `directional`: every family's point estimate is, not every CI.
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
| `C1a` | **supported** | 4/4 | 4/4 | +0.42 [0.41, 0.44] ✓ | +0.25 [0.24, 0.26] ✓ | +0.44 [0.43, 0.45] ✓ | +0.37 [0.36, 0.39] ✓ |  |
| `C1b:incumbent` | **directional** | 4/4 | 3/4 | -0.10 [-0.18, -0.02] ✓ | -0.15 [-0.24, -0.05] ✓ | -0.14 [-0.22, -0.06] ✓ | -0.05 [-0.14, 0.02] ~ | -0.04 [-0.13, 0.05] ~ |
| `C1b:caps_only` | **supported** | 4/4 | 4/4 | -0.09 [-0.15, -0.01] ✓ | -0.16 [-0.24, -0.08] ✓ | -0.15 [-0.22, -0.08] ✓ | -0.07 [-0.14, -0.00] ✓ | -0.02 [-0.09, 0.06] ~ |
| `C1c` | **supported** | 4/4 | 4/4 | +0.10 [0.07, 0.13] ✓ | +0.10 [0.07, 0.13] ✓ | +0.04 [0.01, 0.08] ✓ | +0.09 [0.06, 0.12] ✓ |  |

Predicted information and realized information about the truth (nats per
check, fitted strength, repair 3), and the outcome log loss of the
incumbent's checks:

| Family | incumbent, hand-set: predicted EIG / realized truth gain [CI] | caps_only, hand-set | incumbent, family's model | outcome log loss hand-set / family (incumbent) |
|---|---|---|---|---|
| `lca` | 0.316 / -0.104 [-0.184, -0.020] | 0.307 / -0.087 [-0.150, -0.013] | 0.110 / +0.101 [0.073, 0.133] | 1.300 / 1.079 |
| `cdm` | 0.330 / -0.146 [-0.243, -0.047] | 0.332 / -0.157 [-0.240, -0.079] | 0.089 / +0.102 [0.073, 0.127] | 1.368 / 1.043 |
| `nrm` | 0.284 / -0.140 [-0.217, -0.056] | 0.287 / -0.150 [-0.225, -0.077] | 0.084 / +0.040 [0.012, 0.075] | 1.278 / 0.940 |
| `lta` | 0.340 / -0.055 [-0.140, 0.022] | 0.327 / -0.074 [-0.139, -0.004] | 0.102 / +0.091 [0.059, 0.120] | 1.354 / 1.107 |
| `lta_reveal` | 0.338 / -0.037 [-0.126, 0.046] | 0.328 / -0.020 [-0.086, 0.062] | 0.102 / +0.096 [0.063, 0.125] | 1.331 / 1.066 |

* **Supported in every family: the card is overconfident.** Fitted
  consistency is 0.25–0.44 against the card's 0.83 (`C1a`), and every
  family's 95% CI (subjects resampled) lies below it: `lca` 0.41–0.44, `cdm`
  0.24–0.26, `nrm` 0.43–0.45, `lta` 0.36–0.39. (The first report certified this
  by a fixed 0.2 margin with no CI.)
* **Under the card, the checks move belief away from the truth** in every
  family. The checks the incumbent picks are forecast at 0.28–0.34 nats each
  and realize −0.04 to −0.15 nats about the truth (`C1b:caps_only` supported:
  every CI is below 0; `C1b:incumbent` directional: `lta`'s CI reaches
  +0.02). Under each family's own calibrated model, the same chooser realizes
  +0.04 to +0.10 nats (`C1c` **supported**). In the first run `nrm`'s CI
  touched 0; that was F3, its system's mean-parameter rows, not the
  single-cause approximation.
* **What the card costs in minutes** (hand-set minus the family's calibrated
  model, fitted strength, repair 3):

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` |
|---|---:|---:|---:|---:|---:|
| `incumbent` | +0.40 | +0.37 | +0.42 | +0.52 | +0.61 |
| `caps_only` | -0.12 | -0.54 | +0.14 | +0.02 | +0.12 |
| `evsi` | +0.19 | +0.22 | +0.12 | +0.19 | +0.17 |
| `evsi_lookahead` | +0.33 | +0.42 | +0.18 | +0.31 | +0.29 |
| `eig` | +0.53 | +0.44 | +0.33 | +0.47 | +0.48 |
| `voi_successor` | +0.33 | +0.46 | +0.17 | +0.28 | +0.27 |
| `voi_proposed` | +0.33 | +0.46 | +0.17 | +0.31 | +0.29 |

The card costs today's serving 0.37–0.52 minutes per episode, the successor
0.17–0.46 and the package 0.17–0.46. `caps_only` alone gains in two families:
the overconfident card makes its decision-stable stop fire sooner, and at
Eedi's strength fewer checks is cheaper.

### 4.2 Where checks are as weak as Eedi's, value rules stop, and win

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C7:3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.87 [-1.99, -1.75] ✓ | -1.95 [-2.01, -1.90] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `C7:10` | **supported** | 4/4 | 4/4 | -1.92 [-2.20, -1.66] ✓ | -1.59 [-1.96, -1.22] ✓ | -1.92 [-2.08, -1.74] ✓ | -1.90 [-2.09, -1.71] ✓ | -1.37 [-1.67, -1.08] ✓ |
| `C7:30` | **directional** | 4/4 | 3/4 | -1.87 [-2.71, -1.07] ✓ | -0.79 [-1.90, 0.38] ~ | -1.82 [-2.28, -1.29] ✓ | -1.80 [-2.34, -1.21] ✓ | -0.22 [-1.13, 0.67] ~ |
| `C3w:fitted/3` | **supported** | 4/4 | 4/4 | -1.34 [-1.46, -1.22] ✓ | -1.55 [-1.66, -1.42] ✓ | -0.81 [-0.92, -0.71] ✓ | -1.42 [-1.52, -1.32] ✓ | -1.19 [-1.28, -1.08] ✓ |
| `C8w:fitted/3` | **supported** | 4/4 | 4/4 | -6.57 [-7.09, -6.11] ✓ | -8.23 [-8.78, -7.68] ✓ | -5.39 [-5.98, -4.80] ✓ | -6.80 [-7.27, -6.31] ✓ | -6.47 [-7.00, -5.94] ✓ |
| `C4b:fitted/3` | **supported** | 4/4 | 4/4 | -6.59 [-7.11, -6.14] ✓ | -8.31 [-8.87, -7.77] ✓ | -5.39 [-5.98, -4.80] ✓ | -6.81 [-7.28, -6.32] ✓ | -6.48 [-7.01, -5.95] ✓ |
| `C4b:fitted/30` | **supported** | 4/4 | 4/4 | -6.21 [-7.76, -4.88] ✓ | -8.05 [-9.62, -6.22] ✓ | -5.72 [-6.91, -4.66] ✓ | -6.11 [-7.20, -5.10] ✓ | -0.04 [-1.19, 1.16] ~ |

* `C7`: at the fitted strength, EVSI as built stops after the error that
  opened the episode. It beats the incumbent by 1.87–1.95 minutes per episode
  at repair 3 and by 1.59–1.92 at repair 10, in every family (supported). At
  repair 30 the result is directional (`cdm` −0.79 [−1.90, 0.38]). This
  confirms the single-family study's 3.77 vs 1.81.
* `C3w`: **here today's robust completion gate *saves* minutes**, 0.81–1.55
  per episode against the same caps without it, in every family
  (supported). It ends 174–331 of 400 incumbent episodes after the minimum two
  checks, and at Eedi's strength a third or fourth check is worth less than
  its minute.
* `C8w`, `C4b:fitted`: the EIG path with `VALUE_PER_NAT_MINUTES = 60`
  measures 5.4–8.4 checks per episode once its agreement gate is removed (no
  count bound now: up to 26–43 checks in an episode, Appendix A). Loss-derived
  EVSI beats it by 5.4–8.3 minutes, and so does the gate (supported).

### 4.3 Where checks are strong, EVSI as built under-probes

Consistency 0.9, repair 30 minutes (every regime is in Appendix A). Mean
minutes per episode (checks per episode; right-repair rate); the best per
family in bold:

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 13.13 (2.0; 0.72) | 13.15 (2.1; 0.83) | 11.08 (2.1; 0.84) | 13.12 (2.1; 0.72) | 12.58 (2.1; 0.73) |
| `caps_only` | 9.73 (2.8; 0.84) | 11.78 (2.6; 0.91) | 11.49 (2.6; 0.85) | 11.38 (2.8; 0.81) | 11.69 (2.8; 0.79) |
| `evsi` | 17.03 (0.0; 0.45) | 18.86 (0.0; 0.61) | 11.86 (0.0; 0.73) | 16.32 (0.0; 0.47) | 14.44 (0.0; 0.53) |
| `evsi_lcb_only` | 12.62 (0.8; 0.65) | 11.74 (1.6; 0.88) | 10.59 (0.2; 0.79) | 13.36 (0.8; 0.62) | 13.26 (0.7; 0.62) |
| `evsi_lookahead` | 10.04 (1.6; 0.78) | 11.08 (1.9; 0.91) | 10.41 (0.4; 0.80) | 11.40 (1.5; 0.74) | 11.48 (1.5; 0.73) |
| `eig` | 15.70 (0.3; 0.52) | 17.48 (0.4; 0.66) | 11.60 (0.0; 0.74) | 15.69 (0.2; 0.51) | 14.43 (0.2; 0.56) |
| `eig_no_gate` | **9.54 (4.4; 0.90)** | 13.03 (4.2; 0.92) | 12.45 (4.0; 0.86) | **10.02 (4.5; 0.89)** | 12.05 (5.2; 0.83) |
| `max_entropy` | 16.13 (3.2; 0.68) | 15.80 (3.1; 0.82) | 13.86 (2.8; 0.78) | 16.66 (3.2; 0.65) | 15.24 (3.2; 0.68) |
| `random` | 15.29 (3.2; 0.68) | 17.40 (3.2; 0.75) | 12.47 (2.7; 0.81) | 15.46 (3.2; 0.67) | 13.26 (3.1; 0.72) |
| `voi_successor` | 13.39 (0.7; 0.63) | 12.53 (1.4; 0.83) | 10.22 (0.2; 0.80) | 13.26 (0.7; 0.62) | 13.17 (0.6; 0.62) |
| `voi_proposed` | 9.84 (1.5; 0.78) | **10.53 (1.8; 0.92)** | **9.93 (0.4; 0.81)** | 11.52 (1.4; 0.73) | **10.97 (1.4; 0.74)** |
| `voi_p_with_gate` | 11.84 (1.1; 0.71) | 12.45 (1.4; 0.84) | 10.00 (0.3; 0.81) | 12.81 (1.0; 0.68) | 12.35 (1.0; 0.69) |
| `voi_p_with_fallback` | 9.93 (1.5; 0.78) | 10.54 (1.8; 0.92) | 10.00 (0.4; 0.81) | 11.30 (1.4; 0.73) | 11.19 (1.4; 0.73) |
| `voi_p_one_step` | 12.62 (0.8; 0.66) | 10.96 (1.7; 0.90) | 10.39 (0.3; 0.79) | 13.26 (0.7; 0.63) | 12.88 (0.7; 0.64) |
| `voi_p_top_value` | 10.16 (1.5; 0.77) | 11.07 (1.8; 0.91) | 10.41 (0.4; 0.80) | 11.23 (1.5; 0.74) | 11.39 (1.5; 0.73) |

The refitted `lca` reproduces the single-family study's 0.9/30 row: incumbent
13.13 vs 13.32, caps_only 9.73 vs 9.63, evsi 17.03 vs 17.94, evsi_lcb_only
12.62 vs 12.52, evsi_lookahead 10.04 vs 10.76.

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C2a` | **directional** | 4/4 | 3/4 | +3.90 [2.15, 5.67] ✓ | +5.71 [4.12, 7.37] ✓ | +0.78 [-0.51, 2.04] ~ | +3.20 [1.47, 4.71] ✓ | +1.86 [0.11, 3.73] ✓ |
| `C2b:0.9/30` | **supported** | 4/4 | 4/4 | +4.41 [2.90, 5.95] ✓ | +7.12 [5.58, 8.93] ✓ | +1.27 [0.46, 2.02] ✓ | +2.96 [1.65, 4.15] ✓ | +1.18 [-0.08, 2.47] ~ |
| `C2c:0.9/30` | **directional** | 4/4 | 3/4 | -2.59 [-3.83, -1.47] ✓ | -0.66 [-1.33, -0.09] ✓ | -0.18 [-0.62, 0.32] ~ | -1.96 [-3.09, -0.68] ✓ | -1.77 [-2.99, -0.62] ✓ |
| `C2d:0.9/30` | **directional** | 4/4 | 3/4 | -3.10 [-4.71, -1.68] ✓ | -2.07 [-3.06, -1.01] ✓ | -0.67 [-1.91, 0.38] ~ | -1.71 [-3.28, -0.20] ✓ | -1.09 [-2.74, 0.39] ~ |
| `C2e:0.9/30` | **family-dependent** | 2/4 | 0/4 | +0.31 [-1.00, 1.44] ✗ | -0.70 [-1.53, 0.29] ~ | -1.08 [-2.28, 0.01] ~ | +0.03 [-1.34, 1.56] ✗ | -0.20 [-1.74, 1.23] ~ |
| `C2b:0.9/10` | **supported** | 4/4 | 4/4 | +0.46 [0.03, 0.89] ✓ | +1.03 [0.66, 1.49] ✓ | +0.23 [0.07, 0.43] ✓ | +0.51 [0.16, 0.81] ✓ | +0.04 [-0.29, 0.38] ~ |
| `C2c:0.9/10` | **family-dependent** | 3/4 | 1/4 | -0.49 [-0.74, -0.23] ✓ | +0.03 [-0.14, 0.22] ✗ | -0.02 [-0.07, 0.01] ~ | -0.12 [-0.28, 0.02] ~ | -0.10 [-0.29, 0.06] ~ |
| `C2d:0.9/10` | **supported** | 4/4 | 4/4 | -1.00 [-1.47, -0.59] ✓ | -0.45 [-0.78, -0.06] ✓ | -1.38 [-1.78, -0.95] ✓ | -0.93 [-1.41, -0.48] ✓ | -0.88 [-1.38, -0.35] ✓ |
| `C2e:0.9/10` | **directional** | 4/4 | 2/4 | -0.40 [-0.85, 0.01] ~ | -0.33 [-0.73, 0.11] ~ | -1.89 [-2.35, -1.44] ✓ | -0.84 [-1.39, -0.29] ✓ | -1.09 [-1.63, -0.52] ✓ |
| `C2b:0.7/30` | **supported** | 4/4 | 4/4 | +1.16 [0.09, 2.23] ✓ | +5.70 [4.14, 7.09] ✓ | +0.73 [0.29, 1.23] ✓ | +1.06 [0.32, 1.86] ✓ | +0.54 [-0.38, 1.46] ~ |
| `C2c:0.7/30` | **directional** | 4/4 | 2/4 | -0.48 [-1.13, 0.27] ~ | -0.96 [-1.88, -0.06] ✓ | -0.17 [-0.51, 0.13] ~ | -0.80 [-1.43, -0.23] ✓ | -0.81 [-1.46, -0.26] ✓ |
| `C2d:0.7/30` | **directional** | 4/4 | 3/4 | -0.89 [-2.17, 0.37] ~ | -2.10 [-3.58, -0.78] ✓ | -1.84 [-2.57, -1.07] ✓ | -1.26 [-2.37, -0.23] ✓ | -0.21 [-1.49, 1.12] ~ |
| `C2e:0.7/30` | **directional** | 4/4 | 1/4 | -0.42 [-1.95, 0.95] ~ | -0.67 [-1.89, 0.65] ~ | -2.33 [-3.41, -1.19] ✓ | -0.88 [-2.14, 0.45] ~ | +0.19 [-1.39, 1.58] ✗ |
| `C3:0.9/30` | **family-dependent** | 3/4 | 3/4 | +3.40 [2.05, 4.96] ✓ | +1.37 [0.43, 2.23] ✓ | -0.41 [-1.35, 0.43] ✗ | +1.74 [0.44, 3.13] ✓ | +0.89 [-0.33, 2.15] ~ |
| `C3:0.9/10` | **family-dependent** | 3/4 | 1/4 | +0.60 [0.16, 1.10] ✓ | +0.12 [-0.19, 0.39] ~ | -0.51 [-0.82, -0.22] ✗ | +0.09 [-0.35, 0.54] ~ | -0.21 [-0.66, 0.22] ✗ |
| `C3:0.7/30` | **family-dependent** | 3/4 | 1/4 | +0.47 [-0.56, 1.61] ~ | +1.43 [0.42, 2.73] ✓ | -0.49 [-1.46, 0.50] ✗ | +0.38 [-0.86, 1.54] ~ | +0.40 [-0.87, 1.74] ~ |
| `C8:0.9/30` | **family-dependent** | 3/4 | 3/4 | +6.17 [4.49, 7.79] ✓ | +4.45 [2.84, 6.20] ✓ | -0.85 [-2.22, 0.56] ✗ | +5.67 [3.75, 7.36] ✓ | +2.37 [0.84, 4.22] ✓ |
| `C4b:0.9/10` | **supported** | 4/4 | 4/4 | -0.86 [-1.47, -0.34] ✓ | -1.85 [-2.38, -1.34] ✓ | -3.08 [-3.65, -2.47] ✓ | -1.41 [-1.99, -0.86] ✓ | -2.65 [-3.21, -2.05] ✓ |
| `C4b:0.9/30` | **family-dependent** | 2/4 | 2/4 | +3.09 [1.53, 4.65] ✗ | -1.29 [-2.50, -0.24] ✓ | -1.86 [-3.13, -0.35] ✓ | +3.34 [1.64, 4.94] ✗ | +1.21 [-0.34, 3.05] ✗ |

* `C2a` (directional): **EVSI as built costs more than the incumbent where
  checks are strong**, by +0.78 to +5.71 minutes at 0.9/30. The CI is above 0
  in three families; in `nrm` the difference is +0.78 [−0.51, 2.04].
* `C2b` (**supported** at 0.9/30, 0.9/10 and 0.7/30): **the flip abstention is
  the cause.** Ignoring it saves 1.27–7.12 minutes per episode at 0.9/30,
  0.23–1.03 at 0.9/10 and 0.73–5.70 at 0.7/30, with every family's CI above 0.
  At 0.9/30, `rank_feasible` abstains on a downstream-action flip (one
  ensemble member's best action changes after some answer) in 42–291 of 400
  episodes, each time where its robust value had already cleared the cost.
  It holds with the system calibrated to the wrong family too (§4.5).
* `C2c` (**directional** at 0.9/30 and 0.7/30, family-dependent at 0.9/10):
  **the 2–3 check lookahead** saves 0.66–2.59 minutes over the one-step rule
  at 0.9/30 in `lca`, `cdm` and `lta` (CIs below 0) and 0.18 [−0.32, 0.62] in
  `nrm`; at 0.7/30 0.17–0.96. In the first run `nrm` showed no gain (+0.03);
  F3's corrected system values its checks better. At 0.9/10 it saves 0.49 in
  `lca` and nothing elsewhere. In these regimes it never costs a measurable
  minute (inside the package it costs +0.19–0.20 where checks are weak, `A3`
  in §5).
* `C2d` (**supported** at 0.9/10, directional at 0.9/30 and 0.7/30): the
  lookahead beats the incumbent in every family, by 0.45–1.38 minutes at
  0.9/10 and 0.67–3.10 at 0.9/30, with the CI below 0 in three of four
  families at the two 30-minute regimes.
* `C2e` (family-dependent at 0.9/30, directional at 0.9/10 and 0.7/30):
  against the same caps without the gate, the lookahead is no reliable
  improvement at 0.9/30 (`lca` +0.31, `lta` +0.03). Fixed caps of four checks
  happen to suit strong checks at 30-minute stakes. The lookahead is near the
  best everywhere, not only there (§4.4).
* `C3` (family-dependent): **the robust completion gate's cost is the
  single-family study's family speaking.** At 0.9/30 the gate costs +3.40
  minutes in `lca` (the study's 3.7), +1.37 in `cdm`, +1.74 in `lta` and
  nothing in `nrm` (−0.41 [−1.35, 0.43]). At 0.9/10 it costs minutes only in
  `lca` (+0.60), and *saves* them in `nrm` (−0.51 [−0.82, −0.22]). Together
  with `C3w`, the gate helps where checks are weak and hurts where they are
  strong, by an amount the families do not agree on.
* `C8` (family-dependent): the EIG path's 90% agreement gate costs 4.5–6.2
  minutes at 0.9/30 in three families and saves 0.85 [−0.56, 2.22] in `nrm`.
* `C4b` at 0.9: loss-derived EVSI beats the nat-scaled EIG rule at 0.9/10 in
  every family (supported). At 0.9/30 the nat-scaled rule wins in `lca` and
  `lta` (+3.09, +3.34): it over-measures, and at 30-minute repairs
  over-measuring beats the one-step rule's under-measuring.

### 4.4 Which policy wins, by how much, and how robustly

Per regime: each family's winner (lowest mean minutes per episode), top-1
agreement, the rank agreement of all 15 arms (Kendall's τ-b, mean and minimum
over the six family pairs), the arms that no family can distinguish from its
best (paired 95% CI), and the most a family loses by acting on another
family's winner:

| Regime | `lca` winner (min) | `cdm` winner (min) | `nrm` winner (min) | `lta` winner (min) | Top-1 agreement | Kendall τ mean (min) | In every family's co-winners | Max regret of acting on another family's winner |
|---|---|---|---|---|---|---|---|---:|
| fitted/3 | `evsi` (1.75) | `evsi` (2.48) | `eig` (1.19) | `evsi` (1.72) | 3/4 | 0.95 (0.90) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_top_value`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.08 |
| fitted/10 | `evsi` (5.83) | `evsi` (8.25) | `evsi_lcb_only` (3.89) | `evsi` (5.72) | 3/4 | 0.69 (0.38) | `evsi`, `evsi_lcb_only`, `voi_p_one_step`, `voi_p_with_fallback`, `voi_successor` | 0.09 |
| fitted/30 | `evsi_lcb_only` (17.32) | `evsi_lcb_only` (24.07) | `voi_successor` (11.66) | `evsi` (17.18) | 2/4 | 0.58 (0.40) | `voi_p_one_step`, `voi_successor` | 0.68 |
| 0.7/3 | `evsi` (1.73) | `evsi` (2.23) | `evsi` (1.19) | `evsi` (1.70) | 4/4 | 0.98 (0.97) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_top_value`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.00 |
| 0.7/10 | `evsi_lcb_only` (5.52) | `evsi_lookahead` (6.74) | `evsi_lcb_only` (3.90) | `voi_p_with_fallback` (5.44) | 2/4 | 0.68 (0.43) | `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_top_value`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed` | 0.15 |
| 0.7/30 | `eig_no_gate` (15.15) | `voi_p_with_fallback` (15.49) | `voi_p_with_gate` (10.95) | `voi_p_with_fallback` (14.94) | 2/4 | 0.48 (0.24) | `evsi_lookahead`, `voi_p_top_value`, `voi_p_with_fallback` | 4.14 |
| 0.9/3 | `evsi` (1.70) | `voi_p_with_fallback` (1.92) | `evsi` (1.19) | `evsi` (1.65) | 3/4 | 0.85 (0.76) | `evsi`, `evsi_lcb_only`, `evsi_lookahead`, `voi_p_one_step`, `voi_p_top_value`, `voi_p_with_fallback`, `voi_p_with_gate`, `voi_proposed`, `voi_successor` | 0.02 |
| 0.9/10 | `voi_proposed` (4.71) | `voi_p_one_step` (5.14) | `voi_p_with_fallback` (3.69) | `voi_p_with_fallback` (4.78) | 2/4 | 0.71 (0.58) | `evsi_lookahead`, `voi_p_top_value`, `voi_p_with_fallback`, `voi_proposed` | 0.48 |
| 0.9/30 | `eig_no_gate` (9.54) | `voi_proposed` (10.53) | `voi_proposed` (9.93) | `eig_no_gate` (10.02) | 2/4 | 0.52 (0.33) | `voi_p_with_fallback` | 2.52 |

* **Where checks are weak or cheap to skip** (repair 3 at any strength, and
  the fitted strength with 10-minute repairs), every value rule stops and the
  rules tie. The families rank the arms alike (τ 0.85–0.98 at repair 3, 0.69
  at fitted/10), and acting on another family's winner costs at most 0.09
  minutes.
* **Where checks are strong and the stakes high** (0.7/30, 0.9/30), the
  families disagree about the winner (2/4 each), their rankings decorrelate
  (τ 0.48–0.52, minimum 0.24–0.33), and acting on another family's winner costs
  up to 2.5–4.1 minutes per episode. This is exactly where the single-family
  study drew its strongest policy conclusions, and where one family's verdict
  is least safe.
* **One arm is among every family's co-winners in eight of the nine
  regimes:** `voi_p_with_fallback` (the successor with the gate dropped and
  the lookahead added). At 0.9/30 it is the only one; at 0.7/30
  `evsi_lookahead` and `voi_p_top_value` join it, at 0.9/10 those two and
  `voi_proposed`. The exception is fitted/30, where the lookahead's
  occasional extra check costs 0.1–0.2 minutes and only the one-step rules
  (`voi_successor`, `voi_p_one_step`) are co-winners everywhere.

**RankCert's robust choice.** When the families disagree, ship the policy
whose worst case is least bad. Each arm's regret (its mean minutes minus the
cell's best) in every family × regime cell (36 fitted cells, every arm
complete in every cell; the `lta_reveal` stress world reported apart):

| Rank | Policy | Worst-case regret (min/episode) | Where | Mean regret | Cells within 0.1 min of the best | max `lca` | max `cdm` | max `nrm` | max `lta` | Stress worst (cell) |
|---:|---|---:|---|---:|---|---:|---:|---:|---:|---|
| 1 | `voi_p_top_value` | 1.21 | lta 0.9/30 | 0.13 | 26/36 | 0.62 | 0.54 | 0.48 | 1.21 | 0.42 (lta_reveal 0.9/30) |
| 2 | `voi_p_with_fallback` | 1.28 | lta 0.9/30 | 0.09 | 29/36 | 0.51 | 0.21 | 0.17 | 1.28 | 0.42 (lta_reveal fitted/30) |
| 3 | `evsi_lookahead` | 1.38 | lta 0.9/30 | 0.13 | 26/36 | 0.50 | 0.56 | 0.48 | 1.38 | 0.51 (lta_reveal 0.9/30) |
| 4 | `voi_proposed` | 1.50 | lta 0.9/30 | 0.10 | 28/36 | 0.34 | 0.56 | 0.10 | 1.50 | 0.41 (lta_reveal fitted/30) |
| 5 | `voi_p_with_gate` | 2.79 | lta 0.9/30 | 0.32 | 25/36 | 2.30 | 1.93 | 0.09 | 2.79 | 1.38 (lta_reveal 0.9/30) |
| 6 | `voi_p_one_step` | 3.24 | lta 0.9/30 | 0.32 | 24/36 | 3.08 | 1.31 | 0.46 | 3.24 | 1.91 (lta_reveal 0.9/30) |
| 7 | `evsi_lcb_only` | 3.34 | lta 0.9/30 | 0.35 | 25/36 | 3.09 | 1.22 | 0.66 | 3.34 | 2.29 (lta_reveal 0.9/30) |
| 8 | `caps_only` | 3.42 | cdm fitted/3 | 2.08 | 0/36 | 3.28 | 3.42 | 2.96 | 3.35 | 2.96 (lta_reveal fitted/3) |
| 9 | `incumbent` | 3.60 | lca 0.9/30 | 1.72 | 0/36 | 3.60 | 2.63 | 2.08 | 3.10 | 1.77 (lta_reveal fitted/3) |
| 10 | `voi_successor` | 3.86 | lca 0.9/30 | 0.43 | 23/36 | 3.86 | 2.25 | 0.29 | 3.24 | 2.19 (lta_reveal 0.9/30) |
| 11 | `max_entropy` | 6.64 | lta 0.9/30 | 3.16 | 0/36 | 6.59 | 5.28 | 3.93 | 6.64 | 4.27 (lta_reveal 0.9/30) |
| 12 | `random` | 6.87 | cdm 0.9/30 | 3.29 | 0/36 | 5.75 | 6.87 | 2.81 | 5.45 | 2.98 (lta_reveal fitted/3) |
| 13 | `eig` | 6.95 | cdm 0.9/30 | 1.00 | 16/36 | 6.17 | 6.95 | 1.67 | 5.67 | 3.45 (lta_reveal 0.9/30) |
| 14 | `eig_no_gate` | 8.31 | cdm fitted/3 | 4.17 | 3/36 | 6.59 | 8.31 | 5.73 | 6.81 | 6.48 (lta_reveal fitted/3) |
| 15 | `evsi` | 8.34 | cdm 0.9/30 | 1.15 | 18/36 | 7.49 | 8.34 | 1.93 | 6.29 | 3.47 (lta_reveal 0.9/30) |

**The four lookahead arms lead, 1.21–1.50 minutes per episode in the worst
case, all four in the same cell (`lta` 0.9/30)**, where the families cannot
tell them apart (`A2` and `A4` there span 0, §5). `voi_p_top_value` is first
(1.21) only through that cell: its serving rule costs 0.48–0.54 minutes in
`cdm` and `nrm` at 0.9/30 with the CI above 0 (`A4`), so it fails §6's
bounded-harm rule. **`voi_p_with_fallback` is second (1.28) and has the
lowest mean regret (0.09) and the most near-best cells (29 of 36)**; the
first report's package (`voi_proposed`, the fallback removed) is fourth
(1.50; mean 0.10, 28 of 36). In the first run the package's 1.21 was the top
of the table; with the successor's serving rule and the corrected `nrm`
system it is 1.50. Today's incumbent is never within 0.1 minutes of the best
(0/36; mean regret 1.72, worst 3.60). The successor as built improves the
mean (0.43) but not the worst case (3.86, `lca` 0.9/30). EVSI as built is the
worst value rule (8.34).

### 4.5 The system calibrated to the wrong family (rotation)

Every truth family × every other family's calibrated system (12 cells per
regime): does the conclusion survive a mis-calibrated system?

| Claim @ regime | Verdict | Cells holding | Cells certified | Effect range (minutes) | Cells against (truth ← system: effect [CI]) |
|---|---|---|---|---|---|
| `evsi_lookahead-incumbent@fitted/3` | **supported** | 12/12 | 12/12 | -2.12 to -1.93 |  |
| `evsi_lookahead-incumbent@0.9/10` | **directional** | 12/12 | 8/12 | -1.81 to -0.08 |  |
| `evsi_lookahead-incumbent@0.9/30` | **family-dependent** | 7/12 | 6/12 | -3.98 to +2.00 | lca←nrm: +1.14 [-0.02, 2.32]; cdm←nrm: +1.14 [-0.09, 2.37]; cdm←lta: +0.69 [-0.50, 1.95]; nrm←cdm: +2.00 [0.79, 3.29]; lta←nrm: +1.01 [-0.48, 2.32] |
| `evsi-evsi_lcb_only@fitted/3` | **no difference** | 0/12 | 0/12 | +0.00 to +0.00 | 12 cells |
| `evsi-evsi_lcb_only@0.9/10` | **family-dependent** | 11/12 | 8/12 | -0.23 to +1.67 | nrm←cdm: -0.23 [-0.69, 0.21] |
| `evsi-evsi_lcb_only@0.9/30` | **directional** | 12/12 | 9/12 | +0.48 to +7.50 |  |
| `incumbent-caps_only@fitted/3` | **contradicted** | 0/12 | 0/12 | -1.72 to -0.82 | 12 cells |
| `incumbent-caps_only@0.9/10` | **family-dependent** | 7/12 | 1/12 | -1.20 to +0.50 | cdm←lca: -0.04 [-0.42, 0.29]; cdm←nrm: -0.39 [-0.73, -0.07]; nrm←lca: -0.88 [-1.26, -0.52]; nrm←cdm: -1.20 [-1.56, -0.83]; nrm←lta: -0.59 [-0.98, -0.28] |
| `incumbent-caps_only@0.9/30` | **family-dependent** | 9/12 | 8/12 | -2.15 to +3.02 | nrm←lca: -0.97 [-2.08, 0.10]; nrm←cdm: -2.15 [-3.16, -1.06]; nrm←lta: -0.34 [-1.49, 0.54] |
| `evsi-incumbent@fitted/3` | **contradicted** | 0/12 | 0/12 | -2.12 to -1.93 | 12 cells |
| `evsi-incumbent@0.9/10` | **family-dependent** | 6/12 | 2/12 | -1.85 to +1.47 | lca←nrm: -0.41 [-0.87, 0.07]; nrm←lca: -1.85 [-2.40, -1.31]; nrm←cdm: -0.75 [-1.18, -0.27]; nrm←lta: -1.71 [-2.18, -1.21]; lta←lca: -0.41 [-1.06, 0.21]; lta←nrm: -0.47 [-0.97, 0.00] |
| `evsi-incumbent@0.9/30` | **family-dependent** | 10/12 | 10/12 | -1.45 to +8.57 | nrm←lca: -1.45 [-3.10, 0.14]; nrm←lta: -1.06 [-2.47, 0.44] |
| `voi_proposed-voi_successor@fitted/3` | **no difference** | 0/12 | 0/12 | +0.00 to +0.00 | 12 cells |
| `voi_proposed-voi_successor@0.9/10` | **family-dependent** | 8/12 | 1/12 | -0.34 to +0.66 | nrm←lca: +0.34 [0.13, 0.56]; nrm←cdm: +0.66 [0.39, 0.92]; nrm←lta: +0.20 [-0.02, 0.43]; lta←nrm: +0.04 [-0.04, 0.15] |
| `voi_proposed-voi_successor@0.9/30` | **family-dependent** | 9/12 | 8/12 | -3.67 to +1.81 | nrm←lca: +0.88 [-0.13, 1.80]; nrm←cdm: +1.81 [0.90, 2.86]; nrm←lta: +0.54 [-0.45, 1.62] |
| `voi_p_with_fallback-voi_successor@fitted/3` | **no difference** | 0/12 | 0/12 | +0.00 to +0.00 | 12 cells |
| `voi_p_with_fallback-voi_successor@0.9/10` | **family-dependent** | 8/12 | 1/12 | -0.32 to +0.62 | nrm←lca: +0.34 [0.10, 0.59]; nrm←cdm: +0.62 [0.36, 0.87]; nrm←lta: +0.21 [0.01, 0.44]; lta←nrm: +0.01 [-0.05, 0.11] |
| `voi_p_with_fallback-voi_successor@0.9/30` | **family-dependent** | 9/12 | 8/12 | -3.50 to +1.70 | nrm←lca: +0.95 [-0.13, 1.86]; nrm←cdm: +1.70 [0.71, 2.73]; nrm←lta: +0.40 [-0.48, 1.45] |

* The two `contradicted` rows at the fitted strength are the expected
  direction there (`C3w`, `C7`): the gate and EVSI as built save minutes
  where checks are weak, under every mis-calibrated system too.
* **The flip abstention costs minutes even under the wrong model**: in all 12
  cells at 0.9/30 (directional; 9 certified) and 11 of 12 at 0.9/10 (8
  certified; the exception, `nrm` truth with `cdm`'s system, −0.23
  [−0.69, 0.21]).
* The lookahead beats the incumbent in all 12 cells at the fitted strength
  and at 0.9/10. At 0.9/30 it fails in 5 of 12 cells, each with `nrm` as
  truth or system or `cdm`'s truth with `lta`'s system; one is certified
  against it (`nrm` truth, `cdm`'s system: +2.00 [0.79, 3.29]).
* The gate's cost stays family-dependent: with `nrm` as the truth, the gate
  saves minutes whatever system is calibrated.
* The package against the successor as built, with either abstention
  handling: no difference at the fitted strength. At 0.9/30 it holds in 9 of
  12 cells (8 certified); the three cells against it all have `nrm` as the
  truth (the worst, with `cdm`'s system, +1.81 [0.90, 2.86] for
  `voi_proposed` and +1.70 [0.71, 2.73] for `voi_p_with_fallback`). At 0.9/10
  it holds in 8 of 12 (1 certified); the `nrm`-truth cells cost +0.20 to
  +0.66. With `nrm` as the truth and another family's system, the successor's
  one-step stop is the better rule.


### 4.6 `VALUE_PER_NAT_MINUTES` = 60

Realized minutes per nat: the slope of a check's realized value on its
predicted EIG, under the family's calibrated model, on the incumbent's and
caps_only's checks:

| Regime | `lca` incumbent / caps_only | `cdm` incumbent / caps_only | `nrm` incumbent / caps_only | `lta` incumbent / caps_only |
|---|---|---|---|---|
| fitted/3 | -0.03 / 0.14 | 0.63 / 0.72 | 0.04 / 0.06 | 0.05 / -0.01 |
| fitted/10 | -0.09 / 0.46 | 2.11 / 2.39 | 0.14 / 0.21 | 0.17 / -0.03 |
| fitted/30 | -0.27 / 1.39 | 6.33 / 7.16 | 0.41 / 0.63 | 0.50 / -0.09 |
| 0.7/3 | 0.85 / 0.92 | 1.56 / 1.58 | 0.51 / 0.37 | 0.68 / 0.79 |
| 0.7/10 | 2.83 / 3.07 | 5.19 / 5.27 | 1.71 / 1.23 | 2.26 / 2.62 |
| 0.7/30 | 8.48 / 9.21 | 15.57 / 15.80 | 5.12 / 3.69 | 6.79 / 7.87 |
| 0.9/3 | 1.16 / 1.43 | 1.41 / 1.44 | 0.97 / 0.82 | 1.03 / 1.18 |
| 0.9/10 | 3.87 / 4.76 | 4.69 / 4.80 | 3.24 / 2.74 | 3.42 / 3.92 |
| 0.9/30 | 11.62 / 14.29 | 14.06 / 14.41 | 9.73 / 8.22 | 10.27 / 11.75 |

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C4` | **directional** | 4/4 | 2/4 | +14.29 [11.64, 17.07] ~ | +15.80 [12.35, 19.12] ~ | +9.73 [5.29, 13.61] ✓ | +11.75 [8.78, 14.24] ✓ |  |
| `C6:value_per_nat_minutes=10` | **supported** | 4/4 | 4/4 | -1.56 [-1.91, -1.13] ✓ | -2.01 [-2.50, -1.58] ✓ | -2.62 [-3.26, -2.05] ✓ | -1.62 [-2.01, -1.21] ✓ |  |

`robust_composition.VALUE_PER_NAT_MINUTES`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` eig/eig_no_gate | `cdm` eig/eig_no_gate | `nrm` eig/eig_no_gate | `lta` eig/eig_no_gate |
|---|---|---|---|---|
| 1 | 5.90 (+0.27 [0.01, 0.57]) / 5.90 (-0.47 [-1.18, 0.31]) | 6.33 (+0.28 [-0.05, 0.65]) / 6.33 (-0.66 [-1.37, 0.05]) | 4.07 (+0.11 [0.01, 0.24]) / 4.07 (-2.92 [-3.68, -2.21]) | 5.63 (+0.16 [-0.07, 0.43]) / 5.63 (-0.84 [-1.56, -0.08]) |
| 2.5 | 5.94 (+0.31 [0.04, 0.61]) / 5.74 (-0.63 [-1.32, 0.22]) | 6.25 (+0.20 [-0.06, 0.47]) / 5.98 (-1.02 [-1.70, -0.25]) | 3.96 (+0.01 [-0.05, 0.08]) / 3.80 (-3.19 [-3.93, -2.52]) | 5.63 (+0.16 [-0.05, 0.38]) / 5.61 (-0.86 [-1.56, -0.06]) |
| 5 | 5.61 (-0.02 [-0.03, -0.00]) / 4.75 (-1.62 [-2.20, -0.98]) | 6.01 (-0.04 [-0.10, 0.03]) / 4.84 (-2.15 [-2.67, -1.61]) | 3.94 (-0.01 [-0.03, 0.00]) / 3.97 (-3.01 [-3.67, -2.30]) | 5.46 (-0.01 [-0.02, 0.00]) / 5.00 (-1.47 [-2.03, -0.85]) |
| 10 | 5.61 (-0.01 [-0.03, -0.00]) / 4.81 (-1.56 [-1.91, -1.13]) | 5.99 (-0.06 [-0.10, -0.04]) / 4.99 (-2.01 [-2.50, -1.58]) | 3.94 (-0.01 [-0.03, 0.00]) / 4.37 (-2.62 [-3.26, -2.05]) | 5.46 (-0.01 [-0.02, 0.00]) / 4.85 (-1.62 [-2.01, -1.21]) |
| 20 | 5.62 (-0.01 [-0.02, 0.00]) / 5.29 (-1.08 [-1.31, -0.85]) | 6.01 (-0.04 [-0.06, -0.02]) / 5.73 (-1.26 [-1.60, -0.95]) | 3.94 (-0.01 [-0.03, 0.00]) / 5.12 (-1.86 [-2.33, -1.39]) | 5.46 (-0.01 [-0.02, 0.00]) / 5.41 (-1.06 [-1.30, -0.83]) |
| 40 | 5.62 (-0.00 [-0.01, 0.00]) / 6.09 (-0.28 [-0.35, -0.20]) | 6.04 (-0.01 [-0.03, -0.00]) / 6.62 (-0.37 [-0.53, -0.18]) | 3.95 (-0.00 [-0.01, 0.00]) / 6.40 (-0.59 [-0.85, -0.37]) | 5.46 (-0.01 [-0.02, 0.00]) / 6.07 (-0.40 [-0.50, -0.32]) |
| 60 (current) | 5.63 / 6.37 | 6.05 / 7.00 | 3.95 / 6.99 | 5.47 / 6.47 |
| 120 | 5.64 (+0.01 [0.00, 0.03]) / 7.11 (+0.74 [0.61, 0.88]) | 6.07 (+0.02 [0.00, 0.03]) / 8.26 (+1.27 [0.87, 1.71]) | 3.96 (+0.00 [0.00, 0.01]) / 8.24 (+1.26 [0.93, 1.69]) | 5.48 (+0.01 [0.00, 0.02]) / 7.29 (+0.82 [0.68, 0.99]) |

* `C4` (directional): **60 is above every measured minutes-per-nat in every
  family**: 3.8–6.2 times the largest one anywhere (`cdm` 15.8 at 0.7/30,
  `lca` 14.3 at 0.9/30, `lta` 11.8, `nrm` 9.7). Under the strict test (60 ≥ 4×
  the largest value's upper CI) it is certified in `nrm` and `lta` only. At
  the fitted strength, measured minutes per nat are below 1.4 in three
  families (negative for one of the two choosers in `lca` and `lta`) and up
  to 7.2 in `cdm`. A nat is worth about 0.27–0.48 × the repair minutes at consistency
  0.9 (`nrm` 0.27–0.32, `lta` 0.34–0.39, `lca` 0.39–0.48, `cdm` 0.47–0.48).
  The single-family "0.4–0.5 × repair" is again `lca`'s value; no constant
  fits every regime.
* `C6:value_per_nat_minutes=10` (**supported**): lowering the scale to 10
  saves 1.56–2.62 minutes per episode on the gate-free EIG rule at 0.9/10
  in every family. Each family's best value is 2.5–10, and **5 has the
  smallest worst-case regret across families** (0.17 minutes, against 0.57
  at 10 and 1.14 at 2.5); 5 also saves minutes with the CI below 0 in every
  family. With the agreement gate on, the scale hardly matters (|Δ| ≤ 0.31).
  This is a fact about the EIG rule. In the successor the nat scale's only
  simulated role is the fallback after a flip abstention, where 60 works
  because it is too high (§5, `A2`); §6 therefore does not lower it there.

### 4.7 Part C: charging the measured unresolved cost

`U` = Eedi's excess repeat rate 0.148 × encounters × 2 minutes per repeated
error. Paired Δ = measured − minutes-only, for `evsi_lookahead` (the
`evsi_lcb_only` rows agree):

| Strength | Encounters | U (min) | `lca` lookahead Δ [CI] (checks) | `cdm` lookahead Δ [CI] (checks) | `nrm` lookahead Δ [CI] (checks) | `lta` lookahead Δ [CI] (checks) |
|---|---:|---:|---|---|---|---|
| fitted | 3 | 0.89 | -0.05 [-0.11, 0.01] (0.00→0.00) | -0.04 [-0.09, 0.02] (0.00→0.00) | -0.01 [-0.04, 0.01] (0.00→0.00) | +0.00 [-0.03, 0.04] (0.00→0.00) |
| fitted | 6 | 1.78 | -0.01 [-0.10, 0.09] (0.00→0.00) | -0.04 [-0.14, 0.06] (0.00→0.00) | -0.04 [-0.09, 0.02] (0.00→0.00) | +0.00 [-0.05, 0.06] (0.00→0.00) |
| fitted | 12 | 3.55 | -0.25 [-0.46, -0.01] (0.00→0.00) | -0.08 [-0.28, 0.14] (0.00→0.00) | -0.05 [-0.15, 0.03] (0.00→0.00) | +0.01 [-0.11, 0.14] (0.00→0.00) |
| fitted | 24 | 7.10 | -0.57 [-1.04, -0.11] (0.00→0.03) | -0.71 [-1.14, -0.28] (0.00→0.01) | -0.08 [-0.25, 0.09] (0.00→0.00) | -0.18 [-0.52, 0.14] (0.00→0.01) |
| 0.9 | 3 | 0.89 | -0.05 [-0.14, 0.07] (0.07→0.17) | +0.02 [-0.04, 0.08] (0.06→0.11) | -0.01 [-0.05, 0.03] (0.00→0.01) | -0.01 [-0.09, 0.07] (0.04→0.16) |
| 0.9 | 6 | 1.78 | -0.11 [-0.27, 0.06] (0.07→0.24) | -0.08 [-0.22, 0.02] (0.06→0.20) | -0.08 [-0.15, -0.01] (0.00→0.03) | -0.06 [-0.19, 0.11] (0.04→0.26) |
| 0.9 | 12 | 3.55 | -0.53 [-0.80, -0.25] (0.07→0.46) | -0.27 [-0.50, -0.05] (0.06→0.46) | -0.21 [-0.34, -0.07] (0.00→0.10) | -0.25 [-0.49, -0.02] (0.04→0.43) |
| 0.9 | 24 | 7.10 | -1.54 [-2.05, -1.09] (0.07→0.86) | -1.16 [-1.62, -0.74] (0.06→0.88) | -0.58 [-0.88, -0.30] (0.00→0.22) | -1.28 [-1.69, -0.77] (0.04→1.09) |

`C5`'s value is the smallest `U` whose CI is below 0 at consistency 0.9; its
CI column is the `U` = 7.10 row's:

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C5` | **supported** | 4/4 | 4/4 | +3.55 [-2.05, -1.09] ✓ | +3.55 [-1.62, -0.74] ✓ | +1.78 [-0.88, -0.30] ✓ | +3.55 [-1.69, -0.77] ✓ |  |

* `C5` (**supported**): at consistency 0.9, charging the true `U` saves
  minutes in every family once it reaches 3.55 minutes (0.21–0.53 at 3.55,
  0.58–1.54 at 7.10; in `nrm` already 0.08 [0.01, 0.15] at 1.78). Below that
  nothing else is distinguishable from 0, and it never costs more than 0.02
  minutes. This confirms the single-family "pays off above ~3.6". At the
  fitted strength it pays only in `lca` (from 3.55) and `cdm` (at 7.10).

### 4.8 The robustness knobs

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `C6a` | **directional** | 4/4 | 0/4 | 8/8 under; q25 closer 6/8 ~ | 9/9 under; q25 closer 9/9 ~ | 5/5 under; q25 closer 5/5 ~ | 6/6 under; q25 closer 6/6 ~ |  |
| `C6:robust_quantile=0.25` | **directional** | 4/4 | 1/4 | -0.05 [-0.24, 0.17] ~ | -0.32 [-0.61, -0.09] ✓ | -0.07 [-0.18, 0.01] ~ | +0.00 [-0.25, 0.26] ~ |  |
| `C6:perturbation_delta=0.1` | **directional** | 4/4 | 0/4 | -0.05 [-0.14, 0.02] ~ | -0.02 [-0.09, 0.02] ~ | +0.00 [-0.01, 0.01] ~ | -0.09 [-0.18, 0.00] ~ |  |
| `C6:burden_cost=0.5` | **family-dependent** | 1/4 | 0/4 | +0.23 [-0.01, 0.54] ✗ | +0.00 [-0.24, 0.23] ~ | +0.12 [0.01, 0.25] ✗ | +0.19 [-0.02, 0.38] ✗ |  |
| `C6:repair_minutes=10` | **supported** | 4/4 | 4/4 | -1.01 [-1.52, -0.54] ✓ | -0.91 [-1.46, -0.39] ✓ | -0.34 [-0.56, -0.11] ✓ | -0.69 [-1.09, -0.30] ✓ |  |
| `C6:instrument_concentration=4` | **family-dependent** | 3/4 | 0/4 | -0.27 [-0.69, 0.17] ~ | -0.17 [-0.57, 0.25] ~ | -0.04 [-0.21, 0.13] ~ | +0.01 [-0.38, 0.38] ✗ |  |

* `ROBUST_QUANTILE` 0.10 → 0.25 (**directional**): it never costs minutes and
  saves 0.32 in `cdm` (`evsi_lookahead`, CI below 0). On `evsi_lcb_only` it
  saves 0.33 in `lca` and 0.28 in `cdm` (both CIs below 0), 0.07 in `nrm` and
  nothing in `lta` (sweep in Appendix B). Whether the 10th percentile
  under-predicts the value checks realize is now **directional** too (`C6a`):
  yes in every cell with value in every family (`lca` 8/8, `cdm` 9/9, `nrm`
  5/5, `lta` 6/6), and the 25th percentile is closer in 26 of those 28 cells.
  In the first run `nrm` said the opposite (0/5): its mean-parameter system
  over-predicted value (F3). `C6a` is a count of cells, not a CI, so it is
  never `supported`.
* `PERTURBATION_DELTA` 0.15 → 0.10: no decision effect in any family
  (|Δ| ≤ 0.09 minutes, every CI touching 0). Delta only feeds the flip
  abstention, and on `evsi_lcb_only` and `evsi_lookahead` every delta gives
  identical episodes.
* `BURDEN_COST` > 0 costs the lookahead minutes: +0.12 to +0.23 at 0.5 in
  three families (`cdm` +0.00), and +0.31 to +0.92 at 2 in every family. Keep
  it at 0.
* Assumed repair minutes: knowing the true 10 instead of the default 3 saves
  0.34–1.01 minutes for the lookahead (**supported**: every CI below 0).
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
| `cdm` | 0.9/10 | 1.301 / +0.271 | 1.022 / +0.279 | 1.010 / +0.271 | 1.018 / +0.271 | 1.024 / +0.281 | 0.963 / +0.277 | -0.0090 [-0.0324, 0.0127] |
| `cdm` | fitted/3 | 1.375 / -0.144 | 1.104 / +0.050 | 1.098 / +0.042 | 1.086 / +0.007 | 1.094 / -0.012 | 1.074 / +0.090 | +0.0127 [-0.0091, 0.0350] |
| `nrm` | 0.9/10 | 1.260 / -0.082 | 1.078 / +0.096 | 1.095 / +0.099 | 1.079 / +0.087 | 1.083 / +0.075 | 1.003 / +0.114 | +0.0160 [-0.0141, 0.0476] |
| `nrm` | fitted/3 | 1.321 / -0.146 | 1.126 / +0.011 | 1.079 / -0.140 | 1.054 / -0.228 | 1.097 / -0.058 | 1.026 / +0.027 | +0.0257 [-0.0034, 0.0557] |
| `lta` | 0.9/10 | 1.271 / +0.154 | 1.175 / +0.202 | 1.146 / +0.244 | 1.134 / +0.239 | 1.127 / +0.232 | 1.125 / +0.277 | +0.0112 [-0.0037, 0.0279] |
| `lta` | fitted/3 | 1.378 / -0.080 | 1.241 / +0.053 | 1.199 / +0.058 | 1.184 / +0.072 | 1.194 / +0.046 | 1.169 / +0.095 | +0.0146 [-0.0074, 0.0369] |

* **Not supported.** After the fix to `C6c`'s bootstrap (§8), no family×regime
  row shows a log-loss difference between 2 and 8 that its CI separates from
  0. Pseudo count 2 is ahead in 3 of 8 rows and 8 in 5. The single-family
  recommendation (2) was never simulated there; here it makes no measurable
  difference.
* **What matters is counting at all.** Any pseudo count from 0.5 to 32 takes
  the log loss from the frozen card's 1.26–1.38 to 1.01–1.24, most of the way
  to each family's calibrated rows (0.96–1.17). It also turns the card's
  negative information about the truth (−0.08 to −0.15 at the fitted
  strength) positive in most rows. The rest of the gap is structural: the
  card has three role rows shared across items, the families have per-item
  rows.

### 4.10 When the learner learns during probing

* **`lta` behaves like `lca` within an episode.** The fitted within-session
  transitions are near identity. `lta` agrees with `lca` in sign on 67 of
  75 paired claims; the eight exceptions are effects under 0.33 minutes per
  episode, and `lta` certifies only one of them (`S4` at 0.9/30, −0.17).
* **The reveal stress (`lta_reveal`)**: each answer's reveal teaches at the
  between-session rates (a holder moves on with probability 0.07, an unsure
  learner comes to know with 0.23). Learners then drift toward knowing during
  the episode, and a further check is worth less. The claims about EVSI as
  built weaken there: the flip abstention's cost, the gate's cost and the
  hand-set checks' negative information are no longer certified. The
  successor as built is no better than today's serving at the fitted strength
  with 30-minute repairs (−0.12 [−1.00, 0.73]). **The package's advantages
  hold**: against the successor −1.98 [−3.12, −0.82] at 0.9/30 with the
  fallback kept (−2.19 [−3.41, −1.08] without), the gate costing +1.38
  [0.37, 2.37] and the lookahead saving −1.91 [−2.95, −0.91] inside it, with
  a worst-case regret of 0.41–0.42 minutes.

## 5. The successor, as built and as proposed

Minutes per episode for the incumbent / `voi_successor` /
`voi_p_with_fallback` (fb: the successor with the gate dropped and the
lookahead added) / `voi_proposed` (fb without the abstention fallback);
checks per episode in brackets:

| Regime | `lca` inc / succ / fb / prop | `cdm` inc / succ / fb / prop | `nrm` inc / succ / fb / prop | `lta` inc / succ / fb / prop | `lta_reveal` inc / succ / fb / prop |
|---|---|---|---|---|---|
| fitted/3 | 3.69 / 1.75 / 1.75 / 1.75 (1.9/0.0/0.0/0.0) | 4.34 / 2.48 / 2.48 / 2.48 (2.0/0.0/0.0/0.0) | 3.15 / 1.19 / 1.19 / 1.19 (2.0/0.0/0.0/0.0) | 3.65 / 1.72 / 1.72 / 1.72 (1.9/0.0/0.0/0.0) | 3.30 / 1.53 / 1.53 / 1.53 (1.9/0.0/0.0/0.0) |
| fitted/10 | 7.75 / 5.83 / 5.83 / 5.86 (1.9/0.0/0.0/0.0) | 9.84 / 8.26 / 8.26 / 8.28 (2.0/0.0/0.0/0.0) | 5.89 / 3.92 / 3.92 / 3.92 (2.0/0.0/0.0/0.0) | 7.62 / 5.72 / 5.72 / 5.72 (1.9/0.0/0.0/0.0) | 6.47 / 5.10 / 5.10 / 5.10 (1.9/0.0/0.0/0.0) |
| fitted/30 | 19.35 / 17.71 / 17.83 / 17.66 (1.9/0.1/0.1/0.1) | 25.54 / 24.22 / 24.28 / 24.27 (2.0/0.1/0.2/0.2) | 13.74 / 11.66 / 11.68 / 11.68 (2.0/0.0/0.1/0.1) | 18.98 / 17.20 / 17.20 / 17.20 (1.9/0.0/0.0/0.0) | 15.52 / 15.40 / 15.40 / 15.40 (1.9/0.0/0.0/0.0) |
| 0.7/3 | 3.48 / 1.73 / 1.73 / 1.73 (2.0/0.0/0.0/0.0) | 3.69 / 2.23 / 2.23 / 2.23 (2.1/0.0/0.0/0.0) | 3.07 / 1.19 / 1.19 / 1.19 (2.0/0.0/0.0/0.0) | 3.48 / 1.70 / 1.70 / 1.70 (2.0/0.0/0.0/0.0) | 3.24 / 1.52 / 1.52 / 1.52 (2.0/0.0/0.0/0.0) |
| 0.7/10 | 6.83 / 5.55 / 5.56 / 5.53 (2.0/0.2/0.2/0.2) | 7.35 / 6.96 / 6.89 / 6.86 (2.1/0.6/0.6/0.6) | 5.59 / 3.92 / 3.92 / 3.92 (2.0/0.0/0.0/0.0) | 6.84 / 5.46 / 5.44 / 5.49 (2.0/0.2/0.2/0.2) | 6.06 / 5.03 / 4.99 / 5.03 (2.0/0.2/0.2/0.2) |
| 0.7/30 | 16.43 / 16.39 / 15.47 / 15.32 (2.0/0.3/0.7/0.7) | 17.80 / 17.75 / 15.49 / 16.05 (2.1/1.0/1.8/1.7) | 12.79 / 10.97 / 11.12 / 11.04 (2.0/0.1/0.2/0.2) | 16.45 / 15.69 / 14.94 / 15.07 (2.0/0.3/0.5/0.5) | 14.11 / 14.42 / 13.79 / 13.94 (2.0/0.3/0.5/0.5) |
| 0.9/3 | 3.14 / 1.73 / 1.73 / 1.72 (2.0/0.1/0.1/0.1) | 3.16 / 1.92 / 1.92 / 1.93 (2.1/0.1/0.1/0.1) | 2.98 / 1.19 / 1.19 / 1.19 (2.1/0.0/0.0/0.0) | 3.19 / 1.66 / 1.66 / 1.66 (2.1/0.0/0.0/0.0) | 3.13 / 1.50 / 1.50 / 1.51 (2.1/0.0/0.0/0.0) |
| 0.9/10 | 5.73 / 5.19 / 4.75 / 4.71 (2.0/0.3/0.6/0.6) | 5.75 / 5.33 / 5.21 / 5.14 (2.1/0.9/1.2/1.1) | 5.08 / 3.73 / 3.69 / 3.71 (2.1/0.1/0.1/0.1) | 5.76 / 4.93 / 4.78 / 4.80 (2.1/0.4/0.5/0.5) | 5.58 / 4.75 / 4.61 / 4.63 (2.1/0.3/0.5/0.5) |
| 0.9/30 | 13.13 / 13.39 / 9.93 / 9.84 (2.0/0.7/1.5/1.5) | 13.15 / 12.53 / 10.54 / 10.53 (2.1/1.4/1.8/1.8) | 11.08 / 10.22 / 10.00 / 9.93 (2.1/0.2/0.4/0.4) | 13.12 / 13.26 / 11.30 / 11.52 (2.1/0.7/1.4/1.4) | 12.58 / 13.17 / 11.19 / 10.97 (2.1/0.6/1.4/1.4) |

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `S1:fitted/3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.87 [-1.99, -1.75] ✓ | -1.95 [-2.01, -1.90] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `S2:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S3:fitted/3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.87 [-1.99, -1.75] ✓ | -1.95 [-2.01, -1.90] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `S4:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S5:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S6:fitted/3` | **supported** | 4/4 | 4/4 | -1.94 [-2.03, -1.86] ✓ | -1.87 [-1.99, -1.75] ✓ | -1.95 [-2.01, -1.90] ✓ | -1.94 [-2.00, -1.88] ✓ | -1.77 [-1.86, -1.68] ✓ |
| `S1:fitted/30` | **supported** | 4/4 | 4/4 | -1.64 [-2.38, -1.00] ✓ | -1.32 [-2.15, -0.47] ✓ | -2.08 [-2.48, -1.69] ✓ | -1.78 [-2.29, -1.18] ✓ | -0.12 [-1.00, 0.73] ~ |
| `S2:fitted/30` | **family-dependent** | 1/4 | 0/4 | -0.05 [-0.36, 0.35] ~ | +0.04 [-0.27, 0.37] ✗ | +0.02 [0.00, 0.04] ✗ | +0.00 [-0.01, 0.01] ✗ | +0.00 [-0.01, 0.01] ✗ |
| `S3:fitted/30` | **supported** | 4/4 | 4/4 | -1.69 [-2.42, -1.09] ✓ | -1.27 [-2.16, -0.40] ✓ | -2.06 [-2.46, -1.65] ✓ | -1.78 [-2.29, -1.18] ✓ | -0.12 [-1.00, 0.73] ~ |
| `S4:fitted/30` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S5:fitted/30` | **contradicted** | 0/4 | 0/4 | +0.12 [-0.14, 0.45] ✗ | +0.06 [-0.25, 0.38] ✗ | +0.02 [0.00, 0.04] ✗ | +0.00 [0.00, 0.01] ✗ | +0.00 [0.00, 0.01] ✗ |
| `S6:fitted/30` | **supported** | 4/4 | 4/4 | -1.51 [-2.21, -0.92] ✓ | -1.26 [-2.15, -0.49] ✓ | -2.07 [-2.46, -1.66] ✓ | -1.77 [-2.29, -1.18] ✓ | -0.12 [-1.00, 0.73] ~ |
| `S1:0.7/30` | **directional** | 4/4 | 1/4 | -0.05 [-1.04, 1.10] ~ | -0.05 [-0.98, 0.79] ~ | -1.81 [-2.43, -1.12] ✓ | -0.76 [-1.68, 0.23] ~ | +0.31 [-0.99, 1.49] ✗ |
| `S2:0.7/30` | **family-dependent** | 3/4 | 2/4 | -1.06 [-1.94, -0.31] ✓ | -1.70 [-2.76, -0.66] ✓ | +0.07 [-0.22, 0.37] ✗ | -0.62 [-1.22, 0.09] ~ | -0.48 [-1.20, 0.26] ~ |
| `S3:0.7/30` | **directional** | 4/4 | 3/4 | -1.11 [-2.39, 0.02] ~ | -1.75 [-3.16, -0.61] ✓ | -1.75 [-2.38, -1.01] ✓ | -1.37 [-2.44, -0.30] ✓ | -0.17 [-1.52, 1.08] ~ |
| `S4:0.7/30` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S5:0.7/30` | **family-dependent** | 3/4 | 3/4 | -0.92 [-1.76, -0.14] ✓ | -2.25 [-3.35, -1.21] ✓ | +0.14 [-0.16, 0.47] ✗ | -0.76 [-1.30, -0.15] ✓ | -0.62 [-1.26, -0.04] ✓ |
| `S6:0.7/30` | **directional** | 4/4 | 3/4 | -0.96 [-2.22, 0.16] ~ | -2.31 [-3.64, -1.13] ✓ | -1.67 [-2.35, -0.90] ✓ | -1.51 [-2.57, -0.52] ✓ | -0.32 [-1.65, 0.90] ~ |
| `S1:0.9/10` | **supported** | 4/4 | 4/4 | -0.54 [-1.05, -0.08] ✓ | -0.42 [-0.72, -0.08] ✓ | -1.35 [-1.76, -0.93] ✓ | -0.83 [-1.32, -0.42] ✓ | -0.83 [-1.34, -0.32] ✓ |
| `S2:0.9/10` | **directional** | 4/4 | 1/4 | -0.48 [-0.74, -0.22] ✓ | -0.19 [-0.41, 0.05] ~ | -0.01 [-0.06, 0.01] ~ | -0.13 [-0.31, 0.06] ~ | -0.12 [-0.36, 0.09] ~ |
| `S3:0.9/10` | **supported** | 4/4 | 4/4 | -1.03 [-1.46, -0.63] ✓ | -0.61 [-0.97, -0.22] ✓ | -1.37 [-1.78, -0.94] ✓ | -0.96 [-1.43, -0.59] ✓ | -0.94 [-1.42, -0.49] ✓ |
| `S4:0.9/10` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `S5:0.9/10` | **directional** | 4/4 | 1/4 | -0.44 [-0.69, -0.20] ✓ | -0.12 [-0.30, 0.09] ~ | -0.04 [-0.10, 0.01] ~ | -0.15 [-0.33, 0.01] ~ | -0.14 [-0.38, 0.06] ~ |
| `S6:0.9/10` | **supported** | 4/4 | 4/4 | -0.98 [-1.40, -0.57] ✓ | -0.54 [-0.87, -0.17] ✓ | -1.39 [-1.81, -0.98] ✓ | -0.99 [-1.46, -0.61] ✓ | -0.97 [-1.45, -0.52] ✓ |
| `S1:0.9/30` | **family-dependent** | 2/4 | 1/4 | +0.26 [-0.93, 1.52] ✗ | -0.63 [-1.11, -0.04] ✓ | -0.86 [-1.82, 0.27] ~ | +0.15 [-1.23, 1.23] ✗ | +0.59 [-0.67, 1.87] ✗ |
| `S2:0.9/30` | **directional** | 4/4 | 3/4 | -3.56 [-4.99, -2.35] ✓ | -2.00 [-2.95, -1.08] ✓ | -0.29 [-0.78, 0.18] ~ | -1.74 [-2.88, -0.54] ✓ | -2.19 [-3.41, -1.08] ✓ |
| `S3:0.9/30` | **supported** | 4/4 | 4/4 | -3.29 [-4.96, -1.88] ✓ | -2.63 [-3.56, -1.70] ✓ | -1.15 [-2.15, -0.10] ✓ | -1.59 [-2.96, -0.22] ✓ | -1.60 [-3.11, -0.23] ✓ |
| `S4:0.9/30` | **family-dependent** | 3/4 | 2/4 | +0.12 [-0.02, 0.40] ✗ | -0.01 [-0.03, -0.00] ✓ | -0.00 [-0.01, 0.00] ~ | -0.17 [-0.49, -0.01] ✓ | -0.10 [-0.27, -0.00] ✓ |
| `S5:0.9/30` | **directional** | 4/4 | 3/4 | -3.46 [-4.76, -2.20] ✓ | -1.99 [-2.85, -1.12] ✓ | -0.23 [-0.68, 0.23] ~ | -1.97 [-3.05, -0.83] ✓ | -1.98 [-3.12, -0.82] ✓ |
| `S6:0.9/30` | **supported** | 4/4 | 4/4 | -3.20 [-4.74, -1.85] ✓ | -2.62 [-3.45, -1.80] ✓ | -1.08 [-2.04, -0.05] ✓ | -1.82 [-3.22, -0.48] ✓ | -1.39 [-2.88, 0.06] ~ |

Each piece of the successor as built, put back into the package, and the
serving variant (leave-one-out; effect = the arm with the piece minus
`voi_proposed`):

| Claim | Verdict | Hold | Certified | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|---|---|---|
| `A1:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A2:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A3:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A4:fitted/3` | **no difference** | 0/4 | 0/4 | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A1:fitted/30` | **family-dependent** | 1/4 | 0/4 | -0.01 [-0.02, 0.00] ✗ | -0.01 [-0.03, 0.00] ✗ | +0.07 [-0.01, 0.20] ~ | +0.00 [0.00, 0.00] ✗ | +0.00 [0.00, 0.00] ✗ |
| `A2:fitted/30` | **family-dependent** | 3/4 | 0/4 | +0.17 [-0.13, 0.46] ~ | +0.01 [-0.20, 0.22] ~ | -0.00 [-0.01, 0.00] ✗ | +0.00 [0.00, 0.01] ~ | +0.00 [0.00, 0.01] ~ |
| `A3:fitted/30` | **contradicted** | 0/4 | 0/4 | +0.19 [0.02, 0.51] ✗ | +0.20 [0.02, 0.47] ✗ | +0.02 [0.00, 0.04] ✗ | +0.00 [0.00, 0.01] ✗ | +0.00 [0.00, 0.01] ✗ |
| `A4:fitted/30` | **family-dependent** | 3/4 | 0/4 | -0.16 [-0.61, 0.21] ~ | -0.08 [-0.24, 0.01] ~ | -0.01 [-0.03, 0.01] ~ | +0.07 [0.00, 0.23] ✗ | -0.07 [-0.30, 0.00] ~ |
| `A1:0.7/30` | **family-dependent** | 3/4 | 2/4 | +0.59 [0.13, 1.19] ✓ | +1.35 [0.37, 2.48] ✓ | -0.10 [-0.34, 0.14] ✗ | +0.43 [-0.05, 0.94] ~ | +0.13 [-0.39, 0.69] ~ |
| `A2:0.7/30` | **family-dependent** | 2/4 | 0/4 | +0.15 [-0.02, 0.40] ~ | -0.56 [-1.14, -0.02] ✗ | +0.08 [0.00, 0.23] ~ | -0.14 [-0.44, 0.02] ✗ | -0.14 [-0.44, 0.01] ✗ |
| `A3:0.7/30` | **directional** | 4/4 | 2/4 | -0.93 [-1.77, -0.15] ✓ | -0.75 [-1.51, 0.04] ~ | -0.02 [-0.24, 0.21] ~ | -0.57 [-1.11, -0.03] ✓ | -0.57 [-1.14, -0.10] ✓ |
| `A4:0.7/30` | **family-dependent** | 2/4 | 0/4 | +0.23 [-0.45, 0.93] ✗ | -0.35 [-1.07, 0.30] ~ | -0.09 [-0.41, 0.21] ~ | +0.12 [-0.20, 0.43] ✗ | -0.04 [-0.36, 0.29] ~ |
| `A1:0.9/10` | **family-dependent** | 3/4 | 1/4 | +0.12 [-0.01, 0.29] ~ | +0.07 [-0.11, 0.26] ~ | +0.00 [0.00, 0.00] ✗ | +0.11 [0.01, 0.24] ✓ | +0.17 [0.04, 0.32] ✓ |
| `A2:0.9/10` | **family-dependent** | 2/4 | 0/4 | +0.04 [-0.01, 0.12] ~ | +0.07 [-0.03, 0.21] ~ | -0.02 [-0.06, 0.00] ✗ | -0.03 [-0.10, 0.00] ✗ | -0.02 [-0.07, 0.01] ✗ |
| `A3:0.9/10` | **family-dependent** | 3/4 | 1/4 | -0.48 [-0.70, -0.23] ✓ | +0.00 [-0.14, 0.16] ✗ | -0.01 [-0.06, 0.01] ~ | -0.14 [-0.30, 0.02] ~ | -0.11 [-0.34, 0.08] ~ |
| `A4:0.9/10` | **family-dependent** | 1/4 | 0/4 | +0.03 [-0.15, 0.23] ✗ | +0.17 [-0.02, 0.41] ✗ | -0.01 [-0.08, 0.06] ~ | +0.03 [-0.20, 0.25] ✗ | +0.07 [-0.18, 0.28] ✗ |
| `A1:0.9/30` | **directional** | 4/4 | 3/4 | +2.00 [0.92, 3.16] ✓ | +1.93 [1.13, 2.81] ✓ | +0.07 [-0.30, 0.45] ~ | +1.29 [0.08, 2.39] ✓ | +1.38 [0.37, 2.37] ✓ |
| `A2:0.9/30` | **family-dependent** | 3/4 | 0/4 | +0.09 [-0.27, 0.46] ~ | +0.01 [-0.33, 0.47] ~ | +0.07 [-0.01, 0.22] ~ | -0.22 [-0.69, 0.16] ✗ | +0.21 [0.02, 0.52] ✓ |
| `A3:0.9/30` | **directional** | 4/4 | 3/4 | -2.78 [-3.94, -1.75] ✓ | -0.43 [-0.98, 0.09] ~ | -0.46 [-0.98, -0.01] ✓ | -1.74 [-2.81, -0.61] ✓ | -1.91 [-2.95, -0.91] ✓ |
| `A4:0.9/30` | **family-dependent** | 1/4 | 0/4 | +0.32 [-0.30, 1.00] ✗ | +0.54 [0.04, 1.12] ✗ | +0.48 [0.05, 1.01] ✗ | -0.29 [-1.31, 0.65] ~ | +0.42 [-0.36, 1.22] ✗ |

1. **The successor as built beats today's serving where checks are weak or
   moderate.** `S1` is supported at the fitted strength with 3- and
   30-minute repairs (−1.87 to −1.95 and −1.32 to −2.08 minutes per episode)
   and at 0.9/10 (−0.42 to −1.35). It stops after the opening error wherever
   a check is worth less than its minute, which at Eedi's strength is almost
   always. Its review fix F6 (a decision is at stake over the posterior
   support) matters. Before the fix, the arm measured 0.1–0.3 checks per
   episode at the fitted strength through the nat-scaled path and cost
   0.08–0.29 minutes more (the earlier run, §8).
2. **Where checks are strong and the stakes high, it is family-dependent
   against today's serving** (`S1` at 0.9/30: `cdm` −0.63 certified, `nrm`
   −0.86 [−1.82, 0.27]; `lca` +0.26 and `lta` +0.15). It keeps today's robust
   completion gate, which ends 16–98 of 400 episodes at 0.9/30 with
   `couldnt_reliably_distinguish` before value would stop them. It also
   values one check at a time. Its right-repair rate at 0.9/30 is 0.62–0.83,
   against 0.73–0.92 for the package.
3. **Dropping the gate and adding the lookahead** (`S5`,
   `voi_p_with_fallback`) costs the same as the successor where checks are
   weak (both stop: `no difference` at fitted/3; +0.00 to +0.12 at
   fitted/30, every CI reaching 0: `contradicted` only because no point
   estimate is below 0). At 0.9/30 it saves 1.97–3.46
   minutes per episode in `lca`, `cdm` and `lta` (`nrm` −0.23 [−0.68, 0.23]:
   directional); at 0.9/10 0.04–0.44 (directional); at 0.7/30 0.76–2.25 in
   three families with the CI below 0, `nrm` +0.14 [−0.16, 0.47]
   (family-dependent). Against today's serving (`S6`) it is **supported** at
   the fitted strength, at 0.9/10 and at 0.9/30, and directional at 0.7/30
   (`lca` −0.96 [−2.22, 0.16]). The first report's package (`voi_proposed`,
   also without the fallback: `S2`, `S3`) gives the same verdicts within
   noise.
4. **Each piece, put back into `voi_proposed`:**
   * **Robust completion gate** (`A1`): directional at 0.9/30 (+0.07 to +2.00
     minutes; 3 of 4 certified); at 0.7/30 it costs 0.43–1.35 in three
     families (two certified) and `nrm` −0.10 [−0.34, 0.14]; at 0.9/10
     +0.00 to +0.12. It never saves a measurable minute anywhere (the most
     negative effect is that −0.10). The gate's saving where checks are weak
     (`C3w`) belonged to the cap-only rules; a value rule already stops there.
     With the gate, worst-case regret rises from 1.50 to 2.79.
   * **The abstention's nat-scaled fallback** (`A2`): no measurable effect in
     19 of 20 family × regime cells (|Δ| ≤ 0.22 there). In one, `cdm` 0.7/30,
     keeping it **saves** 0.56 [0.02, 1.14] minutes; in the reveal stress
     world at 0.9/30 it costs 0.21 [0.02, 0.52]. Across 20 cells one such
     interval is about what chance alone gives, so the fallback is neutral.
     `rank_feasible` abstains only after its robust LCB has cleared the cost,
     and with 60 minutes per nat the EIG fallback almost always agrees and
     measures. **It is neutral only because 60 is too high** (§4.6): with a
     lower scale an abstention would stop instead, which is EVSI as built and
     its 0.2–7.1 minutes of under-probing (`C2b`). Removing the fallback buys
     nothing measurable and raises the worst case from 1.28 to 1.50, so §6 no
     longer proposes it.
   * **The lookahead** (`A3`): directional at 0.9/30 (−0.43 to −2.78; 3 of 4
     certified, `nrm` now among them at −0.46 [−0.98, −0.01]) and at 0.7/30
     (−0.02 to −0.93). At 0.9/10 it saves 0.48 in `lca` and nothing
     elsewhere. Where checks are weak it costs: +0.19 [0.02, 0.51] in `lca`
     and +0.20 [0.02, 0.47] in `cdm` at the fitted strength with 30-minute
     repairs (`contradicted` there: no family gains). Without it the
     package's worst-case regret more than doubles (3.24 vs 1.50).
   * **Serving `rank_feasible`'s top-ranked check** instead of the
     successor's choice (`A4`, `voi_p_top_value`): family-dependent in every
     regime. At 0.9/30 it costs +0.54 [0.04, 1.12] in `cdm` and +0.48
     [0.05, 1.01] in `nrm`, +0.32 [−0.30, 1.00] in `lca`, and saves 0.29
     [−0.65, 1.31] in `lta`; elsewhere |Δ| ≤ 0.35 with every CI reaching 0.
     This is the serving change the first report's package carried unawares
     (Codex review F1): its episodes are `voi_p_top_value`'s, identical in
     every `lca` and `lta` cell. It did not produce the reported gains; in
     `cdm` and `nrm` it diluted them.
   * **The stability stops** (`S4`, decision stable and action equivalent,
     now `voi_p_top_value` against `evsi_lookahead`, which differ by the
     stops alone): no difference in four of five regimes, and −0.17 to +0.12
     at 0.9/30. They are harmless and give each stop an honest label.
   * **The lifted episode maximum**: the package asks more than 4 checks in up
     to 26 of 400 episodes at 0.9/30 (at most 6–9). The successor as built
     exceeds 4 checks once in all 36 fitted cells (5 checks, `cdm`), because
     its gate stops it first.

The decomposition is now exact by construction: with the gate, the fallback
and no lookahead put back, the package **is** the successor (tested decision
for decision), and `A4` isolates the serving rule. `S2` and `S5` still need
not equal the sum of the `A` effects, because the pieces interact (the
lookahead adds checks that the gate would otherwise stop).

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
| 1 | **The robust completion gate does not stop an episode while value decides** | `A1` directional at 0.9/30: +0.07 to +2.00 minutes per episode when put back into the package (3/4 certified); +0.43 to +1.35 at 0.7/30 in three families, `nrm` −0.10 [−0.34, 0.14]. It never saves a measurable minute (the most negative effect is that `nrm` −0.10). Worst-case regret 2.79 → 1.50. It still holds under the reveal stress (+1.38 [0.37, 2.37]) | `diagnosis/probe_episodes.py:_evaluate_completion`: in the unstable branch, call `_robust_completion_override` only when `not voi_probe_site_active(vault)` or the new switch is on. When value decides, record the gate's verdict on the value stop's receipt as a counterfactual (as `voi_stopping.former_cap` does for the caps) instead of completing. `diagnosis/voi_stopping.py:probe_episode_decision` carries it in `former_cap` | `voi_stopping.robust_gate_with_value: bool = False` (true restores today's gate) |
| 2 | **Value the best 2–3 checks jointly when no single check pays** (lookahead) | `A3` directional at 0.9/30 (−0.43 to −2.78, 3/4 certified, `nrm` included) and at 0.7/30 (−0.02 to −0.93). Where checks are weak it costs: +0.19 [0.02, 0.51] (`lca`) and +0.20 [0.02, 0.47] (`cdm`) at fitted/30, within the 0.2-minute bound. Without it worst-case regret rises 1.50 → 3.24; it ships under the minimax rule | `scheduling/evsi.py`: a new `robust_batch_evsi(candidates, loss_table, *, k, quantile)`: per ensemble member, the product of the k candidates' tables (conditionally independent given the hypothesis), `evsi_for_conditionals`, then the robust quantile, as `evsi_calibration/policies.py:_paying_batch` does. `diagnosis/voi_stopping.py:value_candidates`: when a decision is at stake, `rank` did not abstain and no candidate continues, value `rank.ranked[:k]` for k = 2..max. If one batch's robust value exceeds the sum of its candidates' `lambda_time × minutes + burden`, continue with a check of the batch (which one: below), method `robust_evsi_lookahead_<k>`, reason `robust_evsi_batch_clears_minutes_cost`. The forecast body records the batch. The batch's checks all pay; serve the successor's choice among them (the highest-EIG one when it is in the batch, else the batch's top-ranked one), as `evsi_calibration/policies.py:decide_package` does | `voi_stopping.lookahead_max_checks: int = 3` (1 turns it off) |
| 3 | **`ROBUST_QUANTILE` 0.10 → 0.25 in the successor's value gate** | `C6a` directional: at the 10th percentile the members under-predict the value checks realize in every cell with value in every family (28 of 28), and the 25th percentile is closer in 26. `C6` directional: 0.25 never costs minutes and saves 0.32 (`cdm`, lookahead) and 0.28–0.33 (`lca`, `cdm`, one-step rule) with the CI below 0. *Simulated on the lookahead and one-step rules at 0.9/10, not inside the package.* In the first report this waited (`nrm` said the opposite); that was F3. Ship after ranks 1–2 | `diagnosis/voi_stopping.py:value_candidates`: pass `quantile=config.voi_stopping.robust_quantile` to `EV.rank_feasible` (today its default, `ROBUST_QUANTILE`) and use it for the EIG path's `robust_quantile(member_eigs, ...)` and rank 2's batch value; `heuristic_parameters` reports it (provenance `evsi_multisim`, source the config key). `robust_composition.ROBUST_QUANTILE` stays 0.10 for the mvp-0.8 paths | `voi_stopping.robust_quantile: float = 0.25` (0.10 restores today's) |
| 4 | **Charge the measured unresolved cost in the successor's loss table** | `C5` supported: at consistency 0.9 it saves 0.21–0.53 minutes per episode once `U` ≥ 3.55 and 0.58–1.54 at 7.10, in every family (`nrm` already at 1.78), and never costs more than 0.02 | After the successor takes main (Part C, `scheduling/unresolved_cost.py`, is on main since `3192d0c9`, not on the successor's base): `diagnosis/voi_stopping.py:VoiContext.loss_table` passes `unresolved_minutes=unresolved_minutes_for_hypotheses(repository, labels, pseudo_count=config.evsi.unresolved_cost_prior_pseudo_count)[0]` to `action_loss.build_loss_table` when `config.evsi.measured_loss_enabled`, and keys its cache on it. The receipt's `loss_model` parameter names the regime | the existing `evsi.measured_loss_enabled` (default off; the owner's history decides `U`) |
| 5 | Keep the stability stops, the lifted episode maximum, the successor's handling of a flip abstention (the nat-scaled fallback, at 60) and its serving rule | `S4`: no difference in four of five regimes, −0.17 to +0.12 at 0.9/30. `A2`: removing the fallback buys nothing measurable in 19 of 20 cells, costs 0.56 [0.02, 1.14] in `cdm` 0.7/30 and raises the worst case 1.28 → 1.50. `A4`: serving the top-ranked check costs 0.48–0.54 at 0.9/30 in `cdm` and `nrm` (CI above 0). The package uses the lifted maximum in up to 26/400 episodes at 0.9/30 | none | — |

Ranks 1–2 together are `voi_p_with_fallback`: the lowest mean regret of the
15 arms (0.09 minutes per episode), the most cells within 0.1 minutes of the
best (29 of 36), the only arm among every family's co-winners at 0.9/30, and
the second-smallest worst case (1.28, against 3.86 for the successor as built
and 3.60 for today's serving). The smallest worst case, `voi_p_top_value`'s
1.21, comes from one cell the families cannot separate (`lta` 0.9/30) and
fails the bounded-harm rule (`A4`). Ranks 1–4 are independent switches, so a
regression in one site can be switched off alone.

**Changed from the first report.** Its rank 3 (a flip abstention decided by
the robust LCB, not the nat scale) is withdrawn: with the successor's serving
rule and the corrected `nrm` system it buys nothing and raises the worst case
(`A2`). Its rank 4 (a successor-scoped nat scale of 5) depended on rank 3: in
the successor the same constant decides the abstention fallback that rank 5
now keeps, and 5 there would turn abstentions into stops, EVSI as built's
0.2–7.1 minutes of under-probing (`C2b`). It moves to §6.2. `ROBUST_QUANTILE`
moves from §6.2 to rank 3.

### 6.2 Wait for live `voi_forecasts` data (family-dependent)

| Change | Why it waits | The live measure that decides it |
|---|---|---|
| The nat scale where **nothing is at stake** (follow-up, teach-back and project-probe sites; hypotheses that share a repair) | `C4` directional: 60 is 3.8–6.2× the largest measured minutes per nat; `C6` supported: on the EIG rule 10 saves 1.56–2.62 minutes and 5 has the smallest worst-case regret across families (0.17). But none of those sites was simulated, and in the successor the same constant decides the abstention fallback (rank 5 keeps it at 60). A change needs its own, site-scoped constant | Per-site action-change calibration (report (c)) of the successor's `eig_value` decisions where nothing is at stake |
| The robust completion gate on the **kill-switch path** (value off, mvp-0.16) | `C3` family-dependent where checks are strong (−0.41 to +3.40 at 0.9/30), `C3w` supported where they are weak (it saves 0.81–1.55) | The live outcome calibration of probe forecasts (`learnloop evsi calibration`, report (a)): the owner's realized instrument consistency says which side of the line his checks are on |
| The lookahead's depth beyond 3, and its value at the follow-up and teach-back sites | Simulated only for probe episodes, k ≤ 3 | Per-site action-change calibration (report (c)) of `robust_evsi_lookahead_<k>` decisions |
| Any change to the card vocabulary's rows | `C1` is supported in every family (the card is overconfident and its checks mislead), but which rows replace it depends on the instrument type (§7.2) | The per-family conditional counts the cards already fold in (§4.9: counting at all recovers most of the gap) |

### 6.3 No change

| Parameter or rule | Why |
|---|---|
| The flip-abstention fallback and the serving rule | `A2`, `A4` (rank 5) |
| `PERTURBATION_DELTA` 0.15 | No decision effect in any family (\|Δ\| ≤ 0.09). It only feeds the flip abstention |
| `DEFAULT_CONDITIONAL_PSEUDO_COUNT` 8 | 8 → 2 is not supported (§4.9). Counting at all is what matters, and it is on |
| `BURDEN_COST` 0, `INSTRUMENT_PERTURBATION_CONCENTRATION` 40, `ROBUST_DRAW_COUNT` 128 | Positive burden costs minutes; the others move nothing consistently |
| `DEFAULT_INTERVENTION_MINUTES` 3.0 | Knowing the true repair minutes is worth 0.34–1.01 minutes per episode (supported), but that is a measurement (repair durations per repair class, the decision-value spec's Stage 2), not a better constant |

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
   family's population-average single-cause model, averaged over the
   learners and the item pool (it never knows a question's own parameters,
   and never represents two held misconceptions).
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
   contradictions. The CIs are per claim and per family, not adjusted for the
   number of comparisons: across 20 family × regime cells, one interval
   excluding 0 is about what chance alone gives (`A2`, §5).
9. **The bank is the only bound.** No episode has a count bound (F4), but a
   subject has a finite number of questions, so a rule that would keep
   checking stops when they run out. That happens mostly to the nat-scaled
   EIG rule without its gate (510–831 of its episodes per family across the
   nine regimes, up to 26–43 checks) and to the capped rules after the
   opening error; the value rules run out in under 50 episodes per family
   (Appendix A).

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
| `04af4cf8` | the Codex review's five fixes (below and [`evsi-multisim-codex-review.md`](evsi-multisim-codex-review.md)); this report is the rerun with them |
| `e3df1f50` | claims `S5`/`S6` and their rotation claim: the successor with only the gate dropped and the lookahead added, which the rerun made the recommendation |

**Fixed after the Codex review** (job `20261013-094805-rur4XA`; each with a
test that fails on the reviewed code; the study rerun with all five):

1. **F1, selection.** The package served `rank_feasible`'s top-ranked check
   while the successor serves the incumbent's highest-EIG check when it
   pays: an undocumented fourth change inside "the successor with three
   changes". The package now shares the successor's value gate and serving
   rule (with every piece put back it is the successor, decision for
   decision), and the top-value serving is its own arm (`voi_p_top_value`,
   claim `A4`).
2. **F2, certification.** The analyzer counted every family whatever its
   adequacy, and a family missing a cell silently stopped voting. Only
   adequate families vote now, a missing cell is `insufficient evidence`,
   exclusions are listed, and a value certifies only through a CI (`C1a`
   was certified by a fixed margin).
3. **F3, calibrated systems.** `nrm`'s system applied the softmax to the mean
   item parameters (and `cdm`'s used the mean item); both now average
   response probabilities over the item pool, and the strength calibration
   follows.
4. **F4, count bound.** The 25-check safety bound was active (an `nrm`
   `eig_no_gate` episode stopped at 25 checks, 31 minutes, that runs 40
   checks, 46 minutes, without it). The study now runs with no bound.
5. **F5, artifacts.** `--reanalyze` truncated the report before rewriting it;
   every fit and report is now written atomically.

**Fixed after the Codex re-review** (job `20261013-124855-mfsjE3`; each with a
test that fails on `2ccd0078`; neither changes this report's numbers, see
[`evsi-multisim-codex-review.md`](evsi-multisim-codex-review.md)):

1. **F2 (reopened), a required family's absence.** Deleting `nrm`'s results
   while keeping its passing validation and its place in the settings let the
   other three certify alone (`C2b:0.9/30` supported, 3/3; every regret row
   complete). A required, adequate family absent from the report now stays in
   every claim's coverage (`coverage_families`).
2. **F6, the `nrm` row cache.** The per-process cache of `nrm`'s system rows
   was keyed by the question id alone, so a revised bank with the same ids
   read the earlier bank's rows in one process. The key now carries the
   question's correct option and distractor labels.

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
# This report: the stored fits, every family, every arm (≈ 99 minutes on a loaded 32-core machine):
uv run learnloop evsi multisim --eedi-2024 fixtures-local/eedi-2024 \
    --fits fixtures-local/evsi-multisim/family_fits.json \
    --output fixtures-local/evsi-multisim-v4 --workers 12
# Re-score a stored report (no fit, no simulation; seconds):
uv run learnloop evsi multisim --reanalyze fixtures-local/evsi-multisim-v4/multisim_report.json
```

Report: `fixtures-local/evsi-multisim-v4/multisim_report.json` (gitignored;
re-scored after the run to add `S5`, `S6` and their rotation claim; the
as-run copy is `multisim_report.as-run.json` beside it;
family fits `fixtures-local/evsi-multisim/family_fits.json`, source hash
`70a1c5606097637b`). Seed 20261012; 400 learners per cell, 300 per
sensitivity arm, 32 ensemble draws, 400 bootstrap draws.
The first run's report (`fixtures-local/evsi-multisim-v3/`) is kept. Against
it, with the same seed, `lca`, `lta` and `lta_reveal` reproduced every arm's
per-learner episodes exactly (in every cell whose system is not calibrated to
`cdm` or `nrm`) except where the review changed them: `eig_no_gate` only for
learners the old bound had stopped at 25 checks, and the package arms, whose
serving rule changed; `voi_p_top_value` reproduced the first run's
`voi_proposed` in all 39 such cells. The first run had 181 episodes at the
bound across 54 cell × arm vectors. `cdm` and `nrm` change throughout (F3).

## 10. Paid calls and data

No paid call, no network, no vault: the study reads the Eedi 2024 Kaggle
files and the public Eedi NeurIPS 2020 archive from `fixtures-local/`
(gitignored, never committed), as the single-family stage did.

## 11. Gate

Run at `e3df1f50` (the last code commit; the review commits after it are
documentation only), in the worktree, `TMPDIR` under its `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8676 passed**, 0 failed, 0 skipped (5 min 2 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8582 deselected (1 min 48 s) |
| targeted: `tests/test_evsi_multisim.py`, `tests/test_evsi_calibration_sim.py`, `tests/test_evsi.py` | 48 passed |

No frontend, `src-tauri`, schema or migration change: the npm, cargo and DB
reference steps do not apply. The Codex review's own gate attempt could not
run (read-only sandbox); see the review file.

## 12. Open questions for the owner

1. **The shipping rule for a family-dependent change.** The lookahead (rank 2)
   costs 0.19–0.20 minutes per episode in two families where checks are weak
   and 30-minute repairs are at stake, but saves up to 2.78 where checks are
   strong, and without it the worst case more than doubles. Ship it under
   RankCert's minimax rule, behind `voi_stopping.lookahead_max_checks`?
   *Recommended: yes.*
2. **The robust completion gate.** Turn it off only where value decides (the
   successor path), and keep it on the kill-switch path, where it saves
   minutes at Eedi's strength? *Recommended: yes.*
3. **The flip abstention (changed from the first report).** Keep the
   successor's nat-scaled fallback after a flip abstention, at 60 minutes per
   nat, rather than letting the robust LCB decide? The rerun finds the two
   indistinguishable, with the fallback's worst case slightly better.
   *Recommended: keep it.*
4. **The nat scale where nothing is at stake.** The follow-up, teach-back and
   project-probe sites, and hypotheses that share a repair, were not
   simulated, and in the successor the same constant decides the abstention
   fallback. Give those sites their own constant once `voi_forecasts`
   measures them (the simulation's EIG rule favours about 5), or stop
   outright when no decision is at stake (the decision value is then zero by
   construction)? *Recommended: a separate, site-scoped constant, decided by
   live data; 60 stays on the abstention path.*
5. **`ROBUST_QUANTILE` 0.25 in the successor** (rank 3): directional in every
   family, simulated on the value rules at one regime, not inside the
   package. Ship it behind its switch now, or wait for the live quantile
   check? *Recommended: ship behind the switch; the live check confirms it.*
6. **Part C in the successor.** Leave `evsi.measured_loss_enabled` off until
   the owner's recurrence history gives `U` ≥ ~3.6 minutes for his
   misconceptions? *Recommended: off until then; the switch is the owner's.*
7. **The single-family study's own count bound.** Its arms keep
   `PolicySettings.safety_bound = 25`, which this review found binding in the
   multi-family study (F4). That study is merged and out of this stage's
   scope; rerun it without the bound before relying on its `eig_no_gate`
   numbers? *Recommended: yes, as a follow-up.*
   *Done 2026-10-13* ([`evsi-single-family-unbounded.md`](evsi-single-family-unbounded.md)): the bound stopped 2 of 400 `eig_no_gate` episodes at Eedi's strength; no other number, claim, conclusion or rank moved, and §6 stands.

## 13. Merge onto main (2026-10-13)

Merged onto main at `dd262244` (`evsi/calibration` tip `31841a2d`), after
sources, facet locks, UX Phase 1 (migrations 198-199) and the route-rules
successor (mvp-0.20). Main already had the branch's first part (merged at
`3192d0c9`). What landed: the four-family study and its ranked proposal
(this report), both Codex reviews, the single-family rerun without the
25-check bound ([`evsi-single-family-unbounded.md`](evsi-single-family-unbounded.md)),
and `learnloop evsi multisim` and `learnloop evsi compare`.

* **Offline only.** `git diff main...evsi/calibration --stat` lists 22 files,
  all in `src/learnloop/evsi_calibration/`, `src/learnloop/cli/evsi.py` (the
  two new subcommands and the offline study's default bound), `tests/` and
  `docs/reviews/`. No serving module imports `evsi_calibration` (only the
  CLI does). No config default, schema, migration or `apps/` change, so the
  defaults snapshots did not move.
* **Conflicts: none.** `tests/cli_help_snapshot.json` auto-merged, and
  `--write` regenerated it unchanged. The references were regenerated: only
  `source_commit` stamps and generator-derived citations moved (the
  `probe.episode` consumer line numbers in `policies.py`, `family_fit.py`
  among `forecasts`' source paths, `test_evsi_multisim.py` in
  `misconceptions`' test list). No counts moved, so the prose in
  `Configuration.md` and `Database.md` stands.
* **The successor this proposal targets is not on main yet.**
  `serving/voi-stopping` is still unmerged. Main has since used its label
  `mvp-0.17` for the proofs route check, so the successor lands under the
  next free tag. The study simulates the successor's rule offline, in
  `evsi_calibration/policies.py`. The only file the two branches share is
  `tests/cli_help_snapshot.json`; whichever lands second regenerates it.
* **Gate** at `37f2a667` (`TMPDIR` = the worktree's `fixtures-local/tmp`;
  `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`):
  `lint-imports` 17 kept, 0 broken; full suite `-n auto` **10,247 passed**,
  0 failed, 0 skipped (7 min 12 s, under heavy machine load); `-m durability`
  **99 passed** (1 min 44 s); targeted EVSI and CLI snapshot tests 92 passed;
  `db_validate_reference.py` `errors: []`. No frontend or `src-tauri` change,
  so those steps were not run. No paid call. The stored study reports remain
  under the `learnanything-evsi-cal` worktree's `fixtures-local/`
  (gitignored).

## Appendix A. Every regime

Mean minutes per episode (checks per episode; right-repair rate); best per
family in bold. 0.9/30 is in §4.3.

Every episode runs without a count bound (F4). Over the nine regimes, each
arm's largest number of checks in one episode, and the episodes that ended
because the subject's questions ran out (of 3,600 per family):

| Policy | `lca` max checks / ran out of questions | `cdm` max checks / ran out of questions | `nrm` max checks / ran out of questions | `lta` max checks / ran out of questions | `lta_reveal` max checks / ran out of questions |
|---|---|---|---|---|---|
| `incumbent` | 4 / 249 | 4 / 285 | 4 / 273 | 4 / 225 | 4 / 243 |
| `caps_only` | 4 / 321 | 4 / 342 | 4 / 282 | 4 / 276 | 4 / 288 |
| `evsi` | 1 / 36 | 1 / 39 | 1 / 45 | 1 / 36 | 1 / 45 |
| `evsi_lcb_only` | 7 / 37 | 7 / 44 | 5 / 45 | 6 / 37 | 6 / 46 |
| `evsi_lookahead` | 11 / 38 | 13 / 45 | 5 / 46 | 8 / 37 | 8 / 46 |
| `eig` | 5 / 72 | 3 / 111 | 5 / 48 | 5 / 60 | 5 / 69 |
| `eig_no_gate` | 26 / 510 | 35 / 831 | 43 / 717 | 34 / 513 | 35 / 675 |
| `max_entropy` | 4 / 315 | 4 / 357 | 4 / 267 | 4 / 285 | 4 / 294 |
| `random` | 4 / 324 | 4 / 366 | 4 / 273 | 4 / 282 | 4 / 294 |
| `voi_successor` | 3 / 37 | 5 / 45 | 3 / 45 | 4 / 37 | 4 / 46 |
| `voi_proposed` | 13 / 38 | 10 / 45 | 6 / 45 | 8 / 37 | 15 / 46 |
| `voi_p_with_gate` | 4 / 37 | 4 / 44 | 3 / 45 | 4 / 37 | 4 / 46 |
| `voi_p_with_fallback` | 9 / 38 | 11 / 45 | 6 / 45 | 9 / 37 | 8 / 46 |
| `voi_p_one_step` | 6 / 37 | 8 / 44 | 5 / 45 | 5 / 37 | 6 / 46 |
| `voi_p_top_value` | 11 / 38 | 13 / 45 | 5 / 46 | 8 / 37 | 8 / 46 |

**Fitted strength, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.69 (1.9; 0.46) | 4.34 (2.0; 0.44) | 3.15 (2.0; 0.74) | 3.65 (1.9; 0.45) | 3.30 (1.9; 0.56) |
| `caps_only` | 5.03 (3.3; 0.51) | 5.89 (3.6; 0.47) | 3.96 (2.8; 0.74) | 5.07 (3.4; 0.46) | 4.49 (3.3; 0.61) |
| `evsi` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `evsi_lcb_only` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `evsi_lookahead` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `eig` | 1.77 (0.0; 0.43) | 2.56 (0.1; 0.36) | **1.19 (0.0; 0.73)** | 1.73 (0.0; 0.43) | 1.54 (0.0; 0.49) |
| `eig_no_gate` | 8.34 (6.7; 0.55) | 10.79 (8.4; 0.51) | 6.58 (5.4; 0.75) | 8.53 (6.9; 0.50) | 8.01 (7.2; 0.75) |
| `max_entropy` | 5.08 (3.3; 0.47) | 5.93 (3.6; 0.47) | 3.99 (2.8; 0.76) | 5.07 (3.4; 0.45) | 4.45 (3.3; 0.61) |
| `random` | 5.09 (3.4; 0.47) | 6.10 (3.7; 0.41) | 4.00 (2.8; 0.75) | 5.11 (3.4; 0.44) | 4.51 (3.3; 0.61) |
| `voi_successor` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_proposed` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_with_gate` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_with_fallback` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_one_step` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |
| `voi_p_top_value` | **1.75 (0.0; 0.42)** | **2.48 (0.0; 0.36)** | **1.19 (0.0; 0.73)** | **1.72 (0.0; 0.43)** | **1.53 (0.0; 0.49)** |

**Fitted strength, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 7.75 (1.9; 0.46) | 9.84 (2.0; 0.44) | 5.89 (2.0; 0.74) | 7.62 (1.9; 0.45) | 6.47 (1.9; 0.56) |
| `caps_only` | 8.95 (3.3; 0.51) | 11.20 (3.6; 0.47) | 6.72 (2.8; 0.74) | 9.08 (3.4; 0.46) | 7.29 (3.3; 0.61) |
| `evsi` | **5.83 (0.0; 0.42)** | **8.25 (0.0; 0.36)** | 3.98 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `evsi_lcb_only` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | **3.89 (0.0; 0.74)** | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `evsi_lookahead` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | **3.89 (0.0; 0.74)** | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `eig` | 5.85 (0.0; 0.43) | 8.33 (0.1; 0.36) | 3.98 (0.0; 0.73) | 5.74 (0.0; 0.43) | 5.11 (0.0; 0.49) |
| `eig_no_gate` | 12.28 (6.7; 0.55) | 16.32 (8.4; 0.51) | 9.38 (5.4; 0.75) | 12.38 (6.9; 0.50) | 9.91 (7.2; 0.75) |
| `max_entropy` | 9.18 (3.3; 0.47) | 11.30 (3.6; 0.47) | 6.65 (2.8; 0.76) | 9.05 (3.4; 0.45) | 7.18 (3.3; 0.61) |
| `random` | 9.13 (3.4; 0.47) | 11.79 (3.7; 0.41) | 6.70 (2.8; 0.75) | 9.20 (3.4; 0.44) | 7.31 (3.3; 0.61) |
| `voi_successor` | 5.83 (0.0; 0.43) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_proposed` | 5.86 (0.0; 0.42) | 8.28 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_with_gate` | 5.86 (0.0; 0.42) | 8.28 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_with_fallback` | 5.83 (0.0; 0.43) | 8.26 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_one_step` | 5.86 (0.0; 0.42) | 8.28 (0.0; 0.36) | 3.92 (0.0; 0.73) | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |
| `voi_p_top_value` | 5.86 (0.0; 0.42) | 8.26 (0.0; 0.36) | **3.89 (0.0; 0.74)** | **5.72 (0.0; 0.43)** | **5.10 (0.0; 0.49)** |

**Fitted strength, repair 30**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 19.35 (1.9; 0.46) | 25.54 (2.0; 0.44) | 13.74 (2.0; 0.74) | 18.98 (1.9; 0.45) | 15.52 (1.9; 0.56) |
| `caps_only` | 20.15 (3.3; 0.51) | 26.34 (3.6; 0.47) | 14.62 (2.8; 0.74) | 20.53 (3.4; 0.46) | 15.29 (3.3; 0.61) |
| `evsi` | 17.48 (0.0; 0.42) | 24.75 (0.0; 0.36) | 11.93 (0.0; 0.73) | **17.18 (0.0; 0.43)** | 15.30 (0.0; 0.49) |
| `evsi_lcb_only` | **17.32 (0.1; 0.44)** | **24.07 (0.1; 0.39)** | 11.66 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `evsi_lookahead` | 17.50 (0.1; 0.44) | 24.19 (0.2; 0.39) | 11.67 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |
| `eig` | 17.50 (0.0; 0.43) | 24.83 (0.1; 0.36) | 11.93 (0.0; 0.73) | 17.18 (0.0; 0.43) | 15.31 (0.0; 0.49) |
| `eig_no_gate` | 23.53 (6.7; 0.55) | 32.12 (8.4; 0.51) | 17.39 (5.4; 0.75) | 23.38 (6.9; 0.50) | 15.37 (7.2; 0.75) |
| `max_entropy` | 20.88 (3.3; 0.47) | 26.65 (3.6; 0.47) | 14.25 (2.8; 0.76) | 20.45 (3.4; 0.45) | **14.98 (3.3; 0.61)** |
| `random` | 20.68 (3.4; 0.47) | 28.04 (3.7; 0.41) | 14.40 (2.8; 0.75) | 20.90 (3.4; 0.44) | 15.31 (3.3; 0.61) |
| `voi_successor` | 17.71 (0.1; 0.43) | 24.22 (0.1; 0.39) | **11.66 (0.0; 0.74)** | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_proposed` | 17.66 (0.1; 0.44) | 24.27 (0.2; 0.39) | 11.68 (0.1; 0.74) | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_p_with_gate` | 17.66 (0.1; 0.44) | 24.26 (0.2; 0.39) | 11.74 (0.0; 0.74) | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_p_with_fallback` | 17.83 (0.1; 0.43) | 24.28 (0.2; 0.39) | 11.68 (0.1; 0.74) | 17.20 (0.0; 0.43) | 15.40 (0.0; 0.49) |
| `voi_p_one_step` | 17.47 (0.1; 0.44) | 24.07 (0.1; 0.40) | 11.66 (0.0; 0.74) | 17.20 (0.0; 0.43) | 15.39 (0.0; 0.49) |
| `voi_p_top_value` | 17.50 (0.1; 0.44) | 24.19 (0.2; 0.39) | 11.67 (0.0; 0.74) | 17.27 (0.0; 0.43) | 15.32 (0.0; 0.49) |

**0.7, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.48 (2.0; 0.61) | 3.69 (2.1; 0.70) | 3.07 (2.0; 0.78) | 3.48 (2.0; 0.57) | 3.24 (2.0; 0.65) |
| `caps_only` | 4.50 (3.2; 0.69) | 4.42 (3.1; 0.78) | 3.76 (2.7; 0.79) | 4.46 (3.2; 0.65) | 4.19 (3.1; 0.71) |
| `evsi` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `evsi_lcb_only` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `evsi_lookahead` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `eig` | 1.81 (0.1; 0.46) | 2.38 (0.3; 0.51) | 1.20 (0.0; 0.73) | 1.72 (0.1; 0.47) | 1.57 (0.1; 0.52) |
| `eig_no_gate` | 6.38 (5.4; 0.79) | 7.12 (5.8; 0.80) | 5.84 (4.8; 0.81) | 6.78 (5.6; 0.73) | 6.76 (6.0; 0.81) |
| `max_entropy` | 4.79 (3.3; 0.60) | 4.64 (3.2; 0.76) | 3.88 (2.8; 0.78) | 4.85 (3.3; 0.56) | 4.51 (3.2; 0.63) |
| `random` | 4.83 (3.3; 0.57) | 5.20 (3.5; 0.64) | 3.83 (2.8; 0.79) | 4.84 (3.3; 0.56) | 4.43 (3.3; 0.65) |
| `voi_successor` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_proposed` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_with_gate` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_with_fallback` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_one_step` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |
| `voi_p_top_value` | **1.73 (0.0; 0.43)** | **2.23 (0.0; 0.49)** | **1.19 (0.0; 0.73)** | **1.70 (0.0; 0.44)** | **1.52 (0.0; 0.49)** |

**0.7, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 6.83 (2.0; 0.61) | 7.35 (2.1; 0.70) | 5.59 (2.0; 0.78) | 6.84 (2.0; 0.57) | 6.06 (2.0; 0.65) |
| `caps_only` | 7.47 (3.2; 0.69) | 7.52 (3.1; 0.78) | 6.23 (2.7; 0.79) | 7.47 (3.2; 0.65) | 6.66 (3.1; 0.71) |
| `evsi` | 5.74 (0.0; 0.43) | 7.45 (0.0; 0.49) | 3.95 (0.0; 0.73) | 5.68 (0.0; 0.44) | 5.08 (0.0; 0.50) |
| `evsi_lcb_only` | **5.52 (0.2; 0.49)** | 6.78 (0.6; 0.58) | **3.90 (0.0; 0.74)** | 5.52 (0.2; 0.48) | 5.00 (0.2; 0.53) |
| `evsi_lookahead` | 5.53 (0.2; 0.49) | **6.74 (0.6; 0.59)** | **3.90 (0.0; 0.74)** | 5.53 (0.2; 0.48) | **4.98 (0.2; 0.53)** |
| `eig` | 5.71 (0.1; 0.46) | 7.33 (0.3; 0.51) | 3.98 (0.0; 0.73) | 5.50 (0.1; 0.47) | 5.02 (0.1; 0.52) |
| `eig_no_gate` | 8.65 (5.4; 0.79) | 10.15 (5.8; 0.80) | 8.24 (4.8; 0.81) | 9.44 (5.6; 0.73) | 8.53 (6.0; 0.81) |
| `max_entropy` | 8.24 (3.3; 0.60) | 7.95 (3.2; 0.76) | 6.38 (2.8; 0.78) | 8.54 (3.3; 0.56) | 7.56 (3.2; 0.63) |
| `random` | 8.33 (3.3; 0.57) | 9.26 (3.5; 0.64) | 6.22 (2.8; 0.79) | 8.45 (3.3; 0.56) | 7.18 (3.3; 0.65) |
| `voi_successor` | 5.55 (0.2; 0.49) | 6.96 (0.6; 0.57) | 3.92 (0.0; 0.74) | 5.46 (0.2; 0.48) | 5.03 (0.2; 0.53) |
| `voi_proposed` | 5.53 (0.2; 0.49) | 6.86 (0.6; 0.58) | 3.92 (0.0; 0.74) | 5.49 (0.2; 0.49) | 5.03 (0.2; 0.53) |
| `voi_p_with_gate` | 5.53 (0.2; 0.49) | 6.86 (0.6; 0.58) | 3.92 (0.0; 0.74) | 5.49 (0.2; 0.49) | 5.03 (0.2; 0.53) |
| `voi_p_with_fallback` | 5.56 (0.2; 0.49) | 6.89 (0.6; 0.58) | 3.92 (0.0; 0.74) | **5.44 (0.2; 0.49)** | 4.99 (0.2; 0.53) |
| `voi_p_one_step` | 5.53 (0.2; 0.49) | 6.92 (0.6; 0.57) | 3.92 (0.0; 0.74) | 5.48 (0.2; 0.49) | 5.05 (0.2; 0.53) |
| `voi_p_top_value` | 5.53 (0.2; 0.49) | **6.74 (0.6; 0.59)** | **3.90 (0.0; 0.74)** | 5.53 (0.2; 0.48) | **4.98 (0.2; 0.53)** |

**0.7, repair 30**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 16.43 (2.0; 0.61) | 17.80 (2.1; 0.70) | 12.79 (2.0; 0.78) | 16.45 (2.0; 0.57) | 14.11 (2.0; 0.65) |
| `caps_only` | 15.97 (3.2; 0.69) | 16.37 (3.1; 0.78) | 13.28 (2.7; 0.79) | 16.07 (3.2; 0.65) | 13.71 (3.1; 0.71) |
| `evsi` | 17.19 (0.0; 0.43) | 22.35 (0.0; 0.49) | 11.86 (0.0; 0.73) | 17.05 (0.0; 0.44) | 15.24 (0.0; 0.50) |
| `evsi_lcb_only` | 16.03 (0.4; 0.53) | 16.66 (1.1; 0.69) | 11.12 (0.1; 0.76) | 15.99 (0.3; 0.50) | 14.71 (0.3; 0.54) |
| `evsi_lookahead` | 15.55 (0.7; 0.56) | 15.70 (1.7; 0.76) | 10.95 (0.1; 0.77) | 15.19 (0.5; 0.54) | 13.90 (0.5; 0.57) |
| `eig` | 16.86 (0.1; 0.46) | 21.48 (0.3; 0.51) | 11.93 (0.0; 0.73) | 16.30 (0.1; 0.47) | 14.87 (0.1; 0.52) |
| `eig_no_gate` | **15.15 (5.4; 0.79)** | 18.80 (5.8; 0.80) | 15.09 (4.8; 0.81) | 17.04 (5.6; 0.73) | **13.58 (6.0; 0.81)** |
| `max_entropy` | 18.09 (3.3; 0.60) | 17.40 (3.2; 0.76) | 13.53 (2.8; 0.78) | 19.09 (3.3; 0.56) | 16.26 (3.2; 0.63) |
| `random` | 18.33 (3.3; 0.57) | 20.86 (3.5; 0.64) | 13.07 (2.8; 0.79) | 18.75 (3.3; 0.56) | 15.03 (3.3; 0.65) |
| `voi_successor` | 16.39 (0.3; 0.52) | 17.75 (1.0; 0.65) | 10.97 (0.1; 0.76) | 15.69 (0.3; 0.50) | 14.42 (0.3; 0.55) |
| `voi_proposed` | 15.32 (0.7; 0.57) | 16.05 (1.7; 0.74) | 11.04 (0.2; 0.77) | 15.07 (0.5; 0.54) | 13.94 (0.5; 0.57) |
| `voi_p_with_gate` | 15.91 (0.5; 0.55) | 17.40 (1.3; 0.68) | **10.95 (0.1; 0.77)** | 15.50 (0.4; 0.51) | 14.07 (0.4; 0.56) |
| `voi_p_with_fallback` | 15.47 (0.7; 0.56) | **15.49 (1.8; 0.76)** | 11.12 (0.2; 0.77) | **14.94 (0.5; 0.54)** | 13.79 (0.5; 0.58) |
| `voi_p_one_step` | 16.25 (0.4; 0.52) | 16.80 (1.2; 0.69) | 11.06 (0.1; 0.76) | 15.64 (0.3; 0.51) | 14.51 (0.3; 0.55) |
| `voi_p_top_value` | 15.55 (0.7; 0.56) | 15.70 (1.7; 0.76) | 10.95 (0.1; 0.77) | 15.19 (0.5; 0.54) | 13.90 (0.5; 0.57) |

**0.9, repair 3**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 3.14 (2.0; 0.72) | 3.16 (2.1; 0.83) | 2.98 (2.1; 0.84) | 3.19 (2.1; 0.72) | 3.13 (2.1; 0.73) |
| `caps_only` | 3.52 (2.8; 0.84) | 3.48 (2.6; 0.91) | 3.52 (2.6; 0.85) | 3.68 (2.8; 0.81) | 3.73 (2.8; 0.79) |
| `evsi` | **1.70 (0.0; 0.45)** | 1.93 (0.0; 0.60) | **1.19 (0.0; 0.73)** | **1.65 (0.0; 0.46)** | **1.47 (0.0; 0.52)** |
| `evsi_lcb_only` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `evsi_lookahead` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `eig` | 1.80 (0.3; 0.52) | 2.08 (0.4; 0.66) | 1.20 (0.0; 0.74) | 1.79 (0.2; 0.51) | 1.67 (0.2; 0.56) |
| `eig_no_gate` | 4.88 (4.4; 0.90) | 5.07 (4.2; 0.92) | 4.82 (4.0; 0.86) | 5.09 (4.5; 0.89) | 5.84 (5.2; 0.83) |
| `max_entropy` | 4.52 (3.2; 0.68) | 4.33 (3.1; 0.82) | 3.87 (2.8; 0.78) | 4.58 (3.2; 0.65) | 4.37 (3.2; 0.68) |
| `random` | 4.42 (3.2; 0.68) | 4.64 (3.2; 0.75) | 3.70 (2.7; 0.81) | 4.39 (3.2; 0.67) | 4.14 (3.1; 0.72) |
| `voi_successor` | 1.73 (0.1; 0.47) | **1.92 (0.1; 0.61)** | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.50 (0.0; 0.53) |
| `voi_proposed` | 1.72 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `voi_p_with_gate` | 1.72 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `voi_p_with_fallback` | 1.73 (0.1; 0.47) | **1.92 (0.1; 0.61)** | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.50 (0.0; 0.53) |
| `voi_p_one_step` | 1.72 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |
| `voi_p_top_value` | 1.74 (0.1; 0.47) | 1.93 (0.1; 0.61) | **1.19 (0.0; 0.73)** | 1.66 (0.0; 0.47) | 1.51 (0.0; 0.52) |

**0.9, repair 10**

| Policy | `lca` | `cdm` | `nrm` | `lta` | `lta_reveal` (stress) |
|---|---|---|---|---|---|
| `incumbent` | 5.73 (2.0; 0.72) | 5.75 (2.1; 0.83) | 5.08 (2.1; 0.84) | 5.76 (2.1; 0.72) | 5.58 (2.1; 0.73) |
| `caps_only` | 5.13 (2.8; 0.84) | 5.63 (2.6; 0.91) | 5.59 (2.6; 0.85) | 5.67 (2.8; 0.81) | 5.79 (2.8; 0.79) |
| `evsi` | 5.68 (0.0; 0.45) | 6.31 (0.0; 0.61) | 3.96 (0.0; 0.73) | 5.46 (0.0; 0.47) | 4.84 (0.0; 0.53) |
| `evsi_lcb_only` | 5.22 (0.3; 0.56) | 5.28 (1.0; 0.77) | 3.72 (0.1; 0.77) | 4.96 (0.4; 0.57) | 4.80 (0.4; 0.59) |
| `evsi_lookahead` | 4.73 (0.6; 0.63) | 5.30 (1.1; 0.79) | 3.71 (0.1; 0.77) | 4.83 (0.6; 0.60) | 4.70 (0.6; 0.62) |
| `eig` | 5.40 (0.3; 0.52) | 6.08 (0.4; 0.66) | 3.90 (0.0; 0.74) | 5.39 (0.2; 0.51) | 4.97 (0.2; 0.56) |
| `eig_no_gate` | 6.09 (4.4; 0.90) | 7.13 (4.2; 0.92) | 6.80 (4.0; 0.86) | 6.37 (4.5; 0.89) | 7.45 (5.2; 0.83) |
| `max_entropy` | 7.53 (3.2; 0.68) | 7.30 (3.1; 0.82) | 6.46 (2.8; 0.78) | 7.71 (3.2; 0.65) | 7.19 (3.2; 0.68) |
| `random` | 7.24 (3.2; 0.68) | 7.95 (3.2; 0.75) | 5.97 (2.7; 0.81) | 7.26 (3.2; 0.67) | 6.51 (3.1; 0.72) |
| `voi_successor` | 5.19 (0.3; 0.56) | 5.33 (0.9; 0.76) | 3.73 (0.1; 0.77) | 4.93 (0.4; 0.57) | 4.75 (0.3; 0.59) |
| `voi_proposed` | **4.71 (0.6; 0.63)** | **5.14 (1.1; 0.81)** | 3.71 (0.1; 0.77) | 4.80 (0.5; 0.60) | 4.63 (0.5; 0.62) |
| `voi_p_with_gate` | 4.83 (0.5; 0.61) | 5.21 (1.0; 0.79) | 3.71 (0.1; 0.77) | 4.91 (0.5; 0.59) | 4.80 (0.5; 0.61) |
| `voi_p_with_fallback` | 4.75 (0.6; 0.62) | 5.21 (1.2; 0.81) | **3.69 (0.1; 0.77)** | **4.78 (0.5; 0.61)** | **4.61 (0.5; 0.63)** |
| `voi_p_one_step` | 5.18 (0.4; 0.56) | **5.14 (1.0; 0.79)** | 3.73 (0.1; 0.77) | 4.94 (0.4; 0.57) | 4.74 (0.4; 0.59) |
| `voi_p_top_value` | 4.73 (0.6; 0.63) | 5.30 (1.1; 0.79) | 3.71 (0.1; 0.77) | 4.83 (0.6; 0.60) | 4.70 (0.6; 0.62) |

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
| `voi_proposed` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |
| `voi_p_with_gate` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |
| `voi_p_with_fallback` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.01 (0.1; 0.45) | 1.81 (0.1; 0.50) |
| `voi_p_one_step` | 2.08 (0.1; 0.44) | 2.93 (0.2; 0.39) | 1.36 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.81 (0.1; 0.50) |
| `voi_p_top_value` | 2.08 (0.1; 0.44) | 2.89 (0.2; 0.40) | 1.37 (0.1; 0.72) | 2.02 (0.1; 0.45) | 1.82 (0.1; 0.49) |

## Appendix B. Sensitivity sweeps (0.9/10)

`robust_composition.ROBUST_QUANTILE`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.05 | 5.90 (+0.00 [0.00, 0.00]) / 5.50 (+0.05 [-0.14, 0.27]) / 4.85 (+0.02 [-0.12, 0.17]) | 6.32 (+0.00 [-0.01, 0.02]) / 5.37 (+0.15 [-0.08, 0.39]) / 5.26 (-0.03 [-0.29, 0.24]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.76 (+0.01 [-0.09, 0.11]) / 3.74 (+0.01 [-0.09, 0.11]) | 5.55 (-0.03 [-0.10, 0.00]) / 5.31 (+0.26 [0.01, 0.55]) / 5.05 (+0.12 [-0.07, 0.36]) |
| 0.1 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 0.25 | 5.91 (+0.00 [0.00, 0.01]) / 5.12 (-0.33 [-0.66, -0.05]) / 4.77 (-0.05 [-0.24, 0.17]) | 6.28 (-0.03 [-0.09, 0.00]) / 4.95 (-0.28 [-0.50, -0.09]) / 4.97 (-0.32 [-0.61, -0.09]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.68 (-0.07 [-0.18, 0.01]) / 3.66 (-0.07 [-0.18, 0.01]) | 5.57 (-0.01 [-0.02, 0.01]) / 5.06 (+0.01 [-0.18, 0.21]) / 4.93 (+0.00 [-0.25, 0.26]) |
| 0.5 | 5.87 (-0.03 [-0.09, 0.00]) / 4.97 (-0.48 [-0.85, -0.17]) / 4.75 (-0.08 [-0.33, 0.19]) | 6.25 (-0.07 [-0.17, 0.00]) / 4.95 (-0.28 [-0.61, 0.04]) / 4.96 (-0.33 [-0.66, -0.00]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.66 (-0.09 [-0.21, 0.00]) / 3.68 (-0.05 [-0.18, 0.08]) | 5.54 (-0.04 [-0.10, 0.00]) / 5.17 (+0.12 [-0.19, 0.45]) / 5.01 (+0.09 [-0.27, 0.45]) |

`evsi.PERTURBATION_DELTA`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.05 | 5.94 (+0.03 [-0.10, 0.17]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.22 (-0.09 [-0.22, 0.01]) / 5.23 (+0.00 [0.00, 0.00]) / 5.29 (+0.00 [0.00, 0.00]) | 4.07 (+0.00 [-0.01, 0.01]) / 3.75 (+0.00 [0.00, 0.00]) / 3.73 (+0.00 [0.00, 0.00]) | 5.37 (-0.21 [-0.36, -0.06]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.1 | 5.86 (-0.05 [-0.14, 0.02]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.29 (-0.02 [-0.09, 0.02]) / 5.23 (+0.00 [0.00, 0.00]) / 5.29 (+0.00 [0.00, 0.00]) | 4.07 (+0.00 [-0.01, 0.01]) / 3.75 (+0.00 [0.00, 0.00]) / 3.73 (+0.00 [0.00, 0.00]) | 5.49 (-0.09 [-0.18, 0.00]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.15 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 0.25 | 5.90 (+0.00 [0.00, 0.00]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.31 (-0.01 [-0.11, 0.09]) / 5.23 (+0.00 [0.00, 0.00]) / 5.29 (+0.00 [0.00, 0.00]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.75 (+0.00 [0.00, 0.00]) / 3.73 (+0.00 [0.00, 0.00]) | 5.59 (+0.01 [-0.04, 0.08]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |
| 0.35 | 5.90 (-0.00 [-0.01, 0.00]) / 5.45 (+0.00 [0.00, 0.00]) / 4.83 (+0.00 [0.00, 0.00]) | 6.34 (+0.02 [-0.10, 0.15]) / 5.23 (+0.00 [0.00, 0.00]) / 5.29 (+0.00 [0.00, 0.00]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.75 (+0.00 [0.00, 0.00]) / 3.73 (+0.00 [0.00, 0.00]) | 5.64 (+0.06 [-0.03, 0.18]) / 5.05 (+0.00 [0.00, 0.00]) / 4.93 (+0.00 [0.00, 0.00]) |

`robust_composition.BURDEN_COST`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 0.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.46 (+0.01 [-0.21, 0.25]) / 5.05 (+0.23 [-0.01, 0.54]) | 6.32 (+0.00 [0.00, 0.00]) / 5.47 (+0.24 [0.02, 0.43]) / 5.29 (+0.00 [-0.24, 0.23]) | 4.07 (-0.01 [-0.02, 0.00]) / 3.88 (+0.13 [0.02, 0.27]) / 3.85 (+0.12 [0.01, 0.25]) | 5.58 (+0.00 [0.00, 0.00]) / 5.27 (+0.22 [0.06, 0.38]) / 5.11 (+0.19 [-0.02, 0.38]) |
| 1 | 5.90 (+0.00 [0.00, 0.00]) / 5.55 (+0.10 [-0.14, 0.36]) / 5.43 (+0.61 [0.26, 0.97]) | 6.31 (-0.00 [-0.01, 0.00]) / 5.62 (+0.39 [0.04, 0.71]) / 5.52 (+0.23 [-0.12, 0.55]) | 4.07 (-0.01 [-0.02, 0.00]) / 4.00 (+0.25 [0.10, 0.42]) / 4.00 (+0.27 [0.10, 0.45]) | 5.59 (+0.01 [-0.03, 0.08]) / 5.20 (+0.15 [-0.09, 0.37]) / 5.14 (+0.21 [-0.05, 0.46]) |
| 2 | 5.90 (-0.00 [-0.01, 0.00]) / 5.79 (+0.34 [-0.02, 0.66]) / 5.74 (+0.92 [0.48, 1.31]) | 6.33 (+0.02 [-0.10, 0.15]) / 6.17 (+0.94 [0.49, 1.40]) / 6.16 (+0.87 [0.35, 1.38]) | 4.07 (-0.01 [-0.02, 0.00]) / 4.04 (+0.28 [0.08, 0.49]) / 4.04 (+0.31 [0.09, 0.52]) | 5.60 (+0.02 [-0.04, 0.13]) / 5.40 (+0.35 [0.03, 0.71]) / 5.42 (+0.50 [0.17, 0.88]) |

`action_loss.DEFAULT_INTERVENTION_MINUTES (repair minutes)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 1.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.90 (+0.06 [-0.15, 0.31]) / 5.90 (+0.06 [-0.15, 0.31]) | 6.33 (+0.00 [0.00, 0.00]) / 6.33 (+0.13 [0.00, 0.30]) / 6.33 (+0.13 [0.00, 0.30]) | 4.07 (+0.00 [0.00, 0.00]) / 4.07 (+0.00 [0.00, 0.00]) / 4.07 (+0.00 [0.00, 0.00]) | 5.63 (+0.03 [0.00, 0.09]) / 5.63 (+0.02 [-0.10, 0.16]) / 5.63 (+0.02 [-0.10, 0.16]) |
| 3 (current) | 5.90 / 5.84 / 5.84 | 6.33 / 6.20 / 6.20 | 4.07 / 4.07 / 4.07 | 5.60 / 5.61 / 5.61 |
| 6 | 5.90 (+0.00 [0.00, 0.01]) / 5.48 (-0.36 [-0.66, -0.08]) / 5.45 (-0.39 [-0.80, 0.01]) | 6.32 (-0.02 [-0.15, 0.10]) / 5.52 (-0.68 [-1.12, -0.30]) / 5.56 (-0.64 [-1.09, -0.25]) | 4.07 (+0.00 [0.00, 0.00]) / 3.94 (-0.12 [-0.28, 0.04]) / 3.94 (-0.12 [-0.28, 0.04]) | 5.57 (-0.03 [-0.14, 0.03]) / 5.21 (-0.40 [-0.75, -0.11]) / 5.16 (-0.45 [-0.78, -0.14]) |
| 10 | 5.90 (+0.00 [0.00, 0.01]) / 5.45 (-0.39 [-0.78, -0.03]) / 4.83 (-1.01 [-1.52, -0.54]) | 6.32 (-0.02 [-0.15, 0.10]) / 5.23 (-0.97 [-1.44, -0.48]) / 5.29 (-0.91 [-1.46, -0.39]) | 4.07 (+0.01 [0.00, 0.02]) / 3.75 (-0.31 [-0.52, -0.10]) / 3.73 (-0.34 [-0.56, -0.11]) | 5.58 (-0.02 [-0.13, 0.04]) / 5.05 (-0.56 [-0.94, -0.21]) / 4.93 (-0.69 [-1.09, -0.30]) |
| 20 | 5.90 (+0.00 [0.00, 0.01]) / 5.19 (-0.65 [-1.12, -0.24]) / 4.52 (-1.32 [-1.88, -0.78]) | 6.32 (-0.02 [-0.15, 0.10]) / 4.99 (-1.21 [-1.83, -0.73]) / 4.86 (-1.34 [-1.96, -0.80]) | 4.08 (+0.01 [0.00, 0.02]) / 3.68 (-0.38 [-0.63, -0.14]) / 3.67 (-0.40 [-0.72, -0.08]) | 5.58 (-0.02 [-0.13, 0.04]) / 5.04 (-0.57 [-0.99, -0.14]) / 4.91 (-0.70 [-1.25, -0.16]) |

`check minutes (probe burden; causal selector default 1.5)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 0.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.19 (-0.26 [-0.57, 0.00]) / 4.52 (-0.30 [-0.58, -0.00]) | 6.32 (+0.00 [0.00, 0.00]) / 4.99 (-0.24 [-0.62, 0.15]) / 4.86 (-0.43 [-0.82, -0.01]) | 4.08 (+0.00 [0.00, 0.01]) / 3.68 (-0.07 [-0.22, 0.06]) / 3.67 (-0.06 [-0.29, 0.16]) | 5.58 (+0.00 [0.00, 0.00]) / 5.04 (-0.01 [-0.22, 0.20]) / 4.91 (-0.02 [-0.31, 0.32]) |
| 1 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 1.5 | 5.90 (+0.00 [0.00, 0.00]) / 5.46 (+0.01 [-0.21, 0.25]) / 5.42 (+0.59 [0.28, 0.92]) | 6.32 (+0.00 [0.00, 0.00]) / 5.47 (+0.24 [0.02, 0.43]) / 5.39 (+0.10 [-0.20, 0.40]) | 4.07 (-0.01 [-0.02, 0.00]) / 3.88 (+0.13 [0.02, 0.27]) / 3.88 (+0.15 [0.02, 0.31]) | 5.58 (+0.00 [0.00, 0.00]) / 5.27 (+0.22 [0.06, 0.38]) / 5.22 (+0.29 [0.03, 0.52]) |
| 3 | 5.90 (-0.00 [-0.01, 0.00]) / 5.79 (+0.34 [-0.02, 0.66]) / 5.79 (+0.96 [0.52, 1.43]) | 6.33 (+0.02 [-0.10, 0.15]) / 6.17 (+0.94 [0.49, 1.40]) / 6.17 (+0.88 [0.38, 1.39]) | 4.07 (-0.01 [-0.02, 0.00]) / 4.04 (+0.28 [0.08, 0.49]) / 4.04 (+0.31 [0.09, 0.52]) | 5.60 (+0.02 [-0.04, 0.13]) / 5.40 (+0.35 [0.03, 0.71]) / 5.40 (+0.47 [0.10, 0.88]) |

`robust_composition.INSTRUMENT_PERTURBATION_CONCENTRATION`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 4 | 5.90 (-0.00 [-0.01, 0.00]) / 5.17 (-0.28 [-0.66, 0.05]) / 4.56 (-0.27 [-0.69, 0.17]) | 6.33 (+0.02 [-0.10, 0.15]) / 5.39 (+0.16 [-0.17, 0.51]) / 5.12 (-0.17 [-0.57, 0.25]) | 4.07 (-0.01 [-0.02, 0.00]) / 3.87 (+0.11 [0.01, 0.24]) / 3.69 (-0.04 [-0.21, 0.13]) | 5.63 (+0.05 [-0.03, 0.18]) / 5.28 (+0.23 [-0.01, 0.48]) / 4.94 (+0.01 [-0.38, 0.38]) |
| 10 | 5.90 (-0.00 [-0.01, 0.00]) / 5.45 (+0.00 [-0.29, 0.31]) / 4.73 (-0.10 [-0.40, 0.25]) | 6.33 (+0.02 [-0.10, 0.15]) / 5.12 (-0.11 [-0.33, 0.11]) / 4.92 (-0.37 [-0.65, -0.13]) | 4.07 (-0.01 [-0.02, 0.00]) / 3.80 (+0.04 [-0.08, 0.17]) / 3.79 (+0.06 [-0.06, 0.20]) | 5.61 (+0.03 [-0.07, 0.16]) / 5.38 (+0.33 [0.09, 0.59]) / 4.85 (-0.08 [-0.32, 0.17]) |
| 40 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 160 | 5.92 (+0.01 [-0.08, 0.12]) / 5.28 (-0.17 [-0.44, 0.10]) / 4.88 (+0.06 [-0.17, 0.29]) | 6.25 (-0.07 [-0.19, 0.02]) / 5.09 (-0.13 [-0.35, 0.08]) / 5.02 (-0.27 [-0.54, -0.03]) | 4.01 (-0.06 [-0.15, 0.00]) / 3.65 (-0.11 [-0.21, -0.01]) / 3.62 (-0.11 [-0.22, -0.01]) | 5.61 (+0.03 [-0.11, 0.17]) / 5.22 (+0.17 [-0.06, 0.41]) / 5.09 (+0.16 [-0.09, 0.38]) |

`robust_composition.ROBUST_DRAW_COUNT (simulation draws)`; mean minutes per episode at 0.9/10 (300 learners), paired Δ vs current [95% CI]:

| Value | `lca` evsi/evsi_lcb_only/evsi_lookahead | `cdm` evsi/evsi_lcb_only/evsi_lookahead | `nrm` evsi/evsi_lcb_only/evsi_lookahead | `lta` evsi/evsi_lcb_only/evsi_lookahead |
|---|---|---|---|---|
| 16 | 5.87 (-0.03 [-0.09, 0.00]) / 5.40 (-0.05 [-0.21, 0.08]) / 4.96 (+0.14 [-0.09, 0.39]) | 6.32 (+0.01 [-0.11, 0.11]) / 5.28 (+0.05 [-0.08, 0.19]) / 5.17 (-0.12 [-0.30, 0.05]) | 4.07 (+0.00 [-0.01, 0.01]) / 3.67 (-0.08 [-0.19, 0.00]) / 3.65 (-0.08 [-0.19, 0.00]) | 5.59 (+0.01 [-0.12, 0.15]) / 5.20 (+0.15 [-0.11, 0.41]) / 5.24 (+0.32 [0.09, 0.57]) |
| 32 (current) | 5.90 / 5.45 / 4.83 | 6.32 / 5.23 / 5.29 | 4.07 / 3.75 / 3.73 | 5.58 / 5.05 / 4.93 |
| 64 | 5.90 (+0.00 [0.00, 0.00]) / 5.43 (-0.02 [-0.17, 0.15]) / 4.79 (-0.04 [-0.21, 0.13]) | 6.32 (+0.00 [0.00, 0.01]) / 5.15 (-0.07 [-0.22, 0.06]) / 5.14 (-0.15 [-0.39, 0.05]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.76 (+0.00 [0.00, 0.01]) / 3.71 (-0.02 [-0.08, 0.01]) | 5.57 (-0.01 [-0.10, 0.07]) / 5.16 (+0.11 [-0.09, 0.34]) / 4.99 (+0.06 [-0.19, 0.29]) |
| 128 | 5.91 (+0.00 [0.00, 0.01]) / 5.54 (+0.09 [-0.10, 0.32]) / 4.90 (+0.07 [-0.13, 0.31]) | 6.34 (+0.02 [-0.09, 0.15]) / 5.17 (-0.05 [-0.17, 0.05]) / 5.18 (-0.11 [-0.27, 0.03]) | 4.07 (-0.00 [-0.01, 0.00]) / 3.78 (+0.03 [-0.01, 0.09]) / 3.76 (+0.03 [-0.01, 0.09]) | 5.66 (+0.08 [-0.04, 0.22]) / 5.24 (+0.19 [-0.03, 0.42]) / 5.03 (+0.11 [-0.14, 0.34]) |

## Appendix C. Claim statements

- `C1a`: the hand-set card implies consistency 0.8333; every family's fitted consistency is lower
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
- `S4:fitted/3`: fitted/3: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)
- `A1:fitted/3`: fitted/3: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:fitted/3`: fitted/3: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:fitted/3`: fitted/3: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S5:fitted/3`: fitted/3: the successor with the robust completion gate dropped and the lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes than the successor as built (voi_p_with_fallback - voi_successor < 0)
- `S6:fitted/3`: fitted/3: voi_p_with_fallback costs fewer minutes than the incumbent
- `A4:fitted/3`: fitted/3: inside the package, serving rank_feasible's top-ranked paying check instead of the successor's choice (the highest-EIG check when it pays) saves minutes (voi_p_top_value - voi_proposed < 0)
- `S1:fitted/30`: fitted/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:fitted/30`: fitted/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:fitted/30`: fitted/30: the proposed package costs fewer minutes than the incumbent
- `S4:fitted/30`: fitted/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)
- `A1:fitted/30`: fitted/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:fitted/30`: fitted/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:fitted/30`: fitted/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S5:fitted/30`: fitted/30: the successor with the robust completion gate dropped and the lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes than the successor as built (voi_p_with_fallback - voi_successor < 0)
- `S6:fitted/30`: fitted/30: voi_p_with_fallback costs fewer minutes than the incumbent
- `A4:fitted/30`: fitted/30: inside the package, serving rank_feasible's top-ranked paying check instead of the successor's choice (the highest-EIG check when it pays) saves minutes (voi_p_top_value - voi_proposed < 0)
- `S1:0.7/30`: 0.7/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.7/30`: 0.7/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.7/30`: 0.7/30: the proposed package costs fewer minutes than the incumbent
- `S4:0.7/30`: 0.7/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)
- `A1:0.7/30`: 0.7/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.7/30`: 0.7/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.7/30`: 0.7/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S5:0.7/30`: 0.7/30: the successor with the robust completion gate dropped and the lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes than the successor as built (voi_p_with_fallback - voi_successor < 0)
- `S6:0.7/30`: 0.7/30: voi_p_with_fallback costs fewer minutes than the incumbent
- `A4:0.7/30`: 0.7/30: inside the package, serving rank_feasible's top-ranked paying check instead of the successor's choice (the highest-EIG check when it pays) saves minutes (voi_p_top_value - voi_proposed < 0)
- `S1:0.9/10`: 0.9/10: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.9/10`: 0.9/10: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.9/10`: 0.9/10: the proposed package costs fewer minutes than the incumbent
- `S4:0.9/10`: 0.9/10: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)
- `A1:0.9/10`: 0.9/10: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.9/10`: 0.9/10: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.9/10`: 0.9/10: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S5:0.9/10`: 0.9/10: the successor with the robust completion gate dropped and the lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes than the successor as built (voi_p_with_fallback - voi_successor < 0)
- `S6:0.9/10`: 0.9/10: voi_p_with_fallback costs fewer minutes than the incumbent
- `A4:0.9/10`: 0.9/10: inside the package, serving rank_feasible's top-ranked paying check instead of the successor's choice (the highest-EIG check when it pays) saves minutes (voi_p_top_value - voi_proposed < 0)
- `S1:0.9/30`: 0.9/30: the successor as built (voi_successor) costs no more minutes than the incumbent (voi_successor - incumbent < 0)
- `S2:0.9/30`: 0.9/30: the proposed package (voi_proposed) costs fewer minutes than the successor as built (voi_proposed - voi_successor < 0)
- `S3:0.9/30`: 0.9/30: the proposed package costs fewer minutes than the incumbent
- `S4:0.9/30`: 0.9/30: keeping the stability stops (decision stable, action equivalent) on top of the lookahead saves minutes (voi_p_top_value - evsi_lookahead < 0)
- `A1:0.9/30`: 0.9/30: inside the package, today's robust completion gate costs minutes (voi_p_with_gate - voi_proposed > 0)
- `A2:0.9/30`: 0.9/30: inside the package, handing a flip abstention to the nat-scaled EIG costs minutes (voi_p_with_fallback - voi_proposed > 0)
- `A3:0.9/30`: 0.9/30: inside the package, the 2-3 check lookahead saves minutes (voi_proposed - voi_p_one_step < 0)
- `S5:0.9/30`: 0.9/30: the successor with the robust completion gate dropped and the lookahead added, its abstention handling kept (voi_p_with_fallback), costs fewer minutes than the successor as built (voi_p_with_fallback - voi_successor < 0)
- `S6:0.9/30`: 0.9/30: voi_p_with_fallback costs fewer minutes than the incumbent
- `A4:0.9/30`: 0.9/30: inside the package, serving rank_feasible's top-ranked paying check instead of the successor's choice (the highest-EIG check when it pays) saves minutes (voi_p_top_value - voi_proposed < 0)
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
- `R:voi_p_with_fallback-voi_successor@fitted/3`: fitted/3, system calibrated to another family: the gate dropped and the lookahead added beat the successor as built (voi_p_with_fallback-voi_successor, sign -1)
- `R:voi_p_with_fallback-voi_successor@0.9/10`: 0.9/10, system calibrated to another family: the gate dropped and the lookahead added beat the successor as built (voi_p_with_fallback-voi_successor, sign -1)
- `R:voi_p_with_fallback-voi_successor@0.9/30`: 0.9/30, system calibrated to another family: the gate dropped and the lookahead added beat the successor as built (voi_p_with_fallback-voi_successor, sign -1)
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
