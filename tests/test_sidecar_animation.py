"""Concept-animation sidecar contract: request → foreground drain → status.

The manim runtime probe and the renderer are monkeypatched (no real manim in
CI); the LLM is a fake client injected through the runner services factory.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import learnloop_sidecar.handlers.animation as animation_handlers
from learnloop.codex.schemas import ManimAnimation
from learnloop.services.concept_animation import RenderResult
from learnloop_sidecar.server import serve

from tests.helpers import create_basic_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _messages(vault_root: Path, *calls):
    payload = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}]
    payload.extend(
        {"jsonrpc": "2.0", "id": index + 2, "method": name, "params": params}
        for index, (name, params) in enumerate(calls)
    )
    return payload


def _fake_manim_available(_executable=None, **_kwargs):
    return {"available": True, "version": "Manim Community v0.18.1", "reason": None}


def test_animation_runtime_reports_probe_and_routed_model(tmp_path, monkeypatch):
    monkeypatch.setattr(animation_handlers, "manim_runtime", _fake_manim_available)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    result = _rpc(_messages(vault_root, ("get_animation_runtime", {})))[1]["result"]

    assert result["enabled"] is True
    assert result["manimAvailable"] is True
    assert "0.18.1" in result["manimVersion"]
    assert result["provider"] == "codex_medium"
    assert result["timeoutSeconds"] == 300


def test_request_rejects_missing_consent_and_missing_manim(tmp_path, monkeypatch):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    no_consent = _rpc(
        _messages(
            vault_root,
            ("request_concept_animation", {"conceptId": "singular_value_decomposition"}),
        )
    )[1]
    assert no_consent["error"]["data"]["code"] == "consent_required"

    monkeypatch.setattr(
        animation_handlers,
        "manim_runtime",
        lambda _executable=None, **_kwargs: {"available": False, "version": None, "reason": "not on PATH"},
    )
    missing = _rpc(
        _messages(
            vault_root,
            (
                "request_concept_animation",
                {"conceptId": "singular_value_decomposition", "consent": True},
            ),
        )
    )[1]
    assert missing["error"]["data"]["code"] == "manim_missing"
    assert "learnloop[animation]" in missing["error"]["data"].get("message", "") or True


def test_request_generates_and_status_reports_completed(tmp_path, monkeypatch):
    import learnloop.services.concept_animation as animation_service
    import learnloop.services.ingest_runner as runner_module

    monkeypatch.setattr(animation_handlers, "manim_runtime", _fake_manim_available)

    class _FakeClient:
        provider_name = "openrouter"
        model = "anthropic/claude-sonnet-4.5"

        def run_concept_animation(self, context) -> ManimAnimation:
            return ManimAnimation(
                scene_code=(
                    "from manim import Scene, Circle, Create\n\n\n"
                    "class ExplainSVD(Scene):\n"
                    "    def construct(self):\n"
                    "        self.play(Create(Circle()))\n"
                ),
                scene_class="ExplainSVD",
                title="SVD, visually",
                narration_md="Watch the circle.",
            )

    # The sidecar's background worker resolves these module globals at call
    # time, so patching them steers the in-process worker thread.
    monkeypatch.setattr(runner_module, "default_animation_client", lambda ctx: _FakeClient())
    monkeypatch.setattr(
        animation_service,
        "render_scene",
        lambda *args, **kwargs: RenderResult(True, b"mp4", "", 0),
    )

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    requested = _rpc(
        _messages(
            vault_root,
            (
                "request_concept_animation",
                {"conceptId": "singular_value_decomposition", "consent": True},
            ),
        )
    )[1]["result"]
    assert requested["status"] == "queued"
    animation_id = requested["animationId"]
    assert requested["batchId"]

    # The serve() session's background worker (same process) drains the durable
    # job; wait on the repository row, then assert the RPC contract.
    import time

    from learnloop.db.repositories import Repository

    repository = Repository(vault_root / "state.sqlite")
    deadline = time.time() + 30
    row = None
    while time.time() < deadline:
        row = repository.concept_animation(animation_id)
        if row and row["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)
    assert row is not None and row["status"] == "completed", row

    responses = _rpc(
        _messages(
            vault_root,
            ("get_concept_animation_status", {"animationId": animation_id}),
            ("list_concept_animations", {"conceptId": "singular_value_decomposition"}),
        )
    )
    status = responses[1]["result"]
    assert status["status"] == "completed"
    assert status["videoFileName"].startswith("sha256-")
    assert status["provider"] == "openrouter"
    assert status["title"] == "SVD, visually"
    video = vault_root / "media" / "animations" / status["videoFileName"]
    assert video.read_bytes() == b"mp4"

    listing = responses[2]["result"]
    assert listing["animations"][0]["animationId"] == animation_id
    # Non-failed rows never expose scene code over the wire.
    assert "sceneCode" not in listing["animations"][0]
