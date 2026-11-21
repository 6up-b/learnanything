# ADM0 simulation report

Preregistration SHA-256: `dbc4373bfce05bab88b0cb6fbc6b011b1963c20201b161dc4b7ab65642605dcd`.

The protocol was written and hash-frozen on 2026-11-21 **before new simulation code, tests or runs**. The hash was recorded in this report before implementation. The sandbox cannot commit; the orchestrator commits the artifacts together. This establishes the session's order, not a separate earlier Git commit.

Completed registered-run JUnit timestamp: `2026-11-21T10:23:15.461351-05:00`. Base: `3f42da228a`. Source: `tests/test_ad_memory_simulation.py::test_registered_experiment` (`arc_close`). All 384 synthetic trajectories / 18,432 presentations were included. No owner outcomes, owner vaults, configuration files, network or model calls were used. **No claim of learner benefit, including at n=1.**

The simulation calls the real AD `Bank`, `View`, category kernel and FSRS review/recall functions. The sole production-file edit is a keyword-only residual-variance argument to `Bank.update`; omission executes the old residual calculation. No production caller supplies it. Nothing served, persisted, configured, tagged or migrated changes. Existing `ad_synthetic.py`, scenario seeds and fixtures remain untouched.

## Findings

1. **Decides something:** the joint same-item filter retains the analytically required ability variance floor; retaining cross-covariance is necessary for this interpretation.
2. **Decides something:** extra warmth coefficients preserve the prior eta mean and add predictive variance immediately; success probability and band probability consequently change.
3. **Decides something:** stable item and family coordinates, strict pre-serve features and once-per-surface gamma can be exercised through the existing numerical model without a served-model change.
4. **Cannot be decided by simulation:** none of the registered support/ladder comparisons satisfies all selection conditions below; no production rho, LO value or warmth ladder is selected.
5. **Cannot be decided by simulation:** per-learner family/item decomposition is weakly identified; repeated success alone does not identify transferable ability. Recovery and contraction are reported, not inferred from loss.
6. **Cannot be decided by simulation:** prior widths are not established population values. Quarter/four-times variance and one-SD mean perturbations remain alternatives, even where one has lower synthetic loss.
7. **Cannot be decided by simulation:** the planted effective-stability multiplier does not identify RE8's latent weights or the LP width support; no RE8 fitter is implemented here.
8. **Decides something:** numerical cold replay, cached-input construction, candidate-grid work and synthetic Next have measured costs and explicit workloads; no covariance approximation is proposed.
9. **Cannot be decided by simulation:** these numerical timings do not establish production Next latency, database replay cost, storage growth or owner-data prevalence.
10. **Cannot be decided by simulation:** synthetic prediction/recovery says nothing by itself about learner benefit or the effects of a changed serving policy.

## Design and limits

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Six worlds and all 48 scheduled events per learner. At synthetic origin 2026-01-01T00:00:00Z, block b starts at day 36b; offsets are 0, 1/24, 1/4, 1, 3, 7, 30, 31, 32, 33, 34, 35 days. Strict review-time < serve-time; labels close inclusively at 2026-06-01T00:00:00Z under `adm0_synthetic_categories_v1`. Every presentation is issued, answered and resolved; missing, unbound, censored, held, primed and pre-exposed counts are all zero. This experiment does not validate their production eligibility.

Each trajectory has 20 items, 12 surface groups, 28 same-item repeats (including four singleton repeats), eight unseen siblings, four singleton first encounters, four initial anchors and four novel families after drilling. Assigned/natural-labelled delays each cover 24 events. The latter are scripted, not observational evidence. Views share truth and outcome uniforms. Subject filtering uses three distinct inherited split points; coupling/implication duplicates in the 36-point grid are numerically equivalent in this one-cell design (tested against the full grid). LO filtering has fixed rho candidates 0/.5/1, never a learned rho mixture.

True effects are stable while the filter applies the spec's inherited drift. This deliberate mismatch can make intervals conservative and prevent contraction. No random-walk truth recovery is claimed. Memory uses past FSRS reviews; the slow-retention world alone reads planted S_eff=S*exp(.5). The truth uses its own pre-memory eta and each candidate freezes its own mean. The positive-easiness sign convention follows ADM §4.4; §4.2's contrary -1 wording remains a spec-owner correction.

Rho is the initial variance split. Even at rho=0 or 1, an initially zero-variance effect receives the specified later drift; the endpoints do not impose a permanent zero effect.

Scores are binary unassisted-success log loss and Brier; calibration is ten-bin absolute calibration error (ECE) and signed mean p-y. Coverage is a nominal 95% moment interval for planted latent eta, including unseen residuals, using **pre-update mixture weights**. It is not coverage of binary labels and is not an exact mixture quantile. Paired intervals use eight seed-level means with t(7), not attempts as independent samples. FSRS predicts recall (rating != AGAIN), and mastery predicts rubric correctness; their target mismatch to AD's category-2 success is retained and disclosed.

## Execution ledger

Tests were written first and initially failed collection because the new module did not exist. The fast test's initial per-filter comparison was corrected to compare matching grids. The first arc-close attempt failed during first-world score aggregation (NumPy boolean negation); labels were cast to floats, with a regression test. A subsequent complete run was superseded after a stronger novel-only compatibility test found that candidate drift preceded prediction instead of following View.observe's boundary. The candidate now predicts first, then applies cell/effect drift, measurement and learning. The final complete registered rerun supplies all tables; earlier numerical results are discarded. This necessary correctness rerun departs from the requested single successful execution, not from the statistical protocol. No seed, world, prior, selection criterion or frozen-protocol byte changed. JUnit's explicit `--junitxml` destination records the aggregate payload as `adm0_results`; this replaces the protocol's proposed environment-variable output mechanism because the supplied wrapper clears the environment. This is an output-only deviation.

## Reading the numerical results

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). In the balanced world, subject repeat loss is 0.4887 for the predecessor and 0.4091 for the R3/H3 reference (1,792 repeat outcomes). This descriptive gain does not select rho or warmth. R3's seed-mean entropy fractions span 0.9964–0.9996 across worlds, close to uniform. The rho point that generated a world gets slightly more than uniform mass, but that is weak evidence, not reliable identification.

After 48 events, the balanced reference's first family/item variances are 1.298 and 1.373 times their original priors (64 estimates each): neither contracts. The memory-weight ratios are 0.509 and 0.343, showing some information about those terms. In slow_retention, ability RMSE is 1.859 and interval coverage 0.703; the model can forecast practised answers while misattributing their explanation.

Across the fourteen one-factor prior perturbations, balanced-world overall subject loss ranges 0.4480–0.4602 (3,072 outcomes per arm). These are sensitivity results, not a search for a replacement prior. The full tables retain each perturbation and every world, including losses and coverage failures. Added warmth scales have strongly overlapping temporal signals here; small prediction differences and curve-recovery failures leave ladder selection unresolved.

## Exact joint same-item variance floor

Deterministic, no random seed; 1 filter per row, 512 alternating category-0/2 observations at fixed time; no learning transition, memory or warmth. v_s=3, v_e as listed. Floor=3*v_e/(3+v_e).

| v_e | Floor | Minimum / final ability variance | Ability/effect covariance | Sibling variance | Novel variance |
| --- | --- | --- | --- | --- | --- |
| 0.2500 | 0.2308 | 0.2393 | -0.2301 | 0.2544 | 0.4893 |
| 1.0000 | 0.7500 | 0.7556 | -0.7481 | 0.9451 | 1.7556 |
| 4.0000 | 1.7143 | 1.7161 | -1.7118 | 3.4337 | 5.7161 |

The observed sum can become precise while ability and stable effects remain negatively correlated. This is exact within the existing Gaussian projection, not an exact non-Gaussian posterior. The floor is a fixed-time, fixed-feature result; gamma uncertainty and drift in the main run add other uncertainty.

A structural contrast (no sampled outcomes): ability=+1 with effect=0 and ability=-1 with effect=+2 give identical drilled-item eta=1 and success=.98*sigmoid(1). On a novel family at zero mean effect they give eta=+1 and -1. Same-item likelihoods cannot distinguish the two; novel families expose a different projection, but **one novel binary answer cannot identify the decomposition**. These +/-1 and +2 values are an algebraic illustration, not added fitted priors or an unregistered recovery run.

## Warmth prior predictive check

Deterministic, no random seed; 1 cold LO filter per row, 0 observations, one fresh item/family at each stated exposure gap. Variance excludes the unchanged unit residual; added variance=sum(.25*exp(-2*hours/h)) over extra scales.

| Ladder | Hours | Eta mean (old=new) | Old variance | Added variance | New variance | Old/new success | Old/new band |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 0.0 | 1.0000 | 3.2500 | 0.0000 | 3.2500 | 0.6323 / 0.6323 | 0.1434 / 0.1434 |
| H1 | 0.375 | 0.9394 | 3.2206 | 0.0000 | 3.2206 | 0.6243 / 0.6243 | 0.1428 / 0.1428 |
| H1 | 1.5 | 0.7788 | 3.1516 | 0.0000 | 3.1516 | 0.6026 / 0.6026 | 0.1401 / 0.1401 |
| H1 | 6.0 | 0.3679 | 3.0338 | 0.0000 | 3.0338 | 0.5443 / 0.5443 | 0.1268 / 0.1268 |
| H1 | 24.0 | 0.0183 | 3.0001 | 0.0000 | 3.0001 | 0.4927 / 0.4927 | 0.1103 / 0.1103 |
| H1 | 96.0 | 1.125e-07 | 3.0000 | 0.0000 | 3.0000 | 0.4900 / 0.4900 | 0.1094 / 0.1094 |
| H3 | 0.0 | 1.0000 | 3.2500 | 0.5000 | 3.7500 | 0.6323 / 0.6276 | 0.1434 / 0.1341 |
| H3 | 0.375 | 0.9394 | 3.2206 | 0.3939 | 3.6146 | 0.6243 / 0.6208 | 0.1428 / 0.1354 |
| H3 | 1.5 | 0.7788 | 3.1516 | 0.2545 | 3.4061 | 0.6026 / 0.6006 | 0.1401 / 0.1355 |
| H3 | 6.0 | 0.3679 | 3.0338 | 0.1517 | 3.1856 | 0.5443 / 0.5437 | 0.1268 / 0.1249 |
| H3 | 24.0 | 0.0183 | 3.0001 | 0.0338 | 3.0339 | 0.4927 / 0.4927 | 0.1103 / 0.1101 |
| H3 | 96.0 | 1.125e-07 | 3.0000 | 8.387e-05 | 3.0001 | 0.4900 / 0.4900 | 0.1094 / 0.1094 |
| H5 | 0.0 | 1.0000 | 3.2500 | 1.0000 | 4.2500 | 0.6323 / 0.6234 | 0.1434 / 0.1264 |
| H5 | 0.375 | 0.9394 | 3.2206 | 0.6758 | 3.8965 | 0.6243 / 0.6184 | 0.1428 / 0.1308 |
| H5 | 1.5 | 0.7788 | 3.1516 | 0.4969 | 3.6485 | 0.6026 / 0.5988 | 0.1401 / 0.1315 |
| H5 | 6.0 | 0.3679 | 3.0338 | 0.3723 | 3.4062 | 0.5443 / 0.5428 | 0.1268 / 0.1222 |
| H5 | 24.0 | 0.0183 | 3.0001 | 0.1855 | 3.1856 | 0.4927 / 0.4927 | 0.1103 / 0.1092 |
| H5 | 96.0 | 1.125e-07 | 3.0000 | 0.0339 | 3.0339 | 0.4900 / 0.4900 | 0.1094 / 0.1092 |

## All candidates and prior sensitivity — subject

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each row: 3,072 predictions (48 per learner), final ability recovery over 64 learners. H ladders and R supports follow the frozen register; sensitivity rows change one prior at a time around R3/H3 (LO: fixed rho=.5/H3). No result chooses a constant.

| World | Arm | N | Loss | Brier | ECE | Bias | Eta coverage | Ability RMSE | Ability coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | R1-H1 | 3072 | 0.4516 | 0.1441 | 0.0185 | -0.0065 | 0.9854 | 1.0757 | 0.9688 |
| balanced | R1-H3 | 3072 | 0.4516 | 0.1441 | 0.0192 | -0.0065 | 0.9857 | 1.0812 | 0.9688 |
| balanced | R1-H5 | 3072 | 0.4516 | 0.1441 | 0.0176 | -0.0062 | 0.9863 | 1.0995 | 1.0000 |
| balanced | R3-H1 | 3072 | 0.4518 | 0.1442 | 0.0191 | -0.0065 | 0.9850 | 1.0758 | 0.9688 |
| balanced | R3-H3 | 3072 | 0.4518 | 0.1442 | 0.0193 | -0.0065 | 0.9863 | 1.0813 | 0.9688 |
| balanced | R3-H5 | 3072 | 0.4518 | 0.1442 | 0.0185 | -0.0063 | 0.9863 | 1.0997 | 1.0000 |
| balanced | R5-H1 | 3072 | 0.4518 | 0.1442 | 0.0186 | -0.0065 | 0.9857 | 1.0758 | 0.9688 |
| balanced | R5-H3 | 3072 | 0.4517 | 0.1442 | 0.0195 | -0.0065 | 0.9867 | 1.0813 | 0.9688 |
| balanced | R5-H5 | 3072 | 0.4517 | 0.1442 | 0.0180 | -0.0062 | 0.9863 | 1.0997 | 1.0000 |
| balanced | effect_scalex0.25 | 3072 | 0.4526 | 0.1444 | 0.0187 | -0.0030 | 0.9600 | 1.0833 | 0.9531 |
| balanced | effect_scalex4 | 3072 | 0.4544 | 0.1452 | 0.0218 | -0.0156 | 0.9987 | 1.1847 | 0.9531 |
| balanced | extra_mean+0.5 | 3072 | 0.4506 | 0.1437 | 0.0146 | -0.0037 | 0.9867 | 1.0894 | 0.9531 |
| balanced | extra_mean-0.5 | 3072 | 0.4537 | 0.1449 | 0.0176 | -0.0094 | 0.9840 | 1.0891 | 0.9531 |
| balanced | extra_varx0.25 | 3072 | 0.4518 | 0.1442 | 0.0192 | -0.0065 | 0.9854 | 1.0772 | 0.9688 |
| balanced | extra_varx4 | 3072 | 0.4518 | 0.1442 | 0.0172 | -0.0065 | 0.9863 | 1.0984 | 0.9844 |
| balanced | family_mean+0.5 | 3072 | 0.4569 | 0.1453 | 0.0269 | 0.0027 | 0.9805 | 1.0877 | 0.9844 |
| balanced | family_mean-0.5 | 3072 | 0.4591 | 0.1474 | 0.0246 | -0.0174 | 0.9818 | 1.0933 | 0.9531 |
| balanced | family_varx0.25 | 3072 | 0.4480 | 0.1426 | 0.0138 | -0.0076 | 0.9867 | 1.0824 | 1.0000 |
| balanced | family_varx4 | 3072 | 0.4602 | 0.1472 | 0.0320 | -0.0055 | 0.9837 | 1.0920 | 0.9531 |
| balanced | item_mean+0.5 | 3072 | 0.4547 | 0.1447 | 0.0270 | -0.0043 | 0.9840 | 1.1139 | 0.9531 |
| balanced | item_mean-0.5 | 3072 | 0.4587 | 0.1471 | 0.0224 | -0.0099 | 0.9837 | 1.0755 | 0.9688 |
| balanced | item_varx0.25 | 3072 | 0.4490 | 0.1431 | 0.0199 | -0.0062 | 0.9863 | 1.0727 | 0.9844 |
| balanced | item_varx4 | 3072 | 0.4585 | 0.1464 | 0.0275 | -0.0072 | 0.9834 | 1.1041 | 0.9688 |
| balanced | predecessor | 3072 | 0.5043 | 0.1665 | 0.0907 | -0.0907 | 0.9694 | 1.2319 | 0.9844 |
| family_memory | R1-H1 | 3072 | 0.3607 | 0.1078 | 0.0283 | -0.0217 | 0.9639 | 1.4727 | 0.8594 |
| family_memory | R1-H3 | 3072 | 0.3607 | 0.1077 | 0.0279 | -0.0217 | 0.9642 | 1.4782 | 0.8750 |
| family_memory | R1-H5 | 3072 | 0.3606 | 0.1077 | 0.0271 | -0.0214 | 0.9648 | 1.4971 | 0.8750 |
| family_memory | R3-H1 | 3072 | 0.3607 | 0.1078 | 0.0284 | -0.0217 | 0.9639 | 1.4730 | 0.8594 |
| family_memory | R3-H3 | 3072 | 0.3607 | 0.1078 | 0.0279 | -0.0218 | 0.9642 | 1.4785 | 0.8750 |
| family_memory | R3-H5 | 3072 | 0.3606 | 0.1077 | 0.0271 | -0.0215 | 0.9648 | 1.4974 | 0.8750 |
| family_memory | R5-H1 | 3072 | 0.3607 | 0.1078 | 0.0283 | -0.0217 | 0.9639 | 1.4729 | 0.8594 |
| family_memory | R5-H3 | 3072 | 0.3607 | 0.1078 | 0.0280 | -0.0217 | 0.9642 | 1.4784 | 0.8750 |
| family_memory | R5-H5 | 3072 | 0.3606 | 0.1077 | 0.0272 | -0.0215 | 0.9648 | 1.4973 | 0.8750 |
| family_memory | effect_scalex0.25 | 3072 | 0.3604 | 0.1077 | 0.0260 | -0.0162 | 0.9303 | 1.5203 | 0.8438 |
| family_memory | effect_scalex4 | 3072 | 0.3660 | 0.1096 | 0.0397 | -0.0383 | 0.9912 | 1.5183 | 0.9062 |
| family_memory | extra_mean+0.5 | 3072 | 0.3605 | 0.1076 | 0.0243 | -0.0183 | 0.9635 | 1.4805 | 0.8750 |
| family_memory | extra_mean-0.5 | 3072 | 0.3611 | 0.1081 | 0.0283 | -0.0252 | 0.9668 | 1.4904 | 0.8906 |
| family_memory | extra_varx0.25 | 3072 | 0.3607 | 0.1078 | 0.0283 | -0.0217 | 0.9639 | 1.4744 | 0.8594 |
| family_memory | extra_varx4 | 3072 | 0.3607 | 0.1077 | 0.0281 | -0.0218 | 0.9652 | 1.4942 | 0.8906 |
| family_memory | family_mean+0.5 | 3072 | 0.3459 | 0.1030 | 0.0160 | -0.0117 | 0.9740 | 1.4504 | 0.8750 |
| family_memory | family_mean-0.5 | 3072 | 0.3885 | 0.1180 | 0.0460 | -0.0345 | 0.9033 | 1.5336 | 0.8594 |
| family_memory | family_varx0.25 | 3072 | 0.3703 | 0.1111 | 0.0277 | -0.0240 | 0.9408 | 1.5308 | 0.8594 |
| family_memory | family_varx4 | 3072 | 0.3554 | 0.1061 | 0.0196 | -0.0192 | 0.9701 | 1.4349 | 0.8750 |
| family_memory | item_mean+0.5 | 3072 | 0.3536 | 0.1058 | 0.0196 | -0.0179 | 0.9707 | 1.4658 | 0.8750 |
| family_memory | item_mean-0.5 | 3072 | 0.3763 | 0.1132 | 0.0377 | -0.0273 | 0.9072 | 1.5200 | 0.8594 |
| family_memory | item_varx0.25 | 3072 | 0.3636 | 0.1085 | 0.0294 | -0.0223 | 0.9447 | 1.5041 | 0.8438 |
| family_memory | item_varx4 | 3072 | 0.3595 | 0.1079 | 0.0238 | -0.0214 | 0.9704 | 1.4431 | 0.8906 |
| family_memory | predecessor | 3072 | 0.5504 | 0.1858 | 0.1905 | -0.1869 | 0.6846 | 1.2267 | 0.9688 |
| independent | R1-H1 | 3072 | 0.4489 | 0.1431 | 0.0142 | -0.0075 | 0.9792 | 1.0989 | 0.9688 |
| independent | R1-H3 | 3072 | 0.4489 | 0.1431 | 0.0137 | -0.0076 | 0.9792 | 1.1029 | 0.9688 |
| independent | R1-H5 | 3072 | 0.4489 | 0.1431 | 0.0144 | -0.0073 | 0.9795 | 1.1132 | 0.9688 |
| independent | R3-H1 | 3072 | 0.4490 | 0.1431 | 0.0143 | -0.0075 | 0.9792 | 1.0999 | 0.9688 |
| independent | R3-H3 | 3072 | 0.4491 | 0.1431 | 0.0137 | -0.0076 | 0.9792 | 1.1040 | 0.9688 |
| independent | R3-H5 | 3072 | 0.4490 | 0.1431 | 0.0142 | -0.0073 | 0.9795 | 1.1144 | 0.9688 |
| independent | R5-H1 | 3072 | 0.4490 | 0.1431 | 0.0142 | -0.0075 | 0.9795 | 1.0997 | 0.9688 |
| independent | R5-H3 | 3072 | 0.4490 | 0.1431 | 0.0137 | -0.0076 | 0.9792 | 1.1037 | 0.9688 |
| independent | R5-H5 | 3072 | 0.4490 | 0.1431 | 0.0142 | -0.0073 | 0.9795 | 1.1141 | 0.9688 |
| independent | effect_scalex0.25 | 3072 | 0.4499 | 0.1434 | 0.0169 | -0.0043 | 0.9495 | 1.1161 | 0.9688 |
| independent | effect_scalex4 | 3072 | 0.4517 | 0.1443 | 0.0188 | -0.0161 | 0.9974 | 1.1677 | 0.9688 |
| independent | extra_mean+0.5 | 3072 | 0.4477 | 0.1426 | 0.0119 | -0.0046 | 0.9801 | 1.1089 | 0.9688 |
| independent | extra_mean-0.5 | 3072 | 0.4511 | 0.1439 | 0.0168 | -0.0105 | 0.9795 | 1.1156 | 0.9531 |
| independent | extra_varx0.25 | 3072 | 0.4490 | 0.1431 | 0.0143 | -0.0075 | 0.9792 | 1.1010 | 0.9688 |
| independent | extra_varx4 | 3072 | 0.4492 | 0.1432 | 0.0148 | -0.0076 | 0.9798 | 1.1165 | 0.9688 |
| independent | family_mean+0.5 | 3072 | 0.4543 | 0.1442 | 0.0241 | 0.0021 | 0.9736 | 1.1131 | 0.9688 |
| independent | family_mean-0.5 | 3072 | 0.4565 | 0.1465 | 0.0243 | -0.0188 | 0.9756 | 1.1172 | 0.9531 |
| independent | family_varx0.25 | 3072 | 0.4447 | 0.1415 | 0.0139 | -0.0087 | 0.9785 | 1.0938 | 0.9688 |
| independent | family_varx4 | 3072 | 0.4583 | 0.1462 | 0.0260 | -0.0063 | 0.9769 | 1.1236 | 0.9531 |
| independent | item_mean+0.5 | 3072 | 0.4526 | 0.1437 | 0.0192 | -0.0054 | 0.9756 | 1.1414 | 0.9531 |
| independent | item_mean-0.5 | 3072 | 0.4554 | 0.1460 | 0.0198 | -0.0109 | 0.9762 | 1.0934 | 0.9688 |
| independent | item_varx0.25 | 3072 | 0.4460 | 0.1421 | 0.0177 | -0.0075 | 0.9808 | 1.0977 | 0.9688 |
| independent | item_varx4 | 3072 | 0.4559 | 0.1453 | 0.0227 | -0.0083 | 0.9772 | 1.1259 | 0.9531 |
| independent | predecessor | 3072 | 0.5021 | 0.1654 | 0.0935 | -0.0935 | 0.9684 | 1.2532 | 0.9531 |
| no_memory | R1-H1 | 3072 | 0.4889 | 0.1601 | 0.0310 | 0.0001 | 0.9658 | 0.9860 | 1.0000 |
| no_memory | R1-H3 | 3072 | 0.4889 | 0.1601 | 0.0304 | 0.0002 | 0.9658 | 0.9880 | 1.0000 |
| no_memory | R1-H5 | 3072 | 0.4890 | 0.1602 | 0.0300 | 0.0003 | 0.9658 | 1.0007 | 1.0000 |
| no_memory | R3-H1 | 3072 | 0.4891 | 0.1602 | 0.0312 | 0.0001 | 0.9655 | 0.9853 | 1.0000 |
| no_memory | R3-H3 | 3072 | 0.4891 | 0.1602 | 0.0301 | 0.0002 | 0.9658 | 0.9873 | 1.0000 |
| no_memory | R3-H5 | 3072 | 0.4892 | 0.1602 | 0.0298 | 0.0003 | 0.9658 | 1.0000 | 1.0000 |
| no_memory | R5-H1 | 3072 | 0.4891 | 0.1601 | 0.0317 | 0.0001 | 0.9655 | 0.9855 | 1.0000 |
| no_memory | R5-H3 | 3072 | 0.4891 | 0.1602 | 0.0304 | 0.0002 | 0.9658 | 0.9875 | 1.0000 |
| no_memory | R5-H5 | 3072 | 0.4892 | 0.1602 | 0.0296 | 0.0003 | 0.9658 | 1.0002 | 1.0000 |
| no_memory | effect_scalex0.25 | 3072 | 0.4918 | 0.1613 | 0.0277 | 0.0009 | 0.9167 | 1.0134 | 1.0000 |
| no_memory | effect_scalex4 | 3072 | 0.4934 | 0.1612 | 0.0216 | -0.0039 | 0.9902 | 1.0358 | 0.9844 |
| no_memory | extra_mean+0.5 | 3072 | 0.4900 | 0.1604 | 0.0319 | 0.0020 | 0.9691 | 1.0047 | 1.0000 |
| no_memory | extra_mean-0.5 | 3072 | 0.4901 | 0.1605 | 0.0254 | -0.0017 | 0.9629 | 0.9842 | 0.9844 |
| no_memory | extra_varx0.25 | 3072 | 0.4891 | 0.1602 | 0.0305 | 0.0001 | 0.9658 | 0.9858 | 1.0000 |
| no_memory | extra_varx4 | 3072 | 0.4893 | 0.1603 | 0.0285 | 0.0004 | 0.9668 | 0.9956 | 1.0000 |
| no_memory | family_mean+0.5 | 3072 | 0.4967 | 0.1622 | 0.0350 | 0.0084 | 0.9600 | 1.0040 | 1.0000 |
| no_memory | family_mean-0.5 | 3072 | 0.4932 | 0.1621 | 0.0347 | -0.0086 | 0.9632 | 0.9837 | 0.9844 |
| no_memory | family_varx0.25 | 3072 | 0.4865 | 0.1592 | 0.0335 | 0.0004 | 0.9665 | 0.9870 | 1.0000 |
| no_memory | family_varx4 | 3072 | 0.4958 | 0.1625 | 0.0275 | -0.0002 | 0.9648 | 0.9988 | 1.0000 |
| no_memory | item_mean+0.5 | 3072 | 0.5044 | 0.1651 | 0.0464 | 0.0021 | 0.9538 | 1.0338 | 1.0000 |
| no_memory | item_mean-0.5 | 3072 | 0.4840 | 0.1583 | 0.0181 | -0.0019 | 0.9665 | 0.9622 | 1.0000 |
| no_memory | item_varx0.25 | 3072 | 0.4917 | 0.1611 | 0.0289 | -0.0002 | 0.9635 | 0.9839 | 1.0000 |
| no_memory | item_varx4 | 3072 | 0.4915 | 0.1609 | 0.0245 | 0.0005 | 0.9658 | 1.0097 | 1.0000 |
| no_memory | predecessor | 3072 | 0.5142 | 0.1707 | 0.0254 | -0.0136 | 0.9619 | 1.2319 | 0.9844 |
| shared | R1-H1 | 3072 | 0.4484 | 0.1434 | 0.0155 | -0.0082 | 0.9831 | 1.1826 | 0.8906 |
| shared | R1-H3 | 3072 | 0.4483 | 0.1434 | 0.0158 | -0.0082 | 0.9834 | 1.1865 | 0.8906 |
| shared | R1-H5 | 3072 | 0.4481 | 0.1433 | 0.0161 | -0.0079 | 0.9834 | 1.2019 | 0.9219 |
| shared | R3-H1 | 3072 | 0.4485 | 0.1434 | 0.0149 | -0.0082 | 0.9827 | 1.1836 | 0.8906 |
| shared | R3-H3 | 3072 | 0.4485 | 0.1434 | 0.0158 | -0.0082 | 0.9831 | 1.1874 | 0.8906 |
| shared | R3-H5 | 3072 | 0.4482 | 0.1433 | 0.0157 | -0.0079 | 0.9837 | 1.2029 | 0.9219 |
| shared | R5-H1 | 3072 | 0.4485 | 0.1434 | 0.0144 | -0.0082 | 0.9827 | 1.1834 | 0.8906 |
| shared | R5-H3 | 3072 | 0.4484 | 0.1434 | 0.0158 | -0.0082 | 0.9831 | 1.1872 | 0.8906 |
| shared | R5-H5 | 3072 | 0.4482 | 0.1433 | 0.0157 | -0.0079 | 0.9834 | 1.2026 | 0.9219 |
| shared | effect_scalex0.25 | 3072 | 0.4501 | 0.1441 | 0.0236 | -0.0054 | 0.9577 | 1.1874 | 0.9062 |
| shared | effect_scalex4 | 3072 | 0.4504 | 0.1439 | 0.0178 | -0.0159 | 0.9990 | 1.3000 | 0.9375 |
| shared | extra_mean+0.5 | 3072 | 0.4467 | 0.1428 | 0.0137 | -0.0053 | 0.9844 | 1.1879 | 0.9219 |
| shared | extra_mean-0.5 | 3072 | 0.4508 | 0.1443 | 0.0172 | -0.0111 | 0.9811 | 1.2017 | 0.8750 |
| shared | extra_varx0.25 | 3072 | 0.4485 | 0.1434 | 0.0153 | -0.0082 | 0.9831 | 1.1845 | 0.8906 |
| shared | extra_varx4 | 3072 | 0.4483 | 0.1434 | 0.0158 | -0.0082 | 0.9834 | 1.2001 | 0.9219 |
| shared | family_mean+0.5 | 3072 | 0.4544 | 0.1445 | 0.0200 | 0.0010 | 0.9788 | 1.1921 | 0.9219 |
| shared | family_mean-0.5 | 3072 | 0.4549 | 0.1467 | 0.0250 | -0.0190 | 0.9782 | 1.2008 | 0.9062 |
| shared | family_varx0.25 | 3072 | 0.4445 | 0.1419 | 0.0184 | -0.0091 | 0.9824 | 1.1836 | 0.8906 |
| shared | family_varx4 | 3072 | 0.4568 | 0.1462 | 0.0244 | -0.0073 | 0.9808 | 1.2016 | 0.8906 |
| shared | item_mean+0.5 | 3072 | 0.4518 | 0.1440 | 0.0217 | -0.0059 | 0.9801 | 1.2314 | 0.8906 |
| shared | item_mean-0.5 | 3072 | 0.4553 | 0.1464 | 0.0162 | -0.0116 | 0.9801 | 1.1745 | 0.8906 |
| shared | item_varx0.25 | 3072 | 0.4460 | 0.1426 | 0.0099 | -0.0081 | 0.9834 | 1.1733 | 0.9062 |
| shared | item_varx4 | 3072 | 0.4551 | 0.1456 | 0.0244 | -0.0087 | 0.9818 | 1.2139 | 0.8906 |
| shared | predecessor | 3072 | 0.5033 | 0.1670 | 0.0935 | -0.0935 | 0.9736 | 1.2630 | 0.9844 |
| slow_retention | R1-H1 | 3072 | 0.3208 | 0.0922 | 0.0386 | -0.0358 | 0.9421 | 1.8563 | 0.6875 |
| slow_retention | R1-H3 | 3072 | 0.3208 | 0.0922 | 0.0383 | -0.0359 | 0.9427 | 1.8593 | 0.7031 |
| slow_retention | R1-H5 | 3072 | 0.3207 | 0.0922 | 0.0379 | -0.0355 | 0.9440 | 1.8656 | 0.7500 |
| slow_retention | R3-H1 | 3072 | 0.3208 | 0.0922 | 0.0379 | -0.0358 | 0.9421 | 1.8558 | 0.6875 |
| slow_retention | R3-H3 | 3072 | 0.3208 | 0.0923 | 0.0384 | -0.0359 | 0.9430 | 1.8588 | 0.7031 |
| slow_retention | R3-H5 | 3072 | 0.3207 | 0.0922 | 0.0369 | -0.0355 | 0.9443 | 1.8651 | 0.7500 |
| slow_retention | R5-H1 | 3072 | 0.3208 | 0.0922 | 0.0381 | -0.0358 | 0.9421 | 1.8560 | 0.6875 |
| slow_retention | R5-H3 | 3072 | 0.3208 | 0.0922 | 0.0384 | -0.0359 | 0.9430 | 1.8589 | 0.7031 |
| slow_retention | R5-H5 | 3072 | 0.3207 | 0.0922 | 0.0372 | -0.0355 | 0.9443 | 1.8652 | 0.7500 |
| slow_retention | effect_scalex0.25 | 3072 | 0.3201 | 0.0920 | 0.0324 | -0.0303 | 0.8988 | 1.8189 | 0.6875 |
| slow_retention | effect_scalex4 | 3072 | 0.3262 | 0.0940 | 0.0531 | -0.0524 | 0.9844 | 2.0286 | 0.7812 |
| slow_retention | extra_mean+0.5 | 3072 | 0.3198 | 0.0918 | 0.0354 | -0.0324 | 0.9427 | 1.8002 | 0.7344 |
| slow_retention | extra_mean-0.5 | 3072 | 0.3220 | 0.0928 | 0.0397 | -0.0394 | 0.9450 | 1.9258 | 0.7031 |
| slow_retention | extra_varx0.25 | 3072 | 0.3208 | 0.0922 | 0.0378 | -0.0358 | 0.9421 | 1.8566 | 0.6875 |
| slow_retention | extra_varx4 | 3072 | 0.3208 | 0.0923 | 0.0382 | -0.0359 | 0.9463 | 1.8669 | 0.7188 |
| slow_retention | family_mean+0.5 | 3072 | 0.3078 | 0.0882 | 0.0307 | -0.0274 | 0.9691 | 1.8132 | 0.7500 |
| slow_retention | family_mean-0.5 | 3072 | 0.3459 | 0.1016 | 0.0479 | -0.0474 | 0.8646 | 1.9421 | 0.6719 |
| slow_retention | family_varx0.25 | 3072 | 0.3286 | 0.0949 | 0.0372 | -0.0372 | 0.9040 | 1.9213 | 0.6562 |
| slow_retention | family_varx4 | 3072 | 0.3175 | 0.0914 | 0.0358 | -0.0349 | 0.9645 | 1.8335 | 0.7344 |
| slow_retention | item_mean+0.5 | 3072 | 0.3159 | 0.0908 | 0.0352 | -0.0340 | 0.9681 | 1.8950 | 0.7188 |
| slow_retention | item_mean-0.5 | 3072 | 0.3336 | 0.0970 | 0.0431 | -0.0399 | 0.8584 | 1.8749 | 0.7188 |
| slow_retention | item_varx0.25 | 3072 | 0.3224 | 0.0927 | 0.0365 | -0.0361 | 0.9079 | 1.8742 | 0.6875 |
| slow_retention | item_varx4 | 3072 | 0.3211 | 0.0928 | 0.0371 | -0.0362 | 0.9639 | 1.8511 | 0.7344 |
| slow_retention | predecessor | 3072 | 0.4883 | 0.1605 | 0.1843 | -0.1832 | 0.6562 | 1.3600 | 0.9844 |

## All candidates and prior sensitivity — lo

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each row: 3,072 predictions (48 per learner), final ability recovery over 64 learners. H ladders and R supports follow the frozen register; sensitivity rows change one prior at a time around R3/H3 (LO: fixed rho=.5/H3). No result chooses a constant.

| World | Arm | N | Loss | Brier | ECE | Bias | Eta coverage | Ability RMSE | Ability coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | effect_scalex0.25 | 3072 | 0.4526 | 0.1444 | 0.0186 | -0.0030 | 0.9603 | 1.0832 | 0.9531 |
| balanced | effect_scalex4 | 3072 | 0.4538 | 0.1450 | 0.0222 | -0.0155 | 0.9987 | 1.1855 | 0.9531 |
| balanced | extra_mean+0.5 | 3072 | 0.4504 | 0.1436 | 0.0148 | -0.0037 | 0.9867 | 1.0892 | 0.9531 |
| balanced | extra_mean-0.5 | 3072 | 0.4535 | 0.1448 | 0.0176 | -0.0093 | 0.9847 | 1.0892 | 0.9531 |
| balanced | extra_varx0.25 | 3072 | 0.4516 | 0.1441 | 0.0185 | -0.0065 | 0.9857 | 1.0771 | 0.9688 |
| balanced | extra_varx4 | 3072 | 0.4516 | 0.1441 | 0.0165 | -0.0065 | 0.9863 | 1.0982 | 0.9844 |
| balanced | family_mean+0.5 | 3072 | 0.4568 | 0.1453 | 0.0268 | 0.0027 | 0.9808 | 1.0878 | 0.9844 |
| balanced | family_mean-0.5 | 3072 | 0.4589 | 0.1473 | 0.0247 | -0.0174 | 0.9818 | 1.0932 | 0.9531 |
| balanced | family_varx0.25 | 3072 | 0.4479 | 0.1426 | 0.0139 | -0.0076 | 0.9867 | 1.0822 | 1.0000 |
| balanced | family_varx4 | 3072 | 0.4600 | 0.1471 | 0.0319 | -0.0054 | 0.9837 | 1.0919 | 0.9531 |
| balanced | item_mean+0.5 | 3072 | 0.4546 | 0.1447 | 0.0277 | -0.0042 | 0.9840 | 1.1139 | 0.9531 |
| balanced | item_mean-0.5 | 3072 | 0.4586 | 0.1471 | 0.0221 | -0.0099 | 0.9840 | 1.0755 | 0.9688 |
| balanced | item_varx0.25 | 3072 | 0.4488 | 0.1430 | 0.0202 | -0.0062 | 0.9863 | 1.0727 | 0.9844 |
| balanced | item_varx4 | 3072 | 0.4583 | 0.1464 | 0.0275 | -0.0072 | 0.9834 | 1.1040 | 0.9688 |
| balanced | predecessor | 3072 | 0.5043 | 0.1665 | 0.0907 | -0.0907 | 0.9694 | 1.2319 | 0.9844 |
| balanced | rho0.0-H1 | 3072 | 0.4517 | 0.1441 | 0.0159 | -0.0070 | 0.9857 | 1.0809 | 0.9531 |
| balanced | rho0.0-H3 | 3072 | 0.4517 | 0.1441 | 0.0156 | -0.0071 | 0.9857 | 1.0866 | 0.9531 |
| balanced | rho0.0-H5 | 3072 | 0.4517 | 0.1441 | 0.0155 | -0.0068 | 0.9863 | 1.1051 | 1.0000 |
| balanced | rho0.5-H1 | 3072 | 0.4516 | 0.1441 | 0.0185 | -0.0065 | 0.9854 | 1.0757 | 0.9688 |
| balanced | rho0.5-H3 | 3072 | 0.4516 | 0.1441 | 0.0192 | -0.0065 | 0.9857 | 1.0812 | 0.9688 |
| balanced | rho0.5-H5 | 3072 | 0.4516 | 0.1441 | 0.0176 | -0.0062 | 0.9863 | 1.0995 | 1.0000 |
| balanced | rho1.0-H1 | 3072 | 0.4525 | 0.1445 | 0.0197 | -0.0060 | 0.9824 | 1.0712 | 0.9688 |
| balanced | rho1.0-H3 | 3072 | 0.4525 | 0.1445 | 0.0194 | -0.0060 | 0.9824 | 1.0765 | 0.9844 |
| balanced | rho1.0-H5 | 3072 | 0.4525 | 0.1445 | 0.0183 | -0.0058 | 0.9831 | 1.0947 | 1.0000 |
| family_memory | effect_scalex0.25 | 3072 | 0.3604 | 0.1077 | 0.0260 | -0.0162 | 0.9303 | 1.5202 | 0.8438 |
| family_memory | effect_scalex4 | 3072 | 0.3661 | 0.1095 | 0.0398 | -0.0384 | 0.9919 | 1.5219 | 0.8906 |
| family_memory | extra_mean+0.5 | 3072 | 0.3605 | 0.1076 | 0.0237 | -0.0182 | 0.9635 | 1.4803 | 0.8750 |
| family_memory | extra_mean-0.5 | 3072 | 0.3611 | 0.1080 | 0.0283 | -0.0252 | 0.9668 | 1.4900 | 0.8906 |
| family_memory | extra_varx0.25 | 3072 | 0.3607 | 0.1078 | 0.0282 | -0.0217 | 0.9639 | 1.4741 | 0.8594 |
| family_memory | extra_varx4 | 3072 | 0.3606 | 0.1077 | 0.0269 | -0.0218 | 0.9652 | 1.4938 | 0.8906 |
| family_memory | family_mean+0.5 | 3072 | 0.3458 | 0.1030 | 0.0161 | -0.0117 | 0.9740 | 1.4500 | 0.8750 |
| family_memory | family_mean-0.5 | 3072 | 0.3885 | 0.1180 | 0.0470 | -0.0344 | 0.9040 | 1.5340 | 0.8594 |
| family_memory | family_varx0.25 | 3072 | 0.3703 | 0.1111 | 0.0285 | -0.0240 | 0.9411 | 1.5309 | 0.8594 |
| family_memory | family_varx4 | 3072 | 0.3553 | 0.1061 | 0.0196 | -0.0191 | 0.9697 | 1.4345 | 0.8750 |
| family_memory | item_mean+0.5 | 3072 | 0.3536 | 0.1058 | 0.0196 | -0.0179 | 0.9707 | 1.4657 | 0.8750 |
| family_memory | item_mean-0.5 | 3072 | 0.3763 | 0.1132 | 0.0388 | -0.0273 | 0.9072 | 1.5193 | 0.8594 |
| family_memory | item_varx0.25 | 3072 | 0.3636 | 0.1085 | 0.0291 | -0.0223 | 0.9447 | 1.5037 | 0.8438 |
| family_memory | item_varx4 | 3072 | 0.3595 | 0.1079 | 0.0232 | -0.0214 | 0.9701 | 1.4429 | 0.8906 |
| family_memory | predecessor | 3072 | 0.5504 | 0.1858 | 0.1905 | -0.1869 | 0.6846 | 1.2267 | 0.9688 |
| family_memory | rho0.0-H1 | 3072 | 0.3610 | 0.1078 | 0.0266 | -0.0213 | 0.9629 | 1.4824 | 0.8750 |
| family_memory | rho0.0-H3 | 3072 | 0.3610 | 0.1078 | 0.0273 | -0.0213 | 0.9635 | 1.4877 | 0.8906 |
| family_memory | rho0.0-H5 | 3072 | 0.3610 | 0.1078 | 0.0261 | -0.0210 | 0.9642 | 1.5057 | 0.8906 |
| family_memory | rho0.5-H1 | 3072 | 0.3607 | 0.1078 | 0.0283 | -0.0217 | 0.9639 | 1.4727 | 0.8594 |
| family_memory | rho0.5-H3 | 3072 | 0.3607 | 0.1077 | 0.0279 | -0.0217 | 0.9642 | 1.4782 | 0.8750 |
| family_memory | rho0.5-H5 | 3072 | 0.3606 | 0.1077 | 0.0271 | -0.0214 | 0.9648 | 1.4971 | 0.8750 |
| family_memory | rho1.0-H1 | 3072 | 0.3607 | 0.1078 | 0.0296 | -0.0220 | 0.9635 | 1.4672 | 0.8438 |
| family_memory | rho1.0-H3 | 3072 | 0.3606 | 0.1078 | 0.0295 | -0.0221 | 0.9639 | 1.4728 | 0.8594 |
| family_memory | rho1.0-H5 | 3072 | 0.3606 | 0.1078 | 0.0290 | -0.0218 | 0.9648 | 1.4927 | 0.8750 |
| independent | effect_scalex0.25 | 3072 | 0.4499 | 0.1434 | 0.0169 | -0.0043 | 0.9495 | 1.1159 | 0.9688 |
| independent | effect_scalex4 | 3072 | 0.4513 | 0.1441 | 0.0206 | -0.0160 | 0.9977 | 1.1672 | 0.9688 |
| independent | extra_mean+0.5 | 3072 | 0.4476 | 0.1426 | 0.0125 | -0.0047 | 0.9798 | 1.1077 | 0.9688 |
| independent | extra_mean-0.5 | 3072 | 0.4510 | 0.1438 | 0.0167 | -0.0105 | 0.9788 | 1.1146 | 0.9531 |
| independent | extra_varx0.25 | 3072 | 0.4489 | 0.1431 | 0.0143 | -0.0075 | 0.9792 | 1.0999 | 0.9688 |
| independent | extra_varx4 | 3072 | 0.4491 | 0.1431 | 0.0139 | -0.0076 | 0.9795 | 1.1153 | 0.9688 |
| independent | family_mean+0.5 | 3072 | 0.4542 | 0.1442 | 0.0235 | 0.0021 | 0.9733 | 1.1122 | 0.9688 |
| independent | family_mean-0.5 | 3072 | 0.4563 | 0.1465 | 0.0243 | -0.0188 | 0.9749 | 1.1162 | 0.9531 |
| independent | family_varx0.25 | 3072 | 0.4446 | 0.1415 | 0.0144 | -0.0087 | 0.9772 | 1.0927 | 0.9688 |
| independent | family_varx4 | 3072 | 0.4582 | 0.1462 | 0.0259 | -0.0063 | 0.9766 | 1.1225 | 0.9531 |
| independent | item_mean+0.5 | 3072 | 0.4525 | 0.1437 | 0.0193 | -0.0054 | 0.9753 | 1.1403 | 0.9531 |
| independent | item_mean-0.5 | 3072 | 0.4553 | 0.1460 | 0.0187 | -0.0110 | 0.9769 | 1.0925 | 0.9688 |
| independent | item_varx0.25 | 3072 | 0.4459 | 0.1420 | 0.0175 | -0.0075 | 0.9805 | 1.0968 | 0.9688 |
| independent | item_varx4 | 3072 | 0.4559 | 0.1452 | 0.0213 | -0.0083 | 0.9769 | 1.1247 | 0.9531 |
| independent | predecessor | 3072 | 0.5021 | 0.1654 | 0.0935 | -0.0935 | 0.9684 | 1.2532 | 0.9531 |
| independent | rho0.0-H1 | 3072 | 0.4482 | 0.1428 | 0.0151 | -0.0081 | 0.9798 | 1.1126 | 0.9531 |
| independent | rho0.0-H3 | 3072 | 0.4482 | 0.1428 | 0.0154 | -0.0082 | 0.9801 | 1.1167 | 0.9531 |
| independent | rho0.0-H5 | 3072 | 0.4481 | 0.1428 | 0.0159 | -0.0079 | 0.9805 | 1.1261 | 0.9688 |
| independent | rho0.5-H1 | 3072 | 0.4489 | 0.1431 | 0.0142 | -0.0075 | 0.9792 | 1.0989 | 0.9688 |
| independent | rho0.5-H3 | 3072 | 0.4489 | 0.1431 | 0.0137 | -0.0076 | 0.9792 | 1.1029 | 0.9688 |
| independent | rho0.5-H5 | 3072 | 0.4489 | 0.1431 | 0.0144 | -0.0073 | 0.9795 | 1.1132 | 0.9688 |
| independent | rho1.0-H1 | 3072 | 0.4510 | 0.1438 | 0.0161 | -0.0071 | 0.9717 | 1.0873 | 0.9688 |
| independent | rho1.0-H3 | 3072 | 0.4510 | 0.1438 | 0.0169 | -0.0071 | 0.9723 | 1.0913 | 0.9688 |
| independent | rho1.0-H5 | 3072 | 0.4510 | 0.1438 | 0.0155 | -0.0068 | 0.9727 | 1.1025 | 0.9688 |
| no_memory | effect_scalex0.25 | 3072 | 0.4918 | 0.1613 | 0.0273 | 0.0009 | 0.9170 | 1.0135 | 1.0000 |
| no_memory | effect_scalex4 | 3072 | 0.4929 | 0.1610 | 0.0233 | -0.0037 | 0.9899 | 1.0394 | 0.9844 |
| no_memory | extra_mean+0.5 | 3072 | 0.4898 | 0.1604 | 0.0312 | 0.0020 | 0.9691 | 1.0053 | 1.0000 |
| no_memory | extra_mean-0.5 | 3072 | 0.4899 | 0.1605 | 0.0264 | -0.0017 | 0.9632 | 0.9849 | 0.9844 |
| no_memory | extra_varx0.25 | 3072 | 0.4889 | 0.1601 | 0.0312 | 0.0002 | 0.9658 | 0.9864 | 1.0000 |
| no_memory | extra_varx4 | 3072 | 0.4891 | 0.1602 | 0.0280 | 0.0004 | 0.9668 | 0.9963 | 1.0000 |
| no_memory | family_mean+0.5 | 3072 | 0.4965 | 0.1621 | 0.0349 | 0.0085 | 0.9596 | 1.0046 | 1.0000 |
| no_memory | family_mean-0.5 | 3072 | 0.4930 | 0.1620 | 0.0351 | -0.0085 | 0.9632 | 0.9846 | 0.9844 |
| no_memory | family_varx0.25 | 3072 | 0.4863 | 0.1591 | 0.0330 | 0.0004 | 0.9665 | 0.9878 | 1.0000 |
| no_memory | family_varx4 | 3072 | 0.4956 | 0.1624 | 0.0280 | -0.0002 | 0.9652 | 0.9994 | 1.0000 |
| no_memory | item_mean+0.5 | 3072 | 0.5042 | 0.1650 | 0.0452 | 0.0021 | 0.9538 | 1.0343 | 1.0000 |
| no_memory | item_mean-0.5 | 3072 | 0.4838 | 0.1582 | 0.0164 | -0.0019 | 0.9665 | 0.9629 | 1.0000 |
| no_memory | item_varx0.25 | 3072 | 0.4914 | 0.1610 | 0.0286 | -0.0001 | 0.9635 | 0.9844 | 1.0000 |
| no_memory | item_varx4 | 3072 | 0.4913 | 0.1608 | 0.0255 | 0.0005 | 0.9658 | 1.0104 | 1.0000 |
| no_memory | predecessor | 3072 | 0.5142 | 0.1707 | 0.0254 | -0.0136 | 0.9619 | 1.2319 | 0.9844 |
| no_memory | rho0.0-H1 | 3072 | 0.4894 | 0.1603 | 0.0352 | 0.0004 | 0.9661 | 0.9968 | 1.0000 |
| no_memory | rho0.0-H3 | 3072 | 0.4894 | 0.1603 | 0.0359 | 0.0005 | 0.9665 | 0.9987 | 1.0000 |
| no_memory | rho0.0-H5 | 3072 | 0.4895 | 0.1604 | 0.0317 | 0.0006 | 0.9665 | 1.0112 | 0.9844 |
| no_memory | rho0.5-H1 | 3072 | 0.4889 | 0.1601 | 0.0310 | 0.0001 | 0.9658 | 0.9860 | 1.0000 |
| no_memory | rho0.5-H3 | 3072 | 0.4889 | 0.1601 | 0.0304 | 0.0002 | 0.9658 | 0.9880 | 1.0000 |
| no_memory | rho0.5-H5 | 3072 | 0.4890 | 0.1602 | 0.0300 | 0.0003 | 0.9658 | 1.0007 | 1.0000 |
| no_memory | rho1.0-H1 | 3072 | 0.4896 | 0.1604 | 0.0303 | -0.0004 | 0.9616 | 0.9770 | 1.0000 |
| no_memory | rho1.0-H3 | 3072 | 0.4897 | 0.1604 | 0.0303 | -0.0003 | 0.9619 | 0.9791 | 1.0000 |
| no_memory | rho1.0-H5 | 3072 | 0.4898 | 0.1605 | 0.0301 | -0.0003 | 0.9635 | 0.9919 | 1.0000 |
| shared | effect_scalex0.25 | 3072 | 0.4501 | 0.1441 | 0.0236 | -0.0054 | 0.9577 | 1.1873 | 0.9062 |
| shared | effect_scalex4 | 3072 | 0.4498 | 0.1437 | 0.0181 | -0.0158 | 0.9997 | 1.2981 | 0.9375 |
| shared | extra_mean+0.5 | 3072 | 0.4466 | 0.1428 | 0.0158 | -0.0053 | 0.9844 | 1.1870 | 0.9219 |
| shared | extra_mean-0.5 | 3072 | 0.4507 | 0.1442 | 0.0180 | -0.0111 | 0.9814 | 1.2007 | 0.8750 |
| shared | extra_varx0.25 | 3072 | 0.4484 | 0.1434 | 0.0155 | -0.0082 | 0.9834 | 1.1836 | 0.8906 |
| shared | extra_varx4 | 3072 | 0.4482 | 0.1433 | 0.0166 | -0.0082 | 0.9837 | 1.1992 | 0.9219 |
| shared | family_mean+0.5 | 3072 | 0.4542 | 0.1445 | 0.0197 | 0.0010 | 0.9795 | 1.1916 | 0.9062 |
| shared | family_mean-0.5 | 3072 | 0.4549 | 0.1467 | 0.0233 | -0.0189 | 0.9782 | 1.1996 | 0.9062 |
| shared | family_varx0.25 | 3072 | 0.4444 | 0.1419 | 0.0184 | -0.0091 | 0.9834 | 1.1829 | 0.8906 |
| shared | family_varx4 | 3072 | 0.4566 | 0.1462 | 0.0248 | -0.0073 | 0.9811 | 1.2009 | 0.8906 |
| shared | item_mean+0.5 | 3072 | 0.4517 | 0.1440 | 0.0226 | -0.0058 | 0.9798 | 1.2312 | 0.8906 |
| shared | item_mean-0.5 | 3072 | 0.4552 | 0.1463 | 0.0156 | -0.0116 | 0.9808 | 1.1732 | 0.8906 |
| shared | item_varx0.25 | 3072 | 0.4459 | 0.1425 | 0.0111 | -0.0081 | 0.9834 | 1.1723 | 0.9062 |
| shared | item_varx4 | 3072 | 0.4549 | 0.1455 | 0.0239 | -0.0087 | 0.9821 | 1.2131 | 0.8906 |
| shared | predecessor | 3072 | 0.5033 | 0.1670 | 0.0935 | -0.0935 | 0.9736 | 1.2630 | 0.9844 |
| shared | rho0.0-H1 | 3072 | 0.4495 | 0.1439 | 0.0161 | -0.0090 | 0.9840 | 1.1918 | 0.8906 |
| shared | rho0.0-H3 | 3072 | 0.4494 | 0.1439 | 0.0163 | -0.0090 | 0.9844 | 1.1957 | 0.8906 |
| shared | rho0.0-H5 | 3072 | 0.4492 | 0.1438 | 0.0183 | -0.0088 | 0.9847 | 1.2105 | 0.8906 |
| shared | rho0.5-H1 | 3072 | 0.4484 | 0.1434 | 0.0155 | -0.0082 | 0.9831 | 1.1826 | 0.8906 |
| shared | rho0.5-H3 | 3072 | 0.4483 | 0.1434 | 0.0158 | -0.0082 | 0.9834 | 1.1865 | 0.8906 |
| shared | rho0.5-H5 | 3072 | 0.4481 | 0.1433 | 0.0161 | -0.0079 | 0.9834 | 1.2019 | 0.9219 |
| shared | rho1.0-H1 | 3072 | 0.4485 | 0.1434 | 0.0180 | -0.0075 | 0.9792 | 1.1750 | 0.8906 |
| shared | rho1.0-H3 | 3072 | 0.4485 | 0.1434 | 0.0186 | -0.0076 | 0.9795 | 1.1788 | 0.9219 |
| shared | rho1.0-H5 | 3072 | 0.4482 | 0.1433 | 0.0170 | -0.0073 | 0.9805 | 1.1949 | 0.9219 |
| slow_retention | effect_scalex0.25 | 3072 | 0.3201 | 0.0920 | 0.0324 | -0.0303 | 0.8988 | 1.8189 | 0.6875 |
| slow_retention | effect_scalex4 | 3072 | 0.3264 | 0.0941 | 0.0534 | -0.0527 | 0.9837 | 2.0405 | 0.7812 |
| slow_retention | extra_mean+0.5 | 3072 | 0.3198 | 0.0918 | 0.0352 | -0.0324 | 0.9427 | 1.8006 | 0.7500 |
| slow_retention | extra_mean-0.5 | 3072 | 0.3220 | 0.0928 | 0.0397 | -0.0394 | 0.9456 | 1.9263 | 0.7031 |
| slow_retention | extra_varx0.25 | 3072 | 0.3208 | 0.0922 | 0.0383 | -0.0359 | 0.9417 | 1.8571 | 0.6875 |
| slow_retention | extra_varx4 | 3072 | 0.3208 | 0.0923 | 0.0377 | -0.0359 | 0.9466 | 1.8674 | 0.7188 |
| slow_retention | family_mean+0.5 | 3072 | 0.3078 | 0.0882 | 0.0307 | -0.0274 | 0.9691 | 1.8131 | 0.7500 |
| slow_retention | family_mean-0.5 | 3072 | 0.3459 | 0.1016 | 0.0481 | -0.0473 | 0.8649 | 1.9440 | 0.6562 |
| slow_retention | family_varx0.25 | 3072 | 0.3287 | 0.0949 | 0.0372 | -0.0372 | 0.9036 | 1.9226 | 0.6562 |
| slow_retention | family_varx4 | 3072 | 0.3175 | 0.0914 | 0.0358 | -0.0349 | 0.9645 | 1.8335 | 0.7344 |
| slow_retention | item_mean+0.5 | 3072 | 0.3159 | 0.0908 | 0.0352 | -0.0340 | 0.9681 | 1.8961 | 0.7188 |
| slow_retention | item_mean-0.5 | 3072 | 0.3336 | 0.0970 | 0.0431 | -0.0399 | 0.8584 | 1.8750 | 0.7188 |
| slow_retention | item_varx0.25 | 3072 | 0.3224 | 0.0927 | 0.0362 | -0.0361 | 0.9079 | 1.8747 | 0.6875 |
| slow_retention | item_varx4 | 3072 | 0.3211 | 0.0928 | 0.0371 | -0.0362 | 0.9635 | 1.8520 | 0.7344 |
| slow_retention | predecessor | 3072 | 0.4883 | 0.1605 | 0.1843 | -0.1832 | 0.6562 | 1.3600 | 0.9844 |
| slow_retention | rho0.0-H1 | 3072 | 0.3215 | 0.0924 | 0.0376 | -0.0358 | 0.9424 | 1.8809 | 0.7031 |
| slow_retention | rho0.0-H3 | 3072 | 0.3215 | 0.0924 | 0.0370 | -0.0358 | 0.9434 | 1.8838 | 0.7188 |
| slow_retention | rho0.0-H5 | 3072 | 0.3214 | 0.0924 | 0.0374 | -0.0354 | 0.9447 | 1.8897 | 0.7500 |
| slow_retention | rho0.5-H1 | 3072 | 0.3208 | 0.0922 | 0.0386 | -0.0358 | 0.9421 | 1.8563 | 0.6875 |
| slow_retention | rho0.5-H3 | 3072 | 0.3208 | 0.0922 | 0.0383 | -0.0359 | 0.9427 | 1.8593 | 0.7031 |
| slow_retention | rho0.5-H5 | 3072 | 0.3207 | 0.0922 | 0.0379 | -0.0355 | 0.9440 | 1.8656 | 0.7500 |
| slow_retention | rho1.0-H1 | 3072 | 0.3203 | 0.0922 | 0.0404 | -0.0359 | 0.9430 | 1.8342 | 0.6875 |
| slow_retention | rho1.0-H3 | 3072 | 0.3203 | 0.0922 | 0.0401 | -0.0359 | 0.9437 | 1.8373 | 0.7031 |
| slow_retention | rho1.0-H5 | 3072 | 0.3203 | 0.0922 | 0.0397 | -0.0355 | 0.9443 | 1.8442 | 0.7656 |

## Descriptive baselines

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Same baseline predictions in both views. Each world: 3,072 presentations; FSRS available only on 1,792 repeats (28/learner), not comparable to a full-stream loss without restricting the other arms. Rate a=.5/1/2 all remain candidates; last-outcome's 0/1 values are clipped only for log loss.

| World | Baseline | N | Loss | Brier | ECE | Bias | Eta coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | fsrs | 1792 | 0.4868 | 0.1383 | 0.0972 | 0.0972 | N/A |
| balanced | last | 3072 | 5.5056 | 0.2702 | 0.2656 | -0.0046 | N/A |
| balanced | mastery_ekf | 3072 | 0.4832 | 0.1570 | 0.0139 | -0.0050 | N/A |
| balanced | rate:.5 | 3072 | 0.4959 | 0.1617 | 0.0566 | -0.0517 | N/A |
| balanced | rate:1 | 3072 | 0.4941 | 0.1614 | 0.0632 | -0.0632 | N/A |
| balanced | rate:2 | 3072 | 0.4990 | 0.1630 | 0.0811 | -0.0811 | N/A |
| family_memory | fsrs | 1792 | 0.2721 | 0.0707 | 0.0221 | 0.0221 | N/A |
| family_memory | last | 3072 | 4.1901 | 0.2067 | 0.2021 | -0.0042 | N/A |
| family_memory | mastery_ekf | 3072 | 0.4332 | 0.1331 | 0.0461 | -0.0270 | N/A |
| family_memory | rate:.5 | 3072 | 0.4417 | 0.1363 | 0.0544 | -0.0397 | N/A |
| family_memory | rate:1 | 3072 | 0.4413 | 0.1368 | 0.0619 | -0.0562 | N/A |
| family_memory | rate:2 | 3072 | 0.4488 | 0.1396 | 0.0825 | -0.0822 | N/A |
| independent | fsrs | 1792 | 0.4707 | 0.1345 | 0.0935 | 0.0935 | N/A |
| independent | last | 3072 | 5.5123 | 0.2705 | 0.2656 | -0.0046 | N/A |
| independent | mastery_ekf | 3072 | 0.4800 | 0.1560 | 0.0185 | -0.0076 | N/A |
| independent | rate:.5 | 3072 | 0.4951 | 0.1621 | 0.0600 | -0.0558 | N/A |
| independent | rate:1 | 3072 | 0.4937 | 0.1617 | 0.0667 | -0.0667 | N/A |
| independent | rate:2 | 3072 | 0.4988 | 0.1632 | 0.0839 | -0.0839 | N/A |
| no_memory | fsrs | 1792 | 0.7899 | 0.2242 | 0.2004 | 0.2004 | N/A |
| no_memory | last | 3072 | 5.5595 | 0.2728 | 0.2682 | -0.0046 | N/A |
| no_memory | mastery_ekf | 3072 | 0.4884 | 0.1601 | 0.0165 | 0.0113 | N/A |
| no_memory | rate:.5 | 3072 | 0.5087 | 0.1685 | 0.0681 | -0.0667 | N/A |
| no_memory | rate:1 | 3072 | 0.5070 | 0.1681 | 0.0725 | -0.0725 | N/A |
| no_memory | rate:2 | 3072 | 0.5117 | 0.1695 | 0.0826 | -0.0819 | N/A |
| shared | fsrs | 1792 | 0.4861 | 0.1377 | 0.0968 | 0.0958 | N/A |
| shared | last | 3072 | 5.4246 | 0.2663 | 0.2617 | -0.0046 | N/A |
| shared | mastery_ekf | 3072 | 0.4833 | 0.1576 | 0.0125 | -0.0078 | N/A |
| shared | rate:.5 | 3072 | 0.4951 | 0.1621 | 0.0575 | -0.0537 | N/A |
| shared | rate:1 | 3072 | 0.4937 | 0.1617 | 0.0650 | -0.0650 | N/A |
| shared | rate:2 | 3072 | 0.4988 | 0.1633 | 0.0827 | -0.0827 | N/A |
| slow_retention | fsrs | 1792 | 0.2466 | 0.0610 | 0.0145 | 0.0121 | N/A |
| slow_retention | last | 3072 | 3.5493 | 0.1758 | 0.1712 | -0.0059 | N/A |
| slow_retention | mastery_ekf | 3072 | 0.3767 | 0.1119 | 0.0408 | -0.0408 | N/A |
| slow_retention | rate:.5 | 3072 | 0.3861 | 0.1156 | 0.0579 | -0.0512 | N/A |
| slow_retention | rate:1 | 3072 | 0.3885 | 0.1165 | 0.0703 | -0.0683 | N/A |
| slow_retention | rate:2 | 3072 | 0.4001 | 0.1202 | 0.0954 | -0.0954 | N/A |

## Strata, delay and singleton checks — subject

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Row N is the prediction count. Overlapping flags (singleton_all, all_first_surfaces, delay and source) are not additional observations. First_surface names initial anchors; all_first_surfaces also includes singleton-first and novel-after-drilling.

| World | Arm | Stratum | N | Loss | Brier | ECE | Bias | Eta coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | predecessor | all_first_surfaces | 768 | 0.5385 | 0.1806 | 0.0382 | -0.0130 | 0.9544 |
| balanced | predecessor | assigned | 1536 | 0.5383 | 0.1796 | 0.1199 | -0.1138 | 0.9753 |
| balanced | predecessor | delay:1..7d | 512 | 0.5262 | 0.1772 | 0.1477 | -0.1477 | 0.9805 |
| balanced | predecessor | delay:<=1d | 1024 | 0.4564 | 0.1464 | 0.1559 | -0.1559 | 0.9775 |
| balanced | predecessor | delay:>7d | 256 | 0.5431 | 0.1809 | 0.1116 | -0.0853 | 0.9961 |
| balanced | predecessor | delay:none | 1280 | 0.5263 | 0.1755 | 0.0324 | -0.0168 | 0.9531 |
| balanced | predecessor | first_surface | 256 | 0.5820 | 0.1979 | 0.0250 | 0.0107 | 0.9492 |
| balanced | predecessor | natural | 1536 | 0.4704 | 0.1534 | 0.0690 | -0.0676 | 0.9635 |
| balanced | predecessor | novel_after_drilling | 256 | 0.5096 | 0.1684 | 0.0410 | -0.0175 | 0.9727 |
| balanced | predecessor | same_item | 1792 | 0.4887 | 0.1601 | 0.1435 | -0.1435 | 0.9810 |
| balanced | predecessor | singleton_all | 512 | 0.4845 | 0.1577 | 0.0901 | -0.0854 | 0.9707 |
| balanced | predecessor | singleton_first | 256 | 0.5239 | 0.1754 | 0.0785 | -0.0322 | 0.9414 |
| balanced | predecessor | unseen_sibling | 512 | 0.5079 | 0.1679 | 0.0449 | -0.0225 | 0.9512 |
| balanced | R3-H3 | all_first_surfaces | 768 | 0.5246 | 0.1749 | 0.0311 | -0.0019 | 0.9622 |
| balanced | R3-H3 | assigned | 1536 | 0.4789 | 0.1541 | 0.0261 | -0.0147 | 0.9857 |
| balanced | R3-H3 | delay:1..7d | 512 | 0.4239 | 0.1322 | 0.0403 | -0.0034 | 1.0000 |
| balanced | R3-H3 | delay:<=1d | 1024 | 0.3781 | 0.1133 | 0.0279 | -0.0189 | 1.0000 |
| balanced | R3-H3 | delay:>7d | 256 | 0.5034 | 0.1647 | 0.0423 | -0.0057 | 1.0000 |
| balanced | R3-H3 | delay:none | 1280 | 0.5116 | 0.1695 | 0.0307 | 0.0020 | 0.9672 |
| balanced | R3-H3 | first_surface | 256 | 0.5722 | 0.1936 | 0.0386 | 0.0170 | 0.9609 |
| balanced | R3-H3 | natural | 1536 | 0.4247 | 0.1342 | 0.0222 | 0.0017 | 0.9870 |
| balanced | R3-H3 | novel_after_drilling | 256 | 0.4964 | 0.1627 | 0.0272 | -0.0032 | 0.9766 |
| balanced | R3-H3 | same_item | 1792 | 0.4091 | 0.1260 | 0.0240 | -0.0126 | 1.0000 |
| balanced | R3-H3 | singleton_all | 512 | 0.4423 | 0.1410 | 0.0296 | -0.0254 | 0.9746 |
| balanced | R3-H3 | singleton_first | 256 | 0.5053 | 0.1684 | 0.0569 | -0.0195 | 0.9492 |
| balanced | R3-H3 | unseen_sibling | 512 | 0.4920 | 0.1615 | 0.0318 | 0.0078 | 0.9746 |
| family_memory | predecessor | all_first_surfaces | 768 | 0.5485 | 0.1849 | 0.0336 | -0.0037 | 0.9635 |
| family_memory | predecessor | assigned | 1536 | 0.5853 | 0.2010 | 0.2260 | -0.2257 | 0.6602 |
| family_memory | predecessor | delay:1..7d | 512 | 0.5999 | 0.2066 | 0.2837 | -0.2742 | 0.5508 |
| family_memory | predecessor | delay:<=1d | 1024 | 0.4803 | 0.1575 | 0.2431 | -0.2431 | 0.4990 |
| family_memory | predecessor | delay:>7d | 256 | 0.7484 | 0.2603 | 0.2895 | -0.1825 | 0.6992 |
| family_memory | predecessor | delay:none | 1280 | 0.5471 | 0.1852 | 0.1081 | -0.1079 | 0.8836 |
| family_memory | predecessor | first_surface | 256 | 0.6033 | 0.2064 | 0.0329 | 0.0157 | 0.9609 |
| family_memory | predecessor | natural | 1536 | 0.5154 | 0.1705 | 0.1551 | -0.1481 | 0.7090 |
| family_memory | predecessor | novel_after_drilling | 256 | 0.5029 | 0.1658 | 0.0247 | -0.0068 | 0.9805 |
| family_memory | predecessor | same_item | 1792 | 0.5527 | 0.1862 | 0.2503 | -0.2433 | 0.5424 |
| family_memory | predecessor | singleton_all | 512 | 0.5116 | 0.1704 | 0.1189 | -0.1189 | 0.9395 |
| family_memory | predecessor | singleton_first | 256 | 0.5393 | 0.1824 | 0.0630 | -0.0201 | 0.9492 |
| family_memory | predecessor | unseen_sibling | 512 | 0.5450 | 0.1857 | 0.2642 | -0.2642 | 0.7637 |
| family_memory | R3-H3 | all_first_surfaces | 768 | 0.5753 | 0.1941 | 0.0711 | 0.0597 | 0.9102 |
| family_memory | R3-H3 | assigned | 1536 | 0.3672 | 0.1096 | 0.0531 | -0.0475 | 0.9629 |
| family_memory | R3-H3 | delay:1..7d | 512 | 0.2538 | 0.0666 | 0.0513 | -0.0375 | 0.9824 |
| family_memory | R3-H3 | delay:<=1d | 1024 | 0.2592 | 0.0681 | 0.0537 | -0.0537 | 0.9893 |
| family_memory | R3-H3 | delay:>7d | 256 | 0.4046 | 0.1203 | 0.0824 | -0.0083 | 0.9688 |
| family_memory | R3-H3 | delay:none | 1280 | 0.4758 | 0.1535 | 0.0233 | 0.0074 | 0.9359 |
| family_memory | R3-H3 | first_surface | 256 | 0.6322 | 0.2148 | 0.0788 | 0.0628 | 0.9258 |
| family_memory | R3-H3 | natural | 1536 | 0.3541 | 0.1059 | 0.0110 | 0.0040 | 0.9655 |
| family_memory | R3-H3 | novel_after_drilling | 256 | 0.5422 | 0.1799 | 0.0710 | 0.0620 | 0.9219 |
| family_memory | R3-H3 | same_item | 1792 | 0.2784 | 0.0751 | 0.0429 | -0.0426 | 0.9844 |
| family_memory | R3-H3 | singleton_all | 512 | 0.4432 | 0.1420 | 0.0316 | -0.0068 | 0.9414 |
| family_memory | R3-H3 | singleton_first | 256 | 0.5516 | 0.1878 | 0.0861 | 0.0544 | 0.8828 |
| family_memory | R3-H3 | unseen_sibling | 512 | 0.3265 | 0.0925 | 0.0715 | -0.0711 | 0.9746 |
| independent | predecessor | all_first_surfaces | 768 | 0.5334 | 0.1771 | 0.0399 | -0.0066 | 0.9518 |
| independent | predecessor | assigned | 1536 | 0.5302 | 0.1762 | 0.1132 | -0.1129 | 0.9753 |
| independent | predecessor | delay:1..7d | 512 | 0.5325 | 0.1786 | 0.1537 | -0.1487 | 0.9922 |
| independent | predecessor | delay:<=1d | 1024 | 0.4514 | 0.1450 | 0.1587 | -0.1587 | 0.9785 |
| independent | predecessor | delay:>7d | 256 | 0.5214 | 0.1727 | 0.1264 | -0.1077 | 0.9961 |
| independent | predecessor | delay:none | 1280 | 0.5265 | 0.1749 | 0.0256 | -0.0164 | 0.9453 |
| independent | predecessor | first_surface | 256 | 0.5610 | 0.1885 | 0.0562 | 0.0079 | 0.9531 |
| independent | predecessor | natural | 1536 | 0.4739 | 0.1546 | 0.0741 | -0.0741 | 0.9616 |
| independent | predecessor | novel_after_drilling | 256 | 0.5382 | 0.1768 | 0.0654 | 0.0076 | 0.9570 |
| independent | predecessor | same_item | 1792 | 0.4846 | 0.1586 | 0.1485 | -0.1485 | 0.9849 |
| independent | predecessor | singleton_all | 512 | 0.4653 | 0.1495 | 0.0920 | -0.0880 | 0.9727 |
| independent | predecessor | singleton_first | 256 | 0.5009 | 0.1658 | 0.0426 | -0.0351 | 0.9453 |
| independent | predecessor | unseen_sibling | 512 | 0.5163 | 0.1717 | 0.0412 | -0.0312 | 0.9355 |
| independent | R3-H3 | all_first_surfaces | 768 | 0.5209 | 0.1716 | 0.0381 | 0.0053 | 0.9479 |
| independent | R3-H3 | assigned | 1536 | 0.4743 | 0.1524 | 0.0270 | -0.0131 | 0.9805 |
| independent | R3-H3 | delay:1..7d | 512 | 0.4087 | 0.1267 | 0.0170 | -0.0033 | 0.9961 |
| independent | R3-H3 | delay:<=1d | 1024 | 0.3756 | 0.1128 | 0.0238 | -0.0184 | 1.0000 |
| independent | R3-H3 | delay:>7d | 256 | 0.4727 | 0.1536 | 0.0558 | -0.0278 | 0.9961 |
| independent | R3-H3 | delay:none | 1280 | 0.5192 | 0.1718 | 0.0223 | 0.0035 | 0.9523 |
| independent | R3-H3 | first_surface | 256 | 0.5453 | 0.1825 | 0.0615 | 0.0156 | 0.9609 |
| independent | R3-H3 | natural | 1536 | 0.4238 | 0.1338 | 0.0145 | -0.0020 | 0.9779 |
| independent | R3-H3 | novel_after_drilling | 256 | 0.5235 | 0.1693 | 0.0457 | 0.0228 | 0.9414 |
| independent | R3-H3 | same_item | 1792 | 0.3989 | 0.1226 | 0.0177 | -0.0154 | 0.9983 |
| independent | R3-H3 | singleton_all | 512 | 0.4364 | 0.1382 | 0.0455 | -0.0271 | 0.9707 |
| independent | R3-H3 | singleton_first | 256 | 0.4939 | 0.1630 | 0.0515 | -0.0225 | 0.9414 |
| independent | R3-H3 | unseen_sibling | 512 | 0.5168 | 0.1721 | 0.0435 | 0.0008 | 0.9590 |
| no_memory | predecessor | all_first_surfaces | 768 | 0.5385 | 0.1806 | 0.0382 | -0.0130 | 0.9544 |
| no_memory | predecessor | assigned | 1536 | 0.5415 | 0.1810 | 0.0566 | -0.0305 | 0.9642 |
| no_memory | predecessor | delay:1..7d | 512 | 0.5330 | 0.1788 | 0.0342 | -0.0149 | 0.9648 |
| no_memory | predecessor | delay:<=1d | 1024 | 0.4902 | 0.1612 | 0.0159 | -0.0085 | 0.9707 |
| no_memory | predecessor | delay:>7d | 256 | 0.5120 | 0.1680 | 0.1199 | -0.0149 | 0.9648 |
| no_memory | predecessor | delay:none | 1280 | 0.5263 | 0.1755 | 0.0324 | -0.0168 | 0.9531 |
| no_memory | predecessor | first_surface | 256 | 0.5820 | 0.1979 | 0.0250 | 0.0107 | 0.9492 |
| no_memory | predecessor | natural | 1536 | 0.4868 | 0.1603 | 0.0229 | 0.0034 | 0.9596 |
| no_memory | predecessor | novel_after_drilling | 256 | 0.5096 | 0.1684 | 0.0410 | -0.0175 | 0.9727 |
| no_memory | predecessor | same_item | 1792 | 0.5055 | 0.1672 | 0.0224 | -0.0112 | 0.9682 |
| no_memory | predecessor | singleton_all | 512 | 0.4915 | 0.1620 | 0.0459 | -0.0190 | 0.9629 |
| no_memory | predecessor | singleton_first | 256 | 0.5239 | 0.1754 | 0.0785 | -0.0322 | 0.9414 |
| no_memory | predecessor | unseen_sibling | 512 | 0.5079 | 0.1679 | 0.0449 | -0.0225 | 0.9512 |
| no_memory | R3-H3 | all_first_surfaces | 768 | 0.5208 | 0.1739 | 0.0405 | -0.0208 | 0.9596 |
| no_memory | R3-H3 | assigned | 1536 | 0.5173 | 0.1705 | 0.0326 | -0.0046 | 0.9674 |
| no_memory | R3-H3 | delay:1..7d | 512 | 0.4739 | 0.1541 | 0.0716 | 0.0175 | 0.9609 |
| no_memory | R3-H3 | delay:<=1d | 1024 | 0.4800 | 0.1563 | 0.0463 | 0.0324 | 0.9590 |
| no_memory | R3-H3 | delay:>7d | 256 | 0.4777 | 0.1541 | 0.0445 | -0.0172 | 0.9844 |
| no_memory | R3-H3 | delay:none | 1280 | 0.5048 | 0.1670 | 0.0351 | -0.0290 | 0.9695 |
| no_memory | R3-H3 | first_surface | 256 | 0.5616 | 0.1903 | 0.0363 | 0.0011 | 0.9609 |
| no_memory | R3-H3 | natural | 1536 | 0.4610 | 0.1499 | 0.0290 | 0.0050 | 0.9642 |
| no_memory | R3-H3 | novel_after_drilling | 256 | 0.4980 | 0.1640 | 0.0761 | -0.0251 | 0.9570 |
| no_memory | R3-H3 | same_item | 1792 | 0.4779 | 0.1554 | 0.0388 | 0.0211 | 0.9632 |
| no_memory | R3-H3 | singleton_all | 512 | 0.4854 | 0.1601 | 0.0487 | -0.0012 | 0.9609 |
| no_memory | R3-H3 | singleton_first | 256 | 0.5029 | 0.1672 | 0.0859 | -0.0383 | 0.9609 |
| no_memory | R3-H3 | unseen_sibling | 512 | 0.4808 | 0.1566 | 0.0559 | -0.0414 | 0.9844 |
| shared | predecessor | all_first_surfaces | 768 | 0.5070 | 0.1692 | 0.0356 | -0.0236 | 0.9596 |
| shared | predecessor | assigned | 1536 | 0.5390 | 0.1813 | 0.1169 | -0.1136 | 0.9753 |
| shared | predecessor | delay:1..7d | 512 | 0.5216 | 0.1755 | 0.1432 | -0.1432 | 0.9844 |
| shared | predecessor | delay:<=1d | 1024 | 0.4649 | 0.1503 | 0.1613 | -0.1595 | 0.9717 |
| shared | predecessor | delay:>7d | 256 | 0.5639 | 0.1916 | 0.1488 | -0.1061 | 0.9961 |
| shared | predecessor | delay:none | 1280 | 0.5146 | 0.1719 | 0.0340 | -0.0182 | 0.9664 |
| shared | predecessor | first_surface | 256 | 0.5328 | 0.1802 | 0.0307 | -0.0071 | 0.9570 |
| shared | predecessor | natural | 1536 | 0.4677 | 0.1526 | 0.0742 | -0.0733 | 0.9720 |
| shared | predecessor | novel_after_drilling | 256 | 0.4623 | 0.1505 | 0.0552 | -0.0301 | 0.9727 |
| shared | predecessor | same_item | 1792 | 0.4952 | 0.1634 | 0.1472 | -0.1472 | 0.9788 |
| shared | predecessor | singleton_all | 512 | 0.4913 | 0.1609 | 0.0984 | -0.0865 | 0.9746 |
| shared | predecessor | singleton_first | 256 | 0.5258 | 0.1771 | 0.0636 | -0.0336 | 0.9492 |
| shared | predecessor | unseen_sibling | 512 | 0.5261 | 0.1759 | 0.0571 | -0.0102 | 0.9766 |
| shared | R3-H3 | all_first_surfaces | 768 | 0.4952 | 0.1650 | 0.0171 | -0.0137 | 0.9453 |
| shared | R3-H3 | assigned | 1536 | 0.4730 | 0.1526 | 0.0274 | -0.0142 | 0.9818 |
| shared | R3-H3 | delay:1..7d | 512 | 0.4284 | 0.1345 | 0.0198 | 0.0045 | 1.0000 |
| shared | R3-H3 | delay:<=1d | 1024 | 0.3799 | 0.1137 | 0.0293 | -0.0195 | 1.0000 |
| shared | R3-H3 | delay:>7d | 256 | 0.4821 | 0.1571 | 0.0341 | -0.0227 | 1.0000 |
| shared | R3-H3 | delay:none | 1280 | 0.5046 | 0.1680 | 0.0180 | -0.0013 | 0.9594 |
| shared | R3-H3 | first_surface | 256 | 0.5350 | 0.1805 | 0.0322 | -0.0011 | 0.9492 |
| shared | R3-H3 | natural | 1536 | 0.4239 | 0.1342 | 0.0203 | -0.0021 | 0.9844 |
| shared | R3-H3 | novel_after_drilling | 256 | 0.4471 | 0.1460 | 0.0375 | -0.0176 | 0.9492 |
| shared | R3-H3 | same_item | 1792 | 0.4083 | 0.1259 | 0.0186 | -0.0131 | 1.0000 |
| shared | R3-H3 | singleton_all | 512 | 0.4425 | 0.1416 | 0.0341 | -0.0257 | 0.9688 |
| shared | R3-H3 | singleton_first | 256 | 0.5033 | 0.1686 | 0.0477 | -0.0225 | 0.9375 |
| shared | R3-H3 | unseen_sibling | 512 | 0.5189 | 0.1724 | 0.0365 | 0.0174 | 0.9805 |
| slow_retention | predecessor | all_first_surfaces | 768 | 0.4957 | 0.1636 | 0.0380 | -0.0337 | 0.9505 |
| slow_retention | predecessor | assigned | 1536 | 0.5323 | 0.1794 | 0.2207 | -0.2207 | 0.6133 |
| slow_retention | predecessor | delay:1..7d | 512 | 0.5407 | 0.1824 | 0.2580 | -0.2503 | 0.4941 |
| slow_retention | predecessor | delay:<=1d | 1024 | 0.4361 | 0.1386 | 0.2194 | -0.2193 | 0.4922 |
| slow_retention | predecessor | delay:>7d | 256 | 0.6222 | 0.2110 | 0.2501 | -0.1957 | 0.7031 |
| slow_retention | predecessor | delay:none | 1280 | 0.4824 | 0.1591 | 0.1250 | -0.1250 | 0.8430 |
| slow_retention | predecessor | first_surface | 256 | 0.5256 | 0.1761 | 0.0479 | -0.0176 | 0.9375 |
| slow_retention | predecessor | natural | 1536 | 0.4443 | 0.1416 | 0.1540 | -0.1457 | 0.6992 |
| slow_retention | predecessor | novel_after_drilling | 256 | 0.4434 | 0.1420 | 0.0719 | -0.0579 | 0.9727 |
| slow_retention | predecessor | same_item | 1792 | 0.4926 | 0.1615 | 0.2326 | -0.2248 | 0.5229 |
| slow_retention | predecessor | singleton_all | 512 | 0.4792 | 0.1557 | 0.1221 | -0.1179 | 0.9238 |
| slow_retention | predecessor | singleton_first | 256 | 0.5181 | 0.1727 | 0.0519 | -0.0256 | 0.9414 |
| slow_retention | predecessor | unseen_sibling | 512 | 0.4625 | 0.1523 | 0.2619 | -0.2619 | 0.6816 |
| slow_retention | R3-H3 | all_first_surfaces | 768 | 0.5143 | 0.1688 | 0.0482 | 0.0335 | 0.8945 |
| slow_retention | R3-H3 | assigned | 1536 | 0.3358 | 0.0976 | 0.0585 | -0.0576 | 0.9447 |
| slow_retention | R3-H3 | delay:1..7d | 512 | 0.2417 | 0.0615 | 0.0535 | -0.0447 | 0.9297 |
| slow_retention | R3-H3 | delay:<=1d | 1024 | 0.2466 | 0.0629 | 0.0553 | -0.0553 | 0.9766 |
| slow_retention | R3-H3 | delay:>7d | 256 | 0.3297 | 0.0918 | 0.0787 | -0.0513 | 0.9375 |
| slow_retention | R3-H3 | delay:none | 1280 | 0.4099 | 0.1281 | 0.0251 | -0.0137 | 0.9227 |
| slow_retention | R3-H3 | first_surface | 256 | 0.5381 | 0.1802 | 0.0508 | 0.0308 | 0.9062 |
| slow_retention | R3-H3 | natural | 1536 | 0.3057 | 0.0869 | 0.0226 | -0.0142 | 0.9414 |
| slow_retention | R3-H3 | novel_after_drilling | 256 | 0.4457 | 0.1424 | 0.0273 | 0.0166 | 0.9062 |
| slow_retention | R3-H3 | same_item | 1792 | 0.2571 | 0.0666 | 0.0526 | -0.0517 | 0.9576 |
| slow_retention | R3-H3 | singleton_all | 512 | 0.4281 | 0.1319 | 0.0404 | -0.0132 | 0.9336 |
| slow_retention | R3-H3 | singleton_first | 256 | 0.5591 | 0.1838 | 0.0731 | 0.0530 | 0.8711 |
| slow_retention | R3-H3 | unseen_sibling | 512 | 0.2534 | 0.0671 | 0.0848 | -0.0844 | 0.9648 |

## Strata, delay and singleton checks — lo

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Row N is the prediction count. Overlapping flags (singleton_all, all_first_surfaces, delay and source) are not additional observations. First_surface names initial anchors; all_first_surfaces also includes singleton-first and novel-after-drilling.

| World | Arm | Stratum | N | Loss | Brier | ECE | Bias | Eta coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | predecessor | all_first_surfaces | 768 | 0.5385 | 0.1806 | 0.0382 | -0.0130 | 0.9544 |
| balanced | predecessor | assigned | 1536 | 0.5383 | 0.1796 | 0.1199 | -0.1138 | 0.9753 |
| balanced | predecessor | delay:1..7d | 512 | 0.5262 | 0.1772 | 0.1477 | -0.1477 | 0.9805 |
| balanced | predecessor | delay:<=1d | 1024 | 0.4564 | 0.1464 | 0.1559 | -0.1559 | 0.9775 |
| balanced | predecessor | delay:>7d | 256 | 0.5431 | 0.1809 | 0.1116 | -0.0853 | 0.9961 |
| balanced | predecessor | delay:none | 1280 | 0.5263 | 0.1755 | 0.0324 | -0.0168 | 0.9531 |
| balanced | predecessor | first_surface | 256 | 0.5820 | 0.1979 | 0.0250 | 0.0107 | 0.9492 |
| balanced | predecessor | natural | 1536 | 0.4704 | 0.1534 | 0.0690 | -0.0676 | 0.9635 |
| balanced | predecessor | novel_after_drilling | 256 | 0.5096 | 0.1684 | 0.0410 | -0.0175 | 0.9727 |
| balanced | predecessor | same_item | 1792 | 0.4887 | 0.1601 | 0.1435 | -0.1435 | 0.9810 |
| balanced | predecessor | singleton_all | 512 | 0.4845 | 0.1577 | 0.0901 | -0.0854 | 0.9707 |
| balanced | predecessor | singleton_first | 256 | 0.5239 | 0.1754 | 0.0785 | -0.0322 | 0.9414 |
| balanced | predecessor | unseen_sibling | 512 | 0.5079 | 0.1679 | 0.0449 | -0.0225 | 0.9512 |
| balanced | rho0.5-H3 | all_first_surfaces | 768 | 0.5246 | 0.1749 | 0.0316 | -0.0019 | 0.9596 |
| balanced | rho0.5-H3 | assigned | 1536 | 0.4788 | 0.1541 | 0.0262 | -0.0147 | 0.9844 |
| balanced | rho0.5-H3 | delay:1..7d | 512 | 0.4240 | 0.1322 | 0.0403 | -0.0034 | 1.0000 |
| balanced | rho0.5-H3 | delay:<=1d | 1024 | 0.3781 | 0.1133 | 0.0262 | -0.0189 | 1.0000 |
| balanced | rho0.5-H3 | delay:>7d | 256 | 0.5033 | 0.1647 | 0.0423 | -0.0057 | 1.0000 |
| balanced | rho0.5-H3 | delay:none | 1280 | 0.5111 | 0.1694 | 0.0319 | 0.0020 | 0.9656 |
| balanced | rho0.5-H3 | first_surface | 256 | 0.5722 | 0.1936 | 0.0399 | 0.0170 | 0.9609 |
| balanced | rho0.5-H3 | natural | 1536 | 0.4244 | 0.1342 | 0.0213 | 0.0017 | 0.9870 |
| balanced | rho0.5-H3 | novel_after_drilling | 256 | 0.4964 | 0.1627 | 0.0272 | -0.0032 | 0.9766 |
| balanced | rho0.5-H3 | same_item | 1792 | 0.4091 | 0.1261 | 0.0240 | -0.0126 | 1.0000 |
| balanced | rho0.5-H3 | singleton_all | 512 | 0.4423 | 0.1410 | 0.0308 | -0.0254 | 0.9707 |
| balanced | rho0.5-H3 | singleton_first | 256 | 0.5052 | 0.1684 | 0.0607 | -0.0195 | 0.9414 |
| balanced | rho0.5-H3 | unseen_sibling | 512 | 0.4909 | 0.1611 | 0.0346 | 0.0079 | 0.9746 |
| family_memory | predecessor | all_first_surfaces | 768 | 0.5485 | 0.1849 | 0.0336 | -0.0037 | 0.9635 |
| family_memory | predecessor | assigned | 1536 | 0.5853 | 0.2010 | 0.2260 | -0.2257 | 0.6602 |
| family_memory | predecessor | delay:1..7d | 512 | 0.5999 | 0.2066 | 0.2837 | -0.2742 | 0.5508 |
| family_memory | predecessor | delay:<=1d | 1024 | 0.4803 | 0.1575 | 0.2431 | -0.2431 | 0.4990 |
| family_memory | predecessor | delay:>7d | 256 | 0.7484 | 0.2603 | 0.2895 | -0.1825 | 0.6992 |
| family_memory | predecessor | delay:none | 1280 | 0.5471 | 0.1852 | 0.1081 | -0.1079 | 0.8836 |
| family_memory | predecessor | first_surface | 256 | 0.6033 | 0.2064 | 0.0329 | 0.0157 | 0.9609 |
| family_memory | predecessor | natural | 1536 | 0.5154 | 0.1705 | 0.1551 | -0.1481 | 0.7090 |
| family_memory | predecessor | novel_after_drilling | 256 | 0.5029 | 0.1658 | 0.0247 | -0.0068 | 0.9805 |
| family_memory | predecessor | same_item | 1792 | 0.5527 | 0.1862 | 0.2503 | -0.2433 | 0.5424 |
| family_memory | predecessor | singleton_all | 512 | 0.5116 | 0.1704 | 0.1189 | -0.1189 | 0.9395 |
| family_memory | predecessor | singleton_first | 256 | 0.5393 | 0.1824 | 0.0630 | -0.0201 | 0.9492 |
| family_memory | predecessor | unseen_sibling | 512 | 0.5450 | 0.1857 | 0.2642 | -0.2642 | 0.7637 |
| family_memory | rho0.5-H3 | all_first_surfaces | 768 | 0.5753 | 0.1941 | 0.0712 | 0.0598 | 0.9102 |
| family_memory | rho0.5-H3 | assigned | 1536 | 0.3673 | 0.1096 | 0.0531 | -0.0476 | 0.9629 |
| family_memory | rho0.5-H3 | delay:1..7d | 512 | 0.2538 | 0.0666 | 0.0513 | -0.0375 | 0.9824 |
| family_memory | rho0.5-H3 | delay:<=1d | 1024 | 0.2591 | 0.0681 | 0.0536 | -0.0536 | 0.9893 |
| family_memory | rho0.5-H3 | delay:>7d | 256 | 0.4046 | 0.1203 | 0.0824 | -0.0083 | 0.9688 |
| family_memory | rho0.5-H3 | delay:none | 1280 | 0.4758 | 0.1535 | 0.0236 | 0.0074 | 0.9359 |
| family_memory | rho0.5-H3 | first_surface | 256 | 0.6323 | 0.2148 | 0.0788 | 0.0629 | 0.9258 |
| family_memory | rho0.5-H3 | natural | 1536 | 0.3541 | 0.1059 | 0.0101 | 0.0041 | 0.9655 |
| family_memory | rho0.5-H3 | novel_after_drilling | 256 | 0.5423 | 0.1798 | 0.0710 | 0.0621 | 0.9219 |
| family_memory | rho0.5-H3 | same_item | 1792 | 0.2784 | 0.0751 | 0.0428 | -0.0425 | 0.9844 |
| family_memory | rho0.5-H3 | singleton_all | 512 | 0.4431 | 0.1420 | 0.0316 | -0.0068 | 0.9414 |
| family_memory | rho0.5-H3 | singleton_first | 256 | 0.5515 | 0.1877 | 0.0861 | 0.0545 | 0.8828 |
| family_memory | rho0.5-H3 | unseen_sibling | 512 | 0.3265 | 0.0925 | 0.0716 | -0.0713 | 0.9746 |
| independent | predecessor | all_first_surfaces | 768 | 0.5334 | 0.1771 | 0.0399 | -0.0066 | 0.9518 |
| independent | predecessor | assigned | 1536 | 0.5302 | 0.1762 | 0.1132 | -0.1129 | 0.9753 |
| independent | predecessor | delay:1..7d | 512 | 0.5325 | 0.1786 | 0.1537 | -0.1487 | 0.9922 |
| independent | predecessor | delay:<=1d | 1024 | 0.4514 | 0.1450 | 0.1587 | -0.1587 | 0.9785 |
| independent | predecessor | delay:>7d | 256 | 0.5214 | 0.1727 | 0.1264 | -0.1077 | 0.9961 |
| independent | predecessor | delay:none | 1280 | 0.5265 | 0.1749 | 0.0256 | -0.0164 | 0.9453 |
| independent | predecessor | first_surface | 256 | 0.5610 | 0.1885 | 0.0562 | 0.0079 | 0.9531 |
| independent | predecessor | natural | 1536 | 0.4739 | 0.1546 | 0.0741 | -0.0741 | 0.9616 |
| independent | predecessor | novel_after_drilling | 256 | 0.5382 | 0.1768 | 0.0654 | 0.0076 | 0.9570 |
| independent | predecessor | same_item | 1792 | 0.4846 | 0.1586 | 0.1485 | -0.1485 | 0.9849 |
| independent | predecessor | singleton_all | 512 | 0.4653 | 0.1495 | 0.0920 | -0.0880 | 0.9727 |
| independent | predecessor | singleton_first | 256 | 0.5009 | 0.1658 | 0.0426 | -0.0351 | 0.9453 |
| independent | predecessor | unseen_sibling | 512 | 0.5163 | 0.1717 | 0.0412 | -0.0312 | 0.9355 |
| independent | rho0.5-H3 | all_first_surfaces | 768 | 0.5209 | 0.1716 | 0.0390 | 0.0053 | 0.9479 |
| independent | rho0.5-H3 | assigned | 1536 | 0.4743 | 0.1524 | 0.0270 | -0.0131 | 0.9811 |
| independent | rho0.5-H3 | delay:1..7d | 512 | 0.4087 | 0.1267 | 0.0178 | -0.0033 | 0.9961 |
| independent | rho0.5-H3 | delay:<=1d | 1024 | 0.3756 | 0.1128 | 0.0238 | -0.0184 | 1.0000 |
| independent | rho0.5-H3 | delay:>7d | 256 | 0.4727 | 0.1536 | 0.0558 | -0.0278 | 0.9961 |
| independent | rho0.5-H3 | delay:none | 1280 | 0.5190 | 0.1718 | 0.0211 | 0.0034 | 0.9523 |
| independent | rho0.5-H3 | first_surface | 256 | 0.5453 | 0.1825 | 0.0614 | 0.0156 | 0.9609 |
| independent | rho0.5-H3 | natural | 1536 | 0.4236 | 0.1338 | 0.0153 | -0.0020 | 0.9772 |
| independent | rho0.5-H3 | novel_after_drilling | 256 | 0.5235 | 0.1694 | 0.0512 | 0.0229 | 0.9414 |
| independent | rho0.5-H3 | same_item | 1792 | 0.3989 | 0.1226 | 0.0180 | -0.0154 | 0.9983 |
| independent | rho0.5-H3 | singleton_all | 512 | 0.4363 | 0.1382 | 0.0455 | -0.0271 | 0.9707 |
| independent | rho0.5-H3 | singleton_first | 256 | 0.4937 | 0.1629 | 0.0531 | -0.0225 | 0.9414 |
| independent | rho0.5-H3 | unseen_sibling | 512 | 0.5161 | 0.1720 | 0.0423 | 0.0006 | 0.9590 |
| no_memory | predecessor | all_first_surfaces | 768 | 0.5385 | 0.1806 | 0.0382 | -0.0130 | 0.9544 |
| no_memory | predecessor | assigned | 1536 | 0.5415 | 0.1810 | 0.0566 | -0.0305 | 0.9642 |
| no_memory | predecessor | delay:1..7d | 512 | 0.5330 | 0.1788 | 0.0342 | -0.0149 | 0.9648 |
| no_memory | predecessor | delay:<=1d | 1024 | 0.4902 | 0.1612 | 0.0159 | -0.0085 | 0.9707 |
| no_memory | predecessor | delay:>7d | 256 | 0.5120 | 0.1680 | 0.1199 | -0.0149 | 0.9648 |
| no_memory | predecessor | delay:none | 1280 | 0.5263 | 0.1755 | 0.0324 | -0.0168 | 0.9531 |
| no_memory | predecessor | first_surface | 256 | 0.5820 | 0.1979 | 0.0250 | 0.0107 | 0.9492 |
| no_memory | predecessor | natural | 1536 | 0.4868 | 0.1603 | 0.0229 | 0.0034 | 0.9596 |
| no_memory | predecessor | novel_after_drilling | 256 | 0.5096 | 0.1684 | 0.0410 | -0.0175 | 0.9727 |
| no_memory | predecessor | same_item | 1792 | 0.5055 | 0.1672 | 0.0224 | -0.0112 | 0.9682 |
| no_memory | predecessor | singleton_all | 512 | 0.4915 | 0.1620 | 0.0459 | -0.0190 | 0.9629 |
| no_memory | predecessor | singleton_first | 256 | 0.5239 | 0.1754 | 0.0785 | -0.0322 | 0.9414 |
| no_memory | predecessor | unseen_sibling | 512 | 0.5079 | 0.1679 | 0.0449 | -0.0225 | 0.9512 |
| no_memory | rho0.5-H3 | all_first_surfaces | 768 | 0.5208 | 0.1738 | 0.0405 | -0.0207 | 0.9596 |
| no_memory | rho0.5-H3 | assigned | 1536 | 0.5172 | 0.1705 | 0.0333 | -0.0046 | 0.9674 |
| no_memory | rho0.5-H3 | delay:1..7d | 512 | 0.4740 | 0.1541 | 0.0736 | 0.0176 | 0.9609 |
| no_memory | rho0.5-H3 | delay:<=1d | 1024 | 0.4799 | 0.1563 | 0.0467 | 0.0324 | 0.9590 |
| no_memory | rho0.5-H3 | delay:>7d | 256 | 0.4776 | 0.1541 | 0.0408 | -0.0171 | 0.9844 |
| no_memory | rho0.5-H3 | delay:none | 1280 | 0.5044 | 0.1668 | 0.0351 | -0.0290 | 0.9695 |
| no_memory | rho0.5-H3 | first_surface | 256 | 0.5616 | 0.1903 | 0.0362 | 0.0011 | 0.9609 |
| no_memory | rho0.5-H3 | natural | 1536 | 0.4606 | 0.1497 | 0.0289 | 0.0051 | 0.9642 |
| no_memory | rho0.5-H3 | novel_after_drilling | 256 | 0.4980 | 0.1641 | 0.0761 | -0.0250 | 0.9570 |
| no_memory | rho0.5-H3 | same_item | 1792 | 0.4779 | 0.1553 | 0.0402 | 0.0211 | 0.9632 |
| no_memory | rho0.5-H3 | singleton_all | 512 | 0.4854 | 0.1601 | 0.0511 | -0.0010 | 0.9609 |
| no_memory | rho0.5-H3 | singleton_first | 256 | 0.5027 | 0.1672 | 0.0859 | -0.0381 | 0.9609 |
| no_memory | rho0.5-H3 | unseen_sibling | 512 | 0.4797 | 0.1562 | 0.0559 | -0.0416 | 0.9844 |
| shared | predecessor | all_first_surfaces | 768 | 0.5070 | 0.1692 | 0.0356 | -0.0236 | 0.9596 |
| shared | predecessor | assigned | 1536 | 0.5390 | 0.1813 | 0.1169 | -0.1136 | 0.9753 |
| shared | predecessor | delay:1..7d | 512 | 0.5216 | 0.1755 | 0.1432 | -0.1432 | 0.9844 |
| shared | predecessor | delay:<=1d | 1024 | 0.4649 | 0.1503 | 0.1613 | -0.1595 | 0.9717 |
| shared | predecessor | delay:>7d | 256 | 0.5639 | 0.1916 | 0.1488 | -0.1061 | 0.9961 |
| shared | predecessor | delay:none | 1280 | 0.5146 | 0.1719 | 0.0340 | -0.0182 | 0.9664 |
| shared | predecessor | first_surface | 256 | 0.5328 | 0.1802 | 0.0307 | -0.0071 | 0.9570 |
| shared | predecessor | natural | 1536 | 0.4677 | 0.1526 | 0.0742 | -0.0733 | 0.9720 |
| shared | predecessor | novel_after_drilling | 256 | 0.4623 | 0.1505 | 0.0552 | -0.0301 | 0.9727 |
| shared | predecessor | same_item | 1792 | 0.4952 | 0.1634 | 0.1472 | -0.1472 | 0.9788 |
| shared | predecessor | singleton_all | 512 | 0.4913 | 0.1609 | 0.0984 | -0.0865 | 0.9746 |
| shared | predecessor | singleton_first | 256 | 0.5258 | 0.1771 | 0.0636 | -0.0336 | 0.9492 |
| shared | predecessor | unseen_sibling | 512 | 0.5261 | 0.1759 | 0.0571 | -0.0102 | 0.9766 |
| shared | rho0.5-H3 | all_first_surfaces | 768 | 0.4952 | 0.1650 | 0.0171 | -0.0138 | 0.9453 |
| shared | rho0.5-H3 | assigned | 1536 | 0.4730 | 0.1526 | 0.0264 | -0.0143 | 0.9818 |
| shared | rho0.5-H3 | delay:1..7d | 512 | 0.4284 | 0.1345 | 0.0197 | 0.0045 | 1.0000 |
| shared | rho0.5-H3 | delay:<=1d | 1024 | 0.3799 | 0.1138 | 0.0293 | -0.0196 | 1.0000 |
| shared | rho0.5-H3 | delay:>7d | 256 | 0.4821 | 0.1571 | 0.0294 | -0.0227 | 1.0000 |
| shared | rho0.5-H3 | delay:none | 1280 | 0.5043 | 0.1679 | 0.0194 | -0.0012 | 0.9602 |
| shared | rho0.5-H3 | first_surface | 256 | 0.5351 | 0.1805 | 0.0322 | -0.0011 | 0.9492 |
| shared | rho0.5-H3 | natural | 1536 | 0.4237 | 0.1342 | 0.0228 | -0.0021 | 0.9850 |
| shared | rho0.5-H3 | novel_after_drilling | 256 | 0.4472 | 0.1461 | 0.0376 | -0.0177 | 0.9492 |
| shared | rho0.5-H3 | same_item | 1792 | 0.4084 | 0.1259 | 0.0186 | -0.0131 | 1.0000 |
| shared | rho0.5-H3 | singleton_all | 512 | 0.4425 | 0.1416 | 0.0322 | -0.0258 | 0.9688 |
| shared | rho0.5-H3 | singleton_first | 256 | 0.5033 | 0.1686 | 0.0476 | -0.0225 | 0.9375 |
| shared | rho0.5-H3 | unseen_sibling | 512 | 0.5180 | 0.1722 | 0.0393 | 0.0175 | 0.9824 |
| slow_retention | predecessor | all_first_surfaces | 768 | 0.4957 | 0.1636 | 0.0380 | -0.0337 | 0.9505 |
| slow_retention | predecessor | assigned | 1536 | 0.5323 | 0.1794 | 0.2207 | -0.2207 | 0.6133 |
| slow_retention | predecessor | delay:1..7d | 512 | 0.5407 | 0.1824 | 0.2580 | -0.2503 | 0.4941 |
| slow_retention | predecessor | delay:<=1d | 1024 | 0.4361 | 0.1386 | 0.2194 | -0.2193 | 0.4922 |
| slow_retention | predecessor | delay:>7d | 256 | 0.6222 | 0.2110 | 0.2501 | -0.1957 | 0.7031 |
| slow_retention | predecessor | delay:none | 1280 | 0.4824 | 0.1591 | 0.1250 | -0.1250 | 0.8430 |
| slow_retention | predecessor | first_surface | 256 | 0.5256 | 0.1761 | 0.0479 | -0.0176 | 0.9375 |
| slow_retention | predecessor | natural | 1536 | 0.4443 | 0.1416 | 0.1540 | -0.1457 | 0.6992 |
| slow_retention | predecessor | novel_after_drilling | 256 | 0.4434 | 0.1420 | 0.0719 | -0.0579 | 0.9727 |
| slow_retention | predecessor | same_item | 1792 | 0.4926 | 0.1615 | 0.2326 | -0.2248 | 0.5229 |
| slow_retention | predecessor | singleton_all | 512 | 0.4792 | 0.1557 | 0.1221 | -0.1179 | 0.9238 |
| slow_retention | predecessor | singleton_first | 256 | 0.5181 | 0.1727 | 0.0519 | -0.0256 | 0.9414 |
| slow_retention | predecessor | unseen_sibling | 512 | 0.4625 | 0.1523 | 0.2619 | -0.2619 | 0.6816 |
| slow_retention | rho0.5-H3 | all_first_surfaces | 768 | 0.5142 | 0.1688 | 0.0467 | 0.0336 | 0.8945 |
| slow_retention | rho0.5-H3 | assigned | 1536 | 0.3359 | 0.0976 | 0.0585 | -0.0576 | 0.9447 |
| slow_retention | rho0.5-H3 | delay:1..7d | 512 | 0.2417 | 0.0615 | 0.0535 | -0.0446 | 0.9297 |
| slow_retention | rho0.5-H3 | delay:<=1d | 1024 | 0.2466 | 0.0629 | 0.0553 | -0.0553 | 0.9766 |
| slow_retention | rho0.5-H3 | delay:>7d | 256 | 0.3297 | 0.0918 | 0.0787 | -0.0513 | 0.9375 |
| slow_retention | rho0.5-H3 | delay:none | 1280 | 0.4100 | 0.1281 | 0.0249 | -0.0138 | 0.9219 |
| slow_retention | rho0.5-H3 | first_surface | 256 | 0.5381 | 0.1802 | 0.0509 | 0.0308 | 0.9062 |
| slow_retention | rho0.5-H3 | natural | 1536 | 0.3057 | 0.0869 | 0.0231 | -0.0141 | 0.9408 |
| slow_retention | rho0.5-H3 | novel_after_drilling | 256 | 0.4456 | 0.1424 | 0.0227 | 0.0167 | 0.9062 |
| slow_retention | rho0.5-H3 | same_item | 1792 | 0.2571 | 0.0666 | 0.0526 | -0.0517 | 0.9576 |
| slow_retention | rho0.5-H3 | singleton_all | 512 | 0.4280 | 0.1319 | 0.0404 | -0.0131 | 0.9336 |
| slow_retention | rho0.5-H3 | singleton_first | 256 | 0.5590 | 0.1838 | 0.0732 | 0.0531 | 0.8711 |
| slow_retention | rho0.5-H3 | unseen_sibling | 512 | 0.2536 | 0.0671 | 0.0851 | -0.0847 | 0.9629 |

## Baseline strata

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Same predictions for both views; N=0 means unavailable (never imputed). Use same_item to compare FSRS against AD on the identical 1,792 outcomes per world.

| World | Baseline | Stratum | N | Loss | Brier | ECE | Bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | fsrs | same_item | 1792 | 0.4868 | 0.1383 | 0.0972 | 0.0972 |
| balanced | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| balanced | fsrs | singleton_all | 256 | 0.4293 | 0.1340 | 0.0863 | 0.0863 |
| balanced | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| balanced | fsrs | delay:<=1d | 1024 | 0.4704 | 0.1233 | 0.0970 | 0.0970 |
| balanced | fsrs | delay:1..7d | 512 | 0.4950 | 0.1499 | 0.1075 | 0.1075 |
| balanced | fsrs | delay:>7d | 256 | 0.5360 | 0.1751 | 0.0775 | 0.0775 |
| balanced | last | same_item | 1792 | 5.3427 | 0.2578 | 0.2578 | -0.0357 |
| balanced | last | unseen_sibling | 512 | 5.8689 | 0.2832 | 0.2832 | 0.0371 |
| balanced | last | singleton_all | 512 | 5.5046 | 0.2656 | 0.2656 | -0.0781 |
| balanced | last | novel_after_drilling | 256 | 6.0713 | 0.2930 | 0.2930 | 0.1211 |
| balanced | last | delay:<=1d | 1024 | 5.6058 | 0.2705 | 0.2705 | -0.0850 |
| balanced | last | delay:1..7d | 512 | 4.6546 | 0.2246 | 0.2246 | 0.0137 |
| balanced | last | delay:>7d | 256 | 5.6665 | 0.2734 | 0.2734 | 0.0625 |
| balanced | mastery_ekf | same_item | 1792 | 0.4437 | 0.1402 | 0.0711 | -0.0697 |
| balanced | mastery_ekf | unseen_sibling | 512 | 0.5339 | 0.1777 | 0.1003 | 0.1003 |
| balanced | mastery_ekf | singleton_all | 512 | 0.4597 | 0.1491 | 0.0266 | 0.0152 |
| balanced | mastery_ekf | novel_after_drilling | 256 | 0.5097 | 0.1677 | 0.0797 | 0.0749 |
| balanced | mastery_ekf | delay:<=1d | 1024 | 0.4352 | 0.1366 | 0.1157 | -0.1151 |
| balanced | mastery_ekf | delay:1..7d | 512 | 0.4317 | 0.1357 | 0.0399 | -0.0335 |
| balanced | mastery_ekf | delay:>7d | 256 | 0.5017 | 0.1633 | 0.0585 | 0.0394 |
| balanced | rate:.5 | same_item | 1792 | 0.4786 | 0.1553 | 0.1151 | -0.1149 |
| balanced | rate:.5 | unseen_sibling | 512 | 0.5193 | 0.1676 | 0.0540 | 0.0489 |
| balanced | rate:.5 | singleton_all | 512 | 0.4568 | 0.1481 | 0.0569 | -0.0364 |
| balanced | rate:.5 | novel_after_drilling | 256 | 0.4910 | 0.1591 | 0.0348 | 0.0211 |
| balanced | rate:.5 | delay:<=1d | 1024 | 0.4863 | 0.1581 | 0.1594 | -0.1594 |
| balanced | rate:.5 | delay:1..7d | 512 | 0.4439 | 0.1425 | 0.0798 | -0.0795 |
| balanced | rate:.5 | delay:>7d | 256 | 0.5174 | 0.1695 | 0.0529 | -0.0079 |
| balanced | rate:1 | same_item | 1792 | 0.4795 | 0.1553 | 0.1278 | -0.1277 |
| balanced | rate:1 | unseen_sibling | 512 | 0.5089 | 0.1660 | 0.0416 | 0.0374 |
| balanced | rate:1 | singleton_all | 512 | 0.4598 | 0.1485 | 0.0645 | -0.0458 |
| balanced | rate:1 | novel_after_drilling | 256 | 0.4891 | 0.1592 | 0.0438 | 0.0124 |
| balanced | rate:1 | delay:<=1d | 1024 | 0.4842 | 0.1571 | 0.1714 | -0.1712 |
| balanced | rate:1 | delay:1..7d | 512 | 0.4526 | 0.1449 | 0.0938 | -0.0938 |
| balanced | rate:1 | delay:>7d | 256 | 0.5143 | 0.1690 | 0.0585 | -0.0212 |
| balanced | rate:2 | same_item | 1792 | 0.4884 | 0.1581 | 0.1467 | -0.1467 |
| balanced | rate:2 | unseen_sibling | 512 | 0.5047 | 0.1652 | 0.0535 | 0.0187 |
| balanced | rate:2 | singleton_all | 512 | 0.4673 | 0.1502 | 0.0755 | -0.0616 |
| balanced | rate:2 | novel_after_drilling | 256 | 0.4917 | 0.1603 | 0.0538 | -0.0027 |
| balanced | rate:2 | delay:<=1d | 1024 | 0.4912 | 0.1592 | 0.1886 | -0.1886 |
| balanced | rate:2 | delay:1..7d | 512 | 0.4687 | 0.1500 | 0.1155 | -0.1153 |
| balanced | rate:2 | delay:>7d | 256 | 0.5163 | 0.1698 | 0.0493 | -0.0422 |
| family_memory | fsrs | same_item | 1792 | 0.2721 | 0.0707 | 0.0221 | 0.0221 |
| family_memory | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| family_memory | fsrs | singleton_all | 256 | 0.3139 | 0.0902 | 0.0180 | 0.0180 |
| family_memory | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| family_memory | fsrs | delay:<=1d | 1024 | 0.2520 | 0.0601 | 0.0224 | 0.0224 |
| family_memory | fsrs | delay:1..7d | 512 | 0.2450 | 0.0659 | 0.0183 | 0.0154 |
| family_memory | fsrs | delay:>7d | 256 | 0.4067 | 0.1224 | 0.0530 | 0.0343 |
| family_memory | last | same_item | 1792 | 3.5271 | 0.1702 | 0.1702 | -0.0631 |
| family_memory | last | unseen_sibling | 512 | 3.5618 | 0.1719 | 0.1719 | -0.0352 |
| family_memory | last | singleton_all | 512 | 6.6379 | 0.3203 | 0.3203 | 0.0039 |
| family_memory | last | novel_after_drilling | 256 | 6.4760 | 0.3125 | 0.3125 | 0.2109 |
| family_memory | last | delay:<=1d | 1024 | 4.5939 | 0.2217 | 0.2217 | -0.1396 |
| family_memory | last | delay:1..7d | 512 | 1.8214 | 0.0879 | 0.0879 | 0.0137 |
| family_memory | last | delay:>7d | 256 | 2.6714 | 0.1289 | 0.1289 | 0.0898 |
| family_memory | mastery_ekf | same_item | 1792 | 0.3543 | 0.1005 | 0.1028 | -0.0999 |
| family_memory | mastery_ekf | unseen_sibling | 512 | 0.3080 | 0.0844 | 0.0667 | -0.0638 |
| family_memory | mastery_ekf | singleton_all | 512 | 0.5250 | 0.1718 | 0.0816 | 0.0727 |
| family_memory | mastery_ekf | novel_after_drilling | 256 | 0.6687 | 0.2291 | 0.1749 | 0.1719 |
| family_memory | mastery_ekf | delay:<=1d | 1024 | 0.3412 | 0.0970 | 0.1327 | -0.1327 |
| family_memory | mastery_ekf | delay:1..7d | 512 | 0.3146 | 0.0850 | 0.0942 | -0.0908 |
| family_memory | mastery_ekf | delay:>7d | 256 | 0.4859 | 0.1452 | 0.0734 | 0.0129 |
| family_memory | rate:.5 | same_item | 1792 | 0.3706 | 0.1071 | 0.1121 | -0.1120 |
| family_memory | rate:.5 | unseen_sibling | 512 | 0.3230 | 0.0893 | 0.0756 | -0.0755 |
| family_memory | rate:.5 | singleton_all | 512 | 0.5183 | 0.1703 | 0.0761 | 0.0566 |
| family_memory | rate:.5 | novel_after_drilling | 256 | 0.6508 | 0.2232 | 0.1624 | 0.1540 |
| family_memory | rate:.5 | delay:<=1d | 1024 | 0.3663 | 0.1075 | 0.1469 | -0.1469 |
| family_memory | rate:.5 | delay:1..7d | 512 | 0.3158 | 0.0860 | 0.1035 | -0.1003 |
| family_memory | rate:.5 | delay:>7d | 256 | 0.4978 | 0.1476 | 0.0823 | 0.0043 |
| family_memory | rate:1 | same_item | 1792 | 0.3778 | 0.1094 | 0.1313 | -0.1297 |
| family_memory | rate:1 | unseen_sibling | 512 | 0.3297 | 0.0912 | 0.0942 | -0.0926 |
| family_memory | rate:1 | singleton_all | 512 | 0.5080 | 0.1677 | 0.0612 | 0.0417 |
| family_memory | rate:1 | novel_after_drilling | 256 | 0.6328 | 0.2190 | 0.1489 | 0.1405 |
| family_memory | rate:1 | delay:<=1d | 1024 | 0.3713 | 0.1085 | 0.1632 | -0.1632 |
| family_memory | rate:1 | delay:1..7d | 512 | 0.3330 | 0.0913 | 0.1236 | -0.1203 |
| family_memory | rate:1 | delay:>7d | 256 | 0.4934 | 0.1488 | 0.0967 | -0.0144 |
| family_memory | rate:2 | same_item | 1792 | 0.3959 | 0.1157 | 0.1570 | -0.1566 |
| family_memory | rate:2 | unseen_sibling | 512 | 0.3467 | 0.0962 | 0.1221 | -0.1205 |
| family_memory | rate:2 | singleton_all | 512 | 0.5009 | 0.1651 | 0.0537 | 0.0166 |
| family_memory | rate:2 | novel_after_drilling | 256 | 0.6133 | 0.2130 | 0.1255 | 0.1172 |
| family_memory | rate:2 | delay:<=1d | 1024 | 0.3881 | 0.1139 | 0.1877 | -0.1877 |
| family_memory | rate:2 | delay:1..7d | 512 | 0.3616 | 0.1012 | 0.1540 | -0.1505 |
| family_memory | rate:2 | delay:>7d | 256 | 0.4958 | 0.1523 | 0.1136 | -0.0440 |
| independent | fsrs | same_item | 1792 | 0.4707 | 0.1345 | 0.0935 | 0.0935 |
| independent | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| independent | fsrs | singleton_all | 256 | 0.4293 | 0.1340 | 0.0863 | 0.0863 |
| independent | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| independent | fsrs | delay:<=1d | 1024 | 0.4623 | 0.1224 | 0.0970 | 0.0970 |
| independent | fsrs | delay:1..7d | 512 | 0.4741 | 0.1450 | 0.1064 | 0.1064 |
| independent | fsrs | delay:>7d | 256 | 0.4977 | 0.1620 | 0.0725 | 0.0537 |
| independent | last | same_item | 1792 | 5.0999 | 0.2461 | 0.2461 | -0.0385 |
| independent | last | unseen_sibling | 512 | 6.2332 | 0.3008 | 0.3008 | 0.0430 |
| independent | last | singleton_all | 512 | 5.9094 | 0.2852 | 0.2852 | -0.0742 |
| independent | last | novel_after_drilling | 256 | 6.4760 | 0.3125 | 0.3125 | 0.1484 |
| independent | last | delay:<=1d | 1024 | 5.4844 | 0.2646 | 0.2646 | -0.0811 |
| independent | last | delay:1..7d | 512 | 4.2499 | 0.2051 | 0.2051 | 0.0098 |
| independent | last | delay:>7d | 256 | 5.2618 | 0.2539 | 0.2539 | 0.0352 |
| independent | mastery_ekf | same_item | 1792 | 0.4365 | 0.1379 | 0.0749 | -0.0747 |
| independent | mastery_ekf | unseen_sibling | 512 | 0.5395 | 0.1812 | 0.0948 | 0.0914 |
| independent | mastery_ekf | singleton_all | 512 | 0.4542 | 0.1465 | 0.0346 | 0.0128 |
| independent | mastery_ekf | novel_after_drilling | 256 | 0.5382 | 0.1777 | 0.1095 | 0.1003 |
| independent | mastery_ekf | delay:<=1d | 1024 | 0.4345 | 0.1369 | 0.1177 | -0.1177 |
| independent | mastery_ekf | delay:1..7d | 512 | 0.4255 | 0.1334 | 0.0455 | -0.0345 |
| independent | mastery_ekf | delay:>7d | 256 | 0.4663 | 0.1504 | 0.0436 | 0.0167 |
| independent | rate:.5 | same_item | 1792 | 0.4760 | 0.1544 | 0.1220 | -0.1220 |
| independent | rate:.5 | unseen_sibling | 512 | 0.5276 | 0.1736 | 0.0458 | 0.0399 |
| independent | rate:.5 | singleton_all | 512 | 0.4551 | 0.1465 | 0.0523 | -0.0390 |
| independent | rate:.5 | novel_after_drilling | 256 | 0.5087 | 0.1674 | 0.0623 | 0.0462 |
| independent | rate:.5 | delay:<=1d | 1024 | 0.4880 | 0.1593 | 0.1649 | -0.1649 |
| independent | rate:.5 | delay:1..7d | 512 | 0.4434 | 0.1426 | 0.0861 | -0.0816 |
| independent | rate:.5 | delay:>7d | 256 | 0.4932 | 0.1585 | 0.0748 | -0.0312 |
| independent | rate:1 | same_item | 1792 | 0.4763 | 0.1543 | 0.1340 | -0.1340 |
| independent | rate:1 | unseen_sibling | 512 | 0.5184 | 0.1717 | 0.0350 | 0.0287 |
| independent | rate:1 | singleton_all | 512 | 0.4578 | 0.1471 | 0.0557 | -0.0481 |
| independent | rate:1 | novel_after_drilling | 256 | 0.5093 | 0.1676 | 0.0572 | 0.0377 |
| independent | rate:1 | delay:<=1d | 1024 | 0.4849 | 0.1580 | 0.1757 | -0.1757 |
| independent | rate:1 | delay:1..7d | 512 | 0.4522 | 0.1449 | 0.0991 | -0.0954 |
| independent | rate:1 | delay:>7d | 256 | 0.4898 | 0.1583 | 0.0823 | -0.0442 |
| independent | rate:2 | same_item | 1792 | 0.4851 | 0.1570 | 0.1522 | -0.1522 |
| independent | rate:2 | unseen_sibling | 512 | 0.5141 | 0.1703 | 0.0299 | 0.0104 |
| independent | rate:2 | singleton_all | 512 | 0.4655 | 0.1492 | 0.0667 | -0.0636 |
| independent | rate:2 | novel_after_drilling | 256 | 0.5128 | 0.1686 | 0.0467 | 0.0229 |
| independent | rate:2 | delay:<=1d | 1024 | 0.4915 | 0.1599 | 0.1920 | -0.1920 |
| independent | rate:2 | delay:1..7d | 512 | 0.4685 | 0.1501 | 0.1186 | -0.1163 |
| independent | rate:2 | delay:>7d | 256 | 0.4928 | 0.1596 | 0.0689 | -0.0647 |
| no_memory | fsrs | same_item | 1792 | 0.7899 | 0.2242 | 0.2004 | 0.2004 |
| no_memory | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| no_memory | fsrs | singleton_all | 256 | 0.7448 | 0.2402 | 0.2191 | 0.2191 |
| no_memory | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| no_memory | fsrs | delay:<=1d | 1024 | 0.9279 | 0.2454 | 0.2358 | 0.2358 |
| no_memory | fsrs | delay:1..7d | 512 | 0.6427 | 0.2063 | 0.1893 | 0.1893 |
| no_memory | fsrs | delay:>7d | 256 | 0.5322 | 0.1758 | 0.0889 | 0.0808 |
| no_memory | last | same_item | 1792 | 5.3890 | 0.2600 | 0.2600 | -0.0067 |
| no_memory | last | unseen_sibling | 512 | 5.7070 | 0.2754 | 0.2754 | 0.0020 |
| no_memory | last | singleton_all | 512 | 5.4237 | 0.2617 | 0.2617 | -0.0117 |
| no_memory | last | novel_after_drilling | 256 | 6.7189 | 0.3242 | 0.3242 | -0.0117 |
| no_memory | last | delay:<=1d | 1024 | 5.3225 | 0.2568 | 0.2568 | -0.0186 |
| no_memory | last | delay:1..7d | 512 | 5.1808 | 0.2500 | 0.2500 | 0.0117 |
| no_memory | last | delay:>7d | 256 | 6.0713 | 0.2930 | 0.2930 | 0.0039 |
| no_memory | mastery_ekf | same_item | 1792 | 0.4831 | 0.1579 | 0.0177 | 0.0012 |
| no_memory | mastery_ekf | unseen_sibling | 512 | 0.4742 | 0.1531 | 0.0347 | 0.0295 |
| no_memory | mastery_ekf | singleton_all | 512 | 0.4743 | 0.1565 | 0.0476 | 0.0249 |
| no_memory | mastery_ekf | novel_after_drilling | 256 | 0.4791 | 0.1556 | 0.0470 | 0.0183 |
| no_memory | mastery_ekf | delay:<=1d | 1024 | 0.4819 | 0.1577 | 0.0328 | -0.0207 |
| no_memory | mastery_ekf | delay:1..7d | 512 | 0.4839 | 0.1585 | 0.0467 | 0.0279 |
| no_memory | mastery_ekf | delay:>7d | 256 | 0.4858 | 0.1579 | 0.0550 | 0.0351 |
| no_memory | rate:.5 | same_item | 1792 | 0.5087 | 0.1689 | 0.0753 | -0.0753 |
| no_memory | rate:.5 | unseen_sibling | 512 | 0.4909 | 0.1602 | 0.0876 | -0.0525 |
| no_memory | rate:.5 | singleton_all | 512 | 0.4934 | 0.1658 | 0.0714 | -0.0609 |
| no_memory | rate:.5 | novel_after_drilling | 256 | 0.4841 | 0.1569 | 0.0927 | -0.0706 |
| no_memory | rate:.5 | delay:<=1d | 1024 | 0.5269 | 0.1760 | 0.0964 | -0.0964 |
| no_memory | rate:.5 | delay:1..7d | 512 | 0.4786 | 0.1579 | 0.0612 | -0.0487 |
| no_memory | rate:.5 | delay:>7d | 256 | 0.4957 | 0.1627 | 0.0608 | -0.0435 |
| no_memory | rate:1 | same_item | 1792 | 0.5072 | 0.1686 | 0.0820 | -0.0818 |
| no_memory | rate:1 | unseen_sibling | 512 | 0.4888 | 0.1599 | 0.0793 | -0.0583 |
| no_memory | rate:1 | singleton_all | 512 | 0.4935 | 0.1652 | 0.0749 | -0.0660 |
| no_memory | rate:1 | novel_after_drilling | 256 | 0.4836 | 0.1574 | 0.0800 | -0.0753 |
| no_memory | rate:1 | delay:<=1d | 1024 | 0.5224 | 0.1748 | 0.1027 | -0.1027 |
| no_memory | rate:1 | delay:1..7d | 512 | 0.4825 | 0.1588 | 0.0684 | -0.0557 |
| no_memory | rate:1 | delay:>7d | 256 | 0.4962 | 0.1632 | 0.0628 | -0.0501 |
| no_memory | rate:2 | same_item | 1792 | 0.5136 | 0.1705 | 0.0935 | -0.0916 |
| no_memory | rate:2 | unseen_sibling | 512 | 0.4922 | 0.1608 | 0.0766 | -0.0679 |
| no_memory | rate:2 | singleton_all | 512 | 0.4974 | 0.1654 | 0.0895 | -0.0747 |
| no_memory | rate:2 | novel_after_drilling | 256 | 0.4880 | 0.1590 | 0.0960 | -0.0836 |
| no_memory | rate:2 | delay:<=1d | 1024 | 0.5262 | 0.1760 | 0.1134 | -0.1120 |
| no_memory | rate:2 | delay:1..7d | 512 | 0.4937 | 0.1621 | 0.0763 | -0.0664 |
| no_memory | rate:2 | delay:>7d | 256 | 0.5028 | 0.1654 | 0.0778 | -0.0606 |
| shared | fsrs | same_item | 1792 | 0.4861 | 0.1377 | 0.0968 | 0.0958 |
| shared | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| shared | fsrs | singleton_all | 256 | 0.4293 | 0.1340 | 0.0863 | 0.0863 |
| shared | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| shared | fsrs | delay:<=1d | 1024 | 0.4674 | 0.1220 | 0.0954 | 0.0954 |
| shared | fsrs | delay:1..7d | 512 | 0.5142 | 0.1563 | 0.1150 | 0.1150 |
| shared | fsrs | delay:>7d | 256 | 0.5048 | 0.1633 | 0.0744 | 0.0594 |
| shared | last | same_item | 1792 | 5.3080 | 0.2561 | 0.2561 | -0.0363 |
| shared | last | unseen_sibling | 512 | 5.8284 | 0.2812 | 0.2812 | 0.0586 |
| shared | last | singleton_all | 512 | 5.7475 | 0.2773 | 0.2773 | -0.0898 |
| shared | last | novel_after_drilling | 256 | 5.8284 | 0.2812 | 0.2812 | 0.1094 |
| shared | last | delay:<=1d | 1024 | 5.5249 | 0.2666 | 0.2666 | -0.0811 |
| shared | last | delay:1..7d | 512 | 4.8570 | 0.2344 | 0.2344 | 0.0156 |
| shared | last | delay:>7d | 256 | 5.3427 | 0.2578 | 0.2578 | 0.0391 |
| shared | mastery_ekf | same_item | 1792 | 0.4443 | 0.1408 | 0.0736 | -0.0736 |
| shared | mastery_ekf | unseen_sibling | 512 | 0.5664 | 0.1907 | 0.1133 | 0.1133 |
| shared | mastery_ekf | singleton_all | 512 | 0.4647 | 0.1506 | 0.0304 | 0.0131 |
| shared | mastery_ekf | novel_after_drilling | 256 | 0.4758 | 0.1577 | 0.0863 | 0.0615 |
| shared | mastery_ekf | delay:<=1d | 1024 | 0.4402 | 0.1390 | 0.1189 | -0.1189 |
| shared | mastery_ekf | delay:1..7d | 512 | 0.4320 | 0.1363 | 0.0355 | -0.0289 |
| shared | mastery_ekf | delay:>7d | 256 | 0.4850 | 0.1571 | 0.0605 | 0.0184 |
| shared | rate:.5 | same_item | 1792 | 0.4770 | 0.1550 | 0.1180 | -0.1178 |
| shared | rate:.5 | unseen_sibling | 512 | 0.5497 | 0.1806 | 0.0621 | 0.0621 |
| shared | rate:.5 | singleton_all | 512 | 0.4637 | 0.1512 | 0.0490 | -0.0371 |
| shared | rate:.5 | novel_after_drilling | 256 | 0.4563 | 0.1477 | 0.0687 | 0.0088 |
| shared | rate:.5 | delay:<=1d | 1024 | 0.4897 | 0.1598 | 0.1622 | -0.1614 |
| shared | rate:.5 | delay:1..7d | 512 | 0.4399 | 0.1411 | 0.0756 | -0.0746 |
| shared | rate:.5 | delay:>7d | 256 | 0.5005 | 0.1632 | 0.0387 | -0.0295 |
| shared | rate:1 | same_item | 1792 | 0.4782 | 0.1551 | 0.1305 | -0.1304 |
| shared | rate:1 | unseen_sibling | 512 | 0.5379 | 0.1787 | 0.0508 | 0.0508 |
| shared | rate:1 | singleton_all | 512 | 0.4659 | 0.1513 | 0.0575 | -0.0464 |
| shared | rate:1 | novel_after_drilling | 256 | 0.4564 | 0.1478 | 0.0801 | 0.0001 |
| shared | rate:1 | delay:<=1d | 1024 | 0.4876 | 0.1588 | 0.1734 | -0.1732 |
| shared | rate:1 | delay:1..7d | 512 | 0.4488 | 0.1434 | 0.0909 | -0.0887 |
| shared | rate:1 | delay:>7d | 256 | 0.4996 | 0.1635 | 0.0473 | -0.0425 |
| shared | rate:2 | same_item | 1792 | 0.4876 | 0.1580 | 0.1493 | -0.1493 |
| shared | rate:2 | unseen_sibling | 512 | 0.5315 | 0.1773 | 0.0490 | 0.0322 |
| shared | rate:2 | singleton_all | 512 | 0.4723 | 0.1525 | 0.0696 | -0.0622 |
| shared | rate:2 | novel_after_drilling | 256 | 0.4618 | 0.1490 | 0.0895 | -0.0149 |
| shared | rate:2 | delay:<=1d | 1024 | 0.4945 | 0.1608 | 0.1906 | -0.1906 |
| shared | rate:2 | delay:1..7d | 512 | 0.4652 | 0.1486 | 0.1119 | -0.1099 |
| shared | rate:2 | delay:>7d | 256 | 0.5051 | 0.1655 | 0.0641 | -0.0630 |
| slow_retention | fsrs | same_item | 1792 | 0.2466 | 0.0610 | 0.0145 | 0.0121 |
| slow_retention | fsrs | unseen_sibling | 0 | N/A | N/A | N/A | N/A |
| slow_retention | fsrs | singleton_all | 256 | 0.2639 | 0.0718 | 0.0034 | -0.0017 |
| slow_retention | fsrs | novel_after_drilling | 0 | N/A | N/A | N/A | N/A |
| slow_retention | fsrs | delay:<=1d | 1024 | 0.2381 | 0.0546 | 0.0209 | 0.0182 |
| slow_retention | fsrs | delay:1..7d | 512 | 0.2302 | 0.0597 | 0.0092 | 0.0092 |
| slow_retention | fsrs | delay:>7d | 256 | 0.3135 | 0.0891 | 0.0462 | -0.0064 |
| slow_retention | last | same_item | 1792 | 3.1918 | 0.1540 | 0.1540 | -0.0592 |
| slow_retention | last | unseen_sibling | 512 | 2.6309 | 0.1270 | 0.1270 | -0.0254 |
| slow_retention | last | singleton_all | 512 | 5.9903 | 0.2891 | 0.2891 | 0.0039 |
| slow_retention | last | novel_after_drilling | 256 | 4.6142 | 0.2227 | 0.2227 | 0.1523 |
| slow_retention | last | delay:<=1d | 1024 | 4.1892 | 0.2021 | 0.2021 | -0.1221 |
| slow_retention | last | delay:1..7d | 512 | 1.8214 | 0.0879 | 0.0879 | 0.0098 |
| slow_retention | last | delay:>7d | 256 | 1.9428 | 0.0938 | 0.0938 | 0.0547 |
| slow_retention | mastery_ekf | same_item | 1792 | 0.3205 | 0.0880 | 0.0987 | -0.0987 |
| slow_retention | mastery_ekf | unseen_sibling | 512 | 0.2401 | 0.0597 | 0.0817 | -0.0806 |
| slow_retention | mastery_ekf | singleton_all | 512 | 0.4816 | 0.1524 | 0.0747 | 0.0558 |
| slow_retention | mastery_ekf | novel_after_drilling | 256 | 0.5204 | 0.1724 | 0.1062 | 0.1035 |
| slow_retention | mastery_ekf | delay:<=1d | 1024 | 0.3194 | 0.0886 | 0.1241 | -0.1241 |
| slow_retention | mastery_ekf | delay:1..7d | 512 | 0.2946 | 0.0772 | 0.0883 | -0.0868 |
| slow_retention | mastery_ekf | delay:>7d | 256 | 0.3767 | 0.1076 | 0.0499 | -0.0209 |
| slow_retention | rate:.5 | same_item | 1792 | 0.3376 | 0.0949 | 0.1101 | -0.1087 |
| slow_retention | rate:.5 | unseen_sibling | 512 | 0.2513 | 0.0640 | 0.0893 | -0.0893 |
| slow_retention | rate:.5 | singleton_all | 512 | 0.4823 | 0.1523 | 0.0627 | 0.0426 |
| slow_retention | rate:.5 | novel_after_drilling | 256 | 0.5044 | 0.1686 | 0.0975 | 0.0885 |
| slow_retention | rate:.5 | delay:<=1d | 1024 | 0.3461 | 0.0992 | 0.1459 | -0.1367 |
| slow_retention | rate:.5 | delay:1..7d | 512 | 0.2951 | 0.0783 | 0.0971 | -0.0939 |
| slow_retention | rate:.5 | delay:>7d | 256 | 0.3891 | 0.1107 | 0.0667 | -0.0267 |
| slow_retention | rate:1 | same_item | 1792 | 0.3457 | 0.0973 | 0.1315 | -0.1271 |
| slow_retention | rate:1 | unseen_sibling | 512 | 0.2624 | 0.0665 | 0.1085 | -0.1069 |
| slow_retention | rate:1 | singleton_all | 512 | 0.4711 | 0.1502 | 0.0488 | 0.0271 |
| slow_retention | rate:1 | novel_after_drilling | 256 | 0.4964 | 0.1661 | 0.0905 | 0.0743 |
| slow_retention | rate:1 | delay:<=1d | 1024 | 0.3504 | 0.1002 | 0.1564 | -0.1536 |
| slow_retention | rate:1 | delay:1..7d | 512 | 0.3124 | 0.0836 | 0.1178 | -0.1145 |
| slow_retention | rate:1 | delay:>7d | 256 | 0.3935 | 0.1130 | 0.0933 | -0.0460 |
| slow_retention | rate:2 | same_item | 1792 | 0.3654 | 0.1039 | 0.1550 | -0.1550 |
| slow_retention | rate:2 | unseen_sibling | 512 | 0.2856 | 0.0727 | 0.1375 | -0.1358 |
| slow_retention | rate:2 | singleton_all | 512 | 0.4647 | 0.1484 | 0.0292 | 0.0008 |
| slow_retention | rate:2 | novel_after_drilling | 256 | 0.4907 | 0.1632 | 0.0732 | 0.0498 |
| slow_retention | rate:2 | delay:<=1d | 1024 | 0.3671 | 0.1055 | 0.1793 | -0.1793 |
| slow_retention | rate:2 | delay:1..7d | 512 | 0.3414 | 0.0934 | 0.1492 | -0.1457 |
| slow_retention | rate:2 | delay:>7d | 256 | 0.4067 | 0.1184 | 0.1020 | -0.0765 |

## Recovery and identifiability

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each row: 64 posterior estimates, after 12 or 48 events/learner (768 or 3,072 training observations/world). Reference R3/H3 subject and rho=.5/H3 LO only. Family/item are the first anchor's stable effects. Variance ratios use the original prior, not a drift-adjusted prior; ability's denominator is the initial 3 (later gamma uncertainty is retained in its numerator).

| World | View | After | Quantity | RMSE | Bias | 95% coverage | Posterior/prior variance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | subject | 12 | ability | 1.1447 | 0.0636 | 0.9219 | 0.3957 |
| balanced | subject | 12 | family | 0.6164 | 0.0136 | 1.0000 | 1.4272 |
| balanced | subject | 12 | item | 0.7344 | 0.0102 | 0.9688 | 1.4252 |
| balanced | subject | 12 | memory_item | 0.1996 | 0.0742 | 1.0000 | 0.6918 |
| balanced | subject | 12 | memory_family | 0.2466 | 0.0349 | 1.0000 | 0.5541 |
| balanced | subject | 48 | ability | 1.0813 | 0.0097 | 0.9688 | 0.3908 |
| balanced | subject | 48 | family | 0.5979 | -0.0035 | 1.0000 | 1.2983 |
| balanced | subject | 48 | item | 0.7194 | 0.0040 | 0.9844 | 1.3733 |
| balanced | subject | 48 | memory_item | 0.1979 | 0.0682 | 1.0000 | 0.5094 |
| balanced | subject | 48 | memory_family | 0.2369 | 0.0577 | 0.9688 | 0.3435 |
| balanced | lo | 12 | ability | 1.1444 | 0.0632 | 0.9219 | 0.3957 |
| balanced | lo | 12 | family | 0.6116 | 0.0166 | 1.0000 | 1.4406 |
| balanced | lo | 12 | item | 0.7340 | 0.0086 | 0.9531 | 1.4147 |
| balanced | lo | 12 | memory_item | 0.1994 | 0.0741 | 1.0000 | 0.6919 |
| balanced | lo | 12 | memory_family | 0.2470 | 0.0349 | 1.0000 | 0.5536 |
| balanced | lo | 48 | ability | 1.0812 | 0.0107 | 0.9688 | 0.3909 |
| balanced | lo | 48 | family | 0.5948 | -0.0007 | 1.0000 | 1.3355 |
| balanced | lo | 48 | item | 0.7186 | -0.0005 | 0.9688 | 1.3780 |
| balanced | lo | 48 | memory_item | 0.1979 | 0.0684 | 1.0000 | 0.5097 |
| balanced | lo | 48 | memory_family | 0.2368 | 0.0575 | 0.9688 | 0.3436 |
| family_memory | subject | 12 | ability | 1.4298 | 0.3786 | 0.9062 | 0.4134 |
| family_memory | subject | 12 | family | 0.6730 | 0.1853 | 0.9844 | 1.4728 |
| family_memory | subject | 12 | item | 0.7641 | 0.0204 | 0.9844 | 1.4420 |
| family_memory | subject | 12 | memory_item | 0.4253 | -0.3826 | 0.9688 | 0.7332 |
| family_memory | subject | 12 | memory_family | 0.3354 | -0.2247 | 0.9375 | 0.5829 |
| family_memory | subject | 48 | ability | 1.4785 | 0.0176 | 0.8750 | 0.4021 |
| family_memory | subject | 48 | family | 0.7153 | 0.1104 | 0.9844 | 1.3888 |
| family_memory | subject | 48 | item | 0.7532 | -0.0076 | 0.9844 | 1.4158 |
| family_memory | subject | 48 | memory_item | 0.4220 | -0.3306 | 0.9531 | 0.5864 |
| family_memory | subject | 48 | memory_family | 0.2584 | -0.0870 | 0.9688 | 0.3962 |
| family_memory | lo | 12 | ability | 1.4287 | 0.3797 | 0.9062 | 0.4134 |
| family_memory | lo | 12 | family | 0.6751 | 0.1837 | 0.9844 | 1.4649 |
| family_memory | lo | 12 | item | 0.7629 | 0.0209 | 0.9688 | 1.4404 |
| family_memory | lo | 12 | memory_item | 0.4257 | -0.3827 | 0.9688 | 0.7332 |
| family_memory | lo | 12 | memory_family | 0.3346 | -0.2240 | 0.9375 | 0.5817 |
| family_memory | lo | 48 | ability | 1.4782 | 0.0180 | 0.8750 | 0.4019 |
| family_memory | lo | 48 | family | 0.7143 | 0.1092 | 0.9844 | 1.3940 |
| family_memory | lo | 48 | item | 0.7572 | -0.0076 | 0.9844 | 1.4155 |
| family_memory | lo | 48 | memory_item | 0.4223 | -0.3310 | 0.9531 | 0.5863 |
| family_memory | lo | 48 | memory_family | 0.2588 | -0.0867 | 0.9688 | 0.3961 |
| independent | subject | 12 | ability | 1.1298 | 0.0172 | 0.9375 | 0.3919 |
| independent | subject | 12 | family | 0.2717 | -0.0090 | 1.0000 | 1.4126 |
| independent | subject | 12 | item | 0.9686 | -0.0172 | 0.8906 | 1.4255 |
| independent | subject | 12 | memory_item | 0.2145 | 0.0874 | 1.0000 | 0.6819 |
| independent | subject | 12 | memory_family | 0.2442 | 0.0256 | 1.0000 | 0.5652 |
| independent | subject | 48 | ability | 1.1040 | 0.0290 | 0.9688 | 0.3965 |
| independent | subject | 48 | family | 0.3134 | -0.0271 | 1.0000 | 1.2896 |
| independent | subject | 48 | item | 0.9442 | -0.0217 | 0.8906 | 1.3854 |
| independent | subject | 48 | memory_item | 0.2059 | 0.0531 | 0.9844 | 0.5062 |
| independent | subject | 48 | memory_family | 0.2213 | 0.0450 | 0.9688 | 0.3520 |
| independent | lo | 12 | ability | 1.1300 | 0.0172 | 0.9375 | 0.3920 |
| independent | lo | 12 | family | 0.2742 | -0.0091 | 1.0000 | 1.4392 |
| independent | lo | 12 | item | 0.9662 | -0.0169 | 0.8906 | 1.4169 |
| independent | lo | 12 | memory_item | 0.2143 | 0.0873 | 1.0000 | 0.6818 |
| independent | lo | 12 | memory_family | 0.2445 | 0.0258 | 1.0000 | 0.5651 |
| independent | lo | 48 | ability | 1.1029 | 0.0298 | 0.9688 | 0.3967 |
| independent | lo | 48 | family | 0.3188 | -0.0271 | 1.0000 | 1.3358 |
| independent | lo | 48 | item | 0.9469 | -0.0237 | 0.8906 | 1.3809 |
| independent | lo | 48 | memory_item | 0.2060 | 0.0533 | 0.9844 | 0.5063 |
| independent | lo | 48 | memory_family | 0.2213 | 0.0444 | 0.9688 | 0.3523 |
| no_memory | subject | 12 | ability | 1.0965 | -0.1630 | 0.9375 | 0.3783 |
| no_memory | subject | 12 | family | 0.6176 | 0.0088 | 1.0000 | 1.4034 |
| no_memory | subject | 12 | item | 0.6736 | -0.0823 | 0.9844 | 1.4111 |
| no_memory | subject | 12 | memory_item | 0.4285 | 0.3577 | 0.9844 | 0.6706 |
| no_memory | subject | 12 | memory_family | 0.2686 | -0.0126 | 1.0000 | 0.5808 |
| no_memory | subject | 48 | ability | 0.9873 | -0.0648 | 1.0000 | 0.3776 |
| no_memory | subject | 48 | family | 0.5994 | -0.0086 | 1.0000 | 1.2943 |
| no_memory | subject | 48 | item | 0.6756 | -0.0648 | 0.9844 | 1.3585 |
| no_memory | subject | 48 | memory_item | 0.3800 | 0.2703 | 0.9531 | 0.4715 |
| no_memory | subject | 48 | memory_family | 0.2293 | 0.0106 | 0.9688 | 0.3541 |
| no_memory | lo | 12 | ability | 1.0965 | -0.1628 | 0.9375 | 0.3786 |
| no_memory | lo | 12 | family | 0.6138 | 0.0110 | 1.0000 | 1.4209 |
| no_memory | lo | 12 | item | 0.6759 | -0.0847 | 0.9688 | 1.4029 |
| no_memory | lo | 12 | memory_item | 0.4285 | 0.3578 | 0.9844 | 0.6703 |
| no_memory | lo | 12 | memory_family | 0.2688 | -0.0126 | 1.0000 | 0.5803 |
| no_memory | lo | 48 | ability | 0.9880 | -0.0639 | 1.0000 | 0.3775 |
| no_memory | lo | 48 | family | 0.6001 | -0.0045 | 1.0000 | 1.3121 |
| no_memory | lo | 48 | item | 0.6747 | -0.0747 | 0.9844 | 1.3625 |
| no_memory | lo | 48 | memory_item | 0.3797 | 0.2710 | 0.9531 | 0.4717 |
| no_memory | lo | 48 | memory_family | 0.2294 | 0.0097 | 0.9844 | 0.3542 |
| shared | subject | 12 | ability | 1.1296 | 0.0328 | 0.9375 | 0.3989 |
| shared | subject | 12 | family | 0.8398 | 0.0124 | 0.9531 | 1.4375 |
| shared | subject | 12 | item | 0.3672 | 0.0415 | 1.0000 | 1.4465 |
| shared | subject | 12 | memory_item | 0.1973 | 0.0631 | 1.0000 | 0.6932 |
| shared | subject | 12 | memory_family | 0.2581 | 0.0423 | 1.0000 | 0.5593 |
| shared | subject | 48 | ability | 1.1874 | 0.0842 | 0.8906 | 0.4014 |
| shared | subject | 48 | family | 0.8190 | 0.0232 | 0.9531 | 1.3324 |
| shared | subject | 48 | item | 0.3697 | 0.0230 | 1.0000 | 1.3801 |
| shared | subject | 48 | memory_item | 0.2075 | 0.0656 | 1.0000 | 0.5060 |
| shared | subject | 48 | memory_family | 0.2295 | 0.0118 | 0.9688 | 0.3379 |
| shared | lo | 12 | ability | 1.1285 | 0.0323 | 0.9375 | 0.3989 |
| shared | lo | 12 | family | 0.8315 | 0.0163 | 0.9531 | 1.4420 |
| shared | lo | 12 | item | 0.3598 | 0.0390 | 1.0000 | 1.4169 |
| shared | lo | 12 | memory_item | 0.1973 | 0.0630 | 1.0000 | 0.6930 |
| shared | lo | 12 | memory_family | 0.2587 | 0.0422 | 1.0000 | 0.5586 |
| shared | lo | 48 | ability | 1.1865 | 0.0828 | 0.8906 | 0.4008 |
| shared | lo | 48 | family | 0.8149 | 0.0205 | 0.9688 | 1.3365 |
| shared | lo | 48 | item | 0.3697 | 0.0247 | 1.0000 | 1.3806 |
| shared | lo | 48 | memory_item | 0.2076 | 0.0654 | 1.0000 | 0.5064 |
| shared | lo | 48 | memory_family | 0.2301 | 0.0127 | 0.9688 | 0.3373 |
| slow_retention | subject | 12 | ability | 1.5391 | 0.5482 | 0.8594 | 0.4131 |
| slow_retention | subject | 12 | family | 0.6701 | 0.1773 | 0.9844 | 1.4733 |
| slow_retention | subject | 12 | item | 0.7752 | 0.0035 | 0.9844 | 1.4354 |
| slow_retention | subject | 12 | memory_item | 0.4308 | -0.3896 | 0.9844 | 0.7354 |
| slow_retention | subject | 12 | memory_family | 0.3232 | -0.2315 | 0.9531 | 0.5806 |
| slow_retention | subject | 48 | ability | 1.8588 | 0.8087 | 0.7031 | 0.4448 |
| slow_retention | subject | 48 | family | 0.7016 | 0.0634 | 0.9844 | 1.3990 |
| slow_retention | subject | 48 | item | 0.7648 | -0.0499 | 0.9844 | 1.4058 |
| slow_retention | subject | 48 | memory_item | 0.4555 | -0.3808 | 0.9688 | 0.5950 |
| slow_retention | subject | 48 | memory_family | 0.2968 | -0.1422 | 0.9688 | 0.4129 |
| slow_retention | lo | 12 | ability | 1.5381 | 0.5492 | 0.8594 | 0.4132 |
| slow_retention | lo | 12 | family | 0.6726 | 0.1761 | 0.9844 | 1.4665 |
| slow_retention | lo | 12 | item | 0.7736 | 0.0051 | 0.9688 | 1.4419 |
| slow_retention | lo | 12 | memory_item | 0.4312 | -0.3898 | 0.9844 | 0.7355 |
| slow_retention | lo | 12 | memory_family | 0.3224 | -0.2309 | 0.9531 | 0.5792 |
| slow_retention | lo | 48 | ability | 1.8593 | 0.8104 | 0.7031 | 0.4446 |
| slow_retention | lo | 48 | family | 0.6980 | 0.0616 | 0.9844 | 1.4013 |
| slow_retention | lo | 48 | item | 0.7691 | -0.0499 | 0.9844 | 1.4191 |
| slow_retention | lo | 48 | memory_item | 0.4555 | -0.3810 | 0.9688 | 0.5950 |
| slow_retention | lo | 48 | memory_family | 0.2969 | -0.1418 | 0.9688 | 0.4126 |

## Warmth curve recovery

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each row: 64 estimates after 48 events/learner (3,072/world). Pointwise curve recovery is reported instead of asserting that correlated basis coefficients were separately identified.

| World | View | Ladder | Gap | RMSE | Bias | 95% coverage | Variance ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | subject | H1 | warmth@0.375h | 0.0654 | 0.0189 | 1.0000 | 0.9765 |
| balanced | subject | H1 | warmth@0h | 0.0696 | 0.0201 | 1.0000 | 0.9765 |
| balanced | subject | H1 | warmth@1.5h | 0.0542 | 0.0156 | 1.0000 | 0.9765 |
| balanced | subject | H1 | warmth@24h | 0.0013 | 0.0004 | 1.0000 | 0.9765 |
| balanced | subject | H1 | warmth@6h | 0.0256 | 0.0074 | 1.0000 | 0.9765 |
| balanced | subject | H1 | warmth@96h | 7.829e-09 | 2.259e-09 | 1.0000 | 0.9765 |
| balanced | subject | H3 | warmth@0.375h | 0.1635 | 0.0518 | 1.0000 | 0.9404 |
| balanced | subject | H3 | warmth@0h | 0.1738 | 0.0565 | 1.0000 | 0.9443 |
| balanced | subject | H3 | warmth@1.5h | 0.1408 | 0.0416 | 1.0000 | 0.9345 |
| balanced | subject | H3 | warmth@24h | 0.0379 | 0.0085 | 1.0000 | 0.9471 |
| balanced | subject | H3 | warmth@6h | 0.0961 | 0.0248 | 1.0000 | 0.9356 |
| balanced | subject | H3 | warmth@96h | 0.0018 | 0.0004 | 1.0000 | 0.9494 |
| balanced | subject | H5 | warmth@0.375h | 0.2572 | 0.0744 | 1.0000 | 0.8975 |
| balanced | subject | H5 | warmth@0h | 0.2652 | 0.0806 | 1.0000 | 0.9202 |
| balanced | subject | H5 | warmth@1.5h | 0.2411 | 0.0633 | 1.0000 | 0.8804 |
| balanced | subject | H5 | warmth@24h | 0.1411 | 0.0252 | 1.0000 | 0.8760 |
| balanced | subject | H5 | warmth@6h | 0.2059 | 0.0453 | 1.0000 | 0.8697 |
| balanced | subject | H5 | warmth@96h | 0.0544 | 0.0082 | 1.0000 | 0.9053 |
| balanced | lo | H1 | warmth@0.375h | 0.0653 | 0.0189 | 1.0000 | 0.9765 |
| balanced | lo | H1 | warmth@0h | 0.0695 | 0.0201 | 1.0000 | 0.9765 |
| balanced | lo | H1 | warmth@1.5h | 0.0541 | 0.0157 | 1.0000 | 0.9765 |
| balanced | lo | H1 | warmth@24h | 0.0013 | 0.0004 | 1.0000 | 0.9765 |
| balanced | lo | H1 | warmth@6h | 0.0256 | 0.0074 | 1.0000 | 0.9765 |
| balanced | lo | H1 | warmth@96h | 7.819e-09 | 2.265e-09 | 1.0000 | 0.9765 |
| balanced | lo | H3 | warmth@0.375h | 0.1634 | 0.0519 | 1.0000 | 0.9404 |
| balanced | lo | H3 | warmth@0h | 0.1737 | 0.0566 | 1.0000 | 0.9443 |
| balanced | lo | H3 | warmth@1.5h | 0.1407 | 0.0418 | 1.0000 | 0.9345 |
| balanced | lo | H3 | warmth@24h | 0.0379 | 0.0085 | 1.0000 | 0.9471 |
| balanced | lo | H3 | warmth@6h | 0.0961 | 0.0249 | 1.0000 | 0.9356 |
| balanced | lo | H3 | warmth@96h | 0.0018 | 0.0004 | 1.0000 | 0.9494 |
| balanced | lo | H5 | warmth@0.375h | 0.2572 | 0.0747 | 1.0000 | 0.8975 |
| balanced | lo | H5 | warmth@0h | 0.2653 | 0.0808 | 1.0000 | 0.9203 |
| balanced | lo | H5 | warmth@1.5h | 0.2411 | 0.0635 | 1.0000 | 0.8804 |
| balanced | lo | H5 | warmth@24h | 0.1411 | 0.0253 | 1.0000 | 0.8760 |
| balanced | lo | H5 | warmth@6h | 0.2060 | 0.0454 | 1.0000 | 0.8697 |
| balanced | lo | H5 | warmth@96h | 0.0544 | 0.0083 | 1.0000 | 0.9053 |
| family_memory | subject | H1 | warmth@0.375h | 0.1085 | 0.1037 | 1.0000 | 0.9852 |
| family_memory | subject | H1 | warmth@0h | 0.0342 | 0.0009 | 1.0000 | 0.9852 |
| family_memory | subject | H1 | warmth@1.5h | 0.2877 | 0.2865 | 1.0000 | 0.9852 |
| family_memory | subject | H1 | warmth@24h | 0.1840 | 0.1840 | 0.0000 | 0.9852 |
| family_memory | subject | H1 | warmth@6h | 0.3808 | 0.3806 | 0.0469 | 0.9852 |
| family_memory | subject | H1 | warmth@96h | 0.0092 | 0.0092 | 0.0000 | 0.9852 |
| family_memory | subject | H3 | warmth@0.375h | 0.1612 | 0.1132 | 1.0000 | 0.9605 |
| family_memory | subject | H3 | warmth@0h | 0.1198 | 0.0107 | 1.0000 | 0.9633 |
| family_memory | subject | H3 | warmth@1.5h | 0.3130 | 0.2952 | 1.0000 | 0.9564 |
| family_memory | subject | H3 | warmth@24h | 0.1901 | 0.1871 | 1.0000 | 0.9633 |
| family_memory | subject | H3 | warmth@6h | 0.3953 | 0.3875 | 1.0000 | 0.9564 |
| family_memory | subject | H3 | warmth@96h | 0.0095 | 0.0093 | 1.0000 | 0.9648 |
| family_memory | subject | H5 | warmth@0.375h | 0.2774 | 0.1381 | 1.0000 | 0.9237 |
| family_memory | subject | H5 | warmth@0h | 0.2472 | 0.0358 | 1.0000 | 0.9410 |
| family_memory | subject | H5 | warmth@1.5h | 0.3944 | 0.3197 | 1.0000 | 0.9096 |
| family_memory | subject | H5 | warmth@24h | 0.2508 | 0.2062 | 1.0000 | 0.9005 |
| family_memory | subject | H5 | warmth@6h | 0.4586 | 0.4107 | 1.0000 | 0.8988 |
| family_memory | subject | H5 | warmth@96h | 0.0579 | 0.0183 | 1.0000 | 0.9222 |
| family_memory | lo | H1 | warmth@0.375h | 0.1085 | 0.1037 | 1.0000 | 0.9852 |
| family_memory | lo | H1 | warmth@0h | 0.0341 | 0.0009 | 1.0000 | 0.9852 |
| family_memory | lo | H1 | warmth@1.5h | 0.2877 | 0.2865 | 1.0000 | 0.9852 |
| family_memory | lo | H1 | warmth@24h | 0.1840 | 0.1840 | 0.0000 | 0.9852 |
| family_memory | lo | H1 | warmth@6h | 0.3808 | 0.3806 | 0.0469 | 0.9852 |
| family_memory | lo | H1 | warmth@96h | 0.0092 | 0.0092 | 0.0000 | 0.9852 |
| family_memory | lo | H3 | warmth@0.375h | 0.1611 | 0.1131 | 1.0000 | 0.9605 |
| family_memory | lo | H3 | warmth@0h | 0.1197 | 0.0106 | 1.0000 | 0.9633 |
| family_memory | lo | H3 | warmth@1.5h | 0.3130 | 0.2952 | 1.0000 | 0.9564 |
| family_memory | lo | H3 | warmth@24h | 0.1901 | 0.1871 | 1.0000 | 0.9633 |
| family_memory | lo | H3 | warmth@6h | 0.3953 | 0.3875 | 1.0000 | 0.9564 |
| family_memory | lo | H3 | warmth@96h | 0.0095 | 0.0093 | 1.0000 | 0.9648 |
| family_memory | lo | H5 | warmth@0.375h | 0.2774 | 0.1381 | 1.0000 | 0.9237 |
| family_memory | lo | H5 | warmth@0h | 0.2473 | 0.0358 | 1.0000 | 0.9410 |
| family_memory | lo | H5 | warmth@1.5h | 0.3944 | 0.3197 | 1.0000 | 0.9096 |
| family_memory | lo | H5 | warmth@24h | 0.2509 | 0.2062 | 1.0000 | 0.9004 |
| family_memory | lo | H5 | warmth@6h | 0.4586 | 0.4107 | 1.0000 | 0.8988 |
| family_memory | lo | H5 | warmth@96h | 0.0579 | 0.0183 | 1.0000 | 0.9221 |
| independent | subject | H1 | warmth@0.375h | 0.0652 | 0.0246 | 1.0000 | 0.9773 |
| independent | subject | H1 | warmth@0h | 0.0694 | 0.0262 | 1.0000 | 0.9773 |
| independent | subject | H1 | warmth@1.5h | 0.0541 | 0.0204 | 1.0000 | 0.9773 |
| independent | subject | H1 | warmth@24h | 0.0013 | 0.0005 | 1.0000 | 0.9773 |
| independent | subject | H1 | warmth@6h | 0.0255 | 0.0097 | 1.0000 | 0.9773 |
| independent | subject | H1 | warmth@96h | 7.811e-09 | 2.952e-09 | 1.0000 | 0.9773 |
| independent | subject | H3 | warmth@0.375h | 0.1593 | 0.0600 | 1.0000 | 0.9419 |
| independent | subject | H3 | warmth@0h | 0.1692 | 0.0657 | 1.0000 | 0.9458 |
| independent | subject | H3 | warmth@1.5h | 0.1377 | 0.0478 | 1.0000 | 0.9360 |
| independent | subject | H3 | warmth@24h | 0.0382 | 0.0088 | 1.0000 | 0.9481 |
| independent | subject | H3 | warmth@6h | 0.0952 | 0.0275 | 1.0000 | 0.9369 |
| independent | subject | H3 | warmth@96h | 0.0019 | 0.0004 | 1.0000 | 0.9503 |
| independent | subject | H5 | warmth@0.375h | 0.2562 | 0.0809 | 1.0000 | 0.8993 |
| independent | subject | H5 | warmth@0h | 0.2629 | 0.0882 | 1.0000 | 0.9217 |
| independent | subject | H5 | warmth@1.5h | 0.2425 | 0.0675 | 1.0000 | 0.8823 |
| independent | subject | H5 | warmth@24h | 0.1464 | 0.0239 | 1.0000 | 0.8776 |
| independent | subject | H5 | warmth@6h | 0.2106 | 0.0460 | 1.0000 | 0.8716 |
| independent | subject | H5 | warmth@96h | 0.0568 | 0.0075 | 1.0000 | 0.9065 |
| independent | lo | H1 | warmth@0.375h | 0.0653 | 0.0247 | 1.0000 | 0.9773 |
| independent | lo | H1 | warmth@0h | 0.0695 | 0.0263 | 1.0000 | 0.9773 |
| independent | lo | H1 | warmth@1.5h | 0.0541 | 0.0205 | 1.0000 | 0.9773 |
| independent | lo | H1 | warmth@24h | 0.0013 | 0.0005 | 1.0000 | 0.9773 |
| independent | lo | H1 | warmth@6h | 0.0256 | 0.0097 | 1.0000 | 0.9773 |
| independent | lo | H1 | warmth@96h | 7.822e-09 | 2.964e-09 | 1.0000 | 0.9773 |
| independent | lo | H3 | warmth@0.375h | 0.1597 | 0.0603 | 1.0000 | 0.9419 |
| independent | lo | H3 | warmth@0h | 0.1696 | 0.0661 | 1.0000 | 0.9458 |
| independent | lo | H3 | warmth@1.5h | 0.1380 | 0.0481 | 1.0000 | 0.9361 |
| independent | lo | H3 | warmth@24h | 0.0382 | 0.0089 | 1.0000 | 0.9481 |
| independent | lo | H3 | warmth@6h | 0.0954 | 0.0277 | 1.0000 | 0.9369 |
| independent | lo | H3 | warmth@96h | 0.0019 | 0.0004 | 1.0000 | 0.9503 |
| independent | lo | H5 | warmth@0.375h | 0.2566 | 0.0814 | 1.0000 | 0.8993 |
| independent | lo | H5 | warmth@0h | 0.2634 | 0.0887 | 1.0000 | 0.9217 |
| independent | lo | H5 | warmth@1.5h | 0.2428 | 0.0680 | 1.0000 | 0.8823 |
| independent | lo | H5 | warmth@24h | 0.1465 | 0.0241 | 1.0000 | 0.8776 |
| independent | lo | H5 | warmth@6h | 0.2108 | 0.0464 | 1.0000 | 0.8716 |
| independent | lo | H5 | warmth@96h | 0.0568 | 0.0075 | 1.0000 | 0.9064 |
| no_memory | subject | H1 | warmth@0.375h | 0.0882 | -0.0153 | 1.0000 | 0.9667 |
| no_memory | subject | H1 | warmth@0h | 0.0939 | -0.0163 | 1.0000 | 0.9667 |
| no_memory | subject | H1 | warmth@1.5h | 0.0731 | -0.0127 | 1.0000 | 0.9667 |
| no_memory | subject | H1 | warmth@24h | 0.0017 | -0.0003 | 1.0000 | 0.9667 |
| no_memory | subject | H1 | warmth@6h | 0.0345 | -0.0060 | 1.0000 | 0.9667 |
| no_memory | subject | H1 | warmth@96h | 1.056e-08 | -1.832e-09 | 1.0000 | 0.9667 |
| no_memory | subject | H3 | warmth@0.375h | 0.2036 | -0.0233 | 1.0000 | 0.9227 |
| no_memory | subject | H3 | warmth@0h | 0.2191 | -0.0262 | 1.0000 | 0.9269 |
| no_memory | subject | H3 | warmth@1.5h | 0.1702 | -0.0171 | 1.0000 | 0.9173 |
| no_memory | subject | H3 | warmth@24h | 0.0408 | -0.0013 | 1.0000 | 0.9383 |
| no_memory | subject | H3 | warmth@6h | 0.1097 | -0.0076 | 1.0000 | 0.9223 |
| no_memory | subject | H3 | warmth@96h | 0.0020 | -4.965e-05 | 1.0000 | 0.9413 |
| no_memory | subject | H5 | warmth@0.375h | 0.2877 | -0.0136 | 1.0000 | 0.8823 |
| no_memory | subject | H5 | warmth@0h | 0.3027 | -0.0172 | 1.0000 | 0.9070 |
| no_memory | subject | H5 | warmth@1.5h | 0.2599 | -0.0072 | 1.0000 | 0.8660 |
| no_memory | subject | H5 | warmth@24h | 0.1380 | 0.0060 | 1.0000 | 0.8689 |
| no_memory | subject | H5 | warmth@6h | 0.2101 | 0.0016 | 1.0000 | 0.8588 |
| no_memory | subject | H5 | warmth@96h | 0.0524 | 0.0032 | 1.0000 | 0.9011 |
| no_memory | lo | H1 | warmth@0.375h | 0.0880 | -0.0152 | 1.0000 | 0.9667 |
| no_memory | lo | H1 | warmth@0h | 0.0937 | -0.0162 | 1.0000 | 0.9667 |
| no_memory | lo | H1 | warmth@1.5h | 0.0730 | -0.0126 | 1.0000 | 0.9667 |
| no_memory | lo | H1 | warmth@24h | 0.0017 | -0.0003 | 1.0000 | 0.9667 |
| no_memory | lo | H1 | warmth@6h | 0.0345 | -0.0060 | 1.0000 | 0.9667 |
| no_memory | lo | H1 | warmth@96h | 1.054e-08 | -1.824e-09 | 1.0000 | 0.9667 |
| no_memory | lo | H3 | warmth@0.375h | 0.2035 | -0.0232 | 1.0000 | 0.9226 |
| no_memory | lo | H3 | warmth@0h | 0.2189 | -0.0261 | 1.0000 | 0.9269 |
| no_memory | lo | H3 | warmth@1.5h | 0.1701 | -0.0170 | 1.0000 | 0.9173 |
| no_memory | lo | H3 | warmth@24h | 0.0408 | -0.0013 | 1.0000 | 0.9383 |
| no_memory | lo | H3 | warmth@6h | 0.1096 | -0.0076 | 1.0000 | 0.9223 |
| no_memory | lo | H3 | warmth@96h | 0.0020 | -4.961e-05 | 1.0000 | 0.9412 |
| no_memory | lo | H5 | warmth@0.375h | 0.2877 | -0.0136 | 1.0000 | 0.8822 |
| no_memory | lo | H5 | warmth@0h | 0.3026 | -0.0172 | 1.0000 | 0.9070 |
| no_memory | lo | H5 | warmth@1.5h | 0.2599 | -0.0072 | 1.0000 | 0.8660 |
| no_memory | lo | H5 | warmth@24h | 0.1380 | 0.0060 | 1.0000 | 0.8689 |
| no_memory | lo | H5 | warmth@6h | 0.2101 | 0.0016 | 1.0000 | 0.8588 |
| no_memory | lo | H5 | warmth@96h | 0.0524 | 0.0032 | 1.0000 | 0.9011 |
| shared | subject | H1 | warmth@0.375h | 0.0749 | 0.0257 | 1.0000 | 0.9765 |
| shared | subject | H1 | warmth@0h | 0.0797 | 0.0273 | 1.0000 | 0.9765 |
| shared | subject | H1 | warmth@1.5h | 0.0621 | 0.0213 | 1.0000 | 0.9765 |
| shared | subject | H1 | warmth@24h | 0.0015 | 0.0005 | 1.0000 | 0.9765 |
| shared | subject | H1 | warmth@6h | 0.0293 | 0.0100 | 1.0000 | 0.9765 |
| shared | subject | H1 | warmth@96h | 8.969e-09 | 3.074e-09 | 1.0000 | 0.9765 |
| shared | subject | H3 | warmth@0.375h | 0.1921 | 0.0690 | 1.0000 | 0.9408 |
| shared | subject | H3 | warmth@0h | 0.2044 | 0.0751 | 1.0000 | 0.9447 |
| shared | subject | H3 | warmth@1.5h | 0.1648 | 0.0558 | 1.0000 | 0.9349 |
| shared | subject | H3 | warmth@24h | 0.0441 | 0.0115 | 1.0000 | 0.9476 |
| shared | subject | H3 | warmth@6h | 0.1120 | 0.0336 | 1.0000 | 0.9361 |
| shared | subject | H3 | warmth@96h | 0.0021 | 0.0005 | 1.0000 | 0.9499 |
| shared | subject | H5 | warmth@0.375h | 0.3066 | 0.0955 | 1.0000 | 0.8988 |
| shared | subject | H5 | warmth@0h | 0.3170 | 0.1033 | 1.0000 | 0.9212 |
| shared | subject | H5 | warmth@1.5h | 0.2861 | 0.0810 | 1.0000 | 0.8820 |
| shared | subject | H5 | warmth@24h | 0.1657 | 0.0310 | 1.0000 | 0.8783 |
| shared | subject | H5 | warmth@6h | 0.2429 | 0.0573 | 1.0000 | 0.8717 |
| shared | subject | H5 | warmth@96h | 0.0636 | 0.0097 | 1.0000 | 0.9073 |
| shared | lo | H1 | warmth@0.375h | 0.0748 | 0.0256 | 1.0000 | 0.9765 |
| shared | lo | H1 | warmth@0h | 0.0796 | 0.0272 | 1.0000 | 0.9765 |
| shared | lo | H1 | warmth@1.5h | 0.0620 | 0.0212 | 1.0000 | 0.9765 |
| shared | lo | H1 | warmth@24h | 0.0015 | 0.0005 | 1.0000 | 0.9765 |
| shared | lo | H1 | warmth@6h | 0.0293 | 0.0100 | 1.0000 | 0.9765 |
| shared | lo | H1 | warmth@96h | 8.963e-09 | 3.064e-09 | 1.0000 | 0.9765 |
| shared | lo | H3 | warmth@0.375h | 0.1921 | 0.0688 | 1.0000 | 0.9408 |
| shared | lo | H3 | warmth@0h | 0.2044 | 0.0749 | 1.0000 | 0.9447 |
| shared | lo | H3 | warmth@1.5h | 0.1648 | 0.0557 | 1.0000 | 0.9349 |
| shared | lo | H3 | warmth@24h | 0.0441 | 0.0115 | 1.0000 | 0.9476 |
| shared | lo | H3 | warmth@6h | 0.1120 | 0.0335 | 1.0000 | 0.9361 |
| shared | lo | H3 | warmth@96h | 0.0021 | 0.0005 | 1.0000 | 0.9499 |
| shared | lo | H5 | warmth@0.375h | 0.3067 | 0.0954 | 1.0000 | 0.8988 |
| shared | lo | H5 | warmth@0h | 0.3170 | 0.1032 | 1.0000 | 0.9212 |
| shared | lo | H5 | warmth@1.5h | 0.2861 | 0.0810 | 1.0000 | 0.8820 |
| shared | lo | H5 | warmth@24h | 0.1657 | 0.0310 | 1.0000 | 0.8783 |
| shared | lo | H5 | warmth@6h | 0.2429 | 0.0574 | 1.0000 | 0.8718 |
| shared | lo | H5 | warmth@96h | 0.0636 | 0.0097 | 1.0000 | 0.9073 |
| slow_retention | subject | H1 | warmth@0.375h | 0.6819 | -0.6812 | 1.0000 | 0.9857 |
| slow_retention | subject | H1 | warmth@0h | 0.9997 | -0.9992 | 0.1094 | 0.9857 |
| slow_retention | subject | H1 | warmth@1.5h | 0.5014 | -0.5008 | 1.0000 | 0.9857 |
| slow_retention | subject | H1 | warmth@24h | 0.3894 | -0.3894 | 0.0000 | 0.9857 |
| slow_retention | subject | H1 | warmth@6h | 0.4695 | -0.4694 | 0.0000 | 0.9857 |
| slow_retention | subject | H1 | warmth@96h | 0.1839 | -0.1839 | 0.0000 | 0.9857 |
| slow_retention | subject | H3 | warmth@0.375h | 0.6693 | -0.6619 | 1.0000 | 0.9621 |
| slow_retention | subject | H3 | warmth@0h | 0.9848 | -0.9794 | 1.0000 | 0.9647 |
| slow_retention | subject | H3 | warmth@1.5h | 0.4910 | -0.4826 | 1.0000 | 0.9582 |
| slow_retention | subject | H3 | warmth@24h | 0.3837 | -0.3825 | 0.1562 | 0.9650 |
| slow_retention | subject | H3 | warmth@6h | 0.4598 | -0.4547 | 1.0000 | 0.9583 |
| slow_retention | subject | H3 | warmth@96h | 0.1836 | -0.1836 | 0.0000 | 0.9664 |
| slow_retention | subject | H5 | warmth@0.375h | 0.6525 | -0.6157 | 1.0000 | 0.9266 |
| slow_retention | subject | H5 | warmth@0h | 0.9583 | -0.9329 | 1.0000 | 0.9433 |
| slow_retention | subject | H5 | warmth@1.5h | 0.4842 | -0.4371 | 1.0000 | 0.9131 |
| slow_retention | subject | H5 | warmth@24h | 0.3706 | -0.3465 | 1.0000 | 0.9043 |
| slow_retention | subject | H5 | warmth@6h | 0.4514 | -0.4113 | 1.0000 | 0.9027 |
| slow_retention | subject | H5 | warmth@96h | 0.1741 | -0.1665 | 1.0000 | 0.9250 |
| slow_retention | lo | H1 | warmth@0.375h | 0.6819 | -0.6812 | 1.0000 | 0.9857 |
| slow_retention | lo | H1 | warmth@0h | 0.9997 | -0.9992 | 0.1094 | 0.9857 |
| slow_retention | lo | H1 | warmth@1.5h | 0.5014 | -0.5008 | 1.0000 | 0.9857 |
| slow_retention | lo | H1 | warmth@24h | 0.3894 | -0.3894 | 0.0000 | 0.9857 |
| slow_retention | lo | H1 | warmth@6h | 0.4695 | -0.4694 | 0.0000 | 0.9857 |
| slow_retention | lo | H1 | warmth@96h | 0.1839 | -0.1839 | 0.0000 | 0.9857 |
| slow_retention | lo | H3 | warmth@0.375h | 0.6693 | -0.6618 | 1.0000 | 0.9621 |
| slow_retention | lo | H3 | warmth@0h | 0.9848 | -0.9793 | 1.0000 | 0.9647 |
| slow_retention | lo | H3 | warmth@1.5h | 0.4910 | -0.4826 | 1.0000 | 0.9582 |
| slow_retention | lo | H3 | warmth@24h | 0.3837 | -0.3825 | 0.1562 | 0.9650 |
| slow_retention | lo | H3 | warmth@6h | 0.4598 | -0.4546 | 1.0000 | 0.9583 |
| slow_retention | lo | H3 | warmth@96h | 0.1836 | -0.1836 | 0.0000 | 0.9664 |
| slow_retention | lo | H5 | warmth@0.375h | 0.6524 | -0.6156 | 1.0000 | 0.9266 |
| slow_retention | lo | H5 | warmth@0h | 0.9582 | -0.9328 | 1.0000 | 0.9433 |
| slow_retention | lo | H5 | warmth@1.5h | 0.4841 | -0.4370 | 1.0000 | 0.9131 |
| slow_retention | lo | H5 | warmth@24h | 0.3705 | -0.3465 | 1.0000 | 0.9043 |
| slow_retention | lo | H5 | warmth@6h | 0.4512 | -0.4112 | 1.0000 | 0.9027 |
| slow_retention | lo | H5 | warmth@96h | 0.1741 | -0.1665 | 1.0000 | 0.9250 |

## Rho grid identifiability

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each row: 64 learners after 48 events (3,072 observations). Weights are learner/seed averages in support order; entropy fraction is averaged over seed-mean weight vectors. It therefore measures cohort concentration and can conceal different individual posteriors. LO has no rho grid. No quarter-point generating world was registered, so R5 resolution cannot be validated.

| World | Support/ladder | Posterior masses | Entropy / uniform entropy |
| --- | --- | --- | --- |
| balanced | R3-H3 | 0.3383, 0.3359, 0.3258 | 0.9993 |
| balanced | R5-H3 | 0.2026, 0.2024, 0.2011, 0.1987, 0.1951 | 0.9997 |
| family_memory | R3-H3 | 0.3311, 0.3337, 0.3352 | 0.9996 |
| family_memory | R5-H3 | 0.1986, 0.1995, 0.2001, 0.2007, 0.2011 | 0.9998 |
| independent | R3-H3 | 0.3486, 0.3354, 0.3161 | 0.9986 |
| independent | R5-H3 | 0.2090, 0.2054, 0.2009, 0.1955, 0.1892 | 0.9992 |
| no_memory | R3-H3 | 0.3317, 0.3385, 0.3298 | 0.9986 |
| no_memory | R5-H3 | 0.1983, 0.2013, 0.2023, 0.2010, 0.1972 | 0.9993 |
| shared | R3-H3 | 0.3258, 0.3352, 0.3390 | 0.9964 |
| shared | R5-H3 | 0.1951, 0.1983, 0.2008, 0.2025, 0.2033 | 0.9981 |
| slow_retention | R3-H3 | 0.3247, 0.3335, 0.3418 | 0.9996 |
| slow_retention | R5-H3 | 0.1948, 0.1975, 0.2001, 0.2026, 0.2051 | 0.9998 |

## Registered selection diagnostics

Seeds `adm0-v1:0`–`adm0-v1:7`; 8 synthetic learners/seed/world (64/world). Each interval has 8 paired seed means; each seed has 224 repeat, 64 sibling and 96 first-surface outcomes. Cells give mean / lower / upper of candidate-minus-simpler log loss, t(7) 95%. Negative favours the candidate. Coverage minimum covers ability, memory weights and six warmth-curve points at event 48. The joint rule is deliberately reported separately from isolated loss improvements.

| Comparison | World | Repeat delta / CI | Sibling delta / CI | First-surface delta / CI | Min recovery coverage | Joint criteria |
| --- | --- | --- | --- | --- | --- | --- |
| lo:rho0.5-H3 vs rho0.5-H1 | balanced | -7.827e-06 / -0.0002 / 0.0002 | 0.0001 / -6.361e-05 / 0.0003 | -8.392e-05 / -0.0004 / 0.0002 | 0.9688 | False |
| lo:rho0.5-H3 vs rho0.5-H1 | family_memory | 7.214e-05 / -0.0001 / 0.0003 | -0.0003 / -0.0004 / -8.449e-05 | -7.763e-05 / -0.0004 / 0.0002 | 0.8750 | False |
| lo:rho0.5-H3 vs rho0.5-H1 | independent | 6.317e-06 / -0.0002 / 0.0002 | 9.107e-05 / -4.639e-05 / 0.0002 | -1.651e-05 / -0.0004 / 0.0003 | 0.9688 | False |
| lo:rho0.5-H3 vs rho0.5-H1 | no_memory | 7.056e-05 / -0.0005 / 0.0007 | -4.549e-06 / -0.0002 / 0.0002 | -5.914e-05 / -0.0004 / 0.0003 | 0.9531 | False |
| lo:rho0.5-H3 vs rho0.5-H1 | shared | -3.658e-05 / -0.0003 / 0.0002 | 4.649e-05 / -0.0002 / 0.0003 | -0.0003 / -0.0007 / 0.0002 | 0.8906 | False |
| lo:rho0.5-H3 vs rho0.5-H1 | slow_retention | 9.999e-05 / -2.295e-05 / 0.0002 | -0.0002 / -0.0005 / -3.922e-05 | -9.592e-06 / -0.0002 / 0.0002 | 0.0000 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | balanced | -8.314e-05 / -0.0003 / 0.0001 | 0.0004 / -0.0002 / 0.0010 | -0.0002 / -0.0008 / 0.0005 | 0.9688 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | family_memory | 2.145e-05 / -0.0003 / 0.0004 | -0.0005 / -0.0009 / -7.274e-05 | 0.0001 / -0.0009 / 0.0011 | 0.8750 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | independent | -8.942e-05 / -0.0004 / 0.0002 | 0.0002 / -0.0001 / 0.0006 | -0.0002 / -0.0011 / 0.0008 | 0.9688 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | no_memory | 3.928e-05 / -0.0005 / 0.0006 | 0.0006 / -7.310e-05 / 0.0013 | -0.0001 / -0.0009 / 0.0006 | 0.9531 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | shared | -0.0002 / -0.0006 / 0.0002 | 0.0002 / -0.0006 / 0.0010 | -0.0005 / -0.0016 / 0.0005 | 0.9219 | False |
| lo:rho0.5-H5 vs rho0.5-H3 | slow_retention | 6.133e-05 / -0.0002 / 0.0003 | -0.0006 / -0.0010 / -0.0001 | -1.923e-06 / -0.0006 / 0.0006 | 0.7500 | False |
| subject:R3-H3 vs R1-H3 | balanced | -4.885e-05 / -7.837e-05 / -1.934e-05 | 0.0011 / 0.0005 / 0.0018 | 2.619e-05 / -0.0001 / 0.0002 | 0.9688 | False |
| subject:R3-H3 vs R1-H3 | family_memory | 3.509e-05 / -3.917e-05 / 0.0001 | -1.235e-05 / -0.0003 / 0.0003 | -5.616e-06 / -0.0002 / 0.0002 | 0.8750 | False |
| subject:R3-H3 vs R1-H3 | independent | -8.633e-06 / -5.755e-05 / 4.029e-05 | 0.0006 / -0.0004 / 0.0016 | 3.639e-05 / -0.0001 / 0.0002 | 0.9688 | False |
| subject:R3-H3 vs R1-H3 | no_memory | 1.929e-05 / -0.0001 / 0.0002 | 0.0010 / 0.0006 / 0.0015 | 7.393e-05 / -0.0002 / 0.0003 | 0.9531 | False |
| subject:R3-H3 vs R1-H3 | shared | -3.108e-05 / -6.813e-05 / 5.968e-06 | 0.0009 / -0.0011 / 0.0029 | -2.087e-05 / -0.0001 / 0.0001 | 0.8906 | False |
| subject:R3-H3 vs R1-H3 | slow_retention | 3.457e-05 / -2.257e-05 / 9.171e-05 | -0.0002 / -0.0005 / 0.0001 | 4.046e-05 / -8.818e-05 / 0.0002 | 0.0000 | False |
| subject:R3-H3 vs R3-H1 | balanced | -6.682e-06 / -0.0002 / 0.0002 | 0.0001 / -7.022e-05 / 0.0003 | -8.586e-05 / -0.0004 / 0.0002 | 0.9688 | False |
| subject:R3-H3 vs R3-H1 | family_memory | 7.198e-05 / -0.0001 / 0.0003 | -0.0003 / -0.0004 / -8.620e-05 | -7.781e-05 / -0.0004 / 0.0002 | 0.8750 | False |
| subject:R3-H3 vs R3-H1 | independent | 6.663e-06 / -0.0002 / 0.0002 | 8.955e-05 / -4.051e-05 / 0.0002 | -1.872e-05 / -0.0004 / 0.0003 | 0.9688 | False |
| subject:R3-H3 vs R3-H1 | no_memory | 7.139e-05 / -0.0005 / 0.0007 | -2.012e-05 / -0.0002 / 0.0002 | -5.743e-05 / -0.0004 / 0.0003 | 0.9531 | False |
| subject:R3-H3 vs R3-H1 | shared | -3.586e-05 / -0.0003 / 0.0002 | 4.667e-05 / -0.0002 / 0.0003 | -0.0003 / -0.0007 / 0.0002 | 0.8906 | False |
| subject:R3-H3 vs R3-H1 | slow_retention | 9.964e-05 / -2.330e-05 / 0.0002 | -0.0002 / -0.0005 / -3.883e-05 | -1.013e-05 / -0.0002 / 0.0002 | 0.0000 | False |
| subject:R3-H5 vs R3-H3 | balanced | -8.168e-05 / -0.0003 / 0.0001 | 0.0004 / -0.0002 / 0.0010 | -0.0002 / -0.0008 / 0.0005 | 0.9688 | False |
| subject:R3-H5 vs R3-H3 | family_memory | 2.047e-05 / -0.0003 / 0.0004 | -0.0005 / -0.0009 / -6.260e-05 | 0.0001 / -0.0009 / 0.0011 | 0.8750 | False |
| subject:R3-H5 vs R3-H3 | independent | -8.983e-05 / -0.0004 / 0.0002 | 0.0002 / -0.0001 / 0.0006 | -0.0002 / -0.0011 / 0.0008 | 0.9688 | False |
| subject:R3-H5 vs R3-H3 | no_memory | 4.097e-05 / -0.0005 / 0.0006 | 0.0006 / -0.0001 / 0.0013 | -0.0001 / -0.0009 / 0.0006 | 0.9531 | False |
| subject:R3-H5 vs R3-H3 | shared | -0.0002 / -0.0006 / 0.0002 | 0.0002 / -0.0005 / 0.0010 | -0.0005 / -0.0016 / 0.0005 | 0.9219 | False |
| subject:R3-H5 vs R3-H3 | slow_retention | 6.040e-05 / -0.0002 / 0.0003 | -0.0006 / -0.0010 / -0.0001 | -4.841e-06 / -0.0006 / 0.0006 | 0.7500 | False |
| subject:R5-H3 vs R3-H3 | balanced | 1.193e-05 / 4.630e-06 / 1.923e-05 | -0.0003 / -0.0004 / -0.0001 | -7.134e-06 / -4.912e-05 / 3.485e-05 | 0.9688 | False |
| subject:R5-H3 vs R3-H3 | family_memory | -8.749e-06 / -2.735e-05 / 9.852e-06 | 1.728e-06 / -8.259e-05 / 8.604e-05 | 1.152e-06 / -4.493e-05 / 4.723e-05 | 0.8750 | False |
| subject:R5-H3 vs R3-H3 | independent | 1.776e-06 / -1.018e-05 / 1.373e-05 | -0.0002 / -0.0004 / 5.780e-05 | -8.261e-06 / -4.997e-05 / 3.345e-05 | 0.9688 | False |
| subject:R5-H3 vs R3-H3 | no_memory | -4.937e-06 / -3.817e-05 / 2.830e-05 | -0.0003 / -0.0004 / -0.0001 | -1.960e-05 / -8.137e-05 / 4.217e-05 | 0.9531 | False |
| subject:R5-H3 vs R3-H3 | shared | 7.676e-06 / -1.512e-06 / 1.686e-05 | -0.0002 / -0.0007 / 0.0003 | 5.480e-06 / -2.599e-05 / 3.695e-05 | 0.8906 | False |
| subject:R5-H3 vs R3-H3 | slow_retention | -8.629e-06 / -2.299e-05 / 5.730e-06 | 4.086e-05 / -2.993e-05 / 0.0001 | -1.030e-05 / -4.267e-05 / 2.208e-05 | 0.0000 | False |

- `lo:rho0.5-H3 vs rho0.5-H1`: **data cannot select this candidate**; additional diagnostics `{"curve_rmse_reduced": false}`.
- `lo:rho0.5-H5 vs rho0.5-H3`: **data cannot select this candidate**; additional diagnostics `{"curve_rmse_reduced": true}`.
- `subject:R3-H3 vs R1-H3`: **data cannot select this candidate**; additional diagnostics `{"quarter_point_truth_available": null, "rho_mass_above_uniform": true}`.
- `subject:R3-H3 vs R3-H1`: **data cannot select this candidate**; additional diagnostics `{"curve_rmse_reduced": false}`.
- `subject:R3-H5 vs R3-H3`: **data cannot select this candidate**; additional diagnostics `{"curve_rmse_reduced": true}`.
- `subject:R5-H3 vs R3-H3`: **data cannot select this candidate**; additional diagnostics `{"quarter_point_truth_available": false, "rho_mass_above_uniform": true}`.


Failure to select is not equivalence, nor proof that no effect exists. Where a loss interval is wholly positive it is evidence against that candidate under that world; intervals crossing zero cannot resolve the predictive ordering. Sparse siblings, correlated memory/effect terms and prior sensitivity prevent a general per-learner recovery claim. These are observational fits to scripted schedules, not randomized policy-effect estimates.

## Cost

Seeds `adm0-v1:0`–`adm0-v1:7`; balanced world, 1 learner/seed, 48-event cold replays. Cached-input and synthetic Next costs are per call over 100 calls/seed. Next uses the full 108-filter state, three repeat/sibling/novel predictions and 16 fixed novel-family demand points; it is not the production router. No model, DB, UI or disk work is included. Covariance bytes count S and S0 only.

| Workload | Median ms | Min ms | Max ms | Calls/seed | Filters | Coordinates | Covariance bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cached_inputs | 0.0500 | 0.0493 | 0.0527 | 100 | N/A | N/A | N/A |
| candidate_cold | 12.0290 | 11.8403 | 12.6904 | 1 | 9 | 58 | 484416 |
| full_grid_cold | 50.7145 | 48.4159 | 54.7020 | 1 | 108 | 58 | 5812992 |
| predecessor_cold | 5.1355 | 4.5390 | 5.4426 | 1 | 3 | 26 | 32448 |
| synthetic_next | 1.8326 | 1.7973 | 1.8674 | 100 | 108 for Next | N/A | N/A |

Complete candidate-grid experiment: **52.823 s**; complete numerical report workload including diagnostics/benchmarks: **55.141 s**. Counts: 6 worlds x 8 seeds x 2 views x (23 candidates + predecessor) x 48 events x 8 learners = 884,736 arm-predictions, plus six descriptive baselines on the same 18,432 presentations. Subject candidate filters per learner are 3, 9 or 15; the full inherited-grid/R3 benchmark has 108. The timings include Python/NumPy overhead and depend on the execution environment; no latency threshold was chosen. Full inherited 36-point predecessor cost was not separately timed; the exact collapsed three-point predecessor was. No approximation is proposed, so approximation error is N/A.

## Tests, reproduction and owner questions

Landing contracts: `tests/test_ad_memory_simulation.py -m 'not arc_close'`. Full report source: the same explicit file with `-m arc_close --junitxml=results.xml` (final corrected run at the registered size). Render with `python scripts/adm0_simulation_report.py results.xml docs/reviews/adm0-simulation-report.md`. Use the supplied pytest/venv wrappers; no index or commit operations are performed. The final handoff records the actual regression/gate command results.

For the spec owner: correct §4.2's sign wording to match §4.4; keep the rho/warmth/prior ranges unselected pending stronger identification; confirm that RE8 width recovery belongs to ADM3; decide whether later experiments should independently vary delays, include quarter-point rho truths and multiple cells, or randomized novel-family checks. Those require a new preregistration. Owner-copy counts remain entirely in the owner's lane. No production support or LO value is authorized by this report.

## Final validation record (after rendering)

`T` denotes the supplied `$SCRATCH/t.sh`; `P` denotes `$SCRATCH/py.sh`.
The final explicit-file regression/guard batch was equivalent to this shell
brace expansion (23 files, at most two workers, never the whole suite):

```sh
T tests/test_{ad_memory_simulation,ad2_model,ad23_sim_smoke,ad2_serving,km5_sim_gates,km2_sim_gates,learner_read_model_pinning,sim_teach_back,sim_probe_validation_cli,sim_probe_validation,sim_planted_types_forty_seeds,sim_goals,ad23_sim,ad3_subject_view,ad3_reading,ad3_dose_arm,ad23_fix_review,one_retrievability,identity_pins,structure_ratchets,public_tip_guards,test_layout,architecture}.py -q -n 2 -m 'not arc_close'
```

Last result: `578 passed, 11 skipped in 115.10s (0:01:55)`.
The 21 new fast contracts are included. The 11 skips are exclusively
`test_learner_read_model_pinning.py`'s owner-vault lane, intentionally not enabled.
A separate `T tests/test_learner_read_model_pinning.py -q -n 2 -rs` confirmed
all eleven require authorized backup-API copies; last line: `11 skipped in 1.12s`.
No other requested check was blocked by the sandbox.

- Final `T tests/test_ad_memory_simulation.py -q -n 2 -m arc_close --junitxml=.adm0-results.xml`: `1 passed in 56.84s`.
- `P python scripts/adm0_simulation_report.py .adm0-results.xml docs/reviews/adm0-simulation-report.md`: `Rendered 6 worlds, 18432 presentations; preregistration hash verified`.
- `P ruff check`: `All checks passed!`.
- `P lint-imports --no-cache`: `Contracts: 45 kept, 0 broken.`
- `P python scripts/check_gate_partition.py`: `collected 32368: landing 32302 + arc_close 66` (collection only).
- `git diff --check`: exit 0, no output.

The two new simulation modules have narrow development-only import-linter
exceptions beside the existing simulation exceptions; no production
configuration changed. The frozen-cycle contract initially caught these
undeclared leaf edges and passed after registration. Tracked-file guards
were run with the index untouched. An additional prospective structure sweep
included the new Python files and passed; the new test contributes exactly
zero private LearnLoop patch sites and zero source-text assertions.
The orchestrator still runs the landing gate after adding the new files.

The temporary JUnit payload/logs are removed from the handoff because JUnit
contains local paths. The numerical tables above retain only synthetic
aggregates. This manual validation section is recorded after table generation;
a future rerender should replace it with that execution's actual checks.
