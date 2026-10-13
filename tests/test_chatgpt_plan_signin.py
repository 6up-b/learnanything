"""Sign in with ChatGPT: registration, validation, storage, refresh and sign-out.

Everything runs against the local fake in ``tests/chatgpt_plan_fakes.py`` on
127.0.0.1; the store is a per-test LEARNLOOP_CONFIG_DIR, so no test reads the
real one, and the file backend is forced (conftest), so none reaches a keyring.
"""
from __future__ import annotations

import base64
import json
import stat
import sys
import threading
import types
import urllib.parse

import pytest

from learnloop.ai.chatgpt_plan.oauth import SignInError, rs256_verify, validate_id_token
from learnloop.ai.chatgpt_plan.session import (
    ChatGPTPlanNotEnabled,
    ChatGPTSignInRequired,
    PlanSession,
)
from learnloop.ai.chatgpt_plan.store import KEYRING_SERVICE, PlanStore
from learnloop.ai.errors import AIProviderUnavailable

from tests.chatgpt_plan_fakes import (
    IDENTITY_SCOPES,
    complete_browser_flow,
    fake_chatgpt,
    rsa_test_key,
    sign_in,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    return tmp_path / "config" / "chatgpt_plan"


def _query(url: str) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))


def test_first_sign_in_registers_validates_and_stores_machine_locally(isolated_store):
    with fake_chatgpt() as server:
        session = PlanSession()
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        query = _query(pending.authorize_url)
        assert query["client_id"] == "dynamic_agent_client"
        assert query["agent_name_hint"] == "LearnLoop"
        assert query["ext_agent_host_id"].startswith("urn:uuid:")
        assert query["scope"] == "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
        assert query["resource"] == "https://api.openai.com/v1"
        assert query["code_challenge_method"] == "S256"
        assert query["redirect_uri"].startswith("http://127.0.0.1:") and query["redirect_uri"].endswith("/auth/callback")
        assert "localhost" not in pending.authorize_url
        assert query["state"] and query["nonce"] and query["state"] != query["nonce"]
        complete_browser_flow(pending.authorize_url)
        result = pending.wait(timeout=10)

        assert result.client_id == "oaiapp_test_client"
        assert result.new_registration and result.plan_usage_enabled and result.welcome_pending
        assert result.id_token_signature == "rs256"
        exchange = server.token_requests[-1]
        assert exchange["grant_type"] == "authorization_code"
        assert exchange["client_id"] == "oaiapp_test_client"  # the issued id, never dynamic_agent_client
        assert exchange["redirect_uri"] == query["redirect_uri"]
        assert exchange["resource"] == "https://api.openai.com/v1"

    # Machine-local, owner-only, and the account file holds no token.
    assert stat.S_IMODE(isolated_store.stat().st_mode) == 0o700
    for path in isolated_store.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, path.name
    account = json.loads((isolated_store / "account.json").read_text())
    assert account["client_id"] == "oaiapp_test_client" and account["email"] == "learner@example.com"
    assert "access-" not in json.dumps(account) and "refresh-" not in json.dumps(account)
    tokens = json.loads((isolated_store / "tokens.json").read_text())
    assert tokens["client_id"] == "oaiapp_test_client" and tokens["tokens"]["access_token"].startswith("access-")
    status = PlanSession().status().as_dict()
    assert status["state"] == "ready" and status["welcome_pending"] is True
    assert "access-" not in json.dumps(status)


def test_returning_sign_in_reuses_the_issued_client_and_host():
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        host = session.store.host_id()
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        query = _query(pending.authorize_url)
        assert query["client_id"] == "oaiapp_test_client"
        assert "agent_name_hint" not in query
        assert query["login_hint"] == "learner@example.com"
        assert query["ext_agent_host_id"] == host
        complete_browser_flow(pending.authorize_url)
        result = pending.wait(timeout=10)
        assert not result.new_registration and result.client_id == "oaiapp_test_client"


def test_state_mismatch_is_refused_before_any_exchange():
    with fake_chatgpt() as server:
        session = PlanSession()
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        pending.close()
        with pytest.raises(SignInError) as caught:
            pending.finish({"state": "forged", "code": "code-1", "client_id": "oaiapp_x"})
        assert caught.value.code == "state_mismatch"
        assert server.token_requests == []
    assert session.store.load_account() is None


def test_declined_consent_saves_nothing():
    with fake_chatgpt() as server:
        server.deny = True
        session = PlanSession()
        with pytest.raises(SignInError) as caught:
            sign_in(session, server)
        assert caught.value.code == "access_denied"
        assert server.token_requests == []
    assert session.store.load_account() is None


def test_registration_without_issued_client_id_is_incomplete():
    with fake_chatgpt(include_client_id_in_callback=False) as server:
        with pytest.raises(SignInError) as caught:
            sign_in(PlanSession(), server)
        assert caught.value.code == "registration_incomplete"


def test_reauthorization_rejects_a_callback_naming_another_client():
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        pending.close()
        with pytest.raises(SignInError) as caught:
            pending.finish({"state": pending.state, "code": "c", "client_id": "oaiapp_other"})
        assert caught.value.code == "client_mismatch"


def test_wrong_nonce_is_refused_and_nothing_replaced():
    with fake_chatgpt(wrong_nonce=True) as server:
        session = PlanSession()
        with pytest.raises(SignInError) as caught:
            sign_in(session, server)
        assert caught.value.code == "invalid_id_token" and "nonce" in str(caught.value)
    assert session.store.load_account() is None


def test_returning_sign_in_with_another_account_keeps_the_saved_one():
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        server.subject = "someone-else"
        with pytest.raises(SignInError) as caught:
            sign_in(session, server)
        assert caught.value.code == "account_mismatch"
        account = session.store.load_account()
        assert account.subject == "user-sub-1" and account.signed_in


def test_a_grant_without_plan_usage_signs_in_but_is_not_usable():
    with fake_chatgpt(granted_scope=IDENTITY_SCOPES + " offline_access") as server:
        session = PlanSession()
        result = sign_in(session, server)
        assert not result.plan_usage_enabled and not result.welcome_pending
        state, message = session.status().readiness()
        assert state == "plan_usage_disabled" and "--consent" in message
        with pytest.raises(ChatGPTPlanNotEnabled):
            session.check_usable(pause_minutes=15)
        # Re-enabling asks for consent again with the full scope set.
        pending = session.begin_sign_in(issuer=server.issuer, port=0, consent=True)
        query = _query(pending.authorize_url)
        pending.close()
        assert query["prompt"] == "consent" and "chatgpt.tokens.use.direct" in query["scope"]


def test_sign_in_timeout_and_cancel_end_the_attempt():
    with fake_chatgpt() as server:
        session = PlanSession()
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        with pytest.raises(SignInError) as caught:
            pending.wait(timeout=0.05)
        assert caught.value.code == "timed_out"
        pending = session.begin_sign_in(issuer=server.issuer, port=0)
        threading.Timer(0.05, pending.cancel).start()
        with pytest.raises(SignInError) as caught:
            pending.wait(timeout=10)
        assert caught.value.code == "cancelled"


def test_id_token_signature_checks():
    key = rsa_test_key()
    claims = {"iss": "https://issuer", "aud": "oaiapp_a", "sub": "s", "iat": 1, "exp": 4_000_000_000, "nonce": "n"}
    good = key.sign_jwt(claims)
    jwks = lambda: [key.jwk()]  # noqa: E731
    assert validate_id_token(good, issuer="https://issuer", client_id="oaiapp_a", nonce="n", jwks=jwks).signature == "rs256"
    header, payload, signature = good.split(".")
    tampered = ".".join([header, payload[:-2] + ("A" if payload[-2] != "A" else "B") + payload[-1], signature])
    with pytest.raises(SignInError):
        validate_id_token(tampered, issuer="https://issuer", client_id="oaiapp_a", nonce="n", jwks=jwks)
    with pytest.raises(SignInError):
        validate_id_token(key.sign_jwt(claims, alg="none"), issuer="https://issuer", client_id="oaiapp_a",
                          nonce="n", jwks=jwks)
    hmac_header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    with pytest.raises(SignInError):
        validate_id_token(".".join([hmac_header, payload, signature]), issuer="https://issuer",
                          client_id="oaiapp_a", nonce="n", jwks=jwks)
    with pytest.raises(SignInError):
        validate_id_token(good, issuer="https://other", client_id="oaiapp_a", nonce="n", jwks=jwks)
    with pytest.raises(SignInError):
        validate_id_token(good, issuer="https://issuer", client_id="oaiapp_b", nonce="n", jwks=jwks)
    expired = key.sign_jwt({**claims, "exp": 10})
    with pytest.raises(SignInError):
        validate_id_token(expired, issuer="https://issuer", client_id="oaiapp_a", nonce="n", jwks=jwks)
    # Unreachable keys fall back to the TLS rule (recorded), never to "verified".
    assert validate_id_token(good, issuer="https://issuer", client_id="oaiapp_a", nonce="n",
                             jwks=lambda: []).signature == "tls_endpoint"
    # The verifier refuses short keys and a wrong-length signature.
    assert not rs256_verify(key.n % (1 << 1024), key.e, b"x", b"\x00" * 128)


def test_refresh_rotates_tokens_and_never_sends_scope():
    with fake_chatgpt(access_lifetime=60) as server:  # inside the refresh margin
        session = PlanSession()
        sign_in(session, server)
        first = session.store.load_tokens(session.store.load_account())
        token = session.access_token()
        refreshed = session.store.load_tokens(session.store.load_account())
        request = server.token_requests[-1]
        assert request["grant_type"] == "refresh_token" and "scope" not in request
        assert request["client_id"] == "oaiapp_test_client" and request["resource"] == "https://api.openai.com/v1"
        assert token == refreshed.access_token != first.access_token
        assert refreshed.refresh_token != first.refresh_token
        assert refreshed.id_token == first.id_token  # kept when the refresh returns none
        # The rotated-out refresh token is dead.
        assert first.refresh_token in server.used_refresh_tokens


def test_concurrent_refreshes_send_one_request():
    with fake_chatgpt(access_lifetime=60) as server:
        sign_in(PlanSession(), server)
        server.access_lifetime = 3600  # the refreshed token is fresh
        before = len(server.token_requests)
        barrier = threading.Barrier(4)
        tokens: list[str] = []
        errors: list[BaseException] = []

        def worker() -> None:
            session = PlanSession()  # separate objects on one store, as two processes would be
            barrier.wait()
            try:
                tokens.append(session.access_token())
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        assert not errors
        assert len(server.token_requests) - before == 1
        assert len(set(tokens)) == 1


def test_invalid_grant_clears_tokens_and_requires_sign_in():
    with fake_chatgpt(access_lifetime=60) as server:
        session = PlanSession()
        sign_in(session, server)
        server.refresh_error = "invalid_grant"
        with pytest.raises(ChatGPTSignInRequired) as caught:
            session.access_token()
        assert "learnloop ai signin chatgpt" in str(caught.value)
        account = session.store.load_account()
        assert account.client_id == "oaiapp_test_client" and not account.signed_in  # registration kept
        assert session.store.load_tokens(account) is None
        assert session.status().readiness()[0] == "signed_out"


def test_transient_refresh_failure_keeps_credentials(monkeypatch):
    with fake_chatgpt(access_lifetime=600) as server:  # valid, but inside the margin
        session = PlanSession()
        sign_in(session, server)
        monkeypatch.setattr("learnloop.ai.chatgpt_plan.session.REFRESH_MARGIN_SECONDS", 900)
        server.refresh_error = "temporarily_unavailable"
        token = session.access_token()  # still valid: the old token serves
        assert token.startswith("access-")
        assert session.store.load_account().signed_in
    session.store.update_state(force_refresh=True)
    expired = session.store.load_tokens(session.store.load_account())
    expired.expires_at = 0
    session.store.save_tokens(session.store.load_account(), expired)
    with pytest.raises(AIProviderUnavailable):
        session.access_token()  # the fake is gone: unreachable, credentials kept
    assert session.store.load_account().signed_in


def test_sign_out_revokes_then_clears_tokens_but_keeps_the_registration():
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        refresh = session.store.load_tokens(session.store.load_account()).refresh_token
        result = session.sign_out()
        assert result["revoked"] is True
        assert server.revocations == [{"token": refresh, "token_type_hint": "refresh_token",
                                       "client_id": "oaiapp_test_client"}]
        account = session.store.load_account()
        assert account.client_id == "oaiapp_test_client" and not account.signed_in
        assert session.store.load_tokens(account) is None
        assert not (session.store.root / "tokens.json").exists()


def test_keyring_backend_keeps_tokens_out_of_files(monkeypatch):
    saved: dict[tuple[str, str], str] = {}

    class Backend:
        priority = 5

    fake_keyring = types.ModuleType("keyring")
    fake_keyring.get_keyring = lambda: Backend()  # type: ignore[attr-defined]
    fake_keyring.get_password = lambda service, user: saved.get((service, user))  # type: ignore[attr-defined]
    fake_keyring.set_password = lambda service, user, value: saved.__setitem__((service, user), value)  # type: ignore[attr-defined]
    fake_keyring.delete_password = lambda service, user: saved.pop((service, user), None)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "keyring", fake_keyring)
    monkeypatch.delenv("LEARNLOOP_CHATGPT_SECRET_STORE", raising=False)
    with fake_chatgpt() as server:
        session = PlanSession()
        result = sign_in(session, server)
        assert result.secret_store == "keyring"
        assert (KEYRING_SERVICE, "oaiapp_test_client") in saved
        assert not (session.store.root / "tokens.json").exists()
        assert session.access_token().startswith("access-")
        session.sign_out()
        assert saved == {}


def test_store_root_follows_the_config_dir(isolated_store):
    assert PlanStore().root == isolated_store


def test_a_pause_ends_by_itself_after_the_profile_window():
    with fake_chatgpt() as server:
        session = PlanSession()
        sign_in(session, server)
        session.store.update_state(usage_limit={"code": "subscription_sharing_usage_limit_exceeded",
                                                "at": "2020-01-01T00:00:00+00:00", "request_id": None})
        status = session.status()
        assert status.readiness(pause_minutes=15)[0] == "ready"
        assert status.as_dict(pause_minutes=15)["paused_until"] is None
        session.note_success()
        assert "usage_limit" not in session.store.load_state()
