from __future__ import annotations

from typing import Annotated, Any, Literal, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

if TYPE_CHECKING:
    from learnloop.config.compat import CodexConfig
class StorageConfig(BaseModel):
    sqlite_path: str = "state.sqlite"


class AlgorithmsConfig(BaseModel):
    # Fallback for configs that omit the field, i.e. vaults created before the
    # mvp-0.7 template. Treat them as legacy; activation must go through
    # `learnloop upgrade`, never through a silent default flip. New vaults get
    # an explicit current version from the generated template.
    algorithm_version: str = "mvp-0.6"


class SchedulerSurpriseConfig(BaseModel):
    theta_pos: float = 1.5
    theta_neg: float = 1.5
    alpha_interval: float = 0.3
    f_min: float = 0.5
    f_max: float = 1.5
    epsilon_error_surprise: float = 0.05


class SchedulerFollowupConfig(BaseModel):
    # Re-tuned for the probability-space EKF surprise (spec_irt_difficulty.md §6.2):
    # the bounded EKF moves mu gently, so per-attempt Bayesian surprise is ~6x
    # smaller in nats than the legacy logit update. 0.3 was unreachable post-EKF.
    tau_followup_nats: float = 0.05
    gamma_min: float = 0.5
    tau_severe_error: float = 0.75
    tau_repeated_item_failures: int = 2
    tau_repeated_facet_failures: int = 2
    tau_unfamiliar_intervention: float = 0.85
    # From mvp-0.21 the kill-switch path only (voi_stopping.followups off):
    # with it on, a further intervention is queued while its value of
    # information pays for its minutes.
    max_interventions_per_lo_per_session: int = 1
    cold_start_min_lo_evidence: float = 2.0
    min_target_facet_overlap: float = 0.5
    max_diagnostic_target_facets: int = 2
    # Data-relative thresholds (gate modernization): "quantile" resolves
    # tau_followup_nats / tau_severe_error against this learner's own logged
    # signal distribution; below quantile_min_samples observations the absolute
    # constants above remain the cold-start fallback.
    threshold_mode: str = "quantile"  # "quantile" | "absolute"
    tau_followup_quantile: float = 0.85  # fire on the top 15% of negative surprises
    tau_severe_error_quantile: float = 0.90
    quantile_min_samples: int = 30
    quantile_window: int = 200
    # Continuous gate score: "score" combines all signals through one logistic
    # with the threshold applied last (near-misses become loggable gradients);
    # "cascade" is the legacy hard trigger/suppression chain, kept as a
    # bit-for-bit escape hatch and regression baseline.
    gate_mode: str = "score"  # "cascade" | "score"
    gate_score_threshold: float = 0.5
    gate_subscore_steepness: float = 12.0
    # Predictive facet EIG (Adaptive Elicitation): expected reduction in
    # entropy of predicted answers to held-out target items. Logged on every
    # follow-up slate; weight 0.0 keeps ranking bit-for-bit unchanged until the
    # logs justify trusting it (log-before-trust).
    predictive_eig_weight: float = 0.0
    predictive_eig_target_cap: int = 4
    # Misconception discrimination gate (spec §4.1, Phase 1: parsed but inert).
    # A diagnostic candidate must clear this Youden-J lower bound against an
    # active misconception to be diagnostic-eligible. require_misconception_discrimination
    # gates whether an active misconception with no discriminating candidate
    # routes to no_suitable_item instead of queueing a paraphrase.
    tau_discrimination_power: float = 0.3
    require_misconception_discrimination: bool = True


class SchedulerConfig(BaseModel):
    forgetting_risk_weight: float = 1.0
    # Goal facet frontier: rewards items whose evidence facets are not yet
    # on track for an active goal (unexamined, known gap, or projected below
    # the goal's target_recall at its due date).
    goal_frontier_weight: float = 0.25
    recent_error_weight: float = 0.50
    probe_eig_weight: float = 0.25
    # Goal quota: guaranteed floor share of the built queue overlapping the
    # goal frontier while an active goal has at-risk facets. Ramps from min
    # to max as due_at approaches (linearly over the last ramp_days); goals
    # without a due date stay at min; past-due goals use max. Composition
    # gating, not a score weight — the priority-weight sweep showed additive
    # weights are decision-inert.
    goal_quota_floor_min: float = 0.30
    goal_quota_floor_max: float = 0.70
    goal_quota_ramp_days: int = 28
    short_session_minutes: int = 20
    candidate_log_retention_limit: int = 200
    # Matches the generated template: exploration stays on even for vaults whose
    # learnloop.toml predates the key, or logged slates carry degenerate
    # propensities and off-policy evaluation is dead (architecture_pivot Stage 0).
    selection_exploration_rate: float = 0.1
    selection_exploration_reward_window: float = 0.15
    surprise: SchedulerSurpriseConfig = Field(default_factory=SchedulerSurpriseConfig)
    followup: SchedulerFollowupConfig = Field(default_factory=SchedulerFollowupConfig)


class GoalsConfig(BaseModel):
    # Projection horizon for goals without a due date: facet recall is
    # forward-projected this many days out when deciding on-track status.
    default_projection_horizon_days: int = 30
    # Exam protection's serving rules (docs/reviews/exam-protection.md; the
    # kill switch of its Codex review F6): material the learner has been shown
    # never becomes an exam item, a certification cold probe or a cold retry;
    # an exam item shown after its reservation is withdrawn before the exam
    # starts; an item made from held-out material stays out of routine
    # practice (Today, the quick check, find_practice, picks and session
    # serves) and is never a cold probe or retry; the plan's reading step in
    # DL1's order (plan.reading_from_furthest off) never offers exam material
    # (exam protection by extraction identity, Codex review F6). Live at every
    # version (replay never reads it); off restores the selection before the
    # stage. What a model is shown (teaching, the Reader, leakage) is not
    # switched.
    held_out_selection: bool = True


class HypothesisConfig(BaseModel):
    session_card_budget: int = Field(default=2, ge=0)
    claim_cooldown_days: int = Field(default=7, ge=0)
    # F5 overconfidence list (§4.3): the minimum aggregate evidence mass a facet
    # needs before "Ready high, Demonstrated false" is trusted over cold-start
    # noise.
    overconfidence_min_evidence_mass: float = Field(default=1.0, ge=0.0)
    # F7 welcome-back diff (§4.4): a gap strictly larger than this many days
    # since the last session end opens the re-entry panel.
    reentry_gap_days: int = Field(default=7, ge=1)
    # F7 no-goal decay pressure (§4.5): the recall threshold a facet "crosses"
    # and how far out we search for the crossing day.
    decay_pressure_target_recall: float = Field(default=0.8, gt=0.0, le=1.0)
    decay_pressure_horizon_days: int = Field(default=60, ge=1)


class MasteryIRTConfig(BaseModel):
    enabled: bool = True                     # false -> legacy logit-space update (bit-for-bit)
    discrimination_default: float = 1.0
    discrimination_min: float = 0.2          # forward-compat clamp; a is fixed 1.0 in Phase A
    discrimination_max: float = 3.0
    difficulty_default: float = 0.0          # b at mu_0
    difficulty_from_prior: bool = True       # derive b from PracticeItem.difficulty / LO.difficulty_prior
    difficulty_prior_scale: float = 2.5      # difficulty 0..1 -> b in [-2.5, 2.5]; also the prior-trust dial
    b_abs_max: float = 4.0
    p_clip: float = 1e-4                     # numerical clamp on p before H/R_y
    mu_abs_max: float = 5.0                  # sanity clamp on logit_mean
    max_logit_step: float = 4.0              # per-attempt cap on |mu_new - mu| (EKF-overshoot guard)
    # Empirical-Bayes per-item difficulty (Fable's-take item 5). Ships dark:
    # theta and b are confounded at N=1, and a bad b trajectory corrupts
    # mastery, surprise, and gating simultaneously — validate via calibration
    # flags + flag-flip-and-rebuild before defaulting on. The authored value
    # stays the prior mean; b learns ~5x slower than mu (gain scale) with a
    # per-attempt step clamp.
    # Primed attempts (retry launched from the source-review panel): the item
    # is effectively easier because the source is fresh in working memory.
    # Applied as b_eff = b - priming_b_offset AFTER resolve_item_irt_params
    # clamping, so a primed success barely moves mu (predicted p near 1) while
    # a primed failure moves it strongly. Default is provisional pending sim
    # sweep calibration (mastery.irt.priming_b_offset in default_sweep.yaml).
    priming_b_offset: float = 2.0
    eb_difficulty_enabled: bool = False
    b_prior_variance: float = 0.25           # sigma = 0.5 logits around the authored prior
    b_learning_rate_scale: float = 0.2
    b_max_step: float = 0.25
    b_var_min: float = 0.01


class ProbeIRTConfig(BaseModel):
    theta_mastered: float = 2.0
    theta_unfamiliar: float = -2.0
    cut_mid: float = -1.0
    cut_high: float = 1.0
    unfamiliar_error_leak: float = 0.20
    err_low_frac: float = 0.80               # §5.3 misconception:E low-bucket routing
    err_mid_frac: float = 0.50               # §5.3 misconception:E mid-bucket routing


class ProbeSelfTagConfig(BaseModel):
    """Learner self-attributed misconception probe coverage (spec_irt_difficulty.md §12)."""

    w_base: float = 0.5            # base label trust before semantic modulation (§12.3)
    w_max: float = 0.7            # cap: a self-tag can never reach rubric strength w=1
    target_degree: float = 2.0    # graph density at which a *missing* link is fully trusted
    promotion_threshold: int = 3  # per-(item, E) self-tags before a reviewed rubric-fatal proposal


class MasteryConfig(BaseModel):
    base_observation_variance: float = 1.0   # probability-space scale: inverse effective trials in R_y
    sigma2_drift: float = 0.01
    p_max: float = 4.0
    # Cold-start prior widths (P0 revision). A vault serves complete novices
    # through rusty experts, so the no-signal prior must be broad: 3.0 puts the
    # central 80% interval near [0.07, 0.93] instead of [0.22, 0.78] at 1.0.
    # Claims move the MEAN but must not manufacture confidence — a claim-seeded
    # prior keeps at least claim_prior_min_variance of logit variance however
    # large its pseudo-count.
    cold_start_prior_logit_variance: float = 3.0
    claim_prior_min_variance: float = 2.0
    # Display banding for mastery means: > strong renders green, > developing
    # renders amber, else red. Owned here (not in the frontend) so the breakpoints
    # can become fitted values without a UI release.
    display_strong_threshold: float = 0.6
    display_developing_threshold: float = 0.35
    irt: MasteryIRTConfig = Field(default_factory=MasteryIRTConfig)


class ProbeEpisodeConfig(BaseModel):
    """Diagnostic-episode policy (spec_probe_eig_redesign.md §5/§11).

    Belief updates and episode advancement are separate accounting paths: the
    *_evidence_weight fields dampen incidental/contaminated likelihoods toward
    the bucket marginal for belief only — such evidence never advances an
    episode regardless of weight.
    """

    minimum_independent_observations: int = 2
    # Initial/goal placement episodes are routing conclusions, not
    # demonstrations: one qualifying observation may complete them.
    placement_minimum_observations: int = 1
    maximum_observations: int = 4
    posterior_stop_threshold: float = 0.85
    # A high-cost hypothesis pair is unresolved while the smaller of the two
    # probabilities exceeds this fraction of the larger (§11).
    ambiguity_threshold: float = 0.30
    # Decision-equivalence stop: complete after >=1 qualifying observation once
    # every hypothesis holding at least action_equivalence_plausible_threshold
    # posterior routes to the same first intervention — remaining uncertainty
    # has no action value, so further probing only spends learner minutes.
    action_equivalence_enabled: bool = True
    action_equivalence_plausible_threshold: float = 0.10
    open_set_prior: float = 0.10
    open_set_trigger_threshold: float = 0.35
    hinted_evidence_weight: float = 0.5
    contaminated_evidence_weight: float = 0.3
    # From mvp-0.21 the kill-switch path only (voi_stopping.probe_episodes
    # off): with it on, each next observation is served while its value of
    # information pays for its minutes.
    session_qualifying_observation_cap: int = 4
    # Explicit §11 fast path replacing the legacy claim_skip_threshold: a strong
    # prior claim plus a highly discriminating cross-facet instrument may complete
    # after one qualifying observation.
    fast_path_enabled: bool = True
    fast_path_claim_threshold: float = 0.75
    presentation_ttl_minutes: int = 240
    # §7.4/§7.5: predictive EIG per expected second is the diagnostic default
    # objective when enough held-out target instruments exist; hypothesis EIG
    # is the fallback and audit signal. Never added together (§7.4).
    predictive_selection_enabled: bool = True
    predictive_target_minimum: int = Field(default=2, ge=1)
    predictive_target_cap: int = Field(default=6, ge=1)
    selection_overhead_seconds: float = Field(default=10.0, ge=0.0)
    # §5.9 fresh-vault onboarding ceiling: once this many qualifying diagnostic
    # observations exist and no ordinary practice attempt has been recorded yet,
    # the probe contract deactivates so the learner reaches ordinary practice.
    # 0 disables the ceiling. A calibration session (explicit opt-in) lifts it.
    onboarding_practice_ceiling_observations: int = Field(default=4, ge=0)
    # §6.5 re-probe triggers. Repeated prediction errors: at least
    # `reprobe_prediction_error_count` negative-surprise attempts above the
    # predictive-surprise threshold (nats) within the last
    # `reprobe_prediction_error_window` attempts reopen the LO's episode.
    reprobe_prediction_error_count: int = Field(default=3, ge=1)
    reprobe_prediction_error_window: int = Field(default=10, ge=1)
    reprobe_predictive_surprise_threshold: float = Field(default=1.0, ge=0.0)
    # Stale uncertainty: a completed episode whose LO still has logit variance
    # at/above this after `reprobe_stale_uncertainty_days` re-enters probing.
    # 0 days disables the periodic producer.
    reprobe_stale_uncertainty_variance: float = Field(default=0.6, ge=0.0)
    reprobe_stale_uncertainty_days: int = Field(default=30, ge=0)


class ProbeGenerationConfig(BaseModel):
    """Parameterized instance generation from admitted family/card bindings (§10)."""

    instances_per_need: int = Field(default=2, ge=1, le=3)
    auto_generate_on_entry: bool = False
    # LLM-backed instance surfaces (§9.2/§9.4): used only when a capable AI
    # client is threaded through; every surface still passes the structural
    # instance gate, and the parametric templates remain the fallback.
    llm_surfaces: bool = True


class ProbeDialogueConfig(BaseModel):
    """Short adaptive dialogue microprobes (§8.1)."""

    planned_turns: int = Field(default=3, ge=1, le=6)


class ProbeCalibrationConfig(BaseModel):
    """Learner-initiated calibration sessions (§5.9)."""

    default_time_budget_minutes: int = Field(default=20, ge=1)
    max_planned_episodes: int = Field(default=8, ge=1)
    # §5.9/§6.4 planner priority: disagreement among the graph-propagated
    # prior, learner claims, and observed evidence multiplies the information
    # rate by (1 + weight * disagreement). 0 disables the signal.
    disagreement_weight: float = Field(default=0.5, ge=0.0)


class ProbeHierarchyConfig(BaseModel):
    """Hierarchical family → item shrinkage (§9.7, Checkpoint 4.2).

    Item-instance conditionals shrink toward the family-version posterior with
    the strength of ``item_shrinkage_pseudo_count`` family-equivalent
    observations: an item's own counts only move its rows meaningfully once
    they rival that mass. Within a single-learner vault every estimate is
    learner-specific pooling, never psychometric calibration (§9.7).
    """

    item_shrinkage_pseudo_count: float = Field(default=25.0, gt=0.0)


class ProbeLifecycleConfig(BaseModel):
    """Metric gates for trusted/revise/retire transitions (§9.7, Checkpoint 4.7).

    Promotion to ``trusted`` requires real-learner evidence, acceptable regrade
    agreement, and realized-information health; retirement triggers on sustained
    negative realized information or grading disagreement. All thresholds apply
    to real-learner rows only — synthetic gate statistics never qualify a
    family for trust (§9.6).
    """

    trust_minimum_real_sample: int = Field(default=20, ge=1)
    trust_minimum_regrade_checks: int = Field(default=5, ge=0)
    trust_minimum_regrade_agreement: float = Field(default=0.8, ge=0.0, le=1.0)
    trust_maximum_negative_information_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    retire_minimum_sample: int = Field(default=10, ge=1)
    retire_negative_information_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    retire_regrade_agreement_floor: float = Field(default=0.5, ge=0.0, le=1.0)


class ProbeShadowConfig(BaseModel):
    """Shadow-mode alternative selection policies (§13.3, Checkpoint 5.1).

    Alternative rankings are logged onto the committed presentation; a policy
    is promoted only after held-out predictive gains, never from shadow logs
    alone. Off-policy estimates stay on hold for single-learner vaults.
    """

    enabled: bool = True
    top_k: int = Field(default=3, ge=1, le=10)


class ProbeBlockConfig(BaseModel):
    """Precommitted diagnostic blocks (§5.6, Checkpoint 5.2/5.3).

    ``family_redundancy_penalty`` demotes candidates whose family already
    produced an observation this episode (a separate ranking component, never
    folded into the EIG label). Joint greedy conditional EIG applies only to
    blocks committed before answers are observed; sequential selection keeps
    conditioning on the live posterior (§16 test 29).
    """

    family_redundancy_penalty: float = Field(default=0.6, gt=0.0, le=1.0)
    max_block_size: int = Field(default=4, ge=2, le=8)
    # §5.6/§5.7 default diagnostic block: sequential (non-dialogue,
    # non-precommitted) probes run the block-end hook after this many
    # observations in the current state segment.
    default_block_observations: int = Field(default=2, ge=1, le=8)
    # Outcome branches kept per already-picked instrument when marginalizing
    # the expected posterior for conditional EIG (caps the combination tree).
    conditional_branch_cap: int = Field(default=3, ge=1, le=8)


class ProbeConfig(BaseModel):
    # LEGACY fields (Checkpoint 0.4): consumed only by the frozen pre-redesign
    # replay path in diagnosis/probes.py. Live policy lives in `episode`; see the
    # [probe] TOML block for the field-by-field mapping.
    attempts_target_default: int = 3
    attempts_target_with_strong_claim: int = 1
    claim_skip_threshold: float = 0.75
    variance_convergence_threshold: float = 0.10
    hypothesis_set_max_size: int = 5
    irt: ProbeIRTConfig = Field(default_factory=ProbeIRTConfig)
    self_tag: ProbeSelfTagConfig = Field(default_factory=ProbeSelfTagConfig)
    episode: ProbeEpisodeConfig = Field(default_factory=ProbeEpisodeConfig)
    generation: ProbeGenerationConfig = Field(default_factory=ProbeGenerationConfig)
    dialogue: ProbeDialogueConfig = Field(default_factory=ProbeDialogueConfig)
    calibration: ProbeCalibrationConfig = Field(default_factory=ProbeCalibrationConfig)
    hierarchy: ProbeHierarchyConfig = Field(default_factory=ProbeHierarchyConfig)
    lifecycle: ProbeLifecycleConfig = Field(default_factory=ProbeLifecycleConfig)
    shadow: ProbeShadowConfig = Field(default_factory=ProbeShadowConfig)
    block: ProbeBlockConfig = Field(default_factory=ProbeBlockConfig)


class PracticeGenerationConfig(BaseModel):
    """Difficulty-calibration targets for authored Practice Items and probes.

    Difficulty is calibrated to a target *success rate* (research_on_learning.md
    §8/§10), inverted through the mastery 2PL link at the learner's ability.
    Practice items sit in the desirable-difficulty band - effortful but usually
    successful. Probes sit on the learner's boundary, where outcome variance (and
    thus diagnostic information / EIG) is maximized. Each band is ``(low, high)``
    on the success-probability scale.
    """

    practice_success_band: tuple[float, float] = (0.70, 0.85)
    probe_success_band: tuple[float, float] = (0.45, 0.55)
    #: Floor on authored difficulty, and the minimum width of a recommended band.
    #:
    #: Inverting the success band at a low ability estimate asks for an item
    #: easier than the difficulty scale can express, so the band collapses onto
    #: 0.0 and every generated item is authored at the very bottom. Those items
    #: certify nothing: the model already predicts success, so a correct answer
    #: carries almost no information and the ability estimate that produced the
    #: floor never gets the evidence that would lift it. The floor keeps items
    #: informative even when the learner model is (possibly wrongly) pessimistic.
    difficulty_floor: float = 0.15
    min_band_width: float = 0.10


class SeverityExampleConfig(BaseModel):
    attempt_type: str = "independent_attempt"
    hints_used: int = 0
    correctness: float = 0.0
    expected_correctness: float = 0.65
    effective_coverage: float = 0.85
    recent_same_item_failures: int = 0
    recent_same_facet_failures: int = 0
    bad_item_suspicion: float = 0.0
    target_error_type: str | None = None
    expected_error_type: str
    expected_severity_band: tuple[float, float]


def default_severity_examples() -> dict[str, SeverityExampleConfig]:
    return {
        "first_dont_know": SeverityExampleConfig(
            attempt_type="dont_know",
            expected_error_type="recall_failure",
            expected_severity_band=(0.70, 0.82),
        ),
        "second_same_item_dont_know": SeverityExampleConfig(
            attempt_type="dont_know",
            recent_same_item_failures=1,
            expected_error_type="recall_failure",
            expected_severity_band=(0.95, 1.00),
        ),
        "second_same_facet_dont_know": SeverityExampleConfig(
            attempt_type="dont_know",
            recent_same_facet_failures=1,
            expected_error_type="recall_failure",
            expected_severity_band=(0.80, 1.00),
        ),
        "hinted_dont_know": SeverityExampleConfig(
            attempt_type="dont_know",
            hints_used=2,
            effective_coverage=0.80,
            expected_error_type="scaffold_failure",
            expected_severity_band=(0.85, 0.95),
        ),
        "arithmetic_slip": SeverityExampleConfig(
            correctness=0.75,
            expected_correctness=0.70,
            target_error_type="arithmetic_slip",
            expected_error_type="arithmetic_slip",
            expected_severity_band=(0.25, 0.35),
        ),
        "ambiguous_item": SeverityExampleConfig(
            expected_correctness=0.70,
            bad_item_suspicion=0.70,
            expected_error_type="recall_failure",
            expected_severity_band=(0.45, 0.75),
        ),
    }


class RecallCoverageConfig(BaseModel):
    familiarity_recent_attempt_window: int = 8
    same_item_evidence_discount: float = 0.50
    same_surface_family_evidence_discount: float = 0.70
    same_facet_surface_evidence_discount: float = 0.85
    min_independent_evidence_discount: float = 0.20
    facet_blend_evidence_count: float = 4.0
    bad_item_min_evidence: int = 3
    bad_item_suspicion_review_threshold: float = 0.65
    bad_item_suspicion_damage_mitigation_cap: float = 0.20
    max_error_sharpening: float = 3.0
    kappa_uncertain: float = 2.0
    tau_facet_share: float = 0.10
    min_facet_evidence_mass: float = 0.50
    variance_floor_at_zero_coverage: float = 0.5
    variance_floor_at_full_coverage: float = 0.0
    severity_examples: dict[str, SeverityExampleConfig] = Field(default_factory=default_severity_examples)


class MisconceptionsConfig(BaseModel):
    """Automatic misconception resolution ("close the loop").

    An active error event resolves once its learning object accumulates
    ``auto_resolve_clean_attempts`` clean attempts after the event's
    ``created_at``. Clean = correctness >= ``auto_resolve_min_correctness``,
    no error attribution written, and not a ``dont_know``/``skip``
    self-diagnosis (see ``count_clean_attempts_since``).
    """

    auto_resolve_clean_attempts: int = 3
    auto_resolve_min_correctness: float = 0.85
    # Evidence-based resolution (spec §7, Phase 1: parsed, consumed later): a
    # registry misconception resolves once its posterior P(misconception) falls
    # below this threshold, rather than by a raw clean-attempt count.
    tau_misconception_resolved: float = 0.15
    # Sim discrimination gate (spec §6, Phase 1: parsed, consumed later). A
    # generated diagnostic is accepted only if the sim-estimated Beta lower
    # bounds clear these thresholds over sim_gate_trials planted/clean trials;
    # specificity errs stricter because false fires poison the posterior.
    sim_gate_min_sensitivity_lb: float = 0.7
    sim_gate_min_specificity_lb: float = 0.8
    # 8 trials, not 5: a perfect N-trial run has a 25th-percentile lower bound of
    # 0.25^(1/(N+1)) — 0.794 at N=5, which fails the 0.8 specificity gate even
    # for a flawless discriminator; N=8 gives 0.857.
    sim_gate_trials: int = 8
    # Opt-in codex answers-under-belief pass for the sim gate (spec §6). 0 keeps
    # the pure-deterministic string-match grader (no provider tokens). When > 0,
    # codex role-plays that many planted + that many clean students in ONE call
    # per gate run; their fires combine with the deterministic trials into the
    # Beta posteriors. Costs provider tokens per accepted item, so it is off by
    # default. Same N-trial caveat as sim_gate_trials: a perfect discriminator
    # needs the COMBINED N >= 8 to clear the 0.8 specificity gate (the
    # 25th-percentile lower bound is 0.25^(1/(N+1))), and low counts self-limit.
    sim_gate_llm_trials: int = 0


class FacetDiagnosticConfig(BaseModel):
    tau_facet_failed: float = 0.40
    tau_facet_uncertain_variance: float = 0.15
    hedge_uncertainty_floor: float = 0.50
    facet_resolved_threshold: float = 0.10


class ExamSeedingConfig(BaseModel):
    """Exam seeding: imported past-exam outcomes as backdated attempts.

    ``grader_confidence`` is the reliability discount persisted on every seeded
    ``exam_evidence`` attempt (imported outcomes are self-reported after the
    fact, so they never carry full grader trust). ``default_learner_confidence``
    is the 1-5 self-grade confidence recorded when an outcome omits one.
    """

    grader_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    default_learner_confidence: int = Field(default=3, ge=1, le=5)


class TutorQAConfig(BaseModel):
    """Tutor Q&A ("ask") behavior.

    Question limits are enforced server-side per context: practice is per
    (practice item, session), feedback is per attempt, library is per note per
    UTC day. ``apply_uncertainty_effect`` gates the read-side diagnostic bump:
    recent unresolved questions about a facet raise that facet's displayed
    uncertainty in ``mastery_diagnostic_view`` by ``uncertainty_evidence_mass``
    per question (bounded); mastery means are never lowered by asking.
    """

    max_questions_practice: int = Field(default=3, ge=0)
    max_questions_feedback: int = Field(default=5, ge=0)
    max_questions_library: int = Field(default=8, ge=0)
    # U-033 (§7.6): span-grounded reader Ask budget, per source span per UTC day.
    max_questions_reader: int = Field(default=8, ge=0)
    # The reader is on by default for fresh vaults so the lead-user journey
    # needs no hand-edited config. The §12.3.2
    # invariant — the golden path completes with reader dialogue disabled —
    # is preserved by tests that disable it explicitly; the spine never imports
    # the reader module regardless of this flag.
    reader_enabled: bool = True
    # Kill switch for the reader's reference-question adoption sweep (daily-loop
    # follow-up, review F8): a question kept as a reference becomes practice
    # once an active LO cites its passage. false restores the previous
    # behaviour: references stay references, and cards the sweep adopted are
    # not served (vault.lifecycle) but never removed; true serves them again.
    adopt_reference_questions: bool = True
    apply_uncertainty_effect: bool = True
    uncertainty_evidence_mass: float = Field(default=0.15, ge=0.0, le=1.0)
    # Write-path question evidence (decision-time, read-side): substantive
    # unresolved questions update the facet hypothesis marginal used by
    # follow-up selection and diagnostic-focus targeting.
    # ``question_solid_likelihood_ratio`` is the ABSOLUTE FALLBACK for
    # L(ask | facet_solid) / L(ask | not solid) — < 1 because learners rarely
    # ask mechanism/prerequisite questions about facets they hold solidly. It
    # is superseded by the learner's own empirical question->failure lift once
    # ``question_likelihood_min_samples`` questioned attempts exist (see
    # tutor/question_signal.py), keeping this a single self-retiring
    # constant rather than a per-question-type table.
    apply_question_evidence: bool = True
    question_solid_likelihood_ratio: float = Field(default=0.45, gt=0.0, le=1.0)
    question_likelihood_min_samples: int = Field(default=12, ge=1)
    # §13.4 (probe redesign Checkpoint 4.6): interaction-preference questions
    # (requested explanation style, pace, scaffold level, direct-explanation
    # asks) change tutor policy, not mastery belief. Until contextual
    # likelihoods are calibrated their mastery likelihood is damped toward 1
    # (no-op) by this factor: ratio' = 1 - (1 - ratio) * damping. 0 disables
    # the mastery effect of preference-channel questions entirely.
    preference_channel_damping: float = Field(default=0.4, ge=0.0, le=1.0)
    # Tutor delivery fixes (owner, 2026-10-13): the source text one tutor turn
    # reads, in tokens (characters / 4). Passages arrive as complete blocks in
    # priority order (selection, cited blocks, nearest neighbours; or the
    # chosen spans and what they cite); only the first passage past the budget
    # is trimmed and the rest dropped, recorded on the question's
    # source_context.delivery. Generous by default (no premature cut-off).
    context_token_budget: int = Field(default=24_000, ge=1_000, le=400_000)
    # Follow "by Theorem 3.2", "Example 1.4.13", "Equation (3.4)" in a
    # delivered passage to the numbered block of the same extraction (within
    # the budget and the exam rule). false is the kill switch: no reference
    # is followed.
    resolve_references: bool = True
    # Kill switch for the expanded delivery (tutor delivery fixes items 1 and
    # 2; Codex review F5): false restores the predecessor's passages. The
    # Reader gets the span view's window again (the three blocks on each side
    # of the block in view, page furniture included, as 240-character
    # previews, at most max(4, spans + 2) spans) and retrieved, pinned and
    # linked spans their 600-character cut. References (resolve_references)
    # and the budget are separate.
    expanded_delivery: bool = True


class TutorPromotionConfig(BaseModel):
    """Promoting Socratic tutor questions to practice items / learning objects
    (spec_tutor_promotion.md §5).

    Gap route: a "this exposed a gap" promotion writes a low self-report
    ``learner_claims`` row (``gap_claim_level`` at ``gap_claim_pseudo_count``
    pseudo-observations) and, for established LOs, counts as an unresolved-
    question observation with its own likelihood slot in ``question_signal``.
    That slot's ratio is fit empirically from the learner's own gap-declaration
    -> subsequent-failure lift; ``gap_declaration_solid_likelihood_ratio`` is the
    absolute fallback (below 1: a declared gap makes "facet is solid" less
    likely, more strongly than an ordinary ask) used until
    ``gap_declaration_likelihood_min_samples`` gap-declared attempts exist.
    The filed ``tutor_gap_declaration`` need goes stale after
    ``gap_need_ttl_days``. ``requested_items_per_session`` bounds how many
    requested (promoted-but-unattempted) items the scheduler floor guarantees a
    slot per built queue (§4a).
    """

    gap_claim_level: float = Field(default=0.25, ge=0.0, le=1.0)
    gap_claim_pseudo_count: float = Field(default=2.0, ge=0.0)
    gap_declaration_solid_likelihood_ratio: float = Field(default=0.35, gt=0.0, le=1.0)
    gap_declaration_likelihood_min_samples: int = Field(default=12, ge=1)
    gap_need_ttl_days: int = Field(default=21, ge=0)
    requested_items_per_session: int = Field(default=1, ge=0)


class TeachBackConfig(BaseModel):
    """Teach-back conversation behavior.

    ``max_followups`` bounds the number of naive-student questions per
    conversation (one per selected rubric criterion; when the rubric has
    transfer-tier criteria the planner guarantees the final slot is one, so
    the default leaves three uncertainty-driven slots plus that reserved
    transfer slot).
    ``transfer_evidence_multiplier`` is the symmetric evidence-mass multiplier
    applied to facet evidence contributed by transfer-tier rubric criteria —
    both success and failure are discounted equally, and the multiplier is
    read from config at apply time so replay reproduces it. ``session_cap``
    is the maximum number of teach_back items in one built practice queue
    below mvp-0.21 (or with ``voi_stopping.teach_back`` off); from mvp-0.21 it
    is a floor, and each teach-back beyond it stays while its value of
    information pays for its minutes.
    """

    max_followups: int = Field(default=4, ge=1)
    transfer_evidence_multiplier: float = Field(default=0.5, ge=0.0, le=1.0)
    # From mvp-0.21 the floor only (voi_stopping.teach_back): a teach-back
    # beyond it stays while its value of information pays for its minutes.
    session_cap: int = Field(default=1, ge=0)


class GlmOcrConfig(BaseModel):
    """[ingest.pdf.glm_ocr]: GLM-OCR's complete layout + recognition pipeline
    (learnloop.ingest.extractors.glm_ocr). Spend is observed and recorded per
    request, never capped per file (owner policy)."""

    # "auto"/"api": z.ai when a key is set. "local": the self-hosted glmocr
    # server at local_url, when it answers.
    backend: Literal["auto", "api", "local"] = "auto"
    # z.ai's layout_parsing endpoint (Zhipu: open.bigmodel.cn/api/paas/v4).
    api_url: str = "https://api.z.ai/api/paas/v4/layout_parsing"
    # The environment variable holding the key (ZHIPU_API_KEY and
    # ZHIPUAI_API_KEY are read when it is unset); never the key itself.
    api_key_env: str = "ZAI_API_KEY"
    # `python -m glmocr.server` (MaaS mode off in its config.yaml).
    local_url: str = "http://127.0.0.1:5002/glmocr/parse"
    # Per request (a window of up to 30 pages); the glmocr SDK's own default.
    request_timeout_seconds: float = Field(default=300, gt=0, allow_inf_nan=False)
    # The hosted service reads at most 30 pages per request.
    max_pages_per_request: int = Field(default=30, ge=1, le=30)
    # USD per million tokens, input and output alike (z.ai's list price).
    price_per_million_tokens: float = Field(default=0.03, ge=0, allow_inf_nan=False)
    # How the file is sent: a data URI (documented) or bare base64.
    base64_style: Literal["data_uri", "raw"] = "data_uri"


class PdfIngestConfig(BaseModel):
    # "native" sends the WHOLE PDF to the routed canonical_ingest chat provider
    # as a file content part instead of extracting locally; page ranges are
    # not applied. The provider must declare "pdf" in input_modalities (see
    # learnloop.ai.native_media); limits live under [ingest.native].
    engine: Literal["auto", "glm_ocr", "marker", "pypdf", "native"] = "auto"
    glm_ocr: GlmOcrConfig = Field(default_factory=GlmOcrConfig)
    # Device for marker model inference: "" lets marker/surya auto-detect
    # (cuda when available), or pin e.g. "cuda", "cuda:1", "cpu", "mps".
    torch_device: str = ""
    force_ocr: bool = False
    use_llm: bool = False
    llm_service: str = "marker.services.openai.OpenAIService"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key_env: str = "LEARNLOOP_PDF_LLM_API_KEY"
    # Escape hatch: raw marker settings merged over the derived config
    # (e.g. {"paginate_output" = true} under [ingest.pdf.marker_options]).
    marker_options: dict[str, Any] = Field(default_factory=dict)


class AnimationConfig(BaseModel):
    """AI-generated Manim explainer animations (spec_fork_features §2).

    ``enabled`` is a hard kill-switch; every generation additionally requires a
    per-run learner consent click (server-side re-checked) — that consent is
    the security boundary for executing LLM-written scene code. The AST
    allowlist and constrained subprocess are best-effort hardening around it."""

    enabled: bool = True
    # Which renderer produces the video: "manim" renders an LLM-written scene
    # locally; "video_model" sends an LLM-written storyboard to a text-to-video
    # model through OpenRouter ([ai.routing] video_generation) and stitches the
    # shots. The video-model path runs no local code.
    renderer: Literal["manim", "video_model"] = "manim"
    # Video-model options. Each storyboard shot is one OpenRouter job, billed
    # on submission; shot durations are clamped to what the model supports.
    video_resolution: str = "720p"
    video_aspect_ratio: str = "16:9"
    video_generate_audio: bool = False
    video_max_shots: int = 4
    # Wall-clock cap for the whole storyboard (submit, poll, download, stitch).
    video_timeout_seconds: int = 1800
    # manim render quality: "ql" (854x480 @ 15 fps, fast) | "qm" (1280x720 @ 30)
    # | "qh" (1920x1080 @ 60, slow).
    quality: str = "qm"
    timeout_seconds: int = 600
    # Pacing band: the prompt targets it and a pre-render lint sends a scene
    # that comes in under the minimum back to the model once.
    min_duration_seconds: int = 30
    max_duration_seconds: int = 60
    # Tex/MathTex requires a LaTeX toolchain; off by default.
    latex_enabled: bool = False
    # One stderr round-trip back to the model when a render fails.
    auto_repair: bool = True
    # Override the renderer executable; default: sys.executable -m manim.
    manim_executable: str | None = None
    # Optional dedicated virtualenv whose python renders scenes, isolating
    # model-authored code from the app's own packages. Relative paths resolve
    # under the vault root. When unset, the ambient interpreter is used (the
    # env the app was launched from). Takes effect only when manim_executable
    # is unset.
    venv_path: str | None = None
    # When true and venv_path is missing, create it and pip-install manim on
    # first use. Off by default (a heavy, network-bound install); on failure the
    # renderer falls back to the ambient interpreter.
    auto_provision_venv: bool = False


class AudioIngestConfig(BaseModel):
    """Audio-source ingestion (.mp3/.wav/...): transcription settings.

    provider "openai_compatible" (default) sends the file to an OpenAI-style
    POST {base_url}/audio/transcriptions endpoint (OpenAI whisper, Groq, a
    local faster-whisper server, ...) with the key from the env var named by
    ``transcription_api_key_env``. The ``provider`` field is retained as a raw
    compatibility input: legacy "openrouter" values are translated into an
    ``openrouter_transcription`` AI profile plus ``ai.routing.transcription``.
    Runtime chat transcription uses only that standard route. Keys are never
    stored in this file."""

    provider: str = "openai_compatible"  # legacy input; chat routes normalize into [ai]
    # "transcription" (default): the [ai.routing] transcription chat route when
    # set, else the /audio/transcriptions endpoint below. "native": send
    # mp3/wav as input_audio parts to the canonical_ingest chat provider (it
    # must declare "audio" in input_modalities); other containers still take
    # the transcription path.
    mode: Literal["transcription", "native"] = "transcription"
    transcription_base_url: str = "https://api.openai.com/v1"
    transcription_model: str = "whisper-1"
    transcription_api_key_env: str = "LEARNLOOP_TRANSCRIPTION_API_KEY"
    # BCP-47 hint forwarded to the endpoint; "" lets the model auto-detect.
    language: str = ""
    timeout_seconds: int = 600
    # Rejected before any upload (OpenAI's transcription limit is 25 MB).
    max_file_mb: int = 25


class NativeIngestConfig(BaseModel):
    """Shared limits for native media ingestion (media as chat content parts).

    The per-modality switches live with the modality: ``[ingest.pdf] engine =
    "native"`` and ``[ingest.audio] mode = "native"``. The legacy
    ``enabled``/``audio``/``pdf`` gates are normalized away in
    ``learnloop.config.compat``. Media bytes leave the machine to the chat
    provider whenever a native path is selected."""

    # Base64 inflates ~33% inside a chat body; rejected before any upload.
    max_audio_mb: int = 20
    # OpenAI-compatible file inputs cap at 32 MB per file.
    max_pdf_mb: int = 32
    # When native is selected but the routed provider cannot take the modality
    # for a configuration reason, use the non-native path (PDF: marker/pypdf;
    # audio: the transcription route/endpoint) with a health flag instead of
    # failing closed. Off by default: an explicit native choice fails loudly.
    fallback_when_unavailable: bool = False


class IngestBudgetsConfig(BaseModel):
    """Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1)."""

    model_config = ConfigDict(extra="allow")

    inventory_input_tokens: int = 20000
    inventory_output_tokens: int = 3000
    synthesis_shard_input_tokens: int = 40000
    synthesis_shard_output_tokens: int = 10000
    synthesis_total_input_ceiling: int = 48000
    synthesis_output_tokens: int = 16000
    append_neighborhood_input_tokens: int = 24000
    append_output_tokens: int = 10000
    # Span-request protocol caps (§8.5): one bounded request round only.
    synthesis_span_request_max_count: int = 12
    synthesis_span_char_cap: int = 4000
    # Quick add (§1): the ToC-guided relevant-scope cap. When a source's whole
    # outline fits under this, Quick add selects the whole thing; otherwise it
    # selects the brief/subject-matching chapters up to this token size.
    quick_add_scope_input_tokens: int = 40000


class IngestProviderLimits(BaseModel):
    """Per-provider context/output limits consulted by preflight (spec §3.1)."""

    model_config = ConfigDict(extra="allow")

    context_tokens: int | None = None
    max_output_tokens: int | None = None


class IngestRunnerConfig(BaseModel):
    """Durable-queue worker settings for ingestion v2 (source-ingestion §6.2).

    The runner drains queued jobs sequentially under a single lease. A running
    job is kept alive by its heartbeat; a lease older than ``lease_ttl_seconds``
    is considered dead and recovered to failed(interrupted) on startup.
    """

    model_config = ConfigDict(extra="allow")

    lease_ttl_seconds: int = 120
    heartbeat_interval_seconds: int = 15
    poll_interval_seconds: float = 1.0


class IngestCostPauseConfig(BaseModel):
    """When an automatic question build asks before spending (UX Phase 1, Q5),
    and its daily guard.

    A build started by Add or by reading progress runs silently unless its
    estimate exceeds ``threshold_usd`` or ``daily_cap_fraction`` of what is
    left of ``daily_cap_usd`` today. ``daily_cap_usd`` is the daily guard
    (metered spend today, from every model call's receipt): no automatic
    build, job or request runs past it, "Build them" included; unset, there
    is none. There is no per-build money cap (owner, 2026-10-13: per-operation
    caps off by default, a daily guard, spend observed; applied to automatic
    book preparation when UX Phase 1 landed on main). Routes billed to the
    ChatGPT subscription (Codex, the ChatGPT plan) cost nothing extra and
    never pause. A metered route is priced at ``prices[<profile>]`` USD per
    million tokens, else ``default_price_per_million_tokens``.
    """

    model_config = ConfigDict(extra="allow")

    threshold_usd: float = Field(default=1.0, ge=0)
    daily_cap_fraction: float = Field(default=0.25, ge=0, le=1)
    # The daily guard, as source_service.max_daily_cost_usd (owner, 2026-10-13).
    daily_cap_usd: float | None = Field(default=5.0, ge=0)
    default_price_per_million_tokens: float = Field(default=5.0, ge=0)
    prices: dict[str, float] = Field(default_factory=dict)


class IngestConfig(BaseModel):
    window_char_cap: int = 150000
    min_content_chars: int = 400
    default_goal_priority: float = 0.5
    allow_auto_captions: bool = False
    # Bootstrap item authoring when the brief is silent: "upfront" authors
    # practice items at synthesis time (legacy behavior; CLI/append unchanged);
    # "as_you_read" authors none — items accrue progressively from reading. The
    # product UI sends the brief field explicitly, so this default only governs
    # briefless callers.
    bootstrap_practice_items: str = "upfront"
    # UX Phase 1 kill switches (docs/specs/ux_learnloop_v1.md §6, §10). With
    # auto_build on, a source added through Add builds questions for the
    # chapter being read (and the next) once its text is ready, and keeps one
    # chapter ahead as reading advances; off, Add only makes the source
    # readable. auto_apply_passing_builds applies those automatic builds when
    # every gate passes (undo from the book); off, they wait as proposals.
    auto_build: bool = True
    auto_apply_passing_builds: bool = True
    cost_pause: IngestCostPauseConfig = Field(default_factory=IngestCostPauseConfig)
    pdf: PdfIngestConfig = Field(default_factory=PdfIngestConfig)
    audio: AudioIngestConfig = Field(default_factory=AudioIngestConfig)
    native: NativeIngestConfig = Field(default_factory=NativeIngestConfig)
    budgets: IngestBudgetsConfig = Field(default_factory=IngestBudgetsConfig)
    providers: dict[str, IngestProviderLimits] = Field(default_factory=dict)
    runner: IngestRunnerConfig = Field(default_factory=IngestRunnerConfig)


class RungVariantsConfig(BaseModel):
    """Learner-initiated re-runging (content/authoring/rung_variants).

    The score fractions drive the deterministic self-graded ``self_report``
    attempt the request records on the SOURCE item (evidence mass stays the
    global ``self_report`` entry, 0.3): easier = declared soft failure, harder
    = success. Claim levels seed the per-LO cold-state prior.
    """

    easier_score_fraction: float = 0.25
    harder_score_fraction: float = 1.0
    # Maps to grader_confidence 0.6 — above the 0.4 manual-review threshold.
    self_grade_confidence: int = 3
    easier_claim_level: float = 0.25
    harder_claim_level: float = 0.70
    claim_pseudo_count: float = 2.0
    max_pending_per_item: int = 1
    retry_on_rung_violation: bool = True


_COMPAT_OPTIONAL_PROVIDER_FIELDS = frozenset(
    {
        "api_key_env",
        "response_format",
        "thinking",
        "reasoning_summary",
        "max_tokens",
        "http_referer",
        "x_title",
        "checkout_path",
        "revision",
        "startup_command",
        "startup_timeout_seconds",
        "healthcheck_timeout_seconds",
        "sdk_python_path",
        "sdk_codex_bin",
        "sdk_launch_command",
        "healthcheck_path",
        "authoring_path",
        "canonical_ingest_path",
        "grading_path",
        "tutor_qa_path",
        "teach_back_path",
        "teach_back_authoring_path",
        "misconception_match_path",
    }
)


#: Media modalities a provider profile may declare under ``input_modalities``.
#: ``pdf`` and ``audio`` have native ingest paths today; ``image`` and
#: ``video`` are accepted so capability detection can record them ahead of
#: an ingest path.
KNOWN_INPUT_MODALITIES: tuple[str, ...] = ("audio", "pdf", "image", "video")


class AIProviderConfig(BaseModel):
    """Shared provider fields plus a direct-construction compatibility seam.

    Config files validate into the strict discriminated subclasses below.  The
    permissive base remains importable because provider-client tests and local
    integrations historically constructed it directly.
    """

    model_config = ConfigDict(extra="allow")

    type: str = "codex_sdk"
    model: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None
    timeout_seconds: int | None = None
    # A provider capability rather than a transport-specific setting.
    input_modalities: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _discard_auth_mode(cls, data: Any) -> Any:
        from learnloop.config.compat import discard_retired_provider_settings

        return discard_retired_provider_settings(data)

    def __getattr__(self, item: str) -> Any:
        try:
            return super().__getattr__(item)
        except AttributeError:
            # Sparse directly-constructed compatibility profiles historically
            # exposed every optional transport field as None.  This view does
            # not add those fields to concrete model schemas or serialization.
            if item in _COMPAT_OPTIONAL_PROVIDER_FIELDS:
                return None
            raise

    def __eq__(self, other: object) -> bool:
        # Profiles parsed through the discriminated union are concrete
        # subclasses; keep structural equality for legacy callers that still
        # construct the compatibility base directly.
        if isinstance(other, AIProviderConfig):
            return self.model_dump(exclude_none=True) == other.model_dump(
                exclude_none=True
            )
        return super().__eq__(other)


class _CodexProviderConfig(AIProviderConfig):
    model_config = ConfigDict(extra="ignore")

    checkout_path: str | None = None
    revision: str | None = None
    startup_command: str | None = None
    startup_timeout_seconds: int | None = None
    healthcheck_timeout_seconds: int | None = None
    reasoning_summary: str | None = None
    sdk_python_path: str | None = None
    sdk_codex_bin: str | None = None
    sdk_launch_command: str | None = None
    healthcheck_path: str | None = None
    authoring_path: str | None = None
    canonical_ingest_path: str | None = None
    grading_path: str | None = None
    tutor_qa_path: str | None = None
    teach_back_path: str | None = None
    teach_back_authoring_path: str | None = None
    misconception_match_path: str | None = None


class CodexSDKProviderConfig(_CodexProviderConfig):
    type: Literal["codex_sdk"] = "codex_sdk"


class CodexHTTPProviderConfig(_CodexProviderConfig):
    type: Literal["http"] = "http"


class OpenAICompatibleProviderConfig(AIProviderConfig):
    model_config = ConfigDict(extra="ignore")

    type: Literal["openai_chat"] = "openai_chat"
    api_key_env: str | None = None
    response_format: str | None = None
    thinking: str | None = None
    max_tokens: int | None = None


class OpenRouterProviderConfig(OpenAICompatibleProviderConfig):
    type: Literal["openrouter"] = "openrouter"
    http_referer: str | None = None
    x_title: str | None = None


class OpenAIEmbeddingProviderConfig(OpenAICompatibleProviderConfig):
    type: Literal["openai_embedding"] = "openai_embedding"
    model: str = "qwen/qwen3-embedding-8b"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key_env: str = "OPENROUTER_API_KEY"
    dimensions: int = Field(default=4096, gt=0)
    max_input_tokens: int = Field(default=32768, gt=0)


#: Local contextual retrieval P1b (spec_local_contextual_retrieval_v1 §8): the
#: hosted fallback space's embedding-only profile type. It serves only the
#: source-retrieval fallback space (``embedding.fallback.provider``); every AI
#: task, the ``embedding`` task included, refuses it (``ai.routing``), so no
#: route or ``LEARNLOOP_AI_PROVIDER`` can send generation or Qwen-route text to it.
VOYAGE_CONTEXTUAL_PROFILE_TYPE = "voyage_contextual_embedding"


class VoyageContextualEmbeddingProviderConfig(AIProviderConfig):
    """``voyage-context-4`` through ``POST /v1/contextualizedembeddings``.

    Grouped windows (``input_type="document"``) and single-chunk queries
    (``input_type="query"``), 1024-d float, L2-normalized. ``api_key_env`` names
    the key (default ``VOYAGE_API_KEY``, loaded from the settings file like any
    key); receipts record the name and its availability, never the value."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["voyage_contextual_embedding"] = "voyage_contextual_embedding"
    model: str = "voyage-context-4"
    base_url: str = "https://api.voyageai.com/v1"
    api_key_env: str = "VOYAGE_API_KEY"
    dimensions: int = Field(default=1024, gt=0)


DECIDER_PROFILE_TYPE = "decider"
DEFAULT_DECIDER_PROVIDER = "openrouter_decider"
DEFAULT_EMBEDDING_PROVIDER = "openrouter_embedding"
DEFAULT_DECIDER_MODEL = "perplexity/pplx-decider-v1.1-27b"
# OpenRouter's listing for the model (checked 2026-10-12): $0.02 per million
# input tokens, output free. Used for estimates; OpenRouter also reports cost.
DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT = 0.02


class DeciderProviderConfig(AIProviderConfig):
    """A decision model (router spec §6): typed questions in, probabilities out.

    It has no chat transport, so it never serves a generation route, and the
    decider routes accept nothing else. ``api`` selects the wire dialect and
    path: ``openrouter`` posts to ``<base_url>/alpha/decisions`` (OpenRouter's
    Decisions API, the owner's route), ``perplexity`` to
    ``<base_url>/v1/decisions`` (Perplexity's direct API, the documented
    reference shape). Unset fields resolve from ``api`` in the client.
    """

    model_config = ConfigDict(extra="ignore")

    type: Literal["decider"] = "decider"
    api: Literal["openrouter", "perplexity"] = "openrouter"
    api_key_env: str | None = None
    http_referer: str | None = None
    x_title: str | None = None
    price_per_million_input: float = Field(default=DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT, ge=0)
    max_input_tokens: int = Field(default=262_144, gt=0)


CHATGPT_PLAN_PROFILE_TYPE = "chatgpt_plan"
#: The only API the ChatGPT-plan access token is minted for (its OAuth
#: ``resource``). A loopback base URL is allowed for local fakes and proxies.
CHATGPT_PLAN_API_BASE_URL = "https://api.openai.com/v1"


class ChatGPTPlanProviderConfig(AIProviderConfig):
    """OpenAI models billed to the owner's ChatGPT plan ("Continue with ChatGPT").

    Sign in once per machine with ``learnloop ai signin chatgpt``; the tokens
    live in the machine's LearnLoop config directory, never in a vault. Each
    request is one streamed Responses call with ``store=false``; only a
    read-only-workspace turn declares tools (below). ``model`` is a slug from
    ``learnloop ai models chatgpt``. ``enabled = false`` is the per-profile
    kill switch: the profile reads as not ready, so routes that allow fallback
    fall back. ``response_format`` is ``json_schema`` (strict structured
    output) or ``json_object`` (JSON mode plus one repair). After a
    usage-limit error the plan is paused for ``usage_limit_pause_minutes``
    before LearnLoop tries it again.

    A read-only workspace (a snapshot diagnosis's as-of export) is served by
    LearnLoop itself (``learnloop.ai.chatgpt_plan.workspace``):
    ``workspace_mode = "inline"`` (the default since plan-first transport T1:
    every file in the one request; an export over ``max_workspace_chars`` is
    served in tools mode instead, each round its own admitted request, unless
    the owner wrote ``workspace_mode = "inline"``, which then refuses it) or
    ``"tools"`` (Responses function calling: at most ``max_tool_rounds``
    rounds of calls, ``max_entry_chars`` per read and ``max_workspace_chars``
    served in all; the turn's resent input is capped at four times
    ``max_workspace_chars``, past which the model is asked to answer).
    """

    model_config = ConfigDict(extra="ignore")

    type: Literal["chatgpt_plan"] = "chatgpt_plan"
    enabled: bool = True
    response_format: Literal["json_schema", "json_object"] = "json_schema"
    usage_limit_pause_minutes: int = Field(default=15, ge=1, le=24 * 60)
    workspace_mode: Literal["tools", "inline"] = "inline"
    max_tool_rounds: int = Field(default=16, ge=1, le=64)
    max_entry_chars: int = Field(default=24_000, ge=1_000, le=1_000_000)
    max_workspace_chars: int = Field(default=400_000, ge=10_000, le=4_000_000)

    @field_validator("base_url")
    @classmethod
    def _api_or_loopback(cls, value: str | None) -> str | None:
        # The bearer token is a ChatGPT-plan credential: it may go only to
        # OpenAI's API or to a loopback endpoint on this machine.
        if value is None or not value.strip():
            return None
        from urllib.parse import urlsplit

        cleaned = value.strip().rstrip("/")
        parts = urlsplit(cleaned)
        official = parts.scheme == "https" and parts.hostname == "api.openai.com"
        loopback = parts.scheme in {"http", "https"} and parts.hostname in {"127.0.0.1", "localhost", "::1"}
        if not (official or loopback):
            raise ValueError(
                "chatgpt_plan base_url must be https://api.openai.com/... or a loopback URL; "
                "the plan's access token is never sent anywhere else"
            )
        return cleaned


AIProviderProfile = Annotated[
    CodexSDKProviderConfig
    | CodexHTTPProviderConfig
    | OpenAICompatibleProviderConfig
    | OpenRouterProviderConfig
    | OpenAIEmbeddingProviderConfig
    | DeciderProviderConfig
    | ChatGPTPlanProviderConfig
    | VoyageContextualEmbeddingProviderConfig,
    Field(discriminator="type"),
]


#: Routes removed from the schema. A vault that still sets one loads (the
#: value is ignored) and `learnloop doctor` warns that it should be removed.
RETIRED_ROUTES: dict[str, str] = {
    # Phase 2's numeric llm_probability arm, retired by the owner on
    # 2026-10-12 in favour of router R0's V1-V3 arms (llm_probability_llm,
    # llm_probability_decider).
    "field_llm_probability": (
        "Phase 2's numeric llm_probability arm is retired; the V1-V3 arms "
        "(`learnloop eval --section field --probability-arm ...`) use "
        "ai.routing.llm_probability_llm and ai.routing.llm_probability_decider."
    ),
    # mvp-0.17's separate proofs route check, removed from serving by the
    # owner on 2026-10-13 (route-check-in-grader): its rules are in the
    # grader's own prompt, which uses the grading route.
    "proof_check": (
        "mvp-0.17's separate proofs route check is retired; the grader applies the "
        "own-route rules in its one call on ai.routing.grading (mvp-0.20, kill switch "
        "proof_check.enabled)."
    ),
}


class AIRoutingConfig(BaseModel):
    # Never inherits active_provider, its fallback or LEARNLOOP_AI_PROVIDER.
    # Empty = the code-default openrouter_embedding profile (owner, 2026-10-12);
    # nothing is sent unless embedding.enabled (default false) is also on.
    embedding: str | None = DEFAULT_EMBEDDING_PROVIDER
    field_question_classifier: str | None = None
    pf_generator: str | None = None
    # Ensemble proposers: profile names whose models must be at least two
    # distinct slugs, else generation is refused (Slice 2 §5.3, §13).
    pf_proposers: list[str] = Field(default_factory=list)
    pf_selection_judge: str | None = None
    pf_family_judge: str | None = None
    pf_isomorph_judge: str | None = None
    pf_closed_book: str | None = None
    pf_reference_verifier: str | None = None
    # One profile, or a list for a panel at different tiers (P10).
    pf_solver_panel: str | list[str] | None = None
    # Practice index (Slice 2 §5.9): facet dossier writer, find_practice's LLM
    # rerank, and the retrieval evaluation's query writer and relevance judge.
    # Empty = follow ai.active_provider like any generation route.
    practice_dossier: str | None = None
    practice_rerank: str | None = None
    practice_query_writer: str | None = None
    practice_relevance_judge: str | None = None
    # Slice 2 T6 source retrieval: the live rewrite of conceptual questions,
    # the tutor-span verification rerank, and the retrieval evaluation's / B4's
    # question writer and relevance judge. Empty = ai.active_provider.
    source_query_rewrite: str | None = None
    source_rerank: str | None = None
    source_query_writer: str | None = None
    source_relevance_judge: str | None = None
    # Canonical sources: the book's-solution match (S1), compare_sources (S3),
    # the exercise discrimination screen and the worked-example equivalence
    # judge (S2a). Empty = ai.active_provider; a metered route needs
    # source_service.llm_price_per_million or the step is skipped and labelled.
    source_solution_match: str | None = None
    source_compare: str | None = None
    exercise_discrimination: str | None = None
    worked_example_equivalence: str | None = None

    # Slice 2 T4: the leak/reveal judge of `learnloop contamination report`
    # (shadow flags only). Empty = ai.active_provider.
    contamination_judge: str | None = None
    # Facet identity (handoff §4): the cheap judge that partitions candidate
    # facets into same-skill sets at ingest and in `learnloop facets dedupe`.
    # Empty = the code-default `codex_luna` profile when the active provider
    # is Codex, else ai.active_provider. A decider profile (router R0, e.g.
    # `openrouter_decider`) is also accepted: one typed choice question per
    # pair, partitioned with the no-chaining union (owner, 2026-10-12).
    facet_identity_judge: str | None = None
    grading: str | None = None
    # Slice 1 history-aware diagnoser. Empty = the resolved `grading` route.
    diagnosis: str | None = None
    # Offline diagnosis review (Slice 1 M1): the blind pairwise judge and the
    # planted-case / grader-probe generator. Empty = ai.active_provider.
    diagnosis_judge: str | None = None
    diagnosis_generator: str | None = None
    # Slice 2 T1: the same-cause judge (live, backlog and the guard suite).
    # Empty = the resolved diagnosis route (itself the grading route when unset).
    same_cause_judge: str | None = None
    # Learner-text gaps (implementation_handoffs §4): the same/different and
    # "needed for this item?" judge, and the reader of stuck text. Empty = the
    # resolved diagnosis route. The Decider's second opinion is a decider task:
    # empty = the code-default openrouter_decider profile, never a chat
    # fallback and never LEARNLOOP_AI_PROVIDER.
    learner_gap_judge: str | None = None
    learner_gap_reader: str | None = None
    learner_gap_decider: str | None = None
    canonical_ingest: str | None = None
    canonical_ingest_retry: str | None = None
    authoring: str | None = None
    tutor_qa: str | None = None
    # Teach-back naive-student questions + transcript grading. Empty = follow
    # ai.active_provider (same fallback chain as tutor_qa).
    teach_back: str | None = None
    # Learner-requested easier/harder variant authoring (content/authoring/rung_variants):
    # a small, gate-checked task — defaults to the low-effort profile.
    rung_variant: str | None = None
    # Manim explainer-scene authoring (content/authoring/concept_animation): code
    # generation, defaults to the medium-effort profile.
    animation: str | None = None
    # Optional independently selected media-transcription profile. Empty keeps
    # the endpoint/native-ingest fallback behavior for legacy vaults.
    transcription: str | None = None
    # OpenRouter video-model profile for [animation] renderer = "video_model"
    # (Settings materializes it as openrouter_video). Empty = the video
    # renderer is unavailable; manim rendering is unaffected.
    video_generation: str | None = None
    # Project understanding (spec_project_understanding_v1 §7): delayed-probe
    # authoring and the closed-book check. Empty = follow the grading route,
    # then ai.active_provider. Probe grading itself uses the grading route.
    project: str | None = None
    # Action router and the learner field's llm_probability arms (router spec
    # §6.2). The decider routes accept only a `decider` profile: empty = the
    # code-default openrouter_decider profile; never a chat fallback and never
    # LEARNLOOP_AI_PROVIDER. The LLM routes are ordinary chat routes: empty =
    # ai.active_provider (Codex on the subscription is allowed).
    # Tier 1 (owner 2026-10-13): the small judgments [decider_routes] moves
    # to the Decider; empty = the code-default openrouter_decider profile.
    tier1_decider: str | None = None
    router_decider: str | None = None
    router_llm: str | None = None
    llm_probability_decider: str | None = None
    llm_probability_llm: str | None = None
    # Method-explicit items (owner rule 2026-10-13): the judge of `learnloop
    # grading method-phrasing`, which reads whether a rubric criterion is
    # phrased by method. A decider profile (typed choice questions) or a chat
    # profile. Empty = the Tier-1 Decider (tier1_decider's profile, else the
    # code-default openrouter_decider) when it is ready, else
    # ai.active_provider; with neither ready the report falls back to the
    # conservative heuristic and says so. The same judge makes the one-time
    # required-method statement judgments (redesign 2026-10-14: a textbook
    # statement at import, a PF variant's stem at selection; the Decider only
    # while decider_routes.required_method_statement is on), with no heuristic
    # fallback; grading never uses it.
    rubric_phrasing_judge: str | None = None
    # Reader workbench RW1b (spec_reader_workbench_v1 §4.2): the intent box's
    # router, one typed choice to a decision model. A decider-only route:
    # empty = the code-default openrouter_decider profile, never a chat
    # fallback and never LEARNLOOP_AI_PROVIDER.
    reader_intent: str | None = None
    # Reader workbench RW4a (spec_reader_workbench_v1 §7.3, §7.6): the library
    # answer's organizer, one listwise call (a note per passage on what it
    # contributes). Empty = ai.active_provider; a metered route needs
    # source_retrieval.llm_price_per_million or the notes are skipped and
    # labelled. Serves live requests, so the fast route is recommended.
    library_organizer: str | None = None
    # Adaptive hints H1 (spec_adaptive_hints_v1 §4.3, §7.2): the approach-map
    # builder and the learner-route merge, one structured call each, in the
    # background (never on a request path). Empty = ai.active_provider; any
    # chat profile, Codex (codex_low) included. Metered routes are held to
    # hints.maps.max_daily_cost_usd at hints.price_per_million (unset: a
    # metered build is refused before sending); Codex is estimated_only.
    approach_map: str | None = None
    # Adaptive hints H2a (spec_adaptive_hints_v1 §4.5, §7.2): the hint
    # chooser, one Decider request with two typed questions (kind and level;
    # horizon). A decider-only route: empty = the code-default
    # openrouter_decider profile, never a chat fallback and never
    # LEARNLOOP_AI_PROVIDER.
    hint_chooser: str | None = None
    # Adaptive hints H2a (§4.6, §7.2, D9): the hint writer, one structured
    # chat call per hint on the request path. Empty = ai.active_provider, but
    # it never resolves to Codex (too slow for a hint): a Codex route falls
    # back to the item's authored hints and says so. A ChatGPT-plan profile is
    # recommended; a metered one is held to hints.max_daily_cost_usd at
    # hints.price_per_million (unset: refused before sending).
    hint_writer: str | None = None
    # Adaptive hints H2b (spec_adaptive_hints_v1 §6.1, §7.2, D11): outcome
    # placement, one structured call in the background after a hinted answer
    # graded not fully correct (never on a request path). Empty =
    # ai.active_provider; any chat profile, Codex (codex_low) included.
    # Metered routes join hints.maps.max_daily_cost_usd at
    # hints.price_per_million (unset: refused before sending).
    hint_outcome: str | None = None
    # Adaptive difficulty AD1 (spec_adaptive_difficulty_v1 §8.2, §7.2, D4):
    # the outside forecasters (background, never on a request path) and the
    # feature audit's LLM fallback. ad_forecast_llm serves llm_v1:item and
    # llm_v3:llm: empty = ai.active_provider (Codex on the subscription is
    # estimated_only). ad_forecast_decider serves llm_v3:decider, a
    # decider-only route: empty = the code-default openrouter_decider
    # profile, never a chat fallback and never LEARNLOOP_AI_PROVIDER. The
    # audit's Decider is tier1_decider's; ad_feature_audit is its LLM judge
    # (empty = ai.active_provider). Metered calls are held to
    # adaptive_difficulty.daily_spend_cap_usd (an LLM route at
    # adaptive_difficulty.price_per_million; unset: refused before sending).
    ad_forecast_llm: str | None = None
    ad_forecast_decider: str | None = None
    ad_feature_audit: str | None = None
    # Reader workbench RW2b (spec_reader_workbench_v1 §5.2, §5.8): "Check my
    # work", one structured chat call on the request path (step verdicts,
    # the step graph, the map node each valid step reaches, the error-kind
    # guess, the declared symbolic checks). Empty = ai.active_provider.
    # Codex runs it on the owner's subscription (estimated_only, fix round 1,
    # F12; the spec's D7 recommends a ChatGPT-plan or fast OpenRouter profile
    # for latency, reported, not enforced). A metered profile is held to workbench.max_daily_cost_usd at
    # workbench.price_per_million (unset: refused before sending).
    workbench_check: str | None = None
    # Reader workbench RW3b (spec_reader_workbench_v1 §6.2, §6.4): the cue
    # judge, one listwise call per cue target (a verdict, a quote and the
    # instructional roles per passage), in the background when a source opens
    # (never on a request path). Empty = ai.active_provider (Codex by default,
    # estimated_only); a metered route needs
    # source_retrieval.llm_price_per_million and is held to
    # cues.max_daily_cost_usd, or the judgment is skipped and labelled.
    passage_cue_judge: str | None = None
    # Reader workbench RW4e (spec_reader_workbench_v1 §7.9): the owner-run
    # batch role labeller (`learnloop reader label-roles`), one listwise call
    # per batch of a source's passages in reading order (instructional roles
    # with a confidence, written as source-object proposals). Never on a
    # request path. Empty = ai.active_provider (Codex is estimated_only); a
    # metered route needs source_retrieval.llm_price_per_million and is held
    # to roles.batch_max_cost_usd per run, checked before each batch.
    role_labeller: str | None = None
    # Reader workbench RW7a (spec_reader_workbench_v1 §10.1): the reading-path
    # judge, one structured call per source and depth over the section list
    # (labels, roles, the linked LOs' statuses, the depth and the goal's
    # title), cached by its state key. Empty = ai.active_provider (Codex is
    # estimated_only); a metered route needs
    # source_retrieval.llm_price_per_million and is held to
    # reading_paths.max_daily_cost_usd, checked before the call.
    reading_path_judge: str | None = None
    # Reader workbench RW5a (spec_reader_workbench_v1 §8.5): explorable
    # figures. figure_author writes the declarative figure spec (a chat route;
    # a region or figure block sends its crop as an image when the profile
    # lists "image" in input_modalities). RW5a has no verifier route: the
    # source check is RW5c's. Empty = ai.active_provider (Codex allowed,
    # estimated_only). Metered calls are held to figures.max_daily_cost_usd at
    # figures.price_per_million (unset: refused before sending).
    figure_author: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _drop_retired_routes(cls, data: Any) -> Any:
        # Backwards compatible: a retired route key is ignored, never an error.
        if isinstance(data, dict) and any(name in data for name in RETIRED_ROUTES):
            return {key: value for key, value in data.items() if key not in RETIRED_ROUTES}
        return data

    @model_validator(mode="after")
    def _default_embedding_route(self) -> "AIRoutingConfig":
        # Empty is unset, as for every other route: the code-default profile.
        if not (self.embedding or "").strip():
            self.embedding = DEFAULT_EMBEDDING_PROVIDER
        return self


#: The shared output-token budget of every LLM role (owner, 2026-10-12): large
#: enough for a reasoning model's thinking plus its answer, so no role is cut
#: off by a hand-set cap. ``learnloop.ai.output_budget`` resolves it.
DEFAULT_OUTPUT_TOKENS = 16_384
#: Reasoning efforts a route may request; "" (or "profile") keeps the profile's.
REASONING_EFFORTS = frozenset({"", "profile", "none", "minimal", "low", "medium", "high", "xhigh"})
#: Routes that ask for low reasoning effort unless the owner says otherwise
#: (owner, 2026-10-12): T6's live query rewrite and tutor-span verification.
DEFAULT_ROUTE_REASONING_EFFORT: dict[str, str] = {
    "source_query_rewrite": "low",
    "source_rerank": "low",
    # Reader workbench RW4a: the library answer's organizer serves live requests.
    "library_organizer": "low",
}


class AIConsentRecord(BaseModel):
    """One learner OK for one data flow to one AI provider (UX Phase 1, Q4).

    Recorded once, when the provider is connected, instead of a checkbox per
    build. ``data_flow`` names what may leave the machine; an action that
    would send something new asks again in place."""

    model_config = ConfigDict(extra="allow")

    granted_at: str
    data_flow: str = "passages_and_answers"


class AIConfig(BaseModel):
    # Plan-first transport T1 (owner, 2026-10-21): the tool-free ChatGPT plan.
    active_provider: str = "chatgpt"
    # A configured readiness fallback for routes that allow one. Never an
    # agent-harness (Codex) profile: such a fallback is ignored.
    fallback_provider: str | None = None
    # Owner opt-in for the Codex agent harness (codex_sdk / http profiles).
    # False (default): every such profile is refused for every task before
    # any process starts, and `learnloop doctor` reports routes that pin one.
    agent_harness_opt_in: bool = False
    # The OpenRouter profile offered when the ChatGPT plan is unavailable
    # (signed out, paused, usage limit, refresh failure). LearnLoop only ASKS:
    # nothing is sent to it until the learner chooses "Use OpenRouter instead"
    # (desktop: that feature for this session) or sets
    # LEARNLOOP_AI_FALLBACK=openrouter (CLI: that command). No offer without
    # its API key; "" never offers.
    plan_fallback_profile: str = "openrouter"
    timeout_seconds: int = 180
    providers: dict[str, AIProviderProfile] = Field(default_factory=dict)
    routing: AIRoutingConfig = Field(default_factory=AIRoutingConfig)
    # Output budget of every LLM role, in tokens (the request's max_tokens and
    # the spend reservation). route_output_tokens replaces it for one route. A
    # profile's own max_tokens is a ceiling: it replaces the default for that
    # profile and holds a route override to it (the transport never sends
    # more). A truncated answer is logged and retried once at double the
    # budget (held to that ceiling; a call at it fails), never accepted.
    output_tokens: int = Field(default=DEFAULT_OUTPUT_TOKENS, ge=256)
    route_output_tokens: dict[str, int] = Field(default_factory=dict)
    # Reasoning effort per route ("low", "medium", ...; "" or "profile" keeps
    # the profile's reasoning_effort). Sent where the provider supports it
    # (OpenRouter's reasoning.effort, Codex's turn effort). Entries merge over
    # DEFAULT_ROUTE_REASONING_EFFORT.
    route_reasoning_effort: dict[str, str] = Field(
        default_factory=lambda: dict(DEFAULT_ROUTE_REASONING_EFFORT))
    # Keyed by provider family ("codex", "chatgpt", "openrouter", or a
    # profile name), see learnloop.content.pipeline.add_source.consent_key.
    consent: dict[str, AIConsentRecord] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _normalize_provider_profiles(cls, data: Any) -> Any:
        from learnloop.config.compat import normalize_ai_input

        return normalize_ai_input(data)

    @field_validator("route_output_tokens")
    @classmethod
    def _known_route_budgets(cls, value: dict[str, int]) -> dict[str, int]:
        _require_known_routes(value, "ai.route_output_tokens")
        for route, tokens in value.items():
            if type(tokens) is not int or tokens < 256:
                raise ValueError(f"ai.route_output_tokens.{route} must be an integer of at least 256")
        return value

    @field_validator("route_reasoning_effort", mode="before")
    @classmethod
    def _merge_route_efforts(cls, value: Any) -> Any:
        # An owner table names only the routes it changes; the defaults stay.
        if isinstance(value, dict):
            return {**DEFAULT_ROUTE_REASONING_EFFORT, **value}
        return value

    @field_validator("route_reasoning_effort")
    @classmethod
    def _known_route_efforts(cls, value: dict[str, str]) -> dict[str, str]:
        _require_known_routes(value, "ai.route_reasoning_effort")
        for route, effort in value.items():
            if str(effort).strip().lower() not in REASONING_EFFORTS:
                raise ValueError(
                    f"ai.route_reasoning_effort.{route} must be one of "
                    f"{', '.join(sorted(name for name in REASONING_EFFORTS if name))} or empty"
                )
        return {route: str(effort).strip().lower() for route, effort in value.items()}


def _require_known_routes(value: dict[str, Any], setting: str) -> None:
    # A retired route's budget or effort is ignored, never an error.
    unknown = sorted(set(value) - set(AIRoutingConfig.model_fields) - set(RETIRED_ROUTES))
    if unknown:
        raise ValueError(f"{setting} names unknown routes: {', '.join(unknown)}")


DEFAULT_CODEX_MODEL = "gpt-5.6-sol"
DEFAULT_CODEX_REASONING_EFFORT = "low"
LEGACY_CODEX_MODEL = "gpt-5.5"
CODEX_LOW_PROVIDER = "codex_low"
CODEX_MEDIUM_PROVIDER = "codex_medium"
# The cheapest Codex model the owner's account lists (`gpt-6-luna`, "fast and
# affordable model for easier tasks"; checked in the Codex CLI's model list on
# 2026-10-12). Code-default profile for cheap judges such as facet identity.
CODEX_LUNA_PROVIDER = "codex_luna"
CODEX_LUNA_MODEL = "gpt-6-luna"
CODEX_PROVIDER_NAMES = frozenset({"codex", CODEX_LOW_PROVIDER, CODEX_MEDIUM_PROVIDER, CODEX_LUNA_PROVIDER})
# Claude Haiku through OpenRouter: the metered alternative for cheap judges
# (OpenRouter listing on 2026-10-12: $0.10 per million input tokens, $0.50
# per million output tokens).
OPENROUTER_HAIKU_PROVIDER = "openrouter_haiku"
OPENROUTER_HAIKU_MODEL = "anthropic/claude-haiku-5.5"
OPENROUTER_TRANSCRIPTION_PROVIDER = "openrouter_transcription"

#: Profile types that run an agent harness (the Codex app-server, or the
#: retired HTTP adapter in front of it). Plan-first transport T1 (owner,
#: 2026-10-21): refused for every serving task unless
#: ``ai.agent_harness_opt_in`` is set, and never a fallback.
AGENT_HARNESS_PROFILE_TYPES = frozenset({"codex_sdk", "http", "http_adapter"})

# Plan-first transport T1 (owner, 2026-10-21): every serving route defaults to
# LearnLoop's own tool-free ChatGPT-plan client (one POST /v1/responses per
# admitted request, store=false, no tools). The slugs are the ones the Codex
# profiles served; the owner confirms them with `learnloop ai models chatgpt`
# and sets [ai.providers.chatgpt] model (the low/medium copies follow it).
CHATGPT_PLAN_PROVIDER = "chatgpt"
CHATGPT_LOW_PROVIDER = "chatgpt_low"
CHATGPT_MEDIUM_PROVIDER = "chatgpt_medium"
CHATGPT_LUNA_PROVIDER = "chatgpt_luna"
DEFAULT_CHATGPT_PLAN_MODEL = DEFAULT_CODEX_MODEL
CHATGPT_LUNA_MODEL = CODEX_LUNA_MODEL
CHATGPT_PLAN_PROVIDER_NAMES = frozenset({
    CHATGPT_PLAN_PROVIDER, CHATGPT_LOW_PROVIDER, CHATGPT_MEDIUM_PROVIDER, CHATGPT_LUNA_PROVIDER,
})

#: The code-default route of each task that names a tiered profile (an unset
#: route of a vault whose active provider is the plan).
DEFAULT_SERVING_TASK_ROUTES = {
    "grading": CHATGPT_LOW_PROVIDER,
    "canonical_ingest": CHATGPT_MEDIUM_PROVIDER,
    "canonical_ingest_retry": CHATGPT_MEDIUM_PROVIDER,
    "authoring": CHATGPT_MEDIUM_PROVIDER,
    "tutor_qa": CHATGPT_LOW_PROVIDER,
    "teach_back": CHATGPT_LOW_PROVIDER,
    "rung_variant": CHATGPT_LOW_PROVIDER,
    "animation": CHATGPT_MEDIUM_PROVIDER,
    "facet_identity_judge": CHATGPT_LUNA_PROVIDER,
}
#: The pre-T1 table: the routes of a vault whose active provider is Codex
#: (served only with ``ai.agent_harness_opt_in``; `learnloop doctor` reports
#: them otherwise). Also the meaning of a legacy ``routing.<task> = "codex"``.
LEGACY_CODEX_TASK_ROUTES = {
    "grading": CODEX_LOW_PROVIDER,
    "canonical_ingest": CODEX_MEDIUM_PROVIDER,
    "canonical_ingest_retry": CODEX_MEDIUM_PROVIDER,
    "authoring": CODEX_MEDIUM_PROVIDER,
    "tutor_qa": CODEX_LOW_PROVIDER,
    "teach_back": CODEX_LOW_PROVIDER,
    "rung_variant": CODEX_LOW_PROVIDER,
    "animation": CODEX_MEDIUM_PROVIDER,
    "facet_identity_judge": CODEX_LUNA_PROVIDER,
}
#: `learnloop doctor --fix`: the plan profile that replaces each code-default
#: Codex profile (no silent aliasing at load: receipts key on provider+model).
CODEX_TO_PLAN_PROFILE = {
    "codex": CHATGPT_PLAN_PROVIDER,
    CODEX_LOW_PROVIDER: CHATGPT_LOW_PROVIDER,
    CODEX_MEDIUM_PROVIDER: CHATGPT_MEDIUM_PROVIDER,
    CODEX_LUNA_PROVIDER: CHATGPT_LUNA_PROVIDER,
}


class ErrorImpact(BaseModel):
    """Error impact settings.

    ``lo_mastery_delta`` remains for legacy compatibility. New recall coverage
    code uses ``local_severity_gain`` to sharpen the EKF observation instead of
    applying a separate mastery nudge.
    """

    families: dict[str, float] = Field(default_factory=dict)
    lo_mastery_delta: float = 0.0
    local_severity_gain: float = 0.8


class FsrsFittingConfig(BaseModel):
    """`learnloop fit fsrs` knobs (architecture_pivot.md Stage 1)."""

    min_reviews: int = 50
    min_elapsed_days: float = 0.5
    l2_lambda: float = 1.0
    max_iterations: int = 300
    initial_step: float = 0.05
    min_relative_improvement: float = 0.01


class FittingConfig(BaseModel):
    fsrs: FsrsFittingConfig = Field(default_factory=FsrsFittingConfig)


class LocksConfig(BaseModel):
    """Retired: facet identity locks were removed (owner, 2026-10-12).

    Facets used to lock when their direct evidence spanned
    ``facet_surface_groups`` distinct surface/correlation groups, reached
    ``facet_lock_mass`` independent mass, or entered an active goal's
    certified scope; a locked facet refused merges and rewording. Nothing
    reads these values any more: merges apply live with an undo and a reword
    writes a facet version (knowledge-model §3.4). The section stays in the
    schema so the effective-defaults snapshots of every released version stay
    as recorded; ``learnloop doctor`` warns when a vault sets it.
    """

    facet_lock_mass: float = 2.0
    facet_surface_groups: int = 2


class EvidenceMassEntry(BaseModel):
    """Evidence carried by one attempt type (Fable's-take item 3).

    ``evidence_mass`` weights ability-belief updates (mastery EKF reliability);
    ``surface_exposure`` is the fraction of the item's facet surface the attempt
    certifies as probed (coverage). ``surface_exposure = None`` means "same as
    evidence_mass". They diverge only where diagnosis and demonstration differ:
    a confident "don't know" fully covers the surface as evidence-of-absence
    (exposure 1.0) but is self-diagnosis, not demonstration (mass 0.7).
    """

    evidence_mass: float = 1.0
    surface_exposure: float | None = None


def default_attempt_type_evidence() -> dict[str, EvidenceMassEntry]:
    return {
        "independent_attempt": EvidenceMassEntry(evidence_mass=1.0),
        "open_text": EvidenceMassEntry(evidence_mass=1.0),
        "diagnostic_probe": EvidenceMassEntry(evidence_mass=1.0),
        "hinted_attempt": EvidenceMassEntry(evidence_mass=1.0),
        "reconstruction_after_walkthrough": EvidenceMassEntry(evidence_mass=0.5),
        "dont_know": EvidenceMassEntry(evidence_mass=0.7, surface_exposure=1.0),
        "self_report": EvidenceMassEntry(evidence_mass=0.3),
        "exam_evidence": EvidenceMassEntry(evidence_mass=0.35),
        # Held-out practice-exam answer on a fresh, never-practiced item: the
        # highest-quality evidence in the system, so full mass (unlike the
        # discounted exam_evidence import type above).
        "exam_attempt": EvidenceMassEntry(evidence_mass=1.0),
        # High-quality generative evidence, but one correlated multi-question
        # conversation, so less than a full independent attempt per facet.
        "teach_back": EvidenceMassEntry(evidence_mass=0.8),
        "guided_walkthrough": EvidenceMassEntry(evidence_mass=0.0),
        "skip": EvidenceMassEntry(evidence_mass=0.0),
    }


def default_practice_mode_item_coverage() -> dict[str, float]:
    return {
        "constructed_response": 0.85,
        "open_text": 0.85,
        "short_answer": 0.75,
        "diagnostic_probe": 0.80,
        "independent_attempt": 0.75,
        "hinted_attempt": 0.65,
        "multiple_choice": 0.45,
        "self_report": 0.25,
    }


class EvidenceCorrelationConfig(BaseModel):
    """Vault-wide surface-correlation discounting (knowledge-model spec §6).

    Reserved in Phase 0 of the KM/ingestion-v2 plan; consumed from KM2.
    """

    model_config = ConfigDict(extra="allow")


class EvidenceCertificationConfig(BaseModel):
    """Bounded certification credit (knowledge-model §5.4).

    ``max_groups_per_attempt`` caps how many independently-observable
    correlation groups one attempt may certify (the attempt-wide ceiling is
    ``evidence_mass(attempt_type) * max_groups_per_attempt``). ``group_budgets``
    overrides the per-``(attempt_type, group)`` budget, which otherwise defaults
    to ``evidence_mass(attempt_type)``. KM1 ships this table as data; the write
    path that consumes it lands with KM2.

    ``max_embedded_credit_share`` is A1 guard 2 (``spec_measurement_efficiency_v1``
    §3.A1): no ``(facet, capability)`` cell may take more than this fraction of
    its certification credit from *embedded* (supporting-role) observations. A1
    lets one conjunctive item credit several cells at once, and the passed-facet
    firewall only protects the negative direction — positive smearing has no
    firewall and nobody contests being told they know something. At the default
    0.5 a cell needs at least as much direct as embedded credit, so a cell whose
    entire history is supporting credit reads as *inferred* (Part II's honest
    label), never as demonstrated. Set to 1.0 to disable the cap.
    """

    model_config = ConfigDict(extra="allow")

    max_groups_per_attempt: int = 3
    group_budgets: dict[str, float] = Field(default_factory=dict)
    max_embedded_credit_share: float = 0.5


class EvidenceBlueprintsConfig(BaseModel):
    """Blueprint recipe likelihood defaults (knowledge-model spec §9.2)."""

    model_config = ConfigDict(extra="allow")

    slip: float = 0.05
    guess_by_format: dict[str, float] = Field(
        default_factory=lambda: {"multiple_choice": 0.25, "constructed_response": 0.0}
    )


class EvidenceConfig(BaseModel):
    """Single source of truth for per-attempt-type evidence carried.

    Replaces the former ``ATTEMPT_TYPE_FACTORS`` (mastery/reliability) and
    ``ATTEMPT_TYPE_COVERAGE_FACTORS`` (coverage) module tables, which had
    drifted apart for the same attempt modes.
    """

    attempt_types: dict[str, EvidenceMassEntry] = Field(default_factory=default_attempt_type_evidence)
    item_coverage_by_practice_mode: dict[str, float] = Field(
        default_factory=default_practice_mode_item_coverage
    )
    item_coverage_default: float = 0.75
    correlation: EvidenceCorrelationConfig = Field(default_factory=EvidenceCorrelationConfig)
    certification: EvidenceCertificationConfig = Field(
        default_factory=EvidenceCertificationConfig
    )
    blueprints: EvidenceBlueprintsConfig = Field(default_factory=EvidenceBlueprintsConfig)

    @model_validator(mode="after")
    def _merge_defaults(self) -> "EvidenceConfig":
        # A vault TOML overriding one attempt type must not silently reset the
        # others to 1.0 (a partial [evidence.attempt_types] replaces the dict).
        for attempt_type, entry in default_attempt_type_evidence().items():
            self.attempt_types.setdefault(attempt_type, entry)
        for mode, coverage in default_practice_mode_item_coverage().items():
            self.item_coverage_by_practice_mode.setdefault(mode, coverage)
        return self


class CapabilitiesConfig(BaseModel):
    """Capability damping/shrinkage + lazy residual activation (spec §4.2).

    Residual activation ships behind config, DEFAULT OFF. The thresholds below are
    open calibration knobs (KM5): the shared parent stays the launch prediction
    state, and a learner-specific ``(facet, capability)`` residual is only
    activated when a closed diagnostic episode demonstrates divergence OR the
    capability-sliced residual persistently disagrees with the pooled parent.
    """

    model_config = ConfigDict(extra="allow")

    # Master switch (§4.2 / §14 "capability-residual-by-default" is Deferred).
    residual_activation_enabled: bool = False
    # |capability_mean - parent_mean| that counts as a persistent residual
    # disagreement (open calibration knob).
    residual_divergence_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    # Independent evidence required before the persistent-disagreement trigger
    # fires (guards against activating on a single noisy surface).
    residual_min_independent_mass: float = Field(default=2.0, ge=0.0)
    residual_min_independent_groups: int = Field(default=2, ge=1)
    # A closed diagnostic episode demonstrating divergence activates at this
    # lower divergence threshold (the episode already paid for the evidence).
    residual_episode_divergence_threshold: float = Field(default=0.12, ge=0.0, le=1.0)
    # Shared parent as a shrinkage prior: pseudo-count strength pulling the
    # residual belief toward the pooled parent mean while capability data is thin.
    residual_shrinkage_pseudo_count: float = Field(default=4.0, ge=0.0)


class TraceEvidenceConfig(BaseModel):
    """A6 opportunistic trace evidence and its elicitation budget (Meas §3.A6).

    Two knobs, and the second is the one that matters. ``max_elicitations_per_session``
    is the hard budget on asking the learner for a one-line justification: "more
    explanation is more evidence, so there is a standing temptation to demand it
    everywhere. Do not." A system that makes people narrate their arithmetic has
    traded a measurement problem for a retention problem (§11 non-goals), and
    standing constraint 10 makes annoyance a first-class regression.

    ``elicitation_enabled`` exists because the *reporting* half of A6 (the grader
    naming facets it saw) has no learner cost and should not be revertible by the
    same switch as the half that does.
    """

    model_config = ConfigDict(extra="allow")

    elicitation_enabled: bool = True
    max_elicitations_per_session: int = 2


class DiagnosticAugmentationConfig(BaseModel):
    """Stage 7 live diagnosis rungs.

    ``sample_count`` is C3's k and therefore both a support and cost decision.
    ``history_limit`` is C4's anchoring/exposure bound.  They are explicit
    registry parameters rather than module constants so a revert can restore
    the one-sample/no-history baseline without changing historical receipts.

    The shipped default is the ONE-SAMPLE BASELINE (``sample_count=1``).  C1-C4
    were promoted live simultaneously under a single grading-prompt bump, which
    the augmentation spec forbids: each rung carries its own hypothesis and
    revert criterion and therefore needs its own promotion.  k=3 tripled the paid
    grading calls per graded attempt and, on disagreement, rewrote the winning
    attribution to ``unresolved`` -- a live behaviour change that never had its
    own trial.  k>1 stays available (planted-eval harness, or a deliberate
    promotion trial) by setting it here; it is not the default a learner pays for.
    """

    model_config = ConfigDict(extra="allow")

    sampling_enabled: bool = True
    sample_count: int = Field(default=1, ge=1, le=9)
    history_limit: int = Field(default=4, ge=0, le=20)


class DiagnosisConfig(BaseModel):
    """Slice 1 M2: the live blind grader + asynchronous history-aware diagnoser.

    Dormant below ``mvp-0.10``: the algorithm version, not this section, decides
    whether a vault grades split (spec §6.2). ``split_enabled`` is the kill
    switch: off, an ``mvp-0.10`` (or later) vault grades NEW attempts jointly as
    ``mvp-0.9`` did; already-blind attempts keep their records and replay from
    them (an attempt's grader mode is persisted, never read from this switch).
    ``history_mode`` defaults to ``full`` (O16) and is changed by config once the
    M1 report is reviewed.
    """

    split_enabled: bool = True
    history_mode: Literal["exact", "full", "snapshot", "hybrid"] = "full"
    full_history_token_budget: int = Field(default=100_000, ge=1_000)
    exact_history_token_budget: int = Field(default=12_000, ge=1_000)
    history_error_limit: int = Field(default=6, ge=0, le=50)
    history_success_limit: int = Field(default=4, ge=0, le=50)
    # Diagnoser k-sampling (cause disagreement, §4.4) is not built in M2: one
    # diagnosis per attempt, so only 1 is accepted rather than ignored.
    sample_count: int = Field(default=1, ge=1, le=1)
    correct_answer_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    # Joint vaults only: run the diagnoser in shadow next to the joint grader.
    shadow: bool = False
    next_item_wait_seconds: float = Field(default=10.0, ge=0.0, le=120.0)
    max_attempts: int = Field(default=5, ge=1, le=20)
    # Per-turn deadline for a Codex diagnoser turn. The diagnosis is async (no
    # learner waits on it beyond next_item_wait_seconds), so it need not share
    # the interactive ai.timeout_seconds; it stays under the job lease (1200 s).
    timeout_seconds: int = Field(default=300, ge=30, le=1_000)
    # Diagnoser calls per UTC day; past it a job is skipped ("budget"), never the grade.
    max_calls_per_day: int = Field(default=500, ge=0)
    # The diagnosis card (§12.2) and whether its taps reach an open
    # unresolved-cause factor's self-report channel (O14).
    card_enabled: bool = True
    forward_card_taps: bool = True
    # Diagnosis input provenance (spec_mcp_frontend_c1 §4.8): the chat
    # frontend shows a model-written text (a diagnosis summary, a hypothesis,
    # a misconception or candidate statement, a learner question's words, a
    # generated topic's name) only when its write-time record is complete and
    # every recorded input is safe. Off: chat holds every such text back (the
    # C1a narrow rule). Writers record either way; nothing is evidence.
    # Off as landed (2026-10-15, owner: "land narrow, then fix source"): the
    # final verify reopened two High findings in the release path (a gap
    # reader's record folds topics without checking the titles it showed; C4
    # history dependencies escape grading validation). It stays off until
    # every model-context build records through one capture point and a clean
    # verify passes (docs/reviews/diagnosis-input-provenance.md, "Landing
    # onto main").
    chat_shows_recorded_text: bool = False
    # PF-c (spec_embedding_consumers_v1 §5.5): reference policy, valid-
    # alternative path and solve-first in the blind prompt. Off restores the
    # mvp-2.0 blind prompt exactly.
    grading_support: bool = True
    # Hybrid kNN (S1.4b): shortlist size, fused top-N, reciprocal-rank k.
    knn_limit: int = Field(default=8, ge=1, le=64)
    hybrid_keep: int = Field(default=6, ge=1, le=64)
    rrf_k: int = Field(default=60, ge=1)
    # mvp-0.21 Part 2 (the Guide-fix audit's question 1, owner decision
    # 2026-10-12/13): under split grading the probe hypothesis lane (the
    # follow-up misconception gate's hypothesis set) reads the diagnoser's
    # verdict through the diagnosis overlay instead of the blind grader's
    # taxonomy prior. Dormant below mvp-0.21; off, the lane reads the stored
    # events exactly as mvp-0.16 does.
    probe_lane_reads_diagnosis: bool = True
    # While an event's live diagnosis is pending: "hold_out" leaves it out of
    # the lane until the diagnoser's verdict arrives (the recommended default);
    # "keep_prior" admits it on the stored flag meanwhile. A failed or skipped
    # diagnosis never arrives, so its event is read as stored either way.
    probe_lane_pending: Literal["hold_out", "keep_prior"] = "hold_out"
    # Saved diagnosis forecasts (owner go-ahead 2026-10-15; docs/reviews/
    # diagnosis-forecast-receipts.md): a completed diagnosis and a scheduled
    # repair cold check each write their forecast as a forecast_receipts row in
    # the deciding transaction, scored later by `learnloop diagnosis
    # calibration`. Logging only (no grading, scoring, scheduling or serving
    # change, so no successor); off writes nothing and reads stay possible.
    forecast_receipts: bool = True


class RecurrenceBlockingCutoff(BaseModel):
    """One benchmark-set blocking cutoff and the vectors it was measured on.

    B3 writes the whole entry. The cutoff describes the cosine distribution of
    exactly this model, width, text recipe and task prefix, so the shortlist
    applies it only to stored vectors of that identity and refuses it (top-k
    alone then blocks) for any other.
    """

    model_config = ConfigDict(extra="forbid")

    cutoff: float
    dims: int = Field(gt=0)
    recipe: str = Field(min_length=1)
    task_prefix: str = Field(min_length=1)
    target_recall: float | None = Field(default=None, gt=0.0, le=1.0)
    confirmed_matches: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _a_cosine(self) -> "RecurrenceBlockingCutoff":
        value = float(self.cutoff)
        if value != value or not -1.0 <= value <= 1.0:
            raise ValueError("a blocking cutoff must be a cosine in [-1, 1]")
        return self


class RecurrenceConfig(BaseModel):
    """Slice 2 T1 (M3): recurrence groups with authority (spec_embedding_consumers_v1 §3).

    Dormant below ``mvp-0.12``: the algorithm version, not this section, decides
    whether grouping sites read recurrence groups. ``enabled`` is the kill
    switch: off, an ``mvp-0.12`` vault groups by exact statement again (vault
    open and every normalization re-sync the groups projection; consumers that
    hold the vault check the switch directly); verdicts already in
    ``judgment_ledger`` are kept.

    Candidate pairs for the same-cause judge come from hypothesis-embedding
    kNN: the top ``top_k`` earlier hypotheses in scope, and, for a model with
    a benchmark-set cutoff in ``blocking_cutoffs`` (model id -> B3's entry:
    the cutoff and the width, recipe and prefix it was measured on), only
    those at or above it. No cutoff is hand-set: an empty map blocks by top-k
    alone, and an entry measured on other vectors is refused. Scores never
    merge or reject anything.

    ``require_guard`` (default false, owner 2026-10-12) decides only whether
    `learnloop upgrade` to mvp-0.12 refuses while the same-answer/different-
    cause guard has not passed; it changes nothing a vault serves.
    """

    enabled: bool = True
    # `learnloop upgrade` to mvp-0.12 refuses until the same-answer/
    # different-cause guard passes for the configured judge. Off (the default,
    # owner 2026-10-12): the guard is advisory; the upgrade prints its status
    # and proceeds.
    require_guard: bool = False
    # The live same-cause judge inside the diagnose job (the backlog command
    # and the guard run regardless; they are explicit owner commands).
    judge_enabled: bool = True
    top_k: int = Field(default=3, ge=1, le=20)
    blocking_cutoffs: dict[str, RecurrenceBlockingCutoff] = Field(default_factory=dict)
    # Live judge calls per diagnose job; pairs beyond it wait for the backlog.
    judge_max_pairs_per_attempt: int = Field(default=4, ge=0, le=20)
    # Per-turn deadline for one Codex judge turn.
    judge_timeout_seconds: int = Field(default=180, ge=30, le=1_000)
    # The escalated-repair block on the diagnosis card (UI only).
    escalation_card_enabled: bool = True
    # §3.7: when a group reaches K and none of the diagnosis's repairs differs
    # from the repairs shown before, ask the diagnosis route once for a repair
    # with a different operator and representation. Off: the card says the
    # repair is the same kind as before.
    escalation_repair_enabled: bool = True

    @model_validator(mode="after")
    def _cutoffs_name_models(self) -> "RecurrenceConfig":
        for model_id in self.blocking_cutoffs:
            if not str(model_id).strip():
                raise ValueError("recurrence.blocking_cutoffs keys must be embedding model ids")
        return self


class StuckPromptConfig(BaseModel):
    """"Write what you can" replaces "I don't know" (``mvp-0.13``).

    Dormant below ``mvp-0.13``: the algorithm version, not this section,
    decides whether the learner's surfaces offer "I'm stuck". ``enabled`` is
    the kill switch: off, an ``mvp-0.13`` vault shows "I don't know" and
    records ``dont_know`` at its configured mass exactly as ``mvp-0.12`` does.
    Already-recorded stuck answers keep their meaning (``declared_stuck`` is
    persisted per attempt and replay never reads this switch).
    """

    enabled: bool = True


class HintsMapsConfig(BaseModel):
    """Adaptive hints H1: approach maps (spec_adaptive_hints_v1 §4.3, §4.3.1, §9).

    An approach map is a small subgoal graph of one item (nodes, edges and
    alternative routes with their origin) built by one structured call on
    route ``ai.routing.approach_map`` from the item's reference solution,
    rubric, authored hints, trace contract, PF skeleton, the learner's own
    textbook worked examples and the learner's own correct solutions, checked
    in code and stored in ``approach_maps`` (a revised item or changed seeds
    gets a new row). Nothing in H1 shows a map: the hint writer (H2) and the
    Reader workbench (RW2b) read it later, and the grader never does.

    ``build_on_serve``: when the practice screen serves an item that has no
    map for its current revision, one is built in the background (never on the
    request path: the serve neither waits for it nor changes because of it),
    once per item revision; it also governs the lazy learner-route merge a
    shown hint schedules in the background when the item's map predates the
    learner's newest correct answers in its family (H2a, §4.3.1 row 3). Each
    such build or merge is one model call (Codex on the
    subscription is ``estimated_only``); ``learnloop hints report`` shows the
    counts and the day's spend. ``max_daily_cost_usd``: the metered dollars a
    UTC day for map builds and merges, shared by every process (a capped day
    builds nothing more and says so). ``enabled`` is the kill switch: off,
    nothing is built and nothing reads a map. Maps are help, never evidence:
    no scoring, scheduling, projection or serving change, so no successor.
    """

    enabled: bool = True
    build_on_serve: bool = True
    max_daily_cost_usd: float = Field(default=0.50, ge=0.0)


class HintsConfig(BaseModel):
    """Adaptive hints (spec_adaptive_hints_v1 §9). H0 adds only the telemetry.

    ``telemetry_enabled``: the practice screen records each authored hint it
    reveals as a ``help_assists`` row (``practice.record_hint_reveal``: which
    hint, when, and a hash and length of the draft it was revealed on), and
    submit attaches the item's rows to the attempt. Telemetry only: the
    attempt's ``hints_used`` is still the client's count, and ``primed``,
    reveal events, evidence, FSRS, certification, scheduling and grading never
    read these rows, so no scoring, scheduling, projection or serving change
    and no successor. Off (the kill switch): no row is written, the RPC is a
    no-op, and the practice RPCs and screen are exactly as before H0.
    The phases after H0 add their own keys here (§9's list).

    H1 adds ``price_per_million``: the owner's price (USD per million tokens)
    for the hint routes on a METERED profile (OpenRouter, an API key); unset,
    a metered call is refused before it is sent (the spend rule). Codex and
    the ChatGPT plan need none: their cost is ``estimated_only``. And
    ``maps`` (:class:`HintsMapsConfig`).

    H2a adds the hint service (``practice.request_hint``): ``adaptive_enabled``
    (the kill switch), ``chooser_enabled``, ``choice_policy``,
    ``chooser_timeout_seconds``, ``help_style`` and ``max_daily_cost_usd``,
    with the routes ``ai.routing.hint_chooser`` (a decider-only route) and
    ``ai.routing.hint_writer`` (a chat route that never resolves to Codex,
    D9). A shown hint reaches the attempt only through ``hints_used`` (levels
    1-3) and ``primed`` (levels 4-5) and a ``tutor_answer`` reveal on key
    overlap, with their existing meaning (§5), so no scoring, scheduling,
    projection or serving change and no successor.

    H2b adds the practice screen's hint panel and outcome placement:
    ``authored_offer_after_seconds`` (a display cap: how long a hint is
    written before the panel offers the item's own hint instead) and
    ``outcome_placement_enabled`` (one background call on route
    ``ai.routing.hint_outcome`` after a hinted answer graded not fully
    correct, placing the final answer on the item's approach map: measurement
    only, never the grade, the diagnosis or evidence; it joins the maps'
    envelope ``maps.max_daily_cost_usd``). Neither is read by scoring,
    scheduling, projection or serving, so no successor.
    """

    telemetry_enabled: bool = True
    price_per_million: float | None = Field(default=None, gt=0)
    maps: HintsMapsConfig = Field(default_factory=HintsMapsConfig)
    #: H2a: hints written for the learner's work (``practice.request_hint``).
    #: Off (the kill switch), the RPC answers ``disabled`` and the practice
    #: RPCs are byte-identical to the base. Needs ``telemetry_enabled`` (the
    #: rows are how a shown hint is counted at submit).
    adaptive_enabled: bool = True
    #: H2a: the Decider chooses the kind, level and horizon (route
    #: ``ai.routing.hint_chooser``); off, the fallback order serves.
    chooser_enabled: bool = True
    #: H2a: ``sample`` draws from the Decider's probabilities and logs the
    #: drawn option's propensity (D4); ``argmax`` serves the top option and
    #: logs 1 (no off-policy evaluation is then possible).
    choice_policy: Literal["sample", "argmax"] = "sample"
    #: H2a: the chooser's time box; past it the fallback serves (a latency
    #: bound, not a judgment).
    chooser_timeout_seconds: float = Field(default=3.0, gt=0)
    #: H2a: the one stored help-style preference every surface reads (D5);
    #: a stated preference the Decider weighs, never a block.
    help_style: Literal["let_me_struggle", "balanced", "guide_me"] = "balanced"
    #: H2a: the metered dollars a UTC day for the hint writer and chooser,
    #: shared by every process (spec §7.3). A capped day falls back to the
    #: item's authored hints and says so. Codex and the ChatGPT plan are
    #: ``estimated_only`` and never counted against it.
    max_daily_cost_usd: float = Field(default=1.00, ge=0.0)
    #: H2b: seconds a hint is being written before the panel offers the
    #: item's own hint instead (*use the item's hint instead*: the request is
    #: cancelled first, so only one hint is recorded). A display cap.
    authored_offer_after_seconds: float = Field(default=4.0, gt=0)
    #: H2b (spec §6.1, D11): after a hinted answer graded not fully correct on
    #: an item with an approach map, one background call (route
    #: ``ai.routing.hint_outcome``) places the final answer on the map, so the
    #: report can say whether the learner got past the hint's target.
    #: Measurement only; off, no call is made.
    outcome_placement_enabled: bool = True


class ReaderInquiryConfig(BaseModel):
    """Reader workbench RW1a: inquiry (spec_reader_workbench_v1 §4.1).

    Branching Ask (a follow-up names its parent exchange and sees only its
    ancestors), inquiry status on the root question with reopen, the return
    stack and detour strip, the reconnect line with its passage-scoped quick
    check, and the reader activity the funnel report reads. Content and
    display only: no scoring, scheduling, projection or serving change, so no
    algorithm successor. ``enabled`` is the kill switch: off restores today's
    flat rail, and every RPC RW1a touches answers exactly as before.

    The reconnect line's passage check is a paid call admitted through the
    Phase 1 spend framework (W10) before it is sent: at most
    ``max_checks_per_day`` checks a UTC day (counted from their receipts,
    failed calls included); on a metered route (OpenRouter, an API key) one
    admitted request per physical request at ``metered_price_per_million``
    (unset: a metered route is refused before sending), held to
    ``max_usd_per_check``. Codex on the ChatGPT subscription needs no price:
    its cost is estimated_only and it has no token, dollar or physical-request
    bound (Slice A §5 rule 6).
    """

    enabled: bool = True
    max_checks_per_day: int = Field(default=100, ge=0)
    max_usd_per_check: float = Field(default=0.50, ge=0.0, le=5.0)
    metered_price_per_million: float | None = Field(default=None, gt=0)


class CuesConfig(BaseModel):
    """Reader workbench RW3a: margin cues from the Guide (spec_reader_workbench_v1 §6).

    The Guide's own passages whose Learning Object carries a recent
    misunderstanding (the diagnoser's overlay, ``reader_guidance``) are shown
    as quiet margin marks beside the text, with a one-line note from a fixed
    template and a "because" line. Display only: nothing here writes
    evidence, mastery, projections, FSRS or the plan, and nothing changes
    serving, so no algorithm successor; taps are salience-only events and
    ``learner_card`` verdicts (task ``passage_cue``). ``enabled`` is the kill
    switch: off, the guide plan carries no cues and the Reader shows no marks
    and no density control.

    ``density`` is the learner's display limit per section (off, fewer,
    normal, more = 0, 1, 2 or 4 marks; "fewer marks like this" steps it down),
    remembered here so it holds across devices. ``one_per_viewport`` keeps at
    most one mark per screenful at every density (off: the per-section budget
    alone). ``off_sources`` are the books the learner switched cues off for.

    Reader workbench RW3b (discovered cues, §6.2 items 1-6): with
    ``discovery_enabled``, passages the Guide's citations miss are found per
    target (a durable misconception, an open hypothesis, a named learner-text
    gap, a demonstrated facet) through T6 retrieval over the open source and
    one listwise judgment per target (``ai.routing.passage_cue_judge``, ledger
    task ``passage_cue``), in the background when a source opens, at most
    ``max_calls_per_source_open`` judge calls per open,
    ``max_calls_per_source_per_day`` judge calls per source per rolling 24
    hours (UTC) over every open (counted from the durable receipts, the
    subscription's included; Codex verify F16; the name says "day", the
    window is a rolling 24 hours so no timezone or DST rule moves it) and ``max_daily_cost_usd`` metered a UTC day
    (Codex is ``estimated_only``).
    ``try_first_enabled``: the judge's "try this step first" offers on worked
    examples and derivations (pressing one opens RW1b's next-step question).
    ``value_order_enabled``: cues are ordered by the probability their target
    is still open, then the judge's rank, Guide first on ties (off: the
    Guide's order, discovered cues after). ``holdout_rate``: the share of
    eligible discovered cues withheld at random, seed and propensity logged
    (0 turns the holdout off; Guide cues are never held out). Display only:
    nothing here reaches evidence, mastery, grading or serving, so no
    algorithm successor.
    """

    enabled: bool = True
    density: Literal["off", "fewer", "normal", "more"] = "normal"
    one_per_viewport: bool = True
    off_sources: list[str] = Field(default_factory=list)
    discovery_enabled: bool = True
    try_first_enabled: bool = True
    value_order_enabled: bool = True
    holdout_rate: float = Field(default=0.1, ge=0.0, lt=1.0)
    max_calls_per_source_open: int = Field(default=12, ge=0)
    max_calls_per_source_per_day: int = Field(default=36, ge=0)
    max_daily_cost_usd: float = Field(default=0.5, ge=0.0)


class WorkbenchConfig(BaseModel):
    """Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1 §5.1, §5.9).

    A problem worked in steps beside the source in the Reader (or full width
    on the practice screen), saved as it is typed, resumable, abandonable and
    reopened, and submitted through the ordinary attempt path. A visible book
    is one hint-equivalent, the rule ``submit_reading_question`` already
    records, so the attempt maps onto existing fields (``hints_used``) and no
    algorithm successor is needed; nothing else here is evidence. ``enabled``
    is the kill switch: off, no workbench entry anywhere, every workbench RPC
    refuses, and the practice screen is byte-identical. ``open_session_days``
    is a display limit: an open session untouched for longer is shown as
    "unfinished" in the recap, without alarm, and never closed automatically.
    """

    enabled: bool = True
    open_session_days: int = Field(default=30, ge=1)
    #: RW2b (spec §5.2-5.5, §5.9): "Check my work", the help ladder and its
    #: hints through the one hint service (adaptive hints H3). Off: RW2a only
    #: (no check, no ladder; every RW2a RPC byte-identical).
    help_enabled: bool = True
    #: Declared symbolic checks run in the PF-b sandbox (§5.3); off, every
    #: verdict is the model's reading and the sandbox is never invoked.
    #: Off by default (RW2b fix round 9, the orchestrator's decision): a
    #: LaTeX-text checker could not be made to agree with what KaTeX displays;
    #: on again once the renderer-equivalent (MathML) checker lands, or by the
    #: owner knowing the limits recorded in the RW2b review.
    symbolic_checks_enabled: bool = False
    #: Off: ``discriminating`` is never among the workbench's options and
    #: rung 1 is an ordinary question (§5.9).
    discriminate_enabled: bool = True
    #: Off: no error-kind guess is shown or traced (§5.9).
    error_kind_enabled: bool = True
    #: "Compare with the book" under a hint in the Reader (§5.2 bridging): a
    #: background passage lookup through T6's practice context.
    bridge_enabled: bool = True
    #: RW2c (spec §5.10): what helps this learner. The help-outcome lines (a
    #: pure read of the ledgers) given to the hint writer and the chooser;
    #: off, both get the request they got before RW2c.
    help_outcomes_enabled: bool = True
    #: The worked example that takes the learner's route (the sources spec's
    #: ``worked_example`` intent): after a level-3+ hint and on "Show me a
    #: similar example". Absent when the sources spec's S3 is not available.
    examples_enabled: bool = True
    #: "Compare with the book's method" after a correct Submit (the reference
    #: read by id, recorded as a reveal on the item before it is shown).
    compare_methods_enabled: bool = True
    #: The logged draw between two or more passages that all passed the judge
    #: (bridge, worked example); off, the first passage is shown as before.
    passage_draw_enabled: bool = True
    #: The workbench's own calls (checks, bridges, examples, comparisons) per problem: a money cap
    #: counted in calls (§5.8). Hint calls are the hint service's (C8).
    max_calls_per_session: int = Field(default=24, ge=1)
    #: The workbench's own metered spend a UTC day (§5.8).
    max_daily_cost_usd: float = Field(default=1.0, ge=0)
    #: The owner's price (USD per million tokens) for a METERED
    #: ``ai.routing.workbench_check`` profile; unset, a metered check is
    #: refused before it is sent. Codex needs none (estimated_only).
    price_per_million: float | None = Field(default=None, gt=0)


class RecapConfig(BaseModel):
    """Reader workbench RW6a: "Last time here" and Wrap up (spec_reader_workbench_v1 §9.1, §9.6).

    On returning to a source the Guide opens with a compact card: where
    reading stopped, the questions still open, the unfinished problems, what
    is worth a second look, and what the learner has since demonstrated on
    their own. Wrap up lists a session's resolved, still-open and
    worth-reinforcing threads, offered in the rail after activity and, after
    leaving, once where the learner lands. Both are pure reads over existing
    ledgers: no model call, nothing stored but three salience-only events
    (``recap_shown``, ``recap_dismissed``, ``wrap_up_opened``), and nothing
    here is read by scoring, scheduling, projection or serving, so no
    algorithm successor. ``enabled`` is the card's kill switch and
    ``wrap_up_enabled`` Wrap up's; off, the Reader and Today render exactly as
    before RW6a and the RPCs refuse.
    """

    enabled: bool = True
    wrap_up_enabled: bool = True


class ReaderIntentConfig(BaseModel):
    """Reader workbench RW1b: the intent box (spec_reader_workbench_v1 §4.2, §4.4).

    Selecting text shows a small, unfocused box under the selection; the
    learner types what they want in their own words and one typed choice to
    the Decider (``ai.routing.reader_intent``) picks the palette action it
    means, which then runs exactly as the palette's own (same RPC, same
    payload). An empty Enter asks, with no model call; an unavailable, timed
    out (``timeout_seconds``) or spent-out Decider routes to Ask. The palette
    stays one key away (Tab), grouped by the five learner intentions, and
    selecting never switches the rail tab. Content and display only: routing
    writes ``judgment_ledger`` rows (task ``reader_intent``) and salience-only
    reader events, and nothing in scoring, scheduling, projection or serving
    reads them, so no algorithm successor. ``enabled`` is the kill switch: off
    (or with ``reader_inquiry.enabled`` off), a selection opens the palette in
    Notes and the rail flips to Notes, exactly as before RW1b.

    ``speculative_enabled``: routing starts once typing pauses for
    ``speculate_after_ms``, so Enter usually finds the routing already made
    (off: route on Enter only). It sends text the learner has typed but not yet
    submitted, which the disclosure says. ``max_calls_per_day`` caps the
    route's Decider calls a UTC day (counted from their receipts, failed calls
    included; about $0.0004 a call at the listed price); speculation stops
    once 80% of it is used, and Enter still routes until the cap.
    """

    enabled: bool = True
    speculative_enabled: bool = True
    speculate_after_ms: int = Field(default=600, ge=100, le=5_000)
    timeout_seconds: float = Field(default=4.0, gt=0.0, le=30.0)
    max_calls_per_day: int = Field(default=200, ge=0)


class ReaderActiveReadingConfig(BaseModel):
    """Reader workbench RW1b: active reading (spec_reader_workbench_v1 §4.2).

    On a selected derivation or worked example: "let me try the next step"
    (the book's following lines fold while the learner tries), "why does
    this step work?", "what does this assume?", "reconstruct this later" (an
    escalated item with a ``test_me_later`` commitment, undoable) and "another
    way to see this" (the sources service's ``find_sources`` with intent
    ``alternative``, the open passage excluded). The questions are the
    quick-check producer's selection-scoped rows, admitted under
    ``[reader_inquiry]``'s caps; answering them and the learner's three-way
    self-check are formative and never an attempt. ``enabled`` is the kill
    switch: off, none of these actions is offered and their RPCs refuse.
    """

    enabled: bool = True


class ReaderFormativeConfig(BaseModel):
    """Reader workbench RW1b: missed answers as learner text (spec_reader_workbench_v1 §4.2, W1).

    A next-step, why-step or assumption answer the learner marks *partly* or
    *no* is queued for learner-text gaps as a ``reader_formative`` text (the
    answer, the selection and the expected answer), so the pipeline can name
    what was missing, as it does for reader questions; a match writes nothing
    new. Tier 2: never an attempt, evidence, mastery, certification or FSRS.
    ``enabled`` is the kill switch: off, no ``reader_formative`` text is
    queued and the answers stay on their rows and in the report.
    """

    enabled: bool = True


class LibraryAskConfig(BaseModel):
    """Reader workbench RW4a: ask your library (spec_reader_workbench_v1 §7.3, §7.7).

    "Ask" (Shift+Enter) in the library search box, Ctrl+Shift+F in the Reader,
    or "where else is this explained?" / "where is this used?" / "what do I
    need first?" on a selection answer sources first, beside the open source:
    up to eight verbatim passages from the sources service's ``find_sources``
    (intent ``explain``, the library scope, the Reader caller's derived
    policy), grouped by source and role, each with a one-line note on what it
    contributes from one listwise call (``ai.routing.library_organizer``,
    ledger task ``library_contribution``) whose lines must each cite exactly
    their own passage. ``expand_graph``: one more ``find_sources`` per
    concept-graph expansion (prerequisites, applications), keeping only
    passages linked to those learning objects, labelled. The tutor answers
    only when asked, only from the passages pinned. Retrieval is context and
    the notes are display (T6's ruling): nothing in scoring, scheduling,
    projection or serving reads them, so no algorithm successor.
    ``personalized_default``: whether the "personalized" chip starts on (the
    note may then name one open question the learner has on a passage's
    learning objects; off, plain retrieval order). ``max_daily_cost_usd``:
    the organizer's metered spend a UTC day (Codex is ``estimated_only``).
    ``enabled`` is the kill switch: off (or with ``source_service.enabled`` or
    ``reader_inquiry.enabled`` off), the library search and the Reader are
    exactly as before RW4a and the RPCs refuse.
    """

    enabled: bool = True
    expand_graph: bool = True
    personalized_default: bool = True
    max_daily_cost_usd: float = Field(default=1.0, ge=0.0)


class ReaderTutorConfig(BaseModel):
    """Reader workbench RW1c: a tutor that looks things up (spec_reader_workbench_v1 §4.6).

    ``retrieval_enabled``: Ask in the Reader retrieves from the learner's
    books on its own (the sources service's ``find_sources`` with verification
    under the Reader caller's derived policy, after the selection and its
    neighbours), answers in three labelled modes (a quote-verified "From your
    books" excerpt, a grounded explanation, a bridge to the learner's work),
    says so when the books don't cover the question, and offers "another
    way" (intent ``alternative``) and "that didn't help" (intent
    ``remediate``). Off: today's selection-and-neighbours tutor, byte for byte.
    ``offers_enabled``: the buttons under an answer (the sources service's
    practice request and tool requests, fetched when the answer lands and
    shown only when pressed, and "Try the next step first" on a cited
    derivation or worked example). Off: no buttons under answers in the
    Reader. Retrieval is context and display, buttons are learner picks (T6's
    ruling): nothing in scoring, scheduling, projection or serving reads
    either, so no algorithm successor. A Reader question asked inside a
    workbench session bound to an item is stored on that item and practice
    session, so the existing question hint-equivalents and reveals carry it
    to the attempt, with their existing meaning. The sources service's
    ``source_service.tutor_tools`` gates the tutor's requests themselves.
    """

    retrieval_enabled: bool = True
    offers_enabled: bool = True


class LibraryExercisesConfig(BaseModel):
    """Reader workbench RW4b: exercises from my sources (spec_reader_workbench_v1 §7.4, §7.7).

    ``enabled``: the Reader's view of the sources service's textbook-exercise
    candidates wherever it lists practice proposals (RW4a's "practice this
    question"): the verbatim statement, source and page, "open in the book",
    "use this one" (the sources service's import, inside the workbench) and
    the key's honest status, with the sources service's exposure rule
    (``instructional/exposure.py``) labelling a candidate the learner has
    already seen, which is then never offered as a check on your own. Off:
    the Reader's practice proposals render exactly as before RW4b and the
    RPCs refuse. ``fallback_enabled``: the learner-initiated "find an
    exercise in my sources" when ``find_practice`` finds nothing
    (``find_sources`` over the question's learning objects, exercise blocks
    of the teaching scope only, imported with the Reader's own
    ``import_exercises``). The spec retires it once the sources service's
    candidates are live, which they are, so it defaults off (§7.4). Both are
    kill switches over display and a learner's own pick: nothing in scoring,
    scheduling, projection or serving reads them, so no algorithm successor.
    """

    enabled: bool = True
    fallback_enabled: bool = False


class FiguresConfig(BaseModel):
    """Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8, §8.6).

    ``enabled``: "make this explorable" on a selected equation, figure block
    or passage builds a declarative figure spec (route ``figure_author``),
    verifies it before it shows (structure, invariants and shaded areas; RW5a
    makes no source claim: every figure is an illustration, the source check
    is RW5c's), and draws it inline under its passage. Off: the Reader is exactly
    as before RW5a, the RPCs refuse and no route is called.
    ``predictions_enabled``: one prediction before the first change, the
    observed before/after readout and "what changed?" (formative; a missed
    one is a ``reader_formative`` learner text). ``region_enabled``: a
    Ctrl+drag region of a figure on the original page, of which only the crop
    is sent. ``revisions_enabled``: "not right?" asks for a new version with
    the learner's note (the earlier one is kept).

    RW5b (§8.7): ``advanced_panels_enabled``: heat maps, vector fields,
    trajectories (fixed-step RK4) and iterated maps in the same declarative
    grammar; off, the author is not told of them and may not emit them, and a
    stored figure that uses one shows as "can't draw this yet".
    ``offers_enabled``: the library organizer (RW4a) and the Reader tutor
    (RW1c) judge, in the call they already make, whether a cited equation or
    figure block could become an explorable figure, and a yes adds "make this
    explorable" to that passage or answer (pressing it builds through the same
    pipeline, origin ``library`` | ``tutor``); off, their prompts, outputs and
    what the Reader shows are as before RW5b.

    Caps (money, W4): two author attempts per request; ``max_daily_cost_usd``
    meters the author route's metered spend a UTC day at
    ``price_per_million`` (unset: a metered route is refused before sending;
    Codex is ``estimated_only``). Content and formative only: nothing in
    scoring, scheduling, projection or serving reads these keys, so no
    algorithm successor (§8.6).
    """

    enabled: bool = True
    predictions_enabled: bool = True
    region_enabled: bool = True
    revisions_enabled: bool = True
    advanced_panels_enabled: bool = True
    offers_enabled: bool = True
    max_daily_cost_usd: float = Field(default=1.0, ge=0)
    price_per_million: float | None = Field(default=None, gt=0)


class ReaderCompareConfig(BaseModel):
    """Reader workbench RW4a: compare pinned passages (spec_reader_workbench_v1 §7.3).

    The Reader's compare UI over the sources service's ``compare_sources``
    (whose own switch is ``source_service.compare`` and whose bounds are
    ``source_service.compare_max_prompt_tokens`` / ``compare_max_cost_usd``):
    a table with one row per source, each cell a quote-verified line, no
    consensus. ``enabled`` is the kill switch: off, no compare action and the
    RPC refuses.

    RW4d (§7.8): ``keep_enabled`` is the kill switch of "Keep this
    comparison" (the kept claims and relations as source-object proposals,
    the learner's own take, ``⇄`` marks, requested perspectives and Keep on
    the tutor's comparison). Proposals and display only: nothing becomes a
    concept edge, facet merge, prerequisite, LO change or evidence. Off, the
    compare display is RW4a's exactly and the keep RPCs refuse.
    """

    enabled: bool = True
    keep_enabled: bool = True


class RolesConfig(BaseModel):
    """Reader workbench RW4e: instructional roles (spec_reader_workbench_v1 §7.9).

    The Reader's own judges (the library organizer, ``ai.routing.library_organizer``,
    and the cue judge, ``ai.routing.passage_cue_judge``) propose each passage
    they judge one or more instructional roles (definition, theorem,
    explanation, intuition, worked example, exercise, figure, counterexample,
    contrast, prerequisite, alternative treatment, application), each with a
    confidence, at no extra call; they are stored as ``source_objects``
    proposals (authorship ``ai``, status ``proposed``, one citation each).
    ``on_demand_enabled`` is the kill switch of those writes: off, both judges'
    requests and outputs are RW4a's and RW3b's exactly and nothing is written.
    ``positive_filter_enabled`` is the kill switch of every use: the sources
    service's ``find_sources(roles=...)`` and intent lists matching the
    proposals as well as ingest's ``role_hint`` (low confidence only when
    nothing better exists), RW3b preferring contrast and counterexample
    passages for distinction cues, and library answers grouped by a
    proposed role labelled "model's label"; off, proposals are ignored and
    ingest's roles alone apply. ``batch_max_cost_usd`` caps one run of the
    owner-run batch labeller (``learnloop reader label-roles``, route
    ``ai.routing.role_labeller``), checked before each batch call (metered
    routes; Codex is ``estimated_only``). Roles add, never exclude: ingest's
    ``role_hint`` and item links stay the authority for exclusions. Labels on
    sources only: nothing in scoring, scheduling, projection or serving reads
    them, so no algorithm successor.
    """

    on_demand_enabled: bool = True
    positive_filter_enabled: bool = True
    batch_max_cost_usd: float = Field(default=5.0, ge=0.0)


class ReadingPathsConfig(BaseModel):
    """Reader workbench RW7a: reading paths in the Guide (spec_reader_workbench_v1 §10.1).

    At the depth the learner picks for a source (get the idea, learn to use
    it, fluency; DL2's intent on the source preselects it, display-level
    only), the Guide's path card labels each section core, prerequisite,
    enrichment, already shown or assumed with a one-line why, read it anyway
    / skip it, one exercise worth trying per core section and a suggested
    next activity composed without a model. The labels come from one call
    per source and depth (``ai.routing.reading_path_judge``), cached by the
    depth, the section list and the linked LOs' statuses; "already shown"
    stands only when every LO the section teaches is demonstrated and
    "assumed" only with an open assumption, enforced in code. ``enabled`` is
    the kill switch (off: today's Guide, no call, every RPC refused).
    ``max_daily_cost_usd`` caps a metered judge route a UTC day (checked
    before the call; Codex is ``estimated_only``). Display only: nothing in
    scoring, scheduling, projection or serving reads a path, so no algorithm
    successor (RW7b, the plan following the path, is a later stage).
    """

    enabled: bool = True
    max_daily_cost_usd: float = Field(default=0.5, ge=0.0)


class LearnerTextGapsConfig(BaseModel):
    """Learner-text gaps (implementation_handoffs §4, owner-directed 2026-10-12).

    One pipeline turns a learner's own text (a tutor question, a non-empty
    stuck answer, a diagnosis) into a named gap and acts on it. Live behind
    kill switches (frictionless defaults); what changes serving is an
    algorithm successor (``mvp-0.16``), with ``sooner_check_enabled`` as its
    switch: the sooner check, and a matched gap's target read as a weak
    prerequisite signal by the field loader (placement's fast-track rule
    reads it). Nothing here writes evidence, mastery or certification (G13).

    ``chooser`` decides whose kind is authoritative: ``context_model`` (the
    tutor, the diagnoser or the stuck-text reader: the model with the whole
    exchange) or ``decider``; the other is a logged second opinion. For
    prerequisite matches it also picks the authoritative judge; belief matches
    are always the LLM judge's (the Decider's verdict is logged, never joins).
    """

    # The pipeline's kill switch: off, no learner text is read or acted on, and
    # the field loader ignores gap targets (the F11 grounded rule applies).
    enabled: bool = True
    chooser: Literal["context_model", "decider"] = "context_model"
    # The Decider's second opinion on the kind and on every judged pair (at
    # mvp-0.22 its deciding verdict). Off, no learner text reaches the Decider
    # at any version: the Tier-1 text-gap switches then act as off.
    decider_enabled: bool = True
    # Vault-wide LO and registry shortlist breadth (stored vectors; R4).
    top_k: int = Field(default=4, ge=1, le=20)
    # Candidate pairs judged per learner text (each by both judges).
    judge_max_pairs: int = Field(default=8, ge=1, le=20)
    judge_timeout_seconds: int = Field(default=180, ge=30, le=1_000)
    # A matched prerequisite that is not declared: ask "needed for this item?"
    # and add the edge on yes (refused on a cycle; one-tap undo).
    add_edges_enabled: bool = True
    # A missing prerequisite is drafted, written and seeded live. Off: nothing
    # new is created and earlier creations are not served.
    create_prerequisites_enabled: bool = True
    max_creations_per_day: int = Field(default=3, ge=0, le=50)
    # The created LO's seed item is one delayed check after this many days.
    seed_check_delay_days: int = Field(default=1, ge=0, le=60)
    # A stated belief is a holding-pen sighting (or a new candidate).
    sightings_enabled: bool = True
    # mvp-0.16's kill switch: a matched prerequisite gap brings an assumed or
    # maintenance LO's next check forward to no sooner than this delay, and
    # its target is a weak prerequisite signal (placement's fast-track rule).
    # Off: mvp-0.15's serving exactly.
    sooner_check_enabled: bool = True
    sooner_check_delay_hours: int = Field(default=24, ge=1, le=24 * 60)
    # Per learner text: paid requests (all routes) and metered dollars.
    max_calls_per_text: int = Field(default=30, ge=1, le=200)
    max_usd_per_text: float = Field(default=0.25, ge=0.0, le=5.0)
    # The live path (sidecar worker) across texts: logical calls per UTC day,
    # counted from the live path's receipts before each text; at the cap the
    # queue waits for the next day (`learnloop gaps run` has its own caps,
    # and its calls are receipted apart and never counted here).
    max_calls_per_day: int = Field(default=500, ge=0)
    # Owner price estimate (USD per million tokens) for METERED chat routes
    # (judge, reader, draft, seed). Unset: a metered route with no published
    # price is refused before sending (spend rule); Codex needs none.
    metered_price_per_million: float | None = Field(default=None, gt=0)


class EvsiConfig(BaseModel):
    """EVSI calibration (docs/reviews/evsi-calibration.md).

    ``forecast_logging`` records the forecast every live value-of-information
    decision runs on in ``voi_forecasts`` (probe selection, the robust probe
    stop, follow-up selection, every ``rank_feasible`` caller): logging only,
    no serving change; false is its kill switch.

    ``measured_loss_enabled`` (Part C) adds the measured minutes an
    unresolved misconception costs later (``scheduling.unresolved_cost``) to
    the EVSI loss table. It changes what EVSI values, so it is off until the
    owner turns it on; today only the causal shadow selector's EVSI reads it.
    ``unresolved_cost_prior_pseudo_count`` is how many of the learner's own
    recurrence classes the Eedi population prior is worth in the shrinkage.
    """

    forecast_logging: bool = True
    measured_loss_enabled: bool = False
    unresolved_cost_prior_pseudo_count: float = Field(default=5.0, gt=0.0)


class ProofCheckConfig(BaseModel):
    """The valid-alternative gate for proofs and explanations, in the grader.

    ``enabled`` is the kill switch of ``mvp-0.20``'s own-route rules (the
    grader grades every criterion on the learner's own route and marks down
    only by quoting the failing step; a mark-down on a divergent route that
    quotes nothing is unassessed, and a grade with nothing assessed and
    nothing validated is held for review). Dormant below ``mvp-0.20``. Off, new
    answers grade as ``mvp-0.19`` now does: mvp-0.17's separate route check
    was removed from serving (owner decision 2026-10-13), which is the state
    its own switch defined, so an ``mvp-0.17``, ``mvp-0.18`` or ``mvp-0.19``
    vault grades as ``mvp-0.16`` did whatever this says. Grades already recorded keep their meaning (the blind
    record and the evidence rows carry the outcome; replay never reads this
    switch).
    """

    enabled: bool = True


class RequiredMethodConfig(BaseModel):
    """Method-explicit items (owner rule 2026-10-13): the grading side.

    ``enabled`` is the kill switch of the method-explicit successor
    (``mvp-0.25``): the own-route rules grade a criterion tied to an item's
    ``required_method`` (frozen with the assessment contract: the one
    authority, never re-derived from the prompt) on use of that method
    (``own-route-v2``), so another route fails it without a quoted wrong
    step. Dormant below the successor and whenever the own-route rules
    themselves are off (``proof_check.enabled``). Off, new answers grade
    exactly as ``mvp-0.24``. Grades already recorded keep their meaning (the
    blind record carries the rules and the method criteria; replay never reads
    this switch). The generation side (criteria phrased by fact) and the
    ``criterion:method_phrased`` doctor check are content paths, not gated
    here.
    """

    enabled: bool = True


class ProjectConfig(BaseModel):
    """Project understanding M1 (spec_project_understanding_v1): delayed probes.

    Enrollment (`learnloop project enroll`) is the opt-in; nothing here sends
    code anywhere until a repo is enrolled. ``auto_sweep`` is the kill switch
    for the automatic capture at app start and at plan build. Capture only
    runs git; generation (the paid step) runs in `learnloop project sweep` and
    before `learnloop project probes` serves a due diff that has none.
    """

    auto_sweep: bool = True
    # Probes stay sealed (never rendered) until captured_at + this many days (D4).
    probe_delay_days: int = Field(default=7, ge=0, le=365)
    probes_per_diff: int = Field(default=2, ge=1, le=6)
    candidates_per_diff: int = Field(default=6, ge=1, le=12)
    # M1b (spec §5.1): diffs under this many changed lines are excluded from
    # gate randomization. M1 probes every diff with probe-able content.
    min_diff_lines: int = Field(default=5, ge=0)
    # Lines of head-side context sent around each hunk (D7).
    context_lines: int = Field(default=40, ge=0, le=400)
    # Upper bound on the estimated tokens of one diff's bundle sent to a model.
    context_token_budget: int = Field(default=12_000, ge=500)
    # Agent-trailer commits from this many days before enrollment are captured too.
    enroll_backfill_days: int = Field(default=7, ge=0, le=365)
    # Plan-build sweeps run at most this often (app start always sweeps).
    plan_sweep_min_interval_minutes: int = Field(default=15, ge=0)
    generate_before_serving: bool = True
    # Spec §5.2: probe grading (the closed-book judgment and answer grades) is
    # one high-effort pass. Applied to the grading route's profile when that
    # profile takes a reasoning effort; "" keeps the route's own effort.
    grading_reasoning_effort: Literal["", "minimal", "low", "medium", "high", "xhigh"] = "high"
    # Model calls promise a scope (diff, questions only, quoted evidence). An
    # agentic transport (Codex) can read any file its process can, so it runs
    # in a bubblewrap sandbox that shows it an empty working directory and no
    # home, vault or repo; a transport that cannot be confined is refused.
    # Kill switch: false runs agentic transports unconfined, and receipts
    # record tool_isolation = "none".
    require_tool_isolation: bool = True


class FamiliesConfig(BaseModel):
    """Offline family authoring only; live scheduling remains per card."""

    max_exhaustive_items: int = Field(default=40, ge=2)
    blocking_top_k: int = Field(default=20, ge=1)


class PFScalingConfig(BaseModel):
    """The scaling check's two configured tiers (Slice 2 §5.6), as route lists.

    A tier's first profile serves the single-route roles (program writer,
    single-shot, isomorph and selection judges); all of its profiles propose on
    the ensemble path, so an ensemble tier needs two distinct models.
    """

    cheap: list[str] = Field(default_factory=list)
    frontier: list[str] = Field(default_factory=list)


class PFConfig(BaseModel):
    """PF-b: generate, verify, select and publish (Slice 2 §5.3-§5.4).

    ``generation_enabled`` is the kill switch for every paid PF command and for
    publication; it is off in the template. Publishing verified items is a
    content change, capped per UTC day, not an algorithm change.
    """

    generation_enabled: bool = False
    max_published_per_day: int = Field(default=10, ge=0)
    default_path: Literal["ensemble", "generator"] = "ensemble"
    candidates_per_family: int = Field(default=6, ge=1, le=60)
    select_per_family: int = Field(default=2, ge=1)
    # P10 defaults: about three solves per panel model, at least two agreeing.
    panel_solves_per_model: int = Field(default=3, ge=1, le=10)
    min_agreeing_solves: int = Field(default=2, ge=2)
    # Generator-program unit tests: draws checked for CAS and invariance.
    generator_test_draws: int = Field(default=8, ge=2, le=100)
    sandbox_cpu_seconds: int = Field(default=20, ge=1)
    sandbox_memory_mb: int = Field(default=2048, ge=256)
    sandbox_wall_seconds: int = Field(default=60, ge=1)
    # Freshness comparison set for large LOs: stem-embedding top-k (blocking only).
    freshness_top_k: int = Field(default=10, ge=1)
    scaling: PFScalingConfig = Field(default_factory=PFScalingConfig)


class LocalEmbeddingConfig(BaseModel):
    """Local contextual retrieval P1a (spec_local_contextual_retrieval_v1 §4).

    The local pplx v2 9B document space. ``enabled = false`` (the default) is
    the kill switch: nothing is queued, launched or read, and retrieval is
    exactly today's. It stays off until the owner runs ``learnloop embeddings
    local setup`` (the separate environment and the pinned model files under
    ``~/.local/share/learnloop``). ``index_on_extract`` queues a
    ``local_source_index`` job after each extraction (only while enabled);
    ``index_batch_minutes`` (keep: an operational default the owner can tune,
    §9.6) lets a burst of re-extractions load the 9B once.
    """

    enabled: bool = False
    index_on_extract: bool = True
    index_batch_minutes: float = Field(default=15.0, ge=0)


class FallbackEmbeddingConfig(BaseModel):
    """Local contextual retrieval P1b (spec §8): the hosted Voyage fallback space.

    ``enabled = false`` (the default) is the kill switch: nothing is queued or
    sent. With it on (and ``embedding.enabled``), ``provider`` names the
    ``voyage_contextual_embedding`` profile, each extraction queues a capped
    backfill when ``maintain_index`` is on, and the resolver queries the space
    only for extractions no higher-weighted space covers. One backfill run is
    capped at ``max_cost_usd_per_run`` (keep: spending authority is the
    owner's, §9.6), admitted at ``price_per_million`` (Voyage's published
    $0.12/M; the free tier is never assumed).
    """

    enabled: bool = False
    provider: str = "voyage_context"
    maintain_index: bool = True
    max_cost_usd_per_run: float = Field(default=1.0, ge=0)
    price_per_million: float = Field(default=0.12, ge=0)


class SourceSpaceConfig(BaseModel):
    """The source-space resolver and its fusion (spec §5, §9.2).

    ``default`` is the seed: the fusion's prior mean puts full weight on it
    (Qwen until P3's owner-confirmed seed decision). ``learned_fusion = false``
    (the default; orchestrator scoping 2026-10-24) serves the seed weights and
    only LOGS what the learned rule would do; ``exploration = false`` (its own
    switch) never reorders anything, and when on it may reorder only spans the
    posterior cannot order (a gap smaller than its own posterior spread).
    ``log_feedback`` records deliveries and signals while a new space is on.
    """

    default: Literal["qwen", "local:grouped", "local:singleton", "voyage"] = "qwen"
    learned_fusion: bool = False
    exploration: bool = False
    log_feedback: bool = True


class EmbeddingConfig(BaseModel):
    enabled: bool = False
    backfill_enabled: bool = False
    model: str = Field(default="qwen/qwen3-embedding-8b", min_length=1)
    dimensions: int = Field(default=4096, gt=0)
    # Slice 2 T7 kill switch (display only). The knowledge map ranks an item's
    # neighbours by its stored stem vector when one is current; false keeps
    # the facet/concept-graph neighbours. Reads stored vectors only, so it
    # makes no calls and is independent of `enabled`.
    map_neighbors_enabled: bool = True
    # Tutor delivery fixes (owner, 2026-10-13): a completed extraction (an
    # import, a re-extraction, a page repair) queues the source_block/text
    # backfill of its source's current extraction, so dense retrieval keeps
    # covering it. Acts only when `enabled` and `backfill_enabled` are both on
    # (with either off nothing is queued or sent); false is the kill switch
    # (the explicit `learnloop embeddings backfill --record-kind source_block`
    # remains). One run is capped at source_backfill_max_cost_usd (a whole
    # 4,000-block book cost about $0.01 at the default model's price).
    backfill_sources_on_extract: bool = True
    source_backfill_max_cost_usd: float = Field(default=1.0, ge=0)
    # Local contextual retrieval P1a/P1b (spec_local_contextual_retrieval_v1):
    # the local 9B space, the Voyage fallback and the space resolver. All off
    # or at the seed by default: retrieval is exactly today's.
    local: LocalEmbeddingConfig = Field(default_factory=LocalEmbeddingConfig)
    fallback: FallbackEmbeddingConfig = Field(default_factory=FallbackEmbeddingConfig)
    source_space: SourceSpaceConfig = Field(default_factory=SourceSpaceConfig)

    @computed_field
    @property
    def privacy_disclosure(self) -> str:
        return (
            "When enabled, remote embeddings send canonical or learner-derived text "
            "to the configured endpoint (by default OpenRouter and its upstream provider). "
            "Requests ask for OpenRouter data_collection=deny; custom endpoints may ignore "
            "that option, so verify their retention policy. Vectors approximate "
            "plaintext: protect them like practice attempts in backups, exports and sync; "
            "never share them across vaults."
        )


class GraphNominationConfig(BaseModel):
    """Slice 2 T5: embedding nominations for ingest and graph review.

    Nominations only, never identity: the append-reconciliation or
    graph-structuring model, or the owner, decides every merge. Acts only when
    ``embedding.enabled`` is also true; ``enabled = false`` is the kill switch
    that restores the lexical-only behaviour exactly. Registry vectors come
    from the backfill; an incomplete index degrades to lexical. New
    LLM-written candidate text is embedded at ingest within these caps (per
    synthesis or append run); exceeding them degrades to lexical too.
    """

    enabled: bool = True
    # Nearest registry neighbours nominated per new claim, concept or facet.
    # A rank limit, not a cosine cutoff (R4: cutoffs come from a report).
    top_k: int = Field(default=5, ge=1, le=50)
    embed_new_text: bool = True
    max_query_texts: int = Field(default=256, ge=0)
    max_query_calls: int = Field(default=8, ge=0)
    max_query_tokens: int = Field(default=200_000, ge=0)
    max_query_cost_usd: float = Field(default=0.05, ge=0)


class FacetIdentityConfig(BaseModel):
    """Facet identity at mint time, and the dedupe command (handoff §4).

    At ingest, a cheap judge sees each concept neighbourhood of candidate
    facets whole and partitions it into same-skill sets (``merge``,
    ``absorb``, ``keep_distinct``); candidates nominated against registered
    facets go to the same judge. ``learnloop facets dedupe`` does the same for
    an existing vault. Merges and absorbs apply live, each with an undo.
    Embeddings only bound and shortlist neighbourhoods; the judge decides.
    ``enabled = false`` is the kill switch: today's lexical gate only, the
    pre-change synthesis prompts, no judge and no shortlist embedding.
    ``reword_confirm = false`` is the kill switch of the owner's one-tap
    reword confirm (2026-10-13; ``content.facet_identity.authority``).
    """

    enabled: bool = True
    # Facets one judge call partitions; a larger neighbourhood is split.
    max_group_size: int = Field(default=40, ge=2, le=120)
    # Embedding shortlist rank within a run (the study: every duplicate was
    # within rank 4) and registry nominations per candidate (T5, top-4).
    shortlist_top_k: int = Field(default=4, ge=1, le=20)
    attach_top_k: int = Field(default=4, ge=1, le=20)
    # Retired compatibility key: nothing reads it. Facet identity locks were
    # removed (owner, 2026-10-12), so every merge and absorb applies live with
    # its undo; ``learnloop doctor`` warns when a vault sets it. (A merge still
    # never adds a precondition to a registered facet, and a retiree that a
    # graded criterion names with its survivor is still held back.) Kept so
    # the recorded effective-defaults snapshots do not move.
    merge_locked_facets: bool = True
    # A model-proposed change to a registered facet's meaning with no textbook,
    # lecture, paper, reference or alternate-explanation span behind it (not
    # exam-only) waits for the owner's one-tap confirm, and a title or
    # worked-example change needs no explanatory citation (owner, 2026-10-13).
    # false is the kill switch: the predecessor rule, under which such a change
    # is refused (the producers drop it) and titles and worked examples need
    # explanatory support like the rest of the meaning. Exam-only support is
    # refused either way; rewords already held can still be confirmed or kept.
    reword_confirm: bool = True
    # Per ingest run (and the dedupe command's defaults). Codex runs on the
    # subscription: tokens and dollars are estimated only, never enforced.
    max_calls: int = Field(default=24, ge=0)
    max_facets: int = Field(default=400, ge=0)
    max_pairs: int = Field(default=20_000, ge=0)
    max_retries: int = Field(default=2, ge=0)
    max_total_tokens: int = Field(default=600_000, ge=0)
    max_cost_usd: float = Field(default=0.5, ge=0)
    # Owner price override (USD per million tokens, input and output) for a
    # metered judge model without a built-in price; unknown prices refuse.
    price_per_million_input: float | None = Field(default=None, gt=0)
    price_per_million_output: float | None = Field(default=None, ge=0)


class FieldConfig(BaseModel):
    """Offline F1 analysis only; activation requires a later algorithm successor."""

    enabled: bool = False
    active_predictor: Literal["mastery_ekf"] = "mastery_ekf"
    legacy_fallback: Literal["exclude", "current_content"] = "exclude"
    question_classification_enabled: bool = False
    llm_probability_enabled: bool = False


class PracticeIndexConfig(BaseModel):
    """The practice index: facet dossiers and ``find_practice`` (Slice 2 §5.9).

    ``find_practice`` proposes items and never serves them, so nothing here is an
    algorithm successor. Dossier generation and the retrieval evaluation are
    paid batch work with their own switches, off in the template.
    """

    # Kill switch for find_practice (RPC, CLI and agent tool).
    enabled: bool = True
    # auto: the two-level dossier path only when the latest retrieval evaluation
    # on the current index manifest found that it beats direct item search.
    retrieval_path: Literal["auto", "direct", "dossier"] = "auto"
    # The LLM rerank of find_practice's candidate pool (route practice_rerank).
    rerank_enabled: bool = True
    # Metered rerank routes need a price estimate (USD per million tokens) or the
    # rerank is skipped; subscription (Codex) routes have no marginal cost.
    rerank_price_per_million: float | None = Field(default=None, gt=0)
    # A reservation cap: the rerank reserves its full output budget
    # (ai.output_tokens) and a truncation retry twice that.
    rerank_max_cost_usd: float = Field(default=0.30, ge=0)
    # USD per million input tokens for find_practice's query embedding when
    # embedding.model has no published estimate; unknown prices skip it.
    query_embedding_price_per_million: float | None = Field(default=None, gt=0)
    # The two-level path keeps at least this many facets, then more in rank
    # order until their admissible items fill candidate_pool.
    facet_top_k: int = Field(default=5, ge=1, le=50)
    candidate_pool: int = Field(default=20, ge=1, le=60)
    proposals: int = Field(default=5, ge=1, le=20)
    # Reciprocal-rank-fusion constant (Cormack et al. 2009); ranks, not scores.
    rrf_k: int = Field(default=60, ge=1)
    # Facets with fewer admissible items than this are generation targets.
    coverage_min_eligible: int = Field(default=3, ge=0)
    # A proposed item attempted within this window counts as "practised".
    usage_window_hours: int = Field(default=72, ge=1)
    # Paid batch work: off until the owner enables it.
    dossiers_enabled: bool = False
    evaluation_enabled: bool = False


class SourceRetrievalConfig(BaseModel):
    """Slice 2 T6: source retrieval (spec_embedding_consumers_v1 §9).

    Four consumers: the library search, the tutor's source spans, the Quick Add
    scope and a nearest-LO suggestion for spans without provenance. Keyword
    search (FTS5 BM25 over ``source_block_fts``) and dense search over the
    stored ``source_block/text`` vectors are fused by reciprocal rank. Retrieval
    is context: nothing here scores, schedules, projects or serves, so it is
    not an algorithm successor. ``enabled = false`` is the kill switch that
    restores every consumer's previous behaviour exactly.
    """

    enabled: bool = True
    # Dense retrieval over stored source_block/text vectors, used only when every
    # block in the searched scope has a current vector for embedding.model (the
    # query embedding also needs embedding.enabled). Otherwise keyword only.
    dense: bool = True
    # LLM rewrite of conceptual questions before retrieval (route
    # source_query_rewrite) for deep library searches (Enter).
    query_rewrite: bool = True
    # The same rewrite for tutor questions. Off by default: the tutor already
    # waits for verification, which decides the spans, and an unset route runs
    # on Codex, so a rewrite would add a slow call to every conceptual question.
    tutor_query_rewrite: bool = False
    # Tutor spans: an LLM listwise rerank verifies every retrieved candidate
    # (route source_rerank) and only verified spans reach the tutor. Off or
    # unavailable, the tutor keeps the learning object's linked spans.
    tutor_rerank: bool = True
    # Seconds. A deep library search's time box: its rewrite and query
    # embedding carry the time left as their timeout, and it keeps what it has
    # when the time runs out. For a tutor question it is a soft deadline only
    # (owner, 2026-10-12): every step is timed on the question's receipt and a
    # step over it is flagged, never cancelled, unless tutor_deadline_cancels.
    retrieval_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    # true restores the tutor's time box (cancel at retrieval_timeout_seconds
    # and keep the linked spans).
    tutor_deadline_cancels: bool = False
    # How retrieval's ranked lists become one candidate pool (owner,
    # 2026-10-12): "dense_plus_bm25" is the dense top-k plus the BM25 top
    # pool_keyword_extras that dense did not return, ranked dense first for
    # display (verification picks from all of it on the tutor's path);
    # "hybrid_rrf" fuses every list by reciprocal rank (T6 as merged). Without
    # a complete dense index for the scope, dense_plus_bm25 falls back to
    # hybrid_rrf. Default from the T6 follow-up evaluation (Haiku 5.5 labels,
    # two library copies): it beat hybrid_rrf on the verified tutor path and
    # on the library's display ranking (docs/reviews/t6-followup.md).
    pool: Literal["dense_plus_bm25", "hybrid_rrf"] = "dense_plus_bm25"
    pool_keyword_extras: int = Field(default=4, ge=0, le=20)
    # A labelled nearest-LO suggestion for reader spans without provenance.
    suggest_learning_objects: bool = True
    # Metered rewrite / rerank routes need a USD-per-million-token estimate, or
    # the step is skipped; Codex (subscription) routes have no marginal cost.
    llm_price_per_million: float | None = Field(default=None, gt=0)
    # Per-question dollar caps (reservations: each call reserves its full
    # output budget, ai.output_tokens, and a truncation retry twice that).
    rewrite_max_cost_usd: float = Field(default=0.15, ge=0)
    rerank_max_cost_usd: float = Field(default=0.30, ge=0)
    # USD per million input tokens for query embeddings when embedding.model has
    # no published estimate; unknown prices skip dense retrieval.
    query_embedding_price_per_million: float | None = Field(default=None, gt=0)
    # Reciprocal-rank-fusion constant (Cormack et al. 2009); ranks, not scores.
    rrf_k: int = Field(default=60, ge=1)
    # Candidates the tutor's verification rerank judges, and spans it keeps
    # (at most 4: the ING M8 §9.2 bound on source spans offered to one turn).
    tutor_candidate_pool: int = Field(default=12, ge=1, le=40)
    tutor_spans: int = Field(default=4, ge=1, le=4)
    # Tutor delivery fixes (owner, 2026-10-13): one candidate passage as the
    # relevance judges read it (the tutor's verification, the remediate and
    # find_sources checks, the T6 report's labeller), in tokens (characters /
    # 4). A passage is its complete block, whitespace collapsed, and is
    # trimmed (marked "…" and counted) only past this; it was cut at 900
    # characters before. Generous by default.
    passage_token_budget: int = Field(default=4_000, ge=250, le=100_000)
    # Kill switch for complete judge passages (tutor delivery fixes item 2;
    # Codex review F5): false restores the 900-character passages the judges
    # read before (the tutor's verification, the find_sources checks and the
    # T6 labeller, whose report is then t6-eval-v2 again).
    complete_passages: bool = True


class SourceServiceConfig(BaseModel):
    """Canonical sources as a shared instructional service
    (``spec_source_practice_and_probes_v1.md`` §13).

    One master switch and one kill switch per phase. Tools propose and serving
    paths serve (SC1). Every key here is a kill switch, a time or prompt-size
    bound, or a money cap; none decides learning (SC6). ``enabled = false``
    turns every phase off at once. No key turns off the certification gate for
    unverified imported answer keys (C3, §7.3a): it is versioned by the
    algorithm tag, not switched.
    """

    enabled: bool = True
    # S0: a practice request on every tutor answer (practice, feedback, library
    # and reader contexts).
    tutor_offers: bool = True
    # S1: textbook exercises as practice candidates, their verifier ladder,
    # whether an import whose key does not verify is still written (labelled),
    # and attachment to an existing practice family.
    exercise_arm: bool = True
    exercise_verification: bool = True
    unverified_imports: bool = True
    family_attachment: bool = True
    # S2a: the value intents (discriminate, retention, remediate); off, only
    # ``practice`` is accepted. S2b: source-first fulfilment of intervention
    # needs (a successor; vaults below its tag never run it).
    discriminating_search: bool = True
    source_first_needs: bool = True
    # S3: the tutor's intent-aware grounding, ranked remediation passages and
    # compare_sources.
    tutor_intents: bool = True
    remediation_passages: bool = True
    compare: bool = True
    # S4: the tutor's typed tool requests. S5: the intervention records.
    tutor_tools: bool = True
    interventions: bool = True
    # Time bound (seconds) on the interactive import's verifier ladder; past it
    # the item is written labelled "being checked" and the check finishes later.
    verify_timeout_seconds: float = Field(default=90.0, gt=0, le=900)
    # Prompt-size bound on one comparison (sources that do not fit are listed,
    # uncompared, never dropped).
    compare_max_prompt_tokens: int = Field(default=24_000, ge=1_000, le=400_000)
    # Money caps (USD, metered routes; Codex and the ChatGPT plan are
    # estimated_only, never counted). Owner (2026-10-13): the per-operation
    # caps are off by default (None: no cap; set one to bound an import or a
    # comparison) and the daily guard is 5.00, with headroom: spend is observed
    # in real use (`learnloop sources report`) and caps set later from it; the
    # provider key's own limit is the hard backstop.
    import_max_cost_usd: float | None = Field(default=None, ge=0)
    compare_max_cost_usd: float | None = Field(default=None, ge=0)
    max_daily_cost_usd: float = Field(default=5.00, ge=0)
    # USD per million tokens for the service's own metered judge routes
    # (source_solution_match, source_compare, exercise_discrimination,
    # worked_example_equivalence). Unset: those steps are skipped and labelled
    # on a metered route, never guessed.
    llm_price_per_million: float | None = Field(default=None, gt=0)


class PlacementConfig(BaseModel):
    """Learner field F2: starting new material without ceremony (spec §5.2).

    Acts only on a vault at a placement algorithm version (``mvp-0.11`` or later, ``PLACEMENT_VERSIONS``).
    ``enabled`` is the kill switch: off restores the predecessor's opening
    probes, serving and ordering exactly, and ignores recorded assumptions.
    """

    enabled: bool = True
    # D11: no opening diagnostic episode per new LO. True restores them while
    # keeping assumed-known (a narrower switch than ``enabled``).
    initial_probes: bool = False
    # D6: the assumed LO's first review is the check.
    assumed_first_interval_days: int = Field(default=14, ge=1)
    # D6: at least this many cold, unhinted, unhelped, full-marks first answers.
    fast_track_min_correct: int = Field(default=2, ge=2)
    # D6: P(theta_L > theta_known) >= q, theta_known = logit(known_probability).
    fast_track_q: float = Field(default=0.8, gt=0.5, lt=1.0)
    known_probability: float = Field(default=0.75, gt=0.5, lt=1.0)
    # D4: the optional quick check ("Check what I already know").
    quick_check_k: int = Field(default=4, ge=1, le=4)
    quick_check_budget_minutes: int = Field(default=8, ge=1, le=8)


class PlanConfig(BaseModel):
    """Daily-loop DL1: the finite daily plan (``spec_daily_loop_v1.md`` §6, §10).

    Acts only on a vault at a daily-plan algorithm version (``mvp-0.14`` or a
    later successor, ``DAILY_PLAN_VERSIONS``).
    ``enabled`` is the kill switch: off restores mvp-0.13's Today (the open queue
    with the re-entry cap) exactly. ``new_admission_enabled`` and
    ``reading_blocks`` are narrower sub-switches; ``reading_from_furthest``
    (a live change wherever the plan acts, no successor tag) off restores
    DL1's reading-block selection; ``deterministic_staged_plans`` (a live
    change wherever the router composes Today, no successor tag) off restores
    the staged plan's pool as ``mvp-0.23`` landed (session-seeded draws);
    ``headline`` only hides the optional Today headline (display).
    """

    enabled: bool = True
    # §6.3: load-based new-material admission. Off admits no system-chosen new
    # material at all (learner requests and scheduled checks still serve).
    new_admission_enabled: bool = True
    # §6.10: at most one reading block a day from an as_you_read source.
    reading_blocks: bool = True
    # UX Phase 1 usability round 1 (U4): the reading block continues from the
    # furthest section the learner read into and is never front or back matter
    # while a chapter is left. A live change behind this kill switch at every
    # daily-plan version, not a successor tag (owner ruling at the UX merge,
    # docs/reviews/ux-phase1.md: the selection is a serving choice replay never
    # reads). Off, the reading block is DL1's exactly, the first unfinished
    # section in book order.
    reading_from_furthest: bool = True
    # Plan determinism (owner rule 2026-10-13: staged plans are deterministic;
    # exploration only from the router mixture's logged floor). Where the
    # router composes Today (mvp-0.23 or later with router.enabled), the plan's
    # pool is the scheduler's greedy order, and a contrast pair's member order
    # is the pair's own draw (seeded on the pair, not the session), so the same
    # vault state plans the same blocks in every session. A live change behind
    # this kill switch, not a successor tag (owner's standing ruling: serving
    # changes replay never reads). At mvp-0.24 the same pool gives the model
    # mixture its candidates (the staged pick and the support); the mixture
    # keeps its own seeded draw, floor and logged propensities. Off, the
    # staged plan's pool is as mvp-0.23 and mvp-0.24 landed: the scheduler's
    # seeded exploration and the per-session pair order. DL1's own plan
    # (router off, or below mvp-0.23) is unaffected.
    deterministic_staged_plans: bool = True
    # D1: minutes on a fresh vault; afterwards the remembered budget.
    default_minutes: int = Field(default=25, ge=1, le=600)
    minutes_presets: list[int] = Field(default_factory=lambda: [10, 15, 25, 40, 60])
    # D2: split caps (§6.2). repair + maintain < 1 leaves room for new and push.
    repair_max_share: float = Field(default=0.30, ge=0.0, le=1.0)
    maintain_max_share: float = Field(default=0.60, ge=0.0, le=1.0)
    # D3: one "keep going" extension.
    keep_going_minutes: int = Field(default=10, ge=1, le=120)
    # §6.3 (Q11): projected review load over this horizon, against a ceiling.
    load_horizon_days: int = Field(default=14, ge=1, le=90)
    load_ceiling: float = Field(default=0.80, gt=0.0, le=1.0)
    new_item_reviews_14d: int = Field(default=4, ge=0, le=30)
    max_new_items_per_day: int = Field(default=10, ge=0, le=200)
    min_new_items_per_day: int = Field(default=1, ge=0, le=200)
    # §6.4 (Q12): own latencies are winsorized at this many minutes.
    latency_cap_minutes: float = Field(default=15.0, gt=0.0, le=120.0)
    # §6.4: a reading block's estimate is the section's words left / this.
    read_words_per_minute: int = Field(default=120, ge=10, le=2000)
    # §6.10: pre-questions arrive in DL4; DL1 never serves any.
    pre_questions: int = Field(default=3, ge=0, le=10)
    # D11: a re-entry plan's caps (§7).
    reentry_minutes: int = Field(default=15, ge=1, le=120)
    reentry_max_items: int = Field(default=8, ge=1, le=100)
    # §6.9: due project probes in the maintain lane per day. From mvp-0.21
    # the kill-switch path only (voi_stopping.project_probes off): with it on,
    # every due probe whose value pays for its minutes competes for the
    # plan's minutes.
    project_probes_max_per_day: int = Field(default=4, ge=0, le=50)
    # D7: the optional one-line Today headline.
    headline: bool = True

    @model_validator(mode="after")
    def _shares_leave_room(self) -> "PlanConfig":
        if self.repair_max_share + self.maintain_max_share > 1.0:
            raise ValueError("plan.repair_max_share + plan.maintain_max_share must not exceed 1.0")
        if self.min_new_items_per_day > self.max_new_items_per_day:
            raise ValueError("plan.min_new_items_per_day must not exceed plan.max_new_items_per_day")
        if not self.minutes_presets or any(value <= 0 for value in self.minutes_presets):
            raise ValueError("plan.minutes_presets must be positive minute values")
        return self


#: §5.3 (Q8, accepted 2026-10-12; the owner may override at DL2's checkpoint):
#: the recall target each depth preset is maintained at, and the uncommitted one.
DEFAULT_RECALL_TARGETS: dict[str, float] = {
    "keep_in_touch": 0.80,
    "remember_key_ideas": 0.85,
    "work_fluently": 0.90,
    "master_tasks_like_these": 0.92,
    "uncommitted": 0.90,
}


class IntentConfig(BaseModel):
    """Daily-loop DL2: intent (``spec_daily_loop_v1.md`` §5, §11).

    The successor ``mvp-0.29`` behind its kill switches (the DL2 Codex
    re-review F2: intent changes which items are served as measurements, the
    2026-10-17 rule; ``docs/reviews/daily-loop-dl2-codex-review.md``): intent is
    read only when serving, and ``due_at``, FSRS state, evidence and every
    projection are unchanged. Below the tag these keys are inert.

    ``enabled`` off restores serving exactly as before DL2: commitments are read
    only for requested items (and staged-owned runs). With it on and no
    commitment, serving is today's too (every item uncommitted, target 0.90,
    whose ratio is exactly 1). ``recall_targets_enabled`` off keeps the
    resolution (exclusion, "Check once", push, admission, re-entry) but serves
    every item at its stored ``due_at``.
    """

    enabled: bool = True
    recall_targets_enabled: bool = True
    recall_targets: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_RECALL_TARGETS))

    @model_validator(mode="after")
    def _targets_are_probabilities(self) -> "IntentConfig":
        missing = sorted(set(DEFAULT_RECALL_TARGETS) - set(self.recall_targets))
        if missing:
            raise ValueError(f"intent.recall_targets is missing {', '.join(missing)}")
        unknown = sorted(set(self.recall_targets) - set(DEFAULT_RECALL_TARGETS))
        if unknown:
            raise ValueError(f"intent.recall_targets has unknown keys: {', '.join(unknown)}")
        for key, value in self.recall_targets.items():
            if not 0.5 <= float(value) <= 0.99:
                raise ValueError(f"intent.recall_targets.{key} must be in [0.5, 0.99]")
        return self


class CaptureConfig(BaseModel):
    """Daily-loop capture settings (``spec_daily_loop_v1.md`` §10).

    DL2 adds only ``test_me_later_days``: when a "Check once" (the control's,
    or any ``test_me_later`` commitment without a ``due_hint``) comes due. DL3
    adds the capture box and processor keys to this section.
    """

    test_me_later_days: int = Field(default=7, ge=0, le=365)


class RouterWeights(BaseModel):
    """The model mixture's component weights (D1: one third each). Normalized
    before use; a model that fails or is not set up gives its weight to
    ``staged`` for that decision."""

    model_config = ConfigDict(extra="forbid")

    staged: float = Field(default=1.0 / 3.0, ge=0.0)
    decider: float = Field(default=1.0 / 3.0, ge=0.0)
    llm: float = Field(default=1.0 / 3.0, ge=0.0)

    @model_validator(mode="after")
    def validate_total(self) -> "RouterWeights":
        if self.staged + self.decider + self.llm <= 0:
            raise ValueError("router.weights must not all be zero")
        return self


class RouterConfig(BaseModel):
    """Action router (spec_action_router_v1). R1: decision logging on today's paths.

    ``log_decisions`` writes one ``router_decisions`` row per Today offer, staged
    P2 decision and learner pick. It is not a serving change and acts at every
    algorithm version; off stops the rows and nothing else.
    ``probe_tie_admission`` is the kill switch of the ``mvp-0.15`` successor
    (``PROBE_TIE_VERSIONS``): probe near-ties, teach-back items included (owner
    decision D11), join the Today queue's seeded exploration. Off (or below
    ``mvp-0.15``) serves exactly as ``mvp-0.14``.

    Router R2a (``mvp-0.23``, ``ROUTER_STAGED_FRAME_VERSIONS``; plan_router_r2_v1
    §9): ``enabled`` is the router's kill switch. On, Today's plan is composed
    by the staged frame (DL1's lanes and ``lane_quota_v1`` over the set the P4
    constraint engine admits) and ``golden_path.advance`` goes through the P2
    bridge; off (or below ``mvp-0.23``) both serve exactly as ``mvp-0.22``.
    ``card_token_budget`` bounds the learner-state card each boundary stores
    (D8). ``payload_retention_days`` prunes the stored payloads (the card, and
    from R2b the models' requests and raw answers, ``router_decision_payloads``);
    the hashes stay on the decision row.

    Router R2b + R2c (the successor after ``mvp-0.23``,
    ``ROUTER_MIXTURE_VERSIONS``; plan_router_r2_v1 §3.3-§3.7, owner decisions
    2026-10-13). ``mode`` names who chooses each block: ``mixture`` (the
    default: a logged draw from the staged rule, the Decider and the router
    LLM, weighted by ``weights``, over the top ``k`` reversible candidates
    with a floor of ``epsilon_min`` each; exact propensities) or ``staged``
    (the rule alone, deterministic, no model asked: R2a exactly). Below the
    successor the mixture is dormant and ``mixture`` serves as ``staged``.
    ``ties_only`` applies the mixture only among the rule's pick and the
    candidates of its lane. ``prefetch_timeout_seconds`` is how long the
    models have, from the moment a decision is prefetched (Today's open, the
    feedback after a block's last answer); ``timeout_seconds`` is how long a
    blocking step (Begin, Continue) waits for them before the rule's share
    takes theirs (G7). ``max_daily_cost_usd`` guards metered model spend per
    UTC day (subscription routes uncapped; the provider key's own limit is the
    backstop). ``sensors`` adds the logged-only ``teach_first`` and
    ``will_pass_next`` questions (``router_qs_v2``), ``sensor_source`` the
    model whose ``intervene_now`` is the restraint's sensor of record.
    ``restraint`` makes a mid-block follow-up a logged decision
    (``plan_interrupt``: join the current block now, or wait for the next
    one); off, a follow-up always joins the current block (R2b).
    ``similar_decisions`` shows the models up to ``similar_k`` matured similar
    past decisions on a logged random ``similar_include_rate`` of decisions
    (needs ``embedding.enabled``; a logged no-op otherwise).
    ``teach_back_summary`` summarizes each graded teach-back dialogue (after
    grading, off the hot path) into the card's typed evidence.
    """

    log_decisions: bool = True
    probe_tie_admission: bool = True
    enabled: bool = True
    mode: Literal["staged", "mixture"] = "mixture"
    card_token_budget: int = Field(default=16_000, ge=1_000)
    payload_retention_days: int = Field(default=365, ge=1)
    weights: RouterWeights = Field(default_factory=lambda: RouterWeights())
    k: int = Field(default=6, ge=2, le=64)
    epsilon_min: float = Field(default=0.02, ge=0.0, lt=0.5)
    ties_only: bool = False
    timeout_seconds: float = Field(default=8.0, gt=0.0, le=120.0)
    prefetch_timeout_seconds: float = Field(default=45.0, gt=0.0, le=600.0)
    max_daily_cost_usd: float = Field(default=5.0, ge=0.0)
    sensors: bool = True
    sensor_source: Literal["decider", "llm"] = "decider"
    restraint: bool = True
    similar_decisions: bool = True
    similar_k: int = Field(default=6, ge=1, le=32)
    similar_include_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    teach_back_summary: bool = True

    @model_validator(mode="after")
    def validate_floor(self) -> "RouterConfig":
        if self.k * self.epsilon_min >= 1.0:
            raise ValueError("router.k * router.epsilon_min must stay below 1 (the floor would take every draw)")
        return self


class VoiStoppingConfig(BaseModel):
    """mvp-0.21 Part 1: four count caps lifted onto value of information.

    Acts only on a vault at a value-of-information successor (``mvp-0.21`` or
    later, ``VOI_STOPPING_VERSIONS``). ``enabled`` is the kill switch: off (or
    below ``mvp-0.21``) the four former caps serve exactly as ``mvp-0.16``:
    ``probe.episode.session_qualifying_observation_cap``,
    ``scheduler.followup.max_interventions_per_lo_per_session``,
    ``teach_back.session_cap`` and ``plan.project_probes_max_per_day``. Each
    site has a narrower sub-switch that restores its own cap alone.

    On, the next observation at each site is served while its value of
    information pays for its minutes (``diagnosis.voi_stopping``): robust EVSI
    and ``evsi.rank_feasible``'s stop rule where a next-action decision is at
    stake, otherwise the robust EIG converted to minutes. The decision
    parameters are the existing heuristic ones in
    ``diagnosis.robust_composition`` (lambda_time, burden, the nat-to-minutes
    scale), and the three below.

    The multi-family EVSI study (``docs/reviews/evsi-multisim.md`` §6.1,
    ranks 1 to 3; the owner may flip each) adds one switch per change, each
    at the study's recommendation; the value in brackets restores the
    successor as it was before the study, exactly:

    * ``robust_gate_with_value`` (false; true restores): whether the mvp-0.8
      robust completion gate (``couldnt_reliably_distinguish``) may still end
      an episode while value decides it. Off, a value-decided episode ends on
      its value stop (or a stability stop), and that stop's receipt records
      the gate's verdict as a counterfactual. Where value does not decide (the
      site off, below the successor, a calibration session) the gate serves
      as before.
    * ``lookahead_max_checks`` (3; 1 restores): in a probe episode, when a
      decision is at stake, ``rank_feasible`` did not abstain and no single
      check pays, the best 2 to this many ranked checks that can be
      administered together (one per canonical surface group) are valued
      jointly (robust EVSI of their product table) against their summed
      minutes; a paying batch continues with the site's own choice among it.
      The follow-up and teach-back sites wait for live calibration (the
      study's §6.2). A valuation depth, never a count of observations
      (bounded at 4: the joint table grows as the alphabet to the power k).
    * ``robust_quantile`` (0.25; 0.10 restores): the lower quantile of the
      credible set the value gate reads (``rank_feasible``'s robust EVSI, the
      robust EIG, the lookahead's batch value). The mvp-0.8 paths keep
      ``robust_composition.ROBUST_QUANTILE`` (0.10).
    """

    enabled: bool = True
    probe_episodes: bool = True
    followups: bool = True
    teach_back: bool = True
    project_probes: bool = True
    robust_gate_with_value: bool = False
    lookahead_max_checks: int = Field(default=3, ge=1, le=4)
    robust_quantile: float = Field(default=0.25, gt=0.0, le=0.5)


class DeciderRoutesConfig(BaseModel):
    """Tier 1 (owner decision 2026-10-13): small judgments the Decider decides, the LLM its fallback.

    One kill switch per judgment, each on by default; false restores that
    judgment's predecessor LLM path exactly. The serving judgments act only at
    ``mvp-0.22`` or later (``algorithm_versions.DECIDER_TIER1_VERSIONS``);
    ``facet_span_support``, a content check on model-proposed facet rewords,
    and ``required_method_statement``, the method-explicit items' one-time
    statement judgment, act at every version. The Decider is ``ai.routing.tier1_decider`` (empty:
    the code-default ``openrouter_decider`` profile); learner-text gaps keep
    ``ai.routing.learner_gap_decider``. See ``learnloop.decider_judgments``.
    """

    #: Learner-text gaps: the same-prerequisite / same-belief pairs and "needed?".
    learner_gap_judge: bool = True
    #: Learner-text gaps: the kind of a learner's text (the gap chooser).
    learner_gap_kind: bool = True
    #: Matching a diagnosed belief to the misconception registry (a joint grade's).
    misconception_match: bool = True
    #: The offline review's pattern-link judgments (`learnloop diagnose review`).
    diagnosis_link_judgment: bool = True
    #: `learnloop field classify-questions`: a learner question's missing metadata.
    field_question_classification: bool = True
    #: The contamination report's exam / tutor-answer leak verdicts.
    contamination_leak_judgment: bool = True
    #: The contamination report's reader-reserve reveal verdicts.
    contamination_reveal_judgment: bool = True
    #: The span-support check before a cited model reword of a facet applies.
    facet_span_support: bool = True
    #: Method-explicit items (a content path, every version): the Decider's
    #: one-time judgment of a statement a required method is read from (does
    #: a textbook exercise's statement require its proposed method, at import;
    #: does a PF variant's stem contradict its parent's, at selection). Off:
    #: the LLM judge on ``ai.routing.rubric_phrasing_judge`` decides it.
    required_method_statement: bool = True
    #: Adaptive difficulty AD1's feature audit (spec_adaptive_difficulty_v1
    #: §7.2, §10.3; a content path, every version): one Decider choice per
    #: audited task-feature dimension of an item revision. Off: the audit's
    #: LLM judge on ``ai.routing.ad_feature_audit`` decides every dimension.
    #: ``adaptive_difficulty.feature_audit`` off runs no audit at all.
    ad_feature_audit: bool = True


class UiConfig(BaseModel):
    """How the desktop app presents learner surfaces (``docs/specs/ux_learnloop_v1.md`` §10).

    Display only: nothing here is read by grading, scheduling, evidence,
    projections or replay, so a value never needs an algorithm successor.

    ``practice_feedback`` is the kill switch of UX Phase 4 (practice and
    feedback, §7.4/§7.5): ``"simple"`` leads every practice card, feedback,
    short-check result and session finish with one plain line and one next
    step, the rest behind *details*; ``"classic"`` restores the screens as they
    were before Phase 4 exactly (owner ruling: live changes behind kill
    switches, no shadow stage).

    ``shell`` is the kill switch of UX Phase 2 (the shell, §5, Q17):
    ``"simple"`` is the four places (Today, Library, Reader, Progress) with
    *+ Add*, the palette and *⋯*, the demoted screens under the hood, and the
    notice system; ``"classic"`` keeps the ten-tab shell exactly as it was
    (meant to stay selectable for a month after Phase 2 lands).
    """

    practice_feedback: Literal["simple", "classic"] = "simple"
    shell: Literal["simple", "classic"] = "simple"


class EligibilityConfig(BaseModel):
    """One serve/administration eligibility decision (``mvp-0.27``;
    ``learnloop.serve_eligibility``, ``docs/reviews/serve-eligibility-decision.md``).

    ``enabled`` is the successor's kill switch. On (at ``mvp-0.27`` or later),
    every serve path asks the decision submit asks: an item submit would prime
    is never served as a cold check, a probe or a quick-check offer; a cold
    check whose item can no longer be taken cold (its answer shown with no
    lapse, or the item practised since the check was set) is withdrawn with
    its typed disposition and the item served as ordinary practice; and exam
    seeding, an exam's finish and a kept-state sim count only reveals up to
    their own instant when auto-priming. Off (or below the tag), every path
    serves and admits exactly as ``mvp-0.26``. Attempts and dispositions
    already recorded keep their meaning; replay never reads this switch.
    """

    enabled: bool = True


#: Adaptive difficulty AD1's outside forecasters (spec_adaptive_difficulty_v1 §8.2, D4).
AD_OUTSIDE_FORECASTERS = ("llm_v1:item", "llm_v3:llm", "llm_v3:decider")


class AdaptiveDifficultyConfig(BaseModel):
    """Adaptive difficulty (``docs/specs/spec_adaptive_difficulty_v1.md`` §11.4). AD1 adds only
    the measuring and logging keys; the later phases add theirs.

    AD1 is not an algorithm successor: it writes receipts (item forecasts as kind
    ``item_unassisted_success`` in ``forecast_receipts``, ``item_serve_inputs``,
    ``ad_reading_opportunities``), two nullable attempt columns and feature-audit
    judgments, and nothing serving, scoring, scheduling, evidence, FSRS or
    certification reads them (A2, A12). Each switch false restores its part's
    predecessor exactly; all false (and ``enabled`` false) writes no row, sends
    no extra model call and changes no prompt (G-AD1-5).

    * ``enabled``: the master switch; false turns every AD behaviour off,
      logging included (§11.1).
    * ``forecast_receipts``: at every plan serve, in the serve transaction, the
      reading-opportunity sweep, the frozen serve inputs of a never-attempted
      item and the in-process forecasts (``mastery_ekf``,
      ``lo_general+composite``); and the first-hint progress marker on the
      attempt. No model call.
    * ``outside_forecasters``: the paid forecasters that run (D4):
      ``llm_v1:item`` once per item revision when it is prepared for the plan's
      pool (background), ``llm_v3:llm`` and ``llm_v3:decider`` per
      presentation (background, after the serve). Off the critical path; an
      empty list (or false) runs none.
    * ``rating_tap``: the practice screen's optional "Felt: easy / about right
      / hard" beside Submit, stored on the attempt only when tapped (§12).
    * ``feature_audit``: one Decider judgment per audited task-feature
      dimension of each item revision prepared for the pool (§7.2), with
      ``[decider_routes] ad_feature_audit`` choosing the Decider (off: its
      LLM fallback on ``ai.routing.ad_feature_audit`` judges).
    * ``daily_spend_cap_usd``: the metered dollars a UTC day for the outside
      forecasters and the feature audit, shared by every process; Codex and
      the ChatGPT plan are ``estimated_only`` and never counted.
    * ``price_per_million``: the owner's price (USD per million tokens) for a
      METERED LLM route of these roles; unset, a metered LLM call is refused
      before it is sent. The Decider is priced at its profile's listed price.
    """

    enabled: bool = True
    forecast_receipts: bool = True
    outside_forecasters: list[Literal["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]] = Field(
        default_factory=lambda: list(AD_OUTSIDE_FORECASTERS)
    )
    rating_tap: bool = True
    feature_audit: bool = True
    daily_spend_cap_usd: float = Field(default=0.50, ge=0.0)
    price_per_million: float | None = Field(default=None, gt=0)

    @field_validator("outside_forecasters", mode="before")
    @classmethod
    def _forecasters_switch(cls, value: Any) -> Any:
        # A boolean reads as the switch it is: true runs all three, false none.
        if value is True:
            return list(AD_OUTSIDE_FORECASTERS)
        if value is False or value is None:
            return []
        return value

    @field_validator("outside_forecasters")
    @classmethod
    def _canonical_forecasters(cls, value: list[str]) -> list[str]:
        chosen = set(value)
        return [name for name in AD_OUTSIDE_FORECASTERS if name in chosen]


class LearnLoopConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal[1, 2] = 2
    storage: StorageConfig = Field(default_factory=StorageConfig)
    algorithms: AlgorithmsConfig = Field(default_factory=AlgorithmsConfig)
    evidence: EvidenceConfig = Field(default_factory=EvidenceConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    goals: GoalsConfig = Field(default_factory=GoalsConfig)
    hypothesis: HypothesisConfig = Field(default_factory=HypothesisConfig)
    mastery: MasteryConfig = Field(default_factory=MasteryConfig)
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    recall_coverage: RecallCoverageConfig = Field(default_factory=RecallCoverageConfig)
    facet_diagnostic: FacetDiagnosticConfig = Field(default_factory=FacetDiagnosticConfig)
    misconceptions: MisconceptionsConfig = Field(default_factory=MisconceptionsConfig)
    practice_generation: PracticeGenerationConfig = Field(default_factory=PracticeGenerationConfig)
    exam_seeding: ExamSeedingConfig = Field(default_factory=ExamSeedingConfig)
    tutor_qa: TutorQAConfig = Field(default_factory=TutorQAConfig)
    tutor_promotion: TutorPromotionConfig = Field(default_factory=TutorPromotionConfig)
    teach_back: TeachBackConfig = Field(default_factory=TeachBackConfig)
    rung_variants: RungVariantsConfig = Field(default_factory=RungVariantsConfig)
    animation: AnimationConfig = Field(default_factory=AnimationConfig)
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    graph_nomination: GraphNominationConfig = Field(default_factory=GraphNominationConfig)
    source_retrieval: SourceRetrievalConfig = Field(default_factory=SourceRetrievalConfig)
    facet_identity: FacetIdentityConfig = Field(default_factory=FacetIdentityConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    field: FieldConfig = Field(default_factory=FieldConfig)
    families: FamiliesConfig = Field(default_factory=FamiliesConfig)
    practice_index: PracticeIndexConfig = Field(default_factory=PracticeIndexConfig)
    source_service: SourceServiceConfig = Field(default_factory=SourceServiceConfig)
    placement: PlacementConfig = Field(default_factory=PlacementConfig)
    router: RouterConfig = Field(default_factory=RouterConfig)
    pf: PFConfig = Field(default_factory=PFConfig)
    plan: PlanConfig = Field(default_factory=PlanConfig)
    intent: IntentConfig = Field(default_factory=IntentConfig)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    locks: LocksConfig = Field(default_factory=LocksConfig)
    error_impacts: dict[str, ErrorImpact] = Field(default_factory=dict)
    fitting: FittingConfig = Field(default_factory=FittingConfig)
    trace_evidence: TraceEvidenceConfig = Field(default_factory=TraceEvidenceConfig)
    diagnostic_augmentation: DiagnosticAugmentationConfig = Field(
        default_factory=DiagnosticAugmentationConfig
    )
    diagnosis: DiagnosisConfig = Field(default_factory=DiagnosisConfig)
    recurrence: RecurrenceConfig = Field(default_factory=RecurrenceConfig)
    stuck_prompt: StuckPromptConfig = Field(default_factory=StuckPromptConfig)
    hints: HintsConfig = Field(default_factory=HintsConfig)
    learner_text_gaps: LearnerTextGapsConfig = Field(default_factory=LearnerTextGapsConfig)
    evsi: EvsiConfig = Field(default_factory=EvsiConfig)
    reader_inquiry: ReaderInquiryConfig = Field(default_factory=ReaderInquiryConfig)
    cues: CuesConfig = Field(default_factory=CuesConfig)
    workbench: WorkbenchConfig = Field(default_factory=WorkbenchConfig)
    recap: RecapConfig = Field(default_factory=RecapConfig)
    reader_intent: ReaderIntentConfig = Field(default_factory=ReaderIntentConfig)
    reader_active_reading: ReaderActiveReadingConfig = Field(default_factory=ReaderActiveReadingConfig)
    reader_formative: ReaderFormativeConfig = Field(default_factory=ReaderFormativeConfig)
    library_ask: LibraryAskConfig = Field(default_factory=LibraryAskConfig)
    library_exercises: LibraryExercisesConfig = Field(default_factory=LibraryExercisesConfig)
    figures: FiguresConfig = Field(default_factory=FiguresConfig)
    reader_compare: ReaderCompareConfig = Field(default_factory=ReaderCompareConfig)
    roles: RolesConfig = Field(default_factory=RolesConfig)
    reading_paths: ReadingPathsConfig = Field(default_factory=ReadingPathsConfig)
    reader_tutor: ReaderTutorConfig = Field(default_factory=ReaderTutorConfig)
    proof_check: ProofCheckConfig = Field(default_factory=ProofCheckConfig)
    voi_stopping: VoiStoppingConfig = Field(default_factory=VoiStoppingConfig)
    adaptive_difficulty: AdaptiveDifficultyConfig = Field(default_factory=AdaptiveDifficultyConfig)
    decider_routes: DeciderRoutesConfig = Field(default_factory=DeciderRoutesConfig)
    required_method: RequiredMethodConfig = Field(default_factory=RequiredMethodConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    eligibility: EligibilityConfig = Field(default_factory=EligibilityConfig)

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_input(cls, data: Any) -> Any:
        """Keep direct model validation compatible; implementation lives in compat."""

        from learnloop.config.compat import normalize_config_input

        return normalize_config_input(data)

    @model_validator(mode="after")
    def _ensure_effective_defaults(self) -> "LearnLoopConfig":
        if "codex" not in self.ai.providers:
            self.ai.providers["codex"] = default_codex_provider()
        codex_runtime_profile = self.ai.providers["codex"]
        self.ai.providers.setdefault(
            CODEX_LOW_PROVIDER,
            codex_runtime_profile.model_copy(
                update={"model": DEFAULT_CODEX_MODEL, "reasoning_effort": "low"}
            ),
        )
        self.ai.providers.setdefault(
            CODEX_MEDIUM_PROVIDER,
            codex_runtime_profile.model_copy(
                update={"model": DEFAULT_CODEX_MODEL, "reasoning_effort": "medium"}
            ),
        )
        self.ai.providers.setdefault(
            CODEX_LUNA_PROVIDER,
            codex_runtime_profile.model_copy(
                update={"model": CODEX_LUNA_MODEL, "reasoning_effort": "low"}
            ),
        )
        # Plan-first transport T1: the ChatGPT-plan profiles every default
        # route names. The tiers copy the vault's `chatgpt` profile (its slug,
        # base URL and switches), so the owner sets one model for all three.
        self.ai.providers.setdefault(CHATGPT_PLAN_PROVIDER, default_chatgpt_plan_provider())
        plan_profile = self.ai.providers[CHATGPT_PLAN_PROVIDER]
        if not isinstance(plan_profile, ChatGPTPlanProviderConfig):
            plan_profile = default_chatgpt_plan_provider()
        self.ai.providers.setdefault(
            CHATGPT_LOW_PROVIDER, plan_profile.model_copy(update={"reasoning_effort": "low"}),
        )
        self.ai.providers.setdefault(
            CHATGPT_MEDIUM_PROVIDER, plan_profile.model_copy(update={"reasoning_effort": "medium"}),
        )
        self.ai.providers.setdefault(
            CHATGPT_LUNA_PROVIDER,
            plan_profile.model_copy(update={"model": CHATGPT_LUNA_MODEL, "reasoning_effort": "low"}),
        )
        self.ai.providers.setdefault("deepseek_flash", deepseek_flash_provider())
        self.ai.providers.setdefault("deepseek_pro", deepseek_pro_provider())
        self.ai.providers.setdefault("openrouter", openrouter_provider())
        # Profiles from code defaults (implementation_goal §5 B6): a vault
        # whose learnloop.toml predates them still resolves routes that name
        # them. An explicit vault profile of the same name stays authoritative.
        self.ai.providers.setdefault(DEFAULT_EMBEDDING_PROVIDER, openrouter_embedding_provider())
        self.ai.providers.setdefault(DEFAULT_DECIDER_PROVIDER, openrouter_decider_provider())
        self.ai.providers.setdefault(OPENROUTER_HAIKU_PROVIDER, openrouter_haiku_provider())
        # An unset tiered route follows the active provider: the plan's tiers
        # when it is the plan, the legacy Codex tiers when a vault still names
        # Codex (refused without ai.agent_harness_opt_in; doctor reports it),
        # else the active provider itself.
        tier_routes = (
            DEFAULT_SERVING_TASK_ROUTES if self.ai.active_provider == CHATGPT_PLAN_PROVIDER
            else LEGACY_CODEX_TASK_ROUTES if self.ai.active_provider == "codex"
            else None
        )
        for task in DEFAULT_SERVING_TASK_ROUTES:
            if task == "canonical_ingest_retry":
                # Resolved after the loop so it can mirror the (possibly
                # non-plan) canonical_ingest route once that is settled.
                continue
            routed = getattr(self.ai.routing, task)
            if not routed:
                setattr(
                    self.ai.routing,
                    task,
                    tier_routes[task] if tier_routes is not None else self.ai.active_provider,
                )
        # canonical_ingest_retry defaults to the primary canonical_ingest route
        # so every provider gets one ingest retry pass.
        retry_route = getattr(self.ai.routing, "canonical_ingest_retry", "")
        if not retry_route:
            self.ai.routing.canonical_ingest_retry = self.ai.routing.canonical_ingest
        self.error_impacts.setdefault(
            "recall_failure",
            ErrorImpact(families={"recall": -0.25}, lo_mastery_delta=-0.05, local_severity_gain=0.8),
        )
        self.error_impacts.setdefault(
            "scaffold_failure",
            ErrorImpact(families={"recall": -0.35}, lo_mastery_delta=-0.05, local_severity_gain=1.5),
        )
        self.error_impacts.setdefault(
            "arithmetic_slip",
            ErrorImpact(families={"numeric": -0.05}, local_severity_gain=0.35),
        )
        return self

    @property
    def codex(self) -> CodexConfig:
        """Non-serialized compatibility view of ``ai.providers.codex``."""

        from learnloop.config.compat import codex_config_view

        return codex_config_view(self)


def default_codex_provider() -> CodexSDKProviderConfig:
    """Return the modeled canonical Codex profile used when none is explicit."""

    return CodexSDKProviderConfig(
        model=DEFAULT_CODEX_MODEL,
        checkout_path="",
        revision="<pinned-commit>",
        startup_command="",
        startup_timeout_seconds=20,
        healthcheck_timeout_seconds=5,
        reasoning_effort=DEFAULT_CODEX_REASONING_EFFORT,
        reasoning_summary="none",
        sdk_python_path="sdk/python/src",
        sdk_codex_bin="",
        sdk_launch_command="",
        base_url="http://127.0.0.1:8765",
        healthcheck_path="/health",
        authoring_path="/authoring-proposal",
        canonical_ingest_path="/canonical-ingest",
        grading_path="/grading-proposal",
        tutor_qa_path="/tutor-qa",
        teach_back_path="/teach-back",
        teach_back_authoring_path="/teach-back-authoring",
        misconception_match_path="/misconception-match",
    )


def default_chatgpt_plan_provider() -> ChatGPTPlanProviderConfig:
    """The code-default ChatGPT-plan profile (plan-first transport T1).

    The slug is a config value (``[ai.providers.chatgpt] model``); the owner
    confirms it against ``learnloop ai models chatgpt`` after signing in.
    """

    return ChatGPTPlanProviderConfig(
        model=DEFAULT_CHATGPT_PLAN_MODEL,
        reasoning_effort=DEFAULT_CODEX_REASONING_EFFORT,
    )


def deepseek_flash_provider() -> AIProviderConfig:
    return OpenAICompatibleProviderConfig(
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        model="deepseek-v4-flash",
        response_format="json_object",
        thinking="disabled",
        max_tokens=8192,
        timeout_seconds=90,
    )


def deepseek_pro_provider() -> AIProviderConfig:
    return OpenAICompatibleProviderConfig(
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        model="deepseek-v4-pro",
        response_format="json_object",
        thinking="enabled",
        reasoning_effort="high",
        max_tokens=16384,
        timeout_seconds=180,
    )


def openrouter_haiku_provider() -> AIProviderConfig:
    """Claude Haiku through OpenRouter, for cheap metered judges."""

    return OpenRouterProviderConfig(
        model=OPENROUTER_HAIKU_MODEL,
        api_key_env="OPENROUTER_API_KEY",
        response_format="json_object",
        timeout_seconds=120,
    )


def openrouter_provider() -> AIProviderConfig:
    # base_url defaults inside the client; max_tokens stays unset so
    # synthesis-sized outputs are never truncated by a blanket cap.
    return OpenRouterProviderConfig(
        model="deepseek/deepseek-chat",
        api_key_env="OPENROUTER_API_KEY",
        response_format="json_object",
        timeout_seconds=180,
    )


def openrouter_embedding_provider() -> AIProviderConfig:
    """The template's embedding profile, for vaults whose config predates it.

    ``embedding.model`` and ``embedding.dimensions`` stay authoritative for
    the route. ``ai.routing.embedding`` defaults to this profile, and
    ``embedding.enabled`` (default false) still gates every request.
    """

    return OpenAIEmbeddingProviderConfig(
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        max_input_tokens=32768,
        timeout_seconds=180,
    )


def openrouter_decider_provider() -> AIProviderConfig:
    """Perplexity Decider v1.1 through OpenRouter (router spec D4, owner)."""

    return DeciderProviderConfig(
        api="openrouter",
        model=DEFAULT_DECIDER_MODEL,
        base_url="https://openrouter.ai/api",
        api_key_env="OPENROUTER_API_KEY",
        timeout_seconds=30,
    )
