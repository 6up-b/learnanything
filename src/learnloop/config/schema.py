from __future__ import annotations

from typing import Annotated, Any, Literal, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    # Owner decision 2026-07-20: the reader is on by default for fresh vaults
    # (lead-user journey needs it without hand-editing config). The §12.3.2
    # invariant — the golden path completes with reader dialogue disabled —
    # is preserved by tests that disable it explicitly; the spine never imports
    # the reader module regardless of this flag.
    reader_enabled: bool = True
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
    is the maximum number of teach_back items in one built practice queue.
    """

    max_followups: int = Field(default=4, ge=1)
    transfer_evidence_multiplier: float = Field(default=0.5, ge=0.0, le=1.0)
    session_cap: int = Field(default=1, ge=0)


class PdfIngestConfig(BaseModel):
    # "native" sends the PDF to the routed OpenAI-compatible chat provider as a
    # file content part instead of extracting locally (see [ingest.native]).
    engine: Literal["auto", "marker", "pypdf", "native"] = "auto"
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
    # manim render quality: "ql" (low, fast) | "qm" | "qh".
    quality: str = "ql"
    timeout_seconds: int = 300
    max_duration_seconds: int = 45
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
    transcription_base_url: str = "https://api.openai.com/v1"
    transcription_model: str = "whisper-1"
    transcription_api_key_env: str = "LEARNLOOP_TRANSCRIPTION_API_KEY"
    # BCP-47 hint forwarded to the endpoint; "" lets the model auto-detect.
    language: str = ""
    timeout_seconds: int = 600
    # Rejected before any upload (OpenAI's transcription limit is 25 MB).
    max_file_mb: int = 25


class NativeIngestConfig(BaseModel):
    """Native multimodal ingestion: media as chat content parts (§spec 1a).

    When enabled AND the routed canonical_ingest provider is an
    OpenAI-compatible chat provider whose profile lists the modality under
    ``input_modalities``, media is ingested natively instead of via the local
    pipeline: audio as input_audio parts (yielding a timestamped transcript),
    PDFs as file parts (set engine = "native" under [ingest.pdf]). Off by
    default: media bytes leave the machine to the chat provider."""

    enabled: bool = False
    audio: bool = True
    pdf: bool = True
    # Base64 inflates ~33% inside a chat body; rejected before any upload.
    max_audio_mb: int = 20


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


AIProviderProfile = Annotated[
    CodexSDKProviderConfig
    | CodexHTTPProviderConfig
    | OpenAICompatibleProviderConfig
    | OpenRouterProviderConfig,
    Field(discriminator="type"),
]


class AIRoutingConfig(BaseModel):
    grading: str | None = None
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


class AIConfig(BaseModel):
    active_provider: str = "codex"
    fallback_provider: str | None = None
    timeout_seconds: int = 180
    providers: dict[str, AIProviderProfile] = Field(default_factory=dict)
    routing: AIRoutingConfig = Field(default_factory=AIRoutingConfig)

    @model_validator(mode="before")
    @classmethod
    def _normalize_provider_profiles(cls, data: Any) -> Any:
        from learnloop.config.compat import normalize_ai_input

        return normalize_ai_input(data)


DEFAULT_CODEX_MODEL = "gpt-5.6-sol"
DEFAULT_CODEX_REASONING_EFFORT = "low"
LEGACY_CODEX_MODEL = "gpt-5.5"
CODEX_LOW_PROVIDER = "codex_low"
CODEX_MEDIUM_PROVIDER = "codex_medium"
CODEX_PROVIDER_NAMES = frozenset({"codex", CODEX_LOW_PROVIDER, CODEX_MEDIUM_PROVIDER})
OPENROUTER_TRANSCRIPTION_PROVIDER = "openrouter_transcription"

DEFAULT_CODEX_TASK_ROUTES = {
    "grading": CODEX_LOW_PROVIDER,
    "canonical_ingest": CODEX_MEDIUM_PROVIDER,
    "canonical_ingest_retry": CODEX_MEDIUM_PROVIDER,
    "authoring": CODEX_MEDIUM_PROVIDER,
    "tutor_qa": CODEX_LOW_PROVIDER,
    "teach_back": CODEX_LOW_PROVIDER,
    "rung_variant": CODEX_LOW_PROVIDER,
    "animation": CODEX_MEDIUM_PROVIDER,
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
    """Curriculum identity-lock policy (knowledge-model §3.4/§12).

    Facet identity locking is independence-gated: a facet locks when its direct
    evidence spans >= ``facet_surface_groups`` distinct surface/correlation
    groups, or its independent evidence mass reaches ``facet_lock_mass``, or it
    enters an active goal's certified scope. KM1 records the policy and the
    ``can_apply`` closure; the independence-gate trigger itself lands with KM2's
    capability ledgers (the seam in ``curriculum_locks.py``).
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
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    locks: LocksConfig = Field(default_factory=LocksConfig)
    error_impacts: dict[str, ErrorImpact] = Field(default_factory=dict)
    fitting: FittingConfig = Field(default_factory=FittingConfig)
    trace_evidence: TraceEvidenceConfig = Field(default_factory=TraceEvidenceConfig)
    diagnostic_augmentation: DiagnosticAugmentationConfig = Field(
        default_factory=DiagnosticAugmentationConfig
    )

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
        self.ai.providers.setdefault("deepseek_flash", deepseek_flash_provider())
        self.ai.providers.setdefault("deepseek_pro", deepseek_pro_provider())
        self.ai.providers.setdefault("openrouter", openrouter_provider())
        for task, default_provider in DEFAULT_CODEX_TASK_ROUTES.items():
            if task == "canonical_ingest_retry":
                # Resolved after the loop so it can mirror the (possibly
                # non-codex) canonical_ingest route once that is settled.
                continue
            routed = getattr(self.ai.routing, task)
            if not routed:
                setattr(
                    self.ai.routing,
                    task,
                    (
                        default_provider
                        if self.ai.active_provider == "codex"
                        else self.ai.active_provider
                    ),
                )
        # canonical_ingest_retry follows the primary canonical_ingest provider
        # when unset, so a non-codex ingest backend still gets a retry pass
        # (previously the retry route was left empty for non-codex providers,
        # silently disabling ingest retry).
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


def openrouter_provider() -> AIProviderConfig:
    # base_url defaults inside the client; max_tokens stays unset so
    # synthesis-sized outputs are never truncated by a blanket cap.
    return OpenRouterProviderConfig(
        model="deepseek/deepseek-chat",
        api_key_env="OPENROUTER_API_KEY",
        response_format="json_object",
        timeout_seconds=180,
    )
