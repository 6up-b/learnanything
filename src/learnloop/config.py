from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_CONFIG_TEXT = """schema_version = 1

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.1"

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
tau_followup_nats = 0.3
gamma_min = 0.5

[mastery]
base_observation_variance = 1.0
sigma2_drift = 0.01
p_max = 4.0

[probe]
attempts_target_default = 3
attempts_target_with_strong_claim = 1
claim_skip_threshold = 0.75
variance_convergence_threshold = 0.10
hypothesis_set_max_size = 5

[codex]
checkout_path = "../codex"
revision = "<pinned-commit>"
startup_command = "npm run app-server"
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
base_url = "http://127.0.0.1:8765"
healthcheck_path = "/health"
authoring_path = "/authoring-proposal"
grading_path = "/grading-proposal"
"""


class StorageConfig(BaseModel):
    sqlite_path: str = "state.sqlite"


class AlgorithmsConfig(BaseModel):
    algorithm_version: str = "mvp-0.1"


class SchedulerSurpriseConfig(BaseModel):
    theta_pos: float = 1.5
    theta_neg: float = 1.5
    alpha_interval: float = 0.3
    f_min: float = 0.5
    f_max: float = 1.5
    epsilon_error_surprise: float = 0.05


class SchedulerFollowupConfig(BaseModel):
    tau_followup_nats: float = 0.3
    gamma_min: float = 0.5


class SchedulerConfig(BaseModel):
    forgetting_risk_weight: float = 1.0
    active_goal_weight: float = 0.35
    recent_error_weight: float = 0.50
    probe_eig_weight: float = 0.25
    short_session_minutes: int = 20
    surprise: SchedulerSurpriseConfig = Field(default_factory=SchedulerSurpriseConfig)
    followup: SchedulerFollowupConfig = Field(default_factory=SchedulerFollowupConfig)


class MasteryConfig(BaseModel):
    base_observation_variance: float = 1.0
    sigma2_drift: float = 0.01
    p_max: float = 4.0


class ProbeConfig(BaseModel):
    attempts_target_default: int = 3
    attempts_target_with_strong_claim: int = 1
    claim_skip_threshold: float = 0.75
    variance_convergence_threshold: float = 0.10
    hypothesis_set_max_size: int = 5


class CodexConfig(BaseModel):
    checkout_path: str = "../codex"
    revision: str = "<pinned-commit>"
    startup_command: str = "npm run app-server"
    startup_timeout_seconds: int = 20
    healthcheck_timeout_seconds: int = 5
    auth_mode: str = "chatgpt"
    base_url: str = "http://127.0.0.1:8765"
    healthcheck_path: str = "/health"
    authoring_path: str = "/authoring-proposal"
    grading_path: str = "/grading-proposal"


class LearnLoopConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    storage: StorageConfig = Field(default_factory=StorageConfig)
    algorithms: AlgorithmsConfig = Field(default_factory=AlgorithmsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    mastery: MasteryConfig = Field(default_factory=MasteryConfig)
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)


def load_config(path: Path) -> LearnLoopConfig:
    with path.open("rb") as handle:
        return LearnLoopConfig.model_validate(tomllib.load(handle))


def write_default_config(path: Path) -> None:
    if path.exists():
        return
    path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
