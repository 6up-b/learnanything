"""E0 fix round 4 follow-up: the orchestrator-verified prices and the Codex lockdown, fakes only.

* Every metered pin carries exactly the price, source and date the
  orchestrator verified on 2026-10-21; Voyage's free tier is noted and never
  assumed (admission charges the full price).
* The paid run refuses to start unless the Codex tool lockdown (main
  55063be64) is importable and in force, and E0's Codex roles (the label
  passes among them) run through its locked-down turn.

No network: a socket guard refuses any connection; no Codex turn starts."""
from __future__ import annotations

import builtins
import socket

import pytest

from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from tests.e0_fakes import FAKE_KEYS, FakeEmbeddingTransport, build_e0_vault

VERIFIED = {
    "pplx_4b": (0.03, "https://docs.perplexity.ai/docs/pricing"),
    "pplx_context_4b": (0.05, "https://docs.perplexity.ai/docs/pricing"),
    "voyage_4_large": (0.12, "https://docs.voyageai.com/docs/pricing"),
    "voyage_context_4": (0.12, "https://docs.voyageai.com/docs/pricing"),
    "qwen3_8b": (0.01, "https://openrouter.ai/qwen/qwen3-embedding-8b/pricing"),
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def test_every_metered_pin_carries_exactly_the_orchestrator_verified_price():
    for name, (price, url) in VERIFIED.items():
        pin = pins.EMBEDDING_PINS[name]
        assert pin.price_per_million_upper_bound == price, name
        assert (pin.price_verified.source_url, pin.price_verified.checked_on) == (url, "2026-10-21"), name
        assert pins.price_problem(pin) is None, name
    for role in ("adjudicator", "judge_adjudicator"):
        pin = pins.ROLE_PINS[role]
        assert (pin.input_price_per_million, pin.output_price_per_million) == (2.0, 10.0)
        assert pin.price_verified.source_url == "https://openrouter.ai/anthropic/claude-sonnet-5.5/pricing"
        assert pin.price_verified.checked_on == "2026-10-21"
        assert "platform.claude.com/docs/en/about-claude/pricing" in pin.price_verified.note
    assert pins.unverified_prices() == {"embeddings": [], "roles": []}
    for name in ("voyage_4_large", "voyage_context_4"):
        note = pins.EMBEDDING_PINS[name].price_verified.note
        assert "200M tokens are free" in note and "never assumes the free tier" in note


def test_voyage_is_admitted_at_the_full_price_never_the_free_tier(tmp_path):
    pin = pins.EMBEDDING_PINS["voyage_4_large"]
    ledger = E0Ledger(tmp_path / "ledger")
    adapter = A.VoyageIndependentAdapter(pin, encoding="independent", recipe="plain", ledger=ledger, arm="R5",
                                         transport=FakeEmbeddingTransport(dims={pin.model: pin.dimensions}),
                                         receipts=A.Receipts(None), store=A.VectorStore(None), environ=FAKE_KEYS,
                                         sleep=lambda _seconds: None)
    text = "Definition of a vector space."
    adapter.encode_documents([A.Document("w1", (A.Chunk("w1:a", text),), key="k1")])
    [entry] = __import__("json").loads(ledger.path.read_text(encoding="utf-8"))["entries"].values()
    tokens = pins.token_upper_bound(text) + pins.CHUNK_MARKER_TOKENS
    assert float(entry["reserved_usd"]) == pytest.approx(tokens * 0.12 / 1_000_000)
    assert float(entry["reserved_usd"]) > 0


# -- the Codex lockdown -------------------------------------------------------------------


def test_the_lockdown_is_active_on_this_tree():
    from learnloop.experiments.contextual_embeddings.boundary import require_codex_lockdown

    checked = require_codex_lockdown()
    assert checked["codex_lockdown"] == "active" and checked["overrides_checked"] > 40


def _plan(tmp_path):
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    return paths, dry_run([paths.root], environ=FAKE_KEYS)


def test_the_paid_run_refuses_when_the_lockdown_is_not_importable(tmp_path, monkeypatch):
    from learnloop.experiments.contextual_embeddings import live
    from learnloop.experiments.contextual_embeddings.boundary import CodexLockdownMissing

    paths, plan = _plan(tmp_path)
    real_import = builtins.__import__

    def without_lockdown(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "learnloop.ai.providers.codex_lockdown" or (
                name == "learnloop.ai.providers" and fromlist and "codex_lockdown" in fromlist):
            raise ImportError("codex_lockdown removed for this test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", without_lockdown)
    with pytest.raises(CodexLockdownMissing, match="not importable"):
        live.run_live([paths.root], plan=plan, run_dir=tmp_path / "fixtures-local" / "runs", key_envs={})
    monkeypatch.setattr(builtins, "__import__", real_import)
    # Refused before anything: no ledger, no run directory.
    assert not (tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger").exists()
    assert not (tmp_path / "fixtures-local" / "runs").exists()


def test_the_paid_cli_refuses_when_the_lockdown_is_not_in_force(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.ai.providers import codex as provider
    from learnloop.cli import app
    from learnloop.experiments.contextual_embeddings import live, runner

    paths, _plan_unused = _plan(tmp_path)
    original = provider.isolated_turn_overrides
    monkeypatch.setattr(provider, "isolated_turn_overrides",
                        lambda *args, **kwargs: [item for item in original(*args, **kwargs)
                                                 if item != "agents.enabled=false"])
    monkeypatch.setattr(runner, "dry_run", lambda *args, **kwargs: {"totals": {"fits_cap": True},
                                                                     "prices": {"unverified": {}}})
    called = []
    monkeypatch.setattr(live, "run_live", lambda *args, **kwargs: called.append(1))
    result = CliRunner().invoke(app, ["experiments", "e0", "run", "--copy", str(paths.root),
                                      "--i-am-authorized-to-spend", "--run-dir",
                                      str(tmp_path / "fixtures-local" / "runs")])
    assert result.exit_code == 1 and "lockdown is not active" in result.output
    assert called == []


def test_the_label_passes_run_through_the_locked_down_codex_turn(tmp_path, monkeypatch):
    """E0's Codex roles resolve the production Codex client and reach its
    locked-down turn (``SdkCodexClient._run_sdk_turn``, isolated: every turn
    there runs the lockdown's verified overrides and ``TurnLockdown``); the
    turn is stopped at its entry, so nothing starts."""

    from learnloop.ai.providers import codex as provider
    from learnloop.experiments.contextual_embeddings.budget import E0ProviderFailure
    from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    reached = []

    def stop_at_the_turn(self, prompt, output_schema, **kwargs):
        reached.append({"isolated": kwargs.get("isolated"), "workspace": kwargs.get("workspace")})
        raise provider.CodexLockdownUnavailable("stopped at the locked-down turn's entry (test)")

    monkeypatch.setattr(provider.SdkCodexClient, "_run_sdk_turn", stop_at_the_turn)
    monkeypatch.setattr(provider.SdkCodexClient, "_ensure_codex_ready", lambda self: None, raising=False)
    caller = LiveRoleCaller(handle.root, handle.vault.config, E0Ledger(tmp_path / "ledger"),
                            checkpoints=Checkpoints(None))
    for role in ("label_a", "label_b"):
        with pytest.raises(E0ProviderFailure):
            caller.call(role, prompt="prompt_version: e0-label-v1\n{}", result_model=B.LabelPass)
    assert reached and all(item["isolated"] is True and item["workspace"] is None for item in reached)
    client, _identity = caller._client(pins.ROLE_PINS["label_a"])
    assert isinstance(client, provider.SdkCodexClient)
