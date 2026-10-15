"""A local fake of Sign in with ChatGPT and of the ChatGPT-plan Responses API.

One HTTP server on 127.0.0.1 plays both parts, enforcing the documented
contract the client must satisfy (developers.openai.com/siwc):

* **auth**: discovery, a JWKS with a test RSA key, ``/api/accounts/authorize``
  (validates the parameters and redirects to the loopback callback with
  ``code``, ``state``, the issued ``client_id`` on a first registration and
  the granted ``scope``), the token endpoint (PKCE S256, same redirect URI,
  ``resource``, issued client id; refresh tokens rotate and a reused one is
  ``invalid_grant``) and revocation;
* **inference**: ``POST /v1/responses`` requires the current bearer token,
  ``store: false``, ``stream: true``, no unsupported field and no ``role:
  system`` item, and answers with a scripted SSE stream; ``GET /v1/models``
  lists models. Tools must be function tools grouped in a namespace (no
  hosted tool, no top-level function; preview-limitations, re-read
  2026-10-15). A tool round's history must be self-contained with ``store:
  false``: no input item carries a stored id, a reasoning item carries its
  ``encrypted_content`` (asked for with ``include``), and every function call
  has exactly one ``function_call_output`` after it, and every output a call.

``complete_browser_flow`` plays the browser: it opens the authorization URL
and follows the redirect to the client's loopback listener. Nothing leaves
the machine.
"""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import random
import threading
import time
from typing import Any, Callable, Iterator
import urllib.error
import urllib.parse
import urllib.request

#: The route's unsupported request fields, copied from the docs
#: (developers.openai.com/siwc/token-sharing-open-source/preview-limitations,
#: re-read 2026-10-12) and kept independent of the implementation's constant,
#: so the fake cannot drift along with it. ``previous_response_id`` must be
#: omitted over HTTP (same page).
DOCUMENTED_UNSUPPORTED_FIELDS = frozenset({
    "background", "conversation", "max_output_tokens", "max_tool_calls", "metadata", "moderation",
    "multi_agent", "prompt", "prompt_cache_retention", "safety_identifier", "temperature",
    "top_logprobs", "top_p", "truncation", "user", "previous_response_id",
})
#: LearnLoop's own rule on top: it never sends ``tool_choice``. (``tools`` is
#: checked separately: namespaced function tools only.)
REFUSED_FIELDS = DOCUMENTED_UNSUPPORTED_FIELDS | {"tool_choice"}
#: Hosted tool types the route does not support (preview-limitations).
HOSTED_TOOL_TYPES = frozenset({
    "image_generation", "file_search", "code_interpreter", "computer_use_preview", "computer", "mcp",
    "tool_search", "web_search", "web_search_preview",
})

PLAN_SCOPES = "chatgpt.tokens.use.direct email offline_access openid profile resource.invoke"
IDENTITY_SCOPES = "email openid profile"


# -- a deterministic RSA test key (pure Python; tests only) --------------------


def _is_probable_prime(n: int, rng: random.Random) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(24):
        a = rng.randrange(2, n - 2)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _prime(bits: int, rng: random.Random) -> int:
    while True:
        candidate = rng.getrandbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if _is_probable_prime(candidate, rng):
            return candidate


class RsaTestKey:
    def __init__(self, seed: int = 20261012, bits: int = 2048) -> None:
        rng = random.Random(seed)
        self.e = 65537
        while True:
            p, q = _prime(bits // 2, rng), _prime(bits // 2, rng)
            phi = (p - 1) * (q - 1)
            if p != q and phi % self.e:
                break
        self.n = p * q
        self.d = pow(self.e, -1, phi)
        self.kid = "test-key-1"

    def jwk(self) -> dict[str, str]:
        size = (self.n.bit_length() + 7) // 8
        return {"kty": "RSA", "kid": self.kid, "alg": "RS256", "use": "sig",
                "n": _b64(self.n.to_bytes(size, "big")), "e": _b64(self.e.to_bytes(3, "big"))}

    def sign_jwt(self, claims: dict[str, Any], *, alg: str = "RS256", kid: str | None = None) -> str:
        header = {"alg": alg, "typ": "JWT", "kid": kid or self.kid}
        signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(claims).encode())}".encode()
        if alg == "none":
            return signing_input.decode() + "."
        size = (self.n.bit_length() + 7) // 8
        digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(signing_input).digest()
        encoded = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
        signature = pow(int.from_bytes(encoded, "big"), self.d, self.n).to_bytes(size, "big")
        return signing_input.decode() + "." + _b64(signature)


_KEY: RsaTestKey | None = None


def rsa_test_key() -> RsaTestKey:
    global _KEY
    if _KEY is None:
        _KEY = RsaTestKey()
    return _KEY


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unsigned_jwt(claims: dict[str, Any]) -> str:
    return f"{_b64(b'{}')}.{_b64(json.dumps(claims).encode())}.{_b64(b'sig')}"


# -- scripted Responses streams --------------------------------------------------


def completed_events(text: str, *, model: str = "gpt-test-2026-10-01", usage: dict[str, Any] | None = None,
                     response_id: str = "resp_test_1", deltas: bool = True) -> list[dict[str, Any]]:
    usage = usage if usage is not None else {
        "input_tokens": 120, "input_tokens_details": {"cached_tokens": 20},
        "output_tokens": 30, "output_tokens_details": {"reasoning_tokens": 8}, "total_tokens": 150,
    }
    response = {"id": response_id, "object": "response", "status": "in_progress", "model": model}
    events: list[dict[str, Any]] = [
        {"type": "response.created", "response": response},
        {"type": "response.in_progress", "response": response},
    ]
    if deltas:
        for start in range(0, len(text), 7):
            events.append({"type": "response.output_text.delta", "delta": text[start:start + 7]})
        events.append({"type": "response.output_text.done", "text": text})
    events.append({"type": "response.completed", "response": {
        **response, "status": "completed", "usage": usage,
        "output": [
            {"type": "reasoning", "id": "rs_1", "summary": []},
            {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]},
        ],
    }})
    return events


def tool_call_events(calls: list[tuple[str, Any]], *, namespace: str | None = "workspace",
                     response_id: str = "resp_tools", call_prefix: str = "call", encrypted: bool = True,
                     usage: dict[str, Any] | None = None, model: str = "gpt-test-2026-10-01",
                     in_terminal_output: bool = True) -> list[dict[str, Any]]:
    """A response that calls functions: a reasoning item, then one ``function_call`` per entry.

    ``calls`` holds ``(name, arguments)``; a dict is JSON-encoded, a string is
    sent as is (so a test can send malformed arguments). Items are streamed as
    ``response.output_item.done`` and, unless ``in_terminal_output`` is False,
    repeated in the terminal response's ``output``.
    """

    usage = usage if usage is not None else {
        "input_tokens": 400, "input_tokens_details": {"cached_tokens": 100},
        "output_tokens": 60, "output_tokens_details": {"reasoning_tokens": 40}, "total_tokens": 460,
    }
    response = {"id": response_id, "object": "response", "status": "in_progress", "model": model}
    reasoning: dict[str, Any] = {"type": "reasoning", "id": f"rs_{response_id}", "summary": []}
    if encrypted:
        reasoning["encrypted_content"] = f"enc-{response_id}"
    output: list[dict[str, Any]] = [reasoning]
    for index, (name, arguments) in enumerate(calls):
        item: dict[str, Any] = {
            "type": "function_call", "id": f"fc_{response_id}_{index}", "status": "completed",
            "call_id": f"{call_prefix}_{response_id}_{index}", "name": name,
            "arguments": arguments if isinstance(arguments, str) else json.dumps(arguments),
        }
        if namespace is not None:
            item["namespace"] = namespace
        output.append(item)
    events: list[dict[str, Any]] = [{"type": "response.created", "response": response}]
    for index, item in enumerate(output):
        events.append({"type": "response.output_item.added", "output_index": index, "item": {**item, "arguments": ""}
                       if item["type"] == "function_call" else item})
        events.append({"type": "response.output_item.done", "output_index": index, "item": item})
    events.append({"type": "response.completed", "response": {
        **response, "status": "completed", "usage": usage, "output": output if in_terminal_output else [],
    }})
    return events


def failed_events(code: str, message: str = "failed", *, after_deltas: str = "") -> list[dict[str, Any]]:
    response = {"id": "resp_failed", "status": "in_progress", "model": "gpt-test-2026-10-01"}
    events: list[dict[str, Any]] = [{"type": "response.created", "response": response}]
    if after_deltas:
        events.append({"type": "response.output_text.delta", "delta": after_deltas})
    events.append({"type": "response.failed", "response": {
        **response, "status": "failed", "error": {"code": code, "message": message},
        "usage": {"input_tokens": 50, "output_tokens": 2},
    }})
    return events


class Reply:
    """One scripted answer to ``POST /v1/responses``."""

    def __init__(self, *, events: list[dict[str, Any]] | None = None, status: int = 200,
                 body: Any = None, delay: float = 0.0, stall: float = 0.0, truncate: bool = False,
                 headers: dict[str, str] | None = None, chunked: bool = False,
                 respond: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None) -> None:
        self.chunked = chunked
        self.events = events or []
        #: Builds the events from the request body (a reply that depends on what was served).
        self.respond = respond
        self.status = status
        self.body = body
        self.delay = delay
        self.stall = stall
        self.truncate = truncate
        self.headers = headers or {}


# -- the server -----------------------------------------------------------------


class FakeChatGPT:
    def __init__(self, *, granted_scope: str = PLAN_SCOPES, email: str = "learner@example.com",
                 subject: str = "user-sub-1", issued_client_id: str = "oaiapp_test_client",
                 access_lifetime: int = 3600, id_token_alg: str = "RS256",
                 include_client_id_in_callback: bool = True, wrong_nonce: bool = False) -> None:
        self.key = rsa_test_key()
        self.granted_scope = granted_scope
        self.email = email
        self.subject = subject
        self.issued_client_id = issued_client_id
        self.access_lifetime = access_lifetime
        self.id_token_alg = id_token_alg
        self.include_client_id_in_callback = include_client_id_in_callback
        self.wrong_nonce = wrong_nonce
        self.deny = False
        self.callback_error: str | None = None
        self.replies: deque[Reply] = deque()
        #: Builds the reply from the request body when no scripted reply is queued.
        self.default_reply: Callable[[dict[str, Any]], Reply] | None = None
        self.requests: list[dict[str, Any]] = []
        self.token_requests: list[dict[str, str]] = []
        self.authorize_requests: list[dict[str, str]] = []
        self.revocations: list[dict[str, str]] = []
        self.model_list_requests = 0
        self.refresh_error: str | None = None
        self._codes: dict[str, dict[str, str]] = {}
        self.access_tokens: set[str] = set()
        self.refresh_tokens: set[str] = set()
        self.used_refresh_tokens: set[str] = set()
        self._counter = 0
        self._lock = threading.Lock()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: Any) -> None:
                return

            def _json(self, status: int, payload: Any, headers: dict[str, str] | None = None) -> None:
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                for name, value in (headers or {}).items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:  # noqa: N802
                parts = urllib.parse.urlsplit(self.path)
                if parts.path == "/.well-known/openid-configuration":
                    base = fake.issuer
                    self._json(200, {
                        "issuer": base,
                        "authorization_endpoint": base + "/api/accounts/authorize",
                        "token_endpoint": base + "/api/accounts/oauth/token",
                        "jwks_uri": base + "/.well-known/jwks.json",
                        "revocation_endpoint": base + "/api/accounts/oauth/revoke",
                    })
                elif parts.path == "/.well-known/jwks.json":
                    self._json(200, {"keys": [fake.key.jwk()]})
                elif parts.path == "/api/accounts/authorize":
                    self._authorize(dict(urllib.parse.parse_qsl(parts.query)))
                elif parts.path == "/v1/models":
                    fake.model_list_requests += 1
                    if not fake._authorized(self.headers.get("Authorization")):
                        self._json(401, {"error": {"code": "subscription_sharing_invalid_user", "message": "no"}})
                        return
                    self._json(200, {"models": [
                        {"slug": "gpt-test-fast", "display_name": "GPT Test Fast", "visibility": "list"},
                        {"slug": "gpt-test-hidden", "display_name": "Hidden", "visibility": "hide"},
                        {"slug": "gpt-test-pro", "display_name": "GPT Test Pro", "visibility": "list"},
                    ]})
                else:
                    self._json(404, {"detail": "not found"})

            def _authorize(self, params: dict[str, str]) -> None:
                fake.authorize_requests.append(params)
                redirect = params.get("redirect_uri", "")
                ok = (
                    params.get("response_type") == "code"
                    and params.get("code_challenge_method") == "S256"
                    and params.get("resource") == "https://api.openai.com/v1"
                    and set(params.get("scope", "").split()) == set(PLAN_SCOPES.split())
                    and redirect.startswith("http://127.0.0.1:") and redirect.endswith("/auth/callback")
                    and params.get("ext_agent_host_id", "").startswith("urn:uuid:")
                    and params.get("state") and params.get("nonce") and params.get("code_challenge")
                )
                first = params.get("client_id") == "dynamic_agent_client"
                if first and params.get("agent_name_hint") != "LearnLoop":
                    ok = False
                if not first and "agent_name_hint" in params:
                    ok = False
                if not ok:
                    self._json(400, {"detail": "invalid authorization request"})
                    return
                query: dict[str, str] = {"state": params["state"]}
                if fake.deny:
                    query["error"] = "access_denied"
                elif fake.callback_error:
                    query["error"] = fake.callback_error
                else:
                    code = f"code-{fake._next()}"
                    client_id = fake.issued_client_id if first else params["client_id"]
                    fake._codes[code] = {**params, "issued_client_id": client_id}
                    query["code"] = code
                    query["scope"] = fake.granted_scope.replace(" ", "+")
                    if first and fake.include_client_id_in_callback:
                        query["client_id"] = client_id
                location = redirect + "?" + "&".join(f"{k}={urllib.parse.quote(v, safe='+')}" for k, v in query.items())
                self.send_response(302)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self) -> None:  # noqa: N802
                parts = urllib.parse.urlsplit(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length)
                if parts.path == "/api/accounts/oauth/token":
                    self._token(dict(urllib.parse.parse_qsl(raw.decode())))
                elif parts.path == "/api/accounts/oauth/revoke":
                    fake.revocations.append(dict(urllib.parse.parse_qsl(raw.decode())))
                    fake.refresh_tokens.discard(dict(urllib.parse.parse_qsl(raw.decode())).get("token", ""))
                    self.send_response(200)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif parts.path == "/v1/responses":
                    self._responses(raw)
                else:
                    self._json(404, {"detail": "not found"})

            def _token(self, form: dict[str, str]) -> None:
                fake.token_requests.append(form)
                if form.get("resource") != "https://api.openai.com/v1":
                    self._json(400, {"error": "invalid_request", "error_description": "resource"})
                    return
                if form.get("client_id") == "dynamic_agent_client":
                    self._json(400, {"error": "invalid_client", "error_description": "use the issued id"})
                    return
                if form.get("grant_type") == "authorization_code":
                    pending = fake._codes.pop(form.get("code", ""), None)
                    if pending is None:
                        self._json(400, {"error": "invalid_grant", "error_description": "unknown code"})
                        return
                    challenge = _b64(hashlib.sha256(form.get("code_verifier", "").encode()).digest())
                    if (challenge != pending["code_challenge"] or form.get("redirect_uri") != pending["redirect_uri"]
                            or form.get("client_id") != pending["issued_client_id"]):
                        self._json(400, {"error": "invalid_grant", "error_description": "pkce/redirect/client"})
                        return
                    nonce = "wrong" if fake.wrong_nonce else pending["nonce"]
                    self._json(200, fake._token_set(pending["issued_client_id"], nonce=nonce))
                    return
                if form.get("grant_type") == "refresh_token":
                    if "scope" in form:
                        self._json(400, {"error": "invalid_request", "error_description": "no scope on refresh"})
                        return
                    if fake.refresh_error:
                        self._json(400, {"error": fake.refresh_error})
                        return
                    token = form.get("refresh_token", "")
                    if token in fake.used_refresh_tokens:
                        self._json(400, {"error": "refresh_token_reused"})
                        return
                    if token not in fake.refresh_tokens:
                        self._json(400, {"error": "invalid_grant"})
                        return
                    fake.refresh_tokens.discard(token)
                    fake.used_refresh_tokens.add(token)
                    self._json(200, fake._token_set(form["client_id"], nonce=None, with_id_token=False))
                    return
                self._json(400, {"error": "unsupported_grant_type"})

            def _responses(self, raw: bytes) -> None:
                body = json.loads(raw.decode())
                fake.requests.append({"body": body, "authorization": self.headers.get("Authorization")})
                if not fake._authorized(self.headers.get("Authorization")):
                    self._json(401, {"error": {"code": "subscription_sharing_invalid_user", "message": "token"}},
                               {"x-request-id": "req_401"})
                    return
                problems = sorted(set(body) & REFUSED_FIELDS)
                if body.get("store") is not False or body.get("stream") is not True or problems:
                    self._json(400, {"error": {"code": "subscription_sharing_unsupported_capability",
                                               "message": "bad body", "param": problems[0] if problems else "store"}})
                    return
                if any(isinstance(item, dict) and item.get("role") == "system" for item in body.get("input", [])):
                    self._json(400, {"error": {"code": "invalid_request", "message": "system items rejected"}})
                    return
                problem = _tool_problem(body)
                if problem is not None:
                    code, param, message = problem
                    self._json(400, {"error": {"code": code, "message": message, "param": param}})
                    return
                if fake.replies:
                    reply = fake.replies.popleft()
                elif fake.default_reply is not None:
                    reply = fake.default_reply(body)
                else:
                    reply = Reply(events=completed_events('{"ok": true}'))
                if reply.respond is not None:
                    reply.events = reply.respond(body)
                if reply.delay:
                    time.sleep(reply.delay)
                if reply.status != 200:
                    self._json(reply.status, reply.body if reply.body is not None else {"detail": "error"},
                               {"x-request-id": f"req_{reply.status}", **reply.headers})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("x-request-id", "req_ok")
                if reply.chunked:
                    # The real API streams with chunked transfer encoding.
                    self.send_header("Transfer-Encoding", "chunked")
                else:
                    self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                for index, event in enumerate(reply.events):
                    if reply.truncate and event.get("type") == "response.completed":
                        break
                    chunk = f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode()
                    if reply.chunked:
                        # Split each event across two chunks to exercise reassembly.
                        half = len(chunk) // 2
                        chunk = b"".join(f"{len(part):x}\r\n".encode() + part + b"\r\n"
                                         for part in (chunk[:half], chunk[half:]))
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except OSError:
                        return
                    if reply.stall and index == 0:
                        time.sleep(reply.stall)
                if reply.chunked:
                    try:
                        self.wfile.write(b"0\r\n\r\n")
                        self.wfile.flush()
                    except OSError:
                        return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self.port = self._server.server_address[1]
        self.issuer = f"http://127.0.0.1:{self.port}"
        self.base_url = f"http://127.0.0.1:{self.port}/v1"
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05},
                                        daemon=True)
        self._thread.start()

    def _next(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def _authorized(self, header: str | None) -> bool:
        return bool(header) and header.startswith("Bearer ") and header[len("Bearer "):] in self.access_tokens

    def _token_set(self, client_id: str, *, nonce: str | None, with_id_token: bool = True) -> dict[str, Any]:
        n = self._next()
        access = f"access-{n}"
        refresh = f"refresh-{n}"
        self.access_tokens.add(access)
        self.refresh_tokens.add(refresh)
        now = int(time.time())
        payload: dict[str, Any] = {
            "access_token": access, "refresh_token": refresh, "token_type": "Bearer",
            "expires_in": self.access_lifetime, "scope": self.granted_scope, "earliest_refresh_at": now + 60,
        }
        if with_id_token:
            claims = {"iss": self.issuer, "aud": client_id, "sub": self.subject, "email": self.email,
                      "iat": now, "exp": now + 3600}
            if nonce is not None:
                claims["nonce"] = nonce
            payload["id_token"] = self.key.sign_jwt(claims, alg=self.id_token_alg)
        return payload

    def revoke_all_access(self) -> None:
        self.access_tokens.clear()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _tool_problem(body: dict[str, Any]) -> tuple[str, str, str] | None:
    """``(code, param, message)`` when the body breaks the plan route's tool contract."""

    tools = body.get("tools")
    if tools is not None:
        if not isinstance(tools, list):
            return "invalid_request", "tools", "tools must be a list"
        for tool in tools:
            kind = tool.get("type") if isinstance(tool, dict) else None
            if kind in HOSTED_TOOL_TYPES:
                return "subscription_sharing_unsupported_capability", "tools", f"hosted tool {kind} is unsupported"
            if kind != "namespace":
                return ("subscription_sharing_unsupported_capability", "tools",
                        "group function tools in a namespace or supply them through additional_tools")
            for function in tool.get("tools") or []:
                if not isinstance(function, dict) or function.get("type") != "function":
                    return "subscription_sharing_unsupported_capability", "tools", "namespaces hold function tools"
                parameters = function.get("parameters") or {}
                if function.get("strict") and (parameters.get("additionalProperties") is not False or
                                               set(parameters.get("required") or []) != set(parameters.get("properties") or {})):
                    return "invalid_request", "tools", "strict function schemas need every property required"
        if "reasoning.encrypted_content" not in (body.get("include") or []):
            return "invalid_request", "include", "a tool round with store=false must include reasoning.encrypted_content"
    calls: dict[str, int] = {}
    answered: dict[str, int] = {}
    for item in body.get("input") or []:
        if not isinstance(item, dict):
            continue
        if "id" in item:
            return ("invalid_request", "input", f"Item with id {item['id']!r} not found. Items are not persisted "
                    "when `store` is set to false.")
        kind = item.get("type")
        if kind == "reasoning" and not item.get("encrypted_content"):
            return "invalid_request", "input", "a reasoning item needs encrypted_content when store is false"
        if kind == "reasoning" and ("summary" not in item or "content" in item):
            return "invalid_request", "input", "a reasoning input item takes summary and encrypted_content"
        if kind == "function_call":
            if tools is None:
                return "invalid_request", "tools", "a function call in input needs its tool declared"
            calls[str(item.get("call_id"))] = calls.get(str(item.get("call_id")), 0) + 1
        elif kind == "function_call_output":
            call_id = str(item.get("call_id"))
            if call_id not in calls:
                return "invalid_request", "input", f"No tool call found for function call output with call_id {call_id}."
            answered[call_id] = answered.get(call_id, 0) + 1
            if not isinstance(item.get("output"), str):
                return "invalid_request", "input", "function_call_output.output must be a string"
    missing = sorted(call_id for call_id in calls if answered.get(call_id) != 1)
    if missing:
        return "invalid_request", "input", f"No tool output found for function call {missing[0]}."
    return None


def served_outputs(body: dict[str, Any]) -> list[str]:
    """The ``function_call_output`` texts a request carries, in order."""

    return [item["output"] for item in body.get("input") or []
            if isinstance(item, dict) and item.get("type") == "function_call_output"]


@contextmanager
def fake_chatgpt(**kwargs: Any) -> Iterator[FakeChatGPT]:
    server = FakeChatGPT(**kwargs)
    try:
        yield server
    finally:
        server.close()


def complete_browser_flow(authorize_url: str) -> None:
    """Play the browser: open the authorization URL and follow its redirect home."""

    with urllib.request.urlopen(authorize_url, timeout=10) as response:  # noqa: S310 - loopback only
        response.read()


def sign_in(session: Any, server: FakeChatGPT, **kwargs: Any) -> Any:
    pending = session.begin_sign_in(issuer=server.issuer, port=0, **kwargs)
    complete_browser_flow(pending.authorize_url)
    return pending.wait(timeout=10)


def run_in_thread(target: Callable[[], Any]) -> tuple[threading.Thread, dict[str, Any]]:
    out: dict[str, Any] = {}

    def run() -> None:
        try:
            out["value"] = target()
        except BaseException as exc:  # noqa: BLE001 - surfaced to the test
            out["error"] = exc

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, out


def pause_after(marker: bytes, reached: threading.Event, release: threading.Event) -> Callable[..., Any]:
    """An ``HttpCall`` that completes against the fake, then waits before returning.

    It holds a token-endpoint answer in flight (the request whose form body
    contains ``marker``), so a test can interleave a sign-out, an interrupt or
    a reader between the server's reply and the local commit.
    """

    from learnloop.ai.chatgpt_plan.oauth import urllib_call

    def http(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> Any:
        answer = urllib_call(method, url, headers, body, timeout)
        if body and marker in body:
            reached.set()
            release.wait(10)
        return answer

    return http
