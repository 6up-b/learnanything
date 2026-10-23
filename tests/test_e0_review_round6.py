"""Pre-paid verify of 6b203def3 (SAFE TO RUN): the small round M1, M2, L1, L4, L7, fakes only.

* M1: no E0 vault load reads a dotenv or ``settings.env`` (a LEARNLOOP_AI_PROVIDER
  there would re-route the copies' source routes mid-run).
* M2: the re-allocation within the $40 cap leaves headroom above an Opus
  reservation in labels and answers.
* L1: the HTTPS transport never follows a redirect (the key header would be
  replayed); a 3xx is a contract failure, never retried.
* L4: the Messages API client refuses to send without an active request gate.
* L7: the paid run refuses a run directory outside fixtures-local.

No network: a socket guard refuses any connection."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import urllib.error
import urllib.request

import pytest

from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.anthropic_api import AnthropicMessagesClient
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, E0ProviderFailure
from learnloop.experiments.contextual_embeddings.callers import E0RequestGate
from tests.e0_fakes import FAKE_KEYS, build_e0_vault

ARTIFACT = Path(__file__).resolve().parents[1] / "docs" / "reviews" / "artifacts" / "experiments-e0" / "dry-run-plan.json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


# -- M1 -----------------------------------------------------------------------------------


def test_m1_no_e0_vault_load_reads_settings_env_or_a_copy_dotenv(tmp_path, monkeypatch):
    from learnloop.config.loader import global_settings_path
    from learnloop.experiments.contextual_embeddings.system_arms import make_service_copy, open_service

    environ = {key: value for key, value in os.environ.items()
               if key not in ("LEARNLOOP_AI_PROVIDER", "E0_TEST_DOTENV_MARKER")}
    monkeypatch.setattr(os, "environ", environ)
    config_dir = tmp_path / "learnloop-config"
    config_dir.mkdir()
    environ["LEARNLOOP_CONFIG_DIR"] = str(config_dir)
    # Test setup first (the helpers load the test vault their own way), then the files E0 must not read.
    paths, _repository = build_e0_vault(tmp_path)
    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / "r0")
    environ.pop("LEARNLOOP_AI_PROVIDER", None)
    settings = global_settings_path()
    assert settings == config_dir / "settings.env"  # the test's own config dir, never the owner's
    settings.write_text("LEARNLOOP_AI_PROVIDER=e0-test-provider\n", encoding="utf-8")
    (root / ".env").write_text("E0_TEST_DOTENV_MARKER=from-the-copy\n", encoding="utf-8")
    (paths.root / ".env").write_text("E0_TEST_DOTENV_MARKER=from-the-frozen-copy\n", encoding="utf-8")
    handle = open_service(root)
    C.open_copy(paths.root)
    assert "LEARNLOOP_AI_PROVIDER" not in os.environ and "E0_TEST_DOTENV_MARKER" not in os.environ
    assert handle.vault.config.ai.active_provider != "e0-test-provider"


# -- M2 -----------------------------------------------------------------------------------


def test_m2_the_allocation_covers_each_expected_spend_with_headroom_above_an_opus_reservation():
    assert pins.E0_CAP_USD == 40.0
    assert pins.ALLOCATION_USD == {"embeddings": 0.25, "drafting_context": 0.85, "labels_audits": 24.60,
                                   "answers_verification": 14.30}
    assert sum(pins.ALLOCATION_USD.values()) == pytest.approx(40.0)
    plan = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert plan["totals"]["cap_usd"] == 40.0
    opus = pins.ROLE_PINS["adjudicator"]
    one_reservation = pins.ROLE_PINS["adjudicator"].max_output_tokens * opus.output_price_per_million / 1e6
    for name, category in plan["totals"]["categories"].items():
        assert category["allocation_usd"] == pins.ALLOCATION_USD[name]  # the committed plan is current
        assert category["estimated_usd"] <= category["allocation_usd"], name
    for name in ("labels_audits", "answers_verification"):
        category = plan["totals"]["categories"][name]
        assert category["allocation_usd"] - category["estimated_usd"] > one_reservation, name


# -- L1 -----------------------------------------------------------------------------------


def test_l1_the_transport_never_follows_a_redirect():
    handlers = A.UrllibTransport.opener.handlers
    assert any(isinstance(handler, A.NoRedirect) for handler in handlers)
    assert not any(type(handler) is urllib.request.HTTPRedirectHandler for handler in handlers)
    request = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
                                     headers={"x-api-key": "k"})
    assert A.NoRedirect().redirect_request(request, None, 307, "Temporary Redirect", {},
                                           "https://elsewhere.example/v1/messages") is None


class _Redirecting:
    """An opener whose every request answers 302 (urllib raises it as an HTTPError)."""

    def __init__(self):
        self.calls = 0

    def open(self, request, timeout=None):
        self.calls += 1
        raise urllib.error.HTTPError(request.full_url, 302, "Found", {"location": "https://elsewhere.example/"},
                                     None)


def test_l1_a_redirect_is_a_contract_failure_that_is_never_retried(tmp_path, monkeypatch):
    from learnloop.ai.execution import gate_model_requests

    opener = _Redirecting()
    transport = A.UrllibTransport()
    monkeypatch.setattr(transport, "opener", opener)
    assert transport.post("https://api.anthropic.com/v1/messages", headers={}, body={}, timeout=1).status == 302
    opener.calls = 0
    pin = pins.ROLE_PINS["tutor"]
    client = AnthropicMessagesClient(pin, environ={"ANTHROPIC_API_KEY": "sk-ant-test-not-real"}, transport=transport,
                                     sleep=lambda _seconds: None)
    from learnloop.experiments.contextual_embeddings import bank as B

    with gate_model_requests(E0RequestGate(E0Ledger(tmp_path / "ledger"), pin)):
        with pytest.raises(E0ProviderFailure) as raised:
            client.structured(purpose="e0_tutor", prompt="p", result_model=B.WrittenQuestions, max_tokens=64)
    assert raised.value.classification == "contract" and raised.value.status_code == 302
    assert opener.calls == 1  # never retried
    # The hosted embedding adapters treat it the same way.
    opener.calls = 0
    voyage = pins.EMBEDDING_PINS["voyage_4_large"]
    import dataclasses

    voyage = dataclasses.replace(voyage, price_verified=pins.PriceVerification("https://example.invalid/p",
                                                                               "2026-10-22"))
    adapter = A.VoyageIndependentAdapter(voyage, encoding="independent", recipe="plain",
                                         ledger=E0Ledger(tmp_path / "ledger2"), arm="R5", transport=transport,
                                         receipts=A.Receipts(None), store=A.VectorStore(None), environ=FAKE_KEYS,
                                         sleep=lambda _seconds: None)
    with pytest.raises(A.AdapterError) as failure:
        adapter.encode_documents([A.Document("w1", (A.Chunk("w1:a", "Definition of a vector space."),), key="k")])
    assert failure.value.kind == "contract" and opener.calls == 1


# -- L4 -----------------------------------------------------------------------------------


def test_l4_the_messages_client_refuses_to_send_without_a_request_gate():
    posts = []

    class Server:
        def post(self, *args, **kwargs):
            posts.append(1)
            raise AssertionError("sent without a gate")

    client = AnthropicMessagesClient(pins.ROLE_PINS["tutor"], environ={"ANTHROPIC_API_KEY": "sk-ant-test-not-real"},
                                     transport=Server())
    with pytest.raises(E0BudgetExceeded, match="no E0 request gate"):
        client.send(client.body("s", "u", 16), purpose="x", prompt_identity="x")
    assert posts == []


# -- L7 -----------------------------------------------------------------------------------


def test_l7_the_paid_run_refuses_a_run_directory_outside_fixtures_local(tmp_path):
    from learnloop.experiments.contextual_embeddings import live

    paths, _repository = build_e0_vault(tmp_path)
    with pytest.raises(ValueError, match="fixtures-local"):
        live.run_live([paths.root], plan={"run_id": "e0_0123456789abcdef"}, run_dir=tmp_path / "elsewhere",
                      key_envs={})
    assert not (tmp_path / "elsewhere").exists()
    assert not (tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger").exists()
