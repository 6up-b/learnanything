from __future__ import annotations

import tomllib
from types import SimpleNamespace

import pytest

from learnloop.ai.embedding import EmbeddingClient, TASK_PREFIXES
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import observe_model_calls, record_model_calls
from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient, prefixed_text
from learnloop.ai.routing import provider_for_task, ready_client_for_task
from learnloop.ai.runtime import check_ai_runtime
from learnloop.config import DEFAULT_CONFIG_TEXT, LearnLoopConfig, OpenAIEmbeddingProviderConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from tests.helpers import create_basic_vault
from tests.openai_fakes import install_fake_openai


def response(*vectors, indices=None):
    return SimpleNamespace(
        data=[SimpleNamespace(index=index, embedding=vector) for index, vector in
              zip(indices if indices is not None else range(len(vectors)), vectors)],
        usage=SimpleNamespace(prompt_tokens=12, total_tokens=12),
    )


def client(monkeypatch, *responses, **profile):
    module = install_fake_openai(monkeypatch, embeddings=responses)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    built = OpenAIEmbeddingProviderClient("embed", OpenAIEmbeddingProviderConfig(dimensions=2, **profile))
    return built, module.instances[0]


def test_batched_openrouter_request_mrl_order_and_receipt(tmp_path, monkeypatch):
    built, sdk = client(monkeypatch, response([0, 2, 3], [3, 4, 5], indices=[1, 0]))
    assert isinstance(built, EmbeddingClient)
    assert built.modalities == {"text"}
    assert sdk.kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert sdk.kwargs["max_retries"] == 0
    vault = create_basic_vault(tmp_path / "vault")
    repository = Repository(vault.sqlite_path)
    with record_model_calls(repository, owner_kind="cli", owner_id="embedding-test"):
        vectors = built.embed(["first", "second"], "retrieval-document")
    assert vectors == [[0.6, 0.8], [0.0, 1.0]]
    assert len(sdk.embedding_requests) == 1
    assert sdk.embedding_requests[0] == {
        "input": ["first", "second"],
        "model": "qwen/qwen3-embedding-8b",
        "encoding_format": "float",
        "extra_body": {"provider": {"data_collection": "deny"}},
    }
    with connect(vault.sqlite_path) as connection:
        receipt = connection.execute(
            "SELECT purpose, status, input_tokens, output_tokens FROM model_call_receipts"
        ).fetchone()
    assert tuple(receipt) == ("embedding", "completed", 12, 0)


@pytest.mark.parametrize("model", [
    "qwen/qwen3-embedding-8b", "google/gemini-embedding-2", "openai/text-embedding-3-small",
])
@pytest.mark.parametrize("prefix", sorted(TASK_PREFIXES))
def test_prefix_mapping_is_coarse_and_bounded(model, prefix):
    text = prefixed_text("hello", prefix, model)
    assert len(text.encode()) - len(b"hello") <= 128
    if model.startswith("openai/") or (model.startswith("qwen/") and prefix != "retrieval-query"):
        assert text == "hello"
    elif model.startswith("qwen/"):
        assert text.startswith("Instruct: ")
        assert text.endswith("\nQuery: hello")
    else:
        assert text.endswith(":\nhello")


@pytest.mark.parametrize("inputs,prefix", [
    (["hello"], "nuanced arbitrary instruction"),
    ([("image/png", b"image")], "similarity"),
    ([""], "retrieval-document"),
    (["   "], "retrieval-query"),
    (["x" * 32769], "retrieval-document"),
])
def test_invalid_input_rejected_before_request(monkeypatch, inputs, prefix):
    built, sdk = client(monkeypatch)
    with pytest.raises(ValueError):
        built.embed(inputs, prefix)
    assert sdk.embedding_requests == []


@pytest.mark.parametrize("reply", [
    response([1]),
    response([0, 0]),
    response([float("nan"), 1]),
    response([1, 2], indices=[1]),
    response([1, 2], [2, 3]),
    response([1, 2, float("inf")]),
])
def test_invalid_paid_response_still_records_usage(monkeypatch, reply):
    built, sdk = client(monkeypatch, reply)
    events = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        with pytest.raises(ValueError):
            built.embed(["text"], "similarity")
    assert len(sdk.embedding_requests) == 1
    assert events[-1][1]["status"] == "failed"
    assert events[-1][1]["input_tokens"] == 12


def test_empty_batch_and_provider_failure_do_not_retry(monkeypatch):
    built, sdk = client(monkeypatch, RuntimeError("offline failure"))
    assert built.embed([], "similarity") == []
    assert sdk.embedding_requests == []
    with pytest.raises(AIProviderUnavailable, match="Embedding request failed") as failure:
        built.embed(["hello"], "similarity")
    assert "offline failure" not in str(failure.value)
    assert len(sdk.embedding_requests) == 1


def test_only_known_mrl_models_can_truncate(monkeypatch):
    built, sdk = client(monkeypatch, response([1, 2, 3]), model="other/embedder")
    with pytest.raises(ValueError, match="known MRL"):
        built.embed(["hello"], "similarity")
    assert len(sdk.embedding_requests) == 1


def test_custom_key_and_endpoint(tmp_path, monkeypatch):
    module = install_fake_openai(monkeypatch)
    config = LearnLoopConfig.model_validate({
        "embedding": {"enabled": True},
        "ai": {
            "routing": {"embedding": "private"},
            "providers": {"private": {
                "type": "openai_embedding",
                "api_key_env": "PRIVATE_EMBEDDING_TEST_KEY",
                "base_url": "https://proxy.invalid/v1",
            }},
        },
    })
    monkeypatch.setenv("OPENROUTER_API_KEY", "wrong-provider-key")
    monkeypatch.delenv("PRIVATE_EMBEDDING_TEST_KEY", raising=False)
    assert not ready_client_for_task(tmp_path, config, "embedding").ready
    monkeypatch.setenv("PRIVATE_EMBEDDING_TEST_KEY", "offline-custom-key")
    assert ready_client_for_task(tmp_path, config, "embedding").ready
    assert module.instances[0].kwargs["api_key"] == "offline-custom-key"
    assert module.instances[0].kwargs["base_url"] == "https://proxy.invalid/v1"


def test_receipt_admission_failure_prevents_request(monkeypatch):
    built, sdk = client(monkeypatch)
    def reject(action, event):
        raise RuntimeError("cancelled before start")
    with observe_model_calls(reject), pytest.raises(RuntimeError, match="cancelled"):
        built.embed(["hello"], "similarity")
    assert sdk.embedding_requests == []


def test_explicit_embedding_route_never_uses_env_active_or_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "codex")
    config = LearnLoopConfig()
    config.embedding.enabled = True
    config.ai.fallback_provider = "codex"
    assert provider_for_task(config, "embedding").provider_name == ""
    assert not ready_client_for_task(tmp_path, config, "embedding").ready
    config.ai.routing.embedding = "missing"
    resolution = ready_client_for_task(tmp_path, config, "embedding")
    assert resolution.provider_name == "missing"
    assert resolution.fallback_from is None
    config.ai.routing.embedding = "codex"
    refused = ready_client_for_task(tmp_path, config, "embedding")
    assert not refused.ready
    assert "openai_embedding" in refused.runtime.message


def test_readiness_factory_and_authoritative_embedding_model(tmp_path, monkeypatch):
    module = install_fake_openai(monkeypatch)
    config = LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT))
    assert not config.embedding.enabled
    assert not config.embedding.backfill_enabled
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert not ready_client_for_task(tmp_path, config, "embedding").ready
    assert module.instances == []
    config.embedding.enabled = True
    config.embedding.model = "qwen/qwen3-embedding-4b"
    config.embedding.dimensions = 1024
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert not ready_client_for_task(tmp_path, config, "embedding").ready
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "codex")
    ready = ready_client_for_task(tmp_path, config, "embedding")
    assert ready.ready
    assert ready.client.model_id == config.embedding.model
    assert ready.client.dims == 1024
    assert ready.runtime.model == config.embedding.model
    assert len(module.instances) == 1
    def no_chat_probe(profile):
        pytest.fail("Embedding readiness must not perform a chat call")
    assert check_ai_runtime(
        tmp_path, config, provider_name="openrouter_embedding",
        openai_chat_healthcheck=no_chat_probe,
    ).ready


def test_privacy_disclosure_is_effective_config_and_settings(tmp_path):
    from tests.test_settings_sidecar import _settings_rpc

    vault = create_basic_vault(tmp_path / "vault")
    disclosure = vault.config.model_dump()["embedding"]["privacy_disclosure"]
    assert "OpenRouter" in disclosure and "plaintext" in disclosure
    settings = _settings_rpc(vault.root, ("get_settings", {}))[0]["result"]
    assert settings["embedding"]["privacyDisclosure"] == disclosure
    assert settings["embedding"]["enabled"] is False


def test_template_keeps_ai_comments_on_ai_and_no_project_jargon():
    text = DEFAULT_CONFIG_TEXT
    assert "# Exception: embeddings use only their explicit route, never env/active/fallback.\n[ai]\n" in text
    assert text.index("[embedding]") > text.index("[ai.routing]")
    assert "Phase 1" not in text and "pf_" not in text
    assert "data_collection=deny" in text


def test_gemini_embedding_2_embeds_page_images_through_openrouter_multimodal_input(monkeypatch):
    # Slice 2 T6's B4: an image is one {"content": [image_url part]} input; the
    # receipt hashes only a digest of the image, never the bytes.
    built, sdk = client(monkeypatch, response([0, 2], [3, 4]), model="google/gemini-embedding-2")
    assert built.modalities == {"text", "image"}
    events = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        vectors = built.embed(["a question", ("image/png", b"\x89PNG fake")], "retrieval-document")
    assert vectors == [[0.0, 1.0], [0.6, 0.8]]
    sent = sdk.embedding_requests[0]["input"]
    assert sent[0] == "Represent this document for retrieval:\na question"
    assert sent[1] == {"content": [{"type": "image_url",
                                    "image_url": {"url": "data:image/png;base64,iVBORyBmYWtl"}}]}
    assert events[0][1]["input_text"] is None  # a list prompt is hashed, not stored


@pytest.mark.parametrize("value", [("image/gif", b"x"), ("image/png", b""), ("image/png", "not bytes")])
def test_image_inputs_are_validated_before_any_request(monkeypatch, value):
    built, sdk = client(monkeypatch, model="google/gemini-embedding-2")
    with pytest.raises(ValueError):
        built.embed([value], "retrieval-document")
    assert sdk.embedding_requests == []
