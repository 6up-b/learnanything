# LearnLoop Algorithm Documentation

Canonical reference for the Python backend implementation as of 2026-05-28.

This document describes the math and the current architecture of the LearnLoop learning algorithm implemented in `src/learnloop`. It is intentionally implementation-bound: when a statement here names a parameter, table, service, or equation, it reflects the code paths currently used by the Python backend, not a future design target.

## 1. Scope And Source Map

The learning algorithm is not a single model. It is a deterministic pipeline that combines item-level memory scheduling, Learning Object mastery, facet-level recall, diagnostic probe beliefs, error events, item quality, and authoring/regrade services.

Primary implementation files:

- `src/learnloop/services/attempts.py`: the shared attempt application pipeline. Every live attempt, replayed attempt, and accepted regrade is converted into the same derived state updates here.
- `src/learnloop/services/mastery.py`: scalar Learning Object mastery state, the 2PL probability-space EKF, display conversion, difficulty resolution, and the legacy logit Kalman fallback.
- `src/learnloop/services/fsrs.py`: deterministic local FSRS-6 item memory model.
- `src/learnloop/services/recall_coverage.py`: coverage, reliability, familiarity discounting, facet Beta updates, predicted correctness, error severity, and practice item quality.
- `src/learnloop/services/probes.py`: probe hypothesis sets, conditional outcome distributions, expected information gain, Bayesian posterior replay, self-tagged misconception weighting, and probe completion.
- `src/learnloop/services/scheduler.py`: due queue construction, legacy priority terms, probe EIG insertion, follow-up insertion, scheduler explanations, and scheduler slate logs.
- `src/learnloop/services/selection_rewards.py`: skill and item demand vectors, predicted correctness for selection, selection reward, and the decomposed probe information reward.
- `src/learnloop/services/grading.py`: grading context construction, self/Codex/AI grade validation, rubric score validation, and error attribution validation.
- `src/learnloop/services/observations.py`: observation template registration, observation event recording, and optional conversion of bound observations into self-graded attempts.
- `src/learnloop/services/proposals.py`, `practice_generation.py`, `source_ingestion.py`, and `patches.py`: question authoring, canonical source ingestion, post-probe and diagnostic practice generation, proposal review policy, validation, auto-apply rules, and vault writes through writer services.
- `src/learnloop/services/replay.py` and `regrade.py`: deterministic rebuilds and deferred AI/Codex regrades.
- `src/learnloop/config.py`: default parameters. The local `learnloop.toml` may omit some newer sections; Pydantic defaults still apply.
- `src/learnloop/vault/models.py` and `src/learnloop/db/repositories.py`: durable YAML models and SQLite-derived state models.

Current algorithm version is `mvp-0.2` from `[algorithms].algorithm_version`.

## 2. The State Spaces

LearnLoop keeps source-of-truth learning content in Markdown/YAML and derived learner state in SQLite. The important state variables are:

- Practice item memory state: for Practice Item $i$, FSRS stores dynamic item memory difficulty $D_i$, stability $S_i$, retrievability $R_i$, due time $t_{due,i}$, active flag, content hash, and last attempt time in `practice_item_state`.
- Learning Object mastery state: for Learning Object $\ell$, `learning_object_mastery` stores logit-space latent mean $\mu_\ell$, logit variance $P_\ell$, evidence count, last evidence time, algorithm version, and updated time. The display mastery is $m_\ell = \sigma(\mu_\ell)$ and the display variance is $\operatorname{Var}(m_\ell) \approx (m_\ell(1-m_\ell))^2 P_\ell$.
- Facet recall state: for Learning Object $\ell$ and evidence facet $f$, optionally scoped to Practice Item $i$, `evidence_facet_recall_state` stores Beta parameters $\alpha_{\ell f}$ and $\beta_{\ell f}$, mean $\alpha/(\alpha+\beta)$, variance $\alpha\beta/((\alpha+\beta)^2(\alpha+\beta+1))$, independent evidence mass, raw coverage mass, and consecutive failures.
- Error event state: `error_events` stores active or resolved error events with error type $E$, local severity $s_E \in [0,1]$, misconception flag, and timestamps.
- Probe state: `lo_probe_state` stores whether a Learning Object is in an in-progress or complete probe phase, the locked hypothesis set id, completed attempts, target attempts, convergence families, and entry/completion times.
- Probe hypothesis set: `hypothesis_sets` stores a locked categorical prior over labels such as `mastered`, `unfamiliar`, and `misconception:<error_type>`.
- Learner state beliefs: `learner_state_beliefs` persists misconception posteriors from probes. It stores mean, variance, evidence count, and last surprise for scope type `misconception`.
- Attempt surprise: `attempt_surprise` stores predicted score distribution metadata, predicted error type distribution, observed bucket, predictive surprise, Bayesian surprise, surprise direction, FSRS interval factor, and actions.
- Observation templates and events: `observation_templates` stores reusable external-observation schemas, while `observation_events` stores recorded observations, binding mode, response payload, related entity ids, and any emitted attempt id.
- Attempt debug payloads: `attempt_debug_payloads` stores the structured attempt computation trace keyed by attempt id and algorithm version.
- Intervention needs: `intervention_needs` stores unresolved follow-up requests when the scheduler cannot queue a suitable existing item. A need records the Learning Object, optional triggering attempt and Practice Item, desired intent, trigger reason, target facets, an `error_types` field, candidate requirements, priority, status, and blocked reason. Follow-up-created needs currently leave `error_types` empty and rely on `trigger_reason` plus `target_facets`.
- Practice item quality: `practice_item_quality_state` stores bad item suspicion $q_i \in [0,1]$, evidence count, reasons, and last flagged time.
- Ability transition events: `ability_transition_events` stores an audited expected skill gain from doing or reviewing an item. In the current implementation this is not applied to mastery or facet counts.
- Scheduler slate logs: `scheduler_slates` and `scheduler_slate_candidates` store structured scheduler candidate sets for a session, including ranks, reward components, returned rows, selected rows, and the eventual chosen attempt link when available.
- Learning outcome labels: `learning_outcome_labels` stores passive retention and transfer labels that connect a new attempt outcome to up to 20 earlier attempts on the same Learning Object. These labels are for training/evaluation data; they are not an online mastery update.

Important separation: static `PracticeItem.difficulty` is an authored/LLM field in $[0,1]$ used to resolve IRT difficulty $b_i$. Dynamic `practice_item_state.difficulty` is FSRS difficulty $D_i \in [1,10]$. These are unrelated and never substituted for each other.

## 3. End-To-End Attempt Pipeline

A formal attempt starts as an `AttemptDraft` with `practice_item_id`, `learner_answer_md`, `attempt_type`, `hints_used`, and optional latency. Non-recording attempt types `guided_walkthrough` and `skip` are rejected by the formal attempt service.

The attempt target is resolved to a Practice Item, Learning Object, and rubric. If the attempt type is not `dont_know`, it must be allowed by `item.attempt_types_allowed`; `dont_know` is a universal escape hatch and is always accepted. Rubrics come from `item.grading_rubric` or the default rubric for the item's `practice_mode`.

Grading happens before the shared update step. The result is a `ResolvedGrade` containing rubric score, criterion points, grading evidence rows, error attributions, grader confidence, optional self-confidence, and manual review reason.

After grading, `apply_attempt` computes and writes these derived outcomes in one transaction-like service call:

1. Prior mastery $\mu,P$ is loaded or initialized.
2. Static item IRT parameters $(a_i,b_i)$ are resolved.
3. Coverage, facet outcomes, reliability, familiarity discount, local error severity, and error impact are computed.
4. Learning Object mastery is updated by the EKF or the legacy fallback.
5. Surprise is computed from the same observation model.
6. FSRS item memory is updated and a new due time is computed.
7. The attempt row, grading evidence, error events, attempt surprise, practice item state, mastery state, facet recall states, item quality state, ability transition event, and debug payload are persisted. If the attempt has a session id that matches a recent scheduler slate, the attempt is linked to the chosen scheduler slate/candidate. The repository also writes passive `learning_outcome_labels` for recent same-LO source attempts.
8. If the Learning Object has an in-progress probe, `record_probe_attempt` advances the probe.
9. Normal CLI/sidecar practice flows evaluate follow-up/intervention logic and may queue a follow-up or persist an unresolved intervention need.

Replay and regrade use the same `apply_attempt` path. `replay_learning_object` clears derived state for one Learning Object and replays persisted attempts in original timestamp order without calling AI.

## 4. Mastery Math

### 4.1 Initial Mastery

By default a Learning Object starts with $\mu_0=0$, $P_0=1$, evidence count $0$, and no `last_evidence_at`. Therefore the displayed mastery starts at $\sigma(0)=0.5$.

A learner claim can override the initial prior. `initial_mastery_state_for_learning_object` finds the best covering claim by specificity, pseudo-count, claimed level, timestamp, and id. A claim covers a Learning Object if its scope is global, the same Learning Object, the same concept, or a matching subject/domain. If `claimed_level < probe.claim_skip_threshold`, the claim is ignored. Otherwise $m_0=\operatorname{claimed\_level}$, $\mu_0=\operatorname{logit}(m_0)$ with input clipped to $[0.02,0.98]$, and $P_0=1/n_0$ where $n_0=\max(\operatorname{prior\_pseudo\_count},0.25)$.

### 4.2 Static Item Difficulty And Discrimination

For Practice Item $i$, the current implementation resolves one discrimination and one difficulty:

- $a_i = \texttt{mastery.irt.discrimination\_default}$, default $1.0$.
- If `mastery.irt.difficulty_from_prior` is false, $b_i=\texttt{mastery.irt.difficulty\_default}$.
- Otherwise choose $d_i$ from `PracticeItem.difficulty`; if absent, choose `LearningObject.difficulty_prior`; if absent, use `difficulty_default`.
- If $d_i$ exists, $b_i=\operatorname{clamp}(2\,\texttt{difficulty\_prior\_scale}(d_i-0.5),-\texttt{b\_abs\_max},\texttt{b\_abs\_max})$.

With the default `difficulty_prior_scale = 2.5`, $d_i=0$ maps to $b_i=-2.5$, $d_i=0.5$ maps to $b_i=0$, and $d_i=1$ maps to $b_i=2.5$. The clamp default is $|b_i| \le 4.0$.

These parameters are static priors. The backend does not fit $a_i$ or $b_i$ online. The only current difficulty calibration path is the monitor in `services/calibration.py`, which flags persistent one-sided innovations for author review.

### 4.3 Observation Weight

The EKF uses a scalar observation weight $w$. In the current attempt pipeline, `MasteryObservation.observation_weight_override` is set, so `observation_weight` returns this override rather than multiplying the raw fields directly. The override is produced by `resolve_error_impact`:

$w = C_{eff} \cdot \rho_{obs} \cdot S_{err} \cdot F_{ind}$.

The terms are:

- $C_{eff}$: effective coverage from `resolve_coverage`.
- $\rho_{obs}$: observation reliability from `resolve_reliability`.
- $S_{err}$: error sharpening from local error severity, default $1$ when no error is present.
- $F_{ind}$: independent evidence discount from recent same-item, same-surface, and same-facet evidence.

Coverage is intentionally independent of correctness. A `dont_know` can be a high-coverage negative observation. Coverage is computed from authored evidence weights, rubric fallback, or practice-mode defaults, then modified by hints, response engagement, and attempt type:

$C_{item}^{eff}=\operatorname{clamp}(C_{item}\,h_{surface}\,r_{engage}\,a_{coverage})$.

Facet coverage is then allocated as $c_f=C_{item}^{eff}\,\tilde{w}_f$, where $\tilde{w}_f$ is the normalized positive facet weight. The effective coverage is $C_{eff}=\sum_f c_f$.

Reliability is $\rho_{obs}=\operatorname{clamp}(\gamma\,h_{mastery}\,a_{attempt})$, where $\gamma$ is grader confidence, $h_{mastery}$ comes from `hint_policy.mastery_alpha_dampening_by_hint`, and $a_{attempt}$ comes from `ATTEMPT_TYPE_FACTORS`.

The familiarity discount is the product of three component discounts, clamped to `[min_independent_evidence_discount, 1]`. For a component with target discount $q$ and recent overlap mass $M$, the component discount is $1-(1-q)\operatorname{clamp}(M,0,1)$. The configured targets are `same_item_evidence_discount`, `same_surface_family_evidence_discount`, and `same_facet_surface_evidence_discount`.

When an error event exists, local severity $s$ increases observation precision through sharpening, not through a separate additive mastery nudge. With local severity gain $g$ and coverage $C_{eff}$, $S_{err}=\operatorname{clamp}(1+g s C_{eff},1,\texttt{max\_error\_sharpening})$.

### 4.4 2PL Probability-Space EKF

The latent ability for a Learning Object is $\theta \sim N(\mu,P)$ in logit space. The item response model is 2PL:

$p_i(\theta)=\sigma(a_i(\theta-b_i))$.

The observed score fraction is $y=\operatorname{clamp}(\texttt{rubric\_score}/\max(\texttt{max\_points},1),0,1)$.

Before the observation update, variance drifts with elapsed time since last evidence:

$P^- = \min(P + \sigma_d^2 \Delta t, P_{max})$,

where $\sigma_d^2=\texttt{mastery.sigma2\_drift}$, default $0.01$ per day, and $P_{max}=\texttt{mastery.p\_max}$, default $4.0$.

The EKF linearizes the 2PL link at $\mu$:

- $p=\operatorname{clamp}(\sigma(a_i(\mu-b_i)),\epsilon_p,1-\epsilon_p)$.
- $H=a_i p(1-p)$.
- $R_y=\texttt{base\_observation\_variance}\cdot p(1-p)/\max(w,0.10)$.
- $S=H^2P^-+R_y$.
- $K=P^-H/S$.
- $\mu_{raw}=\mu+K(y-p)$.
- $P^+=(1-KH)P^-$.

The implementation then caps the mean step and clamps the mean:

- If $|\mu_{raw}-\mu| > \texttt{max\_logit\_step}$, replace the step with that cap while preserving sign.
- Clamp the resulting mean to $[-\texttt{mu\_abs\_max},\texttt{mu\_abs\_max}]$.

The stored posterior is $\mu^+$, $P^+$, incremented evidence count, and updated timestamps. The debug trace stores item id, $a$, $b$, $\theta$ prior, expected correctness $p$, predicted score, $y$, innovation $y-p$, $H$, Fisher information $aH=a^2p(1-p)$, $R_y$, $S$, $K$, variance reduction $KH$, before/after means, step cap flags, and before/after probabilities.

Interpretation: the mean move follows the realized innovation $y-p$, so a hard correct answer moves $\mu$ up more than an easy correct answer. The variance reduction follows sensitivity $H$, so confidence gain is largest near the learner's boundary.

### 4.5 Legacy Fallback

If `mastery.irt.enabled = false`, the backend uses the legacy logit-space Kalman update. It computes $z=\operatorname{logit}(\operatorname{clamp}(y,0.02,0.98))$, $R_z=\texttt{base\_observation\_variance}/\max(w,0.10)$, $K=P^-/(P^-+R_z)$, $\mu^+=\mu+K(z-\mu)$, and $P^+=(1-K)P^-$. The fallback is kept for reproducibility and is not the default.

## 5. FSRS Item Memory

FSRS is per Practice Item. It answers a different question from LO mastery: whether this specific item should be reviewed now. LearnLoop implements FSRS-6 locally in `services/fsrs.py` using pinned weights:

`(0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542)`.

The rating is derived from rubric score ratio $r=\texttt{score}/\max(\texttt{max\_points},1)$:

- $r<0.25$: `again`.
- $0.25 \le r < 0.60$: `hard`.
- $0.60 \le r < 0.90$: `good`.
- $r \ge 0.90$: `easy`.

Hints can cap the rating through `hint_policy.fsrs_rating_cap_by_hint`. For example, if one hint caps the rating at `good`, a nominal `easy` becomes `good` before FSRS is applied.

For a new item, FSRS initializes $S$ and $D$ from the rating. `initial_stability` returns $w_{rating-1}$ with lower bound $S_{min}=0.001$. `initial_difficulty` returns $\operatorname{clamp}(w_4 - \exp(w_5(rating-1)) + 1,1,10)$.

For an existing item, retrievability is $R(t)=(1+f\,t/S)^{-d}$ with $d=w_{20}$ and $f=0.9^{1/(-d)}-1$, clamped to $[0,1]$. Dynamic difficulty updates as $D'=\operatorname{clamp}(w_7D_{easy}+(1-w_7)(D-w_6(rating-3)),1,10)$.

If the rating is `again`, stability updates with `next_forget_stability`: $S'=\max(w_{11}D^{-w_{12}}((S+1)^{w_{13}}-1)\exp((1-R)w_{14}),S_{min})$.

For `hard`, `good`, or `easy`, stability updates with `next_recall_stability`: $S'=\max(S(1+\exp(w_8)(11-D)S^{-w_9}(\exp((1-R)w_{10})-1)h e),S_{min})$, where $h=w_{15}$ for `hard` otherwise $1$, and $e=w_{16}$ for `easy` otherwise $1$. For `hard`, the implementation caps $S'$ at at most the previous $S$.

The nominal interval for desired retention $q$ is $I=S(q^{1/(-d)}-1)/f$, with default desired retention $q=0.9$.

LearnLoop then multiplies this interval by the surprise interval factor from the mastery/surprise model: $I_{final}=I\cdot F_{surprise}$. The due timestamp is the observed attempt time plus $I_{final}$ days. This is the main coupling between FSRS and the novel mastery model: FSRS owns per-item spacing, but Bayesian surprise can shorten or lengthen the next interval.

## 6. Surprise And Follow-Up Signals

Surprise is computed after mastery posterior update using the prior, posterior, same mastery observation, and same static item $(a,b)$.

With IRT enabled, the standardized residual is $z=(y-p)/\sqrt{S}$, where $p$ and $S=H^2P^-+R_y$ come from the same EKF observation. With IRT disabled, the residual is the legacy logit residual $(z_{obs}-\mu)/\sqrt{P+R_z}$.

Predictive surprise is $0.5(z^2+\log(2\pi S))$. Bayesian surprise is the KL divergence between the posterior and prior univariate Gaussians in logit space: $0.5(\log(P/P^+) + P^+/P + (\mu-\mu^+)^2/P - 1)$.

The FSRS interval factor is $F_{surprise}=\operatorname{clamp}(\exp(\alpha z),F_{min},F_{max})$, with `alpha_interval = 0.3`, `f_min = 0.5`, and `f_max = 1.5` by default. Positive residuals lengthen the next interval; negative residuals shorten it.

The predicted error type distribution is a decayed categorical distribution over active errors plus a `null` baseline. It starts with weight $1$ on `null`. Each active error contributes $s_E\exp(-\Delta t/7)$ to its error type. The weights are normalized.

Surprise direction is:

- `negative` if the observed error type is present and its predicted probability is below `epsilon_error_surprise`.
- Otherwise `positive` if residual $z > \theta_{pos}$.
- Otherwise `negative` if $z < -\theta_{neg}$.
- Otherwise `none`.

Defaults are `theta_pos = 1.5`, `theta_neg = 1.5`, and `epsilon_error_surprise = 0.05`.

Intervention follow-up logic reads surprise, local severity, repeated failures, high unfamiliar posterior, grader confidence, time availability, and session caps. Current trigger thresholds include `tau_followup_nats = 0.05`, `gamma_min = 0.5`, `tau_severe_error = 0.75`, `tau_repeated_item_failures = 2`, `tau_repeated_facet_failures = 2`, `tau_unfamiliar_intervention = 0.85`, and `cold_start_min_lo_evidence = 2.0` through config defaults.

All follow-up triggers except `high_unfamiliar_posterior` require that the attempt wrote an error event. Low grader confidence, no remaining time, and per-LO session caps suppress follow-up. If a trigger remains, the service chooses an intent of `probe`, `guided_reconstruction`, `repair`, or `review`. It can queue a follow-up Practice Item by adding an action to `attempt_surprise.triggered_actions_json`, or persist an `intervention_need` if no alternate same-LO item exists. Existing-item selection currently considers alternate Practice Items on the same Learning Object and ranks them by target-facet overlap, scaffold bonus for repair/guided reconstruction, bad-item suspicion, and id. The `candidate_requirements` JSON is recorded on unresolved needs for later diagnostic generation; it is not enforced while choosing an existing follow-up item.

Pending `intervention_needs` are now an authoring input. `generate-diagnostics` reads pending needs, resolves their target facets and source Practice Item context, estimates a recommended difficulty band from aggregate facet recall or mastery, and asks the authoring provider to propose one reviewed diagnostic Practice Item per need. The generated proposal must stay on the same Learning Object, honor `candidate_requirements`, avoid duplicating the source prompt, use `practice_mode = diagnostic_probe`, and localize evidence to the target facets. After the proposal batch is queued, each targeted need is marked `fulfilled` with blocked reason `diagnostic_proposal_queued:<proposal_id>`.

## 7. Facet Recall, Coverage, And Error Severity

Practice Items can define evidence facets. Facets let the system say that a learner remembered one part of a Learning Object but missed another.

The coverage source order is:

1. Authored `evidence_weights` if present.
2. Rubric-derived coverage if the item has a rubric.
3. Practice-mode defaults.

Practice-mode coverage defaults are `constructed_response = 0.85`, `open_text = 0.85`, `short_answer = 0.75`, `diagnostic_probe = 0.80`, `independent_attempt = 0.75`, `hinted_attempt = 0.65`, `multiple_choice = 0.45`, and `self_report = 0.25`.

Attempt-type coverage factors are `dont_know = 1.0`, `independent_attempt = 1.0`, `open_text = 1.0`, `diagnostic_probe = 1.0`, `hinted_attempt = 0.90`, `reconstruction_after_walkthrough = 0.60`, `self_report = 0.30`, `guided_walkthrough = 0.0`, and `skip = 0.0`.

Attempt-type reliability factors are `independent_attempt = 1.0`, `open_text = 1.0`, `diagnostic_probe = 1.0`, `hinted_attempt = 1.0`, `reconstruction_after_walkthrough = 0.5`, `dont_know = 0.7`, `self_report = 0.3`, `guided_walkthrough = 0.0`, and `skip = 0.0`.

Facet outcomes use criterion-facet mappings when possible. For each facet $f$, the service loops over rubric criteria $c$. It normalizes the criterion's facet map, computes criterion correctness $o_c=\operatorname{clamp}(points_c/max_c)$, weights the criterion by $points_c/max\_points$, and computes $o_f=\operatorname{clamp}(\sum_c weight_c share_{cf} o_c / \sum_c weight_c share_{cf})$. If an item has exactly one evidence facet, every rubric criterion maps to that facet. Otherwise, authored `criterion_facet_weights` are authoritative; missing mappings use a conservative lexical fallback from criterion ids/descriptions to facet ids. If no criterion maps to a facet but an error attribution targets that facet through its evidence family, the outcome is $0$. If neither mapping nor attribution applies, the fallback is whole-item correctness. A `dont_know` forces $o_f=0$ for all covered facets.

For every covered facet and for two scopes, aggregate `(learning_object_id, facet_id, NULL)` and item-local `(learning_object_id, facet_id, practice_item_id)`, the Beta state update is:

- prior defaults: $\alpha=1$, $\beta=1$.
- discounted weight: $w_f=c_fF_{ind}$.
- $\alpha' = \alpha + w_f o_f$.
- $\beta' = \beta + w_f(1-o_f)$.
- mean $=\alpha'/(\alpha'+\beta')$.
- variance $=\alpha'\beta'/((\alpha'+\beta')^2(\alpha'+\beta'+1))$.
- independent evidence mass adds $w_f$.
- raw coverage mass adds $c_f$.
- consecutive failures increments if $o_f<0.40$, otherwise resets to $0$.

Error severity is frozen at event write time. For error type $E$, the local severity starts from the grade-provided severity, taxonomy default, or fallback $0.5$. It then adds and subtracts attempt-local components:

$s_E = \operatorname{clamp}(s_0 + 0.12(1-correctness) + 0.10\hat{p} + 0.08C_{eff} + \min(0.25,0.15n_{item}) + \min(0.20,0.10n_{facet}) + \min(0.10,0.05n_E) + 0.05\mathbf{1}_{dont\_know} + 0.08m_{failed\_facets} - 0.04hints - \min(0.20q_i,\texttt{mitigation\_cap}))$.

Here $\hat{p}$ is predicted correctness, $n_{item}$ is recent same-item failures, $n_{facet}$ is recent failures sharing target facets, $n_E$ is recent same-error events, $m_{failed\_facets}$ is the mass of covered facets with outcome below $0.40$, and $q_i$ is prior bad item suspicion.

## 8. Probes

A probe is not a different attempt database row. It is a phase around a Learning Object where normal Practice Items are chosen for diagnostic information gain, and every completed attempt on that Learning Object advances a locked Bayesian hypothesis set.

### 8.1 Why Probes Exist

Cold Learning Objects have no evidence. The scheduler normally excludes cold Learning Objects unless they are in an in-progress probe phase. `sync_vault_state` enters an initial probe for an active Learning Object if it has no evidence and has an active local Practice Item, or if it is connected to an active goal and has a local Practice Item. If there is no local item, the system logs an elicitation event with fallback outcome `existing_pi_inadequate`.

Probes have four roles:

1. Estimate initial mastery and uncertainty for a Learning Object.
2. Decide whether the learner is mastered, unfamiliar, or affected by a known misconception.
3. Drive early item selection using expected information gain rather than only FSRS due dates.
4. Mark when enough diagnostic evidence exists so the system can generate additional practice coverage.

### 8.2 Hypothesis Set Construction

`enter_probe` locks a `HypothesisSet` for the probe phase. The set always begins with `mastered` and `unfamiliar`. If current mastery mean is $m=\sigma(\mu)$, the initial unnormalized weights are $m$ and $1-m$, each floored at $10^{-6}$.

Misconception hypotheses are added from active misconception error events on the Learning Object and from `confusable_with` neighbor concepts. An active misconception error contributes weight $s_E\exp(-\Delta t/7)$. Neighbor misconceptions are included only when the neighbor Learning Object mastery is at least $0.7$; the most severe active misconception from that neighbor is used. The hypothesis set is capped by `probe.hypothesis_set_max_size`, default $5$, dropping the lowest-severity misconceptions first.

The prior is normalized and written to `hypothesis_sets`. It stays locked for the phase. Live posterior evidence is replayed against that locked set; the set itself is not mutated mid-probe.

Probe target attempts default to `probe.attempts_target_default = 3`. If a covering learner claim has `claimed_level >= probe.claim_skip_threshold`, the target becomes `probe.attempts_target_with_strong_claim = 1`.

### 8.3 Probe Conditional Outcome Model

Probe outcomes live in the space $o=(s,E)$, where score bucket $s \in \{low,mid,high\}$ and error type $E$ is either `null` or a known error type from the locked hypothesis set.

A score bucket is derived from rubric score: scores $0$ and $1$ are `low`, scores $2$ and $3$ are `mid`, and score $4$ is `high`.

For a hypothesis and item, define $\eta=a_i(\theta_h-b_i)$. The graded bucket marginals are:

- $P(low)=1-\sigma(\eta-c_{mid})$.
- $P(mid)=\sigma(\eta-c_{mid})-\sigma(\eta-c_{high})$.
- $P(high)=\sigma(\eta-c_{high})$.

Defaults are $c_{mid}=-1$, $c_{high}=1$, $\theta_{mastered}=2$, and $\theta_{unfamiliar}=-2$.

Conditional rules:

- `mastered`: use $\theta_{mastered}$ and put all bucket mass on `null` error.
- `misconception:E` when the item rubric does not have fatal error `E`: treat it like mastered for this item, because the item does not probe that misconception.
- `unfamiliar`: use $\theta_{unfamiliar}$. Put mid and high mass on `null`. Put low mass mostly on `null`, but leak `unfamiliar_error_leak` across known error channels. Default leak is $0.20$.
- `misconception:E` when the item probes `E`: use $\theta_{unfamiliar}$. Route low mass to `E` with fraction `err_low_frac = 0.80` and low null with the remainder. Route mid mass to `E` with fraction `err_mid_frac = 0.50` and mid null with the remainder. High mass goes to null.

This corrected rule is important: on an item that actually probes error `E`, `(low,E)` confirms `misconception:E` rather than merely confirming `unfamiliar`.

### 8.4 Expected Information Gain

For a candidate item, the model computes $P(o|h,i)$ for every hypothesis $h$. The mixture is $P(o|i)=\sum_h \pi_hP(o|h,i)$. Expected information gain is:

$EIG(i)=\sum_h \pi_h \sum_o P(o|h,i)\log(P(o|h,i)/P(o|i))$.

The scheduler component is normalized as $EIG(i)/\log(|H|)$ when there is more than one hypothesis. During scheduling this raw component is multiplied by prospective independent evidence discount, so repeating the same item or surface has less diagnostic value.

Probe EIG appears in legacy priority as `scheduler.probe_eig_weight * probe_eig`, with default weight $0.25$. Short sessions suppress probe EIG unless the item otherwise has zero priority and probe EIG is the only way to surface it.

The scheduler also records `elicitation_events` for selected probe items, including candidate scores, expected information gain, hypothesis set id, and selected reason.

### 8.5 Probe Posterior Update

Probe posterior is recomputed statelessly from persisted attempts. Starting from the locked prior, each attempt multiplies by the likelihood and normalizes:

$P(h|o_{1:t}) \propto P(h|o_{1:t-1})L_t(h)$.

Normally $L_t(h)=P(s_t,E_t|h,i_t)$ if the observed error type is represented. If the joint outcome is impossible or unknown, the update falls back to score-bucket marginal $P(s_t|h,i_t)$ so a single odd label cannot zero the entire posterior.

The realized information gain is $H(prior)-H(posterior)$ in nats, clamped at zero. Normalized realized information gain divides by $\log(|H|)$.

After each probe attempt, misconception posterior marginals are persisted to `learner_state_beliefs` with variance $p(1-p)$, evidence count equal to probe-phase attempt count, and last surprise equal to posterior minus prior.

### 8.6 Self-Attributed Misconceptions

Learners can self-attach a misconception during self-grading. This affects probes in two ways.

First, if the self-attached error type is already in the locked hypothesis set but not in the item's rubric fatal errors, the posterior uses a trust-weighted label mixture:

$L(h)=w_{self}P_{probe}(s,E|h)+(1-w_{self})P_{marg}(s|h)$.

Here $P_{probe}$ is computed as if the item probes `E`, and $P_{marg}$ is the current score-bucket marginal ignoring the self-tag label. If $w_{self}=1$, the label is trusted like a rubric fatal error. If $w_{self}=0$, the attempt updates only from the score bucket.

The trust weight is zero for a high score. Otherwise $w_{self}=\min(w_{max},w_{base}c_{eff})$, with defaults `w_base = 0.5` and `w_max = 0.7`. The closeness term is $c_{eff}=\rho c_{raw}+(1-\rho)$. $c_{raw}$ is graph hop closeness from the item's concept to the error type's related concepts, using hop decay from cross-LO propagation. $\rho$ increases with graph density and local linkability, so sparse graphs fall back toward neutral trust instead of punishing missing edges.

Second, repeated self-tags can promote an item into a durable probe for that misconception. `maybe_promote_self_tagged_fatal_error` queues a reviewed rubric update when a misconception appears on the same item at least `probe.self_tag.promotion_threshold = 3` times, the error type exists and is marked as a misconception, and the item does not already have that fatal error. The proposal is always `review_required`.

### 8.7 Probe Completion

`record_probe_attempt` increments completed attempts after any formal attempt on an in-progress probe Learning Object. A probe completes when any of these conditions holds:

- completed attempts reach `probe_attempts_target`;
- mastery logit variance $P_\ell$ is at most `probe.variance_convergence_threshold`, default $0.10$;
- the hypothesis posterior top probability is within that same threshold of $1$, meaning $1-\max_hP(h) \le 0.10$.

The probe state records converged families such as `mastery` or `hypothesis` and completion time.

## 9. Practice Items

Practice Items are the main learning actions after the initial diagnostic probe. A Practice Item links to one Learning Object and contains the prompt, expected answer, attempt types, rubric, hints, difficulty prior, and reward-facing metadata.

Important item fields:

- `learning_object_id`: the Learning Object whose mastery and facet recall are updated.
- `practice_mode`: surface category such as `constructed_response`, `open_text`, `short_answer`, or `diagnostic_probe`.
- `attempt_types_allowed`: formal attempt types the item accepts. `dont_know` is accepted globally even if absent.
- `prompt` and `expected_answer`: shown to learner and passed to grading.
- `grading_rubric`: criteria and fatal errors. Criteria determine point validation and can map to facets. Fatal errors cap rubric score and can represent misconceptions.
- `difficulty`: authored/LLM prior $d_i \in [0,1]$ used to resolve IRT $b_i$.
- `evidence_facets`, `evidence_weights`, `criterion_facet_weights`: define the knowledge surface and how rubric evidence localizes to facets.
- `retrieval_demand`: how much unaided recall the item demands, $[0,1]$.
- `transfer_distance`: how far the item is from previously seen forms, $[0,1]$.
- `scaffold_level`: how much support the item provides, $[0,1]$.
- `surface_family`: stable label for repeated or near-repeated item surfaces.
- `repair_targets`: facets or fatal error ids that this item can repair.
- `hint_policy`: rating caps and dampening for hints.

Practice Items update all three belief layers: the item-specific FSRS memory, Learning Object mastery, and facet recall. They can also generate error events, item-quality evidence, and follow-up actions.

Post-probe practice generation is deliberately gated. `generate-practice` targets active Learning Objects with `lo_probe_state.status = complete` whose active Practice Item count is below `target_items_per_lo` (default CLI value $5$). It asks the authoring provider to create only Practice Items, exactly the requested count per target, and to vary facets, difficulty, and expected answer shape.

Diagnostic practice generation is separate from normal post-probe expansion. `generate-diagnostics` targets pending `intervention_needs`, not completed probes. Each target carries the need id, Learning Object, trigger reason, desired intent, target facets, source Practice Item prompt and expected answer when available, candidate requirements, current mastery, aggregate facet recall means/variances, and a recommended difficulty band. The band is `(0.25,0.45)` for low ability, `(0.45,0.65)` around the boundary, and `(0.60,0.80)` for stronger facet state. The authoring provider is instructed to create exactly one `diagnostic_probe` Practice Item per need, with high retrieval demand, low-to-moderate transfer distance, low scaffold level, `evidence_facets` equal to the target facets, normalized `evidence_weights`, `repair_targets` equal to target facets, and rubric criteria mapped through `criterion_facet_weights`. These proposals are always `review_required`.

## 10. Estimating Current Skill

The current skill estimate is composite, not one scalar.

### 10.1 Learning Object Skill

The primary scalar for a Learning Object is $m_\ell=\sigma(\mu_\ell)$. The uncertainty shown for that display value is $V_m=(m_\ell(1-m_\ell))^2P_\ell$. This is what `display_mastery` returns.

### 10.2 Facet Skill

For evidence facet $f$, recall skill is the Beta posterior mean $\alpha_{\ell f}/(\alpha_{\ell f}+\beta_{\ell f})$. Its uncertainty is the Beta variance. Aggregate facet rows with `practice_item_id = NULL` represent the Learning Object facet estimate. Item-local rows represent how the learner performs on that particular item/surface.

### 10.3 Item Memory

For Practice Item $i$, FSRS retrievability $R_i(t)$ estimates whether the learner can retrieve that item now. Scheduler forgetting risk is computed only for due or overdue items: if an item is not due, risk is $0$; if due, risk is $1-R_i(t)$, or $1$ when stability is unavailable.

### 10.4 Misconceptions

There are two misconception signals:

- Active error events, used directly by scheduling and selection reward. In `ability_vector`, active misconception severities are normalized by total active error severity to form `misconception_posterior_by_error_type`.
- Probe posteriors, persisted to `learner_state_beliefs`. These are categorical Bayesian beliefs over locked probe hypotheses and are used by probe replay/debug surfaces and future belief inspection.

### 10.5 Ability Vector And Predicted Correctness

`selection_rewards.ability_vector` produces a scheduler-facing skill vector:

- `lo_mastery = \sigma(\mu_\ell)` or $0.5$ if missing.
- `lo_mastery_variance = clamp(P_\ell)` or $1$ if missing.
- facet recall means, variances, and independent evidence masses from aggregate facet rows.
- normalized active misconception severities.

`item_demand_vector` resolves item demand:

- evidence weights;
- $a_i,b_i$;
- retrieval demand, transfer distance, scaffold level;
- surface family;
- misconception targets from rubric fatal errors;
- repair targets;
- bad item suspicion.

The selection predicted correctness is:

$p_{IRT}=\sigma(a_i(\operatorname{logit}(m_\ell)-b_i))$.

Facet readiness is the evidence-weighted facet mean, defaulting to LO mastery. A facet variance aggregate is converted into a blend weight $\lambda=\operatorname{clamp}(V_f/\max(\texttt{facet\_blend\_evidence\_count},0.1))$. The base prediction is $(1-\lambda)p_{IRT}+\lambda r_f$. The final prediction is:

$\hat{p}=\operatorname{clamp}(base + 0.12\,scaffold - 0.15\,retrieval\,\max(0,0.55-r_f) - 0.10\,badItemSuspicion)$.

The attempt debug path has a similar `recall_coverage.predicted_correctness`, but it uses independent evidence mass to set the facet blend and slightly different adjustments: scaffold $+0.10\,scaffold$ and retrieval $-0.10\,retrieval(1-r_f)$.

## 11. Scheduling And Selection

`build_due_queue` constructs candidates from active Practice Items. It skips inactive items, items without a Learning Object, and cold Learning Objects unless they are in an in-progress probe.

The legacy priority components are:

$priority = w_F F_i + w_G G_\ell + w_E E_\ell + w_P PIG_i$.

Defaults are `forgetting_risk_weight = 1.0`, `active_goal_weight = 0.35`, `recent_error_weight = 0.50`, and `probe_eig_weight = 0.25`.

- $F_i$ is FSRS forgetting risk.
- $G_\ell$ is active goal weight. A goal affects its anchor concepts and one-hop `prerequisite` or `part_of` targets.
- $E_\ell$ is recent error boost, the max over active errors of $s_E\exp(-\Delta t/7)$.
- $PIG_i$ is discounted normalized probe expected information gain, only in probe phases.

Items with non-positive legacy priority are normally excluded. There is one exception: if an item targets a facet with existing aggregate recall state and that facet is weak while the item is near the learner's predicted correctness boundary, the scheduler assigns a small `boundary_target` priority. This lets a targeted spectral-norm diagnostic item surface even when it is not due under FSRS. For remaining items, selection reward is computed and the queue is sorted primarily by `selection_reward`, secondarily by priority, then item id.

Selection intent is chosen as:

- `probe` if in probe phase and probe EIG is positive;
- `practice` for diagnostic probes outside an active probe phase, unless they are repair items with a recent error;
- `repair` if recent error is positive and the item has repair targets;
- `transfer` if transfer distance is positive;
- otherwise `practice`.

Selection reward terms:

- For `probe`: $0.70$ normalized total probe information reward, $0.10$ LO mastery variance, $0.10$ facet uncertainty, $0.10$ active goal, minus duplicate probe penalty.
- For `repair`: $0.30$ repair value, $0.25$ gradient fit, $0.20$ facet weakness, $0.10$ targeted boundary fit, $0.15$ normalized expected skill gain, $0.10$ recent error, minus overload and repetition fatigue.
- For practice/transfer/review: $0.20$ forgetting risk, $0.15$ active goal, $0.20$ facet weakness, $0.20$ gradient fit, $0.15$ targeted boundary fit, $0.10$ normalized expected skill gain, $0.05$ transfer distance, minus overload and repetition fatigue.

Gradient fit rewards predicted correctness in an intent-specific target band. Probe targets $0.40$ to $0.60$, repair targets $0.75$ to $0.90$, transfer targets $0.60$ to $0.80$, and normal practice targets $0.55$ to $0.75$. Outside the band, fit decays linearly to zero over distance $0.40$.

Targeted boundary fit is `facet_weakness * gradient_fit`, but only over demanded facets that already have aggregate facet recall state. It does not make completely unobserved facets eligible by itself.

The expected skill gain used in reward is audited by `estimate_ability_transition` but not applied as evidence. Diagnostic probes have expected gain $0$. A `dont_know`, hinted attempt, or item with an error event has gain $0.04+0.04(1-correctness)$, capped at $0.08$. Otherwise successful practice has gain $0.02 correctness$.

Seeded exploration exists but defaults to off. If `selection_exploration_rate > 0`, a session-id and date keyed hash can choose an alternative within `selection_exploration_reward_window`, excluding probe items.

Pending follow-up Practice Items are inserted at the front with priority above the current max and an `intervention_followup` component. Legacy rows with `negative_surprise_followup` are still read for compatibility.

When `persist_explanations` is enabled and the scheduler session has a session id, `build_due_queue` writes both legacy `scheduler_explanations` rows and structured `scheduler_slates` / `scheduler_slate_candidates` rows. Later attempts with the same session id are linked back to the most recent matching slate candidate when the attempt is recorded.

## 12. Grading

Grading converts a learner answer into a rubric score, criterion evidence, error attributions, and confidence.

### 12.1 Self Grading

CLI/self grading supplies criterion points, confidence $1..5$, optional fatal errors, optional legacy single `error_type`, optional notes, and optional per-criterion self-attributed errors.

Self confidence maps to grader confidence as $1 \to 0.2$, $2 \to 0.4$, $3 \to 0.6$, $4 \to 0.8$, and $5 \to 1.0$. Self grades below $0.4$ confidence produce manual review reason `low_self_confidence`.

Criterion points are validated against rubric criteria. Unknown criteria, negative points, and points above the criterion max are rejected.

Rubric score is $round(\sum_c points_c)$, clamped to $[0,\min(max\_points,4)]$. Fatal errors then cap the score using their `max_grade`. The final score is again clamped to $[0,4]$.

A `dont_know` attempt overrides the self grade: all criterion points become $0$, fatal errors are cleared, per-criterion attributions are cleared, and the error type is deterministic. With zero hints it is `recall_failure`; with hints it is `scaffold_failure`.

Self-attributed error sources are merged in priority order: fatal errors, legacy single `error_type`, then per-criterion attributions. They are deduplicated by error type. Severity and misconception status come from `errors/error_types.yaml`, falling back to severity $0.5$ and `is_misconception = false` for unknown types.

### 12.2 AI/Codex Grading

AI/Codex grading builds a `GradingContext` containing attempt id, practice item id, prompt, expected answer, learner answer, resolved rubric, item evidence facets, evidence weights, criterion-facet weights, and the current error taxonomy guidance. The context hash is stored in `agent_runs`. The provider returns a `GradingProposal` with rubric score, criterion evidence, fatal errors, error attributions, grader confidence, manual review recommendation, optional feedback, and repair suggestions.

The grading prompt version is `mvp-0.3-grading-canonical-errors`. It tells the provider to prefer five canonical error types for ordinary grading:

- `recall_failure`: the learner explicitly cannot retrieve the requested fact, formula, step, or facet.
- `conceptual_slip`: the answer reveals a wrong definition, relationship, interpretation, or mental model.
- `procedure_misapplication`: the learner chooses the wrong rule, formula, algorithm step, retained/discarded case, or condition.
- `arithmetic_slip`: the setup and concept are correct, but arithmetic, algebra, sign, indexing, or simplification is locally wrong.
- `incomplete_answer`: the answer is partially correct but omits a required value, justification, condition, unit, or explanation.

Rubric fatal error ids and vault-specific taxonomy ids are still allowed when they apply more precisely. A new error type should be proposed only for a durable, specific misconception not covered by the canonical ids, rubric fatal ids, or vault taxonomy. Explicit "I don't know", "I don't remember", or "I can't recall" language for a requested part is normalized to `recall_failure`; the system does not treat model-invented names such as `missing_spectral_norm_error` as new taxonomy when the evidence is an explicit recall failure.

Validation requires:

- returned `attempt_id` equals the expected attempt id;
- returned `practice_item_id` equals the item id;
- every criterion id is known and not duplicated;
- criterion points are within `[0, criterion.points]`;
- fatal error ids are known;
- fatal errors correctly cap the rubric score;
- error severities are either provided in `[0,1]` or resolved from taxonomy;
- `target_evidence_families` resolve to item evidence facets;
- `target_criterion_ids` resolve to rubric criteria and are mapped back to evidence facets through criterion-facet weights.

Manual review reason is `codex_manual_review` when the model recommends review, `low_grader_confidence` when confidence is below $0.4$, `unknown_target_evidence_family:<ids>` for unknown facet targets, `unknown_target_criterion:<ids>` for unknown rubric-line targets, or `unknown_error_type:<ids>` when attributions name unknown taxonomy ids after canonical normalization.

If configured for fallback and the provider is unavailable or validation fails, the system records a self-graded attempt with fallback reason. Required grading mode raises instead.

Deferred regrade reuses the same grading context and validation. If a regrade changes the score by at least two points, a `regrade_disagreement` content event is written. Then `replay_learning_object` rebuilds derived state so mastery, FSRS, facet recall, surprise, and errors are consistent with the new grade.

## 13. Observation Templates And Events

An observation template is a reusable schema for learning evidence that originates outside the normal Today/practice attempt UI. It defines the expected response fields for a kind of external observation and, optionally, how those fields should be converted into a normal self-graded Practice Item attempt. Typical uses are imported quiz results, worksheet checks, oral recall checks, tutor notes, manual rubric observations, or other structured evidence that should be stored consistently without forcing the learner through the live practice screen.

Observation templates separate two concepts:

- The observation event itself: a durable record that something was observed, with a template id, response payload, binding mode, subject/session metadata, and optional related Learning Object or Practice Item.
- An emitted attempt: an optional algorithmic learning update created only when the template declares an `emits` block and the caller provides a resolved Practice Item binding.

This separation lets LearnLoop preserve ambiguous or external evidence even when it cannot safely turn that evidence into mastery/FSRS/facet updates yet. It also prevents the system from guessing which Practice Item an external observation should affect.

Observation templates are currently a CLI-facing intake path. `register-observation-template` validates template YAML and stores it in `observation_templates`. `record-observation` loads the template, validates the response, writes an `observation_events` row, and records subject/session/related entity ids when supplied.

If the template has an `emits` block and the caller supplies `related_practice_item_id`, the observation emits a self-graded attempt through `complete_self_graded_attempt`; the emitted attempt then uses the shared attempt pipeline and can update mastery, FSRS item memory, facet recall, item quality, surprise, and probe progress. If an emitting template is recorded without a bound Practice Item, the event is stored with binding mode `pending` and no attempt is emitted. Non-emitting templates only record the observation event. The current `record-observation` CLI path does not run post-attempt intervention follow-up after an emitted attempt.

## 14. Question Authoring

Questions are authored as Practice Items through proposal services. The backend never lets the model write YAML directly. It asks for an `AuthoringProposal`, validates every item, persists the proposal in SQLite, and applies accepted items through vault writer services.

### 14.1 Authoring Context

`build_authoring_context` deterministically assembles:

- selected subjects;
- note excerpts filtered by id or subject;
- supplied source refs;
- existing concepts;
- existing Learning Objects;
- existing Practice Items with prompt excerpts;
- active goals;
- optional user instructions.

The context is hashed and recorded in `agent_runs` with prompt version `mvp-0.2-authoring-difficulty`.

### 14.2 Authoring Prompt Requirements

The authoring prompt tells the provider to return schema-valid JSON only. It requires difficulty estimates:

- Practice Item `difficulty` and Learning Object `difficulty_prior` use a $[0,1]$ anchor scale.
- $0.0$ to $0.2$ means trivial or recognition.
- $0.2$ to $0.4$ means easy recall.
- $0.4$ to $0.5$ means basic application.
- $0.5$ means normal target-level.
- $0.6$ to $0.8$ means transfer or multi-step.
- $0.8$ to $1.0$ means difficult synthesis or adversarial.
- Estimated fields should set `difficulty_source = "llm_estimate"`.

For every generated Practice Item, the prompt requires reward-facing metadata: `evidence_facets`, `evidence_weights`, `criterion_facet_weights` when a rubric exists, `retrieval_demand`, `transfer_distance`, `scaffold_level`, `surface_family`, and `repair_targets`. `repair_targets` must name evidence facets or rubric fatal error ids.

### 14.3 Proposal Schema

Authoring proposals can create, update, or deactivate these entity types: `learning_object`, `practice_item`, `concept`, `concept_edge`, `rubric`, and `error_type`.

A Practice Item proposal payload can include id, Learning Object id, subjects, practice mode, attempt types, prompt, expected answer, rubric, evidence facets and weights, criterion-facet weights, difficulty, difficulty source, retrieval demand, transfer distance, scaffold level, surface family, repair targets, hints, hint policy, and tags.

A Learning Object proposal payload can include title, concept id, subjects, knowledge type, status, contradiction target, summary, prerequisites, confusables, difficulty prior, difficulty source, and tags.

### 14.4 Validation And Review Policy

Validation rejects or warns on:

- `review_route = reject`;
- unresolved source refs;
- duplicate ids on creates;
- missing required fields;
- missing Learning Object or concept references;
- unsupported attempt types;
- missing rubric when no default rubric exists;
- generated Practice Items missing evidence facets, reward metadata, repair targets, or generated audit;
- evidence weights for unknown facets;
- criterion-facet weights for unknown criteria or unknown facets;
- invalid concept edges.

Auto-apply is narrowly scoped. It is allowed only for create operations on Learning Objects, Practice Items, or concept edges when the item is directly source-grounded, has resolvable refs, has no id collision, passes validation, and passes generated audit checks. Otherwise the item remains `review_required`. Review-required items are persisted for human acceptance, editing, or rejection.

Accepted proposal items are compiled into vault writes through `vault.writer` helpers such as `upsert_learning_object` and `upsert_practice_item`. Proposal application records change batches and content events, then syncs derived SQLite state.

### 14.5 Practice Generation After Probes

`generate_post_probe_practice_proposal` scans completed-probe Learning Objects and counts active Practice Items. It requests more items only when active count is below `target_items_per_lo`. Its instructions tell the provider to create only Practice Items, attach them to specified target Learning Objects, prefer constructed response with `open_text` attempts unless another supported type is clearly needed, avoid duplicate prompts, and create exactly the requested number per target.

This is how probes and practice items pair in authoring: probes establish initial diagnostic state and identify gaps; post-probe generation fills out the practice surface with more varied items.

### 14.6 Diagnostic Generation From Intervention Needs

`generate_diagnostic_practice_proposal` scans pending `intervention_needs` and builds a `DiagnosticPracticePlan`. This plan is narrower than post-probe expansion: it exists to create a diagnostic item for a known gap when the scheduler could not find a suitable existing item.

Each target includes:

- the pending need id;
- Learning Object id, title, subject ids, and concept id;
- desired intent and trigger reason;
- target facets, canonicalized through the vault;
- source Practice Item id, prompt, and expected answer when available;
- candidate requirements recorded on the need;
- current display mastery and aggregate facet recall means/variances;
- a recommended difficulty band.

The provider instructions require exactly one Practice Item per need. The item must use `practice_mode = diagnostic_probe`, allow `diagnostic_probe`, `open_text`, and `dont_know`, test the target facets directly, use the recommended difficulty band, provide rubric criteria for each target facet, and map those criteria to facets with `criterion_facet_weights`. It must use `review_route = review_required`; diagnostic generation queues a proposal only and never writes YAML directly. After the proposal batch is persisted, targeted needs are moved from `pending` to `fulfilled`.

### 14.7 Canonical Source Ingestion

`ingest` is a CLI authoring flow for canonical source material. It detects or accepts a source kind, fetches and normalizes source content, registers a canonical source note, chunks the content, and calls the canonical ingestor prompt with version `mvp-0.2-canonical-ingest-difficulty`. The generated rows are validated and persisted as a proposal batch. If a stronger retry provider is configured, invalid rows can be retried once. Auto-apply rows are downgraded when prerequisite Learning Objects, Practice Items, or concept edges are not ready; eligible rows are applied through the same proposal application path and content events are recorded.

## 15. Parameter Reference

This section lists the parameters that currently affect the learning algorithm. Values are defaults from `config.py` unless overridden in `learnloop.toml`.

### 15.1 Scheduler

| Parameter | Default | Meaning |
|---|---:|---|
| `scheduler.forgetting_risk_weight` | `1.0` | Weight on FSRS forgetting risk in legacy priority. |
| `scheduler.active_goal_weight` | `0.35` | Weight on active-goal concept relevance. |
| `scheduler.recent_error_weight` | `0.50` | Weight on recent active error severity. |
| `scheduler.probe_eig_weight` | `0.25` | Weight on probe expected information gain. |
| `scheduler.short_session_minutes` | `20` | Available minutes at or below this count as a short session. |
| `scheduler.candidate_log_retention_limit` | `200` | Retained scheduler explanation rows per session insert. |
| `scheduler.selection_exploration_rate` | `0.0` | Seeded exploration probability. Off by default. |
| `scheduler.selection_exploration_reward_window` | `0.15` | Maximum reward gap for exploration alternatives. |

### 15.2 Surprise And Follow-Up

| Parameter | Default | Meaning |
|---|---:|---|
| `scheduler.surprise.theta_pos` | `1.5` | Positive residual threshold. |
| `scheduler.surprise.theta_neg` | `1.5` | Negative residual threshold. |
| `scheduler.surprise.alpha_interval` | `0.3` | Exponent coefficient for FSRS interval factor. |
| `scheduler.surprise.f_min` | `0.5` | Minimum FSRS interval multiplier. |
| `scheduler.surprise.f_max` | `1.5` | Maximum FSRS interval multiplier. |
| `scheduler.surprise.epsilon_error_surprise` | `0.05` | If observed error probability is below this, direction becomes negative. |
| `scheduler.followup.tau_followup_nats` | `0.05` | Bayesian surprise threshold for follow-up. |
| `scheduler.followup.gamma_min` | `0.5` | Minimum grader confidence unless deterministic `dont_know`. |
| `scheduler.followup.tau_severe_error` | `0.75` | Local error severity threshold. |
| `scheduler.followup.tau_repeated_item_failures` | `2` | Repeated same-item failure trigger. |
| `scheduler.followup.tau_repeated_facet_failures` | `2` | Repeated same-facet failure trigger. |
| `scheduler.followup.tau_unfamiliar_intervention` | `0.85` | High unfamiliar posterior trigger. |
| `scheduler.followup.max_interventions_per_lo_per_session` | `1` | Per-session intervention cap per Learning Object. |
| `scheduler.followup.cold_start_min_lo_evidence` | `2.0` | Below this independent evidence mass, follow-up intent prefers probe. |

### 15.3 Mastery And IRT

| Parameter | Default | Meaning |
|---|---:|---|
| `mastery.base_observation_variance` | `1.0` | Probability-space measurement noise scale. |
| `mastery.sigma2_drift` | `0.01` | Daily logit variance drift. |
| `mastery.p_max` | `4.0` | Maximum drifted logit variance. |
| `mastery.irt.enabled` | `true` | Enables probability-space 2PL EKF. False uses legacy update. |
| `mastery.irt.discrimination_default` | `1.0` | Current fixed item discrimination $a_i$. |
| `mastery.irt.discrimination_min` | `0.2` | Forward-compatible clamp, not used for per-item fitting. |
| `mastery.irt.discrimination_max` | `3.0` | Forward-compatible clamp, not used for per-item fitting. |
| `mastery.irt.difficulty_default` | `0.0` | Default $b_i$ when no static difficulty exists. |
| `mastery.irt.difficulty_from_prior` | `true` | Resolve $b_i$ from item/LO difficulty fields. |
| `mastery.irt.difficulty_prior_scale` | `2.5` | Maps $d \in [0,1]$ to logit difficulty. |
| `mastery.irt.b_abs_max` | `4.0` | Absolute clamp on $b_i$. |
| `mastery.irt.p_clip` | `1e-4` | Clamp on predicted correctness before computing $H$ and $R_y$. |
| `mastery.irt.mu_abs_max` | `5.0` | Absolute clamp on $\mu$. |
| `mastery.irt.max_logit_step` | `4.0` | Per-attempt cap on $|\Delta\mu|$. |

### 15.4 Probe

| Parameter | Default | Meaning |
|---|---:|---|
| `probe.attempts_target_default` | `3` | Normal target attempt count for a probe. |
| `probe.attempts_target_with_strong_claim` | `1` | Target attempts when learner has a strong prior claim. |
| `probe.claim_skip_threshold` | `0.75` | Claim level threshold for strong-claim behavior and mastery prior use. |
| `probe.variance_convergence_threshold` | `0.10` | Probe completion threshold for mastery variance or residual hypothesis mass. |
| `probe.hypothesis_set_max_size` | `5` | Maximum hypothesis labels in a probe. |
| `probe.irt.theta_mastered` | `2.0` | Ability anchor for mastered hypothesis. |
| `probe.irt.theta_unfamiliar` | `-2.0` | Ability anchor for unfamiliar and probed misconception low anchor. |
| `probe.irt.cut_mid` | `-1.0` | First graded bucket cut. |
| `probe.irt.cut_high` | `1.0` | Second graded bucket cut. |
| `probe.irt.unfamiliar_error_leak` | `0.20` | Low-bucket error leak for unfamiliar. |
| `probe.irt.err_low_frac` | `0.80` | Low-bucket mass routed to a probed misconception. |
| `probe.irt.err_mid_frac` | `0.50` | Mid-bucket mass routed to a probed misconception. |
| `probe.self_tag.w_base` | `0.5` | Base trust for learner self-tagged misconception. |
| `probe.self_tag.w_max` | `0.7` | Cap on self-tag trust. |
| `probe.self_tag.target_degree` | `2.0` | Graph density where missing links become informative. |
| `probe.self_tag.promotion_threshold` | `3` | Repeated self-tags before a reviewed durable-probe proposal. |

### 15.5 Recall Coverage

| Parameter | Default | Meaning |
|---|---:|---|
| `recall_coverage.familiarity_recent_attempt_window` | `8` | Recent LO attempts considered for familiarity discount. |
| `recall_coverage.same_item_evidence_discount` | `0.50` | Component discount at full same-item overlap. |
| `recall_coverage.same_surface_family_evidence_discount` | `0.70` | Component discount at full same-surface overlap. |
| `recall_coverage.same_facet_surface_evidence_discount` | `0.85` | Component discount at full same-facet overlap. |
| `recall_coverage.min_independent_evidence_discount` | `0.20` | Lower bound on independent evidence discount. |
| `recall_coverage.facet_recall_prior_pseudo_count` | `1.0` | Reserved prior pseudo-count parameter; current code initializes Beta at $1,1$. |
| `recall_coverage.facet_blend_evidence_count` | `4.0` | Scale for blending IRT and facet readiness. |
| `recall_coverage.bad_item_min_evidence` | `3` | Configured minimum for item review concepts; current flag path uses evidence count $3$. |
| `recall_coverage.bad_item_suspicion_review_threshold` | `0.65` | Bad item suspicion flag threshold. |
| `recall_coverage.bad_item_suspicion_damage_mitigation_cap` | `0.20` | Max mitigation of local error severity from bad item suspicion. |
| `recall_coverage.max_error_sharpening` | `3.0` | Max EKF observation sharpening from severity. |

### 15.6 Error Impacts And Cross-LO Gates

Each `error_impacts.<error_type>` can define `families`, `lo_mastery_delta`, and `local_severity_gain`. Current mastery uses `local_severity_gain` through observation sharpening. `lo_mastery_delta` remains for legacy compatibility and defaults to $0$ in the model, although the default config text includes `recall_failure.lo_mastery_delta = -0.05` for older compatibility.

Cross-LO propagation config has defaults `max_depth = 3`, `hop_decay = 0.5`, and `total_propagated_weight_cap = 0.7`. The current probe self-tag graph closeness and neighbor misconception logic use concept graph relations and hop decay; general cross-LO mean propagation is not a central current mastery update path.

### 15.7 Other Fixed Coefficients

The current implementation also contains fixed coefficients in service code:

- Local severity: incorrectness $0.12$, expected correctness $0.10$, coverage $0.08$, repeated same item up to $0.25$, repeated same facet up to $0.20$, repeated same error up to $0.10$, `dont_know` $0.05$, failed facet mass $0.08$, hint mitigation $0.04$ per hint.
- Practice item quality: low grader confidence adds $0.08$, repeated failure adds $0.06$, failure despite high LO state adds $0.06$, clean success subtracts $0.04$.
- Predicted correctness for selection: scaffold $0.12$, retrieval penalty $0.15$, bad item penalty $0.10$.
- Predicted correctness for attempt debug: scaffold $0.10$, retrieval penalty $0.10$.
- Ability transition: diagnostic probe $0$; feedback after gap $0.04+0.04(1-correctness)$; successful reinforcement $0.02 correctness$; all capped to $[0,0.08]$.

## 16. How FSRS Pairs With LearnLoop's Novel Model

FSRS and the LearnLoop model are intentionally not competing estimates of the same thing.

FSRS estimates item memory. It models whether the learner will retrieve Practice Item $i$ at time $t$ using $D_i$, $S_i$, and $R_i(t)$. Its output is due timing and forgetting risk. It is local to the item and has no concept graph, facet graph, misconception belief, or rubric coverage model.

The LearnLoop model estimates skill and diagnostic state. It models Learning Object mastery $\theta_\ell$, facet recall Beta states, misconception hypotheses, local error severity, and item quality. It uses item difficulty priors and evidence metadata to decide what an answer means.

They are paired at three points:

1. Attempt outcome: the same rubric score produces an FSRS rating and a mastery/facet observation. FSRS receives a coarse rating; the EKF receives a calibrated score fraction with coverage, reliability, familiarity, difficulty, and severity.
2. Interval adjustment: the mastery/surprise residual produces $F_{surprise}$, which multiplies the FSRS retention interval. Unexpected success can lengthen the next interval; unexpected failure can shorten it.
3. Scheduling: FSRS forgetting risk is one priority term, while active goals, recent errors, probe EIG, predicted correctness, facet weakness, repair value, and expected skill gain shape final ordering.

What the pairing avoids:

- FSRS dynamic difficulty $D_i$ is never used as IRT $b_i$.
- Expected skill gain is never written as observed evidence.
- Error severity does not directly add a non-Bayesian nudge to mastery; it changes observation precision.
- Probe EIG does not replace normal practice scheduling; it is active only during probe phases and is blended into the deterministic scheduler.

## 17. Current Implementation Caveats

These are important for interpreting the current backend accurately.

- The IRT difficulty $b_i$ is static. It comes from authored or LLM-estimated difficulty fields. The backend can flag miscalibration but does not update difficulty online.
- Discrimination $a_i$ is fixed at the default, currently $1.0$. Per-item discrimination fields are not currently authored or fitted.
- The EKF is a one-step linearization at the prior mean. It has a step cap and mean clamp but does not currently run an iterated or Laplace correction.
- `learner_theta` exists in the schema but is not the main active mastery model. Current Learning Object mastery lives in `learning_object_mastery`.
- `learner_state_beliefs` currently persists misconception posterior beliefs from probes; scheduler reward currently uses active error events for the misconception component and uses probe posterior through the in-progress hypothesis set for EIG.
- `ability_transition_events` are audit and reward signals only. They explicitly store `applied_to_belief_counts = false`, `applied_to_mastery = false`, and `applied_to_facet_recall = false`.
- Facet canonicalization is registry-backed through `facets.yaml`. The loader canonicalizes item evidence facets, evidence weights, criterion-facet weights, repair targets, and grading attribution targets through registered aliases. Doctor still treats unregistered facets as a review problem rather than an automatic content rewrite.
- `recall_coverage.facet_recall_prior_pseudo_count` is defined in config, but current Beta updates initialize unseen facet rows at $\alpha=1,\beta=1$ directly.
- The local `learnloop.toml` may not list every config field. Missing fields use Pydantic defaults in `config.py`.
- The sidecar and CLI call `sync_vault_state`, which can create missing Practice Item state, missing mastery state, and initial probe state from YAML content.

## 18. Code Path Summary

A normal CLI/sidecar practice attempt follows this call graph:

1. CLI or sidecar creates an `AttemptDraft`.
2. `complete_attempt_with_ai_fallback`, `complete_attempt_with_codex_fallback`, or `complete_self_graded_attempt` resolves grading.
3. `apply_attempt` calls `compute_attempt_application`.
4. `compute_attempt_application` delegates to `_compute_resolved_grade_application`, which calls `item_irt_params`, `predicted_correctness`, `resolve_coverage`, `derive_facet_outcomes`, `resolve_reliability`, `familiarity_discount`, `event_local_severity`, `resolve_error_impact`, `update_mastery_traced`, `compute_surprise`, FSRS `apply_review`, `build_facet_recall_updates`, `build_quality_state_update`, and `estimate_ability_transition`.
5. Repository writes all attempt-derived outcomes.
6. `record_probe_attempt` updates probe posterior/progress if relevant.
7. CLI/sidecar evaluates intervention follow-up.

A scheduler refresh follows this path:

1. Load vault and repository.
2. `sync_vault_state` reconciles YAML-owned entities with SQLite state.
3. CLI review/why paths and sidecar context load/reload call `run_startup_maintenance`; the queue build itself starts at `build_due_queue`.
4. `build_due_queue` reads item state, mastery, probe states, active errors, goals, pending follow-ups, and facet states.
5. For probe Learning Objects, it loads the live posterior hypothesis set and scores candidate item probe EIG.
6. It computes legacy priority and selection reward.
7. It sorts, applies seeded exploration if configured, inserts pending follow-ups, optionally persists scheduler explanations and structured scheduler slate/candidate logs, and records probe elicitation.

An authoring flow follows this path:

1. `build_authoring_context` gathers deterministic context.
2. AI/Codex returns an `AuthoringProposal` JSON object.
3. `persist_authoring_proposal` or `generate_authoring_proposal` validates and persists proposal rows.
4. Auto-apply rows are accepted if policy allows.
5. Human-accepted rows compile through `patches.py` into vault writer calls.
6. The vault is reloaded and derived state is synced.

A diagnostic-generation flow follows this path:

1. `generate-diagnostics` loads the vault, syncs SQLite state, and reads pending `intervention_needs`.
2. `build_diagnostic_practice_plan` filters to active Learning Objects, resolves target facets, attaches source-item context, reads mastery and facet recall state, and computes difficulty bands.
3. `generate_authoring_proposal` calls the authoring provider with diagnostic-specific instructions.
4. The returned `AuthoringProposal` is validated and persisted as a normal proposal batch.
5. Targeted intervention needs are marked `fulfilled` with a `diagnostic_proposal_queued:<proposal_id>` blocked reason.
6. The reviewed proposal item can later be accepted through the normal proposal application path.

Doctor review for content and derived state follows this path:

1. Loader canonicalizes Practice Item facets through `facets.yaml` aliases.
2. `doctor` validates criterion-facet maps, flags unregistered facets when a registry exists, and reports high-similarity facet pairs with a suggested `facets.yaml` alias patch.
3. With `--fix-state`, existing registered aliases are used to merge aggregate and item-local facet recall rows in SQLite.
4. `doctor` also reports stale derived-state rebuild markers, difficulty miscalibration, high bad-item suspicion, likely duplicate Learning Objects, and pending duplicate diagnostic Practice Item proposals that target the same Learning Object and canonical facet set.

## 19. Minimal Equation Index

- Display mastery: $m=\sigma(\mu)$ and $V_m=(m(1-m))^2P$.
- Static difficulty: $b=\operatorname{clamp}(2s(d-0.5),-b_{max},b_{max})$.
- Predicted correctness: $p=\sigma(a(\mu-b))$.
- EKF sensitivity: $H=ap(1-p)$.
- EKF measurement noise: $R_y=base\cdot p(1-p)/\max(w,0.10)$.
- Drifted variance: $P^-=\min(P+\sigma_d^2\Delta t,P_{max})$.
- Innovation variance: $S=H^2P^-+R_y$.
- Kalman gain: $K=P^-H/S$.
- Mastery mean update: $\mu^+=\operatorname{cap\_and\_clamp}(\mu+K(y-p))$.
- Mastery variance update: $P^+=(1-KH)P^-$.
- Bayesian surprise: $0.5(\log(P/P^+)+P^+/P+(\mu-\mu^+)^2/P-1)$.
- Predictive surprise: $0.5(z^2+\log(2\pi S))$.
- FSRS interval factor: $F=\operatorname{clamp}(\exp(\alpha z),F_{min},F_{max})$.
- Facet Beta update: $\alpha'=\alpha+w_fo_f$, $\beta'=\beta+w_f(1-o_f)$.
- Probe graded marginals: $P(low)=1-\sigma(\eta-c_1)$, $P(mid)=\sigma(\eta-c_1)-\sigma(\eta-c_2)$, $P(high)=\sigma(\eta-c_2)$.
- Probe EIG: $\sum_h\pi_h\sum_oP(o|h,i)\log(P(o|h,i)/P(o|i))$.
- Probe posterior: $P(h|o)\propto P(h)L(h)$.
- Self-tag mixture: $L(h)=wP_{probe}(s,E|h)+(1-w)P_{marg}(s|h)$.

## 20. Practical Interpretation

Mastery is updated by asking: given the item difficulty, coverage, reliability, and current prior, how surprising was the observed score fraction? FSRS is updated by asking: given the same outcome as a coarse rating, when should this exact item be reviewed again? Probes are scheduled by asking: before seeing an answer, which item is expected to reduce the most uncertainty about the locked hypothesis set and continuous skill state? Practice generation is triggered after probes so the system first diagnoses what it knows, then expands the item surface around the Learning Object. Diagnostic generation is triggered from pending intervention needs when an observed gap has no suitable existing follow-up item; it creates a reviewed proposal for a targeted probe at the learner's current facet boundary.

That division of labor is the core of the current backend: FSRS handles item memory; the EKF handles scalar skill; Beta states handle facet recall; categorical Bayes handles diagnostic misconceptions; proposal services author new questions under validation and review.
