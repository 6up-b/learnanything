"""Generated configuration text and the effective-defaults snapshot contract."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION

if TYPE_CHECKING:
    from learnloop.config.schema import LearnLoopConfig


# Retained only as the before-image for the template-equivalence guard. New
# vaults are written from the decision-only template below.
LEGACY_DEFAULT_CONFIG_TEXT = """schema_version = 1

[storage]
sqlite_path = "state.sqlite"

[algorithms]
# mvp-0.9: the mvp-0.8 authority-propagation projection (P0.5 cutover, spec §7.2)
# plus cross-channel reveal accounting (migration 154) -- an attempt taken after
# the answer was exposed is recorded as primed, which changes evidence recording
# and so must be replayable under its own version. The PROJECTION is unchanged:
# mvp-0.9 is a successor tag on the mvp-0.8 namespace
# (`assessment_contracts.P0_PROJECTION_VERSIONS`), which is itself a strict
# superset of the mvp-0.7 canonical shared-facet knowledge model plus the
# P0.2/P0.3 calibrated grade channel, robust composition, and
# reliability-discounted certification. New vaults start here. Pre-existing
# mvp-0.7 vaults activate the projection via `learnloop upgrade`; pre-existing
# legacy mvp-0.6 content upgrades to mvp-0.7 first. Legacy `probe_<lo_id>` phases
# recorded under earlier versions replay through the frozen path forever; new
# diagnostic episodes replay exclusively through probe_observations under the
# pinned channel snapshot.
algorithm_version = "mvp-0.9"

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
# Predictive facet EIG (logged-but-inert at weight 0.0; see diagnosis/predictive_eig.py).
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
# adopt_reference_questions: a reader question kept as a reference becomes
# practice once an active LO cites its passage (false: kill switch; adopted
# cards are kept but not served until it is true again).
[tutor_qa]
max_questions_practice = 3
max_questions_feedback = 5
max_questions_library = 8
max_questions_reader = 8
reader_enabled = true
adopt_reference_questions = true
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
# transfer escalation; when the rubric has transfer criteria the final slot is
# guaranteed to be one), and the transcript is graded as one attempt.
# transfer_evidence_multiplier symmetrically discounts the evidence mass of
# transfer-tier criterion evidence; session_cap bounds teach_back items per
# built queue.
[teach_back]
max_followups = 4
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

# Audio ingestion (.mp3/.wav/.m4a/.flac/.ogg/.oga/.opus/.aac). With provider =
# "openai_compatible" the file is sent to an OpenAI-style POST
# {base_url}/audio/transcriptions endpoint (OpenAI whisper, Groq, a local
# faster-whisper server, ...) with the API key read from the env var named by
# transcription_api_key_env; models that reject verbose_json (e.g.
# gpt-4o-transcribe) degrade to a single untimestamped transcript unit. With
# provider = "openrouter" the audio is sent as chat input_audio parts to the
# openrouter profile with transcription_model as the slug (must accept audio
# input; mp3/wav only), reusing OPENROUTER_API_KEY.
[ingest.audio]
provider = "openai_compatible"
transcription_base_url = "https://api.openai.com/v1"
transcription_model = "whisper-1"
transcription_api_key_env = "LEARNLOOP_TRANSCRIPTION_API_KEY"
# BCP-47 hint forwarded to the endpoint; "" lets the model auto-detect.
language = ""
timeout_seconds = 600
# Rejected before any upload (OpenAI's transcription limit is 25 MB).
max_file_mb = 25

# Native multimodal ingestion: when enabled AND the routed canonical_ingest
# provider is an OpenAI-compatible chat provider whose profile lists the
# modality under input_modalities, media is ingested via chat content parts
# instead of the local pipeline: audio as input_audio (yielding a timestamped
# transcript), PDFs as file parts (set engine = "native" under [ingest.pdf]).
# Off by default: media bytes leave the machine to the chat provider.
[ingest.native]
enabled = false
audio = true
pdf = true
max_audio_mb = 20

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

# AI-generated Manim explainer animations (concept inspector -> "generate
# animation"). enabled is a hard kill-switch; every run ALSO requires a
# per-generation consent click — the LLM-written scene code is AST-validated
# and rendered by a local manim subprocess (manim ships with LearnLoop's
# Python environment; verify with: python -m manim --version). The authoring
# model follows [ai.routing] animation.
[animation]
enabled = true
renderer = "manim"
quality = "qm"
timeout_seconds = 600
min_duration_seconds = 30
max_duration_seconds = 60
latex_enabled = false
auto_repair = true

[ai]
active_provider = "codex"
fallback_provider = ""
timeout_seconds = 180

[ai.routing]
grading = "codex_low"
canonical_ingest = "codex_medium"
canonical_ingest_retry = "codex_medium"
authoring = "codex_medium"
tutor_qa = "codex_low"
teach_back = "codex_low"
rung_variant = "codex_low"
animation = "codex_medium"

[ai.providers.codex]
type = "codex_sdk"
model = "gpt-5.6-sol"
# Per-machine; set LEARNLOOP_CODEX_CHECKOUT_PATH in ~/.config/learnloop/settings.env.
checkout_path = ""
revision = "<pinned-commit>"
startup_command = ""
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
reasoning_effort = "low"
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
# input_modalities = ["audio", "pdf"]        # native media this model accepts ([ingest.native])

# ChatGPT plan ("Continue with ChatGPT"): OpenAI models billed to your ChatGPT
# plan, one HTTPS request per call (no Codex process, no shell). Sign in once
# per machine with `learnloop ai signin chatgpt`, pick a model from
# `learnloop ai models chatgpt`, then point routes at the profile, e.g.
# [ai.routing] source_query_rewrite = "chatgpt" and source_rerank = "chatgpt".
# To run everything on it, set [ai] active_provider = "chatgpt" with
# fallback_provider = "codex" (a route that is not pinned uses Codex while the
# plan is signed out or paused), and point the [ai.routing] entries above that
# name codex_low or codex_medium at "chatgpt" (ai.route_reasoning_effort can
# keep "medium" for the codex_medium ones). Unconfigured, nothing changes;
# enabled = false turns the profile off. A snapshot diagnosis's read-only workspace is served by
# LearnLoop: "tools" lets the model list and read the files it needs (each
# file served is recorded), "inline" sends every file in the request.
# [ai.providers.chatgpt]
# type = "chatgpt_plan"
# model = "<a slug from learnloop ai models chatgpt>"
# reasoning_effort = "low"
# response_format = "json_schema"            # or "json_object" (JSON mode + one repair)
# usage_limit_pause_minutes = 15             # pause after a usage-limit error
# timeout_seconds = 60
# workspace_mode = "tools"                   # or "inline"
# max_tool_rounds = 16                       # rounds of workspace calls per turn
# max_entry_chars = 24000                    # characters one read returns at most
# max_workspace_chars = 400000               # characters served per turn at most

[codex]
provider = "sdk"
# Per-machine; set LEARNLOOP_CODEX_CHECKOUT_PATH in ~/.config/learnloop/settings.env.
checkout_path = ""
revision = "<pinned-commit>"
startup_command = ""
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
model = "gpt-5.6-sol"
reasoning_effort = "low"
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

# NOTE: [locks] is retired: facet identity locks were removed (owner,
# 2026-10-12). Merges apply live with an undo and a reword writes a facet
# version (knowledge-model §3.4). `learnloop doctor` warns when a vault TOML
# still declares the block.

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


#: Where the decision-only template names its ``algorithm_version``.
_ALGORITHM_VERSION_PLACEHOLDER = "@ALGORITHM_VERSION@"

_DEFAULT_CONFIG_TEMPLATE = """schema_version = 2

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "@ALGORITHM_VERSION@"

# AI is optional (manual without it); routes use your ChatGPT plan: learnloop ai signin chatgpt.
# Precedence: explicit flag > LEARNLOOP_AI_PROVIDER > task route > active provider.
# Exception: embeddings use only their own route, never env/active/fallback.
[ai]
active_provider = "chatgpt"
fallback_provider = ""

[ai.providers.chatgpt]
type = "chatgpt_plan"
model = "gpt-5.6-sol"
reasoning_effort = "low"

[ai.providers.openrouter]
type = "openrouter"
model = "deepseek/deepseek-chat"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"
timeout_seconds = 180
# input_modalities = ["audio", "pdf"]

[ai.providers.openrouter_embedding]
type = "openai_embedding"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
# embedding.model and embedding.dimensions are authoritative for this route.
timeout_seconds = 180

[ai.routing]
grading = "chatgpt_low"
canonical_ingest = "chatgpt_medium"
canonical_ingest_retry = "chatgpt_medium"
authoring = "chatgpt_medium"
tutor_qa = "chatgpt_low"
teach_back = "chatgpt_low"
rung_variant = "chatgpt_low"
animation = "chatgpt_medium"
transcription = ""
video_generation = ""
embedding = "openrouter_embedding"
# project = ""  # project understanding: probe authoring + closed-book check (empty = the grading route)
field_question_classifier = ""

# Embeddings are opt-in: both switches stay off until you enable them.
# Remote embeddings send learner-derived text to OpenRouter and its upstream
# provider, with data_collection=deny. Vectors approximate plaintext: protect
# them like practice attempts in backups/exports/sync; never share across vaults.
[embedding]
enabled = false
backfill_enabled = false
model = "qwen/qwen3-embedding-8b"
dimensions = 4096

[pf]
generation_enabled = false # PF-b publishes only verified items, capped per day

# F1 is offline analysis, not serving. Paid analysis is independently opt-in.
[field]
active_predictor = "mastery_ekf"
legacy_fallback = "exclude"
question_classification_enabled = false
llm_probability_enabled = false

# auto reads with GLM-OCR (a z.ai key in Settings, or glm_ocr.backend = "local"), else Marker, else pypdf
[ingest.pdf]
engine = "auto" # auto | glm_ocr | marker | pypdf | native (send the PDF to the ingest model)

[animation]
renderer = "manim" # manim | video_model (OpenRouter text-to-video, see [ai.routing] video_generation)

# All other policy uses modeled defaults. Inspect it with:
#   learnloop config effective
# Override any modeled key by adding it under the same TOML path.
"""


def default_config_text(algorithm_version: str = LATEST_ALGORITHM_VERSION) -> str:
    """The decision-only template as a vault at ``algorithm_version`` holds it.

    New vaults are written at ``LATEST_ALGORITHM_VERSION`` (owner decision
    2026-10-12, Slice 1 M2 open question 1); existing vaults keep their version
    until the owner runs ``learnloop upgrade``. Every recorded defaults snapshot
    is pinned (by a test) to this text rendered at its own version, so a
    successor merge appends its tag to ``algorithm_versions.SUCCESSOR_CHAIN``
    (LATEST and every version gate follow) and records its own snapshot.
    """

    return _DEFAULT_CONFIG_TEMPLATE.replace(_ALGORITHM_VERSION_PLACEHOLDER, algorithm_version, 1)


DEFAULT_CONFIG_TEXT = default_config_text()


#: The effective-defaults fingerprint of a new vault, per algorithm version.
#: Each entry is a literal hash (the tripwire), pinned by a test to
#: ``defaults_fingerprint_for_version(version)``: the template rendered at that
#: version (``default_config_text``), so every version keeps its recorded
#: snapshot whichever version the template currently writes. A successor adds
#: its own entry; a deliberate default change recomputes the entries it moves.
DEFAULTS_SNAPSHOT_BY_ALGORITHM: dict[str, str] = {
    # Slice A Phase 1 adds disabled embedding infrastructure and dormant PF
    # routes only; no scoring, scheduling, projection or serving change.
    # Project understanding M1 adds the [project] section and the
    # ai.routing.project route; both act only on the standalone project store.
    # Slice 1 M1 adds the unset diagnosis / diagnosis_judge /
    # diagnosis_generator routes, consumed only by the offline review.
    # Slice A F1 adds offline field analysis and disabled paid routes; Phase 3
    # (PF-a) adds explicit-command family proposal blocking defaults. No live
    # scoring, scheduling, evidence projection or serving change (no Phase 3b).
    # The Slice A 2-3 review adds tutor_qa.adopt_reference_questions = true,
    # the kill switch over the daily-loop reference-question adoption sweep;
    # its default keeps the merged behaviour.
    # Slice 2 T7 adds embedding.map_neighbors_enabled, a display-only kill
    # switch for the knowledge map's item neighbours (no learner-state effect).
    # Phase 5b adds the practice index ([practice_index], modelled defaults
    # only, with its paid dossier/evaluation switches off, and four
    # practice_* routes), which proposes and never serves, plus its query
    # embedding price override. No scoring, scheduling, projection or serving
    # change.
    # Slice 1 M2 adds the [diagnosis] section (modelled defaults only, left
    # out of the decision-only template). It is dormant below mvp-0.10 (the
    # algorithm version gates the split), so mvp-0.9 serving is unchanged.
    # Mobile M1 adds no vault config (the capture host reads its own
    # mobile.toml outside the vault), so neither snapshot moves; recomputed
    # at the merge and confirmed equal.
    # Slice 2 T4 adds the unset ai.routing.contamination_judge route, consumed
    # only by the owner-run `learnloop contamination report` (shadow flags).
    # Slice 2 T5 adds [graph_nomination] (modelled defaults only, left out of
    # the decision-only template): embedding nominations shown to the
    # structuring / append models and cosine review columns. It acts only when
    # embedding.enabled (default false) is also on, changes no scoring,
    # scheduling, projection or serving, and enabled = false is its kill switch.
    # Slice A Phase 5a (PF-b) adds the [pf] section (generation_enabled off,
    # the daily publish cap and generation bounds; only the off switch is in
    # the decision-only template) and the pf_proposers / pf_selection_judge
    # routes: publishing verified items is a content change, gated by its own
    # kill switch, not an algorithm successor. At its merge three template
    # lines equal to modelled defaults were left out to keep the 80-line cap
    # (the bare [ingest] header, the embedding profile's max_input_tokens and
    # animation's enabled = true); the effective config is unchanged by that.
    # Router R0 adds the decider provider type, the code-default
    # openrouter_embedding and openrouter_decider profiles (B6) and the unset
    # router/llm_probability judgment routes. The routes have no live consumer
    # (the router is R2; the llm_probability arms are an opt-in offline
    # harness): no scoring, scheduling, projection or serving change.
    # At its merge (owner, 2026-10-12) ai.routing.field_llm_probability is
    # retired with Phase 2's numeric arm (its template line dropped), and an
    # unset ai.routing.embedding means openrouter_embedding, still gated by
    # embedding.enabled = false. All three snapshots were recomputed then
    # (mvp-0.10 and mvp-0.11 from DEFAULT_CONFIG_TEXT with only
    # algorithm_version replaced); no serving change.
    # Slice 2 T1 adds the [recurrence] section (modelled defaults only) and
    # the unset ai.routing.same_cause_judge route. Both are dormant below
    # mvp-0.12 (the algorithm version gates the recurrence groups), so
    # mvp-0.9, mvp-0.10 and mvp-0.11 serving are unchanged. Every snapshot
    # was recomputed at its merge (defaults_fingerprint_for_version).
    # Slice 2 T6 adds [source_retrieval] (modelled defaults only, left out of
    # the decision-only template) and four unset source_* routes: retrieval is
    # context for the library search, tutor spans, the Quick Add preview and
    # labelled LO suggestions. No scoring, scheduling, projection or serving
    # change, so no successor; enabled = false is its kill switch. All three
    # snapshots were recomputed for it (each moves only because the effective
    # config gains the section and routes), and again for the T6 review fixes
    # (tutor_query_rewrite, retrieval_timeout_seconds, tutor_spans at most 4).
    # At its merge after Slice 2 T1 every snapshot, mvp-0.12's included, was
    # recomputed (defaults_fingerprint_for_version); no serving change.
    # The stuck prompt adds [stuck_prompt] enabled = true (modelled default,
    # left out of the decision-only template), the kill switch of mvp-0.13's
    # "I'm stuck" control. It is dormant below mvp-0.13 (the algorithm version
    # gates it), so mvp-0.9 to mvp-0.12 serving is unchanged. Built as
    # mvp-0.11 and relabelled mvp-0.13 at its merge after Slice 2 T6, where
    # every snapshot was recomputed (defaults_fingerprint_for_version).
    # Daily-loop DL1 adds [plan] (modelled defaults only, left out of the
    # decision-only template), the kill switch and sizes of mvp-0.14's finite
    # daily plan. It is dormant below mvp-0.14 (the algorithm version gates
    # the plan), so mvp-0.9 to mvp-0.13 serving is unchanged. Built as
    # mvp-0.12 and relabelled mvp-0.14 at its merge after the stuck prompt,
    # where every snapshot was recomputed (defaults_fingerprint_for_version);
    # they move only because the effective config gains the section.
    # Owner batch 2 (2026-10-12) adds recurrence.require_guard = false: the
    # mvp-0.12 upgrade's same-cause guard becomes advisory (true restores the
    # refusal). It only decides whether `learnloop upgrade` refuses; no
    # scoring, scheduling, projection or serving change and no version
    # semantics change. Every snapshot moves only because the effective config
    # gains the key; all four were recomputed (defaults_fingerprint_for_version).
    # Router R1 adds the [router] section (modelled defaults only, left out of
    # the decision-only template): log_decisions (decision logging, not a
    # serving change, acts at every version) and probe_tie_admission (the
    # mvp-0.15 kill switch, dormant below mvp-0.15). Built as mvp-0.12 and
    # relabelled mvp-0.15 at its merge after DL1, where every snapshot was
    # recomputed (defaults_fingerprint_for_version); they move only because
    # the effective config gains the section, so mvp-0.9 to mvp-0.14 serving
    # is unchanged.
    # Learner-text gaps add [learner_text_gaps] (modelled defaults only, left
    # out of the decision-only template) and three unset routes
    # (learner_gap_judge, learner_gap_reader, learner_gap_decider): live at
    # every version behind learner_text_gaps.enabled and their own switches;
    # only the sooner check is version-gated (mvp-0.16, dormant below it).
    # Built as mvp-0.13 and relabelled mvp-0.16 at its merge after router R1,
    # where every snapshot was recomputed (defaults_fingerprint_for_version);
    # they move only because the effective config gains the section and
    # routes, so mvp-0.9 to mvp-0.15 serving is unchanged.
    # Facet identity (handoff §4) adds [facet_identity] (modelled defaults
    # only, left out of the decision-only template), the facet_identity_judge
    # route (default: the code-default codex_luna profile, gpt-6-luna) and the
    # code-default codex_luna and openrouter_haiku profiles. It changes which
    # facets ingest mints (a judge merges duplicates, each with an undo), not
    # scoring, scheduling, projection or serving; enabled = false is its kill
    # switch. Its review (F2) defaulted merge_locked_facets to false; the
    # owner's decision at its merge (2026-10-12, option c) restores true:
    # locked facets merge live too, each action naming its lock, with an undo.
    # Merged after learner-text gaps (mvp-0.16), where every snapshot was
    # recomputed (defaults_fingerprint_for_version); no successor.
    # The T6 follow-up (owner decisions 2026-10-12; merged after facet
    # identity) adds the output-budget policy (ai.output_tokens = 16384,
    # ai.route_output_tokens,
    # ai.route_reasoning_effort with low for source_query_rewrite and
    # source_rerank), source_retrieval.pool = "dense_plus_bm25" (chosen by the
    # follow-up evaluation), pool_keyword_extras and tutor_deadline_cancels,
    # and raises three per-question reservation caps (rewrite 0.15, rerank
    # 0.30, practice rerank 0.30). Modelled defaults only, none in the
    # decision-only template. These change, under every version, which source
    # spans the tutor's verifier and the library list see and how much a model
    # may write (context and transport), never scoring, scheduling,
    # projections, evidence, certification or which item is served, and
    # nothing persisted changes meaning (replay makes no model call). T6's rule
    # applies ("retrieval is context, so no successor unless something
    # persisted changes meaning"), with the owner's live-behind-kill-switches
    # decision: no successor (Codex review F7 rejected, see
    # docs/reviews/t6-followup-codex-review.md); the kill switches restore T6
    # as merged. Every snapshot was recomputed (defaults_fingerprint_for_version).
    # EVSI calibration (docs/reviews/evsi-calibration.md; merged after the T6
    # follow-up) adds [evsi] (forecast_logging = true, measured_loss_enabled =
    # false, the shrinkage pseudo-count; modelled defaults, left out of the
    # decision-only template): the voi_forecasts log is logging only and the
    # measured loss is off, so no scoring, scheduling, projection or serving
    # change and no successor. Every snapshot moves only because the effective
    # config gains the section; all eight were recomputed
    # (defaults_fingerprint_for_version).
    # Reader workbench RW1a (docs/reviews/rw1a-inquiry.md; merged after EVSI
    # calibration) adds [reader_inquiry] enabled = true (modelled
    # default, left out of the decision-only template): the kill switch of
    # branching Ask, inquiry status, the detour strip, the reconnect line and
    # its passage-scoped quick check, and the Reader's funnel activity, plus
    # the passage check's spend caps (max_checks_per_day 100,
    # max_usd_per_check 0.25, no metered price; Codex review F2). Content
    # and display only: no scoring, scheduling, projection or serving change,
    # so no successor; it acts at every version. Every snapshot was recomputed
    # with defaults_fingerprint_for_version (each moves only because the
    # effective config gains the section).
    # Owner (2026-10-13): reader_inquiry.max_usd_per_check 0.25 -> 0.50, so a
    # metered passage check can afford its one truncation retry. A spend cap
    # only: no scoring, scheduling, projection or serving change; every
    # snapshot moves because the effective config changed.
    # The proofs-and-explanations route check (grading/proof-alternatives,
    # built as mvp-0.15, a placeholder tag, and relabelled mvp-0.17 at its
    # merge after EVSI calibration) adds [proof_check] enabled = true
    # (modelled default, left out of the decision-only template) and the unset
    # ai.routing.proof_check route. Both are dormant below mvp-0.17 (the
    # algorithm version gates the check), so mvp-0.9 to mvp-0.16 grading is
    # unchanged; every snapshot moves only because the effective config gains
    # them, and all nine were recomputed (defaults_fingerprint_for_version).
    # It landed on main after RW1a and the passage-check cap, where all nine
    # were recomputed again from the composed defaults.
    # Canonical sources (spec_source_practice_and_probes_v1; branch
    # sources/canonical-practice, merged after the route check) adds
    # [source_service] (modelled defaults only, left out of the decision-only
    # template: one master switch, a kill switch per phase, time, prompt-size
    # and money bounds) and four unset routes (source_solution_match,
    # source_compare, exercise_discrimination, worked_example_equivalence).
    # Below mvp-0.18 the switches propose and record only (tools propose,
    # serving paths serve), so mvp-0.9 to mvp-0.17 serving is unchanged. Its
    # two successors were built as mvp-0.15 and mvp-0.16 (placeholder tags)
    # and relabelled mvp-0.18 (the answer-key certification gate) and
    # mvp-0.19 (source-first needs) at its merge. The sources merge moved
    # every snapshot (each moves only because the effective config gains the
    # section and routes); all eleven were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Owner (2026-10-13): source service per-operation caps off by default
    # (source_service.import_max_cost_usd and compare_max_cost_usd 0.25 / 0.05
    # -> None, no cap; one can still be set) and the daily guard
    # (max_daily_cost_usd) 1.00 -> 5.00; spend is observed in real use
    # (`learnloop sources report`) and caps set later from it, the provider
    # key's own limit the hard backstop. Money bounds only: no scoring,
    # scheduling, projection or serving change; every snapshot moves because
    # the effective config changed, and all eleven were recomputed.
    # Facet locks were then removed (facets/locks-and-depends-on; built on
    # merge/facet-locks after EVSI calibration and landed after the sources
    # track): [locks] and merge_locked_facets stay in the schema
    # with their defaults, unread, so no snapshot moves; the legacy before-image
    # drops [locks] (no snapshot moves either, since its values were the
    # defaults). All eight were recomputed at its merge and are unchanged.
    # The facet reword confirm's review (F6; docs/reviews/
    # facet-reword-confirm-codex-review.md) adds facet_identity.reword_confirm
    # = true (modelled default, left out of the decision-only template), the
    # kill switch of the owner's one-tap reword confirm: which facet writes
    # are admitted, live at every version, never scoring, scheduling,
    # projections, evidence or what is served, so no successor. Every snapshot
    # moves only because the effective config gains the key; all eight were
    # recomputed (defaults_fingerprint_for_version) on its branch, and all
    # eleven again from the composed defaults when it landed after the sources
    # track.
    # UX Phase 1 (docs/specs/ux_learnloop_v1.md §6; landed after the facet
    # reword confirm) adds [ingest] auto_build and auto_apply_passing_builds
    # (both true: the kill switches of Add's automatic, reading-order question
    # builds), [ingest.cost_pause] (when an automatic build asks before
    # spending, Q5, and its daily guard daily_cap_usd = 5.00: the owner's
    # 2026-10-13 caps direction, no per-operation cap, applied at the landing),
    # an empty [ai] consent table (the learner's one OK per provider, Q4) and
    # plan.reading_from_furthest = true (the reading step, U4), all modelled
    # defaults left out of the decision-only template. Auto-applied study maps
    # from Add are a content change under the owner's R1 decision, and the
    # reading step a live serving change behind its kill switch at every
    # version (the branch's placeholder successor tag was dropped at the
    # landing: the owner's live-behind-kill-switches ruling, since replay
    # never reads the selection). No scoring, scheduling or projection change
    # and no successor. Every snapshot moves only because the effective config
    # gains the keys; all eleven were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # route-check-in-grader (owner decision 2026-10-13; built as successor
    # mvp-0.18, a placeholder tag, and relabelled mvp-0.20 at its merge after
    # the sources track, facet locks and UX Phase 1) removes the
    # ai.routing.proof_check route (retired: ignored if set) and keeps
    # [proof_check] enabled = true as mvp-0.20's kill switch. Every snapshot
    # moves only because the effective config loses the route; all twelve
    # were recomputed from the composed defaults, UX Phase 1's keys included
    # (defaults_fingerprint_for_version).
    # Value-of-information stopping (serving/voi-stopping; built as successor
    # mvp-0.17, a placeholder tag, and relabelled mvp-0.21 at its merge after
    # the route rules) adds [voi_stopping] (modelled defaults only, left out of
    # the decision-only template: the kill switch, one sub-switch per site and
    # voi-v2's three switches from the multi-family EVSI study,
    # robust_gate_with_value, lookahead_max_checks and robust_quantile) and
    # diagnosis.probe_lane_reads_diagnosis / diagnosis.probe_lane_pending
    # (Part 2's switch and pending rule). All are dormant below mvp-0.21 (the
    # algorithm version gates them), so mvp-0.9 to mvp-0.20 serving is
    # unchanged; every snapshot moves only because the effective config gains
    # the keys, and all thirteen were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # Tier 1 (the Decider migration, owner decision 2026-10-13; built as
    # successor mvp-0.20, a placeholder tag, and relabelled mvp-0.22 at its
    # merge after the route rules and value-of-information stopping) adds
    # [decider_routes] (one kill switch per judgment, each true; modelled
    # defaults, left out of the decision-only template) and the unset
    # ai.routing.tier1_decider route. The serving judgments are dormant below
    # mvp-0.22 (the algorithm version gates them), so mvp-0.9 to mvp-0.21
    # serving is unchanged; facet_span_support, a content check on cited model
    # rewords, acts at every version (no successor, as the reword confirm).
    # Every snapshot moves only because the effective config gains the
    # section and route; all fourteen were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Exam protection's Codex review (F6; docs/reviews/
    # exam-protection-codex-review.md) adds goals.held_out_selection = true
    # (modelled default, left out of the decision-only template), the kill
    # switch of the stage's serving rules (shown material never an exam item,
    # cold probe or cold retry; exposed exam items withdrawn at the exam's
    # start; items made from held-out material out of routine practice). A
    # live change at every version under the owner's standing ruling (live
    # changes behind kill switches, not successors, for serving changes replay
    # never reads), so no successor; off restores the stage's predecessor
    # selection. Every snapshot moves only because the effective config gains
    # the key; all eleven were recomputed (defaults_fingerprint_for_version)
    # on its branch, and all fourteen again from the composed defaults when it
    # landed after value-of-information stopping and Tier 1 (the Decider).
    # Router R2a (the staged frame on Today, owner-directed 2026-10-13; built
    # as successor mvp-0.23, a placeholder tag that kept its label when it
    # landed after exam protection and reading hardening) adds four [router]
    # keys: enabled (the router's kill switch, true), mode ("staged"),
    # card_token_budget (16000, D8) and payload_retention_days (365);
    # modelled defaults, left out of the decision-only template. The staged
    # frame and the P2 bridge are dormant below mvp-0.23 (the algorithm
    # version gates them), so mvp-0.9 to mvp-0.22 serving is unchanged; the
    # receipts R2a adds (presentations, outcomes v2) are logging at every
    # version. Every snapshot moves only because the effective config gains
    # the keys; all fifteen were recomputed from the composed defaults
    # (defaults_fingerprint_for_version) on its branch, and all fifteen again
    # when it landed on main after exam protection.
    # Reader workbench RW3a (docs/reviews/reader-hook-rw3a.md) adds [cues]
    # (enabled = true, density = "normal", one_per_viewport = true,
    # off_sources = []; modelled defaults, left out of the decision-only
    # template): margin cues from the Guide's own citations, display only
    # (taps are salience-only events and learner_card verdicts), so no
    # scoring, scheduling, projection or serving change and no successor;
    # it acts at every version. Every snapshot moves only because the
    # effective config gains the section; all fourteen were recomputed
    # (defaults_fingerprint_for_version) on its branch, and all fifteen
    # again from the composed defaults when it landed after router R2a.
    # Tutor delivery fixes (owner-approved 2026-10-13; docs/reviews/
    # tutor-delivery-fixes.md) add tutor_qa.context_token_budget = 24000 and
    # tutor_qa.resolve_references = true (complete blocks within one budget,
    # cited numbered blocks followed), source_retrieval.passage_token_budget =
    # 4000 (complete passages for the relevance judges) and
    # embedding.backfill_sources_on_extract = true with
    # embedding.source_backfill_max_cost_usd = 1.0 (a completed extraction
    # queues its source's block-vector backfill, only when both embedding
    # switches are on), and (Codex review F5) the kill switches
    # tutor_qa.expanded_delivery = true and source_retrieval.complete_passages
    # = true (false restores the predecessor's passages). Modelled defaults,
    # left out of the decision-only template. Context delivery and retrieval
    # evaluation only: no scoring, scheduling, projection, evidence or serving
    # change, and replay reads none of it, so no successor; each has its kill
    # switch or bound. Every
    # snapshot moves only because the effective config gains the keys; all
    # fourteen were recomputed (defaults_fingerprint_for_version) on its
    # branch, and all fifteen again from the composed defaults when it landed
    # after router R2a and RW3a.
    # GLM-OCR primary document reading (owner request 2026-10-13; docs/reviews/
    # glm-ocr-ingest.md) adds [ingest.pdf.glm_ocr] (backend, endpoints, key
    # variable name, timeout, window size, price, base64 style; modelled
    # defaults, left out of the decision-only template) and the glm_ocr
    # engine. Document extraction only: no scoring, scheduling, projection or
    # serving change, so no successor. Every snapshot moves only because the
    # effective config gains the section; all fourteen were recomputed
    # (defaults_fingerprint_for_version) on its branch (again when its second
    # review raised glm_ocr.request_timeout_seconds to 300, the glmocr SDK's
    # own), and all fifteen again from the composed defaults when it landed
    # after router R2a, RW3a and the tutor delivery fixes.
    # Router R2b + R2c (the model mixture and the restraint, owner decisions
    # 2026-10-13; built as successor mvp-0.24, a placeholder tag that kept its
    # label when it landed after RW3a, the tutor delivery fixes and GLM-OCR,
    # nothing on main having taken it) change router.mode's default to
    # "mixture" (dormant below mvp-0.24, where it serves as "staged") and add
    # modelled [router] keys, left out of the decision-only template: weights
    # (one third each, D1), k (6, D3), epsilon_min (0.02), ties_only (false),
    # timeout_seconds (8), prefetch_timeout_seconds (45), max_daily_cost_usd
    # (5.00: the owner's
    # metered guard, subscription routes uncapped), sensors (true),
    # sensor_source ("decider"), restraint (true), similar_decisions (true,
    # needs embedding.enabled), similar_k (6), similar_include_rate (0.5) and
    # teach_back_summary (true). mvp-0.9 to mvp-0.23 serving is unchanged;
    # every snapshot moves only because the effective config gains the keys,
    # and all sixteen were recomputed from the composed defaults
    # (defaults_fingerprint_for_version) on its branch, and all sixteen again
    # when it landed on main after RW3a, the tutor delivery fixes and GLM-OCR.
    # Plan determinism's Codex review (F2; docs/reviews/
    # plan-determinism-codex-review.md) adds plan.deterministic_staged_plans
    # = true (modelled default, left out of the decision-only template), the
    # kill switch of the stage's serving rule (owner rule 2026-10-13: staged
    # plans are deterministic): where the router composes Today, the plan's
    # pool is the scheduler's greedy order and a contrast pair's member order
    # is the pair's own draw, so the same vault state plans the same blocks in
    # every session. A live change under the owner's standing ruling (live
    # changes behind kill switches, not successors, for serving changes replay
    # never reads), so no successor; off restores the staged plan's pool as
    # mvp-0.23 and mvp-0.24 landed (session-seeded draws). Dormant below
    # mvp-0.23 and with the router off; at mvp-0.24 it fixes the order of the
    # candidates the mixture draws over (the staged rule's pick and the
    # support), while the mixture keeps its own seed, floor and logged
    # propensities. Every snapshot moves only because the effective config
    # gains the key; all fifteen were recomputed
    # (defaults_fingerprint_for_version) on its branch, and all sixteen again
    # from the composed defaults when it landed on main after GLM-OCR and
    # router R2b + R2c.
    # Method-explicit items (owner rule 2026-10-13; built as successor
    # mvp-0.22-placeholder, a placeholder tag, and relabelled mvp-0.25 at its
    # merge after router R2b + R2c) add [required_method] enabled = true
    # (modelled default, left out of the decision-only template), the kill
    # switch of the successor's required-method grading, dormant below it; the
    # unset ai.routing.rubric_phrasing_judge route (the judge of the owner-run
    # `learnloop grading method-phrasing` report and of the one-time
    # required-method statement judgments at import and PF selection; no
    # grading use); and, at its landing, decider_routes.required_method_statement
    # = true (the statement judgment registered as a Tier-1 content task: off,
    # the LLM judge decides it). Every snapshot moves only because the
    # effective config gains the section, the route and the switch; all
    # thirteen were recomputed (defaults_fingerprint_for_version) on its
    # branch, and all seventeen again from the composed defaults when it
    # landed on main after router R2b + R2c and plan determinism.
    # Diagnosis input provenance (owner decision 2026-10-14, "land narrow,
    # then fix source"; docs/reviews/diagnosis-input-provenance.md) adds
    # diagnosis.chat_shows_recorded_text (modelled default, left out of the
    # decision-only template): the kill switch of the chat frontend's rule
    # (c), which shows a model-written text only when its write-time record
    # is complete and every recorded input is safe (off: the C1a narrow rule,
    # nothing derived is shown). Built on by default; it landed on main OFF
    # (2026-10-15) because the final verify reopened two High findings in the
    # release path, and stays off until every model-context build records
    # through one capture point and a clean verify passes. The writers record
    # either way. A read-model change only: the records are append-only
    # receipts nothing in grading, scoring, scheduling, projection or replay
    # reads, so no successor. Every snapshot moves only because the effective
    # config gains the key; all seventeen were recomputed
    # (defaults_fingerprint_for_version) on the branch, and all seventeen
    # again at the landing with the switch off.
    # Saved diagnosis forecasts (owner go-ahead 2026-10-15; docs/reviews/
    # diagnosis-forecast-receipts.md) add diagnosis.forecast_receipts = true
    # (modelled default, left out of the decision-only template), the kill
    # switch of the forecast receipts a completed diagnosis and a scheduled
    # repair cold check write (forecast_receipts, migration 206; built as
    # 230, a placeholder number, and renumbered at its landing after
    # diagnosis input provenance's 205). Logging only: no grading, scoring,
    # scheduling, projection or serving change, replay never reads the
    # receipts, so no successor; it acts at every version. Every snapshot
    # moves only because the effective config gains the key; all seventeen
    # were recomputed (defaults_fingerprint_for_version) on the branch, and
    # all seventeen again from the composed defaults when it landed on main
    # after diagnosis input provenance.
    # UX Phase 4 (practice and feedback, docs/specs/ux_learnloop_v1.md §7.4,
    # §7.5; owner go-ahead 2026-10-15) adds [ui] practice_feedback = "simple"
    # (modelled default, left out of the decision-only template), the kill
    # switch of the simple practice card, feedback, short-check result and
    # session finish ("classic" restores the screens exactly). Display only:
    # the desktop reads it, and no grading, scheduling, evidence, projection or
    # replay path does, so no successor (the owner's live-behind-kill-switches
    # ruling). Every snapshot moves only because the effective config gains
    # the section; all seventeen were recomputed from the composed defaults
    # (defaults_fingerprint_for_version) on its branch, and all seventeen
    # again from the composed defaults when it landed on main after diagnosis
    # input provenance, the Reader PDF selection and saved diagnosis forecasts.
    # The one eligibility decision (mvp-0.27; docs/reviews/
    # serve-eligibility-decision.md) adds [eligibility] enabled = true
    # (modelled default, left out of the decision-only template), the kill
    # switch of that successor; dormant below it. Every snapshot moves only
    # because the effective config gains the section; all eighteen were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW2a (the resumable scratchpad; docs/reviews/
    # reader-workbench-RW2a.md) adds [workbench] enabled = true and
    # open_session_days = 30 (modelled defaults, left out of the
    # decision-only template): the kill switch of the step workbench and a
    # display limit for the recap's "unfinished". A workbench attempt maps
    # onto existing fields (a visible book is one hints_used, the rule
    # submit_reading_question records) through the ordinary submit path, so
    # no scoring, scheduling, projection or serving change and no successor;
    # it acts at every version. Every snapshot moves only because the
    # effective config gains the section; all nineteen were recomputed from
    # the composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW6a ("Last time here"; docs/reviews/
    # reader-workbench-RW6a.md) adds [recap] enabled = true and
    # wrap_up_enabled = true (modelled defaults, left out of the
    # decision-only template): the kill switches of the returning card and
    # of Wrap up. Both are pure reads over existing ledgers that write only
    # salience-only reader events, and nothing in scoring, scheduling,
    # projection or serving reads them, so no scoring, scheduling,
    # projection or serving change and no successor; they act at every
    # version. Every snapshot moves only because the effective config gains
    # the section; all nineteen were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # Reader workbench RW1b (the intent box and active reading; docs/reviews/
    # reader-workbench-RW1b.md) adds [reader_intent] (enabled, speculative_enabled,
    # speculate_after_ms, timeout_seconds, max_calls_per_day), [reader_active_reading]
    # enabled and [reader_formative] enabled (modelled defaults, left out of the
    # decision-only template) and the decider route ai.routing.reader_intent: the
    # intent box's router, active reading's formative questions and missed
    # answers as learner text. Routing writes ledger rows and salience-only
    # events, the questions are formative rows, and a missed answer reaches
    # learner-text gaps as a reader question already does; nothing in scoring,
    # scheduling, projection or serving reads the new keys, so no scoring,
    # scheduling, projection or serving change and no successor; they act at every
    # version. Every snapshot moves only because the effective config gains the
    # sections; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # Reader workbench RW4a (library questions and source comparison;
    # docs/reviews/reader-workbench-RW4a.md) adds [library_ask] (enabled,
    # expand_graph, personalized_default, max_daily_cost_usd) and
    # [reader_compare] enabled (modelled defaults, left out of the
    # decision-only template) and the listwise route ai.routing.library_organizer
    # (low reasoning effort by default): the library answer, its organizer
    # notes, the concept-graph expansion and the display-only comparison.
    # Retrieval is context and the notes and comparison are display (T6's
    # ruling): nothing in scoring, scheduling, projection or serving reads the
    # new keys, so no scoring, scheduling, projection or serving change and no
    # successor; they act at every version. Every snapshot moves only because
    # the effective config gains the sections; all of them were recomputed
    # from the composed defaults (defaults_fingerprint_for_version).
    # Adaptive hints H0 (hint telemetry; docs/reviews/adaptive-hints-H0.md)
    # adds [hints] telemetry_enabled = true (a modelled default, left out of
    # the decision-only template): authored-hint reveals recorded as
    # help_assists rows and attached to the attempt at submit. Telemetry only:
    # hints_used stays the client's count and nothing in scoring, scheduling,
    # projection or serving reads the rows or the key, so no scoring,
    # scheduling, projection or serving change and no successor; it acts at
    # every version. Every snapshot moves only because the effective config
    # gains the section; all of them were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Adaptive hints H1 (approach maps; docs/reviews/adaptive-hints-H1.md)
    # adds [hints] price_per_million (unset) and [hints.maps] (enabled,
    # build_on_serve, max_daily_cost_usd = 0.50; modelled defaults, left out
    # of the decision-only template) and the chat route
    # ai.routing.approach_map (unset: the active provider): a small subgoal
    # map per item, built in the background when the item is served, stored
    # in approach_maps and read by no scoring, scheduling, projection,
    # serving, grading or replay path (the hint writer reads it from H2), so
    # no scoring, scheduling, projection or serving change and no successor;
    # it acts at every version. Every snapshot moves only because the
    # effective config gains the keys; all of them were recomputed from the
    # composed defaults (defaults_fingerprint_for_version).
    # Adaptive hints H2a (the hint service; docs/reviews/adaptive-hints-H2a.md)
    # adds [hints] adaptive_enabled = true, chooser_enabled = true,
    # choice_policy = "sample", chooser_timeout_seconds = 3, help_style =
    # "balanced" and max_daily_cost_usd = 1.00 (modelled defaults, left out of
    # the decision-only template) and the routes ai.routing.hint_chooser (a
    # decider-only route) and ai.routing.hint_writer (unset: the active
    # provider, never Codex): practice.request_hint writes a hint for the
    # learner's work, served only when asked (no UI calls it until H2b). A
    # shown hint reaches the attempt only through hints_used (levels 1-3),
    # primed (levels 4-5) and a tutor_answer reveal on key overlap, with
    # their existing meaning, so no scoring, scheduling, projection or serving
    # change and no successor; it acts at every version. Every snapshot moves
    # only because the effective config gains the keys; all of them were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    # Adaptive hints H2b (the practice screen's hint panel;
    # docs/reviews/adaptive-hints-H2b.md) adds [hints]
    # authored_offer_after_seconds = 4 (a display cap) and
    # outcome_placement_enabled = true (modelled defaults, left out of the
    # decision-only template) and the chat route ai.routing.hint_outcome
    # (unset: the active provider): one background call after a hinted answer
    # graded not fully correct places it on the item's approach map, stored
    # as judgment_ledger rows the report reads. Measurement only: nothing in
    # scoring, scheduling, projection, serving, grading or replay reads it, so
    # no scoring, scheduling, projection or serving change and no successor;
    # it acts at every version. Every snapshot moves only because the
    # effective config gains the keys; all of them were recomputed from the
    # composed defaults (defaults_fingerprint_for_version).
    # Adaptive difficulty AD1 (measure and log; docs/reviews/adaptive-difficulty-ad1.md)
    # adds [adaptive_difficulty] (enabled, forecast_receipts, outside_forecasters,
    # rating_tap, feature_audit, daily_spend_cap_usd = 0.50, price_per_million
    # unset; modelled defaults, left out of the decision-only template),
    # [decider_routes] ad_feature_audit = true and the routes
    # ai.routing.ad_forecast_llm, ad_forecast_decider and ad_feature_audit:
    # receipts (item forecasts, frozen serve inputs, reading opportunities),
    # two logged attempt columns and feature-audit judgments that nothing in
    # scoring, scheduling, projection, serving, grading or replay reads, so no
    # scoring, scheduling, projection or serving change and no successor; it
    # acts at every version. Every snapshot moves only because the effective
    # config gains the keys; all of them were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Reader workbench RW2b + adaptive hints H3 (checks and the help ladder;
    # docs/reviews/reader-workbench-RW2b.md) adds [workbench] help_enabled,
    # symbolic_checks_enabled (false since fix round 9), discriminate_enabled,
    # error_kind_enabled and bridge_enabled (true), max_calls_per_session = 24,
    # max_daily_cost_usd = 1.00 and price_per_million (unset; modelled
    # defaults, left out of the decision-only template) and the chat route
    # ai.routing.workbench_check (unset: the active provider; Codex allowed,
    # estimated_only). A
    # shown check or hint reaches the attempt only through hints_used (one
    # each, levels 1-3) and primed (levels 4-5) and a tutor_answer reveal on
    # key overlap, with their existing meaning, so no scoring, scheduling,
    # projection or serving change and no successor; it acts at every
    # version. Every snapshot moves only because the effective config gains
    # the keys; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # RW2b fix round 9 (the orchestrator's decision) turns
    # workbench.symbolic_checks_enabled off by default (a modelled default,
    # left out of the template): no step or hint claim is labelled checked
    # until the renderer-equivalent checker lands. Display-only labels; no
    # scoring, scheduling, projection or serving change and no successor.
    # Every snapshot moves with the default and was recomputed.
    # Reader workbench RW1c (a tutor that looks things up; docs/reviews/
    # reader-workbench-RW1c.md) adds [reader_tutor] retrieval_enabled and
    # offers_enabled (true; modelled defaults, left out of the decision-only
    # template): the Reader tutor's retrieval, three answer modes,
    # abstention, another way and that didn't help, and the offer buttons
    # under its answers. Retrieval is context and display and the buttons are
    # learner picks (T6's ruling); a Reader question asked inside a workbench
    # session bound to an item is stored on that item and practice session,
    # so it reaches the attempt only through the existing question
    # hint-equivalents and tutor_answer / source_review reveals (their
    # existing meaning; Codex review F1), so no scoring,
    # scheduling, projection or serving change and no successor; it adds no
    # route (the tutor's own; the sources service's for its functions) and
    # acts at every version. Every snapshot moves only because the effective
    # config gains the keys; all of them were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Reader workbench RW4b (exercises from my sources;
    # docs/reviews/reader-workbench-RW4b.md) adds [library_exercises] enabled
    # = true and fallback_enabled = false (modelled defaults, left out of the
    # decision-only template): the Reader's view of the sources service's
    # textbook-exercise candidates with its exposure labels, "use this one"
    # through the service's own import in the workbench, and the retired
    # fallback search. Display and a learner's own pick through the existing
    # import and pick paths: nothing in scoring, scheduling, projection or
    # serving reads the keys, so no scoring, scheduling, projection or serving
    # change and no successor; they act at every version. Every snapshot moves
    # only because the effective config gains the section; all of them were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    # Daily-loop DL2 (intent; docs/reviews/daily-loop-dl2.md) adds [intent]
    # enabled = true, recall_targets_enabled = true and recall_targets (Q8:
    # keep_in_touch 0.80, remember_key_ideas 0.85, work_fluently 0.90,
    # master_tasks_like_these 0.92, uncommitted 0.90) and [capture]
    # test_me_later_days = 7 (modelled defaults, left out of the decision-only
    # template). Intent is read only when serving (exclusion by disposition,
    # "Check once", effective dues at the recall targets, push, admission and
    # re-entry by intent); due_at, FSRS state, evidence and projections are
    # unchanged and replay never reads it, and with no commitment serving is
    # unchanged (the 0.90 ratio is exactly 1). It acts only at the successor
    # mvp-0.29 (the DL2 Codex re-review F2: it changes which items are served
    # as measurements, the 2026-10-17 rule); the sections are present, inert,
    # at every earlier version. Every snapshot moves
    # only because the effective config gains the two sections (checked by
    # dropping them, which reproduces each prior value); all of them were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW3b (discovered cues; docs/reviews/reader-workbench-
    # RW3b.md) adds [cues] discovery_enabled, try_first_enabled,
    # value_order_enabled (true), holdout_rate (0.1),
    # max_calls_per_source_open (12) and max_daily_cost_usd (0.5), and the
    # listwise route ai.routing.passage_cue_judge (empty = the active
    # provider; modelled defaults, left out of the decision-only template):
    # passages found per open target by T6 retrieval and one judgment each,
    # in the background, ordered by the probability the target is still
    # open, with a logged holdout. Display only (taps are salience-only
    # events, learner_card verdicts and impression receipts; "check me" and
    # "try this step first" are learner picks), so no scoring, scheduling,
    # projection or serving change and no successor; it acts at every
    # version. Every snapshot moves only because the effective config gains
    # the keys and the route; all of them were recomputed from the composed
    # defaults (defaults_fingerprint_for_version). RW3b fix round 5 (Codex
    # verify F16) adds [cues] max_calls_per_source_per_day (36): the cue
    # judge's calls per source per rolling 24 hours over every open, counted from the
    # durable receipts; a spend bound, display only, no successor. Every
    # snapshot moved again only for that key, recomputed the same way.
    # Reader workbench RW4d (syntopic reading, kept;
    # docs/reviews/reader-workbench-RW4d.md) adds [reader_compare]
    # keep_enabled = true (a modelled default, left out of the decision-only
    # template): "Keep this comparison" as source-object proposals, the
    # learner's own take, the kept-comparison margin mark, requested
    # perspectives and Keep on the tutor's comparison. Proposals and display:
    # nothing in scoring, scheduling, projection or serving reads the key, so
    # no scoring, scheduling, projection or serving change and no successor;
    # it acts at every version. Every snapshot moves only because the
    # effective config gains the key; all of them were recomputed from the
    # composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW4e (instructional roles;
    # docs/reviews/reader-workbench-RW4e.md) adds [roles]
    # on_demand_enabled = true, positive_filter_enabled = true and
    # batch_max_cost_usd = 5.0, and the listwise route
    # ai.routing.role_labeller (empty = the active provider; modelled
    # defaults, left out of the decision-only template): the Reader's judges'
    # per-passage instructional roles as source-object proposals, the
    # owner-run batch labeller's per-run cap, and their positive use in
    # retrieval, cue shortlists and library grouping (roles add, never
    # exclude). Labels on sources: nothing in scoring, scheduling,
    # projection or serving reads them, so no scoring, scheduling,
    # projection or serving change and no successor; it acts at every
    # version. Every snapshot moves only because the effective config gains
    # the keys and the route; all of them were recomputed from the composed
    # defaults (defaults_fingerprint_for_version).
    # Reader workbench RW7a (reading paths in the Guide;
    # docs/reviews/reader-workbench-RW7a.md) adds [reading_paths]
    # enabled = true and max_daily_cost_usd = 0.5, and the chat route
    # ai.routing.reading_path_judge (empty = the active provider; modelled
    # defaults, left out of the decision-only template): the Guide's path
    # card (section labels with a why, overrides, one exercise per core
    # section, the suggested next line) and its judge's daily cap. Display
    # only: nothing in scoring, scheduling, projection or serving reads a
    # path, so no scoring, scheduling, projection or serving change and no
    # successor; it acts at every version. Every snapshot moves only because
    # the effective config gains the keys and the route; all of them were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW5a (explorable figures; docs/reviews/reader-workbench-RW5a.md)
    # adds [figures] enabled, predictions_enabled, region_enabled and
    # revisions_enabled (true), max_daily_cost_usd = 1.00 and
    # price_per_million (unset; modelled defaults, left out of the
    # decision-only template) and the chat route ai.routing.figure_author
    # (unset: the active provider; Codex allowed, estimated_only; RW5a has
    # no verifier route, the source check is RW5c's). Figures are content and their predictions
    # formative: nothing in scoring, scheduling, projection or serving
    # reads the keys, so no scoring, scheduling, projection or serving
    # change and no successor; they act at every version. Every snapshot
    # moves only because the effective config gains the section and the
    # route; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # Reader workbench RW2c (what helps this learner;
    # docs/reviews/reader-workbench-RW2c.md) adds [workbench]
    # help_outcomes_enabled, examples_enabled, compare_methods_enabled and
    # passage_draw_enabled (true; modelled defaults, left out of the
    # decision-only template): help-outcome lines (a pure read) for the hint
    # writer and chooser, the worked example in the learner's route, "Compare
    # with the book's method" after a correct Submit and the logged draw
    # between passages that all passed the judge. Context, display and
    # learner picks; a comparison reaches evidence only through an existing
    # reveal kind on the item, so no scoring, scheduling, projection or
    # serving change and no successor; they act at every version and add no
    # route. Every snapshot moves only because the effective config gains the
    # keys; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # UX Phase 2 (the shell; docs/specs/ux_learnloop_v1.md §5, §10 2.1-2.5,
    # Q17; docs/reviews/ux-phase2.md) adds [ui] shell = "simple" (modelled
    # default, left out of the decision-only template), the kill switch of
    # the four-place shell, Under the hood, the notice system and the
    # palette's ">" prefix ("classic" keeps the ten-tab shell exactly).
    # Display only: the desktop reads it, and no grading, scheduling,
    # evidence, projection or replay path does, so no successor (the owner's
    # live-behind-kill-switches ruling). Every snapshot moves only because
    # the effective config gains the key; all of them were recomputed from
    # the composed defaults (defaults_fingerprint_for_version).
    # Plan-first transport T1 (docs/reviews/ai-plan-first-transport-t1.md;
    # owner decisions 2026-10-21) moves every snapshot: the code-default
    # ChatGPT-plan profiles chatgpt, chatgpt_low, chatgpt_medium and
    # chatgpt_luna, ai.active_provider = "chatgpt" and the tiered routes on
    # them (the decision-only template too), ai.agent_harness_opt_in =
    # false (Codex refused for serving, never a fallback),
    # ai.plan_fallback_profile = "openrouter" (asked, never automatic) and
    # the plan's workspace_mode = "inline". The served model changes (Codex
    # to the plan's models, owner-approved); prompts, parsing, scoring,
    # scheduling, projections and replayed meaning do not, so no successor;
    # it acts at every version. All snapshots were recomputed from the
    # composed defaults (defaults_fingerprint_for_version).
    # Reader workbench RW5b (more figure kinds and offered figures;
    # docs/reviews/reader-workbench-RW5b.md) adds [figures]
    # advanced_panels_enabled and offers_enabled (true; modelled defaults,
    # left out of the decision-only template): heat maps, vector fields,
    # trajectories and iterated maps in the figure grammar, and "make this
    # explorable" judged by the library organizer and the Reader tutor in the
    # calls they already make. Content and display: no scoring, scheduling,
    # projection or serving change and no successor; they act at every
    # version and add no route. Every snapshot moves only because the
    # effective config gains the keys; all of them were recomputed from the
    # composed defaults (defaults_fingerprint_for_version).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d (workbench signals in the learner field;
    # docs/reviews/reader-workbench-RW2d.md) adds [workbench]
    # field_signals_enabled (true; a modelled default, left out of the
    # decision-only template): the kill switch of its successor. It acts only
    # at that tag and later; at every earlier version the key is present and
    # inert. Every snapshot moves only because the effective config gains the
    # key; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # Local contextual retrieval P1 (spec_local_contextual_retrieval_v1; docs/reviews/
    # retrieval-local-p1.md) adds [embedding.local] (enabled = false until the owner runs
    # `learnloop embeddings local setup`), [embedding.fallback] (the Voyage space, enabled =
    # false, $1 per run keep cap) and [embedding.source_space] (default qwen, learned_fusion and
    # exploration off): modelled defaults only, left out of the decision-only template. With
    # them at their defaults retrieval is exactly today's (no scoring, scheduling, projection
    # or serving change); every snapshot moves only because the effective config gains them.
    # Teacher TE0 (spec_teacher_v1 §15.2; docs/reviews/teacher-te0-codex-review.md F5) adds
    # [teacher] confidence_events_enabled (true; a modelled default, left out of the
    # decision-only template): the kill switch of the confidence events in the router card,
    # the history-aware diagnoser, the hint writer and the tutor. Context only, at every
    # version (no successor); every snapshot moves only because the effective config gains
    # the key; all of them were recomputed from the composed defaults
    # (defaults_fingerprint_for_version).
    # LP-min (a), the claim fixes (spec_learned_parameters_v1 §3.0b item 1;
    # docs/reviews/lp-min-claim-fixes.md), adds [mastery] claim_fixes_enabled
    # (true; a modelled default, left out of the decision-only template): the
    # one kill switch of its successor. It acts only at that tag and later; at
    # every earlier version the key is present and inert. Every snapshot moves
    # only because the effective config gains the key; all of them were
    # recomputed from the composed defaults (defaults_fingerprint_for_version).
    "mvp-0.9": "fed0b5bdb62dd7397dfb401bd549823e82c7fb078865550a89c377f5764f898b",
    # mvp-0.10 (Slice 1 M2): the same effective defaults with the split live:
    # blind grading, the asynchronous diagnoser (history_mode = "full", O16),
    # the diagnosis card and PF-c grading support. Reached by
    # `learnloop upgrade --to mvp-0.10`; the template stays at mvp-0.9 until
    # the S1.5 exit review. Computed from DEFAULT_CONFIG_TEXT with only
    # algorithm_version changed. Slice 2 T5's [graph_nomination] moves it
    # too (modelled defaults, nominations only; no serving change).
    # Phase 5a's [pf] section and routes move it too (no serving change).
    # Router R0's merge moves it too (see mvp-0.9; no serving change).
    # Slice 2 T1's merge moves it too (see mvp-0.9; no serving change).
    # Slice 2 T6's merge moves it too (see mvp-0.9; no serving change).
    # The stuck prompt's merge moves it too (see mvp-0.9; no serving change).
    # DL1's merge moves it too (see mvp-0.9; no serving change).
    # Owner batch 2's recurrence.require_guard moves it too (see mvp-0.9).
    # Router R1's [router] section moves it too (see mvp-0.9).
    # Learner-text gaps' [learner_text_gaps] moves it too (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.10": "dc2fbfdffa2e73540964a6c2e472b31a786896e62596e89199279ae33bbb1fac",
    # mvp-0.11 (Slice A Phase 6, learner field F2): mvp-0.10's split plus
    # placement (the [placement] section, modelled defaults only, left out of
    # the decision-only template): no opening probes, assumed-known checked in
    # the first review, the optional quick check. Kill switch
    # placement.enabled. Reached by `learnloop upgrade --to mvp-0.11` from
    # mvp-0.10, or from mvp-0.9 through mvp-0.10. [placement] is dormant below
    # mvp-0.11, so the mvp-0.9 and mvp-0.10 snapshots were recomputed at the
    # merge (they move only because the effective config gains the section).
    # All three were recomputed again at the Phase 5a merge for [pf] and the
    # two PF routes (content generation behind pf.generation_enabled, off).
    # Router R0's merge moves it too (see mvp-0.9; no serving change).
    # The owner's 2026-10-12 decisions amend mvp-0.11 in place (no vault had
    # reached it) without a default change: new
    # vaults started here (the template's LATEST_ALGORITHM_VERSION) until
    # mvp-0.12 merged, a first review or a lapse in maintenance is decided by
    # the diagnosis, and unanswered opening episodes are ignored under
    # placement.
    # Slice 2 T1's merge moves it too (see mvp-0.9; no serving change).
    # Slice 2 T6's merge moves it too (see mvp-0.9; no serving change).
    # The stuck prompt's merge moves it too (see mvp-0.9; no serving change).
    # DL1's merge moves it too (see mvp-0.9; no serving change).
    # Owner batch 2's recurrence.require_guard moves it too (see mvp-0.9).
    # Router R1's [router] section moves it too (see mvp-0.9).
    # Learner-text gaps' [learner_text_gaps] moves it too (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.11": "b95c1a50b4cd4b92fd95af4f8f2452b91ae8b2fff52188a44acd061456cc9791",
    # mvp-0.12 (Slice 2 T1 / M3): mvp-0.11's split and placement plus
    # recurrence groups live (recurrence.enabled, the live same-cause judge
    # with top_k 3 and no blocking cutoff until B3 sets one, the escalation
    # card and its escalated-repair request). T1 was built as mvp-0.11 and
    # relabelled when it merged after Phase 6. Existing vaults reach it by
    # `learnloop upgrade` (default target) from mvp-0.11, or from
    # mvp-0.9/mvp-0.10 through the chain, once the same-answer/different-cause
    # guard passes for the configured judge. New vaults start here (the
    # template's LATEST_ALGORITHM_VERSION; owner decision 2026-10-12) until
    # mvp-0.13 merged: their groups are active from the first answer, built
    # only from the judge's and the diagnoser's verdicts on their own history.
    # Slice 2 T6's merge moves it too (see mvp-0.9; no serving change).
    # The stuck prompt's merge moves it too (see mvp-0.9; no serving change).
    # DL1's merge moves it too (see mvp-0.9; no serving change).
    # Owner batch 2: the same-cause guard is advisory (recurrence.require_guard
    # = true restores the refusal); no serving change.
    # Router R1's [router] section moves it too (see mvp-0.9).
    # Learner-text gaps' [learner_text_gaps] moves it too (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.12": "82cc5b60e71b60c69e4c69092842af362733981c09339ed52d0b96fb2dd80f50",
    # mvp-0.13 ("Write what you can" replaces "I don't know"): mvp-0.12's
    # split, placement and recurrence groups plus "I'm stuck" live
    # (stuck_prompt.enabled = true): a stuck answer with text is an ordinary
    # attempt at the standard mass, graded under the +stuck-v1 prompt and
    # diagnosed; an empty one scores 0 with no model call and no error tag
    # (owner decision 2026-10-12, no default change). Built as mvp-0.11
    # and relabelled at its merge. Existing vaults reach it by `learnloop
    # upgrade --to mvp-0.13` from mvp-0.12, or from mvp-0.9 to mvp-0.11
    # through the chain (under mvp-0.12's guard). New vaults start here (the
    # template's LATEST_ALGORITHM_VERSION; owner decision 2026-10-12) until
    # mvp-0.14 merged. DL1's merge moves it too (see mvp-0.9; no serving
    # change). Router R1's [router] section moves it too (see mvp-0.9).
    # Learner-text gaps' [learner_text_gaps] moves it too (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.13": "382bc1587cac0186d9ae5f2ad3321471690e363a84d9a34d03560b1b6c6bd584",
    # mvp-0.14 (daily-loop DL1, daily_plan_v1): mvp-0.13's split, placement,
    # recurrence groups and stuck prompt plus the finite daily plan ([plan],
    # modelled defaults only): the system-set split, load-based new-material
    # admission, block-by-block choice through the §6.8 source/chooser seam,
    # goal-optional re-entry and reading blocks. Kill switch plan.enabled.
    # Built as mvp-0.12 and relabelled at its merge. Existing vaults reach it
    # by `learnloop upgrade` (default target) from mvp-0.13, or from mvp-0.9
    # to mvp-0.12 through the chain (under mvp-0.12's guard). New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.15 merged. Router R1's [router] section moves it
    # too (see mvp-0.9). Learner-text gaps' [learner_text_gaps] moves it too
    # (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.14": "4afafc8b62d280f9d4c6354003d2704c62980d4a21da0575be48cf43744bf65f",
    # mvp-0.15 (router R1): mvp-0.14's split, placement, recurrence groups,
    # stuck prompt and plan plus probe near-ties (teach-back items included,
    # owner decision D11) admitted to the Today queue's seeded exploration
    # with a logged propensity. Kill switch router.probe_tie_admission
    # (default on). Built as mvp-0.12 and relabelled at its merge. Existing
    # vaults reach it by `learnloop upgrade` (default target) from mvp-0.14, or
    # from mvp-0.9 to mvp-0.13 through the chain (under mvp-0.12's advisory
    # guard). New vaults started here (the template's LATEST_ALGORITHM_VERSION;
    # owner decision 2026-10-12) until mvp-0.16 merged. Learner-text gaps'
    # [learner_text_gaps] moves it too (see mvp-0.9).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.15": "a4ac890e2acfba7cc160cf64f96ac5bb4bee758322ace4740baa10265c2da51e",
    # mvp-0.16 (learner-text gaps, implementation_handoffs §4): mvp-0.15's
    # split, placement, recurrence groups, stuck prompt, plan and probe ties
    # plus the sooner check: a matched prerequisite gap on an LO assumed known
    # or in maintenance brings its next check forward (no sooner than
    # learner_text_gaps.sooner_check_delay_hours after the gap). Kill switch
    # learner_text_gaps.sooner_check_enabled. Built as mvp-0.13 and relabelled
    # at its merge. Existing vaults reach it by `learnloop upgrade` (default
    # target) from mvp-0.15, or from mvp-0.9 to mvp-0.14 through the chain
    # (under mvp-0.12's advisory guard). New vaults started here (the
    # template's LATEST_ALGORITHM_VERSION; owner decision 2026-10-12) until
    # mvp-0.17 merged. The rest of
    # [learner_text_gaps] (modelled defaults only, left out of the
    # decision-only template) and the unset learner_gap_judge /
    # learner_gap_reader / learner_gap_decider routes are live at every
    # version behind learner_text_gaps.enabled and their own switches (named
    # gaps, matches, "needed"-gated edges, created prerequisites as content,
    # holding-pen sightings, the gap targets the field loader reads).
    # Facet identity's [facet_identity], route and profiles move it too.
    # The T6 follow-up's output budgets and pool move it too (see mvp-0.9).
    # EVSI calibration's [evsi] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW1a's [reader_inquiry] moves it too (see mvp-0.9).
    # The route check's [proof_check] and route move it too (see mvp-0.9).
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.16": "2f984391184ce2bfa276c3e8e5d102c52af0aaeca3e7dbc388c75de4c4bf3e90",
    # mvp-0.17 (the proofs-and-explanations route check; built as mvp-0.15, a
    # placeholder tag, and relabelled at its merge): mvp-0.16's split,
    # placement, recurrence groups, stuck prompt, plan, probe ties and sooner
    # check plus the valid-alternative gate for proofs and explanations
    # (proof_check.enabled = true; ai.routing.proof_check unset = the first
    # configured route with a model other than the grader's): on an item an
    # LLM reads as proof-like, an independent re-derivation of the learner's
    # route restores a criterion marked down without a located error, records
    # one disputed on a located step unassessed, flags an accepted step it
    # refutes, and holds for review a grade with nothing assessed and nothing
    # validated. Existing vaults reach it by `learnloop upgrade --to mvp-0.17`
    # from mvp-0.16, or from mvp-0.9 to mvp-0.15 through the chain (under
    # mvp-0.12's advisory guard). New vaults started here (the template's
    # LATEST_ALGORITHM_VERSION; owner decision 2026-10-12) until mvp-0.18
    # merged.
    # Canonical sources' [source_service] and routes move it too (see mvp-0.9).
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader (owner decision 2026-10-13) removed the separate
    # check from serving: an mvp-0.17 vault grades new answers as its kill
    # switch defined (as mvp-0.16), and the retired route moves it too (see
    # mvp-0.9).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.17": "d373ca8a542cb56a0a683e66689bd3307e95bde0f8ce70be8d445fb78aab9f75",
    # mvp-0.18 (canonical sources S1, the certification gate C3; built as
    # mvp-0.15, a placeholder tag, and relabelled at its merge): mvp-0.17
    # plus practice_attempts.reference_status. An attempt on an imported
    # textbook exercise whose answer key is not verified (book_solution,
    # checked or panel_agrees, bound to the stem, key and rubric checked)
    # records reference_status = unverified: FSRS updates, certification
    # credit does not (exam pools and certification cold probes skip
    # unverified imports). No switch turns the gate off; it is versioned by
    # this tag. Existing vaults reach it by `learnloop upgrade --to mvp-0.18`
    # from mvp-0.17, or from mvp-0.9 to mvp-0.16 through the chain (under
    # mvp-0.12's advisory guard); never retroactive.
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9; the
    # separate check no longer runs here either).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.18": "775b69e2c0f0b2410d3d280079b03f9ef206697ea0241da4c9699973d37a2d62",
    # mvp-0.19 (canonical sources S2b; built as mvp-0.16, a placeholder tag,
    # and relabelled at its merge): mvp-0.18 plus source-first fulfilment of
    # intervention needs: the primed-retry handler and `learnloop
    # generate-diagnostics` try the learner's textbook exercises (key-checked,
    # validated and, for discriminate, through the follow-up chooser's own
    # gate) before generating. Kill switch source_service.source_first_needs
    # (off: the generation lane is byte-identical). Existing vaults reach it
    # by `learnloop upgrade --to mvp-0.19` from mvp-0.18, or from mvp-0.9 to
    # mvp-0.17 through the chain (under mvp-0.12's advisory guard). New
    # vaults started here (the template's LATEST_ALGORITHM_VERSION) until
    # mvp-0.20 merged.
    # The reword confirm's facet_identity.reword_confirm moves it too (see mvp-0.9).
    # UX Phase 1's [ingest] keys, [ai] consent and reading step move it too (see mvp-0.9).
    # route-check-in-grader's retired route moves it too (see mvp-0.9; the
    # separate check no longer runs here either).
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.19": "e8b55b0fab9debd2fa8ea316b35861326fff85a731fcebcb2b82383ccbecbe20",
    # mvp-0.20 (route rules in the grader, route-check-in-grader; built as
    # mvp-0.18, a placeholder tag, and relabelled at its merge after the
    # sources track): mvp-0.19 plus the own-route rules in the blind grader's
    # prompt and the server-side unlocated rule (a mark-down on a divergent
    # route that quotes nothing is unassessed; a grade with nothing assessed
    # and nothing validated is held for review), in one grading call. Kill
    # switch proof_check.enabled (default on). Existing vaults reach it by
    # `learnloop upgrade` (default target) from mvp-0.19, or from mvp-0.9 to
    # mvp-0.18 through the chain (under mvp-0.12's advisory guard). New
    # vaults started here (the template's LATEST_ALGORITHM_VERSION; owner
    # decision 2026-10-12) until mvp-0.21 merged.
    # Value-of-information stopping's [voi_stopping] and probe-lane keys move
    # it too (see mvp-0.9; dormant below mvp-0.21).
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.20": "31bb6e5eda48f04b5b909eada0080d48aee8e4180e4e73c4c82828264572264b",
    # mvp-0.21 (value-of-information stopping, owner-directed 2026-10-12/13;
    # built as mvp-0.17, a placeholder tag, and relabelled at its merge after
    # the route rules): mvp-0.20 plus Part 1, four count caps lifted onto
    # value of information (probe observations per session, further follow-ups
    # per LO per session, further teach-backs per queue, due project probes per
    # day: each served while its value pays for its minutes; kill switch
    # voi_stopping.enabled, a sub-switch per site), and Part 2, the probe
    # hypothesis lane reading the diagnoser's verdict through the diagnosis
    # overlay and holding out a pending diagnosis (kill switch
    # diagnosis.probe_lane_reads_diagnosis; diagnosis.probe_lane_pending =
    # "hold_out"). No new constants: the value rule reads robust_composition's
    # heuristic decision parameters. voi-v2: the value rule also reads the
    # multi-family EVSI study's switches, at its recommendations (the robust
    # completion gate does not end a value-decided episode, a 2-3 check
    # lookahead at probe episodes, the value gate's robust quantile 0.25);
    # true / 1 / 0.10 restore the successor as it was before the study.
    # evsi.measured_loss_enabled (default off) also reaches its loss table at
    # the merge (rank 4). Existing vaults reach it by `learnloop upgrade`
    # (default target) from mvp-0.20, or from mvp-0.9 to mvp-0.19 through the
    # chain (under mvp-0.12's advisory guard). New vaults started here (the
    # template's LATEST_ALGORITHM_VERSION; owner decision 2026-10-12) until
    # mvp-0.22 merged.
    # Tier 1's [decider_routes] and route move it too (see mvp-0.9; dormant below mvp-0.22).
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.21": "9e92140e981d31b9ca4d2097021b082250112660e92c2b9c0c63ee1cbebf9913",
    # mvp-0.22 (Tier 1, the Decider migration, owner decision 2026-10-13;
    # built as mvp-0.20, a placeholder tag, and relabelled at its merge after
    # the route rules and value-of-information stopping): mvp-0.21 plus the
    # Decider deciding the small judgments [decider_routes] names
    # (learner-text gap pairs, "needed?" and kind; misconception match; the
    # review's pattern links; field question classification; the
    # contamination report's leak and reveal verdicts), each with its LLM as
    # fallback when the Decider is unavailable, refused for spend, failing or
    # tied, and its own kill switch (false: that judgment's mvp-0.21 path). It
    # changes what is served from now on (gaps created, misconceptions
    # matched, links), never the meaning of recorded history. Existing vaults
    # reach it by `learnloop upgrade` (default target) from mvp-0.21, or from
    # mvp-0.9 to mvp-0.20 through the chain (under mvp-0.12's advisory
    # guard). New vaults started here (the template's LATEST_ALGORITHM_VERSION;
    # owner decision 2026-10-12) until mvp-0.23 merged.
    # Exam protection's goals.held_out_selection moves it too (see mvp-0.9).
    # Router R2a's [router] keys and RW3a's [cues] move it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.22": "50eab1e9819f8f856c1515faf3572a989855b3a3a3f51dd95776ea43e53df059",
    # mvp-0.23 (router R2a, owner-directed 2026-10-13; a placeholder tag that
    # kept its label at its merge, nothing on main having taken it): mvp-0.22
    # plus Today composed by the staged frame (DL1's lanes and lane_quota_v1
    # over the set the P4 constraint engine admits: a block loses only the
    # items a named hard constraint refuses, its order unchanged) and
    # golden_path.advance through the P2 bridge (D13). Kill switch
    # router.enabled (off: mvp-0.22's serving exactly). Existing vaults reach
    # it by `learnloop upgrade` (default target) from mvp-0.22, or from
    # mvp-0.9 to mvp-0.21 through the chain (under mvp-0.12's advisory guard).
    # New vaults started here (the template's LATEST_ALGORITHM_VERSION; owner
    # decision 2026-10-12) until mvp-0.24 merged.
    # Reader workbench RW3a's [cues] moves it too (see mvp-0.9).
    # Tutor delivery fixes' tutor_qa, source_retrieval and embedding keys move it too (see mvp-0.9).
    # GLM-OCR's [ingest.pdf.glm_ocr] moves it too (see mvp-0.9).
    # Router R2b + R2c's [router] keys move it too (see mvp-0.9; dormant below mvp-0.24).
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.23": "1230bd81986a57ff20a1d8b2a97cdc582bceb51709223f0002aea3501d0ac32a",
    # mvp-0.24 (router R2b + R2c, owner decisions 2026-10-13; a placeholder
    # tag that kept its label at its merge, nothing on main having taken it):
    # mvp-0.23 plus Today's next block drawn from the logged model mixture
    # (the staged rule, the Decider and the router LLM over the top-k
    # reversible candidates, exact propensities, a floor for each) and
    # mid-block follow-ups decided by the restraint (plan_interrupt). Kill
    # switches router.mode = "staged" (mvp-0.23's serving exactly) and
    # router.restraint = false. Existing vaults reach it
    # by `learnloop upgrade` (default target) from mvp-0.23, or from mvp-0.9 to
    # mvp-0.22 through the chain (under mvp-0.12's advisory guard). New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.25 merged.
    # Plan determinism's plan.deterministic_staged_plans moves it too (see mvp-0.9).
    # The method-explicit [required_method], route and Decider switch move it too (see mvp-0.9).
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.24": "306fb83a6430e5a19f4d484d48c643a184cac13b3fe1183747b7f32a0b34aa78",
    # mvp-0.25 (method-explicit items, owner rule 2026-10-13; built as
    # mvp-0.22-placeholder, a placeholder tag, and relabelled at its merge
    # after router R2b + R2c): mvp-0.24 plus required-method grading
    # (own-route-v2: a criterion tied to an item's required method, frozen with
    # its assessment contract, is graded on use of that method, so another
    # route fails it with no quoted wrong step; every other criterion keeps
    # the own-route rules). Kill switch required_method.enabled (default on;
    # off grades new answers exactly as mvp-0.24). Existing vaults reach it by
    # `learnloop upgrade` (default target) from mvp-0.24, or from mvp-0.9 to
    # mvp-0.23 through the chain (under mvp-0.12's advisory guard). New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.26 merged.
    # Saved diagnosis forecasts' diagnosis.forecast_receipts moves it too (see mvp-0.9).
    # UX Phase 4's [ui] practice_feedback moves it too (see mvp-0.9).
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.25": "3b805e634ff9acfda69fa51ea6c1fb9d2b77d2620659db300362b28d935ddbb4",
    # mvp-0.26 (regrade contracts, queued 2026-10-16;
    # docs/reviews/regrade-contract-replay.md): mvp-0.25 plus every regrade
    # citing the assessment contract it graded against (a snapshot of the item
    # it read, or the frozen method contract), as the attempt's next grading
    # revision superseding every live row, and replay reading the current
    # grading epoch's own contract (a current epoch citing none, written
    # before the tag, is held for review rather than read against today's
    # item). No config key and no default changes: only the version string
    # moves the fingerprint. No kill switch. Existing vaults reach it by
    # `learnloop upgrade` (default target) from mvp-0.25, or from mvp-0.9 to
    # mvp-0.24 through the chain (under mvp-0.12's advisory guard). New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.27 merged.
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.26": "205a3bcdf4577340fb012a6dfcd4f590e5c8de864034f8731c9b4a6b0eb61853",
    # mvp-0.27 (one serve/administration eligibility decision, queued
    # 2026-10-16; docs/reviews/serve-eligibility-decision.md and its Codex
    # review F4): mvp-0.26 plus every serve path asking the decision submit
    # asks (an item submit would prime is never served as a cold check, a
    # probe or a quick-check offer; a cold check its item can no longer take
    # cold is withdrawn with its typed disposition and the item served as
    # practice) and historical writers bounding their auto-prime window at
    # their own instant. Kill switch [eligibility] enabled (default true; off
    # serves and admits exactly as mvp-0.26). Existing vaults reach it by
    # `learnloop upgrade` (default target) from mvp-0.26, or from mvp-0.9 to
    # mvp-0.25 through the chain (under mvp-0.12's advisory guard). New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.29 merged.
    # Reader workbench RW2a's [workbench] moves it too (see mvp-0.9).
    # Reader workbench RW6a's [recap] moves it too (see mvp-0.9).
    # Reader workbench RW1b's [reader_intent] and its two sections move it too (see mvp-0.9).
    # Reader workbench RW4a's [library_ask], [reader_compare] and route move it too (see mvp-0.9).
    # Adaptive hints H0's [hints] telemetry_enabled moves it too (see mvp-0.9; no serving change).
    # Adaptive hints H1's [hints.maps], hints.price_per_million and route move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2a's [hints] service keys and two routes move it too (see mvp-0.9; no serving change).
    # Adaptive hints H2b's [hints] panel and outcome-placement keys and route move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD1's [adaptive_difficulty], its Decider switch and three routes move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2b + adaptive hints H3's [workbench] help keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW1c's [reader_tutor] moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4b's [library_exercises] moves it too (see mvp-0.9; no serving change).
    # Daily-loop DL2's [intent] and [capture] move it too (see mvp-0.9; inert below mvp-0.29).
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.27": "4b0ba991e197744e697fc3279481254f9822fbd2f0c5349a946e2519758bbfde",
    # mvp-0.29 (daily-loop DL2, the learner's intent; docs/reviews/
    # daily-loop-dl2.md and its Codex re-review F2): the predecessor plus
    # serving by intent (an excluded item is never served, requested or
    # rebuilt as a follow-up; a "Check once" is a cold check on your own;
    # effective dues at the recall targets, push, admission, re-entry and
    # reading by intent). Kill switch [intent] enabled (default true; off
    # serves exactly as the predecessor). No default changes here: only the
    # version string moves the fingerprint ([intent] and [capture] are in
    # every snapshot above, inert below the tag). Its predecessor is
    # mvp-0.27: DL2 landed on main before adaptive difficulty AD2+AD3, so
    # mvp-0.28 is never used on main and AD2+AD3 lands as mvp-0.30 after it.
    # Existing vaults reach it by `learnloop upgrade` (default target) from
    # the predecessor, or from mvp-0.9 onwards through the chain. New vaults
    # started here (the template's LATEST_ALGORITHM_VERSION; owner decision
    # 2026-10-12) until mvp-0.30 merged.
    # Reader workbench RW3b's [cues] discovery keys and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW4d's [reader_compare] keep_enabled moves it too (see mvp-0.9; no serving change).
    # Reader workbench RW4e's [roles] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW7a's [reading_paths] and route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW5a's [figures] and its route move it too (see mvp-0.9; no serving change).
    # Reader workbench RW2c's [workbench] help-outcome, example, compare and draw switches move it too (see mvp-0.9; no serving change).
    # UX Phase 2's [ui] shell moves it too (see mvp-0.9; display only).
    # Plan-first transport T1's ChatGPT-plan defaults move it too (see mvp-0.9; the served model changes, no successor).
    # Reader workbench RW5b's [figures] advanced_panels_enabled and offers_enabled move it too (see mvp-0.9; no serving change).
    # Adaptive difficulty AD2+AD3's [adaptive_difficulty] switches and constants, and its routes on the plan's tiers (T1), move it too (see mvp-0.30; dormant below it).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.29": "c909aa0243030e40d3dcdecb40668ef2f5731ac64fc5b039baf34ba77599fbde",
    # mvp-0.30 (adaptive difficulty AD2+AD3, owner 2026-10-18;
    # docs/reviews/adaptive-difficulty-ad23.md): mvp-0.29 plus AD's draw at a
    # planned new-material slot (practice in the 70-80% band, calibration within
    # acceptable difficulty, exact logged propensities; an empty support defers
    # the slot's item), the generation contract (an item AT a commissioned
    # feature point, no difficulty band), and the subject view (learned
    # relatedness, reading, the self-check verdict term) for live decisions and
    # the readiness numbers. Six kill switches under [adaptive_difficulty]
    # (selection, generation_contract, promoted_predictor, learned_coupling,
    # reading_opportunities, reading_self_check), each restoring its part of
    # mvp-0.29 exactly; the Reader's dose offers (reading_dose_offers) ship beside
    # it with no tag. Modelled defaults, left out of the decision-only template.
    # Owner decisions 2026-10-19: learned_coupling off until the owner adopts a
    # coupling version, calibrate_below 0.25 (amendment A17), and AD's own
    # history_fallback = "current_content" (field.legacy_fallback unchanged).
    # Existing vaults reach it by `learnloop upgrade` (default target) from
    # mvp-0.29, or from mvp-0.9 onwards through the chain (mvp-0.28 is never
    # used: AD2+AD3 lands after DL2, orchestrator decision 2026-10-20). New vaults start
    # here until mvp-0.31 landed (the template's LATEST_ALGORITHM_VERSION).
    # Reader workbench RW2d's [workbench] field_signals_enabled moves it too (see mvp-0.9; inert below mvp-0.31).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.30": "0a48c029551b3402ec483e580e408a3bd53f37ac1494afa5edf1a203f21abef6",
    # mvp-0.31 (reader workbench RW2d, workbench signals in the learner
    # field; spec_reader_workbench_v1 §5.11, docs/reviews/
    # reader-workbench-RW2d.md; chained after adaptive difficulty AD2+AD3's
    # mvp-0.30 at its landing): mvp-0.30 plus two zero-mass field
    # signals from the workbench (a mid-work stuck step with text, help
    # before the first step) that keep an LO out of fast-track and teach it
    # first, with receipts of what the predecessor would have decided. Kill
    # switch [workbench] field_signals_enabled (default true; off derives,
    # serves and plans exactly as the predecessor). No default changes here:
    # only the version string moves the fingerprint (the key is in every
    # snapshot above, inert below the tag). Existing vaults reach it by
    # `learnloop upgrade` from mvp-0.30, or from mvp-0.9 onwards through
    # the chain. New vaults started here until LP-min (a)'s successor
    # landed (the template's LATEST_ALGORITHM_VERSION).
    # Local contextual retrieval P1's [embedding.local], [embedding.fallback] and [embedding.source_space] move it too (see mvp-0.9; off or at the seed: no serving change).
    # Teacher TE0's [teacher] confidence_events_enabled moves it too (see mvp-0.9; context only, no successor).
    # LP-min (a)'s [mastery] claim_fixes_enabled moves it too (see mvp-0.9; inert below mvp-0.32).
    "mvp-0.31": "19edbbb8ac905a72ad0083320353a515129528ab01c73da7fdf02627ba7cea23",
    # mvp-0.32 (learned parameters LP-min (a), the four claim-defect fixes;
    # spec_learned_parameters_v1 §3.0b item 1, docs/reviews/lp-min-claim-fixes.md;
    # built beside reader workbench RW7b's successor, renumbered at landing):
    # mvp-0.31 plus tutor gap declarations re-anchoring mastery, claims replayed
    # at their own time, a mean-only warm claim merge and recency-first claim
    # ties. Kill switch [mastery] claim_fixes_enabled (default true; off seeds,
    # re-anchors, merges, ranks and replays exactly as the predecessor). No
    # default changes here: only the version string moves the fingerprint (the
    # key is in every snapshot above, inert below the tag). Existing vaults
    # reach it by `learnloop upgrade` (default target) from mvp-0.31, or from
    # mvp-0.9 onwards through the chain. New vaults start here (the template's
    # LATEST_ALGORITHM_VERSION; owner decision 2026-10-12).
    "mvp-0.32": "c555098a34da908786360d7982841b62ab62321f07849c90cfb6aee690083031",
}


def write_default_config(path: Path) -> None:
    """Write the decision-only template without replacing an existing file."""

    if path.exists():
        return
    path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")


def effective_defaults_fingerprint(
    config: LearnLoopConfig | None = None,
) -> str:
    """Content address of the complete effective defaults for a new vault.

    The snapshot is keyed by ``algorithm_version`` in CI. A deliberate policy
    default change therefore requires an explicit version/snapshot decision,
    rather than silently changing every minimal-config vault.
    """

    if config is None:
        from learnloop.config.schema import LearnLoopConfig

        config = LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT))
    payload = json.dumps(
        config.model_dump(mode="json", exclude_none=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def defaults_fingerprint_for_version(algorithm_version: str) -> str:
    """The effective-defaults fingerprint of a new vault at ``algorithm_version``.

    The template rendered at that version (:func:`default_config_text`), so a
    recorded snapshot is recomputed the same way after the template moves on.
    """

    from learnloop.config.schema import LearnLoopConfig

    config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(algorithm_version)))
    return effective_defaults_fingerprint(config)


__all__ = [
    "DEFAULT_CONFIG_TEXT",
    "DEFAULTS_SNAPSHOT_BY_ALGORITHM",
    "LEGACY_DEFAULT_CONFIG_TEXT",
    "default_config_text",
    "defaults_fingerprint_for_version",
    "effective_defaults_fingerprint",
    "write_default_config",
]
