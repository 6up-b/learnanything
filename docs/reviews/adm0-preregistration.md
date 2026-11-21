# ADM0 preregistration — frozen before implementation and results

Frozen protocol, 2026-11-21, base `3f42da228a`, ADM §§4.2–4.5,
§5, §7 and §9. This file is completed before new simulation code or its tests
are written or run. Its SHA-256 is recorded in the simulation report before
running them. The orchestrator, not this sandbox, commits the artifacts; this
is a hash-frozen preregistration, not a claim of a prior Git commit.
No owner data is read. No constant is selected from observed owner outcomes.
At n = 1 this exercise makes **no claim of learner benefit**.

## Scope and numerical reference

Add `sim/ad_memory_synthetic.py` beside `ad_synthetic.py`: the predecessor's
single-use pools, seeds, fixtures and scenarios remain unchanged. Use the real
`Bank`, `View`, category likelihood and Gaussian projection, retaining all
cross-covariances. One behaviour-neutral seam may expose residual variance to
`Bank.update`, defaulting to its exact old expression; no production caller
opts in. No approximation to the joint Gaussian bank is proposed. “Exact”
means exact joint covariance within AD's existing assumed-density filtering
and 32-node quadrature, not an exact non-Gaussian posterior.

Effects enter with positive sign in eta, as the displayed predictor in ADM
§4.4 states. The sentence in §4.2 giving coefficients -1 conflicts with that
predictor: -1 would be appropriate for the old difficulty residual epsilon,
not for an easiness effect. Zero-centred priors make either consistent sign
convention equivalent; recovery will use the positive-easiness convention.

## Prior register and candidate supports

All Gaussian pairs below mean (mean, **variance**), not standard deviation.
Sources are repository references, requiring no network or model call.

| Quantity | Candidate and basis |
|---|---|
| Shared AD state | Unmodified `adaptive_difficulty/priors.py`, `ad_priors_v1` and `ad_hyper_v1`; historical baseline basis in `docs/reviews/adaptive-difficulty-ad23.md` §1.1 and AD spec §5.5. Cold cell variance 3, gamma N(0.2,0.01), drift 0.01/day, discrimination 1, lapse .02, category offset 1.5 and residual variance 1 are inherited, not newly validated population estimates. |
| Family/item effects | N(0,rho*tau0²), N(0,(1-rho)*tau0²), independent initially; ADM §4.2 preserves inherited total residual variance tau0²=1. A singleton has one N(0,1) item effect and no family effect/memory. No published basis for the split. |
| rho | **Variance split, not a decay rate.** R1=(.5), R3=(0,.5,1), R5=(0,.25,.5,.75,1), uniform initial weights; named simulation design ranges, not supported population constants. LO reference .5 is a registered diagnostic value only; LO sensitivity runs fixed rho 0 and 1 too. Subject crosses rho with its existing grid. |
| Item memory weight | N(.5,.25), ADM §4.4: router combiner's labelled seed in `router_objective/memory.py`; legacy analogy, not an empirical AD estimate. |
| Family memory weight | N(0,.25), ADM §4.4: zero-centred shrinkage, explicitly no published magnitude. Width .25 is an unsupported inherited proposal; carry .0625,.25,1 as sensitivity, never declare .25 established. |
| Warmth | Six-hour coefficient N(1,.25), inherited `ZETA_PRIOR`. Extra coefficients N(0,.25), ADM §4.5; no empirical basis for their width or scales. H1=(6), H3=(1.5,6,24), H5=(.375,1.5,6,24,96) hours are named geometric design ranges containing 6, not chosen constants. Signed weights remain allowed. |
| Retention | Read `retrievability` at FSRS-6 defaults and fold with `apply_review`; population basis is the pinned py-fsrs release/commit documented in `scheduling/fsrs.py`. Rating mapping is the synthetic rubric below. No fitted owner weights. |
| Effective-stability width | LP §4.6 proposes s=(.05,.15,.5,1), uniform, w~N(0,s²). Basis is explicitly simulation pending recovery, not published widths. ADM0 tests sensitivity to planted S_eff; it does not implement RE8's fitter or select s. Those widths cannot be selected by this experiment. |
| Running success baseline | `adm0_rate_v1`: Beta(a,a), a in (.5,1,2). Symmetric ignorance/Jeffreys (.5) and uniform (1) mathematical conventions, no population basis. All three are reported, none selected. Last-outcome baseline starts at .5; thereafter 0 or 1, clipped only for scoring. |

Prior sensitivity is one factor at a time around R3/H3: separately multiply
item-memory, family-memory, extra-warmth and total-effect variances by .25
and 4; separately shift item-memory and family-memory means by +/- one
reference SD (.5), and all extra-warmth means together by +/- .5. The total
effect sensitivity scales the corresponding unseen residual too and is a
stress test, not a proposed replacement for tau0. Singleton variance scales
with the total-effect stress. Six-hour prior stays inherited. Report all
these arms, including bad results. The nine R1/R3/R5 x H1/H3/H5 reference
arms plus fourteen sensitivities are 23 candidates per subject view. LO
uses fixed rho .5 for ladder/prior comparisons plus fixed endpoints 0 and 1;
it does not pretend to have a learned rho posterior.

## Events, temporal boundary, label closure and truth

An event is one synthetic presentation with fixed revision/item/surface IDs,
one retrieval cell in one LO/subject, reference feature tuple, no assistance,
no pre-exposure, one finalized rubric category. Y=1 iff category=2 (unassisted
success); categories 0/1/2 follow today's graded-logistic link. Synthetic
rubric scores 0/2/4 out of 4 map to FSRS AGAIN/HARD/GOOD respectively, and
mastery receives those same scores. There are no hidden grading corrections.
This study does not estimate assisted/primed/held performance.

Time origin is 2026-01-01T00:00:00Z. Each 12-presentation block starts at day
36*b, b=0..3; offsets in days are (0,1/24,1/4,1,3,7,30,31,32,33,34,35).
Within a block: anchor, six same-anchor repeats, two previously unseen
siblings in that anchor's family, singleton, repeat of that singleton,
then first item in a novel family after drilling. IDs do not change on repeat.
There are 48 presentations, 20 items, 12 surface groups, eight unseen siblings,
28 same-item repeats, four singleton first encounters, four initial anchors
and four novel-after-drilling observations per synthetic learner. Singleton
repeats also have an explicit singleton flag, never a duplicated family term.
Delays are grouped by <=1 day, >1..7 days, >7 days and no prior item; assigned
versus natural-labelled delays alternate by block (each 24 events). Natural
is a scripted label, not evidence of a real observational sampling process.

A serve admits reviews with review time **strictly less** than its serve;
an equal-time review is not a feature. All labels close at
2026-06-01T00:00:00Z, inclusive, resolver `adm0_synthetic_categories_v1`.
All scheduled events precede closure. The event's prediction and frozen
memory offsets are computed before its category is read; measurement then
once-per-first-surface learning, then review-fold append. The first graded
surface consumes the opportunity even if ineligible in boundary tests.
In the scored main runs every event is eligible: issued=answered=resolved;
missing=unbound=censored=held=primed=pre-exposed=0. A boundary unit test varies
the current/future/equal-time category; it must not change the current inputs.

Truth uses independent seeded Gaussian ability (variance 3) and gamma
N(.2,.01), stable family/item effects with variance total 1 and the world's
rho. Gamma is not clipped; its inherited Gaussian is the truth distribution.
Only the first encounter of a surface adds gamma to truth. The stable effects
do not random-walk; the filter retains spec drift. This deliberate mismatch
must be stated in coverage/recovery discussion. Truth memory offsets use
true pre-memory eta; candidate offsets use their own frozen predicted mean.
Neither reads the current outcome. Truth and candidates read the same past
FSRS fold, but only truth may apply the planted stability multiplier.

Six named worlds (design interventions, **not asserted human constants**):

| World | rho | zeta_I,zeta_F | Warmth coefficients | S multiplier |
|---|---:|---|---|---:|
| independent | 0 | .5,0 | H1: (1) | 1 |
| balanced | .5 | .5,0 | H1: (1) | 1 |
| shared | 1 | .5,0 | H1: (1) | 1 |
| no_memory | .5 | 0,0 | H1: (1) | 1 |
| family_memory | .5 | 1,.5 | H3: (.5,1,-.5) | 1 |
| slow_retention | .5 | 1,.5 | H5: (.5,0,1,0,.5) | exp(.5) |

Seeds are the eight exact strings `adm0-v1:0` through `adm0-v1:7`, using
`ad_synthetic.rng_for`. Each world/seed has eight independent learners.
Draw base normals and one outcome uniform per event/learner before fitting
any arm; transform the same normals across worlds, and reuse identical truth,
labels, uniforms and schedules across every paired arm and both views.
Total 384 synthetic trajectories and 18,432 presentations, **not 384 real
people**. Fast tests may use smaller explicit seeds and sizes; they are not
sources of headline recovery or model-selection results.

## Baselines, scores and recovery

Predecessor: today's `View`/`Bank`, full subject grid (36) and fixed LO point,
six-hour warmth, independent integrated residual each prediction, measurement
and gamma only at the first surface. No successor effects or memory. The
subject's 36 points have identical coupling/implication behaviour in this
one-cell experiment; collapse those duplicate points to the three split
points for the main candidate runs, with exactly matching uniform weights.
Benchmark the full 36 x rho grid separately. Do not infer cross-topic
transfer recovery from this design.

Other baselines, same events and past-only inputs: plain FSRS R on repeats
(no prediction without an item state); Beta running success; last outcome;
and real `mastery_ekf` using its default `MasteryConfig`, reference item a=1
and the configured default difficulty. Report eligibility denominator for
FSRS. No baseline gets the generating truth as a feature.

Report binary log loss (clip [1e-9,1-1e-9] only for numeric safety), Brier,
calibration error in ten equal-width probability bins, signed calibration
bias, and coverage of nominal 95% latent-eta intervals of the AD mixtures
(moment mean +/- normal .975 quantile times moment SD, including unobserved
residual). Coverage is of planted eta, **not a Bernoulli outcome**. Baselines
without a latent posterior get N/A for this coverage. The mixture moment
interval is a declared diagnostic summary, not an approximation to the fit.

Tables include both views, first surface, same item, unseen sibling,
singleton (first and repeat flag), novel after drilling, delay buckets and
delay source. Every table states seed set and event/learner counts. Aggregate
calibration is descriptive; dependent attempts are not independent samples.
Paired loss differences use each seed's mean across its eight learners,
with a Student-t 95% interval over eight seeds (df=7); no post-hoc exclusions.

Recoverability: at event 12 and 48 report ability, first family effect,
first item effect, item/family memory weight and warmth curve (at hours
0,.375,1.5,6,24,96): RMSE, bias, 95% interval coverage and posterior/prior
variance ratio, averaged across seeds/learners. Report rho posterior weights,
entropy relative to uniform and planted-point mass. An isolated same-item
study has 512 observations, fixed time, gamma transition disabled, no warmth
or memory: ability prior v_s=3 and total stable effect v_e=1 imply floor
v_s*v_e/(v_s+v_e)=.75. Also test v_e=.25 and 4 (floors derived, not tuned).
Report cross-covariance and sibling/novel variances. A deterministic contrast
of high ability/no extra familiarity and low ability/heavy familiarity
with equal repeated-item eta demonstrates the non-identifiable direction;
novel-family predictions break that equality, but a single binary answer
cannot establish the decomposition. Do not claim per-person separation from
that one answer.

## Selection rules, fixed before results

No production choice or activation gate is made by this study. A candidate
is **favoured within these simulations** only if its seed-paired loss interval
is below zero against the simpler candidate, separately on repeated items
and unseen siblings, while its first-surface interval does not demonstrate
harm (lower endpoint >0), and its identifiable planted quantities' 95%
coverage is at least .90. The .90 coverage check is a registered Monte Carlo
diagnostic tolerance, not a human learning threshold. Brier/calibration and
recovery failures must be reported even if loss improves.

R3 versus R1 and R5 versus R3: require in addition that mean posterior mass
at the true represented rho exceed its uniform mass in every represented
rho world (independent/balanced/shared), and interval/recovery checks above.
Choose the smallest support satisfying these diagnostics. The experiment
contains no quarter-point truth, so it cannot justify R5's interior resolution.
H3 versus H1 and H5 versus H3: require curve RMSE reduction on the world that
plants the added scales as well as the predictive/coverage criteria; require
no demonstrated first-surface harm in the six-hour-only worlds. Otherwise
report **the data cannot tell them apart** (or evidence against a candidate,
where the interval demonstrates harm), retain candidate ranges, and defer
support/LO-value selection. Overlapping intervals, weak contraction,
near-uniform grid weights or confounded coefficients are not “recovered”.
Prior sensitivity is a robustness report, never a way to tune until a gate
passes. Warmth's mean-equality check must explicitly report extra variance
sum(.25*exp(-2*delay/h)) and change in prior-predictive success and band mass.

## Cost, artifacts and test partition

Measure with monotonic wall time, no timing pass/fail thresholds: one-learner
48-event cold numerical replay (predecessor, R3/H3 and full 36 x R3 subject),
full candidate experiment, cached-input construction (100 calls), synthetic
Next (100 calls: frozen novel/sibling/repeat predictions and band calculation
on 16 fixed feature-demand points from -2 to 2, no DB/LLM/UI). Report median
and range over registered seeds, dimensions and counts; cached construction
must not include replay. This is numerical workload cost, not production
Next latency, storage or vault rebuild time. No owner-path measurements.

Fast deterministic contract tests belong to the landing gate. One explicitly
marked `arc_close` test runs all registered seeds/worlds/candidates, writes the
aggregate report payload only when an explicit output destination is passed
by environment, and is the report's source. Failed scientific selection
criteria are reported as findings, not xfails or reasons to alter seeds.
Implementation errors may be corrected with a report ledger, without editing
this frozen protocol or tuning candidates. No approximation is proposed,
so approximation-error comparison is not applicable. Owner-copy prevalence,
RE8 width learning, production latency and learner benefit remain undecided.
