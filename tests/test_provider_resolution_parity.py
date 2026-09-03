from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import learnloop.ai.routing as routing
import pytest
from learnloop.ai.client import make_ai_provider_client_from_profile
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.providers.codex_http import HttpCodexClient
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.routing import MANUAL_PROVIDER, ROUTE_FOR_OPERATION, ready_client_for_task
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.diagnosis.ai_contracts import DiagnosticFireJudgment
from learnloop.ai.transport import (
    MEDIA_MARKDOWN,
    MEDIA_TRANSCRIPTION,
    STRUCTURED_COMPLETION,
    StructuredRequest,
)
from learnloop.config import CodexConfig, LearnLoopConfig
from learnloop.diagnosis.diagnostic_gate import request_diagnostic_fire


RESOLUTION_SITES = (
    ("learnloop.cli.runtime", "_ready_provider_for_task"),
    ("learnloop_sidecar.handlers.ai_providers", "ready_grading_provider"),
    ("learnloop.tui.screens.feedback", "_grading_provider"),
    ("learnloop.ops.startup", "run_startup_maintenance"),
    ("learnloop.content.pipeline.jobs", "default_run_legacy_ingest"),
    ("learnloop.content.pipeline.jobs", "default_inventory_client"),
)


def _runtime(provider: str, *, ready: bool) -> AIRuntimeReport:
    return AIRuntimeReport(
        status="ready" if ready else "provider_unavailable",
        active_provider=provider,
        provider_type="codex_sdk",
        model="test-model",
        message=None if ready else f"{provider} unavailable",
    )


@pytest.mark.parametrize(("module_name", "function_name"), RESOLUTION_SITES)
def test_all_six_entry_point_paths_delegate_to_the_composition_root(
    module_name: str,
    function_name: str,
) -> None:
    """Keep entry-point parity structural: sites select no provider locally."""

    module = importlib.import_module(module_name)
    module_path = Path(module.__file__ or "")
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    definitions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    assert definitions, f"{module_name}.{function_name} is missing"
    assert any(
        isinstance(call.func, ast.Name) and call.func.id == "ready_client_for_task"
        for definition in definitions
        for call in ast.walk(definition)
        if isinstance(call, ast.Call)
    ), f"{module_name}.{function_name} bypasses ready_client_for_task"


@pytest.mark.parametrize(
    ("payload", "unavailable", "expected"),
    (
        ({}, set(), ("codex_low", "codex_sdk", "gpt-5.6-sol", "codex_low", None)),
        (
            {
                "ai": {
                    "routing": {"grading": "named"},
                    "providers": {
                        "named": {
                            "type": "codex_sdk",
                            "model": "named-model",
                            "reasoning_effort": "high",
                        }
                    },
                }
            },
            set(),
            ("named", "codex_sdk", "named-model", "named", None),
        ),
        (
            {
                "ai": {
                    "active_provider": "openrouter",
                    "routing": {"grading": "openrouter"},
                }
            },
            set(),
            ("openrouter", "openrouter", "deepseek/deepseek-chat", "openrouter", None),
        ),
        (
            {
                "ai": {
                    "routing": {"grading": "primary"},
                    "fallback_provider": "backup",
                    "providers": {
                        "primary": {"type": "openrouter", "model": "primary-model"},
                        "backup": {"type": "openai_chat", "model": "backup-model"},
                    },
                }
            },
            {"primary"},
            ("backup", "openai_chat", "backup-model", "primary", "primary"),
        ),
    ),
    ids=("codex-only", "named-profile", "openrouter-active", "fallback"),
)
def test_provider_resolution_config_matrix_is_uniform(
    tmp_path,
    monkeypatch,
    payload,
    unavailable,
    expected,
) -> None:
    config = LearnLoopConfig.model_validate(payload)

    def runtime_for_provider(_root, parsed, name):
        profile = parsed.ai.providers[name]
        ready = name not in unavailable
        return AIRuntimeReport(
            status="ready" if ready else "provider_unavailable",
            active_provider=name,
            provider_type=profile.type,
            model=profile.model,
            message=None if ready else f"{name} unavailable",
        )

    monkeypatch.setattr(routing, "runtime_for_provider", runtime_for_provider)
    monkeypatch.setattr(
        routing,
        "client_for_provider",
        lambda _root, parsed, name, **_kwargs: SimpleNamespace(
            provider_name=name,
            provider_type=parsed.ai.providers[name].type,
            model=parsed.ai.providers[name].model,
        ),
    )

    resolved = ready_client_for_task(tmp_path, config, "grading")

    assert (
        resolved.provider_name,
        resolved.client.provider_type,
        resolved.client.model,
        resolved.selection.provider_name,
        resolved.fallback_from,
    ) == expected


@pytest.mark.parametrize(
    ("payload", "unavailable"),
    (
        ({}, set()),
        (
            {
                "ai": {
                    "routing": {"grading": "named", "canonical_ingest": "named"},
                    "providers": {
                        "named": {"type": "codex_sdk", "model": "named-model"}
                    },
                }
            },
            set(),
        ),
        (
            {
                "ai": {
                    "active_provider": "openrouter",
                    "routing": {
                        "grading": "openrouter",
                        "canonical_ingest": "openrouter",
                    },
                }
            },
            set(),
        ),
        (
            {
                "ai": {
                    "routing": {
                        "grading": "primary",
                        "canonical_ingest": "primary",
                    },
                    "fallback_provider": "backup",
                    "providers": {
                        "primary": {"type": "openrouter", "model": "primary-model"},
                        "backup": {"type": "openai_chat", "model": "backup-model"},
                    },
                }
            },
            {"primary"},
        ),
        (
            {
                "ai": {
                    "routing": {
                        "grading": MANUAL_PROVIDER,
                        "canonical_ingest": MANUAL_PROVIDER,
                    },
                }
            },
            set(),
        ),
    ),
    ids=("codex-only", "named-profile", "openrouter-active", "fallback", "manual"),
)
def test_config_matrix_executes_all_six_production_resolution_paths(
    tmp_path,
    monkeypatch,
    payload,
    unavailable,
) -> None:
    """Run the six adapters, not merely their shared root or their ASTs."""

    from learnloop.attempts import clarification
    from learnloop.attempts.regrade import DeferredRegradeResult
    from learnloop.cli import runtime as cli_runtime
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline import source_ingestion
    from learnloop.ops import startup
    from learnloop.tui.screens import feedback
    from learnloop.vault import loader
    from learnloop_sidecar.handlers import ai_providers

    config = LearnLoopConfig.model_validate(payload)
    vault = SimpleNamespace(root=tmp_path, config=config)

    def runtime_for_provider(_root, parsed, name):
        profile = parsed.ai.providers[name]
        ready = name not in unavailable
        return AIRuntimeReport(
            status="ready" if ready else "provider_unavailable",
            active_provider=name,
            provider_type=profile.type,
            model=profile.model,
            message=None if ready else f"{name} unavailable",
        )

    monkeypatch.setattr(routing, "runtime_for_provider", runtime_for_provider)
    monkeypatch.setattr(
        routing,
        "client_for_provider",
        lambda _root, parsed, name, **_kwargs: SimpleNamespace(
            provider_name=name,
            provider_type=parsed.ai.providers[name].type,
            model=parsed.ai.providers[name].model,
        ),
    )
    original_ready = ready_client_for_task

    def identity(resolved):
        return (
            resolved.provider_name,
            resolved.client.provider_type if resolved.client is not None else None,
            resolved.client.model if resolved.client is not None else None,
            resolved.selection.provider_name,
            resolved.fallback_from,
        )

    expected = {
        task: identity(original_ready(tmp_path, config, task))
        for task in ("grading", "canonical_ingest")
    }
    observed: list[tuple[str, tuple[object, ...]]] = []

    def recording_ready(root, parsed, task, **kwargs):
        resolved = original_ready(root, parsed, task, **kwargs)
        observed.append((task, identity(resolved)))
        return resolved

    monkeypatch.setattr(routing, "ready_client_for_task", recording_ready)
    monkeypatch.setattr(cli_runtime, "ready_client_for_task", recording_ready)
    monkeypatch.setattr(ai_providers, "ready_client_for_task", recording_ready)
    monkeypatch.setattr(feedback, "ready_client_for_task", recording_ready)
    monkeypatch.setattr(startup, "ready_client_for_task", recording_ready)

    # Keep startup headless and side-effect-free while executing its real
    # selection branch.
    empty_regrades = DeferredRegradeResult(attempted=0, regraded=0, failed=0)
    monkeypatch.setattr(clarification, "expire_clarifications", lambda *_a, **_k: [])
    monkeypatch.setattr(clarification, "resolve_awaiting_regrades", lambda *_a, **_k: None)
    monkeypatch.setattr(startup, "runtime_for_provider", runtime_for_provider)
    monkeypatch.setattr(startup, "run_deferred_regrades", lambda *_a, **_k: empty_regrades)
    monkeypatch.setattr(startup, "run_deferred_ai_regrades", lambda *_a, **_k: empty_regrades)

    # The ingest defaults import these dependencies inside their functions.
    monkeypatch.setattr(loader, "load_vault", lambda _root: vault)
    monkeypatch.setattr(
        source_ingestion,
        "ingest_canonical_source",
        lambda _root, _source, client, **_kwargs: client,
    )

    cli_runtime._ready_provider_for_task(tmp_path, config, "grading")
    ai_providers.ready_grading_provider(vault)
    feedback.FeedbackScreen._grading_provider(
        SimpleNamespace(state=SimpleNamespace(vault=vault))
    )
    startup.run_startup_maintenance(vault, SimpleNamespace())
    if expected["canonical_ingest"][0] == MANUAL_PROVIDER:
        with pytest.raises(jobs.IngestRunnerError):
            jobs.default_run_legacy_ingest(
                vault_root=tmp_path,
                source="source.md",
                subject_id="subject",
                mode="canonical",
                progress=None,
                clock=None,
            )
        with pytest.raises(jobs.IngestRunnerError):
            jobs.default_inventory_client(SimpleNamespace(vault_root=tmp_path))
    else:
        jobs.default_run_legacy_ingest(
            vault_root=tmp_path,
            source="source.md",
            subject_id="subject",
            mode="canonical",
            progress=None,
            clock=None,
        )
        jobs.default_inventory_client(SimpleNamespace(vault_root=tmp_path))

    assert observed == [
        ("grading", expected["grading"]),
        ("grading", expected["grading"]),
        ("grading", expected["grading"]),
        ("grading", expected["grading"]),
        ("canonical_ingest", expected["canonical_ingest"]),
        ("canonical_ingest", expected["canonical_ingest"]),
    ]


def test_composition_root_uses_fallback_and_preserves_requested_selection(tmp_path, monkeypatch):
    config = LearnLoopConfig()
    config.ai.routing.grading = "primary"
    config.ai.fallback_provider = "backup"
    reports = {
        "primary": _runtime("primary", ready=False),
        "backup": _runtime("backup", ready=True),
    }
    monkeypatch.setattr(
        routing,
        "runtime_for_provider",
        lambda _root, _config, name: reports[name],
    )
    monkeypatch.setattr(
        routing,
        "client_for_provider",
        lambda _root, _config, name, **_kwargs: SimpleNamespace(provider_name=name),
    )

    resolved = ready_client_for_task(tmp_path, config, "grading")

    assert resolved.selection.provider_name == "primary"
    assert resolved.provider_name == "backup"
    assert resolved.fallback_from == "primary"
    assert resolved.ready is True
    assert resolved.client.provider_name == "backup"


def test_explicit_and_environment_selections_suppress_fallback(tmp_path, monkeypatch):
    config = LearnLoopConfig()
    config.ai.routing.grading = "routed"
    config.ai.fallback_provider = "backup"
    monkeypatch.setattr(
        routing,
        "runtime_for_provider",
        lambda _root, _config, name: _runtime(name, ready=False),
    )
    built: list[str] = []
    monkeypatch.setattr(
        routing,
        "client_for_provider",
        lambda _root, _config, name, **_kwargs: built.append(name),
    )

    explicit = ready_client_for_task(tmp_path, config, "grading", explicit="chosen")
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "environment")
    environment = ready_client_for_task(tmp_path, config, "grading")

    assert explicit.provider_name == "chosen"
    assert explicit.selection.explicit is True
    assert environment.provider_name == "environment"
    assert environment.selection.from_env is True
    assert built == []


def test_manual_is_a_typed_no_client_outcome(tmp_path):
    resolved = ready_client_for_task(
        tmp_path,
        LearnLoopConfig(),
        "grading",
        explicit=MANUAL_PROVIDER,
    )

    assert resolved.manual is True
    assert resolved.provider_name == MANUAL_PROVIDER
    assert resolved.client is None
    assert resolved.ready is False
    assert resolved.runtime.active_provider == MANUAL_PROVIDER


def test_operation_routes_include_semantic_diagnostic_grading():
    assert ROUTE_FOR_OPERATION["grade_diagnostic_fire"] == "grading"
    assert ROUTE_FOR_OPERATION["source_unit_inventory"] == "canonical_ingest"
    assert ROUTE_FOR_OPERATION["concept_animation"] == "animation"
    assert ROUTE_FOR_OPERATION["video_storyboard"] == "animation"
    assert ROUTE_FOR_OPERATION["video_generation"] == "video_generation"


def test_named_codex_profile_identity_survives_provider_construction(tmp_path):
    config = LearnLoopConfig()
    profile = config.ai.providers["codex_medium"]

    client = make_ai_provider_client_from_profile("codex_medium", profile, tmp_path)

    assert client.provider_name == "codex_medium"
    assert client.provider_type == "codex_sdk"
    assert client.model == profile.model


def test_diagnostic_fire_uses_the_structured_completion_path():
    client = object.__new__(SdkCodexClient)
    client.config = SimpleNamespace(timeout_seconds=12)
    captured = []
    client.complete = lambda request: (  # type: ignore[method-assign]
        captured.append(request) or DiagnosticFireJudgment(fires=True, rationale="matched")
    )

    fires = request_diagnostic_fire(client, answer="wrong", expected="right")

    assert fires is True
    assert captured[0].purpose == "grade_diagnostic_fire"
    assert captured[0].result_model is DiagnosticFireJudgment


def test_legacy_http_declares_exactly_its_endpoint_operations():
    client = HttpCodexClient(CodexConfig(provider="http"))
    operations = {
        "authoring",
        "canonical_ingest",
        "grading",
        "tutor_qa",
        "teach_back",
        "teach_back_authoring",
        "misconception_match",
        "promotion_analysis",
    }

    assert all(client.supports(operation) for operation in operations)
    assert client.supports(STRUCTURED_COMPLETION) is False
    assert not hasattr(client, "complete")


def test_chat_complete_and_declared_media_capabilities_share_one_contract():
    client = object.__new__(OpenAIChatProviderClient)
    client.profile = SimpleNamespace(input_modalities=["audio"], timeout_seconds=9)
    captured = []
    client._run_json_messages = lambda messages, model: (  # type: ignore[method-assign]
        captured.append((messages, model)) or model(fires=False)
    )

    result = client.complete(
        StructuredRequest(
            purpose="grade_diagnostic_fire",
            prompt="judge this",
            result_model=DiagnosticFireJudgment,
            timeout_seconds=4,
        )
    )

    assert result.fires is False
    assert captured[0][1] is DiagnosticFireJudgment
    assert client.supports(STRUCTURED_COMPLETION) is True
    assert client.supports(MEDIA_TRANSCRIPTION) is True
    assert client.supports(MEDIA_MARKDOWN) is False
