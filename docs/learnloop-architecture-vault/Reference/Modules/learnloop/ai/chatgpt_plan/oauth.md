---
title: "learnloop.ai.chatgpt_plan.oauth"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/oauth.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/oauth.py"
source_commit: "00e41515c6d7353c28031d6342efa95c4b051412"
source_commit_timestamp: "2026-10-12T21:57:45-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.chatgpt_plan"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.chatgpt_plan.oauth module"
  - "src/learnloop/ai/chatgpt_plan/oauth.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.oauth`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.oauth` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: Sign in with ChatGPT for open-source apps: OAuth 2.0 code flow with PKCE.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py) |
| Source lines | 581 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `00e41515c6d7353c28031d6342efa95c4b051412` |
| Commit timestamp | `2026-10-12T21:57:45-04:00` |

## Public API

- `class SignInError(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 79) — The sign-in attempt ended without usable credentials.
  - `__init__(self, message: str, *, code: str='sign_in_failed') -> None` (line 82; internal)
- `class TokenEndpointError(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 87) — The token or revocation endpoint answered with an error status.
  - `__init__(self, status: int, error: str | None, description: str | None) -> None` (line 90; internal)
- `class EndpointUnreachable(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 97) — A network failure before any answer (the reason never echoes a URL or token).
- `urllib_call(method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float) -> tuple[int, Mapping[str, str], bytes]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 101)
- `class Discovery` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 118)
  - `as_dict(self) -> dict[str, Any]` (line 126; public)
- `discover(issuer: str=AUTH_ISSUER, *, http: HttpCall=urllib_call, timeout: float=HTTP_TIMEOUT_SECONDS) -> Discovery` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 134) — The issuer's endpoints, from its discovery document or the documented defaults.
- `b64url(data: bytes) -> str` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 180)
- `b64url_decode(text: str) -> bytes` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 184)
- `new_pkce_pair() -> tuple[str, str]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 188) — ``(verifier, challenge)``: a 64-character verifier and its S256 challenge.
- `authorization_url(discovery: Discovery, *, client_id: str, redirect_uri: str, state: str, nonce: str, code_challenge: str, host_id: str, agent_name_hint: str | None=None, login_hint: str | None=None, id_token_hint: str | None=None, consent: bool=False) -> str` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 196)
- `redact_authorization_url(url: str) -> str` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 226) — The URL without ``id_token_hint`` (never log an ID token).
- `class CallbackListener` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 242) — A one-shot HTTP listener on ``127.0.0.1`` for ``/auth/callback``.
  - `__init__(self, *, port: int | None=None) -> None` (line 250; internal)
  - `_accept(self, params: dict[str, str]) -> bool` (line 300; internal)
  - `cancel(self) -> None` (line 307; public) — End a wait early; a later callback is answered but ignored.
  - `wait(self, timeout: float) -> dict[str, str] | None` (line 315; public)
  - `received(self) -> bool` (line 321; public)
  - `close(self) -> None` (line 324; public)
- `post_form(url: str, fields: Mapping[str, str], *, http: HttpCall=urllib_call, timeout: float=HTTP_TIMEOUT_SECONDS) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 339)
- `exchange_code(discovery: Discovery, *, client_id: str, code: str, code_verifier: str, redirect_uri: str, http: HttpCall=urllib_call) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 362)
- `refresh_grant(token_endpoint: str, *, client_id: str, refresh_token: str, http: HttpCall=urllib_call, timeout: float=HTTP_TIMEOUT_SECONDS) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 374)
- `revoke_refresh_token(revocation_endpoint: str, *, client_id: str, refresh_token: str, http: HttpCall=urllib_call) -> None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 385) — Revoke the renewable session; an empty HTTP 200 is success, also for an invalid token.
- `granted_scopes(token_payload: Mapping[str, Any], *, callback_scope: str | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 394) — The token response's granted scopes, else the callback's, else the access token's claim.
- `decode_jwt(token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 415) — ``(header, claims, signing_input, signature)``; raises ValueError when malformed.
- `rs256_verify(modulus: int, exponent: int, signing_input: bytes, signature: bytes) -> bool` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 432) — RSASSA-PKCS1-v1_5 with SHA-256 (RFC 8017 §8.2.2), by re-encoding.
- `fetch_jwks(jwks_uri: str, *, http: HttpCall=urllib_call) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 456)
- `class IdentityClaims` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 470)
- `validate_id_token(token: str, *, issuer: str, client_id: str, nonce: str | None, jwks: Callable[[], list[dict[str, Any]]] | None, now: float | None=None) -> IdentityClaims` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 477) — Check an ID token from the token endpoint; raises :class:`SignInError`.
- `states_match(expected: str, returned: str | None) -> bool` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 544)

### Module constants

- `AUTH_ISSUER` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 50)
- `AUTHORIZE_PATH` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 51)
- `TOKEN_PATH` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 52)
- `PLAN_RESOURCE` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 53)
- `PLAN_SCOPE` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 54)
- `REQUESTED_SCOPES` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 55)
- `DYNAMIC_CLIENT_ID` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 56)
- `AGENT_NAME` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 57)
- `CALLBACK_HOST` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 58)
- `CALLBACK_PATH` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 59)
- `PREFERRED_CALLBACK_PORT` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 61)
- `CLOCK_SKEW_SECONDS` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 63)
- `HTTP_TIMEOUT_SECONDS` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 64)
- `TERMINAL_REFRESH_ERRORS` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 67)
- `_SHA256_DIGEST_INFO` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 72)
- `_MIN_RSA_BITS` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 73)
- `_PAGE` ([src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py), line 237)

### Explicit exports

`__all__` declares:

- `AGENT_NAME`
- `AUTH_ISSUER`
- `CALLBACK_PATH`
- `CallbackListener`
- `DYNAMIC_CLIENT_ID`
- `Discovery`
- `EndpointUnreachable`
- `HttpCall`
- `IdentityClaims`
- `PLAN_RESOURCE`
- `PLAN_SCOPE`
- `REQUESTED_SCOPES`
- `SignInError`
- `TERMINAL_REFRESH_ERRORS`
- `TokenEndpointError`
- `authorization_url`
- `b64url`
- `b64url_decode`
- `decode_jwt`
- `discover`
- `exchange_code`
- `fetch_jwks`
- `granted_scopes`
- `new_pkce_pair`
- `post_form`
- `redact_authorization_url`
- `refresh_grant`
- `revoke_refresh_token`
- `rs256_verify`
- `states_match`
- `urllib_call`
- `validate_id_token`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `AGENT_NAME`, `AUTH_ISSUER`, `CallbackListener`, `DYNAMIC_CLIENT_ID`, `Discovery`, `EndpointUnreachable`, `HTTP_TIMEOUT_SECONDS`, `HttpCall`, `PLAN_SCOPE`, `SignInError`, `TERMINAL_REFRESH_ERRORS`, `TokenEndpointError`, `authorization_url`, `discover`, `exchange_code`, `fetch_jwks`, `granted_scopes`, `new_pkce_pair`, `refresh_grant`, `revoke_refresh_token`, `states_match`, `urllib_call`, `validate_id_token`; statically calls `CallbackListener`, `SignInError`, `authorization_url`, `discover`, `exchange_code`, `fetch_jwks`, `granted_scopes`, `new_pkce_pair`, `refresh_grant`, `revoke_refresh_token`, `states_match`, `validate_id_token`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `EndpointUnreachable`, `urllib_call`; statically calls `urllib_call`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `SignInError`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `SignInError`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `dataclasses`, `hashlib`, `hmac`, `html`, `http`, `json`, `secrets`, `threading`, `time`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]], [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/chatgpt_plan_fakes.py](../../../../../../../tests/chatgpt_plan_fakes.py) — direct import
- [tests/test_chatgpt_plan_signin.py](../../../../../../../tests/test_chatgpt_plan_signin.py) — direct import
  - `test_cancel_after_the_browser_returned_saves_nothing`
  - `test_declined_consent_saves_nothing`
  - `test_id_token_signature_checks`
  - `test_reauthorization_rejects_a_callback_naming_another_client`
  - `test_registration_without_issued_client_id_is_incomplete`
  - `test_returning_sign_in_with_another_account_keeps_the_saved_one`
  - `test_sign_in_timeout_and_cancel_end_the_attempt`
  - `test_sign_out_invalidates_a_sign_in_that_was_already_pending`
  - `test_state_mismatch_is_refused_before_any_exchange`
  - `test_wrong_nonce_is_refused_and_nothing_replaced`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/oauth.py](../../../../../../../src/learnloop/ai/chatgpt_plan/oauth.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
