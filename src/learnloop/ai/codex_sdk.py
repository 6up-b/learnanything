from __future__ import annotations

from pathlib import Path

from learnloop.config import AIProviderConfig, CodexConfig
from learnloop.codex.client import HttpCodexClient, SdkCodexClient


def codex_config_from_ai_profile(profile: AIProviderConfig) -> CodexConfig:
    provider = "http" if profile.type in {"http", "http_adapter"} else "sdk"
    return CodexConfig(
        provider=provider,
        # Left blank when unset so the runtime check surfaces a clear
        # "configure LEARNLOOP_CODEX_CHECKOUT_PATH" message instead of silently
        # resolving a stale relative default.
        checkout_path=profile.checkout_path or "",
        revision=profile.revision or "<pinned-commit>",
        startup_command=profile.startup_command or "",
        startup_timeout_seconds=profile.startup_timeout_seconds or 20,
        healthcheck_timeout_seconds=profile.healthcheck_timeout_seconds or profile.timeout_seconds or 5,
        auth_mode=profile.auth_mode or "chatgpt",
        model=profile.model or "gpt-5.6-sol",
        reasoning_effort=profile.reasoning_effort or "low",
        reasoning_summary=profile.reasoning_summary or "none",
        sdk_python_path=profile.sdk_python_path or "sdk/python/src",
        sdk_codex_bin=profile.sdk_codex_bin or "",
        sdk_launch_command=profile.sdk_launch_command or "",
        base_url=profile.base_url or "http://127.0.0.1:8765",
        healthcheck_path=profile.healthcheck_path or "/health",
        authoring_path=profile.authoring_path or "/authoring-proposal",
        canonical_ingest_path=profile.canonical_ingest_path or "/canonical-ingest",
        grading_path=profile.grading_path or "/grading-proposal",
        tutor_qa_path=profile.tutor_qa_path or "/tutor-qa",
        teach_back_path=profile.teach_back_path or "/teach-back",
    )


class CodexSDKProviderClient(SdkCodexClient):
    provider_type = "codex_sdk"

    def __init__(self, provider_name: str, profile: AIProviderConfig, vault_root: Path):
        self.provider_name = provider_name
        self.model = profile.model
        super().__init__(codex_config_from_ai_profile(profile), vault_root)


class HttpAdapterProviderClient(HttpCodexClient):
    provider_type = "http_adapter"

    def __init__(self, provider_name: str, profile: AIProviderConfig):
        self.provider_name = provider_name
        self.model = profile.model
        super().__init__(codex_config_from_ai_profile(profile))
