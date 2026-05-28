from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_CONFIG_TEXT = """schema_version = 1

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.2"

[scheduler]
forgetting_risk_weight = 1.0
active_goal_weight = 0.35
recent_error_weight = 0.50
probe_eig_weight = 0.25
short_session_minutes = 20

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

[mastery]
base_observation_variance = 1.0
sigma2_drift = 0.01
p_max = 4.0

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

[probe]
attempts_target_default = 3
attempts_target_with_strong_claim = 1
claim_skip_threshold = 0.75
variance_convergence_threshold = 0.10
hypothesis_set_max_size = 5

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

[ingest]
window_char_cap = 150000
min_content_chars = 400
default_goal_priority = 0.5
allow_auto_captions = false

[ai]
active_provider = "codex"
fallback_provider = ""
timeout_seconds = 60

[ai.routing]
grading = "codex"
canonical_ingest = "codex"
canonical_ingest_retry = ""
authoring = "codex"

[ai.providers.codex]
type = "codex_sdk"
model = "gpt-5.5"
checkout_path = "../codex"
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

[codex]
provider = "sdk"
checkout_path = "../codex"
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

# Cross-LO propagation gates per error type (spec §"Error-type gate").
[cross_lo_propagation.default]
max_depth = 3
hop_decay = 0.5
total_propagated_weight_cap = 0.7

[cross_lo_propagation.error_gates.recall_failure]
mean_factor = 0.0          # forgetting a definition is not evidence prereqs are weak
variance_factor = 0.25
scope = "all"

[cross_lo_propagation.error_gates.scaffold_failure]
mean_factor = 0.0
variance_factor = 0.35
scope = "all"

[cross_lo_propagation.error_gates.arithmetic_slip]
mean_factor = 0.0
variance_factor = 0.10
scope = "all"

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
    algorithm_version: str = "mvp-0.2"


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


class SchedulerConfig(BaseModel):
    forgetting_risk_weight: float = 1.0
    active_goal_weight: float = 0.35
    recent_error_weight: float = 0.50
    probe_eig_weight: float = 0.25
    short_session_minutes: int = 20
    candidate_log_retention_limit: int = 200
    selection_exploration_rate: float = 0.0
    selection_exploration_reward_window: float = 0.15
    surprise: SchedulerSurpriseConfig = Field(default_factory=SchedulerSurpriseConfig)
    followup: SchedulerFollowupConfig = Field(default_factory=SchedulerFollowupConfig)


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
    irt: MasteryIRTConfig = Field(default_factory=MasteryIRTConfig)


class ProbeConfig(BaseModel):
    attempts_target_default: int = 3
    attempts_target_with_strong_claim: int = 1
    claim_skip_threshold: float = 0.75
    variance_convergence_threshold: float = 0.10
    hypothesis_set_max_size: int = 5
    irt: ProbeIRTConfig = Field(default_factory=ProbeIRTConfig)
    self_tag: ProbeSelfTagConfig = Field(default_factory=ProbeSelfTagConfig)


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
    severity_examples: dict[str, SeverityExampleConfig] = Field(default_factory=default_severity_examples)


class IngestConfig(BaseModel):
    window_char_cap: int = 150000
    min_content_chars: int = 400
    default_goal_priority: float = 0.5
    allow_auto_captions: bool = False


class CodexConfig(BaseModel):
    provider: str = "sdk"
    checkout_path: str = "../codex"
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


class AIRoutingConfig(BaseModel):
    grading: str | None = None
    canonical_ingest: str | None = None
    canonical_ingest_retry: str | None = None
    authoring: str | None = None


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
    default: CrossLoPropagationDefaults = Field(default_factory=CrossLoPropagationDefaults)
    error_gates: dict[str, ErrorGate] = Field(default_factory=dict)


class LearnLoopConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    storage: StorageConfig = Field(default_factory=StorageConfig)
    algorithms: AlgorithmsConfig = Field(default_factory=AlgorithmsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    mastery: MasteryConfig = Field(default_factory=MasteryConfig)
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    recall_coverage: RecallCoverageConfig = Field(default_factory=RecallCoverageConfig)
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)
    error_impacts: dict[str, ErrorImpact] = Field(default_factory=dict)
    cross_lo_propagation: CrossLoPropagationConfig = Field(default_factory=CrossLoPropagationConfig)

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
        self.cross_lo_propagation.error_gates.setdefault(
            "recall_failure",
            ErrorGate(mean_factor=0.0, variance_factor=0.25, scope="all"),
        )
        self.cross_lo_propagation.error_gates.setdefault(
            "scaffold_failure",
            ErrorGate(mean_factor=0.0, variance_factor=0.35, scope="all"),
        )
        self.cross_lo_propagation.error_gates.setdefault(
            "arithmetic_slip",
            ErrorGate(mean_factor=0.0, variance_factor=0.10, scope="all"),
        )
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


_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ConfigLoadError(ValueError):
    def __init__(self, path: Path, message: str):
        self.path = path
        super().__init__(message)


def load_config(path: Path) -> LearnLoopConfig:
    load_dotenv(path.parent / ".env")
    try:
        with path.open("rb") as handle:
            return LearnLoopConfig.model_validate(tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLoadError(path, _format_toml_error(path, exc)) from exc


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
