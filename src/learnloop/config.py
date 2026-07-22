from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_CONFIG_TEXT = """schema_version = 1

[storage]
sqlite_path = "state.sqlite"

[algorithms]
# mvp-0.7: canonical shared-facet knowledge model (KM §15). New vaults start
# here; only pre-existing vaults with legacy mvp-0.6 content need
# `learnloop upgrade` to activate it. Legacy `probe_<lo_id>` phases recorded
# under earlier versions replay through the frozen path in services/probes.py
# forever; new diagnostic episodes replay exclusively through
# probe_observations.
algorithm_version = "mvp-0.7"

# Single source of truth for per-attempt-type evidence (Fable's-take item 3).
# evidence_mass weights ability-belief updates (mastery EKF / reliability);
# surface_exposure is the fraction of the item's facet surface the attempt
# certifies as probed (coverage). surface_exposure defaults to evidence_mass;
# dont_know overrides it because a confident "don't know" fully covers the
# surface as evidence-of-absence while remaining self-diagnosis, not
# demonstration.
[evidence.attempt_types]
independent_attempt = { evidence_mass = 1.0 }
open_text = { evidence_mass = 1.0 }
diagnostic_probe = { evidence_mass = 1.0 }
hinted_attempt = { evidence_mass = 1.0 }
reconstruction_after_walkthrough = { evidence_mass = 0.5 }
dont_know = { evidence_mass = 0.7, surface_exposure = 1.0 }
self_report = { evidence_mass = 0.3 }
# Imported past-exam outcome: one exam is one correlated evidence event, so
# each seeded question carries a fraction of a live independent attempt.
exam_evidence = { evidence_mass = 0.35 }
# Held-out practice-exam answer on a fresh, never-practiced item: a proctored
# fresh-item answer is the highest-quality evidence in the system, so it carries
# full evidence mass (deliberately unlike the discounted `exam_evidence` import).
exam_attempt = { evidence_mass = 1.0 }
# Teach-back conversation graded as one attempt: high-quality generative
# evidence, but the opening explanation and follow-up answers are one
# correlated multi-question event, so it carries less than a full independent
# attempt per facet.
teach_back = { evidence_mass = 0.8 }
guided_walkthrough = { evidence_mass = 0.0 }
skip = { evidence_mass = 0.0 }

# Item-side coverage prior per practice mode: how much of an LO's facet surface
# an item of this mode can surface when it has no evidence weights or rubric.
# Not derivable from attempt-type evidence_mass (different question).
[evidence.item_coverage_by_practice_mode]
constructed_response = 0.85
open_text = 0.85
short_answer = 0.75
diagnostic_probe = 0.80
independent_attempt = 0.75
hinted_attempt = 0.65
multiple_choice = 0.45
self_report = 0.25

# Vault-wide evidence correlation lookup (knowledge-model spec §6): discounts
# for repeated/near-clone/shared-stimulus surfaces once facet state is global.
# Reserved for KM2; parsed now so vault TOMLs can set values early.
[evidence.correlation]

# Capability-aware certification budgets (knowledge-model spec §5.4).
# group_budget defaults to evidence_mass(attempt_type) per correlation group;
# max_groups_per_attempt caps the attempt-wide certification ceiling.
[evidence.certification]
max_groups_per_attempt = 3

# Blueprint recipe likelihood defaults (knowledge-model spec §9.2): noisy-AND
# core with slip, plus a guess floor by response format.
[evidence.blueprints]
slip = 0.05

[evidence.blueprints.guess_by_format]
multiple_choice = 0.25
constructed_response = 0.0

[scheduler]
forgetting_risk_weight = 1.0
# Goal facet frontier: fraction of an item's evidence facets not yet on track
# for an active goal (unexamined/known_gap or projected below target_recall
# at the goal's due date), scaled by goal priority.
goal_frontier_weight = 0.25
recent_error_weight = 0.50
probe_eig_weight = 0.25
# Goal quota: guaranteed floor share of the queue overlapping the goal
# frontier; ramps min -> max over the last ramp_days before due_at.
goal_quota_floor_min = 0.30
goal_quota_floor_max = 0.70
goal_quota_ramp_days = 28
short_session_minutes = 20
# Seeded exploration over near-tie candidates so logged slates carry non-degenerate
# selection propensities (off-policy learnability). See architecture_pivot.md Stage 0.
selection_exploration_rate = 0.1
selection_exploration_reward_window = 0.15

[scheduler.surprise]
theta_pos = 1.5
theta_neg = 1.5
alpha_interval = 0.3
f_min = 0.5
f_max = 1.5
epsilon_error_surprise = 0.05

[scheduler.followup]
tau_followup_nats = 0.05
gamma_min = 0.5
min_target_facet_overlap = 0.5
# Gate modernization: thresholds resolve as quantiles of this learner's own
# signal history; the absolute values above remain the cold-start fallback.
threshold_mode = "quantile"
tau_followup_quantile = 0.85
tau_severe_error_quantile = 0.90
quantile_min_samples = 30
quantile_window = 200
# gate_mode = "score" scores all signals through one logistic (threshold last);
# "cascade" preserves the legacy hard trigger/suppression chain bit-for-bit.
gate_mode = "score"
gate_score_threshold = 0.5
gate_subscore_steepness = 12.0
# Predictive facet EIG (logged-but-inert at weight 0.0; see services/predictive_eig.py).
predictive_eig_weight = 0.0
predictive_eig_target_cap = 4
# Misconception discrimination gate (spec_misconception_diagnostics.md §4.1).
# tau_discrimination_power is the Youden-J lower bound a diagnostic candidate
# must clear against an active misconception; require_misconception_discrimination
# routes to no_suitable_item rather than queueing a non-discriminating paraphrase.
tau_discrimination_power = 0.3
require_misconception_discrimination = true

# Goal projection: open-ended goals (no due_at) project facet recall at a
# fixed horizon so the frontier stays defined.
[goals]
default_projection_horizon_days = 30

[hypothesis]
session_card_budget = 2
claim_cooldown_days = 7
overconfidence_min_evidence_mass = 1.0
reentry_gap_days = 7
decay_pressure_target_recall = 0.8
decay_pressure_horizon_days = 60

[forecasts]
default_horizon_days = 14

# Automatic misconception resolution ("close the loop"): an active error event
# is resolved once the learning object accumulates N clean attempts after the
# event was created. Clean = correctness >= auto_resolve_min_correctness, no
# error attribution written, and not a dont_know/skip self-diagnosis.
[misconceptions]
auto_resolve_clean_attempts = 3
auto_resolve_min_correctness = 0.85
# Registry-based resolution and the sim discrimination gate
# (spec_misconception_diagnostics.md §6, §7). Parsed now; consumed in later phases.
tau_misconception_resolved = 0.15
sim_gate_min_sensitivity_lb = 0.7
sim_gate_min_specificity_lb = 0.8
# 8, not 5: a perfect run over N trials has lower bound 0.25^(1/(N+1)) at the
# 25th percentile — 0.794 at N=5 (below the 0.8 specificity gate), 0.857 at N=8.
sim_gate_trials = 8
# Opt-in codex answers-under-belief pass for the gate. 0 = pure deterministic
# (no provider tokens). When > 0, codex role-plays that many planted + clean
# students in ONE call per gate run and their fires combine with the
# deterministic trials. Costs provider tokens per accepted item; the same N>=8
# caveat applies (0.25^(1/(N+1)) at the 25th percentile) to the COMBINED counts.
sim_gate_llm_trials = 0

# Offline parameter fitting from the learner's own logs (`learnloop fit`).
# Fitted sets live in the fitted_parameters table; defaults apply when none is active.
[fitting.fsrs]
min_reviews = 50
min_elapsed_days = 0.5
l2_lambda = 1.0
max_iterations = 300
initial_step = 0.05
min_relative_improvement = 0.01

[mastery]
base_observation_variance = 1.0
sigma2_drift = 0.01
p_max = 4.0
# Display banding: > strong renders green, > developing renders amber, else red.
display_strong_threshold = 0.6
display_developing_threshold = 0.35

# IRT 2PL difficulty-aware mastery update (spec_irt_difficulty.md §4).
# enabled = false restores the legacy logit-space Kalman update bit-for-bit.
[mastery.irt]
enabled = true
discrimination_default = 1.0
difficulty_default = 0.0
difficulty_from_prior = true
difficulty_prior_scale = 2.5
b_abs_max = 4.0
p_clip = 1e-4
mu_abs_max = 5.0
max_logit_step = 4.0
# Empirical-Bayes per-item difficulty posterior (dark by default; see
# MasteryIRTConfig for the identifiability rationale).
eb_difficulty_enabled = false
b_prior_variance = 0.25
b_learning_rate_scale = 0.2
b_max_step = 0.25
b_var_min = 0.01

[probe]
# LEGACY (probe redesign Checkpoint 0.4): attempts_target_default,
# attempts_target_with_strong_claim, claim_skip_threshold, and
# variance_convergence_threshold configure only the frozen pre-redesign replay
# path. Their live roles moved to [probe.episode]: the attempt targets map to
# minimum/maximum_observations, the strong-claim skip maps to the explicit
# fast-path policy (fast_path_claim_threshold), and variance convergence is
# superseded by the §11 completion policy (posterior_stop_threshold).
attempts_target_default = 3
attempts_target_with_strong_claim = 1
claim_skip_threshold = 0.75
variance_convergence_threshold = 0.10
hypothesis_set_max_size = 5

# Diagnostic episodes (spec_probe_eig_redesign.md §5/§11).
[probe.episode]
minimum_independent_observations = 2
maximum_observations = 4
posterior_stop_threshold = 0.85
ambiguity_threshold = 0.30
open_set_prior = 0.10
open_set_trigger_threshold = 0.35
hinted_evidence_weight = 0.5
contaminated_evidence_weight = 0.3
self_graded_evidence_weight = 0.3
session_qualifying_observation_cap = 4
fast_path_enabled = true
fast_path_claim_threshold = 0.75
presentation_ttl_minutes = 240
# Predictive EIG per expected time is the diagnostic default objective (§7.4/§7.5)
# whenever at least predictive_target_minimum held-out instruments exist for the
# episode; hypothesis EIG remains the fallback and audit signal.
predictive_selection_enabled = true
predictive_target_minimum = 2
predictive_target_cap = 6
selection_overhead_seconds = 10.0
# §5.9 fresh-vault onboarding: probes deactivate after this many qualifying
# observations until ordinary practice has started (0 disables).
onboarding_practice_ceiling_observations = 4
# §6.5 re-probe triggers: repeated prediction errors and stale uncertainty.
reprobe_prediction_error_count = 3
reprobe_prediction_error_window = 10
reprobe_predictive_surprise_threshold = 1.0
reprobe_stale_uncertainty_variance = 0.6
reprobe_stale_uncertainty_days = 30

# Parameterized instance generation from admitted family/card bindings (§10).
# llm_surfaces: when an AI provider capable of run_probe_instance_surfaces is
# wired through, instance surfaces come from the LLM (grounded in the LO,
# validated by the structural instance gate) and fall back to the parametric
# templates on provider failure or gate rejection.
[probe.generation]
instances_per_need = 2
auto_generate_on_entry = false
llm_surfaces = true

# Short adaptive dialogue microprobes (§8.1): turns within one block share the
# family's total task evidence mass (§7.7).
[probe.dialogue]
planned_turns = 3
max_turns = 4

# Learner-initiated calibration sessions (§5.9): batch episode blocks across a
# goal scope; lift only the per-session qualifying-observation cap within the
# declared time budget.
[probe.calibration]
default_time_budget_minutes = 20
max_planned_episodes = 8
disagreement_weight = 0.5

# Hierarchical family -> item shrinkage (§9.7, Checkpoint 4.2): item rows shrink
# toward the family-version posterior with this much family-equivalent mass.
[probe.hierarchy]
item_shrinkage_pseudo_count = 25.0

# Family-version lifecycle gates (§9.7, Checkpoint 4.7). Trust requires
# real-learner evidence; synthetic gate statistics never qualify a family.
[probe.lifecycle]
trust_minimum_real_sample = 20
trust_minimum_regrade_checks = 5
trust_minimum_regrade_agreement = 0.80
trust_maximum_negative_information_rate = 0.20
retire_minimum_sample = 10
retire_negative_information_rate = 0.50
retire_regrade_agreement_floor = 0.50

# Shadow-mode alternative selection policies (§13.3, Checkpoint 5.1): log-only
# rankings on the committed presentation. Off-policy estimation stays on hold
# for single-learner vaults.
[probe.shadow]
enabled = true
top_k = 3

# Precommitted diagnostic blocks (Checkpoint 5.2/5.3): redundancy penalty is a
# separate ranking component (never labeled EIG); joint greedy conditional EIG
# applies only to blocks committed before answers are observed.
[probe.block]
family_redundancy_penalty = 0.6
max_block_size = 4
conditional_branch_cap = 3
# §5.6/§5.7: sequential probes run the block-end hook after this many
# observations in the current state segment.
default_block_observations = 2

# IRT difficulty-aware probe conditionals (spec_irt_difficulty.md §5).
[probe.irt]
theta_mastered = 2.0
theta_unfamiliar = -2.0
cut_mid = -1.0
cut_high = 1.0
unfamiliar_error_leak = 0.20
err_low_frac = 0.80
err_mid_frac = 0.50

# Learner self-attributed misconception probe coverage (spec_irt_difficulty.md §12).
[probe.self_tag]
w_base = 0.5
w_max = 0.7
target_degree = 2.0
promotion_threshold = 3

# Exam seeding (`learnloop ingest-exam` + `learnloop seed-exam-attempts`):
# imported per-question outcomes become backdated exam_evidence attempts.
# grader_confidence is the reliability discount persisted on seeded attempts;
# default_learner_confidence (1-5) is used when an outcome omits confidence.
[exam_seeding]
grader_confidence = 0.7
default_learner_confidence = 3

# Tutor Q&A ("ask"): question limits per context (practice: per item+session,
# feedback: per attempt, library: per note per day) and the read-side
# uncertainty bump applied for recent unresolved questions about a facet.
[tutor_qa]
max_questions_practice = 3
max_questions_feedback = 5
max_questions_library = 8
apply_uncertainty_effect = true
uncertainty_evidence_mass = 0.15

# Promoting Socratic tutor questions to practice items / learning objects.
# Gap route: a "this exposed a gap" promotion writes a low self-report claim
# (gap_claim_level at gap_claim_pseudo_count pseudo-observations) and counts as
# an unresolved-question observation with its own likelihood slot fit from the
# learner's gap-declaration -> failure lift, falling back to
# gap_declaration_solid_likelihood_ratio below gap_declaration_likelihood_min_samples.
# The filed need goes stale after gap_need_ttl_days; requested_items_per_session
# bounds the scheduler floor for promoted-but-unattempted items.
[tutor_promotion]
gap_claim_level = 0.25
gap_claim_pseudo_count = 2.0
gap_declaration_solid_likelihood_ratio = 0.35
gap_declaration_likelihood_min_samples = 12
gap_need_ttl_days = 21
requested_items_per_session = 1

# Teach-back conversations: the learner explains, an AI naive student asks up
# to max_followups questions (one per rubric criterion, uncertainty-ranked with
# transfer escalation), and the transcript is graded as one attempt.
# transfer_evidence_multiplier symmetrically discounts the evidence mass of
# transfer-tier criterion evidence; session_cap bounds teach_back items per
# built queue.
[teach_back]
max_followups = 3
transfer_evidence_multiplier = 0.5
session_cap = 1

[ingest]
window_char_cap = 150000
min_content_chars = 400
default_goal_priority = 0.5
allow_auto_captions = false

# PDF extraction for canonical sources (textbook chapters, past exams, any
# ingested .pdf). engine "auto" uses marker-pdf (structured Markdown with
# headings, tables, LaTeX math, and OCR for scanned pages) when installed
# (`pip install learnloop[pdf]`), falling back to plain pypdf text extraction.
# use_llm adds marker's VLM boost for difficult scans and dense math: hard
# regions are sent to an OpenAI-compatible endpoint -- e.g. a local vLLM
# serving deepseek-ai/DeepSeek-OCR (llm_base_url = "http://127.0.0.1:8000/v1",
# llm_model = "deepseek-ai/DeepSeek-OCR") or any hosted vision model. The API
# key is read from the env var named by llm_api_key_env. Marker conversions
# are cached under .learnloop/source-cache/pdf/ keyed by file bytes + config.
[ingest.pdf]
engine = "auto"
# "" = auto-detect (GPU when the installed torch supports it); pin with
# "cuda", "cuda:1", "cpu", or "mps" to override.
torch_device = ""
force_ocr = false
use_llm = false
llm_service = "marker.services.openai.OpenAIService"
llm_base_url = ""
llm_model = ""
llm_api_key_env = "LEARNLOOP_PDF_LLM_API_KEY"

# Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1).
# Preflight/build-plan estimates read these; a stage exceeding its ceiling
# shards or pauses for narrower scope — it never silently truncates.
[ingest.budgets]
inventory_input_tokens = 20000
inventory_output_tokens = 3000
synthesis_shard_input_tokens = 40000
synthesis_shard_output_tokens = 10000
evidence_span_input_tokens = 12000
synthesis_total_input_ceiling = 48000
synthesis_output_tokens = 16000
append_neighborhood_input_tokens = 24000
append_output_tokens = 10000
# Span-request protocol caps (§8.5): one bounded request round only.
synthesis_span_request_max_count = 12
synthesis_span_char_cap = 4000
# Quick add (§1): ToC-guided relevant-scope cap.
quick_add_scope_input_tokens = 40000

# Per-provider context/output limits consulted by preflight, keyed by the
# [ai.providers.<name>] entries (source-ingestion spec §3.1), e.g.
# [ingest.providers.codex] context_tokens / max_output_tokens.
# For openrouter, set these to the chosen model's real limits, e.g.
# [ingest.providers.openrouter]
# context_tokens = 128000
# max_output_tokens = 32768

# Durable ingest-queue worker settings (source-ingestion spec §6.2). One worker
# (sidecar background loop or foreground CLI) drains queued jobs at a time under
# a single lease; a running lease older than lease_ttl_seconds is recovered to
# failed(interrupted) on startup and its queued siblings resume.
[ingest.runner]
lease_ttl_seconds = 120
heartbeat_interval_seconds = 15
poll_interval_seconds = 1.0

[ai]
active_provider = "codex"
fallback_provider = ""
timeout_seconds = 60

[ai.routing]
grading = "codex"
canonical_ingest = "codex"
canonical_ingest_retry = ""
authoring = "codex"
# Empty = follow ai.active_provider; point at any configured provider to route
# tutor Q&A elsewhere (a vault decision, not forced-cheap).
tutor_qa = ""
# Empty = follow ai.active_provider; teach-back questions + grading routing.
teach_back = ""

[ai.providers.codex]
type = "codex_sdk"
model = "gpt-5.5"
# Per-machine; set LEARNLOOP_CODEX_CHECKOUT_PATH in ~/.config/learnloop/settings.env.
checkout_path = ""
revision = "<pinned-commit>"
startup_command = ""
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
reasoning_effort = "medium"
reasoning_summary = "none"
sdk_python_path = "sdk/python/src"
sdk_codex_bin = ""
sdk_launch_command = ""
base_url = "http://127.0.0.1:8765"
healthcheck_path = "/health"
authoring_path = "/authoring-proposal"
canonical_ingest_path = "/canonical-ingest"
grading_path = "/grading-proposal"
misconception_match_path = "/misconception-match"

[ai.providers.deepseek_flash]
type = "openai_chat"
base_url = "https://api.deepseek.com"
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-flash"
response_format = "json_object"
thinking = "disabled"
max_tokens = 8192
timeout_seconds = 90

[ai.providers.deepseek_pro]
type = "openai_chat"
base_url = "https://api.deepseek.com"
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-pro"
response_format = "json_object"
thinking = "enabled"
reasoning_effort = "high"
max_tokens = 16384
timeout_seconds = 180

# Any OpenRouter model slug works here: "anthropic/claude-sonnet-4.5",
# "openai/gpt-5-mini", "deepseek/deepseek-chat", ... Set OPENROUTER_API_KEY in
# the vault .env or ~/.config/learnloop/settings.env.
[ai.providers.openrouter]
type = "openrouter"
model = "deepseek/deepseek-chat"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"
timeout_seconds = 180
# base_url = "https://openrouter.ai/api/v1"  # default; override for proxies
# response_format = "json_schema"            # strict per-request schema on supporting models
# reasoning_effort = "medium"                # OpenRouter unified reasoning effort
# http_referer = ""                          # optional attribution header
# x_title = "LearnLoop"                      # optional attribution header

[codex]
provider = "sdk"
# Per-machine; set LEARNLOOP_CODEX_CHECKOUT_PATH in ~/.config/learnloop/settings.env.
checkout_path = ""
revision = "<pinned-commit>"
startup_command = ""
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
model = "gpt-5.5"
reasoning_effort = "medium"
reasoning_summary = "none"
sdk_python_path = "sdk/python/src"
sdk_codex_bin = ""
sdk_launch_command = ""
base_url = "http://127.0.0.1:8765"
healthcheck_path = "/health"
authoring_path = "/authoring-proposal"
canonical_ingest_path = "/canonical-ingest"
grading_path = "/grading-proposal"
misconception_match_path = "/misconception-match"

# Family-keyed mastery damage per error type (spec §"Error-aware updates").
# recall_failure is the deterministic attribution for `dont_know` attempts.
[error_impacts]
max_sharpening = 3.0

[error_impacts.recall_failure]
families = { recall = -0.25 }
lo_mastery_delta = -0.05
local_severity_gain = 0.8

[error_impacts.scaffold_failure]
families = { recall = -0.35 }
lo_mastery_delta = -0.05
local_severity_gain = 1.5

[error_impacts.arithmetic_slip]
families = { numeric = -0.05 }
lo_mastery_delta = 0.0
local_severity_gain = 0.35

# Capability damping/shrinkage for shared-parent facet belief (knowledge-model
# spec §4.2). Reserved for KM2+; residual activation ships default-off.
[capabilities]

# Identity-lock policy (knowledge-model spec §3.4): a facet's semantic identity
# locks at direct evidence in >=2 distinct surface/correlation groups, at
# facet_lock_mass independent evidence mass, or on entering an active goal's
# certified scope — whichever comes first.
[locks]
facet_lock_mass = 2.0
facet_surface_groups = 2

# NOTE: [cross_lo_propagation] is retired (knowledge-model §8.3/§15). The LO-to-LO
# graph-propagated prior is prerequisite-only, direction-respecting, and
# shadow/diagnostic-only; its error_gates were dormant. `learnloop doctor` warns
# when a vault TOML still declares the block.

[recall_coverage.severity_examples.first_dont_know]
attempt_type = "dont_know"
hints_used = 0
correctness = 0.0
expected_correctness = 0.65
effective_coverage = 0.85
expected_error_type = "recall_failure"
expected_severity_band = [0.70, 0.82]

[recall_coverage.severity_examples.second_same_item_dont_know]
attempt_type = "dont_know"
hints_used = 0
correctness = 0.0
expected_correctness = 0.65
effective_coverage = 0.85
recent_same_item_failures = 1
expected_error_type = "recall_failure"
expected_severity_band = [0.95, 1.00]

[recall_coverage.severity_examples.second_same_facet_dont_know]
attempt_type = "dont_know"
hints_used = 0
correctness = 0.0
expected_correctness = 0.65
effective_coverage = 0.85
recent_same_facet_failures = 1
expected_error_type = "recall_failure"
expected_severity_band = [0.80, 1.00]

[recall_coverage.severity_examples.hinted_dont_know]
attempt_type = "dont_know"
hints_used = 2
correctness = 0.0
expected_correctness = 0.65
effective_coverage = 0.80
expected_error_type = "scaffold_failure"
expected_severity_band = [0.85, 0.95]

[recall_coverage.severity_examples.arithmetic_slip]
attempt_type = "independent_attempt"
correctness = 0.75
expected_correctness = 0.70
effective_coverage = 0.85
target_error_type = "arithmetic_slip"
expected_error_type = "arithmetic_slip"
expected_severity_band = [0.25, 0.35]

[recall_coverage.severity_examples.ambiguous_item]
attempt_type = "independent_attempt"
correctness = 0.0
expected_correctness = 0.70
effective_coverage = 0.85
bad_item_suspicion = 0.70
expected_error_type = "recall_failure"
expected_severity_band = [0.45, 0.75]
"""


class StorageConfig(BaseModel):
    sqlite_path: str = "state.sqlite"


class AlgorithmsConfig(BaseModel):
    # Fallback for configs that omit the field, i.e. vaults created before the
    # mvp-0.7 template. Treat them as legacy; activation must go through
    # `learnloop upgrade`, never through a silent default flip. New vaults get
    # an explicit "mvp-0.7" from DEFAULT_CONFIG_TEXT.
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
    # Matches DEFAULT_CONFIG_TEXT: exploration must stay on even for vaults whose
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


class ForecastsConfig(BaseModel):
    default_horizon_days: int = Field(default=14, ge=1)


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
    maximum_observations: int = 4
    posterior_stop_threshold: float = 0.85
    # A high-cost hypothesis pair is unresolved while the smaller of the two
    # probabilities exceeds this fraction of the larger (§11).
    ambiguity_threshold: float = 0.30
    open_set_prior: float = 0.10
    open_set_trigger_threshold: float = 0.35
    hinted_evidence_weight: float = 0.5
    contaminated_evidence_weight: float = 0.3
    self_graded_evidence_weight: float = 0.3
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
    max_turns: int = Field(default=4, ge=1, le=8)


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
    # replay path in services/probes.py. Live policy lives in `episode`; see the
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
    facet_recall_prior_pseudo_count: float = 1.0
    facet_blend_evidence_count: float = 4.0
    bad_item_min_evidence: int = 3
    bad_item_suspicion_review_threshold: float = 0.65
    bad_item_suspicion_damage_mitigation_cap: float = 0.20
    max_error_sharpening: float = 3.0
    kappa_uncertain: float = 2.0
    coverage_epsilon: float = 1e-3
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
    # services/question_signal.py), keeping this a single self-retiring
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
    conversation (one per selected rubric criterion).
    ``transfer_evidence_multiplier`` is the symmetric evidence-mass multiplier
    applied to facet evidence contributed by transfer-tier rubric criteria —
    both success and failure are discounted equally, and the multiplier is
    read from config at apply time so replay reproduces it. ``session_cap``
    is the maximum number of teach_back items in one built practice queue.
    """

    max_followups: int = Field(default=3, ge=1)
    transfer_evidence_multiplier: float = Field(default=0.5, ge=0.0, le=1.0)
    session_cap: int = Field(default=1, ge=0)


class PdfIngestConfig(BaseModel):
    engine: Literal["auto", "marker", "pypdf"] = "auto"
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


class IngestBudgetsConfig(BaseModel):
    """Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1)."""

    model_config = ConfigDict(extra="allow")

    inventory_input_tokens: int = 20000
    inventory_output_tokens: int = 3000
    synthesis_shard_input_tokens: int = 40000
    synthesis_shard_output_tokens: int = 10000
    evidence_span_input_tokens: int = 12000
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
    pdf: PdfIngestConfig = Field(default_factory=PdfIngestConfig)
    budgets: IngestBudgetsConfig = Field(default_factory=IngestBudgetsConfig)
    providers: dict[str, IngestProviderLimits] = Field(default_factory=dict)
    runner: IngestRunnerConfig = Field(default_factory=IngestRunnerConfig)


class CodexConfig(BaseModel):
    provider: str = "sdk"
    checkout_path: str = ""  # per-machine; see LEARNLOOP_CODEX_CHECKOUT_PATH
    revision: str = "<pinned-commit>"
    startup_command: str = ""
    startup_timeout_seconds: int = 20
    healthcheck_timeout_seconds: int = 5
    auth_mode: str = "chatgpt"
    model: str = "gpt-5.5"
    reasoning_effort: str = "medium"
    reasoning_summary: str = "none"
    sdk_python_path: str = "sdk/python/src"
    sdk_codex_bin: str = ""
    sdk_launch_command: str = ""
    base_url: str = "http://127.0.0.1:8765"
    healthcheck_path: str = "/health"
    authoring_path: str = "/authoring-proposal"
    canonical_ingest_path: str = "/canonical-ingest"
    grading_path: str = "/grading-proposal"
    tutor_qa_path: str = "/tutor-qa"
    teach_back_path: str = "/teach-back"
    misconception_match_path: str = "/misconception-match"


class AIProviderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "codex_sdk"
    model: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    response_format: str | None = None
    thinking: str | None = None
    reasoning_effort: str | None = None
    reasoning_summary: str | None = None
    max_tokens: int | None = None
    timeout_seconds: int | None = None
    # OpenRouter attribution headers (type = "openrouter" only).
    http_referer: str | None = None
    x_title: str | None = None

    checkout_path: str | None = None
    revision: str | None = None
    startup_command: str | None = None
    startup_timeout_seconds: int | None = None
    healthcheck_timeout_seconds: int | None = None
    auth_mode: str | None = None
    sdk_python_path: str | None = None
    sdk_codex_bin: str | None = None
    sdk_launch_command: str | None = None
    healthcheck_path: str | None = None
    authoring_path: str | None = None
    canonical_ingest_path: str | None = None
    grading_path: str | None = None
    tutor_qa_path: str | None = None
    teach_back_path: str | None = None
    misconception_match_path: str | None = None


class AIRoutingConfig(BaseModel):
    grading: str | None = None
    canonical_ingest: str | None = None
    canonical_ingest_retry: str | None = None
    authoring: str | None = None
    tutor_qa: str | None = None
    # Teach-back naive-student questions + transcript grading. Empty = follow
    # ai.active_provider (same fallback chain as tutor_qa).
    teach_back: str | None = None


class AIConfig(BaseModel):
    active_provider: str = "codex"
    fallback_provider: str | None = None
    timeout_seconds: int = 60
    providers: dict[str, AIProviderConfig] = Field(default_factory=dict)
    routing: AIRoutingConfig = Field(default_factory=AIRoutingConfig)


class ErrorImpact(BaseModel):
    """Error impact settings.

    ``lo_mastery_delta`` remains for legacy compatibility. New recall coverage
    code uses ``local_severity_gain`` to sharpen the EKF observation instead of
    applying a separate mastery nudge.
    """

    families: dict[str, float] = Field(default_factory=dict)
    lo_mastery_delta: float = 0.0
    local_severity_gain: float = 0.8


class ErrorGate(BaseModel):
    """Per-error-type cross-LO propagation gate (spec §"Error-type gate")."""

    mean_factor: float = 1.0
    variance_factor: float = 1.0
    scope: str = "all"


class CrossLoPropagationDefaults(BaseModel):
    max_depth: int = 3
    hop_decay: float = 0.5
    total_propagated_weight_cap: float = 0.7


class CrossLoPropagationConfig(BaseModel):
    """RETIRED (knowledge-model §8.3/§15). Retained only so legacy vault TOMLs
    that still declare ``[cross_lo_propagation]`` continue to parse; no code
    reads it. The LO-to-LO graph prior is prerequisite-only, direction-respecting,
    and shadow/diagnostic-only, and ``error_gates`` was already dormant.
    ``learnloop doctor`` emits a migration warning when the block is present.
    """

    default: CrossLoPropagationDefaults = Field(default_factory=CrossLoPropagationDefaults)
    error_gates: dict[str, ErrorGate] = Field(default_factory=dict)


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
    """

    model_config = ConfigDict(extra="allow")

    max_groups_per_attempt: int = 3
    group_budgets: dict[str, float] = Field(default_factory=dict)


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


class LearnLoopConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    storage: StorageConfig = Field(default_factory=StorageConfig)
    algorithms: AlgorithmsConfig = Field(default_factory=AlgorithmsConfig)
    evidence: EvidenceConfig = Field(default_factory=EvidenceConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    goals: GoalsConfig = Field(default_factory=GoalsConfig)
    hypothesis: HypothesisConfig = Field(default_factory=HypothesisConfig)
    forecasts: ForecastsConfig = Field(default_factory=ForecastsConfig)
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
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    locks: LocksConfig = Field(default_factory=LocksConfig)
    error_impacts: dict[str, ErrorImpact] = Field(default_factory=dict)
    cross_lo_propagation: CrossLoPropagationConfig = Field(default_factory=CrossLoPropagationConfig)
    fitting: FittingConfig = Field(default_factory=FittingConfig)

    @model_validator(mode="before")
    @classmethod
    def _normalize_error_impacts_max_sharpening(cls, data):
        if not isinstance(data, dict):
            return data
        impacts = data.get("error_impacts")
        if not isinstance(impacts, dict) or "max_sharpening" not in impacts:
            return data
        normalized = dict(data)
        normalized_impacts = dict(impacts)
        max_sharpening = normalized_impacts.pop("max_sharpening")
        recall_coverage = dict(normalized.get("recall_coverage") or {})
        recall_coverage.setdefault("max_error_sharpening", max_sharpening)
        normalized["recall_coverage"] = recall_coverage
        normalized["error_impacts"] = normalized_impacts
        return normalized

    @model_validator(mode="after")
    def _ensure_ai_legacy_codex_profile(self) -> "LearnLoopConfig":
        if "codex" not in self.ai.providers:
            self.ai.providers["codex"] = ai_provider_from_codex(self.codex)
        self.ai.providers.setdefault("deepseek_flash", deepseek_flash_provider())
        self.ai.providers.setdefault("deepseek_pro", deepseek_pro_provider())
        self.ai.providers.setdefault("openrouter", openrouter_provider())
        if not self.ai.routing.grading:
            self.ai.routing.grading = self.ai.active_provider
        if not self.ai.routing.canonical_ingest:
            self.ai.routing.canonical_ingest = self.ai.active_provider
        if not self.ai.routing.authoring:
            self.ai.routing.authoring = self.ai.active_provider
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
        # [cross_lo_propagation].error_gates seeding is retired (knowledge-model
        # §8.3): the gates were dormant and the config block is deprecated.
        return self


def ai_provider_from_codex(config: CodexConfig) -> AIProviderConfig:
    provider_type = "http_adapter" if config.provider.lower() == "http" else "codex_sdk"
    return AIProviderConfig(
        type=provider_type,
        model=config.model,
        checkout_path=config.checkout_path,
        revision=config.revision,
        startup_command=config.startup_command,
        startup_timeout_seconds=config.startup_timeout_seconds,
        healthcheck_timeout_seconds=config.healthcheck_timeout_seconds,
        auth_mode=config.auth_mode,
        reasoning_effort=config.reasoning_effort,
        reasoning_summary=config.reasoning_summary,
        sdk_python_path=config.sdk_python_path,
        sdk_codex_bin=config.sdk_codex_bin,
        sdk_launch_command=config.sdk_launch_command,
        base_url=config.base_url,
        healthcheck_path=config.healthcheck_path,
        authoring_path=config.authoring_path,
        canonical_ingest_path=config.canonical_ingest_path,
        grading_path=config.grading_path,
        tutor_qa_path=config.tutor_qa_path,
        teach_back_path=config.teach_back_path,
        misconception_match_path=config.misconception_match_path,
    )


def deepseek_flash_provider() -> AIProviderConfig:
    return AIProviderConfig(
        type="openai_chat",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        model="deepseek-v4-flash",
        response_format="json_object",
        thinking="disabled",
        max_tokens=8192,
        timeout_seconds=90,
    )


def deepseek_pro_provider() -> AIProviderConfig:
    return AIProviderConfig(
        type="openai_chat",
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
    return AIProviderConfig(
        type="openrouter",
        model="deepseek/deepseek-chat",
        api_key_env="OPENROUTER_API_KEY",
        response_format="json_object",
        timeout_seconds=180,
    )


_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ConfigLoadError(ValueError):
    def __init__(self, path: Path, message: str):
        self.path = path
        super().__init__(message)


CODEX_CHECKOUT_ENV = "LEARNLOOP_CODEX_CHECKOUT_PATH"


def global_settings_path() -> Path:
    """Location of the machine-global learnloop settings env file.

    This holds per-machine settings that should not live in a vault's committed
    ``learnloop.toml`` -- most notably the local Codex checkout path. Overridable
    with ``LEARNLOOP_CONFIG_DIR``; otherwise ``XDG_CONFIG_HOME`` or ``~/.config``.
    """

    override = os.environ.get("LEARNLOOP_CONFIG_DIR")
    if override:
        base = Path(override).expanduser()
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        root = Path(xdg).expanduser() if xdg else Path.home() / ".config"
        base = root / "learnloop"
    return base / "settings.env"


def _apply_global_overrides(config: LearnLoopConfig) -> LearnLoopConfig:
    """Overlay machine-global settings (env / global settings file) onto config.

    The Codex checkout path is a per-machine concern, so it is sourced from the
    ``LEARNLOOP_CODEX_CHECKOUT_PATH`` env var rather than the committed vault
    config. When set, it wins over any ``checkout_path`` in ``learnloop.toml``.
    """

    checkout = os.environ.get(CODEX_CHECKOUT_ENV, "").strip()
    if checkout:
        resolved = str(Path(checkout).expanduser())
        config.codex.checkout_path = resolved
        provider = config.ai.providers.get("codex")
        if provider is not None:
            provider.checkout_path = resolved
    return config


def load_config(path: Path) -> LearnLoopConfig:
    # Precedence: shell env > vault-local .env > machine-global settings.env.
    # load_dotenv never overwrites keys already in os.environ, so loading the
    # vault .env first lets it win over the global file for the same key.
    load_dotenv(path.parent / ".env")
    load_dotenv(global_settings_path())
    try:
        with path.open("rb") as handle:
            config = LearnLoopConfig.model_validate(tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLoadError(path, _format_toml_error(path, exc)) from exc
    return _apply_global_overrides(config)


def _format_toml_error(path: Path, exc: tomllib.TOMLDecodeError) -> str:
    message = f"Could not parse {path}: {exc}"
    hint = _windows_path_hint(path, exc)
    return f"{message}\n{hint}" if hint else message


def _windows_path_hint(path: Path, exc: tomllib.TOMLDecodeError) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    line_number = getattr(exc, "lineno", None) or _line_number_from_toml_error(str(exc))
    line = _line_at(text, line_number)
    if line is None:
        return None
    if "\\" not in line or "=" not in line:
        return None
    key = line.split("=", 1)[0].strip()
    if key not in {"checkout_path", "sdk_python_path", "sdk_codex_bin", "sdk_launch_command"}:
        return None
    return (
        "Likely cause: a Windows path is written with backslashes inside a "
        "double-quoted TOML string. TOML treats sequences like \\U as escapes. "
        "For Codex paths, use forward slashes, for example "
        'checkout_path = "C:/Users/banan/OneDrive/Documents/thinking/learnloop/codex", '
        "or use single quotes around the Windows path."
    )


def _line_number_from_toml_error(message: str) -> int | None:
    match = re.search(r"line (\d+)", message)
    return int(match.group(1)) if match else None


def _line_at(text: str, line_number: int | None) -> str | None:
    if line_number is None:
        return None
    lines = text.splitlines()
    if line_number < 1 or line_number > len(lines):
        return None
    return lines[line_number - 1]


def load_dotenv(path: Path) -> None:
    """Load vault-local environment variables without overriding the shell."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not _ENV_KEY_RE.match(key) or key in os.environ:
            continue
        os.environ[key] = _parse_dotenv_value(value)


def _parse_dotenv_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if "#" in value:
        value = value.split("#", 1)[0].rstrip()
    return value


def write_default_config(path: Path) -> None:
    if path.exists():
        return
    path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
