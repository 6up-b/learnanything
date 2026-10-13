"""Sign in with ChatGPT for open-source apps: OAuth 2.0 code flow with PKCE.

Pinned from OpenAI's developer docs (developers.openai.com/siwc, re-verified
2026-10-12 and recorded in ``docs/reviews/chatgpt-plan-provider.md``):

* **Registration.** The first sign-in uses ``client_id=dynamic_agent_client``
  with this host's ``ext_agent_host_id`` and ``agent_name_hint=LearnLoop``. The
  callback returns the issued ``oaiapp_…`` client id, which is saved and used
  for the code exchange and every later sign-in, refresh and revocation (never
  ``dynamic_agent_client``). No client secret.
* **Authorize.** ``https://auth.openai.com/api/accounts/authorize`` with
  ``response_type=code``, the loopback ``redirect_uri``
  (``http://127.0.0.1:<port>/auth/callback``, never ``localhost``; only the
  port may vary), ``scope=openid profile email offline_access resource.invoke
  chatgpt.tokens.use.direct``, ``resource=https://api.openai.com/v1``, a fresh
  ``state``, ``nonce`` and S256 ``code_challenge``. Later sign-ins send the
  saved client id, omit ``agent_name_hint`` and may send ``login_hint``.
* **Exchange and refresh.** Form POSTs to
  ``https://auth.openai.com/api/accounts/oauth/token`` (``authorization_code``
  with the verifier, the same ``redirect_uri`` and ``resource``; or
  ``refresh_token`` with ``resource`` and no ``scope``). Refresh tokens rotate:
  the access token, expiry, scopes and refresh token are replaced together.
* **Validation.** ``state`` before anything else; then the ID token's
  issuer, audience (the issued client id), expiry and nonce, and its signature
  against the issuer's JWKS. ChatGPT plan usage is enabled only when the
  granted scopes include ``chatgpt.tokens.use.direct``.

Endpoints come from the issuer's discovery document when it answers, with the
documented paths as the fallback. Nothing here logs or returns a token.
"""
from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import hmac
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import secrets
import threading
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

AUTH_ISSUER = "https://auth.openai.com"
AUTHORIZE_PATH = "/api/accounts/authorize"
TOKEN_PATH = "/api/accounts/oauth/token"
PLAN_RESOURCE = "https://api.openai.com/v1"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
REQUESTED_SCOPES = ("openid", "profile", "email", "offline_access", "resource.invoke", PLAN_SCOPE)
DYNAMIC_CLIENT_ID = "dynamic_agent_client"
AGENT_NAME = "LearnLoop"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PATH = "/auth/callback"
#: The docs' example port; any free port works because only the port may vary.
PREFERRED_CALLBACK_PORT = 1455
#: Allowed clock skew when checking the ID token's expiry.
CLOCK_SKEW_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 20.0
#: Refresh-token error codes after which the token set is unusable
#: (errors-and-recovery: "Clear unusable tokens and repeat OAuth").
TERMINAL_REFRESH_ERRORS = frozenset({
    "invalid_grant", "invalid_refresh_token", "token_expired", "refresh_token_expired",
    "refresh_token_invalidated", "refresh_token_reused",
})
#: RSA PKCS #1 v1.5 DigestInfo prefix for SHA-256 (RFC 8017 §9.2).
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")
_MIN_RSA_BITS = 2048

#: (method, url, headers, body, timeout) -> (status, headers, body)
HttpCall = Callable[[str, str, Mapping[str, str], bytes | None, float], tuple[int, Mapping[str, str], bytes]]


class SignInError(RuntimeError):
    """The sign-in attempt ended without usable credentials."""

    def __init__(self, message: str, *, code: str = "sign_in_failed") -> None:
        super().__init__(message)
        self.code = code


class TokenEndpointError(RuntimeError):
    """The token or revocation endpoint answered with an error status."""

    def __init__(self, status: int, error: str | None, description: str | None) -> None:
        detail = f"{error}: {description}" if error and description else (error or description or "no error body")
        super().__init__(f"HTTP {status}: {detail[:300]}")
        self.status = status
        self.error = error


class EndpointUnreachable(RuntimeError):
    """A network failure before any answer (the reason never echoes a URL or token)."""


def urllib_call(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float,
) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https/loopback endpoints
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise EndpointUnreachable(f"{type(exc).__name__}") from None


# -- discovery ----------------------------------------------------------------


@dataclass(frozen=True)
class Discovery:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str | None
    revocation_endpoint: str | None
    from_document: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "issuer": self.issuer, "authorization_endpoint": self.authorization_endpoint,
            "token_endpoint": self.token_endpoint, "jwks_uri": self.jwks_uri,
            "revocation_endpoint": self.revocation_endpoint, "from_document": self.from_document,
        }


def discover(issuer: str = AUTH_ISSUER, *, http: HttpCall = urllib_call, timeout: float = HTTP_TIMEOUT_SECONDS) -> Discovery:
    """The issuer's endpoints, from its discovery document or the documented defaults."""

    issuer = issuer.rstrip("/")
    defaults = Discovery(
        issuer=issuer,
        authorization_endpoint=issuer + AUTHORIZE_PATH,
        token_endpoint=issuer + TOKEN_PATH,
        jwks_uri=issuer + "/.well-known/jwks.json",
        revocation_endpoint=None,
        from_document=False,
    )
    try:
        status, _headers, raw = http("GET", issuer + "/.well-known/openid-configuration",
                                     {"Accept": "application/json"}, None, timeout)
    except EndpointUnreachable:
        return defaults
    if status != 200:
        return defaults
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return defaults
    if not isinstance(document, Mapping):
        return defaults
    published = str(document.get("issuer") or "").rstrip("/")
    if published and published != issuer:
        raise SignInError(f"The discovery document names issuer {published!r}, not {issuer!r}.", code="issuer_mismatch")

    def endpoint(key: str, fallback: str | None) -> str | None:
        value = document.get(key)
        return value if isinstance(value, str) and value.startswith(("https://", "http://127.0.0.1", "http://localhost")) else fallback

    return Discovery(
        issuer=issuer,
        authorization_endpoint=endpoint("authorization_endpoint", defaults.authorization_endpoint) or defaults.authorization_endpoint,
        token_endpoint=endpoint("token_endpoint", defaults.token_endpoint) or defaults.token_endpoint,
        jwks_uri=endpoint("jwks_uri", defaults.jwks_uri),
        revocation_endpoint=endpoint("revocation_endpoint", None),
        from_document=True,
    )


# -- PKCE and the authorization request ---------------------------------------


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def new_pkce_pair() -> tuple[str, str]:
    """``(verifier, challenge)``: a 64-character verifier and its S256 challenge."""

    verifier = secrets.token_urlsafe(48)
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def authorization_url(
    discovery: Discovery, *, client_id: str, redirect_uri: str, state: str, nonce: str,
    code_challenge: str, host_id: str, agent_name_hint: str | None = None,
    login_hint: str | None = None, id_token_hint: str | None = None, consent: bool = False,
) -> str:
    params: list[tuple[str, str]] = [("client_id", client_id)]
    if agent_name_hint:
        params.append(("agent_name_hint", agent_name_hint))
    params.append(("ext_agent_host_id", host_id))
    if id_token_hint:
        params.append(("id_token_hint", id_token_hint))
    if login_hint:
        params.append(("login_hint", login_hint))
    params += [
        ("response_type", "code"),
        ("redirect_uri", redirect_uri),
        ("scope", " ".join(REQUESTED_SCOPES)),
        ("resource", PLAN_RESOURCE),
        ("state", state),
        ("nonce", nonce),
        ("code_challenge_method", "S256"),
        ("code_challenge", code_challenge),
    ]
    if consent:
        # errors-and-recovery: re-enabling plan usage after a decline repeats
        # OAuth with the full scope set; prompt=consent asks again.
        params.append(("prompt", "consent"))
    return discovery.authorization_endpoint + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def redact_authorization_url(url: str) -> str:
    """The URL without ``id_token_hint`` (never log an ID token)."""

    parts = urllib.parse.urlsplit(url)
    query = [(key, "<redacted>" if key == "id_token_hint" else value)
             for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query, quote_via=urllib.parse.quote)))


# -- the loopback callback -----------------------------------------------------

_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LearnLoop</title>
<style>body{{font-family:system-ui,sans-serif;margin:3rem auto;max-width:32rem;line-height:1.5;color:#222}}</style>
</head><body><h1>{title}</h1><p>{body}</p></body></html>"""


class CallbackListener:
    """A one-shot HTTP listener on ``127.0.0.1`` for ``/auth/callback``.

    It records the first callback's query parameters and answers the browser
    with a short page. Every other path is a 404, and nothing but the
    loopback interface is bound.
    """

    def __init__(self, *, port: int | None = None) -> None:
        self._result: dict[str, str] | None = None
        self._received = threading.Event()
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - http.server API
                parts = urllib.parse.urlsplit(self.path)
                if parts.path != CALLBACK_PATH:
                    self.send_error(404)
                    return
                params = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
                first = listener._accept(params)
                if not first:
                    title, body = "Already received", "LearnLoop already has a sign-in result. You can close this tab."
                elif "error" in params:
                    title, body = "Sign-in not completed", "Return to LearnLoop for details. You can close this tab."
                else:
                    title, body = "Signed in", "Return to LearnLoop to finish. You can close this tab."
                page = _PAGE.format(title=html.escape(title), body=html.escape(body)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(page)

            def log_message(self, *_args: Any) -> None:  # the query holds the code: never log it
                return

        candidates = [port] if port is not None else [PREFERRED_CALLBACK_PORT, 0]
        server: ThreadingHTTPServer | None = None
        last_error: OSError | None = None
        for candidate in candidates:
            try:
                server = ThreadingHTTPServer((CALLBACK_HOST, candidate), Handler)
                break
            except OSError as exc:
                last_error = exc
        if server is None:
            raise SignInError(f"Cannot listen on {CALLBACK_HOST} for the sign-in callback ({last_error}).",
                              code="listener_unavailable")
        server.daemon_threads = True
        self._server = server
        self.port = server.server_address[1]
        self.redirect_uri = f"http://{CALLBACK_HOST}:{self.port}{CALLBACK_PATH}"
        self._thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                                        name="learnloop-chatgpt-callback", daemon=True)
        self._thread.start()

    def _accept(self, params: dict[str, str]) -> bool:
        if self._received.is_set():
            return False
        self._result = params
        self._received.set()
        return True

    def cancel(self) -> None:
        """End a wait early; a later callback is answered but ignored."""

        self.cancelled = True
        self._received.set()

    cancelled = False

    def wait(self, timeout: float) -> dict[str, str] | None:
        if not self._received.wait(timeout) or self.cancelled:
            return None
        return self._result

    @property
    def received(self) -> bool:
        return self._received.is_set()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._server.shutdown()
        finally:
            self._server.server_close()

    _closed = False


# -- token endpoint ------------------------------------------------------------


def post_form(url: str, fields: Mapping[str, str], *, http: HttpCall = urllib_call,
              timeout: float = HTTP_TIMEOUT_SECONDS) -> dict[str, Any]:
    body = urllib.parse.urlencode(list(fields.items())).encode("ascii")
    status, _headers, raw = http("POST", url, {
        "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
    }, body, timeout)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, ValueError):
        payload = {}
    if status != 200:
        error = payload.get("error") if isinstance(payload, Mapping) else None
        if isinstance(error, Mapping):  # an API-style error object
            code, description = error.get("code") or error.get("type"), error.get("message")
        else:
            code = error
            description = payload.get("error_description") if isinstance(payload, Mapping) else None
        raise TokenEndpointError(status, str(code) if code else None, str(description) if description else None)
    if not isinstance(payload, dict):
        raise TokenEndpointError(status, "invalid_response", "the token endpoint returned no JSON object")
    return payload


def exchange_code(discovery: Discovery, *, client_id: str, code: str, code_verifier: str,
                  redirect_uri: str, http: HttpCall = urllib_call) -> dict[str, Any]:
    return post_form(discovery.token_endpoint, {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
        "resource": PLAN_RESOURCE,
    }, http=http)


def refresh_grant(token_endpoint: str, *, client_id: str, refresh_token: str,
                  http: HttpCall = urllib_call, timeout: float = HTTP_TIMEOUT_SECONDS) -> dict[str, Any]:
    # No scope: the refresh keeps the original grant (accounts-and-sessions).
    return post_form(token_endpoint, {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
        "resource": PLAN_RESOURCE,
    }, http=http, timeout=timeout)


def revoke_refresh_token(revocation_endpoint: str, *, client_id: str, refresh_token: str,
                         http: HttpCall = urllib_call) -> None:
    """Revoke the renewable session; an empty HTTP 200 is success, also for an invalid token."""

    post_form(revocation_endpoint, {
        "token": refresh_token, "token_type_hint": "refresh_token", "client_id": client_id,
    }, http=http)


def granted_scopes(token_payload: Mapping[str, Any], *, callback_scope: str | None = None) -> list[str]:
    """The token response's granted scopes, else the callback's, else the access token's claim."""

    for value in (token_payload.get("scope"), callback_scope):
        if isinstance(value, str) and value.strip():
            return sorted(set(value.replace("+", " ").split()))
    access = token_payload.get("access_token")
    if isinstance(access, str):
        try:
            claims = decode_jwt(access)[1]
        except ValueError:
            claims = {}
        scope = claims.get("scope")
        if isinstance(scope, str) and scope.strip():
            return sorted(set(scope.split()))
    return []


# -- ID token ------------------------------------------------------------------


def decode_jwt(token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    """``(header, claims, signing_input, signature)``; raises ValueError when malformed."""

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("not a compact JWS")
    try:
        header = json.loads(b64url_decode(parts[0]))
        claims = json.loads(b64url_decode(parts[1]))
        signature = b64url_decode(parts[2])
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("undecodable JWT") from exc
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise ValueError("JWT header and claims must be objects")
    return header, claims, f"{parts[0]}.{parts[1]}".encode("ascii"), signature


def rs256_verify(modulus: int, exponent: int, signing_input: bytes, signature: bytes) -> bool:
    """RSASSA-PKCS1-v1_5 with SHA-256 (RFC 8017 §8.2.2), by re-encoding.

    The recovered block is compared whole against the expected encoding, never
    parsed, so a malformed padding cannot be mistaken for a valid one.
    """

    if modulus.bit_length() < _MIN_RSA_BITS or exponent < 3 or exponent % 2 == 0:
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    value = int.from_bytes(signature, "big")
    if value >= modulus:
        return False
    recovered = pow(value, exponent, modulus).to_bytes(size, "big")
    digest_info = _SHA256_DIGEST_INFO + hashlib.sha256(signing_input).digest()
    padding = size - len(digest_info) - 3
    if padding < 8:
        return False
    expected = b"\x00\x01" + b"\xff" * padding + b"\x00" + digest_info
    return hmac.compare_digest(recovered, expected)


def fetch_jwks(jwks_uri: str, *, http: HttpCall = urllib_call) -> list[dict[str, Any]]:
    status, _headers, raw = http("GET", jwks_uri, {"Accept": "application/json"}, None, HTTP_TIMEOUT_SECONDS)
    if status != 200:
        raise SignInError(f"The issuer's signing keys could not be fetched (HTTP {status}).", code="jwks_unavailable")
    try:
        keys = json.loads(raw.decode("utf-8")).get("keys")
    except (UnicodeDecodeError, ValueError, AttributeError):
        keys = None
    if not isinstance(keys, list):
        raise SignInError("The issuer's JWKS document has no keys.", code="jwks_unavailable")
    return [key for key in keys if isinstance(key, dict)]


@dataclass(frozen=True)
class IdentityClaims:
    subject: str
    email: str | None
    signature: str  # "rs256" or "tls_endpoint"
    claims: dict[str, Any]


def validate_id_token(
    token: str, *, issuer: str, client_id: str, nonce: str | None,
    jwks: Callable[[], list[dict[str, Any]]] | None, now: float | None = None,
) -> IdentityClaims:
    """Check an ID token from the token endpoint; raises :class:`SignInError`.

    RS256 tokens are verified against the issuer's JWKS. An ID token signed
    with another asymmetric algorithm is accepted on the TLS rule of OpenID
    Connect Core 3.1.3.7 step 6 (it came straight from the token endpoint) and
    recorded as ``tls_endpoint``; ``none`` and HMAC algorithms are refused.
    """

    try:
        header, claims, signing_input, signature = decode_jwt(token)
    except ValueError as exc:
        raise SignInError(f"The ID token is malformed ({exc}).", code="invalid_id_token") from None
    algorithm = str(header.get("alg") or "")
    if not algorithm or algorithm == "none" or algorithm.startswith("HS"):
        raise SignInError(f"The ID token uses an unacceptable algorithm ({algorithm or 'none'}).", code="invalid_id_token")
    # Without a key to check against, the TLS rule applies (and is recorded);
    # a key that exists and does not verify the signature is a refusal.
    signature_mode = "tls_endpoint"
    if algorithm == "RS256" and jwks is not None:
        try:
            available = jwks()
        except SignInError:
            available = []
        kid = header.get("kid")
        candidates: list[tuple[int, int]] = []
        for key in available:
            if key.get("kty") != "RSA" or key.get("alg") not in (None, "RS256") or key.get("use") not in (None, "sig"):
                continue
            if kid is not None and key.get("kid") != kid:
                continue
            try:
                candidates.append((int.from_bytes(b64url_decode(str(key["n"])), "big"),
                                   int.from_bytes(b64url_decode(str(key["e"])), "big")))
            except (KeyError, ValueError):
                continue
        if candidates:
            if not any(rs256_verify(n, e, signing_input, signature) for n, e in candidates):
                raise SignInError("The ID token's signature does not match the issuer's keys.", code="invalid_id_token")
            signature_mode = "rs256"
    current = time.time() if now is None else now
    if str(claims.get("iss") or "").rstrip("/") != issuer.rstrip("/"):
        raise SignInError("The ID token was issued by another issuer.", code="invalid_id_token")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if client_id not in audiences:
        raise SignInError("The ID token was issued for another client.", code="invalid_id_token")
    expires = claims.get("exp")
    if not isinstance(expires, (int, float)) or expires + CLOCK_SKEW_SECONDS < current:
        raise SignInError("The ID token has expired.", code="invalid_id_token")
    if not isinstance(claims.get("iat"), (int, float)):
        raise SignInError("The ID token has no issue time.", code="invalid_id_token")
    if nonce is not None and not hmac.compare_digest(str(claims.get("nonce") or ""), nonce):
        raise SignInError("The ID token's nonce does not match this sign-in.", code="invalid_id_token")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise SignInError("The ID token has no subject.", code="invalid_id_token")
    email = claims.get("email")
    return IdentityClaims(subject=subject, email=email if isinstance(email, str) else None,
                          signature=signature_mode, claims=claims)


def states_match(expected: str, returned: str | None) -> bool:
    return returned is not None and hmac.compare_digest(expected.encode("utf-8"), returned.encode("utf-8"))


__all__ = [
    "AGENT_NAME",
    "AUTH_ISSUER",
    "CALLBACK_PATH",
    "CallbackListener",
    "DYNAMIC_CLIENT_ID",
    "Discovery",
    "EndpointUnreachable",
    "HttpCall",
    "IdentityClaims",
    "PLAN_RESOURCE",
    "PLAN_SCOPE",
    "REQUESTED_SCOPES",
    "SignInError",
    "TERMINAL_REFRESH_ERRORS",
    "TokenEndpointError",
    "authorization_url",
    "b64url",
    "b64url_decode",
    "decode_jwt",
    "discover",
    "exchange_code",
    "fetch_jwks",
    "granted_scopes",
    "new_pkce_pair",
    "post_form",
    "redact_authorization_url",
    "refresh_grant",
    "revoke_refresh_token",
    "rs256_verify",
    "states_match",
    "urllib_call",
    "validate_id_token",
]
